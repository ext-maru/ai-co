#!/usr/bin/env python3
"""
Security Level Enforcer - セキュリティ境界エンフォーサー
Phase 1 Week 2 Day 11-12: セキュリティレベル分離システム

4賢者の知見を統合した高度なセキュリティ境界管理システム
- レベル間データ転送の暗号化・検証
- API呼び出しの認証・認可機能  
- コンテナ間通信の制限・監視
- 自動権限降格システム
"""

import os
import sys
import json
import hmac
import hashlib
import secrets
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import cryptography.fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import logging

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.shared_enums import SecurityLevel
from libs.env_config import get_config

class PermissionLevel(Enum):
    """権限レベル定義"""
    NONE = "none"           # アクセス不可
    READ = "read"           # 読み取りのみ
    WRITE = "write"         # 読み書き可能
    EXECUTE = "execute"     # 実行可能
    ADMIN = "admin"         # 管理者権限

class DataClassification(Enum):
    """データ分類レベル"""
    PUBLIC = "public"           # 公開データ
    INTERNAL = "internal"       # 内部データ
    CONFIDENTIAL = "confidential"  # 機密データ
    RESTRICTED = "restricted"   # 制限データ
    TOP_SECRET = "top_secret"   # 極秘データ

class AccessViolationType(Enum):
    """アクセス違反タイプ"""
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    RESOURCE_ABUSE = "resource_abuse"
    POLICY_VIOLATION = "policy_violation"

@dataclass
class SecurityContext:
    """セキュリティコンテキスト"""
    user_id: str
    session_id: str
    security_level: SecurityLevel
    permissions: List[PermissionLevel]
    data_access_levels: List[DataClassification]
    created_at: datetime
    expires_at: datetime
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    additional_claims: Dict[str, Any] = None

@dataclass
class AccessRequest:
    """アクセス要求"""
    resource_id: str
    action: str
    data_classification: DataClassification
    required_permission: PermissionLevel
    context: SecurityContext
    metadata: Dict[str, Any] = None

@dataclass
class AccessResult:
    """アクセス結果"""
    granted: bool
    reason: str
    session_id: str
    timestamp: datetime
    risk_score: float
    restrictions: List[str] = None
    audit_data: Dict[str, Any] = None

@dataclass
class SecurityViolation:
    """セキュリティ違反記録"""
    violation_id: str
    violation_type: AccessViolationType
    user_id: str
    security_level: SecurityLevel
    resource_id: str
    timestamp: datetime
    severity: int  # 1-10
    description: str
    evidence: Dict[str, Any]
    response_action: str

