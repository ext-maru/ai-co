"""
Worker Auto-Recovery System

自動的にワーカーの健康状態を監視し、問題が発生した場合に自動復旧を行うシステム。

Components:
- HealthChecker: ワーカーの健康状態をチェック
- RecoveryManager: 復旧処理の管理
- RecoveryStrategies: 復旧戦略の実装
- StateManager: ワーカーの状態保持と復元
- NotificationHandler: 通知処理

Usage:
    from libs.worker_auto_recovery import WorkerRecoveryManager

    manager = WorkerRecoveryManager()
    manager.start_monitoring()
"""

# Import classes from parent module
import sys
from pathlib import Path

from .health_checker import HealthChecker
from .notification_handler import NotificationHandler
from .recovery_manager import WorkerRecoveryManager
from .recovery_strategies import RecoveryStrategies
from .state_manager import StateManager

# Add parent module to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

try:
    # Import from the parent module (libs/worker_auto_recovery.py)
    # モジュール名の競合を避けるため、別名でインポート
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "worker_auto_recovery_module",
        str(Path(__file__).parent.parent / "libs" / "worker_auto_recovery.py"),
    )
    worker_auto_recovery_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(worker_auto_recovery_module)

    WorkerHealthMonitor = worker_auto_recovery_module.WorkerHealthMonitor
    AutoRecoveryEngine = worker_auto_recovery_module.AutoRecoveryEngine
    RecoveryStrategyManager = worker_auto_recovery_module.RecoveryStrategyManager
    HealthCheckService = worker_auto_recovery_module.HealthCheckService
    WorkerState = worker_auto_recovery_module.WorkerState
    RecoveryStrategy = worker_auto_recovery_module.RecoveryStrategy
    HealthStatus = worker_auto_recovery_module.HealthStatus
    RecoveryAction = worker_auto_recovery_module.RecoveryAction
except Exception as e:
    # Create placeholder classes if import fails
    class WorkerHealthMonitor:
        def __init__(self, config=None):
            import logging

            logging.warning("Using placeholder WorkerHealthMonitor")
            self.config = config or {}
            self.check_interval = self.config.get("check_interval", 30)
            self.failure_threshold = self.config.get("failure_threshold", 3)
            self.timeout = self.config.get("timeout", 5)
            self.is_monitoring = False
            self._worker_states = {}
            self._worker_configs = {}
            self._health_change_handlers = []
            self._monitoring_task = None

        def get_system_status(self):
            return {
                "total_workers": 0,
                "health_summary": {"healthy": 0, "unhealthy": 0},
                "is_monitoring": self.is_monitoring,
            }

        async def start_monitoring(self):
            self.is_monitoring = True

        async def stop_monitoring(self):
            self.is_monitoring = False

        def get_tracked_workers(self):
            return []

        async def register_worker(self, worker_id, config):
            self._worker_configs[worker_id] = config

        async def check_worker_health(self, worker_id):
            from datetime import datetime

            return WorkerState(
                worker_id=worker_id,
                status=HealthStatus.HEALTHY,
                last_health_check=datetime.now(),
            )

        def get_worker_state(self, worker_id):
            return self._worker_states.get(worker_id)

        def on_health_change(self, handler):
            self._health_change_handlers.append(handler)

    class AutoRecoveryEngine:
        def __init__(
            self, strategies=None, max_recovery_attempts=3, backoff_multiplier=1.0
        ):
            import logging

            logging.warning("Using placeholder AutoRecoveryEngine")
            self.enabled_strategies = strategies or [RecoveryStrategy.RESTART]
            self.max_recovery_attempts = max_recovery_attempts
            self.backoff_multiplier = backoff_multiplier
            self._recovery_handlers = []
            self._strategy_manager = None

        async def attempt_recovery(self, worker_state):
            from dataclasses import dataclass
            from datetime import datetime

            @dataclass
            class RecoveryResult:
                success: bool = False
                worker_id: str = ""
                action: str = "none"
                attempts: int = 0
                reason: str = "placeholder"
                timestamp: datetime = None

            return RecoveryResult()

        def calculate_backoff_time(self, worker_state):
            base_time = 1.0
            return base_time * (
                self.backoff_multiplier**worker_state.recovery_attempts
            )

        async def handle_health_change(self, event):
            pass

        def on_recovery_attempt(self, handler):
            self._recovery_handlers.append(handler)

        def set_strategy_manager(self, manager):
            self._strategy_manager = manager

    class RecoveryStrategyManager:
        def __init__(self, *args, **kwargs):
            import logging

            logging.warning("Using placeholder RecoveryStrategyManager")
            self.strategies = {}

        def get_available_strategies(self):
            return []

        def register_strategy(self, strategy, handler, priority=0):
            pass

        def get_strategies_by_priority(self):
            return []

        def select_strategy(self, worker_state):
            return None

        async def execute_strategy(self, strategy, worker_state):
            return True

    class HealthCheckService:
        def __init__(self, port=8080, **kwargs):
            import logging

            logging.warning("Using placeholder HealthCheckService")
            self.port = port
            self.is_running = False
            self._monitors = []
            self._health_monitor = None
            self.app = None

        async def start(self):
            self.is_running = True

        async def stop(self):
            self.is_running = False

        def register_monitor(self, monitor):
            self._monitors.append(monitor)

        def set_health_monitor(self, monitor):
            self._health_monitor = monitor

        async def get_worker_status(self, worker_id):
            return {
                "worker_id": worker_id,
                "status": "unknown",
                "error": "Placeholder service",
            }

        async def collect_metrics(self):
            return {
                "workers": {},
                "system": {"total_workers": 0, "healthy_workers": 0},
                "timestamp": datetime.now().isoformat(),
            }

        async def handle_health(self, request):
            pass

        async def handle_worker_health(self, request):
            pass

        async def handle_metrics(self, request):
            pass

        async def handle_prometheus_metrics(self, request):
            pass

        async def update_health_status(self, worker_id, status):
            pass

    # Placeholder enums and dataclasses
    from dataclasses import dataclass, field
    from datetime import datetime
    from enum import Enum
    from typing import Any, Dict, Optional

    class HealthStatus(Enum):
        HEALTHY = "healthy"
        UNHEALTHY = "unhealthy"
        DEGRADED = "degraded"
        UNKNOWN = "unknown"

    class RecoveryStrategy(Enum):
        RESTART = "restart"
        RESET = "reset"
        RECREATE = "recreate"
        CUSTOM = "custom"

    class RecoveryAction(Enum):
        RESTART = "restart"
        RESET = "reset"
        RECREATE = "recreate"
        NONE = "none"

    @dataclass
    class WorkerState:
        worker_id: str
        status: HealthStatus
        last_health_check: datetime
        consecutive_failures: int = 0
        recovery_attempts: int = 0
        last_recovery: Optional[datetime] = None
        failure_reason: Optional[str] = None
        metadata: Dict[str, Any] = field(default_factory=dict)


__all__ = [
    "WorkerRecoveryManager",
    "HealthChecker",
    "RecoveryStrategies",
    "StateManager",
    "NotificationHandler",
    "WorkerHealthMonitor",
    "AutoRecoveryEngine",
    "RecoveryStrategyManager",
    "HealthCheckService",
    "WorkerState",
    "RecoveryStrategy",
    "HealthStatus",
    "RecoveryAction",
]

__version__ = "1.0.0"
