#!/usr/bin/env python3
"""
🧪 Enhanced Merge System Tests
スマートリトライ・監視・進捗報告統合システムのテスト

テストカテゴリ:
- スマートリトライエンジン
- PR状態監視システム
- 状況別戦略エンジン
- 進捗報告システム
- 統合システム全体
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json

# テスト対象モジュールのインポート
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from elders_guild.elder_tree.integrations.github.smart_merge_retry import (
    SmartMergeRetryEngine, MergeableState, RetryConfig, RetryAttempt
)
from elders_guild.elder_tree.integrations.github.pr_state_monitor import (
    PRStateMonitor, StateChangeEvent, PRState, MonitoringConfig
)
from elders_guild.elder_tree.integrations.github.situation_strategies import (
    SituationStrategyEngine, StrategyContext, StrategyResult
)
from elders_guild.elder_tree.integrations.github.progress_reporter import (
    ProgressReporter, ProgressSession, ProgressEntry
)
from elders_guild.elder_tree.integrations.github.enhanced_merge_system import EnhancedMergeSystem


class TestSmartMergeRetryEngine:
    """スマートリトライエンジンのテスト"""
    
    @pytest.fixture
    def mock_pr_api_client(self):
        """モックPR APIクライアント"""
        client = Mock()
        client._get_pull_request = Mock()
        client._enable_auto_merge = Mock()
        return client
    
    @pytest.fixture
    def retry_engine(self, mock_pr_api_client):
        """リトライエンジンインスタンス"""
        return SmartMergeRetryEngine(
            pr_api_client=mock_pr_api_client,
            progress_callback=AsyncMock()
        )
    
    @pytest.mark.asyncio
    async def test_immediate_merge_success(self, retry_engine, mock_pr_api_client):
        """即座マージ成功のテスト"""
        # PR状態: 即座マージ可能
        mock_pr_api_client._get_pull_request.return_value = {
            "success": True,
            "pull_request": {
                "mergeable": True,
                "mergeable_state": "clean",
                "draft": False
            }
        }
        
        # マージ成功
        mock_pr_api_client._enable_auto_merge.return_value = {
            "success": True,
            "merged": True
        }
        
        result = await retry_engine.attempt_smart_merge(123)
        
        assert result["success"] is True
        assert "merge_result" in result
        mock_pr_api_client._enable_auto_merge.assert_called_once_with(123)
    
    @pytest.mark.asyncio
    async def test_retry_for_unstable_state(self, retry_engine, mock_pr_api_client):
        """CI実行中状態でのリトライテスト"""
        # 初回: CI実行中
        # 2回目: マージ可能
        pr_states = [
            {
                "success": True,
                "pull_request": {
                    "mergeable": None,
                    "mergeable_state": "unstable",
                    "draft": False
                }
            },
            {
                "success": True,
                "pull_request": {
                    "mergeable": True,
                    "mergeable_state": "clean",
                    "draft": False
                }
            }
        ]
        
        mock_pr_api_client._get_pull_request.side_effect = pr_states
        mock_pr_api_client._enable_auto_merge.return_value = {
            "success": True,
            "merged": True
        }
        
        # 短い設定でテスト高速化
        custom_config = {
            MergeableState.UNSTABLE: RetryConfig(
                max_retries=2, base_delay=0.1, max_delay=0.2, timeout=5
            )
        }
        
        result = await retry_engine.attempt_smart_merge(123, custom_config)
        
        assert result["success"] is True
        assert result["attempts"] == 2
        assert mock_pr_api_client._get_pull_request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_manual_intervention_required(self, retry_engine, mock_pr_api_client):
        """手動対応必要なケースのテスト"""
        mock_pr_api_client._get_pull_request.return_value = {
            "success": True,
            "pull_request": {
                "mergeable": False,
                "mergeable_state": "dirty",
                "draft": False
            }
        }
        
        result = await retry_engine.attempt_smart_merge(123)
        
        assert result["success"] is False
        assert result["reason"] == "manual_intervention_required"
        assert "dirty" in result["message"]
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, retry_engine, mock_pr_api_client):
        """タイムアウト処理のテスト"""
        # 常にCI実行中を返す
        mock_pr_api_client._get_pull_request.return_value = {
            "success": True,
            "pull_request": {
                "mergeable": None,
                "mergeable_state": "unstable",
                "draft": False
            }
        }
        
        # 短いタイムアウト設定
        custom_config = {
            MergeableState.UNSTABLE: RetryConfig(
                max_retries=100, base_delay=0.01, max_delay=0.02, timeout=0.1
            )
        }
        
        result = await retry_engine.attempt_smart_merge(123, custom_config)
        
        assert result["success"] is False
        assert result["reason"] == "timeout"
    
    def test_delay_calculation(self, retry_engine):
        """待機時間計算のテスト"""
        config = RetryConfig(base_delay=10, backoff_factor=2.0, max_delay=100)
        
        # 指数バックオフの確認
        assert retry_engine._calculate_delay(0, config) == 10
        assert retry_engine._calculate_delay(1, config) == 20
        assert retry_engine._calculate_delay(2, config) == 40
        assert retry_engine._calculate_delay(10, config) == 100  # max_delay制限


class TestPRStateMonitor:
    """PR状態監視システムのテスト"""
    
    @pytest.fixture
    def mock_pr_api_client(self):
        """モックPR APIクライアント"""
        client = Mock()
        client._get_pull_request = Mock()
        return client
    
    @pytest.fixture
    def state_monitor(self, mock_pr_api_client):
        """状態監視インスタンス"""
        return PRStateMonitor(mock_pr_api_client)
    
    @pytest.mark.asyncio
    async def test_start_monitoring(self, state_monitor, mock_pr_api_client):
        """監視開始のテスト"""
        mock_pr_api_client._get_pull_request.return_value = {
            "success": True,
            "pull_request": {
                "mergeable": True,
                "mergeable_state": "clean",
                "draft": False,
                "state": "open"
            }
        }
        
        config = MonitoringConfig(polling_interval=0.1, max_monitoring_duration=1)
        result = await state_monitor.start_monitoring(123, config)
        
        assert result is True
        assert 123 in state_monitor.active_monitors
        assert 123 in state_monitor.state_history
        
        # 監視停止
        await state_monitor.stop_monitoring(123)
    
    @pytest.mark.asyncio
    async def test_state_change_detection(self, state_monitor):
        """状態変化検出のテスト"""
        # 前の状態: CI実行中
        previous = PRState(
            pr_number=123,
            timestamp=datetime.now(),
            mergeable=None,
            mergeable_state="unstable",
            draft=False,
            state="open"
        )
        
        # 現在の状態: マージ可能
        current = PRState(
            pr_number=123,
            timestamp=datetime.now(),
            mergeable=True,
            mergeable_state="clean",
            draft=False,
            state="open"
        )
        
        events = state_monitor._detect_state_changes(previous, current)
        
        # CI成功イベントが検出されることを確認
        event_types = [event[0] for event in events]
        assert StateChangeEvent.CI_PASSED in event_types
    
    def test_auto_stop_conditions(self, state_monitor):
        """自動停止条件のテスト"""
        config = MonitoringConfig(auto_stop_on_merge=True, auto_stop_on_close=True)
        
        # マージ状態
        merged_state = PRState(
            pr_number=123,
            timestamp=datetime.now(),
            mergeable=True,
            mergeable_state="clean",
            draft=False,
            state="merged"
        )
        
        assert state_monitor._should_auto_stop(merged_state, config) is True
        
        # クローズ状態
        closed_state = PRState(
            pr_number=123,
            timestamp=datetime.now(),
            mergeable=False,
            mergeable_state="unknown",
            draft=False,
            state="closed"
        )
        
        assert state_monitor._should_auto_stop(closed_state, config) is True


class TestSituationStrategyEngine:
    """状況別戦略エンジンのテスト"""
    
    @pytest.fixture
    def mock_pr_api_client(self):
        """モックPR APIクライアント"""
        client = Mock()
        client._get_pull_request = Mock()
        client._enable_auto_merge = Mock()
        return client
    
    @pytest.fixture
    def strategy_engine(self, mock_pr_api_client):
        """戦略エンジンインスタンス"""
        return SituationStrategyEngine(mock_pr_api_client)
    
    @pytest.mark.asyncio
    async def test_clean_state_strategy(self, strategy_engine, mock_pr_api_client):
        """クリーン状態での戦略テスト"""
        context = StrategyContext(
            pr_number=123,
            pr_title="Test PR",
            branch_name="feature/test",
            base_branch="main",
            mergeable_state="clean",
            mergeable=True,
            draft=False,
            ci_status="success",
            review_state="approved"
        )
        
        # マージ成功をモック
        mock_pr_api_client._enable_auto_merge.return_value = {
            "success": True,
            "merged": True
        }
        
        result = await strategy_engine.execute_strategy(context)
        
        assert result.result == StrategyResult.SUCCESS
        assert "マージが正常に完了" in result.message
    
    @pytest.mark.asyncio
    async def test_unstable_state_strategy(self, strategy_engine):
        """不安定状態での戦略テスト"""
        context = StrategyContext(
            pr_number=123,
            pr_title="Test PR",
            branch_name="feature/test",
            base_branch="main",
            mergeable_state="unstable",
            mergeable=None,
            draft=False,
            ci_status="pending",
            review_state=None
        )
        
        result = await strategy_engine.execute_strategy(context)
        
        # CI実行中なので後でリトライ
        assert result.result == StrategyResult.RETRY_LATER
        assert result.retry_after is not None
    
    @pytest.mark.asyncio
    async def test_dirty_state_strategy(self, strategy_engine):
        """コンフリクト状態での戦略テスト"""
        context = StrategyContext(
            pr_number=123,
            pr_title="Test PR",
            branch_name="feature/test",
            base_branch="main",
            mergeable_state="dirty",
            mergeable=False,
            draft=False,
            ci_status=None,
            review_state=None
        )
        
        result = await strategy_engine.execute_strategy(context)
        
        # コンフリクトは手動対応
        assert result.result == StrategyResult.MANUAL_REQUIRED
        assert "手動解決" in result.message
    
    @pytest.mark.asyncio
    async def test_unknown_state_handling(self, strategy_engine):
        """不明状態の処理テスト"""
        context = StrategyContext(
            pr_number=123,
            pr_title="Test PR",
            branch_name="feature/test",
            base_branch="main",
            mergeable_state="invalid_state",
            mergeable=None,
            draft=False,
            ci_status=None,
            review_state=None
        )
        
        result = await strategy_engine.execute_strategy(context)
        
        assert result.result == StrategyResult.NOT_APPLICABLE
        assert "Unknown mergeable state" in result.message


class TestProgressReporter:
    """進捗報告システムのテスト"""
    
    @pytest.fixture
    def mock_github_client(self):
        """モックGitHubクライアント"""
        client = Mock()
        client.repo = Mock()
        
        # イシューモック
        issue = Mock()
        comment = Mock()
        comment.id = 12345
        issue.create_comment.return_value = comment
        issue.get_comment.return_value = comment
        client.repo.get_issue.return_value = issue
        
        # PRモック
        pr = Mock()
        client.repo.get_pull.return_value = pr
        
        return client
    
    @pytest.fixture
    def progress_reporter(self, mock_github_client):
        """進捗報告インスタンス"""
        return ProgressReporter(mock_github_client)
    
    def test_start_session(self, progress_reporter):
        """セッション開始のテスト"""
        session_id = progress_reporter.start_session(
            pr_number=123,
            issue_number=456,
            initial_message="テスト開始"
        )
        
        assert session_id.startswith("pr_123_")
        assert 123 in progress_reporter.active_sessions
        
        session = progress_reporter.active_sessions[123]
        assert session.pr_number == 123
        assert session.issue_number == 456
        assert len(session.entries) == 1
        assert session.entries[0].message == "テスト開始"
    
    @pytest.mark.asyncio
    async def test_progress_update(self, progress_reporter, mock_github_client):
        """進捗更新のテスト"""
        # セッション開始
        progress_reporter.start_session(123, 456, "開始")
        
        # 進捗更新
        result = await progress_reporter.update_progress(
            123, "in_progress", "処理中...", {"step": "analysis"}
        )
        
        assert result is True
        session = progress_reporter.active_sessions[123]
        assert len(session.entries) == 2
        assert session.entries[-1].status == "in_progress"
        assert session.entries[-1].details["step"] == "analysis"
    
    def test_comment_body_generation(self, progress_reporter):
        """コメント本文生成のテスト"""
        # セッション作成
        progress_reporter.start_session(123, 456, "開始")
        session = progress_reporter.active_sessions[123]
        
        # 複数エントリ追加
        session.add_entry("in_progress", "分析中", {"progress": 50})
        session.add_entry("waiting", "CI待機中", {"ci_status": "pending"})
        
        comment_body = progress_reporter._generate_comment_body(session)
        
        assert "Auto Issue Processor - 進捗報告" in comment_body
        assert "CI待機中" in comment_body
        assert "処理履歴" in comment_body
        assert "セッション情報" in comment_body
        assert session.session_id in comment_body
    
    @pytest.mark.asyncio
    async def test_session_completion(self, progress_reporter, mock_github_client):
        """セッション完了のテスト"""
        # セッション開始
        progress_reporter.start_session(123, 456, "開始")
        
        # セッション完了
        result = await progress_reporter.complete_session(
            123, "completed", "完了しました", {"result": "success"}
        )
        
        assert result is True
        assert 123 not in progress_reporter.active_sessions
        assert len(progress_reporter.session_history) == 1
        
        completed_session = progress_reporter.session_history[0]
        assert completed_session.end_time is not None
        assert completed_session.current_status == "completed"


class TestEnhancedMergeSystem:
    """統合システム全体のテスト"""
    
    @pytest.fixture
    def mock_pr_api_client(self):
        """モックPR APIクライアント"""
        client = Mock()
        client.create_pull_request = Mock()
        client._get_pull_request = Mock()
        client._enable_auto_merge = Mock()
        return client
    
    @pytest.fixture
    def mock_github_client(self):
        """モックGitHubクライアント"""
        client = Mock()
        client.repo = Mock()
        return client
    
    @pytest.fixture
    def enhanced_system(self, mock_pr_api_client, mock_github_client):
        """拡張マージシステムインスタンス"""
        return EnhancedMergeSystem(mock_pr_api_client, mock_github_client)
    
    @pytest.mark.asyncio
    async def test_immediate_merge_flow(self, enhanced_system, mock_pr_api_client, mock_github_client):
        """即座マージフローのテスト"""
        # PR作成成功
        mock_pr_api_client.create_pull_request.return_value = {
            "success": True,
            "pull_request": {
                "number": 123,
                "title": "Test PR",
                "html_url": "https://github.com/test/repo/pull/123",
                "head": {"ref": "feature/test"},
                "base": {"ref": "main"}
            },
            "pr_url": "https://github.com/test/repo/pull/123"
        }
        
        # PR状態: 即座マージ可能
        mock_pr_api_client._get_pull_request.return_value = {
            "success": True,
            "pull_request": {
                "mergeable": True,
                "mergeable_state": "clean",
                "draft": False
            }
        }
        
        # マージ成功
        mock_pr_api_client._enable_auto_merge.return_value = {
            "success": True,
            "merged": True
        }
        
        # GitHubクライアントのモック設定
        mock_issue = Mock()
        mock_comment = Mock()
        mock_comment.id = 12345
        mock_issue.create_comment.return_value = mock_comment
        mock_github_client.repo.get_issue.return_value = mock_issue
        
        result = await enhanced_system.create_pr_with_smart_merge(
            title="Test PR",
            head="feature/test",
            base="main",
            issue_number=456
        )
        
        assert result["success"] is True
        assert result["smart_merge_result"]["success"] is True
        assert result["smart_merge_result"]["merge_type"] == "immediate"
    
    @pytest.mark.asyncio
    async def test_retry_required_flow(self, enhanced_system, mock_pr_api_client, mock_github_client):
        """リトライ必要フローのテスト"""
        # PR作成成功
        mock_pr_api_client.create_pull_request.return_value = {
            "success": True,
            "pull_request": {
                "number": 123,
                "title": "Test PR",
                "html_url": "https://github.com/test/repo/pull/123",
                "head": {"ref": "feature/test"},
                "base": {"ref": "main"}
            },
            "pr_url": "https://github.com/test/repo/pull/123"
        }
        
        # 初期状態: CI実行中
        # リトライ後: マージ可能
        pr_states = [
            {
                "success": True,
                "pull_request": {
                    "mergeable": None,
                    "mergeable_state": "unstable",
                    "draft": False
                }
            },
            {
                "success": True,
                "pull_request": {
                    "mergeable": True,
                    "mergeable_state": "clean",
                    "draft": False
                }
            }
        ]
        
        mock_pr_api_client._get_pull_request.side_effect = pr_states
        mock_pr_api_client._enable_auto_merge.return_value = {
            "success": True,
            "merged": True
        }
        
        # GitHubクライアントのモック設定
        mock_issue = Mock()
        mock_comment = Mock()
        mock_comment.id = 12345
        mock_issue.create_comment.return_value = mock_comment
        mock_github_client.repo.get_issue.return_value = mock_issue
        
        result = await enhanced_system.create_pr_with_smart_merge(
            title="Test PR",
            head="feature/test",
            base="main",
            issue_number=456
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_system_status(self, enhanced_system):
        """システム状況取得のテスト"""
        status = await enhanced_system.get_system_status()
        
        assert "active_monitors" in status
        assert "active_progress_sessions" in status
        assert "retry_statistics" in status
        assert "timestamp" in status
    
    @pytest.mark.asyncio
    async def test_processing_cancellation(self, enhanced_system, mock_github_client):
        """処理キャンセルのテスト"""
        # GitHubクライアントのモック設定
        mock_issue = Mock()
        mock_comment = Mock()
        mock_comment.id = 12345
        mock_issue.create_comment.return_value = mock_comment
        mock_github_client.repo.get_issue.return_value = mock_issue
        
        # 進捗セッション開始
        enhanced_system.progress_reporter.start_session(123, 456, "テスト")
        
        result = await enhanced_system.cancel_pr_processing(123)
        
        assert result is True
        assert 123 not in enhanced_system.progress_reporter.active_sessions


# テスト実行用のメイン関数
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])