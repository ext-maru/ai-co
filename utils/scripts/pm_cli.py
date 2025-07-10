#!/usr/bin/env python3
import pika
import json
import argparse
import sys

def send_task(prompt, task_type="general"):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='task_queue', durable=True)

    task = {
        "task_id": "pm_cli_task",
        "type": task_type,
        "prompt": prompt
    }

    channel.basic_publish(exchange='', routing_key='task_queue',
                          body=json.dumps(task),
                          properties=pika.BasicProperties(delivery_mode=2))
    print("タスク送信完了:", task)

def main():
    parser = argparse.ArgumentParser(
        description="PM CLI - Project Manager Command Line Interface for task submission",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Interactive mode
  %(prog)s --task "Create new feature" --type code   # Single task submission
  %(prog)s --interactive             # Force interactive mode
        """
    )
    
    parser.add_argument(
        "--task", "-t",
        help="Task description to submit (skips interactive mode)"
    )
    
    parser.add_argument(
        "--type", "-T",
        default="general",
        choices=["general", "code", "analysis", "test", "fix"],
        help="Task type (default: general)"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Force interactive mode even when --task is provided"
    )

    args = parser.parse_args()

    if args.task and not args.interactive:
        # Single task mode
        send_task(args.task, args.type)
        return

    # Interactive mode
    print("PM CLI 簡易版 - タスク送信用")
    print("使用方法: タスク内容を入力してください（終了は 'exit'）")
    print("利用可能なタスクタイプ: general, code, analysis, test, fix")
    print()
    
    while True:
        prompt = input("タスク内容（終了はexit）> ")
        if prompt.lower() == "exit":
            break
        
        task_type = input(f"タスクタイプ（デフォルト: general）> ").strip()
        if not task_type:
            task_type = "general"
        
        send_task(prompt, task_type)

if __name__ == "__main__":
    main()
