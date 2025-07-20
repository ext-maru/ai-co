#!/usr/bin/env python3
"""
MCP Status Check - 簡単な状態確認
"""

import sys
from pathlib import Path
import time

PROJECT_ROOT = Path("/home/aicompany/ai_co")
sys.path.insert(0, str(PROJECT_ROOT))

from libs.ai_command_helper import AICommandHelper
from libs.ai_log_viewer import AILogViewer

print("🔍 MCP Status Check")
print("=" * 40)

helper = AICommandHelper()
viewer = AILogViewer()

# 最新の実行結果を確認
print("\n📊 Recent MCP-related executions:")
latest_logs = viewer.get_latest_command_logs(10)

mcp_logs = [log for log in latest_logs if 'mcp' in log.get('task', '').lower()]
for log in mcp_logs[-5:]:
    status = "✅" if log.get('exit_code', 1) == 0 else "❌"
    print(f"{status} {log.get('task')} - {log.get('timestamp', 'N/A')}")

# ファイル存在確認
print("\n📁 MCP Files:")
files = [
    "scripts/ai-mcp",
    "libs/mcp_servers/filesystem_server.py",
    "libs/mcp_servers/executor_server.py",
    "config/mcp_config.json"
]

all_exist = True
for file in files:
    path = PROJECT_ROOT / file
    if path.exists():
        print(f"✅ {file}")
    else:
        print(f"❌ {file} - Not found")
        all_exist = False

if all_exist:
    print("\n🎉 MCP is ready to use!")
    print("\nNext steps:")
    print("1. Start MCP servers: ai-mcp start")
    print("2. Check server status: ai-mcp status")
    print("3. Use MCP tools in your Claude conversations!")
else:
    print("\n⚠️ MCP setup incomplete. Run:")
    print("  python3 mcp_execute_now.py")

# 実行サマリー
summary = viewer.get_execution_summary()
print(f"\n📈 Total executions: {summary.get('total_logs', 0)}")
print(f"📊 Failed programs: {summary.get('failed_programs', 0)}")
