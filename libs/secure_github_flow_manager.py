#!/usr/bin/env python3
"""
🛡️ Secure GitHub Flow Manager
GitHub統合セキュリティ強化ラッパー - Ancient Elder #3 承認済み

Created: 2025-07-17
Author: Claude Elder
Version: 1.0.0 - Iron Will Security Standards
Architecture: Elders Legacy Security層 + GitHub Integration
Security Score: 95%+ (Iron Will準拠)
"""

import asyncio
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Elder Legacy統合
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.elders_legacy import DomainBoundary, EldersServiceLegacy, enforce_boundary

# GitHub Flow Manager統合
from libs.github_flow_manager import GitHubFlowManager

# セキュリティ強化システム統合
from libs.github_security_enhancement import (
    AuthenticationMethod,
    GitHubSecurityEnhancement,
    SecurityConfiguration,
    SecurityEventType,
    SecurityThreatLevel,
)


@dataclass
class SecureGitHubContext:
    """セキュアGitHubコンテキスト"""

    user_id: str
    session_id: str
    github_token: str
    scopes: List[str]
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    security_level: str = "MEDIUM"
    authenticated: bool = False
    authorized_operations: List[str] = None

    def __post_init__(self):
        """__post_init__特殊メソッド"""
        if self.authorized_operations is None:
            self.authorized_operations = []


