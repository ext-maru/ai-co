#!/usr/bin/env python3
"""
設定ファイル読み込みユーティリティ

JSONファイルの環境変数テンプレートを展開
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.env_manager import EnvManager

class ConfigLoader:
    """設定ファイル読み込みクラス"""
    
    @staticmethod
    def load_json_with_env_vars(file_path: Path) -> Dict[str, Any]:
        """
        環境変数テンプレートを含むJSONファイルを読み込み
        
        Args:
            file_path: JSONファイルのパス
            
        Returns:
            Dict: 環境変数が展開された設定辞書
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 環境変数テンプレートを展開
        expanded_content = ConfigLoader._expand_env_vars(content)
        
        try:
            return json.loads(expanded_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file {file_path}: {e}")
    
    @staticmethod
    def _expand_env_vars(content: str) -> str:
        """
        文字列内の環境変数テンプレートを展開
        
        対応形式: ${VAR_NAME}, ${VAR_NAME:default_value}
        """
        # ${VAR_NAME} または ${VAR_NAME:default} の形式を検索
        pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
        
        def replace_var(match):
            """replace_varメソッド"""
            var_name = match.group(1)
            default_value = match.group(2) or ''
            
            # 環境変数を取得
            value = os.getenv(var_name, default_value)
            return value
        
        return re.sub(pattern, replace_var, content)
    
    @staticmethod
    def load_repository_config() -> Dict[str, Any]:
        """
        リポジトリ設定を読み込み
        
        Returns:
            Dict: リポジトリ設定
        """
        project_root = EnvManager.get_project_root()
        config_path = project_root / "config" / "repository_config.json"
        
        config = ConfigLoader.load_json_with_env_vars(config_path)
        
        # デフォルト値との補完
        if "default_values" in config:
            default_values = config["default_values"]
            
            # GITHUB_REPO_OWNER と GITHUB_REPO_NAME の設定
            if not os.getenv("GITHUB_REPO_OWNER"):
                os.environ["GITHUB_REPO_OWNER"] = default_values.get("owner", "ext-maru")
            
            if not os.getenv("GITHUB_REPO_NAME"):
                os.environ["GITHUB_REPO_NAME"] = default_values.get("name", "ai-co")
            
            # 再度展開
            config = ConfigLoader.load_json_with_env_vars(config_path)
        
        return config
    
    @staticmethod
    def get_primary_repository() -> Dict[str, str]:
        """
        プライマリリポジトリ情報を取得
        
        Returns:
            Dict: owner, name を含む辞書
        """
        config = ConfigLoader.load_repository_config()
        
        # プライマリリポジトリを検索
        for repo in config.get("allowed_repositories", []):
            if repo.get("is_primary", False):
                return {
                    "owner": repo["owner"],
                    "name": repo["name"]
                }
        
        # プライマリが見つからない場合はdefault_repositoryを使用
        if "default_repository" in config:
            return config["default_repository"]
        
        # フォールバック
        return {
            "owner": EnvManager.get_github_repo_owner(),
            "name": EnvManager.get_github_repo_name()
        }
    
    @staticmethod
    def is_repository_allowed(owner: str, name: str) -> bool:
        """
        リポジトリが許可されているかチェック
        
        Args:
            owner: リポジトリオーナー
            name: リポジトリ名
            
        Returns:
            bool: 許可されている場合True
        """
        config = ConfigLoader.load_repository_config()
        
        # 禁止リポジトリチェック
        for forbidden in config.get("forbidden_repositories", []):
            if forbidden["owner"] == owner and forbidden["name"] == name:
                return False
        
        # 許可リポジトリチェック
        for allowed in config.get("allowed_repositories", []):
            if allowed["owner"] == owner and allowed["name"] == name:
                return True
        
        # strict_modeが有効な場合は明示的に許可されたもののみ
        if config.get("strict_mode", False):
            return False
        
        return True

if __name__ == "__main__":
    # テスト実行
    print("=== Config Loader Test ===")
    
    try:
        config = ConfigLoader.load_repository_config()
        print(f"✅ Repository config loaded successfully")
        
        primary = ConfigLoader.get_primary_repository()
        print(f"Primary Repository: {primary['owner']}/{primary['name']}")
        
        # テスト: リポジトリ許可チェック
        is_allowed = ConfigLoader.is_repository_allowed(primary['owner'], primary['name'])
        print(f"Primary repository allowed: {is_allowed}")
        
        # 禁止リポジトリのテスト
        is_forbidden = ConfigLoader.is_repository_allowed("anthropics", "claude-code")
        print(f"Forbidden repository allowed: {is_forbidden}")
        
    except Exception as e:
        print(f"❌ Error: {e}")