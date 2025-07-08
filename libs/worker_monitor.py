#!/usr/bin/env python3
"""
Worker Monitor - ワーカーとシステムの監視（修正版）
"""
import subprocess
import psutil
import pika
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger('WorkerMonitor')

class WorkerMonitor:
    def __init__(self, config_file=None):
        """ワーカー監視システムの初期化"""
        if config_file is None:
            config_file = Path(__file__).parent.parent / "config" / "scaling.conf"
        self.config = self._load_config(config_file)
        self.rabbitmq_host = 'localhost'
        
    def _load_config(self, config_file):
        """設定ファイル読み込み"""
        config = {}
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # 数値として解析を試みる
                        try:
                            config[key] = int(value)
                        except ValueError:
                            config[key] = value
            logger.info(f"設定読み込み完了: {config}")
        except Exception as e:
            logger.error(f"設定読み込みエラー: {e}")
        return config
    
    def get_queue_length(self, queue_name='task_queue'):
        """RabbitMQキューの長さを取得（Pikaを使用）"""
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(self.rabbitmq_host))
            channel = connection.channel()
            
            # キューを宣言（passive=Trueで既存のキューのみ確認）
            method = channel.queue_declare(queue=queue_name, durable=True, passive=True)
            queue_length = method.method.message_count
            
            connection.close()
            return queue_length
            
        except Exception as e:
            logger.error(f"キュー長取得エラー: {e}")
            return 0
    
    def get_active_workers(self):
        """稼働中のTaskWorkerプロセス情報を取得（改善版）"""
        workers = []
        try:
            # psutilを使ってプロセスを探す
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and len(cmdline) >= 3:
                        # Pythonプロセスでtask_worker.pyを実行しているものを探す
                        if 'python' in cmdline[0] and any('task_worker.py' in arg for arg in cmdline):
                            # worker IDを探す
                            worker_id = None
                            for i, arg in enumerate(cmdline):
                                if 'task_worker.py' in arg and i + 1 < len(cmdline):
                                    # 次の引数がworker ID
                                    worker_id = cmdline[i + 1]
                                    break
                            
                            if worker_id and worker_id.startswith('worker-'):
                                # RabbitMQ接続をチェック
                                has_rabbitmq = self._check_worker_rabbitmq_connection(worker_id)
                                
                                workers.append({
                                    'pid': proc.info['pid'],
                                    'cpu': proc.cpu_percent(interval=0.1),
                                    'mem': proc.memory_percent(),
                                    'worker_id': worker_id,
                                    'start_time': datetime.fromtimestamp(proc.create_time()).strftime('%H:%M:%S'),
                                    'has_rabbitmq_connection': has_rabbitmq
                                })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            logger.error(f"ワーカー情報取得エラー: {e}")
        
        return workers
    
    def _check_worker_rabbitmq_connection(self, worker_id):
        """ワーカーのRabbitMQ接続状態をチェック"""
        try:
            # RabbitMQのコンシューマーを確認
            connection = pika.BlockingConnection(pika.ConnectionParameters(self.rabbitmq_host))
            channel = connection.channel()
            
            # task_queueのコンシューマー数を確認
            method = channel.queue_declare(queue='task_queue', durable=True, passive=True)
            consumer_count = method.method.consumer_count
            
            connection.close()
            
            # コンシューマーが1つ以上あれば接続ありと判断（簡易的）
            return consumer_count > 0
            
        except Exception:
            return False
    
    def get_system_metrics(self):
        """システムメトリクス（CPU、メモリ使用率）を取得"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'load_average': psutil.getloadavg()[0],  # 1分間の負荷平均
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"システムメトリクス取得エラー: {e}")
            return {
                'cpu_percent': 0,
                'memory_percent': 0,
                'load_average': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_worker_health(self, worker_id):
        """特定ワーカーの健康状態を確認"""
        workers = self.get_active_workers()
        for worker in workers:
            if worker['worker_id'] == worker_id:
                # CPU使用率が異常に高い、またはメモリ使用率が高い場合は不健康
                is_healthy = (
                    worker['cpu'] < 90 and 
                    worker['mem'] < 90 and
                    worker.get('has_rabbitmq_connection', False)
                )
                return {
                    'worker_id': worker_id,
                    'pid': worker['pid'],
                    'healthy': is_healthy,
                    'cpu': worker['cpu'],
                    'mem': worker['mem'],
                    'has_rabbitmq_connection': worker.get('has_rabbitmq_connection', False)
                }
        return None
    
    def get_all_metrics(self):
        """全ての監視メトリクスを統合して返す"""
        workers = self.get_active_workers()
        return {
            'queue_length': self.get_queue_length(),
            'active_workers': len(workers),
            'worker_details': workers,
            'system': self.get_system_metrics(),
            'timestamp': datetime.now().isoformat()
        }

if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    monitor = WorkerMonitor()
    
    print("=== Worker Monitor Test ===")
    metrics = monitor.get_all_metrics()
    print(json.dumps(metrics, indent=2, ensure_ascii=False))