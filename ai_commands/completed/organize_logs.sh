#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "🗂️ Starting log organization..."

# ログ整理を実行
python3 organize_logs_now.py

# 結果を確認
echo ""
echo "📊 Log directory structure:"
ls -la logs/

echo ""
echo "📁 Slack logs:"
ls -la logs/slack/ 2>/dev/null | head -10 || echo "No slack logs yet"

echo ""
echo "🗄️ Archived logs:"
ls -la logs/archive/slack/ 2>/dev/null | wc -l || echo "0"
echo "archived log files"

echo ""
echo "✅ Log organization complete!"
