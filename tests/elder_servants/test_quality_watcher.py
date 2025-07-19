"""
QualityWatcher (E01) - 品質監視専門サーバントのテスト
エルフの森所属 - コード品質・Iron Will基準監視のエキスパート
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from libs.elder_servants.elf_forest.quality_watcher import QualityWatcher


class TestQualityWatcherBasics:
    """QualityWatcherの基本機能テスト"""

    @pytest.fixture
    def quality_watcher(self):
        """QualityWatcherインスタンスを生成"""
        return QualityWatcher()

    def test_initialization(self, quality_watcher):
        """初期化テスト"""
        assert quality_watcher.servant_id == "E01"
        assert quality_watcher.name == "QualityWatcher"
        assert quality_watcher.category == "elf_forest"
        assert quality_watcher.specialization == "quality_monitoring"

    def test_get_capabilities(self, quality_watcher):
        """能力リスト取得テスト"""
        capabilities = quality_watcher.get_capabilities()
        assert "monitor_code_quality" in capabilities
        assert "check_iron_will_compliance" in capabilities
        assert "analyze_test_coverage" in capabilities
        assert "monitor_performance" in capabilities
        assert "security_scan" in capabilities
        assert "dependency_audit" in capabilities
        assert len(capabilities) >= 6


class TestQualityMonitoring:
    """品質監視機能のテスト"""

    @pytest.fixture
    def quality_watcher(self):
        return QualityWatcher()

    @pytest.mark.asyncio
    async def test_monitor_code_quality(self, quality_watcher):
        """コード品質監視テスト"""
        source_code = '''
def calculate_sum(numbers):
    """Calculate sum of numbers"""
    total = 0
    for num in numbers:
        total += num
    return total

class Calculator:
    def __init__(self):
        self.history = []

    def add(self, a, b):
        result = a + b
        self.history.append(f"add({a}, {b}) = {result}")
        return result
'''

        result = await quality_watcher.execute_task(
            {
                "action": "monitor_code_quality",
                "source_code": source_code,
                "file_path": "calculator.py",
            }
        )

        assert result["status"] == "success"
        assert "quality_metrics" in result
        assert "complexity_score" in result["quality_metrics"]
        assert "maintainability_index" in result["quality_metrics"]
        assert "code_smells" in result
        assert "suggestions" in result
        assert result["overall_score"] >= 80

    @pytest.mark.asyncio
    async def test_check_iron_will_compliance(self, quality_watcher):
        """Iron Will基準準拠チェックテスト"""
        project_metrics = {
            "test_coverage": 96,
            "code_quality": 94,
            "security_score": 92,
            "performance_score": 88,
            "documentation_coverage": 85,
        }

        result = await quality_watcher.execute_task(
            {"action": "check_iron_will_compliance", "project_metrics": project_metrics}
        )

        assert result["status"] == "success"
        assert "compliance_status" in result
        assert "criteria_results" in result
        assert len(result["criteria_results"]) == 6  # 6大品質基準
        assert "overall_compliance" in result
        assert "non_compliant_areas" in result
        assert "improvement_plan" in result

    @pytest.mark.asyncio
    async def test_analyze_test_coverage(self, quality_watcher):
        """テストカバレッジ分析テスト"""
        coverage_data = {
            "overall_coverage": 94.5,
            "file_coverage": {
                "calculator.py": 98.0,
                "utils.py": 85.0,
                "models.py": 92.0,
            },
            "uncovered_lines": {"utils.py": [45, 67, 89], "models.py": [123, 145]},
        }

        result = await quality_watcher.execute_task(
            {"action": "analyze_test_coverage", "coverage_data": coverage_data}
        )

        assert result["status"] == "success"
        assert result["coverage_assessment"]["meets_iron_will"] == False  # 95%未満
        assert "priority_files" in result
        assert "coverage_recommendations" in result
        assert len(result["coverage_recommendations"]) >= 2

    @pytest.mark.asyncio
    async def test_monitor_performance(self, quality_watcher):
        """パフォーマンス監視テスト"""
        performance_data = {
            "response_times": [120, 145, 98, 167, 134],  # ms
            "memory_usage": [45.2, 47.8, 44.1, 48.9, 46.3],  # MB
            "cpu_usage": [15.4, 18.2, 12.7, 21.1, 16.8],  # %
            "error_rate": 0.02,
        }

        result = await quality_watcher.execute_task(
            {
                "action": "monitor_performance",
                "performance_data": performance_data,
                "time_window": "last_hour",
            }
        )

        assert result["status"] == "success"
        assert "performance_summary" in result
        assert "alerts" in result
        assert "trends" in result
        assert result["performance_score"] >= 0


class TestSecurityAndDependency:
    """セキュリティと依存関係監査のテスト"""

    @pytest.fixture
    def quality_watcher(self):
        return QualityWatcher()

    @pytest.mark.asyncio
    async def test_security_scan(self, quality_watcher):
        """セキュリティスキャンテスト"""
        result = await quality_watcher.execute_task(
            {
                "action": "security_scan",
                "project_path": "/path/to/project",
                "scan_type": "comprehensive",
            }
        )

        assert result["status"] == "success"
        assert "security_score" in result
        assert "vulnerabilities" in result
        assert "security_recommendations" in result
        assert "compliance_status" in result
        assert len(result["security_recommendations"]) >= 3

    @pytest.mark.asyncio
    async def test_dependency_audit(self, quality_watcher):
        """依存関係監査テスト"""
        dependencies = {
            "fastapi": "0.104.1",
            "requests": "2.31.0",
            "pydantic": "2.5.0",
            "pytest": "7.4.3",
        }

        result = await quality_watcher.execute_task(
            {"action": "dependency_audit", "dependencies": dependencies}
        )

        assert result["status"] == "success"
        assert "audit_results" in result
        assert "outdated_packages" in result
        assert "security_vulnerabilities" in result
        assert "update_recommendations" in result
        assert "risk_assessment" in result


class TestAdvancedQualityFeatures:
    """高度な品質機能のテスト"""

    @pytest.fixture
    def quality_watcher(self):
        return QualityWatcher()

    @pytest.mark.asyncio
    async def test_continuous_monitoring(self, quality_watcher):
        """継続監視テスト"""
        result = await quality_watcher.execute_task(
            {
                "action": "setup_continuous_monitoring",
                "project_path": "/path/to/project",
                "monitoring_interval": "hourly",
                "quality_thresholds": {
                    "test_coverage": 95,
                    "code_quality": 90,
                    "performance_score": 85,
                },
            }
        )

        assert result["status"] == "success"
        assert "monitoring_config" in result
        assert "scheduled_checks" in result
        assert "alert_configuration" in result
        assert result["monitoring_active"] == True

    @pytest.mark.asyncio
    async def test_quality_trend_analysis(self, quality_watcher):
        """品質トレンド分析テスト"""
        historical_data = [
            {"date": "2025-01-15", "coverage": 92, "quality": 88, "performance": 85},
            {"date": "2025-01-16", "coverage": 93, "quality": 89, "performance": 87},
            {"date": "2025-01-17", "coverage": 94, "quality": 91, "performance": 86},
            {"date": "2025-01-18", "coverage": 95, "quality": 92, "performance": 88},
            {"date": "2025-01-19", "coverage": 96, "quality": 94, "performance": 90},
        ]

        result = await quality_watcher.execute_task(
            {
                "action": "analyze_quality_trends",
                "historical_data": historical_data,
                "timeframe": "week",
            }
        )

        assert result["status"] == "success"
        assert "trend_analysis" in result
        assert "improvement_rate" in result
        assert "predictions" in result
        assert "trend_status" in result
        assert result["trend_status"] in ["improving", "stable", "declining"]

    @pytest.mark.asyncio
    async def test_quality_gates(self, quality_watcher):
        """品質ゲートテスト"""
        commit_metrics = {
            "files_changed": 5,
            "lines_added": 120,
            "lines_removed": 30,
            "test_coverage_change": 2.1,
            "complexity_change": -1.5,
        }

        result = await quality_watcher.execute_task(
            {
                "action": "evaluate_quality_gate",
                "commit_metrics": commit_metrics,
                "gate_rules": {
                    "min_coverage_change": 0,
                    "max_complexity_increase": 5,
                    "require_tests": True,
                },
            }
        )

        assert result["status"] == "success"
        assert "gate_result" in result
        assert result["gate_result"] in ["pass", "fail", "warning"]
        assert "gate_checks" in result
        assert "blocking_issues" in result


class TestReportingAndIntegration:
    """レポートと統合機能のテスト"""

    @pytest.fixture
    def quality_watcher(self):
        return QualityWatcher()

    @pytest.mark.asyncio
    async def test_generate_quality_report(self, quality_watcher):
        """品質レポート生成テスト"""
        result = await quality_watcher.execute_task(
            {
                "action": "generate_quality_report",
                "project_name": "ElderServants",
                "report_type": "comprehensive",
                "time_period": "last_week",
            }
        )

        assert result["status"] == "success"
        assert "report" in result
        assert "executive_summary" in result["report"]
        assert "detailed_metrics" in result["report"]
        assert "recommendations" in result["report"]
        assert "charts_data" in result["report"]
        assert result["report"]["iron_will_compliance"] in [True, False]

    @pytest.mark.asyncio
    async def test_alert_system(self, quality_watcher):
        """アラートシステムテスト"""
        quality_violation = {
            "type": "coverage_drop",
            "current_value": 92,
            "threshold": 95,
            "file": "new_feature.py",
            "severity": "high",
        }

        result = await quality_watcher.execute_task(
            {"action": "process_quality_alert", "violation": quality_violation}
        )

        assert result["status"] == "success"
        assert "alert_sent" in result
        assert "escalation_level" in result
        assert "remediation_steps" in result
        assert len(result["remediation_steps"]) >= 2

    @pytest.mark.asyncio
    async def test_integration_with_sages(self, quality_watcher):
        """4賢者統合テスト"""
        with patch.object(quality_watcher, "collaborate_with_sages") as mock_collab:
            mock_collab.return_value = {
                "knowledge_sage": {
                    "quality_patterns": ["solid_principles", "design_patterns"]
                },
                "task_sage": {"priority": "high", "deadline": "2025-01-20"},
                "incident_sage": {"risk_level": "medium", "mitigation": ["add_tests"]},
                "rag_sage": {"similar_issues": ["coverage_issue_123.md"]},
            }

            result = await quality_watcher.execute_task(
                {
                    "action": "monitor_code_quality",
                    "source_code": "def test(): pass",
                    "consult_sages": True,
                }
            )

            mock_collab.assert_called_once()
            assert result["status"] == "success"
            assert "sage_consultation" in result


class TestQualityCompliance:
    """品質コンプライアンステスト"""

    @pytest.fixture
    def quality_watcher(self):
        return QualityWatcher()

    @pytest.mark.asyncio
    async def test_iron_will_enforcement(self, quality_watcher):
        """Iron Will強制実行テスト"""
        # 基準を満たさないメトリクス
        poor_metrics = {
            "test_coverage": 80,  # 95%未満
            "code_quality": 70,  # 90%未満
            "security_score": 85,  # 90%未満
            "performance_score": 75,  # 85%未満
            "documentation_coverage": 60,  # 80%未満
        }

        result = await quality_watcher.execute_task(
            {"action": "enforce_iron_will", "project_metrics": poor_metrics}
        )

        assert result["status"] == "failed"  # 基準を満たさないため
        assert "enforcement_actions" in result
        assert "blocked_operations" in result
        assert len(result["blocked_operations"]) > 0
        assert "improvement_required" in result

    @pytest.mark.asyncio
    async def test_quality_score_calculation(self, quality_watcher):
        """品質スコア計算テスト"""
        metrics = {
            "complexity": 3.2,
            "duplication": 5.1,
            "test_coverage": 94.5,
            "maintainability": 88.7,
            "reliability": 92.3,
        }

        result = await quality_watcher.execute_task(
            {"action": "calculate_quality_score", "metrics": metrics}
        )

        assert result["status"] == "success"
        assert "overall_score" in result
        assert 0 <= result["overall_score"] <= 100
        assert "component_scores" in result
        assert "score_breakdown" in result


class TestHealthAndMetrics:
    """ヘルスチェックとメトリクステスト"""

    @pytest.fixture
    def quality_watcher(self):
        return QualityWatcher()

    @pytest.mark.asyncio
    async def test_health_check(self, quality_watcher):
        """ヘルスチェック"""
        health = await quality_watcher.health_check()

        assert health["status"] == "healthy"
        assert health["servant_id"] == "E01"
        assert "capabilities" in health
        assert health["iron_will_compliance"] == True
        assert health["performance_metrics"]["avg_monitoring_time"] < 5.0

    def test_get_metrics(self, quality_watcher):
        """メトリクス取得"""
        metrics = quality_watcher.get_metrics()

        assert "total_quality_checks" in metrics
        assert "alerts_generated" in metrics
        assert "average_quality_score" in metrics
        assert metrics["average_quality_score"] >= 90
