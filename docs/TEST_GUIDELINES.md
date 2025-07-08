# 🧪 AI Company テスト規約・ガイドライン

## 📋 概要

AI Companyの全コンポーネントに適用される統一的なテスト規約。コード変更時は必ずこの規約に従ってテストを作成・更新する。

## 🎯 テストの原則

### 1. **テストファースト開発**
- 新機能実装前にテストを書く
- 既存コード修正時は先にテストを追加
- テストが通ることを確認してから本実装

### 2. **カバレッジ目標**
- **Core モジュール**: 90%以上
- **Workers**: 80%以上
- **Libs/Managers**: 80%以上
- **Scripts**: 60%以上（主要パスのみ）

### 3. **テストの独立性**
- 各テストは他のテストに依存しない
- テスト順序に関係なく実行可能
- 外部リソース（DB、API）はモック化

## 📂 テストファイル構造

```
tests/
├── __init__.py
├── conftest.py          # pytest設定・共通fixture
├── unit/                # ユニットテスト
│   ├── core/           # Coreモジュールのテスト
│   ├── workers/        # ワーカーのテスト
│   └── libs/           # ライブラリのテスト
├── integration/         # 統合テスト
│   ├── test_worker_chain.py
│   └── test_message_flow.py
├── e2e/                # エンドツーエンドテスト
│   └── test_full_workflow.py
└── fixtures/           # テストデータ
    ├── sample_tasks.json
    └── mock_responses.json
```

## 🔧 テストの命名規則

### ファイル名
```python
# ユニットテスト
test_<module_name>.py  # 例: test_task_worker.py

# 統合テスト
test_<feature>_integration.py  # 例: test_rag_integration.py

# E2Eテスト
test_<workflow>_e2e.py  # 例: test_code_generation_e2e.py
```

### テスト関数名
```python
# 基本パターン
def test_<action>_<condition>_<expected_result>():
    """テストの説明（日本語OK）"""
    pass

# 例
def test_process_message_with_valid_json_returns_success():
    """有効なJSONでメッセージ処理が成功することを確認"""
    pass

def test_process_message_with_invalid_json_raises_exception():
    """無効なJSONで例外が発生することを確認"""
    pass
```

## 📝 テストコード規約

### 1. **AAA パターン**
```python
def test_worker_processes_task():
    # Arrange（準備）
    worker = TaskWorker()
    task_data = {"task_id": "test_123", "prompt": "test"}
    
    # Act（実行）
    result = worker.process_task(task_data)
    
    # Assert（検証）
    assert result["status"] == "success"
    assert "output" in result
```

### 2. **Fixture 活用**
```python
# conftest.py
@pytest.fixture
def mock_task():
    """テスト用タスクデータ"""
    return {
        "task_id": "test_20250702_123456",
        "task_type": "code",
        "prompt": "Create a test function"
    }

@pytest.fixture
def test_worker():
    """設定済みワーカーインスタンス"""
    with patch('pika.BlockingConnection'):
        worker = TaskWorker(worker_id="test-1")
        yield worker
        worker.cleanup()
```

### 3. **モック使用規則**
```python
# 外部依存はすべてモック化
@patch('requests.post')
@patch('pika.BlockingConnection')
def test_slack_notification(mock_rabbit, mock_requests):
    mock_requests.return_value.status_code = 200
    
    notifier = SlackNotifier()
    result = notifier.send_message("test")
    
    assert result is True
    mock_requests.assert_called_once()
```

### 4. **パラメータ化テスト**
```python
@pytest.mark.parametrize("task_type,expected_queue", [
    ("code", "ai_tasks"),
    ("general", "ai_tasks"),
    ("dialog", "ai_dialog"),
])
def test_task_routing(task_type, expected_queue):
    """タスクタイプ別のキュー振り分けを確認"""
    router = TaskRouter()
    queue = router.get_queue(task_type)
    assert queue == expected_queue
```

## 🚀 自動テスト生成ルール

