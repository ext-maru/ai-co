import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'
import { exec } from 'child_process'
import { promisify } from 'util'

const execAsync = promisify(exec)

interface ProjectDetail {
  project_id: string
  name: string
  path: string
  project_type: string
  status: string
  tech_stack: string[]
  description: string
  created_at: string
  updated_at: string
  code_structure?: {
    total_lines: number
    total_files: number
    classes: string[]
    functions: string[]
    complexity_score: number
    languages: Record<string, number>
  }
  git_metrics?: {
    total_commits: number
    contributors: string[]
    last_commit: string
    creation_date: string
    active_branches: number
    commit_frequency: number
  }
  dependencies: Array<{
    name: string
    version?: string
    type: string
  }>
  documentation?: {
    overview: string
    architecture: string
    setup_guide: string
    api_reference: string
    usage_examples: string
    diagrams: Record<string, string>
    quality_score: number
  }
}

// プロジェクトの詳細情報を取得
async function getProjectDetail(projectId: string): Promise<ProjectDetail | null> {
  try {
    // メタデータファイルから基本情報を読み込む
    const metadataPath = path.resolve(process.cwd(), '../../data/project_metadata', `${projectId}.json`)
    
    if (!fs.existsSync(metadataPath)) {
      console.log(`Metadata not found for project: ${projectId}`)
      return null
    }
    
    const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'))
    
    // プロジェクトパスを決定
    const projectPath = path.resolve(process.cwd(), '..', projectId)
    
    // 基本情報
    const detail: ProjectDetail = {
      project_id: projectId,
      name: metadata.name,
      path: `/projects/${projectId}`,
      project_type: getProjectType(metadata.tags || []),
      status: metadata.status,
      tech_stack: metadata.dependencies || [],
      description: getDescription(projectId, metadata),
      created_at: metadata.estimated_completion || new Date().toISOString(),
      updated_at: metadata.actual_completion || metadata.estimated_completion || new Date().toISOString(),
      dependencies: []
    }
    
    // コード構造の分析（簡易版）
    if (fs.existsSync(projectPath)) {
      detail.code_structure = await analyzeCodeStructure(projectPath)
      detail.git_metrics = await analyzeGitMetrics(projectPath)
      detail.dependencies = await analyzeDependencies(projectPath, projectId)
    }
    
    // ドキュメント情報（存在する場合）
    const docPath = path.join(projectPath, 'documentation.json')
    if (fs.existsSync(docPath)) {
      detail.documentation = JSON.parse(fs.readFileSync(docPath, 'utf8'))
    }
    
    return detail
    
  } catch (error) {
    console.error('Error getting project detail:', error)
    return null
  }
}

// コード構造を分析
async function analyzeCodeStructure(projectPath: string) {
  const structure = {
    total_lines: 0,
    total_files: 0,
    classes: [] as string[],
    functions: [] as string[],
    complexity_score: 0,
    languages: {} as Record<string, number>
  }
  
  try {
    // ファイル数をカウント（簡易版）
    const files = getAllFiles(projectPath)
    structure.total_files = files.length
    
    // 言語別ファイル数
    files.forEach(file => {
      const ext = path.extname(file).toLowerCase()
      const lang = getLanguageFromExt(ext)
      if (lang) {
        structure.languages[lang] = (structure.languages[lang] || 0) + 1
      }
    })
    
    // 行数を概算
    structure.total_lines = structure.total_files * 100 // 簡易推定
    
    // 複雑度スコア（簡易計算）
    structure.complexity_score = Math.min(100, structure.total_files * 2)
    
  } catch (error) {
    console.error('Error analyzing code structure:', error)
  }
  
  return structure
}

