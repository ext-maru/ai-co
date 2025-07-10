import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

interface ProjectSummary {
  project_id: string
  name: string
  project_type: string
  status: string
  tech_stack: string[]
  description: string
  updated_at: string
}

// プロジェクトメタデータを読み込む
function loadProjectMetadata(): ProjectSummary[] {
  const projects: ProjectSummary[] = []

  // 相対パスで../../data/project_metadataにアクセス
  const metadataPath = path.resolve(process.cwd(), '../../data/project_metadata')

  console.log('Looking for metadata at:', metadataPath)

  try {
    if (fs.existsSync(metadataPath)) {
      const files = fs.readdirSync(metadataPath)
      console.log('Found metadata files:', files)

      for (const file of files) {
        if (file.endsWith('.json')) {
          try {
            const filePath = path.join(metadataPath, file)
            const content = fs.readFileSync(filePath, 'utf8')
            const metadata = JSON.parse(content)

            const projectId = file.replace('.json', '')
            projects.push({
              project_id: projectId,
              name: metadata.name,
              project_type: getProjectType(metadata.tags || []),
              status: metadata.status,
              tech_stack: metadata.dependencies || [],
              description: getDescription(projectId, metadata),
              updated_at: metadata.actual_completion || metadata.estimated_completion || new Date().toISOString()
            })
          } catch (error) {
            console.error(`Error loading metadata for ${file}:`, error)
          }
        }
      }
    } else {
      console.log('Metadata directory not found, using fallback data')
    }
  } catch (error) {
    console.error('Error loading project metadata:', error)
  }

  // メタデータが見つからない場合のフォールバック
  if (projects.length === 0) {
    console.log('Using fallback projects data')
    return getFallbackProjects()
  }

  return projects
}

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

function getFallbackProjects(): ProjectSummary[] {
  return [
    {
      project_id: 'image-upload-manager',
      name: '画像アップロード管理システム',
      project_type: 'application',
      status: 'completed',
      tech_stack: ['Flask', 'Google Drive API', 'SQLite', 'Docker'],
      description: 'Google Drive統合による画像アップロード・顧客管理システム',
      updated_at: '2025-07-10T00:44:29.223057'
    },
    {
      project_id: 'elders-guild-web',
      name: 'エルダーズギルド Webシステム',
      project_type: 'application',
      status: 'completed',
      tech_stack: ['Next.js', 'FastAPI', 'WebSocket', 'PostgreSQL'],
      description: '4賢者リアルタイム通信システム',
      updated_at: '2025-07-10T17:15:00.000000'
    },
    {
      project_id: 'frontend-project-manager',
      name: 'フロントエンドプロジェクト管理',
      project_type: 'application',
      status: 'development',
      tech_stack: ['Next.js', 'TypeScript', 'Tailwind CSS', 'Mermaid'],
      description: 'プロジェクト詳細表示・図表レンダリングシステム',
      updated_at: '2025-07-10T17:20:00.000000'
    },
    {
      project_id: 'web-monitoring-dashboard',
      name: 'Web監視ダッシュボード',
      project_type: 'application',
      status: 'development',
      tech_stack: ['Flask', 'React', 'Vite', 'WebSocket'],
      description: 'リアルタイム監視・分析ダッシュボード',
      updated_at: '2025-07-10T16:00:00.000000'
    },
    {
      project_id: 'test-calculator-project',
      name: 'テスト計算機プロジェクト',
      project_type: 'script',
      status: 'completed',
      tech_stack: ['Python', 'Flask', 'TDD'],
      description: 'TDD学習・テスト実装の実習プロジェクト',
      updated_at: '2025-07-10T17:10:00.000000'
    }
  ]
}

export async function GET() {
  try {
    console.log('Projects API called')
    const projects = loadProjectMetadata()
    console.log(`Returning ${projects.length} projects`)
    return NextResponse.json(projects)
  } catch (error) {
    console.error('API Error:', error)
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 })
  }
}

// 新規プロジェクト作成
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    console.log('Creating new project:', body)

    // 必須フィールドの検証
    if (!body.name || !body.project_id) {
      return NextResponse.json(
        { error: 'name and project_id are required' },
        { status: 400 }
      )
    }

    // メタデータファイルパス
    const metadataPath = path.resolve(process.cwd(), '../../data/project_metadata', `${body.project_id}.json`)

    // 既存チェック
    if (fs.existsSync(metadataPath)) {
      return NextResponse.json(
        { error: 'Project already exists' },
        { status: 409 }
      )
    }

    // 新規メタデータ作成
    const newMetadata = {
      name: body.name,
      status: body.status || 'development',
      priority: body.priority || 'medium',
      owner: body.owner || 'claude_elder',
      elder_role: body.elder_role || 'project_manager',
      tags: body.tags || [],
      dependencies: body.dependencies || [],
      progress: body.progress || 0,
      estimated_completion: body.estimated_completion || null,
      actual_completion: null,
      description: body.description || ''
    }

    // メタデータディレクトリが存在しない場合は作成
    const metadataDir = path.dirname(metadataPath)
    if (!fs.existsSync(metadataDir)) {
      fs.mkdirSync(metadataDir, { recursive: true })
    }

    // ファイルに保存
    fs.writeFileSync(metadataPath, JSON.stringify(newMetadata, null, 2))

    // プロジェクトディレクトリ作成（オプション）
    if (body.create_directory) {
      const projectDir = path.resolve(process.cwd(), '..', body.project_id)
      if (!fs.existsSync(projectDir)) {
        fs.mkdirSync(projectDir, { recursive: true })

        // README.md を作成
        const readmeContent = `# ${body.name}\n\n${body.description || 'プロジェクトの説明'}\n\n## Status: ${body.status || 'development'}\n`
        fs.writeFileSync(path.join(projectDir, 'README.md'), readmeContent)
      }
    }

    console.log('Project created successfully:', body.project_id)
    return NextResponse.json({
      success: true,
      project_id: body.project_id,
      message: 'Project created successfully'
    }, { status: 201 })

  } catch (error) {
    console.error('Create project error:', error)
    return NextResponse.json(
      { error: 'Failed to create project' },
      { status: 500 }
    )
  }
}
