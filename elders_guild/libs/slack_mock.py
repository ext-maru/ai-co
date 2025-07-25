#!/usr/bin/env python3
"""
Slack SDK Complete Mock Implementation
Phase 3: 完全なSlack SDKモック実装
"""
import asyncio
import json
import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class MockMessage:
    """Mock Slack message"""

    text: str
    channel: str
    user: str = "U123456789"
    ts: str = field(default_factory=lambda: str(time.time()))
    thread_ts: Optional[str] = None
    attachments: List[Dict] = field(default_factory=list)
    blocks: List[Dict] = field(default_factory=list)


@dataclass
class MockUser:
    """Mock Slack user"""

    id: str
    name: str
    real_name: str
    email: str
    is_bot: bool = False
    is_admin: bool = False
    profile: Dict = field(default_factory=dict)


@dataclass
class MockChannel:
    """Mock Slack channel"""

    id: str
    name: str
    is_private: bool = False
    is_archived: bool = False
    members: List[str] = field(default_factory=list)
    topic: Dict = field(default_factory=lambda: {"value": ""})
    purpose: Dict = field(default_factory=lambda: {"value": ""})


class MockWebClient:
    """Mock Slack WebClient"""

    def __init__(self, token=None):
        """初期化メソッド"""
        self.token = token
        self.messages = defaultdict(list)
        self.channels = {}
        self.users = {}
        self.reactions = defaultdict(list)
        self.files = {}
        self._init_default_data()
        logger.info("Mock Slack WebClient initialized")

    def _init_default_data(self):
        """Initialize with some default data"""
        # Default channels
        self.channels = {
            "C123456789": MockChannel(
                id="C123456789", name="general", members=["U123456789", "U987654321"]
            ),
            "C987654321": MockChannel(
                id="C987654321", name="random", members=["U123456789", "U987654321"]
            ),
            "C111111111": MockChannel(
                id="C111111111", name="engineering", members=["U123456789"]
            ),
        }

        # Default users
        self.users = {
            "U123456789": MockUser(
                id="U123456789",
                name="testuser",
                real_name="Test User",
                email="test@example.com",
            ),
            "U987654321": MockUser(
                id="U987654321",
                name="botuser",
                real_name="Bot User",
                email="bot@example.com",
                is_bot=True,
            ),
        }

    def chat_postMessage(
        self,
        channel,
        text=None,
        blocks=None,
        attachments=None,
        thread_ts=None,
        **kwargs,
    ):
        """Post a message to a channel"""
        if not channel:
            raise ValueError("channel is required")

        # 複雑な条件判定
        if not text and not blocks and not attachments:
            raise ValueError("One of text, blocks, or attachments is required")

        message = MockMessage(
            text=text or "",
            channel=channel,
            thread_ts=thread_ts,
            attachments=attachments or [],
            blocks=blocks or [],
        )

        # Store message
        self.messages[channel].append(message)

        logger.info(f"Message posted to {channel}: {text}")

        return {
            "ok": True,
            "channel": channel,
            "ts": message.ts,
            "message": {
                "text": message.text,
                "user": message.user,
                "ts": message.ts,
                "thread_ts": message.thread_ts,
            },
        }

    def chat_update(self, channel, ts, text=None, blocks=None, attachments=None):
        """Update a message"""
        if not channel or not ts:
            raise ValueError("channel and ts are required")

        # Find and update message
        for message in self.messages.get(channel, []):
            if message.ts == ts:
                if text is not None:
                    message.text = text
                if blocks is not None:
                    message.blocks = blocks
                if attachments is not None:
                    message.attachments = attachments

                logger.info(f"Message updated in {channel} (ts: {ts})")

                return {"ok": True, "channel": channel, "ts": ts, "text": message.text}

        raise Exception(f"Message not found: channel={channel}, ts={ts}")

    def chat_delete(self, channel, ts):
        """Delete a message"""
        if not channel or not ts:
            raise ValueError("channel and ts are required")

        messages = self.messages.get(channel, [])
        self.messages[channel] = [m for m in messages if m.ts != ts]

        logger.info(f"Message deleted from {channel} (ts: {ts})")

        return {"ok": True, "channel": channel, "ts": ts}

    def conversations_list(self, types="public_channel", limit=100, **kwargs):
        """List conversations"""
        channels = []

        for channel in self.channels.values():
            if types == "public_channel" and not channel.is_private:
                channels.append(channel)
            elif types == "private_channel" and channel.is_private:
                channels.append(channel)
            elif types == "public_channel,private_channel":
                channels.append(channel)

        return {
            "ok": True,
            "channels": [
                {
                    "id": c.id,
                    "name": c.name,
                    "is_private": c.is_private,
                    "is_archived": c.is_archived,
                    "num_members": len(c.members),
                }
                for c in channels[:limit]
            ],
        }

    def conversations_info(self, channel):
        """Get conversation info"""
        if channel not in self.channels:
            raise Exception(f"Channel not found: {channel}")

        channel_obj = self.channels[channel]

        return {
            "ok": True,
            "channel": {
                "id": channel_obj.id,
                "name": channel_obj.name,
                "is_private": channel_obj.is_private,
                "is_archived": channel_obj.is_archived,
                "topic": channel_obj.topic,
                "purpose": channel_obj.purpose,
            },
        }

    def conversations_members(self, channel, limit=100):
        """List members of a conversation"""
        if channel not in self.channels:
            raise Exception(f"Channel not found: {channel}")

        members = self.channels[channel].members[:limit]

        return {
            "ok": True,
            "members": members,
            "response_metadata": {"next_cursor": ""},
        }

    def users_list(self, limit=100):
        """List users"""
        return {
            "ok": True,
            "members": [
                {
                    "id": u.id,
                    "name": u.name,
                    "real_name": u.real_name,
                    "is_bot": u.is_bot,
                    "is_admin": u.is_admin,
                    "profile": u.profile,
                }
                for u in list(self.users.values())[:limit]
            ],
        }

    def users_info(self, user):
        """Get user info"""
        if user not in self.users:
            raise Exception(f"User not found: {user}")

        user_obj = self.users[user]

        return {
            "ok": True,
            "user": {
                "id": user_obj.id,
                "name": user_obj.name,
                "real_name": user_obj.real_name,
                "is_bot": user_obj.is_bot,
                "is_admin": user_obj.is_admin,
                "profile": user_obj.profile,
            },
        }

    def reactions_add(self, channel, timestamp, name):
        """Add a reaction to a message"""
        key = f"{channel}:{timestamp}"

        if name not in self.reactions[key]:
            self.reactions[key].append(name)

        logger.info(f"Reaction added: {name} to {channel}:{timestamp}")

        return {"ok": True}

    def reactions_remove(self, channel, timestamp, name):
        """Remove a reaction from a message"""
        key = f"{channel}:{timestamp}"

        if name in self.reactions[key]:
            self.reactions[key].remove(name)

        logger.info(f"Reaction removed: {name} from {channel}:{timestamp}")

        return {"ok": True}

    def files_upload(
        self,
        channels=None,
        content=None,
        file=None,
        filename=None,
        title=None,
        initial_comment=None,
        thread_ts=None,
    ):
        """Upload a file"""
        if not content and not file:
            raise ValueError("One of content or file is required")

        file_id = f"F{uuid.uuid4().hex[:10].upper()}"

        file_obj = {
            "id": file_id,
            "name": filename or "untitled",
            "title": title or filename or "untitled",
            "mimetype": "text/plain",
            "size": len(content) if content else 0,
            "url_private": f"https://files.slack.com/files-pri/{file_id}/{filename}",
            "channels": (
                channels.split(",") if isinstance(channels, str) else (channels or [])
            ),
        }

        self.files[file_id] = file_obj

        # Post initial comment if provided
        if initial_comment and channels:
            for channel in file_obj["channels"]:
                self.chat_postMessage(
                    channel=channel, text=initial_comment, thread_ts=thread_ts
                )

        logger.info(f"File uploaded: {file_obj['name']} (id: {file_id})")

        return {"ok": True, "file": file_obj}

    def api_test(self, error=None):
        """Test API connectivity"""
        if error:
            return {"ok": False, "error": error}
        return {"ok": True}


