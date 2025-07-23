#!/usr/bin/env python3
"""
Elders Guild Council Commit Command
5分以内の評議会承認コミットシステム

使用方法:
  ai-commit-council "新機能: ユーザー認証システム"
  ai-commit-council "feat: API エンドポイント追加" --high-priority
  ai-commit-council "refactor: コード整理" --files src/core.py src/utils.py

設計: クロードエルダー
実装: エルダーズ・ハーモニー・システム Phase 2
"""

import argparse
import asyncio
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

from libs.elders_harmony_system import (
    CommitUrgency,
    DevelopmentLayer,
    LightningCommitSystem,
    SageConsultationResult,
)
from libs.env_manager import EnvManager

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CouncilCommitCLI:
    """Council Commit コマンドラインインターフェース"""

    def __init__(self):
        """初期化メソッド"""
        self.lightning_system = LightningCommitSystem()
        self.project_root = EnvManager.get_project_root()

    def get_git_changes(self) -> dict:
        """Git変更状況を取得"""
        try:
            # ステージされた変更
            staged_result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            # ステージされていない変更
            unstaged_result = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            # 追跡されていないファイル
            untracked_result = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            staged_files = (
                staged_result.stdout.strip().split("\n")
                if staged_result.stdout.strip()
                else []
            )
            unstaged_files = (
                unstaged_result.stdout.strip().split("\n")
                if unstaged_result.stdout.strip()
                else []
            )
            untracked_files = (
                untracked_result.stdout.strip().split("\n")
                if untracked_result.stdout.strip()
                else []
            )

            return {
                "staged": staged_files,
                "unstaged": unstaged_files,
                "untracked": untracked_files,
                "total_files": len(staged_files)
                + len(unstaged_files)
                + len(untracked_files),
            }

        except Exception as e:
            # Handle specific exception case
            logger.error(f"Git状態取得エラー: {e}")
            return {"staged": [], "unstaged": [], "untracked": [], "total_files": 0}

    def auto_stage_changes(self, specific_files: list = None) -> bool:
        """変更を自動ステージ"""
        try:
            if specific_files:
                # 指定ファイルのみ
                cmd = ["git", "add"] + specific_files
            else:
                # 全変更をステージ
                cmd = ["git", "add", "."]

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.project_root
            )

            return result.returncode == 0

        except Exception as e:
            # Handle specific exception case
            logger.error(f"Auto stage エラー: {e}")
            return False

    def analyze_complexity(self, files: list) -> float:
        """変更の複雑度を分析"""
        if not files:
            return 0.0

        complexity_factors = {
            "file_count": min(len(files) / 15, 1.0),  # ファイル数（Council用に調整）
            "critical_files": 0.0,  # 重要ファイル
            "config_changes": 0.0,  # 設定変更
            "core_changes": 0.0,  # コアシステム変更
            "test_changes": 0.0,  # テストファイル
        }

        for file in files:
            # 重要ファイルの判定
            if any(
                critical in file.lower()
                for critical in ["config", "core", "libs", "worker", "elder"]
            ):
                complexity_factors["critical_files"] += 0.15

            # 設定ファイル
            if file.endswith((".yaml", ".json", ".conf", ".ini")):
                complexity_factors["config_changes"] += 0.1

            # コアシステム
            if "core/" in file or "libs/" in file:
                # Complex condition - consider breaking down
                complexity_factors["core_changes"] += 0.12

            # テストファイル（複雑度を下げる）
            if "test" in file.lower() or file.startswith("test_"):
                # Complex condition - consider breaking down
                complexity_factors["test_changes"] -= 0.05

        # 複雑度計算（0.0-1.0）
        total_complexity = sum(complexity_factors.values()) / 5
        return max(min(total_complexity, 1.0), 0.0)

    def create_enhanced_commit_message(
        self,
        base_message: str,
        context: dict,
        sage_results: List[SageConsultationResult],
    ) -> str:
        """強化されたコミットメッセージ生成"""
        enhanced_message = base_message

        # Council Protocol表示
        enhanced_message += "\n\n🏛️ Council Protocol Commit"

        # 4賢者の合意情報
        approvals = sum(1 for r in sage_results if r.approval)
        enhanced_message += f"\n🧙‍♂️ 4賢者合意: {approvals}/{len(sage_results)}名承認"

        # 個別賢者のアドバイス
        for result in sage_results:
            status = "✅" if result.approval else "⚠️"
            enhanced_message += f"\n  {status} {result.sage_name}: {result.advice}"

        # 優先度情報
        if context.get("urgency") == CommitUrgency.HIGH:
            enhanced_message += "\n🔥 HIGH PRIORITY: 重要機能"
        elif context.get("urgency") == CommitUrgency.NORMAL:
            enhanced_message += "\n📋 NORMAL: 標準開発"

        # ファイル情報
        files = context.get("files", [])
        if files and len(files) <= 8:
            # Complex condition - consider breaking down
            enhanced_message += f"\n📁 Files: {', '.join(files)}"
        elif files:
            enhanced_message += f"\n📁 Files: {len(files)} files changed"

        # 複雑度とリスク情報
        complexity = context.get("complexity", 0)
        if complexity > 0.3:
            enhanced_message += f"\n⚠️ Complexity: {complexity:.1f}"

        # 平均リスクスコア
        avg_risk = (
            sum(r.risk_score for r in sage_results) / len(sage_results)
            if sage_results
            else 0
        )
        if avg_risk > 0.5:
            enhanced_message += f"\n🎯 Risk Score: {avg_risk:.2f}"

        # エルダーズ署名
        enhanced_message += "\n\n🤖 Generated with Council Protocol"
        enhanced_message += "\n🏛️ 5-minute commit by 4 Sages Council"
        enhanced_message += "\n⚡ Elders Guild Elders Harmony System"

        return enhanced_message

    def display_sage_consultation_details(
        self, sage_results: List[SageConsultationResult]
    ):
        """賢者相談の詳細表示"""
        print("\n🧙‍♂️ 4賢者評議会結果:")
        print("=" * 50)

        for result in sage_results:
            # Process each item in collection
            status = "✅ 承認" if result.approval else "❌ 反対"
            risk_level = (
                "🟢 低"
                if result.risk_score < 0.3
                else "🟡 中"
                if result.risk_score < 0.7
                else "🔴 高"
            )

            print(f"📚 {result.sage_name}: {status}")
            print(f"   💡 アドバイス: {result.advice}")
            print(f"   🎯 リスク: {risk_level} ({result.risk_score:.2f})")
            print()

    async def execute_council_commit(self, message: str, args) -> bool:
        """Council コミット実行"""
        print("🏛️ Council Protocol 開始...")
        start_time = asyncio.get_event_loop().time()

        try:
            # 1. Git状態分析
            git_changes = self.get_git_changes()
            print(f"📊 変更ファイル: {git_changes['total_files']}個")

            # 2. 自動ステージング（必要に応じて）
            if not git_changes["staged"] and (
                git_changes["unstaged"] or git_changes["untracked"]
            ):
                print("🔄 変更を自動ステージング...")
                if args.files:
                    staged = self.auto_stage_changes(args.files)
                else:
                    staged = self.auto_stage_changes()

                if not staged:
                    print("❌ ステージング失敗")
                    return False

                # 再取得
                git_changes = self.get_git_changes()

            # 3. コンテキスト作成
            all_files = git_changes["staged"] + (args.files if args.files else [])
            complexity = self.analyze_complexity(all_files)

            # 緊急度判定
            urgency = CommitUrgency.HIGH if args.high_priority else CommitUrgency.NORMAL

            context = {
                "urgency": urgency,
                "files": all_files,
                "complexity": complexity,
                "description": message,
                "git_changes": git_changes,
            }

            print(f"🎯 判定: 緊急度={urgency.value}, 複雑度={complexity:.2f}")

            # 4. レイヤー判定
            layer = self.lightning_system.determine_layer(context)
            print(f"📋 実行レイヤー: {layer.value}")

            if layer == DevelopmentLayer.LIGHTNING:
                print("⚡ Lightning Protocolの方が適しています")
                print("   推奨: ai-commit-lightning")
                return False
            elif layer == DevelopmentLayer.GRAND:
                print("👑 Grand Protocolが必要です")
                print("   推奨: ai-commit-grand")
                return False

            # 5. 4賢者評議会開始
            print("🧙‍♂️ 4賢者評議会招集中...")
            sage_results = (
                await self.lightning_system.harmony_engine.council_consultation(context)
            )

            # 6. 相談結果表示
            self.display_sage_consultation_details(sage_results)

            # 7. 合意判定
            decision = self.lightning_system._make_council_decision(sage_results)

            if not decision.approved:
                print(f"❌ 評議会で承認されませんでした")
                print(f"   理由: {decision.reasoning}")
                return False

            print(f"✅ 評議会承認: {decision.reasoning}")

            # 8. 強化コミットメッセージ
            enhanced_message = self.create_enhanced_commit_message(
                message, context, sage_results
            )

            # 9. Council実行
            print("🏛️ Council実行中...")
            success = await self.lightning_system.execute_council_commit(
                enhanced_message, context
            )

            elapsed = asyncio.get_event_loop().time() - start_time

            if success:
                print(f"✅ Council Commit成功! ({elapsed:.1f}秒)")
                print(f"🏛️ 4賢者承認による高品質コミット完了")
                return True
            else:
                print(f"❌ Council Commit失敗 ({elapsed:.1f}秒)")
                return False

        except Exception as e:
            # Handle specific exception case
            elapsed = asyncio.get_event_loop().time() - start_time
            print(f"💥 Council Protocol エラー ({elapsed:.1f}秒): {e}")
            return False


