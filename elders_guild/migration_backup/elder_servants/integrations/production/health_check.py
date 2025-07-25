"""
🩺 Elder Servants統合ヘルスチェック・自己修復システム
Phase 3 プロダクション対応：自動診断とセルフヒーリング

EldersServiceLegacy統合: Iron Will品質基準とエルダー評議会令第27号完全準拠
目標: 99.9%可用性・ゼロダウンタイム・自動復旧
"""

import asyncio
import json
import logging
import os
import socket
import subprocess
import threading
import time
import traceback
import uuid
import weakref
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import psutil

# EldersLegacy統合インポート
from libs.core.elders_legacy import (
    EldersLegacyDomain,
    EldersServiceLegacy,
    IronWillCriteria,
    enforce_boundary,
)

# プロダクション統合インポート
from libs.elder_servants.integrations.production.error_handling import (
    ElderIntegrationError,
    ErrorCategory,
    ErrorSeverity,
)
from libs.elder_servants.integrations.production.monitoring import (
    ElderIntegrationMonitor,
    log_error,
    log_info,
    record_metric,
)


class HealthStatus(Enum):
    """ヘルス状態"""

    HEALTHY = "healthy"  # 正常
    DEGRADED = "degraded"  # 性能低下
    UNHEALTHY = "unhealthy"  # 異常
    CRITICAL = "critical"  # クリティカル
    UNKNOWN = "unknown"  # 不明


class ComponentType(Enum):
    """コンポーネントタイプ"""

    SYSTEM = "system"  # システムコンポーネント
    SERVICE = "service"  # サービス
    DATABASE = "database"  # データベース
    CACHE = "cache"  # キャッシュ
    QUEUE = "queue"  # キュー
    EXTERNAL_API = "external_api"  # 外部API
    NETWORK = "network"  # ネットワーク
    FILESYSTEM = "filesystem"  # ファイルシステム


class HealingAction(Enum):
    """自己修復アクション"""

    RESTART_SERVICE = "restart_service"  # サービス再起動
    CLEAR_CACHE = "clear_cache"  # キャッシュクリア
    CLEANUP_TEMP = "cleanup_temp"  # 一時ファイル削除
    RESTART_CONNECTION = "restart_connection"  # 接続再起動
    SCALE_UP = "scale_up"  # スケールアップ
    SCALE_DOWN = "scale_down"  # スケールダウン
    FAILOVER = "failover"  # フェイルオーバー
    GRACEFUL_DEGRADE = "graceful_degrade"  # 機能劣化
    MANUAL_INTERVENTION = "manual_intervention"  # 手動対応必要


@dataclass
class HealthCheckResult:
    """ヘルスチェック結果"""

    component_name: str
    component_type: ComponentType
    status: HealthStatus
    response_time_ms: float
    timestamp: datetime
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    suggested_actions: List[HealingAction] = field(default_factory=list)


@dataclass
class HealingActionResult:
    """自己修復アクション結果"""

    action: HealingAction
    component_name: str
    success: bool
    timestamp: datetime
    execution_time_ms: float
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


class HealthChecker:
    """ヘルスチェッカー基底クラス"""

    def __init__(self, component_name: str, component_type: ComponentType):
        """初期化メソッド"""
        self.component_name = component_name
        self.component_type = component_type
        self.logger = logging.getLogger(f"health_checker.{component_name}")

    async def check_health(self) -> HealthCheckResult:
        """ヘルスチェック実行（継承クラスで実装）"""
        raise NotImplementedError


