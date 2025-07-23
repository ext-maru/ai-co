"""ワーカー間通信システム"""

import json
from typing import Any, Dict, Optional


class CommunicationMixin:
    """ワーカー間通信のMixin"""

    def __init__(self):
        """初期化メソッド"""
        self.communication_routes = {}

    def register_route(self, target_worker: str, message_type: str):
        """通信ルートを登録"""
        if target_worker not in self.communication_routes:
            self.communication_routes[target_worker] = []
        self.communication_routes[target_worker].append(message_type)

    def send_to_worker(
        self,
        target_worker: str,
        message_type: str,
        data: Dict[str, Any],
        priority: str = "normal",
    ):
        """他のワーカーにメッセージを送信"""
        message = {
            "type": message_type,
            "data": data,
            "priority": priority,
            "from": getattr(self, "worker_type", "unknown"),
            "timestamp": datetime.now().isoformat(),
        }

        # 実際の送信処理（キューを使用）
        if hasattr(self, "channel") and self.channel:
            target_queue = f"ai_{target_worker}"
            self.channel.basic_publish(
                exchange="", routing_key=target_queue, body=json.dumps(message)
            )
            return True
        return False

    def handle_worker_message(self, message: Dict[str, Any]):
        """他のワーカーからのメッセージを処理"""
        # サブクラスで実装
        pass


from datetime import datetime


class WorkerCommunicationMixin:
    """Mixin for worker communication"""

    def __init__(self):
        """初期化メソッド"""
        self.communication_enabled = True

    def send_message(self, target_worker, message):
        """Send message to another worker"""
        pass


__all__ = ["WorkerCommunicationMixin"]
