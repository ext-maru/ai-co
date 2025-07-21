#!/usr/bin/env python3
"""
🏛️ Elder Scheduler Manager
エルダーズギルドAPScheduler統合管理ツール

使用方法:
  python3 elder-scheduler-manager.py status
  python3 elder-scheduler-manager.py start
  python3 elder-scheduler-manager.py stop
  python3 elder-scheduler-manager.py restart
  python3 elder-scheduler-manager.py jobs
  python3 elder-scheduler-manager.py logs
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
PID_FILE = PROJECT_ROOT / "logs" / "elder_scheduler.pid"
LOG_DIR = PROJECT_ROOT / "logs" / "elder_scheduler"

def get_scheduler_pid():
    """スケジューラーPID取得"""
    if not PID_FILE.exists():
        return None
    
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        # プロセス存在確認
        os.kill(pid, 0)
        return pid
    except (ValueError, ProcessLookupError, OSError):
        # PIDファイル削除
        PID_FILE.unlink(missing_ok=True)
        return None

def is_scheduler_running():
    """スケジューラー稼働状況確認"""
    return get_scheduler_pid() is not None

def status_command():
    """スケジューラー状態表示"""
    print("🏛️ Elder Scheduler Status")
    print("=" * 50)
    
    pid = get_scheduler_pid()
    if pid:
        print(f"✅ Status: RUNNING (PID: {pid})")
        
        # プロセス詳細情報
        try:
            result = subprocess.run([
                'ps', '-p', str(pid), '-o', 'pid,ppid,etime,pcpu,pmem,cmd'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    headers = lines[0].split()
                    values = lines[1].split()
                    print(f"📊 CPU: {values[3]}%, Memory: {values[4]}%")
                    print(f"⏰ Runtime: {values[2]}")
        except:
            pass
            
        # 最新ログファイル
        if LOG_DIR.exists():
            log_files = sorted(LOG_DIR.glob("*.log"), key=os.path.getmtime, reverse=True)
            if log_files:
                latest_log = log_files[0]
                print(f"📝 Latest log: {latest_log}")
                
                # 最新ログの末尾を表示
                try:
                    result = subprocess.run(['tail', '-5', str(latest_log)], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        print("📄 Recent log entries:")
                        for line in result.stdout.strip().split('\n'):
                            print(f"   {line}")
                except:
                    pass
    else:
        print("❌ Status: STOPPED")
    
    # 設定ファイル確認
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        print(f"🔧 Environment: {env_file} ✅")
    else:
        print("⚠️ Environment: .env file missing")

def start_command():
    """スケジューラー起動"""
    if is_scheduler_running():
        print("⚠️ Elder Scheduler is already running")
        return 1
    
    print("🚀 Starting Elder Scheduler...")
    
    start_script = PROJECT_ROOT / "scripts" / "start-elder-scheduler.sh"
    if not start_script.exists():
        print(f"❌ Start script not found: {start_script}")
        return 1
    
    result = subprocess.run([str(start_script)])
    return result.returncode

def stop_command():
    """スケジューラー停止"""
    if not is_scheduler_running():
        print("⚠️ Elder Scheduler is not running")
        return 1
    
    print("🛑 Stopping Elder Scheduler...")
    
    stop_script = PROJECT_ROOT / "scripts" / "stop-elder-scheduler.sh"
    if not stop_script.exists():
        print(f"❌ Stop script not found: {stop_script}")
        return 1
    
    result = subprocess.run([str(stop_script)])
    return result.returncode

def restart_command():
    """スケジューラー再起動"""
    print("🔄 Restarting Elder Scheduler...")
    
    if is_scheduler_running():
        stop_result = stop_command()
        if stop_result != 0:
            return stop_result
        time.sleep(2)
    
    return start_command()

def jobs_command():
    """ジョブ一覧表示"""
    print("🎯 Elder Scheduler Jobs")
    print("=" * 50)
    
    if not is_scheduler_running():
        print("❌ Scheduler is not running")
        return 1
    
    # 一時的にスケジューラーを起動してジョブ情報取得
    sys.path.insert(0, str(PROJECT_ROOT))
    
    try:
        from libs.elder_scheduled_tasks import start_elder_scheduled_tasks
        import logging
        
        # ログレベルを警告以上に設定
        logging.basicConfig(level=logging.WARNING)
        
        print("📋 Fetching job information...")
        task_system = start_elder_scheduled_tasks()
        
        jobs = task_system.scheduler.get_jobs()
        
        if not jobs:
            print("📝 No jobs scheduled")
        else:
            print(f"📊 Total jobs: {len(jobs)}")
            print()
            
            # カテゴリ別にジョブを整理
            categories = {
                "GitHub": [],
                "System": [],
                "Reports": [],
                "nWo": [],
                "Knowledge": [],
                "Legacy": []
            }
            
            for job in jobs:
                if any(keyword in job.name for keyword in ['github', 'issue', 'pr']):
                    categories["GitHub"].append(job)
                elif any(keyword in job.name for keyword in ['system', 'backup', 'cleanup', 'security']):
                    categories["System"].append(job) 
                elif any(keyword in job.name for keyword in ['report', 'daily', 'weekly']):
                    categories["Reports"].append(job)
                elif 'nwo' in job.name:
                    categories["nWo"].append(job)
                elif any(keyword in job.name for keyword in ['knowledge', 'learning']):
                    categories["Knowledge"].append(job)
                else:
                    categories["Legacy"].append(job)
            
            for category, category_jobs in categories.items():
                if category_jobs:
                    print(f"📂 {category} ({len(category_jobs)} jobs):")
                    for job in category_jobs:
                        next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else "N/A"
                        print(f"  ⏰ {job.name}: {next_run}")
                    print()
        
        task_system.scheduler.shutdown()
        
    except Exception as e:
        print(f"❌ Error fetching jobs: {e}")
        return 1

def logs_command():
    """ログ表示"""
    print("📝 Elder Scheduler Logs")
    print("=" * 50)
    
    if not LOG_DIR.exists():
        print("❌ Log directory not found")
        return 1
    
    log_files = sorted(LOG_DIR.glob("*.log"), key=os.path.getmtime, reverse=True)
    
    if not log_files:
        print("📝 No log files found")
        return 0
    
    latest_log = log_files[0]
    print(f"📄 Latest log: {latest_log}")
    print(f"📅 Last modified: {datetime.fromtimestamp(latest_log.stat().st_mtime)}")
    print()
    
    # ログファイルの末尾20行を表示
    try:
        result = subprocess.run(['tail', '-20', str(latest_log)], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("❌ Error reading log file")
    except Exception as e:
        print(f"❌ Error reading log: {e}")
        return 1

def main():
    parser = argparse.ArgumentParser(
        description="🏛️ Elder Scheduler Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  status    Show scheduler status and information
  start     Start the Elder Scheduler 
  stop      Stop the Elder Scheduler
  restart   Restart the Elder Scheduler
  jobs      List all scheduled jobs
  logs      Show recent log entries

Examples:
  python3 elder-scheduler-manager.py status
  python3 elder-scheduler-manager.py jobs
        """
    )
    
    parser.add_argument(
        'command',
        choices=['status', 'start', 'stop', 'restart', 'jobs', 'logs'],
        help='Command to execute'
    )
    
    args = parser.parse_args()
    
    # プロジェクトルートに移動
    os.chdir(PROJECT_ROOT)
    
    commands = {
        'status': status_command,
        'start': start_command,
        'stop': stop_command,
        'restart': restart_command,
        'jobs': jobs_command,
        'logs': logs_command
    }
    
    return commands[args.command]()

if __name__ == "__main__":
    sys.exit(main())