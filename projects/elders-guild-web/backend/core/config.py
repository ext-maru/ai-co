import os
from typing import List
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    WORKERS: int = 1

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Elders Guild Web API"
    VERSION: str = "1.0.0"

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", "8000"))

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,https://ai-company-web.vercel.app"

    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/ai_company_db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "your-super-secret-key-here-change-in-production"
    JWT_SECRET: str = "your-jwt-secret-key-here-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30

    # Elder Council Configuration
    ELDER_COUNCIL_ENABLED: bool = True
    MAX_SAGES: int = 4
    COVERAGE_TARGET: float = 66.7

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 900  # 15 minutes in seconds

    # WebSocket Configuration
    WS_MAX_CONNECTIONS: int = 1000
    WS_HEARTBEAT_INTERVAL: int = 30

    # Monitoring Configuration
    SENTRY_DSN: Optional[str] = None
    ENABLE_MONITORING: bool = True
    ENABLE_METRICS: bool = True

    # External API Configuration
    FLASK_API_URL: str = "http://localhost:5000"
    MIGRATION_MODE: str = "gradual"  # gradual, immediate, proxy

    # Production Security Headers
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
