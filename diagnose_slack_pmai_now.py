#!/usr/bin/env python3
"""
Elders Guild Slack PM-AI連携の診断と修正
AI Command Executorを使用して自動実行
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.ai_command_helper import AICommandHelper
import time

def main():
    helper = AICommandHelper()
    
    print("Slack PM-AI連携の診断を開始します...")
    
    # 診断スクリプトを実行
    bash_content = """#!/bin/bash
cd /home/aicompany/ai_co
chmod +x scripts/check_and_fix_slack_pmai.sh
./scripts/check_and_fix_slack_pmai.sh
"""
    
    cmd_id = helper.create_bash_command(bash_content, "diagnose_slack_pmai")
    print(f"診断コマンドを作成しました: {cmd_id}")
    print("6秒後に自動実行されます...")
    
    # 実行完了を待つ
    time.sleep(10)
    
    # 結果確認
    result = helper.check_results("diagnose_slack_pmai")
    if result:
        print("\n診断結果:")
        print(f"Exit Code: {result.get('exit_code', 'N/A')}")
        
        # ログファイルを読む
        log_content = helper.get_latest_log("diagnose_slack_pmai")
        if log_content:
            print("\n詳細ログ:")
            print("=" * 60)
            print(log_content)
            print("=" * 60)
    
    # 追加で、ワーカーの状態を直接確認
    print("\n追加確認: Slack Polling Workerのテスト実行")
    
    test_script = """#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

# ワーカーのテスト実行
python3 workers/slack_polling_worker.py --test

# プロセス確認
echo ""
echo "現在動作中のSlack関連プロセス:"
ps aux | grep -E "(slack_polling|slack_monitor)" | grep -v grep

# tmuxセッション確認
echo ""
echo "tmuxセッション:"
tmux ls 2>/dev/null | grep slack || echo "Slack関連のtmuxセッションなし"
"""
    
    test_id = helper.create_bash_command(test_script, "test_slack_worker")
    print(f"\nテストコマンドを作成しました: {test_id}")
    
    # テスト結果を待つ
    time.sleep(10)
    
    test_result = helper.check_results("test_slack_worker")
    if test_result:
        test_log = helper.get_latest_log("test_slack_worker")
        if test_log:
            print("\nテスト結果:")
            print("=" * 60)
            print(test_log)
            print("=" * 60)

if __name__ == "__main__":
    main()
