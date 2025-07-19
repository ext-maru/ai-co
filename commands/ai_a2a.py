#!/usr/bin/env python3
"""
AI A2A Communication Command
A2A通信システムの管理・監視コマンド
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from commands.base_command import BaseCommand
from libs.a2a_communication import (
    AGENT_REGISTRY,
    MessagePriority,
    MessageType,
    create_a2a_client,
)
from libs.elder_servant_a2a_optimization import ElderServantOptimizer


class A2ACommand(BaseCommand):
    """A2A通信管理コマンド"""

    def __init__(self):
        super().__init__()
        self.command_name = "ai_a2a"
        self.description = "A2A (Agent to Agent) Communication Management"

    def add_arguments(self, parser):
        """引数追加"""
        subparsers = parser.add_subparsers(dest="action", help="A2A Actions")

        # test サブコマンド
        test_parser = subparsers.add_parser("test", help="Test A2A communication")
        test_parser.add_argument(
            "--source", default="knowledge_sage", help="Source agent ID"
        )
        test_parser.add_argument(
            "--target", default="task_sage", help="Target agent ID"
        )
        test_parser.add_argument(
            "--message", default="test query", help="Test message content"
        )

        # status サブコマンド
        status_parser = subparsers.add_parser("status", help="Show A2A system status")

        # demo サブコマンド
        demo_parser = subparsers.add_parser("demo", help="Run Four Sages demo")
        demo_parser.add_argument(
            "--scenario",
            choices=["collaboration", "optimization"],
            default="collaboration",
            help="Demo scenario",
        )

        # optimization サブコマンド
        opt_parser = subparsers.add_parser(
            "optimize", help="Elder-Servant optimization"
        )
        opt_parser.add_argument(
            "--enable", action="store_true", help="Enable optimization"
        )
        opt_parser.add_argument(
            "--disable", action="store_true", help="Disable optimization"
        )
        opt_parser.add_argument(
            "--metrics", action="store_true", help="Show optimization metrics"
        )

        # registry サブコマンド
        registry_parser = subparsers.add_parser("registry", help="Show agent registry")

        # monitor サブコマンド
        monitor_parser = subparsers.add_parser("monitor", help="Monitor A2A traffic")
        monitor_parser.add_argument(
            "--duration", type=int, default=30, help="Monitoring duration in seconds"
        )

    async def run_async(self, args):
        """非同期実行"""
        if args.action == "test":
            await self._test_communication(args)
        elif args.action == "status":
            await self._show_status(args)
        elif args.action == "demo":
            await self._run_demo(args)
        elif args.action == "optimize":
            await self._handle_optimization(args)
        elif args.action == "registry":
            await self._show_registry(args)
        elif args.action == "monitor":
            await self._monitor_traffic(args)
        else:
            self.print_error("No action specified. Use --help for usage.")

    async def _test_communication(self, args):
        """A2A通信テスト"""
        self.print_info(f"Testing A2A communication: {args.source} -> {args.target}")

        try:
            # ソースエージェント作成
            source_client = await create_a2a_client(args.source)

            # テストメッセージ送信
            start_time = datetime.now()

            response = await source_client.send_message(
                target_agent=args.target,
                message_type=MessageType.QUERY_REQUEST,
                method="test_communication",
                params={
                    "message": args.message,
                    "timestamp": start_time.isoformat(),
                    "test_mode": True,
                },
                wait_for_response=True,
                timeout=10.0,
            )

            end_time = datetime.now()
            latency = (end_time - start_time).total_seconds() * 1000

            if response:
                self.print_success(f"✅ Communication successful!")
                self.print_info(f"   Response time: {latency:.2f}ms")
                self.print_info(f"   Response data: {response.payload.data}")
            else:
                self.print_error("❌ No response received")

            # メトリクス表示
            metrics = await source_client.get_metrics()
            self.print_info(f"\\nClient metrics:")
            self.print_info(f"   Messages sent: {metrics['messages_sent']}")
            self.print_info(f"   Messages received: {metrics['messages_received']}")
            self.print_info(f"   Errors: {metrics['errors_count']}")

            await source_client.disconnect()

        except Exception as e:
            self.print_error(f"Communication test failed: {e}")

    async def _show_status(self, args):
        """A2Aシステムステータス表示"""
        self.print_info("A2A Communication System Status")
        self.print_info("=" * 40)

        try:
            # 各エージェントのステータス確認
            for agent_id in AGENT_REGISTRY.keys():
                try:
                    client = await create_a2a_client(agent_id)
                    metrics = await client.get_metrics()

                    self.print_success(f"✅ {agent_id}:")
                    self.print_info(
                        f"   Type: {AGENT_REGISTRY[agent_id].agent_type.value}"
                    )
                    self.print_info(
                        f"   Capabilities: {', '.join(AGENT_REGISTRY[agent_id].capabilities)}"
                    )
                    self.print_info(f"   Messages sent: {metrics['messages_sent']}")
                    self.print_info(
                        f"   Messages received: {metrics['messages_received']}"
                    )

                    await client.disconnect()

                except Exception as e:
                    self.print_error(f"❌ {agent_id}: Connection failed ({e})")

            # システム情報表示
            self.print_info(f"\\nSystem Information:")
            self.print_info(f"   Protocol version: 1.0")
            self.print_info(f"   Message types: {len(MessageType)}")
            self.print_info(f"   Priority levels: {len(MessagePriority)}")
            self.print_info(f"   Registered agents: {len(AGENT_REGISTRY)}")

        except Exception as e:
            self.print_error(f"Status check failed: {e}")

    async def _run_demo(self, args):
        """デモ実行"""
        if args.scenario == "collaboration":
            await self._run_collaboration_demo()
        elif args.scenario == "optimization":
            await self._run_optimization_demo()

    async def _run_collaboration_demo(self):
        """協調デモ実行"""
        self.print_info("Running Four Sages Collaboration Demo...")

        try:
            # デモモジュールのインポート
            from examples.four_sages_a2a_demo import FourSagesOrchestrator

            orchestrator = FourSagesOrchestrator()

            self.print_info("Initializing Four Sages...")
            await orchestrator.initialize_sages()

            self.print_info("Demonstrating collaboration scenarios...")
            await orchestrator.demonstrate_collaboration()

            self.print_info("Displaying metrics...")
            await orchestrator.display_metrics()

            await orchestrator.shutdown()

            self.print_success("✅ Collaboration demo completed successfully!")

        except Exception as e:
            self.print_error(f"Demo failed: {e}")

    async def _run_optimization_demo(self):
        """最適化デモ実行"""
        self.print_info("Running Elder-Servant Optimization Demo...")

        try:
            # Knowledge Sageクライアント作成
            elder_client = await create_a2a_client("knowledge_sage")

            # 最適化システム初期化
            optimizer = ElderServantOptimizer(elder_client)
            await optimizer.initialize()

            self.print_info("Testing optimization features...")

            # 高優先度タスク
            result1 = await optimizer.send_optimized_message(
                capability="task_execution",
                message_type=MessageType.TASK_ASSIGNMENT,
                method="execute_critical_task",
                params={"task_id": "demo_001"},
                priority=MessagePriority.CRITICAL,
            )

            self.print_info(f"Critical task result: {result1}")

            # バッチ処理テスト
            for i in range(3):
                await optimizer.send_optimized_message(
                    capability="data_processing",
                    message_type=MessageType.COMMAND,
                    method="process_demo_data",
                    params={"chunk_id": f"demo_chunk_{i}"},
                    priority=MessagePriority.LOW,
                    use_batching=True,
                )

            # メトリクス表示
            metrics = await optimizer.get_optimization_metrics()
            self.print_info("\\nOptimization Metrics:")
            for key, value in metrics.items():
                if key != "servant_metrics":
                    self.print_info(f"   {key}: {value}")

            await optimizer.shutdown()
            await elder_client.disconnect()

            self.print_success("✅ Optimization demo completed successfully!")

        except Exception as e:
            self.print_error(f"Optimization demo failed: {e}")

    async def _handle_optimization(self, args):
        """最適化管理"""
        if args.enable or args.disable or args.metrics:
            try:
                elder_client = await create_a2a_client("knowledge_sage")
                optimizer = ElderServantOptimizer(elder_client)
                await optimizer.initialize()

                if args.enable:
                    await optimizer.enable_optimization(True)
                    self.print_success("✅ Optimization enabled")

                elif args.disable:
                    await optimizer.enable_optimization(False)
                    self.print_success("✅ Optimization disabled")

                if args.metrics:
                    metrics = await optimizer.get_optimization_metrics()
                    self.print_info("\\nOptimization Metrics:")
                    self.print_info(json.dumps(metrics, indent=2))

                await optimizer.shutdown()
                await elder_client.disconnect()

            except Exception as e:
                self.print_error(f"Optimization management failed: {e}")
        else:
            self.print_error("Specify --enable, --disable, or --metrics")

    async def _show_registry(self, args):
        """エージェントレジストリ表示"""
        self.print_info("A2A Agent Registry")
        self.print_info("=" * 30)

        for agent_id, agent_info in AGENT_REGISTRY.items():
            self.print_info(f"\\n🤖 {agent_id}:")
            self.print_info(f"   Type: {agent_info.agent_type.value}")
            self.print_info(f"   Instance: {agent_info.instance_id}")
            self.print_info(f"   Priority: {agent_info.priority.name}")
            self.print_info(f"   Capabilities: {', '.join(agent_info.capabilities)}")
            self.print_info(f"   Endpoints: {', '.join(agent_info.endpoints)}")

    async def _monitor_traffic(self, args):
        """A2Aトラフィック監視"""
        self.print_info(f"Monitoring A2A traffic for {args.duration} seconds...")

        try:
            # 全エージェントのクライアント作成
            clients = {}
            initial_metrics = {}

            for agent_id in AGENT_REGISTRY.keys():
                try:
                    client = await create_a2a_client(agent_id)
                    clients[agent_id] = client
                    initial_metrics[agent_id] = await client.get_metrics()
                except Exception as e:
                    self.print_warning(f"Failed to connect to {agent_id}: {e}")

            # 監視期間待機
            await asyncio.sleep(args.duration)

            # 最終メトリクス取得
            self.print_info(f"\\nA2A Traffic Summary ({args.duration}s):")
            self.print_info("=" * 40)

            total_sent = 0
            total_received = 0
            total_errors = 0

            for agent_id, client in clients.items():
                try:
                    final_metrics = await client.get_metrics()
                    initial = initial_metrics[agent_id]

                    sent_delta = (
                        final_metrics["messages_sent"] - initial["messages_sent"]
                    )
                    received_delta = (
                        final_metrics["messages_received"]
                        - initial["messages_received"]
                    )
                    error_delta = (
                        final_metrics["errors_count"] - initial["errors_count"]
                    )

                    if sent_delta > 0 or received_delta > 0 or error_delta > 0:
                        self.print_info(f"\\n📊 {agent_id}:")
                        self.print_info(f"   Sent: {sent_delta}")
                        self.print_info(f"   Received: {received_delta}")
                        if error_delta > 0:
                            self.print_warning(f"   Errors: {error_delta}")

                    total_sent += sent_delta
                    total_received += received_delta
                    total_errors += error_delta

                    await client.disconnect()

                except Exception as e:
                    self.print_error(f"Error getting metrics for {agent_id}: {e}")

            self.print_info(f"\\n📈 Total Traffic:")
            self.print_info(f"   Messages sent: {total_sent}")
            self.print_info(f"   Messages received: {total_received}")
            self.print_info(f"   Total errors: {total_errors}")
            self.print_info(
                f"   Messages/sec: {(total_sent + total_received) / args.duration:.2f}"
            )

        except Exception as e:
            self.print_error(f"Traffic monitoring failed: {e}")


def main():
    """メイン関数"""
    command = A2ACommand()
    parser = argparse.ArgumentParser(
        description=command.description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test communication between agents
  python3 commands/ai_a2a.py test --source knowledge_sage --target task_sage

  # Show system status
  python3 commands/ai_a2a.py status

  # Run collaboration demo
  python3 commands/ai_a2a.py demo --scenario collaboration

  # Enable optimization
  python3 commands/ai_a2a.py optimize --enable

  # Show agent registry
  python3 commands/ai_a2a.py registry

  # Monitor traffic for 60 seconds
  python3 commands/ai_a2a.py monitor --duration 60
        """,
    )

    command.add_arguments(parser)
    args = parser.parse_args()

    if not hasattr(args, "action") or args.action is None:
        parser.print_help()
        return

    try:
        asyncio.run(command.run_async(args))
    except KeyboardInterrupt:
        print("\\n🛑 Operation cancelled by user")
    except Exception as e:
        print(f"❌ Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
