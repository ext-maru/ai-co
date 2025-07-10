import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

interface FilterOptions {
  status?: string[]
  tech_stack?: string[]
  tags?: string[]
  priority?: string[]
  owner?: string[]
  date_from?: string
  date_to?: string
  progress_min?: number
  progress_max?: number
  search?: string
}

// フィルタリングされたプロジェクトを返すAPI
export async function POST(request: NextRequest) {
  try {
    const filters: FilterOptions = await request.json()
    console.log('Filter projects with:', filters)
    
    // すべてのプロジェクトメタデータを読み込む
    const metadataPath = path.resolve(process.cwd(), '../../data/project_metadata')
    const files = fs.readdirSync(metadataPath)
    
    let projects: any[] = []
    
    for (const file of files) {
      if (!file.endsWith('.json')) continue
      
      try {
        const filePath = path.join(metadataPath, file)
        const metadata = JSON.parse(fs.readFileSync(filePath, 'utf8'))
        const projectId = file.replace('.json', '')
        
        projects.push({
          project_id: projectId,
          name: metadata.name,
          project_type: getProjectType(metadata.tags || []),
          status: metadata.status,
          tech_stack: metadata.dependencies || [],
          description: getDescription(projectId, metadata),
          updated_at: metadata.actual_completion || metadata.estimated_completion || new Date().toISOString(),
          priority: metadata.priority,
          owner: metadata.owner,
          tags: metadata.tags || [],
          progress: metadata.progress || 0
        })
      } catch (error) {
        console.error(`Error loading ${file}:`, error)
      }
    }
    
    // フィルタリング適用
    let filteredProjects = projects
    
    // ステータスフィルタ
    if (filters.status && filters.status.length > 0) {
      filteredProjects = filteredProjects.filter(p => 
        filters.status!.includes(p.status)
      )
    }
    
    // 技術スタックフィルタ（OR条件）
    if (filters.tech_stack && filters.tech_stack.length > 0) {
      filteredProjects = filteredProjects.filter(p => 
        p.tech_stack.some((tech: string) => 
          filters.tech_stack!.some(filterTech => 
            tech.toLowerCase().includes(filterTech.toLowerCase())
          )
        )
      )
    }
    
    // タグフィルタ（OR条件）
    if (filters.tags && filters.tags.length > 0) {
      filteredProjects = filteredProjects.filter(p => 
        p.tags.some((tag: string) => 
          filters.tags!.includes(tag)
        )
      )
    }
    
    // 優先度フィルタ
    if (filters.priority && filters.priority.length > 0) {
      filteredProjects = filteredProjects.filter(p => 
        filters.priority!.includes(p.priority)
      )
    }
    
    // オーナーフィルタ
    if (filters.owner && filters.owner.length > 0) {
      filteredProjects = filteredProjects.filter(p => 
        filters.owner!.includes(p.owner)
      )
    }
    
    // 日付範囲フィルタ
    if (filters.date_from || filters.date_to) {
      filteredProjects = filteredProjects.filter(p => {
        const projectDate = new Date(p.updated_at)
        
        if (filters.date_from && projectDate < new Date(filters.date_from)) {
          return false
        }
        
        if (filters.date_to && projectDate > new Date(filters.date_to)) {
          return false
        }
        
        return true
      })
    }
    
    // 進捗フィルタ
    if (filters.progress_min !== undefined || filters.progress_max !== undefined) {
      filteredProjects = filteredProjects.filter(p => {
        const progress = p.progress * 100
        
        if (filters.progress_min !== undefined && progress < filters.progress_min) {
          return false
        }
        
        if (filters.progress_max !== undefined && progress > filters.progress_max) {
          return false
        }
        
        return true
      })
    }
    
    // 検索フィルタ（名前、説明、技術スタックを検索）
    if (filters.search && filters.search.trim()) {
      const searchTerm = filters.search.toLowerCase()
      filteredProjects = filteredProjects.filter(p => 
        p.name.toLowerCase().includes(searchTerm) ||
        p.description.toLowerCase().includes(searchTerm) ||
        p.tech_stack.some((tech: string) => tech.toLowerCase().includes(searchTerm)) ||
        p.tags.some((tag: string) => tag.toLowerCase().includes(searchTerm))
      )
    }
    
    // フィルタ結果の統計情報も返す
    const stats = {
      total_results: filteredProjects.length,
      by_status: {} as Record<string, number>,
      by_priority: {} as Record<string, number>,
      by_tech_stack: {} as Record<string, number>
    }
    
    filteredProjects.forEach(p => {
      // ステータス別カウント
      stats.by_status[p.status] = (stats.by_status[p.status] || 0) + 1
      
      // 優先度別カウント
      stats.by_priority[p.priority] = (stats.by_priority[p.priority] || 0) + 1
      
      // 技術スタック別カウント
      p.tech_stack.forEach((tech: string) => {
        stats.by_tech_stack[tech] = (stats.by_tech_stack[tech] || 0) + 1
      })
    })
    
    console.log(`Filtered ${filteredProjects.length} projects from ${projects.length} total`)
    
    return NextResponse.json({
      projects: filteredProjects,
      stats,
      applied_filters: filters
    })
    
  } catch (error) {
    console.error('Filter error:', error)
    return NextResponse.json(
      { error: 'Filter operation failed' },
      { status: 500 }
    )
  }
}

