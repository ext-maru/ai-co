# 個人タスク管理ガイド

## 概要

TodoListとタスクトラッカーの統合システムで、**自分専用のタスク**を管理できるようになりました！

## 🎯 主な機能

### 1. **ユーザー別タスク管理**
- 各タスクに`assigned_to`（担当者）を自動設定
- 自分のタスクのみを同期・表示

### 2. **セッション追跡**
- セッションIDを自動生成
- タグとメタデータで詳細な追跡

### 3. **個人フィルタリング**
- 自分のタスクのみを表示
- 他のユーザーのタスクは非表示

## 🚀 使い方

### 基本コマンド

```bash
# 自分のタスクのみ同期（デフォルト）
todo-tracker-sync sync --user claude_elder

# 全タスクを同期
todo-tracker-sync sync --all

# 自分のタスク一覧
todo-tracker-sync my-tasks --user claude_elder

# 別ユーザーとして操作
todo-tracker-sync sync --user maru
todo-tracker-sync my-tasks --user maru
```

### タスク作成時の自動設定

```python
# タスク作成時に自動的に以下が設定されます：
- assigned_to: "claude_elder"  # 担当者
- created_by: "claude_elder"   # 作成者
- tags: ["user-claude_elder", "session-20250721-143025"]
- metadata: {
    "session_id": "session-20250721-143025",
    "user_id": "claude_elder"
  }
```

### 個人タスクの取得

```bash
# CLIコマンド
todo-tracker-sync my-tasks

# 出力例：
📋 claude_elder's Tasks (5 total):

🔄 🟠 [abc12345] OAuth2.0認証システム実装
   🏷️  Tags: user-claude_elder, security, session-20250721-143025

⏳ 🟡 [def67890] ドキュメント更新
   🏷️  Tags: user-claude_elder, docs, session-20250721-143025
```

## 📊 ステータス確認

```bash
todo-tracker-sync status --user claude_elder

# 出力例：
{
  "user_id": "claude_elder",
  "session_id": "session-20250721-143025",
  "my_tasks_stats": {
    "total": 5,
    "pending": 2,
    "in_progress": 2,
    "completed": 1
  },
  "global_tracker_stats": {
    "total_tasks": 50,
    ...
  }
}
```

## 🔧 Python APIでの使用

```python
from libs.todo_tracker_integration import TodoTrackerIntegration

# 個人用統合システム初期化
integration = TodoTrackerIntegration(
    user_id="claude_elder",
    auto_sync=True
)
await integration.initialize()

# 個人タスク作成（自動的に担当者設定）
task_id = await integration.create_task_with_todo_sync(
    title="新機能実装",
    task_type=TaskType.FEATURE,
    priority=TaskPriority.HIGH
)

# 自分のタスクのみ取得
my_tasks = await integration.get_my_tasks()

# 自分のタスクのみ同期
await integration.sync_both_ways(personal_only=True)
```

## 🎯 ユースケース

### 1. **個人作業セッション**
```bash
# セッション開始
todo-tracker-sync sync --user claude_elder

# 作業中
todo-hook add "バグ修正" high  # 自動的にclaude_elderに割り当て

# セッション終了
todo-tracker-sync sync --user claude_elder
```

### 2. **チーム開発**
```bash
# 各メンバーが自分のユーザーIDで作業
todo-tracker-sync sync --user maru
todo-tracker-sync sync --user knowledge_sage
todo-tracker-sync sync --user incident_sage

# 全体の状況確認
todo-tracker-sync sync --all --user admin
```

### 3. **複数セッション管理**
```bash
# セッション1: 機能開発
todo-tracker-sync daemon --user claude_elder

# セッション2: バグ修正（別ターミナル）
todo-tracker-sync sync --user claude_elder_bugfix
```

## 📝 メリット

1. **競合回避**: 各ユーザーが独立したタスク空間
2. **追跡性**: セッションIDで作業履歴を追跡
3. **柔軟性**: ユーザーを切り替えて異なる役割で作業
4. **統合性**: TodoListと完全同期

## ⚠️ 注意事項

- デフォルトユーザーは`claude_elder`
- `--all`オプションなしでは自分のタスクのみ同期
- セッションIDは起動時に自動生成

---

**実装者**: クロードエルダー（Claude Elder）
**日付**: 2025年7月21日