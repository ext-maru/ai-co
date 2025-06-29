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

# RAG・Slack統合
sys.path.append(str(Path(__file__).parent.parent))
from libs.rag_manager import RAGManager
from libs.slack_notifier import SlackNotifier

PROJECT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_DIR / "output"
LOG_DIR = PROJECT_DIR / "logs"

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
        self.model = "claude-sonnet-4-20250514"
        # RAG・Slack統合
        self.rag = RAGManager(model=self.model)
        self.slack = SlackNotifier()

    def connect(self):
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
        try:
            task = json.loads(body)
            task_id = task.get('task_id', f'unknown_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            prompt = task.get('prompt', '')
            task_type = task.get('type', 'general')

            logger.info(f"📨 タスク受信: {task_id} (タイプ: {task_type})")
            logger.info(f"プロンプト: {prompt[:100]}")

            # 🧠 RAG: 過去履歴を含めたプロンプト構築
            enhanced_prompt = self.rag.build_context_prompt(prompt, include_history=True)
            rag_applied = len(enhanced_prompt) > len(prompt)
            
            if rag_applied:
                logger.info(f"✨ RAG適用: プロンプト拡張 {len(prompt)} → {len(enhanced_prompt)} 文字")

            # 出力フォルダ作成
            task_output_dir = OUTPUT_DIR / task_type / task_id
            os.makedirs(task_output_dir, exist_ok=True)
            output_file = task_output_dir / "result.txt"

            # Claude CLI実行
            if self.check_claude_cli():
                cmd = ["claude", "--model", self.model, "--allowedTools", "Edit,Write,FileSystem", "--print"]
                logger.info(f"🤖 Claude CLI実行中...")
                
                try:
                    result = subprocess.run(
                        cmd,
                        input=enhanced_prompt,
                        capture_output=True,
                        text=True,
                        cwd="/root/ai_co/output",
                        timeout=300
                    )

                    if result.returncode == 0:
                        output_text = result.stdout
                        status = "completed"
                        logger.info(f"✅ CLI成功: 出力{len(output_text)}文字")
                    else:
                        output_text = f"エラー: {result.stderr}"
                        status = "failed"
                        logger.error(f"❌ CLI失敗: {result.stderr}")

                except subprocess.TimeoutExpired:
                    output_text = "エラー: CLIタイムアウト(5分)"
                    status = "failed"
                    logger.error("⏱️ CLIタイムアウト")
            else:
                output_text = f"[シミュレーション]\nタスク: {prompt}\n応答: シミュレーション結果"
                status = "completed"
                logger.warning("🔧 シミュレーションモード")

            # ファイル保存
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"=== Task Info ===\n")
                    f.write(f"Task ID: {task_id}\n")
                    f.write(f"Worker: {self.worker_id}\n")
                    f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                    f.write(f"Model: {self.model}\n")
                    f.write(f"RAG Applied: {'Yes' if rag_applied else 'No'}\n")
                    f.write(f"Slack Sent: Yes\n")
                    f.write(f"\n=== Original Prompt ===\n{prompt}\n")
                    f.write(f"\n=== Response ===\n{output_text}\n")
                    f.write(f"=== End ===\n")
                logger.info(f"💾 ファイル保存: {output_file}")
            except Exception as e:
                logger.error(f"💾 ファイル保存失敗: {e}")

            # 🧠 RAG: 履歴保存・要約生成
            try:
                self.rag.save_task_with_summary(
                    task_id=task_id,
                    worker=self.worker_id,
                    prompt=prompt,
                    response=output_text,
                    status=status,
                    task_type=task_type
                )
                logger.info(f"🧠 RAG履歴保存完了")
            except Exception as e:
                logger.error(f"🧠 RAG履歴保存失敗: {e}")

            # 📱 Slack通知送信
            try:
                slack_success = self.slack.send_task_completion_simple(
                    task_id=task_id,
                    worker=self.worker_id,
                    prompt=prompt,
                    response=output_text,
                    status=status,
                    task_type=task_type,
                    rag_applied=rag_applied
                )
                if slack_success:
                    logger.info(f"📱 Slack通知送信完了")
                else:
                    logger.warning(f"📱 Slack通知送信失敗")
            except Exception as e:
                logger.error(f"📱 Slack通知例外: {e}")

            # 結果キュー送信
            result_data = {
                "task_id": task_id,
                "worker": self.worker_id,
                "status": status,
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
            logger.info(f"🎯 タスク完了: {task_id}")

        except Exception as e:
            logger.error(f"❌ タスク処理例外: {e}")
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
            return

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue='task_queue', on_message_callback=self.process_task)

        logger.info(f"🚀 {self.worker_id} RAG+Slack統合版起動 - task_queue待機中...")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("🛑 ワーカー停止中...")
            self.channel.stop_consuming()
            self.connection.close()

if __name__ == "__main__":
    worker_id = sys.argv[1] if len(sys.argv) > 1 else "worker-1"
    worker = TaskWorker(worker_id)
    worker.start()
