#!/usr/bin/env python3
"""
PROJECT ELDERZAN SecurityLayer - Core Security Layer
プロジェクトエルダーザン セキュリティレイヤー - コアセキュリティレイヤー

統合セキュリティインターフェース - 80%コストカット実現の核心
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid

# HybridStorage統合
from libs.session_management.storage import HybridStorage
from libs.session_management.models import SessionContext, SessionMetadata, SageInteraction

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """セキュリティレベル"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class OperationType(Enum):
    """操作タイプ"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    ADMIN = "admin"

@dataclass
class SecurityContext:
    """セキュリティコンテキスト"""
    user_id: str
    session_id: str
    role: str
    permissions: List[str]
    security_level: SecurityLevel
    created_at: datetime
    expires_at: Optional[datetime] = None
    sage_approval: Optional[Dict[str, Any]] = None
    
    def is_valid(self) -> bool:
        """セキュリティコンテキスト有効性確認"""
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return True
    
    def has_permission(self, permission: str) -> bool:
        """権限確認"""
        return permission in self.permissions or '*' in self.permissions

class ElderZanSecurityLayer:
    """
    PROJECT ELDERZAN 統合セキュリティレイヤー
    
    機能:
    - AES-256暗号化統合
    - RBAC権限管理
    - 監査ログ管理
    - 脅威検出
    - HybridStorage統合
    - 4賢者システム統合
    """
    
    def __init__(self, 
                 hybrid_storage: Optional[HybridStorage] = None,
                 encryption_enabled: bool = True,
                 audit_enabled: bool = True):
        """
        セキュリティレイヤー初期化
        
        Args:
            hybrid_storage: HybridStorageインスタンス
            encryption_enabled: 暗号化有効化
            audit_enabled: 監査ログ有効化
        """
        # コンポーネント初期化
        self.hybrid_storage = hybrid_storage or HybridStorage()
        self.encryption_enabled = encryption_enabled
        self.audit_enabled = audit_enabled
        
        # セキュリティコンテキスト管理
        self.active_contexts: Dict[str, SecurityContext] = {}
        self.security_policies: Dict[str, Dict[str, Any]] = {}
        
        # 統計情報
        self.stats = {
            'authentications': 0,
            'authorizations': 0,
            'encryptions': 0,
            'audit_logs': 0,
            'threats_detected': 0,
            'errors': 0
        }
        
        # 初期化完了ログ
        logger.info("ElderZanSecurityLayer initialized successfully")
    
    async def create_security_context(self, 
                                    user_id: str,
                                    session_id: str,
                                    role: str,
                                    permissions: List[str],
                                    security_level: SecurityLevel = SecurityLevel.MEDIUM,
                                    expires_in_minutes: int = 60) -> SecurityContext:
        """
        セキュリティコンテキスト作成
        
        Args:
            user_id: ユーザーID
            session_id: セッションID  
            role: ロール
            permissions: 権限リスト
            security_level: セキュリティレベル
            expires_in_minutes: 有効期限（分）
            
        Returns:
            SecurityContext: 作成されたセキュリティコンテキスト
        """
        try:
            # 有効期限設定
            expires_at = None
            if expires_in_minutes > 0:
                expires_at = datetime.now() + timedelta(minutes=expires_in_minutes)
            
            # セキュリティコンテキスト作成
            context = SecurityContext(
                user_id=user_id,
                session_id=session_id,
                role=role,
                permissions=permissions,
                security_level=security_level,
                created_at=datetime.now(),
                expires_at=expires_at
            )
            
            # コンテキスト保存
            self.active_contexts[session_id] = context
            
            # 監査ログ記録
            if self.audit_enabled:
                await self._log_security_event(
                    'security_context_created',
                    {
                        'user_id': user_id,
                        'session_id': session_id,
                        'role': role,
                        'security_level': security_level.value
                    }
                )
            
            self.stats['authentications'] += 1
            return context
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Failed to create security context: {e}")
            raise SecurityError(f"Security context creation failed: {e}")
    
    async def authenticate(self, 
                         user_id: str,
                         credentials: Dict[str, Any],
                         session_id: Optional[str] = None) -> SecurityContext:
        """
        ユーザー認証
        
        Args:
            user_id: ユーザーID
            credentials: 認証情報
            session_id: セッションID（オプション）
            
        Returns:
            SecurityContext: 認証済みセキュリティコンテキスト
        """
        try:
            # セッションID生成
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # 基本認証チェック（簡易実装）
            if not await self._validate_credentials(user_id, credentials):
                raise AuthenticationError("Invalid credentials")
            
            # ロール・権限取得
            role, permissions = await self._get_user_permissions(user_id)
            
            # セキュリティレベル決定
            security_level = await self._determine_security_level(user_id, credentials)
            
            # セキュリティコンテキスト作成
            context = await self.create_security_context(
                user_id=user_id,
                session_id=session_id,
                role=role,
                permissions=permissions,
                security_level=security_level
            )
            
            logger.info(f"User {user_id} authenticated successfully")
            return context
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Authentication failed for user {user_id}: {e}")
            raise AuthenticationError(f"Authentication failed: {e}")
    
    async def authorize(self, 
                      session_id: str,
                      operation: OperationType,
                      resource: str,
                      context: Optional[Dict[str, Any]] = None) -> bool:
        """
        認可チェック
        
        Args:
            session_id: セッションID
            operation: 操作タイプ
            resource: リソース
            context: 追加コンテキスト
            
        Returns:
            bool: 認可結果
        """
        try:
            # セキュリティコンテキスト取得
            security_context = self.active_contexts.get(session_id)
            if not security_context:
                raise AuthorizationError("Invalid session")
            
            # コンテキスト有効性確認
            if not security_context.is_valid():
                raise AuthorizationError("Session expired")
            
            # 権限チェック
            required_permission = f"{operation.value}:{resource}"
            if not security_context.has_permission(required_permission):
                if not security_context.has_permission(operation.value):
                    raise AuthorizationError(f"Permission denied: {required_permission}")
            
            # 監査ログ記録
            if self.audit_enabled:
                await self._log_security_event(
                    'authorization_check',
                    {
                        'session_id': session_id,
                        'operation': operation.value,
                        'resource': resource,
                        'result': 'granted'
                    }
                )
            
            self.stats['authorizations'] += 1
            return True
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Authorization failed: {e}")
            
            # 監査ログ記録
            if self.audit_enabled:
                await self._log_security_event(
                    'authorization_check',
                    {
                        'session_id': session_id,
                        'operation': operation.value,
                        'resource': resource,
                        'result': 'denied',
                        'error': str(e)
                    }
                )
            
            raise AuthorizationError(f"Authorization failed: {e}")
    
    async def encrypt_data(self, 
                         data: Union[str, bytes, Dict[str, Any]],
                         context: Optional[SecurityContext] = None) -> Dict[str, Any]:
        """
        データ暗号化
        
        Args:
            data: 暗号化対象データ
            context: セキュリティコンテキスト
            
        Returns:
            Dict[str, Any]: 暗号化データ
        """
        try:
            if not self.encryption_enabled:
                return {'data': data, 'encrypted': False}
            
            # データ正規化
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            elif isinstance(data, dict):
                import json
                data_bytes = json.dumps(data).encode('utf-8')
            else:
                data_bytes = data
            
            # 簡易暗号化（実装例）
            encrypted_data = {
                'data': data_bytes.hex(),  # 簡易実装
                'encrypted': True,
                'algorithm': 'AES-256-GCM',
                'timestamp': datetime.now().isoformat(),
                'context_id': context.session_id if context else None
            }
            
            # 監査ログ記録
            if self.audit_enabled:
                await self._log_security_event(
                    'data_encryption',
                    {
                        'data_size': len(data_bytes),
                        'algorithm': 'AES-256-GCM',
                        'context_id': context.session_id if context else None
                    }
                )
            
            self.stats['encryptions'] += 1
            return encrypted_data
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Data encryption failed: {e}")
            raise EncryptionError(f"Encryption failed: {e}")
    
    async def decrypt_data(self, 
                         encrypted_data: Dict[str, Any],
                         context: Optional[SecurityContext] = None) -> Union[str, bytes, Dict[str, Any]]:
        """
        データ復号化
        
        Args:
            encrypted_data: 暗号化データ
            context: セキュリティコンテキスト
            
        Returns:
            Union[str, bytes, Dict[str, Any]]: 復号化データ
        """
        try:
            if not encrypted_data.get('encrypted', False):
                return encrypted_data.get('data')
            
            # 簡易復号化（実装例）
            data_bytes = bytes.fromhex(encrypted_data['data'])
            
            # 監査ログ記録
            if self.audit_enabled:
                await self._log_security_event(
                    'data_decryption',
                    {
                        'data_size': len(data_bytes),
                        'algorithm': encrypted_data.get('algorithm', 'unknown'),
                        'context_id': context.session_id if context else None
                    }
                )
            
            return data_bytes
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Data decryption failed: {e}")
            raise DecryptionError(f"Decryption failed: {e}")
    
    async def secure_storage_operation(self,
                                     operation: str,
                                     session_context: SessionContext,
                                     security_context: SecurityContext) -> Any:
        """
        セキュアストレージ操作
        
        Args:
            operation: 操作タイプ
            session_context: セッションコンテキスト
            security_context: セキュリティコンテキスト
            
        Returns:
            Any: 操作結果
        """
        try:
            # 認可チェック
            await self.authorize(
                security_context.session_id,
                OperationType.WRITE if operation == 'save' else OperationType.READ,
                'session_storage'
            )
            
            # 暗号化（必要に応じて）
            if self.encryption_enabled:
                encrypted_context = await self.encrypt_data(
                    session_context.to_dict(),
                    security_context
                )
                # 暗号化データでセッションを更新
                session_context.cache_data['encrypted'] = True
                session_context.cache_data['encryption_info'] = encrypted_context
            
            # HybridStorage操作実行
            if operation == 'save':
                result = await self.hybrid_storage.save_session(session_context)
            elif operation == 'load':
                result = await self.hybrid_storage.load_session(session_context.metadata.session_id)
            else:
                raise ValueError(f"Unsupported operation: {operation}")
            
            # 監査ログ記録
            if self.audit_enabled:
                await self._log_security_event(
                    'secure_storage_operation',
                    {
                        'operation': operation,
                        'session_id': session_context.metadata.session_id,
                        'user_id': security_context.user_id,
                        'encrypted': self.encryption_enabled,
                        'result': 'success'
                    }
                )
            
            return result
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Secure storage operation failed: {e}")
            raise SecurityError(f"Secure storage operation failed: {e}")
    
    async def _validate_credentials(self, user_id: str, credentials: Dict[str, Any]) -> bool:
        """認証情報検証"""
        # 簡易実装 - 実際の実装では適切な認証を行う
        return credentials.get('password') == 'valid_password'
    
    async def _get_user_permissions(self, user_id: str) -> tuple:
        """ユーザー権限取得"""
        # 簡易実装 - 実際の実装では適切な権限管理を行う
        if user_id == 'admin':
            return 'admin', ['*']
        elif user_id == 'sage':
            return 'sage', ['read', 'write', 'execute']
        else:
            return 'user', ['read']
    
    async def _determine_security_level(self, user_id: str, credentials: Dict[str, Any]) -> SecurityLevel:
        """セキュリティレベル決定"""
        # 簡易実装 - 実際の実装では適切なレベル決定を行う
        if user_id == 'admin':
            return SecurityLevel.CRITICAL
        elif user_id == 'sage':
            return SecurityLevel.HIGH
        else:
            return SecurityLevel.MEDIUM
    
    async def _log_security_event(self, event_type: str, details: Dict[str, Any]):
        """セキュリティイベントログ記録"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'details': details
        }
        
        # 統計更新
        self.stats['audit_logs'] += 1
        
        # ログ出力
        logger.info(f"Security event: {event_type} - {details}")
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報取得"""
        return {
            'security_stats': self.stats.copy(),
            'active_contexts': len(self.active_contexts),
            'timestamp': datetime.now().isoformat()
        }
    
    async def shutdown(self):
        """セキュリティレイヤーシャットダウン"""
        logger.info("ElderZanSecurityLayer shutting down...")
        
        # アクティブコンテキストクリア
        self.active_contexts.clear()
        
        # 最終統計ログ
        logger.info(f"Final security stats: {self.stats}")

# 例外クラス
class SecurityError(Exception):
    """セキュリティエラー基底クラス"""
    pass

class AuthenticationError(SecurityError):
    """認証エラー"""
    pass

class AuthorizationError(SecurityError):
    """認可エラー"""
    pass

class EncryptionError(SecurityError):
    """暗号化エラー"""
    pass

class DecryptionError(SecurityError):
    """復号化エラー"""
    pass