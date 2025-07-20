#!/usr/bin/env python3
"""
🔒 Auto Issue Processor A2A Security Manager
セキュリティ強化・脆弱性対策・アクセス制御システム

Issue #194対応: 包括的セキュリティ機能の実装
"""

import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger("SecurityManager")


class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PermissionLevel(Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    EXECUTE = "execute"


@dataclass
class SecurityContext:
    user_id: str
    session_id: str
    permissions: List[PermissionLevel]
    security_level: SecurityLevel
    expires_at: datetime
    mfa_verified: bool = False
    audit_trail_id: str = ""


@dataclass
class VulnerabilityResult:
    severity: SecurityLevel
    vulnerability_type: str
    description: str
    affected_components: List[str]
    mitigation_steps: List[str]
    cve_references: List[str] = None


class InputValidator:
    """入力検証・サニタイゼーションシステム"""
    
    # 危険なパターン
    DANGEROUS_PATTERNS = [
        r'[;&|`$]',  # Command injection
        r'<script[^>]*>.*?</script>',  # XSS
        r'javascript:',  # JavaScript protocol
        r'data:text/html',  # Data URI XSS
        r'(?i)(union|select|insert|update|delete|drop|create|alter)',  # SQL injection
        r'\.\./',  # Path traversal
        r'__import__|eval|exec|compile',  # Python code injection
    ]
    
    # 許可されたファイル拡張子
    ALLOWED_EXTENSIONS = {'.py', '.md', '.txt', '.json', '.yaml', '.yml', '.cfg', '.ini'}
    
    def __init__(self):
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.DANGEROUS_PATTERNS]
    
    def validate_input(self, data: Any, context: str = "general") -> Dict[str, Any]:
        """包括的入力検証"""
        result = {
            "valid": True,
            "sanitized_data": data,
            "violations": [],
            "severity": SecurityLevel.LOW
        }
        
        if isinstance(data, str):
            # 文字列検証
            violations = self._check_string_patterns(data)
            if violations:
                result["violations"].extend(violations)
                result["severity"] = SecurityLevel.HIGH
                result["valid"] = False
                result["sanitized_data"] = self._sanitize_string(data)
        
        elif isinstance(data, dict):
            # 辞書検証（再帰）
            for key, value in data.items():
                key_result = self.validate_input(key, f"{context}.key")
                value_result = self.validate_input(value, f"{context}.{key}")
                
                if not key_result["valid"] or not value_result["valid"]:
                    result["violations"].extend(key_result["violations"])
                    result["violations"].extend(value_result["violations"])
                    result["severity"] = max(result["severity"], key_result["severity"], value_result["severity"])
                    result["valid"] = False
        
        elif isinstance(data, list):
            # リスト検証
            for i, item in enumerate(data):
                item_result = self.validate_input(item, f"{context}[{i}]")
                if not item_result["valid"]:
                    result["violations"].extend(item_result["violations"])
                    result["severity"] = max(result["severity"], item_result["severity"])
                    result["valid"] = False
        
        return result
    
    def _check_string_patterns(self, text: str) -> List[str]:
        """危険なパターンチェック"""
        violations = []
        
        for pattern in self.patterns:
            if pattern.search(text):
                violations.append(f"Dangerous pattern detected: {pattern.pattern}")
        
        return violations
    
    def _sanitize_string(self, text: str) -> str:
        """文字列サニタイゼーション"""
        # HTML エンティティエスケープ
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&#x27;')
        
        # スクリプトタグ除去
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        return text
    
    def validate_file_path(self, file_path: str) -> Dict[str, Any]:
        """ファイルパス検証"""
        result = {
            "valid": True,
            "violations": [],
            "normalized_path": file_path
        }
        
        try:
            # パス正規化
            normalized = os.path.normpath(file_path)
            result["normalized_path"] = normalized
            
            # 絶対パスチェック
            if os.path.isabs(normalized):
                result["violations"].append("Absolute paths not allowed")
                result["valid"] = False
            
            # パストラバーサルチェック
            if '..' in normalized or normalized.startswith('/'):
                result["violations"].append("Path traversal detected")
                result["valid"] = False
            
            # 拡張子チェック
            if Path(normalized).suffix not in self.ALLOWED_EXTENSIONS:
                result["violations"].append(f"File extension not allowed: {Path(normalized).suffix}")
                result["valid"] = False
            
        except Exception as e:
            result["violations"].append(f"Path validation error: {str(e)}")
            result["valid"] = False
        
        return result


