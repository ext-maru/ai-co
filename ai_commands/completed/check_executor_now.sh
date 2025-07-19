#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "🔍 AI Command Executor状態確認"
echo "================================\n"

# プロセス確認
echo "📊 CommandExecutorWorkerプロセス:"
if ps aux | grep -v grep | grep -q "command_executor_worker"; then
    echo "✅ 実行中"
    ps aux | grep -v grep | grep "command_executor_worker" | head -1
else
    echo "❌ 停止中"
fi

echo ""
echo "📁 Pendingコマンド数:"
ls -1 /home/aicompany/ai_co/ai_commands/pending/*.json 2>/dev/null | wc -l

echo ""
echo "📋 最新のPendingコマンド:"
ls -lt /home/aicompany/ai_co/ai_commands/pending/*.json 2>/dev/null | head -5

echo ""
echo "📝 ベストプラクティス関連コマンド:"
ls -la /home/aicompany/ai_co/ai_commands/pending/final_* 2>/dev/null || echo "見つかりません"

echo ""
echo "🔄 最近実行されたコマンド（過去1分）:"
find /home/aicompany/ai_co/ai_commands/logs -name "*.log" -mmin -1 -type f | sort -r | head -5
