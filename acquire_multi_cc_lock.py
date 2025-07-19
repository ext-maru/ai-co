#!/usr/bin/env python3
"""Acquire lock for Multi-CC Coordination Framework implementation"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging

from libs.task_lock_manager import TaskLockManager

logging.basicConfig(level=logging.INFO)

# Create task lock manager
lock_manager = TaskLockManager()

# Task information
task_id = "multi_cc_coordination_framework"
task_info = {
    "description": "Implement Multi-CC Coordination Framework with TDD approach",
    "components": ["test_multi_cc_coordination.py", "libs/multi_cc_coordination.py"],
    "started_at": "2025-07-06T10:00:00",
}

# Try to acquire lock
if lock_manager.acquire_lock(task_id, task_info):
    print(f"✓ Successfully acquired lock for task: {task_id}")
    print(f"  Instance ID: {lock_manager.instance_id}")
    print("  You can now proceed with the implementation.")
else:
    print(f"✗ Failed to acquire lock for task: {task_id}")
    print("  Another instance may be working on this task.")
    sys.exit(1)