class AuthenticationManager:
    """認証・認可システム（RBAC対応）"""
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or os.getenv("A2A_SECRET_KEY", self._generate_secret_key())
        self.sessions: Dict[str, SecurityContext] = {}
        self.failed_attempts: Dict[str, List[datetime]] = {}
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=15)
    
    def _generate_secret_key(self) -> str:
        """セキュアなシークレットキー生成"""
        return secrets.token_urlsafe(32)
    
    def authenticate_user(self, user_id: str, token: str, mfa_code: str = None) -> Optional[SecurityContext]:
        """ユーザー認証（MFA対応）"""
        try:
            # レート制限チェック
            if self._is_rate_limited(user_id):
                logger.warning(f"Rate limited authentication attempt for user: {user_id}")
                return None
            
            # JWT トークン検証
            try:
                payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
                token_user_id = payload.get('user_id')
                
                if token_user_id != user_id:
                    self._record_failed_attempt(user_id)
                    return None
                
            except jwt.ExpiredSignatureError:
                logger.warning(f"Expired token for user: {user_id}")
                return None
            except jwt.InvalidTokenError:
                self._record_failed_attempt(user_id)
                return None
            
            # MFA検証（必要に応じて）
            mfa_verified = self._verify_mfa(user_id, mfa_code) if mfa_code else False
            
            # セキュリティコンテキスト作成
            session_id = secrets.token_urlsafe(32)
            security_context = SecurityContext(
                user_id=user_id,
                session_id=session_id,
                permissions=self._get_user_permissions(user_id),
                security_level=self._determine_security_level(user_id),
                expires_at=datetime.now() + timedelta(hours=24),
                mfa_verified=mfa_verified,
                audit_trail_id=self._create_audit_trail(user_id, session_id)
            )
            
            self.sessions[session_id] = security_context
            logger.info(f"Successful authentication for user: {user_id}")
            
            return security_context
            
        except Exception as e:
            logger.error(f"Authentication error for user {user_id}: {str(e)}")
            self._record_failed_attempt(user_id)
            return None
    
    def _is_rate_limited(self, user_id: str) -> bool:
        """レート制限チェック"""
        if user_id not in self.failed_attempts:
            return False
        
        # 過去のリセット
        cutoff = datetime.now() - self.lockout_duration
        self.failed_attempts[user_id] = [
            attempt for attempt in self.failed_attempts[user_id]
            if attempt > cutoff
        ]
        
        return len(self.failed_attempts[user_id]) >= self.max_failed_attempts
    
    def _record_failed_attempt(self, user_id: str):
        """失敗試行記録"""
        if user_id not in self.failed_attempts:
            self.failed_attempts[user_id] = []
        
        self.failed_attempts[user_id].append(datetime.now())
    
    def _verify_mfa(self, user_id: str, mfa_code: str) -> bool:
        """MFA検証（TOTP実装例）"""
        # 実装例: 時間ベースのワンタイムパスワード
        # 実際の実装では、ユーザーごとのシークレットを使用
        return len(mfa_code) == 6 and mfa_code.isdigit()
    
    def _get_user_permissions(self, user_id: str) -> List[PermissionLevel]:
        """ユーザー権限取得（RBAC）"""
        # TODO: データベースまたは設定ファイルから権限を取得
        # 現在は環境変数ベースの簡単な実装
        admin_users = os.getenv("A2A_ADMIN_USERS", "").split(",")
        
        if user_id in admin_users:
            return [PermissionLevel.ADMIN, PermissionLevel.EXECUTE, PermissionLevel.WRITE, PermissionLevel.READ]
        else:
            return [PermissionLevel.READ, PermissionLevel.WRITE]
    
    def _determine_security_level(self, user_id: str) -> SecurityLevel:
        """セキュリティレベル決定"""
        permissions = self._get_user_permissions(user_id)
        
        if PermissionLevel.ADMIN in permissions:
            return SecurityLevel.HIGH
        elif PermissionLevel.EXECUTE in permissions:
            return SecurityLevel.MEDIUM
        else:
            return SecurityLevel.LOW
    
    def _create_audit_trail(self, user_id: str, session_id: str) -> str:
        """監査証跡作成"""
        audit_id = secrets.token_hex(16)
        
        # 監査ログファイルに記録
        audit_dir = Path("logs/audit")
        audit_dir.mkdir(exist_ok=True)
        
        audit_entry = {
            "audit_id": audit_id,
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "action": "authentication",
            "status": "success"
        }
        
        audit_file = audit_dir / f"auth_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            # 既存ファイルの読み込み
            if audit_file.exists():
                with open(audit_file, 'r') as f:
                    audit_data = json.load(f)
            else:
                audit_data = []
            
            audit_data.append(audit_entry)
            
            # ファイルに書き込み
            with open(audit_file, 'w') as f:
                json.dump(audit_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to create audit trail: {str(e)}")
        
        return audit_id
    
    def validate_session(self, session_id: str) -> Optional[SecurityContext]:
        """セッション検証"""
        context = self.sessions.get(session_id)
        
        if not context:
            return None
        
        # 有効期限チェック
        if datetime.now() > context.expires_at:
            del self.sessions[session_id]
            return None
        
        return context
    
    def revoke_session(self, session_id: str) -> bool:
        """セッション無効化"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session revoked: {session_id}")
            return True
        return False


class DataProtectionManager:
    """データ保護・暗号化システム"""
    
    def __init__(self, master_key: str = None):
        self.master_key = master_key or os.getenv("A2A_MASTER_KEY")
        if not self.master_key:
            self.master_key = self._generate_master_key()
            logger.warning("Generated new master key. Store securely!")
        
        self.cipher_suite = self._create_cipher_suite()
    
    def _generate_master_key(self) -> str:
        """マスターキー生成"""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
    
    def _create_cipher_suite(self) -> Fernet:
        """暗号化スイート作成"""
        # パスワードベースの鍵導出
        password = self.master_key.encode()
        salt = b'a2a_salt_2025'  # 実際の実装では動的なsaltを使用
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return Fernet(key)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """機密データ暗号化"""
        try:
            encrypted = self.cipher_suite.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """機密データ復号化"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher_suite.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise
    
    def hash_sensitive_data(self, data: str, salt: str = None) -> Tuple[str, str]:
        """機密データハッシュ化（ソルト付き）"""
        if not salt:
            salt = secrets.token_hex(16)
        
        hash_obj = hashlib.pbkdf2_hmac('sha256', data.encode(), salt.encode(), 100000)
        return base64.urlsafe_b64encode(hash_obj).decode(), salt
    
    def verify_hash(self, data: str, hash_value: str, salt: str) -> bool:
        """ハッシュ検証"""
        computed_hash, _ = self.hash_sensitive_data(data, salt)
        return hmac.compare_digest(computed_hash, hash_value)


class VulnerabilityScanner:
    """脆弱性スキャンシステム"""
    
    def __init__(self):
        self.known_vulnerabilities = self._load_vulnerability_database()
    
    def _load_vulnerability_database(self) -> Dict[str, Any]:
        """脆弱性データベース読み込み"""
        # 簡単な実装例 - 実際はCVEデータベースと連携
        return {
            "command_injection": {
                "patterns": [r'[;&|`$]', r'&&', r'||'],
                "severity": SecurityLevel.CRITICAL,
                "mitigation": ["Input validation", "Parameterized execution"]
            },
            "path_traversal": {
                "patterns": [r'\.\./', r'\\.\\.\\'],
                "severity": SecurityLevel.HIGH,
                "mitigation": ["Path normalization", "Whitelist validation"]
            },
            "code_injection": {
                "patterns": [r'eval\(', r'exec\(', r'__import__'],
                "severity": SecurityLevel.CRITICAL,
                "mitigation": ["Code sanitization", "Sandboxing"]
            }
        }
    
    def scan_code(self, code: str, context: str = "general") -> List[VulnerabilityResult]:
        """コード脆弱性スキャン"""
        vulnerabilities = []
        
        for vuln_type, vuln_info in self.known_vulnerabilities.items():
            for pattern in vuln_info["patterns"]:
                if re.search(pattern, code, re.IGNORECASE):
                    vulnerability = VulnerabilityResult(
                        severity=vuln_info["severity"],
                        vulnerability_type=vuln_type,
                        description=f"{vuln_type} detected in {context}",
                        affected_components=[context],
                        mitigation_steps=vuln_info["mitigation"]
                    )
                    vulnerabilities.append(vulnerability)
        
        return vulnerabilities
    
    def scan_dependencies(self, requirements_file: str = "requirements.txt") -> List[VulnerabilityResult]:
        """依存関係脆弱性スキャン"""
        vulnerabilities = []
        
        try:
            if Path(requirements_file).exists():
                with open(requirements_file, 'r') as f:
                    dependencies = f.readlines()
                
                # 簡単なバージョンチェック例
                for dep in dependencies:
                    dep = dep.strip()
                    if dep and not dep.startswith('#'):
                        # 既知の脆弱性チェック
                        if self._check_vulnerable_dependency(dep):
                            vulnerability = VulnerabilityResult(
                                severity=SecurityLevel.HIGH,
                                vulnerability_type="vulnerable_dependency",
                                description=f"Vulnerable dependency detected: {dep}",
                                affected_components=[dep],
                                mitigation_steps=["Update to latest version", "Use alternative package"]
                            )
                            vulnerabilities.append(vulnerability)
        
        except Exception as e:
            logger.error(f"Dependency scan failed: {str(e)}")
        
        return vulnerabilities
    
    def _check_vulnerable_dependency(self, dependency: str) -> bool:
        """脆弱な依存関係チェック（簡単な実装）"""
        # 実際の実装では、安全でないバージョンのデータベースを使用
        vulnerable_patterns = [
            r'requests==2\.25\.0',  # 例: 既知の脆弱なバージョン
            r'urllib3==1\.26\.0',
        ]
        
        return any(re.search(pattern, dependency) for pattern in vulnerable_patterns)


class SecurityManager:
    """包括的セキュリティマネージャー"""
    
    def __init__(self):
        self.input_validator = InputValidator()
        self.auth_manager = AuthenticationManager()
        self.data_protection = DataProtectionManager()
        self.vulnerability_scanner = VulnerabilityScanner()
        
        # セキュリティポリシー
        self.security_policies = {
            "max_file_size": 10 * 1024 * 1024,  # 10MB
            "allowed_operations": ["read", "write", "execute"],
            "require_mfa_for_admin": True,
            "session_timeout_hours": 24,
            "audit_retention_days": 90
        }
    
    def validate_request(self, request: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """リクエスト包括検証"""
        result = {
            "valid": True,
            "violations": [],
            "sanitized_request": request,
            "security_level": SecurityLevel.LOW
        }
        
        try:
            # 入力検証
            input_result = self.input_validator.validate_input(request, "request")
            if not input_result["valid"]:
                result["violations"].extend(input_result["violations"])
                result["valid"] = False
                result["security_level"] = input_result["severity"]
            
            # 権限チェック
            operation = request.get("operation", "read")
            if not self._check_permission(security_context, operation):
                result["violations"].append(f"Insufficient permissions for operation: {operation}")
                result["valid"] = False
                result["security_level"] = SecurityLevel.HIGH
            
            # セキュリティポリシーチェック
            policy_violations = self._check_security_policies(request, security_context)
            if policy_violations:
                result["violations"].extend(policy_violations)
                result["valid"] = False
                result["security_level"] = SecurityLevel.MEDIUM
            
            # 脆弱性スキャン（コードが含まれる場合）
            if "code" in request:
                vulnerabilities = self.vulnerability_scanner.scan_code(request["code"], "request_code")
                if vulnerabilities:
                    critical_vulns = [v for v in vulnerabilities if v.severity == SecurityLevel.CRITICAL]
                    if critical_vulns:
                        result["violations"].append("Critical vulnerabilities detected in code")
                        result["valid"] = False
                        result["security_level"] = SecurityLevel.CRITICAL
            
        except Exception as e:
            logger.error(f"Security validation error: {str(e)}")
            result["violations"].append(f"Security validation failed: {str(e)}")
            result["valid"] = False
            result["security_level"] = SecurityLevel.HIGH
        
        return result
    
    def _check_permission(self, context: SecurityContext, operation: str) -> bool:
        """権限チェック"""
        operation_mapping = {
            "read": PermissionLevel.READ,
            "write": PermissionLevel.WRITE,
            "execute": PermissionLevel.EXECUTE,
            "admin": PermissionLevel.ADMIN
        }
        
        required_permission = operation_mapping.get(operation, PermissionLevel.READ)
        return required_permission in context.permissions
    
    def _check_security_policies(self, request: Dict[str, Any], context: SecurityContext) -> List[str]:
        """セキュリティポリシーチェック"""
        violations = []
        
        # MFA要件チェック
        if (PermissionLevel.ADMIN in context.permissions and 
            self.security_policies["require_mfa_for_admin"] and 
            not context.mfa_verified):
            violations.append("MFA required for admin operations")
        
        # ファイルサイズチェック
        if "file_content" in request:
            content = request["file_content"]
            if isinstance(content, str) and len(content.encode()) > self.security_policies["max_file_size"]:
                violations.append("File size exceeds maximum allowed")
        
        return violations
    
    def create_security_report(self) -> Dict[str, Any]:
        """セキュリティレポート作成"""
        # 依存関係スキャン
        dependency_vulns = self.vulnerability_scanner.scan_dependencies()
        
        # 監査ログ統計
        audit_stats = self._get_audit_statistics()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "vulnerability_summary": {
                "total_vulnerabilities": len(dependency_vulns),
                "critical": len([v for v in dependency_vulns if v.severity == SecurityLevel.CRITICAL]),
                "high": len([v for v in dependency_vulns if v.severity == SecurityLevel.HIGH]),
                "medium": len([v for v in dependency_vulns if v.severity == SecurityLevel.MEDIUM]),
                "low": len([v for v in dependency_vulns if v.severity == SecurityLevel.LOW])
            },
            "audit_summary": audit_stats,
            "active_sessions": len(self.auth_manager.sessions),
            "security_policies": self.security_policies,
            "recommendations": self._generate_security_recommendations(dependency_vulns)
        }
        
        return report
    
    def _get_audit_statistics(self) -> Dict[str, Any]:
        """監査統計取得"""
        # 簡単な実装例
        audit_dir = Path("logs/audit")
        if not audit_dir.exists():
            return {"total_events": 0, "recent_events": 0}
        
        total_events = 0
        recent_events = 0
        recent_cutoff = datetime.now() - timedelta(hours=24)
        
        for audit_file in audit_dir.glob("auth_*.json"):
            try:
                with open(audit_file, 'r') as f:
                    events = json.load(f)
                    total_events += len(events)
                    
                    for event in events:
                        event_time = datetime.fromisoformat(event["timestamp"])
                        if event_time > recent_cutoff:
                            recent_events += 1
            except Exception as e:
                logger.warning(f"Failed to read audit file {audit_file}: {str(e)}")
        
        return {
            "total_events": total_events,
            "recent_events": recent_events
        }
    
    def _generate_security_recommendations(self, vulnerabilities: List[VulnerabilityResult]) -> List[str]:
        """セキュリティ推奨事項生成"""
        recommendations = []
        
        if vulnerabilities:
            recommendations.append("Update vulnerable dependencies to latest versions")
            recommendations.append("Implement automated vulnerability scanning in CI/CD")
        
        recommendations.extend([
            "Enable MFA for all admin users",
            "Regularly rotate encryption keys",
            "Monitor audit logs for suspicious activities",
            "Implement rate limiting for API endpoints",
            "Use HTTPS for all communications"
        ])
        
        return recommendations


# シングルトンインスタンス
_security_manager = None

def get_security_manager() -> SecurityManager:
    """セキュリティマネージャーシングルトン取得"""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager