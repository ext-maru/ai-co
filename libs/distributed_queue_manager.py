"""
Distributed Queue Manager for Auto Issue Processor A2A
Phase 2 implementation - Advanced queue management with priority, DLQ, and backpressure
"""
import asyncio
import time
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum, IntEnum
import heapq
import threading
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


class QueuePriority(IntEnum):
    """Queue item priority levels"""
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


@dataclass
class QueueItem:
    """Item in the queue"""
    id: str
    data: Dict[str, Any]
    priority: QueuePriority = QueuePriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    max_retries: int = 3
    ttl_seconds: Optional[float] = None
    partition: Optional[int] = None
    
    def __lt__(self, other):
        """For priority queue ordering (higher priority first)"""
        return self.priority > other.priority
    
    def is_expired(self) -> bool:
        """Check if item has expired"""
        if not self.ttl_seconds:
            return False
        elapsed = (datetime.now() - self.created_at).total_seconds()
        return elapsed > self.ttl_seconds


@dataclass
class DeadLetterItem:
    """Item in dead letter queue"""
    item: QueueItem
    failure_reason: str
    failed_at: datetime = field(default_factory=datetime.now)


@dataclass
class QueueMetrics:
    """Queue performance metrics"""
    total_enqueued: int = 0
    total_dequeued: int = 0
    current_size: int = 0
    dead_letter_count: int = 0
    avg_wait_time: float = 0.0
    backpressure_events: int = 0
    expired_items: int = 0


