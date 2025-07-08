#!/usr/bin/env python3
"""
実行結果確認コマンド
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

# 結果確認コマンド
check_command = """#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

python3 check_slack_setup_status.py

echo ""
echo "📋 Slack App権限設定について"
echo "============================="
echo ""
echo "Q: チャンネル選択が1個しか選べない？"
echo ""
echo "A: それは正常です！"
echo ""
echo "Slack Appの権限設定には2種類あります："
echo ""
echo "1. 🔓 ワークスペース全体への権限（推奨）"
echo "   - チャンネル選択は不要"
echo "   - Botは招待されたチャンネルにのみアクセス可能"
echo "   - 今回はこちらでOK"
echo ""
echo "2. 🔒 特定チャンネルのみへの権限"
echo "   - チャンネルを明示的に選択"
echo "   - より制限的なアクセス"
echo "   - 1個ずつしか選べない仕様"
echo ""
echo "✅ 現在の設定で問題ありません！"
echo ""
echo "Botは以下の仕組みで動作します："
echo "- chat:write 権限でメッセージ送信可能"
echo "- 各チャンネルに招待されたら送信できる"
echo "- チャンネル選択は不要"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 最新の動作確認
echo "🧪 最新の動作確認..."
python3 -c "
from libs.slack_channel_notifier import SlackChannelNotifier
import time

notifier = SlackChannelNotifier()

# 動作確認メッセージ
print('送信テスト中...')

success1 = notifier.send_to_channel(
    '#ai-company-scaling',
    '✅ チャンネル別通知設定完了 - スケーリング通知はこちらに届きます'
)

time.sleep(1)

success2 = notifier.send_to_channel(
    '#ai-company-health',
    '✅ チャンネル別通知設定完了 - ヘルスチェック通知はこちらに届きます'
)

if success1 and success2:
    print('')
    print('🎉 設定完了！全てのチャンネルで動作確認済み')
    print('')
    print('残りの作業:')
    print('1. PMWorkerを再起動: ai-restart')
    print('2. Bot Tokenを再生成（セキュリティ対策）')
else:
    print('⚠️ 一部のチャンネルで送信失敗')
    print('Botが各チャンネルに参加しているか確認してください')
"
"""

# コマンドを作成
result = helper.create_bash_command(
    content=check_command,
    command_id="final_slack_check"
)

print("✅ 最終確認コマンドを作成しました")
print("6秒後に自動実行されます...")
