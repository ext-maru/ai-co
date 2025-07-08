"""
Simple Environment Configuration
シンプルな環境変数管理 - .envファイルベース
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent

def load_env_file(env_path: str = None) -> bool:
    """
    .envファイルを読み込み
    """
    if env_path is None:
        env_path = PROJECT_ROOT / '.env'
    
    if not os.path.exists(env_path):
        logger.warning(f".env file not found: {env_path}")
        return False
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # コメント行や空行をスキップ
                if not line or line.startswith('#'):
                    continue
                
                # KEY=VALUE形式をパース
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # クォートを除去
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    # 環境変数に設定（既存の値は上書きしない）
                    if key not in os.environ:
                        os.environ[key] = value
                
    except Exception as e:
        logger.error(f"Failed to load .env file: {e}")
        return False
    
    logger.info(f"Loaded environment from: {env_path}")
    return True

def get_env(key: str, default: Any = None, required: bool = False) -> Any:
    """
    環境変数を取得
    """
    value = os.getenv(key, default)
    
    if required and not value:
        raise ValueError(f"Required environment variable '{key}' is not set")
    
    return value

def get_bool_env(key: str, default: bool = False) -> bool:
    """
    boolean型の環境変数を取得
    """
    value = get_env(key, str(default))
    return value.lower() in ('true', '1', 'yes', 'on')

def get_int_env(key: str, default: int = 0) -> int:
    """
    integer型の環境変数を取得
    """
    value = get_env(key, str(default))
    try:
        return int(value)
    except ValueError:
        return default

def get_float_env(key: str, default: float = 0.0) -> float:
    """
    float型の環境変数を取得
    """
    value = get_env(key, str(default))
    try:
        return float(value)
    except ValueError:
        return default

def get_list_env(key: str, default: list = None, separator: str = ',') -> list:
    """
    リスト型の環境変数を取得（カンマ区切り）
    """
    if default is None:
        default = []
    
    value = get_env(key)
    if not value:
        return default
    
    return [item.strip() for item in value.split(separator) if item.strip()]

class Config:
    """
    AI Company設定クラス
    """
    
    def __init__(self):
        # .envファイル自動読み込み
        load_env_file()
        
        # Anthropic/Claude API
        simulation_mode = get_bool_env('TASK_WORKER_SIMULATION_MODE', False)
        self.ANTHROPIC_API_KEY = get_env('ANTHROPIC_API_KEY', required=not simulation_mode)
        self.ANTHROPIC_API_KEYS = self._get_api_keys()
        
        # Slack
        self.SLACK_BOT_TOKEN = get_env('SLACK_BOT_TOKEN')
        self.SLACK_APP_TOKEN = get_env('SLACK_APP_TOKEN')
        self.SLACK_TEAM_ID = get_env('SLACK_TEAM_ID')
        self.SLACK_CHANNEL_IDS = get_env('SLACK_CHANNEL_IDS')
        self.SLACK_CHANNEL = get_env('SLACK_CHANNEL', '#ai-notifications')
        
        # Slack Polling
        self.SLACK_POLLING_CHANNEL_ID = get_env('SLACK_POLLING_CHANNEL_ID', 'C0946R76UU8')
        self.SLACK_POLLING_INTERVAL = get_int_env('SLACK_POLLING_INTERVAL', 20)
        self.SLACK_POLLING_ENABLED = get_bool_env('SLACK_POLLING_ENABLED', True)
        self.SLACK_REQUIRE_MENTION = get_bool_env('SLACK_REQUIRE_MENTION', True)
        
        # RabbitMQ
        self.RABBITMQ_HOST = get_env('RABBITMQ_HOST', 'localhost')
        self.RABBITMQ_PORT = get_int_env('RABBITMQ_PORT', 5672)
        self.RABBITMQ_USER = get_env('RABBITMQ_USER', 'guest')
        self.RABBITMQ_PASS = get_env('RABBITMQ_PASS', 'guest')
        
        # System
        self.PROJECT_ROOT = PROJECT_ROOT
        self.PYTHONPATH = get_env('PYTHONPATH', str(PROJECT_ROOT))
        self.AI_VENV_ACTIVE = get_bool_env('AI_VENV_ACTIVE', True)
        self.AI_AUTO_GIT_DISABLED = get_bool_env('AI_AUTO_GIT_DISABLED', False)
        
        # Logging
        self.LOG_LEVEL = get_env('LOG_LEVEL', 'INFO')
        self.DEBUG = get_bool_env('DEBUG', False)
        
        # Web UI
        self.WEB_UI_PORT = get_int_env('WEB_UI_PORT', 5555)
        self.WEB_UI_HOST = get_env('WEB_UI_HOST', 'localhost')
        
        # Database
        self.DATABASE_URL = get_env('DATABASE_URL', f'sqlite:///{PROJECT_ROOT}/data/tasks.db')
        
        # API Rate Limiting
        self.API_KEY_ROTATION_ENABLED = get_bool_env('API_KEY_ROTATION_ENABLED', True)
        self.API_KEY_ROTATION_STRATEGY = get_env('API_KEY_ROTATION_STRATEGY', 'rate_limit_aware')
        self.API_KEY_COOLDOWN_MINUTES = get_int_env('API_KEY_COOLDOWN_MINUTES', 60)
        self.API_KEY_MAX_RETRIES = get_int_env('API_KEY_MAX_RETRIES', 3)
    
    def _get_api_keys(self) -> list:
        """
        複数のAPIキーを取得
        """
        keys = []
        
        # Primary key
        if self.ANTHROPIC_API_KEY:
            keys.append(self.ANTHROPIC_API_KEY)
        
        # Additional keys (ANTHROPIC_API_KEY_1, ANTHROPIC_API_KEY_2, etc.)
        for i in range(1, 10):
            key = get_env(f'ANTHROPIC_API_KEY_{i}')
            if key:
                keys.append(key)
        
        return keys
    
    def validate(self) -> Dict[str, bool]:
        """
        設定の妥当性をチェック
        """
        validation = {
            'anthropic_api_key': bool(self.ANTHROPIC_API_KEY),
            'slack_bot_token': bool(self.SLACK_BOT_TOKEN),
            'pythonpath_set': bool(self.PYTHONPATH),
            'project_root_exists': self.PROJECT_ROOT.exists(),
        }
        
        return validation
    
    def get_slack_config(self) -> Dict[str, str]:
        """
        Slack設定を辞書で取得
        """
        return {
            'bot_token': self.SLACK_BOT_TOKEN,
            'app_token': self.SLACK_APP_TOKEN,
            'team_id': self.SLACK_TEAM_ID,
            'channel_ids': self.SLACK_CHANNEL_IDS,
            'channel': self.SLACK_CHANNEL
        }
    
    def get_rabbitmq_config(self) -> Dict[str, Any]:
        """
        RabbitMQ設定を辞書で取得
        """
        return {
            'host': self.RABBITMQ_HOST,
            'port': self.RABBITMQ_PORT,
            'user': self.RABBITMQ_USER,
            'password': self.RABBITMQ_PASS
        }
    
    def get_api_rotation_config(self) -> Dict[str, Any]:
        """
        APIローテーション設定を辞書で取得
        """
        return {
            'enabled': self.API_KEY_ROTATION_ENABLED,
            'strategy': self.API_KEY_ROTATION_STRATEGY,
            'cooldown_minutes': self.API_KEY_COOLDOWN_MINUTES,
            'max_retries': self.API_KEY_MAX_RETRIES,
            'api_keys': self.ANTHROPIC_API_KEYS
        }
    
    def __repr__(self):
        safe_config = {}
        for key, value in self.__dict__.items():
            if 'token' in key.lower() or 'key' in key.lower() or 'pass' in key.lower():
                # センシティブ情報をマスク
                if isinstance(value, str) and len(value) > 8:
                    safe_config[key] = f"{value[:4]}****{value[-4:]}"
                elif isinstance(value, list):
                    safe_config[key] = [f"{v[:4]}****{v[-4:]}" if isinstance(v, str) and len(v) > 8 else v for v in value]
                else:
                    safe_config[key] = "****"
            else:
                safe_config[key] = value
        
        return f"Config({safe_config})"

# グローバル設定インスタンス
config = Config()

def get_config() -> Config:
    """
    グローバル設定インスタンスを取得
    """
    return config

def verify_setup() -> bool:
    """
    AI Company環境セットアップを確認
    """
    validation = config.validate()
    
    print("🔍 AI Company Environment Verification")
    print("=" * 40)
    
    all_good = True
    
    for check, status in validation.items():
        emoji = "✅" if status else "❌"
        print(f"{emoji} {check.replace('_', ' ').title()}: {'OK' if status else 'FAILED'}")
        if not status:
            all_good = False
    
    if all_good:
        print("\n🎉 Environment setup is complete!")
    else:
        print("\n⚠️  Some issues found. Please check your .env file.")
        print("💡 Copy .env.template to .env and fill in the required values.")
    
    return all_good