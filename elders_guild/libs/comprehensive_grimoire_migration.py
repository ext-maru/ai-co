#!/usr/bin/env python3
"""
Comprehensive Grimoire Migration System
全エルダーズ魔法書統合移行システム

514個のMDファイルをPostgreSQL + pgvectorシステムに移行し、
4賢者の魔法書を完全統合する包括的移行システム
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
import hashlib
import json
import logging
import os
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import aiofiles
except ImportError:
    aiofiles = None

from libs.grimoire_database import (
    GrimoireDatabase,
    MagicSchool,
    SpellMetadata,
    SpellType,
)
from libs.grimoire_spell_evolution import EvolutionEngine, EvolutionType
from libs.grimoire_vector_search import GrimoireVectorSearch, SearchQuery
from libs.rag_grimoire_integration import RagGrimoireConfig, RagGrimoireIntegration
from libs.task_sage_grimoire_vectorization import TaskSageGrimoireVectorization

logger = logging.getLogger(__name__)

@dataclass
class FileAnalysis:
    """ファイル分析結果"""

    file_path: str
    relative_path: str
    file_name: str
    content: str
    size: int
    checksum: str

    # メタデータ分析
    spell_name: str
    suggested_spell_type: SpellType
    suggested_magic_school: MagicSchool
    suggested_power_level: int
    extracted_tags: List[str]

    # 重複分析
    similarity_candidates: List[str] = field(default_factory=list)
    is_duplicate: bool = False
    merge_target: Optional[str] = None

    # 品質分析
    content_quality_score: float = 0
    technical_complexity: float = 0
    importance_score: float = 0

@dataclass
class MigrationBatch:
    """移行バッチ"""

    batch_id: str
    files: List[FileAnalysis]
    priority: str  # HIGH, MEDIUM, LOW
    estimated_time: float  # 推定移行時間（分）
    dependencies: List[str] = field(default_factory=list)

@dataclass
class MigrationResult:
    """移行結果"""

    batch_id: str
    total_files: int
    successful: int
    failed: int
    skipped: int

    successful_spells: List[str] = field(default_factory=list)
    failed_files: List[Dict[str, str]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    start_time: datetime = None
    end_time: datetime = None
    duration_seconds: float = 0

class ContentAnalyzer:
    """コンテンツ分析・分類システム"""

    def __init__(self):
        """初期化メソッド"""
        self.logger = logging.getLogger(__name__)

        # 4賢者分類キーワード
        self.magic_school_keywords = {
            MagicSchool.KNOWLEDGE_SAGE: [
                "knowledge",
                "learn",
                "pattern",
                "insight",
                "wisdom",
                "analysis",
                "study",
                "research",
                "understanding",
                "concept",
                "theory",
            ],
            MagicSchool.TASK_ORACLE: [
                "task",
                "workflow",
                "process",
                "procedure",
                "step",
                "execution",
                "schedule",
                "priority",
                "planning",
                "project",
                "management",
            ],
            MagicSchool.CRISIS_SAGE: [
                "error",
                "incident",
                "problem",
                "issue",

                "failure",
                "emergency",
                "crisis",
                "recovery",
                "fix",
                "troubleshoot",

            ],
            MagicSchool.SEARCH_MYSTIC: [
                "search",
                "query",
                "retrieval",
                "find",
                "lookup",
                "index",
                "semantic",
                "context",
                "similarity",
                "match",
                "relevance",
            ],
        }

        # スペルタイプキーワード
        self.spell_type_keywords = {
            SpellType.KNOWLEDGE: [
                "guide",
                "concept",
                "theory",
                "principle",
                "overview",
                "introduction",
            ],
            SpellType.PROCEDURE: [
                "how to",
                "steps",
                "procedure",
                "process",
                "workflow",
                "method",
            ],
            SpellType.CONFIGURATION: [
                "config",
                "setting",
                "parameter",
                "option",
                "environment",
                "setup",
            ],

                "example",
                "sample",
                "boilerplate",
                "scaffold",
            ],
            SpellType.REFERENCE: [
                "reference",
                "api",
                "documentation",
                "spec",
                "manual",
                "list",
            ],
        }

    def analyze_file(self, file_path: str) -> FileAnalysis:
        """ファイル完全分析"""
        try:
            path_obj = Path(file_path)

            # ファイル読み込み
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 基本情報
            checksum = hashlib.sha256(content.encode()).hexdigest()
            size = len(content.encode())

            # メタデータ抽出
            spell_name = self._extract_spell_name(path_obj, content)
            spell_type = self._detect_spell_type(content, path_obj.name)
            magic_school = self._infer_magic_school(content, path_obj)
            power_level = self._calculate_power_level(content, path_obj)
            tags = self._extract_tags(content, path_obj)

            # 品質分析
            quality_score = self._assess_content_quality(content)
            complexity = self._assess_technical_complexity(content)
            importance = self._assess_importance(content, path_obj)

            return FileAnalysis(
                file_path=str(file_path),
                relative_path=str(path_obj.relative_to(Path.cwd())),
                file_name=path_obj.name,
                content=content,
                size=size,
                checksum=checksum,
                spell_name=spell_name,
                suggested_spell_type=spell_type,
                suggested_magic_school=magic_school,
                suggested_power_level=power_level,
                extracted_tags=tags,
                content_quality_score=quality_score,
                technical_complexity=complexity,
                importance_score=importance,
            )

        except Exception as e:
            self.logger.error(f"File analysis failed: {file_path} - {e}")
            raise

    def _extract_spell_name(self, path_obj: Path, content: str) -> str:
        """スペル名抽出"""
        # ファイルの最初のH1見出しを探す
        h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()

        # ファイル名から生成
        name = path_obj.stem
        name = re.sub(r"[_-]", " ", name)
        return name.title()

    def _detect_spell_type(self, content: str, filename: str) -> SpellType:
        """スペルタイプ検出"""
        content_lower = content.lower()
        filename_lower = filename.lower()

        scores = {}
        for spell_type, keywords in self.spell_type_keywords.items():
            score = 0
            for keyword in keywords:
                score += content_lower.count(keyword)
                if keyword in filename_lower:
                    score += 5  # ファイル名に含まれる場合は重み付け
            scores[spell_type] = score

        # 最高スコアのタイプを返す
        return max(scores, key=scores.get) if scores else SpellType.KNOWLEDGE

    def _infer_magic_school(self, content: str, path_obj: Path) -> MagicSchool:
        """魔法学派推定"""
        content_lower = content.lower()
        path_lower = str(path_obj).lower()

        scores = {}
        for school, keywords in self.magic_school_keywords.items():
            score = 0
            for keyword in keywords:
                # コンテンツ内出現回数
                score += content_lower.count(keyword)
                # パス内出現の重み付け
                if keyword in path_lower:
                    score += 10
            scores[school] = score

        # パス解析による追加判定
        if "task" in path_lower or "workflow" in path_lower:
            scores[MagicSchool.TASK_ORACLE] += 20

            scores[MagicSchool.CRISIS_SAGE] += 20
        elif "search" in path_lower or "rag" in path_lower:
            scores[MagicSchool.SEARCH_MYSTIC] += 20
        elif "knowledge" in path_lower or "guide" in path_lower:
            scores[MagicSchool.KNOWLEDGE_SAGE] += 20

        return max(scores, key=scores.get) if scores else MagicSchool.KNOWLEDGE_SAGE

    def _calculate_power_level(self, content: str, path_obj: Path) -> int:
        """パワーレベル計算 (1-10)"""
        score = 5  # ベース値

        # ファイルサイズ
        size = len(content)
        if size > 10000:
            score += 2
        elif size > 5000:
            score += 1
        elif size < 1000:
            score -= 1

        # 重要キーワード
        important_keywords = [
            "important",
            "critical",
            "essential",
            "main",
            "core",
            "primary",
            "master",
            "guide",
            "overview",
            "architecture",
            "design",
        ]
        content_lower = content.lower()
        for keyword in important_keywords:
            if keyword in content_lower:
                score += 1

        # パス解析
        path_lower = str(path_obj).lower()
        if "readme" in path_lower or "main" in path_lower:
            score += 2
        elif "claude" in path_lower:
            score += 3  # Claudeに関連するファイルは重要

            score -= 2

        # 見出しの数（構造化度）
        h1_count = len(re.findall(r"^#\s+", content, re.MULTILINE))
        h2_count = len(re.findall(r"^##\s+", content, re.MULTILINE))
        if h1_count > 0 and h2_count > 3:
            score += 1

        return max(1, min(10, score))

    def _extract_tags(self, content: str, path_obj: Path) -> List[str]:
        """タグ抽出"""
        tags = set()

        # パスからタグ抽出
        path_parts = path_obj.parts
        for part in path_parts:
            if part not in [".", "..", "home", "aicompany", "ai_co"]:
                tags.add(part.lower())

        # ファイルタイプ
        if path_obj.suffix == ".md":
            tags.add("markdown")

        # コンテンツからキーワード抽出
        content_lower = content.lower()
        keyword_patterns = [
            r"(?:^|\s)(tdd|test[\s-]?driven[\s-]?development)(?:\s|$)",
            r"(?:^|\s)(api|rest|graphql)(?:\s|$)",
            r"(?:^|\s)(docker|container)(?:\s|$)",
            r"(?:^|\s)(postgres|postgresql|database)(?:\s|$)",
            r"(?:^|\s)(python|javascript|typescript)(?:\s|$)",
            r"(?:^|\s)(claude|ai|llm)(?:\s|$)",
        ]

        for pattern in keyword_patterns:
            matches = re.findall(pattern, content_lower, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    tags.add(match[0])
                else:
                    tags.add(match)

        return sorted(list(tags))

    def _assess_content_quality(self, content: str) -> float:
        """コンテンツ品質評価 (0-1)"""
        score = 0

        # 基本構造
        if re.search(r"^#\s+", content, re.MULTILINE):  # H1見出しあり
            score += 0.2
        if re.search(r"^##\s+", content, re.MULTILINE):  # H2見出しあり
            score += 0.1

        # コードブロック
        if "```" in content:
            score += 0.2

        # リスト構造
        if re.search(r"^\s*[-*+]\s+", content, re.MULTILINE):
            score += 0.1

        # 適切な長さ
        length = len(content)
        if 500 <= length <= 10000:
            score += 0.2
        elif length > 100:
            score += 0.1

        # 改行・段落構造
        paragraphs = content.split("\n\n")
        if len(paragraphs) > 2:
            score += 0.1

        # リンク
        if "[" in content and "]" in content:
            score += 0.1

        return min(1, score)

    def _assess_technical_complexity(self, content: str) -> float:
        """技術的複雑性評価 (0-1)"""
        score = 0
        content_lower = content.lower()

        # 技術用語の密度
        technical_terms = [
            "algorithm",
            "architecture",
            "async",
            "await",
            "class",
            "function",
            "implementation",
            "interface",
            "method",
            "module",
            "object",
            "parameter",
            "protocol",
            "schema",
            "system",
            "vector",
            "database",
        ]

        term_count = sum(content_lower.count(term) for term in technical_terms)
        term_density = term_count / max(len(content.split()), 1)
        score += min(0.4, term_density * 10)

        # コードブロックの複雑さ
        code_blocks = re.findall(r"```[\s\S]*?```", content)
        if code_blocks:
            avg_code_length = sum(len(block) for block in code_blocks) / len(
                code_blocks
            )
            score += min(0.3, avg_code_length / 1000)

        # JSONやYAMLの存在
        if "{" in content and "}" in content:
            score += 0.1
        if ":" in content and re.search(r"^\s*\w+:", content, re.MULTILINE):
            score += 0.1

        # 複雑な構造
        nesting_level = max(line.count("  ") for line in content.split("\n"))
        score += min(0.1, nesting_level / 20)

        return min(1, score)

    def _assess_importance(self, content: str, path_obj: Path) -> float:
        """重要度評価 (0-1)"""
        score = 0

        # パス解析
        path_lower = str(path_obj).lower()

        # 重要ファイル
        important_files = ["readme", "claude", "main", "index", "getting_started"]
        for important in important_files:
            if important in path_lower:
                score += 0.3
                break

        # 重要ディレクトリ
        if "knowledge_base" in path_lower:
            score += 0.2
        elif "docs" in path_lower:
            score += 0.1

            score -= 0.2

        # コンテンツ解析
        content_lower = content.lower()
        importance_indicators = [
            "important",
            "critical",
            "essential",
            "required",
            "mandatory",
            "architecture",
            "design",
            "specification",
            "standard",
        ]

        for indicator in importance_indicators:
            if indicator in content_lower:
                score += 0.1

        # ファイルサイズ（適度な情報量）
        size = len(content)
        if 1000 <= size <= 20000:
            score += 0.1

        return max(0, min(1, score))

class DuplicateDetector:
    """重複・類似コンテンツ検出システム"""

    def __init__(self):
        """初期化メソッド"""
        self.logger = logging.getLogger(__name__)
        self.similarity_threshold = 0.8

    def detect_duplicates(self, analyses: List[FileAnalysis]) -> List[FileAnalysis]:
        """重複検出と統合候補特定"""
        self.logger.info(f"Analyzing {len(analyses)} files for duplicates...")

        # 簡単な重複検出（チェックサム）
        checksum_groups = {}
        for analysis in analyses:
            if analysis.checksum in checksum_groups:
                checksum_groups[analysis.checksum].append(analysis)
            else:
                checksum_groups[analysis.checksum] = [analysis]

        # 重複をマーク
        for checksum, group in checksum_groups.items():
            if len(group) > 1:
                # 最も重要なファイルを残し、他を重複マーク
                group.sort(key=lambda x: x.importance_score, reverse=True)
                primary = group[0]

                for duplicate in group[1:]:
                    duplicate.is_duplicate = True
                    duplicate.merge_target = primary.file_path
                    primary.similarity_candidates.append(duplicate.file_path)

        # 内容類似性検出（簡略版）
        self._detect_content_similarity(analyses)

        duplicates_count = sum(1 for a in analyses if a.is_duplicate)
        self.logger.info(f"Found {duplicates_count} duplicates")

        return analyses

    def _detect_content_similarity(self, analyses: List[FileAnalysis]):
        """コンテンツ類似性検出"""
        # 簡単な類似性検出（単語重複率）
        for i, analysis1 in enumerate(analyses):
            if analysis1is_duplicate:
                continue

            words1 = set(analysis1content.lower().split())

            for analysis2 in analyses[i + 1 :]:
                if analysis2is_duplicate:
                    continue

                words2 = set(analysis2content.lower().split())

                if not words1 or not words2:
                    continue

                # Jaccard係数計算
                intersection = words1.intersection(words2)
                union = words1.union(words2)
                similarity = len(intersection) / len(union) if union else 0

                if similarity > self.similarity_threshold:
                    # より重要度の低い方を重複とマーク
                    if analysis1importance_score >= analysis2importance_score:
                        analysis2is_duplicate = True
                        analysis2merge_target = analysis1file_path
                        analysis1similarity_candidates.append(analysis2file_path)
                    else:
                        analysis1is_duplicate = True
                        analysis1merge_target = analysis2file_path
                        analysis2similarity_candidates.append(analysis1file_path)

class ComprehensiveGrimoireMigration:
    """包括的魔法書移行システム"""

    def __init__(self, database_url: Optional[str] = None):
        """初期化メソッド"""
        self.database_url = database_url or os.getenv(
            "GRIMOIRE_DATABASE_URL",
            "postgresql://aicompany@localhost:5432/ai_company_grimoire",
        )
        self.logger = logging.getLogger(__name__)

        # コンポーネント
        self.grimoire_db = None
        self.vector_search = None
        self.evolution_engine = None
        self.task_sage = None
        self.rag_integration = None

        # 分析システム
        self.content_analyzer = ContentAnalyzer()
        self.duplicate_detector = DuplicateDetector()

        # 移行統計
        self.migration_stats = {
            "total_files_found": 0,
            "files_analyzed": 0,
            "duplicates_detected": 0,
            "batches_created": 0,
            "files_migrated": 0,
            "migration_failures": 0,
            "start_time": None,
            "end_time": None,
        }

        # 設定
        self.batch_size = 50
        self.max_concurrent_migrations = 5

    async def initialize(self):
        """システム初期化"""
        try:
            self.logger.info("Initializing Comprehensive Grimoire Migration System...")

            # 魔法書データベース
            self.grimoire_db = GrimoireDatabase(self.database_url)
            await self.grimoire_db.initialize()

            # ベクトル検索
            self.vector_search = GrimoireVectorSearch(database=self.grimoire_db)
            await self.vector_search.initialize()

            # 進化エンジン
            self.evolution_engine = EvolutionEngine(database=self.grimoire_db)
            await self.evolution_engine.initialize()

            # タスク賢者ベクトル化システム
            self.task_sage = TaskSageGrimoireVectorization(self.database_url)
            await self.task_sage.initialize()

            # RAG統合システム
            config = RagGrimoireConfig(
                database_url=self.database_url, migration_mode=True
            )
            self.rag_integration = RagGrimoireIntegration(config)
            await self.rag_integration.initialize()

            self.logger.info("✅ Comprehensive Grimoire Migration System initialized")

        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            raise

    async def discover_files(self, root_path: str = ".") -> List[str]:
        """MDファイル発見"""
        self.logger.info(f"Discovering MD files in {root_path}...")

        md_files = []
        root_path_obj = Path(root_path)

        # 除外パターン
        exclude_patterns = [
            "**/.*",  # 隠しファイル
            "**/venv/**",
            "**/node_modules/**",
            "**/__pycache__/**",

            "**/tmp/**",
        ]

        for md_file in root_path_obj.rglob("*.md"):
            # 除外パターンチェック
            should_exclude = False
            for pattern in exclude_patterns:
                if md_file.match(pattern):
                    should_exclude = True
                    break

            if not should_exclude:
                md_files.append(str(md_file.absolute()))

        self.migration_stats["total_files_found"] = len(md_files)
        self.logger.info(f"Found {len(md_files)} MD files")

        return md_files

    async def analyze_files(self, file_paths: List[str]) -> List[FileAnalysis]:
        """ファイル一括分析"""
        self.logger.info(f"Analyzing {len(file_paths)} files...")

        analyses = []

        # 並行分析
        semaphore = asyncio.Semaphore(10)  # 同時分析数制限

        async def analyze_single_file(file_path: str) -> Optional[FileAnalysis]:
            """analyze_single_file分析メソッド"""
            async with semaphore:
                try:
                    # CPU集約的タスクなので同期実行
                    analysis = await asyncio.get_event_loop().run_in_executor(
                        None, self.content_analyzer.analyze_file, file_path
                    )
                    return analysis
                except Exception as e:
                    self.logger.error(f"Analysis failed for {file_path}: {e}")
                    return None

        # 並行実行
        tasks = [analyze_single_file(path) for path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 結果収集
        for result in results:
            if isinstance(result, FileAnalysis):
                analyses.append(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Analysis exception: {result}")

        self.migration_stats["files_analyzed"] = len(analyses)

        # 重複検出
        analyses = await asyncio.get_event_loop().run_in_executor(
            None, self.duplicate_detector.detect_duplicates, analyses
        )

        duplicates = sum(1 for a in analyses if a.is_duplicate)
        self.migration_stats["duplicates_detected"] = duplicates

        self.logger.info(
            f"Analysis complete: {len(analyses)} files, {duplicates} duplicates"
        )

        return analyses

    def create_migration_batches(
        self, analyses: List[FileAnalysis]
    ) -> List[MigrationBatch]:
        """移行バッチ作成"""
        self.logger.info("Creating migration batches...")

        # 重複を除外
        non_duplicates = [a for a in analyses if not a.is_duplicate]

        # 優先度別分類
        high_priority = []
        medium_priority = []
        low_priority = []

        for analysis in non_duplicates:
            if analysis.importance_score >= 0.7:
                high_priority.append(analysis)
            elif analysis.importance_score >= 0.4:
                medium_priority.append(analysis)
            else:
                low_priority.append(analysis)

        # バッチ作成
        batches = []

        # 高優先度バッチ
        for i in range(0, len(high_priority), self.batch_size):
            batch_files = high_priority[i : i + self.batch_size]
            batch = MigrationBatch(
                batch_id=f"high_priority_{i // self.batch_size + 1}",
                files=batch_files,
                priority="HIGH",
                estimated_time=len(batch_files) * 0.5,  # 30秒/ファイル
            )
            batches.append(batch)

        # 中優先度バッチ
        for i in range(0, len(medium_priority), self.batch_size):
            batch_files = medium_priority[i : i + self.batch_size]
            batch = MigrationBatch(
                batch_id=f"medium_priority_{i // self.batch_size + 1}",
                files=batch_files,
                priority="MEDIUM",
                estimated_time=len(batch_files) * 0.3,
            )
            batches.append(batch)

        # 低優先度バッチ
        for i in range(0, len(low_priority), self.batch_size):
            batch_files = low_priority[i : i + self.batch_size]
            batch = MigrationBatch(
                batch_id=f"low_priority_{i // self.batch_size + 1}",
                files=batch_files,
                priority="LOW",
                estimated_time=len(batch_files) * 0.2,
            )
            batches.append(batch)

        self.migration_stats["batches_created"] = len(batches)

        total_files = sum(len(batch.files) for batch in batches)
        total_time = sum(batch.estimated_time for batch in batches)

        self.logger.info(f"Created {len(batches)} batches for {total_files} files")
        self.logger.info(f"Estimated migration time: {total_time:0.1f} minutes")

        return batches

    async def migrate_batch(self, batch: MigrationBatch) -> MigrationResult:
        """バッチ移行実行"""
        result = MigrationResult(
            batch_id=batch.batch_id,
            total_files=len(batch.files),
            successful=0,
            failed=0,
            skipped=0,
            start_time=datetime.now(timezone.utc),
        )

        self.logger.info(
            f"Starting migration of batch {batch.batch_id} ({len(batch.files)} files)"
        )

        try:
            for analysis in batch.files:
                try:
                    # SpellMetadata作成
                    spell_metadata = SpellMetadata(
                        id=str(uuid.uuid4()),
                        spell_name=analysis.spell_name,
                        content=analysis.content,
                        spell_type=analysis.suggested_spell_type,
                        magic_school=analysis.suggested_magic_school,
                        tags=analysis.extracted_tags,
                        power_level=analysis.suggested_power_level,
                        casting_frequency=0,
                        last_cast_at=None,
                        is_eternal=analysis.importance_score >= 0.8,  # 高重要度は永続化
                        evolution_history=[],
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                        version=1,
                    )

                    # データベースに保存
                    spell_id = await self.grimoire_db.create_spell(spell_metadata)

                    # ベクトル検索インデックス追加
                    await self.vector_search.index_spell(spell_id, spell_metadata)

                    result.successful += 1
                    result.successful_spells.append(spell_id)

                        f"✅ Migrated: {analysis.file_name} -> {spell_id}"
                    )

                except Exception as e:
                    result.failed += 1
                    result.failed_files.append(
                        {"file": analysis.file_path, "error": str(e)}
                    )
                    self.logger.error(
                        f"❌ Migration failed: {analysis.file_name} - {e}"
                    )

            result.end_time = datetime.now(timezone.utc)
            result.duration_seconds = (
                result.end_time - result.start_time
            ).total_seconds()

            self.migration_stats["files_migrated"] += result.successful
            self.migration_stats["migration_failures"] += result.failed

            self.logger.info(
                f"Batch {batch.batch_id} complete: "
                f"{result.successful} successful, {result.failed} failed, "
                f"{result.duration_seconds:0.1f}s"
            )

        except Exception as e:
            self.logger.error(f"Batch migration failed: {batch.batch_id} - {e}")
            result.failed = len(batch.files)
            result.end_time = datetime.now(timezone.utc)
            result.duration_seconds = (
                result.end_time - result.start_time
            ).total_seconds()

        return result

    async def execute_full_migration(self, root_path: str = ".") -> Dict[str, Any]:
        """完全移行実行"""
        self.migration_stats["start_time"] = datetime.now(timezone.utc)

        try:
            self.logger.info("🏛️ Starting Comprehensive Grimoire Migration...")

            # 1 ファイル発見
            file_paths = await self.discover_files(root_path)

            if not file_paths:
                self.logger.warning("No MD files found")
                return {"error": "No MD files found"}

            # 2 ファイル分析
            analyses = await self.analyze_files(file_paths)

            # 3 バッチ作成
            batches = self.create_migration_batches(analyses)

            if not batches:
                self.logger.warning("No migration batches created")
                return {"error": "No migration batches created"}

            # 4 バッチ移行実行
            migration_results = []

            # セマフォアで同時実行数制御
            semaphore = asyncio.Semaphore(self.max_concurrent_migrations)

            async def migrate_single_batch(batch: MigrationBatch) -> MigrationResult:
                """migrate_single_batchメソッド"""
                async with semaphore:
                    return await self.migrate_batch(batch)

            # 優先度順に実行
            high_priority_batches = [b for b in batches if b.priority == "HIGH"]
            medium_priority_batches = [b for b in batches if b.priority == "MEDIUM"]
            low_priority_batches = [b for b in batches if b.priority == "LOW"]

            # 高優先度を先に実行
            if high_priority_batches:
                self.logger.info(
                    f"Migrating {len(high_priority_batches)} high priority batches..."
                )
                high_results = await asyncio.gather(
                    *[migrate_single_batch(batch) for batch in high_priority_batches]
                )
                migration_results.extend(high_results)

            # 中優先度
            if medium_priority_batches:
                self.logger.info(
                    f"Migrating {len(medium_priority_batches)} medium priority batches..."
                )
                medium_results = await asyncio.gather(
                    *[migrate_single_batch(batch) for batch in medium_priority_batches]
                )
                migration_results.extend(medium_results)

            # 低優先度
            if low_priority_batches:
                self.logger.info(
                    f"Migrating {len(low_priority_batches)} low priority batches..."
                )
                low_results = await asyncio.gather(
                    *[migrate_single_batch(batch) for batch in low_priority_batches]
                )
                migration_results.extend(low_results)

            # 結果集計
            self.migration_stats["end_time"] = datetime.now(timezone.utc)

            total_successful = sum(r.successful for r in migration_results)
            total_failed = sum(r.failed for r in migration_results)
            total_duration = (
                self.migration_stats["end_time"] - self.migration_stats["start_time"]
            ).total_seconds()

            # 最終レポート
            final_report = {
                "migration_completed": True,
                "summary": {
                    "total_files_discovered": self.migration_stats["total_files_found"],
                    "files_analyzed": self.migration_stats["files_analyzed"],
                    "duplicates_detected": self.migration_stats["duplicates_detected"],
                    "batches_processed": len(migration_results),
                    "files_migrated_successfully": total_successful,
                    "migration_failures": total_failed,
                    "total_duration_seconds": total_duration,
                    "average_files_per_second": (
                        total_successful / total_duration if total_duration > 0 else 0
                    ),
                },
                "migration_stats": self.migration_stats,
                "batch_results": [asdict(result) for result in migration_results],
                "database_url": self.database_url,
            }

            # 成功ログ
            self.logger.info(
                f"🎉 Migration Complete! "
                f"{total_successful} files migrated successfully, "
                f"{total_failed} failures, "
                f"{total_duration:0.1f}s total"
            )

            return final_report

        except Exception as e:
            self.migration_stats["end_time"] = datetime.now(timezone.utc)
            self.logger.error(f"Full migration failed: {e}")

            return {
                "migration_completed": False,
                "error": str(e),
                "migration_stats": self.migration_stats,
            }

    async def generate_migration_report(self, report_data: Dict[str, Any]) -> str:
        """移行レポート生成"""
        report_path = f"/home/aicompany/ai_co/migration_reports/grimoire_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # レポートディレクトリ作成
        os.makedirs(os.path.dirname(report_path), exist_ok=True)

        # レポート保存
        if aiofiles:
            async with aiofiles.open(report_path, "w") as f:
                await f.write(json.dumps(report_data, indent=2, default=str))
        else:
            with open(report_path, "w") as f:
                f.write(json.dumps(report_data, indent=2, default=str))

        self.logger.info(f"Migration report saved: {report_path}")
        return report_path

    async def cleanup(self):
        """リソースクリーンアップ"""
        try:
            if self.grimoire_db:
                await self.grimoire_db.close()

            if self.vector_search and hasattr(self.vector_search, "cleanup"):
                await self.vector_search.cleanup()

            if self.evolution_engine and hasattr(self.evolution_engine, "cleanup"):
                await self.evolution_engine.cleanup()

            if self.task_sage and hasattr(self.task_sage, "cleanup"):
                await self.task_sage.cleanup()

            if self.rag_integration and hasattr(self.rag_integration, "cleanup"):
                await self.rag_integration.cleanup()

            self.logger.info("Comprehensive Grimoire Migration System cleaned up")

        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")

# メイン実行関数
async def execute_comprehensive_migration():
    """包括的移行の実行"""
    migration_system = ComprehensiveGrimoireMigration()

    try:
        # 初期化
        await migration_system.initialize()

        # 完全移行実行
        result = await migration_system.execute_full_migration()

        # レポート生成
        report_path = await migration_system.generate_migration_report(result)

        print("=" * 80)
        print("🏛️ Elders Guild Grimoire Migration Complete!")
        print("=" * 80)
        print(f"📊 Summary:")
        if result.get("migration_completed"):
            summary = result["summary"]
            print(f"  • Files discovered: {summary['total_files_discovered']}")
            print(f"  • Files analyzed: {summary['files_analyzed']}")
            print(f"  • Duplicates detected: {summary['duplicates_detected']}")
            print(f"  • Files migrated: {summary['files_migrated_successfully']}")
            print(f"  • Failures: {summary['migration_failures']}")
            print(f"  • Duration: {summary['total_duration_seconds']:0.1f} seconds")
            print(f"  • Speed: {summary['average_files_per_second']:0.2f} files/sec")
        else:
            print(f"  ❌ Migration failed: {result.get('error')}")

        print(f"📄 Report: {report_path}")
        print("=" * 80)

        return result

    finally:
        await migration_system.cleanup()

if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    )

    # 実行
    asyncio.run(execute_comprehensive_migration())
