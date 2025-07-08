#!/bin/bash
#!/bin/bash
set -e

echo "🎯 AI Company Commit Message Best Practices - Full Setup"
echo "========================================================"
echo ""

cd /home/aicompany/ai_co

# Phase 1: セットアップ実行
echo "📦 Phase 1: Running setup script..."
if [ -f setup_commit_best_practices.sh ]; then
    chmod +x setup_commit_best_practices.sh
    ./setup_commit_best_practices.sh
else
    echo "❌ Setup script not found!"
    exit 1
fi

echo ""
echo "📝 Phase 2: Patching PMWorker..."
if [ -f patch_pm_worker_best_practices.py ]; then
    python3 patch_pm_worker_best_practices.py
else
    echo "⚠️ PMWorker patch script not found (optional)"
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
ai-git best-practices > /dev/null 2>&1 && echo "✅ best-practices command works" || echo "❌ best-practices command failed"
ai-git analyze > /dev/null 2>&1 && echo "✅ analyze command works" || echo "❌ analyze command failed"

echo ""
echo "📊 Phase 4: Creating sample CHANGELOG..."
ai-git changelog --output CHANGELOG_SAMPLE.md

echo ""
echo "✨ Phase 5: Final status check..."
echo "Configuration files:"
ls -la config/commit_best_practices.json 2>/dev/null && echo "✅ Config file exists" || echo "❌ Config file missing"
ls -la .gitmessage 2>/dev/null && echo "✅ Git template exists" || echo "❌ Git template missing"

echo ""
echo "Python modules:"
python3 -c "
from libs.commit_message_generator import CommitMessageGenerator
from libs.git_flow_manager import GitFlowManager
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
echo "  1. Make changes to files"
echo "  2. git add ."
echo "  3. ai-git commit --preview"
echo "  4. ai-git commit"
echo ""
echo "🔍 All commits now follow Conventional Commits!"
echo "   Format: <type>(<scope>): <subject>"
echo ""
date
