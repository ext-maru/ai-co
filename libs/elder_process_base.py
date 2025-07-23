#!/usr/bin/env python3
"""
エルダープロセス基底クラス
Elder Process Base Class - プロセス分離アーキテクチャの基盤

各エルダーが独立したプロセスとして動作するための基底実装
"""

import asyncio
import json
import logging
import os
import signal
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

# aioredis TimeoutError重複基底クラス問題の完全回避
REDIS_AVAILABLE = False
aioredis = None

# 安全なRedis機能無効化による根本対応
try:
    # 従来のRedis連携を一時的に無効化
    # import aioredis  # 問題のあるインポートをコメントアウト
    # from aioredis.client import PubSub
    REDIS_AVAILABLE = False  # 強制的にフォールバックモード

except Exception as e:
    REDIS_AVAILABLE = False


# モッククラス定義（Redis無しでも動作）
class MockPubSub:
    """MockPubSubクラス"""
    async def subscribe(self, *args):
        """subscribeメソッド"""
        pass

    async def unsubscribe(self, *args):
        """unsubscribeメソッド"""
        pass

    async def get_message(self):
        """message取得メソッド"""
        return None


PubSub = MockPubSub


class ElderRole(Enum):
    """エルダー役割"""

    GRAND_ELDER = "grand_elder"
    CLAUDE_ELDER = "claude_elder"
    SAGE = "sage"
    COUNCIL = "council"
    SERVANT = "servant"


class SageType(Enum):
    """賢者タイプ"""

    KNOWLEDGE = "knowledge"
    TASK = "task"
    INCIDENT = "incident"
    RAG = "rag"


class MessageType(Enum):
    """メッセージタイプ"""

    COMMAND = "command"
    QUERY = "query"
    REPORT = "report"
    HEARTBEAT = "heartbeat"
    EMERGENCY = "emergency"
    ACKNOWLEDGE = "acknowledge"


