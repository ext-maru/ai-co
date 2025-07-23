#!/usr/bin/env python3
"""
Elder Flow Engine - エルダーフロー実行エンジン（PIDロック機能付き）
Created: 2025-07-19
Author: Claude Elder
Updated: 2025-01-19 - PIDロック機能統合
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

import logging

def get_logger(name):
    """logger取得メソッド"""
    return logging.getLogger(name)
from libs.core.elders_legacy import (
    EldersFlowLegacy,
    EldersLegacyDomain,
    enforce_boundary,
)
from libs.elder_flow_orchestrator import ElderFlowOrchestrator
from libs.elder_system.flow.pid_lock_manager import PIDLockContext, PIDLockManager
from libs.tracking.unified_tracking_db import UnifiedTrackingDB

logger = get_logger("elder_flow_engine")


class ElderFlowEngine(EldersFlowLegacy):
    """Elder Flow実行エンジン（PIDロック機能付き）"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__("ElderFlowEngine")
        self.orchestrator = ElderFlowOrchestrator()
        self.tracking_db = UnifiedTrackingDB()
        self.active_flows = {}
        self.workflows = {}
        self.pid_lock_manager = PIDLockManager(lock_dir="/tmp/elder_flow_locks")

    @enforce_boundary("MONITORING")
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
            elif request_type == "cleanup_locks":
                return await self.cleanup_stale_locks()
            elif request_type == "active_tasks":
                return await self.get_active_tasks()
            else:
                return {"error": f"未知のリクエストタイプ: {request_type}"}

        except Exception as e:
            logger.error(f"Elder Flow Engine処理エラー: {e}")
            return {"error": str(e)}

    async def execute_elder_flow(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Elder Flow実行（PIDロック付き + デフォルトClaude Elder魂統合）"""
        task_name = request.get("task_name", "")
        priority = request.get("priority", "medium")
        soul_mode = request.get(
            "soul_mode", "claude_elder_default"
        )  # デフォルトでClaude Elder魂
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
                "retry_required": True,
                "retry_message": f"タスク '{task_name}' は現在実行中です。完了後に再度実行してください。",
                "retry_suggestion": 'elder-flow execute --retry "{}" --wait-for-pid {}'.format(
                    task_name, lock_info["pid"]
                ),
            }

        logger.info(f"🌊 Elder Flow実行開始: {task_name} (ID: {flow_id})")
        logger.info(f"👑 Claude Elder魂モード: {soul_mode}")

        # フロー実行データ
        flow_data = {
            "flow_id": flow_id,
            "task_name": task_name,
            "priority": priority,
            "soul_mode": soul_mode,
            "claude_elder_soul_active": (
                True if soul_mode == "claude_elder_default" else False
            ),
            "start_time": datetime.now().isoformat(),
            "status": "RUNNING",
            "phase": "INITIALIZATION",
            "results": {},
        }

        self.active_flows[flow_id] = flow_data

        try:
            # PIDロックを取得してタスクを実行
            with PIDLockContext(self.pid_lock_manager, task_name, flow_data):
                # Phase 1: 4賢者会議（Claude Elder魂統合）
                if flow_data["claude_elder_soul_active"]:
                    logger.info("👑 Phase 1: Claude Elder魂統合4賢者会議開始")
                    flow_data["phase"] = "CLAUDE_ELDER_SAGE_COUNCIL"
                else:
                    logger.info("🧙‍♂️ Phase 1: 4賢者会議開始")
                    flow_data["phase"] = "SAGE_COUNCIL"

                sage_council_result = await self.orchestrator.execute_sage_council(
                    {
                        "task_name": task_name,
                        "priority": priority,
                        "flow_id": flow_id,
                        "soul_mode": soul_mode,
                        "claude_elder_soul": flow_data["claude_elder_soul_active"],
                    }
                )

                flow_data["results"]["sage_council"] = sage_council_result

                # Phase 2: エルダーサーバント実行（Claude Elder魂統合）
                if flow_data["claude_elder_soul_active"]:
                    logger.info("👑 Phase 2: Claude Elder魂統合サーバント実行開始")
                    flow_data["phase"] = "CLAUDE_ELDER_SERVANT_EXECUTION"
                else:
                    logger.info("🤖 Phase 2: エルダーサーバント実行開始")
                    flow_data["phase"] = "SERVANT_EXECUTION"

                servant_result = await self.orchestrator.execute_elder_servants(
                    {
                        "task_name": task_name,
                        "sage_recommendations": sage_council_result.get(
                            "recommendations", []
                        ),
                        "flow_id": flow_id,
                        "soul_mode": soul_mode,
                        "claude_elder_soul": flow_data["claude_elder_soul_active"],
                    }
                )

                flow_data["results"]["servant_execution"] = servant_result

                # Phase 3: 品質ゲート（Claude Elder魂統合）
                if flow_data["claude_elder_soul_active"]:
                    logger.info("👑 Phase 3: Claude Elder魂統合品質ゲート開始")
                    flow_data["phase"] = "CLAUDE_ELDER_QUALITY_GATE"
                else:
                    logger.info("🔍 Phase 3: 品質ゲート開始")
                    flow_data["phase"] = "QUALITY_GATE"

                quality_gate_result = await self.orchestrator.execute_quality_gate(
                    {
                        "task_name": task_name,
                        "implementation_results": servant_result,
                        "flow_id": flow_id,
                        "soul_mode": soul_mode,
                        "claude_elder_soul": flow_data["claude_elder_soul_active"],
                    }
                )

                flow_data["results"]["quality_gate"] = quality_gate_result

                # Phase 4: 評議会報告（Claude Elder魂統合）
                if flow_data["claude_elder_soul_active"]:
                    logger.info("👑 Phase 4: Claude Elder魂統合評議会報告開始")
                    flow_data["phase"] = "CLAUDE_ELDER_COUNCIL_REPORT"
                else:
                    logger.info("📊 Phase 4: 評議会報告開始")
                    flow_data["phase"] = "COUNCIL_REPORT"

                council_report_result = await self.orchestrator.execute_council_report(
                    {
                        "task_name": task_name,
                        "all_results": flow_data["results"],
                        "flow_id": flow_id,
                        "soul_mode": soul_mode,
                        "claude_elder_soul": flow_data["claude_elder_soul_active"],
                    }
                )

                flow_data["results"]["council_report"] = council_report_result

                # Phase 5: Git自動化（Claude Elder魂統合）
                if flow_data["claude_elder_soul_active"]:
                    logger.info("👑 Phase 5: Claude Elder魂統合Git自動化開始")
                    flow_data["phase"] = "CLAUDE_ELDER_GIT_AUTOMATION"
                else:
                    logger.info("📤 Phase 5: Git自動化開始")
                    flow_data["phase"] = "GIT_AUTOMATION"

                git_automation_result = await self.orchestrator.execute_git_automation(
                    {
                        "task_name": task_name,
                        "implementation_results": servant_result,
                        "flow_id": flow_id,
                        "soul_mode": soul_mode,
                        "claude_elder_soul": flow_data["claude_elder_soul_active"],
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
                    "soul_mode": soul_mode,
                    "claude_elder_soul_active": flow_data["claude_elder_soul_active"],
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
                "soul_mode": soul_mode,
                "claude_elder_soul_active": flow_data.get(
                    "claude_elder_soul_active", False
                ),
                "error": str(e),
            }

    async def get_status(self) -> Dict[str, Any]:
        """エンジンステータス取得（アクティブタスク情報付き）"""
        active_tasks = self.pid_lock_manager.get_active_tasks()

        return {
            "status": "RUNNING",
            "active_flows": len(self.active_flows),
            "active_flows_list": list(self.active_flows.keys()),
            "workflows": len(self.workflows),
            "locked_tasks": len(active_tasks),
            "locked_tasks_list": [
                {
                    "task_id": task_id,
                    "pid": info["pid"],
                    "started_at": info["started_at"],
                }
                for task_id, info in active_tasks.items()
            ],
            "component": "elder_flow_engine",
            "version": "1.1.0",  # PIDロック機能追加
            "features": [
                "sage_council",
                "servant_execution",
                "quality_gate",
                "council_report",
                "git_automation",
                "pid_lock_protection",  # 新機能
            ],
        }

    async def cleanup_stale_locks(self) -> Dict[str, Any]:
        """古いロックのクリーンアップ"""
        try:
            cleaned_count = self.pid_lock_manager.cleanup_stale_locks()
            logger.info(f"🧹 {cleaned_count}個の古いロックをクリーンアップしました")

            return {
                "status": "success",
                "cleaned_locks": cleaned_count,
                "message": f"Successfully cleaned {cleaned_count} stale locks",
            }
        except Exception as e:
            logger.error(f"ロッククリーンアップエラー: {e}")
            return {"status": "error", "error": str(e)}

    async def get_active_tasks(self) -> Dict[str, Any]:
        """現在アクティブなタスクのリストを取得"""
        try:
            active_tasks = self.pid_lock_manager.get_active_tasks()

            return {
                "status": "success",
                "active_tasks_count": len(active_tasks),
                "active_tasks": [
                    {
                        "task_id": task_id,
                        "pid": info["pid"],
                        "started_at": info["started_at"],
                        "task_info": info.get("task_info", {}),
                    }
                    for task_id, info in active_tasks.items()
                ],
            }
        except Exception as e:
            logger.error(f"アクティブタスク取得エラー: {e}")
            return {"status": "error", "error": str(e)}

    async def manage_workflow(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """ワークフロー管理"""
        action = request.get("action", "")

        if action == "create":
            workflow_name = request.get("workflow_name", "")
            tasks = request.get("tasks", [])
            workflow_id = str(uuid.uuid4())

            self.workflows[workflow_id] = {
                "workflow_id": workflow_id,
                "workflow_name": workflow_name,
                "tasks": tasks,
                "created_at": datetime.now().isoformat(),
                "status": "CREATED",
            }

            logger.info(f"🔄 ワークフロー作成: {workflow_name} (ID: {workflow_id})")

            # 即座に実行するオプション
            if request.get("execute", False):
                return await self.execute_workflow(workflow_id)

            return {
                "workflow_id": workflow_id,
                "workflow_name": workflow_name,
                "status": "CREATED",
                "tasks_count": len(tasks),
            }

        elif action == "list":
            return {"workflows": list(self.workflows.values())}

        elif action == "execute":
            workflow_id = request.get("workflow_id", "")
            return await self.execute_workflow(workflow_id)

        else:
            return {"error": f"未知のワークフローアクション: {action}"}

    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """ワークフロー実行"""
        if workflow_id not in self.workflows:
            return {"error": f"ワークフローが見つかりません: {workflow_id}"}

        workflow = self.workflows[workflow_id]
        workflow["status"] = "RUNNING"
        workflow["start_time"] = datetime.now().isoformat()

        logger.info(
            f"🔄 ワークフロー実行開始: {workflow['workflow_name']} (ID: {workflow_id})"
        )

        results = []
        for task in workflow["tasks"]:
            # PIDロックチェック
            lock_info = self.pid_lock_manager.is_task_locked(task["task_name"])
            if lock_info:
                logger.warning(
                    f"⏭️ タスク '{task['task_name']}' はスキップ（既に実行中）"
                )
                results.append(
                    {
                        "task_name": task["task_name"],
                        "status": "SKIPPED",
                        "reason": "Already running",
                        "running_pid": lock_info["pid"],
                    }
                )
                continue

            result = await self.execute_elder_flow(
                {
                    "task_name": task["task_name"],
                    "priority": task.get("priority", "medium"),
                }
            )
            results.append(result)

        workflow["status"] = "COMPLETED"
        workflow["end_time"] = datetime.now().isoformat()
        workflow["results"] = results

        logger.info(
            f"✅ ワークフロー実行完了: {workflow['workflow_name']} (ID: {workflow_id})"
        )

        return {
            "workflow_id": workflow_id,
            "workflow_name": workflow["workflow_name"],
            "status": "COMPLETED",
            "results": results,
        }

    def validate_request(self, request: Dict[str, Any]) -> bool:
        """リクエスト検証"""
        request_type = request.get("type", "execute")

        if request_type == "execute":
            return "task_name" in request
        elif request_type == "workflow":
            action = request.get("action", "")
            if action == "create":
                return "workflow_name" in request and "tasks" in request
            elif action == "execute":
                return "workflow_id" in request
            return action in ["list"]

        return request_type in ["status", "cleanup_locks", "active_tasks"]

    def get_capabilities(self) -> Dict[str, Any]:
        """エンジン機能情報"""
        return {
            "name": "Elder Flow Engine with PID Lock & Claude Elder Soul Integration",
            "version": "1.2.0",
            "capabilities": [
                "sage_council_execution",
                "servant_orchestration",
                "quality_gate_validation",
                "council_reporting",
                "git_automation",
                "workflow_management",
                "pid_lock_protection",
                "multiprocess_safety",
                "stale_lock_cleanup",
                "active_task_monitoring",
                "claude_elder_soul_integration",
                "default_soul_activation",
            ],
            "soul_integration": {
                "default_mode": "claude_elder_default",
                "description": "Claude Elder's soul is activated by default when no soul mode is specified",
                "phases_enhanced": [
                    "CLAUDE_ELDER_SAGE_COUNCIL",
                    "CLAUDE_ELDER_SERVANT_EXECUTION",
                    "CLAUDE_ELDER_QUALITY_GATE",
                    "CLAUDE_ELDER_COUNCIL_REPORT",
                    "CLAUDE_ELDER_GIT_AUTOMATION",
                ],
            },
            "supported_requests": [
                "execute",
                "status",
                "workflow",
                "cleanup_locks",
                "active_tasks",
            ],
        }


# CLI実行用
async def main():
    """mainメソッド"""
    engine = ElderFlowEngine()

    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            result = await engine.get_status()
        elif sys.argv[1] == "cleanup":
            result = await engine.cleanup_stale_locks()
        elif sys.argv[1] == "active":
            result = await engine.get_active_tasks()
        elif sys.argv[1] == "execute" and len(sys.argv) > 2:
            result = await engine.execute_elder_flow(
                {"task_name": " ".join(sys.argv[2:]), "priority": "medium"}
            )
        else:
            result = {
                "error": "使用法: elder_flow_engine.py [status|cleanup|active|execute <task_name>]"
            }
    else:
        result = {
            "error": "コマンドを指定してください: status, cleanup, active, execute <task_name>"
        }

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
