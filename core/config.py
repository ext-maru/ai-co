#!/usr/bin/env python3
"""
EldersGuildConfig - Elder's Guild 設定管理

環境変数と設定ファイルを統合した設定管理システム。
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .common_utils import get_project_paths, load_json_file, safe_get


@dataclass
class RabbitMQConfig:
    """RabbitMQ設定"""

    host: str = os.getenv("RABBITMQ_HOST", "localhost")
    port: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    username: str = os.getenv("RABBITMQ_USER", "guest")
    password: str = os.getenv("RABBITMQ_PASSWORD", "guest")
    heartbeat: int = 600
    blocked_connection_timeout: int = 300

    @classmethod
    def from_env(cls) -> "RabbitMQConfig":
        """環境変数から設定を読み込み"""
        return cls(
            host=os.getenv("RABBITMQ_HOST", "localhost"),
            port=int(os.getenv("RABBITMQ_PORT", "5672")),
            username=os.getenv("RABBITMQ_USER", "guest"),
            password=os.getenv("RABBITMQ_PASSWORD", "guest"),
            heartbeat=int(os.getenv("RABBITMQ_HEARTBEAT", "600")),
            blocked_connection_timeout=int(os.getenv("RABBITMQ_TIMEOUT", "300")),
        )


@dataclass
class SlackConfig:
    """Slack設定"""

    webhook_url: str = ""
    channel: str = "#general"
    username: str = "エルダーズギルドBot"
    enabled: bool = True

    # Slack Polling設定
    bot_token: str = ""
    polling_channel_id: str = ""
    polling_interval: int = 20
    polling_enabled: bool = False
    require_mention: bool = True

    # Slack Monitor設定
    monitor_enabled: bool = False
    error_channel: str = "#elders-guild-errors"
    notification_channel: str = "#elders-guild-notifications"
    monitor_interval: int = 10
    error_threshold: int = 3
    error_surge_threshold: int = 20

    # 通知設定
    mention_on_critical: bool = True
    mention_users: str = "@channel"
    rate_limit_max: int = 10
    rate_limit_cooldown: int = 60

    # キーワード設定
    critical_keywords: List[str] = field(
        default_factory=lambda: ["CRITICAL", "FATAL", "ERROR", "Exception", "Traceback"]
    )

    @classmethod
    def from_file(cls, config_path: Path) -> "SlackConfig":
        """設定ファイルから読み込み"""
        config = {}

        if config_path.exists():
            with open(config_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        config[key.strip()] = value.strip().strip('"')

        # slack_config.jsonも読み込み
        json_config = {}
        json_path = config_path.parent / "slack_config.json"
        if json_path.exists():
            json_config = load_json_file(json_path) or {}

        return cls(
            webhook_url=config.get("SLACK_WEBHOOK_URL", ""),
            channel=config.get("SLACK_CHANNEL", "#general"),
            username=config.get("SLACK_USERNAME", "エルダーズギルドBot"),
            enabled=config.get("ENABLE_SLACK", "true").lower() == "true",
            # Bot設定
            bot_token=config.get("SLACK_BOT_TOKEN", json_config.get("bot_token", "")),
            polling_channel_id=config.get(
                "SLACK_POLLING_CHANNEL_ID", json_config.get("polling_channel_id", "")
            ),
            polling_interval=int(
                config.get(
                    "SLACK_POLLING_INTERVAL", json_config.get("polling_interval", 20)
                )
            ),
            polling_enabled=config.get("SLACK_POLLING_ENABLED", "false").lower()
            == "true",
            require_mention=config.get("SLACK_REQUIRE_MENTION", "true").lower()
            == "true",
            # Monitor設定
            monitor_enabled=config.get("SLACK_MONITOR_ENABLED", "false").lower()
            == "true",
            error_channel=config.get(
                "SLACK_ERROR_CHANNEL",
                json_config.get("error_channel", "#elders-guild-errors"),
            ),
            notification_channel=config.get(
                "SLACK_NOTIFICATION_CHANNEL",
                json_config.get("notification_channel", "#elders-guild-notifications"),
            ),
            monitor_interval=int(
                config.get(
                    "SLACK_MONITOR_INTERVAL", json_config.get("monitor_interval", 10)
                )
            ),
            error_threshold=int(
                config.get(
                    "SLACK_ERROR_THRESHOLD", json_config.get("error_threshold", 3)
                )
            ),
            error_surge_threshold=int(
                config.get(
                    "SLACK_ERROR_SURGE_THRESHOLD",
                    json_config.get("error_surge_threshold", 20),
                )
            ),
            # 通知設定
            mention_on_critical=config.get("SLACK_MENTION_ON_CRITICAL", "true").lower()
            == "true",
            mention_users=config.get(
                "SLACK_MENTION_USERS",
                json_config.get("notification_settings", {}).get(
                    "mention_users", ["@channel"]
                )[0],
            ),
            rate_limit_max=int(
                config.get(
                    "SLACK_RATE_LIMIT_MAX",
                    json_config.get("notification_settings", {})
                    .get("rate_limit", {})
                    .get("max_messages_per_minute", 10),
                )
            ),
            rate_limit_cooldown=int(
                config.get(
                    "SLACK_RATE_LIMIT_COOLDOWN",
                    json_config.get("notification_settings", {})
                    .get("rate_limit", {})
                    .get("cooldown_seconds", 60),
                )
            ),
            # キーワード
            critical_keywords=json_config.get(
                "critical_keywords",
                ["CRITICAL", "FATAL", "ERROR", "Exception", "Traceback"],
            ),
        )


@dataclass
class WorkerConfig:
    """ワーカー設定"""

    default_model: str = "claude-sonnet-4-20250514"
    timeout: int = 300
    max_retries: int = 3
    prefetch_count: int = 1
    scaling_enabled: bool = True
    min_workers: int = 1
    max_workers: int = 5
    scale_check_interval: int = 30
    health_check_interval: int = 60


@dataclass
class StorageConfig:
    """ストレージ設定"""

    max_file_size_mb: int = 100
    allowed_extensions: List[str] = field(
        default_factory=lambda: [
            ".py",
            ".js",
            ".html",
            ".css",
            ".json",
            ".yaml",
            ".yml",
            ".sh",
            ".bash",
            ".conf",
            ".ini",
            ".md",
            ".txt",
        ]
    )
    retention_days: int = 30
    auto_cleanup: bool = True


@dataclass
class LanguageConfig:
    """言語設定"""

    default_language: str = "ja"
    supported_languages: List[str] = field(default_factory=lambda: ["ja", "en"])
    date_format: str = "%Y年%m月%d日"
    time_format: str = "%H時%M分%S秒"
    timezone: str = "Asia/Tokyo"
    encoding: str = "utf-8"


@dataclass
class GitConfig:
    """Git設定"""

    auto_commit: bool = True
    auto_push: bool = True
    remote: str = "origin"
    branch: str = "master"
    commit_prefix: str = "🤖 AI自動生成:"


class EldersGuildConfig:
    """エルダーズギルド統合設定管理"""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Args:
            config_dir: 設定ディレクトリ（未指定時はデフォルト）
        """
        self.paths = get_project_paths()
        self.config_dir = config_dir or self.paths["config"]

        # 各設定の初期化
        self.rabbitmq = RabbitMQConfig.from_env()
        self.slack = SlackConfig.from_file(self.config_dir / "slack.conf")
        self.worker = WorkerConfig()
        self.storage = StorageConfig()
        self.git = GitConfig()
        self.language = LanguageConfig()

        # カスタム設定
        self._custom_configs: Dict[str, Any] = {}

        # 設定ファイルからの読み込み
        self._load_config_files()

    def _load_config_files(self):
        """設定ファイルの読み込み"""
        # worker.json
        worker_config = load_json_file(self.config_dir / "worker.json")
        if worker_config:
            self._update_dataclass(self.worker, worker_config)

        # storage.json
        storage_config = load_json_file(self.config_dir / "storage.json")
        if storage_config:
            self._update_dataclass(self.storage, storage_config)

        # git.json
        git_config = load_json_file(self.config_dir / "git.json")
        if git_config:
            self._update_dataclass(self.git, git_config)

        # language.json
        language_config = load_json_file(self.config_dir / "language.json")
        if language_config:
            self._update_dataclass(self.language, language_config)

        # custom.json（カスタム設定）
        custom_config = load_json_file(self.config_dir / "custom.json")
        if custom_config:
            self._custom_configs.update(custom_config)

    def _update_dataclass(self, obj: Any, updates: Dict[str, Any]):
        """データクラスの更新"""
        for key, value in updates.items():
            if hasattr(obj, key):
                setattr(obj, key, value)

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        設定値の取得（ドット記法対応）

        Args:
            key_path: キーパス（例: "worker.timeout"）
            default: デフォルト値

        Returns:
            設定値
        """
        # 組み込み設定の確認
        parts = key_path.split(".")
        if len(parts) >= 2:
            section = parts[0]
            attr = ".".join(parts[1:])

            if hasattr(self, section):
                obj = getattr(self, section)
                return safe_get(obj.__dict__, attr, default)

        # カスタム設定の確認
        return safe_get(self._custom_configs, key_path, default)

    def set(self, key_path: str, value: Any):
        """
        設定値の設定（実行時のみ、永続化なし）

        Args:
            key_path: キーパス
            value: 設定値
        """
        parts = key_path.split(".")

        if len(parts) >= 2:
            section = parts[0]
            attr = parts[1]

            if hasattr(self, section) and len(parts) == 2:
                obj = getattr(self, section)
                if hasattr(obj, attr):
                    setattr(obj, attr, value)
                    return

        # カスタム設定として保存
        self._set_nested(self._custom_configs, key_path, value)

    def _set_nested(self, dictionary: Dict[str, Any], key_path: str, value: Any):
        """ネストされた辞書に値を設定"""
        keys = key_path.split(".")

        for key in keys[:-1]:
            if key not in dictionary:
                dictionary[key] = {}
            dictionary = dictionary[key]

        dictionary[keys[-1]] = value

    def get_all(self) -> Dict[str, Any]:
        """全設定を辞書として取得"""
        return {
            "rabbitmq": self.rabbitmq.__dict__,
            "slack": self.slack.__dict__,
            "worker": self.worker.__dict__,
            "storage": self.storage.__dict__,
            "git": self.git.__dict__,
            "language": self.language.__dict__,
            "custom": self._custom_configs,
            "paths": {k: str(v) for k, v in self.paths.items()},
        }

    def validate(self) -> List[str]:
        """
        設定の検証

        Returns:
            エラーメッセージのリスト
        """
        errors = []

        # Slack設定の検証
        if self.slack.enabled and not self.slack.webhook_url:
            errors.append("Slackが有効ですがWebhook URLが設定されていません")

        # ワーカー設定の検証
        if self.worker.min_workers > self.worker.max_workers:
            errors.append("min_workers は max_workers 以下である必要があります")

        if self.worker.timeout <= 0:
            errors.append("timeout は正の値である必要があります")

        # ストレージ設定の検証
        if self.storage.max_file_size_mb <= 0:
            errors.append("max_file_size_mb は正の値である必要があります")

        return errors

    def save_custom_config(self) -> bool:
        """カスタム設定の保存"""
        custom_path = self.config_dir / "custom.json"

        try:
            with open(custom_path, "w", encoding="utf-8") as f:
                json.dump(self._custom_configs, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def __repr__(self) -> str:
        """設定の文字列表現"""
        return f"EldersGuildConfig(rabbitmq={self.rabbitmq.host}, slack_enabled={self.slack.enabled}, workers={self.worker.min_workers}-{self.worker.max_workers})"


# グローバル設定インスタンス（シングルトン）
_global_config: Optional[EldersGuildConfig] = None


def get_config() -> EldersGuildConfig:
    """グローバル設定インスタンスの取得"""
    global _global_config

    if _global_config is None:
        _global_config = EldersGuildConfig()

    return _global_config


def reload_config() -> EldersGuildConfig:
    """設定の再読み込み"""
    global _global_config
    _global_config = EldersGuildConfig()
    return _global_config


if __name__ == "__main__":
    # テスト実行
    config = get_config()

    print("エルダーズギルド 設定:")
    print(f"  RabbitMQ: {config.rabbitmq.host}:{config.rabbitmq.port}")
    print(f"  Slack: {'有効' if config.slack.enabled else '無効'}")
    print(f"  デフォルトモデル: {config.worker.default_model}")
    print(f"  ワーカー数: {config.worker.min_workers}-{config.worker.max_workers}")

    # 検証
    errors = config.validate()
    if errors:
        print("\n設定エラー:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✅ 設定検証: OK")
