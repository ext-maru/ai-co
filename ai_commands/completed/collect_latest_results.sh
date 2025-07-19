#!/bin/bash
# 20秒待ってから最新結果を収集
sleep 20

cd /home/aicompany/ai_co

echo "=== 最新の診断結果まとめ ==="
echo "時刻: $(date)"
echo ""

# 最新のログファイルから結果を抽出
echo "【最新の診断ログ】"
for logfile in ai_commands/logs/*slack*.log; do
    if [ -f "$logfile" ]; then
        filename=$(basename "$logfile")
        mod_time=$(stat -c %Y "$logfile" 2>/dev/null || echo "0")
        current_time=$(date +%s)
        age=$((current_time - mod_time))

        # 5分以内のログのみ
        if [ $age -lt 300 ]; then
            echo ""
            echo "📄 $filename (${age}秒前)"

            # 重要な行を抽出
            grep -E "(✅|❌|⚠️|結論|診断|動作中|停止|タスク化)" "$logfile" | head -10
        fi
    fi
done | tail -50

echo ""
echo "【最終状態】"
if pgrep -f "slack_polling_worker" > /dev/null; then
    echo "✅ Slack Polling Worker: 動作中"
else
    echo "❌ Slack Polling Worker: 停止中"
fi
