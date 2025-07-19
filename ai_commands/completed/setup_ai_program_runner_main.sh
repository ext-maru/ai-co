#!/bin/bash
#!/bin/bash
# AI Program Runner 完全自動セットアップ
cd /home/aicompany/ai_co

echo "🚀 AI Program Runner セットアップ開始"
echo "Time: $(date)"
echo "=================================="

# 1. ディレクトリ作成
echo "📁 ディレクトリ構造を作成..."
mkdir -p ai_programs/{inbox,archive,ai_logs,failed}
chmod -R 755 ai_programs/

# 2. 動作テスト
echo ""
echo "🧪 動作テスト実行..."
source venv/bin/activate
python3 auto_setup_ai_program_runner.py

# 3. 結果表示
echo ""
echo "📊 作成されたディレクトリ:"
find ai_programs -type d | sort

# 4. Slack通知
python3 -c "
import sys
sys.path.insert(0, '/home/aicompany/ai_co')
try:
    from libs.slack_notifier import SlackNotifier
    notifier = SlackNotifier()
    notifier.send_message('🚀 AI Program Runner セットアップ完了！\\n自動実行システムが利用可能になりました。')
except Exception as e:
    print(f'Slack通知エラー: {e}')
"

echo ""
echo "✅ セットアップ完了！"
