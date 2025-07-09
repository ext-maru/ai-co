#!/usr/bin/env python3
"""
AI Company Slack Notifier v5.0
高機能なSlack通知システム
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import requests
from datetime import datetime
import os

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent

class SlackNotifier:
    """Slack通知を管理するクラス"""
    
    def __init__(self, webhook_url: Optional[str] = None, bot_token: Optional[str] = None):
        """
        初期化
        
        Args:
            webhook_url: SlackのWebhook URL（省略時は設定ファイルから読み込み）
            bot_token: Slack Bot Token（Web API用）
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Webhook URLの取得
        if webhook_url:
            self.webhook_url = webhook_url
        else:
            self.webhook_url = self._load_webhook_url()
        
        # Bot Tokenの取得（Web API用）
        if bot_token:
            self.bot_token = bot_token
        else:
            self.bot_token = self._load_bot_token()
        
        # 送信履歴（デバッグ用）
        self.send_history: List[Dict[str, Any]] = []
        
    def _load_webhook_url(self) -> Optional[str]:
        """設定ファイルからWebhook URLを読み込む"""
        # 環境変数から取得を試みる
        webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
        if webhook_url:
            return webhook_url
        
        # 設定ファイルから取得を試みる
        config_file = PROJECT_ROOT / 'config' / 'slack.conf'
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    for line in f:
                        if line.startswith('WEBHOOK_URL='):
                            return line.split('=', 1)[1].strip()
            except Exception as e:
                self.logger.error(f"Failed to read config file: {e}")
        
        # Core設定から取得を試みる
        try:
            from core import get_config
            config = get_config()
            return config.get('slack.webhook_url')
        except:
            pass
        
        self.logger.warning("No Slack webhook URL configured")
        return None
    
    def _load_bot_token(self) -> Optional[str]:
        """設定ファイルからBot Tokenを読み込む"""
        # 環境変数から取得を試みる
        bot_token = os.environ.get('SLACK_BOT_TOKEN')
        if bot_token:
            return bot_token
        
        # 設定ファイルから取得を試みる
        config_file = PROJECT_ROOT / 'config' / 'slack.conf'
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    for line in f:
                        if line.startswith('BOT_TOKEN='):
                            return line.split('=', 1)[1].strip()
            except Exception as e:
                self.logger.error(f"Failed to read config file: {e}")
        
        # Core設定から取得を試みる
        try:
            from core import get_config
            config = get_config()
            return config.get('slack.bot_token')
        except:
            pass
        
        self.logger.debug("No Slack bot token configured")
        return None
    
    def send_message(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Slackにメッセージを送信
        
        Args:
            text: 送信するメッセージ
            **kwargs: 追加のSlackメッセージパラメータ
        
        Returns:
            dict: 送信結果（ts、channel等を含む）
        """
        if not self.webhook_url and not self.bot_token:
            self.logger.warning("Slack webhook URL not configured, skipping notification")
            return {}
        
        # Web APIを優先（スレッド機能のため）
        if self.bot_token:
            return self._send_via_api(text, **kwargs)
        
        # Webhook経由での送信
        payload = {
            'text': text,
            **kwargs
        }
        
        # 送信履歴に記録
        self.send_history.append({
            'timestamp': datetime.now().isoformat(),
            'text': text[:100] + '...' if len(text) > 100 else text,
            'success': None
        })
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            success = response.status_code == 200
            self.send_history[-1]['success'] = success
            
            if success:
                self.logger.debug(f"Slack notification sent successfully")
                return {'ok': True}
            else:
                self.logger.error(f"Slack notification failed: {response.status_code} - {response.text}")
                return {}
            
        except requests.exceptions.Timeout:
            self.logger.error("Slack notification timeout")
            self.send_history[-1]['success'] = False
            return {}
        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {str(e)}")
            self.send_history[-1]['success'] = False
            return {}
    
    def _send_via_api(self, text: str, **kwargs) -> Dict[str, Any]:
        """Slack Web APIを使用してメッセージを送信"""
        # チャンネルの取得
        channel = kwargs.get('channel')
        if not channel:
            # デフォルトチャンネルを使用
            try:
                from core import get_config
                config = get_config()
                channel = config.get('slack.channel', 'general')
            except:
                channel = os.environ.get('SLACK_CHANNEL', 'general')
        
        # API パラメータ
        api_params = {
            'channel': channel,
            'text': text,
            'mrkdwn': True
        }
        
        # その他のパラメータを追加
        for key in ['thread_ts', 'blocks', 'attachments']:
            if key in kwargs:
                api_params[key] = kwargs[key]
        
        headers = {
            'Authorization': f'Bearer {self.bot_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                'https://slack.com/api/chat.postMessage',
                headers=headers,
                json=api_params,
                timeout=10
            )
            
            result = response.json()
            if result.get('ok'):
                self.logger.debug(f"Slack API message sent successfully")
                return result
            else:
                self.logger.error(f"Slack API error: {result.get('error')}")
                return {}
        
        except Exception as e:
            self.logger.error(f"Failed to send via Slack API: {str(e)}")
            return {}
    
    def send_thread_message(self, channel: str, thread_ts: str, message: str, **kwargs) -> Dict[str, Any]:
        """
        スレッドにメッセージを送信
        
        Args:
            channel: チャンネルID
            thread_ts: スレッドのタイムスタンプ
            message: 送信するメッセージ
            **kwargs: 追加パラメータ
        
        Returns:
            dict: 送信結果
        """
        if not self.bot_token:
            self.logger.warning("Bot token not configured, cannot send thread message")
            return {}
        
        return self._send_via_api(
            text=message,
            channel=channel,
            thread_ts=thread_ts,
            **kwargs
        )
    
    def send_blocks(self, blocks: List[Dict[str, Any]], text: str = "AI Company Notification") -> Dict[str, Any]:
        """
        Slack Block Kitを使用してリッチなメッセージを送信
        
        Args:
            blocks: Slack blocks
            text: フォールバックテキスト
        
        Returns:
            dict: 送信結果
        """
        return self.send_message(text, blocks=blocks)
    
    def send_error_notification(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        エラー通知を送信
        
        Args:
            error: 発生したエラー
            context: エラーコンテキスト情報
        
        Returns:
            bool: 送信成功時True
        """
        error_type = error.__class__.__name__
        error_msg = str(error)
        
        # メッセージ構築
        message_parts = [
            f"🚨 **Error Alert: {error_type}**",
            f"",
            f"**Message:** `{error_msg}`",
        ]
        
        if context:
            message_parts.extend([
                f"",
                f"**Context:**"
            ])
            for key, value in context.items():
                message_parts.append(f"• {key}: `{value}`")
        
        message_parts.extend([
            f"",
            f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ])
        
        result = self.send_message("\n".join(message_parts))
        return bool(result)
    
    def send_success_notification(self, title: str, details: Optional[Dict[str, Any]] = None) -> bool:
        """
        成功通知を送信
        
        Args:
            title: 通知タイトル
            details: 詳細情報
        
        Returns:
            bool: 送信成功時True
        """
        message_parts = [
            f"✅ **{title}**",
            f""
        ]
        
        if details:
            for key, value in details.items():
                # キーを人間が読みやすい形式に変換
                display_key = key.replace('_', ' ').title()
                message_parts.append(f"• {display_key}: `{value}`")
        
        message_parts.append(f"\n**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        result = self.send_message("\n".join(message_parts))
        return bool(result)
    
    def send_progress_notification(self, task_id: str, progress: int, message: str = "") -> bool:
        """
        進捗通知を送信
        
        Args:
            task_id: タスクID
            progress: 進捗率（0-100）
            message: 追加メッセージ
        
        Returns:
            bool: 送信成功時True
        """
        # プログレスバーの生成
        bar_length = 20
        filled = int(bar_length * progress / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        notification = f"⏳ **Task Progress: {task_id}**\n"
        notification += f"[{bar}] {progress}%"
        
        if message:
            notification += f"\n{message}"
        
        result = self.send_message(notification)
        return bool(result)
    
    def send_batch_notification(self, notifications: List[str], title: str = "Batch Notification") -> bool:
        """
        複数の通知をまとめて送信
        
        Args:
            notifications: 通知メッセージのリスト
            title: バッチ通知のタイトル
        
        Returns:
            bool: 送信成功時True
        """
        if not notifications:
            return False
        
        message = f"📦 **{title}** ({len(notifications)} items)\n\n"
        
        for i, notification in enumerate(notifications[:10]):  # 最大10件
            message += f"{i+1}. {notification}\n"
        
        if len(notifications) > 10:
            message += f"\n... and {len(notifications) - 10} more items"
        
        result = self.send_message(message)
        return bool(result)
    
    def get_send_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        送信履歴を取得
        
        Args:
            limit: 取得する履歴の最大数
        
        Returns:
            送信履歴のリスト
        """
        return self.send_history[-limit:]
    
    def test_connection(self) -> bool:
        """
        Slack接続をテスト
        
        Returns:
            bool: 接続成功時True
        """
        result = self.send_message("🔗 AI Company Slack connection test - OK")
        return bool(result)

    def send_success(self, message: str, details: Optional[Dict[str, Any]] = None) -> bool:
        """成功通知を送信（テスト用エイリアス）"""
        return self.send_success_notification(message, details)

    def send_error(self, message: str, error: str = None, context: Optional[Dict[str, Any]] = None) -> bool:
        """エラー通知を送信（テスト用エイリアス）"""
        if error:
            error_obj = Exception(error)
        else:
            error_obj = Exception(message)
        return self.send_error_notification(error_obj, context)
    
    def send_task_completion_simple(self, task_id: str, worker: str, prompt: str, 
                                   response: str, status: str = "completed",
                                   task_type: str = "general", rag_applied: bool = False) -> bool:
        """
        タスク完了のシンプルな通知を送信（プロフェッショナル版）
        
        Args:
            task_id: タスクID
            worker: ワーカーID
            prompt: 元のプロンプト
            response: 応答内容
            status: ステータス
            task_type: タスクタイプ
            rag_applied: RAG適用フラグ
        
        Returns:
            bool: 送信成功時True
        """
        # プロンプトと応答のプレビュー（長さ制限）
        prompt_preview = prompt[:500] + "..." if len(prompt) > 500 else prompt
        response_preview = response[:1500] + "..." if len(response) > 1500 else response
        
        # RAG適用情報（脳みそ絵文字なし）
        rag_info = "RAG: Applied" if rag_applied else "RAG: Not Applied"
        
        # メッセージ構築（プロフェッショナル）
        message_parts = [
            f"✅ **Task Completed**",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"**ID:** `{task_id}`",
            f"**Worker:** `{worker}`",
            f"**Type:** `{task_type}`",
            f"**Status:** `{rag_info}`",
            f"",
            f"**Request:**",
            f"`{prompt_preview}`",
            f"",
            f"**Response:**",
            f"{response_preview}",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"*AI Company System*"
        ]
        
        result = self.send_message("\n".join(message_parts))
        return bool(result)


# ユーティリティ関数
def format_duration(seconds: float) -> str:
    """
    秒数を人間が読みやすい形式に変換
    
    Args:
        seconds: 秒数
    
    Returns:
        フォーマットされた文字列
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def format_file_size(bytes: int) -> str:
    """
    バイト数を人間が読みやすい形式に変換
    
    Args:
        bytes: バイト数
    
    Returns:
        フォーマットされた文字列
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f}{unit}"
        bytes /= 1024.0
    return f"{bytes:.1f}TB"


if __name__ == "__main__":
    # テスト実行
    import sys
    
    print("AI Company Slack Notifier v5.0 Test")
    print("=" * 50)
    
    notifier = SlackNotifier()
    
    if not notifier.webhook_url:
        print("❌ Slack webhook URL not configured")
        print("\nTo configure:")
        print("1. Set SLACK_WEBHOOK_URL environment variable")
        print("2. Or add to config/slack.conf: WEBHOOK_URL=https://hooks.slack.com/...")
        sys.exit(1)
    
    print("✅ Webhook URL configured")
    print("\nTesting connection...")
    
    if notifier.test_connection():
        print("✅ Connection test successful")
        
        # 各種通知のテスト
        print("\nSending test notifications...")
        
        # 成功通知
        notifier.send_success_notification(
            "Test Task Completed",
            {
                "task_id": "test_123",
                "duration": "2.34s",
                "files_created": 3
            }
        )
        
        # エラー通知
        try:
            raise ValueError("This is a test error")
        except Exception as e:
            notifier.send_error_notification(e, {"task_id": "test_123"})
        
        # 進捗通知
        notifier.send_progress_notification("test_123", 75, "Processing files...")
        
        print("\n✅ All test notifications sent")
        
        # 送信履歴表示
        print("\nSend History:")
        for item in notifier.get_send_history():
            status = "✅" if item['success'] else "❌"
            print(f"{status} {item['timestamp']}: {item['text']}")
    else:
        print("❌ Connection test failed")
