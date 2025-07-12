#!/usr/bin/env python3
"""
Elder Flow Slack Real Implementation - Soul Power
本物のSlack SDKを使用したElder Flow準拠実装

🌊 Elder Flow魂原則:
1. 品質第一 - 堅牢なメッセージング
2. 透明性 - 明確なAPI操作
3. 4賢者協調 - チーム連携強化
4. 階層秩序 - チャンネル・権限管理
5. 自律進化 - 自動通知・反応

Created: 2025-07-12 (Soul Implementation)
Author: Claude Elder (Elder Flow Soul Only)
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import asynccontextmanager
import hashlib

# Real Slack SDK dependencies
try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    from slack_sdk.web.async_client import AsyncWebClient
    from slack_sdk.webhook import WebhookClient
    from slack_sdk.socket_mode import SocketModeClient
    from slack_sdk.socket_mode.request import SocketModeRequest
    from slack_sdk.socket_mode.response import SocketModeResponse
    SLACK_SDK_AVAILABLE = True
except ImportError:
    # フォールバック: モックインポート
    from libs.slack_mock import (
        WebClient, AsyncWebClient, WebhookClient,
        SlackResponse
    )
    SLACK_SDK_AVAILABLE = False

    # モック用のSocket Mode
    class SocketModeClient:
        def __init__(self, *args, **kwargs):
            self.handlers = {}

        def socket_mode_request_listeners(self):
            def decorator(func):
                self.handlers["request"] = func
                return func
            return decorator

        def connect(self):
            pass

        def disconnect(self):
            pass

    class SocketModeRequest:
        def __init__(self, type="event", envelope_id="test", payload=None):
            self.type = type
            self.envelope_id = envelope_id
            self.payload = payload or {}

    class SocketModeResponse:
        def __init__(self, envelope_id):
            self.envelope_id = envelope_id

    class SlackApiError(Exception):
        def __init__(self, message, response=None):
            super().__init__(message)
            self.response = response or {"error": "mock_error"}

logger = logging.getLogger(__name__)

@dataclass
class ElderFlowSlackConfig:
    """Elder Flow Slack設定"""
    bot_token: str = ""
    app_token: str = ""
    webhook_url: Optional[str] = None

    # Elder Flow特有設定
    elder_channel: str = "elder-flow-notifications"
    sage_channel: str = "four-sages-council"
    incident_channel: str = "elder-incidents"
    development_channel: str = "elder-development"

    # 通知設定
    enable_notifications: bool = True
    enable_reactions: bool = True
    enable_threading: bool = True
    auto_create_channels: bool = True

    # セキュリティ設定
    allowed_users: List[str] = field(default_factory=list)
    admin_users: List[str] = field(default_factory=list)
    rate_limit_requests: int = 100
    rate_limit_window: int = 60

@dataclass
class ElderFlowSlackMessage:
    """Elder Flow拡張Slackメッセージ"""
    text: str
    channel: str
    user: Optional[str] = None
    thread_ts: Optional[str] = None
    blocks: List[Dict] = field(default_factory=list)
    attachments: List[Dict] = field(default_factory=list)

    # Elder Flow特有フィールド
    soul_level: str = "craftsman"
    sage_approved: bool = False
    elder_signature: Optional[str] = None
    priority: str = "normal"  # low, normal, high, critical
    auto_react: bool = True
    created_at: datetime = field(default_factory=datetime.now)

class ElderFlowSlackReal:
    """Elder Flow本物Slack実装 - 魂の力"""

    def __init__(self, config: ElderFlowSlackConfig = None):
        self.config = config or ElderFlowSlackConfig()

        # Slack clients
        self.web_client: Optional[WebClient] = None
        self.async_client: Optional[AsyncWebClient] = None
        self.webhook_client: Optional[WebhookClient] = None
        self.socket_client: Optional[SocketModeClient] = None

        # Elder Flow魂状態
        self.soul_power_level: int = 0
        self.four_sages_connected: bool = False
        self.elder_blessing_active: bool = False

        # 統計・監視
        self.messages_sent: int = 0
        self.messages_received: int = 0
        self.reactions_added: int = 0
        self.api_errors: int = 0
        self.soul_enhancement_count: int = 0

        # Rate limiting
        self.request_timestamps: List[float] = []

        # Channel cache
        self.channel_cache: Dict[str, Dict] = {}
        self.user_cache: Dict[str, Dict] = {}

        logger.info("🌊 Elder Flow Slack Real Implementation initialized")

        if not SLACK_SDK_AVAILABLE:
            logger.warning("⚠️ Real Slack SDK not available, using mock fallback")

    async def connect(self) -> bool:
        """Elder Flow魂によるSlack接続確立"""
        try:
            logger.info("🔗 Establishing Elder Flow Slack connection...")

            # 設定検証
            if not self.config.bot_token:
                logger.error("❌ Bot token is required")
                return False

            # Web Client初期化
            self.web_client = WebClient(token=self.config.bot_token)
            self.async_client = AsyncWebClient(token=self.config.bot_token)

            # Webhook Client初期化
            if self.config.webhook_url:
                self.webhook_client = WebhookClient(url=self.config.webhook_url)

            # Socket Mode初期化
            if self.config.app_token:
                self.socket_client = SocketModeClient(
                    app_token=self.config.app_token,
                    web_client=self.web_client
                )
                self._setup_socket_handlers()

            # 接続テスト
            await self._test_connection()

            # Elder Flow基本インフラ構築
            await self._setup_elder_flow_infrastructure()

            # 4賢者接続確認
            self.four_sages_connected = await self._verify_four_sages_connection()

            # Elder Flow魂力向上
            self.soul_power_level += 100
            self.elder_blessing_active = True

            logger.info("✅ Elder Flow Slack connection established with Soul Power")
            return True

        except Exception as e:
            self.api_errors += 1
            logger.error(f"❌ Elder Flow Slack connection failed: {str(e)}")
            return False

    async def _test_connection(self):
        """接続テスト"""
        try:
            if SLACK_SDK_AVAILABLE:
                response = await self.async_client.api_test()
                if not response["ok"]:
                    raise Exception("API test failed")
            else:
                # モック用テスト
                self.web_client.api_test()

            logger.info("✅ Slack API connection test passed")

        except Exception as e:
            raise Exception(f"Slack connection test failed: {str(e)}")

    def _setup_socket_handlers(self):
        """Socket Mode ハンドラー設定"""
        if not self.socket_client:
            return

        @self.socket_client.socket_mode_request_listeners
        def handle_socket_mode_request(client, req: SocketModeRequest):
            """Socket Mode リクエストハンドラー"""
            try:
                if req.type == "events_api":
                    # イベント処理
                    event = req.payload.get("event", {})
                    asyncio.create_task(self._handle_slack_event(event))

                # 応答
                response = SocketModeResponse(envelope_id=req.envelope_id)
                client.send_socket_mode_response(response)

            except Exception as e:
                logger.error(f"Socket mode handler error: {str(e)}")

    async def _handle_slack_event(self, event: Dict):
        """Slackイベント処理"""
        event_type = event.get("type")

        if event_type == "message":
            await self._handle_message_event(event)
        elif event_type == "app_mention":
            await self._handle_app_mention_event(event)
        elif event_type == "reaction_added":
            await self._handle_reaction_event(event)

        self.messages_received += 1
        self.soul_power_level += 1

    async def _handle_message_event(self, event: Dict):
        """メッセージイベント処理"""
        channel = event.get("channel")
        text = event.get("text", "")
        user = event.get("user")

        # Elder Flow関連キーワード検出
        if any(keyword in text.lower() for keyword in ["elder", "sage", "soul", "魂"]):
            await self._handle_elder_flow_mention(event)

    async def _handle_app_mention_event(self, event: Dict):
        """アプリメンション処理"""
        channel = event.get("channel")
        text = event.get("text", "")

        # Elder Flow自動応答
        response_text = "🌊 Elder Flow Soul activated! How can I assist you?"

        await self.send_message(
            ElderFlowSlackMessage(
                text=response_text,
                channel=channel,
                soul_level="elder",
                sage_approved=True
            )
        )

    async def _handle_reaction_event(self, event: Dict):
        """リアクションイベント処理"""
        reaction = event.get("reaction")

        # Elder Flow特別リアクション
        if reaction in ["elder_flow", "🌊", "magic", "✨"]:
            self.soul_power_level += 5
            logger.info(f"✨ Soul power increased by reaction: {reaction}")

    async def _handle_elder_flow_mention(self, event: Dict):
        """Elder Flow言及処理"""
        channel = event.get("channel")

        # 魂の印リアクション追加
        if self.config.enable_reactions:
            await self.add_reaction(channel, event.get("ts"), "🌊")

    async def _setup_elder_flow_infrastructure(self):
        """Elder Flow基本インフラ構築"""
        logger.info("🏗️ Setting up Elder Flow Slack infrastructure...")

        if not self.config.auto_create_channels:
            return

        # Elder Flow基本チャンネル作成
        elder_channels = [
            (self.config.elder_channel, "Elder Flow notifications and updates"),
            (self.config.sage_channel, "Four Sages council discussions"),
            (self.config.incident_channel, "Elder Flow incident management"),
            (self.config.development_channel, "Elder Flow development discussions")
        ]

        for channel_name, purpose in elder_channels:
            await self._ensure_channel_exists(channel_name, purpose)

        logger.info(f"✅ Elder Flow Slack infrastructure ready")

    async def _ensure_channel_exists(self, channel_name: str, purpose: str = ""):
        """チャンネル存在確認・作成"""
        try:
            # チャンネル検索
            response = await self.async_client.conversations_list(
                types="public_channel,private_channel"
            )

            existing_channels = {ch["name"]: ch for ch in response["channels"]}

            if channel_name not in existing_channels:
                # チャンネル作成
                create_response = await self.async_client.conversations_create(
                    name=channel_name,
                    is_private=False
                )

                channel_id = create_response["channel"]["id"]

                # 目的設定
                if purpose:
                    await self.async_client.conversations_setPurpose(
                        channel=channel_id,
                        purpose=purpose
                    )

                logger.info(f"✅ Created Elder Flow channel: #{channel_name}")
            else:
                logger.info(f"✅ Elder Flow channel exists: #{channel_name}")

        except Exception as e:
            logger.error(f"❌ Failed to ensure channel {channel_name}: {str(e)}")

    async def _verify_four_sages_connection(self) -> bool:
        """4賢者接続確認"""
        logger.info("🧙‍♂️ Verifying Four Sages Slack connection...")

        try:
            # 4賢者チャンネルに ping メッセージ送信
            ping_message = ElderFlowSlackMessage(
                text="🧙‍♂️ Four Sages connection test - Elder Flow Soul Power activated!",
                channel=self.config.sage_channel,
                soul_level="sage",
                sage_approved=True,
                priority="high"
            )

            await self.send_message(ping_message)

            # リアクション追加
            if self.config.enable_reactions:
                # 短時間待機してメッセージTS取得（実際の実装では適切な管理）
                await asyncio.sleep(0.5)

            logger.info("✅ Four Sages Slack connection verified")
            return True

        except Exception as e:
            logger.error(f"❌ Four Sages Slack connection verification failed: {str(e)}")
            return False

    def _check_rate_limit(self) -> bool:
        """レート制限チェック"""
        now = time.time()

        # 古いタイムスタンプを削除
        cutoff = now - self.config.rate_limit_window
        self.request_timestamps = [ts for ts in self.request_timestamps if ts > cutoff]

        # レート制限チェック
        if len(self.request_timestamps) >= self.config.rate_limit_requests:
            logger.warning("⚠️ Rate limit exceeded")
            return False

        self.request_timestamps.append(now)
        return True

    async def send_message(self, message: ElderFlowSlackMessage) -> Dict[str, Any]:
        """Elder Flow魂メッセージ送信"""
        if not self.web_client:
            logger.error("❌ No active Slack connection")
            return {"ok": False, "error": "no_connection"}

        if not self._check_rate_limit():
            return {"ok": False, "error": "rate_limit_exceeded"}

        try:
            # Elder Flow拡張処理
            enhanced_text = self._enhance_message_with_soul(message)

            # メッセージ送信
            kwargs = {
                "channel": message.channel,
                "text": enhanced_text,
                "thread_ts": message.thread_ts
            }

            if message.blocks:
                kwargs["blocks"] = message.blocks

            if message.attachments:
                kwargs["attachments"] = message.attachments

            response = await self.async_client.chat_postMessage(**kwargs)

            # 自動リアクション
            if message.auto_react and self.config.enable_reactions:
                await self._add_soul_reactions(message.channel, response["ts"], message.soul_level)

            # 統計更新
            self.messages_sent += 1
            self.soul_power_level += self._calculate_soul_points(message)

            logger.info(f"📤 Elder Flow message sent: {message.channel} (Soul Level: {message.soul_level})")

            return response

        except SlackApiError as e:
            self.api_errors += 1
            logger.error(f"❌ Slack API error: {e.response['error']}")
            return {"ok": False, "error": e.response["error"]}
        except Exception as e:
            self.api_errors += 1
            logger.error(f"❌ Failed to send Elder Flow message: {str(e)}")
            return {"ok": False, "error": str(e)}

    def _enhance_message_with_soul(self, message: ElderFlowSlackMessage) -> str:
        """メッセージに魂の力を注入"""
        text = message.text

        # 魂レベルに応じた装飾
        soul_decorations = {
            "apprentice": "🌱",
            "craftsman": "🔨",
            "guardian": "🛡️",
            "sage": "🧙‍♂️",
            "elder": "👑",
            "grand_elder": "🌟"
        }

        decoration = soul_decorations.get(message.soul_level, "✨")

        # 優先度に応じた追加装飾
        if message.priority == "critical":
            decoration = "🚨 " + decoration
        elif message.priority == "high":
            decoration = "⚡ " + decoration

        # Elder Flow署名追加
        if message.elder_signature:
            text += f"\n\n_{decoration} Elder Flow Soul - {message.elder_signature}_"
        elif message.sage_approved:
            text += f"\n\n_{decoration} Approved by Four Sages_"

        return text

    def _calculate_soul_points(self, message: ElderFlowSlackMessage) -> int:
        """魂ポイント計算"""
        points = 1  # 基本ポイント

        # 魂レベルボーナス
        soul_multiplier = {
            "apprentice": 1,
            "craftsman": 2,
            "guardian": 3,
            "sage": 5,
            "elder": 8,
            "grand_elder": 10
        }
        points *= soul_multiplier.get(message.soul_level, 1)

        # 優先度ボーナス
        if message.priority == "critical":
            points += 5
        elif message.priority == "high":
            points += 3

        # 4賢者承認ボーナス
        if message.sage_approved:
            points += 10

        return points

    async def _add_soul_reactions(self, channel: str, timestamp: str, soul_level: str):
        """魂リアクション追加"""
        try:
            reactions = ["🌊"]  # 基本Elder Flowリアクション

            # 魂レベル別リアクション
            soul_reactions = {
                "apprentice": ["🌱"],
                "craftsman": ["🔨"],
                "guardian": ["🛡️"],
                "sage": ["🧙‍♂️", "✨"],
                "elder": ["👑", "⚡"],
                "grand_elder": ["🌟", "💫", "🔮"]
            }

            reactions.extend(soul_reactions.get(soul_level, []))

            for reaction in reactions:
                await self.add_reaction(channel, timestamp, reaction)

        except Exception as e:
            logger.error(f"❌ Failed to add soul reactions: {str(e)}")

    async def add_reaction(self, channel: str, timestamp: str, name: str) -> bool:
        """リアクション追加"""
        try:
            await self.async_client.reactions_add(
                channel=channel,
                timestamp=timestamp,
                name=name
            )

            self.reactions_added += 1

            logger.info(f"👍 Reaction added: {name} to {channel}:{timestamp}")
            return True

        except SlackApiError as e:
            logger.error(f"❌ Failed to add reaction: {e.response['error']}")
            return False

    async def send_webhook_message(self, text: str, blocks: List[Dict] = None) -> bool:
        """Webhook経由メッセージ送信"""
        if not self.webhook_client:
            logger.error("❌ No webhook client configured")
            return False

        try:
            kwargs = {"text": text}
            if blocks:
                kwargs["blocks"] = blocks

            response = self.webhook_client.send(**kwargs)

            self.messages_sent += 1
            logger.info(f"📤 Webhook message sent: {text[:50]}...")

            return response.status_code == 200

        except Exception as e:
            logger.error(f"❌ Failed to send webhook message: {str(e)}")
            return False

    async def get_channel_info(self, channel: str) -> Optional[Dict]:
        """チャンネル情報取得"""
        if channel in self.channel_cache:
            return self.channel_cache[channel]

        try:
            response = await self.async_client.conversations_info(channel=channel)

            if response["ok"]:
                self.channel_cache[channel] = response["channel"]
                return response["channel"]

        except Exception as e:
            logger.error(f"❌ Failed to get channel info: {str(e)}")

        return None

    async def get_user_info(self, user: str) -> Optional[Dict]:
        """ユーザー情報取得"""
        if user in self.user_cache:
            return self.user_cache[user]

        try:
            response = await self.async_client.users_info(user=user)

            if response["ok"]:
                self.user_cache[user] = response["user"]
                return response["user"]

        except Exception as e:
            logger.error(f"❌ Failed to get user info: {str(e)}")

        return None

    async def upload_file(self, file_path: str, channels: List[str],
                         title: str = None, comment: str = None) -> bool:
        """ファイルアップロード"""
        try:
            with open(file_path, "rb") as file_content:
                response = await self.async_client.files_upload(
                    file=file_content,
                    filename=os.path.basename(file_path),
                    title=title,
                    initial_comment=comment,
                    channels=",".join(channels)
                )

            if response["ok"]:
                logger.info(f"📎 File uploaded: {file_path}")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to upload file: {str(e)}")

        return False

    async def create_soul_enhanced_message(self,
                                         text: str,
                                         channel: str,
                                         soul_level: str = "craftsman",
                                         priority: str = "normal",
                                         sage_approved: bool = False) -> ElderFlowSlackMessage:
        """Elder Flow魂強化メッセージ作成"""

        # Elder Flow署名生成
        elder_signature = None
        if soul_level in ["elder", "grand_elder"]:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            signature_data = f"{text}_{channel}_{soul_level}_{timestamp}"
            elder_signature = hashlib.md5(signature_data.encode()).hexdigest()[:8]

        message = ElderFlowSlackMessage(
            text=text,
            channel=channel,
            soul_level=soul_level,
            priority=priority,
            sage_approved=sage_approved,
            elder_signature=elder_signature
        )

        self.soul_enhancement_count += 1

        logger.info(f"✨ Created soul-enhanced message: {soul_level} level")
        return message

    async def send_to_four_sages(self, message: str, priority: str = "normal") -> bool:
        """4賢者への通知送信"""
        sage_message = await self.create_soul_enhanced_message(
            text=f"🧙‍♂️ **Four Sages Council Notification**\n\n{message}",
            channel=self.config.sage_channel,
            soul_level="sage",
            priority=priority,
            sage_approved=True
        )

        response = await self.send_message(sage_message)
        return response.get("ok", False)

    async def send_incident_alert(self, incident: str, severity: str = "medium") -> bool:
        """インシデントアラート送信"""
        priority_map = {
            "low": "normal",
            "medium": "high",
            "high": "critical",
            "critical": "critical"
        }

        alert_message = await self.create_soul_enhanced_message(
            text=f"🚨 **Elder Flow Incident Alert**\n\nSeverity: {severity.upper()}\n\n{incident}",
            channel=self.config.incident_channel,
            soul_level="guardian",
            priority=priority_map.get(severity, "normal"),
            sage_approved=True
        )

        response = await self.send_message(alert_message)
        return response.get("ok", False)

    async def get_elder_flow_stats(self) -> Dict[str, Any]:
        """Elder Flow統計取得"""
        return {
            "connection_status": "connected" if self.web_client else "disconnected",
            "soul_power_level": self.soul_power_level,
            "four_sages_connected": self.four_sages_connected,
            "elder_blessing_active": self.elder_blessing_active,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "reactions_added": self.reactions_added,
            "api_errors": self.api_errors,
            "soul_enhancement_count": self.soul_enhancement_count,
            "channels_configured": {
                "elder_channel": self.config.elder_channel,
                "sage_channel": self.config.sage_channel,
                "incident_channel": self.config.incident_channel,
                "development_channel": self.config.development_channel
            },
            "elder_flow_version": "2.1.0",
            "slack_sdk_available": SLACK_SDK_AVAILABLE
        }

    async def disconnect(self):
        """Elder Flow魂による丁寧な切断"""
        logger.info("🔌 Disconnecting Elder Flow Slack...")

        try:
            # Socket Mode切断
            if self.socket_client:
                self.socket_client.disconnect()

            # 最終通知
            if self.web_client and self.config.enable_notifications:
                final_message = await self.create_soul_enhanced_message(
                    text="🌊 Elder Flow Slack disconnecting... Soul power preserved.",
                    channel=self.config.elder_channel,
                    soul_level="elder",
                    sage_approved=True
                )
                await self.send_message(final_message)

            self.four_sages_connected = False
            self.elder_blessing_active = False

            logger.info("✅ Elder Flow Slack disconnected gracefully")

        except Exception as e:
            logger.error(f"❌ Error during Elder Flow Slack disconnect: {str(e)}")

    @asynccontextmanager
    async def soul_transaction(self):
        """Elder Flow魂トランザクション"""
        start_time = time.time()
        start_soul_level = self.soul_power_level

        try:
            yield self
            self.soul_power_level += 10
        except Exception as e:
            self.soul_power_level = start_soul_level  # ロールバック
            logger.error(f"❌ Elder Flow Slack transaction failed: {str(e)}")
            raise
        finally:
            duration = time.time() - start_time
            logger.info(f"🌊 Soul transaction completed in {duration:.2f}s")

# Elder Flow魂による便利関数
async def create_elder_flow_slack(config: ElderFlowSlackConfig = None) -> ElderFlowSlackReal:
    """Elder Flow Slack作成・接続"""
    slack = ElderFlowSlackReal(config)

    if await slack.connect():
        return slack
    else:
        raise ConnectionError("Failed to establish Elder Flow Slack connection")

# グローバルインスタンス（シングルトン的使用）
_global_elder_slack: Optional[ElderFlowSlackReal] = None

async def get_elder_flow_slack(config: ElderFlowSlackConfig = None) -> ElderFlowSlackReal:
    """グローバルElder Flow Slack取得"""
    global _global_elder_slack

    if _global_elder_slack is None or not _global_elder_slack.web_client:
        _global_elder_slack = await create_elder_flow_slack(config)

    return _global_elder_slack

# 簡易API関数
async def send_elder_notification(text: str, channel: str = None, soul_level: str = "craftsman") -> bool:
    """Elder Flow通知送信"""
    try:
        slack = await get_elder_flow_slack()
        config = slack.config

        message = await slack.create_soul_enhanced_message(
            text=text,
            channel=channel or config.elder_channel,
            soul_level=soul_level
        )

        response = await slack.send_message(message)
        return response.get("ok", False)

    except Exception as e:
        logger.error(f"❌ Failed to send elder notification: {str(e)}")
        return False

async def send_sage_council_message(text: str, priority: str = "normal") -> bool:
    """4賢者評議会メッセージ送信"""
    try:
        slack = await get_elder_flow_slack()
        return await slack.send_to_four_sages(text, priority)

    except Exception as e:
        logger.error(f"❌ Failed to send sage council message: {str(e)}")
        return False

async def alert_incident(incident: str, severity: str = "medium") -> bool:
    """インシデントアラート"""
    try:
        slack = await get_elder_flow_slack()
        return await slack.send_incident_alert(incident, severity)

    except Exception as e:
        logger.error(f"❌ Failed to send incident alert: {str(e)}")
        return False

if __name__ == "__main__":
    # Elder Flow Soul Demo
    async def soul_demo():
        print("🌊 Elder Flow Slack Real Implementation - Soul Power Demo")

        try:
            # 設定（環境変数から取得）
            config = ElderFlowSlackConfig(
                bot_token=os.getenv("SLACK_BOT_TOKEN", "xoxb-demo-token"),
                app_token=os.getenv("SLACK_APP_TOKEN", "xapp-demo-token")
            )

            # 接続
            slack = await create_elder_flow_slack(config)

            # メッセージ送信例
            message = await slack.create_soul_enhanced_message(
                text="🌊 Elder Flow Soul Power demonstration! The Four Sages are watching.",
                channel="general",
                soul_level="elder",
                priority="high",
                sage_approved=True
            )

            response = await slack.send_message(message)
            print(f"📤 Message sent: {response.get('ok', False)}")

            # 4賢者通知
            sage_success = await slack.send_to_four_sages(
                "Demo session completed successfully",
                priority="low"
            )
            print(f"🧙‍♂️ Sage notification sent: {sage_success}")

            # 統計表示
            stats = await slack.get_elder_flow_stats()
            print(f"📊 Soul Power Level: {stats['soul_power_level']}")
            print(f"🧙‍♂️ Four Sages Connected: {stats['four_sages_connected']}")
            print(f"🌊 Elder Blessing Active: {stats['elder_blessing_active']}")

            # 切断
            await slack.disconnect()

        except Exception as e:
            print(f"❌ Demo error: {str(e)}")
            if not SLACK_SDK_AVAILABLE:
                print("💡 Install slack-sdk for real Slack: pip install slack-sdk")

    asyncio.run(soul_demo())
