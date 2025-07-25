#!/usr/bin/env python3
"""
Docker Redundancy System - Docker冗長化システム
四賢者推奨Phase 3最優先タスク

Docker Compose冗長化・高可用性システム
リアルタイム監視・自動フェイルオーバー・スケーリング
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
import json
import logging
import os
import subprocess

import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import psutil
import yaml

# 既存システム統合
try:
    from libs.worker_auto_recovery_system import WorkerHealthMonitor
    from libs.worker_monitoring_dashboard import (
        MetricsCollector,
        WorkerMonitoringDashboard,
    )

    EXISTING_SYSTEMS_AVAILABLE = True
except ImportError:
    EXISTING_SYSTEMS_AVAILABLE = False
    logging.warning("Existing systems not available")

logger = logging.getLogger(__name__)

@dataclass
class RedundancyConfig:
    """冗長化設定"""

    # Docker Compose設定
    compose_file_path: str = "docker-compose.redundancy.yml"
    network_name: str = "ai-company-network"

    # サービス設定
    default_restart_policy: str = "always"
    health_check_interval: int = 30
    health_check_timeout: int = 10
    health_check_retries: int = 3

    # フェイルオーバー設定
    failover_threshold: int = 3  # 連続失敗回数
    failover_timeout: int = 30  # フェイルオーバータイムアウト（秒）
    auto_recovery_enabled: bool = True

    # スケーリング設定
    min_replicas: Dict[str, int] = None
    max_replicas: Dict[str, int] = None
    scale_up_threshold: float = 80.0  # CPU使用率%
    scale_down_threshold: float = 20.0

    # 監視設定
    monitoring_interval: int = 10  # 監視間隔（秒）
    metrics_retention_hours: int = 24
    alert_enabled: bool = True

    def __post_init__(self):
        """__post_init__特殊メソッド"""
        if self.min_replicas is None:
            self.min_replicas = {
                "pm-worker": 1,
                "task-worker": 2,
                "monitoring-dashboard": 1,
            }
        if self.max_replicas is None:
            self.max_replicas = {
                "pm-worker": 4,
                "task-worker": 8,
                "monitoring-dashboard": 2,
            }

@dataclass
class ServiceStatus:
    """サービス状態"""

    name: str
    container_id: str
    status: str  # running, exited, restarting, etc.
    health: str  # healthy, unhealthy, starting
    created_at: datetime
    started_at: Optional[datetime]
    cpu_percent: float
    memory_mb: float
    restart_count: int
    last_restart: Optional[datetime]
    replicas_running: int
    replicas_target: int
    ports: List[Dict[str, Any]]
    networks: List[str]
    volumes: List[str]

@dataclass
class FailoverEvent:
    """フェイルオーバーイベント"""

    id: str
    service_name: str
    trigger_type: str  # health_failure, container_exit, resource_exhaustion
    failure_details: Dict[str, Any]
    failover_strategy: str  # restart, scale_up, switch_backup
    started_at: datetime
    completed_at: Optional[datetime]
    success: bool
    recovery_actions: List[Dict[str, Any]]
    impact_assessment: Dict[str, Any]

class DockerComposeManager:
    """Docker Compose管理クラス"""

    def __init__(self, config: RedundancyConfig):
        """初期化メソッド"""
        self.config = config
        self.compose_path = PROJECT_ROOT / self.config.compose_file_path

    def generate_compose_config(
        self, services_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Docker Compose設定を生成"""
        compose_config = {
            "version": "3.8",
            "services": {},
            "networks": {
                self.config.network_name: {
                    "driver": "bridge",
                    "driver_opts": {"com.docker.network.enable_ipv6": "false"},
                }
            },
            "volumes": {},
        }

        # サービス設定の生成
        for service_name, service_config in services_config.items():
            # プライマリサービス
            primary_service = self._generate_service_definition(
                service_name, service_config, "primary"
            )
            compose_config["services"][f"{service_name}-primary"] = primary_service

            # レプリカ数が2以上の場合はバックアップサービスも生成
            if service_config.get("replicas", 1) >= 2:
                backup_service = self._generate_service_definition(
                    service_name, service_config, "backup"
                )
                compose_config["services"][f"{service_name}-backup"] = backup_service

            # 3つ以上のレプリカの場合はクラスター設定
            if service_config.get("replicas", 1) >= 3:
                cluster_service = self._generate_cluster_service_definition(
                    service_name, service_config
                )
                compose_config["services"][service_name] = cluster_service

        # ボリューム設定の追加
        self._add_volume_definitions(compose_config, services_config)

        return compose_config

    def _generate_service_definition(
        self, service_name: str, config: Dict[str, Any], role: str
    ) -> Dict[str, Any]:
        """個別サービス定義を生成"""
        service_def = {
            "image": config.get("image", f"ai-company/{service_name}:latest"),
            "container_name": f"{service_name}-{role}",
            "restart": config.get("restart_policy", self.config.default_restart_policy),
            "networks": [self.config.network_name],
            "environment": config.get("environment", {}),
            "volumes": config.get("volumes", []),
            "depends_on": config.get("dependencies", []),
        }

        # ポート設定（プライマリのみ公開）
        if role == "primary" and "ports" in config:
            service_def["ports"] = config["ports"]

        # ヘルスチェック設定
        if config.get("health_check", True):
            service_def["healthcheck"] = {
                "test": config.get(
                    "health_check_command",
                    "curl -f http://localhost:8080/health || exit 1",
                ),
                "interval": f"{self.config.health_check_interval}s",
                "timeout": f"{self.config.health_check_timeout}s",
                "retries": self.config.health_check_retries,
                "start_period": "40s",
            }

        # 環境固有の設定
        service_def["environment"].update(
            {
                "SERVICE_ROLE": role,
                "SERVICE_NAME": service_name,
                "REDUNDANCY_ENABLED": "true",
            }
        )

        return service_def

    def _generate_cluster_service_definition(
        self, service_name: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """クラスターサービス定義を生成"""
        replicas = config.get("replicas", 3)

        cluster_def = {
            "image": config.get("image", f"ai-company/{service_name}:latest"),
            "deploy": {
                "replicas": replicas,
                "restart_policy": {
                    "condition": "on-failure",
                    "delay": "5s",

                    "window": "120s",
                },
                "update_config": {
                    "parallelism": 1,
                    "delay": "10s",
                    "failure_action": "rollback",
                    "monitor": "60s",
                },
                "rollback_config": {
                    "parallelism": 1,
                    "delay": "0s",
                    "failure_action": "pause",
                    "monitor": "60s",
                },
            },
            "networks": [self.config.network_name],
            "environment": config.get("environment", {}),
            "volumes": config.get("volumes", []),
        }

        # クラスター用ヘルスチェック
        if config.get("health_check", True):
            cluster_def["healthcheck"] = {
                "test": config.get(
                    "health_check_command",
                    "curl -f http://localhost:8080/health || exit 1",
                ),
                "interval": f"{self.config.health_check_interval}s",
                "timeout": f"{self.config.health_check_timeout}s",
                "retries": self.config.health_check_retries,
                "start_period": "40s",
            }

        return cluster_def

    def _add_volume_definitions(
        self, compose_config: Dict[str, Any], services_config: Dict[str, Any]
    ):
        """ボリューム定義を追加"""
        # 共通ボリューム
        compose_config["volumes"].update(
            {
                "ai_company_data": {
                    "driver": "local",
                    "driver_opts": {
                        "type": "none",
                        "o": "bind",
                        "device": str(PROJECT_ROOT / "data"),
                    },
                },
                "ai_company_logs": {
                    "driver": "local",
                    "driver_opts": {
                        "type": "none",
                        "o": "bind",
                        "device": str(PROJECT_ROOT / "logs"),
                    },
                },
                "ai_company_config": {
                    "driver": "local",
                    "driver_opts": {
                        "type": "none",
                        "o": "bind",
                        "device": str(PROJECT_ROOT / "config"),
                    },
                },
            }
        )

    def generate_compose_yaml(self, services_config: Dict[str, Any]) -> str:
        """Docker Compose YAMLファイルを生成"""
        compose_config = self.generate_compose_config(services_config)
        return yaml.dump(compose_config, default_flow_style=False, sort_keys=False)

    def save_compose_file(self, services_config: Dict[str, Any]) -> str:
        """Docker Compose ファイルを保存"""
        compose_yaml = self.generate_compose_yaml(services_config)

        with open(self.compose_path, "w") as f:
            f.write(compose_yaml)

        logger.info(f"Docker Compose file saved to {self.compose_path}")
        return str(self.compose_path)

    def deploy_services(self) -> Dict[str, Any]:
        """サービスをデプロイ"""
        try:
            # Docker Compose up コマンド実行
            cmd = [
                "docker-compose",
                "-f",
                str(self.compose_path),
                "up",
                "-d",
                "--remove-orphans",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                # デプロイされたサービスリストを取得
                deployed_services = self._get_deployed_services()

                return {
                    "success": True,
                    "deployed_services": deployed_services,
                    "output": result.stdout,
                    "deployment_time": datetime.now().isoformat(),
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "returncode": result.returncode,
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Deployment timeout (5 minutes)",
                "returncode": -1,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "returncode": -1}

    def _get_deployed_services(self) -> List[str]:
        """デプロイされたサービスのリストを取得"""
        try:
            cmd = ["docker-compose", "-f", str(self.compose_path), "ps", "--services"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return [
                    line.strip() for line in result.stdout.split("\n") if line.strip()
                ]
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to get deployed services: {e}")
            return []

    def rolling_update(self, update_config: Dict[str, Any]) -> Dict[str, Any]:
        """ローリングアップデート実行"""
        service = update_config["service"]
        strategy = update_config.get("strategy", "rolling")

        try:
            if strategy == "rolling":
                return self._execute_rolling_update(update_config)
            elif strategy == "blue_green":
                return self._execute_blue_green_update(update_config)
            else:
                return {
                    "success": False,
                    "error": f"Unknown update strategy: {strategy}",
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_rolling_update(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """ローリングアップデート実行"""
        service = config["service"]
        new_image = config.get("new_image")
        max_unavailable = config.get("max_unavailable", 1)
        update_delay = config.get("update_delay", 30)

        updated_replicas = []

        # プライマリサービス更新
        primary_result = self._update_single_service(f"{service}-primary", new_image)
        if primary_result["success"]:
            updated_replicas.append(f"{service}-primary")
            time.sleep(update_delay)

        # バックアップサービス更新
        backup_result = self._update_single_service(f"{service}-backup", new_image)
        if backup_result["success"]:
            updated_replicas.append(f"{service}-backup")

        return {
            "success": len(updated_replicas) > 0,
            "strategy": "rolling",
            "updated_replicas": updated_replicas,
            "update_time": datetime.now().isoformat(),
        }

    def _update_single_service(
        self, service_name: str, new_image: Optional[str]
    ) -> Dict[str, Any]:
        """単一サービスの更新"""
        try:
            cmd = [
                "docker-compose",
                "-f",
                str(self.compose_path),
                "up",
                "-d",
                service_name,
            ]
            if new_image:
                # 新しいイメージを指定してプル
                pull_cmd = ["docker", "pull", new_image]
                subprocess.run(pull_cmd, check=True)

            result = subprocess.run(cmd, capture_output=True, text=True)
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def rollback_service(self, rollback_config: Dict[str, Any]) -> Dict[str, Any]:
        """サービスロールバック"""
        service = rollback_config["service"]
        target_version = rollback_config["target_version"]
        immediate = rollback_config.get("immediate", False)

        try:
            # ロールバック対象の特定
            services_to_rollback = [f"{service}-primary", f"{service}-backup"]

            rollback_results = []
            for service_name in services_to_rollback:
                # 古いバージョンのイメージを指定
                old_image = f"ai-company/{service}:{target_version}"
                result = self._update_single_service(service_name, old_image)
                rollback_results.append(
                    {
                        "service": service_name,
                        "success": result["success"],
                        "error": result.get("error"),
                    }
                )

                if not immediate:
                    time.sleep(10)  # 段階的ロールバック

            success_count = sum(1 for r in rollback_results if r["success"])

            return {
                "success": success_count > 0,
                "rolled_back_to": target_version,
                "rollback_reason": rollback_config.get("reason", "Manual rollback"),
                "rollback_results": rollback_results,
                "rollback_time": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

class ServiceHealthMonitor:
    """サービスヘルス監視クラス"""

    def __init__(self, config: RedundancyConfig):
        """初期化メソッド"""
        self.config = config
        self.docker_client = self._get_docker_client()
        self.service_cache = {}
        self.health_history = defaultdict(deque)

    def _get_docker_client(self):
        """Docker クライアントを取得（モック対応）"""
        try:
            import docker

            return docker.from_env()
        except ImportError:
            logger.warning(
                "Docker Python client not available, using subprocess fallback"
            )
            return None

    def check_all_services(self) -> Dict[str, Any]:
        """全サービスのヘルス状態をチェック"""
        services = []
        healthy_count = 0
        unhealthy_count = 0

        try:
            # Docker Compose のサービス一覧を取得
            service_names = self._get_compose_services()

            for service_name in service_names:
                service_status = self._check_single_service(service_name)
                services.append(service_status)

                if service_status["health_status"] == "healthy":
                    healthy_count += 1
                else:
                    unhealthy_count += 1

                # ヘルス履歴に追加
                self.health_history[service_name].append(
                    {
                        "timestamp": datetime.now(),
                        "status": service_status["health_status"],
                        "container_status": service_status["container_status"],
                    }
                )

                # 履歴は最新100件のみ保持
                if len(self.health_history[service_name]) > 100:
                    self.health_history[service_name].popleft()

        except Exception as e:
            logger.error(f"Failed to check services health: {e}")
            return {"success": False, "error": str(e)}

        return {
            "success": True,
            "services": services,
            "healthy_count": healthy_count,
            "unhealthy_count": unhealthy_count,
            "total_replicas": len(services),
            "check_time": datetime.now().isoformat(),
        }

    def _get_compose_services(self) -> List[str]:
        """Docker Compose サービス一覧を取得"""
        try:
            compose_path = PROJECT_ROOT / self.config.compose_file_path
            cmd = ["docker-compose", "-f", str(compose_path), "ps", "--services"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return [
                    line.strip() for line in result.stdout.split("\n") if line.strip()
                ]
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to get compose services: {e}")
            return []

    def _check_single_service(self, service_name: str) -> Dict[str, Any]:
        """単一サービスのヘルス状態をチェック"""
        try:
            # Docker container inspect を使用してヘルス状態を取得
            cmd = ["docker", "inspect", service_name, "--format", "{{json .}}"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                container_info = json.loads(result.stdout)
                state = container_info["State"]

                # ヘルス状態の判定
                health_status = "unknown"
                if "Health" in state:
                    health_status = state["Health"]["Status"]
                elif state.get("Running", False):
                    health_status = "healthy"
                elif state.get("Status") == "exited":
                    health_status = "unhealthy"

                return {
                    "name": service_name,
                    "container_id": container_info["Id"][:12],
                    "container_status": state.get("Status", "unknown"),
                    "health_status": health_status,
                    "started_at": state.get("StartedAt"),
                    "restart_count": container_info.get("RestartCount", 0),
                    "cpu_percent": 0.0,  # 詳細メトリクスは別途取得
                    "memory_mb": 0.0,
                    "ports": container_info.get("NetworkSettings", {}).get("Ports", {}),
                    "networks": list(
                        container_info.get("NetworkSettings", {})
                        .get("Networks", {})
                        .keys()
                    ),
                }
            else:
                return {
                    "name": service_name,
                    "container_id": "N/A",
                    "container_status": "not_found",
                    "health_status": "unhealthy",
                    "error": result.stderr,
                }

        except Exception as e:
            return {
                "name": service_name,
                "container_id": "N/A",
                "container_status": "error",
                "health_status": "unhealthy",
                "error": str(e),
            }

    def get_service_metrics(self, service_name: str) -> Dict[str, Any]:
        """サービスの詳細メトリクスを取得"""
        try:
            # Docker stats を使用してリソース使用率を取得
            cmd = [
                "docker",
                "stats",
                service_name,
                "--no-stream",
                "--format",
                "table {{.CPUPerc}}\t{{.MemUsage}}",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) >= 2:
                    stats_line = lines[1]  # ヘッダーをスキップ
                    parts = stats_line.split("\t")

                    cpu_percent = float(parts[0].rstrip("%"))
                    memory_usage = parts[1]  # "123.4MiB / 2GiB" 形式

                    # メモリ使用量をMBに変換
                    memory_mb = self._parse_memory_usage(memory_usage)

                    return {
                        "cpu_percent": cpu_percent,
                        "memory_mb": memory_mb,
                        "timestamp": datetime.now().isoformat(),
                    }

            return {
                "cpu_percent": 0.0,
                "memory_mb": 0.0,
                "error": "Could not retrieve metrics",
            }

        except Exception as e:
            return {"cpu_percent": 0.0, "memory_mb": 0.0, "error": str(e)}

    def _parse_memory_usage(self, memory_str: str) -> float:
        """メモリ使用量文字列をMBに変換"""
        try:
            # "123.4MiB / 2GiB" から "123.4MiB" を抽出
            used_part = memory_str.split(" / ")[0]

            if "MiB" in used_part:
                return float(used_part.replace("MiB", ""))
            elif "GiB" in used_part:
                return float(used_part.replace("GiB", "")) * 1024
            elif "KiB" in used_part:
                return float(used_part.replace("KiB", "")) / 1024
            else:
                return 0.0
        except Exception:
            return 0.0

class FailoverManager:
    """フェイルオーバー管理クラス"""

    def __init__(self, config: RedundancyConfig):
        """初期化メソッド"""
        self.config = config
        self.failure_counts = defaultdict(int)
        self.failure_history = defaultdict(deque)
        self.active_failovers = {}

    def should_trigger_failover(self, failure_event: Dict[str, Any]) -> bool:
        """フェイルオーバーをトリガーすべきかを判定"""
        service = failure_event["service"]
        failure_type = failure_event["type"]

        # 連続失敗回数をカウント
        self.failure_counts[service] += 1
        self.failure_history[service].append(
            {
                "timestamp": datetime.now(),
                "type": failure_type,
                "details": failure_event,
            }
        )

        # 履歴は最新50件のみ保持
        if len(self.failure_history[service]) > 50:
            self.failure_history[service].popleft()

        # フェイルオーバー判定
        consecutive_failures = failure_event.get(
            "consecutive_failures", self.failure_counts[service]
        )

        # 閾値チェック
        if consecutive_failures >= self.config.failover_threshold:
            logger.warning(
                f"Service {service} exceeded failure threshold ({consecutive_failures} >= " \
                    "{self.config.failover_threshold})"
            )
            return True

        # 重大な失敗タイプの場合は即座にフェイルオーバー
        critical_failure_types = [
            "container_exit",
            "health_check_timeout",
            "resource_exhaustion",
        ]
        if failure_type in critical_failure_types:
            logger.error(
                f"Critical failure detected for service {service}: {failure_type}"
            )
            return True

        return False

    def execute_failover(self, failure_event: Dict[str, Any]) -> Dict[str, Any]:
        """フェイルオーバーを実行"""
        service = failure_event["service"]
        failover_id = str(uuid.uuid4())

        failover_event = FailoverEvent(
            id=failover_id,
            service_name=service,
            trigger_type=failure_event["type"],
            failure_details=failure_event,
            failover_strategy="",
            started_at=datetime.now(),
            completed_at=None,
            success=False,
            recovery_actions=[],
            impact_assessment={},
        )

        self.active_failovers[failover_id] = failover_event

        try:
            # フェイルオーバー戦略の決定
            strategy = self._determine_failover_strategy(failure_event)
            failover_event.failover_strategy = strategy["action"]

            # フェイルオーバー実行
            if strategy["action"] == "restart_container":
                recovery_result = self._restart_container(service)
            elif strategy["action"] == "scale_up":
                recovery_result = self._scale_up_service(service, strategy)
            elif strategy["action"] == "switch_to_backup":
                recovery_result = self._switch_to_backup(service, strategy)
            else:
                recovery_result = {
                    "success": False,
                    "error": f"Unknown strategy: {strategy['action']}",
                }

            # 結果の記録
            failover_event.completed_at = datetime.now()
            failover_event.success = recovery_result["success"]
            failover_event.recovery_actions = recovery_result.get("actions", [])

            # 影響評価
            failover_time = (
                failover_event.completed_at - failover_event.started_at
            ).total_seconds()
            failover_event.impact_assessment = {
                "failover_time_seconds": failover_time,
                "downtime_estimated": recovery_result.get("downtime_seconds", 0),
                "affected_connections": recovery_result.get("affected_connections", 0),
            }

            if recovery_result["success"]:
                # 失敗カウントをリセット
                self.failure_counts[service] = 0
                logger.info(f"Failover completed successfully for service {service}")

            return {
                "success": recovery_result["success"],
                "failover_id": failover_id,
                "strategy": strategy["action"],
                "backup_service": strategy.get("target_service"),
                "failover_time": failover_time,
                "recovery_actions": failover_event.recovery_actions,
                "error": recovery_result.get("error"),
            }

        except Exception as e:
            failover_event.completed_at = datetime.now()
            failover_event.success = False
            logger.error(f"Failover failed for service {service}: {e}")

            return {"success": False, "failover_id": failover_id, "error": str(e)}

    def _determine_failover_strategy(
        self, failure_event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """フェイルオーバー戦略を決定"""
        service = failure_event["service"]
        failure_type = failure_event["type"]

        # サービス名からベース名を抽出
        base_service = service.replace("-primary", "").replace("-backup", "")

        # 失敗タイプに基づく戦略決定
        if failure_type in ["container_exit", "health_check_failed"]:
            # まずは再起動を試行
            return {
                "action": "restart_container",
                "target_service": service,
                "estimated_downtime": 30,
            }

        elif failure_type == "resource_exhaustion":
            # リソース不足の場合はスケールアップ
            return {
                "action": "scale_up",
                "target_service": base_service,
                "scale_factor": 1,
                "estimated_downtime": 60,
            }

        elif failure_type == "network_partition":
            # ネットワーク分断の場合はバックアップに切り替え
            backup_service = (
                f"{base_service}-backup"
                if not service.endswith("-backup")
                else f"{base_service}-primary"
            )
            return {
                "action": "switch_to_backup",
                "target_service": backup_service,
                "estimated_downtime": 10,
            }

        else:
            # デフォルトは再起動
            return {
                "action": "restart_container",
                "target_service": service,
                "estimated_downtime": 30,
            }

    def _restart_container(self, service: str) -> Dict[str, Any]:
        """コンテナを再起動"""
        try:
            cmd = ["docker", "restart", service]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                return {
                    "success": True,
                    "actions": [
                        {
                            "type": "restart_container",
                            "service": service,
                            "timestamp": datetime.now().isoformat(),
                        }
                    ],
                    "downtime_seconds": 30,
                }
            else:
                return {"success": False, "error": result.stderr, "actions": []}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Restart timeout", "actions": []}
        except Exception as e:
            return {"success": False, "error": str(e), "actions": []}

    def _scale_up_service(
        self, service: str, strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """サービスをスケールアップ"""
        try:
            # Docker Compose scale コマンド
            scale_factor = strategy.get("scale_factor", 1)
            compose_path = PROJECT_ROOT / self.config.compose_file_path

            cmd = [
                "docker-compose",
                "-f",
                str(compose_path),
                "up",
                "-d",
                "--scale",
                f"{service}={scale_factor}",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                return {
                    "success": True,
                    "actions": [
                        {
                            "type": "scale_up",
                            "service": service,
                            "scale_factor": scale_factor,
                            "timestamp": datetime.now().isoformat(),
                        }
                    ],
                    "downtime_seconds": 0,
                }
            else:
                return {"success": False, "error": result.stderr, "actions": []}

        except Exception as e:
            return {"success": False, "error": str(e), "actions": []}

    def _switch_to_backup(
        self, service: str, strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """バックアップサービスに切り替え"""
        try:
            target_service = strategy["target_service"]

            # 失敗したサービスを停止
            stop_cmd = ["docker", "stop", service]
            stop_result = subprocess.run(stop_cmd, capture_output=True, text=True)

            # バックアップサービスを開始（既に動いている場合はスキップ）
            start_cmd = ["docker", "start", target_service]
            start_result = subprocess.run(start_cmd, capture_output=True, text=True)

            actions = []
            if stop_result.returncode == 0:
                actions.append(
                    {
                        "type": "stop_service",
                        "service": service,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            if start_result.returncode == 0:
                actions.append(
                    {
                        "type": "start_backup",
                        "service": target_service,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            return {
                "success": len(actions) > 0,
                "actions": actions,
                "downtime_seconds": 10,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "actions": []}

    def execute_automatic_recovery(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """自動復旧を実行"""
        failed_service = scenario["failed_service"]
        backup_service = scenario.get("backup_service")
        recovery_strategy = scenario["recovery_strategy"]

        recovery_actions = []

        try:
            if recovery_strategy == "restart_and_fallback":
                # まず再起動を試行
                restart_result = self._restart_container(failed_service)
                recovery_actions.extend(restart_result.get("actions", []))

                # 再起動失敗の場合はバックアップに切り替え
                if not restart_result["success"] and backup_service:
                    fallback_result = self._switch_to_backup(
                        failed_service, {"target_service": backup_service}
                    )
                    recovery_actions.extend(fallback_result.get("actions", []))
                    success = fallback_result["success"]
                else:
                    success = restart_result["success"]

            elif recovery_strategy == "scale_up_existing":
                # 既存サービスをスケールアップ
                scale_result = self._scale_up_service(
                    failed_service, {"scale_factor": 2}
                )
                recovery_actions.extend(scale_result.get("actions", []))
                success = scale_result["success"]

            else:
                return {
                    "success": False,
                    "error": f"Unknown recovery strategy: {recovery_strategy}",
                    "recovery_actions": [],
                }

            return {
                "success": success,
                "recovery_actions": recovery_actions,
                "recovery_time": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "recovery_actions": recovery_actions,
            }

    def detect_cascading_failure(
        self, failure_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """カスケード障害を検知"""
        if len(failure_events) < 2:
            return {"is_cascading": False}

        # 時間窓内での失敗を分析
        time_window = timedelta(minutes=5)
        recent_failures = []

        for event in failure_events:
            event_time = datetime.fromisoformat(event["timestamp"])
            if datetime.now() - event_time <= time_window:
                recent_failures.append(event)

        # カスケード障害の判定
        if len(recent_failures) >= 3:
            affected_services = len(set(event["service"] for event in recent_failures))
            time_span = max(
                datetime.fromisoformat(e["timestamp"]) for e in recent_failures
            ) - min(datetime.fromisoformat(e["timestamp"]) for e in recent_failures)

            return {
                "is_cascading": True,
                "affected_services": affected_services,
                "failure_count": len(recent_failures),
                "time_window": time_span.total_seconds(),
            }

        return {"is_cascading": False}

    def generate_emergency_response_plan(
        self, cascade_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """緊急時対応計画を生成"""
        emergency_actions = []

        # システム分離
        emergency_actions.append(
            {
                "type": "system_isolation",
                "priority": "immediate",
                "description": "Isolate failed services to prevent further cascade",
                "estimated_time": 60,
            }
        )

        # 管理者アラート
        emergency_actions.append(
            {
                "type": "alert_administrators",
                "priority": "immediate",
                "description": "Send critical alert to system administrators",
                "estimated_time": 5,
            }
        )

        # 健全なサービスのスケールアップ
        emergency_actions.append(
            {
                "type": "emergency_scale_up",
                "priority": "high",
                "description": "Scale up healthy services to handle increased load",
                "estimated_time": 120,
            }
        )

        # データ保護
        emergency_actions.append(
            {
                "type": "data_protection",
                "priority": "high",
                "description": "Enable emergency data backup and protection",
                "estimated_time": 300,
            }
        )

        return {
            "priority": "critical",
            "estimated_total_time": sum(
                action["estimated_time"] for action in emergency_actions
            ),
            "emergency_actions": emergency_actions,
            "cascade_severity": cascade_info.get("affected_services", 0),
            "plan_generated_at": datetime.now().isoformat(),
        }

class DockerRedundancySystem:
    """Docker冗長化システム統合クラス"""

    def __init__(self, config: Optional[RedundancyConfig] = None):
        """初期化メソッド"""
        self.config = config or RedundancyConfig()
        self.compose_manager = DockerComposeManager(self.config)
        self.health_monitor = ServiceHealthMonitor(self.config)
        self.failover_manager = FailoverManager(self.config)

        # 監視ループ制御
        self.monitoring_active = False
        self.monitoring_thread = None

        # 既存システム統合
        self.dashboard_integration = None
        if EXISTING_SYSTEMS_AVAILABLE:
            try:
                from libs.worker_monitoring_dashboard import WorkerMonitoringDashboard

                logger.info("Existing monitoring dashboard available for integration")
            except ImportError:
                pass

    def initialize_redundancy(self, services_config: Dict[str, Any]) -> Dict[str, Any]:
        """冗長化システムを初期化"""
        try:
            logger.info("Initializing Docker redundancy system...")

            # Docker Compose ファイル生成
            compose_file = self.compose_manager.save_compose_file(services_config)
            logger.info(f"Generated Docker Compose file: {compose_file}")

            # サービスデプロイ
            deploy_result = self.compose_manager.deploy_services()
            if not deploy_result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to deploy services: {deploy_result['error']}",
                }

            # 監視開始
            self.start_monitoring()

            return {
                "success": True,
                "compose_file": compose_file,
                "deployed_services": deploy_result["deployed_services"],
                "monitoring_active": self.monitoring_active,
                "initialization_time": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to initialize redundancy system: {e}")
            return {"success": False, "error": str(e)}

    def start_monitoring(self):
        """監視を開始"""
        if self.monitoring_active:
            logger.warning("Monitoring is already active")
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self.monitoring_thread.start()
        logger.info("Started redundancy monitoring")

    def stop_monitoring(self):
        """監視を停止"""
        self.monitoring_active = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=10)
        logger.info("Stopped redundancy monitoring")

    def _monitoring_loop(self):
        """監視ループ"""
        while self.monitoring_active:
            try:
                # ヘルス状態チェック
                health_status = self.health_monitor.check_all_services()

                if health_status["success"]:
                    # 異常なサービスのチェック
                    for service in health_status["services"]:
                        if service["health_status"] != "healthy":
                            # フェイルオーバー判定
                            failure_event = {
                                "service": service["name"],
                                "type": "health_check_failed",
                                "container_status": service["container_status"],
                                "health_status": service["health_status"],
                                "timestamp": datetime.now().isoformat(),
                                "consecutive_failures": 1,
                            }

                            if self.failover_manager.should_trigger_failover(
                                failure_event
                            ):
                                logger.warning(
                                    f"Triggering failover for service {service['name']}"
                                )
                                failover_result = (
                                    self.failover_manager.execute_failover(
                                        failure_event
                                    )
                                )

                                if failover_result["success"]:
                                    logger.info(
                                        f"Failover completed for {service['name']}"
                                    )
                                else:
                                    logger.error(
                                        f"Failover failed for {service['name']}: {failover_result.get('error')}"
                                    )

                # 監視間隔待機
                time.sleep(self.config.monitoring_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.config.monitoring_interval)

    def get_system_status(self) -> Dict[str, Any]:
        """システム全体の状態を取得"""
        try:
            # ヘルス状態取得
            health_status = self.health_monitor.check_all_services()

            # アクティブなフェイルオーバー情報
            active_failovers = {
                fid: {
                    "service": fo.service_name,
                    "strategy": fo.failover_strategy,
                    "started_at": fo.started_at.isoformat(),
                    "success": fo.success,
                }
                for fid, fo in self.failover_manager.active_failovers.items()
                if fo.completed_at is None
                or (datetime.now() - fo.completed_at).seconds < 300
            }

            # システム可用性計算
            if health_status["success"] and health_status["services"]:
                availability = (
                    health_status["healthy_count"] / len(health_status["services"])
                ) * 100
            else:
                availability = 0.0

            return {
                "success": True,
                "monitoring_active": self.monitoring_active,
                "health_status": health_status,
                "active_failovers": active_failovers,
                "system_availability": availability,
                "config": asdict(self.config),
                "status_time": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def integrate_with_dashboard(self, dashboard) -> Dict[str, Any]:
        """監視ダッシュボードとの統合"""
        try:
            self.dashboard_integration = dashboard
            logger.info("Integrated with monitoring dashboard")

            return {"success": True, "integration_time": datetime.now().isoformat()}
        except Exception as e:
            logger.error(f"Failed to integrate with dashboard: {e}")
            return {"success": False, "error": str(e)}

# デフォルト設定でのサービス設定例
DEFAULT_SERVICES_CONFIG = {
    "pm-worker": {
        "image": "ai-company/pm-worker:latest",
        "replicas": 2,
        "environment": {
            "RABBITMQ_HOST": "rabbitmq",
            "LOG_LEVEL": "INFO",
            "WORKER_TYPE": "pm",
        },
        "dependencies": ["monitoring-dashboard"],
        "restart_policy": "always",
        "health_check": True,
        "health_check_command": "python3 -c \"import workers.async_pm_worker_simple; print('OK')\" || exit 1",
    },
    "task-worker": {
        "image": "ai-company/task-worker:latest",
        "replicas": 3,
        "environment": {
            "RABBITMQ_HOST": "rabbitmq",
            "LOG_LEVEL": "INFO",
            "WORKER_TYPE": "task",
        },
        "dependencies": ["monitoring-dashboard"],
        "restart_policy": "always",
        "health_check": True,
        "health_check_command": "python3 -c \"import workers.simple_task_worker; print('OK')\" || exit 1",
    },
    "monitoring-dashboard": {
        "image": "ai-company/monitoring:latest",
        "replicas": 1,
        "environment": {"LOG_LEVEL": "INFO", "WEB_PORT": "8000"},
        "ports": ["8000:8000"],
        "volumes": ["./data:/app/data", "./logs:/app/logs"],
        "restart_policy": "always",
        "health_check": True,
        "health_check_command": "curl -f http://localhost:8000/health || exit 1",
    },
}

if __name__ == "__main__":
    # テスト実行用のエントリーポイント
    logging.basicConfig(level=logging.INFO)

    # 冗長化システムの初期化
    redundancy_system = DockerRedundancySystem()

    # デフォルト設定でシステム初期化
    result = redundancy_system.initialize_redundancy(DEFAULT_SERVICES_CONFIG)

    if result["success"]:
        print("✅ Docker Redundancy System initialized successfully")
        print(f"📁 Compose file: {result['compose_file']}")
        print(f"🚀 Deployed services: {result['deployed_services']}")
        print(f"📊 Monitoring active: {result['monitoring_active']}")
    else:
        print(f"❌ Failed to initialize: {result['error']}")
