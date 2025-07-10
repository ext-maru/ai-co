#!/usr/bin/env python3
"""
リアルタイムWebSocket API
4賢者システムのリアルタイム監視・通知
"""

import logging
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Blueprint
from flask import Flask
from flask import jsonify
from flask import request

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Blueprint作成
realtime_api = Blueprint("realtime_api", __name__, url_prefix="/api/realtime")


class WebSocketSimulator:
    """WebSocket機能シミュレーター（実装簡略版）"""

    def __init__(self):
        self.connections = {}  # connection_id -> connection_info
        self.subscriptions = {}  # channel -> Set[connection_id]
        self.message_queue = []
        self.is_running = True

        # バックグラウンドでメッセージ配信を実行
        self.worker_thread = threading.Thread(target=self._message_worker)
        self.worker_thread.daemon = True
        self.worker_thread.start()

    def connect(self, user_id: str, metadata: Dict[str, Any] = None) -> str:
        """新規接続確立"""
        connection_id = str(uuid.uuid4())
        self.connections[connection_id] = {
            "id": connection_id,
            "user_id": user_id,
            "connected_at": datetime.now().isoformat(),
            "metadata": metadata or {},
            "channels": set(),
        }

        logger.info(f"WebSocket接続確立: {connection_id} (user: {user_id})")
        return connection_id

    def disconnect(self, connection_id: str):
        """接続切断"""
        if connection_id in self.connections:
            # すべてのチャンネルから購読解除
            for channel in self.connections[connection_id]["channels"]:
                if channel in self.subscriptions:
                    self.subscriptions[channel].discard(connection_id)

            del self.connections[connection_id]
            logger.info(f"WebSocket接続切断: {connection_id}")

    def subscribe(self, connection_id: str, channel: str):
        """チャンネル購読"""
        if connection_id not in self.connections:
            return False

        if channel not in self.subscriptions:
            self.subscriptions[channel] = set()

        self.subscriptions[channel].add(connection_id)
        self.connections[connection_id]["channels"].add(channel)

        logger.info(f"チャンネル購読: {connection_id} -> {channel}")
        return True

    def unsubscribe(self, connection_id: str, channel: str):
        """チャンネル購読解除"""
        if connection_id in self.connections:
            self.connections[connection_id]["channels"].discard(channel)

        if channel in self.subscriptions:
            self.subscriptions[channel].discard(connection_id)

    def broadcast(self, channel: str, message: Dict[str, Any]):
        """チャンネルへのブロードキャスト"""
        if channel not in self.subscriptions:
            return 0

        sent_count = 0
        for connection_id in self.subscriptions[channel]:
            self.send_to_connection(
                connection_id, {"channel": channel, "message": message, "timestamp": datetime.now().isoformat()}
            )
            sent_count += 1

        return sent_count

    def send_to_connection(self, connection_id: str, data: Dict[str, Any]):
        """特定の接続へのメッセージ送信"""
        if connection_id in self.connections:
            self.message_queue.append(
                {"connection_id": connection_id, "data": data, "queued_at": datetime.now().isoformat()}
            )

    def _message_worker(self):
        """メッセージ配信ワーカー"""
        while self.is_running:
            if self.message_queue:
                # メッセージを処理（実際の実装では WebSocket 経由で送信）
                message = self.message_queue.pop(0)
                logger.debug(f"メッセージ配信: {message['connection_id']}")
            time.sleep(0.1)


