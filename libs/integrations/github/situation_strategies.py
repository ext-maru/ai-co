#!/usr/bin/env python3
"""
🎯 Situation-Specific Strategies
状況別対応戦略システム

機能:
- mergeable_state別の対応戦略
- 自動ブランチ更新
- CI待機戦略
- レビュー対応
- 安全なコンフリクト解決
"""

import asyncio
import logging
import subprocess
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import os
import tempfile

logger = logging.getLogger(__name__)


class StrategyResult(Enum):
    """戦略実行結果"""
    SUCCESS = "success"
    FAILED = "failed"
    MANUAL_REQUIRED = "manual_required"
    RETRY_LATER = "retry_later"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class StrategyContext:
    """戦略実行コンテキスト"""
    pr_number: int
    pr_title: str
    branch_name: str
    base_branch: str
    mergeable_state: str
    mergeable: Optional[bool]
    draft: bool
    ci_status: Optional[str]
    review_state: Optional[str]
    additional_data: Dict[str, Any] = None
    
    def __post_init__(self):
        """__post_init__特殊メソッド"""
        if self.additional_data is None:
            self.additional_data = {}


@dataclass
class StrategyResponse:
    """戦略実行結果"""
    result: StrategyResult
    message: str
    actions_taken: List[str]
    retry_after: Optional[int] = None  # 秒
    error_details: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "result": self.result.value,
            "message": self.message,
            "actions_taken": self.actions_taken,
            "retry_after": self.retry_after,
            "error_details": self.error_details
        }


