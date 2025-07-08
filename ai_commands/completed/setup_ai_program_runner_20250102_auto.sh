#!/bin/bash
# AI Program Runner 完全自動セットアップ
# このファイルは6秒後に自動実行されます

cd /home/aicompany/ai_co

echo "🚀 AI Program Runner 完全自動セットアップ"
echo "=================================="
echo "実行時刻: $(date)"
echo ""

# Python環境の確認
echo "🐍 Python環境確認..."
source venv/bin/activate
which python3
python3 --version

# セットアップ実行
echo ""
echo "📦 セットアップスクリプト実行..."
python3 auto_setup_ai_program_runner.py

# 結果確認
echo ""
echo "📊 セットアップ結果:"
echo "- ディレクトリ構造:"
tree ai_programs 2>/dev/null || find ai_programs -type d | sort

echo ""
echo "✅ AI Program Runner の準備が整いました！"
echo "=================================="

# Slack通知
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
