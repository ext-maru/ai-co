# Elders Guild AI Company

エルダーズギルドAIカンパニー - AIエージェント統合管理システム

## 概要

エルダーズギルドは、複数のAIエージェント（エルダーサーバント）を統合管理し、高度な開発タスクを自動化するシステムです。

## 主要コンポーネント

- **4賢者システム**: ナレッジ賢者、タスク賢者、インシデント賞者、RAG賢者による統合管理
- **エルダーサーバント**: 32体の専門AIエージェント群
- **Elder Flow**: 完全自動化開発フロー
- **EITMS**: Todo・Issue・TaskTracker・Planning統合システム（新規追加）
- **タスクトラッカー**: 高度なタスク管理システム

## ディレクトリ構造

```
ai_co/
├── libs/               # コアライブラリ
├── workers/            # ワーカー実装
├── commands/           # CLIコマンド
├── scripts/            # ユーティリティスクリプト
├── tests/              # テストスイート
├── docs/               # ドキュメント
└── knowledge_base/     # ナレッジベース
```

## クイックスタート

```bash
# システム起動
ai-start

# タスク実行
elder-flow execute "タスク内容" --priority high

# ステータス確認
ai-status
```

詳細は[ドキュメント](docs/)を参照してください。