class MockWebhookClient:
    """Mock Slack WebhookClient"""

    def __init__(self, url):
        """初期化メソッド"""
        self.url = url
        self.messages_sent = []
        logger.info(f"Mock WebhookClient initialized with URL: {url}")

    def send(self, text=None, blocks=None, attachments=None):
        """Send a message via webhook"""
        message = {
            "text": text,
            "blocks": blocks,
            "attachments": attachments,
            "timestamp": datetime.now().isoformat(),
        }

        self.messages_sent.append(message)

        logger.info(f"Webhook message sent: {text}")

        return {"ok": True}


class MockAsyncWebClient:
    """Mock Async Slack WebClient"""

    def __init__(self, token=None):
        """初期化メソッド"""
        self.sync_client = MockWebClient(token)

    async def chat_postMessage(self, **kwargs):
        """Async post message"""
        await asyncio.sleep(0.01)  # Simulate network delay
        return self.sync_client.chat_postMessage(**kwargs)

    async def chat_update(self, **kwargs):
        """Async update message"""
        await asyncio.sleep(0.01)
        return self.sync_client.chat_update(**kwargs)

    async def chat_delete(self, **kwargs):
        """Async delete message"""
        await asyncio.sleep(0.01)
        return self.sync_client.chat_delete(**kwargs)

    async def conversations_list(self, **kwargs):
        """Async list conversations"""
        await asyncio.sleep(0.01)
        return self.sync_client.conversations_list(**kwargs)

    async def users_list(self, **kwargs):
        """Async list users"""
        await asyncio.sleep(0.01)
        return self.sync_client.users_list(**kwargs)

    async def files_upload(self, **kwargs):
        """Async file upload"""
        await asyncio.sleep(0.01)
        return self.sync_client.files_upload(**kwargs)


