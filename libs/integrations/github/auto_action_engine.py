#!/usr/bin/env python3
"""
🎯 Auto Action Engine
状態変化に応じた自動アクション実行システム

機能:
- 状態変化イベントに対する自動アクション
- マージ試行の自動化
- コンフリクト解決の自動化
- アクション履歴管理
- クールダウン制御
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from .pr_state_monitor import StateChangeEvent

logger = logging.getLogger(__name__)


@dataclass
class ActionRecord:
    """アクション実行記録"""
    pr_number: int
    timestamp: datetime
    event_type: StateChangeEvent
    action_type: str
    success: bool
    result: Dict[str, Any]
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "pr_number": self.pr_number,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value if isinstance(self.event_type, StateChangeEvent) else str(self.event_type),
            "action_type": self.action_type,
            "success": self.success,
            "result": self.result,
            "error": self.error
        }


class ActionType(Enum):
    """アクションタイプ"""
    MERGE_ATTEMPT = "merge_attempt"
    CHECK_READINESS = "check_merge_readiness"
    CONFLICT_RESOLUTION = "conflict_resolution"
    AUTO_MERGE = "auto_merge"
    ANALYZE_BLOCK = "analyze_block_reason"
    RESTART_MERGE = "restart_merge_process"
    RETRY_CI = "retry_ci"
    UPDATE_BRANCH = "update_branch"


class AutoActionEngine:
    """自動アクションエンジン"""
    
    def __init__(self, pr_api_client, conflict_resolver=None):
        """
        初期化
        
        Args:
            pr_api_client: PR操作用のAPIクライアント
            conflict_resolver: コンフリクト解決システム（オプション）
        """
        self.pr_api_client = pr_api_client
        self.conflict_resolver = conflict_resolver
        self.action_history: List[ActionRecord] = []
        self.cooldown_periods: Dict[int, Dict[str, datetime]] = {}
        self.default_cooldown = timedelta(seconds=60)  # デフォルト1分のクールダウン
        
    async def handle_state_change(
        self, 
        pr_number: int, 
        event: StateChangeEvent, 
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        状態変化に応じたアクションを実行
        
        Args:
            pr_number: PR番号
            event: 状態変化イベント
            event_data: イベントデータ
            
        Returns:
            Dict[str, Any]: アクション実行結果
        """
        logger.info(f"Handling state change for PR #{pr_number}: {event.value}")
        
        # クールダウンチェック
        if self._is_in_cooldown(pr_number, event.value):
            cooldown_remaining = self._get_cooldown_remaining(pr_number, event.value)
            return {
                "action_taken": "skipped_cooldown",
                "reason": "Action is in cooldown period",
                "cooldown_remaining": cooldown_remaining.total_seconds()
            }
        
        result = {}
        
        try:
            # イベントタイプに応じたアクション実行
            if event == StateChangeEvent.CI_PASSED:
                result = await self._handle_ci_passed(pr_number, event_data)
            elif event == StateChangeEvent.REVIEW_APPROVED:
                result = await self._handle_review_approved(pr_number, event_data)
            elif event == StateChangeEvent.CONFLICTS_DETECTED:
                result = await self._handle_conflicts_detected(pr_number, event_data)
            elif event == StateChangeEvent.CONFLICTS_RESOLVED:
                result = await self._handle_conflicts_resolved(pr_number, event_data)
            elif event == StateChangeEvent.READY_TO_MERGE:
                result = await self._handle_ready_to_merge(pr_number, event_data)
            elif event == StateChangeEvent.MERGE_BLOCKED:
                result = await self._handle_merge_blocked(pr_number, event_data)
            elif event == StateChangeEvent.BRANCH_UPDATED:
                result = await self._handle_branch_updated(pr_number, event_data)
            else:
                result = {
                    "action_taken": "none",
                    "reason": f"No action defined for event: {event.value}"
                }
            
            # アクション成功
            self._record_action(pr_number, event, result.get("action_taken", "unknown"), True, result)
            self._set_cooldown(pr_number, event.value)
            
        except Exception as e:
            logger.error(f"Action failed for PR #{pr_number}: {e}")
            result = {
                "success": False,
                "error": str(e),
                "action_taken": "error"
            }
            self._record_action(pr_number, event, "error", False, result, str(e))
        
        return result
    
    async def _handle_ci_passed(self, pr_number: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """CI成功時の処理"""
        logger.info(f"CI passed for PR #{pr_number}, attempting merge")
        
        # PRの状態を確認
        pr_info = self.pr_api_client.get_pull_request(pr_number)
        if not pr_info["success"]:
            return {
                "action_taken": ActionType.MERGE_ATTEMPT.value,
                "success": False,
                "reason": "Failed to get PR info"
            }
        
        pr = pr_info["pull_request"]
        
        # マージ可能かチェック
        if pr.get("mergeable") and pr.get("mergeable_state") == "clean":
            # マージ試行
            merge_result = await self.pr_api_client.merge_pull_request(pr_number)
            return {
                "action_taken": ActionType.MERGE_ATTEMPT.value,
                "success": merge_result["success"],
                "merge_sha": merge_result.get("sha"),
                "message": merge_result.get("message")
            }
        else:
            return {
                "action_taken": ActionType.MERGE_ATTEMPT.value,
                "success": False,
                "reason": f"PR not mergeable: state={pr.get('mergeable_state')}"
            }
    
    async def _handle_review_approved(self, pr_number: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """レビュー承認時の処理"""
        logger.info(f"Review approved for PR #{pr_number}, checking merge readiness")
        
        # PRの状態を確認
        pr_info = self.pr_api_client.get_pull_request(pr_number)
        if not pr_info["success"]:
            return {
                "action_taken": ActionType.CHECK_READINESS.value,
                "success": False,
                "reason": "Failed to get PR info"
            }
        
        pr = pr_info["pull_request"]
        mergeable = pr.get("mergeable", False)
        mergeable_state = pr.get("mergeable_state", "unknown")
        
        result = {
            "action_taken": ActionType.CHECK_READINESS.value,
            "success": True,
            "mergeable": mergeable,
            "mergeable_state": mergeable_state,
            "ready_to_merge": mergeable and mergeable_state == "clean"
        }
        
        # 準備完了ならマージを試行
        if result["ready_to_merge"]:
            merge_result = await self.pr_api_client.merge_pull_request(pr_number)
            result["merge_attempted"] = True
            result["merge_success"] = merge_result["success"]
        
        return result
    
    async def _handle_conflicts_detected(self, pr_number: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """コンフリクト検出時の処理"""
        logger.info(f"Conflicts detected for PR #{pr_number}")
        
        if self.conflict_resolver:
            # コンフリクト解決を試行
            resolution_result = await self.conflict_resolver.resolve_conflicts(pr_number)
            return {
                "action_taken": ActionType.CONFLICT_RESOLUTION.value,
                "success": resolution_result["success"],
                "conflicts_resolved": resolution_result.get("conflicts_resolved", 0),
                "files_updated": resolution_result.get("files_updated", [])
            }
        else:
            return {
                "action_taken": ActionType.CONFLICT_RESOLUTION.value,
                "success": False,
                "reason": "No conflict resolver available"
            }
    
    async def _handle_conflicts_resolved(self, pr_number: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """コンフリクト解決時の処理"""
        logger.info(f"Conflicts resolved for PR #{pr_number}, restarting merge process")
        
        # マージプロセスを再開
        return await self._handle_ci_passed(pr_number, event_data)
    
    async def _handle_ready_to_merge(self, pr_number: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """マージ準備完了時の処理"""
        logger.info(f"PR #{pr_number} is ready to merge")
        
        # 自動マージを実行
        merge_result = await self.pr_api_client.merge_pull_request(pr_number)
        return {
            "action_taken": ActionType.AUTO_MERGE.value,
            "success": merge_result["success"],
            "merge_sha": merge_result.get("sha"),
            "message": merge_result.get("message")
        }
    
    async def _handle_merge_blocked(self, pr_number: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """マージブロック時の処理"""
        logger.info(f"Merge blocked for PR #{pr_number}")
        
        # ブロック理由を分析
        pr_info = self.pr_api_client.get_pull_request(pr_number)
        if not pr_info["success"]:
            return {
                "action_taken": ActionType.ANALYZE_BLOCK.value,
                "success": False,
                "reason": "Failed to get PR info"
            }
        
        pr = pr_info["pull_request"]
        mergeable_state = pr.get("mergeable_state", "unknown")
        
        block_reasons = []
        retry_available = True
        
        if mergeable_state == "blocked":
            block_reasons.append("required_status_checks")
        elif mergeable_state == "behind":
            block_reasons.append("branch_out_of_date")
        elif mergeable_state == "dirty":
            block_reasons.append("merge_conflicts")
        elif mergeable_state == "unknown":
            block_reasons.append("state_calculation_pending")
            retry_available = True
        
        return {
            "action_taken": ActionType.ANALYZE_BLOCK.value,
            "success": True,
            "block_reason": ", ".join(block_reasons) if block_reasons else "unknown",
            "mergeable_state": mergeable_state,
            "retry_available": retry_available
        }
    
    async def _handle_branch_updated(self, pr_number: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """ブランチ更新時の処理"""
        logger.info(f"Branch updated for PR #{pr_number}")
        
        # CI再実行などの処理をここに実装
        return {
            "action_taken": ActionType.UPDATE_BRANCH.value,
            "success": True,
            "behind_by": event_data.get("current_behind", 0),
            "ahead_by": event_data.get("current_ahead", 0)
        }
    
    def _is_in_cooldown(self, pr_number: int, event_type: str) -> bool:
        """クールダウン中かチェック"""
        if pr_number not in self.cooldown_periods:
            return False
        
        if event_type not in self.cooldown_periods[pr_number]:
            return False
        
        cooldown_end = self.cooldown_periods[pr_number][event_type]
        return datetime.now() < cooldown_end
    
    def _get_cooldown_remaining(self, pr_number: int, event_type: str) -> timedelta:
        """残りクールダウン時間を取得"""
        if pr_number not in self.cooldown_periods:
            return timedelta(0)
        
        if event_type not in self.cooldown_periods[pr_number]:
            return timedelta(0)
        
        cooldown_end = self.cooldown_periods[pr_number][event_type]
        remaining = cooldown_end - datetime.now()
        return remaining if remaining > timedelta(0) else timedelta(0)
    
    def _set_cooldown(self, pr_number: int, event_type: str):
        """クールダウンを設定"""
        if pr_number not in self.cooldown_periods:
            self.cooldown_periods[pr_number] = {}
        
        self.cooldown_periods[pr_number][event_type] = datetime.now() + self.default_cooldown
    
    def _record_action(
        self, 
        pr_number: int, 
        event: StateChangeEvent,
        action_type: str,
        success: bool,
        result: Dict[str, Any],
        error: Optional[str] = None
    ):
        """アクションを記録"""
        record = ActionRecord(
            pr_number=pr_number,
            timestamp=datetime.now(),
            event_type=event,
            action_type=action_type,
            success=success,
            result=result,
            error=error
        )
        self.action_history.append(record)
    
    def get_action_history(self, pr_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """アクション履歴を取得"""
        if pr_number is None:
            return [record.to_dict() for record in self.action_history]
        else:
            return [
                record.to_dict() 
                for record in self.action_history 
                if record.pr_number == pr_number
            ]
    
    def clear_cooldowns(self, pr_number: Optional[int] = None):
        """クールダウンをクリア"""
        if pr_number is None:
            self.cooldown_periods.clear()
        elif pr_number in self.cooldown_periods:
            del self.cooldown_periods[pr_number]