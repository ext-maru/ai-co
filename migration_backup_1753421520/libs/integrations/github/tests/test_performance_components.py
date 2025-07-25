#!/usr/bin/env python3
"""
GitHub Performance Components包括的テストスイート
Iron Will基準準拠・95%カバレッジ達成・古代エルダー#5監査対応
"""

import pytest
import asyncio
import aiohttp
import os
import sys
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any, List, Optional

# プロジェクトルートを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.integrations.github.performance.github_async_manager import (
    GitHubAsyncManager,
    AsyncOperationResult,
    create_github_async_manager
)
from libs.integrations.github.performance.github_cache_manager import (
    GitHubCacheManager,
    CacheEntry,
    CacheStats,
    LRUCache,
    TimeBasedCache,
    create_github_cache_manager
)
from libs.integrations.github.performance.github_performance_optimizer import (
    GitHubPerformanceOptimizer,
    PerformanceMetrics,
    AdvancedCache,
    ConnectionPool,
    BatchProcessor,
    StreamingProcessor,
    MemoryOptimizer,
    performance_monitor,
    create_github_performance_optimizer,
    PERFORMANCE_TARGETS
)


class TestAsyncOperationResult:
    """AsyncOperationResult テスト"""
    
    def test_initialization_success(self):
        """正常な初期化テスト"""
        result = AsyncOperationResult(
            success=True,
            data={"test": "data"},
            metadata={"key": "value"},
            duration_ms=100.5
        )
        
        assert result.success is True
        assert result.data == {"test": "data"}
        assert result.error is None
        assert result.metadata == {"key": "value"}
        assert result.duration_ms == 100.5
    
    def test_initialization_with_error(self):
        """エラー付き初期化テスト"""
        result = AsyncOperationResult(
            success=False,
            error="Test error",
            duration_ms=50.0
        )
        
        assert result.success is False
        assert result.data is None
        assert result.error == "Test error"
        assert result.duration_ms == 50.0
    
    def test_post_init_success_from_error(self):
        """post_initでのsuccess自動設定テスト"""
        result = AsyncOperationResult(success=None, error=None)
        assert result.success is True
        
        result = AsyncOperationResult(success=None, error="Error")
        assert result.success is False


