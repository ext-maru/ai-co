#!/usr/bin/env python3
"""
nWo Library Update Command
Think it, Rule it, Own it - 開発界新世界秩序のライブラリ管理コマンド

Usage:
    python3 commands/ai_nwo_library_update.py [options]

Options:
    --analyze-only          分析のみ実行
    --security-only         セキュリティアップデートのみ
    --strategic-only        nWo戦略ライブラリのみ
    --force-update          強制アップデート
    --dry-run              実行せずに計画のみ表示
    --report-only          レポートのみ生成
"""

import asyncio
import argparse
import sys
from pathlib import Path

# パス設定
sys.path.append(str(Path(__file__).parent.parent))

from libs.nwo_library_update_strategy import nWoLibraryUpdateStrategy, UpdatePriority
try:
    from libs.elder_council import ElderCouncil
    from libs.prophecy_engine import ProphecyEngine
    HAS_ELDER_COUNCIL = True
except ImportError:
    # Mock Elder Council for testing
    class ElderCouncil:
        def __init__(self, prophecy_engine=None):
            pass
        async def emergency_report(self, title, message, priority):
            print(f"[Elder Council] {priority}: {title} - {message}")
        async def log_activity(self, title, message, level):
            print(f"[Elder Council] {level}: {title} - {message}")

    class ProphecyEngine:
        def __init__(self):
            pass

    HAS_ELDER_COUNCIL = False

try:
    from libs.nwo_daily_council import nWoDailyCouncil
except ImportError:
    # Mock nWo Daily Council for testing
    class nWoDailyCouncil:
        def __init__(self):
            pass
        async def report_strategic_update(self, libraries):
            print(f"[nWo Daily Council] Strategic Update: {len(libraries)} libraries")


