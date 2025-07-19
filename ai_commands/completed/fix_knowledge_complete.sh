#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

# 1. knowledge_consolidator.pyの修正
echo "📝 Fixing knowledge_consolidator.py..."
sed -i 's/super().__init__(manager_type=.knowledge_consolidator.)/super().__init__(manager_name="knowledge_consolidator")/' libs/knowledge_consolidator.py

# 2. knowledge_evolution_tracker.pyの修正
echo "📝 Fixing knowledge_evolution_tracker.py..."
sed -i 's/super().__init__(manager_type=.knowledge_evolution.)/super().__init__(manager_name="knowledge_evolution")/' libs/knowledge_evolution_tracker.py

# 3. ai_knowledge.pyの修正（既に修正済みか確認）
echo "📝 Checking ai_knowledge.py..."
if grep -q "EMOJI\['book'\]" commands/ai_knowledge.py; then
    echo "Fixing EMOJI keys in ai_knowledge.py..."
    sed -i "s/EMOJI\['book'\]/EMOJI['template']/g" commands/ai_knowledge.py
    sed -i "s/EMOJI\['check'\]/EMOJI['success']/g" commands/ai_knowledge.py
    sed -i "s/EMOJI\['seedling'\]/EMOJI['evolution']/g" commands/ai_knowledge.py
    sed -i "s/EMOJI\['chart'\]/EMOJI['monitor']/g" commands/ai_knowledge.py
    sed -i "s/EMOJI\['x'\]/EMOJI['error']/g" commands/ai_knowledge.py
fi

echo "✅ All files fixed!"

# 実行
source venv/bin/activate
echo ""
echo "📚 Running knowledge consolidation..."
python3 commands/ai_knowledge.py consolidate

echo ""
echo "✅ Knowledge Management System is ready!"
echo ""
echo "Available commands:"
echo "  ai-knowledge consolidate    - Consolidate all knowledge"
echo "  ai-knowledge evolve         - Track evolution"
echo "  ai-knowledge status         - Show status"
