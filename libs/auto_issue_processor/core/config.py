#!/usr/bin/env python3
"""
Auto Issue Processor 統一設定管理
すべての設定を一元管理し、環境変数とYAMLファイルの両方をサポート
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import yaml
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class FeatureFlags:
    """機能フラグ設定"""
    pr_creation: bool = True
    error_recovery: bool = True
    parallel_processing: bool = False
    smart_merge: bool = False
    four_sages_integration: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureFlags":
        """辞書から作成"""
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


@dataclass
class GitHubConfig:
    """GitHub関連設定"""
    token: Optional[str] = None
    repo: Optional[str] = None
    owner: Optional[str] = None
    rate_limit_buffer: int = 100
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    def __post_init__(self):
        """環境変数から自動読み込み"""
        if not self.token:
            self.token = os.getenv("GITHUB_TOKEN")
        if not self.repo:
            repo_full = os.getenv("GITHUB_REPOSITORY", "ext-maru/ai-co")
            if "/" in repo_full:
                self.owner, self.repo = repo_full.split("/", 1)
            else:
                self.repo = repo_full


@dataclass
class LockConfig:
    """ロック機能設定"""
    backend: str = "file"  # file, redis, memory
    lock_dir: str = "./.issue_locks"
    default_ttl: int = 300  # 秒
    cleanup_interval: int = 60  # 秒
    redis_url: Optional[str] = None
    
    def __post_init__(self):
        """ディレクトリ作成"""
        if self.backend == "file":
            Path(self.lock_dir).mkdir(exist_ok=True)


@dataclass
class ProcessingConfig:
    """処理関連設定"""
    max_issues_per_run: int = 5
    processing_timeout: int = 300  # 秒
    priorities: list = field(default_factory=lambda: ["critical", "high", "medium", "low"])
    skip_labels: list = field(default_factory=lambda: ["wontfix", "duplicate", "invalid"])
    required_labels: list = field(default_factory=list)
    
    # 並列処理設定
    max_parallel_workers: int = 3
    parallel_batch_size: int = 10
    
    # テンプレート設定
    use_enhanced_templates: bool = False  # デフォルトで無効！
    template_dir: Optional[str] = None


@dataclass
class LoggingConfig:
    """ロギング設定"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = "logs/auto_issue_processor.log"
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5
    
    def setup_logging(self):
        """ロギングを設定"""
        logging.basicConfig(
            level=getattr(logging, self.level.upper()),
            format=self.format
        )
        
        if self.file:
            from logging.handlers import RotatingFileHandler
            handler = RotatingFileHandler(
                self.file,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count
            )
            handler.setFormatter(logging.Formatter(self.format))
            logging.getLogger().addHandler(handler)


@dataclass
class SchedulerConfig:
    """スケジューラー設定"""
    enabled: bool = True
    interval_minutes: int = 10
    start_time: Optional[str] = None  # HH:MM形式
    timezone: str = "Asia/Tokyo"
    jitter: int = 0  # 秒単位のランダム遅延


