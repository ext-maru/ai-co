# 🧪 AI Company テストルール・ガイドライン

## 📋 基本原則

### **テストファーストの開発**
```
1. 機能追加・変更時は必ずテストを書く
2. テストが通ってからマージする
3. 既存テストを壊さない
4. テスト結果はSlackに自動通知
```

## 🎯 テストカバレッジ目標

| コンポーネント | 目標カバレッジ | 現状 | 必須テスト |
|---------------|--------------|------|-----------|
| Core基盤 | 90%以上 | - | ユニット + 統合 |
| Workers | 80%以上 | - | ユニット + 統合 |
| Managers | 80%以上 | - | ユニット + 統合 |
| Scripts | 70%以上 | - | 統合のみ |
| 新機能 | 85%以上 | - | ユニット + 統合 |

## 📁 テストファイル構造

```
/home/aicompany/ai_co/tests/
├── unit/                    # ユニットテスト
│   ├── core/               # Coreモジュールのテスト
│   ├── workers/            # ワーカーのテスト
│   ├── libs/               # ライブラリのテスト
│   └── utils/              # ユーティリティのテスト
├── integration/            # 統合テスト
│   ├── test_worker_chain.py    # ワーカー連携テスト
│   ├── test_message_flow.py    # メッセージフローテスト
│   └── test_e2e.py            # エンドツーエンドテスト
├── performance/            # パフォーマンステスト
│   └── test_load.py       # 負荷テスト
├── fixtures/              # テストデータ
└── conftest.py           # pytest設定
```

## 🔧 テスト実装ルール

### 1. ファイル命名規則
```python
# ユニットテスト
test_<module_name>.py      # 例: test_base_worker.py

# 統合テスト
test_integration_<feature>.py  # 例: test_integration_task_flow.py

# テストクラス
class Test<ClassName>:     # 例: class TestBaseWorker:

# テストメソッド
def test_<what_it_does>(): # 例: def test_handles_invalid_json():
```

### 2. テストの構造（AAA Pattern）
```python
def test_worker_processes_message_successfully():
    """ワーカーがメッセージを正常に処理することを確認"""
    # Arrange（準備）
    worker = TaskWorker()
    test_message = {"task_id": "test_123", "prompt": "test"}
    
    # Act（実行）
    result = worker.process_test_message(test_message)
    
    # Assert（検証）
    assert result["status"] == "completed"
    assert "output" in result
```

### 3. モックの使用
```python
from unittest.mock import Mock, patch, MagicMock

@patch('pika.BlockingConnection')
@patch('libs.slack_notifier.SlackNotifier')
def test_worker_with_mocks(mock_slack, mock_connection):
    """外部依存をモック化したテスト"""
    # RabbitMQとSlackをモック化
    mock_connection.return_value = MagicMock()
    mock_slack.return_value.send_message = MagicMock()
    
    worker = BaseWorker(worker_type='test')
    assert worker.connection is not None
```

### 4. フィクスチャの活用
```python
import pytest

@pytest.fixture
def worker_instance():
    """再利用可能なワーカーインスタンス"""
    worker = TaskWorker()
    yield worker
    worker.cleanup()

@pytest.fixture
def sample_task():
    """テスト用タスクデータ"""
    return {
        "task_id": "test_20250702_120000",
        "task_type": "code",
        "prompt": "Create a test function"
    }
```

## 🚀 自動テスト生成ルール

### ワーカー/マネージャー作成時
```python
# 新規ワーカー作成時は必ず対応するテストも生成
def create_worker_with_test(worker_name: str):
    # 1. ワーカー本体を作成
    create_worker_file(worker_name)
    
    # 2. 対応するユニットテストを自動生成
    create_unit_test(worker_name)
    
    # 3. 統合テストに追加
    add_to_integration_test(worker_name)
```

### テストテンプレート
```python
# tests/templates/unit_test_template.py
UNIT_TEST_TEMPLATE = """
import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from {module_path} import {class_name}

class Test{class_name}:
    
    @pytest.fixture
    def {instance_name}(self):
        with patch('pika.BlockingConnection'):
            instance = {class_name}()
            yield instance
            instance.cleanup()
    
    def test_initialization(self, {instance_name}):
        '''初期化が正常に行われることを確認'''
        assert {instance_name} is not None
        assert {instance_name}.worker_type == '{worker_type}'
    
    def test_process_message_success(self, {instance_name}):
        '''メッセージ処理が成功することを確認'''
        # テストデータ
        test_body = {test_data}
        
        # 実行
        result = {instance_name}.process_test_message(test_body)
        
        # 検証
        assert result is not None
        assert result.get('status') == 'success'
    
    def test_error_handling(self, {instance_name}):
        '''エラーハンドリングが適切に動作することを確認'''
        # 不正なデータ
        invalid_body = {{"invalid": "data"}}
        
        # エラーが適切に処理されることを確認
        with pytest.raises(Exception):
            {instance_name}.process_test_message(invalid_body)
    
    @patch('libs.slack_notifier.SlackNotifier')
    def test_slack_notification(self, mock_slack, {instance_name}):
        '''Slack通知が送信されることを確認'''
        mock_slack.return_value.send_message = Mock()
        
        # 処理実行
        {instance_name}._notify_completion("Test completed")
        
        # Slack通知が呼ばれたことを確認
        mock_slack.return_value.send_message.assert_called_once()
"""
```

