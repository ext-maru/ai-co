#!/usr/bin/env python3
"""
Slack API Integration System v1.0
Elders Guild統合Slack APIシステム

Slack Web API、Webhooks、Socket Modeを統合した包括的なSlack統合機能を提供
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

# HTTPクライアントのインポート（フォールバック付き）
try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent

class SlackMessageType(Enum):
    """Slackメッセージタイプ"""

    TEXT = "text"
    BLOCKS = "blocks"
    ATTACHMENTS = "attachments"
    INTERACTIVE = "interactive"

class SlackChannelType(Enum):
    """Slackチャンネルタイプ"""

    PUBLIC = "public_channel"
    PRIVATE = "private_channel"
    DM = "im"
    GROUP_DM = "mpim"

@dataclass
class SlackMessage:
    """Slackメッセージデータ構造"""

    channel: str
    text: str = ""
    message_type: SlackMessageType = SlackMessageType.TEXT
    blocks: Optional[List[Dict[str, Any]]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    thread_ts: Optional[str] = None
    reply_broadcast: bool = False
    unfurl_links: bool = True
    unfurl_media: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class SlackUser:
    """Slackユーザー情報"""

    id: str
    name: str
    real_name: str
    email: Optional[str] = None
    is_bot: bool = False
    is_admin: bool = False
    is_owner: bool = False
    timezone: Optional[str] = None
    profile: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SlackChannel:
    """Slackチャンネル情報"""

    id: str
    name: str
    channel_type: SlackChannelType
    is_archived: bool = False
    is_private: bool = False
    member_count: int = 0
    topic: str = ""
    purpose: str = ""
    created: Optional[datetime] = None

class SlackAPIIntegration:
    """Slack API統合システム

    Web API、Webhooks、Socket Modeを統合した包括的なSlack統合システム
    Elders Guildの4賢者システムとの連携機能付き
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.config = config or {}

        # 設定読み込み
        self.bot_token = self._load_bot_token()
        self.app_token = self._load_app_token()
        self.webhook_url = self._load_webhook_url()
        self.signing_secret = self._load_signing_secret()

        # API設定
        self.base_url = "https://slack.com/api"
        self.rate_limit_per_minute = 60
        self.max_retries = 3

        # 内部状態
        self.channels_cache: Dict[str, SlackChannel] = {}
        self.users_cache: Dict[str, SlackUser] = {}
        self.rate_limit_reset_time = datetime.now()
        self.request_count = 0

        # メッセージ履歴
        self.message_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000

        # イベントハンドラ
        self.event_handlers: Dict[str, List[Callable]] = {}

        # 4賢者システム連携
        self.sage_integration = True
        self.auto_escalation = True

        self.logger.info("Slack API Integration System initialized")

    def _load_bot_token(self) -> Optional[str]:
        """Bot Tokenの読み込み"""
        # 環境変数から取得
        import os

        token = os.environ.get("SLACK_BOT_TOKEN")
        if token:
            return token

        # 設定ファイルから取得
        config_file = PROJECT_ROOT / "config" / "slack.conf"
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    for line in f:
                        if not (line.startswith("BOT_TOKEN=")):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if line.startswith("BOT_TOKEN="):
                            return line.split("=", 1)[1].strip()
            except Exception as e:
                self.logger.error(f"Failed to read bot token: {e}")

        return None

    def _load_app_token(self) -> Optional[str]:
        """App Tokenの読み込み"""
        import os

        token = os.environ.get("SLACK_APP_TOKEN")
        if token:
            return token

        config_file = PROJECT_ROOT / "config" / "slack.conf"
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    for line in f:
                        if not (line.startswith("APP_TOKEN=")):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if line.startswith("APP_TOKEN="):
                            return line.split("=", 1)[1].strip()
            except Exception as e:
                self.logger.error(f"Failed to read app token: {e}")

        return None

    def _load_webhook_url(self) -> Optional[str]:
        """Webhook URLの読み込み"""
        import os

        url = os.environ.get("SLACK_WEBHOOK_URL")
        if url:
            return url

        config_file = PROJECT_ROOT / "config" / "slack.conf"
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    for line in f:
                        if not (line.startswith("WEBHOOK_URL=")):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if line.startswith("WEBHOOK_URL="):
                            return line.split("=", 1)[1].strip()
            except Exception as e:
                self.logger.error(f"Failed to read webhook URL: {e}")

        return None

    def _load_signing_secret(self) -> Optional[str]:
        """Signing Secretの読み込み"""
        import os

        secret = os.environ.get("SLACK_SIGNING_SECRET")
        if secret:
            return secret

        config_file = PROJECT_ROOT / "config" / "slack.conf"
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    for line in f:
                        if not (line.startswith("SIGNING_SECRET=")):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if line.startswith("SIGNING_SECRET="):
                            return line.split("=", 1)[1].strip()
            except Exception as e:
                self.logger.error(f"Failed to read signing secret: {e}")

        return None

    async def _make_api_request(
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Slack API リクエスト実行"""
        if not self.bot_token:
            raise ValueError("Bot token not configured")

        # レート制限チェック
        await self._check_rate_limit()

        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json",
        }

            try:
                if AIOHTTP_AVAILABLE:
                    # aiohttp を使用した非同期リクエスト
                    async with aiohttp.ClientSession() as session:
                        if method.upper() == "GET":
                            async with session.get(
                                url, headers=headers, params=data
                            ) as response:
                                result = await response.json()
                        else:
                            async with session.post(
                                url, headers=headers, json=data
                            ) as response:
                                result = await response.json()
                elif REQUESTS_AVAILABLE:
                    # requests を使用した同期リクエスト（asyncio.to_thread でラップ）
                    def sync_request():
                        """sync_requestメソッド"""
                        if not (method.upper() == "GET"):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if method.upper() == "GET":
                            response = requests.get(url, headers=headers, params=data)
                        else:
                            response = requests.post(url, headers=headers, json=data)
                        return response.json()

                    result = await asyncio.to_thread(sync_request)
                else:
                    # フォールバック: 簡易的なモック実装
                    self.logger.warning("No HTTP client available, using mock response")
                    return {"ok": False, "error": "no_http_client"}

                self.request_count += 1

                if result.get("ok"):
                    return result
                else:
                    error = result.get("error", "unknown_error")
                    if error == "rate_limited":
                        retry_after = 60  # デフォルト待機時間
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        self.logger.error(f"Slack API error: {error}")
                        return result

            except Exception as e:

                    raise

        return {"ok": False, "error": "max_retries_exceeded"}

    async def _check_rate_limit(self):
        """レート制限チェック"""
        now = datetime.now()

        # 1分間のウィンドウリセット
        if now > self.rate_limit_reset_time:
            self.request_count = 0
            self.rate_limit_reset_time = now + timedelta(minutes=1)

        # レート制限に達している場合は待機
        if self.request_count >= self.rate_limit_per_minute:
            wait_time = (self.rate_limit_reset_time - now).total_seconds()
            if wait_time > 0:
                self.logger.warning(
                    f"Rate limit reached, waiting {wait_time:0.2f} seconds"
                )
                await asyncio.sleep(wait_time)

    async def send_message(self, message: SlackMessage) -> Dict[str, Any]:
        """メッセージ送信"""
        data = {
            "channel": message.channel,
            "text": message.text,
            "unfurl_links": message.unfurl_links,
            "unfurl_media": message.unfurl_media,
        }

        if message.blocks:
            data["blocks"] = message.blocks

        if message.attachments:
            data["attachments"] = message.attachments

        if message.thread_ts:
            data["thread_ts"] = message.thread_ts
            data["reply_broadcast"] = message.reply_broadcast

        if message.metadata:
            data["metadata"] = message.metadata

        result = await self._make_api_request("POST", "chat.postMessage", data)

        # 履歴に記録
        self.message_history.append(
            {
                "timestamp": message.timestamp.isoformat(),
                "channel": message.channel,
                "message": (
                    message.text[:100] + "..."
                    if len(message.text) > 100
                    else message.text
                ),
                "success": result.get("ok", False),
                "ts": result.get("ts"),
                "message_type": message.message_type.value,
            }
        )

        # 履歴サイズ制限
        if len(self.message_history) > self.max_history_size:
            self.message_history = self.message_history[-self.max_history_size :]

        return result

    async def send_webhook_message(self, text: str, **kwargs) -> bool:
        """Webhook経由でメッセージ送信"""
        if not self.webhook_url:
            self.logger.warning("Webhook URL not configured")
            return False

        payload = {"text": text, **kwargs}

        try:
            if AIOHTTP_AVAILABLE:
                # aiohttp を使用
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.webhook_url, json=payload) as response:
                        success = response.status == 200

                        if success:

                        else:
                            self.logger.error(f"Webhook failed: {response.status}")

                        return success
            elif REQUESTS_AVAILABLE:
                # requests を使用
                def sync_webhook():
                    """sync_webhookメソッド"""
                    response = requests.post(self.webhook_url, json=payload)
                    return response.status_code == 200

                success = await asyncio.to_thread(sync_webhook)

                if success:

                else:
                    self.logger.error("Webhook failed")

                return success
            else:
                # フォールバック
                self.logger.warning("No HTTP client available for webhook")
                return False

        except Exception as e:
            self.logger.error(f"Webhook error: {e}")
            return False

    async def get_channels(
        self,
        types: Optional[List[SlackChannelType]] = None,
        exclude_archived: bool = True,
    ) -> List[SlackChannel]:
        """チャンネル一覧取得"""
        types_param = ",".join(
            [
                t.value
                for t in (types or [SlackChannelType.PUBLIC, SlackChannelType.PRIVATE])
            ]
        )

        data = {
            "types": types_param,
            "exclude_archived": exclude_archived,
            "limit": 1000,
        }

        result = await self._make_api_request("GET", "conversations.list", data)

        if not result.get("ok"):
            return []

        channels = []
        for channel_data in result.get("channels", []):
            channel = SlackChannel(
                id=channel_data["id"],
                name=channel_data["name"],
                channel_type=SlackChannelType(
                    channel_data.get("type", "public_channel")
                ),
                is_archived=channel_data.get("is_archived", False),
                is_private=channel_data.get("is_private", False),
                member_count=channel_data.get("num_members", 0),
                topic=channel_data.get("topic", {}).get("value", ""),
                purpose=channel_data.get("purpose", {}).get("value", ""),
                created=(
                    datetime.fromtimestamp(channel_data.get("created", 0))
                    if channel_data.get("created")
                    else None
                ),
            )
            channels.append(channel)
            self.channels_cache[channel.id] = channel

        return channels

    async def get_users(self) -> List[SlackUser]:
        """ユーザー一覧取得"""
        result = await self._make_api_request("GET", "users.list")

        if not result.get("ok"):
            return []

        users = []
        for user_data in result.get("members", []):
            user = SlackUser(
                id=user_data["id"],
                name=user_data["name"],
                real_name=user_data.get("real_name", ""),
                email=user_data.get("profile", {}).get("email"),
                is_bot=user_data.get("is_bot", False),
                is_admin=user_data.get("is_admin", False),
                is_owner=user_data.get("is_owner", False),
                timezone=user_data.get("tz"),
                profile=user_data.get("profile", {}),
            )
            users.append(user)
            self.users_cache[user.id] = user

        return users

    async def send_formatted_message(
        self, channel: str, title: str, content: str, color: str = "good"
    ) -> Dict[str, Any]:
        """フォーマット済みメッセージ送信"""
        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": title}},
            {"type": "section", "text": {"type": "mrkdwn", "text": content}},
        ]

        message = SlackMessage(
            channel=channel,
            text=f"{title}\n{content}",  # フォールバック
            message_type=SlackMessageType.BLOCKS,
            blocks=blocks,
        )

        return await self.send_message(message)

    async def send_4sages_notification(
        self, sage_type: str, message: str, priority: str = "normal"
    ) -> Dict[str, Any]:
        """4賢者システム通知"""
        if not self.sage_integration:
            return await self.send_webhook_message(message)

        emoji_map = {
            "Knowledge Sage": "📚",
            "Task Oracle": "📋",
            "Crisis Sage": "🚨",
            "Search Mystic": "🔍",
        }

        priority_colors = {
            "low": "good",
            "normal": "#439FE0",
            "high": "warning",
            "critical": "danger",
        }

        emoji = emoji_map.get(sage_type, "🤖")
        color = priority_colors.get(priority, "#439FE0")

        title = f"{emoji} {sage_type} Notification"

        try:
            from core import get_config

            config = get_config()
            channel = config.get("slack.sages_channel", "general")
        except:
            import os

            channel = os.environ.get("SLACK_SAGES_CHANNEL", "general")

        return await self.send_formatted_message(channel, title, message, color)

    def register_event_handler(self, event_type: str, handler: Callable):
        """イベントハンドラ登録"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    async def handle_event(self, event_type: str, event_data: Dict[str, Any]):
        """イベント処理"""
        handlers = self.event_handlers.get(event_type, [])

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_data)
                else:
                    handler(event_data)
            except Exception as e:
                self.logger.error(f"Event handler error for {event_type}: {e}")

    async def send_error_alert(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """エラーアラート送信"""
        error_type = error.__class__.__name__
        error_msg = str(error)

        message_parts = [
            f"🚨 **Error Alert: {error_type}**",
            f"",
            f"**Message:** `{error_msg}`",
        ]

        if context:
            message_parts.extend([f"", f"**Context:**"])
            for key, value in context.items():
                message_parts.append(f"• {key}: `{value}`")

        message_parts.extend(
            [f"", f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
        )

        message_text = "\n".join(message_parts)

        try:
            # 4賢者通知を優先
            result = await self.send_4sages_notification(
                "Crisis Sage", message_text, "critical"
            )
            return result.get("ok", False)
        except:
            # フォールバックでWebhook使用
            return await self.send_webhook_message(message_text)

    async def get_message_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """メッセージ履歴取得"""
        return self.message_history[-limit:]

    async def test_connection(self) -> Dict[str, Any]:
        """接続テスト"""
        test_results = {
            "bot_token": bool(self.bot_token),
            "webhook_url": bool(self.webhook_url),
            "api_test": False,
            "webhook_test": False,
        }

        # API テスト
        if self.bot_token:
            try:
                result = await self._make_api_request("POST", "auth.test")
                test_results["api_test"] = result.get("ok", False)
                if test_results["api_test"]:
                    test_results["bot_info"] = {
                        "user": result.get("user"),
                        "team": result.get("team"),
                        "url": result.get("url"),
                    }
            except Exception as e:
                self.logger.error(f"API test failed: {e}")

        # Webhook テスト
        if self.webhook_url:
            try:
                test_results["webhook_test"] = await self.send_webhook_message(
                    "🔗 Elders Guild Slack API Integration test - OK"
                )
            except Exception as e:
                self.logger.error(f"Webhook test failed: {e}")

        return test_results

# ユーティリティ関数
async def create_slack_integration(
    config: Optional[Dict[str, Any]] = None,
) -> SlackAPIIntegration:
    """Slack統合システムのファクトリ関数"""
    integration = SlackAPIIntegration(config)
    return integration

def format_code_block(code: str, language: str = "") -> str:
    """コードブロックフォーマット"""
    return f"```{language}\n{code}\n```"

def format_user_mention(user_id: str) -> str:
    """ユーザーメンション形式"""
    return f"<@{user_id}>"

def format_channel_mention(channel_id: str) -> str:
    """チャンネルメンション形式"""
    return f"<#{channel_id}>"

if __name__ == "__main__":
    # テスト実行
    import sys

    async def main():
        """mainメソッド"""
        print("Elders Guild Slack API Integration v1.0 Test")
        print("=" * 50)

        integration = await create_slack_integration()

        # 接続テスト
        test_results = await integration.test_connection()

        print("Connection Test Results:")
        for key, value in test_results.items():
            status = "✅" if value else "❌"
            print(f"{status} {key}: {value}")

        if test_results.get("api_test") or test_results.get("webhook_test"):
            print("\n✅ Slack API Integration is working!")

            # 4賢者通知テスト
            await integration.send_4sages_notification(
                "Knowledge Sage",
                "Slack API Integration test completed successfully",
                "normal",
            )
        else:
            print("\n❌ Slack API Integration setup required")
            print("\nTo configure:")
            print("1.0 Set SLACK_BOT_TOKEN environment variable")
            print("2.0 Set SLACK_WEBHOOK_URL environment variable")
            print("3.0 Or add to config/slack.conf")

    if sys.version_info >= (3, 7):
        asyncio.run(main())
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
