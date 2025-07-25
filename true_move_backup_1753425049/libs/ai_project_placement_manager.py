#!/usr/bin/env python3
"""
Elders Guild Intelligent Project Placement Manager
Automatically determines optimal project placement based on requirements, risk analysis, and resource availability
Part of Phase 1: Foundation System
"""

import json
import logging
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.auto_project_manager import AutoProjectManager
from libs.env_config import get_config
from libs.project_risk_analyzer import ProjectRiskAnalyzer, RiskLevel
from libs.shared_enums import SecurityLevel


class PlacementStrategy(Enum):
    """Project placement strategies"""

    SECURITY_FIRST = "security_first"  # Prioritize security over convenience
    BALANCED = "balanced"  # Balance security and development needs
    DEVELOPMENT_FOCUSED = "dev_focused"  # Prioritize development convenience
    PERFORMANCE_OPTIMIZED = "performance"  # Optimize for computational performance


class ResourceType(Enum):
    """Available resource types"""

    CPU = "cpu"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"
    GPU = "gpu"


@dataclass
class PlacementCriteria:
    """Criteria for project placement decisions"""

    security_requirements: SecurityLevel
    resource_needs: Dict[ResourceType, float]  # 0.0 to 1.0 scale
    development_phase: str  # prototype, development, testing, production
    team_access_level: str  # junior, senior, architect, admin
    compliance_requirements: List[str]
    performance_requirements: Dict[str, Any]


@dataclass
class PlacementRecommendation:
    """Recommended placement for a project"""

    workspace_path: Path
    security_level: SecurityLevel
    isolation_type: str
    resource_allocation: Dict[ResourceType, float]
    justification: List[str]
    warnings: List[str]
    estimated_setup_time: int  # minutes
    confidence_score: float  # 0.0 to 1.0


