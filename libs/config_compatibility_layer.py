#!/usr/bin/env python3
"""
🔗 AI Company 設定互換性レイヤー
既存システムとの完全互換性を確保し、段階的移行を支援

このレイヤーは：
1. 既存の設定アクセスパターンを全て維持
2. 新しい統合設定システムへの透過的な移行
3. 4賢者システムとの完全統合
4. 段階的な移行プロセスのサポート
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from functools import wraps
import warnings

# 統合設定システムのインポート
from .integrated_config_system import IntegratedConfigSystem, get_config as get_integrated_config
from .env_config import Config as LegacyConfig, get_config as get_legacy_config

logger = logging.getLogger(__name__)

class ConfigCompatibilityLayer:
    """設定互換性レイヤー"""
    
    def __init__(self):
        self.project_root = Path("/home/aicompany/ai_co")
        self.config_dir = self.project_root / "config"
        self.integrated_config = IntegratedConfigSystem()
        self.legacy_config = LegacyConfig()
        
        # 移行状態の管理
        self.migration_status = self._check_migration_status()
        
        # フィールドマッピング定義
        self.field_mappings = {
            # レガシー -> 統合設定のマッピング
            "claude.model": "claude.api.model",
            "claude.max_tokens": "claude.api.max_tokens",
            "claude.temperature": "claude.api.temperature",
            "claude.api_key": "claude.api_keys",
            
            "slack.bot_token": "slack.auth.bot_token",
            "slack.app_token": "slack.auth.app_token",
            "slack.channel": "slack.channels.default",
            "slack.polling_interval": "slack.polling.interval",
            
            "workers.timeout": "workers.common.timeout",
            "workers.retry_count": "workers.common.retry_count",
            "workers.max_workers": "workers.common.max_workers",
            
            "database.host": "database.basic.host",
            "database.port": "database.basic.port",
            "database.database": "database.basic.database"
        }
        
        # 逆マッピング
        self.reverse_mappings = {v: k for k, v in self.field_mappings.items()}
        
    def _check_migration_status(self) -> Dict[str, Any]:
        """マイグレーション状態をチェック"""
        migration_state_path = self.config_dir / "migration" / "migration_state.json"
        
        if migration_state_path.exists():
            try:
                with open(migration_state_path) as f:
                    return json.load(f)
            except Exception:
                pass
                
        return {
            "phase": "not_started",
            "completed_steps": [],
            "use_legacy": True
        }
        
    def get_config(self, namespace: str, use_legacy: bool = None) -> Dict[str, Any]:
        """
        互換性を保った設定取得
        
        Args:
            namespace: 設定名前空間
            use_legacy: レガシー設定を使用するか（Noneの場合は自動判定）
            
        Returns:
            設定辞書
        """
        if use_legacy is None:
            use_legacy = self.migration_status.get("use_legacy", True)
            
        if use_legacy or self.migration_status["phase"] == "not_started":
            return self._get_legacy_config(namespace)
        else:
            return self._get_integrated_config(namespace)
            
    def _get_legacy_config(self, namespace: str) -> Dict[str, Any]:
        """レガシー設定システムから設定を取得"""
        try:
            if namespace == "core":
                return self._get_legacy_core_config()
            elif namespace == "claude":
                return self._get_legacy_claude_config()
            elif namespace == "slack":
                return self._get_legacy_slack_config()
            elif namespace == "workers":
                return self._get_legacy_workers_config()
            elif namespace == "database":
                return self._get_legacy_database_config()
            else:
                logger.warning(f"Unknown namespace for legacy config: {namespace}")
                return {}
                
        except Exception as e:
            logger.error(f"Failed to get legacy config for {namespace}: {e}")
            return {}
            
    def _get_integrated_config(self, namespace: str) -> Dict[str, Any]:
        """統合設定システムから設定を取得"""
        try:
            return get_integrated_config(namespace)
        except Exception as e:
            logger.error(f"Failed to get integrated config for {namespace}: {e}")
            # フォールバック
            return self._get_legacy_config(namespace)
            
    def _get_legacy_core_config(self) -> Dict[str, Any]:
        """レガシーコア設定を取得"""
        config = {
            "system": {
                "name": "AI Company",
                "version": "5.3",
                "language": "ja"
            },
            "project": {
                "name": "ai_co",
                "root_dir": str(self.project_root)
            }
        }
        
        # system.jsonから読み込み
        system_json_path = self.config_dir / "system.json"
        if system_json_path.exists():
            try:
                with open(system_json_path) as f:
                    system_config = json.load(f)
                if "language" in system_config:
                    config["system"]["language"] = system_config["language"]
            except Exception as e:
                logger.debug(f"Failed to load system.json: {e}")
                
        return config
        
    def _get_legacy_claude_config(self) -> Dict[str, Any]:
        """レガシーClaude設定を取得"""
        config = {
            "api": {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 4096,
                "temperature": 0.7
            },
            "api_keys": {
                "rotation_enabled": True,
                "rotation_strategy": "rate_limit_aware"
            }
        }
        
        # config.jsonから読み込み
        config_json_path = self.config_dir / "config.json"
        if config_json_path.exists():
            try:
                with open(config_json_path) as f:
                    main_config = json.load(f)
                    
                if "claude" in main_config:
                    claude_config = main_config["claude"]
                    if "model" in claude_config:
                        config["api"]["model"] = claude_config["model"]
                    if "max_tokens" in claude_config:
                        config["api"]["max_tokens"] = claude_config["max_tokens"]
                    if "temperature" in claude_config:
                        config["api"]["temperature"] = claude_config["temperature"]
                    if "api_key_rotation" in claude_config:
                        config["api_keys"].update(claude_config["api_key_rotation"])
                        
            except Exception as e:
                logger.debug(f"Failed to load config.json: {e}")
                
        # 環境変数から取得
        if hasattr(self.legacy_config, 'ANTHROPIC_API_KEY'):
            config["api"]["key"] = self.legacy_config.ANTHROPIC_API_KEY
            
        return config
        
    def _get_legacy_slack_config(self) -> Dict[str, Any]:
        """レガシーSlack設定を取得"""
        config = {
            "basic": {
                "enabled": True,
                "rate_limit": 1
            },
            "channels": {
                "default": "#ai-notifications"
            },
            "polling": {
                "enabled": True,
                "interval": 20
            }
        }
        
        # 各Slack設定ファイルから読み込み
        slack_files = [
            "slack_config.json",
            "slack_pm_config.json",
            "slack_api_config.json"
        ]
        
        for filename in slack_files:
            file_path = self.config_dir / filename
            if file_path.exists():
                try:
                    with open(file_path) as f:
                        slack_config = json.load(f)
                        
                    if "bot_token" in slack_config:
                        config["auth"] = config.get("auth", {})
                        # セキュリティ上、実際のトークンは表示しない
                        config["auth"]["has_bot_token"] = True
                        
                    if "polling_interval" in slack_config:
                        config["polling"]["interval"] = slack_config["polling_interval"]
                        
                    if "rate_limit" in slack_config:
                        config["basic"]["rate_limit"] = slack_config["rate_limit"]
                        
                except Exception as e:
                    logger.debug(f"Failed to load {filename}: {e}")
                    
        # 環境変数から取得
        if hasattr(self.legacy_config, 'SLACK_BOT_TOKEN'):
            config["auth"] = config.get("auth", {})
            config["auth"]["has_bot_token"] = bool(self.legacy_config.SLACK_BOT_TOKEN)
            
        return config
        
    def _get_legacy_workers_config(self) -> Dict[str, Any]:
        """レガシーワーカー設定を取得"""
        config = {
            "common": {
                "timeout": 300,
                "retry_count": 3,
                "max_workers": 4
            },
            "rabbitmq": {
                "host": "localhost",
                "port": 5672
            }
        }
        
        # worker_config.jsonから読み込み
        worker_config_path = self.config_dir / "worker_config.json"
        if worker_config_path.exists():
            try:
                with open(worker_config_path) as f:
                    worker_config = json.load(f)
                    
                if "timeout" in worker_config:
                    config["common"]["timeout"] = worker_config["timeout"]
                if "retry_count" in worker_config:
                    config["common"]["retry_count"] = worker_config["retry_count"]
                    
            except Exception as e:
                logger.debug(f"Failed to load worker_config.json: {e}")
                
        # async_workers_config.yamlから読み込み
        async_config_path = self.config_dir / "async_workers_config.yaml"
        if async_config_path.exists():
            try:
                with open(async_config_path) as f:
                    async_config = yaml.safe_load(f)
                    
                if "common" in async_config:
                    common_config = async_config["common"]
                    if "rabbitmq_host" in common_config:
                        config["rabbitmq"]["host"] = common_config["rabbitmq_host"]
                    if "rabbitmq_port" in common_config:
                        config["rabbitmq"]["port"] = common_config["rabbitmq_port"]
                        
            except Exception as e:
                logger.debug(f"Failed to load async_workers_config.yaml: {e}")
                
        return config
        
    def _get_legacy_database_config(self) -> Dict[str, Any]:
        """レガシーデータベース設定を取得"""
        config = {
            "basic": {
                "driver": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "ai_company"
            }
        }
        
        # database.confから読み込み
        database_conf_path = self.config_dir / "database.conf"
        if database_conf_path.exists():
            try:
                import configparser
                parser = configparser.ConfigParser()
                parser.read(database_conf_path)
                
                if "database" in parser:
                    db_section = parser["database"]
                    if "host" in db_section:
                        config["basic"]["host"] = db_section["host"]
                    if "port" in db_section:
                        config["basic"]["port"] = int(db_section["port"])
                    if "database_name" in db_section:
                        config["basic"]["database"] = db_section["database_name"]
                    if "driver" in db_section:
                        config["basic"]["driver"] = db_section["driver"]
                        
            except Exception as e:
                logger.debug(f"Failed to load database.conf: {e}")
                
        # 環境変数から取得
        if hasattr(self.legacy_config, 'DATABASE_URL'):
            config["basic"]["url"] = self.legacy_config.DATABASE_URL
            
        return config
        
    def get_field_value(self, field_path: str, default: Any = None) -> Any:
        """
        フィールドパスから値を取得（レガシーパス対応）
        
        Args:
            field_path: フィールドパス（例: "claude.model"）
            default: デフォルト値
            
        Returns:
            フィールド値
        """
        # レガシーパスを統合パスに変換
        if field_path in self.field_mappings:
            integrated_path = self.field_mappings[field_path]
        else:
            integrated_path = field_path
            
        # 名前空間を抽出
        namespace = integrated_path.split('.')[0]
        
        try:
            config = self.get_config(namespace)
            return self._get_nested_value(config, integrated_path, default)
        except Exception as e:
            logger.debug(f"Failed to get field value {field_path}: {e}")
            return default
            
    def _get_nested_value(self, config: Dict[str, Any], path: str, default: Any = None) -> Any:
        """ネストされた値を取得"""
        keys = path.split('.')
        current = config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
                
        return current
        
    def set_field_value(self, field_path: str, value: Any) -> bool:
        """
        フィールドパスに値を設定
        
        Args:
            field_path: フィールドパス
            value: 設定値
            
        Returns:
            設定成功フラグ
        """
        # 統合設定システムが利用可能な場合のみ設定可能
        if self.migration_status["phase"] == "not_started":
            logger.warning("Cannot set field value before migration")
            return False
            
        # レガシーパスを統合パスに変換
        if field_path in self.field_mappings:
            integrated_path = self.field_mappings[field_path]
        else:
            integrated_path = field_path
            
        # 名前空間を抽出
        namespace = integrated_path.split('.')[0]
        
        try:
            # 統合設定システムで設定
            config = self.get_config(namespace)
            self._set_nested_value(config, integrated_path, value)
            return True
        except Exception as e:
            logger.error(f"Failed to set field value {field_path}: {e}")
            return False
            
    def _set_nested_value(self, config: Dict[str, Any], path: str, value: Any):
        """ネストされた値を設定"""
        keys = path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
            
        current[keys[-1]] = value

def deprecated_config_warning(func):
    """非推奨設定アクセスの警告デコレータ"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        warnings.warn(
            f"Function {func.__name__} is deprecated. Use the integrated config system instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return func(*args, **kwargs)
    return wrapper

