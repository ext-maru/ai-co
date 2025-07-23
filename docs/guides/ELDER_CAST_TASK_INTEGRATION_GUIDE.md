# 🏛️ AI Elder Cast タスク統合ガイド

**エルダー評議会承認文書** - 2025年7月22日制定

## 📋 概要

AI Elder Castにタスクトラッカー統合機能を実装しました。これにより、Claude Elder起動時に自動的にタスク状態が同期され、セッション間でのタスク継続性が保証されます。

## 🚀 新コマンド

### 1. **ai-elder-cast-with-tasks** （フル機能版）

```bash
# 基本使用（medium知識 + タスク同期）
ai-elder-cast-with-tasks

# コア版 + タスク同期
ai-elder-cast-with-tasks core

# 複数セクション + タスク同期
ai-elder-cast-with-tasks core sages tdd

# タスク同期なしで起動
ai-elder-cast-with-tasks --no-sync

# バックグラウンド同期デーモン付き
ai-elder-cast-with-tasks --daemon
```

#### 主要機能
- 📊 **タスク統計表示**: 総数、未着手、進行中、完了数
- 🎯 **優先度別表示**: Critical/High/Medium/Low別にアクティブタスク表示
- 📅 **本日のタスク**: 今日作成/完了したタスク一覧
- ⚡ **継続タスク**: 前回セッションから引き継ぐべきタスク
- 🔄 **自動同期**: 5分間隔のバックグラウンド同期（--daemon）

### 2. **ai-elder-cast-simple** （更新版）

既存のシンプル版にもタスク同期機能を追加：

```bash
# 通常起動（タスク同期あり）
ai-elder-cast-simple

# タスク同期をスキップ
ELDER_CAST_SKIP_SYNC=true ai-elder-cast-simple
```

## 🔧 環境変数

| 変数名 | デフォルト | 説明 |
|--------|------------|------|
| `CLAUDE_ELDER_USER` | `claude_elder` | タスクトラッカーのユーザーID |
| `ELDER_CAST_SKIP_SYNC` | `false` | タスク同期をスキップ（simpleのみ） |

## 📋 タスク知識注入

起動時に以下の情報が知識として注入されます：

```markdown
# 📊 現在のタスク状況

**セッション開始時刻**: 2025-07-22 10:30:00
**アクティブタスク数**: 5件

## 📈 タスク統計
- **総タスク数**: 283件
- **未着手**: 3件
- **進行中**: 2件
- **完了**: 278件
- **本日完了**: 4件

## 🎯 優先度別アクティブタスク

### 🟠 HIGH (2件)
- 🔄 **OAuth2.0認証実装** (#abc12345, 07/21)
  - 認証フローの実装とテスト...
- 📋 **データベース最適化** (#def67890, 07/20)

### 🟡 MEDIUM (3件)
...
```

## 🔄 同期の仕組み

### 起動時処理フロー

1. **PostgreSQL接続**: タスクトラッカーDBへ接続
2. **前回セッション継承**: 未完了タスクの自動検出
3. **双方向同期**: 
   - Claude Code → タスクトラッカー
   - タスクトラッカー → Claude Code
4. **タスクサマリー生成**: 優先度別、状態別に整理
5. **知識注入**: タスク情報を知識コンテンツに追加
6. **Claude Code起動**: 統合された知識で起動

### エラーハンドリング

- タスク同期でエラーが発生しても、Claude Code起動は継続
- エラー時は警告メッセージを表示してスキップ
- PostgreSQLが停止していても影響なし

## 🎯 使用シナリオ

### 1. 日常の開発セッション

```bash
# 朝の開始時
ai-elder-cast-with-tasks

# タスクが自動的に表示され、前回の続きから作業可能
```

### 2. 長時間セッション

```bash
# デーモンモードで起動（5分ごとに自動同期）
ai-elder-cast-with-tasks --daemon
```

### 3. オフライン作業

```bash
# DBアクセスなしで起動
ai-elder-cast-with-tasks --no-sync
```

## 🛠️ トラブルシューティング

### PostgreSQLエラー

```bash
# PostgreSQL状態確認
sudo systemctl status postgresql

# 必要に応じて起動
sudo systemctl start postgresql
```

### 同期のデバッグ

```bash
# 詳細ログを確認
tail -f logs/todo_tracker_integration.log
```

### 手動同期テスト

```bash
# CLIから手動同期
todo-tracker-sync sync --user claude_elder
```

## 📚 関連ドキュメント

- [TodoTrackerIntegration仕様](../technical/TODO_TRACKER_INTEGRATION_SPEC.md)
- [AI Elder Cast統一仕様書](../../knowledge_base/core/protocols/AI_ELDER_CAST_UNIFIED_SPECIFICATION.md)
- [タスクトラッカー運用ガイド](TASK_TRACKER_OPERATION_GUIDE.md)

## 🔮 今後の拡張予定

1. **リアルタイム同期**: WebSocketによる即時反映
2. **タスク予測**: AIによる次のタスク提案
3. **チーム連携**: 他のエルダーとのタスク共有
4. **視覚化**: タスク進捗のグラフ表示

---
**エルダー評議会承認済み** - クロードエルダー実装