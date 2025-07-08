# AI Send Extended - タスクタイプ拡張ガイド

## 概要
ai-sendコマンドが13種類のタスクタイプに対応しました。

## 利用可能なタスクタイプ

| タスクタイプ | 説明 | 優先度 | 使用例 |
|------------|------|--------|--------|
| create | 新規作成・開発タスク | 5 | `ai-send create "新機能の実装"` |
| test | テスト作成・実行 | 6 | `ai-send test "ユニットテスト追加"` |
| fix | バグ修正・問題解決 | 8 | `ai-send fix "メモリリーク修正"` |
| deploy | デプロイ・リリース | 7 | `ai-send deploy "本番環境へのリリース"` |
| review | コードレビュー | 5 | `ai-send review "PRのレビュー"` |
| docs | ドキュメント生成 | 3 | `ai-send docs "API仕様書作成"` |
| optimize | パフォーマンス最適化 | 4 | `ai-send optimize "クエリ最適化"` |
| security | セキュリティ監査 | 9 | `ai-send security "脆弱性スキャン"` |
| monitor | システム監視 | 6 | `ai-send monitor "リソース使用状況確認"` |
| backup | バックアップ作業 | 4 | `ai-send backup "DBバックアップ"` |
| migrate | データ移行・システム移行 | 7 | `ai-send migrate "新DBへの移行"` |
| analyze | データ分析・調査 | 5 | `ai-send analyze "ログ分析"` |
| report | レポート生成 | 4 | `ai-send report "月次レポート作成"` |

## 使用方法

### 基本構文
```bash
ai-send <task_type> "<description>" [--priority <1-10>] [--model <model_name>]
```

### 例
```bash
# バグ修正（高優先度）
ai-send fix "ログイン機能のバグ修正" --priority 9

# テスト作成
ai-send test "新機能のE2Eテスト作成"

# ドキュメント生成（低優先度）
ai-send docs "README更新" --priority 2
```

## カスタムテンプレート

各タスクタイプは `/home/aicompany/ai_co/templates/task_types/` にテンプレートを持っています。
カスタマイズが必要な場合は、これらのテンプレートを編集してください。

## 優先度について

- 1-3: 低優先度（ドキュメント、軽微な改善）
- 4-6: 中優先度（通常の開発タスク）
- 7-9: 高優先度（バグ修正、セキュリティ）
- 10: 最高優先度（緊急対応）

## Slack通知

全てのタスクは完了時にSlackに通知されます。
通知先: `#task-result`

---
作成日: 2025-07-04 14:52:55.619012