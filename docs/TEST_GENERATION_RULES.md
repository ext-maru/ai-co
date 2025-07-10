# 🧪 Elders Guild テスト適用プロンプトルール

## 📋 コード生成時の必須テストルール

### **最重要原則**
```
1. コード生成 = テスト生成も必須
2. FileSystemで本体とテストを同時生成
3. テスト実行スクリプトも自動作成
4. 変更時は回帰テストも考慮
```

## 🎯 テスト生成の具体的手順

### 1. 新規ワーカー/マネージャー作成時

```python
# Step 1: 本体コードを生成
Filesystem:write_file(
    path="/home/aicompany/ai_co/workers/new_worker.py",
    content="""[ワーカーの実装]"""
)

# Step 2: 必ずユニットテストも生成
Filesystem:write_file(
    path="/home/aicompany/ai_co/tests/unit/test_new_worker.py",
    content="""#!/usr/bin/env python3
\"\"\"
NewWorker Unit Tests
\"\"\"

import sys
import json
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from workers.new_worker import NewWorker


class TestNewWorker:
    def setup_method(self):
        self.worker = None
    
    def teardown_method(self):
        if self.worker:
            self.worker.cleanup()
    
    @patch('pika.BlockingConnection')
    def test_initialization(self, mock_connection):
        mock_connection.return_value = Mock()
        self.worker = NewWorker()
        assert self.worker is not None
        assert self.worker.worker_type == 'new'
    
    @patch('pika.BlockingConnection')
    def test_message_processing(self, mock_connection):
        mock_connection.return_value = Mock()
        self.worker = NewWorker()
        
        # テストメッセージ
        test_body = json.dumps({
            'task_id': 'test_123',
            'data': 'test data'
        })
        
        mock_channel = Mock()
        mock_method = Mock(delivery_tag='test_tag')
        
        self.worker.process_message(
            mock_channel,
            mock_method,
            {},
            test_body
        )
        
        mock_channel.basic_ack.assert_called_with(delivery_tag='test_tag')
    
    def test_error_handling(self):
        # エラーケースのテスト
        pass
"""
)

# Step 3: テスト実行スクリプトも生成
Filesystem:write_file(
    path="/home/aicompany/ai_co/scripts/test_new_worker.sh",
    content="""#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate
pytest tests/unit/test_new_worker.py -v
"""
)
```

### 2. 既存コード修正時

```python
# 修正前に既存テストの確認
Filesystem:read_file(
    path="/home/aicompany/ai_co/tests/unit/test_existing_worker.py"
)

# 修正に応じてテストも更新
Filesystem:edit_file(
    path="/home/aicompany/ai_co/tests/unit/test_existing_worker.py",
    edits=[
        {
            "oldText": "# 古いテストケース",
            "newText": """# 新機能のテストケース
    def test_new_feature(self):
        # 新機能のテスト実装
        assert True"""
        }
    ]
)
```

### 3. テストカバレッジ確認

```bash
# テスト実行とカバレッジ確認のスクリプト
Filesystem:write_file(
    path="/home/aicompany/ai_co/scripts/check_coverage.sh",
    content="""#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

# カバレッジ付きでテスト実行
pytest tests/ --cov=. --cov-report=term-missing

# 結果をSlackに通知
python3 -c "
from libs.slack_notifier import SlackNotifier
notifier = SlackNotifier()
notifier.send_message('🧪 Test coverage check completed')
"
"""
)
```

## 📊 テスト品質基準

### 必須テストケース

1. **初期化テスト** - すべてのコンポーネントで必須
2. **正常系テスト** - 主要機能の動作確認
3. **異常系テスト** - エラーハンドリング確認
4. **設定テスト** - 設定読み込みの確認

### コンポーネント別要件

| コンポーネント | 必須テスト | 推奨カバレッジ |
|---------------|-----------|---------------|
| Worker | Unit + Integration | 80% |
| Manager | Unit | 80% |
| Core | Unit | 90% |
| Script | Command Test | 70% |

## 🔧 テスト生成時の注意点

### DO ✅
- モックを適切に使用（外部依存を排除）
- テストは独立して実行可能に
- 説明的なテスト名を使用
- アサーションメッセージを含める

### DON'T ❌
- 実際のRabbitMQ接続を使用
- テスト間の依存関係を作る
- sleepを使った待機
- ハードコードされた値

## 📝 実装例

### 完全なワーカー生成（本体＋テスト）

```python
# 1. ワーカー本体
Filesystem:write_file(
    path="/home/aicompany/ai_co/workers/email_worker.py",
    content="""[EmailWorker実装]"""
)

# 2. ユニットテスト
Filesystem:write_file(
    path="/home/aicompany/ai_co/tests/unit/test_email_worker.py",
    content="""[完全なテストコード]"""
)

# 3. 統合テスト（必要に応じて）
Filesystem:write_file(
    path="/home/aicompany/ai_co/tests/integration/test_email_worker_integration.py",
    content="""[統合テストコード]"""
)

# 4. テスト実行確認
Filesystem:write_file(
    path="/home/aicompany/ai_co/scripts/verify_email_worker.sh",
    content="""#!/bin/bash
# 実装とテストの確認
cd /home/aicompany/ai_co
source venv/bin/activate

# テスト実行
ai-test specific email_worker

# 動作確認
python3 workers/email_worker.py --test
"""
)
```

## 🎯 自動適用ルール

### プロンプトへの自動挿入

コード生成リクエストを受けたら、必ず以下を実行：

1. **本体コード生成**
2. **対応するテストコード生成**
3. **テスト実行スクリプト生成**
4. **実行確認コマンドの提示**

### 応答フォーマット

```markdown
実装内容を理解しました。EmailWorkerとそのテストを作成します。

[Filesystem:write_file で本体コード生成]
[Filesystem:write_file でテストコード生成]
[Filesystem:write_file でテスト実行スクリプト生成]

実行とテスト：

```bash
# 権限付与と実行
chmod +x /home/aicompany/ai_co/workers/email_worker.py
chmod +x /home/aicompany/ai_co/scripts/test_email_worker.sh

# テスト実行
cd /home/aicompany/ai_co && ./scripts/test_email_worker.sh

# 本体実行
./workers/email_worker.py
```

これでEmailWorkerの実装とテストが完了しました。
```

---

**🧪 このルールにより、Elders Guildのコードは常にテスト付きで生成されます**
