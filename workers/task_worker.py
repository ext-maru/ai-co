#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import pika
import traceback
from datetime import datetime
from pathlib import Path

# プロジェクトルート
PROJECT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_DIR / "output"
LOG_DIR = PROJECT_DIR / "logs"

# ログ設定
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "task_worker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TaskWorker")

class TaskWorker:
    def __init__(self, worker_id="worker-1"):
        self.worker_id = worker_id
        self.model = "claude-sonnet-4-20250514"  # 正しいモデル名
        
    def connect(self):
        """RabbitMQ接続"""
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters('localhost')
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue='task_queue', durable=True)
            self.channel.queue_declare(queue='result_queue', durable=True)
            logger.info(f"{self.worker_id} - RabbitMQ接続成功")
            return True
        except Exception as e:
            logger.error(f"RabbitMQ接続失敗: {e}")
            return False
    
    def process_task(self, ch, method, properties, body):
        """タスク処理"""
        try:
            task = json.loads(body)
            task_id = task.get('task_id', f'unknown_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            prompt = task.get('prompt', '')
            
            logger.info(f"タスク受信: {task_id}")
            logger.info(f"プロンプト: {prompt[:100]}...")
            
            # 出力ファイルパス
            output_file = OUTPUT_DIR / f"task_{task_id}.txt"
            logger.info(f"出力先: {output_file}")
            
            # Claude CLI実行
            if self.check_claude_cli():
                # 正しいモデル名で実行
                cmd = ["claude", "--model", self.model, "--max-tokens", "4000"]
                logger.info(f"コマンド実行: {' '.join(cmd)}")
                
                try:
                    # プロンプトを標準入力で渡す
                    result = subprocess.run(
                        cmd,
                        input=prompt,
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    
                    logger.info(f"実行完了 - リターンコード: {result.returncode}")
                    
                    if result.returncode == 0:
                        output_text = result.stdout
                        logger.info(f"出力文字数: {len(output_text)}")
                    else:
                        output_text = f"エラー: {result.stderr}"
                        logger.error(f"Claude CLIエラー: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    output_text = "エラー: タイムアウト (5分)"
                    logger.error("Claude CLIタイムアウト")
                    
            else:
                # シミュレーションモード
                logger.warning("Claude CLI未検出 - シミュレーションモード")
                output_text = f"[シミュレーション]\nタスクID: {task_id}\nプロンプト: {prompt}\n\nシミュレーション応答です。"
            
            # ファイル保存（詳細ログ付き）
            try:
                logger.info(f"ファイル保存開始: {output_file}")
                
                # メタデータ付きで保存
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"=== Task Information ===\n")
                    f.write(f"Task ID: {task_id}\n")
                    f.write(f"Worker: {self.worker_id}\n")
                    f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                    f.write(f"Model: {self.model}\n")
                    f.write(f"\n=== Prompt ===\n")
                    f.write(prompt)
                    f.write(f"\n\n=== Response ===\n")
                    f.write(output_text)
                    f.write(f"\n\n=== End ===\n")
                
                # ファイル存在確認
                if output_file.exists():
                    file_size = output_file.stat().st_size
                    logger.info(f"ファイル保存成功: {output_file} (サイズ: {file_size} bytes)")
                else:
                    logger.error(f"ファイルが作成されませんでした: {output_file}")
                    
            except Exception as e:
                logger.error(f"ファイル保存エラー: {e}")
                traceback.print_exc()
            
            # 結果をresult_queueに送信
            result_data = {
                "task_id": task_id,
                "worker": self.worker_id,
                "status": "completed",
                "output_file": str(output_file),
                "timestamp": datetime.now().isoformat()
            }
            
            self.channel.basic_publish(
                exchange='',
                routing_key='result_queue',
                body=json.dumps(result_data),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"タスク完了: {task_id}")
            
        except Exception as e:
            logger.error(f"タスク処理エラー: {e}")
            traceback.print_exc()
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def check_claude_cli(self):
        """Claude CLI確認"""
        try:
            result = subprocess.run(["which", "claude"], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def start(self):
        """ワーカー開始"""
        if not self.connect():
            return
            
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue='task_queue',
            on_message_callback=self.process_task
        )
        
        logger.info(f"{self.worker_id} 起動完了 - タスク待機中...")
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("シャットダウン中...")
            self.channel.stop_consuming()
            self.connection.close()

if __name__ == "__main__":
    worker_id = sys.argv[1] if len(sys.argv) > 1 else "worker-1"
    worker = TaskWorker(worker_id)
    worker.start()
