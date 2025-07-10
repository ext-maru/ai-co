from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "契約書類アップロードシステム"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"

    # Database - SQLite使用（開発用）
    DATABASE_URL: str = "sqlite:///./upload_service.db"

    # Redis - エルダーズギルド共有インフラ使用
    REDIS_URL: str = "redis://host.docker.internal:8004"

    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # File upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".webp"]

    # Storage
    UPLOAD_PATH: str = "/app/uploads"

    class Config:
        env_file = ".env"


settings = Settings()
