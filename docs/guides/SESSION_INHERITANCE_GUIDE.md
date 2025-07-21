# セッション継承機能ガイド

## 概要

Claude Codeのセッション切断時に、前回の未完了タスクを新しいセッションに自動継承する機能です。

## 🎯 主な機能

### 1. **自動継承提案**
- セッション開始時に前回の未完了タスクを検出
- 3個以下なら自動で継承を提案
- 4個以上なら手動操作を推奨

### 2. **手動継承**
- `resume`コマンドで明示的にタスクを継承
- 強制継承オプション（確認なし）

### 3. **セッション追跡**
- 各タスクにセッションIDを自動付与
- 継承履歴をメタデータに記録
- 継承元セッションの情報を保持

## 🚀 使い方

### 基本的な継承操作

```bash
# 前回のセッションから未完了タスクを継承
todo-tracker-sync resume --user claude_elder

# 確認なしで強制継承
todo-tracker-sync resume --user claude_elder --force

# 継承可能なタスクを確認
todo-tracker-sync my-tasks --user claude_elder
```

### 自動継承機能

```bash
# 通常の同期（自動継承提案あり）
todo-tracker-sync sync --user claude_elder

# 自動継承を明示的に有効化
todo-tracker-sync sync --auto-inherit --user claude_elder
```

## 📊 実際の使用例

### セッション1: 作業開始
```bash
# 新しいタスクを作成
todo-hook add "OAuth実装" high --user claude_elder
todo-hook add "テスト作成" medium --user claude_elder

# タスクには session-abc123 のようなIDが自動付与
todo-tracker-sync my-tasks
# ⏳ 🟠 [task-001] OAuth実装
#    🏷️  Tags: user-claude_elder, session-abc123
# ⏳ 🟡 [task-002] テスト作成  
#    🏷️  Tags: user-claude_elder, session-abc123
```

### セッション切断・再開

```bash
# 新しいセッション（session-def456）で再開
todo-tracker-sync sync --user claude_elder

# 出力例：
# 📋 前回のセッションから 2 個の未完了タスクが見つかりました:
#   ⏳ OAuth実装
#   ⏳ テスト作成
# 引き継ぎますか？ (y/N): y
# ✅ 2 個のタスクを現在のセッションに引き継ぎました

# 確認
todo-tracker-sync my-tasks
# ⏳ 🟠 [task-001] OAuth実装
#    🏷️  Tags: user-claude_elder, session-def456  ← 新セッションID
# ⏳ 🟡 [task-002] テスト作成
#    🏷️  Tags: user-claude_elder, session-def456
```

## 🔧 詳細機能

### セッション継承の動作

1. **検出条件**
   - 自分のタスク（`assigned_to` = 自分）
   - 未完了ステータス（`pending`, `in_progress`）
   - 現在のセッション以外のセッションID

2. **継承処理**
   - セッションタグを現在のセッションに更新
   - メタデータに継承情報を追加
   - TodoListに自動反映

3. **継承メタデータ**
   ```json
   {
     "session_id": "session-def456",
     "user_id": "claude_elder", 
     "inherited_from": "session-abc123",
     "inherited_at": "2025-07-21T11:04:34.799"
   }
   ```

### 自動継承ロジック

```python
# 3個以下：自動で継承提案
if len(previous_tasks) <= 3:
    await inherit_pending_tasks(confirm_prompt=True)

# 4個以上：手動操作を推奨
else:
    print("多くのタスクがあるため、手動で確認してください")
    print("todo-tracker-sync resume --user {user}")
```

## ⚙️ 設定オプション

### CLIオプション

```bash
# resumeコマンド
todo-tracker-sync resume [options]
  --user USER_ID      継承するユーザー（デフォルト: claude_elder）
  --force            確認なしで強制継承

# syncコマンド
todo-tracker-sync sync [options] 
  --auto-inherit     自動継承提案を有効化
  --user USER_ID     ユーザー指定
```

### Python API

```python
from libs.todo_tracker_integration import TodoTrackerIntegration

integration = TodoTrackerIntegration(user_id="claude_elder")
await integration.initialize()

# 前回タスクの取得
previous_tasks = await integration.get_pending_tasks_from_previous_sessions()

# 手動継承
inherited_count = await integration.inherit_pending_tasks(confirm_prompt=False)

# 自動継承提案
auto_inherited = await integration.auto_inherit_if_pending()
```

## 📝 ベストプラクティス

### 1. **セッション開始時**
```bash
# 推奨：同期時に自動継承提案
todo-tracker-sync sync --user claude_elder
```

### 2. **明示的な継承**
```bash
# 大量のタスクがある場合
todo-tracker-sync resume --user claude_elder

# 確認を省略したい場合
todo-tracker-sync resume --force --user claude_elder
```

### 3. **継承状況の確認**
```bash
# 継承されたタスクの確認
todo-tracker-sync my-tasks --user claude_elder

# システム全体の状況
todo-tracker-sync status --user claude_elder
```

## 🚨 注意事項

1. **セッションIDの一意性**
   - 各起動時にUUID-based IDが自動生成
   - 同じセッション内では同じIDを使用

2. **継承の対象**
   - 自分が担当者のタスクのみ
   - 未完了ステータスのみ
   - 他のセッションのタスクのみ

3. **データの整合性**
   - 継承時にメタデータを自動更新
   - 元のセッション情報は保持
   - 継承タイムスタンプを記録

## 🔍 トラブルシューティング

### 継承されない場合
```bash
# デバッグ情報の確認
todo-tracker-sync status --user claude_elder

# タスク一覧の詳細確認
todo-tracker-sync my-tasks --user claude_elder
```

### エラーが発生する場合
- PostgreSQL接続の確認
- ユーザーIDの正確性確認
- ログファイルの確認

---

**実装者**: クロードエルダー（Claude Elder）
**テスト**: 7/7 成功
**日付**: 2025年7月21日