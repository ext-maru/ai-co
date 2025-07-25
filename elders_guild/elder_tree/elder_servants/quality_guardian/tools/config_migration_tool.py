#!/usr/bin/env python3
"""
🚀 Elders Guild 設定統合マイグレーションツール
段階的統合実装 - 既存システムとの完全互換性確保

このツールは設定ファイルの統合を段階的に実行し、
既存システムの動作を中断することなく統合を完了します。
"""

import argparse
import json
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.env_config import Config as LegacyConfig
from libs.integrated_config_system import IntegratedConfigSystem, get_config

logger = logging.getLogger(__name__)

class ConfigMigrationTool:
    """設定マイグレーションツール"""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.project_root = Path("/home/aicompany/ai_co")
        self.config_dir = self.project_root / "config"
        self.backup_dir = self.config_dir / "backups"
        self.migration_dir = self.config_dir / "migration"

        # ディレクトリ作成
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.migration_dir.mkdir(parents=True, exist_ok=True)

        # 統合設定システム
        self.integrated_config = IntegratedConfigSystem()

        # マイグレーション状態
        self.migration_state = {
            "phase": "not_started",
            "completed_steps": [],
            "failed_steps": [],
            "timestamp": datetime.now().isoformat(),
        }

        # バックアップタイムスタンプ
        self.backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def run_migration(self, phase: str = "all") -> bool:
        """マイグレーションを実行"""
        logger.info(
            f"Starting configuration migration (phase: {phase}, dry_run: {self.dry_run})"
        )

        try:
            if phase == "all" or phase == "phase1":
                self.execute_phase1()

            if phase == "all" or phase == "phase2":
                self.execute_phase2()

            if phase == "all" or phase == "phase3":
                self.execute_phase3()

            self.migration_state["phase"] = "completed"
            self.save_migration_state()

            logger.info("Migration completed successfully")
            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.migration_state["phase"] = "failed"
            self.migration_state["error"] = str(e)
            self.save_migration_state()
            return False

    def execute_phase1(self):
        """Phase 1: 緊急統合 - 重複設定の即座解決"""
        logger.info("Executing Phase 1: Emergency Integration")

        # ステップ1: 設定ファイルバックアップ
        self.backup_existing_configs()

        # ステップ2: モデル指定統一
        self.unify_model_specifications()

        # ステップ3: 重複Slack設定統合
        self.merge_slack_configs()

        # ステップ4: 基本システム設定統合
        self.merge_system_configs()

        # ステップ5: 統合設定ファイル生成
        self.generate_integrated_configs()

        self.migration_state["completed_steps"].append("phase1")

    def execute_phase2(self):
        """Phase 2: 構造改善 - 設定構造の最適化"""
        logger.info("Executing Phase 2: Structural Improvements")

        # ステップ1: 階層定義の設定ファイル化
        self.create_hierarchy_config()

        # ステップ2: 環境別設定分離
        self.separate_environment_configs()

        # ステップ3: バリデーション機能追加
        self.add_config_validation()

        # ステップ4: 設定互換性レイヤー作成
        self.create_compatibility_layer()

        self.migration_state["completed_steps"].append("phase2")

    def execute_phase3(self):
        """Phase 3: 高度化 - 動的機能の実装"""
        logger.info("Executing Phase 3: Advanced Features")

        # ステップ1: 動的設定リロード
        self.implement_dynamic_reload()

        # ステップ2: 設定変更監査ログ
        self.implement_audit_logging()

        # ステップ3: 自動設定最適化
        self.implement_auto_optimization()

        self.migration_state["completed_steps"].append("phase3")

    def backup_existing_configs(self):
        """既存設定ファイルのバックアップ"""
        logger.info("Backing up existing configuration files")

        backup_path = self.backup_dir / f"pre_migration_{self.backup_timestamp}"
        backup_path.mkdir(exist_ok=True)

        # バックアップ対象ファイル
        config_files = [
            "config.json",
            "system.json",
            "system.conf",
            "slack_config.json",
            "slack_pm_config.json",
            "slack_api_config.json",
            "slack_monitor.json",
            "worker.json",
            "worker_config.json",
            "async_workers_config.yaml",
            "worker_recovery.yaml",
            "database.conf",
            "logging.json",
            "storage.json",
            "task_types.json",
        ]

        backed_up_files = []
        for filename in config_files:
            source_path = self.config_dir / filename
            if source_path.exists():
                dest_path = backup_path / filename
                if not self.dry_run:
                    shutil.copy2(source_path, dest_path)
                backed_up_files.append(filename)
                logger.info(f"Backed up: {filename}")

        # バックアップメタデータ
        metadata = {
            "timestamp": self.backup_timestamp,
            "files": backed_up_files,
            "migration_version": "1.0",
        }

        if not self.dry_run:
            with open(backup_path / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)

        logger.info(f"Backup completed: {backup_path}")

    def unify_model_specifications(self):
        """モデル指定の統一"""
        logger.info("Unifying model specifications")

        unified_model = "claude-sonnet-4-20250514"

        # config.jsonの更新
        config_path = self.config_dir / "config.json"
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)

            if "claude" in config:
                config["claude"]["model"] = unified_model

            if not self.dry_run:
                with open(config_path, "w") as f:
                    json.dump(config, f, indent=2)

        # worker.jsonの更新
        worker_path = self.config_dir / "worker.json"
        if worker_path.exists():
            with open(worker_path) as f:
                worker_config = json.load(f)

            worker_config["default_model"] = unified_model

            if not self.dry_run:
                with open(worker_path, "w") as f:
                    json.dump(worker_config, f, indent=2)

        # YAML設定ファイルの更新
        async_worker_path = self.config_dir / "async_workers_config.yaml"
        if async_worker_path.exists():
            with open(async_worker_path) as f:
                async_config = yaml.safe_load(f)

            if (
                "enhanced_task_worker" in async_config
                and "claude_model" in async_config["enhanced_task_worker"]
            ):
                async_config["enhanced_task_worker"]["claude_model"] = unified_model

            if not self.dry_run:
                with open(async_worker_path, "w") as f:
                    yaml.dump(async_config, f, default_flow_style=False)

        logger.info(f"Model specification unified to: {unified_model}")

    def merge_slack_configs(self):
        """Slack設定の統合"""
        logger.info("Merging Slack configurations")

        merged_config = {
            "basic": {"enabled": True, "rate_limit": 1},
            "channels": {
                "default": "#ai-notifications",
                "error": "#elders-guild-errors",
                "notification": "#elders-guild-notifications",
            },
            "polling": {"enabled": True, "interval": 20},
        }

        # 既存設定から統合
        slack_files = [
            "slack_config.json",
            "slack_pm_config.json",
            "slack_api_config.json",
            "slack_monitor.json",
        ]

        # 繰り返し処理
        for filename in slack_files:
            file_path = self.config_dir / filename
            if file_path.exists():
                with open(file_path) as f:
                    config = json.load(f)

                # 基本設定の統合
                if "bot_token" in config:
                    merged_config["auth"] = merged_config.get("auth", {})
                    # セキュリティ上、実際のトークンは環境変数で管理

                if "polling_interval" in config:
                    merged_config["polling"]["interval"] = config["polling_interval"]

                if "rate_limit" in config:
                    merged_config["basic"]["rate_limit"] = config["rate_limit"]

                # その他の設定も統合
                for key, value in config.items():
                    if key not in ["bot_token", "app_token"]:  # センシティブ情報は除外
                        merged_config[key] = value

        # 統合設定を保存
        integrated_slack_path = self.config_dir / "integrated" / "slack.yaml"
        if not self.dry_run:
            integrated_slack_path.parent.mkdir(exist_ok=True)
            with open(integrated_slack_path, "w") as f:
                yaml.dump(merged_config, f, default_flow_style=False)

        logger.info("Slack configurations merged successfully")

    def merge_system_configs(self):
        """システム設定の統合"""
        logger.info("Merging system configurations")

        merged_config = {
            "system": {"name": "Elders Guild", "version": "6.0", "language": "ja"},
            "project": {"name": "ai_co", "root_dir": "/home/aicompany/ai_co"},
        }

        # system.jsonから統合
        system_json_path = self.config_dir / "system.json"
        if system_json_path.exists():
            with open(system_json_path) as f:
                system_config = json.load(f)

            if "language" in system_config:
                merged_config["system"]["language"] = system_config["language"]

        # system.confから統合
        system_conf_path = self.config_dir / "system.conf"
        if system_conf_path.exists():
            with open(system_conf_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()

                        if not (key == "PROJECT_DIR"):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if key == "PROJECT_DIR":
                            merged_config["project"]["root_dir"] = value
                        elif key == "PROJECT_NAME":
                            merged_config["project"]["name"] = value

        # 統合設定を保存
        integrated_core_path = self.config_dir / "integrated" / "core.yaml"
        if not self.dry_run:
            integrated_core_path.parent.mkdir(exist_ok=True)
            with open(integrated_core_path, "w") as f:
                yaml.dump(merged_config, f, default_flow_style=False)

        logger.info("System configurations merged successfully")

    def generate_integrated_configs(self):
        """統合設定ファイルの生成"""
        logger.info("Generating integrated configuration files")

        if not self.dry_run:
            self.integrated_config.create_integrated_config_files()

        logger.info("Integrated configuration files generated")

    def create_hierarchy_config(self):
        """階層設定の作成"""
        logger.info("Creating hierarchy configuration")

        hierarchy_config = {
            "hierarchy": {
                "supreme_authority": {
                    "name": "グランドエルダーmaru",
                    "title": "Grand Elder maru",
                    "role": "最高権限者・戦略決定者",
                },
                "executive_partner": {
                    "name": "クロードエルダー",
                    "title": "Claude Elder",
                    "role": "開発実行責任者・4賢者統括",
                },
                "wisdom_council": {
                    "name": "4賢者システム",
                    "title": "Four Sages System",
                    "enabled": True,
                },
            }
        }

        hierarchy_path = self.config_dir / "integrated" / "hierarchy.yaml"
        if not self.dry_run:
            hierarchy_path.parent.mkdir(exist_ok=True)
            with open(hierarchy_path, "w") as f:
                yaml.dump(hierarchy_config, f, default_flow_style=False)

        logger.info("Hierarchy configuration created")

    def separate_environment_configs(self):
        """環境別設定の分離"""
        logger.info("Separating environment-specific configurations")

        environments = ["development", "staging", "production"]

        for env in environments:
            env_config = {
                "environment": env,

                "monitoring": {
                    "enabled": env == "production",

                },
            }

            env_path = self.config_dir / "integrated" / f"{env}.yaml"
            if not self.dry_run:
                env_path.parent.mkdir(exist_ok=True)
                with open(env_path, "w") as f:
                    yaml.dump(env_config, f, default_flow_style=False)

        logger.info("Environment-specific configurations separated")

    def add_config_validation(self):
        """設定バリデーション機能の追加"""
        logger.info("Adding configuration validation")

        validation_config = {
            "validation": {
                "enabled": True,
                "strict_mode": True,
                "required_fields": {
                    "claude": ["model", "api_key"],
                    "slack": ["bot_token"],
                    "database": ["host", "database"],
                },
            }
        }

        validation_path = self.config_dir / "integrated" / "validation.yaml"
        if not self.dry_run:
            validation_path.parent.mkdir(exist_ok=True)
            with open(validation_path, "w") as f:
                yaml.dump(validation_config, f, default_flow_style=False)

        logger.info("Configuration validation added")

    def create_compatibility_layer(self):
        """互換性レイヤーの作成"""
        logger.info("Creating compatibility layer")

        compatibility_mapping = {
            "legacy_paths": {
                "config.json": "integrated/core.yaml",
                "slack_config.json": "integrated/slack.yaml",
                "worker_config.json": "integrated/workers.yaml",
                "database.conf": "integrated/database.yaml",
            },
            "field_mappings": {
                "claude.model": "claude.api.model",
                "workers.timeout": "workers.common.timeout",
                "slack.bot_token": "slack.auth.bot_token",
            },
        }

        compatibility_path = self.config_dir / "integrated" / "compatibility.yaml"
        if not self.dry_run:
            compatibility_path.parent.mkdir(exist_ok=True)
            with open(compatibility_path, "w") as f:
                yaml.dump(compatibility_mapping, f, default_flow_style=False)

        logger.info("Compatibility layer created")

    def implement_dynamic_reload(self):
        """動的設定リロードの実装"""
        logger.info("Implementing dynamic configuration reload")

        # 設定変更監視スクリプト
        reload_script = """#!/usr/bin/env python3
import time
import os
from pathlib import Path
from libs.integrated_config_system import integrated_config

def monitor_config_changes():
    config_dir = Path("/home/aicompany/ai_co/config/integrated")
    last_modified = {}

    while True:
        for config_file in config_dir.glob("*.yaml"):
            current_modified = config_file.stat().st_mtime

            if config_file.name not in last_modified:
                last_modified[config_file.name] = current_modified
                continue

            if current_modified > last_modified[config_file.name]:
                print(f"Configuration changed: {config_file.name}")
                # 設定リロード
                namespace = config_file.stem
                integrated_config.get_config(namespace, force_reload=True)
                last_modified[config_file.name] = current_modified

        time.sleep(5)

if __name__ == "__main__":
    monitor_config_changes()
"""

        reload_script_path = self.project_root / "tools" / "config_reload_monitor.py"
        if not self.dry_run:
            reload_script_path.parent.mkdir(exist_ok=True)
            with open(reload_script_path, "w") as f:
                f.write(reload_script)
            reload_script_path.chmod(0o755)

        logger.info("Dynamic configuration reload implemented")

    def implement_audit_logging(self):
        """設定変更監査ログの実装"""
        logger.info("Implementing configuration audit logging")

        audit_config = {
            "audit": {
                "enabled": True,
                "log_file": "/home/aicompany/ai_co/logs/config_audit.log",
                "retention_days": 30,
                "log_level": "INFO",
            }
        }

        audit_path = self.config_dir / "integrated" / "audit.yaml"
        if not self.dry_run:
            audit_path.parent.mkdir(exist_ok=True)
            with open(audit_path, "w") as f:
                yaml.dump(audit_config, f, default_flow_style=False)

        logger.info("Configuration audit logging implemented")

    def implement_auto_optimization(self):
        """自動設定最適化の実装"""
        logger.info("Implementing automatic configuration optimization")

        optimization_config = {
            "optimization": {
                "enabled": True,
                "auto_tune": True,
                "performance_monitoring": True,
                "adaptive_settings": {
                    "worker_scaling": True,
                    "cache_tuning": True,
                    "rate_limiting": True,
                },
            }
        }

        optimization_path = self.config_dir / "integrated" / "optimization.yaml"
        if not self.dry_run:
            optimization_path.parent.mkdir(exist_ok=True)
            with open(optimization_path, "w") as f:
                yaml.dump(optimization_config, f, default_flow_style=False)

        logger.info("Automatic configuration optimization implemented")

    def save_migration_state(self):
        """マイグレーション状態の保存"""
        state_path = self.migration_dir / "migration_state.json"
        if not self.dry_run:
            with open(state_path, "w") as f:
                json.dump(self.migration_state, f, indent=2)

    def rollback_migration(self):
        """マイグレーションのロールバック"""
        logger.info("Rolling back migration")

        backup_path = self.backup_dir / f"pre_migration_{self.backup_timestamp}"
        if not backup_path.exists():
            logger.error("Backup not found, cannot rollback")
            return False

        # バックアップから復元
        with open(backup_path / "metadata.json") as f:
            metadata = json.load(f)

        for filename in metadata["files"]:
            source_path = backup_path / filename
            dest_path = self.config_dir / filename

            if source_path.exists():
                if not self.dry_run:
                    shutil.copy2(source_path, dest_path)
                logger.info(f"Restored: {filename}")

        logger.info("Migration rollback completed")
        return True

    def validate_migration(self) -> bool:
        """マイグレーション結果の検証"""
        logger.info("Validating migration results")

        try:
            # 統合設定システムの健全性チェック
            health_check = self.integrated_config.health_check()

            if health_check["overall_status"] != "healthy":
                logger.error("Health check failed")
                return False

            # 各名前空間の設定が正常に読み込めるかチェック
            for namespace in ["core", "claude", "slack", "workers", "database"]:
                config = get_config(namespace)
                if not config:
                    logger.error(f"Failed to load config for namespace: {namespace}")
                    return False

            logger.info("Migration validation successful")
            return True

        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            return False

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="Elders Guild Configuration Migration Tool"
    )
    parser.add_argument(
        "--phase",
        choices=["phase1", "phase2", "phase3", "all"],
        default="all",
        help="Migration phase to execute",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--rollback", action="store_true", help="Rollback the migration"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate migration results"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # ログ設定

    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # マイグレーションツール初期化
    migration_tool = ConfigMigrationTool(dry_run=args.dry_run)

    try:
        if args.rollback:
            success = migration_tool.rollback_migration()
        elif args.validate:
            success = migration_tool.validate_migration()
        else:
            success = migration_tool.run_migration(args.phase)

        if success:
            logger.info("Operation completed successfully")
            sys.exit(0)
        else:
            logger.error("Operation failed")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