@dataclass
class ProcessorConfig:
    """Auto Issue Processor統一設定"""
    
    # 基本設定
    enabled: bool = True
    dry_run: bool = False
    
    # サブ設定
    features: FeatureFlags = field(default_factory=FeatureFlags)
    github: GitHubConfig = field(default_factory=GitHubConfig)
    lock: LockConfig = field(default_factory=LockConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    
    @classmethod
    def from_file(cls, path: str) -> "ProcessorConfig":
        """YAMLファイルから設定を読み込む"""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        config = cls()
        
        # 各セクションを更新
        if "features" in data:
            config.features = FeatureFlags.from_dict(data["features"])
        if "github" in data:
            config.github = GitHubConfig(**data["github"])
        if "lock" in data:
            config.lock = LockConfig(**data["lock"])
        if "processing" in data:
            config.processing = ProcessingConfig(**data["processing"])
        if "logging" in data:
            config.logging = LoggingConfig(**data["logging"])
        if "scheduler" in data:
            config.scheduler = SchedulerConfig(**data["scheduler"])
        
        # トップレベル設定
        if "enabled" in data:
            config.enabled = data["enabled"]
        if "dry_run" in data:
            config.dry_run = data["dry_run"]
        
        return config
    
    @classmethod
    def from_env(cls) -> "ProcessorConfig":
        """環境変数から設定を読み込む"""
        config = cls()
        
        # 環境変数のプレフィックス
        prefix = "AUTO_ISSUE_PROCESSOR_"
        
        # 基本設定
        if os.getenv(f"{prefix}ENABLED"):
            config.enabled = os.getenv(f"{prefix}ENABLED").lower() == "true"
        if os.getenv(f"{prefix}DRY_RUN"):
            config.dry_run = os.getenv(f"{prefix}DRY_RUN").lower() == "true"
        
        # 機能フラグ
        for feature in ["pr_creation", "error_recovery", "parallel_processing", "smart_merge", "four_sages_integration"]:
            env_key = f"{prefix}FEATURE_{feature.upper()}"
            if os.getenv(env_key):
                setattr(config.features, feature, os.getenv(env_key).lower() == "true")
        
        # 処理設定
        if os.getenv(f"{prefix}MAX_ISSUES_PER_RUN"):
            config.processing.max_issues_per_run = int(os.getenv(f"{prefix}MAX_ISSUES_PER_RUN"))
        if os.getenv(f"{prefix}USE_ENHANCED_TEMPLATES"):
            config.processing.use_enhanced_templates = os.getenv(f"{prefix}USE_ENHANCED_TEMPLATES").lower() == "true"
        
        # スケジューラー設定
        if os.getenv(f"{prefix}SCHEDULER_INTERVAL"):
            config.scheduler.interval_minutes = int(os.getenv(f"{prefix}SCHEDULER_INTERVAL"))
        
        logger.info("Configuration loaded from environment variables")
        return config
    
    @classmethod
    def load(cls, config_file: Optional[str] = None) -> "ProcessorConfig":
        """設定をロード（ファイル優先、なければ環境変数）"""
        if config_file and os.path.exists(config_file):
            logger.info(f"Loading configuration from file: {config_file}")
            config = cls.from_file(config_file)
        else:
            logger.info("Loading configuration from environment variables")
            config = cls.from_env()
        
        # ロギング設定を適用
        config.logging.setup_logging()
        
        return config
    
    def validate(self) -> bool:
        """設定の妥当性を検証"""
        errors = []
        
        # GitHub設定の検証
        if self.features.pr_creation and not self.github.token:
            errors.append("GitHub token is required when PR creation is enabled")
        
        # ロック設定の検証
        if self.lock.backend == "redis" and not self.lock.redis_url:
            errors.append("Redis URL is required when using Redis lock backend")
        
        # 処理設定の検証
        if self.processing.max_issues_per_run < 1:
            errors.append("max_issues_per_run must be at least 1")
        
        if self.processing.max_parallel_workers < 1:
            errors.append("max_parallel_workers must be at least 1")
        
        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式で出力"""
        return {
            "enabled": self.enabled,
            "dry_run": self.dry_run,
            "features": {
                "pr_creation": self.features.pr_creation,
                "error_recovery": self.features.error_recovery,
                "parallel_processing": self.features.parallel_processing,
                "smart_merge": self.features.smart_merge,
                "four_sages_integration": self.features.four_sages_integration,
            },
            "github": {
                "repo": self.github.repo,
                "owner": self.github.owner,
                "rate_limit_buffer": self.github.rate_limit_buffer,
            },
            "lock": {
                "backend": self.lock.backend,
                "lock_dir": self.lock.lock_dir,
                "default_ttl": self.lock.default_ttl,
            },
            "processing": {
                "max_issues_per_run": self.processing.max_issues_per_run,
                "processing_timeout": self.processing.processing_timeout,
                "use_enhanced_templates": self.processing.use_enhanced_templates,
            },
            "scheduler": {
                "enabled": self.scheduler.enabled,
                "interval_minutes": self.scheduler.interval_minutes,
            }
        }


# デフォルト設定のシングルトン
_default_config: Optional[ProcessorConfig] = None


def get_default_config(reload: bool = False) -> ProcessorConfig:
    """デフォルト設定を取得"""
    global _default_config
    
    if _default_config is None or reload:
        config_file = os.getenv("AUTO_ISSUE_PROCESSOR_CONFIG_FILE")
        _default_config = ProcessorConfig.load(config_file)
    
    return _default_config


if __name__ == "__main__":
    # 設定のテスト
    config = get_default_config()
    print("Current configuration:")
    print(yaml.dump(config.to_dict(), default_flow_style=False))