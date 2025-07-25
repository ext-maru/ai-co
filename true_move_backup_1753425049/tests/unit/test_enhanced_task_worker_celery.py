#!/usr/bin/env python3
"""
Enhanced Task Worker Celery版 テストスイート
Issue #93: OSS移行プロジェクト - pytest移行完了版
"""
import json
import os
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# テスト対象のimport
from workers.enhanced_task_worker_celery import (
    CeleryTaskWorkerConfig,
    app,
    claude_task,
    notification_task,
    sage_consultation,
    _execute_claude_cli,
    _consult_knowledge_sage,
    _consult_task_sage,
    _consult_incident_sage,
    _consult_rag_sage,
    _send_slack_notification,
)


@pytest.fixture
def temp_output_dir():
    """一時出力ディレクトリ"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config():
    """モック設定"""
    config = MagicMock()
    config.WORKER_DEFAULT_MODEL = "claude-sonnet-4-20250514"
    config.WORKER_ALLOWED_TOOLS = ["bash", "editor"]
    return config


@pytest.fixture
def celery_config(temp_output_dir, mock_config):
    """Celery設定のテスト用インスタンス"""
    with patch('workers.enhanced_task_worker_celery.get_config', return_value=mock_config):
        with patch('workers.enhanced_task_worker_celery.PROJECT_ROOT', temp_output_dir):
            config = CeleryTaskWorkerConfig()
            config.output_dir = temp_output_dir
            return config


@pytest.fixture
def claude_task_data():
    """Claude task用テストデータ"""
    return {
        'task_id': 'test_task_001',
        'prompt': 'テスト用プロンプト',
        'context': {'project': 'test_project'},
        'options': {'model': 'claude-sonnet-4', 'timeout': 60}
    }


@pytest.fixture
def sage_consultation_data():
    """Sage consultation用テストデータ"""
    return {
        'task_id': 'test_consultation_001',
        'task_data': {'type': 'analysis'},
        'claude_result': {'success': True, 'output': 'test output'}
    }


@pytest.fixture
def notification_data():
    """Notification用テストデータ"""
    return {
        'type': 'success',
        'task_id': 'test_notification_001',
        'message': 'タスクが完了しました',
        'context': {'user': 'test_user'}
    }


class TestCeleryTaskWorkerConfig:
    """CeleryTaskWorkerConfig テストクラス"""

    def test_config_initialization(self, celery_config, temp_output_dir):
        """設定の初期化テスト"""
        assert celery_config.output_dir == temp_output_dir
        assert celery_config.output_dir.exists()
        assert celery_config.claude_cmd in ["claude", "/usr/local/bin/claude", "/opt/homebrew/bin/claude"]

    def test_get_claude_command_default(self, celery_config):
        """Claude コマンド取得（デフォルト）テスト"""
        # 実行可能ファイルが見つからない場合はデフォルト
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            cmd = celery_config._get_claude_command()
            assert cmd == "claude"

    @patch('subprocess.run')
    def test_get_claude_command_found(self, mock_run, celery_config):
        """Claude コマンド取得（見つかった場合）テスト"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        cmd = celery_config._get_claude_command()
        assert cmd in ["/usr/local/bin/claude", "/opt/homebrew/bin/claude", "claude"]

    def test_elder_integration_disabled(self, temp_output_dir, mock_config):
        """エルダーズギルド統合無効時のテスト"""
        with patch('workers.enhanced_task_worker_celery.ELDER_INTEGRATION_AVAILABLE', False):
            with patch('workers.enhanced_task_worker_celery.get_config', return_value=mock_config):
                with patch('workers.enhanced_task_worker_celery.PROJECT_ROOT', temp_output_dir):
                    config = CeleryTaskWorkerConfig()
                    assert not config.elder_integration


