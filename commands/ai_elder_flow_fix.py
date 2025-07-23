#!/usr/bin/env python3
"""
Elder Flow Fix Command
エルダーフロー違反修正コマンド - 品質第一の鉄則を守る

Usage:
    python3 commands/ai_elder_flow_fix.py [options]

Options:
    --analyze-only      分析のみ実行
    --fix-abstract      抽象メソッド違反のみ修正
    --fix-identity      アイデンティティ違反のみ修正
    --restart-daemon    品質デーモンのみ再起動
    --force            確認なしで実行
    --report           レポートのみ生成
"""

import asyncio
import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime

# パス設定
sys.path.append(str(Path(__file__).parent.parent))

from libs.elder_flow_violation_resolver import ElderFlowViolationResolver

# Elder Council/ProphecyEngineは使用しない（依存関係の問題）


class ElderFlowFixCommand:
    """Elder Flow Fix Command"""

    def __init__(self):
        """初期化メソッド"""
        self.resolver = ElderFlowViolationResolver()
        self.logger = logging.getLogger(__name__)

        # Elder Council機能は現在無効
        self.elder_council = None
        self.has_council = False

    async def run_analyze_only(self):
        """分析のみ実行"""
        print("🔍 Elder Flow違反分析実行中...")

        violations = await self.resolver.analyze_violations()
        summary = violations['summary']

        print(f"""
📊 Elder Flow違反分析結果
========================
総違反数: {summary['total']}件
Critical: {summary['critical']}件
未解決: {summary['open']}件

違反タイプ別:
- 抽象メソッド: {summary['types']['abstract_methods']}件
- アイデンティティ: {summary['types']['identity']}件
- 品質ゲート: {summary['types']['quality_gates']}件
""")

        # Critical違反の詳細表示
        if summary['critical'] > 0:
            print("\n⚠️ Critical違反詳細:")
            abstract_violations = violations.get('abstract_methods', [])
            if isinstance(abstract_violations, list):
                for v in abstract_violations[:10]:  # 最初の10件
                    if isinstance(v, dict) and v.get('severity') == 'critical':
                        # Complex condition - consider breaking down
                        print(f"- {v['class_name']}.{v['method_name']} ({v['file_path']})")

    async def run_fix_abstract(self):
        """抽象メソッド違反修正"""
        print("🔧 抽象メソッド違反修正開始...")

        # Elder Council報告（現在無効）
        # if self.has_council:
        #     await self.elder_council.emergency_report(
        #         "Abstract Method Violation Fix",
        #         "231件の抽象メソッド違反修正開始",
        #         "high"
        #     )

        results = await self.resolver.resolve_abstract_violations()

        print(f"""
✅ 抽象メソッド違反修正完了
=====================
総違反数: {results['total']}件
解決済み: {results['resolved']}件
失敗: {results['failed']}件
""")

        # 詳細表示
        for detail in results.get('details', []):
            if detail['resolved'] > 0:
                print(f"✅ {detail['class_name']}: {detail['resolved']}メソッド実装")

    async def run_fix_identity(self):
        """アイデンティティ違反修正"""
        print("🆔 アイデンティティ違反修正開始...")

        results = await self.resolver.resolve_identity_violations()

        print(f"""
✅ アイデンティティ違反修正完了
========================
総違反数: {results['total']}件
解決済み: {results['resolved']}件
失敗: {results['failed']}件

更新ファイル:
""")

        for file_path in results.get('updated_files', []):
            # Process each item in collection
            print(f"- {file_path}")

    async def run_restart_daemon(self):
        """品質デーモン再起動"""
        print("🔄 品質デーモン再起動中...")

        result = await self.resolver.restart_quality_daemon()

        if result['status'] == 'success':
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")

    async def run_report(self):
        """レポート生成"""
        print("📄 Elder Flow違反レポート生成中...")

        report = await self.resolver.generate_violation_report()

        # レポート保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"knowledge_base/elder_flow_reports/violation_report_{timestamp}.md"
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w') as f:
            f.write(report)

        print(f"📄 レポート保存: {report_path}")

        # サマリー表示
        print("\n" + report.split("### 🎯 推奨アクション")[0])

    async def run_full_fix(self, force=False):
        """完全修正実行"""
        print("🚀 Elder Flow違反完全修正開始...")

        # 事前分析
        violations = await self.resolver.analyze_violations()
        summary = violations['summary']

        print(f"""
⚠️ 以下の違反を修正します:
- 総違反数: {summary['total']}件
- Critical: {summary['critical']}件
- 抽象メソッド: {summary['types']['abstract_methods']}件
- アイデンティティ: {summary['types']['identity']}件
""")

        # 確認
        if not force:
            response = input("\n続行しますか？ (y/n): ")
            if response.lower() != 'y':
                print("❌ 修正をキャンセルしました")
                return

        # Elder Council緊急会議（可能であれば）
        if self.has_council:
            try:
                await self.elder_council.emergency_report(
                    "Elder Flow Emergency Fix",
                    f"{summary['total']}件の違反修正開始",
                    "critical"
                )
            except AttributeError:
                # emergency_reportメソッドがない場合はスキップ
                self.logger.info("Elder Council報告をスキップ（メソッド未実装）")

        # 完全修正実行
        results = await self.resolver.run_full_resolution()

        print(f"""
✅ Elder Flow違反修正完了
====================
開始時刻: {results['start_time']}
終了時刻: {results.get('end_time', 'N/A')}

修正結果:
- 抽象メソッド: {results['abstract_methods'].get(
    'resolved',
    0)}/{results['abstract_methods'].get('total',
    0
)} 解決
- アイデンティティ: {results['identity'].get('resolved', 0)}/{results['identity'].get('total', 0)} 解決
- 品質デーモン: {results['quality_daemon'].get('status', 'unknown')}

レポート: {results.get('report_path', 'N/A')}
""")

        # Elder Council報告（現在無効）
        # if self.has_council and results.get('abstract_methods', {}).get('resolved', 0) > 0:
            # Complex condition - consider breaking down
        #     await self.elder_council.log_activity(
        #         "Elder Flow Violations Resolved",
        #         f"{results['abstract_methods']['resolved']}件の違反解決完了",
        #         "info"
        #     )

    async def run_interactive(self):
        """対話型修正"""
        print("🎮 Elder Flow違反対話型修正")

        while True:
            print("""
選択してください:
1. 違反分析
2. 抽象メソッド修正
3. アイデンティティ修正
4. 品質デーモン再起動
5. レポート生成
6. 完全修正実行
0. 終了
""")

            choice = input("選択 (0-6): ")

            try:
                if choice == '0':
                    print("👋 終了します")
                    break
                elif choice == '1':
                    await self.run_analyze_only()
                elif choice == '2':
                    await self.run_fix_abstract()
                elif choice == '3':
                    await self.run_fix_identity()
                elif choice == '4':
                    await self.run_restart_daemon()
                elif choice == '5':
                    await self.run_report()
                elif choice == '6':
                    await self.run_full_fix()
                else:
                    print("❌ 無効な選択です")

            except Exception as e:
                # Handle specific exception case
                print(f"❌ エラー: {e}")

            input("\nEnterキーで続行...")


