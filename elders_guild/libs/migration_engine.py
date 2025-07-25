#!/usr/bin/env python3
"""
Migration Engine for Magic Grimoire System
魔法書システム移行エンジン - 466個MDファイル→PostgreSQL+pgvector
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)

try:
    from libs.grand_elder_approval_system import (
        FourSagesReviewer,
        GrandElderApprovalSystem,
    )
    from libs.grimoire_database import GrimoireDatabase, MagicSchool, SpellType
    from libs.grimoire_vector_search import GrimoireVectorSearch
except ImportError as e:
    # For testing purposes, create mock classes
    logger.warning(f"Import warning: {e}")

    class MockSpellType:
        """MockSpellTypeクラス"""
        KNOWLEDGE = "knowledge"
        PROCEDURE = "procedure"
        CONFIGURATION = "configuration"

        REFERENCE = "reference"

    class MockMagicSchool:
        """MockMagicSchoolクラス"""
        KNOWLEDGE_SAGE = "knowledge_sage"
        TASK_ORACLE = "task_oracle"
        CRISIS_SAGE = "crisis_sage"
        SEARCH_MYSTIC = "search_mystic"

    SpellType = MockSpellType
    MagicSchool = MockMagicSchool

    class MockGrimoireDatabase:
        """MockGrimoireDatabaseクラス"""
        async def initialize(self):
            """initializeメソッド"""
            return True

        async def close(self):
            """closeメソッド"""
            pass

    class MockGrimoireVectorSearch:
        """MockGrimoireVectorSearchクラス"""
        async def initialize(self):
            """initializeメソッド"""
            return True

        async def index_spell(self, spell_id, spell_data):
            """index_spellメソッド"""
            return True

    class MockFourSagesReviewer:
        """MockFourSagesReviewer - 4賢者システム関連クラス"""
        pass

    GrimoireDatabase = MockGrimoireDatabase
    GrimoireVectorSearch = MockGrimoireVectorSearch
    FourSagesReviewer = MockFourSagesReviewer

class MigrationStatus(Enum):
    """移行ステータス"""

    PENDING = "pending"  # 移行待ち
    ANALYZING = "analyzing"  # 分析中
    CLASSIFYING = "classifying"  # 分類中
    DEDUPLICATING = "deduplicating"  # 重複除去中
    INDEXING = "indexing"  # インデックス化中
    COMPLETED = "completed"  # 完了
    FAILED = "failed"  # 失敗
    SKIPPED = "skipped"  # スキップ

class ContentType(Enum):
    """コンテンツタイプ"""

    GUIDE = "guide"  # ガイド・手順書
    REFERENCE = "reference"  # リファレンス

    CONFIG = "config"  # 設定ファイル
    KNOWLEDGE = "knowledge"  # 一般知識
    PROCEDURE = "procedure"  # 手順書

@dataclass
class MigrationResult:
    """移行結果"""

    file_path: str
    status: MigrationStatus
    spell_id: Optional[str] = None
    original_hash: Optional[str] = None
    migration_timestamp: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    duplicate_of: Optional[str] = None
    sage_classification: Optional[Dict[str, Any]] = None

@dataclass
class MigrationBatch:
    """移行バッチ"""

    batch_id: str
    files: List[str]
    batch_size: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_files: int = 0
    successful_migrations: int = 0
    failed_migrations: int = 0
    skipped_files: int = 0
    duplicate_files: int = 0

class MDFileAnalyzer:
    """MDファイル分析クラス"""

    def __init__(self):
        """初期化"""
        self.content_patterns = {
            "code_blocks": r"```[\s\S]*?```",
            "headers": r"^#{1,6}\s+(.+)$",
            "lists": r"^[\s]*[-*+]\s+(.+)$",
            "links": r"\[([^\]]+)\]\(([^)]+)\)",
            "images": r"!\[([^\]]*)\]\(([^)]+)\)",
            "tables": r"\|.*\|",
            "commands": r"`([^`]+)`",
        }

        # Elders Guild特有のパターン
        self.aicompany_patterns = {
            "tdd_content": r"(TDD|test.*driven|pytest|テスト駆動)",
            "sage_references": r"(賢者|sage|ナレッジ賢者|タスク賢者|インシデント賢者|RAG賢者)",
            "ai_tools": r"(claude|gpt|ai-|assistant)",
            "technical_commands": r"(npm|pip|git|docker|pytest)",
            "incident_content": r"(エラー|障害|インシデント|問題|修正|解決)",
            "workflow_content": r"(ワークフロー|手順|プロセス|フロー)",
        }

    async def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """ファイル分析実行"""
        try:
            content = await self._read_file(file_path)
            if not content.strip():
                return {"error": "Empty file"}

            # 基本情報
            basic_info = await self._extract_basic_info(file_path, content)

            # コンテンツ分析
            content_analysis = await self._analyze_content(content)

            # Elders Guild固有分析
            aicompany_analysis = await self._analyze_aicompany_content(content)

            # メタデータ抽出
            metadata = await self._extract_metadata(content)

            # 分類提案
            classification = await self._suggest_classification(content, basic_info)

            return {
                "basic_info": basic_info,
                "content_analysis": content_analysis,
                "aicompany_analysis": aicompany_analysis,
                "metadata": metadata,
                "classification": classification,
                "content_hash": hashlib.sha256(content.encode()).hexdigest(),
            }

        except Exception as e:
            logger.error(f"File analysis failed for {file_path}: {e}")
            return {"error": str(e)}

    async def _read_file(self, file_path: Path) -> str:
        """ファイル読み込み"""
        try:
            return file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # フォールバック
            return file_path.read_text(encoding="utf-8", errors="ignore")

    async def _extract_basic_info(
        self, file_path: Path, content: str
    ) -> Dict[str, Any]:
        """基本情報抽出"""
        stat = file_path.stat()

        # Try to get relative path, fallback to absolute path if not under PROJECT_ROOT
        try:
            relative_path = str(file_path.relative_to(PROJECT_ROOT))
        except ValueError:
            relative_path = str(file_path)

        return {
            "file_name": file_path.name,
            "file_size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime, timezone.utc),
            "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc),
            "line_count": len(content.splitlines()),
            "char_count": len(content),
            "word_count": len(content.split()),
            "relative_path": relative_path,
        }

    async def _analyze_content(self, content: str) -> Dict[str, Any]:
        """コンテンツ分析"""
        analysis = {}

        for pattern_name, pattern in self.content_patterns.items():
            matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
            analysis[pattern_name] = len(matches)

            if pattern_name == "headers" and matches:
                analysis["main_title"] = matches[0] if matches else None
                analysis["section_titles"] = matches[1:] if len(matches) > 1 else []

        # 言語分析
        analysis["language"] = (
            "ja" if re.search(r"[ひらがなカタカナ漢字]", content) else "en"
        )

        # 技術内容の分析
        analysis["technical_density"] = self._calculate_technical_density(content)

        return analysis

    async def _analyze_aicompany_content(self, content: str) -> Dict[str, Any]:
        """Elders Guild固有コンテンツ分析"""
        analysis = {}

        for category, pattern in self.aicompany_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            analysis[category] = len(matches)

        # 4賢者システム関連度
        sage_score = (
            analysis.get("sage_references", 0)
            + analysis.get("tdd_content", 0)
            + analysis.get("ai_tools", 0)
        )
        analysis["sage_relevance_score"] = min(sage_score / 10, 1.0)

        return analysis

    async def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """メタデータ抽出"""
        metadata = {}

        # YAML frontmatter抽出
        yaml_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if yaml_match:
            try:
                import yaml

                metadata["frontmatter"] = yaml.safe_load(yaml_match.group(1))
            except ImportError:
                metadata["frontmatter"] = {"raw": yaml_match.group(1)}

        # タグ抽出
        tags = re.findall(r"#(\w+)", content)
        metadata["hashtags"] = list(set(tags))

        # 日付抽出
        date_patterns = [
            r"(\d{4}-\d{2}-\d{2})",
            r"(\d{4}年\d{1,2}月\d{1,2}日)",
            r"(20\d{2}年\d{1,2}月)",
        ]

        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, content))
        metadata["mentioned_dates"] = list(set(dates))

        return metadata

    async def _suggest_classification(
        self, content: str, basic_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分類提案"""
        content_lower = content.lower()
        file_name_lower = basic_info["file_name"].lower()

        # 魔法学派の判定
        magic_school = MagicSchool.KNOWLEDGE_SAGE  # デフォルト

        if any(
            keyword in content_lower

        ):
            magic_school = MagicSchool.TASK_ORACLE
        elif any(
            keyword in content_lower
            for keyword in ["error", "incident", "エラー", "障害", "緊急", "fix"]
        ):
            magic_school = MagicSchool.CRISIS_SAGE
        elif any(
            keyword in content_lower
            for keyword in ["search", "find", "rag", "検索", "探索"]
        ):
            magic_school = MagicSchool.SEARCH_MYSTIC

        # 呪文タイプの判定
        spell_type = SpellType.KNOWLEDGE  # デフォルト

        if any(
            keyword in content_lower
            for keyword in ["guide", "how to", "手順", "step", "procedure"]
        ):
            spell_type = SpellType.PROCEDURE
        elif any(
            keyword in content_lower
            for keyword in ["config", "setting", "設定", "configuration"]
        ):
            spell_type = SpellType.CONFIGURATION
        elif any(
            keyword in content_lower

        ):

        elif any(
            keyword in content_lower
            for keyword in ["reference", "api", "doc", "リファレンス"]
        ):
            spell_type = SpellType.REFERENCE

        # 威力レベルの推定
        power_level = self._estimate_power_level(content, basic_info)

        # 永続化判定
        is_eternal = self._should_be_eternal(content, basic_info)

        # タグ提案
        suggested_tags = self._suggest_tags(content, basic_info)

        return {
            "magic_school": magic_school,
            "spell_type": spell_type,
            "power_level": power_level,
            "is_eternal": is_eternal,
            "suggested_tags": suggested_tags,
            "confidence_score": self._calculate_confidence(content, basic_info),
        }

    def _calculate_technical_density(self, content: str) -> float:
        """技術密度計算"""
        technical_indicators = [
            r"```",  # コードブロック
            r"`[^`]+`",  # インラインコード
            r"npm|pip|git|docker|pytest|curl|wget",  # コマンド
            r"https?://",  # URL
            r"\.py|\.js|\.md|\.json|\.yaml|\.yml",  # ファイル拡張子
        ]

        total_matches = 0
        for pattern in technical_indicators:
            total_matches += len(re.findall(pattern, content, re.IGNORECASE))

        words = len(content.split())
        return min(total_matches / max(words / 100, 1), 1.0)

    def _estimate_power_level(self, content: str, basic_info: Dict[str, Any]) -> int:
        """威力レベル推定"""
        score = 1

        # サイズによる加点
        if basic_info["char_count"] > 5000:
            score += 2
        elif basic_info["char_count"] > 2000:
            score += 1

        # 技術密度による加点
        technical_density = self._calculate_technical_density(content)
        if technical_density > 0.3:
            score += 2
        elif technical_density > 0.1:
            score += 1

        # 重要キーワードによる加点
        important_keywords = [
            "critical",
            "important",
            "重要",
            "必須",
            "required",
            "essential",
        ]
        if any(keyword in content.lower() for keyword in important_keywords):
            score += 1

        # コード例の多さ
        code_blocks = len(re.findall(r"```", content))
        if code_blocks > 5:
            score += 2
        elif code_blocks > 2:
            score += 1

        return min(score, 10)

    def _should_be_eternal(self, content: str, basic_info: Dict[str, Any]) -> bool:
        """永続化判定"""
        eternal_indicators = [
            "claude.md",
            "readme.md",
            "tdd",
            "test",
            "賢者",
            "sage",
            "core",
            "foundation",
            "base",
            "基本",
            "基盤",
        ]

        content_lower = content.lower()
        file_name_lower = basic_info["file_name"].lower()

        return any(
            indicator in content_lower or indicator in file_name_lower
            for indicator in eternal_indicators
        )

    def _suggest_tags(self, content: str, basic_info: Dict[str, Any]) -> List[str]tags = set():
    """グ提案"""

        # ファイル名ベースのタグ
        file_stem = Path(basic_info["file_name"]).stem.lower():
        if "guide" in file_stem:
            tags.add("guide")
        if "tdd" in file_stem:
            tags.add("tdd")
        if "claude" in file_stem:
            tags.add("claude")

        # コンテンツベースのタグ
        content_lower = content.lower()

        # 技術タグ
        tech_tags = {
            "python": r"python|\.py|pip|pytest",
            "javascript": r"javascript|\.js|npm|node",
            "docker": r"docker|dockerfile|container",
            "git": r"git|github|repository",
            "ai": r"ai|claude|gpt|assistant|人工知能",
            "database": r"database|sql|postgresql|mysql",
            "web": r"web|http|api|rest|html|css",
            "test": r"test|テスト|pytest|unittest",
        }

        for tag, pattern in tech_tags.items():
            if re.search(pattern, content_lower):
                tags.add(tag)

        # Elders Guild固有タグ
        if re.search(r"賢者|sage", content_lower):
            tags.add("four-sages")
        if re.search(r"tdd|テスト駆動", content_lower):
            tags.add("tdd")
        if re.search(r"incident|インシデント|障害", content_lower):
            tags.add("incident")

        return list(tags)[:10]  # 最大10個

    def _calculate_confidence(self, content: str, basic_info: Dict[str, Any]) -> float:
        """信頼度計算"""
        confidence = 0.5  # ベース

        # ファイルサイズによる信頼度
        if basic_info["char_count"] > 1000:
            confidence += 0.2

        # 構造化度
        headers = len(re.findall(r"^#{1,6}\s+", content, re.MULTILINE))
        if headers > 2:
            confidence += 0.1

        # コード例の存在
        if re.search(r"```", content):
            confidence += 0.1

        # Elders Guild固有性
        aicompany_keywords = ["賢者", "claude", "tdd", "elders guild", "エルダー"]
        matches = sum(1 for keyword in aicompany_keywords if keyword in content.lower())
        confidence += min(matches * 0.05, 0.1)

        return min(confidence, 1.0)

