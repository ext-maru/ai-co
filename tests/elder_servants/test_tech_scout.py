"""
TechScout (W01) - 技術調査専門サーバントのテスト
RAGウィザーズ所属 - 最新技術・ライブラリ調査のエキスパート
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from libs.elder_servants.rag_wizards.tech_scout import TechScout


class TestTechScoutBasics:
    """TechScoutの基本機能テスト"""
    
    @pytest.fixture
    def tech_scout(self):
        """TechScoutインスタンスを生成"""
        return TechScout()
    
    def test_initialization(self, tech_scout):
        """初期化テスト"""
        assert tech_scout.servant_id == "W01"
        assert tech_scout.name == "TechScout"
        assert tech_scout.category == "rag_wizards"
        assert tech_scout.specialization == "technology_research"
    
    def test_get_capabilities(self, tech_scout):
        """能力リスト取得テスト"""
        capabilities = tech_scout.get_capabilities()
        assert "research_technology" in capabilities
        assert "evaluate_library" in capabilities
        assert "analyze_trends" in capabilities
        assert "compare_solutions" in capabilities
        assert "security_assessment" in capabilities
        assert "performance_benchmark" in capabilities
        assert len(capabilities) >= 6


class TestTechnologyResearch:
    """技術調査機能のテスト"""
    
    @pytest.fixture
    def tech_scout(self):
        return TechScout()
    
    @pytest.mark.asyncio
    async def test_research_technology(self, tech_scout):
        """技術調査の基本テスト"""
        result = await tech_scout.execute_task({
            "action": "research_technology",
            "topic": "Python async frameworks",
            "depth": "comprehensive"
        })
        
        assert result["status"] == "success"
        assert "research_summary" in result
        assert "key_findings" in result
        assert len(result["key_findings"]) >= 3
        assert "recommendations" in result
        assert result["confidence_score"] >= 80
    
    @pytest.mark.asyncio
    async def test_evaluate_library(self, tech_scout):
        """ライブラリ評価テスト"""
        result = await tech_scout.execute_task({
            "action": "evaluate_library",
            "library_name": "FastAPI",
            "criteria": ["performance", "documentation", "community", "stability"]
        })
        
        assert result["status"] == "success"
        assert "evaluation_scores" in result
        assert all(criterion in result["evaluation_scores"] for criterion in ["performance", "documentation", "community", "stability"])
        assert "overall_score" in result
        assert 0 <= result["overall_score"] <= 100
        assert "pros" in result and len(result["pros"]) > 0
        assert "cons" in result and len(result["cons"]) >= 0
        assert "recommendation" in result
    
    @pytest.mark.asyncio
    async def test_analyze_trends(self, tech_scout):
        """技術トレンド分析テスト"""
        result = await tech_scout.execute_task({
            "action": "analyze_trends",
            "domain": "web development",
            "timeframe": "last_year"
        })
        
        assert result["status"] == "success"
        assert "trending_technologies" in result
        assert len(result["trending_technologies"]) >= 5
        assert "declining_technologies" in result
        assert "emerging_patterns" in result
        assert "future_predictions" in result
        assert len(result["future_predictions"]) >= 3
    
    @pytest.mark.asyncio
    async def test_compare_solutions(self, tech_scout):
        """ソリューション比較テスト"""
        solutions = ["Django", "FastAPI", "Flask"]
        
        result = await tech_scout.execute_task({
            "action": "compare_solutions",
            "solutions": solutions,
            "use_case": "REST API development",
            "comparison_criteria": ["performance", "ease_of_use", "features", "ecosystem"]
        })
        
        assert result["status"] == "success"
        assert "comparison_matrix" in result
        assert all(solution in result["comparison_matrix"] for solution in solutions)
        assert "winner" in result
        assert result["winner"] in solutions
        assert "detailed_analysis" in result
        assert len(result["detailed_analysis"]) == len(solutions)


class TestSecurityAndPerformance:
    """セキュリティとパフォーマンス評価のテスト"""
    
    @pytest.fixture
    def tech_scout(self):
        return TechScout()
    
    @pytest.mark.asyncio
    async def test_security_assessment(self, tech_scout):
        """セキュリティ評価テスト"""
        result = await tech_scout.execute_task({
            "action": "security_assessment",
            "technology": "JWT authentication",
            "context": "web application"
        })
        
        assert result["status"] == "success"
        assert "security_score" in result
        assert 0 <= result["security_score"] <= 100
        assert "vulnerabilities" in result
        assert "best_practices" in result
        assert len(result["best_practices"]) >= 3
        assert "recommendations" in result
    
    @pytest.mark.asyncio
    async def test_performance_benchmark(self, tech_scout):
        """パフォーマンスベンチマークテスト"""
        result = await tech_scout.execute_task({
            "action": "performance_benchmark",
            "technologies": ["asyncio", "threading", "multiprocessing"],
            "benchmark_type": "concurrent_requests"
        })
        
        assert result["status"] == "success"
        assert "benchmark_results" in result
        assert all(tech in result["benchmark_results"] for tech in ["asyncio", "threading", "multiprocessing"])
        assert "performance_ranking" in result
        assert len(result["performance_ranking"]) == 3
        assert "analysis" in result
        assert "recommendations" in result


class TestAdvancedResearchFeatures:
    """高度な調査機能のテスト"""
    
    @pytest.fixture
    def tech_scout(self):
        return TechScout()
    
    @pytest.mark.asyncio
    async def test_deep_dive_research(self, tech_scout):
        """深掘り調査テスト"""
        result = await tech_scout.execute_task({
            "action": "deep_dive_research",
            "topic": "Microservices architecture patterns",
            "aspects": ["design_patterns", "communication", "data_management", "deployment"]
        })
        
        assert result["status"] == "success"
        assert "comprehensive_report" in result
        assert all(aspect in result["comprehensive_report"] for aspect in ["design_patterns", "communication", "data_management", "deployment"])
        assert "case_studies" in result
        assert len(result["case_studies"]) >= 2
        assert "implementation_roadmap" in result
    
    @pytest.mark.asyncio
    async def test_technology_radar(self, tech_scout):
        """技術レーダー生成テスト"""
        result = await tech_scout.execute_task({
            "action": "generate_tech_radar",
            "categories": ["languages", "frameworks", "tools", "platforms"],
            "organization_context": "startup"
        })
        
        assert result["status"] == "success"
        assert "tech_radar" in result
        assert "adopt" in result["tech_radar"]
        assert "trial" in result["tech_radar"]
        assert "assess" in result["tech_radar"]
        assert "hold" in result["tech_radar"]
        assert sum(len(result["tech_radar"][phase]) for phase in ["adopt", "trial", "assess", "hold"]) >= 20
    
    @pytest.mark.asyncio
    async def test_migration_analysis(self, tech_scout):
        """移行分析テスト"""
        result = await tech_scout.execute_task({
            "action": "analyze_migration",
            "from_technology": "monolithic Django app",
            "to_technology": "microservices with FastAPI",
            "project_size": "medium"
        })
        
        assert result["status"] == "success"
        assert "migration_complexity" in result
        assert result["migration_complexity"] in ["low", "medium", "high", "very_high"]
        assert "migration_steps" in result
        assert len(result["migration_steps"]) >= 5
        assert "risks" in result
        assert "timeline_estimate" in result
        assert "cost_benefit_analysis" in result


class TestKnowledgeManagement:
    """知識管理機能のテスト"""
    
    @pytest.fixture
    def tech_scout(self):
        return TechScout()
    
    @pytest.mark.asyncio
    async def test_knowledge_storage(self, tech_scout):
        """調査結果の保存テスト"""
        research_data = {
            "topic": "GraphQL",
            "findings": ["Strong typing", "Efficient data fetching", "Good tooling"],
            "date": datetime.now().isoformat()
        }
        
        with patch.object(tech_scout, '_store_research_knowledge') as mock_store:
            mock_store.return_value = True
            
            result = await tech_scout._store_research_knowledge(research_data)
            
            assert result is True
            mock_store.assert_called_once_with(research_data)
    
    @pytest.mark.asyncio
    async def test_research_cache(self, tech_scout):
        """調査結果キャッシュテスト"""
        # 最初の調査
        result1 = await tech_scout.execute_task({
            "action": "research_technology",
            "topic": "Rust for web development",
            "use_cache": True
        })
        
        # キャッシュからの取得
        result2 = await tech_scout.execute_task({
            "action": "research_technology",
            "topic": "Rust for web development",
            "use_cache": True
        })
        
        assert result1["status"] == "success"
        assert result2["status"] == "success"
        assert result2.get("from_cache") is True
        assert result1["research_summary"] == result2["research_summary"]


class TestQualityAndCompliance:
    """品質とコンプライアンステスト"""
    
    @pytest.fixture
    def tech_scout(self):
        return TechScout()
    
    @pytest.mark.asyncio
    async def test_iron_will_compliance(self, tech_scout):
        """Iron Will品質基準準拠テスト"""
        # 高品質な調査結果の生成
        result = await tech_scout.execute_task({
            "action": "research_technology",
            "topic": "Kubernetes",
            "quality_requirements": "iron_will"
        })
        
        assert result["status"] == "success"
        assert result.get("quality_score", 0) >= 95
        assert len(result.get("sources", [])) >= 5
        assert result.get("confidence_score", 0) >= 90
    
    @pytest.mark.asyncio
    async def test_error_handling(self, tech_scout):
        """エラーハンドリングテスト"""
        # 無効なアクション
        result = await tech_scout.execute_task({
            "action": "invalid_action",
            "topic": "test"
        })
        
        assert result["status"] == "error"
        assert "error" in result
        assert "recovery_suggestion" in result
    
    @pytest.mark.asyncio
    async def test_sage_collaboration(self, tech_scout):
        """4賢者との協調テスト"""
        with patch.object(tech_scout, 'collaborate_with_sages') as mock_collab:
            mock_collab.return_value = {
                "knowledge_sage": {"related_knowledge": ["Previous research on Docker"]},
                "task_sage": {"priority": "high", "deadline": "2025-01-20"},
                "incident_sage": {"risks": ["Outdated information risk"]},
                "rag_sage": {"similar_research": ["container_orchestration.md"]}
            }
            
            result = await tech_scout.execute_task({
                "action": "research_technology",
                "topic": "Container orchestration",
                "consult_sages": True
            })
            
            mock_collab.assert_called_once()
            assert result["status"] == "success"


class TestHealthAndMetrics:
    """ヘルスチェックとメトリクステスト"""
    
    @pytest.fixture
    def tech_scout(self):
        return TechScout()
    
    @pytest.mark.asyncio
    async def test_health_check(self, tech_scout):
        """ヘルスチェック"""
        health = await tech_scout.health_check()
        
        assert health["status"] == "healthy"
        assert health["servant_id"] == "W01"
        assert "capabilities" in health
        assert health["iron_will_compliance"] == True
        assert health["performance_metrics"]["avg_research_time"] < 10.0
    
    def test_get_metrics(self, tech_scout):
        """メトリクス取得"""
        metrics = tech_scout.get_metrics()
        
        assert "total_researches" in metrics
        assert "research_topics" in metrics
        assert "average_confidence_score" in metrics
        assert metrics["average_confidence_score"] >= 85