#!/usr/bin/env python3
import os
import subprocess

# スクリプトに実行権限を付与
script_path = "/home/aicompany/ai_co/fix_ai_restart.sh"
os.chmod(script_path, 0o755)
print(f"✅ {script_path} に実行権限を付与しました")
