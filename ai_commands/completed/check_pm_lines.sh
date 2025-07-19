#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "🔍 PMWorker 130-140行目の確認"
echo "================================"
echo ""
sed -n '130,140p' workers/pm_worker.py | nl -v 130

echo ""
echo "📊 修正状態:"
if grep -q 'commit_message = f"Task {task_id}' workers/pm_worker.py; then
    echo "✅ commit_message定義あり"
    echo "   場所: $(grep -n 'commit_message = f"Task {task_id}' workers/pm_worker.py | head -1 | cut -d: -f1)行目"
else
    echo "❌ commit_message定義なし"
fi

if grep -q 'if self.git_flow.commit_changes(None' workers/pm_worker.py; then
    echo "⚠️  まだNoneが渡されています（要修正）"
else
    echo "✅ Noneは修正済み"
fi
