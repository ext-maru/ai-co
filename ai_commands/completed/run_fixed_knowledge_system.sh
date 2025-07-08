#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "🎯 AI Company Knowledge Management - Fixed Version"
echo ""

# 1. ai-knowledgeコマンドの作成
echo "📦 Creating ai-knowledge command..."
python3 setup_knowledge_system.py

# AI Command Executorの処理待ち
echo "⏳ Waiting for command setup..."
sleep 6

# 2. 初回統合の実行
echo ""
echo "📚 Running knowledge consolidation..."
python3 libs/knowledge_consolidator.py

# 3. 進化追跡の実行
echo ""
echo "🌱 Running evolution tracking..."
python3 libs/knowledge_evolution_tracker.py

# 4. 結果の確認
echo ""
echo "📊 Checking results..."
ls -la /home/aicompany/ai_co/knowledge_base/CONSOLIDATED_KNOWLEDGE/ 2>/dev/null || echo "No consolidated docs yet"
ls -la /home/aicompany/ai_co/knowledge_base/evolution_tracking/ 2>/dev/null || echo "No evolution data yet"

echo ""
echo "✅ Knowledge Management System setup complete!"
echo ""
echo "🚀 You can now use:"
echo "  ai-knowledge consolidate    - Consolidate all knowledge"
echo "  ai-knowledge evolve         - Track evolution"
echo "  ai-knowledge schedule       - Run scheduler"
echo "  ai-knowledge status         - Show status"
