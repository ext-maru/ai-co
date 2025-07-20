"""
Environment Configuration - 環境設定管理

既存のenv_configから実装をインポート
"""

try:
    from core.env_config import *
except ImportError:
    import os
    
    def get_config(key, default=None):
        """環境変数から設定を取得"""
        return os.getenv(key, default)
    
    def get_database_url():
        """データベースURLを取得"""
        return get_config('DATABASE_URL', 'sqlite:///data/app.db')
    
    def get_github_token():
        """GitHub トークンを取得"""
        return get_config('GITHUB_TOKEN')
