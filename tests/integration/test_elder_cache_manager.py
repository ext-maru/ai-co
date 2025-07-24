"""
🧪 Elder Cache Manager TDDテストスイート
Phase 3 パフォーマンス最適化：キャッシングシステムテスト

TDD Red-Green-Refactor サイクルによる品質保証
Iron Will品質基準95%達成必須
"""

import pytest
import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from libs.elder_servants.integrations.performance.cache_manager import (
    ElderCacheManager,
    CacheStrategy,
    CacheKeyType,
    CacheRequest,
    CacheResponse,
    CacheStats,
    get_cache_manager,
    cache_quality_check_result,
    get_cached_quality_check,
    cache_sage_consultation,
    get_cached_sage_consultation
)


class TestElderCacheManager:
    """Elder Cache Manager 基本機能テスト"""
    
    @pytest.fixture
    async def cache_manager(self):
        """テスト用キャッシュマネージャー"""
        manager = ElderCacheManager(
            redis_url="redis://localhost:6379",
            strategy=CacheStrategy.BALANCED
        )
        yield manager
        await manager.close()
    
    @pytest.fixture
    def sample_cache_request(self):
        """サンプルキャッシュリクエスト"""
        return CacheRequest(
            key_type=CacheKeyType.QUALITY_CHECK,
            data={"file_hash": "abc123", "check_type": "syntax"},
            ttl_seconds=3600,
            strategy=CacheStrategy.BALANCED
        )
    
    def test_cache_manager_initialization(self, cache_manager):
        """キャッシュマネージャー初期化テスト"""
        assert cache_manager.strategy == CacheStrategy.BALANCED
        assert cache_manager.quality_threshold == 95.0
        assert cache_manager.config["default_ttl"] == 3600
        assert isinstance(cache_manager.stats, CacheStats)
    
    def test_cache_key_generation(self, cache_manager):
        """キャッシュキー生成テスト"""
        data = {"file_hash": "test123", "check_type": "syntax"}
        key = cache_manager._generate_cache_key(CacheKeyType.QUALITY_CHECK, data)
        
        assert key.startswith("elder:quality_check:")
        assert len(key) <= cache_manager.config["max_key_length"]
        
        # 同じデータで同じキーが生成されることを確認
        key2 = cache_manager._generate_cache_key(CacheKeyType.QUALITY_CHECK, data)
        assert key == key2
    
    def test_ttl_strategy_mapping(self, cache_manager):
        """TTL戦略マッピングテスト"""
        # QUALITY_CHECK のTTL取得
        ttl = cache_manager._get_ttl_for_key_type(CacheKeyType.QUALITY_CHECK)
        expected_ttl = cache_manager.ttl_strategies[CacheKeyType.QUALITY_CHECK][CacheStrategy.BALANCED]
        assert ttl == expected_ttl
        
        # 未定義キータイプのデフォルトTTL
        cache_manager.strategy = CacheStrategy.AGGRESSIVE
        ttl_default = cache_manager._get_ttl_for_key_type(CacheKeyType.PERFORMANCE_METRIC)
        assert ttl_default == cache_manager.config["default_ttl"]
    
    def test_request_validation(self, cache_manager, sample_cache_request):
        """リクエスト検証テスト"""
        # 正常なリクエスト
        assert cache_manager.validate_request(sample_cache_request)
        
        # 不正なキータイプ
        invalid_request = CacheRequest(
            key_type="invalid_type",  # type: ignore
            data={"test": "data"},
            ttl_seconds=3600
        )
        assert not cache_manager.validate_request(invalid_request)
        
        # 不正なデータ
        invalid_data_request = CacheRequest(
            key_type=CacheKeyType.QUALITY_CHECK,
            data="not_a_dict",  # type: ignore
            ttl_seconds=3600
        )
        assert not cache_manager.validate_request(invalid_data_request)
        
        # 負のTTL
        negative_ttl_request = CacheRequest(
            key_type=CacheKeyType.QUALITY_CHECK,
            data={"test": "data"},
            ttl_seconds=-1
        )
        assert not cache_manager.validate_request(negative_ttl_request)
    
    def test_capabilities(self, cache_manager):
        """能力一覧テスト"""
        capabilities = cache_manager.get_capabilities()
        expected_capabilities = [
            "intelligent_caching",
            "performance_optimization", 
            "ttl_management",
            "cache_statistics",
            "memory_management",
            "redis_integration"
        ]
        
        for capability in expected_capabilities:
            assert capability in capabilities
    
    @pytest.mark.asyncio
    async def test_redis_connection_failure_fallback(self):
        """Redis接続失敗フォールバックテスト"""
        # 無効なRedis URLでテスト
        cache_manager = ElderCacheManager(redis_url="redis://invalid:9999")
        
        # 接続確保試行（失敗が期待される）
        await cache_manager._ensure_redis_connection()
        
        # Redis接続がNoneになることを確認
        assert cache_manager.redis_client is None
        
        await cache_manager.close()
    
    @pytest.mark.asyncio
    async def test_cache_miss_and_set(self, cache_manager, sample_cache_request):
        """キャッシュミス時の設定テスト"""
        with patch.object(cache_manager, '_get_from_cache', return_value=None):
            with patch.object(cache_manager, '_set_to_cache') as mock_set:
                response = await cache_manager.process_request(sample_cache_request)
                
                assert response.success
                assert not response.cached
                assert response.data == sample_cache_request.data
                assert cache_manager.stats.cache_misses == 1
                mock_set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, cache_manager, sample_cache_request):
        """キャッシュヒットテスト"""
        cached_data = {"cached": True, "result": "success"}
        
        with patch.object(cache_manager, '_get_from_cache', return_value=cached_data):
            response = await cache_manager.process_request(sample_cache_request)
            
            assert response.success
            assert response.cached
            assert response.data == cached_data
            assert cache_manager.stats.cache_hits == 1
    
    @pytest.mark.asyncio
    async def test_cache_error_handling(self, cache_manager, sample_cache_request):
        """キャッシュエラーハンドリングテスト"""
        with patch.object(cache_manager, '_get_from_cache', side_effect=Exception("Redis error")):
            response = await cache_manager.process_request(sample_cache_request)
            
            assert not response.success
            assert response.error_message == "Redis error"
            assert cache_manager.stats.errors == 1


