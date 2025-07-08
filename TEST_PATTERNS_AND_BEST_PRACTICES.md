# AI Company テストパターン & ベストプラクティス集

## 📚 確立されたテストパターン

### 1. 完全モック化パターン

#### 1.1 RabbitMQ モックパターン
```python
from unittest.mock import Mock, patch, MagicMock

class MockChannel:
    def __init__(self):
        self.queue_declare = Mock()
        self.basic_consume = Mock()
        self.basic_publish = Mock()
        self.start_consuming = Mock()
        self.stop_consuming = Mock()
        self.close = Mock()

class MockConnection:
    def __init__(self):
        self.channel = Mock(return_value=MockChannel())
        self.close = Mock()
        self.is_closed = False

@pytest.fixture
def mock_rabbitmq():
    with patch('pika.BlockingConnection', return_value=MockConnection()):
        yield
```

#### 1.2 Slack SDK モックパターン
```python
@pytest.fixture
def mock_slack_client():
    mock_client = Mock()
    mock_client.chat_postMessage = Mock(return_value={'ok': True})
    mock_client.conversations_list = Mock(return_value={
        'ok': True,
        'channels': [{'id': 'C123', 'name': 'general'}]
    })
    
    with patch('slack_sdk.WebClient', return_value=mock_client):
        yield mock_client
```

#### 1.3 ファイルシステムモックパターン
```python
@pytest.fixture
def mock_filesystem(tmp_path):
    """一時ファイルシステムを使用したテスト"""
    test_dir = tmp_path / "test_workspace"
    test_dir.mkdir()
    
    # テストファイルの作成
    (test_dir / "config.json").write_text('{"test": true}')
    (test_dir / "data.txt").write_text("test data")
    
    with patch('pathlib.Path.home', return_value=tmp_path):
        yield test_dir
```

### 2. Worker テストパターン

#### 2.1 基本Workerテストテンプレート
```python
class TestWorkerTemplate:
    """全てのWorkerテストが継承すべき基本クラス"""
    
    @pytest.fixture
    def worker_config(self):
        return {
            'name': 'test_worker',
            'input_queue': 'test.in',
            'output_queues': ['test.out'],
            'error_queue': 'test.error'
        }
    
    @pytest.fixture
    def mock_dependencies(self):
        """共通の依存関係をモック"""
        with patch('pika.BlockingConnection'):
            with patch('core.config.get_config'):
                with patch('libs.slack_notifier.SlackNotifier'):
                    yield
    
    @pytest.fixture
    def worker(self, worker_config, mock_dependencies):
        """テスト対象のWorkerインスタンス"""
        return self.worker_class(**worker_config)
    
    def test_initialization(self, worker, worker_config):
        """初期化テスト"""
        assert worker.name == worker_config['name']
        assert worker.input_queue == worker_config['input_queue']
    
    def test_process_valid_message(self, worker):
        """正常メッセージ処理テスト"""
        message = self.create_valid_message()
        result = worker.process_message(message)
        assert result['status'] == 'completed'
    
    def test_process_invalid_message(self, worker):
        """異常メッセージ処理テスト"""
        message = self.create_invalid_message()
        with pytest.raises(ValueError):
            worker.process_message(message)
    
    @pytest.mark.parametrize("error_type,expected_action", [
        (ConnectionError, 'retry'),
        (ValueError, 'reject'),
        (TimeoutError, 'requeue'),
    ])
    def test_error_handling(self, worker, error_type, expected_action):
        """エラーハンドリングテスト"""
        worker.process_message = Mock(side_effect=error_type)
        action = worker.handle_error(error_type())
        assert action == expected_action
```

#### 2.2 非同期Workerテストパターン
```python
@pytest.mark.asyncio
class TestAsyncWorker:
    @pytest.fixture
    async def async_worker(self):
        worker = AsyncWorker()
        await worker.initialize()
        yield worker
        await worker.cleanup()
    
    async def test_async_process(self, async_worker):
        result = await async_worker.process_async(test_data)
        assert result['status'] == 'success'
    
    async def test_concurrent_processing(self, async_worker):
        """並行処理テスト"""
        tasks = [
            async_worker.process_async(data)
            for data in test_data_list
        ]
        results = await asyncio.gather(*tasks)
        assert all(r['status'] == 'success' for r in results)
```

### 3. 統合テストパターン

#### 3.1 マルチワーカー統合テスト
```python
class TestWorkerIntegration:
    @pytest.fixture
    def worker_chain(self, mock_dependencies):
        """ワーカーチェーンのセットアップ"""
        task_worker = TaskWorker()
        pm_worker = PMWorker()
        result_worker = ResultWorker()
        
        # キューを接続
        task_worker.output_queues = ['pm.input']
        pm_worker.input_queue = 'pm.input'
        pm_worker.output_queues = ['result.input']
        result_worker.input_queue = 'result.input'
        
        return task_worker, pm_worker, result_worker
    
    def test_full_workflow(self, worker_chain):
        """完全なワークフローテスト"""
        task_worker, pm_worker, result_worker = worker_chain
        
        # タスク投入
        initial_task = {'type': 'test', 'data': 'test_data'}
        task_result = task_worker.process_message(initial_task)
        
        # PM処理
        pm_result = pm_worker.process_message(task_result)
        
        # 結果処理
        final_result = result_worker.process_message(pm_result)
        
        assert final_result['status'] == 'completed'
        assert 'results' in final_result
```

### 4. パフォーマンステストパターン

