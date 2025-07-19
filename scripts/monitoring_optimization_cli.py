#!/usr/bin/env python3
"""
Monitoring & Optimization CLI
監視・最適化システムCLI管理ツール

使用例:
python3 scripts/monitoring_optimization_cli.py --start-monitoring
python3 scripts/monitoring_optimization_cli.py --status
python3 scripts/monitoring_optimization_cli.py --analyze
python3 scripts/monitoring_optimization_cli.py --emergency-optimize
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

from libs.monitoring_optimization_system import (
    MonitoringOptimizationSystem,
    MonitoringLevel,
    OptimizationStrategy,
)


class MonitoringOptimizationCLI:
    """監視・最適化システムCLI"""

    def __init__(
        self,
        monitoring_level: MonitoringLevel = MonitoringLevel.DETAILED,
        optimization_strategy: OptimizationStrategy = OptimizationStrategy.BALANCED,
    ):
        self.monitoring_system = MonitoringOptimizationSystem(
            monitoring_level, optimization_strategy
        )
        self.initialized = False

    async def initialize(self):
        """初期化"""
        if not self.initialized:
            init_result = await self.monitoring_system.initialize_system()
            if init_result["success"]:
                self.initialized = True
                print("✅ 監視・最適化システム初期化完了")
            else:
                print(f"❌ 初期化失敗: {init_result.get('error', 'Unknown error')}")
                return False
        return True

    async def start_monitoring(self):
        """監視開始"""
        if not await self.initialize():
            return

        print("🔍 監視・最適化システムを開始します")
        print("=" * 60)

        try:
            result = await self.monitoring_system.start_monitoring()

            if result["success"]:
                print("✅ 監視開始成功")
                print(f"   監視間隔: {result['monitoring_interval']}秒")
                print(f"   開始時刻: {result['start_time']}")
                print("\n📊 監視中...")
                print("🛑 停止するには Ctrl+C を押してください")

                # 監視継続
                try:
                    while True:
                        await asyncio.sleep(10)

                        # 状況更新
                        status = self.monitoring_system.get_system_status()
                        print(
                            f"\r📈 監視サイクル: {status['stats']['monitoring_cycles']} | "
                            f"最適化: {status['stats']['optimizations_applied']} | "
                            f"アラート: {status['stats']['alerts_generated']}",
                            end="",
                        )

                except KeyboardInterrupt:
                    print("\n\n⚠️ 監視を停止しています...")
                    stop_result = await self.monitoring_system.stop_monitoring()
                    if stop_result["success"]:
                        print("✅ 監視停止完了")
                        print(f"   総サイクル: {stop_result['total_cycles']}")
                    else:
                        print(f"❌ 停止エラー: {stop_result.get('error')}")
            else:
                print(f"❌ 監視開始失敗: {result.get('error')}")

        except Exception as e:
            print(f"❌ 監視開始エラー: {e}")

    async def stop_monitoring(self):
        """監視停止"""
        if not await self.initialize():
            return

        print("⏹️ 監視を停止します")
        print("=" * 60)

        try:
            result = await self.monitoring_system.stop_monitoring()

            if result["success"]:
                print("✅ 監視停止成功")
                print(f"   停止時刻: {result['stop_time']}")
                print(f"   総サイクル: {result['total_cycles']}")
            else:
                print(f"❌ 監視停止失敗: {result.get('error')}")

        except Exception as e:
            print(f"❌ 監視停止エラー: {e}")

    async def show_status(self):
        """システム状況表示"""
        if not await self.initialize():
            return

        print("📊 監視・最適化システム状況")
        print("=" * 60)

        try:
            report = await self.monitoring_system.get_monitoring_report()

            if "error" not in report:
                # 監視状況
                monitoring_status = report["monitoring_status"]
                print(f"📈 監視状況:")
                print(f"   アクティブ: {'✅' if monitoring_status['active'] else '❌'}")
                print(f"   監視間隔: {monitoring_status['interval']}秒")
                print(f"   総サイクル: {monitoring_status['cycles']}")
                print(f"   稼働時間: {monitoring_status['uptime']:.1f}秒")

                # システムメトリクス
                if report.get("system_metrics"):
                    metrics = report["system_metrics"]
                    print(f"\n💻 システムメトリクス:")
                    print(f"   CPU使用率: {metrics['cpu_usage']:.1f}%")
                    print(f"   メモリ使用率: {metrics['memory_usage']:.1f}%")
                    print(f"   ディスク使用率: {metrics['disk_usage']:.1f}%")
                    print(f"   エラー率: {metrics['error_rate']:.1f}%")
                    print(f"   応答時間: {metrics['response_time']:.3f}秒")

                # 最新アラート
                if report.get("recent_alerts"):
                    alerts = report["recent_alerts"]
                    print(f"\n🚨 最新アラート ({len(alerts)}件):")
                    for alert in alerts[-5:]:  # 最新5件
                        print(f"   {alert['severity'].upper()}: {alert['message']}")

                # 最適化履歴
                if report.get("recent_optimizations"):
                    optimizations = report["recent_optimizations"]
                    print(f"\n🔧 最適化履歴 ({len(optimizations)}件):")
                    for opt in optimizations[-5:]:  # 最新5件
                        print(f"   {opt['type']}: {opt['result']}")

                # 統計情報
                stats = report["statistics"]
                print(f"\n📊 統計情報:")
                print(f"   監視サイクル: {stats['monitoring_cycles']}")
                print(f"   最適化適用: {stats['optimizations_applied']}")
                print(f"   アラート生成: {stats['alerts_generated']}")
                print(f"   開始時刻: {stats['start_time']}")

            else:
                print(f"❌ 状況取得エラー: {report['error']}")

        except Exception as e:
            print(f"❌ 状況表示エラー: {e}")

    async def run_analysis(self):
        """パフォーマンス分析実行"""
        if not await self.initialize():
            return

        print("🔍 パフォーマンス分析実行")
        print("=" * 60)

        try:
            result = await self.monitoring_system.run_performance_analysis()

            if result["success"]:
                analysis = result["analysis"]

                print("✅ パフォーマンス分析完了")
                print(f"   分析時刻: {analysis['timestamp']}")
                print(f"   システムヘルス: {analysis['system_health']}")
                print(f"   データベースヘルス: {analysis['database_health']}")

                # ボトルネック
                if analysis.get("bottlenecks"):
                    print(f"\n🚫 ボトルネック ({len(analysis['bottlenecks'])}件):")
                    for bottleneck in analysis["bottlenecks"]:
                        print(f"   - {bottleneck}")

                # 最適化機会
                if analysis.get("optimization_opportunities"):
                    print(
                        f"\n💡 最適化機会 ({len(analysis['optimization_opportunities'])}件):"
                    )
                    for opportunity in analysis["optimization_opportunities"]:
                        print(f"   - {opportunity}")

                # 推奨事項
                if analysis.get("recommendations"):
                    print(f"\n📋 推奨事項 ({len(analysis['recommendations'])}件):")
                    for recommendation in analysis["recommendations"]:
                        print(f"   - {recommendation}")

                # サマリー
                print(f"\n📈 分析サマリー:")
                print(f"   推奨事項: {result['recommendations_count']}件")
                print(f"   ボトルネック: {result['bottlenecks_count']}件")
                print(f"   最適化機会: {result['optimization_opportunities']}件")

            else:
                print(f"❌ 分析失敗: {result.get('error')}")

        except Exception as e:
            print(f"❌ 分析エラー: {e}")

    async def emergency_optimize(self):
        """緊急最適化実行"""
        if not await self.initialize():
            return

        print("🚨 緊急最適化実行")
        print("=" * 60)

        try:
            result = await self.monitoring_system.apply_emergency_optimizations()

            if result["success"]:
                print("✅ 緊急最適化完了")
                print(f"   緊急最適化: {result['emergency_optimizations']}件適用")
                print(f"   総最適化: {result['total_optimizations']}件")

                # 詳細確認
                report = await self.monitoring_system.get_monitoring_report()
                if "error" not in report and report.get("recent_optimizations"):
                    print(f"\n🔧 最新の最適化:")
                    for opt in report["recent_optimizations"][-3:]:  # 最新3件
                        print(f"   {opt['type']}: {opt['result']}")

            else:
                print(f"❌ 緊急最適化失敗: {result.get('error')}")

        except Exception as e:
            print(f"❌ 緊急最適化エラー: {e}")

    async def run_demo(self):
        """デモ実行"""
        print("🎬 監視・最適化システムデモ実行")
        print("=" * 60)

        try:
            # システム初期化
            print("1. システム初期化...")
            if not await self.initialize():
                return

            # パフォーマンス分析
            print("\n2. パフォーマンス分析...")
            await self.run_analysis()

            # 緊急最適化
            print("\n3. 緊急最適化...")
            await self.emergency_optimize()

            # 状況確認
            print("\n4. システム状況確認...")
            await self.show_status()

            # 短時間監視
            print("\n5. 短時間監視デモ...")
            print("   5秒間隔で15秒間監視します...")

            self.monitoring_system.monitoring_interval = 5
            start_result = await self.monitoring_system.start_monitoring()

            if start_result["success"]:
                print("   監視開始")
                await asyncio.sleep(15)

                stop_result = await self.monitoring_system.stop_monitoring()
                if stop_result["success"]:
                    print(f"   監視停止 (サイクル: {stop_result['total_cycles']}回)")

            print("\n🎉 デモ実行完了")
            print("✅ 全ての機能が正常に動作しています")

        except Exception as e:
            print(f"❌ デモ実行エラー: {e}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="監視・最適化システムCLI管理ツール")

    # 基本コマンド
    parser.add_argument("--start-monitoring", action="store_true", help="監視開始")
    parser.add_argument("--stop-monitoring", action="store_true", help="監視停止")
    parser.add_argument("--status", action="store_true", help="システム状況表示")
    parser.add_argument("--analyze", action="store_true", help="パフォーマンス分析")
    parser.add_argument("--emergency-optimize", action="store_true", help="緊急最適化")
    parser.add_argument("--demo", action="store_true", help="デモ実行")

    # 設定オプション
    parser.add_argument(
        "--monitoring-level",
        choices=["basic", "detailed", "comprehensive"],
        default="detailed",
        help="監視レベル",
    )
    parser.add_argument(
        "--optimization-strategy",
        choices=["conservative", "balanced", "aggressive"],
        default="balanced",
        help="最適化戦略",
    )

    args = parser.parse_args()

    # 設定適用
    monitoring_level = MonitoringLevel(args.monitoring_level)
    optimization_strategy = OptimizationStrategy(args.optimization_strategy)

    # CLIインスタンス作成
    cli = MonitoringOptimizationCLI(monitoring_level, optimization_strategy)

    async def run_cli():
        try:
            if args.start_monitoring:
                await cli.start_monitoring()
            elif args.stop_monitoring:
                await cli.stop_monitoring()
            elif args.status:
                await cli.show_status()
            elif args.analyze:
                await cli.run_analysis()
            elif args.emergency_optimize:
                await cli.emergency_optimize()
            elif args.demo:
                await cli.run_demo()
            else:
                parser.print_help()
                print("\n💡 使用例:")
                print(
                    "   python3 scripts/monitoring_optimization_cli.py --start-monitoring"
                )
                print("   python3 scripts/monitoring_optimization_cli.py --status")
                print("   python3 scripts/monitoring_optimization_cli.py --analyze")
                print(
                    "   python3 scripts/monitoring_optimization_cli.py --emergency-optimize"
                )
                print("   python3 scripts/monitoring_optimization_cli.py --demo")
                print("\n🔧 設定例:")
                print(
                    "   --monitoring-level comprehensive --optimization-strategy aggressive"
                )

        except KeyboardInterrupt:
            print("\n⚠️ 処理が中断されました")
        except Exception as e:
            print(f"\n❌ エラーが発生しました: {e}")

    # 非同期実行
    asyncio.run(run_cli())


if __name__ == "__main__":
    main()