class TestCacheStrategies:
    """キャッシュ戦略テスト"""
    
    @pytest.mark.asyncio
    async def test_aggressive_strategy(self):
        """積極的キャッシュ戦略テスト"""
        cache_manager = ElderCacheManager(strategy=CacheStrategy.AGGRESSIVE)
        
        # 長いTTLが設定されることを確認
        ttl = cache_manager._get_ttl_for_key_type(CacheKeyType.QUALITY_CHECK)
        expected_ttl = cache_manager.ttl_strategies[CacheKeyType.QUALITY_CHECK][CacheStrategy.AGGRESSIVE]
        assert ttl == expected_ttl
        assert ttl > cache_manager.ttl_strategies[CacheKeyType.QUALITY_CHECK][CacheStrategy.BALANCED]
        
        await cache_manager.close()
    
    @pytest.mark.asyncio
    async def test_conservative_strategy(self):
        """保守的キャッシュ戦略テスト"""
        cache_manager = ElderCacheManager(strategy=CacheStrategy.CONSERVATIVE)
        
        # 短いTTLが設定されることを確認
        ttl = cache_manager._get_ttl_for_key_type(CacheKeyType.QUALITY_CHECK)
        expected_ttl = cache_manager.ttl_strategies[CacheKeyType.QUALITY_CHECK][CacheStrategy.CONSERVATIVE]
        assert ttl == expected_ttl
        assert ttl < cache_manager.ttl_strategies[CacheKeyType.QUALITY_CHECK][CacheStrategy.BALANCED]
        
        await cache_manager.close()
    
    def test_cache_key_strategy_differences(self):
        """戦略別キャッシュキー差異テスト"""
        data = {"file_hash": "test123", "check_type": "syntax"}
        
        aggressive_manager = ElderCacheManager(strategy=CacheStrategy.AGGRESSIVE)
        conservative_manager = ElderCacheManager(strategy=CacheStrategy.CONSERVATIVE)
        
        aggressive_key = aggressive_manager._generate_cache_key(CacheKeyType.QUALITY_CHECK, data)
        conservative_key = conservative_manager._generate_cache_key(CacheKeyType.QUALITY_CHECK, data)
        
        # 保守的戦略では時間要素が含まれるため、キーが異なる可能性がある
        # （実際の時間によって変わるため、基本構造のみチェック）
        assert aggressive_key.startswith("elder:quality_check:")
        assert conservative_key.startswith("elder:quality_check:")


class TestQualityCheckCaching:
    """品質チェックキャッシュテスト"""
    
    @pytest.fixture
    async def cache_manager(self):
        """テスト用キャッシュマネージャー"""
        manager = ElderCacheManager(strategy=CacheStrategy.BALANCED)
        yield manager
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_quality_check_cache_set_get(self, cache_manager):
        """品質チェックキャッシュ設定・取得テスト"""
        file_hash = "abc123def456"
        check_type = "syntax"
        result = {"score": 95.5, "issues": [], "passed": True}
        
        with patch.object(cache_manager, '_set_to_cache') as mock_set:
            with patch.object(cache_manager, '_get_from_cache', return_value=None):
                # キャッシュ設定
                success = await cache_manager.set_quality_check_cache(file_hash, check_type, result)
                assert success
                mock_set.assert_called_once()
        
        # 設定されたデータを取得
        with patch.object(cache_manager, '_get_from_cache', return_value={
            "file_hash": file_hash,
            "check_type": check_type,
            "result": result
        }):
            cached_result = await cache_manager.get_quality_check_cache(file_hash, check_type)
            assert cached_result is not None
            assert cached_result["result"] == result
    
    @pytest.mark.asyncio
    async def test_quality_check_cache_miss(self, cache_manager):
        """品質チェックキャッシュミステスト"""
        with patch.object(cache_manager, '_get_from_cache', return_value=None):
            result = await cache_manager.get_quality_check_cache("nonexistent", "syntax")
            assert result is None


