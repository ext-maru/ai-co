"""
Test suite for Knowledge Sage Analytics and Four Sages Integration API
Tests statistics, analysis, and cross-sage collaboration features
"""

import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from elders_guild.elder_tree.knowledge_sage_analytics_api import KnowledgeSageAnalyticsAPI


@pytest.fixture
async def analytics_sage():
    """Create analytics-enabled Knowledge Sage instance"""
    sage = KnowledgeSageAnalyticsAPI()
    await sage.initialize()
    yield sage
    await sage.cleanup()


@pytest.fixture
def sample_analytics_data():
    """Sample data for analytics testing"""
    return {
        "knowledge_entries": [
            {
                "id": "doc1",
                "title": "Python Best Practices",
                "content": "Follow PEP 8 style guide for Python code formatting and structure.",
                "category": "development",
                "tags": ["python", "best-practices", "coding"],
                "created_at": (datetime.now() - timedelta(days=30)).isoformat(),
                "views": 150,
                "quality_score": 0.9
            },
            {
                "id": "doc2", 
                "title": "Docker Security",
                "content": "Secure Docker containers by using non-root users and minimal base images.",
                "category": "security",
                "tags": ["docker", "security", "containers"],
                "created_at": (datetime.now() - timedelta(days=15)).isoformat(),
                "views": 200,
                "quality_score": 0.85
            },
            {
                "id": "doc3",
                "title": "API Design Patterns",
                "content": "RESTful API design principles including proper HTTP status codes and versioning.",
                "category": "architecture",
                "tags": ["api", "rest", "design", "patterns"],
                "created_at": (datetime.now() - timedelta(days=5)).isoformat(),
                "views": 75,
                "quality_score": 0.8
            }
        ],
        "search_queries": [
            {"query": "python best practices", "timestamp": "2024-01-01T10:00:00", "results": 5},
            {"query": "docker security", "timestamp": "2024-01-01T11:00:00", "results": 3},
            {"query": "api design", "timestamp": "2024-01-01T12:00:00", "results": 8}
        ],
        "user_interactions": [
            {"action": "view", "document_id": "doc1", "timestamp": "2024-01-01T10:00:00"},
            {"action": "search", "query": "python", "timestamp": "2024-01-01T10:05:00"},
            {"action": "export", "document_id": "doc2", "timestamp": "2024-01-01T10:10:00"}
        ]
    }


