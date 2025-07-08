#!/usr/bin/env python3
"""
Command Executor ウォッチドッグ
Command Executorの状態を監視し、停止時に自動再起動する
"""

import sys
import os
import time
import subprocess
import psutil
from pathlib import Path
from datetime import datetime
import signal

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import setup_logging, EMOJI
from libs.slack_notifier import SlackNotifier

class CommandExecutorWatchdog:
    def __init__(self):
        self.logger = setup_logging(
            name="CommandExecutorWatchdog",
            log_file=PROJECT_ROOT / "logs" / "executor_watchdog.log"
        )
        self.slack = SlackNotifier()
        self.running = True
        self.check_interval = 30  # 30秒ごとにチェック
        self.restart_count = 0
        self.max_restarts = 10  # 最大再起動回数
        
    def run(self):
        """メインループ"""
        self.logger.info(f"{EMOJI['start']} Command Executor Watchdog started")
        
        # シグナルハンドラ設定
        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGINT, self.handle_signal)
        
        try:
            while self.running:
                if not self.check_executor_running():
                    self.restart_executor()
                    
                time.sleep(self.check_interval)
                
        except Exception as e:
            self.logger.error(f"{EMOJI['error']} Watchdog error: {str(e)}")
            
    def handle_signal(self, signum, frame):
        """シグナルハンドラ"""
        self.logger.info(f"{EMOJI['stop']} Received signal {signum}, shutting down...")
        self.running = False
        
    def check_executor_running(self):
        """Command Executorが動作しているか確認"""
        for proc in psutil.process_iter(['pid', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and 'command_executor_worker.py' in ' '.join(cmdline):
                    return True
            except:
                pass
        return False
        
    def restart_executor(self):
        """Command Executorを再起動"""
        if self.restart_count >= self.max_restarts:
            self.logger.error(f"{EMOJI['error']} Max restart attempts reached ({self.max_restarts})")
            self.slack.send_message(
                f"❌ Command Executor Watchdog: 最大再起動回数に達しました\n"
                f"手動での確認が必要です"
            )
            self.running = False
            return
            
        self.logger.warning(f"{EMOJI['warning']} Command Executor not running, restarting...")
        self.restart_count += 1
        
        try:
            # tmuxで起動
            cmd = f"""
cd {PROJECT_ROOT}
source venv/bin/activate
tmux new-session -d -s command_executor_{self.restart_count} 'python3 workers/command_executor_worker.py'
"""
            subprocess.run(["bash", "-c", cmd], check=True)
            
            # 起動確認
            time.sleep(3)
            if self.check_executor_running():
                self.logger.info(f"{EMOJI['success']} Command Executor restarted successfully")
                self.slack.send_message(
                    f"🔄 Command Executor自動再起動成功\n"
                    f"再起動回数: {self.restart_count}/{self.max_restarts}"
                )
            else:
                self.logger.error(f"{EMOJI['error']} Failed to restart Command Executor")
                
        except Exception as e:
            self.logger.error(f"{EMOJI['error']} Error restarting: {str(e)}")
            

if __name__ == "__main__":
    watchdog = CommandExecutorWatchdog()
    watchdog.run()
