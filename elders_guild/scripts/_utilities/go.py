#!/usr/bin/env python3
import subprocess
import sys

print("🚀 Executing MCP Setup...")
result = subprocess.run(
    [sys.executable, "/home/aicompany/ai_co/mcp_final_setup.py"],
    cwd="/home/aicompany/ai_co",
)
sys.exit(result.returncode)
