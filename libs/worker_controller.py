#!/usr/bin/env python3
"""
Worker Controller - ワーカーの起動・停止制御（修正版）
"""
import subprocess
import time
import signal
import os
import logging
from pathlib import Path

logger = logging.getLogger('WorkerController')

class WorkerController:
    def __init__(self, config_file=None):
        """ワーカー制御システムの初期化"""
        if config_file is None:
            config_file = Path(__file__).parent.parent / "config" / "scaling.conf"
        self.config = self._load_config(config_file)
        self.ai_company_root = Path(__file__).parent.parent
        
    def _load_config(self, config_file):
        """設定ファイル読み込み"""
        config = {
            'WORKER_START_DELAY': 2,
            'WORKER_STOP_DELAY': 1,
            'GRACEFUL_SHUTDOWN_TIMEOUT': 30
        }
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        try:
                            config[key] = int(value)
                        except ValueError:
                            config[key] = value
        except Exception as e:
            logger.error(f"設定読み込みエラー: {e}")
        return config
    
    def start_worker(self, worker_id):
        """新しいワーカーを起動（新しいペインで）"""
        try:
            # tmuxセッションの存在確認
            check_tmux = subprocess.run(
                ['tmux', 'has-session', '-t', 'elders_guild'],
                capture_output=True
            )
            
            if check_tmux.returncode == 0:
                # 新しいウィンドウを作成してワーカーを起動
                window_name = worker_id
                
                # ウィンドウが既に存在するか確認
                check_window = subprocess.run(
                    ['tmux', 'list-windows', '-t', 'elders_guild', '-F', '#{window_name}'],
                    capture_output=True, text=True
                )
                
                if window_name in check_window.stdout:
                    # 既存のウィンドウを削除
                    subprocess.run(['tmux', 'kill-window', '-t', f'elders_guild:{window_name}'])
                    time.sleep(0.5)
                
                # 新しいウィンドウを作成して起動
                cmd = f"cd {self.ai_company_root} && source venv/bin/activate && python3 workers/task_worker.py {worker_id}"
                subprocess.run([
                    'tmux', 'new-window', '-t', 'elders_guild', '-n', window_name, cmd
                ])
                
                logger.info(f"✅ ワーカー起動 (tmux:{window_name}): {worker_id}")
                
            else:
                # tmuxがない場合は直接起動
                self._start_worker_direct(worker_id)
                
            # 起動待機
            time.sleep(self.config.get('WORKER_START_DELAY', 2))
            return True
            
        except Exception as e:
            logger.error(f"ワーカー起動エラー: {worker_id} - {e}")
            return False
    
    def _start_worker_direct(self, worker_id):
        """ワーカーを直接起動（tmuxなし）"""
        try:
            activate_script = self.ai_company_root / 'venv' / 'bin' / 'activate'
            worker_script = self.ai_company_root / 'workers' / 'task_worker.py'
            
            # 起動スクリプトを作成
            start_script = f"""#!/bin/bash
cd {self.ai_company_root}
source {activate_script}
exec python3 {worker_script} {worker_id}
"""
            
            # 一時ファイルに保存
            temp_script = Path(f"/tmp/start_worker_{worker_id}.sh")
            temp_script.write_text(start_script)
            temp_script.chmod(0o755)
            
            # バックグラウンドで実行
            subprocess.Popen(
                [str(temp_script)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            
            logger.info(f"✅ ワーカー起動 (直接): {worker_id}")
            
            # 一時ファイルを削除（少し待ってから）
            time.sleep(1)
            temp_script.unlink(missing_ok=True)
            
        except Exception as e:
            logger.error(f"直接起動エラー: {e}")
            raise
    
    def stop_worker(self, worker_id, graceful=True):
        """ワーカーを停止"""
        try:
            # プロセスを検索
            ps_cmd = ['ps', 'aux']
            result = subprocess.run(ps_cmd, capture_output=True, text=True)
            
            for line in result.stdout.split('\n'):
                if 'task_worker.py' in line and worker_id in line:
                    parts = line.split()
                    if len(parts) > 1:
                        pid = int(parts[1])
                        
                        if graceful:
                            # グレースフルシャットダウン
                            os.kill(pid, signal.SIGTERM)
                            logger.info(f"📤 SIGTERM送信: {worker_id} (PID: {pid})")
                            
                            # 終了を待つ
                            timeout = self.config.get('GRACEFUL_SHUTDOWN_TIMEOUT', 30)
                            for _ in range(timeout):
                                if not self._is_process_alive(pid):
                                    logger.info(f"✅ ワーカー正常終了: {worker_id}")
                                    break
                                time.sleep(1)
                            else:
                                # タイムアウトしたら強制終了
                                os.kill(pid, signal.SIGKILL)
                                logger.warning(f"⚠️ ワーカー強制終了: {worker_id}")
                        else:
                            # 即座に強制終了
                            os.kill(pid, signal.SIGKILL)
                            logger.info(f"💥 ワーカー強制終了: {worker_id}")
                        
                        # 停止待機
                        time.sleep(self.config.get('WORKER_STOP_DELAY', 1))
                        return True
            
            logger.warning(f"ワーカーが見つかりません: {worker_id}")
            return False
            
        except Exception as e:
            logger.error(f"ワーカー停止エラー: {worker_id} - {e}")
            return False
    
    def restart_worker(self, worker_id):
        """ワーカーを再起動"""
        logger.info(f"🔄 ワーカー再起動: {worker_id}")
        
        # 停止
        if self.stop_worker(worker_id, graceful=True):
            # 起動
            return self.start_worker(worker_id)
        else:
            # 停止に失敗しても起動を試みる
            logger.warning(f"停止に失敗しましたが起動を試みます: {worker_id}")
            return self.start_worker(worker_id)
    
    def scale_workers(self, target_count):
        """ワーカー数を調整"""
        try:
            current_workers = self._get_current_workers()
            current_count = len(current_workers)
            
            if current_count < target_count:
                # スケールアップ
                for i in range(current_count + 1, target_count + 1):
                    worker_id = f"worker-{i}"
                    if not self.start_worker(worker_id):
                        logger.error(f"スケールアップ失敗: {worker_id}")
                        return False
            elif current_count > target_count:
                # スケールダウン
                workers_to_stop = current_workers[target_count:]
                for worker_id in workers_to_stop:
                    if not self.stop_worker(worker_id):
                        logger.error(f"スケールダウン失敗: {worker_id}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"スケーリングエラー: {e}")
            return False
    
    def _get_current_workers(self):
        """現在のワーカーリストを取得"""
        workers = []
        ps_cmd = ['ps', 'aux']
        result = subprocess.run(ps_cmd, capture_output=True, text=True)
        
        for line in result.stdout.split('\n'):
            if 'task_worker.py' in line and 'worker-' in line:
                # worker IDを抽出
                for part in line.split():
                    if part.startswith('worker-'):
                        workers.append(part)
                        break
        
        return sorted(set(workers))
    
    def _is_process_alive(self, pid):
        """プロセスが生きているかチェック"""
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

if __name__ == "__main__":
    # テスト実行
    import sys
    controller = WorkerController()
    
    if len(sys.argv) > 2:
        action = sys.argv[1]
        worker_id = sys.argv[2]
        
        if action == "start":
            controller.start_worker(worker_id)
        elif action == "stop":
            controller.stop_worker(worker_id)
        elif action == "restart":
            controller.restart_worker(worker_id)
    else:
        print("Usage: worker_controller.py [start|stop|restart] worker-id")