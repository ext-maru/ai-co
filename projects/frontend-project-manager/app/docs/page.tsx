'use client'

import Link from 'next/link'
import { ArrowLeftIcon, DocumentTextIcon, FolderIcon, CodeBracketIcon, BeakerIcon } from '@heroicons/react/24/outline'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function DocsPage() {
  const documentationContent = `
# エルダーズギルド プロジェクト管理システム

## 概要

このシステムは、エルダーズギルドのすべてのプロジェクトを統合管理するためのWebポータルです。
プロジェクトの検索、詳細表示、統計分析、ドキュメント生成などの機能を提供します。

## 主な機能

### 1. プロジェクト一覧表示
- すべてのプロジェクトをカード形式で表示
- リアルタイム検索機能
- プロジェクトタイプ、ステータス、技術スタックによるフィルタリング

### 2. プロジェクト詳細表示
- プロジェクトの基本情報（名前、説明、ステータス）
- 技術スタック一覧
- ファイル構造の可視化
- 関連プロジェクトの表示
- プロジェクトノートの管理

### 3. 統計ダッシュボード
- プロジェクト総数、アクティブ数、完了数の表示
- プロジェクトタイプ別の分布グラフ
- ステータス別の分布グラフ
- 技術スタック使用状況の可視化

### 4. ドキュメント生成
- プロジェクトごとのREADME自動生成
- Mermaidダイアグラムによるアーキテクチャ図
- APIドキュメントの生成

## 技術スタック

- **フロントエンド**: Next.js 14 (App Router), React 18, TypeScript
- **スタイリング**: Tailwind CSS
- **データフェッチング**: SWR
- **チャート**: Recharts
- **アニメーション**: Framer Motion
- **マークダウン**: React Markdown, Remark GFM
- **ダイアグラム**: Mermaid

## API エンドポイント

### プロジェクト管理
- \`GET /api/projects\` - プロジェクト一覧取得
- \`GET /api/projects/[id]\` - プロジェクト詳細取得
- \`POST /api/projects\` - 新規プロジェクト作成
- \`PATCH /api/projects/[id]/update\` - プロジェクト更新
- \`DELETE /api/projects/[id]/update\` - プロジェクト削除

### 統計情報
- \`GET /api/projects/stats\` - 統計情報取得

### ドキュメント
- \`POST /api/projects/[id]/documentation\` - ドキュメント生成

### お気に入り
- \`GET /api/projects/[id]/favorite\` - お気に入り状態取得
- \`POST /api/projects/[id]/favorite\` - お気に入り切り替え
- \`GET /api/projects/favorites\` - お気に入り一覧取得

### ノート
- \`GET /api/projects/[id]/notes\` - ノート一覧取得
- \`POST /api/projects/[id]/notes\` - ノート作成
- \`PATCH /api/projects/[id]/notes\` - ノート更新
- \`DELETE /api/projects/[id]/notes\` - ノート削除

### タグ
- \`GET /api/projects/[id]/tags\` - タグ一覧取得
- \`PATCH /api/projects/[id]/tags\` - タグ更新

### フィルタ・エクスポート
- \`POST /api/projects/filter\` - プロジェクトフィルタリング
- \`GET /api/projects/filter\` - フィルタオプション取得
- \`GET /api/projects/export\` - 全プロジェクトエクスポート
- \`GET /api/projects/[id]/export\` - 個別プロジェクトエクスポート

## 使い方

### プロジェクトの検索
1. トップページの検索バーにキーワードを入力
2. プロジェクト名、説明、技術スタックから検索されます
3. リアルタイムで結果が更新されます

### プロジェクトの詳細確認
1. プロジェクトカードをクリック
2. 詳細ページでプロジェクト情報を確認
3. ファイル構造タブでソースコードの構成を確認
4. ノートタブでプロジェクトに関するメモを管理

### 統計情報の確認
1. メニューから「統計情報」をクリック
2. プロジェクト全体の傾向を把握
3. 技術スタックの使用状況を確認

## 開発者向け情報

### セットアップ
\`\`\`bash
# 依存関係のインストール
npm install

# 開発サーバーの起動
npm run dev

# ビルド
npm run build

# プロダクション実行
npm start
\`\`\`

### 環境設定
- ポート: 9005（docker-compose.ymlで設定）
- データ保存先: \`../../data/project_metadata/\`
- ログ出力: 開発環境でコンソールに出力

### テスト
\`\`\`bash
# テストの実行
npm test

# カバレッジレポート
npm run test:coverage
\`\`\`

## トラブルシューティング

### プロジェクトが表示されない
1. APIエンドポイントが正しく動作しているか確認
2. データディレクトリにメタデータファイルが存在するか確認
3. ブラウザのコンソールでエラーを確認

### 404エラーが発生する
1. Next.jsの開発サーバーが起動しているか確認
2. ポート9005が他のアプリケーションで使用されていないか確認
3. docker-composeで起動している場合は、コンテナが正常に動作しているか確認

## 今後の開発予定

- プロジェクトテンプレート機能
- チーム管理機能
- タスク管理統合
- CI/CD統合
- 通知機能

---

*エルダーズギルド開発チーム*
  `

  return (
    <div className="min-h-screen bg-elder-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* ヘッダー */}
        <div className="mb-8">
          <Link href="/" className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4">
            <ArrowLeftIcon className="h-5 w-5 mr-2" />
            ホームに戻る
          </Link>

          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <DocumentTextIcon className="h-8 w-8 mr-3 text-elder-600" />
            ドキュメント
          </h1>
        </div>

        {/* クイックリンク */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Link href="#概要" className="card hover:shadow-lg transition-shadow">
            <div className="flex items-center">
              <FolderIcon className="h-6 w-6 text-elder-600 mr-3" />
              <span className="font-medium">概要</span>
            </div>
          </Link>

          <Link href="#api-エンドポイント" className="card hover:shadow-lg transition-shadow">
            <div className="flex items-center">
              <CodeBracketIcon className="h-6 w-6 text-elder-600 mr-3" />
              <span className="font-medium">APIリファレンス</span>
            </div>
          </Link>

          <Link href="#開発者向け情報" className="card hover:shadow-lg transition-shadow">
            <div className="flex items-center">
              <BeakerIcon className="h-6 w-6 text-elder-600 mr-3" />
              <span className="font-medium">開発ガイド</span>
            </div>
          </Link>
        </div>

        {/* ドキュメント本文 */}
        <div className="card">
          <div className="prose prose-lg max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {documentationContent}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  )
}
