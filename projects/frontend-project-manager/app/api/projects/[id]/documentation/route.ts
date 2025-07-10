import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

interface Documentation {
  overview: string
  architecture: string
  setup_guide: string
  api_reference: string
  usage_examples: string
  diagrams: {
    architecture?: string
    dataFlow?: string
    deployment?: string
  }
  quality_score: number
  generated_at: string
}

// AI風ドキュメント生成（実際にはテンプレートベース）
async function generateDocumentation(projectId: string): Promise<Documentation | null> {
  try {
    // メタデータ読み込み
    const metadataPath = path.resolve(process.cwd(), '../../data/project_metadata', `${projectId}.json`)

    if (!fs.existsSync(metadataPath)) {
      return null
    }

    const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'))
    const projectPath = path.resolve(process.cwd(), '..', projectId)

    // プロジェクト情報から自動生成
    const doc: Documentation = {
      overview: generateOverview(projectId, metadata),
      architecture: generateArchitecture(projectId, metadata),
      setup_guide: generateSetupGuide(projectId, metadata),
      api_reference: generateApiReference(projectId, metadata),
      usage_examples: generateUsageExamples(projectId, metadata),
      diagrams: generateDiagrams(projectId, metadata),
      quality_score: calculateQualityScore(metadata),
      generated_at: new Date().toISOString()
    }

    // ドキュメントを保存
    const docPath = path.join(projectPath, 'documentation.json')
    if (fs.existsSync(projectPath)) {
      fs.writeFileSync(docPath, JSON.stringify(doc, null, 2))
    }

    return doc

  } catch (error) {
    console.error('Error generating documentation:', error)
    return null
  }
}

// 概要生成
function generateOverview(projectId: string, metadata: any): string {
  const templates: Record<string, string> = {
    'image-upload-manager': `# ${metadata.name}

## 概要
本システムは、Google Drive APIと統合された画像アップロード管理システムです。顧客情報と画像ファイルを効率的に管理し、クラウドストレージとの連携により、大容量ファイルの取り扱いを可能にします。

## 主要機能
- 画像ファイルのアップロード・管理
- Google Drive統合によるクラウドストレージ
- 顧客情報管理
- 管理者ダッシュボード
- レスポンシブWebインターフェース

## 技術的特徴
- Flask フレームワークによる軽量実装
- SQLiteデータベースによるローカルデータ管理
- Google OAuth2認証
- Docker対応による環境独立性`,

    'elders-guild-web': `# ${metadata.name}

## 概要
エルダーズギルドの中核となる4賢者システムのリアルタイム通信プラットフォームです。Next.js 14とFastAPIを活用し、WebSocketによる双方向通信を実現しています。

## 4賢者システム
- **ナレッジ賢者**: 知識管理・ドキュメント作成
- **タスク賢者**: プロジェクト管理・ワークフロー
- **インシデント賢者**: 監視・アラート・自動対応
- **サーチ賢者**: RAG搭載インテリジェント検索

## アーキテクチャ特徴
- マイクロサービス設計
- リアルタイムWebSocket通信
- 非同期処理による高パフォーマンス
- 型安全性を保証するTypeScript`,

    'frontend-project-manager': `# ${metadata.name}

## 概要
プロジェクトポートフォリオを管理・可視化するためのモダンなWebアプリケーションです。プロジェクトの詳細情報、技術スタック、進捗状況を一元管理し、美しいUIで表示します。

## 主要機能
- プロジェクト一覧・詳細表示
- 技術スタック分析
- Mermaid図表レンダリング
- 類似プロジェクト検索
- レスポンシブデザイン

## 技術スタック
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Framer Motion
- SWR データフェッチング`,

    'web-monitoring-dashboard': `# ${metadata.name}

## 概要
システム全体の監視・分析を行うリアルタイムダッシュボードです。メトリクス収集、可視化、アラート管理を統合的に提供します。

## 監視機能
- リアルタイムメトリクス表示
- パフォーマンス分析
- エラー追跡
- カスタムアラート設定
- 履歴データ分析

## 技術構成
- Flask バックエンド
- React フロントエンド
- WebSocket リアルタイム通信
- Vite 高速ビルド`,

    'test-calculator-project': `# ${metadata.name}

## 概要
TDD（テスト駆動開発）の学習・実践を目的としたシンプルな計算機プロジェクトです。基本的な算術演算を実装し、テストの書き方を学ぶための教材として設計されています。

## 学習目標
- TDDの基本サイクル（Red-Green-Refactor）
- ユニットテストの作成方法
- テストカバレッジの確保
- Flaskによる簡単なWeb API実装

## 実装機能
- 基本演算（加算・乗算）
- 計算履歴の保持
- Web UIでの操作`
  }

  return templates[projectId] || `# ${metadata.name}\n\n${metadata.description || 'プロジェクトの説明'}`
}