class DuplicateDetector:
    """重複検出クラス"""

    def __init__(self):
        """初期化"""
        self.similarity_threshold = 0.8
        self.content_hashes = {}
        self.similar_groups = []

    async def detect_duplicates(
        self, analyzed_files: List[Dict[str, Any]]
    ) -> List[List[str]]:
        """重複検出実行"""
        try:
            # ハッシュベースの完全一致検出
            exact_duplicates = await self._find_exact_duplicates(analyzed_files)

            # 類似度ベースの類似検出
            similar_groups = await self._find_similar_content(analyzed_files)

            # 結果統合
            all_duplicate_groups = exact_duplicates + similar_groups

            logger.info(
                f"🔍 重複検出完了: {len(exact_duplicates)}個の完全一致, {len(similar_groups)}個の類似グループ"
            )
            return all_duplicate_groups

        except Exception as e:
            logger.error(f"❌ 重複検出エラー: {e}")
            return []

    async def _find_exact_duplicates(
        self, analyzed_files: List[Dict[str, Any]]
    ) -> List[List[str]]:
        """完全一致検出"""
        hash_groups = {}

        for file_analysis in analyzed_files:
            if "error" in file_analysis:
                continue

            content_hash = file_analysis.get("content_hash")
            file_path = file_analysis["basic_info"]["relative_path"]

            if content_hash:
                if content_hash not in hash_groups:
                    hash_groups[content_hash] = []
                hash_groups[content_hash].append(file_path)

        # 2つ以上のファイルを持つグループのみ返す
        return [group for group in hash_groups.values() if len(group) > 1]

    async def _find_similar_content(
        self, analyzed_files: List[Dict[str, Any]]
    ) -> List[List[str]]:
        """類似コンテンツ検出"""
        # 簡略化実装：タイトルと構造の類似性で判定
        title_groups = {}

        for file_analysis in analyzed_files:
            if "error" in file_analysis:
                continue

            content_analysis = file_analysis.get("content_analysis", {})
            main_title = content_analysis.get("main_title", "")
            file_path = file_analysis["basic_info"]["relative_path"]

            if main_title:
                # タイトルの正規化
                normalized_title = re.sub(r"[^\w\s]", "", main_title.lower()).strip()

                if normalized_title:
                    if normalized_title not in title_groups:
                        title_groups[normalized_title] = []
                    title_groups[normalized_title].append(file_path)

        # 2つ以上のファイルを持つグループのみ返す
        return [group for group in title_groups.values() if len(group) > 1]