class nWoLibraryUpdateCommand:
    """nWo Library Update Command"""

    def __init__(self):
        self.strategy = nWoLibraryUpdateStrategy()

        # Elder Council初期化
        if HAS_ELDER_COUNCIL:
            try:
                prophecy_engine = ProphecyEngine()
                self.elder_council = ElderCouncil(prophecy_engine)
            except Exception:
                self.elder_council = ElderCouncil()
        else:
            self.elder_council = ElderCouncil()

        self.nwo_council = nWoDailyCouncil()

    async def run_analyze_only(self):
        """分析のみ実行"""
        print("🔍 ライブラリ分析実行中...")

        libraries = await self.strategy.analyze_library_updates()

        print(f"\n📊 分析結果: {len(libraries)} ライブラリ")
        print(f"🔄 アップデート可能: {len([lib for lib in libraries if lib.update_available])}")
        print(f"🚨 セキュリティ: {len([lib for lib in libraries if lib.priority == UpdatePriority.SECURITY_CRITICAL])}")
        print(f"🎯 nWo戦略: {len([lib for lib in libraries if lib.priority == UpdatePriority.NWO_STRATEGIC])}")
        print(f"🏛️ エルダー評議会: {len([lib for lib in libraries if lib.priority == UpdatePriority.ELDER_COUNCIL])}")

        # 詳細表示
        for lib in libraries:
            if lib.update_available:
                status = "🚨" if lib.security_update else "🔄"
                print(f"{status} {lib.name}: {lib.current_version} → {lib.latest_version} ({lib.priority.value})")

    async def run_security_only(self):
        """セキュリティアップデートのみ"""
        print("🚨 セキュリティアップデート実行中...")

        libraries = await self.strategy.analyze_library_updates()
        security_libs = [lib for lib in libraries if lib.priority == UpdatePriority.SECURITY_CRITICAL]

        if not security_libs:
            print("✅ セキュリティアップデートはありません")
            return

        # セキュリティアップデート計画作成
        plans = await self.strategy.create_update_plan(security_libs)

        print(f"🚨 {len(plans)} 件のセキュリティアップデートを実行します")

        # 実行
        results = await self.strategy.execute_update_plan(plans)

        print(f"✅ 完了: {results['succeeded']} 成功, {results['failed']} 失敗")

    async def run_strategic_only(self):
        """nWo戦略ライブラリのみ"""
        print("🎯 nWo戦略ライブラリアップデート実行中...")

        libraries = await self.strategy.analyze_library_updates()
        strategic_libs = [lib for lib in libraries if lib.priority == UpdatePriority.NWO_STRATEGIC]

        if not strategic_libs:
            print("✅ nWo戦略ライブラリのアップデートはありません")
            return

        # nWo評議会に報告
        await self.nwo_council.report_strategic_update(strategic_libs)

        # 戦略アップデート計画作成
        plans = await self.strategy.create_update_plan(strategic_libs)

        print(f"🎯 {len(plans)} 件のnWo戦略アップデートを実行します")

        # 実行
        results = await self.strategy.execute_update_plan(plans)

        print(f"✅ 完了: {results['succeeded']} 成功, {results['failed']} 失敗")

    async def run_force_update(self):
        """強制アップデート"""
        print("⚡ 強制アップデート実行中...")

        libraries = await self.strategy.analyze_library_updates()
        update_libs = [lib for lib in libraries if lib.update_available]

        if not update_libs:
            print("✅ アップデート対象のライブラリはありません")
            return

        # 強制アップデート計画作成（承認無視）
        plans = await self.strategy.create_update_plan(update_libs)

        # 承認要求を無視
        for plan in plans:
            plan.approval_required = False

        print(f"⚡ {len(plans)} 件の強制アップデートを実行します")

        # エルダー評議会に緊急報告
        await self.elder_council.emergency_report(
            "Force Library Update",
            f"強制アップデート実行: {len(plans)} ライブラリ",
            "high"
        )

        # 実行
        results = await self.strategy.execute_update_plan(plans)

        print(f"✅ 完了: {results['succeeded']} 成功, {results['failed']} 失敗")

    async def run_dry_run(self):
        """ドライラン（実行せずに計画のみ）"""
        print("📋 ドライラン実行中...")

        libraries = await self.strategy.analyze_library_updates()
        plans = await self.strategy.create_update_plan(libraries)

        print(f"\n📋 アップデート計画: {len(plans)} 件")

        for plan in plans:
            lib = plan.library
            print(f"""
🔄 {lib.name}
   現在: {lib.current_version} → 最新: {lib.latest_version}
   優先度: {lib.priority.value}
   nWo影響度: {plan.nwo_impact_score}/100
   実行予定: {plan.scheduled_date.strftime('%Y-%m-%d %H:%M')}
   承認必要: {'はい' if plan.approval_required else 'いいえ'}
   破壊的変更: {'はい' if lib.breaking_changes else 'いいえ'}
   テスト: {', '.join(plan.test_requirements)}
""")

    async def run_report_only(self):
        """レポートのみ生成"""
        print("📄 レポート生成中...")

        libraries = await self.strategy.analyze_library_updates()
        plans = await self.strategy.create_update_plan(libraries)

        report = await self.strategy.generate_update_report(libraries, plans)

        # レポート保存
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"knowledge_base/nwo_reports/library_update_report_{timestamp}.md"
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w') as f:
            f.write(report)

        print(f"📄 レポート保存: {report_path}")

        # 簡易表示
        print(report[:1000] + "...")

    async def run_full_cycle(self):
        """フルサイクル実行"""
        print("🌟 nWo Library Update フルサイクル実行中...")

        results = await self.strategy.run_nwo_update_cycle()

        print(f"""
🌟 nWo Library Update 完了
📊 分析ライブラリ: {results['libraries_analyzed']}
📋 作成計画: {results['plans_created']}
⚡ 即座実行: {results['immediate_executions']}
📄 レポート: {results['report_path']}

実行結果:
✅ 成功: {results['execution_results']['succeeded']}
❌ 失敗: {results['execution_results']['failed']}
⏭️ スキップ: {results['execution_results']['skipped']}
""")


async def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(description="nWo Library Update Command")
    parser.add_argument("--analyze-only", action="store_true", help="分析のみ実行")
    parser.add_argument("--security-only", action="store_true", help="セキュリティアップデートのみ")
    parser.add_argument("--strategic-only", action="store_true", help="nWo戦略ライブラリのみ")
    parser.add_argument("--force-update", action="store_true", help="強制アップデート")
    parser.add_argument("--dry-run", action="store_true", help="実行せずに計画のみ表示")
    parser.add_argument("--report-only", action="store_true", help="レポートのみ生成")

    args = parser.parse_args()

    command = nWoLibraryUpdateCommand()

    try:
        if args.analyze_only:
            await command.run_analyze_only()
        elif args.security_only:
            await command.run_security_only()
        elif args.strategic_only:
            await command.run_strategic_only()
        elif args.force_update:
            await command.run_force_update()
        elif args.dry_run:
            await command.run_dry_run()
        elif args.report_only:
            await command.run_report_only()
        else:
            await command.run_full_cycle()

    except Exception as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
