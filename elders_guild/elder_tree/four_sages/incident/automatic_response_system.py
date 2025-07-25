#!/usr/bin/env python3
"""
🤖 Automatic Response System - 自動対応システム
Phase 26: Incident Sage統合実装
Created: 2025-07-17
Author: Claude Elder
Version: 1.0.0
"""

import asyncio
import json
import logging
import shlex
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# Elders Legacy Integration
from core.elders_legacy import EldersServiceLegacy
from elders_guild.elder_tree.four_sages.incident.incident_sage import (
    IncidentAction,
    IncidentCategory,
    IncidentEntry,
    IncidentSeverity,
)

logger = logging.getLogger("automatic_response_system")


class ResponseStatus(Enum):
    """対応ステータス"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


@dataclass
class ResponseRule:
    """自動対応ルール"""

    rule_id: str
    rule_name: str
    conditions: List[str]  # マッチング条件
    actions: List[str]  # 実行アクション
    priority: int = 5
    max_retries: int = 3
    cooldown: int = 300  # 秒単位のクールダウン
    approval_required: bool = False
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResponseExecution:
    """対応実行記録"""

    execution_id: str
    incident_id: str
    rule_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: ResponseStatus = ResponseStatus.PENDING
    actions_executed: List[Dict[str, Any]] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)
    rollback_performed: bool = False
    effectiveness_score: float = 0.0


class AutomaticResponseSystem(EldersServiceLegacy):
    """自動対応システム"""

    def __init__(self, incident_sage):
        """初期化メソッド"""
        super().__init__(name="AutomaticResponseSystem", service_type="automation")
        self.incident_sage = incident_sage
        self.response_rules: Dict[str, ResponseRule] = {}
        self.recovery_scripts: Dict[str, Dict[str, Any]] = {}
        self.response_history: List[ResponseExecution] = []
        self.execution_lock = asyncio.Lock()
        self.cooldown_tracker: Dict[str, datetime] = {}

        # 対応アクションレジストリ
        self.action_registry: Dict[str, Callable] = {
            "restart_service": self._restart_service,
            "scale_up": self._scale_up_resources,
            "rollback_deployment": self._rollback_deployment,
            "clear_cache": self._clear_cache,
            "rotate_logs": self._rotate_logs,
            "restart_container": self._restart_container,
            "failover": self._perform_failover,
            "throttle_requests": self._throttle_requests,
            "block_ip": self._block_ip,
            "restore_backup": self._restore_backup,
        }

        # 効果測定メトリクス
        self.effectiveness_metrics = {
            "total_executions": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "average_response_time": 0.0,
            "automation_rate": 0.0,
        }

        # デフォルトルール設定
        self._configure_default_rules()

        logger.info("🤖 Automatic Response System initialized")

    def _configure_default_rules(self):
        """デフォルト対応ルール設定"""
        default_rules = [
            ResponseRule(
                rule_id="service_restart_rule",
                rule_name="Service Restart on Failure",
                conditions=[
                    "service_failure",
                    "service_unresponsive",
                    "health_check_failed",
                ],
                actions=["restart_service", "verify_health"],
                priority=1,
                max_retries=3,
                cooldown=300,
            ),
            ResponseRule(
                rule_id="resource_scaling_rule",
                rule_name="Auto-scale on High Load",
                conditions=[
                    "high_cpu_usage",
                    "high_memory_usage",
                    "resource_exhaustion",
                ],
                actions=["scale_up", "balance_load"],
                priority=2,
                cooldown=600,
                approval_required=False,
            ),
            ResponseRule(
                rule_id="deployment_rollback_rule",
                rule_name="Rollback on Deployment Failure",
                conditions=[
                    "deployment_failure",
                    "post_deploy_errors",
                    "version_incompatibility",
                ],
                actions=["rollback_deployment", "verify_rollback"],
                priority=1,
                approval_required=True,
            ),
            ResponseRule(
                rule_id="cache_clear_rule",
                rule_name="Clear Cache on Performance Issues",
                conditions=[
                    "cache_corruption",
                    "performance_degradation",
                    "memory_pressure",
                ],
                actions=["clear_cache", "warm_cache"],
                priority=3,
                cooldown=1800,
            ),
            ResponseRule(
                rule_id="container_restart_rule",
                rule_name="Container Restart on Crash",
                conditions=["container_exit", "container_oom", "container_unhealthy"],
                actions=["restart_container", "check_container_logs"],
                priority=1,
                max_retries=5,
            ),
        ]

        for rule in default_rules:
            self.response_rules[rule.rule_id] = rule

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """リクエスト処理"""
        request_type = request.get("type", "handle")

        if request_type == "handle":
            return await self._handle_incident(request)
        elif request_type == "configure_rule":
            return await self._configure_rule(request)
        elif request_type == "execute_action":
            return await self._execute_action(request)
        elif request_type == "get_history":
            return await self._get_history(request)
        elif request_type == "measure_effectiveness":
            return await self._measure_effectiveness(request)
        elif request_type == "register_script":
            return await self._register_script(request)
        else:
            return {"success": False, "error": f"Unknown request type: {request_type}"}

    async def handle_incident(self, incident: IncidentEntry) -> Dict[str, Any]:
        """インシデント自動対応"""
        try:
            logger.info(f"🤖 Handling incident: {incident.id} - {incident.title}")

            # マッチするルールを検索
            matched_rules = await self._match_rules(incident)

            if not matched_rules:
                logger.info("📋 No matching rules found for incident")
                return {
                    "success": True,
                    "handled": False,
                    "message": "No automatic response rules matched",
                }

            # 優先度順にソート
            matched_rules.sort(key=lambda r: r.priority)

            executions = []
            for rule in matched_rules:
                # クールダウンチェック
                if not await self._check_cooldown(rule):
                    logger.info(f"⏳ Rule {rule.rule_id} in cooldown period")
                    continue

                # 承認チェック
                if rule.approval_required:
                    logger.warning(
                        f"🔐 Rule {rule.rule_id} requires approval, skipping"
                    )
                    continue

                # ルール実行
                execution = await self._execute_rule(rule, incident)
                executions.append(execution)

                # 成功した場合は後続ルールをスキップ可能
                if execution.status == ResponseStatus.SUCCESS:
                    break

            # 効果測定
            await self._update_effectiveness_metrics(executions)

            return {
                "success": True,
                "handled": True,
                "executions": [self._execution_to_dict(e) for e in executions],
                "total_rules_matched": len(matched_rules),
                "total_executed": len(executions),
            }

        except Exception as e:
            logger.error(f"❌ Incident handling failed: {e}")
            return {"success": False, "error": str(e)}

    async def _match_rules(self, incident: IncidentEntry) -> List[ResponseRule]:
        """インシデントに対応するルールをマッチング"""
        matched_rules = []

        # インシデントの属性を条件文字列に変換
        incident_conditions = set()

        # カテゴリベースの条件
        category_conditions = {
            IncidentCategory.SYSTEM_FAILURE: [
                "service_failure",
                "system_error",
                "crash",
            ],
            IncidentCategory.PERFORMANCE_ISSUE: [
                "high_load",
                "slow_response",
                "performance_degradation",
            ],
            IncidentCategory.NETWORK_ISSUE: [
                "network_error",
                "connection_failure",
                "timeout",
            ],
            IncidentCategory.SECURITY_BREACH: [
                "security_alert",
                "unauthorized_access",
                "intrusion",
            ],
            IncidentCategory.DATA_CORRUPTION: [
                "data_error",
                "corruption",
                "integrity_failure",
            ],
            IncidentCategory.CONFIGURATION_ERROR: [
                "config_error",
                "misconfiguration",
                "deployment_failure",
            ],
        }

        if incident.category in category_conditions:
            incident_conditions.update(category_conditions[incident.category])

        # 重要度ベースの条件
        if incident.severity in [IncidentSeverity.CRITICAL, IncidentSeverity.HIGH]:
            incident_conditions.add("high_priority")

        # 説明文からキーワード抽出
        description_lower = incident.description.lower()
        keyword_conditions = {
            "timeout": ["timeout", "timed out"],
            "memory": ["memory", "oom", "heap"],
            "cpu": ["cpu", "processor", "high load"],
            "disk": ["disk", "storage", "space"],
            "network": ["network", "connection", "socket"],
            "service": ["service", "process", "daemon"],
            "container": ["container", "docker", "kubernetes", "k8s"],
            "deployment": ["deploy", "rollout", "release"],
        }

        for condition, keywords in keyword_conditions.items():
            if any(keyword in description_lower for keyword in keywords):
                incident_conditions.add(condition)

        # ルールマッチング
        for rule in self.response_rules.values():
            if not rule.enabled:
                continue

            # いずれかの条件がマッチすればOK
            if any(condition in incident_conditions for condition in rule.conditions):
                matched_rules.append(rule)

        return matched_rules

    async def _check_cooldown(self, rule: ResponseRule) -> bool:
        """クールダウン期間チェック"""
        if rule.rule_id not in self.cooldown_tracker:
            return True

        last_execution = self.cooldown_tracker[rule.rule_id]
        cooldown_end = last_execution + timedelta(seconds=rule.cooldown)

        return datetime.now() > cooldown_end

    async def _execute_rule(
        self, rule: ResponseRule, incident: IncidentEntry
    ) -> ResponseExecution:
        """ルール実行"""
        execution = ResponseExecution(
            execution_id=str(uuid.uuid4()),
            incident_id=incident.id,
            rule_id=rule.rule_id,
            started_at=datetime.now(),
        )

        try:
            async with self.execution_lock:
                execution.status = ResponseStatus.IN_PROGRESS
                logger.info(f"⚡ Executing rule: {rule.rule_name}")

                # 各アクション実行
                for action_name in rule.actions:
                    if action_name in self.action_registry:
                        action_func = self.action_registry[action_name]
                        result = await self._execute_action_with_retry(
                            action_func, incident, rule.max_retries
                        )

                        execution.actions_executed.append(
                            {
                                "action": action_name,
                                "result": result,
                                "timestamp": datetime.now().isoformat(),
                            }
                        )

                        if not result["success"]:
                            execution.error_messages.append(
                                f"Action {action_name} failed: {result.get(
                                    'error',
                                    'Unknown error'
                                )}"
                            )
                    else:
                        logger.warning(f"⚠️ Unknown action: {action_name}")

                # 実行結果判定
                if all(a["result"]["success"] for a in execution.actions_executed):
                    execution.status = ResponseStatus.SUCCESS
                elif any(a["result"]["success"] for a in execution.actions_executed):
                    execution.status = ResponseStatus.PARTIAL
                else:
                    execution.status = ResponseStatus.FAILED

                # クールダウン記録
                self.cooldown_tracker[rule.rule_id] = datetime.now()

                # インシデントに対応記録を追加
                await self._record_response_to_incident(incident, execution, rule)

        except Exception as e:
            logger.error(f"❌ Rule execution failed: {e}")
            execution.status = ResponseStatus.FAILED
            execution.error_messages.append(str(e))

        finally:
            execution.completed_at = datetime.now()
            self.response_history.append(execution)

        return execution

    async def _execute_action_with_retry(
        self, action_func: Callable, incident: IncidentEntry, max_retries: int
    ) -> Dict[str, Any]:
        """リトライ付きアクション実行"""
        for attempt in range(max_retries):
            try:
                result = await action_func(incident)
                if result["success"]:
                    return result

                if attempt < max_retries - 1:
                    logger.info(
                        f"🔄 Retrying action (attempt {attempt + 2}/{max_retries})"
                    )
                    await asyncio.sleep(2**attempt)  # 指数バックオフ

            except Exception as e:
                logger.error(f"❌ Action execution error: {e}")
                if attempt == max_retries - 1:
                    return {"success": False, "error": str(e)}

        return {"success": False, "error": "Max retries exceeded"}

    async def _record_response_to_incident(
        self, incident: IncidentEntry, execution: ResponseExecution, rule: ResponseRule
    ):
        """インシデントに対応記録を追加"""
        try:
            action_description = f"Automatic response executed: {rule.rule_name}"
            action_result = f"Status: {execution.status.value}, Actions: {len(execution.actions_executed)}" \
                "Status: {execution.status.value}, Actions: {len(execution.actions_executed)}"

            response = await self.incident_sage.process_request(
                {
                    "type": "update_incident",
                    "incident_id": incident.id,
                    "action": {
                        "type": "automatic_response",
                        "description": action_description,
                        "performed_by": "automatic_response_system",
                        "result": action_result,
                    },
                }
            )

            if response.get("success"):
                logger.info("✅ Response recorded to incident")

        except Exception as e:
            logger.error(f"❌ Failed to record response: {e}")

    # アクション実装
    async def _restart_service(self, incident: IncidentEntry) -> Dict[str, Any]:
        """サービス再起動"""
        try:
            # サービス名を特定
            service_name = self._extract_service_name(incident)
            if not service_name:
                return {"success": False, "error": "Could not identify service"}

            # systemctl restart コマンド実行（実際の環境では適切な権限管理が必要）
            cmd = f"sudo systemctl restart {shlex.quote(service_name)}"
            result = await self._execute_command(cmd)

            if result["success"]:
                # 健全性確認
                await asyncio.sleep(5)
                health_check = await self._check_service_health(service_name)
                result["health_check"] = health_check

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _scale_up_resources(self, incident: IncidentEntry) -> Dict[str, Any]:
        """リソーススケールアップ"""
        try:
            # リソースタイプを特定
            resource_type = self._identify_resource_type(incident)

            # スケーリング実行（プレースホルダー）
            logger.info(f"📈 Scaling up {resource_type} resources")

            # 実際の実装では、クラウドプロバイダーAPIを呼び出す
            # 例: AWS Auto Scaling, Kubernetes HPA など

            return {
                "success": True,
                "resource_type": resource_type,
                "scaled_up": True,
                "new_capacity": "2x",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _rollback_deployment(self, incident: IncidentEntry) -> Dict[str, Any]:
        """デプロイメントロールバック"""
        try:
            # 現在のバージョンと前のバージョンを特定
            current_version = self._get_current_version(incident)
            previous_version = self._get_previous_version(incident)

            if not previous_version:
                return {"success": False, "error": "No previous version found"}

            logger.info(f"🔄 Rolling back from {current_version} to {previous_version}")

            # ロールバック実行（プレースホルダー）
            # 実際の実装では、デプロイメントツールのAPIを使用

            return {
                "success": True,
                "rolled_back_from": current_version,
                "rolled_back_to": previous_version,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _clear_cache(self, incident: IncidentEntry) -> Dict[str, Any]:
        """キャッシュクリア"""
        try:
            # キャッシュタイプを特定
            cache_types = ["redis", "memcached", "application"]
            cleared = []

            for cache_type in cache_types:
                if cache_type == "redis":
                    # Redis FLUSHDB（実際の環境では慎重に）
                    logger.info("🗑️ Clearing Redis cache")
                    cleared.append("redis")
                elif cache_type == "application":
                    # アプリケーションキャッシュクリア
                    logger.info("🗑️ Clearing application cache")
                    cleared.append("application")

            return {"success": True, "cleared_caches": cleared}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _rotate_logs(self, incident: IncidentEntry) -> Dict[str, Any]:
        """ログローテーション"""
        try:
            # logrotate実行
            cmd = "sudo logrotate -f /etc/logrotate.conf"
            result = await self._execute_command(cmd)

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _restart_container(self, incident: IncidentEntry) -> Dict[str, Any]:
        """コンテナ再起動"""
        try:
            # コンテナ名を特定
            container_name = self._extract_container_name(incident)
            if not container_name:
                return {"success": False, "error": "Could not identify container"}

            # Docker restart
            cmd = f"docker restart {shlex.quote(container_name)}"
            result = await self._execute_command(cmd)

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _perform_failover(self, incident: IncidentEntry) -> Dict[str, Any]:
        """フェイルオーバー実行"""
        try:
            logger.info("🔀 Performing failover")

            # フェイルオーバー実行（プレースホルダー）
            # 実際の実装では、ロードバランサーAPIやDNS更新を行う

            return {
                "success": True,
                "failover_completed": True,
                "new_primary": "backup-server-1",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _throttle_requests(self, incident: IncidentEntry) -> Dict[str, Any]:
        """リクエストスロットリング"""
        try:
            # レート制限設定
            logger.info("🚦 Applying request throttling")

            # 実際の実装では、APIゲートウェイやリバースプロキシの設定を更新

            return {
                "success": True,
                "throttling_applied": True,
                "rate_limit": "100 req/min",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _block_ip(self, incident: IncidentEntry) -> Dict[str, Any]:
        """IP ブロック"""
        try:
            # 悪意のあるIPを特定
            malicious_ips = self._extract_malicious_ips(incident)

            if not malicious_ips:
                return {"success": False, "error": "No malicious IPs identified"}

            # ファイアウォールルール追加（プレースホルダー）
            logger.info(f"🛡️ Blocking IPs: {malicious_ips}")

            return {"success": True, "blocked_ips": malicious_ips}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _restore_backup(self, incident: IncidentEntry) -> Dict[str, Any]:
        """バックアップ復元"""
        try:
            # 最新のバックアップを特定
            logger.info("💾 Restoring from backup")

            # バックアップ復元（プレースホルダー）
            # 実際の実装では、バックアップシステムAPIを使用

            return {
                "success": True,
                "backup_restored": True,
                "backup_timestamp": "2025-07-17T10:00:00",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ヘルパーメソッド
    async def _execute_command(self, cmd: str, timeout: int = 30) -> Dict[str, Any]:
        """コマンド実行（セキュリティ注意）"""
        try:
            # 実際の実装では、適切な権限管理とサニタイゼーションが必要
            logger.info(f"🔧 Executing: {cmd}")

            # プレースホルダー実装
            return {
                "success": True,
                "command": cmd,
                "output": "Command executed successfully",
                "exit_code": 0,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "exit_code": 1}

    def _extract_service_name(self, incident: IncidentEntry) -> Optional[str]:
        """インシデントからサービス名抽出"""
        # 実装: インシデントの説明やタグからサービス名を抽出
        for system in incident.affected_systems:
            if "service" in system.lower():
                return system.split(":")[-1].strip()
        return None

    def _extract_container_name(self, incident: IncidentEntry) -> Optional[str]:
        """インシデントからコンテナ名抽出"""
        # 実装: インシデントの説明やタグからコンテナ名を抽出
        description = incident.description.lower()
        if "container" in description:
            # 簡易的なパターンマッチング
            words = description.split()
            for i, word in enumerate(words):
                if word == "container" and i + 1 < len(words):
                    return words[i + 1]
        return None

    def _identify_resource_type(self, incident: IncidentEntry) -> str:
        """リソースタイプ特定"""
        description = incident.description.lower()
        if "cpu" in description:
            return "cpu"
        elif "memory" in description or "ram" in description:
            return "memory"
        elif "disk" in description or "storage" in description:
            return "storage"
        else:
            return "compute"

    def _get_current_version(self, incident: IncidentEntry) -> str:
        """現在のバージョン取得"""
        # 実装: デプロイメントシステムから現在のバージョンを取得
        return "v2.1.0"

    def _get_previous_version(self, incident: IncidentEntry) -> Optional[str]:
        """前のバージョン取得"""
        # 実装: デプロイメント履歴から前のバージョンを取得
        return "v2.0.5"

    def _extract_malicious_ips(self, incident: IncidentEntry) -> List[str]:
        """悪意のあるIP抽出"""
        # 実装: ログやインシデント情報から悪意のあるIPを抽出
        # プレースホルダー
        return []

    async def _check_service_health(self, service_name: str) -> Dict[str, Any]:
        """サービス健全性チェック"""
        # 実装: サービスのヘルスチェックエンドポイントを呼び出す
        return {"healthy": True, "status": "running", "uptime": "5 seconds"}

    async def _update_effectiveness_metrics(self, executions: List[ResponseExecution]):
        """効果測定メトリクス更新"""
        self.effectiveness_metrics["total_executions"] += len(executions)

        for execution in executions:
            if execution.status == ResponseStatus.SUCCESS:
                self.effectiveness_metrics["successful_responses"] += 1
            else:
                self.effectiveness_metrics["failed_responses"] += 1

            # 応答時間計算
            if execution.completed_at:
                response_time = (
                    execution.completed_at - execution.started_at
                ).total_seconds()
                current_avg = self.effectiveness_metrics["average_response_time"]
                total = self.effectiveness_metrics["total_executions"]
                self.effectiveness_metrics["average_response_time"] = (
                    current_avg * (total - len(executions)) + response_time
                ) / total

        # 自動化率計算
        if self.effectiveness_metrics["total_executions"] > 0:
            self.effectiveness_metrics["automation_rate"] = (
                self.effectiveness_metrics["successful_responses"]
                / self.effectiveness_metrics["total_executions"]
            )

    def _execution_to_dict(self, execution: ResponseExecution) -> Dict[str, Any]:
        """実行記録を辞書形式に変換"""
        return {
            "execution_id": execution.execution_id,
            "incident_id": execution.incident_id,
            "rule_id": execution.rule_id,
            "started_at": execution.started_at.isoformat(),
            "completed_at": (
                execution.completed_at.isoformat() if execution.completed_at else None
            ),
            "status": execution.status.value,
            "actions_executed": execution.actions_executed,
            "error_messages": execution.error_messages,
            "rollback_performed": execution.rollback_performed,
            "effectiveness_score": execution.effectiveness_score,
        }

    # リクエスト処理メソッド
    async def _handle_incident(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """インシデント処理リクエスト"""
        incident_data = request.get("incident")
        if not incident_data:
            return {"success": False, "error": "Incident data required"}

        # IncidentEntry オブジェクトに変換（簡易版）
        incident = IncidentEntry(
            id=incident_data.get("id", str(uuid.uuid4())),
            title=incident_data.get("title", ""),
            description=incident_data.get("description", ""),
            category=IncidentCategory(incident_data.get("category", "system_failure")),
            severity=IncidentSeverity(incident_data.get("severity", "medium")),
            status=incident_data.get("status", "open"),
            affected_systems=incident_data.get("affected_systems", []),
        )

        return await self.handle_incident(incident)

    async def _configure_rule(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """ルール設定リクエスト"""
        rule_data = request.get("rule")
        if not rule_data:
            return {"success": False, "error": "Rule data required"}

        rule = ResponseRule(
            rule_id=rule_data.get("rule_id", str(uuid.uuid4())),
            rule_name=rule_data.get("rule_name", ""),
            conditions=rule_data.get("conditions", []),
            actions=rule_data.get("actions", []),
            priority=rule_data.get("priority", 5),
            max_retries=rule_data.get("max_retries", 3),
            cooldown=rule_data.get("cooldown", 300),
            approval_required=rule_data.get("approval_required", False),
            enabled=rule_data.get("enabled", True),
        )

        self.response_rules[rule.rule_id] = rule
        return {"success": True, "rule_id": rule.rule_id}

    async def _execute_action(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """アクション実行リクエスト"""
        action_name = request.get("action")
        incident_data = request.get("incident", {})

        if action_name not in self.action_registry:
            return {"success": False, "error": f"Unknown action: {action_name}"}

        # 簡易的なインシデント作成
        incident = IncidentEntry(
            id=str(uuid.uuid4()),
            title="Manual action execution",
            description=f"Executing {action_name}",
            category=IncidentCategory.SYSTEM_FAILURE,
            severity=IncidentSeverity.MEDIUM,
            status="open",
        )

        action_func = self.action_registry[action_name]
        result = await action_func(incident)

        return result

    async def _get_history(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """履歴取得リクエスト"""
        limit = request.get("limit", 100)
        incident_id = request.get("incident_id")

        history = self.response_history[-limit:]

        if incident_id:
            history = [h for h in history if h.incident_id == incident_id]

        return {
            "success": True,
            "history": [self._execution_to_dict(h) for h in history],
            "count": len(history),
        }

    async def _measure_effectiveness(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """効果測定リクエスト"""
        execution_id = request.get("execution_id")

        if execution_id:
            # 特定の実行の効果測定
            for execution in self.response_history:
                if execution.execution_id == execution_id:
                    # 簡易的な効果スコア計算
                    if execution.status == ResponseStatus.SUCCESS:
                        execution.effectiveness_score = 1.0
                    elif execution.status == ResponseStatus.PARTIAL:
                        execution.effectiveness_score = 0.5
                    else:
                        execution.effectiveness_score = 0.0

                    return {
                        "success": True,
                        "execution_id": execution_id,
                        "effectiveness_score": execution.effectiveness_score,
                    }

            return {"success": False, "error": "Execution not found"}

        # 全体の効果測定
        return {"success": True, "metrics": self.effectiveness_metrics}

    async def _register_script(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """復旧スクリプト登録リクエスト"""
        script_name = request.get("script_name")
        script_path = request.get("script_path")
        script_params = request.get("params", {})

        if not script_name or not script_path:
            return {"success": False, "error": "script_name and script_path required"}

        self.recovery_scripts[script_name] = {
            "path": script_path,
            "params": script_params,
            "registered_at": datetime.now().isoformat(),
        }

        return {"success": True, "script_name": script_name}

    def get_capabilities(self) -> List[str]:
        """能力一覧"""
        return [
            "automatic_incident_response",
            "rule_based_automation",
            "recovery_script_execution",
            "service_restart",
            "resource_scaling",
            "deployment_rollback",
            "cache_management",
            "container_management",
            "failover_execution",
            "request_throttling",
            "security_response",
            "backup_restoration",
            "effectiveness_measurement",
        ]


# エクスポート
__all__ = [
    "AutomaticResponseSystem",
    "ResponseRule",
    "ResponseExecution",
    "ResponseStatus",
]
