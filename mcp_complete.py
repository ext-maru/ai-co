#!/usr/bin/env python3
"""
MCP Complete Execution
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path("/home/aicompany/ai_co")
sys.path.insert(0, str(PROJECT_ROOT))

from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

# Final execution
cmd = """#!/bin/bash
cd /home/aicompany/ai_co
python3 go_final.py
"""

command_id = helper.create_bash_command(cmd, "mcp_complete_exec")
print(f"✅ MCP Complete Setup Started: {command_id}")
print("\n⏳ MCP will be ready in about 50 seconds...")
print("\n📊 Check with: python3 check_mcp_now.py")
