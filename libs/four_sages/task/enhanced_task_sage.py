#!/usr/bin/env python3
"""
Enhanced Task Sage - 追跡システム統合版
Created: 2025-07-17
Author: Claude Elder
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

# プロジェクトルートインポート
import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.four_sages.task.task_sage import TaskSage, TaskEntry, TaskStatus
from libs.four_sages.task.dynamic_priority_engine import DynamicPriorityEngine
from libs.four_sages.task.execution_time_predictor import ExecutionTimePredictor
from libs.four_sages.task.resource_optimization_engine import ResourceOptimizationEngine
from libs.four_sages.task.task_scheduling_optimizer import TaskSchedulingOptimizer, SchedulingConstraint
from libs.tracking.unified_tracking_db import UnifiedTrackingDB
from core.lightweight_logger import get_logger

logger = get_logger("enhanced_task_sage")

class EnhancedTaskSage(TaskSage):
    """追跡システム統合版 Task Sage"""
    
    def __init__(self):
        super().__init__()
        
        # 追跡データベース初期化
        self.tracking_db = UnifiedTrackingDB()
        
        # 統合コンポーネント初期化
        self.priority_engine = DynamicPriorityEngine(self, self.tracking_db)
        self.time_predictor = ExecutionTimePredictor(self.tracking_db)
        self.resource_engine = ResourceOptimizationEngine(self, self.tracking_db)
        self.scheduling_optimizer = TaskSchedulingOptimizer(
            self, self.priority_engine, self.time_predictor
        )
        
        # 拡張機能フラグ
        self.enhanced_features = {
            'dynamic_priority': True,
            'time_prediction': True,
            'resource_optimization': True,
            'smart_scheduling': True
        }
        
        logger.info("🚀 Enhanced Task Sage initialized with tracking integration")
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """拡張リクエスト処理"""
        request_type = request.get("type", "unknown")
        
        # 新しい統合機能のリクエスト処理
        if request_type == "optimize_schedule":
            return await self._optimize_schedule_request(request)
        elif request_type == "predict_completion":
            return await self._predict_completion_request(request)
        elif request_type == "analyze_resources":
            return await self._analyze_resources_request(request)
        elif request_type == "get_recommendations":
            return await self._get_recommendations_request(request)
        elif request_type == "update_tracking":
            return await self._update_tracking_request(request)
        else:
            # 基本クラスの処理にフォールバック
            return await super().process_request(request)
    
    async def _optimize_schedule_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """スケジュール最適化リクエスト"""
        try:
            # 対象タスクを取得
            status = request.get("status", "pending")
            tasks = await self.database.search_tasks(
                status=TaskStatus(status),
                limit=request.get("limit", 100)
            )
            
            if not tasks:
                return {
                    "success": True,
                    "message": "No tasks to optimize",
                    "optimized_schedule": []
                }
            
            # 制約条件を設定
            constraints = SchedulingConstraint(
                max_parallel_tasks=request.get("max_parallel", 10),
                respect_due_dates=request.get("respect_due_dates", True),
                allow_overtime=request.get("allow_overtime", False)
            )
            
            # スケジュール最適化実行
            optimized_schedule = await self.scheduling_optimizer.optimize_schedule(
                tasks, constraints
            )
            
            # リソース最適化も実行
            resource_result = await self.resource_engine.optimize_resource_allocation(tasks)
            
            # 結果を統合
            schedule_data = []
            for scheduled_task in optimized_schedule:
                schedule_data.append({
                    'task_id': scheduled_task.task.id,
                    'title': scheduled_task.task.title,
                    'priority': scheduled_task.task.priority.value,
                    'dynamic_priority': scheduled_task.dynamic_priority,
                    'scheduled_start': scheduled_task.scheduled_start.isoformat(),
                    'scheduled_end': scheduled_task.scheduled_end.isoformat(),
                    'predicted_duration': scheduled_task.predicted_time,
                    'parallel_group': scheduled_task.parallel_group
                })
            
            # ガントチャートデータも生成
            gantt_data = self.scheduling_optimizer.get_gantt_chart_data(optimized_schedule)
            
            return {
                "success": True,
                "optimized_schedule": schedule_data,
                "gantt_chart": gantt_data,
                "resource_optimization": resource_result,
                "metrics": {
                    "total_tasks": len(tasks),
                    "scheduled_tasks": len(optimized_schedule),
                    "parallelization_factor": resource_result.get('parallel_groups', []),
                    "estimated_total_time": sum(st.predicted_time for st in optimized_schedule)
                }
            }
            
        except Exception as e:
            logger.error(f"Schedule optimization failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _predict_completion_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """完了時間予測リクエスト"""
        try:
            task_id = request.get("task_id")
            if not task_id:
                return {
                    "success": False,
                    "error": "Task ID required"
                }
            
            # タスクを取得
            task = await self.database.retrieve_task(task_id)
            if not task:
                return {
                    "success": False,
                    "error": "Task not found"
                }
            
            # 実行時間予測
            predicted_time, confidence_interval = await self.time_predictor.predict_execution_time(task)
            
            # 動的優先度計算
            dynamic_priority = await self.priority_engine.calculate_dynamic_priority(task)
            
            # 現在の実行状況を考慮した開始時刻予測
            pending_tasks = await self.database.search_tasks(
                status=TaskStatus.PENDING,
                limit=100
            )
            
            # 簡易的な開始時刻計算
            queue_position = len([t for t in pending_tasks if t.id != task_id])
            estimated_start = datetime.now() + timedelta(seconds=queue_position * 300)  # 5分/タスク
            estimated_end = estimated_start + timedelta(seconds=predicted_time)
            
            return {
                "success": True,
                "prediction": {
                    "task_id": task_id,
                    "predicted_duration_seconds": predicted_time,
                    "confidence_interval": {
                        "lower": confidence_interval[0],
                        "upper": confidence_interval[1]
                    },
                    "dynamic_priority": dynamic_priority,
                    "estimated_start": estimated_start.isoformat(),
                    "estimated_completion": estimated_end.isoformat(),
                    "queue_position": queue_position
                },
                "accuracy_metrics": self.time_predictor.get_model_accuracy(task.task_type)
            }
            
        except Exception as e:
            logger.error(f"Completion prediction failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_resources_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """リソース分析リクエスト"""
        try:
            # 現在のシステムリソース
            current_resources = await self.resource_engine.resource_monitor.get_current_usage()
            
            # 実行中タスクのリソース使用状況
            executing_tasks = await self.database.search_tasks(
                status=TaskStatus.IN_PROGRESS,
                limit=50
            )
            
            # リソース効率スコア
            efficiency_score = self.resource_engine.get_resource_efficiency_score()
            
            # 平均リソース使用状況
            avg_resources = self.resource_engine.resource_monitor.get_average_usage(minutes=10)
            
            return {
                "success": True,
                "resource_analysis": {
                    "current": {
                        "cpu_percent": current_resources.cpu_percent,
                        "memory_percent": current_resources.memory_percent,
                        "cpu_cores": current_resources.cpu_cores,
                        "memory_available_gb": current_resources.memory_available_gb,
                        "disk_io_mb": current_resources.disk_io_read_mb + current_resources.disk_io_write_mb,
                        "network_io_mb": current_resources.network_io_send_mb + current_resources.network_io_recv_mb
                    },
                    "average_10min": {
                        "cpu_percent": avg_resources.cpu_percent if avg_resources else 0,
                        "memory_percent": avg_resources.memory_percent if avg_resources else 0
                    } if avg_resources else None,
                    "executing_tasks": len(executing_tasks),
                    "efficiency_score": efficiency_score,
                    "recommendations": [
                        f"System is {'healthy' if efficiency_score > 0.7 else 'under stress'}",
                        f"{len(executing_tasks)} tasks currently executing"
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Resource analysis failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_recommendations_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """タスク推奨リクエスト"""
        try:
            limit = request.get("limit", 10)
            
            # 動的優先度に基づく推奨タスク
            priority_recommendations = await self.priority_engine.get_priority_recommendations(limit)
            
            # スケジューリングメトリクス
            schedule_metrics = await self.scheduling_optimizer.get_schedule_metrics()
            
            # リソース最適化推奨
            pending_tasks = await self.database.search_tasks(
                status=TaskStatus.PENDING,
                limit=50
            )
            
            resource_optimization = await self.resource_engine.optimize_resource_allocation(
                pending_tasks[:limit]
            )
            
            return {
                "success": True,
                "recommendations": {
                    "priority_tasks": priority_recommendations,
                    "schedule_metrics": schedule_metrics,
                    "resource_recommendations": resource_optimization.get('recommendations', []),
                    "summary": {
                        "high_priority_count": len([r for r in priority_recommendations if r['dynamic_priority'] > 100]),
                        "optimal_parallel_groups": len(resource_optimization.get('parallel_groups', [])),
                        "system_efficiency": self.resource_engine.get_resource_efficiency_score()
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Get recommendations failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _update_tracking_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """追跡データ更新リクエスト"""
        try:
            task_id = request.get("task_id")
            if not task_id:
                return {
                    "success": False,
                    "error": "Task ID required"
                }
            
            # タスクを取得
            task = await self.database.retrieve_task(task_id)
            if not task:
                return {
                    "success": False,
                    "error": "Task not found"
                }
            
            # 追跡データを更新
            tracking_data = {
                'task_id': task_id,
                'description': task.title,
                'priority': task.priority.value,
                'status': task.status.value,
                'created_at': task.created_at,
                'metadata': {
                    'task_type': task.task_type.value,
                    'tags': list(task.tags),
                    'dependency_count': len(task.dependencies),
                    'resource_count': len(task.resources),
                    'has_due_date': task.due_date is not None,
                    'description_length': len(task.description),
                    'estimated_hours': task.estimated_duration.total_seconds() / 3600 if task.estimated_duration else 0
                }
            }
            
            # 実行時間データがある場合
            if task.actual_duration:
                tracking_data['execution_time_seconds'] = task.actual_duration.total_seconds()
                tracking_data['completed_at'] = task.completed_at
                
                # 予測モデルを更新
                await self.time_predictor.update_prediction(
                    task_id, task.actual_duration.total_seconds()
                )
                
                # 優先度学習を更新
                performance_data = {
                    'success': task.status == TaskStatus.COMPLETED,
                    'execution_time': task.actual_duration.total_seconds(),
                    'quality_score': 0.8  # デフォルト値
                }
                await self.priority_engine.update_priority_learning(task_id, performance_data)
            
            # UnifiedTrackingDBに記録
            result = self.tracking_db.create_task(
                task_id=task_id,
                description=task.title,
                priority=task.priority.value,
                metadata=tracking_data['metadata']
            )
            
            return {
                "success": True,
                "message": "Tracking data updated",
                "task_id": task_id,
                "tracking_result": result
            }
            
        except Exception as e:
            logger.error(f"Update tracking failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_capabilities(self) -> List[str]:
        """拡張能力一覧"""
        base_capabilities = super().get_capabilities()
        enhanced_capabilities = [
            "dynamic_priority_calculation",     # 動的優先度計算
            "execution_time_prediction",        # 実行時間予測
            "resource_optimization",            # リソース最適化
            "smart_task_scheduling",           # スマートスケジューリング
            "performance_tracking",            # パフォーマンス追跡
            "ml_based_predictions",            # 機械学習ベース予測
            "real_time_monitoring",            # リアルタイム監視
            "advanced_analytics"               # 高度な分析
        ]
        
        return base_capabilities + enhanced_capabilities

# グローバルインスタンス
enhanced_task_sage = None

def get_enhanced_task_sage_instance():
    """Enhanced Task Sage インスタンスを取得"""
    global enhanced_task_sage
    if enhanced_task_sage is None:
        enhanced_task_sage = EnhancedTaskSage()
    return enhanced_task_sage

# Export
__all__ = ['EnhancedTaskSage', 'get_enhanced_task_sage_instance']