class SituationStrategyEngine:
    """状況別戦略エンジン"""
    
    def __init__(self, pr_api_client, git_repo_path: Optional[str] = None):
        """
        初期化
        
        Args:
            pr_api_client: PR操作用のAPIクライアント
            git_repo_path: Gitリポジトリのパス
        """
        self.pr_api_client = pr_api_client
        self.git_repo_path = git_repo_path or os.getcwd()
        
        # 戦略マッピング
        self.strategies = {
            "unstable": self._handle_unstable_state,
            "behind": self._handle_behind_state,
            "blocked": self._handle_blocked_state,
            "dirty": self._handle_dirty_state,
            "unknown": self._handle_unknown_state,
            "clean": self._handle_clean_state
        }
    
    async def execute_strategy(self, context: StrategyContext) -> StrategyResponse:
        """
        状況に応じた戦略を実行
        
        Args:
            context: 戦略実行コンテキスト
            
        Returns:
            StrategyResponse: 実行結果
        """
        mergeable_state = context.mergeable_state.lower()
        
        if mergeable_state not in self.strategies:
            return StrategyResponse(
                result=StrategyResult.NOT_APPLICABLE,
                message=f"Unknown mergeable state: {mergeable_state}",
                actions_taken=[]
            )
        
        logger.info(f"Executing strategy for PR #{context.pr_number} - State: {mergeable_state}")
        
        try:
            return await self.strategies[mergeable_state](context)
        except Exception as e:
            logger.error(f"Strategy execution error for PR #{context.pr_number}: {e}")
            return StrategyResponse(
                result=StrategyResult.FAILED,
                message=f"Strategy execution failed: {str(e)}",
                actions_taken=[],
                error_details=str(e)
            )
    
    async def _handle_unstable_state(self, context: StrategyContext) -> StrategyResponse:
        """CI実行中・失敗状態への対応"""
        actions = []
        
        # CI状況の詳細分析
        ci_info = await self._analyze_ci_status(context.pr_number)
        actions.append(f"CI状況分析完了: {ci_info.get('summary', 'Unknown')}")
        
        if ci_info.get("status") == "pending":
            # CI実行中 - 待機戦略
            return StrategyResponse(
                result=StrategyResult.RETRY_LATER,
                message="CI実行中です。完了まで待機します。",
                actions_taken=actions,
                retry_after=60  # 1分後に再試行
            )
        
        elif ci_info.get("status") == "failure":
            # CI失敗 - 失敗原因を分析
            failure_analysis = await self._analyze_ci_failures(context.pr_number, ci_info)
            actions.append(f"CI失敗分析: {failure_analysis.get('summary', 'Analysis failed')}")
            
            if failure_analysis.get("auto_fixable", False):
                # 自動修正可能
                fix_result = await self._attempt_auto_fix(context, failure_analysis)
                actions.extend(fix_result.get("actions", []))
                
                if fix_result.get("success", False):
                    return StrategyResponse(
                        result=StrategyResult.SUCCESS,
                        message="CI失敗を自動修正しました。再実行を待機中です。",
                        actions_taken=actions,
                        retry_after=120  # 2分後に状態確認
                    )
                else:
                    return StrategyResponse(
                        result=StrategyResult.MANUAL_REQUIRED,
                        message=f"自動修正に失敗しました: {fix_result.get('error', 'Unknown error')}",
                        actions_taken=actions
                    )
            else:
                # 手動対応が必要
                return StrategyResponse(
                    result=StrategyResult.MANUAL_REQUIRED,
                    message="CI失敗は手動対応が必要です。",
                    actions_taken=actions,
                    error_details=failure_analysis.get("details", "")
                )
        
        else:
            # その他の状況
            return StrategyResponse(
                result=StrategyResult.RETRY_LATER,
                message="CI状況を監視中です。",
                actions_taken=actions,
                retry_after=90
            )
    
    async def _handle_behind_state(self, context: StrategyContext) -> StrategyResponse:
        """ベースブランチ遅れ状態への対応"""
        actions = []
        
        # ベースブランチとの差分を分析
        diff_analysis = await self._analyze_branch_diff(context)
        actions.append(f"ブランチ差分分析: {diff_analysis.get('summary', 'Unknown')}")
        
        if diff_analysis.get("fast_forward_possible", False):
            # ファストフォワード可能 - 自動更新
            update_result = await self._update_branch_fast_forward(context)
            actions.extend(update_result.get("actions", []))
            
            if update_result.get("success", False):
                return StrategyResponse(
                    result=StrategyResult.SUCCESS,
                    message="ブランチを自動更新しました。",
                    actions_taken=actions,
                    retry_after=30  # 30秒後に状態確認
                )
            else:
                return StrategyResponse(
                    result=StrategyResult.FAILED,
                    message=f"ブランチ更新に失敗: {update_result.get('error', 'Unknown error')}",
                    actions_taken=actions
                )
        
        elif diff_analysis.get("merge_possible", False):
            # マージ可能だがコンフリクトリスクあり
            if diff_analysis.get("conflict_risk", "high") == "low":
                # 低リスク - 自動マージ更新
                merge_result = await self._update_branch_merge(context)
                actions.extend(merge_result.get("actions", []))
                
                if merge_result.get("success", False):
                    return StrategyResponse(
                        result=StrategyResult.SUCCESS,
                        message="ブランチをマージ更新しました。",
                        actions_taken=actions,
                        retry_after=30
                    )
                else:
                    return StrategyResponse(
                        result=StrategyResult.MANUAL_REQUIRED,
                        message="ブランチ更新でコンフリクトが発生しました。",
                        actions_taken=actions
                    )
            else:
                # 高リスク - 手動対応推奨
                return StrategyResponse(
                    result=StrategyResult.MANUAL_REQUIRED,
                    message="ブランチ更新はコンフリクトリスクが高いため手動対応が必要です。",
                    actions_taken=actions
                )
        
        else:
            # 複雑な状況 - 手動対応
            return StrategyResponse(
                result=StrategyResult.MANUAL_REQUIRED,
                message="ブランチ状況が複雑なため手動対応が必要です。",
                actions_taken=actions
            )
    
    async def _handle_blocked_state(self, context: StrategyContext) -> StrategyResponse:
        """ブロック状態への対応"""
        actions = []
        
        # ブロック原因を分析
        block_analysis = await self._analyze_block_reasons(context.pr_number)
        actions.append(f"ブロック原因分析: {block_analysis.get('summary', 'Unknown')}")
        
        block_reasons = block_analysis.get("reasons", [])
        
        if "missing_reviews" in block_reasons:
            # レビュー不足
            review_result = await self._handle_missing_reviews(context)
            actions.extend(review_result.get("actions", []))
            
            return StrategyResponse(
                result=StrategyResult.RETRY_LATER,
                message="レビュー待ちです。レビュアーに通知しました。",
                actions_taken=actions,
                retry_after=300  # 5分後に再確認
            )
        
        elif "failing_checks" in block_reasons:
            # 必須チェック失敗
            return StrategyResponse(
                result=StrategyResult.MANUAL_REQUIRED,
                message="必須チェックが失敗しています。修正が必要です。",
                actions_taken=actions
            )
        
        elif "branch_protection" in block_reasons:
            # ブランチプロテクション
            protection_details = block_analysis.get("protection_details", {})
            
            if protection_details.get("admin_override_possible", False):
                return StrategyResponse(
                    result=StrategyResult.MANUAL_REQUIRED,
                    message="ブランチプロテクションにより管理者権限が必要です。",
                    actions_taken=actions
                )
            else:
                return StrategyResponse(
                    result=StrategyResult.RETRY_LATER,
                    message="ブランチプロテクション条件の満たしを待機中です。",
                    actions_taken=actions,
                    retry_after=180  # 3分後に再確認
                )
        
        else:
            return StrategyResponse(
                result=StrategyResult.MANUAL_REQUIRED,
                message="不明なブロック原因のため手動対応が必要です。",
                actions_taken=actions
            )
    
    async def _handle_dirty_state(self, context: StrategyContext) -> StrategyResponse:
        """コンフリクト状態への対応"""
        actions = []
        
        # コンフリクトを分析
        conflict_analysis = await self._analyze_conflicts(context)
        actions.append(f"コンフリクト分析: {conflict_analysis.get('summary', 'Unknown')}")
        
        conflict_types = conflict_analysis.get("types", [])
        auto_resolvable = conflict_analysis.get("auto_resolvable", [])
        
        if auto_resolvable:
            # 自動解決可能なコンフリクトがある
            resolution_result = await self._resolve_safe_conflicts(context, auto_resolvable)
            actions.extend(resolution_result.get("actions", []))
            
            if resolution_result.get("success", False):
                return StrategyResponse(
                    result=StrategyResult.SUCCESS,
                    message="安全なコンフリクトを自動解決しました。",
                    actions_taken=actions,
                    retry_after=30  # 30秒後に状態確認
                )
            else:
                return StrategyResponse(
                    result=StrategyResult.MANUAL_REQUIRED,
                    message=f"コンフリクト解決に失敗: {resolution_result.get('error', 'Unknown error')}",
                    actions_taken=actions
                )
        
        else:
            # 手動対応が必要
            conflict_guide = self._generate_conflict_resolution_guide(conflict_analysis)
            
            return StrategyResponse(
                result=StrategyResult.MANUAL_REQUIRED,
                message="コンフリクトは手動解決が必要です。",
                actions_taken=actions + [f"解決ガイド生成: {len(conflict_guide)} steps"]
            )
    
    async def _handle_unknown_state(self, context: StrategyContext) -> StrategyResponse:
        """不明状態への対応"""
        actions = []
        
        # 状態を再確認
        refresh_result = await self._refresh_pr_state(context.pr_number)
        actions.append("PR状態を再取得")
        
        if refresh_result.get("success", False):
            new_state = refresh_result.get("mergeable_state", "unknown")
            
            if new_state != "unknown":
                # 状態が判明した場合は再実行
                context.mergeable_state = new_state
                return await self.execute_strategy(context)
            else:
                # まだ不明
                return StrategyResponse(
                    result=StrategyResult.RETRY_LATER,
                    message="GitHubがPR状態を計算中です。しばらく待機します。",
                    actions_taken=actions,
                    retry_after=120  # 2分後に再試行
                )
        else:
            return StrategyResponse(
                result=StrategyResult.FAILED,
                message="PR状態の取得に失敗しました。",
                actions_taken=actions
            )
    
    async def _handle_clean_state(self, context: StrategyContext) -> StrategyResponse:
        """マージ可能状態への対応"""
        actions = []
        
        # 最終チェック
        final_checks = await self._perform_final_merge_checks(context)
        actions.extend(final_checks.get("actions", []))
        
        if final_checks.get("ready_to_merge", False):
            # マージ実行
            merge_result = await self._execute_merge(context.pr_number)
            actions.extend(merge_result.get("actions", []))
            
            if merge_result.get("success", False):
                return StrategyResponse(
                    result=StrategyResult.SUCCESS,
                    message="マージが正常に完了しました。",
                    actions_taken=actions
                )
            else:
                return StrategyResponse(
                    result=StrategyResult.FAILED,
                    message=f"マージに失敗: {merge_result.get('error', 'Unknown error')}",
                    actions_taken=actions
                )
        else:
            return StrategyResponse(
                result=StrategyResult.MANUAL_REQUIRED,
                message="最終チェックで問題が検出されました。",
                actions_taken=actions,
                error_details=final_checks.get("issues", "")
            )
    
    # ヘルパーメソッド（実装は簡略化）
    
    async def _analyze_ci_status(self, pr_number: int) -> Dict[str, Any]:
        """CI状況の分析"""
        return {"status": "pending", "summary": "CI analysis placeholder"}
    
    async def _analyze_ci_failures(self, pr_number: int, ci_info: Dict[str, Any]) -> Dict[str, Any]:
        """CI失敗の分析"""
        return {"auto_fixable": False, "summary": "CI failure analysis placeholder"}
    
    async def _attempt_auto_fix(
        self,
        context: StrategyContext,
        failure_analysis: Dict[str,
        Any]
    ) -> Dict[str, Any]:
        """自動修正の試行"""
        return {"success": False, "actions": ["Auto-fix placeholder"], "error": "Not implemented"}
    
    async def _analyze_branch_diff(self, context: StrategyContext) -> Dict[str, Any]:
        """ブランチ差分の分析"""
        return {
            "fast_forward_possible": True,
            "merge_possible": True,
            "conflict_risk": "low",
            "summary": "Branch diff analysis placeholder"
        }
    
    async def _update_branch_fast_forward(self, context: StrategyContext) -> Dict[str, Any]:
        """ファストフォワード更新"""
        return {"success": True, "actions": ["Fast-forward update placeholder"]}
    
    async def _update_branch_merge(self, context: StrategyContext) -> Dict[str, Any]:
        """マージ更新"""
        return {"success": True, "actions": ["Merge update placeholder"]}
    
    async def _analyze_block_reasons(self, pr_number: int) -> Dict[str, Any]:
        """ブロック原因の分析"""
        return {
            "reasons": ["missing_reviews"],
            "summary": "Block analysis placeholder"
        }
    
    async def _handle_missing_reviews(self, context: StrategyContext) -> Dict[str, Any]:
        """レビュー不足への対応"""
        return {"actions": ["Review request placeholder"]}
    
    async def _analyze_conflicts(self, context: StrategyContext) -> Dict[str, Any]:
        """コンフリクトの分析"""
        return {
            "types": ["merge_conflict"],
            "auto_resolvable": [],
            "summary": "Conflict analysis placeholder"
        }
    
    async def _resolve_safe_conflicts(
        self,
        context: StrategyContext,
        auto_resolvable: List[str]
    ) -> Dict[str, Any]:
        """安全なコンフリクトの解決"""
        return {"success": False, "actions": ["Conflict resolution placeholder"]}
    
    def _generate_conflict_resolution_guide(self, conflict_analysis: Dict[str, Any]) -> List[str]:
        """コンフリクト解決ガイドの生成"""
        return ["Manual conflict resolution guide placeholder"]
    
    async def _refresh_pr_state(self, pr_number: int) -> Dict[str, Any]:
        """PR状態の再取得"""
        return {"success": True, "mergeable_state": "clean"}
    
    async def _perform_final_merge_checks(self, context: StrategyContext) -> Dict[str, Any]:
        """最終マージチェック"""
        return {"ready_to_merge": True, "actions": ["Final checks placeholder"]}
    
    async def _execute_merge(self, pr_number: int) -> Dict[str, Any]:
        """マージの実行"""
        try:
            result = self.pr_api_client._enable_auto_merge(pr_number)
            return {
                "success": result.get("success", False),
                "actions": ["Merge execution"],
                "error": result.get("error")
            }
        except Exception as e:
            return {"success": False, "actions": ["Merge attempt"], "error": str(e)}