## 📊 テスト実行コマンド

### 基本コマンド
```bash
# 全テスト実行
ai-test all

# ユニットテストのみ
ai-test unit

# 統合テストのみ
ai-test integration

# 特定モジュールのテスト
ai-test module <module_name>

# カバレッジ付き実行
ai-test coverage

# 変更されたファイルのテストのみ
ai-test changed
```

### CI/CD統合
```yaml
# .github/workflows/test.yml
name: AI Company Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Run tests
      run: |
        ./scripts/ai-test all
        ./scripts/ai-test coverage
```

## 🔄 変更時のテストフロー

### 1. プレコミットフック
```bash
#!/bin/bash
# .git/hooks/pre-commit

# 変更されたPythonファイルを取得
changed_files=$(git diff --cached --name-only --diff-filter=ACM | grep "\.py$")

if [ -n "$changed_files" ]; then
    echo "🧪 Running tests for changed files..."
    
    # 各ファイルに対応するテストを実行
    for file in $changed_files; do
        test_file="tests/unit/test_$(basename $file)"
        if [ -f "$test_file" ]; then
            pytest "$test_file" -v
            if [ $? -ne 0 ]; then
                echo "❌ Tests failed for $file"
                exit 1
            fi
        else
            echo "⚠️  No test found for $file"
            # テストがない場合は警告（後でエラーに変更）
        fi
    done
fi

echo "✅ All tests passed"
```

### 2. マージ前チェック
```python
# scripts/check_test_coverage.py
def check_coverage_before_merge():
    """マージ前のカバレッジチェック"""
    
    # カバレッジ計測
    coverage_result = run_coverage_test()
    
    # 基準チェック
    if coverage_result['total'] < 80:
        raise Exception(f"Coverage {coverage_result['total']}% is below 80%")
    
    # Slack通知
    notify_slack(f"✅ Coverage: {coverage_result['total']}%")
```

## 🎯 テスト品質基準

### 1. 単体テストの基準
- 各パブリックメソッドに最低1つのテスト
- 正常系と異常系の両方をカバー
- 外部依存はモック化
- 実行時間は1テスト5秒以内

### 2. 統合テストの基準
- 主要なユースケースをカバー
- ワーカー間の連携を検証
- 実際のRabbitMQを使用（テスト用キュー）
- 実行時間は1テスト30秒以内

### 3. コードレビュー時のチェック項目
- [ ] 新機能/変更にテストがあるか
- [ ] テストが意味のある検証をしているか
- [ ] エッジケースがカバーされているか
- [ ] モックが適切に使われているか
- [ ] テストが独立して実行可能か

## 📈 テストメトリクス

### 自動収集されるメトリクス
```python
{
    "total_tests": 150,
    "passed": 148,
    "failed": 2,
    "skipped": 0,
    "coverage": {
        "total": 85.5,
        "core": 92.3,
        "workers": 88.1,
        "libs": 79.8
    },
    "execution_time": 45.6,
    "slowest_tests": [
        {"name": "test_heavy_load", "time": 8.2},
        {"name": "test_integration_full_flow", "time": 6.1}
    ]
}
```

### Slack通知フォーマット
```
✅ Test Results: 148/150 passed (98.7%)
Coverage: 85.5% | Time: 45.6s
Failed: test_worker_timeout, test_invalid_config
Details: http://localhost:8080/test-report
```

## 🚨 テスト失敗時の対応

### 1. 自動リトライ
```python
@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_network_dependent():
    """ネットワーク依存のテストは3回までリトライ"""
    pass
```

### 2. 失敗の自動分析
```python
def analyze_test_failure(test_name, error):
    """テスト失敗の自動分析"""
    
    # エラータイプ分類
    if "timeout" in str(error).lower():
        return "Timeout issue - check network/service"
    elif "connection" in str(error).lower():
        return "Connection issue - check RabbitMQ"
    elif "import" in str(error).lower():
        return "Import error - check dependencies"
    
    return "Unknown error - manual investigation needed"
```

---

**🧪 このテストルールにより、AI Companyは高品質で信頼性の高いシステムを維持します**