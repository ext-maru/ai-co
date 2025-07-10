# 🤖 AI Command Executor ナレッジベース v1.1

## 📋 概要

AI Command Executorは、AIとユーザー間のコマンド実行を完全自動化するシステムです。AIが作成したコマンドを自動的に実行し、結果をログに保存することで、手動でのコマンドコピペ作業を完全に排除します。

**v1.1更新: `ai-start`でデフォルトで起動されるようになりました。**

### **システムの特徴**
- ✅ **完全自動実行**: 5秒ごとにコマンドをチェックして自動実行
- ✅ **非同期処理**: AIとワーカーが独立して動作
- ✅ **完全なログ記録**: 全ての実行履歴とエラーを保存
- ✅ **bash/Python対応**: 両方のスクリプトタイプをサポート
- ✅ **デフォルト起動**: v1.1より`ai-start`で自動起動

## 🗂️ システム構成

### ディレクトリ構造
```
/home/aicompany/ai_co/
├── ai_commands/              # コマンド管理ディレクトリ
│   ├── pending/             # 実行待ちコマンド（AIが作成）
│   ├── running/             # 実行中のコマンド
│   ├── completed/           # 実行完了したコマンド
│   └── logs/                # 実行ログと結果
├── workers/
│   └── command_executor_worker.py  # 実行ワーカー
├── libs/
│   └── ai_command_helper.py        # AIヘルパーライブラリ
└── scripts/
    ├── ai-cmd-executor             # 管理コマンド
    └── start-command-executor.sh   # 起動スクリプト
```

### 主要コンポーネント

#### 1. CommandExecutorWorker
- **場所**: `workers/command_executor_worker.py`
- **機能**: pendingディレクトリを監視し、コマンドを自動実行
- **特徴**: 
  - RabbitMQを使わない独立したワーカー
  - 5秒ごとにディレクトリをチェック
  - エラーハンドリングとリトライ機能
  - **v1.1**: `ai-start`で自動起動

#### 2. AICommandHelper
- **場所**: `libs/ai_command_helper.py`
- **機能**: AIがコマンドを作成・結果確認するためのヘルパー
- **主要メソッド**:
  - `create_bash_command()`: bashコマンド作成
  - `create_python_command()`: Pythonコマンド作成
  - `check_results()`: 実行結果確認
  - `get_latest_log()`: 最新ログ取得

## 🚀 使用方法

### 1. システムの起動（v1.1更新）

```bash
# 通常の起動（ai-startに統合済み）
ai-start  # Command Executorも自動起動

# Command Executorなしで起動したい場合
ai-start --no-executor

# 個別に起動する場合（通常は不要）
ai-cmd-executor start

# または直接起動
./scripts/start-command-executor.sh
```

### 2. AIからのコマンド作成

```python
from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

# Bashコマンドの作成
bash_content = """
echo "System check by AI"
ps aux | grep worker | wc -l
df -h
"""
helper.create_bash_command(bash_content, "system_check")

# Pythonコマンドの作成
python_content = """
import psutil
print(f"CPU Usage: {psutil.cpu_percent()}%")
print(f"Memory Usage: {psutil.virtual_memory().percent}%")
"""
helper.create_python_command(python_content, "resource_check")
```

### 3. 実行結果の確認

```python
# 特定コマンドの結果確認
result = helper.check_results("system_check")
print(result)

# 最新のログ確認
latest_log = helper.get_latest_log()
print(latest_log)
```

### 4. 管理コマンド

```bash
# 状態確認
ai-cmd-executor status

# 停止（通常はai-stopで停止される）
ai-cmd-executor stop

# ログ確認
ai-cmd-executor logs

# テスト実行
ai-cmd-executor test
```

## 🔄 動作フロー

```mermaid
graph LR
    A[AI creates command] --> B[Save to pending/]
    B --> C[Executor checks every 5s]
    C --> D[Move to running/]
    D --> E[Execute command]
    E --> F[Save log to logs/]
    F --> G[Move to completed/]
    G --> H[AI reads results]
```

### 詳細な処理フロー

1. **コマンド作成**
   - AIが `AICommandHelper` を使用してJSONファイルを作成
   - `pending/` ディレクトリに保存

2. **自動検出**
   - `CommandExecutorWorker` が5秒ごとに `pending/` をチェック
   - `.json`, `.sh`, `.py` ファイルを検出

3. **実行準備**
   - ファイルを `running/` に移動
   - JSONの場合は実行可能ファイルに変換

4. **コマンド実行**
   - subprocess.runで実行
   - stdout/stderr/exit_codeを記録

5. **結果保存**
   - 詳細ログを `logs/` に保存
   - 結果サマリーをJSONで保存

6. **クリーンアップ**
   - 実行済みファイルを `completed/` に移動

## 📊 コマンドフォーマット

### JSON形式（推奨）

```json
{
  "type": "bash",           // または "python"
  "content": "実行内容",
  "id": "unique_command_id",
  "created_at": "2025-07-02T18:00:00"
}
```

### 直接ファイル形式

- `.sh` ファイル: bashスクリプトとして実行
- `.py` ファイル: Pythonスクリプトとして実行

## 📝 ログフォーマット

### 実行ログ（.log）

```
=== Command Execution Log ===
Command: system_check.sh
Started: 2025-07-02T18:00:00
Working Directory: /home/aicompany/ai_co
==================================================

Exit Code: 0
Duration: 0.15 seconds

=== STDOUT ===
[標準出力]

=== STDERR ===
[標準エラー出力]

==================================================
Completed: 2025-07-02T18:00:15
```

