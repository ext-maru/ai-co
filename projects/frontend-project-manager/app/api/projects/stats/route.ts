import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

interface Stats {
  total_projects: number
  by_type: Record<string, number>
  by_status: Record<string, number>
  by_tech_stack: Record<string, number>
  most_used_tech?: [string, number]
}

// プロジェクト統計を生成
function generateStats(): Stats {
  const projects = loadProjectsForStats()
  
  const stats: Stats = {
    total_projects: projects.length,
    by_type: {},
    by_status: {},
    by_tech_stack: {}
  }
  
  // 統計データを集計
  projects.forEach(project => {
    // プロジェクトタイプ別
    stats.by_type[project.project_type] = (stats.by_type[project.project_type] || 0) + 1
    
    // ステータス別
    stats.by_status[project.status] = (stats.by_status[project.status] || 0) + 1
    
    // 技術スタック別
    project.tech_stack.forEach(tech => {
      stats.by_tech_stack[tech] = (stats.by_tech_stack[tech] || 0) + 1
    })
  })
  
  // 最も使用されている技術を特定
  if (Object.keys(stats.by_tech_stack).length > 0) {
    const sortedTech = Object.entries(stats.by_tech_stack)
      .sort(([,a], [,b]) => b - a)
    stats.most_used_tech = sortedTech[0] as [string, number]
  }
  
  return stats
}

function loadProjectsForStats() {
  const metadataPath = path.resolve(process.cwd(), '../../data/project_metadata')
  const projects: any[] = []
  
  console.log('Loading stats from:', metadataPath)
  
  try {
    if (fs.existsSync(metadataPath)) {
      const files = fs.readdirSync(metadataPath)
      
      for (const file of files) {
        if (file.endsWith('.json')) {
          try {
            const filePath = path.join(metadataPath, file)
            const content = fs.readFileSync(filePath, 'utf8')
            const metadata = JSON.parse(content)
            
            const projectId = file.replace('.json', '')
            projects.push({
              project_id: projectId,
              project_type: getProjectType(metadata.tags || []),
              status: metadata.status,
              tech_stack: metadata.dependencies || []
            })
          } catch (error) {
            console.error(`Error loading stats for ${file}:`, error)
          }
        }
      }
    } else {
      console.log('Stats: metadata directory not found, using fallback')
    }
  } catch (error) {
    console.error('Error loading project stats:', error)
  }
  
  // フォールバックデータ
  if (projects.length === 0) {
    console.log('Using fallback stats data')
    return [
      {
        project_id: 'image-upload-manager',
        project_type: 'application',
        status: 'completed',
        tech_stack: ['Flask', 'Google Drive API', 'SQLite', 'Docker']
      },
      {
        project_id: 'elders-guild-web',
        project_type: 'application',
        status: 'completed',
        tech_stack: ['Next.js', 'FastAPI', 'WebSocket', 'PostgreSQL']
      },
      {
        project_id: 'frontend-project-manager',
        project_type: 'application',
        status: 'development',
        tech_stack: ['Next.js', 'TypeScript', 'Tailwind CSS', 'Mermaid']
      },
      {
        project_id: 'web-monitoring-dashboard',
        project_type: 'application',
        status: 'development',
        tech_stack: ['Flask', 'React', 'Vite', 'WebSocket']
      },
      {
        project_id: 'test-calculator-project',
        project_type: 'script',
        status: 'completed',
        tech_stack: ['Python', 'Flask', 'TDD']
      }
    ]
  }
  
  return projects
}

function getProjectType(tags: string[]): string {
  if (tags.includes('web-app') || tags.includes('next.js')) return 'application'
  if (tags.includes('test-project') || tags.includes('tdd')) return 'script'
  if (tags.includes('monitoring') || tags.includes('dashboard')) return 'application'
  return 'application'
}

export async function GET() {
  try {
    console.log('Stats API called')
    const stats = generateStats()
    console.log('Generated stats:', stats)
    return NextResponse.json(stats)
  } catch (error) {
    console.error('Stats API Error:', error)
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 })
  }
}