from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

# 日本語化セットアップを自動実行
setup_command = """#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate
python3 setup_japanese.py
"""

helper.create_bash_command(setup_command, "execute_japanese_setup")
print("✅ 日本語化セットアップコマンドを作成しました。6秒後に自動実行されます。")
