import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

// プロジェクトデータのエクスポート
export async function GET(request: NextRequest) {
  try {
    const url = new URL(request.url)
    const format = url.searchParams.get('format') || 'json'
    const projectIds = url.searchParams.get('projects')?.split(',').filter(Boolean)
    
    console.log('Export requested:', { format, projectIds })
    
    // すべてのプロジェクトメタデータを読み込む
    const metadataPath = path.resolve(process.cwd(), '../../data/project_metadata')
    const files = fs.readdirSync(metadataPath)
    
    const projects: any[] = []
    
    for (const file of files) {
      if (!file.endsWith('.json')) continue
      
      const projectId = file.replace('.json', '')
      
      // 特定のプロジェクトのみエクスポートする場合
      if (projectIds && projectIds.length > 0 && !projectIds.includes(projectId)) {
        continue
      }
      
      try {
        const filePath = path.join(metadataPath, file)
        const metadata = JSON.parse(fs.readFileSync(filePath, 'utf8'))
        
        projects.push({
          project_id: projectId,
          ...metadata
        })
      } catch (error) {
        console.error(`Error loading ${file}:`, error)
      }
    }
    
    // フォーマットに応じてエクスポート
    switch (format.toLowerCase()) {
      case 'json':
        return NextResponse.json({
          export_date: new Date().toISOString(),
          total_projects: projects.length,
          projects
        })
        
      case 'csv':
        const csv = generateCSV(projects)
        return new NextResponse(csv, {
          headers: {
            'Content-Type': 'text/csv',
            'Content-Disposition': `attachment; filename="projects_export_${new Date().toISOString().split('T')[0]}.csv"`
          }
        })
        
      case 'markdown':
        const markdown = generateMarkdown(projects)
        return new NextResponse(markdown, {
          headers: {
            'Content-Type': 'text/markdown',
            'Content-Disposition': `attachment; filename="projects_export_${new Date().toISOString().split('T')[0]}.md"`
          }
        })
        
      default:
        return NextResponse.json(
          { error: 'Unsupported format. Use json, csv, or markdown' },
          { status: 400 }
        )
    }
    
  } catch (error) {
    console.error('Export error:', error)
    return NextResponse.json(
      { error: 'Export failed' },
      { status: 500 }
    )
  }
}

// CSV生成
function generateCSV(projects: any[]): string {
  const headers = [
    'Project ID',
    'Name',
    'Status',
    'Priority',
    'Owner',
    'Progress',
    'Tech Stack',
    'Tags',
    'Created',
    'Updated'
  ]
  
  const rows = projects.map(p => [
    p.project_id,
    `"${p.name}"`,
    p.status,
    p.priority,
    p.owner,
    (p.progress * 100).toFixed(0) + '%',
    `"${(p.dependencies || []).join(', ')}"`,
    `"${(p.tags || []).join(', ')}"`,
    p.estimated_completion || 'N/A',
    p.actual_completion || p.last_updated || 'N/A'
  ])
  
  return [
    headers.join(','),
    ...rows.map(row => row.join(','))
  ].join('\n')
}

// Markdown生成
function generateMarkdown(projects: any[]): string {
  let markdown = `# エルダーズギルド プロジェクトポートフォリオ

**エクスポート日時**: ${new Date().toISOString()}  
**総プロジェクト数**: ${projects.length}

## 📊 統計情報

| ステータス | プロジェクト数 |
|-----------|--------------|
`

  // ステータス別統計
  const statusCounts: Record<string, number> = {}
  projects.forEach(p => {
    statusCounts[p.status] = (statusCounts[p.status] || 0) + 1
  })
  
  Object.entries(statusCounts).forEach(([status, count]) => {
    markdown += `| ${status} | ${count} |\n`
  })
  
  markdown += `\n## 📁 プロジェクト一覧\n\n`
  
  // プロジェクトリスト
  projects.forEach(p => {
    markdown += `### ${p.name}
- **ID**: ${p.project_id}
- **ステータス**: ${p.status}
- **優先度**: ${p.priority}
- **進捗**: ${(p.progress * 100).toFixed(0)}%
- **技術スタック**: ${(p.dependencies || []).join(', ')}
- **タグ**: ${(p.tags || []).join(', ')}
- **説明**: ${p.description || 'なし'}

---

`
  })
  
  return markdown
}