class AIProjectPlacementManager:
    """Intelligent project placement decision engine"""

    def __init__(self):
        """初期化メソッド"""
        self.config = get_config()
        self.auto_manager = AutoProjectManager()
        self.risk_analyzer = ProjectRiskAnalyzer()
        self.logger = logging.getLogger(__name__)

        # Initialize placement rules and scoring weights
        self._initialize_placement_rules()
        self._initialize_resource_monitoring()

    def _initialize_placement_rules(self):
        """Initialize intelligent placement rules"""
        self.placement_rules = {
            # Security-based rules
            "security_rules": {
                SecurityLevel.SANDBOX: {
                    "max_network_access": 0.0,
                    "filesystem_isolation": True,
                    "resource_limits": {"cpu": 0.5, "memory": 0.5, "storage": 0.3},
                    "monitoring_level": "high",
                },
                SecurityLevel.RESTRICTED: {
                    "max_network_access": 0.3,
                    "filesystem_isolation": True,
                    "resource_limits": {"cpu": 0.7, "memory": 0.7, "storage": 0.5},
                    "monitoring_level": "medium",
                },
                SecurityLevel.DEVELOPMENT: {
                    "max_network_access": 0.8,
                    "filesystem_isolation": False,
                    "resource_limits": {"cpu": 0.9, "memory": 0.9, "storage": 0.8},
                    "monitoring_level": "low",
                },
                SecurityLevel.TRUSTED: {
                    "max_network_access": 1.0,
                    "filesystem_isolation": False,
                    "resource_limits": {"cpu": 1.0, "memory": 1.0, "storage": 1.0},
                    "monitoring_level": "audit",
                },
            },
            # Development phase rules
            "phase_rules": {
                "prototype": {
                    "preferred_security": SecurityLevel.DEVELOPMENT,
                    "resource_multiplier": 0.5,
                    "isolation_priority": "low",
                },
                "development": {
                    "preferred_security": SecurityLevel.DEVELOPMENT,
                    "resource_multiplier": 0.8,
                    "isolation_priority": "medium",
                },
                "testing": {
                    "preferred_security": SecurityLevel.RESTRICTED,
                    "resource_multiplier": 1.0,
                    "isolation_priority": "high",
                },
                "production": {
                    "preferred_security": SecurityLevel.SANDBOX,
                    "resource_multiplier": 1.2,
                    "isolation_priority": "maximum",
                },
            },
            # Team access rules
            "access_rules": {
                "junior": {
                    "max_security_level": SecurityLevel.DEVELOPMENT,
                    "requires_approval": ["RESTRICTED", "SANDBOX", "TRUSTED"],
                    "resource_limits": {"cpu": 0.6, "memory": 0.6},
                },
                "senior": {
                    "max_security_level": SecurityLevel.RESTRICTED,
                    "requires_approval": ["TRUSTED"],
                    "resource_limits": {"cpu": 0.9, "memory": 0.9},
                },
                "architect": {
                    "max_security_level": SecurityLevel.SANDBOX,
                    "requires_approval": ["TRUSTED"],
                    "resource_limits": {"cpu": 1.0, "memory": 1.0},
                },
                "admin": {
                    "max_security_level": SecurityLevel.TRUSTED,
                    "requires_approval": [],
                    "resource_limits": {"cpu": 1.0, "memory": 1.0},
                },
            },
        }

        # Scoring weights for placement decisions
        self.scoring_weights = {
            "security_compliance": 0.35,
            "resource_availability": 0.25,
            "development_efficiency": 0.20,
            "team_experience": 0.15,
            "performance_requirements": 0.05,
        }

    def _initialize_resource_monitoring(self):
        """Initialize resource monitoring capabilities"""
        self.resource_thresholds = {
            ResourceType.CPU: 0.8,  # 80% CPU usage threshold
            ResourceType.MEMORY: 0.8,  # 80% memory usage threshold
            ResourceType.STORAGE: 0.9,  # 90% storage usage threshold
            ResourceType.NETWORK: 0.7,  # 70% network usage threshold
        }

        # Mock current resource usage (in production, this would query actual system)
        self.current_resource_usage = {
            SecurityLevel.SANDBOX: {
                ResourceType.CPU: 0.3,
                ResourceType.MEMORY: 0.4,
                ResourceType.STORAGE: 0.2,
                ResourceType.NETWORK: 0.1,
            },
            SecurityLevel.RESTRICTED: {
                ResourceType.CPU: 0.5,
                ResourceType.MEMORY: 0.6,
                ResourceType.STORAGE: 0.4,
                ResourceType.NETWORK: 0.3,
            },
            SecurityLevel.DEVELOPMENT: {
                ResourceType.CPU: 0.7,
                ResourceType.MEMORY: 0.6,
                ResourceType.STORAGE: 0.5,
                ResourceType.NETWORK: 0.6,
            },
            SecurityLevel.TRUSTED: {
                ResourceType.CPU: 0.2,
                ResourceType.MEMORY: 0.3,
                ResourceType.STORAGE: 0.1,
                ResourceType.NETWORK: 0.1,
            },
        }

    def analyze_placement_requirements(
        self,
        requirements: Dict,
        strategy: PlacementStrategy = PlacementStrategy.BALANCED,
    ) -> PlacementCriteria:
        """Analyze project requirements to determine placement criteria"""

        # Analyze security requirements using risk analyzer
        project_content = json.dumps(requirements, default=str)
        risk_analysis = self.risk_analyzer.analyze_project(
            project_content, requirements
        )

        # Map risk level to security requirements
        security_mapping = {
            RiskLevel.MINIMAL: SecurityLevel.DEVELOPMENT,
            RiskLevel.LOW: SecurityLevel.DEVELOPMENT,
            RiskLevel.MEDIUM: SecurityLevel.RESTRICTED,
            RiskLevel.HIGH: SecurityLevel.SANDBOX,
            RiskLevel.CRITICAL: SecurityLevel.SANDBOX,
        }
        security_requirements = security_mapping.get(
            risk_analysis.risk_level, SecurityLevel.SANDBOX
        )

        # Estimate resource needs based on project characteristics
        resource_needs = self._estimate_resource_needs(requirements)

        # Determine development phase
        development_phase = requirements.get("development_phase", "development")

        # Get team access level
        team_access_level = requirements.get("team_access_level", "senior")

        # Extract compliance requirements
        compliance_requirements = requirements.get("compliance", [])

        # Extract performance requirements
        performance_requirements = requirements.get("performance", {})

        return PlacementCriteria(
            security_requirements=security_requirements,
            resource_needs=resource_needs,
            development_phase=development_phase,
            team_access_level=team_access_level,
            compliance_requirements=compliance_requirements,
            performance_requirements=performance_requirements,
        )

    def _estimate_resource_needs(self, requirements: Dict) -> Dict[ResourceType, float]:
        """Estimate resource needs based on project characteristics"""

        base_needs = {
            ResourceType.CPU: 0.3,
            ResourceType.MEMORY: 0.3,
            ResourceType.STORAGE: 0.2,
            ResourceType.NETWORK: 0.2,
        }

        # Adjust based on project type and features
        features = requirements.get("features", [])
        dependencies = requirements.get("dependencies", [])

        # High CPU needs
        if any(
            feature in str(features).lower()
            for feature in ["ml", "ai", "compute", "processing"]
        ):
            base_needs[ResourceType.CPU] += 0.4

        # High memory needs
        if any(
            feature in str(features).lower()
            for feature in ["database", "cache", "analytics"]
        ):
            base_needs[ResourceType.MEMORY] += 0.3

        # High storage needs
        if any(
            feature in str(features).lower()
            for feature in ["file_upload", "storage", "backup"]
        ):
            base_needs[ResourceType.STORAGE] += 0.4

        # High network needs
        if any(
            feature in str(features).lower()
            for feature in ["api", "web", "scraping", "download"]
        ):
            base_needs[ResourceType.NETWORK] += 0.3

        # Adjust based on dependencies
        heavy_deps = ["tensorflow", "pytorch", "opencv", "pandas", "numpy"]
        if any(dep in str(dependencies).lower() for dep in heavy_deps):
            base_needs[ResourceType.CPU] += 0.2
            base_needs[ResourceType.MEMORY] += 0.2

        # Normalize to 0.0-1.0 range
        for resource in base_needs:
            base_needs[resource] = min(base_needs[resource], 1.0)

        return base_needs

    def recommend_placement(
        self,
        criteria: PlacementCriteria,
        strategy: PlacementStrategy = PlacementStrategy.BALANCED,
    ) -> PlacementRecommendation:
        """Generate intelligent placement recommendation"""

        # Calculate placement scores for each security level
        placement_scores = self._calculate_placement_scores(criteria, strategy)

        # Select best placement option
        best_security_level = max(
            placement_scores.keys(), key=lambda x: placement_scores[x]["total_score"]
        )
        best_score_data = placement_scores[best_security_level]

        # Determine workspace path
        workspace_path = self.auto_manager.workspace_root / best_security_level.value

        # Determine isolation type
        isolation_type = self._determine_isolation_type(criteria, best_security_level)

        # Calculate resource allocation
        resource_allocation = self._calculate_resource_allocation(
            criteria, best_security_level
        )

        # Generate justification
        justification = self._generate_justification(
            criteria, best_security_level, best_score_data
        )

        # Generate warnings
        warnings = self._generate_warnings(criteria, best_security_level)

        # Estimate setup time
        setup_time = self._estimate_setup_time(criteria, best_security_level)

        return PlacementRecommendation(
            workspace_path=workspace_path,
            security_level=best_security_level,
            isolation_type=isolation_type,
            resource_allocation=resource_allocation,
            justification=justification,
            warnings=warnings,
            estimated_setup_time=setup_time,
            confidence_score=best_score_data["total_score"],
        )

    def _calculate_placement_scores(
        self, criteria: PlacementCriteria, strategy: PlacementStrategy
    ) -> Dict[SecurityLevel, Dict]:
        """Calculate placement scores for each security level"""
        scores = {}

        for security_level in SecurityLevel:
            score_components = {}

            # Security compliance score
            security_score = self._calculate_security_score(criteria, security_level)
            score_components["security"] = security_score

            # Resource availability score
            resource_score = self._calculate_resource_score(criteria, security_level)
            score_components["resource"] = resource_score

            # Development efficiency score
            efficiency_score = self._calculate_efficiency_score(
                criteria, security_level
            )
            score_components["efficiency"] = efficiency_score

            # Team experience score
            team_score = self._calculate_team_score(criteria, security_level)
            score_components["team"] = team_score

            # Performance score
            performance_score = self._calculate_performance_score(
                criteria, security_level
            )
            score_components["performance"] = performance_score

            # Apply strategy-specific weights
            strategy_weights = self._get_strategy_weights(strategy)

            total_score = (
                score_components["security"] * strategy_weights["security_compliance"]
                + score_components["resource"]
                * strategy_weights["resource_availability"]
                + score_components["efficiency"]
                * strategy_weights["development_efficiency"]
                + score_components["team"] * strategy_weights["team_experience"]
                + score_components["performance"]
                * strategy_weights["performance_requirements"]
            )

            score_components["total_score"] = total_score
            scores[security_level] = score_components

        return scores

    def _calculate_security_score(
        self, criteria: PlacementCriteria, security_level: SecurityLevel
    ) -> float:
        """Calculate security compliance score"""

        if security_level == criteria.security_requirements:
            return 1.0
        elif (
            security_level.value == "sandbox"
            and criteria.security_requirements.value in ["restricted", "development"]
        ):
            return 0.8  # Over-secure is better than under-secure
        elif (
            security_level.value == "restricted"
            and criteria.security_requirements.value == "development"
        ):
            return 0.7
        elif (
            security_level.value == "development"
            and criteria.security_requirements.value in ["restricted", "sandbox"]
        ):
            return 0.3  # Under-secure is risky
        else:
            return 0.5

    def _calculate_resource_score(
        self, criteria: PlacementCriteria, security_level: SecurityLevel
    ) -> float:
        """Calculate resource availability score"""

        current_usage = self.current_resource_usage[security_level]
        resource_limits = self.placement_rules["security_rules"][security_level][
            "resource_limits"
        ]

        # Check if resources are available
        available_score = 1.0
        for resource_type, needed in criteria.resource_needs.items():
            if (
                resource_type in current_usage
                and resource_type.value in resource_limits
            ):
                current = current_usage[resource_type]
                limit = resource_limits[resource_type.value]
                available = limit - current

                if needed > available:
                    available_score *= 0.5  # Penalize if resources not available

        return available_score

    def _calculate_efficiency_score(
        self, criteria: PlacementCriteria, security_level: SecurityLevel
    ) -> float:
        """Calculate development efficiency score"""

        phase_rules = self.placement_rules["phase_rules"]
        phase_data = phase_rules.get(
            criteria.development_phase, phase_rules["development"]
        )

        if security_level == phase_data["preferred_security"]:
            return 1.0
        elif security_level.value == "development":
            return 0.9  # Development is usually most efficient
        elif security_level.value == "restricted":
            return 0.7
        elif security_level.value == "sandbox":
            return 0.4  # Sandbox has development overhead
        else:
            return 0.3

    def _calculate_team_score(
        self, criteria: PlacementCriteria, security_level: SecurityLevel
    ) -> float:
        """Calculate team experience score"""

        access_rules = self.placement_rules["access_rules"]
        team_data = access_rules.get(criteria.team_access_level, access_rules["senior"])

        # Check if team has access to this security level
        if security_level.value.upper() in team_data["requires_approval"]:
            return 0.3  # Requires approval, lower score
        elif security_level == team_data["max_security_level"]:
            return 1.0
        else:
            return 0.8

    def _calculate_performance_score(
        self, criteria: PlacementCriteria, security_level: SecurityLevel
    ) -> float:
        """Calculate performance requirements score"""

        # More restrictive security levels have performance overhead
        performance_factors = {
            SecurityLevel.DEVELOPMENT: 1.0,
            SecurityLevel.RESTRICTED: 0.8,
            SecurityLevel.SANDBOX: 0.6,
            SecurityLevel.TRUSTED: 0.9,
        }

        return performance_factors.get(security_level, 0.7)

    def _get_strategy_weights(self, strategy: PlacementStrategy) -> Dict[str, float]:
        """Get scoring weights for different strategies"""

        strategy_weights = {
            PlacementStrategy.SECURITY_FIRST: {
                "security_compliance": 0.5,
                "resource_availability": 0.2,
                "development_efficiency": 0.1,
                "team_experience": 0.1,
                "performance_requirements": 0.1,
            },
            PlacementStrategy.BALANCED: self.scoring_weights,
            PlacementStrategy.DEVELOPMENT_FOCUSED: {
                "security_compliance": 0.2,
                "resource_availability": 0.2,
                "development_efficiency": 0.4,
                "team_experience": 0.15,
                "performance_requirements": 0.05,
            },
            PlacementStrategy.PERFORMANCE_OPTIMIZED: {
                "security_compliance": 0.2,
                "resource_availability": 0.3,
                "development_efficiency": 0.2,
                "team_experience": 0.1,
                "performance_requirements": 0.2,
            },
        }

        return strategy_weights.get(strategy, self.scoring_weights)

    def _determine_isolation_type(
        self, criteria: PlacementCriteria, security_level: SecurityLevel
    ) -> str:
        """Determine specific isolation configuration"""

        isolation_configs = {
            SecurityLevel.SANDBOX: "complete_isolation",
            SecurityLevel.RESTRICTED: "network_limited",
            SecurityLevel.DEVELOPMENT: "workspace_isolated",
            SecurityLevel.TRUSTED: "minimal_isolation",
        }

        return isolation_configs.get(security_level, "workspace_isolated")

    def _calculate_resource_allocation(
        self, criteria: PlacementCriteria, security_level: SecurityLevel
    ) -> Dict[ResourceType, float]:
        """Calculate optimal resource allocation"""

        security_limits = self.placement_rules["security_rules"][security_level][
            "resource_limits"
        ]

        allocation = {}
        for resource_type, needed in criteria.resource_needs.items():
            if resource_type.value in security_limits:
                # Allocate needed amount within security limits
                max_allowed = security_limits[resource_type.value]
                allocation[resource_type] = min(needed, max_allowed)
            else:
                allocation[resource_type] = needed

        return allocation

    def _generate_justification(
        self,
        criteria: PlacementCriteria,
        security_level: SecurityLevel,
        score_data: Dict,
    ) -> List[str]:
        """Generate human-readable justification for placement decision"""

        justifications = []

        # Security justification
        if security_level == criteria.security_requirements:
            justifications.append(
                f"Matches required security level: {security_level.value}"
            )
        elif security_level.value == "sandbox":
            justifications.append(
                "Enhanced security isolation recommended due to risk factors"
            )

        # Resource justification
        if score_data["resource"] > 0.8:
            justifications.append("Sufficient resources available in this environment")
        elif score_data["resource"] < 0.5:
            justifications.append("Limited resources, may need optimization")

        # Development phase justification
        phase_rules = self.placement_rules["phase_rules"]
        phase_data = phase_rules.get(criteria.development_phase, {})
        if security_level == phase_data.get("preferred_security"):
            justifications.append(f"Optimal for {criteria.development_phase} phase")

        # Team access justification
        access_rules = self.placement_rules["access_rules"]
        team_data = access_rules.get(criteria.team_access_level, {})
        if security_level.value.upper() not in team_data.get("requires_approval", []):
            justifications.append(
                f"Appropriate for {criteria.team_access_level} team access level"
            )

        return justifications

    def _generate_warnings(
        self, criteria: PlacementCriteria, security_level: SecurityLevel
    ) -> List[str]:
        """Generate warnings about the placement decision"""

        warnings = []

        # Security warnings
        if security_level != criteria.security_requirements:
            if (
                security_level.value == "development"
                and criteria.security_requirements.value in ["restricted", "sandbox"]
            ):
                warnings.append(
                    "⚠️ Security level lower than recommended - additional approval may be required"
                )

        # Resource warnings
        current_usage = self.current_resource_usage[security_level]
        for resource_type, needed in criteria.resource_needs.items():
            if resource_type in current_usage:
                if (
                    current_usage[resource_type] + needed
                    > self.resource_thresholds[resource_type]
                ):
                    warnings.append(
                        f"⚠️ High {resource_type.value} usage - monitor performance"
                    )

        # Team access warnings
        access_rules = self.placement_rules["access_rules"]
        team_data = access_rules.get(criteria.team_access_level, {})
        if security_level.value.upper() in team_data.get("requires_approval", []):
            warnings.append("⚠️ Manual approval required for this security level")

        return warnings

    def _estimate_setup_time(
        self, criteria: PlacementCriteria, security_level: SecurityLevel
    ) -> int:
        """Estimate project setup time in minutes"""

        base_times = {
            SecurityLevel.DEVELOPMENT: 5,
            SecurityLevel.RESTRICTED: 10,
            SecurityLevel.SANDBOX: 15,
            SecurityLevel.TRUSTED: 20,
        }

        base_time = base_times.get(security_level, 10)

        # Add time for complex resource requirements
        total_resources = sum(criteria.resource_needs.values())
        if total_resources > 2.0:
            base_time += 5

        # Add time for compliance requirements
        if criteria.compliance_requirements:
            base_time += len(criteria.compliance_requirements) * 2

        return base_time

    def create_project_with_intelligent_placement(
        self,
        project_name: str,
        requirements: Dict,
        strategy: PlacementStrategy = PlacementStrategy.BALANCED,
    ) -> Tuple[Path, Dict]:
        """Create project using intelligent placement system"""

        # Analyze placement requirements
        criteria = self.analyze_placement_requirements(requirements, strategy)

        # Get placement recommendation
        recommendation = self.recommend_placement(criteria, strategy)

        # Log placement decision
        self._log_placement_decision(project_name, criteria, recommendation)

        # Create project using recommended placement
        try:
            project_path, risk_assessment = self.auto_manager.create_project(
                project_name, requirements, recommendation.security_level
            )

            # Save placement metadata (convert enums to strings for JSON serialization)
            criteria_dict = asdict(criteria)
            criteria_dict["security_requirements"] = (
                criteria.security_requirements.value
            )
            criteria_dict["resource_needs"] = {
                k.value: v for k, v in criteria.resource_needs.items()
            }

            recommendation_dict = asdict(recommendation)
            recommendation_dict["security_level"] = recommendation.security_level.value
            recommendation_dict["workspace_path"] = str(recommendation.workspace_path)
            recommendation_dict["resource_allocation"] = {
                k.value: v for k, v in recommendation.resource_allocation.items()
            }

            placement_metadata = {
                "criteria": criteria_dict,
                "recommendation": recommendation_dict,
                "risk_assessment": {
                    "level": risk_assessment.level,
                    "factors": risk_assessment.factors,
                    "manual_approval": risk_assessment.manual_approval,
                },
                "created_at": datetime.now().isoformat(),
                "strategy_used": strategy.value,
            }

            metadata_file = project_path / ".elders_guild" / "placement.json"
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(
                    placement_metadata, f, indent=2, ensure_ascii=False, default=str
                )

            return project_path, {
                "placement_recommendation": recommendation,
                "risk_assessment": risk_assessment,
                "metadata_saved": str(metadata_file),
            }

        except Exception as e:
            self.logger.error(
                f"Failed to create project with intelligent placement: {e}"
            )
            raise

    def _log_placement_decision(
        self,
        project_name: str,
        criteria: PlacementCriteria,
        recommendation: PlacementRecommendation,
    ):
        """Log placement decision for audit and learning"""

        # Convert criteria to serializable format
        criteria_dict = asdict(criteria)
        criteria_dict["security_requirements"] = criteria.security_requirements.value
        criteria_dict["resource_needs"] = {
            k.value: v for k, v in criteria.resource_needs.items()
        }

        # Convert recommendation to serializable format
        recommendation_dict = asdict(recommendation)
        recommendation_dict["security_level"] = recommendation.security_level.value
        recommendation_dict["workspace_path"] = str(recommendation.workspace_path)
        recommendation_dict["resource_allocation"] = {
            k.value: v for k, v in recommendation.resource_allocation.items()
        }

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "project_name": project_name,
            "criteria": criteria_dict,
            "recommendation": recommendation_dict,
            "decision_factors": {
                "security_level": recommendation.security_level.value,
                "confidence": recommendation.confidence_score,
                "warnings_count": len(recommendation.warnings),
            },
        }

        log_file = self.auto_manager.workspace_root / "logs" / "placement_decisions.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, default=str) + "\n")


