#!/usr/bin/env python3
"""
Elders Guild Slack Channel Notifier
チャンネル指定可能な拡張Slack通知システム
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
import requests
from datetime import datetime

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent

class SlackChannelNotifier:
    """チャンネル指定可能なSlack通知クラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 設定読み込み
        self._load_config()
        
    def _load_config(self):
        """設定ファイルから各種設定を読み込む"""
        config_file = PROJECT_ROOT / 'config' / 'slack.conf'
        
        # デフォルト値
        self.bot_token = None
        self.webhook_url = None
        self.default_channel = "#general"
        self.scaling_channel = "#ai-company-scaling"
        self.health_channel = "#ai-company-health"
        self.error_channel = "#ai-company-errors"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"')
                            
                            if key == 'SLACK_BOT_TOKEN':
                                self.bot_token = value
                            elif key == 'SLACK_WEBHOOK_URL':
                                self.webhook_url = value
                            elif key == 'SLACK_CHANNEL':
                                self.default_channel = value
                            elif key == 'SLACK_SCALING_CHANNEL':
                                self.scaling_channel = value
                            elif key == 'SLACK_HEALTH_CHANNEL':
                                self.health_channel = value
                            elif key == 'SLACK_ERROR_CHANNEL':
                                self.error_channel = value
            except Exception as e:
                self.logger.error(f"設定ファイル読み込みエラー: {e}")
        
        # 環境変数からも取得を試みる
        self.bot_token = os.environ.get('SLACK_BOT_TOKEN', self.bot_token)
        self.webhook_url = os.environ.get('SLACK_WEBHOOK_URL', self.webhook_url)
    
    def send_to_channel(self, channel: str, text: str, **kwargs) -> bool:
        """
        指定チャンネルにメッセージを送信（Bot API使用）
        
        Args:
            channel: 送信先チャンネル（例: #ai-company-scaling）
            text: メッセージテキスト
            **kwargs: 追加パラメータ（blocks等）
        
        Returns:
            bool: 送信成功時True
        """
        if not self.bot_token:
            self.logger.warning("Slack Bot Token未設定 - webhook経由で送信します")
            return self._send_via_webhook(text, **kwargs)
        
        headers = {
            'Authorization': f'Bearer {self.bot_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'channel': channel,
            'text': text,
            **kwargs
        }
        
        try:
            response = requests.post(
                'https://slack.com/api/chat.postMessage',
                headers=headers,
                json=payload,
                timeout=10
            )
            
            data = response.json()
            if data.get('ok'):
                self.logger.info(f"Slack通知送信成功: {channel}")
                return True
            else:
                self.logger.error(f"Slack通知失敗: {data.get('error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Slack API エラー: {str(e)}")
            return False
    
    def _send_via_webhook(self, text: str, **kwargs) -> bool:
        """Webhook経由でメッセージ送信（フォールバック）"""
        if not self.webhook_url:
            self.logger.error("Slack webhook URL未設定")
            return False
        
        payload = {
            'text': text,
            **kwargs
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"Webhook送信エラー: {str(e)}")
            return False
    
    def send_scaling_notification(self, action: str, current_workers: int, 
                                  target_workers: int, queue_length: int,
                                  task_id: Optional[str] = None) -> bool:
        """
        スケーリング通知を専用チャンネルに送信
        
        Args:
            action: スケーリングアクション（up/down）
            current_workers: 現在のワーカー数
            target_workers: 目標ワーカー数
            queue_length: キュー長
            task_id: タスクID
        """
        emoji = "📈" if action == "up" else "📉"
        action_text = "スケールアップ" if action == "up" else "スケールダウン"
        
        message = f"{emoji} **ワーカー自動スケーリング**\n"
        message += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += f"**アクション:** {action_text}\n"
        message += f"**ワーカー数:** {current_workers} → {target_workers}\n"
        message += f"**キュー長:** {queue_length}\n"
        message += f"**時刻:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if task_id:
            message += f"**タスクID:** `{task_id}`\n"
        
        message += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += f"*Elders Guild Auto Scaler*"
        
        return self.send_to_channel(self.scaling_channel, message)
    
    def send_health_notification(self, worker_id: str, action: str, 
                                 issues: list, success: bool = True) -> bool:
        """
        ヘルスチェック通知を専用チャンネルに送信
        
        Args:
            worker_id: ワーカーID
            action: 実行したアクション
            issues: 検出された問題リスト
            success: アクション成功フラグ
        """
        emoji = "✅" if success else "❌"
        status = "成功" if success else "失敗"
        
        message = f"🏥 **ワーカーヘルスチェック**\n"
        message += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += f"**ワーカー:** `{worker_id}`\n"
        message += f"**アクション:** {action}\n"
        message += f"**ステータス:** {emoji} {status}\n"
        
        if issues:
            message += f"**検出された問題:**\n"
            for issue in issues:
                message += f"  • {issue}\n"
        
        message += f"**時刻:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += f"*Elders Guild Health Monitor*"
        
        return self.send_to_channel(self.health_channel, message)
    
    def send_task_completion(self, task_id: str, worker: str, prompt: str, 
                            response: str, channel: Optional[str] = None) -> bool:
        """
        タスク完了通知（チャンネル指定可能）
        
        Args:
            task_id: タスクID
            worker: ワーカー名
            prompt: プロンプト
            response: 応答
            channel: 送信先チャンネル（省略時はデフォルト）
        """
        channel = channel or self.default_channel
        
        # プロンプトと応答のプレビュー
        prompt_preview = prompt[:300] + "..." if len(prompt) > 300 else prompt
        response_preview = response[:1000] + "..." if len(response) > 1000 else response
        
        message = f"✅ **Task Completed**\n"
        message += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += f"**ID:** `{task_id}`\n"
        message += f"**Worker:** `{worker}`\n"
        message += f"\n**Request:**\n`{prompt_preview}`\n"
        message += f"\n**Response:**\n{response_preview}\n"
        message += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += f"*Elders Guild System*"
        
        return self.send_to_channel(channel, message)


if __name__ == "__main__":
    # テスト実行
    print("Elders Guild Slack Channel Notifier Test")
    print("=" * 50)
    
    notifier = SlackChannelNotifier()
    
    print(f"Bot Token: {'設定済み' if notifier.bot_token else '未設定'}")
    print(f"Webhook URL: {'設定済み' if notifier.webhook_url else '未設定'}")
    print(f"Scaling Channel: {notifier.scaling_channel}")
    print(f"Health Channel: {notifier.health_channel}")
    
    # テスト通知
    print("\nテスト通知送信中...")
    
    # スケーリング通知テスト
    success = notifier.send_scaling_notification(
        action="up",
        current_workers=2,
        target_workers=3,
        queue_length=10,
        task_id="test_scaling_001"
    )
    
    print(f"スケーリング通知: {'成功' if success else '失敗'}")
