"""
WebSocket Manager for Elders Guild Web - Four Sages Real-time Communication
"""

import asyncio
from typing import Dict
from typing import Optional
from typing import Set

import structlog
from app.core.config import settings
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from pydantic import BaseModel

logger = structlog.get_logger()


class ConnectionInfo(BaseModel):
    """WebSocket connection information."""

    connection_id: str
    user_id: Optional[str] = None
    sage_type: Optional[str] = None  # knowledge, task, incident, search
    elder_council_session: Optional[str] = None
    connected_at: float
    last_heartbeat: float


class SageMessage(BaseModel):
    """Message structure for Four Sages communication."""

    message_id: str
    sage_type: str  # knowledge, task, incident, search
    message_type: str  # status_update, request, response, broadcast
    content: dict
    target_sage: Optional[str] = None
    elder_council_session: Optional[str] = None
    timestamp: float


class WebSocketManager:
    """
    Manages WebSocket connections for the Four Sages system.
    Handles real-time communication between sages and Elder Council sessions.
    """

    def __init__(self):
        # Active WebSocket connections
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_info: Dict[str, ConnectionInfo] = {}

        # Sage-specific connections
        self.sage_connections: Dict[str, Set[str]] = {
            "knowledge": set(),
            "task": set(),
            "incident": set(),
            "search": set(),
        }

        # Elder Council sessions
        self.elder_council_sessions: Dict[str, Set[str]] = {}

        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None

    async def startup(self):
        """Initialize WebSocket manager."""
        logger.info("Starting WebSocket manager")
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def shutdown(self):
        """Shutdown WebSocket manager."""
        logger.info("Shutting down WebSocket manager")

        # Cancel background tasks
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()

        # Close all connections
        for connection_id in list(self.active_connections.keys()):
            await self.disconnect(connection_id)

    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        user_id: Optional[str] = None,
        sage_type: Optional[str] = None,
        elder_council_session: Optional[str] = None,
    ) -> str:
        """
        Accept a new WebSocket connection.
        """
        await websocket.accept()

        # Store connection
        self.active_connections[connection_id] = websocket

        # Create connection info
        import time

        now = time.time()
        self.connection_info[connection_id] = ConnectionInfo(
            connection_id=connection_id,
            user_id=user_id,
            sage_type=sage_type,
            elder_council_session=elder_council_session,
            connected_at=now,
            last_heartbeat=now,
        )

        # Register with appropriate sage
        if sage_type and sage_type in self.sage_connections:
            self.sage_connections[sage_type].add(connection_id)

        # Join Elder Council session
        if elder_council_session:
            if elder_council_session not in self.elder_council_sessions:
                self.elder_council_sessions[elder_council_session] = set()
            self.elder_council_sessions[elder_council_session].add(connection_id)

        logger.info(
            "WebSocket connected",
            connection_id=connection_id,
            user_id=user_id,
            sage_type=sage_type,
            elder_council_session=elder_council_session,
        )

        # Send welcome message
        await self.send_personal_message(
            connection_id,
            {
                "type": "connection_established",
                "connection_id": connection_id,
                "sage_type": sage_type,
                "elder_council_session": elder_council_session,
                "timestamp": now,
            },
        )

        return connection_id

    async def disconnect(self, connection_id: str):
        """
        Disconnect a WebSocket connection.
        """
        if connection_id not in self.active_connections:
            return

        connection_info = self.connection_info.get(connection_id)

        # Remove from sage connections
        if connection_info and connection_info.sage_type:
            sage_type = connection_info.sage_type
            if sage_type in self.sage_connections:
                self.sage_connections[sage_type].discard(connection_id)

        # Remove from Elder Council session
        if connection_info and connection_info.elder_council_session:
            session_id = connection_info.elder_council_session
            if session_id in self.elder_council_sessions:
                self.elder_council_sessions[session_id].discard(connection_id)
                # Clean up empty sessions
                if not self.elder_council_sessions[session_id]:
                    del self.elder_council_sessions[session_id]

        # Close connection
        websocket = self.active_connections[connection_id]
        try:
            await websocket.close()
        except Exception as e:
            logger.warning("Error closing WebSocket", error=str(e))

        # Clean up
        del self.active_connections[connection_id]
        if connection_id in self.connection_info:
            del self.connection_info[connection_id]

        logger.info(
            "WebSocket disconnected",
            connection_id=connection_id,
            user_id=connection_info.user_id if connection_info else None,
        )

    async def send_personal_message(self, connection_id: str, message: dict):
        """
        Send a message to a specific connection.
        """
        if connection_id not in self.active_connections:
            logger.warning("Connection not found", connection_id=connection_id)
            return

        websocket = self.active_connections[connection_id]
        try:
            await websocket.send_json(message)
        except WebSocketDisconnect:
            await self.disconnect(connection_id)
        except Exception as e:
            logger.error(
                "Error sending message",
                connection_id=connection_id,
                error=str(e),
            )
            await self.disconnect(connection_id)

    async def broadcast_to_sage(self, sage_type: str, message: dict):
        """
        Broadcast a message to all connections of a specific sage type.
        """
        if sage_type not in self.sage_connections:
            logger.warning("Invalid sage type", sage_type=sage_type)
            return

        connections = self.sage_connections[sage_type].copy()
        logger.info(
            "Broadcasting to sage",
            sage_type=sage_type,
            connection_count=len(connections),
        )

        for connection_id in connections:
            await self.send_personal_message(connection_id, message)

    async def broadcast_to_elder_council(self, session_id: str, message: dict):
        """
        Broadcast a message to all connections in an Elder Council session.
        """
        if session_id not in self.elder_council_sessions:
            logger.warning("Elder Council session not found", session_id=session_id)
            return

        connections = self.elder_council_sessions[session_id].copy()
        logger.info(
            "Broadcasting to Elder Council",
            session_id=session_id,
            connection_count=len(connections),
        )

        for connection_id in connections:
            await self.send_personal_message(connection_id, message)

    async def send_sage_message(self, message: SageMessage):
        """
        Send a message from one sage to another or broadcast.
        """
        message_dict = message.dict()

        if message.target_sage:
            # Send to specific sage
            await self.broadcast_to_sage(message.target_sage, message_dict)
        elif message.elder_council_session:
            # Send to Elder Council session
            await self.broadcast_to_elder_council(message.elder_council_session, message_dict)
        else:
            # Broadcast to all sages
            for sage_type in self.sage_connections:
                await self.broadcast_to_sage(sage_type, message_dict)

    async def handle_heartbeat(self, connection_id: str):
        """
        Handle heartbeat from a connection.
        """
        if connection_id in self.connection_info:
            import time

            self.connection_info[connection_id].last_heartbeat = time.time()

    async def _heartbeat_loop(self):
        """
        Send periodic heartbeat to all connections.
        """
        while True:
            try:
                await asyncio.sleep(settings.WEBSOCKET_HEARTBEAT_INTERVAL)

                import time

                now = time.time()
                heartbeat_message = {
                    "type": "heartbeat",
                    "timestamp": now,
                }

                for connection_id in list(self.active_connections.keys()):
                    await self.send_personal_message(connection_id, heartbeat_message)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in heartbeat loop", error=str(e))

    async def _cleanup_loop(self):
        """
        Clean up stale connections.
        """
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                import time

                now = time.time()
                stale_connections = []

                for connection_id, info in self.connection_info.items():
                    # Consider connection stale if no heartbeat for 2 intervals
                    if now - info.last_heartbeat > (settings.WEBSOCKET_HEARTBEAT_INTERVAL * 2):
                        stale_connections.append(connection_id)

                for connection_id in stale_connections:
                    logger.info("Cleaning up stale connection", connection_id=connection_id)
                    await self.disconnect(connection_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in cleanup loop", error=str(e))

    def get_stats(self) -> dict:
        """
        Get WebSocket connection statistics.
        """
        return {
            "total_connections": len(self.active_connections),
            "sage_connections": {
                sage_type: len(connections) for sage_type, connections in self.sage_connections.items()
            },
            "elder_council_sessions": len(self.elder_council_sessions),
            "elder_council_connections": {
                session_id: len(connections) for session_id, connections in self.elder_council_sessions.items()
            },
        }


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
