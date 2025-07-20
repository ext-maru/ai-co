#!/usr/bin/env python3
"""
Complete Knowledge Base Migration to PostgreSQL Magic Grimoire System
完全ナレッジベース移行システム - 漏れゼロ保証
"""

import asyncio
import hashlib
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import asyncpg

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.grimoire_database import MagicSchool, SpellType
from libs.rag_grimoire_integration import RagGrimoireConfig, RagGrimoireIntegration

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class MigrationStats:
    """移行統計"""

    total_files: int = 0
    processed_files: int = 0
    successful_migrations: int = 0
    failed_migrations: int = 0
    skipped_files: int = 0
    total_size: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class ComprehensiveKnowledgeMigrator:
    """完全ナレッジ移行システム"""

    def __init__(self):
        self.stats = MigrationStats()
        self.knowledge_base_path = PROJECT_ROOT / "knowledge_base"
        self.grimoire_integration = None
        self.batch_size = 10  # バッチ処理サイズ

        # ファイル分類
        self.file_categories = {
            "master_knowledge": [],
            "elder_council": [],
            "incident_management": [],
            "ai_learning": [],
            "archives": [],
            "special_files": [],
            "executable_scripts": [],
        }

        logger.info("🚀 Complete Knowledge Migration System initialized")

    async def initialize(self):
        """システム初期化"""
        try:
            # Grimoire統合システム初期化
            config = RagGrimoireConfig()
            self.grimoire_integration = RagGrimoireIntegration(config)
            await self.grimoire_integration.initialize()

            logger.info("✅ Grimoire integration system ready")
            return True

        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False

    def analyze_knowledge_base(self) -> Dict[str, Any]:
        """完全ナレッジベース分析"""
        logger.info("🔍 Starting comprehensive knowledge base analysis...")

        analysis = {
            "directories": [],
            "files_by_category": {},
            "special_files": [],
            "external_dependencies": [],
            "total_stats": {},
        }

        # 全ファイルをスキャン
        all_files = []
        for root, dirs, files in os.walk(self.knowledge_base_path):
            for file in files:
                file_path = Path(root) / file
                all_files.append(file_path)

        # ファイル分類
        for file_path in all_files:
            category = self._categorize_file(file_path)
            if category not in analysis["files_by_category"]:
                analysis["files_by_category"][category] = []
            analysis["files_by_category"][category].append(str(file_path))

            # 特殊ファイルの検出
            if self._is_special_file(file_path):
                analysis["special_files"].append(
                    {
                        "path": str(file_path),
                        "type": self._get_special_type(file_path),
                        "size": file_path.stat().st_size if file_path.exists() else 0,
                    }
                )

        # 統計
        analysis["total_stats"] = {
            "total_files": len(all_files),
            "total_size": sum(f.stat().st_size for f in all_files if f.exists()),
            "categories": len(analysis["files_by_category"]),
            "special_files": len(analysis["special_files"]),
        }

        self.stats.total_files = analysis["total_stats"]["total_files"]
        self.stats.total_size = analysis["total_stats"]["total_size"]

        logger.info(
            f"📊 Analysis complete: {self.stats.total_files} files, {self.stats.total_size/1024/1024:.2f}MB"
        )
        return analysis

    def _categorize_file(self, file_path: Path) -> str:
        """ファイルカテゴリ分類"""
        path_str = str(file_path).lower()

        if "master" in path_str or "core_knowledge" in path_str:
            return "master_knowledge"
        elif "elder_council" in path_str or "council" in path_str:
            return "elder_council"
        elif "incident" in path_str or "auto_fix" in path_str:
            return "incident_management"
        elif (
            "learning" in path_str or "feedback" in path_str or "evolution" in path_str
        ):
            return "ai_learning"
        elif "archive" in path_str or "daily_log" in path_str:
            return "archives"
        elif file_path.suffix in [".py", ".sh"]:
            return "executable_scripts"
        elif file_path.suffix == ".md":
            return "documentation"
        elif file_path.suffix == ".json":
            return "structured_data"
        else:
            return "other"

    def _is_special_file(self, file_path: Path) -> bool:
        """特殊ファイル判定"""
        return (
            file_path.is_symlink()
            or file_path.name.startswith(".")
            or file_path.suffix in [".py", ".sh"]
            or file_path.stat().st_size > 100000
            or "postgresql" in file_path.name.lower()  # 100KB以上
            or any(lang in file_path.name for lang in ["japanese", "日本語"])
        )

    def _get_special_type(self, file_path: Path) -> str:
        """特殊ファイルタイプ取得"""
        if file_path.is_symlink():
            return "symbolic_link"
        elif file_path.name.startswith("."):
            return "hidden_file"
        elif file_path.suffix in [".py", ".sh"]:
            return "executable_script"
        elif file_path.stat().st_size > 100000:
            return "large_file"
        else:
            return "special_content"

    async def migrate_all_knowledge(self, dry_run: bool = False) -> Dict[str, Any]:
        """全ナレッジの完全移行"""
        logger.info(
            f"🚀 Starting {'DRY RUN' if dry_run else 'LIVE'} complete knowledge migration..."
        )

        self.stats.start_time = datetime.now()

        # 分析
        analysis = self.analyze_knowledge_base()

        # 移行実行
        migration_results = {}

        for category, files in analysis["files_by_category"].items():
            logger.info(f"📁 Migrating category: {category} ({len(files)} files)")

            category_results = await self._migrate_category(category, files, dry_run)
            migration_results[category] = category_results

            self.stats.processed_files += len(files)

        self.stats.end_time = datetime.now()

        # 結果サマリー
        summary = self._generate_migration_summary(analysis, migration_results)

        # レポート保存
        if not dry_run:
            await self._save_migration_report(summary)

        logger.info(
            f"✅ Migration complete: {self.stats.successful_migrations}/{self.stats.total_files} files"
        )
        return summary

    async def _migrate_category(
        self, category: str, files: List[str], dry_run: bool
    ) -> Dict[str, Any]:
        """カテゴリ別移行"""
        results = {
            "category": category,
            "total_files": len(files),
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "files": [],
        }

        for file_path_str in files:
            file_path = Path(file_path_str)

            try:
                if not file_path.exists():
                    results["skipped"] += 1
                    continue

                # ファイル読み込み
                content = self._read_file_content(file_path)
                if not content:
                    results["skipped"] += 1
                    continue

                # 移行実行
                if not dry_run:
                    spell_id = await self._migrate_single_file(
                        file_path, content, category
                    )
                    results["files"].append(
                        {
                            "path": str(file_path),
                            "spell_id": spell_id,
                            "size": file_path.stat().st_size,
                            "status": "success",
                        }
                    )
                    self.stats.successful_migrations += 1
                else:
                    results["files"].append(
                        {
                            "path": str(file_path),
                            "size": file_path.stat().st_size,
                            "status": "dry_run",
                        }
                    )

                results["successful"] += 1

            except Exception as e:
                logger.error(f"❌ Failed to migrate {file_path}: {e}")
                results["failed"] += 1
                self.stats.failed_migrations += 1
                self.stats.errors.append(f"{file_path}: {str(e)}")

                results["files"].append(
                    {"path": str(file_path), "status": "failed", "error": str(e)}
                )

        return results

    def _read_file_content(self, file_path: Path) -> Optional[str]:
        """ファイルコンテンツ読み込み"""
        try:
            if file_path.suffix == ".json":
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return json.dumps(data, ensure_ascii=False, indent=2)
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
        except Exception as e:
            logger.warning(f"⚠️ Could not read {file_path}: {e}")
            return None

    async def _migrate_single_file(
        self, file_path: Path, content: str, category: str
    ) -> str:
        """単一ファイル移行"""
        # メタデータ準備
        metadata = {
            "original_path": str(file_path),
            "category": category,
            "file_size": len(content),
            "file_type": file_path.suffix,
            "migration_date": datetime.now().isoformat(),
            "relative_path": str(file_path.relative_to(self.knowledge_base_path)),
        }

        # 魔法学派の決定
        magic_school = self._determine_magic_school(file_path, content)

        # 呪文名の生成
        spell_name = self._generate_spell_name(file_path, category)

        # Grimoireシステムに追加
        spell_id = await self.grimoire_integration.add_knowledge_unified(
            spell_name=spell_name,
            content=content,
            metadata=metadata,
            category=category,
            tags=self._generate_tags(file_path, content),
        )

        return spell_id

    def _determine_magic_school(self, file_path: Path, content: str) -> MagicSchool:
        """魔法学派決定"""
        path_str = str(file_path).lower()
        content_lower = content.lower()

        if (
            "incident" in path_str
            or "error" in content_lower
            or "crisis" in content_lower
        ):
            return MagicSchool.CRISIS_SAGE
        elif (
            "task" in path_str
            or "project" in content_lower
            or "workflow" in content_lower
        ):
            return MagicSchool.TASK_ORACLE
        elif "search" in path_str or "rag" in content_lower or "query" in content_lower:
            return MagicSchool.SEARCH_MYSTIC
        else:
            return MagicSchool.KNOWLEDGE_SAGE

    def _generate_spell_name(self, file_path: Path, category: str) -> str:
        """呪文名生成"""
        base_name = file_path.stem
        return f"{category}_{base_name}".replace(" ", "_").replace("-", "_")

    def _generate_tags(self, file_path: Path, content: str) -> List[str]:
        """タグ生成"""
        tags = []

        # パスベースタグ
        path_parts = file_path.parts
        tags.extend([part for part in path_parts if part != "knowledge_base"])

        # コンテンツベースタグ
        content_lower = content.lower()
        tag_keywords = [
            "claude",
            "elder",
            "council",
            "sage",
            "incident",
            "task",
            "rag",
            "postgresql",
            "migration",
            "test",
            "error",
            "system",
            "ai",
        ]

        for keyword in tag_keywords:
            if keyword in content_lower:
                tags.append(keyword)

        return list(set(tags))  # 重複除去

    def _generate_migration_summary(
        self, analysis: Dict[str, Any], results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """移行サマリー生成"""
        duration = (self.stats.end_time - self.stats.start_time).total_seconds()

        return {
            "migration_id": hashlib.md5(
                f"{self.stats.start_time}".encode()
            ).hexdigest()[:16],
            "timestamp": self.stats.start_time.isoformat(),
            "duration_seconds": duration,
            "source_analysis": analysis,
            "migration_results": results,
            "statistics": {
                "total_files": self.stats.total_files,
                "processed_files": self.stats.processed_files,
                "successful_migrations": self.stats.successful_migrations,
                "failed_migrations": self.stats.failed_migrations,
                "skipped_files": self.stats.skipped_files,
                "success_rate": (
                    self.stats.successful_migrations / self.stats.total_files * 100
                )
                if self.stats.total_files > 0
                else 0,
                "total_size_mb": self.stats.total_size / 1024 / 1024,
                "errors": self.stats.errors,
            },
        }

    async def _save_migration_report(self, summary: Dict[str, Any]):
        """移行レポート保存"""
        report_file = PROJECT_ROOT / f"migration_report_{summary['migration_id']}.json"

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 Migration report saved: {report_file}")

    async def verify_migration(self) -> Dict[str, Any]:
        """移行検証"""
        logger.info("🔍 Verifying migration completeness...")

        # PostgreSQLから全データ取得
        grimoire_spells = await self._get_all_grimoire_spells()

        # 元データと比較
        original_files = list(self.knowledge_base_path.rglob("*"))
        original_md_files = [
            f for f in original_files if f.suffix in [".md", ".json"] and f.is_file()
        ]

        verification = {
            "original_files_count": len(original_md_files),
            "migrated_spells_count": len(grimoire_spells),
            "coverage_percentage": (len(grimoire_spells) / len(original_md_files) * 100)
            if original_md_files
            else 0,
            "missing_files": [],
            "verification_passed": False,
        }

        # 不足ファイル検出
        migrated_paths = {
            spell.get("metadata", {}).get("original_path") for spell in grimoire_spells
        }

        for original_file in original_md_files:
            if str(original_file) not in migrated_paths:
                verification["missing_files"].append(str(original_file))

        verification["verification_passed"] = len(verification["missing_files"]) == 0

        logger.info(
            f"✅ Verification complete: {verification['coverage_percentage']:.1f}% coverage"
        )
        return verification

    async def _get_all_grimoire_spells(self) -> List[Dict[str, Any]]:
        """全Grimoire呪文取得"""
        try:
            # PostgreSQLから直接取得
            conn = await asyncpg.connect(os.getenv("GRIMOIRE_DATABASE_URL"))

            rows = await conn.fetch(
                """
                SELECT id, spell_name, content, created_at
                FROM knowledge_grimoire
                ORDER BY created_at DESC
            """
            )

            await conn.close()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"❌ Failed to get grimoire spells: {e}")
            return []

    async def cleanup(self):
        """クリーンアップ"""
        if self.grimoire_integration:
            await self.grimoire_integration.cleanup()


