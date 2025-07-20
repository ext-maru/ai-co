#!/usr/bin/env python3
"""
Elder Flow v2.0 CLI - Mind Reading Protocol統合コマンドライン
maru様専用の思考理解・自動実行システム

🌌 nWo Command Line Interface
Usage: elder-flow-v2 "maru様の指示"
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path

# Elder Flow v2.0 Mind Reading統合
from elder_flow_mind_reading_v2 import ElderFlowMindReading


async def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="Elder Flow v2.0 - Mind Reading Protocol統合CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  elder-flow-v2 "OAuth2.0認証システムを実装して"
  elder-flow-v2 "今すぐバグを修正してください" --auto
  elder-flow-v2 "DBを最適化したい" --priority high
  elder-flow-v2 --stats
  elder-flow-v2 --demo
        """
    )

    parser.add_argument(
        "instruction",
        nargs="?",
        help="maru様からの指示テキスト"
    )

    parser.add_argument(
        "--auto",
        action="store_true",
        help="自動実行モードを有効にする"
    )

    parser.add_argument(
        "--priority",
        choices=["low", "medium", "high", "critical"],
        default="medium",
        help="優先度を指定"
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        help="統計情報を表示"
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="デモンストレーションを実行"
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="対話モードで起動"
    )

    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="出力形式"
    )

    args = parser.parse_args()

    # Elder Flow v2.0初期化
    elder_flow = ElderFlowMindReading()
    await elder_flow.initialize_mind_reading()

    if args.auto:
        elder_flow.set_auto_mode(True)

    # 統計情報表示
    if args.stats:
        stats = elder_flow.get_statistics()
        if args.output == "json":
            print(json.dumps(stats, indent=2, ensure_ascii=False))
        else:
            print("📊 Elder Flow v2.0 Statistics:")
            print(f"   Total Executions: {stats['total_executions']}")
            print(f"   Success Rate: {stats['successful_executions'] / max(stats['total_executions'], 1) * 100:.1f}%")
            print(f"   Mind Reading Accuracy: {stats['mind_reading_accuracy']:.2%}")
            print(f"   Auto Execution Rate: {stats['auto_execution_rate']:.2%}")
            print(f"   Mind Reading Available: {stats['mind_reading_available']}")
        return

    # デモ実行
    if args.demo:
        await run_demo(elder_flow, args.output)
        return

    # 対話モード
    if args.interactive:
        await run_interactive_mode(elder_flow)
        return

    # 指示処理
    if args.instruction:
        result = await elder_flow.process_maru_input(args.instruction)

        if args.output == "json":
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print_result(result)
    else:
        parser.print_help()


async def run_demo(elder_flow: ElderFlowMindReading, output_format: str):
    """デモ実行"""
    demo_scenarios = [
        "Elder FlowでOAuth2.0認証を実装",
        "重要なバグを今すぐ修正して",
        "素晴らしい実装です！",
        "パフォーマンスを最適化したい",
        "セキュリティ監査を実行"
    ]

    if output_format == "json":
        results = []
        for scenario in demo_scenarios:
            result = await elder_flow.process_maru_input(scenario)
            results.append(result)
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print("🎯 Elder Flow v2.0 Demo")
        print("=" * 50)

        for i, scenario in enumerate(demo_scenarios, 1):
            print(f"\n[{i}] \"{scenario}\"")
            result = await elder_flow.process_maru_input(scenario)
            print_result(result, compact=True)

        # 統計表示
        stats = elder_flow.get_statistics()
        print(f"\n📊 Demo Results: {stats['successful_executions']}/{stats['total_executions']} successful")


async def run_interactive_mode(elder_flow: ElderFlowMindReading):
    """対話モード"""
    print("🌊 Elder Flow v2.0 Interactive Mode")
    print("💭 Type your instructions for maru様")
    print("Type 'quit', 'exit', or 'q' to exit")
    print("Type 'stats' to see statistics")
    print("Type 'auto' to toggle auto-execution mode")
    print("-" * 50)

    while True:
        try:
            instruction = input("\nmaru様> ").strip()

            if instruction.lower() in ["quit", "exit", "q"]:
                break
            elif instruction.lower() == "stats":
                stats = elder_flow.get_statistics()
                print(f"📊 Executions: {stats['total_executions']}, "
                      f"Success: {stats['successful_executions'] / max(stats['total_executions'], 1) * 100:.1f}%, "
                      f"Auto Mode: {stats['auto_mode']}")
                continue
            elif instruction.lower() == "auto":
                elder_flow.set_auto_mode(not elder_flow.auto_mode)
                print(f"🤖 Auto mode: {'ON' if elder_flow.auto_mode else 'OFF'}")
                continue
            elif not instruction:
                continue

            # 指示処理
            result = await elder_flow.process_maru_input(instruction)
            print_result(result, compact=True)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n👋 Elder Flow v2.0 session ended")


def print_result(result: dict, compact: bool = False):
    """結果を表示"""
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return

    if compact:
        status = "✅" if result.get("executed") else "📋"
        print(f"   {status} {result['intent']} ({result['confidence']:.0%}) → {result['command'][:40]}...")
    else:
        print(f"🧠 Intent: {result['intent']}")
        print(f"📊 Confidence: {result['confidence']:.1%}")
        print(f"💻 Command: {result['command']}")
        print(f"⚡ Auto-executed: {'Yes' if result['executed'] else 'No'}")

        if result['executed'] and 'result' in result:
            exec_result = result['result']
            if exec_result.get('status') == 'success':
                print(f"✅ Status: Success")
                if 'result' in exec_result:
                    print(f"📝 Output: {str(exec_result['result'])[:100]}...")
            else:
                print(f"❌ Status: {exec_result.get('status', 'Unknown')}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
