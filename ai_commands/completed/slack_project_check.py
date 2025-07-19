#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path("/home/aicompany/ai_co")))

from libs.ai_command_helper import AICommandHelper

# 確認コマンドを作成
helper = AICommandHelper()

cmd_content = """#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate
python3 check_slack_project_status.py
"""

result = helper.create_bash_command(cmd_content, "slack_project_check")
print(f"コマンド作成完了: {result}")
print("6秒後に自動実行されます...")
