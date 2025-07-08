#!/usr/bin/env python3
"""
テスト結果確認コマンドの実行
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

echo "⏳ 10秒待機してからテスト結果を確認します..."
sleep 10

echo ""
python3 check_slack_test_results.py
"""

# コマンドを作成
result = helper.create_bash_command(
    content=check_command,
    command_id="check_slack_test_status"
)

print("✅ テスト結果確認コマンドを作成しました")
print("10秒後に自動的にテスト結果を表示します")
