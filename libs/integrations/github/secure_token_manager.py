"""
セキュアなGitHubトークン管理システム
環境変数とシークレット管理の統合
"""

import base64
import json
import logging
import os
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class SecureTokenManager:
    """セキュアなトークン管理"""

    def __init__(self, config_path: Optional[str] = None):
        """初期化

        Args:
            config_path: 設定ファイルパス（オプション）
        """
        self.config_path = config_path or os.path.expanduser(
            "~/.elders_guild/github_config.json"
        )
        self.cipher = None
        self._init_encryption()

    def _init_encryption(self):
        """暗号化の初期化"""
        # マスターキーを環境変数から取得または生成
        master_key = os.getenv("ELDERS_MASTER_KEY")

        if not master_key:
            # 初回は自動生成
            master_key = Fernet.generate_key().decode()
            logger.warning(
                "No master key found. Generated new key. "
                "Please set ELDERS_MASTER_KEY environment variable."
            )
            print(
                f"\n⚠️  Set this in your environment:\nexport ELDERS_MASTER_KEY='{master_key}'\n"
            )

        # 暗号化オブジェクトを作成
        self.cipher = Fernet(
            master_key.encode() if isinstance(master_key, str) else master_key
        )

    def get_token(self, token_type: str = "github") -> Optional[str]:
        """トークンを取得

        Args:
            token_type: トークンタイプ（デフォルト: github）

        Returns:
            復号化されたトークン
        """
        # 1. 環境変数から取得を試みる
        env_key = f"{token_type.upper()}_TOKEN"
        token = os.getenv(env_key)

        if token:
            return token

        # 2. 暗号化された設定ファイルから取得
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    encrypted_data = json.load(f)

                if token_type in encrypted_data:
                    encrypted_token = encrypted_data[token_type].encode()
                    return self.cipher.decrypt(encrypted_token).decode()

            except Exception as e:
                logger.error(f"Failed to read encrypted token: {e}")

        # 3. GitHub CLIから取得を試みる
        if token_type == "github":
            token = self._get_from_gh_cli()
            if token:
                # 今後のために保存
                self.save_token("github", token)
                return token

        return None

    def save_token(self, token_type: str, token: str):
        """トークンを暗号化して保存

        Args:
            token_type: トークンタイプ
            token: 保存するトークン
        """
        # ディレクトリ作成
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

        # 既存の設定を読み込み
        encrypted_data = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    encrypted_data = json.load(f)
            except:
                pass

        # トークンを暗号化
        encrypted_token = self.cipher.encrypt(token.encode()).decode()
        encrypted_data[token_type] = encrypted_token

        # 保存
        with open(self.config_path, "w") as f:
            json.dump(encrypted_data, f, indent=2)

        # パーミッションを制限
        os.chmod(self.config_path, 0o600)

        logger.info(f"Token saved for {token_type}")

    def _get_from_gh_cli(self) -> Optional[str]:
        """GitHub CLIからトークンを取得"""
        try:
            import subprocess

            result = subprocess.run(
                ["gh", "auth", "token"], capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except:
            return None

    def validate_token(self, token: str) -> bool:
        """トークンの有効性を検証

        Args:
            token: 検証するトークン

        Returns:
            有効な場合True
        """
        try:
            from github import Github

            g = Github(token)
            # 簡単なAPIコールで検証
            g.get_user().login
            return True
        except:
            return False

    def get_minimal_scopes(self, operation: str) -> list:
        """操作に必要な最小限のスコープを返す

        Args:
            operation: 操作タイプ

        Returns:
            必要なスコープのリスト
        """
        scope_map = {
            "read_issues": ["repo:status", "public_repo"],
            "write_issues": ["repo"],
            "create_pr": ["repo", "write:pull_request"],
            "workflow": ["workflow"],
            "admin": ["repo", "admin:repo_hook"],
        }

        return scope_map.get(operation, ["repo"])


class GitHubTokenValidator:
    """GitHubトークンのバリデーター"""

    @staticmethod
    def check_scopes(token: str, required_scopes: list) -> Dict[str, Any]:
        """トークンのスコープをチェック

        Args:
            token: GitHubトークン
            required_scopes: 必要なスコープ

        Returns:
            検証結果
        """
        import requests

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

        try:
            response = requests.get("https://api.github.com/user", headers=headers)
            response.raise_for_status()

            # スコープを取得
            scopes = response.headers.get("X-OAuth-Scopes", "").split(", ")
            scopes = [s.strip() for s in scopes if s.strip()]

            # 必要なスコープがあるかチェック
            missing_scopes = [s for s in required_scopes if s not in scopes]

            return {
                "valid": len(missing_scopes) == 0,
                "scopes": scopes,
                "missing_scopes": missing_scopes,
                "rate_limit_remaining": response.headers.get(
                    "X-RateLimit-Remaining", "unknown"
                ),
            }

        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "scopes": [],
                "missing_scopes": required_scopes,
            }


# 環境変数ヘルパー
def setup_github_env():
    """GitHub環境変数のセットアップヘルパー"""
    print("🔐 GitHub Token Setup")
    print("=" * 50)

    manager = SecureTokenManager()

    # 既存のトークンをチェック
    existing_token = manager.get_token("github")

    if existing_token and manager.validate_token(existing_token):
        print("✅ Valid GitHub token found!")
        validator = GitHubTokenValidator()
        result = validator.check_scopes(existing_token, ["repo", "workflow"])

        print(f"Current scopes: {', '.join(result['scopes'])}")
        if result["missing_scopes"]:
            print(f"⚠️  Missing scopes: {', '.join(result['missing_scopes'])}")

        return existing_token

    print("\n📝 GitHub Personal Access Token required")
    print("Visit: https://github.com/settings/tokens/new")
    print("\nRequired scopes:")
    print("  ✓ repo (Full control of private repositories)")
    print("  ✓ workflow (Update GitHub Action workflows)")
    print()

    token = input("Enter your GitHub token: ").strip()

    if manager.validate_token(token):
        manager.save_token("github", token)
        print("✅ Token saved successfully!")
        return token
    else:
        print("❌ Invalid token. Please check and try again.")
        return None


if __name__ == "__main__":
    # セットアップヘルパーを実行
    setup_github_env()
