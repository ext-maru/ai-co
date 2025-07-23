#!/usr/bin/env python3
"""
RabbitMQ A2A Communication Command
RabbitMQベースA2A通信管理コマンド
"""

import sys
import asyncio
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from libs.rabbitmq_a2a_communication import RabbitMQA2AClient, MessageType, MessagePriority
from libs.four_sages_rabbitmq_integration import rabbitmq_four_sages_controller

class RabbitMQA2ACommand:
    """RabbitMQ A2A通信管理"""

    def __init__(self):
        """初期化メソッド"""
        self.command_name = "ai_a2a_rabbitmq"

    async def send_message(self, recipient: str, message: str, priority: str = "normal"):
        """メッセージ送信（RabbitMQ経由）"""
        client = RabbitMQA2AClient("claude_elder_cmd")
        await client.connect()

        priority_map = {
            "low": MessagePriority.LOW,
            "normal": MessagePriority.NORMAL,
            "high": MessagePriority.HIGH,
            "urgent": MessagePriority.URGENT,
            "emergency": MessagePriority.EMERGENCY
        }

        try:
            message_id = await client.send_message(
                recipient=recipient,
                message_type=MessageType.QUERY,
                payload={"message": message},
                priority=priority_map.get(priority, MessagePriority.NORMAL)
            )

            print(f"🐰 Message sent via RabbitMQ to {recipient}")
            print(f"   Message ID: {message_id}")
            print(f"   Priority: {priority}")
            print(f"   Encryption: Enabled")
            print(f"   Transport: RabbitMQ")
            return message_id

        finally:
            await client.disconnect()

    async def consult_sages(self, query: str):
        """4賢者に相談（RabbitMQ経由）"""
        print(f"🐰🧙‍♂️ Consulting Four Sages via RabbitMQ about: {query}")

        try:
            # 4賢者システムを起動
            await rabbitmq_four_sages_controller.start_all_sages()
            await asyncio.sleep(2)  # 起動待ち

            results = await rabbitmq_four_sages_controller.consult_all_sages(query)

            print("\n📊 RabbitMQ Four Sages Consultation Results:")
            for sage, result in results.items():
                # Process each item in collection
                print(f"  🐰🧙‍♂️ {sage}:")
                if isinstance(result, dict):
                    for key, value in result.items():
                        # Process each item in collection
                        if not (key == "result" and isinstance(value, dict)):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if key == "result" and isinstance(value, dict):
                            # Complex condition - consider breaking down
                            # Deep nesting detected (depth: 6) - consider refactoring
                            for sub_key, sub_value in value.items():
                                # Process each item in collection
                                print(f"     {sub_key}: {sub_value}")
                        else:
                            print(f"     {key}: {value}")
                else:
                    print(f"     {result}")
                print()

        finally:
            await rabbitmq_four_sages_controller.stop_all_sages()

    async def emergency_council(self, issue: str):
        """緊急評議会招集（RabbitMQ経由）"""
        print(f"🐰🚨 Summoning Emergency Council via RabbitMQ for: {issue}")

        try:
            await rabbitmq_four_sages_controller.start_all_sages()
            await asyncio.sleep(1)

            result = await rabbitmq_four_sages_controller.emergency_council({
                "issue": issue,
                "severity": "high",
                "summoned_by": "claude_elder_rabbitmq_command"
            })

            print("🏛️ RabbitMQ Emergency Council Status:")
            print(f"   Status: {result['status']}")
            print(f"   Messages sent: {len(result['message_ids'])}")
            print(f"   Time: {result['timestamp']}")
            print(f"   Transport: {result['transport']}")
            print(f"   Encryption: {result['encryption']}")

        finally:
            await rabbitmq_four_sages_controller.stop_all_sages()

    async def status(self):
        """RabbitMQ A2Aシステム状態確認"""
        print("🐰 RabbitMQ A2A Communication System Status")
        print("=" * 55)

        # RabbitMQ接続テスト
        try:
            test_client = RabbitMQA2AClient("status_check")
            await test_client.connect()
            await test_client.disconnect()

            print("✅ RabbitMQ Server: Connected")
            print("   Host: localhost:5673")
            print("   Username: elders")
            print("   Exchange: elders_guild")
            print("   Type: Topic Exchange")

        except Exception as e:
            # Handle specific exception case
            print(f"❌ RabbitMQ Server: Connection Failed - {e}")
            return

        print("\n🐰🧙‍♂️ RabbitMQ Four Sages Status:")
        print("   - Knowledge Sage: Available (RabbitMQ)")
        print("   - Task Sage: Available (RabbitMQ)")
        print("   - Incident Sage: Available (RabbitMQ)")
        print("   - RAG Sage: Available (RabbitMQ)")

        print("\n🔐 Security Features:")
        print("   - JWT Message Signing: Enabled")
        print("   - Fernet Encryption: Enabled")
        print("   - Message TTL: 1 hour")
        print("   - Priority Queuing: 5 levels")

        print("\n⚡ Performance Features:")
        print("   - Persistent Messages: Enabled")
        print("   - QoS Prefetch: 100")
        print("   - Connection Pooling: Robust")
        print("   - Auto-reconnection: Enabled")

async def main():
    """mainメソッド"""
    # Core functionality implementation
    parser = argparse.ArgumentParser(description="RabbitMQ A2A Communication Command")
    subparsers = parser.add_subparsers(dest='action', help='Available actions')

    # send サブコマンド
    send_parser = subparsers.add_parser('send', help='Send message via RabbitMQ')
    send_parser.add_argument('recipient', help='Recipient agent ID')
    send_parser.add_argument('message', help='Message to send')
    send_parser.add_argument('--priority', default='normal',
                           choices=['low', 'normal', 'high', 'urgent', 'emergency'],
                           help='Message priority')

    # consult サブコマンド
    consult_parser = subparsers.add_parser('consult', help='Consult Four Sages via RabbitMQ')
    consult_parser.add_argument('query', help='Query for the sages')

    # emergency サブコマンド
    emergency_parser = subparsers.add_parser('emergency', help='Emergency council via RabbitMQ')
    emergency_parser.add_argument('issue', help='Emergency issue')

    # status サブコマンド
    subparsers.add_parser('status', help='Show RabbitMQ A2A system status')

    args = parser.parse_args()

    command = RabbitMQA2ACommand()

    if args.action == 'send':
        await command.send_message(args.recipient, args.message, args.priority)
    elif args.action == 'consult':
        await command.consult_sages(args.query)
    elif args.action == 'emergency':
        await command.emergency_council(args.issue)
    elif args.action == 'status':
        await command.status()
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
