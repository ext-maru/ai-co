"""
負荷分散・ロードバランシングシステム

Elder Servants間の負荷を動的に分散し、システム全体のパフォーマンスと
可用性を最適化するインテリジェント負荷分散システム。
"""

import asyncio
import heapq
import logging
import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..base.elder_servant_base import (
    ElderServantBase,
    ServantCapability,
    ServantDomain,
    ServantRequest,
    ServantResponse,
)
from ..registry.servant_registry import ServantRegistry, get_registry
from ..selection.servant_auto_selector import ServantAutoSelector, get_auto_selector

class LoadBalancingStrategy(Enum):
    """負荷分散戦略"""

    ROUND_ROBIN = "round_robin"  # ラウンドロビン
    LEAST_CONNECTIONS = "least_connections"  # 最少接続数
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"  # 重み付きラウンドロビン
    LEAST_RESPONSE_TIME = "least_response_time"  # 最短応答時間
    HASH_BASED = "hash_based"  # ハッシュベース
    ADAPTIVE = "adaptive"  # 適応型
    RESOURCE_BASED = "resource_based"  # リソースベース
    INTELLIGENT = "intelligent"  # AI選択統合

class HealthStatus(Enum):
    """健全性ステータス"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"

@dataclass
class LoadMetrics:
    """負荷メトリクス"""

    cpu_usage: float = 0.0  # CPU使用率
    memory_usage: float = 0.0  # メモリ使用率
    active_connections: int = 0  # アクティブ接続数
    pending_tasks: int = 0  # 待機タスク数
    response_time: float = 0.0  # 平均応答時間
    error_rate: float = 0.0  # エラー率
    throughput: float = 0.0  # スループット
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class ServantNode:
    """サーバントノード（負荷分散対象）"""

    servant: ElderServantBase
    weight: float = 1.0  # 負荷分散重み
    max_connections: int = 100  # 最大接続数
    health_status: HealthStatus = HealthStatus.HEALTHY
    load_metrics: LoadMetrics = field(default_factory=LoadMetrics)
    current_requests: int = 0  # 現在のリクエスト数
    total_requests: int = 0  # 総リクエスト数
    successful_requests: int = 0  # 成功リクエスト数
    failed_requests: int = 0  # 失敗リクエスト数
    last_health_check: datetime = field(default_factory=datetime.now)

@dataclass
class LoadBalancingResult:
    """負荷分散結果"""

    selected_servant: ElderServantBase
    routing_reason: str
    load_metrics_snapshot: Dict[str, Any]
    alternative_servants: List[ElderServantBase]
    balancing_strategy: LoadBalancingStrategy
    selection_time: float

class LoadBalancer:
    """
    Elder Servants負荷分散システム

    複数の負荷分散戦略を組み合わせて、最適なサーバント選択と
    負荷分散を実現する。
    """

    def __init__(
        self,
        registry: Optional[ServantRegistry] = None,
        auto_selector: Optional[ServantAutoSelector] = None,
    ):
        self.logger = logging.getLogger("elder_servants.load_balancer")
        self.registry = registry or get_registry()
        self.auto_selector = auto_selector or get_auto_selector()

        # サーバントノード管理
        self.servant_nodes: Dict[str, ServantNode] = {}

        # 負荷分散戦略
        self.default_strategy = LoadBalancingStrategy.ADAPTIVE
        self.strategy_functions = {
            LoadBalancingStrategy.ROUND_ROBIN: self._round_robin_selection,
            LoadBalancingStrategy.LEAST_CONNECTIONS: self._least_connections_selection,
            LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN: self._weighted_round_robin_selection,
            LoadBalancingStrategy.LEAST_RESPONSE_TIME: self._least_response_time_selection,
            LoadBalancingStrategy.HASH_BASED: self._hash_based_selection,
            LoadBalancingStrategy.ADAPTIVE: self._adaptive_selection,
            LoadBalancingStrategy.RESOURCE_BASED: self._resource_based_selection,
            LoadBalancingStrategy.INTELLIGENT: self._intelligent_selection,
        }

        # ラウンドロビン状態
        self.round_robin_counters: Dict[ServantDomain, int] = defaultdict(int)

        # 統計情報
        self.balancing_stats = {
            "total_requests": 0,
            "successful_routings": 0,
            "failed_routings": 0,
            "strategy_usage": defaultdict(int),
            "average_response_time": 0.0,
            "last_reset": datetime.now(),
        }

        # ヘルスチェック設定
        self.health_check_interval = 30.0  # 30秒
        self.health_check_timeout = 5.0  # 5秒
        self.health_check_task = None

        # 負荷監視設定
        self.load_monitoring_interval = 10.0  # 10秒
        self.load_monitoring_task = None

        # 履歴データ
        self.response_time_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=100)
        )
        self.load_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

    async def start(self)self.logger.info("Starting Load Balancer system...")
    """負荷分散システム開始"""

        # サーバントノード初期化
        await self._initialize_servant_nodes()

        # ヘルスチェック開始
        self.health_check_task = asyncio.create_task(self._health_check_loop())

        # 負荷監視開始
        self.load_monitoring_task = asyncio.create_task(self._load_monitoring_loop())

        self.logger.info(
            f"Load Balancer started with {len(self.servant_nodes)} servant nodes"
        )

    async def stop(self)self.logger.info("Stopping Load Balancer system...")
    """負荷分散システム停止"""

        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass

        if self.load_monitoring_task:
            self.load_monitoring_task.cancel()
            try:
                await self.load_monitoring_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Load Balancer stopped")

    async def route_request(
        self,
        request: ServantRequest,
        strategy: Optional[LoadBalancingStrategy] = None,
        preferred_domain: Optional[ServantDomain] = None,
    ) -> LoadBalancingResult:
        """
        リクエストを適切なサーバントにルーティング

        Args:
            request: ルーティングするリクエスト
            strategy: 使用する負荷分散戦略
            preferred_domain: 優先ドメイン

        Returns:
            負荷分散結果
        """
        start_time = time.time()
        strategy = strategy or self.default_strategy

            f"Routing request {request.task_id} with strategy {strategy.value}"
        )

        try:
            # 候補サーバント取得
            candidate_nodes = await self._get_candidate_nodes(request, preferred_domain)

            if not candidate_nodes:
                raise ValueError("No healthy servants available for routing")

            # 戦略に基づくサーバント選択
            strategy_func = self.strategy_functions.get(strategy)
            if not strategy_func:
                raise ValueError(f"Unknown load balancing strategy: {strategy}")

            selected_node = await strategy_func(request, candidate_nodes)

            if not selected_node:
                raise ValueError("Strategy failed to select a servant")

            # 代替サーバント取得
            alternatives = [
                node.servant for node in candidate_nodes if node != selected_node
            ][
                :3
            ]  # 上位3つ

            # 負荷メトリクススナップショット
            metrics_snapshot = {
                node.servant.name: {
                    "current_requests": node.current_requests,
                    "load_metrics": node.load_metrics.__dict__,
                    "health_status": node.health_status.value,
                }
                for node in candidate_nodes
            }

            # ルーティング理由生成
            routing_reason = self._generate_routing_reason(
                selected_node, strategy, candidate_nodes
            )

            # 統計更新
            self._update_routing_stats(strategy, time.time() - start_time, True)

            result = LoadBalancingResult(
                selected_servant=selected_node.servant,
                routing_reason=routing_reason,
                load_metrics_snapshot=metrics_snapshot,
                alternative_servants=alternatives,
                balancing_strategy=strategy,
                selection_time=time.time() - start_time,
            )

            # リクエスト開始記録
            await self._record_request_start(selected_node, request)

            return result

        except Exception as e:
            self.logger.error(f"Request routing failed: {str(e)}")
            self._update_routing_stats(strategy, time.time() - start_time, False)
            raise

    async def _initialize_servant_nodes(self)self.servant_nodes.clear()
    """サーバントノード初期化"""

        all_servants = self.registry.list_all_servants()

        for servant_info in all_servants:
            servant = self.registry.get_servant(servant_info["name"])
            if servant:
                node = ServantNode(
                    servant=servant,
                    weight=self._calculate_initial_weight(servant),
                    max_connections=self._calculate_max_connections(servant),
                )

                # 初期負荷メトリクス設定
                await self._update_load_metrics(node)

                self.servant_nodes[servant.name] = node

    def _calculate_initial_weight(self, servant: ElderServantBase) -> float:
        """初期重み計算"""
        # ドメインベースの基本重み
        domain_weights = {
            ServantDomain.DWARF_WORKSHOP: 1.0,
            ServantDomain.RAG_WIZARDS: 0.8,  # 調査研究は重め
            ServantDomain.ELF_FOREST: 1.2,  # 監視は軽め
            ServantDomain.INCIDENT_KNIGHTS: 0.6,  # 緊急対応は重め
        }

        base_weight = domain_weights.get(servant.domain, 1.0)

        # パフォーマンス履歴による調整
        metrics = servant.get_metrics()
        success_rate = metrics.get("success_rate", 0.5)

        # 成功率による重み調整
        performance_adjustment = 0.5 + success_rate

        return base_weight * performance_adjustment

    def _calculate_max_connections(self, servant: ElderServantBase) -> int:
        """最大接続数計算"""
        # ドメインベースの基本容量
        domain_capacity = {
            ServantDomain.DWARF_WORKSHOP: 50,
            ServantDomain.RAG_WIZARDS: 30,
            ServantDomain.ELF_FOREST: 80,
            ServantDomain.INCIDENT_KNIGHTS: 20,
        }

        return domain_capacity.get(servant.domain, 40)

    async def _get_candidate_nodes(
        self, request: ServantRequest, preferred_domain: Optional[ServantDomain]
    ) -> List[ServantNode]:
        """候補ノード取得"""
        candidates = []

        for node in self.servant_nodes.values():
            # 健全性チェック
            if node.health_status not in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]:
                continue

            # 容量チェック
            if node.current_requests >= node.max_connections:
                continue

            # ドメイン優先チェック
            if preferred_domain and node.servant.domain != preferred_domain:
                continue

            # リクエスト妥当性チェック
            if not node.servant.validate_request(request):
                continue

            candidates.append(node)

        # 優先ドメインで候補が見つからない場合は全ドメインを対象
        if not candidates and preferred_domain:
            return await self._get_candidate_nodes(request, None)

        return candidates

    # === 負荷分散戦略実装 ===

    async def _round_robin_selection(
        self, request: ServantRequest, candidates: List[ServantNode]
    ) -> ServantNode:
        """ラウンドロビン選択"""
        if not candidates:
            return None

        # ドメイン別ラウンドロビン
        domain = candidates[0].servant.domain
        domain_candidates = [
            node for node in candidates if node.servant.domain == domain
        ]

        if not domain_candidates:
            domain_candidates = candidates

        counter = self.round_robin_counters[domain]
        selected_index = counter % len(domain_candidates)
        self.round_robin_counters[domain] += 1

        return domain_candidates[selected_index]

    async def _least_connections_selection(
        self, request: ServantRequest, candidates: List[ServantNode]
    ) -> ServantNode:
        """最少接続数選択"""
        if not candidates:
            return None

        return min(candidates, key=lambda node: node.current_requests)

    async def _weighted_round_robin_selection(
        self, request: ServantRequest, candidates: List[ServantNode]
    ) -> ServantNode:
        """重み付きラウンドロビン選択"""
        if not candidates:
            return None

        # 重みに基づく選択
        total_weight = sum(node.weight for node in candidates)
        weights = [node.weight / total_weight for node in candidates]

        # 累積重みで選択
        import random

        rand = random.random()
        cumulative_weight = 0.0

        for i, weight in enumerate(weights):
            cumulative_weight += weight
            if rand <= cumulative_weight:
                return candidates[i]

        return candidates[-1]  # フォールバック

    async def _least_response_time_selection(
        self, request: ServantRequest, candidates: List[ServantNode]
    ) -> ServantNode:
        """最短応答時間選択"""
        if not candidates:
            return None

        return min(candidates, key=lambda node: node.load_metrics.response_time)

    async def _hash_based_selection(
        self, request: ServantRequest, candidates: List[ServantNode]
    ) -> ServantNode:
        """ハッシュベース選択"""
        if not candidates:
            return None

        # タスクIDのハッシュベース選択
        hash_value = hash(request.task_id) % len(candidates)
        return candidates[hash_value]

    async def _adaptive_selection(
        self, request: ServantRequest, candidates: List[ServantNode]
    ) -> ServantNode:
        """適応型選択"""
        if not candidates:
            return None

        # 複数要因を考慮した適応型選択
        scored_candidates = []

        for node in candidates:
            score = 0.0

            # 負荷スコア (低いほど良い)
            load_score = 1.0 - (node.current_requests / node.max_connections)
            score += load_score * 0.3

            # 応答時間スコア (短いほど良い)
            max_response_time = max(n.load_metrics.response_time for n in candidates)
            if max_response_time > 0:
                response_score = 1.0 - (
                    node.load_metrics.response_time / max_response_time
                )
            else:
                response_score = 1.0
            score += response_score * 0.3

            # 成功率スコア
            total_requests = node.total_requests
            if total_requests > 0:
                success_rate = node.successful_requests / total_requests
            else:
                success_rate = 1.0
            score += success_rate * 0.2

            # 重みスコア
            score += node.weight * 0.2

            scored_candidates.append((node, score))

        # 最高スコアのノード選択
        return max(scored_candidates, key=lambda x: x[1])[0]

    async def _resource_based_selection(
        self, request: ServantRequest, candidates: List[ServantNode]
    ) -> ServantNode:
        """リソースベース選択"""
        if not candidates:
            return None

        # リソース使用率ベースの選択
        scored_candidates = []

        for node in candidates:
            # CPU、メモリ、ネットワーク使用率を考慮
            cpu_score = 1.0 - node.load_metrics.cpu_usage
            memory_score = 1.0 - node.load_metrics.memory_usage

            # ペンディングタスクによる調整
            pending_penalty = node.load_metrics.pending_tasks * 0.1

            total_score = (cpu_score * 0.4 + memory_score * 0.4) - pending_penalty
            scored_candidates.append((node, max(0.0, total_score)))

        return max(scored_candidates, key=lambda x: x[1])[0]

    async def _intelligent_selection(
        self, request: ServantRequest, candidates: List[ServantNode]
    ) -> ServantNode:
        """インテリジェント選択（AI統合）"""
        if not candidates:
            return None

        try:
            # 自動選択システムとの統合
            candidate_servants = [node.servant for node in candidates]

            # 簡易タスクプロファイル作成
            from ..selection.servant_auto_selector import (
                SelectionCriteria,
                TaskProfile,
                TaskType,
            )

            task_profile = TaskProfile(
                task_id=request.task_id,
                task_type=TaskType.ROUTINE,  # デフォルト
                priority=request.priority,
                estimated_duration=0.0,
                required_capabilities=[],  # 推定
                preferred_domain=None,
                complexity_score=0.5,
                urgency_score=0.7 if request.priority == "high" else 0.5,
                quality_requirement=0.8,
            )

            # AI選択実行
            selection_result = await self.auto_selector.select_optimal_servant(
                task_profile, SelectionCriteria.PERFORMANCE
            )

            # 選択されたサーバントに対応するノードを返す
            for node in candidates:
                if node.servant == selection_result.selected_servant:
                    return node

            # AI選択が候補に含まれない場合はフォールバック
            return await self._adaptive_selection(request, candidates)

        except Exception as e:
            self.logger.warning(
                f"Intelligent selection failed, falling back to adaptive: {str(e)}"
            )
            return await self._adaptive_selection(request, candidates)

    def _generate_routing_reason(
        self,
        selected_node: ServantNode,
        strategy: LoadBalancingStrategy,
        candidates: List[ServantNode],
    ) -> str:
        """ルーティング理由生成"""
        reasons = []

        if strategy == LoadBalancingStrategy.ROUND_ROBIN:
            reasons.append("ラウンドロビン順序による選択")
        elif strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            reasons.append(f"最少接続数 ({selected_node.current_requests} 接続)")
        elif strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
            reasons.append(
                f"最短応答時間 ({selected_node.load_metrics.response_time:0.2f}ms)"
            )
        elif strategy == LoadBalancingStrategy.ADAPTIVE:
            reasons.append("適応型アルゴリズムによる最適選択")
        elif strategy == LoadBalancingStrategy.INTELLIGENT:
            reasons.append("AI自動選択システムによる最適化選択")

        # 追加情報
        if selected_node.health_status == HealthStatus.DEGRADED:
            reasons.append("注意: 性能低下状態")

        if selected_node.current_requests > selected_node.max_connections * 0.8:
            reasons.append("注意: 高負荷状態")

        return " | ".join(reasons)

    async def _record_request_start(self, node: ServantNode, request: ServantRequest):
        """リクエスト開始記録"""
        node.current_requests += 1
        node.total_requests += 1

        # 負荷メトリクス更新
        node.load_metrics.active_connections = node.current_requests
        node.load_metrics.last_updated = datetime.now()

    async def record_request_completion(
        self,
        servant_name: str,
        success: bool,
        response_time: float,
        error: Optional[str] = None,
    ):
        """リクエスト完了記録"""
        if servant_name not in self.servant_nodes:
            return

        node = self.servant_nodes[servant_name]

        # 接続数減算
        node.current_requests = max(0, node.current_requests - 1)

        # 成功/失敗カウント
        if success:
            node.successful_requests += 1
        else:
            node.failed_requests += 1

        # 応答時間履歴更新
        self.response_time_history[servant_name].append(response_time)

        # 負荷メトリクス更新
        await self._update_response_time_metrics(node)

        # 統計更新
        self._update_completion_stats(response_time)

            f"Recorded completion for {servant_name}: success={success}, time={response_time:0.2f}ms"
        )

    async def _update_response_time_metrics(self, node: ServantNode):
        """応答時間メトリクス更新"""
        history = self.response_time_history[node.servant.name]

        if history:
            node.load_metrics.response_time = statistics.mean(history)

            # エラー率計算
            if node.total_requests > 0:
                node.load_metrics.error_rate = (
                    node.failed_requests / node.total_requests
                )

            # スループット計算 (簡易版)
            if len(history) >= 2:
                recent_times = list(history)[-10:]  # 最新10件
                node.load_metrics.throughput = (
                    len(recent_times) / sum(recent_times) * 1000
                )  # req/sec

    async def _update_load_metrics(self, node: ServantNode):
        """負荷メトリクス更新"""
        # 実際の実装ではシステムメトリクスを取得
        # ここではサーバントの統計情報から推定
        metrics = node.servant.get_metrics()

        # CPU使用率推定 (タスク処理数ベース)
        tasks_processed = metrics.get("tasks_processed", 0)
        node.load_metrics.cpu_usage = min(1.0, tasks_processed / 100.0)

        # メモリ使用率推定
        node.load_metrics.memory_usage = min(
            1.0, node.current_requests / node.max_connections
        )

        # アクティブ接続数
        node.load_metrics.active_connections = node.current_requests

        # ペンディングタスク数（仮想）
        node.load_metrics.pending_tasks = max(0, node.current_requests - 5)

        node.load_metrics.last_updated = datetime.now()

    async def _health_check_loop(self):
        """ヘルスチェックループ"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_checks()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check loop error: {str(e)}")

    async def _perform_health_checks(self)for node in self.servant_nodes.values():
    """ヘルスチェック実行"""
            try:
                # 簡易ヘルスチェック
                metrics = node.servant.get_metrics()
                success_rate = metrics.get("success_rate", 0.0)

                # 健全性判定
                if success_rate >= 0.9:
                    new_status = HealthStatus.HEALTHY
                elif success_rate >= 0.7:
                    new_status = HealthStatus.DEGRADED
                else:
                    new_status = HealthStatus.UNHEALTHY

                # ステータス変更ログ
                if node.health_status != new_status:
                    self.logger.info(
                        (
                            f"f"Health status changed for {node.servant.name}: {node.health_status.value} -> "
                            f"{new_status.value}""
                        )
                    )
                    node.health_status = new_status

                node.last_health_check = datetime.now()

            except Exception as e:
                self.logger.error(
                    f"Health check failed for {node.servant.name}: {str(e)}"
                )
                node.health_status = HealthStatus.UNHEALTHY

    async def _load_monitoring_loop(self):
        """負荷監視ループ"""
        while True:
            try:
                await asyncio.sleep(self.load_monitoring_interval)
                await self._update_all_load_metrics()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Load monitoring loop error: {str(e)}")

    async def _update_all_load_metrics(self)for node in self.servant_nodes.values()await self._update_load_metrics(node)
    """全負荷メトリクス更新"""

            # 負荷履歴記録
            load_snapshot = {
                "timestamp": datetime.now().isoformat(),
                "cpu_usage": node.load_metrics.cpu_usage,
                "memory_usage": node.load_metrics.memory_usage,
                "active_connections": node.load_metrics.active_connections,
                "response_time": node.load_metrics.response_time,
            }

            self.load_history[node.servant.name].append(load_snapshot)

    def _update_routing_stats(
        self, strategy: LoadBalancingStrategy, selection_time: float, success: bool
    ):
        """ルーティング統計更新"""
        self.balancing_stats["total_requests"] += 1
        self.balancing_stats["strategy_usage"][strategy.value] += 1

        if success:
            self.balancing_stats["successful_routings"] += 1
        else:
            self.balancing_stats["failed_routings"] += 1

    def _update_completion_stats(self, response_time: float):
        """完了統計更新"""
        total = self.balancing_stats["total_requests"]
        current_avg = self.balancing_stats["average_response_time"]

        # 移動平均更新
        self.balancing_stats["average_response_time"] = (
            current_avg * (total - 1) + response_time
        ) / total

    # === 管理・監視メソッド ===

    async def get_load_balancer_status(self) -> Dict[str, Any]:
        """負荷分散システム状態取得"""
        return {
            "system_status": {
                "total_nodes": len(self.servant_nodes),
                "healthy_nodes": sum(
                    1
                    for node in self.servant_nodes.values()
                    if node.health_status == HealthStatus.HEALTHY
                ),
                "degraded_nodes": sum(
                    1
                    for node in self.servant_nodes.values()
                    if node.health_status == HealthStatus.DEGRADED
                ),
                "unhealthy_nodes": sum(
                    1
                    for node in self.servant_nodes.values()
                    if node.health_status == HealthStatus.UNHEALTHY
                ),
                "total_active_requests": sum(
                    node.current_requests for node in self.servant_nodes.values()
                ),
                "default_strategy": self.default_strategy.value,
            },
            "balancing_stats": self.balancing_stats,
            "node_details": {
                name: {
                    "health_status": node.health_status.value,
                    "current_requests": node.current_requests,
                    "total_requests": node.total_requests,
                    "success_rate": (
                        node.successful_requests / node.total_requests
                        if node.total_requests > 0
                        else 0
                    ),
                    "load_metrics": {
                        "cpu_usage": node.load_metrics.cpu_usage,
                        "memory_usage": node.load_metrics.memory_usage,
                        "response_time": node.load_metrics.response_time,
                        "error_rate": node.load_metrics.error_rate,
                    },
                }
                for name, node in self.servant_nodes.items()
            },
        }

    async def set_servant_weight(self, servant_name: str, weight: float):
        """サーバント重み設定"""
        if servant_name in self.servant_nodes:
            self.servant_nodes[servant_name].weight = max(0.1, min(10.0, weight))
            self.logger.info(f"Updated weight for {servant_name}: {weight}")

    async def set_servant_maintenance(self, servant_name: str, maintenance: bool):
        """サーバントメンテナンスモード設定"""
        if servant_name in self.servant_nodes:
            if maintenance:
                self.servant_nodes[servant_name].health_status = (
                    HealthStatus.MAINTENANCE
                )
            else:
                self.servant_nodes[servant_name].health_status = HealthStatus.HEALTHY

            self.logger.info(f"Set maintenance mode for {servant_name}: {maintenance}")

    async def reset_statistics(self):
        """統計リセット"""
        self.balancing_stats = {
            "total_requests": 0,
            "successful_routings": 0,
            "failed_routings": 0,
            "strategy_usage": defaultdict(int),
            "average_response_time": 0.0,
            "last_reset": datetime.now(),
        }

        # ノード統計リセット
        for node in self.servant_nodes.values():
            node.total_requests = 0
            node.successful_requests = 0
            node.failed_requests = 0

        self.logger.info("Load balancer statistics reset")

# グローバル負荷分散インスタンス
_global_load_balancer = None

def get_load_balancer() -> LoadBalancer:
    """グローバル負荷分散インスタンスを取得"""
    global _global_load_balancer
    if _global_load_balancer is None:
        _global_load_balancer = LoadBalancer()
    return _global_load_balancer
