#!/usr/bin/env python3
"""
MCP Final Launch - 最終実行
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path("/home/aicompany/ai_co")
sys.path.insert(0, str(PROJECT_ROOT))

from libs.ai_command_helper import AICommandHelper
import time

helper = AICommandHelper()

# 最終実行コマンド
final_command = """#!/bin/bash
cd /home/aicompany/ai_co

echo "🚀 Elders Guild MCP Integration - Final Launch"
echo "==========================================="
echo ""

# 実行権限を全スクリプトに付与
echo "📝 Setting permissions..."
chmod +x *.py *.sh
chmod +x scripts/ai-mcp 2>/dev/null || true

# メイン実行
echo ""
echo "🔌 Launching MCP setup..."
python3 run_mcp_full_setup.py

echo ""
echo "✅ MCP integration launched!"
echo ""
echo "📊 Monitor progress with:"
echo "  python3 mcp_status.py"
echo ""
echo "🚀 After ~30 seconds, start using:"
echo "  ai-mcp start"
"""

# コマンド作成
command_id = helper.create_bash_command(final_command, "mcp_final_launch")

print("=" * 60)
print("🎉 MCP Integration Ready!")
print("=" * 60)
print("")
print(f"✅ Launch command created: {command_id}")
print("")
print("⏳ Automatic execution in 6 seconds...")
print("")
print("📋 What will happen:")
print("1. MCP servers will be installed")
print("2. Management commands will be created")
print("3. Integration will be verified")
print("4. Demo will run automatically")
print("")
print("📊 To check progress:")
print(f"   helper.check_results('{command_id}')")
print("   python3 mcp_status.py")
print("")
print("🚀 After completion (~30 seconds):")
print("   ai-mcp start    # Start MCP servers")
print("   ai-mcp status   # Check status")
print("")
print("💡 Then Claude can use MCP tools directly!")

# 15秒後に状態確認
time.sleep(15)
print("\n" + "=" * 60)
print("📊 Checking initial results...")
result = helper.check_results(command_id)
if result:
    print(f"Status: {result.get('status', 'Unknown')}")
    print(f"Exit code: {result.get('exit_code', 'N/A')}")
else:
    print("Still executing... Check again with: python3 mcp_status.py")
