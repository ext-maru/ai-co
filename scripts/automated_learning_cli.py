#!/usr/bin/env python3
"""
Automated Learning System CLI
自動化・学習システム CLI インターフェース

使用例:
python3 scripts/automated_learning_cli.py --status
python3 scripts/automated_learning_cli.py --create-task supervised search_results accuracy
python3 scripts/automated_learning_cli.py --start-learning
python3 scripts/automated_learning_cli.py --stop-learning
"""

import sys
import argparse
import asyncio
import json
from pathlib import Path
from datetime import datetime

# パス設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.automated_learning_system import (
    AutomatedLearningSystem,
    LearningType,
    AutomationLevel,
    LearningStatus,
)


class AutomatedLearningCLI:
    """自動化・学習システムCLI"""

    def __init__(self):
        self.learning_system = AutomatedLearningSystem()
        self.initialized = False

    async def initialize(self):
        """初期化"""
        if not self.initialized:
            init_result = await self.learning_system.initialize_learning_system()
            if init_result["success"]:
                self.initialized = True
                print("✅ 自動化・学習システム初期化完了")
            else:
                print(f"❌ 初期化失敗: {init_result.get('error', 'Unknown error')}")
                return False
        return True

    async def show_status(self):
        """システム状況表示"""
        if not await self.initialize():
            return

        print("🤖 自動化・学習システム状況")
        print("=" * 60)

        try:
            status = await self.learning_system.get_learning_status()

            # 基本情報
            print(f"🔧 システム初期化: {'✅' if self.initialized else '❌'}")
            print(
                f"🔄 継続学習: {'✅ 稼働中' if status['continuous_learning_active'] else '❌ 停止中'}"
            )
            print(f"🕐 確認時刻: {status['timestamp']}")

            # タスク統計
            print(f"\n📊 タスク統計:")
            print(f"   総タスク数: {status['total_tasks']}")
            print(f"   アクティブタスク: {status['active_tasks']}")
            print(f"   待機タスク: {status['queued_tasks']}")
            print(f"   完了タスク: {status['completed_tasks']}")
            print(f"   成功率: {status['success_rate']:.2%}")

            # パフォーマンス指標
            if status.get("performance_metrics"):
                metrics = status["performance_metrics"]
                print(f"\n📈 パフォーマンス指標:")
                print(f"   総学習タスク: {metrics['total_learning_tasks']}")
                print(f"   成功学習タスク: {metrics['successful_learning_tasks']}")
                print(f"   平均学習時間: {metrics['average_learning_time']:.2f}秒")
                print(f"   モデル精度向上: {metrics['model_accuracy_improvement']:.2%}")
                print(
                    f"   システム性能向上: {metrics['system_performance_improvement']:.2%}"
                )
                print(f"   知識成長率: {metrics['knowledge_growth_rate']:.2%}")

            # 学習エージェント
            if status.get("learning_agents"):
                print(f"\n🤖 学習エージェント:")
                for agent in status["learning_agents"]:
                    print(f"   ✅ {agent}")

            # 最近の学習履歴
            if status.get("recent_history"):
                print(f"\n📚 最近の学習履歴:")
                for entry in status["recent_history"][-5:]:
                    success_icon = "✅" if entry["success"] else "❌"
                    print(
                        f"   {success_icon} {entry['task_type']} | "
                        f"改善: {entry['performance_improvement']:.2%} | "
                        f"{entry['timestamp']}"
                    )

            # 自動化設定
            if status.get("automation_settings"):
                settings = status["automation_settings"]
                print(f"\n⚙️ 自動化設定:")
                print(
                    f"   自動学習: {'✅' if settings['auto_learning_enabled'] else '❌'}"
                )
                print(
                    f"   自動最適化: {'✅' if settings['auto_optimization_enabled'] else '❌'}"
                )
                print(
                    f"   自動デプロイ: {'✅' if settings['auto_deployment_enabled'] else '❌'}"
                )

                if settings.get("learning_schedule"):
                    schedule = settings["learning_schedule"]
                    print(f"   継続学習: {'✅' if schedule['continuous'] else '❌'}")
                    print(f"   バッチ間隔: {schedule['batch_interval']}秒")
                    print(f"   評価間隔: {schedule['evaluation_interval']}秒")

        except Exception as e:
            print(f"❌ 状況表示エラー: {e}")

    async def create_learning_task(
        self,
        task_type: str,
        data_source: str,
        target_metric: str,
        automation_level: str = "fully_automatic",
        priority: int = 5,
    ):
        """学習タスク作成"""
        if not await self.initialize():
            return

        print(f"📚 学習タスク作成")
        print(f"   タイプ: {task_type}")
        print(f"   データソース: {data_source}")
        print(f"   目標指標: {target_metric}")
        print(f"   自動化レベル: {automation_level}")
        print(f"   優先度: {priority}")
        print("-" * 50)

        try:
            task_id = await self.learning_system.create_learning_task(
                task_type=LearningType(task_type),
                data_source=data_source,
                target_metric=target_metric,
                automation_level=AutomationLevel(automation_level),
                priority=priority,
            )

            print(f"✅ 学習タスク作成成功")
            print(f"   タスクID: {task_id}")
            print(f"   作成時刻: {datetime.now()}")

        except Exception as e:
            print(f"❌ 学習タスク作成失敗: {e}")

    async def start_continuous_learning(self):
        """継続学習開始"""
        if not await self.initialize():
            return

        print("🔄 継続学習開始")
        print("-" * 50)

        try:
            await self.learning_system.start_continuous_learning()
            print("✅ 継続学習が開始されました")
            print("   バックグラウンドで学習が実行されています")

        except Exception as e:
            print(f"❌ 継続学習開始失敗: {e}")

    async def stop_continuous_learning(self):
        """継続学習停止"""
        if not await self.initialize():
            return

        print("⏹️ 継続学習停止")
        print("-" * 50)

        try:
            await self.learning_system.stop_continuous_learning()
            print("✅ 継続学習が停止されました")

        except Exception as e:
            print(f"❌ 継続学習停止失敗: {e}")

    async def execute_learning_tasks(self):
        """学習タスク実行"""
        if not await self.initialize():
            return

        print("🎯 学習タスク実行")
        print("-" * 50)

        try:
            # 現在の状況確認
            status_before = await self.learning_system.get_learning_status()
            queued_before = status_before["queued_tasks"]

            print(f"実行前の待機タスク: {queued_before}")

            # 学習タスク実行
            await self.learning_system._execute_learning_tasks()

            # 実行後の状況確認
            await asyncio.sleep(2)  # 実行完了待機
            status_after = await self.learning_system.get_learning_status()
            active_after = status_after["active_tasks"]

            print(f"実行後のアクティブタスク: {active_after}")
            print("✅ 学習タスク実行完了")

        except Exception as e:
            print(f"❌ 学習タスク実行失敗: {e}")

    async def show_learning_history(self, limit: int = 10):
        """学習履歴表示"""
        if not await self.initialize():
            return

        print(f"📚 学習履歴 (最新{limit}件)")
        print("=" * 60)

        try:
            status = await self.learning_system.get_learning_status()
            history = status.get("recent_history", [])

            if not history:
                print("🔍 学習履歴がありません")
                return

            for i, entry in enumerate(history[-limit:], 1):
                success_icon = "✅" if entry["success"] else "❌"
                print(f"{i}. {success_icon} {entry['task_type'].upper()}")
                print(f"   タスクID: {entry['task_id']}")
                print(f"   性能改善: {entry['performance_improvement']:.2%}")
                print(f"   実行時刻: {entry['timestamp']}")
                print()

        except Exception as e:
            print(f"❌ 学習履歴表示エラー: {e}")

    async def show_available_options(self):
        """利用可能オプション表示"""
        print("🛠️ 利用可能オプション")
        print("=" * 60)

        # 学習タイプ
        print("📚 学習タイプ:")
        learning_types = [
            "supervised (教師あり学習)",
            "unsupervised (教師なし学習)",
            "reinforcement (強化学習)",
            "transfer (転移学習)",
            "online (オンライン学習)",
            "incremental (増分学習)",
        ]

        for learning_type in learning_types:
            print(f"   • {learning_type}")

        # 自動化レベル
        print("\n🤖 自動化レベル:")
        automation_levels = [
            "manual (手動)",
            "semi_automatic (半自動)",
            "fully_automatic (完全自動)",
            "adaptive (適応型)",
        ]

        for level in automation_levels:
            print(f"   • {level}")

        # データソース例
        print("\n💾 データソース例:")
        data_sources = [
            "search_results (検索結果)",
            "user_interactions (ユーザー行動)",
            "knowledge_patterns (知識パターン)",
            "performance_metrics (パフォーマンス指標)",
            "system_logs (システムログ)",
        ]

        for source in data_sources:
            print(f"   • {source}")

        # 目標指標例
        print("\n🎯 目標指標例:")
        target_metrics = [
            "accuracy (精度)",
            "precision (適合率)",
            "recall (再現率)",
            "engagement (エンゲージメント)",
            "performance (パフォーマンス)",
            "quality (品質)",
        ]

        for metric in target_metrics:
            print(f"   • {metric}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="自動化・学習システム CLI")

    # 基本コマンド
    parser.add_argument("--status", action="store_true", help="システム状況表示")
    parser.add_argument("--options", action="store_true", help="利用可能オプション表示")
    parser.add_argument(
        "--history", type=int, default=10, help="学習履歴表示（件数指定）"
    )

    # 学習タスク管理
    parser.add_argument(
        "--create-task",
        nargs=3,
        metavar=("TYPE", "DATA_SOURCE", "TARGET_METRIC"),
        help="学習タスク作成: タイプ データソース 目標指標",
    )
    parser.add_argument(
        "--automation-level",
        choices=["manual", "semi_automatic", "fully_automatic", "adaptive"],
        default="fully_automatic",
        help="自動化レベル",
    )
    parser.add_argument("--priority", type=int, default=5, help="優先度 (1-10)")

    # 継続学習制御
    parser.add_argument("--start-learning", action="store_true", help="継続学習開始")
    parser.add_argument("--stop-learning", action="store_true", help="継続学習停止")
    parser.add_argument("--execute-tasks", action="store_true", help="学習タスク実行")

    args = parser.parse_args()

    # CLIインスタンス作成
    cli = AutomatedLearningCLI()

    async def run_cli():
        try:
            if args.status:
                await cli.show_status()
            elif args.options:
                await cli.show_available_options()
            elif args.history:
                await cli.show_learning_history(args.history)
            elif args.create_task:
                task_type, data_source, target_metric = args.create_task
                await cli.create_learning_task(
                    task_type,
                    data_source,
                    target_metric,
                    args.automation_level,
                    args.priority,
                )
            elif args.start_learning:
                await cli.start_continuous_learning()
            elif args.stop_learning:
                await cli.stop_continuous_learning()
            elif args.execute_tasks:
                await cli.execute_learning_tasks()
            else:
                parser.print_help()
                print("\n💡 使用例:")
                print("   python3 scripts/automated_learning_cli.py --status")
                print("   python3 scripts/automated_learning_cli.py --options")
                print(
                    "   python3 scripts/automated_learning_cli.py --create-task supervised search_results accuracy"
                )
                print("   python3 scripts/automated_learning_cli.py --start-learning")
                print("   python3 scripts/automated_learning_cli.py --history 5")

        except KeyboardInterrupt:
            print("\n⚠️ 処理が中断されました")
        except Exception as e:
            print(f"\n❌ エラーが発生しました: {e}")

    # 非同期実行
    asyncio.run(run_cli())


if __name__ == "__main__":
    main()