class MigrationEngine:
    """メイン移行エンジン"""

    def __init__(self, source_directory: Optional[Path] = None):
        """初期化"""
        self.source_directory = source_directory or PROJECT_ROOT / "knowledge_base"
        self.database = GrimoireDatabase()
        self.search_engine = GrimoireVectorSearch()
        self.four_sages = FourSagesReviewer()
        self.analyzer = MDFileAnalyzer()
        self.duplicate_detector = DuplicateDetector()

        # 設定
        self.batch_size = 50
        self.concurrent_limit = 10

        # 統計
        self.total_files_found = 0
        self.total_files_processed = 0
        self.successful_migrations = 0
        self.failed_migrations = 0
        self.skipped_files = 0
        self.duplicate_files = 0

        logger.info("🚀 Migration Engine initialized")

    async def initialize(self) -> bool:
        """システム初期化"""
        try:
            await self.database.initialize()
            await self.search_engine.initialize()

            logger.info("✅ Migration Engine ready")
            return True

        except Exception as e:
            logger.error(f"❌ Migration Engine initialization failed: {e}")
            return False

    async def run_full_migration(self) -> Dict[str, Any]migration_start = datetime.now(timezone.utc)migration_id = f"migration_{migration_start.strftime('%Y%m%d_%H%M%S')}"
    """全移行実行"""