class TestClaudeTask:
    """claude_task テストクラス"""

    @patch('workers.enhanced_task_worker_celery._execute_claude_cli')
    def test_claude_task_success(self, mock_execute, claude_task_data):
        """Claude task成功テスト"""
        # モック設定
        mock_execute.return_value = {
            'returncode': 0,
            'stdout': 'Success output',
            'stderr': '',
            'success': True
        }
        
        # タスク実行
        result = claude_task(claude_task_data)
        
        # 検証
        assert result['success'] is True
        assert result['task_id'] == 'test_task_001'
        assert 'result' in result
        assert 'completed_at' in result
        mock_execute.assert_called_once()

    @patch('workers.enhanced_task_worker_celery._execute_claude_cli')
    @patch('workers.enhanced_task_worker_celery.notification_task')
    def test_claude_task_failure(self, mock_notification, mock_execute, claude_task_data):
        """Claude task失敗テスト"""
        # モック設定
        mock_execute.side_effect = Exception("CLI execution failed")
        mock_notification.delay = MagicMock()
        
        # タスク実行
        result = claude_task(claude_task_data)
        
        # 検証
        assert result['success'] is False
        assert result['task_id'] == 'test_task_001'
        assert 'error' in result
        assert 'failed_at' in result
        mock_notification.delay.assert_called_once()

    @patch('workers.enhanced_task_worker_celery.notification_task')
    def test_claude_task_empty_prompt(self, mock_notification):
        """空プロンプトのテスト"""
        # notification_taskをモック化
        mock_notification.delay = MagicMock()
        
        task_data = {
            'task_id': 'empty_prompt_test',
            'prompt': '',
            'context': {},
            'options': {}
        }
        
        result = claude_task(task_data)
        
        assert result['success'] is False
        assert 'プロンプトが空です' in result['error']

    @patch('workers.enhanced_task_worker_celery.sage_consultation')
    @patch('workers.enhanced_task_worker_celery._execute_claude_cli')
    @patch('workers.enhanced_task_worker_celery.task_config')
    def test_claude_task_with_sage_consultation(self, mock_config, mock_execute, mock_sage, claude_task_data):
        """Sage consultation付きClaude taskテスト"""
        # モック設定
        mock_config.elder_integration = True
        mock_execute.return_value = {'success': True, 'output': 'test'}
        mock_sage.delay = MagicMock()
        mock_sage.delay.return_value.id = 'sage_task_123'
        
        # Sage consultation有効化
        claude_task_data['options']['enable_sage_consultation'] = True
        
        # タスク実行
        result = claude_task(claude_task_data)
        
        # 検証
        assert result['success'] is True
        assert result['result']['sage_consultation_id'] == 'sage_task_123'  # result内に入っている
        mock_sage.delay.assert_called_once()


class TestSageConsultation:
    """sage_consultation テストクラス"""

    @patch('workers.enhanced_task_worker_celery.task_config')
    @patch('workers.enhanced_task_worker_celery._consult_knowledge_sage')
    @patch('workers.enhanced_task_worker_celery._consult_task_sage')
    @patch('workers.enhanced_task_worker_celery._consult_incident_sage')
    @patch('workers.enhanced_task_worker_celery._consult_rag_sage')
    def test_sage_consultation_success(self, mock_rag, mock_incident, mock_task, mock_knowledge, 
                                     mock_config, sage_consultation_data):
        """Sage consultation成功テスト"""
        # モック設定
        mock_config.elder_integration = True
        mock_knowledge.return_value = {'sage': 'knowledge', 'status': 'success'}
        mock_task.return_value = {'sage': 'task', 'status': 'success'}
        mock_incident.return_value = {'sage': 'incident', 'status': 'success'}
        mock_rag.return_value = {'sage': 'rag', 'status': 'success'}
        
        # タスク実行
        result = sage_consultation(sage_consultation_data)
        
        # 検証
        assert result['success'] is True
        assert result['task_id'] == 'test_consultation_001'
        assert 'sage_results' in result
        assert len(result['sage_results']) == 4
        assert 'completed_at' in result

    @patch('workers.enhanced_task_worker_celery.task_config')
    def test_sage_consultation_integration_disabled(self, mock_config, sage_consultation_data):
        """エルダーズギルド統合無効時のテスト"""
        mock_config.elder_integration = False
        
        result = sage_consultation(sage_consultation_data)
        
        assert result['success'] is False
        assert 'エルダーズギルド統合が無効です' in result['error']

    @patch('workers.enhanced_task_worker_celery.task_config')
    @patch('workers.enhanced_task_worker_celery._consult_knowledge_sage')
    def test_sage_consultation_error(self, mock_knowledge, mock_config, sage_consultation_data):
        """Sage consultation エラーテスト"""
        mock_config.elder_integration = True
        mock_knowledge.side_effect = Exception("Sage consultation failed")
        
        result = sage_consultation(sage_consultation_data)
        
        assert result['success'] is False
        assert 'error' in result


class TestNotificationTask:
    """notification_task テストクラス"""

    @patch.dict(os.environ, {'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/test'})
    @patch('workers.enhanced_task_worker_celery._send_slack_notification')
    def test_notification_task_slack(self, mock_slack, notification_data):
        """Slack通知テスト"""
        mock_slack.return_value = None
        
        result = notification_task(notification_data)
        
        assert result['success'] is True
        assert result['notification_type'] == 'success'
        assert result['task_id'] == 'test_notification_001'
        mock_slack.assert_called_once()

    @patch.dict(os.environ, {'SMTP_HOST': 'localhost'})
    @patch('workers.enhanced_task_worker_celery._send_email_notification')
    def test_notification_task_email(self, mock_email, notification_data):
        """メール通知テスト"""
        mock_email.return_value = None
        
        result = notification_task(notification_data)
        
        assert result['success'] is True
        mock_email.assert_called_once()

    def test_notification_task_no_config(self, notification_data):
        """通知設定なしのテスト"""
        with patch.dict(os.environ, {}, clear=True):
            result = notification_task(notification_data)
            
            assert result['success'] is True  # 設定がなくても成功扱い

    @patch('workers.enhanced_task_worker_celery._send_slack_notification')
    def test_notification_task_error(self, mock_slack, notification_data):
        """通知タスクエラーテスト"""
        mock_slack.side_effect = Exception("Notification failed")
        
        with patch.dict(os.environ, {'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/test'}):
            result = notification_task(notification_data)
            
            assert result['success'] is False
            assert 'error' in result


