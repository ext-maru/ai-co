"""
Mock responses and helpers for testing
"""

# Add project root to Python path
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
from unittest.mock import Mock, MagicMock
import time


class MockResponses:
    """テスト用のモックレスポンス集"""
    
    # サンプルデータファイルの読み込み
    FIXTURES_DIR = Path(__file__).parent
    with open(FIXTURES_DIR / 'sample_data.json', 'r') as f:
        SAMPLE_DATA = json.load(f)
    
    @classmethod
    def get_claude_success_response(cls):
        """Claudeの成功レスポンスを返す"""
        return Mock(
            returncode=0,
            stdout=cls.SAMPLE_DATA['claude_responses']['success']['stdout'],
            stderr=''
        )
    
    @classmethod
    def get_claude_error_response(cls):
        """Claudeのエラーレスポンスを返す"""
        return Mock(
            returncode=1,
            stdout='',
            stderr=cls.SAMPLE_DATA['claude_responses']['error']['stderr']
        )
    
    @classmethod
    def get_claude_with_files_response(cls):
        """ファイル作成を含むClaudeレスポンスを返す"""
        return Mock(
            returncode=0,
            stdout=cls.SAMPLE_DATA['claude_responses']['with_files']['stdout'],
            stderr=''
        )
    
    @classmethod
    def create_mock_channel(cls):
        """RabbitMQチャネルのモックを作成"""
        channel = Mock()
        channel.queue_declare = Mock()
        channel.basic_consume = Mock()
        channel.basic_publish = Mock()
        channel.basic_ack = Mock()
        channel.start_consuming = Mock()
        return channel
    
    @classmethod
    def create_mock_connection(cls, channel=None):
        """RabbitMQ接続のモックを作成"""
        if channel is None:
            channel = cls.create_mock_channel()
        
        connection = Mock()
        connection.channel.return_value = channel
        connection.is_open = True
        connection.close = Mock()
        return connection
    
    @classmethod
    def create_mock_task_message(cls, task_type='code', task_id=None):
        """タスクメッセージのモックを作成"""
        if task_id is None:
            task_id = f"{task_type}_{int(time.time())}"
        
        task = cls.SAMPLE_DATA['sample_tasks'][0].copy()
        task['task_id'] = task_id
        task['type'] = task_type
        
        method = Mock()
        method.delivery_tag = 1
        
        properties = Mock()
        
        body = json.dumps(task)
        
        return Mock(), method, properties, body
    
    @classmethod
    def create_mock_slack_notifier(cls):
        """SlackNotifierのモックを作成"""
        notifier = Mock()
        notifier.send_message = Mock(return_value=True)
        notifier.send_task_notification = Mock(return_value=True)
        notifier.send_error_notification = Mock(return_value=True)
        return notifier
    
    @classmethod
    def create_mock_rag_manager(cls):
        """RAGManagerのモックを作成"""
        rag = Mock()
        rag.search_similar_tasks = Mock(return_value=[])
        rag.generate_enhanced_prompt = Mock(
            side_effect=lambda prompt, *args: f"Enhanced: {prompt}"
        )
        rag.save_task = Mock()
        return rag
    
    @classmethod
    def create_mock_conversation_manager(cls):
        """ConversationManagerのモックを作成"""
        conv_manager = Mock()
        conv_manager.create_conversation = Mock(
            return_value=cls.SAMPLE_DATA['sample_conversations'][0]
        )
        conv_manager.get_conversation = Mock(
            return_value=cls.SAMPLE_DATA['sample_conversations'][0]
        )
        conv_manager.add_message = Mock()
        conv_manager.update_status = Mock()
        return conv_manager
    
    @classmethod
    def create_mock_config(cls):
        """設定オブジェクトのモックを作成"""
        config = MagicMock()
        test_config = cls.SAMPLE_DATA['sample_configs']['test_config']
        
        # ドット記法でアクセスできるように設定
        config.worker.default_model = test_config['worker']['default_model']
        config.worker.timeout = test_config['worker']['timeout']
        config.worker.retry_count = test_config['worker']['retry_count']
        config.slack.enabled = test_config['slack']['enabled']
        config.slack.webhook_url = test_config['slack']['webhook_url']
        
        # get メソッドも実装
        config.get = Mock(side_effect=lambda key, default=None: {
            'worker.default_model': test_config['worker']['default_model'],
            'worker.timeout': test_config['worker']['timeout'],
            'slack.enabled': test_config['slack']['enabled']
        }.get(key, default))
        
        return config


class MockDatabase:
    """テスト用のモックデータベース"""
    
    def __init__(self):
        self.data = {}
        self.tables = {
            'task_history': [],
            'conversations': [],
            'messages': []
        }
    
    def execute(self, query, params=None):
        """SQLクエリの実行をシミュレート"""
        query_lower = query.lower()
        
        if 'insert into task_history' in query_lower:
            task = {
                'task_id': params[0] if params else 'test_123',
                'prompt': params[1] if params and len(params) > 1 else 'test prompt',
                'status': 'pending'
            }
            self.tables['task_history'].append(task)
            return Mock(lastrowid=len(self.tables['task_history']))
        
        elif 'select' in query_lower and 'from task_history' in query_lower:
            return Mock(fetchall=lambda: self.tables['task_history'],
                       fetchone=lambda: self.tables['task_history'][0] if self.tables['task_history'] else None)
        
        return Mock()
    
    def commit(self):
        """コミットをシミュレート"""
        pass
    
    def rollback(self):
        """ロールバックをシミュレート"""
        pass
    
    def close(self):
        """接続クローズをシミュレート"""
        pass


class TestHelpers:
    """テスト用のヘルパー関数"""
    
    @staticmethod
    def create_temp_config(config_dict):
        """一時的な設定ファイルを作成"""
        import tempfile
        import json
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_dict, f, indent=2)
            return f.name
    
    @staticmethod
    def wait_for_condition(condition_func, timeout=5, interval=0.1):
        """条件が満たされるまで待機"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            time.sleep(interval)
        return False
    
    @staticmethod
    def capture_logs(logger_name):
        """ログ出力をキャプチャ"""
        import logging
        from io import StringIO
        
        logger = logging.getLogger(logger_name)
        original_handlers = logger.handlers[:]
        
        # StringIOハンドラを追加
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        logger.addHandler(handler)
        
        class LogCapture:
            def __enter__(self):
                return log_capture
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                # 元のハンドラに戻す
                logger.handlers = original_handlers
        
        return LogCapture()
    
    @staticmethod
    def create_mock_subprocess_run(outputs):
        """subprocess.runのモックを作成（複数の出力に対応）"""
        outputs_iter = iter(outputs)
        
        def mock_run(*args, **kwargs):
            try:
                return next(outputs_iter)
            except StopIteration:
                return outputs[-1]  # 最後の出力を繰り返す
        
        return mock_run
