#!/usr/bin/env python3
"""
Advanced Project Risk Analysis System
Part of AI Company Phase 1: Foundation System
Provides comprehensive security risk assessment for automated project placement
"""

import re
import json
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class RiskCategory(Enum):
    """Risk category classification"""
    SYSTEM_ACCESS = "system_access"
    NETWORK_OPERATIONS = "network_operations"
    FILE_OPERATIONS = "file_operations"
    EXTERNAL_DEPENDENCIES = "external_dependencies"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_SENSITIVITY = "data_sensitivity"
    CRYPTO_OPERATIONS = "crypto_operations"
    CONTAINER_ESCAPE = "container_escape"

class RiskLevel(Enum):
    """Risk level enumeration"""
    MINIMAL = "minimal"        # Score: 0.0 - 0.2
    LOW = "low"                # Score: 0.2 - 0.4
    MEDIUM = "medium"          # Score: 0.4 - 0.6
    HIGH = "high"              # Score: 0.6 - 0.8
    CRITICAL = "critical"      # Score: 0.8 - 1.0

@dataclass
class RiskFactor:
    """Individual risk factor detected in project"""
    category: RiskCategory
    description: str
    severity: float  # 0.0 to 1.0
    pattern: str
    mitigation: str
    detected_in: str  # file or section where detected

@dataclass
class RiskAnalysisResult:
    """Comprehensive risk analysis result"""
    overall_score: float
    risk_level: RiskLevel
    factors: List[RiskFactor]
    recommendations: List[str]
    required_mitigations: List[str]
    manual_review_required: bool
    isolation_level: str  # sandbox, restricted, development, trusted
    analysis_timestamp: str

