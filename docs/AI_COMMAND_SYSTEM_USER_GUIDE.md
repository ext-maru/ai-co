# AI Command System ユーザーガイド

**バージョン**: 2.0.0
**承認**: エルダー評議会 (2025年7月9日)

## 🚀 クイックスタート

新しいAIコマンドシステムは、すべてのコマンドを `ai` から始まる統一された形式で提供します。

```bash
# システム状態確認
ai status

# エルダー設定表示
ai elder settings

# ヘルプ表示
ai help
```

## 📋 基本構造

### コマンド形式

```
ai <command>              # Core commands
ai <category> <command>   # Category commands
ai help <category>        # Category help
ai find <query>          # Command search
```

## 🗂️ カテゴリー一覧

### 1. Core Commands (基本コマンド)
システムの基本操作を行うコマンド群

| コマンド | 説明 | 旧コマンド |
|---------|------|-----------|
| `ai start` | システム起動 | `ai-start` |
| `ai stop` | システム停止 | `ai-stop` |
| `ai status` | システム状態確認 | `ai-status` |
| `ai env` | 環境設定 | `ai-env` |

### 2. Elder Management (エルダー管理)
エルダーシステムの管理機能

| コマンド | 説明 | 旧コマンド |
|---------|------|-----------|
| `ai elder status` | エルダー状態確認 | `ai-elder` |
| `ai elder council` | 評議会管理 | `ai-elder-council` |
| `ai elder settings` | 設定表示 | `ai-elder-settings` |
| `ai elder tree` | エルダーツリー表示 | `ai-elder-tree` |
| `ai elder servant` | サーバント管理 | `ai-servant` |

### 3. Worker Management (ワーカー管理)
ワーカーの管理とモニタリング

| コマンド | 説明 | 旧コマンド |
|---------|------|-----------|
| `ai worker status` | ワーカー通信状態 | `ai-worker-comm` |
| `ai worker recovery` | ワーカー復旧 | `ai-worker-recovery` |
| `ai worker dlq` | DLQ管理 | `ai-dlq` |

### 4. Development Tools (開発ツール)
開発作業を支援するツール群

| コマンド | 説明 | 旧コマンド |
|---------|------|-----------|
| `ai dev codegen` | コード生成 | `ai-codegen` |
| `ai dev document` | ドキュメント生成 | `ai-document` |
| `ai dev git` | Git統合 | `ai-git` |
| `ai dev tdd` | TDD開発 | `ai-tdd` |

### 5. Testing Tools (テストツール)
テスト実行と品質管理

| コマンド | 説明 | 旧コマンド |
|---------|------|-----------|
| `ai test coverage` | カバレッジ分析 | `ai-test-coverage` |
| `ai test quality` | 品質分析 | `ai-test-quality` |
| `ai test runner` | テスト実行 | `ai-test-runner` |
| `ai test magic` | エルフテスト魔法 | `ai-elf-test-magic` |

### 6. Operations (運用ツール)
システム運用とAPI管理

| コマンド | 説明 | 旧コマンド |
|---------|------|-----------|
| `ai ops dashboard` | ダッシュボード | `ai-dashboard` |
| `ai ops api-status` | API状態 | `ai-api-status` |
| `ai ops api-health` | APIヘルス | `ai-api-health` |
| `ai ops api-reset` | APIリセット | `ai-api-reset` |

### 7. Monitoring (監視・ログ)
システム監視とログ管理

| コマンド | 説明 | 旧コマンド |
|---------|------|-----------|
| `ai monitor logs` | ログ表示 | `ai-logs` |
| `ai monitor proactive` | 予防的監視 | `ai-elder-proactive-monitor` |

### 8. Integrations (外部連携)
外部サービスとの連携

| コマンド | 説明 | 旧コマンド |
|---------|------|-----------|
| `ai integrate slack` | Slack統合 | `ai-slack` |
| `ai integrate mcp` | MCP統合 | `ai-mcp` |
| `ai integrate send` | メッセージ送信 | `ai-send` |

## 🔍 コマンド検索

### find コマンドの使用

```bash
# "test"を含むコマンドを検索
ai find test

# "elder"を含むコマンドを検索
ai find elder

# "api"を含むコマンドを検索
ai find api
```

## 🎯 便利な機能

### 1. 自動補完
bashやzshで自動補完を有効にできます（設定方法は後日追加）

### 2. エイリアス
よく使うコマンドの短縮形：
- `ai h` → `ai help`
- `ai v` → `ai version`
- `ai ?` → `ai help`

### 3. レガシー互換性
旧コマンドも引き続き使用可能ですが、警告が表示されます：

```bash
$ ai-elder-status
⚠️ Legacy command detected. Please use new syntax.
  Old: ai-elder-status
  New: ai elder status
```

## 📝 移行ガイド

### 移行手順

1. **新コマンドの学習**
   - `ai help` で全体像を把握
   - `ai help <category>` で詳細確認

2. **スクリプトの更新**
   - 自動化スクリプト内の旧コマンドを新コマンドに置換
   - 移行スクリプト（準備中）を使用

3. **エイリアスの設定**
   - 頻繁に使うコマンドはシェルエイリアスに登録

### 移行例

```bash
# 旧形式
ai-elder-council
ai-test-coverage --html
ai-worker-recovery --force

# 新形式
ai elder council
ai test coverage --html
ai worker recovery --force
```

## 🆘 トラブルシューティング

### Q: コマンドが見つからない
A: `ai find <keyword>` で検索するか、`ai help` で確認してください

### Q: 旧コマンドはいつまで使える？
A: 当面は維持されますが、新コマンドへの移行を推奨します

### Q: カスタムコマンドを追加したい
A: 現在準備中のプラグインシステムで対応予定です

## 📚 関連ドキュメント

- [エルダー評議会決定記録](/reports/ELDER_COUNCIL_RECORD_20250709_AI_COMMAND_REORG.md)
- [コマンド分類レポート](/reports/AI_COMMAND_CATEGORIZATION_20250709.md)
- [移行計画詳細](/reports/ai_command_migration_guide_draft.md)

---
*AI Command System User Guide v2.0.0*
*エルダー評議会承認済み*
