#!/usr/bin/env python3
"""
generate_task_id utility function for testing
"""
from datetime import datetime

def generate_task_id(prefix="task"):
    """Generate a task ID with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}"

# Export for backward compatibility
if __name__ == "__main__":
    print(generate_task_id())