class TestKnowledgeSageAnalyticsAPI:
    """Test suite for analytics and four sages integration"""

    @pytest.mark.asyncio
    async def test_initialization(self, analytics_sage):
        """Test analytics system initialization"""
        assert analytics_sage is not None
        assert analytics_sage.is_initialized()
        assert hasattr(analytics_sage, 'four_sages_api')
        assert hasattr(analytics_sage, 'analytics_engine')
        assert hasattr(analytics_sage, 'stats_collector')

    @pytest.mark.asyncio
    async def test_knowledge_statistics(self, analytics_sage, sample_analytics_data):
        """Test knowledge base statistics generation"""
        # Load sample data
        for entry in sample_analytics_data["knowledge_entries"]:
            await analytics_sage.store_document(**entry)
        
        result = await analytics_sage.get_knowledge_statistics(
            time_period="30d",
            include_trends=True
        )
        
        assert result["success"] is True
        assert "statistics" in result
        
        stats = result["statistics"]
        assert "total_documents" in stats
        assert "categories" in stats
        assert "tags" in stats
        assert "quality_metrics" in stats
        assert "growth_trends" in stats
        
        # Verify counts
        assert stats["total_documents"] == 3
        assert len(stats["categories"]) > 0
        assert stats["quality_metrics"]["average_score"] > 0

    @pytest.mark.asyncio
    async def test_search_analytics(self, analytics_sage, sample_analytics_data):
        """Test search query analytics"""
        # Store search queries
        for query_data in sample_analytics_data["search_queries"]:
            await analytics_sage.log_search_query(
                query=query_data["query"],
                results_count=query_data["results"],
                timestamp=query_data["timestamp"]
            )
        
        result = await analytics_sage.get_search_analytics(
            time_period="7d",
            include_popular_queries=True
        )
        
        assert result["success"] is True
        assert "analytics" in result
        
        analytics = result["analytics"]
        assert "total_searches" in analytics
        assert "popular_queries" in analytics
        assert "search_trends" in analytics
        assert "avg_results_per_query" in analytics

    @pytest.mark.asyncio
    async def test_user_behavior_analysis(self, analytics_sage, sample_analytics_data):
        """Test user behavior analysis"""
        # Log user interactions
        for interaction in sample_analytics_data["user_interactions"]:
            await analytics_sage.log_user_interaction(
                action=interaction["action"],
                document_id=interaction.get("document_id"),
                query=interaction.get("query"),
                timestamp=interaction["timestamp"]
            )
        
        result = await analytics_sage.analyze_user_behavior(
            time_period="24h",
            include_patterns=True
        )
        
        assert result["success"] is True
        assert "behavior_analysis" in result
        
        analysis = result["behavior_analysis"]
        assert "action_distribution" in analysis
        assert "popular_documents" in analysis
        assert "usage_patterns" in analysis

    @pytest.mark.asyncio
    async def test_content_performance_metrics(self, analytics_sage, sample_analytics_data):
        """Test content performance metrics"""
        # Load documents with performance data
        for entry in sample_analytics_data["knowledge_entries"]:
            await analytics_sage.store_document(**entry)
        
        result = await analytics_sage.get_content_performance(
            sort_by="views",
            include_recommendations=True
        )
        
        assert result["success"] is True
        assert "performance_metrics" in result
        
        metrics = result["performance_metrics"]
        assert "top_performing" in metrics
        assert "underperforming" in metrics
        assert "recommendations" in metrics
        
        # Should be sorted by views (descending)
        top_docs = metrics["top_performing"]
        if len(top_docs) > 1:
            assert top_docs[0]["views"] >= top_docs[1]["views"]

    @pytest.mark.asyncio
    async def test_knowledge_gap_analysis(self, analytics_sage, sample_analytics_data):
        """Test knowledge gap identification"""
        # Load sample data
        for entry in sample_analytics_data["knowledge_entries"]:
            await analytics_sage.store_document(**entry)
        
        # Define required knowledge areas
        required_areas = [
            "testing", "deployment", "monitoring", "troubleshooting",
            "performance", "scalability", "backup", "recovery"
        ]
        
        result = await analytics_sage.analyze_knowledge_gaps(
            required_areas=required_areas,
            coverage_threshold=0.7,
            suggest_priorities=True
        )
        
        assert result["success"] is True
        assert "gap_analysis" in result
        
        analysis = result["gap_analysis"]
        assert "coverage_map" in analysis
        assert "identified_gaps" in analysis
        assert "priority_recommendations" in analysis

    @pytest.mark.asyncio
    async def test_four_sages_collaboration(self, analytics_sage):
        """Test integration with other four sages"""
        # Mock other sages
        with patch.object(analytics_sage, 'task_sage') as mock_task_sage, \
             patch.object(analytics_sage, 'incident_sage') as mock_incident_sage, \
             patch.object(analytics_sage, 'rag_sage') as mock_rag_sage:
            
            # Configure mock responses (use AsyncMock for async methods)
            mock_task_sage.get_active_tasks = AsyncMock(return_value={
                "success": True,
                "tasks": [{"id": "task1", "priority": "high", "category": "development"}]
            })
            
            mock_incident_sage.get_recent_incidents = AsyncMock(return_value={
                "success": True,
                "incidents": [{"id": "inc1", "severity": "medium", "category": "performance"}]
            })
            
            mock_rag_sage.get_search_trends = AsyncMock(return_value={
                "success": True,
                "trends": ["python", "security", "api"]
            })
            
            # Test cross-sage analytics
            result = await analytics_sage.get_cross_sage_analytics()
            
            assert result["success"] is True
            assert "task_insights" in result
            assert "incident_patterns" in result
            assert "search_intelligence" in result

    @pytest.mark.asyncio
    async def test_knowledge_recommendation_engine(self, analytics_sage, sample_analytics_data):
        """Test knowledge recommendation system"""
        # Load sample data
        for entry in sample_analytics_data["knowledge_entries"]:
            await analytics_sage.store_document(**entry)
        
        result = await analytics_sage.get_knowledge_recommendations(
            user_profile={
                "interests": ["python", "security"],
                "experience_level": "intermediate",
                "recent_queries": ["docker security", "python best practices"]
            },
            recommendation_count=5
        )
        
        assert result["success"] is True
        assert "recommendations" in result
        
        recommendations = result["recommendations"]
        assert len(recommendations) <= 5
        assert all("title" in rec for rec in recommendations)
        assert all("relevance_score" in rec for rec in recommendations)
        assert all("reason" in rec for rec in recommendations)

    @pytest.mark.asyncio
    async def test_predictive_analytics(self, analytics_sage, sample_analytics_data):
        """Test predictive analytics features"""
        # Load historical data
        for entry in sample_analytics_data["knowledge_entries"]:
            await analytics_sage.store_document(**entry)
        
        result = await analytics_sage.generate_predictions(
            prediction_horizon="30d",
            metrics=["knowledge_growth", "search_volume", "popular_topics"]
        )
        
        assert result["success"] is True
        assert "predictions" in result
        
        predictions = result["predictions"]
        assert "knowledge_growth" in predictions
        assert "search_volume" in predictions
        assert "popular_topics" in predictions
        
        # Check prediction structure
        growth_pred = predictions["knowledge_growth"]
        assert "predicted_value" in growth_pred
        assert "confidence_interval" in growth_pred

    @pytest.mark.asyncio
    async def test_real_time_monitoring(self, analytics_sage):
        """Test real-time monitoring capabilities"""
        # Start monitoring
        result = await analytics_sage.start_realtime_monitoring(
            metrics=["active_users", "search_rate", "system_load"],
            update_interval=5  # seconds
        )
        
        assert result["success"] is True
        assert "monitoring_id" in result
        
        monitoring_id = result["monitoring_id"]
        
        # Get current metrics
        metrics_result = await analytics_sage.get_realtime_metrics(monitoring_id)
        
        assert metrics_result["success"] is True
        assert "metrics" in metrics_result
        assert "timestamp" in metrics_result

    @pytest.mark.asyncio
    async def test_custom_dashboards(self, analytics_sage):
        """Test custom dashboard creation"""
        dashboard_config = {
            "name": "Knowledge Management Dashboard",
            "widgets": [
                {
                    "type": "metric_card",
                    "title": "Total Documents",
                    "metric": "total_documents"
                },
                {
                    "type": "chart",
                    "title": "Search Trends",
                    "chart_type": "line",
                    "metric": "search_volume",
                    "time_range": "7d"
                },
                {
                    "type": "table",
                    "title": "Top Categories",
                    "data_source": "category_stats"
                }
            ]
        }
        
        result = await analytics_sage.create_dashboard(dashboard_config)
        
        assert result["success"] is True
        assert "dashboard_id" in result
        assert "dashboard_url" in result or "dashboard_data" in result

    @pytest.mark.asyncio
    async def test_export_analytics_data(self, analytics_sage, sample_analytics_data):
        """Test analytics data export"""
        # Load sample data
        for entry in sample_analytics_data["knowledge_entries"]:
            await analytics_sage.store_document(**entry)
        
        result = await analytics_sage.export_analytics_data(
            data_types=["knowledge_stats", "search_analytics", "user_behavior"],
            format="json",
            time_period="30d"
        )
        
        assert result["success"] is True
        assert "export_data" in result or "export_file" in result
        
        if "export_data" in result:
            export_data = result["export_data"]
            assert "knowledge_stats" in export_data
            assert "search_analytics" in export_data
            assert "user_behavior" in export_data

    @pytest.mark.asyncio
    async def test_alerting_system(self, analytics_sage):
        """Test analytics alerting system"""
        # Configure alerts
        alert_rules = [
            {
                "name": "Low Content Quality",
                "condition": "average_quality_score < 0.7",
                "severity": "medium",
                "notification_channels": ["email", "webhook"]
            },
            {
                "name": "High Search Volume",
                "condition": "search_rate > 1000 per hour",
                "severity": "info",
                "notification_channels": ["dashboard"]
            }
        ]
        
        result = await analytics_sage.configure_alerts(alert_rules)
        
        assert result["success"] is True
        assert "alert_ids" in result
        
        # Test alert triggering
        trigger_result = await analytics_sage.check_alert_conditions()
        
        assert trigger_result["success"] is True
        assert "triggered_alerts" in trigger_result

    @pytest.mark.asyncio
    async def test_collaborative_filtering(self, analytics_sage, sample_analytics_data):
        """Test collaborative filtering for recommendations"""
        # Simulate user behavior patterns
        user_interactions = [
            {"user_id": "user1", "document_id": "doc1", "action": "view", "rating": 5},
            {"user_id": "user1", "document_id": "doc2", "action": "view", "rating": 3},
            {"user_id": "user2", "document_id": "doc1", "action": "view", "rating": 4},
            {"user_id": "user2", "document_id": "doc3", "action": "view", "rating": 5},
        ]
        
        # Train collaborative filtering model
        result = await analytics_sage.train_collaborative_filtering(
            interactions=user_interactions,
            algorithm="matrix_factorization"
        )
        
        assert result["success"] is True
        assert "model_metrics" in result
        
        # Get recommendations for a user
        recommendations = await analytics_sage.get_collaborative_recommendations(
            user_id="user1",
            n_recommendations=3
        )
        
        assert recommendations["success"] is True
        assert "recommended_documents" in recommendations

    @pytest.mark.asyncio
    async def test_anomaly_detection(self, analytics_sage):
        """Test anomaly detection in knowledge usage patterns"""
        # Generate some normal and anomalous data
        usage_data = [
            {"timestamp": "2024-01-01T10:00:00", "searches": 50, "views": 200},
            {"timestamp": "2024-01-01T11:00:00", "searches": 45, "views": 180},
            {"timestamp": "2024-01-01T12:00:00", "searches": 1000, "views": 50},  # Anomaly
            {"timestamp": "2024-01-01T13:00:00", "searches": 55, "views": 220},
        ]
        
        result = await analytics_sage.detect_anomalies(
            data=usage_data,
            detection_method="statistical",
            sensitivity=0.95
        )
        
        assert result["success"] is True
        assert "anomalies" in result
        assert "anomaly_scores" in result
        
        # Should detect the anomalous data point
        anomalies = result["anomalies"]
        assert len(anomalies) > 0

    @pytest.mark.asyncio
    async def test_a_b_testing_framework(self, analytics_sage):
        """Test A/B testing framework for knowledge features"""
        # Create A/B test
        test_config = {
            "name": "Search Algorithm Test",
            "variants": [
                {"name": "control", "weight": 0.5, "config": {"algorithm": "tfidf"}},
                {"name": "treatment", "weight": 0.5, "config": {"algorithm": "semantic"}}
            ],
            "success_metrics": ["click_through_rate", "user_satisfaction"],
            "minimum_sample_size": 100
        }
        
        result = await analytics_sage.create_ab_test(test_config)
        
        assert result["success"] is True
        assert "test_id" in result
        
        test_id = result["test_id"]
        
        # Log test events
        events = [
            {"user_id": "user1", "variant": "control", "metric": "click_through_rate", "value": 0.15},
            {"user_id": "user2", "variant": "treatment", "metric": "click_through_rate", "value": 0.22},
        ]
        
        for event in events:
            await analytics_sage.log_ab_test_event(test_id, event)
        
        # Get test results
        results = await analytics_sage.get_ab_test_results(test_id)
        
        assert results["success"] is True
        assert "statistical_significance" in results
        assert "variant_performance" in results

    @pytest.mark.asyncio
    async def test_knowledge_lifecycle_analytics(self, analytics_sage, sample_analytics_data):
        """Test knowledge lifecycle analytics"""
        # Load documents with lifecycle data
        for entry in sample_analytics_data["knowledge_entries"]:
            await analytics_sage.store_document(**entry)
        
        result = await analytics_sage.analyze_knowledge_lifecycle(
            include_stages=["creation", "adoption", "peak_usage", "decline", "retirement"],
            time_granularity="monthly"
        )
        
        assert result["success"] is True
        assert "lifecycle_analysis" in result
        
        analysis = result["lifecycle_analysis"]
        assert "stage_distribution" in analysis
        assert "lifecycle_trends" in analysis
        assert "document_health_scores" in analysis

    @pytest.mark.asyncio
    async def test_performance_benchmarking(self, analytics_sage):
        """Test system performance benchmarking"""
        benchmark_tests = [
            {"name": "search_latency", "target_metric": "response_time", "threshold": 100},
            {"name": "indexing_throughput", "target_metric": "docs_per_second", "threshold": 50},
            {"name": "concurrent_users", "target_metric": "max_users", "threshold": 100}
        ]
        
        result = await analytics_sage.run_performance_benchmarks(
            tests=benchmark_tests,
            duration_minutes=5
        )
        
        assert result["success"] is True
        assert "benchmark_results" in result
        
        results = result["benchmark_results"]
        for test in benchmark_tests:
            test_name = test["name"]
            assert test_name in results
            assert "actual_value" in results[test_name]
            assert "passed" in results[test_name]

    @pytest.mark.asyncio
    async def test_integration_health_monitoring(self, analytics_sage):
        """Test four sages integration health monitoring"""
        result = await analytics_sage.monitor_integration_health()
        
        assert result["success"] is True
        assert "sage_health" in result
        
        health = result["sage_health"]
        expected_sages = ["task_sage", "incident_sage", "rag_sage"]
        
        for sage_name in expected_sages:
            if sage_name in health:
                assert "status" in health[sage_name]
                assert "last_communication" in health[sage_name]
                assert "response_time" in health[sage_name]

    @pytest.mark.asyncio
    async def test_cleanup(self, analytics_sage):
        """Test cleanup of analytics resources"""
        # Create some resources to cleanup
        await analytics_sage.start_realtime_monitoring(
            metrics=["test_metric"],
            update_interval=10
        )
        
        # Cleanup
        await analytics_sage.cleanup()
        
        # Verify cleanup
        assert not analytics_sage.is_initialized()