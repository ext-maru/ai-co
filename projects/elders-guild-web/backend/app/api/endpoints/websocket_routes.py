"""
WebSocket Routes for Real-time Four Sages Communication
"""

import json
from typing import Optional
from uuid import uuid4

import structlog
from app.websocket.manager import websocket_manager
from fastapi import APIRouter
from fastapi import Query
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

logger = structlog.get_logger()
router = APIRouter()


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    sage_type: Optional[str] = Query(None, description="Type of sage: knowledge, task, incident, search"),
    user_id: Optional[str] = Query(None, description="User identifier"),
    elder_council_session: Optional[str] = Query(None, description="Elder Council session ID"),
):
    """
    Main WebSocket endpoint for Four Sages real-time communication.
    """
    connection_id = str(uuid4())

    try:
        # Connect to WebSocket manager
        await websocket_manager.connect(
            websocket=websocket,
            connection_id=connection_id,
            user_id=user_id,
            sage_type=sage_type,
            elder_council_session=elder_council_session,
        )

        logger.info(
            "WebSocket client connected",
            connection_id=connection_id,
            sage_type=sage_type,
            user_id=user_id,
            elder_council_session=elder_council_session,
        )

        # Main message loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle different message types
                message_type = message.get("type", "unknown")

                if message_type == "heartbeat":
                    # Handle heartbeat
                    await websocket_manager.handle_heartbeat(connection_id)
                    await websocket.send_json(
                        {
                            "type": "heartbeat_ack",
                            "timestamp": message.get("timestamp"),
                        }
                    )

                elif message_type == "sage_message":
                    # Handle sage-to-sage communication
                    content = message.get("content", {})
                    target_sage = message.get("target_sage")

                    from app.websocket.manager import SageMessage

                    sage_message = SageMessage(
                        message_id=str(uuid4()),
                        sage_type=sage_type or "unknown",
                        message_type="request",
                        content=content,
                        target_sage=target_sage,
                        elder_council_session=elder_council_session,
                        timestamp=0,
                    )

                    await websocket_manager.send_sage_message(sage_message)

                    logger.info(
                        "Sage message sent",
                        connection_id=connection_id,
                        source_sage=sage_type,
                        target_sage=target_sage,
                        message_content=content,
                    )

                elif message_type == "council_message":
                    # Handle Elder Council messages
                    if elder_council_session:
                        content = message.get("content", "")
                        sender = message.get("sender", user_id or "Unknown")

                        council_message = {
                            "type": "council_message",
                            "session_id": elder_council_session,
                            "sender": sender,
                            "content": content,
                            "timestamp": message.get("timestamp"),
                        }

                        await websocket_manager.broadcast_to_elder_council(elder_council_session, council_message)

                        logger.info(
                            "Council message sent",
                            connection_id=connection_id,
                            session_id=elder_council_session,
                            sender=sender,
                        )

                elif message_type == "status_update":
                    # Handle status updates
                    content = message.get("content", {})

                    from app.websocket.manager import SageMessage

                    status_message = SageMessage(
                        message_id=str(uuid4()),
                        sage_type=sage_type or "unknown",
                        message_type="status_update",
                        content=content,
                        elder_council_session=elder_council_session,
                        timestamp=0,
                    )

                    await websocket_manager.send_sage_message(status_message)

                    logger.info(
                        "Status update sent",
                        connection_id=connection_id,
                        sage_type=sage_type,
                        content=content,
                    )

                elif message_type == "join_session":
                    # Join an Elder Council session
                    session_id = message.get("session_id")
                    if session_id:
                        # Update connection info
                        if connection_id in websocket_manager.connection_info:
                            websocket_manager.connection_info[connection_id].elder_council_session = session_id

                        # Add to session
                        if session_id not in websocket_manager.elder_council_sessions:
                            websocket_manager.elder_council_sessions[session_id] = set()
                        websocket_manager.elder_council_sessions[session_id].add(connection_id)

                        await websocket.send_json(
                            {
                                "type": "session_joined",
                                "session_id": session_id,
                            }
                        )

                        logger.info(
                            "Client joined council session",
                            connection_id=connection_id,
                            session_id=session_id,
                        )

                elif message_type == "leave_session":
                    # Leave an Elder Council session
                    session_id = message.get("session_id")
                    if session_id and session_id in websocket_manager.elder_council_sessions:
                        websocket_manager.elder_council_sessions[session_id].discard(connection_id)

                        # Update connection info
                        if connection_id in websocket_manager.connection_info:
                            websocket_manager.connection_info[connection_id].elder_council_session = None

                        await websocket.send_json(
                            {
                                "type": "session_left",
                                "session_id": session_id,
                            }
                        )

                        logger.info(
                            "Client left council session",
                            connection_id=connection_id,
                            session_id=session_id,
                        )

                else:
                    # Unknown message type
                    logger.warning(
                        "Unknown message type received",
                        connection_id=connection_id,
                        message_type=message_type,
                    )

                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": f"Unknown message type: {message_type}",
                        }
                    )

            except json.JSONDecodeError as e:
                logger.error(
                    "Invalid JSON received",
                    connection_id=connection_id,
                    error=str(e),
                )
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "Invalid JSON format",
                    }
                )

            except Exception as e:
                logger.error(
                    "Error processing message",
                    connection_id=connection_id,
                    error=str(e),
                )
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "Error processing message",
                    }
                )

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected", connection_id=connection_id)

    except Exception as e:
        logger.error(
            "WebSocket error",
            connection_id=connection_id,
            error=str(e),
        )

    finally:
        # Clean up connection
        await websocket_manager.disconnect(connection_id)


