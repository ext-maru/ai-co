#!/usr/bin/env python3
"""
Slack PM-AI動作モニタリングスクリプト
リアルタイムで動作を確認
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import time
import subprocess
from datetime import datetime

def monitor_slack_pmai():
    """Slack PM-AI動作を監視"""
    print("🔍 Slack PM-AI動作モニタリング開始")
    print("=" * 50)
    
    while True:
        try:
            # TMUXウィンドウ確認
            tmux_result = subprocess.run(
                ["tmux", "list-windows", "-t", "ai_company"],
                capture_output=True,
                text=True
            )
            
            if tmux_result.returncode == 0:
                windows = tmux_result.stdout.strip().split('\n')
                slack_window = [w for w in windows if 'slack_polling' in w]
                
                if slack_window:
                    print(f"\n✅ Slack Polling Worker: 稼働中")
                    print(f"   {slack_window[0]}")
                else:
                    print(f"\n❌ Slack Polling Worker: 停止中")
            
            # プロセス確認
            ps_result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True
            )
            
            slack_process = [line for line in ps_result.stdout.split('\n') 
                           if 'slack_polling_worker.py' in line and 'grep' not in line]
            
            if slack_process:
                print(f"✅ プロセス: {len(slack_process)}個稼働中")
            
            # キュー状態
            queue_result = subprocess.run(
                ["sudo", "rabbitmqctl", "list_queues", "name", "messages"],
                capture_output=True,
                text=True
            )
            
            if queue_result.returncode == 0:
                print("\n📊 キュー状態:")
                for line in queue_result.stdout.strip().split('\n'):
                    if 'ai_tasks' in line or 'pm_task_queue' in line:
                        print(f"   {line}")
            
            # 最新ログ
            log_file = Path("/home/aicompany/ai_co/logs/slack_polling_worker.log")
            if log_file.exists():
                # 最後の5行を取得
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    recent_lines = lines[-5:] if len(lines) > 5 else lines
                
                print("\n📜 最新ログ:")
                for line in recent_lines:
                    print(f"   {line.strip()}")
            
            print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 次回更新まで10秒...")
            print("-" * 50)
            
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\n👋 モニタリング終了")
            break
        except Exception as e:
            print(f"\n❌ エラー: {str(e)}")
            time.sleep(10)

if __name__ == "__main__":
    monitor_slack_pmai()