#### 4.1 ベンチマークテスト
```python
@pytest.mark.benchmark
def test_performance_process_message(benchmark, worker):
    """メッセージ処理のパフォーマンステスト"""
    test_message = create_test_message()
    
    result = benchmark(worker.process_message, test_message)
    
    assert result['status'] == 'completed'
    # ベンチマーク統計が自動的に生成される
```

#### 4.2 負荷テスト
```python
def test_high_load_processing(worker):
    """高負荷処理テスト"""
    message_count = 1000
    messages = [create_test_message() for _ in range(message_count)]
    
    start_time = time.time()
    results = []
    
    for message in messages:
        result = worker.process_message(message)
        results.append(result)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # パフォーマンス基準
    assert duration < 10  # 10秒以内
    assert all(r['status'] == 'completed' for r in results)
    
    # スループット計算
    throughput = message_count / duration
    assert throughput > 100  # 100 msg/sec 以上
```

### 5. テストデータ管理パターン

#### 5.1 フィクスチャファクトリー
```python
@pytest.fixture
def task_factory():
    """タスクデータのファクトリー"""
    def _create_task(task_type='default', **kwargs):
        base_task = {
            'task_id': str(uuid.uuid4()),
            'type': task_type,
            'timestamp': datetime.now().isoformat(),
            'user_id': 'test_user',
            'data': {}
        }
        base_task.update(kwargs)
        return base_task
    return _create_task

@pytest.fixture
def message_factory(task_factory):
    """RabbitMQメッセージのファクトリー"""
    def _create_message(task_type='default', **kwargs):
        task = task_factory(task_type, **kwargs)
        return {
            'body': json.dumps(task).encode(),
            'properties': Mock(
                reply_to='test.reply',
                correlation_id=task['task_id']
            )
        }
    return _create_message
```

#### 5.2 テストデータセット
```python
class TestDataSets:
    """共通テストデータセット"""
    
    VALID_TASKS = [
        {'type': 'text_analysis', 'data': {'text': 'Hello World'}},
        {'type': 'image_processing', 'data': {'image_url': 'http://example.com/image.jpg'}},
        {'type': 'data_validation', 'data': {'schema': {}, 'data': {}}},
    ]
    
    INVALID_TASKS = [
        {},  # 空のタスク
        {'type': 'unknown'},  # 未知のタイプ
        {'type': 'text_analysis'},  # データなし
        {'type': None, 'data': {}},  # Nullタイプ
    ]
    
    ERROR_TASKS = [
        {'type': 'error_simulation', 'data': {'error_type': 'timeout'}},
        {'type': 'error_simulation', 'data': {'error_type': 'memory'}},
        {'type': 'error_simulation', 'data': {'error_type': 'permission'}},
    ]
```

### 6. アサーションパターン

#### 6.1 構造化アサーション
```python
def assert_valid_result(result):
    """結果の妥当性を検証する構造化アサーション"""
    # 必須フィールドの存在確認
    assert 'status' in result
    assert 'task_id' in result
    assert 'timestamp' in result
    
    # 値の妥当性確認
    assert result['status'] in ['completed', 'failed', 'pending']
    assert isinstance(result['timestamp'], str)
    
    # 条件付きアサーション
    if result['status'] == 'completed':
        assert 'results' in result
        assert result['results'] is not None
    elif result['status'] == 'failed':
        assert 'error' in result
        assert 'error_code' in result

def assert_performance_metrics(metrics):
    """パフォーマンスメトリクスの検証"""
    assert metrics['response_time'] < 1000  # 1秒以内
    assert metrics['memory_usage'] < 500 * 1024 * 1024  # 500MB以内
    assert metrics['cpu_usage'] < 80  # 80%以内
```

### 7. エラーシミュレーションパターン

#### 7.1 障害注入テスト
```python
class FaultInjector:
    """障害注入ユーティリティ"""
    
    @staticmethod
    def simulate_network_error(probability=0.1):
        """ネットワークエラーをシミュレート"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                if random.random() < probability:
                    raise ConnectionError("Simulated network error")
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def simulate_timeout(timeout_seconds=1):
        """タイムアウトをシミュレート"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                time.sleep(timeout_seconds)
                raise TimeoutError("Simulated timeout")
            return wrapper
        return decorator

# 使用例
@FaultInjector.simulate_network_error(probability=0.5)
def unreliable_network_call():
    return "success"
```

## 📋 ベストプラクティス

### 1. テスト命名規則
- `test_<対象>_<条件>_<期待結果>`
- 例: `test_worker_with_invalid_input_raises_exception`

### 2. テスト構造 (AAA パターン)
```python
def test_example():
    # Arrange (準備)
    worker = create_test_worker()
    test_data = create_test_data()
    
    # Act (実行)
    result = worker.process(test_data)
    
    # Assert (検証)
    assert result['status'] == 'success'
```

### 3. テストの独立性
- 各テストは他のテストに依存しない
- テスト順序に関わらず実行可能
- 共有状態を避ける

### 4. モックの適切な使用
- 外部依存は必ずモック
- 内部実装はモックしない
- モックは最小限に

### 5. パラメータ化テストの活用
```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("", ""),
    (None, None),
])
def test_uppercase(input, expected):
    assert uppercase(input) == expected
```

## 🎯 カバレッジ向上のコツ

1. **エッジケースを網羅**: 境界値、null、空配列など
2. **エラーパスをテスト**: 例外処理、エラーハンドリング
3. **条件分岐を全て通る**: if/else、switch文の全パス
4. **ループの境界**: 0回、1回、多数回
5. **並行処理**: 競合状態、デッドロック

---

*このドキュメントは、AI Companyのテスト品質向上のための生きたガイドラインです。*