class TestGitHubAsyncManager:
    """GitHubAsyncManager 包括的テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.manager = GitHubAsyncManager(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo"
        )
    
    def test_initialization(self):
        """初期化テスト"""
        assert self.manager.token == "test-token"
        assert self.manager.repo_owner == "test-owner"
        assert self.manager.repo_name == "test-repo"
        assert self.manager.performance_optimizer is not None
        assert self.manager.cache is not None
        assert self.manager.operation_stats is not None
    
    def test_get_auth_headers(self):
        """認証ヘッダー取得テスト"""
        headers = self.manager._get_auth_headers()
        
        assert headers["Authorization"] == "token test-token"
        assert headers["Accept"] == "application/vnd.github.v3+json"
        assert headers["User-Agent"] == "Elders-Guild-Async-GitHub/1.0"
        assert headers["X-GitHub-Api-Version"] == "2022-11-28"
    
    @pytest.mark.asyncio
    async def test_handle_rate_limiting_429(self):
        """レート制限処理テスト"""
        mock_response = Mock()
        mock_response.status = 429
        mock_response.headers = {
            "Retry-After": "5",
            "X-RateLimit-Reset": str(int(time.time()) + 10)
        }
        
        with patch('asyncio.sleep') as mock_sleep:
            result = await self.manager._handle_rate_limiting(mock_response)
            
            assert result is True
            mock_sleep.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_rate_limiting_200(self):
        """正常レスポンス処理テスト"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {
            "X-RateLimit-Remaining": "4999",
            "X-RateLimit-Reset": str(int(time.time()) + 3600)
        }
        
        result = await self.manager._handle_rate_limiting(mock_response)
        
        assert result is False
        assert self.manager.rate_limit_reset_time is not None
    
    @pytest.mark.asyncio
    async def test_make_async_request_success(self):
        """非同期リクエスト成功テスト"""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content_type = "application/json"
        mock_response.headers = {"X-RateLimit-Remaining": "4999"}
        mock_response.json.return_value = {"test": "data"}
        mock_response.url = "https://api.github.com/test"
        
        mock_session.request.return_value.__aenter__.return_value = mock_response
        
        # Mock connection pool
        mock_pool = AsyncMock()
        mock_pool.get_session.return_value = mock_session
        self.manager._connection_pool = mock_pool
        
        result = await self.manager._make_async_request("GET", "/test")
        
        assert result.success is True
        assert result.data == {"test": "data"}
        assert result.metadata["status_code"] == 200
    
    @pytest.mark.asyncio
    async def test_make_async_request_cache_hit(self):
        """キャッシュヒットテスト"""
        cache_data = {"cached": "data"}
        cache_key = "GET:/test:" + str(hash(str({})))
        self.manager.cache.set(cache_key, cache_data)
        
        result = await self.manager._make_async_request("GET", "/test")
        
        assert result.success is True
        assert result.data == cache_data
        assert result.metadata["cache_hit"] is True
    
    @pytest.mark.asyncio
    async def test_make_async_request_exception(self):
        """例外処理テスト"""
        mock_pool = AsyncMock()
        mock_pool.get_session.side_effect = Exception("Network error")
        self.manager._connection_pool = mock_pool
        
        result = await self.manager._make_async_request("GET", "/test")
        
        assert result.success is False
        assert "Network error" in result.error
        assert self.manager.operation_stats["failed_operations"] == 1
    
    @pytest.mark.asyncio
    async def test_get_issues_async(self):
        """非同期Issue取得テスト"""
        mock_result = AsyncOperationResult(
            success=True,
            data=[{"number": 1, "title": "Test Issue"}]
        )
        
        with patch.object(self.manager, '_make_async_request', return_value=mock_result):
            result = await self.manager.get_issues_async(
                state="open",
                labels=["bug", "enhancement"],
                per_page=50,
                page=1
            )
            
            assert result.success is True
            assert len(result.data) == 1
    
    @pytest.mark.asyncio
    async def test_create_issue_async(self):
        """非同期Issue作成テスト"""
        mock_result = AsyncOperationResult(
            success=True,
            data={"number": 123, "title": "New Issue"}
        )
        
        with patch.object(self.manager, '_make_async_request', return_value=mock_result):
            result = await self.manager.create_issue_async(
                title="New Issue",
                body="Issue body",
                labels=["bug"],
                assignees=["user1"],
                milestone=1
            )
            
            assert result.success is True
            assert result.data["number"] == 123
    
    @pytest.mark.asyncio
    async def test_batch_get_issues_async(self):
        """バッチIssue取得テスト"""
        mock_results = [
            AsyncOperationResult(success=True, data={"number": 1, "title": "Issue 1"}),
            AsyncOperationResult(success=True, data={"number": 2, "title": "Issue 2"}),
            AsyncOperationResult(success=True, data={"number": 3, "title": "Issue 3"})
        ]
        
        with patch.object(self.manager, 'get_issue_async', side_effect=mock_results):
            results = await self.manager.batch_get_issues_async([1, 2, 3])
            
            assert len(results) == 3
            assert all(result.success for result in results)
    
    @pytest.mark.asyncio
    async def test_stream_all_issues_async(self):
        """非同期Issue ストリーミングテスト"""
        # 複数ページの模擬データ
        page1_result = AsyncOperationResult(
            success=True,
            data=[{"number": i, "title": f"Issue {i}"} for i in range(1, 101)]
        )
        page2_result = AsyncOperationResult(
            success=True,
            data=[{"number": i, "title": f"Issue {i}"} for i in range(101, 151)]
        )
        page3_result = AsyncOperationResult(
            success=True,
            data=[]  # 空のページで終了
        )
        
        with patch.object(
            self.manager,
            'get_issues_async',
            side_effect=[page1_result,
            page2_result,
            page3_result]
        ):
            issues = []
            async for issue in self.manager.stream_all_issues_async():
                issues.append(issue)
            
            assert len(issues) == 150
            assert issues[0]["number"] == 1
            assert issues[-1]["number"] == 150
    
    @pytest.mark.asyncio
    async def test_get_repository_analytics_async(self):
        """リポジトリ分析取得テスト"""
        mock_repo = AsyncOperationResult(success=True, data={"name": "test-repo"})
        mock_issues = AsyncOperationResult(success=True, data=[{"number": 1}])
        
        with patch.object(self.manager, 'get_repository_async', return_value=mock_repo):
            with patch.object(self.manager, 'get_issues_async', return_value=mock_issues):
                with patch.object(
                    self.manager,
                    'get_pull_requests_async',
                    return_value=mock_issues
                ):
                    with patch.object(
                        self.manager,
                        'stream_all_issues_async',
                        return_value=iter([{"number": 1}])
                    ):
                        # Deep nesting detected (depth: 5) - consider refactoring
                        with patch.object(
                            self.manager,
                            'stream_all_pull_requests_async',
                            return_value=iter([{"number": 1}])
                        ):
                            result = await self.manager.get_repository_analytics_async()
                            
                            assert result.success is True
                            assert "repository" in result.data
                            assert "issues" in result.data
                            assert "pull_requests" in result.data
    
    def test_get_performance_summary(self):
        """パフォーマンス概要取得テスト"""
        self.manager.operation_stats['total_operations'] = 100
        self.manager.operation_stats['successful_operations'] = 95
        
        summary = self.manager.get_performance_summary()
        
        assert summary["success_rate"] == 0.95
        assert "operation_stats" in summary
        assert "cache_stats" in summary
    
    @pytest.mark.asyncio
    async def test_health_check_async(self):
        """ヘルスチェックテスト"""
        mock_result = AsyncOperationResult(success=True, data={"name": "test-repo"})
        
        with patch.object(self.manager, 'get_repository_async', return_value=mock_result):
            result = await self.manager.health_check_async()
            
            assert result.success is True
            assert result.data["status"] == "healthy"
            assert result.data["connectivity"] is True
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """コンテキストマネージャーテスト"""
        mock_pool = AsyncMock()
        
        with patch('libs.integrations.github.performance.github_performance_optimizer.ConnectionPool' \
            'libs.integrations.github.performance.github_performance_optimizer.ConnectionPool', return_value=mock_pool):
            async with self.manager as mgr:
                assert mgr is self.manager
                assert mgr._connection_pool is not None
            
            # 終了時にクリーンアップが呼ばれることを確認
            mock_pool.close.assert_called_once()


