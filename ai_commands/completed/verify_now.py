#!/usr/bin/env python3
"""
システム状態確認の実行
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

# 状態確認コマンド
verify_command = """#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

python3 verify_system_status.py
"""

# コマンドを作成
result = helper.create_bash_command(
    content=verify_command,
    command_id="verify_system_now"
)

print(f"✅ システム状態確認を開始: {result['command_id']}")
print("6秒後に結果が表示されます...")