// アーキテクチャ生成
function generateArchitecture(projectId: string, metadata: any): string {
  const techStack = (metadata.dependencies || []).join(', ')

  return `## システムアーキテクチャ

### 技術スタック
${techStack}

### レイヤー構成
\`\`\`
┌─────────────────────────────────┐
│     プレゼンテーション層         │
│  (UI/UX, API エンドポイント)     │
├─────────────────────────────────┤
│      ビジネスロジック層          │
│   (コア機能, 処理ロジック)       │
├─────────────────────────────────┤
│       データアクセス層           │
│  (データベース, 外部API連携)     │
└─────────────────────────────────┘
\`\`\`

### 主要コンポーネント
- **フロントエンド**: ユーザーインターフェース
- **バックエンド**: APIサーバー・ビジネスロジック
- **データストア**: 永続化層
- **外部連携**: サードパーティサービス統合`
}

// セットアップガイド生成
function generateSetupGuide(projectId: string, metadata: any): string {
  const isNode = metadata.dependencies?.some((dep: string) =>
    dep.toLowerCase().includes('next') || dep.toLowerCase().includes('react')
  )

  const isPython = metadata.dependencies?.some((dep: string) =>
    dep.toLowerCase().includes('flask') || dep.toLowerCase().includes('django')
  )

  let setupSteps = '## セットアップガイド\n\n'

  if (isNode) {
    setupSteps += `### Node.js プロジェクト

1. **依存関係のインストール**
   \`\`\`bash
   npm install
   # または
   yarn install
   \`\`\`

2. **環境変数の設定**
   \`\`\`bash
   cp .env.example .env
   # .envファイルを編集して必要な値を設定
   \`\`\`

3. **開発サーバーの起動**
   \`\`\`bash
   npm run dev
   # または
   yarn dev
   \`\`\`

4. **本番ビルド**
   \`\`\`bash
   npm run build
   npm start
   \`\`\`
`
  }

  if (isPython) {
    setupSteps += `### Python プロジェクト

1. **仮想環境の作成**
   \`\`\`bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # または
   venv\\Scripts\\activate  # Windows
   \`\`\`

2. **依存関係のインストール**
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

3. **環境変数の設定**
   \`\`\`bash
   export FLASK_APP=app.py
   export FLASK_ENV=development
   \`\`\`

4. **開発サーバーの起動**
   \`\`\`bash
   flask run
   # または
   python app.py
   \`\`\`
`
  }

  setupSteps += `
### Docker を使用する場合

1. **イメージのビルド**
   \`\`\`bash
   docker build -t ${projectId} .
   \`\`\`

2. **コンテナの起動**
   \`\`\`bash
   docker run -p 8080:8080 ${projectId}
   \`\`\`

3. **Docker Compose**
   \`\`\`bash
   docker-compose up -d
   \`\`\`
`

  return setupSteps
}

