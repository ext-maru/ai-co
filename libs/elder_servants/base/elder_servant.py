"""
エルダーサーバント基盤クラス
4賢者システムの実行部隊として機能する32専門ワーカーの基盤
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib


class ServantCategory(Enum):
    """サーバント分類"""
    DWARF = "dwarf"          # ドワーフ工房（開発製作）
    WIZARD = "wizard"        # RAGウィザーズ（調査研究）
    ELF = "elf"             # エルフの森（監視メンテナンス）


class TaskStatus(Enum):
    """タスク実行状況"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """タスク優先度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ServantCapability:
    """サーバント能力定義"""
    
    def __init__(self, name: str, description: str, input_types: List[str], 
                 output_types: List[str], complexity: int = 1):
        self.name = name
        self.description = description
        self.input_types = input_types
        self.output_types = output_types
        self.complexity = complexity  # 1-10 (実行複雑度)
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_types": self.input_types,
            "output_types": self.output_types,
            "complexity": self.complexity
        }


class TaskResult:
    """タスク実行結果"""
    
    def __init__(self, task_id: str, servant_id: str, status: TaskStatus,
                 result_data: Dict[str, Any] = None, error_message: str = None,
                 execution_time_ms: float = 0.0, quality_score: float = 0.0):
        self.task_id = task_id
        self.servant_id = servant_id
        self.status = status
        self.result_data = result_data or {}
        self.error_message = error_message
        self.execution_time_ms = execution_time_ms
        self.quality_score = quality_score
        self.completed_at = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "servant_id": self.servant_id,
            "status": self.status.value,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms,
            "quality_score": self.quality_score,
            "completed_at": self.completed_at.isoformat()
        }


