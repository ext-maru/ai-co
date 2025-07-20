#!/usr/bin/env python3
import os
import sys
sys.path.append('/home/aicompany/ai_co')

# 実行権限を付与
os.chmod('/home/aicompany/ai_co/fix_ai_restart.sh', 0o755)

# AI Command Helperで実行
from libs.ai_command_helper import AICommandHelper
helper = AICommandHelper()

# bashコマンドとして作成
command_file = helper.create_bash_command(
    "cd /home/aicompany/ai_co && chmod +x fix_ai_restart.sh && bash fix_ai_restart.sh",
    "fix_ai_restart_via_claude_cli"
)

print("✅ Claude CLI用の修正スクリプトを準備しました")
print("")
print("WSL2で以下のいずれかを実行してください：")
print("")
print("1) 直接実行:")
print("   bash /home/aicompany/ai_co/fix_ai_restart.sh")
print("")
print("2) Claude CLIで実行:")
print("   claude 'bash /home/aicompany/ai_co/fix_ai_restart.sh を実行してください。sudoパスワードは aicompany です。'")
print("")
print("3) 指示書を読み込んで実行:")
print("   claude 'cat /home/aicompany/ai_co/fix_ai_restart_instructions.md の内容を実行してください。'")