if __name__ == "__main__":
    # Example usage and testing
    placement_manager = AIProjectPlacementManager()

    # Test with different project types
    test_cases = [
        {
            "name": "safe_web_app",
            "requirements": {
                "description": "Simple web application",
                "dependencies": ["fastapi", "uvicorn"],
                "features": ["web_api", "database"],
                "development_phase": "development",
                "team_access_level": "senior",
            },
        },
        {
            "name": "ml_project",
            "requirements": {
                "description": "Machine learning project",
                "dependencies": ["tensorflow", "pandas", "scikit-learn"],
                "features": ["ml_training", "data_processing"],
                "development_phase": "prototype",
                "team_access_level": "senior",
                "performance": {"gpu_required": True},
            },
        },
        {
            "name": "admin_tool",
            "requirements": {
                "description": "System administration tool",
                "dependencies": ["paramiko", "fabric"],
                "features": ["ssh_access", "system_commands"],
                "development_phase": "testing",
                "team_access_level": "admin",
            },
        },
    ]

    # 繰り返し処理
    for test_case in test_cases:
        print(f"\n=== Testing: {test_case['name']} ===")

        try:
            criteria = placement_manager.analyze_placement_requirements(
                test_case["requirements"]
            )
            recommendation = placement_manager.recommend_placement(criteria)

            print(f"Security Level: {recommendation.security_level.value}")
            print(f"Isolation: {recommendation.isolation_type}")
            print(f"Confidence: {recommendation.confidence_score:0.2f}")
            print(f"Setup Time: {recommendation.estimated_setup_time} minutes")
            print(f"Justifications: {len(recommendation.justification)}")
            for justification in recommendation.justification:
                print(f"  - {justification}")

            if recommendation.warnings:
                print("Warnings:")
                # Deep nesting detected (depth: 5) - consider refactoring
                for warning in recommendation.warnings:
                    print(f"  - {warning}")

        except Exception as e:
            print(f"Error: {e}")

    print("\n✅ AI Project Placement Manager test completed")
