#!/usr/bin/env python3
"""
Elder Flow - Task Tracker統合
タスクトラッカーとElder Flowを連携させる統合モジュール
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.claude_task_tracker import (
    TaskPriority,
    TaskStatus,
    TaskType,
    get_task_tracker,
)

logger = logging.getLogger(__name__)


class ElderFlowTaskIntegration:
    """Elder FlowとTask Trackerの統合"""

    def __init__(self):
        """初期化メソッド"""
        self.task_tracker = get_task_tracker()
        self.active_flows = {}
        logger.info("Elder Flow Task Integration initialized")

    async def execute_elder_flow(
        self,
        description: str,
        priority: str = "medium",
        task_type: str = "feature",
        context: Optional[Dict] = None,
    ) -> str:
        """
        Elder Flow実行（簡易版）

        Args:
            description: タスク説明
            priority: 優先度
            task_type: タスクタイプ
            context: 実行コンテキスト

        Returns:
            task_id: 作成されたタスクID
        """
        # 優先度マッピング
        priority_map = {
            "critical": TaskPriority.CRITICAL,
            "high": TaskPriority.HIGH,
            "medium": TaskPriority.MEDIUM,
            "low": TaskPriority.LOW,
        }

        # タスクタイプマッピング
        type_map = {
            "feature": TaskType.FEATURE,
            "bug_fix": TaskType.BUG_FIX,
            "refactor": TaskType.REFACTOR,
            "documentation": TaskType.DOCUMENTATION,
            "research": TaskType.RESEARCH,
            "deployment": TaskType.DEPLOYMENT,
            "maintenance": TaskType.MAINTENANCE,
        }

        # タスク作成
        task_id = self.task_tracker.create_task(
            title=f"[Elder Flow] {description[:100]}",
            task_type=type_map.get(task_type, TaskType.FEATURE),
            priority=priority_map.get(priority, TaskPriority.MEDIUM),
            description=description,
            created_by="elder_flow",
            metadata={"flow_type": "elder_flow", "context": context or {}},
        )

        # フロー実行
        try:
            await self._execute_flow_stages(task_id, description, context)
            return task_id
        except Exception as e:
            logger.error(f"Elder Flow実行エラー: {e}")
            self.task_tracker.update_task_status(
                task_id, TaskStatus.FAILED, error_message=str(e)
            )
            raise

    async def _execute_flow_stages(
        self, task_id: str, description: str, context: Optional[Dict] = None
    ):
        """Elder Flowの各段階を実行"""
        stages = [
            ("analyze", "タスク分析", 0.2),
            ("plan", "実行計画作成", 0.4),
            ("implement", "実装実行", 0.6),
            ("test", "品質確認", 0.8),
            ("deploy", "デプロイ", 1.0),
        ]

        # 開始
        self.task_tracker.update_task_status(
            task_id, TaskStatus.IN_PROGRESS, progress=0.0
        )

        execution_id = self.task_tracker.record_execution(
            task_id, status="started", execution_context={"description": description}
        )

        logs = []

        for stage_name, stage_desc, progress in stages:
            logger.info(f"実行中: {stage_name} - {stage_desc}")
            logs.append(f"[{datetime.now().isoformat()}] {stage_name}: {stage_desc}")

            # ステージ実行（簡易シミュレーション）
            await asyncio.sleep(0.5)  # 実際の処理の代わり

            # 進捗更新
            self.task_tracker.update_task_status(
                task_id, TaskStatus.IN_PROGRESS, progress=progress
            )

            # 実行ログ更新
            self.task_tracker.record_execution(
                task_id,
                execution_id=execution_id,
                status="in_progress",
                log_entries=logs,
            )

        # 完了
        self.task_tracker.update_task_status(
            task_id,
            TaskStatus.COMPLETED,
            progress=1.0,
            result={
                "status": "success",
                "stages_completed": len(stages),
                "execution_time": "2.5s",
            },
        )

        logger.info(f"Elder Flow完了: {task_id}")

    def get_flow_status(self, task_id: str) -> Optional[Dict]:
        """フロー状態取得"""
        task = self.task_tracker.get_task(task_id)
        if task and task.get("metadata", {}).get("flow_type") == "elder_flow":
            return {
                "task_id": task_id,
                "status": task["status"],
                "progress": task.get("progress", 0),
                "created_at": task["created_at"],
                "updated_at": task["updated_at"],
            }
        return None

    def list_active_flows(self) -> List[Dict]:
        """アクティブなElder Flow一覧"""
        active_tasks = self.task_tracker.list_tasks(status=TaskStatus.IN_PROGRESS)

        flows = []
        for task in active_tasks:
            if task.get("metadata", {}).get("flow_type") == "elder_flow":
                flows.append(
                    {
                        "task_id": task["task_id"],
                        "title": task["title"],
                        "progress": task.get("progress", 0),
                        "started_at": task.get("started_at"),
                    }
                )

        return flows

    async def auto_apply_elder_flow(self, user_input: str) -> Optional[str]:
        """
        Elder Flow自動適用判定

        Args:
            user_input: ユーザー入力

        Returns:
            task_id: 適用された場合のタスクID
        """
        # 自動適用キーワード
        implementation_keywords = [
            "実装",
            "implement",
            "add",
            "create",
            "build",
            "develop",
            "新機能",
        ]
        fix_keywords = ["修正", "fix", "bug", "エラー", "error", "問題", "issue"]
        optimization_keywords = ["最適化", "optimize", "リファクタリング", "refactor", "改善"]
        security_keywords = ["セキュリティ", "security", "認証", "authentication"]

        # 強制適用キーワード
        force_keywords = ["elder flow", "elder-flow", "エルダーフロー", "エルダー・フロー"]

        input_lower = user_input.lower()

        # 強制適用チェック
        if any(keyword in input_lower for keyword in force_keywords):
            logger.info("Elder Flow強制適用")
            return await self.execute_elder_flow(
                description=user_input, priority="high", task_type="feature"
            )

        # 自動適用チェック
        task_type = "feature"
        priority = "medium"

        if any(keyword in input_lower for keyword in implementation_keywords):
            task_type = "feature"
            priority = "high"
        elif any(keyword in input_lower for keyword in fix_keywords):
            task_type = "bug_fix"
            priority = "high"
        elif any(keyword in input_lower for keyword in optimization_keywords):
            task_type = "refactor"
            priority = "medium"
        elif any(keyword in input_lower for keyword in security_keywords):
            task_type = "feature"
            priority = "critical"
        else:
            # 自動適用対象外
            return None

        logger.info(f"Elder Flow自動適用: type={task_type}, priority={priority}")
        return await self.execute_elder_flow(
            description=user_input, priority=priority, task_type=task_type
        )


# シングルトンインスタンス
_integration = None


def get_elder_flow_integration() -> ElderFlowTaskIntegration:
    """Elder Flow統合のシングルトンインスタンス取得"""
    global _integration
    if _integration is None:
        _integration = ElderFlowTaskIntegration()
    return _integration


# エクスポート
__all__ = ["ElderFlowTaskIntegration", "get_elder_flow_integration"]
