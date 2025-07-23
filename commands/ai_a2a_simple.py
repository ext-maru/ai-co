#!/usr/bin/env python3
"""
Simple A2A Communication Command
実用的なA2A通信管理コマンド
"""

import sys
import asyncio
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from libs.simple_a2a_communication import SimpleA2AClient, MessageType, MessagePriority
from libs.four_sages_simple_integration import four_sages_controller

class SimpleA2ACommand:
    """シンプルA2A通信管理"""

    def __init__(self):
        """初期化メソッド"""
        self.command_name = "ai_a2a_simple"

    async def send_message(self, recipient: str, message: str, priority: str = "normal"):
        """メッセージ送信"""
        client = SimpleA2AClient("claude_elder")

        priority_map = {
            "low": MessagePriority.LOW,
            "normal": MessagePriority.NORMAL,
            "high": MessagePriority.HIGH,
            "urgent": MessagePriority.URGENT,
            "emergency": MessagePriority.EMERGENCY
        }

        message_id = await client.send_message(
            recipient=recipient,
            message_type=MessageType.QUERY,
            payload={"message": message},
            priority=priority_map.get(priority, MessagePriority.NORMAL)
        )

        print(f"✅ Message sent to {recipient}")
        print(f"   Message ID: {message_id}")
        print(f"   Priority: {priority}")
        return message_id

    async def check_messages(self, agent_id: str):
        """メッセージ確認"""
        client = SimpleA2AClient(agent_id)
        messages = client.get_messages()

        if not messages:
            print(f"📭 No messages for {agent_id}")
            return

        print(f"📬 {len(messages)} messages for {agent_id}:")
        for message in messages:
            # Process each item in collection
            print(f"  📩 From: {message.sender}")
            print(f"     Type: {message.message_type.value}")
            print(f"     Priority: {message.priority.value}")
            print(f"     Time: {message.timestamp}")
            print(f"     Payload: {message.payload}")
            print()

    async def consult_sages(self, query: str):
        """4賢者に相談"""
        print(f"🧙‍♂️ Consulting Four Sages about: {query}")

        # 4賢者システムを起動
        four_sages_controller.start_all_sages()
        await asyncio.sleep(1)  # 起動待ち

        try:
            results = await four_sages_controller.consult_all_sages(query)

            print("\n📊 Consultation Results:")
            for sage, result in results.items():
                # Process each item in collection
                print(f"  🧙‍♂️ {sage}:")
                if isinstance(result, dict):
                    for key, value in result.items():
                        # Process each item in collection
                        print(f"     {key}: {value}")
                else:
                    print(f"     {result}")
                print()

        finally:
            four_sages_controller.stop_all_sages()

    async def emergency_council(self, issue: str):
        """緊急評議会招集"""
        print(f"🚨 Summoning Emergency Council for: {issue}")

        four_sages_controller.start_all_sages()
        await asyncio.sleep(0.5)

        try:
            result = await four_sages_controller.emergency_council({
                "issue": issue,
                "severity": "high",
                "summoned_by": "claude_elder_command"
            })

            print("🏛️ Emergency Council Status:")
            print(f"   Status: {result['status']}")
            print(f"   Messages sent: {len(result['message_ids'])}")
            print(f"   Time: {result['timestamp']}")

        finally:
            four_sages_controller.stop_all_sages()

    async def status(self):
        """A2Aシステム状態確認"""
        print("🔍 A2A Communication System Status")
        print("=" * 50)

        # データディレクトリ確認
        from libs.simple_a2a_communication import A2A_STORAGE_DIR

        if A2A_STORAGE_DIR.exists():
            print(f"✅ Storage Directory: {A2A_STORAGE_DIR}")

            # 各エージェントのメッセージ数確認
            inbox_dir = A2A_STORAGE_DIR / "inbox"
            if inbox_dir.exists():
                for agent_dir in inbox_dir.iterdir():
                    # Process each item in collection
                    if agent_dir.is_dir():
                        message_count = len(list(agent_dir.glob("*.json")))
                        print(f"   📬 {agent_dir.name}: {message_count} messages")
        else:
            print("❌ Storage Directory not found")

        print("\n🧙‍♂️ Four Sages Status:")
        print("   - Knowledge Sage: Available")
        print("   - Task Sage: Available")
        print("   - Incident Sage: Available")
        print("   - RAG Sage: Available")

async def main():
    """mainメソッド"""
    # Core functionality implementation
    parser = argparse.ArgumentParser(description="Simple A2A Communication Command")
    subparsers = parser.add_subparsers(dest='action', help='Available actions')

    # send サブコマンド
    send_parser = subparsers.add_parser('send', help='Send message')
    send_parser.add_argument('recipient', help='Recipient agent ID')
    send_parser.add_argument('message', help='Message to send')
    send_parser.add_argument('--priority', default='normal',
                           choices=['low', 'normal', 'high', 'urgent', 'emergency'],
                           help='Message priority')

    # check サブコマンド
    check_parser = subparsers.add_parser('check', help='Check messages')
    check_parser.add_argument('agent_id', help='Agent ID to check')

    # consult サブコマンド
    consult_parser = subparsers.add_parser('consult', help='Consult Four Sages')
    consult_parser.add_argument('query', help='Query for the sages')

    # emergency サブコマンド
    emergency_parser = subparsers.add_parser('emergency', help='Emergency council')
    emergency_parser.add_argument('issue', help='Emergency issue')

    # status サブコマンド
    subparsers.add_parser('status', help='Show A2A system status')

    args = parser.parse_args()

    command = SimpleA2ACommand()

    if args.action == 'send':
        await command.send_message(args.recipient, args.message, args.priority)
    elif args.action == 'check':
        await command.check_messages(args.agent_id)
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