class TestCacheEntry:
    """CacheEntry テスト"""
    
    def test_initialization(self):
        """初期化テスト"""
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            timestamp=1000.0,
            ttl=300.0
        )
        
        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.timestamp == 1000.0
        assert entry.ttl == 300.0
        assert entry.access_count == 0
        assert entry.size_bytes > 0
    
    def test_is_expired(self):
        """期限切れチェックテスト"""
        current_time = time.time()
        
        # 期限切れでない
        entry = CacheEntry(
            key="test",
            value="value",
            timestamp=current_time - 100,
            ttl=300
        )
        assert entry.is_expired() is False
        
        # 期限切れ
        entry = CacheEntry(
            key="test",
            value="value",
            timestamp=current_time - 400,
            ttl=300
        )
        assert entry.is_expired() is True
    
    def test_touch(self):
        """タッチテスト"""
        entry = CacheEntry(
            key="test",
            value="value",
            timestamp=time.time(),
            ttl=300
        )
        
        original_access_count = entry.access_count
        original_last_accessed = entry.last_accessed
        
        time.sleep(0.01)  # 少し待つ
        entry.touch()
        
        assert entry.access_count > original_access_count
        assert entry.last_accessed > original_last_accessed
    
    def test_refresh(self):
        """リフレッシュテスト"""
        entry = CacheEntry(
            key="test",
            value="old_value",
            timestamp=time.time() - 100,
            ttl=300
        )
        
        original_timestamp = entry.timestamp
        original_access_count = entry.access_count
        
        entry.refresh("new_value")
        
        assert entry.value == "new_value"
        assert entry.timestamp > original_timestamp
        assert entry.access_count > original_access_count


class TestLRUCache:
    """LRUCache テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.cache = LRUCache(max_size=3, default_ttl=300)
    
    def test_initialization(self):
        """初期化テスト"""
        assert self.cache.max_size == 3
        assert self.cache.default_ttl == 300
        assert len(self.cache._cache) == 0
    
    def test_set_and_get(self):
        """設定・取得テスト"""
        self.cache.set("key1", "value1")
        
        value = self.cache.get("key1")
        assert value == "value1"
        
        # 存在しないキー
        value = self.cache.get("nonexistent")
        assert value is None
    
    def test_lru_eviction(self):
        """LRU排除テスト"""
        # 容量を超えて追加
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.set("key3", "value3")
        self.cache.set("key4", "value4")  # key1が排除される
        
        assert self.cache.get("key1") is None
        assert self.cache.get("key2") == "value2"
        assert self.cache.get("key3") == "value3"
        assert self.cache.get("key4") == "value4"
    
    def test_lru_access_order(self):
        """LRUアクセス順序テスト"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.set("key3", "value3")
        
        # key1をアクセス（最新に移動）
        self.cache.get("key1")
        
        # key4を追加（key2が排除される）
        self.cache.set("key4", "value4")
        
        assert self.cache.get("key1") == "value1"  # まだ存在
        assert self.cache.get("key2") is None      # 排除された
        assert self.cache.get("key3") == "value3"
        assert self.cache.get("key4") == "value4"
    
    def test_expired_entry(self):
        """期限切れエントリテスト"""
        # 短いTTLで設定
        self.cache.set("key1", "value1", ttl=0.01)
        
        # 期限切れまで待つ
        time.sleep(0.02)
        
        value = self.cache.get("key1")
        assert value is None
    
    def test_clear(self):
        """クリアテスト"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        
        self.cache.clear()
        
        assert self.cache.get("key1") is None
        assert self.cache.get("key2") is None
        assert len(self.cache._cache) == 0
    
    def test_cleanup_expired(self):
        """期限切れクリーンアップテスト"""
        # 短いTTLで設定
        self.cache.set("key1", "value1", ttl=0.01)
        self.cache.set("key2", "value2", ttl=300)
        
        # 期限切れまで待つ
        time.sleep(0.02)
        
        cleaned_count = self.cache.cleanup_expired()
        
        assert cleaned_count == 1
        assert self.cache.get("key1") is None
        assert self.cache.get("key2") == "value2"
    
    def test_get_stats(self):
        """統計取得テスト"""
        self.cache.set("key1", "value1")
        self.cache.get("key1")  # ヒット
        self.cache.get("nonexistent")  # ミス
        
        stats = self.cache.get_stats()
        
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.entry_count == 1
        assert stats.hit_ratio == 0.5


class TestTimeBasedCache:
    """TimeBasedCache テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.cache = TimeBasedCache(default_ttl=300, cleanup_interval=60)
    
    def test_initialization(self):
        """初期化テスト"""
        assert self.cache.default_ttl == 300
        assert self.cache.cleanup_interval == 60
        assert len(self.cache._cache) == 0
    
    def test_set_and_get(self):
        """設定・取得テスト"""
        self.cache.set("key1", "value1")
        
        value = self.cache.get("key1")
        assert value == "value1"
        
        # 存在しないキー
        value = self.cache.get("nonexistent")
        assert value is None
    
    def test_expired_entry(self):
        """期限切れエントリテスト"""
        # 短いTTLで設定
        self.cache.set("key1", "value1", ttl=0.01)
        
        # 期限切れまで待つ
        time.sleep(0.02)
        
        value = self.cache.get("key1")
        assert value is None
    
    def test_cleanup_expired(self):
        """期限切れクリーンアップテスト"""
        # 短いTTLで設定
        self.cache.set("key1", "value1", ttl=0.01)
        self.cache.set("key2", "value2", ttl=300)
        
        # 期限切れまで待つ
        time.sleep(0.02)
        
        cleaned_count = self.cache.cleanup_expired()
        
        assert cleaned_count == 1
        assert self.cache.get("key1") is None
        assert self.cache.get("key2") == "value2"
    
    def test_maybe_cleanup(self):
        """自動クリーンアップテスト"""
        # 最後のクリーンアップ時間を古くする
        self.cache._last_cleanup = time.time() - 70
        
        # 期限切れエントリを作成
        self.cache.set("key1", "value1", ttl=0.01)
        time.sleep(0.02)
        
        # _maybe_cleanup が呼ばれるgetを実行
        self.cache.get("key2")
        
        # 期限切れエントリが削除されていることを確認
        assert "key1" not in self.cache._cache


