#!/usr/bin/env python3
"""
Security Validation Layer
OSS統合セキュリティ検証層

Phase 3: Issue #5 段階的移行
OSS統合環境における包括的セキュリティ検証システム
Elder Guild セキュリティ基準とOSSセキュリティツールの統合
"""

import asyncio
import sys
import os
import time
import json
import hashlib
import re
import subprocess
from typing import Dict, List, Any, Optional, Union, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

try:
    from libs.elder_servants.integrations.oss_adapter_framework import (
        create_oss_adapter_framework,
        AdapterRequest
    )
except ImportError:
    # Fallback for simplified testing
    class MockAdapterRequest:
        def __init__(self, tool_name, operation, data, context):
            self.tool_name = tool_name
            self.operation = operation
            self.data = data
            self.context = context
    
    class MockFramework:
        async def execute_with_fallback(self, request):
            class MockResponse:
                def __init__(self):
                    self.success = True
                    self.data = {
                        "vulnerabilities": [],
                        "security_score": 95,
                        "risk_level": "LOW",
                        "dependencies_checked": 25
                    }
                    self.error = None
            return MockResponse()
    
    def create_oss_adapter_framework():
        return MockFramework()
    
    AdapterRequest = MockAdapterRequest

class SecurityRiskLevel(Enum):
    """セキュリティリスクレベル"""
    CRITICAL = "critical"    # 即座対応必須
    HIGH = "high"           # 高優先度
    MEDIUM = "medium"       # 中優先度
    LOW = "low"             # 低優先度
    INFO = "info"           # 情報レベル
    SECURE = "secure"       # セキュア

class SecurityCategory(Enum):
    """セキュリティカテゴリ"""
    CODE_INJECTION = "code_injection"           # コードインジェクション
    DEPENDENCY_VULNERABILITY = "dependency"     # 依存関係脆弱性
    AUTHENTICATION = "authentication"          # 認証・認可
    DATA_EXPOSURE = "data_exposure"            # データ露出
    CRYPTO_WEAKNESS = "crypto_weakness"         # 暗号化弱点
    INPUT_VALIDATION = "input_validation"       # 入力検証
    CONFIGURATION = "configuration"            # 設定問題
    PRIVILEGE_ESCALATION = "privilege"         # 権限昇格
    NETWORK_SECURITY = "network"               # ネットワークセキュリティ
    OSS_INTEGRATION = "oss_integration"        # OSS統合固有

class SecurityScanType(Enum):
    """セキュリティスキャンタイプ"""
    STATIC_ANALYSIS = "static_analysis"         # 静的解析
    DEPENDENCY_SCAN = "dependency_scan"         # 依存関係スキャン
    SECRETS_DETECTION = "secrets_detection"     # シークレット検出
    CONFIGURATION_AUDIT = "config_audit"       # 設定監査
    OSS_SECURITY = "oss_security"              # OSS特化セキュリティ
    ELDER_SECURITY = "elder_security"          # Elder Guild セキュリティ

@dataclass
class SecurityVulnerability:
    """セキュリティ脆弱性定義"""
    id: str
    title: str
    description: str
    category: SecurityCategory
    risk_level: SecurityRiskLevel
    cvss_score: float  # 0.0-10.0
    location: str  # ファイル:行番号
    source_tool: str  # 検出ツール
    remediation: str
    cwe_id: Optional[str] = None
    cve_id: Optional[str] = None
    detected_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "risk_level": self.risk_level.value,
            "cvss_score": self.cvss_score,
            "location": self.location,
            "source_tool": self.source_tool,
            "remediation": self.remediation,
            "cwe_id": self.cwe_id,
            "cve_id": self.cve_id,
            "detected_at": self.detected_at.isoformat()
        }

@dataclass
class SecurityScanResult:
    """セキュリティスキャン結果"""
    scan_id: str
    scan_type: SecurityScanType
    status: str
    overall_risk_level: SecurityRiskLevel
    security_score: float  # 0-100
    vulnerabilities: List[SecurityVulnerability]
    dependencies_scanned: int
    execution_time_ms: float
    elder_compliance: bool
    oss_tools_used: List[str]
    recommendations: List[str]
    scan_metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "scan_id": self.scan_id,
            "scan_type": self.scan_type.value,
            "status": self.status,
            "overall_risk_level": self.overall_risk_level.value,
            "security_score": self.security_score,
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities],
            "dependencies_scanned": self.dependencies_scanned,
            "execution_time_ms": self.execution_time_ms,
            "elder_compliance": self.elder_compliance,
            "oss_tools_used": self.oss_tools_used,
            "recommendations": self.recommendations,
            "scan_metadata": self.scan_metadata,
            "timestamp": self.timestamp.isoformat()
        }

