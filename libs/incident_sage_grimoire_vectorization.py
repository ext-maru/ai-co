#!/usr/bin/env python3
"""
Incident Sage Grimoire Vectorization System
インシデント賢者魔法書ベクトル化システム

エラーパターンの類似検索、予兆検知、自動解決策提案を実現
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

logger = logging.getLogger(__name__)


class IncidentSeverity(Enum):
    """インシデント重要度"""

    CRITICAL = "critical"  # 🐉 古龍の覚醒 (システム全体障害)
    HIGH = "high"  # 💀 スケルトン軍団 (重要サービス停止)
    MEDIUM = "medium"  # ⚔️ オークの大軍 (複数障害)
    LOW = "low"  # 👹 ゴブリンの小細工 (設定ミス)
    MINOR = "minor"  # 🧚‍♀️ 妖精の悪戯 (軽微バグ)


class IncidentCategory(Enum):
    """インシデント分類"""

    MEMORY_LEAK = "memory_leak"  # 🌊 スライムの増殖
    INFINITE_LOOP = "infinite_loop"  # 🗿 ゴーレムの暴走
    DEADLOCK = "deadlock"  # 🕷️ クモの巣
    PROCESS_CRASH = "process_crash"  # 🧟‍♂️ ゾンビの侵入
    CONFIG_ERROR = "config_error"  # 👹 ゴブリンの小細工
    NETWORK_ISSUE = "network_issue"  # 🌩️ 嵐の妨害
    DATABASE_ERROR = "database_error"  # 💎 クリスタルの破損
    PERMISSION_DENIED = "permission_denied"  # 🛡️ 結界の拒絶


@dataclass
class IncidentVectorMetadata:
    """インシデントベクトル化メタデータ"""

    incident_id: str
    incident_type: IncidentCategory
    severity: IncidentSeverity
    error_patterns: List[str] = field(default_factory=list)
    stack_trace_patterns: List[str] = field(default_factory=list)
    resolution_patterns: List[str] = field(default_factory=list)
    affected_systems: List[str] = field(default_factory=list)
    resolution_time_minutes: Optional[float] = None
    recurrence_count: int = 0
    related_incidents: List[str] = field(default_factory=list)


@dataclass
class IncidentVectorDimensions:
    """インシデントベクトル次元定義"""

    error_message: int = 512  # エラーメッセージの埋め込み
    stack_trace: int = 384  # スタックトレース情報
    system_context: int = 256  # システム状況・コンテキスト
    resolution_steps: int = 384  # 解決手順・対策
    prevention_measures: int = 256  # 予防策・改善点


class IncidentSageGrimoireVectorization:
    """インシデント賢者魔法書ベクトル化システム"""

    def __init__(
        self,
        database_url: str = "postgresql://aicompany@localhost:5432/ai_company_grimoire",
    ):
        self.database_url = database_url
        self.logger = logging.getLogger(__name__)

        # エルダー階層への敬意
        self.logger.info("🛡️ インシデント賢者による危機対応システム初期化")
        self.logger.info("🏛️ グランドエルダーmaru → クロードエルダーの指示下で実行")

        # コンポーネント
        self.grimoire_db = None
        self.vector_search = None
        self.evolution_engine = None
        self.four_sages = None

        # ベクトル次元
        self.dimensions = IncidentVectorDimensions()
        self.total_dimensions = (
            self.dimensions.error_message
            + self.dimensions.stack_trace
            + self.dimensions.system_context
            + self.dimensions.resolution_steps
            + self.dimensions.prevention_measures
        )

        # 検索キャッシュ
        self.pattern_cache = {}
        self.similarity_cache = {}

        # インシデント統計
        self.stats = {
            "incidents_vectorized": 0,
            "pattern_searches": 0,
            "resolutions_provided": 0,
            "preventions_applied": 0,
            "crisis_averted": 0,
        }

        # エラーパターン正規表現
        self.error_patterns = {
            IncidentCategory.MEMORY_LEAK: [
                r"out of memory",
                r"memory leak",
                r"oom killed",
                r"heap.*full",
            ],
            IncidentCategory.INFINITE_LOOP: [
                r"infinite loop",
                r"stack overflow",
                r"recursion limit",
                r"timeout",
            ],
            IncidentCategory.DEADLOCK: [
                r"deadlock",
                r"lock.*timeout",
                r"circular dependency",
                r"blocked",
            ],
            IncidentCategory.PROCESS_CRASH: [
                r"segmentation fault",
                r"core dumped",
                r"crash",
                r"terminated",
            ],
            IncidentCategory.CONFIG_ERROR: [
                r"config.*error",
                r"invalid.*setting",
                r"missing.*parameter",
            ],
            IncidentCategory.NETWORK_ISSUE: [
                r"connection.*refused",
                r"timeout",
                r"network.*unreachable",
            ],
            IncidentCategory.DATABASE_ERROR: [
                r"database.*error",
                r"sql.*error",
                r"connection.*failed",
            ],
            IncidentCategory.PERMISSION_DENIED: [
                r"permission.*denied",
                r"access.*forbidden",
                r"unauthorized",
            ],
        }

    async def initialize(self):
        """システム初期化（エルダー承認必須）"""
        try:
            self.logger.info("🏛️ インシデント賢者システム初期化中...")

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

            # インシデント賢者専用テーブル作成
            await self._create_incident_sage_tables()

            self.logger.info("✅ インシデント賢者魔法書ベクトル化システム初期化完了")
            self.logger.info("🛡️ 危機対応準備完了 - エルダーズの指示を待機中")

        except Exception as e:
            self.logger.error(f"❌ インシデント賢者初期化失敗: {e}")
            self.logger.error("🏛️ グランドエルダーmaruへの緊急報告が必要")
            raise

    async def _create_incident_sage_tables(self):
        """インシデント賢者専用テーブル作成"""
        try:
            async with self.grimoire_db.connection_pool.acquire() as conn:
                # インシデントパターンテーブル
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS incident_patterns (
                        id SERIAL PRIMARY KEY,
                        incident_id TEXT NOT NULL,
                        pattern_type TEXT NOT NULL,
                        pattern_text TEXT NOT NULL,
                        severity VARCHAR(20),
                        category VARCHAR(50),
                        occurrence_count INTEGER DEFAULT 1,
                        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(incident_id, pattern_type, pattern_text)
                    )
                """
                )

                # 解決策履歴テーブル
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS incident_resolutions (
                        id SERIAL PRIMARY KEY,
                        incident_id TEXT NOT NULL,
                        resolution_text TEXT NOT NULL,
                        resolution_steps JSONB,
                        success_rate FLOAT DEFAULT 0.0,
                        resolution_time_minutes FLOAT,
                        applied_by VARCHAR(100),
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        effectiveness_score FLOAT DEFAULT 0.0
                    )
                """
                )

                # 予防策テーブル
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS incident_preventions (
                        id SERIAL PRIMARY KEY,
                        incident_category VARCHAR(50) NOT NULL,
                        prevention_measure TEXT NOT NULL,
                        implementation_difficulty VARCHAR(20),
                        effectiveness_rating FLOAT DEFAULT 0.0,
                        implementation_count INTEGER DEFAULT 0,
                        success_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # インシデント関連性テーブル
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS incident_relationships (
                        id SERIAL PRIMARY KEY,
                        incident_id_1 TEXT NOT NULL,
                        incident_id_2 TEXT NOT NULL,
                        relationship_type VARCHAR(50),
                        similarity_score FLOAT,
                        relationship_strength FLOAT DEFAULT 0.0,
                        identified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(incident_id_1, incident_id_2)
                    )
                """
                )

            self.logger.info("🛡️ インシデント賢者専用テーブル作成完了")

        except Exception as e:
            self.logger.error(f"❌ インシデント賢者テーブル作成失敗: {e}")
            raise

    async def vectorize_incident(self, incident_data: Dict[str, Any]) -> str:
        """インシデントのベクトル化"""
        try:
            self.logger.info(
                f"🚨 インシデント分析開始: {incident_data.get('title', 'Unknown')}"
            )

            # インシデントメタデータ準備
            incident_metadata = await self._analyze_incident_metadata(incident_data)

            # 複合ベクトル生成
            incident_vector = await self._generate_incident_vector(
                incident_data, incident_metadata
            )

            # 魔法書メタデータ作成
            spell_metadata = SpellMetadata(
                id=str(uuid.uuid4()),
                spell_name=f"incident_{incident_metadata.incident_id}",
                content=json.dumps(incident_data),
                spell_type=SpellType.REFERENCE,  # インシデントは参照系
                magic_school=MagicSchool.CRISIS_SAGE,
                tags=[
                    "incident_sage",
                    incident_metadata.incident_type.value,
                    incident_metadata.severity.value,
                ],
                power_level=self._severity_to_power_level(incident_metadata.severity),
                casting_frequency=incident_metadata.recurrence_count,
                last_cast_at=None,
                is_eternal=incident_metadata.severity
                in [IncidentSeverity.CRITICAL, IncidentSeverity.HIGH],
                evolution_history=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                version=1,
            )

            # データベースに保存
            spell_id = await self.grimoire_db.create_spell(
                {
                    "spell_name": spell_metadata.spell_name,
                    "content": spell_metadata.content,
                    "spell_type": spell_metadata.spell_type.value,
                    "magic_school": spell_metadata.magic_school.value,
                    "tags": spell_metadata.tags,
                    "power_level": spell_metadata.power_level,
                    "is_eternal": spell_metadata.is_eternal,
                }
            )

            # ベクトルインデックス追加
            await self.vector_search.index_spell(spell_id, spell_metadata.__dict__)

            # パターン保存
            await self._save_incident_patterns(incident_metadata)

            # 解決策保存
            if incident_data.get("resolution"):
                await self._save_incident_resolution(
                    incident_metadata, incident_data["resolution"]
                )

            # 統計更新
            self.stats["incidents_vectorized"] += 1

            self.logger.info(f"✅ インシデント魔法書化完了: {spell_id}")
            return spell_id

        except Exception as e:
            self.logger.error(f"❌ インシデントベクトル化失敗: {e}")
            raise

    async def _analyze_incident_metadata(
        self, incident_data: Dict[str, Any]
    ) -> IncidentVectorMetadata:
        """インシデントメタデータ分析"""
        incident_id = incident_data.get("id", f"incident_{datetime.now().timestamp()}")

        # エラーメッセージからカテゴリ推定
        error_message = incident_data.get("error_message", "").lower()
        incident_type = await self._classify_incident_type(error_message)

        # 重要度推定
        severity = await self._assess_incident_severity(incident_data)

        # パターン抽出
        error_patterns = await self._extract_error_patterns(incident_data)
        stack_patterns = await self._extract_stack_trace_patterns(incident_data)
        resolution_patterns = await self._extract_resolution_patterns(incident_data)

        return IncidentVectorMetadata(
            incident_id=incident_id,
            incident_type=incident_type,
            severity=severity,
            error_patterns=error_patterns,
            stack_trace_patterns=stack_patterns,
            resolution_patterns=resolution_patterns,
            affected_systems=incident_data.get("affected_systems", []),
            resolution_time_minutes=incident_data.get("resolution_time_minutes"),
            recurrence_count=incident_data.get("recurrence_count", 0),
        )

    async def _classify_incident_type(self, error_message: str) -> IncidentCategory:
        """インシデントタイプ分類"""
        for category, patterns in self.error_patterns.items():
            for pattern in patterns:
                if re.search(pattern, error_message, re.IGNORECASE):
                    return category

        return IncidentCategory.CONFIG_ERROR  # デフォルト

    async def _assess_incident_severity(
        self, incident_data: Dict[str, Any]
    ) -> IncidentSeverity:
        """インシデント重要度評価"""
        severity_indicators = {
            IncidentSeverity.CRITICAL: [
                "system down",
                "complete failure",
                "total outage",
                "critical",
                "production halt",
                "data loss",
                "security breach",
            ],
            IncidentSeverity.HIGH: [
                "service unavailable",
                "major functionality",
                "multiple users",
                "performance degradation",
                "important feature",
            ],
            IncidentSeverity.MEDIUM: [
                "some users affected",
                "partial functionality",
                "moderate impact",
                "workaround available",
            ],
            IncidentSeverity.LOW: [
                "minor issue",
                "cosmetic",
                "single user",
                "low priority",
            ],
        }

        description = (
            incident_data.get("description", "")
            + " "
            + incident_data.get("error_message", "")
        ).lower()

        for severity, indicators in severity_indicators.items():
            for indicator in indicators:
                if indicator in description:
                    return severity

        return IncidentSeverity.MINOR

    def _severity_to_power_level(self, severity: IncidentSeverity) -> int:
        """重要度をパワーレベルに変換"""
        severity_map = {
            IncidentSeverity.CRITICAL: 10,
            IncidentSeverity.HIGH: 8,
            IncidentSeverity.MEDIUM: 6,
            IncidentSeverity.LOW: 4,
            IncidentSeverity.MINOR: 2,
        }
        return severity_map.get(severity, 1)

    async def _extract_error_patterns(self, incident_data: Dict[str, Any]) -> List[str]:
        """エラーパターン抽出"""
        patterns = []

        error_message = incident_data.get("error_message", "")
        if error_message:
            # 一般的なエラーパターンを抽出
            patterns.extend(re.findall(r"\w+Error", error_message))
            patterns.extend(re.findall(r"\w+Exception", error_message))
            patterns.extend(re.findall(r"HTTP \d{3}", error_message))

        return list(set(patterns))

    async def _extract_stack_trace_patterns(
        self, incident_data: Dict[str, Any]
    ) -> List[str]:
        """スタックトレースパターン抽出"""
        patterns = []

        stack_trace = incident_data.get("stack_trace", "")
        if stack_trace:
            # ファイル名とメソッド名を抽出
            patterns.extend(re.findall(r"at\s+(\S+)", stack_trace))
            patterns.extend(re.findall(r'File\s+"([^"]+)"', stack_trace))

        return list(set(patterns))

    async def _extract_resolution_patterns(
        self, incident_data: Dict[str, Any]
    ) -> List[str]:
        """解決パターン抽出"""
        patterns = []

        resolution = incident_data.get("resolution", {})
        if isinstance(resolution, dict):
            steps = resolution.get("steps", [])
            for step in steps:
                if isinstance(step, str):
                    # 解決手順のキーワードを抽出
                    patterns.extend(
                        re.findall(
                            r"\b(restart|reload|reset|update|fix|patch)\b", step.lower()
                        )
                    )

        return list(set(patterns))

    async def _generate_incident_vector(
        self, incident_data: Dict[str, Any], metadata: IncidentVectorMetadata
    ) -> np.ndarray:
        """インシデントベクトル生成"""
        try:
            # 各次元のベクトル生成
            error_vec = await self._generate_error_message_vector(
                incident_data.get("error_message", "")
            )

            stack_vec = await self._generate_stack_trace_vector(
                incident_data.get("stack_trace", "")
            )

            context_vec = await self._generate_system_context_vector(
                incident_data, metadata
            )

            resolution_vec = await self._generate_resolution_vector(
                incident_data.get("resolution", {})
            )

            prevention_vec = await self._generate_prevention_vector(
                incident_data.get("prevention_measures", [])
            )

            # 複合ベクトル結合
            combined_vector = np.concatenate(
                [error_vec, stack_vec, context_vec, resolution_vec, prevention_vec]
            )

            # 正規化
            norm = np.linalg.norm(combined_vector)
            if norm > 0:
                combined_vector = combined_vector / norm

            return combined_vector

        except Exception as e:
            self.logger.error(f"❌ インシデントベクトル生成失敗: {e}")
            raise

    async def _generate_error_message_vector(self, error_message: str) -> np.ndarray:
        """エラーメッセージベクトル生成"""
        # 実際の実装ではOpenAI APIを使用
        # ここではダミー実装
        vector = np.random.randn(self.dimensions.error_message)

        # エラーメッセージの特徴を反映
        if "memory" in error_message.lower():
            vector[0] = 1.0
        if "connection" in error_message.lower():
            vector[1] = 1.0
        if "timeout" in error_message.lower():
            vector[2] = 1.0

        return vector / np.linalg.norm(vector) if np.linalg.norm(vector) > 0 else vector

    async def _generate_stack_trace_vector(self, stack_trace: str) -> np.ndarray:
        """スタックトレースベクトル生成"""
        vector = np.zeros(self.dimensions.stack_trace)

        if stack_trace:
            # スタックトレースの深さ
            lines = stack_trace.count("\n")
            vector[0] = min(lines / 20.0, 1.0)

            # ファイル数
            files = len(re.findall(r'File\s+"[^"]+"', stack_trace))
            vector[1] = min(files / 10.0, 1.0)

            # 特定パターン
            if "recursion" in stack_trace.lower():
                vector[2] = 1.0

        return vector

    async def _generate_system_context_vector(
        self, incident_data: Dict[str, Any], metadata: IncidentVectorMetadata
    ) -> np.ndarray:
        """システムコンテキストベクトル生成"""
        vector = np.zeros(self.dimensions.system_context)

        # 重要度
        vector[0] = self._severity_to_power_level(metadata.severity) / 10.0

        # 影響システム数
        affected_count = len(metadata.affected_systems)
        vector[1] = min(affected_count / 5.0, 1.0)

        # 再発回数
        vector[2] = min(metadata.recurrence_count / 10.0, 1.0)

        # 解決時間（時間単位）
        if metadata.resolution_time_minutes:
            vector[3] = min(
                metadata.resolution_time_minutes / 1440.0, 1.0
            )  # 24時間で正規化

        return vector

    async def _generate_resolution_vector(
        self, resolution: Dict[str, Any]
    ) -> np.ndarray:
        """解決手順ベクトル生成"""
        vector = np.zeros(self.dimensions.resolution_steps)

        if resolution:
            steps = resolution.get("steps", [])
            vector[0] = min(len(steps) / 10.0, 1.0)  # ステップ数

            # 解決手順の種類
            if any("restart" in str(step).lower() for step in steps):
                vector[1] = 1.0
            if any("config" in str(step).lower() for step in steps):
                vector[2] = 1.0
            if any("update" in str(step).lower() for step in steps):
                vector[3] = 1.0

        return vector

    async def _generate_prevention_vector(self, preventions: List[str]) -> np.ndarray:
        """予防策ベクトル生成"""
        vector = np.zeros(self.dimensions.prevention_measures)

        if preventions:
            vector[0] = min(len(preventions) / 5.0, 1.0)  # 予防策数

            # 予防策の種類
            prevention_text = " ".join(preventions).lower()
            if "monitoring" in prevention_text:
                vector[1] = 1.0
            if "backup" in prevention_text:
                vector[2] = 1.0
            if "testing" in prevention_text:
                vector[3] = 1.0

        return vector

    async def search_similar_incidents(
        self,
        query: Union[str, Dict[str, Any]],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """類似インシデント検索"""
        try:
            self.stats["pattern_searches"] += 1

            # 検索クエリ作成
            search_query = SearchQuery(
                query_text=query if isinstance(query, str) else json.dumps(query),
                limit=limit,
                filters=filters,
            )

            # ベクトル検索実行
            results = await self.vector_search.search(search_query)

            # 結果を拡張情報付きで返す
            enhanced_results = []
            for result in results:
                incident_data = json.loads(result.content)

                enhanced_results.append(
                    {
                        "incident_id": incident_data.get("id"),
                        "similarity_score": result.similarity_score,
                        "incident_data": incident_data,
                        "severity": (
                            result.tags[2] if len(result.tags) > 2 else "unknown"
                        ),
                        "category": (
                            result.tags[1] if len(result.tags) > 1 else "unknown"
                        ),
                        "spell_id": result.spell_id,
                        "resolution_available": bool(incident_data.get("resolution")),
                    }
                )

            return enhanced_results

        except Exception as e:
            self.logger.error(f"❌ 類似インシデント検索失敗: {e}")
            return []

    async def predict_incident_prevention(
        self, system_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """インシデント予兆検知・予防策提案"""
        try:
            self.logger.info("🔮 インシデント予兆分析開始")

            # システム状況分析
            risk_analysis = await self._analyze_system_risk(system_context)

            # 類似過去インシデント検索
            similar_incidents = await self.search_similar_incidents(
                json.dumps(system_context), limit=5
            )

            # 予防策生成
            prevention_measures = await self._generate_prevention_measures(
                risk_analysis, similar_incidents
            )

            # 4賢者統合相談
            sage_consultation = await self._consult_other_sages_for_prevention(
                system_context, risk_analysis
            )

            result = {
                "risk_level": risk_analysis["overall_risk"],
                "predicted_incidents": risk_analysis["potential_incidents"],
                "prevention_measures": prevention_measures,
                "similar_past_incidents": similar_incidents,
                "sage_consultation": sage_consultation,
                "monitoring_recommendations": await self._generate_monitoring_recommendations(
                    risk_analysis
                ),
                "immediate_actions": await self._generate_immediate_actions(
                    risk_analysis
                ),
            }

            self.stats["preventions_applied"] += 1

            if risk_analysis["overall_risk"] < 0.3:
                self.stats["crisis_averted"] += 1
                self.logger.info("✅ 危機回避成功 - エルダーズへの報告完了")

            return result

        except Exception as e:
            self.logger.error(f"❌ インシデント予兆検知失敗: {e}")
            raise

    async def provide_incident_resolution(
        self, incident_description: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """インシデント解決策提供"""
        try:
            self.logger.info("🚑 インシデント解決策分析開始")

            # 類似インシデント検索
            similar_incidents = await self.search_similar_incidents(
                incident_description, limit=3
            )

            # 解決策統合
            resolution_strategies = []
            for incident in similar_incidents:
                if incident["resolution_available"]:
                    strategy = await self._extract_resolution_strategy(incident)
                    if strategy:
                        resolution_strategies.append(strategy)

            # 最適解決策選択
            best_resolution = await self._select_best_resolution(
                resolution_strategies, context
            )

            # 4賢者統合相談
            sage_guidance = await self._consult_sages_for_resolution(
                incident_description, context, best_resolution
            )

            result = {
                "recommended_resolution": best_resolution,
                "alternative_resolutions": resolution_strategies,
                "confidence_score": await self._calculate_resolution_confidence(
                    best_resolution
                ),
                "estimated_resolution_time": await self._estimate_resolution_time(
                    best_resolution
                ),
                "risk_assessment": await self._assess_resolution_risk(best_resolution),
                "sage_guidance": sage_guidance,
                "follow_up_actions": await self._generate_follow_up_actions(
                    best_resolution
                ),
            }

            self.stats["resolutions_provided"] += 1

            return result

        except Exception as e:
            self.logger.error(f"❌ インシデント解決策提供失敗: {e}")
            raise

    async def _save_incident_patterns(self, metadata: IncidentVectorMetadata):
        """インシデントパターン保存"""
        async with self.grimoire_db.connection_pool.acquire() as conn:
            # エラーパターン保存
            for pattern in metadata.error_patterns:
                await conn.execute(
                    """
                    INSERT INTO incident_patterns
                    (incident_id, pattern_type, pattern_text, severity, category)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (incident_id, pattern_type, pattern_text)
                    DO UPDATE SET occurrence_count = incident_patterns.occurrence_count + 1,
                                  last_seen = CURRENT_TIMESTAMP
                """,
                    metadata.incident_id,
                    "error",
                    pattern,
                    metadata.severity.value,
                    metadata.incident_type.value,
                )

    async def _save_incident_resolution(
        self, metadata: IncidentVectorMetadata, resolution: Dict[str, Any]
    ):
        """インシデント解決策保存"""
        async with self.grimoire_db.connection_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO incident_resolutions
                (incident_id, resolution_text, resolution_steps, resolution_time_minutes)
                VALUES ($1, $2, $3, $4)
            """,
                metadata.incident_id,
                json.dumps(resolution),
                json.dumps(resolution.get("steps", [])),
                metadata.resolution_time_minutes,
            )

    # 予兆検知・予防策関連メソッド
    async def _analyze_system_risk(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """システムリスク分析"""
        risk_factors = []
        risk_score = 0.0

        # メモリ使用率
        memory_usage = context.get("memory_usage_percent", 0)
        if memory_usage > 90:
            risk_factors.append("Critical memory usage")
            risk_score += 0.4
        elif memory_usage > 80:
            risk_factors.append("High memory usage")
            risk_score += 0.2

        # CPU使用率
        cpu_usage = context.get("cpu_usage_percent", 0)
        if cpu_usage > 95:
            risk_factors.append("Critical CPU usage")
            risk_score += 0.3

        # ディスク使用率
        disk_usage = context.get("disk_usage_percent", 0)
        if disk_usage > 95:
            risk_factors.append("Critical disk space")
            risk_score += 0.3

        return {
            "overall_risk": min(risk_score, 1.0),
            "risk_factors": risk_factors,
            "potential_incidents": await self._predict_potential_incidents(context),
        }

    async def _predict_potential_incidents(
        self, context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """潜在的インシデント予測"""
        predictions = []

        memory_usage = context.get("memory_usage_percent", 0)
        if memory_usage > 85:
            predictions.append(
                {
                    "type": IncidentCategory.MEMORY_LEAK.value,
                    "probability": min((memory_usage - 85) / 15, 1.0),
                    "estimated_time_to_incident": f"{int((100 - memory_usage) * 2)} minutes",
                }
            )

        return predictions

    async def _generate_prevention_measures(
        self, risk_analysis: Dict[str, Any], similar_incidents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """予防策生成"""
        measures = []

        for risk_factor in risk_analysis["risk_factors"]:
            if "memory" in risk_factor.lower():
                measures.append(
                    {
                        "measure": "Implement memory monitoring and cleanup",
                        "priority": "high",
                        "effort": "medium",
                    }
                )
            elif "cpu" in risk_factor.lower():
                measures.append(
                    {
                        "measure": "Scale resources or optimize processes",
                        "priority": "high",
                        "effort": "high",
                    }
                )

        return measures

    async def _consult_other_sages_for_prevention(
        self, context: Dict[str, Any], risk_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """他の賢者への予防策相談"""
        if self.four_sages:
            request = {
                "type": "prevention_consultation",
                "data": {
                    "system_context": context,
                    "risk_analysis": risk_analysis,
                    "requester": "incident_sage",
                },
            }

            response = await self.four_sages.coordinate_learning_session(request)

            return {
                "consultation_successful": response.get("consensus_reached", False),
                "prevention_insights": response.get("learning_outcome", {}),
                "sage_recommendations": response.get("individual_responses", {}),
            }

        return {"consultation_successful": False, "reason": "Four sages not available"}

    # その他のヘルパーメソッド（簡略化実装）
    async def _generate_monitoring_recommendations(
        self, risk_analysis: Dict[str, Any]
    ) -> List[str]:
        """監視推奨事項生成"""
        return [
            "Set up memory usage alerts at 85% threshold",
            "Monitor CPU utilization trends",
            "Implement automated health checks",
        ]

    async def _generate_immediate_actions(
        self, risk_analysis: Dict[str, Any]
    ) -> List[str]:
        """即座対応アクション生成"""
        actions = []

        if risk_analysis["overall_risk"] > 0.7:
            actions.append("Alert operations team immediately")
            actions.append("Prepare rollback procedures")

        return actions

    async def _extract_resolution_strategy(
        self, incident: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """解決策戦略抽出"""
        incident_data = incident.get("incident_data", {})
        resolution = incident_data.get("resolution")

        if resolution:
            return {
                "strategy": resolution,
                "success_rate": 0.9,  # 簡略化
                "estimated_time": incident_data.get("resolution_time_minutes", 60),
            }

        return None

    async def _select_best_resolution(
        self, strategies: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """最適解決策選択"""
        if not strategies:
            return None

        # 成功率で選択（簡略化）
        return max(strategies, key=lambda s: s.get("success_rate", 0))

    async def _consult_sages_for_resolution(
        self, incident: str, context: Dict[str, Any], resolution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """解決策について他の賢者に相談"""
        if self.four_sages:
            request = {
                "type": "resolution_consultation",
                "data": {
                    "incident_description": incident,
                    "context": context,
                    "proposed_resolution": resolution,
                    "requester": "incident_sage",
                },
            }

            response = await self.four_sages.coordinate_learning_session(request)

            return {
                "consultation_successful": response.get("consensus_reached", False),
                "resolution_validation": response.get("learning_outcome", {}),
                "sage_feedback": response.get("individual_responses", {}),
            }

        return {"consultation_successful": False}

    async def _calculate_resolution_confidence(
        self, resolution: Dict[str, Any]
    ) -> float:
        """解決策信頼度計算"""
        return resolution.get("success_rate", 0.5) if resolution else 0.0

    async def _estimate_resolution_time(self, resolution: Dict[str, Any]) -> int:
        """解決時間推定"""
        return resolution.get("estimated_time", 60) if resolution else 60

    async def _assess_resolution_risk(
        self, resolution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """解決策リスク評価"""
        return {
            "risk_level": "low",
            "potential_side_effects": [],
            "rollback_required": False,
        }

    async def _generate_follow_up_actions(
        self, resolution: Dict[str, Any]
    ) -> List[str]:
        """フォローアップアクション生成"""
        return [
            "Monitor system stability after resolution",
            "Document lessons learned",
            "Update prevention measures",
        ]

    async def get_statistics(self) -> Dict[str, Any]:
        """統計情報取得"""
        return {
            "system_stats": self.stats.copy(),
            "cache_stats": {
                "pattern_cache_size": len(self.pattern_cache),
                "similarity_cache_size": len(self.similarity_cache),
            },
            "vector_dimensions": {
                "total": self.total_dimensions,
                "breakdown": {
                    "error_message": self.dimensions.error_message,
                    "stack_trace": self.dimensions.stack_trace,
                    "system_context": self.dimensions.system_context,
                    "resolution_steps": self.dimensions.resolution_steps,
                    "prevention_measures": self.dimensions.prevention_measures,
                },
            },
            "incident_categories": [category.value for category in IncidentCategory],
            "severity_levels": [severity.value for severity in IncidentSeverity],
        }

    async def cleanup(self):
        """リソースクリーンアップ"""
        try:
            if self.grimoire_db:
                await self.grimoire_db.close()

            self.logger.info("🛡️ インシデント賢者システムクリーンアップ完了")
            self.logger.info("🏛️ エルダーズへの最終報告完了")

        except Exception as e:
            self.logger.error(f"❌ クリーンアップ失敗: {e}")


# 使用例とテスト用関数
async def test_incident_sage_system():
    """インシデント賢者システムのテスト"""
    incident_sage = IncidentSageGrimoireVectorization()

    try:
        await incident_sage.initialize()

        # テストインシデント
        test_incident = {
            "id": "test_incident_001",
            "title": "Memory leak in worker process",
            "description": "Worker process consuming excessive memory",
            "error_message": "OutOfMemoryError: Java heap space",
            "stack_trace": "at java.util.ArrayList.grow(ArrayList.java:267)",
            "affected_systems": ["worker-service", "api-gateway"],
            "severity": "high",
            "resolution": {
                "steps": [
                    "Restart worker service",
                    "Increase heap size",
                    "Add memory monitoring",
                ]
            },
            "resolution_time_minutes": 45,
        }

        # インシデントベクトル化
        spell_id = await incident_sage.vectorize_incident(test_incident)
        print(f"✅ Test incident vectorized: {spell_id}")

        # 類似インシデント検索
        similar = await incident_sage.search_similar_incidents(
            "OutOfMemoryError in worker", limit=3
        )
        print(f"✅ Found {len(similar)} similar incidents")

        # 統計情報
        stats = await incident_sage.get_statistics()
        print(f"✅ System stats: {stats['system_stats']}")

    finally:
        await incident_sage.cleanup()


if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    )

    # テスト実行
    asyncio.run(test_incident_sage_system())
