#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "🎯 AI Company Knowledge Management System - Full Execution"
echo ""

# 1. セットアップスクリプトの実行
echo "📦 Running setup script..."
python3 setup_knowledge_system.py

# 5秒待機（AI Command Executorの処理待ち）
echo "⏳ Waiting for command execution..."
sleep 5

# 2. 初回統合の実行
echo ""
echo "📚 Running initial knowledge consolidation..."
python3 libs/knowledge_consolidator.py

# 3. 進化追跡の実行
echo ""
echo "🌱 Running evolution tracking..."
python3 libs/knowledge_evolution_tracker.py

# 4. 結果の確認
echo ""
echo "📊 Results:"
echo "- Consolidated docs: /home/aicompany/ai_co/knowledge_base/CONSOLIDATED_KNOWLEDGE/"
echo "- Evolution data: /home/aicompany/ai_co/knowledge_base/evolution_tracking/"
echo "- Web reports: /home/aicompany/ai_co/web/"

echo ""
echo "✅ Knowledge Management System is ready!"
echo ""
echo "📋 Available commands:"
echo "  ai-knowledge consolidate    - Consolidate all knowledge"
echo "  ai-knowledge evolve         - Track evolution"
echo "  ai-knowledge schedule       - Run scheduler"
echo "  ai-knowledge status         - Show status"
