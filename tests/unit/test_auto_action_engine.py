#!/usr/bin/env python3
"""
🎯 Auto Action Engine テスト
状態変化に応じた自動アクション実行のテスト
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os

# テスト対象のインポート
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from libs.integrations.github.pr_state_monitor import StateChangeEvent
from libs.integrations.github.auto_action_engine import AutoActionEngine, ActionType


class TestAutoActionEngine:
    """自動アクションエンジンのテスト"""
    
    @pytest.fixture
    def mock_pr_api_client(self):
        """モックAPIクライアント"""
        client = Mock()
        client.merge_pull_request = AsyncMock(return_value={
            "success": True,
            "sha": "abc123",
            "merged": True,
            "message": "Pull Request successfully merged"
        })
        client.get_pull_request = Mock(return_value={
            "success": True,
            "pull_request": {
                "number": 123,
                "title": "Test PR",
                "mergeable": True,
                "mergeable_state": "clean"
            }
        })
        return client
    
    @pytest.fixture
    def mock_conflict_resolver(self):
        """モックコンフリクトリゾルバー"""
        resolver = Mock()
        resolver.resolve_conflicts = AsyncMock(return_value={
            "success": True,
            "conflicts_resolved": 3,
            "files_updated": ["file1.0py", "file2.0py", "file3.0py"]
        })
        return resolver
    
    @pytest.fixture
    def engine(self, mock_pr_api_client, mock_conflict_resolver):
        """エンジンインスタンス"""
        engine = AutoActionEngine(mock_pr_api_client)
        engine.conflict_resolver = mock_conflict_resolver
        return engine
    
    @pytest.mark.asyncio
    async def test_handle_ci_passed(self, engine, mock_pr_api_client):
        """CI成功時の自動マージテスト"""
        # CI成功イベント
        event = StateChangeEvent.CI_PASSED
        event_data = {
            "previous_state": "unstable",
            "current_state": "clean"
        }
        
        # アクション実行
        result = await engine.handle_state_change(123, event, event_data)
        
        # マージが試行されたことを確認
        assert result["action_taken"] == "merge_attempt"
        assert result["success"] is True
        mock_pr_api_client.merge_pull_request.assert_called_once_with(123)
    
    @pytest.mark.asyncio
    async def test_handle_review_approved(self, engine, mock_pr_api_client):
        """レビュー承認時のマージ準備確認テスト"""
        # レビュー承認イベント
        event = StateChangeEvent.REVIEW_APPROVED
        event_data = {
            "reviewer": "reviewer1",
            "review_state": "approved"
        }
        
        # アクション実行
        result = await engine.handle_state_change(123, event, event_data)
        
        # マージ準備確認が実行されたことを確認
        assert result["action_taken"] == "check_merge_readiness"
        assert result["mergeable"] is True
        assert result["ready_to_merge"] is True
    
    @pytest.mark.asyncio
    async def test_handle_conflicts_detected(self, engine, mock_conflict_resolver):
        """コンフリクト検出時の自動解決テスト"""
        # コンフリクト検出イベント
        event = StateChangeEvent.CONFLICTS_DETECTED
        event_data = {
            "previous_state": "clean",
            "current_state": "dirty"
        }
        
        # アクション実行
        result = await engine.handle_state_change(456, event, event_data)
        
        # コンフリクト解決が試行されたことを確認
        assert result["action_taken"] == "conflict_resolution"
        assert result["success"] is True
        assert result["conflicts_resolved"] == 3
        mock_conflict_resolver.resolve_conflicts.assert_called_once_with(456)
    
    @pytest.mark.asyncio
    async def test_handle_ready_to_merge(self, engine, mock_pr_api_client):
        """マージ準備完了時の自動マージテスト"""
        # マージ準備完了イベント
        event = StateChangeEvent.READY_TO_MERGE
        event_data = {
            "mergeable_changed": True,
            "mergeable_state": "clean"
        }
        
        # アクション実行
        result = await engine.handle_state_change(789, event, event_data)
        
        # 自動マージが実行されたことを確認
        assert result["action_taken"] == "auto_merge"
        assert result["success"] is True
        mock_pr_api_client.merge_pull_request.assert_called_once_with(789)
    
    @pytest.mark.asyncio
    async def test_handle_merge_blocked(self, engine):
        """マージブロック時の処理テスト"""
        # マージブロックイベント
        event = StateChangeEvent.MERGE_BLOCKED
        event_data = {
            "mergeable_changed": True,
            "mergeable_state": "blocked",
            "reason": "required_status_checks"
        }
        
        # アクション実行
        result = await engine.handle_state_change(999, event, event_data)
        
        # ブロック理由の分析が実行されたことを確認
        assert result["action_taken"] == "analyze_block_reason"
        assert "block_reason" in result
        assert result["retry_available"] is True
    
    @pytest.mark.asyncio
    async def test_error_handling(self, engine, mock_pr_api_client):
        """エラー処理のテスト"""
        # マージエラーを設定
        mock_pr_api_client.merge_pull_request.side_effect = Exception("API Error")
        
        # CI成功イベント
        event = StateChangeEvent.CI_PASSED
        event_data = {"current_state": "clean"}
        
        # アクション実行
        result = await engine.handle_state_change(111, event, event_data)
        
        # エラーがキャッチされたことを確認
        assert result["success"] is False
        assert "error" in result
        assert "API Error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_action_cooldown(self, engine):
        """アクションクールダウンのテスト"""
        # 同じPRに対する連続アクションをテスト
        event = StateChangeEvent.CI_PASSED
        event_data = {"current_state": "clean"}
        
        # 1回目のアクション
        result1 = await engine.handle_state_change(222, event, event_data)
        assert result1["success"] is True
        
        # 即座に2回目のアクション（クールダウン中）
        result2 = await engine.handle_state_change(222, event, event_data)
        assert result2["action_taken"] == "skipped_cooldown"
        assert result2["cooldown_remaining"] > 0
    
    def test_get_action_history(self, engine):
        """アクション履歴取得のテスト"""
        # 初期状態では空
        history = engine.get_action_history(333)
        assert len(history) == 0
        
        # アクション履歴がある場合のテストは実装後に追加