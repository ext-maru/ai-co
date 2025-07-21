# TodoList と タスクトラッカー 完全統合ガイド

## 概要

Claude CodeのTodoListツール（TodoRead/TodoWrite）とエルダーズギルドのタスクトラッカー（PostgreSQL版）を完全統合するシステムです。

## 🎯 特徴

### 1. **双方向同期**
- TodoList → タスクトラッカー：セッション中のタスクを永続化
- タスクトラッカー → TodoList：既存タスクをセッションに読み込み

### 2. **リアルタイム連携**
- タスク作成時に自動でTodoListに追加
- ステータス更新が双方向で即座に反映

### 3. **自動同期デーモン**
- 5分ごとに自動で双方向同期
- エラー時の自動リトライ機能

## 📦 構成要素

### 1. **libs/postgres_claude_task_tracker.py**
- `sync_with_todo_list()`: TodoListからタスクトラッカーへの同期
- `sync_tracker_to_todo_list()`: タスクトラッカーからTodoListへの同期
- マッピング関数群: ステータス・優先度の相互変換

### 2. **libs/todo_tracker_integration.py**
- `TodoTrackerIntegration`: 統合管理クラス
- 自動同期機能
- インポート/エクスポート機能

### 3. **libs/todo_hook_system.py**
- `TodoHookSystem`: TodoList操作の監視・フック
- `TodoCommandWrapper`: CLIコマンドラッパー

## 🚀 使い方

### 基本コマンド

```bash
# 手動同期
todo-tracker-sync sync

# ステータス確認
todo-tracker-sync status

# デーモンモード（自動同期）
todo-tracker-sync daemon --interval 300

# インポート/エクスポート
todo-tracker-sync import --file todos.json
todo-tracker-sync export --file todos.json
```

### Todo操作コマンド

```bash
# Todo追加（タスクトラッカーにも自動登録）
todo-hook add "新機能の実装" high

# Todo更新
todo-hook update task-123 in_progress

# Todo完了
todo-hook complete task-123

# Todo一覧（タスクトラッカーから取得）
todo-hook list

# 同期実行
todo-hook sync
```

### Pythonコードでの使用

```python
from libs.todo_tracker_integration import TodoTrackerIntegration

# 統合システム初期化
integration = TodoTrackerIntegration(auto_sync=True)
await integration.initialize()

# タスク作成（TodoListにも自動追加）
task_id = await integration.create_task_with_todo_sync(
    title="新機能実装",
    task_type=TaskType.FEATURE,
    priority=TaskPriority.HIGH
)

# ステータス更新（TodoListも自動更新）
await integration.update_task_with_todo_sync(
    task_id,
    status=TaskStatus.IN_PROGRESS
)

# 手動同期
await integration.sync_both_ways()
```

## 📊 データマッピング

### ステータスマッピング

| TodoList | タスクトラッカー |
|----------|-----------------|
| pending | PENDING |
| in_progress | IN_PROGRESS |
| completed | COMPLETED |
| - | FAILED → pending |
| - | CANCELLED → completed |
| - | REVIEW → in_progress |
| - | BLOCKED → pending |

### 優先度マッピング

| TodoList | タスクトラッカー |
|----------|-----------------|
| high | HIGH/CRITICAL |
| medium | MEDIUM |
| low | LOW |

### タスクタイプ推定

コンテンツから自動推定：
- 「実装」「implement」→ FEATURE
- 「修正」「fix」「bug」→ BUG_FIX
- 「リファクタ」「refactor」→ REFACTOR
- 「テスト」「test」→ TEST
- 「ドキュメント」「doc」→ DOCS

## 🔧 設定

### 環境変数

```bash
# 同期間隔（秒）
export TODO_SYNC_INTERVAL=300

# 自動同期有効化
export TODO_AUTO_SYNC=true
```

### 統合設定

```python
# 自動同期あり（デフォルト）
integration = TodoTrackerIntegration(
    auto_sync=True,
    sync_interval=300  # 5分
)

# 手動同期のみ
integration = TodoTrackerIntegration(
    auto_sync=False
)
```

## 📝 注意事項

1. **TodoListの制限**
   - セッション終了で消失
   - 最大20件まで同期（パフォーマンスのため）

2. **同期タイミング**
   - タスク作成/更新時
   - 5分ごとの自動同期
   - 手動同期コマンド実行時

3. **エラー処理**
   - 同期エラーはログに記録
   - 個別タスクのエラーは無視して継続

## 🎯 ベストプラクティス

1. **セッション開始時**
   ```bash
   # 既存タスクを読み込む
   todo-tracker-sync sync
   ```

2. **長時間作業時**
   ```bash
   # デーモンモードで自動同期
   todo-tracker-sync daemon
   ```

3. **重要タスク**
   ```bash
   # 即座に永続化
   todo-hook add "重要タスク" high
   todo-hook sync
   ```

## 🐛 トラブルシューティング

### 同期されない場合
1. PostgreSQLの接続確認
2. `todo-tracker-sync status`でステータス確認
3. ログファイルの確認

### 重複タスク
- `metadata.todo_id`でユニーク管理
- 既存タスクはステータスのみ更新

### パフォーマンス
- 大量タスクは20件ずつバッチ処理
- 非同期処理で高速化

---

**実装者**: クロードエルダー（Claude Elder）
**承認**: エルダーズギルド評議会
**日付**: 2025年7月21日