#!/usr/bin/env python3
"""
ナレッジベース統合版の作成
既存のv1.1と新しいv2.0を統合
"""

from pathlib import Path
import shutil
from datetime import datetime

PROJECT_ROOT = Path("/home/aicompany/ai_co")
kb_dir = PROJECT_ROOT / "knowledge_base"

print("📚 Command Executorナレッジベース統合")
print("="*50)

# 統合版の内容を作成
integrated_content = """# 🤖 AI Command Executor 統合ナレッジベース v2.1

> 最終更新: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """

## 📋 概要

AI Command Executorは、AIとユーザー間のコマンド実行を完全自動化するシステムです。v2.1では、修復・監視システムを統合し、24時間365日の安定稼働を実現しています。

### **システムの特徴**
- ✅ **完全自動実行**: 5秒ごとにコマンドをチェックして自動実行
- ✅ **非同期処理**: AIとワーカーが独立して動作
- ✅ **完全なログ記録**: 全ての実行履歴とエラーを保存
- ✅ **bash/Python対応**: 両方のスクリプトタイプをサポート
- ✅ **デフォルト起動**: `ai-start`で自動起動
- 🆕 **自動修復機能**: 問題を検出して自動修正
- 🆕 **Watchdog監視**: 停止時の自動再起動
- 🆕 **永続化設定**: システム再起動後も自動起動

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
│   ├── command_executor_worker.py  # 実行ワーカー
│   └── executor_watchdog.py        # 監視デーモン（v2.0新規）
├── libs/
│   └── ai_command_helper.py        # AIヘルパーライブラリ
└── scripts/
    ├── ai-cmd-executor             # 管理コマンド
    ├── start-command-executor.sh   # 起動スクリプト
    ├── diagnose_command_executor.py # 診断スクリプト（v2.0新規）
    ├── check_executor_health.sh     # 健全性チェック（v2.0新規）
    └── setup_executor_persistence.py # 永続化設定（v2.0新規）
```

## 🚀 クイックスタート

### 1. 通常の起動（推奨）
```bash
# AI Company全体を起動（Command Executorも自動起動）
ai-start

# 状態確認
ai-status
```

### 2. 問題が発生した場合
```bash
# 完全修復プログラムを実行
cd /home/aicompany/ai_co
python3 fix_executor_complete.py

# または診断のみ
python3 scripts/diagnose_command_executor.py
```

### 3. AIからのコマンド作成
```python
from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

# シンプルな例
helper.create_bash_command("echo 'Hello from AI'", "hello_test")

# 複雑な例
bash_content = \"\"\"
#!/bin/bash
set -e
echo "Starting complex task..."
# 処理内容
echo "Task completed!"
\"\"\"
helper.create_bash_command(bash_content, "complex_task")
```

## 🔧 修復・監視システム（v2.0新機能）

### 自動診断システム

問題を自動的に検出・修正する包括的な診断システム：

```python
# 診断実行
python3 scripts/diagnose_command_executor.py

# 診断内容
1. プロセス状態確認
2. ディレクトリ構造チェック
3. ログ分析
4. tmuxセッション確認
5. 実行テスト
6. 自動修正
```

### Watchdog監視

Command Executorを常時監視し、停止時に自動再起動：

```bash
# Watchdog起動
tmux new-session -d -s executor_watchdog 'python3 workers/executor_watchdog.py'

# 特徴
- 30秒ごとに監視
- 最大10回まで再起動試行
- Slack通知
```

### 永続化設定

システム再起動後も自動的に起動：

```bash
# 永続化設定スクリプト実行
python3 scripts/setup_executor_persistence.py

# 設定方法
1. crontab（推奨）
2. systemd
3. tmux + .bashrc
```

## 📊 トラブルシューティング

### よくある問題と解決方法

#### 1. コマンドが実行されない

```bash
# 診断実行
python3 scripts/diagnose_command_executor.py

# 手動確認
ls -la /home/aicompany/ai_co/ai_commands/pending/
ps aux | grep command_executor
```

#### 2. プロセスが停止している

```bash
# 健全性チェックと自動修復
./scripts/check_executor_health.sh

# または完全修復
python3 fix_executor_complete.py
```

#### 3. ログが出力されない

```bash
# ディレクトリ権限確認
ls -la /home/aicompany/ai_co/ai_commands/logs/
chmod 755 /home/aicompany/ai_co/ai_commands/logs/

