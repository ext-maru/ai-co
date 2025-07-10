import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

// タグの追加・削除
export async function PATCH(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const body = await request.json()
    console.log('Updating tags for project:', params.id)
    
    // メタデータファイルパス
    const metadataPath = path.resolve(process.cwd(), '../../data/project_metadata', `${params.id}.json`)
    
    // 存在チェック
    if (!fs.existsSync(metadataPath)) {
      return NextResponse.json(
        { error: 'Project not found' },
        { status: 404 }
      )
    }
    
    // 既存メタデータを読み込む
    const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'))
    
    // タグ操作
    if (body.action === 'add' && body.tags) {
      // タグ追加
      const currentTags = new Set(metadata.tags || [])
      body.tags.forEach((tag: string) => currentTags.add(tag))
      metadata.tags = Array.from(currentTags)
      
    } else if (body.action === 'remove' && body.tags) {
      // タグ削除
      const currentTags = new Set(metadata.tags || [])
      body.tags.forEach((tag: string) => currentTags.delete(tag))
      metadata.tags = Array.from(currentTags)
      
    } else if (body.action === 'set' && body.tags) {
      // タグ置き換え
      metadata.tags = body.tags
      
    } else {
      return NextResponse.json(
        { error: 'Invalid action or missing tags' },
        { status: 400 }
      )
    }
    
    // 更新日時を記録
    metadata.last_updated = new Date().toISOString()
    
    // ファイルに保存
    fs.writeFileSync(metadataPath, JSON.stringify(metadata, null, 2))
    
    console.log('Tags updated successfully for project:', params.id)
    return NextResponse.json({
      success: true,
      project_id: params.id,
      tags: metadata.tags,
      action: body.action
    })
    
  } catch (error) {
    console.error('Update tags error:', error)
    return NextResponse.json(
      { error: 'Failed to update tags' },
      { status: 500 }
    )
  }
}

// タグ一覧取得
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    console.log('Getting tags for project:', params.id)
    
    // メタデータファイルパス
    const metadataPath = path.resolve(process.cwd(), '../../data/project_metadata', `${params.id}.json`)
    
    // 存在チェック
    if (!fs.existsSync(metadataPath)) {
      return NextResponse.json(
        { error: 'Project not found' },
        { status: 404 }
      )
    }
    
    // 既存メタデータを読み込む
    const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'))
    
    return NextResponse.json({
      project_id: params.id,
      tags: metadata.tags || []
    })
    
  } catch (error) {
    console.error('Get tags error:', error)
    return NextResponse.json(
      { error: 'Failed to get tags' },
      { status: 500 }
    )
  }
}