class RealtimeMonitor:
    """リアルタイム監視システム"""

    def __init__(self, websocket: WebSocketSimulator):
        self.websocket = websocket
        self.monitors = {}
        self.is_monitoring = True

        # 監視スレッド開始
        self.monitor_thread = threading.Thread(target=self._monitor_worker)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def add_monitor(self, monitor_id: str, monitor_type: str, config: Dict[str, Any]):
        """監視項目追加"""
        self.monitors[monitor_id] = {
            "id": monitor_id,
            "type": monitor_type,
            "config": config,
            "created_at": datetime.now().isoformat(),
            "last_check": None,
            "status": "active",
        }

    def remove_monitor(self, monitor_id: str):
        """監視項目削除"""
        if monitor_id in self.monitors:
            del self.monitors[monitor_id]

    def _monitor_worker(self):
        """監視ワーカー"""
        while self.is_monitoring:
            for monitor_id, monitor in self.monitors.items():
                if monitor["status"] == "active":
                    # 監視実行（簡略版）
                    result = self._check_monitor(monitor)
                    if result:
                        # 変更があればブロードキャスト
                        self.websocket.broadcast(
                            f"monitor:{monitor['type']}",
                            {
                                "monitor_id": monitor_id,
                                "type": monitor["type"],
                                "data": result,
                                "timestamp": datetime.now().isoformat(),
                            },
                        )

                    monitor["last_check"] = datetime.now().isoformat()

            time.sleep(5)  # 5秒ごとに監視

    def _check_monitor(self, monitor: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """監視チェック実行"""
        monitor_type = monitor["type"]

        if monitor_type == "sages_health":
            # 4賢者の健全性監視
            return {
                "knowledge_sage": {"health": 95, "status": "active"},
                "task_sage": {"health": 92, "status": "active"},
                "incident_sage": {"health": 98, "status": "active"},
                "rag_sage": {"health": 94, "status": "active"},
            }

        elif monitor_type == "system_performance":
            # システムパフォーマンス監視
            import psutil

            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage("/").percent,
            }

        elif monitor_type == "task_queue":
            # タスクキュー監視
            return {"pending": 5, "active": 2, "completed": 150, "failed": 1}

        return None


class CollaborationSessionManager:
    """協調セッション管理"""

    def __init__(self, websocket: WebSocketSimulator):
        self.websocket = websocket
        self.sessions = {}

    def create_session(self, session_type: str, participants: List[str], objective: str) -> str:
        """協調セッション作成"""
        session_id = f"session_{uuid.uuid4().hex[:8]}"

        session = {
            "id": session_id,
            "type": session_type,
            "participants": participants,
            "objective": objective,
            "status": "planning",
            "created_at": datetime.now().isoformat(),
            "messages": [],
            "consensus": None,
        }

        self.sessions[session_id] = session

        # セッション作成通知
        self.websocket.broadcast(f"session:{session_id}", {"event": "session_created", "session": session})

        return session_id

    def update_session_status(self, session_id: str, status: str):
        """セッション状態更新"""
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = status

            # 状態更新通知
            self.websocket.broadcast(
                f"session:{session_id}", {"event": "status_updated", "session_id": session_id, "new_status": status}
            )

    def add_message(self, session_id: str, sage: str, message: str):
        """セッションメッセージ追加"""
        if session_id in self.sessions:
            msg = {"id": str(uuid.uuid4()), "sage": sage, "message": message, "timestamp": datetime.now().isoformat()}

            self.sessions[session_id]["messages"].append(msg)

            # メッセージ通知
            self.websocket.broadcast(
                f"session:{session_id}", {"event": "message_added", "session_id": session_id, "message": msg}
            )

    def submit_consensus(self, session_id: str, proposal: str, votes: Dict[str, bool]):
        """コンセンサス提出"""
        if session_id in self.sessions:
            consensus = {
                "proposal": proposal,
                "votes": votes,
                "timestamp": datetime.now().isoformat(),
                "approved": all(votes.values()),
            }

            self.sessions[session_id]["consensus"] = consensus

            # コンセンサス通知
            self.websocket.broadcast(
                f"session:{session_id}",
                {"event": "consensus_reached", "session_id": session_id, "consensus": consensus},
            )


class LiveNotificationSystem:
    """ライブ通知システム"""

    def __init__(self, websocket: WebSocketSimulator):
        self.websocket = websocket
        self.notification_queue = []

    def send_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        priority: str = "normal",
        data: Dict[str, Any] = None,
    ):
        """通知送信"""
        notification = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": notification_type,
            "title": title,
            "message": message,
            "priority": priority,
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
            "read": False,
        }

        # ユーザーチャンネルへ通知
        self.websocket.broadcast(f"user:{user_id}", {"event": "notification", "notification": notification})

        # 通知履歴に追加
        self.notification_queue.append(notification)

        return notification["id"]

    def broadcast_announcement(self, title: str, message: str, channels: List[str] = None):
        """全体アナウンス"""
        announcement = {
            "id": str(uuid.uuid4()),
            "type": "announcement",
            "title": title,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }

        if channels:
            for channel in channels:
                self.websocket.broadcast(channel, {"event": "announcement", "announcement": announcement})
        else:
            # 全接続にブロードキャスト
            self.websocket.broadcast("global", {"event": "announcement", "announcement": announcement})