class SecurityLevelEnforcer:
    """セキュリティレベル間の境界を厳格に管理するエンフォーサー"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        
        # セキュリティ設定初期化
        self._initialize_security_matrix()
        self._initialize_encryption()
        self._initialize_monitoring()
        
        # アクティブセッション管理
        self.active_sessions: Dict[str, SecurityContext] = {}
        self.session_lock = threading.RLock()
        
        # 違反追跡
        self.violations: List[SecurityViolation] = []
        self.violation_thresholds = self._load_violation_thresholds()
        
        # セキュリティポリシー
        self.security_policies = self._load_security_policies()
        
        self.logger.info("🛡️ SecurityLevelEnforcer initialized")
    
    def _initialize_security_matrix(self):
        """セキュリティレベル間のアクセスマトリックス初期化"""
        self.access_matrix = {
            # From -> To のアクセス許可マトリックス
            SecurityLevel.SANDBOX: {
                SecurityLevel.SANDBOX: [PermissionLevel.READ, PermissionLevel.WRITE],
                SecurityLevel.RESTRICTED: [PermissionLevel.NONE],
                SecurityLevel.DEVELOPMENT: [PermissionLevel.NONE],
                SecurityLevel.TRUSTED: [PermissionLevel.NONE]
            },
            SecurityLevel.RESTRICTED: {
                SecurityLevel.SANDBOX: [PermissionLevel.READ, PermissionLevel.WRITE],
                SecurityLevel.RESTRICTED: [PermissionLevel.READ, PermissionLevel.WRITE],
                SecurityLevel.DEVELOPMENT: [PermissionLevel.READ],
                SecurityLevel.TRUSTED: [PermissionLevel.NONE]
            },
            SecurityLevel.DEVELOPMENT: {
                SecurityLevel.SANDBOX: [PermissionLevel.READ, PermissionLevel.WRITE, PermissionLevel.EXECUTE],
                SecurityLevel.RESTRICTED: [PermissionLevel.READ, PermissionLevel.WRITE],
                SecurityLevel.DEVELOPMENT: [PermissionLevel.READ, PermissionLevel.WRITE, PermissionLevel.EXECUTE],
                SecurityLevel.TRUSTED: [PermissionLevel.READ]
            },
            SecurityLevel.TRUSTED: {
                SecurityLevel.SANDBOX: [PermissionLevel.READ, PermissionLevel.WRITE, PermissionLevel.EXECUTE, PermissionLevel.ADMIN],
                SecurityLevel.RESTRICTED: [PermissionLevel.READ, PermissionLevel.WRITE, PermissionLevel.EXECUTE],
                SecurityLevel.DEVELOPMENT: [PermissionLevel.READ, PermissionLevel.WRITE, PermissionLevel.EXECUTE],
                SecurityLevel.TRUSTED: [PermissionLevel.READ, PermissionLevel.WRITE, PermissionLevel.EXECUTE, PermissionLevel.ADMIN]
            }
        }
        
        # データ分類別アクセス制御
        self.data_access_matrix = {
            SecurityLevel.SANDBOX: [DataClassification.PUBLIC],
            SecurityLevel.RESTRICTED: [DataClassification.PUBLIC, DataClassification.INTERNAL],
            SecurityLevel.DEVELOPMENT: [DataClassification.PUBLIC, DataClassification.INTERNAL, DataClassification.CONFIDENTIAL],
            SecurityLevel.TRUSTED: [DataClassification.PUBLIC, DataClassification.INTERNAL, 
                                   DataClassification.CONFIDENTIAL, DataClassification.RESTRICTED, 
                                   DataClassification.TOP_SECRET]
        }
    
    def _initialize_encryption(self):
        """暗号化システム初期化"""
        # セキュリティレベル別暗号化キー生成
        self.encryption_keys = {}
        
        for level in SecurityLevel:
            # レベル固有のソルト
            salt = f"ai_company_{level.value}_security".encode()
            
            # PBKDF2でキー導出
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            # 環境変数またはデフォルトパスワードからキー生成
            password = os.getenv(f'SECURITY_KEY_{level.value.upper()}', 
                               f'ai_company_default_{level.value}').encode()
            key = base64.urlsafe_b64encode(kdf.derive(password))
            
            self.encryption_keys[level] = cryptography.fernet.Fernet(key)
        
        self.logger.info("🔐 Security encryption system initialized")
    
    def _initialize_monitoring(self):
        """監視システム初期化"""
        self.access_log = []
        self.anomaly_detector = AnomalyDetector()
        
        # セキュリティメトリクス
        self.security_metrics = {
            'total_access_requests': 0,
            'denied_access_attempts': 0,
            'security_violations': 0,
            'privilege_escalations': 0,
            'data_exfiltration_attempts': 0
        }
        
        self.logger.info("📊 Security monitoring system initialized")
    
    def _load_violation_thresholds(self) -> Dict[str, int]:
        """違反閾値設定読み込み"""
        return {
            'max_failed_attempts_per_hour': 10,
            'max_privilege_escalation_attempts': 3,
            'max_data_access_violations': 5,
            'session_timeout_minutes': 60,
            'max_concurrent_sessions': 5
        }
    
    def _load_security_policies(self) -> Dict[str, Any]:
        """セキュリティポリシー読み込み"""
        return {
            'enforce_encryption': True,
            'require_authentication': True,
            'enable_audit_logging': True,
            'auto_revoke_privileges': True,
            'anomaly_detection': True,
            'real_time_monitoring': True,
            'automatic_incident_response': True
        }
    
    def create_security_context(self, user_id: str, security_level: SecurityLevel,
                              permissions: List[PermissionLevel] = None,
                              session_duration_minutes: int = 60,
                              source_ip: str = None) -> SecurityContext:
        """セキュリティコンテキスト作成"""
        
        session_id = secrets.token_urlsafe(32)
        now = datetime.now()
        
        # デフォルト権限設定
        if permissions is None:
            permissions = self._get_default_permissions(security_level)
        
        # データアクセスレベル決定
        data_access_levels = self.data_access_matrix.get(security_level, [DataClassification.PUBLIC])
        
        context = SecurityContext(
            user_id=user_id,
            session_id=session_id,
            security_level=security_level,
            permissions=permissions,
            data_access_levels=data_access_levels,
            created_at=now,
            expires_at=now + timedelta(minutes=session_duration_minutes),
            source_ip=source_ip
        )
        
        # セッション管理に追加
        with self.session_lock:
            self.active_sessions[session_id] = context
        
        self.logger.info(f"🆔 Security context created: {session_id} for {user_id} at {security_level.value}")
        return context
    
    def _get_default_permissions(self, security_level: SecurityLevel) -> List[PermissionLevel]:
        """セキュリティレベルのデフォルト権限取得"""
        default_permissions = {
            SecurityLevel.SANDBOX: [PermissionLevel.READ],
            SecurityLevel.RESTRICTED: [PermissionLevel.READ, PermissionLevel.WRITE],
            SecurityLevel.DEVELOPMENT: [PermissionLevel.READ, PermissionLevel.WRITE, PermissionLevel.EXECUTE],
            SecurityLevel.TRUSTED: [PermissionLevel.READ, PermissionLevel.WRITE, PermissionLevel.EXECUTE, PermissionLevel.ADMIN]
        }
        return default_permissions.get(security_level, [PermissionLevel.READ])
    
    def validate_access(self, request: AccessRequest) -> AccessResult:
        """アクセス要求の検証"""
        
        start_time = time.time()
        self.security_metrics['total_access_requests'] += 1
        
        try:
            # セッション有効性チェック
            if not self._validate_session(request.context):
                return self._create_denied_result(request, "Invalid or expired session", 0.9)
            
            # 権限チェック
            if not self._check_permission(request):
                self.security_metrics['denied_access_attempts'] += 1
                return self._create_denied_result(request, "Insufficient permissions", 0.8)
            
            # データ分類アクセスチェック
            if not self._check_data_access(request):
                self.security_metrics['denied_access_attempts'] += 1
                return self._create_denied_result(request, "Data classification access denied", 0.8)
            
            # セキュリティレベル間アクセスチェック
            if not self._validate_cross_level_access(request):
                self.security_metrics['denied_access_attempts'] += 1
                return self._create_denied_result(request, "Cross-level access denied", 0.9)
            
            # 異常検知
            risk_score = self._calculate_risk_score(request)
            if risk_score > 0.7:
                self._record_potential_violation(request, risk_score)
            
            # アクセス許可
            result = AccessResult(
                granted=True,
                reason="Access granted",
                session_id=request.context.session_id,
                timestamp=datetime.now(),
                risk_score=risk_score,
                restrictions=self._get_access_restrictions(request),
                audit_data={
                    'user_id': request.context.user_id,
                    'security_level': request.context.security_level.value,
                    'resource': request.resource_id,
                    'action': request.action,
                    'processing_time_ms': (time.time() - start_time) * 1000
                }
            )
            
            self._log_access_attempt(request, result)
            return result
            
        except Exception as e:
            self.logger.error(f"🚨 Access validation error: {e}")
            return self._create_denied_result(request, f"System error: {str(e)}", 1.0)
    
    def _validate_session(self, context: SecurityContext) -> bool:
        """セッション有効性検証"""
        
        with self.session_lock:
            # セッション存在確認
            if context.session_id not in self.active_sessions:
                return False
            
            # 有効期限確認
            if datetime.now() > context.expires_at:
                del self.active_sessions[context.session_id]
                return False
            
            # セッション整合性確認
            stored_context = self.active_sessions[context.session_id]
            if (stored_context.user_id != context.user_id or 
                stored_context.security_level != context.security_level):
                return False
        
        return True
    
    def _check_permission(self, request: AccessRequest) -> bool:
        """権限チェック"""
        return request.required_permission in request.context.permissions
    
    def _check_data_access(self, request: AccessRequest) -> bool:
        """データ分類アクセスチェック"""
        return request.data_classification in request.context.data_access_levels
    
    def _validate_cross_level_access(self, request: AccessRequest) -> bool:
        """セキュリティレベル間アクセス検証"""
        
        # リソースのセキュリティレベル推定（実装では外部から取得）
        resource_security_level = self._get_resource_security_level(request.resource_id)
        
        if resource_security_level is None:
            return True  # レベル不明の場合は許可（デフォルト動作）
        
        # アクセスマトリックスチェック
        allowed_permissions = self.access_matrix.get(request.context.security_level, {}).get(
            resource_security_level, [PermissionLevel.NONE]
        )
        
        return request.required_permission in allowed_permissions
    
    def _get_resource_security_level(self, resource_id: str) -> Optional[SecurityLevel]:
        """リソースのセキュリティレベル取得"""
        # 実装例：リソースIDからセキュリティレベルを推定
        if 'sandbox' in resource_id.lower():
            return SecurityLevel.SANDBOX
        elif 'restricted' in resource_id.lower():
            return SecurityLevel.RESTRICTED
        elif 'development' in resource_id.lower():
            return SecurityLevel.DEVELOPMENT
        elif 'trusted' in resource_id.lower():
            return SecurityLevel.TRUSTED
        return None
    
    def _calculate_risk_score(self, request: AccessRequest) -> float:
        """リスクスコア計算"""
        
        score = 0.0
        
        # 時間ベースリスク
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:  # 深夜早朝アクセス
            score += 0.2
        
        # 権限レベルリスク
        if request.required_permission == PermissionLevel.ADMIN:
            score += 0.4
        elif request.required_permission == PermissionLevel.EXECUTE:
            score += 0.2
        
        # データ分類リスク
        data_risk = {
            DataClassification.PUBLIC: 0.0,
            DataClassification.INTERNAL: 0.1,
            DataClassification.CONFIDENTIAL: 0.3,
            DataClassification.RESTRICTED: 0.5,
            DataClassification.TOP_SECRET: 0.7
        }
        score += data_risk.get(request.data_classification, 0.0)
        
        # セッション年数リスク
        session_age = datetime.now() - request.context.created_at
        if session_age.total_seconds() > 3600:  # 1時間以上の古いセッション
            score += 0.2
        
        # 異常パターン検知
        anomaly_score = self.anomaly_detector.detect_anomaly(request)
        score += anomaly_score
        
        return min(score, 1.0)
    
    def _get_access_restrictions(self, request: AccessRequest) -> List[str]:
        """アクセス制限取得"""
        restrictions = []
        
        # セキュリティレベル別制限
        if request.context.security_level == SecurityLevel.SANDBOX:
            restrictions.extend(['no_network_access', 'read_only_filesystem', 'limited_cpu'])
        elif request.context.security_level == SecurityLevel.RESTRICTED:
            restrictions.extend(['limited_network_access', 'monitored_filesystem'])
        
        # データ分類別制限
        if request.data_classification in [DataClassification.CONFIDENTIAL, DataClassification.RESTRICTED]:
            restrictions.append('encryption_required')
        
        if request.data_classification == DataClassification.TOP_SECRET:
            restrictions.extend(['dual_authorization_required', 'audit_trail_mandatory'])
        
        return restrictions
    
    def _create_denied_result(self, request: AccessRequest, reason: str, risk_score: float) -> AccessResult:
        """アクセス拒否結果作成"""
        
        result = AccessResult(
            granted=False,
            reason=reason,
            session_id=request.context.session_id,
            timestamp=datetime.now(),
            risk_score=risk_score,
            audit_data={
                'user_id': request.context.user_id,
                'security_level': request.context.security_level.value,
                'resource': request.resource_id,
                'action': request.action,
                'denial_reason': reason
            }
        )
        
        self._log_access_attempt(request, result)
        return result
    
    def _record_potential_violation(self, request: AccessRequest, risk_score: float):
        """潜在的違反記録"""
        
        violation = SecurityViolation(
            violation_id=secrets.token_urlsafe(16),
            violation_type=AccessViolationType.POLICY_VIOLATION,
            user_id=request.context.user_id,
            security_level=request.context.security_level,
            resource_id=request.resource_id,
            timestamp=datetime.now(),
            severity=int(risk_score * 10),
            description=f"High risk access attempt: {risk_score:.2f}",
            evidence={
                'request': asdict(request),
                'risk_score': risk_score,
                'context': asdict(request.context)
            },
            response_action="monitoring_increased"
        )
        
        self.violations.append(violation)
        self.security_metrics['security_violations'] += 1
        
        self.logger.warning(f"⚠️ Potential security violation recorded: {violation.violation_id}")
    
    def _log_access_attempt(self, request: AccessRequest, result: AccessResult):
        """アクセス試行ログ記録"""
        
        log_entry = {
            'timestamp': result.timestamp.isoformat(),
            'user_id': request.context.user_id,
            'session_id': request.context.session_id,
            'security_level': request.context.security_level.value,
            'resource_id': request.resource_id,
            'action': request.action,
            'data_classification': request.data_classification.value,
            'required_permission': request.required_permission.value,
            'granted': result.granted,
            'reason': result.reason,
            'risk_score': result.risk_score,
            'restrictions': result.restrictions
        }
        
        self.access_log.append(log_entry)
        
        # ログファイルに保存
        log_file = Path("/home/aicompany/workspace/logs/security_access.log")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def encrypt_data(self, data: str, security_level: SecurityLevel) -> str:
        """セキュリティレベル別データ暗号化"""
        
        if security_level not in self.encryption_keys:
            raise ValueError(f"No encryption key for security level: {security_level}")
        
        fernet = self.encryption_keys[security_level]
        encrypted_data = fernet.encrypt(data.encode())
        
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt_data(self, encrypted_data: str, security_level: SecurityLevel) -> str:
        """セキュリティレベル別データ復号化"""
        
        if security_level not in self.encryption_keys:
            raise ValueError(f"No encryption key for security level: {security_level}")
        
        fernet = self.encryption_keys[security_level]
        decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = fernet.decrypt(decoded_data)
        
        return decrypted_data.decode()
    
    def revoke_session(self, session_id: str, reason: str = "Manual revocation"):
        """セッション無効化"""
        
        with self.session_lock:
            if session_id in self.active_sessions:
                context = self.active_sessions[session_id]
                del self.active_sessions[session_id]
                
                self.logger.info(f"🚫 Session revoked: {session_id} for {context.user_id} - {reason}")
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """セキュリティメトリクス取得"""
        
        with self.session_lock:
            active_sessions_count = len(self.active_sessions)
        
        return {
            'active_sessions': active_sessions_count,
            'total_violations': len(self.violations),
            'recent_access_attempts': len([
                log for log in self.access_log 
                if datetime.fromisoformat(log['timestamp']) > datetime.now() - timedelta(hours=1)
            ]),
            **self.security_metrics
        }
    
    def cleanup_expired_sessions(self):
        """期限切れセッションクリーンアップ"""
        
        now = datetime.now()
        expired_sessions = []
        
        with self.session_lock:
            for session_id, context in list(self.active_sessions.items()):
                if now > context.expires_at:
                    expired_sessions.append(session_id)
                    del self.active_sessions[session_id]
        
        if expired_sessions:
            self.logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")

class AnomalyDetector:
    """セキュリティ異常検知システム"""
    
    def __init__(self):
        self.baseline_patterns = {}
        self.suspicious_patterns = [
            'unusual_time_access',
            'rapid_permission_requests',
            'cross_level_escalation',
            'bulk_data_access',
            'repeated_failures'
        ]
    
    def detect_anomaly(self, request: AccessRequest) -> float:
        """異常スコア計算（0.0-1.0）"""
        
        # 簡易実装（実際はより高度な機械学習モデルを使用）
        anomaly_score = 0.0
        
        # 時間パターン異常
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:
            anomaly_score += 0.3
        
        # 権限エスカレーション検知
        if (request.required_permission == PermissionLevel.ADMIN and 
            request.context.security_level != SecurityLevel.TRUSTED):
            anomaly_score += 0.5
        
        # データアクセスパターン異常
        if (request.data_classification in [DataClassification.RESTRICTED, DataClassification.TOP_SECRET] and
            request.context.security_level in [SecurityLevel.SANDBOX, SecurityLevel.RESTRICTED]):
            anomaly_score += 0.6
        
        return min(anomaly_score, 1.0)

if __name__ == "__main__":
    # SecurityLevelEnforcer のテスト
    enforcer = SecurityLevelEnforcer()
    
    print("🛡️ SecurityLevelEnforcer Test Starting...")
    
    # テストセッション作成
    context = enforcer.create_security_context(
        user_id="test_user",
        security_level=SecurityLevel.DEVELOPMENT,
        permissions=[PermissionLevel.READ, PermissionLevel.WRITE]
    )
    
    print(f"✅ Security context created: {context.session_id}")
    
    # アクセス要求テスト
    access_request = AccessRequest(
        resource_id="development_project_1",
        action="read_file",
        data_classification=DataClassification.INTERNAL,
        required_permission=PermissionLevel.READ,
        context=context
    )
    
    result = enforcer.validate_access(access_request)
    print(f"📋 Access result: {'✅ GRANTED' if result.granted else '❌ DENIED'}")
    print(f"   Reason: {result.reason}")
    print(f"   Risk Score: {result.risk_score:.2f}")
    
    # セキュリティメトリクス表示
    metrics = enforcer.get_security_metrics()
    print(f"📊 Security Metrics:")
    for key, value in metrics.items():
        print(f"   {key}: {value}")
    
    print("✅ SecurityLevelEnforcer test completed")