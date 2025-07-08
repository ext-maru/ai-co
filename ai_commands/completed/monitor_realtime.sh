#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "🔍 AI Company リアルタイムモニタリング"
echo "===================================="
echo "Ctrl+C で終了"
echo ""

while true; do
    clear
    echo "📊 AI Company モニタリング - $(date)"
    echo "===================================="
    
    echo "📁 Pending コマンド:"
    pending_count=$(ls -1 ai_commands/pending/*.json 2>/dev/null | wc -l)
    echo "   数: $pending_count"
    if [ $pending_count -gt 0 ]; then
        echo "   最新:"
        ls -t ai_commands/pending/*.json 2>/dev/null | head -3 | while read f; do
            echo "     - $(basename $f)"
        done
    fi
    
    echo ""
    echo "✅ 実行済み（最新5件）:"
    ls -t ai_commands/completed/*.json 2>/dev/null | head -5 | while read f; do
        echo "   - $(basename $f .json) ($(stat -c %y $f | cut -d' ' -f2 | cut -d'.' -f1))"
    done
    
    echo ""
    echo "🔄 プロセス状態:"
    if ps aux | grep -E 'command_executor' | grep -v grep > /dev/null; then
        echo "   Command Executor: ✅ 実行中"
    else
        echo "   Command Executor: ❌ 停止中"
    fi
    
    worker_count=$(ps aux | grep -E 'worker.py' | grep -v grep | wc -l)
    echo "   ワーカー数: $worker_count"
    
    echo ""
    echo "📋 最新ログ（最後の5行）:"
    latest_log=$(ls -t ai_commands/logs/*.log 2>/dev/null | head -1)
    if [ -n "$latest_log" ]; then
        echo "   ファイル: $(basename $latest_log)"
        tail -5 "$latest_log" | sed 's/^/   /'
    fi
    
    echo ""
    echo "🔄 5秒後に更新..."
    sleep 5
done