@dataclass
class RetryStrategy:
    """Retry configuration"""
    max_attempts: int = 3
    initial_delay: float = 1.0
    backoff_factor: float = 2.0
    max_delay: float = 60.0
    
    def get_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay for given attempt"""
        delay = self.initial_delay * (self.backoff_factor ** (attempt - 1))
        return min(delay, self.max_delay)


@dataclass
class Alert:
    """Queue alert"""
    type: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)


class BackpressureController:
    """Controls backpressure mechanism"""
    
    def __init__(self, threshold:
        """初期化メソッド"""
    float = 0.8):
        self.threshold = threshold
        self.is_active = False
        self.activation_count = 0
    
    def check_pressure(self, current_size: int, max_size: int) -> bool:
        """Check if backpressure should be activated"""
        ratio = current_size / max_size if max_size > 0 else 0
        should_activate = ratio >= self.threshold
        
        if should_activate and not self.is_active:
            self.is_active = True
            self.activation_count += 1
        elif not should_activate and self.is_active:
            self.is_active = False
        
        return self.is_active


class CircuitBreaker:
    """Circuit breaker for downstream protection"""
    
    def __init__(self, failure_threshold:
        """初期化メソッド"""
    int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False
    
    def record_success(self):
        """Record successful operation"""
        self.failure_count = 0
        self.is_open = False
    
    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
    
    def can_proceed(self) -> bool:
        """Check if operations can proceed"""
        if not self.is_open:
            return True
        
        # Check if recovery timeout has passed
        if self.last_failure_time:
            elapsed = (datetime.now() - self.last_failure_time).total_seconds()
            if elapsed > self.recovery_timeout:
                self.is_open = False
                self.failure_count = 0
                return True
        
        return False


class DistributedQueueManager:
    """Advanced queue manager with priority, DLQ, and backpressure"""
    
    def __init__(self, max_size:
        """初期化メソッド"""
    int = 10000, 
                 enable_dead_letter: bool = True,
                 enable_backpressure: bool = True):
        self.max_size = max_size
        self.enable_dead_letter = enable_dead_letter
        self.enable_backpressure = enable_backpressure
        
        # Main priority queue
        self._queue: List[QueueItem] = []
        self._lock = threading.RLock()
        
        # Dead letter queue
        self._dead_letter_queue: List[DeadLetterItem] = []
        
        # Metrics
        self.metrics = QueueMetrics()
        self._wait_times: deque = deque(maxlen=1000)
        
        # Controllers
        self._backpressure = BackpressureController()
        self._circuit_breaker = CircuitBreaker()
        self._retry_strategy = RetryStrategy()
        
        # Persistence
        self._persistence_enabled = False
        self._persistence_path: Optional[str] = None
        
        # Partitioning
        self._partitioned = False
        self._partitions: Dict[int, List[QueueItem]] = {}
        self._partition_count = 1
        
        # Rate limiting
        self._rate_limit: Optional[float] = None
        self._last_dequeue_time = 0.0
        
        # Alerts
        self._alert_thresholds: Dict[str, float] = {}
        self._active_alerts: List[Alert] = []
        
        # Expired items tracking
        self._expired_items: List[QueueItem] = []
    
    async def enqueue(self, item: QueueItem) -> None:
        """Add item to queue"""
        with self._lock:
            # Check backpressure
            if self.enable_backpressure and self._backpressure.check_pressure(
                len(self._queue),
                self.max_size
            ):
                self.metrics.backpressure_events += 1
                raise Exception("Queue backpressure active - cannot enqueue")
            
            # Check queue size
            if len(self._queue) >= self.max_size:
                raise Exception("Queue is full")
            
            # Add to appropriate queue/partition
            if self._partitioned and item.partition is not None:
                partition = item.partition % self._partition_count
                if partition not in self._partitions:
                    self._partitions[partition] = []
                heapq.heappush(self._partitions[partition], item)
            else:
                heapq.heappush(self._queue, item)
            
            self.metrics.total_enqueued += 1
            self.metrics.current_size = len(self._queue)
            
            # Check alerts
            self._check_alerts()
    
    async def enqueue_batch(self, items: List[QueueItem]) -> None:
        """Add multiple items to queue"""
        for item in items:
            await self.enqueue(item)
    
    async def dequeue(self) -> Optional[QueueItem]:
        """Remove and return highest priority item"""
        # Check circuit breaker
        if not self._circuit_breaker.can_proceed():
            raise Exception("Circuit breaker is open")
        
        # Apply rate limiting
        if self._rate_limit:
            await self._apply_rate_limit()
        
        with self._lock:
            # Remove expired items first
            self._remove_expired_items()
            
            if not self._queue:
                return None
            
            item = heapq.heappop(self._queue)
            
            # Update metrics
            self.metrics.total_dequeued += 1
            self.metrics.current_size = len(self._queue)
            
            # Calculate wait time
            wait_time = (datetime.now() - item.created_at).total_seconds()
            self._wait_times.append(wait_time)
            self._update_avg_wait_time()
            
            return item
    
    async def dequeue_batch(self, count: int) -> List[QueueItem]:
        """Remove and return multiple items"""
        items = []
        for _ in range(count):
            item = await self.dequeue()
            if item:
                items.append(item)
            else:
                break
        return items
    
    async def dequeue_filtered(
        self,
        filter_func: Callable[[QueueItem],
        bool]
    ) -> Optional[QueueItem]:
        """Dequeue item matching filter"""
        with self._lock:
            # Find matching item
            for i, item in enumerate(self._queue):
                if filter_func(item):
                    # Remove from heap (inefficient but works)
                    self._queue.pop(i)
                    heapq.heapify(self._queue)
                    
                    self.metrics.total_dequeued += 1
                    self.metrics.current_size = len(self._queue)
                    return item
            
            return None
    
    def size(self) -> int:
        """Get current queue size"""
        with self._lock:
            return len(self._queue)
    
    def is_backpressure_active(self) -> bool:
        """Check if backpressure is active"""
        return self._backpressure.is_active
    
    async def move_to_dead_letter(self, item: QueueItem, reason: str) -> None:
        """Move item to dead letter queue"""
        if not self.enable_dead_letter:
            return
        
        with self._lock:
            dlq_item = DeadLetterItem(item, reason)
            self._dead_letter_queue.append(dlq_item)
            self.metrics.dead_letter_count += 1
    
    def get_dead_letter_items(self) -> List[DeadLetterItem]:
        """Get items in dead letter queue"""
        with self._lock:
            return self._dead_letter_queue.copy()
    
    def set_retry_strategy(self, strategy: RetryStrategy) -> None:
        """Set retry strategy"""
        self._retry_strategy = strategy
    
    def get_metrics(self) -> QueueMetrics:
        """Get queue metrics"""
        with self._lock:
            return QueueMetrics(
                total_enqueued=self.metrics.total_enqueued,
                total_dequeued=self.metrics.total_dequeued,
                current_size=len(self._queue),
                dead_letter_count=self.metrics.dead_letter_count,
                avg_wait_time=self.metrics.avg_wait_time,
                backpressure_events=self.metrics.backpressure_events,
                expired_items=self.metrics.expired_items
            )
    
    def get_expired_items(self) -> List[QueueItem]:
        """Get expired items"""
        with self._lock:
            return self._expired_items.copy()
    
    def enable_persistence(self, path: str) -> None:
        """Enable queue persistence"""
        self._persistence_enabled = True
        self._persistence_path = path
    
    async def save_state(self) -> None:
        """Save queue state to disk"""
        if not self._persistence_enabled:
            return
        
        with self._lock:
            state = {
                'queue': [self._item_to_dict(item) for item in self._queue],
                'metrics': {
                    'total_enqueued': self.metrics.total_enqueued,
                    'total_dequeued': self.metrics.total_dequeued
                }
            }
        
        # Simple JSON persistence (could use SQLite for production)
        with open(self._persistence_path, 'w') as f:
            json.dump(state, f)
    
    async def restore_state(self, path: str) -> None:
        """Restore queue state from disk"""
        try:
            with open(path, 'r') as f:
                state = json.load(f)
            
            with self._lock:
                self._queue = []
                for item_dict in state['queue']:
                    item = self._dict_to_item(item_dict)
                    heapq.heappush(self._queue, item)
                
                self.metrics.total_enqueued = state['metrics']['total_enqueued']
                self.metrics.total_dequeued = state['metrics']['total_dequeued']
                self.metrics.current_size = len(self._queue)
        except:
            logger.error("Failed to restore queue state")
    
    def set_alert_threshold(self, metric: str, threshold: float) -> None:
        """Set alert threshold for metric"""
        self._alert_thresholds[metric] = threshold
    
    def get_active_alerts(self) -> List[Alert]:
        """Get currently active alerts"""
        return self._active_alerts.copy()
    
    def enable_partitioning(self, partitions: int) -> None:
        """Enable queue partitioning"""
        self._partitioned = True
        self._partition_count = partitions
        for i in range(partitions):
            self._partitions[i] = []
    
    def get_partition_distribution(self) -> Dict[int, int]:
        """Get item count per partition"""
        if not self._partitioned:
            return {}
        
        with self._lock:
            return {p: len(items) for p, items in self._partitions.items()}
    
    def configure_circuit_breaker(self, failure_threshold: int, recovery_timeout: float) -> None:
        """Configure circuit breaker"""
        self._circuit_breaker = CircuitBreaker(failure_threshold, recovery_timeout)
    
    def report_processing_failure(self, error: str) -> None:
        """Report downstream processing failure"""
        self._circuit_breaker.record_failure()
    
    def is_circuit_open(self) -> bool:
        """Check if circuit breaker is open"""
        return self._circuit_breaker.is_open
    
    def set_rate_limit(self, items_per_second: float) -> None:
        """Set dequeue rate limit"""
        self._rate_limit = items_per_second
    
    def export_stats(self) -> Dict[str, Any]:
        """Export statistics for monitoring"""
        with self._lock:
            return {
                'queue_size': len(self._queue),
                'total_enqueued': self.metrics.total_enqueued,
                'total_dequeued': self.metrics.total_dequeued,
                'dead_letter_count': self.metrics.dead_letter_count,
                'avg_wait_time': self.metrics.avg_wait_time,
                'backpressure_events': self.metrics.backpressure_events,
                'expired_items': self.metrics.expired_items,
                'circuit_breaker_open': self._circuit_breaker.is_open,
                'backpressure_active': self._backpressure.is_active
            }
    
    def _remove_expired_items(self) -> None:
        """Remove expired items from queue"""
        expired = []
        remaining = []
        
        for item in self._queue:
            if item.is_expired():
                expired.append(item)
                self.metrics.expired_items += 1
            else:
                remaining.append(item)
        
        if expired:
            self._expired_items.extend(expired)
            self._queue = remaining
            heapq.heapify(self._queue)
    
    def _update_avg_wait_time(self) -> None:
        """Update average wait time metric"""
        if self._wait_times:
            self.metrics.avg_wait_time = sum(self._wait_times) / len(self._wait_times)
    
    def _check_alerts(self) -> None:
        """Check and update alerts"""
        self._active_alerts = []
        
        # Check size threshold
        if 'size' in self._alert_thresholds:
            if len(self._queue) > self._alert_thresholds['size']:
                self._active_alerts.append(
                    Alert('size_threshold', f'Queue size {len(self._queue)} exceeds threshold')
                )
        
        # Check wait time threshold
        if 'wait_time' in self._alert_thresholds:
            if self.metrics.avg_wait_time > self._alert_thresholds['wait_time']:
                self._active_alerts.append(
                    Alert(
                        'wait_time_threshold',
                        f'Avg wait time {self.metrics.avg_wait_time:.2f}s exceeds threshold'
                    )
                )
    
    async def _apply_rate_limit(self) -> None:
        """Apply rate limiting to dequeue operations"""
        if not self._rate_limit:
            return
        
        current_time = time.time()
        min_interval = 1.0 / self._rate_limit
        
        elapsed = current_time - self._last_dequeue_time
        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)
        
        self._last_dequeue_time = time.time()
    
    def _item_to_dict(self, item: QueueItem) -> Dict:
        """Convert QueueItem to dictionary"""
        return {
            'id': item.id,
            'data': item.data,
            'priority': item.priority,
            'created_at': item.created_at.isoformat(),
            'retry_count': item.retry_count,
            'max_retries': item.max_retries,
            'ttl_seconds': item.ttl_seconds
        }
    
    def _dict_to_item(self, data: Dict) -> QueueItem:
        """Convert dictionary to QueueItem"""
        item = QueueItem(
            id=data['id'],
            data=data['data'],
            priority=QueuePriority(data['priority']),
            retry_count=data['retry_count'],
            max_retries=data['max_retries'],
            ttl_seconds=data.get('ttl_seconds')
        )
        item.created_at = datetime.fromisoformat(data['created_at'])
        return item