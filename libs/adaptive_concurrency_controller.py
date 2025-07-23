"""
Adaptive Concurrency Controller for Auto Issue Processor A2A
Phase 2 implementation for dynamic parallelism adjustment
"""
import asyncio
import time
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import psutil
import numpy as np
from collections import deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConcurrencyMetrics:
    """System metrics for concurrency decisions"""
    cpu_percent: float
    memory_percent: float
    active_workers: int
    queue_size: int
    avg_processing_time: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'active_workers': self.active_workers,
            'queue_size': self.queue_size,
            'avg_processing_time': self.avg_processing_time
        }


@dataclass
class ScalingDecision:
    """Scaling decision result"""
    should_scale: bool
    direction: str  # 'up', 'down', or 'stable'
    new_worker_count: int
    reason: str


class ResourceMonitor:
    """Monitor system resources"""
    
    def __init__(self):
        """初期化メソッド"""
        self.cpu_history = deque(maxlen=60)  # 1 minute history
        self.memory_history = deque(maxlen=60)
        self.io_history = deque(maxlen=60)
    
    def get_snapshot(self) -> Dict:
        """Get current resource snapshot"""
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory().percent
        io = psutil.disk_io_counters() if hasattr(psutil, 'disk_io_counters') else None
        net = psutil.net_io_counters() if hasattr(psutil, 'net_io_counters') else None
        
        snapshot = {
            'cpu_percent': cpu,
            'memory_percent': memory,
            'timestamp': datetime.now()
        }
        
        if io:
            snapshot['io_counters'] = {
                'read_bytes': io.read_bytes,
                'write_bytes': io.write_bytes
            }
        
        if net:
            snapshot['network_io'] = {
                'bytes_sent': net.bytes_sent,
                'bytes_recv': net.bytes_recv
            }
        
        # Update history
        self.cpu_history.append(cpu)
        self.memory_history.append(memory)
        
        return snapshot
    
    def get_trends(self) -> Dict:
        """Get resource usage trends"""
        if len(self.cpu_history) < 2:
            return {'cpu_trend': 'stable', 'memory_trend': 'stable'}
        
        cpu_trend = np.mean(list(self.cpu_history)[-5:]) - np.mean(list(self.cpu_history)[-10:-5])
        memory_trend = np.mean(list(self.memory_history)[-5:]) - np.mean(list(self.memory_history)[-10:-5])
        
        return {
            'cpu_trend': 'increasing' if cpu_trend > 5 else 'decreasing' if cpu_trend < -5 else 'stable',
            'memory_trend': 'increasing' if memory_trend > 5 else 'decreasing' if memory_trend < -5 else 'stable'
        }


class MLPredictor:
    """Machine learning based workload predictor"""
    
    def __init__(self):
        """初期化メソッド"""
        self.history = deque(maxlen=1000)
    
    def add_observation(self, metrics: ConcurrencyMetrics, decision: str):
        """Add observation for learning"""
        self.history.append({
            'metrics': metrics.to_dict(),
            'decision': decision,
            'timestamp': datetime.now()
        })
    
    def predict_optimal_workers(self, current_metrics: ConcurrencyMetrics, 
                              min_workers: int, max_workers: int) -> int:
        """Predict optimal worker count based on history"""
        if len(self.history) < 10:
            # Not enough data, use simple heuristic
            if current_metrics.cpu_percent > 80:
                return min(current_metrics.active_workers + 2, max_workers)
            elif current_metrics.cpu_percent < 40:
                return max(current_metrics.active_workers - 1, min_workers)
            return current_metrics.active_workers
        
        # Simple prediction based on recent similar situations
        similar_situations = []
        for obs in self.history:
            metrics = obs['metrics']
            cpu_diff = abs(metrics['cpu_percent'] - current_metrics.cpu_percent)
            mem_diff = abs(metrics['memory_percent'] - current_metrics.memory_percent)
            
            if cpu_diff < 10 and mem_diff < 10:
                similar_situations.append(obs)
        
        if similar_situations:
            # Average worker count from similar situations
            worker_counts = [s['metrics']['active_workers'] for s in similar_situations]
            optimal = int(np.mean(worker_counts))
            return max(min_workers, min(optimal, max_workers))
        
        # Fallback to simple scaling
        return current_metrics.active_workers