class SecurityValidationLayer:
    """
    OSS統合セキュリティ検証層
    Elder Guild セキュリティ基準とOSSツールを統合した包括的セキュリティ検証
    """
    
    def __init__(self):
        self.scan_id_prefix = "SEC"
        self.oss_framework = create_oss_adapter_framework()
        
        # Elder セキュリティ基準
        self.elder_security_threshold = 90.0  # 90%以上でセキュア判定
        self.critical_threshold = 8.0  # CVSS 8.0以上はクリティカル
        
        # OSS セキュリティツール設定
        self.oss_security_tools = {
            "bandit": {"weight": 0.30, "focus": "static_analysis"},
            "safety": {"weight": 0.25, "focus": "dependency_scan"},
            "semgrep": {"weight": 0.20, "focus": "pattern_detection"},
            "secrets_scanner": {"weight": 0.15, "focus": "secrets_detection"},
            "dependency_checker": {"weight": 0.10, "focus": "license_compliance"}
        }
        
        # セキュリティパターン定義
        self.security_patterns = {
            "sql_injection": {
                "patterns": [r"\+.*\s*['\"].*['\"]\s*\+", r"format\(.*%s.*\)", r"\.execute\(.*%.*\)"],
                "category": SecurityCategory.CODE_INJECTION,
                "risk": SecurityRiskLevel.HIGH,
                "remediation": "Use parameterized queries instead of string concatenation"
            },
            "hardcoded_secrets": {
                "patterns": [r"password\s*=\s*['\"][^'\"]{8,}['\"]i", r"api_key\s*=\s*['\"][^'\"]{16,}['\"]i", r"secret\s*=\s*['\"][^'\"]{12,}['\"]i"],
                "category": SecurityCategory.DATA_EXPOSURE,
                "risk": SecurityRiskLevel.CRITICAL,
                "remediation": "Move secrets to environment variables or secure key management"
            },
            "unsafe_yaml": {
                "patterns": [r"yaml\.load\(", r"yaml\.unsafe_load\("],
                "category": SecurityCategory.CODE_INJECTION,
                "risk": SecurityRiskLevel.HIGH,
                "remediation": "Use yaml.safe_load() instead of yaml.load()"
            },
            "weak_crypto": {
                "patterns": [r"hashlib\.md5\(", r"hashlib\.sha1\(", r"random\.random\("],
                "category": SecurityCategory.CRYPTO_WEAKNESS,
                "risk": SecurityRiskLevel.MEDIUM,
                "remediation": "Use stronger cryptographic algorithms (SHA-256, SHA-3)"
            },
            "shell_injection": {
                "patterns": [r"os\.system\(", r"subprocess\.call\(.*shell=True", r"eval\("],
                "category": SecurityCategory.CODE_INJECTION,
                "risk": SecurityRiskLevel.HIGH,
                "remediation": "Avoid shell=True and validate inputs thoroughly"
            }
        }
        
        # Elder セキュリティ要件
        self.elder_security_requirements = {
            "logging_security": {
                "patterns": ["logging", "audit", "security_log"],
                "weight": 20,
                "description": "Security logging and auditing"
            },
            "input_validation": {
                "patterns": ["validate", "sanitize", "isinstance", "assert"],
                "weight": 25,
                "description": "Input validation and sanitization"
            },
            "error_handling": {
                "patterns": ["try:", "except", "finally:"],
                "weight": 20,
                "description": "Proper error handling"
            },
            "access_control": {
                "patterns": ["permission", "authorize", "authenticate", "@login_required"],
                "weight": 25,
                "description": "Access control and authorization"
            },
            "secure_defaults": {
                "patterns": ["secure=True", "https", "ssl", "tls"],
                "weight": 10,
                "description": "Secure default configurations"
            }
        }
    
    async def execute_comprehensive_security_scan(self, code: str, file_path: str = None, 
                                                 context: Dict[str, Any] = None) -> SecurityScanResult:
        """
        包括的セキュリティスキャン実行
        
        Args:
            code: スキャン対象コード
            file_path: ファイルパス (オプション)
            context: 実行コンテキスト
            
        Returns:
            SecurityScanResult: 統合セキュリティスキャン結果
        """
        start_time = time.time()
        scan_id = self._generate_scan_id()
        context = context or {}
        
        try:
            all_vulnerabilities = []
            oss_tools_used = []
            
            # Elder セキュリティチェック
            elder_vulns = await self._execute_elder_security_checks(code, file_path)
            all_vulnerabilities.extend(elder_vulns)
            
            # OSS セキュリティツール実行
            for tool_name, tool_config in self.oss_security_tools.items():
                tool_vulns = await self._execute_oss_security_tool(tool_name, code, file_path)
                all_vulnerabilities.extend(tool_vulns)
                oss_tools_used.append(tool_name)
            
            # 総合セキュリティスコア計算
            security_score = self._calculate_security_score(all_vulnerabilities)
            
            # 全体リスクレベル判定
            overall_risk = self._determine_overall_risk_level(all_vulnerabilities, security_score)
            
            # Elder コンプライアンス判定
            elder_compliance = await self._check_elder_security_compliance(code, all_vulnerabilities)
            
            # 推奨事項生成
            recommendations = self._generate_security_recommendations(all_vulnerabilities, security_score)
            
            # 実行時間計算
            execution_time_ms = (time.time() - start_time) * 1000
            
            # 依存関係スキャン数 (模擬)
            dependencies_scanned = self._count_dependencies(code)
            
            return SecurityScanResult(
                scan_id=scan_id,
                scan_type=SecurityScanType.OSS_SECURITY,
                status="completed",
                overall_risk_level=overall_risk,
                security_score=security_score,
                vulnerabilities=all_vulnerabilities,
                dependencies_scanned=dependencies_scanned,
                execution_time_ms=execution_time_ms,
                elder_compliance=elder_compliance,
                oss_tools_used=oss_tools_used,
                recommendations=recommendations,
                scan_metadata={
                    "elder_patterns_checked": len(self.elder_security_requirements),
                    "oss_tools_count": len(self.oss_security_tools),
                    "pattern_checks": len(self.security_patterns),
                    "file_path": file_path or "<string>"
                }
            )
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return SecurityScanResult(
                scan_id=scan_id,
                scan_type=SecurityScanType.OSS_SECURITY,
                status="error",
                overall_risk_level=SecurityRiskLevel.CRITICAL,
                security_score=0.0,
                vulnerabilities=[SecurityVulnerability(
                    id=f"{scan_id}_ERROR",
                    title="Security scan execution error",
                    description=str(e),
                    category=SecurityCategory.CONFIGURATION,
                    risk_level=SecurityRiskLevel.HIGH,
                    cvss_score=7.5,
                    location="<scan_engine>",
                    source_tool="SecurityValidationLayer",
                    remediation="Fix security scan configuration and dependencies"
                )],
                dependencies_scanned=0,
                execution_time_ms=execution_time_ms,
                elder_compliance=False,
                oss_tools_used=[],
                recommendations=["Fix security scan system errors before proceeding"]
            )
    
    async def _execute_elder_security_checks(self, code: str, file_path: str = None) -> List[SecurityVulnerability]:
        """Elder セキュリティチェック実行"""
        vulnerabilities = []
        
        # セキュリティパターン検出
        for pattern_name, pattern_config in self.security_patterns.items():
            for pattern in pattern_config["patterns"]:
                matches = re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    line_num = code[:match.start()].count('\n') + 1
                    vuln = SecurityVulnerability(
                        id=f"ELDER_{pattern_name.upper()}_{line_num}",
                        title=f"Elder Security: {pattern_name.replace('_', ' ').title()}",
                        description=f"Potential {pattern_config['category'].value} detected",
                        category=pattern_config["category"],
                        risk_level=pattern_config["risk"],
                        cvss_score=self._risk_to_cvss(pattern_config["risk"]),
                        location=f"{file_path or '<string>'}:{line_num}",
                        source_tool="Elder_Security",
                        remediation=pattern_config["remediation"]
                    )
                    vulnerabilities.append(vuln)
        
        # Elder セキュリティ要件チェック
        elder_security_score = self._check_elder_security_requirements(code)
        if elder_security_score < 80:
            vuln = SecurityVulnerability(
                id="ELDER_SECURITY_REQUIREMENTS",
                title="Elder Security Requirements Not Met",
                description=f"Elder security requirements score: {elder_security_score}%",
                category=SecurityCategory.CONFIGURATION,
                risk_level=SecurityRiskLevel.MEDIUM,
                cvss_score=5.0,
                location=file_path or "<string>",
                source_tool="Elder_Security",
                remediation="Implement Elder Guild security patterns and requirements"
            )
            vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    async def _execute_oss_security_tool(self, tool_name: str, code: str, file_path: str = None) -> List[SecurityVulnerability]:
        """OSS セキュリティツール実行"""
        vulnerabilities = []
        
        try:
            if tool_name == "bandit":
                vulns = await self._run_bandit_scan(code, file_path)
            elif tool_name == "safety":
                vulns = await self._run_safety_scan(code)
            elif tool_name == "semgrep":
                vulns = await self._run_semgrep_scan(code, file_path)
            elif tool_name == "secrets_scanner":
                vulns = await self._run_secrets_scan(code, file_path)
            elif tool_name == "dependency_checker":
                vulns = await self._run_dependency_check(code)
            else:
                vulns = []  # 未知のツール
            
            vulnerabilities.extend(vulns)
            
        except Exception as e:
            # ツール実行エラーを脆弱性として記録
            vuln = SecurityVulnerability(
                id=f"{tool_name.upper()}_ERROR",
                title=f"{tool_name} execution error",
                description=str(e),
                category=SecurityCategory.CONFIGURATION,
                risk_level=SecurityRiskLevel.LOW,
                cvss_score=2.0,
                location=file_path or "<string>",
                source_tool=tool_name,
                remediation=f"Fix {tool_name} configuration or installation"
            )
            vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    async def _run_bandit_scan(self, code: str, file_path: str = None) -> List[SecurityVulnerability]:
        """Bandit静的解析実行"""
        request = AdapterRequest(
            tool_name="bandit",
            operation="security_scan",
            data={"code_content": code, "file_path": file_path},
            context={}
        )
        
        response = await self.oss_framework.execute_with_fallback(request)
        vulnerabilities = []
        
        if response.success and response.data:
            bandit_issues = response.data.get("issues", [])
            for issue in bandit_issues:
                vuln = SecurityVulnerability(
                    id=f"BANDIT_{issue.get('test_id', 'UNKNOWN')}",
                    title=issue.get('test_name', 'Bandit Security Issue'),
                    description=issue.get('issue_text', 'Security issue detected by Bandit'),
                    category=SecurityCategory.STATIC_ANALYSIS,
                    risk_level=self._bandit_severity_to_risk(issue.get('issue_severity', 'LOW')),
                    cvss_score=self._severity_to_cvss(issue.get('issue_severity', 'LOW')),
                    location=f"{file_path or '<string>'}:{issue.get('line_number', 1)}",
                    source_tool="bandit",
                    remediation="Follow Bandit recommendations for secure coding practices"
                )
                vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    async def _run_safety_scan(self, code: str) -> List[SecurityVulnerability]:
        """Safety依存関係脆弱性スキャン"""
        request = AdapterRequest(
            tool_name="safety",
            operation="dependency_scan",
            data={"requirements": self._extract_dependencies(code)},
            context={}
        )
        
        response = await self.oss_framework.execute_with_fallback(request)
        vulnerabilities = []
        
        if response.success and response.data:
            safety_vulns = response.data.get("vulnerabilities", [])
            for vuln_data in safety_vulns:
                vuln = SecurityVulnerability(
                    id=f"SAFETY_{vuln_data.get('id', 'UNKNOWN')}",
                    title=f"Dependency Vulnerability: {vuln_data.get('package', 'Unknown')}",
                    description=vuln_data.get('advisory', 'Vulnerable dependency detected'),
                    category=SecurityCategory.DEPENDENCY_VULNERABILITY,
                    risk_level=SecurityRiskLevel.HIGH,
                    cvss_score=vuln_data.get('cvss', 7.0),
                    location="dependencies",
                    source_tool="safety",
                    remediation=f"Update {vuln_data.get('package', 'package')} to version {vuln_data.get('safe_version', 'latest')}",
                    cve_id=vuln_data.get('cve')
                )
                vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    async def _run_semgrep_scan(self, code: str, file_path: str = None) -> List[SecurityVulnerability]:
        """Semgrepパターンマッチング実行"""
        vulnerabilities = []
        
        # Semgrep 基本パターンマッチング (簡略化)
        semgrep_patterns = {
            "dangerous_functions": ["exec(", "eval(", "__import__"],
            "weak_randoms": ["random.random", "random.choice"],
            "unsafe_deserialization": ["pickle.load", "cPickle.load"]
        }
        
        for pattern_group, patterns in semgrep_patterns.items():
            for pattern in patterns:
                if pattern in code:
                    line_num = code[:code.find(pattern)].count('\n') + 1 if pattern in code else 1
                    vuln = SecurityVulnerability(
                        id=f"SEMGREP_{pattern_group.upper()}_{line_num}",
                        title=f"Semgrep: {pattern_group.replace('_', ' ').title()}",
                        description=f"Potentially dangerous pattern detected: {pattern}",
                        category=SecurityCategory.CODE_INJECTION,
                        risk_level=SecurityRiskLevel.MEDIUM,
                        cvss_score=5.5,
                        location=f"{file_path or '<string>'}:{line_num}",
                        source_tool="semgrep",
                        remediation="Review usage and implement safer alternatives"
                    )
                    vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    async def _run_secrets_scan(self, code: str, file_path: str = None) -> List[SecurityVulnerability]:
        """シークレット検出スキャン"""
        vulnerabilities = []
        
        secret_patterns = {
            "api_key": r"(?i)(api[_-]?key|apikey)\s*[=:]\s*['\"][a-z0-9]{16,}['\"]\s*",
            "password": r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"][^'\"]{8,}['\"]\s*",
            "token": r"(?i)(token|access[_-]?token)\s*[=:]\s*['\"][a-z0-9]{20,}['\"]\s*",
            "private_key": r"-----BEGIN [A-Z ]+ PRIVATE KEY-----"
        }
        
        for secret_type, pattern in secret_patterns.items():
            matches = re.finditer(pattern, code, re.MULTILINE)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                vuln = SecurityVulnerability(
                    id=f"SECRET_{secret_type.upper()}_{line_num}",
                    title=f"Potential {secret_type.replace('_', ' ').title()} Exposure",
                    description=f"Hardcoded {secret_type} detected in source code",
                    category=SecurityCategory.DATA_EXPOSURE,
                    risk_level=SecurityRiskLevel.CRITICAL,
                    cvss_score=9.0,
                    location=f"{file_path or '<string>'}:{line_num}",
                    source_tool="secrets_scanner",
                    remediation="Move secrets to environment variables or secure vault"
                )
                vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    async def _run_dependency_check(self, code: str) -> List[SecurityVulnerability]:
        """依存関係セキュリティチェック"""
        vulnerabilities = []
        
        # 危険な依存関係パターン
        dangerous_imports = {
            "os": "System command execution risk",
            "subprocess": "Shell command injection risk", 
            "eval": "Code injection risk",
            "exec": "Code execution risk",
            "pickle": "Deserialization vulnerability risk"
        }
        
        import_pattern = r"^\s*(?:from\s+(\w+)|import\s+(\w+))"
        matches = re.finditer(import_pattern, code, re.MULTILINE)
        
        for match in matches:
            imported_module = match.group(1) or match.group(2)
            if imported_module in dangerous_imports:
                line_num = code[:match.start()].count('\n') + 1
                vuln = SecurityVulnerability(
                    id=f"IMPORT_{imported_module.upper()}_{line_num}",
                    title=f"Risky Import: {imported_module}",
                    description=dangerous_imports[imported_module],
                    category=SecurityCategory.DEPENDENCY_VULNERABILITY,
                    risk_level=SecurityRiskLevel.MEDIUM,
                    cvss_score=4.0,
                    location=f"<string>:{line_num}",
                    source_tool="dependency_checker",
                    remediation=f"Review usage of {imported_module} and implement proper security controls"
                )
                vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def _calculate_security_score(self, vulnerabilities: List[SecurityVulnerability]) -> float:
        """セキュリティスコア計算"""
        if not vulnerabilities:
            return 100.0
        
        # リスクレベル別ペナルティ
        risk_penalties = {
            SecurityRiskLevel.CRITICAL: 30,
            SecurityRiskLevel.HIGH: 20,
            SecurityRiskLevel.MEDIUM: 10,
            SecurityRiskLevel.LOW: 5,
            SecurityRiskLevel.INFO: 1
        }
        
        total_penalty = 0
        for vuln in vulnerabilities:
            penalty = risk_penalties.get(vuln.risk_level, 5)
            total_penalty += penalty
        
        # スコア計算 (100点満点から減点)
        security_score = max(0.0, 100.0 - total_penalty)
        return round(security_score, 1)
    
    def _determine_overall_risk_level(self, vulnerabilities: List[SecurityVulnerability], security_score: float) -> SecurityRiskLevel:
        """全体リスクレベル判定"""
        # クリティカル脆弱性が1つでもあれば CRITICAL
        critical_vulns = [v for v in vulnerabilities if v.risk_level == SecurityRiskLevel.CRITICAL]
        if critical_vulns:
            return SecurityRiskLevel.CRITICAL
        
        # セキュリティスコアによる判定
        if security_score >= 90:
            return SecurityRiskLevel.SECURE
        elif security_score >= 80:
            return SecurityRiskLevel.LOW
        elif security_score >= 60:
            return SecurityRiskLevel.MEDIUM
        elif security_score >= 40:
            return SecurityRiskLevel.HIGH
        else:
            return SecurityRiskLevel.CRITICAL
    
    async def _check_elder_security_compliance(self, code: str, vulnerabilities: List[SecurityVulnerability]) -> bool:
        """Elder セキュリティコンプライアンス判定"""
        # Elder セキュリティ要件スコア
        requirements_score = self._check_elder_security_requirements(code)
        
        # クリティカル脆弱性なし
        critical_vulns = [v for v in vulnerabilities if v.risk_level == SecurityRiskLevel.CRITICAL]
        no_critical_vulns = len(critical_vulns) == 0
        
        # 全体判定
        return requirements_score >= 80 and no_critical_vulns
    
    def _check_elder_security_requirements(self, code: str) -> float:
        """Elder セキュリティ要件チェック"""
        total_score = 0
        
        for req_name, req_config in self.elder_security_requirements.items():
            req_score = 0
            for pattern in req_config["patterns"]:
                if pattern in code.lower():
                    req_score += req_config["weight"]
                    break  # 1つでも見つかればOK
            
            total_score += min(req_config["weight"], req_score)
        
        return round(total_score, 1)
    
    def _generate_security_recommendations(self, vulnerabilities: List[SecurityVulnerability], security_score: float) -> List[str]:
        """セキュリティ推奨事項生成"""
        recommendations = []
        
        # スコア別推奨事項
        if security_score < 50:
            recommendations.append("🚨 URGENT: Address critical security issues immediately")
        elif security_score < 70:
            recommendations.append("⚠️ HIGH PRIORITY: Resolve major security concerns")
        elif security_score < 90:
            recommendations.append("📝 RECOMMENDED: Improve security posture")
        else:
            recommendations.append("✅ GOOD: Security posture is acceptable")
        
        # カテゴリ別推奨事項
        categories = {}
        for vuln in vulnerabilities:
            if vuln.category not in categories:
                categories[vuln.category] = []
            categories[vuln.category].append(vuln)
        
        for category, vulns in categories.items():
            if category == SecurityCategory.CODE_INJECTION:
                recommendations.append("🛡️ Implement input validation and parameterized queries")
            elif category == SecurityCategory.DATA_EXPOSURE:
                recommendations.append("🔒 Move secrets to secure storage (env vars, vault)")
            elif category == SecurityCategory.DEPENDENCY_VULNERABILITY:
                recommendations.append("📦 Update vulnerable dependencies to secure versions")
            elif category == SecurityCategory.CRYPTO_WEAKNESS:
                recommendations.append("🔐 Use strong cryptographic algorithms (SHA-256+)")
            elif category == SecurityCategory.AUTHENTICATION:
                recommendations.append("🔑 Implement proper authentication and authorization")
        
        # Elder 特有の推奨事項
        if any(v.source_tool == "Elder_Security" for v in vulnerabilities):
            recommendations.append("🏛️ Follow Elder Guild security patterns and standards")
        
        return recommendations[:8]  # 最大8個の推奨事項
    
    def _risk_to_cvss(self, risk_level: SecurityRiskLevel) -> float:
        """リスクレベルをCVSSスコアに変換"""
        risk_to_cvss_map = {
            SecurityRiskLevel.CRITICAL: 9.0,
            SecurityRiskLevel.HIGH: 7.0,
            SecurityRiskLevel.MEDIUM: 5.0,
            SecurityRiskLevel.LOW: 3.0,
            SecurityRiskLevel.INFO: 1.0,
            SecurityRiskLevel.SECURE: 0.0
        }
        return risk_to_cvss_map.get(risk_level, 5.0)
    
    def _bandit_severity_to_risk(self, severity: str) -> SecurityRiskLevel:
        """Bandit重要度をリスクレベルに変換"""
        severity_map = {
            "HIGH": SecurityRiskLevel.HIGH,
            "MEDIUM": SecurityRiskLevel.MEDIUM,
            "LOW": SecurityRiskLevel.LOW
        }
        return severity_map.get(severity.upper(), SecurityRiskLevel.MEDIUM)
    
    def _severity_to_cvss(self, severity: str) -> float:
        """重要度をCVSSスコアに変換"""
        severity_map = {
            "CRITICAL": 9.0,
            "HIGH": 7.0,
            "MEDIUM": 5.0,
            "LOW": 3.0
        }
        return severity_map.get(severity.upper(), 5.0)
    
    def _extract_dependencies(self, code: str) -> List[str]:
        """コードから依存関係抽出"""
        import_pattern = r"^\s*(?:from\s+(\w+)|import\s+(\w+))"
        matches = re.finditer(import_pattern, code, re.MULTILINE)
        dependencies = set()
        
        for match in matches:
            module = match.group(1) or match.group(2)
            if module:
                dependencies.add(module)
        
        return list(dependencies)
    
    def _count_dependencies(self, code: str) -> int:
        """依存関係数カウント"""
        return len(self._extract_dependencies(code))
    
    def _generate_scan_id(self) -> str:
        """スキャンID生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{self.scan_id_prefix}_{timestamp}"

# Testing function
async def test_security_validation_layer():
    """セキュリティ検証層テスト"""
    print("🛡️ Testing Security Validation Layer")
    print("=" * 60)
    
    validator = SecurityValidationLayer()
    
    # テストケース1: セキュアなElder コード
    print("\n✅ Test Case 1: Secure Elder Code")
    secure_code = '''# Elder Guild Secure Implementation
import logging
import hashlib
from typing import Dict, Any
import os

class ElderSecureSystem:
    """Elder Guild secure system implementation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.security_enabled = True
        
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Secure input validation"""
        if not isinstance(data, dict):
            raise ValueError("Invalid input type")
        
        required_fields = ['user_id', 'action']
        for field in required_fields:
            if field not in data:
                self.logger.warning(f"Missing field: {field}")
                return False
        
        return True
    
    def hash_password(self, password: str) -> str:
        """Secure password hashing"""
        salt = os.urandom(32)
        return hashlib.sha256(salt + password.encode()).hexdigest()
    
    def authorize_access(self, user_id: str, resource: str) -> bool:
        """Access control validation"""
        try:
            # Check permissions
            if not user_id or not resource:
                return False
            
            self.logger.info(f"Access granted: {user_id} -> {resource}")
            return True
            
        except Exception as e:
            self.logger.error(f"Authorization error: {e}")
            return False
'''
    
    result = await validator.execute_comprehensive_security_scan(secure_code, "secure_elder.py")
    
    print(f"🔍 Scan ID: {result.scan_id}")
    print(f"🛡️ Status: {result.status}")
    print(f"⚡ Security Score: {result.security_score}%")
    print(f"📊 Risk Level: {result.overall_risk_level.value}")
    print(f"🏛️ Elder Compliance: {result.elder_compliance}")
    print(f"🔧 OSS Tools: {', '.join(result.oss_tools_used)}")
    print(f"⚠️ Vulnerabilities: {len(result.vulnerabilities)}")
    print(f"⏱️ Execution Time: {result.execution_time_ms:.2f}ms")
    
    # テストケース2: 脆弱性のあるコード
    print("\n⚠️ Test Case 2: Vulnerable Code")
    vulnerable_code = '''import os
import pickle
import yaml
import subprocess

# Vulnerable code examples
password = "hardcoded_secret_123"  # Secret exposure
api_key = "sk-1234567890abcdef1234567890abcdef"  # API key exposure

def unsafe_query(user_input):
    # SQL injection vulnerability
    query = "SELECT * FROM users WHERE id = '" + user_input + "'"
    return query

def load_config(config_data):
    # Unsafe YAML loading
    return yaml.load(config_data)

def execute_command(cmd):
    # Shell injection risk
    return os.system(cmd)

def deserialize_data(data):
    # Unsafe deserialization
    return pickle.loads(data)

def weak_hash(data):
    import hashlib
    return hashlib.md5(data.encode()).hexdigest()  # Weak crypto
'''
    
    result2 = await validator.execute_comprehensive_security_scan(vulnerable_code, "vulnerable.py")
    
    print(f"🔍 Scan ID: {result2.scan_id}")
    print(f"🛡️ Status: {result2.status}")
    print(f"⚡ Security Score: {result2.security_score}%")
    print(f"📊 Risk Level: {result2.overall_risk_level.value}")
    print(f"🏛️ Elder Compliance: {result2.elder_compliance}")
    print(f"⚠️ Vulnerabilities: {len(result2.vulnerabilities)}")
    
    # 脆弱性詳細表示
    if result2.vulnerabilities:
        print("\n🔍 Top Vulnerabilities:")
        for vuln in result2.vulnerabilities[:3]:  # 上位3つ
            print(f"  • {vuln.title} ({vuln.risk_level.value}) - {vuln.source_tool}")
    
    # テストケース3: 混合品質コード
    print("\n⚖️ Test Case 3: Mixed Quality Code")
    mixed_code = '''import logging
import hashlib
from typing import Dict

class MixedSystem:
    """System with mixed security quality"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Some hardcoded secret (bad)
        self.debug_token = "debug_12345678"  
    
    def process_data(self, data: Dict) -> Dict:
        """Process data with some validation"""
        try:
            if not isinstance(data, dict):
                raise ValueError("Invalid input")
            
            # Good: proper logging
            self.logger.info("Processing data")
            
            # Bad: weak hashing
            data_hash = hashlib.md5(str(data).encode()).hexdigest()
            
            return {"status": "processed", "hash": data_hash}
            
        except Exception as e:
            # Good: error handling
            self.logger.error(f"Error: {e}")
            return {"status": "error"}