async def main():
    """メイン実行"""
    migrator = ComprehensiveKnowledgeMigrator()

    try:
        # 初期化
        if not await migrator.initialize():
            logger.error("❌ Failed to initialize migrator")
            return

        # ドライランで確認
        logger.info("🧪 Running dry run analysis...")
        dry_run_results = await migrator.migrate_all_knowledge(dry_run=True)

        print("\n" + "=" * 60)
        print("📊 DRY RUN ANALYSIS RESULTS")
        print("=" * 60)
        print(f"Total files found: {dry_run_results['statistics']['total_files']}")
        print(f"Total size: {dry_run_results['statistics']['total_size_mb']:.2f} MB")
        print(f"Categories: {len(dry_run_results['migration_results'])}")

        for category, result in dry_run_results["migration_results"].items():
            print(f"  - {category}: {result['total_files']} files")

        # 実際の移行実行確認
        print("\n" + "=" * 60)
        print("🚀 PROCEEDING WITH LIVE MIGRATION...")
        print("=" * 60)

        logger.info("🚀 Starting LIVE migration...")
        live_results = await migrator.migrate_all_knowledge(dry_run=False)

        print("\n" + "=" * 60)
        print("✅ LIVE MIGRATION COMPLETED")
        print("=" * 60)
        print(f"Successful: {live_results['statistics']['successful_migrations']}")
        print(f"Failed: {live_results['statistics']['failed_migrations']}")
        print(f"Success rate: {live_results['statistics']['success_rate']:.1f}%")

        # 検証
        verification = await migrator.verify_migration()
        print(f"\n🔍 VERIFICATION: {verification['coverage_percentage']:.1f}% coverage")

        if verification["verification_passed"]:
            print("🎉 Migration verification PASSED - No data loss detected!")
        else:
            print(f"⚠️ Missing {len(verification['missing_files'])} files")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise
    finally:
        await migrator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
