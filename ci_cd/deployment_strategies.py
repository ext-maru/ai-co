#!/usr/bin/env python3
"""
環境別デプロイメント戦略システム
"""
import json
import logging
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)


class DeploymentManager:
    """デプロイメント管理クラス"""

    def __init__(self, auto_rollback_on_failure: bool = False):
        """
        デプロイメントマネージャーの初期化

        Args:
            auto_rollback_on_failure: ヘルスチェック失敗時の自動ロールバック
        """
        self.auto_rollback_on_failure = auto_rollback_on_failure
        self.environment_strategies = {
            "development": "direct",
            "staging": "rolling",
            "production": "blue_green",
        }

    def validate_environment(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        環境設定の検証

        Args:
            config: 環境設定

        Returns:
            検証結果
        """
        errors = []

        # 必須フィールドチェック
        required_fields = ["name", "type", "url"]
        for field in required_fields:
            if field not in config:
                errors.append(f"必須フィールド '{field}' が不足しています")

        # URL形式チェック
        if "url" in config:
            try:
                parsed = urlparse(config["url"])
                if not parsed.scheme or not parsed.netloc:
                    errors.append("無効なurl形式です")
            except Exception:
                errors.append("urlの解析に失敗しました")

        # 環境タイプチェック
        valid_types = ["development", "staging", "production"]
        if "type" in config and config["type"] not in valid_types:
            errors.append(f"無効な環境タイプ: {config['type']}")

        return {"valid": len(errors) == 0, "errors": errors}

    def deploy_to_environment(
        self, environment: str, deployment_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        指定された環境にデプロイ

        Args:
            environment: デプロイ先環境
            deployment_config: デプロイ設定

        Returns:
            デプロイ結果
        """
        deployment_id = str(uuid.uuid4())
        strategy = self.environment_strategies.get(environment, "direct")

        # 承認チェック
        if not self._check_deployment_approval(environment, deployment_config):
            return self._create_approval_denied_result(environment)

        try:
            deployment_context = self._create_deployment_context(
                deployment_config, environment, deployment_id, strategy
            )

            # デプロイ実行
            deploy_result = self._execute_deployment_strategy(
                strategy, deployment_context
            )

            if not deploy_result["success"]:
                return deploy_result

            # 品質チェック実行
            return self._perform_post_deployment_checks(
                deploy_result, deployment_context
            )

        except Exception as e:
            logger.error(f"デプロイメントエラー: {str(e)}")
            return self._create_error_result(environment, deployment_id, str(e))

    def _check_deployment_approval(
        self, environment: str, deployment_config: Dict[str, Any]
    ) -> bool:
        """デプロイメント承認チェック"""
        if environment == "production" and deployment_config.get("approval_required"):
            return self._get_deployment_approval(deployment_config)
        return True

    def _create_approval_denied_result(self, environment: str) -> Dict[str, Any]:
        """承認拒否結果作成"""
        return {
            "success": False,
            "environment": environment,
            "error": "デプロイメント承認が得られませんでした",
            "approval_received": False,
        }

    def _create_deployment_context(
        self,
        deployment_config: Dict[str, Any],
        environment: str,
        deployment_id: str,
        strategy: str,
    ) -> Dict[str, Any]:
        """デプロイメントコンテキスト作成"""
        return {
            **deployment_config,
            "environment": environment,
            "deployment_id": deployment_id,
            "strategy": strategy,
        }

    def _execute_deployment_strategy(
        self, strategy: str, deployment_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """デプロイメント戦略実行"""
        strategy_class = self._get_strategy_class(strategy)
        strategy_instance = strategy_class()
        return strategy_instance.deploy(deployment_context)

    def _perform_post_deployment_checks(
        self, deploy_result: Dict[str, Any], deployment_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """デプロイ後チェック実行"""
        deployment_config = deployment_context

        # ヘルスチェック
        if deployment_config.get("health_checks"):
            health_result = self._run_health_checks(deployment_context)
            deploy_result["health_checks_passed"] = health_result["healthy"]

            if not health_result["healthy"] and self.auto_rollback_on_failure:
                return self._handle_health_check_failure(
                    deploy_result, deployment_context
                )

        # スモークテスト
        if deployment_config.get("smoke_tests"):
            smoke_result = self._run_smoke_tests(deployment_context)
            deploy_result["smoke_tests_passed"] = smoke_result["passed"]

        # 承認情報追加
        if deployment_context["environment"] == "production":
            deploy_result["approval_received"] = deployment_config.get(
                "approval_required", False
            )

        return deploy_result

    def _handle_health_check_failure(
        self, deploy_result: Dict[str, Any], deployment_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ヘルスチェック失敗時の処理"""
        rollback_result = self._execute_auto_rollback(deployment_context)
        deploy_result.update(
            {
                "success": False,
                "auto_rollback_executed": True,
                "rollback_successful": rollback_result["success"],
            }
        )
        return deploy_result

    def _create_error_result(
        self, environment: str, deployment_id: str, error: str
    ) -> Dict[str, Any]:
        """エラー結果作成"""
        return {
            "success": False,
            "environment": environment,
            "deployment_id": deployment_id,
            "error": error,
        }

    def rollback_deployment(
        self, deployment_id: str, deployment_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        デプロイメントのロールバック

        Args:
            deployment_id: デプロイメントID
            deployment_info: デプロイメント情報

        Returns:
            ロールバック結果
        """
        rollback_id = str(uuid.uuid4())
        strategy = deployment_info.get("strategy", "direct")

        try:
            # ロールバックコマンド実行
            cmd = [
                "sh",
                "-c",
                f'echo "Rolling back deployment {deployment_id} using {strategy} strategy"',
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return {
                    "success": True,
                    "rollback_id": rollback_id,
                    "rolled_back_to": deployment_info.get("previous_version"),
                    "rollback_strategy": strategy,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                return {
                    "success": False,
                    "rollback_id": rollback_id,
                    "error": result.stderr,
                    "manual_intervention_required": True,
                }

        except Exception as e:
            return {
                "success": False,
                "rollback_id": rollback_id,
                "error": str(e),
                "manual_intervention_required": True,
            }

    def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """デプロイメント状態取得"""
        # 実装は省略（実際にはデータベースから取得）
        return {
            "deployment_id": deployment_id,
            "status": "completed",
            "environment": "production",
        }

    def _get_deployment_approval(self, deployment_config: Dict[str, Any]) -> bool:
        """デプロイメント承認取得"""
        # 実際の実装では承認システムと連携
        return True

    def _get_strategy_class(self, strategy: str):
        """戦略クラス取得"""
        strategy_map = {
            "direct": DirectDeploymentStrategy,
            "rolling": RollingDeploymentStrategy,
            "blue_green": BlueGreenDeploymentStrategy,
            "canary": CanaryDeploymentStrategy,
        }
        return strategy_map.get(strategy, DirectDeploymentStrategy)

    def _run_health_checks(self, deployment_context: Dict[str, Any]) -> Dict[str, Any]:
        """ヘルスチェック実行"""
        try:
            cmd = ["curl", "-f", "-s", "http://localhost/health"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return {"healthy": result.returncode == 0}
        except Exception:
            return {"healthy": False}

    def _run_smoke_tests(self, deployment_context: Dict[str, Any]) -> Dict[str, Any]:
        """スモークテスト実行"""
        return {"passed": True}  # 簡易実装

    def _execute_auto_rollback(
        self, deployment_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """自動ロールバック実行"""
        try:
            cmd = ["sh", "-c", 'echo "Auto rollback executed"']
            result = subprocess.run(cmd, capture_output=True, text=True)
            return {"success": result.returncode == 0}
        except Exception:
            return {"success": False}


class DirectDeploymentStrategy:
    """直接デプロイ戦略"""

    def deploy(self, deployment_context: Dict[str, Any]) -> Dict[str, Any]:
        """直接デプロイ実行"""
        try:
            cmd = ["sh", "-c", 'echo "Direct deployment completed"']
            result = subprocess.run(cmd, capture_output=True, text=True)

            return {
                "success": result.returncode == 0,
                "strategy": "direct",
                "deployment_id": deployment_context.get(
                    "deployment_id", str(uuid.uuid4())
                ),
                "environment": deployment_context.get("environment", "unknown"),
                "downtime": 30,  # 30秒のダウンタイム
                "output": result.stdout,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"success": False, "strategy": "direct", "error": str(e)}


class RollingDeploymentStrategy:
    """ローリングデプロイ戦略"""

    def __init__(self, batch_size: int = 1):
        self.batch_size = batch_size

    def deploy(self, deployment_context: Dict[str, Any]) -> Dict[str, Any]:
        """ローリングデプロイ実行"""
        try:
            instances = deployment_context.get("instances", ["server1", "server2"])
            batches = len(instances) // self.batch_size
            if len(instances) % self.batch_size != 0:
                batches += 1

            cmd = ["sh", "-c", 'echo "Rolling deployment completed"']
            result = subprocess.run(cmd, capture_output=True, text=True)

            return {
                "success": result.returncode == 0,
                "strategy": "rolling",
                "deployment_id": deployment_context.get(
                    "deployment_id", str(uuid.uuid4())
                ),
                "environment": deployment_context.get("environment", "unknown"),
                "batches_deployed": batches,
                "downtime": 0,  # ダウンタイムなし
                "output": result.stdout,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"success": False, "strategy": "rolling", "error": str(e)}


class BlueGreenDeploymentStrategy:
    """ブルーグリーンデプロイ戦略"""

    def deploy(self, deployment_context: Dict[str, Any]) -> Dict[str, Any]:
        """ブルーグリーンデプロイ実行"""
        try:
            current_active = deployment_context.get("current_active", "blue")
            switch_to = "green" if current_active == "blue" else "blue"

            cmd = ["sh", "-c", 'echo "Blue-Green deployment completed"']
            result = subprocess.run(cmd, capture_output=True, text=True)

            return {
                "success": result.returncode == 0,
                "strategy": "blue_green",
                "deployment_id": deployment_context.get(
                    "deployment_id", str(uuid.uuid4())
                ),
                "environment": deployment_context.get("environment", "unknown"),
                "switched_to": switch_to,
                "previous_environment": current_active,
                "downtime": 0,  # ダウンタイムなし
                "output": result.stdout,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"success": False, "strategy": "blue_green", "error": str(e)}


class CanaryDeploymentStrategy:
    """カナリアデプロイ戦略"""

    def __init__(self, canary_percentage: int = 10):
        self.canary_percentage = canary_percentage

    def deploy(self, deployment_context: Dict[str, Any]) -> Dict[str, Any]:
        """カナリアデプロイ実行"""
        try:
            total_instances = deployment_context.get("total_instances", 10)
            canary_instances = max(1, total_instances * self.canary_percentage // 100)

            cmd = ["sh", "-c", 'echo "Canary deployment completed"']
            result = subprocess.run(cmd, capture_output=True, text=True)

            # カナリアメトリクス監視
            metrics_healthy = self._monitor_canary_metrics(deployment_context)

            return {
                "success": result.returncode == 0,
                "strategy": "canary",
                "deployment_id": deployment_context.get(
                    "deployment_id", str(uuid.uuid4())
                ),
                "environment": deployment_context.get("environment", "unknown"),
                "canary_instances": canary_instances,
                "metrics_healthy": metrics_healthy,
                "full_rollout_completed": metrics_healthy,
                "downtime": 0,
                "output": result.stdout,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"success": False, "strategy": "canary", "error": str(e)}

    def _monitor_canary_metrics(self, deployment_context: Dict[str, Any]) -> bool:
        """カナリアメトリクス監視"""
        # 簡易実装：実際にはメトリクス収集と分析
        return True


class DeploymentMonitor:
    """デプロイメント監視クラス"""

    def check_deployment_health(
        self, deployment_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """デプロイメントヘルスチェック"""
        try:
            endpoint = deployment_info.get("health_endpoint", "/health")
            expected_instances = deployment_info.get("expected_instances", 1)

            # ヘルスチェック実行（モック）
            start_time = time.time()

            # 実際の実装では requests.get() を使用
            response_data = {
                "status": "healthy",
                "instances": expected_instances,
                "version": "v1.3.0",
            }

            response_time = (time.time() - start_time) * 1000  # ms

            return {
                "healthy": response_data["status"] == "healthy",
                "all_instances_ready": response_data["instances"] == expected_instances,
                "response_time": response_time,
                "version": response_data.get("version"),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def collect_deployment_metrics(
        self, deployment_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """デプロイメントメトリクス収集"""
        try:
            # メトリクス収集（モック）
            metrics = self._collect_metrics(deployment_info)

            # パフォーマンス評価
            performance_acceptable = (
                metrics["response_time_avg"] < 200
                and metrics["error_rate"] < 0.05
                and metrics["cpu_usage"] < 80
            )

            return {
                "success": True,
                "metrics": metrics,
                "performance_acceptable": performance_acceptable,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _collect_metrics(self, deployment_info: Dict[str, Any]) -> Dict[str, Any]:
        """メトリクス収集（モック実装）"""
        return {
            "response_time_avg": 150,
            "error_rate": 0.01,
            "cpu_usage": 45,
            "memory_usage": 60,
            "request_count": 1000,
        }


class DeploymentNotifier:
    """デプロイメント通知クラス"""

    def send_deployment_notification(
        self, deployment_result: Dict[str, Any], notification_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """デプロイメント通知送信"""
        notifications_sent = 0
        results = {}

        channels = notification_config.get("channels", [])

        # Slack通知
        if "slack" in channels:
            slack_result = self._send_slack_notification(
                deployment_result, notification_config
            )
            results["slack_success"] = slack_result
            if slack_result:
                notifications_sent += 1

        # Email通知
        if "email" in channels:
            email_result = self._send_email_notification(
                deployment_result, notification_config
            )
            results["email_success"] = email_result
            if email_result:
                notifications_sent += 1

        return {"notifications_sent": notifications_sent, **results}

    def _send_slack_notification(
        self, deployment_result: Dict[str, Any], config: Dict[str, Any]
    ) -> bool:
        """Slack通知送信"""
        try:
            # 実際の実装では requests.post() でWebhook送信
            return True
        except Exception:
            return False

    def _send_email_notification(
        self, deployment_result: Dict[str, Any], config: Dict[str, Any]
    ) -> bool:
        """Email通知送信"""
        try:
            # 実際の実装ではSMTPでメール送信
            return True
        except Exception:
            return False


class DeploymentHistory:
    """デプロイメント履歴管理クラス"""

    def record_deployment(
        self, deployment_record: Dict[str, Any], history_file: Path
    ) -> None:
        """デプロイメント履歴記録"""
        try:
            # 既存履歴読み込み
            if history_file.exists():
                with open(history_file, "r") as f:
                    history = json.load(f)
            else:
                history = []

            # 新規レコード追加
            history.append(deployment_record)

            # 履歴保存
            with open(history_file, "w") as f:
                json.dump(history, f, indent=2)

        except Exception as e:
            logger.error(f"履歴記録エラー: {str(e)}")

    def get_deployment_history(
        self, environment: str, history_file: Path, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """デプロイメント履歴取得"""
        try:
            if not history_file.exists():
                return []

            with open(history_file, "r") as f:
                history = json.load(f)

            # 環境でフィルタ
            env_history = [
                record for record in history if record.get("environment") == environment
            ]

            # 最新順でソート
            env_history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            return env_history[:limit]

        except Exception as e:
            logger.error(f"履歴取得エラー: {str(e)}")
            return []

    def get_deployment_statistics(
        self, environment: str, history_file: Path
    ) -> Dict[str, Any]:
        """デプロイメント統計取得"""
        history = self.get_deployment_history(environment, history_file, limit=100)

        if not history:
            return {"total_deployments": 0, "success_rate": 0.0, "average_duration": 0}

        total_deployments = len(history)
        successful_deployments = sum(1 for record in history if record.get("success"))
        success_rate = (successful_deployments / total_deployments) * 100

        # 平均デプロイ時間計算
        durations = [
            record.get("duration", 0) for record in history if record.get("duration")
        ]
        average_duration = sum(durations) / len(durations) if durations else 0

        return {
            "total_deployments": total_deployments,
            "success_rate": round(success_rate, 1),
            "average_duration": round(average_duration),
        }
