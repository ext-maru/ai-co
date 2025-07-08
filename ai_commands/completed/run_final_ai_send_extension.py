#!/usr/bin/env python3
import sys
from pathlib import Path
PROJECT_ROOT = Path("/home/aicompany/ai_co")
sys.path.insert(0, str(PROJECT_ROOT))

# 最終実装を実行
exec(open(PROJECT_ROOT / "final_execute_ai_send_extension.py").read())