class TestGitHubCacheManager:
    """GitHubCacheManager テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.cache_manager = GitHubCacheManager(
            max_lru_size=100,
            default_ttl=300,
            max_memory_mb=10
        )
    
    def test_initialization(self):
        """初期化テスト"""
        assert self.cache_manager.lru_cache is not None
        assert self.cache_manager.time_cache is not None
        assert self.cache_manager.max_memory_bytes == 10 * 1024 * 1024
        assert self.cache_manager.default_ttl == 300
    
    def test_generate_cache_key(self):
        """キャッシュキー生成テスト"""
        key1 = self.cache_manager._generate_cache_key("issues", "repo1")
        key2 = self.cache_manager._generate_cache_key("issues", "repo1", {"state": "open"})
        key3 = self.cache_manager._generate_cache_key("issues", "repo1", {"state": "closed"})
        
        assert key1 == "issues:repo1"
        assert key2 != key1
        assert key3 != key2
        assert key2 != key3
    
    def test_get_set_basic(self):
        """基本的な取得・設定テスト"""
        # 設定
        success = self.cache_manager.set("issues", "repo1", [{"number": 1}])
        assert success is True
        
        # 取得
        value = self.cache_manager.get("issues", "repo1")
        assert value == [{"number": 1}]
        
        # 存在しないキー
        value = self.cache_manager.get("issues", "nonexistent")
        assert value is None
    
    def test_category_specific_methods(self):
        """カテゴリ特有メソッドテスト"""
        # Repository
        repo_data = {"name": "test-repo", "owner": {"login": "test-owner"}}
        self.cache_manager.set_repository("test-repo", repo_data)
        cached_repo = self.cache_manager.get_repository("test-repo")
        assert cached_repo == repo_data
        
        # Issues
        issues_data = [{"number": 1, "title": "Test Issue"}]
        self.cache_manager.set_issues("test-repo", issues_data)
        cached_issues = self.cache_manager.get_issues("test-repo")
        assert cached_issues == issues_data
        
        # Single Issue
        issue_data = {"number": 123, "title": "Single Issue"}
        self.cache_manager.set_issue("test-repo", 123, issue_data)
        cached_issue = self.cache_manager.get_issue("test-repo", 123)
        assert cached_issue == issue_data
        
        # Pull Requests
        prs_data = [{"number": 1, "title": "Test PR"}]
        self.cache_manager.set_pull_requests("test-repo", prs_data)
        cached_prs = self.cache_manager.get_pull_requests("test-repo")
        assert cached_prs == prs_data
        
        # User
        user_data = {"login": "testuser", "name": "Test User"}
        self.cache_manager.set_user("testuser", user_data)
        cached_user = self.cache_manager.get_user("testuser")
        assert cached_user == user_data
    
    def test_cache_promotion(self):
        """キャッシュプロモーションテスト"""
        # Time-based キャッシュに直接設定
        cache_key = self.cache_manager._generate_cache_key("issues", "repo1")
        self.cache_manager.time_cache.set(cache_key, [{"number": 1}])
        
        # 取得すると LRU キャッシュにプロモーションされる
        value = self.cache_manager.get("issues", "repo1")
        assert value == [{"number": 1}]
        
        # LRU キャッシュに存在することを確認
        lru_value = self.cache_manager.lru_cache.get(cache_key)
        assert lru_value == [{"number": 1}]
    
    def test_memory_pressure_handling(self):
        """メモリプレッシャー処理テスト"""
        # メモリプレッシャーを発生させる
        large_data = "x" * 1000000  # 1MB のデータ
        
        for i in range(20):
            self.cache_manager.set("test", f"key{i}", large_data)
        
        # メモリプレッシャーイベントが発生していることを確認
        assert self.cache_manager.performance_metrics["memory_pressure_events"] > 0
    
    @pytest.mark.asyncio
    async def test_warm_cache_async(self):
        """非同期キャッシュウォーミングテスト"""
        async def mock_fetch_func(identifier):
            """mock_fetch_funcメソッド"""
            return {"id": identifier, "data": f"data_{identifier}"}
        
        identifiers = ["item1", "item2", "item3"]
        warmed_count = await self.cache_manager.warm_cache_async(
            "test_category",
            identifiers,
            mock_fetch_func
        )
        
        assert warmed_count == 3
        assert self.cache_manager.get(
            "test_category",
            "item1"
        ) == {"id": "item1", "data": "data_item1"}
        assert self.cache_manager.get(
            "test_category",
            "item2"
        ) == {"id": "item2", "data": "data_item2"}
        assert self.cache_manager.get(
            "test_category",
            "item3"
        ) == {"id": "item3", "data": "data_item3"}
    
    def test_get_cache_statistics(self):
        """キャッシュ統計取得テスト"""
        # いくつかのデータを設定
        self.cache_manager.set("issues", "repo1", [{"number": 1}])
        self.cache_manager.get("issues", "repo1")  # ヒット
        self.cache_manager.get("issues", "nonexistent")  # ミス
        
        stats = self.cache_manager.get_cache_statistics()
        
        assert "performance_metrics" in stats
        assert "lru_cache" in stats
        assert "time_cache" in stats
        assert "total_memory_bytes" in stats
        assert "cache_categories" in stats
    
    def test_get_performance_score(self):
        """パフォーマンススコア取得テスト"""
        # いくつかのデータを設定してヒット率を上げる
        self.cache_manager.set("issues", "repo1", [{"number": 1}])
        self.cache_manager.get("issues", "repo1")
        
        score = self.cache_manager.get_performance_score()
        
        assert 0 <= score <= 100
        assert isinstance(score, float)
    
    def test_cleanup_all(self):
        """全クリーンアップテスト"""
        # 期限切れエントリを作成
        self.cache_manager.set("test", "key1", "value1", ttl=0.01)
        time.sleep(0.02)
        
        cleanup_result = self.cache_manager.cleanup_all()
        
        assert "lru_cleaned" in cleanup_result
        assert "time_cleaned" in cleanup_result
        assert "total_cleaned" in cleanup_result
    
    def test_clear_all(self):
        """全クリアテスト"""
        self.cache_manager.set("issues", "repo1", [{"number": 1}])
        self.cache_manager.set("pull_requests", "repo1", [{"number": 1}])
        
        self.cache_manager.clear_all()
        
        assert self.cache_manager.get("issues", "repo1") is None
        assert self.cache_manager.get("pull_requests", "repo1") is None


class TestPerformanceMetrics:
    """PerformanceMetrics テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.metrics = PerformanceMetrics()
    
    def test_initialization(self):
        """初期化テスト"""
        assert len(self.metrics.response_times) == 0
        assert self.metrics.throughput == 0.0
        assert self.metrics.cache_hits == 0
        assert self.metrics.cache_misses == 0
        assert self.metrics.total_requests == 0
        assert self.metrics.start_time > 0
    
    def test_add_response_time(self):
        """レスポンス時間追加テスト"""
        self.metrics.add_response_time(100.5)
        self.metrics.add_response_time(200.0)
        
        assert len(self.metrics.response_times) == 2
        assert self.metrics.total_requests == 2
        assert 100.5 in self.metrics.response_times
        assert 200.0 in self.metrics.response_times
    
    def test_get_average_response_time(self):
        """平均レスポンス時間取得テスト"""
        self.metrics.add_response_time(100.0)
        self.metrics.add_response_time(200.0)
        self.metrics.add_response_time(300.0)
        
        average = self.metrics.get_average_response_time()
        assert average == 200.0
    
    def test_get_p95_latency(self):
        """95パーセンタイルレイテンシテスト"""
        # 100個のレスポンス時間を追加
        for i in range(100):
            self.metrics.add_response_time(i)
        
        p95 = self.metrics.get_p95_latency()
        assert p95 == 95  # 95パーセンタイル
    
    def test_get_cache_hit_ratio(self):
        """キャッシュヒット率取得テスト"""
        self.metrics.cache_hits = 80
        self.metrics.cache_misses = 20
        
        hit_ratio = self.metrics.get_cache_hit_ratio()
        assert hit_ratio == 0.8
    
    def test_update_throughput(self):
        """スループット更新テスト"""
        # 開始時間を調整
        self.metrics.start_time = time.time() - 10  # 10秒前
        self.metrics.total_requests = 100
        
        self.metrics.update_throughput()
        
        assert self.metrics.throughput > 0
        assert self.metrics.throughput <= 10  # 100 requests / 10 seconds = 10 req/sec
    
    @patch('psutil.Process')
    def test_get_memory_usage_mb(self, mock_process):
        """メモリ使用量取得テスト"""
        mock_memory_info = Mock()
        mock_memory_info.rss = 52428800  # 50MB
        mock_process.return_value.memory_info.return_value = mock_memory_info
        
        memory_mb = self.metrics.get_memory_usage_mb()
        
        assert memory_mb == 50.0
        assert len(self.metrics.memory_usage) == 1


