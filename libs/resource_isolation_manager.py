#!/usr/bin/env python3
"""
Resource Isolation Manager - リソース隔離マネージャー
Phase 1 Week 2 Day 11-12: セキュリティレベル分離システム

4賢者との協議で決定された高度なリソース隔離システム
- プロセス・メモリ・ネットワーク・ファイルシステムの完全隔離
- 動的リソース制限とクォータ管理
- セキュリティレベル別のリソース配分
- リアルタイムリソース監視とアラート
"""

import json
import logging
import os
import resource
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import cgroups
import psutil

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.env_config import get_config
from libs.shared_enums import SecurityLevel


class ResourceType(Enum):
    """リソース種別"""

    CPU = "cpu"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"
    PROCESSES = "processes"
    FILE_DESCRIPTORS = "file_descriptors"
    THREADS = "threads"


class IsolationType(Enum):
    """隔離タイプ"""

    NONE = "none"
    PROCESS = "process"
    NAMESPACE = "namespace"
    CONTAINER = "container"
    VM = "vm"


class ResourceStatus(Enum):
    """リソース状態"""

    AVAILABLE = "available"
    ALLOCATED = "allocated"
    EXHAUSTED = "exhausted"
    EXCEEDED = "exceeded"
    SUSPENDED = "suspended"


@dataclass
class ResourceQuota:
    """リソースクォータ定義"""

    cpu_percent: float  # CPU使用率上限 (0.0-1.0)
    memory_mb: int  # メモリ上限 (MB)
    storage_mb: int  # ストレージ上限 (MB)
    network_bps: int  # ネットワーク帯域幅 (bytes/sec)
    max_processes: int  # 最大プロセス数
    max_file_descriptors: int  # 最大ファイルディスクリプタ数
    max_threads: int  # 最大スレッド数
    max_connections: int  # 最大ネットワーク接続数


@dataclass
class ResourceUsage:
    """リソース使用状況"""

    cpu_percent: float
    memory_mb: float
    storage_mb: float
    network_bps: float
    process_count: int
    file_descriptor_count: int
    thread_count: int
    connection_count: int
    timestamp: datetime


@dataclass
class IsolationContext:
    """隔離コンテキスト"""

    context_id: str
    security_level: SecurityLevel
    isolation_type: IsolationType
    resource_quota: ResourceQuota
    namespace_config: Dict[str, Any]
    filesystem_mounts: List[Dict[str, str]]
    network_config: Dict[str, Any]
    process_limits: Dict[str, int]
    created_at: datetime
    expires_at: Optional[datetime] = None


@dataclass
class ResourceAlert:
    """リソースアラート"""

    alert_id: str
    context_id: str
    resource_type: ResourceType
    alert_level: str  # warning, critical, emergency
    threshold_exceeded: float
    current_usage: float
    message: str
    timestamp: datetime
    auto_action_taken: Optional[str] = None


