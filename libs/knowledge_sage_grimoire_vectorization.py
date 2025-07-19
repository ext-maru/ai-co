#!/usr/bin/env python3
"""
Knowledge Sage Grimoire Vectorization System
ナレッジ賢者魔法書ベクトル化システム

知識の類似性検索、知恵の継承、知識進化の追跡を実現
グランドエルダーmaru直属のクロードエルダーによる慎重な実装
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from libs.four_sages_integration import FourSagesIntegration
from libs.grimoire_database import (
    GrimoireDatabase,
    MagicSchool,
    SpellMetadata,
    SpellType,
)
from libs.grimoire_spell_evolution import EvolutionEngine, EvolutionType
from libs.grimoire_vector_search import GrimoireVectorSearch, SearchQuery, SearchResult
from libs.knowledge_base_manager import KnowledgeBaseManager

logger = logging.getLogger(__name__)


class KnowledgeType(Enum):
    """知識タイプ分類"""

    TECHNICAL = "technical"  # 🔧 技術的知識 (実装方法、API仕様)
    PROCEDURAL = "procedural"  # 📋 手順・プロセス知識 (TDD、ワークフロー)
    CONCEPTUAL = "conceptual"  # 💡 概念的知識 (設計思想、原理)
    HISTORICAL = "historical"  # 📜 歴史的知識 (過去の決定、経緯)
    EXPERIENTIAL = "experiential"  # 🎯 経験的知識 (失敗談、教訓)


class KnowledgeDepth(Enum):
    """知識の深さ"""

    SURFACE = "surface"  # 🌊 表層的知識 (概要、サマリー)
    INTERMEDIATE = "intermediate"  # 🏔️ 中間的知識 (詳細説明)
    DEEP = "deep"  # 🏗️ 深層的知識 (実装詳細、設計思想)
    EXPERT = "expert"  # 🧙‍♂️ 専門的知識 (エルダー級の英智)


@dataclass
class KnowledgeVectorMetadata:
    """ナレッジベクトル化メタデータ"""

    knowledge_id: str
    knowledge_type: KnowledgeType
    knowledge_depth: KnowledgeDepth
    source_file: str
    tags: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    prerequisite_knowledge: List[str] = field(default_factory=list)
    wisdom_level: float = 0.0  # 0.0-1.0 エルダー評価による知恵レベル
    creation_context: Optional[str] = None
    last_evolution: Optional[datetime] = None
    evolution_count: int = 0


@dataclass
class KnowledgeVectorDimensions:
    """ナレッジベクトル次元定義"""

    content_semantic: int = 768  # コンテンツのセマンティック埋め込み
    concept_relations: int = 256  # 概念間関係性
    procedural_steps: int = 256  # 手順・プロセス情報
    contextual_embedding: int = 384  # コンテキスト埋め込み
    wisdom_evolution: int = 128  # 知恵の進化履歴


class KnowledgeSageGrimoireVectorization:
    """ナレッジ賢者魔法書ベクトル化システム"""

    def __init__(
        self,
        database_url: str = "postgresql://aicompany@localhost:5432/ai_company_grimoire",
    ):
        self.database_url = database_url
        self.logger = logging.getLogger(__name__)

        # エルダー階層への敬意
        self.logger.info("📚 ナレッジ賢者による知識ベクトル化システム初期化")
        self.logger.info("🏛️ グランドエルダーmaru → クロードエルダーの指示下で実行")

        # コンポーネント
        self.grimoire_db = None
        self.vector_search = None
        self.evolution_engine = None
        self.four_sages = None
        self.knowledge_manager = KnowledgeBaseManager()

        # ベクトル次元
        self.dimensions = KnowledgeVectorDimensions()
        self.total_dimensions = (
            self.dimensions.content_semantic
            + self.dimensions.concept_relations
            + self.dimensions.procedural_steps
            + self.dimensions.contextual_embedding
            + self.dimensions.wisdom_evolution
        )

        # 知識キャッシュ
        self.knowledge_cache = {}
        self.wisdom_cache = {}

        # ナレッジ賢者統計
        self.stats = {
            "knowledge_vectorized": 0,
            "wisdom_searches": 0,
            "concept_mappings": 0,
            "knowledge_evolutions": 0,
            "elder_consultations": 0,
        }

        # 知識パターン認識
        self.knowledge_patterns = {
            KnowledgeType.TECHNICAL: [
                r"def\s+\w+",
                r"class\s+\w+",
                r"import\s+\w+",
                r"pip install",
                r"npm\s+install",
                r"docker\s+run",
                r"git\s+\w+",
            ],
            KnowledgeType.PROCEDURAL: [
                r"step\s+\d+",
                r"phase\s+\d+",
                r"プロセス",
                r"手順",
                r"workflow",
            ],
            KnowledgeType.CONCEPTUAL: [
                r"concept",
                r"principle",
                r"theory",
                r"paradigm",
                r"philosophy",
            ],
            KnowledgeType.HISTORICAL: [
                r"history",
                r"legacy",
                r"deprecated",
                r"migration",
                r"version",
            ],
            KnowledgeType.EXPERIENTIAL: [
                r"lesson learned",
                r"best practice",
                r"pitfall",
                r"gotcha",
                r"experience",
            ],
        }

    async def initialize(self):
        """ナレッジ賢者ベクトル化システム初期化 - エルダーズ標準API"""
        try:
            self.logger.info("🏛️ ナレッジ賢者ベクトル化システム初期化中...")

            # 魔法書データベース初期化
            self.grimoire_db = GrimoireDatabase(self.database_url)
            await self.grimoire_db.initialize()

            # ベクトル検索エンジン初期化
            self.vector_search = GrimoireVectorSearch(database=self.grimoire_db)
            await self.vector_search.initialize()

            # 進化エンジン初期化
            self.evolution_engine = EvolutionEngine(database=self.grimoire_db)
            await self.evolution_engine.initialize()

            # 4賢者統合システム
            self.four_sages = FourSagesIntegration()
            await self.four_sages.initialize()

            # ナレッジ賢者専用テーブル作成
            await self._create_knowledge_sage_tables()

            self.logger.info("✅ ナレッジ賢者ベクトル化システム初期化完了")
            self.logger.info("📚 知識の継承と進化準備完了 - エルダーズの英智を待機中")

        except Exception as e:
            self.logger.error(f"❌ ナレッジ賢者初期化失敗: {e}")
            self.logger.error("🏛️ グランドエルダーmaruへの緊急報告が必要")
            raise

    async def _create_knowledge_sage_tables(self):
        """ナレッジ賢者専用テーブル作成"""
        try:
            async with self.grimoire_db.connection_pool.acquire() as conn:
                # 知識関連性テーブル
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS knowledge_relations (
                        id SERIAL PRIMARY KEY,
                        source_knowledge_id TEXT NOT NULL,
                        target_knowledge_id TEXT NOT NULL,
                        relation_type VARCHAR(50),
                        strength FLOAT DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(source_knowledge_id, target_knowledge_id)
                    )
                """
                )

                # 知識進化履歴テーブル
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS knowledge_evolution_history (
                        id SERIAL PRIMARY KEY,
                        knowledge_id TEXT NOT NULL,
                        evolution_type VARCHAR(50),
                        old_content TEXT,
                        new_content TEXT,
                        wisdom_delta FLOAT DEFAULT 0.0,
                        elder_approval BOOLEAN DEFAULT FALSE,
                        evolution_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # 概念マッピングテーブル
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS concept_mappings (
                        id SERIAL PRIMARY KEY,
                        concept_name TEXT NOT NULL,
                        knowledge_ids TEXT[], -- Array of knowledge IDs
                        concept_vector FLOAT[], -- Vector representation
                        usage_frequency INTEGER DEFAULT 1,
                        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # エルダー知恵評価テーブル
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS elder_wisdom_evaluations (
                        id SERIAL PRIMARY KEY,
                        knowledge_id TEXT NOT NULL,
                        evaluator VARCHAR(100),
                        wisdom_score FLOAT,
                        evaluation_criteria TEXT,
                        comments TEXT,
                        evaluation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

            self.logger.info("📚 ナレッジ賢者専用テーブル作成完了")

        except Exception as e:
            self.logger.error(f"❌ ナレッジ賢者テーブル作成失敗: {e}")
            raise

    async def vectorize_knowledge(self, knowledge_data: Dict[str, Any]) -> str:
        """知識のベクトル化"""
        try:
            self.logger.info(f"📚 知識分析開始: {knowledge_data.get('title', 'Unknown')}")

            # 知識メタデータ分析
            knowledge_metadata = await self._analyze_knowledge_metadata(knowledge_data)

            # 複合ベクトル生成
            knowledge_vector = await self._generate_knowledge_vector(
                knowledge_data, knowledge_metadata
            )

            # 魔法書メタデータ作成
            spell_metadata = SpellMetadata(
                id=str(uuid.uuid4()),
                spell_name=f"knowledge_{knowledge_metadata.knowledge_id}",
                content=json.dumps(knowledge_data),
                spell_type=SpellType.REFERENCE,
                magic_school=MagicSchool.KNOWLEDGE_SAGE,
                tags=[
                    "knowledge_sage",
                    knowledge_metadata.knowledge_type.value,
                    knowledge_metadata.knowledge_depth.value,
                ]
                + knowledge_metadata.tags,
                power_level=self._wisdom_to_power_level(
                    knowledge_metadata.wisdom_level
                ),
                casting_frequency=0,
                last_cast_at=None,
                is_eternal=knowledge_metadata.knowledge_depth
                in [KnowledgeDepth.EXPERT, KnowledgeDepth.DEEP],
                evolution_history=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                version=1,
            )

            # データベースに保存
            spell_id = await self.grimoire_db.create_spell(
                {
                    "metadata": spell_metadata,
                    "vector": knowledge_vector,
                    "knowledge_metadata": knowledge_metadata,
                }
            )

            # 概念マッピング更新
            await self._update_concept_mappings(knowledge_metadata, spell_id)

            # 統計更新
            self.stats["knowledge_vectorized"] += 1

            self.logger.info(f"✅ 知識ベクトル化完了: {spell_id}")
            return spell_id

        except Exception as e:
            self.logger.error(f"❌ 知識ベクトル化失敗: {e}")
            raise

    async def _analyze_knowledge_metadata(
        self, knowledge_data: Dict[str, Any]
    ) -> KnowledgeVectorMetadata:
        """知識メタデータ分析"""
        knowledge_id = knowledge_data.get("id", str(uuid.uuid4()))

        # 知識タイプ分類
        knowledge_type = await self._classify_knowledge_type(
            knowledge_data.get("content", "")
        )

        # 知識の深さ評価
        knowledge_depth = await self._assess_knowledge_depth(knowledge_data)

        # タグ抽出
        tags = self._extract_knowledge_tags(knowledge_data)

        # 関連概念抽出
        related_concepts = await self._extract_related_concepts(knowledge_data)

        # 知恵レベル評価
        wisdom_level = await self._evaluate_wisdom_level(
            knowledge_data, knowledge_type, knowledge_depth
        )

        return KnowledgeVectorMetadata(
            knowledge_id=knowledge_id,
            knowledge_type=knowledge_type,
            knowledge_depth=knowledge_depth,
            source_file=knowledge_data.get("source_file", "unknown"),
            tags=tags,
            related_concepts=related_concepts,
            wisdom_level=wisdom_level,
            creation_context=knowledge_data.get("context", None),
            last_evolution=None,
            evolution_count=0,
        )

    async def _classify_knowledge_type(self, content: str) -> KnowledgeType:
        """知識タイプ分類"""
        content_lower = content.lower()

        type_scores = {}
        for knowledge_type, patterns in self.knowledge_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, content_lower, re.IGNORECASE))
                score += matches
            type_scores[knowledge_type] = score

        # 最高スコアのタイプを返す
        if type_scores:
            return max(type_scores, key=type_scores.get)
        return KnowledgeType.CONCEPTUAL

    async def _assess_knowledge_depth(
        self, knowledge_data: Dict[str, Any]
    ) -> KnowledgeDepth:
        """知識の深さ評価"""
        content = knowledge_data.get("content", "")
        content_length = len(content)

        # コード例の数
        code_blocks = len(re.findall(r"```.*?```", content, re.DOTALL))

        # 詳細度の指標
        technical_terms = len(
            re.findall(
                r"\b(implementation|architecture|algorithm|optimization)\b",
                content,
                re.IGNORECASE,
            )
        )

        if code_blocks >= 3 or technical_terms >= 5 or content_length > 3000:
            return KnowledgeDepth.EXPERT
        elif code_blocks >= 2 or technical_terms >= 3 or content_length > 1500:
            return KnowledgeDepth.DEEP
        elif code_blocks >= 1 or technical_terms >= 1 or content_length > 500:
            return KnowledgeDepth.INTERMEDIATE
        else:
            return KnowledgeDepth.SURFACE

    def _extract_knowledge_tags(self, knowledge_data: Dict[str, Any]) -> List[str]:
        """知識タグ抽出"""
        tags = []
        content = knowledge_data.get("content", "").lower()

        # 技術スタック検出
        tech_keywords = [
            "python",
            "javascript",
            "docker",
            "postgresql",
            "react",
            "fastapi",
            "pytest",
        ]
        for keyword in tech_keywords:
            if keyword in content:
                tags.append(keyword)

        # ファイル拡張子から推測
        source_file = knowledge_data.get("source_file", "")
        if source_file.endswith(".py"):
            tags.append("python")
        elif source_file.endswith(".md"):
            tags.append("documentation")
        elif source_file.endswith(".json"):
            tags.append("configuration")

        return tags

    async def _extract_related_concepts(
        self, knowledge_data: Dict[str, Any]
    ) -> List[str]:
        """関連概念抽出"""
        content = knowledge_data.get("content", "")

        # 概念キーワード抽出
        concept_patterns = [
            r"\b([A-Z][a-z]+(?:[A-Z][a-z]+)*)\b",  # PascalCase
            r"\b(design pattern|best practice|anti-pattern)\b",
            r"\b(algorithm|data structure|architecture)\b",
        ]

        concepts = set()
        for pattern in concept_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            concepts.update(matches)

        return list(concepts)[:10]  # 最大10個

    async def _evaluate_wisdom_level(
        self,
        knowledge_data: Dict[str, Any],
        knowledge_type: KnowledgeType,
        knowledge_depth: KnowledgeDepth,
    ) -> float:
        """知恵レベル評価"""
        base_score = 0.3

        # 深さによる重み
        depth_weights = {
            KnowledgeDepth.SURFACE: 0.1,
            KnowledgeDepth.INTERMEDIATE: 0.3,
            KnowledgeDepth.DEEP: 0.6,
            KnowledgeDepth.EXPERT: 1.0,
        }

        # タイプによる重み
        type_weights = {
            KnowledgeType.EXPERIENTIAL: 0.9,  # 経験的知識は高価値
            KnowledgeType.HISTORICAL: 0.8,
            KnowledgeType.CONCEPTUAL: 0.7,
            KnowledgeType.TECHNICAL: 0.6,
            KnowledgeType.PROCEDURAL: 0.5,
        }

        wisdom_score = (
            base_score
            + depth_weights.get(knowledge_depth, 0.3) * 0.4
            + type_weights.get(knowledge_type, 0.5) * 0.3
        )

        return min(wisdom_score, 1.0)

    def _wisdom_to_power_level(self, wisdom_level: float) -> int:
        """知恵レベルをパワーレベルに変換"""
        return int(wisdom_level * 100)

    async def _generate_knowledge_vector(
        self, knowledge_data: Dict[str, Any], metadata: KnowledgeVectorMetadata
    ) -> np.ndarray:
        """知識ベクトル生成"""
        # 総次元数のベクトル初期化
        vector = np.zeros(self.total_dimensions)

        current_idx = 0

        # 1. コンテンツセマンティック埋め込み
        content_vector = await self._generate_content_semantic_vector(
            knowledge_data.get("content", "")
        )
        vector[
            current_idx : current_idx + self.dimensions.content_semantic
        ] = content_vector
        current_idx += self.dimensions.content_semantic

        # 2. 概念間関係性
        concept_vector = await self._generate_concept_relations_vector(
            metadata.related_concepts
        )
        vector[
            current_idx : current_idx + self.dimensions.concept_relations
        ] = concept_vector
        current_idx += self.dimensions.concept_relations

        # 3. 手順・プロセス情報
        procedural_vector = await self._generate_procedural_vector(knowledge_data)
        vector[
            current_idx : current_idx + self.dimensions.procedural_steps
        ] = procedural_vector
        current_idx += self.dimensions.procedural_steps

        # 4. コンテキスト埋め込み
        contextual_vector = await self._generate_contextual_vector(
            knowledge_data, metadata
        )
        vector[
            current_idx : current_idx + self.dimensions.contextual_embedding
        ] = contextual_vector
        current_idx += self.dimensions.contextual_embedding

        # 5. 知恵の進化履歴
        wisdom_vector = await self._generate_wisdom_evolution_vector(metadata)
        vector[
            current_idx : current_idx + self.dimensions.wisdom_evolution
        ] = wisdom_vector

        return vector

    async def _generate_content_semantic_vector(self, content: str) -> np.ndarray:
        """コンテンツセマンティック埋め込み生成"""
        # OpenAI Embeddings APIを使用（モック実装）
        # 実際の実装では: openai.Embedding.create(model="text-embedding-ada-002", input=content)
        return np.random.random(self.dimensions.content_semantic)

    async def _generate_concept_relations_vector(
        self, concepts: List[str]
    ) -> np.ndarray:
        """概念間関係性ベクトル生成"""
        vector = np.zeros(self.dimensions.concept_relations)

        # 概念の頻度と関係性をエンコード
        for i, concept in enumerate(concepts[:32]):  # 最大32概念
            if i * 8 + 8 <= len(vector):
                concept_hash = hash(concept) % 256
                vector[i * 8 : (i + 1) * 8] = [
                    concept_hash / 256.0,  # 概念ID
                    1.0,  # 存在フラグ
                    0.8,  # 重要度（固定値）
                    0.5,  # 関連度（固定値）
                    0.0,
                    0.0,
                    0.0,
                    0.0,  # 将来拡張用
                ]

        return vector

    async def _generate_procedural_vector(
        self, knowledge_data: Dict[str, Any]
    ) -> np.ndarray:
        """手順・プロセス情報ベクトル生成"""
        vector = np.zeros(self.dimensions.procedural_steps)

        content = knowledge_data.get("content", "")

        # ステップ検出
        step_patterns = [r"step\s+(\d+)", r"phase\s+(\d+)", r"(\d+)\."]
        step_count = 0

        for pattern in step_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            step_count += len(matches)

        # 手順数を正規化してエンコード
        vector[0] = min(step_count / 10.0, 1.0)

        # プロセスタイプ分類
        if "workflow" in content.lower():
            vector[1] = 1.0
        if "procedure" in content.lower():
            vector[2] = 1.0
        if "guide" in content.lower():
            vector[3] = 1.0

        return vector

    async def _generate_contextual_vector(
        self, knowledge_data: Dict[str, Any], metadata: KnowledgeVectorMetadata
    ) -> np.ndarray:
        """コンテキスト埋め込み生成"""
        vector = np.zeros(self.dimensions.contextual_embedding)

        # メタデータエンコーディング
        vector[0] = list(KnowledgeType).index(metadata.knowledge_type) / len(
            KnowledgeType
        )
        vector[1] = list(KnowledgeDepth).index(metadata.knowledge_depth) / len(
            KnowledgeDepth
        )
        vector[2] = metadata.wisdom_level
        vector[3] = len(metadata.tags) / 10.0

        return vector

    async def _generate_wisdom_evolution_vector(
        self, metadata: KnowledgeVectorMetadata
    ) -> np.ndarray:
        """知恵の進化履歴ベクトル生成"""
        vector = np.zeros(self.dimensions.wisdom_evolution)

        # 進化履歴のエンコード
        vector[0] = metadata.evolution_count / 10.0
        vector[1] = metadata.wisdom_level

        # 最終進化からの経過時間
        if metadata.last_evolution:
            days_since = (datetime.now(timezone.utc) - metadata.last_evolution).days
            vector[2] = min(days_since / 365.0, 1.0)

        return vector

    async def _update_concept_mappings(
        self, metadata: KnowledgeVectorMetadata, spell_id: str
    ):
        """概念マッピング更新"""
        try:
            async with self.grimoire_db.connection_pool.acquire() as conn:
                for concept in metadata.related_concepts:
                    await conn.execute(
                        """
                        INSERT INTO concept_mappings (concept_name, knowledge_ids, usage_frequency)
                        VALUES ($1, $2, 1)
                        ON CONFLICT (concept_name) DO UPDATE SET
                            knowledge_ids = array_append(concept_mappings.knowledge_ids, $2),
                            usage_frequency = concept_mappings.usage_frequency + 1,
                            last_accessed = CURRENT_TIMESTAMP
                    """,
                        concept,
                        spell_id,
                    )

            self.stats["concept_mappings"] += len(metadata.related_concepts)

        except Exception as e:
            self.logger.warning(f"⚠️ 概念マッピング更新失敗: {e}")

    async def search_wisdom(self, query: str, limit: int = 10) -> List[SearchResult]:
        """知恵検索"""
        try:
            self.logger.info(f"🔍 知恵検索開始: {query}")

            search_query = SearchQuery(
                query_text=query,
                magic_schools=[MagicSchool.KNOWLEDGE_SAGE],
                limit=limit,
                similarity_threshold=0.7,
            )

            results = await self.vector_search.search_similar(search_query)

            self.stats["wisdom_searches"] += 1

            self.logger.info(f"📚 知恵検索完了: {len(results)}件の知識を発見")
            return results

        except Exception as e:
            self.logger.error(f"❌ 知恵検索失敗: {e}")
            return []

    async def evolve_knowledge(
        self,
        knowledge_id: str,
        new_content: str,
        evolution_type: str = "content_update",
    ) -> Dict[str, Any]:
        """知識進化"""
        try:
            self.logger.info(f"🌱 知識進化開始: {knowledge_id}")

            # 既存知識取得
            old_knowledge = await self._get_knowledge_by_id(knowledge_id)
            if not old_knowledge:
                raise ValueError(f"Knowledge {knowledge_id} not found")

            # 進化の分析
            evolution_analysis = await self._analyze_knowledge_evolution(
                old_knowledge, new_content, evolution_type
            )

            # 4賢者への相談
            if evolution_analysis["significance"] > 0.7:
                elder_consultation = await self._consult_elders_for_evolution(
                    knowledge_id, evolution_analysis
                )
                evolution_analysis["elder_approval"] = elder_consultation.get(
                    "approved", False
                )

            # 進化履歴記録
            await self._record_knowledge_evolution(knowledge_id, evolution_analysis)

            self.stats["knowledge_evolutions"] += 1

            self.logger.info(f"✅ 知識進化完了: {knowledge_id}")
            return evolution_analysis

        except Exception as e:
            self.logger.error(f"❌ 知識進化失敗: {e}")
            raise

    async def _get_knowledge_by_id(self, knowledge_id: str) -> Optional[Dict[str, Any]]:
        """ID による知識取得"""
        # 簡易実装
        return {"id": knowledge_id, "content": "existing content"}

    async def _analyze_knowledge_evolution(
        self, old_knowledge: Dict[str, Any], new_content: str, evolution_type: str
    ) -> Dict[str, Any]:
        """知識進化分析"""
        return {
            "evolution_type": evolution_type,
            "significance": 0.8,  # 簡易実装
            "improvements": ["More detailed examples", "Updated best practices"],
            "wisdom_delta": 0.1,
        }

    async def _consult_elders_for_evolution(
        self, knowledge_id: str, evolution_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """知識進化についてエルダーズに相談"""
        if self.four_sages:
            consultation_request = {
                "type": "knowledge_evolution_review",
                "data": {
                    "knowledge_id": knowledge_id,
                    "evolution_analysis": evolution_analysis,
                    "requester": "knowledge_sage",
                },
            }

            response = await self.four_sages.coordinate_learning_session(
                consultation_request
            )
            self.stats["elder_consultations"] += 1

            return {
                "approved": response.get("consensus_reached", False),
                "elder_feedback": response.get("learning_outcome", {}),
                "sage_votes": response.get("individual_responses", {}),
            }

        return {"approved": True, "reason": "Elders not available"}

    async def _record_knowledge_evolution(
        self, knowledge_id: str, evolution_analysis: Dict[str, Any]
    ):
        """知識進化履歴記録"""
        try:
            async with self.grimoire_db.connection_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO knowledge_evolution_history
                    (knowledge_id, evolution_type, wisdom_delta, elder_approval)
                    VALUES ($1, $2, $3, $4)
                """,
                    knowledge_id,
                    evolution_analysis["evolution_type"],
                    evolution_analysis.get("wisdom_delta", 0.0),
                    evolution_analysis.get("elder_approval", False),
                )

        except Exception as e:
            self.logger.warning(f"⚠️ 知識進化履歴記録失敗: {e}")

    async def get_statistics(self) -> Dict[str, Any]:
        """統計情報取得 - エルダーズ標準API"""
        return {
            "system_stats": self.stats.copy(),
            "cache_stats": {
                "knowledge_cache_size": len(self.knowledge_cache),
                "wisdom_cache_size": len(self.wisdom_cache),
            },
            "vector_dimensions": {
                "total": self.total_dimensions,
                "breakdown": {
                    "content_semantic": self.dimensions.content_semantic,
                    "concept_relations": self.dimensions.concept_relations,
                    "procedural_steps": self.dimensions.procedural_steps,
                    "contextual_embedding": self.dimensions.contextual_embedding,
                    "wisdom_evolution": self.dimensions.wisdom_evolution,
                },
            },
            "knowledge_types": [ktype.value for ktype in KnowledgeType],
            "knowledge_depths": [depth.value for depth in KnowledgeDepth],
        }

    async def cleanup(self):
        """リソースクリーンアップ - エルダーズ標準API"""
        try:
            if self.four_sages:
                await self.four_sages.cleanup()

            if self.grimoire_db:
                await self.grimoire_db.close()

            self.logger.info("📚 ナレッジ賢者システムクリーンアップ完了")
            self.logger.info("🏛️ エルダーズへの最終報告完了")

        except Exception as e:
            self.logger.error(f"❌ クリーンアップ失敗: {e}")


# 使用例とテスト用関数
async def test_knowledge_sage_system():
    """ナレッジ賢者システムのテスト"""
    knowledge_sage = KnowledgeSageGrimoireVectorization()

    try:
        await knowledge_sage.initialize()

        # テスト知識
        test_knowledge = {
            "id": "test_knowledge_001",
            "title": "Test Driven Development Best Practices",
            "content": """
            # Test Driven Development (TDD) Best Practices

            TDD is a software development methodology where tests are written before code.

            ## Steps:
            1. Write a failing test (Red)
            2. Write minimal code to pass (Green)
            3. Refactor and improve (Refactor)

            ## Best Practices:
            - Keep tests simple and focused
            - Use descriptive test names
            - Follow the AAA pattern (Arrange, Act, Assert)

            ```python
            def test_user_creation():
                # Arrange
                user_data = {"name": "John", "email": "john@example.com"}

                # Act
                user = create_user(user_data)

                # Assert
                assert user.name == "John"
                assert user.email == "john@example.com"
            ```
            """,
            "source_file": "knowledge_base/tdd_best_practices.md",
            "context": "Development methodology documentation",
        }

        # 知識ベクトル化
        spell_id = await knowledge_sage.vectorize_knowledge(test_knowledge)
        print(f"✅ Test knowledge vectorized: {spell_id}")

        # 知恵検索
        results = await knowledge_sage.search_wisdom("TDD best practices", limit=3)
        print(f"✅ Found {len(results)} related wisdom entries")

        # 統計情報
        stats = await knowledge_sage.get_statistics()
        print(f"✅ System stats: {stats['system_stats']}")

    finally:
        await knowledge_sage.cleanup()


if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    )

    # テスト実行
    asyncio.run(test_knowledge_sage_system())
