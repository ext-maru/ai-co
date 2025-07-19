#!/bin/bash
# 最終診断結果サマリー（30秒後）
cd /home/aicompany/ai_co

echo "⏳ 全分析完了待機中..."
sleep 30

echo ""
echo "📊 Slack PM-AI最終診断結果"
echo "=========================="
echo "実行時刻: $(date)"
echo ""

# analyze_all_logsの結果から重要部分を抽出
echo "1. 診断結果サマリー:"
echo "-------------------"
find ai_commands/logs -name "*analyze_all_logs*.log" -mmin -5 -exec grep -A 20 "診断結果サマリー" {} \; | head -30

echo ""
echo "2. 検出された問題:"
echo "-----------------"
find ai_commands/logs -name "*wait_analyze*.log" -mmin -5 -exec grep -A 10 "検出された問題" {} \; | head -20

echo ""
echo "3. Slack通知送信"
echo "---------------"
source venv/bin/activate
python3 << 'EOF'
import sys
sys.path.append("/home/aicompany/ai_co")
from libs.slack_notifier import SlackNotifier

try:
    notifier = SlackNotifier()

    # 最新の診断結果を読み込む
    from pathlib import Path
    log_dir = Path("/home/aicompany/ai_co/ai_commands/logs")

    # 最新のwait_analyzeログを探す
    wait_logs = sorted(log_dir.glob("wait_analyze*.log"), key=lambda f: f.stat().st_mtime, reverse=True)

    if wait_logs:
        with open(wait_logs[0], 'r') as f:
            content = f.read()

        # 問題部分を抽出
        if "検出された問題と解決策" in content:
            idx = content.find("検出された問題と解決策")
            problem_section = content[idx:idx+1000]

            message = f"📊 Slack PM-AI診断完了\\n{'='*30}\\n{problem_section[:500]}"
        else:
            message = "📊 Slack PM-AI診断完了\\n診断結果はログを確認してください"
    else:
        message = "📊 Slack PM-AI診断完了\\n詳細はログファイルを確認してください"

    notifier.send_message(message)
    print("✅ Slack通知送信")
except Exception as e:
    print(f"Slack通知スキップ: {e}")
EOF

echo ""
echo "✅ 診断完了"
echo ""
echo "詳細ログ確認:"
echo "tail -f /home/aicompany/ai_co/ai_commands/logs/*analyze*.log"
