#!/usr/bin/env python3
"""
Elders Guild Automated Project Manager with Docker Isolation and GitHub Integration
Implements Phase 1: Foundation System for secure project development
"""

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.env_config import get_config
from libs.project_risk_analyzer import ProjectRiskAnalyzer
from libs.project_risk_analyzer import RiskLevel as AnalyzerRiskLevel
from libs.shared_enums import ProjectType, SecurityLevel


@dataclass
class ProjectRisk:
    """Project risk assessment result"""

    level: str  # low, medium, high, critical
    factors: List[str]
    recommended_security: SecurityLevel
    isolation_required: bool
    manual_approval: bool


class AutoProjectManager:
    """Automated project placement and management with security isolation"""

    def __init__(self):
        """初期化メソッド"""
        self.config = get_config()
        self.ai_company_root = Path("/home/aicompany/ai_co")
        self.workspace_root = Path("/home/aicompany/workspace")
        self.projects_root = Path("/home/aicompany/projects")

        # Initialize advanced risk analyzer
        self.risk_analyzer = ProjectRiskAnalyzer()

        # Docker template manager will be initialized lazily
        self._docker_manager = None

        # Initialize workspace structure
        self._initialize_workspace()

    @property
    def docker_manager(self):
        """Lazy initialization of Docker template manager"""
        if self._docker_manager is None:
            from libs.docker_template_manager import DockerTemplateManager

            self._docker_manager = DockerTemplateManager()
        return self._docker_manager

    def _initialize_workspace(self):
        """Initialize secure workspace directory structure"""
        workspace_dirs = [
            self.workspace_root / "sandbox",  # Sandboxed projects
            self.workspace_root / "restricted",  # Restricted projects
            self.workspace_root / "development",  # Development projects
            self.workspace_root / "trusted",  # Trusted projects
            self.workspace_root / "templates",  # Project templates
            self.workspace_root / "docker",  # Docker configurations
            self.workspace_root / "logs",  # Security and audit logs
            self.workspace_root / ".elders_guild",  # Management metadata
        ]

        for directory in workspace_dirs:
            directory.mkdir(parents=True, exist_ok=True)

        # Create security configuration
        self._create_security_config()

        # Initialize Docker templates
        self._initialize_docker_templates()

    def _create_security_config(self):
        """Create security configuration file"""
        security_config = {
            "version": "1.0.0",
            "created": datetime.now().isoformat(),
            "security_levels": {
                "sandbox": {
                    "description": "完全に隔離された環境",
                    "network_access": False,
                    "filesystem_access": "limited",
                    "docker_params": [
                        "--network=none",
                        "--read-only",
                        "--tmpfs=/tmp",
                        "--security-opt=no-new-privileges",
                    ],
                },
                "restricted": {
                    "description": "制限付きネットワークアクセス",
                    "network_access": "limited",
                    "filesystem_access": "project_only",
                    "docker_params": [
                        "--network=restricted",
                        "--cap-drop=ALL",
                        "--security-opt=no-new-privileges",
                    ],
                },
                "development": {
                    "description": "標準開発環境",
                    "network_access": True,
                    "filesystem_access": "workspace",
                    "docker_params": [
                        "--network=bridge",
                        "--cap-drop=ALL",
                        "--cap-add=NET_BIND_SERVICE",
                    ],
                },
                "trusted": {
                    "description": "信頼済みプロジェクト（手動承認必要）",
                    "network_access": True,
                    "filesystem_access": "full",
                    "docker_params": ["--privileged"],
                    "manual_approval": True,
                },
            },
            "risk_thresholds": {
                "low": 0.3,
                "medium": 0.6,
                "high": 0.8,
                "critical": 1.0,
            },
        }

        config_file = self.workspace_root / ".elders_guild" / "security_config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(security_config, f, indent=2, ensure_ascii=False)

    def _initialize_docker_templates(self):
        """Initialize Docker configuration templates"""
        docker_dir = self.workspace_root / "docker"

        # Sandbox Dockerfile
        sandbox_dockerfile = docker_dir / "Dockerfile.sandbox"
        sandbox_dockerfile.write_text(
            """
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 aidev

# Install minimal dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Switch to non-root user
USER aidev

# Set safe defaults
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

CMD ["python", "-c", "print('Sandbox environment ready')"]
"""
        )

        # Restricted Dockerfile
        restricted_dockerfile = docker_dir / "Dockerfile.restricted"
        restricted_dockerfile.write_text(
            """
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 aidev

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    git \\
    curl \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Switch to non-root user
USER aidev

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

CMD ["python", "-c", "print('Restricted environment ready')"]
"""
        )

        # Development Dockerfile
        development_dockerfile = docker_dir / "Dockerfile.development"
        development_dockerfile.write_text(
            """
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 aidev

# Install full development stack
RUN apt-get update && apt-get install -y --no-install-recommends \\
    git \\
    curl \\
    wget \\
    build-essential \\
    nodejs \\
    npm \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Switch to non-root user
USER aidev

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

CMD ["bash"]
"""
        )

        # Docker Compose template
        compose_template = docker_dir / "docker-compose.template.yml"
        compose_template.write_text(
            """
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.{security_level}
    container_name: "{project_name}_{security_level}"
    volumes:
      - "./:/workspace"
    environment:
      - PROJECT_NAME={project_name}
      - SECURITY_LEVEL={security_level}
    {additional_config}
"""
        )

    def analyze_project_risk(
        self, project_content: str, requirements: Dict
    ) -> ProjectRisk:
        """Analyze project requirements using advanced risk analyzer"""

        # Use advanced risk analyzer
        analysis = self.risk_analyzer.analyze_project(project_content, requirements)

        # Convert analyzer result to legacy ProjectRisk format for compatibility
        risk_factors = [
            f"{factor.description} (severity: {factor.severity:0.1f})"
            for factor in analysis.factors
        ]

        # Map analyzer risk level to security level
        security_level_mapping = {
            AnalyzerRiskLevel.MINIMAL: SecurityLevel.DEVELOPMENT,
            AnalyzerRiskLevel.LOW: SecurityLevel.DEVELOPMENT,
            AnalyzerRiskLevel.MEDIUM: SecurityLevel.RESTRICTED,
            AnalyzerRiskLevel.HIGH: SecurityLevel.SANDBOX,
            AnalyzerRiskLevel.CRITICAL: SecurityLevel.SANDBOX,
        }

        recommended_security = security_level_mapping.get(
            analysis.risk_level, SecurityLevel.SANDBOX
        )

        return ProjectRisk(
            level=analysis.risk_level.value,
            factors=risk_factors,
            recommended_security=recommended_security,
            isolation_required=analysis.overall_score > 0.3,
            manual_approval=analysis.manual_review_required,
        )

    def create_project(
        self,
        project_name: str,
        requirements: Dict,
        security_override: Optional[SecurityLevel] = None,
    ) -> Tuple[Path, ProjectRisk]:
        """Create a new project with appropriate security isolation"""

        # Analyze risk
        project_content = json.dumps(requirements, default=str)
        risk_assessment = self.analyze_project_risk(project_content, requirements)

        # Apply security override if provided
        security_level = security_override or risk_assessment.recommended_security

        # Manual approval check
        if risk_assessment.manual_approval and not security_override:
            raise PermissionError(
                f"Project '{project_name}' requires manual approval due to high risk factors: "
                f"{', '.join(risk_assessment.factors)}"
            )

        # Sanitize project name
        safe_name = self._sanitize_name(project_name)

        # Determine project location based on security level
        security_dir = self.workspace_root / security_level.value
        project_path = security_dir / safe_name

        # Handle name conflicts
        if project_path.exists():
            counter = 1
            while (security_dir / f"{safe_name}_{counter}").exists():
                counter += 1
            project_path = security_dir / f"{safe_name}_{counter}"

        # Create project structure
        self._create_project_structure(project_path, requirements, security_level)

        # Create Docker environment
        self._create_docker_environment(
            project_path, safe_name, security_level, requirements
        )

        # Log project creation
        self._log_project_creation(project_path, risk_assessment, security_level)

        return project_path, risk_assessment

    def _sanitize_name(self, name: str) -> str:
        """Sanitize project name for filesystem safety"""
        import re

        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", name.lower())
        safe_name = re.sub(r"_+", "_", safe_name)
        return safe_name.strip("_") or "unnamed_project"

    def _create_project_structure(
        self, project_path: Path, requirements: Dict, security_level: SecurityLevel
    ):
        """Create standardized project directory structure"""

        # Create base directories
        directories = [
            "src",
            "tests",
            "docs",
            "config",
            "scripts",
            "data",
            "logs",
            ".elders_guild",
            ".docker",
        ]

        for directory in directories:
            (project_path / directory).mkdir(parents=True, exist_ok=True)

        # Create project metadata
        metadata = {
            "name": project_path.name,
            "created": datetime.now().isoformat(),
            "security_level": security_level.value,
            "requirements": requirements,
            "ai_company_version": "1.0.0",
            "docker_enabled": True,
            "github_integration": False,
        }

        metadata_file = project_path / ".elders_guild" / "project.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # Create README
        self._create_readme(project_path, requirements, security_level)

        # Create requirements.txt
        self._create_requirements_file(project_path, requirements)

        # Create .gitignore
        self._create_gitignore(project_path)

    def _detect_project_type(self, requirements: Dict) -> str:
        """Detect project type from requirements"""

        features = requirements.get("features", [])
        dependencies = requirements.get("dependencies", [])
        description = requirements.get("description", "").lower()

        # Convert to lowercase strings for matching
        features_str = " ".join(str(f).lower() for f in features)
        deps_str = " ".join(str(d).lower() for d in dependencies)
        content = f"{features_str} {deps_str} {description}"

        # Project type detection rules
        if any(
            term in content
            for term in ["ml", "machine learning", "tensorflow", "pytorch", "jupyter"]
        ):
            if any(term in content for term in ["research", "experiment", "notebook"]):
                return "ml_research"
            else:
                return "ml_production"

        elif any(
            term in content for term in ["web", "api", "fastapi", "flask", "django"]
        ):
            if any(
                term in content for term in ["frontend", "react", "vue", "fullstack"]
            ):
                return "fullstack"
            else:
                return "web_api"

        elif any(term in content for term in ["cli", "command", "tool", "script"]):
            return "cli_tools"

        elif any(
            term in content for term in ["microservice", "service", "distributed"]
        ):
            return "microservices"

        elif any(
            term in content for term in ["data", "analytics", "pandas", "analysis"]
        ):
            return "data_science"

        else:
            return "web_api"  # Default fallback

    def _create_docker_environment(
        self,
        project_path: Path,
        project_name: str,
        security_level: SecurityLevel,
        requirements: Dict = None,
    ):
        """Create advanced Docker environment using template manager"""

        # Detect project type
        project_type = self._detect_project_type(requirements or {})

        # Get appropriate Docker template
        docker_template = self.docker_manager.get_template_for_project(
            project_type, security_level
        )

        if docker_template:
            # Use advanced template system
            created_files = self.docker_manager.create_template_environment(
                project_path, docker_template, project_name
            )

            # Log template usage
            self._log_docker_template_usage(
                project_name, project_type, docker_template, created_files
            )
        else:
            # Fallback to basic Docker setup
            self._create_basic_docker_environment(
                project_path, project_name, security_level
            )

    def _create_basic_docker_environment(
        self, project_path: Path, project_name: str, security_level: SecurityLevel
    ):
        """Create basic Docker environment (fallback)"""

        docker_dir = project_path / ".docker"

        # Copy appropriate Dockerfile
        source_dockerfile = (
            self.workspace_root / "docker" / f"Dockerfile.{security_level.value}"
        )
        target_dockerfile = docker_dir / "Dockerfile"

        if source_dockerfile.exists():
            shutil.copy2(source_dockerfile, target_dockerfile)

        # Create docker-compose.yml
        compose_template = (
            self.workspace_root / "docker" / "docker-compose.template.yml"
        )
        if compose_template.exists():
            compose_content = compose_template.read_text()

            # Configure based on security level
            additional_config = self._get_docker_security_config(security_level)

            compose_content = compose_content.format(
                security_level=security_level.value,
                project_name=project_name,
                additional_config=additional_config,
            )

            compose_file = docker_dir / "docker-compose.yml"
            compose_file.write_text(compose_content)

        # Create start script
        start_script = docker_dir / "start.sh"
        start_script.write_text(
            f"""#!/bin/bash
# Elders Guild Project Start Script
# Security Level: {security_level.value}

echo "🚀 Starting {project_name} in {security_level.value} mode"

# Build and start container
docker-compose -f .docker/docker-compose.yml up --build -d

echo "✅ Project started successfully"
echo "📁 Access via: docker exec -it {project_name}_{security_level.value} bash"
"""
        )
        start_script.chmod(0o755)

        # Create stop script
        stop_script = docker_dir / "stop.sh"
        stop_script.write_text(
            f"""#!/bin/bash
# Elders Guild Project Stop Script

echo "🛑 Stopping {project_name}"

# Stop and remove container
docker-compose -f .docker/docker-compose.yml down

echo "✅ Project stopped successfully"
"""
        )
        stop_script.chmod(0o755)

    def _log_docker_template_usage(
        self, project_name: str, project_type: str, template, created_files: Dict
    ):
        """Log Docker template usage for analytics"""

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "project_name": project_name,
            "project_type": project_type,
            "template_name": template.name,
            "security_level": template.security_level.value,
            "runtime": template.runtime.value,
            "created_files": list(created_files.keys()),
            "resource_limits": template.resource_limits,
        }

        log_file = self.workspace_root / "logs" / "docker_template_usage.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, default=str) + "\n")

    def _get_docker_security_config(self, security_level: SecurityLevel) -> str:
        """Get Docker security configuration based on security level"""

        configs = {
            SecurityLevel.SANDBOX: """
    network_mode: none
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges
    cap_drop:
      - ALL""",
            SecurityLevel.RESTRICTED: """
    networks:
      - restricted
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges""",
            SecurityLevel.DEVELOPMENT: """
    ports:
      - "8000:8000"
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE""",
            SecurityLevel.TRUSTED: """
    ports:
      - "8000:8000"
    privileged: true
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock""",
        }

        return configs.get(security_level, "")

    def _create_readme(
        self, project_path: Path, requirements: Dict, security_level: SecurityLevel
    ):
        """Create project README with security information"""

        readme_content = f"""# {project_path.name}

Elders Guild Auto-Generated Project

## 🔒 Security Information

**Security Level**: {security_level.value}
**Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📋 Project Overview

{requirements.get('description', 'No description provided')}

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Start the development environment
./.docker/start.sh

# Access the container
docker exec -it {project_path.name}_{security_level.value} bash

# Stop the environment
./.docker/stop.sh
```

### Direct Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Start development server (if applicable)
python src/main.py
```

## 📁 Project Structure

```
{project_path.name}/
├── src/                    # Source code
├── tests/                  # Test files (TDD required)
├── docs/                   # Documentation
├── config/                 # Configuration files
├── scripts/                # Utility scripts
├── data/                   # Data files
├── logs/                   # Log files
├── .ai_company/           # Elders Guild metadata
└── .docker/               # Docker configuration
```

## 🛡️ Security Features

- **Isolated Environment**: Project runs in {security_level.value} security mode
- **Docker Containerization**: Sandboxed execution environment
- **Access Control**: Limited filesystem and network access
- **Audit Logging**: All operations are logged for security

## 🔄 Elders Guild Integration

This project is managed by Elders Guild's automated development system:

```bash
# Submit tasks to Elders Guild
ai-test "Add new feature: user authentication"

# Generate code from requirements
ai-requirements-to-code requirements.json

# Project status
ai-project-status {project_path.name}
```

## 🤝 Contributing

1.0 All development must follow TDD (Test-Driven Development)
2.0 Use the provided Docker environment for consistency
3.0 Security policies are enforced automatically
4.0 Submit changes through Elders Guild workflow

---
Generated by Elders Guild - Automated Development System
Security Level: {security_level.value} | Docker: Enabled
"""

        readme_file = project_path / "README.md"
        readme_file.write_text(readme_content)

    def _create_requirements_file(self, project_path: Path, requirements: Dict):
        """Create requirements.txt based on project requirements"""

        # Base requirements for all projects
        base_requirements = [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ]

        # Extract additional requirements from project specs
        additional_reqs = requirements.get("dependencies", [])
        if isinstance(additional_reqs, str):
            additional_reqs = [additional_reqs]

        all_requirements = base_requirements + additional_reqs

        requirements_file = project_path / "requirements.txt"
        requirements_file.write_text("\n".join(all_requirements) + "\n")

    def _create_gitignore(self, project_path: Path):
        """Create comprehensive .gitignore"""

        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/
