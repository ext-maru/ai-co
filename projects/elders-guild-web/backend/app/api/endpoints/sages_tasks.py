"""
Task Sage API Endpoints
Manages tasks, projects, and workflow automation
"""

from typing import List
from typing import Optional
from uuid import UUID
from uuid import uuid4

import structlog
from app.schemas.sages import Task
from app.schemas.sages import TaskCreate
from app.schemas.sages import TaskResponse
from app.schemas.sages import TaskUpdate
from app.websocket.manager import SageMessage
from app.websocket.manager import websocket_manager
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Query

logger = structlog.get_logger()
router = APIRouter()

# In-memory storage for demonstration (replace with database in production)
task_store: dict[str, Task] = {}


@router.get("/", response_model=TaskResponse)
async def get_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    assignee: Optional[str] = Query(None, description="Filter by assignee"),
    project: Optional[str] = Query(None, description="Filter by project"),
    labels: Optional[List[str]] = Query(None, description="Filter by labels"),
    limit: int = Query(10, ge=1, le=100, description="Number of tasks to return"),
    offset: int = Query(0, ge=0, description="Number of tasks to skip"),
):
    """
    Get all tasks with optional filtering.
    """
    try:
        tasks = list(task_store.values())

        # Apply filters
        if status:
            tasks = [t for t in tasks if t.status == status]

        if priority:
            tasks = [t for t in tasks if t.priority == priority]

        if assignee:
            tasks = [t for t in tasks if t.assignee == assignee]

        if project:
            tasks = [t for t in tasks if t.project == project]

        if labels:
            tasks = [t for t in tasks if any(label in t.labels for label in labels)]

        # Sort by priority and creation date
        priority_order = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
        tasks.sort(key=lambda t: (-priority_order.get(t.priority, 0), t.created_at or t.updated_at), reverse=True)

        # Pagination
        total_count = len(tasks)
        tasks = tasks[offset : offset + limit]

        # Broadcast status update
        await websocket_manager.send_sage_message(
            SageMessage(
                message_id=str(uuid4()),
                sage_type="task",
                message_type="status_update",
                content={
                    "action": "tasks_retrieved",
                    "count": len(tasks),
                    "total": total_count,
                    "filters": {
                        "status": status,
                        "priority": priority,
                        "assignee": assignee,
                        "project": project,
                    },
                },
                timestamp=0,
            )
        )

        return TaskResponse(
            data=tasks,
            total_count=total_count,
            message=f"Retrieved {len(tasks)} tasks",
        )

    except Exception as e:
        logger.error("Error retrieving tasks", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve tasks")


@router.post("/", response_model=TaskResponse)
async def create_task(task: TaskCreate):
    """
    Create a new task.
    """
    try:
        # Generate ID
        task_id = str(uuid4())

        # Create task
        new_task = Task(
            id=UUID(task_id),
            **task.dict(),
        )

        # Store task
        task_store[task_id] = new_task

        # Broadcast creation to other sages
        await websocket_manager.send_sage_message(
            SageMessage(
                message_id=str(uuid4()),
                sage_type="task",
                message_type="broadcast",
                content={
                    "action": "task_created",
                    "task_id": task_id,
                    "title": new_task.title,
                    "priority": new_task.priority,
                    "assignee": new_task.assignee,
                    "project": new_task.project,
                },
                timestamp=0,
            )
        )

        # Notify incident sage if high priority
        if new_task.priority in ["high", "urgent"]:
            await websocket_manager.send_sage_message(
                SageMessage(
                    message_id=str(uuid4()),
                    sage_type="task",
                    message_type="request",
                    target_sage="incident",
                    content={
                        "action": "high_priority_task_created",
                        "task_id": task_id,
                        "title": new_task.title,
                        "priority": new_task.priority,
                    },
                    timestamp=0,
                )
            )

        logger.info(
            "Task created",
            task_id=task_id,
            title=new_task.title,
            priority=new_task.priority,
            assignee=new_task.assignee,
        )

        return TaskResponse(
            data=new_task,
            message="Task created successfully",
        )

    except Exception as e:
        logger.error("Error creating task", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create task")


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """
    Get a specific task by ID.
    """
    try:
        if task_id not in task_store:
            raise HTTPException(status_code=404, detail="Task not found")

        task = task_store[task_id]

        # Broadcast view event
        await websocket_manager.send_sage_message(
            SageMessage(
                message_id=str(uuid4()),
                sage_type="task",
                message_type="status_update",
                content={
                    "action": "task_viewed",
                    "task_id": task_id,
                    "title": task.title,
                },
                timestamp=0,
            )
        )

        return TaskResponse(
            data=task,
            message="Task retrieved successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving task", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve task")


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, update: TaskUpdate):
    """
    Update a task.
    """
    try:
        if task_id not in task_store:
            raise HTTPException(status_code=404, detail="Task not found")

        task = task_store[task_id]
        old_status = task.status

        # Update fields
        update_data = update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        # Update timestamp
        from datetime import datetime

        task.updated_at = datetime.utcnow()

        # Broadcast update
        await websocket_manager.send_sage_message(
            SageMessage(
                message_id=str(uuid4()),
                sage_type="task",
                message_type="broadcast",
                content={
                    "action": "task_updated",
                    "task_id": task_id,
                    "title": task.title,
                    "old_status": old_status,
                    "new_status": task.status,
                    "updated_fields": list(update_data.keys()),
                },
                timestamp=0,
            )
        )

        # Special notifications for status changes
        if old_status != task.status:
            if task.status == "done":
                # Notify knowledge sage to potentially create documentation
                await websocket_manager.send_sage_message(
                    SageMessage(
                        message_id=str(uuid4()),
                        sage_type="task",
                        message_type="request",
                        target_sage="knowledge",
                        content={
                            "action": "task_completed",
                            "task_id": task_id,
                            "title": task.title,
                            "description": task.description,
                        },
                        timestamp=0,
                    )
                )
            elif task.status == "blocked":
                # Notify incident sage about blocked task
                await websocket_manager.send_sage_message(
                    SageMessage(
                        message_id=str(uuid4()),
                        sage_type="task",
                        message_type="request",
                        target_sage="incident",
                        content={
                            "action": "task_blocked",
                            "task_id": task_id,
                            "title": task.title,
                            "description": task.description,
                        },
                        timestamp=0,
                    )
                )

        logger.info(
            "Task updated",
            task_id=task_id,
            old_status=old_status,
            new_status=task.status,
            updated_fields=list(update_data.keys()),
        )

        return TaskResponse(
            data=task,
            message="Task updated successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating task", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update task")


@router.delete("/{task_id}", response_model=TaskResponse)
async def delete_task(task_id: str):
    """
    Delete a task.
    """
    try:
        if task_id not in task_store:
            raise HTTPException(status_code=404, detail="Task not found")

        task = task_store[task_id]
        del task_store[task_id]

        # Broadcast deletion
        await websocket_manager.send_sage_message(
            SageMessage(
                message_id=str(uuid4()),
                sage_type="task",
                message_type="broadcast",
                content={
                    "action": "task_deleted",
                    "task_id": task_id,
                    "title": task.title,
                },
                timestamp=0,
            )
        )

        logger.info("Task deleted", task_id=task_id)

        return TaskResponse(
            message="Task deleted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting task", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete task")


@router.get("/projects/", response_model=TaskResponse)
async def get_projects():
    """
    Get all available projects.
    """
    try:
        projects = list(set(task.project for task in task_store.values() if task.project))
        projects.sort()

        project_stats = {}
        for project in projects:
            project_tasks = [t for t in task_store.values() if t.project == project]
            project_stats[project] = {
                "total_tasks": len(project_tasks),
                "todo": len([t for t in project_tasks if t.status == "todo"]),
                "in_progress": len([t for t in project_tasks if t.status == "in_progress"]),
                "done": len([t for t in project_tasks if t.status == "done"]),
                "blocked": len([t for t in project_tasks if t.status == "blocked"]),
            }

        return TaskResponse(
            data=project_stats,
            message=f"Retrieved {len(projects)} projects",
        )

    except Exception as e:
        logger.error("Error retrieving projects", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve projects")


@router.get("/assignees/", response_model=TaskResponse)
async def get_assignees():
    """
    Get all task assignees with their task counts.
    """
    try:
        assignees = list(set(task.assignee for task in task_store.values() if task.assignee))
        assignees.sort()

        assignee_stats = {}
        for assignee in assignees:
            assignee_tasks = [t for t in task_store.values() if t.assignee == assignee]
            assignee_stats[assignee] = {
                "total_tasks": len(assignee_tasks),
                "todo": len([t for t in assignee_tasks if t.status == "todo"]),
                "in_progress": len([t for t in assignee_tasks if t.status == "in_progress"]),
                "done": len([t for t in assignee_tasks if t.status == "done"]),
                "blocked": len([t for t in assignee_tasks if t.status == "blocked"]),
            }

        return TaskResponse(
            data=assignee_stats,
            message=f"Retrieved {len(assignees)} assignees",
        )

    except Exception as e:
        logger.error("Error retrieving assignees", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve assignees")


@router.get("/stats/", response_model=TaskResponse)
async def get_task_stats():
    """
    Get task statistics and analytics.
    """
    try:
        total_tasks = len(task_store)

        stats = {
            "total_tasks": total_tasks,
            "status_breakdown": {
                "todo": len([t for t in task_store.values() if t.status == "todo"]),
                "in_progress": len([t for t in task_store.values() if t.status == "in_progress"]),
                "done": len([t for t in task_store.values() if t.status == "done"]),
                "blocked": len([t for t in task_store.values() if t.status == "blocked"]),
            },
            "priority_breakdown": {
                "urgent": len([t for t in task_store.values() if t.priority == "urgent"]),
                "high": len([t for t in task_store.values() if t.priority == "high"]),
                "medium": len([t for t in task_store.values() if t.priority == "medium"]),
                "low": len([t for t in task_store.values() if t.priority == "low"]),
            },
            "total_projects": len(set(t.project for t in task_store.values() if t.project)),
            "total_assignees": len(set(t.assignee for t in task_store.values() if t.assignee)),
            "completion_rate": (
                len([t for t in task_store.values() if t.status == "done"]) / total_tasks * 100
                if total_tasks > 0
                else 0
            ),
        }

        return TaskResponse(
            data=stats,
            message="Task statistics retrieved",
        )

    except Exception as e:
        logger.error("Error retrieving task stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")
