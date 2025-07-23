#!/usr/bin/env python3
"""
Enhanced Auto Issue Processor with comprehensive error handling
Issue #191対応: 包括的なエラーハンドリングと回復機能の実装
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from github import Github
from github.Issue import Issue

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.core.elders_legacy import EldersServiceLegacy
from libs.auto_issue_processor_error_handling import (
    AutoIssueProcessorErrorHandler,
    ErrorContext,
    ErrorType,
    RecoveryAction,
    with_error_recovery,
    CircuitBreakerOpenError
)
from libs.integrations.github.auto_issue_processor import (
    AutoIssueElderFlowEngine,
    ProcessingLimiter,
    ComplexityEvaluator,
    ComplexityScore
)
from libs.integrations.github.reopened_issue_tracker import ReopenedIssueTracker

# 4賢者システム
from libs.task_sage import TaskSage
from libs.incident_sage import IncidentSage
from libs.knowledge_sage import KnowledgeSage
from libs.rag_manager import RagManager

logger = logging.getLogger("EnhancedAutoIssueProcessor")


class EnhancedAutoIssueProcessor(EldersServiceLegacy):
    """
    Enhanced GitHub Issue Auto Processor with Error Handling and Recovery
    """

    def __init__(self):
        """初期化メソッド"""
        super().__init__("enhanced_auto_issue_processor")
        self.domain = "GITHUB"
        self.service_name = "EnhancedAutoIssueProcessor"

        # GitHub API初期化
        github_token = os.getenv("GITHUB_TOKEN")
        repo_owner = os.getenv("GITHUB_REPO_OWNER", "ext-maru")
        repo_name = os.getenv("GITHUB_REPO_NAME", "ai-co")

        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable not set")

        self.github = Github(github_token)
        self.repo = self.github.get_repo(f"{repo_owner}/{repo_name}")

        # コンポーネント初期化
        self.elder_flow = AutoIssueElderFlowEngine()
        self.task_sage = TaskSage()
        self.incident_sage = IncidentSage()
        self.knowledge_sage = KnowledgeSage()
        self.rag_sage = RagManager()

        self.limiter = ProcessingLimiter()
        self.evaluator = ComplexityEvaluator()
        self.reopened_tracker = ReopenedIssueTracker(self.repo)
        
        # エラーハンドラー初期化
        self.error_handler = AutoIssueProcessorErrorHandler()

        # 処理対象の優先度
        self.target_priorities = ["critical", "high", "medium", "low"]
        
        # 処理履歴ファイル
        self.processing_history_file = "logs/auto_issue_processing.json"
        
        # メトリクス収集
        self.metrics = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "retry_count": 0,
            "rollback_count": 0,
            "circuit_breaker_activations": 0
        }

    def validate_request(self, request: Dict[str, Any]) -> bool:
        """リクエストの妥当性を検証"""
        # 処理モードの検証
        if "mode" in request and request["mode"] not in ["scan", "process", "dry_run"]:
            return False

        # イシュー番号が指定されている場合の検証
        if "issue_number" in request:
            if not isinstance(request["issue_number"], int):
                return False

        return True

    def get_capabilities(self) -> Dict[str, Any]:
        """サービスの機能を返す"""
        return {
            "service": "EnhancedAutoIssueProcessor",
            "version": "2.0.0",
            "capabilities": [
                "GitHub issue scanning",
                "Complexity evaluation",
                "Automatic processing",
                "Elder Flow integration",
                "Comprehensive error handling",
                "Automatic recovery",
                "Circuit breaker protection",
                "Rollback mechanism",
                "Metrics tracking"
            ],
            "error_handling": {
                "retry_strategies": ["exponential_backoff", "jitter"],
                "recovery_actions": ["retry", "rollback", "skip", "abort"],
                "circuit_breaker": True,
                "resource_cleanup": True
            },
            "limits": {
                "max_issues_per_hour": ProcessingLimiter.MAX_ISSUES_PER_HOUR,
                "max_concurrent": ProcessingLimiter.MAX_CONCURRENT,
                "target_priorities": self.target_priorities,
            },
            "metrics": self.metrics
        }

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """イシュー自動処理のメインエントリーポイント（エラーハンドリング強化版）"""
        mode = request.get("mode", "scan")
        
        # サーキットブレーカーチェック
        circuit_breaker = self.error_handler.get_circuit_breaker("process_request")
        if not circuit_breaker.can_execute():
            self.metrics["circuit_breaker_activations"] += 1
            return {
                "status": "circuit_breaker_open",
                "message": "Service temporarily unavailable due to high error rate",
                "retry_after": circuit_breaker.recovery_timeout
            }

        try:
            if mode == "scan":
                return await self._scan_issues_with_recovery()
            elif mode == "process":
                return await self._process_issues_with_recovery()
            elif mode == "dry_run":
                return await self._dry_run_with_recovery(request)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown mode: {mode}"
                }
                
        except CircuitBreakerOpenError as e:
            self.metrics["circuit_breaker_activations"] += 1
            return {
                "status": "circuit_breaker_open",
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error in process_request: {str(e)}")
            self.metrics["failed"] += 1
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}"
            }

    async def _scan_issues_with_recovery(self) -> Dict[str, Any]:
        """イシュースキャン（エラーリカバリー付き）"""
        retry_count = 0
        max_retries = 3
        
        while retry_count <= max_retries:
            try:
                issues = await self.scan_processable_issues()
                return {
                    "status": "success",
                    "processable_issues": len(issues),
                    "issues": [
                        {
                            "number": issue.number,
                            "title": issue.title,
                            "priority": self._determine_priority(issue),
                            "complexity": (await self.evaluator.evaluate(issue)).score,
                        }
                        for issue in issues[:5]
                    ],
                }
            except Exception as e:
                recovery_result = await self.error_handler.handle_error(
                    error=e,
                    operation="scan_issues",
                    retry_count=retry_count
                )
                
                if recovery_result.success and recovery_result.action_taken == RecoveryAction.RETRY:
                    retry_count += 1
                    self.metrics["retry_count"] += 1
                    if recovery_result.retry_after:
                        await asyncio.sleep(recovery_result.retry_after)
                    continue
                else:
                    raise

        raise Exception(f"Failed to scan issues after {max_retries} retries")

    async def _process_issues_with_recovery(self) -> Dict[str, Any]:
        """イシュー処理（エラーリカバリー付き）"""
        if not await self.limiter.can_process():
            return {
                "status": "rate_limited",
                "message": "Processing limit reached. Please try again later.",
            }

        issues = await self.scan_processable_issues()
        if not issues:
            return {
                "status": "no_issues",
                "message": "No processable issues found.",
            }

        # 最初のイシューを処理
        issue = issues[0]
        
        try:
            result = await self._execute_auto_processing_with_recovery(issue)
            self.metrics["successful"] += 1
            self.metrics["total_processed"] += 1
            
            return {
                "status": "success",
                "processed_issue": {
                    "number": issue.number,
                    "title": issue.title,
                    "result": result,
                },
                "metrics": self.metrics
            }
            
        except Exception as e:
            self.metrics["failed"] += 1
            self.metrics["total_processed"] += 1
            
            return {
                "status": "error",
                "message": f"Failed to process issue #{issue.number}: {str(e)}",
                "metrics": self.metrics
            }

    async def _execute_auto_processing_with_recovery(self, issue: Issue) -> Dict[str, Any]:
        """自動処理実行（エラーハンドリング・回復機能付き）"""
        retry_count = 0
        max_retries = 3
        files_created = []
        branch_name = None
        
        while retry_count <= max_retries:
            try:
                # 既存のPRチェック
                existing_pr = await self._check_existing_pr_for_issue(issue.number)
                if existing_pr:
                    return await self._handle_existing_pr(issue, existing_pr)
                
                # 処理記録
                await self.limiter.record_processing(issue.number)
                
                # 複雑度評価
                complexity = await self.evaluator.evaluate(issue)
                
                # 4賢者に相談
                sage_advice = await self.consult_four_sages(issue)
                
                # Elder Flowリクエスト構築
                flow_request = {
                    "task_name": f"Auto-fix Issue #{issue.number}: {issue.title}",
                    "priority": self._determine_priority(issue),
                    "context": {
                        "issue_number": issue.number,
                        "issue_title": issue.title,
                        "issue_body": issue.body or "",
                        "labels": [label.name for label in issue.labels],
                        "sage_advice": sage_advice,
                    },
                }
                
                # Elder Flow実行
                result = await self.elder_flow.execute_flow(flow_request)
                
                # ブランチ名とファイルパスを保存（ロールバック用）
                if result.get("pr_result"):
                    branch_name = result["pr_result"].get("branch_name")
                if result.get("flow_result") and result["flow_result"].get("files_created"):
                    files_created = result["flow_result"]["files_created"]
                
                # 結果処理
                return await self._handle_processing_result(issue, result, complexity)
                
            except Exception as e:
                # エラーハンドリング
                recovery_result = await self.error_handler.handle_error(
                    error=e,
                    operation=f"execute_auto_processing_issue_{issue.number}",
                    issue_number=issue.number,
                    branch_name=branch_name,
                    files_created=files_created,
                    retry_count=retry_count
                )
                
                if recovery_result.success and recovery_result.action_taken == RecoveryAction.RETRY:
                    retry_count += 1
                    self.metrics["retry_count"] += 1
                    if recovery_result.retry_after:
                        logger.info(f"Retrying after {recovery_result.retry_after}s...")
                        await asyncio.sleep(recovery_result.retry_after)
                    continue
                elif recovery_result.action_taken == RecoveryAction.ROLLBACK:
                    self.metrics["rollback_count"] += 1
                    logger.info(f"Rolled back {len(recovery_result.cleaned_resources)} resources")
                    raise Exception(f"Processing failed and rolled back: {recovery_result.message}")
                else:
                    raise

        raise Exception(f"Failed to process issue #{issue.number} after {max_retries} retries")

    async def _handle_existing_pr(
        self,
        issue: Issue,
        existing_pr: Dict[str,
        Any]
    ) -> Dict[str, Any]:
        """既存PRの処理"""
        logger.info(f"PR already exists for issue #{issue.number}: PR #{existing_pr['number']}")
        
        # 再オープンされたIssueの場合の特別処理
        reopened_info = await self.reopened_tracker.check_if_reopened(issue.number)
        if reopened_info['is_reopened']:
            await self._handle_reopened_issue_with_pr(issue, existing_pr, reopened_info)
        
        return {
            "status": "already_exists",
            "message": f"PR #{existing_pr['number']} already exists for this issue",
            "pr_url": existing_pr['html_url'],
            "pr_number": existing_pr['number']
        }

    async def _handle_reopened_issue_with_pr(
        self,
        issue: Issue,
        existing_pr: Dict[str,
        Any],
        reopened_info: Dict[str,
        Any]
    ):
        """再オープンされたIssueの処理"""
        await self.reopened_tracker.record_reprocessing(issue.number, {
            "status": "pr_exists",
            "pr_number": existing_pr['number'],
            "action": "monitoring_for_quality_fix"
        })
        
        # コメント作成
        comment_text = self._create_reopened_issue_comment(existing_pr, reopened_info)
        issue.create_comment(comment_text)

    async def _handle_processing_result(
        self,
        issue: Issue,
        result: Dict[str,
        Any],
        complexity: ComplexityScore
    ) -> Dict[str, Any]:
        """処理結果のハンドリング"""
        if result.get("status") == "success":
            await self._handle_successful_processing(issue, result, complexity)
        elif result.get("status") == "partial_success":
            await self._handle_partial_success(issue, result)
        
        return result

    async def _handle_successful_processing(
        self,
        issue: Issue,
        result: Dict[str,
        Any],
        complexity: ComplexityScore
    ):
        """成功時の処理"""
        pr_url = result.get("pr_url")
        
        if pr_url:
            # 再オープンされたIssueの再処理の場合
            reopened_info = await self.reopened_tracker.check_if_reopened(issue.number)
            if reopened_info['is_reopened']:
                await self._handle_reopened_issue_success(issue, result, reopened_info)
            else:
                # 通常の成功コメント
                issue.create_comment(
                    f"🤖 Auto-processed by Elder Flow\n\n"
                    f"PR created: {pr_url}\n\n"
                    f"This issue was automatically processed based on its complexity "
                    f"({complexity.score:.2f}) and priority level."
                )

    async def _handle_reopened_issue_success(
        self,
        issue: Issue,
        result: Dict[str,
        Any],
        reopened_info: Dict[str,
        Any]
    ):
        """再オープンIssueの成功処理"""
        await self.reopened_tracker.record_reprocessing(issue.number, {
            "status": "reprocessed_successfully",
            "pr_url": result.get("pr_url"),
            "pr_number": result.get("pr_number"),
            "action": "new_pr_created"
        })
        
        issue.create_comment(
            f"🔄 **再処理完了**\n\n"
            f"再オープンされたIssueを再処理し、新しいPRを作成しました: {result.get('pr_url')}\n\n"
            f"- 再オープン回数: {reopened_info['reopen_count']}\n"
            f"- 品質基準を満たすよう実装されています\n\n"
            f"This issue was automatically reprocessed after being reopened."
        )

    async def _handle_partial_success(self, issue: Issue, result: Dict[str, Any]):
        """部分的成功の処理"""
        issue.create_comment(
            f"⚠️ **部分的成功**\n\n"
            f"Elder Flowは完了しましたが、PR作成に失敗しました。\n"
            f"エラー: {result.get('pr_error', '不明なエラー')}\n\n"
            f"手動での確認が必要です。"
        )

    def _create_reopened_issue_comment(
        self,
        existing_pr: Dict[str,
        Any],
        reopened_info: Dict[str,
        Any]
    ) -> str:
        """再オープンIssue用のコメント作成"""
        comment_text = f"🔄 **再オープン検知**\n\n"
        comment_text += f"このIssueは再オープンされましたが、既にPR #{existing_pr['number']} が存在します。\n\n"
        
        # 推定理由
        reopen_reason = "品質基準未達成"
        if existing_pr['state'] == 'closed' and not existing_pr.get('merged'):
            reopen_reason = "PRが却下されたため再実装が必要"
        
        comment_text += f"**推定される再オープン理由**: {reopen_reason}\n\n"
        comment_text += f"**詳細情報**:\n"
        comment_text += f"- 再オープン回数: {reopened_info['reopen_count']}\n"
        comment_text += f"- 再オープン日時: {reopened_info['reopened_at']}\n"
        comment_text += f"- 再オープン者: @{reopened_info['reopened_by']}\n\n"
        
        # 次のアクション
        comment_text += "**次のアクション**:\n"
        if reopened_info['reopen_count'] >= 3:
            comment_text += "- ⚠️ 複数回の再オープンが検出されました。人間レビューを推奨します\n"
            comment_text += "- 根本的な設計見直しが必要かもしれません\n"
        else:
            comment_text += "- 既存PRの品質問題を修正してください\n"
            comment_text += "- または新しいアプローチでの再実装を検討してください\n"
        
        return comment_text

    async def _dry_run_with_recovery(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """ドライラン（エラーリカバリー付き）"""
        issue_number = request.get("issue_number")
        if not issue_number:
            return {
                "status": "error",
                "message": "issue_number is required for dry_run mode"
            }
        
        try:
            issue = self.repo.get_issue(issue_number)
            complexity = await self.evaluator.evaluate(issue)
            
            return {
                "status": "dry_run",
                "issue": {
                    "number": issue.number,
                    "title": issue.title,
                    "priority": self._determine_priority(issue),
                    "complexity": complexity.score,
                    "processable": complexity.is_processable,
                    "factors": complexity.factors,
                },
                "error_handling": {
                    "circuit_breaker_state": self.error_handler.get_circuit_breaker("process_request").state.value,
                    "metrics": self.metrics
                }
            }
        except Exception as e:
            logger.error(f"Error in dry_run: {str(e)}")
            return {
                "status": "error",
                "message": f"Dry run failed: {str(e)}"
            }

    # 既存のメソッドを継承（必要に応じて再実装）
    async def scan_processable_issues(self) -> List[Issue]:
        """処理可能なイシューをスキャン"""
        # 既存の実装を使用（必要に応じてエラーハンドリングを追加）
        from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
        base_processor = AutoIssueProcessor()
        return await base_processor.scan_processable_issues()

    def _determine_priority(self, issue: Issue) -> str:
        """イシューの優先度を決定"""
        labels = [label.name.lower() for label in issue.labels]
        
        if any(p in labels for p in ["priority:critical", "critical"]):
            return "critical"
        elif any(p in labels for p in ["priority:high", "high"]):
            return "high"
        elif any(p in labels for p in ["priority:medium", "medium"]):
            return "medium"
        elif any(p in labels for p in ["priority:low", "low"]):
            return "low"
        else:
            return "medium"  # デフォルト

    async def _check_existing_pr_for_issue(self, issue_number: int) -> Optional[Dict[str, Any]]:
        """既存のPRをチェック"""
        pulls = self.repo.get_pulls(state='all')
        for pr in pulls:
            if f"#{issue_number}" in pr.title or f"Closes #{issue_number}" in pr.body:
                return {
                    "number": pr.number,
                    "html_url": pr.html_url,
                    "state": pr.state,
                    "merged": pr.merged
                }
        return None

    async def consult_four_sages(self, issue: Issue) -> Dict[str, Any]:
        """4賢者に相談"""
        sage_advice = {}
        
        try:
            # タスク賢者
            task_analysis = await self.task_sage.analyze_issue(issue)
            sage_advice["task_sage"] = task_analysis
            
            # インシデント賢者
            risk_assessment = await self.incident_sage.assess_risk(issue)
            sage_advice["incident_sage"] = risk_assessment
            
            # ナレッジ賢者
            knowledge_search = await self.knowledge_sage.search_related_knowledge(issue.title)
            sage_advice["knowledge_sage"] = knowledge_search
            
            # RAG賢者
            rag_results = await self.rag_sage.search(issue.title)
            sage_advice["rag_sage"] = rag_results
            
        except Exception as e:
            logger.error(f"Error consulting four sages: {str(e)}")
            sage_advice["error"] = str(e)
        
        return sage_advice

    def get_metrics(self) -> Dict[str, Any]:
        """メトリクスを取得"""
        circuit_breakers_state = {}
        for operation, cb in self.error_handler.circuit_breakers.items():
            circuit_breakers_state[operation] = cb.get_metrics()
        
        return {
            "processing_metrics": self.metrics,
            "circuit_breakers": circuit_breakers_state
        }


# エクスポート
__all__ = ["EnhancedAutoIssueProcessor"]