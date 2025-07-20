#!/usr/bin/env python3
"""
Execute MCP Final Setup Now
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path("/home/aicompany/ai_co")
sys.path.insert(0, str(PROJECT_ROOT))

from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

# Execute
exec_command = """#!/bin/bash
cd /home/aicompany/ai_co
python3 run_mcp_final.py
"""

command_id = helper.create_bash_command(exec_command, "mcp_exec_now")
print(f"Started: {command_id}")
