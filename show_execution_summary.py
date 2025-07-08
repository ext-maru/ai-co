#!/usr/bin/env python3
"""
AI Command Executor実行状況サマリー
"""

from libs.ai_log_viewer import AILogViewer
from datetime import datetime

def show_execution_summary():
    """実行状況サマリー表示"""
    viewer = AILogViewer()
    
    print("📊 AI Command Executor実行状況")
    print("=" * 60)
    print(f"現在時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 実行サマリー取得
    summary = viewer.get_execution_summary()
    print(f"総コマンド数: {summary['command_logs']}")
    print(f"プログラム実行数: {summary['program_logs']}")
    print(f"失敗コマンド数: {summary['failed_programs']}")
    print()
    
    # 最新のコマンドログ
    print("最新実行コマンド:")
    print("-" * 60)
    
    latest_logs = viewer.get_latest_command_logs(10)
    
    for log in latest_logs:
        cmd_id = log['command_id']
        status = '✅' if log.get('exit_code', 1) == 0 else '❌'
        timestamp = log.get('timestamp', 'unknown')
        
        # Slack関連を強調
        if 'slack' in cmd_id.lower():
            print(f"{status} 🔷 {cmd_id} - {timestamp}")
        else:
            print(f"{status} {cmd_id} - {timestamp}")
    
    # Slack関連コマンドの詳細
    print("\n\nSlack関連コマンド詳細:")
    print("-" * 60)
    
    slack_commands = [
        log for log in latest_logs 
        if any(kw in log['command_id'].lower() for kw in ['slack', 'diagnose', 'fix', 'repair'])
    ]
    
    for log in slack_commands[:5]:
        print(f"\n📌 {log['command_id']}")
        print(f"   終了コード: {log.get('exit_code', 'N/A')}")
        print(f"   実行時刻: {log.get('timestamp', 'unknown')}")
        
        # ログパス表示
        if 'path' in log:
            print(f"   ログ: {log['path']}")

if __name__ == "__main__":
    show_execution_summary()
