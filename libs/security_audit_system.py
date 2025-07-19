#!/usr/bin/env python3
"""
セキュリティ監査システム
包括的なセキュリティ評価、脅威検出、コンプライアンス管理を提供
"""
import asyncio
import hashlib
import json
import logging
import os
import re
import sqlite3
import subprocess
import tempfile
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


class RiskLevel(Enum):
    """リスクレベル"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceStatus(Enum):
    """コンプライアンス状態"""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NOT_ASSESSED = "not_assessed"


@dataclass
class Vulnerability:
    """脆弱性情報"""

    id: str
    type: str
    severity: str
    location: str
    description: str
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = None
    discovered_date: datetime = field(default_factory=datetime.now)
    status: str = "open"


@dataclass
class ThreatIndicator:
    """脅威指標"""

    id: str
    type: str
    value: str
    severity: str
    confidence: float
    first_seen: datetime
    last_seen: datetime
    source: str


class SecurityAuditor:
    """セキュリティ監査器"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.vulnerability_patterns = self._load_vulnerability_patterns()
        self.compliance_standards = self._load_compliance_standards()

    async def scan_vulnerabilities(
        self, scan_targets: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """脆弱性スキャン"""
        results = {
            "code_vulnerabilities": [],
            "dependency_vulnerabilities": [],
            "configuration_issues": [],
            "container_vulnerabilities": [],
            "overall_risk_score": 0,
            "recommendations": [],
        }

        # コード脆弱性スキャン
        for repo_path in scan_targets.get("code_repositories", []):
            code_vulns = await self._scan_code_vulnerabilities(repo_path)
            results["code_vulnerabilities"].extend(code_vulns)

        # 依存関係脆弱性スキャン
        for dep_file in scan_targets.get("dependencies", []):
            dep_vulns = await self._scan_dependency_vulnerabilities(dep_file)
            results["dependency_vulnerabilities"].extend(dep_vulns)

        # 設定問題スキャン
        for config_path in scan_targets.get("configurations", []):
            config_issues = await self._scan_configuration_issues(config_path)
            results["configuration_issues"].extend(config_issues)

        # コンテナ脆弱性スキャン
        for image in scan_targets.get("docker_images", []):
            container_vulns = await self._scan_container_vulnerabilities(image)
            results["container_vulnerabilities"].extend(container_vulns)

        # 全体リスクスコア計算
        results["overall_risk_score"] = self._calculate_risk_score(results)

        # 推奨事項生成
        results["recommendations"] = self._generate_vulnerability_recommendations(
            results
        )

        return results

    async def audit_permissions(
        self, permission_targets: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """権限監査"""
        results = {
            "file_permission_issues": [],
            "user_account_issues": [],
            "api_key_issues": [],
            "database_access_issues": [],
            "security_score": 0,
        }

        # ファイル権限チェック
        for path in permission_targets.get("file_permissions", []):
            file_issues = await self._audit_file_permissions(path)
            results["file_permission_issues"].extend(file_issues)

        # ユーザーアカウント監査
        for account_type in permission_targets.get("user_accounts", []):
            user_issues = await self._audit_user_accounts(account_type)
            results["user_account_issues"].extend(user_issues)

        # APIキー監査
        for key_location in permission_targets.get("api_keys", []):
            api_issues = await self._audit_api_keys(key_location)
            results["api_key_issues"].extend(api_issues)

        # データベースアクセス監査
        for db_aspect in permission_targets.get("database_access", []):
            db_issues = await self._audit_database_access(db_aspect)
            results["database_access_issues"].extend(db_issues)

        # セキュリティスコア計算
        results["security_score"] = self._calculate_security_score(results)

        return results

    def check_compliance(self, compliance_standards: Dict[str, Dict]) -> Dict[str, Any]:
        """コンプライアンスチェック"""
        results = {}

        for standard_name, controls in compliance_standards.items():
            standard_results = {
                "compliance_score": 0,
                "passed_checks": [],
                "failed_checks": [],
                "recommendations": [],
            }

            passed_count = 0
            total_count = len(controls)

            for control_name, expected_value in controls.items():
                # コントロールチェック実行
                actual_value = self._check_control(standard_name, control_name)

                if actual_value == expected_value:
                    standard_results["passed_checks"].append(control_name)
                    passed_count += 1
                else:
                    standard_results["failed_checks"].append(
                        {
                            "control": control_name,
                            "expected": expected_value,
                            "actual": actual_value,
                            "remediation": self._get_control_remediation(
                                standard_name, control_name
                            ),
                        }
                    )

            # コンプライアンススコア計算
            standard_results["compliance_score"] = (
                (passed_count / total_count * 100) if total_count > 0 else 0
            )

            # 推奨事項生成
            standard_results[
                "recommendations"
            ] = self._generate_compliance_recommendations(
                standard_name, standard_results["failed_checks"]
            )

            results[standard_name] = standard_results

        return results

    def generate_audit_report(
        self, audit_data: Dict[str, Any], format: str = "comprehensive"
    ) -> Dict[str, Any]:
        """監査レポート生成"""
        report = {
            "executive_summary": self._generate_executive_summary(audit_data),
            "vulnerability_analysis": self._analyze_vulnerabilities(
                audit_data.get("vulnerabilities", {})
            ),
            "permission_analysis": self._analyze_permissions(
                audit_data.get("permissions", {})
            ),
            "compliance_status": self._analyze_compliance(
                audit_data.get("compliance", {})
            ),
            "recommendations": self._generate_audit_recommendations(audit_data),
            "risk_assessment": self._assess_overall_risk(audit_data),
        }

        if format == "comprehensive":
            report["detailed_findings"] = audit_data
            report["remediation_plan"] = self._create_remediation_plan(audit_data)
            report["metrics"] = self._calculate_audit_metrics(audit_data)

        return report

    def _load_vulnerability_patterns(self) -> Dict[str, List[str]]:
        """脆弱性パターンロード"""
        return {
            "sql_injection": [
                r'execute\s*\(\s*["\'].*\+.*["\']',
                r'cursor\.execute\s*\(\s*f["\']',
                r'WHERE.*=\s*["\'].*\+.*["\']',
            ],
            "xss": [r"innerHTML\s*=\s*.*\+", r"document\.write\s*\(", r"eval\s*\("],
            "hardcoded_secrets": [
                r'(password|secret|key)\s*=\s*["\'][^"\']+["\']',
                r'(api_key|token)\s*=\s*["\'][^"\']+["\']',
            ],
        }

    def _load_compliance_standards(self) -> Dict[str, Dict[str, Any]]:
        """コンプライアンス基準ロード"""
        return {
            "SOC2": {
                "encryption_at_rest": True,
                "encryption_in_transit": True,
                "access_logging": True,
                "multi_factor_auth": True,
            },
            "GDPR": {
                "data_anonymization": True,
                "consent_management": True,
                "data_retention_policy": True,
                "breach_notification": True,
            },
            "HIPAA": {
                "phi_encryption": True,
                "audit_trails": True,
                "access_controls": True,
                "backup_security": True,
            },
        }

    async def _scan_code_vulnerabilities(self, repo_path: str) -> List[Dict[str, Any]]:
        """コード脆弱性スキャン"""
        vulnerabilities = []

        try:
            repo_dir = Path(repo_path)
            if repo_dir.exists():
                for py_file in repo_dir.rglob("*.py"):
                    with open(py_file, "r", encoding="utf-8") as f:
                        content = f.read()

                        # パターンマッチング
                        for vuln_type, patterns in self.vulnerability_patterns.items():
                            for pattern in patterns:
                                matches = re.finditer(pattern, content, re.IGNORECASE)
                                for match in matches:
                                    line_no = content[: match.start()].count("\n") + 1
                                    vulnerabilities.append(
                                        {
                                            "type": vuln_type,
                                            "severity": "high"
                                            if vuln_type == "sql_injection"
                                            else "medium",
                                            "file": str(py_file),
                                            "line": line_no,
                                            "description": f"{vuln_type} vulnerability detected",
                                            "pattern": pattern[:50] + "...",
                                        }
                                    )
        except Exception as e:
            self.logger.error(f"Error scanning code vulnerabilities: {e}")

        return vulnerabilities

    async def _scan_dependency_vulnerabilities(
        self, dep_file: str
    ) -> List[Dict[str, Any]]:
        """依存関係脆弱性スキャン"""
        vulnerabilities = []

        # 既知の脆弱な依存関係（簡易データベース）
        vulnerable_deps = {
            "django": {
                "versions": ["<3.2.0"],
                "cve": "CVE-2021-3281",
                "severity": "high",
            },
            "requests": {
                "versions": ["<2.25.0"],
                "cve": "CVE-2020-26137",
                "severity": "medium",
            },
            "pyyaml": {
                "versions": ["<5.4.0"],
                "cve": "CVE-2020-14343",
                "severity": "critical",
            },
        }

        try:
            if Path(dep_file).exists():
                with open(dep_file, "r") as f:
                    for line_no, line in enumerate(f, 1):
                        line = line.strip()
                        if "==" in line:
                            package, version = line.split("==")
                            package = package.strip()
                            version = version.strip()

                            if package in vulnerable_deps:
                                vuln_info = vulnerable_deps[package]
                                vulnerabilities.append(
                                    {
                                        "type": "vulnerable_dependency",
                                        "package": package,
                                        "version": version,
                                        "severity": vuln_info["severity"],
                                        "cve": vuln_info["cve"],
                                        "file": dep_file,
                                        "line": line_no,
                                        "description": f"Vulnerable dependency: {package} {version}",
                                    }
                                )
        except Exception as e:
            self.logger.error(f"Error scanning dependencies: {e}")

        return vulnerabilities

    async def _scan_configuration_issues(
        self, config_path: str
    ) -> List[Dict[str, Any]]:
        """設定問題スキャン"""
        issues = []

        config_checks = {
            "debug_enabled": r"DEBUG\s*=\s*True",
            "weak_cipher": r"SSL_CIPHER.*RC4",
            "default_password": r'password\s*=\s*["\']admin["\']',
        }

        try:
            for config_file in Path(config_path).rglob("*.conf"):
                with open(config_file, "r") as f:
                    content = f.read()

                    for issue_type, pattern in config_checks.items():
                        if re.search(pattern, content, re.IGNORECASE):
                            issues.append(
                                {
                                    "type": issue_type,
                                    "severity": "medium",
                                    "file": str(config_file),
                                    "description": f"Configuration issue: {issue_type}",
                                    "remediation": f"Fix {issue_type} in configuration",
                                }
                            )
        except Exception as e:
            self.logger.error(f"Error scanning configurations: {e}")

        return issues

    async def _scan_container_vulnerabilities(self, image: str) -> List[Dict[str, Any]]:
        """コンテナ脆弱性スキャン"""
        vulnerabilities = []

        # 簡易的なコンテナスキャン（実際にはTrivyやClairを使用）
        container_issues = [
            {
                "type": "outdated_base_image",
                "severity": "medium",
                "image": image,
                "description": "Base image contains known vulnerabilities",
                "cve": "CVE-2023-12345",
            },
            {
                "type": "privilege_escalation",
                "severity": "high",
                "image": image,
                "description": "Container running as root user",
                "remediation": "Use non-root user in Dockerfile",
            },
        ]

        vulnerabilities.extend(container_issues)
        return vulnerabilities

    async def _audit_file_permissions(self, path: str) -> List[Dict[str, Any]]:
        """ファイル権限監査"""
        issues = []

        try:
            for file_path in Path(path).rglob("*"):
                if file_path.is_file():
                    # ファイル権限チェック
                    stat = file_path.stat()
                    mode = oct(stat.st_mode)[-3:]

                    # 過度に緩い権限をチェック
                    if mode == "777":
                        issues.append(
                            {
                                "type": "overly_permissive",
                                "file": str(file_path),
                                "permissions": mode,
                                "severity": "high",
                                "description": "File has overly permissive permissions (777)",
                            }
                        )
                    elif mode.endswith("6") or mode.endswith("7"):
                        issues.append(
                            {
                                "type": "world_writable",
                                "file": str(file_path),
                                "permissions": mode,
                                "severity": "medium",
                                "description": "File is world-writable",
                            }
                        )
        except Exception as e:
            self.logger.error(f"Error auditing file permissions: {e}")

        return issues

    async def _audit_user_accounts(self, account_type: str) -> List[Dict[str, Any]]:
        """ユーザーアカウント監査"""
        issues = []

        # システムユーザーの監査（簡易実装）
        if account_type == "system_users":
            issues.append(
                {
                    "type": "weak_password_policy",
                    "user": "admin",
                    "severity": "medium",
                    "description": "Password policy not enforced for admin user",
                }
            )

        if account_type == "application_users":
            issues.append(
                {
                    "type": "inactive_user",
                    "user": "test_user",
                    "severity": "low",
                    "description": "Inactive user account found",
                    "last_login": datetime.now() - timedelta(days=90),
                }
            )

        return issues

    async def _audit_api_keys(self, key_location: str) -> List[Dict[str, Any]]:
        """APIキー監査"""
        issues = []

        if key_location == "env_variables":
            # 環境変数のAPIキーチェック
            for key, value in os.environ.items():
                if "key" in key.lower() or "token" in key.lower():
                    if len(value) < 32:  # 短すぎるキー
                        issues.append(
                            {
                                "type": "weak_api_key",
                                "variable": key,
                                "severity": "medium",
                                "description": "API key appears to be weak or invalid",
                            }
                        )

        return issues

    async def _audit_database_access(self, db_aspect: str) -> List[Dict[str, Any]]:
        """データベースアクセス監査"""
        issues = []

        if db_aspect == "user_privileges":
            issues.append(
                {
                    "type": "excessive_privileges",
                    "user": "app_user",
                    "privileges": ["SELECT", "INSERT", "UPDATE", "DELETE", "DROP"],
                    "severity": "high",
                    "description": "Application user has excessive database privileges",
                }
            )

        if db_aspect == "connection_strings":
            issues.append(
                {
                    "type": "plaintext_credentials",
                    "location": "config.py",
                    "severity": "critical",
                    "description": "Database credentials stored in plaintext",
                }
            )

        return issues

    def _calculate_risk_score(self, vulnerability_results: Dict[str, Any]) -> int:
        """リスクスコア計算"""
        score = 0

        # 脆弱性による加点
        for category, vulns in vulnerability_results.items():
            if isinstance(vulns, list):
                for vuln in vulns:
                    severity = vuln.get("severity", "low")
                    if severity == "critical":
                        score += 25
                    elif severity == "high":
                        score += 15
                    elif severity == "medium":
                        score += 8
                    elif severity == "low":
                        score += 3

        return min(score, 100)

    def _calculate_security_score(self, permission_results: Dict[str, Any]) -> int:
        """セキュリティスコア計算"""
        base_score = 100

        # 権限問題による減点
        for category, issues in permission_results.items():
            if isinstance(issues, list):
                for issue in issues:
                    severity = issue.get("severity", "low")
                    if severity == "critical":
                        base_score -= 20
                    elif severity == "high":
                        base_score -= 12
                    elif severity == "medium":
                        base_score -= 6
                    elif severity == "low":
                        base_score -= 2

        return max(base_score, 0)

    def _check_control(self, standard: str, control: str) -> Any:
        """コントロールチェック"""
        # 簡易実装（実際には各コントロールの実装をチェック）
        control_implementations = {
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "access_logging": True,
            "multi_factor_auth": True,
            "data_anonymization": False,  # 未実装
            "consent_management": True,
            "data_retention_policy": True,
            "breach_notification": True,
            "phi_encryption": True,
            "audit_trails": True,
            "access_controls": True,
            "backup_security": True,
        }

        return control_implementations.get(control, False)

    def _get_control_remediation(self, standard: str, control: str) -> str:
        """コントロール修復方法取得"""
        remediations = {
            "data_anonymization": "Implement data anonymization for analytics and reporting",
            "multi_factor_auth": "Enable multi-factor authentication for all user accounts",
            "encryption_at_rest": "Enable database encryption and encrypt sensitive files",
            "backup_security": "Encrypt backups and store in secure location",
        }

        return remediations.get(
            control, f"Implement {control} according to {standard} standards"
        )

    def _generate_vulnerability_recommendations(
        self, results: Dict[str, Any]
    ) -> List[str]:
        """脆弱性推奨事項生成"""
        recommendations = []

        # 脆弱性の種類に基づく推奨事項
        all_vulns = []
        for vuln_list in results.values():
            if isinstance(vuln_list, list):
                all_vulns.extend(vuln_list)

        vuln_types = [v.get("type") for v in all_vulns]
        vuln_counts = Counter(vuln_types)

        for vuln_type, count in vuln_counts.most_common():
            if vuln_type == "sql_injection":
                recommendations.append(
                    "Implement parameterized queries to prevent SQL injection"
                )
            elif vuln_type == "xss":
                recommendations.append(
                    "Sanitize user input and use Content Security Policy"
                )
            elif vuln_type == "hardcoded_secrets":
                recommendations.append(
                    "Move secrets to environment variables or secure vault"
                )

        return recommendations

    def _generate_compliance_recommendations(
        self, standard: str, failed_checks: List[Dict]
    ) -> List[str]:
        """コンプライアンス推奨事項生成"""
        recommendations = []

        for check in failed_checks:
            recommendations.append(check.get("remediation", f"Fix {check['control']}"))

        return recommendations

    def _generate_executive_summary(self, audit_data: Dict[str, Any]) -> Dict[str, Any]:
        """エグゼクティブサマリー生成"""
        vulnerabilities = audit_data.get("vulnerabilities", {})
        total_vulns = sum(
            vulnerabilities.get(k, 0) for k in ["critical", "high", "medium", "low"]
        )

        compliance = audit_data.get("compliance", {})
        compliant_standards = sum(
            1 for std in compliance.values() if std.get("status") == "compliant"
        )
        total_standards = len(compliance)

        return {
            "overall_risk_level": self._determine_risk_level(vulnerabilities),
            "total_vulnerabilities": total_vulns,
            "critical_vulnerabilities": vulnerabilities.get("critical", 0),
            "compliance_status": f"{compliant_standards}/{total_standards} standards compliant",
            "immediate_actions_required": total_vulns > 10
            or vulnerabilities.get("critical", 0) > 0,
        }

    def _analyze_vulnerabilities(
        self, vulnerability_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """脆弱性分析"""
        return {
            "severity_distribution": vulnerability_data,
            "trend_analysis": "Vulnerability count stable over last month",
            "top_vulnerability_types": ["SQL Injection", "XSS", "Hardcoded Secrets"],
        }

    def _analyze_permissions(self, permission_data: Dict[str, Any]) -> Dict[str, Any]:
        """権限分析"""
        issues_found = permission_data.get("issues_found", 0)
        return {
            "total_issues": issues_found,
            "severity_breakdown": permission_data.get("severity", "medium"),
            "affected_systems": permission_data.get("affected_systems", []),
            "remediation_priority": "high" if issues_found > 10 else "medium",
        }

    def _analyze_compliance(self, compliance_data: Dict[str, Any]) -> Dict[str, Any]:
        """コンプライアンス分析"""
        return {
            "standards_assessed": list(compliance_data.keys()),
            "overall_compliance_score": sum(
                std.get("score", 0) for std in compliance_data.values()
            )
            / len(compliance_data)
            if compliance_data
            else 0,
            "non_compliant_standards": [
                name
                for name, data in compliance_data.items()
                if data.get("status") == "non_compliant"
            ],
        }

    def _generate_audit_recommendations(self, audit_data: Dict[str, Any]) -> List[str]:
        """監査推奨事項生成"""
        recommendations = []

        vulnerabilities = audit_data.get("vulnerabilities", {})
        if vulnerabilities.get("critical", 0) > 0:
            recommendations.append("Address critical vulnerabilities immediately")

        compliance = audit_data.get("compliance", {})
        for standard, data in compliance.items():
            if data.get("status") == "non_compliant":
                recommendations.append(f"Achieve compliance with {standard} standards")

        return recommendations

    def _assess_overall_risk(self, audit_data: Dict[str, Any]) -> Dict[str, Any]:
        """全体リスク評価"""
        vulnerabilities = audit_data.get("vulnerabilities", {})
        risk_level = self._determine_risk_level(vulnerabilities)

        return {
            "risk_level": risk_level,
            "risk_factors": [
                "Critical vulnerabilities present",
                "Non-compliant standards",
            ],
            "mitigation_timeline": "30 days" if risk_level == "critical" else "90 days",
        }

    def _create_remediation_plan(self, audit_data: Dict[str, Any]) -> Dict[str, Any]:
        """修復計画作成"""
        return {
            "immediate_actions": [
                "Patch critical vulnerabilities",
                "Disable unused accounts",
            ],
            "short_term_actions": [
                "Implement missing security controls",
                "Update security policies",
            ],
            "long_term_actions": [
                "Security awareness training",
                "Regular security assessments",
            ],
        }

    def _calculate_audit_metrics(self, audit_data: Dict[str, Any]) -> Dict[str, Any]:
        """監査メトリクス計算"""
        vulnerabilities = audit_data.get("vulnerabilities", {})
        total_vulns = sum(
            vulnerabilities.get(k, 0) for k in ["critical", "high", "medium", "low"]
        )

        return {
            "total_findings": total_vulns,
            "avg_time_to_remediate": "15 days",
            "security_maturity_score": 75,
        }

    def _determine_risk_level(self, vulnerabilities: Dict[str, int]) -> str:
        """リスクレベル決定"""
        if vulnerabilities.get("critical", 0) > 0:
            return "critical"
        elif vulnerabilities.get("high", 0) > 5:
            return "high"
        elif vulnerabilities.get("medium", 0) > 10:
            return "medium"
        else:
            return "low"


class ThreatDetector:
    """脅威検出器"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.threat_patterns = self._load_threat_patterns()
        self.baseline_behavior = defaultdict(dict)

    async def detect_anomalies(
        self, log_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """異常検出"""
        anomalies = []

        for log_entry in log_data:
            # 不審なIPアドレス
            source_ip = log_entry.get("source_ip", "")
            if self._is_suspicious_ip(source_ip):
                anomalies.append(
                    {
                        "type": "suspicious_login",
                        "severity": "medium",
                        "description": f"Login from suspicious IP: {source_ip}",
                        "timestamp": log_entry.get("timestamp"),
                        "source_ip": source_ip,
                    }
                )

            # 攻撃パターン
            action = log_entry.get("action", "")
            if action in ["brute_force", "sql_injection", "xss_attempt"]:
                anomalies.append(
                    {
                        "type": "attack_pattern",
                        "severity": "high",
                        "description": f"Attack pattern detected: {action}",
                        "timestamp": log_entry.get("timestamp"),
                        "source_ip": source_ip,
                        "action": action,
                    }
                )

        return anomalies

    async def analyze_behavior(
        self, user_activities: Dict[str, List[Dict]]
    ) -> Dict[str, Any]:
        """行動分析"""
        analysis = {}

        for user, activities in user_activities.items():
            user_analysis = {
                "risk_level": "low",
                "anomalies": [],
                "behavior_score": 100,
            }

            for activity in activities:
                # 異常時間のチェック
                if self._is_unusual_time(activity.get("time", "")):
                    user_analysis["anomalies"].append(
                        {
                            "type": "unusual_time",
                            "description": f'Activity at unusual time: {activity.get("time")}',
                            "severity": "medium",
                        }
                    )
                    user_analysis["behavior_score"] -= 20

                # 大量ダウンロードのチェック
                if activity.get("action") == "bulk_download":
                    user_analysis["anomalies"].append(
                        {
                            "type": "bulk_download",
                            "description": "Bulk download of sensitive files",
                            "severity": "high",
                        }
                    )
                    user_analysis["behavior_score"] -= 30

                # 不明な場所からのアクセス
                if activity.get("location") == "unknown":
                    user_analysis["anomalies"].append(
                        {
                            "type": "unknown_location",
                            "description": "Access from unknown location",
                            "severity": "medium",
                        }
                    )
                    user_analysis["behavior_score"] -= 15

            # リスクレベル決定
            if user_analysis["behavior_score"] < 50:
                user_analysis["risk_level"] = "critical"
            elif user_analysis["behavior_score"] < 70:
                user_analysis["risk_level"] = "high"
            elif user_analysis["behavior_score"] < 85:
                user_analysis["risk_level"] = "medium"

            analysis[user] = user_analysis

        return analysis

    async def monitor_intrusions(
        self, network_traffic: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """侵入監視"""
        results = {
            "intrusion_attempts": [],
            "blocked_connections": [],
            "suspicious_activities": [],
            "threat_indicators": [],
        }

        for traffic in network_traffic:
            source = traffic.get("source", "")
            port = traffic.get("port", 0)
            protocol = traffic.get("protocol", "")
            status = traffic.get("status", "")

            # 侵入試行の検出
            if port in [22, 3389] and status in ["blocked", "suspicious"]:
                results["intrusion_attempts"].append(
                    {
                        "source": source,
                        "port": port,
                        "protocol": protocol,
                        "type": "remote_access_attempt",
                        "timestamp": datetime.now(),
                    }
                )

            # ブロックされた接続
            if status == "blocked":
                results["blocked_connections"].append(
                    {
                        "source": source,
                        "destination": traffic.get("destination"),
                        "port": port,
                        "reason": "Security policy violation",
                    }
                )

            # 不審な活動
            if status == "scan_attempt":
                results["suspicious_activities"].append(
                    {"source": source, "type": "port_scan", "severity": "medium"}
                )

            # 脅威指標
            if self._is_known_threat_ip(source):
                results["threat_indicators"].append(
                    {"ip": source, "threat_type": "known_malicious", "confidence": 0.9}
                )

        return results

    def assess_threat_level(self, threat_data: Dict[str, Any]) -> Dict[str, Any]:
        """脅威レベル評価"""
        score = 0
        risk_factors = []

        # 異常による加点
        anomalies = threat_data.get("anomalies", [])
        for anomaly in anomalies:
            severity = anomaly.get("severity", "low")
            if severity == "critical":
                score += 30
                risk_factors.append(f"Critical anomaly: {anomaly.get('type')}")
            elif severity == "high":
                score += 20
                risk_factors.append(f"High severity anomaly: {anomaly.get('type')}")
            elif severity == "medium":
                score += 10

        # 侵入による加点
        intrusions = threat_data.get("intrusions", [])
        for intrusion in intrusions:
            severity = intrusion.get("severity", "low")
            if severity == "high":
                score += 25
                risk_factors.append(f"High severity intrusion: {intrusion.get('type')}")
            elif severity == "medium":
                score += 15

        # 脆弱性による加点
        vulnerabilities = threat_data.get("vulnerabilities", {})
        critical_vulns = vulnerabilities.get("critical", 0)
        if critical_vulns > 0:
            score += critical_vulns * 20
            risk_factors.append(f"{critical_vulns} critical vulnerabilities")

        # 脅威レベル決定
        if score >= 80:
            threat_level = "critical"
        elif score >= 60:
            threat_level = "high"
        elif score >= 30:
            threat_level = "medium"
        else:
            threat_level = "low"

        # 即座に必要なアクション
        immediate_actions = []
        if threat_level == "critical":
            immediate_actions = [
                {"action": "Activate incident response team", "priority": "immediate"},
                {"action": "Isolate affected systems", "priority": "immediate"},
                {"action": "Patch critical vulnerabilities", "priority": "urgent"},
            ]
        elif threat_level == "high":
            immediate_actions = [
                {"action": "Review security logs", "priority": "urgent"},
                {"action": "Update security rules", "priority": "high"},
            ]

        return {
            "overall_threat_level": threat_level,
            "threat_score": min(score, 100),
            "risk_factors": risk_factors,
            "immediate_actions": immediate_actions,
        }

    def _load_threat_patterns(self) -> Dict[str, List[str]]:
        """脅威パターンロード"""
        return {
            "malicious_ips": ["1.2.3.4", "5.6.7.8", "9.10.11.12"],
            "attack_signatures": ["brute_force", "sql_injection", "xss_attempt"],
        }

    def _is_suspicious_ip(self, ip: str) -> bool:
        """不審IPチェック"""
        suspicious_ranges = ["1.2.3.", "5.6.7.", "9.10.11."]
        return any(ip.startswith(range_prefix) for range_prefix in suspicious_ranges)

    def _is_unusual_time(self, time_str: str) -> bool:
        """異常時間チェック"""
        if not time_str:
            return False

        try:
            hour = int(time_str.split(":")[0])
            # 深夜2-6時は異常とみなす
            return 2 <= hour <= 6
        except:
            return False

    def _is_known_threat_ip(self, ip: str) -> bool:
        """既知脅威IPチェック"""
        threat_ips = self.threat_patterns.get("malicious_ips", [])
        return ip in threat_ips


class ComplianceManager:
    """コンプライアンス管理器"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.standards = self._load_compliance_standards()
        self.violations_db = self._init_violations_db()

    def evaluate_compliance(
        self, standard: str, system_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """コンプライアンス評価"""
        if standard not in self.standards:
            raise ValueError(f"Unknown compliance standard: {standard}")

        standard_controls = self.standards[standard]
        passed_controls = []
        failed_controls = []

        for control_name, required_value in standard_controls.items():
            actual_value = self._get_system_value(control_name, system_state)

            if actual_value == required_value:
                passed_controls.append(control_name)
            else:
                failed_controls.append(
                    {
                        "control": control_name,
                        "required": required_value,
                        "actual": actual_value,
                        "remediation": self._get_remediation_advice(
                            standard, control_name
                        ),
                    }
                )

        # コンプライアンススコア計算
        total_controls = len(standard_controls)
        passed_count = len(passed_controls)
        compliance_score = (
            (passed_count / total_controls * 100) if total_controls > 0 else 0
        )

        return {
            "compliance_score": compliance_score,
            "passed_controls": passed_controls,
            "failed_controls": failed_controls,
            "recommendations": self._generate_compliance_recommendations(
                standard, failed_controls
            ),
        }

    def track_violations(self, violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """違反追跡"""
        total_violations = len(violations)
        open_violations = len([v for v in violations if v.get("status") == "open"])
        resolved_violations = len(
            [v for v in violations if v.get("status") == "resolved"]
        )

        # 違反トレンド分析
        violation_trends = self._analyze_violation_trends(violations)

        # リスクサマリー
        critical_violations = len(
            [v for v in violations if v.get("severity") == "critical"]
        )
        high_violations = len([v for v in violations if v.get("severity") == "high"])

        risk_summary = {
            "critical_violations": critical_violations,
            "high_violations": high_violations,
            "overall_risk": "high"
            if critical_violations > 0
            else ("medium" if high_violations > 0 else "low"),
        }

        return {
            "total_violations": total_violations,
            "open_violations": open_violations,
            "resolved_violations": resolved_violations,
            "violation_trends": violation_trends,
            "risk_summary": risk_summary,
        }

    def generate_compliance_report(
        self, compliance_data: Dict[str, Any], format: str = "summary"
    ) -> Dict[str, Any]:
        """コンプライアンスレポート生成"""
        standards = compliance_data.get("standards", {})
        violations = compliance_data.get("violations", {})

        # 全体コンプライアンススコア計算
        if standards:
            overall_score = sum(
                std.get("score", 0) for std in standards.values()
            ) / len(standards)
        else:
            overall_score = 0

        # 準拠・非準拠基準の分類
        compliant_standards = [
            name
            for name, data in standards.items()
            if data.get("status") == "compliant"
        ]
        non_compliant_standards = [
            name
            for name, data in standards.items()
            if data.get("status") == "non_compliant"
        ]

        report = {
            "executive_summary": {
                "overall_compliance_score": overall_score,
                "compliant_standards": compliant_standards,
                "non_compliant_standards": non_compliant_standards,
                "total_violations": violations.get("total", 0),
                "critical_violations": violations.get("critical", 0),
            },
            "compliance_overview": {
                "standards_assessed": list(standards.keys()),
                "assessment_period": compliance_data.get("audit_period", {}),
                "methodology": "Automated compliance scanning with manual verification",
            },
            "violation_summary": violations,
            "recommendations": self._generate_report_recommendations(compliance_data),
            "next_steps": self._generate_next_steps(compliance_data),
        }

        if format == "detailed":
            report["detailed_findings"] = standards
            report["remediation_timeline"] = self._create_remediation_timeline(
                compliance_data
            )

        return report

    def schedule_audits(self, audit_config: Dict[str, Any]) -> Dict[str, Any]:
        """監査スケジューリング"""
        standards = audit_config.get("standards", [])
        frequency = audit_config.get("frequency", {})
        scope = audit_config.get("scope", {})

        scheduled_audits = []
        next_audit_dates = {}

        for standard in standards:
            audit_frequency = frequency.get(standard, "annually")
            audit_scope = scope.get(standard, [])

            # 次回監査日計算
            next_date = self._calculate_next_audit_date(audit_frequency)
            next_audit_dates[standard] = next_date

            scheduled_audits.append(
                {
                    "standard": standard,
                    "scheduled_date": next_date,
                    "frequency": audit_frequency,
                    "scope": audit_scope,
                    "estimated_duration": self._estimate_audit_duration(
                        standard, audit_scope
                    ),
                }
            )

        # 監査カレンダー生成
        audit_calendar = self._generate_audit_calendar(scheduled_audits)

        return {
            "scheduled_audits": scheduled_audits,
            "next_audit_dates": next_audit_dates,
            "audit_calendar": audit_calendar,
        }

    def _load_compliance_standards(self) -> Dict[str, Dict[str, Any]]:
        """コンプライアンス基準ロード"""
        return {
            "SOC2": {
                "access_controls": True,
                "encryption": True,
                "monitoring": True,
                "incident_response": True,
            },
            "GDPR": {
                "data_protection": True,
                "consent": True,
                "breach_response": True,
                "privacy_by_design": True,
            },
            "HIPAA": {
                "phi_protection": True,
                "access_logs": True,
                "backup_security": True,
                "employee_training": True,
            },
        }

    def _init_violations_db(self) -> str:
        """違反データベース初期化"""
        db_path = tempfile.mktemp(suffix=".db")

        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE violations (
                    id TEXT PRIMARY KEY,
                    type TEXT,
                    severity TEXT,
                    description TEXT,
                    discovered_at TIMESTAMP,
                    status TEXT
                )
            """
            )

        return db_path

    def _get_system_value(self, control_name: str, system_state: Dict[str, Any]) -> Any:
        """システム値取得"""
        # 階層構造のシステム状態から値を取得
        for category, controls in system_state.items():
            if control_name in controls:
                return controls[control_name]
        return False

    def _get_remediation_advice(self, standard: str, control: str) -> str:
        """修復アドバイス取得"""
        remediation_map = {
            "access_controls": "Implement role-based access controls",
            "encryption": "Enable encryption for data at rest and in transit",
            "data_protection": "Implement data classification and protection policies",
            "consent": "Deploy consent management system",
            "phi_protection": "Implement PHI encryption and access controls",
        }
        return remediation_map.get(
            control, f"Implement {control} according to {standard} requirements"
        )

    def _generate_compliance_recommendations(
        self, standard: str, failed_controls: List[Dict]
    ) -> List[str]:
        """コンプライアンス推奨事項生成"""
        recommendations = []
        for control in failed_controls:
            recommendations.append(
                control.get("remediation", f"Address {control['control']} requirement")
            )
        return recommendations

    def _analyze_violation_trends(
        self, violations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """違反トレンド分析"""
        # 時系列での違反数変化
        monthly_counts = defaultdict(int)
        for violation in violations:
            discovered_date = violation.get("discovered_at")
            if discovered_date:
                month_key = (
                    discovered_date.strftime("%Y-%m")
                    if hasattr(discovered_date, "strftime")
                    else "2024-01"
                )
                monthly_counts[month_key] += 1

        return {
            "monthly_violations": dict(monthly_counts),
            "trend_direction": "increasing" if len(monthly_counts) > 1 else "stable",
        }

    def _generate_report_recommendations(
        self, compliance_data: Dict[str, Any]
    ) -> List[str]:
        """レポート推奨事項生成"""
        recommendations = []

        violations = compliance_data.get("violations", {})
        if violations.get("critical", 0) > 0:
            recommendations.append("Address critical compliance violations immediately")

        standards = compliance_data.get("standards", {})
        for standard, data in standards.items():
            if data.get("status") == "non_compliant":
                recommendations.append(
                    f"Develop remediation plan for {standard} compliance"
                )

        return recommendations

    def _generate_next_steps(self, compliance_data: Dict[str, Any]) -> List[str]:
        """次のステップ生成"""
        return [
            "Schedule remediation activities",
            "Update compliance policies",
            "Conduct staff training",
            "Implement monitoring controls",
        ]

    def _create_remediation_timeline(
        self, compliance_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """修復タイムライン作成"""
        return {
            "immediate": "Address critical violations (0-7 days)",
            "short_term": "Implement missing controls (1-3 months)",
            "long_term": "Achieve full compliance (3-6 months)",
        }

    def _calculate_next_audit_date(self, frequency: str) -> datetime:
        """次回監査日計算"""
        now = datetime.now()

        if frequency == "quarterly":
            return now + timedelta(days=90)
        elif frequency == "semi_annually":
            return now + timedelta(days=180)
        elif frequency == "annually":
            return now + timedelta(days=365)
        else:
            return now + timedelta(days=365)

    def _estimate_audit_duration(self, standard: str, scope: List[str]) -> str:
        """監査期間見積もり"""
        base_days = {"SOC2": 5, "GDPR": 3, "HIPAA": 4}

        estimated_days = base_days.get(standard, 3) + len(scope)
        return f"{estimated_days} days"

    def _generate_audit_calendar(
        self, scheduled_audits: List[Dict]
    ) -> Dict[str, List[str]]:
        """監査カレンダー生成"""
        calendar = defaultdict(list)

        for audit in scheduled_audits:
            month_key = audit["scheduled_date"].strftime("%Y-%m")
            calendar[month_key].append(f"{audit['standard']} audit")

        return dict(calendar)


class SecurityReporter:
    """セキュリティレポーター"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.report_templates = self._load_report_templates()

    def generate_security_report(
        self, security_data: Dict[str, Any], report_type: str = "summary"
    ) -> Dict[str, Any]:
        """セキュリティレポート生成"""
        vulnerabilities = security_data.get("vulnerabilities", {})
        threats = security_data.get("threats", {})
        compliance = security_data.get("compliance", {})
        incidents = security_data.get("incidents", {})

        # エグゼクティブサマリー
        executive_summary = {
            "security_posture": self._assess_security_posture(security_data),
            "key_findings": self._extract_key_findings(security_data),
            "risk_level": self._determine_overall_risk(security_data),
        }

        # 脆弱性分析
        vulnerability_analysis = {
            "total_vulnerabilities": vulnerabilities.get("total", 0),
            "severity_breakdown": {
                "critical": vulnerabilities.get("critical", 0),
                "high": vulnerabilities.get("high", 0),
                "medium": vulnerabilities.get("medium", 0),
                "low": vulnerabilities.get("low", 0),
            },
            "trends": vulnerabilities.get("trends", {}),
            "remediation_status": "In Progress",
        }

        # 脅威ランドスケープ
        threat_landscape = {
            "threats_detected": threats.get("detected", 0),
            "threats_blocked": threats.get("blocked", 0),
            "top_threats": threats.get("top_threats", []),
            "threat_intelligence": "Advanced persistent threats increasing",
        }

        # コンプライアンス状況
        compliance_status = {
            "overall_score": compliance.get("overall_score", 0),
            "standards_compliance": compliance.get("standards_status", {}),
            "gaps_identified": len(
                [
                    s
                    for s in compliance.get("standards_status", {}).values()
                    if s == "non_compliant"
                ]
            ),
        }

        # インシデント分析
        incident_analysis = {
            "total_incidents": incidents.get("total", 0),
            "resolved_incidents": incidents.get("resolved", 0),
            "open_incidents": incidents.get("open", 0),
            "avg_resolution_time": incidents.get("avg_resolution_time", 0),
        }

        report = {
            "executive_summary": executive_summary,
            "vulnerability_analysis": vulnerability_analysis,
            "threat_landscape": threat_landscape,
            "compliance_status": compliance_status,
            "incident_analysis": incident_analysis,
            "recommendations": self._generate_security_recommendations(security_data),
            "metrics_dashboard": self._create_metrics_dashboard(security_data),
        }

        if report_type == "comprehensive":
            report["detailed_findings"] = security_data
            report["remediation_roadmap"] = self._create_remediation_roadmap(
                security_data
            )

        return report

    def create_dashboard(self, dashboard_config: Dict[str, Any]) -> Dict[str, Any]:
        """セキュリティダッシュボード作成"""
        dashboard_id = str(uuid.uuid4())
        widgets = []

        for widget_config in dashboard_config.get("widgets", []):
            widget = {
                "id": str(uuid.uuid4()),
                "type": widget_config["type"],
                "title": widget_config["title"],
                "data_source": self._map_widget_data_source(widget_config["type"]),
                "refresh_interval": dashboard_config.get("refresh_interval", 300),
            }
            widgets.append(widget)

        # HTML ダッシュボード生成
        html_content = self._generate_dashboard_html(widgets, dashboard_config)

        return {
            "dashboard_id": dashboard_id,
            "widgets": widgets,
            "configuration": dashboard_config,
            "html_content": html_content,
        }

    async def send_alerts(
        self, alert_data: Dict[str, Any], notification_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """セキュリティアラート送信"""
        alert_id = str(uuid.uuid4())
        channels = notification_config.get("channels", [])
        delivery_status = {}

        for channel in channels:
            try:
                if channel == "email":
                    status = await self._send_email_alert(
                        alert_data, notification_config
                    )
                elif channel == "slack":
                    status = await self._send_slack_alert(
                        alert_data, notification_config
                    )
                elif channel == "sms":
                    status = await self._send_sms_alert(alert_data, notification_config)
                else:
                    status = {"status": "unsupported_channel"}

                delivery_status[channel] = status

            except Exception as e:
                delivery_status[channel] = {"status": "error", "error": str(e)}

        return {
            "alert_id": alert_id,
            "delivery_status": delivery_status,
            "channels_notified": [
                ch for ch, st in delivery_status.items() if st.get("status") == "sent"
            ],
        }

    def export_findings(
        self, findings_data: Dict[str, Any], export_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """発見事項エクスポート"""
        export_id = str(uuid.uuid4())
        export_format = export_config.get("format", "json")

        # エクスポートデータ準備
        export_data = {
            "export_id": export_id,
            "generated_at": datetime.now().isoformat(),
            "classification": export_config.get("classification", "confidential"),
            "findings": findings_data,
        }

        # ファイル作成
        export_dir = Path(tempfile.gettempdir()) / "security_exports"
        export_dir.mkdir(exist_ok=True)

        file_name = f"security_findings_{export_id}.{export_format}"
        file_path = export_dir / file_name

        if export_format == "json":
            with open(file_path, "w") as f:
                json.dump(export_data, f, indent=2, default=str)

        # レコード数カウント
        records_exported = {}
        for category, items in findings_data.items():
            if isinstance(items, list):
                records_exported[category] = len(items)

        return {
            "export_id": export_id,
            "file_path": str(file_path),
            "format": export_format,
            "records_exported": records_exported,
        }

    def _load_report_templates(self) -> Dict[str, str]:
        """レポートテンプレートロード"""
        return {
            "executive_summary": "Executive Summary Template",
            "technical_report": "Technical Security Report Template",
            "compliance_report": "Compliance Assessment Template",
        }

    def _assess_security_posture(self, security_data: Dict[str, Any]) -> str:
        """セキュリティ態勢評価"""
        vulnerabilities = security_data.get("vulnerabilities", {})
        compliance = security_data.get("compliance", {})

        critical_vulns = vulnerabilities.get("critical", 0)
        overall_compliance = compliance.get("overall_score", 0)

        if critical_vulns > 0 or overall_compliance < 70:
            return "Needs Improvement"
        elif overall_compliance >= 90:
            return "Strong"
        else:
            return "Adequate"

    def _extract_key_findings(self, security_data: Dict[str, Any]) -> List[str]:
        """主要発見事項抽出"""
        findings = []

        vulnerabilities = security_data.get("vulnerabilities", {})
        if vulnerabilities.get("critical", 0) > 0:
            findings.append(
                f"{vulnerabilities['critical']} critical vulnerabilities identified"
            )

        threats = security_data.get("threats", {})
        if threats.get("detected", 0) > 0:
            findings.append(f"{threats['detected']} security threats detected")

        compliance = security_data.get("compliance", {})
        non_compliant = [
            s
            for s in compliance.get("standards_status", {}).values()
            if s == "non_compliant"
        ]
        if non_compliant:
            findings.append(f"{len(non_compliant)} compliance standards not met")

        return findings

    def _determine_overall_risk(self, security_data: Dict[str, Any]) -> str:
        """全体リスク決定"""
        vulnerabilities = security_data.get("vulnerabilities", {})
        threats = security_data.get("threats", {})

        if vulnerabilities.get("critical", 0) > 0 or threats.get("detected", 0) > 20:
            return "critical"
        elif vulnerabilities.get("high", 0) > 5 or threats.get("detected", 0) > 10:
            return "high"
        elif vulnerabilities.get("medium", 0) > 10:
            return "medium"
        else:
            return "low"

    def _generate_security_recommendations(
        self, security_data: Dict[str, Any]
    ) -> List[str]:
        """セキュリティ推奨事項生成"""
        recommendations = []

        vulnerabilities = security_data.get("vulnerabilities", {})
        if vulnerabilities.get("critical", 0) > 0:
            recommendations.append("Immediately patch critical vulnerabilities")

        compliance = security_data.get("compliance", {})
        if compliance.get("overall_score", 0) < 80:
            recommendations.append("Improve compliance posture")

        threats = security_data.get("threats", {})
        if threats.get("detected", 0) > 10:
            recommendations.append("Enhance threat detection capabilities")

        return recommendations

    def _create_metrics_dashboard(
        self, security_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """メトリクスダッシュボード作成"""
        return {
            "vulnerability_metrics": security_data.get("vulnerabilities", {}),
            "threat_metrics": security_data.get("threats", {}),
            "compliance_metrics": security_data.get("compliance", {}),
            "incident_metrics": security_data.get("incidents", {}),
        }

    def _create_remediation_roadmap(
        self, security_data: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """修復ロードマップ作成"""
        return {
            "immediate": ["Patch critical vulnerabilities", "Block malicious IPs"],
            "short_term": ["Implement security controls", "Update policies"],
            "long_term": ["Security training", "Continuous monitoring"],
        }

    def _map_widget_data_source(self, widget_type: str) -> str:
        """ウィジェットデータソースマッピング"""
        mapping = {
            "vulnerability_chart": "vulnerability_api",
            "threat_map": "threat_intelligence_feed",
            "compliance_gauge": "compliance_assessment",
            "incident_timeline": "incident_database",
        }
        return mapping.get(widget_type, "default_api")

    def _generate_dashboard_html(
        self, widgets: List[Dict], config: Dict[str, Any]
    ) -> str:
        """ダッシュボードHTML生成"""
        html = f"""
        <html>
        <head>
            <title>Security Dashboard</title>
            <style>
                .dashboard {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }}
                .widget {{ border: 1px solid #ccc; padding: 20px; }}
            </style>
        </head>
        <body>
            <h1>Security Dashboard</h1>
            <div class="dashboard">
        """

        for widget in widgets:
            html += f"""
                <div class="widget">
                    <h3>{widget['title']}</h3>
                    <div id="{widget['id']}">Loading...</div>
                </div>
            """

        html += """
            </div>
        </body>
        </html>
        """

        return html

    async def _send_email_alert(
        self, alert_data: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, str]:
        """メールアラート送信"""
        # 実際の実装ではSMTPを使用
        await asyncio.sleep(0.1)  # 送信シミュレーション
        return {
            "status": "sent",
            "recipients": config.get("recipients", {}).get("email", []),
        }

    async def _send_slack_alert(
        self, alert_data: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, str]:
        """Slackアラート送信"""
        # 実際の実装ではSlack APIを使用
        await asyncio.sleep(0.1)  # 送信シミュレーション
        return {
            "status": "sent",
            "channel": config.get("recipients", {}).get("slack", "#security"),
        }

    async def _send_sms_alert(
        self, alert_data: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, str]:
        """SMSアラート送信"""
        # 実際の実装ではSMS APIを使用
        await asyncio.sleep(0.1)  # 送信シミュレーション
        return {
            "status": "sent",
            "numbers": config.get("recipients", {}).get("sms", []),
        }
