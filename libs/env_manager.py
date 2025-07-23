#!/usr/bin/env python3
"""
環境変数統一管理システム
Elders Guild Environment Manager

全プロジェクトで使用する環境変数を一元管理
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class EnvManager:
    """環境変数統一管理クラス"""
    
    # === Core Settings ===
    @staticmethod
    def get_project_root() -> Path:
        """プロジェクトルートパスを取得"""
        return Path(os.getenv("PROJECT_ROOT", "/home/aicompany/ai_co"))
    
    @staticmethod
    def get_project_name() -> str:
        """プロジェクト名を取得"""
        return os.getenv("PROJECT_NAME", "elders-guild")
    
    @staticmethod
    def get_env() -> str:
        """環境を取得（development/staging/production）"""
        return os.getenv("ENV", "development")
    
    @staticmethod
    def get_log_level() -> str:
        """ログレベルを取得"""
        return os.getenv("LOG_LEVEL", "INFO")
    
    @staticmethod
    def is_debug() -> bool:
        """デバッグモードかどうか"""
        return os.getenv("DEBUG", "false").lower() == "true"
    
    # === Language & Timezone ===
    @staticmethod
    def get_default_language() -> str:
        """デフォルト言語を取得"""
        return os.getenv("DEFAULT_LANGUAGE", "ja")
    
    @staticmethod
    def get_timezone() -> str:
        """タイムゾーンを取得"""
        return os.getenv("TIMEZONE", "Asia/Tokyo")
    
    # === GitHub Integration ===
    @staticmethod
    def get_github_token() -> Optional[str]:
        """GitHubトークンを取得"""
        return os.getenv("GITHUB_TOKEN")
    
    @staticmethod
    def get_github_repo_owner() -> str:
        """GitHubリポジトリオーナーを取得"""
        return os.getenv("GITHUB_REPO_OWNER", "ext-maru")
    
    @staticmethod
    def get_github_repo_name() -> str:
        """GitHubリポジトリ名を取得"""
        return os.getenv("GITHUB_REPO_NAME", "ai-co")
    
    @staticmethod
    def get_github_api_base_url() -> str:
        """GitHub API ベースURLを取得"""
        return os.getenv("GITHUB_API_BASE_URL", "https://api.github.com")
    
    # === Database Configuration ===
    @staticmethod
    def get_database_config() -> Dict[str, Any]:
        """データベース設定を取得"""
        return {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("POSTGRES_DATABASE", "elders_guild"),
            "user": os.getenv("POSTGRES_USER", "elder_admin"),
            "password": os.getenv("POSTGRES_PASSWORD", ""),
        }
    
    @staticmethod
    def get_database_url() -> str:
        """データベースURLを取得"""
        config = EnvManager.get_database_config()
        return (
            f"postgresql://{config['user']}:{config['password']}"
            f"@{config['host']}:{config['port']}/{config['database']}"
        )
    
    @staticmethod
    def get_ai_company_database_url() -> str:
        """AI Company データベースURLを取得"""
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("AI_COMPANY_DB_NAME", "ai_company")
        user = os.getenv("AI_COMPANY_DB_USER", "ai_company_user")
        password = os.getenv("AI_COMPANY_DB_PASSWORD", "")
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    
    @staticmethod
    def get_elders_knowledge_database_url() -> str:
        """Elders Knowledge データベースURLを取得"""
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("ELDERS_KNOWLEDGE_DB_NAME", "elders_knowledge")
        user = os.getenv("ELDERS_KNOWLEDGE_DB_USER", "elders_guild")
        password = os.getenv("ELDERS_KNOWLEDGE_DB_PASSWORD", "")
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    
    # === Redis Configuration ===
    @staticmethod
    def get_redis_config() -> Dict[str, Any]:
        """Redis設定を取得"""
        return {
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "db": int(os.getenv("REDIS_DB", "0")),
            "password": os.getenv("REDIS_PASSWORD", None),
        }
    
    @staticmethod
    def get_redis_url() -> str:
        """Redis URLを取得"""
        config = EnvManager.get_redis_config()
        password = f":{config['password']}@" if config['password'] else ""
        return f"redis://{password}{config['host']}:{config['port']}/{config['db']}"
    
    # === RabbitMQ Configuration ===
    @staticmethod
    def get_rabbitmq_config() -> Dict[str, Any]:
        """RabbitMQ設定を取得"""
        return {
            "host": os.getenv("RABBITMQ_HOST", "localhost"),
            "port": int(os.getenv("RABBITMQ_PORT", "5672")),
            "user": os.getenv("RABBITMQ_USER", "guest"),
            "password": os.getenv("RABBITMQ_PASSWORD", "guest"),
            "vhost": os.getenv("RABBITMQ_VHOST", "/"),
        }
    
    @staticmethod
    def get_rabbitmq_url() -> str:
        """RabbitMQ URLを取得"""
        config = EnvManager.get_rabbitmq_config()
        return (
            f"amqp://{config['user']}:{config['password']}"
            f"@{config['host']}:{config['port']}{config['vhost']}"
        )
    
    # === API Keys ===
    @staticmethod
    def get_anthropic_api_key() -> Optional[str]:
        """Anthropic APIキーを取得"""
        return os.getenv("ANTHROPIC_API_KEY")
    
    @staticmethod
    def get_openai_api_key() -> Optional[str]:
        """OpenAI APIキーを取得"""
        return os.getenv("OPENAI_API_KEY")
    
    # === Service Ports ===
    @staticmethod
    def get_api_port() -> int:
        """APIサーバーポートを取得"""
        return int(os.getenv("API_PORT", "8001"))
    
    @staticmethod
    def get_api_host() -> str:
        """APIサーバーホストを取得"""
        return os.getenv("API_HOST", "0.0.0.0")
    
    # === Path Configuration ===
    @staticmethod
    def get_knowledge_base_path() -> Path:
        """ナレッジベースパスを取得"""
        root = EnvManager.get_project_root()
        return root / "knowledge_base"
    
    @staticmethod
    def get_logs_path() -> Path:
        """ログパスを取得"""
        root = EnvManager.get_project_root()
        return root / "logs"
    
    @staticmethod
    def get_data_path() -> Path:
        """データパスを取得"""
        root = EnvManager.get_project_root()
        return root / "data"
    
    @staticmethod
    def get_scripts_path() -> Path:
        """スクリプトパスを取得"""
        root = EnvManager.get_project_root()
        return root / "scripts"
    
    @staticmethod
    def get_libs_path() -> Path:
        """ライブラリパスを取得"""
        root = EnvManager.get_project_root()
        return root / "libs"
    
    @staticmethod
    def get_tests_path() -> Path:
        """テストパスを取得"""
        root = EnvManager.get_project_root()
        return root / "tests"
    
    @staticmethod
    def get_workers_path() -> Path:
        """ワーカーパスを取得"""
        root = EnvManager.get_project_root()
        return root / "workers"
    
    @staticmethod
    def get_commands_path() -> Path:
        """コマンドパスを取得"""
        root = EnvManager.get_project_root()
        return root / "commands"
    
    @staticmethod
    def get_config_path() -> Path:
        """設定パスを取得"""
        root = EnvManager.get_project_root()
        return root / "config"
    
    # === Feature Flags ===
    @staticmethod
    def is_auto_issue_processor_enabled() -> bool:
        """Auto Issue Processorが有効か"""
        return os.getenv("ENABLE_AUTO_ISSUE_PROCESSOR", "true").lower() == "true"
    
    @staticmethod
    def is_elder_flow_enabled() -> bool:
        """Elder Flowが有効か"""
        return os.getenv("ENABLE_ELDER_FLOW", "true").lower() == "true"
    
    @staticmethod
    def is_a2a_communication_enabled() -> bool:
        """A2A通信が有効か"""
        return os.getenv("ENABLE_A2A_COMMUNICATION", "true").lower() == "true"
    
    @staticmethod
    def is_nwo_system_enabled() -> bool:
        """nWoシステムが有効か"""
        return os.getenv("ENABLE_NWO_SYSTEM", "true").lower() == "true"
    
    # === Utility Methods ===
    @staticmethod
    def validate_required_env_vars() -> bool:
        """必須環境変数が設定されているか検証"""
        # .envファイルから環境変数を読み込む
        from pathlib import Path
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        if not (key not in os.environ):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if key not in os.environ:
                            os.environ[key] = value
        
        required_vars = [
            "GITHUB_TOKEN",
            "POSTGRES_PASSWORD",
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        return True
    
    @staticmethod
    def get_all_env_vars() -> Dict[str, str]:
        """すべての環境変数を取得（デバッグ用）"""
        return {
            "PROJECT_ROOT": str(EnvManager.get_project_root()),
            "PROJECT_NAME": EnvManager.get_project_name(),
            "ENV": EnvManager.get_env(),
            "DATABASE_URL": EnvManager.get_database_url(),
            "REDIS_URL": EnvManager.get_redis_url(),
            "RABBITMQ_URL": EnvManager.get_rabbitmq_url(),
            "API_PORT": str(EnvManager.get_api_port()),
            "GITHUB_REPO": f"{EnvManager.get_github_repo_owner()}/{EnvManager.get_github_repo_name()}",
        }


if __name__ == "__main__":
    # テスト実行
    print("=== Elders Guild Environment Manager ===")
    print(f"Project Root: {EnvManager.get_project_root()}")
    print(f"Environment: {EnvManager.get_env()}")
    print(f"Database URL: {EnvManager.get_database_url()}")
    print(f"Redis URL: {EnvManager.get_redis_url()}")
    print(f"Knowledge Base Path: {EnvManager.get_knowledge_base_path()}")
    print(f"\nValidation: {'✅ OK' if EnvManager.validate_required_env_vars() else '❌ NG'}")