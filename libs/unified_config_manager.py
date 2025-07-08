#!/usr/bin/env python3
"""
🛡️ Unified Configuration Manager
統一設定管理システム - 設定ファイル問題の根本解決

全ての設定を一元管理し、自動検証・修復・フォールバックを提供
"""

import json
import os
import sys
import hashlib
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@dataclass
class ConfigSource:
    """設定ソースの定義"""
    name: str
    path: Path
    format: str  # 'json', 'env', 'yaml'
    priority: int  # 低い数値が高優先度
    required: bool = True
    
@dataclass 
class ConfigValidation:
    """設定検証ルール"""
    key: str
    required: bool = True
    type_check: Optional[type] = None
    pattern: Optional[str] = None
    default: Optional[Any] = None

class UnifiedConfigManager:
    """統一設定管理システム"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.config_dir = self.project_root / "config"
        self.backup_dir = self.config_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 設定キャッシュ
        self._config_cache = {}
        self._config_hash = {}
        
        # 設定ソースの優先順位定義
        self.sources = {
            'slack': [
                ConfigSource("env", self.project_root / ".env", "env", 1),
                ConfigSource("json", self.config_dir / "slack_config.json", "json", 2),
                ConfigSource("conf", self.config_dir / "slack.conf", "conf", 3),
                ConfigSource("pm_json", self.config_dir / "slack_pm_config.json", "json", 4),
            ],
            'database': [
                ConfigSource("env", self.project_root / ".env", "env", 1),
                ConfigSource("conf", self.config_dir / "database.conf", "conf", 2),
            ],
            'worker': [
                ConfigSource("json", self.config_dir / "worker_config.json", "json", 1),
                ConfigSource("yaml", self.config_dir / "async_workers_config.yaml", "yaml", 2),
            ]
        }
        
        # 検証ルール
        self.validation_rules = {
            'slack': [
                ConfigValidation("bot_token", required=True, pattern=r"^xoxb-\d+-\d+-\w+$"),
                ConfigValidation("channel_id", required=True, pattern=r"^C[A-Z0-9]+$"),
                ConfigValidation("polling_interval", required=False, type_check=int, default=20),
                ConfigValidation("webhook_url", required=False, pattern=r"^https://hooks\.slack\.com/"),
            ],
            'database': [
                ConfigValidation("host", required=True, default="localhost"),
                ConfigValidation("port", required=False, type_check=int, default=5432),
                ConfigValidation("database", required=True),
            ],
            'worker': [
                ConfigValidation("max_workers", required=False, type_check=int, default=4),
                ConfigValidation("queue_size", required=False, type_check=int, default=100),
            ]
        }
        
    def get_config(self, namespace: str) -> Dict[str, Any]:
        """設定を取得（自動フォールバック付き）"""
        if namespace in self._config_cache:
            return self._config_cache[namespace]
            
        config = {}
        sources = self.sources.get(namespace, [])
        
        # 優先順位順に設定を読み込み、マージ
        for source in sorted(sources, key=lambda x: x.priority):
            try:
                source_config = self._load_from_source(source)
                config = self._merge_config(config, source_config)
                logger.debug(f"Loaded config from {source.name}: {source.path}")
            except Exception as e:
                if source.required:
                    logger.warning(f"Failed to load required source {source.name}: {e}")
                else:
                    logger.debug(f"Optional source {source.name} not available: {e}")
                    
        # 検証とデフォルト値適用
        config = self._validate_and_fill_defaults(namespace, config)
        
        # キャッシュに保存
        self._config_cache[namespace] = config
        self._config_hash[namespace] = self._hash_config(config)
        
        return config
        
    def _load_from_source(self, source: ConfigSource) -> Dict[str, Any]:
        """設定ソースから読み込み"""
        if not source.path.exists():
            raise FileNotFoundError(f"Config file not found: {source.path}")
            
        if source.format == "json":
            with open(source.path) as f:
                return json.load(f)
        elif source.format == "env":
            return self._load_env_file(source.path)
        elif source.format == "yaml":
            import yaml
            with open(source.path) as f:
                return yaml.safe_load(f)
        elif source.format == "conf":
            return self._load_conf_file(source.path)
        else:
            raise ValueError(f"Unsupported format: {source.format}")
            
    def _load_env_file(self, path: Path) -> Dict[str, Any]:
        """環境変数ファイルを読み込み"""
        config = {}
        if not path.exists():
            return config
            
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        # SLACK_BOT_TOKEN -> bot_token に変換
                        normalized_key = self._normalize_env_key(key.strip())
                        config[normalized_key] = value.strip().strip('"\'')
        return config
        
    def _load_conf_file(self, path: Path) -> Dict[str, Any]:
        """.confファイルを読み込み"""
        # 簡単なkey=value形式をサポート
        return self._load_env_file(path)
        
    def _normalize_env_key(self, env_key: str) -> str:
        """環境変数キーを正規化"""
        mapping = {
            'SLACK_BOT_TOKEN': 'bot_token',
            'SLACK_CHANNEL_ID': 'channel_id',
            'SLACK_CHANNEL_IDS': 'channel_id',
            'SLACK_POLLING_CHANNEL_ID': 'channel_id',
            'SLACK_WEBHOOK_URL': 'webhook_url',
            'SLACK_POLLING_INTERVAL': 'polling_interval',
            'DATABASE_HOST': 'host',
            'DATABASE_PORT': 'port',
            'DATABASE_NAME': 'database',
        }
        return mapping.get(env_key, env_key.lower())
        
    def _merge_config(self, base: Dict, override: Dict) -> Dict:
        """設定をマージ（override優先）"""
        result = base.copy()
        for key, value in override.items():
            if value:  # 空文字やNoneは無視
                result[key] = value
        return result
        
    def _validate_and_fill_defaults(self, namespace: str, config: Dict) -> Dict:
        """設定を検証し、デフォルト値を適用"""
        rules = self.validation_rules.get(namespace, [])
        validated = config.copy()
        
        for rule in rules:
            if rule.key not in validated:
                if rule.required and rule.default is None:
                    raise ValueError(f"Required config key missing: {rule.key}")
                elif rule.default is not None:
                    validated[rule.key] = rule.default
                    
            if rule.key in validated:
                value = validated[rule.key]
                
                # 型チェック
                if rule.type_check and not isinstance(value, rule.type_check):
                    try:
                        validated[rule.key] = rule.type_check(value)
                    except (ValueError, TypeError):
                        raise ValueError(f"Invalid type for {rule.key}: expected {rule.type_check.__name__}")
                        
                # パターンチェック
                if rule.pattern and isinstance(value, str):
                    import re
                    if not re.match(rule.pattern, value):
                        raise ValueError(f"Invalid format for {rule.key}: {value}")
                        
        return validated
        
    def _hash_config(self, config: Dict) -> str:
        """設定のハッシュ値を計算"""
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()
        
    @contextmanager
    def atomic_config_update(self, namespace: str):
        """アトミックな設定更新"""
        primary_source = self._get_primary_source(namespace)
        if not primary_source:
            raise ValueError(f"No primary source defined for namespace: {namespace}")
            
        # バックアップ作成
        backup_path = self._create_backup(primary_source.path)
        
        try:
            yield primary_source
            # 更新後の検証
            self.invalidate_cache(namespace)
            self.get_config(namespace)  # 検証を兼ねる
            logger.info(f"Config updated successfully: {primary_source.path}")
        except Exception as e:
            # 失敗時はバックアップから復元
            if backup_path.exists():
                shutil.copy2(backup_path, primary_source.path)
                logger.error(f"Config update failed, restored from backup: {e}")
            raise
            
    def _get_primary_source(self, namespace: str) -> Optional[ConfigSource]:
        """プライマリ設定ソースを取得"""
        sources = self.sources.get(namespace, [])
        if not sources:
            return None
        return min(sources, key=lambda x: x.priority)
        
    def _create_backup(self, config_path: Path) -> Path:
        """設定ファイルのバックアップを作成"""
        if not config_path.exists():
            return Path()
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{config_path.name}.{timestamp}.backup"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(config_path, backup_path)
        
        # 古いバックアップを削除（最新5つを保持）
        self._cleanup_old_backups(config_path.name)
        
        return backup_path
        
    def _cleanup_old_backups(self, config_name: str, keep: int = 5):
        """古いバックアップファイルを削除"""
        pattern = f"{config_name}.*.backup"
        backups = sorted(self.backup_dir.glob(pattern), key=lambda x: x.stat().st_mtime, reverse=True)
        
        for backup in backups[keep:]:
            backup.unlink()
            logger.debug(f"Removed old backup: {backup}")
            
    def invalidate_cache(self, namespace: str = None):
        """キャッシュを無効化"""
        if namespace:
            self._config_cache.pop(namespace, None)
            self._config_hash.pop(namespace, None)
        else:
            self._config_cache.clear()
            self._config_hash.clear()
            
    def health_check(self) -> Dict[str, Any]:
        """設定の健全性チェック"""
        results = {}
        
        for namespace in self.sources.keys():
            try:
                config = self.get_config(namespace)
                results[namespace] = {
                    'status': 'healthy',
                    'config_keys': list(config.keys()),
                    'sources_found': self._get_available_sources(namespace)
                }
            except Exception as e:
                results[namespace] = {
                    'status': 'error',
                    'error': str(e),
                    'sources_found': self._get_available_sources(namespace)
                }
                
        return results
        
    def _get_available_sources(self, namespace: str) -> List[str]:
        """利用可能なソースを取得"""
        sources = self.sources.get(namespace, [])
        available = []
        
        for source in sources:
            if source.path.exists():
                available.append(f"{source.name}:{source.path}")
                
        return available
        
    def auto_repair(self, namespace: str) -> bool:
        """設定の自動修復"""
        try:
            # まず現在の設定を取得してみる
            config = self.get_config(namespace)
            return True
        except Exception as e:
            logger.warning(f"Config error detected for {namespace}: {e}")
            
            # バックアップから復元を試行
            primary_source = self._get_primary_source(namespace)
            if primary_source and not primary_source.path.exists():
                backup_restored = self._restore_from_backup(primary_source.path)
                if backup_restored:
                    self.invalidate_cache(namespace)
                    try:
                        self.get_config(namespace)
                        logger.info(f"Successfully restored {namespace} config from backup")
                        return True
                    except Exception:
                        pass
                        
            # 他のソースから再構築を試行
            return self._rebuild_config(namespace)
            
    def _restore_from_backup(self, config_path: Path) -> bool:
        """バックアップから復元"""
        pattern = f"{config_path.name}.*.backup"
        backups = sorted(self.backup_dir.glob(pattern), key=lambda x: x.stat().st_mtime, reverse=True)
        
        for backup in backups:
            try:
                shutil.copy2(backup, config_path)
                logger.info(f"Restored config from backup: {backup}")
                return True
            except Exception as e:
                logger.warning(f"Failed to restore from backup {backup}: {e}")
                
        return False
        
    def _rebuild_config(self, namespace: str) -> bool:
        """他のソースから設定を再構築"""
        try:
            # 利用可能なソースから設定を収集
            config = {}
            sources = self.sources.get(namespace, [])
            
            for source in sorted(sources, key=lambda x: x.priority):
                try:
                    source_config = self._load_from_source(source)
                    config = self._merge_config(config, source_config)
                except Exception:
                    continue
                    
            if not config:
                return False
                
            # プライマリソースに書き戻し
            primary_source = self._get_primary_source(namespace)
            if primary_source and primary_source.format == "json":
                with open(primary_source.path, 'w') as f:
                    json.dump(config, f, indent=2)
                    
                self.invalidate_cache(namespace)
                logger.info(f"Rebuilt config for {namespace}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to rebuild config for {namespace}: {e}")
            
        return False

# グローバルインスタンス
config_manager = UnifiedConfigManager()

def get_config(namespace: str) -> Dict[str, Any]:
    """設定取得のショートカット"""
    return config_manager.get_config(namespace)

def health_check() -> Dict[str, Any]:
    """健全性チェックのショートカット"""
    return config_manager.health_check()

def auto_repair_all() -> Dict[str, bool]:
    """全設定の自動修復"""
    results = {}
    for namespace in config_manager.sources.keys():
        results[namespace] = config_manager.auto_repair(namespace)
    return results