class TestSageConsultationCaching:
    """4賢者相談キャッシュテスト"""
    
    @pytest.fixture
    async def cache_manager(self):
        """テスト用キャッシュマネージャー"""
        manager = ElderCacheManager(strategy=CacheStrategy.BALANCED)
        yield manager
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_sage_consultation_cache_set_get(self, cache_manager):
        """4賢者相談キャッシュ設定・取得テスト"""
        sage_type = "knowledge"
        context = {"query": "optimization strategy", "priority": "high"}
        result = {"recommendation": "use aggressive caching", "confidence": 0.95}
        
        with patch.object(cache_manager, '_set_to_cache') as mock_set:
            with patch.object(cache_manager, '_get_from_cache', return_value=None):
                # キャッシュ設定
                success = await cache_manager.set_sage_consultation_cache(sage_type, context, result)
                assert success
                mock_set.assert_called_once()
        
        # 設定されたデータを取得
        with patch.object(cache_manager, '_get_from_cache', return_value={
            "sage_type": sage_type,
            "context": context,
            "result": result
        }):
            cached_result = await cache_manager.get_sage_consultation_cache(sage_type, context)
            assert cached_result is not None
            assert cached_result == result


class TestCacheStatistics:
    """キャッシュ統計テスト"""
    
    @pytest.fixture
    async def cache_manager(self):
        """テスト用キャッシュマネージャー"""
        manager = ElderCacheManager(strategy=CacheStrategy.BALANCED)
        yield manager
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_cache_statistics_calculation(self, cache_manager):
        """キャッシュ統計計算テスト"""
        # 統計を手動設定してテスト
        cache_manager.stats.total_requests = 100
        cache_manager.stats.cache_hits = 75
        cache_manager.stats.cache_misses = 20
        cache_manager.stats.errors = 5
        
        with patch.object(cache_manager, 'redis_client') as mock_redis:
            mock_redis.info.return_value = {
                "used_memory": 1024000,
                "used_memory_human": "1.0M",
                "maxmemory": 0
            }
            
            stats = await cache_manager.get_cache_statistics()
            
            assert stats["cache_stats"]["total_requests"] == 100
            assert stats["cache_stats"]["cache_hits"] == 75
            assert stats["cache_stats"]["hit_rate_percent"] == 75.0
            assert stats["iron_will_compliance"] is True  # 75% > 70%
    
    @pytest.mark.asyncio
    async def test_low_hit_rate_iron_will_violation(self, cache_manager):
        """低ヒット率でのIron Will違反テスト"""
        # 低いヒット率を設定
        cache_manager.stats.total_requests = 100
        cache_manager.stats.cache_hits = 60  # 60% < 70%
        cache_manager.stats.cache_misses = 40
        
        with patch.object(cache_manager, 'redis_client') as mock_redis:
            mock_redis.info.return_value = {}
            
            stats = await cache_manager.get_cache_statistics()
            
            assert stats["cache_stats"]["hit_rate_percent"] == 60.0
            assert stats["iron_will_compliance"] is False  # 60% < 70%


class TestCacheInvalidation:
    """キャッシュ無効化テスト"""
    
    @pytest.fixture
    async def cache_manager(self):
        """テスト用キャッシュマネージャー"""
        manager = ElderCacheManager(strategy=CacheStrategy.BALANCED)
        yield manager
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_cache_pattern_invalidation(self, cache_manager):
        """パターンマッチキャッシュ無効化テスト"""
        with patch.object(cache_manager, 'redis_client') as mock_redis:
            mock_redis.keys.return_value = [
                "elder:quality_check:abc123",
                "elder:quality_check:def456"
            ]
            mock_redis.delete.return_value = 2
            
            deleted_count = await cache_manager.invalidate_cache_pattern("quality_check:*")
            
            assert deleted_count == 2
            mock_redis.keys.assert_called_once_with("elder:quality_check:*")
            mock_redis.delete.assert_called_once()


