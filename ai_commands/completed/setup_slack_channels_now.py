#!/usr/bin/env python3
"""
AI Command Executor 用コマンド作成
Slackチャンネル分離設定の自動実行
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

# 最終的な実行コマンド
final_command = """#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "🚀 Elders Guild Slack チャンネル分離設定"
echo "====================================="
echo ""

# start_slack_channel_setup.py を実行
python3 start_slack_channel_setup.py

echo ""
echo "✅ コマンド作成完了"
echo "6秒後に自動実行されます..."
"""

# AI Command Executorに登録
result = helper.create_bash_command(
    content=final_command,
    command_id="slack_channel_separation_main"
)

print(f"✅ コマンドを作成しました: {result['command_id']}")
print("\n6秒後に自動実行されます...")
