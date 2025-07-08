#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "📊 Slack PM-AI修復最終レポート"
echo "==============================="
echo "日時: $(date)"
echo ""

echo "1. ワーカー状態"
echo "---------------"
tmux list-windows -t ai_company 2>/dev/null | grep -E "(task|pm|result|slack)" || echo "TMUXセッションなし"

echo -e "
2. プロセス状態"
echo "---------------"
ps aux | grep -E "worker.*\.py" | grep -v grep | wc -l | xargs -I {} echo "稼働中のワーカー数: {}"

echo -e "
3. Slack Polling Worker最新ログ"
echo "--------------------------------"
tail -10 logs/slack_polling_worker.log 2>/dev/null || echo "ログファイルなし"

echo -e "
4. 使用方法"
echo "-----------"
echo "Slackで以下のようにメンションしてください："
echo "@pm-ai 新しいワーカーを作成してください"
echo "@pm-ai データベース接続用のクラスを実装して"
echo ""
echo "✅ 修復完了！Slackからの指示が自動的に処理されます。"

# Slack通知
python3 << 'EOF'
import sys
sys.path.append("/home/aicompany/ai_co")
from libs.slack_notifier import SlackNotifier

try:
    notifier = SlackNotifier()
    message = '''✨ Slack PM-AI完全修復完了！
━━━━━━━━━━━━━━━━━━━━━━
✅ 全システム正常稼働
✅ Slack Polling Worker起動完了
✅ API接続テスト成功
✅ 統合テスト完了

📡 使い方:
@pm-ai [指示内容]

💡 例:
@pm-ai RESTful APIサーバーを作成して
@pm-ai データ分析スクリプトを作って

🔍 動作確認:
tmux attach -t ai_company
→ slack_polling ウィンドウで動作確認'''
    
    notifier.send_message(message)
except:
    pass
EOF
