"""
API Router configuration for Elders Guild Web FastAPI Backend
Four Sages System API endpoints
"""

from fastapi import APIRouter

from app.api.endpoints import (
    sages_knowledge,
    sages_tasks,
    sages_incidents,
    sages_search,
    elder_council,
    websocket_routes,
)

# Main API router
api_router = APIRouter()

# Four Sages API endpoints
api_router.include_router(
    sages_knowledge.router,
    prefix="/sages/knowledge",
    tags=["Knowledge Sage"],
)

api_router.include_router(
    sages_tasks.router,
    prefix="/sages/tasks",
    tags=["Task Sage"],
)

api_router.include_router(
    sages_incidents.router,
    prefix="/sages/incidents",
    tags=["Incident Sage"],
)

api_router.include_router(
    sages_search.router,
    prefix="/sages/search",
    tags=["RAG Search Sage"],
)

# Elder Council coordination endpoints
api_router.include_router(
    elder_council.router,
    prefix="/elder-council",
    tags=["Elder Council"],
)

# WebSocket endpoints
api_router.include_router(
    websocket_routes.router,
    prefix="/ws",
    tags=["WebSocket"],
)