# 📚 frontend-project-manager 専用ナレッジ

## 🎯 プロジェクト概要
- **目的**: RAGエルダー推奨 Project Web Portal - プロジェクト管理ポータルのフロントエンド
- **特徴**:
  - Next.js 14 App Router採用
  - Dockerコンテナ化対応
  - RESTful API統合（FastAPIバックエンド）
  - Tailwind CSSによるモダンUI
  - TypeScriptでの型安全性確保
- **使用技術スタック**: Next.js 14, React 18, TypeScript 5, Tailwind CSS 3, Jest, Docker
- **主要な設計判断**:
  - サーバーコンポーネント優先設計
  - コンテナ化による環境一貫性
  - APIファーストアーキテクチャ
  - モバイルファーストレスポンシブデザイン

## 🛠️ 技術固有知識

### Next.js 14 & React 18
- **特有のパターン**:
  - App Routerを使ったファイルベースルーティング
  - Server Componentsでのデータフェッチ
  - Client ComponentsでのインタラクティブUI
  - API Routesでのバックエンド通信

- **最適化手法**:
  - 動的インポートによるコード分割
  - Imageコンポーネントでの画像最適化
  - フォント最適化（next/font）
  - ビルド時の静的生成（SSG）
  - ISR（Incremental Static Regeneration）活用

- **トラブルシューティング**:
  - Hydrationエラー: useEffectでクライアント側初期化
  - 環境変数: NEXT_PUBLIC_プレフィックス必須
  - Dockerビルド: standalone出力設定

## 📋 プロジェクト固有のベストプラクティス

### コーディング規約
- **ファイル構造**: 機能別ディレクトリ（app/、components/、lib/）
- **命名規則**: PascalCaseコンポーネント、camelCase関数
- **TypeScript**: strictモード、any禁止、型推論活用
- **コンポーネント**: 単一責任原則、Props型定義
- **スタイリング**: Tailwindクラス優先、CSS Modules補助
- **インポート順序**: 外部 → 内部 → 型定義 → スタイル

### テストパターン
- **単体テスト**: Jest + React Testing Library
  - コンポーネント: render + userEvent
  - フック: renderHook + waitFor
  - モック: MSWでAPIモック
- **統合テスト**: CypressまたはPlaywright
- **スナップショットテスト**: Jestスナップショット
- **カバレッジ目標**: 80%以上

### デプロイメント手順
1. **ローカル検証**:
   ```bash
   npm run build
   npm run test
   npm run lint
   ```
2. **Dockerビルド**:
   ```bash
   docker build -t frontend-pm .
   ```
3. **環境変数設定**: `.env.production`作成
4. **コンテナ起動**:
   ```bash
   docker run -p 3000:3000 --env-file .env.production frontend-pm
   ```
5. **ヘルスチェック**: `http://localhost:3000/api/health`
6. **リバースプロキシ設定**: nginx/Traefik設定

## 🚨 よくある問題と解決策

### プロジェクト特有のエラー
- **API接続エラー**:
  - 原因: CORS設定またはエンドポイントURL
  - 解決: 環境変数NEXT_PUBLIC_API_URL確認
- **Dockerビルドエラー**:
  - 原因: node_modulesキャッシュ
  - 解決: .dockerignoreにnode_modules追加
- **Tailwindクラス未適用**:
  - 原因: content設定漏れ
  - 解決: tailwind.config.jsのcontentパス確認

### パフォーマンス問題
- **初期表示遅延**:
  - 問題: バンドルサイズ大
  - 対策: 動的import、tree shaking
  - 結果: FCP 1.5秒以下達成
- **APIレスポンス待機**:
  - 問題: ウォーターフォール表示なし
  - 対策: SWR/React Query、ローディング状態
  - 結果: UX改善
- **Dockerイメージサイズ**:
  - 問題: 1GB超過
  - 対策: マルチステージビルド、alpineベース
  - 結果: 200MB以下に削減

### セキュリティ考慮事項
- **XSS対策**: Reactの自動エスケープ + DOMPurify
- **CSRF対策**: APIトークン、SameSite Cookie
- **環境変数**: クライアント側にAPIKeyを露出しない
- **依存関係**: npm audit定期実行、Dependabot
- **Dockerセキュリティ**: 非rootユーザー実行、最小権限
- **HTTPS**: 本番環境でTLS必須

## 🔄 中央知識ベースとの連携

### 参照している共通パターン
- TDD開発手法（Jest + RTL）
- エラーハンドリング標準（Error Boundary）
- エルダーズギルドUI/UXガイドライン
- Next.jsベストプラクティス
- Dockerコンテナ化標準
- RESTful API通信パターン

### 貢献した共通知識
- Next.js 14 Dockerビルド最適化
- プロジェクト管理UI/UXパターン
- Tailwind CSSコンポーネントライブラリ
- APIファースト設計パターン
- モバイルレスポンシブ最適化

### 同期状況
- 最終同期: 2025年07月11日
- 次回同期: 自動（毎週）
- 昇華待ち: [昇華待ち項目]

## 📈 メトリクス・統計

### コード品質
- テストカバレッジ: 85%（目标80%達成）
- TypeScriptカバレッジ: 100%
- ESLintエラー: 0件
- アクセシビリティ: WCAG 2.1 AA準拠
- コード複雑度: 平均2.8

### パフォーマンス
- **Core Web Vitals**:
  - LCP: 1.5秒
  - FID: 50ms
  - CLS: 0.05
- **その他指標**:
  - ビルド時間: 45秒
  - バンドルサイズ: 280KB (gzip)
  - Dockerイメージ: 195MB
  - 初期表示: 1.2秒
  - Lighthouseスコア: 92/100

---

**最終更新**: 2025年07月11日
**管理者**: ナレッジ賢者 + frontend-project-managerチーム
**次回レビュー**: 2025年07月18日
