"""
SecurityGuard (D06) - セキュリティ守護者サーバント
ドワーフ工房のセキュリティ専門家

EldersLegacy準拠実装 - Issue #70
"""

import ast
import asyncio
import base64
import hashlib
import logging
import os
import re
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Union

from elders_guild.elder_tree.elder_servants.base.elder_servant import (
    ServantCapability,
    TaskResult,
    TaskStatus,
)
from elders_guild.elder_tree.elder_servants.base.specialized_servants import DwarfServant

class SecurityGuard(DwarfServant[Dict[str, Any], Dict[str, Any]]):
    """
    D06: SecurityGuard - セキュリティ守護者サーバント
    コードとシステムのセキュリティ強化・脆弱性対策のスペシャリスト

    EldersLegacy準拠: Iron Will品質基準に基づく
    徹底的なセキュリティ監査と自動化された防御を提供
    """

    def __init__(self):
        """初期化メソッド"""
        capabilities = [
            ServantCapability(
                "security_audit",
                "包括的セキュリティ監査",
                ["source_code", "config_files"],
                ["security_report"],
                complexity=9,
            ),
            ServantCapability(
                "vulnerability_assessment",
                "脆弱性評価",
                ["application_code", "dependencies"],
                ["vulnerability_assessment"],
                complexity=8,
            ),
            ServantCapability(
                "secure_code_generation",
                "セキュアコード生成",
                ["functionality_spec", "security_requirements"],
                ["secure_code"],
                complexity=7,
            ),
            ServantCapability(
                "encryption_implementation",
                "暗号化実装",
                ["data_spec", "encryption_requirements"],
                ["encryption_code"],
                complexity=8,
            ),
            ServantCapability(
                "access_control_design",
                "アクセス制御設計",
                ["user_roles", "resource_permissions"],
                ["access_control_system"],
                complexity=7,
            ),
            ServantCapability(
                "security_testing",
                "セキュリティテスト生成",
                ["application_code", "attack_vectors"],
                ["security_tests"],
                complexity=8,
            ),
        ]

        super().__init__(
            servant_id="D06",
            servant_name="SecurityGuard",
            specialization="セキュリティ強化",
            capabilities=capabilities,
        )

        # SecurityGuard固有の設定
        self.security_standards = {
            "owasp_top_10": self._load_owasp_standards(),
            "cwe_top_25": self._load_cwe_standards(),
            "nist_guidelines": self._load_nist_guidelines(),
        }

        # セキュリティパターン
        self.secure_patterns = self._initialize_secure_patterns()
        self.vulnerability_db = self._initialize_vulnerability_database()

        # セキュリティツール
        self.crypto_manager = CryptographyManager()
        self.access_controller = AccessController()
        self.threat_analyzer = ThreatAnalyzer()
        self.secure_coder = SecureCoder()

        # セキュリティ設定
        self.security_config = {
            "min_password_length": 12,
            "session_timeout": 1800,  # 30分

            "encryption_algorithm": "AES-256-GCM",
            "hash_algorithm": "SHA-256",
        }

        self.logger.info("SecurityGuard ready to protect and secure")

    def get_specialized_capabilities(self) -> List[ServantCapability]:
        """専門能力の取得"""
        return [
            ServantCapability(
                "penetration_testing",
                "ペネトレーションテスト支援",
                ["target_application", "test_scenarios"],
                ["pentest_report"],
                complexity=9,
            ),
            ServantCapability(
                "compliance_check",
                "コンプライアンスチェック",
                ["source_code", "compliance_standard"],
                ["compliance_report"],
                complexity=6,
            ),
            ServantCapability(
                "security_monitoring",
                "セキュリティ監視システム",
                ["application_logs", "monitoring_rules"],
                ["monitoring_system"],
                complexity=7,
            ),
        ]

    async def execute_task(self, task: Dict[str, Any]) -> TaskResult:
        """タスク実行"""
        start_time = datetime.now()
        task_id = task.get("task_id", "unknown")
        task_type = task.get("task_type", "")

        try:
            self.logger.info(f"Securing system for task {task_id}: {task_type}")

            result_data = {}
            payload = task.get("payload", {})

            if task_type == "security_audit":
                result_data = await self._security_audit(
                    payload.get("source_code", ""), payload.get("config_files", [])
                )
            elif task_type == "vulnerability_assessment":
                result_data = await self._vulnerability_assessment(
                    payload.get("application_code", ""), payload.get("dependencies", [])
                )
            elif task_type == "secure_code_generation":
                result_data = await self._secure_code_generation(
                    payload.get("functionality_spec", {}),
                    payload.get("security_requirements", []),
                )
            elif task_type == "encryption_implementation":
                result_data = await self._encryption_implementation(
                    payload.get("data_spec", {}),
                    payload.get("encryption_requirements", {}),
                )
            elif task_type == "access_control_design":
                result_data = await self._access_control_design(
                    payload.get("user_roles", []),
                    payload.get("resource_permissions", {}),
                )
            elif task_type == "security_testing":
                result_data = await self._security_testing(
                    payload.get("application_code", ""),
                    payload.get("attack_vectors", []),
                )
            elif task_type == "penetration_testing":
                result_data = await self._penetration_testing(
                    payload.get("target_application", {}),
                    payload.get("test_scenarios", []),
                )
            elif task_type == "compliance_check":
                result_data = await self._compliance_check(
                    payload.get("source_code", ""),
                    payload.get("compliance_standard", ""),
                )
            elif task_type == "security_monitoring":
                result_data = await self._security_monitoring(
                    payload.get("application_logs", []),
                    payload.get("monitoring_rules", {}),
                )
            else:
                raise ValueError(f"Unknown task type: {task_type}")

            # SecurityGuard品質検証
            quality_score = await self._validate_security_quality(result_data)

            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            return TaskResult(
                task_id=task_id,
                servant_id=self.servant_id,
                status=TaskStatus.COMPLETED,
                result_data=result_data,
                execution_time_ms=execution_time,
                quality_score=quality_score,
            )

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Security task failed for {task_id}: {str(e)}")
            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            return TaskResult(
                task_id=task_id,
                servant_id=self.servant_id,
                status=TaskStatus.FAILED,
                error_message=str(e),
                execution_time_ms=execution_time,
                quality_score=0.0,
            )

    async def craft_artifact(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        """SecurityGuard専用の製作メソッド"""
        security_type = specification.get("type", "security_audit")

        if security_type == "comprehensive_security":
            # 包括的セキュリティ強化
            source_code = specification.get("source_code", "")

            audit_result = await self._security_audit(source_code, [])
            vuln_result = await self._vulnerability_assessment(source_code, [])
            secure_code = await self._secure_code_generation(
                {"original_code": source_code},
                ["input_validation", "output_encoding", "secure_storage"],
            )

            return {
                "comprehensive_security": {
                    "audit_report": audit_result,
                    "vulnerability_assessment": vuln_result,
                    "secured_code": secure_code,
                },
                "security_score": self._calculate_overall_security_score(
                    [audit_result, vuln_result]
                ),
            }
        else:
            return await self._security_audit(specification.get("source_code", ""), [])

    async def _security_audit(
        self, source_code: str, config_files: List[str]
    ) -> Dict[str, Any]:
        """包括的セキュリティ監査"""
        if not source_code:
            raise ValueError("Source code is required for security audit")

        try:
            # セキュリティ問題の検出
            security_issues = []

            # OWASP Top 10チェック
            owasp_issues = await self._check_owasp_top_10(source_code)
            security_issues.extend(owasp_issues)

            # CWE脆弱性チェック
            cwe_issues = await self._check_cwe_vulnerabilities(source_code)
            security_issues.extend(cwe_issues)

            # 設定ファイルセキュリティチェック
            if config_files:
                config_issues = await self._check_configuration_security(config_files)
                security_issues.extend(config_issues)

            # セキュリティベストプラクティスチェック
            best_practice_issues = await self._check_security_best_practices(
                source_code
            )
            security_issues.extend(best_practice_issues)

            # リスク評価
            risk_assessment = self._assess_security_risks(security_issues)

            # 修復計画
            remediation_plan = self._create_security_remediation_plan(security_issues)

            return {
                "security_report": {
                    "total_issues": len(security_issues),
                    "critical_issues": len(
                        [i for i in security_issues if i.get("severity") == "critical"]
                    ),
                    "high_issues": len(
                        [i for i in security_issues if i.get("severity") == "high"]
                    ),
                    "medium_issues": len(
                        [i for i in security_issues if i.get("severity") == "medium"]
                    ),
                    "low_issues": len(
                        [i for i in security_issues if i.get("severity") == "low"]
                    ),
                    "risk_assessment": risk_assessment,
                },
                "security_issues": security_issues,
                "remediation_plan": remediation_plan,
                "security_score": self._calculate_security_score(security_issues),
                "compliance_status": self._check_compliance_status(security_issues),
            }

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Security audit failed: {e}")
            return {
                "security_report": {"error": str(e)},
                "security_issues": [],
                "security_score": 0.0,
            }

    async def _vulnerability_assessment(
        self, application_code: str, dependencies: List[str]
    ) -> Dict[str, Any]:
        """脆弱性評価"""
        if not application_code:
            raise ValueError(
                "Application code is required for vulnerability assessment"
            )

        try:
            vulnerabilities = []

            # コード脆弱性スキャン
            code_vulns = await self._scan_code_vulnerabilities(application_code)
            vulnerabilities.extend(code_vulns)

            # 依存関係脆弱性チェック
            if dependencies:
                dep_vulns = await self._scan_dependency_vulnerabilities(dependencies)
                vulnerabilities.extend(dep_vulns)

            # 脆弱性の優先順位付け
            prioritized_vulns = self._prioritize_vulnerabilities(vulnerabilities)

            # CVSS スコア計算
            cvss_scores = {
                vuln["id"]: self._calculate_cvss_score(vuln) for vuln in vulnerabilities
            }

            return {
                "vulnerability_assessment": {
                    "total_vulnerabilities": len(vulnerabilities),
                    "critical_count": len(
                        [v for v in vulnerabilities if v.get("severity") == "critical"]
                    ),
                    "high_count": len(
                        [v for v in vulnerabilities if v.get("severity") == "high"]
                    ),
                    "medium_count": len(
                        [v for v in vulnerabilities if v.get("severity") == "medium"]
                    ),
                    "low_count": len(
                        [v for v in vulnerabilities if v.get("severity") == "low"]
                    ),
                },
                "vulnerabilities": prioritized_vulns,
                "cvss_scores": cvss_scores,
                "risk_level": self._determine_risk_level(vulnerabilities),
                "remediation_timeline": self._create_remediation_timeline(
                    prioritized_vulns
                ),
            }

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Vulnerability assessment failed: {e}")
            return {
                "vulnerability_assessment": {"error": str(e)},
                "vulnerabilities": [],
                "risk_level": "unknown",
            }

    async def _secure_code_generation(
        self, functionality_spec: Dict[str, Any], security_requirements: List[str]
    ) -> Dict[str, Any]:
        """セキュアコード生成"""
        try:
            # セキュリティ要件の解析
            security_controls = self._parse_security_requirements(security_requirements)

            # セキュアコードパターンの適用
            secure_code_components = []

            # 入力検証コード
            if "input_validation" in security_requirements:
                validation_code = self.secure_coder.generate_input_validation()
                secure_code_components.append(validation_code)

            # 出力エンコーディング
            if "output_encoding" in security_requirements:
                encoding_code = self.secure_coder.generate_output_encoding()
                secure_code_components.append(encoding_code)

            # 認証・認可
            if "authentication" in security_requirements:
                auth_code = self.secure_coder.generate_authentication_system()
                secure_code_components.append(auth_code)

            # セキュアストレージ
            if "secure_storage" in security_requirements:
                storage_code = self.secure_coder.generate_secure_storage()
                secure_code_components.append(storage_code)

            # セキュアログ記録
            if "secure_logging" in security_requirements:
                logging_code = self.secure_coder.generate_secure_logging()
                secure_code_components.append(logging_code)

            # 統合されたセキュアコード
            integrated_code = self._integrate_secure_components(secure_code_components)

            return {
                "secure_code": integrated_code,
                "security_controls": security_controls,
                "components_generated": len(secure_code_components),
                "security_patterns_applied": security_requirements,
                "security_compliance": self._verify_security_compliance(
                    integrated_code, security_requirements
                ),
            }

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Secure code generation failed: {e}")
            return {"secure_code": "", "error": str(e), "security_controls": []}

    async def _encryption_implementation(
        self, data_spec: Dict[str, Any], encryption_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """暗号化実装"""
        try:
            # 暗号化仕様の解析
            data_types = data_spec.get("data_types", [])
            sensitivity_level = encryption_requirements.get("sensitivity", "medium")

            # 暗号化方式の選択
            encryption_method = self._select_encryption_method(sensitivity_level)

            # 暗号化コードの生成
            encryption_components = []

            # データ暗号化
            if "data_encryption" in encryption_requirements:
                data_encryption = self.crypto_manager.generate_data_encryption_code(
                    encryption_method
                )
                encryption_components.append(data_encryption)

            # キー管理
            if "key_management" in encryption_requirements:
                key_management = self.crypto_manager.generate_key_management_code()
                encryption_components.append(key_management)

            # 通信暗号化
            if "transport_encryption" in encryption_requirements:
                transport_encryption = (
                    self.crypto_manager.generate_transport_encryption_code()
                )
                encryption_components.append(transport_encryption)

            # ハッシュ化
            if "hashing" in encryption_requirements:
                hashing_code = self.crypto_manager.generate_hashing_code()
                encryption_components.append(hashing_code)

            # 統合された暗号化システム
            integrated_encryption = self._integrate_encryption_components(
                encryption_components
            )

            return {
                "encryption_code": integrated_encryption,
                "encryption_method": encryption_method,
                "key_length": self._get_key_length(encryption_method),
                "components_implemented": len(encryption_components),
                "security_strength": self._assess_encryption_strength(
                    encryption_method
                ),
                "performance_impact": self._estimate_encryption_performance_impact(
                    encryption_method
                ),
            }

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Encryption implementation failed: {e}")
            return {"encryption_code": "", "error": str(e), "encryption_method": "none"}

    async def _access_control_design(
        self, user_roles: List[str], resource_permissions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """アクセス制御設計"""
        try:
            # RBAC (Role-Based Access Control) システムの設計
            rbac_system = self.access_controller.design_rbac_system(
                user_roles, resource_permissions
            )

            # 権限マトリックスの生成
            permission_matrix = self._generate_permission_matrix(
                user_roles, resource_permissions
            )

            # アクセス制御コードの生成
            access_control_code = self.access_controller.generate_access_control_code(
                rbac_system
            )

            # セキュリティポリシーの定義
            security_policies = self._define_security_policies(
                user_roles, resource_permissions
            )

            return {
                "access_control_system": {
                    "rbac_design": rbac_system,
                    "permission_matrix": permission_matrix,
                    "security_policies": security_policies,
                },
                "access_control_code": access_control_code,
                "roles_count": len(user_roles),
                "permissions_count": len(resource_permissions),
                "security_level": self._assess_access_control_security(rbac_system),
            }

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Access control design failed: {e}")
            return {
                "access_control_system": {},
                "error": str(e),
                "access_control_code": "",
            }

    async def _security_testing(
        self, application_code: str, attack_vectors: List[str]
    ) -> Dict[str, Any]:
        """セキュリティテスト生成"""
        try:
            # セキュリティテストケースの生成
            security_tests = []

            # 攻撃ベクターに基づくテスト
            for vector in attack_vectors:
                test_cases = self._generate_attack_vector_tests(
                    vector, application_code
                )
                security_tests.extend(test_cases)

            # OWASP ベーステスト
            owasp_tests = self._generate_owasp_security_tests(application_code)
            security_tests.extend(owasp_tests)

            # 境界値セキュリティテスト
            boundary_tests = self._generate_boundary_security_tests(application_code)
            security_tests.extend(boundary_tests)

            # ペネトレーションテストスクリプト
            pentest_scripts = self._generate_pentest_scripts(
                application_code, attack_vectors
            )

            return {
                "security_tests": security_tests,
                "test_count": len(security_tests),
                "attack_vectors_covered": len(attack_vectors),
                "pentest_scripts": pentest_scripts,
                "test_coverage": self._calculate_security_test_coverage(
                    security_tests, application_code
                ),
            }

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Security testing generation failed: {e}")
            return {"security_tests": [], "error": str(e), "test_count": 0}

    async def _validate_security_quality(self, result_data: Dict[str, Any]) -> float:
        """セキュリティ品質検証"""
        quality_score = await self.validate_crafting_quality(result_data)

        try:
            # セキュリティ固有の品質チェック
            security_score = result_data.get("security_score", 0)
            quality_score += security_score * 0.3

            # 検出した脆弱性・問題数
            issues_count = len(result_data.get("security_issues", [])) + len(
                result_data.get("vulnerabilities", [])
            )
            quality_score += min(20.0, issues_count * 1.5)

            # 修復計画・コード生成
            if result_data.get("remediation_plan") or result_data.get("secure_code"):
                # Complex condition - consider breaking down
                quality_score += 15.0

            # コンプライアンス状況
            compliance = result_data.get("compliance_status", {})
            if compliance and compliance.get("compliant", False):
                # Complex condition - consider breaking down
                quality_score += 10.0

            # エラーなしボーナス
            if "error" not in result_data:
                quality_score += 10.0

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Security quality validation error: {e}")
            quality_score = max(quality_score - 10.0, 0.0)

        return min(quality_score, 100.0)

    # ヘルパーメソッドとクラス
    def _load_owasp_standards(self) -> Dict[str, Any]:
        """OWASP標準読み込み"""
        return {

                "severity": "high",

            },
            "A02_cryptographic_failures": {
                "severity": "high",
                "description": "Cryptographic Failures",
            },
            "A03_injection": {"severity": "critical", "description": "Injection"},
            "A04_insecure_design": {
                "severity": "medium",
                "description": "Insecure Design",
            },
            "A05_security_misconfiguration": {
                "severity": "medium",
                "description": "Security Misconfiguration",
            },
            "A06_vulnerable_components": {
                "severity": "medium",
                "description": "Vulnerable and Outdated Components",
            },
            "A07_identification_failures": {
                "severity": "high",
                "description": "Identification and Authentication Failures",
            },
            "A08_software_integrity_failures": {
                "severity": "medium",
                "description": "Software and Data Integrity Failures",
            },
            "A09_security_logging_failures": {
                "severity": "low",
                "description": "Security Logging and Monitoring Failures",
            },
            "A10_server_side_request_forgery": {
                "severity": "medium",
                "description": "Server-Side Request Forgery",
            },
        }

    def _load_cwe_standards(self) -> Dict[str, Any]:
        """CWE標準読み込み"""
        return {
            "CWE-79": {"name": "Cross-site Scripting", "severity": "high"},
            "CWE-89": {"name": "SQL Injection", "severity": "critical"},
            "CWE-22": {"name": "Path Traversal", "severity": "high"},
            "CWE-78": {"name": "Command Injection", "severity": "critical"},
            "CWE-94": {"name": "Code Injection", "severity": "critical"},
        }

    def _load_nist_guidelines(self) -> Dict[str, Any]:
        """NIST ガイドライン読み込み"""
        return {
            "access_control": "Implement least privilege access",
            "audit_logging": "Maintain comprehensive audit logs",
            "data_protection": "Encrypt sensitive data at rest and in transit",
            "incident_response": "Establish incident response procedures",
        }

    def _initialize_secure_patterns(self) -> Dict[str, Any]:
        """セキュアパターン初期化"""
        return {
            "input_validation": {
                "pattern": "validate_all_inputs",
                "description": "Validate all user inputs",
            },
            "output_encoding": {
                "pattern": "encode_all_outputs",
                "description": "Encode all outputs to prevent XSS",
            },
            "secure_storage": {
                "pattern": "encrypt_sensitive_data",
                "description": "Encrypt sensitive data at rest",
            },
        }

    def _initialize_vulnerability_database(self) -> Dict[str, Any]:
        """脆弱性データベース初期化"""
        return {
            "known_vulnerabilities": [],
            "patterns": [],
            "mitigation_strategies": {},
        }

class CryptographyManager:
    """暗号化管理"""

    def generate_data_encryption_code(self, method: str) -> str:
        """データ暗号化コード生成"""
        if method == "AES-256-GCM":
            return '''
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

def encrypt_data(data: bytes, key: bytes) -> tuple:
    """AES-256-GCM encryption"""
    iv = os.urandom(12)  # 96-bit IV for GCM
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(data) + encryptor.finalize()
    return (ciphertext, iv, encryptor.tag)

def decrypt_data(ciphertext: bytes, key: bytes, iv: bytes, tag: bytes) -> bytes:
    """AES-256-GCM decryption"""
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()
'''
        return "# Encryption code placeholder"

    def generate_key_management_code(self) -> str:
        """キー管理コード生成"""
        return '''
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import base64

def generate_key_from_password(password: str, salt: bytes = None) -> bytes:
    """Generate encryption key from password using PBKDF2"""
    if salt is None:
        salt = os.urandom(16)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = kdf.derive(password.encode())
    return key

def generate_random_key() -> bytes:
    """Generate cryptographically secure random key"""
    return os.urandom(32)  # 256-bit key
'''

    def generate_transport_encryption_code(self) -> str:
        """通信暗号化コード生成"""
        return '''
import ssl
import socket

def create_secure_context():
    """Create secure SSL context for transport encryption"""
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context

def secure_socket_connection(host: str, port: int):
    """Create secure socket connection"""
    context = create_secure_context()
    with socket.create_connection((host, port)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            return ssock
'''

    def generate_hashing_code(self) -> str:
        """ハッシュ化コード生成"""
        return '''
import hashlib
import secrets

def secure_hash_password(password: str) -> tuple:
    """Securely hash password with salt"""
    salt = secrets.token_bytes(32)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return (pwdhash, salt)

def verify_password(password: str, stored_hash: bytes, salt: bytes) -> bool:
    """Verify password against stored hash"""
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return pwdhash == stored_hash
'''

class AccessController:
    """アクセス制御"""

    def design_rbac_system(
        self, roles: List[str], permissions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """RBAC システム設計"""
        return {
            "roles": roles,
            "permissions": permissions,
            "role_hierarchy": self._create_role_hierarchy(roles),
            "access_matrix": self._create_access_matrix(roles, permissions),
        }

    def generate_access_control_code(self, rbac_system: Dict[str, Any]) -> str:
        """アクセス制御コード生成"""
        return '''
from functools import wraps
from typing import List, Dict

class AccessController:
    # Main class implementation:
    def __init__(self, user_roles: Dict[str, List[str]], role_permissions: Dict[str, List[str]]):
        self.user_roles = user_roles
        self.role_permissions = role_permissions

    def has_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has specific permission"""
        user_roles = self.user_roles.get(user_id, [])
        for role in user_roles:
            # Process each item in collection
            if permission in self.role_permissions.get(role, []):
                return True
        return False

    def require_permission(self, permission: str):
        """Decorator for permission-based access control"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Get user from context (implementation specific)
                user_id = get_current_user_id()
                if not self.has_permission(user_id, permission):
                    raise PermissionError(f"Access denied: {permission} required")
                return func(*args, **kwargs)
            return wrapper
        return decorator
'''

class ThreatAnalyzer:
    """脅威分析"""

    def analyze_threats(self, code: str) -> List[Dict[str, Any]]:
        """脅威分析実行"""
        threats = []

        # 簡易実装: 危険なパターンの検出
        if "eval(" in code:
            threats.append(
                {
                    "type": "code_injection",
                    "severity": "critical",
                    "description": "Use of eval() function detected",
                }
            )

        if "subprocess.run(" in code:
            threats.append(
                {
                    "type": "command_injection",
                    "severity": "high",
                    "description": "Use of subprocess.run(, shell=False, shell=False) detected",
                }
            )

        return threats

class SecureCoder:
    """セキュアコーダー"""

    def generate_input_validation(self) -> str:
        """入力検証コード生成"""
        return '''
import re
from typing import Any

def validate_input(data: str, pattern: str = None, max_length: int = 255) -> bool:
    """Validate input data against security criteria"""
    if not isinstance(data, str):
        return False

    if len(data) > max_length:
        return False

    if pattern and not re.match(pattern, data):
        # Complex condition - consider breaking down
        return False

    # Check for common injection patterns
    dangerous_patterns = ['<script', 'javascript:', 'vbscript:', 'onload=', 'onerror=']
    data_lower = data.lower()
    for pattern in dangerous_patterns:
        # Process each item in collection
        if pattern in data_lower:
            return False

    return True
'''

    def generate_output_encoding(self) -> str:
        """出力エンコーディングコード生成"""
        return '''
import html
import urllib.parse

def encode_for_html(data: str) -> str:
    """Encode data for safe HTML output"""
    return html.escape(data, quote=True)

def encode_for_url(data: str) -> str:
    """Encode data for safe URL output"""
    return urllib.parse.quote(data, safe='')

def encode_for_javascript(data: str) -> str:
    """Encode data for safe JavaScript output"""
    return data.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
'''
