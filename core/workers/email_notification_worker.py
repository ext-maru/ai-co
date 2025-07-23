#!/usr/bin/env python3
import base64
import email
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import pika

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print(
        "Google APIs not installed. Install with: pip install google-api-python-client " \
            "google-auth-httplib2 google-auth-oauthlib"
    )
    sys.exit(1)

PROJECT_DIR = Path(__file__).parent.parent
LOG_DIR = PROJECT_DIR / "logs"
CREDENTIALS_DIR = PROJECT_DIR / "credentials"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [EmailWorker] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "email_worker.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("EmailWorker")


class EmailNotificationWorker:
    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

    def __init__(self, worker_id="email-worker-1"):
        """初期化メソッド"""
        self.worker_id = worker_id
        self.gmail_service = None
        self.credentials = None
        self.setup_gmail_service()

    def setup_gmail_service(self):
        """Gmail API認証とサービス初期化"""
        try:
            os.makedirs(CREDENTIALS_DIR, exist_ok=True)
            token_path = CREDENTIALS_DIR / "gmail_token.json"
            credentials_path = CREDENTIALS_DIR / "gmail_credentials.json"

            creds = None
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(
                    str(token_path), self.SCOPES
                )

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not credentials_path.exists():
                        logger.error(f"Gmail認証情報が見つかりません: {credentials_path}")
                        logger.error(
                            "Google Cloud ConsoleでOAuth2クライアントIDを作成し、credentials.jsonとして保存してください"
                        )
                        return False

                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(credentials_path), self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                with open(token_path, "w") as token:
                    token.write(creds.to_json())

            self.credentials = creds
            self.gmail_service = build("gmail", "v1", credentials=creds)
            logger.info("Gmail API認証成功")
            return True

        except Exception as e:
            logger.error(f"Gmail API初期化失敗: {e}")
            return False

    def connect(self):
        """RabbitMQ接続"""
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters("localhost")
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue="email_queue", durable=True)
            self.channel.queue_declare(queue="result_queue", durable=True)
            logger.info(f"{self.worker_id} - RabbitMQ接続成功")
            return True
        except Exception as e:
            logger.error(f"RabbitMQ接続失敗: {e}")
            return False

    def create_message(self, to, subject, body, attachments=None, cc=None, bcc=None):
        """メールメッセージ作成"""
        try:
            message = MIMEMultipart()
            message["to"] = to
            message["subject"] = subject

            if cc:
                message["cc"] = cc
            if bcc:
                message["bcc"] = bcc

            # HTML/テキスト本文
            if body.strip().startswith("<"):
                message.attach(MIMEText(body, "html"))
            else:
                message.attach(MIMEText(body, "plain"))

            # 添付ファイル処理
            if attachments:
                for attachment_path in attachments:
                    if os.path.exists(attachment_path):
                        with open(attachment_path, "rb") as attachment:
                            part = MIMEBase("application", "octet-stream")
                            part.set_payload(attachment.read())

                        encoders.encode_base64(part)
                        part.add_header(
                            "Content-Disposition",
                            f"attachment; filename= {os.path.basename(attachment_path)}",
                        )
                        message.attach(part)
                        logger.info(f"添付ファイル追加: {attachment_path}")
                    else:
                        logger.warning(f"添付ファイルが見つかりません: {attachment_path}")

            return {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}

        except Exception as e:
            logger.error(f"メッセージ作成失敗: {e}")
            return None

    def send_email(self, to, subject, body, attachments=None, cc=None, bcc=None):
        """Gmail経由でメール送信"""
        try:
            if not self.gmail_service:
                logger.error("Gmail service not initialized")
                return False

            message = self.create_message(to, subject, body, attachments, cc, bcc)
            if not message:
                return False

            result = (
                self.gmail_service.users()
                .messages()
                .send(userId="me", body=message)
                .execute()
            )

            message_id = result.get("id")
            logger.info(f"📧 メール送信成功: {message_id} → {to}")
            return True

        except HttpError as error:
            logger.error(f"Gmail API エラー: {error}")
            return False
        except Exception as e:
            logger.error(f"メール送信失敗: {e}")
            return False

    def process_email_task(self, ch, method, properties, body):
        """メール送信タスク処理"""
        try:
            task = json.loads(body)
            task_id = task.get(
                "task_id", f'email_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            )
            email_data = task.get("email_data", {})

            to = email_data.get("to", "")
            subject = email_data.get("subject", "AI生成通知")
            body = email_data.get("body", "")
            attachments = email_data.get("attachments", [])
            cc = email_data.get("cc", None)
            bcc = email_data.get("bcc", None)

            logger.info(f"📨 メールタスク受信: {task_id}")
            logger.info(f"宛先: {to}")
            logger.info(f"件名: {subject}")

            if not to or not body:
                logger.error("必須項目不足: to または body が空です")
                status = "failed"
                error_msg = "Missing required fields: to or body"
            else:
                # メール送信実行
                success = self.send_email(to, subject, body, attachments, cc, bcc)

                if success:
                    status = "completed"
                    error_msg = None
                    logger.info(f"✅ メール送信完了: {task_id}")
                else:
                    status = "failed"
                    error_msg = "Email sending failed"
                    logger.error(f"❌ メール送信失敗: {task_id}")

            # 結果キューに送信
            result_data = {
                "task_id": task_id,
                "worker": self.worker_id,
                "status": status,
                "email_to": to,
                "email_subject": subject,
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
            }

            self.channel.basic_publish(
                exchange="",
                routing_key="result_queue",
                body=json.dumps(result_data),
                properties=pika.BasicProperties(delivery_mode=2),
            )

            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"🎯 メールタスク完了: {task_id}")

        except Exception as e:
            logger.error(f"❌ メールタスク処理例外: {e}")
            traceback.print_exc()
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def send_task_notification(self, task_id, task_type, status, details=""):
        """タスク完了通知メール（便利関数）"""
        subject = f"🤖 AI タスク完了通知 - {task_id}"

        if status == "completed":
            emoji = "✅"
            status_text = "正常完了"
        else:
            emoji = "❌"
            status_text = "失敗"

        body = f"""
        <html>
        <body>
        <h2>{emoji} AI タスク処理完了</h2>
        <ul>
        <li><strong>タスクID:</strong> {task_id}</li>
        <li><strong>タイプ:</strong> {task_type}</li>
        <li><strong>ステータス:</strong> {status_text}</li>
        <li><strong>処理時刻:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
        </ul>

        {f'<h3>詳細:</h3><pre>{details}</pre>' if details else ''}

        <hr>
        <p><small>このメールはAI自動処理システムから送信されました。</small></p>
        </body>
        </html>
        """

        # デフォルト送信先（環境変数から取得）
        default_to = os.getenv("DEFAULT_NOTIFICATION_EMAIL", "admin@example.com")

        return self.send_email(default_to, subject, body)

    def start(self):
        """ワーカー開始"""
        if not self.gmail_service:
            logger.error("Gmail service not available. Cannot start worker.")
            return

        if not self.connect():
            return

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue="email_queue", on_message_callback=self.process_email_task
        )

        logger.info(f"🚀 {self.worker_id} 起動 - email_queue待機中...")
        logger.info("📧 Gmail連携メール通知システム ready")

        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("🛑 Email Worker停止中...")
            self.channel.stop_consuming()
            self.connection.close()


if __name__ == "__main__":
    worker_id = sys.argv[1] if len(sys.argv) > 1 else "email-worker-1"
    worker = EmailNotificationWorker(worker_id)
    worker.start()
