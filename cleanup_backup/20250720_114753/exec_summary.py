#!/usr/bin/env python3
"""
Execute Summary
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path("/home/aicompany/ai_co")
sys.path.insert(0, str(PROJECT_ROOT))

from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

cmd = """#!/bin/bash
cd /home/aicompany/ai_co
python3 show_summary.py
"""

command_id = helper.create_bash_command(cmd, "show_mcp_summary")
print(f"Started: {command_id}")