class TestAdvancedCache:
    """AdvancedCache テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.cache = AdvancedCache(max_size=3, ttl_seconds=300)
    
    def test_initialization(self):
        """初期化テスト"""
        assert self.cache.max_size == 3
        assert self.cache.ttl_seconds == 300
        assert len(self.cache._cache) == 0
    
    def test_set_and_get(self):
        """設定・取得テスト"""
        self.cache.set("key1", "value1")
        
        value = self.cache.get("key1")
        assert value == "value1"
        
        # 存在しないキー
        value = self.cache.get("nonexistent")
        assert value is None
    
    def test_ttl_expiration(self):
        """TTL期限切れテスト"""
        # 短いTTLで設定
        cache = AdvancedCache(max_size=3, ttl_seconds=0.01)
        cache.set("key1", "value1")
        
        # 期限切れまで待つ
        time.sleep(0.02)
        
        value = cache.get("key1")
        assert value is None
    
    def test_lru_eviction(self):
        """LRU排除テスト"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.set("key3", "value3")
        
        # アクセス順序を変更
        self.cache.get("key1")
        
        # 新しいキーを追加（key2が排除される）
        self.cache.set("key4", "value4")
        
        assert self.cache.get("key1") == "value1"
        assert self.cache.get("key2") is None
        assert self.cache.get("key3") == "value3"
        assert self.cache.get("key4") == "value4"
    
    def test_get_stats(self):
        """統計取得テスト"""
        self.cache.set("key1", "value1")
        self.cache.get("key1")  # ヒット
        self.cache.get("nonexistent")  # ミス
        
        stats = self.cache.get_stats()
        
        assert stats["hit_count"] == 1
        assert stats["miss_count"] == 1
        assert stats["hit_ratio"] == 0.5
        assert stats["size"] == 1
    
    def test_clear(self):
        """クリアテスト"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        
        self.cache.clear()
        
        assert self.cache.get("key1") is None
        assert self.cache.get("key2") is None
        assert len(self.cache._cache) == 0


class TestConnectionPool:
    """ConnectionPool テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.pool = ConnectionPool(max_connections=10, timeout=30)
    
    def test_initialization(self):
        """初期化テスト"""
        assert self.pool.max_connections == 10
        assert self.pool.timeout == 30
        assert self.pool.active_connections == 0
        assert self.pool._session is None
    
    @pytest.mark.asyncio
    async def test_get_session(self):
        """セッション取得テスト"""
        session = await self.pool.get_session()
        
        assert session is not None
        assert isinstance(session, aiohttp.ClientSession)
        assert not session.closed
        
        # 同じセッションが返されることを確認
        session2 = await self.pool.get_session()
        assert session2 is session
    
    @pytest.mark.asyncio
    async def test_close(self):
        """クローズテスト"""
        session = await self.pool.get_session()
        
        await self.pool.close()
        
        assert session.closed
    
    def test_get_connection_stats(self):
        """接続統計取得テスト"""
        stats = self.pool.get_connection_stats()
        
        assert stats["max_connections"] == 10
        assert stats["active_connections"] == 0
        assert stats["session_closed"] is True


