#!/usr/bin/env python3
"""
Show MCP Success
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path("/home/aicompany/ai_co")
sys.path.insert(0, str(PROJECT_ROOT))

from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

cmd = """#!/bin/bash
cd /home/aicompany/ai_co

# Show success report
python3 show_success.py

# Also run the test
echo ""
echo "Running MCP test..."
python3 test_mcp_complete.py
"""

command_id = helper.create_bash_command(cmd, "show_mcp_success")
print(f"✅ Showing MCP success report: {command_id}")