// Git メトリクスを分析
async function analyzeGitMetrics(projectPath: string) {
  const metrics = {
    total_commits: 0,
    contributors: [] as string[],
    last_commit: new Date().toISOString(),
    creation_date: new Date().toISOString(),
    active_branches: 1,
    commit_frequency: 0
  }
  
  try {
    // Git リポジトリかチェック
    if (!fs.existsSync(path.join(projectPath, '.git'))) {
      return metrics
    }
    
    // コミット数を取得（エラーハンドリング付き）
    try {
      const { stdout: commitCount } = await execAsync('git rev-list --count HEAD', { cwd: projectPath })
      metrics.total_commits = parseInt(commitCount.trim()) || 0
    } catch (e) {
      console.log('Git not initialized or no commits')
    }
    
  } catch (error) {
    console.error('Error analyzing git metrics:', error)
  }
  
  return metrics
}

// 依存関係を分析
async function analyzeDependencies(projectPath: string, projectId: string) {
  const dependencies: Array<{ name: string; version?: string; type: string }> = []
  
  try {
    // package.json (Node.js)
    const packageJsonPath = path.join(projectPath, 'package.json')
    if (fs.existsSync(packageJsonPath)) {
      const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'))
      
      if (packageJson.dependencies) {
        Object.entries(packageJson.dependencies).forEach(([name, version]) => {
          dependencies.push({ name, version: version as string, type: 'runtime' })
        })
      }
      
      if (packageJson.devDependencies) {
        Object.entries(packageJson.devDependencies).forEach(([name, version]) => {
          dependencies.push({ name, version: version as string, type: 'development' })
        })
      }
    }
    
    // requirements.txt (Python)
    const requirementsPath = path.join(projectPath, 'requirements.txt')
    if (fs.existsSync(requirementsPath)) {
      const requirements = fs.readFileSync(requirementsPath, 'utf8').split('\n')
      requirements.forEach(req => {
        const trimmed = req.trim()
        if (trimmed && !trimmed.startsWith('#')) {
          const [name, version] = trimmed.split('==')
          dependencies.push({ name, version: version || 'latest', type: 'runtime' })
        }
      })
    }
    
  } catch (error) {
    console.error('Error analyzing dependencies:', error)
  }
  
  return dependencies
}

// ヘルパー関数
function getAllFiles(dirPath: string, arrayOfFiles: string[] = []): string[] {
  try {
    const files = fs.readdirSync(dirPath)
    
    files.forEach((file) => {
      const filePath = path.join(dirPath, file)
      
      // 除外するディレクトリ
      if (['node_modules', '.git', 'dist', 'build', '.next', '__pycache__'].includes(file)) {
        return
      }
      
      if (fs.statSync(filePath).isDirectory()) {
        arrayOfFiles = getAllFiles(filePath, arrayOfFiles)
      } else {
        arrayOfFiles.push(filePath)
      }
    })
  } catch (error) {
    console.error('Error getting files:', error)
  }
  
  return arrayOfFiles
}

function getLanguageFromExt(ext: string): string | null {
  const langMap: Record<string, string> = {
    '.ts': 'TypeScript',
    '.tsx': 'TypeScript',
    '.js': 'JavaScript',
    '.jsx': 'JavaScript',
    '.py': 'Python',
    '.java': 'Java',
    '.cpp': 'C++',
    '.c': 'C',
    '.cs': 'C#',
    '.go': 'Go',
    '.rs': 'Rust',
    '.php': 'PHP',
    '.rb': 'Ruby',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.html': 'HTML',
    '.css': 'CSS',
    '.scss': 'SCSS',
    '.json': 'JSON',
    '.xml': 'XML',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.md': 'Markdown'
  }
  
  return langMap[ext] || null
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

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    console.log('Project detail API called for:', params.id)
    
    const projectDetail = await getProjectDetail(params.id)
    
    if (!projectDetail) {
      return NextResponse.json(
        { error: 'Project not found' },
        { status: 404 }
      )
    }
    
    console.log('Returning project detail for:', params.id)
    return NextResponse.json(projectDetail)
    
  } catch (error) {
    console.error('Project detail API error:', error)
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    )
  }
}