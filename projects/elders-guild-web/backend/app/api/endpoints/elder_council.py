"""
Elder Council API Endpoints
Manages coordination between the Four Sages
"""

from typing import List, Optional
from uuid import uuid4

import structlog
from fastapi import APIRouter, HTTPException, Query

from app.schemas.sages import (
    ElderCouncilSession,
    ElderCouncilMessage,
    ElderCouncilResponse,
)
from app.websocket.manager import SageMessage, websocket_manager

logger = structlog.get_logger()
router = APIRouter()

# In-memory storage for demonstration (replace with database in production)
council_sessions: dict[str, ElderCouncilSession] = {}
council_messages: dict[str, List[ElderCouncilMessage]] = {}


@router.get("/sessions", response_model=ElderCouncilResponse)
async def get_council_sessions(
    status: Optional[str] = Query(None, description="Filter by session status"),
    limit: int = Query(10, ge=1, le=100, description="Number of sessions to return"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip"),
):
    """
    Get all Elder Council sessions.
    """
    try:
        sessions = list(council_sessions.values())
        
        # Apply filters
        if status:
            sessions = [s for s in sessions if s.status == status]
        
        # Sort by creation date
        sessions.sort(key=lambda s: s.created_at or s.updated_at, reverse=True)
        
        # Pagination
        total_count = len(sessions)
        sessions = sessions[offset:offset + limit]
        
        return ElderCouncilResponse(
            data=sessions,
            message=f"Retrieved {len(sessions)} council sessions",
        )
        
    except Exception as e:
        logger.error("Error retrieving council sessions", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve sessions")


@router.post("/sessions", response_model=ElderCouncilResponse)
async def create_council_session(session: ElderCouncilSession):
    """
    Create a new Elder Council session.
    """
    try:
        # Generate session ID
        session_id = str(uuid4())
        
        # Create session
        new_session = ElderCouncilSession(
            session_id=session_id,
            **session.dict(exclude={"session_id"}),
        )
        
        # Store session
        council_sessions[session_id] = new_session
        council_messages[session_id] = []
        
        # Broadcast session creation
        await websocket_manager.send_sage_message(
            SageMessage(
                message_id=str(uuid4()),
                sage_type="elder_council",
                message_type="broadcast",
                content={
                    "action": "council_session_created",
                    "session_id": session_id,
                    "title": new_session.title,
                    "participants": new_session.participants,
                },
                elder_council_session=session_id,
                timestamp=0,
            )
        )
        
        # Notify all sages about the new session
        for sage_type in ["knowledge", "task", "incident", "search"]:
            await websocket_manager.send_sage_message(
                SageMessage(
                    message_id=str(uuid4()),
                    sage_type="elder_council",
                    message_type="request",
                    target_sage=sage_type,
                    content={
                        "action": "join_council_session",
                        "session_id": session_id,
                        "title": new_session.title,
                        "description": new_session.description,
                    },
                    timestamp=0,
                )
            )
        
        logger.info(
            "Elder Council session created",
            session_id=session_id,
            title=new_session.title,
            participants=new_session.participants,
        )
        
        return ElderCouncilResponse(
            data=new_session,
            session_id=session_id,
            message="Council session created successfully",
        )
        
    except Exception as e:
        logger.error("Error creating council session", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create session")


@router.get("/sessions/{session_id}", response_model=ElderCouncilResponse)
async def get_council_session(session_id: str):
    """
    Get a specific Elder Council session.
    """
    try:
        if session_id not in council_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = council_sessions[session_id]
        messages = council_messages.get(session_id, [])
        
        session_data = {
            "session": session,
            "messages": messages,
            "message_count": len(messages),
        }
        
        return ElderCouncilResponse(
            data=session_data,
            session_id=session_id,
            message="Session retrieved successfully",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving council session", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve session")


@router.put("/sessions/{session_id}", response_model=ElderCouncilResponse)
async def update_council_session(
    session_id: str,
    status: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
):
    """
    Update an Elder Council session.
    """
    try:
        if session_id not in council_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = council_sessions[session_id]
        old_status = session.status
        
        # Update fields
        if status:
            session.status = status
        if title:
            session.title = title
        if description:
            session.description = description
        
        # Update timestamp
        from datetime import datetime
        session.updated_at = datetime.utcnow()
        
        # Broadcast session update
        await websocket_manager.send_sage_message(
            SageMessage(
                message_id=str(uuid4()),
                sage_type="elder_council",
                message_type="broadcast",
                content={
                    "action": "council_session_updated",
                    "session_id": session_id,
                    "title": session.title,
                    "old_status": old_status,
                    "new_status": session.status,
                },
                elder_council_session=session_id,
                timestamp=0,
            )
        )
        
        logger.info(
            "Elder Council session updated",
            session_id=session_id,
            old_status=old_status,
            new_status=session.status,
        )
        
        return ElderCouncilResponse(
            data=session,
            session_id=session_id,
            message="Session updated successfully",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating council session", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update session")


@router.post("/sessions/{session_id}/messages", response_model=ElderCouncilResponse)
async def send_council_message(session_id: str, message: ElderCouncilMessage):
    """
    Send a message to an Elder Council session.
    """
    try:
        if session_id not in council_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Generate message ID
        message_id = str(uuid4())
        
        # Create message
        new_message = ElderCouncilMessage(
            message_id=message_id,
            session_id=session_id,
            **message.dict(exclude={"message_id", "session_id"}),
        )
        
        # Store message
        if session_id not in council_messages:
            council_messages[session_id] = []
        council_messages[session_id].append(new_message)
        
        # Broadcast message to session participants
        await websocket_manager.broadcast_to_elder_council(
            session_id,
            {
                "type": "council_message",
                "message": new_message.dict(),
                "session_id": session_id,
            }
        )
        
        # Special handling for different message types
        if new_message.message_type == "decision":
            # Broadcast decision to all sages
            await websocket_manager.send_sage_message(
                SageMessage(
                    message_id=str(uuid4()),
                    sage_type="elder_council",
                    message_type="broadcast",
                    content={
                        "action": "council_decision",
                        "session_id": session_id,
                        "decision": new_message.content,
                        "sender": new_message.sender,
                    },
                    timestamp=0,
                )
            )
        
        logger.info(
            "Council message sent",
            session_id=session_id,
            message_id=message_id,
            sender=new_message.sender,
            message_type=new_message.message_type,
        )
        
        return ElderCouncilResponse(
            data=new_message,
            session_id=session_id,
            message="Message sent successfully",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error sending council message", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to send message")


@router.get("/sessions/{session_id}/messages", response_model=ElderCouncilResponse)
async def get_council_messages(
    session_id: str,
    message_type: Optional[str] = Query(None, description="Filter by message type"),
    limit: int = Query(50, ge=1, le=200, description="Number of messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
):
    """
    Get messages from an Elder Council session.
    """
    try:
        if session_id not in council_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        messages = council_messages.get(session_id, [])
        
        # Apply filters
        if message_type:
            messages = [m for m in messages if m.message_type == message_type]
        
        # Sort by creation time
        messages.sort(key=lambda m: m.created_at or 0)
        
        # Pagination
        total_count = len(messages)
        messages = messages[offset:offset + limit]
        
        return ElderCouncilResponse(
            data=messages,
            session_id=session_id,
            message=f"Retrieved {len(messages)} messages",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving council messages", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve messages")


@router.post("/sessions/{session_id}/invoke")
async def invoke_sage_council(
    session_id: str,
    topic: str,
    priority: str = "medium",
    auto_invite_sages: bool = True,
):
    """
    Invoke a council session on a specific topic, automatically inviting relevant sages.
    """
    try:
        if session_id not in council_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = council_sessions[session_id]
        
        # Determine which sages should be invited based on topic
        relevant_sages = []
        topic_lower = topic.lower()
        
        if any(word in topic_lower for word in ["knowledge", "documentation", "learning", "wiki"]):
            relevant_sages.append("knowledge")
        
        if any(word in topic_lower for word in ["task", "project", "workflow", "deadline"]):
            relevant_sages.append("task")
        
        if any(word in topic_lower for word in ["incident", "alert", "outage", "error"]):
            relevant_sages.append("incident")
        
        if any(word in topic_lower for word in ["search", "find", "query", "lookup"]):
            relevant_sages.append("search")
        
        # If no specific sages identified, invite all
        if not relevant_sages:
            relevant_sages = ["knowledge", "task", "incident", "search"]
        
        # Send invitations to relevant sages
        if auto_invite_sages:
            for sage_type in relevant_sages:
                await websocket_manager.send_sage_message(
                    SageMessage(
                        message_id=str(uuid4()),
                        sage_type="elder_council",
                        message_type="request",
                        target_sage=sage_type,
                        content={
                            "action": "council_invitation",
                            "session_id": session_id,
                            "topic": topic,
                            "priority": priority,
                            "session_title": session.title,
                        },
                        elder_council_session=session_id,
                        timestamp=0,
                    )
                )
        
        # Create system message about the invocation
        system_message = ElderCouncilMessage(
            message_id=str(uuid4()),
            session_id=session_id,
            sender="System",
            message_type="system",
            content=f"Council invoked on topic: {topic}. Invited sages: {', '.join(relevant_sages)}",
        )
        
        if session_id not in council_messages:
            council_messages[session_id] = []
        council_messages[session_id].append(system_message)
        
        # Broadcast to session
        await websocket_manager.broadcast_to_elder_council(
            session_id,
            {
                "type": "council_invoked",
                "topic": topic,
                "priority": priority,
                "invited_sages": relevant_sages,
                "message": system_message.dict(),
            }
        )
        
        logger.info(
            "Council invoked",
            session_id=session_id,
            topic=topic,
            priority=priority,
            invited_sages=relevant_sages,
        )
        
        return ElderCouncilResponse(
            data={
                "topic": topic,
                "priority": priority,
                "invited_sages": relevant_sages,
                "system_message": system_message,
            },
            session_id=session_id,
            message=f"Council invoked on topic: {topic}",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error invoking council", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to invoke council")


@router.get("/stats", response_model=ElderCouncilResponse)
async def get_council_stats():
    """
    Get Elder Council statistics.
    """
    try:
        total_sessions = len(council_sessions)
        total_messages = sum(len(messages) for messages in council_messages.values())
        
        stats = {
            "total_sessions": total_sessions,
            "active_sessions": len([s for s in council_sessions.values() if s.status == "active"]),
            "completed_sessions": len([s for s in council_sessions.values() if s.status == "completed"]),
            "total_messages": total_messages,
            "average_messages_per_session": (
                total_messages / total_sessions if total_sessions > 0 else 0
            ),
            "websocket_stats": websocket_manager.get_stats(),
        }
        
        return ElderCouncilResponse(
            data=stats,
            message="Council statistics retrieved",
        )
        
    except Exception as e:
        logger.error("Error retrieving council stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")