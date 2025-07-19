# 🔧 Elders Guild エラー対応ナレッジベース v1.0

## 📋 エラーパターン一覧

### Pattern #001: ModuleNotFoundError - 'core'
**エラー例**:
```
ModuleNotFoundError: No module named 'core'
```

**原因**: PYTHONPATHが設定されていない

**標準修正**:
```python
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import BaseWorker  # これで正常にインポート可能
```

### Pattern #002: ImportError - 相対インポート
**エラー例**:
```
ImportError: attempted relative import with no known parent package
```

**原因**: スクリプトとして直接実行時の相対インポート

**標準修正**:
```python
# NG: from ..libs import something
# OK: from libs import something
```

### Pattern #003: KeyError - config access
**エラー例**:
```
KeyError: 'rabbitmq'
```

**原因**: 設定ファイルの直接キーアクセス

**標準修正**:
```python
# NG: config['rabbitmq']['host']
# OK:
config.get('rabbitmq', {}).get('host', 'localhost')
```

### Pattern #004: FileNotFoundError - config.json
**エラー例**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'config.json'
```

**原因**: 相対パスでの設定ファイル参照

**標準修正**:
```python
# NG: with open('config.json') as f:
# OK:
config_path = Path(__file__).parent.parent / 'config' / 'config.json'
with open(config_path) as f:
```

### Pattern #005: PermissionError
**エラー例**:
```
PermissionError: [Errno 13] Permission denied: '/home/aicompany/ai_co/scripts/script.sh'
```

**原因**: 実行権限がない

**標準修正**:
```python
import os
import stat

# ファイル作成後に実行権限を付与
file_path = Path('/home/aicompany/ai_co/scripts/script.sh')
file_path.chmod(file_path.stat().st_mode | stat.S_IEXEC)
```

### Pattern #006: venv not activated
**エラー例**:
```
ModuleNotFoundError: No module named 'pika'
```

**原因**: 仮想環境が有効化されていない

**標準修正**:
```bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate  # 必須
python3 your_script.py
```

### Pattern #007: Slack webhook failure
**エラー例**:
```
requests.exceptions.ConnectionError
```

**原因**: Slack通知の例外処理不足

**標準修正**:
```python
def _notify_completion(self, message):
    """Slack通知（エラーを握りつぶす）"""
    try:
        from libs.slack_notifier import SlackNotifier
        notifier = SlackNotifier()
        notifier.send_message(f"{EMOJI['robot']} {message}")
    except Exception as e:
        self.logger.warning(f"Slack notification failed: {e}")
        # エラーでも処理は継続
```

### Pattern #008: Connection refused
**エラー例**:
```
pika.exceptions.AMQPConnectionError
```

**原因**: RabbitMQサービスが起動していない

**標準修正**:
```python
# 接続前にサービス確認
import subprocess

def check_rabbitmq_service():
    try:
        result = subprocess.run(['systemctl', 'is-active', 'rabbitmq-server'],
                              capture_output=True, text=True)
        if result.stdout.strip() != 'active':
            # AI Command Executorで起動
            subprocess.run(['sudo', 'systemctl', 'start', 'rabbitmq-server'])
    except:
        pass
```

### Pattern #009: Log directory not found
**エラー例**:
```
FileNotFoundError: [Errno 2] No such file or directory: '/home/aicompany/ai_co/logs/worker.log'
```

**原因**: logsディレクトリが存在しない

**標準修正**:
```python
# BaseWorkerのsetup_loggingに追加
log_dir = Path(self.config.get('logging.directory', 'logs'))
log_dir.mkdir(parents=True, exist_ok=True)
```

### Pattern #010: JSONDecodeError
**エラー例**:
```
json.decoder.JSONDecodeError: Expecting value
```

**原因**: 空のレスポンスや不正なJSON

**標準修正**:
```python
try:
    data = json.loads(response)
except json.JSONDecodeError:
    self.logger.error(f"Invalid JSON response: {response[:100]}")
    data = {}  # デフォルト値で継続
```

## 🔍 エラー診断手順

### 1. 初期診断（1-2分）
```python
# エラータイプの判定
error_type = classify_error(error_message)

# 既知パターンとの照合
pattern_id = match_pattern(error_message)
```

### 2. 修正適用（2-3分）
```python
# 標準修正テンプレートを適用
apply_fix_template(file_path, pattern_id)

# AI Command Executorで自動実行
helper.create_bash_command(fix_script, f"fix_{pattern_id}")
```

### 3. 検証（1分）
```bash
# 構文チェック
python3 -m py_compile fixed_file.py

# 実行テスト
python3 fixed_file.py --test
```

## 📊 エラー統計（2025年1月）

| パターン | 発生頻度 | 自動修正率 |
|---------|---------|-----------|
| #001 (PYTHONPATH) | 高 | 100% |
| #003 (KeyError) | 中 | 100% |
| #006 (venv) | 中 | 100% |
| #007 (Slack) | 低 | 100% |
| #004 (config path) | 低 | 100% |

## 🛡️ 予防的対策

### ワーカーテンプレートの標準化
```python
#!/usr/bin/env python3
"""標準ワーカーテンプレート"""

import sys
from pathlib import Path

# PYTHONPATH設定（必須）
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import BaseWorker, get_config, EMOJI

class NewWorker(BaseWorker):
    def __init__(self):
        super().__init__(worker_type='new')
        self.config = get_config()

    def process_message(self, ch, method, properties, body):
        try:
            # ビジネスロジック
            pass
        except Exception as e:
            self.handle_error(e, "process_message")
            self._safe_notify("エラーが発生しました")

    def _safe_notify(self, message):
        """安全なSlack通知"""
        try:
            from libs.slack_notifier import SlackNotifier
            notifier = SlackNotifier()
            notifier.send_message(f"{EMOJI['robot']} {message}")
        except:
            self.logger.warning("Slack notification failed")
```

### 起動スクリプトの標準化
```bash
#!/bin/bash
set -e

cd /home/aicompany/ai_co
source venv/bin/activate

# ログディレクトリ確保
mkdir -p logs

# 実行
python3 workers/new_worker.py
```

## 🚀 クイックフィックス

### PYTHONPATH問題
```bash
# 即座に修正
echo 'sys.path.insert(0, str(Path(__file__).parent.parent))' >> worker.py
```

### 設定アクセス問題
```bash
# 検索置換
sed -i "s/config\['(.*)'\]/config.get('\1', {})/g" worker.py
```

### 権限問題
```bash
# 一括権限付与
chmod +x scripts/*.sh
```

## 📈 継続的改善

### 週次レビュー
- 新規エラーパターンの追加
- 修正テンプレートの最適化
- 予防策の効果測定

### 月次アップデート
- ワーカーテンプレートの更新
- エラー統計の分析
- ナレッジベースの拡充

---

**🎯 目標: 同じエラーで2度悩まない開発環境の実現**
