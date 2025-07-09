#!/usr/bin/env python3
"""
統合認証専用ワーカー v1.0
AI Company Elder Hierarchy Authentication Worker

Elder階層システムの認証・セッション管理専用ワーカー
エルダーズ評議会承認済み
"""

import asyncio
import json
import time
import secrets
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Dict, Any, Optional, List, Tuple

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Elder階層システム統合
from core.elder_aware_base_worker import (
    ElderAwareBaseWorker,
    ElderTaskContext,
    ElderTaskResult,
    WorkerExecutionMode,
    ElderTaskPriority,
    elder_worker_required,
    SecurityError
)

# 統合認証システム
from libs.unified_auth_provider import (
    UnifiedAuthProvider,
    ElderRole,
    SageType,
    User,
    AuthSession,
    AuthRequest,
    AuthResult,
    create_demo_auth_system
)

# 既存システム統合
from core import BaseWorker, get_config, EMOJI
from libs.slack_notifier import SlackNotifier
import logging

# 認証専用絵文字
AUTH_EMOJI = {
    **EMOJI,
    'auth': '🔐',
    'session': '🎫',
    'mfa': '📱',
    'security': '🛡️',
    'key': '🔑',
    'lock': '🔒',
    'unlock': '🔓',
    'elder': '🏛️',
    'warning': '⚠️',
    'critical': '🚨'
}

# 認証アクションタイプ
class AuthActionType:
    """認証アクションタイプ定義"""
    LOGIN = "login"
    LOGOUT = "logout"
    REFRESH = "refresh_session"
    VALIDATE = "validate_token"
    MFA_ENABLE = "enable_mfa"
    MFA_VERIFY = "verify_mfa"
    SESSION_LIST = "list_sessions"
    SESSION_REVOKE = "revoke_sessions"
    USER_CREATE = "create_user"
    USER_UPDATE = "update_user"
    USER_DEACTIVATE = "deactivate_user"
    PERMISSION_CHECK = "check_permission"
    ELDER_PROMOTION = "elder_promotion"
    EMERGENCY_ACCESS = "emergency_access"


