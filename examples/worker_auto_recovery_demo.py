#!/usr/bin/env python3
"""
Worker Auto-Recovery System Demo

This script demonstrates the functionality of the Worker Auto-Recovery System
implemented following TDD principles based on Elder Council's guidance.
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.worker_auto_recovery import (
    AutoRecoveryEngine,
    HealthCheckService,
    HealthStatus,
    RecoveryStrategy,
    RecoveryStrategyManager,
    WorkerHealthMonitor,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


async def simulate_worker_failure(monitor: WorkerHealthMonitor, worker_id: str):
    """Simulate a worker failure scenario"""
    logger.info(f"🔴 Simulating failure for worker {worker_id}")

    # Mock the health check to return False (unhealthy)
    original_check = monitor._check_worker_health

    async def failing_health_check(wid):
        if wid == worker_id:
            return False
        return await original_check(wid)

    monitor._check_worker_health = failing_health_check

    # Wait for a few health checks
    await asyncio.sleep(monitor.check_interval * 4)

    # Restore original health check
    monitor._check_worker_health = original_check
    logger.info(f"🟢 Restored normal operation for worker {worker_id}")


async def main():
    """Main demo function"""
    logger.info("🚀 Starting Worker Auto-Recovery System Demo")

    # 1. Initialize components
    logger.info("📦 Initializing components...")

    # Configure monitor with custom settings
    monitor_config = {
        "check_interval": 5,  # Check every 5 seconds
        "failure_threshold": 2,  # Mark unhealthy after 2 failures
        "timeout": 3,
    }
    monitor = WorkerHealthMonitor(config=monitor_config)

    # Initialize recovery engine
    recovery_engine = AutoRecoveryEngine(
        strategies=[RecoveryStrategy.RESTART, RecoveryStrategy.RESET],
        max_recovery_attempts=3,
        backoff_multiplier=2.0,
    )

    # Initialize strategy manager
    strategy_manager = RecoveryStrategyManager()
    recovery_engine.set_strategy_manager(strategy_manager)

    # Initialize health check service
    health_service = HealthCheckService(port=8888)
    health_service.set_health_monitor(monitor)

    # 2. Connect components
    logger.info("🔗 Connecting components...")

    # Track recovery events
    recovery_events = []

    async def track_recovery(event):
        """track_recoveryメソッド"""
        recovery_events.append(event)
        logger.info(
            f"🔧 Recovery attempt: {event['worker_id']} - {event['action'].value}"
        )

    recovery_engine.on_recovery_attempt(track_recovery)

    # Connect monitor to recovery engine
    monitor.on_health_change(recovery_engine.handle_health_change)

    # 3. Register workers
    logger.info("👷 Registering workers...")
    workers = [
        {
            "id": "task_worker_1",
            "config": {
                "type": "task",
                "critical": True,
                "health_check_endpoint": "http://localhost:8001/health",
                "restart_command": 'echo "Restarting task_worker_1"',
            },
        },
        {
            "id": "pm_worker_1",
            "config": {
                "type": "pm",
                "critical": True,
                "health_check_endpoint": "http://localhost:8002/health",
                "restart_command": 'echo "Restarting pm_worker_1"',
            },
        },
        {
            "id": "result_worker_1",
            "config": {
                "type": "result",
                "critical": False,
                "health_check_endpoint": "http://localhost:8003/health",
                "restart_command": 'echo "Restarting result_worker_1"',
            },
        },
    ]

    for worker in workers:
        await monitor.register_worker(worker["id"], worker["config"])
        logger.info(f"✅ Registered {worker['id']}")

    # 4. Start services
    logger.info("🏃 Starting services...")

    # Start monitoring
    await monitor.start_monitoring()

    # Start health check service
    await health_service.start()
    logger.info(
        f"📊 Health check service running on http://localhost:{health_service.port}/health"
    )
    logger.info(
        f"📈 Metrics available at http://localhost:{health_service.port}/metrics"
    )
    logger.info(
        f"📉 Prometheus metrics at http://localhost:{health_service.port}/metrics/prometheus"
    )

    # 5. Demonstrate functionality
    logger.info("🎭 Starting demonstration...")

    # Let system run normally for a bit
    await asyncio.sleep(10)

    # Check initial status
    logger.info("📋 Initial worker status:")
    for worker_id in monitor.get_tracked_workers():
        state = monitor.get_worker_state(worker_id)
        logger.info(f"  - {worker_id}: {state.status.value}")

    # Simulate worker failure
    await simulate_worker_failure(monitor, "task_worker_1")

    # Wait for recovery attempts
    await asyncio.sleep(20)

    # Check final status
    logger.info("📋 Final worker status:")
    for worker_id in monitor.get_tracked_workers():
        state = monitor.get_worker_state(worker_id)
        logger.info(
            f"  - {worker_id}: {state.status.value} (failures: {state.consecutive_failures}, " \
                "recoveries: {state.recovery_attempts})"
        )

    # Show recovery events
    logger.info(f"🔧 Total recovery attempts: {len(recovery_events)}")

    # Show metrics
    metrics = await health_service.collect_metrics()
    logger.info(f"📊 System metrics: {metrics['system']}")

    # 6. Cleanup
    logger.info("🧹 Shutting down...")
    await monitor.stop_monitoring()

    logger.info("✅ Demo completed successfully!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Demo interrupted by user")
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        raise
