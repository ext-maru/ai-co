#!/usr/bin/env python3
"""
Elder Flow Engine - エルダーフロー実行エンジン
Created: 2025-07-19
Author: Claude Elder
"""

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.elders_legacy import DomainBoundary, EldersFlowLegacy, enforce_boundary
from core.lightweight_logger import get_logger
from elders_guild.elder_tree.elder_system.flow.elder_flow_orchestrator import ElderFlowOrchestrator
from elders_guild.elder_tree.elder_system.flow.pid_lock_manager import PIDLockContext, PIDLockManager
from elders_guild.elder_tree.tracking.unified_tracking_db import UnifiedTrackingDB

logger = get_logger("elder_flow_engine")


class ElderFlowEngine(EldersFlowLegacy):
    """Elder Flow実行エンジン"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__(name="ElderFlowEngine")
        self.orchestrator = ElderFlowOrchestrator()
        self.tracking_db = UnifiedTrackingDB()
        self.active_flows = {}
        self.workflows = {}
        self.pid_lock_manager = PIDLockManager(lock_dir="/tmp/elder_flow_locks")

    @enforce_boundary(DomainBoundary.MONITORING, "execute_elder_flow")
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Elder Flow実行要求の処理"""
        try:
            request_type = request.get("type", "execute")

            if request_type == "execute":
                return await self.execute_elder_flow(request)
            elif request_type == "status":
                return await self.get_status()
            elif request_type == "workflow":
                return await self.manage_workflow(request)
            else:
                return {"error": f"Unknown request type: {request_type}"}

        except Exception as e:
            logger.error(f"Elder Flow Engine処理エラー: {e}")
            return {"error": str(e)}

    async def execute_elder_flow(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Elder Flow実行"""
        task_name = request.get("task_name", "")
        priority = request.get("priority", "medium")
        flow_id = str(uuid.uuid4())

        # PIDロックのチェック
        lock_info = self.pid_lock_manager.is_task_locked(task_name)
        if lock_info:
            logger.warning(
                f"🔒 タスク '{task_name}' は既に実行中です (PID: {lock_info['pid']}, 開始時刻: {lock_info['started_at']})"
            )
            return {
                "error": "Task already running",
                "task_name": task_name,
                "running_pid": lock_info["pid"],
                "started_at": lock_info["started_at"],
            }

        logger.info(f"🌊 Elder Flow実行開始: {task_name} (ID: {flow_id})")

        # フロー実行データ
        flow_data = {
            "flow_id": flow_id,
            "task_name": task_name,
            "priority": priority,
            "start_time": datetime.now().isoformat(),
            "status": "RUNNING",
            "phase": "INITIALIZATION",
            "results": {},
        }

        self.active_flows[flow_id] = flow_data

        try:
            # PIDロックを取得してタスクを実行
            with PIDLockContext(self.pid_lock_manager, task_name, flow_data):
                # Phase 1: 4賢者会議
                logger.info("🧙‍♂️ Phase 1: 4賢者会議開始")
                flow_data["phase"] = "SAGE_COUNCIL"

            sage_council_result = await self.orchestrator.execute_sage_council(
                {"task_name": task_name, "priority": priority, "flow_id": flow_id}
            )

            flow_data["results"]["sage_council"] = sage_council_result

            # Phase 2: エルダーサーバント実行
            logger.info("🤖 Phase 2: エルダーサーバント実行開始")
            flow_data["phase"] = "SERVANT_EXECUTION"

            servant_result = await self.orchestrator.execute_elder_servants(
                {
                    "task_name": task_name,
                    "sage_recommendations": sage_council_result.get(
                        "recommendations", []
                    ),
                    "flow_id": flow_id,
                }
            )

            flow_data["results"]["servant_execution"] = servant_result

            # Phase 3: 品質ゲート
            logger.info("🔍 Phase 3: 品質ゲート開始")
            flow_data["phase"] = "QUALITY_GATE"

            quality_gate_result = await self.orchestrator.execute_quality_gate(
                {
                    "task_name": task_name,
                    "implementation_results": servant_result,
                    "flow_id": flow_id,
                }
            )

            flow_data["results"]["quality_gate"] = quality_gate_result

            # Phase 4: 評議会報告
            logger.info("📊 Phase 4: 評議会報告開始")
            flow_data["phase"] = "COUNCIL_REPORT"

            council_report_result = await self.orchestrator.execute_council_report(
                {
                    "task_name": task_name,
                    "all_results": flow_data["results"],
                    "flow_id": flow_id,
                }
            )

            flow_data["results"]["council_report"] = council_report_result

            # Phase 5: Git自動化
            logger.info("📤 Phase 5: Git自動化開始")
            flow_data["phase"] = "GIT_AUTOMATION"

            git_automation_result = await self.orchestrator.execute_git_automation(
                {
                    "task_name": task_name,
                    "implementation_results": servant_result,
                    "flow_id": flow_id,
                }
            )

            flow_data["results"]["git_automation"] = git_automation_result

            # 完了
            flow_data["status"] = "COMPLETED"
            flow_data["end_time"] = datetime.now().isoformat()
            flow_data["phase"] = "COMPLETED"

            logger.info(f"✅ Elder Flow実行完了: {task_name} (ID: {flow_id})")

            # トラッキングDB記録
            await self.tracking_db.save_execution_record(
                {
                    "flow_type": "elder_flow",
                    "flow_id": flow_id,
                    "task_name": task_name,
                    "priority": priority,
                    "status": "COMPLETED",
                    "results": flow_data["results"],
                    "start_time": flow_data["start_time"],
                    "end_time": flow_data["end_time"],
                }
            )

            return {
                "flow_id": flow_id,
                "task_name": task_name,
                "status": "COMPLETED",
                "results": flow_data["results"],
                "execution_time": flow_data["end_time"],
            }

        except Exception as e:
            logger.error(f"❌ Elder Flow実行エラー: {e}")
            flow_data["status"] = "ERROR"
            flow_data["error"] = str(e)
            flow_data["end_time"] = datetime.now().isoformat()

            # エラーもトラッキングDB記録
            await self.tracking_db.save_execution_record(
                {
                    "flow_type": "elder_flow",
                    "flow_id": flow_id,
                    "task_name": task_name,
                    "priority": priority,
                    "status": "ERROR",
                    "error": str(e),
                    "start_time": flow_data["start_time"],
                    "end_time": flow_data["end_time"],
                }
            )

            return {
                "flow_id": flow_id,
                "task_name": task_name,
                "status": "ERROR",
                "error": str(e),
            }

    async def get_status(self) -> Dict[str, Any]:
        """エンジンステータス取得"""
        return {
            "engine_status": "ACTIVE",
            "active_flows_count": len(self.active_flows),
            "workflows_count": len(self.workflows),
            "timestamp": datetime.now().isoformat(),
        }

    async def get_active_flows(self) -> List[Dict[str, Any]]:
        """アクティブフロー一覧取得"""
        return [
            {
                "flow_id": flow_id,
                "task_name": data["task_name"],
                "status": data["status"],
                "phase": data["phase"],
                "start_time": data["start_time"],
            }
            for flow_id, data in self.active_flows.items()
        ]

    async def create_workflow(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """ワークフロー作成"""
        workflow_name = request.get("name", "")
        execute = request.get("execute", False)

        if not workflow_name:
            return {"error": "ワークフロー名が必要です"}

        workflow_id = str(uuid.uuid4())
        workflow_data = {
            "workflow_id": workflow_id,
            "name": workflow_name,
            "created_at": datetime.now().isoformat(),
            "status": "CREATED",
            "tasks": [],
        }

        self.workflows[workflow_id] = workflow_data

        result = {
            "workflow_id": workflow_id,
            "name": workflow_name,
            "status": "CREATED",
        }

        if execute:
            # ワークフロー実行
            execution_result = await self.execute_elder_flow(
                {
                    "task_name": f"ワークフロー実行: {workflow_name}",
                    "priority": "high",
                    "workflow_id": workflow_id,
                }
            )
            result["execution"] = execution_result

        return result

    async def list_workflows(self) -> List[Dict[str, Any]]:
        """ワークフロー一覧取得"""
        return [
            {
                "workflow_id": workflow_id,
                "name": data["name"],
                "status": data["status"],
                "created_at": data["created_at"],
            }
            for workflow_id, data in self.workflows.items()
        ]

    async def manage_workflow(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """ワークフロー管理"""
        action = request.get("action", "")

        if action == "create":
            return await self.create_workflow(request)
        elif action == "list":
            return {"workflows": await self.list_workflows()}
        else:
            return {"error": f"Unknown workflow action: {action}"}

    def validate_request(self, request: Dict[str, Any]) -> bool:
        """リクエスト検証"""
        return isinstance(request, dict)

    def get_capabilities(self) -> List[str]:
        """機能一覧"""
        return [
            "elder_flow_execution",
            "multi_phase_orchestration",
            "workflow_management",
            "status_monitoring",
            "tracking_integration",
        ]


# エクスポート用のファクトリ関数
def create_elder_flow_engine() -> ElderFlowEngine:
    """Elder Flow Engine作成"""
    return ElderFlowEngine()


if __name__ == "__main__":
    # テスト実行
    async def test_engine():
        """test_engineテストメソッド"""
        engine = create_elder_flow_engine()

        # テストタスク実行
        result = await engine.execute_elder_flow(
            {"task_name": "テストタスク", "priority": "medium"}
        )

        print(f"実行結果: {result}")

    asyncio.run(test_engine())
