# 🤖 AI Command Executor - 完全自動実行システム

## 概要

AIとユーザーの間でbashコマンドをやり取りする作業を完全自動化します。

```
AIがコマンド作成 → ワーカーが自動実行 → ログをAIが確認
```

## ディレクトリ構造

```
ai_commands/
├── pending/     # AIが作成したコマンド（実行待ち）
├── running/     # 実行中のコマンド
├── completed/   # 実行完了したコマンド
└── logs/        # 実行ログとその結果
```

## 使い方

### 1. Command Executor Workerを起動

```bash
chmod +x /home/aicompany/ai_co/scripts/start-command-executor.sh
/home/aicompany/ai_co/scripts/start-command-executor.sh
```

### 2. AIからコマンドを作成

```python
# Pythonコード内で
from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

# Bashコマンドを作成
cmd_content = """
echo "システム情報を取得"
uname -a
df -h
free -h
"""
helper.create_bash_command(cmd_content, "system_info_check")

# 5秒後に自動実行される
```

### 3. 結果を確認

```python
# 実行結果を確認
result = helper.check_results("system_info_check")
print(result)
```

## サンプルコマンド

### システム状態確認
```json
{
  "type": "bash",
  "content": "ps aux | grep worker | wc -l",
  "id": "check_workers"
}
```

### Python実行
```json
{
  "type": "python",
  "content": "import psutil\nprint(f'CPU: {psutil.cpu_percent()}%')",
  "id": "check_cpu"
}
```

## 特徴

- ✅ 5秒ごとに自動チェック
- ✅ bash/pythonコマンド対応
- ✅ 実行ログ自動保存
- ✅ エラーハンドリング
- ✅ JSON形式で結果保存

## ログ形式

実行ログ例:
```
=== Command Execution Log ===
Command: system_info_check.sh
Started: 2025-07-02T10:00:00
Working Directory: /home/aicompany/ai_co
==================================================

Exit Code: 0
Duration: 0.15 seconds

=== STDOUT ===
システム情報を取得
Linux MSI 5.15.153.1-microsoft-standard-WSL2 #1 SMP ...

=== STDERR ===
(no errors)

==================================================
Completed: 2025-07-02T10:00:00
```

結果JSON例:
```json
{
  "command": "system_info_check.sh",
  "exit_code": 0,
  "duration": 0.15,
  "log_file": "system_info_check_20250702_100000.log",
  "timestamp": "2025-07-02T10:00:00",
  "status": "SUCCESS"
}
```

## これにより実現されること

1. **ユーザーの手間削減**: bashコマンドをコピペする必要なし
2. **完全自動化**: AIがコマンドを作成すれば自動実行
3. **履歴管理**: 全ての実行履歴が保存される
4. **エラー追跡**: エラーも自動的にログに記録

## テスト実行

```bash
# テストモードで起動（サンプルコマンドを自動作成）
python3 /home/aicompany/ai_co/workers/command_executor_worker.py --test
```
