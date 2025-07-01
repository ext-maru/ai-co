#!/usr/bin/env python3
import sys
sys.path.append("/root/ai_co")
import sys
import pika
import json
import logging
import subprocess
from libs.worker_monitor import WorkerMonitor
from libs.worker_controller import WorkerController
from libs.scaling_policy import ScalingPolicy
from libs.health_checker import HealthChecker
import threading

import os
import traceback
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_DIR / "output"
LOG_DIR = PROJECT_DIR / "logs"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [PMWorker] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "pm_worker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PMWorker")

class PMWorker:
    def __init__(self):
        self.model = "claude-opus-4-20250514"
        # 動的管理関連
        self.monitor = WorkerMonitor()
        self.controller = WorkerController()
        self.policy = ScalingPolicy()
        self.health_checker = HealthChecker()
        self.scaling_enabled = True
        self.check_interval = 30
        self.health_check_interval = 60

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue='pm_task_queue', durable=True)
            self.channel.queue_declare(queue='result_queue', durable=True)
            logger.info("RabbitMQ接続成功")
            return True
        except Exception as e:
            logger.error(f"RabbitMQ接続失敗: {e}")
            return False

    def start_result_monitoring(self):
        """結果キューを監視してGitコミット"""
        try:
            # result_queueも監視
            self.channel.queue_declare(queue='result_queue', durable=True)
            self.channel.basic_consume(
                queue='result_queue',
                on_message_callback=self.handle_task_completion,
                auto_ack=True
            )
            logger.info("📁 結果監視開始 - ファイル生成時自動Git処理")
        except Exception as e:
            logger.error(f"結果監視開始失敗: {e}")

    def handle_task_completion(self, ch, method, properties, body):
        """タスク完了時の自動Git処理"""
        try:
            result = json.loads(body)
            task_id = result.get('task_id', 'unknown')
            status = result.get('status', 'unknown')
            output_file = result.get('output_file', '')

            logger.info(f"📋 タスク完了検知: {task_id} ({status})")

            if status == "completed":
                # 新しいファイルが生成されたかチェック
                new_files = self.detect_new_files()
                
                if new_files:
                    logger.info(f"📁 新規ファイル検出: {len(new_files)}件")
                    for file_path in new_files:
                        logger.info(f"  - {file_path}")
                    
                    # Git自動コミット
                    commit_success = self.auto_git_commit(task_id, new_files)
                    
                    if commit_success:
                        logger.info(f"✅ Git自動コミット成功: {task_id}")
                    else:
                        logger.warning(f"⚠️ Git自動コミット失敗: {task_id}")
                else:
                    logger.info(f"📁 新規ファイル未検出: {task_id}")

        except Exception as e:
            logger.error(f"タスク完了処理エラー: {e}")
            traceback.print_exc()

    def detect_new_files(self):
        """新しく生成されたファイルを検出"""
        try:
            # 最近5分以内に作成/更新されたファイルを検索
            import time
            current_time = time.time()
            recent_threshold = current_time - 300  # 5分前

            new_files = []
            
            # outputディレクトリ内の.py, .txt, .js, .html, .css等を検索
            extensions = ['*.py', '*.txt', '*.js', '*.html', '*.css', '*.json', '*.md']
            
            for ext in extensions:
                files = OUTPUT_DIR.rglob(ext)
                for file_path in files:
                    if file_path.stat().st_mtime > recent_threshold:
                        new_files.append(str(file_path.relative_to(PROJECT_DIR)))
            
            return new_files

        except Exception as e:
            logger.error(f"新規ファイル検出エラー: {e}")
            return []

    def auto_git_commit(self, task_id, new_files):
        """自動Gitコミット"""
        try:
            os.chdir(PROJECT_DIR)
            
            # Git状態確認
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                logger.error(f"Git状態確認失敗: {result.stderr}")
                return False

            # 変更があるかチェック
            if not result.stdout.strip():
                logger.info("Git: 変更なし")
                return True

            # 新規ファイルをステージング
            for file_path in new_files:
                add_result = subprocess.run(['git', 'add', file_path], 
                                          capture_output=True, text=True, timeout=10)
                if add_result.returncode == 0:
                    logger.info(f"Git add: {file_path}")
                else:
                    logger.warning(f"Git add失敗: {file_path} - {add_result.stderr}")

            # その他の変更もステージング
            subprocess.run(['git', 'add', '.'], capture_output=True, timeout=10)

            # コミット作成
            commit_message = f"🤖 AI自動生成: {task_id} - {len(new_files)}ファイル追加"
            
            if new_files:
                commit_message += f"\n\n新規ファイル:\n"
                for file_path in new_files:
                    commit_message += f"- {file_path}\n"
                
            commit_message += f"\nタイムスタンプ: {datetime.now().isoformat()}"

            commit_result = subprocess.run([
                'git', 'commit', '-m', commit_message
            ], capture_output=True, text=True, timeout=30)

            if commit_result.returncode == 0:
                logger.info(f"Git commit成功: {commit_message.split()[0]}")
                
                # 自動プッシュ
                push_result = subprocess.run([
                    'git', 'push', 'origin', 'master'
                ], capture_output=True, text=True, timeout=60)
                
                if push_result.returncode == 0:
                    logger.info("Git push成功")
                    return True
                else:
                    logger.error(f"Git push失敗: {push_result.stderr}")
                    return False
            else:
                if "nothing to commit" in commit_result.stdout:
                    logger.info("Git: コミットする変更なし")
                    return True
                else:
                    logger.error(f"Git commit失敗: {commit_result.stderr}")
                    return False

        except subprocess.TimeoutExpired:
            logger.error("Git処理タイムアウト")
            return False
        except Exception as e:
            logger.error(f"Git自動コミットエラー: {e}")
            traceback.print_exc()
            return False

    def process_pm_task(self, ch, method, properties, body):
        """PM専用タスク処理"""
        try:
            task = json.loads(body)
            task_id = task.get("task_id", f"pm_unknown_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            command = task.get("command", "")
            params = task.get("params", {})

            logger.info(f"PMタスク受信: {task_id} コマンド: {command}")

            if command == "git_commit":
                # 手動Gitコミット要求
                files = params.get("files", [])
                success = self.auto_git_commit(task_id, files)
                logger.info(f"手動Git処理: {'成功' if success else '失敗'}")
            else:
                logger.warning(f"未知のコマンド: {command}")

            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"PMタスク処理例外: {e}")
            traceback.print_exc()
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    
    def start_scaling_monitor(self):
        """スケーリング監視スレッドを開始"""
        def monitor_and_scale():
            logger.info("🚀 スケーリング監視開始")
            while self.scaling_enabled:
                try:
                    # メトリクス取得
                    metrics = self.monitor.get_all_metrics()
                    logger.info(f"📊 メトリクス: ワーカー={metrics['active_workers']}, キュー={metrics['queue_length']}")
                    
                    # スケーリング判定
                    action, target = self.policy.should_scale(metrics)
                    
                    if action != 'none' and target is not None:
                        current = metrics['active_workers']
                        logger.info(f"🎯 スケーリング実行: {action} ({current} → {target})")
                        
                        # スケーリング実行
                        success = self.controller.scale_workers(target)
                        
                        if success:
                            self.policy.record_scaling(action, current, target)
                            logger.info(f"✅ スケーリング成功")
                            
                            # Slack通知
                            if hasattr(self, 'slack') and self.slack:
                                message = f"🔄 ワーカー自動スケーリング\n"
                                message += f"アクション: {'スケールアップ' if action == 'up' else 'スケールダウン'}\n"
                                message += f"ワーカー数: {current} → {target}\n"
                                message += f"キュー長: {metrics['queue_length']}"
                                self.slack.send_task_completion_simple(
                                    task_id=f"scaling_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                                    worker="pm_worker",
                                    prompt="自動スケーリング",
                                    response=message
                                )
                        else:
                            logger.error(f"❌ スケーリング失敗")
                    
                except Exception as e:
                    logger.error(f"スケーリング監視エラー: {e}")
                
                # 次回チェックまで待機
                time.sleep(self.check_interval)
        
        # 監視スレッド開始
        scaling_thread = threading.Thread(target=monitor_and_scale, daemon=True)
        scaling_thread.start()
        logger.info(f"📊 スケーリング監視スレッド開始 (間隔: {self.check_interval}秒)")

    
    def start_health_monitor(self):
        """ヘルスチェック監視スレッドを開始"""
        def monitor_health():
            logger.info("🏥 ヘルスチェック監視開始")
            while self.scaling_enabled:  # スケーリングと同じフラグを使用
                try:
                    # 全ワーカーの健康状態をチェック
                    workers = self.monitor.get_active_workers()
                    unhealthy_count = 0
                    
                    for worker_info in workers:
                        health_status = self.health_checker.check_worker_health(worker_info)
                        
                        if not health_status['healthy']:
                            unhealthy_count += 1
                            worker_id = worker_info['worker_id']
                            
                            # 再起動が必要か判断
                            if self.health_checker.should_restart_worker(worker_id):
                                logger.warning(f"🔄 {worker_id} の再起動を実行")
                                
                                # 再起動実行
                                success = self.controller.restart_worker(worker_id)
                                
                                if success:
                                    self.health_checker.record_restart(worker_id)
                                    logger.info(f"✅ {worker_id} 再起動成功")
                                    
                                    # Slack通知
                                    if hasattr(self, 'slack') and self.slack:
                                        issues_text = ', '.join(health_status['issues'])
                                        message = f"🔄 ワーカー自動再起動\n"
                                        message += f"ワーカー: {worker_id}\n"
                                        message += f"理由: {issues_text}"
                                        self.slack.send_task_completion_simple(
                                            task_id=f"health_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                                            worker="pm_worker",
                                            prompt="ヘルスチェック",
                                            response=message
                                        )
                                else:
                                    logger.error(f"❌ {worker_id} 再起動失敗")
                    
                    if unhealthy_count > 0:
                        logger.info(f"⚠️ 不健康なワーカー: {unhealthy_count}/{len(workers)}")
                    
                except Exception as e:
                    logger.error(f"ヘルスチェックエラー: {e}")
                
                # 次回チェックまで待機
                time.sleep(self.health_check_interval)
        
        # 監視スレッド開始
        health_thread = threading.Thread(target=monitor_health, daemon=True)
        health_thread.start()
        logger.info(f"🏥 ヘルスチェック監視スレッド開始 (間隔: {self.health_check_interval}秒)")

    def start(self):
        self.start_scaling_monitor()
        self.start_health_monitor()
        if not self.connect():
            return
        
        # PM専用タスクキューとresult_queueの両方を監視
        self.channel.basic_qos(prefetch_count=1)
        
        # PM専用タスク処理
        self.channel.basic_consume(queue='pm_task_queue', on_message_callback=self.process_pm_task)
        
        # 結果監視（自動Git処理）
        self.start_result_monitoring()
        
        logger.info("🚀 PM Worker起動 - 自動Git機能付き")
        logger.info("📋 監視中: pm_task_queue (PM専用)")
        logger.info("📁 監視中: result_queue (自動Git)")
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("PM Worker停止中...")
            self.channel.stop_consuming()
            self.connection.close()

if __name__ == "__main__":
    worker = PMWorker()
    worker.start()
