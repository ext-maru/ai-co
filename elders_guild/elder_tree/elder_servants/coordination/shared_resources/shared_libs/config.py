"""
🏛️ Elders Guild Configuration Management
環境変数とデフォルト値の管理
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load .env file if exists
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

class Config:
    """中央設定管理クラス"""
    
    # === System Paths ===
    ELDERS_GUILD_HOME: str = os.getenv('ELDERS_GUILD_HOME', str(Path(__file__).parent.parent.absolute()))
    PROJECT_ROOT: str = os.getenv('PROJECT_ROOT', ELDERS_GUILD_HOME)
    
    # === Database Configuration ===
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'postgresql://aicompany:password@localhost/elder_tree')
    SQLITE_URL: str = os.getenv('SQLITE_URL', 'sqlite+aiosqlite:///elder_tree.db')
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # === Service Ports ===
    API_PORT: int = int(os.getenv('API_PORT', '8000'))
    WEB_PORT: int = int(os.getenv('WEB_PORT', '8080'))
    PROMETHEUS_PORT: int = int(os.getenv('PROMETHEUS_PORT', '9090'))
    CONSUL_PORT: int = int(os.getenv('CONSUL_PORT', '8500'))
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', '6379'))
    POSTGRES_EXPORTER_PORT: int = int(os.getenv('POSTGRES_EXPORTER_PORT', '9187'))
    REDIS_EXPORTER_PORT: int = int(os.getenv('REDIS_EXPORTER_PORT', '9121'))
    
    # === Service URLs ===
    API_BASE_URL: str = os.getenv('API_BASE_URL', f'http://localhost:{API_PORT}')
    PROMETHEUS_URL: str = os.getenv('PROMETHEUS_URL', f'http://localhost:{PROMETHEUS_PORT}')
    CONSUL_URL: str = os.getenv('CONSUL_URL', f'http://localhost:{CONSUL_PORT}')
    
    # === A2A Configuration ===
    A2A_KNOWLEDGE_SAGE_PORT: int = int(os.getenv('A2A_KNOWLEDGE_SAGE_PORT', '8806'))
    A2A_TASK_SAGE_PORT: int = int(os.getenv('A2A_TASK_SAGE_PORT', '8809'))
    A2A_INCIDENT_SAGE_PORT: int = int(os.getenv('A2A_INCIDENT_SAGE_PORT', '8807'))
    A2A_RAG_SAGE_PORT: int = int(os.getenv('A2A_RAG_SAGE_PORT', '8808'))
    
    # === Security ===
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', 'password')
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'your-secret-key-here')
    API_TOKEN: str = os.getenv('API_TOKEN', 'your-api-token-here')
    
    # === Environment ===
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')

    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # === Integration Services ===
    CONTINUE_DEV_PORT: int = int(os.getenv('CONTINUE_DEV_PORT', '3000'))
    AIDER_PORT: int = int(os.getenv('AIDER_PORT', '8081'))
    
    # === Monitoring ===
    OTEL_EXPORTER_OTLP_ENDPOINT: str = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4317')
    METRICS_ENABLED: bool = os.getenv('METRICS_ENABLED', 'true').lower() == 'true'
    TRACING_ENABLED: bool = os.getenv('TRACING_ENABLED', 'true').lower() == 'true'
    
    @classmethod
    def get_db_path(cls, db_name: str) -> Path:
        """データベースファイルのパスを取得"""
        return Path(cls.PROJECT_ROOT) / 'data' / db_name
    
    @classmethod
    def get_service_url(cls, service: str, port: Optional[int] = None) -> str:
        """サービスURLを動的に生成"""
        if port is None:
            port = getattr(cls, f'{service.upper()}_PORT', 8000)
        return f"http://localhost:{port}"
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """設定を辞書として取得"""
        return {
            key: getattr(cls, key)
            for key in dir(cls)
            if not key.startswith('_') and key.isupper()
        }

# シングルトンインスタンス
config = Config()