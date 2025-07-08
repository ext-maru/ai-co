#!/usr/bin/env python3
import sys
from pathlib import Path
PROJECT_ROOT = Path("/home/aicompany/ai_co")
sys.path.insert(0, str(PROJECT_ROOT))

# Python実装スクリプトを実行
exec(open(PROJECT_ROOT / "python_implement_ai_send.py").read())