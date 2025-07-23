#!/usr/bin/env python3
"""
ai-prophecy-dashboard - 予言書ダッシュボード
エルダーズギルド 予言書システムの包括的な状態監視・管理インターフェース
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# プロジェクトルート設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from commands.base_command import BaseCommand
from libs.prophecy_engine import ProphecyEngine
from libs.prophecy_management_system import ProphecyManagementSystem
from libs.elder_council import ElderCouncil


class ProphecyDashboardCommand(BaseCommand):
    """予言書ダッシュボードコマンド"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__(
            name="ai-prophecy-dashboard",
            description="🏛️ エルダーズギルド 予言書ダッシュボード"
        )
        self.prophecy_engine = ProphecyEngine()
        self.management_system = ProphecyManagementSystem()
        self.elder_council = ElderCouncil(self.prophecy_engine)

    def setup_parser(self):
        """パーサーのセットアップ"""
        parser = argparse.ArgumentParser(
            description="🏛️ エルダーズギルド 予言書ダッシュボード",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
🏛️ 予言書システム包括ダッシュボード:

現在の予言書の状態を包括的に表示・管理します。

使用例:
  ai-prophecy-dashboard                       # 全体ダッシュボード
  ai-prophecy-dashboard --active-only         # 活動中の予言書のみ
  ai-prophecy-dashboard --with-metrics        # メトリクス付き表示
  ai-prophecy-dashboard --elder-council       # エルダーズ評議会状況
  ai-prophecy-dashboard --export dashboard.json  # ダッシュボード出力
            """,
        )

        parser.add_argument("--active-only", action="store_true", help="活動中の予言書のみ表示")
        parser.add_argument("--with-metrics", action="store_true", help="メトリクス付き表示")
        parser.add_argument("--elder-council", action="store_true", help="エルダーズ評議会状況")
        parser.add_argument("--export", help="ダッシュボードをJSONで出力")
        parser.add_argument("--watch", action="store_true", help="リアルタイム監視モード")
        parser.add_argument("--summary", action="store_true", help="サマリー表示")

        return parser

    def run(self, args):
        """コマンド実行"""
        parser = self.setup_parser()
        parsed_args = parser.parse_args(args)

        if parsed_args.watch:
            return asyncio.run(self.run_watch_mode(parsed_args))
        else:
            return self.show_dashboard(parsed_args)

    def show_dashboard(self, args):
        """ダッシュボード表示"""
        self.info("🏛️ エルダーズギルド 予言書ダッシュボード")
        self.info("=" * 70)
        self.info(f"⏰ 表示時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.info("")

        # システム全体の状況
        self.show_system_overview()

        # 予言書一覧
        self.show_prophecy_list(args.active_only)

        # メトリクス付き表示
        if args.with_metrics:
            self.show_metrics_summary()

        # エルダーズ評議会状況
        if args.elder_council:
            self.show_elder_council_status()

        # ダッシュボード出力
        if args.export:
            dashboard_data = self.collect_dashboard_data()
            self.export_dashboard(dashboard_data, args.export)

        return 0

    def show_system_overview(self):
        """システム概要表示"""
        self.info("🎯 システム概要")
        self.info("-" * 50)

        # 基本予言書エンジン
        basic_prophecies = self.prophecy_engine.list_prophecies()

        # 管理システム
        managed_prophecies = self.management_system.list_managed_prophecies()

        # 統計情報
        self.info(f"📜 基本予言書: {len(basic_prophecies)}件")
        self.info(f"🏛️ 管理予言書: {len(managed_prophecies)}件")

        # 品質デーモン状態
        try:
            daemon_status = self.check_quality_daemon_status()
            self.info(f"🤖 品質デーモン: {daemon_status}")
        except:
            self.info("🤖 品質デーモン: 停止中")

        # 既存ファイルの確認
        prophecy_files = self.scan_prophecy_files()
        self.info(f"📁 予言書ファイル: {len(prophecy_files)}件")

        self.info("")

    def show_prophecy_list(self, active_only=False):
        """予言書一覧表示"""
        self.info("📜 予言書一覧")
        self.info("-" * 50)

        # 基本予言書エンジンから取得
        basic_prophecies = self.prophecy_engine.list_prophecies()

        # 管理システムから取得
        managed_prophecies = self.management_system.list_managed_prophecies()

        # 既存ファイルから取得
        prophecy_files = self.scan_prophecy_files()

        if basic_prophecies:
            self.info("🔮 基本予言書エンジン:")
            for prophecy in basic_prophecies:
                # Process each item in collection
                self.info(f"   📋 {prophecy['name']}")
                self.info(f"      📄 {prophecy['description']}")
                self.info(f"      📊 Phase {prophecy['current_phase']}/{prophecy['total_phases']}")
                self.info(f"      🏷️  {prophecy['category']}")
                self.info("")

        if managed_prophecies:
            self.info("🏛️ 管理システム:")
            for prophecy in managed_prophecies:
                # Process each item in collection
                if active_only and prophecy['lifecycle_stage'] != 'active':
                    # Complex condition - consider breaking down
                    continue

                self.info(f"   📋 {prophecy['prophecy_name']}")
                self.info(f"      📊 {prophecy['lifecycle_stage']}")
                self.info(f"      🎯 リスク: {prophecy['risk_level']}")
                self.info(f"      ✅ 品質: {prophecy['quality_score']:.1%}")
                self.info(f"      🔖 v{prophecy['latest_version']}")
                self.info("")

        if prophecy_files and not basic_prophecies and not managed_prophecies:
            # Complex condition - consider breaking down
            self.info("📁 検出された予言書ファイル:")
            for file_path in prophecy_files:
                # Process each item in collection
                self.info(f"   📄 {file_path.name}")
                self.info(f"      📁 {file_path}")

                # ファイルの基本情報
                try:
                    stat = file_path.stat()
                    size = stat.st_size
                    modified = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                    self.info(f"      📊 サイズ: {size}B, 更新: {modified}")
                except:
                    pass
                self.info("")

        if not basic_prophecies and not managed_prophecies and not prophecy_files:
            # Complex condition - consider breaking down
            self.warning("📋 現在アクティブな予言書はありません")
            self.info("")
            self.info("💡 予言書を開始するには:")
            self.info("   ai-prophecy load prophecies/quality_evolution.yaml")
            self.info("   ai-prophecy-management create --template quality --name '新システム'")

    def show_metrics_summary(self):
        """メトリクス概要表示"""
        self.info("📊 メトリクス概要")
        self.info("-" * 50)

        try:
            # 品質デーモンからメトリクス取得を試行
            from scripts.quality_daemon import QualityMetricsCollector

            # 非同期でメトリクス収集
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            collector = QualityMetricsCollector()
            metrics = loop.run_until_complete(collector.collect_all_metrics())

            self.info("🎯 現在のメトリクス:")
            self.info(f"   📈 Git活動: {metrics.get('git_commits_7d', 0)}コミット (7日間)")
            self.info(f"   ⚙️  Pre-commit: {metrics.get('precommit_success_rate', 0):.1f}% 成功率")
            self.info(f"   🐍 Python: {metrics.get('python_syntax_errors', 0)}件の構文エラー")
            self.info(f"   👥 チーム満足度: {metrics.get('team_satisfaction', 0):.1f}%")
            self.info(f"   🔧 ツール理解度: {metrics.get('tool_understanding_black', 0):.1f}%")

            loop.close()

        except Exception as e:
            # Handle specific exception case
            self.warning("📊 メトリクス収集システムが利用できません")
            self.info("   💡 品質デーモンの起動を確認してください")
            self.info("   🔧 scripts/quality_system_manager.sh start")

        self.info("")

    def show_elder_council_status(self):
        """エルダーズ評議会状況表示"""
        self.info("🏛️ エルダーズ評議会状況")
        self.info("-" * 50)

        # 評議会統計
        council_stats = self.elder_council.get_council_statistics()

        self.info(f"📊 評議会統計:")
        self.info(f"   🏛️ 開催回数: {council_stats['total_council_sessions']}回")
        self.info(f"   🔧 調整実行: {council_stats['total_adjustments']}件")
        self.info(f"   📅 最近30日: {council_stats['recent_sessions_30d']}回")
        self.info(f"   📈 調整率: {council_stats['adjustment_rate']:.1%}")

        if council_stats['last_session']:
            self.info(f"   ⏰ 最終開催: {council_stats['last_session']}")

        # 最近の評議会履歴
        recent_history = self.elder_council.get_council_history(7)

        if recent_history:
            self.info(f"\n📋 最近の評議会活動 ({len(recent_history)}件):")
            for session in recent_history[-3:]:  # 最新3件
                date = session['date'][:10]  # 日付のみ
                reviewed = len(session['prophecies_reviewed'])
                adjusted = len(session['adjustments_made'])
                self.info(f"   📅 {date}: {reviewed}件レビュー, {adjusted}件調整")

        self.info("")

    def scan_prophecy_files(self) -> List[Path]:
        """予言書ファイルのスキャン"""
        prophecy_files = []

        # propheciesディレクトリ
        prophecies_dir = PROJECT_ROOT / "prophecies"
        if prophecies_dir.exists():
            prophecy_files.extend(prophecies_dir.glob("*.yaml"))
            prophecy_files.extend(prophecies_dir.glob("*.yml"))

        # その他の場所
        for pattern in ["*prophecy*.yaml", "*prophecy*.yml"]:
            prophecy_files.extend(PROJECT_ROOT.glob(pattern))

        return sorted(prophecy_files)

    def check_quality_daemon_status(self) -> str:
        """品質デーモンの状態確認"""
        try:
            import subprocess
            result = subprocess.run(
                ['systemctl', 'is-active', 'quality-evolution'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return "✅ 稼働中"
            else:
                return "❌ 停止中"
        except:
            return "❓ 不明"

    def collect_dashboard_data(self) -> Dict:
        """ダッシュボードデータ収集"""
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'system_overview': {
                'basic_prophecies': self.prophecy_engine.list_prophecies(),
                'managed_prophecies': self.management_system.list_managed_prophecies(),
                'prophecy_files': [str(f) for f in self.scan_prophecy_files()]
            },
            'elder_council': {
                'statistics': self.elder_council.get_council_statistics(),
                'recent_history': self.elder_council.get_council_history(7)
            }
        }

        # メトリクス追加（利用可能な場合）
        try:
            from scripts.quality_daemon import QualityMetricsCollector
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            collector = QualityMetricsCollector()
            metrics = loop.run_until_complete(collector.collect_all_metrics())
            dashboard_data['metrics'] = metrics

            loop.close()
        except:
            dashboard_data['metrics'] = {'status': 'unavailable'}

        return dashboard_data

    def export_dashboard(self, dashboard_data: Dict, output_path: str):
        """ダッシュボードデータ出力"""
        output_file = Path(output_path)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2, ensure_ascii=False, default=str)

        self.success(f"📄 ダッシュボード出力完了: {output_file}")

    async def run_watch_mode(self, args):
        """リアルタイム監視モード"""
        self.info("🏛️ エルダーズギルド 予言書ダッシュボード - リアルタイム監視")
        self.info("=" * 70)
        self.info("⏰ Ctrl+C で終了")
        self.info("")

        try:
            while True:
                # 画面クリア（簡易版）
                print("\n" * 5)

                # ダッシュボード表示
                self.show_dashboard(args)

                # 30秒待機
                await asyncio.sleep(30)

        except KeyboardInterrupt:
            # Handle specific exception case
            self.info("\n👋 リアルタイム監視を終了します")
            return 0

    def show_prophecy_recommendations(self):
        """予言書推奨事項表示"""
        self.info("💡 推奨事項")
        self.info("-" * 50)

        # 基本的な推奨事項
        recommendations = []

        # 予言書が少ない場合
        basic_prophecies = self.prophecy_engine.list_prophecies()
        managed_prophecies = self.management_system.list_managed_prophecies()

        if len(basic_prophecies) == 0 and len(managed_prophecies) == 0:
            # Complex condition - consider breaking down
            recommendations.append("📋 予言書を作成してシステムを開始してください")

        # 品質デーモンが停止している場合
        daemon_status = self.check_quality_daemon_status()
        if "停止中" in daemon_status:
            recommendations.append("🤖 品質デーモンを開始してください")

        # 評議会が開催されていない場合
        council_stats = self.elder_council.get_council_statistics()
        if council_stats['total_council_sessions'] == 0:
            recommendations.append("🏛️ エルダーズ評議会の定期開催を設定してください")

        if recommendations:
            for rec in recommendations:
                # Process each item in collection
                self.info(f"   • {rec}")
        else:
            self.info("   ✅ 現在のシステム状態は良好です")

        self.info("")


def main():
    """メインエントリーポイント"""
    command = ProphecyDashboardCommand()
    return command.run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
