#!/usr/bin/env python3
"""
Execute MCP Setup Start
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path("/home/aicompany/ai_co")
sys.path.insert(0, str(PROJECT_ROOT))

from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

# Start
cmd = """#!/bin/bash
cd /home/aicompany/ai_co
python3 start.py
"""

command_id = helper.create_bash_command(cmd, "start_mcp_setup")
print(f"✅ Started: {command_id}")