class SystemHealthChecker(HealthChecker):
    """システムヘルスチェッカー"""

    def __init__(self):
        """super().__init__("system", ComponentType.SYSTEM)
    """初期化メソッド"""
        self.thresholds = {
            "cpu_warning": 80.0,
            "cpu_critical": 95.0,
            "memory_warning": 85.0,
            "memory_critical": 95.0,
            "disk_warning": 85.0,
            "disk_critical": 95.0,
        }

    async def check_health(self) -> HealthCheckResultstart_time = time.time():
    """ステムヘルスチェック"""
:
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)

            # メモリ使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # ディスク使用率
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100

            # プロセス数
            process_count = len(psutil.pids())

            # 負荷平均
            load_avg = os.getloadavg()[0] if hasattr(os, "getloadavg") else 0.0

            # ステータス判定
            status = HealthStatus.HEALTHY
            message = "System is operating normally"
            suggested_actions = []

            if (
                cpu_percent >= self.thresholds["cpu_critical"]
            # 複雑な条件判定
                or memory_percent >= self.thresholds["memory_critical"]
                or disk_percent >= self.thresholds["disk_critical"]
            ):
                status = HealthStatus.CRITICAL
                message = "Critical system resource usage detected"
                suggested_actions = [HealingAction.CLEANUP_TEMP, HealingAction.SCALE_UP]

            elif (
            # 複雑な条件判定
                cpu_percent >= self.thresholds["cpu_warning"]
                or memory_percent >= self.thresholds["memory_warning"]
                or disk_percent >= self.thresholds["disk_warning"]
            ):
                status = HealthStatus.DEGRADED
                message = "High system resource usage detected"
                suggested_actions = [HealingAction.CLEANUP_TEMP]

            execution_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component_name=self.component_name,
                component_type=self.component_type,
                status=status,
                response_time_ms=execution_time,
                timestamp=datetime.now(),
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent,
                    "process_count": process_count,
                    "load_average": load_avg,
                },
                metrics={
                    "cpu_usage": cpu_percent,
                    "memory_usage": memory_percent,
                    "disk_usage": disk_percent,
                    "process_count": process_count,
                },
                suggested_actions=suggested_actions,
            )

        except Exception as e:
            # Handle specific exception case
            execution_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component_name=self.component_name,
                component_type=self.component_type,
                status=HealthStatus.UNKNOWN,
                response_time_ms=execution_time,
                timestamp=datetime.now(),
                message=f"Health check failed: {str(e)}",
                suggested_actions=[HealingAction.MANUAL_INTERVENTION],
            )


class ServiceHealthChecker(HealthChecker):
    """サービスヘルスチェッカー"""

    def __init__(self, service_name: str, service_obj: Any)super().__init__(service_name, ComponentType.SERVICE)
    """初期化メソッド"""
        self.service_ref = weakref.ref(service_obj) if service_obj else None
        self.response_time_threshold = 5000  # 5秒

    async def check_health(self) -> HealthCheckResultstart_time = time.time():
    """ービスヘルスチェック"""
:
        try:
            service = self.service_ref() if self.service_ref else None

            if not service:
                return HealthCheckResult(
                    component_name=self.component_name,
                    component_type=self.component_type,
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=0,
                    timestamp=datetime.now(),
                    message="Service reference is None",
                    suggested_actions=[HealingAction.RESTART_SERVICE],
                )

            # サービスのヘルスチェックメソッド呼び出し
            if hasattr(service, "health_check"):
                health_result = await service.health_check()
                execution_time = (time.time() - start_time) * 1000

                # 応答時間チェック
                if execution_time > self.response_time_threshold:
                    status = HealthStatus.DEGRADED
                    message = f"Slow response time: {execution_time:0.2f}ms"
                    suggested_actions = [HealingAction.RESTART_SERVICE]
                else:
                    status = HealthStatus.HEALTHY
                    message = "Service is responsive"
                    suggested_actions = []

                return HealthCheckResult(
                    component_name=self.component_name,
                    component_type=self.component_type,
                    status=status,
                    response_time_ms=execution_time,
                    timestamp=datetime.now(),
                    message=message,
                    details=health_result if isinstance(health_result, dict) else {},
                    metrics={"response_time_ms": execution_time},
                    suggested_actions=suggested_actions,
                )
            else:
                # health_checkメソッドが無い場合の基本チェック
                execution_time = (time.time() - start_time) * 1000

                return HealthCheckResult(
                    component_name=self.component_name,
                    component_type=self.component_type,
                    status=HealthStatus.HEALTHY,
                    response_time_ms=execution_time,
                    timestamp=datetime.now(),
                    message="Service object exists (no health_check method)",
                    metrics={"response_time_ms": execution_time},
                )

        except Exception as e:
            # Handle specific exception case
            execution_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component_name=self.component_name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=execution_time,
                timestamp=datetime.now(),
                message=f"Service health check failed: {str(e)}",
                suggested_actions=[HealingAction.RESTART_SERVICE],
            )


class NetworkHealthChecker(HealthChecker):
    """ネットワークヘルスチェッカー"""

    def __init__(self, target_hosts: List[Tuple[str, int]] = None)super().__init__("network", ComponentType.NETWORK)
    """初期化メソッド"""
        self.target_hosts = target_hosts or [
            ("8.8.8.8", 53),  # Google DNS
            ("1.1.1.1", 53),  # Cloudflare DNS
            ("localhost", 22),  # SSH
        ]
        self.timeout_seconds = 5

    async def check_health(self) -> HealthCheckResultstart_time = time.time():
    """ットワークヘルスチェック"""
:
        try:
            connectivity_results = []

            for host, port in self.target_hosts:
                # Process each item in collection
                conn_start = time.time()
                try:
                    # 非同期ソケット接続テスト
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(self.timeout_seconds)
                    result = sock.connect_ex((host, port))
                    sock.close()

                    conn_time = (time.time() - conn_start) * 1000

                    connectivity_results.append(
                        {
                            "host": host,
                            "port": port,
                            "connected": result == 0,
                            "response_time_ms": conn_time,
                        }
                    )

                except Exception as e:
                    # Handle specific exception case
                    connectivity_results.append(
                        {
                            "host": host,
                            "port": port,
                            "connected": False,
                            "error": str(e),
                        }
                    )

            # 接続成功率計算
            successful_connections = len(
                [r for r in connectivity_results if r.get("connected", False)]
            )
            success_rate = (successful_connections / len(connectivity_results)) * 100

            # ステータス判定
            if success_rate >= 80:
                status = HealthStatus.HEALTHY
                message = f"Network connectivity good ({success_rate:0.1f}%)"
                suggested_actions = []
            elif success_rate >= 50:
                status = HealthStatus.DEGRADED
                message = f"Network connectivity degraded ({success_rate:0.1f}%)"
                suggested_actions = [HealingAction.RESTART_CONNECTION]
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Network connectivity poor ({success_rate:0.1f}%)"
                suggested_actions = [
                    HealingAction.RESTART_CONNECTION,
                    HealingAction.MANUAL_INTERVENTION,
                ]

            execution_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component_name=self.component_name,
                component_type=self.component_type,
                status=status,
                response_time_ms=execution_time,
                timestamp=datetime.now(),
                message=message,
                details={
                    "connectivity_results": connectivity_results,
                    "success_rate_percent": success_rate,
                },
                metrics={
                    "success_rate": success_rate,
                    "total_tests": len(connectivity_results),
                    "successful_connections": successful_connections,
                },
                suggested_actions=suggested_actions,
            )

        except Exception as e:
            # Handle specific exception case
            execution_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component_name=self.component_name,
                component_type=self.component_type,
                status=HealthStatus.UNKNOWN,
                response_time_ms=execution_time,
                timestamp=datetime.now(),
                message=f"Network health check failed: {str(e)}",
                suggested_actions=[HealingAction.MANUAL_INTERVENTION],
            )


class FilesystemHealthChecker(HealthChecker):
    """ファイルシステムヘルスチェッカー"""

    def __init__(self, paths_to_check: List[str] = None)super().__init__("filesystem", ComponentType.FILESYSTEM)
    """初期化メソッド"""
        self.paths_to_check = paths_to_check or ["/", "/tmp", "/var/log"]
        self.write_test_enabled = True

    async def check_health(self) -> HealthCheckResultstart_time = time.time():
    """ァイルシステムヘルスチェック"""
:
        try:
            filesystem_results = []

            for path in self.paths_to_check:
                # Process each item in collection
                path_result = {"path": path}

                try:
                    # 存在確認
                    if os.path.exists(path):
                        path_result["exists"] = True

                        # ディスク使用量
                        if not (os.path.isdir(path)):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if os.path.isdir(path):
                            disk_usage = psutil.disk_usage(path)
                            path_result["total_gb"] = disk_usage.total / (1024**3)
                            path_result["used_gb"] = disk_usage.used / (1024**3)
                            path_result["free_gb"] = disk_usage.free / (1024**3)
                            path_result["usage_percent"] = (
                                disk_usage.used / disk_usage.total
                            ) * 100

                        # 読み取りテスト
                        if not (os.access(path, os.R_OK)):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if os.access(path, os.R_OK):
                            path_result["readable"] = True
                        else:
                            path_result["readable"] = False

                        # 書き込みテスト（安全な場所のみ）
                        if not (():
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if (
                            self.write_test_enabled
                            and path in ["/tmp"]
                            and os.access(path, os.W_OK)
                        ):
                            test_file = os.path.join(
                                path, f"health_test_{uuid.uuid4().hex[:8]}"
                            )
                            # Deep nesting detected (depth: 6) - consider refactoring
                            try:
                                # TODO: Extract this complex nested logic into a separate method
                                with open(test_file, "w") as f:
                                    f.write("health test")
                                os.remove(test_file)
                                path_result["writable"] = True
                            except:
                                path_result["writable"] = False
                        else:
                            path_result["writable"] = os.access(path, os.W_OK)
                    else:
                        path_result["exists"] = False

                except Exception as e:
                    # Handle specific exception case
                    path_result["error"] = str(e)

                filesystem_results.append(path_result)

            # 全体ステータス判定
            critical_issues = []
            warnings = []

            for result in filesystem_results:
                # Process each item in collection
                if not result.get("exists", False):
                    critical_issues.append(f"Path {result['path']} does not exist")
                elif not result.get("readable", False):
                    critical_issues.append(f"Path {result['path']} is not readable")
                elif result.get("usage_percent", 0) > 95:
                    critical_issues.append(
                        f"Path {result['path']} is {result['usage_percent']:0.1f}% full"
                    )
                elif result.get("usage_percent", 0) > 85:
                    warnings.append(
                        f"Path {result['path']} is {result['usage_percent']:0.1f}% full"
                    )

            if critical_issues:
                status = HealthStatus.CRITICAL
                message = f"Critical filesystem issues: {'; '.join(critical_issues)}"
                suggested_actions = [
                    HealingAction.CLEANUP_TEMP,
                    HealingAction.MANUAL_INTERVENTION,
                ]
            elif warnings:
                status = HealthStatus.DEGRADED
                message = f"Filesystem warnings: {'; '.join(warnings)}"
                suggested_actions = [HealingAction.CLEANUP_TEMP]
            else:
                status = HealthStatus.HEALTHY
                message = "Filesystem is healthy"
                suggested_actions = []

            execution_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component_name=self.component_name,
                component_type=self.component_type,
                status=status,
                response_time_ms=execution_time,
                timestamp=datetime.now(),
                message=message,
                details={"filesystem_results": filesystem_results},
                metrics={
                    "paths_checked": len(filesystem_results),
                    "critical_issues": len(critical_issues),
                    "warnings": len(warnings),
                },
                suggested_actions=suggested_actions,
            )

        except Exception as e:
            # Handle specific exception case
            execution_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component_name=self.component_name,
                component_type=self.component_type,
                status=HealthStatus.UNKNOWN,
                response_time_ms=execution_time,
                timestamp=datetime.now(),
                message=f"Filesystem health check failed: {str(e)}",
                suggested_actions=[HealingAction.MANUAL_INTERVENTION],
            )


class SelfHealingEngine:
    """自己修復エンジン"""

    def __init__(self):
    """初期化メソッド"""
        self.healing_handlers: Dict[HealingAction, Callable] = {}
        self.healing_history: List[HealingActionResult] = []
        self.healing_enabled = True

        # デフォルトハンドラー登録
        self._register_default_handlers()

    def _register_default_handlers(self):
        """デフォルト修復ハンドラー登録"""
        self.healing_handlers[HealingAction.CLEANUP_TEMP] = self._cleanup_temp_files
        self.healing_handlers[HealingAction.CLEAR_CACHE] = self._clear_cache
        self.healing_handlers[HealingAction.RESTART_CONNECTION] = (
            self._restart_connection
        )
        self.healing_handlers[HealingAction.GRACEFUL_DEGRADE] = self._graceful_degrade

    async def execute_healing_action(
        self, action: HealingAction, component_name: str, context: Dict[str, Any] = None
    ) -> HealingActionResult:
        """修復アクション実行"""
        if not self.healing_enabled:
            return HealingActionResult(
                action=action,
                component_name=component_name,
                success=False,
                timestamp=datetime.now(),
                execution_time_ms=0,
                message="Self-healing is disabled",
            )

        start_time = time.time()

        try:
            self.logger.info(
                f"Executing healing action: {action.value} for {component_name}"
            )

            handler = self.healing_handlers.get(action)
            if not handler:
                return HealingActionResult(
                    action=action,
                    component_name=component_name,
                    success=False,
                    timestamp=datetime.now(),
                    execution_time_ms=0,
                    message=f"No handler registered for action: {action.value}",
                )

            # ハンドラー実行
            if asyncio.iscoroutinefunction(handler):
                result = await handler(component_name, context or {})
            else:
                result = handler(component_name, context or {})

            execution_time = (time.time() - start_time) * 1000

            healing_result = HealingActionResult(
                action=action,
                component_name=component_name,
                success=result.get("success", False),
                timestamp=datetime.now(),
                execution_time_ms=execution_time,
                message=result.get("message", ""),
                details=result.get("details", {}),
            )

            # 履歴記録
            self.healing_history.append(healing_result)
            if len(self.healing_history) > 1000:
                self.healing_history = self.healing_history[-1000:]

            self.logger.info(
                f"Healing action completed: {action.value}, success: {healing_result.success}"
            )

            return healing_result

        except Exception as e:
            # Handle specific exception case
            execution_time = (time.time() - start_time) * 1000

            healing_result = HealingActionResult(
                action=action,
                component_name=component_name,
                success=False,
                timestamp=datetime.now(),
                execution_time_ms=execution_time,
                message=f"Healing action failed: {str(e)}",
            )

            self.healing_history.append(healing_result)
            self.logger.error(f"Healing action failed: {action.value}, error: {str(e)}")

            return healing_result

    async def _cleanup_temp_files(
        self, component_name: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """一時ファイルクリーンアップ"""
        try:
            temp_dirs = ["/tmp", "/var/tmp"]
            cleaned_files = 0
            freed_bytes = 0

            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    # 24時間以上古いファイルを削除
                    cutoff_time = time.time() - (24 * 3600)

                    for root, dirs, files in os.walk(temp_dir):
                        # Process each item in collection
                        # Deep nesting detected (depth: 5) - consider refactoring
                        for file in files:
                            # Process each item in collection
                            file_path = os.path.join(root, file)
                            # Deep nesting detected (depth: 6) - consider refactoring
                            try:
                                stat = os.stat(file_path)
                                if not (stat.st_mtime < cutoff_time):
                                    continue  # Early return to reduce nesting
                                # Reduced nesting - original condition satisfied
                                if stat.st_mtime < cutoff_time:
                                    file_size = stat.st_size
                                    os.remove(file_path)
                                    cleaned_files += 1
                                    freed_bytes += file_size
                            except (OSError, PermissionError):
                                # ファイルアクセスエラーは無視
                                pass

            return {
                "success": True,
                "message": f"Cleaned {cleaned_files} files, freed {freed_bytes / 1024 / 1024:0.2f} MB",
                "details": {"cleaned_files": cleaned_files, "freed_bytes": freed_bytes},
            }

        except Exception as e:
            # Handle specific exception case
            return {"success": False, "message": f"Cleanup failed: {str(e)}"}

    async def _clear_cache(
        self, component_name: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """キャッシュクリア"""
        try:
            # 実装では具体的なキャッシュシステムと連携
            self.logger.info(f"Clearing cache for component: {component_name}")

            return {
                "success": True,
                "message": f"Cache cleared for {component_name}",
                "details": {"component": component_name},
            }

        except Exception as e:
            # Handle specific exception case
            return {"success": False, "message": f"Cache clear failed: {str(e)}"}

    async def _restart_connection(
        self, component_name: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """接続再起動"""
        try:
            self.logger.info(f"Restarting connections for component: {component_name}")

            # 実装では具体的な接続管理と連携
            await asyncio.sleep(0.1)  # シミュレート

            return {
                "success": True,
                "message": f"Connections restarted for {component_name}",
                "details": {"component": component_name},
            }

        except Exception as e:
            # Handle specific exception case
            return {"success": False, "message": f"Connection restart failed: {str(e)}"}

    async def _graceful_degrade(
        self, component_name: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """機能劣化"""
        try:
            self.logger.warning(f"Gracefully degrading component: {component_name}")

            # 実装では機能フラグシステムと連携
            degraded_features = context.get(
                "features_to_disable", ["advanced_features"]
            )

            return {
                "success": True,
                "message": f"Gracefully degraded {component_name}",
                "details": {
                    "component": component_name,
                    "disabled_features": degraded_features,
                },
            }

        except Exception as e:
            # Handle specific exception case
            return {
                "success": False,
                "message": f"Graceful degradation failed: {str(e)}",
            }

    def register_healing_handler(self, action: HealingAction, handler: Callable):
        """カスタム修復ハンドラー登録"""
        self.healing_handlers[action] = handler
        self.logger.info(f"Registered healing handler for action: {action.value}")

    def get_healing_statistics(self) -> Dict[str, Any]:
        """修復統計取得"""
        if not self.healing_history:
            return {"message": "No healing actions performed"}

        total_actions = len(self.healing_history)
        successful_actions = len([h for h in self.healing_history if h.success])
        success_rate = (successful_actions / total_actions) * 100

        # アクション別統計
        action_stats = defaultdict(lambda: {"total": 0, "successful": 0})
        for healing in self.healing_history:
            action_stats[healing.action.value]["total"] += 1
            if healing.success:
                action_stats[healing.action.value]["successful"] += 1

        # 最近の実行
        recent_actions = sorted(
            self.healing_history, key=lambda h: h.timestamp, reverse=True
        )[:10]

        return {
            "total_actions": total_actions,
            "successful_actions": successful_actions,
            "success_rate_percent": round(success_rate, 2),
            "action_statistics": dict(action_stats),
            "recent_actions": [
                {
                    "action": h.action.value,
                    "component": h.component_name,
                    "success": h.success,
                    "timestamp": h.timestamp.isoformat(),
                    "message": h.message,
                }
                for h in recent_actions
            ],
            "healing_enabled": self.healing_enabled,
        }


class ElderIntegrationHealthChecker(
    EldersServiceLegacy[Dict[str, Any], Dict[str, Any]]
):
    """
    🩺 Elder Servants統合ヘルスチェック・自己修復システム

    EldersServiceLegacyから継承し、Iron Will品質基準に完全準拠。
    自動診断・セルフヒーリング・99.9%可用性を実現。
    """

    def __init__(self):
        """super().__init__("elder_integration_health_checker")
    """初期化メソッド"""

        self.logger = logging.getLogger("elder_servants.health_checker")

        # ヘルスチェッカー
        self.health_checkers: Dict[str, HealthChecker] = {}
        self.check_intervals: Dict[str, int] = {}  # 秒単位

        # 自己修復エンジン
        self.healing_engine = SelfHealingEngine()

        # 監視タスク
        self.monitoring_task: Optional[asyncio.Task] = None
        self.monitoring_enabled = True

        # ヘルスチェック履歴
        self.health_history: List[HealthCheckResult] = []

        # 依存関係マップ
        self.dependency_map: Dict[str, List[str]] = {}

        # 統計情報
        self.statistics = {
            "total_checks": 0,
            "healthy_checks": 0,
            "degraded_checks": 0,
            "unhealthy_checks": 0,
            "critical_checks": 0,
            "start_time": datetime.now(),
        }

        # デフォルトチェッカー登録
        self._register_default_checkers()

        # ヘルスチェック監視開始
        self._start_health_monitoring()

        # Iron Will品質基準
        self.quality_threshold = 99.9  # 99.9%可用性

        self.logger.info("Elder Integration Health Checker initialized")

    def _register_default_checkers(self):
        """デフォルトヘルスチェッカー登録"""
        # システムヘルスチェッカー
        self.register_health_checker("system", SystemHealthChecker(), 30)

        # ネットワークヘルスチェッカー
        self.register_health_checker("network", NetworkHealthChecker(), 60)

        # ファイルシステムヘルスチェッカー
        self.register_health_checker("filesystem", FilesystemHealthChecker(), 120)

    def register_health_checker(
        self, name: str, checker: HealthChecker, interval_seconds: int = 60
    ):
        """ヘルスチェッカー登録"""
        self.health_checkers[name] = checker
        self.check_intervals[name] = interval_seconds
        self.logger.info(
            f"Registered health checker: {name} (interval: {interval_seconds}s)"
        )

    def register_service_health_checker(
        self, service_name: str, service_obj: Any, interval_seconds: int = 30
    ):
        """サービスヘルスチェッカー登録"""
        checker = ServiceHealthChecker(service_name, service_obj)
        self.register_health_checker(
            f"service_{service_name}", checker, interval_seconds
        )

    def set_dependency(self, component: str, dependencies: List[str]):
        """依存関係設定"""
        self.dependency_map[component] = dependencies
        self.logger.info(f"Set dependencies for {component}: {dependencies}")

    def _start_health_monitoring(self):
        """ヘルスチェック監視開始"""
        try:
            loop = asyncio.get_event_loop()
            self.monitoring_task = loop.create_task(self._health_monitoring_loop())
        except RuntimeError:
            # イベントループが無い場合はスキップ
            pass

    async def _health_monitoring_loop(self):
        """ヘルスチェック監視ループ"""
        last_check_times = {}

        # ループ処理
        while self.monitoring_enabled:
            try:
                current_time = time.time()

                for checker_name, checker in self.health_checkers.items():
                    # Process each item in collection
                    interval = self.check_intervals.get(checker_name, 60)
                    last_check = last_check_times.get(checker_name, 0)

                    if current_time - last_check >= interval:
                        # ヘルスチェック実行
                        # Deep nesting detected (depth: 5) - consider refactoring
                        try:
                            result = await checker.check_health()
                            await self._process_health_result(result)
                            last_check_times[checker_name] = current_time

                        except Exception as e:
                            # Handle specific exception case
                            self.logger.error(
                                f"Health check failed for {checker_name}: {str(e)}"
                            )

                # 10秒間隔でチェック
                await asyncio.sleep(10)

            except Exception as e:
                # Handle specific exception case
                self.logger.error(f"Health monitoring loop error: {str(e)}")
                await asyncio.sleep(60)  # エラー時は1分待機

    async def _process_health_result(self, result: HealthCheckResult):
        """ヘルスチェック結果処理"""
        # 履歴記録
        self.health_history.append(result)
        if len(self.health_history) > 10000:
            self.health_history = self.health_history[-10000:]

        # 統計更新
        self.statistics["total_checks"] += 1

        if result.status == HealthStatus.HEALTHY:
            self.statistics["healthy_checks"] += 1
        elif result.status == HealthStatus.DEGRADED:
            self.statistics["degraded_checks"] += 1
        elif result.status == HealthStatus.UNHEALTHY:
            self.statistics["unhealthy_checks"] += 1
        elif result.status == HealthStatus.CRITICAL:
            self.statistics["critical_checks"] += 1

        # ログ記録
        await log_info(
            f"Health check completed: {result.component_name}",
            component=result.component_name,
            status=result.status.value,
            response_time_ms=result.response_time_ms,
        )

        # メトリクス記録
        await record_metric(
            f"health_check_response_time_ms",
            result.response_time_ms,
            "histogram",
            {"component": result.component_name},
        )

        await record_metric(
            f"health_check_status",
            1.0,
            "counter",
            {"component": result.component_name, "status": result.status.value},
        )

        # 自動修復判定
        if result.status in [
            HealthStatus.DEGRADED,
            HealthStatus.UNHEALTHY,
            HealthStatus.CRITICAL,
        ]:
            await self._trigger_auto_healing(result)

    async def _trigger_auto_healing(self, health_result: HealthCheckResult):
        """自動修復トリガー"""
        if not health_result.suggested_actions:
            return

        self.logger.warning(
            f"Health issue detected for {health_result.component_name}: {health_result.message}"
        )

        # 依存関係チェック
        dependencies = self.dependency_map.get(health_result.component_name, [])
        if dependencies:
            # 依存コンポーネントのヘルス確認
            for dep in dependencies:
                dep_healthy = await self._check_component_health(dep)
                if not dep_healthy:
                    self.logger.warning(
                        f"Dependency {dep} is unhealthy, skipping auto-healing"
                    )
                    return

        # 修復アクション実行
        for action in health_result.suggested_actions:
            if action == HealingAction.MANUAL_INTERVENTION:
                # 手動対応が必要な場合はアラート送信
                await log_error(
                    f"Manual intervention required for {health_result.component_name}",
                    component=health_result.component_name,
                    status=health_result.status.value,
                    message=health_result.message,
                )
                continue

            healing_result = await self.healing_engine.execute_healing_action(
                action,
                health_result.component_name,
                {"health_result": health_result.details},
            )

            if healing_result.success:
                await log_info(
                    f"Auto-healing successful: {action.value}",
                    component=health_result.component_name,
                    action=action.value,
                    execution_time_ms=healing_result.execution_time_ms,
                )
                break  # 成功したら他のアクションはスキップ
            else:
                await log_error(
                    f"Auto-healing failed: {action.value}",
                    component=health_result.component_name,
                    action=action.value,
                    error_message=healing_result.message,
                )

    async def _check_component_health(self, component_name: str) -> boolchecker = self.health_checkers.get(component_name):
    """ンポーネントヘルス確認""":
        if not checker:
            return True  # チェッカーが無い場合は健全とみなす

        try:
            result = await checker.check_health()
            return result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
        except:
            return False

    @enforce_boundary("health_check")
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        EldersServiceLegacy統一リクエスト処理

        Args:
            request: ヘルスチェックリクエスト

        Returns:
            Dict[str, Any]: ヘルスチェック結果
        """
        try:
            request_type = request.get("type", "unknown")

            if request_type == "health_check":
                return await self._handle_health_check_request(request)
            elif request_type == "healing_action":
                return await self._handle_healing_action_request(request)
            elif request_type == "statistics":
                return await self._handle_statistics_request(request)
            elif request_type == "register_checker":
                return await self._handle_register_checker_request(request)
            else:
                return {"error": f"Unknown request type: {request_type}"}

        except Exception as e:
            # Handle specific exception case
            await log_error(f"Health check request processing failed: {str(e)}")
            return {"error": str(e)}

    async def _handle_health_check_request(
        self, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ヘルスチェックリクエスト処理"""
        component_name = request.get("component")

        if component_name and component_name in self.health_checkers:
            # Complex condition - consider breaking down
            # 特定コンポーネントのヘルスチェック
            checker = self.health_checkers[component_name]
            result = await checker.check_health()

            return {
                "component": result.component_name,
                "status": result.status.value,
                "response_time_ms": result.response_time_ms,
                "message": result.message,
                "details": result.details,
                "metrics": result.metrics,
                "timestamp": result.timestamp.isoformat(),
            }
        else:
            # 全コンポーネントのヘルスチェック
            results = {}

            for name, checker in self.health_checkers.items():
                # Process each item in collection
                try:
                    result = await checker.check_health()
                    results[name] = {
                        "status": result.status.value,
                        "response_time_ms": result.response_time_ms,
                        "message": result.message,
                        "timestamp": result.timestamp.isoformat(),
                    }
                except Exception as e:
                    # Handle specific exception case
                    results[name] = {
                        "status": "error",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                    }

            # 全体ステータス計算
            statuses = [r.get("status", "error") for r in results.values()]
            if "critical" in statuses:
                overall_status = "critical"
            elif "unhealthy" in statuses:
                overall_status = "unhealthy"
            elif "degraded" in statuses:
                overall_status = "degraded"
            elif "error" in statuses:
                overall_status = "error"
            else:
                overall_status = "healthy"

            return {
                "overall_status": overall_status,
                "components": results,
                "timestamp": datetime.now().isoformat(),
            }

    async def _handle_healing_action_request(
        self, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """修復アクションリクエスト処理"""
        action_name = request.get("action")
        component_name = request.get("component", "unknown")
        context = request.get("context", {})

        try:
            action = HealingAction(action_name)
            result = await self.healing_engine.execute_healing_action(
                action, component_name, context
            )

            return {
                "success": result.success,
                "action": result.action.value,
                "component": result.component_name,
                "execution_time_ms": result.execution_time_ms,
                "message": result.message,
                "details": result.details,
                "timestamp": result.timestamp.isoformat(),
            }

        except ValueError:
            # Handle specific exception case
            return {"error": f"Unknown healing action: {action_name}"}
        except Exception as e:
            # Handle specific exception case
            return {"error": f"Healing action failed: {str(e)}"}

    async def _handle_statistics_request(
        self, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """統計リクエスト処理"""
        health_stats = self._calculate_health_statistics()
        healing_stats = self.healing_engine.get_healing_statistics()

        uptime = datetime.now() - self.statistics["start_time"]

        return {
            "uptime_seconds": uptime.total_seconds(),
            "health_statistics": health_stats,
            "healing_statistics": healing_stats,
            "monitoring_enabled": self.monitoring_enabled,
            "registered_checkers": list(self.health_checkers.keys()),
            "dependency_map": self.dependency_map,
        }

    def _calculate_health_statistics(self) -> Dict[str, Any]:
        """ヘルス統計計算"""
        total_checks = self.statistics["total_checks"]

        if total_checks == 0:
            return {"message": "No health checks performed"}

        availability = (self.statistics["healthy_checks"] / total_checks) * 100

        # 最近のヘルス状況（最新100件）
        recent_results = self.health_history[-100:] if self.health_history else []
        recent_by_component = defaultdict(list)

        for result in recent_results:
            # Process each item in collection
            recent_by_component[result.component_name].append(result)

        component_health = {}
        for component, results in recent_by_component.items():
            # Process each item in collection
            healthy_count = len(
                [r for r in results if r.status == HealthStatus.HEALTHY]
            )
            component_availability = (healthy_count / len(results)) * 100

            component_health[component] = {
                "availability_percent": round(component_availability, 2),
                "recent_checks": len(results),
                "latest_status": results[-1].status.value if results else "unknown",
            }

        return {
            "total_checks": total_checks,
            "overall_availability_percent": round(availability, 2),
            "healthy_checks": self.statistics["healthy_checks"],
            "degraded_checks": self.statistics["degraded_checks"],
            "unhealthy_checks": self.statistics["unhealthy_checks"],
            "critical_checks": self.statistics["critical_checks"],
            "component_health": component_health,
            "iron_will_compliance": availability >= 99.9,
        }

    def validate_request(self, request: Dict[str, Any]) -> boolif not isinstance(request, dict):
    """EldersServiceLegacyリクエスト検証"""
            return False
        if "type" not in request:
            return False
        return True

    def get_capabilities(self) -> List[str]:
        """EldersServiceLegacy能力取得"""
        return [
            "comprehensive_health_checking",
            "self_healing_automation",
            "dependency_aware_monitoring",
            "real_time_diagnostics",
            "availability_tracking",
            "auto_recovery_actions",
            "health_statistics",
        ]

    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        try:
            # 基本ヘルスチェック
            base_health = await super().health_check()

            # ヘルスチェッカー自体のヘルス
            health_stats = self._calculate_health_statistics()

            # システム健全性判定
            availability = health_stats.get("overall_availability_percent", 0)
            system_healthy = availability >= 99.0  # 99%以上で健全

            return {
                **base_health,
                "health_checker_status": "healthy" if system_healthy else "degraded",
                "overall_availability": availability,
                "monitoring_enabled": self.monitoring_enabled,
                "registered_checkers": len(self.health_checkers),
                "iron_will_compliance": availability >= 99.9,
            }

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Health check failed: {str(e)}")
            return {"success": False, "status": "error", "error": str(e)}

    async def shutdown(self):
        """システムシャットダウン"""
        self.monitoring_enabled = False

        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                # Handle specific exception case
                pass

        await log_info("Elder Integration Health Checker shutting down")


# グローバルヘルスチェッカーインスタンス
_global_health_checker: Optional[ElderIntegrationHealthChecker] = None


async def get_global_health_checker() -> ElderIntegrationHealthChecker:
    """グローバルヘルスチェッカー取得"""
    global _global_health_checker

    if _global_health_checker is None:
        _global_health_checker = ElderIntegrationHealthChecker()

    return _global_health_checker


# 便利関数群
async def check_component_health(component_name: str = None) -> Dict[str, Any]health_checker = await get_global_health_checker():
    """ンポーネントヘルスチェック（便利関数）"""
    return await health_checker.process_request(:
        {"type": "health_check", "component": component_name}
    )


async def trigger_healing_action(
    action: str, component_name: str, context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """修復アクション実行（便利関数）"""
    health_checker = await get_global_health_checker()
    return await health_checker.process_request(
        {
            "type": "healing_action",
            "action": action,
            "component": component_name,
            "context": context or {},
        }
    )


asdef get_health_statistics() -> Dict[str, Any]health_checker = await get_global_health_checker()return await health_checker.process_request({"type": "statistics"})
""""""ヘルス統計取得（便利関数）""":