// 使用可能なフィルタオプションを返すAPI
export async function GET() {
  try {
    // すべてのプロジェクトから利用可能なオプションを収集
    const metadataPath = path.resolve(process.cwd(), '../../data/project_metadata')
    const files = fs.readdirSync(metadataPath)
    
    const options = {
      statuses: new Set<string>(),
      tech_stack: new Set<string>(),
      tags: new Set<string>(),
      priorities: new Set<string>(),
      owners: new Set<string>()
    }
    
    for (const file of files) {
      if (!file.endsWith('.json')) continue
      
      try {
        const filePath = path.join(metadataPath, file)
        const metadata = JSON.parse(fs.readFileSync(filePath, 'utf8'))
        
        // 各オプションを収集
        if (metadata.status) options.statuses.add(metadata.status)
        if (metadata.priority) options.priorities.add(metadata.priority)
        if (metadata.owner) options.owners.add(metadata.owner)
        
        if (metadata.dependencies) {
          metadata.dependencies.forEach((dep: string) => options.tech_stack.add(dep))
        }
        
        if (metadata.tags) {
          metadata.tags.forEach((tag: string) => options.tags.add(tag))
        }
      } catch (error) {
        console.error(`Error loading ${file}:`, error)
      }
    }
    
    return NextResponse.json({
      available_filters: {
        statuses: Array.from(options.statuses).sort(),
        tech_stack: Array.from(options.tech_stack).sort(),
        tags: Array.from(options.tags).sort(),
        priorities: Array.from(options.priorities).sort(),
        owners: Array.from(options.owners).sort()
      }
    })
    
  } catch (error) {
    console.error('Get filter options error:', error)
    return NextResponse.json(
      { error: 'Failed to get filter options' },
      { status: 500 }
    )
  }
}

// ヘルパー関数
function getProjectType(tags: string[]): string {
  if (tags.includes('web-app') || tags.includes('next.js')) return 'application'
  if (tags.includes('test-project') || tags.includes('tdd')) return 'script'
  if (tags.includes('monitoring') || tags.includes('dashboard')) return 'application'
  return 'application'
}

function getDescription(projectId: string, metadata: any): string {
  const descriptions: Record<string, string> = {
    'image-upload-manager': 'Google Drive統合による画像アップロード・顧客管理システム',
    'elders-guild-web': '4賢者リアルタイム通信システム',
    'frontend-project-manager': 'プロジェクト詳細表示・図表レンダリングシステム',
    'web-monitoring-dashboard': 'リアルタイム監視・分析ダッシュボード',
    'test-calculator-project': 'TDD学習・テスト実装の実習プロジェクト'
  }
  
  return descriptions[projectId] || metadata.description || 'プロジェクトの説明がありません'
}