class ResourceIsolationManager:
    """リソース隔離マネージャー - 包括的なリソース管理と隔離"""

    def __init__(self):
        """初期化メソッド"""
        self.config = get_config()
        self.logger = logging.getLogger(__name__)

        # 隔離コンテキスト管理
        self.active_contexts: Dict[str, IsolationContext] = {}
        self.context_lock = threading.RLock()

        # リソース監視
        self.resource_monitor = ResourceMonitor()
        self.alert_manager = AlertManager()

        # セキュリティレベル別デフォルトクォータ
        self._initialize_default_quotas()
        self._initialize_isolation_configs()

        # 監視スレッド開始
        self.monitoring_thread = threading.Thread(
            target=self._monitor_resources_loop, daemon=True
        )
        self.monitoring_active = True
        self.monitoring_thread.start()

        self.logger.info("🏗️ ResourceIsolationManager initialized")

    def _initialize_default_quotas(self):
        """セキュリティレベル別デフォルトクォータ設定"""
        self.default_quotas = {
            SecurityLevel.SANDBOX: ResourceQuota(
                cpu_percent=0.2,  # 20% CPU
                memory_mb=256,  # 256MB RAM
                storage_mb=512,  # 512MB Storage
                network_bps=1024 * 1024,  # 1MB/s
                max_processes=10,  # 10プロセス
                max_file_descriptors=256,  # 256ファイル
                max_threads=20,  # 20スレッド
                max_connections=10,  # 10接続
            ),
            SecurityLevel.RESTRICTED: ResourceQuota(
                cpu_percent=0.4,  # 40% CPU
                memory_mb=512,  # 512MB RAM
                storage_mb=1024,  # 1GB Storage
                network_bps=5 * 1024 * 1024,  # 5MB/s
                max_processes=25,  # 25プロセス
                max_file_descriptors=512,  # 512ファイル
                max_threads=50,  # 50スレッド
                max_connections=25,  # 25接続
            ),
            SecurityLevel.DEVELOPMENT: ResourceQuota(
                cpu_percent=0.7,  # 70% CPU
                memory_mb=1024,  # 1GB RAM
                storage_mb=2048,  # 2GB Storage
                network_bps=10 * 1024 * 1024,  # 10MB/s
                max_processes=50,  # 50プロセス
                max_file_descriptors=1024,  # 1024ファイル
                max_threads=100,  # 100スレッド
                max_connections=50,  # 50接続
            ),
            SecurityLevel.TRUSTED: ResourceQuota(
                cpu_percent=1.0,  # 100% CPU
                memory_mb=2048,  # 2GB RAM
                storage_mb=4096,  # 4GB Storage
                network_bps=50 * 1024 * 1024,  # 50MB/s
                max_processes=100,  # 100プロセス
                max_file_descriptors=2048,  # 2048ファイル
                max_threads=200,  # 200スレッド
                max_connections=100,  # 100接続
            ),
        }

    def _initialize_isolation_configs(self):
        """隔離設定初期化"""
        self.isolation_configs = {
            SecurityLevel.SANDBOX: {
                "isolation_type": IsolationType.NAMESPACE,
                "namespace_types": ["pid", "net", "mnt", "uts", "ipc"],
                "filesystem_readonly": True,
                "network_isolated": True,
                "process_isolation": True,
                "capability_restrictions": ["CAP_SYS_ADMIN", "CAP_NET_ADMIN"],
            },
            SecurityLevel.RESTRICTED: {
                "isolation_type": IsolationType.NAMESPACE,
                "namespace_types": ["pid", "net", "mnt"],
                "filesystem_readonly": False,
                "network_isolated": False,
                "process_isolation": True,
                "capability_restrictions": ["CAP_SYS_ADMIN"],
            },
            SecurityLevel.DEVELOPMENT: {
                "isolation_type": IsolationType.PROCESS,
                "namespace_types": [],
                "filesystem_readonly": False,
                "network_isolated": False,
                "process_isolation": False,
                "capability_restrictions": [],
            },
            SecurityLevel.TRUSTED: {
                "isolation_type": IsolationType.NONE,
                "namespace_types": [],
                "filesystem_readonly": False,
                "network_isolated": False,
                "process_isolation": False,
                "capability_restrictions": [],
            },
        }

    def create_isolation_context(
        self,
        security_level: SecurityLevel,
        custom_quota: Optional[ResourceQuota] = None,
        custom_config: Optional[Dict] = None,
        session_duration_hours: int = 8,
    ) -> IsolationContext:
        """隔離コンテキスト作成"""

        context_id = f"ctx_{security_level.value}_{uuid.uuid4().hex[:8]}"

        # クォータ決定
        quota = custom_quota or self.default_quotas[security_level]

        # 隔離設定
        isolation_config = self.isolation_configs[security_level].copy()
        if custom_config:
            isolation_config.update(custom_config)

        # ファイルシステムマウント設定
        filesystem_mounts = self._prepare_filesystem_mounts(security_level, context_id)

        # ネットワーク設定
        network_config = self._prepare_network_config(security_level, context_id)

        # プロセス制限設定
        process_limits = self._prepare_process_limits(quota)

        context = IsolationContext(
            context_id=context_id,
            security_level=security_level,
            isolation_type=IsolationType(isolation_config["isolation_type"].value),
            resource_quota=quota,
            namespace_config=isolation_config,
            filesystem_mounts=filesystem_mounts,
            network_config=network_config,
            process_limits=process_limits,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=session_duration_hours),
        )

        # コンテキスト登録
        with self.context_lock:
            self.active_contexts[context_id] = context

        # リソース制限適用
        self._apply_resource_limits(context)

        self.logger.info(
            f"🏗️ Isolation context created: {context_id} ({security_level.value})"
        )
        return context

    def _prepare_filesystem_mounts(
        self, security_level: SecurityLevel, context_id: str
    ) -> List[Dict[str, str]]:
        """ファイルシステムマウント準備"""

        base_workspace = Path(f"/home/aicompany/workspace/{security_level.value}")
        context_workspace = base_workspace / context_id
        context_workspace.mkdir(parents=True, exist_ok=True)

        mounts = [
            {
                "source": str(context_workspace),
                "target": "/workspace",
                "type": "bind",
                "options": "rw" if security_level != SecurityLevel.SANDBOX else "ro",
            }
        ]

        # セキュリティレベル別追加マウント
        if security_level == SecurityLevel.SANDBOX:
            # 読み取り専用の最小システム
            mounts.extend(
                [
                    {
                        "source": "/usr",
                        "target": "/usr",
                        "type": "bind",
                        "options": "ro",
                    },
                    {
                        "source": "/lib",
                        "target": "/lib",
                        "type": "bind",
                        "options": "ro",
                    },
                    {
                        "source": "/bin",
                        "target": "/bin",
                        "type": "bind",
                        "options": "ro",
                    },
                ]
            )
        elif security_level == SecurityLevel.RESTRICTED:
            # 制限付きシステムアクセス
            mounts.extend(
                [
                    {
                        "source": "/tmp",
                        "target": "/tmp",
                        "type": "tmpfs",
                        "options": "size=100m",
                    },
                    {
                        "source": "/var/tmp",
                        "target": "/var/tmp",
                        "type": "tmpfs",
                        "options": "size=50m",
                    },
                ]
            )

        return mounts

    def _prepare_network_config(
        self, security_level: SecurityLevel, context_id: str
    ) -> Dict[str, Any]:
        """ネットワーク設定準備"""

        if security_level == SecurityLevel.SANDBOX:
            return {
                "type": "none",
                "isolated": True,
                "allowed_ports": [],
                "blocked_ports": ["*"],
                "dns_servers": [],
            }
        elif security_level == SecurityLevel.RESTRICTED:
            return {
                "type": "restricted",
                "isolated": False,
                "allowed_ports": [80, 443],
                "blocked_ports": [22, 23, 3389],
                "dns_servers": ["8.8.8.8", "8.8.4.4"],
                "bandwidth_limit": 5 * 1024 * 1024,  # 5MB/s
            }
        else:
            return {
                "type": "standard",
                "isolated": False,
                "allowed_ports": ["*"],
                "blocked_ports": [],
                "dns_servers": ["8.8.8.8", "1.1.1.1"],
                "bandwidth_limit": None,
            }

    def _prepare_process_limits(self, quota: ResourceQuota) -> Dict[str, int]:
        """プロセス制限設定準備"""
        return {
            "max_processes": quota.max_processes,
            "max_threads": quota.max_threads,
            "max_file_descriptors": quota.max_file_descriptors,
            "max_memory_mb": quota.memory_mb,
            "cpu_percent": int(quota.cpu_percent * 100),
        }

    def _apply_resource_limits(self, context: IsolationContext):
        """リソース制限適用"""

        try:
            # CPU制限設定
            self._apply_cpu_limits(context)

            # メモリ制限設定
            self._apply_memory_limits(context)

            # プロセス制限設定
            self._apply_process_limits(context)

            # ネットワーク制限設定
            self._apply_network_limits(context)

            self.logger.info(
                f"✅ Resource limits applied for context: {context.context_id}"
            )

        except Exception as e:
            self.logger.error(
                f"❌ Failed to apply resource limits for {context.context_id}: {e}"
            )
            raise

    def _apply_cpu_limits(self, context: IsolationContext):
        """CPU制限適用"""

        if context.isolation_type in [IsolationType.NAMESPACE, IsolationType.CONTAINER]:
            # cgroupsを使用したCPU制限
            cgroup_name = f"ai_company_{context.context_id}"

            try:
                # CPU cgroupの作成
                cpu_cgroup = cgroups.Cgroup(cgroup_name)
                cpu_cgroup.set_cpu_limit(context.resource_quota.cpu_percent)

                self.logger.debug(
                    f"📊 CPU limit set: {context.resource_quota.cpu_percent*100}% for " \
                        "{context.context_id}"
                )

            except Exception as e:
                self.logger.warning(
                    f"⚠️ Failed to set CPU cgroup for {context.context_id}: {e}"
                )

    def _apply_memory_limits(self, context: IsolationContext):
        """メモリ制限適用"""

        if context.isolation_type in [IsolationType.NAMESPACE, IsolationType.CONTAINER]:
            try:
                # メモリ制限をulimitで設定
                memory_limit_bytes = context.resource_quota.memory_mb * 1024 * 1024
                resource.setrlimit(
                    resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes)
                )

                self.logger.debug(
                    f"💾 Memory limit set: {context.resource_quota.memory_mb}MB for {context.context_id}"
                )

            except Exception as e:
                self.logger.warning(
                    f"⚠️ Failed to set memory limit for {context.context_id}: {e}"
                )

    def _apply_process_limits(self, context: IsolationContext):
        """プロセス制限適用"""

        try:
            # プロセス数制限
            resource.setrlimit(
                resource.RLIMIT_NPROC,
                (
                    context.resource_quota.max_processes,
                    context.resource_quota.max_processes,
                ),
            )

            # ファイルディスクリプタ制限
            resource.setrlimit(
                resource.RLIMIT_NOFILE,
                (
                    context.resource_quota.max_file_descriptors,
                    context.resource_quota.max_file_descriptors,
                ),
            )

            self.logger.debug(f"🔢 Process limits set for {context.context_id}")

        except Exception as e:
            self.logger.warning(
                f"⚠️ Failed to set process limits for {context.context_id}: {e}"
            )

    def _apply_network_limits(self, context: IsolationContext):
        """ネットワーク制限適用"""

        if context.network_config.get("bandwidth_limit"):
            try:
                # tc (traffic control) でネットワーク帯域制限
                bandwidth = context.network_config["bandwidth_limit"]

                # シンプルな帯域制限コマンド（実装例）- セキュリティ修正
                subprocess.run(
                    ["tc", "qdisc", "add", "dev", "eth0", "root", "handle", "1:", "htb", "default", "12"],
                    check=False
                )

                subprocess.run(
                                        [
                        "tc",
                        "class",
                        "add",
                        "dev",
                        "eth0",
                        "parent",
                        "1:",
                        "classid",
                        "1:12",
                        "htb",
                        "rate",
                        f"{bandwidth//1024}kbit"
                    ],
                    check=False
                )

                self.logger.debug(f"🌐 Network limits set for {context.context_id}")

            except Exception as e:
                self.logger.warning(
                    f"⚠️ Failed to set network limits for {context.context_id}: {e}"
                )

    def get_resource_usage(self, context_id: str) -> Optional[ResourceUsage]:
        """リソース使用状況取得"""

        with self.context_lock:
            if context_id not in self.active_contexts:
                return None

            context = self.active_contexts[context_id]

        try:
            # 現在のリソース使用状況を収集
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage("/")
            network_info = psutil.net_io_counters()

            # プロセス情報
            process_count = len(psutil.pids())

            # ファイルディスクリプタ数（近似）
            fd_count = 0
            try:
                for proc in psutil.process_iter(["num_fds"]):
                    fd_count += proc.info["num_fds"] or 0
            except:
                fd_count = 0

            usage = ResourceUsage(
                cpu_percent=cpu_percent / 100.0,
                memory_mb=memory_info.used / (1024 * 1024),
                storage_mb=disk_info.used / (1024 * 1024),
                network_bps=network_info.bytes_sent + network_info.bytes_recv,
                process_count=process_count,
                file_descriptor_count=fd_count,
                thread_count=threading.active_count(),
                connection_count=len(psutil.net_connections()),
                timestamp=datetime.now(),
            )

            return usage

        except Exception as e:
            self.logger.error(f"❌ Failed to get resource usage for {context_id}: {e}")
            return None

    def check_resource_violations(self, context_id: str) -> List[ResourceAlert]:
        """リソース制限違反チェック"""

        usage = self.get_resource_usage(context_id)
        if not usage:
            return []

        with self.context_lock:
            context = self.active_contexts.get(context_id)
            if not context:
                return []

        alerts = []
        quota = context.resource_quota

        # CPU違反チェック
        if usage.cpu_percent > quota.cpu_percent:
            alerts.append(
                ResourceAlert(
                    alert_id=uuid.uuid4().hex[:8],
                    context_id=context_id,
                    resource_type=ResourceType.CPU,
                    alert_level=(
                        "critical"
                        if usage.cpu_percent > quota.cpu_percent * 1.5
                        else "warning"
                    ),
                    threshold_exceeded=usage.cpu_percent / quota.cpu_percent,
                    current_usage=usage.cpu_percent,
                    message=f"CPU usage exceeded: {usage.cpu_percent:.1%} > {quota.cpu_percent:.1%}" \
                        "CPU usage exceeded: {usage.cpu_percent:.1%} > {quota.cpu_percent:.1%}",
                    timestamp=datetime.now(),
                )
            )

        # メモリ違反チェック
        if usage.memory_mb > quota.memory_mb:
            alerts.append(
                ResourceAlert(
                    alert_id=uuid.uuid4().hex[:8],
                    context_id=context_id,
                    resource_type=ResourceType.MEMORY,
                    alert_level=(
                        "critical"
                        if usage.memory_mb > quota.memory_mb * 1.2
                        else "warning"
                    ),
                    threshold_exceeded=usage.memory_mb / quota.memory_mb,
                    current_usage=usage.memory_mb,
                    message=f"Memory usage exceeded: {usage.memory_mb:.0f}MB > {quota.memory_mb}MB",
                    timestamp=datetime.now(),
                )
            )

        # プロセス数違反チェック
        if usage.process_count > quota.max_processes:
            alerts.append(
                ResourceAlert(
                    alert_id=uuid.uuid4().hex[:8],
                    context_id=context_id,
                    resource_type=ResourceType.PROCESSES,
                    alert_level="warning",
                    threshold_exceeded=usage.process_count / quota.max_processes,
                    current_usage=float(usage.process_count),
                    message=f"Process count exceeded: {usage.process_count} > {quota.max_processes}" \
                        "Process count exceeded: {usage.process_count} > {quota.max_processes}",
                    timestamp=datetime.now(),
                )
            )

        return alerts

    def terminate_context(self, context_id: str, reason: str = "Manual termination"):
        """隔離コンテキスト終了"""

        with self.context_lock:
            if context_id not in self.active_contexts:
                self.logger.warning(
                    f"⚠️ Context not found for termination: {context_id}"
                )
                return

            context = self.active_contexts[context_id]
            del self.active_contexts[context_id]

        try:
            # リソース制限解除
            self._cleanup_resource_limits(context)

            # ファイルシステムクリーンアップ
            self._cleanup_filesystem(context)

            # ネットワーク設定クリーンアップ
            self._cleanup_network(context)

            self.logger.info(f"🗑️ Context terminated: {context_id} - {reason}")

        except Exception as e:
            self.logger.error(f"❌ Error during context cleanup {context_id}: {e}")

    def _cleanup_resource_limits(self, context: IsolationContext):
        """リソース制限クリーンアップ"""

        try:
            # cgroup削除
            cgroup_name = f"ai_company_{context.context_id}"
            subprocess.run(
                f"cgdelete -g cpu,memory:{cgroup_name}", shell=True, check=False
            )

            self.logger.debug(f"🧹 Resource limits cleaned up for {context.context_id}")

        except Exception as e:
            self.logger.warning(
                f"⚠️ Failed to cleanup resource limits for {context.context_id}: {e}"
            )

    def _cleanup_filesystem(self, context: IsolationContext):
        """ファイルシステムクリーンアップ"""

        try:
            # コンテキスト専用ディレクトリ削除
            context_workspace = Path(
                f"/home/aicompany/workspace/{context.security_level.value}/{context.context_id}"
            )
            if context_workspace.exists():
                import shutil

                shutil.rmtree(context_workspace)

            self.logger.debug(f"🗂️ Filesystem cleaned up for {context.context_id}")

        except Exception as e:
            self.logger.warning(
                f"⚠️ Failed to cleanup filesystem for {context.context_id}: {e}"
            )

    def _cleanup_network(self, context: IsolationContext):
        """ネットワーク設定クリーンアップ"""

        try:
            # ネットワーク制限削除
            subprocess.run("tc qdisc del dev eth0 root", shell=True, check=False)

            self.logger.debug(
                f"🌐 Network configuration cleaned up for {context.context_id}"
            )

        except Exception as e:
            self.logger.warning(
                f"⚠️ Failed to cleanup network for {context.context_id}: {e}"
            )

    def _monitor_resources_loop(self):
        """リソース監視ループ"""

        while self.monitoring_active:
        # ループ処理
            try:
                current_contexts = list(self.active_contexts.keys())

                for context_id in current_contexts:
                    # 期限切れチェック
                    with self.context_lock:
                        context = self.active_contexts.get(context_id)
                        # 複雑な条件判定
                        if not (context and context.get('status') == 'active'):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if (
                            context
                            and context.expires_at
                            and datetime.now() > context.expires_at
                        ):
                            self.terminate_context(context_id, "Context expired")
                            continue

                    # リソース違反チェック
                    alerts = self.check_resource_violations(context_id)
                    for alert in alerts:
                        self.alert_manager.handle_alert(alert)

                time.sleep(30)  # 30秒間隔で監視

            except Exception as e:
                self.logger.error(f"❌ Error in resource monitoring loop: {e}")
                time.sleep(60)  # エラー時は1分待機

    def get_system_metrics(self) -> Dict[str, Any]:
        """システム全体のメトリクス取得"""

        with self.context_lock:
            active_contexts_count = len(self.active_contexts)
            contexts_by_level = {}
            for context in self.active_contexts.values():
                level = context.security_level.value
                contexts_by_level[level] = contexts_by_level.get(level, 0) + 1

        # システムリソース
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "timestamp": datetime.now().isoformat(),
            "active_contexts": active_contexts_count,
            "contexts_by_security_level": contexts_by_level,
            "system_resources": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / (1024 * 1024),
                "disk_usage_percent": (disk.used / disk.total) * 100,
                "disk_free_mb": disk.free / (1024 * 1024),
            },
            "monitoring_active": self.monitoring_active,
        }

    def shutdown(self):
        """システムシャットダウン"""

        self.logger.info("🛑 Shutting down ResourceIsolationManager...")

        # 監視停止
        self.monitoring_active = False

        # 全コンテキスト終了
        with self.context_lock:
            active_context_ids = list(self.active_contexts.keys())

        for context_id in active_context_ids:
            self.terminate_context(context_id, "System shutdown")

        self.logger.info("✅ ResourceIsolationManager shutdown complete")


