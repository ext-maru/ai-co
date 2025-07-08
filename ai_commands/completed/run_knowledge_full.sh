#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "🎯 AI Company Knowledge Management System v5.3"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. 事前チェック
echo "📋 Pre-check: EMOJI keys..."
python3 -c "
from core import EMOJI
print('Available keys:', list(EMOJI.keys())[:5], '...')
print('Total keys:', len(EMOJI))
"
echo ""

# 2. ナレッジ統合実行
echo "📚 Running Knowledge Consolidation..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 commands/ai_knowledge.py consolidate
echo ""

# 3. 進化追跡
echo "🌱 Tracking Knowledge Evolution..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 commands/ai_knowledge.py evolve --visualize
echo ""

# 4. 結果確認
echo "📊 Results Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📁 Consolidated Documents:"
ls -la /home/aicompany/ai_co/knowledge_base/CONSOLIDATED_KNOWLEDGE/ | tail -5
echo ""
echo "📈 Evolution Reports:"
ls -la /home/aicompany/ai_co/knowledge_base/evolution_tracking/ | tail -5
echo ""
echo "🌐 Web Reports:"
ls -la /home/aicompany/ai_co/web/*knowledge*.html | tail -5
echo ""

echo "✅ Knowledge Management Complete!"
echo ""
echo "Available commands:"
echo "  ai-knowledge consolidate    - Run consolidation"
echo "  ai-knowledge evolve         - Track evolution"
echo "  ai-knowledge status         - Show status"
echo ""
echo "Access reports at: http://localhost:8080/"
