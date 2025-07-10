import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

// お気に入りファイルのパスを取得
function getFavoritesFilePath(): string {
  const favoritesDir = path.resolve(process.cwd(), '../../data')
  if (!fs.existsSync(favoritesDir)) {
    fs.mkdirSync(favoritesDir, { recursive: true })
  }
  return path.join(favoritesDir, 'project_favorites.json')
}

// お気に入りを読み込む
function loadFavorites(): Record<string, string[]> {
  const filePath = getFavoritesFilePath()
  
  if (!fs.existsSync(filePath)) {
    return {}
  }
  
  try {
    const data = fs.readFileSync(filePath, 'utf8')
    return JSON.parse(data)
  } catch (error) {
    console.error('Error loading favorites:', error)
    return {}
  }
}

// ユーザーのお気に入りプロジェクト一覧を取得
export async function GET(request: NextRequest) {
  try {
    const url = new URL(request.url)
    const userId = url.searchParams.get('user_id') || 'default_user'
    
    console.log('Getting favorite projects for user:', userId)
    
    const favorites = loadFavorites()
    const userFavorites = favorites[userId] || []
    
    // お気に入りプロジェクトの詳細情報を取得
    const metadataPath = path.resolve(process.cwd(), '../../data/project_metadata')
    const favoriteProjects: any[] = []
    
    for (const projectId of userFavorites) {
      try {
        const projectMetadataPath = path.join(metadataPath, `${projectId}.json`)
        
        if (fs.existsSync(projectMetadataPath)) {
          const metadata = JSON.parse(fs.readFileSync(projectMetadataPath, 'utf8'))
          
          favoriteProjects.push({
            project_id: projectId,
            name: metadata.name,
            project_type: getProjectType(metadata.tags || []),
            status: metadata.status,
            tech_stack: metadata.dependencies || [],
            description: getDescription(projectId, metadata),
            updated_at: metadata.actual_completion || metadata.estimated_completion || new Date().toISOString(),
            is_favorite: true
          })
        }
      } catch (error) {
        console.error(`Error loading project ${projectId}:`, error)
      }
    }
    
    return NextResponse.json({
      user_id: userId,
      total_favorites: favoriteProjects.length,
      projects: favoriteProjects
    })
    
  } catch (error) {
    console.error('Get favorite projects error:', error)
    return NextResponse.json(
      { error: 'Failed to get favorite projects' },
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