#!/usr/bin/env python3
"""
Execute Monitor MCP Setup
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path("/home/aicompany/ai_co")
sys.path.insert(0, str(PROJECT_ROOT))

from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

# Execute monitoring
command = """#!/bin/bash
cd /home/aicompany/ai_co

echo "🎯 Executing MCP Setup with Monitoring"
python3 monitor_mcp_setup.py
"""

command_id = helper.create_bash_command(command, "mcp_monitor_exec")
print(f"✅ Monitoring started: {command_id}")
print("\n⏳ MCP will be ready in about 35 seconds...")
print("\n📊 The system is:")
print("1.0 Starting complete setup")
print("2.0 Monitoring progress")
print("3.0 Creating MCP wrapper")
print("4.0 Running tests")
print("\n🎉 Please wait...")