### 新規ファイル作成時
```python
# ワーカー/マネージャー作成時は自動でテストスケルトン生成
# 例: new_worker.py → test_new_worker.py

class TestNewWorker:
    """NewWorkerのテストクラス"""
    
    def test_initialization(self):
        """初期化が正常に行われることを確認"""
        pass
    
    def test_process_message_success(self):
        """メッセージ処理が成功することを確認"""
        pass
    
    def test_error_handling(self):
        """エラーハンドリングが適切に動作することを確認"""
        pass
```

### 既存ファイル修正時
```python
# 修正した関数に対応するテストを必ず追加/更新
# 例: process_message()を修正 → test_process_message_*を確認
```

## 📊 テスト実行コマンド

### 基本コマンド
```bash
# 全テスト実行
ai-test all

# ユニットテストのみ
ai-test unit

# 特定モジュールのテスト
ai-test workers/task_worker

# カバレッジ付き実行
ai-test all --coverage

# 並列実行（高速）
ai-test all --parallel
```

### CI/CD統合
```bash
# プリコミットフック（自動設定済み）
# .git/hooks/pre-commit
#!/bin/bash
ai-test quick || exit 1
```

## 🎯 テスト品質チェックリスト

### コミット前確認事項
- [ ] 新規/修正コードに対応するテストがある
- [ ] すべてのテストが通る
- [ ] カバレッジが基準値以上
- [ ] モックが適切に使用されている
- [ ] テストが独立して実行可能
- [ ] エッジケースがカバーされている

### レビュー観点
1. **正常系テスト**: 期待される動作の確認
2. **異常系テスト**: エラー処理の確認
3. **境界値テスト**: 限界値での動作確認
4. **パフォーマンステスト**: 処理時間の確認（必要な場合）

## 🔧 テストユーティリティ

### 共通ヘルパー関数
```python
# tests/utils.py
def create_mock_task(task_type="code", **kwargs):
    """モックタスクを生成"""
    base_task = {
        "task_id": f"{task_type}_20250702_123456",
        "task_type": task_type,
        "prompt": "Test prompt"
    }
    base_task.update(kwargs)
    return base_task

def assert_slack_called(mock_slack, expected_message):
    """Slack通知が呼ばれたことを確認"""
    mock_slack.assert_called()
    args = mock_slack.call_args[0]
    assert expected_message in args[0]
```

### テストデータ管理
```python
# tests/fixtures/sample_data.py
VALID_TASKS = [
    {"task_id": "code_001", "prompt": "Create function"},
    {"task_id": "general_001", "prompt": "Explain concept"},
]

INVALID_TASKS = [
    {"task_id": None},  # IDなし
    {"prompt": "No ID"},  # IDフィールドなし
    {},  # 空のタスク
]
```

## 🚨 アンチパターン

### 避けるべきこと
```python
# ❌ テスト間の依存
def test_create_user():
    global user_id
    user_id = create_user()

def test_delete_user():
    delete_user(user_id)  # 前のテストに依存

# ❌ 実際の外部API呼び出し
def test_slack_notification():
    notifier = SlackNotifier()
    notifier.send_message("Real message")  # 実際にSlackに送信

# ❌ ハードコーディングされたパス
def test_file_processing():
    process_file("/home/ubuntu/test.txt")  # 環境依存

# ❌ スリープの使用
def test_async_process():
    start_process()
    time.sleep(5)  # 固定時間待機
    check_result()
```

### 推奨パターン
```python
# ✅ 独立したテスト
def test_create_user():
    user = create_user()
    assert user.id is not None
    cleanup_user(user.id)

# ✅ モックの使用
@patch('requests.post')
def test_slack_notification(mock_post):
    mock_post.return_value.status_code = 200
    notifier = SlackNotifier()
    assert notifier.send_message("Test") is True

# ✅ 相対パス使用
def test_file_processing(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    process_file(str(test_file))

# ✅ 明示的な待機
def test_async_process():
    future = start_process()
    result = future.result(timeout=10)
    assert result.status == "completed"
```

## 📈 継続的改善

### メトリクス監視
- テスト実行時間
- カバレッジ推移
- 失敗率
- フレーキーテストの検出

### 定期レビュー
- 月次でテストコードのレビュー
- 不要なテストの削除
- 新しいテストパターンの共有
- ベストプラクティスの更新

---

**🧪 これらの規約により、AI Companyは高品質で保守性の高いコードベースを維持します**
