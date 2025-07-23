#!/usr/bin/env python3
"""
AI Daily Evolution Command - AI日次進化コマンド
自己進化システムを実行し、最新技術トレンドを調査・企画・実装する

使用方法:
  ai-evolve-daily                    # 日次進化サイクル実行
  ai-evolve-daily --status           # システム状況確認
  ai-evolve-daily --pending          # 保留中の相談確認
  ai-evolve-daily --history          # 進化履歴表示
  ai-evolve-daily --force-cycle      # 強制的に進化サイクル実行
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.self_evolution_system import SelfEvolutionSystem
from libs.slack_notifier import SlackNotifier


class AIEvolveDailyCommand:
    """AI日次進化コマンド"""

    def __init__(self):
        """初期化メソッド"""
        self.evolution_system = SelfEvolutionSystem()
        self.notifier = SlackNotifier()

    async def execute(self, args):
        """メイン実行"""
        try:
            if args.status:
                await self.show_system_status()
            elif args.pending:
                await self.show_pending_consultations()
            elif args.history:
                await self.show_evolution_history(args.limit)
            elif args.force_cycle:
                await self.force_evolution_cycle()
            else:
                await self.run_daily_cycle()

        except Exception as e:
            # Handle specific exception case
            print(f"❌ エラー: {e}")
            await self.notifier.send_message(f"❌ AI進化システムエラー: {e}")
            raise

    async def run_daily_cycle(self):
        """日次進化サイクル実行"""
        print("🌟 Elders Guild 自己進化システム - 日次サイクル開始")

        # 既に今日実行済みかチェック
        status = self.evolution_system.get_system_status()
        if status.get("last_cycle_date"):
            last_cycle = datetime.fromisoformat(
                status["last_cycle_date"].replace("Z", "+00:00")
            )
            today = datetime.now().date()

            if last_cycle.date() == today:
                print(f"✅ 本日の進化サイクルは既に実行済みです ({last_cycle.strftime('%H:%M')})")
                return

        # 進化サイクル実行
        await self.evolution_system.start_daily_evolution_cycle()

        print("✅ 日次進化サイクル完了")
        print("👑 グランドエルダーの決定をお待ちください")

    async def force_evolution_cycle(self):
        """強制進化サイクル実行"""
        print("🚀 強制進化サイクル実行")

        await self.evolution_system.start_daily_evolution_cycle()

        print("✅ 強制進化サイクル完了")

    async def show_system_status(self):
        """システム状況表示"""
        print("📊 自己進化システム状況")
        print("=" * 50)

        status = self.evolution_system.get_system_status()

        # 基本統計
        stats = status["statistics"]
        print(f"🔍 総発見トレンド: {stats['trends_discovered']}件")
        print(f"💡 総作成企画: {stats['proposals_created']}件")
        print(f"✅ 総承認企画: {stats['proposals_approved']}件")
        print(f"🚀 総実装完了: {stats['implementations_completed']}件")
        print()

        # システム状態
        print("🔧 コンポーネント状況:")
        for component, state in status["components_status"].items():
            status_icon = "✅" if state == "active" else "❌"
            print(f"  {status_icon} {component}: {state}")
        print()

        # 保留中の相談
        if status["pending_consultations"] > 0:
            print(f"👑 グランドエルダー相談待ち: {status['pending_consultations']}件")
        else:
            print("📭 現在、保留中の相談はありません")

        # 最終実行日
        if status["last_cycle_date"]:
            last_cycle = datetime.fromisoformat(
                status["last_cycle_date"].replace("Z", "+00:00")
            )
            print(f"📅 最終実行: {last_cycle.strftime('%Y年%m月%d日 %H:%M')}")
        else:
            print("📅 まだ実行されていません")

    async def show_pending_consultations(self):
        """保留中の相談表示"""
        print("👑 グランドエルダー相談待ち企画")
        print("=" * 50)

        if not self.evolution_system.pending_consultations:
            print("📭 現在、保留中の相談はありません")
            return

        # 繰り返し処理
        for i, consultation in enumerate(
            self.evolution_system.pending_consultations, 1
        ):
            print(f"\n📋 相談 #{i}")
            print(f"📊 企画数: {consultation['proposals_summary']['total_proposals']}件")

            # 高優先度企画
            if consultation["proposals_summary"]["high_priority"]:
                print("🎯 高優先度企画:")
                for title in consultation["proposals_summary"]["high_priority"]:
                    # Process each item in collection
                    print(f"  - {title}")

            # クイックウィン企画
            if consultation["proposals_summary"]["quick_wins"]:
                print("⚡ クイックウィン企画:")
                for title in consultation["proposals_summary"]["quick_wins"]:
                    # Process each item in collection
                    print(f"  - {title}")

            # リソース集約型企画
            if consultation["proposals_summary"]["resource_intensive"]:
                print("🔧 リソース集約型企画:")
                for title in consultation["proposals_summary"]["resource_intensive"]:
                    # Process each item in collection
                    print(f"  - {title}")

        print("\n💡 グランドエルダーに未来ビジョンをお聞きして、企画の優先順位を決定してください")

    async def show_evolution_history(self, limit=10):
        """進化履歴表示"""
        print(f"📜 進化履歴 (最新{limit}件)")
        print("=" * 50)

        history = self.evolution_system.evolution_history[-limit:]

        if not history:
            print("📭 履歴がありません")
            return

        for entry in reversed(history):  # 新しい順に表示
            date = datetime.fromisoformat(entry["date"].replace("Z", "+00:00"))
            print(f"\n📅 {date.strftime('%Y年%m月%d日 %H:%M')}")

            if "trends_count" in entry:
                print(f"  🔍 発見トレンド: {entry['trends_count']}件")
                print(f"  💡 作成企画: {entry['proposals_count']}件")
                print(f"  ✅ 評議会承認: {entry['council_approved']}件")
                print(f"  📊 状況: {entry['status']}")

            if "approved_count" in entry:
                print(f"  🚀 実装承認: {entry['approved_count']}件")
                print(f"  📊 実装状況: {entry['implementation_status']}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Elders Guild 自己進化システム")

    parser.add_argument("--status", action="store_true", help="システム状況を表示")
    parser.add_argument("--pending", action="store_true", help="保留中の相談を表示")
    parser.add_argument("--history", action="store_true", help="進化履歴を表示")
    parser.add_argument("--limit", type=int, default=10, help="履歴表示件数 (default: 10)")
    parser.add_argument("--force-cycle", action="store_true", help="強制的に進化サイクルを実行")
    parser.add_argument("--verbose", action="store_true", help="詳細出力")

    args = parser.parse_args()

    # 実行
    command = AIEvolveDailyCommand()
    asyncio.run(command.execute(args))


if __name__ == "__main__":
    main()
