#!/usr/bin/env python3
"""
Execute Status Check via AI Command Executor
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path("/home/aicompany/ai_co")
sys.path.insert(0, str(PROJECT_ROOT))

from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

# Execute
cmd = """#!/bin/bash
cd /home/aicompany/ai_co
python3 run_status_check.py
"""

command_id = helper.create_bash_command(cmd, "exec_status_check")
print(f"✅ Status check started: {command_id}")
