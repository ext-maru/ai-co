#!/usr/bin/env python3
"""
Tests for PR State Monitor
Issue #145: Test coverage for PR state monitoring system
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from libs.integrations.github.pr_state_monitor import (
    PRStateMonitor,
    MonitoringState,
    StateTransition,
    PRSnapshot,
    MonitoringSession
)


class TestPRSnapshot:
    """Test PRSnapshot dataclass"""
    
    def test_pr_snapshot_creation(self):
        """Test PRSnapshot creation"""
        snapshot = PRSnapshot(
            timestamp=1234567890.0,
            state="open",
            mergeable=True,
            mergeable_state="clean",
            checks_status="success",
            review_status={"approved": 2, "changes_requested": 0},
            behind_by=0,
            head_sha="abc123"
        )
        
        assert snapshot.timestamp == 1234567890.0
        assert snapshot.state == "open"
        assert snapshot.mergeable is True
        assert snapshot.mergeable_state == "clean"
        assert snapshot.checks_status == "success"
        assert snapshot.review_status["approved"] == 2
    
    def test_pr_snapshot_to_dict(self):
        """Test PRSnapshot to_dict method"""
        snapshot = PRSnapshot(
            timestamp=1234567890.0,
            state="open",
            mergeable=True,
            mergeable_state="clean"
        )
        
        result = snapshot.to_dict()
        assert isinstance(result, dict)
        assert result["timestamp"] == 1234567890.0
        assert result["state"] == "open"
        assert result["mergeable"] is True
        assert result["mergeable_state"] == "clean"


class TestMonitoringSession:
    """Test MonitoringSession dataclass"""
    
    def test_monitoring_session_creation(self):
        """Test MonitoringSession creation"""
        session = MonitoringSession(pr_number=123)
        
        assert session.pr_number == 123
        assert session.state == MonitoringState.ACTIVE
        assert session.snapshots == []
        assert session.state_transitions == []
        assert session.merge_opportunities == []
        assert session.final_status is None
    
    def test_monitoring_session_with_data(self):
        """Test MonitoringSession with data"""
        session = MonitoringSession(pr_number=456)
        
        # Add snapshot
        snapshot = PRSnapshot(
            timestamp=1234567890.0,
            state="open",
            mergeable=True,
            mergeable_state="clean"
        )
        session.snapshots.append(snapshot)
        
        # Add state transition
        session.state_transitions.append(("unstable", "clean", 1234567900.0))
        
        # Add merge opportunity
        session.merge_opportunities.append(1234567910.0)
        
        assert len(session.snapshots) == 1
        assert len(session.state_transitions) == 1
        assert len(session.merge_opportunities) == 1


class TestPRStateMonitor:
    """Test PRStateMonitor functionality"""
    
    @pytest.fixture
    def mock_github_client(self):
        """Create mock GitHub client"""
        client = Mock()
        client.pulls = Mock()
        client.pulls.get = AsyncMock()
        client.checks = Mock()
        client.checks.list_for_ref = AsyncMock()
        client.pulls.list_reviews = AsyncMock()
        client.repos = Mock()
        client.repos.compare = AsyncMock()
        client.issues = Mock()
        client.issues.create_comment = AsyncMock()
        return client
    
    @pytest.fixture
    def monitor(self, mock_github_client):
        """Create PRStateMonitor instance"""
        return PRStateMonitor(mock_github_client)
    
    def test_initialization(self, monitor):
        """Test monitor initialization"""
        assert monitor.polling_interval == 30.0
        assert len(monitor.monitoring_sessions) == 0
        assert len(monitor.active_monitors) == 0
        assert len(monitor.callbacks) == 4
    
    def test_register_callback(self, monitor):
        """Test callback registration"""
        def test_callback(pr_number):
            pass
        
        monitor.register_callback("merge_ready", test_callback)
        
        assert test_callback in monitor.callbacks["merge_ready"]
    
    @pytest.mark.asyncio
    async def test_get_pr_snapshot_success(self, monitor, mock_github_client):
        """Test successful PR snapshot retrieval"""
        # Mock PR data
        mock_github_client.pulls.get.return_value = {
            "state": "open",
            "mergeable": True,
            "mergeable_state": "clean",
            "merged": False,
            "head": {"sha": "abc123"},
            "base": {"sha": "def456"},
            "draft": False
        }
        
        # Mock checks data
        mock_github_client.checks.list_for_ref.return_value = {
            "check_runs": [
                {"conclusion": "success"},
                {"conclusion": "success"}
            ]
        }
        
        # Mock reviews data
        mock_github_client.pulls.list_reviews.return_value = [
            {"state": "APPROVED"},
            {"state": "APPROVED"}
        ]
        
        # Mock comparison data
        mock_github_client.repos.compare.return_value = {
            "behind_by": 0,
            "ahead_by": 3
        }
        
        snapshot = await monitor._get_pr_snapshot("owner", "repo", 123)
        
        assert snapshot.state == "open"
        assert snapshot.mergeable is True
        assert snapshot.mergeable_state == "clean"
        assert snapshot.checks_status == "success"
        assert snapshot.review_status["approved"] == 2
        assert snapshot.behind_by == 0
        assert snapshot.head_sha == "abc123"
    
    @pytest.mark.asyncio
    async def test_get_pr_snapshot_error(self, monitor, mock_github_client):
        """Test PR snapshot retrieval with error"""
        mock_github_client.pulls.get.side_effect = Exception("API Error")
        
        snapshot = await monitor._get_pr_snapshot("owner", "repo", 123)
        
        assert snapshot.state == "error"
        assert snapshot.mergeable is None
        assert snapshot.mergeable_state == "unknown"
    
    def test_detect_state_transition_no_change(self, monitor):
        """Test state transition detection with no change"""
        prev = PRSnapshot(
            timestamp=1234567890.0,
            state="open",
            mergeable=True,
            mergeable_state="clean"
        )
        curr = PRSnapshot(
            timestamp=1234567900.0,
            state="open",
            mergeable=True,
            mergeable_state="clean"
        )
        
        transition = monitor._detect_state_transition(prev, curr)
        assert transition == StateTransition.NO_CHANGE
    
    def test_detect_state_transition_improved(self, monitor):
        """Test state transition detection - improved"""
        prev = PRSnapshot(
            timestamp=1234567890.0,
            state="open",
            mergeable=False,
            mergeable_state="unstable"
        )
        curr = PRSnapshot(
            timestamp=1234567900.0,
            state="open",
            mergeable=True,
            mergeable_state="clean"
        )
        
        transition = monitor._detect_state_transition(prev, curr)
        assert transition == StateTransition.IMPROVED
    
    def test_detect_state_transition_degraded(self, monitor):
        """Test state transition detection - degraded"""
        prev = PRSnapshot(
            timestamp=1234567890.0,
            state="open",
            mergeable=True,
            mergeable_state="clean"
        )
        curr = PRSnapshot(
            timestamp=1234567900.0,
            state="open",
            mergeable=False,
            mergeable_state="blocked"
        )
        
        transition = monitor._detect_state_transition(prev, curr)
        assert transition == StateTransition.DEGRADED
    
    def test_detect_state_transition_critical(self, monitor):
        """Test state transition detection - critical"""
        prev = PRSnapshot(
            timestamp=1234567890.0,
            state="open",
            mergeable=True,
            mergeable_state="clean"
        )
        curr = PRSnapshot(
            timestamp=1234567900.0,
            state="open",
            mergeable=False,
            mergeable_state="dirty"
        )
        
        transition = monitor._detect_state_transition(prev, curr)
        assert transition == StateTransition.CRITICAL
    
    @pytest.mark.asyncio
    async def test_fire_callbacks(self, monitor):
        """Test callback firing"""
        callback_called = False
        callback_args = None
        
        def test_callback(*args, **kwargs):
            nonlocal callback_called, callback_args
            callback_called = True
            callback_args = (args, kwargs)
        
        monitor.callbacks["merge_ready"].append(test_callback)
        
        await monitor._fire_callbacks("merge_ready", pr_number=123)
        
        assert callback_called is True
        assert callback_args[1]["pr_number"] == 123
    
    @pytest.mark.asyncio
    async def test_fire_callbacks_async(self, monitor):
        """Test async callback firing"""
        callback_called = False
        
        async def async_callback(*args, **kwargs):
            nonlocal callback_called
            callback_called = True
        
        monitor.callbacks["merge_ready"].append(async_callback)
        
        await monitor._fire_callbacks("merge_ready", pr_number=123)
        
        assert callback_called is True
    
    @pytest.mark.asyncio
    async def test_fire_callbacks_error_handling(self, monitor):
        """Test callback error handling"""
        def error_callback(*args, **kwargs):
            raise Exception("Callback error")
        
        def good_callback(*args, **kwargs):
            pass
        
        monitor.callbacks["merge_ready"].append(error_callback)
        monitor.callbacks["merge_ready"].append(good_callback)
        
        # Should not raise exception
        await monitor._fire_callbacks("merge_ready", pr_number=123)
    
    @pytest.mark.asyncio
    async def test_start_monitoring(self, monitor, mock_github_client):
        """Test starting PR monitoring"""
        # Mock initial PR state
        mock_github_client.pulls.get.return_value = {
            "state": "open",
            "mergeable": False,
            "mergeable_state": "unstable",
            "head": {"sha": "abc123"},
            "base": {"sha": "def456"}
        }
        mock_github_client.checks.list_for_ref.return_value = {"check_runs": []}
        mock_github_client.pulls.list_reviews.return_value = []
        mock_github_client.repos.compare.return_value = {"behind_by": 0}
        
        session = await monitor.start_monitoring("owner", "repo", 123)
        
        assert session.pr_number == 123
        assert session.state == MonitoringState.ACTIVE
        assert 123 in monitor.active_monitors
        assert 123 in monitor.monitoring_sessions
    
    @pytest.mark.asyncio
    async def test_start_monitoring_already_active(self, monitor, mock_github_client):
        """Test starting monitoring for already monitored PR"""
        # Start first monitoring
        await monitor.start_monitoring("owner", "repo", 123)
        
        # Try to start again
        session = await monitor.start_monitoring("owner", "repo", 123)
        
        assert session.pr_number == 123
        assert len(monitor.active_monitors) == 1
    
    @pytest.mark.asyncio
    async def test_stop_monitoring(self, monitor, mock_github_client):
        """Test stopping PR monitoring"""
        # Start monitoring first
        mock_github_client.pulls.get.return_value = {"state": "open", "mergeable_state": "unstable"}
        mock_github_client.checks.list_for_ref.return_value = {"check_runs": []}
        mock_github_client.pulls.list_reviews.return_value = []
        mock_github_client.repos.compare.return_value = {"behind_by": 0}
        
        await monitor.start_monitoring("owner", "repo", 123)
        
        # Stop monitoring
        await monitor.stop_monitoring(123)
        
        assert 123 not in monitor.active_monitors
        assert monitor.monitoring_sessions[123].state == MonitoringState.STOPPED
    
    @pytest.mark.asyncio
    async def test_pause_resume_monitoring(self, monitor):
        """Test pausing and resuming monitoring"""
        # Create session
        session = MonitoringSession(pr_number=123)
        monitor.monitoring_sessions[123] = session
        
        # Pause
        await monitor.pause_monitoring(123)
        assert session.state == MonitoringState.PAUSED
        
        # Resume
        await monitor.resume_monitoring(123)
        assert session.state == MonitoringState.ACTIVE
    
    def test_get_session_stats_no_session(self, monitor):
        """Test getting stats for non-existent session"""
        stats = monitor.get_session_stats(999)
        assert stats is None
    
    def test_get_session_stats_empty_session(self, monitor):
        """Test getting stats for empty session"""
        session = MonitoringSession(pr_number=123)
        monitor.monitoring_sessions[123] = session
        
        stats = monitor.get_session_stats(123)
        assert stats is None
    
    def test_get_session_stats_with_data(self, monitor):
        """Test getting stats for session with data"""
        session = MonitoringSession(pr_number=123)
        session.start_time = 1234567890.0
        session.end_time = 1234568490.0  # 10 minutes later
        
        # Add snapshots
        session.snapshots.append(PRSnapshot(
            timestamp=1234567890.0,
            state="open",
            mergeable=False,
            mergeable_state="unstable"
        ))
        session.snapshots.append(PRSnapshot(
            timestamp=1234568190.0,  # 5 minutes later
            state="open",
            mergeable=True,
            mergeable_state="clean"
        ))
        
        # Add state transition
        session.state_transitions.append(("unstable", "clean", 1234568190.0))
        
        # Add merge opportunity
        session.merge_opportunities.append(1234568190.0)
        
        monitor.monitoring_sessions[123] = session
        
        stats = monitor.get_session_stats(123)
        
        assert stats["pr_number"] == 123
        assert stats["duration"] == 600.0  # 10 minutes
        assert stats["snapshots_count"] == 2
        assert stats["state_transitions"] == 1
        assert stats["merge_opportunities"] == 1
        assert stats["current_state"] == "clean"
        assert "unstable" in stats["state_durations"]
    
    @pytest.mark.asyncio
    async def test_get_all_active_monitors(self, monitor):
        """Test getting all active monitors"""
        # Create multiple sessions
        for pr_num in [123, 456, 789]:
            session = MonitoringSession(pr_number=pr_num)
            session.snapshots.append(PRSnapshot(
                timestamp=1234567890.0,
                state="open",
                mergeable=False,
                mergeable_state="unstable"
            ))
            monitor.monitoring_sessions[pr_num] = session
        
        # Mark 789 as stopped
        monitor.monitoring_sessions[789].state = MonitoringState.STOPPED
        
        active = await monitor.get_all_active_monitors()
        
        assert len(active) == 2
        pr_numbers = [s["pr_number"] for s in active]
        assert 123 in pr_numbers
        assert 456 in pr_numbers
        assert 789 not in pr_numbers
    
    @pytest.mark.asyncio
    async def test_cleanup_old_sessions(self, monitor):
        """Test cleaning up old sessions"""
        current_time = 1234567890.0
        
        # Create old sessions
        for i, age_hours in enumerate([1, 12, 25, 48]):
            session = MonitoringSession(pr_number=100 + i)
            session.state = MonitoringState.STOPPED
            session.end_time = current_time - (age_hours * 3600)
            monitor.monitoring_sessions[100 + i] = session
        
        # Create active session
        active_session = MonitoringSession(pr_number=200)
        active_session.state = MonitoringState.ACTIVE
        monitor.monitoring_sessions[200] = active_session
        
        with patch('time.time', return_value=current_time):
            cleaned = await monitor.cleanup_old_sessions(max_age_hours=24)
        
        assert cleaned == 2  # Sessions aged 25 and 48 hours
        assert 100 in monitor.monitoring_sessions  # 1 hour old
        assert 101 in monitor.monitoring_sessions  # 12 hours old
        assert 102 not in monitor.monitoring_sessions  # 25 hours old - cleaned
        assert 103 not in monitor.monitoring_sessions  # 48 hours old - cleaned
        assert 200 in monitor.monitoring_sessions  # Active session
    
    @pytest.mark.asyncio
    async def test_monitor_pr_state_changes(self, monitor, mock_github_client):
        """Test monitoring PR with state changes"""
        call_count = 0
        merge_ready_called = False
        
        async def mock_get_pr(*args):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                # First call - unstable
                return {
                    "state": "open",
                    "mergeable": False,
                    "mergeable_state": "unstable",
                    "head": {"sha": "abc123"},
                    "base": {"sha": "def456"}
                }
            else:
                # Second call - clean
                return {
                    "state": "open",
                    "mergeable": True,
                    "mergeable_state": "clean",
                    "head": {"sha": "abc123"},
                    "base": {"sha": "def456"}
                }
        
        mock_github_client.pulls.get.side_effect = mock_get_pr
        mock_github_client.checks.list_for_ref.return_value = {"check_runs": [{"conclusion": "success"}]}
        mock_github_client.pulls.list_reviews.return_value = []
        mock_github_client.repos.compare.return_value = {"behind_by": 0}
        
        # Register callback
        async def on_merge_ready(pr_number):
            nonlocal merge_ready_called
            merge_ready_called = True
        
        monitor.register_callback("merge_ready", on_merge_ready)
        
        # Start monitoring with very short polling interval
        monitor.polling_interval = 0.1
        session = await monitor.start_monitoring("owner", "repo", 123)
        
        # Wait for state change
        await asyncio.sleep(0.3)
        
        # Stop monitoring
        await monitor.stop_monitoring(123)
        
        # Check results
        assert len(session.snapshots) >= 2
        assert len(session.state_transitions) >= 1
        assert merge_ready_called is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])