#!/usr/bin/env python3
"""
ContainerCrafter (D12) テストスイート

Docker/Podman/Kubernetes等のコンテナ技術専門サーバントのテスト
"""

import asyncio
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, Mock

from libs.elder_servants.dwarf_workshop.container_crafter import (
    ContainerCrafter,
    ContainerMetrics,
    BuildResult,
    DeploymentResult
)
from libs.elder_servants.base.elder_servant import (
    ServantRequest,
    TaskPriority,
    TaskStatus
)


class TestContainerCrafter:
    """ContainerCrafter テストクラス"""

    def setup_method(self):
        """テストセットアップ"""
        self.servant = ContainerCrafter()

    def test_initialization(self):
        """初期化テスト"""
        assert self.servant.servant_id == "D12"
        assert self.servant.servant_name == "ContainerCrafter"
        assert self.servant.specialization == "コンテナ技術"
        assert len(self.servant.capabilities) > 0

    def test_capabilities(self):
        """能力定義テスト"""
        capabilities = self.servant.get_all_capabilities()
        capability_names = [cap.name for cap in capabilities]
        
        assert "dockerfile_generation" in capability_names
        assert "image_build" in capability_names
        assert "container_run" in capability_names
        assert "kubernetes_manifest" in capability_names
        assert "docker_compose" in capability_names

    @pytest.mark.asyncio
    async def test_dockerfile_generation(self):
        """Dockerfile生成テスト"""
        request = ServantRequest(
            task_id="test_dockerfile_001",
            task_type="dockerfile_generation",
            priority=TaskPriority.MEDIUM,
            payload={
                "spec": {
                    "base_image": "python:3.9-slim",
                    "working_dir": "/app",
                    "dependencies": ["requirements.txt"],
                    "commands": ["pip install -r requirements.txt"],
                    "expose_ports": [8000],
                    "environment": {"PYTHONPATH": "/app"}
                }
            }
        )
        
        response = await self.servant.process_request(request)
        
        assert response.status == TaskStatus.COMPLETED
        assert response.quality_score >= 95.0
        assert "dockerfile" in response.result_data
        assert "FROM python:3.9-slim" in response.result_data["dockerfile"]

    @pytest.mark.asyncio
    async def test_docker_compose_generation(self):
        """Docker Compose生成テスト"""
        request = ServantRequest(
            task_id="test_compose_001",
            task_type="docker_compose",
            priority=TaskPriority.MEDIUM,
            payload={
                "spec": {
                    "services": {
                        "web": {
                            "image": "nginx:latest",
                            "ports": ["80:80"]
                        },
                        "db": {
                            "image": "postgres:13",
                            "environment": {
                                "POSTGRES_PASSWORD": "secret"
                            }
                        }
                    }
                }
            }
        )
        
        response = await self.servant.process_request(request)
        
        assert response.status == TaskStatus.COMPLETED
        assert response.quality_score >= 95.0
        assert "compose_yaml" in response.result_data

    @pytest.mark.asyncio
    async def test_kubernetes_manifest_generation(self):
        """Kubernetes マニフェスト生成テスト"""
        request = ServantRequest(
            task_id="test_k8s_001",
            task_type="kubernetes_manifest",
            priority=TaskPriority.HIGH,
            payload={
                "spec": {
                    "app_name": "test-app",
                    "image": "test-app:latest",
                    "replicas": 3,
                    "port": 8080,
                    "service_type": "LoadBalancer"
                }
            }
        )
        
        response = await self.servant.process_request(request)
        
        assert response.status == TaskStatus.COMPLETED
        assert response.quality_score >= 95.0
        assert "manifests" in response.result_data
        assert len(response.result_data["manifests"]) >= 2  # Deployment + Service

    @pytest.mark.asyncio
    async def test_container_security_scan(self):
        """コンテナセキュリティスキャンテスト"""
        request = ServantRequest(
            task_id="test_security_001",
            task_type="security_scan",
            priority=TaskPriority.HIGH,
            payload={
                "image": "nginx:latest",
                "scan_type": "vulnerability"
            }
        )
        
        response = await self.servant.process_request(request)
        
        assert response.status == TaskStatus.COMPLETED
        assert response.quality_score >= 95.0
        assert "scan_results" in response.result_data

    @pytest.mark.asyncio
    async def test_container_optimization(self):
        """コンテナ最適化テスト"""
        dockerfile_content = '''
        FROM ubuntu:20.04
        RUN apt-get update
        RUN apt-get install -y python3
        COPY . /app
        WORKDIR /app
        '''
        
        request = ServantRequest(
            task_id="test_optimize_001",
            task_type="container_optimization",
            priority=TaskPriority.MEDIUM,
            payload={
                "dockerfile": dockerfile_content
            }
        )
        
        response = await self.servant.process_request(request)
        
        assert response.status == TaskStatus.COMPLETED
        assert response.quality_score >= 95.0
        assert "optimized_dockerfile" in response.result_data

    @pytest.mark.asyncio
    async def test_multi_arch_build(self):
        """マルチアーキテクチャビルドテスト"""
        request = ServantRequest(
            task_id="test_multiarch_001",
            task_type="multi_arch_build",
            priority=TaskPriority.HIGH,
            payload={
                "image_name": "test-app",
                "platforms": ["linux/amd64", "linux/arm64"],
                "dockerfile": "FROM alpine:latest\nCOPY . /app"
            }
        )
        
        response = await self.servant.process_request(request)
        
        assert response.status == TaskStatus.COMPLETED
        assert response.quality_score >= 95.0
        assert "build_manifest" in response.result_data

    @pytest.mark.asyncio
    async def test_helm_chart_generation(self):
        """Helm Chart生成テスト"""
        request = ServantRequest(
            task_id="test_helm_001",
            task_type="helm_chart",
            priority=TaskPriority.MEDIUM,
            payload={
                "chart_name": "my-app",
                "app_version": "1.0.0",
                "image": "my-app:1.0.0",
                "values": {
                    "replicaCount": 2,
                    "service": {"port": 80}
                }
            }
        )
        
        response = await self.servant.process_request(request)
        
        assert response.status == TaskStatus.COMPLETED
        assert response.quality_score >= 95.0
        assert "chart_files" in response.result_data

    @pytest.mark.asyncio
    async def test_container_registry_operations(self):
        """コンテナレジストリ操作テスト"""
        request = ServantRequest(
            task_id="test_registry_001",
            task_type="registry_operation",
            priority=TaskPriority.MEDIUM,
            payload={
                "operation": "list_tags",
                "registry": "docker.io",
                "repository": "library/nginx"
            }
        )
        
        response = await self.servant.process_request(request)
        
        assert response.status == TaskStatus.COMPLETED
        assert response.quality_score >= 95.0
        assert "tags" in response.result_data

    def test_request_validation(self):
        """リクエスト検証テスト"""
        # 有効なリクエスト
        valid_request = ServantRequest(
            task_id="test_001",
            task_type="dockerfile_generation",
            priority=TaskPriority.MEDIUM,
            payload={"spec": {"base_image": "python:3.9"}}
        )
        assert self.servant.validate_request(valid_request)
        
        # 無効なリクエスト（ペイロードなし）
        invalid_request = ServantRequest(
            task_id="test_002",
            task_type="dockerfile_generation",
            priority=TaskPriority.MEDIUM,
            payload={}
        )
        assert not self.servant.validate_request(invalid_request)

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """エラーハンドリングテスト"""
        request = ServantRequest(
            task_id="test_error_001",
            task_type="invalid_task_type",
            priority=TaskPriority.MEDIUM,
            payload={"invalid": "data"}
        )
        
        response = await self.servant.process_request(request)
        
        assert response.status == TaskStatus.FAILED
        assert response.error_message is not None
        assert response.quality_score == 0.0

    @pytest.mark.asyncio
    async def test_iron_will_quality_compliance(self):
        """Iron Will品質基準準拠テスト"""
        request = ServantRequest(
            task_id="test_quality_001",
            task_type="dockerfile_generation",
            priority=TaskPriority.HIGH,
            payload={
                "spec": {
                    "base_image": "python:3.9-slim",
                    "working_dir": "/app"
                }
            }
        )
        
        response = await self.servant.process_request(request)
        
        # Iron Will基準：95%以上
        assert response.quality_score >= 95.0
        assert response.status == TaskStatus.COMPLETED
        
        # 品質検証
        quality_score = await self.servant.validate_iron_will_quality(response.result_data)
        assert quality_score >= 95.0

    @pytest.mark.asyncio
    async def test_health_check(self):
        """ヘルスチェックテスト"""
        health = await self.servant.health_check()
        
        assert health["success"] is True
        assert health["servant_id"] == "D12"
        assert health["servant_name"] == "ContainerCrafter"
        assert "status" in health
        assert "stats" in health


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])