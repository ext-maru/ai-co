"""
🏛️ エルダーズギルド プロジェクト別デプロイメント設定システム
作成者: クロードエルダー（Claude Elder）
日付: 2025年7月10日

プロジェクトごとにデプロイメント方法を選択・変更できるシステム
4賢者統合による自動最適化機能付き
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from libs.four_sages_integration import FourSagesIntegration

logger = logging.getLogger(__name__)

@dataclass
class DeploymentConfig:
    """プロジェクト別デプロイメント設定"""

    project_name: str
    deployment_method: str
    environments: Dict[str, Dict[str, Any]]
    four_sages_config: Dict[str, Any]
    knights_config: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "project_name": self.project_name,
            "deployment_method": self.deployment_method,
            "environments": self.environments,
            "four_sages_config": self.four_sages_config,
            "knights_config": self.knights_config,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeploymentConfig":
        """辞書から作成"""
        return cls(
            project_name=data.get("project_name", ""),
            deployment_method=data.get("deployment_method", "github_actions"),
            environments=data.get("environments", {}),
            four_sages_config=data.get("four_sages_config", {}),
            knights_config=data.get("knights_config", {}),
            metadata=data.get("metadata", {}),
        )

class ProjectDeploymentManager:
    """プロジェクト別デプロイメント管理システム"""

    def __init__(self, config_dir: str = "deployment-configs"):
        """初期化メソッド"""
        self.config_dir = Path(config_dir)
        self.sages = FourSagesIntegration()
        self.deployment_history = []

        # 設定ディレクトリ作成
        try:
            self._ensure_config_directories()
            self.global_config = self._load_global_config()
        except Exception as e:
            logger.warning(f"設定ディレクトリ初期化エラー: {e}")
            self.global_config = self._create_default_global_config()

    def _ensure_config_directories(self):
        """設定ディレクトリの作成"""
        directories = [
            self.config_dir / "global",

            self.config_dir / "global" / "schemas",
            self.config_dir / "projects",
            self.config_dir / "overrides",
        ]

        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"ディレクトリ作成エラー {directory}: {e}")
                raise

    def _load_global_config(self) -> Dict[str, Any]:
        """グローバル設定読み込み"""
        try:
            global_config_path = self.config_dir / "global" / "default.yml"
            if global_config_path.exists():
                with open(global_config_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            else:
                # デフォルト設定作成
                return self._create_default_global_config()
        except Exception as e:
            logger.error(f"グローバル設定読み込みエラー: {e}")
            return self._create_default_global_config()

    def _create_default_global_config(self) -> Dict[str, Any]:
        """デフォルトグローバル設定作成"""
        default_config = {
            "apiVersion": "v1",
            "kind": "DeploymentConfig",
            "metadata": {
                "name": "global-default",
                "version": "1.0.0",
                "created_by": "elders-guild",
            },
            "default": {
                "deployment_method": "github_actions",
                "four_sages_integration": True,
                "knights_protection": True,
                "environments": {
                    "development": {
                        "auto_deploy": True,
                        "approval_required": False,
                        "rollback_enabled": True,
                    },
                    "staging": {
                        "auto_deploy": True,
                        "approval_required": True,
                        "rollback_enabled": True,
                    },
                    "production": {
                        "auto_deploy": False,
                        "approval_required": True,
                        "rollback_enabled": True,
                    },
                },
                "github_actions": {
                    "trigger_on": ["push", "pull_request"],
                    "runner": "ubuntu-latest",
                    "timeout": 30,
                    "retry_count": 3,
                },
                "ssh": {
                    "connection_timeout": 30,
                    "retry_count": 3,
                    "backup_before_deploy": True,
                    "health_check_wait": 30,
                },
                "four_sages": {
                    "knowledge_sage": {"enabled": True, "history_tracking": True},
                    "task_sage": {"enabled": True, "dependency_check": True},
                    "incident_sage": {"enabled": True, "monitoring": True},
                    "rag_sage": {"enabled": True, "optimization": True},
                },
                "knights": {
                    "security_scan": True,
                    "vulnerability_check": True,
                    "permission_audit": True,
                    "real_time_monitoring": True,
                },
            },
        }

        # ファイル保存
        global_config_path = self.config_dir / "global" / "default.yml"
        with open(global_config_path, "w", encoding="utf-8") as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)

        return default_config

    def get_project_config(
        self, project_name: str, environment: str
    ) -> DeploymentConfig:
        """プロジェクト設定取得（設定継承付き）"""
        try:
            # プロジェクトが存在しない場合はNoneを返す
            if project_name not in self.list_projects():
                logger.warning(f"プロジェクト '{project_name}' が見つかりません")
                return None

            # 設定継承: Global → Project → Environment → Override
            config = self.global_config.get("default", {}).copy()

            # プロジェクト設定
            project_config = self._load_project_config(project_name)
            if project_config:
                self._merge_config(config, project_config)

            # 環境設定
            env_config = self._load_environment_config(project_name, environment)
            if env_config:
                self._merge_config(config, env_config)

            # オーバーライド設定
            override_config = self._load_override_config(project_name, environment)
            if override_config:
                self._merge_config(config, override_config)

            # 4賢者による最適化
            optimized_config = self.sages.optimize_deployment_config(config)

            return DeploymentConfig(
                project_name=project_name,
                deployment_method=optimized_config.get(
                    "deployment_method", "github_actions"
                ),
                environments=optimized_config.get("environments", {}),
                four_sages_config=optimized_config.get("four_sages", {}),
                knights_config=optimized_config.get("knights", {}),
                metadata={
                    "last_updated": datetime.now().isoformat(),
                    "optimized_by": "four_sages",
                    "environment": environment,
                },
            )
        except Exception as e:
            logger.error(f"プロジェクト設定取得エラー: {e}")
            raise

    def _load_project_config(self, project_name: str) -> Dict[str, Any]:
        """プロジェクト設定読み込み"""
        project_config_path = (
            self.config_dir / "projects" / project_name / "project.yml"
        )
        if project_config_path.exists():
            with open(project_config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {}

    def _load_environment_config(
        self, project_name: str, environment: str
    ) -> Dict[str, Any]:
        """環境設定読み込み"""
        env_config_path = (
            self.config_dir / "projects" / project_name / f"{environment}.yml"
        )
        if env_config_path.exists():
            with open(env_config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {}

    def _load_override_config(
        self, project_name: str, environment: str
    ) -> Dict[str, Any]:
        """オーバーライド設定読み込み"""
        override_files = [
            self.config_dir / "overrides" / f"{project_name}-{environment}.yml",
            self.config_dir / "overrides" / f"{project_name}.yml",
            self.config_dir / "overrides" / "global-overrides.yml",
        ]

        override_config = {}
        for override_file in override_files:
            if override_file.exists():
                with open(override_file, "r", encoding="utf-8") as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        self._merge_config(override_config, file_config)

        return override_config

    def _merge_config(
        self, base_config: Dict[str, Any], override_config: Dict[str, Any]
    ):
        """設定マージ（深いマージ）"""
        for key, value in override_config.items():
            if isinstance(value, dict) and key in base_config:
                if isinstance(base_config[key], dict):
                    self._merge_config(base_config[key], value)
                else:
                    base_config[key] = value
            else:
                base_config[key] = value

    def validate_config(
        self, project_name: str, environment: str
    ) -> tuple[bool, List[str]]:
        """設定検証"""
        errors = []

        try:
            config = self.get_project_config(project_name, environment)

            # 必須フィールド確認
            required_fields = ["deployment_method", "environments"]
            for field in required_fields:
                if not hasattr(config, field):
                    errors.append(f"必須フィールド '{field}' が見つかりません")

            # デプロイ方法検証
            valid_methods = ["github_actions", "ssh", "hybrid"]
            if config.deployment_method not in valid_methods:
                errors.append(f"無効なデプロイ方法: {config.deployment_method}")

            # 環境設定検証
            if environment not in config.environments:
                errors.append(f"環境 '{environment}' の設定が見つかりません")

            # 4賢者による検証
            sage_validation = self.sages.validate_deployment_config(config.to_dict())
            if not sage_validation.get("valid", False):
                errors.extend(sage_validation.get("errors", []))

        except Exception as e:
            errors.append(f"設定検証エラー: {e}")

        return len(errors) == 0, errors

    def create_project_config(
        self,
        project_name: str,

        project_type: str = "web-app",
    ) -> bool:
        """プロジェクト設定作成"""
        try:
            # プロジェクトが既に存在する場合はエラー
            if project_name in self.list_projects():
                logger.warning(f"プロジェクト '{project_name}' は既に存在します")
                return False

            # テンプレート読み込み

            # プロジェクトディレクトリ作成
            project_dir = self.config_dir / "projects" / project_name
            project_dir.mkdir(parents=True, exist_ok=True)

            # プロジェクト設定作成
            project_config = {
                "apiVersion": "v1",
                "kind": "ProjectConfig",
                "metadata": {
                    "name": project_name,

                    "version": "1.0.0",
                    "created_at": datetime.now().isoformat(),
                    "created_by": "elders-guild",
                },
                "project": {
                    "name": project_name,
                    "type": project_type,

                },

            }

            # 環境設定作成
            environment_configs = {
                "development": {
                    "environment": "development",
                    "deployment_method": "ssh",
                    "auto_deploy": True,
                    "approval_required": False,
                },
                "staging": {
                    "environment": "staging",
                    "deployment_method": "github_actions",
                    "auto_deploy": True,
                    "approval_required": True,
                },
                "production": {
                    "environment": "production",
                    "deployment_method": "github_actions",
                    "auto_deploy": False,
                    "approval_required": True,
                    "deployment_window": ["02:00-04:00"],
                },
            }

            # ファイル保存
            config_files = {
                "project.yml": project_config,
                **{f"{env}.yml": config for env, config in environment_configs.items()},
            }

            for filename, config_data in config_files.items():
                config_path = project_dir / filename
                with open(config_path, "w", encoding="utf-8") as f:
                    yaml.dump(
                        config_data, f, default_flow_style=False, allow_unicode=True
                    )

            logger.info(f"プロジェクト '{project_name}' の設定を作成しました")
            return True

        except Exception as e:
            logger.error(f"プロジェクト設定作成エラー: {e}")
            return False

        """テンプレート読み込み"""

                return yaml.safe_load(f)
        else:
            # デフォルトテンプレート

        """デフォルトテンプレート作成"""

            "web-app": {
                "technology_stack": ["python", "fastapi", "postgresql", "redis"],
                "settings": {
                    "build_command": "python -m build",
                    "test_command": "pytest tests/",
                    "health_check_endpoint": "/health",
                },
                "four_sages_custom": {
                    "knowledge_sage": {"learning_rate": "high"},
                    "task_sage": {"optimization_level": "aggressive"},
                    "incident_sage": {"alert_threshold": "medium"},
                    "rag_sage": {"analysis_depth": "deep"},
                },
                "resources": {"cpu": "2", "memory": "4Gi", "storage": "20Gi"},
            },
            "microservice": {
                "technology_stack": ["python", "fastapi", "postgresql"],
                "settings": {
                    "build_command": "python -m build",
                    "test_command": "pytest tests/",
                    "health_check_endpoint": "/health",
                },
                "four_sages_custom": {
                    "knowledge_sage": {"learning_rate": "medium"},
                    "task_sage": {"optimization_level": "balanced"},
                    "incident_sage": {"alert_threshold": "low"},
                    "rag_sage": {"analysis_depth": "medium"},
                },
                "resources": {"cpu": "1", "memory": "2Gi", "storage": "10Gi"},
            },
            "background-job": {
                "technology_stack": ["python", "celery", "redis"],
                "settings": {
                    "build_command": "python -m build",
                    "test_command": "pytest tests/",
                    "health_check_endpoint": "/health",
                },
                "four_sages_custom": {
                    "knowledge_sage": {"learning_rate": "low"},
                    "task_sage": {"optimization_level": "conservative"},
                    "incident_sage": {"alert_threshold": "high"},
                    "rag_sage": {"analysis_depth": "shallow"},
                },
                "resources": {"cpu": "0.5", "memory": "1Gi", "storage": "5Gi"},
            },
        }

    def update_project_config(
        self, project_name: str, config_updates: Dict[str, Any]
    ) -> bool:
        """プロジェクト設定更新"""
        try:
            project_config_path = (
                self.config_dir / "projects" / project_name / "project.yml"
            )

            if project_config_path.exists():
                with open(project_config_path, "r", encoding="utf-8") as f:
                    current_config = yaml.safe_load(f)
            else:
                current_config = {}

            # 設定更新
            self._merge_config(current_config, config_updates)

            # メタデータ更新
            current_config.setdefault("metadata", {})
            current_config["metadata"]["last_updated"] = datetime.now().isoformat()
            current_config["metadata"]["updated_by"] = "elders-guild"

            # 4賢者による最適化
            try:
                optimized_config = self.sages.optimize_deployment_config(current_config)
                current_config = optimized_config
            except Exception as e:
                logger.warning(f"4賢者最適化エラー: {e}")

            # 設定保存
            with open(project_config_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    current_config, f, default_flow_style=False, allow_unicode=True
                )

            logger.info(f"プロジェクト '{project_name}' の設定を更新しました")
            return True

        except Exception as e:
            logger.error(f"プロジェクト設定更新エラー: {e}")
            return False

    def get_deployment_strategy(self, project_name: str, environment: str) -> str:
        """デプロイ戦略取得"""
        try:
            config = self.get_project_config(project_name, environment)
            return config.deployment_method
        except Exception as e:
            logger.error(f"デプロイ戦略取得エラー: {e}")
            return "github_actions"  # デフォルト

    def set_deployment_method(
        self, project_name: str, environment: str, method: str
    ) -> bool:
        """デプロイ方法設定"""
        try:
            valid_methods = ["github_actions", "ssh", "hybrid"]
            if method not in valid_methods:
                raise ValueError(f"無効なデプロイ方法: {method}")

            env_config_path = (
                self.config_dir / "projects" / project_name / f"{environment}.yml"
            )

            if env_config_path.exists():
                with open(env_config_path, "r", encoding="utf-8") as f:
                    env_config = yaml.safe_load(f)
            else:
                env_config = {"environment": environment}

            env_config["deployment_method"] = method
            env_config["last_updated"] = datetime.now().isoformat()

            with open(env_config_path, "w", encoding="utf-8") as f:
                yaml.dump(env_config, f, default_flow_style=False, allow_unicode=True)

            logger.info(
                f"プロジェクト '{project_name}' の {environment} 環境のデプロイ方法を '{method}' に設定しました"
            )
            return True

        except Exception as e:
            logger.error(f"デプロイ方法設定エラー: {e}")
            return False

    def list_projects(self) -> List[str]:
        """プロジェクト一覧取得"""
        try:
            projects_dir = self.config_dir / "projects"
            if not projects_dir.exists():
                return []

            return [d.name for d in projects_dir.iterdir() if d.is_dir()]
        except Exception as e:
            logger.error(f"プロジェクト一覧取得エラー: {e}")
            return []

    def get_project_environments(self, project_name: str) -> List[str]:
        """プロジェクト環境一覧取得"""
        try:
            project_dir = self.config_dir / "projects" / project_name
            if not project_dir.exists():
                return []

            environments = []
            for file in project_dir.iterdir():
                if file.is_file() and file.suffix == ".yml" and file.stem != "project":
                    environments.append(file.stem)

            return sorted(environments)
        except Exception as e:
            logger.error(f"プロジェクト環境一覧取得エラー: {e}")
            return []

    def dry_run_deployment(self, project_name: str, environment: str) -> Dict[str, Any]:
        """デプロイドライラン"""
        try:
            config = self.get_project_config(project_name, environment)

            # 4賢者による事前分析
            pre_analysis = self.sages.pre_deployment_analysis(config.to_dict())

            return {
                "project_name": project_name,
                "environment": environment,
                "deployment_method": config.deployment_method,
                "validation_result": self.validate_config(project_name, environment),
                "four_sages_analysis": pre_analysis,
                "estimated_duration": self._estimate_deployment_duration(config),
                "risk_assessment": self._assess_deployment_risk(config),
            }
        except Exception as e:
            logger.error(f"デプロイドライランエラー: {e}")
            return {"error": str(e)}

    def _estimate_deployment_duration(self, config: DeploymentConfig) -> str:
        """デプロイ時間推定"""
        base_time = 5  # 基本時間（分）

        if config.deployment_method == "github_actions":
            base_time += 10  # CI/CDパイプライン時間
        elif config.deployment_method == "ssh":
            base_time += 3  # SSH直接デプロイ時間

        # プロジェクト規模による調整
        if config.metadata.get("project_size", "medium") == "large":
            base_time *= 1.5

        return f"約 {int(base_time)} 分"

    def _assess_deployment_risk(self, config: DeploymentConfig) -> str:
        """デプロイリスク評価"""
        risk_factors = 0

        # 本番環境チェック
        if any("production" in env for env in config.environments.keys()):
            risk_factors += 2

        # 承認フローチェック
        if not config.environments.get("production", {}).get(
            "approval_required", False
        ):
            risk_factors += 3

        # ロールバック機能チェック
        if not config.environments.get("production", {}).get("rollback_enabled", False):
            risk_factors += 2

        if risk_factors <= 2:
            return "低リスク"
        elif risk_factors <= 4:
            return "中リスク"
        else:
            return "高リスク"

    def generate_deployment_report(
        self, project_name: str, environment: str
    ) -> Dict[str, Any]:
        """デプロイレポート生成"""
        try:
            config = self.get_project_config(project_name, environment)
            validation_result, errors = self.validate_config(project_name, environment)

            report = {
                "project_name": project_name,
                "environment": environment,
                "timestamp": datetime.now().isoformat(),
                "deployment_config": config.to_dict(),
                "validation": {"valid": validation_result, "errors": errors},
                "four_sages_analysis": self.sages.generate_deployment_analysis(
                    config.to_dict()
                ),
                "recommendations": self.sages.generate_deployment_recommendations(
                    config.to_dict()
                ),
            }

            return report
        except Exception as e:
            logger.error(f"デプロイレポート生成エラー: {e}")
            return {"error": str(e)}

# 使用例とテスト用
if __name__ == "__main__":
    # デプロイ設定管理システムのテスト
    manager = ProjectDeploymentManager()

    # プロジェクト作成テスト
    print("🏛️ プロジェクト別デプロイメント設定システムテスト")
    print("=" * 50)

    # テストプロジェクト作成
    project_name = "test-web-app"
    if manager.create_project_config(project_name, "web-app"):
        print(f"✅ プロジェクト '{project_name}' を作成しました")

    # 設定取得テスト
    try:
        config = manager.get_project_config(project_name, "development")
        print(f"✅ 設定取得成功: {config.deployment_method}")
    except Exception as e:
        print(f"❌ 設定取得エラー: {e}")

    # 設定検証テスト
    is_valid, errors = manager.validate_config(project_name, "development")
    if is_valid:
        print("✅ 設定検証成功")
    else:
        print(f"❌ 設定検証エラー: {errors}")

    # デプロイ方法変更テスト
    if manager.set_deployment_method(project_name, "production", "github_actions"):
        print("✅ デプロイ方法変更成功")

    print("\n🏛️ テスト完了")