class TestHealthCheck:
    """ヘルスチェックテスト"""
    
    @pytest.fixture
    async def cache_manager(self):
        """テスト用キャッシュマネージャー"""
        manager = ElderCacheManager(strategy=CacheStrategy.BALANCED)
        yield manager
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_healthy_cache_manager(self, cache_manager):
        """健全なキャッシュマネージャーヘルスチェック"""
        # 良好な統計を設定
        cache_manager.stats.total_requests = 100
        cache_manager.stats.cache_hits = 80
        cache_manager.stats.errors = 2
        
        with patch.object(cache_manager, 'redis_client') as mock_redis:
            mock_redis.ping = AsyncMock()
            
            health = await cache_manager.health_check()
            
            assert health["success"]
            assert health["status"] == "healthy"
            assert health["redis_connection"] is True
            assert health["iron_will_compliant"] is True
    
    @pytest.mark.asyncio
    async def test_degraded_cache_manager(self, cache_manager):
        """性能低下キャッシュマネージャーヘルスチェック"""
        # 低いヒット率を設定
        cache_manager.stats.total_requests = 100
        cache_manager.stats.cache_hits = 50  # 50% < 70%
        cache_manager.stats.errors = 10     # 10% > 5%
        
        with patch.object(cache_manager, 'redis_client') as mock_redis:
            mock_redis.ping = AsyncMock()
            
            health = await cache_manager.health_check()
            
            assert health["success"]
            assert health["status"] == "degraded"
            assert health["iron_will_compliant"] is False


class TestConvenienceFunctions:
    """便利関数テスト"""
    
    @pytest.mark.asyncio
    async def test_global_cache_manager_singleton(self):
        """グローバルキャッシュマネージャーシングルトンテスト"""
        manager1 = await get_cache_manager()
        manager2 = await get_cache_manager()
        
        # 同じインスタンスが返されることを確認
        assert manager1 is manager2
        
        await manager1.close()
    
    @pytest.mark.asyncio
    async def test_convenience_quality_check_functions(self):
        """品質チェック便利関数テスト"""
        with patch('libs.elder_servants.integrations.performance.cache_manager.get_cache_manager') as mock_get_manager:
            mock_manager = AsyncMock()
            mock_manager.set_quality_check_cache.return_value = True
            mock_manager.get_quality_check_cache.return_value = {"score": 95}
            mock_get_manager.return_value = mock_manager
            
            # 設定関数テスト
            result = await cache_quality_check_result("hash123", "syntax", {"score": 95})
            assert result is True
            
            # 取得関数テスト
            cached = await get_cached_quality_check("hash123", "syntax")
            assert cached == {"score": 95}
    
    @pytest.mark.asyncio
    async def test_convenience_sage_consultation_functions(self):
        """4賢者相談便利関数テスト"""
        with patch('libs.elder_servants.integrations.performance.cache_manager.get_cache_manager') as mock_get_manager:
            mock_manager = AsyncMock()
            mock_manager.set_sage_consultation_cache.return_value = True
            mock_manager.get_sage_consultation_cache.return_value = {"advice": "optimize"}
            mock_get_manager.return_value = mock_manager
            
            # 設定関数テスト
            result = await cache_sage_consultation("knowledge", {"query": "test"}, {"advice": "optimize"})
            assert result is True
            
            # 取得関数テスト
            cached = await get_cached_sage_consultation("knowledge", {"query": "test"})
            assert cached == {"advice": "optimize"}


class TestIronWillCompliance:
    """Iron Will品質基準遵守テスト"""
    
    @pytest.mark.asyncio
    async def test_iron_will_performance_requirement(self):
        """Iron Willパフォーマンス要件テスト"""
        cache_manager = ElderCacheManager(strategy=CacheStrategy.BALANCED)
        
        request = CacheRequest(
            key_type=CacheKeyType.QUALITY_CHECK,
            data={"test": "data"},
            ttl_seconds=3600
        )
        
        with patch.object(cache_manager, '_get_from_cache', return_value={"cached": "data"}):
            start_time = time.time()
            response = await cache_manager.process_request(request)
            elapsed_time = time.time() - start_time
            
            # レスポンス時間が100ms以下であることを確認（パフォーマンス要件）
            assert elapsed_time < 0.1
            assert response.execution_time_ms < 100
        
        await cache_manager.close()
    
    @pytest.mark.asyncio
    async def test_iron_will_error_handling_requirement(self):
        """Iron Willエラーハンドリング要件テスト"""
        cache_manager = ElderCacheManager(strategy=CacheStrategy.BALANCED)
        
        request = CacheRequest(
            key_type=CacheKeyType.QUALITY_CHECK,
            data={"test": "data"},
            ttl_seconds=3600
        )
        
        # エラーが発生してもレスポンスが返されることを確認
        with patch.object(cache_manager, '_get_from_cache', side_effect=Exception("Test error")):
            response = await cache_manager.process_request(request)
            
            assert not response.success
            assert response.error_message == "Test error"
            assert isinstance(response.execution_time_ms, float)
        
        await cache_manager.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])