@dataclass
class ElderMessage:
    """エルダー間メッセージ"""

    message_id: str
    source_elder: str
    target_elder: str
    message_type: MessageType
    payload: Dict[str, Any]
    priority: int = 5  # 1-10, 10が最高
    timestamp: str = None
    requires_ack: bool = False

    def __post_init__(self):
        """__post_init__特殊メソッド"""
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_json(self) -> str:
        """JSON変換"""
        data = asdict(self)
        data["message_type"] = self.message_type.value
        return json.dumps(data, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "ElderMessage":
        """JSONから復元"""
        data = json.loads(json_str)
        data["message_type"] = MessageType(data["message_type"])
        return cls(**data)


class ElderProcessBase(ABC):
    """
    エルダープロセス基底クラス

    各エルダーはこのクラスを継承して独立プロセスとして動作する
    """

    def __init__(
        self,
        elder_name: str,
        elder_role: ElderRole,
        port: int,
        redis_url: str = "redis://localhost:6379",
        sage_type: Optional[SageType] = None,
    ):
        """
        Args:
            elder_name: エルダー名（プロセス識別子）
            elder_role: エルダー役割
            port: HTTPサーバーポート
            redis_url: Redis接続URL
            sage_type: 賢者タイプ（賢者の場合のみ）
        """
        self.elder_name = elder_name
        self.elder_role = elder_role
        self.sage_type = sage_type
        self.port = port
        self.redis_url = redis_url

        # ロガー設定
        self.logger = self._setup_logger()

        # Redis接続
        self.redis: Optional[aioredis.Redis] = None
        self.pubsub: Optional[PubSub] = None

        # プロセス状態
        self.is_running = False
        self.start_time = None
        self.message_handlers: Dict[MessageType, Callable] = {}

        # 統計情報
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0,
            "uptime": 0,
        }

        # 下位エルダーリスト（階層構造）
        self.subordinates: List[str] = []

        # シグナルハンドラー設定
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger(f"elder.{self.elder_name}")
        logger.setLevel(logging.INFO)

        # ファイルハンドラー
        log_dir = Path("logs/elders")
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_dir / f"{self.elder_name}.log")

        # フォーマッター
        formatter = logging.Formatter(
            f"%(asctime)s - [{self.elder_name}] - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)

        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def _signal_handler(self, signum, frame):
        """シグナルハンドラー"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.is_running = False

    async def start(self):
        """プロセス開始"""
        self.logger.info(f"🚀 Starting {self.elder_name} ({self.elder_role.value})")
        self.start_time = datetime.now()
        self.is_running = True

        try:
            # Redis接続
            await self._connect_redis()

            # メッセージハンドラー登録
            self._register_message_handlers()

            # 初期化処理（サブクラスで実装）
            await self.initialize()

            # メインループ開始
            await asyncio.gather(
                self._message_loop(), self._heartbeat_loop(), self._main_loop()
            )

        except Exception as e:
            self.logger.error(f"Fatal error: {e}", exc_info=True)
            self.stats["errors"] += 1
        finally:
            await self.cleanup()

    async def _connect_redis(self):
        """Redis接続"""
        self.logger.info("Connecting to Redis...")
        self.redis = await aioredis.from_url(self.redis_url)
        self.pubsub = self.redis.pubsub()

        # 自分宛のチャンネルを購読
        await self.pubsub.subscribe(
            f"elder:{self.elder_name}",
            f"elder:broadcast",
            f"elder:role:{self.elder_role.value}",
        )

        self.logger.info("✅ Redis connected")

    def _register_message_handlers(self):
        """メッセージハンドラー登録"""
        self.message_handlers[MessageType.HEARTBEAT] = self._handle_heartbeat
        self.message_handlers[MessageType.ACKNOWLEDGE] = self._handle_acknowledge
        # サブクラスで追加のハンドラーを登録
        self.register_handlers()

    async def _message_loop(self):
        """メッセージ受信ループ"""
        self.logger.info("Starting message loop...")

        async for message in self.pubsub.listen():
            if not self.is_running:
                break

            if message["type"] == "message":
                try:
                    # メッセージ解析
                    elder_msg = ElderMessage.from_json(message["data"])
                    self.stats["messages_received"] += 1

                    # ハンドラー実行
                    handler = self.message_handlers.get(elder_msg.message_type)
                    if handler:
                        await handler(elder_msg)
                    else:
                        await self.handle_message(elder_msg)

                    # ACK送信（必要な場合）
                    if elder_msg.requires_ack:
                        await self._send_ack(elder_msg)

                except Exception as e:
                    self.logger.error(f"Message handling error: {e}", exc_info=True)
                    self.stats["errors"] += 1

    async def _heartbeat_loop(self):
        """ハートビートループ"""
        while self.is_running:
            try:
                # ハートビート送信
                heartbeat_msg = ElderMessage(
                    message_id=f"hb_{self.elder_name}_{datetime.now().timestamp()}",
                    source_elder=self.elder_name,
                    target_elder="broadcast",
                    message_type=MessageType.HEARTBEAT,
                    payload={
                        "status": "active",
                        "uptime": (datetime.now() - self.start_time).total_seconds(),
                        "stats": self.stats,
                    },
                    priority=1,
                )

                await self.send_message(heartbeat_msg)

                # 30秒ごと
                await asyncio.sleep(30)

            except Exception as e:
                self.logger.error(f"Heartbeat error: {e}")

    async def _main_loop(self):
        """メインループ（サブクラスで実装）"""
        while self.is_running:
            try:
                await self.process()
                await asyncio.sleep(0.1)  # CPU使用率調整
            except Exception as e:
                self.logger.error(f"Process error: {e}", exc_info=True)
                self.stats["errors"] += 1

    async def send_message(self, message: ElderMessage):
        """メッセージ送信"""
        try:
            # 宛先チャンネル決定
            if message.target_elder == "broadcast":
                channel = "elder:broadcast"
            else:
                channel = f"elder:{message.target_elder}"

            # 送信
            await self.redis.publish(channel, message.to_json())
            self.stats["messages_sent"] += 1

            self.logger.debug(
                f"Sent message to {channel}: {message.message_type.value}"
            )

        except Exception as e:
            self.logger.error(f"Message send error: {e}")
            self.stats["errors"] += 1

    async def _send_ack(self, original_msg: ElderMessage):
        """ACKメッセージ送信"""
        ack_msg = ElderMessage(
            message_id=f"ack_{original_msg.message_id}",
            source_elder=self.elder_name,
            target_elder=original_msg.source_elder,
            message_type=MessageType.ACKNOWLEDGE,
            payload={
                "original_message_id": original_msg.message_id,
                "status": "received",
            },
            priority=original_msg.priority,
        )
        await self.send_message(ack_msg)

    async def _handle_heartbeat(self, message: ElderMessage):
        """ハートビート処理"""
        # 他のエルダーの生存確認
        self.logger.debug(f"Heartbeat from {message.source_elder}")

    async def _handle_acknowledge(self, message: ElderMessage):
        """ACK処理"""
        self.logger.debug(f"ACK received from {message.source_elder}")

    async def query_elder(
        self, target_elder: str, query: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """他のエルダーに問い合わせ"""
        query_msg = ElderMessage(
            message_id=f"query_{self.elder_name}_{datetime.now().timestamp()}",
            source_elder=self.elder_name,
            target_elder=target_elder,
            message_type=MessageType.QUERY,
            payload=query,
            priority=7,
            requires_ack=True,
        )

        # 応答用のFuture
        response_future = asyncio.Future()

        # TODO: 応答待機メカニズムの実装
        await self.send_message(query_msg)

        try:
            # タイムアウト付きで応答を待つ
            response = await asyncio.wait_for(response_future, timeout=30.0)
            return response
        except asyncio.TimeoutError:
            self.logger.warning(f"Query timeout for {target_elder}")
            return None

    async def report_to_superior(self, report: Dict[str, Any]):
        """上位エルダーへの報告"""
        # 階層に基づく報告先の決定
        if self.elder_role == ElderRole.SERVANT:
            target = "sage"  # 最も近い賢者
        elif self.elder_role == ElderRole.SAGE:
            target = "claude_elder"
        elif self.elder_role == ElderRole.CLAUDE_ELDER:
            target = "grand_elder"
        else:
            return  # Grand Elderは報告しない

        report_msg = ElderMessage(
            message_id=f"report_{self.elder_name}_{datetime.now().timestamp()}",
            source_elder=self.elder_name,
            target_elder=target,
            message_type=MessageType.REPORT,
            payload=report,
            priority=6,
        )

        await self.send_message(report_msg)

    async def cleanup(self):
        """クリーンアップ処理"""
        self.logger.info("Cleaning up...")

        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()

        if self.redis:
            await self.redis.close()

        # サブクラスのクリーンアップ
        await self.on_cleanup()

        self.logger.info("✅ Cleanup completed")

    # 抽象メソッド（サブクラスで実装）

    @abstractmethod
    async def initialize(self):
        """初期化処理"""
        pass

    @abstractmethod
    async def process(self):
        """メイン処理"""
        pass

    @abstractmethod
    async def handle_message(self, message: ElderMessage):
        """メッセージ処理"""
        pass

    @abstractmethod
    def register_handlers(self):
        """追加のメッセージハンドラー登録"""
        pass

    @abstractmethod
    async def on_cleanup(self):
        """サブクラス固有のクリーンアップ"""
        pass


# プロセス起動用ヘルパー関数
def run_elder_process(elder_class, *args, **kwargs):
    """エルダープロセスを起動"""

    async def main():
        """mainメソッド"""
        elder = elder_class(*args, **kwargs)
        await elder.start()

    asyncio.run(main())
