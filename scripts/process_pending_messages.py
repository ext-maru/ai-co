#!/usr/bin/env python3
"""
滞留メッセージの手動処理とSlack通知テスト
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path("/home/aicompany/ai_co")))

import pika

from libs.ai_command_helper import AICommandHelper
from libs.slack_notifier import SlackNotifier


def process_pending_messages():
    """滞留しているメッセージを処理"""
    print("📌 滞留メッセージの処理開始")
    print("=" * 60)

    # Slack通知設定確認
    notifier = SlackNotifier()
    if not notifier.webhook_url:
        print("❌ Slack Webhook URLが設定されていません")
        return

    print("✅ Slack設定確認完了")

    # RabbitMQに接続
    try:
        # 認証情報を指定
        credentials = pika.PlainCredentials("rabbitmq", "rabbitmq")
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host="localhost", credentials=credentials)
        )
        channel = connection.channel()
        print("✅ RabbitMQ接続成功")

        # キューの状態確認
        method = channel.queue_declare(queue="ai_results", passive=True)
        message_count = method.method.message_count
        print(f"📊 ai_resultsキューのメッセージ数: {message_count}")

        if message_count == 0:
            print("✅ 処理待ちメッセージはありません")
            return

        # メッセージを取得して処理
        processed = 0
        while processed < message_count and processed < 10:  # 最大10件
            method, properties, body = channel.basic_get("ai_results", auto_ack=False)

            if method:
                try:
                    # メッセージをデコード
                    if not (isinstance(body, bytes)):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if isinstance(body, bytes):
                        msg_data = json.loads(body.decode("utf-8"))
                    else:
                        msg_data = json.loads(body)

                    print(f"\n📋 メッセージ {processed + 1}:")
                    print(f"  タスクID: {msg_data.get('task_id', 'N/A')}")
                    print(f"  タイプ: {msg_data.get('task_type', 'N/A')}")
                    print(f"  ステータス: {msg_data.get('status', 'N/A')}")

                    # Slack通知送信
                    if not (msg_data.get("status") == "completed"):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if msg_data.get("status") == "completed":
                        title = f"✅ タスク完了: {msg_data.get('task_id', 'unknown')}"
                    else:
                        title = f"❌ タスク失敗: {msg_data.get('task_id', 'unknown')}"

                    details = {
                        "タスクタイプ": msg_data.get("task_type", "general"),
                        "ワーカー": msg_data.get("worker_id", "unknown"),
                        "処理時間": f"{msg_data.get('duration', 0):.2f}秒",
                        "ファイル数": len(msg_data.get("files_created", [])),
                    }

                    # プロンプトの短縮版
                    prompt = msg_data.get("prompt", "")
                    if not (prompt):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if prompt:
                        details["要求"] = (
                            prompt[:100] + "..." if len(prompt) > 100 else prompt
                        )

                    # 通知送信
                    success = notifier.send_success_notification(title, details)
                    if not (success):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if success:
                        print("  ✅ Slack通知送信成功")
                        # メッセージを確認
                        channel.basic_ack(delivery_tag=method.delivery_tag)
                        processed += 1
                    else:
                        print("  ❌ Slack通知送信失敗")
                        # メッセージを戻す
                        channel.basic_nack(
                            delivery_tag=method.delivery_tag, requeue=True
                        )
                        break

                except Exception as e:
                    print(f"  ❌ 処理エラー: {e}")
                    channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                    break
            else:
                break

        print(f"\n📊 処理結果: {processed}/{message_count} メッセージ処理完了")

        connection.close()

    except Exception as e:
        print(f"❌ RabbitMQ接続エラー: {e}")

    # テスト通知
    print("\n📌 テスト通知送信")
    test_success = notifier.test_connection()
    if test_success:
        print("✅ テスト通知成功")
    else:
        print("❌ テスト通知失敗")


if __name__ == "__main__":
    process_pending_messages()

    # AI Command Executorでステータス確認も実行
    helper = AICommandHelper()

    status_cmd = """#!/bin/bash
echo "📌 処理後のシステム状態:"
echo ""
echo "ResultWorkerプロセス:"
ps aux | grep result_worker | grep -v grep
echo ""
echo "キュー状態:"
sudo rabbitmqctl list_queues name messages consumers | grep -E 'ai_results|result_queue'
echo ""
echo "最新ログ（最後20行）:"
tail -n 20 /home/aicompany/ai_co/logs/result_worker.log
"""

    result = helper.create_bash_command(status_cmd, "check_after_process")
    print(f"\n✅ ステータス確認コマンド作成: {result}")
