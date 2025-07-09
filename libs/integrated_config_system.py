#!/usr/bin/env python3
"""
🏛️ AI Company統合設定システム - 4賢者統合対応版
設定ファイル統合プロジェクト - 全設定を一元管理し、4賢者システムとの完全統合を実現

Design Principles:
- 4賢者システムとの完全整合性
- 環境変数 > YAML > JSON > CONF の階層設定
- セキュリティ第一のアプローチ
- 既存システムとの後方互換性確保
- 段階的移行サポート
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager
import hashlib
import shutil
from enum import Enum

logger = logging.getLogger(__name__)

class ConfigPriority(Enum):
    """設定の優先順位"""
    ENVIRONMENT = 1     # 環境変数（最高優先度）
    YAML = 2           # YAML設定ファイル
    JSON = 3           # JSON設定ファイル
    CONF = 4           # CONF設定ファイル
    DEFAULT = 5        # デフォルト値（最低優先度）

@dataclass
class ConfigSource:
    """設定ソースの定義"""
    name: str
    path: Path
    priority: ConfigPriority
    format: str
    required: bool = True
    validator: Optional[callable] = None
    
    def exists(self) -> bool:
        """ファイルが存在するかチェック"""
        return self.path.exists() if self.path else False

@dataclass
class ConfigNamespace:
    """設定名前空間の定義"""
    name: str
    sources: List[ConfigSource] = field(default_factory=list)
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    defaults: Dict[str, Any] = field(default_factory=dict)
    
class IntegratedConfigSystem:
    """統合設定システム - 4賢者システム対応"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path("/home/aicompany/ai_co")
        self.config_dir = self.project_root / "config"
        self.backup_dir = self.config_dir / "backups"
        self.integrated_dir = self.config_dir / "integrated"
        
        # ディレクトリ作成
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.integrated_dir.mkdir(parents=True, exist_ok=True)
        
        # 設定キャッシュ
        self._config_cache = {}
        self._config_timestamps = {}
        
        # 4賢者システム統合設定
        self._setup_four_sages_integration()
        
        # 設定名前空間の初期化
        self._setup_namespaces()
        
    def _setup_four_sages_integration(self):
        """4賢者システムとの統合設定"""
        self.four_sages_config = {
            "knowledge_sage": {
                "model": "claude-sonnet-4-20250514",
                "temperature": 0.3,
                "max_tokens": 4096,
                "specialty": "knowledge_management"
            },
            "task_sage": {
                "model": "claude-sonnet-4-20250514", 
                "temperature": 0.5,
                "max_tokens": 4096,
                "specialty": "task_optimization"
            },
            "incident_sage": {
                "model": "claude-sonnet-4-20250514",
                "temperature": 0.1,
                "max_tokens": 4096,
                "specialty": "crisis_response"
            },
            "rag_sage": {
                "model": "claude-sonnet-4-20250514",
                "temperature": 0.4,
                "max_tokens": 4096,
                "specialty": "information_search"
            }
        }
        
    def _setup_namespaces(self):
        """設定名前空間の初期化"""
        self.namespaces = {
            # Core System Configuration
            "core": ConfigNamespace(
                name="core",
                sources=[
                    ConfigSource("env", None, ConfigPriority.ENVIRONMENT, "env"),
                    ConfigSource("main", self.integrated_dir / "core.yaml", ConfigPriority.YAML, "yaml"),
                    ConfigSource("legacy_config", self.config_dir / "config.json", ConfigPriority.JSON, "json", required=False),
                    ConfigSource("legacy_system", self.config_dir / "system.json", ConfigPriority.JSON, "json", required=False),
                ],
                defaults={
                    "language": "ja",
                    "version": "6.0",
                    "debug": False,
                    "log_level": "INFO"
                }
            ),
            
            # Claude API Configuration
            "claude": ConfigNamespace(
                name="claude",
                sources=[
                    ConfigSource("env", None, ConfigPriority.ENVIRONMENT, "env"),
                    ConfigSource("main", self.integrated_dir / "claude.yaml", ConfigPriority.YAML, "yaml"),
                ],
                defaults={
                    "model": "claude-sonnet-4-20250514",
                    "temperature": 0.7,
                    "max_tokens": 4096,
                    "api_key_rotation": {
                        "enabled": True,
                        "strategy": "rate_limit_aware",
                        "cooldown_minutes": 60,
                        "max_retries": 3
                    }
                }
            ),
            
            # Slack Integration Configuration
            "slack": ConfigNamespace(
                name="slack",
                sources=[
                    ConfigSource("env", None, ConfigPriority.ENVIRONMENT, "env"),
                    ConfigSource("main", self.integrated_dir / "slack.yaml", ConfigPriority.YAML, "yaml"),
                    ConfigSource("legacy_config", self.config_dir / "slack_config.json", ConfigPriority.JSON, "json", required=False),
                    ConfigSource("legacy_pm", self.config_dir / "slack_pm_config.json", ConfigPriority.JSON, "json", required=False),
                ],
                defaults={
                    "enabled": True,
                    "polling_interval": 20,
                    "rate_limit": 1,
                    "channel": "#ai-notifications"
                }
            ),
            
            # Worker Configuration
            "workers": ConfigNamespace(
                name="workers",
                sources=[
                    ConfigSource("env", None, ConfigPriority.ENVIRONMENT, "env"),
                    ConfigSource("main", self.integrated_dir / "workers.yaml", ConfigPriority.YAML, "yaml"),
                    ConfigSource("legacy_async", self.config_dir / "async_workers_config.yaml", ConfigPriority.YAML, "yaml", required=False),
                    ConfigSource("legacy_worker", self.config_dir / "worker_config.json", ConfigPriority.JSON, "json", required=False),
                ],
                defaults={
                    "max_workers": 4,
                    "timeout": 300,
                    "retry_count": 3,
                    "retry_delay": 60
                }
            ),
            
            # Database Configuration
            "database": ConfigNamespace(
                name="database",
                sources=[
                    ConfigSource("env", None, ConfigPriority.ENVIRONMENT, "env"),
                    ConfigSource("main", self.integrated_dir / "database.yaml", ConfigPriority.YAML, "yaml"),
                    ConfigSource("legacy_conf", self.config_dir / "database.conf", ConfigPriority.CONF, "conf", required=False),
                ],
                defaults={
                    "host": "localhost",
                    "port": 5432,
                    "database": "ai_company",
                    "driver": "postgresql"
                }
            ),
        }
    
    def get_config(self, namespace: str, force_reload: bool = False) -> Dict[str, Any]:
        """設定を取得（キャッシュ機能付き）"""
        if not force_reload and namespace in self._config_cache:
            # タイムスタンプをチェックしてキャッシュの有効性を確認
            if self._is_cache_valid(namespace):
                return self._config_cache[namespace]
        
        if namespace not in self.namespaces:
            raise ValueError(f"Unknown namespace: {namespace}")
        
        config_namespace = self.namespaces[namespace]
        config = config_namespace.defaults.copy()
        
        # 優先順位順に設定をマージ
        for source in sorted(config_namespace.sources, key=lambda x: x.priority.value):
            try:
                source_config = self._load_from_source(source, namespace)
                if source_config:
                    config = self._deep_merge(config, source_config)
                    logger.debug(f"Loaded config from {source.name} for {namespace}")
            except Exception as e:
                if source.required:
                    logger.error(f"Failed to load required source {source.name} for {namespace}: {e}")
                    raise
                else:
                    logger.debug(f"Optional source {source.name} not available for {namespace}: {e}")
        
        # 4賢者システム統合設定を適用
        if namespace == "claude":
            config = self._apply_four_sages_integration(config)
        
        # 設定を検証
        validated_config = self._validate_config(namespace, config)
        
        # キャッシュに保存
        self._config_cache[namespace] = validated_config
        self._config_timestamps[namespace] = datetime.now()
        
        return validated_config
    
    def _load_from_source(self, source: ConfigSource, namespace: str) -> Optional[Dict[str, Any]]:
        """設定ソースから読み込み"""
        if source.format == "env":
            return self._load_from_env(namespace)
        elif source.format == "yaml":
            return self._load_yaml_file(source.path)
        elif source.format == "json":
            return self._load_json_file(source.path)
        elif source.format == "conf":
            return self._load_conf_file(source.path)
        else:
            raise ValueError(f"Unsupported format: {source.format}")
    
    def _load_from_env(self, namespace: str) -> Dict[str, Any]:
        """環境変数から設定を読み込み"""
        config = {}
        env_mappings = {
            "core": {
                "AI_COMPANY_LANGUAGE": "language",
                "AI_COMPANY_VERSION": "version",
                "DEBUG": "debug",
                "LOG_LEVEL": "log_level"
            },
            "claude": {
                "ANTHROPIC_API_KEY": "api_key",
                "ANTHROPIC_API_KEYS": "api_keys",
                "CLAUDE_MODEL": "model",
                "CLAUDE_TEMPERATURE": "temperature",
                "CLAUDE_MAX_TOKENS": "max_tokens",
                "API_KEY_ROTATION_ENABLED": "api_key_rotation.enabled",
                "API_KEY_ROTATION_STRATEGY": "api_key_rotation.strategy",
                "API_KEY_COOLDOWN_MINUTES": "api_key_rotation.cooldown_minutes",
                "API_KEY_MAX_RETRIES": "api_key_rotation.max_retries"
            },
            "slack": {
                "SLACK_BOT_TOKEN": "bot_token",
                "SLACK_APP_TOKEN": "app_token",
                "SLACK_CHANNEL": "channel",
                "SLACK_CHANNEL_ID": "channel_id",
                "SLACK_CHANNEL_IDS": "channel_ids",
                "SLACK_POLLING_CHANNEL_ID": "polling_channel_id",
                "SLACK_POLLING_INTERVAL": "polling_interval",
                "SLACK_POLLING_ENABLED": "polling_enabled",
                "SLACK_WEBHOOK_URL": "webhook_url",
                "SLACK_RATE_LIMIT": "rate_limit"
            },
            "workers": {
                "MAX_WORKERS": "max_workers",
                "WORKER_TIMEOUT": "timeout",
                "WORKER_RETRY_COUNT": "retry_count",
                "WORKER_RETRY_DELAY": "retry_delay"
            },
            "database": {
                "DATABASE_URL": "url",
                "DB_HOST": "host",
                "DB_PORT": "port",
                "DB_NAME": "database",
                "DB_USER": "user",
                "DB_PASSWORD": "password",
                "DB_DRIVER": "driver"
            }
        }
        
        mappings = env_mappings.get(namespace, {})
        for env_key, config_key in mappings.items():
            value = os.getenv(env_key)
            if value is not None:
                # ネストされたキーをサポート
                if "." in config_key:
                    self._set_nested_value(config, config_key, value)
                else:
                    config[config_key] = self._convert_env_value(value)
        
        return config
    
    def _load_yaml_file(self, path: Path) -> Optional[Dict[str, Any]]:
        """YAMLファイルから読み込み"""
        if not path.exists():
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load YAML file {path}: {e}")
            return None
    
    def _load_json_file(self, path: Path) -> Optional[Dict[str, Any]]:
        """JSONファイルから読み込み"""
        if not path.exists():
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load JSON file {path}: {e}")
            return None
    
    def _load_conf_file(self, path: Path) -> Optional[Dict[str, Any]]:
        """CONFファイルから読み込み（INI形式）"""
        if not path.exists():
            return None
        
        try:
            import configparser
            parser = configparser.ConfigParser()
            parser.read(path)
            
            config = {}
            for section in parser.sections():
                config[section] = dict(parser[section])
            
            # セクションがない場合は直接辞書として扱う
            if not config:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
            
            return config
        except Exception as e:
            logger.error(f"Failed to load CONF file {path}: {e}")
            return None
    
    def _apply_four_sages_integration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """4賢者システム統合設定を適用"""
        # 全賢者で統一モデルを使用
        config["model"] = "claude-sonnet-4-20250514"
        
        # 4賢者固有の設定を追加
        config["four_sages"] = self.four_sages_config
        
        return config
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """深い階層でのマージ"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any):
        """ネストされたキーに値を設定"""
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = self._convert_env_value(value)
    
    def _convert_env_value(self, value: str) -> Any:
        """環境変数値を適切な型に変換"""
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        if value.isdigit():
            return int(value)
        
        try:
            return float(value)
        except ValueError:
            pass
        
        return value
    
    def _validate_config(self, namespace: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """設定の検証"""
        # 基本的な検証
        if namespace == "claude":
            if "api_key" not in config or not config["api_key"]:
                logger.warning("Claude API key not configured")
        
        elif namespace == "slack":
            if "bot_token" not in config or not config["bot_token"]:
                logger.warning("Slack bot token not configured")
        
        return config
    
    def _is_cache_valid(self, namespace: str) -> bool:
        """キャッシュの有効性をチェック"""
        if namespace not in self._config_timestamps:
            return False
        
        # 5分間キャッシュを有効とする
        cache_duration = 300  # 5 minutes
        elapsed = (datetime.now() - self._config_timestamps[namespace]).total_seconds()
        
        return elapsed < cache_duration
    
    def create_integrated_config_files(self):
        """統合設定ファイルを作成"""
        logger.info("Creating integrated configuration files...")
        
        # 各名前空間の統合設定ファイルを作成
        for namespace_name, namespace in self.namespaces.items():
            integrated_path = self.integrated_dir / f"{namespace_name}.yaml"
            
            # 既存の設定を収集
            config = self.get_config(namespace_name)
            
            # YAMLファイルとして保存
            with open(integrated_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Created integrated config: {integrated_path}")
    
    def migrate_legacy_configs(self):
        """レガシー設定ファイルを統合設定に移行"""
        logger.info("Migrating legacy configuration files...")
        
        # バックアップ作成
        backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"legacy_backup_{backup_timestamp}"
        backup_path.mkdir(exist_ok=True)
        
        # レガシーファイルをバックアップ
        legacy_files = [
            "config.json",
            "system.json", 
            "system.conf",
            "slack_config.json",
            "slack_pm_config.json",
            "worker_config.json",
            "async_workers_config.yaml",
            "database.conf"
        ]
        
        for filename in legacy_files:
            source_path = self.config_dir / filename
            if source_path.exists():
                backup_file_path = backup_path / filename
                shutil.copy2(source_path, backup_file_path)
                logger.info(f"Backed up: {filename}")
        
        # 統合設定ファイルを作成
        self.create_integrated_config_files()
        
        logger.info(f"Migration completed. Backup saved to: {backup_path}")
    
    def health_check(self) -> Dict[str, Any]:
        """システムの健全性チェック"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "namespaces": {},
            "overall_status": "healthy"
        }
        
        for namespace_name in self.namespaces.keys():
            try:
                config = self.get_config(namespace_name)
                results["namespaces"][namespace_name] = {
                    "status": "healthy",
                    "config_keys": list(config.keys()),
                    "sources_loaded": self._get_loaded_sources(namespace_name)
                }
            except Exception as e:
                results["namespaces"][namespace_name] = {
                    "status": "error",
                    "error": str(e)
                }
                results["overall_status"] = "unhealthy"
        
        return results
    
    def _get_loaded_sources(self, namespace: str) -> List[str]:
        """読み込まれたソースのリストを取得"""
        loaded_sources = []
        namespace_config = self.namespaces[namespace]
        
        for source in namespace_config.sources:
            if source.format == "env":
                loaded_sources.append("environment_variables")
            elif source.exists():
                loaded_sources.append(str(source.path))
        
        return loaded_sources

# グローバルインスタンス
integrated_config = IntegratedConfigSystem()

def get_config(namespace: str, force_reload: bool = False) -> Dict[str, Any]:
    """設定取得のショートカット"""
    return integrated_config.get_config(namespace, force_reload)

def migrate_configs():
    """設定移行のショートカット"""
    integrated_config.migrate_legacy_configs()

def health_check() -> Dict[str, Any]:
    """ヘルスチェックのショートカット"""
    return integrated_config.health_check()