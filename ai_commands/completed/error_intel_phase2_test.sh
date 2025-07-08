#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "🧪 Phase 2テスト開始..."
python3 scripts/test_error_intelligence_phase2.py
echo "✅ テスト実行完了"