# グローバルインスタンス
websocket_sim = WebSocketSimulator()
realtime_monitor = RealtimeMonitor(websocket_sim)
session_manager = CollaborationSessionManager(websocket_sim)
notification_system = LiveNotificationSystem(websocket_sim)

# API エンドポイント


@realtime_api.route("/connect", methods=["POST"])
def websocket_connect():
    """WebSocket接続確立（シミュレート）"""
    try:
        data = request.json
        user_id = data.get("user_id", "anonymous")
        metadata = data.get("metadata", {})

        connection_id = websocket_sim.connect(user_id, metadata)

        # デフォルトチャンネルに購読
        websocket_sim.subscribe(connection_id, "global")
        websocket_sim.subscribe(connection_id, f"user:{user_id}")

        return jsonify({"success": True, "connection_id": connection_id, "channels": ["global", f"user:{user_id}"]})

    except Exception as e:
        logger.error(f"WebSocket接続エラー: {e}")
        return jsonify({"error": str(e)}), 500


@realtime_api.route("/disconnect", methods=["POST"])
def websocket_disconnect():
    """WebSocket切断"""
    try:
        data = request.json
        connection_id = data.get("connection_id")

        if not connection_id:
            return jsonify({"error": "connection_id required"}), 400

        websocket_sim.disconnect(connection_id)

        return jsonify({"success": True})

    except Exception as e:
        logger.error(f"WebSocket切断エラー: {e}")
        return jsonify({"error": str(e)}), 500


@realtime_api.route("/subscribe", methods=["POST"])
def subscribe_channel():
    """チャンネル購読"""
    try:
        data = request.json
        connection_id = data.get("connection_id")
        channel = data.get("channel")

        if not all([connection_id, channel]):
            return jsonify({"error": "connection_id and channel required"}), 400

        success = websocket_sim.subscribe(connection_id, channel)

        return jsonify({"success": success, "channel": channel})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@realtime_api.route("/monitors", methods=["POST"])
def add_monitor():
    """監視項目追加"""
    try:
        data = request.json
        monitor_type = data.get("type")
        config = data.get("config", {})

        if not monitor_type:
            return jsonify({"error": "monitor type required"}), 400

        monitor_id = f"mon_{uuid.uuid4().hex[:8]}"
        realtime_monitor.add_monitor(monitor_id, monitor_type, config)

        return jsonify({"success": True, "monitor_id": monitor_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@realtime_api.route("/sessions", methods=["POST"])
def create_collaboration_session():
    """協調セッション作成"""
    try:
        data = request.json
        session_type = data.get("type", "general")
        participants = data.get("participants", [])
        objective = data.get("objective", "")

        session_id = session_manager.create_session(session_type, participants, objective)

        return jsonify({"success": True, "session_id": session_id, "session": session_manager.sessions[session_id]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@realtime_api.route("/sessions/<session_id>/message", methods=["POST"])
def add_session_message(session_id):
    """セッションメッセージ追加"""
    try:
        data = request.json
        sage = data.get("sage")
        message = data.get("message")

        if not all([sage, message]):
            return jsonify({"error": "sage and message required"}), 400

        session_manager.add_message(session_id, sage, message)

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@realtime_api.route("/notify", methods=["POST"])
def send_notification():
    """通知送信"""
    try:
        data = request.json
        user_id = data.get("user_id")
        notification_type = data.get("type", "info")
        title = data.get("title")
        message = data.get("message")
        priority = data.get("priority", "normal")

        if not all([user_id, title, message]):
            return jsonify({"error": "user_id, title, and message required"}), 400

        notification_id = notification_system.send_notification(
            user_id, notification_type, title, message, priority, data.get("data")
        )

        return jsonify({"success": True, "notification_id": notification_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@realtime_api.route("/announce", methods=["POST"])
def broadcast_announcement():
    """全体アナウンス"""
    try:
        data = request.json
        title = data.get("title")
        message = data.get("message")
        channels = data.get("channels")

        if not all([title, message]):
            return jsonify({"error": "title and message required"}), 400

        notification_system.broadcast_announcement(title, message, channels)

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # テスト用実行
    app = Flask(__name__)
    app.register_blueprint(realtime_api)

    print("=== リアルタイムWebSocket API ===")
    print("監視タイプ:")
    print("- sages_health: 4賢者健全性")
    print("- system_performance: システムパフォーマンス")
    print("- task_queue: タスクキュー状態")

    app.run(debug=True, port=5004)
