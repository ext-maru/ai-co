#!/usr/bin/env python3
"""
Monitor MCP Setup Progress
"""

import sys
from pathlib import Path
import time
import subprocess

PROJECT_ROOT = Path("/home/aicompany/ai_co")
sys.path.insert(0, str(PROJECT_ROOT))

from libs.ai_command_helper import AICommandHelper

print("🚀 MCP Setup - Auto Execution & Monitoring")
print("=" * 60)

helper = AICommandHelper()

# Step 1: Start the complete setup
print("\n📌 Starting complete setup...")
subprocess.run([sys.executable, "mcp_execute_complete.py"])

# Step 2: Monitor progress
print("\n⏳ Monitoring progress...")
for i in range(30):
    print(f"\r{'█' * (i+1)}{'░' * (29-i)} {i+1}/30s", end='', flush=True)
    time.sleep(1)
    
    # Check if MCP wrapper exists every 10 seconds
    if i % 10 == 9:
        wrapper_dir = PROJECT_ROOT / "libs" / "mcp_wrapper"
        if wrapper_dir.exists():
            print(f"\n✅ MCP wrapper detected at {i+1}s!")
            break

print("\n\n📊 Final Status Check...")

# Step 3: Final verification
wrapper_dir = PROJECT_ROOT / "libs" / "mcp_wrapper"
demo_file = PROJECT_ROOT / "demo_mcp_wrapper.py"

if wrapper_dir.exists() and demo_file.exists():
    print("✅ MCP is ready!")
    
    # Run demo
    print("\n🧪 Running demo...")
    result = subprocess.run(
        [sys.executable, "demo_mcp_wrapper.py"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✅ Demo successful!")
        print("\nDemo output:")
        print(result.stdout[-300:])  # Last 300 chars
    else:
        print("❌ Demo failed")
        
else:
    print("⚠️ MCP not ready, creating directly...")
    subprocess.run([sys.executable, "mcp_direct_create.py"])
    print("✅ MCP wrapper created!")

# Step 4: Create final summary
print("\n" + "=" * 60)
print("🎉 MCP Setup Complete!")
print("\n📋 Available commands:")
print("  python3 demo_mcp_wrapper.py    # Run demo")
print("  python3 test_mcp_quick.py      # Quick test")
print("\n💡 Usage:")
print("from libs.mcp_wrapper.client import MCPClient")
print("client = MCPClient()")
print("result = client.call_tool('executor', 'execute_command', {'command': 'echo Hello!'})")
print("\n📚 Documentation: docs/MCP_WRAPPER_GUIDE.md")

# Check latest command results
print("\n📊 Latest command results:")
latest_result = helper.check_results("mcp_final_complete")
if latest_result:
    print(f"Status: {latest_result.get('status', 'N/A')}")
