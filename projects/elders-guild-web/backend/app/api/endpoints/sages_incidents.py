"""
Incident Sage API Endpoints
Manages incidents, monitoring, and automated responses
"""

from typing import List
from typing import Optional
from uuid import UUID
from uuid import uuid4

import structlog
from app.schemas.sages import Incident
from app.schemas.sages import IncidentCreate
from app.schemas.sages import IncidentResponse
from app.schemas.sages import IncidentUpdate
from app.websocket.manager import SageMessage
from app.websocket.manager import websocket_manager
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Query

logger = structlog.get_logger()
router = APIRouter()

# In-memory storage for demonstration (replace with database in production)
incident_store: dict[str, Incident] = {}


@router.get("/", response_model=IncidentResponse)
async def get_incidents(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status"),
    assignee: Optional[str] = Query(None, description="Filter by assignee"),
    affected_systems: Optional[List[str]] = Query(None, description="Filter by affected systems"),
    limit: int = Query(10, ge=1, le=100, description="Number of incidents to return"),
    offset: int = Query(0, ge=0, description="Number of incidents to skip"),
):
    """
    Get all incidents with optional filtering.
    """
    try:
        incidents = list(incident_store.values())

        # Apply filters
        if severity:
            incidents = [i for i in incidents if i.severity == severity]

        if status:
            incidents = [i for i in incidents if i.status == status]

        if assignee:
            incidents = [i for i in incidents if i.assignee == assignee]

        if affected_systems:
            incidents = [i for i in incidents if any(system in i.affected_systems for system in affected_systems)]

        # Sort by severity and creation date
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        incidents.sort(key=lambda i: (-severity_order.get(i.severity, 0), i.created_at or i.updated_at), reverse=True)

        # Pagination
        total_count = len(incidents)
        incidents = incidents[offset : offset + limit]

        # Broadcast status update
        await websocket_manager.send_sage_message(
            SageMessage(
                message_id=str(uuid4()),
                sage_type="incident",
                message_type="status_update",
                content={
                    "action": "incidents_retrieved",
                    "count": len(incidents),
                    "total": total_count,
                    "active_critical": len(
                        [
                            i
                            for i in incident_store.values()
                            if i.severity == "critical" and i.status in ["open", "investigating"]
                        ]
                    ),
                },
                timestamp=0,
            )
        )

        return IncidentResponse(
            data=incidents,
            total_count=total_count,
            message=f"Retrieved {len(incidents)} incidents",
        )

    except Exception as e:
        logger.error("Error retrieving incidents", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve incidents")


@router.post("/", response_model=IncidentResponse)
async def create_incident(incident: IncidentCreate):
    """
    Create a new incident.
    """
    try:
        # Generate ID
        incident_id = str(uuid4())

        # Create incident
        new_incident = Incident(
            id=UUID(incident_id),
            **incident.dict(),
        )

        # Store incident
        incident_store[incident_id] = new_incident

        # Broadcast creation to other sages
        await websocket_manager.send_sage_message(
            SageMessage(
                message_id=str(uuid4()),
                sage_type="incident",
                message_type="broadcast",
                content={
                    "action": "incident_created",
                    "incident_id": incident_id,
                    "title": new_incident.title,
                    "severity": new_incident.severity,
                    "affected_systems": new_incident.affected_systems,
                    "reporter": new_incident.reporter,
                },
                timestamp=0,
            )
        )

        # Critical incidents trigger immediate notifications
        if new_incident.severity == "critical":
            # Notify all sages about critical incident
            await websocket_manager.send_sage_message(
                SageMessage(
                    message_id=str(uuid4()),
                    sage_type="incident",
                    message_type="broadcast",
                    content={
                        "action": "critical_incident_alert",
                        "incident_id": incident_id,
                        "title": new_incident.title,
                        "affected_systems": new_incident.affected_systems,
                        "description": new_incident.description,
                    },
                    timestamp=0,
                )
            )

            # Request knowledge sage to search for solutions
            await websocket_manager.send_sage_message(
                SageMessage(
                    message_id=str(uuid4()),
                    sage_type="incident",
                    message_type="request",
                    target_sage="knowledge",
                    content={
                        "action": "search_incident_solutions",
                        "incident_id": incident_id,
                        "title": new_incident.title,
                        "description": new_incident.description,
                        "affected_systems": new_incident.affected_systems,
                    },
                    timestamp=0,
                )
            )

            # Request search sage for related incidents
            await websocket_manager.send_sage_message(
                SageMessage(
                    message_id=str(uuid4()),
                    sage_type="incident",
                    message_type="request",
                    target_sage="search",
                    content={
                        "action": "find_similar_incidents",
                        "incident_id": incident_id,
                        "query": f"{new_incident.title} {new_incident.description}",
                        "systems": new_incident.affected_systems,
                    },
                    timestamp=0,
                )
            )

        logger.info(
            "Incident created",
            incident_id=incident_id,
            title=new_incident.title,
            severity=new_incident.severity,
            affected_systems=new_incident.affected_systems,
        )

        return IncidentResponse(
            data=new_incident,
            message="Incident created successfully",
        )

    except Exception as e:
        logger.error("Error creating incident", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create incident")


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: str):
    """
    Get a specific incident by ID.
    """
    try:
        if incident_id not in incident_store:
            raise HTTPException(status_code=404, detail="Incident not found")

        incident = incident_store[incident_id]

        # Broadcast view event
        await websocket_manager.send_sage_message(
            SageMessage(
                message_id=str(uuid4()),
                sage_type="incident",
                message_type="status_update",
                content={
                    "action": "incident_viewed",
                    "incident_id": incident_id,
                    "title": incident.title,
                    "severity": incident.severity,
                },
                timestamp=0,
            )
        )

        return IncidentResponse(
            data=incident,
            message="Incident retrieved successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving incident", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve incident")


@router.put("/{incident_id}", response_model=IncidentResponse)
async def update_incident(incident_id: str, update: IncidentUpdate):
    """
    Update an incident.
    """
    try:
        if incident_id not in incident_store:
            raise HTTPException(status_code=404, detail="Incident not found")

        incident = incident_store[incident_id]
        old_status = incident.status
        old_severity = incident.severity

        # Update fields
        update_data = update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(incident, field, value)

        # Set resolved timestamp if status changed to resolved
        if old_status != "resolved" and incident.status == "resolved":
            from datetime import datetime

            incident.resolved_at = datetime.utcnow()

        # Update timestamp
        from datetime import datetime

        incident.updated_at = datetime.utcnow()

        # Broadcast update
        await websocket_manager.send_sage_message(
            SageMessage(
                message_id=str(uuid4()),
                sage_type="incident",
                message_type="broadcast",
                content={
                    "action": "incident_updated",
                    "incident_id": incident_id,
                    "title": incident.title,
                    "old_status": old_status,
                    "new_status": incident.status,
                    "old_severity": old_severity,
                    "new_severity": incident.severity,
                    "updated_fields": list(update_data.keys()),
                },
                timestamp=0,
            )
        )

        # Special notifications for status changes
        if old_status != incident.status:
            if incident.status == "resolved":
                # Notify knowledge sage to document solution
                await websocket_manager.send_sage_message(
                    SageMessage(
                        message_id=str(uuid4()),
                        sage_type="incident",
                        message_type="request",
                        target_sage="knowledge",
                        content={
                            "action": "document_incident_resolution",
                            "incident_id": incident_id,
                            "title": incident.title,
                            "description": incident.description,
                            "resolution": incident.resolution,
                            "affected_systems": incident.affected_systems,
                        },
                        timestamp=0,
                    )
                )

                # Notify task sage to create follow-up tasks if needed
                await websocket_manager.send_sage_message(
                    SageMessage(
                        message_id=str(uuid4()),
                        sage_type="incident",
                        message_type="request",
                        target_sage="task",
                        content={
                            "action": "create_incident_followup",
                            "incident_id": incident_id,
                            "title": incident.title,
                            "resolution": incident.resolution,
                            "severity": incident.severity,
                        },
                        timestamp=0,
                    )
                )

        # Alert if severity escalated
        if old_severity != incident.severity and severity_order.get(incident.severity, 0) > severity_order.get(
            old_severity, 0
        ):
            await websocket_manager.send_sage_message(
                SageMessage(
                    message_id=str(uuid4()),
                    sage_type="incident",
                    message_type="broadcast",
                    content={
                        "action": "incident_escalated",
                        "incident_id": incident_id,
                        "title": incident.title,
                        "old_severity": old_severity,
                        "new_severity": incident.severity,
                    },
                    timestamp=0,
                )
            )

        logger.info(
            "Incident updated",
            incident_id=incident_id,
            old_status=old_status,
            new_status=incident.status,
            updated_fields=list(update_data.keys()),
        )

        return IncidentResponse(
            data=incident,
            message="Incident updated successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating incident", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update incident")


@router.delete("/{incident_id}", response_model=IncidentResponse)
async def delete_incident(incident_id: str):
    """
    Delete an incident.
    """
    try:
        if incident_id not in incident_store:
            raise HTTPException(status_code=404, detail="Incident not found")

        incident = incident_store[incident_id]
        del incident_store[incident_id]

        # Broadcast deletion
        await websocket_manager.send_sage_message(
            SageMessage(
                message_id=str(uuid4()),
                sage_type="incident",
                message_type="broadcast",
                content={
                    "action": "incident_deleted",
                    "incident_id": incident_id,
                    "title": incident.title,
                },
                timestamp=0,
            )
        )

        logger.info("Incident deleted", incident_id=incident_id)

        return IncidentResponse(
            message="Incident deleted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting incident", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete incident")


@router.get("/systems/", response_model=IncidentResponse)
async def get_affected_systems():
    """
    Get all systems that have been affected by incidents.
    """
    try:
        all_systems = set()
        for incident in incident_store.values():
            all_systems.update(incident.affected_systems)

        systems = sorted(list(all_systems))

        system_stats = {}
        for system in systems:
            system_incidents = [i for i in incident_store.values() if system in i.affected_systems]
            system_stats[system] = {
                "total_incidents": len(system_incidents),
                "open": len([i for i in system_incidents if i.status == "open"]),
                "investigating": len([i for i in system_incidents if i.status == "investigating"]),
                "resolved": len([i for i in system_incidents if i.status == "resolved"]),
                "closed": len([i for i in system_incidents if i.status == "closed"]),
                "critical_count": len([i for i in system_incidents if i.severity == "critical"]),
            }

        return IncidentResponse(
            data=system_stats,
            message=f"Retrieved {len(systems)} affected systems",
        )

    except Exception as e:
        logger.error("Error retrieving systems", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve systems")


@router.get("/stats/", response_model=IncidentResponse)
async def get_incident_stats():
    """
    Get incident statistics and analytics.
    """
    try:
        total_incidents = len(incident_store)

        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}

        stats = {
            "total_incidents": total_incidents,
            "status_breakdown": {
                "open": len([i for i in incident_store.values() if i.status == "open"]),
                "investigating": len([i for i in incident_store.values() if i.status == "investigating"]),
                "resolved": len([i for i in incident_store.values() if i.status == "resolved"]),
                "closed": len([i for i in incident_store.values() if i.status == "closed"]),
            },
            "severity_breakdown": {
                "critical": len([i for i in incident_store.values() if i.severity == "critical"]),
                "high": len([i for i in incident_store.values() if i.severity == "high"]),
                "medium": len([i for i in incident_store.values() if i.severity == "medium"]),
                "low": len([i for i in incident_store.values() if i.severity == "low"]),
            },
            "active_incidents": len([i for i in incident_store.values() if i.status in ["open", "investigating"]]),
            "critical_active": len(
                [
                    i
                    for i in incident_store.values()
                    if i.severity == "critical" and i.status in ["open", "investigating"]
                ]
            ),
            "total_affected_systems": len(
                set(system for incident in incident_store.values() for system in incident.affected_systems)
            ),
            "resolution_rate": (
                len([i for i in incident_store.values() if i.status in ["resolved", "closed"]]) / total_incidents * 100
                if total_incidents > 0
                else 0
            ),
        }

        return IncidentResponse(
            data=stats,
            message="Incident statistics retrieved",
        )

    except Exception as e:
        logger.error("Error retrieving incident stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@router.post("/alert", response_model=IncidentResponse)
async def create_alert_incident(
    title: str,
    description: str,
    severity: str,
    affected_systems: List[str],
    auto_response: bool = True,
):
    """
    Create an incident from an automated alert.
    """
    try:
        # Create incident from alert
        incident_create = IncidentCreate(
            title=f"ALERT: {title}",
            description=description,
            severity=severity,
            reporter="System Alert",
            affected_systems=affected_systems,
        )

        # Create the incident
        incident_response = await create_incident(incident_create)

        # Trigger automated response if enabled
        if auto_response and severity in ["critical", "high"]:
            await websocket_manager.send_sage_message(
                SageMessage(
                    message_id=str(uuid4()),
                    sage_type="incident",
                    message_type="broadcast",
                    content={
                        "action": "automated_response_triggered",
                        "incident_id": str(incident_response.data.id),
                        "title": title,
                        "severity": severity,
                        "affected_systems": affected_systems,
                    },
                    timestamp=0,
                )
            )

        return incident_response

    except Exception as e:
        logger.error("Error creating alert incident", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create alert incident")
