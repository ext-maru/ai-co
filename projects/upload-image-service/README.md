# upload-image-service

画像アップロード管理システム - 承認フロー付き

## 🚀 クイックスタート

### 開発環境起動
```bash
docker-compose up
```

### アクセスURL
- フロントエンド: http://localhost:3000
- バックエンドAPI: http://localhost:8000
- APIドキュメント: http://localhost:8000/docs

## 🏗️ アーキテクチャ

- **バックエンド**: fastapi
- **フロントエンド**: react-ts
- **データベース**: postgresql
- **ストレージ**: google-drive

## 📋 機能一覧

- 📤 マルチファイルアップロード
- 🖼️ 画像プレビュー・サムネイル生成
- 📊 アップロード進捗表示
- 🔐 ユーザー認証・権限管理
- 👤 管理者承認フロー
- ☁️ クラウドストレージ統合
- 🔄 自動画像最適化
- 📱 レスポンシブUI

## 🧪 テスト実行

### バックエンドテスト
```bash
cd backend
pytest
```

### フロントエンドテスト
```bash
cd frontend
npm test
```

## 📊 PDCA分析

プロジェクトの品質改善状況を確認:
```bash
ai-project pdca upload-image-service
```

## 🏛️ エルダーズギルド統合

- 🧪 TDD（テスト駆動開発）
- 🧙‍♂️ 4賢者システム統合
- 📊 品質監視ダッシュボード
- 🔄 CI/CDパイプライン

## 📚 詳細ドキュメント

- [API仕様書](./docs/api.md)
- [開発ガイド](./docs/development.md)
- [デプロイガイド](./docs/deployment.md)