// APIリファレンス生成
function generateApiReference(projectId: string, metadata: any): string {
  const apiExamples: Record<string, string> = {
    'frontend-project-manager': `## API リファレンス

### プロジェクト一覧取得
\`\`\`
GET /api/projects
\`\`\`

**レスポンス:**
\`\`\`json
[
  {
    "project_id": "example-project",
    "name": "Example Project",
    "status": "active",
    "tech_stack": ["React", "Node.js"]
  }
]
\`\`\`

### プロジェクト詳細取得
\`\`\`
GET /api/projects/{id}
\`\`\`

### プロジェクト統計取得
\`\`\`
GET /api/projects/stats
\`\`\``,

    'web-monitoring-dashboard': `## API リファレンス

### メトリクス取得
\`\`\`
GET /api/metrics
\`\`\`

### アラート一覧
\`\`\`
GET /api/alerts
\`\`\`

### WebSocket接続
\`\`\`
WS /ws/metrics
\`\`\``
  }

  return apiExamples[projectId] || '## API リファレンス\n\n*API ドキュメントは準備中です*'
}

// 使用例生成
function generateUsageExamples(projectId: string, metadata: any): string {
  return `## 使用例

### 基本的な使い方
\`\`\`javascript
// APIの呼び出し例
const response = await fetch('/api/projects')
const projects = await response.json()

console.log(projects)
\`\`\`

### 高度な使用例
\`\`\`javascript
// フィルタリングとソート
const filteredProjects = projects
  .filter(p => p.status === 'active')
  .sort((a, b) => a.name.localeCompare(b.name))
\`\`\`

### エラーハンドリング
\`\`\`javascript
try {
  const data = await fetchProjectData()
} catch (error) {
  console.error('エラーが発生しました:', error)
}
\`\`\``
}

// 図表生成（Mermaid形式）
function generateDiagrams(projectId: string, metadata: any): Record<string, string> {
  const diagrams: Record<string, string> = {}

  // アーキテクチャ図
  diagrams.architecture = `graph TB
    subgraph "フロントエンド"
        UI[ユーザーインターフェース]
        State[状態管理]
    end

    subgraph "バックエンド"
        API[APIサーバー]
        Logic[ビジネスロジック]
    end

    subgraph "データ層"
        DB[(データベース)]
        Cache[(キャッシュ)]
    end

    UI --> API
    API --> Logic
    Logic --> DB
    Logic --> Cache
    State --> UI`

  // データフロー図
  diagrams.dataFlow = `sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Database

    User->>Frontend: リクエスト
    Frontend->>API: API呼び出し
    API->>Database: データ取得
    Database-->>API: データ返却
    API-->>Frontend: レスポンス
    Frontend-->>User: 結果表示`

  // デプロイメント図
  diagrams.deployment = `graph LR
    subgraph "開発環境"
        Dev[ローカル開発]
    end

    subgraph "CI/CD"
        CI[ビルド & テスト]
        CD[デプロイ]
    end

    subgraph "本番環境"
        Prod[プロダクション]
        Monitor[監視]
    end

    Dev --> CI
    CI --> CD
    CD --> Prod
    Prod --> Monitor`

  return diagrams
}

// 品質スコア計算
function calculateQualityScore(metadata: any): number {
  let score = 70 // 基本スコア

  // 完了状態で加点
  if (metadata.status === 'completed') score += 10

  // 依存関係が明確で加点
  if (metadata.dependencies && metadata.dependencies.length > 0) score += 10

  // タグが豊富で加点
  if (metadata.tags && metadata.tags.length > 3) score += 10

  return Math.min(100, score)
}

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    console.log('Documentation generation requested for:', params.id)

    const body = await request.json()
    const includeAll = body.include_similar || false

    const documentation = await generateDocumentation(params.id)

    if (!documentation) {
      return NextResponse.json(
        { error: 'Project not found' },
        { status: 404 }
      )
    }

    console.log('Documentation generated for:', params.id)
    return NextResponse.json({
      success: true,
      documentation,
      generated_at: new Date().toISOString()
    })

  } catch (error) {
    console.error('Documentation generation error:', error)
    return NextResponse.json(
      { error: 'Documentation generation failed' },
      { status: 500 }
    )
  }
}
