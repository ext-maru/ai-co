#!/usr/bin/env python3
"""
💬 Progress Reporter テスト
リアルタイム進捗報告システムのテスト
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os

# テスト対象のインポート
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from libs.integrations.github.pr_state_monitor import StateChangeEvent
from libs.integrations.github.progress_reporter import ProgressReporter


class TestProgressReporter:
    """進捗報告システムのテスト"""
    
    @pytest.fixture
    def mock_github_client(self):
        """モックGitHubクライアント"""
        client = Mock()
        
        # GitHub API オブジェクトのモック
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
    def reporter(self, mock_github_client):
        """レポーターインスタンス"""
        return ProgressReporter(mock_github_client)
    
    @pytest.mark.asyncio
    async def test_start_session(self, reporter, mock_github_client):
        """セッション開始のテスト"""
        # セッションを開始
        session_id = reporter.start_session(
            pr_number=123,
            issue_number=147,
            initial_message="マージ状態の継続的監視システム構築"
        )
        
        assert session_id is not None
        assert session_id.startswith("pr_123_")
        
        # セッション状況を確認
        status = reporter.get_session_status(123)
        assert status is not None
        assert status["pr_number"] == 123
        assert status["issue_number"] == 147
    
    @pytest.mark.asyncio
    async def test_update_progress(self, reporter, mock_github_client):
        """進捗更新のテスト"""
        # セッションを開始
        reporter.start_session(123, 147, "Test PR")
        
        # 進捗を更新
        result = await reporter.update_progress(
            pr_number=123,
            status="in_progress",
            message="CI実行中",
            details={
                "ci_jobs_completed": 5,
                "ci_jobs_total": 8,
                "elapsed_time": "5分12秒"
            },
            force_comment_update=True
        )
        
        assert result is True
        
        # セッション状況を確認
        status = reporter.get_session_status(123)
        assert status["current_status"] == "in_progress"
    
    @pytest.mark.asyncio
    async def test_session_entry_addition(self, reporter):
        """セッションエントリ追加のテスト"""
        # セッションを開始
        reporter.start_session(123, 147, "Test PR")
        
        # 進捗を追加
        await reporter.update_progress(
            pr_number=123,
            status="in_progress",
            message="CI実行開始",
            details={"ci_status": "running"}
        )
        
        # セッション状況を確認
        status = reporter.get_session_status(123)
        assert len(status["entries"]) >= 2  # 初期エントリ + 新エントリ
        assert any(entry["message"] == "CI実行開始" for entry in status["entries"])
    
    @pytest.mark.asyncio
    async def test_complete_session(self, reporter, mock_github_client):
        """セッション完了のテスト"""
        # セッションを開始
        reporter.start_session(123, 147, "Test PR")
        
        # セッションを完了
        result = await reporter.complete_session(
            pr_number=123,
            final_status="completed",
            final_message="マージ完了",
            final_details={
                "merge_sha": "abc123",
                "total_duration": "15分30秒"
            }
        )
        
        assert result is True
        
        # セッションが非アクティブになったことを確認
        status = reporter.get_session_status(123)
        assert status is None
    
    @pytest.mark.asyncio
    async def test_error_reporting(self, reporter, mock_github_client):
        """エラー報告のテスト"""
        # セッションを開始
        reporter.start_session(123, 147, "Test PR")
        
        # エラーを報告
        result = await reporter.update_progress(
            pr_number=123,
            status="error",
            message="マージコンフリクトが発生しました",
            details={
                "error_type": "MergeConflict",
                "suggested_action": "手動でコンフリクトを解決してください"
            },
            force_comment_update=True
        )
        
        assert result is True
        
        # セッション状況を確認
        status = reporter.get_session_status(123)
        assert status["current_status"] == "error"
    
    @pytest.mark.asyncio
    async def test_comment_body_generation(self, reporter):
        """コメント本文生成のテスト"""
        # セッションを開始
        reporter.start_session(123, 147, "Test PR")
        
        # いくつかの進捗を追加
        await reporter.update_progress(123, "in_progress", "CI実行中", {"ci_status": "running"})
        await reporter.update_progress(123, "waiting", "レビュー待ち", {"reviewers": 2})
        
        # セッション取得
        session = reporter.active_sessions[123]
        
        # コメント本文を生成
        formatted = reporter._generate_comment_body(session)
        
        # フォーマットを確認
        assert "🤖 **Auto Issue Processor - 進捗報告**" in formatted
        assert "レビュー待ち" in formatted
        assert "処理履歴" in formatted
        assert "セッション情報" in formatted
        assert "PR: #123" in formatted
    
    def test_session_status_retrieval(self, reporter):
        """セッション状況取得のテスト"""
        # セッションを開始
        session_id = reporter.start_session(123, 147, "Test PR")
        
        # セッション状況を取得
        status = reporter.get_session_status(123)
        
        # セッション情報を確認
        assert status is not None
        assert status["pr_number"] == 123
        assert status["issue_number"] == 147
        assert status["session_id"] == session_id
        assert "start_time" in status
        assert "entries" in status
    
    def test_session_history_management(self, reporter):
        """セッション履歴管理のテスト"""
        # 複数セッションを作成・完了
        reporter.start_session(123, 147, "Test PR 1")
        reporter.start_session(456, 148, "Test PR 2")
        
        # アクティブセッション確認
        active = reporter.get_all_active_sessions()
        assert len(active) == 2
        assert 123 in active
        assert 456 in active
        
        # 一つを完了
        asyncio.run(reporter.complete_session(123, "completed", "完了"))
        
        # アクティブセッションが減っていることを確認
        active = reporter.get_all_active_sessions()
        assert len(active) == 1
        assert 456 in active
        assert 123 not in active