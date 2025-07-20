#!/usr/bin/env python3

import subprocess
import sys

print("🚀 Executing MCP Auto Setup...")
print("")

# Execute the final auto setup
result = subprocess.run([sys.executable, "/home/aicompany/ai_co/final_mcp_auto.py"])

sys.exit(result.returncode)
