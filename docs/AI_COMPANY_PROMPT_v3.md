# 🚀 AI Company 最新プロンプト指示書 v3.0

## 🎯 開発理念：FileSystem一発完結主義

### **最重要原則**
```
1. FileSystemで全て完結させる
2. コピペ一発で動くコードを生成する
3. 手動作業は一切求めない
4. 結果はSlackで自動通知
```

## 📝 必須対応事項

### 1. FileSystem Tools使用時の鉄則

```python
# ❌ 絶対にやってはいけないこと
- 「次に〇〇してください」という指示
- 「確認してください」だけの応答
- 部分的なコード提示
- 手動でのファイル編集依頼

# ✅ 必ずやること
- Filesystem:write_file で完全なファイルを作成
- Filesystem:edit_file で既存ファイルを自動修正
- 実行可能な完全なコードを生成
- 相対パスを使用（ハードコーディング禁止）
```

### 2. 標準的な応答パターン

```markdown
## 実装内容

[要件の理解と実装方針を簡潔に説明]

それでは実装します：

[Filesystem:write_file/edit_file で全ファイルを作成/修正]

## 実行方法

```bash
# 権限付与と実行
chmod +x /home/aicompany/ai_co/[作成したスクリプト]
cd /home/aicompany/ai_co && ./[作成したスクリプト]
```

これで[期待される結果]が実現されます。
```

### 3. AI Company固有の実装ルール

```python
# プロジェクト構造の理解
PROJECT_ROOT = "/home/aicompany/ai_co"  # WSL2環境

# ファイル配置（自己進化システム）
"*_worker.py"    → f"{PROJECT_ROOT}/workers/"
"*_manager.py"   → f"{PROJECT_ROOT}/libs/"
"*.sh"          → f"{PROJECT_ROOT}/scripts/"
"*.conf"        → f"{PROJECT_ROOT}/config/"

# 必須インポート（Coreモジュール活用）
from core import BaseWorker, BaseManager, get_config, EMOJI
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

# Slack通知（タスク完了時）
from libs.slack_notifier import SlackNotifier
notifier = SlackNotifier()
notifier.send_message(f"{EMOJI['success']} タスク完了: {task_id}")
```

## 🔧 実装時の必須チェックリスト

### FileSystem操作前の確認

1. **ディレクトリ確認**
   ```python
   # 必要に応じてディレクトリ作成
   Filesystem:create_directory(path="/home/aicompany/ai_co/new_dir")
   ```

2. **既存ファイル確認**
   ```python
   # 上書き前に確認
   Filesystem:read_file(path="対象ファイル")
   # または
   Filesystem:list_directory(path="対象ディレクトリ")
   ```

3. **権限設定**
   ```python
   # スクリプトファイルは実行権限付きで作成
   # ファイル作成後に chmod +x を含める
   ```

### コード生成時の必須要素

```python
#!/usr/bin/env python3
"""
AI Company [コンポーネント名]
自動生成日時: [timestamp]
"""

import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import BaseWorker, get_config, EMOJI
import logging

class NewWorker(BaseWorker):
    """Core基盤を活用した実装"""
    
    def __init__(self):
        super().__init__(worker_type='new')
        self.config = get_config()
    
    def process_message(self, ch, method, properties, body):
        """ビジネスロジックの実装"""
        try:
            # 処理実装
            self.logger.info(f"{EMOJI['process']} 処理開始")
            
            # 成功時は必ずSlack通知
            self._notify_completion("タスク完了")
            
        except Exception as e:
            self.handle_error(e, "process_message")
            raise
    
    def _notify_completion(self, message):
        """Slack通知（モバイル対応）"""
        from libs.slack_notifier import SlackNotifier
        notifier = SlackNotifier()
        notifier.send_message(f"{EMOJI['robot']} {message}")

if __name__ == "__main__":
    worker = NewWorker()
    worker.run()
```

## 🎨 コード品質基準

### 必須実装項目

1. **エラーハンドリング**
   ```python
   try:
       # 処理
   except Exception as e:
       self.logger.error(f"{EMOJI['error']} エラー: {str(e)}")
       self.handle_error(e, "operation_name")
       # 必要に応じてSlack通知
   ```

2. **ログ出力**
   ```python
   self.logger.info(f"{EMOJI['start']} 開始: {task_id}")
   self.logger.debug(f"{EMOJI['debug']} デバッグ情報")
   self.logger.error(f"{EMOJI['error']} エラー発生")
   ```

3. **設定活用**
   ```python
   config = get_config()
   timeout = config.get('worker.timeout', 300)
   model = config.worker.default_model
   ```

## 📋 タスクタイプ別テンプレート

### 1. 新規ワーカー作成

```python
# FileSystemで自動作成
Filesystem:write_file(
    path="/home/aicompany/ai_co/workers/new_worker.py",
    content="""[BaseWorker継承の完全なコード]"""
)

# テストスクリプトも同時作成
Filesystem:write_file(
    path="/home/aicompany/ai_co/scripts/test_new_worker.sh",
    content="""#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate
python3 workers/new_worker.py --test
"""
)
```

### 2. 設定ファイル作成

```python
# JSON形式の設定
Filesystem:write_file(
    path="/home/aicompany/ai_co/config/new_feature.json",
    content=json.dumps({
        "enabled": True,
        "settings": {...}
    }, indent=2)
)
```

### 3. 統合スクリプト作成

```python
# 複数ファイルを一括作成するスクリプト
Filesystem:write_file(
    path="/home/aicompany/ai_co/scripts/setup_feature.sh",
    content="""#!/bin/bash
# 自動セットアップスクリプト
set -e

echo "🚀 Setting up new feature..."

# ファイル作成
cat > file1.py << 'EOF'
[Pythonコード]
EOF

# 権限設定
chmod +x *.sh

# 実行
python3 file1.py

echo "✅ Setup completed!"
"""
)
```

## 🚨 禁止事項（絶対守る）

1. **ハードコーディングパス禁止**
   ```python
   # ❌ NG
   path = "/root/ai_co/file.py"
   
   # ✅ OK
   path = Path(__file__).parent.parent / "file.py"
   ```

2. **部分的な実装禁止**
   ```python
   # ❌ NG: 「以下のコードを追加してください」
   
   # ✅ OK: FileSystemで完全なファイルを作成
   ```

3. **手動作業指示禁止**
   ```python
   # ❌ NG: 「設定ファイルを編集してください」
   
   # ✅ OK: Filesystem:edit_file で自動編集
   ```

## 🎯 成功基準

- **コピペ一発**: 生成されたコマンドをコピペするだけで完了
- **自動通知**: 完了時にSlackに自動通知
- **エラー耐性**: エラー時も適切にハンドリング
- **自己完結**: 外部の手動作業不要

## 💡 応答例

```markdown
要件を理解しました。EmailNotificationWorkerを実装します。

実装内容：
- BaseWorkerを継承したメール送信ワーカー
- 自動的にworkers/ディレクトリに配置
- Slack通知付き

[Filesystem:write_file で完全なコードを生成]

実行は以下のコマンドで完了します：

```bash
chmod +x /home/aicompany/ai_co/workers/email_notification_worker.py
cd /home/aicompany/ai_co && python3 workers/email_notification_worker.py --test
```

これでEmailNotificationWorkerが稼働開始し、完了通知がSlackに送信されます。
```

---

**🎊 このプロンプトに従うことで、AI Companyは真の「コピペ一発開発」を実現します**
