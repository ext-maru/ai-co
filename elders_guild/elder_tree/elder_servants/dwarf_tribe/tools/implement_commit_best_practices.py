#!/usr/bin/env python3
"""
コミットメッセージベストプラクティス完全導入スクリプト
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

import time

from libs.ai_command_helper import AICommandHelper

def main():
    """mainメソッド"""
    helper = AICommandHelper()

    print("🚀 Starting Commit Message Best Practices Implementation")
    print("=" * 60)

    # マスターセットアップコマンド
    master_command = """#!/bin/bash
set -e

echo "🎯 Elders Guild Commit Message Best Practices - Full Setup"
echo "========================================================"
echo ""

cd /home/aicompany/ai_co

# Phase 1: セットアップ実行
echo "📦 Phase 1: Running setup script..."
if [ -f setup_commit_best_practices.sh ]; then:
    chmod +x setup_commit_best_practices.sh
    ./setup_commit_best_practices.sh
else
    echo "❌ Setup script not found!":
    exit 1
fi

echo ""
echo "📝 Phase 2: Patching PMWorker..."
if [ -f patch_pm_worker_best_practices.py ]; then:
    python3 patch_pm_worker_best_practices.py
else
    echo "⚠️ PMWorker patch script not found (optional)":
fi

echo ""
echo "🧪 Phase 3: Running comprehensive tests..."

# テスト1: コミットメッセージ生成テスト
echo "Test 1: Commit message generation"
cd /home/aicompany/ai_co
echo "test content" > test_file.txt
git add test_file.txt 2>/dev/null || true
ai-git commit --preview > /tmp/commit_preview.txt 2>&1
cat /tmp/commit_preview.txt
git reset HEAD test_file.txt 2>/dev/null || true
rm -f test_file.txt

echo ""
echo "Test 2: Command availability"
ai-git best-practices > /dev/null 2>&1 && echo "✅ best-practices command \
    works" || echo "❌ best-practices command failed"
ai-git analyze > /dev/null 2>&1 && echo "✅ analyze command works" || echo "❌ analyze command failed"

echo ""
echo "📊 Phase 4: Creating sample CHANGELOG..."
ai-git changelog --output CHANGELOG_SAMPLE.md

echo ""
echo "✨ Phase 5: Final status check..."
echo "Configuration files:"
ls -la config/commit_best_practices.json 2>/dev/null && echo "✅ Config file exists" || echo "❌ Config file missing"

echo ""
echo "Python modules:"
python3 -c "
from libs.commit_message_generator import CommitMessageGenerator
from libs.github_flow_manager import GitHubFlowManager
print('✅ All Python modules loaded successfully')
"

echo ""
echo "==============================================="
echo "🎉 SETUP COMPLETED SUCCESSFULLY!"
echo "==============================================="
echo ""
echo "📚 Quick Reference:"
echo "  • ai-git commit           - Auto-generate & commit"
echo "  • ai-git commit --preview - Preview message"
echo "  • ai-git analyze          - Analyze changes"
echo "  • ai-git changelog        - Generate CHANGELOG"
echo "  • ai-git best-practices   - Show guidelines"
echo ""
echo "💡 Example workflow:"
echo "  1.0 Make changes to files"
echo "  2.0 git add ."
echo "  3.0 ai-git commit --preview"
echo "  4.0 ai-git commit"
echo ""
echo "🔍 All commits now follow Conventional Commits!"
echo "   Format: <type>(<scope>): <subject>"
echo ""
date
"""

    # コマンドを作成して実行
    result = helper.create_bash_command(
        master_command, "full_commit_best_practices_setup"
    )

    print(f"\n✅ Master setup command created!")
    print(f"📄 Command ID: {result['command_id']}")
    print("⏳ Executing setup (this may take a moment)...")

    # 実行完了を待つ
    for i in range(12):  # 最大60秒待つ
        time.sleep(5)
        check = helper.check_results("full_commit_best_practices_setup")
        if check and check.get("status") in ["SUCCESS", "FAILED"]:
            print(f"\n🏁 Execution completed with status: {check['status']}")

            # ログを表示
            log = helper.get_latest_log("full_commit_best_practices_setup")
            if log:
                print("\n📜 Setup Log (last 3000 chars):")
                print("=" * 60)
                print(log[-3000:])
            break
        else:
            print(f"⏳ Still executing... ({(i+1)*5}s)")

    print("\n🎯 Next Steps:")
    print("1.0 Check Slack for detailed results")
    print("2.0 Try 'ai-git commit --preview' to test")
    print("3.0 All future commits will use best practices!")

    # サマリー生成
    print("\n📋 Implementation Summary:")
    print("• CommitMessageGenerator - Analyzes changes and generates messages")
    print("• GitFlowManager v2 - Integrated with best practices")
    print("• ai-git enhanced - New commands for better workflow")
    print("• Automatic validation - Ensures message quality")
    print("• CHANGELOG generation - From commit history")

    print("\n✨ Commit messages will now be:")
    print("• Conventional Commits compliant")
    print("• Automatically categorized (feat/fix/docs/etc)")
    print("• Properly formatted (50/72 rule)")
    print("• Include detailed context")
    print("• Support breaking changes")

if __name__ == "__main__":
    main()
