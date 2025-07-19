#!/usr/bin/env python3
import sys
from pathlib import Path

PROJECT_ROOT = Path("/home/aicompany/ai_co")
sys.path.insert(0, str(PROJECT_ROOT))

# quick_implement_ai_send.pyを実行
import subprocess

result = subprocess.run(
    [sys.executable, str(PROJECT_ROOT / "quick_implement_ai_send.py")],
    capture_output=True,
    text=True,
)

print("📊 実行結果:")
print("=" * 50)
if result.stdout:
    print(result.stdout)
if result.stderr:
    print("エラー:")
    print(result.stderr)
print("Exit Code:", result.returncode)