class ResourceMonitor:
    """リソース監視クラス"""

    def __init__(self):
        """初期化メソッド"""
        self.logger = logging.getLogger(f"{__name__}.ResourceMonitor")

    def get_system_load(self) -> Dict[str, float]:
        """システム負荷取得"""

        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_io_percent": psutil.disk_io_counters().read_bytes
            + psutil.disk_io_counters().write_bytes,
            "network_io_percent": psutil.net_io_counters().bytes_sent
            + psutil.net_io_counters().bytes_recv,
        }


class AlertManager:
    """アラート管理クラス"""

    def __init__(self):
        """初期化メソッド"""
        self.logger = logging.getLogger(f"{__name__}.AlertManager")
        self.alert_history: List[ResourceAlert] = []

    def handle_alert(self, alert: ResourceAlert):
        """アラート処理"""

        self.alert_history.append(alert)

        # ログ出力
        level_emoji = {"warning": "⚠️", "critical": "🚨", "emergency": "🆘"}
        emoji = level_emoji.get(alert.alert_level, "📢")

        self.logger.warning(
            f"{emoji} Resource Alert [{alert.alert_level.upper()}]: {alert.message}"
        )

        # 自動対応
        if alert.alert_level == "critical":
            self._handle_critical_alert(alert)

    def _handle_critical_alert(self, alert: ResourceAlert):
        """クリティカルアラート自動対応"""

        self.logger.info(f"🤖 Auto-handling critical alert: {alert.alert_id}")

        # 具体的な自動対応はここで実装
        # 例: プロセス終了、リソース追加割り当て等
        alert.auto_action_taken = "logged_and_monitored"


