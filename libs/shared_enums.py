#!/usr/bin/env python3
"""
Shared Enums for Elders Guild Project Management System
Provides common enumerations to avoid circular imports
"""

from enum import Enum

class SecurityLevel(Enum):
    """Docker isolation security levels"""
    SANDBOX = "sandbox"      # Minimal permissions, no network
    RESTRICTED = "restricted"  # Limited network, filesystem isolation
    DEVELOPMENT = "development"  # Standard development environment
    TRUSTED = "trusted"        # Full permissions (manual approval required)

class ProjectType(Enum):
    """Supported project types with specialized environments"""
    WEB_API = "web_api"           # FastAPI, Flask, Django REST
    FULL_STACK_WEB = "fullstack"  # React/Vue + Backend
    ML_RESEARCH = "ml_research"   # Jupyter, TensorFlow, PyTorch
    ML_PRODUCTION = "ml_prod"     # Production ML services
    DATA_SCIENCE = "data_science" # Pandas, Analysis tools
    CLI_TOOLS = "cli_tools"       # Command line applications
    MICROSERVICES = "microservices" # Distributed systems
    BLOCKCHAIN = "blockchain"     # Web3, Smart contracts
    IOT_EDGE = "iot_edge"        # Edge computing, sensors
    GAME_DEV = "game_dev"        # Game development
    MOBILE_BACKEND = "mobile_api" # Mobile app backends
    DEVOPS_TOOLS = "devops"      # Infrastructure tools

class RuntimeEnvironment(Enum):
    """Runtime environment types"""
    PYTHON_SLIM = "python_slim"
    PYTHON_FULL = "python_full"
    NODE_LTS = "node_lts"
    NODE_ALPINE = "node_alpine"
    GOLANG = "golang"
    RUST = "rust"
    JAVA_OPENJDK = "java_openjdk"
    DOTNET = "dotnet"
    UBUNTU_DEV = "ubuntu_dev"
    ALPINE_MINIMAL = "alpine_minimal"