# ログ確認
tail -f /home/aicompany/ai_co/logs/command_executor.log
```

## 📈 パフォーマンス最適化

### モニタリング

```python
# 定期的な状態確認
helper.create_bash_command(\"\"\"
echo "=== Performance Check ==="
echo "Pending files: $(ls /home/aicompany/ai_co/ai_commands/pending | wc -l)"
echo "CPU usage: $(ps aux | grep command_executor | awk '{print $3}')%"
echo "Memory usage: $(ps aux | grep command_executor | awk '{print $4}')%"
\"\"\", "performance_check")
```

### ログ管理

```bash
# 古いログのアーカイブ（月次実行推奨）
cd /home/aicompany/ai_co/ai_commands/logs
tar -czf archive_$(date +%Y%m).tar.gz *.log
find . -name "*.log" -mtime +30 -delete
```

## 🎯 ベストプラクティス

### 1. エラーハンドリング

```python
# コマンド作成時の完全なエラーハンドリング
try:
    result = helper.create_bash_command(cmd, cmd_id)
    time.sleep(10)  # 実行を待つ
    
    check = helper.check_results(cmd_id)
    if check.get('exit_code', 1) != 0:
        log = helper.get_latest_log(cmd_id)
        # エラー分析と対処
        slack.send_message(f"⚠️ Command failed: {cmd_id}")
except Exception as e:
    slack.send_message(f"❌ Error creating command: {str(e)}")
```

### 2. 実行の監視

```python
# タイムアウト付き実行監視
import time
start_time = time.time()
timeout = 300  # 5分

while time.time() - start_time < timeout:
    result = helper.check_results(cmd_id)
    if result.get('status') != 'pending':
        break
    time.sleep(5)
else:
    # タイムアウト処理
    slack.send_message(f"⏱️ Command timeout: {cmd_id}")
```

### 3. リソース管理

```python
# 大量のコマンドを実行する場合
import time

commands = ["cmd1", "cmd2", "cmd3", ...]
batch_size = 5

for i in range(0, len(commands), batch_size):
    batch = commands[i:i+batch_size]
    for cmd in batch:
        helper.create_bash_command(cmd, f"batch_{i}_{cmd}")
    time.sleep(30)  # バッチ間で待機
```

## 📋 メンテナンスガイド

### 日次チェック
- プロセス動作確認: `ps aux | grep command_executor`
- pendingファイル確認: `ls -la ai_commands/pending/`
- エラーログ確認: `grep ERROR logs/command_executor.log`

### 週次メンテナンス
- ディスク使用量: `du -sh ai_commands/*`
- 古いファイルクリーンアップ
- パフォーマンス分析

### 月次メンテナンス
- 完全診断: `python3 scripts/diagnose_command_executor.py`
- ログアーカイブ
- 設定見直し

## 🚀 今後の拡張計画

### Phase 1: 基本改善（実装済み）
- ✅ 自動修復機能
- ✅ Watchdog監視
- ✅ 永続化設定
- ✅ 診断ツール

### Phase 2: 高度な機能（計画中）
- [ ] Webhook完了通知
- [ ] 並列実行サポート
- [ ] 優先度キュー
- [ ] リモート実行

### Phase 3: エンタープライズ（将来）
- [ ] RESTful API
- [ ] 実行履歴DB
- [ ] 分散実行
- [ ] 高度なセキュリティ

## 📚 リファレンス

### AICommandHelper API

```python
# 利用可能なメソッド
helper.create_bash_command(content, command_id)
helper.create_python_command(content, command_id)
helper.check_results(command_id)
helper.get_latest_log(command_id=None)
helper.list_pending_commands()
helper.list_completed_commands(limit=10)
```

### 管理コマンド

```bash
ai-cmd-executor start    # 起動
ai-cmd-executor stop     # 停止
ai-cmd-executor status   # 状態確認
ai-cmd-executor logs     # ログ表示
ai-cmd-executor test     # テスト実行
```

---

**🎊 AI Command Executor v2.1 - 完全自律的な実行システムへ進化**

このナレッジベースは定期的に更新されます。最新情報は `/home/aicompany/ai_co/knowledge_base/` を確認してください。
"""

# 統合版ファイルを作成
integrated_file = kb_dir / "AI_Command_Executor_Complete_KB_v2.1.md"
with open(integrated_file, 'w', encoding='utf-8') as f:
    f.write(integrated_content)

print(f"✅ 統合版ナレッジベース作成: {integrated_file}")

# インデックスファイルも更新
index_content = f"""# AI Company Knowledge Base Index

最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📚 Command Executor関連

1. **[AI_Command_Executor_Complete_KB_v2.1.md](AI_Command_Executor_Complete_KB_v2.1.md)**
   - 統合版ナレッジベース（最新・推奨）
   - 基本機能 + 修復・監視システム
   
2. **[AI_Command_Executor_Knowledge_v1.1.md](AI_Command_Executor_Knowledge_v1.1.md)**
   - 基本機能のナレッジベース
   
3. **[Command_Executor_Repair_System_v2.0.md](Command_Executor_Repair_System_v2.0.md)**
   - 修復・監視システムの詳細

## 🔧 その他のナレッジベース

- [AI_Company_Core_Knowledge_v5.1.md](AI_Company_Core_Knowledge_v5.1.md)
- [Error_Intelligence_System_Design_v1.0.md](Error_Intelligence_System_Design_v1.0.md)
- [KB_GitCommitBestPractices.md](KB_GitCommitBestPractices.md)
"""

index_file = kb_dir / "README.md"
with open(index_file, 'w', encoding='utf-8') as f:
    f.write(index_content)

print(f"✅ インデックスファイル更新: {index_file}")
print("\n📚 ナレッジベース統合完了！")