class ElderServant(ABC):
    """エルダーサーバント基盤クラス"""
    
    def __init__(self, servant_id: str, servant_name: str, category: ServantCategory, 
                 specialization: str, capabilities: List[ServantCapability]):
        self.servant_id = servant_id
        self.servant_name = servant_name
        self.category = category
        self.specialization = specialization
        self.capabilities = capabilities
        
        # ロガー設定
        self.logger = logging.getLogger(f"elder_servants.{servant_id}")
        
        # 実行統計
        self.stats = {
            "tasks_executed": 0,
            "tasks_succeeded": 0,
            "tasks_failed": 0,
            "total_execution_time_ms": 0.0,
            "average_quality_score": 0.0,
            "last_activity": datetime.now(),
            "created_at": datetime.now()
        }
        
        # 現在実行中のタスク
        self.current_tasks: Dict[str, Dict[str, Any]] = {}
        
        # 4賢者との連携用
        self.sage_connections = {}
        
        # Iron Will品質基準
        self.quality_threshold = 95.0  # 95%以上必須
        
        self.logger.info(f"Elder Servant {servant_name} ({servant_id}) initialized")
    
    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> TaskResult:
        """
        タスク実行（各サーバントで具体実装）
        
        Args:
            task: 実行タスク情報
            
        Returns:
            TaskResult: 実行結果
        """
        pass
    
    @abstractmethod
    def get_specialized_capabilities(self) -> List[ServantCapability]:
        """
        専門特化能力の取得（各サーバントで具体実装）
        
        Returns:
            List[ServantCapability]: 専門能力一覧
        """
        pass
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        リクエスト処理（統一インターフェース）
        
        Args:
            request: 処理リクエスト
            
        Returns:
            Dict[str, Any]: 処理結果
        """
        start_time = datetime.now()
        request_id = request.get("request_id", str(uuid.uuid4()))
        
        try:
            request_type = request.get("type", "unknown")
            
            if request_type == "execute_task":
                task = request.get("task", {})
                task["request_id"] = request_id
                result = await self.execute_task(task)
                
                # 統計更新
                await self._update_stats(result)
                
                return {
                    "success": True,
                    "request_id": request_id,
                    "result": result.to_dict()
                }
                
            elif request_type == "health_check":
                return await self.health_check()
                
            elif request_type == "get_capabilities":
                return {
                    "success": True,
                    "capabilities": [cap.to_dict() for cap in self.get_all_capabilities()]
                }
                
            elif request_type == "get_stats":
                return {
                    "success": True,
                    "stats": self.stats.copy()
                }
                
            elif request_type == "cancel_task":
                task_id = request.get("task_id")
                return await self._cancel_task(task_id)
                
            else:
                return {
                    "success": False,
                    "error": f"Unknown request type: {request_type}",
                    "supported_types": [
                        "execute_task", "health_check", "get_capabilities", 
                        "get_stats", "cancel_task"
                    ]
                }
                
        except Exception as e:
            self.logger.error(f"Request processing error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "request_id": request_id
            }
        finally:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.debug(f"Request {request_id} processed in {processing_time:.2f}ms")
    
    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        uptime = datetime.now() - self.stats["created_at"]
        
        # 品質スコア計算
        quality_status = "excellent" if self.stats["average_quality_score"] >= 95 else \
                        "good" if self.stats["average_quality_score"] >= 85 else \
                        "warning" if self.stats["average_quality_score"] >= 75 else "critical"
        
        # 稼働率計算
        success_rate = (self.stats["tasks_succeeded"] / max(self.stats["tasks_executed"], 1)) * 100
        
        return {
            "success": True,
            "servant_id": self.servant_id,
            "servant_name": self.servant_name,
            "category": self.category.value,
            "specialization": self.specialization,
            "status": "healthy" if quality_status in ["excellent", "good"] and success_rate >= 90 else "degraded",
            "uptime_seconds": uptime.total_seconds(),
            "current_tasks": len(self.current_tasks),
            "stats": {
                "tasks_executed": self.stats["tasks_executed"],
                "success_rate": round(success_rate, 2),
                "average_quality_score": round(self.stats["average_quality_score"], 2),
                "quality_status": quality_status
            },
            "capabilities_count": len(self.get_all_capabilities()),
            "last_activity": self.stats["last_activity"].isoformat()
        }
    
    def get_all_capabilities(self) -> List[ServantCapability]:
        """全能力取得（基本能力 + 専門能力）"""
        base_capabilities = [
            ServantCapability(
                "health_check",
                "サーバント健康状態確認",
                ["none"],
                ["health_status"],
                1
            ),
            ServantCapability(
                "task_execution",
                "汎用タスク実行",
                ["task_definition"],
                ["task_result"],
                3
            ),
            ServantCapability(
                "quality_validation",
                "Iron Will品質基準検証",
                ["result_data"],
                ["quality_score"],
                2
            )
        ]
        
        return base_capabilities + self.get_specialized_capabilities()
    
    async def collaborate_with_sages(self, sage_type: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        4賢者との連携
        
        Args:
            sage_type: 連携先賢者タイプ (knowledge/task/incident/rag)
            request: 連携リクエスト
            
        Returns:
            Dict[str, Any]: 連携結果
        """
        self.logger.info(f"Collaborating with {sage_type} sage: {request.get('type', 'unknown')}")
        
        # 実際の実装では賢者システムとの通信を行う
        # プレースホルダー実装
        return {
            "success": True,
            "sage_type": sage_type,
            "message": f"Collaboration request sent to {sage_type} sage",
            "request_id": request.get("request_id", str(uuid.uuid4()))
        }
    
    async def validate_iron_will_quality(self, result_data: Dict[str, Any]) -> float:
        """
        Iron Will品質基準検証
        
        Args:
            result_data: 検証対象データ
            
        Returns:
            float: 品質スコア (0-100)
        """
        quality_score = 0.0
        checks = 0
        
        # 基本品質チェック
        if result_data.get("success", False):
            quality_score += 30
        checks += 1
        
        # エラーハンドリング確認
        if "error" not in result_data or result_data.get("error") is None:
            quality_score += 20
        checks += 1
        
        # 完全性確認
        required_fields = ["status", "data"]
        if all(field in result_data for field in required_fields):
            quality_score += 25
        checks += 1
        
        # パフォーマンス確認
        execution_time = result_data.get("execution_time_ms", 0)
        if execution_time > 0 and execution_time < 5000:  # 5秒未満
            quality_score += 25
        checks += 1
        
        # 正規化 - チェック数で割らずに合計スコアを返す
        final_score = quality_score
        
        self.logger.debug(f"Quality validation score: {final_score:.2f}")
        return final_score
    
    async def _update_stats(self, result: TaskResult):
        """統計情報更新"""
        self.stats["tasks_executed"] += 1
        self.stats["total_execution_time_ms"] += result.execution_time_ms
        self.stats["last_activity"] = datetime.now()
        
        if result.status == TaskStatus.COMPLETED:
            self.stats["tasks_succeeded"] += 1
        elif result.status == TaskStatus.FAILED:
            self.stats["tasks_failed"] += 1
        
        # 平均品質スコア更新
        if self.stats["tasks_executed"] > 0:
            total_quality = self.stats["average_quality_score"] * (self.stats["tasks_executed"] - 1)
            self.stats["average_quality_score"] = (total_quality + result.quality_score) / self.stats["tasks_executed"]
    
    async def _cancel_task(self, task_id: str) -> Dict[str, Any]:
        """タスクキャンセル"""
        if task_id in self.current_tasks:
            task_info = self.current_tasks[task_id]
            task_info["status"] = TaskStatus.CANCELLED
            del self.current_tasks[task_id]
            
            self.logger.info(f"Task {task_id} cancelled")
            return {
                "success": True,
                "message": f"Task {task_id} cancelled successfully"
            }
        else:
            return {
                "success": False,
                "error": f"Task {task_id} not found or not running"
            }
    
    def __str__(self) -> str:
        return f"{self.servant_name}({self.servant_id})"
    
    def __repr__(self) -> str:
        return f"<ElderServant {self.servant_name} category={self.category.value} tasks={self.stats['tasks_executed']}>"


