import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

// 個別プロジェクトのエクスポート
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const url = new URL(request.url)
    const format = url.searchParams.get('format') || 'json'
    
    console.log('Export project:', params.id, 'format:', format)
    
    // メタデータを読み込む
    const metadataPath = path.resolve(process.cwd(), '../../data/project_metadata', `${params.id}.json`)
    
    if (!fs.existsSync(metadataPath)) {
      return NextResponse.json(
        { error: 'Project not found' },
        { status: 404 }
      )
    }
    
    const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'))
    const projectPath = path.resolve(process.cwd(), '..', params.id)
    
    // プロジェクト詳細データを構築
    const projectData = {
      project_id: params.id,
      ...metadata,
      export_date: new Date().toISOString()
    }
    
    // フォーマットに応じてエクスポート
    switch (format.toLowerCase()) {
      case 'json':
        return NextResponse.json(projectData, {
          headers: {
            'Content-Disposition': `attachment; filename="${params.id}_export.json"`
          }
        })
        
      case 'markdown':
        const markdown = generateProjectMarkdown(projectData)
        return new NextResponse(markdown, {
          headers: {
            'Content-Type': 'text/markdown',
            'Content-Disposition': `attachment; filename="${params.id}_export.md"`
          }
        })
        
      case 'report':
        const report = generateProjectReport(projectData)
        return new NextResponse(report, {
          headers: {
            'Content-Type': 'text/markdown',
            'Content-Disposition': `attachment; filename="${params.id}_report.md"`
          }
        })
        
      default:
        return NextResponse.json(
          { error: 'Unsupported format. Use json, markdown, or report' },
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

// プロジェクトMarkdown生成
function generateProjectMarkdown(project: any): string {
  return `# ${project.name}

**プロジェクトID**: ${project.project_id}  
**エクスポート日時**: ${project.export_date}

## 📋 基本情報

| 項目 | 内容 |
|------|------|
| ステータス | ${project.status} |
| 優先度 | ${project.priority} |
| オーナー | ${project.owner} |
| 役割 | ${project.elder_role} |
| 進捗 | ${(project.progress * 100).toFixed(0)}% |

## 📝 説明

${project.description || 'プロジェクトの説明がありません'}

## 🛠️ 技術スタック

${(project.dependencies || []).map((dep: string) => `- ${dep}`).join('\n')}

## 🏷️ タグ

${(project.tags || []).map((tag: string) => `- ${tag}`).join('\n')}

## 📅 スケジュール

- **見積完了日**: ${project.estimated_completion || '未設定'}
- **実際の完了日**: ${project.actual_completion || '未完了'}
- **最終更新**: ${project.last_updated || 'N/A'}

---

*このドキュメントは、エルダーズギルド プロジェクト管理システムから自動生成されました。*
`
}

// プロジェクトレポート生成
function generateProjectReport(project: any): string {
  const statusEmoji = {
    'completed': '✅',
    'development': '🚧',
    'planning': '📋',
    'deleted': '🗑️'
  }
  
  const priorityEmoji = {
    'high': '🔴',
    'medium': '🟡',
    'low': '🟢'
  }
  
  return `# 📊 プロジェクトレポート: ${project.name}

**レポート生成日時**: ${new Date().toISOString()}  
**プロジェクトID**: \`${project.project_id}\`

## 🎯 エグゼクティブサマリー

${statusEmoji[project.status] || '⚪'} **ステータス**: ${project.status}  
${priorityEmoji[project.priority] || '⚪'} **優先度**: ${project.priority}  
📈 **進捗**: ${(project.progress * 100).toFixed(0)}%

## 📋 プロジェクト概要

### 説明
${project.description || 'プロジェクトの説明がありません'}

### 主要ステークホルダー
- **プロジェクトオーナー**: ${project.owner}
- **エルダー役割**: ${project.elder_role}

## 🛠️ 技術的詳細

### 使用技術
\`\`\`
${(project.dependencies || []).join('\n')}
\`\`\`

### プロジェクト分類
${(project.tags || []).map((tag: string) => `\`${tag}\``).join(' ')}

## 📈 進捗分析

### 現在の状況
- 進捗率: **${(project.progress * 100).toFixed(0)}%**
- ステータス: **${project.status}**

### タイムライン
| マイルストーン | 日付 |
|--------------|------|
| プロジェクト開始 | ${project.estimated_completion ? new Date(project.estimated_completion).toISOString().split('T')[0] : 'N/A'} |
| 完了予定 | ${project.estimated_completion || '未設定'} |
| 実際の完了 | ${project.actual_completion || '未完了'} |

## 🎯 今後のアクション

${project.status === 'completed' ? 
  '✅ このプロジェクトは完了しています。' :
  project.status === 'development' ?
    `### 推奨事項
1. 開発を継続し、予定通りの完了を目指す
2. 定期的な進捗レビューを実施
3. リスク要因の早期特定と対処` :
    '### 推奨事項\n1. プロジェクト計画の詳細化\n2. リソースの割り当て\n3. スケジュールの確定'
}

## 📊 メトリクス

\`\`\`
優先度: ${project.priority}
進捗: ${(project.progress * 100).toFixed(0)}%
技術数: ${(project.dependencies || []).length}
タグ数: ${(project.tags || []).length}
\`\`\`

---

**エルダーズギルド プロジェクト管理システム**  
*品質第一 × 階層秩序*
`
}