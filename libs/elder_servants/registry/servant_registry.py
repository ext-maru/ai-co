"""
エルダーサーバントレジストリ

すべてのエルダーサーバントの登録と管理を行う中央レジストリ。
サーバントの検索、フィルタリング、統計情報の提供を行う。
"""

import asyncio
import logging
from collections import defaultdict
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
        pass
    
    class ServantCapability:
        pass
    
    class ServantCategory:
        pass
    
    class ServantRequest:
        pass
    
    class ServantResponse:
        pass
    
    class ServantDomain:
        pass


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
                self._capability_map[cap].append(name)

            self._stats["total_registered"] += 1
            self._stats["active_servants"] = len(self._servants)

            self.logger.info(f"Registered servant: {name} in domain {domain.value}")
            return True

        except Exception as e:
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
                return await servant.execute_with_quality_gate(request)

        # タスクタイプに基づいて適切なサーバントを探す
        # TODO: より高度なルーティングロジックの実装
        for name, servant in self._instance_cache.items():
            if servant.validate_request(request):
                self.logger.info(f"Routing task {request.task_id} to {name}")
                return await servant.execute_with_quality_gate(request)

        self.logger.warning(f"No suitable servant found for task {request.task_id}")
        return None

    def get_statistics(self) -> Dict[str, Any]:
        """レジストリの統計情報を取得"""
        domain_stats = {}
        for domain in ServantDomain:
            count = len(self._domain_map.get(domain, []))
            domain_stats[domain.value] = count

        capability_stats = {}
        for cap in ServantCapability:
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
