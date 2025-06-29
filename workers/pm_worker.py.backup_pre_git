#!/usr/bin/env python3
import pika
import json
import logging
import subprocess
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
        self.model = "claude-sonnet-4-20250514"

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue='pm_task_queue', durable=True)
            self.channel.queue_declare(queue='task_queue', durable=True)
            logger.info("RabbitMQ接続成功")
            return True
        except Exception as e:
            logger.error(f"RabbitMQ接続失敗: {e}")
            return False

    def process_pm_task(self, ch, method, properties, body):
        try:
            task = json.loads(body)
            task_id = task.get("task_id", f"pm_unknown_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            command = task.get("command", "")
            params = task.get("params", {})

            logger.info(f"PMタスク受信: {task_id} コマンド: {command}")

            if command == "run_code":
                prompt = params.get("prompt", "")
                result = self.run_claude_cli(prompt)
                self.send_worker_task(task_id, prompt, result)
            elif command == "generate_task":
                subtasks = self.generate_subtasks(params)
                for st in subtasks:
                    self.send_worker_task(st["task_id"], st["prompt"], "")
            else:
                logger.warning(f"未知のコマンド: {command}")

            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"PMタスク処理例外: {e}")
            traceback.print_exc()
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def run_claude_cli(self, prompt):
        cmd = ["claude", "--model", self.model, "--allowedTools", "Edit,Write,FileSystem", "--print"]
        try:
            proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=300)
            if proc.returncode != 0:
                logger.error(f"Claude CLI実行失敗: {proc.stderr}")
                return ""
            logger.info(f"Claude CLI実行成功、出力長: {len(proc.stdout)}")
            return proc.stdout
        except Exception as e:
            logger.error(f"Claude CLI例外: {e}")
            return ""

    def send_worker_task(self, task_id, prompt, previous_result):
        task = {
            "task_id": task_id,
            "prompt": prompt,
            "previous_result": previous_result,
            "type": "code",
            "created_at": datetime.now().isoformat()
        }
        try:
            self.channel.basic_publish(
                exchange='',
                routing_key='task_queue',
                body=json.dumps(task),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            logger.info(f"ワーカーへタスク送信: {task_id}")
        except Exception as e:
            logger.error(f"ワーカータスク送信失敗: {e}")

    def generate_subtasks(self, params):
        # 実装例。実際はAIやロジックで生成
        return [{
            "task_id": f"subtask_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "prompt": params.get("description", "新規タスク"),
        }]

    def start(self):
        if not self.connect():
            return
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue='pm_task_queue', on_message_callback=self.process_pm_task)
        logger.info("PM Worker 起動 - pm_task_queue待機中...")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("シャットダウン中...")
            self.channel.stop_consuming()
            self.connection.close()

if __name__ == "__main__":
    worker = PMWorker()
    worker.start()
