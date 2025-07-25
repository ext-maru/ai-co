"""
🏛️ Elder Servant Registry
Manages registration and status of all Elder Servants in the Elders Guild
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ServantInfo:
    """Information about an Elder Servant"""

    servant_id: str
    servant_type: str
    description: str
    status: str  # active, inactive, maintenance, retired
    specialties: List[str]
    current_tasks: List[str]
    completed_tasks: int
    success_rate: float
    last_activity: datetime
    registration_date: datetime
    max_concurrent_tasks: int
    average_completion_time: float  # in minutes


class ServantRegistry:
    """🏛️ Elder Servant Registry and Management System"""

    def __init__(self):
        """初期化メソッド"""
        self.registry_file = Path("/home/aicompany/ai_co/data/servant_registry.json")
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)

        self.servants: Dict[str, ServantInfo] = {}
        self.servant_types = ["knight", "dwarf", "wizard", "elf"]
        self._loaded = False

    async def _ensure_loaded(self):
        """Ensure registry is loaded"""
        if not self._loaded:
            await self._load_registry()
            self._loaded = True

    async def _load_registry(self):
        """Load servant registry from file"""
        try:
            if self.registry_file.exists():
                data = json.loads(self.registry_file.read_text())

                for servant_id, servant_data in data.items():
                    # Convert datetime strings back to datetime objects
                    servant_data["last_activity"] = datetime.fromisoformat(
                        servant_data["last_activity"]
                    )
                    servant_data["registration_date"] = datetime.fromisoformat(
                        servant_data["registration_date"]
                    )

                    self.servants[servant_id] = ServantInfo(**servant_data)

                logger.info(f"📚 Loaded {len(self.servants)} servants from registry")
            else:
                # Initialize with known servants
                await self._initialize_default_servants()
        except Exception as e:
            logger.error(f"Error loading servant registry: {e}")
            await self._initialize_default_servants()

    async def _save_registry(self):
        """Save servant registry to file"""
        try:
            # Convert ServantInfo objects to dictionaries with datetime serialization
            registry_data = {}
            for servant_id, servant_info in self.servants.items():
                servant_dict = asdict(servant_info)
                servant_dict["last_activity"] = servant_info.last_activity.isoformat()
                servant_dict["registration_date"] = (
                    servant_info.registration_date.isoformat()
                )
                registry_data[servant_id] = servant_dict

            self.registry_file.write_text(json.dumps(registry_data, indent=2))
            logger.debug(f"💾 Saved servant registry with {len(self.servants)} entries")
        except Exception as e:
            logger.error(f"Error saving servant registry: {e}")

    async def _initialize_default_servants(self):
        """Initialize registry with default known servants"""

        # Register Test Guardian Knight (known active servant)
        await self.register_servant(
            servant_id="test_guardian_001",
            servant_type="knight",
            description="Continuous testing and quality assurance knight",
            specialties=["testing", "quality_assurance", "test_coverage", "guard_duty"],
        )

        # Register example servants for each type
        await self.register_servant(
            servant_id="coverage_enhancement_001",
            servant_type="knight",
            description="Test coverage enhancement specialist knight",
            specialties=["coverage_analysis", "test_enhancement", "quality_metrics"],
        )

        await self.register_servant(
            servant_id="build_support_001",
            servant_type="dwarf",
            description="Build pipeline optimization dwarf",
            specialties=["build_optimization", "deployment", "infrastructure"],
        )

        await self.register_servant(
            servant_id="monitoring_analysis_001",
            servant_type="wizard",
            description="System monitoring and analysis wizard",
            specialties=["monitoring", "analysis", "automation", "diagnostics"],
        )

        await self.register_servant(
            servant_id="alert_watcher_001",
            servant_type="elf",
            description="Alert monitoring and notification elf",
            specialties=["alerting", "surveillance", "logging", "notification"],
        )

        logger.info("🏗️ Initialized default servant registry")

    async def register_servant(
        self,
        servant_id: str,
        servant_type: str,
        description: str,
        specialties: List[str],
        max_concurrent_tasks: Optional[int] = None,
    ) -> bool:
        """Register a new Elder Servant"""

        if servant_type not in self.servant_types:
            logger.error(f"Invalid servant type: {servant_type}")
            return False

        if servant_id in self.servants:
            logger.warning(f"Servant {servant_id} already registered")
            return False

        # Set default max concurrent tasks based on type
        if max_concurrent_tasks is None:
            defaults = {"knight": 3, "dwarf": 2, "wizard": 4, "elf": 5}
            max_concurrent_tasks = defaults[servant_type]

        servant_info = ServantInfo(
            servant_id=servant_id,
            servant_type=servant_type,
            description=description,
            status="active",
            specialties=specialties,
            current_tasks=[],
            completed_tasks=0,
            success_rate=1.0,
            last_activity=datetime.now(),
            registration_date=datetime.now(),
            max_concurrent_tasks=max_concurrent_tasks,
            average_completion_time=30.0,  # Default 30 minutes
        )

        self.servants[servant_id] = servant_info
        await self._save_registry()

        logger.info(f"✅ Registered {servant_type.title()} {servant_id}: {description}")
        return True

    async def unregister_servant(self, servant_id: str) -> bool:
        """Unregister an Elder Servant"""

        if servant_id not in self.servants:
            logger.warning(f"Servant {servant_id} not found in registry")
            return False

        servant_info = self.servants[servant_id]

        # Check if servant has active tasks
        if servant_info.current_tasks:
            logger.error(
                f"Cannot unregister {servant_id}: has {len(servant_info.current_tasks)} " \
                    "active tasks"
            )
            return False

        # Mark as retired instead of removing completely
        servant_info.status = "retired"
        servant_info.last_activity = datetime.now()

        await self._save_registry()

        logger.info(f"🏛️ Retired {servant_info.servant_type.title()} {servant_id}")
        return True

    async def update_servant_status(self, servant_id: str, status: str) -> bool:
        """Update servant status"""

        valid_statuses = ["active", "inactive", "maintenance", "retired"]

        if status not in valid_statuses:
            logger.error(f"Invalid status: {status}")
            return False

        if servant_id not in self.servants:
            logger.error(f"Servant {servant_id} not found")
            return False

        self.servants[servant_id].status = status
        self.servants[servant_id].last_activity = datetime.now()

        await self._save_registry()

        logger.info(f"📊 Updated {servant_id} status to {status}")
        return True

    async def assign_task(self, servant_id: str, task_id: str) -> bool:
        """Assign task to servant"""

        if servant_id not in self.servants:
            logger.error(f"Servant {servant_id} not found")
            return False

        servant_info = self.servants[servant_id]

        # Check if servant is active
        if servant_info.status != "active":
            logger.error(
                f"Servant {servant_id} is not active (status: {servant_info.status})"
            )
            return False

        # Check capacity
        if len(servant_info.current_tasks) >= servant_info.max_concurrent_tasks:
            logger.error(
                f"Servant {servant_id} is at capacity ({len(servant_info.current_tasks)}/"
                f"{servant_info.max_concurrent_tasks})"
            )
            return False

        # Assign task
        servant_info.current_tasks.append(task_id)
        servant_info.last_activity = datetime.now()

        await self._save_registry()

        logger.info(
            f"⚔️ Assigned task {task_id} to {servant_info.servant_type.title()} {servant_id}"
        )
        return True

    async def complete_task(
        self, servant_id: str, task_id: str, success: bool = True
    ) -> bool:
        """Mark task as completed for servant"""

        if servant_id not in self.servants:
            logger.error(f"Servant {servant_id} not found")
            return False

        servant_info = self.servants[servant_id]

        if task_id not in servant_info.current_tasks:
            logger.warning(f"Task {task_id} not found in {servant_id}'s current tasks")
            return False

        # Remove from current tasks
        servant_info.current_tasks.remove(task_id)
        servant_info.completed_tasks += 1
        servant_info.last_activity = datetime.now()

        # Update success rate
        total_tasks = servant_info.completed_tasks
        if success:
            # Maintain or improve success rate
            servant_info.success_rate = (
                servant_info.success_rate * (total_tasks - 1) + 1.0
            ) / total_tasks
        else:
            # Decrease success rate
            servant_info.success_rate = (
                servant_info.success_rate * (total_tasks - 1)
            ) / total_tasks

        await self._save_registry()

        status_emoji = "✅" if success else "❌"
        logger.info(
            f"{status_emoji} Task {task_id} completed by {servant_info.servant_type.title()} " \
                "{servant_id}"
        )
        return True

    async def list_servants(
        self, servant_type: Optional[str] = None, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List servants with optional filtering"""

        await self._ensure_loaded()

        filtered_servants = []

        for servant_id, servant_info in self.servants.items():
            # Apply filters
            if servant_type and servant_info.servant_type != servant_type:
                continue

            if status and servant_info.status != status:
                continue

            # Convert to dictionary for return
            servant_dict = {
                "id": servant_id,
                "type": servant_info.servant_type,
                "description": servant_info.description,
                "status": servant_info.status,
                "specialties": servant_info.specialties,
                "current_tasks": len(servant_info.current_tasks),
                "max_concurrent_tasks": servant_info.max_concurrent_tasks,
                "completed_tasks": servant_info.completed_tasks,
                "success_rate": round(
                    servant_info.success_rate * 100, 1
                ),  # Convert to percentage
                "last_activity": servant_info.last_activity.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "registration_date": servant_info.registration_date.strftime(
                    "%Y-%m-%d"
                ),
            }

            filtered_servants.append(servant_dict)

        # Sort by servant type, then by ID
        filtered_servants.sort(key=lambda x: (x["type"], x["id"]))

        return filtered_servants

    async def get_servant_status(self, servant_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of specific servant"""

        await self._ensure_loaded()

        if servant_id not in self.servants:
            return None

        servant_info = self.servants[servant_id]

        return {
            "servant_id": servant_id,
            "type": servant_info.servant_type,
            "description": servant_info.description,
            "status": servant_info.status,
            "specialties": servant_info.specialties,
            "current_task": (
                servant_info.current_tasks[-1] if servant_info.current_tasks else None
            ),
            "current_tasks_count": len(servant_info.current_tasks),
            "max_concurrent_tasks": servant_info.max_concurrent_tasks,
            "completed_tasks": servant_info.completed_tasks,
            "success_rate": round(servant_info.success_rate * 100, 1),
            "average_completion_time": servant_info.average_completion_time,
            "last_activity": servant_info.last_activity.strftime("%Y-%m-%d %H:%M:%S"),
            "registration_date": servant_info.registration_date.strftime("%Y-%m-%d"),
            "uptime_days": (datetime.now() - servant_info.registration_date).days,
            "capacity_utilization": round(
                (len(servant_info.current_tasks) / servant_info.max_concurrent_tasks)
                * 100,
                1,
            ),
        }

    async def get_servant_capacity(self, servant_id: str) -> Optional[Dict[str, int]]:
        """Get servant capacity information"""

        if servant_id not in self.servants:
            return None

        servant_info = self.servants[servant_id]

        return {
            "current_tasks": len(servant_info.current_tasks),
            "max_concurrent_tasks": servant_info.max_concurrent_tasks,
            "available_capacity": servant_info.max_concurrent_tasks
            - len(servant_info.current_tasks),
            "utilization_percentage": round(
                (len(servant_info.current_tasks) / servant_info.max_concurrent_tasks)
                * 100,
                1,
            ),
        }

    async def find_available_servants(
        self, servant_type: Optional[str] = None, specialty: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find servants available for new tasks"""

        available_servants = []

        for servant_id, servant_info in self.servants.items():
            # Must be active
            if servant_info.status != "active":
                continue

            # Must have capacity
            if len(servant_info.current_tasks) >= servant_info.max_concurrent_tasks:
                continue

            # Apply type filter
            if servant_type and servant_info.servant_type != servant_type:
                continue

            # Apply specialty filter
            if specialty and specialty not in servant_info.specialties:
                continue

            available_capacity = servant_info.max_concurrent_tasks - len(
                servant_info.current_tasks
            )

            servant_dict = {
                "servant_id": servant_id,
                "type": servant_info.servant_type,
                "description": servant_info.description,
                "specialties": servant_info.specialties,
                "available_capacity": available_capacity,
                "success_rate": round(servant_info.success_rate * 100, 1),
                "completed_tasks": servant_info.completed_tasks,
                "average_completion_time": servant_info.average_completion_time,
            }

            available_servants.append(servant_dict)

        # Sort by availability (most available first), then by success rate
        available_servants.sort(
            key=lambda x: (-x["available_capacity"], -x["success_rate"])
        )

        return available_servants

    async def get_registry_stats(self) -> Dict[str, Any]:
        """Get overall registry statistics"""

        stats = {
            "total_servants": len(self.servants),
            "by_type": {},
            "by_status": {},
            "total_active_tasks": 0,
            "total_completed_tasks": 0,
            "average_success_rate": 0.0,
        }

        success_rates = []

        for servant_info in self.servants.values():
            # Count by type
            servant_type = servant_info.servant_type
            if servant_type not in stats["by_type"]:
                stats["by_type"][servant_type] = 0
            stats["by_type"][servant_type] += 1

            # Count by status
            status = servant_info.status
            if status not in stats["by_status"]:
                stats["by_status"][status] = 0
            stats["by_status"][status] += 1

            # Accumulate task counts
            stats["total_active_tasks"] += len(servant_info.current_tasks)
            stats["total_completed_tasks"] += servant_info.completed_tasks

            # Collect success rates
            success_rates.append(servant_info.success_rate)

        # Calculate average success rate
        if success_rates:
            stats["average_success_rate"] = round(
                sum(success_rates) / len(success_rates) * 100, 1
            )

        return stats

    async def maintenance_mode(self, servant_id: str, enable: bool = True) -> bool:
        """Enable or disable maintenance mode for servant"""

        if servant_id not in self.servants:
            logger.error(f"Servant {servant_id} not found")
            return False

        servant_info = self.servants[servant_id]

        if enable:
            # Check if servant has active tasks
            if servant_info.current_tasks:
                logger.error(
                    (
                        f"Cannot enable maintenance mode for {servant_id}: has "
                        f"{len(servant_info.current_tasks)} active tasks"
                    )
                )
                return False

            servant_info.status = "maintenance"
            logger.info(f"🔧 Enabled maintenance mode for {servant_id}")
        else:
            if servant_info.status == "maintenance":
                servant_info.status = "active"
                logger.info(f"✅ Disabled maintenance mode for {servant_id}")

        servant_info.last_activity = datetime.now()
        await self._save_registry()

        return True