#!/usr/bin/env python3
import pika
import json
import argparse
from datetime import datetime

def send_task(prompt, task_type="general"):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        channel = connection.channel()
        channel.queue_declare(queue='task_queue', durable=True)
        
        task = {
            "task_id": f"{task_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "type": task_type,
            "prompt": prompt,
            "created_at": datetime.now().isoformat()
        }
        
        channel.basic_publish(
            exchange='',
            routing_key='task_queue',
            body=json.dumps(task),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        
        print(f"✅ タスク送信成功")
        print(f"   ID: {task['task_id']}")
        print(f"   プロンプト: {prompt[:50]}...")
        
        connection.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Task submission tool - Send tasks to the Elders Guild task queue",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Create Python fibonacci function" code
  %(prog)s "Analyze system performance" analysis
  %(prog)s "Write unit tests for auth module" test
  %(prog)s "Fix database connection issue" fix
        """
    )
    
    parser.add_argument(
        "prompt",
        help="Task description or prompt to send to the AI system"
    )
    
    parser.add_argument(
        "type",
        nargs="?",
        default="general",
        choices=["general", "code", "analysis", "test", "fix"],
        help="Task type (default: general). Available types: general, code, analysis, test, fix"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output with task details"
    )

    args = parser.parse_args()
    
    if args.verbose:
        print(f"📋 タスク詳細:")
        print(f"   タイプ: {args.type}")
        print(f"   プロンプト: {args.prompt}")
        print(f"   送信時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    send_task(args.prompt, args.type)

if __name__ == "__main__":
    main()
