#!/usr/bin/env python3
"""
Advanced Docker Template Management System
Phase 1 Week 2: Enhanced Docker Template Environment Creation
Provides specialized Docker environments for different project types and security levels
"""

import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.env_config import get_config
from libs.shared_enums import ProjectType, RuntimeEnvironment, SecurityLevel


@dataclass
class DockerTemplate:
    """Docker template configuration"""

    name: str
    project_type: ProjectType
    runtime: RuntimeEnvironment
    security_level: SecurityLevel
    base_image: str
    packages: List[str]
    python_packages: List[str]
    node_packages: List[str]
    system_packages: List[str]
    ports: List[str]
    volumes: List[str]
    environment_vars: Dict[str, str]
    health_check: Optional[str]
    startup_command: str
    development_tools: List[str]
    security_hardening: List[str]
    resource_limits: Dict[str, Any]


class DockerTemplateManager:
    """Advanced Docker template management system"""

    def __init__(self):
        self.config = get_config()
        self.workspace_root = Path("/home/aicompany/workspace")
        self.templates_dir = self.workspace_root / "docker" / "templates"
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # Initialize template configurations
        self._initialize_template_library()
        self._initialize_security_profiles()
        self._initialize_optimization_profiles()

    def _initialize_template_library(self):
        """Initialize comprehensive template library"""
        self.template_library = {
            # Web API Templates
            ProjectType.WEB_API: {
                SecurityLevel.DEVELOPMENT: DockerTemplate(
                    name="web_api_dev",
                    project_type=ProjectType.WEB_API,
                    runtime=RuntimeEnvironment.PYTHON_FULL,
                    security_level=SecurityLevel.DEVELOPMENT,
                    base_image="python:3.11-slim",
                    packages=[
                        "fastapi",
                        "uvicorn",
                        "pydantic",
                        "sqlalchemy",
                        "alembic",
                    ],
                    python_packages=[
                        "fastapi[all]",
                        "uvicorn[standard]",
                        "python-multipart",
                        "sqlalchemy",
                        "alembic",
                        "psycopg2-binary",
                        "redis",
                    ],
                    node_packages=[],
                    system_packages=["curl", "wget", "git", "vim", "htop"],
                    ports=["8000:8000", "5432:5432", "6379:6379"],
                    volumes=["./:/app", "./data:/app/data"],
                    environment_vars={
                        "PYTHONPATH": "/app",
                        "FASTAPI_ENV": "development",
                        "LOG_LEVEL": "debug",
                    },
                    health_check="curl -f http://localhost:8000/health || exit 1",
                    startup_command="uvicorn main:app --host 0.0.0.0 --port 8000 --reload",
                    development_tools=[
                        "pytest",
                        "black",
                        "flake8",
                        "mypy",
                        "pre-commit",
                    ],
                    security_hardening=["--cap-drop=ALL", "--cap-add=NET_BIND_SERVICE"],
                    resource_limits={"memory": "1g", "cpus": "1.0"},
                ),
                SecurityLevel.SANDBOX: DockerTemplate(
                    name="web_api_sandbox",
                    project_type=ProjectType.WEB_API,
                    runtime=RuntimeEnvironment.PYTHON_SLIM,
                    security_level=SecurityLevel.SANDBOX,
                    base_image="python:3.11-slim",
                    packages=["fastapi", "uvicorn"],
                    python_packages=["fastapi", "uvicorn"],
                    node_packages=[],
                    system_packages=[],  # Minimal system packages for security
                    ports=["8000:8000"],
                    volumes=["./src:/app/src:ro"],  # Read-only source
                    environment_vars={
                        "PYTHONPATH": "/app",
                        "FASTAPI_ENV": "production",
                        "LOG_LEVEL": "warning",
                    },
                    health_check="python -c 'import requests; requests.get(\"http://localhost:8000/health\")'",
                    startup_command="uvicorn src.main:app --host 0.0.0.0 --port 8000",
                    development_tools=[],
                    security_hardening=[
                        "--read-only",
                        "--tmpfs=/tmp",
                        "--network=none",
                        "--cap-drop=ALL",
                        "--security-opt=no-new-privileges",
                        "--user=nobody",
                    ],
                    resource_limits={"memory": "512m", "cpus": "0.5"},
                ),
            },
            # Machine Learning Templates
            ProjectType.ML_RESEARCH: {
                SecurityLevel.DEVELOPMENT: DockerTemplate(
                    name="ml_research_dev",
                    project_type=ProjectType.ML_RESEARCH,
                    runtime=RuntimeEnvironment.PYTHON_FULL,
                    security_level=SecurityLevel.DEVELOPMENT,
                    base_image="tensorflow/tensorflow:latest-gpu-jupyter",
                    packages=[
                        "tensorflow",
                        "pytorch",
                        "scikit-learn",
                        "pandas",
                        "numpy",
                    ],
                    python_packages=[
                        "tensorflow",
                        "torch",
                        "torchvision",
                        "scikit-learn",
                        "pandas",
                        "numpy",
                        "matplotlib",
                        "seaborn",
                        "plotly",
                        "jupyter",
                        "jupyterlab",
                        "notebook",
                        "ipywidgets",
                        "wandb",
                        "tensorboard",
                        "mlflow",
                    ],
                    node_packages=[],
                    system_packages=["git", "curl", "wget", "unzip", "graphviz"],
                    ports=[
                        "8888:8888",
                        "6006:6006",
                        "5000:5000",
                    ],  # Jupyter, TensorBoard, MLflow
                    volumes=[
                        "./:/workspace",
                        "./data:/workspace/data",
                        "./models:/workspace/models",
                    ],
                    environment_vars={
                        "JUPYTER_ENABLE_LAB": "yes",
                        "GRANT_SUDO": "yes",
                        "CHOWN_HOME": "yes",
                    },
                    health_check="curl -f http://localhost:8888/api || exit 1",
                    startup_command="jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root" \
                        "jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root",
                    development_tools=["pytest", "black", "isort", "nbstripout"],
                    security_hardening=["--cap-drop=ALL"],
                    resource_limits={"memory": "8g", "cpus": "4.0", "gpus": "all"},
                )
            },
            # Full Stack Web Templates
            ProjectType.FULL_STACK_WEB: {
                SecurityLevel.DEVELOPMENT: DockerTemplate(
                    name="fullstack_dev",
                    project_type=ProjectType.FULL_STACK_WEB,
                    runtime=RuntimeEnvironment.NODE_LTS,
                    security_level=SecurityLevel.DEVELOPMENT,
                    base_image="node:18-slim",
                    packages=["react", "express", "postgresql"],
                    python_packages=[],
                    node_packages=[
                        "react",
                        "next",
                        "@types/react",
                        "@types/node",
                        "express",
                        "cors",
                        "helmet",
                        "morgan",
                        "prisma",
                        "@prisma/client",
                        "pg",
                        "@types/pg",
                        "jest",
                        "@testing-library/react",
                        "eslint",
                        "prettier",
                    ],
                    system_packages=["python3", "pip", "curl", "git"],
                    ports=["3000:3000", "3001:3001", "5432:5432"],
                    volumes=["./:/app", "./node_modules:/app/node_modules"],
                    environment_vars={
                        "NODE_ENV": "development",
                        "CHOKIDAR_USEPOLLING": "true",
                    },
                    health_check="curl -f http://localhost:3000 || exit 1",
                    startup_command="npm run dev",
                    development_tools=["eslint", "prettier", "jest", "cypress"],
                    security_hardening=["--cap-drop=ALL"],
                    resource_limits={"memory": "2g", "cpus": "2.0"},
                )
            },
            # CLI Tools Templates
            ProjectType.CLI_TOOLS: {
                SecurityLevel.RESTRICTED: DockerTemplate(
                    name="cli_tools_restricted",
                    project_type=ProjectType.CLI_TOOLS,
                    runtime=RuntimeEnvironment.PYTHON_SLIM,
                    security_level=SecurityLevel.RESTRICTED,
                    base_image="python:3.11-alpine",
                    packages=["click", "typer"],
                    python_packages=["click", "typer", "rich", "pydantic"],
                    node_packages=[],
                    system_packages=["git", "curl"],
                    ports=[],
                    volumes=["./:/app:ro", "./output:/app/output"],
                    environment_vars={"PYTHONPATH": "/app", "CLI_ENV": "restricted"},
                    health_check="python -c 'import click; print(\"OK\")'",
                    startup_command="python -m src.cli",
                    development_tools=["pytest", "black"],
                    security_hardening=[
                        "--read-only",
                        "--tmpfs=/tmp",
                        "--cap-drop=ALL",
                        "--security-opt=no-new-privileges",
                        "--network=restricted",
                    ],
                    resource_limits={"memory": "256m", "cpus": "0.5"},
                )
            },
            # Microservices Templates
            ProjectType.MICROSERVICES: {
                SecurityLevel.RESTRICTED: DockerTemplate(
                    name="microservices_restricted",
                    project_type=ProjectType.MICROSERVICES,
                    runtime=RuntimeEnvironment.PYTHON_SLIM,
                    security_level=SecurityLevel.RESTRICTED,
                    base_image="python:3.11-slim",
                    packages=["fastapi", "uvicorn", "redis", "celery"],
                    python_packages=[
                        "fastapi",
                        "uvicorn",
                        "pydantic",
                        "redis",
                        "celery",
                        "aioredis",
                        "httpx",
                        "python-consul",
                        "prometheus-client",
                    ],
                    node_packages=[],
                    system_packages=["curl"],
                    ports=["8000:8000"],
                    volumes=["./:/app:ro"],
                    environment_vars={
                        "SERVICE_NAME": "microservice",
                        "SERVICE_VERSION": "1.0.0",
                        "CONSUL_HOST": "consul",
                        "REDIS_URL": "redis://redis:6379",
                    },
                    health_check="curl -f http://localhost:8000/health || exit 1",
                    startup_command="uvicorn src.main:app --host 0.0.0.0 --port 8000",
                    development_tools=["pytest", "pytest-asyncio"],
                    security_hardening=[
                        "--read-only",
                        "--tmpfs=/tmp",
                        "--cap-drop=ALL",
                        "--security-opt=no-new-privileges",
                    ],
                    resource_limits={"memory": "512m", "cpus": "1.0"},
                )
            },
        }

    def _initialize_security_profiles(self):
        """Initialize security hardening profiles"""
        self.security_profiles = {
            SecurityLevel.SANDBOX: {
                "network_mode": "none",
                "read_only": True,
                "tmpfs": {"/tmp": "noexec,nosuid,size=100m"},
                "cap_drop": ["ALL"],
                "security_opt": ["no-new-privileges"],
                "user": "nobody",
                "memory_limit": "512m",
                "cpu_limit": "0.5",
                "pids_limit": 100,
            },
            SecurityLevel.RESTRICTED: {
                "network_mode": "restricted",
                "read_only": True,
                "tmpfs": {"/tmp": "size=200m"},
                "cap_drop": ["ALL"],
                "cap_add": ["NET_BIND_SERVICE"],
                "security_opt": ["no-new-privileges"],
                "memory_limit": "1g",
                "cpu_limit": "1.0",
                "pids_limit": 200,
            },
            SecurityLevel.DEVELOPMENT: {
                "network_mode": "bridge",
                "read_only": False,
                "cap_drop": ["ALL"],
                "cap_add": ["NET_BIND_SERVICE", "SYS_PTRACE"],
                "memory_limit": "2g",
                "cpu_limit": "2.0",
                "pids_limit": 500,
            },
            SecurityLevel.TRUSTED: {
                "network_mode": "host",
                "privileged": True,
                "memory_limit": "4g",
                "cpu_limit": "4.0",
                "pids_limit": 1000,
            },
        }

    def _initialize_optimization_profiles(self):
        """Initialize performance optimization profiles"""
        self.optimization_profiles = {
            "minimal": {
                "multi_stage_build": True,
                "layer_caching": True,
                "package_cleanup": True,
                "compress_layers": True,
            },
            "development": {
                "multi_stage_build": False,
                "layer_caching": True,
                "package_cleanup": False,
                "development_tools": True,
                "hot_reload": True,
            },
            "production": {
                "multi_stage_build": True,
                "layer_caching": True,
                "package_cleanup": True,
                "compress_layers": True,
                "health_checks": True,
                "logging_optimization": True,
            },
        }

    def generate_dockerfile(
        self, template: DockerTemplate, optimization_profile: str = "development"
    ) -> str:
        """Generate optimized Dockerfile from template"""

        optimization = self.optimization_profiles.get(
            optimization_profile, self.optimization_profiles["development"]
        )

        dockerfile_content = []

        # Multi-stage build setup
        if optimization.get("multi_stage_build", False):
            dockerfile_content.extend(
                [
                    f"# Build stage",
                    f"FROM {template.base_image} as builder",
                    "",
                    "# Install build dependencies",
                    "RUN apt-get update && apt-get install -y --no-install-recommends \\",
                    "    build-essential \\",
                    "    && rm -rf /var/lib/apt/lists/*",
                    "",
                    "# Copy and install Python packages",
                    "COPY requirements.txt .",
                    "RUN pip install --no-cache-dir --user -r requirements.txt",
                    "",
                    "# Production stage",
                    f"FROM {template.base_image} as production",
                    "",
                    "# Copy installed packages from builder",
                    "COPY --from=builder /root/.local /root/.local",
                    "",
                ]
            )
        else:
            dockerfile_content.extend([f"FROM {template.base_image}", ""])

        # Security hardening
        if template.security_level in [SecurityLevel.SANDBOX, SecurityLevel.RESTRICTED]:
            dockerfile_content.extend(
                [
                    "# Security: Create non-root user",
                    "RUN groupadd -r appuser && useradd -r -g appuser appuser",
                    "",
                ]
            )

        # System packages installation
        if template.system_packages:
            dockerfile_content.extend(
                [
                    "# Install system packages",
                    "RUN apt-get update && apt-get install -y --no-install-recommends \\",
                ]
            )
            for pkg in template.system_packages:
                dockerfile_content.append(f"    {pkg} \\")

            if optimization.get("package_cleanup", False):
                dockerfile_content.extend(
                    [
                        "    && apt-get clean \\",
                        "    && rm -rf /var/lib/apt/lists/* \\",
                        "    && rm -rf /var/cache/apt/archives/*",
                        "",
                    ]
                )
            else:
                dockerfile_content.extend(["", ""])

        # Python packages installation
        if template.python_packages:
            dockerfile_content.extend(
                [
                    "# Install Python packages",
                    "COPY requirements.txt .",
                ]
            )

            if optimization.get("layer_caching", True):
                dockerfile_content.append(
                    "RUN pip install --no-cache-dir -r requirements.txt"
                )
            else:
                dockerfile_content.extend(
                    [
                        "RUN pip install --upgrade pip \\",
                        f"    && pip install --no-cache-dir {' '.join(template.python_packages)}",
                    ]
                )
            dockerfile_content.append("")

        # Node packages installation (if applicable)
        if template.node_packages:
            dockerfile_content.extend(
                [
                    "# Install Node packages",
                    "COPY package.json package-lock.json ./",
                    "RUN npm ci --only=production \\",
                    "    && npm cache clean --force",
                    "",
                ]
            )

        # Working directory setup
        dockerfile_content.extend(["# Set working directory", "WORKDIR /app", ""])

        # Copy application code
        if template.security_level in [SecurityLevel.SANDBOX, SecurityLevel.RESTRICTED]:
            dockerfile_content.extend(
                [
                    "# Copy application code (security: specific files only)",
                    "COPY src/ ./src/",
                    "COPY config/ ./config/",
                    "",
                ]
            )
        else:
            dockerfile_content.extend(["# Copy application code", "COPY . .", ""])

        # Environment variables
        if template.environment_vars:
            dockerfile_content.append("# Environment variables")
            for key, value in template.environment_vars.items():
                dockerfile_content.append(f"ENV {key}={value}")
            dockerfile_content.append("")

        # Development tools (only for development environments)
        if optimization.get("development_tools", False) and template.development_tools:
            dockerfile_content.extend(
                [
                    "# Development tools",
                    f"RUN pip install --no-cache-dir {' '.join(template.development_tools)}",
                    "",
                ]
            )

        # Expose ports
        if template.ports:
            dockerfile_content.append("# Expose ports")
            for port in template.ports:
                if ":" in port:
                    internal_port = port.split(":")[1]
                    dockerfile_content.append(f"EXPOSE {internal_port}")
                else:
                    dockerfile_content.append(f"EXPOSE {port}")
            dockerfile_content.append("")

        # Health check
        if template.health_check and optimization.get("health_checks", True):
            dockerfile_content.extend(
                [
                    "# Health check",
                    f"HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\",
                    f"    CMD {template.health_check}",
                    "",
                ]
            )

        # Security: Switch to non-root user
        if template.security_level in [SecurityLevel.SANDBOX, SecurityLevel.RESTRICTED]:
            dockerfile_content.extend(
                [
                    "# Security: Switch to non-root user",
                    "RUN chown -R appuser:appuser /app",
                    "USER appuser",
                    "",
                ]
            )

        # Startup command
        dockerfile_content.extend(
            [
                "# Startup command",
                f"CMD {template.startup_command}",
            ]
        )

        return "\n".join(dockerfile_content)

    def generate_docker_compose(
        self, template: DockerTemplate, project_name: str
    ) -> str:
        """Generate Docker Compose configuration"""

        security_profile = self.security_profiles[template.security_level]

        compose_config = {
            "version": "3.8",
            "services": {
                "app": {
                    "build": {"context": ".", "dockerfile": "Dockerfile"},
                    "container_name": f"{project_name}_{template.security_level.value}",
                    "restart": "unless-stopped",
                    "environment": template.environment_vars,
                    **self._apply_security_config(security_profile),
                }
            },
        }

        # Add ports
        if template.ports:
            compose_config["services"]["app"]["ports"] = template.ports

        # Add volumes
        if template.volumes:
            compose_config["services"]["app"]["volumes"] = template.volumes

        # Add dependent services based on project type
        if template.project_type in [ProjectType.WEB_API, ProjectType.FULL_STACK_WEB]:
            # Add PostgreSQL service
            compose_config["services"]["postgres"] = {
                "image": "postgres:15-alpine",
                "environment": {
                    "POSTGRES_DB": "appdb",
                    "POSTGRES_USER": "appuser",
                    "POSTGRES_PASSWORD": "apppass",
                },
                "volumes": ["postgres_data:/var/lib/postgresql/data"],
                "ports": ["5432:5432"],
            }

            # Add Redis service
            compose_config["services"]["redis"] = {
                "image": "redis:7-alpine",
                "ports": ["6379:6379"],
                "volumes": ["redis_data:/data"],
            }

            # Add volumes section
            compose_config["volumes"] = {"postgres_data": {}, "redis_data": {}}

        # Add monitoring for production environments
        if template.security_level == SecurityLevel.TRUSTED:
            compose_config["services"]["prometheus"] = {
                "image": "prom/prometheus:latest",
                "ports": ["9090:9090"],
                "volumes": [
                    "./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml"
                ],
            }

        return yaml.dump(compose_config, default_flow_style=False, indent=2)

    def _apply_security_config(self, security_profile: Dict) -> Dict:
        """Apply security configuration to Docker Compose service"""
        config = {}

        if "network_mode" in security_profile:
            config["network_mode"] = security_profile["network_mode"]

        if "read_only" in security_profile:
            config["read_only"] = security_profile["read_only"]

        if "tmpfs" in security_profile:
            config["tmpfs"] = list(security_profile["tmpfs"].keys())

        if "cap_drop" in security_profile or "cap_add" in security_profile:
            config["cap_drop"] = security_profile.get("cap_drop", [])
            config["cap_add"] = security_profile.get("cap_add", [])

        if "security_opt" in security_profile:
            config["security_opt"] = security_profile["security_opt"]

        if "user" in security_profile:
            config["user"] = security_profile["user"]

        if "memory_limit" in security_profile:
            config["mem_limit"] = security_profile["memory_limit"]

        if "cpu_limit" in security_profile:
            config["cpus"] = security_profile["cpu_limit"]

        if "pids_limit" in security_profile:
            config["pids_limit"] = security_profile["pids_limit"]

        if "privileged" in security_profile:
            config["privileged"] = security_profile["privileged"]

        return config

    def generate_requirements_file(self, template: DockerTemplate) -> str:
        """Generate requirements.txt file"""

        requirements = []

        # Add Python packages with versions
        package_versions = {
            "fastapi": ">=0.100.0",
            "uvicorn": ">=0.23.0",
            "pydantic": ">=2.0.0",
            "sqlalchemy": ">=2.0.0",
            "alembic": ">=1.11.0",
            "psycopg2-binary": ">=2.9.0",
            "redis": ">=4.6.0",
            "tensorflow": ">=2.13.0",
            "torch": ">=2.0.0",
            "scikit-learn": ">=1.3.0",
            "pandas": ">=2.0.0",
            "numpy": ">=1.24.0",
            "click": ">=8.1.0",
            "typer": ">=0.9.0",
            "rich": ">=13.0.0",
            "pytest": ">=7.4.0",
            "black": ">=23.0.0",
            "flake8": ">=6.0.0",
            "mypy": ">=1.5.0",
        }

        for package in template.python_packages:
            if package in package_versions:
                requirements.append(f"{package}{package_versions[package]}")
            else:
                requirements.append(package)

        # Add development tools for development environments
        if template.security_level == SecurityLevel.DEVELOPMENT:
            requirements.extend(template.development_tools)

        return "\n".join(sorted(requirements)) + "\n"

    def create_template_environment(
        self, project_path: Path, template: DockerTemplate, project_name: str
    ) -> Dict[str, str]:
        """Create complete Docker template environment"""

        docker_dir = project_path / ".docker"
        docker_dir.mkdir(exist_ok=True)

        created_files = {}

        # Generate Dockerfile
        dockerfile_content = self.generate_dockerfile(template, "development")
        dockerfile_path = docker_dir / "Dockerfile"
        dockerfile_path.write_text(dockerfile_content)
        created_files["dockerfile"] = str(dockerfile_path)

        # Generate Docker Compose
        compose_content = self.generate_docker_compose(template, project_name)
        compose_path = docker_dir / "docker-compose.yml"
        compose_path.write_text(compose_content)
        created_files["compose"] = str(compose_path)

        # Generate requirements.txt
        requirements_content = self.generate_requirements_file(template)
        requirements_path = project_path / "requirements.txt"
        requirements_path.write_text(requirements_content)
        created_files["requirements"] = str(requirements_path)

        # Generate package.json for Node projects
        if template.node_packages:
            package_json = {
                "name": project_name,
                "version": "1.0.0",
                "description": f"{template.project_type.value} project",
                "main": "index.js",
                "scripts": {
                    "dev": "nodemon src/index.js",
                    "start": "node src/index.js",
                    "test": "jest",
                    "lint": "eslint src/",
                    "format": "prettier --write src/",
                },
                "dependencies": {pkg: "latest" for pkg in template.node_packages},
                "devDependencies": {
                    "nodemon": "latest",
                    "jest": "latest",
                    "eslint": "latest",
                    "prettier": "latest",
                },
            }
            package_path = project_path / "package.json"
            package_path.write_text(json.dumps(package_json, indent=2))
            created_files["package_json"] = str(package_path)

        # Generate management scripts
        self._create_management_scripts(docker_dir, template, project_name)
        created_files["scripts"] = str(docker_dir / "scripts")

        # Generate monitoring configuration for production
        if template.security_level == SecurityLevel.TRUSTED:
            self._create_monitoring_config(docker_dir)
            created_files["monitoring"] = str(docker_dir / "monitoring")

        return created_files

    def _create_management_scripts(
        self, docker_dir: Path, template: DockerTemplate, project_name: str
    ):
        """Create Docker management scripts"""

        scripts_dir = docker_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)

        # Build script
        build_script = scripts_dir / "build.sh"
        build_script.write_text(
            f"""#!/bin/bash
# Build {project_name} Docker image
set -e

echo "🔨 Building {project_name} image..."

docker-compose -f ../docker-compose.yml build

echo "✅ Build completed successfully"
"""
        )
        build_script.chmod(0o755)

        # Start script
        start_script = scripts_dir / "start.sh"
        start_script.write_text(
            f"""#!/bin/bash
# Start {project_name} services
set -e

echo "🚀 Starting {project_name} services..."

# Build if needed
if [[ "$1" == "--build" ]]; then
    docker-compose -f ../docker-compose.yml up --build -d
else
    docker-compose -f ../docker-compose.yml up -d
fi

echo "✅ Services started successfully"
echo "📊 Status:"
docker-compose -f ../docker-compose.yml ps

echo ""
echo "📁 Access application:"
echo "  - Container: docker exec -it {project_name}_{template.security_level.value} bash"
if "8000:8000" in template.ports:
    echo "  - Web: http://localhost:8000"
if "8888:8888" in template.ports:
    echo "  - Jupyter: http://localhost:8888"
"""
        )
        start_script.chmod(0o755)

        # Stop script
        stop_script = scripts_dir / "stop.sh"
        stop_script.write_text(
            f"""#!/bin/bash
# Stop {project_name} services
set -e

echo "🛑 Stopping {project_name} services..."

docker-compose -f ../docker-compose.yml down

if [[ "$1" == "--clean" ]]; then
    echo "🧹 Cleaning up volumes and images..."
    docker-compose -f ../docker-compose.yml down -v --rmi all
fi

echo "✅ Services stopped successfully"
"""
        )
        stop_script.chmod(0o755)

        # Logs script
        logs_script = scripts_dir / "logs.sh"
        logs_script.write_text(
            f"""#!/bin/bash
# View {project_name} logs
set -e

SERVICE="${{1:-app}}"

echo "📋 Showing logs for service: $SERVICE"

docker-compose -f ../docker-compose.yml logs -f "$SERVICE"
"""
        )
        logs_script.chmod(0o755)

        # Health check script
        health_script = scripts_dir / "health.sh"
        health_script.write_text(
            f"""#!/bin/bash
# Health check for {project_name}
set -e

echo "🏥 Health check for {project_name}"

docker-compose -f ../docker-compose.yml ps

echo ""
echo "📊 Container stats:"
docker stats --no-stream $(docker-compose -f ../docker-compose.yml ps -q)

echo ""
echo "🔍 Service health:"
if docker-compose -f ../docker-compose.yml exec app {template.health_check}; then
    echo "✅ Application is healthy"
else
    echo "❌ Application health check failed"
    exit 1
fi
"""
        )
        health_script.chmod(0o755)

    def _create_monitoring_config(self, docker_dir: Path):
        """Create monitoring configuration for production environments"""

        monitoring_dir = docker_dir / "monitoring"
        monitoring_dir.mkdir(exist_ok=True)

        # Prometheus configuration
        prometheus_config = {
            "global": {"scrape_interval": "15s", "evaluation_interval": "15s"},
            "scrape_configs": [
                {
                    "job_name": "app",
                    "static_configs": [{"targets": ["app:8000"]}],
                    "metrics_path": "/metrics",
                    "scrape_interval": "5s",
                }
            ],
        }

        prometheus_file = monitoring_dir / "prometheus.yml"
        prometheus_file.write_text(yaml.dump(prometheus_config, indent=2))

    def get_template_for_project(
        self, project_type: str, security_level: SecurityLevel
    ) -> Optional[DockerTemplate]:
        """Get appropriate template for project type and security level"""

        try:
            project_enum = ProjectType(project_type)
        except ValueError:
            return None

        project_templates = self.template_library.get(project_enum, {})

        # Try exact match first
        if security_level in project_templates:
            return project_templates[security_level]

        # Fall back to closest security level
        fallback_order = {
            SecurityLevel.SANDBOX: [
                SecurityLevel.RESTRICTED,
                SecurityLevel.DEVELOPMENT,
            ],
            SecurityLevel.RESTRICTED: [
                SecurityLevel.DEVELOPMENT,
                SecurityLevel.SANDBOX,
            ],
            SecurityLevel.DEVELOPMENT: [
                SecurityLevel.RESTRICTED,
                SecurityLevel.SANDBOX,
            ],
            SecurityLevel.TRUSTED: [
                SecurityLevel.DEVELOPMENT,
                SecurityLevel.RESTRICTED,
            ],
        }

        for fallback_level in fallback_order.get(security_level, []):
            if fallback_level in project_templates:
                return project_templates[fallback_level]

        return None

    def list_available_templates(self) -> Dict[str, List[str]]:
        """List all available templates organized by project type"""

        templates = {}
        for project_type, type_templates in self.template_library.items():
            templates[project_type.value] = [
                f"{level.value}_{template.name}"
                for level, template in type_templates.items()
            ]

        return templates


if __name__ == "__main__":
    # Test the Docker template manager
    manager = DockerTemplateManager()

    print("=== Docker Template Manager Test ===")

    # List available templates
    templates = manager.list_available_templates()
    print(f"Available templates: {len(templates)} project types")
    for project_type, template_list in templates.items():
        print(f"  {project_type}: {len(template_list)} templates")

    # Test template generation
    web_api_template = manager.get_template_for_project(
        "web_api", SecurityLevel.DEVELOPMENT
    )
    if web_api_template:
        print(f"\n=== Web API Development Template ===")
        print(f"Name: {web_api_template.name}")
        print(f"Runtime: {web_api_template.runtime.value}")
        print(f"Packages: {len(web_api_template.python_packages)}")
        print(f"Ports: {web_api_template.ports}")

        # Generate Dockerfile
        dockerfile = manager.generate_dockerfile(web_api_template)
        print(f"\nDockerfile length: {len(dockerfile)} characters")

        # Generate Docker Compose
        compose = manager.generate_docker_compose(web_api_template, "test_project")
        print(f"Docker Compose length: {len(compose)} characters")

    print("\n✅ Docker Template Manager test completed")
