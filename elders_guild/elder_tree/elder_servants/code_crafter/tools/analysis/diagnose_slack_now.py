#!/usr/bin/env python3
"""
Slack診断を即座に開始
"""

from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

# 診断実行
bash_script = """#!/bin/bash
cd /home/aicompany/ai_co
echo "=== Slack PM-AI診断を開始します ==="
python3 run_slack_diagnosis.py
"""

cmd_id = helper.create_bash_command(bash_script, "start_slack_diagnosis")
print(f"Slack診断を開始しました。")
print(f"コマンドID: {cmd_id}")
print(f"\n6秒後に自動実行されます。")
print(f"\n診断結果は以下で確認できます:")
print(f"- ログファイル: /home/aicompany/ai_co/slack_diagnosis.log")
print(f"- Slackに通知")
print(f"\nSlackで @pm-ai にメンションを送ってテストしてください。")