class ServantRegistry:
    """エルダーサーバント管理レジストリ"""
    
    def __init__(self):
        self.servants: Dict[str, ElderServant] = {}
        self.category_index: Dict[ServantCategory, List[str]] = {
            ServantCategory.DWARF: [],
            ServantCategory.WIZARD: [],
            ServantCategory.ELF: []
        }
        self.specialization_index: Dict[str, List[str]] = {}
        self.logger = logging.getLogger("elder_servants.registry")
    
    def register_servant(self, servant: ElderServant):
        """サーバント登録"""
        self.servants[servant.servant_id] = servant
        self.category_index[servant.category].append(servant.servant_id)
        
        if servant.specialization not in self.specialization_index:
            self.specialization_index[servant.specialization] = []
        self.specialization_index[servant.specialization].append(servant.servant_id)
        
        self.logger.info(f"Registered servant: {servant.servant_name} ({servant.servant_id})")
    
    def get_servant(self, servant_id: str) -> Optional[ElderServant]:
        """サーバント取得"""
        return self.servants.get(servant_id)
    
    def get_servants_by_category(self, category: ServantCategory) -> List[ElderServant]:
        """カテゴリ別サーバント取得"""
        servant_ids = self.category_index.get(category, [])
        return [self.servants[sid] for sid in servant_ids if sid in self.servants]
    
    def get_servants_by_specialization(self, specialization: str) -> List[ElderServant]:
        """専門分野別サーバント取得"""
        servant_ids = self.specialization_index.get(specialization, [])
        return [self.servants[sid] for sid in servant_ids if sid in self.servants]
    
    def find_best_servant_for_task(self, task: Dict[str, Any]) -> Optional[ElderServant]:
        """タスクに最適なサーバント選出"""
        task_type = task.get("type", "")
        required_capability = task.get("required_capability", "")
        
        best_servant = None
        best_score = 0
        
        for servant in self.servants.values():
            score = 0
            
            # 専門分野マッチング
            if required_capability in servant.specialization:
                score += 50
            
            # 能力マッチング
            for capability in servant.get_all_capabilities():
                if required_capability in capability.name:
                    score += 30
                if task_type in capability.input_types:
                    score += 20
            
            # 現在の負荷考慮
            if len(servant.current_tasks) == 0:
                score += 10
            elif len(servant.current_tasks) < 3:
                score += 5
            
            # 品質スコア考慮
            score += servant.stats["average_quality_score"] * 0.1
            
            if score > best_score:
                best_score = score
                best_servant = servant
        
        return best_servant
    
    async def execute_task_with_best_servant(self, task: Dict[str, Any]) -> TaskResult:
        """最適サーバントでタスク実行"""
        servant = self.find_best_servant_for_task(task)
        
        if not servant:
            return TaskResult(
                task_id=task.get("task_id", str(uuid.uuid4())),
                servant_id="none",
                status=TaskStatus.FAILED,
                error_message="No suitable servant found for task"
            )
        
        self.logger.info(f"Executing task with servant: {servant.servant_name}")
        return await servant.execute_task(task)
    
    async def broadcast_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """全サーバントへのブロードキャスト"""
        results = {}
        tasks = []
        
        for servant_id, servant in self.servants.items():
            task = asyncio.create_task(
                servant.process_request(request),
                name=f"{servant_id}_broadcast"
            )
            tasks.append((servant_id, task))
        
        for servant_id, task in tasks:
            try:
                results[servant_id] = await task
            except Exception as e:
                results[servant_id] = {
                    "success": False,
                    "error": str(e)
                }
        
        return {
            "success": True,
            "broadcast_results": results,
            "responded_servants": len(results)
        }
    
    async def health_check_all(self) -> Dict[str, Any]:
        """全サーバントヘルスチェック"""
        health_results = {}
        
        for servant_id, servant in self.servants.items():
            try:
                health_results[servant_id] = await servant.health_check()
            except Exception as e:
                health_results[servant_id] = {
                    "success": False,
                    "servant_id": servant_id,
                    "status": "error",
                    "error": str(e)
                }
        
        # 全体統計計算
        total_servants = len(self.servants)
        healthy_servants = sum(1 for result in health_results.values() 
                              if result.get("status") == "healthy")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_servants": total_servants,
            "healthy_servants": healthy_servants,
            "health_rate": round((healthy_servants / max(total_servants, 1)) * 100, 2),
            "servants": health_results
        }


# グローバルレジストリインスタンス
servant_registry = ServantRegistry()