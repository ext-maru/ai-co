#!/usr/bin/env python3
"""
Elders Guild Lightning Commit Command
30秒以内の超高速コミットシステム

使用方法:
  ai-commit-lightning "緊急バグ修正"
  ai-commit-lightning "hotfix: システム停止解決" --emergency
  ai-commit-lightning "fix: 重要API修正" --files src/api.py

設計: クロードエルダー
実装: エルダーズ・ハーモニー・システム
"""

import argparse
import asyncio
import subprocess
import sys
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

from libs.elders_harmony_system import (
    CommitUrgency,
    DevelopmentLayer,
    LightningCommitSystem,
)

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LightningCommitCLI:
    """Lightning Commit コマンドラインインターフェース"""

    def __init__(self):
        """初期化メソッド"""
        self.lightning_system = LightningCommitSystem()
        self.project_root = Path("/home/aicompany/ai_co")

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
            "file_count": min(len(files) / 10, 1.0),  # ファイル数
            "critical_files": 0.0,  # 重要ファイル
            "config_changes": 0.0,  # 設定変更
            "core_changes": 0.0,  # コアシステム変更
        }

        for file in files:
            # 重要ファイルの判定
            if any(
                critical in file.lower()
                for critical in ["config", "core", "libs", "worker", "elder"]
            ):
                complexity_factors["critical_files"] += 0.2

            # 設定ファイル
            if file.endswith((".yaml", ".json", ".conf", ".ini")):
                complexity_factors["config_changes"] += 0.1

            # コアシステム
            if "core/" in file or "libs/" in file:
                # Complex condition - consider breaking down
                complexity_factors["core_changes"] += 0.1

        # 複雑度計算（0.0-1.0）
        total_complexity = sum(complexity_factors.values()) / 4
        return min(total_complexity, 1.0)

    def create_enhanced_commit_message(self, base_message: str, context: dict) -> str:
        """強化されたコミットメッセージ生成"""
        enhanced_message = base_message

        # Lightning Protocol表示
        enhanced_message += "\n\n⚡ Lightning Protocol Commit"

        # 緊急度情報
        if context.get("urgency") == CommitUrgency.EMERGENCY:
            enhanced_message += "\n🚨 EMERGENCY: システム緊急対応"
        elif context.get("urgency") == CommitUrgency.HIGH:
            enhanced_message += "\n🔥 HIGH PRIORITY: 重要修正"

        # ファイル情報
        files = context.get("files", [])
        if files and len(files) <= 5:
            # Complex condition - consider breaking down
            enhanced_message += f"\n📁 Files: {', '.join(files)}"
        elif files:
            enhanced_message += f"\n📁 Files: {len(files)} files changed"

        # 複雑度情報
        complexity = context.get("complexity", 0)
        if complexity > 0.5:
            enhanced_message += f"\n⚠️ Complexity: {complexity:0.1f}"

        # エルダーズ署名
        enhanced_message += "\n\n🤖 Generated with Lightning Protocol"
        enhanced_message += "\n⚡ 30-second commit by Claude Elder"
        enhanced_message += "\n🏛️ Elders Guild Elders Harmony System"

        return enhanced_message

    async def execute_lightning_commit(self, message: str, args) -> bool:
        """Lightning コミット実行"""
        print("⚡ Lightning Protocol 開始...")
        start_time = asyncio.get_event_loop().time()

        try:
            # 1.0 Git状態分析
            git_changes = self.get_git_changes()
            print(f"📊 変更ファイル: {git_changes['total_files']}個")

            # 2.0 自動ステージング（必要に応じて）
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

            # 3.0 コンテキスト作成
            all_files = git_changes["staged"] + (args.files if args.files else [])
            complexity = self.analyze_complexity(all_files)

            # 緊急度判定
            urgency = (
                CommitUrgency.EMERGENCY
                if args.emergency
                else CommitUrgency.HIGH
                if args.high_priority or complexity < 0.3
                else CommitUrgency.NORMAL
            )

            context = {
                "urgency": urgency,
                "files": all_files,
                "complexity": complexity,
                "description": message,
                "git_changes": git_changes,
            }

            print(f"🎯 判定: 緊急度={urgency.value}, 複雑度={complexity:0.2f}")

            # 4.0 レイヤー判定
            layer = self.lightning_system.determine_layer(context)
            print(f"📋 実行レイヤー: {layer.value}")

            if layer != DevelopmentLayer.LIGHTNING:
                print(f"⚠️ Lightning Protocolには適さない変更です")
                print(f"   推奨: ai-commit-{layer.value}")
                return False

            # 5.0 強化コミットメッセージ
            enhanced_message = self.create_enhanced_commit_message(message, context)

            # 6.0 Lightning実行
            print("⚡ Lightning実行中...")
            success = await self.lightning_system.execute_lightning_commit(
                enhanced_message, context
            )

            elapsed = asyncio.get_event_loop().time() - start_time

            if success:
                print(f"✅ Lightning Commit成功! ({elapsed:0.1f}秒)")
                print(f"🚀 コミット完了: 超高速開発実現")
                return True
            else:
                print(f"❌ Lightning Commit失敗 ({elapsed:0.1f}秒)")
                return False

        except Exception as e:
            # Handle specific exception case
            elapsed = asyncio.get_event_loop().time() - start_time
            print(f"💥 Lightning Protocol エラー ({elapsed:0.1f}秒): {e}")
            return False


