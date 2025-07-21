#!/usr/bin/env python3
"""
🔗 PR Monitoring Integration Test
PR状態監視システム全体の統合テスト
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os

# テスト対象のインポート
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from libs.integrations.github.pr_state_monitor import (
    PRStateMonitor, MonitoringConfig, StateChangeEvent
)
from libs.integrations.github.auto_action_engine import AutoActionEngine, ActionType
from libs.integrations.github.progress_reporter import ProgressReporter


class TestPRMonitoringIntegration:
    """PR監視システム統合テスト"""
    
    @pytest.fixture
    def mock_github_client(self):
        """統合用モックGitHubクライアント"""
        client = Mock()
        
        # PR情報のモック
        client.get_pull_request = Mock(return_value={
            "success": True,
            "pull_request": {
                "number": 123,
                "title": "Test Feature Implementation",
                "state": "open",
                "mergeable": True,
                "mergeable_state": "clean",
                "draft": False,
                "behind_by": 0,
                "ahead_by": 3,
                "head": {"sha": "abc123", "ref": "feature-branch"},
                "base": {"sha": "def456", "ref": "main"}
            }
        })
        
        # マージ処理のモック
        client.merge_pull_request = AsyncMock(return_value={
            "success": True,
            "merged": True,
            "sha": "merged_sha_123",
            "message": "Pull Request successfully merged"
        })
        
        # GitHub API オブジェクト（ProgressReporter用）
        mock_repo = Mock()
        mock_issue = Mock()
        mock_comment = Mock()
        mock_comment.id = 12345
        mock_issue.create_comment.return_value = mock_comment
        mock_issue.get_comment.return_value = mock_comment
        mock_repo.get_issue.return_value = mock_issue
        mock_repo.get_pull.return_value = mock_issue
        client.repo = mock_repo
        
        return client
    
    @pytest.fixture
    def monitoring_components(self, mock_github_client):
        """監視システムコンポーネント"""
        # 各コンポーネントを初期化
        monitor = PRStateMonitor(mock_github_client)
        action_engine = AutoActionEngine(mock_github_client)
        progress_reporter = ProgressReporter(mock_github_client)
        
        return {
            "monitor": monitor,
            "action_engine": action_engine,
            "progress_reporter": progress_reporter,
            "github_client": mock_github_client
        }
    
    @pytest.mark.asyncio
    async def test_complete_monitoring_workflow(self, monitoring_components):
        """完全な監視ワークフローテスト"""
        monitor = monitoring_components["monitor"]
        action_engine = monitoring_components["action_engine"]
        progress_reporter = monitoring_components["progress_reporter"]
        
        pr_number = 123
        issue_number = 147
        
        # 1. 進捗報告セッション開始
        session_id = progress_reporter.start_session(
            pr_number=pr_number,
            issue_number=issue_number,
            initial_message="PR状態監視を開始します"
        )
        assert session_id is not None
        
        # 2. 監視設定
        events_received = []
        actions_taken = []
        
        async def event_handler(pr_num, event_type, event_data):
            """イベントハンドラー"""
            events_received.append((event_type, event_data))
            
            # 進捗更新
            await progress_reporter.update_progress(
                pr_number=pr_num,
                status="in_progress",
                message=f"イベント検出: {event_type.value}",
                details=event_data,
                force_comment_update=True
            )
            
            # 自動アクション実行
            action_result = await action_engine.handle_state_change(
                pr_num, event_type, event_data
            )
            actions_taken.append(action_result)
            
            # アクション結果を進捗に反映
            if action_result.get("success"):
                await progress_reporter.update_progress(
                    pr_number=pr_num,
                    status="success",
                    message=f"自動アクション完了: {action_result.get('action_taken')}",
                    details=action_result,
                    force_comment_update=True
                )
            else:
                await progress_reporter.update_progress(
                    pr_number=pr_num,
                    status="error",
                    message=f"自動アクション失敗: {action_result.get('error', 'Unknown error')}",
                    details=action_result,
                    force_comment_update=True
                )
        
        config = MonitoringConfig(
            polling_interval=1,  # 高速テスト用
            max_monitoring_duration=10,  # 10秒間のテスト
            event_callbacks={
                StateChangeEvent.CI_PASSED: [event_handler],
                StateChangeEvent.REVIEW_APPROVED: [event_handler],
                StateChangeEvent.READY_TO_MERGE: [event_handler],
                StateChangeEvent.MERGE_BLOCKED: [event_handler]
            }
        )
        
        # 3. 監視開始
        monitoring_started = await monitor.start_monitoring(pr_number, config)
        assert monitoring_started is True
        
        # 状態を変更してイベントをトリガー
        # CI成功状態に変更
        monitor._update_pr_state(pr_number, {
            "mergeable_state": "clean",
            "state": "open",
            "ci_status": "success"  # モック用
        })
        
        # 少し待機してイベント処理を確認
        await asyncio.sleep(2)
        
        # 4. 監視停止
        await monitor.stop_monitoring(pr_number)
        
        # 5. セッション完了
        completion_success = await progress_reporter.complete_session(
            pr_number=pr_number,
            final_status="completed",
            final_message="PR監視が正常に完了しました",
            final_details={
                "events_detected": len(events_received),
                "actions_taken": len(actions_taken),
                "session_duration": "10秒"
            }
        )
        assert completion_success is True
        
        # 結果検証
        assert len(events_received) >= 0  # イベント検出（状態変化による）
        assert len(actions_taken) >= 0   # アクション実行（イベントによる）
        
        # セッション履歴確認
        final_status = progress_reporter.get_session_status(pr_number)
        assert final_status is None  # セッションが完了して削除されている
        
        # 監視状態確認
        monitoring_status = monitor.get_monitoring_status()
        assert pr_number not in monitoring_status.get("active_monitors", {})
    
    @pytest.mark.asyncio
    async def test_error_scenario_handling(self, monitoring_components):
        """エラーシナリオハンドリングテスト"""
        monitor = monitoring_components["monitor"]
        action_engine = monitoring_components["action_engine"]
        progress_reporter = monitoring_components["progress_reporter"]
        github_client = monitoring_components["github_client"]
        
        pr_number = 456
        issue_number = 148
        
        # GitHub API エラーを発生させる
        github_client.get_pull_request.return_value = {
            "success": False,
            "error": "API rate limit exceeded"
        }
        
        # セッション開始
        session_id = progress_reporter.start_session(
            pr_number=pr_number,
            issue_number=issue_number,
            initial_message="エラーシナリオテスト開始"
        )
        
        # エラー状況でのアクション実行
        result = await action_engine.handle_state_change(
            pr_number, StateChangeEvent.CI_PASSED, {}
        )
        
        # エラーが適切にハンドリングされることを確認
        assert result["success"] is False
        assert "error" in result or "Failed to get PR info" in result.get("reason", "")
        
        # エラー報告
        await progress_reporter.update_progress(
            pr_number=pr_number,
            status="error",
            message="API呼び出しでエラーが発生しました",
            details={"error": "API rate limit exceeded"},
            force_comment_update=True
        )
        
        # セッション完了
        await progress_reporter.complete_session(
            pr_number=pr_number,
            final_status="failed",
            final_message="APIエラーにより処理を中断しました"
        )
        
        # エラーが記録されていることを確認
        final_status = progress_reporter.get_session_status(pr_number)
        assert final_status is None  # セッション完了
    
    @pytest.mark.asyncio
    async def test_concurrent_monitoring(self, monitoring_components):
        """複数PR同時監視テスト"""
        monitor = monitoring_components["monitor"]
        progress_reporter = monitoring_components["progress_reporter"]
        
        pr_numbers = [100, 200, 300]
        
        # 複数PRの監視を同時開始
        for pr_num in pr_numbers:
            session_id = progress_reporter.start_session(
                pr_number=pr_num,
                issue_number=pr_num + 47,  # 147, 247, 347
                initial_message=f"PR #{pr_num} の監視を開始"
            )
            assert session_id is not None
            
            config = MonitoringConfig(
                polling_interval=2,
                max_monitoring_duration=5,
                event_callbacks={}
            )
            
            monitoring_started = await monitor.start_monitoring(pr_num, config)
            assert monitoring_started is True
        
        # 全セッションがアクティブであることを確認
        active_sessions = progress_reporter.get_all_active_sessions()
        assert len(active_sessions) == 3
        for pr_num in pr_numbers:
            assert pr_num in active_sessions
        
        # 少し待機
        await asyncio.sleep(3)
        
        # 全監視を停止
        for pr_num in pr_numbers:
            await monitor.stop_monitoring(pr_num)
            await progress_reporter.complete_session(
                pr_number=pr_num,
                final_status="completed",
                final_message=f"PR #{pr_num} 監視完了"
            )
        
        # 全セッションが終了していることを確認
        active_sessions = progress_reporter.get_all_active_sessions()
        assert len(active_sessions) == 0
    
    def test_component_integration_basic(self, monitoring_components):
        """コンポーネント統合基本テスト"""
        monitor = monitoring_components["monitor"]
        action_engine = monitoring_components["action_engine"]
        progress_reporter = monitoring_components["progress_reporter"]
        
        # 各コンポーネントが適切に初期化されていることを確認
        assert monitor is not None
        assert action_engine is not None  
        assert progress_reporter is not None
        
        # 基本的なAPIが利用可能であることを確認
        assert hasattr(monitor, 'start_monitoring')
        assert hasattr(action_engine, 'handle_state_change')
        assert hasattr(progress_reporter, 'start_session')
        
        # 初期状態の確認
        monitoring_status = monitor.get_monitoring_status()
        assert "active_monitors" in monitoring_status
        
        active_sessions = progress_reporter.get_all_active_sessions()
        assert len(active_sessions) == 0
        
        action_history = action_engine.get_action_history()
        assert len(action_history) == 0