#!/usr/bin/env python3
"""
Access Control Gateway - アクセス制御ゲートウェイ
Phase 1 Week 2 Day 11-12: セキュリティレベル分離システム

4賢者との協議で決定された統合アクセス制御システム
- SecurityLevelEnforcer と ResourceIsolationManager の統合
- 包括的なポリシー管理とエンフォースメント
- リアルタイムアクセス監視と自動対応
- 監査証跡とコンプライアンス管理
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
import sys
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.env_config import get_config
from libs.resource_isolation_manager import (
    IsolationContext,
    ResourceAlert,
    ResourceIsolationManager,
    ResourceQuota,
    ResourceType,
    ResourceUsage,
)
from libs.security_level_enforcer import (
    AccessRequest,
    AccessResult,
    AccessViolationType,
    DataClassification,
    PermissionLevel,
    SecurityContext,
    SecurityLevelEnforcer,
)
from libs.shared_enums import SecurityLevel


class PolicyType(Enum):
    """ポリシータイプ"""

    ACCESS_CONTROL = "access_control"
    RESOURCE_LIMIT = "resource_limit"
    DATA_PROTECTION = "data_protection"
    NETWORK_SECURITY = "network_security"
    AUDIT_COMPLIANCE = "audit_compliance"


class PolicyAction(Enum):
    """ポリシーアクション"""

    ALLOW = "allow"
    DENY = "deny"
    RESTRICT = "restrict"
    MONITOR = "monitor"
    REQUIRE_APPROVAL = "require_approval"


class GatewayStatus(Enum):
    """ゲートウェイ状態"""

    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    EMERGENCY = "emergency"
    SHUTDOWN = "shutdown"


@dataclass
class AccessPolicy:
    """アクセスポリシー定義"""

    policy_id: str
    name: str
    policy_type: PolicyType
    security_levels: List[SecurityLevel]
    conditions: Dict[str, Any]
    action: PolicyAction
    priority: int
    created_at: datetime
    enabled: bool = True
    description: str = ""


@dataclass
class PolicyEvaluationResult:
    """ポリシー評価結果"""

    policy_id: str
    matched: bool
    action: PolicyAction
    reason: str
    conditions_met: Dict[str, bool]
    evaluation_time_ms: float


@dataclass
class GatewayRequest:
    """ゲートウェイリクエスト"""

    request_id: str
    user_id: str
    resource_id: str
    action: str
    security_context: SecurityContext
    resource_context: Optional[IsolationContext]
    request_metadata: Dict[str, Any]
    timestamp: datetime


@dataclass
class GatewayResponse:
    """ゲートウェイレスポンス"""

    request_id: str
    granted: bool
    action_taken: str
    policies_applied: List[str]
    restrictions: List[str]
    audit_trail: Dict[str, Any]
    processing_time_ms: float
    timestamp: datetime


@dataclass
class ComplianceRecord:
    """コンプライアンス記録"""

    record_id: str
    event_type: str
    user_id: str
    resource_id: str
    security_level: SecurityLevel
    compliance_status: str
    violations: List[str]
    remediation_actions: List[str]
    timestamp: datetime


class AccessControlGateway:
    """アクセス制御ゲートウェイ - 統合セキュリティ管理システム"""

    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger(__name__)

        # コア統合システム
        self.security_enforcer = SecurityLevelEnforcer()
        self.resource_manager = ResourceIsolationManager()

        # ゲートウェイ状態
        self.status = GatewayStatus.ACTIVE
        self.status_lock = threading.RLock()

        # ポリシー管理
        self.policies: Dict[str, AccessPolicy] = {}
        self.policy_lock = threading.RLock()
        self._initialize_default_policies()

        # セッション統合管理
        self.integrated_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_lock = threading.RLock()

        # 監査とコンプライアンス
        self.audit_log: List[Dict[str, Any]] = []
        self.compliance_records: List[ComplianceRecord] = []
        self.audit_lock = threading.RLock()

        # リアルタイム監視
        self.active_requests: Dict[str, GatewayRequest] = {}
        self.request_metrics = {
            "total_requests": 0,
            "denied_requests": 0,
            "policy_violations": 0,
            "average_response_time_ms": 0.0,
        }

        # バックグラウンド監視開始
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self.monitoring_thread.start()

        self.logger.info(
            "🚪 AccessControlGateway initialized with integrated security systems"
        )

    def _initialize_default_policies(self):
        """デフォルトポリシー初期化"""

        default_policies = [
            # セキュリティレベル基本ポリシー
            AccessPolicy(
                policy_id="default_sandbox_isolation",
                name="Sandbox Complete Isolation",
                policy_type=PolicyType.ACCESS_CONTROL,
                security_levels=[SecurityLevel.SANDBOX],
                conditions={
                    "resource_types": ["network", "filesystem", "system"],
                    "max_risk_score": 0.3,
                },
                action=PolicyAction.RESTRICT,
                priority=100,
                created_at=datetime.now(),
                description="Complete isolation for sandbox environment",
            ),
            AccessPolicy(
                policy_id="resource_quota_enforcement",
                name="Resource Quota Enforcement",
                policy_type=PolicyType.RESOURCE_LIMIT,
                security_levels=[SecurityLevel.SANDBOX, SecurityLevel.RESTRICTED],
                conditions={"resource_threshold": 0.8, "enforcement_strict": True},
                action=PolicyAction.DENY,
                priority=90,
                created_at=datetime.now(),
                description="Strict resource quota enforcement",
            ),
            AccessPolicy(
                policy_id="data_classification_protection",
                name="Data Classification Protection",
                policy_type=PolicyType.DATA_PROTECTION,
                security_levels=[
                    SecurityLevel.SANDBOX,
                    SecurityLevel.RESTRICTED,
                    SecurityLevel.DEVELOPMENT,
                ],
                conditions={
                    "protected_classifications": [
                        "CONFIDENTIAL",
                        "RESTRICTED",
                        "TOP_SECRET",
                    ],
                    "require_encryption": True,
                },
                action=PolicyAction.REQUIRE_APPROVAL,
                priority=95,
                created_at=datetime.now(),
                description="Protect sensitive data based on classification",
            ),
            AccessPolicy(
                policy_id="cross_level_access_control",
                name="Cross-Level Access Control",
                policy_type=PolicyType.ACCESS_CONTROL,
                security_levels=[SecurityLevel.SANDBOX, SecurityLevel.RESTRICTED],
                conditions={
                    "cross_level_access": True,
                    "higher_privilege_required": True,
                },
                action=PolicyAction.MONITOR,
                priority=80,
                created_at=datetime.now(),
                description="Monitor and control cross-security-level access",
            ),
            AccessPolicy(
                policy_id="emergency_lockdown",
                name="Emergency Security Lockdown",
                policy_type=PolicyType.ACCESS_CONTROL,
                security_levels=[
                    SecurityLevel.SANDBOX,
                    SecurityLevel.RESTRICTED,
                    SecurityLevel.DEVELOPMENT,
                    SecurityLevel.TRUSTED,
                ],
                conditions={"threat_level": "critical", "immediate_action": True},
                action=PolicyAction.DENY,
                priority=1000,
                created_at=datetime.now(),
                enabled=False,  # 緊急時のみ有効化
                description="Emergency lockdown for critical threats",
            ),
        ]

        with self.policy_lock:
            for policy in default_policies:
                self.policies[policy.policy_id] = policy

        self.logger.info(f"🛡️ Initialized {len(default_policies)} default policies")

    async def process_access_request(
        self,
        user_id: str,
        resource_id: str,
        action: str,
        security_level: SecurityLevel = None,
        metadata: Dict[str, Any] = None,
    ) -> GatewayResponse:
        """統合アクセス要求処理"""

        start_time = time.time()
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        self.request_metrics["total_requests"] += 1

        try:
            # セキュリティコンテキスト取得または作成
            security_context = await self._get_or_create_security_context(
                user_id, security_level or SecurityLevel.DEVELOPMENT
            )

            # リソースコンテキスト取得または作成
            resource_context = await self._get_or_create_resource_context(
                user_id, security_context.security_level
            )

            # ゲートウェイリクエスト作成
            gateway_request = GatewayRequest(
                request_id=request_id,
                user_id=user_id,
                resource_id=resource_id,
                action=action,
                security_context=security_context,
                resource_context=resource_context,
                request_metadata=metadata or {},
                timestamp=datetime.now(),
            )

            # アクティブリクエスト追加
            self.active_requests[request_id] = gateway_request

            try:
                # ポリシー評価
                policy_results = await self._evaluate_policies(gateway_request)

                # アクセス制御チェック
                access_result = await self._check_access_control(gateway_request)

                # リソース制限チェック
                resource_check = await self._check_resource_limits(gateway_request)

                # 総合判定
                final_decision = self._make_final_decision(
                    gateway_request, policy_results, access_result, resource_check
                )

                # レスポンス作成
                processing_time = (time.time() - start_time) * 1000

                response = GatewayResponse(
                    request_id=request_id,
                    granted=final_decision["granted"],
                    action_taken=final_decision["action"],
                    policies_applied=[r.policy_id for r in policy_results if r.matched],
                    restrictions=final_decision.get("restrictions", []),
                    audit_trail={
                        "security_context_id": security_context.session_id,
                        "resource_context_id": (
                            resource_context.context_id if resource_context else None
                        ),
                        "policy_evaluations": len(policy_results),
                        "access_result": (
                            access_result.granted if access_result else None
                        ),
                        "resource_check": resource_check,
                    },
                    processing_time_ms=processing_time,
                    timestamp=datetime.now(),
                )

                # 監査ログ記録
                await self._record_audit_log(gateway_request, response, policy_results)

                # メトリクス更新
                self._update_metrics(response, processing_time)

                return response

            finally:
                # アクティブリクエスト削除
                self.active_requests.pop(request_id, None)

        except Exception as e:
            self.logger.error(f"❌ Error processing access request {request_id}: {e}")
            processing_time = (time.time() - start_time) * 1000

            return GatewayResponse(
                request_id=request_id,
                granted=False,
                action_taken="error",
                policies_applied=[],
                restrictions=["system_error"],
                audit_trail={"error": str(e)},
                processing_time_ms=processing_time,
                timestamp=datetime.now(),
            )

    async def _get_or_create_security_context(
        self, user_id: str, security_level: SecurityLevel
    ) -> SecurityContext:
        """セキュリティコンテキスト取得または作成"""

        with self.session_lock:
            # 既存セッション確認
            session_key = f"{user_id}_{security_level.value}"
            if session_key in self.integrated_sessions:
                session_data = self.integrated_sessions[session_key]
                security_context = session_data.get("security_context")

                # セッション有効性確認
                if security_context and security_context.expires_at > datetime.now():
                    return security_context

            # 新しいセキュリティコンテキスト作成
            security_context = self.security_enforcer.create_security_context(
                user_id=user_id,
                security_level=security_level,
                session_duration_minutes=480,  # 8時間
            )

            # セッション管理に登録
            self.integrated_sessions[session_key] = {
                "security_context": security_context,
                "resource_context": None,
                "created_at": datetime.now(),
            }

            return security_context

    async def _get_or_create_resource_context(
        self, user_id: str, security_level: SecurityLevel
    ) -> Optional[IsolationContext]:
        """リソースコンテキスト取得または作成"""

        with self.session_lock:
            session_key = f"{user_id}_{security_level.value}"
            session_data = self.integrated_sessions.get(session_key, {})

            resource_context = session_data.get("resource_context")

            # 既存コンテキスト確認
            if resource_context and resource_context.expires_at:
                if resource_context.expires_at > datetime.now():
                    return resource_context

            # 新しいリソースコンテキスト作成（必要な場合のみ）
            if security_level in [SecurityLevel.SANDBOX, SecurityLevel.RESTRICTED]:
                resource_context = self.resource_manager.create_isolation_context(
                    security_level=security_level, session_duration_hours=8
                )

                # セッション更新
                if session_key in self.integrated_sessions:
                    self.integrated_sessions[session_key][
                        "resource_context"
                    ] = resource_context

                return resource_context

            return None

    async def _evaluate_policies(
        self, request: GatewayRequest
    ) -> List[PolicyEvaluationResult]:
        """ポリシー評価"""

        results = []

        with self.policy_lock:
            # 優先順位順でソート
            sorted_policies = sorted(
                [p for p in self.policies.values() if p.enabled],
                key=lambda x: x.priority,
                reverse=True,
            )

        for policy in sorted_policies:
            if request.security_context.security_level not in policy.security_levels:
                continue

            start_time = time.time()

            # ポリシー条件評価
            evaluation = self._evaluate_policy_conditions(policy, request)

            evaluation_time = (time.time() - start_time) * 1000

            result = PolicyEvaluationResult(
                policy_id=policy.policy_id,
                matched=evaluation["matched"],
                action=policy.action,
                reason=evaluation["reason"],
                conditions_met=evaluation["conditions_met"],
                evaluation_time_ms=evaluation_time,
            )

            results.append(result)

            # 高優先度ポリシーが拒否の場合は即座に返す
            if (
                result.matched
                and policy.action == PolicyAction.DENY
                and policy.priority >= 90
            ):
                break

        return results

    def _evaluate_policy_conditions(
        self, policy: AccessPolicy, request: GatewayRequest
    ) -> Dict[str, Any]:
        """ポリシー条件評価"""

        conditions_met = {}
        matched = True
        reasons = []

        for condition_key, condition_value in policy.conditions.items():
            if condition_key == "max_risk_score":
                # リスクスコア条件
                current_risk = getattr(request.security_context, "risk_score", 0.0)
                met = current_risk <= condition_value
                conditions_met[condition_key] = met
                if not met:
                    matched = False
                    reasons.append(
                        f"Risk score {current_risk} exceeds limit {condition_value}"
                    )

            elif condition_key == "resource_threshold":
                # リソース閾値条件
                if request.resource_context:
                    usage = self.resource_manager.get_resource_usage(
                        request.resource_context.context_id
                    )
                    if usage:
                        cpu_usage = (
                            usage.cpu_percent
                            / request.resource_context.resource_quota.cpu_percent
                        )
                        met = cpu_usage <= condition_value
                        conditions_met[condition_key] = met
                        if not met:
                            matched = False
                            reasons.append(
                                f"Resource usage {cpu_usage:.2f} exceeds threshold {condition_value}"
                            )
                    else:
                        conditions_met[condition_key] = True
                else:
                    conditions_met[condition_key] = True

            elif condition_key == "protected_classifications":
                # データ分類保護条件
                data_class = request.request_metadata.get(
                    "data_classification", "PUBLIC"
                )
                met = data_class not in condition_value
                conditions_met[condition_key] = met
                if not met:
                    matched = False
                    reasons.append(
                        f"Data classification {data_class} requires protection"
                    )

            elif condition_key == "cross_level_access":
                # クロスレベルアクセス条件
                resource_level = request.request_metadata.get("target_security_level")
                if resource_level:
                    met = (
                        resource_level == request.security_context.security_level.value
                    )
                    conditions_met[condition_key] = not met  # 逆条件
                    if met:
                        matched = False
                        reasons.append("Cross-level access detected")
                else:
                    conditions_met[condition_key] = False

            elif condition_key == "threat_level":
                # 脅威レベル条件
                current_threat = request.request_metadata.get("threat_level", "low")
                met = current_threat == condition_value
                conditions_met[condition_key] = met
                if not met:
                    matched = False
                    reasons.append(
                        f"Threat level {current_threat} does not match {condition_value}"
                    )

            else:
                # その他の条件（デフォルトで満たされる）
                conditions_met[condition_key] = True

        return {
            "matched": matched,
            "conditions_met": conditions_met,
            "reason": "; ".join(reasons) if reasons else "All conditions met",
        }

    async def _check_access_control(
        self, request: GatewayRequest
    ) -> Optional[AccessResult]:
        """アクセス制御チェック"""

        try:
            # アクセス要求作成
            access_request = AccessRequest(
                resource_id=request.resource_id,
                action=request.action,
                data_classification=DataClassification(
                    request.request_metadata.get("data_classification", "public")
                ),
                required_permission=PermissionLevel(
                    request.request_metadata.get("required_permission", "read")
                ),
                context=request.security_context,
                metadata=request.request_metadata,
            )

            # SecurityLevelEnforcer でアクセス検証
            result = self.security_enforcer.validate_access(access_request)
            return result

        except Exception as e:
            self.logger.error(f"❌ Access control check failed: {e}")
            return None

    async def _check_resource_limits(self, request: GatewayRequest) -> Dict[str, Any]:
        """リソース制限チェック"""

        if not request.resource_context:
            return {"status": "no_resource_context", "violations": []}

        try:
            # リソース違反チェック
            alerts = self.resource_manager.check_resource_violations(
                request.resource_context.context_id
            )

            return {
                "status": "checked",
                "violations": [alert.message for alert in alerts],
                "alert_count": len(alerts),
                "context_id": request.resource_context.context_id,
            }

        except Exception as e:
            self.logger.error(f"❌ Resource limit check failed: {e}")
            return {"status": "error", "error": str(e)}

    def _make_final_decision(
        self,
        request: GatewayRequest,
        policy_results: List[PolicyEvaluationResult],
        access_result: Optional[AccessResult],
        resource_check: Dict[str, Any],
    ) -> Dict[str, Any]:
        """最終判定"""

        decision = {"granted": True, "action": "allow", "restrictions": []}

        # ポリシー評価結果チェック
        for result in policy_results:
            if result.matched:
                if result.action == PolicyAction.DENY:
                    decision["granted"] = False
                    decision["action"] = "deny"
                    decision["restrictions"].append(
                        f"Policy {result.policy_id}: {result.reason}"
                    )
                    return decision  # 拒否は即座に返す

                elif result.action == PolicyAction.RESTRICT:
                    decision["restrictions"].append(
                        f"Restricted by policy {result.policy_id}"
                    )

                elif result.action == PolicyAction.REQUIRE_APPROVAL:
                    decision["granted"] = False
                    decision["action"] = "require_approval"
                    decision["restrictions"].append(
                        f"Manual approval required: {result.policy_id}"
                    )

        # アクセス制御結果チェック
        if access_result and not access_result.granted:
            decision["granted"] = False
            decision["action"] = "deny"
            decision["restrictions"].append(f"Access control: {access_result.reason}")
            return decision

        # リソース制限チェック
        if resource_check.get("violations"):
            decision["restrictions"].extend(resource_check["violations"])
            if len(resource_check["violations"]) > 2:  # 複数違反で拒否
                decision["granted"] = False
                decision["action"] = "deny"

        return decision

    async def _record_audit_log(
        self,
        request: GatewayRequest,
        response: GatewayResponse,
        policy_results: List[PolicyEvaluationResult],
    ):
        """監査ログ記録"""

        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request.request_id,
            "user_id": request.user_id,
            "resource_id": request.resource_id,
            "action": request.action,
            "security_level": request.security_context.security_level.value,
            "granted": response.granted,
            "action_taken": response.action_taken,
            "processing_time_ms": response.processing_time_ms,
            "policies_evaluated": len(policy_results),
            "policies_matched": len([r for r in policy_results if r.matched]),
            "restrictions_applied": len(response.restrictions),
            "compliance_status": "compliant" if response.granted else "violation",
        }

        with self.audit_lock:
            self.audit_log.append(audit_entry)

        # ファイルにも保存
        audit_file = Path("/home/aicompany/workspace/logs/access_gateway_audit.log")
        audit_file.parent.mkdir(parents=True, exist_ok=True)

        with open(audit_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(audit_entry) + "\n")

    def _update_metrics(self, response: GatewayResponse, processing_time: float):
        """メトリクス更新"""

        if not response.granted:
            self.request_metrics["denied_requests"] += 1

        if response.action_taken == "deny":
            self.request_metrics["policy_violations"] += 1

        # 平均レスポンス時間更新
        current_avg = self.request_metrics["average_response_time_ms"]
        total_requests = self.request_metrics["total_requests"]

        new_avg = (
            (current_avg * (total_requests - 1)) + processing_time
        ) / total_requests
        self.request_metrics["average_response_time_ms"] = new_avg

    def _monitoring_loop(self):
        """監視ループ"""

        while self.monitoring_active:
            try:
                # セッションクリーンアップ
                self._cleanup_expired_sessions()

                # システム健全性チェック
                self._check_system_health()

                # コンプライアンス監査
                self._run_compliance_check()

                time.sleep(60)  # 1分間隔

            except Exception as e:
                self.logger.error(f"❌ Error in monitoring loop: {e}")
                time.sleep(300)  # エラー時は5分待機

    def _cleanup_expired_sessions(self):
        """期限切れセッションクリーンアップ"""

        with self.session_lock:
            expired_sessions = []

            for session_key, session_data in self.integrated_sessions.items():
                security_context = session_data.get("security_context")
                if security_context and security_context.expires_at < datetime.now():
                    expired_sessions.append(session_key)

            for session_key in expired_sessions:
                session_data = self.integrated_sessions.pop(session_key, {})

                # リソースコンテキストのクリーンアップ
                resource_context = session_data.get("resource_context")
                if resource_context:
                    self.resource_manager.terminate_context(
                        resource_context.context_id, "Session expired"
                    )

        if expired_sessions:
            self.logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")

    def _check_system_health(self):
        """システム健全性チェック"""

        try:
            # セキュリティエンフォーサーの健全性チェック
            security_metrics = self.security_enforcer.get_security_metrics()

            # リソースマネージャーの健全性チェック
            resource_metrics = self.resource_manager.get_system_metrics()

            # 異常検知
            if security_metrics.get("security_violations", 0) > 10:
                self.logger.warning("⚠️ High security violations detected")

            if resource_metrics.get("system_resources", {}).get("cpu_percent", 0) > 90:
                self.logger.warning("⚠️ High system CPU usage detected")

        except Exception as e:
            self.logger.error(f"❌ System health check failed: {e}")

    def _run_compliance_check(self):
        """コンプライアンスチェック実行"""

        try:
            # 最近の監査ログ分析
            recent_logs = [
                log
                for log in self.audit_log
                if datetime.fromisoformat(log["timestamp"])
                > datetime.now() - timedelta(hours=1)
            ]

            # 違反率チェック
            total_recent = len(recent_logs)
            violations = len(
                [log for log in recent_logs if log["compliance_status"] == "violation"]
            )

            if total_recent > 0:
                violation_rate = violations / total_recent
                if violation_rate > 0.1:  # 10%以上の違反率
                    self.logger.warning(
                        f"⚠️ High compliance violation rate: {violation_rate:.1%}"
                    )

        except Exception as e:
            self.logger.error(f"❌ Compliance check failed: {e}")

    def get_gateway_status(self) -> Dict[str, Any]:
        """ゲートウェイ状態取得"""

        with self.status_lock:
            status = self.status

        with self.session_lock:
            active_sessions = len(self.integrated_sessions)

        return {
            "status": status.value,
            "active_sessions": active_sessions,
            "active_requests": len(self.active_requests),
            "total_policies": len(self.policies),
            "enabled_policies": len([p for p in self.policies.values() if p.enabled]),
            "metrics": self.request_metrics.copy(),
            "system_health": {
                "monitoring_active": self.monitoring_active,
                "audit_log_entries": len(self.audit_log),
                "compliance_records": len(self.compliance_records),
            },
        }

    def emergency_lockdown(self, reason: str = "Emergency lockdown activated"):
        """緊急ロックダウン"""

        with self.status_lock:
            self.status = GatewayStatus.EMERGENCY

        with self.policy_lock:
            # 緊急ロックダウンポリシーを有効化
            if "emergency_lockdown" in self.policies:
                self.policies["emergency_lockdown"].enabled = True

        self.logger.critical(f"🚨 EMERGENCY LOCKDOWN ACTIVATED: {reason}")

    def shutdown(self):
        """システムシャットダウン"""

        self.logger.info("🛑 Shutting down AccessControlGateway...")

        with self.status_lock:
            self.status = GatewayStatus.SHUTDOWN

        # 監視停止
        self.monitoring_active = False

        # 全セッション終了
        with self.session_lock:
            for session_data in self.integrated_sessions.values():
                resource_context = session_data.get("resource_context")
                if resource_context:
                    self.resource_manager.terminate_context(
                        resource_context.context_id, "System shutdown"
                    )

        # 統合システムシャットダウン
        self.resource_manager.shutdown()

        self.logger.info("✅ AccessControlGateway shutdown complete")


if __name__ == "__main__":
    # AccessControlGateway のテスト
    import asyncio

    async def test_gateway():
        gateway = AccessControlGateway()

        print("🚪 AccessControlGateway Test Starting...")

        try:
            # テストアクセス要求
            response = await gateway.process_access_request(
                user_id="test_user",
                resource_id="test_resource",
                action="read",
                security_level=SecurityLevel.DEVELOPMENT,
                metadata={
                    "data_classification": "internal",
                    "required_permission": "read",
                },
            )

            print(f"✅ Access request processed:")
            print(f"   Request ID: {response.request_id}")
            print(f"   Granted: {response.granted}")
            print(f"   Action: {response.action_taken}")
            print(f"   Policies Applied: {len(response.policies_applied)}")
            print(f"   Processing Time: {response.processing_time_ms:.1f}ms")

            if response.restrictions:
                print(f"   Restrictions: {len(response.restrictions)}")
                for restriction in response.restrictions:
                    print(f"     - {restriction}")

            # ゲートウェイ状態確認
            status = gateway.get_gateway_status()
            print(f"\n📊 Gateway Status:")
            print(f"   Status: {status['status']}")
            print(f"   Active Sessions: {status['active_sessions']}")
            print(f"   Total Requests: {status['metrics']['total_requests']}")
            print(
                f"   Average Response Time: {status['metrics']['average_response_time_ms']:.1f}ms"
            )

            print("\n✅ AccessControlGateway test completed successfully")

        except Exception as e:
            print(f"❌ Test failed: {e}")

        finally:
            gateway.shutdown()

    # テスト実行
    asyncio.run(test_gateway())
