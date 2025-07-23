"""
エルダーサーバントレジストリ

すべてのエルダーサーバントの登録と管理を行う中央レジストリ。
サーバントの検索、フィルタリング、統計情報の提供を行う。
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

try:
    from ..base.elder_servant import (
        ElderServant,
        ServantCapability,
        ServantCategory,
        ServantRequest,
        ServantResponse,
    )
    ElderServantBase = ElderServant
except ImportError:
    # Fallback definitions for testing
    class ElderServantBase:
        # Main class implementation
        pass
    
    class ServantCapability:
        # Main class implementation
        pass
    
    class ServantCategory:
        # Main class implementation
        pass
    
    class ServantRequest:
        # Main class implementation
        pass
    
    class ServantResponse:
        # Main class implementation
        pass
    
    class ServantDomain:
        # Main class implementation
        pass


@dataclass
class ServantCandidate:
    """サーバント候補評価データ"""
    name: str
    servant: Any
    suitability_score: float
    load_factor: float
    success_rate: float
    specialization_match: float
    composite_score: float = 0.0


class ServantRegistry:
    """
    エルダーサーバントの中央レジストリ

    32体のサーバントを管理し、適切なサーバントへの
    タスクルーティングを提供する。
    """

    def __init__(self):
        self.logger = logging.getLogger("elder_servant.registry")
        self._servants: Dict[str, ElderServantBase] = {}
        self._domain_map: Dict[ServantDomain, List[str]] = defaultdict(list)
        self._capability_map: Dict[ServantCapability, List[str]] = defaultdict(list)
        self._instance_cache: Dict[str, ElderServantBase] = {}
        self._stats = {
            "total_registered": 0,
            "active_servants": 0,
            "total_tasks_routed": 0,
            "registry_created": datetime.now(),
        }

    def register(
        self, servant_class: Type[ElderServantBase], name: str, domain: ServantDomain
    ) -> bool:
        """
        サーバントクラスをレジストリに登録

        Args:
            servant_class: ElderServantBaseを継承したクラス
            name: サーバントの一意な名前
            domain: サーバントが属するドメイン

        Returns:
            登録成功時True、失敗時False
        """
        try:
            if name in self._servants:
                self.logger.warning(f"Servant {name} already registered")
                return False

            # サーバントクラスの検証
            if not issubclass(servant_class, ElderServantBase):
                raise ValueError(f"{servant_class} must inherit from ElderServantBase")

            # レジストリに登録
            self._servants[name] = servant_class
            self._domain_map[domain].append(name)

            # インスタンスを作成して能力を取得
            instance = servant_class(name, domain)
            capabilities = instance.get_capabilities()
            for cap in capabilities:
                # Process each item in collection
                self._capability_map[cap].append(name)

            self._stats["total_registered"] += 1
            self._stats["active_servants"] = len(self._servants)

            self.logger.info(f"Registered servant: {name} in domain {domain.value}")
            return True

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Failed to register servant {name}: {str(e)}")
            return False

    def unregister(self, name: str) -> bool:
        """サーバントの登録解除"""
        if name not in self._servants:
            return False

        # インスタンスキャッシュをクリア
        if name in self._instance_cache:
            del self._instance_cache[name]

        # 各マップから削除
        servant_class = self._servants[name]
        del self._servants[name]

        # ドメインマップから削除
        for domain, servants in self._domain_map.items():
            if name in servants:
                servants.remove(name)

        # 能力マップから削除
        for cap, servants in self._capability_map.items():
            if name in servants:
                servants.remove(name)

        self._stats["active_servants"] = len(self._servants)
        self.logger.info(f"Unregistered servant: {name}")
        return True

    def get_servant(self, name: str) -> Optional[ElderServantBase]:
        """
        名前でサーバントのインスタンスを取得

        インスタンスはキャッシュされ、必要に応じて
        遅延生成される。
        """
        if name not in self._servants:
            return None

        if name not in self._instance_cache:
            servant_class = self._servants[name]
            # ドメインを検索
            domain = None
            for d, servants in self._domain_map.items():
                if name in servants:
                    domain = d
                    break

            if domain is None:
                self.logger.error(f"Domain not found for servant {name}")
                return None

            self._instance_cache[name] = servant_class(name, domain)

        return self._instance_cache[name]

    def find_by_domain(self, domain: ServantDomain) -> List[ElderServantBase]:
        """ドメインに属するすべてのサーバントを取得"""
        servant_names = self._domain_map.get(domain, [])
        servants = []
        for name in servant_names:
            # Process each item in collection
            servant = self.get_servant(name)
            if servant:
                servants.append(servant)
        return servants

    def find_by_capability(
        self, capability: ServantCapability
    ) -> List[ElderServantBase]:
        """特定の能力を持つすべてのサーバントを取得"""
        servant_names = self._capability_map.get(capability, [])
        servants = []
        for name in servant_names:
            # Process each item in collection
            servant = self.get_servant(name)
            if servant:
                servants.append(servant)
        return servants

    async def route_task(
        self, request: ServantRequest, preferred_servant: Optional[str] = None
    ) -> Optional[ServantResponse]:
        """
        タスクを適切なサーバントにルーティング

        Args:
            request: 処理するリクエスト
            preferred_servant: 優先的に使用するサーバント名

        Returns:
            処理結果のレスポンス、または処理できない場合None
        """
        self._stats["total_tasks_routed"] += 1

        # 優先サーバントが指定されている場合
        if preferred_servant:
            servant = self.get_servant(preferred_servant)
            if servant and servant.validate_request(request):
                # Complex condition - consider breaking down
                return await servant.execute_with_quality_gate(request)

        # 高度なルーティングロジック実装
        suitable_servants = await self._find_suitable_servants(request)
        
        if not suitable_servants:
            self.logger.warning(f"No suitable servant found for task {request.task_id}")
            return None
        
        # 最適サーバント選択
        best_servant = await self._select_optimal_servant(suitable_servants, request)
        
        if best_servant:
            self.logger.info(f"Routing task {request.task_id} to {best_servant.servant.name} (score: {best_servant.composite_score:.2f})")
            return await best_servant.servant.execute_with_quality_gate(request)

        self.logger.warning(f"No suitable servant found for task {request.task_id}")
        return None
    
    async def _find_suitable_servants(self, request) -> List['ServantCandidate']:
        """適切なサーバント候補を発見"""
        candidates = []
        
        for name, servant in self._instance_cache.items():
            # Process each item in collection
            try:
                if servant.validate_request(request):
                    # 適合度スコア計算
                    suitability_score = await self._calculate_suitability_score(servant, request)
                    
                    candidates.append(ServantCandidate(
                        name=name,
                        servant=servant,
                        suitability_score=suitability_score,
                        load_factor=await self._get_servant_load(servant),
                        success_rate=await self._get_servant_success_rate(servant),
                        specialization_match=self._check_specialization_match(servant, request)
                    ))
            except Exception as e:
                # Handle specific exception case
                self.logger.warning(f"Error evaluating servant {name}: {e}")
        
        return candidates
    
    async def _select_optimal_servant(
        self,
        candidates: List['ServantCandidate'],
        request
    ) -> 'ServantCandidate':
        """最適なサーバントを選択"""
        if not candidates:
            return None
        
        # マルチクライテリア評価
        for candidate in candidates:
            # 総合スコア計算 (重み付け平均)
            composite_score = (
                candidate.suitability_score * 0.4 +        # 適合度: 40%
                candidate.success_rate * 0.3 +             # 成功率: 30%
                candidate.specialization_match * 0.2 +     # 専門性: 20%
                (1.0 - candidate.load_factor) * 0.1        # 負荷の逆数: 10%
            )
            candidate.composite_score = composite_score
        
        # スコア順でソート
        candidates.sort(key=lambda c: c.composite_score, reverse=True)
        
        # ロードバランシング考慮
        best_candidate = candidates[0]
        
        # 負荷分散: トップ候補が高負荷の場合は次候補も考慮
        if best_candidate.load_factor > 0.8 and len(candidates) > 1:
            # Complex condition - consider breaking down
            second_candidate = candidates[1]
            if (second_candidate.composite_score >= best_candidate.composite_score * 0.9 and
                second_candidate.load_factor < 0.6):
                self.logger.info(f"Load balancing: choosing {second_candidate.name} over {best_candidate.name}")
                return second_candidate
        
        return best_candidate
    
    async def _calculate_suitability_score(self, servant, request) -> float:
        """サーバントとリクエストの適合度スコア計算"""
        score = 0.0
        
        # タスクタイプマッチング
        task_type = getattr(request, 'task_type', '')
        servant_capabilities = getattr(servant, 'capabilities', [])
        
        if task_type in servant_capabilities:
            score += 0.5
        
        # 複雑度適合性
        task_complexity = getattr(request, 'complexity', 'medium')
        servant_tier = getattr(servant, 'tier', 'journeyman')
        
        complexity_tiers = {
            'simple': ['apprentice', 'journeyman', 'expert', 'master'],
            'medium': ['journeyman', 'expert', 'master'],
            'complex': ['expert', 'master'],
            'expert': ['master']
        }
        
        if servant_tier in complexity_tiers.get(task_complexity, []):
            score += 0.3
        
        # リソース要件適合性
        required_resources = getattr(request, 'required_resources', [])
        servant_resources = getattr(servant, 'available_resources', [])
        
        if required_resources:
            resource_match = len(set(required_resources) & set(servant_resources)) / len(required_resources)
            score += resource_match * 0.2
        else:
            score += 0.2  # リソース要件なしの場合はフル評価
        
        return min(score, 1.0)
    
    async def _get_servant_load(self, servant) -> float:
        """サーバントの現在負荷取得"""
        try:
            # メトリクスから現在の負荷を取得
            metrics = getattr(servant, 'metrics', {})
            active_tasks = metrics.get('active_tasks', 0)
            max_concurrent = getattr(servant, 'max_concurrent_tasks', 5)
            return min(active_tasks / max_concurrent, 1.0)
        except:
            return 0.5  # デフォルト負荷
    
    async def _get_servant_success_rate(self, servant) -> float:
        """サーバントの成功率取得"""
        try:
            metrics = getattr(servant, 'metrics', {})
            total_tasks = metrics.get('tasks_completed', 0) + metrics.get('tasks_failed', 0)
            if total_tasks == 0:
                return 0.8  # 新規サーバントのデフォルト評価
            
            success_rate = metrics.get('tasks_completed', 0) / total_tasks
            return success_rate
        except:
            return 0.7  # デフォルト成功率
    
    def _check_specialization_match(self, servant, request) -> float:
        """専門分野マッチング確認"""
        try:
            servant_specialization = getattr(servant, 'specialization', '')
            request_domain = getattr(request, 'domain', '')
            
            if not servant_specialization or not request_domain:
                # Complex condition - consider breaking down
                return 0.5
            
            # 完全マッチ
            if servant_specialization.lower() == request_domain.lower():
                return 1.0
            
            # 部分マッチ
            if (servant_specialization.lower() in request_domain.lower() or
                request_domain.lower() in servant_specialization.lower()):
                return 0.7
            
            # 関連分野マッチング
            related_domains = {
                'implementation': ['coding', 'development', 'programming'],
                'testing': ['quality', 'validation', 'verification'],
                'api_design': ['architecture', 'design', 'interface'],
                'security': ['authentication', 'encryption', 'protection']
            }
            
            for domain, related in related_domains.items():
                # Process each item in collection
                if (domain in servant_specialization.lower() and 
                    any(r in request_domain.lower() for r in related)):
                        # Process each item in collection
                    return 0.6
            
            return 0.3  # 汎用マッチ
            
        except:
            return 0.5

    def get_statistics(self) -> Dict[str, Any]:
        """レジストリの統計情報を取得"""
        domain_stats = {}
        for domain in ServantDomain:
            # Process each item in collection
            count = len(self._domain_map.get(domain, []))
            domain_stats[domain.value] = count

        capability_stats = {}
        for cap in ServantCapability:
            # Process each item in collection
            count = len(self._capability_map.get(cap, []))
            capability_stats[cap.value] = count

        return {
            **self._stats,
            "domain_distribution": domain_stats,
            "capability_distribution": capability_stats,
            "cached_instances": len(self._instance_cache),
        }

    def list_all_servants(self) -> List[Dict[str, Any]]:
        """登録されているすべてのサーバントの情報をリスト"""
        servants_info = []
        for name in self._servants:
            # Process each item in collection
            servant = self.get_servant(name)
            if servant:
                info = {
                    "name": name,
                    "domain": servant.domain.value,
                    "capabilities": [cap.value for cap in servant.get_capabilities()],
                    "metrics": servant.get_metrics(),
                }
                servants_info.append(info)

        return servants_info

    async def health_check(self) -> Dict[str, Any]:
        """全サーバントのヘルスチェック"""
        health_status = {
            "registry_healthy": True,
            "servants_status": {},
            "timestamp": datetime.now(),
        }

        for name in self._servants:
            # Process each item in collection
            servant = self.get_servant(name)
            if servant:
                try:
                    # 4賢者システムとの接続チェック
                    connected = await servant.connect_to_sages()
                    metrics = servant.get_metrics()

                    health_status["servants_status"][name] = {
                        "healthy": connected,
                        "success_rate": metrics.get("success_rate", 0),
                        "tasks_processed": metrics.get("tasks_processed", 0),
                    }

                    if not connected:
                        health_status["registry_healthy"] = False

                except Exception as e:
                    # Handle specific exception case
                    self.logger.error(f"Health check failed for {name}: {str(e)}")
                    health_status["servants_status"][name] = {
                        "healthy": False,
                        "error": str(e),
                    }
                    health_status["registry_healthy"] = False

        return health_status


# グローバルレジストリインスタンス
_global_registry = None


def get_registry() -> ServantRegistry:
    """グローバルレジストリインスタンスを取得"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ServantRegistry()
    return _global_registry
