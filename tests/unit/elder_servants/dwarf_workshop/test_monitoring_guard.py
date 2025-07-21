"""
MonitoringGuard (D15) のテストケース

TDD方式で監視警備員の各機能をテストします。
24/7システム監視・アラート・メトリクス収集機能の品質を保証。
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# テスト対象のインポート
sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from libs.elder_servants.dwarf_workshop.monitoring_guard import (
    MonitoringGuard,
    MonitoringGuardRequest,
    MonitoringGuardResponse,
    MonitoringConfig,
    MetricDefinition,
    AlertRule,
    Dashboard,
    SystemHealth,
    AlertSeverity,
    MetricType,
)


class TestMonitoringGuard:
    """MonitoringGuard (D15) テストスイート"""

    @pytest.fixture
    def monitoring_guard(self):
        """MonitoringGuardインスタンスを作成"""
        return MonitoringGuard()

    @pytest.fixture
    def basic_request(self):
        """基本的なリクエストを作成"""
        return MonitoringGuardRequest(
            action="setup_monitoring",
            target_system="web_application",
            config={
                "environment": "production",
                "web_servers": [{"host": "web1.example.com", "port": 80}],
                "databases": [{"host": "db1.example.com", "type": "postgresql"}],
                "applications": [{"host": "app1.example.com", "name": "web_app"}],
                "infrastructure": {"containers": True},
            }
        )

    def test_monitoring_guard_initialization(self, monitoring_guard):
        """🔴 MonitoringGuardの初期化テスト"""
        assert monitoring_guard.servant_id == "D15"
        assert monitoring_guard.name == "MonitoringGuard"
        assert monitoring_guard.monitoring_tools is not None
        assert "prometheus" in monitoring_guard.monitoring_tools
        assert "grafana" in monitoring_guard.monitoring_tools
        assert "elk" in monitoring_guard.monitoring_tools

    def test_monitoring_guard_capabilities(self, monitoring_guard):
        """🔴 MonitoringGuardの能力一覧テスト"""
        capabilities = monitoring_guard.get_capabilities()
        
        assert "システム監視設定" in capabilities
        assert "メトリクス収集" in capabilities
        assert "アラート管理" in capabilities
        assert "ダッシュボード作成" in capabilities
        assert "24/7監視体制" in capabilities
        assert len(capabilities) >= 8

    @pytest.mark.asyncio
    async def test_validate_request_valid(self, monitoring_guard, basic_request):
        """🔴 有効なリクエストの検証テスト"""
        is_valid = await monitoring_guard.validate_request(basic_request)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_request_invalid_action(self, monitoring_guard):
        """🔴 無効なアクションのリクエスト検証テスト"""
        invalid_request = MonitoringGuardRequest(action="invalid_action")
        is_valid = await monitoring_guard.validate_request(invalid_request)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_setup_monitoring_success(self, monitoring_guard, basic_request):
        """🟢 監視システムセットアップ成功テスト"""
        response = await monitoring_guard.process_request(basic_request)
        
        assert response.success is True
        assert response.monitoring_config is not None
        assert len(response.monitoring_config.targets) > 0
        assert len(response.monitoring_config.metrics) > 0
        assert len(response.monitoring_config.alerts) > 0
        assert response.recommendations is not None

    @pytest.mark.asyncio
    async def test_monitoring_targets_definition(self, monitoring_guard, basic_request):
        """🟢 監視ターゲット定義テスト"""
        response = await monitoring_guard.process_request(basic_request)
        
        assert response.success is True
        
        # 監視ターゲットの確認
        targets = response.monitoring_config.targets
        target_jobs = [target["job"] for target in targets]
        
        assert "web-server" in target_jobs
        assert "database-postgresql" in target_jobs
        assert "application-web_app" in target_jobs
        assert "node-exporter" in target_jobs

    @pytest.mark.asyncio
    async def test_metrics_definition(self, monitoring_guard, basic_request):
        """🟢 メトリクス定義テスト"""
        response = await monitoring_guard.process_request(basic_request)
        
        assert response.success is True
        
        # メトリクス定義の確認
        metrics = response.monitoring_config.metrics
        metric_names = [metric.name for metric in metrics]
        
        # システムメトリクス
        assert "cpu_usage_percent" in metric_names
        assert "memory_usage_bytes" in metric_names
        assert "disk_usage_percent" in metric_names
        
        # アプリケーションメトリクス
        assert "http_requests_total" in metric_names
        assert "application_errors_total" in metric_names

    @pytest.mark.asyncio
    async def test_alert_rules_definition(self, monitoring_guard, basic_request):
        """🟢 アラートルール定義テスト"""
        response = await monitoring_guard.process_request(basic_request)
        
        assert response.success is True
        
        # アラートルールの確認
        alerts = response.monitoring_config.alerts
        alert_names = [alert.name for alert in alerts]
        
        # システムアラート
        assert "HighCPUUsage" in alert_names
        assert "HighMemoryUsage" in alert_names
        assert "DiskSpaceLow" in alert_names
        
        # アプリケーションアラート
        assert "HighErrorRate" in alert_names
        assert "ServiceDown" in alert_names

    @pytest.mark.asyncio
    async def test_dashboard_definition(self, monitoring_guard, basic_request):
        """🟢 ダッシュボード定義テスト"""
        response = await monitoring_guard.process_request(basic_request)
        
        assert response.success is True
        
        # ダッシュボード定義の確認
        dashboards = response.monitoring_config.dashboards
        dashboard_names = [dashboard.name for dashboard in dashboards]
        
        assert "system_overview" in dashboard_names
        assert "application_monitoring" in dashboard_names
        assert "database_monitoring" in dashboard_names

    @pytest.mark.asyncio
    async def test_notification_channels_setup(self, monitoring_guard):
        """🟢 通知チャンネル設定テスト"""
        request = MonitoringGuardRequest(
            action="setup_monitoring",
            config={
                "slack": {"webhook_url": "https://hooks.slack.com/...", "channel": "#alerts"},
                "email": {"addresses": ["admin@example.com"]},
                "discord": {"webhook_url": "https://discord.com/api/webhooks/..."},
            }
        )
        
        response = await monitoring_guard.process_request(request)
        
        assert response.success is True
        
        # 通知チャンネルの確認
        channels = response.monitoring_config.notification_channels
        channel_names = [channel["name"] for channel in channels]
        
        assert "slack" in channel_names
        assert "email" in channel_names
        assert "discord" in channel_names

    @pytest.mark.asyncio
    async def test_retention_policies_definition(self, monitoring_guard, basic_request):
        """🟢 保持ポリシー定義テスト"""
        response = await monitoring_guard.process_request(basic_request)
        
        assert response.success is True
        
        # 保持ポリシーの確認
        retention_policies = response.monitoring_config.retention_policies
        
        assert "metrics_retention" in retention_policies
        assert "logs_retention" in retention_policies
        assert "alerts_history_retention" in retention_policies
        assert retention_policies["metrics_retention"] == "30d"

    @pytest.mark.asyncio
    async def test_global_settings_definition(self, monitoring_guard, basic_request):
        """🟢 グローバル設定定義テスト"""
        response = await monitoring_guard.process_request(basic_request)
        
        assert response.success is True
        
        # グローバル設定の確認
        global_settings = response.monitoring_config.global_settings
        
        assert "scrape_interval" in global_settings
        assert "evaluation_interval" in global_settings
        assert "query_timeout" in global_settings

    @pytest.mark.asyncio
    async def test_prometheus_config(self, monitoring_guard):
        """🟢 Prometheus設定テスト"""
        prometheus_config = monitoring_guard._get_prometheus_config()
        
        assert prometheus_config["name"] == "prometheus"
        assert "version" in prometheus_config
        assert "port" in prometheus_config
        assert prometheus_config["port"] == 9090

    @pytest.mark.asyncio
    async def test_grafana_config(self, monitoring_guard):
        """🟢 Grafana設定テスト"""
        grafana_config = monitoring_guard._get_grafana_config()
        
        assert grafana_config["name"] == "grafana"
        assert "version" in grafana_config
        assert "port" in grafana_config
        assert grafana_config["port"] == 3000

    @pytest.mark.asyncio
    async def test_elk_config(self, monitoring_guard):
        """🟢 ELK Stack設定テスト"""
        elk_config = monitoring_guard._get_elk_config()
        
        assert elk_config["name"] == "elk"
        assert "elasticsearch" in elk_config
        assert "logstash" in elk_config
        assert "kibana" in elk_config

    @pytest.mark.asyncio
    async def test_metric_definition_creation(self):
        """🟢 MetricDefinitionデータクラステスト"""
        metric = MetricDefinition(
            name="test_metric",
            type=MetricType.GAUGE,
            description="Test metric",
            labels={"instance": "test"},
            unit="bytes"
        )
        
        assert metric.name == "test_metric"
        assert metric.type == MetricType.GAUGE
        assert metric.description == "Test metric"
        assert metric.labels["instance"] == "test"
        assert metric.unit == "bytes"

    @pytest.mark.asyncio
    async def test_alert_rule_creation(self):
        """🟢 AlertRuleデータクラステスト"""
        alert = AlertRule(
            name="TestAlert",
            expression="cpu_usage > 80",
            severity=AlertSeverity.HIGH,
            description="High CPU usage",
            threshold=80,
            duration="5m",
            labels={"team": "ops"}
        )
        
        assert alert.name == "TestAlert"
        assert alert.expression == "cpu_usage > 80"
        assert alert.severity == AlertSeverity.HIGH
        assert alert.threshold == 80
        assert alert.duration == "5m"
        assert alert.labels["team"] == "ops"

    @pytest.mark.asyncio
    async def test_dashboard_creation(self):
        """🟢 Dashboardデータクラステスト"""
        dashboard = Dashboard(
            name="test_dashboard",
            title="Test Dashboard",
            description="Test dashboard description",
            panels=[{"title": "CPU Usage", "type": "stat"}],
            tags=["system", "monitoring"]
        )
        
        assert dashboard.name == "test_dashboard"
        assert dashboard.title == "Test Dashboard"
        assert len(dashboard.panels) == 1
        assert "system" in dashboard.tags
        assert dashboard.refresh_interval == "30s"  # デフォルト値

    @pytest.mark.asyncio
    async def test_predefined_metrics_loading(self, monitoring_guard):
        """🟢 事前定義メトリクス読み込みテスト"""
        predefined_metrics = monitoring_guard._load_predefined_metrics()
        
        assert len(predefined_metrics) > 0
        metric_names = [metric.name for metric in predefined_metrics]
        assert "system_uptime_seconds" in metric_names
        assert "process_count" in metric_names

    @pytest.mark.asyncio
    async def test_predefined_alerts_loading(self, monitoring_guard):
        """🟢 事前定義アラート読み込みテスト"""
        predefined_alerts = monitoring_guard._load_predefined_alerts()
        
        assert len(predefined_alerts) > 0
        alert_names = [alert.name for alert in predefined_alerts]
        assert "SystemDown" in alert_names

    @pytest.mark.asyncio
    async def test_dashboard_templates_loading(self, monitoring_guard):
        """🟢 ダッシュボードテンプレート読み込みテスト"""
        dashboard_templates = monitoring_guard._load_dashboard_templates()
        
        assert "basic_system" in dashboard_templates
        basic_template = dashboard_templates["basic_system"]
        assert basic_template.name == "basic_system"

    @pytest.mark.asyncio
    async def test_notification_channels_loading(self, monitoring_guard):
        """🟢 通知チャンネル読み込みテスト"""
        notification_channels = monitoring_guard._load_notification_channels()
        
        assert len(notification_channels) > 0
        channel_names = [channel["name"] for channel in notification_channels]
        assert "default_email" in channel_names

    @pytest.mark.asyncio
    async def test_custom_metrics_support(self, monitoring_guard):
        """🟢 カスタムメトリクスサポートテスト"""
        request = MonitoringGuardRequest(
            action="setup_monitoring",
            config={
                "custom_metrics": [
                    {
                        "name": "custom_business_metric",
                        "type": "gauge",
                        "description": "Custom business metric",
                        "unit": "count",
                        "labels": {"department": "sales"}
                    }
                ]
            }
        )
        
        response = await monitoring_guard.process_request(request)
        
        assert response.success is True
        
        # カスタムメトリクスが含まれることを確認
        metrics = response.monitoring_config.metrics
        metric_names = [metric.name for metric in metrics]
        assert "custom_business_metric" in metric_names

    @pytest.mark.asyncio
    async def test_custom_alerts_support(self, monitoring_guard):
        """🟢 カスタムアラートサポートテスト"""
        request = MonitoringGuardRequest(
            action="setup_monitoring",
            config={
                "custom_alerts": [
                    {
                        "name": "CustomBusinessAlert",
                        "expression": "business_metric > 100",
                        "severity": "high",
                        "description": "Business metric threshold exceeded",
                        "threshold": 100,
                        "duration": "2m"
                    }
                ]
            }
        )
        
        response = await monitoring_guard.process_request(request)
        
        assert response.success is True
        
        # カスタムアラートが含まれることを確認
        alerts = response.monitoring_config.alerts
        alert_names = [alert.name for alert in alerts]
        assert "CustomBusinessAlert" in alert_names

    @pytest.mark.asyncio
    async def test_unsupported_action(self, monitoring_guard):
        """🔴 サポートされていないアクションテスト"""
        request = MonitoringGuardRequest(action="unsupported_action")
        response = await monitoring_guard.process_request(request)
        
        assert response.success is False
        assert "サポートされていないアクション" in response.error_message

    @pytest.mark.asyncio
    async def test_metrics_retrieval(self, monitoring_guard):
        """🟢 品質メトリクス取得テスト"""
        metrics = await monitoring_guard.get_metrics()
        
        assert isinstance(metrics, dict)
        assert "root_cause_resolution" in metrics
        assert "test_coverage" in metrics
        assert "security_score" in metrics
        
        # Iron Will基準の確認
        assert metrics["root_cause_resolution"] >= 95.0
        assert metrics["test_coverage"] >= 95.0
        assert metrics["security_score"] >= 90.0

    @pytest.mark.asyncio
    async def test_error_handling(self, monitoring_guard):
        """🔴 エラーハンドリングテスト"""
        # 不正なリクエストでエラーが適切に処理されることを確認
        with patch.object(monitoring_guard, '_setup_monitoring', side_effect=Exception("Test error")):
            request = MonitoringGuardRequest(action="setup_monitoring")
            response = await monitoring_guard.process_request(request)
            
            assert response.success is False
            assert "処理エラー" in response.error_message

    @pytest.mark.asyncio
    async def test_system_health_monitoring(self, monitoring_guard):
        """🟢 システム健全性監視テスト"""
        # システム健全性チェックは実装されていないため、基本テストのみ
        request = MonitoringGuardRequest(action="check_system_health")
        response = await monitoring_guard.process_request(request)
        
        # デフォルト実装では成功を返す
        assert response.success is True

    @pytest.mark.asyncio
    async def test_alert_severity_levels(self):
        """🟢 アラート重要度レベルテスト"""
        # すべての重要度レベルが定義されていることを確認
        severities = list(AlertSeverity)
        severity_values = [s.value for s in severities]
        
        assert "critical" in severity_values
        assert "high" in severity_values
        assert "medium" in severity_values
        assert "low" in severity_values
        assert "info" in severity_values

    @pytest.mark.asyncio
    async def test_metric_types(self):
        """🟢 メトリクスタイプテスト"""
        # すべてのメトリクスタイプが定義されていることを確認
        metric_types = list(MetricType)
        type_values = [mt.value for mt in metric_types]
        
        assert "counter" in type_values
        assert "gauge" in type_values
        assert "histogram" in type_values
        assert "summary" in type_values

    @pytest.mark.asyncio
    async def test_monitoring_config_validation(self, monitoring_guard, basic_request):
        """🟢 監視設定検証テスト"""
        response = await monitoring_guard.process_request(basic_request)
        
        assert response.success is True
        
        # 設定検証結果の確認
        config = response.monitoring_config
        
        # 必要なコンポーネントが含まれることを確認
        assert len(config.targets) > 0
        assert len(config.metrics) > 0
        assert len(config.alerts) > 0
        assert len(config.dashboards) > 0

    @pytest.mark.asyncio
    async def test_cache_functionality(self, monitoring_guard):
        """🟢 キャッシュ機能テスト"""
        # キャッシュ機能の基本テスト
        assert monitoring_guard.cache_ttl == 300  # 5分
        assert isinstance(monitoring_guard.health_cache, dict)

    @pytest.mark.asyncio
    async def test_concurrent_monitoring_setup(self, monitoring_guard):
        """🔵 並行監視設定テスト（リファクタリング品質確認）"""
        # 複数の監視設定を並行実行
        requests = [
            MonitoringGuardRequest(
                action="setup_monitoring",
                target_system=f"system_{i}",
                config={"environment": "test"}
            )
            for i in range(3)
        ]
        
        # 並行実行
        responses = await asyncio.gather(*[
            monitoring_guard.process_request(req) for req in requests
        ])
        
        # すべてのレスポンスが成功することを確認
        for response in responses:
            assert response.success is True
            assert response.monitoring_config is not None