def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(
        description="Elders Guild Lightning Commit - 30秒以内超高速コミット",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  ai-commit-lightning "緊急バグ修正"
  ai-commit-lightning "hotfix: API停止解決" --emergency
  ai-commit-lightning "fix: 重要修正" --files src/api.py src/core.py
  ai-commit-lightning "patch: 小修正" --high-priority

⚡ Lightning Protocol適用条件:
  - 緊急度: EMERGENCY または HIGH
  - ファイル数: 3個以下
  - 複雑度: 0.3以下
  - システム影響: 限定的
        """,
    )

    parser.add_argument("message", help="コミットメッセージ")

    parser.add_argument("--emergency", action="store_true", help="緊急対応フラグ（最優先処理）")

    parser.add_argument("--high-priority", action="store_true", help="高優先度フラグ")

    parser.add_argument("--files", nargs="+", help="特定ファイルのみコミット")

    parser.add_argument("--dry-run", action="store_true", help="実際のコミットを行わず、実行プランのみ表示")

    args = parser.parse_args()

    # バナー表示
    print("⚡" * 50)
    print("🏛️  Elders Guild Lightning Commit System")
    print("⚡  30秒以内超高速コミット")
    print("🤖  Powered by Elders Harmony System")
    print("⚡" * 50)

    # Lightning CLI実行
    cli = LightningCommitCLI()

    if args.dry_run:
        print("🧪 Dry Run モード - 実際のコミットは行いません")
        # 分析のみ実行
        git_changes = cli.get_git_changes()
        complexity = cli.analyze_complexity(git_changes.get("staged", []))
        print(f"📊 変更ファイル: {git_changes['total_files']}個")
        print(f"🎯 複雑度: {complexity:0.2f}")

        context = {
            "urgency": CommitUrgency.EMERGENCY
            if args.emergency
            else CommitUrgency.NORMAL,
            "files": git_changes.get("staged", []),
            "complexity": complexity,
        }
        layer = cli.lightning_system.determine_layer(context)
        print(f"📋 推奨レイヤー: {layer.value}")

        return

    # 実際の実行
    try:
        success = asyncio.run(cli.execute_lightning_commit(args.message, args))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        # Handle specific exception case
        print("\n⚠️ Lightning Protocol中断")
        sys.exit(1)
    except Exception as e:
        # Handle specific exception case
        print(f"💥 予期しないエラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
