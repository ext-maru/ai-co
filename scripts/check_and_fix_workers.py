#!/usr/bin/env python3
"""
Emergency Worker Check and Fix Script
緊急ワーカーチェック＆修復スクリプト
"""

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil

PROJECT_ROOT = Path(__file__).parent


def check_process_exists(process_name):
    """プロセスが存在するかチェック"""
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if process_name in " ".join(proc.info["cmdline"] or []):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False


def check_rabbitmq():
    """RabbitMQの状態チェック"""
    try:
        import pika

        connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
        channel = connection.channel()

        queues = ["ai_tasks", "ai_pm", "ai_results", "dialog_task_queue"]
        queue_status = {}

        for queue in queues:
            try:
                method = channel.queue_declare(queue=queue, passive=True)
                queue_status[queue] = method.method.message_count
            except:
                queue_status[queue] = -1

        connection.close()
        return True, queue_status
    except Exception as e:
        return False, str(e)


def start_worker(worker_path, log_name):
    """ワーカーを起動"""
    log_path = (
        PROJECT_ROOT
        / "logs"
        / f'{log_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    )
    cmd = f"nohup python3 {worker_path} > {log_path} 2>&1 &"
    subprocess.run(cmd, shell=True)
    print(f"  ✅ {worker_path} を起動しました")
    time.sleep(2)


def main():
    print("=" * 60)
    print("🏥 Elders Guild 緊急ワーカー診断＆修復")
    print(f"実行時刻: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
    print("=" * 60)

    # RabbitMQチェック
    print("\n1️⃣ RabbitMQチェック...")
    rabbitmq_ok, rabbitmq_info = check_rabbitmq()
    if rabbitmq_ok:
        print("  ✅ RabbitMQ正常")
        for queue, count in rabbitmq_info.items():
            print(f"    - {queue}: {count} messages")
    else:
        print(f"  ❌ RabbitMQエラー: {rabbitmq_info}")
        return

    # 必須ワーカーチェック
    print("\n2️⃣ 必須ワーカーチェック...")
    essential_workers = [
        ("enhanced_task_worker.py", "workers/enhanced_task_worker.py"),
        ("intelligent_pm_worker_simple.py", "workers/intelligent_pm_worker_simple.py"),
        ("async_result_worker_simple.py", "workers/async_result_worker_simple.py"),
    ]

    missing_workers = []
    for worker_name, worker_path in essential_workers:
        if check_process_exists(worker_name):
            print(f"  ✅ {worker_name} 実行中")
        else:
            print(f"  ❌ {worker_name} 停止中")
            missing_workers.append((worker_name, worker_path))

    # 不足ワーカーの起動
    if missing_workers:
        print(f"\n3️⃣ {len(missing_workers)}個のワーカーを起動します...")
        for worker_name, worker_path in missing_workers:
            full_path = PROJECT_ROOT / worker_path
            if full_path.exists():
                start_worker(full_path, worker_name.replace(".py", ""))
            else:
                print(f"  ⚠️ {worker_path} が見つかりません")

    # 最終チェック
    print("\n4️⃣ 最終チェック...")
    time.sleep(3)

    all_running = True
    for worker_name, _ in essential_workers:
        if not check_process_exists(worker_name):
            all_running = False
            break

    if all_running:
        print("  ✅ すべてのワーカーが正常に動作しています")

        # エルダー監視も起動
        print("\n5️⃣ エルダー監視システム起動...")
        if not check_process_exists("start_elder_monitoring.py"):
            elder_script = PROJECT_ROOT / "start_elder_monitoring.py"
            if elder_script.exists():
                start_worker(elder_script, "elder_monitoring")
            else:
                print("  ⚠️ エルダー監視スクリプトが見つかりません")
        else:
            print("  ✅ エルダー監視は既に実行中")

    else:
        print("  ❌ 一部のワーカーが起動できませんでした")

    print("\n" + "=" * 60)
    print("診断＆修復完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
