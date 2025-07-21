# 🔄 Claude Code Todo ⇔ PostgreSQL 完全統合ガイド

**エルダー評議会承認文書** - 2025年7月22日制定

## 📋 概要

Claude CodeのTodoRead/TodoWriteツールとPostgreSQLタスクトラッカーを完全に統合するシステムです。これにより：

- **永続化**: セッション終了後もTodoが保存される
- **引き継ぎ**: 次回起動時に前回の未完了タスクを継続
- **自動同期**: TodoWrite → PostgreSQL、PostgreSQL → TodoRead

## 🚀 クイックスタート

### 1. 通常起動（推奨）

```bash
# Todo同期機能付きで起動
ai-elder-cast-with-todo-sync
```

起動時の動作：
1. PostgreSQLから前回の未完了タスクを検索
2. 「引き継ぎますか？」と確認
3. Yes → 前回のTodoを復元
4. バックグラウンドでTodo監視開始

### 2. 既存コマンドの更新版

```bash
# ai-elder-cast-simple も同期機能付きに更新済み
ai-elder-cast-simple
```

## 🔄 同期の仕組み

### TodoWrite → PostgreSQL

```mermaid
Claude Code → TodoWrite実行 → ~/.claude_todo_hook → 
TodoHookSystem検知 → PostgreSQL保存
```

### PostgreSQL → TodoRead

```mermaid
起動時 → PostgreSQL読み込み → ~/.claude_initial_todos.json → 
Claude Code起動 → TodoRead実行
```

### ファイル構成

| ファイル | 用途 |
|---------|------|
| `~/.claude_todo_hook` | TodoWrite検知用 |
| `~/.claude_todo_current.json` | 現在のTodo状態 |
| `~/.claude_initial_todos.json` | 起動時の初期Todo |
| `~/.claude_todo_monitor.pid` | 監視プロセスPID |

## 🎯 使用シナリオ

### シナリオ1: 日常の開発

```bash
# 朝の開始
$ ai-elder-cast-with-todo-sync

📋 前回のセッションで未完了のタスクが見つかりました:
   3件のアクティブタスク

🔄 進行中のタスク:
  🔄 🟠 OAuth2.0認証実装
    └─ 認証フローの実装とテスト...

📋 未着手のタスク:
  📋 🟡 データベース最適化
    └─ インデックスの追加とクエリ最適化

これらのタスクを引き継ぎますか？
  [Y] 引き継ぐ (デフォルト)
  [N] 新規セッションで開始
  [S] 選択して引き継ぐ
> Y

✅ 3件のタスクを引き継ぎました
🔍 Todo監視システムを開始しました
```

### シナリオ2: Claude Code内での操作

```bash
# Claude Code内で通常通りTodoツールを使用
> TodoWrite: OAuth認証のテスト実装を追加

# 自動的にPostgreSQLに保存される
# 次回起動時も残っている
```

### シナリオ3: 手動テスト

```bash
# Todo同期のテスト
claude-todo-hook test

# 現在のTodoを確認
claude-todo-hook read

# 手動でTodoを追加（テスト用）
echo '[{"id":"test-1","content":"テストタスク","status":"pending","priority":"high"}]' | claude-todo-hook write
```

## 🔧 バックグラウンドプロセス

### Todo監視デーモン

起動時に自動的に開始される監視プロセス：

```bash
# プロセス確認
ps aux | grep todo-monitor-daemon

# ログ確認
tail -f logs/todo_monitor_daemon.log

# 手動起動（通常は不要）
todo-monitor-daemon
```

### 機能

- **ファイル監視**: 1秒ごとに`~/.claude_todo_hook`をチェック
- **自動同期**: 変更検知時にPostgreSQLと同期
- **定期同期**: 5分ごとに全体同期
- **ヘルスチェック**: 1分ごとに状態ログ出力

## 🛠️ トラブルシューティング

### Todoが同期されない

1. **PostgreSQL接続確認**
   ```bash
   sudo systemctl status postgresql
   ```

2. **監視プロセス確認**
   ```bash
   ps aux | grep todo-monitor
   cat ~/.claude_todo_monitor.pid
   ```

3. **フックファイル確認**
   ```bash
   ls -la ~/.claude_todo*
   ```

### 引き継ぎダイアログが表示されない

- 前回のタスクがすべて完了している
- PostgreSQLに接続できない
- ユーザーIDが異なる（環境変数確認）

### 環境変数

| 変数名 | デフォルト | 説明 |
|--------|------------|------|
| `CLAUDE_ELDER_USER` | `claude_elder` | タスクのユーザーID |
| `CLAUDE_INITIAL_TODOS` | - | 初期Todoファイルパス |

## 📊 データフロー

```
起動時:
1. PostgreSQL → 未完了タスク取得
2. ユーザー確認 → Yes/No
3. 初期Todoファイル作成
4. Claude Code起動 + Todo監視開始

実行中:
1. TodoWrite実行
2. ~/.claude_todo_hook にデータ書き込み
3. TodoHookSystem が検知（1秒以内）
4. PostgreSQLに保存
5. フックファイル削除

終了時:
1. 監視プロセス停止
2. 最終同期実行
3. クリーンアップ
```

## 🎨 カスタマイズ

### 同期間隔の変更

```python
# libs/todo_tracker_integration.py
integration = TodoTrackerIntegration(
    auto_sync=True,
    sync_interval=600  # 10分に変更
)
```

### 引き継ぎタイムアウト

```python
# scripts/ai-elder-cast-with-todo-sync
choice = await asyncio.wait_for(
    ...,
    timeout=30.0  # 30秒に変更
)
```

## 📚 関連ファイル

- **起動スクリプト**: `/scripts/ai-elder-cast-with-todo-sync`
- **監視デーモン**: `/scripts/todo-monitor-daemon`
- **テストツール**: `/scripts/claude-todo-hook`
- **統合モジュール**: `/libs/todo_tracker_integration.py`
- **フックシステム**: `/libs/todo_hook_system.py`

## 🔮 今後の拡張予定

1. **リアルタイムWebSocket同期**
2. **選択的タスク引き継ぎUI**
3. **タスクのアーカイブ機能**
4. **チーム間でのタスク共有**

---
**実装者**: クロードエルダー（Claude Elder）  
**承認**: エルダーズギルド評議会