# プロジェクト整理分析レポート

## 調査日時
2025年1月11日

## 調査対象ディレクトリ
- `/home/aicompany/ai_co/projects/`
- `/home/aicompany/ai_co/deployment/`

## プロジェクト一覧と状態

### 1. projects/elders-guild-web (815MB)
- **目的**: エルダーズギルドWebシステム - 4賢者リアルタイムシステム
- **技術**: Next.js 14 + FastAPI + PostgreSQL
- **状態**: アクティブ（最新コミット: 2025/1/11）
- **判定**: ✅ **保持** - メインWebインターフェース

### 2. projects/image-upload-manager (180MB)
- **目的**: 顧客画像アップロード管理システム
- **技術**: Flask + SQLite + Google Drive API
- **状態**: アクティブ（最新コミット: 2025/1/11）
- **判定**: ⚠️ **重複の可能性** - upload-image-serviceと機能重複

### 3. projects/upload-image-service (2.8MB)
- **目的**: 画像アップロード管理システム（承認フロー付き）
- **技術**: FastAPI + React + PostgreSQL + Google Drive
- **状態**: アクティブ（最新コミット: 2025/1/11）
- **判定**: ⚠️ **重複の可能性** - image-upload-managerの新バージョン？

### 4. projects/web-monitoring-dashboard (110MB)
- **目的**: システム監視ダッシュボード
- **技術**: Flask + React + WebSocket
- **状態**: アクティブ
- **判定**: ✅ **保持** - 監視システムとして必要

### 5. projects/frontend-project-manager (2.0MB)
- **目的**: プロジェクト管理フロントエンド
- **技術**: Next.js
- **状態**: アクティブ（最新コミット: 2025/1/11）
- **判定**: ✅ **保持** - プロジェクト管理UI

### 6. projects/test-calculator-project (28KB)
- **目的**: テスト用計算機プロジェクト
- **技術**: Python
- **状態**: テスト用
- **判定**: 🗑️ **削除候補** - テスト用の小規模プロジェクト

### 7. deployment/contract-upload-system (1.5MB)
- **目的**: 契約書類アップロードシステムのデプロイメント版
- **技術**: FastAPI + React + PostgreSQL
- **状態**: 本番デプロイ済み（サーバー: 57.181.4.111）
- **判定**: ✅ **保持** - 本番稼働中

### 8. deployment/image-upload-manager (216KB)
- **目的**: image-upload-managerのデプロイメント設定
- **技術**: Docker設定ファイル
- **状態**: デプロイメント用
- **判定**: ⚠️ **確認必要** - projects版との関係確認必要

## 重複プロジェクトの詳細分析

### 画像アップロード関連の重複
1. **projects/image-upload-manager**
   - Flask ベース
   - SQLite 使用
   - 180MB（node_modules含む）

2. **projects/upload-image-service**
   - FastAPI + React
   - PostgreSQL 使用
   - より新しいアーキテクチャ

3. **deployment/image-upload-manager**
   - デプロイメント設定のみ

**推奨**: upload-image-serviceが新バージョンと思われるため、古いimage-upload-managerは削除候補

## 整理対象（削除候補）リスト

### 優先度: 高（安全に削除可能）
1. **projects/test-calculator-project** - テスト用プロジェクト
2. **projects/gateway/** - 単独のnginx設定（他で代替可能）
3. **projects/monitoring/** - 単独の設定ファイル（web-monitoring-dashboardに統合済み）

### 優先度: 中（確認後削除推奨）
1. **projects/image-upload-manager** - upload-image-serviceと重複
   - 事前に機能確認が必要
   - Google Drive統合の移行確認

### 優先度: 低（詳細調査必要）
1. **deployment/image-upload-manager** - デプロイ状況の確認必要

## node_modules のクリーンアップ
- 合計61個のnode_modulesディレクトリを検出
- 推定削除可能容量: 約1GB以上

## 推奨アクション

### 即時実行可能
```bash
# 1. テストプロジェクトの削除
rm -rf projects/test-calculator-project

# 2. 単独設定ファイルの削除
rm -rf projects/gateway
rm -rf projects/monitoring

# 3. node_modulesのクリーンアップ（開発環境で再生成可能）
find projects -name "node_modules" -type d -prune -exec rm -rf {} +
```

### 確認後実行
```bash
# image-upload-managerの機能がupload-image-serviceに完全移行されていることを確認後
rm -rf projects/image-upload-manager
```

### 追加推奨事項
1. プロジェクトのREADMEを統一フォーマットに更新
2. 各プロジェクトの依存関係を明確化
3. デプロイメント状態の文書化
4. 定期的なプロジェクト棚卸しプロセスの確立

## 削除による影響
- **ディスク容量削減**: 約1.2GB以上
- **プロジェクト数削減**: 8 → 5プロジェクト
- **管理負荷軽減**: 重複プロジェクトの排除

## 注意事項
- 削除前に必ずバックアップを作成
- 本番環境で使用中のプロジェクトは慎重に確認
- チームメンバーへの事前通知を実施
