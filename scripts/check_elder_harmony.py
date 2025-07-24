#!/usr/bin/env python3
"""
🏛️ エルダーズ・ハーモニー整合性チェック
4賢者システムの健全性を確認
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ロギング設定
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class ElderHarmonyChecker:
    """エルダーズ・ハーモニー整合性チェッカー"""

    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.critical_issues = []

    def check_harmony(self) -> bool:
        """4賢者システムの整合性をチェック"""
        logger.info("🏛️ エルダーズ・ハーモニー整合性チェック開始")
        logger.info("=" * 60)

        # チェック項目
        checks = [
            ("4賢者システム構成", self._check_four_sages),
            ("ナレッジ賢者", self._check_knowledge_sage),
            ("タスク賢者", self._check_task_sage),
            ("インシデント賢者", self._check_incident_sage),
            ("RAG賢者", self._check_rag_sage),
            ("エルダーサーバント連携", self._check_elder_servants),
            ("騎士団システム", self._check_knights_system),
            ("データベース整合性", self._check_database_integrity),
            ("設定ファイル", self._check_config_files),
            ("必須モジュール", self._check_required_modules),
        ]

        # 各チェックを実行
        for check_name, check_func in checks:
            logger.info(f"\n🔍 {check_name} チェック中...")
            try:
                if check_func():
                    logger.info(f"  ✅ {check_name}: 正常")
                    self.checks_passed += 1
                else:
                    logger.warning(f"  ❌ {check_name}: 異常")
                    self.checks_failed += 1
            except Exception as e:
                logger.error(f"  💥 {check_name}: エラー - {e}")
                self.checks_failed += 1
                self.critical_issues.append(f"{check_name}: {e}")

        # 結果サマリー
        logger.info("\n" + "=" * 60)
        logger.info("📊 チェック結果")
        logger.info("=" * 60)
        logger.info(f"✅ 成功: {self.checks_passed}")
        logger.info(f"❌ 失敗: {self.checks_failed}")

        if self.critical_issues:
            logger.error("\n🚨 クリティカルな問題:")
            for issue in self.critical_issues:
                logger.error(f"  - {issue}")

        # すべてのチェックが成功した場合のみTrue
        return self.checks_failed == 0

    def _check_four_sages(self) -> bool:
        """4賢者システム構成をチェック"""
        try:
            # エルダーズ・ハーモニーシステムをインポート
            from libs.elders_harmony_system import SagesHarmonyEngine

            engine = SagesHarmonyEngine()

            # 4賢者がすべて存在するか確認
            required_sages = {"knowledge", "task", "incident", "rag"}
            actual_sages = set(engine.sages.keys())

            if required_sages.issubset(actual_sages):
                logger.info("    📚 ナレッジ賢者: ✓")
                logger.info("    📋 タスク賢者: ✓")
                logger.info("    🚨 インシデント賢者: ✓")
                logger.info("    🔍 RAG賢者: ✓")
                return True
            else:
                missing = required_sages - actual_sages
                logger.error(f"    欠損賢者: {missing}")
                return False

        except ImportError:
            logger.error("    エルダーズ・ハーモニーシステムが見つかりません")
            return False

    def _check_knowledge_sage(self) -> bool:
        """ナレッジ賢者をチェック"""
        knowledge_base_dir = PROJECT_ROOT / "knowledge_base"

        if not knowledge_base_dir.exists():
            return False

        # 重要なナレッジファイルの存在確認
        important_files = [
            "CLAUDE_TDD_GUIDE.md",
            "AI_Company_Core_Knowledge_v5.1.0md",
            "IMPLEMENTATION_SUMMARY_2025_07.0md",
        ]

        missing_files = []
        for file_name in important_files:
            if not (knowledge_base_dir / file_name).exists():
                missing_files.append(file_name)

        if missing_files:
            logger.warning(f"    欠損ナレッジ: {missing_files}")
            return False

        # ナレッジファイル数をカウント
        knowledge_files = list(knowledge_base_dir.glob("*.md"))
        logger.info(f"    ナレッジファイル数: {len(knowledge_files)}")

        return len(knowledge_files) >= 10  # 最低10個のナレッジファイル

    def _check_task_sage(self) -> bool:
        """タスク賢者をチェック"""
        # タスクトラッカーの存在確認
        task_tracker = PROJECT_ROOT / "libs" / "claude_task_tracker.py"
        if not task_tracker.exists():
            return False

        # タスクデータベースの確認
        task_db = PROJECT_ROOT / "task_history.db"
        if task_db.exists():
            logger.info(f"    タスクDB: {task_db.stat().st_size / 1024:0.1f}KB")

        return True

    def _check_incident_sage(self) -> bool:
        """インシデント賢者をチェック"""
        # インシデントマネージャーの存在確認
        incident_manager = PROJECT_ROOT / "libs" / "incident_manager.py"
        if not incident_manager.exists():
            return False

        # インシデント騎士団フレームワークの確認
        knights_framework = PROJECT_ROOT / "libs" / "incident_knights_framework.py"
        if not knights_framework.exists():
            logger.warning("    インシデント騎士団フレームワークが見つかりません")
            # フレームワークがなくても基本的な機能があればOK

        return True

    def _check_rag_sage(self) -> bool:
        """RAG賢者をチェック"""
        # RAGマネージャーの存在確認
        rag_files = [
            PROJECT_ROOT / "libs" / "rag_manager.py",
            PROJECT_ROOT / "libs" / "enhanced_rag_manager.py",
        ]

        return any(f.exists() for f in rag_files)

    def _check_elder_servants(self) -> bool:
        """エルダーサーバント連携をチェック"""
        # コマンドディレクトリの確認
        commands_dir = PROJECT_ROOT / "commands"
        if not commands_dir.exists():
            return False

        # 重要なコマンドの存在確認
        important_commands = [
            "ai_commit_auto.py",
            "ai_commit_lightning.py",
            "ai_commit_council.py",
            "ai_commit_grand.py",
        ]

        missing_commands = []
        for cmd in important_commands:
            if not (commands_dir / cmd).exists():
                missing_commands.append(cmd)

        if missing_commands:
            logger.warning(f"    欠損コマンド: {missing_commands}")
            # コマンドが一部なくても基本機能があればOK

        return len(missing_commands) < len(important_commands) // 2

    def _check_knights_system(self) -> bool:
        """騎士団システムをチェック"""
        # 騎士団関連ファイルの確認
        knight_files = [
            "command_guardian_knight.py",
            "auto_repair_knight.py",
            "slack_guardian_knight.py",
            "api_integration_knight.py",
        ]

        libs_dir = PROJECT_ROOT / "libs"
        found_knights = 0

        for knight_file in knight_files:
            if (libs_dir / knight_file).exists():
                found_knights += 1

        logger.info(f"    発見された騎士: {found_knights}/{len(knight_files)}")

        return found_knights >= 2  # 最低2つの騎士が必要

    def _check_database_integrity(self) -> bool:
        """データベース整合性をチェック"""
        try:
            import sqlite3

            # エルダーダッシュボードDB
            elder_db = PROJECT_ROOT / "elder_dashboard.db"
            if elder_db.exists():
                conn = sqlite3connect(str(elder_db))
                cursor = conn.cursor()

                # テーブル存在確認
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()

                logger.info(f"    テーブル数: {len(tables)}")

                conn.close()
                return True
            else:
                logger.info("    エルダーダッシュボードDBは未作成（初回は正常）")
                return True

        except Exception as e:
            logger.error(f"    データベースエラー: {e}")
            return False

    def _check_config_files(self) -> bool:
        """設定ファイルをチェック"""
        config_dir = PROJECT_ROOT / "config"

        if not config_dir.exists():
            config_dir.mkdir(exist_ok=True)

        # 重要な設定ファイル
        important_configs = ["incident_knights_config.json", "notification_config.json"]

        found_configs = 0
        for config_file in important_configs:
            if (config_dir / config_file).exists():
                found_configs += 1

        logger.info(f"    設定ファイル: {found_configs}/{len(important_configs)}")

        # .envファイルの確認
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            logger.info("    .envファイル: ✓")
        else:
            logger.warning("    .envファイル: ✗")

        return True  # 設定ファイルがなくても動作可能

    def _check_required_modules(self) -> bool:
        """必須モジュールをチェック"""
        required_modules = ["click", "rich", "aiofiles", "pytest", "pre_commit"]

        missing_modules = []

        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)

        if missing_modules:
            logger.warning(f"    欠損モジュール: {missing_modules}")
            logger.info("    ヒント: pip install " + " ".join(missing_modules))

        return len(missing_modules) == 0

    def generate_report(self):
        """整合性レポートを生成"""
        report = {
            "check_time": datetime.now().isoformat(),
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "critical_issues": self.critical_issues,
            "harmony_status": "healthy" if self.checks_failed == 0 else "unhealthy",
        }

        # レポート保存
        report_file = PROJECT_ROOT / "data" / "elder_harmony_check.json"
        report_file.parent.mkdir(exist_ok=True)

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"\n📋 レポート保存: {report_file}")


def main():
    """メイン実行関数"""
    checker = ElderHarmonyChecker()

    # 整合性チェック実行
    success = checker.check_harmony()

    # レポート生成
    checker.generate_report()

    # 終了コード
    if success:
        logger.info("\n✅ エルダーズ・ハーモニーは健全です")
        sys.exit(0)
    else:
        logger.error("\n❌ エルダーズ・ハーモニーに問題があります")
        sys.exit(1)


if __name__ == "__main__":
    main()
