"""
ContainerCrafter (D12) - Container Orchestration Specialist Test Suite

This module contains comprehensive tests for the ContainerCrafter servant,
which specializes in container building, optimization, and orchestration.

Test Categories:
1. Basic Initialization and Configuration
2. Container Building and Dockerfile Management
3. Image Optimization and Security
4. Registry Management Operations
5. Orchestration Deployment (K8s, Swarm, ECS)
6. Scaling and Load Balancing
7. Health Monitoring and Logging
8. Resource Management
9. Network and Storage Configuration
10. Elder System Integration
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List
import json
import yaml
from datetime import datetime

# Import the servant to be tested
from libs.elder_servants.dwarf_workshop.container_crafter import ContainerCrafter


class TestContainerCrafterInitialization:
    """Test suite for ContainerCrafter initialization and configuration."""
    
    def test_servant_metadata(self):
        """Test servant has correct metadata."""
        servant = ContainerCrafter()
        
        assert servant.servant_id == "D12"
        assert servant.name == "ContainerCrafter"
        assert servant.specialization == "container_orchestration"
        assert servant.category == "DWARF"
    
    def test_capabilities_list(self):
        """Test servant reports correct capabilities."""
        servant = ContainerCrafter()
        capabilities = servant.get_capabilities()
        
        expected_capabilities = [
            "container_build",
            "image_optimization", 
            "registry_management",
            "orchestration_deployment",
            "scaling_management",
            "health_monitoring"
        ]
        
        for capability in expected_capabilities:
            assert capability in capabilities
    
    def test_platform_support(self):
        """Test servant supports required platforms."""
        servant = ContainerCrafter()
        
        platforms = [
            "docker", "kubernetes", "swarm",
            "ecs", "eks", "gke", "aks", "openshift"
        ]
        
        for platform in platforms:
            assert servant.supports_platform(platform)
    
    @pytest.mark.asyncio
    async def test_initialization_with_config(self):
        """Test initialization with custom configuration."""
        config = {
            "docker_host": "tcp://localhost:2375",
            "registry_url": "registry.example.com",
            "k8s_config": "/path/to/kubeconfig"
        }
        
        servant = ContainerCrafter(config=config)
        await servant.initialize()
        
        assert servant.config["docker_host"] == config["docker_host"]
        assert servant.config["registry_url"] == config["registry_url"]
        assert servant.is_initialized


class TestContainerBuilding:
    """Test suite for container building functionality."""
    
    @pytest.mark.asyncio
    async def test_dockerfile_validation(self):
        """Test Dockerfile validation."""
        servant = ContainerCrafter()
        
        valid_dockerfile = """
        FROM python:3.9-slim
        WORKDIR /app
        COPY requirements.txt .
        RUN pip install -r requirements.txt
        COPY . .
        CMD ["python", "app.py"]
        """
        
        result = await servant.validate_dockerfile(valid_dockerfile)
        assert result["valid"] is True
        assert "warnings" in result
        assert "errors" not in result
    
    @pytest.mark.asyncio
    async def test_dockerfile_with_errors(self):
        """Test Dockerfile validation with errors."""
        servant = ContainerCrafter()
        
        invalid_dockerfile = """
        FROM 
        WORKDIR
        COPY
        RUN
        """
        
        result = await servant.validate_dockerfile(invalid_dockerfile)
        assert result["valid"] is False
        assert "errors" in result
        assert len(result["errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_container_build(self):
        """Test container image building."""
        servant = ContainerCrafter()
        
        build_request = {
            "dockerfile_path": "/path/to/Dockerfile",
            "context_path": "/path/to/context",
            "image_name": "myapp",
            "tag": "v1.0.0",
            "build_args": {
                "APP_VERSION": "1.0.0"
            }
        }
        
        with patch.object(servant, '_execute_docker_build', new_callable=AsyncMock) as mock_build:
            mock_build.return_value = {
                "image_id": "sha256:123456",
                "size": 150 * 1024 * 1024,  # 150MB
                "build_time": 45.2
            }
            
            result = await servant.build_container(build_request)
            
            assert result["success"] is True
            assert result["image_id"] == "sha256:123456"
            assert result["image_name"] == "myapp:v1.0.0"
            assert result["size_mb"] == 150
    
    @pytest.mark.asyncio
    async def test_multi_stage_build(self):
        """Test multi-stage Docker build."""
        servant = ContainerCrafter()
        
        multi_stage_dockerfile = """
        # Build stage
        FROM golang:1.19 AS builder
        WORKDIR /build
        COPY . .
        RUN go build -o app main.go
        
        # Runtime stage
        FROM alpine:latest
        RUN apk add --no-cache ca-certificates
        COPY --from=builder /build/app /app
        ENTRYPOINT ["/app"]
        """
        
        build_request = {
            "dockerfile_content": multi_stage_dockerfile,
            "image_name": "myapp",
            "tag": "slim",
            "target_stage": None  # Build all stages
        }
        
        with patch.object(servant, '_execute_docker_build', new_callable=AsyncMock) as mock_build:
            mock_build.return_value = {
                "image_id": "sha256:789012",
                "size": 25 * 1024 * 1024,  # 25MB (optimized)
                "stages_built": 2
            }
            
            result = await servant.build_multi_stage(build_request)
            
            assert result["success"] is True
            assert result["stages_built"] == 2
            assert result["size_mb"] == 25  # Much smaller than single stage


class TestImageOptimization:
    """Test suite for image optimization and security."""
    
    @pytest.mark.asyncio
    async def test_image_size_optimization(self):
        """Test image size optimization."""
        servant = ContainerCrafter()
        
        optimization_request = {
            "image_id": "sha256:123456",
            "optimization_level": "aggressive",
            "preserve_paths": ["/app", "/config"]
        }
        
        with patch.object(servant, '_analyze_image_layers', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {
                "total_size": 500 * 1024 * 1024,
                "optimizable_size": 200 * 1024 * 1024,
                "layer_count": 15
            }
            
            result = await servant.optimize_image(optimization_request)
            
            assert result["success"] is True
            assert result["original_size_mb"] == 500
            assert result["optimized_size_mb"] < 350  # At least 30% reduction
            assert result["space_saved_mb"] > 150
    
    @pytest.mark.asyncio
    async def test_security_scanning(self):
        """Test container image security scanning."""
        servant = ContainerCrafter()
        
        scan_request = {
            "image_id": "sha256:123456",
            "scan_type": "comprehensive",
            "severity_threshold": "medium"
        }
        
        with patch.object(servant, '_execute_security_scan', new_callable=AsyncMock) as mock_scan:
            mock_scan.return_value = {
                "vulnerabilities": {
                    "critical": 0,
                    "high": 2,
                    "medium": 5,
                    "low": 12
                },
                "compliance": {
                    "cis_docker_benchmark": 0.92,
                    "best_practices": 0.88
                }
            }
            
            result = await servant.scan_image_security(scan_request)
            
            assert result["success"] is True
            assert result["total_vulnerabilities"] == 19
            assert result["action_required"] is True  # Due to high vulnerabilities
            assert "recommendations" in result
    
    @pytest.mark.asyncio
    async def test_layer_optimization(self):
        """Test Docker layer optimization."""
        servant = ContainerCrafter()
        
        dockerfile_content = """
        FROM node:16
        WORKDIR /app
        COPY package*.json ./
        RUN npm install
        COPY . .
        RUN npm run build
        RUN rm -rf node_modules
        RUN npm install --production
        """
        
        result = await servant.optimize_dockerfile_layers(dockerfile_content)
        
        assert result["success"] is True
        assert result["original_layers"] == 8
        assert result["optimized_layers"] < 6  # Combined RUN commands
        assert "optimized_dockerfile" in result


class TestRegistryManagement:
    """Test suite for container registry operations."""
    
    @pytest.mark.asyncio
    async def test_registry_authentication(self):
        """Test registry authentication."""
        servant = ContainerCrafter()
        
        auth_config = {
            "registry": "registry.example.com",
            "username": "user",
            "password": "pass",
            "auth_type": "basic"
        }
        
        with patch.object(servant, '_authenticate_registry', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {
                "token": "jwt-token-123",
                "expires_in": 3600
            }
            
            result = await servant.authenticate_registry(auth_config)
            
            assert result["success"] is True
            assert "token" in result
            assert result["authenticated"] is True
    
    @pytest.mark.asyncio
    async def test_image_push(self):
        """Test pushing image to registry."""
        servant = ContainerCrafter()
        
        push_request = {
            "image_name": "myapp:v1.0.0",
            "registry": "registry.example.com",
            "repository": "myorg/myapp",
            "tags": ["v1.0.0", "latest"]
        }
        
        with patch.object(servant, '_push_to_registry', new_callable=AsyncMock) as mock_push:
            mock_push.return_value = {
                "digest": "sha256:abcdef123456",
                "size": 150 * 1024 * 1024,
                "layers_pushed": 12
            }
            
            result = await servant.push_image(push_request)
            
            assert result["success"] is True
            assert result["full_image_path"] == "registry.example.com/myorg/myapp:v1.0.0"
            assert result["digest"] == "sha256:abcdef123456"
    
    @pytest.mark.asyncio
    async def test_image_pull(self):
        """Test pulling image from registry."""
        servant = ContainerCrafter()
        
        pull_request = {
            "image": "registry.example.com/myorg/myapp:v1.0.0",
            "platform": "linux/amd64",
            "verify_signature": True
        }
        
        with patch.object(servant, '_pull_from_registry', new_callable=AsyncMock) as mock_pull:
            mock_pull.return_value = {
                "image_id": "sha256:fedcba987654",
                "size": 150 * 1024 * 1024,
                "layers_downloaded": 12,
                "signature_valid": True
            }
            
            result = await servant.pull_image(pull_request)
            
            assert result["success"] is True
            assert result["image_id"] == "sha256:fedcba987654"
            assert result["signature_valid"] is True


class TestOrchestrationDeployment:
    """Test suite for container orchestration deployment."""
    
    @pytest.mark.asyncio
    async def test_kubernetes_deployment(self):
        """Test Kubernetes deployment creation."""
        servant = ContainerCrafter()
        
        k8s_deployment = {
            "name": "myapp",
            "namespace": "production",
            "image": "myapp:v1.0.0",
            "replicas": 3,
            "resources": {
                "requests": {"cpu": "100m", "memory": "128Mi"},
                "limits": {"cpu": "500m", "memory": "512Mi"}
            },
            "ports": [{"name": "http", "port": 8080}]
        }
        
        with patch.object(servant, '_deploy_to_kubernetes', new_callable=AsyncMock) as mock_deploy:
            mock_deploy.return_value = {
                "deployment_name": "myapp",
                "replicas_created": 3,
                "service_created": True,
                "endpoint": "myapp.production.svc.cluster.local"
            }
            
            result = await servant.deploy_to_kubernetes(k8s_deployment)
            
            assert result["success"] is True
            assert result["deployment_name"] == "myapp"
            assert result["replicas_created"] == 3
            assert "endpoint" in result
    
    @pytest.mark.asyncio
    async def test_docker_swarm_service(self):
        """Test Docker Swarm service deployment."""
        servant = ContainerCrafter()
        
        swarm_service = {
            "name": "web-service",
            "image": "nginx:latest",
            "replicas": 5,
            "update_config": {
                "parallelism": 2,
                "delay": "10s",
                "failure_action": "rollback"
            },
            "networks": ["frontend"],
            "ports": ["80:80"]
        }
        
        with patch.object(servant, '_deploy_to_swarm', new_callable=AsyncMock) as mock_deploy:
            mock_deploy.return_value = {
                "service_id": "abc123xyz",
                "replicas_scheduled": 5,
                "vip": "10.0.0.5"
            }
            
            result = await servant.deploy_to_swarm(swarm_service)
            
            assert result["success"] is True
            assert result["service_id"] == "abc123xyz"
            assert result["replicas_scheduled"] == 5
    
    @pytest.mark.asyncio
    async def test_ecs_task_deployment(self):
        """Test AWS ECS task deployment."""
        servant = ContainerCrafter()
        
        ecs_task = {
            "family": "myapp-task",
            "container_definitions": [{
                "name": "app",
                "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:latest",
                "cpu": 256,
                "memory": 512,
                "essential": True
            }],
            "cluster": "production",
            "service_name": "myapp-service",
            "desired_count": 3
        }
        
        with patch.object(servant, '_deploy_to_ecs', new_callable=AsyncMock) as mock_deploy:
            mock_deploy.return_value = {
                "task_definition_arn": "arn:aws:ecs:us-east-1:123456789:task-definition/myapp-task:1",
                "service_arn": "arn:aws:ecs:us-east-1:123456789:service/myapp-service",
                "running_count": 3
            }
            
            result = await servant.deploy_to_ecs(ecs_task)
            
            assert result["success"] is True
            assert "task_definition_arn" in result
            assert result["running_count"] == 3


class TestScalingManagement:
    """Test suite for container scaling and load balancing."""
    
    @pytest.mark.asyncio
    async def test_horizontal_autoscaling(self):
        """Test horizontal pod autoscaling configuration."""
        servant = ContainerCrafter()
        
        hpa_config = {
            "name": "myapp-hpa",
            "target_deployment": "myapp",
            "min_replicas": 2,
            "max_replicas": 10,
            "metrics": [
                {"type": "cpu", "target_percentage": 70},
                {"type": "memory", "target_percentage": 80},
                {"type": "custom", "metric": "requests_per_second", "target_value": 1000}
            ]
        }
        
        result = await servant.configure_autoscaling(hpa_config)
        
        assert result["success"] is True
        assert result["hpa_name"] == "myapp-hpa"
        assert result["scaling_enabled"] is True
        assert len(result["metrics"]) == 3
    
    @pytest.mark.asyncio
    async def test_load_balancer_configuration(self):
        """Test load balancer configuration."""
        servant = ContainerCrafter()
        
        lb_config = {
            "name": "myapp-lb",
            "type": "application",  # ALB
            "target_services": ["web", "api"],
            "health_check": {
                "path": "/health",
                "interval": 30,
                "timeout": 5,
                "healthy_threshold": 2,
                "unhealthy_threshold": 3
            },
            "rules": [
                {"path": "/api/*", "target": "api"},
                {"path": "/*", "target": "web"}
            ]
        }
        
        result = await servant.configure_load_balancer(lb_config)
        
        assert result["success"] is True
        assert result["load_balancer_dns"] is not None
        assert len(result["target_groups"]) == 2
        assert result["health_checks_configured"] is True
    
    @pytest.mark.asyncio 
    async def test_rolling_update(self):
        """Test rolling update deployment."""
        servant = ContainerCrafter()
        
        update_config = {
            "deployment": "myapp",
            "new_image": "myapp:v2.0.0",
            "strategy": "rolling",
            "max_surge": "25%",
            "max_unavailable": "25%",
            "readiness_check": {
                "initial_delay": 30,
                "period": 10,
                "timeout": 5
            }
        }
        
        with patch.object(servant, '_execute_rolling_update', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = {
                "updated_replicas": 3,
                "ready_replicas": 3,
                "update_duration": 120,
                "rollback_available": True
            }
            
            result = await servant.perform_rolling_update(update_config)
            
            assert result["success"] is True
            assert result["updated_replicas"] == result["ready_replicas"]
            assert result["rollback_available"] is True
    
    @pytest.mark.asyncio
    async def test_blue_green_deployment(self):
        """Test blue-green deployment strategy."""
        servant = ContainerCrafter()
        
        bg_config = {
            "service": "myapp",
            "blue_version": "v1.0.0",
            "green_version": "v2.0.0",
            "traffic_shift": {
                "type": "gradual",
                "steps": [10, 25, 50, 100],
                "interval": 300  # 5 minutes between steps
            },
            "validation_checks": ["health", "metrics", "errors"]
        }
        
        result = await servant.perform_blue_green_deployment(bg_config)
        
        assert result["success"] is True
        assert result["deployment_strategy"] == "blue-green"
        assert "traffic_shifts" in result
        assert len(result["traffic_shifts"]) == 4
        assert result["rollback_plan"] is not None


class TestHealthMonitoring:
    """Test suite for container health monitoring."""
    
    @pytest.mark.asyncio
    async def test_container_health_checks(self):
        """Test container health check configuration."""
        servant = ContainerCrafter()
        
        health_config = {
            "container": "myapp",
            "checks": [
                {
                    "type": "http",
                    "path": "/health",
                    "port": 8080,
                    "interval": 30,
                    "timeout": 10
                },
                {
                    "type": "tcp",
                    "port": 8080,
                    "interval": 10
                },
                {
                    "type": "exec",
                    "command": ["./health-check.sh"],
                    "interval": 60
                }
            ]
        }
        
        result = await servant.configure_health_checks(health_config)
        
        assert result["success"] is True
        assert len(result["configured_checks"]) == 3
        assert all(check["enabled"] for check in result["configured_checks"])
    
    @pytest.mark.asyncio
    async def test_container_logs_collection(self):
        """Test container log collection and aggregation."""
        servant = ContainerCrafter()
        
        log_config = {
            "containers": ["web", "api", "worker"],
            "log_driver": "fluentd",
            "options": {
                "fluentd-address": "localhost:24224",
                "tag": "myapp.{{.Name}}",
                "labels": "environment,service"
            },
            "retention": "7d"
        }
        
        result = await servant.configure_logging(log_config)
        
        assert result["success"] is True
        assert result["log_driver"] == "fluentd"
        assert len(result["configured_containers"]) == 3
        assert result["centralized_logging"] is True
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self):
        """Test container metrics collection."""
        servant = ContainerCrafter()
        
        metrics_config = {
            "containers": ["myapp"],
            "metrics": ["cpu", "memory", "network", "disk"],
            "interval": 60,
            "aggregation": "prometheus",
            "labels": {
                "environment": "production",
                "service": "web"
            }
        }
        
        with patch.object(servant, '_collect_container_metrics', new_callable=AsyncMock) as mock_metrics:
            mock_metrics.return_value = {
                "cpu_usage_percent": 45.2,
                "memory_usage_mb": 256,
                "network_rx_bytes": 1024000,
                "network_tx_bytes": 512000,
                "disk_read_bytes": 10240000,
                "disk_write_bytes": 5120000
            }
            
            result = await servant.collect_metrics(metrics_config)
            
            assert result["success"] is True
            assert "metrics" in result
            assert result["metrics"]["cpu_usage_percent"] == 45.2
            assert result["prometheus_endpoint"] is not None


class TestResourceManagement:
    """Test suite for container resource management."""
    
    @pytest.mark.asyncio
    async def test_resource_limits(self):
        """Test container resource limits configuration."""
        servant = ContainerCrafter()
        
        resource_config = {
            "container": "myapp",
            "limits": {
                "cpu": "2",
                "memory": "2Gi",
                "ephemeral-storage": "10Gi"
            },
            "requests": {
                "cpu": "500m",
                "memory": "512Mi",
                "ephemeral-storage": "2Gi"
            },
            "gpu": {
                "nvidia.com/gpu": 1
            }
        }
        
        result = await servant.configure_resources(resource_config)
        
        assert result["success"] is True
        assert result["limits_applied"] is True
        assert result["requests_applied"] is True
        assert result["gpu_allocated"] == 1
    
    @pytest.mark.asyncio
    async def test_storage_configuration(self):
        """Test container storage configuration."""
        servant = ContainerCrafter()
        
        storage_config = {
            "container": "database",
            "volumes": [
                {
                    "name": "data",
                    "type": "persistent",
                    "size": "100Gi",
                    "storage_class": "fast-ssd",
                    "mount_path": "/var/lib/postgresql/data"
                },
                {
                    "name": "config",
                    "type": "configmap",
                    "configmap_name": "db-config",
                    "mount_path": "/etc/postgresql"
                },
                {
                    "name": "secrets",
                    "type": "secret",
                    "secret_name": "db-credentials",
                    "mount_path": "/etc/secrets"
                }
            ]
        }
        
        result = await servant.configure_storage(storage_config)
        
        assert result["success"] is True
        assert len(result["volumes_configured"]) == 3
        assert result["persistent_volume_created"] is True
    
    @pytest.mark.asyncio
    async def test_network_policies(self):
        """Test container network policies."""
        servant = ContainerCrafter()
        
        network_config = {
            "container": "api",
            "policies": [
                {
                    "name": "allow-frontend",
                    "type": "ingress",
                    "from": [{"podSelector": {"app": "frontend"}}],
                    "ports": [{"protocol": "TCP", "port": 8080}]
                },
                {
                    "name": "allow-database",
                    "type": "egress",
                    "to": [{"podSelector": {"app": "database"}}],
                    "ports": [{"protocol": "TCP", "port": 5432}]
                }
            ],
            "default_deny": True
        }
        
        result = await servant.configure_network_policies(network_config)
        
        assert result["success"] is True
        assert len(result["policies_applied"]) == 2
        assert result["default_deny_applied"] is True


class TestElderIntegration:
    """Test suite for Elder system integration."""
    
    @pytest.mark.asyncio
    async def test_four_sages_consultation(self):
        """Test consultation with 4 Sages for container best practices."""
        servant = ContainerCrafter()
        
        consultation_request = {
            "topic": "container_security",
            "context": {
                "image_size": "500MB",
                "vulnerabilities": 5,
                "base_image": "ubuntu:latest"
            }
        }
        
        with patch.object(servant, '_consult_four_sages', new_callable=AsyncMock) as mock_consult:
            mock_consult.return_value = {
                "knowledge_sage": {
                    "recommendation": "Use distroless or alpine base images",
                    "references": ["best_practices_2025.md"]
                },
                "task_sage": {
                    "priority": "high",
                    "estimated_time": "2 hours"
                },
                "incident_sage": {
                    "risk_level": "medium",
                    "mitigation": "Apply security patches immediately"
                },
                "rag_sage": {
                    "similar_cases": 3,
                    "success_rate": 0.92
                }
            }
            
            result = await servant.consult_sages(consultation_request)
            
            assert result["success"] is True
            assert "recommendations" in result
            assert result["risk_assessment"] is not None
    
    @pytest.mark.asyncio
    async def test_elder_flow_integration(self):
        """Test Elder Flow integration for automated workflows."""
        servant = ContainerCrafter()
        
        workflow_request = {
            "workflow": "container_deployment",
            "stages": [
                "build",
                "optimize",
                "scan",
                "push",
                "deploy",
                "monitor"
            ],
            "auto_rollback": True
        }
        
        with patch.object(servant, '_execute_elder_flow', new_callable=AsyncMock) as mock_flow:
            mock_flow.return_value = {
                "workflow_id": "wf-123456",
                "stages_completed": 6,
                "total_duration": 300,
                "quality_score": 0.95
            }
            
            result = await servant.execute_workflow(workflow_request)
            
            assert result["success"] is True
            assert result["workflow_id"] == "wf-123456"
            assert result["all_stages_completed"] is True
            assert result["quality_score"] >= 0.95  # Iron Will standard
    
    @pytest.mark.asyncio
    async def test_iron_will_compliance(self):
        """Test Iron Will quality standards compliance."""
        servant = ContainerCrafter()
        
        quality_check = {
            "container": "myapp",
            "checks": [
                "security_scanning",
                "size_optimization",
                "layer_efficiency",
                "health_checks",
                "resource_limits",
                "logging_configured"
            ]
        }
        
        result = await servant.validate_iron_will_compliance(quality_check)
        
        assert result["success"] is True
        assert result["compliance_score"] >= 0.95
        assert all(check["passed"] for check in result["checks"])
        assert result["iron_will_approved"] is True
    
    def test_dwarf_servant_inheritance(self):
        """Test proper DwarfServant base class inheritance."""
        servant = ContainerCrafter()
        
        # Check base class methods
        assert hasattr(servant, 'process_request')
        assert hasattr(servant, 'validate_request')
        assert hasattr(servant, 'get_capabilities')
        assert hasattr(servant, 'execute_with_quality_gate')
        
        # Check servant category
        assert servant.category == "DWARF"
        assert servant.domain == "EXECUTION"


class TestAdvancedFeatures:
    """Test suite for advanced container features."""
    
    @pytest.mark.asyncio
    async def test_container_migration(self):
        """Test container migration between platforms."""
        servant = ContainerCrafter()
        
        migration_request = {
            "source": {
                "platform": "docker_swarm",
                "services": ["web", "api", "worker"]
            },
            "target": {
                "platform": "kubernetes",
                "namespace": "production"
            },
            "strategy": "zero_downtime",
            "rollback_enabled": True
        }
        
        result = await servant.migrate_containers(migration_request)
        
        assert result["success"] is True
        assert result["services_migrated"] == 3
        assert result["downtime_seconds"] == 0
        assert result["rollback_checkpoint"] is not None
    
    @pytest.mark.asyncio
    async def test_disaster_recovery(self):
        """Test container disaster recovery capabilities."""
        servant = ContainerCrafter()
        
        dr_config = {
            "backup_strategy": "continuous",
            "recovery_targets": {
                "rpo": 300,  # 5 minutes
                "rto": 600   # 10 minutes
            },
            "backup_locations": ["s3://backups", "azure://dr-storage"],
            "test_recovery": True
        }
        
        result = await servant.configure_disaster_recovery(dr_config)
        
        assert result["success"] is True
        assert result["backup_configured"] is True
        assert result["recovery_tested"] is True
        assert result["meets_rpo"] is True
        assert result["meets_rto"] is True
    
    @pytest.mark.asyncio
    async def test_container_debugging(self):
        """Test container debugging capabilities."""
        servant = ContainerCrafter()
        
        debug_request = {
            "container": "failing-app",
            "debug_mode": "interactive",
            "tools": ["strace", "tcpdump", "gdb"],
            "capture_coredump": True,
            "profile_performance": True
        }
        
        with patch.object(servant, '_attach_debugger', new_callable=AsyncMock) as mock_debug:
            mock_debug.return_value = {
                "debug_session_id": "debug-123",
                "tools_attached": ["strace", "tcpdump", "gdb"],
                "coredump_location": "/tmp/coredump-123",
                "performance_profile": {
                    "cpu_hotspots": ["function_a", "function_b"],
                    "memory_leaks": []
                }
            }
            
            result = await servant.debug_container(debug_request)
            
            assert result["success"] is True
            assert result["debug_session_active"] is True
            assert len(result["tools_available"]) == 3
            assert result["diagnostics_collected"] is True


@pytest.fixture
def container_crafter():
    """Fixture to provide ContainerCrafter instance."""
    return ContainerCrafter()


@pytest.fixture
def mock_docker_client():
    """Fixture to provide mocked Docker client."""
    mock = MagicMock()
    mock.ping.return_value = True
    mock.version.return_value = {"Version": "20.10.0"}
    return mock


@pytest.fixture
def mock_k8s_client():
    """Fixture to provide mocked Kubernetes client."""
    mock = MagicMock()
    mock.get_api_resources.return_value = MagicMock()
    return mock


# Performance tests
class TestPerformance:
    """Test suite for performance characteristics."""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_builds(self):
        """Test concurrent container builds performance."""
        servant = ContainerCrafter()
        
        build_tasks = []
        for i in range(10):
            build_request = {
                "dockerfile_path": f"/path/to/Dockerfile{i}",
                "image_name": f"app{i}",
                "tag": "v1.0.0"
            }
            build_tasks.append(servant.build_container(build_request))
        
        with patch.object(servant, '_execute_docker_build', new_callable=AsyncMock) as mock_build:
            mock_build.return_value = {
                "image_id": "sha256:123456",
                "size": 100 * 1024 * 1024,
                "build_time": 30
            }
            
            start_time = asyncio.get_event_loop().time()
            results = await asyncio.gather(*build_tasks)
            end_time = asyncio.get_event_loop().time()
            
            assert len(results) == 10
            assert all(r["success"] for r in results)
            assert (end_time - start_time) < 5  # Should complete within 5 seconds
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_large_scale_deployment(self):
        """Test large scale deployment performance."""
        servant = ContainerCrafter()
        
        deployment_request = {
            "services": [f"service-{i}" for i in range(50)],
            "replicas_per_service": 3,
            "platform": "kubernetes",
            "parallel_deployments": 10
        }
        
        with patch.object(servant, '_deploy_services_batch', new_callable=AsyncMock) as mock_deploy:
            mock_deploy.return_value = {
                "deployed_services": 50,
                "total_replicas": 150,
                "deployment_time": 120
            }
            
            result = await servant.deploy_large_scale(deployment_request)
            
            assert result["success"] is True
            assert result["total_services"] == 50
            assert result["total_replicas"] == 150
            assert result["average_deployment_time"] < 3  # Less than 3 seconds per service