def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(
        description="Elders Guild Council Commit - 4賢者評議会承認コミット",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  ai-commit-council "新機能: ユーザー認証システム"
  ai-commit-council "feat: API エンドポイント追加" --high-priority
  ai-commit-council "refactor: コード整理" --files src/core.py
  ai-commit-council "docs: README更新"

🏛️ Council Protocol適用条件:
  - 優先度: NORMAL または HIGH
  - ファイル数: 3-20個
  - 複雑度: 0.3-0.8
  - 4賢者の過半数承認が必要
        """,
    )

    parser.add_argument("message", help="コミットメッセージ")

    parser.add_argument("--high-priority", action="store_true", help="高優先度フラグ")

    parser.add_argument("--files", nargs="+", help="特定ファイルのみコミット")

    parser.add_argument(
        "--dry-run", action="store_true", help="実際のコミットを行わず、評議会シミュレーションのみ"
    )

    args = parser.parse_args()

    # バナー表示
    print("🏛️" * 50)
    print("🧙‍♂️  Elders Guild Council Commit System")
    print("🏛️  4賢者評議会承認コミット")
    print("🤖  Powered by Elders Harmony System")
    print("🏛️" * 50)

    # Council CLI実行
    cli = CouncilCommitCLI()

    if args.dry_run:
        print("🧪 Dry Run モード - 実際のコミットは行いません")

        # 分析のみ実行
        git_changes = cli.get_git_changes()
        complexity = cli.analyze_complexity(git_changes.get("staged", []))
        print(f"📊 変更ファイル: {git_changes['total_files']}個")
        print(f"🎯 複雑度: {complexity:.2f}")

        context = {
            "urgency": CommitUrgency.HIGH
            if args.high_priority
            else CommitUrgency.NORMAL,
            "files": git_changes.get("staged", []),
            "complexity": complexity,
        }
        layer = cli.lightning_system.determine_layer(context)
        print(f"📋 推奨レイヤー: {layer.value}")

        # 評議会シミュレーション
        print("\n🧙‍♂️ 4賢者評議会シミュレーション実行中...")
        try:
            sage_results = asyncio.run(
                cli.lightning_system.harmony_engine.council_consultation(context)
            )
            cli.display_sage_consultation_details(sage_results)
        except Exception as e:
            # Handle specific exception case
            print(f"❌ シミュレーションエラー: {e}")

        return

    # 実際の実行
    try:
        success = asyncio.run(cli.execute_council_commit(args.message, args))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        # Handle specific exception case
        print("\n⚠️ Council Protocol中断")
        sys.exit(1)
    except Exception as e:
        # Handle specific exception case
        print(f"💥 予期しないエラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
