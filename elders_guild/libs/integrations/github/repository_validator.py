#!/usr/bin/env python3
"""
エルダーズギルド リポジトリ検証システム
Repository Validation System for Elders Guild

正しいリポジトリのみを使用することを強制するセキュリティシステム
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from libs.env_manager import EnvManager


class RepositoryValidator:
    """リポジトリ検証・制限システム"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Args:
            config_path: 設定ファイルパス（デフォルト: configs/repository_config.json）
        """
        self.config_path = config_path or "configs/repository_config.json"
        self.logger = logging.getLogger(self.__class__.__name__)

        # 設定の読み込み
        self.config = self._load_config()

        # 許可されたリポジトリ設定
        self.allowed_repos = self.config.get("allowed_repositories", [])
        self.default_repo = self.config.get("default_repository", {})

        # 禁止されたリポジトリ（誤使用防止）
        self.forbidden_repos = self.config.get(
            "forbidden_repositories",
            [
                "anthropics/claude-code",  # 間違って使用したリポジトリ
            ],
        )

        # 検証モード
        self.strict_mode = self.config.get("strict_mode", True)

    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        if not os.path.exists(self.config_path):
            # デフォルト設定を作成
            default_config = {
                "allowed_repositories": [
                    {
                        "owner": EnvManager.get_github_repo_owner(),
                        "name": EnvManager.get_github_repo_name(),
                        "description": "メインプロジェクトリポジトリ",
                        "is_primary": True,
                    }
                ],
                "default_repository": {
                    "owner": EnvManager.get_github_repo_owner(),
                    "name": EnvManager.get_github_repo_name()
                },
                "forbidden_repositories": [
                    {
                        "owner": "anthropics",
                        "name": "claude-code",
                        "reason": "間違って使用したリポジトリ",
                    }
                ],
                "strict_mode": True,
                "auto_correction": True,
            }

            # 設定ディレクトリを作成
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)

            return default_config

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"設定ファイル読み込みエラー: {e}")
            return {}

    def validate_repository(self, repo_owner: str, repo_name: str) -> Tuple[bool, str]:
        """
        リポジトリを検証

        Args:
            repo_owner: リポジトリオーナー
            repo_name: リポジトリ名

        Returns:
            (検証結果, メッセージ)
        """
        # 禁止リポジトリチェック
        if self._is_forbidden_repo(repo_owner, repo_name):
            return False, f"🚫 禁止されたリポジトリです: {repo_owner}/{repo_name}"

        # 許可リポジトリチェック
        if self._is_allowed_repo(repo_owner, repo_name):
            return True, f"✅ 許可されたリポジトリです: {repo_owner}/{repo_name}"

        # 厳密モードの場合は拒否
        if self.strict_mode:
            return (
                False,
                f"🔒 厳密モードで許可されていないリポジトリです: {repo_owner}/{repo_name}",
            )

        # 警告付きで許可
        return True, f"⚠️ 警告: 未設定リポジトリです: {repo_owner}/{repo_name}"

    def _is_forbidden_repo(self, owner: str, name: str) -> bool:
        """禁止リポジトリかどうかチェック"""
        for forbidden in self.forbidden_repos:
            if forbidden.get("owner") == owner and forbidden.get("name") == name:
                return True
        return False

    def _is_allowed_repo(self, owner: str, name: str) -> bool:
        """許可リポジトリかどうかチェック"""
        for allowed in self.allowed_repos:
            if allowed.get("owner") == owner and allowed.get("name") == name:
                return True
        return False

    def get_default_repository(self) -> Dict[str, str]:
        """デフォルトリポジトリを取得"""
        return self.default_repo

    def get_primary_repository(self) -> Dict[str, str]:
        """プライマリリポジトリを取得"""
        for repo in self.allowed_repos:
            if repo.get("is_primary", False):
                return {"owner": repo["owner"], "name": repo["name"]}
        return self.default_repo

    def auto_correct_repository(
        self, repo_owner: str, repo_name: str
    ) -> Dict[str, str]:
        """
        リポジトリを自動修正

        Args:
            repo_owner: 元のオーナー
            repo_name: 元のリポジトリ名

        Returns:
            修正後のリポジトリ情報
        """
        # 禁止リポジトリの場合は強制的にプライマリに変更
        if self._is_forbidden_repo(repo_owner, repo_name):
            primary = self.get_primary_repository()
            self.logger.warning(
                f"禁止リポジトリ {repo_owner}/{repo_name} をプライマリリポジトリに自動修正: {primary['owner']}/{primary['name']}"
            )
            return primary

        # 許可されている場合はそのまま
        if self._is_allowed_repo(repo_owner, repo_name):
            return {"owner": repo_owner, "name": repo_name}

        # 未設定の場合は設定に依存
        if self.config.get("auto_correction", True):
            primary = self.get_primary_repository()
            self.logger.warning(
                f"未設定リポジトリ {repo_owner}/{repo_name} をプライマリリポジトリに自動修正: {primary['owner']}/{primary['name']}"
            )
            return primary

        return {"owner": repo_owner, "name": repo_name}

    def parse_repository_url(self, url: str) -> Optional[Dict[str, str]]:
        """
        GitHubリポジトリURLを解析

        Args:
            url: GitHub URL

        Returns:
            リポジトリ情報（owner, name）
        """
        patterns = [
            r"https://github\.com/([^/]+)/([^/]+)/?",
            r"git@github\.com:([^/]+)/([^/]+)\.git",
            r"([^/]+)/([^/]+)",  # owner/name形式
        ]

        for pattern in patterns:
            match = re.match(pattern, url)
            if match:
                return {
                    "owner": match.group(1),
                    "name": match.group(2).replace(".git", ""),
                }

        return None

    def log_repository_access(
        self, repo_owner: str, repo_name: str, action: str, result: bool, message: str
    ):
        """リポジトリアクセスをログに記録"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "repository": f"{repo_owner}/{repo_name}",
            "action": action,
            "result": "success" if result else "blocked",
            "message": message,
        }

        log_file = Path("logs/repository_access.log")
        log_file.parent.mkdir(exist_ok=True)

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    def add_allowed_repository(
        self, owner: str, name: str, description: str = "", is_primary: bool = False
    ):
        """許可リポジトリを追加"""
        new_repo = {
            "owner": owner,
            "name": name,
            "description": description,
            "is_primary": is_primary,
            "added_at": datetime.now().isoformat(),
        }

        # 既存チェック
        if not self._is_allowed_repo(owner, name):
            self.allowed_repos.append(new_repo)
            self._save_config()
            self.logger.info(f"許可リポジトリを追加: {owner}/{name}")
        else:
            self.logger.info(f"リポジトリは既に許可済み: {owner}/{name}")

    def remove_allowed_repository(self, owner: str, name: str):
        """許可リポジトリを削除"""
        self.allowed_repos = [
            repo
            for repo in self.allowed_repos
            if not (repo.get("owner") == owner and repo.get("name") == name)
        ]
        self._save_config()
        self.logger.info(f"許可リポジトリを削除: {owner}/{name}")

    def _save_config(self):
        """設定を保存"""
        self.config["allowed_repositories"] = self.allowed_repos
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)


# グローバル検証インスタンス
_repository_validator = None


def get_repository_validator() -> RepositoryValidator:
    """グローバル検証インスタンスを取得"""
    global _repository_validator
    if _repository_validator is None:
        _repository_validator = RepositoryValidator()
    return _repository_validator


def validate_repository(repo_owner: str, repo_name: str) -> Tuple[bool, str]:
    """リポジトリ検証（便利関数）"""
    validator = get_repository_validator()
    return validator.validate_repository(repo_owner, repo_name)


def get_safe_repository(repo_owner: str, repo_name: str) -> Dict[str, str]:
    """安全なリポジトリを取得（自動修正付き）"""
    validator = get_repository_validator()

    # 検証
    is_valid, message = validator.validate_repository(repo_owner, repo_name)

    if not is_valid:
        # 自動修正
        corrected = validator.auto_correct_repository(repo_owner, repo_name)
        validator.log_repository_access(
            repo_owner,
            repo_name,
            "auto_correction",
            True,
            f"自動修正: {corrected['owner']}/{corrected['name']}",
        )
        return corrected

    validator.log_repository_access(repo_owner, repo_name, "access", True, message)
    return {"owner": repo_owner, "name": repo_name}
