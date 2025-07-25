#!/usr/bin/env python3
"""
4賢者統合システム完全版テスト
"""

import asyncio
import pytest
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from elders_guild.elder_tree.four_sages_integration_complete import FourSagesIntegrationComplete


class TestFourSagesIntegrationComplete:
    """4賢者統合システム完全版テスト"""
    
    @pytest.fixture
    async def integration(self):
        """統合システムフィクスチャ"""
        system = FourSagesIntegrationComplete()
        await system.initialize()
        yield system
        await system.cleanup()
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """初期化テスト"""
        system = FourSagesIntegrationComplete()
        result = await system.initialize()
        
        assert result["status"] == "success"
        assert result["system_status"] == "operational"
        assert "initialization_time" in result
        assert result["sages_active"]["knowledge"] is True
        assert result["sages_active"]["task"] is True
        assert result["sages_active"]["incident"] is True
        assert result["sages_active"]["rag"] is True
        
        await system.cleanup()
    
    @pytest.mark.asyncio
    async def test_consult_all_sages(self, integration):
        """全賢者相談テスト"""
        result = await integration.consult_all_sages(
            "新機能を実装する最適な方法は？",
            {"priority": "high"}
        )
        
        assert result["success"] is True
        assert "recommendations" in result
        assert len(result["recommendations"]) >= 4  # 4賢者分
        assert "response_time" in result
        assert result["consensus_reached"] is True
    
    @pytest.mark.asyncio
    async def test_execute_with_sages(self, integration):
        """賢者と共に実行テスト"""
        result = await integration.execute_with_sages(
            "ユーザー認証システムの実装"
        )
        
        assert result["success"] is True
        assert "execution_plan" in result
        assert "steps" in result["execution_plan"]
        assert len(result["execution_plan"]["steps"]) > 0
        assert "results" in result
    
    @pytest.mark.asyncio
    async def test_get_system_status(self, integration):
        """システムステータス取得テスト"""
        status = await integration.get_system_status()
        
        assert status["system_status"] == "operational"
        assert "sages_status" in status
        assert status["sages_status"]["knowledge"]["active"] is True
        assert status["sages_status"]["task"]["active"] is True
        assert status["sages_status"]["incident"]["active"] is True
        assert status["sages_status"]["rag"]["active"] is True
        assert "metrics" in status
        assert status["collaboration_active"] is True
    
    @pytest.mark.asyncio
    async def test_optimize_system(self, integration):
        """システム最適化テスト"""
        result = await integration.optimize_system()
        
        assert "timestamp" in result
        assert "optimizations" in result
        assert len(result["optimizations"]) > 0
        assert "system_health" in result
        
        # 最適化タイプ確認
        opt_types = [opt["type"] for opt in result["optimizations"]]
        assert "memory" in opt_types
        assert "cache" in opt_types
        assert "collaboration" in opt_types
    
    @pytest.mark.asyncio
    async def test_metrics_update(self, integration):
        """メトリクス更新テスト"""
        # 初期状態
        initial_metrics = integration.metrics.copy()
        
        # 相談実行
        await integration.consult_all_sages("テストクエリ")
        
        # メトリクス確認
        assert integration.metrics["consultations"] > initial_metrics["consultations"]
        assert integration.metrics["successful_consultations"] >= initial_metrics["successful_consultations"]
        assert integration.metrics["sage_usage"]["knowledge"] > 0
        assert integration.metrics["sage_usage"]["task"] > 0
        assert integration.metrics["sage_usage"]["incident"] > 0
        assert integration.metrics["sage_usage"]["rag"] > 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """エラーハンドリングテスト"""
        system = FourSagesIntegrationComplete()
        # 初期化前に相談を試みる
        result = await system.consult_all_sages("テスト")
        
        assert result["success"] is False
        assert "error" in result
        assert result["error"] == "System not operational"
    
    @pytest.mark.asyncio
    async def test_performance_enhancement(self, integration):
        """パフォーマンス強化テスト"""
        # パフォーマンスエンハンサーが有効か確認
        assert integration.performance_enhancer is not None
        
        # キャッシュ付き実行（2回実行して2回目が速いことを確認）
        import time
        
        # 1回目
        start1 = time.time()
        result1 = await integration.execute_with_sages("テストタスク")
        time1 = time.time() - start1
        
        # 2回目（キャッシュヒット）
        start2 = time.time()
        result2 = await integration.execute_with_sages("テストタスク")
        time2 = time.time() - start2
        
        assert result1["success"] is True
        assert result2["success"] is True
        # キャッシュにより2回目の方が速い（または同等）
        assert time2 <= time1 * 1.1  # 10%の余裕を持たせる
    
    @pytest.mark.asyncio
    async def test_collaboration_integration(self, integration):
        """連携システム統合テスト"""
        # 連携システムが有効か確認
        assert integration.collaboration is not None
        
        # 協調的意思決定を含む相談
        result = await integration.consult_all_sages(
            "マイクロサービス vs モノリス",
            {"type": "architecture_decision"}
        )
        
        assert result["success"] is True
        
        # 協調的推奨が含まれているか確認
        sage_types = [rec["sage"] for rec in result["recommendations"]]
        assert "collaborative" in sage_types or len(sage_types) >= 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])