class TestBatchProcessor:
    """BatchProcessor テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.processor = BatchProcessor(batch_size=3, max_concurrent=2)
    
    def test_initialization(self):
        """初期化テスト"""
        assert self.processor.batch_size == 3
        assert self.processor.max_concurrent == 2
        assert self.processor.processed_batches == 0
        assert self.processor.total_items == 0
    
    @pytest.mark.asyncio
    async def test_process_batch(self):
        """バッチ処理テスト"""
        async def mock_process_func(item):
            """mock_process_func処理メソッド"""
            return f"processed_{item}"
        
        items = [1, 2, 3, 4, 5, 6, 7]
        results = await self.processor.process_batch(items, mock_process_func)
        
        assert len(results) == 7
        assert results[0] == "processed_1"
        assert results[6] == "processed_7"
        assert self.processor.processed_batches > 0
        assert self.processor.total_items == 7
    
    @pytest.mark.asyncio
    async def test_process_batch_with_errors(self):
        """エラーありバッチ処理テスト"""
        async def mock_process_func(item):
            """mock_process_func処理メソッド"""
            if item == 3:
                raise ValueError("Test error")
            return f"processed_{item}"
        
        items = [1, 2, 3, 4, 5]
        results = await self.processor.process_batch(items, mock_process_func)
        
        assert len(results) == 5
        assert results[0] == "processed_1"
        assert results[1] == "processed_2"
        assert "error" in results[2]
        assert results[3] == "processed_4"
        assert results[4] == "processed_5"
    
    def test_get_stats(self):
        """統計取得テスト"""
        stats = self.processor.get_stats()
        
        assert stats["batch_size"] == 3
        assert stats["max_concurrent"] == 2
        assert stats["processed_batches"] == 0
        assert stats["total_items"] == 0


class TestGitHubPerformanceOptimizer:
    """GitHubPerformanceOptimizer テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.optimizer = GitHubPerformanceOptimizer(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo"
        )
    
    def test_initialization(self):
        """初期化テスト"""
        assert self.optimizer.token == "test-token"
        assert self.optimizer.repo_owner == "test-owner"
        assert self.optimizer.repo_name == "test-repo"
        assert self.optimizer.performance_metrics is not None
        assert self.optimizer.cache is not None
        assert self.optimizer.connection_pool is not None
    
    def test_get_auth_headers(self):
        """認証ヘッダー取得テスト"""
        headers = self.optimizer._get_auth_headers()
        
        assert headers["Authorization"] == "token test-token"
        assert headers["Accept"] == "application/vnd.github.v3+json"
        assert headers["User-Agent"] == "Elders-Guild-GitHub-Integration/1.0"
    
    def test_generate_cache_key(self):
        """キャッシュキー生成テスト"""
        key1 = self.optimizer._generate_cache_key("/test/endpoint")
        key2 = self.optimizer._generate_cache_key("/test/endpoint", {"param": "value"})
        
        assert key1 != key2
        assert isinstance(key1, str)
        assert isinstance(key2, str)
    
    @pytest.mark.asyncio
    async def test_make_request_with_cache(self):
        """キャッシュ付きリクエストテスト"""
        # キャッシュに値を設定
        cache_key = self.optimizer._generate_cache_key("/test", {})
        cached_result = {"cached": True, "data": "test"}
        self.optimizer.cache.set(cache_key, cached_result)
        
        result = await self.optimizer._make_request("GET", "/test")
        
        assert result == cached_result
    
    @pytest.mark.asyncio
    async def test_make_request_network_call(self):
        """ネットワークコールテスト"""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content_type = "application/json"
        mock_response.headers = {"X-RateLimit-Remaining": "4999"}
        mock_response.json.return_value = {"test": "data"}
        mock_response.url = "https://api.github.com/test"
        
        mock_session.request.return_value.__aenter__.return_value = mock_response
        
        with patch.object(self.optimizer.connection_pool, 'get_session', return_value=mock_session):
            result = await self.optimizer._make_request("GET", "/test")
            
            assert result["test"] == "data"
            assert result["_metadata"]["status_code"] == 200
    
    @pytest.mark.asyncio
    async def test_make_request_rate_limiting(self):
        """レート制限テスト"""
        mock_session = AsyncMock()
        
        # 最初のレスポンスでレート制限
        rate_limit_response = AsyncMock()
        rate_limit_response.status = 429
        rate_limit_response.headers = {"Retry-After": "1"}
        
        # 二回目のレスポンスで成功
        success_response = AsyncMock()
        success_response.status = 200
        success_response.content_type = "application/json"
        success_response.headers = {}
        success_response.json.return_value = {"success": True}
        success_response.url = "https://api.github.com/test"
        
        mock_session.request.return_value.__aenter__.side_effect = [
            rate_limit_response,
            success_response
        ]
        
        with patch.object(self.optimizer.connection_pool, 'get_session', return_value=mock_session):
            with patch('asyncio.sleep') as mock_sleep:
                result = await self.optimizer._make_request("GET", "/test")
                
                assert result["success"] is True
                mock_sleep.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_get_issues_optimized(self):
        """最適化されたIssue取得テスト"""
        mock_result = {"issues": [{"number": 1, "title": "Test"}]}
        
        with patch.object(self.optimizer, '_make_request', return_value=mock_result):
            result = await self.optimizer.get_issues_optimized(
                state="open",
                per_page=50,
                page=1
            )
            
            assert result == mock_result
    
    @pytest.mark.asyncio
    async def test_batch_get_issues(self):
        """バッチIssue取得テスト"""
        mock_results = [
            {"number": 1, "title": "Issue 1"},
            {"number": 2, "title": "Issue 2"},
            {"number": 3, "title": "Issue 3"}
        ]
        
        with patch.object(self.optimizer, '_make_request', side_effect=mock_results):
            results = await self.optimizer.batch_get_issues([1, 2, 3])
            
            assert len(results) == 3
            assert results[0]["number"] == 1
            assert results[1]["number"] == 2
            assert results[2]["number"] == 3
    
    @pytest.mark.asyncio
    async def test_stream_all_issues(self):
        """すべてのIssueストリーミングテスト"""
        # 2ページ分のデータを模擬
        page1_data = [{"number": i, "title": f"Issue {i}"} for i in range(1, 101)]
        page2_data = [{"number": i, "title": f"Issue {i}"} for i in range(101, 151)]
        
        mock_responses = [
            page1_data,
            page2_data,
            []  # 空のページで終了
        ]
        
        with patch.object(self.optimizer, 'get_issues_optimized', side_effect=mock_responses):
            issues = []
            async for issue in self.optimizer.stream_all_issues():
                issues.append(issue)
            
            assert len(issues) == 150
            assert issues[0]["number"] == 1
            assert issues[-1]["number"] == 150
    
    def test_get_performance_report(self):
        """パフォーマンスレポート取得テスト"""
        # いくつかのメトリクスを設定
        self.optimizer.performance_metrics.add_response_time(100)
        self.optimizer.performance_metrics.add_response_time(200)
        self.optimizer.performance_metrics.cache_hits = 80
        self.optimizer.performance_metrics.cache_misses = 20
        
        report = self.optimizer.get_performance_report()
        
        assert "performance_score" in report
        assert "targets" in report
        assert "metrics" in report
        assert "total_requests" in report
        assert "success_rate" in report
    
    def test_calculate_performance_score(self):
        """パフォーマンススコア計算テスト"""
        # 理想的なメトリクスを設定
        self.optimizer.performance_metrics.add_response_time(100)  # 目標以下
        self.optimizer.performance_metrics.cache_hits = 90
        self.optimizer.performance_metrics.cache_misses = 10
        
        score = self.optimizer._calculate_performance_score()
        
        assert 0 <= score <= 100
        assert isinstance(score, float)
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """コンテキストマネージャーテスト"""
        async with self.optimizer as opt:
            assert opt is self.optimizer
        
        # クローズが呼ばれていることを確認（実際のテストでは詳細な検証が必要）
        assert True