class MockRTMClient:
    """Mock Slack RTMClient"""

    def __init__(self, token=None):
        """初期化メソッド"""
        self.token = token
        self.handlers = defaultdict(list)
        self.running = False
        logger.info("Mock RTMClient initialized")

    def on(self, event):
        """Decorator to register event handlers"""

        def decorator(func):
            """decoratorメソッド"""
            self.handlers[event].append(func)
            return func

        return decorator

    def start(self):
        """Start the RTM client"""
        self.running = True
        logger.info("Mock RTMClient started")

        # Simulate some events
        self._trigger_event("open", {})
        self._trigger_event(
            "message",
            {
                "type": "message",
                "text": "Hello from RTM!",
                "user": "U123456789",
                "channel": "C123456789",
                "ts": str(time.time()),
            },
        )

    def stop(self):
        """Stop the RTM client"""
        self.running = False
        logger.info("Mock RTMClient stopped")

    def _trigger_event(self, event_type, data):
        """Trigger an event"""
        for handler in self.handlers.get(event_type, []):
            try:
                handler(data)
            except Exception as e:
                logger.error(f"Error in RTM handler: {e}")


# Mock response classes
class SlackResponse:
    """Mock Slack API response"""

    def __init__(self, data):
        """初期化メソッド"""
        self.data = data

    def get(self, key, default=None):
        """getメソッド"""
        return self.data.get(key, default)

    def __getitem__(self, key):
        """__getitem__特殊メソッド"""
        return self.data[key]

    def __contains__(self, key):
        """__contains__特殊メソッド"""
        return key in self.data


# Export as slack_sdk compatible names
WebClient = MockWebClient
WebhookClient = MockWebhookClient
AsyncWebClient = MockAsyncWebClient
RTMClient = MockRTMClient

__all__ = [
    "WebClient",
    "WebhookClient",
    "AsyncWebClient",
    "RTMClient",
    "SlackResponse",
    "MockWebClient",
    "MockWebhookClient",
    "MockAsyncWebClient",
    "MockRTMClient",
]