class AdaptiveConcurrencyController:
    """Adaptive concurrency controller with ML-based optimization"""
    
    def __init__(self, min_workers:
        """初期化メソッド"""
    int = 1, max_workers: int = 10,
                 target_cpu_percent: float = 70.0, target_memory_percent: float = 80.0):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.current_workers = min_workers
        self.target_cpu_percent = target_cpu_percent
        self.target_memory_percent = target_memory_percent
        
        self.scaling_history: List[Dict] = []
        self.last_scaling_time = None
        self.cooldown_seconds = 30  # Prevent rapid scaling
        
        self.scaling_strategy = "balanced"  # balanced, aggressive, conservative
        self.queue_threshold = 50
        self.target_processing_time = 2.0
        
        self.resource_monitor = ResourceMonitor()
        self.ml_predictor = MLPredictor()
        
        self._scaling_lock = threading.Lock()
        self._stop_event = threading.Event()
        self.adjustment_interval = 10  # seconds
    
    def get_current_metrics(self) -> ConcurrencyMetrics:
        """Get current system metrics"""
        snapshot = self.resource_monitor.get_snapshot()
        
        # In real implementation, these would come from the actual processor
        # For now, using system metrics and estimates
        return ConcurrencyMetrics(
            cpu_percent=snapshot['cpu_percent'],
            memory_percent=snapshot['memory_percent'],
            active_workers=self.current_workers,
            queue_size=0,  # Would be from actual queue
            avg_processing_time=1.0  # Would be from actual metrics
        )
    
    def should_scale_up(self, metrics: ConcurrencyMetrics) -> ScalingDecision:
        """Determine if should scale up"""
        # Check if at max
        if self.current_workers >= self.max_workers:
            return ScalingDecision(False, "stable", self.current_workers, 
                                 "Already at max workers")
        
        # Check cooldown
        if self._in_cooldown():
            return ScalingDecision(False, "stable", self.current_workers,
                                 "In cooldown period")
        
        # Check various triggers
        reasons = []
        
        if metrics.cpu_percent > self.target_cpu_percent + 10:
            reasons.append("High CPU usage")
        
        if metrics.memory_percent > self.target_memory_percent + 5:
            reasons.append("High memory usage")
        
        if metrics.queue_size > self.queue_threshold:
            reasons.append("High queue size")
        
        if metrics.avg_processing_time > self.target_processing_time:
            reasons.append("High processing time")
        
        if reasons:
            # Determine scaling amount based on strategy
            if self.scaling_strategy == "aggressive":
                increment = min(2, self.max_workers - self.current_workers)
            elif self.scaling_strategy == "conservative":
                increment = 1
            else:  # balanced
                increment = 1 if len(reasons) == 1 else 2
            
            new_count = min(self.current_workers + increment, self.max_workers)
            return ScalingDecision(True, "up", new_count, ", ".join(reasons))
        
        return ScalingDecision(False, "stable", self.current_workers, "Metrics within target")
    
    def should_scale_down(self, metrics: ConcurrencyMetrics) -> ScalingDecision:
        """Determine if should scale down"""
        # Check if at min
        if self.current_workers <= self.min_workers:
            return ScalingDecision(False, "stable", self.current_workers,
                                 "Already at min workers")
        
        # Check cooldown
        if self._in_cooldown():
            return ScalingDecision(False, "stable", self.current_workers,
                                 "In cooldown period")
        
        # Check if significantly under-utilized
        if (metrics.cpu_percent < self.target_cpu_percent - 20 and
            metrics.memory_percent < self.target_memory_percent - 20 and
            metrics.queue_size < self.queue_threshold / 2):
            
            decrement = 1
            new_count = max(self.current_workers - decrement, self.min_workers)
            return ScalingDecision(True, "down", new_count, "Low resource utilization")
        
        return ScalingDecision(False, "stable", self.current_workers, "Metrics within target")
    
    def apply_scaling_decision(self, decision: ScalingDecision) -> bool:
        """Apply scaling decision"""
        if not decision.should_scale:
            return False
        
        # Try to acquire lock
        if not self._scaling_lock.acquire(blocking=False):
            return False  # Another scaling operation in progress
        
        try:
            self.current_workers = decision.new_worker_count
            self.last_scaling_time = datetime.now()
            
            # Record in history
            self.scaling_history.append({
                'timestamp': self.last_scaling_time,
                'direction': decision.direction,
                'new_count': decision.new_worker_count,
                'reason': decision.reason,
                'metrics': self.get_current_metrics().to_dict()
            })
            
            # Update ML predictor
            self.ml_predictor.add_observation(
                self.get_current_metrics(), 
                decision.direction
            )
            
            logger.info(f"Scaled {decision.direction} to {decision.new_worker_count} workers: {decision.reason}")
            return True
            
        finally:
            self._scaling_lock.release()
    
    def _in_cooldown(self) -> bool:
        """Check if in cooldown period"""
        if not self.last_scaling_time:
            return False
        
        elapsed = (datetime.now() - self.last_scaling_time).total_seconds()
        return elapsed < self.cooldown_seconds
    
    async def auto_adjust_loop(self):
        """Automatic adjustment loop"""
        while not self._stop_event.is_set():
            try:
                metrics = self.get_current_metrics()
                
                # Check if should scale up
                up_decision = self.should_scale_up(metrics)
                if up_decision.should_scale:
                    self.apply_scaling_decision(up_decision)
                else:
                    # Check if should scale down
                    down_decision = self.should_scale_down(metrics)
                    if down_decision.should_scale:
                        self.apply_scaling_decision(down_decision)
                
                await asyncio.sleep(self.adjustment_interval)
                
            except Exception as e:
                logger.error(f"Error in auto-adjust loop: {e}")
                await asyncio.sleep(self.adjustment_interval)
    
    def stop_auto_adjust(self):
        """Stop automatic adjustment"""
        self._stop_event.set()
    
    def predict_optimal_workers(self) -> int:
        """Predict optimal worker count using ML"""
        current_metrics = self.get_current_metrics()
        return self.ml_predictor.predict_optimal_workers(
            current_metrics, self.min_workers, self.max_workers
        )
    
    def get_scaling_history(self, limit: int = 10) -> List[Dict]:
        """Get recent scaling history"""
        return list(reversed(self.scaling_history))[:limit]
    
    def reset(self):
        """Reset controller to initial state"""
        self.current_workers = self.min_workers
        self.scaling_history = []
        self.last_scaling_time = None
        self.resource_monitor = ResourceMonitor()
        self.ml_predictor = MLPredictor()
    
    def export_metrics(self) -> Dict:
        """Export metrics for monitoring"""
        return {
            'current_workers': self.current_workers,
            'min_workers': self.min_workers,
            'max_workers': self.max_workers,
            'target_cpu_percent': self.target_cpu_percent,
            'target_memory_percent': self.target_memory_percent,
            'scaling_strategy': self.scaling_strategy,
            'scaling_history_count': len(self.scaling_history),
            'last_scaling_timestamp': self.last_scaling_time.isoformat() if self.last_scaling_time else None
        }