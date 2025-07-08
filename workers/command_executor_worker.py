#!/usr/bin/env python3
"""
AI Command Executor Worker - BaseWorker継承版
AIが作成したコマンドを自動実行し、結果をログに保存
"""

import sys
import os
import time
import subprocess
import json
import shutil
from pathlib import Path
from datetime import datetime

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.base_worker import BaseWorker
from core import ErrorSeverity


class CommandExecutorWorker(BaseWorker):
    """AIが作成したコマンドを自動実行するワーカー"""
    
    def __init__(self, worker_id=None):
        super().__init__(worker_type='command_executor', worker_id=worker_id)
        
        # ディレクトリ設定
        self.base_dir = PROJECT_ROOT / "ai_commands"
        self.pending_dir = self.base_dir / "pending"
        self.running_dir = self.base_dir / "running"
        self.completed_dir = self.base_dir / "completed"
        self.logs_dir = self.base_dir / "logs"
        
        # ディレクトリ作成
        for dir_path in [self.pending_dir, self.running_dir, self.completed_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 実行間隔（秒）
        self.check_interval = 5
    
    def setup_queues(self):
        """コマンド実行用キューの設定"""
        self.input_queue = 'ai_command'
        self.output_queue = 'ai_results'
    
    def process_message(self, ch, method, properties, body):
        """コマンド実行タスク処理"""
        try:
            task_data = json.loads(body)
            command_id = task_data.get('command_id', f"cmd_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            command = task_data.get('command', '')
            description = task_data.get('description', 'No description')
            
            self.logger.info(f"🛠️ コマンド実行要求受信: {command_id}")
            self.logger.info(f"コマンド: {command}")
            
            # コマンド実行
            result = self._execute_command(command_id, command, description)
            
            # 結果を返送
            response = {
                'command_id': command_id,
                'command': command,
                'status': result['status'],
                'output': result['output'],
                'error': result['error'],
                'duration': result['duration'],
                'worker_id': self.worker_id
            }
            
            self._send_result(response)
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            self.logger.info(f"✅ コマンド実行完了: {command_id}")
            
        except Exception as e:
            # コマンド実行エラー
            context = {
                'operation': 'command_process_message',
                'command_id': task_data.get('command_id', 'unknown') if 'task_data' in locals() else 'unknown',
                'command': task_data.get('command', '')[:100] if 'task_data' in locals() else 'unknown',
                'description': task_data.get('description', '') if 'task_data' in locals() else ''
            }
            self.handle_error(e, context, severity=ErrorSeverity.HIGH)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def _execute_command(self, command_id: str, command: str, description: str) -> dict:
        """コマンドを安全に実行"""
        start_time = time.time()
        
        try:
            # 安全性チェック
            if not self._is_safe_command(command):
                return {
                    'status': 'rejected',
                    'output': '',
                    'error': 'Command rejected for security reasons',
                    'duration': 0
                }
            
            # コマンド実行（タイムアウト付き）
            self.logger.info(f"⚡ 実行開始: {command}")
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,  # 5分タイムアウト
                cwd=PROJECT_ROOT
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                self.logger.info(f"✅ 実行成功: {command_id} ({duration:.2f}s)")
                status = 'success'
            else:
                self.logger.warning(f"⚠️ 実行失敗: {command_id} (code: {result.returncode})")
                status = 'failed'
            
            # ログファイルに保存
            self._save_execution_log(command_id, command, description, result, duration)
            
            return {
                'status': status,
                'output': result.stdout,
                'error': result.stderr,
                'duration': duration
            }
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            self.logger.error(f"⏰ タイムアウト: {command_id}")
            return {
                'status': 'timeout',
                'output': '',
                'error': 'Command execution timed out after 5 minutes',
                'duration': duration
            }
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"💥 実行例外: {command_id} - {e}")
            return {
                'status': 'error',
                'output': '',
                'error': str(e),
                'duration': duration
            }
    
    def _is_safe_command(self, command: str) -> bool:
        """コマンドの安全性をチェック"""
        # 危険なコマンドのブラックリスト
        dangerous_patterns = [
            'rm -rf /',
            'dd if=',
            'mkfs',
            'fdisk',
            'format',
            'del /f /q',
            'rmdir /s',
            'shutdown',
            'reboot',
            'halt',
            'poweroff',
            'passwd',
            'su ',
            'sudo su',
            'chmod 777',
            'chown root',
            '> /dev/',
            'curl http',
            'wget http',
            'nc ',
            'netcat',
            'telnet',
            'ssh ',
            'scp ',
            'rsync'
        ]
        
        command_lower = command.lower()
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                self.logger.warning(f"🚨 危険なコマンドを検出: {pattern}")
                return False
        
        return True
    
    def _save_execution_log(self, command_id: str, command: str, description: str, result: subprocess.CompletedProcess, duration: float):
        """実行ログを保存"""
        log_data = {
            'command_id': command_id,
            'command': command,
            'description': description,
            'executed_at': datetime.now().isoformat(),
            'duration': duration,
            'return_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'worker_id': self.worker_id
        }
        
        log_file = self.logs_dir / f"{command_id}.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"📝 実行ログ保存: {log_file}")
    
    def _send_result(self, result_data: dict):
        """結果をOutputキューに送信"""
        try:
            self.channel.basic_publish(
                exchange='',
                routing_key=self.output_queue,
                body=json.dumps(result_data, ensure_ascii=False),
                properties=self._get_message_properties()
            )
            self.logger.info(f"📤 結果送信: {result_data['command_id']}")
        except Exception as e:
            self.logger.error(f"結果送信エラー: {e}")
    
    def run_file_monitor(self):
        """ファイル監視モード（非同期処理用）"""
        self.logger.info("📁 ファイル監視モード開始")
        
        while self.running:
            try:
                # pending ディレクトリの .json ファイルをチェック
                for command_file in self.pending_dir.glob("*.json"):
                    self._process_command_file(command_file)
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                self.logger.info("🛑 ファイル監視停止")
                break
            except Exception as e:
                self.logger.error(f"ファイル監視エラー: {e}")
                time.sleep(self.check_interval)
    
    def _process_command_file(self, command_file: Path):
        """コマンドファイルを処理"""
        try:
            # running ディレクトリに移動
            running_file = self.running_dir / command_file.name
            shutil.move(str(command_file), str(running_file))
            
            # コマンド実行
            with open(running_file, 'r', encoding='utf-8') as f:
                command_data = json.load(f)
            
            command_id = command_data.get('id', running_file.stem)
            command = command_data.get('command', '')
            description = command_data.get('description', '')
            
            result = self._execute_command(command_id, command, description)
            
            # completed ディレクトリに移動
            completed_file = self.completed_dir / command_file.name
            shutil.move(str(running_file), str(completed_file))
            
            self.logger.info(f"✅ ファイル処理完了: {command_file.name}")
            
        except Exception as e:
            self.logger.error(f"ファイル処理エラー: {e}")


    def cleanup(self):
        """TODO: cleanupメソッドを実装してください"""
        pass

    def stop(self):
        """TODO: stopメソッドを実装してください"""
        pass

    def initialize(self) -> None:
        """ワーカーの初期化処理"""
        # TODO: 初期化ロジックを実装してください
        logger.info(f"{self.__class__.__name__} initialized")
        pass

    def handle_error(self):
        """TODO: handle_errorメソッドを実装してください"""
        pass

    def get_status(self):
        """TODO: get_statusメソッドを実装してください"""
        pass

    def validate_config(self):
        """TODO: validate_configメソッドを実装してください"""
        pass

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Command Executor Worker')
    parser.add_argument('--mode', choices=['queue', 'file'], default='queue',
                       help='実行モード: queue (RabbitMQ) または file (ファイル監視)')
    parser.add_argument('--worker-id', help='ワーカーID')
    
    args = parser.parse_args()
    
    worker = CommandExecutorWorker(worker_id=args.worker_id)
    
    if args.mode == 'file':
        worker.run_file_monitor()
    else:
        worker.start()