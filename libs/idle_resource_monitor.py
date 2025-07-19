#!/usr/bin/env python3
"""
🔍 Idle Resource Monitor - System Resource and Activity Detection
Monitors system resources and detects idle periods for automated tasks
"""

import json
import logging
import queue
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psutil


@dataclass
class ResourceMetrics:
    """System resource metrics snapshot"""

    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_io_read: int
    disk_io_write: int
    network_sent: int
    network_recv: int
    process_count: int
    load_avg_1m: float

    def is_idle(self, thresholds: Dict[str, float]) -> bool:
        """Check if system is considered idle based on thresholds"""
        return (
            self.cpu_percent < thresholds.get("cpu", 20.0)
            and self.memory_percent < thresholds.get("memory", 80.0)
            and self.load_avg_1m < thresholds.get("load", 1.0)
        )


@dataclass
class IdlePeriod:
    """Represents a detected idle period"""

    start_time: str
    end_time: Optional[str]
    duration_seconds: float
    avg_cpu: float
    avg_memory: float
    confidence: float  # 0.0 to 1.0


class IdleResourceMonitor:
    """
    Monitors system resources and detects idle periods suitable for automated tasks
    """

    def __init__(
        self,
        check_interval: int = 30,
        history_size: int = 100,
        idle_thresholds: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize the idle resource monitor

        Args:
            check_interval: Seconds between resource checks
            history_size: Number of metrics to keep in memory
            idle_thresholds: Custom thresholds for idle detection
        """
        self.check_interval = check_interval
        self.history_size = history_size
        self.idle_thresholds = idle_thresholds or {
            "cpu": 15.0,  # CPU usage below 15%
            "memory": 75.0,  # Memory usage below 75%
            "load": 0.8,  # Load average below 0.8
            "min_duration": 300,  # Minimum idle duration (5 minutes)
        }

        self.metrics_history: deque = deque(maxlen=history_size)
        self.current_idle_period: Optional[IdlePeriod] = None
        self.idle_periods: List[IdlePeriod] = []
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.event_queue = queue.Queue()

        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Base metrics for delta calculations
        self.last_disk_io = psutil.disk_io_counters()
        self.last_network = psutil.net_io_counters()

    def collect_metrics(self) -> ResourceMetrics:
        """Collect current system resource metrics"""
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            # Disk I/O
            current_disk = psutil.disk_io_counters()
            disk_read_delta = current_disk.read_bytes - self.last_disk_io.read_bytes
            disk_write_delta = current_disk.write_bytes - self.last_disk_io.write_bytes
            self.last_disk_io = current_disk

            # Network I/O
            current_network = psutil.net_io_counters()
            net_sent_delta = current_network.bytes_sent - self.last_network.bytes_sent
            net_recv_delta = current_network.bytes_recv - self.last_network.bytes_recv
            self.last_network = current_network

            # Process count and load
            process_count = len(psutil.pids())
            load_avg = psutil.getloadavg()[0] if hasattr(psutil, "getloadavg") else 0.0

            return ResourceMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_io_read=disk_read_delta,
                disk_io_write=disk_write_delta,
                network_sent=net_sent_delta,
                network_recv=net_recv_delta,
                process_count=process_count,
                load_avg_1m=load_avg,
            )

        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            # Return default metrics on error
            return ResourceMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=100.0,  # High values to prevent false idle detection
                memory_percent=100.0,
                disk_io_read=0,
                disk_io_write=0,
                network_sent=0,
                network_recv=0,
                process_count=0,
                load_avg_1m=10.0,
            )

    def analyze_idle_state(self, metrics: ResourceMetrics) -> bool:
        """Analyze if system is currently idle"""
        return metrics.is_idle(self.idle_thresholds)

    def update_idle_period(self, metrics: ResourceMetrics, is_idle: bool):
        """Update current idle period tracking"""
        now = datetime.fromisoformat(metrics.timestamp)

        if is_idle:
            if self.current_idle_period is None:
                # Start new idle period
                self.current_idle_period = IdlePeriod(
                    start_time=metrics.timestamp,
                    end_time=None,
                    duration_seconds=0.0,
                    avg_cpu=metrics.cpu_percent,
                    avg_memory=metrics.memory_percent,
                    confidence=0.5,
                )
                self.logger.info("🟢 Idle period started")
            else:
                # Update existing idle period
                start_time = datetime.fromisoformat(self.current_idle_period.start_time)
                duration = (now - start_time).total_seconds()

                # Update averages (simple moving average)
                sample_count = max(1, duration // self.check_interval)
                self.current_idle_period.avg_cpu = (
                    self.current_idle_period.avg_cpu * (sample_count - 1)
                    + metrics.cpu_percent
                ) / sample_count
                self.current_idle_period.avg_memory = (
                    self.current_idle_period.avg_memory * (sample_count - 1)
                    + metrics.memory_percent
                ) / sample_count
                self.current_idle_period.duration_seconds = duration

                # Update confidence based on duration and stability
                min_duration = self.idle_thresholds.get("min_duration", 300)
                self.current_idle_period.confidence = min(1.0, duration / min_duration)

        else:
            if self.current_idle_period is not None:
                # End idle period
                self.current_idle_period.end_time = metrics.timestamp

                # Only keep idle periods that meet minimum duration
                min_duration = self.idle_thresholds.get("min_duration", 300)
                if self.current_idle_period.duration_seconds >= min_duration:
                    self.idle_periods.append(self.current_idle_period)
                    self.logger.info(
                        f"🔴 Idle period ended: {self.current_idle_period.duration_seconds:.1f}s "
                        f"(confidence: {self.current_idle_period.confidence:.2f})"
                    )

                    # Notify about idle period
                    self.event_queue.put(
                        {
                            "type": "idle_period_completed",
                            "period": asdict(self.current_idle_period),
                            "suitable_for_tasks": self.current_idle_period.confidence
                            > 0.7,
                        }
                    )

                self.current_idle_period = None

    def get_current_idle_status(self) -> Dict:
        """Get current idle status information"""
        if not self.metrics_history:
            return {
                "is_idle": False,
                "confidence": 0.0,
                "duration": 0.0,
                "suitable_for_tasks": False,
            }

        latest_metrics = self.metrics_history[-1]
        is_idle = self.analyze_idle_state(latest_metrics)

        status = {
            "is_idle": is_idle,
            "current_metrics": asdict(latest_metrics),
            "thresholds": self.idle_thresholds,
        }

        if self.current_idle_period:
            status.update(
                {
                    "confidence": self.current_idle_period.confidence,
                    "duration": self.current_idle_period.duration_seconds,
                    "suitable_for_tasks": self.current_idle_period.confidence > 0.7,
                }
            )
        else:
            status.update(
                {"confidence": 0.0, "duration": 0.0, "suitable_for_tasks": False}
            )

        return status

    def get_idle_history(self, hours: int = 24) -> List[IdlePeriod]:
        """Get idle periods from the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        return [
            period
            for period in self.idle_periods
            if datetime.fromisoformat(period.start_time) >= cutoff_time
        ]

    def predict_next_idle_window(self) -> Optional[Dict]:
        """Predict when the next good idle window might occur"""
        if len(self.idle_periods) < 3:
            return None

        # Analyze patterns in recent idle periods
        recent_periods = self.get_idle_history(hours=48)
        if not recent_periods:
            return None

        # Calculate average time between idle periods
        intervals = []
        for i in range(1, len(recent_periods)):
            start_curr = datetime.fromisoformat(recent_periods[i].start_time)
            end_prev = datetime.fromisoformat(recent_periods[i - 1].end_time)
            intervals.append((start_curr - end_prev).total_seconds())

        if not intervals:
            return None

        avg_interval = sum(intervals) / len(intervals)
        last_period = recent_periods[-1]

        if last_period.end_time:
            last_end = datetime.fromisoformat(last_period.end_time)
            predicted_next = last_end + timedelta(seconds=avg_interval)

            return {
                "predicted_start": predicted_next.isoformat(),
                "confidence": min(
                    0.8, len(recent_periods) / 10
                ),  # More data = higher confidence
                "based_on_periods": len(recent_periods),
            }

        return None

    def start_monitoring(self):
        """Start background monitoring"""
        if self.is_monitoring:
            self.logger.warning("Monitoring already started")
            return

        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self.monitor_thread.start()
        self.logger.info(
            f"🔍 Started resource monitoring (interval: {self.check_interval}s)"
        )

    def stop_monitoring(self):
        """Stop background monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("🛑 Stopped resource monitoring")

    def _monitoring_loop(self):
        """Main monitoring loop (runs in background thread)"""
        while self.is_monitoring:
            try:
                # Collect metrics
                metrics = self.collect_metrics()
                self.metrics_history.append(metrics)

                # Analyze idle state
                is_idle = self.analyze_idle_state(metrics)
                self.update_idle_period(metrics, is_idle)

                # Sleep until next check
                time.sleep(self.check_interval)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.check_interval)

    def save_state(self, filepath: str):
        """Save current monitoring state to file"""
        state = {
            "metrics_history": [asdict(m) for m in self.metrics_history],
            "idle_periods": [asdict(p) for p in self.idle_periods],
            "current_idle_period": asdict(self.current_idle_period)
            if self.current_idle_period
            else None,
            "idle_thresholds": self.idle_thresholds,
            "last_updated": datetime.now().isoformat(),
        }

        try:
            with open(filepath, "w") as f:
                json.dump(state, f, indent=2)
            self.logger.info(f"💾 State saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving state: {e}")

    def load_state(self, filepath: str):
        """Load monitoring state from file"""
        try:
            with open(filepath, "r") as f:
                state = json.load(f)

            # Restore metrics history
            self.metrics_history.clear()
            for m_dict in state.get("metrics_history", []):
                self.metrics_history.append(ResourceMetrics(**m_dict))

            # Restore idle periods
            self.idle_periods = [
                IdlePeriod(**p_dict) for p_dict in state.get("idle_periods", [])
            ]

            # Restore current idle period
            current_dict = state.get("current_idle_period")
            if current_dict:
                self.current_idle_period = IdlePeriod(**current_dict)

            # Restore thresholds
            self.idle_thresholds.update(state.get("idle_thresholds", {}))

            self.logger.info(f"📂 State loaded from {filepath}")

        except Exception as e:
            self.logger.error(f"Error loading state: {e}")


def main():
    """CLI interface for testing"""
    import argparse

    parser = argparse.ArgumentParser(description="Idle Resource Monitor")
    parser.add_argument(
        "--interval", type=int, default=30, help="Check interval in seconds"
    )
    parser.add_argument(
        "--duration", type=int, default=300, help="Test duration in seconds"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Create monitor
    monitor = IdleResourceMonitor(check_interval=args.interval)

    try:
        print("🔍 Starting idle resource monitoring...")
        print(f"⏱️  Check interval: {args.interval}s")
        print(f"⏰ Test duration: {args.duration}s")
        print("Press Ctrl+C to stop")

        monitor.start_monitoring()

        # Monitor for specified duration
        start_time = time.time()
        while time.time() - start_time < args.duration:
            time.sleep(5)

            status = monitor.get_current_idle_status()
            if status["is_idle"]:
                print(
                    f"🟢 IDLE - Duration: {status['duration']:.1f}s, "
                    f"Confidence: {status['confidence']:.2f}"
                )
            else:
                metrics = status["current_metrics"]
                print(
                    f"🔴 BUSY - CPU: {metrics['cpu_percent']:.1f}%, "
                    f"Memory: {metrics['memory_percent']:.1f}%"
                )

    except KeyboardInterrupt:
        print("\n⏹️  Stopping monitoring...")
    finally:
        monitor.stop_monitoring()

        # Print summary
        idle_periods = monitor.get_idle_history()
        if idle_periods:
            total_idle_time = sum(p.duration_seconds for p in idle_periods)
            print(f"\n📊 Summary:")
            print(f"   Idle periods detected: {len(idle_periods)}")
            print(f"   Total idle time: {total_idle_time:.1f}s")
            print(f"   Average idle duration: {total_idle_time/len(idle_periods):.1f}s")


if __name__ == "__main__":
    main()
