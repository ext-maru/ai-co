from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # 基本設定
    app_name: str = "Upload Image Service"
    version: str = "1.0.0"
    debug: bool = True

    # データベース
    database_url: str = Field(
        default="sqlite:///./upload_service.db",
        env="DATABASE_URL"
    )

    # セキュリティ
    secret_key: str = Field(
        default="your-secret-key-here-change-this-in-production",
        env="SECRET_KEY"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # ファイルアップロード
    upload_dir: str = Field(default="./uploads", env="UPLOAD_DIR")
    max_file_size_mb: int = Field(default=100, env="MAX_FILE_SIZE_MB")
    allowed_extensions: set = {".pdf", ".jpg", ".jpeg", ".png", ".gif"}

    # Google Drive設定
    google_drive_enabled: bool = Field(default=False, env="GOOGLE_DRIVE_ENABLED")
    google_drive_credentials_path: Optional[str] = Field(default=None, env="GOOGLE_DRIVE_CREDENTIALS_PATH")
    google_drive_parent_folder_id: Optional[str] = Field(default=None, env="GOOGLE_DRIVE_PARENT_FOLDER_ID")
    google_drive_folder_name_format: str = Field(
        default="[{session_id}]_{submitter_name}",
        env="GOOGLE_DRIVE_FOLDER_NAME_FORMAT"
    )
    google_drive_auto_create_folders: bool = Field(default=True, env="GOOGLE_DRIVE_AUTO_CREATE_FOLDERS")
    google_drive_share_with_submitter: bool = Field(default=True, env="GOOGLE_DRIVE_SHARE_WITH_SUBMITTER")

    # CORS設定
    allowed_origins: list = Field(
        default=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
        env="ALLOWED_ORIGINS"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
