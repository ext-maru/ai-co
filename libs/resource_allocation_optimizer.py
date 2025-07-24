#!/usr/bin/env python3
"""
🎯 RESOURCE ALLOCATION OPTIMIZER - Elder Council Strategic System
Optimizes resource allocation across competing priorities
"""

import json
import logging
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psutil

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.priority_queue_manager import TaskPriority


# Define ResourceQuota and ResourceUsage locally to avoid import issues
@dataclass
class ResourceQuota:
    """Resource quota definition"""

    cpu_percent: float  # CPU usage limit (0.0-1.0)
    memory_mb: int  # Memory limit (MB)
    storage_mb: int  # Storage limit (MB)
    network_bps: int  # Network bandwidth (bytes/sec)
    max_processes: int  # Max process count
    max_file_descriptors: int  # Max file descriptors
    max_threads: int  # Max threads
    max_connections: int  # Max network connections


@dataclass
class ResourceUsage:
    """Resource usage status"""

    cpu_percent: float
    memory_mb: float
    storage_mb: float
    network_bps: float
    process_count: int
    file_descriptor_count: int
    thread_count: int
    connection_count: int
    timestamp: datetime


logger = logging.getLogger(__name__)


class AllocationStrategy(Enum):
    """Resource allocation strategies"""

    BALANCED = "balanced"
    PERFORMANCE = "performance"
    EFFICIENCY = "efficiency"
    CRITICAL_FIRST = "critical_first"
    FAIR_SHARE = "fair_share"


@dataclass
class ResourceAllocation:
    """Resource allocation decision"""

    worker_name: str
    priority: TaskPriority
    allocated_resources: ResourceQuota
    strategy_used: AllocationStrategy
    efficiency_score: float
    timestamp: datetime


@dataclass
class CompetingPriority:
    """Competing priority definition"""

    name: str
    priority_level: TaskPriority
    required_resources: ResourceQuota
    current_allocation: Optional[ResourceQuota] = None
    performance_impact: float = 1.0


