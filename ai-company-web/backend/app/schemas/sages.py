"""
Pydantic schemas for Four Sages System API
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Base Schemas
class BaseResponse(BaseModel):
    """Base response model."""
    success: bool = True
    message: str = "Operation completed successfully"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Knowledge Sage Schemas
class KnowledgeArticle(BaseModel):
    """Knowledge article model."""
    id: Optional[UUID] = None
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1, max_length=50)
    tags: List[str] = Field(default_factory=list)
    author: str = Field(..., min_length=1, max_length=100)
    version: int = Field(default=1, ge=1)
    status: str = Field(default="draft", pattern="^(draft|published|archived)$")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class KnowledgeArticleCreate(BaseModel):
    """Create knowledge article request."""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1, max_length=50)
    tags: List[str] = Field(default_factory=list)
    author: str = Field(..., min_length=1, max_length=100)


class KnowledgeArticleUpdate(BaseModel):
    """Update knowledge article request."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    tags: Optional[List[str]] = None
    status: Optional[str] = Field(None, pattern="^(draft|published|archived)$")


class KnowledgeResponse(BaseResponse):
    """Knowledge sage response."""
    data: Optional[Any] = None
    total_count: Optional[int] = None


# Task Sage Schemas
class Task(BaseModel):
    """Task model."""
    id: Optional[UUID] = None
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: str = Field(default="todo", pattern="^(todo|in_progress|done|blocked)$")
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    assignee: Optional[str] = Field(None, max_length=100)
    project: Optional[str] = Field(None, max_length=100)
    labels: List[str] = Field(default_factory=list)
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    actual_hours: Optional[float] = Field(None, ge=0)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TaskCreate(BaseModel):
    """Create task request."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: str = Field(default="todo", pattern="^(todo|in_progress|done|blocked)$")
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    assignee: Optional[str] = Field(None, max_length=100)
    project: Optional[str] = Field(None, max_length=100)
    labels: List[str] = Field(default_factory=list)
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = Field(None, ge=0)


class TaskUpdate(BaseModel):
    """Update task request."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(todo|in_progress|done|blocked)$")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    assignee: Optional[str] = Field(None, max_length=100)
    project: Optional[str] = Field(None, max_length=100)
    labels: Optional[List[str]] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    actual_hours: Optional[float] = Field(None, ge=0)


class TaskResponse(BaseResponse):
    """Task sage response."""
    data: Optional[Any] = None
    total_count: Optional[int] = None


# Incident Sage Schemas
class Incident(BaseModel):
    """Incident model."""
    id: Optional[UUID] = None
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    status: str = Field(default="open", pattern="^(open|investigating|resolved|closed)$")
    assignee: Optional[str] = Field(None, max_length=100)
    reporter: str = Field(..., min_length=1, max_length=100)
    affected_systems: List[str] = Field(default_factory=list)
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class IncidentCreate(BaseModel):
    """Create incident request."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    assignee: Optional[str] = Field(None, max_length=100)
    reporter: str = Field(..., min_length=1, max_length=100)
    affected_systems: List[str] = Field(default_factory=list)


class IncidentUpdate(BaseModel):
    """Update incident request."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    severity: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    status: Optional[str] = Field(None, pattern="^(open|investigating|resolved|closed)$")
    assignee: Optional[str] = Field(None, max_length=100)
    affected_systems: Optional[List[str]] = None
    resolution: Optional[str] = None


class IncidentResponse(BaseResponse):
    """Incident sage response."""
    data: Optional[Any] = None
    total_count: Optional[int] = None


# Search Sage Schemas
class SearchQuery(BaseModel):
    """Search query model."""
    query: str = Field(..., min_length=1, max_length=500)
    search_type: str = Field(default="semantic", pattern="^(semantic|keyword|hybrid)$")
    filters: Optional[Dict[str, Any]] = None
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SearchResult(BaseModel):
    """Search result model."""
    id: str
    title: str
    content: str
    source: str  # knowledge, task, incident
    score: float = Field(..., ge=0, le=1)
    metadata: Optional[Dict[str, Any]] = None
    highlighted_content: Optional[str] = None


class SearchResponse(BaseResponse):
    """Search sage response."""
    results: List[SearchResult]
    total_count: int
    query_time_ms: float
    suggestions: Optional[List[str]] = None


# Elder Council Schemas
class ElderCouncilSession(BaseModel):
    """Elder Council session model."""
    session_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    participants: List[str] = Field(default_factory=list)
    status: str = Field(default="active", pattern="^(active|paused|completed)$")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ElderCouncilMessage(BaseModel):
    """Elder Council message model."""
    message_id: Optional[str] = None
    session_id: str
    sender: str
    message_type: str = Field(default="chat", pattern="^(chat|decision|vote|system)$")
    content: str = Field(..., min_length=1)
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


class ElderCouncilResponse(BaseResponse):
    """Elder Council response."""
    data: Optional[Any] = None
    session_id: Optional[str] = None


# WebSocket Schemas
class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sage_type: Optional[str] = None
    session_id: Optional[str] = None