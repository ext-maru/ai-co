#!/usr/bin/env python3
"""
test_error_handling.sh に実行権限を付与
"""
import os
import stat
from pathlib import Path

script_path = Path("/home/aicompany/ai_co/test_error_handling.sh")
script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)
print(f"実行権限を付与しました: {script_path}")
