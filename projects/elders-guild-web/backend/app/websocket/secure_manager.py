import asyncio
import json
import time
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Dict
from typing import Optional
from typing import Set

import redis
from fastapi import HTTPException
from fastapi import status
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from ..core.config import settings
from ..core.security import security_manager
from ..models.auth import PermissionType
from ..models.auth import User
from ..models.auth import UserRole


class SecureWebSocketManager:
    """Secure WebSocket manager with authentication and rate limiting"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        # Active connections
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[int, Set[str]] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}

        # Security
        self.redis_client = redis_client or redis.from_url(settings.REDIS_URL)
        self.max_connections_per_user = 5
        self.heartbeat_interval = settings.WS_HEARTBEAT_INTERVAL
        self.message_rate_limit = 10  # messages per minute

        # Elder Council specific
        self.council_connections: Set[str] = set()
        self.sage_connections: Dict[str, Set[str]] = {
            "incident": set(),
            "knowledge": set(),
            "search": set(),
            "task": set(),
        }

        # Background tasks
        self.heartbeat_task = None
        self.cleanup_task = None

    async def authenticate_websocket(self, websocket: WebSocket, token: str) -> Optional[User]:
        """Authenticate WebSocket connection"""
        try:
            # Verify JWT token
            payload = security_manager.verify_token(token)
            if not payload:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return None

            # Get user from database
            user_id = int(payload.get("sub"))

            # Note: In a real implementation, you'd want to inject the database session
            # For now, we'll create a new session
            from ..core.database import SessionLocal

            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if not user or not user.is_active:
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                    return None

                # Check WebSocket permission
                if not user.has_permission(PermissionType.WEBSOCKET_ACCESS):
                    await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
                    return None

                return user
            finally:
                db.close()

        except Exception as e:
            print(f"WebSocket authentication error: {e}")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            return None

    async def connect(self, websocket: WebSocket, user: User, connection_type: str = "general") -> str:
        """Connect user to WebSocket"""
        await websocket.accept()

        # Generate connection ID
        connection_id = f"{user.id}_{int(time.time() * 1000)}"

        # Check connection limits
        user_conn_count = len(self.user_connections.get(user.id, set()))
        if user_conn_count >= self.max_connections_per_user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many WebSocket connections")

        # Store connection
        self.active_connections[connection_id] = websocket

        if user.id not in self.user_connections:
            self.user_connections[user.id] = set()
        self.user_connections[user.id].add(connection_id)

        # Store metadata
        self.connection_metadata[connection_id] = {
            "user_id": user.id,
            "user_role": user.role.value,
            "connection_type": connection_type,
            "connected_at": datetime.utcnow(),
            "last_heartbeat": datetime.utcnow(),
            "message_count": 0,
            "rate_limit_reset": datetime.utcnow() + timedelta(minutes=1),
        }

        # Add to specific connection sets
        if connection_type == "elder_council" and user.has_permission(PermissionType.ELDER_COUNCIL):
            self.council_connections.add(connection_id)
        elif connection_type in self.sage_connections and user.role in [
            UserRole.SAGE,
            UserRole.ELDER,
            UserRole.GRAND_ELDER,
        ]:
            self.sage_connections[connection_type].add(connection_id)

        # Start background tasks if not running
        if not self.heartbeat_task:
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        if not self.cleanup_task:
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())

        # Send welcome message
        await self.send_personal_message(
            {
                "type": "connection",
                "status": "connected",
                "connection_id": connection_id,
                "user_role": user.role.value,
                "permissions": [perm.value for perm in PermissionType if user.has_permission(perm)],
            },
            connection_id,
        )

        return connection_id

    async def disconnect(self, connection_id: str):
        """Disconnect WebSocket"""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]

            # Remove from collections
            del self.active_connections[connection_id]

            # Remove from user connections
            metadata = self.connection_metadata.get(connection_id, {})
            user_id = metadata.get("user_id")
            if user_id and user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]

            # Remove from specific sets
            self.council_connections.discard(connection_id)
            for sage_type in self.sage_connections:
                self.sage_connections[sage_type].discard(connection_id)

            # Clean metadata
            if connection_id in self.connection_metadata:
                del self.connection_metadata[connection_id]

            try:
                await websocket.close()
            except:
                pass

    async def send_personal_message(self, message: dict, connection_id: str):
        """Send message to specific connection"""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message))

                # Update message count for rate limiting
                if connection_id in self.connection_metadata:
                    self.connection_metadata[connection_id]["message_count"] += 1

            except WebSocketDisconnect:
                await self.disconnect(connection_id)
            except Exception as e:
                print(f"Error sending WebSocket message: {e}")
                await self.disconnect(connection_id)

    async def send_to_user(self, message: dict, user_id: int):
        """Send message to all connections of a user"""
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id].copy():
                await self.send_personal_message(message, connection_id)

    async def send_to_role(self, message: dict, role: UserRole):
        """Send message to all users with specific role"""
        for connection_id, metadata in self.connection_metadata.items():
            if metadata.get("user_role") == role.value:
                await self.send_personal_message(message, connection_id)

    async def broadcast_to_elder_council(self, message: dict):
        """Broadcast message to Elder Council members"""
        for connection_id in self.council_connections.copy():
            await self.send_personal_message(message, connection_id)

    async def broadcast_to_sage_type(self, message: dict, sage_type: str):
        """Broadcast message to specific sage type"""
        if sage_type in self.sage_connections:
            for connection_id in self.sage_connections[sage_type].copy():
                await self.send_personal_message(message, connection_id)

    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected users"""
        for connection_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, connection_id)

    async def handle_message(self, connection_id: str, data: str) -> bool:
        """Handle incoming WebSocket message with rate limiting"""
        # Check rate limit
        if not await self._check_message_rate_limit(connection_id):
            await self.send_personal_message({"type": "error", "message": "Rate limit exceeded"}, connection_id)
            return False

        try:
            message = json.loads(data)
            message_type = message.get("type")

            # Handle different message types
            if message_type == "heartbeat":
                await self._handle_heartbeat(connection_id)
            elif message_type == "sage_update":
                await self._handle_sage_update(connection_id, message)
            elif message_type == "elder_council":
                await self._handle_elder_council_message(connection_id, message)
            elif message_type == "chat":
                await self._handle_chat_message(connection_id, message)
            else:
                await self.send_personal_message(
                    {"type": "error", "message": f"Unknown message type: {message_type}"}, connection_id
                )

            return True

        except json.JSONDecodeError:
            await self.send_personal_message({"type": "error", "message": "Invalid JSON format"}, connection_id)
            return False
        except Exception as e:
            print(f"Error handling WebSocket message: {e}")
            await self.send_personal_message({"type": "error", "message": "Internal server error"}, connection_id)
            return False

    async def _check_message_rate_limit(self, connection_id: str) -> bool:
        """Check message rate limit for connection"""
        metadata = self.connection_metadata.get(connection_id, {})
        now = datetime.utcnow()

        # Reset counter if needed
        if now > metadata.get("rate_limit_reset", now):
            metadata["message_count"] = 0
            metadata["rate_limit_reset"] = now + timedelta(minutes=1)

        return metadata.get("message_count", 0) < self.message_rate_limit

    async def _handle_heartbeat(self, connection_id: str):
        """Handle heartbeat message"""
        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]["last_heartbeat"] = datetime.utcnow()

        await self.send_personal_message(
            {"type": "heartbeat_ack", "timestamp": datetime.utcnow().isoformat()}, connection_id
        )

    async def _handle_sage_update(self, connection_id: str, message: dict):
        """Handle sage status update"""
        sage_type = message.get("sage_type")
        status = message.get("status")

        if sage_type and status:
            # Broadcast to relevant sage connections
            await self.broadcast_to_sage_type(
                {
                    "type": "sage_status_update",
                    "sage_type": sage_type,
                    "status": status,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                sage_type,
            )

    async def _handle_elder_council_message(self, connection_id: str, message: dict):
        """Handle Elder Council message"""
        metadata = self.connection_metadata.get(connection_id, {})

        # Check if user has Elder Council permission
        if connection_id not in self.council_connections:
            await self.send_personal_message(
                {"type": "error", "message": "Insufficient permissions for Elder Council"}, connection_id
            )
            return

        # Broadcast to Elder Council
        await self.broadcast_to_elder_council(
            {
                "type": "elder_council_message",
                "message": message.get("content"),
                "sender": metadata.get("user_id"),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    async def _handle_chat_message(self, connection_id: str, message: dict):
        """Handle chat message"""
        metadata = self.connection_metadata.get(connection_id, {})

        chat_message = {
            "type": "chat_message",
            "content": message.get("content"),
            "sender": metadata.get("user_id"),
            "sender_role": metadata.get("user_role"),
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Broadcast to all connections
        await self.broadcast_to_all(chat_message)

    async def _heartbeat_loop(self):
        """Background heartbeat monitoring"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                now = datetime.utcnow()
                timeout_threshold = now - timedelta(seconds=self.heartbeat_interval * 2)

                # Check for stale connections
                stale_connections = []
                for connection_id, metadata in self.connection_metadata.items():
                    last_heartbeat = metadata.get("last_heartbeat")
                    if last_heartbeat and last_heartbeat < timeout_threshold:
                        stale_connections.append(connection_id)

                # Disconnect stale connections
                for connection_id in stale_connections:
                    await self.disconnect(connection_id)

            except Exception as e:
                print(f"Heartbeat loop error: {e}")

    async def _cleanup_loop(self):
        """Background cleanup task"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                # Clean up disconnected connections
                disconnected = []
                for connection_id, websocket in self.active_connections.items():
                    if websocket.client_state.name != "CONNECTED":
                        disconnected.append(connection_id)

                for connection_id in disconnected:
                    await self.disconnect(connection_id)

            except Exception as e:
                print(f"Cleanup loop error: {e}")

    def get_connection_stats(self) -> dict:
        """Get connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "users_connected": len(self.user_connections),
            "elder_council_connections": len(self.council_connections),
            "sage_connections": {
                sage_type: len(connections) for sage_type, connections in self.sage_connections.items()
            },
            "role_distribution": self._get_role_distribution(),
        }

    def _get_role_distribution(self) -> dict:
        """Get distribution of connected users by role"""
        roles = {}
        for metadata in self.connection_metadata.values():
            role = metadata.get("user_role", "unknown")
            roles[role] = roles.get(role, 0) + 1
        return roles


# Global WebSocket manager instance
websocket_manager = SecureWebSocketManager()