@router.websocket("/sage/{sage_type}")
async def sage_websocket_endpoint(
    websocket: WebSocket,
    sage_type: str,
    user_id: Optional[str] = Query(None, description="User identifier"),
):
    """
    Dedicated WebSocket endpoint for specific sage types.
    """
    if sage_type not in ["knowledge", "task", "incident", "search"]:
        await websocket.close(code=1008, reason="Invalid sage type")
        return

    await websocket_endpoint(
        websocket=websocket,
        sage_type=sage_type,
        user_id=user_id,
    )


@router.websocket("/council/{session_id}")
async def council_websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    user_id: Optional[str] = Query(None, description="User identifier"),
):
    """
    Dedicated WebSocket endpoint for Elder Council sessions.
    """
    await websocket_endpoint(
        websocket=websocket,
        user_id=user_id,
        elder_council_session=session_id,
    )


@router.get("/connections")
async def get_websocket_connections():
    """
    Get current WebSocket connection statistics.
    """
    try:
        stats = websocket_manager.get_stats()

        # Add detailed connection info
        detailed_stats = {
            **stats,
            "connections": [
                {
                    "connection_id": conn_id,
                    "user_id": info.user_id,
                    "sage_type": info.sage_type,
                    "elder_council_session": info.elder_council_session,
                    "connected_at": info.connected_at,
                    "last_heartbeat": info.last_heartbeat,
                }
                for conn_id, info in websocket_manager.connection_info.items()
            ],
        }

        return {
            "success": True,
            "data": detailed_stats,
            "message": "WebSocket connection stats retrieved",
        }

    except Exception as e:
        logger.error("Error retrieving connection stats", error=str(e))
        return {
            "success": False,
            "error": "Failed to retrieve connection stats",
        }


@router.post("/broadcast/{sage_type}")
async def broadcast_to_sage(sage_type: str, message: dict):
    """
    Broadcast a message to all connections of a specific sage type.
    """
    try:
        if sage_type not in ["knowledge", "task", "incident", "search"]:
            raise HTTPException(status_code=400, detail="Invalid sage type")

        await websocket_manager.broadcast_to_sage(sage_type, message)

        connection_count = len(websocket_manager.sage_connections.get(sage_type, set()))

        return {
            "success": True,
            "message": f"Message broadcast to {connection_count} {sage_type} sage connections",
        }

    except Exception as e:
        logger.error("Error broadcasting message", error=str(e))
        return {
            "success": False,
            "error": "Failed to broadcast message",
        }


@router.post("/broadcast/council/{session_id}")
async def broadcast_to_council_session(session_id: str, message: dict):
    """
    Broadcast a message to all connections in an Elder Council session.
    """
    try:
        if session_id not in websocket_manager.elder_council_sessions:
            raise HTTPException(status_code=404, detail="Session not found")

        await websocket_manager.broadcast_to_elder_council(session_id, message)

        connection_count = len(websocket_manager.elder_council_sessions.get(session_id, set()))

        return {
            "success": True,
            "message": f"Message broadcast to {connection_count} council session connections",
        }

    except Exception as e:
        logger.error("Error broadcasting to council", error=str(e))
        return {
            "success": False,
            "error": "Failed to broadcast to council session",
        }
