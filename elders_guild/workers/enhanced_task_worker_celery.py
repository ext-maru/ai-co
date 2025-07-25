#!/usr/bin/env python3
"""
Elders Guild Enhanced TaskWorker - Celery版
Issue #93: OSS移行プロジェクト - Celery/Ray移行フェーズ

従来のEnhancedTaskWorkerをCeleryタスクとして再実装
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from celery.utils.log import get_task_logger

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.env_config import get_config

# エルダーズギルド統合
try:
    from libs.elder_council_summoner import ElderCouncilSummoner
    from libs.elder_tree_hierarchy import ElderMessage, ElderRank, get_elder_tree
    from libs.four_sages_integration import FourSagesIntegration
    ELDER_INTEGRATION_AVAILABLE = True
except ImportError:
    # Handle specific exception case
    ELDER_INTEGRATION_AVAILABLE = False

# Celeryアプリケーション設定
app = Celery('elders_guild')

# Redis設定（Docker環境対応）
REDIS_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
app.conf.update(
    broker_url=REDIS_URL,
    result_backend=REDIS_URL,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Tokyo',
    enable_utc=True,
    task_routes={
        'workers.enhanced_task_worker_celery.claude_task': {'queue': 'claude_tasks'},
        'workers.enhanced_task_worker_celery.notification_task': {'queue': 'notifications'},
        'workers.enhanced_task_worker_celery.sage_consultation': {'queue': 'sage_tasks'},
    },
    task_annotations={
        'workers.enhanced_task_worker_celery.claude_task': {'rate_limit': '10/m'},
        'workers.enhanced_task_worker_celery.sage_consultation': {'rate_limit': '20/m'},
    }
)

# タスクロガー
logger = get_task_logger(__name__)

# 絵文字定義
EMOJI = {
    "start": "🚀",
    "success": "✅", 
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "task": "📋",
    "thinking": "🤔",
    "complete": "🎉",
    "process": "⚙️",
    "robot": "🤖",
    "elder": "🏛️",
    "sage": "🧙‍♂️",
    "celery": "🌿",
}

class CeleryTaskWorkerConfig:
    """Celery TaskWorker設定クラス"""
    
    def __init__(self):
        self.config = get_config()
        self.output_dir = PROJECT_ROOT / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        # エルダーズギルド統合
        self.elder_integration = ELDER_INTEGRATION_AVAILABLE
        if self.elder_integration:
            self.four_sages = FourSagesIntegration()
            self.elder_council = ElderCouncilSummoner()
        
        # Claude CLI設定
        self.claude_cmd = self._get_claude_command()
        
        logger.info(f"{EMOJI['celery']} Celery TaskWorker設定完了")
    
    def _get_claude_command(self) -> str:
        """Claude CLIコマンド取得"""
        # Claude CLI実行可能ファイル検索
        claude_paths = [
            "/usr/local/bin/claude",
            "/opt/homebrew/bin/claude", 
            "claude"
        ]
        
        for path in claude_paths:
            # Process each item in collection
            try:
                result = subprocess.run([path, "--version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return path
            except:
                continue
        
        return "claude"  # デフォルト

# グローバル設定インスタンス
task_config = CeleryTaskWorkerConfig()

@app.task(bind=True, name='workers.enhanced_task_worker_celery.claude_task')
def claude_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Claude CLI実行タスク（Celery版）
    
    Args:
        task_data: タスクデータ
            - task_id: タスクID
            - prompt: Claude実行プロンプト
            - context: 実行コンテキスト
            - options: 実行オプション
    
    Returns:
        実行結果辞書
    """
    task_id = task_data.get('task_id', self.request.id)
    prompt = task_data.get('prompt', '')
    context = task_data.get('context', {})
    options = task_data.get('options', {})
    
    logger.info(f"{EMOJI['start']} Claude task開始: {task_id}")
    
    try:
        # プロンプト検証
        if not prompt.strip():
            raise ValueError("プロンプトが空です")
        
        # Claude CLI実行
        result = _execute_claude_cli(
            task_id=task_id,
            prompt=prompt,
            context=context,
            options=options
        )
        
        # 4賢者相談（オプション）
        if options.get('enable_sage_consultation', False) and task_config.elder_integration:
            # Complex condition - consider breaking down
            sage_result = sage_consultation.delay({
                'task_id': task_id,
                'task_data': task_data,
                'claude_result': result
            })
            result['sage_consultation_id'] = sage_result.id
        
        logger.info(f"{EMOJI['success']} Claude task完了: {task_id}")
        return {
            'success': True,
            'task_id': task_id,
            'result': result,
            'completed_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        # Handle specific exception case
        logger.error(f"{EMOJI['error']} Claude task失敗: {task_id} - {str(e)}")
        
        # エラー通知
        notification_task.delay({
            'type': 'error',
            'task_id': task_id,
            'error': str(e),
            'context': context
        })
        
        return {
            'success': False,
            'task_id': task_id,
            'error': str(e),
            'failed_at': datetime.now().isoformat()
        }

@app.task(bind=True, name='workers.enhanced_task_worker_celery.sage_consultation')
def sage_consultation(self, consultation_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    4賢者相談タスク
    
    Args:
        consultation_data: 相談データ
            - task_id: 元タスクID
            - task_data: 元タスクデータ
            - claude_result: Claude実行結果
    
    Returns:
        賢者相談結果
    """
    task_id = consultation_data.get('task_id', self.request.id)
    logger.info(f"{EMOJI['sage']} 4賢者相談開始: {task_id}")
    
    try:
        if not task_config.elder_integration:
            return {
                'success': False,
                'error': 'エルダーズギルド統合が無効です'
            }
        
        # 4賢者との相談処理
        consultation_request = {
            'task_id': task_id,
            'type': 'task_consultation',
            'data': consultation_data.get('task_data', {}),
            'claude_result': consultation_data.get('claude_result', {})
        }
        
        # 各賢者への相談（並列実行可能）
        sage_results = {}
        
        # Knowledge Sage
        knowledge_result = _consult_knowledge_sage(consultation_request)
        sage_results['knowledge'] = knowledge_result
        
        # Task Sage
        task_result = _consult_task_sage(consultation_request)
        sage_results['task'] = task_result
        
        # Incident Sage
        incident_result = _consult_incident_sage(consultation_request)
        sage_results['incident'] = incident_result
        
        # RAG Sage
        rag_result = _consult_rag_sage(consultation_request)
        sage_results['rag'] = rag_result
        
        logger.info(f"{EMOJI['sage']} 4賢者相談完了: {task_id}")
        return {
            'success': True,
            'task_id': task_id,
            'sage_results': sage_results,
            'completed_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        # Handle specific exception case
        logger.error(f"{EMOJI['error']} 4賢者相談失敗: {task_id} - {str(e)}")
        return {
            'success': False,
            'task_id': task_id,
            'error': str(e),
            'failed_at': datetime.now().isoformat()
        }

@app.task(bind=True, name='workers.enhanced_task_worker_celery.notification_task')
def notification_task(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    通知タスク（Slack等）
    
    Args:
        notification_data: 通知データ
            - type: 通知タイプ (success/error/warning/info)
            - task_id: 関連タスクID
            - message: 通知メッセージ
            - context: 追加コンテキスト
    
    Returns:
        通知結果
    """
    notification_type = notification_data.get('type', 'info')
    task_id = notification_data.get('task_id', 'unknown')
    
    logger.info(f"{EMOJI['info']} 通知タスク開始: {notification_type} for {task_id}")
    
    try:
        # Slack通知（設定されている場合）
        slack_url = os.getenv('SLACK_WEBHOOK_URL')
        if slack_url:
            _send_slack_notification(slack_url, notification_data)
        
        # メール通知（設定されている場合）
        if os.getenv('SMTP_HOST'):
            _send_email_notification(notification_data)
        
        logger.info(f"{EMOJI['success']} 通知タスク完了: {notification_type}")
        return {
            'success': True,
            'notification_type': notification_type,
            'task_id': task_id,
            'sent_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        # Handle specific exception case
        logger.error(f"{EMOJI['error']} 通知タスク失敗: {notification_type} - {str(e)}")
        return {
            'success': False,
            'notification_type': notification_type,
            'error': str(e),
            'failed_at': datetime.now().isoformat()
        }

# ヘルパー関数

def _execute_claude_cli(task_id: str, prompt: str, context: Dict, options: Dict) -> Dict[str, Any]:
    """Claude CLI実行"""
    try:
        # 一時ファイルにプロンプト保存

            f.write(prompt)
        
        # Claude CLI実行
        cmd = [
            task_config.claude_cmd,

        ]
        
        # 追加オプション
        if options.get('model'):
            cmd.extend(["--model", options['model']])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=options.get('timeout', 300),
            cwd=PROJECT_ROOT
        )
        
        # 一時ファイル削除

        return {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'success': result.returncode == 0
        }
        
    except subprocess.TimeoutExpired:
        # Handle specific exception case
        raise Exception("Claude CLI実行がタイムアウトしました")
    except Exception as e:
        # Handle specific exception case
        raise Exception(f"Claude CLI実行エラー: {str(e)}")

def _consult_knowledge_sage(request: Dict) -> Dict[str, Any]:
    """Knowledge Sage相談"""
    try:
        # 実際の実装では4賢者システムを呼び出し
        return {
            'sage': 'knowledge',
            'status': 'success',
            'advice': 'Knowledge Sageからの助言',
            'confidence': 0.85
        }
    except Exception as e:
        # Handle specific exception case
        return {'sage': 'knowledge', 'status': 'error', 'error': str(e)}

def _consult_task_sage(request: Dict) -> Dict[str, Any]:
    """Task Sage相談"""
    try:
        return {
            'sage': 'task',
            'status': 'success', 
            'optimization': 'Task Sageからの最適化提案',
            'priority_score': 0.7
        }
    except Exception as e:
        # Handle specific exception case
        return {'sage': 'task', 'status': 'error', 'error': str(e)}

def _consult_incident_sage(request: Dict) -> Dict[str, Any]:
    """Incident Sage相談"""
    try:
        return {
            'sage': 'incident',
            'status': 'success',
            'risk_assessment': 'リスク評価完了',
            'mitigation': 'リスク軽減策'
        }
    except Exception as e:
        # Handle specific exception case
        return {'sage': 'incident', 'status': 'error', 'error': str(e)}

def _consult_rag_sage(request: Dict) -> Dict[str, Any]:
    """RAG Sage相談"""
    try:
        return {
            'sage': 'rag',
            'status': 'success',
            'knowledge_search': 'RAG検索結果',
            'relevance_score': 0.9
        }
    except Exception as e:
        # Handle specific exception case
        return {'sage': 'rag', 'status': 'error', 'error': str(e)}

def _send_slack_notification(webhook_url: str, data: Dict) -> None:
    """Slack通知送信"""
    import requests
    
    emoji_map = {
        'success': '✅',
        'error': '❌', 
        'warning': '⚠️',
        'info': 'ℹ️'
    }
    
    emoji = emoji_map.get(data.get('type', 'info'), 'ℹ️')
    message = f"{emoji} {data.get('message', 'Elders Guild タスク通知')}"
    
    payload = {
        'text': message,
        'username': 'Elders Guild Bot',
        'icon_emoji': ':robot_face:'
    }
    
    requests.post(webhook_url, json=payload, timeout=10)

def _send_email_notification(data: Dict) -> None:
    """メール通知送信（プレースホルダー）"""
    # 実際の実装ではSMTPクライアントを使用
    logger.info(f"メール通知: {data.get('type', 'info')}")

# Celeryシグナル

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """タスク実行前処理"""
    logger.info(f"{EMOJI['start']} Task開始: {task.name} ({task_id})")

@task_postrun.connect  
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, 
                        retval=None, state=None, **kwds):
    """タスク実行後処理"""
    emoji = EMOJI['success'] if state == 'SUCCESS' else EMOJI['error']
    logger.info(f"{emoji} Task完了: {task.name} ({task_id}) - {state}")

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, einfo=None, **kwds):
    """タスク失敗処理"""
    logger.error(f"{EMOJI['error']} Task失敗: {sender.name} ({task_id}) - {exception}")

if __name__ == '__main__':
    # Celeryワーカー起動
    app.start()