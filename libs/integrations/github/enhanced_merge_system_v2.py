#!/usr/bin/env python3
"""
🚀 Enhanced Merge System V2
コンフリクト解決機能を統合した拡張マージシステム

統合機能:
- スマートリトライエンジン
- PR状態監視システム
- 状況別戦略エンジン
- リアルタイム進捗報告
- 自動コンフリクト解決 (NEW!)
- ブランチ自動更新 (NEW!)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
import os

# 既存モジュール
from .smart_merge_retry import SmartMergeRetryEngine, MergeableState, RetryConfig
from .pr_state_monitor import PRStateMonitor, StateChangeEvent, MonitoringConfig
from .situation_strategies import SituationStrategyEngine, StrategyContext, StrategyResult
from .progress_reporter import ProgressReporter

# 新規モジュール - コンフリクト解決
from .improved_conflict_analyzer import ImprovedConflictAnalyzer, ConflictInfo
from .branch_updater import BranchUpdater, UpdateAnalysis, UpdateStrategy, RiskLevel

logger = logging.getLogger(__name__)


class EnhancedMergeSystemV2:
    """拡張マージシステムV2 - コンフリクト解決統合版"""
    
    def __init__(self, pr_api_client, github_client, repo_path: str = None):
        """
        初期化
        
        Args:
            pr_api_client: 既存のPR APIクライアント
            github_client: GitHub PyGithubクライアント
            repo_path: Gitリポジトリのパス（コンフリクト解決用）
        """
        self.pr_api_client = pr_api_client
        self.github_client = github_client
        self.repo_path = repo_path or os.getcwd()
        
        # 既存コンポーネント
        self.retry_engine = SmartMergeRetryEngine(
            pr_api_client=pr_api_client,
            progress_callback=self._retry_progress_callback
        )
        self.state_monitor = PRStateMonitor(pr_api_client)
        self.strategy_engine = SituationStrategyEngine(pr_api_client, self.repo_path)
        self.progress_reporter = ProgressReporter(github_client)
        
        # 新規コンポーネント - コンフリクト解決
        self.conflict_analyzer = ImprovedConflictAnalyzer(self.repo_path)
        self.branch_updater = BranchUpdater(self.repo_path)
        
        # 統計情報
        self.stats = {
            "total_prs_processed": 0,
            "auto_merged": 0,
            "conflicts_resolved": 0,
            "branches_updated": 0,
            "manual_required": 0
        }
    
    async def create_pr_with_smart_merge_v2(
        self,
        title: str,
        head: str,
        base: str,
        body: Optional[str] = None,
        issue_number: Optional[int] = None,
        auto_resolve_conflicts: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        コンフリクト解決機能付きスマートマージPR作成
        
        Args:
            title: PRタイトル
            head: マージ元ブランチ
            base: マージ先ブランチ
            body: PR本文
            issue_number: 関連イシュー番号
            auto_resolve_conflicts: コンフリクト自動解決を有効化
            **kwargs: その他のPR作成オプション
            
        Returns:
            Dict[str, Any]: 作成・マージ結果
        """
        self.stats["total_prs_processed"] += 1
        
        try:
            # 進捗セッション開始
            session_id = self.progress_reporter.start_session(
                pr_number=0,
                issue_number=issue_number,
                initial_message="PR作成とスマートマージV2を開始しています..."
            )
            
            # まずブランチ状態を分析
            if auto_resolve_conflicts:
                branch_result = await self._handle_branch_preparation(head, base)
                if not branch_result["success"]:
                    await self.progress_reporter.complete_session(
                        0, "failed", f"ブランチ準備失敗: {branch_result.get('message', 'Unknown error')}"
                    )
                    self.stats["manual_required"] += 1
                    return branch_result
            
            # PR作成実行
            await self.progress_reporter.update_progress(
                0, "in_progress", "PRを作成中...", {"step": "pr_creation"}
            )
            
            pr_result = self.pr_api_client.create_pull_request(
                title=title,
                head=head,
                base=base,
                body=body,
                **kwargs
            )
            
            if not pr_result.get("success", False):
                await self.progress_reporter.complete_session(
                    0, "failed", f"PR作成に失敗: {pr_result.get('error', 'Unknown error')}"
                )
                return pr_result
            
            pr_number = pr_result["pull_request"]["number"]
            
            # セッションのPR番号を更新
            if 0 in self.progress_reporter.active_sessions:
                session = self.progress_reporter.active_sessions[0]
                session.pr_number = pr_number
                self.progress_reporter.active_sessions[pr_number] = session
                del self.progress_reporter.active_sessions[0]
            
            await self.progress_reporter.update_progress(
                pr_number, "success", f"PR #{pr_number} を作成しました", 
                {"pr_url": pr_result.get("pr_url")}
            )
            
            # 拡張スマートマージプロセス実行
            merge_result = await self._execute_enhanced_merge_process(
                pr_number, issue_number, pr_result, auto_resolve_conflicts
            )
            
            # 統計更新
            if merge_result.get("success"):
                if merge_result.get("merge_type") == "immediate":
                    self.stats["auto_merged"] += 1
                elif merge_result.get("conflicts_resolved", 0) > 0:
                    self.stats["conflicts_resolved"] += merge_result["conflicts_resolved"]
            else:
                self.stats["manual_required"] += 1
            
            # 最終結果
            final_result = {
                **pr_result,
                "smart_merge_result": merge_result,
                "session_id": session_id,
                "statistics": self.get_statistics()
            }
            
            return final_result
            
        except Exception as e:
            logger.error(f"Enhanced merge system V2 error: {e}")
            await self.progress_reporter.complete_session(
                0, "error", f"システムエラー: {str(e)}"
            )
            return {"success": False, "error": str(e)}
    
    async def _handle_branch_preparation(self, head: str, base: str) -> Dict[str, Any]:
        """ブランチ準備処理（behind解決・コンフリクト事前チェック）"""
        try:
            await self.progress_reporter.update_progress(
                0, "in_progress", "ブランチ状態を分析中...", 
                {"step": "branch_analysis"}
            )
            
            # ブランチ更新分析
            update_analysis = await self.branch_updater.analyze_branch_update(head, base)
            
            # behind状態の解決が必要な場合
            if update_analysis.branch_status.commits_behind > 0:
                await self.progress_reporter.update_progress(
                    0, "in_progress", 
                    f"ブランチが{update_analysis.branch_status.commits_behind}コミット遅れています。更新を検討中...",
                    {
                        "commits_behind": update_analysis.branch_status.commits_behind,
                        "risk_level": update_analysis.risk_level.value
                    }
                )
                
                # 安全な場合のみ自動更新
                if update_analysis.risk_level in [RiskLevel.SAFE, RiskLevel.LOW]:
                    update_result = await self.branch_updater.execute_safe_update(
                        update_analysis, dry_run=False
                    )
                    
                    if update_result["success"]:
                        self.stats["branches_updated"] += 1
                        await self.progress_reporter.update_progress(
                            0, "success", "ブランチを自動更新しました",
                            {"update_strategy": update_result.get("strategy")}
                        )
                    else:
                        return {
                            "success": False,
                            "reason": "branch_update_failed",
                            "message": update_result.get("message", "Branch update failed"),
                            "update_analysis": update_analysis.to_dict()
                        }
                else:
                    return {
                        "success": False,
                        "reason": "manual_update_required",
                        "message": f"ブランチ更新のリスクが高いため手動対応が必要です (リスク: {update_analysis.risk_level.value})",
                        "update_analysis": update_analysis.to_dict()
                    }
            
            # コンフリクト事前チェック
            conflict_result = self.conflict_analyzer.analyze_merge_conflicts(base, head)
            
            if conflict_result["conflicts_found"]:
                await self.progress_reporter.update_progress(
                    0, "warning", 
                    f"{conflict_result['total_conflicts']}個のコンフリクトを検出しました",
                    {
                        "total_conflicts": conflict_result["total_conflicts"],
                        "auto_resolvable": conflict_result["auto_resolvable_count"]
                    }
                )
                
                # 自動解決可能なコンフリクトがある場合
                if conflict_result["auto_resolvable_count"] > 0:
                    conflicts = [ConflictInfo(**c) for c in conflict_result["conflicts"]]
                    resolution_result = self.conflict_analyzer.auto_resolve_safe_conflicts(conflicts)
                    
                    if resolution_result["success"]:
                        await self.progress_reporter.update_progress(
                            0, "success", 
                            f"{len(resolution_result['resolved_files'])}個のコンフリクトを自動解決しました",
                            {"resolved_files": resolution_result["resolved_files"]}
                        )
                        
                        # 解決後にコミット
                        import subprocess
                        subprocess.run(
                            ["git", "commit", "-m", f"Auto-resolve conflicts for PR"],
                            cwd=self.repo_path,
                            check=True
                        )
                    else:
                        await self.progress_reporter.update_progress(
                            0, "warning", "一部のコンフリクト解決に失敗しました",
                            {"failed_files": resolution_result["failed_files"]}
                        )
            
            return {"success": True, "conflicts_resolved": conflict_result.get(
                "auto_resolvable_count",
                0
            )}
            
        except Exception as e:
            logger.error(f"Branch preparation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_enhanced_merge_process(
        self, 
        pr_number: int, 
        issue_number: Optional[int],
        pr_result: Dict[str, Any],
        auto_resolve_conflicts: bool
    ) -> Dict[str, Any]:
        """拡張スマートマージプロセスの実行"""
        
        try:
            # 初期状態チェック
            await self.progress_reporter.update_progress(
                pr_number, "in_progress", "PR状態を分析中...", 
                {"step": "initial_analysis"}
            )
            
            initial_state = await self._get_initial_pr_state(pr_number)
            
            # 即座にマージ可能かチェック
            if initial_state.get("ready_to_merge", False):
                await self.progress_reporter.update_progress(
                    pr_number, "in_progress", "即座マージ実行中...",
                    {"mergeable_state": initial_state.get("mergeable_state")}
                )
                
                merge_result = await self.retry_engine._execute_merge(pr_number)
                
                if merge_result.get("success", False):
                    await self.progress_reporter.complete_session(
                        pr_number, "completed", "マージが正常に完了しました",
                        {"merge_type": "immediate", "merge_result": merge_result}
                    )
                    return {"success": True, "merge_type": "immediate", "result": merge_result}
            
            # コンフリクト対応が必要な場合
            if initial_state.get("mergeable_state") == "dirty" and auto_resolve_conflicts:
                conflict_result = await self._handle_pr_conflicts(pr_number, pr_result)
                if conflict_result["handled"]:
                    # コンフリクト解決後、再度マージを試行
                    initial_state = await self._get_initial_pr_state(pr_number)
                    if initial_state.get("ready_to_merge", False):
                        merge_result = await self.retry_engine._execute_merge(pr_number)
                        if merge_result.get("success", False):
                            await self.progress_reporter.complete_session(
                                pr_number, "completed", 
                                "コンフリクト解決後、マージが完了しました",
                                {
                                    "merge_type": "after_conflict_resolution", 
                                    "conflicts_resolved": conflict_result.get("resolved", 0)
                                }
                            )
                            return {
                                "success": True, 
                                "merge_type": "after_conflict_resolution",
                                "conflicts_resolved": conflict_result.get("resolved", 0),
                                "result": merge_result
                            }
            
            # 状況別戦略が必要な場合
            strategy_context = StrategyContext(
                pr_number=pr_number,
                pr_title=pr_result["pull_request"]["title"],
                branch_name=pr_result["pull_request"]["head"]["ref"],
                base_branch=pr_result["pull_request"]["base"]["ref"],
                mergeable_state=initial_state.get("mergeable_state", "unknown"),
                mergeable=initial_state.get("mergeable"),
                draft=initial_state.get("draft", False),
                ci_status=initial_state.get("ci_status"),
                review_state=initial_state.get("review_state")
            )
            
            # 状況別戦略を実行
            await self.progress_reporter.update_progress(
                pr_number, "in_progress", "状況別戦略を実行中...",
                {"mergeable_state": strategy_context.mergeable_state}
            )
            
            strategy_result = await self.strategy_engine.execute_strategy(strategy_context)
            
            if strategy_result.result == StrategyResult.SUCCESS:
                await self.progress_reporter.complete_session(
                    pr_number, "completed", f"戦略により解決: {strategy_result.message}",
                    {"strategy_result": strategy_result.to_dict()}
                )
                return {"success": True, "merge_type": "strategy", "result": strategy_result.to_dict()}
            
            elif strategy_result.result == StrategyResult.MANUAL_REQUIRED:
                await self.progress_reporter.complete_session(
                    pr_number, "manual_required", f"手動対応が必要: {strategy_result.message}",
                    {"strategy_result": strategy_result.to_dict()}
                )
                return {"success": False, "reason": "manual_required", "result": strategy_result.to_dict()}
            
            elif strategy_result.result == StrategyResult.RETRY_LATER:
                # リトライ戦略・監視が必要
                return await self._execute_monitoring_and_retry(pr_number, strategy_result)
            
            else:
                await self.progress_reporter.complete_session(
                    pr_number, "failed", f"戦略実行失敗: {strategy_result.message}",
                    {"strategy_result": strategy_result.to_dict()}
                )
                return {"success": False, "reason": "strategy_failed", "result": strategy_result.to_dict()}
        
        except Exception as e:
            logger.error(f"Enhanced merge process error for PR #{pr_number}: {e}")
            await self.progress_reporter.complete_session(
                pr_number, "error", f"プロセスエラー: {str(e)}"
            )
            return {"success": False, "error": str(e)}
    
    async def _handle_pr_conflicts(
        self,
        pr_number: int,
        pr_result: Dict[str,
        Any]
    ) -> Dict[str, Any]:
        """PRのコンフリクト処理"""
        try:
            await self.progress_reporter.update_progress(
                pr_number, "in_progress", "PRのコンフリクトを分析中...",
                {"step": "conflict_analysis"}
            )
            
            head_branch = pr_result["pull_request"]["head"]["ref"]
            base_branch = pr_result["pull_request"]["base"]["ref"]
            
            # コンフリクト分析
            conflict_result = self.conflict_analyzer.analyze_merge_conflicts(
                base_branch,
                head_branch
            )
            
            if not conflict_result["conflicts_found"]:
                return {"handled": False, "resolved": 0}
            
            await self.progress_reporter.update_progress(
                pr_number, "warning", 
                f"{conflict_result['total_conflicts']}個のコンフリクトを検出",
                {
                    "total_conflicts": conflict_result["total_conflicts"],
                    "auto_resolvable": conflict_result["auto_resolvable_count"]
                }
            )
            
            # 自動解決試行
            if conflict_result["auto_resolvable_count"] > 0:
                conflicts = [ConflictInfo(**c) for c in conflict_result["conflicts"]]
                resolution_result = self.conflict_analyzer.auto_resolve_safe_conflicts(conflicts)
                
                if resolution_result["success"]:
                    await self.progress_reporter.update_progress(
                        pr_number, "success", 
                        f"{len(resolution_result['resolved_files'])}個のコンフリクトを解決",
                        {"resolved_files": resolution_result["resolved_files"]}
                    )
                    
                    # ブランチをプッシュ
                    import subprocess
                    subprocess.run(
                        ["git", "push", "origin", head_branch],
                        cwd=self.repo_path,
                        check=True
                    )
                    
                    return {
                        "handled": True, 
                        "resolved": len(resolution_result["resolved_files"])
                    }
            
            return {"handled": False, "resolved": 0}
            
        except Exception as e:
            logger.error(f"Conflict handling failed for PR #{pr_number}: {e}")
            return {"handled": False, "resolved": 0, "error": str(e)}
    
    async def _execute_monitoring_and_retry(
        self, 
        pr_number: int, 
        strategy_result
    ) -> Dict[str, Any]:
        """監視・リトライプロセスの実行"""
        
        try:
            await self.progress_reporter.update_progress(
                pr_number, "waiting", "監視・リトライプロセスを開始します",
                {
                    "strategy_message": strategy_result.message,
                    "retry_after": strategy_result.retry_after
                }
            )
            
            # 監視設定
            monitoring_config = MonitoringConfig(
                polling_interval=30,
                max_monitoring_duration=1800,  # 30分
                auto_stop_on_merge=True,
                auto_stop_on_close=True
            )
            
            # イベントコールバックを設定
            await self._setup_monitoring_callbacks(pr_number, monitoring_config)
            
            # 監視開始
            monitor_started = await self.state_monitor.start_monitoring(
                pr_number,
                monitoring_config
            )
            
            if not monitor_started:
                await self.progress_reporter.complete_session(
                    pr_number, "failed", "監視開始に失敗しました"
                )
                return {"success": False, "reason": "monitoring_failed"}
            
            # スマートリトライ実行
            retry_result = await self.retry_engine.attempt_smart_merge(pr_number)
            
            # 監視停止
            await self.state_monitor.stop_monitoring(pr_number)
            
            # 結果に応じて進捗完了
            if retry_result.get("success", False):
                await self.progress_reporter.complete_session(
                    pr_number, "completed", "スマートリトライによりマージ完了",
                    {"retry_result": retry_result}
                )
                return {"success": True, "merge_type": "smart_retry", "result": retry_result}
            else:
                reason = retry_result.get("reason", "unknown")
                message = f"スマートリトライ失敗: {reason}"
                
                if reason == "manual_intervention_required":
                    status = "manual_required"
                elif reason == "timeout":
                    status = "timeout"
                else:
                    status = "failed"
                
                await self.progress_reporter.complete_session(
                    pr_number, status, message, {"retry_result": retry_result}
                )
                return {"success": False, "reason": reason, "result": retry_result}
        
        except Exception as e:
            logger.error(f"Monitoring and retry error for PR #{pr_number}: {e}")
            await self.progress_reporter.complete_session(
                pr_number, "error", f"監視・リトライエラー: {str(e)}"
            )
            return {"success": False, "error": str(e)}
    
    async def _setup_monitoring_callbacks(self, pr_number: int, config: MonitoringConfig):
        """監視用イベントコールバックの設定"""
        
        async def on_ci_passed(pr_num, event_type, event_data):
            await self.progress_reporter.update_progress(
                pr_num, "in_progress", "CI実行が完了しました - マージを再試行中",
                {"event": event_type, "event_data": event_data}
            )
        
        async def on_conflicts_resolved(pr_num, event_type, event_data):
            await self.progress_reporter.update_progress(
                pr_num, "in_progress", "コンフリクトが解決されました - マージを再試行中",
                {"event": event_type, "event_data": event_data}
            )
        
        async def on_ready_to_merge(pr_num, event_type, event_data):
            await self.progress_reporter.update_progress(
                pr_num, "in_progress", "マージ準備が完了しました",
                {"event": event_type, "event_data": event_data}
            )
        
        # イベントコールバックを登録
        config.event_callbacks = {
            StateChangeEvent.CI_PASSED: [on_ci_passed],
            StateChangeEvent.CONFLICTS_RESOLVED: [on_conflicts_resolved],
            StateChangeEvent.READY_TO_MERGE: [on_ready_to_merge]
        }
    
    async def _retry_progress_callback(self, pr_number: int, status: str, message: str):
        """リトライエンジンからの進捗コールバック"""
        await self.progress_reporter.update_progress(
            pr_number, status, message, {"source": "retry_engine"}
        )
    
    async def _get_initial_pr_state(self, pr_number: int) -> Dict[str, Any]:
        """初期PR状態の取得"""
        try:
            pr_info = self.pr_api_client._get_pull_request(pr_number)
            if pr_info["success"]:
                pr = pr_info["pull_request"]
                
                # マージ可能性の簡易判定
                ready_to_merge = (
                    pr.get("mergeable") is True and 
                    pr.get("mergeable_state") == "clean" and
                    not pr.get("draft", False)
                )
                
                return {
                    "mergeable": pr.get("mergeable"),
                    "mergeable_state": pr.get("mergeable_state", "unknown"),
                    "draft": pr.get("draft", False),
                    "ready_to_merge": ready_to_merge,
                    "ci_status": None,  # 実装により詳細取得
                    "review_state": None  # 実装により詳細取得
                }
            else:
                return {"ready_to_merge": False, "mergeable_state": "unknown"}
                
        except Exception as e:
            logger.error(f"Error getting initial PR state for #{pr_number}: {e}")
            return {"ready_to_merge": False, "mergeable_state": "unknown"}
    
    def get_statistics(self) -> Dict[str, Any]:
        """統計情報の取得"""
        total = self.stats["total_prs_processed"]
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            "auto_merge_rate": (self.stats["auto_merged"] / total) * 100,
            "conflict_resolution_rate": (self.stats["conflicts_resolved"] / total) * 100,
            "branch_update_rate": (self.stats["branches_updated"] / total) * 100,
            "manual_required_rate": (self.stats["manual_required"] / total) * 100
        }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """システム全体の状況を取得"""
        return {
            "active_monitors": self.state_monitor.get_monitoring_status(),
            "active_progress_sessions": self.progress_reporter.get_all_active_sessions(),
            "retry_statistics": self.retry_engine.get_statistics(),
            "merge_statistics": self.get_statistics(),
            "timestamp": datetime.now().isoformat()
        }


# 使用例とヘルパー関数
async def create_enhanced_merge_system_v2(
    github_token: str, 
    repo_owner: str, 
    repo_name: str,
    repo_path: str = None
):
    """拡張マージシステムV2の作成"""
    from .api_implementations.create_pull_request import GitHubCreatePullRequestImplementation
    from github import Github
    
    # APIクライアント初期化
    pr_api_client = GitHubCreatePullRequestImplementation(
        token=github_token,
        repo_owner=repo_owner,
        repo_name=repo_name
    )
    
    github_client = Github(github_token)
    github_client.repo = github_client.get_repo(f"{repo_owner}/{repo_name}")
    
    # 拡張システムV2作成
    enhanced_system = EnhancedMergeSystemV2(
        pr_api_client, 
        github_client,
        repo_path=repo_path
    )
    
    return enhanced_system