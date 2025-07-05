#!/usr/bin/env python3
"""
Slack通知機能（修正版）
- HTTPレスポンスの詳細なログ記録
- 具体的なエラーハンドリング
- レスポンスボディのチェック
"""

import json
import requests
import logging
from typing import Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class SlackNotifier:
    """Slack通知を送信するクラス"""
    
    def __init__(self, config_file=None):
        if config_file is None:
            config_file = Path(__file__).parent.parent / "config" / "slack.conf"
        
        self.config = self._load_config(config_file)
        self.enabled = self.config.get('ENABLE_SLACK', 'false').lower() == 'true'
        self.webhook_url = self.config.get('SLACK_WEBHOOK_URL')
        
    def _load_config(self, config_file):
        """設定ファイル読み込み"""
        config = {}
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip().strip('"')
        except Exception as e:
            logger.error(f"Slack設定読み込み失敗: {e}")
        
        return config
    
    def send_message(self, message: str) -> bool:
        """Slackにメッセージを送信"""
        if not self.enabled:
            logger.info("Slack通知が無効化されています")
            return False
            
        if not self.webhook_url:
            logger.error("Slack Webhook URLが設定されていません")
            return False
            
        try:
            # メッセージをJSON形式で準備
            payload = {
                'text': message,
                'username': self.config.get('SLACK_USERNAME', 'AI-Company-Bot'),
                'icon_emoji': self.config.get('SLACK_ICON', ':robot_face:'),
                'channel': self.config.get('SLACK_CHANNEL', '#general')
            }
            
            # HTTPリクエストを送信
            logger.info(f"Slack送信開始: {message[:50]}...")
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            # レスポンスの確認
            if response.status_code == 200:
                logger.info(f"Slack送信成功: status={response.status_code}, response={response.text}")
                return True
            else:
                logger.error(
                    f"Slack送信失敗: status={response.status_code}, "
                    f"response={response.text}, url={self.webhook_url[:30]}..."
                )
                return False
                
        except requests.exceptions.Timeout:
            logger.error("Slack送信タイムアウト")
            return False
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Slack接続エラー: {e}")
            return False
        except Exception as e:
            logger.error(f"Slack送信中の予期しないエラー: {type(e).__name__}: {e}")
            return False
    
    def send_formatted_task_result(self, task_result: dict) -> bool:
        """タスク結果を整形して送信"""
        if not self.enabled:
            return False
            
        try:
            status = task_result.get('status', 'unknown')
            task_id = task_result.get('task_id', 'N/A')
            exec_time = task_result.get('execution_time', 0)
            
            # ステータスに応じた絵文字
            emoji_map = {
                'completed': '✅',
                'success': '✅',
                'failed': '❌',
                'error': '❌',
                'timeout': '⏰',
                'pending': '⏳'
            }
            emoji = emoji_map.get(status, '❓')
            
            # メッセージの構築
            message = f"{emoji} *タスク完了通知*\n"
            message += f"• ID: `{task_id}`\n"
            message += f"• ステータス: {status}\n"
            message += f"• 実行時間: {exec_time:.2f}秒\n"
            
            # エラーがある場合は追加
            if task_result.get('error'):
                error_msg = str(task_result['error'])[:100]
                message += f"• エラー: {error_msg}\n"
            
            # 結果の概要がある場合は追加
            if task_result.get('summary'):
                summary = str(task_result['summary'])[:200]
                message += f"• 結果: {summary}\n"
            
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"タスク結果の整形エラー: {e}")
            return False
    
    def send_task_completion_simple(self, task_id, worker, prompt, response, 
                                  status="completed", task_type="general", rag_applied=False):
        """シンプル版タスク完了通知（既存の互換性維持）"""
        if not self.enabled:
            return False
        
        status_emoji = "✅" if status == "completed" else "❌"
        rag_emoji = "🧠" if rag_applied else "🔧"
        
        # 超シンプルなテキスト形式
        message_text = f"""{status_emoji} {rag_emoji} *AI Company タスク完了*

*ID:* {task_id}
*ワーカー:* {worker}
*RAG:* {'適用済み' if rag_applied else '未適用'}

*プロンプト:*
{prompt[:80]}{'...' if len(prompt) > 80 else ''}

*応答:*
{response[:120]}{'...' if len(response) > 120 else ''}

_AI Company RAG System_"""
        
        return self.send_message(message_text)
    
    def test_notification(self):
        """テスト通知"""
        test_message = f"🎉 *AI Company Slack通知テスト成功！*\n\n修正版 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        success = self.send_message(test_message)
        return "✅ テスト通知送信成功" if success else "❌ テスト通知送信失敗"