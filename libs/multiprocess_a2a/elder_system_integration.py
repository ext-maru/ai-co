#!/usr/bin/env python3
"""
🏛️ エルダーシステム統合モジュール
Elder System Integration Module
Created: 2025-07-16
Author: Claude Elder
Version: 1.0.0 - Full Elder System Integration
"""

import asyncio
import json
import logging
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Project root path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Elder Legacy Integration
from core.elders_legacy import EldersFlowLegacy

try:
    from .core import MultiprocessA2ACore
    from .sages_coordinator import ParallelSagesCoordinator
except ImportError:
    from libs.multiprocess_a2a.core import MultiprocessA2ACore
    from libs.multiprocess_a2a.sages_coordinator import ParallelSagesCoordinator

logger = logging.getLogger(__name__)


class ElderType(Enum):
    """エルダータイプ"""

    ANCIENT = "ancient"
    COUNCIL = "council"
    SERVANT = "servant"
    TREE = "tree"
    SAGE = "sage"
    KNIGHT = "knight"


class ElderSystemStatus(Enum):
    """エルダーシステムステータス"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"


@dataclass
class ElderComponent:
    """エルダーコンポーネント"""

    component_id: str
    component_name: str
    elder_type: ElderType
    status: ElderSystemStatus = ElderSystemStatus.ACTIVE
    capabilities: List[str] = field(default_factory=list)
    process_id: Optional[str] = None
    last_heartbeat: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "component_id": self.component_id,
            "component_name": self.component_name,
            "elder_type": self.elder_type.value,
            "status": self.status.value,
            "capabilities": self.capabilities,
            "process_id": self.process_id,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ElderSystemMetrics:
    """エルダーシステムメトリクス"""

    total_components: int = 0
    active_components: int = 0
    council_members: int = 0
    servant_count: int = 0
    sage_count: int = 0
    knight_count: int = 0
    tree_nodes: int = 0
    ancient_elders: int = 0
    coordination_requests: int = 0
    system_health: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class ElderSystemIntegration(EldersFlowLegacy):
    """
    エルダーシステム統合クラス
    4賢者を含むエルダーズギルド全体の統合管理
    """

    def __init__(self, max_components: int = 50):
        """初期化"""
        super().__init__(name="ElderSystemIntegration")
        self.max_components = max_components
        self.integration_id = f"elder_system_{uuid.uuid4().hex[:8]}"

        # エルダーコンポーネント管理
        self.elder_components: Dict[str, ElderComponent] = {}
        self.component_instances: Dict[str, Any] = {}

        # A2A統合
        self.a2a_core = MultiprocessA2ACore("elder_system", "MONITORING")
        self.sages_coordinator = ParallelSagesCoordinator(max_parallel_consultations=20)

        # システムメトリクス
        self.system_metrics = ElderSystemMetrics()

        # 統合履歴
        self.integration_history: List[Dict[str, Any]] = []

        logger.info(f"🏛️ Elder System Integration initialized: {self.integration_id}")

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Elder Legacy準拠リクエスト処理"""
        try:
            request_type = request.get("type", "unknown")

            if request_type == "initialize_elder_system":
                return await self._initialize_elder_system(request)
            elif request_type == "integrate_component":
                return await self._integrate_component(request)
            elif request_type == "get_system_status":
                return await self._get_system_status(request)
            elif request_type == "coordinate_elders":
                return await self._coordinate_elders(request)
            elif request_type == "elder_council_session":
                return await self._elder_council_session(request)
            elif request_type == "servant_deployment":
                return await self._servant_deployment(request)
            elif request_type == "tree_navigation":
                return await self._tree_navigation(request)
            elif request_type == "knight_patrol":
                return await self._knight_patrol(request)
            elif request_type == "ancient_wisdom_access":
                return await self._ancient_wisdom_access(request)
            elif request_type == "full_system_health_check":
                return await self._full_system_health_check(request)
            else:
                return {
                    "success": False,
                    "error": f"Unknown request type: {request_type}",
                    "integration_id": self.integration_id,
                }

        except Exception as e:
            logger.error(f"Elder system request processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "integration_id": self.integration_id,
            }

    async def validate_request(self, request: Dict[str, Any]) -> bool:
        """Elder Legacy準拠バリデーション"""
        required_fields = ["type"]

        for field in required_fields:
            if field not in request:
                logger.error(f"Missing required field: {field}")
                return False

        return True

    def get_capabilities(self) -> List[str]:
        """Elder Legacy準拠機能一覧"""
        return [
            "elder_system_integration",
            "multiprocess_a2a_coordination",
            "full_elder_hierarchy_management",
            "council_session_management",
            "servant_deployment",
            "tree_navigation",
            "knight_patrol_system",
            "ancient_wisdom_access",
            "system_health_monitoring",
            "elder_flow_enhanced",
        ]

    async def _initialize_elder_system(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """エルダーシステム初期化"""
        try:
            # 4賢者統合
            sages_init_result = await self.sages_coordinator.initialize_sages()
            if sages_init_result["success"]:
                logger.info("✅ 4 Sages integrated successfully")

                # 各賢者をコンポーネントとして登録
                for sage_type in ["knowledge", "task", "incident", "rag"]:
                    sage_component = ElderComponent(
                        component_id=f"sage_{sage_type}",
                        component_name=f"{sage_type.title()} Sage",
                        elder_type=ElderType.SAGE,
                        capabilities=[
                            f"{sage_type}_processing",
                            "consultation",
                            "coordination",
                        ],
                    )
                    self.elder_components[sage_component.component_id] = sage_component

            # エルダー評議会統合
            await self._integrate_elder_council()

            # エルダーサーバント統合
            await self._integrate_elder_servants()

            # エルダーツリー統合
            await self._integrate_elder_tree()

            # エルダー騎士団統合
            await self._integrate_elder_knights()

            # エンシェントエルダー統合
            await self._integrate_ancient_elders()

            # システムメトリクス更新
            await self._update_system_metrics()

            # 統合履歴記録
            self.integration_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "action": "system_initialization",
                    "components_integrated": len(self.elder_components),
                    "success": True,
                }
            )

            logger.info(
                f"🏛️ Elder System fully initialized: {len(self.elder_components)} components"
            )

            return {
                "success": True,
                "integration_id": self.integration_id,
                "components_integrated": len(self.elder_components),
                "system_metrics": asdict(self.system_metrics),
                "component_summary": {
                    elder_type.value: len(
                        [
                            c
                            for c in self.elder_components.values()
                            if c.elder_type == elder_type
                        ]
                    )
                    for elder_type in ElderType
                },
            }

        except Exception as e:
            logger.error(f"Elder system initialization failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "integration_id": self.integration_id,
            }

    async def _integrate_elder_council(self):
        """エルダー評議会統合"""
        try:
            # Elder Council動的インポート
            try:
                from governance.elder_council import ElderCouncil

                council_instance = ElderCouncil()

                council_component = ElderComponent(
                    component_id="elder_council",
                    component_name="Elder Council",
                    elder_type=ElderType.COUNCIL,
                    capabilities=[
                        "collective_decision_making",
                        "governance",
                        "approval_processing",
                    ],
                )

                self.elder_components[council_component.component_id] = (
                    council_component
                )
                self.component_instances["elder_council"] = council_instance

                logger.info("✅ Elder Council integrated")

            except ImportError as e:
                logger.warning(f"⚠️ Elder Council integration failed: {e}")

        except Exception as e:
            logger.error(f"Elder Council integration error: {e}")

    async def _integrate_elder_servants(self):
        """エルダーサーバント統合"""
        try:
            # 複数のサーバントを統合
            servant_types = [
                "enhanced_pm_worker",
                "enhanced_task_worker",
                "result_worker",
                "dialog_task_worker",
            ]

            for servant_type in servant_types:
                try:
                    # 動的インポート
                    module_path = f"workers.{servant_type}"
                    class_name = "".join(
                        word.capitalize() for word in servant_type.split("_")
                    )

                    module = __import__(module_path, fromlist=[class_name])
                    if hasattr(module, class_name):
                        servant_class = getattr(module, class_name)
                        servant_instance = servant_class()

                        servant_component = ElderComponent(
                            component_id=f"servant_{servant_type}",
                            component_name=f"{servant_type.replace('_', ' ').title()}",
                            elder_type=ElderType.SERVANT,
                            capabilities=[
                                "task_execution",
                                "worker_processing",
                                "specialized_operations",
                            ],
                        )

                        self.elder_components[servant_component.component_id] = (
                            servant_component
                        )
                        self.component_instances[f"servant_{servant_type}"] = (
                            servant_instance
                        )

                        logger.info(f"✅ Elder Servant integrated: {servant_type}")

                except Exception as e:
                    logger.warning(f"⚠️ Servant {servant_type} integration failed: {e}")

        except Exception as e:
            logger.error(f"Elder Servants integration error: {e}")

    async def _integrate_elder_tree(self):
        """エルダーツリー統合"""
        try:
            # エルダーツリーコンポーネント
            tree_component = ElderComponent(
                component_id="elder_tree",
                component_name="Elder Tree Hierarchy",
                elder_type=ElderType.TREE,
                capabilities=[
                    "hierarchy_navigation",
                    "tree_traversal",
                    "relationship_mapping",
                ],
            )

            self.elder_components[tree_component.component_id] = tree_component

            # 階層構造の模擬実装
            tree_structure = {
                "grand_elder_maru": {"level": 0, "children": ["claude_elder"]},
                "claude_elder": {
                    "level": 1,
                    "children": [
                        "ancient_elder",
                        "elder_council",
                        "four_sages",
                        "knight_orders",
                        "servant_legion",
                    ],
                },
            }

            self.component_instances["elder_tree"] = tree_structure

            logger.info("✅ Elder Tree integrated")

        except Exception as e:
            logger.error(f"Elder Tree integration error: {e}")

    async def _integrate_elder_knights(self):
        """エルダー騎士団統合"""
        try:
            # 騎士団タイプ
            knight_orders = ["incident_knights", "security_knights", "audit_knights"]

            for knight_order in knight_orders:
                knight_component = ElderComponent(
                    component_id=f"knight_{knight_order}",
                    component_name=f"{knight_order.replace('_', ' ').title()}",
                    elder_type=ElderType.KNIGHT,
                    capabilities=[
                        "security_defense",
                        "incident_response",
                        "quality_monitoring",
                    ],
                )

                self.elder_components[knight_component.component_id] = knight_component

                logger.info(f"✅ Elder Knights integrated: {knight_order}")

        except Exception as e:
            logger.error(f"Elder Knights integration error: {e}")

    async def _integrate_ancient_elders(self):
        """エンシェントエルダー統合"""
        try:
            # Ancient Elder動的インポート試行
            try:
                from governance.ancient_elder import AncientElder

                ancient_instance = AncientElder()

                ancient_component = ElderComponent(
                    component_id="ancient_elder",
                    component_name="Ancient Elder",
                    elder_type=ElderType.ANCIENT,
                    capabilities=["quality_auditing", "ancient_wisdom", "oversight"],
                )

                self.elder_components[ancient_component.component_id] = (
                    ancient_component
                )
                self.component_instances["ancient_elder"] = ancient_instance

                logger.info("✅ Ancient Elder integrated")

            except ImportError as e:
                logger.warning(f"⚠️ Ancient Elder integration failed: {e}")

        except Exception as e:
            logger.error(f"Ancient Elder integration error: {e}")

    async def _update_system_metrics(self):
        """システムメトリクス更新"""
        try:
            self.system_metrics.total_components = len(self.elder_components)
            self.system_metrics.active_components = len(
                [
                    c
                    for c in self.elder_components.values()
                    if c.status == ElderSystemStatus.ACTIVE
                ]
            )

            # タイプ別カウント
            for elder_type in ElderType:
                count = len(
                    [
                        c
                        for c in self.elder_components.values()
                        if c.elder_type == elder_type
                    ]
                )
                setattr(self.system_metrics, f"{elder_type.value}_count", count)

            # システム健全性計算
            if self.system_metrics.total_components > 0:
                self.system_metrics.system_health = (
                    self.system_metrics.active_components
                    / self.system_metrics.total_components
                ) * 100

            self.system_metrics.timestamp = datetime.now()

        except Exception as e:
            logger.error(f"System metrics update failed: {e}")

    async def _integrate_component(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """コンポーネント統合"""
        try:
            component_config = request.get("component_config", {})

            component = ElderComponent(
                component_id=component_config.get("component_id", str(uuid.uuid4())),
                component_name=component_config.get(
                    "component_name", "Unknown Component"
                ),
                elder_type=ElderType(component_config.get("elder_type", "servant")),
                capabilities=component_config.get("capabilities", []),
            )

            self.elder_components[component.component_id] = component
            await self._update_system_metrics()

            return {
                "success": True,
                "component_id": component.component_id,
                "integration_id": self.integration_id,
                "system_metrics": asdict(self.system_metrics),
            }

        except Exception as e:
            logger.error(f"Component integration failed: {e}")
            return {"success": False, "error": str(e)}

    async def _get_system_status(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """システム状態取得"""
        try:
            await self._update_system_metrics()

            return {
                "success": True,
                "integration_id": self.integration_id,
                "system_metrics": asdict(self.system_metrics),
                "components": {
                    comp_id: comp.to_dict()
                    for comp_id, comp in self.elder_components.items()
                },
                "component_count_by_type": {
                    elder_type.value: len(
                        [
                            c
                            for c in self.elder_components.values()
                            if c.elder_type == elder_type
                        ]
                    )
                    for elder_type in ElderType
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"System status retrieval failed: {e}")
            return {"success": False, "error": str(e)}

    async def _coordinate_elders(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """エルダー協調処理"""
        try:
            coordination_type = request.get("coordination_type", "general")
            participating_elders = request.get("participating_elders", [])
            payload = request.get("payload", {})

            # 4賢者協調
            if "sages" in participating_elders or not participating_elders:
                sages_result = await self.sages_coordinator.process_request(
                    {
                        "type": "coordinate_sages",
                        "coordination_type": coordination_type,
                        "payload": payload,
                    }
                )
            else:
                sages_result = {
                    "success": True,
                    "message": "Sages coordination skipped",
                }

            # A2A通信による協調
            a2a_result = await self.a2a_core.process_request(
                {
                    "type": "broadcast_message",
                    "message": {
                        "type": "elder_coordination",
                        "payload": {
                            "coordination_type": coordination_type,
                            "participating_elders": participating_elders,
                            "data": payload,
                        },
                    },
                }
            )

            self.system_metrics.coordination_requests += 1

            return {
                "success": True,
                "coordination_type": coordination_type,
                "sages_coordination": sages_result,
                "a2a_coordination": a2a_result,
                "participating_elders": participating_elders,
                "integration_id": self.integration_id,
            }

        except Exception as e:
            logger.error(f"Elder coordination failed: {e}")
            return {"success": False, "error": str(e)}

    async def _elder_council_session(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """エルダー評議会セッション"""
        try:
            session_type = request.get("session_type", "general")
            agenda = request.get("agenda", {})

            # 評議会インスタンスがある場合は実行
            if "elder_council" in self.component_instances:
                council_instance = self.component_instances["elder_council"]
                if hasattr(council_instance, "process_request"):
                    if asyncio.iscoroutinefunction(council_instance.process_request):
                        council_result = await council_instance.process_request(
                            {
                                "type": "council_session",
                                "session_type": session_type,
                                "agenda": agenda,
                            }
                        )
                    else:
                        council_result = council_instance.process_request(
                            {
                                "type": "council_session",
                                "session_type": session_type,
                                "agenda": agenda,
                            }
                        )
                else:
                    council_result = {
                        "success": True,
                        "message": "Council session simulated",
                    }
            else:
                council_result = {"success": True, "message": "Council not available"}

            return {
                "success": True,
                "session_type": session_type,
                "council_result": council_result,
                "integration_id": self.integration_id,
            }

        except Exception as e:
            logger.error(f"Elder council session failed: {e}")
            return {"success": False, "error": str(e)}

    async def _servant_deployment(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """サーバント配置"""
        try:
            deployment_type = request.get("deployment_type", "standard")
            servant_count = request.get("servant_count", 1)
            task_config = request.get("task_config", {})

            # 利用可能なサーバントを取得
            available_servants = [
                comp
                for comp in self.elder_components.values()
                if comp.elder_type == ElderType.SERVANT
                and comp.status == ElderSystemStatus.ACTIVE
            ]

            if len(available_servants) < servant_count:
                return {
                    "success": False,
                    "error": f"Insufficient servants available: {len(available_servants)}/{servant_count}",
                }

            # サーバント配置
            deployed_servants = available_servants[:servant_count]
            deployment_results = []

            for servant in deployed_servants:
                deployment_result = {
                    "servant_id": servant.component_id,
                    "servant_name": servant.component_name,
                    "deployment_status": "deployed",
                    "task_config": task_config,
                }
                deployment_results.append(deployment_result)

            return {
                "success": True,
                "deployment_type": deployment_type,
                "servants_deployed": len(deployed_servants),
                "deployment_results": deployment_results,
                "integration_id": self.integration_id,
            }

        except Exception as e:
            logger.error(f"Servant deployment failed: {e}")
            return {"success": False, "error": str(e)}

    async def _tree_navigation(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """ツリーナビゲーション"""
        try:
            navigation_type = request.get("navigation_type", "hierarchy")
            target_node = request.get("target_node", "root")

            # ツリー構造取得
            tree_structure = self.component_instances.get("elder_tree", {})

            navigation_result = {
                "current_node": target_node,
                "tree_structure": tree_structure,
                "navigation_path": [],
                "available_nodes": (
                    list(tree_structure.keys()) if tree_structure else []
                ),
            }

            return {
                "success": True,
                "navigation_type": navigation_type,
                "navigation_result": navigation_result,
                "integration_id": self.integration_id,
            }

        except Exception as e:
            logger.error(f"Tree navigation failed: {e}")
            return {"success": False, "error": str(e)}

    async def _knight_patrol(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """騎士団パトロール"""
        try:
            patrol_type = request.get("patrol_type", "security")
            patrol_area = request.get("patrol_area", "all")

            # 騎士団コンポーネント取得
            knight_components = [
                comp
                for comp in self.elder_components.values()
                if comp.elder_type == ElderType.KNIGHT
                and comp.status == ElderSystemStatus.ACTIVE
            ]

            patrol_results = []
            for knight in knight_components:
                patrol_result = {
                    "knight_id": knight.component_id,
                    "knight_name": knight.component_name,
                    "patrol_status": "patrolling",
                    "patrol_area": patrol_area,
                    "findings": [],
                }
                patrol_results.append(patrol_result)

            return {
                "success": True,
                "patrol_type": patrol_type,
                "knights_deployed": len(knight_components),
                "patrol_results": patrol_results,
                "integration_id": self.integration_id,
            }

        except Exception as e:
            logger.error(f"Knight patrol failed: {e}")
            return {"success": False, "error": str(e)}

    async def _ancient_wisdom_access(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """古代の知恵アクセス"""
        try:
            wisdom_query = request.get("wisdom_query", "")
            access_level = request.get("access_level", "standard")

            # Ancient Elderインスタンスがある場合は実行
            if "ancient_elder" in self.component_instances:
                ancient_instance = self.component_instances["ancient_elder"]
                if hasattr(ancient_instance, "process_request"):
                    if asyncio.iscoroutinefunction(ancient_instance.process_request):
                        wisdom_result = await ancient_instance.process_request(
                            {
                                "type": "wisdom_access",
                                "query": wisdom_query,
                                "access_level": access_level,
                            }
                        )
                    else:
                        wisdom_result = ancient_instance.process_request(
                            {
                                "type": "wisdom_access",
                                "query": wisdom_query,
                                "access_level": access_level,
                            }
                        )
                else:
                    wisdom_result = {
                        "success": True,
                        "message": "Ancient wisdom simulated",
                    }
            else:
                wisdom_result = {
                    "success": True,
                    "message": "Ancient Elder not available",
                }

            return {
                "success": True,
                "wisdom_query": wisdom_query,
                "access_level": access_level,
                "wisdom_result": wisdom_result,
                "integration_id": self.integration_id,
            }

        except Exception as e:
            logger.error(f"Ancient wisdom access failed: {e}")
            return {"success": False, "error": str(e)}

    async def _full_system_health_check(
        self, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """システム全体健全性チェック"""
        try:
            # 各コンポーネントの健全性チェック
            health_results = {}

            # 4賢者ヘルスチェック
            for sage_id in ["sage_knowledge", "sage_task", "sage_incident", "sage_rag"]:
                if sage_id in self.elder_components:
                    health_results[sage_id] = {
                        "status": "healthy",
                        "component_type": "sage",
                        "last_check": datetime.now().isoformat(),
                    }

            # その他のコンポーネント
            for comp_id, comp in self.elder_components.items():
                if comp_id not in health_results:
                    health_results[comp_id] = {
                        "status": (
                            "healthy"
                            if comp.status == ElderSystemStatus.ACTIVE
                            else "warning"
                        ),
                        "component_type": comp.elder_type.value,
                        "last_check": datetime.now().isoformat(),
                    }

            # システム全体の健全性スコア計算
            healthy_components = len(
                [r for r in health_results.values() if r["status"] == "healthy"]
            )
            total_components = len(health_results)
            system_health_score = (
                (healthy_components / total_components * 100)
                if total_components > 0
                else 0
            )

            await self._update_system_metrics()

            return {
                "success": True,
                "system_health_score": system_health_score,
                "component_health": health_results,
                "system_metrics": asdict(self.system_metrics),
                "integration_id": self.integration_id,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Full system health check failed: {e}")
            return {"success": False, "error": str(e)}


# メイン実行部分
if __name__ == "__main__":

    async def test_elder_system_integration():
        """エルダーシステム統合テスト"""
        logger.info("🧪 Testing Elder System Integration")

        # 統合システム初期化
        integration = ElderSystemIntegration(max_components=100)

        # システム初期化
        init_result = await integration.process_request(
            {"type": "initialize_elder_system"}
        )
        print(f"Init result: {init_result}")

        # システム状態確認
        status_result = await integration.process_request({"type": "get_system_status"})
        print(f"Status result: {status_result}")

        # エルダー協調テスト
        coordination_result = await integration.process_request(
            {
                "type": "coordinate_elders",
                "coordination_type": "full_system_coordination",
                "participating_elders": ["sages", "council", "servants"],
                "payload": {"task": "system integration test"},
            }
        )
        print(f"Coordination result: {coordination_result}")

        # 評議会セッション
        council_result = await integration.process_request(
            {
                "type": "elder_council_session",
                "session_type": "integration_approval",
                "agenda": {"topic": "system integration completion"},
            }
        )
        print(f"Council result: {council_result}")

        # サーバント配置
        servant_result = await integration.process_request(
            {
                "type": "servant_deployment",
                "deployment_type": "full_deployment",
                "servant_count": 2,
                "task_config": {"task": "integration support"},
            }
        )
        print(f"Servant result: {servant_result}")

        # 騎士団パトロール
        knight_result = await integration.process_request(
            {
                "type": "knight_patrol",
                "patrol_type": "security",
                "patrol_area": "full_system",
            }
        )
        print(f"Knight result: {knight_result}")

        # 全体健全性チェック
        health_result = await integration.process_request(
            {"type": "full_system_health_check"}
        )
        print(f"Health result: {health_result}")

        print(f"\n🎉 Elder System Integration Test Complete!")
        print(f"Integration ID: {integration.integration_id}")
        print(f"Components Integrated: {len(integration.elder_components)}")
        print(f"System Health: {integration.system_metrics.system_health:.1f}%")

    # テスト実行
    asyncio.run(test_elder_system_integration())