# グローバルインスタンス
compatibility_layer = ConfigCompatibilityLayer()

# 互換性維持のための関数
def get_config(namespace: str) -> Dict[str, Any]:
    """設定取得（互換性維持）"""
    return compatibility_layer.get_config(namespace)

def get_field_value(field_path: str, default: Any = None) -> Any:
    """フィールド値取得（互換性維持）"""
    return compatibility_layer.get_field_value(field_path, default)

# レガシー関数の互換性維持
@deprecated_config_warning
def get_legacy_config() -> LegacyConfig:
    """レガシー設定取得（非推奨）"""
    return compatibility_layer.legacy_config

@deprecated_config_warning
def load_config_json(filename: str) -> Dict[str, Any]:
    """JSONファイル読み込み（非推奨）"""
    config_path = compatibility_layer.config_dir / filename
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    return {}

@deprecated_config_warning
def load_config_yaml(filename: str) -> Dict[str, Any]:
    """YAMLファイル読み込み（非推奨）"""
    config_path = compatibility_layer.config_dir / filename
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    return {}

def health_check() -> Dict[str, Any]:
    """互換性レイヤーの健全性チェック"""
    return {
        "compatibility_layer": "healthy",
        "migration_status": compatibility_layer.migration_status,
        "legacy_config_available": True,
        "integrated_config_available": compatibility_layer.migration_status["phase"] != "not_started"
    }