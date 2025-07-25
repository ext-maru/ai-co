#!/usr/bin/env python3
"""
Worker Auto-Recovery System

Based on Elder Council's guidance and Four Sages recommendations,
this module implements comprehensive worker auto-recovery functionality.

Components:
- WorkerHealthMonitor: Monitors worker health status
- AutoRecoveryEngine: Executes recovery actions
- RecoveryStrategyManager: Manages recovery strategies
- HealthCheckService: Provides health check endpoints
"""

import asyncio
import json
import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

import aiohttp
import psutil
from aiohttp import web

# Setup logging
logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration"""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class RecoveryStrategy(Enum):
    """Recovery strategy enumeration"""

    RESTART = "restart"
    RESET = "reset"
    RECREATE = "recreate"
    CUSTOM = "custom"


class RecoveryAction(Enum):
    """Recovery action enumeration"""

    RESTART = "restart"
    RESET = "reset"
    RECREATE = "recreate"
    NONE = "none"


@dataclass
class WorkerState:
    """Worker state information"""

    worker_id: str
    status: HealthStatus
    last_health_check: datetime
    consecutive_failures: int = 0
    recovery_attempts: int = 0
    last_recovery: Optional[datetime] = None
    failure_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryResult:
    """Recovery attempt result"""

    success: bool
    worker_id: str
    action: RecoveryAction
    attempts: int = 1
    reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class StrategyInfo:
    """Strategy information"""

    strategy: RecoveryStrategy
    handler: Callable
    priority: int = 0


class WorkerHealthMonitor:
    """Worker Health Monitor class"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Worker Health Monitor

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.check_interval = self.config.get("check_interval", 30)
        self.failure_threshold = self.config.get("failure_threshold", 3)
        self.timeout = self.config.get("timeout", 5)
        self.is_monitoring = False

        # Worker states
        self._worker_states: Dict[str, WorkerState] = {}
        self._worker_configs: Dict[str, Dict[str, Any]] = {}

        # Event handlers
        self._health_change_handlers: List[Callable] = []

        # Monitoring task
        self._monitoring_task: Optional[asyncio.Task] = None

    async def start_monitoring(self):
        """Start monitoring workers"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Worker health monitoring started")

    async def stop_monitoring(self):
        """Stop monitoring workers"""
        if self.is_monitoring:
            self.is_monitoring = False
            if self._monitoring_task:
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass
            logger.info("Worker health monitoring stopped")

    async def check_worker_health(self, worker_id: str) -> WorkerState:
        """
        Check the health of a specific worker

        Args:
            worker_id: Worker identifier

        Returns:
            WorkerState object with current health status
        """
        # Get or create worker state
        if worker_id not in self._worker_states:
            self._worker_states[worker_id] = WorkerState(
                worker_id=worker_id,
                status=HealthStatus.UNKNOWN,
                last_health_check=datetime.now(),
            )

        worker_state = self._worker_states[worker_id]
        previous_status = worker_state.status

        # Perform health check
        try:
            is_healthy = await self._check_worker_health(worker_id)

            if is_healthy:
                worker_state.status = HealthStatus.HEALTHY
                worker_state.consecutive_failures = 0
                worker_state.failure_reason = None
            else:
                worker_state.consecutive_failures += 1
                if worker_state.consecutive_failures >= self.failure_threshold:
                    worker_state.status = HealthStatus.UNHEALTHY
                else:
                    worker_state.status = HealthStatus.DEGRADED

        except Exception as e:
            logger.error(f"Health check failed for {worker_id}: {e}")
            worker_state.consecutive_failures += 1
            worker_state.failure_reason = str(e)

            if worker_state.consecutive_failures >= self.failure_threshold:
                worker_state.status = HealthStatus.UNHEALTHY
            else:
                worker_state.status = HealthStatus.DEGRADED

        worker_state.last_health_check = datetime.now()

        # Emit event if status changed
        if previous_status != worker_state.status:
            await self._emit_health_change(
                worker_id, previous_status, worker_state.status
            )

        return worker_state

    async def _check_worker_health(self, worker_id: str) -> bool:
        """
        Internal method to check worker health

        Args:
            worker_id: Worker identifier

        Returns:
            True if healthy, False otherwise
        """
        # Check if worker process is running
        worker_config = self._worker_configs.get(worker_id, {})

        # Try HTTP health check if endpoint is configured
        health_endpoint = worker_config.get("health_check_endpoint")
        if health_endpoint:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        health_endpoint,
                        timeout=aiohttp.ClientTimeout(total=self.timeout),
                    ) as response:
                        return response.status == 200
            except Exception as e:
                logger.debug(f"HTTP health check failed for {worker_id}: {e}")
                return False

        # Fallback to process check
        return self._check_process_health(worker_id)

    def _check_process_health(self, worker_id: str) -> bool:
        """Check if worker process is running"""
        try:
            # Find process by worker ID
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    cmdline = proc.info.get("cmdline", [])
                    if cmdline and worker_id in " ".join(cmdline):
                        return proc.is_running()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception as e:
            logger.error(f"Process health check failed for {worker_id}: {e}")
            return False

    async def register_worker(self, worker_id: str, config: Dict[str, Any]):
        """
        Register a worker for monitoring

        Args:
            worker_id: Worker identifier
            config: Worker configuration
        """
        self._worker_configs[worker_id] = config
        self._worker_states[worker_id] = WorkerState(
            worker_id=worker_id,
            status=HealthStatus.UNKNOWN,
            last_health_check=datetime.now(),
            metadata=config,
        )
        logger.info(f"Registered worker {worker_id} for monitoring")

    def get_tracked_workers(self) -> List[str]:
        """Get list of tracked worker IDs"""
        return list(self._worker_states.keys())

    def get_worker_state(self, worker_id: str) -> Optional[WorkerState]:
        """Get current state of a worker"""
        return self._worker_states.get(worker_id)

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        total_workers = len(self._worker_states)
        health_summary = {"healthy": 0, "unhealthy": 0, "degraded": 0, "unknown": 0}

        for worker_state in self._worker_states.values():
            status_key = worker_state.status.value
            if status_key in health_summary:
                health_summary[status_key] += 1

        return {
            "total_workers": total_workers,
            "health_summary": health_summary,
            "is_monitoring": self.is_monitoring,
            "worker_states": {
                worker_id: {
                    "status": state.status.value,
                    "last_check": state.last_health_check.isoformat(),
                    "consecutive_failures": state.consecutive_failures,
                }
                for worker_id, state in self._worker_states.items()
            },
        }

    def auto_restart_failed_workers(self) -> List[str]:
        """自動的に失敗したワーカーを再起動"""
        restarted_workers = []

        for worker_id, state in self._worker_states.items():
            if (
                state.status == HealthStatus.UNHEALTHY
                and state.consecutive_failures >= self.failure_threshold
            ):
                try:
                    logger.info(f"🔄 ワーカー自動再起動: {worker_id}")

                    # ワーカープロセスを強制終了
                    self._kill_worker_process(worker_id)

                    # 少し待機
                    import time

                    time.sleep(2)

                    # ワーカーを再起動
                    if self._restart_worker(worker_id):
                        restarted_workers.append(worker_id)
                        state.consecutive_failures = 0
                        state.status = HealthStatus.HEALTHY
                        logger.info(f"✅ ワーカー再起動成功: {worker_id}")
                    else:
                        logger.error(f"❌ ワーカー再起動失敗: {worker_id}")

                except Exception as e:
                    logger.error(f"ワーカー再起動中にエラー: {worker_id} - {e}")

        return restarted_workers

    def _kill_worker_process(self, worker_id: str):
        """ワーカープロセスを強制終了"""
        try:
            import subprocess

            # worker_idからプロセスを特定して終了
            result = subprocess.run(
                ["pkill", "-f", worker_id], capture_output=True, text=True
            )
            if result.returncode == 0:
                logger.info(f"ワーカープロセス終了: {worker_id}")
        except Exception as e:
            logger.error(f"プロセス終了に失敗: {worker_id} - {e}")

    def _restart_worker(self, worker_id: str) -> bool:
        """ワーカーを再起動"""
        try:
            import subprocess
            from pathlib import Path

            # ワーカータイプを判定
            if "task" in worker_id.lower():
                script_path = Path(
                    "/home/aicompany/ai_co/workers/enhanced_task_worker.py"
                )
            elif "pm" in worker_id.lower():
                script_path = Path(
                    "/home/aicompany/ai_co/workers/intelligent_pm_worker_simple.py"
                )
            elif "result" in worker_id.lower():
                script_path = Path(
                    "/home/aicompany/ai_co/workers/async_result_worker_simple.py"
                )
            else:
                logger.error(f"不明なワーカータイプ: {worker_id}")
                return False

            if not script_path.exists():
                logger.error(f"ワーカースクリプトが見つかりません: {script_path}")
                return False

            # バックグラウンドで起動
            subprocess.Popen(
                ["python3", str(script_path)],
                cwd="/home/aicompany/ai_co",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            return True

        except Exception as e:
            logger.error(f"ワーカー起動に失敗: {worker_id} - {e}")
            return False

    def enable_auto_recovery(self):
        """自動復旧を有効化"""
        self.auto_recovery_enabled = True
        logger.info("✅ ワーカー自動復旧が有効になりました")

    def disable_auto_recovery(self):
        """自動復旧を無効化"""
        self.auto_recovery_enabled = False
        logger.info("❌ ワーカー自動復旧が無効になりました")

    def on_health_change(self, handler: Callable):
        """
        Register a health change event handler

        Args:
            handler: Async callable to handle health change events
        """
        self._health_change_handlers.append(handler)

    async def _emit_health_change(
        self, worker_id: str, old_status: HealthStatus, new_status: HealthStatus
    ):
        """Emit health change event"""
        worker_state = self._worker_states.get(worker_id)
        event = {
            "worker_id": worker_id,
            "old_status": old_status,
            "new_status": new_status,
            "timestamp": datetime.now(),
            "worker_state": worker_state,
        }

        for handler in self._health_change_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in health change handler: {e}")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Check all registered workers
                for worker_id in list(self._worker_states.keys()):
                    if self.is_monitoring:
                        await self.check_worker_health(worker_id)

                # Wait for next check interval
                await asyncio.sleep(self.check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)


class AutoRecoveryEngine:
    """Auto Recovery Engine class"""

    def __init__(
        self,
        strategies: Optional[List[RecoveryStrategy]] = None,
        max_recovery_attempts: int = 3,
        backoff_multiplier: float = 1.0,
    ):
        """
        Initialize the Auto Recovery Engine

        Args:
            strategies: List of enabled recovery strategies
            max_recovery_attempts: Maximum recovery attempts per worker
            backoff_multiplier: Backoff time multiplier
        """
        self.enabled_strategies = strategies or [RecoveryStrategy.RESTART]
        self.max_recovery_attempts = max_recovery_attempts
        self.backoff_multiplier = backoff_multiplier

        # Recovery event handlers
        self._recovery_handlers: List[Callable] = []

        # Strategy manager
        self._strategy_manager: Optional[RecoveryStrategyManager] = None

    async def attempt_recovery(self, worker_state: WorkerState) -> RecoveryResult:
        """
        Attempt to recover an unhealthy worker

        Args:
            worker_state: Current worker state

        Returns:
            RecoveryResult object
        """
        # Check if max attempts exceeded
        if worker_state.recovery_attempts >= self.max_recovery_attempts:
            return RecoveryResult(
                success=False,
                worker_id=worker_state.worker_id,
                action=RecoveryAction.NONE,
                attempts=worker_state.recovery_attempts,
                reason="max_attempts_exceeded",
            )

        # Calculate backoff time
        if worker_state.last_recovery:
            backoff_time = self.calculate_backoff_time(worker_state)
            time_since_last = (
                datetime.now() - worker_state.last_recovery
            ).total_seconds()
            if time_since_last < backoff_time:
                return RecoveryResult(
                    success=False,
                    worker_id=worker_state.worker_id,
                    action=RecoveryAction.NONE,
                    attempts=worker_state.recovery_attempts,
                    reason=f"backoff_period (wait {backoff_time - time_since_last:0.1f}s)",
                )

        # Try recovery strategies
        attempts = 0
        for strategy in self.enabled_strategies:
            attempts += 1

            # Emit recovery attempt event
            await self._emit_recovery_attempt(
                worker_state.worker_id, RecoveryAction.RESTART
            )

            # Execute recovery action
            success = await self._execute_recovery_action(strategy, worker_state)

            if success:
                worker_state.recovery_attempts += 1
                worker_state.last_recovery = datetime.now()

                return RecoveryResult(
                    success=True,
                    worker_id=worker_state.worker_id,
                    action=RecoveryAction.RESTART,
                    attempts=attempts,
                )

        # All strategies failed
        worker_state.recovery_attempts += 1
        worker_state.last_recovery = datetime.now()

        return RecoveryResult(
            success=False,
            worker_id=worker_state.worker_id,
            action=RecoveryAction.NONE,
            attempts=attempts,
            reason="all_strategies_failed",
        )

    async def _execute_recovery_action(
        self, strategy: RecoveryStrategy, worker_state: WorkerState
    ) -> bool:
        """
        Execute a recovery action

        Args:
            strategy: Recovery strategy to execute
            worker_state: Current worker state

        Returns:
            True if successful, False otherwise
        """
        try:
            if strategy == RecoveryStrategy.RESTART:
                return await self._restart_worker(worker_state)
            elif strategy == RecoveryStrategy.RESET:
                return await self._reset_worker(worker_state)
            elif strategy == RecoveryStrategy.RECREATE:
                return await self._recreate_worker(worker_state)
            else:
                logger.warning(f"Unknown recovery strategy: {strategy}")
                return False
        except Exception as e:
            logger.error(f"Recovery action failed: {e}")
            return False

    async def _restart_worker(self, worker_state: WorkerState) -> bool:
        """Restart a worker"""
        try:
            # Get restart command from worker metadata
            restart_command = worker_state.metadata.get("restart_command")
            if not restart_command:
                logger.error(f"No restart command for worker {worker_state.worker_id}")
                return False

            # Execute restart command
            result = subprocess.run(
                restart_command, shell=True, capture_output=True, text=True
            )

            return result.returncode == 0

        except Exception as e:
            logger.error(f"Failed to restart worker {worker_state.worker_id}: {e}")
            return False

    async def _reset_worker(self, worker_state: WorkerState) -> bool:
        """Reset a worker (clear state and restart)"""
        # Implementation would clear worker state/cache before restart
        return await self._restart_worker(worker_state)

    async def _recreate_worker(self, worker_state: WorkerState) -> bool:
        """Recreate a worker (destroy and create new)"""
        # Implementation would destroy and recreate worker container/process
        return await self._restart_worker(worker_state)

    def calculate_backoff_time(self, worker_state: WorkerState) -> float:
        """
        Calculate backoff time for recovery attempts

        Args:
            worker_state: Current worker state

        Returns:
            Backoff time in seconds
        """
        base_time = 1.0
        return base_time * (self.backoff_multiplier**worker_state.recovery_attempts)

    async def handle_health_change(self, event: Dict[str, Any]):
        """
        Handle health change events from monitor

        Args:
            event: Health change event
        """
        if event["new_status"] == HealthStatus.UNHEALTHY:
            worker_id = event["worker_id"]
            # Get worker state from event if available
            if "worker_state" in event:
                worker_state = event["worker_state"]
            else:
                # Create a dummy state
                worker_state = WorkerState(
                    worker_id=worker_id,
                    status=HealthStatus.UNHEALTHY,
                    last_health_check=datetime.now(),
                )
            await self.attempt_recovery(worker_state)

    def on_recovery_attempt(self, handler: Callable):
        """Register a recovery attempt event handler"""
        self._recovery_handlers.append(handler)

    async def _emit_recovery_attempt(self, worker_id: str, action: RecoveryAction):
        """Emit recovery attempt event"""
        event = {"worker_id": worker_id, "action": action, "timestamp": datetime.now()}

        for handler in self._recovery_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in recovery handler: {e}")

    def set_strategy_manager(self, manager: "RecoveryStrategyManager"):
        """Set the strategy manager"""
        self._strategy_manager = manager


class RecoveryStrategyManager:
    """Recovery Strategy Manager class"""

    def __init__(self):
        """Initialize the Recovery Strategy Manager"""
        self.strategies: Dict[RecoveryStrategy, StrategyInfo] = {}
        self._register_default_strategies()

    def _register_default_strategies(self):
        """Register default recovery strategies"""
        self.register_strategy(
            RecoveryStrategy.RESTART, self._default_restart_strategy, priority=1
        )
        self.register_strategy(
            RecoveryStrategy.RESET, self._default_reset_strategy, priority=2
        )
        self.register_strategy(
            RecoveryStrategy.RECREATE, self._default_recreate_strategy, priority=3
        )

    async def _default_restart_strategy(self, worker_state: WorkerState) -> bool:
        """Default restart strategy"""
        return True  # Placeholder

    async def _default_reset_strategy(self, worker_state: WorkerState) -> bool:
        """Default reset strategy"""
        return True  # Placeholder

    async def _default_recreate_strategy(self, worker_state: WorkerState) -> bool:
        """Default recreate strategy"""
        return True  # Placeholder

    def register_strategy(
        self, strategy: RecoveryStrategy, handler: Callable, priority: int = 0
    ):
        """
        Register a recovery strategy

        Args:
            strategy: Recovery strategy type
            handler: Strategy handler function
            priority: Strategy priority (lower = higher priority)
        """
        self.strategies[strategy] = StrategyInfo(
            strategy=strategy, handler=handler, priority=priority
        )

    def get_available_strategies(self) -> List[RecoveryStrategy]:
        """Get list of available strategies"""
        return list(self.strategies.keys())

    def get_strategies_by_priority(self) -> List[StrategyInfo]:
        """Get strategies sorted by priority"""
        return sorted(self.strategies.values(), key=lambda x: x.priority)

    def select_strategy(self, worker_state: WorkerState) -> Optional[StrategyInfo]:
        """
        Select appropriate strategy based on worker state

        Args:
            worker_state: Current worker state

        Returns:
            Selected strategy info or None
        """
        # Simple selection based on failure reason
        if (
            worker_state.failure_reason
            and "memory" in worker_state.failure_reason.lower()
        ):
            return self.strategies.get(RecoveryStrategy.RESET)

        # Default to restart
        return self.strategies.get(RecoveryStrategy.RESTART)

    async def execute_strategy(
        self, strategy: RecoveryStrategy, worker_state: WorkerState
    ) -> bool:
        """
        Execute a specific strategy

        Args:
            strategy: Strategy to execute
            worker_state: Current worker state

        Returns:
            True if successful, False otherwise
        """
        strategy_info = self.strategies.get(strategy)
        if not strategy_info:
            logger.error(f"Strategy {strategy} not found")
            return False

        try:
            return await strategy_info.handler(worker_state)
        except Exception as e:
            logger.error(f"Strategy execution failed: {e}")
            return False


class HealthCheckService:
    """Health Check Service class"""

    def __init__(self, port: int = 8080):
        """
        Initialize the Health Check Service

        Args:
            port: Port to run the service on
        """
        self.port = port
        self.is_running = False
        self.app = web.Application()
        self._setup_routes()

        # Monitors
        self._monitors: List[Any] = []
        self._health_monitor: Optional[WorkerHealthMonitor] = None

    def _setup_routes(self):
        """Setup HTTP routes"""
        self.app.router.add_get("/health", self.handle_health)
        self.app.router.add_get("/health/worker/{worker_id}", self.handle_worker_health)
        self.app.router.add_get("/metrics", self.handle_metrics)
        self.app.router.add_get("/metrics/prometheus", self.handle_prometheus_metrics)

    async def start(self):
        """Start the health check service"""
        self.is_running = True
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", self.port)
        await site.start()
        logger.info(f"Health check service started on port {self.port}")

    async def handle_health(self, request: web.Request) -> web.Response:
        """Handle general health endpoint"""
        data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "worker-auto-recovery",
        }
        return web.Response(
            text=json.dumps(data), content_type="application/json", status=200
        )

    async def handle_worker_health(self, request: web.Request) -> web.Response:
        """Handle worker-specific health endpoint"""
        worker_id = request.match_info["worker_id"]

        worker_status = await self.get_worker_status(worker_id)

        return web.Response(
            text=json.dumps(worker_status),
            content_type="application/json",
            status=200 if worker_status["status"] == "healthy" else 503,
        )

    async def handle_metrics(self, request: web.Request) -> web.Response:
        """Handle metrics endpoint"""
        metrics = await self.collect_metrics()

        return web.Response(
            text=json.dumps(metrics), content_type="application/json", status=200
        )

    async def handle_prometheus_metrics(self, request: web.Request) -> web.Response:
        """Handle Prometheus metrics endpoint"""
        metrics = await self.collect_metrics()

        # Convert to Prometheus format
        prometheus_metrics = []

        # Worker health status
        for worker_id, worker_data in metrics.get("workers", {}).items():
            status_value = 1 if worker_data["status"] == "healthy" else 0
            prometheus_metrics.append(
                f'worker_health_status{{worker_id="{worker_id}"}} {status_value}'
            )

            # CPU usage
            if "cpu" in worker_data:
                prometheus_metrics.append(
                    f'worker_cpu_usage{{worker_id="{worker_id}"}} {worker_data["cpu"]}'
                )

            # Memory usage
            if "memory" in worker_data:
                prometheus_metrics.append(
                    f'worker_memory_usage{{worker_id="{worker_id}"}} {worker_data["memory"]}'
                )

        # System metrics
        system_metrics = metrics.get("system", {})
        prometheus_metrics.append(
            f'system_total_workers {system_metrics.get("total_workers", 0)}'
        )
        prometheus_metrics.append(
            f'system_healthy_workers {system_metrics.get("healthy_workers", 0)}'
        )

        return web.Response(
            text="\n".join(prometheus_metrics), content_type="text/plain", status=200
        )

    async def get_worker_status(self, worker_id: str) -> Dict[str, Any]:
        """Get status of a specific worker"""
        if self._health_monitor:
            worker_state = self._health_monitor.get_worker_state(worker_id)
            if worker_state:
                return {
                    "worker_id": worker_id,
                    "status": worker_state.status.value,
                    "last_check": worker_state.last_health_check.isoformat(),
                    "consecutive_failures": worker_state.consecutive_failures,
                    "recovery_attempts": worker_state.recovery_attempts,
                }

        return {
            "worker_id": worker_id,
            "status": "unknown",
            "error": "Worker not found",
        }

    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect system and worker metrics"""
        metrics = {
            "workers": {},
            "system": {"total_workers": 0, "healthy_workers": 0, "uptime": 0},
            "timestamp": datetime.now().isoformat(),
        }

        if self._health_monitor:
            for worker_id in self._health_monitor.get_tracked_workers():
                worker_state = self._health_monitor.get_worker_state(worker_id)
                if worker_state:
                    metrics["workers"][worker_id] = {
                        "status": worker_state.status.value,
                        "cpu": 0,  # Would get from actual monitoring
                        "memory": 0,  # Would get from actual monitoring
                    }
                    metrics["system"]["total_workers"] += 1
                    if worker_state.status == HealthStatus.HEALTHY:
                        metrics["system"]["healthy_workers"] += 1

        return metrics

    def register_monitor(self, monitor: Any):
        """Register a monitor for integration"""
        self._monitors.append(monitor)

    def set_health_monitor(self, monitor: WorkerHealthMonitor):
        """Set the health monitor"""
        self._health_monitor = monitor

    async def update_health_status(self, worker_id: str, status: HealthStatus):
        """Update health status and notify monitors"""
        for monitor in self._monitors:
            if hasattr(monitor, "update_worker_health"):
                monitor.update_worker_health(worker_id, status)
