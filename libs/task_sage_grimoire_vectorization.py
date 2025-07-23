#!/usr/bin/env python3
"""
Task Sage Grimoire Vectorization System
タスク賢者の魔法書ベクトル化実装

タスクの類似性検索、依存関係分析、優先順位の動的調整を実現
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from libs.claude_task_tracker import ClaudeTaskTracker
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


@dataclass
class TaskVectorMetadata:
    """タスクベクトル化メタデータ"""

    task_id: str
    task_type: str
    priority: int
    dependencies: List[str] = field(default_factory=list)
    estimated_duration: float = 0.0
    actual_duration: Optional[float] = None
    success_rate: float = 1.0
    execution_patterns: Dict[str, Any] = field(default_factory=dict)
    optimization_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TaskVectorDimensions:
    """タスクベクトル次元定義"""

    task_description: int = 768  # タスク内容の埋め込み
    task_context: int = 384  # コンテキスト情報
    task_dependencies: int = 256  # 依存関係グラフ
    task_outcomes: int = 384  # 成果物・結果


class TaskSageGrimoireVectorization:
    """タスク賢者魔法書ベクトル化システム"""

    def __init__(self, database_url:
        """初期化メソッド"""
    str = "postgresql://localhost/grimoire"):
        self.database_url = database_url
        self.logger = logging.getLogger(__name__)

        # コンポーネント
        self.grimoire_db = None
        self.vector_search = None
        self.evolution_engine = None
        self.task_tracker = None
        self.four_sages = None

        # ベクトル次元
        self.dimensions = TaskVectorDimensions()
        self.total_dimensions = (
            self.dimensions.task_description
            + self.dimensions.task_context
            + self.dimensions.task_dependencies
            + self.dimensions.task_outcomes
        )

        # キャッシュ
        self.dependency_cache = {}
        self.similarity_cache = {}

        # 統計情報
        self.stats = {
            "tasks_vectorized": 0,
            "similarity_searches": 0,
            "dependency_analyses": 0,
            "priority_adjustments": 0,
            "optimization_cycles": 0,
        }

    async def initialize(self):
        """システム初期化"""
        try:
            # 魔法書データベース初期化
            self.grimoire_db = GrimoireDatabase(self.database_url)
            await self.grimoire_db.initialize()

            # ベクトル検索エンジン初期化
            self.vector_search = GrimoireVectorSearch(database=self.grimoire_db)
            await self.vector_search.initialize()

            # 進化エンジン初期化
            self.evolution_engine = EvolutionEngine(database=self.grimoire_db)
            await self.evolution_engine.initialize()

            # タスクトラッカー統合
            self.task_tracker = ClaudeTaskTracker()

            # 4賢者統合システム
            self.four_sages = FourSagesIntegration()

            # タスク賢者専用テーブル作成
            await self._create_task_sage_tables()

            self.logger.info(
                "Task Sage Grimoire Vectorization initialized successfully"
            )

        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            raise

    async def _create_task_sage_tables(self):
        """タスク賢者専用テーブル作成"""
        try:
            # PostgreSQL接続を使用してテーブル作成
            async with self.grimoire_db.connection_pool.acquire() as conn:
                # タスク依存関係テーブル
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS task_dependencies (
                        id SERIAL PRIMARY KEY,
                        task_id TEXT NOT NULL,
                        dependency_id TEXT NOT NULL,
                        dependency_type TEXT,
                        strength FLOAT DEFAULT 1.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(task_id, dependency_id)
                    )
                """
                )

                # タスク実行履歴テーブル
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS task_execution_history (
                        id SERIAL PRIMARY KEY,
                        task_id TEXT NOT NULL,
                        execution_start TIMESTAMP,
                        execution_end TIMESTAMP,
                        success BOOLEAN,
                        performance_metrics JSONB,
                        optimization_applied JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # タスク類似性キャッシュテーブル
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS task_similarity_cache (
                        id SERIAL PRIMARY KEY,
                        task_id_1 TEXT NOT NULL,
                        task_id_2 TEXT NOT NULL,
                        similarity_score FLOAT,
                        similarity_dimensions JSONB,
                        calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(task_id_1, task_id_2)
                    )
                """
                )

            self.logger.info("Task Sage specific tables created")

        except Exception as e:
            self.logger.error(f"Failed to create task sage tables: {e}")
            raise

    async def vectorize_task(self, task_data: Dict[str, Any]) -> str:
        """タスクのベクトル化"""
        try:
            # タスクメタデータ準備
            task_metadata = TaskVectorMetadata(
                task_id=task_data.get("id", f"task_{datetime.now().timestamp()}"),
                task_type=task_data.get("type", "general"),
                priority=task_data.get("priority", 5),
                dependencies=task_data.get("dependencies", []),
                estimated_duration=task_data.get("estimated_duration", 0.0),
            )

            # 複合ベクトル生成
            task_vector = await self._generate_task_vector(task_data, task_metadata)

            # 魔法書メタデータ作成
            spell_metadata = SpellMetadata(
                id=str(uuid.uuid4()),
                spell_name=f"task_{task_metadata.task_id}",
                content=json.dumps(task_data),
                spell_type=SpellType.PROCEDURE,
                magic_school=MagicSchool.TASK_ORACLE,
                tags=[
                    "task_sage",
                    task_metadata.task_type,
                    f"priority_{task_metadata.priority}",
                ],
                power_level=task_metadata.priority,
                casting_frequency=0,
                last_cast_at=None,
                is_eternal=False,
                evolution_history=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                version=1,
            )

            # データベースに保存
            spell_id = await self.grimoire_db.create_spell(spell_metadata)

            # ベクトルインデックス追加（タスクメタデータも含める）
            spell_with_task_metadata = {
                **spell_metadata.__dict__,
                "task_metadata": task_metadata.__dict__,
                "vector_dimensions": {
                    "description": self.dimensions.task_description,
                    "context": self.dimensions.task_context,
                    "dependencies": self.dimensions.task_dependencies,
                    "outcomes": self.dimensions.task_outcomes,
                },
            }
            await self.vector_search.index_spell(spell_id, spell_metadata)

            # 依存関係の保存
            await self._save_task_dependencies(
                task_metadata.task_id, task_metadata.dependencies
            )

            # 統計更新
            self.stats["tasks_vectorized"] += 1

            self.logger.info(f"Task vectorized successfully: {task_metadata.task_id}")
            return spell_id

        except Exception as e:
            self.logger.error(f"Task vectorization failed: {e}")
            raise

    async def _generate_task_vector(
        self, task_data: Dict[str, Any], metadata: TaskVectorMetadata
    ) -> np.ndarray:
        """タスクベクトル生成"""
        try:
            # 各次元のベクトル生成
            description_vec = await self._generate_description_vector(
                task_data.get("description", ""), task_data.get("title", "")
            )

            context_vec = await self._generate_context_vector(
                task_data.get("context", {}), metadata
            )

            dependency_vec = await self._generate_dependency_vector(
                metadata.dependencies, task_data.get("dependency_weights", {})
            )

            outcome_vec = await self._generate_outcome_vector(
                task_data.get("expected_outcomes", []),
                task_data.get("success_criteria", {}),
            )

            # 複合ベクトル結合
            combined_vector = np.concatenate(
                [description_vec, context_vec, dependency_vec, outcome_vec]
            )

            # 正規化
            norm = np.linalg.norm(combined_vector)
            if norm > 0:
                combined_vector = combined_vector / norm

            return combined_vector

        except Exception as e:
            self.logger.error(f"Vector generation failed: {e}")
            raise

    async def search_similar_tasks(
        self,
        query: Union[str, Dict[str, Any]],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """類似タスク検索"""
        try:
            self.stats["similarity_searches"] += 1

            # クエリベクトル生成
            if isinstance(query, str):
                query_vector = await self._generate_description_vector(query, "")
                # 他の次元はゼロパディング
                query_vector = np.pad(
                    query_vector,
                    (0, self.total_dimensions - len(query_vector)),
                    mode="constant",
                )
            else:
                # 完全なタスクデータからベクトル生成
                temp_metadata = TaskVectorMetadata(
                    task_id="query",
                    task_type=query.get("type", "general"),
                    priority=query.get("priority", 5),
                )
                query_vector = await self._generate_task_vector(query, temp_metadata)

            # 検索クエリ作成（テキストベースの検索としてクエリを設定）
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
                task_data = json.loads(result.content)
                # タスクデータから直接メタデータを取得
                task_id = task_data.get("id", "unknown")

                enhanced_results.append(
                    {
                        "task_id": task_id,
                        "similarity_score": result.similarity_score,
                        "task_data": task_data,
                        "task_type": task_data.get("type", "general"),
                        "priority": result.power_level,  # power_levelを優先度として使用
                        "dependencies": task_data.get("dependencies", []),
                        "estimated_duration": task_data.get("estimated_duration", 0),
                        "spell_id": result.spell_id,
                    }
                )

            return enhanced_results

        except Exception as e:
            self.logger.error(f"Similar task search failed: {e}")
            return []

    async def analyze_task_dependencies(
        self, task_id: str, depth: int = 3
    ) -> Dict[str, Any]:
        """タスク依存関係分析"""
        try:
            self.stats["dependency_analyses"] += 1

            # キャッシュチェック
            cache_key = f"{task_id}_{depth}"
            if cache_key in self.dependency_cache:
                return self.dependency_cache[cache_key]

            # 依存関係グラフ構築
            dependency_graph = await self._build_dependency_graph(task_id, depth)

            # 最適実行順序計算
            execution_order = await self._calculate_optimal_execution_order(
                dependency_graph
            )

            # クリティカルパス分析
            critical_path = await self._analyze_critical_path(dependency_graph)

            # 並行実行可能タスク特定
            parallel_tasks = await self._identify_parallel_tasks(dependency_graph)

            analysis_result = {
                "task_id": task_id,
                "dependency_graph": dependency_graph,
                "optimal_execution_order": execution_order,
                "critical_path": critical_path,
                "parallel_execution_groups": parallel_tasks,
                "total_dependencies": len(dependency_graph) - 1,
                "max_depth_reached": depth,
                "analysis_timestamp": datetime.now().isoformat(),
            }

            # キャッシュ保存
            self.dependency_cache[cache_key] = analysis_result

            return analysis_result

        except Exception as e:
            self.logger.error(f"Dependency analysis failed: {e}")
            raise

    async def optimize_task_priority(
        self, task_batch: List[str], optimization_criteria: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """タスク優先順位の動的最適化"""
        try:
            self.stats["priority_adjustments"] += 1

            # 各タスクの情報取得
            task_infos = []
            for task_id in task_batch:
                task_info = await self._get_task_info(task_id)
                if task_info:
                    task_infos.append(task_info)

            # 最適化基準に基づくスコアリング
            scored_tasks = []
            for task_info in task_infos:
                score = await self._calculate_priority_score(
                    task_info, optimization_criteria
                )
                scored_tasks.append(
                    {
                        "task_id": task_info["task_id"],
                        "original_priority": task_info.get("priority", 5),
                        "optimized_priority": score,
                        "task_info": task_info,
                        "optimization_factors": await self._get_optimization_factors(
                            task_info
                        ),
                    }
                )

            # スコアに基づいてソート
            scored_tasks.sort(key=lambda x: x["optimized_priority"], reverse=True)

            # 優先順位を1-10にマッピング
            for i, task in enumerate(scored_tasks):
                task["final_priority"] = min(10, max(1, 10 - i))

            # 最適化履歴を保存
            await self._save_optimization_history(scored_tasks, optimization_criteria)

            return scored_tasks

        except Exception as e:
            self.logger.error(f"Priority optimization failed: {e}")
            raise

    async def learn_from_execution(
        self, task_id: str, execution_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """タスク実行からの学習"""
        try:
            self.stats["optimization_cycles"] += 1

            # 実行データ保存
            await self._save_execution_history(task_id, execution_data)

            # パフォーマンス分析
            performance_analysis = await self._analyze_task_performance(
                task_id, execution_data
            )

            # 類似タスクへの学習適用
            similar_tasks = await self.search_similar_tasks(
                {"task_id": task_id}, limit=5
            )

            learning_applications = []
            for similar_task in similar_tasks:
                if similar_task["task_id"] != task_id:
                    application = await self._apply_learning_to_task(
                        similar_task["task_id"], performance_analysis
                    )
                    learning_applications.append(application)

            # ベクトル空間の更新
            await self._update_task_vector_space(task_id, performance_analysis)

            return {
                "task_id": task_id,
                "performance_analysis": performance_analysis,
                "learning_applied_to": learning_applications,
                "vector_space_updated": True,
                "improvement_recommendations": await self._generate_improvement_recommendations(
                    performance_analysis
                ),
            }

        except Exception as e:
            self.logger.error(f"Learning from execution failed: {e}")
            raise

    async def integrate_with_other_sages(
        self, task_id: str, integration_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """他の賢者との統合"""
        try:
            integration_results = {}

            # ナレッジ賢者との統合
            if integration_request.get("knowledge_sage", True):
                knowledge_integration = await self._integrate_with_knowledge_sage(
                    task_id, integration_request.get("knowledge_query", {})
                )
                integration_results["knowledge_sage"] = knowledge_integration

            # インシデント賢者との統合
            if integration_request.get("incident_sage", True):
                incident_integration = await self._integrate_with_incident_sage(
                    task_id, integration_request.get("risk_assessment", True)
                )
                integration_results["incident_sage"] = incident_integration

            # RAG賢者との統合
            if integration_request.get("rag_sage", True):
                rag_integration = await self._integrate_with_rag_sage(
                    task_id, integration_request.get("context_enhancement", True)
                )
                integration_results["rag_sage"] = rag_integration

            # 統合結果の合成
            synthesis = await self._synthesize_sage_insights(integration_results)

            return {
                "task_id": task_id,
                "sage_integrations": integration_results,
                "synthesis": synthesis,
                "recommendations": await self._generate_integrated_recommendations(
                    synthesis
                ),
            }

        except Exception as e:
            self.logger.error(f"Sage integration failed: {e}")
            raise

    # ヘルパーメソッド

    async def _generate_description_vector(
        self, description: str, title: str
    ) -> np.ndarray:
        """説明文ベクトル生成"""
        # 実際の実装ではOpenAI APIなどを使用
        # ここではダミー実装
        combined_text = f"{title} {description}"
        vector = np.random.randn(self.dimensions.task_description)
        return vector / np.linalg.norm(vector)

    async def _generate_context_vector(
        self, context: Dict[str, Any], metadata: TaskVectorMetadata
    ) -> np.ndarray:
        """コンテキストベクトル生成"""
        # コンテキスト情報を数値化
        vector = np.zeros(self.dimensions.task_context)

        # 優先度を反映
        vector[0] = metadata.priority / 10.0

        # タスクタイプをone-hot encoding
        task_types = ["general", "bug_fix", "feature", "refactor", "test", "docs"]
        if metadata.task_type in task_types:
            idx = task_types.index(metadata.task_type)
            vector[idx + 1] = 1.0

        # その他のコンテキスト情報
        if context:
            # プロジェクトフェーズ、緊急度など
            vector[10] = context.get("urgency", 0.5)
            vector[11] = context.get("complexity", 0.5)

        return vector / np.linalg.norm(vector) if np.linalg.norm(vector) > 0 else vector

    async def _generate_dependency_vector(
        self, dependencies: List[str], weights: Dict[str, float]
    ) -> np.ndarray:
        """依存関係ベクトル生成"""
        vector = np.zeros(self.dimensions.task_dependencies)

        if dependencies:
            # 依存関係の数
            vector[0] = min(len(dependencies) / 10.0, 1.0)

            # 依存関係の重み付け
            for i, dep in enumerate(dependencies[:10]):  # 最大10個まで
                weight = weights.get(dep, 1.0)
                vector[i + 1] = weight

        return vector / np.linalg.norm(vector) if np.linalg.norm(vector) > 0 else vector

    async def _generate_outcome_vector(
        self, outcomes: List[str], criteria: Dict[str, Any]
    ) -> np.ndarray:
        """成果物ベクトル生成"""
        vector = np.zeros(self.dimensions.task_outcomes)

        # 成果物の数
        if outcomes:
            vector[0] = min(len(outcomes) / 5.0, 1.0)

        # 成功基準の複雑さ
        if criteria:
            vector[1] = min(len(criteria) / 10.0, 1.0)

        return vector / np.linalg.norm(vector) if np.linalg.norm(vector) > 0 else vector

    async def _save_task_dependencies(self, task_id: str, dependencies: List[str]):
        """タスク依存関係保存"""
        async with self.grimoire_db.connection_pool.acquire() as conn:
            for dep_id in dependencies:
                await conn.execute(
                    """
                    INSERT INTO task_dependencies (task_id, dependency_id, dependency_type)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (task_id, dependency_id) DO NOTHING
                """,
                    task_id,
                    dep_id,
                    "direct",
                )

    async def _build_dependency_graph(self, task_id: str, depth: int) -> Dict[str, Any]:
        """依存関係グラフ構築"""
        graph = {"nodes": {}, "edges": []}
        visited = set()

        async def traverse(tid:
            """traverseメソッド"""
        str, current_depth: int):
            if tid in visited or current_depth > depth:
                return

            visited.add(tid)

            # ノード情報取得
            task_info = await self._get_task_info(tid)
            if task_info:
                graph["nodes"][tid] = task_info

                # 依存関係取得
                async with self.grimoire_db.connection_pool.acquire() as conn:
                    deps = await conn.fetch(
                        """
                        SELECT dependency_id, dependency_type, strength
                        FROM task_dependencies
                        WHERE task_id = $1
                    """,
                        tid,
                    )

                for dep in deps:
                    dep_id = dep["dependency_id"]
                    graph["edges"].append(
                        {
                            "from": tid,
                            "to": dep_id,
                            "type": dep["dependency_type"],
                            "strength": dep["strength"],
                        }
                    )

                    # 再帰的に探索
                    await traverse(dep_id, current_depth + 1)

        await traverse(task_id, 0)
        return graph

    async def _calculate_optimal_execution_order(
        self, graph: Dict[str, Any]
    ) -> List[str]:
        """最適実行順序計算（トポロジカルソート）"""
        # 入次数計算
        in_degree = {node: 0 for node in graph["nodes"]}
        adj_list = {node: [] for node in graph["nodes"]}

        for edge in graph["edges"]:
            adj_list[edge["to"]].append(edge["from"])
            in_degree[edge["from"]] += 1

        # トポロジカルソート
        queue = [node for node, degree in in_degree.items() if degree == 0]
        order = []

        while queue:
            node = queue.pop(0)
            order.append(node)

            for neighbor in adj_list.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return order

    async def _analyze_critical_path(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        """クリティカルパス分析"""
        # 簡略化された実装
        # 実際はCPM（Critical Path Method）アルゴリズムを使用
        nodes = list(graph["nodes"].keys())

        if not nodes:
            return {"path": [], "duration": 0}

        # 各ノードの推定時間を使用
        durations = {}
        for node_id, node_info in graph["nodes"].items():
            durations[node_id] = node_info.get("estimated_duration", 1.0)

        # 最長パスを見つける（簡略化）
        max_path = nodes[:3] if len(nodes) >= 3 else nodes
        total_duration = sum(durations.get(n, 1.0) for n in max_path)

        return {
            "path": max_path,
            "duration": total_duration,
            "critical_tasks": max_path,
        }

    async def _identify_parallel_tasks(self, graph: Dict[str, Any]) -> List[List[str]]:
        """並行実行可能タスク特定"""
        # 依存関係がないタスクグループを特定
        execution_order = await self._calculate_optimal_execution_order(graph)

        # レベル分け
        levels = {}
        for task in execution_order:
            # 依存先の最大レベル + 1
            max_level = -1
            for edge in graph["edges"]:
                if edge["to"] == task and edge["from"] in levels:
                    max_level = max(max_level, levels[edge["from"]])
            levels[task] = max_level + 1

        # レベルごとにグループ化
        parallel_groups = {}
        for task, level in levels.items():
            if level not in parallel_groups:
                parallel_groups[level] = []
            parallel_groups[level].append(task)

        return list(parallel_groups.values())

    async def _get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """タスク情報取得"""
        # タスク賢者の魔法書から取得
        async with self.grimoire_db.connection_pool.acquire() as conn:
            results = await conn.fetchrow(
                """
                SELECT content, tags
                FROM knowledge_grimoire
                WHERE spell_name = $1 AND magic_school = 'task_oracle'
            """,
                f"task_{task_id}",
            )

        if results:
            task_data = json.loads(results["content"])
            return {"task_id": task_id, **task_data}
        return None

    async def _calculate_priority_score(
        self, task_info: Dict[str, Any], criteria: Dict[str, Any]
    ) -> float:
        """優先度スコア計算"""
        score = 0.0

        # 基本優先度
        base_priority = task_info.get("priority", 5)
        score += base_priority * criteria.get("priority_weight", 0.3)

        # 緊急度
        urgency = task_info.get("urgency", 0.5)
        score += urgency * 10 * criteria.get("urgency_weight", 0.3)

        # 依存関係の数（少ない方が高スコア）
        dependencies = len(task_info.get("dependencies", []))
        score += (10 - min(dependencies, 10)) * criteria.get("dependency_weight", 0.2)

        # 推定時間（短い方が高スコア）
        duration = task_info.get("estimated_duration", 1.0)
        score += (10 - min(duration / 8, 10)) * criteria.get("duration_weight", 0.2)

        return score

    async def _get_optimization_factors(
        self, task_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """最適化要因取得"""
        return {
            "original_priority": task_info.get("priority", 5),
            "urgency": task_info.get("urgency", 0.5),
            "dependency_count": len(task_info.get("dependencies", [])),
            "estimated_duration": task_info.get("estimated_duration", 1.0),
            "task_type": task_info.get("task_type", "general"),
        }

    async def _save_optimization_history(
        self, optimized_tasks: List[Dict[str, Any]], criteria: Dict[str, Any]
    ):
        """最適化履歴保存"""
        for task in optimized_tasks:
            # タスクのメタデータ更新
            task_id = task["task_id"]
            optimization_data = {
                "timestamp": datetime.now().isoformat(),
                "original_priority": task["original_priority"],
                "optimized_priority": task["optimized_priority"],
                "final_priority": task["final_priority"],
                "criteria": criteria,
            }

            # 既存のタスク情報を取得して更新
            await self.grimoire_db.execute(
                """
                UPDATE spells
                SET metadata = metadata || %s
                WHERE spell_name = %s AND magic_school = 'task_sage'
            """,
                (
                    json.dumps({"optimization_history": [optimization_data]}),
                    f"task_{task_id}",
                ),
            )

    async def _save_execution_history(
        self, task_id: str, execution_data: Dict[str, Any]
    ):
        """実行履歴保存"""
        async with self.grimoire_db.connection_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO task_execution_history
                (task_id, execution_start, execution_end, success, performance_metrics, optimization_applied)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                task_id,
                execution_data.get("start_time"),
                execution_data.get("end_time"),
                execution_data.get("success", True),
                json.dumps(execution_data.get("performance_metrics", {})),
                json.dumps(execution_data.get("optimization_applied", {})),
            )

    async def _analyze_task_performance(
        self, task_id: str, execution_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """タスクパフォーマンス分析"""
        # 実行時間分析
        start_time = execution_data.get("start_time")
        end_time = execution_data.get("end_time")
        actual_duration = (
            (end_time - start_time).total_seconds() if start_time and end_time else 0
        )

        # 推定時間との比較
        task_info = await self._get_task_info(task_id)
        estimated_duration = (
            task_info.get("estimated_duration", 0) * 3600
        )  # 時間を秒に変換

        duration_variance = (
            (actual_duration - estimated_duration) / estimated_duration
            if estimated_duration > 0
            else 0
        )

        return {
            "actual_duration": actual_duration,
            "estimated_duration": estimated_duration,
            "duration_variance": duration_variance,
            "success": execution_data.get("success", True),
            "performance_score": (
                1.0 - abs(duration_variance) if abs(duration_variance) < 1 else 0
            ),
            "optimization_opportunities": await self._identify_optimization_opportunities(
                duration_variance, execution_data
            ),
        }

    async def _identify_optimization_opportunities(
        self, duration_variance: float, execution_data: Dict[str, Any]
    ) -> List[str]:
        """最適化機会の特定"""
        opportunities = []

        if duration_variance > 0.2:
            opportunities.append(
                "Task took longer than estimated - consider breaking down"
            )
        elif duration_variance < -0.2:
            opportunities.append("Task completed faster - update estimation algorithm")

        if execution_data.get("retry_count", 0) > 0:
            opportunities.append("Task required retries - improve error handling")

        if execution_data.get("resource_usage", {}).get("memory", 0) > 80:
            opportunities.append("High memory usage - optimize resource allocation")

        return opportunities

    async def _apply_learning_to_task(
        self, task_id: str, performance_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """学習をタスクに適用"""
        # タスク情報更新
        updates = {}

        # 推定時間の調整
        if abs(performance_analysis["duration_variance"]) > 0.1:
            new_estimate = performance_analysis["actual_duration"] / 3600  # 秒を時間に
            updates["estimated_duration"] = new_estimate

        # 最適化推奨事項の適用
        if performance_analysis["optimization_opportunities"]:
            updates["optimization_recommendations"] = performance_analysis[
                "optimization_opportunities"
            ]

        # メタデータ更新
        if updates:
            await self.grimoire_db.execute(
                """
                UPDATE spells
                SET metadata = metadata || %s
                WHERE spell_name = %s AND magic_school = 'task_sage'
            """,
                (json.dumps({"learning_applied": updates}), f"task_{task_id}"),
            )

        return {
            "task_id": task_id,
            "updates_applied": updates,
            "learning_timestamp": datetime.now().isoformat(),
        }

    async def _update_task_vector_space(
        self, task_id: str, performance_analysis: Dict[str, Any]
    ):
        """タスクベクトル空間更新"""
        # パフォーマンスに基づいてベクトルを微調整
        # 実際の実装では、より洗練されたアルゴリズムを使用

        # 現在のベクトル取得
        task_info = await self._get_task_info(task_id)
        if not task_info:
            return

        # パフォーマンススコアに基づく調整
        performance_score = performance_analysis.get("performance_score", 0.5)

        # ベクトルの再生成（パフォーマンスを考慮）
        adjusted_metadata = TaskVectorMetadata(
            task_id=task_id,
            task_type=task_info.get("task_type", "general"),
            priority=task_info.get("priority", 5),
            actual_duration=performance_analysis.get("actual_duration"),
        )

        new_vector = await self._generate_task_vector(task_info, adjusted_metadata)

        # ベクトルインデックス更新
        spell_name = f"task_{task_id}"
        await self.vector_search.update_vector(spell_name, new_vector.tolist())

    async def _generate_improvement_recommendations(
        self, performance_analysis: Dict[str, Any]
    ) -> List[str]:
        """改善推奨事項生成"""
        recommendations = []

        # パフォーマンススコアに基づく推奨
        score = performance_analysis.get("performance_score", 0.5)

        if score < 0.3:
            recommendations.append("Major estimation adjustment needed")
            recommendations.append("Consider task decomposition")
        elif score < 0.7:
            recommendations.append("Fine-tune estimation parameters")
            recommendations.append("Review dependency analysis")
        else:
            recommendations.append("Current approach is effective")
            recommendations.append("Minor optimizations may help")

        # 最適化機会に基づく推奨
        opportunities = performance_analysis.get("optimization_opportunities", [])
        recommendations.extend(opportunities)

        return recommendations

    async def _integrate_with_knowledge_sage(
        self, task_id: str, query: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ナレッジ賢者との統合"""
        # 4賢者統合システムを使用
        if self.four_sages:
            request = {
                "type": "knowledge_query",
                "data": {"task_id": task_id, "query": query, "requester": "task_sage"},
            }

            response = await self.four_sages.coordinate_learning_session(request)

            return {
                "integration_successful": response.get("consensus_reached", False),
                "knowledge_insights": response.get("learning_outcome", {}),
                "relevant_patterns": response.get("individual_responses", {}).get(
                    "knowledge_sage", {}
                ),
            }

        return {"integration_successful": False, "reason": "Four sages not initialized"}

    async def _integrate_with_incident_sage(
        self, task_id: str, risk_assessment: bool
    ) -> Dict[str, Any]:
        """インシデント賢者との統合"""
        if self.four_sages and risk_assessment:
            request = {
                "type": "risk_assessment",
                "data": {
                    "task_id": task_id,
                    "assessment_type": "pre_execution",
                    "requester": "task_sage",
                },
            }

            response = await self.four_sages.coordinate_learning_session(request)

            return {
                "integration_successful": response.get("consensus_reached", False),
                "risk_analysis": response.get("learning_outcome", {}),
                "potential_issues": response.get("individual_responses", {}).get(
                    "incident_sage", {}
                ),
            }

        return {
            "integration_successful": False,
            "reason": "Risk assessment not requested",
        }

    async def _integrate_with_rag_sage(
        self, task_id: str, context_enhancement: bool
    ) -> Dict[str, Any]:
        """RAG賢者との統合"""
        if self.four_sages and context_enhancement:
            request = {
                "type": "context_enhancement",
                "data": {
                    "task_id": task_id,
                    "enhancement_type": "semantic_expansion",
                    "requester": "task_sage",
                },
            }

            response = await self.four_sages.coordinate_learning_session(request)

            return {
                "integration_successful": response.get("consensus_reached", False),
                "enhanced_context": response.get("learning_outcome", {}),
                "semantic_insights": response.get("individual_responses", {}).get(
                    "rag_sage", {}
                ),
            }

        return {
            "integration_successful": False,
            "reason": "Context enhancement not requested",
        }

    async def _synthesize_sage_insights(
        self, integration_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """賢者の洞察を統合"""
        synthesis = {
            "integrated_insights": [],
            "cross_sage_patterns": [],
            "unified_recommendations": [],
        }

        # 各賢者の成功した統合から洞察を抽出
        for sage, result in integration_results.items():
            if result.get("integration_successful"):
                synthesis["integrated_insights"].append(
                    {
                        "sage": sage,
                        "key_insight": result.get("knowledge_insights")
                        or result.get("risk_analysis")
                        or result.get("enhanced_context", {}),
                    }
                )

        # クロス賢者パターンの特定
        if len(synthesis["integrated_insights"]) > 1:
            synthesis["cross_sage_patterns"].append(
                "Multiple sage perspectives available for comprehensive analysis"
            )

        return synthesis

    async def _generate_integrated_recommendations(
        self, synthesis: Dict[str, Any]
    ) -> List[str]:
        """統合推奨事項生成"""
        recommendations = []

        # 統合された洞察に基づく推奨
        insights_count = len(synthesis.get("integrated_insights", []))

        if insights_count >= 3:
            recommendations.append(
                "Full sage consensus achieved - proceed with high confidence"
            )
        elif insights_count >= 2:
            recommendations.append(
                "Partial sage consensus - consider additional validation"
            )
        else:
            recommendations.append("Limited sage input - gather more perspectives")

        # クロス賢者パターンに基づく推奨
        if synthesis.get("cross_sage_patterns"):
            recommendations.append("Leverage cross-sage insights for holistic approach")

        return recommendations

    async def get_statistics(self) -> Dict[str, Any]:
        """統計情報取得"""
        return {
            "system_stats": self.stats.copy(),
            "cache_stats": {
                "dependency_cache_size": len(self.dependency_cache),
                "similarity_cache_size": len(self.similarity_cache),
            },
            "vector_dimensions": {
                "total": self.total_dimensions,
                "breakdown": {
                    "description": self.dimensions.task_description,
                    "context": self.dimensions.task_context,
                    "dependencies": self.dimensions.task_dependencies,
                    "outcomes": self.dimensions.task_outcomes,
                },
            },
        }

    async def cleanup(self):
        """リソースクリーンアップ"""
        try:
            if self.grimoire_db:
                await self.grimoire_db.close()

            if self.vector_search:
                await self.vector_search.cleanup()

            if self.evolution_engine:
                await self.evolution_engine.cleanup()

            self.logger.info("Task Sage Grimoire Vectorization cleaned up")

        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
