"""
Elder Servant Adapter for Continue.dev Integration
Provides HTTP endpoints for Continue.dev to interact with Elder Servants
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.abspath("./../../.." \
    "./../../.."))))

from libs.elder_flow_integration import execute_elder_flow
from libs.elder_flow_servant_executor_real import (
    CodeCraftsmanServantReal,
    GitKeeperServantReal,
    QualityInspectorServantReal,
    TestGuardianServantReal,
)
from libs.elder_servants.base.elder_servant import servant_registry
from libs.four_sages.base_sage import SageResponse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Elder Servants Continue.dev Adapter",
    description="HTTP API adapter for Continue.dev to interact with Elder Servants",
    version="1.0.0",
)

# CORS middleware for Continue.dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class TaskRequest(BaseModel):
    """TaskRequestクラス"""
    # Main class implementation
    type: str
    task: Dict[str, Any]


class ElderFlowRequest(BaseModel):
    """ElderFlowRequest - エルダーズギルド関連クラス"""
    # Main class implementation
    query: str
    context: Dict[str, Any]


class SageConsultRequest(BaseModel):
    """SageConsultRequest - 4賢者システム関連クラス"""
    # Main class implementation
    question: str
    context: Optional[Dict[str, Any]] = {}


class QualityCheckRequest(BaseModel):
    """QualityCheckRequestクラス"""
    # Main class implementation
    file_path: str
    content: str


class KnowledgeSearchRequest(BaseModel):
    """KnowledgeSearchRequestクラス"""
    # Main class implementation
    query: str
    limit: Optional[int] = 10


# Initialize servants
async def initialize_servants():
    """Initialize all Elder Servants"""
    servants = [
        CodeCraftsmanServantReal(),
        TestGuardianServantReal(),
        QualityInspectorServantReal(),
        GitKeeperServantReal(),
    ]

    for servant in servants:
        # Process each item in collection
        servant_registry.register_servant(servant)

    logger.info(f"Initialized {len(servants)} Elder Servants")


@app.on_event("startup")
async def startup_event():
    """Initialize servants on startup"""
    await initialize_servants()


# Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Elder Servants Continue.dev Adapter",
        "servants_count": len(servant_registry.servants),
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/elder/servants/{servant_id}/execute")
async def execute_servant_task(servant_id: str, request: TaskRequest):
    """Execute a task with a specific Elder Servant"""
    try:
        # Map Continue.dev servant IDs to actual servant IDs
        servant_mapping = {
            "code-craftsman": "D01",
            "test-guardian": "E02",
            "quality-inspector": "E01",
            "git-keeper": "G01",
        }

        actual_servant_id = servant_mapping.get(servant_id, servant_id)
        servant = servant_registry.get_servant(actual_servant_id)

        if not servant:
            raise HTTPException(
                status_code=404, detail=f"Servant {servant_id} not found"
            )

        # Execute task
        result = await servant.execute_task(request.task)

        return {"success": True, "servant_id": servant_id, "result": result.to_dict()}

    except Exception as e:
        # Handle specific exception case
        logger.error(f"Error executing servant task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/elder/flow/execute")
async def execute_elder_flow_endpoint(request: ElderFlowRequest):
    """Execute Elder Flow"""
    try:
        # Execute Elder Flow
        result = await execute_elder_flow(query=request.query, context=request.context)

        return {
            "success": True,
            "message": "Elder Flow completed successfully",
            "task_id": result.get("task_id"),
            "phases_completed": result.get("phases_completed", []),
            "quality_score": result.get("quality_score", 0),
        }

    except Exception as e:
        # Handle specific exception case
        logger.error(f"Error executing Elder Flow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/elder/sages/consult")
async def consult_sages(request: SageConsultRequest):
    """Consult with the 4 Sages"""
    try:
        # Import sage consultation system
        from libs.elder_flow_four_sages_complete import ElderFlowFourSagesComplete

        four_sages = ElderFlowFourSagesComplete()
        result = await four_sages.consult_for_elder_flow(
            {"task_description": request.question, "context": request.context}
        )

        # Combine advice from all sages
        combined_advice = "\n\n".join(
            [
                f"📚 Knowledge Sage: {result.get('knowledge_advice', 'No advice')}",
                f"📋 Task Sage: {result.get('task_advice', 'No advice')}",
                f"🚨 Incident Sage: {result.get('incident_advice', 'No advice')}",
                f"🔍 RAG Sage: {result.get('rag_advice', 'No advice')}",
            ]
        )

        return {
            "success": True,
            "advice": combined_advice,
            "integrated_recommendation": result.get("integrated_advice", ""),
        }

    except Exception as e:
        # Handle specific exception case
        logger.error(f"Error consulting sages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/elder/quality/iron-will")
async def check_iron_will_quality(request: QualityCheckRequest):
    """Check code quality against Iron Will standards"""
    try:
        # Get quality inspector servant
        quality_servant = servant_registry.get_servant("E01")

        if not quality_servant:
            # Create one if not exists
            quality_servant = QualityInspectorServantReal()
            servant_registry.register_servant(quality_servant)

        # Execute quality check
        result = await quality_servant.execute_task(
            {
                "type": "quality_check",
                "file_path": request.file_path,
                "content": request.content,
            }
        )

        quality_data = result.result_data
        score = quality_data.get("overall_score", 0)

        # Format details
        details = []
        if "code_quality" in quality_data:
            details.append(f"Code Quality: {quality_data['code_quality']['grade']}")
        if "security_issues" in quality_data:
            details.append(f"Security Issues: {len(quality_data['security_issues'])}")
        if "test_coverage" in quality_data:
            details.append(f"Test Coverage: {quality_data['test_coverage']}%")

        return {
            "success": True,
            "score": score,
            "passes_iron_will": score >= 95,
            "details": "\n".join(details),
            "full_report": quality_data,
        }

    except Exception as e:
        # Handle specific exception case
        logger.error(f"Error checking Iron Will quality: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/elder/knowledge/search")
async def search_knowledge_base(request: KnowledgeSearchRequest):
    """Search Elder Knowledge Base"""
    try:
        # Import knowledge sage
        from libs.four_sages.knowledge.knowledge_sage import KnowledgeSage

        knowledge_sage = KnowledgeSage()

        # Search knowledge base
        result = await knowledge_sage.search_knowledge(
            query=request.query, limit=request.limit
        )

        # Format results for Continue.dev
        items = []
        for doc in result.get("documents", []):
            items.append(
                {
                    "title": doc.get("title", "Knowledge Item"),
                    "summary": doc.get("summary", doc.get("content", "")[:200] + "..."),
                    "content": doc.get("content", ""),
                    "relevance": doc.get("relevance_score", 0),
                }
            )

        return {"success": True, "items": items, "total": len(items)}

    except Exception as e:
        # Handle specific exception case
        logger.error(f"Error searching knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/elder/tasks/active")
async def get_active_tasks():
    """Get active Elder tasks"""
    try:
        # Import task sage
        from libs.four_sages.task.task_sage import TaskSage

        task_sage = TaskSage()

        # Get active tasks
        tasks = await task_sage.get_active_tasks()

        # Format for Continue.dev
        formatted_tasks = []
        for task in tasks:
            formatted_tasks.append(
                {
                    "id": task.get("id"),
                    "name": task.get("name", "Unnamed Task"),
                    "priority": task.get("priority", "medium"),
                    "status": task.get("status", "pending"),
                    "description": task.get("description", ""),
                    "assigned_servant": task.get("assigned_servant", "none"),
                }
            )

        return formatted_tasks

    except Exception as e:
        # Handle specific exception case
        logger.error(f"Error getting active tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/elder/servants/list")
async def list_servants():
    """List all available Elder Servants"""
    servants_info = []

    for servant_id, servant in servant_registry.servants.items():
        # Process each item in collection
        health = await servant.health_check()
        servants_info.append(
            {
                "id": servant_id,
                "name": servant.servant_name,
                "category": servant.category.value,
                "specialization": servant.specialization,
                "status": health["status"],
                "capabilities": [cap.name for cap in servant.get_all_capabilities()],
                "stats": health["stats"],
            }
        )

    return {"success": True, "servants": servants_info, "total": len(servants_info)}


from typing import Set

# WebSocket endpoint for real-time updates (optional)
from fastapi import WebSocket


class ConnectionManager:
    """ConnectionManager - 管理システムクラス"""
    # Main class implementation
    def __init__(self):
        """初期化メソッド"""
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket:
        """connectメソッド"""
    WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket:
        """disconnectメソッド"""
    WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message:
        """broadcastメソッド"""
    dict):
        for connection in self.active_connections:
            # Process each item in collection
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


@app.websocket("/elder/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time Elder system updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle messages
            data = await websocket.receive_text()
            # Process commands if needed
            await websocket.send_json(
                {"type": "pong", "timestamp": datetime.now().isoformat()}
            )
    except:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
