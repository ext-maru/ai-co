#!/usr/bin/env python3
"""
MCP Setup Status Dashboard
"""

import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path("/home/aicompany/ai_co")
sys.path.insert(0, str(PROJECT_ROOT))

from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

print("📊 MCP Setup Status Dashboard")
print("=" * 60)

# Execute monitor
print("\n🚀 Starting MCP setup with monitoring...")
subprocess.run([sys.executable, "exec_monitor.py"])

# Wait for AI Command Executor
print("\n⏳ Waiting for execution (35 seconds)...")
print("Progress:")

for i in range(35):
    # Progress bar
    progress = int((i + 1) / 35 * 20)
    bar = "█" * progress + "░" * (20 - progress)
    print(f"\r[{bar}] {i+1}/35s", end="", flush=True)

    # Check every 5 seconds
    if i % 5 == 4:
        wrapper_dir = PROJECT_ROOT / "libs" / "mcp_wrapper"
        if wrapper_dir.exists():
            print(f"\n✅ MCP wrapper found at {i+1}s!")
            # Quick verification
            files = list(wrapper_dir.glob("*.py"))
            if len(files) >= 4:  # Should have at least 4 files
                print(f"   Found {len(files)} files")
                break

    time.sleep(1)

print("\n\n📊 Final Status:")

# Check MCP wrapper
wrapper_dir = PROJECT_ROOT / "libs" / "mcp_wrapper"
if wrapper_dir.exists():
    files = list(wrapper_dir.glob("*.py"))
    print(f"✅ MCP wrapper: {len(files)} files")
    for f in files[:5]:  # Show first 5
        print(f"   - {f.name}")
else:
    print("❌ MCP wrapper not found")

# Check demo
demo_file = PROJECT_ROOT / "demo_mcp_wrapper.py"
if demo_file.exists():
    print("✅ Demo file ready")
else:
    print("❌ Demo file not found")

# Check command results
print("\n📋 Command Results:")
commands = ["mcp_monitor_exec", "mcp_final_complete", "mcp_auto_setup"]
for cmd in commands:
    result = helper.check_results(cmd)
    if result:
        status = "✅" if result.get("exit_code") == 0 else "⚠️"
        print(f"{status} {cmd}: {result.get('status', 'N/A')}")

print("\n" + "=" * 60)

if wrapper_dir.exists() and demo_file.exists():
    print("🎉 MCP is ready to use!")
    print("\n🚀 Test commands:")
    print("  python3 demo_mcp_wrapper.py")
    print("  python3 test_mcp_quick.py")
    print("\n💡 Quick example:")
    print("  from libs.mcp_wrapper.client import MCPClient")
    print("  client = MCPClient()")
    print("  client.call_tool('executor', 'execute_command', {'command': 'ls'})")
else:
    print("⚠️ MCP setup may need manual intervention")
    print("Run: python3 mcp_direct_create.py")

print("\n📚 Full documentation: docs/MCP_WRAPPER_GUIDE.md")
