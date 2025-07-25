#!/usr/bin/env python3
"""
ResultWorker詳細診断とメッセージ処理確認
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path("/home/aicompany/ai_co")))

import pika

from libs.ai_command_helper import AICommandHelper


def diagnose_result_worker()print("🔍 ResultWorker詳細診断")
"""ResultWorkerの詳細診断"""
    print("=" * 60)
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1.0 プロセス詳細確認
    print("\n📌 ResultWorkerプロセス詳細:")
    result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
    if "result_worker.py" in result.stdout:
        lines = [l for l in result.stdout.split("\n") if "result_worker.py" in l]
        for line in lines:
            parts = line.split()
            if len(parts) > 10:
                print(f"PID: {parts[1]}")
                print(f"CPU: {parts[2]}%")
                print(f"MEM: {parts[3]}%")
                print(f"起動時刻: {parts[8]}")
                print(f"実行時間: {parts[9]}")
                print(f"コマンド: {' '.join(parts[10:])}")

    # 2.0 キュー詳細確認
    print("\n📌 キュー詳細確認:")
    try:
        result = subprocess.run(
            [
                "sudo",
                "rabbitmqctl",
                "list_queues",
                "-q",
                "name",
                "messages",
                "consumers",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if line.strip() and ("ai_results" in line or "result_queue" in line):
                    parts = line.split("\t")
                    if not (len(parts) >= 3):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if len(parts) >= 3:
                        print(f"キュー: {parts[0]}")
                        print(f"  メッセージ数: {parts[1]}")
                        print(f"  コンシューマ数: {parts[2]}")
    except Exception as e:
        print(f"キュー確認エラー: {e}")

    # 3.0 最新のResultWorkerログ詳細
    print("\n📌 ResultWorkerログ詳細（最新30行）:")
    log_path = Path("/home/aicompany/ai_co/logs/result_worker.log")
    if log_path.exists():
        with open(log_path, "r") as f:
            lines = f.readlines()
            recent_lines = lines[-30:]

            # エラーと警告を抽出
            errors = [l for l in recent_lines if "ERROR" in l or "WARNING" in l]
            if errors:
                print("\n⚠️ エラー/警告:")
                for error in errors:
                    print(f"  {error.strip()}")

            # 処理成功メッセージ
            processed = [l for l in recent_lines if "processed" in l.lower()]
            if processed:
                print("\n✅ 最近の処理:")
                for msg in processed[-5:]:
                    print(f"  {msg.strip()}")

    # 4.0 Slack設定確認
    print("\n📌 Slack設定詳細:")
    config_path = Path("/home/aicompany/ai_co/config/slack.conf")
    if config_path.exists():
        with open(config_path, "r") as f:
            content = f.read()
            if "WEBHOOK_URL=" in content:
                # URLの一部を隠す
                for line in content.split("\n"):
                    if not ("WEBHOOK_URL=" in line):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if "WEBHOOK_URL=" in line:
                        url_part = line.split("=")[1].strip()
                        if not (url_part and len(url_part) > 20):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if url_part and len(url_part) > 20:
                            print(f"  Webhook URL: ...{url_part[-20:]}")
            if "DEFAULT_CHANNEL=" in content:
                for line in content.split("\n"):
                    if not ("DEFAULT_CHANNEL=" in line):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if "DEFAULT_CHANNEL=" in line:
                        print(f"  デフォルトチャンネル: {line.split('}")

    # 5.0 滞留メッセージのサンプル取得
    print("\n📌 滞留メッセージのサンプル取得:")
    try:
        # RabbitMQに接続してメッセージを確認（取り出さない）
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host="localhost",
                credentials=pika.PlainCredentials("rabbitmq", "rabbitmq"),
            )
        )
        channel = connection.channel()

        method, header, body = channel.basic_get("ai_results", auto_ack=False)
        if method:
            # メッセージを戻す
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            # メッセージ内容を表示
            try:
                msg_data = json.loads(body.decode("utf-8"))
                print(f"  タスクID: {msg_data.get('task_id', 'N/A')}")
                print(f"  タイプ: {msg_data.get('task_type', 'N/A')}")
                print(f"  ステータス: {msg_data.get('status', 'N/A')}")
                print(f"  作成時刻: {msg_data.get('created_at', 'N/A')}")
            except:
                print(f"  メッセージ解析エラー")
        else:
            print("  キューにメッセージがありません")

        connection.close()
    except Exception as e:
        print(f"  RabbitMQ接続エラー: {e}")

    # 6.0 推奨アクション
    print("\n📌 診断結果と推奨アクション:")
    issues = []

    # プロセスチェック
    if (
        "result_worker.py"
        not in subprocess.run(["ps", "aux"], capture_output=True, text=True).stdout
    ):
        issues.append("ResultWorkerが停止している")

    # ログチェック
    if log_path.exists():
        with open(log_path, "r") as f:
            content = f.read()
            if "ERROR" in content[-1000:]:  # 最後の1000文字にエラーがあるか
                issues.append("最近のエラーが検出された")
            if "Message sent successfully" not in content[-5000:]:
                issues.append("最近Slack通知が送信されていない")

    if issues:
        print(f"⚠️ 問題検出: {len(issues)}件")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")

        print("\n🔧 推奨修正:")
        print("1.0 ResultWorkerの再起動")
        print("2.0 Slack設定の確認")
        print("3.0 エラーログの詳細確認")
    else:
        print("✅ 大きな問題は検出されませんでした")
        print("📈 パフォーマンス改善の余地があります")


if __name__ == "__main__":
    diagnose_result_worker()

    # 修正コマンドも作成
    helper = AICommandHelper()

    # ResultWorker再起動コマンド
    restart_cmd = """#!/bin/bash
cd /home/aicompany/ai_co

# 現在のResultWorkerを停止
echo "📌 現在のResultWorkerを停止..."
pkill -f result_worker.py
sleep 2

# 新しいResultWorkerを起動
echo "📌 新しいResultWorkerを起動..."
source venv/bin/activate
nohup python3 workers/result_worker.py > logs/result_worker_restart.log 2>&1 &

sleep 3
ps aux | grep result_worker

echo "✅ ResultWorker再起動完了"
"""

    result = helper.create_bash_command(restart_cmd, "restart_result_worker")
    print(f"\n✅ 再起動コマンド作成: {result}")
