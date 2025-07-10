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

// お気に入りを保存
function saveFavorites(favorites: Record<string, string[]>): void {
  const filePath = getFavoritesFilePath()
  fs.writeFileSync(filePath, JSON.stringify(favorites, null, 2))
}

// お気に入りの追加・削除
export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const body = await request.json()
    const userId = body.user_id || 'default_user'
    
    console.log('Toggling favorite for project:', params.id, 'user:', userId)
    
    const favorites = loadFavorites()
    
    // ユーザーのお気に入りリストを取得（なければ作成）
    if (!favorites[userId]) {
      favorites[userId] = []
    }
    
    const userFavorites = favorites[userId]
    const projectIndex = userFavorites.indexOf(params.id)
    
    let action: string
    
    if (projectIndex === -1) {
      // お気に入りに追加
      userFavorites.push(params.id)
      action = 'added'
    } else {
      // お気に入りから削除
      userFavorites.splice(projectIndex, 1)
      action = 'removed'
    }
    
    favorites[userId] = userFavorites
    saveFavorites(favorites)
    
    console.log(`Project ${action} to/from favorites:`, params.id)
    return NextResponse.json({
      success: true,
      project_id: params.id,
      action,
      is_favorite: action === 'added'
    })
    
  } catch (error) {
    console.error('Toggle favorite error:', error)
    return NextResponse.json(
      { error: 'Failed to toggle favorite' },
      { status: 500 }
    )
  }
}

// お気に入り状態を取得
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const url = new URL(request.url)
    const userId = url.searchParams.get('user_id') || 'default_user'
    
    console.log('Getting favorite status for project:', params.id, 'user:', userId)
    
    const favorites = loadFavorites()
    const userFavorites = favorites[userId] || []
    const isFavorite = userFavorites.includes(params.id)
    
    return NextResponse.json({
      project_id: params.id,
      user_id: userId,
      is_favorite: isFavorite
    })
    
  } catch (error) {
    console.error('Get favorite status error:', error)
    return NextResponse.json(
      { error: 'Failed to get favorite status' },
      { status: 500 }
    )
  }
}