class TestHelperFunctions:
    """ヘルパー関数テストクラス"""

    @patch('subprocess.run')
    def test_execute_claude_cli_success(self, mock_run, temp_output_dir):
        """Claude CLI実行成功テスト"""
        # モック設定
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # task_configのモック
        with patch('workers.enhanced_task_worker_celery.task_config') as mock_config:
            mock_config.output_dir = temp_output_dir
            mock_config.claude_cmd = "claude"
            
            result = _execute_claude_cli(
                task_id="test_001",
                prompt="test prompt",
                context={},
                options={}
            )
        
        assert result['success'] is True
        assert result['returncode'] == 0
        assert result['stdout'] == "Success output"

    @patch('subprocess.run')
    def test_execute_claude_cli_timeout(self, mock_run, temp_output_dir):
        """Claude CLI タイムアウトテスト"""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("claude", 300)
        
        with patch('workers.enhanced_task_worker_celery.task_config') as mock_config:
            mock_config.output_dir = temp_output_dir
            mock_config.claude_cmd = "claude"
            
            with pytest.raises(Exception, match="タイムアウト"):
                _execute_claude_cli(
                    task_id="test_timeout",
                    prompt="test prompt",
                    context={},
                    options={'timeout': 1}
                )

    def test_consult_knowledge_sage_success(self):
        """Knowledge Sage相談成功テスト"""
        request = {'task_id': 'test', 'type': 'consultation'}
        
        result = _consult_knowledge_sage(request)
        
        assert result['sage'] == 'knowledge'
        assert result['status'] == 'success'
        assert 'advice' in result
        assert 'confidence' in result

    def test_consult_task_sage_success(self):
        """Task Sage相談成功テスト"""
        request = {'task_id': 'test', 'type': 'consultation'}
        
        result = _consult_task_sage(request)
        
        assert result['sage'] == 'task'
        assert result['status'] == 'success'
        assert 'optimization' in result
        assert 'priority_score' in result

    def test_consult_incident_sage_success(self):
        """Incident Sage相談成功テスト"""
        request = {'task_id': 'test', 'type': 'consultation'}
        
        result = _consult_incident_sage(request)
        
        assert result['sage'] == 'incident'
        assert result['status'] == 'success'
        assert 'risk_assessment' in result
        assert 'mitigation' in result

    def test_consult_rag_sage_success(self):
        """RAG Sage相談成功テスト"""
        request = {'task_id': 'test', 'type': 'consultation'}
        
        result = _consult_rag_sage(request)
        
        assert result['sage'] == 'rag'
        assert result['status'] == 'success'
        assert 'knowledge_search' in result
        assert 'relevance_score' in result

    @patch('requests.post')
    def test_send_slack_notification(self, mock_post):
        """Slack通知送信テスト"""
        mock_post.return_value = MagicMock()
        
        data = {
            'type': 'success',
            'message': 'テスト通知',
            'task_id': 'test_001'
        }
        
        _send_slack_notification('https://hooks.slack.com/test', data)
        
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert 'json' in kwargs
        assert 'text' in kwargs['json']


class TestCeleryAppConfiguration:
    """Celeryアプリケーション設定テスト"""

    def test_celery_app_config(self):
        """Celeryアプリケーション設定テスト"""
        assert app.main == 'elders_guild'
        assert 'redis://localhost:6379/0' in str(app.conf.broker_url)
        assert app.conf.task_serializer == 'json'
        assert app.conf.timezone == 'Asia/Tokyo'

    def test_task_routes_config(self):
        """タスクルーティング設定テスト"""
        routes = app.conf.task_routes
        
        assert 'workers.enhanced_task_worker_celery.claude_task' in routes
        assert 'workers.enhanced_task_worker_celery.notification_task' in routes
        assert 'workers.enhanced_task_worker_celery.sage_consultation' in routes

    def test_task_annotations_config(self):
        """タスクアノテーション設定テスト"""
        annotations = app.conf.task_annotations
        
        assert 'workers.enhanced_task_worker_celery.claude_task' in annotations
        assert 'workers.enhanced_task_worker_celery.sage_consultation' in annotations


if __name__ == '__main__':
    pytest.main([__file__, '-v'])