class AuthenticationWorker(ElderAwareBaseWorker):
    """
    統合認証専用ワーカー
    
    Elder階層システムの認証、セッション管理、権限管理を一元化
    """
    
    def __init__(self, worker_id: Optional[str] = None,
                 auth_provider: Optional[UnifiedAuthProvider] = None):
        # Elder階層BaseWorker初期化
        ElderAwareBaseWorker.__init__(
            self,
            auth_provider=auth_provider,
            required_elder_role=ElderRole.SAGE,
            required_sage_type=SageType.INCIDENT  # セキュリティはインシデント賢者の管轄
        )
        
        # ワーカー設定
        self.worker_type = 'authentication'
        self.worker_id = worker_id or f"auth_worker_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 認証専用キュー
        self.input_queue = 'ai_auth_requests'
        self.output_queue = 'ai_auth_responses'
        
        self.config = get_config()
        self.slack_notifier = SlackNotifier()
        
        # 認証統計
        self.auth_stats = {
            'total_requests': 0,
            'successful_logins': 0,
            'failed_logins': 0,
            'mfa_challenges': 0,
            'sessions_created': 0,
            'sessions_revoked': 0,
            'security_events': 0
        }
        
        # セキュリティ設定
        self.security_config = {
            'max_login_attempts': 5,
            'lockout_duration_minutes': 30,
            'session_timeout_hours': 24,
            'mfa_required_for_elders': True,
            'emergency_access_duration_minutes': 30,
            'audit_all_elder_actions': True
        }
        
        # レート制限設定
        self.rate_limits = {
            'login_per_minute': 10,
            'api_per_minute': 60,
            'emergency_per_hour': 3
        }
        
        # 活性セッション追跡
        self.active_sessions = {}
        
        self.logger.info(f"{AUTH_EMOJI['auth']} Authentication Worker initialized - Required: {self.required_elder_role.value}")
    
    async def process_auth_message(self, elder_context: ElderTaskContext,
                                  auth_data: Dict[str, Any]) -> ElderTaskResult:
        """認証メッセージ処理"""
        action_type = auth_data.get('action', AuthActionType.LOGIN)
        request_id = auth_data.get('request_id', 'unknown')
        
        # 認証アクションログ
        self.audit_logger.log_elder_action(
            elder_context,
            f"auth_action_start",
            f"Auth action: {action_type} - Request: {request_id}"
        )
        
        try:
            # アクションタイプ別処理
            if action_type == AuthActionType.LOGIN:
                result = await self._handle_login(elder_context, auth_data)
            elif action_type == AuthActionType.LOGOUT:
                result = await self._handle_logout(elder_context, auth_data)
            elif action_type == AuthActionType.REFRESH:
                result = await self._handle_session_refresh(elder_context, auth_data)
            elif action_type == AuthActionType.VALIDATE:
                result = await self._handle_token_validation(elder_context, auth_data)
            elif action_type == AuthActionType.MFA_ENABLE:
                result = await self._handle_mfa_enable(elder_context, auth_data)
            elif action_type == AuthActionType.MFA_VERIFY:
                result = await self._handle_mfa_verify(elder_context, auth_data)
            elif action_type == AuthActionType.SESSION_LIST:
                result = await self._handle_session_list(elder_context, auth_data)
            elif action_type == AuthActionType.SESSION_REVOKE:
                result = await self._handle_session_revoke(elder_context, auth_data)
            elif action_type == AuthActionType.USER_CREATE:
                result = await self._handle_user_create(elder_context, auth_data)
            elif action_type == AuthActionType.USER_UPDATE:
                result = await self._handle_user_update(elder_context, auth_data)
            elif action_type == AuthActionType.USER_DEACTIVATE:
                result = await self._handle_user_deactivate(elder_context, auth_data)
            elif action_type == AuthActionType.PERMISSION_CHECK:
                result = await self._handle_permission_check(elder_context, auth_data)
            elif action_type == AuthActionType.ELDER_PROMOTION:
                result = await self._handle_elder_promotion(elder_context, auth_data)
            elif action_type == AuthActionType.EMERGENCY_ACCESS:
                result = await self._handle_emergency_access(elder_context, auth_data)
            else:
                raise ValueError(f"Unknown auth action: {action_type}")
            
            # 統計更新
            self._update_auth_stats(action_type, success=True)
            
            # 成功ログ
            self.audit_logger.log_elder_action(
                elder_context,
                f"auth_action_complete",
                f"Auth action {action_type} completed successfully"
            )
            
            return result
            
        except Exception as e:
            # 統計更新
            self._update_auth_stats(action_type, success=False)
            
            # エラーログ
            self.audit_logger.log_elder_action(
                elder_context,
                f"auth_action_error",
                f"Auth action {action_type} failed: {str(e)}"
            )
            
            self.audit_logger.log_security_event(
                elder_context,
                "auth_error",
                {"action": action_type, "error": str(e), "request_id": request_id}
            )
            
            raise
    
    async def _handle_login(self, context: ElderTaskContext, auth_data: Dict) -> Dict:
        """ログイン処理"""
        username = auth_data.get('username', '')
        password = auth_data.get('password', '')
        mfa_token = auth_data.get('mfa_token')
        device_info = auth_data.get('device_info', {})
        ip_address = auth_data.get('ip_address', 'unknown')
        remember_me = auth_data.get('remember_me', False)
        
        # レート制限チェック
        if not self._check_rate_limit('login', ip_address):
            self.audit_logger.log_security_event(
                context,
                "rate_limit_exceeded",
                {"action": "login", "ip": ip_address}
            )
            raise SecurityError("Login rate limit exceeded")
        
        # 認証リクエスト作成
        auth_request = AuthRequest(
            username=username,
            password=password,
            mfa_token=mfa_token,
            device_info=device_info,
            ip_address=ip_address,
            remember_me=remember_me
        )
        
        # 認証実行
        result, session, user = self.auth_provider.authenticate(auth_request)
        
        if result == AuthResult.SUCCESS:
            # セッション追跡
            self.active_sessions[session.session_id] = {
                'user_id': user.id,
                'username': user.username,
                'elder_role': user.elder_role.value,
                'created_at': datetime.now().isoformat()
            }
            
            # Elder階層セキュリティ通知
            if user.elder_role in [ElderRole.GRAND_ELDER, ElderRole.CLAUDE_ELDER]:
                await self._send_elder_login_notification(user, ip_address, device_info)
            
            return {
                'status': 'success',
                'user': user.to_dict() if hasattr(user, 'to_dict') else {
                    'id': user.id,
                    'username': user.username,
                    'elder_role': user.elder_role.value,
                    'sage_type': user.sage_type.value if user.sage_type else None
                },
                'session': {
                    'token': session.token,
                    'refresh_token': session.refresh_token,
                    'expires_at': session.expires_at.isoformat()
                }
            }
        
        elif result == AuthResult.MFA_REQUIRED:
            self.auth_stats['mfa_challenges'] += 1
            return {
                'status': 'mfa_required',
                'message': 'MFA token required for authentication'
            }
        
        elif result == AuthResult.ACCOUNT_LOCKED:
            self.audit_logger.log_security_event(
                context,
                "account_locked",
                {"username": username, "ip": ip_address}
            )
            return {
                'status': 'account_locked',
                'message': 'Account is temporarily locked'
            }
        
        else:
            self.auth_stats['failed_logins'] += 1
            return {
                'status': 'failed',
                'message': 'Invalid credentials'
            }
    
    async def _handle_logout(self, context: ElderTaskContext, auth_data: Dict) -> Dict:
        """ログアウト処理"""
        session_id = auth_data.get('session_id')
        
        if not session_id:
            raise ValueError("Session ID required for logout")
        
        # ログアウト実行
        success = self.auth_provider.logout(session_id)
        
        if success:
            # セッション追跡から削除
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            return {
                'status': 'success',
                'message': 'Logged out successfully'
            }
        else:
            return {
                'status': 'failed',
                'message': 'Invalid session'
            }
    
    async def _handle_session_refresh(self, context: ElderTaskContext, auth_data: Dict) -> Dict:
        """セッション更新処理"""
        refresh_token = auth_data.get('refresh_token')
        
        if not refresh_token:
            raise ValueError("Refresh token required")
        
        # セッション更新
        success, session = self.auth_provider.refresh_session(refresh_token)
        
        if success:
            return {
                'status': 'success',
                'session': {
                    'token': session.token,
                    'expires_at': session.expires_at.isoformat()
                }
            }
        else:
            return {
                'status': 'failed',
                'message': 'Invalid or expired refresh token'
            }
    
    async def _handle_token_validation(self, context: ElderTaskContext, auth_data: Dict) -> Dict:
        """トークン検証処理"""
        token = auth_data.get('token')
        
        if not token:
            raise ValueError("Token required for validation")
        
        # トークン検証
        is_valid, user, session = self.auth_provider.validate_token(token)
        
        if is_valid:
            return {
                'status': 'valid',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'elder_role': user.elder_role.value,
                    'permissions': self.auth_provider.elder_integration.get_permitted_actions(user)
                }
            }
        else:
            return {
                'status': 'invalid',
                'message': 'Invalid or expired token'
            }
    
    @elder_worker_required(ElderRole.SAGE)
    async def _handle_mfa_enable(self, context: ElderTaskContext, auth_data: Dict) -> Dict:
        """MFA有効化処理"""
        user_id = auth_data.get('user_id')
        
        if not user_id:
            raise ValueError("User ID required for MFA enable")
        
        # MFA有効化
        provisioning_uri = self.auth_provider.enable_mfa_for_user(user_id)
        
        return {
            'status': 'success',
            'provisioning_uri': provisioning_uri,
            'message': 'MFA enabled successfully'
        }
    
    async def _handle_mfa_verify(self, context: ElderTaskContext, auth_data: Dict) -> Dict:
        """MFA検証処理"""
        user_id = auth_data.get('user_id')
        mfa_token = auth_data.get('mfa_token')
        
        if not user_id or not mfa_token:
            raise ValueError("User ID and MFA token required")
        
        # ユーザー取得
        user = self.auth_provider.users.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        # MFA検証
        is_valid = self.auth_provider._verify_mfa(user, mfa_token)
        
        if is_valid:
            return {
                'status': 'success',
                'message': 'MFA verified successfully'
            }
        else:
            return {
                'status': 'failed',
                'message': 'Invalid MFA token'
            }
    
    async def _handle_session_list(self, context: ElderTaskContext, auth_data: Dict) -> Dict:
        """セッション一覧取得処理"""
        user_id = auth_data.get('user_id')
        
        if not user_id:
            # 現在のユーザーのセッション
            user_id = context.user.id
        
        # 権限チェック
        if user_id != context.user.id and context.user.elder_role not in [ElderRole.GRAND_ELDER, ElderRole.CLAUDE_ELDER]:
            raise PermissionError("Insufficient permissions to view other user's sessions")
        
        # アクティブセッション取得
        sessions = self.auth_provider.get_active_sessions(user_id)
        
        return {
            'status': 'success',
            'sessions': [
                {
                    'session_id': s.session_id,
                    'created_at': s.created_at.isoformat() if hasattr(s.created_at, 'isoformat') else str(s.created_at),
                    'expires_at': s.expires_at.isoformat(),
                    'ip_address': s.ip_address,
                    'device_info': s.device_info
                }
                for s in sessions
            ]
        }
    
    @elder_worker_required(ElderRole.CLAUDE_ELDER)
    async def _handle_session_revoke(self, context: ElderTaskContext, auth_data: Dict) -> Dict:
        """セッション取り消し処理"""
        user_id = auth_data.get('user_id')
        
        if not user_id:
            raise ValueError("User ID required for session revocation")
        
        # 全セッション取り消し
        revoked_count = self.auth_provider.revoke_all_sessions(user_id)
        
        # セキュリティ通知
        await self._send_security_notification(
            context,
            f"All sessions revoked for user {user_id} by {context.user.username}"
        )
        
        return {
            'status': 'success',
            'revoked_count': revoked_count,
            'message': f'Revoked {revoked_count} sessions'
        }
    
    @elder_worker_required(ElderRole.CLAUDE_ELDER)
    async def _handle_user_create(self, context: ElderTaskContext, auth_data: Dict) -> Dict:
        """ユーザー作成処理"""
        username = auth_data.get('username')
        password = auth_data.get('password')
        email = auth_data.get('email')
        elder_role = ElderRole(auth_data.get('elder_role', 'servant'))
        sage_type = SageType(auth_data.get('sage_type')) if auth_data.get('sage_type') else None
        
        # 権限チェック - グランドエルダーのみが他のエルダーを作成可能
        if elder_role in [ElderRole.GRAND_ELDER, ElderRole.CLAUDE_ELDER] and context.user.elder_role != ElderRole.GRAND_ELDER:
            raise PermissionError("Only Grand Elder can create other Elders")
        
        # ユーザー作成
        user = self.auth_provider.create_user(
            username=username,
            password=password,
            email=email,
            elder_role=elder_role,
            sage_type=sage_type
        )
        
        # 作成通知
        await self._send_security_notification(
            context,
            f"New user created: {username} ({elder_role.value}) by {context.user.username}"
        )
        
        return {
            'status': 'success',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'elder_role': user.elder_role.value,
                'sage_type': user.sage_type.value if user.sage_type else None
            }
        }
    
    @elder_worker_required(ElderRole.GRAND_ELDER)
    async def _handle_elder_promotion(self, context: ElderTaskContext, auth_data: Dict) -> Dict:
        """Elder階層昇格処理"""
        user_id = auth_data.get('user_id')
        new_elder_role = ElderRole(auth_data.get('new_elder_role'))
        new_sage_type = SageType(auth_data.get('new_sage_type')) if auth_data.get('new_sage_type') else None
        promotion_reason = auth_data.get('reason', 'Elder Council Decision')
        
        # ユーザー取得
        if user_id not in self.auth_provider.users:
            raise ValueError("User not found")
        
        user = self.auth_provider.users[user_id]
        old_role = user.elder_role
        
        # 昇格実行
        user.elder_role = new_elder_role
        user.sage_type = new_sage_type
        
        # 昇格ログ
        self.audit_logger.log_elder_action(
            context,
            "elder_promotion",
            f"User {user.username} promoted from {old_role.value} to {new_elder_role.value}"
        )
        
        # エルダーズ評議会通知
        await self._send_elder_council_notification(
            f"🏛️ **ELDER PROMOTION**\n"
            f"User: {user.username}\n"
            f"From: {old_role.value}\n"
            f"To: {new_elder_role.value}\n"
            f"By: {context.user.username}\n"
            f"Reason: {promotion_reason}"
        )
        
        return {
            'status': 'success',
            'promotion': {
                'user': user.username,
                'old_role': old_role.value,
                'new_role': new_elder_role.value,
                'sage_type': new_sage_type.value if new_sage_type else None,
                'promoted_by': context.user.username,
                'timestamp': datetime.now().isoformat()
            }
        }
    
    @elder_worker_required(ElderRole.GRAND_ELDER)
    async def _handle_emergency_access(self, context: ElderTaskContext, auth_data: Dict) -> Dict:
        """緊急アクセス処理"""
        target_user_id = auth_data.get('target_user_id')
        emergency_reason = auth_data.get('reason', 'Emergency access required')
        duration_minutes = auth_data.get('duration_minutes', self.security_config['emergency_access_duration_minutes'])
        
        # レート制限チェック
        if not self._check_rate_limit('emergency', context.user.username):
            raise SecurityError("Emergency access rate limit exceeded")
        
        # 緊急アクセス記録
        self.audit_logger.log_security_event(
            context,
            "emergency_access_granted",
            {
                "target_user": target_user_id,
                "granted_by": context.user.username,
                "reason": emergency_reason,
                "duration_minutes": duration_minutes,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # 緊急セッション作成（実装簡略化）
        emergency_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(minutes=duration_minutes)
        
        # 緊急通知
        await self._send_emergency_notification(
            f"🚨 **EMERGENCY ACCESS GRANTED**\n"
            f"Target: User {target_user_id}\n"
            f"By: {context.user.username}\n"
            f"Reason: {emergency_reason}\n"
            f"Duration: {duration_minutes} minutes\n"
            f"Expires: {expires_at.isoformat()}"
        )
        
        return {
            'status': 'success',
            'emergency_access': {
                'token': emergency_token,
                'expires_at': expires_at.isoformat(),
                'target_user': target_user_id,
                'granted_by': context.user.username
            }
        }
    
    def _check_rate_limit(self, action: str, identifier: str) -> bool:
        """レート制限チェック"""
        # 実際の実装では Redis 等でレート制限を管理
        # ここでは簡略化
        return True
    
    def _update_auth_stats(self, action: str, success: bool):
        """認証統計更新"""
        self.auth_stats['total_requests'] += 1
        
        if action == AuthActionType.LOGIN:
            if success:
                self.auth_stats['successful_logins'] += 1
            else:
                self.auth_stats['failed_logins'] += 1
        elif action == AuthActionType.SESSION_REVOKE:
            if success:
                self.auth_stats['sessions_revoked'] += 1
    
    async def _send_elder_login_notification(self, user: User, ip_address: str, device_info: Dict):
        """Elder ログイン通知"""
        message = f"""
{AUTH_EMOJI['elder']} **ELDER LOGIN NOTIFICATION**

**User**: {user.username} ({user.elder_role.value})
**IP Address**: {ip_address}
**Device**: {device_info.get('type', 'unknown')}
**Time**: {datetime.now().isoformat()}

{AUTH_EMOJI['security']} High-privilege login detected
"""
        
        await self.slack_notifier.send_message(
            message=message,
            channel='#elder-security-alerts'
        )
    
    async def _send_security_notification(self, context: ElderTaskContext, message: str):
        """セキュリティ通知"""
        enhanced_message = f"{AUTH_EMOJI['security']} [{context.user.username}] {message}"
        await self.slack_notifier.send_message(
            message=enhanced_message,
            channel='#security-notifications'
        )
    
    async def _send_elder_council_notification(self, message: str):
        """エルダーズ評議会通知"""
        await self.slack_notifier.send_message(
            message=message,
            channel='#elder-council-notifications'
        )
    
    async def _send_emergency_notification(self, message: str):
        """緊急通知"""
        await self.slack_notifier.send_message(
            message=message,
            channel='#emergency-alerts',
            priority='critical'
        )
    
    async def _handle_permission_check(self, context: ElderTaskContext, auth_data: Dict) -> Dict:
        """権限チェック処理"""
        user_id = auth_data.get('user_id', context.user.id)
        required_elder_role = ElderRole(auth_data.get('required_elder_role', 'servant'))
        required_sage_type = SageType(auth_data.get('required_sage_type')) if auth_data.get('required_sage_type') else None
        
        # ユーザー取得
        if user_id not in self.auth_provider.users:
            return {
                'status': 'failed',
                'message': 'User not found',
                'has_permission': False
            }
        
        user = self.auth_provider.users[user_id]
        
        # Elder階層権限チェック
        has_elder_permission = self.auth_provider.check_elder_permission(user, required_elder_role)
        
        # 賢者権限チェック（必要な場合）
        has_sage_permission = True
        if required_sage_type:
            has_sage_permission = self.auth_provider.check_sage_permission(user, required_sage_type)
        
        has_permission = has_elder_permission and has_sage_permission
        
        return {
            'status': 'success',
            'has_permission': has_permission,
            'user_role': user.elder_role.value,
            'user_sage_type': user.sage_type.value if user.sage_type else None,
            'required_role': required_elder_role.value,
            'required_sage_type': required_sage_type.value if required_sage_type else None
        }
    
    @elder_worker_required(ElderRole.CLAUDE_ELDER)
    async def _handle_user_update(self, context: ElderTaskContext, auth_data: Dict) -> Dict:
        """ユーザー更新処理"""
        user_id = auth_data.get('user_id')
        update_data = auth_data.get('update_data', {})
        
        if not user_id:
            raise ValueError("User ID required for update")
        
        # 更新実行
        updated_user = self.auth_provider.update_user(user_id, **update_data)
        
        # 更新通知
        await self._send_security_notification(
            context,
            f"User {updated_user.username} updated by {context.user.username}"
        )
        
        return {
            'status': 'success',
            'user': {
                'id': updated_user.id,
                'username': updated_user.username,
                'email': updated_user.email,
                'elder_role': updated_user.elder_role.value
            }
        }
    
    @elder_worker_required(ElderRole.CLAUDE_ELDER)
    async def _handle_user_deactivate(self, context: ElderTaskContext, auth_data: Dict) -> Dict:
        """ユーザー無効化処理"""
        user_id = auth_data.get('user_id')
        reason = auth_data.get('reason', 'Administrative action')
        
        if not user_id:
            raise ValueError("User ID required for deactivation")
        
        # グランドエルダーは無効化不可
        user = self.auth_provider.users.get(user_id)
        if user and user.elder_role == ElderRole.GRAND_ELDER:
            raise PermissionError("Cannot deactivate Grand Elder")
        
        # 無効化実行
        self.auth_provider.deactivate_user(user_id)
        
        # セキュリティイベント記録
        self.audit_logger.log_security_event(
            context,
            "user_deactivated",
            {
                "user_id": user_id,
                "deactivated_by": context.user.username,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # 通知
        await self._send_security_notification(
            context,
            f"User {user_id} deactivated. Reason: {reason}"
        )
        
        return {
            'status': 'success',
            'message': f'User {user_id} deactivated successfully'
        }


# ファクトリー関数
def create_authentication_worker(auth_provider: Optional[UnifiedAuthProvider] = None) -> AuthenticationWorker:
    """認証ワーカー作成"""
    return AuthenticationWorker(auth_provider=auth_provider)


# デモ実行関数
async def demo_authentication_worker():
    """認証ワーカーのデモ実行"""
    print(f"{AUTH_EMOJI['start']} Authentication Worker Demo Starting...")
    
    # デモ認証システム
    auth = create_demo_auth_system()
    
    # 認証ワーカー作成
    worker = create_authentication_worker(auth_provider=auth)
    
    # インシデント賢者として認証
    auth_request = AuthRequest(username="incident_sage", password="incident_password")
    result, session, user = auth.authenticate(auth_request)
    
    if result.value == "success":
        print(f"{AUTH_EMOJI['success']} Authenticated as Incident Sage: {user.username}")
        
        # 認証コンテキスト作成
        context = worker.create_elder_context(
            user=user,
            session=session,
            task_id="demo_auth_001",
            priority=ElderTaskPriority.HIGH
        )
        
        # デモ認証リクエスト
        demo_auth_data = {
            "action": AuthActionType.LOGIN,
            "request_id": "demo_auth_001",
            "username": "servant1",
            "password": "servant_password",
            "ip_address": "127.0.0.1",
            "device_info": {"type": "demo", "browser": "CLI"}
        }
        
        # 認証処理実行
        async def demo_auth_task():
            return await worker.process_auth_message(context, demo_auth_data)
        
        result = await worker.execute_with_elder_context(context, demo_auth_task)
        
        print(f"{AUTH_EMOJI['complete']} Demo Authentication Result:")
        print(f"  Status: {result.status}")
        print(f"  Auth Stats: {worker.auth_stats}")
        print(f"  Active Sessions: {len(worker.active_sessions)}")
        
    else:
        print(f"{AUTH_EMOJI['error']} Authentication failed: {result}")


if __name__ == "__main__":
    # デモ実行
    asyncio.run(demo_authentication_worker())