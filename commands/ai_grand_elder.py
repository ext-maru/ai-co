#!/usr/bin/env python3
"""
AI Grand Elder Interface - グランドエルダー交流コマンド
グランドエルダーとの対話を通じて、Elders Guildの戦略的意思決定を支援

使用方法:
  ai-grand-elder                     # グランドエルダーとの対話開始
  ai-grand-elder --future-vision     # 未来ビジョン要請
  ai-grand-elder --review-proposals  # 企画審査要請
  ai-grand-elder --decisions "..."   # 決定事項の入力
  ai-grand-elder --consultation-log  # 相談履歴表示
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

from libs.self_evolution_system import GrandElderInterface, SelfEvolutionSystem
from libs.slack_notifier import SlackNotifier


class AIGrandElderCommand:
    """グランドエルダー交流コマンド"""

    def __init__(self):
        self.evolution_system = SelfEvolutionSystem()
        self.grand_elder_interface = GrandElderInterface()
        self.notifier = SlackNotifier()

    async def execute(self, args):
        """メイン実行"""
        try:
            if args.future_vision:
                await self.request_future_vision()
            elif args.review_proposals:
                await self.request_proposals_review()
            elif args.decisions:
                await self.process_decisions(args.decisions)
            elif args.consultation_log:
                await self.show_consultation_log(args.limit)
            else:
                await self.interactive_consultation()

        except Exception as e:
            print(f"❌ エラー: {e}")
            await self.notifier.send_message(f"❌ グランドエルダー交流エラー: {e}")
            raise

    async def interactive_consultation(self):
        """対話型相談"""
        print("👑 グランドエルダーとの対話を開始します")
        print("=" * 60)

        # 保留中の相談確認
        pending = self.evolution_system.pending_consultations

        if not pending:
            print("📭 現在、グランドエルダーへの相談事項はありません")
            print("💡 新しい進化企画が作成されたら、自動的に相談が開始されます")
            return

        # 最新の相談を表示
        latest_consultation = pending[-1]

        print("📋 グランドエルダーへの相談事項:")
        print(latest_consultation["consultation_message"])
        print("\n" + "=" * 60)

        # 未来ビジョンの入力を促す
        print("\n🔮 まず、Elders Guildの未来について、ビジョンをお聞かせください:")
        print("  1. 📈 成長の方向性 - どの領域に注力すべきか")
        print("  2. 🎯 戦略的優先順位 - 最も重要な進化は何か")
        print("  3. 🚀 技術革新 - 採用すべき新技術の方向性")
        print("  4. 🌟 競争優位 - 独自性を生み出す要素")
        print("  5. ⚖️ バランス - 安定性と革新性のバランス")

        print("\n👑 グランドエルダーのビジョンを入力してください:")
        print("(複数行入力可能。完了時は空行を入力)")

        future_vision_lines = []
        while True:
            line = input("> ")
            if line.strip() == "":
                break
            future_vision_lines.append(line)

        future_vision = "\n".join(future_vision_lines)

        if not future_vision.strip():
            print("❌ 未来ビジョンが入力されませんでした")
            return

        # 企画一覧表示
        print("\n📋 承認待ち企画一覧:")
        self._display_proposals_summary(latest_consultation["proposals_summary"])

        # 決定要請
        print("\n👑 各企画についての決定をお願いします:")
        print("  選択肢: approved(承認) / rejected(否決) / deferred(保留)")

        decisions = {}
        proposals_summary = latest_consultation["proposals_summary"]

        # 各カテゴリの企画について決定を要請
        for category, proposals in proposals_summary["by_category"].items():
            if proposals:
                print(f"\n📂 {category.upper()} カテゴリ:")
                for proposal in proposals:
                    print(f"  💡 {proposal['title']}")
                    print(
                        f"     価値: {proposal['business_value']:.1%}, 複雑度: {proposal['complexity']:.1%}"
                    )

                    while True:
                        decision = (
                            input(f"     決定 (approved/rejected/deferred): ")
                            .strip()
                            .lower()
                        )
                        if decision in ["approved", "rejected", "deferred"]:
                            decisions[proposal["id"]] = decision
                            break
                        else:
                            print(
                                "     ❌ 無効な選択です。approved/rejected/deferred のいずれかを入力してください"
                            )

        # 決定処理
        await self.process_elder_decisions(future_vision, decisions)

    async def request_future_vision(self):
        """未来ビジョン要請"""
        print("🔮 グランドエルダーへの未来ビジョン要請")
        print("=" * 50)

        vision_request = await self.grand_elder_interface._request_future_vision()
        print(vision_request)

        print("\n👑 上記の観点で、Elders Guildの未来ビジョンをお聞かせください")

    async def request_proposals_review(self):
        """企画審査要請"""
        print("📋 グランドエルダーへの企画審査要請")
        print("=" * 50)

        pending = self.evolution_system.pending_consultations

        if not pending:
            print("📭 現在、審査待ちの企画はありません")
            return

        for i, consultation in enumerate(pending, 1):
            print(f"\n👑 相談 #{i}:")
            print(consultation["consultation_message"])
            print("\n" + "-" * 40)

    async def process_decisions(self, decisions_json):
        """決定事項処理"""
        print("👑 グランドエルダーの決定を処理中...")

        try:
            decisions = json.loads(decisions_json)
        except json.JSONDecodeError:
            print("❌ 決定事項のJSON形式が正しくありません")
            return

        await self.evolution_system.process_grand_elder_decisions(decisions)

        print("✅ グランドエルダーの決定を処理しました")

        # 承認された企画の統計
        approved_count = sum(
            1 for decision in decisions.values() if decision == "approved"
        )
        rejected_count = sum(
            1 for decision in decisions.values() if decision == "rejected"
        )
        deferred_count = sum(
            1 for decision in decisions.values() if decision == "deferred"
        )

        print(f"📊 結果: 承認{approved_count}件, 否決{rejected_count}件, 保留{deferred_count}件")

        if approved_count > 0:
            print(f"🚀 {approved_count}件の企画実装を開始します")

    async def process_elder_decisions(self, future_vision: str, decisions: dict):
        """エルダー決定の処理"""
        print("\n👑 グランドエルダーの決定を記録中...")

        # 未来ビジョンの保存
        vision_record = {
            "timestamp": datetime.now().isoformat(),
            "future_vision": future_vision,
            "decisions": decisions,
        }

        # 決定事項をシステムに反映
        await self.evolution_system.process_grand_elder_decisions(decisions)

        # 結果サマリー
        approved = [k for k, v in decisions.items() if v == "approved"]
        rejected = [k for k, v in decisions.items() if v == "rejected"]
        deferred = [k for k, v in decisions.items() if v == "deferred"]

        print("✅ 決定事項を記録しました")
        print(f"📊 承認: {len(approved)}件, 否決: {len(rejected)}件, 保留: {len(deferred)}件")

        if approved:
            print("🚀 承認された企画の実装を開始します")

        # Slack通知
        await self.notifier.send_message(
            f"👑 グランドエルダーの決定:\n"
            f"承認: {len(approved)}件, 否決: {len(rejected)}件, 保留: {len(deferred)}件\n"
            f"未来ビジョンが更新されました"
        )

    async def show_consultation_log(self, limit=10):
        """相談履歴表示"""
        print(f"📜 グランドエルダー相談履歴 (最新{limit}件)")
        print("=" * 60)

        history = self.grand_elder_interface.consultation_history[-limit:]

        if not history:
            print("📭 相談履歴がありません")
            return

        for i, record in enumerate(reversed(history), 1):
            timestamp = datetime.fromisoformat(
                record["timestamp"].replace("Z", "+00:00")
            )
            print(
                f"\n📅 相談 #{len(history) - i + 1} - {timestamp.strftime('%Y年%m月%d日 %H:%M')}"
            )
            print(f"📋 相談タイプ: {record['consultation_type']}")
            print(f"📊 企画数: {record.get('proposals_count', 'N/A')}件")
            print(f"📊 状況: {record['status']}")

            if len(record.get("consultation_message", "")) > 200:
                preview = record["consultation_message"][:200] + "..."
                print(f"💬 内容: {preview}")
            else:
                print(f"💬 内容: {record.get('consultation_message', 'N/A')}")

    def _display_proposals_summary(self, proposals_summary):
        """企画一覧表示"""
        total = proposals_summary["total_proposals"]
        print(f"📊 総企画数: {total}件")

        if proposals_summary["high_priority"]:
            print("\n🎯 高優先度企画:")
            for title in proposals_summary["high_priority"]:
                print(f"  - {title}")

        if proposals_summary["quick_wins"]:
            print("\n⚡ クイックウィン企画:")
            for title in proposals_summary["quick_wins"]:
                print(f"  - {title}")

        if proposals_summary["resource_intensive"]:
            print("\n🔧 リソース集約型企画:")
            for title in proposals_summary["resource_intensive"]:
                print(f"  - {title}")

        print("\n📂 カテゴリ別詳細:")
        for category, proposals in proposals_summary["by_category"].items():
            if proposals:
                print(f"\n  📁 {category.upper()} ({len(proposals)}件):")
                for proposal in proposals:
                    print(f"    💡 {proposal['title']}")
                    print(
                        f"       価値: {proposal['business_value']:.1%}, 複雑度: {proposal['complexity']:.1%}"
                    )


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Elders Guild グランドエルダー交流システム")

    parser.add_argument("--future-vision", action="store_true", help="未来ビジョンを要請")
    parser.add_argument("--review-proposals", action="store_true", help="企画審査を要請")
    parser.add_argument("--decisions", type=str, help="決定事項をJSON形式で入力")
    parser.add_argument("--consultation-log", action="store_true", help="相談履歴を表示")
    parser.add_argument("--limit", type=int, default=10, help="履歴表示件数 (default: 10)")
    parser.add_argument("--verbose", action="store_true", help="詳細出力")

    args = parser.parse_args()

    # 実行
    command = AIGrandElderCommand()
    asyncio.run(command.execute(args))


if __name__ == "__main__":
    main()
