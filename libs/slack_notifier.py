#!/usr/bin/env python3
"""
Slack通知機能
"""

import requests
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class SlackNotifier:
    def __init__(self, config_file=None):
        if config_file is None:
            config_file = Path(__file__).parent.parent / "config" / "slack.conf"
        
        self.config = self._load_config(config_file)
        self.enabled = self.config.get('ENABLE_SLACK', 'false').lower() == 'true'
        
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
    
    def send_task_completion(self, task_id, worker, prompt, response, 
                           status="completed", task_type="general", rag_applied=False):
        """タスク完了通知"""
        if not self.enabled:
            return False
        
        status_emoji = "✅" if status == "completed" else "❌"
        rag_emoji = "🧠" if rag_applied else ""
        
        response_preview = response[:200] + "..." if len(response) > 200 else response
        
        message = {
            "channel": self.config.get('SLACK_CHANNEL', '#general'),
            "username": self.config.get('SLACK_USERNAME', 'AI-Company-Bot'),
            "icon_emoji": self.config.get('SLACK_ICON', ':robot_face:'),
            "attachments": [
                {
                    "color": "good" if status == "completed" else "danger",
                    "title": f"{status_emoji} {rag_emoji} AI Company タスク完了",
                    "fields": [
                        {
                            "title": "タスクID",
                            "value": task_id,
                            "short": True
                        },
                        {
                            "title": "ワーカー", 
                            "value": worker,
                            "short": True
                        },
                        {
                            "title": "RAG学習",
                            "value": "適用済み" if rag_applied else "未適用",
                            "short": True
                        },
                        {
                            "title": "プロンプト",
                            "value": f"```{prompt[:100]}...```" if len(prompt) > 100 else f"```{prompt}```",
                            "short": False
                        },
                        {
                            "title": "応答",
                            "value": f"```{response_preview}```",
                            "short": False
                        }
                    ],
                    "footer": "AI Company RAG System",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
        
        return self._send_message(message)
    
    def _send_message(self, message):
        """Slackメッセージ送信"""
        webhook_url = self.config.get('SLACK_WEBHOOK_URL')
        if not webhook_url:
            logger.warning("Slack Webhook URL未設定")
            return False
        
        try:
            response = requests.post(
                webhook_url,
                data=json.dumps(message),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Slack通知送信成功")
                return True
            else:
                logger.error(f"Slack通知送信失敗: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Slack通知例外: {e}")
            return False
    
    def test_notification(self):
        """テスト通知"""
        message = {
            "channel": self.config.get('SLACK_CHANNEL', '#general'),
            "username": self.config.get('SLACK_USERNAME', 'AI-Company-Bot'),
            "icon_emoji": ":white_check_mark:",
            "text": f"🎉 AI Company Slack通知テスト成功！ ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
        }
        
        success = self._send_message(message)
        return "✅ テスト通知送信成功" if success else "❌ テスト通知送信失敗"
