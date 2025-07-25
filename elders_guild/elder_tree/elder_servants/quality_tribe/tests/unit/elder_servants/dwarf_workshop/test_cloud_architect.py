"""
CloudArchitect (D13) のテストケース

TDD方式でクラウド設計師の各機能をテストします。
包括的なクラウドアーキテクチャ設計機能の品質を保証。
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# テスト対象のインポート
sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from elders_guild.elder_tree.elder_servants.dwarf_workshop.cloud_architect import (
    CloudArchitect,
    CloudArchitectRequest,
    CloudArchitectResponse,
    CloudArchitecture,
    CloudResource,
    CloudMigrationPlan,
    CloudOptimizationReport,
)


class TestCloudArchitect:
    """CloudArchitect (D13) テストスイート"""

    @pytest.fixture
    def cloud_architect(self):
        """CloudArchitectインスタンスを作成"""
        return CloudArchitect()

    @pytest.fixture
    def basic_request(self):
        """基本的なリクエストを作成"""
        return CloudArchitectRequest(
            action="design_architecture",
            project_name="test_project",
            requirements={
                "type": "web_application",
                "scale": "medium",
                "provider": "aws",
                "environment": "production",
            },
            constraints={
                "budget": 1000,
                "region": "us-west-2",
            },
        )

    def test_cloud_architect_initialization(self, cloud_architect):
        """🔴 CloudArchitectの初期化テスト"""
        assert cloud_architect.servant_id == "D13"
        assert cloud_architect.name == "CloudArchitect"
        assert cloud_architect.supported_providers is not None
        assert "aws" in cloud_architect.supported_providers
        assert "azure" in cloud_architect.supported_providers
        assert "gcp" in cloud_architect.supported_providers

    def test_cloud_architect_capabilities(self, cloud_architect):
        """🔴 CloudArchitectの能力一覧テスト"""
        capabilities = cloud_architect.get_capabilities()
        
        assert "クラウドアーキテクチャ設計" in capabilities
        assert "マルチクラウド対応" in capabilities
        assert "コスト最適化" in capabilities
        assert "セキュリティ強化" in capabilities
        assert len(capabilities) >= 8

    @pytest.mark.asyncio
    async def test_validate_request_valid(self, cloud_architect, basic_request):
        """🔴 有効なリクエストの検証テスト"""
        is_valid = await cloud_architect.validate_request(basic_request)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_request_invalid_action(self, cloud_architect):
        """🔴 無効なアクションのリクエスト検証テスト"""
        invalid_request = CloudArchitectRequest(action="invalid_action")
        is_valid = await cloud_architect.validate_request(invalid_request)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_design_architecture_success(self, cloud_architect, basic_request):
        """🟢 アーキテクチャ設計成功テスト"""
        response = await cloud_architect.process_request(basic_request)
        
        assert response.success is True
        assert response.architecture is not None
        assert response.architecture.name == "test_project"
        assert response.architecture.provider == "aws"
        assert len(response.architecture.resources) > 0
        assert response.recommendations is not None
        assert len(response.recommendations) > 0

    @pytest.mark.asyncio
    async def test_design_architecture_invalid_provider(self, cloud_architect):
        """🔴 無効なプロバイダーでのアーキテクチャ設計テスト"""
        request = CloudArchitectRequest(
            action="design_architecture",
            requirements={"provider": "invalid_provider"}
        )
        
        response = await cloud_architect.process_request(request)
        
        assert response.success is False
        assert "サポートされていないプロバイダー" in response.error_message

    @pytest.mark.asyncio
    async def test_design_architecture_microservices(self, cloud_architect):
        """🟢 マイクロサービスアーキテクチャ設計テスト"""
        request = CloudArchitectRequest(
            action="design_architecture",
            project_name="microservices_app",
            requirements={
                "type": "microservices",
                "scale": "large",
                "provider": "aws",
            }
        )
        
        response = await cloud_architect.process_request(request)
        
        assert response.success is True
        assert response.architecture.name == "microservices_app"
        # マイクロサービス特有のリソースが含まれることを確認
        resource_types = [r.type for r in response.architecture.resources]
        assert any("vpc" in rt or "virtual_network" in rt for rt in resource_types)

    @pytest.mark.asyncio
    async def test_cost_estimation(self, cloud_architect, basic_request):
        """🟢 コスト見積もりテスト"""
        response = await cloud_architect.process_request(basic_request)
        
        assert response.success is True
        assert response.architecture.estimated_monthly_cost is not None
        assert response.architecture.estimated_monthly_cost > 0
        assert response.cost_analysis is not None

    @pytest.mark.asyncio
    async def test_security_configuration(self, cloud_architect, basic_request):
        """🟢 セキュリティ設定テスト"""
        response = await cloud_architect.process_request(basic_request)
        
        assert response.success is True
        
        # セキュリティ設定の確認
        security_config = response.architecture.security_config
        assert security_config["encryption"]["at_rest"] is True
        assert security_config["encryption"]["in_transit"] is True
        assert security_config["access_control"]["mfa_required"] is True

    @pytest.mark.asyncio
    async def test_monitoring_configuration(self, cloud_architect, basic_request):
        """🟢 監視設定テスト"""
        response = await cloud_architect.process_request(basic_request)
        
        assert response.success is True
        
        # 監視設定の確認
        monitoring_config = response.architecture.monitoring_config
        assert "metrics" in monitoring_config
        assert "logging" in monitoring_config
        assert "alerting" in monitoring_config
        assert monitoring_config["logging"]["centralized"] is True

    @pytest.mark.asyncio
    async def test_disaster_recovery_configuration(self, cloud_architect, basic_request):
        """🟢 災害復旧設定テスト"""
        response = await cloud_architect.process_request(basic_request)
        
        assert response.success is True
        
        # 災害復旧設定の確認
        dr_config = response.architecture.disaster_recovery
        assert "strategy" in dr_config
        assert "backup" in dr_config
        assert "testing" in dr_config
        assert dr_config["backup"]["automated"] is True

    @pytest.mark.asyncio
    async def test_resource_generation(self, cloud_architect, basic_request):
        """🟢 リソース生成テスト"""
        response = await cloud_architect.process_request(basic_request)
        
        assert response.success is True
        
        resources = response.architecture.resources
        assert len(resources) > 0
        
        # 必要なリソースタイプが含まれることを確認
        resource_types = [r.type for r in resources]
        assert any("vpc" in rt or "virtual_network" in rt for rt in resource_types)
        assert any("security_group" in rt for rt in resource_types)

    @pytest.mark.asyncio
    async def test_network_design(self, cloud_architect, basic_request):
        """🟢 ネットワーク設計テスト"""
        response = await cloud_architect.process_request(basic_request)
        
        assert response.success is True
        
        # ネットワーク設定の確認
        network_config = response.architecture.network_config
        assert network_config["architecture"] == "three_tier"
        assert "subnets" in network_config
        assert "public" in network_config["subnets"]
        assert "private" in network_config["subnets"]

    @pytest.mark.asyncio
    async def test_cost_optimization_design(self, cloud_architect, basic_request):
        """🟢 コスト最適化設計テスト"""
        response = await cloud_architect.process_request(basic_request)
        
        assert response.success is True
        
        # コスト最適化設定の確認
        cost_opt = response.architecture.cost_optimization
        assert cost_opt["compute"]["spot_instances"] is True
        assert cost_opt["storage"]["tiering"] is True
        assert cost_opt["automation"]["unused_resource_cleanup"] is True

    @pytest.mark.asyncio
    async def test_unsupported_action(self, cloud_architect):
        """🔴 サポートされていないアクションテスト"""
        request = CloudArchitectRequest(action="unsupported_action")
        response = await cloud_architect.process_request(request)
        
        assert response.success is False
        assert "サポートされていないアクション" in response.error_message

    @pytest.mark.asyncio
    async def test_aws_provider_config(self, cloud_architect):
        """🟢 AWSプロバイダー設定テスト"""
        aws_config = cloud_architect._get_aws_config()
        
        assert aws_config["name"] == "aws"
        assert "default_region" in aws_config
        assert "instance_types" in aws_config
        assert "db_instance_types" in aws_config

    @pytest.mark.asyncio
    async def test_azure_provider_config(self, cloud_architect):
        """🟢 Azureプロバイダー設定テスト"""
        azure_config = cloud_architect._get_azure_config()
        
        assert azure_config["name"] == "azure"
        assert "default_region" in azure_config
        assert "instance_types" in azure_config

    @pytest.mark.asyncio
    async def test_gcp_provider_config(self, cloud_architect):
        """🟢 GCPプロバイダー設定テスト"""
        gcp_config = cloud_architect._get_gcp_config()
        
        assert gcp_config["name"] == "gcp"
        assert "default_region" in gcp_config
        assert "instance_types" in gcp_config

    @pytest.mark.asyncio
    async def test_template_loading(self, cloud_architect):
        """🟢 テンプレート読み込みテスト"""
        templates = cloud_architect.architecture_templates
        
        assert "microservices" in templates
        assert "serverless" in templates
        assert "container_orchestration" in templates
        
        # テンプレート構造の確認
        microservices_template = templates["microservices"]
        assert "compute" in microservices_template
        assert "network" in microservices_template

    @pytest.mark.asyncio
    async def test_instance_type_selection(self, cloud_architect):
        """🟢 インスタンスタイプ選択テスト"""
        provider_config = cloud_architect._get_aws_config()
        
        # 様々なスケールでのインスタンスタイプ選択
        small_instance = cloud_architect._select_instance_type("small", provider_config["instance_types"])
        medium_instance = cloud_architect._select_instance_type("medium", provider_config["instance_types"])
        large_instance = cloud_architect._select_instance_type("large", provider_config["instance_types"])
        
        assert small_instance == "t3.0small"
        assert medium_instance == "t3.0medium"
        assert large_instance == "t3.0large"

    @pytest.mark.asyncio
    async def test_database_instance_selection(self, cloud_architect):
        """🟢 DBインスタンスタイプ選択テスト"""
        provider_config = cloud_architect._get_aws_config()
        
        # 様々なスケールでのDBインスタンスタイプ選択
        small_db = cloud_architect._select_db_instance_type("small", provider_config["db_instance_types"])
        medium_db = cloud_architect._select_db_instance_type("medium", provider_config["db_instance_types"])
        
        assert small_db == "db.t3.0micro"
        assert medium_db == "db.t3.0small"

    @pytest.mark.asyncio
    async def test_metrics_retrieval(self, cloud_architect):
        """🟢 品質メトリクス取得テスト"""
        metrics = await cloud_architect.get_metrics()
        
        assert isinstance(metrics, dict)
        assert "root_cause_resolution" in metrics
        assert "test_coverage" in metrics
        assert "security_score" in metrics
        
        # Iron Will基準の確認
        assert metrics["root_cause_resolution"] >= 95.0
        assert metrics["test_coverage"] >= 95.0
        assert metrics["security_score"] >= 90.0

    @pytest.mark.asyncio
    async def test_error_handling(self, cloud_architect):
        """🔴 エラーハンドリングテスト"""
        # 不正なリクエストでエラーが適切に処理されることを確認
        with patch.object(cloud_architect, '_design_architecture', side_effect=Exception("Test error")):
            request = CloudArchitectRequest(action="design_architecture")
            response = await cloud_architect.process_request(request)
            
            assert response.success is False
            assert "処理エラー" in response.error_message

    @pytest.mark.asyncio
    async def test_serverless_template(self, cloud_architect):
        """🟢 サーバーレステンプレートテスト"""
        request = CloudArchitectRequest(
            action="design_architecture",
            requirements={
                "type": "serverless",
                "provider": "aws",
            }
        )
        
        response = await cloud_architect.process_request(request)
        
        assert response.success is True
        assert response.architecture.provider == "aws"

    @pytest.mark.asyncio
    async def test_data_pipeline_template(self, cloud_architect):
        """🟢 データパイプラインテンプレートテスト"""
        request = CloudArchitectRequest(
            action="design_architecture",
            requirements={
                "type": "data_pipeline",
                "provider": "gcp",
            }
        )
        
        response = await cloud_architect.process_request(request)
        
        assert response.success is True
        assert response.architecture.provider == "gcp"

    @pytest.mark.asyncio
    async def test_generate_recommendations(self, cloud_architect, basic_request):
        """🟢 推奨事項生成テスト"""
        response = await cloud_architect.process_request(basic_request)
        
        assert response.success is True
        assert len(response.recommendations) > 0
        
        # 一般的な推奨事項が含まれることを確認
        recommendations_text = " ".join(response.recommendations)
        assert "WAF" in recommendations_text or "セキュリティ" in recommendations_text
        assert "CDN" in recommendations_text or "パフォーマンス" in recommendations_text

    def test_cloud_resource_creation(self):
        """🟢 CloudResourceデータクラステスト"""
        resource = CloudResource(
            name="test-vpc",
            type="aws_vpc",
            provider="aws",
            region="us-west-2",
            configuration={"cidr_block": "10.0.0.0/16"},
            tags={"Environment": "test"}
        )
        
        assert resource.name == "test-vpc"
        assert resource.type == "aws_vpc"
        assert resource.provider == "aws"
        assert resource.configuration["cidr_block"] == "10.0.0.0/16"
        assert resource.tags["Environment"] == "test"
        assert resource.dependencies == []  # デフォルト値

    def test_cloud_architecture_creation(self):
        """🟢 CloudArchitectureデータクラステスト"""
        from datetime import datetime
        
        resources = [
            CloudResource(
                name="test-vpc",
                type="aws_vpc", 
                provider="aws",
                region="us-west-2",
                configuration={}
            )
        ]
        
        architecture = CloudArchitecture(
            name="test-architecture",
            description="Test architecture",
            provider="aws",
            resources=resources,
            network_config={},
            security_config={},
            monitoring_config={},
            cost_optimization={},
            disaster_recovery={},
            created_at=datetime.now(),
            estimated_monthly_cost=500.0
        )
        
        assert architecture.name == "test-architecture"
        assert architecture.provider == "aws"
        assert len(architecture.resources) == 1
        assert architecture.estimated_monthly_cost == 500.0

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, cloud_architect):
        """🔵 並行リクエスト処理テスト（リファクタリング品質確認）"""
        # 複数のリクエストを並行実行
        requests = [
            CloudArchitectRequest(
                action="design_architecture",
                project_name=f"project_{i}",
                requirements={"type": "web_application", "provider": "aws"}
            )
            for i in range(3)
        ]
        
        # 並行実行
        responses = await asyncio.gather(*[
            cloud_architect.process_request(req) for req in requests
        ])
        
        # すべてのレスポンスが成功することを確認
        for response in responses:
            assert response.success is True
            assert response.architecture is not None