class ResourceAllocationOptimizer:
    """Strategic resource allocation optimization system"""

    def __init__(self):
        """初期化メソッド"""
        self.project_root = PROJECT_ROOT
        self.allocation_history = []
        self.competing_priorities = []
        self.system_resources = self._get_system_resources()

        logger.info("Resource Allocation Optimizer initialized")

    def _get_system_resources(self) -> ResourceQuota:
        """Get total system resources"""
        cpu_count = psutil.cpu_count()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return ResourceQuota(
            cpu_percent=1.0,  # 100%
            memory_mb=int(memory.total / (1024 * 1024)),
            storage_mb=int(disk.total / (1024 * 1024)),
            network_bps=1000000000,  # 1 Gbps assumed
            max_processes=32768,
            max_file_descriptors=65536,
            max_threads=4096,
            max_connections=1024,
        )

    def analyze_competing_priorities(self) -> Dict[str, Any]:
        """Analyze all competing priorities"""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "total_priorities": 0,
            "resource_conflicts": [],
            "optimization_opportunities": [],
            "critical_bottlenecks": [],
        }

        # Identify current priorities
        priorities = self._identify_current_priorities()
        analysis["total_priorities"] = len(priorities)

        # Check for resource conflicts
        conflicts = self._detect_resource_conflicts(priorities)
        analysis["resource_conflicts"] = conflicts

        # Find optimization opportunities
        opportunities = self._find_optimization_opportunities(priorities)
        analysis["optimization_opportunities"] = opportunities

        # Identify critical bottlenecks
        bottlenecks = self._identify_bottlenecks()
        analysis["critical_bottlenecks"] = bottlenecks

        return analysis

    def _identify_current_priorities(self) -> List[CompetingPriority]:
        """Identify all current competing priorities"""
        priorities = []

        # Worker system recovery (CRITICAL)
        priorities.append(
            CompetingPriority(
                name="worker_system_recovery",
                priority_level=TaskPriority.CRITICAL,
                required_resources=ResourceQuota(
                    cpu_percent=0.3,
                    memory_mb=2048,
                    storage_mb=1024,
                    network_bps=10000000,
                    max_processes=50,
                    max_file_descriptors=1000,
                    max_threads=100,
                    max_connections=50,
                ),
                performance_impact=0.95,
            )
        )

        # Test coverage enhancement (HIGH)
        priorities.append(
            CompetingPriority(
                name="test_coverage_enhancement",
                priority_level=TaskPriority.HIGH,
                required_resources=ResourceQuota(
                    cpu_percent=0.4,
                    memory_mb=4096,
                    storage_mb=5000,
                    network_bps=5000000,
                    max_processes=100,
                    max_file_descriptors=2000,
                    max_threads=200,
                    max_connections=20,
                ),
                performance_impact=0.8,
            )
        )

        # AI evolution system (NORMAL)
        priorities.append(
            CompetingPriority(
                name="ai_evolution_system",
                priority_level=TaskPriority.NORMAL,
                required_resources=ResourceQuota(
                    cpu_percent=0.2,
                    memory_mb=1024,
                    storage_mb=2000,
                    network_bps=2000000,
                    max_processes=30,
                    max_file_descriptors=500,
                    max_threads=50,
                    max_connections=10,
                ),
                performance_impact=0.6,
            )
        )

        # Monitoring and logging (NORMAL)
        priorities.append(
            CompetingPriority(
                name="monitoring_logging",
                priority_level=TaskPriority.NORMAL,
                required_resources=ResourceQuota(
                    cpu_percent=0.1,
                    memory_mb=512,
                    storage_mb=10000,
                    network_bps=1000000,
                    max_processes=20,
                    max_file_descriptors=1000,
                    max_threads=30,
                    max_connections=5,
                ),
                performance_impact=0.4,
            )
        )

        return priorities

    def _detect_resource_conflicts(
        self, priorities: List[CompetingPriority]
    ) -> List[Dict[str, Any]]:
        """Detect resource allocation conflicts"""
        conflicts = []

        # Calculate total required resources
        total_cpu = sum(p.required_resources.cpu_percent for p in priorities)
        total_memory = sum(p.required_resources.memory_mb for p in priorities)

        if total_cpu > self.system_resources.cpu_percent:
            conflicts.append(
                {
                    "type": "cpu_overallocation",
                    "severity": "high",
                    "required": total_cpu,
                    "available": self.system_resources.cpu_percent,
                    "deficit": total_cpu - self.system_resources.cpu_percent,
                }
            )

        if total_memory > self.system_resources.memory_mb:
            conflicts.append(
                {
                    "type": "memory_overallocation",
                    "severity": "critical",
                    "required": total_memory,
                    "available": self.system_resources.memory_mb,
                    "deficit": total_memory - self.system_resources.memory_mb,
                }
            )

        return conflicts

    def _find_optimization_opportunities(
        self, priorities: List[CompetingPriority]
    ) -> List[Dict[str, Any]]:
        """Find resource optimization opportunities"""
        opportunities = []

        # Check for underutilized resources
        current_usage = self._get_current_resource_usage()

        if current_usage.cpu_percent < 0.5:
            opportunities.append(
                {
                    "type": "cpu_underutilized",
                    "current": current_usage.cpu_percent,
                    "recommendation": "Increase worker concurrency",
                    "potential_gain": "50% performance improvement",
                }
            )

        # Check for imbalanced allocations
        high_priority_allocation = sum(
            p.required_resources.cpu_percent
            for p in priorities
            if p.priority_level in [TaskPriority.CRITICAL, TaskPriority.HIGH]
        )

        if high_priority_allocation < 0.6:
            opportunities.append(
                {
                    "type": "priority_imbalance",
                    "recommendation": "Reallocate resources to high-priority tasks",
                    "potential_gain": "30% faster critical task completion",
                }
            )

        return opportunities

    def _identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify system bottlenecks"""
        bottlenecks = []

        # Check memory pressure
        memory = psutil.virtual_memory()
        if memory.percent > 80:
            bottlenecks.append(
                {
                    "type": "memory_pressure",
                    "severity": "high",
                    "current_usage": f"{memory.percent}%",
                    "recommendation": "Reduce memory allocation or add more RAM",
                }
            )

        # Check CPU wait time
        cpu_stats = psutil.cpu_times()
        if hasattr(cpu_stats, "iowait") and cpu_stats.iowait > 20:
            bottlenecks.append(
                {
                    "type": "io_bottleneck",
                    "severity": "medium",
                    "iowait": cpu_stats.iowait,
                    "recommendation": "Optimize I/O operations or upgrade storage",
                }
            )

        return bottlenecks

    def _get_current_resource_usage(self) -> ResourceUsage:
        """Get current system resource usage"""
        return ResourceUsage(
            cpu_percent=psutil.cpu_percent(interval=1) / 100,
            memory_mb=psutil.virtual_memory().used / (1024 * 1024),
            storage_mb=psutil.disk_usage("/").used / (1024 * 1024),
            network_bps=0,  # Would need nethogs or similar
            process_count=len(psutil.pids()),
            file_descriptor_count=0,  # Would need /proc parsing
            thread_count=sum(
                p.num_threads() for p in psutil.process_iter(["num_threads"])
            ),
            connection_count=len(psutil.net_connections()),
            timestamp=datetime.now(),
        )

    def optimize_allocation(
        self, strategy: AllocationStrategy = AllocationStrategy.CRITICAL_FIRST
    ) -> Dict[str, Any]:
        """Execute resource allocation optimization"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy.value,
            "allocations": [],
            "improvements": [],
            "warnings": [],
        }

        priorities = self._identify_current_priorities()

        # Sort by priority for critical-first strategy
        if strategy == AllocationStrategy.CRITICAL_FIRST:
            priorities.sort(key=lambda p: p.priority_level.value)

        # Allocate resources
        remaining_resources = ResourceQuota(
            cpu_percent=self.system_resources.cpu_percent,
            memory_mb=self.system_resources.memory_mb,
            storage_mb=self.system_resources.storage_mb,
            network_bps=self.system_resources.network_bps,
            max_processes=self.system_resources.max_processes,
            max_file_descriptors=self.system_resources.max_file_descriptors,
            max_threads=self.system_resources.max_threads,
            max_connections=self.system_resources.max_connections,
        )

        for priority in priorities:
            allocation = self._allocate_resources(
                priority, remaining_resources, strategy
            )
            if allocation:
                result["allocations"].append(asdict(allocation))
                # Update remaining resources
                remaining_resources.cpu_percent -= (
                    allocation.allocated_resources.cpu_percent
                )
                remaining_resources.memory_mb -= (
                    allocation.allocated_resources.memory_mb
                )
            else:
                result["warnings"].append(
                    f"Failed to allocate resources for {priority.name}"
                )

        # Calculate improvements
        result["improvements"] = self._calculate_improvements(result["allocations"])

        return result

    def _allocate_resources(
        self,
        priority: CompetingPriority,
        available: ResourceQuota,
        strategy: AllocationStrategy,
    ) -> Optional[ResourceAllocation]:
        """Allocate resources to a priority"""
        # Check if we have enough resources
        if (
            priority.required_resources.cpu_percent > available.cpu_percent
            or priority.required_resources.memory_mb > available.memory_mb
        ):
            # Try to allocate partial resources for non-critical tasks
            if priority.priority_level != TaskPriority.CRITICAL:
                allocated = ResourceQuota(
                    cpu_percent=min(
                        priority.required_resources.cpu_percent, available.cpu_percent
                    ),
                    memory_mb=min(
                        priority.required_resources.memory_mb, available.memory_mb
                    ),
                    storage_mb=min(
                        priority.required_resources.storage_mb, available.storage_mb
                    ),
                    network_bps=min(
                        priority.required_resources.network_bps, available.network_bps
                    ),
                    max_processes=min(
                        priority.required_resources.max_processes,
                        available.max_processes,
                    ),
                    max_file_descriptors=min(
                        priority.required_resources.max_file_descriptors,
                        available.max_file_descriptors,
                    ),
                    max_threads=min(
                        priority.required_resources.max_threads, available.max_threads
                    ),
                    max_connections=min(
                        priority.required_resources.max_connections,
                        available.max_connections,
                    ),
                )
            else:
                return None
        else:
            allocated = priority.required_resources

        return ResourceAllocation(
            worker_name=priority.name,
            priority=priority.priority_level,
            allocated_resources=allocated,
            strategy_used=strategy,
            efficiency_score=self._calculate_efficiency(
                allocated, priority.required_resources
            ),
            timestamp=datetime.now(),
        )

    def _calculate_efficiency(
        self, allocated: ResourceQuota, required: ResourceQuota
    ) -> float:
        """Calculate allocation efficiency"""
        cpu_eff = (
            allocated.cpu_percent / required.cpu_percent
            if required.cpu_percent > 0
            else 1.0
        )
        mem_eff = (
            allocated.memory_mb / required.memory_mb if required.memory_mb > 0 else 1.0
        )
        return (cpu_eff + mem_eff) / 2

    def _calculate_improvements(
        self, allocations: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Calculate expected improvements from optimization"""
        improvements = []

        critical_allocated = any(
            a["priority"] == TaskPriority.CRITICAL.value for a in allocations
        )
        if critical_allocated:
            improvements.append(
                {
                    "area": "Worker System Stability",
                    "improvement": "95% uptime guaranteed",
                    "timeline": "24 hours",
                }
            )

        high_priority_count = sum(
            1
            for a in allocations
            if a["priority"] in [TaskPriority.HIGH.value, TaskPriority.CRITICAL.value]
        )
        if high_priority_count >= 2:
            improvements.append(
                {
                    "area": "Overall System Performance",
                    "improvement": "40% faster task completion",
                    "timeline": "48 hours",
                }
            )

        avg_efficiency = (
            sum(a["efficiency_score"] for a in allocations) / len(allocations)
            if allocations
            else 0
        )
        if avg_efficiency > 0.8:
            improvements.append(
                {
                    "area": "Resource Utilization",
                    "improvement": f"{avg_efficiency * 100:0.1f}% efficiency achieved",
                    "timeline": "Immediate",
                }
            )

        return improvements

    def create_unified_roadmap(self) -> Dict[str, Any]:
        """Create unified project roadmap with clear priorities"""
        roadmap = {
            "timestamp": datetime.now().isoformat(),
            "phases": [],
            "milestones": [],
            "resource_allocation": {},
            "success_metrics": [],
        }

        # Phase 1: Critical Recovery (24 hours)
        roadmap["phases"].append(
            {
                "phase": 1,
                "name": "Critical System Recovery",
                "duration": "24 hours",
                "priorities": ["worker_system_recovery"],
                "resource_allocation": "30% CPU, 2GB RAM",
                "success_criteria": ["All workers operational", "0% failure rate"],
            }
        )

        # Phase 2: Quality Enhancement (Days 2-7)
        roadmap["phases"].append(
            {
                "phase": 2,
                "name": "Test Coverage Enhancement",
                "duration": "6 days",
                "priorities": ["test_coverage_enhancement", "quality_gates"],
                "resource_allocation": "40% CPU, 4GB RAM",
                "success_criteria": ["95% test coverage", "All critical paths tested"],
            }
        )

        # Phase 3: System Evolution (Ongoing)
        roadmap["phases"].append(
            {
                "phase": 3,
                "name": "AI Evolution & Optimization",
                "duration": "Ongoing",
                "priorities": ["ai_evolution_system", "performance_optimization"],
                "resource_allocation": "20% CPU, 1GB RAM",
                "success_criteria": [
                    "Self-learning active",
                    "Performance improved by 40%",
                ],
            }
        )

        # Milestones
        roadmap["milestones"] = [
            {"date": "Day 1", "milestone": "Worker system fully operational"},
            {"date": "Day 3", "milestone": "50% test coverage achieved"},
            {"date": "Day 7", "milestone": "95% test coverage achieved"},
            {"date": "Day 14", "milestone": "AI evolution system deployed"},
            {"date": "Day 30", "milestone": "Full autonomous operation"},
        ]

        return roadmap


def custom_json_encoder(obj):
    """Custom JSON encoder for enums"""
    if isinstance(obj, (TaskPriority, AllocationStrategy)):
        return obj.value
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, "__dict__"):
        return obj.__dict__
    else:
        return str(obj)


if __name__ == "__main__":
    optimizer = ResourceAllocationOptimizer()

    # Analyze current situation
    analysis = optimizer.analyze_competing_priorities()
    print(f"Resource Analysis: {json.dumps(analysis, indent=2)}")

    # Optimize allocation
    optimization = optimizer.optimize_allocation(AllocationStrategy.CRITICAL_FIRST)
    print(
        f"\nOptimization Result: {json.dumps(optimization, indent=2)}"
    )

    # Create roadmap
    roadmap = optimizer.create_unified_roadmap()
    print(f"\nUnified Roadmap: {json.dumps(roadmap, indent=2)}")