class ProjectRiskAnalyzer:
    """Advanced risk analysis engine for project security assessment"""
    
    def __init__(self):
        self.risk_patterns = self._initialize_risk_patterns()
        self.dependency_risks = self._load_dependency_risks()
        self.analysis_cache = {}
    
    def _initialize_risk_patterns(self) -> Dict[RiskCategory, List[Dict]]:
        """Initialize comprehensive risk pattern database"""
        return {
            RiskCategory.SYSTEM_ACCESS: [
                {
                    "patterns": [r"os\.system", r"subprocess\.call", r"subprocess\.run", 
                                r"shell=True", r"exec\s*\(", r"eval\s*\("],
                    "severity": 0.8,
                    "description": "Direct system command execution",
                    "mitigation": "Use safe subprocess calls with shell=False"
                },
                {
                    "patterns": [r"sudo", r"su\s+", r"chmod\s+777", r"chown\s+"],
                    "severity": 0.9,
                    "description": "Privilege escalation commands",
                    "mitigation": "Remove privilege escalation, use appropriate permissions"
                },
                {
                    "patterns": [r"/etc/passwd", r"/etc/shadow", r"/etc/sudoers"],
                    "severity": 1.0,
                    "description": "Access to system authentication files",
                    "mitigation": "Remove access to system authentication files"
                }
            ],
            
            RiskCategory.NETWORK_OPERATIONS: [
                {
                    "patterns": [r"socket\.socket", r"urllib\.request", r"requests\.get",
                                r"http\.client", r"ftplib", r"smtplib"],
                    "severity": 0.4,
                    "description": "Network communication capabilities",
                    "mitigation": "Use network isolation or allowlist specific endpoints"
                },
                {
                    "patterns": [r"paramiko", r"fabric", r"ssh", r"telnet"],
                    "severity": 0.7,
                    "description": "Remote access protocols",
                    "mitigation": "Use restricted network access or VPN"
                },
                {
                    "patterns": [r"nc\s+-l", r"netcat", r"bind\s+shell", r"reverse\s+shell"],
                    "severity": 0.9,
                    "description": "Potential backdoor or shell access",
                    "mitigation": "Remove network shell capabilities"
                }
            ],
            
            RiskCategory.FILE_OPERATIONS: [
                {
                    "patterns": [r"open\s*\(.*['\"]w", r"\.write\(", r"shutil\.rmtree",
                                r"os\.remove", r"os\.unlink"],
                    "severity": 0.3,
                    "description": "File modification operations",
                    "mitigation": "Use read-only filesystem or limited write access"
                },
                {
                    "patterns": [r"rm\s+-rf", r"rmdir", r"del\s+/f", r"format\s+c:"],
                    "severity": 0.9,
                    "description": "Destructive file operations",
                    "mitigation": "Remove destructive file operations"
                },
                {
                    "patterns": [r"/var/log", r"/tmp", r"/home", r"/root"],
                    "severity": 0.6,
                    "description": "Access to system directories",
                    "mitigation": "Restrict access to project directory only"
                }
            ],
            
            RiskCategory.EXTERNAL_DEPENDENCIES: [
                {
                    "patterns": [r"pip\s+install", r"npm\s+install", r"curl.*\|.*sh",
                                r"wget.*\|.*bash"],
                    "severity": 0.5,
                    "description": "Dynamic dependency installation",
                    "mitigation": "Pre-approve and pin all dependencies"
                },
                {
                    "patterns": [r"github\.com/.*\.git", r"bitbucket\.org"],
                    "severity": 0.3,
                    "description": "External repository dependencies",
                    "mitigation": "Review external dependencies for security"
                }
            ],
            
            RiskCategory.PRIVILEGE_ESCALATION: [
                {
                    "patterns": [r"setuid", r"setgid", r"sudo\s+-u", r"su\s+-"],
                    "severity": 0.8,
                    "description": "User privilege manipulation",
                    "mitigation": "Run with minimal required privileges"
                },
                {
                    "patterns": [r"docker\s+run.*--privileged", r"--cap-add=SYS_ADMIN"],
                    "severity": 0.9,
                    "description": "Container privilege escalation",
                    "mitigation": "Use minimal container capabilities"
                }
            ],
            
            RiskCategory.DATA_SENSITIVITY: [
                {
                    "patterns": [r"password", r"secret", r"api_key", r"private_key",
                                r"token", r"credential"],
                    "severity": 0.6,
                    "description": "Potential sensitive data handling",
                    "mitigation": "Use secure secret management"
                },
                {
                    "patterns": [r"credit_card", r"ssn", r"social_security", r"passport"],
                    "severity": 0.8,
                    "description": "Personal identifiable information (PII)",
                    "mitigation": "Implement data protection measures"
                }
            ],
            
            RiskCategory.CRYPTO_OPERATIONS: [
                {
                    "patterns": [r"hashlib", r"cryptography", r"pycrypto", r"openssl"],
                    "severity": 0.3,
                    "description": "Cryptographic operations",
                    "mitigation": "Review cryptographic implementations"
                },
                {
                    "patterns": [r"random\.seed", r"urandom", r"os\.random"],
                    "severity": 0.4,
                    "description": "Random number generation",
                    "mitigation": "Use cryptographically secure random sources"
                }
            ],
            
            RiskCategory.CONTAINER_ESCAPE: [
                {
                    "patterns": [r"/proc/", r"/sys/", r"cgroup", r"namespace"],
                    "severity": 0.7,
                    "description": "Container system interface access",
                    "mitigation": "Restrict access to container system interfaces"
                },
                {
                    "patterns": [r"docker\.sock", r"/var/run/docker\.sock"],
                    "severity": 0.9,
                    "description": "Docker daemon access",
                    "mitigation": "Remove Docker daemon access"
                }
            ]
        }
    
    def _load_dependency_risks(self) -> Dict[str, float]:
        """Load known risky dependencies and their risk scores"""
        return {
            # High-risk packages
            "paramiko": 0.7,
            "fabric": 0.7,
            "pycrypto": 0.8,  # Deprecated, has vulnerabilities
            "pickle": 0.9,    # Unsafe deserialization
            "subprocess32": 0.6,
            "os": 0.5,
            "shutil": 0.4,
            
            # Medium-risk packages
            "requests": 0.3,
            "urllib3": 0.3,
            "selenium": 0.4,
            "scrapy": 0.4,
            
            # Crypto-related (need review)
            "cryptography": 0.3,
            "hashlib": 0.2,
            "hmac": 0.2,
            
            # Network-related
            "socket": 0.4,
            "ftplib": 0.5,
            "smtplib": 0.3,
            "telnetlib": 0.6,
            
            # System interaction
            "psutil": 0.4,
            "platform": 0.2,
            "getpass": 0.3
        }
    
    def analyze_project(self, project_content: str, requirements: Dict, 
                       file_paths: Optional[List[str]] = None) -> RiskAnalysisResult:
        """Perform comprehensive risk analysis on project"""
        
        # Create cache key
        content_hash = hashlib.sha256(project_content.encode()).hexdigest()
        cache_key = f"{content_hash}_{hash(str(requirements))}"
        
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
        
        factors = []
        total_score = 0.0
        
        # Analyze content patterns
        content_factors = self._analyze_content_patterns(project_content)
        factors.extend(content_factors)
        
        # Analyze dependencies
        dependency_factors = self._analyze_dependencies(requirements)
        factors.extend(dependency_factors)
        
        # Analyze project structure
        structure_factors = self._analyze_project_structure(requirements)
        factors.extend(structure_factors)
        
        # Calculate total risk score
        if factors:
            total_score = min(sum(f.severity for f in factors) / len(factors), 1.0)
        
        # Determine risk level
        risk_level = self._calculate_risk_level(total_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(factors, risk_level)
        
        # Determine required mitigations
        mitigations = self._determine_mitigations(factors)
        
        # Check if manual review is required
        manual_review = self._requires_manual_review(factors, total_score)
        
        # Determine isolation level
        isolation = self._determine_isolation_level(risk_level, factors)
        
        result = RiskAnalysisResult(
            overall_score=total_score,
            risk_level=risk_level,
            factors=factors,
            recommendations=recommendations,
            required_mitigations=mitigations,
            manual_review_required=manual_review,
            isolation_level=isolation,
            analysis_timestamp=datetime.now().isoformat()
        )
        
        # Cache result
        self.analysis_cache[cache_key] = result
        
        return result
    
    def _analyze_content_patterns(self, content: str) -> List[RiskFactor]:
        """Analyze content for risk patterns"""
        factors = []
        content_lower = content.lower()
        
        for category, pattern_groups in self.risk_patterns.items():
            for group in pattern_groups:
                for pattern in group["patterns"]:
                    matches = re.finditer(pattern, content_lower, re.IGNORECASE)
                    for match in matches:
                        factor = RiskFactor(
                            category=category,
                            description=group["description"],
                            severity=group["severity"],
                            pattern=pattern,
                            mitigation=group["mitigation"],
                            detected_in=f"content:{match.start()}-{match.end()}"
                        )
                        factors.append(factor)
        
        return factors
    
    def _analyze_dependencies(self, requirements: Dict) -> List[RiskFactor]:
        """Analyze project dependencies for risks"""
        factors = []
        
        dependencies = requirements.get("dependencies", [])
        if isinstance(dependencies, str):
            dependencies = [dependencies]
        
        for dep in dependencies:
            # Extract package name (handle versions like "requests>=2.0.0")
            package_name = re.split(r"[>=<!]", dep)[0].strip()
            
            if package_name in self.dependency_risks:
                severity = self.dependency_risks[package_name]
                factor = RiskFactor(
                    category=RiskCategory.EXTERNAL_DEPENDENCIES,
                    description=f"Potentially risky dependency: {package_name}",
                    severity=severity,
                    pattern=package_name,
                    mitigation=f"Review {package_name} usage and security implications",
                    detected_in=f"dependencies:{package_name}"
                )
                factors.append(factor)
        
        return factors
    
    def _analyze_project_structure(self, requirements: Dict) -> List[RiskFactor]:
        """Analyze project structure and configuration for risks"""
        factors = []
        
        # Check for dangerous features
        features = requirements.get("features", [])
        if isinstance(features, str):
            features = [features]
        
        risky_features = {
            "admin_panel": 0.6,
            "file_upload": 0.5,
            "user_authentication": 0.4,
            "database_access": 0.3,
            "api_endpoints": 0.3,
            "shell_access": 0.9,
            "system_monitoring": 0.7,
            "network_scanner": 0.8,
            "web_scraping": 0.4
        }
        
        for feature in features:
            feature_lower = feature.lower()
            for risky_feature, severity in risky_features.items():
                if risky_feature in feature_lower:
                    factor = RiskFactor(
                        category=RiskCategory.SYSTEM_ACCESS,
                        description=f"High-risk feature: {feature}",
                        severity=severity,
                        pattern=risky_feature,
                        mitigation=f"Implement security controls for {feature}",
                        detected_in=f"features:{feature}"
                    )
                    factors.append(factor)
        
        return factors
    
    def _calculate_risk_level(self, score: float) -> RiskLevel:
        """Convert numeric score to risk level"""
        if score < 0.2:
            return RiskLevel.MINIMAL
        elif score < 0.4:
            return RiskLevel.LOW
        elif score < 0.6:
            return RiskLevel.MEDIUM
        elif score < 0.8:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def _generate_recommendations(self, factors: List[RiskFactor], 
                                 risk_level: RiskLevel) -> List[str]:
        """Generate security recommendations based on analysis"""
        recommendations = []
        
        # Group factors by category
        categories = set(f.category for f in factors)
        
        base_recommendations = {
            RiskLevel.MINIMAL: [
                "Use standard Docker security practices",
                "Enable basic logging and monitoring",
                "Follow principle of least privilege"
            ],
            RiskLevel.LOW: [
                "Implement input validation",
                "Use read-only filesystem where possible",
                "Enable container security scanning"
            ],
            RiskLevel.MEDIUM: [
                "Implement network segmentation",
                "Use security policies (AppArmor/SELinux)",
                "Regular security audits",
                "Restrict filesystem access"
            ],
            RiskLevel.HIGH: [
                "Mandatory security review",
                "Implement strict network isolation",
                "Use security-hardened container images",
                "Continuous security monitoring"
            ],
            RiskLevel.CRITICAL: [
                "Manual security approval required",
                "Complete network isolation",
                "Enhanced audit logging",
                "Real-time threat detection"
            ]
        }
        
        recommendations.extend(base_recommendations.get(risk_level, []))
        
        # Add category-specific recommendations
        if RiskCategory.SYSTEM_ACCESS in categories:
            recommendations.append("Disable system command execution")
        
        if RiskCategory.NETWORK_OPERATIONS in categories:
            recommendations.append("Implement network allowlisting")
        
        if RiskCategory.FILE_OPERATIONS in categories:
            recommendations.append("Use read-only root filesystem")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _determine_mitigations(self, factors: List[RiskFactor]) -> List[str]:
        """Determine required security mitigations"""
        mitigations = set()
        
        for factor in factors:
            mitigations.add(factor.mitigation)
        
        return list(mitigations)
    
    def _requires_manual_review(self, factors: List[RiskFactor], score: float) -> bool:
        """Determine if manual security review is required"""
        
        # Always require manual review for critical risk
        if score >= 0.8:
            return True
        
        # Check for specific high-risk patterns
        critical_categories = {
            RiskCategory.PRIVILEGE_ESCALATION,
            RiskCategory.CONTAINER_ESCAPE
        }
        
        for factor in factors:
            if factor.category in critical_categories and factor.severity >= 0.8:
                return True
        
        # Check for combination of multiple medium-risk factors
        medium_risk_count = sum(1 for f in factors if f.severity >= 0.5)
        if medium_risk_count >= 3:
            return True
        
        return False
    
    def _determine_isolation_level(self, risk_level: RiskLevel, 
                                  factors: List[RiskFactor]) -> str:
        """Determine appropriate isolation level"""
        
        # Check for specific patterns requiring sandbox
        sandbox_categories = {
            RiskCategory.PRIVILEGE_ESCALATION,
            RiskCategory.CONTAINER_ESCAPE,
            RiskCategory.SYSTEM_ACCESS
        }
        
        for factor in factors:
            if factor.category in sandbox_categories and factor.severity >= 0.7:
                return "sandbox"
        
        # Map risk levels to isolation levels
        isolation_mapping = {
            RiskLevel.MINIMAL: "development",
            RiskLevel.LOW: "development", 
            RiskLevel.MEDIUM: "restricted",
            RiskLevel.HIGH: "sandbox",
            RiskLevel.CRITICAL: "sandbox"
        }
        
        return isolation_mapping[risk_level]
    
    def export_analysis(self, analysis: RiskAnalysisResult, format: str = "json") -> str:
        """Export analysis results in specified format"""
        
        if format == "json":
            # Convert to serializable format
            data = asdict(analysis)
            # Convert enums to strings
            data["risk_level"] = analysis.risk_level.value
            for i, factor in enumerate(data["factors"]):
                factor["category"] = analysis.factors[i].category.value
            
            return json.dumps(data, indent=2, ensure_ascii=False)
        
        elif format == "markdown":
            return self._export_markdown(analysis)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_markdown(self, analysis: RiskAnalysisResult) -> str:
        """Export analysis as markdown report"""
        
        report = f"""# Security Risk Analysis Report

## Overview
- **Overall Risk Score**: {analysis.overall_score:.2f}/1.0
- **Risk Level**: {analysis.risk_level.value.upper()}
- **Recommended Isolation**: {analysis.isolation_level}
- **Manual Review Required**: {'Yes' if analysis.manual_review_required else 'No'}
- **Analysis Date**: {analysis.analysis_timestamp}

## Risk Factors Detected

"""
        
        # Group factors by category
        factors_by_category = {}
        for factor in analysis.factors:
            category = factor.category.value
            if category not in factors_by_category:
                factors_by_category[category] = []
            factors_by_category[category].append(factor)
        
        for category, factors in factors_by_category.items():
            report += f"### {category.replace('_', ' ').title()}\n\n"
            for factor in factors:
                report += f"- **{factor.description}** (Severity: {factor.severity:.1f})\n"
                report += f"  - Pattern: `{factor.pattern}`\n"
                report += f"  - Location: {factor.detected_in}\n"
                report += f"  - Mitigation: {factor.mitigation}\n\n"
        
        report += "## Recommendations\n\n"
        for rec in analysis.recommendations:
            report += f"- {rec}\n"
        
        report += "\n## Required Mitigations\n\n"
        for mit in analysis.required_mitigations:
            report += f"- {mit}\n"
        
        return report

if __name__ == "__main__":
    # Example usage and testing
    analyzer = ProjectRiskAnalyzer()
    
    # Test with a sample project
    test_content = """
    import os
    import subprocess
    import requests
    
    def run_command(cmd):
        return os.system(cmd)
    
    def download_file(url):
        response = requests.get(url)
        return response.content
    """
    
    test_requirements = {
        "description": "Test project",
        "dependencies": ["requests", "paramiko"],
        "features": ["file_upload", "admin_panel"]
    }
    
    analysis = analyzer.analyze_project(test_content, test_requirements)
    
    print("=== Risk Analysis Results ===")
    print(f"Risk Level: {analysis.risk_level.value}")
    print(f"Score: {analysis.overall_score:.2f}")
    print(f"Isolation: {analysis.isolation_level}")
    print(f"Manual Review: {analysis.manual_review_required}")
    print(f"\nFactors: {len(analysis.factors)}")
    for factor in analysis.factors:
        print(f"  - {factor.description} ({factor.severity:.1f})")
    
    # Export as JSON
    json_report = analyzer.export_analysis(analysis, "json")
    print(f"\nJSON Export Length: {len(json_report)} characters")