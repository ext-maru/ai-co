import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

// プロジェクト更新（PATCH）
export async function PATCH(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const body = await request.json()
    console.log('Updating project:', params.id, body)
    
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
    const currentMetadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'))
    
    // 更新可能なフィールドのみ更新
    const updatableFields = [
      'name', 'status', 'priority', 'owner', 'elder_role',
      'tags', 'dependencies', 'progress', 'estimated_completion',
      'actual_completion', 'description'
    ]
    
    const updatedMetadata = { ...currentMetadata }
    
    updatableFields.forEach(field => {
      if (body[field] !== undefined) {
        updatedMetadata[field] = body[field]
      }
    })
    
    // 更新日時を記録
    updatedMetadata.last_updated = new Date().toISOString()
    
    // ステータスが completed に変更された場合、実際の完了日を設定
    if (body.status === 'completed' && currentMetadata.status !== 'completed') {
      updatedMetadata.actual_completion = new Date().toISOString()
      updatedMetadata.progress = 1.0
    }
    
    // ファイルに保存
    fs.writeFileSync(metadataPath, JSON.stringify(updatedMetadata, null, 2))
    
    console.log('Project updated successfully:', params.id)
    return NextResponse.json({
      success: true,
      project_id: params.id,
      message: 'Project updated successfully',
      updated_fields: Object.keys(body)
    })
    
  } catch (error) {
    console.error('Update project error:', error)
    return NextResponse.json(
      { error: 'Failed to update project' },
      { status: 500 }
    )
  }
}

// プロジェクト削除（DELETE）
export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    console.log('Deleting project:', params.id)
    
    // メタデータファイルパス
    const metadataPath = path.resolve(process.cwd(), '../../data/project_metadata', `${params.id}.json`)
    
    // 存在チェック
    if (!fs.existsSync(metadataPath)) {
      return NextResponse.json(
        { error: 'Project not found' },
        { status: 404 }
      )
    }
    
    // URLパラメータで物理削除か論理削除か判定
    const url = new URL(request.url)
    const hardDelete = url.searchParams.get('hard') === 'true'
    
    if (hardDelete) {
      // 物理削除
      fs.unlinkSync(metadataPath)
      
      // プロジェクトディレクトリも削除するか確認
      const deleteDirectory = url.searchParams.get('delete_directory') === 'true'
      if (deleteDirectory) {
        const projectDir = path.resolve(process.cwd(), '..', params.id)
        if (fs.existsSync(projectDir)) {
          // 安全のため、プロジェクトディレクトリの削除は実装しない
          console.warn('Directory deletion requested but not implemented for safety')
        }
      }
      
      console.log('Project hard deleted:', params.id)
      return NextResponse.json({
        success: true,
        project_id: params.id,
        message: 'Project permanently deleted'
      })
      
    } else {
      // 論理削除（ステータスを deleted に変更）
      const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'))
      metadata.status = 'deleted'
      metadata.deleted_at = new Date().toISOString()
      
      fs.writeFileSync(metadataPath, JSON.stringify(metadata, null, 2))
      
      console.log('Project soft deleted:', params.id)
      return NextResponse.json({
        success: true,
        project_id: params.id,
        message: 'Project marked as deleted'
      })
    }
    
  } catch (error) {
    console.error('Delete project error:', error)
    return NextResponse.json(
      { error: 'Failed to delete project' },
      { status: 500 }
    )
  }
}