async def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(description="Elder Flow Fix Command")
    parser.add_argument("--analyze-only", action="store_true", help="分析のみ実行")
    parser.add_argument("--fix-abstract", action="store_true", help="抽象メソッド違反のみ修正")
    parser.add_argument("--fix-identity", action="store_true", help="アイデンティティ違反のみ修正")
    parser.add_argument("--restart-daemon", action="store_true", help="品質デーモンのみ再起動")
    parser.add_argument("--force", action="store_true", help="確認なしで実行")
    parser.add_argument("--report", action="store_true", help="レポートのみ生成")
    parser.add_argument("--interactive", action="store_true", help="対話型モード")

    args = parser.parse_args()

    command = ElderFlowFixCommand()

    try:
        if args.analyze_only:
            await command.run_analyze_only()
        elif args.fix_abstract:
            await command.run_fix_abstract()
        elif args.fix_identity:
            await command.run_fix_identity()
        elif args.restart_daemon:
            await command.run_restart_daemon()
        elif args.report:
            await command.run_report()
        elif args.interactive:
            await command.run_interactive()
        else:
            # デフォルトは完全修正
            await command.run_full_fix(force=args.force)

    except KeyboardInterrupt:
        # Handle specific exception case
        print("\n⚡ 中断されました")
        sys.exit(1)
    except Exception as e:
        # Handle specific exception case
        print(f"❌ エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