### 結果JSON（_result.json）

```json
{
  "command": "system_check.sh",
  "exit_code": 0,
  "duration": 0.15,
  "log_file": "system_check_20250702_180000.log",
  "timestamp": "2025-07-02T18:00:15",
  "status": "SUCCESS"
}
```

## 🛡️ エラーハンドリング

### 一般的なエラーと対処

1. **JSON解析エラー**
   - エラーログを作成して `completed/` に移動
   - ワーカーは継続動作

2. **実行エラー（exit_code != 0）**
   - 完全なエラー情報をログに記録
   - STATUSを "FAILED" として記録

3. **タイムアウト**
   - 現在は無制限（今後の改善点）

4. **権限エラー**
   - 実行権限を自動的に付与（bashスクリプトのみ）

## 🎯 ベストプラクティス

### AIからのコマンド作成

1. **一意のIDを使用**
   ```python
   command_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
   ```

2. **エラーハンドリングを含める**
   ```bash
   set -e  # エラー時に停止
   echo "Starting task..." || exit 1
   ```

3. **進捗を出力**
   ```python
   print("Step 1/3: Initializing...")
   # 処理
   print("Step 2/3: Processing...")
   ```

### 結果の確認

1. **実行完了を待つ**
   ```python
   import time
   helper.create_bash_command(cmd, "my_task")
   time.sleep(10)  # 実行を待つ
   result = helper.check_results("my_task")
   ```

2. **エラーチェック**
   ```python
   if result.get('exit_code', 1) != 0:
       log_content = helper.get_latest_log("my_task")
       # エラー処理
   ```

## 🔧 トラブルシューティング（v1.1更新）

### ワーカーが起動しない

```bash
# ai-startで起動確認
ai-status

# プロセス確認
ps aux | grep command_executor

# ログ確認
tail -f /home/aicompany/ai_co/logs/command_executor.log

# 手動起動（デバッグ用）
cd /home/aicompany/ai_co
source venv/bin/activate
python3 workers/command_executor_worker.py
```

### コマンドが実行されない

```bash
# ディレクトリ権限確認
ls -la /home/aicompany/ai_co/ai_commands/

# pendingファイル確認
ls -la /home/aicompany/ai_co/ai_commands/pending/

# ワーカー再起動
ai-cmd-executor stop
ai-cmd-executor start
```

### ログが生成されない

```bash
# logsディレクトリ確認
mkdir -p /home/aicompany/ai_co/ai_commands/logs
chmod 755 /home/aicompany/ai_co/ai_commands/logs
```

## 📈 パフォーマンス指標

### 現在の性能
- **チェック間隔**: 5秒
- **平均実行遅延**: 2.5秒
- **最大同時実行**: 1（シーケンシャル）
- **ログ保持**: 無制限（要改善）

### リソース使用
- **CPU**: < 1%（アイドル時）
- **メモリ**: 約20-30MB
- **ディスクI/O**: 最小限

## 🚀 今後の拡張案

### Phase 1: 基本改善
- [ ] タイムアウト機能
- [ ] 並列実行サポート
- [ ] ログローテーション
- [ ] 実行優先度

### Phase 2: 高度な機能
- [ ] Webhookによる完了通知
- [ ] 条件付き実行（cron式）
- [ ] 依存関係管理
- [ ] リモート実行

### Phase 3: エンタープライズ機能
- [ ] 実行履歴データベース
- [ ] RESTful API
- [ ] 分散実行
- [ ] セキュリティ強化

## 📋 設定ファイル

現在はハードコーディングされていますが、将来的には設定ファイルで管理：

```json
// config/command_executor.json（案）
{
  "check_interval": 5,
  "max_parallel": 1,
  "timeout": 300,
  "log_retention_days": 30,
  "allowed_commands": ["bash", "python"],
  "working_directory": "/home/aicompany/ai_co"
}
```

## 🎓 使用例

### システムモニタリング

```python
# AI側のコード
helper.create_bash_command("""
echo "=== System Monitor Report ==="
echo "Date: $(date)"
echo ""
echo "Active Workers:"
ps aux | grep worker | grep -v grep | wc -l
echo ""
echo "Queue Status:"
sudo rabbitmqctl list_queues name messages
echo ""
echo "Disk Usage:"
df -h | grep -E '^/dev'
""", "system_monitor")
```

### 自動バックアップ

```python
# 定期バックアップコマンド
helper.create_bash_command("""
BACKUP_DIR="/home/aicompany/backups/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# データベースバックアップ
sqlite3 /home/aicompany/ai_co/db/task_history.db ".backup '$BACKUP_DIR/task_history.db'"

# 設定ファイルバックアップ
cp -r /home/aicompany/ai_co/config "$BACKUP_DIR/"

echo "Backup completed: $BACKUP_DIR"
""", "daily_backup")
```

## 📈 v1.1 の変更点

1. **デフォルト起動**
   - `ai-start`で自動的に起動
   - 手動起動が不要に

2. **統合された管理**
   - `ai-stop`で自動的に停止
   - プロセス管理の一元化

3. **起動オプション**
   - `--no-executor`で無効化可能
   - 柔軟な運用が可能

---

**🤖 AI Command Executor v1.1により、Elders Guildは真の自律的システムへと進化しました**