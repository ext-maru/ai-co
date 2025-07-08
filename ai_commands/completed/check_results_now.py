#!/usr/bin/env python3
"""
実行結果の即時確認
"""

import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

print("⏳ 15秒待機してから結果を確認します...")
time.sleep(15)

print("\n📊 実行結果確認")
print("=" * 50)

# 最新の実行結果を確認
result = helper.check_results('verify_system_now')
if result:
    print(f"状態: {result.get('status')}")
    print(f"終了コード: {result.get('exit_code')}")

# ログを取得
log = helper.get_latest_log('verify_system_now')
if log and 'output' in log:
    print("\n実行結果:")
    print("-" * 50)
    print(log['output'])
else:
    print("結果取得中...")
