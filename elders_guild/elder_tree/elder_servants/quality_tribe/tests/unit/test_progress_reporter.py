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
from elders_guild.elder_tree.integrations.github.pr_state_monitor import StateChangeEvent
from elders_guild.elder_tree.integrations.github.progress_reporter import ProgressReporter


class TestProgressReporter:
    """進捗報告システムのテスト"""
    
    @pytest.fixture
    def mock_github_client(self):
        """モックGitHubクライアント"""
        client = Mock()
        client.create_issue_comment = AsyncMock(return_value={
            "success": True,
            "comment_id": 12345,
            "html_url": "https://github.com/owner/repo/issues/147#issuecomment-12345"
        })
        client.update_issue_comment = AsyncMock(return_value={
            "success": True,
            "comment_id": 12345
        })
        return client
    
    @pytest.fixture
    def reporter(self, mock_github_client):
        """レポーターインスタンス"""
        return ProgressReporter(mock_github_client)
    
    @pytest.mark.asyncio
    async def test_create_initial_report(self, reporter, mock_github_client):
        """初期レポート作成のテスト"""
        # 初期レポートを作成
        result = await reporter.create_initial_report(
            pr_number=123,
            issue_number=147,
            title="マージ状態の継続的監視システム構築"
        )
        
        assert result["success"] is True
        assert "comment_id" in result
        
        # コメント作成が呼ばれたことを確認
        mock_github_client.create_issue_comment.assert_called_once()
        args = mock_github_client.create_issue_comment.call_args
        assert args[0][0] == 147  # issue_number
        assert "Auto Issue Processor - 進捗報告" in args[0][1]
        assert "監視開始" in args[0][1]
    
    @pytest.mark.asyncio
    async def test_update_progress(self, reporter, mock_github_client):
        """進捗更新のテスト"""
        # 初期レポートを作成
        await reporter.create_initial_report(123, 147, "Test PR")
        
        # 進捗を更新
        result = await reporter.update_progress(
            issue_number=147,
            state="CI実行中",
            emoji="⏳",
            details={
                "ci_jobs_completed": 5,
                "ci_jobs_total": 8,
                "elapsed_time": "5分12秒"
            }
        )
        
        assert result["success"] is True
        
        # コメント更新が呼ばれたことを確認
        mock_github_client.update_issue_comment.assert_called()
        args = mock_github_client.update_issue_comment.call_args
        assert "CI実行中" in args[0][1]
        assert "5/8 jobs完了" in args[0][1]
    
    @pytest.mark.asyncio
    async def test_add_event_to_history(self, reporter):
        """イベント履歴追加のテスト"""
        # 初期レポートを作成
        await reporter.create_initial_report(123, 147, "Test PR")
        
        # イベントを追加
        reporter.add_event_to_history(
            issue_number=147,
            event_type=StateChangeEvent.CI_STARTED,
            description="CI実行開始",
            emoji="⏳"
        )
        
        # 履歴に追加されたことを確認
        history = reporter.get_event_history(147)
        assert len(history) > 0
        assert history[-1]["description"] == "CI実行開始"
        assert history[-1]["emoji"] == "⏳"
    
    @pytest.mark.asyncio
    async def test_complete_monitoring(self, reporter, mock_github_client):
        """監視完了報告のテスト"""
        # 初期レポートを作成
        await reporter.create_initial_report(123, 147, "Test PR")
        
        # 監視を完了
        result = await reporter.complete_monitoring(
            issue_number=147,
            success=True,
            final_state="マージ完了",
            details={
                "merge_sha": "abc123",
                "total_duration": "15分30秒"
            }
        )
        
        assert result["success"] is True
        
        # 最終更新が呼ばれたことを確認
        mock_github_client.update_issue_comment.assert_called()
        args = mock_github_client.update_issue_comment.call_args
        assert "✅ 完了" in args[0][1]
        assert "マージ完了" in args[0][1]
        assert "15分30秒" in args[0][1]
    
    @pytest.mark.asyncio
    async def test_error_reporting(self, reporter, mock_github_client):
        """エラー報告のテスト"""
        # 初期レポートを作成
        await reporter.create_initial_report(123, 147, "Test PR")
        
        # エラーを報告
        result = await reporter.report_error(
            issue_number=147,
            error_type="MergeConflict",
            error_message="マージコンフリクトが発生しました",
            suggested_action="手動でコンフリクトを解決してください"
        )
        
        assert result["success"] is True
        
        # エラー報告が更新されたことを確認
        mock_github_client.update_issue_comment.assert_called()
        args = mock_github_client.update_issue_comment.call_args
        assert "❌ エラー" in args[0][1]
        assert "マージコンフリクトが発生しました" in args[0][1]
        assert "手動でコンフリクトを解決してください" in args[0][1]
    
    @pytest.mark.asyncio
    async def test_format_progress_report(self, reporter):
        """進捗レポートフォーマットのテスト"""
        # 初期データを設定
        reporter._reports[147] = {
            "pr_number": 123,
            "title": "Test PR",
            "start_time": datetime.now() - timedelta(minutes=10),
            "current_state": "CI実行中",
            "current_emoji": "⏳",
            "history": [
                {
                    "timestamp": datetime.now() - timedelta(minutes=10),
                    "emoji": "✅",
                    "description": "PR作成完了 (#123)"
                },
                {
                    "timestamp": datetime.now() - timedelta(minutes=5),
                    "emoji": "⏳",
                    "description": "CI実行開始"
                }
            ]
        }
        
        # レポートをフォーマット
        formatted = reporter._format_progress_report(147)
        
        # フォーマットを確認
        assert "🤖 **Auto Issue Processor - 進捗報告**" in formatted
        assert "**現在の状態**: CI実行中 ⏳" in formatted
        assert "✅" in formatted
        assert "PR作成完了 (#123)" in formatted
        assert "⏳" in formatted
        assert "CI実行開始" in formatted
        assert "経過時間" in formatted
        assert "最終更新" in formatted
    
    def test_calculate_eta(self, reporter):
        """完了予想時刻計算のテスト"""
        # 開始時刻と現在の進捗から予想時刻を計算
        start_time = datetime.now() - timedelta(minutes=5)
        progress = 0.6  # 60%完了
        
        eta = reporter._calculate_eta(start_time, progress)
        
        # 予想時刻が妥当な範囲にあることを確認
        assert eta > datetime.now()
        assert eta < datetime.now() + timedelta(minutes=10)
    
    def test_format_duration(self, reporter):
        """時間フォーマットのテスト"""
        # 秒数を人間が読みやすい形式に変換
        assert reporter._format_duration(65) == "1分5秒"
        assert reporter._format_duration(3661) == "1時間1分1秒"
        assert reporter._format_duration(30) == "30秒"
        assert reporter._format_duration(7200) == "2時間0分0秒"