*.log

# Data
data/*.csv
data/*.json
!data/.gitkeep

# Docker
.docker/volumes/

# Elders Guild
.ai_company/cache/
.ai_company/temp/

# Security
.env
*.key
*.pem
secrets/
"""

        gitignore_file = project_path / ".gitignore"
        gitignore_file.write_text(gitignore_content)

    def _log_project_creation(
        self,
        project_path: Path,
        risk_assessment: ProjectRisk,
        security_level: SecurityLevel,
    ):
        """Log project creation for audit purposes"""

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "project_created",
            "project_path": str(project_path),
            "project_name": project_path.name,
            "security_level": security_level.value,
            "risk_assessment": {
                "level": risk_assessment.level,
                "factors": risk_assessment.factors,
                "manual_approval": risk_assessment.manual_approval,
            },
        }

        log_file = self.workspace_root / "logs" / "project_creation.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

    def list_projects(self) -> Dict[str, List[Dict]]:
        """List all projects organized by security level"""

        projects_by_level = {}

        # 繰り返し処理
        for security_level in SecurityLevel:
            level_dir = self.workspace_root / security_level.value
            projects = []

            if level_dir.exists():
                for project_dir in level_dir.iterdir():
                    if project_dir.is_dir():
                        metadata_file = project_dir / ".elders_guild" / "project.json"
                        if not (metadata_file.exists()):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if metadata_file.exists():
                            # Deep nesting detected (depth: 6) - consider refactoring
                            with open(metadata_file, "r", encoding="utf-8") as f:
                                metadata = json.load(f)
                            projects.append(
                                {
                                    "name": metadata["name"],
                                    "path": str(project_dir),
                                    "created": metadata["created"],
                                    "security_level": metadata["security_level"],
                                }
                            )

            projects_by_level[security_level.value] = projects

        return projects_by_level

    def get_project_status(self, project_name: str) -> Optional[Dict]:
        """Get project status and security information"""

        # Search across all security levels
        for security_level in SecurityLevel:
            level_dir = self.workspace_root / security_level.value
            project_path = level_dir / project_name

            if project_path.exists():
                metadata_file = project_path / ".elders_guild" / "project.json"
                if metadata_file.exists():
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        metadata = json.load(f)

                    # Check Docker status
                    docker_running = self._check_docker_status(
                        project_name, security_level.value
                    )

                    return {
                        "name": metadata["name"],
                        "path": str(project_path),
                        "security_level": metadata["security_level"],
                        "created": metadata["created"],
                        "docker_running": docker_running,
                        "github_integration": metadata.get("github_integration", False),
                    }

        return None

    def _check_docker_status(self, project_name: str, security_level: str) -> bool:
        """Check if Docker container is running for the project"""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    f"name={project_name}_{security_level}",
                    "--format",
                    "{{.Names}}",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return bool(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False


if __name__ == "__main__":
    # Example usage
    manager = AutoProjectManager()

    # Test project creation
    test_requirements = {
        "description": "Test project for auto manager",
        "dependencies": ["flask", "requests"],
        "features": ["web_server", "api_client"],
    }

    try:
        project_path, risk = manager.create_project(
            "test_auto_project", test_requirements
        )
        print(f"✅ Project created: {project_path}")
        print(f"🔒 Security level: {risk.recommended_security.value}")
        print(f"📊 Risk level: {risk.level}")
    except Exception as e:
        print(f"❌ Error: {e}")
