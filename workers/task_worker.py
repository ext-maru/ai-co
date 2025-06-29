#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import pika
import traceback
from datetime import datetime
from pathlib import Path
import logging

# プロジェクトルートディレクトリ（適宜変更）
PROJECT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_DIR / "output"
LOG_DIR = PROJECT_DIR / "logs"

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [TaskWorker] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "task_worker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TaskWorker")

class TaskWorker:
    def __init__(self, worker_id="worker-1"):
        self.worker_id = worker_id
        self.model = "claude-sonnet-4-20250514"  # 最新の正しいモデル名

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters('localhost')
            )
            self.channel = self.connection.channel()
            # task_queueのみ監視。pm_task_queueはPMワーカー専用
            self.channel.queue_declare(queue='task_queue', durable=True)
            self.channel.queue_declare(queue='result_queue', durable=True)
            logger.info(f"{self.worker_id} - RabbitMQ接続成功")
            return True
        except Exception as e:
            logger.error(f"RabbitMQ接続失敗: {e}")
            return False

    def process_task(self, ch, method, properties, body):
        try:
            task = json.loads(body)
            task_id = task.get('task_id', f'unknown_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            prompt = task.get('prompt', '')
            task_type = task.get('type', 'general')

            logger.info(f"タスク受信: {task_id} (タイプ: {task_type})")
            logger.info(f"プロンプト(先頭100文字): {prompt[:100]}")

            # 保存フォルダ作成
            task_output_dir = OUTPUT_DIR / task_type / task_id
            os.makedirs(task_output_dir, exist_ok=True)

            output_file = task_output_dir / "result.txt"
            logger.info(f"結果ファイル保存先: {output_file}")

            # Claude CLI 呼び出し
            if self.check_claude_cli():
                cmd = ["claude", "--model", self.model, "--allowedTools", "Edit,Write,FileSystem", "--print"]
                logger.info(f"CLIコマンド実行: {' '.join(cmd)}")
                try:
                    result = subprocess.run(
                        cmd,
                        input=prompt,
                        capture_output=True,
                        text=True,
                        cwd="/root/ai_co/output",
                        timeout=300
                    )
                    logger.info(f"CLI実行終了 リターンコード: {result.returncode}")

                    if result.returncode == 0:
                        output_text = result.stdout
                        logger.info(f"出力文字数: {len(output_text)}")
                    else:
                        output_text = f"エラー: {result.stderr}"
                        logger.error(f"CLIエラー: {result.stderr}")

                except subprocess.TimeoutExpired:
                    output_text = "エラー: CLIタイムアウト(5分)"
                    logger.error("CLIタイムアウト発生")
            else:
                logger.warning("Claude CLI未検出。シミュレーションモードで応答生成。")
                output_text = f"[シミュレーション応答]\nタスクID: {task_id}\nプロンプト: {prompt}\n"

            # ファイルに結果保存
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"=== Task Info ===\n")
                    f.write(f"Task ID: {task_id}\n")
                    f.write(f"Worker: {self.worker_id}\n")
                    f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                    f.write(f"Model: {self.model}\n")
                    f.write(f"\n=== Prompt ===\n{prompt}\n")
                    f.write(f"\n=== Response ===\n{output_text}\n")
                    f.write(f"=== End ===\n")
                logger.info(f"結果ファイル保存成功: {output_file} (サイズ: {output_file.stat().st_size} bytes)")
            except Exception as e:
                logger.error(f"結果ファイル保存失敗: {e}")
                traceback.print_exc()

            # 結果キューへ送信
            result_data = {
                "task_id": task_id,
                "worker": self.worker_id,
                "status": "completed" if 'エラー' not in output_text else "failed",
                "output_file": str(output_file),
                "timestamp": datetime.now().isoformat()
            }

            try:
                self.channel.basic_publish(
                    exchange='',
                    routing_key='result_queue',
                    body=json.dumps(result_data),
                    properties=pika.BasicProperties(delivery_mode=2)
                )
                logger.info(f"結果をresult_queueに送信: {task_id}")
            except Exception as e:
                logger.error(f"結果キュー送信失敗: {e}")

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logger.error(f"タスク処理例外: {e}")
            traceback.print_exc()
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def check_claude_cli(self):
        try:
            result = subprocess.run(["which", "claude"], capture_output=True)
            return result.returncode == 0
        except:
            return False

    def start(self):
        if not self.connect():
            logger.error("RabbitMQ接続失敗によりワーカーを起動できません。")
            return

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue='task_queue', on_message_callback=self.process_task)

        logger.info(f"{self.worker_id} 起動完了 - task_queue待機中...")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("ワーカー停止中...")
            self.channel.stop_consuming()
            self.connection.close()


if __name__ == "__main__":
    worker_id = sys.argv[1] if len(sys.argv) > 1 else "worker-1"
    worker = TaskWorker(worker_id)
    worker.start()