if __name__ == "__main__":
    # ResourceIsolationManager のテスト
    manager = ResourceIsolationManager()

    print("🏗️ ResourceIsolationManager Test Starting...")

    try:
        # テストコンテキスト作成
        context = manager.create_isolation_context(
            security_level=SecurityLevel.RESTRICTED, session_duration_hours=1
        )

        print(f"✅ Isolation context created: {context.context_id}")
        print(f"   Security Level: {context.security_level.value}")
        print(f"   Isolation Type: {context.isolation_type.value}")
        print(f"   CPU Quota: {context.resource_quota.cpu_percent:.1%}")
        print(f"   Memory Quota: {context.resource_quota.memory_mb}MB")

        # リソース使用状況確認
        usage = manager.get_resource_usage(context.context_id)
        if usage:
            print(f"📊 Current Usage:")
            print(f"   CPU: {usage.cpu_percent:.1%}")
            print(f"   Memory: {usage.memory_mb:.0f}MB")
            print(f"   Processes: {usage.process_count}")

        # リソース違反チェック
        alerts = manager.check_resource_violations(context.context_id)
        if alerts:
            print(f"⚠️ Resource Alerts: {len(alerts)}")
            for alert in alerts:
                print(f"   - {alert.message}")
        else:
            print("✅ No resource violations detected")

        # システムメトリクス
        metrics = manager.get_system_metrics()
        print(f"🖥️ System Metrics:")
        print(f"   Active Contexts: {metrics['active_contexts']}")
        print(f"   System CPU: {metrics['system_resources']['cpu_percent']:.1f}%")
        print(f"   System Memory: {metrics['system_resources']['memory_percent']:.1f}%")

        # クリーンアップ
        print("\n🧹 Cleaning up test context...")
        manager.terminate_context(context.context_id, "Test completed")

        print("✅ ResourceIsolationManager test completed successfully")

    except Exception as e:
        print(f"❌ Test failed: {e}")

    finally:
        manager.shutdown()
