#!/usr/bin/env python3
"""
🚀 Enhanced Merge System
既存のPR作成システムを拡張し、スマートリトライ・監視・進捗報告を統合

機能:
- 既存create_pull_request.pyとの統合
- スマートリトライエンジンの組み込み
- PR状態監視システムの統合
- 状況別戦略の適用
- リアルタイム進捗報告
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
import os

# 新規実装モジュールをインポート
from .smart_merge_retry import SmartMergeRetryEngine, MergeableState, RetryConfig
from .pr_state_monitor import PRStateMonitor, StateChangeEvent, MonitoringConfig
from .situation_strategies import SituationStrategyEngine, StrategyContext, StrategyResult
from .progress_reporter import ProgressReporter

logger = logging.getLogger(__name__)


class EnhancedMergeSystem:
    """拡張マージシステム - 全機能統合版"""
    
    def __init__(self, pr_api_client, github_client):
        """
        初期化
        
        Args:
            pr_api_client: 既存のPR APIクライアント (GitHubCreatePullRequestImplementation)
            github_client: GitHub PyGithubクライアント
        """
        self.pr_api_client = pr_api_client
        self.github_client = github_client
        
        # コンポーネント初期化
        self.retry_engine = SmartMergeRetryEngine(
            pr_api_client=pr_api_client,
            progress_callback=self._retry_progress_callback
        )
        
        self.state_monitor = PRStateMonitor(pr_api_client)
        self.strategy_engine = SituationStrategyEngine(pr_api_client)
        self.progress_reporter = ProgressReporter(github_client)
        
        # イベントコールバック設定
        self._setup_event_callbacks()
    
    def _setup_event_callbacks(self):
        """イベントコールバックの設定"""
        # 状態変化イベントのコールバックを設定
        # これらは動的に設定されるため、ここでは基本的な構造のみ
        pass
    
    async def create_pr_with_smart_merge(
        self,
        title: str,
        head: str,
        base: str,
        body: Optional[str] = None,
        issue_number: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        スマートマージ機能付きPR作成
        
        Args:
            title: PRタイトル
            head: マージ元ブランチ
            base: マージ先ブランチ
            body: PR本文
            issue_number: 関連イシュー番号
            **kwargs: その他のPR作成オプション
            
        Returns:
            Dict[str, Any]: 作成・マージ結果
        """
        try:
            # 進捗セッション開始
            session_id = self.progress_reporter.start_session(
                pr_number=0,  # 仮の番号、PR作成後に更新
                issue_number=issue_number,
                initial_message="PR作成とスマートマージを開始しています..."
            )
            
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
            
            # スマートマージプロセス開始
            merge_result = await self._execute_smart_merge_process(
                pr_number, issue_number, pr_result
            )
            
            # 最終結果
            final_result = {
                **pr_result,
                "smart_merge_result": merge_result,
                "session_id": session_id
            }
            
            return final_result
            
        except Exception as e:
            logger.error(f"Enhanced merge system error: {e}")
            await self.progress_reporter.complete_session(
                0, "error", f"システムエラー: {str(e)}"
            )
            return {"success": False, "error": str(e)}
    
    async def _execute_smart_merge_process(
        self, 
        pr_number: int, 
        issue_number: Optional[int],
        pr_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """スマートマージプロセスの実行"""
        
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
                # 戦略による即座解決
                await self.progress_reporter.complete_session(
                    pr_number, "completed", f"戦略により解決: {strategy_result.message}",
                    {"strategy_result": strategy_result.to_dict()}
                )
                return {"success": True, "merge_type": "strategy", "result": strategy_result.to_dict()}
            
            elif strategy_result.result == StrategyResult.MANUAL_REQUIRED:
                # 手動対応必要
                await self.progress_reporter.complete_session(
                    pr_number, "manual_required", f"手動対応が必要: {strategy_result.message}",
                    {"strategy_result": strategy_result.to_dict()}
                )
                return {"success": False, "reason": "manual_required", "result": strategy_result.to_dict()}
            
            elif strategy_result.result == StrategyResult.RETRY_LATER:
                # リトライ戦略・監視が必要
                return await self._execute_monitoring_and_retry(pr_number, strategy_result)
            
            else:
                # その他の場合
                await self.progress_reporter.complete_session(
                    pr_number, "failed", f"戦略実行失敗: {strategy_result.message}",
                    {"strategy_result": strategy_result.to_dict()}
                )
                return {"success": False, "reason": "strategy_failed", "result": strategy_result.to_dict()}
        
        except Exception as e:
            logger.error(f"Smart merge process error for PR #{pr_number}: {e}")
            await self.progress_reporter.complete_session(
                pr_number, "error", f"プロセスエラー: {str(e)}"
            )
            return {"success": False, "error": str(e)}
    
    async def _execute_monitoring_and_retry(
        self, 
        pr_number: int, 
        strategy_result
    ) -> Dict[str, Any]:
        """監視・リトライプロセスの実行"""
        
        try:
            # 進捗報告
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
    
    async def get_system_status(self) -> Dict[str, Any]:
        """システム全体の状況を取得"""
        return {
            "active_monitors": self.state_monitor.get_monitoring_status(),
            "active_progress_sessions": self.progress_reporter.get_all_active_sessions(),
            "retry_statistics": self.retry_engine.get_statistics(),
            "timestamp": datetime.now().isoformat()
        }
    
    async def cancel_pr_processing(self, pr_number: int) -> bool:
        """PR処理のキャンセル"""
        try:
            # 監視停止
            await self.state_monitor.stop_monitoring(pr_number)
            
            # 進捗セッション終了
            await self.progress_reporter.complete_session(
                pr_number, "cancelled", "処理がキャンセルされました"
            )
            
            logger.info(f"Cancelled processing for PR #{pr_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling PR #{pr_number}: {e}")
            return False


# 使用例とヘルパー関数
async def create_enhanced_merge_system(github_token: str, repo_owner: str, repo_name: str):
    """拡張マージシステムの作成"""
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
    
    # 拡張システム作成
    enhanced_system = EnhancedMergeSystem(pr_api_client, github_client)
    
    return enhanced_system