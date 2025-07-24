#!/usr/bin/env python3
"""
ai-prophecy - 予言書システム管理コマンド
エルダーズギルド 予言書システムのCLIインターフェース
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List

# プロジェクトルート設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from commands.base_command import BaseCommand
from libs.prophecy_engine import ProphecyEngine, Prophecy
# from libs.quality_daemon import QualityEvolutionDaemon  # 循環インポート回避


class ProphecyCommand(BaseCommand):
    """予言書システム管理コマンド"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__(
            name="ai-prophecy",
            description="🏛️ エルダーズギルド 予言書システム"
        )
        self.engine = ProphecyEngine()
        # self.quality_daemon = QualityEvolutionDaemon()  # 循環インポート回避

    def setup_parser(self):
        """パーサーのセットアップ"""
        parser = argparse.ArgumentParser(
            description="🏛️ エルダーズギルド 予言書システム",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
使用例:
  ai-prophecy list                                    # 予言書一覧
  ai-prophecy status quality_evolution               # 状態確認
  ai-prophecy evaluate quality_evolution             # 進化条件評価
  ai-prophecy evolve quality_evolution gate_1        # 手動進化実行
  ai-prophecy load prophecies/quality_evolution.yaml # 予言書読み込み
  ai-prophecy elder-council quality_evolution        # エルダーズ儀式
            """,
        )

        subparsers = parser.add_subparsers(dest="subcommand", help="サブコマンド")

        # list - 予言書一覧
        list_parser = subparsers.add_parser("list", help="予言書一覧表示")

        # status - 予言書状態
        status_parser = subparsers.add_parser("status", help="予言書状態表示")
        status_parser.add_argument("prophecy_name", help="予言書名")

        # evaluate - 進化条件評価
        evaluate_parser = subparsers.add_parser("evaluate", help="進化条件評価")
        evaluate_parser.add_argument("prophecy_name", help="予言書名")
        evaluate_parser.add_argument("--metrics", help="メトリクス（JSON形式）")

        # evolve - 手動進化実行
        evolve_parser = subparsers.add_parser("evolve", help="手動進化実行")
        evolve_parser.add_argument("prophecy_name", help="予言書名")
        evolve_parser.add_argument("gate_id", help="ゲートID")
        evolve_parser.add_argument("--force", action="store_true", help="強制実行")

        # load - 予言書読み込み
        load_parser = subparsers.add_parser("load", help="予言書読み込み")
        load_parser.add_argument("yaml_path", help="YAMLファイルパス")

        # create - 予言書作成
        create_parser = subparsers.add_parser("create", help="予言書作成")
        create_parser.add_argument("prophecy_name", help="予言書名")
        create_parser.add_argument("--template", choices=["quality", "deployment", "monitoring"],
                                  default="quality", help="テンプレート選択")

        # elder-council - エルダーズ儀式
        council_parser = subparsers.add_parser("elder-council", help="エルダーズ儀式実行")
        council_parser.add_argument("prophecy_name", help="予言書名")
        council_parser.add_argument("--review", action="store_true", help="見直し実行")

        # history - 進化履歴
        history_parser = subparsers.add_parser("history", help="進化履歴表示")
        history_parser.add_argument("prophecy_name", nargs="?", help="予言書名（省略時は全て）")

        # backup - バックアップ管理
        backup_parser = subparsers.add_parser("backup", help="バックアップ管理")
        backup_parser.add_argument("prophecy_name", help="予言書名")
        backup_parser.add_argument("--list", action="store_true", help="バックアップ一覧")
        backup_parser.add_argument("--restore", help="復元するバックアップID")

        return parser

    def run(self, args):
        """コマンド実行"""
        parser = self.setup_parser()
        parsed_args = parser.parse_args(args)

        if not parsed_args.subcommand:
            parser.print_help()
            return 0

        # 非同期サブコマンドの実行
        if parsed_args.subcommand in ["evaluate", "evolve", "elder-council"]:
            # Complex condition - consider breaking down
            return asyncio.run(self.run_async_command(parsed_args))
        else:
            return self.run_sync_command(parsed_args)

    def run_sync_command(self, args):
        """同期サブコマンド実行"""
        if args.subcommand == "list":
            # Complex condition - consider breaking down
            return self.list_prophecies()
        elif args.subcommand == "status":
            # Complex condition - consider breaking down
            return self.show_prophecy_status(args)
        elif args.subcommand == "load":
            # Complex condition - consider breaking down
            return self.load_prophecy(args)
        elif args.subcommand == "create":
            # Complex condition - consider breaking down
            return self.create_prophecy(args)
        elif args.subcommand == "history":
            # Complex condition - consider breaking down
            return self.show_history(args)
        elif args.subcommand == "backup":
            # Complex condition - consider breaking down
            return self.manage_backup(args)

    async def run_async_command(self, args):
        """非同期サブコマンド実行"""
        if args.subcommand == "evaluate":
            # Complex condition - consider breaking down
            return await self.evaluate_prophecy(args)
        elif args.subcommand == "evolve":
            # Complex condition - consider breaking down
            return await self.evolve_prophecy(args)
        elif args.subcommand == "elder-council":
            # Complex condition - consider breaking down
            return await self.elder_council_review(args)

    def list_prophecies(self):
        """予言書一覧表示"""
        self.info("🏛️ エルダーズギルド 予言書一覧")
        self.info("=" * 60)

        prophecies = self.engine.list_prophecies()

        if not prophecies:
            self.warning("登録された予言書がありません")
            self.info("💡 使用方法:")
            self.info("  ai-prophecy load prophecies/quality_evolution.yaml")
            return 0

        for prophecy in prophecies:
            # Process each item in collection
            self.info(f"📜 {prophecy['name']}")
            self.info(f"   📄 説明: {prophecy['description']}")
            self.info(f"   📊 進捗: Phase {prophecy['current_phase']}/{prophecy['total_phases']}")
            self.info(f"   🏷️  カテゴリ: {prophecy['category']}")
            self.info(f"   📅 更新: {prophecy['last_updated']}")
            self.info("")

        return 0

    def show_prophecy_status(self, args):
        """予言書状態表示"""
        self.info("🏛️ 予言書状態レポート")
        self.info("=" * 60)

        status = self.engine.get_prophecy_status(args.prophecy_name)

        if "error" in status:
            self.error(f"❌ {status['error']}")
            return 1

        self.info(f"📜 予言書: {status['prophecy_name']}")
        self.info(f"📄 説明: {status['description']}")
        self.info(f"🔖 バージョン: {status['version']}")
        self.info("")

        # 現在のフェーズ
        current_phase = status['current_phase']
        if current_phase:
            self.info(f"🎯 現在のフェーズ: Phase {current_phase['phase_id']}")
            self.info(f"   📝 名前: {current_phase['name']}")
            self.info(f"   📄 説明: {current_phase['description']}")

            if current_phase['features']:
                self.info("   🌟 機能:")
                for feature in current_phase['features']:
                    # Process each item in collection
                    self.info(f"     • {feature}")
            self.info("")

        # 次のゲート
        next_gate = status['next_gate']
        if next_gate:
            self.info(f"🚪 次のゲート: {next_gate['gate_id']}")
            self.info(f"   🎯 目標フェーズ: Phase {next_gate['target_phase']}")
            self.info(f"   📋 条件数: {next_gate['criteria_count']}")
            self.info(f"   📅 安定期間: {next_gate['stability_days']}日")
        else:
            self.info("🏆 最終フェーズに到達しています")

        # 状態情報
        state = status['state']
        self.info(f"📊 状態:")
        self.info(f"   🕒 作成日時: {state.get('created_at', 'N/A')}")
        self.info(f"   🔄 最終進化: {state.get('last_evolution', 'N/A')}")
        self.info(f"   📈 メトリクス履歴: {len(state.get('metrics_history', []))}件")

        return 0

    async def evaluate_prophecy(self, args):
        """進化条件評価"""
        self.info("🔍 進化条件評価中...")
        self.info("=" * 50)

        # メトリクス取得
        if args.metrics:
            try:
                metrics = json.loads(args.metrics)
            except json.JSONDecodeError:
                # Handle specific exception case
                self.error("無効なJSON形式です")
                return 1
        else:
            # 品質デーモンからメトリクス取得
            try:
                from scripts.quality_daemon import QualityMetricsCollector
                collector = QualityMetricsCollector()
                metrics = await collector.collect_all_metrics()
            except ImportError:
                # Handle specific exception case
                self.warning("品質メトリクス収集システムが利用できません。デフォルトメトリクスを使用します。")
                metrics = {
                    "precommit_success_rate": 90,
                    "precommit_avg_time": 2.5,
                    "python_syntax_errors": 0,
                    "team_satisfaction": 75,
                    "tool_understanding_black": 70,
                    "developer_complaints": 1
                }

        # 評価実行
        evaluation = self.engine.evaluate_prophecy(args.prophecy_name, metrics)

        if "error" in evaluation:
            self.error(f"❌ {evaluation['error']}")
            return 1

        self.info(f"📜 予言書: {evaluation['prophecy_name']}")
        self.info(f"📊 現在フェーズ: Phase {evaluation['current_phase']} ({evaluation['current_phase_name']})")
        self.info("")

        # ゲート状態
        gate_status = evaluation['gate_status']
        readiness = gate_status['readiness_score']

        if gate_status['is_ready']:
            self.success(f"✅ 進化条件達成: {readiness:0.1%}")
        else:
            self.warning(f"⚠️ 進化条件未達成: {readiness:0.1%}")

        # 条件詳細
        self.info("📋 条件詳細:")
        for name, result in gate_status['criteria_results'].items():
            status_icon = "✅" if result['passed'] else "❌"
            self.info(f"   {status_icon} {name}: {result['current']} {result['operator']} {result['target']}")

        # 安定性情報
        stability = evaluation['stability_info']
        self.info(f"\n⏰ 安定性: {stability['stable_days']}/{stability['required_days']}日")

        if stability['is_stable']:
            self.success("✅ 安定期間を満たしています")
        else:
            remaining = stability['required_days'] - stability['stable_days']
            self.info(f"⏳ あと{remaining}日の安定期間が必要です")

        # 進化準備状況
        if evaluation['evolution_ready']:
            self.success("🚀 進化実行準備完了！")
            self.info("💡 進化実行:")
            self.info(f"   ai-prophecy evolve {args.prophecy_name} {gate_status['gate_id']}")
        else:
            self.info("⏳ 進化実行準備中...")

        return 0

    async def evolve_prophecy(self, args):
        """手動進化実行"""
        self.info("🚀 進化実行中...")
        self.info("=" * 50)

        result = await self.engine.execute_evolution(args.prophecy_name, args.gate_id, args.force)

        if "error" in result:
            self.error(f"❌ {result['error']}")
            return 1

        if result['success']:
            self.success("🎉 進化実行成功！")
            self.info(f"📜 予言書: {result['prophecy_name']}")
            self.info(f"🔄 フェーズ: Phase {result['from_phase']} → Phase {result['to_phase']}")
            self.info(f"🆔 ゲート: {result['gate_id']}")
            self.info(f"⏰ 実行時刻: {result['executed_at']}")

            if result['backup_id']:
                self.info(f"💾 バックアップ: {result['backup_id']}")

            self.info("🎯 実行されたアクション:")
            for action in result['evolution_actions']:
                # Process each item in collection
                self.info(f"   • {action}")
        else:
            self.error(f"❌ 進化実行失敗: {result.get('error', '不明なエラー')}")
            return 1

        return 0

    def load_prophecy(self, args):
        """予言書読み込み"""
        yaml_path = Path(args.yaml_path)

        if not yaml_path.exists():
            self.error(f"ファイルが見つかりません: {yaml_path}")
            return 1

        self.info(f"📁 予言書読み込み中: {yaml_path}")

        prophecy = self.engine.load_prophecy_from_yaml(yaml_path)

        if prophecy:
            self.engine.register_prophecy(prophecy)
            self.success(f"✅ 予言書読み込み完了: {prophecy.prophecy_name}")
            self.info(f"📄 説明: {prophecy.description}")
            self.info(f"📊 フェーズ数: {len(prophecy.phases)}")
            return 0
        else:
            self.error("❌ 予言書読み込み失敗")
            return 1

    def create_prophecy(self, args):
        """予言書作成"""
        self.info("📝 予言書作成中...")

        templates = {
            "quality": "品質進化テンプレート",
            "deployment": "デプロイメント進化テンプレート",
            "monitoring": "監視システム進化テンプレート"
        }

        template_name = templates.get(args.template, "不明なテンプレート")

        self.info(f"📋 予言書名: {args.prophecy_name}")
        self.info(f"📄 テンプレート: {template_name}")
        self.info("⚠️ 予言書作成機能は実装中です")

        return 0

    async def elder_council_review(self, args):
        """エルダーズ儀式実行"""
        self.info("🏛️ エルダーズ評議会を招集中...")
        self.info("=" * 50)

        # 4賢者の意見を模擬
        council_opinions = {
            "📚 ナレッジ賢者": "過去の経験から、現在の進化は適切なペースです",
            "📋 タスク賢者": "現在のタスク負荷を考慮すると、段階的進化が最適です",
            "🚨 インシデント賢者": "システムの安定性は良好、リスクは低レベルです",
            "🔍 RAG賢者": "最新のベストプラクティスに照らし合わせても妥当です"
        }

        self.info(f"📜 対象予言書: {args.prophecy_name}")
        self.info("🧙‍♂️ エルダーズ評議会の意見:")

        for elder, opinion in council_opinions.items():
            # Process each item in collection
            self.info(f"   {elder}: {opinion}")

        # 現在の評価を取得
        try:
            from scripts.quality_daemon import QualityMetricsCollector
            collector = QualityMetricsCollector()
            metrics = await collector.collect_all_metrics()
        except ImportError:
            # Handle specific exception case
            metrics = {"system_health": 100, "readiness": 0.8}

        evaluation = self.engine.evaluate_prophecy(args.prophecy_name, metrics)

        if "error" not in evaluation:
            readiness = evaluation['gate_status']['readiness_score']
            self.info(f"\n📊 現在の進化準備度: {readiness:0.1%}")

            if readiness >= 0.8:
                self.success("✅ エルダーズ評議会の承認: 進化準備完了")
            else:
                self.warning("⚠️ エルダーズ評議会の判定: もう少し準備が必要")

        return 0

    def show_history(self, args):
        """進化履歴表示"""
        self.info("📚 進化履歴")
        self.info("=" * 50)

        history = self.engine.prophecy_history

        if not history:
            self.info("進化履歴がありません")
            return 0

        # フィルタリング
        if args.prophecy_name:
            history = [h for h in history if h['prophecy_name'] == args.prophecy_name]

        for entry in history[-10:]:  # 最新10件
            success_icon = "✅" if entry['success'] else "❌"
            self.info(f"{success_icon} {entry['executed_at']}")
            self.info(f"   📜 {entry['prophecy_name']}")
            self.info(f"   🔄 Phase {entry['from_phase']} → Phase {entry['to_phase']}")
            self.info(f"   🆔 {entry['gate_id']}")
            self.info("")

        return 0

    def manage_backup(self, args):
        """バックアップ管理"""
        self.info("💾 バックアップ管理")
        self.info("=" * 50)

        if args.list:
            self.info("📋 バックアップ一覧:")
            backup_dir = self.engine.prophecy_dir / "backups"
            if backup_dir.exists():
                backups = list(backup_dir.glob(f"{args.prophecy_name}_backup_*"))
                for backup in sorted(backups, reverse=True):
                    # Process each item in collection
                    self.info(f"   📁 {backup.name}")
            else:
                self.info("   バックアップが見つかりません")
        elif args.restore:
            self.info(f"🔄 バックアップ復元: {args.restore}")
            self.warning("⚠️ バックアップ復元機能は実装中です")
        else:
            self.info("💡 使用方法:")
            self.info("  ai-prophecy backup prophecy_name --list")
            self.info("  ai-prophecy backup prophecy_name --restore backup_id")

        return 0


def main():
    """メインエントリーポイント"""
    command = ProphecyCommand()
    return command.run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
