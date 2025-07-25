#!/usr/bin/env python3
"""
👀 PR State Monitor テスト
継続的監視システムのユニットテスト
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os

# テスト対象のインポート
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from elders_guild.elder_tree.integrations.github.pr_state_monitor import (
    PRStateMonitor, PRState, StateChangeEvent, MonitoringConfig
)


class TestPRStateMonitor:
    """PR状態監視システムのテスト"""
    
    @pytest.fixture
    def mock_pr_api_client(self):
        """モックAPIクライアント"""
        client = Mock()
        client._get_pull_request = Mock(return_value={
            "success": True,
            "pull_request": {
                "number": 123,
                "mergeable": True,
                "mergeable_state": "clean",
                "draft": False,
                "state": "open",
                "behind_by": 0,
                "ahead_by": 3
            }
        })
        return client
    
    @pytest.fixture
    def monitor(self, mock_pr_api_client):
        """監視システムインスタンス"""
        return PRStateMonitor(mock_pr_api_client)
    
    @pytest.mark.asyncio
    async def test_start_monitoring(self, monitor):
        """監視開始のテスト"""
        # 監視を開始
        result = await monitor.start_monitoring(123)
        assert result is True
        assert 123 in monitor.active_monitors
        assert 123 in monitor.monitoring_configs
        assert 123 in monitor.state_history
        
        # クリーンアップ
        await monitor.stop_monitoring(123)
    
    @pytest.mark.asyncio
    async def test_duplicate_monitoring(self, monitor):
        """重複監視の防止テスト"""
        # 最初の監視開始
        await monitor.start_monitoring(123)
        
        # 重複監視の試み
        result = await monitor.start_monitoring(123)
        assert result is False
        
        # クリーンアップ
        await monitor.stop_monitoring(123)
    
    @pytest.mark.asyncio
    async def test_stop_monitoring(self, monitor):
        """監視停止のテスト"""
        # 監視を開始
        await monitor.start_monitoring(123)
        
        # 監視を停止
        result = await monitor.stop_monitoring(123)
        assert result is True
        assert 123 not in monitor.active_monitors
    
    @pytest.mark.asyncio
    async def test_state_change_detection_ci_passed(self, monitor, mock_pr_api_client):
        """CI成功の検出テスト"""
        # 初期状態: CI実行中
        mock_pr_api_client._get_pull_request.return_value = {
            "success": True,
            "pull_request": {
                "number": 123,
                "mergeable": None,
                "mergeable_state": "unstable",
                "draft": False,
                "state": "open",
                "behind_by": 0,
                "ahead_by": 3
            }
        }
        
        # イベントコールバックを設定
        events_received = []
        async def event_callback(pr_number, event_type, event_data):
            events_received.append((event_type, event_data))
        
        config = MonitoringConfig(
            polling_interval=0.1,  # 100ms
            max_monitoring_duration=2,  # 2秒
            event_callbacks={
                StateChangeEvent.CI_PASSED: [event_callback]
            }
        )
        
        await monitor.start_monitoring(123, config)
        await asyncio.sleep(0.2)  # 初期状態を記録
        
        # 状態を変更: CI成功
        mock_pr_api_client._get_pull_request.return_value = {
            "success": True,
            "pull_request": {
                "number": 123,
                "mergeable": True,
                "mergeable_state": "clean",
                "draft": False,
                "state": "open",
                "behind_by": 0,
                "ahead_by": 3
            }
        }
        
        # イベントが発火するまで待機
        await asyncio.sleep(0.3)
        
        # CI_PASSEDイベントが発火されたことを確認
        assert len(events_received) > 0
        assert events_received[0][0] == StateChangeEvent.CI_PASSED
        
        # クリーンアップ
        await monitor.stop_monitoring(123)
    
    @pytest.mark.asyncio
    async def test_conflict_detection(self, monitor, mock_pr_api_client):
        """コンフリクト検出のテスト"""
        # 初期状態: クリーン
        mock_pr_api_client._get_pull_request.return_value = {
            "success": True,
            "pull_request": {
                "number": 456,
                "mergeable": True,
                "mergeable_state": "clean",
                "draft": False,
                "state": "open",
                "behind_by": 0,
                "ahead_by": 2
            }
        }
        
        events_received = []
        async def event_callback(pr_number, event_type, event_data):
            events_received.append((event_type, event_data))
        
        config = MonitoringConfig(
            polling_interval=0.1,
            max_monitoring_duration=2,
            event_callbacks={
                StateChangeEvent.CONFLICTS_DETECTED: [event_callback]
            }
        )
        
        await monitor.start_monitoring(456, config)
        await asyncio.sleep(0.2)
        
        # コンフリクト発生
        mock_pr_api_client._get_pull_request.return_value = {
            "success": True,
            "pull_request": {
                "number": 456,
                "mergeable": False,
                "mergeable_state": "dirty",
                "draft": False,
                "state": "open",
                "behind_by": 0,
                "ahead_by": 2
            }
        }
        
        await asyncio.sleep(0.3)
        
        # CONFLICTS_DETECTEDイベントが発火されたことを確認
        assert len(events_received) > 0
        assert events_received[0][0] == StateChangeEvent.CONFLICTS_DETECTED
        
        await monitor.stop_monitoring(456)
    
    @pytest.mark.asyncio
    async def test_auto_stop_on_merge(self, monitor, mock_pr_api_client):
        """マージ時の自動停止テスト"""
        # 初期状態: オープン
        mock_pr_api_client._get_pull_request.return_value = {
            "success": True,
            "pull_request": {
                "number": 789,
                "mergeable": True,
                "mergeable_state": "clean",
                "draft": False,
                "state": "open",
                "behind_by": 0,
                "ahead_by": 1
            }
        }
        
        config = MonitoringConfig(
            polling_interval=0.1,
            auto_stop_on_merge=True
        )
        
        await monitor.start_monitoring(789, config)
        await asyncio.sleep(0.2)
        
        # PRがマージされた
        mock_pr_api_client._get_pull_request.return_value = {
            "success": True,
            "pull_request": {
                "number": 789,
                "mergeable": None,
                "mergeable_state": "unknown",
                "draft": False,
                "state": "merged",
                "behind_by": 0,
                "ahead_by": 0
            }
        }
        
        await asyncio.sleep(0.3)
        
        # 自動的に監視が停止されたことを確認
        assert 789 not in monitor.active_monitors
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, monitor):
        """タイムアウト処理のテスト"""
        config = MonitoringConfig(
            polling_interval=0.1,
            max_monitoring_duration=0.5  # 0.5秒でタイムアウト
        )
        
        await monitor.start_monitoring(999, config)
        
        # タイムアウトまで待機
        await asyncio.sleep(0.7)
        
        # タイムアウトで監視が停止されたことを確認
        assert 999 not in monitor.active_monitors
    
    def test_pr_state_to_dict(self):
        """PRState.to_dict()のテスト"""
        state = PRState(
            pr_number=123,
            timestamp=datetime.now(),
            mergeable=True,
            mergeable_state="clean",
            draft=False,
            state="open",
            ci_status="success",
            review_state="approved",
            behind_by=0,
            ahead_by=3
        )
        
        state_dict = state.to_dict()
        assert state_dict["pr_number"] == 123
        assert state_dict["mergeable"] is True
        assert state_dict["mergeable_state"] == "clean"
        assert state_dict["ci_status"] == "success"
        assert state_dict["review_state"] == "approved"
    
    def test_monitoring_status(self, monitor):
        """監視状況の取得テスト"""
        status = monitor.get_monitoring_status()
        assert "active_monitors" in status
        assert "total_monitored" in status
        assert "monitoring_count" in status
        assert status["monitoring_count"] == 0