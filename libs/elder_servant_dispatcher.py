"""
🏛️ Elder Servant Dispatcher
Dispatch tasks to Elder Servants with hierarchy validation and coordination
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DispatchResult:
    """Result of task dispatch operation"""

    success: bool
    task_id: Optional[str] = None
    servant_id: Optional[str] = None
    estimated_completion: Optional[str] = None
    error: Optional[str] = None
    dispatch_timestamp: Optional[datetime] = None


@dataclass
class TaskAssignment:
    """Task assignment details"""

    task_id: str
    servant_type: str
    servant_id: str
    task_description: str
    elder_approval: str
    status: str
    created_at: datetime
    estimated_completion: datetime
    priority: str = "medium"


class ElderServantDispatcher:
    """🏛️ Elder Servant Task Dispatcher with Hierarchy Coordination"""

    def __init__(self):
        self.task_assignments: Dict[str, TaskAssignment] = {}
        self.active_servants: Dict[str, Dict[str, Any]] = {}
        self.dispatch_log_path = Path("/home/aicompany/ai_co/logs/servant_dispatch.log")
        self.dispatch_log_path.parent.mkdir(exist_ok=True)

        # Initialize servant types and their capabilities
        self.servant_capabilities = {
            "knight": {
                "specialties": ["testing", "quality_assurance", "security", "coverage"],
                "max_concurrent_tasks": 3,
                "average_task_duration": 30,  # minutes
            },
            "dwarf": {
                "specialties": [
                    "building",
                    "optimization",
                    "infrastructure",
                    "deployment",
                ],
                "max_concurrent_tasks": 2,
                "average_task_duration": 45,  # minutes
            },
            "wizard": {
                "specialties": ["analysis", "automation", "monitoring", "debugging"],
                "max_concurrent_tasks": 4,
                "average_task_duration": 25,  # minutes
            },
            "elf": {
                "specialties": ["monitoring", "logging", "alerting", "surveillance"],
                "max_concurrent_tasks": 5,
                "average_task_duration": 20,  # minutes
            },
        }

    async def dispatch_task(
        self,
        servant_type: str,
        servant_id: str,
        task_description: str,
        elder_approval: str,
        priority: str = "medium",
    ) -> DispatchResult:
        """Dispatch task to Elder Servant with hierarchy coordination"""

        try:
            # Generate unique task ID
            task_id = f"{servant_type}_{servant_id}_{uuid.uuid4().hex[:8]}"

            # Validate servant availability
            if not await self._validate_servant_availability(servant_type, servant_id):
                return DispatchResult(
                    success=False,
                    error=f"Servant {servant_id} is not available or at capacity",
                )

            # Calculate estimated completion time
            estimated_completion = self._calculate_completion_time(
                servant_type, priority
            )

            # Create task assignment
            assignment = TaskAssignment(
                task_id=task_id,
                servant_type=servant_type,
                servant_id=servant_id,
                task_description=task_description,
                elder_approval=elder_approval,
                status="dispatched",
                created_at=datetime.now(),
                estimated_completion=estimated_completion,
                priority=priority,
            )

            # Store assignment
            self.task_assignments[task_id] = assignment

            # Dispatch to appropriate servant
            dispatch_success = await self._dispatch_to_servant(assignment)

            if dispatch_success:
                # Log successful dispatch
                await self._log_dispatch(assignment, "SUCCESS")

                # Update servant status
                await self._update_servant_status(servant_id, task_id, "assigned")

                return DispatchResult(
                    success=True,
                    task_id=task_id,
                    servant_id=servant_id,
                    estimated_completion=estimated_completion.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    dispatch_timestamp=datetime.now(),
                )
            else:
                # Log failed dispatch
                await self._log_dispatch(assignment, "FAILED")

                return DispatchResult(
                    success=False,
                    error=f"Failed to dispatch task to {servant_type} {servant_id}",
                )

        except Exception as e:
            logger.error(f"Error dispatching task: {e}")
            return DispatchResult(success=False, error=f"Dispatch error: {str(e)}")

    async def _validate_servant_availability(
        self, servant_type: str, servant_id: str
    ) -> bool:
        """Validate that servant is available for new tasks"""

        if servant_type not in self.servant_capabilities:
            return False

        # Check current task load
        current_tasks = [
            task
            for task in self.task_assignments.values()
            if task.servant_id == servant_id
            and task.status in ["dispatched", "in_progress"]
        ]

        max_concurrent = self.servant_capabilities[servant_type]["max_concurrent_tasks"]

        return len(current_tasks) < max_concurrent

    def _calculate_completion_time(self, servant_type: str, priority: str) -> datetime:
        """Calculate estimated completion time based on servant type and priority"""

        base_duration = self.servant_capabilities[servant_type]["average_task_duration"]

        # Adjust for priority
        priority_multipliers = {
            "high": 0.7,  # High priority tasks get expedited
            "medium": 1.0,  # Standard time
            "low": 1.5,  # Low priority takes longer
        }

        adjusted_duration = base_duration * priority_multipliers.get(priority, 1.0)

        return datetime.now() + timedelta(minutes=adjusted_duration)

    async def _dispatch_to_servant(self, assignment: TaskAssignment) -> bool:
        """Dispatch task to specific servant based on type"""

        try:
            if assignment.servant_type == "knight":
                return await self._dispatch_to_knight(assignment)
            elif assignment.servant_type == "dwarf":
                return await self._dispatch_to_dwarf(assignment)
            elif assignment.servant_type == "wizard":
                return await self._dispatch_to_wizard(assignment)
            elif assignment.servant_type == "elf":
                return await self._dispatch_to_elf(assignment)
            else:
                logger.error(f"Unknown servant type: {assignment.servant_type}")
                return False

        except Exception as e:
            logger.error(f"Error dispatching to {assignment.servant_type}: {e}")
            return False

    async def _dispatch_to_knight(self, assignment: TaskAssignment) -> bool:
        """Dispatch task to Knight servant"""

        # Knights handle testing, quality assurance, and security tasks
        knight_task_file = Path(
            f"/home/aicompany/ai_co/tasks/knights/{assignment.servant_id}_task_{assignment.task_id}.json"
        )
        knight_task_file.parent.mkdir(parents=True, exist_ok=True)

        task_data = {
            "task_id": assignment.task_id,
            "description": assignment.task_description,
            "priority": assignment.priority,
            "elder_approval": assignment.elder_approval,
            "assigned_at": assignment.created_at.isoformat(),
            "estimated_completion": assignment.estimated_completion.isoformat(),
            "status": "assigned",
        }

        knight_task_file.write_text(json.dumps(task_data, indent=2))

        # If this is test_guardian_001, integrate with existing system
        if assignment.servant_id == "test_guardian_001":
            await self._integrate_with_test_guardian(assignment)

        logger.info(
            f"⚔️ Task dispatched to Knight {assignment.servant_id}: {assignment.task_id}"
        )
        return True

    async def _dispatch_to_dwarf(self, assignment: TaskAssignment) -> bool:
        """Dispatch task to Dwarf servant"""

        # Dwarfs handle building, optimization, and infrastructure
        dwarf_task_file = Path(
            f"/home/aicompany/ai_co/tasks/dwarfs/{assignment.servant_id}_task_{assignment." \
                "task_id}.json"
        )
        dwarf_task_file.parent.mkdir(parents=True, exist_ok=True)

        task_data = {
            "task_id": assignment.task_id,
            "description": assignment.task_description,
            "priority": assignment.priority,
            "elder_approval": assignment.elder_approval,
            "assigned_at": assignment.created_at.isoformat(),
            "estimated_completion": assignment.estimated_completion.isoformat(),
            "status": "assigned",
            "build_target": self._extract_build_target(assignment.task_description),
            "optimization_focus": self._extract_optimization_focus(
                assignment.task_description
            ),
        }

        dwarf_task_file.write_text(json.dumps(task_data, indent=2))

        logger.info(
            f"⛏️ Task dispatched to Dwarf {assignment.servant_id}: {assignment.task_id}"
        )
        return True

    async def _dispatch_to_wizard(self, assignment: TaskAssignment) -> bool:
        """Dispatch task to Wizard servant"""

        # Wizards handle analysis, automation, and monitoring
        wizard_task_file = Path(
            f"/home/aicompany/ai_co/tasks/wizards/{assignment.servant_id}_task_{assignment." \
                "task_id}.json"
        )
        wizard_task_file.parent.mkdir(parents=True, exist_ok=True)

        task_data = {
            "task_id": assignment.task_id,
            "description": assignment.task_description,
            "priority": assignment.priority,
            "elder_approval": assignment.elder_approval,
            "assigned_at": assignment.created_at.isoformat(),
            "estimated_completion": assignment.estimated_completion.isoformat(),
            "status": "assigned",
            "analysis_type": self._extract_analysis_type(assignment.task_description),
            "automation_scope": self._extract_automation_scope(
                assignment.task_description
            ),
        }

        wizard_task_file.write_text(json.dumps(task_data, indent=2))

        logger.info(
            f"🧙‍♂️ Task dispatched to Wizard {assignment.servant_id}: {assignment.task_id}"
        )
        return True

    async def _dispatch_to_elf(self, assignment: TaskAssignment) -> bool:
        """Dispatch task to Elf servant"""

        # Elfs handle monitoring, logging, and alerting
        elf_task_file = Path(
            f"/home/aicompany/ai_co/tasks/elfs/{assignment.servant_id}_task_{assignment." \
                "task_id}.json"
        )
        elf_task_file.parent.mkdir(parents=True, exist_ok=True)

        task_data = {
            "task_id": assignment.task_id,
            "description": assignment.task_description,
            "priority": assignment.priority,
            "elder_approval": assignment.elder_approval,
            "assigned_at": assignment.created_at.isoformat(),
            "estimated_completion": assignment.estimated_completion.isoformat(),
            "status": "assigned",
            "monitoring_target": self._extract_monitoring_target(
                assignment.task_description
            ),
            "alert_threshold": self._extract_alert_threshold(
                assignment.task_description
            ),
        }

        elf_task_file.write_text(json.dumps(task_data, indent=2))

        logger.info(
            f"🧝‍♂️ Task dispatched to Elf {assignment.servant_id}: {assignment.task_id}"
        )
        return True

    async def _integrate_with_test_guardian(self, assignment: TaskAssignment):
        """Integrate task with existing Test Guardian Knight"""

        # Create special coordination file for Test Guardian
        coordination_file = Path(
            f"/home/aicompany/ai_co/knights/test_guardian_coordination.json"
        )

        coordination_data = {
            "new_task": {
                "task_id": assignment.task_id,
                "description": assignment.task_description,
                "priority": assignment.priority,
                "elder_approval": assignment.elder_approval,
                "coordination_mode": "integrate",
                "assigned_at": assignment.created_at.isoformat(),
            }
        }

        coordination_file.write_text(json.dumps(coordination_data, indent=2))
        logger.info(f"🤝 Test Guardian coordination file created: {assignment.task_id}")

    def _extract_build_target(self, description: str) -> str:
        """Extract build target from task description"""
        if "build" in description.lower():
            if "pipeline" in description.lower():
                return "pipeline"
            elif "deployment" in description.lower():
                return "deployment"
            elif "optimization" in description.lower():
                return "optimization"
        return "general"

    def _extract_optimization_focus(self, description: str) -> str:
        """Extract optimization focus from task description"""
        if "performance" in description.lower():
            return "performance"
        elif "memory" in description.lower():
            return "memory"
        elif "speed" in description.lower():
            return "speed"
        return "general"

    def _extract_analysis_type(self, description: str) -> str:
        """Extract analysis type from task description"""
        if "security" in description.lower():
            return "security"
        elif "performance" in description.lower():
            return "performance"
        elif "code" in description.lower():
            return "code"
        return "general"

    def _extract_automation_scope(self, description: str) -> str:
        """Extract automation scope from task description"""
        if "testing" in description.lower():
            return "testing"
        elif "deployment" in description.lower():
            return "deployment"
        elif "monitoring" in description.lower():
            return "monitoring"
        return "general"

    def _extract_monitoring_target(self, description: str) -> str:
        """Extract monitoring target from task description"""
        if "worker" in description.lower():
            return "worker"
        elif "system" in description.lower():
            return "system"
        elif "performance" in description.lower():
            return "performance"
        return "general"

    def _extract_alert_threshold(self, description: str) -> str:
        """Extract alert threshold from task description"""
        if "critical" in description.lower():
            return "critical"
        elif "warning" in description.lower():
            return "warning"
        elif "info" in description.lower():
            return "info"
        return "medium"

    async def _update_servant_status(self, servant_id: str, task_id: str, status: str):
        """Update servant status with new task assignment"""

        if servant_id not in self.active_servants:
            self.active_servants[servant_id] = {
                "current_tasks": [],
                "completed_tasks": 0,
                "last_activity": datetime.now().isoformat(),
            }

        if status == "assigned":
            self.active_servants[servant_id]["current_tasks"].append(task_id)
        elif status == "completed":
            if task_id in self.active_servants[servant_id]["current_tasks"]:
                self.active_servants[servant_id]["current_tasks"].remove(task_id)
            self.active_servants[servant_id]["completed_tasks"] += 1

        self.active_servants[servant_id]["last_activity"] = datetime.now().isoformat()

    async def _log_dispatch(self, assignment: TaskAssignment, result: str):
        """Log dispatch operation"""

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_id": assignment.task_id,
            "servant_type": assignment.servant_type,
            "servant_id": assignment.servant_id,
            "task_description": (
                assignment.task_description[:100] + "..."
                if len(assignment.task_description) > 100
                else assignment.task_description
            ),
            "priority": assignment.priority,
            "result": result,
            "estimated_completion": assignment.estimated_completion.isoformat(),
        }

        with open(self.dispatch_log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific task"""

        if task_id not in self.task_assignments:
            return None

        assignment = self.task_assignments[task_id]

        return {
            "task_id": task_id,
            "servant_type": assignment.servant_type,
            "servant_id": assignment.servant_id,
            "description": assignment.task_description,
            "status": assignment.status,
            "priority": assignment.priority,
            "created_at": assignment.created_at.isoformat(),
            "estimated_completion": assignment.estimated_completion.isoformat(),
            "elder_approval": assignment.elder_approval,
        }

    async def list_active_tasks(self) -> List[Dict[str, Any]]:
        """List all active task assignments"""

        active_tasks = []

        for task_id, assignment in self.task_assignments.items():
            if assignment.status in ["dispatched", "in_progress"]:
                active_tasks.append(
                    {
                        "task_id": task_id,
                        "servant_type": assignment.servant_type,
                        "servant_id": assignment.servant_id,
                        "description": (
                            assignment.task_description[:50] + "..."
                            if len(assignment.task_description) > 50
                            else assignment.task_description
                        ),
                        "status": assignment.status,
                        "priority": assignment.priority,
                        "created_at": assignment.created_at.isoformat(),
                        "estimated_completion": assignment.estimated_completion.isoformat(),
                    }
                )

        return active_tasks

    async def complete_task(self, task_id: str, result: Dict[str, Any]) -> bool:
        """Mark task as completed with results"""

        if task_id not in self.task_assignments:
            return False

        assignment = self.task_assignments[task_id]
        assignment.status = "completed"

        # Update servant status
        await self._update_servant_status(assignment.servant_id, task_id, "completed")

        # Log completion
        await self._log_dispatch(
            assignment, f"COMPLETED: {result.get('summary', 'No summary')}"
        )

        logger.info(
            f"✅ Task completed: {task_id} by {assignment.servant_type} {assignment.servant_id}"
        )

        return True