:
        logger.info(f"🏛️ 完全移行開始: {migration_id}")

        try:
            # Phase 1: ファイル発見
            md_files = await self._discover_md_files()
            self.total_files_found = len(md_files)
            logger.info(f"📋 発見されたMDファイル: {self.total_files_found}個")

            # Phase 2: ファイル分析
            logger.info("🔍 Phase 2: ファイル分析開始")
            analyzed_files = await self._analyze_files_batch(md_files)

            # Phase 3: 重複検出
            logger.info("🔍 Phase 3: 重複検出開始")
            duplicate_groups = await self.duplicate_detector.detect_duplicates(
                analyzed_files
            )

            # Phase 4: 4賢者分類
            logger.info("🧙‍♂️ Phase 4: 4賢者分類開始")
            classified_files = await self._classify_with_four_sages(analyzed_files)

            # Phase 5: 重複処理戦略決定
            deduplication_plan = await self._create_deduplication_plan(
                duplicate_groups, classified_files
            )

            # Phase 6: バッチ移行実行
            logger.info("🚀 Phase 6: バッチ移行実行開始")
            migration_results = await self._execute_migration_batches(
                classified_files, deduplication_plan
            )

            # Phase 7: 統計レポート生成
            migration_end = datetime.now(timezone.utc)
            final_report = await self._generate_migration_report(
                migration_id,
                migration_start,
                migration_end,
                migration_results,
                duplicate_groups,
            )

            logger.info(f"✅ 完全移行完了: {migration_id}")
            return final_report

        except Exception as e:
            logger.error(f"❌ 完全移行エラー: {e}")
            return {
                "migration_id": migration_id,
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now(timezone.utc),
            }

    async def _discover_md_files(self) -> List[Path]:
        """MDファイル発見"""
        md_files = []

        try:
            # knowledge_base配下のすべての.mdファイルを検索
            for md_file in self.source_directory.rglob("*.md"):
                if md_file.is_file():
                    md_files.append(md_file)

            # ソート（一貫した順序で処理）
            md_files.sort(key=lambda x: str(x))

            logger.info(f"📂 MDファイル発見: {len(md_files)}個")
            return md_files

        except Exception as e:
            logger.error(f"❌ ファイル発見エラー: {e}")
            return []

    async def _analyze_files_batch(self, md_files: List[Path]) -> List[Dict[str, Any]]:
        """ファイル分析バッチ処理"""
        analyzed_files = []

        # セマフォで同時実行数制限
        semaphore = asyncio.Semaphore(self.concurrent_limit)

        async def analyze_single_file(file_pathPath) -> Dict[str, Any]:
    """analyze_single_file分析メソッド"""
            async with semaphore:
                analysis = await self.analyzer.analyze_file(file_path)
                analysis["file_path"] = str(file_path)
                return analysis

        # 並列分析実行
        tasks = [analyze_single_file(md_file) for md_file in md_files]
        analyzed_files = await asyncio.gather(*tasks, return_exceptions=True)

        # 例外処理
        valid_analyses = []
        for i, result in enumerate(analyzed_files):
            if isinstance(result, Exception):
                logger.error(f"❌ ファイル分析失敗 {md_files[i]}: {result}")
            else:
                valid_analyses.append(result)

        logger.info(f"✅ ファイル分析完了: {len(valid_analyses)}/{len(md_files)}個")
        return valid_analyses

    async def _classify_with_four_sages(
        self, analyzed_files: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """4賢者による分類"""
        classified_files = []

        for file_analysis in analyzed_files:
            if "error" in file_analysis:
                classified_files.append(file_analysis)
                continue

            try:
                # 4賢者による追加分析
                sage_classification = await self._get_sage_classification(file_analysis)
                file_analysis["sage_classification"] = sage_classification
                classified_files.append(file_analysis)

            except Exception as e:
                logger.error(
                    f"❌ 4賢者分類エラー {file_analysis.get('file_path', 'unknown')}: {e}"
                )
                file_analysis["sage_classification_error"] = str(e)
                classified_files.append(file_analysis)

        logger.info(f"🧙‍♂️ 4賢者分類完了: {len(classified_files)}個")
        return classified_files

    async def _get_sage_classification(
        self, file_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """4賢者分類取得"""
        # 簡略化実装：分析結果ベースで分類
        classification = file_analysis.get("classification", {})
        aicompany_analysis = file_analysis.get("aicompany_analysis", {})

        # 各賢者の観点での評価
        sage_scores = {
            "knowledge_sage": self._calculate_knowledge_score(file_analysis),
            "task_oracle": self._calculate_task_score(file_analysis),
            "crisis_sage": self._calculate_crisis_score(file_analysis),
            "search_mystic": self._calculate_search_score(file_analysis),
        }

        # 主担当賢者決定
        primary_sage = max(sage_scores.items(), key=lambda x: x[1])[0]

        return {
            "primary_sage": primary_sage,
            "sage_scores": sage_scores,
            "final_classification": classification,
            "ai_company_relevance": aicompany_analysis.get("sage_relevance_score", 0.0),
        }

    def _calculate_knowledge_score(self, file_analysis: Dict[str, Any]) -> float:
        """ナレッジ賢者スコア計算"""
        score = 0.5  # ベース

        content_analysis = file_analysis.get("content_analysis", {})
        aicompany_analysis = file_analysis.get("aicompany_analysis", {})

        # 知識的コンテンツ
        if content_analysis.get("headers", 0) > 3:
            score += 0.1
        if content_analysis.get("lists", 0) > 5:
            score += 0.1
        if content_analysis.get("links", 0) > 3:
            score += 0.1

        # Elders Guild知識
        if aicompany_analysis.get("sage_references", 0) > 0:
            score += 0.2

        return min(score, 1.0)

    def _calculate_task_score(self, file_analysis: Dict[str, Any]) -> float:
        """タスク賢者スコア計算"""
        score = 0.1  # ベース

        aicompany_analysis = file_analysis.get("aicompany_analysis", {})
        basic_info = file_analysis.get("basic_info", {})

        # タスク関連コンテンツ
        if aicompany_analysis.get("workflow_content", 0) > 0:
            score += 0.3
        if "task" in basic_info.get("file_name", "").lower():
            score += 0.2
        if aicompany_analysis.get("technical_commands", 0) > 2:
            score += 0.2

        return min(score, 1.0)

    def _calculate_crisis_score(self, file_analysis: Dict[str, Any]) -> float:
        """インシデント賢者スコア計算"""
        score = 0.1  # ベース

        aicompany_analysis = file_analysis.get("aicompany_analysis", {})
        basic_info = file_analysis.get("basic_info", {})

        # インシデント関連コンテンツ
        if aicompany_analysis.get("incident_content", 0) > 0:
            score += 0.4
        if any(
            keyword in basic_info.get("file_name", "").lower()
            for keyword in ["error", "fix", "trouble", "incident"]
        ):
            score += 0.3

        return min(score, 1.0)

    def _calculate_search_score(self, file_analysis: Dict[str, Any]) -> float:
        """RAG賢者スコア計算"""
        score = 0.2  # ベース

        content_analysis = file_analysis.get("content_analysis", {})
        basic_info = file_analysis.get("basic_info", {})

        # 検索・発見可能性
        if content_analysis.get("links", 0) > 5:
            score += 0.2
        if basic_info.get("word_count", 0) > 1000:
            score += 0.1
        if content_analysis.get("technical_density", 0) > 0.3:
            score += 0.2

        return min(score, 1.0)

    async def _create_deduplication_plan(
        self, duplicate_groups: List[List[str]], classified_files: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """重複除去計画作成"""
        plan = {
            "duplicate_groups": duplicate_groups,
            "merge_candidates": [],
            "skip_duplicates": [],
            "manual_review_required": [],
        }

        # ファイル情報マップ作成
        file_info_map = {}
        for file_analysis in classified_files:
            if "error" not in file_analysis:
                file_path = file_analysis.get("file_path", "")
                basic_info = file_analysis.get("basic_info", {})
                file_info_map[basic_info.get("relative_path", file_path)] = (
                    file_analysis
                )

        # 重複グループごとの処理計画
        for group in duplicate_groups:
            if len(group) < 2:
                continue

            # グループ内でのマスターファイル決定
            master_candidate = await self._select_master_file(group, file_info_map)

            group_plan = {
                "files": group,
                "master_file": master_candidate,
                "action": "merge" if len(group) <= 3 else "manual_review",
            }

            if group_plan["action"] == "merge":
                plan["merge_candidates"].append(group_plan)
            else:
                plan["manual_review_required"].append(group_plan)

        logger.info(
            f"📋 重複除去計画作成完了: {len(plan['merge_candidates'])}個の自動統合, "
            f"{len(plan['manual_review_required'])}個の手動レビュー"
        )

        return plan

    async def _select_master_file(
        self, duplicate_group: List[str], file_info_map: Dict[str, Any]
    ) -> str:
        """マスターファイル選定"""
        scored_files = []

        for file_path in duplicate_group:
            file_info = file_info_map.get(file_path)
            if not file_info:
                continue

            score = 0
            basic_info = file_info.get("basic_info", {})
            classification = file_info.get("classification", {})

            # スコアリング基準
            score += basic_info.get("char_count", 0) / 1000  # サイズ
            score += classification.get("power_level", 1)  # 威力レベル
            score += classification.get("confidence_score", 0) * 10  # 信頼度

            # ファイル名による優先度
            file_name = basic_info.get("file_name", "").lower()
            if "claude" in file_name:
                score += 5
            if "guide" in file_name:
                score += 3
            if "readme" in file_name:
                score += 4

            scored_files.append((file_path, score))

        # 最高スコアのファイルを選択
        if scored_files:
            return max(scored_files, key=lambda x: x[1])[0]
        else:
            return duplicate_group[0]  # フォールバック

    async def _execute_migration_batches(
        self, classified_files: List[Dict[str, Any]], deduplication_plan: Dict[str, Any]
    ) -> List[MigrationResult]:
        """バッチ移行実行"""
        migration_results = []

        # スキップファイル設定
        skip_files = set()
        for group_plan in deduplication_plan.get("merge_candidates", []):
            master_file = group_plan["master_file"]
            for file_path in group_plan["files"]:
                if file_path != master_file:
                    skip_files.add(file_path)

        # バッチ処理
        for i in range(0, len(classified_files), self.batch_size):
            batch = classified_files[i : i + self.batch_size]
            batch_id = f"batch_{i//self.batch_size + 1}"

            logger.info(f"🚀 バッチ{batch_id}処理開始: {len(batch)}ファイル")

            batch_results = await self._process_migration_batch(
                batch, skip_files, batch_id
            )
            migration_results.extend(batch_results)

            # バッチ間の休憩
            await asyncio.sleep(0.1)

        return migration_results

    async def _process_migration_batch(
        self, batch: List[Dict[str, Any]], skip_files: Set[str], batch_id: str
    ) -> List[MigrationResult]:
        """単一バッチ処理"""
        batch_results = []

        for file_analysis in batch:
            result = await self._migrate_single_file(file_analysis, skip_files)
            batch_results.append(result)

            # 統計更新
            self.total_files_processed += 1
            if result.status == MigrationStatus.COMPLETED:
                self.successful_migrations += 1
            elif result.status == MigrationStatus.FAILED:
                self.failed_migrations += 1
            elif result.status == MigrationStatus.SKIPPED:
                self.skipped_files += 1

        logger.info(f"✅ バッチ{batch_id}完了: {len(batch_results)}ファイル処理")
        return batch_results

    async def _migrate_single_file(
        self, file_analysis: Dict[str, Any], skip_files: Set[str]
    ) -> MigrationResult:
        """単一ファイル移行"""
        file_path = file_analysis.get("file_path", "")

        try:
            # エラーファイルのスキップ
            if "error" in file_analysis:
                return MigrationResult(
                    file_path=file_path,
                    status=MigrationStatus.FAILED,
                    error_message=file_analysis["error"],
                )

            basic_info = file_analysis.get("basic_info", {})
            relative_path = basic_info.get("relative_path", file_path)

            # 重複ファイルのスキップ
            if relative_path in skip_files:
                return MigrationResult(
                    file_path=file_path,
                    status=MigrationStatus.SKIPPED,
                    error_message="Duplicate file - skipped in favor of master",
                )

            # 呪文データ構築
            spell_data = await self._build_spell_data(file_analysis)

            # データベースに保存・インデックス化
            spell_id = str(uuid.uuid4())
            await self.search_engine.index_spell(spell_id, spell_data)

            return MigrationResult(
                file_path=file_path,
                status=MigrationStatus.COMPLETED,
                spell_id=spell_id,
                original_hash=file_analysis.get("content_hash"),
                migration_timestamp=datetime.now(timezone.utc),
                metadata=spell_data,
                sage_classification=file_analysis.get("sage_classification"),
            )

        except Exception as e:
            logger.error(f"❌ ファイル移行エラー {file_path}: {e}")
            return MigrationResult(
                file_path=file_path, status=MigrationStatus.FAILED, error_message=str(e)
            )

    async def _build_spell_data(self, file_analysis: Dict[str, Any]) -> Dict[str, Any]basic_info = file_analysis.get("basic_info", {})classification = file_analysis.get("classification", {})
    """文データ構築"""
        sage_classification = file_analysis.get("sage_classification", {})

        # ファイル内容読み込み
        file_path = Path(file_analysis["file_path"])
        content = file_path.read_text(encoding="utf-8")

        # スペルデータ構築 - Enum処理を安全に
        spell_type = classification.get("spell_type", SpellType.KNOWLEDGE)
        spell_type_value = (
            spell_type.value if hasattr(spell_type, "value") else str(spell_type)
        )

        spell_data = {:
            "spell_name": self._generate_spell_name(basic_info, classification),
            "content": content,
            "spell_type": spell_type_value,
            "magic_school": sage_classification.get("primary_sage", "knowledge_sage"),
            "tags": classification.get("suggested_tags", []),
            "power_level": classification.get("power_level", 1),
            "is_eternal": classification.get("is_eternal", False),
            "casting_frequency": 0,  # 初期値
            "original_file_path": basic_info.get("relative_path", ""),
            "migration_metadata": {
                "migrated_at": datetime.now(timezone.utc).isoformat(),
                "original_size": basic_info.get("file_size", 0),
                "confidence_score": classification.get("confidence_score", 0.5),
                "sage_scores": sage_classification.get("sage_scores", {}),
                "ai_company_relevance": sage_classification.get(
                    "ai_company_relevance", 0.0
                ),
            },
        }

        return spell_data

    def _generate_spell_name(
        self, basic_info: Dict[str, Any], classification: Dict[str, Any]
    ) -> str:
        """呪文名生成"""
        file_name = basic_info.get("file_name", "unknown.md")

        # 拡張子除去
        spell_name = Path(file_name).stem

        # 読みやすく整形
        spell_name = spell_name.replace("_", " ").replace("-", " ")
        spell_name = " ".join(word.capitalize() for word in spell_name.split())

        # Elders Guild固有の調整
        if "claude" in spell_name.lower():
            spell_name = spell_name.replace("Claude", "🤖 Claude")
        if "tdd" in spell_name.lower():
            spell_name = spell_name.replace("TDD", "🧪 TDD")
        if "guide" in spell_name.lower():
            spell_name = f"📖 {spell_name}"

        return spell_name

    async def _generate_migration_report(
        self,
        migration_id: str,
        start_time: datetime,
        end_time: datetime,
        migration_results: List[MigrationResult],
        duplicate_groups: List[List[str]],
    ) -> Dict[str, Any]:
        """移行レポート生成"""
        duration = end_time - start_time

        # ステータス別統計
        status_counts = {}
        for status in MigrationStatus:
            status_counts[status.value] = sum(
                1 for r in migration_results if r.status == status
            )

        # 成功率計算
        success_rate = (
            status_counts.get("completed", 0) / max(len(migration_results), 1)
        ) * 100

        # 賢者別統計
        sage_distribution = {}
        for result in migration_results:
            if result.sage_classification:
                primary_sage = result.sage_classification.get("primary_sage", "unknown")
                sage_distribution[primary_sage] = (
                    sage_distribution.get(primary_sage, 0) + 1
                )

        report = {
            "migration_id": migration_id,
            "status": "completed",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "summary": {
                "total_files_discovered": self.total_files_found,
                "total_files_processed": len(migration_results),
                "successful_migrations": status_counts.get("completed", 0),
                "failed_migrations": status_counts.get("failed", 0),
                "skipped_files": status_counts.get("skipped", 0),
                "success_rate_percent": round(success_rate, 2),
            },
            "status_breakdown": status_counts,
            "sage_distribution": sage_distribution,
            "duplicate_detection": {
                "total_duplicate_groups": len(duplicate_groups),
                "total_duplicate_files": sum(len(group) for group in duplicate_groups),
            },
            "migration_results": [asdict(result) for result in migration_results],
        }

        # レポートファイル保存
        report_path = PROJECT_ROOT / f"migration_reports/{migration_id}_report.json"
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"📊 移行レポート保存: {report_path}")
        logger.info(
            f"✅ 移行完了: {status_counts.get('completed', 0)}/{len(migration_results)}ファイル "
            f"(成功率: {success_rate:0.1f}%)"
        )

        return report

    async def close(self)await self.database.close()
    """リソースクローズ"""
        logger.info("🏛️ Migration Engine closed")

# 使用例とテスト用関数
async def test_migration_engine()migration_engine = MigrationEngine()
"""テスト実行"""

    try:
        await migration_engine.initialize()

        # サンプル移行実行
        report = await migration_engine.run_full_migration()

        print(f"✅ 移行テスト完了")
        print(f"📊 成功: {report['summary']['successful_migrations']}ファイル")
        print(f"❌ 失敗: {report['summary']['failed_migrations']}ファイル")
        print(f"⏭️ スキップ: {report['summary']['skipped_files']}ファイル")
        print(f"📈 成功率: {report['summary']['success_rate_percent']}%")

    finally:
        await migration_engine.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_migration_engine())
