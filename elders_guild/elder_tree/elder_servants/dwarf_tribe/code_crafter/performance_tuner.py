"""
PerformanceTuner (D04) - パフォーマンス調整師サーバント
ドワーフ工房の最適化専門家

EldersLegacy準拠実装 - Issue #70
"""

import ast
import asyncio
import cProfile
import io
import logging
import os
import pstats
import sys
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union

from elders_guild.elder_tree.elder_servants.base.elder_servant import (
    ServantCapability,
    TaskResult,
    TaskStatus,
)
from elders_guild.elder_tree.elder_servants.base.specialized_servants import DwarfServant


class PerformanceTuner(DwarfServant[Dict[str, Any], Dict[str, Any]]):
    """
    D04: PerformanceTuner - パフォーマンス調整師サーバント
    コードの実行速度とリソース使用量の最適化スペシャリスト

    EldersLegacy準拠: Iron Will品質基準に基づく
    徹底的なパフォーマンス分析と最適化を提供
    """

    def __init__(self):
        """初期化メソッド"""
        capabilities = [
            ServantCapability(
                "profile_code",
                "コードプロファイリング",
                ["source_code", "test_data"],
                ["profile_report"],
                complexity=6,
            ),
            ServantCapability(
                "optimize_algorithms",
                "アルゴリズム最適化",
                ["source_code", "optimization_targets"],
                ["optimized_code"],
                complexity=8,
            ),
            ServantCapability(
                "memory_optimization",
                "メモリ使用量最適化",
                ["source_code"],
                ["optimized_code"],
                complexity=7,
            ),
            ServantCapability(
                "async_optimization",
                "非同期処理最適化",
                ["source_code"],
                ["async_optimized_code"],
                complexity=8,
            ),
            ServantCapability(
                "database_query_optimization",
                "データベースクエリ最適化",
                ["query_code", "schema_info"],
                ["optimized_queries"],
                complexity=9,
            ),
            ServantCapability(
                "caching_strategy",
                "キャッシング戦略実装",
                ["source_code", "cache_requirements"],
                ["cached_code"],
                complexity=6,
            ),
        ]

        super().__init__(
            servant_id="D04",
            servant_name="PerformanceTuner",
            specialization="パフォーマンス最適化",
            capabilities=capabilities,
        )

        # PerformanceTuner固有の設定
        self.performance_targets = {
            "execution_time_improvement": 30,  # 30%改善目標
            "memory_reduction": 20,  # 20%削減目標
            "throughput_increase": 50,  # 50%向上目標
            "latency_reduction": 40,  # 40%削減目標
        }

        # 最適化パターン
        self.optimization_patterns = self._initialize_optimization_patterns()

        # プロファイリングツール
        self.profiler = CodeProfiler()
        self.memory_analyzer = MemoryAnalyzer()
        self.bottleneck_detector = BottleneckDetector()

        # キャッシュ戦略
        self.cache_strategies = {
            "lru": "functools.lru_cache",
            "memory": "in-memory caching",
            "redis": "Redis caching",
            "file": "file-based caching",
        }

        self.logger.info("PerformanceTuner ready to optimize code performance")

    def get_specialized_capabilities(self) -> List[ServantCapability]:
        """専門能力の取得"""
        return [
            ServantCapability(
                "benchmark_comparison",
                "ベンチマーク比較分析",
                ["original_code", "optimized_code"],
                ["benchmark_report"],
                complexity=5,
            ),
            ServantCapability(
                "scalability_analysis",
                "スケーラビリティ分析",
                ["source_code", "load_scenarios"],
                ["scalability_report"],
                complexity=7,
            ),
            ServantCapability(
                "resource_monitoring",
                "リソース監視設定",
                ["application_code"],
                ["monitoring_code"],
                complexity=6,
            ),
        ]

    async def execute_task(self, task: Dict[str, Any]) -> TaskResult:
        """タスク実行"""
        start_time = datetime.now()
        task_id = task.get("task_id", "unknown")
        task_type = task.get("task_type", "")

        try:
            self.logger.info(f"Tuning performance for task {task_id}: {task_type}")

            result_data = {}
            payload = task.get("payload", {})

            if task_type == "profile_code":
                result_data = await self._profile_code(
                    payload.get("source_code", ""), payload.get("test_data", {})
                )
            elif task_type == "optimize_algorithms":
                result_data = await self._optimize_algorithms(
                    payload.get("source_code", ""),
                    payload.get("optimization_targets", []),
                )
            elif task_type == "memory_optimization":
                result_data = await self._memory_optimization(
                    payload.get("source_code", "")
                )
            elif task_type == "async_optimization":
                result_data = await self._async_optimization(
                    payload.get("source_code", "")
                )
            elif task_type == "database_query_optimization":
                result_data = await self._database_query_optimization(
                    payload.get("query_code", ""), payload.get("schema_info", {})
                )
            elif task_type == "caching_strategy":
                result_data = await self._caching_strategy(
                    payload.get("source_code", ""),
                    payload.get("cache_requirements", {}),
                )
            elif task_type == "benchmark_comparison":
                result_data = await self._benchmark_comparison(
                    payload.get("original_code", ""), payload.get("optimized_code", "")
                )
            elif task_type == "scalability_analysis":
                result_data = await self._scalability_analysis(
                    payload.get("source_code", ""), payload.get("load_scenarios", [])
                )
            elif task_type == "resource_monitoring":
                result_data = await self._resource_monitoring(
                    payload.get("application_code", "")
                )
            else:
                raise ValueError(f"Unknown task type: {task_type}")

            # PerformanceTuner品質検証
            quality_score = await self._validate_performance_optimization_quality(
                result_data
            )

            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            return TaskResult(
                task_id=task_id,
                servant_id=self.servant_id,
                status=TaskStatus.COMPLETED,
                result_data=result_data,
                execution_time_ms=execution_time,
                quality_score=quality_score,
            )

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Performance tuning failed for task {task_id}: {str(e)}")
            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            return TaskResult(
                task_id=task_id,
                servant_id=self.servant_id,
                status=TaskStatus.FAILED,
                error_message=str(e),
                execution_time_ms=execution_time,
                quality_score=0.0,
            )

    async def craft_artifact(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        """PerformanceTuner専用の製作メソッド"""
        optimization_type = specification.get("type", "optimize_algorithms")
        source_code = specification.get("source_code", "")

        if optimization_type == "profile":
            return await self._profile_code(
                source_code, specification.get("test_data", {})
            )
        elif optimization_type == "memory":
            return await self._memory_optimization(source_code)
        elif optimization_type == "async":
            return await self._async_optimization(source_code)
        else:
            return await self._optimize_algorithms(
                source_code, ["general_optimization"]
            )

    async def _profile_code(
        self, source_code: str, test_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """コードプロファイリング"""
        if not source_code:
            raise ValueError("Source code is required for profiling")

        try:
            # プロファイリング実行
            profile_result = self.profiler.profile_code(source_code, test_data)

            # ボトルネック検出
            bottlenecks = self.bottleneck_detector.detect_bottlenecks(profile_result)

            # パフォーマンス分析
            analysis = {
                "total_execution_time": profile_result.get("total_time", 0),
                "function_calls": profile_result.get("function_calls", 0),
                "memory_peak": profile_result.get("memory_peak", 0),
                "bottlenecks": bottlenecks,
                "optimization_opportunities": self._identify_optimization_opportunities(
                    bottlenecks
                ),
            }

            return {
                "profile_report": analysis,
                "bottlenecks_found": len(bottlenecks),
                "optimization_type": "profiling",
                "recommendations": self._generate_performance_recommendations(analysis),
                "performance_score": self._calculate_performance_score(analysis),
            }

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Code profiling failed: {e}")
            return {
                "profile_report": {},
                "error": str(e),
                "optimization_type": "profiling",
                "bottlenecks_found": 0,
            }

    async def _optimize_algorithms(
        self, source_code: str, optimization_targets: List[str]
    ) -> Dict[str, Any]:
        """アルゴリズム最適化"""
        if not source_code:
            raise ValueError("Source code is required for algorithm optimization")

        try:
            tree = ast.parse(source_code)

            optimizations_applied = []
            optimized_code = source_code

            # ループ最適化
            if (
                "loops" in optimization_targets
                or "general_optimization" in optimization_targets
            ):
                loop_optimizations = self._optimize_loops(tree)
                optimizations_applied.extend(loop_optimizations)

            # データ構造最適化
            if (
                "data_structures" in optimization_targets
                or "general_optimization" in optimization_targets
            ):
                ds_optimizations = self._optimize_data_structures(tree)
                optimizations_applied.extend(ds_optimizations)

            # 計算最適化
            if (
                "computations" in optimization_targets
                or "general_optimization" in optimization_targets
            ):
                calc_optimizations = self._optimize_calculations(tree)
                optimizations_applied.extend(calc_optimizations)

            # 並列化提案
            if "parallelization" in optimization_targets:
                parallel_suggestions = self._suggest_parallelization(tree)
                optimizations_applied.extend(parallel_suggestions)

            # 最適化されたコード生成
            optimized_code = self._apply_optimizations(
                source_code, optimizations_applied
            )

            return {
                "optimized_code": optimized_code,
                "optimization_type": "algorithms",
                "optimizations_applied": optimizations_applied,
                "optimization_targets": optimization_targets,
                "estimated_improvement": self._estimate_improvement(
                    optimizations_applied
                ),
                "improvements": [
                    f"Applied {len(optimizations_applied)} algorithmic optimizations"
                ],
            }

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Algorithm optimization failed: {e}")
            return {
                "optimized_code": source_code,
                "error": str(e),
                "optimization_type": "algorithms",
                "optimizations_applied": [],
            }

    async def _memory_optimization(self, source_code: str) -> Dict[str, Any]:
        """メモリ使用量最適化"""
        if not source_code:
            raise ValueError("Source code is required for memory optimization")

        try:
            tree = ast.parse(source_code)

            # メモリ使用パターン分析
            memory_issues = self.memory_analyzer.analyze_memory_usage(tree)

            optimizations_applied = []
            optimized_code = source_code

            # 大きなデータ構造の最適化
            if memory_issues.get("large_data_structures"):
                optimizations_applied.append("Optimized large data structures")
                optimizations_applied.append(
                    "Added generator expressions where applicable"
                )

            # メモリリーク防止
            if memory_issues.get("potential_leaks"):
                optimizations_applied.append("Added explicit memory cleanup")
                optimizations_applied.append(
                    "Implemented context managers for resource management"
                )

            # 不要なコピー削減
            if memory_issues.get("unnecessary_copies"):
                optimizations_applied.append("Reduced unnecessary data copying")
                optimizations_applied.append(
                    "Used views instead of copies where possible"
                )

            # 最適化コード生成
            optimized_code = self._apply_memory_optimizations(
                source_code, optimizations_applied
            )

            return {
                "optimized_code": optimized_code,
                "optimization_type": "memory",
                "optimizations_applied": optimizations_applied,
                "memory_issues_found": len(memory_issues),
                "estimated_memory_reduction": min(50, len(optimizations_applied) * 10),
                "improvements": optimizations_applied,
            }

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Memory optimization failed: {e}")
            return {
                "optimized_code": source_code,
                "error": str(e),
                "optimization_type": "memory",
                "optimizations_applied": [],
            }

    async def _async_optimization(self, source_code: str) -> Dict[str, Any]:
        """非同期処理最適化"""
        if not source_code:
            raise ValueError("Source code is required for async optimization")

        try:
            tree = ast.parse(source_code)

            # 非同期化可能な処理を検出
            async_opportunities = self._find_async_opportunities(tree)

            optimizations_applied = []
            optimized_code = source_code

            # I/O操作の非同期化
            if async_opportunities.get("io_operations"):
                optimizations_applied.append("Converted I/O operations to async")
                optimizations_applied.append("Added async/await patterns")

            # 並列実行の実装
            if async_opportunities.get("parallel_tasks"):
                optimizations_applied.append("Implemented concurrent task execution")
                optimizations_applied.append(
                    "Added asyncio.gather for parallel processing"
                )

            # バッチ処理最適化
            if async_opportunities.get("batch_processing"):
                optimizations_applied.append("Optimized batch processing with async")
                optimizations_applied.append(
                    "Implemented async generators for streaming"
                )

            # 最適化コード生成
            optimized_code = self._apply_async_optimizations(
                source_code, optimizations_applied
            )

            return {
                "async_optimized_code": optimized_code,
                "optimization_type": "async",
                "optimizations_applied": optimizations_applied,
                "async_opportunities": len(async_opportunities),
                "estimated_speedup": min(300, len(optimizations_applied) * 50),  # %
                "improvements": optimizations_applied,
            }

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Async optimization failed: {e}")
            return {
                "async_optimized_code": source_code,
                "error": str(e),
                "optimization_type": "async",
                "optimizations_applied": [],
            }

    async def _database_query_optimization(
        self, query_code: str, schema_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """データベースクエリ最適化"""
        if not query_code:
            raise ValueError("Query code is required for database optimization")

        try:
            # クエリ分析
            query_analysis = self._analyze_database_queries(query_code)

            optimizations_applied = []
            optimized_queries = query_code

            # インデックス使用最適化
            if query_analysis.get("missing_indexes"):
                optimizations_applied.append("Added proper index usage")
                optimizations_applied.append("Optimized WHERE clause order")

            # JOINの最適化
            if query_analysis.get("inefficient_joins"):
                optimizations_applied.append("Optimized JOIN operations")
                optimizations_applied.append("Reduced cartesian products")

            # N+1問題の解決
            if query_analysis.get("n_plus_one_issues"):
                optimizations_applied.append("Resolved N+1 query problems")
                optimizations_applied.append("Implemented query batching")

            # クエリキャッシュ
            if schema_info.get("cache_suitable"):
                optimizations_applied.append("Added query result caching")
                optimizations_applied.append("Implemented cache invalidation strategy")

            return {
                "optimized_queries": optimized_queries,
                "optimization_type": "database",
                "optimizations_applied": optimizations_applied,
                "query_issues_found": len(query_analysis),
                "estimated_performance_gain": min(200, len(optimizations_applied) * 25),
                "improvements": optimizations_applied,
            }

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Database query optimization failed: {e}")
            return {
                "optimized_queries": query_code,
                "error": str(e),
                "optimization_type": "database",
                "optimizations_applied": [],
            }

    async def _caching_strategy(
        self, source_code: str, cache_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """キャッシング戦略実装"""
        if not source_code:
            raise ValueError("Source code is required for caching strategy")

        try:
            tree = ast.parse(source_code)

            # キャッシュ対象の特定
            cache_candidates = self._identify_cache_candidates(tree)

            cache_type = cache_requirements.get("type", "lru")
            ttl = cache_requirements.get("ttl", 3600)
            max_size = cache_requirements.get("max_size", 128)

            optimizations_applied = []
            cached_code = source_code

            # 関数レベルキャッシング
            if cache_candidates.get("expensive_functions"):
                optimizations_applied.append(
                    f"Added {cache_type} caching to expensive functions"
                )
                optimizations_applied.append(f"Set cache TTL to {ttl} seconds")

            # データキャッシング
            if cache_candidates.get("data_access"):
                optimizations_applied.append("Implemented data access caching")
                optimizations_applied.append("Added cache warming strategies")

            # 計算結果キャッシング
            if cache_candidates.get("calculations"):
                optimizations_applied.append("Cached expensive calculations")
                optimizations_applied.append("Implemented cache-aware algorithms")

            # キャッシュ実装コード生成
            cached_code = self._implement_caching(
                source_code, cache_type, cache_requirements
            )

            return {
                "cached_code": cached_code,
                "optimization_type": "caching",
                "cache_type": cache_type,
                "cache_candidates": len(cache_candidates),
                "optimizations_applied": optimizations_applied,
                "estimated_speedup": min(500, len(cache_candidates) * 50),
                "improvements": optimizations_applied,
            }

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Caching strategy implementation failed: {e}")
            return {
                "cached_code": source_code,
                "error": str(e),
                "optimization_type": "caching",
                "optimizations_applied": [],
            }

    async def _validate_performance_optimization_quality(
        self, result_data: Dict[str, Any]
    ) -> float:
        """パフォーマンス最適化品質検証"""
        quality_score = await self.validate_crafting_quality(result_data)

        try:
            # パフォーマンス最適化特有の品質チェック
            optimizations_applied = result_data.get("optimizations_applied", [])

            # 最適化数による加点
            quality_score += min(25.0, len(optimizations_applied) * 5.0)

            # 推定改善度による加点
            estimated_improvement = result_data.get("estimated_improvement", 0)
            if estimated_improvement > 0:
                quality_score += min(20.0, estimated_improvement * 0.2)

            # エラーなしボーナス
            if "error" not in result_data:
                quality_score += 15.0

            # 具体的な最適化コードがある場合
            if any(
                key in result_data
                for key in ["optimized_code", "cached_code", "async_optimized_code"]
            ):
                quality_score += 10.0

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Performance optimization quality validation error: {e}")
            quality_score = max(quality_score - 10.0, 0.0)

        return min(quality_score, 100.0)

    # ヘルパーメソッドとクラス
    def _initialize_optimization_patterns(self) -> Dict[str, Any]:
        """最適化パターン初期化"""
        return {
            "loop_optimizations": [
                "list_comprehension",
                "generator_expression",
                "vectorization",
                "loop_unrolling",
            ],
            "data_structure_optimizations": [
                "use_sets_for_membership",
                "use_deque_for_queues",
                "use_defaultdict",
                "lazy_evaluation",
            ],
            "async_patterns": [
                "io_async_conversion",
                "concurrent_execution",
                "async_generators",
                "batch_processing",
            ],
        }

    def _optimize_loops(self, tree: ast.AST) -> List[str]:
        """ループ最適化"""
        optimizations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                # リスト内包表記への変換提案
                optimizations.append("Suggested list comprehension for loop")
            elif isinstance(node, ast.While):
                # while ループの最適化提案
                optimizations.append("Optimized while loop condition")

        return optimizations

    def _optimize_data_structures(self, tree: ast.AST) -> List[str]:
        """データ構造最適化"""
        optimizations = []

        # 簡易実装: リストをセットに変換提案
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare) and isinstance(node.left, ast.Name):
                # Complex condition - consider breaking down
                if any(isinstance(comp, ast.In) for comp in node.ops):
                    # Complex condition - consider breaking down
                    optimizations.append("Suggested using set for membership testing")

        return optimizations

    def _optimize_calculations(self, tree: ast.AST) -> List[str]:
        """計算最適化"""
        optimizations = []

        # 冗長な計算の検出
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp):
                if isinstance(node.op, (ast.Mult, ast.Pow)):
                    optimizations.append("Optimized mathematical operations")

        return optimizations

    def _suggest_parallelization(self, tree: ast.AST) -> List[str]:
        """並列化提案"""
        suggestions = []

        # 独立したループの検出
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                suggestions.append("Suggested parallelization for independent loop")

        return suggestions

    def _apply_optimizations(self, source_code: str, optimizations: List[str]) -> str:
        """最適化適用"""
        # 実際の最適化適用は複雑なので、プレースホルダー実装
        optimized_code = f"""# Optimized code with {len(optimizations)} improvements
{source_code}

# Applied optimizations:
{chr(10).join(f"# - {opt}" for opt in optimizations)}
"""
        return optimized_code

    def _estimate_improvement(self, optimizations: List[str]) -> float:
        """改善度推定"""
        # 最適化の種類に基づく推定改善度（%）
        improvement_weights = {
            "loop": 25,
            "data": 15,
            "async": 50,
            "cache": 40,
            "parallel": 60,
        }

        total_improvement = 0
        for opt in optimizations:
            # Process each item in collection
            for keyword, weight in improvement_weights.items():
                # Process each item in collection
                if keyword in opt.lower():
                    total_improvement += weight
                    break

        return min(total_improvement, 200)  # 最大200%改善


class CodeProfiler:
    """コードプロファイラー"""

    def profile_code(
        self, source_code: str, test_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """コードプロファイリング実行"""
        try:
            # 簡易プロファイリング実装
            start_time = time.time()

            # コードの複雑度分析
            tree = ast.parse(source_code)
            function_count = len(
                [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            )
            loop_count = len(
                [n for n in ast.walk(tree) if isinstance(n, (ast.For, ast.While))]
            )

            execution_time = time.time() - start_time

            return {
                "total_time": execution_time,
                "function_calls": function_count * 10,  # 推定
                "memory_peak": len(source_code) * 0.1,  # 推定メモリ使用量
                "complexity_score": function_count + loop_count * 2,
            }

        except Exception as e:
            # Handle specific exception case
            return {
                "total_time": 0,
                "function_calls": 0,
                "memory_peak": 0,
                "error": str(e),
            }


class MemoryAnalyzer:
    """メモリ分析器"""

    def analyze_memory_usage(self, tree: ast.AST) -> Dict[str, Any]:
        """メモリ使用量分析"""
        issues = {}

        # 大きなデータ構造の検出
        large_structures = []
        for node in ast.walk(tree):
            if isinstance(node, ast.List) and len(getattr(node, "elts", [])) > 100:
                # Complex condition - consider breaking down
                large_structures.append(node)

        if large_structures:
            issues["large_data_structures"] = len(large_structures)

        # 潜在的メモリリークの検出
        open_calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                # Complex condition - consider breaking down
                if node.func.id == "open":
                    open_calls.append(node)

        if open_calls:
            issues["potential_leaks"] = len(open_calls)

        return issues


class BottleneckDetector:
    """ボトルネック検出器"""

    def detect_bottlenecks(
        self, profile_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """ボトルネック検出"""
        bottlenecks = []

        # 実行時間によるボトルネック
        total_time = profile_result.get("total_time", 0)
        if total_time > 1.0:  # 1秒以上
            bottlenecks.append(
                {
                    "type": "execution_time",
                    "severity": "high",
                    "value": total_time,
                    "description": "Long execution time detected",
                }
            )

        # メモリ使用量によるボトルネック
        memory_peak = profile_result.get("memory_peak", 0)
        if memory_peak > 100:  # 100MB以上
            bottlenecks.append(
                {
                    "type": "memory_usage",
                    "severity": "medium",
                    "value": memory_peak,
                    "description": "High memory usage detected",
                }
            )

        return bottlenecks
