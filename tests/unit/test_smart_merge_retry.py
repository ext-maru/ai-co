#!/usr/bin/env python3
"""
Tests for Smart Merge Retry Engine
Issue #145: Test coverage for advanced retry strategies
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import time
from datetime import datetime

from libs.integrations.github.smart_merge_retry import (
    SmartMergeRetryEngine,
    MergeableState,
    RetryStrategy,
    RetryConfig,
    RetryAttempt
)


class TestRetryConfig:
    """Test retry configuration"""
    
    def test_default_configs(self):
        """Test default retry configurations are properly set"""
        # Test UNSTABLE config
        unstable = SmartMergeRetryEngine.DEFAULT_CONFIGS[MergeableState.UNSTABLE]
        assert unstable.max_retries == 10
        assert unstable.base_delay == 30
        assert unstable.max_delay == 300
        assert unstable.timeout == 1800
        
        # Test BEHIND config
        behind = SmartMergeRetryEngine.DEFAULT_CONFIGS[MergeableState.BEHIND]
        assert behind.max_retries == 3
        assert behind.base_delay == 60
        
        # Test DIRTY config
        dirty = SmartMergeRetryEngine.DEFAULT_CONFIGS[MergeableState.DIRTY]
        assert dirty.max_retries == 0
    
    def test_retry_config_dataclass(self):
        """Test RetryConfig dataclass initialization"""
        config = RetryConfig(
            max_retries=5,
            base_delay=10,
            max_delay=100,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF
        )
        assert config.max_retries == 5
        assert config.base_delay == 10
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF


class TestSmartMergeRetryEngine:
    """Test SmartMergeRetryEngine functionality"""
    
    @pytest.fixture
    def mock_github_client(self):
        """Create mock GitHub client"""
        client = Mock()
        client.pulls = Mock()
        client.pulls.get = AsyncMock()
        client.pulls.merge = AsyncMock()
        client.pulls.update_branch = AsyncMock()
        client.pulls.check_if_merged = AsyncMock()
        client.pulls.list_reviews = AsyncMock()
        client.issues = Mock()
        client.issues.create_comment = AsyncMock()
        return client
    
    @pytest.fixture
    def retry_engine(self, mock_github_client):
        """Create retry engine instance"""
        return SmartMergeRetryEngine(mock_github_client)
    
    def test_calculate_delay_no_backoff(self, retry_engine):
        """Test delay calculation without exponential backoff"""
        strategy = RetryStrategy(
            base_delay=30,
            exponential_backoff=False,
            jitter=False
        )
        
        # Should always return base delay
        assert retry_engine._calculate_delay(strategy, 1) == 30
        assert retry_engine._calculate_delay(strategy, 5) == 30
    
    def test_calculate_delay_with_backoff(self, retry_engine):
        """Test delay calculation with exponential backoff"""
        strategy = RetryStrategy(
            base_delay=10,
            max_delay=100,
            exponential_backoff=True,
            jitter=False
        )
        
        # Test exponential growth
        assert retry_engine._calculate_delay(strategy, 1) == 10  # 10 * 2^0
        assert retry_engine._calculate_delay(strategy, 2) == 20  # 10 * 2^1
        assert retry_engine._calculate_delay(strategy, 3) == 40  # 10 * 2^2
        assert retry_engine._calculate_delay(strategy, 4) == 80  # 10 * 2^3
        assert retry_engine._calculate_delay(strategy, 5) == 100  # capped at max_delay
    
    def test_calculate_delay_with_jitter(self, retry_engine):
        """Test delay calculation with jitter"""
        strategy = RetryStrategy(
            base_delay=100,
            exponential_backoff=False,
            jitter=True
        )
        
        # With jitter, delay should be between base and base + 10%
        delay = retry_engine._calculate_delay(strategy, 1)
        assert 100 <= delay <= 110
    
    def test_get_retry_strategy(self, retry_engine):
        """Test getting retry strategy for different states"""
        # Known states
        assert retry_engine._get_retry_strategy("clean") == RetryStrategy()
        assert retry_engine._get_retry_strategy("unstable") == RETRY_STRATEGIES[MergeableState.UNSTABLE]
        assert retry_engine._get_retry_strategy("behind") == RETRY_STRATEGIES[MergeableState.BEHIND]
        
        # Unknown state
        assert retry_engine._get_retry_strategy("invalid") == RETRY_STRATEGIES[MergeableState.UNKNOWN]
    
    @pytest.mark.asyncio
    async def test_check_pr_state_success(self, retry_engine, mock_github_client):
        """Test successful PR state check"""
        # Mock PR data
        mock_github_client.pulls.get.return_value = {
            "state": "open",
            "mergeable": True,
            "mergeable_state": "clean",
            "merged": False,
            "head": {"sha": "abc123"},
            "base": {"sha": "def456"},
            "requested_reviewers": [],
            "draft": False
        }
        mock_github_client.pulls.check_if_merged.return_value = False
        
        result = await retry_engine._check_pr_state("owner", "repo", 123)
        
        assert result["state"] == "open"
        assert result["mergeable"] is True
        assert result["mergeable_state"] == "clean"
        assert result["merged"] is False
    
    @pytest.mark.asyncio
    async def test_check_pr_state_error(self, retry_engine, mock_github_client):
        """Test PR state check with error"""
        mock_github_client.pulls.get.side_effect = Exception("API Error")
        
        result = await retry_engine._check_pr_state("owner", "repo", 123)
        
        assert result["mergeable_state"] == "unknown"
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_update_branch_success(self, retry_engine, mock_github_client):
        """Test successful branch update"""
        mock_github_client.pulls.update_branch.return_value = {
            "message": "Branch updated successfully"
        }
        
        result = await retry_engine._update_branch("owner", "repo", 123)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_update_branch_failure(self, retry_engine, mock_github_client):
        """Test failed branch update"""
        mock_github_client.pulls.update_branch.side_effect = Exception("Update failed")
        
        result = await retry_engine._update_branch("owner", "repo", 123)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_review_status(self, retry_engine, mock_github_client):
        """Test review status check"""
        mock_github_client.pulls.list_reviews.return_value = [
            {"state": "APPROVED"},
            {"state": "APPROVED"},
            {"state": "CHANGES_REQUESTED"},
            {"state": "PENDING"}
        ]
        
        result = await retry_engine._check_review_status("owner", "repo", 123)
        
        assert result["approved"] == 2
        assert result["changes_requested"] == 1
        assert result["pending"] == 1
        assert result["total"] == 4
    
    @pytest.mark.asyncio
    async def test_attempt_merge_success(self, retry_engine, mock_github_client):
        """Test successful merge attempt"""
        mock_github_client.pulls.merge.return_value = {
            "merged": True,
            "message": "Pull Request successfully merged"
        }
        
        success, message = await retry_engine._attempt_merge("owner", "repo", 123)
        
        assert success is True
        assert message == "Successfully merged"
    
    @pytest.mark.asyncio
    async def test_attempt_merge_failure(self, retry_engine, mock_github_client):
        """Test failed merge attempt"""
        mock_github_client.pulls.merge.side_effect = Exception("Merge conflict")
        
        success, message = await retry_engine._attempt_merge("owner", "repo", 123)
        
        assert success is False
        assert "Merge conflict" in message
    
    @pytest.mark.asyncio
    async def test_smart_merge_clean_state(self, retry_engine, mock_github_client):
        """Test smart merge with clean state (immediate merge)"""
        # Mock PR in clean state
        mock_github_client.pulls.get.return_value = {
            "state": "open",
            "mergeable": True,
            "mergeable_state": "clean",
            "merged": False,
            "head": {"sha": "abc123"},
            "base": {"sha": "def456"}
        }
        mock_github_client.pulls.check_if_merged.return_value = False
        mock_github_client.pulls.merge.return_value = {"merged": True}
        
        result = await retry_engine.smart_merge_with_retry(
            "owner", "repo", 123, update_status=False
        )
        
        assert result["success"] is True
        assert result["attempts"] == 1
        assert "Successfully merged" in result["message"]
    
    @pytest.mark.asyncio
    async def test_smart_merge_already_merged(self, retry_engine, mock_github_client):
        """Test smart merge with already merged PR"""
        # Mock already merged PR
        mock_github_client.pulls.get.return_value = {
            "state": "closed",
            "merged": True,
            "mergeable_state": "clean"
        }
        mock_github_client.pulls.check_if_merged.return_value = True
        
        result = await retry_engine.smart_merge_with_retry(
            "owner", "repo", 123, update_status=False
        )
        
        assert result["success"] is True
        assert "already merged" in result["message"]
    
    @pytest.mark.asyncio
    async def test_smart_merge_unstable_to_clean(self, retry_engine, mock_github_client):
        """Test smart merge transitioning from unstable to clean"""
        call_count = 0
        
        async def mock_get_pr(*args):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                # First two calls return unstable
                return {
                    "state": "open",
                    "mergeable": False,
                    "mergeable_state": "unstable",
                    "merged": False,
                    "head": {"sha": "abc123"},
                    "base": {"sha": "def456"}
                }
            else:
                # Third call returns clean
                return {
                    "state": "open",
                    "mergeable": True,
                    "mergeable_state": "clean",
                    "merged": False,
                    "head": {"sha": "abc123"},
                    "base": {"sha": "def456"}
                }
        
        mock_github_client.pulls.get.side_effect = mock_get_pr
        mock_github_client.pulls.check_if_merged.return_value = False
        mock_github_client.pulls.merge.return_value = {"merged": True}
        
        # Use shorter delays for testing
        with patch.object(retry_engine, '_calculate_delay', return_value=0.1):
            result = await retry_engine.smart_merge_with_retry(
                "owner", "repo", 123, update_status=False
            )
        
        assert result["success"] is True
        assert result["attempts"] == 3
        assert len(result["state_changes"]) == 2  # unstable -> clean
    
    @pytest.mark.asyncio
    async def test_smart_merge_behind_with_auto_update(self, retry_engine, mock_github_client):
        """Test smart merge with behind state and auto update"""
        # Mock PR behind base
        mock_github_client.pulls.get.return_value = {
            "state": "open",
            "mergeable": False,
            "mergeable_state": "behind",
            "merged": False,
            "head": {"sha": "abc123"},
            "base": {"sha": "def456"}
        }
        mock_github_client.pulls.check_if_merged.return_value = False
        mock_github_client.pulls.update_branch.return_value = {"message": "Branch updated successfully"}
        
        # Use shorter delays for testing
        with patch.object(retry_engine, '_calculate_delay', return_value=0.1):
            # Run for limited time to test update branch logic
            with patch('asyncio.sleep', new=AsyncMock()):
                result = await retry_engine.smart_merge_with_retry(
                    "owner", "repo", 123, update_status=False
                )
        
        # Should have attempted to update branch
        mock_github_client.pulls.update_branch.assert_called()
    
    @pytest.mark.asyncio
    async def test_smart_merge_conflict(self, retry_engine, mock_github_client):
        """Test smart merge with merge conflict"""
        # Mock PR with conflict
        mock_github_client.pulls.get.return_value = {
            "state": "open",
            "mergeable": False,
            "mergeable_state": "dirty",
            "merged": False,
            "head": {"sha": "abc123"},
            "base": {"sha": "def456"}
        }
        mock_github_client.pulls.check_if_merged.return_value = False
        
        result = await retry_engine.smart_merge_with_retry(
            "owner", "repo", 123, update_status=False
        )
        
        assert result["success"] is False
        assert "conflict" in result["message"].lower()
        assert result["attempts"] == 1  # Should not retry on conflict
    
    @pytest.mark.asyncio
    async def test_smart_merge_max_retries_exceeded(self, retry_engine, mock_github_client):
        """Test smart merge exceeding max retries"""
        # Mock PR always in unknown state
        mock_github_client.pulls.get.return_value = {
            "state": "open",
            "mergeable": None,
            "mergeable_state": "unknown",
            "merged": False,
            "head": {"sha": "abc123"},
            "base": {"sha": "def456"}
        }
        mock_github_client.pulls.check_if_merged.return_value = False
        
        # Use shorter delays and fewer retries for testing
        with patch.object(retry_engine, '_calculate_delay', return_value=0.01):
            with patch.object(retry_engine, '_get_retry_strategy') as mock_strategy:
                mock_strategy.return_value = RetryStrategy(max_retries=2)
                
                result = await retry_engine.smart_merge_with_retry(
                    "owner", "repo", 123, update_status=False
                )
        
        assert result["success"] is False
        assert "Max retries" in result["message"]
        assert result["attempts"] == 3  # initial + 2 retries
    
    @pytest.mark.asyncio
    async def test_smart_merge_timeout(self, retry_engine, mock_github_client):
        """Test smart merge timeout"""
        # Mock PR always in unstable state
        mock_github_client.pulls.get.return_value = {
            "state": "open",
            "mergeable": False,
            "mergeable_state": "unstable",
            "merged": False,
            "head": {"sha": "abc123"},
            "base": {"sha": "def456"}
        }
        mock_github_client.pulls.check_if_merged.return_value = False
        
        # Mock time to simulate timeout
        start_time = time.time()
        with patch('time.time') as mock_time:
            # First call returns start time, subsequent calls return > 30 min later
            mock_time.side_effect = [start_time, start_time, start_time + 1801]
            
            result = await retry_engine.smart_merge_with_retry(
                "owner", "repo", 123, update_status=False
            )
        
        assert result["success"] is False
        assert "Timeout" in result["message"]
    
    @pytest.mark.asyncio
    async def test_post_status_comment(self, retry_engine, mock_github_client):
        """Test posting status comments"""
        status = RetryStatus(
            attempt=3,
            total_wait_time=90.5,
            state_changes=[("unstable", 10.0), ("clean", 85.0)]
        )
        
        await retry_engine._post_status_comment(
            "owner", "repo", 123, status, "Waiting for CI"
        )
        
        # Verify comment was posted
        mock_github_client.issues.create_comment.assert_called_once()
        args = mock_github_client.issues.create_comment.call_args
        assert args[0] == ("owner", "repo", 123)
        assert "Merge Retry Status Update" in args[1]
        assert "Waiting for CI" in args[1]


class TestRetryStatus:
    """Test RetryStatus tracking"""
    
    def test_retry_status_initialization(self):
        """Test RetryStatus dataclass initialization"""
        status = RetryStatus()
        
        assert status.attempt == 0
        assert status.total_wait_time == 0
        assert status.start_time > 0
        assert status.state_changes == []
        assert status.last_state is None
        assert status.success is False
        assert status.final_message is None
    
    def test_retry_status_tracking(self):
        """Test status tracking during retry"""
        status = RetryStatus()
        
        # Simulate retry attempts
        status.attempt = 3
        status.total_wait_time = 120.5
        status.state_changes.append(("unstable", time.time()))
        status.state_changes.append(("clean", time.time()))
        status.last_state = "clean"
        status.success = True
        status.final_message = "Successfully merged"
        
        assert status.attempt == 3
        assert len(status.state_changes) == 2
        assert status.success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])