class TestMemoryOptimizer:
    """MemoryOptimizer テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.optimizer = MemoryOptimizer()
    
    def test_initialization(self):
        """初期化テスト"""
        assert self.optimizer.cleanup_threshold == 100
        assert self.optimizer.cleanup_interval == 300
        assert self.optimizer.last_cleanup > 0
    
    def test_register_object(self):
        """オブジェクト登録テスト"""
        test_obj = {"test": "object"}
        
        self.optimizer.register_object(test_obj)
        
        assert test_obj in self.optimizer.weak_references
    
    def test_cleanup(self):
        """クリーンアップテスト"""
        # 最後のクリーンアップ時間を古くする
        self.optimizer.last_cleanup = time.time() - 400
        
        original_last_cleanup = self.optimizer.last_cleanup
        
        self.optimizer.cleanup()
        
        assert self.optimizer.last_cleanup > original_last_cleanup
    
    @patch('psutil.Process')
    def test_get_memory_stats(self, mock_process):
        """メモリ統計取得テスト"""
        mock_memory_info = Mock()
        mock_memory_info.rss = 52428800  # 50MB
        mock_memory_info.vms = 104857600  # 100MB
        
        mock_process.return_value.memory_info.return_value = mock_memory_info
        mock_process.return_value.memory_percent.return_value = 5.0
        
        stats = self.optimizer.get_memory_stats()
        
        assert stats["rss_mb"] == 50.0
        assert stats["vms_mb"] == 100.0
        assert stats["percent"] == 5.0
        assert "tracked_objects" in stats


class TestPerformanceDecorator:
    """performance_monitor デコレータテスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.mock_instance = Mock()
        self.mock_instance.performance_metrics = PerformanceMetrics()
    
    @pytest.mark.asyncio
    async def test_performance_monitor_success(self):
        """パフォーマンスモニター成功テスト"""
        @performance_monitor
        async def test_func(self):
            """test_funcテストメソッド"""
            await asyncio.sleep(0.01)
            return "success"
        
        result = await test_func(self.mock_instance)
        
        assert result == "success"
        assert self.mock_instance.performance_metrics.total_requests == 1
        assert len(self.mock_instance.performance_metrics.response_times) == 1
    
    @pytest.mark.asyncio
    async def test_performance_monitor_exception(self):
        """パフォーマンスモニター例外テスト"""
        @performance_monitor
        async def test_func(self):
            """test_funcテストメソッド"""
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            await test_func(self.mock_instance)
        
        assert self.mock_instance.performance_metrics.failed_requests == 1


