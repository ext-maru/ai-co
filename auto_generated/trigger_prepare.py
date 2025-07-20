#!/usr/bin/env python3
import os
import subprocess

# 実行権限を付与
os.chmod('/home/aicompany/ai_co/ai_commands/prepare_fix_for_claude.sh', 0o755)

# 実行
subprocess.run(['bash', '/home/aicompany/ai_co/ai_commands/prepare_fix_for_claude.sh'])
