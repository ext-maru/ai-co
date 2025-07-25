#!/usr/bin/env python3
"""Release lock for Multi-CC Coordination Framework implementation"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from libs.task_lock_manager import TaskLockManager

# Create task lock manager with same instance ID
lock_manager = TaskLockManager()
lock_manager.instance_id = "b181599e-05e1-44dd-a8a4-f54244bbc14b"

# Release the lock
task_id = "multi_cc_coordination_framework"
if lock_manager.release_lock(task_id):
    print(f"✓ Successfully released lock for task: {task_id}")
else:
    print(f"✗ Failed to release lock for task: {task_id}")
