#!/usr/bin/env python3
"""
WSL環境対応 PCスリープ復旧システム
PCスリープ後の自動復旧とワーカー再起動システム
"""

import os
import sys
import time
import subprocess
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WSLSleepRecoverySystem:
    """WSLスリープ復旧システム"""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.recovery_log = self.project_root / "logs" / "wsl_recovery.log"
        self.state_file = self.project_root / "data" / "wsl_state.json"
        self.startup_script = self.project_root / "scripts" / "auto_startup.sh"
        
        # ログディレクトリ作成
        self.recovery_log.parent.mkdir(exist_ok=True)
        self.state_file.parent.mkdir(exist_ok=True)
        
        # 復旧に必要なサービス
        self.required_services = [
            "rabbitmq-server",
        ]
        
        # 復旧に必要なワーカー
        self.required_workers = [
            "enhanced_task_worker",
            "intelligent_pm_worker", 
            "async_result_worker"
        ]
        
        # 復旧に必要なプロセス
        self.required_processes = [
            "elder_watchdog.sh",
            "start_elder_monitoring.py"
        ]
    
    def log_recovery(self, message: str, level: str = "INFO"):
        """復旧ログを記録"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        with open(self.recovery_log, "a") as f:
            f.write(log_entry)
        
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)
    
    def save_state(self):
        """現在の状態を保存"""
        state = {
            "timestamp": datetime.now().isoformat(),
            "services": self._get_service_states(),
            "workers": self._get_worker_states(),
            "processes": self._get_process_states(),
            "system_info": self._get_system_info()
        }
        
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)
        
        self.log_recovery(f"状態保存完了: {len(state['workers'])}ワーカー、{len(state['services'])}サービス")
    
    def load_state(self) -> Optional[Dict]:
        """保存された状態を読み込み"""
        if not self.state_file.exists():
            return None
        
        try:
            with open(self.state_file, "r") as f:
                return json.load(f)
        except Exception as e:
            self.log_recovery(f"状態読み込みエラー: {e}", "ERROR")
            return None
    
    def _get_service_states(self) -> Dict[str, str]:
        """サービス状態を取得"""
        states = {}
        for service in self.required_services:
            try:
                result = subprocess.run(
                    ["systemctl", "is-active", service],
                    capture_output=True, text=True
                )
                states[service] = result.stdout.strip()
            except Exception as e:
                states[service] = f"error: {e}"
        return states
    
    def _get_worker_states(self) -> Dict[str, bool]:
        """ワーカー状態を取得"""
        states = {}
        try:
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
            for worker in self.required_workers:
                states[worker] = worker in result.stdout
        except Exception as e:
            self.log_recovery(f"ワーカー状態取得エラー: {e}", "ERROR")
        return states
    
    def _get_process_states(self) -> Dict[str, bool]:
        """プロセス状態を取得"""
        states = {}
        try:
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
            for process in self.required_processes:
                states[process] = process in result.stdout
        except Exception as e:
            self.log_recovery(f"プロセス状態取得エラー: {e}", "ERROR")
        return states
    
    def _get_system_info(self) -> Dict:
        """システム情報を取得"""
        info = {
            "uptime": self._get_uptime(),
            "memory": self._get_memory_info(),
            "cpu": self._get_cpu_info()
        }
        return info
    
    def _get_uptime(self) -> str:
        """システムアップタイムを取得"""
        try:
            result = subprocess.run(["uptime"], capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return "unknown"
    
    def _get_memory_info(self) -> str:
        """メモリ情報を取得"""
        try:
            result = subprocess.run(["free", "-h"], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            if len(lines) > 1:
                return lines[1]  # Mem行
        except:
            pass
        return "unknown"
    
    def _get_cpu_info(self) -> str:
        """CPU情報を取得"""
        try:
            result = subprocess.run(["top", "-bn1"], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'Cpu(s)' in line:
                    return line.strip()
        except:
            pass
        return "unknown"
    
    def detect_sleep_recovery(self) -> bool:
        """スリープからの復旧を検出"""
        current_state = self.load_state()
        if not current_state:
            self.log_recovery("初回起動またはスリープ復旧検出")
            return True
        
        # 前回の保存からの時間差をチェック
        last_timestamp = datetime.fromisoformat(current_state["timestamp"])
        time_diff = datetime.now() - last_timestamp
        
        if time_diff > timedelta(minutes=10):  # 10分以上の空白
            self.log_recovery(f"スリープ復旧検出: {time_diff}の空白時間")
            return True
        
        # プロセスの状態チェック
        current_processes = self._get_process_states()
        for process, should_be_running in current_state.get("processes", {}).items():
            if should_be_running and not current_processes.get(process, False):
                self.log_recovery(f"プロセス停止検出: {process}")
                return True
        
        return False
    
    def recover_services(self):
        """サービスを復旧"""
        self.log_recovery("サービス復旧開始...")
        
        for service in self.required_services:
            try:
                # サービス状態確認
                result = subprocess.run(
                    ["systemctl", "is-active", service],
                    capture_output=True, text=True
                )
                
                if result.returncode != 0:
                    self.log_recovery(f"サービス復旧中: {service}")
                    # sudoが必要な場合は手動起動を促す
                    self.log_recovery(f"手動でサービス起動してください: sudo systemctl start {service}")
                else:
                    self.log_recovery(f"サービス正常: {service}")
                    
            except Exception as e:
                self.log_recovery(f"サービス復旧エラー {service}: {e}", "ERROR")
    
    def recover_workers(self):
        """ワーカーを復旧"""
        self.log_recovery("ワーカー復旧開始...")
        
        try:
            # check_and_fix_workers.py を実行
            worker_fix_script = self.project_root / "check_and_fix_workers.py"
            if worker_fix_script.exists():
                result = subprocess.run(
                    [sys.executable, str(worker_fix_script)],
                    cwd=self.project_root,
                    capture_output=True, text=True
                )
                
                if result.returncode == 0:
                    self.log_recovery("ワーカー復旧成功")
                else:
                    self.log_recovery(f"ワーカー復旧エラー: {result.stderr}", "ERROR")
            else:
                self.log_recovery("ワーカー復旧スクリプトが見つかりません", "WARNING")
                
        except Exception as e:
            self.log_recovery(f"ワーカー復旧エラー: {e}", "ERROR")
    
    def recover_processes(self):
        """プロセスを復旧"""
        self.log_recovery("プロセス復旧開始...")
        
        # エルダーウォッチドッグの復旧
        watchdog_script = self.project_root / "elder_watchdog.sh"
        if watchdog_script.exists():
            try:
                # 既存のウォッチドッグを停止
                subprocess.run(["pkill", "-f", "elder_watchdog.sh"], 
                              capture_output=True)
                
                # 新しいウォッチドッグを起動
                subprocess.run(
                    ["nohup", str(watchdog_script)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid
                )
                self.log_recovery("エルダーウォッチドッグ復旧完了")
                
            except Exception as e:
                self.log_recovery(f"エルダーウォッチドッグ復旧エラー: {e}", "ERROR")
        
        # エルダー監視の復旧
        elder_monitoring = self.project_root / "start_elder_monitoring.py"
        if elder_monitoring.exists():
            try:
                subprocess.run(
                    ["nohup", sys.executable, str(elder_monitoring)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid
                )
                self.log_recovery("エルダー監視復旧完了")
                
            except Exception as e:
                self.log_recovery(f"エルダー監視復旧エラー: {e}", "ERROR")
    
    def create_startup_script(self):
        """自動起動スクリプトを作成"""
        startup_content = f'''#!/bin/bash
# WSL自動起動スクリプト
# Elders Guild システム復旧用

PROJECT_ROOT="{self.project_root}"
LOG_FILE="$PROJECT_ROOT/logs/auto_startup.log"

echo "[$(date)] WSL自動起動スクリプト実行開始" >> "$LOG_FILE"

# Python環境の復旧
cd "$PROJECT_ROOT"
python3 scripts/wsl_sleep_recovery_system.py >> "$LOG_FILE" 2>&1

echo "[$(date)] WSL自動起動スクリプト実行完了" >> "$LOG_FILE"
'''
        
        with open(self.startup_script, "w") as f:
            f.write(startup_content)
        
        # 実行権限を付与
        os.chmod(self.startup_script, 0o755)
        
        self.log_recovery(f"自動起動スクリプト作成完了: {self.startup_script}")
    
    def create_windows_batch(self):
        """Windows側の自動起動バッチファイルを作成"""
        batch_content = '''@echo off
echo Starting Elders Guild WSL Recovery System...

REM WSLが起動していることを確認
wsl --list --running | findstr "Ubuntu" >nul
if %errorlevel% neq 0 (
    echo WSL not running, starting WSL...
    wsl --distribution Ubuntu --exec echo "WSL started"
)

REM 復旧スクリプトを実行
wsl --distribution Ubuntu --exec bash -c "cd /home/aicompany/ai_co && ./scripts/auto_startup.sh"

echo Elders Guild WSL Recovery System started!
pause
'''
        
        batch_file = self.project_root / "start_ai_company.bat"
        with open(batch_file, "w") as f:
            f.write(batch_content)
        
        self.log_recovery(f"Windows バッチファイル作成完了: {batch_file}")
    
    def install_cron_job(self):
        """cron ジョブをインストール（定期チェック用）"""
        cron_command = f"*/5 * * * * cd {self.project_root} && python3 scripts/wsl_sleep_recovery_system.py --monitor"
        
        try:
            # 既存のcrontabを取得
            result = subprocess.run(["crontab", "-l"], 
                                   capture_output=True, text=True)
            
            existing_cron = result.stdout if result.returncode == 0 else ""
            
            # 復旧スクリプトのcronが既に存在するかチェック
            if "wsl_sleep_recovery_system.py" not in existing_cron:
                new_cron = existing_cron + "\n" + cron_command + "\n"
                
                # 新しいcrontabを設定
                process = subprocess.Popen(["crontab", "-"], 
                                         stdin=subprocess.PIPE, 
                                         text=True)
                process.communicate(input=new_cron)
                
                self.log_recovery("cron ジョブインストール完了")
            else:
                self.log_recovery("cron ジョブは既に存在します")
                
        except Exception as e:
            self.log_recovery(f"cron ジョブインストールエラー: {e}", "ERROR")
    
    def run_recovery(self):
        """復旧プロセスを実行"""
        self.log_recovery("=" * 60)
        self.log_recovery("WSL スリープ復旧システム開始")
        self.log_recovery("=" * 60)
        
        # スリープ復旧の検出
        if self.detect_sleep_recovery():
            self.log_recovery("復旧処理を開始します...")
            
            # 段階的復旧
            self.recover_services()
            time.sleep(2)
            
            self.recover_workers()
            time.sleep(2)
            
            self.recover_processes()
            time.sleep(2)
            
            self.log_recovery("復旧処理完了")
        else:
            self.log_recovery("システムは正常に動作しています")
        
        # 現在の状態を保存
        self.save_state()
        
        self.log_recovery("=" * 60)
        self.log_recovery("WSL スリープ復旧システム終了")
        self.log_recovery("=" * 60)
    
    def monitor_mode(self):
        """監視モード（cron用）"""
        if self.detect_sleep_recovery():
            self.run_recovery()

def main():
    """メイン処理"""
    recovery_system = WSLSleepRecoverySystem()
    
    # コマンドライン引数チェック
    if len(sys.argv) > 1 and sys.argv[1] == "--monitor":
        recovery_system.monitor_mode()
    elif len(sys.argv) > 1 and sys.argv[1] == "--install":
        # インストールモード
        recovery_system.create_startup_script()
        recovery_system.create_windows_batch()
        recovery_system.install_cron_job()
        print("WSL スリープ復旧システムのインストールが完了しました!")
        print("1. Windows側で start_ai_company.bat を実行してください")
        print("2. または、WSL起動時に ./scripts/auto_startup.sh を実行してください")
    else:
        # 通常の復旧モード
        recovery_system.run_recovery()

if __name__ == "__main__":
    main()