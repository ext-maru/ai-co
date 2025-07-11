#!/usr/bin/env python3
"""
Environment Configuration Management
エルダーズギルド設定管理システム
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """データベース設定"""
    host: str = "localhost"
    port: int = 5432
    database: str = "elders_guild"
    username: str = "postgres"
    password: str = ""
    
    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

@dataclass
class MessageQueueConfig:
    """メッセージキュー設定"""
    host: str = "localhost"
    port: int = 5672
    username: str = "guest"
    password: str = "guest"
    virtual_host: str = "/"
    
    @property
    def connection_string(self) -> str:
        return f"amqp://{self.username}:{self.password}@{self.host}:{self.port}/{self.virtual_host}"

@dataclass
class SecurityConfig:
    """セキュリティ設定"""
    jwt_secret: str = "elders-guild-secret-key"
    encryption_key: Optional[str] = None
    
    def __post_init__(self):
        if not self.encryption_key:
            # Fernetキーを生成（本番では環境変数から取得）
            from cryptography.fernet import Fernet
            self.encryption_key = Fernet.generate_key().decode()

@dataclass
class EldersGuildConfig:
    """エルダーズギルド総合設定"""
    database: DatabaseConfig
    message_queue: MessageQueueConfig
    security: SecurityConfig
    debug: bool = True
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> "EldersGuildConfig":
        """環境変数から設定を読み込み"""
        return cls(
            database=DatabaseConfig(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", "5432")),
                database=os.getenv("POSTGRES_DB", "elders_guild"),
                username=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "")
            ),
            message_queue=MessageQueueConfig(
                host=os.getenv("RABBITMQ_HOST", "localhost"),
                port=int(os.getenv("RABBITMQ_PORT", "5672")),
                username=os.getenv("RABBITMQ_USER", "guest"),
                password=os.getenv("RABBITMQ_PASSWORD", "guest"),
                virtual_host=os.getenv("RABBITMQ_VHOST", "/")
            ),
            security=SecurityConfig(
                jwt_secret=os.getenv("JWT_SECRET", "elders-guild-secret-key"),
                encryption_key=os.getenv("ENCRYPTION_KEY")
            ),
            debug=os.getenv("DEBUG", "true").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )

# グローバル設定インスタンス
config = EldersGuildConfig.from_env()

def get_config() -> EldersGuildConfig:
    """設定インスタンスを取得"""
    return config

def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

# 初期化
setup_logging()

if __name__ == "__main__":
    print("🔧 Elders Guild Configuration")
    print(f"Database: {config.database.connection_string}")
    print(f"Message Queue: {config.message_queue.connection_string}")
    print(f"Debug Mode: {config.debug}")
    print(f"Log Level: {config.log_level}")