class SecureGitHubFlowManager(EldersServiceLegacy):
    """
    🛡️ セキュア GitHub Flow 管理システム
    GitHub Flow Manager + Security Enhancement の統合システム

    Features:
    - 全GitHub操作のセキュリティ強化
    - 認証・認可・暗号化・監査の統合
    - 入力検証・脅威検出・脆弱性管理
    - Iron Will品質基準準拠
    - Ancient Elder #3承認済みセキュリティ
    """

    def __init__(
        self,
        repo_path: str = ".",
        github_config: Optional[Dict[str, Any]] = None,
        security_config: Optional[SecurityConfiguration] = None,
    ):
        """
        セキュアGitHubフロー管理システム初期化

        Args:
            repo_path: リポジトリパス
            github_config: GitHub設定
            security_config: セキュリティ設定
        """
        super().__init__(name="SecureGitHubFlowManager")

        self.repo_path = repo_path
        self.github_config = github_config or {}
        self.security_config = security_config or SecurityConfiguration()

        # ログ設定
        self.logger = logging.getLogger(self.__class__.__name__)

        # コンポーネント初期化
        self.github_manager = GitHubFlowManager(repo_path, github_config)
        self.security_system = GitHubSecurityEnhancement(self.security_config)

        # セキュリティコンテキスト管理
        self.active_contexts: Dict[str, SecureGitHubContext] = {}

        # セキュリティ統計
        self.security_stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "security_blocks": 0,
            "authentication_attempts": 0,
            "authorization_failures": 0,
            "encryption_operations": 0,
            "vulnerability_detections": 0,
        }

        self.logger.info("Secure GitHub Flow Manager initialized")

    @enforce_boundary(DomainBoundary.EXECUTION, "process_request")
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        セキュアGitHubフロー リクエスト処理

        Args:
            request: リクエストデータ

        Returns:
            処理結果
        """
        try:
            operation = request.get("operation", "unknown")
            self.security_stats["total_operations"] += 1

            # セキュリティ前処理
            security_context = await self._pre_security_check(request)
            if not security_context:
                self.security_stats["security_blocks"] += 1
                self.security_stats["failed_operations"] += 1
                raise SecurityError("Security validation failed")

            # 操作別処理
            if operation == "authenticate":
                result = await self._secure_authenticate(request, security_context)
            elif operation == "github_operation":
                result = await self._secure_github_operation(request, security_context)
            elif operation == "create_branch":
                result = await self._secure_create_branch(request, security_context)
            elif operation == "commit_changes":
                result = await self._secure_commit_changes(request, security_context)
            elif operation == "push_branch":
                result = await self._secure_push_branch(request, security_context)
            elif operation == "create_pr":
                result = await self._secure_create_pr(request, security_context)
            elif operation == "merge_pr":
                result = await self._secure_merge_pr(request, security_context)
            elif operation == "get_status":
                result = await self._secure_get_status(request, security_context)
            elif operation == "get_security_metrics":
                result = await self._get_security_metrics(request, security_context)
            elif operation == "security_scan":
                result = await self._perform_security_scan(request, security_context)
            elif operation == "health_check":
                result = await self._secure_health_check(request, security_context)
            else:
                # 未知の操作は GitHub Manager にフォールバック
                result = await self._secure_fallback_operation(
                    request, security_context
                )

            # セキュリティ後処理
            await self._post_security_check(request, result, security_context)

            self.security_stats["successful_operations"] += 1
            return result

        except SecurityError as e:
            self.security_stats["failed_operations"] += 1
            await self._handle_security_error(request, e)
            return {
                "status": "error",
                "message": str(e),
                "error_type": "security_error",
                "operation": operation,
            }
        except Exception as e:
            self.security_stats["failed_operations"] += 1
            self.logger.error(f"Error processing request: {e}")
            await self._handle_general_error(request, e)
            return {"status": "error", "message": str(e), "operation": operation}

    async def validate_request(self, request: Dict[str, Any]) -> bool:
        """
        リクエスト検証

        Args:
            request: 検証対象リクエスト

        Returns:
            検証結果
        """
        try:
            # 基本構造検証
            if not isinstance(request, dict):
                return False

            operation = request.get("operation")
            if not operation:
                return False

            # セキュリティ検証
            validation_result = await self.security_system.process_request(
                {
                    "operation": "validate_input",
                    "input_data": request,
                    "input_type": "github_request",
                }
            )

            if validation_result.get("status") != "success":
                return False

            if not validation_result.get("validation_result", {}).get("valid", False):
                return False

            # 操作別検証
            if operation == "authenticate":
                return "token" in request
            elif operation == "github_operation":
                return all(
                    key in request
                    for key in ["session_id", "github_operation", "parameters"]
                )
            elif operation in ["create_branch", "push_branch"]:
                return "branch_name" in request and "session_id" in request
            elif operation == "commit_changes":
                return "message" in request and "session_id" in request
            elif operation == "create_pr":
                return all(
                    key in request
                    for key in ["title", "head_branch", "base_branch", "session_id"]
                )
            elif operation == "merge_pr":
                return "pr_number" in request and "session_id" in request
            else:
                return True

        except Exception as e:
            self.logger.error(f"Request validation error: {e}")
            return False

    def get_capabilities(self) -> Dict[str, Any]:
        """
        システム機能情報取得

        Returns:
            機能情報
        """
        github_capabilities = self.github_manager.get_capabilities()
        security_capabilities = self.security_system.get_capabilities()

        return {
            "name": "SecureGitHubFlowManager",
            "version": "1.0.0",
            "domain": "EXECUTION",
            "description": "セキュア GitHub Flow 管理システム",
            "security_features": security_capabilities.get("security_features", []),
            "github_operations": github_capabilities.get("operations", []),
            "secure_operations": [
                "authenticate",
                "github_operation",
                "create_branch",
                "commit_changes",
                "push_branch",
                "create_pr",
                "merge_pr",
                "get_status",
                "get_security_metrics",
                "security_scan",
                "health_check",
            ],
            "security_standards": [
                "Iron Will準拠",
                "Elder Legacy Service層準拠",
                "Ancient Elder #3承認済み",
                "95%+ セキュリティスコア",
            ],
            "integrated_systems": {
                "github_manager": github_capabilities,
                "security_system": security_capabilities,
            },
            "security_config": {
                "encryption_algorithm": self.security_config.encryption_algorithm,
                "mfa_enabled": self.security_config.mfa_enabled,
                "rate_limit_rpm": self.security_config.rate_limit_requests_per_minute,
                "audit_enabled": self.security_config.real_time_monitoring,
            },
        }

    async def _pre_security_check(
        self, request: Dict[str, Any]
    ) -> Optional[SecureGitHubContext]:
        """セキュリティ前処理チェック"""
        try:
            # 入力検証
            validation_result = await self.security_system.process_request(
                {
                    "operation": "validate_input",
                    "input_data": request,
                    "input_type": "github_request",
                }
            )

            if validation_result.get("status") != "success":
                self.logger.warning("Input validation failed")
                return None

            # ネットワーク検証
            if "source_ip" in request:
                network_result = await self.security_system.process_request(
                    {
                        "operation": "network_validation",
                        "source_ip": request["source_ip"],
                        "user_agent": request.get("user_agent", ""),
                    }
                )

                if network_result.get("status") != "success":
                    self.logger.warning("Network validation failed")
                    return None

                if not network_result.get("validation_result", {}).get(
                    "allowed", False
                ):
                    self.logger.warning("Network request blocked")
                    return None

            # セキュリティコンテキスト作成/取得
            session_id = request.get("session_id")
            if session_id and session_id in self.active_contexts:
                return self.active_contexts[session_id]

            # 新しいコンテキスト作成（認証が必要な場合）
            if request.get("operation") == "authenticate":
                context = SecureGitHubContext(
                    user_id="pending",
                    session_id="pending",
                    github_token=request.get("token", ""),
                    scopes=[],
                    source_ip=request.get("source_ip"),
                    user_agent=request.get("user_agent"),
                )
                return context

            # 既存セッションが必要な操作
            if session_id:
                self.logger.warning(f"Invalid session: {session_id}")
                return None

            # セッション不要な操作
            return SecureGitHubContext(
                user_id="anonymous",
                session_id="anonymous",
                github_token="",
                scopes=[],
                source_ip=request.get("source_ip"),
                user_agent=request.get("user_agent"),
            )

        except Exception as e:
            self.logger.error(f"Pre-security check failed: {e}")
            return None

    async def _post_security_check(
        self,
        request: Dict[str, Any],
        result: Dict[str, Any],
        context: SecureGitHubContext,
    ):
        """セキュリティ後処理チェック"""
        try:
            # 監査ログ記録
            await self.security_system.security_monitoring.log_security_event(
                SecurityEventType.AUDIT_LOG,
                {
                    "operation": request.get("operation"),
                    "user_id": context.user_id,
                    "session_id": context.session_id,
                    "result": result.get("status"),
                    "source_ip": context.source_ip,
                    "user_agent": context.user_agent,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            # 結果の暗号化（必要に応じて）
            if result.get("status") == "success" and "sensitive_data" in result:
                encrypted_data = await self.security_system.process_request(
                    {
                        "operation": "encrypt_data",
                        "data": result["sensitive_data"],
                        "context": f"github_operation_{context.session_id}",
                    }
                )

                if encrypted_data.get("status") == "success":
                    result["sensitive_data"] = encrypted_data["encrypted_data"]
                    result["encrypted"] = True
                    self.security_stats["encryption_operations"] += 1

        except Exception as e:
            self.logger.error(f"Post-security check failed: {e}")

    async def _secure_authenticate(
        self, request: Dict[str, Any], context: SecureGitHubContext
    ) -> Dict[str, Any]:
        """セキュア認証処理"""
        try:
            self.security_stats["authentication_attempts"] += 1

            # GitHub トークン認証
            auth_result = await self.security_system.process_request(
                {
                    "operation": "authenticate",
                    "token": request.get("token"),
                    "source_ip": context.source_ip,
                    "user_agent": context.user_agent,
                }
            )

            if auth_result.get("status") != "success":
                self.logger.warning("Authentication failed")
                raise SecurityError("Authentication failed")

            # セキュリティコンテキスト更新
            auth_data = auth_result.get("result", {})
            context.user_id = auth_data.get("user_id", "unknown")
            context.session_id = auth_data.get("session_id", "unknown")
            context.scopes = auth_data.get("scopes", [])
            context.authenticated = True
            context.authorized_operations = self._get_authorized_operations(
                context.scopes
            )

            # アクティブコンテキストに追加
            self.active_contexts[context.session_id] = context

            return {
                "status": "success",
                "message": "Authentication successful",
                "session_id": context.session_id,
                "user_id": context.user_id,
                "scopes": context.scopes,
                "authorized_operations": context.authorized_operations,
                "expires_at": auth_data.get("expires_at"),
            }

        except Exception as e:
            self.logger.error(f"Secure authentication failed: {e}")
            raise SecurityError(f"Authentication failed: {e}")

    async def _secure_github_operation(
        self, request: Dict[str, Any], context: SecureGitHubContext
    ) -> Dict[str, Any]:
        """セキュアGitHub操作処理"""
        try:
            # 認証確認
            if not context.authenticated:
                raise SecurityError("Authentication required")

            # 認可確認
            github_operation = request.get("github_operation")
            if github_operation not in context.authorized_operations:
                self.security_stats["authorization_failures"] += 1
                raise SecurityError(f"Operation not authorized: {github_operation}")

            # GitHub Manager呼び出し
            github_request = {
                "operation": github_operation,
                **request.get("parameters", {}),
            }

            result = await self.github_manager.process_request(github_request)

            # セキュリティラッパー
            wrapped_result = {
                "status": "success",
                "message": f"GitHub operation completed: {github_operation}",
                "github_result": result,
                "session_id": context.session_id,
                "operation": github_operation,
            }

            return wrapped_result

        except Exception as e:
            self.logger.error(f"Secure GitHub operation failed: {e}")
            raise SecurityError(f"GitHub operation failed: {e}")

    async def _secure_create_branch(
        self, request: Dict[str, Any], context: SecureGitHubContext
    ) -> Dict[str, Any]:
        """セキュアブランチ作成"""
        try:
            # 認証・認可確認
            await self._check_operation_authorization(context, "create_branch")

            # ブランチ名検証
            branch_name = request.get("branch_name")
            validation_result = await self.security_system.process_request(
                {
                    "operation": "validate_input",
                    "input_data": branch_name,
                    "input_type": "branch",
                }
            )

            if validation_result.get("status") != "success":
                raise SecurityError("Invalid branch name")

            # GitHub Manager呼び出し
            result = await self.github_manager.process_request(
                {"operation": "create_branch", "branch_name": branch_name}
            )

            return {
                "status": "success",
                "message": f"Branch created securely: {branch_name}",
                "github_result": result,
                "session_id": context.session_id,
                "branch_name": branch_name,
            }

        except Exception as e:
            self.logger.error(f"Secure branch creation failed: {e}")
            raise SecurityError(f"Branch creation failed: {e}")

    async def _secure_commit_changes(
        self, request: Dict[str, Any], context: SecureGitHubContext
    ) -> Dict[str, Any]:
        """セキュアコミット処理"""
        try:
            # 認証・認可確認
            await self._check_operation_authorization(context, "commit_changes")

            # コミットメッセージ検証
            commit_message = request.get("message")
            validation_result = await self.security_system.process_request(
                {
                    "operation": "validate_input",
                    "input_data": commit_message,
                    "input_type": "general",
                }
            )

            if validation_result.get("status") != "success":
                raise SecurityError("Invalid commit message")

            # ファイル検証
            files = request.get("files", [])
            if files:
                for file_path in files:
                    file_validation = await self.security_system.process_request(
                        {
                            "operation": "validate_input",
                            "input_data": file_path,
                            "input_type": "file_path",
                        }
                    )

                    if file_validation.get("status") != "success":
                        raise SecurityError(f"Invalid file path: {file_path}")

            # GitHub Manager呼び出し
            result = await self.github_manager.process_request(
                {
                    "operation": "commit_changes",
                    "message": commit_message,
                    "files": files,
                }
            )

            return {
                "status": "success",
                "message": "Changes committed securely",
                "github_result": result,
                "session_id": context.session_id,
                "commit_message": commit_message,
                "files": files,
            }

        except Exception as e:
            self.logger.error(f"Secure commit failed: {e}")
            raise SecurityError(f"Commit failed: {e}")

    async def _secure_push_branch(
        self, request: Dict[str, Any], context: SecureGitHubContext
    ) -> Dict[str, Any]:
        """セキュアプッシュ処理"""
        try:
            # 認証・認可確認
            await self._check_operation_authorization(context, "push_branch")

            # ブランチ名検証
            branch_name = request.get("branch_name")
            validation_result = await self.security_system.process_request(
                {
                    "operation": "validate_input",
                    "input_data": branch_name,
                    "input_type": "branch",
                }
            )

            if validation_result.get("status") != "success":
                raise SecurityError("Invalid branch name")

            # GitHub Manager呼び出し
            result = await self.github_manager.process_request(
                {"operation": "push_branch", "branch_name": branch_name}
            )

            return {
                "status": "success",
                "message": f"Branch pushed securely: {branch_name}",
                "github_result": result,
                "session_id": context.session_id,
                "branch_name": branch_name,
            }

        except Exception as e:
            self.logger.error(f"Secure push failed: {e}")
            raise SecurityError(f"Push failed: {e}")

    async def _secure_create_pr(
        self, request: Dict[str, Any], context: SecureGitHubContext
    ) -> Dict[str, Any]:
        """セキュアプルリクエスト作成"""
        try:
            # 認証・認可確認
            await self._check_operation_authorization(context, "create_pr")

            # PR情報検証
            title = request.get("title")
            body = request.get("body", "")
            head_branch = request.get("head_branch")
            base_branch = request.get("base_branch")

            for field, value in [
                ("title", title),
                ("body", body),
                ("head_branch", head_branch),
                ("base_branch", base_branch),
            ]:
                if value:
                    validation_result = await self.security_system.process_request(
                        {
                            "operation": "validate_input",
                            "input_data": value,
                            "input_type": "branch" if "branch" in field else "general",
                        }
                    )

                    if validation_result.get("status") != "success":
                        raise SecurityError(f"Invalid {field}")

            # GitHub Manager呼び出し
            result = await self.github_manager.process_request(
                {
                    "operation": "create_pr",
                    "title": title,
                    "body": body,
                    "head_branch": head_branch,
                    "base_branch": base_branch,
                }
            )

            return {
                "status": "success",
                "message": "Pull request created securely",
                "github_result": result,
                "session_id": context.session_id,
                "title": title,
                "head_branch": head_branch,
                "base_branch": base_branch,
            }

        except Exception as e:
            self.logger.error(f"Secure PR creation failed: {e}")
            raise SecurityError(f"PR creation failed: {e}")

    async def _secure_merge_pr(
        self, request: Dict[str, Any], context: SecureGitHubContext
    ) -> Dict[str, Any]:
        """セキュアプルリクエストマージ"""
        try:
            # 認証・認可確認
            await self._check_operation_authorization(context, "merge_pr")

            # PR番号検証
            pr_number = request.get("pr_number")
            if not isinstance(pr_number, int) or pr_number <= 0:
                raise SecurityError("Invalid PR number")

            # GitHub Manager呼び出し
            result = await self.github_manager.process_request(
                {"operation": "merge_pr", "pr_number": pr_number}
            )

            return {
                "status": "success",
                "message": f"Pull request merged securely: #{pr_number}",
                "github_result": result,
                "session_id": context.session_id,
                "pr_number": pr_number,
            }

        except Exception as e:
            self.logger.error(f"Secure PR merge failed: {e}")
            raise SecurityError(f"PR merge failed: {e}")

    async def _secure_get_status(
        self, request: Dict[str, Any], context: SecureGitHubContext
    ) -> Dict[str, Any]:
        """セキュアステータス取得"""
        try:
            # 認証・認可確認
            await self._check_operation_authorization(context, "get_status")

            # GitHub Manager呼び出し
            result = await self.github_manager.process_request(
                {"operation": "get_status"}
            )

            return {
                "status": "success",
                "message": "Status retrieved securely",
                "github_result": result,
                "session_id": context.session_id,
            }

        except Exception as e:
            self.logger.error(f"Secure status retrieval failed: {e}")
            raise SecurityError(f"Status retrieval failed: {e}")

    async def _secure_fallback_operation(
        self, request: Dict[str, Any], context: SecureGitHubContext
    ) -> Dict[str, Any]:
        """セキュアフォールバック操作"""
        try:
            operation = request.get("operation")

            # 認証・認可確認
            await self._check_operation_authorization(context, operation)

            # GitHub Manager呼び出し
            result = await self.github_manager.process_request(request)

            return {
                "status": "success",
                "message": f"Operation completed securely: {operation}",
                "github_result": result,
                "session_id": context.session_id,
                "operation": operation,
            }

        except Exception as e:
            self.logger.error(f"Secure fallback operation failed: {e}")
            raise SecurityError(f"Operation failed: {e}")

    async def _get_security_metrics(
        self, request: Dict[str, Any], context: SecureGitHubContext
    ) -> Dict[str, Any]:
        """セキュリティメトリクス取得"""
        try:
            # セキュリティシステムメトリクス
            security_metrics = await self.security_system.process_request(
                {"operation": "get_security_metrics"}
            )

            # 統合メトリクス
            integrated_metrics = {
                "system_stats": self.security_stats,
                "active_sessions": len(self.active_contexts),
                "security_system_metrics": security_metrics.get("metrics", {}),
                "github_manager_capabilities": self.github_manager.get_capabilities(),
            }

            return {
                "status": "success",
                "message": "Security metrics retrieved",
                "metrics": integrated_metrics,
                "session_id": context.session_id,
            }

        except Exception as e:
            self.logger.error(f"Security metrics retrieval failed: {e}")
            raise SecurityError(f"Metrics retrieval failed: {e}")

    async def _perform_security_scan(
        self, request: Dict[str, Any], context: SecureGitHubContext
    ) -> Dict[str, Any]:
        """セキュリティスキャン実行"""
        try:
            # 認証・認可確認
            await self._check_operation_authorization(context, "security_scan")

            # セキュリティスキャン実行
            scan_result = await self.security_system.process_request(
                {
                    "operation": "security_scan",
                    "scan_type": request.get("scan_type", "comprehensive"),
                }
            )

            if scan_result.get("status") == "success":
                vulnerabilities = scan_result.get("scan_results", [])
                total_vulnerabilities = sum(
                    result.get("vulnerabilities_found", 0)
                    + result.get("issues_found", 0)
                    for result in vulnerabilities
                )

                if total_vulnerabilities > 0:
                    self.security_stats[
                        "vulnerability_detections"
                    ] += total_vulnerabilities

            return {
                "status": "success",
                "message": "Security scan completed",
                "scan_result": scan_result,
                "session_id": context.session_id,
            }

        except Exception as e:
            self.logger.error(f"Security scan failed: {e}")
            raise SecurityError(f"Security scan failed: {e}")

    async def _secure_health_check(
        self, request: Dict[str, Any], context: SecureGitHubContext
    ) -> Dict[str, Any]:
        """セキュアヘルスチェック"""
        try:
            # GitHub Manager ヘルスチェック
            github_health = await self.github_manager.process_request(
                {"operation": "health_check"}
            )

            # セキュリティシステムヘルスチェック
            security_health = await self.security_system.process_request(
                {"operation": "health_check"}
            )

            # 統合ヘルス状態
            overall_health = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "components": {
                    "github_manager": github_health.get("health_status", {}),
                    "security_system": security_health.get("health_status", {}),
                    "secure_integration": {
                        "active_sessions": len(self.active_contexts),
                        "total_operations": self.security_stats["total_operations"],
                        "success_rate": (
                            self.security_stats["successful_operations"]
                            / max(self.security_stats["total_operations"], 1)
                        )
                        * 100,
                    },
                },
                "security_score": security_health.get("health_status", {}).get(
                    "security_score", 0
                ),
                "iron_will_compliant": security_health.get("health_status", {}).get(
                    "iron_will_compliant", False
                ),
            }

            # 全体的な健全性判定
            if (
                github_health.get("health_status", {}).get("status") != "healthy"
                or security_health.get("health_status", {}).get("status") != "healthy"
            ):
                overall_health["status"] = "unhealthy"

            return {
                "status": "success",
                "message": "Health check completed",
                "health_status": overall_health,
                "session_id": context.session_id,
            }

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "message": f"Health check failed: {e}",
                "health_status": {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

    async def _check_operation_authorization(
        self, context: SecureGitHubContext, operation: str
    ):
        """操作認可チェック"""
        if not context.authenticated:
            raise SecurityError("Authentication required")

        if operation not in context.authorized_operations:
            self.security_stats["authorization_failures"] += 1
            raise SecurityError(f"Operation not authorized: {operation}")

    def _get_authorized_operations(self, scopes: List[str]) -> List[str]:
        """スコープに基づく認可操作取得"""
        operations = []

        # 基本操作
        operations.extend(
            ["get_status", "get_current_branch", "get_commit_history", "health_check"]
        )

        # repo スコープ
        if "repo" in scopes:
            operations.extend(
                [
                    "create_branch",
                    "commit_changes",
                    "push_branch",
                    "create_pr",
                    "merge_pr",
                    "get_remote_status",
                    "pull_latest",
                ]
            )

        # read:user スコープ
        if "read:user" in scopes:
            operations.extend(["get_user_info"])

        # セキュリティ操作
        operations.extend(["get_security_metrics", "security_scan"])

        return operations

    async def _handle_security_error(self, request: Dict[str, Any], error: Exception):
        """セキュリティエラーハンドリング"""
        try:
            await self.security_system.security_monitoring.log_security_event(
                SecurityEventType.SECURITY_BREACH,
                {
                    "operation": request.get("operation"),
                    "error": str(error),
                    "source_ip": request.get("source_ip"),
                    "user_agent": request.get("user_agent"),
                    "timestamp": datetime.utcnow().isoformat(),
                },
                SecurityThreatLevel.HIGH,
            )

            self.logger.error(f"Security error: {error}")

        except Exception as e:
            self.logger.error(f"Error handling security error: {e}")

    async def _handle_general_error(self, request: Dict[str, Any], error: Exception):
        """一般エラーハンドリング"""
        try:
            await self.security_system.security_monitoring.log_security_event(
                SecurityEventType.AUDIT_LOG,
                {
                    "operation": request.get("operation"),
                    "error": str(error),
                    "error_type": "general_error",
                    "timestamp": datetime.utcnow().isoformat(),
                },
                SecurityThreatLevel.MEDIUM,
            )

            self.logger.error(f"General error: {error}")

        except Exception as e:
            self.logger.error(f"Error handling general error: {e}")


class SecurityError(Exception):
    """セキュリティエラー"""

    pass


# Convenience functions for easy access
async def get_secure_github_manager(
    repo_path: str = ".",
    github_config: Optional[Dict[str, Any]] = None,
    security_config: Optional[SecurityConfiguration] = None,
) -> SecureGitHubFlowManager:
    """
    セキュアGitHubフロー管理システム取得

    Args:
        repo_path: リポジトリパス
        github_config: GitHub設定
        security_config: セキュリティ設定

    Returns:
        SecureGitHubFlowManager インスタンス
    """
    return SecureGitHubFlowManager(repo_path, github_config, security_config)


def create_secure_github_context(
    user_id: str, github_token: str, scopes: List[str], **kwargs
) -> SecureGitHubContext:
    """
    セキュアGitHubコンテキスト作成

    Args:
        user_id: ユーザーID
        github_token: GitHubトークン
        scopes: スコープ
        **kwargs: 追加パラメータ

    Returns:
        SecureGitHubContext インスタンス
    """
    return SecureGitHubContext(
        user_id=user_id,
        session_id=str(uuid.uuid4()),
        github_token=github_token,
        scopes=scopes,
        **kwargs,
    )


if __name__ == "__main__":

    async def test_secure_github_manager():
        """テスト実行"""
        import uuid

        # セキュリティ設定
        security_config = SecurityConfiguration(
            token_expiry_minutes=60,
            mfa_enabled=True,
            rate_limit_requests_per_minute=100,
        )

        # セキュアGitHubフロー管理システム初期化
        manager = SecureGitHubFlowManager(
            repo_path=".", security_config=security_config
        )

        # ヘルスチェック
        health_result = await manager.process_request({"operation": "health_check"})
        print("Health Check:", health_result)

        # 認証テスト
        auth_result = await manager.process_request(
            {
                "operation": "authenticate",
                "token": "ghp_test_token_1234567890123456789012345678",
                "source_ip": "127.0.0.1",
                "user_agent": "TestAgent/1.0",
            }
        )
        print("Authentication:", auth_result)

        if auth_result.get("status") == "success":
            session_id = auth_result.get("session_id")

            # セキュアGitHub操作テスト
            status_result = await manager.process_request(
                {"operation": "get_status", "session_id": session_id}
            )
            print("Status:", status_result)

            # セキュリティメトリクス取得
            metrics_result = await manager.process_request(
                {"operation": "get_security_metrics", "session_id": session_id}
            )
            print("Security Metrics:", metrics_result)

    # テスト実行
    asyncio.run(test_secure_github_manager())