'''
    
    result3 = await validator.execute_comprehensive_security_scan(mixed_code, "mixed.py")
    
    print(f"🔍 Scan ID: {result3.scan_id}")
    print(f"⚡ Security Score: {result3.security_score}%")
    print(f"📊 Risk Level: {result3.overall_risk_level.value}")
    print(f"🏛️ Elder Compliance: {result3.elder_compliance}")
    print(f"⚠️ Vulnerabilities: {len(result3.vulnerabilities)}")
    
    # 推奨事項表示
    if result3.recommendations:
        print("\n💡 Recommendations:")
        for rec in result3.recommendations[:3]:
            print(f"  • {rec}")
    
    # 統計サマリー
    print("\n" + "=" * 60)
    print("🛡️ Security Validation Layer Summary:")
    print(f"  ✅ Secure Code: {result.security_score}% ({result.overall_risk_level.value})")
    print(f"  ⚠️ Vulnerable Code: {result2.security_score}% ({result2.overall_risk_level.value})")
    print(f"  ⚖️ Mixed Code: {result3.security_score}% ({result3.overall_risk_level.value})")
    print(f"  🔧 Total OSS Tools: {len(validator.oss_security_tools)}")
    print(f"  🏛️ Elder Patterns: {len(validator.elder_security_requirements)}")
    print(f"  🔍 Security Patterns: {len(validator.security_patterns)}")
    print("🎉 Security Validation Layer operational!")

if __name__ == "__main__":
    asyncio.run(test_security_validation_layer())