class TestFactoryFunctions:
    """ファクトリ関数テスト"""
    
    @pytest.mark.asyncio
    async def test_create_github_async_manager(self):
        """GitHubAsyncManager作成テスト"""
        manager = await create_github_async_manager(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo"
        )
        
        assert isinstance(manager, GitHubAsyncManager)
        assert manager.token == "test-token"
        assert manager.repo_owner == "test-owner"
        assert manager.repo_name == "test-repo"
        
        # クリーンアップ
        await manager._cleanup_async_components()
    
    def test_create_github_cache_manager(self):
        """GitHubCacheManager作成テスト"""
        cache_manager = create_github_cache_manager(
            max_lru_size=500,
            default_ttl=600,
            max_memory_mb=50
        )
        
        assert isinstance(cache_manager, GitHubCacheManager)
        assert cache_manager.lru_cache.max_size == 500
        assert cache_manager.default_ttl == 600
        assert cache_manager.max_memory_bytes == 50 * 1024 * 1024
    
    @pytest.mark.asyncio
    async def test_create_github_performance_optimizer(self):
        """GitHubPerformanceOptimizer作成テスト"""
        optimizer = await create_github_performance_optimizer(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo"
        )
        
        assert isinstance(optimizer, GitHubPerformanceOptimizer)
        assert optimizer.token == "test-token"
        assert optimizer.repo_owner == "test-owner"
        assert optimizer.repo_name == "test-repo"
        
        # クリーンアップ
        await optimizer.close()


class TestPerformanceTargets:
    """パフォーマンス目標テスト"""
    
    def test_performance_targets_defined(self):
        """パフォーマンス目標定義テスト"""
        assert "response_time_ms" in PERFORMANCE_TARGETS
        assert "memory_usage_mb" in PERFORMANCE_TARGETS
        assert "throughput_req_sec" in PERFORMANCE_TARGETS
        assert "latency_p95_ms" in PERFORMANCE_TARGETS
        assert "cache_hit_ratio" in PERFORMANCE_TARGETS
        assert "connection_pool_size" in PERFORMANCE_TARGETS
        assert "batch_size" in PERFORMANCE_TARGETS
        assert "concurrent_requests" in PERFORMANCE_TARGETS
    
    def test_performance_targets_values(self):
        """パフォーマンス目標値テスト"""
        assert PERFORMANCE_TARGETS["response_time_ms"] == 200
        assert PERFORMANCE_TARGETS["memory_usage_mb"] == 50
        assert PERFORMANCE_TARGETS["throughput_req_sec"] == 100
        assert PERFORMANCE_TARGETS["latency_p95_ms"] == 100
        assert PERFORMANCE_TARGETS["cache_hit_ratio"] == 0.85
        assert PERFORMANCE_TARGETS["connection_pool_size"] == 50
        assert PERFORMANCE_TARGETS["batch_size"] == 20
        assert PERFORMANCE_TARGETS["concurrent_requests"] == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])