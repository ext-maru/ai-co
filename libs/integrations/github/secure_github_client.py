#!/usr/bin/env python3
"""
セキュアGitHubクライアント
Secure GitHub Client with Repository Validation

リポジトリ検証を内蔵したセキュアなGitHubクライアント
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from .rate_limiter import get_rate_limiter, safe_github_request
from .repository_validator import RepositoryValidator, get_repository_validator


class SecureGitHubClient:
    """リポジトリ検証機能付きセキュアGitHubクライアント"""

    def __init__(
        self, github_token: Optional[str] = None, auto_correction: bool = True
    ):
        """
        Args:
            github_token: GitHub Personal Access Token
            auto_correction: 自動修正を有効にするか
        """
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.auto_correction = auto_correction
        self.validator = get_repository_validator()
        self.logger = logging.getLogger(self.__class__.__name__)

        # レート制限管理
        self.rate_limiter = get_rate_limiter(self.github_token)

        # GitHub API設定
        self.api_base = "https://api.github.com"

    def _validate_and_correct_repository(
        self, repo_owner: str, repo_name: str
    ) -> Dict[str, str]:
        """
        リポジトリを検証し、必要に応じて修正

        Args:
            repo_owner: リポジトリオーナー
            repo_name: リポジトリ名

        Returns:
            修正後のリポジトリ情報
        """
        # 検証
        is_valid, message = self.validator.validate_repository(repo_owner, repo_name)

        if not is_valid:
            self.logger.warning(f"リポジトリ検証失敗: {message}")

            if self.auto_correction:
                # 自動修正
                corrected = self.validator.auto_correct_repository(
                    repo_owner, repo_name
                )
                self.logger.info(
                    f"リポジトリ自動修正: {repo_owner}/{repo_name} → {corrected['owner']}/{corrected['name']}"
                )
                return corrected
            else:
                # 修正無効の場合はエラー
                raise ValueError(f"リポジトリアクセス拒否: {message}")

        self.logger.info(f"リポジトリ検証成功: {message}")
        return {"owner": repo_owner, "name": repo_name}

    async def create_issue(
        self,
        repo_owner: str,
        repo_name: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        セキュアなIssue作成（レート制限対応）

        Args:
            repo_owner: リポジトリオーナー
            repo_name: リポジトリ名
            title: Issue タイトル
            body: Issue 本文
            labels: ラベルリスト

        Returns:
            作成されたIssue情報
        """
        # リポジトリ検証・修正
        repo_info = self._validate_and_correct_repository(repo_owner, repo_name)

        # Issue作成データ
        issue_data = {"title": title, "body": body, "labels": labels or []}

        # API呼び出し（レート制限対応）
        url = f"{self.api_base}/repos/{repo_info['owner']}/{repo_info['name']}/issues"

        try:
            response = await self.rate_limiter.safe_request(
                "POST", url, json=issue_data
            )

            if response and response.status_code == 201:
                issue = response.json()
                self.logger.info(f"Issue作成成功: {issue['html_url']}")

                # アクセスログ
                self.validator.log_repository_access(
                    repo_info["owner"],
                    repo_info["name"],
                    "create_issue",
                    True,
                    f"Issue #{issue['number']} created",
                )

                return issue
            else:
                error_msg = f"Issue作成失敗: レート制限またはAPIエラー"
                if response:
                    error_msg += f" {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                raise Exception(error_msg)

        except Exception as e:
            self.logger.error(f"Issue作成エラー: {e}")

            # エラーログ
            self.validator.log_repository_access(
                repo_info["owner"],
                repo_info["name"],
                "create_issue",
                False,
                f"Error: {str(e)}",
            )

            raise

    def close_issue(
        self, repo_owner: str, repo_name: str, issue_number: int
    ) -> Dict[str, Any]:
        """
        セキュアなIssueクローズ

        Args:
            repo_owner: リポジトリオーナー
            repo_name: リポジトリ名
            issue_number: Issue番号

        Returns:
            更新されたIssue情報
        """
        # リポジトリ検証・修正
        repo_info = self._validate_and_correct_repository(repo_owner, repo_name)

        # Issue更新データ
        update_data = {"state": "closed"}

        # API呼び出し
        url = f"{self.api_base}/repos/{repo_info['owner']}/{repo_info['name']}/issues/{issue_number}"

        try:
            response = requests.patch(url, json=update_data, headers=self.headers)

            if response.status_code == 200:
                issue = response.json()
                self.logger.info(f"Issue #{issue_number} クローズ成功")

                # アクセスログ
                self.validator.log_repository_access(
                    repo_info["owner"],
                    repo_info["name"],
                    "close_issue",
                    True,
                    f"Issue #{issue_number} closed",
                )

                return issue
            else:
                error_msg = (
                    f"Issueクローズ失敗: {response.status_code} - {response.text}"
                )
                self.logger.error(error_msg)
                raise Exception(error_msg)

        except Exception as e:
            self.logger.error(f"Issueクローズエラー: {e}")

            # エラーログ
            self.validator.log_repository_access(
                repo_info["owner"],
                repo_info["name"],
                "close_issue",
                False,
                f"Error: {str(e)}",
            )

            raise

    def add_comment(
        self, repo_owner: str, repo_name: str, issue_number: int, comment: str
    ) -> Dict[str, Any]:
        """
        セキュアなコメント追加

        Args:
            repo_owner: リポジトリオーナー
            repo_name: リポジトリ名
            issue_number: Issue番号
            comment: コメント内容

        Returns:
            作成されたコメント情報
        """
        # リポジトリ検証・修正
        repo_info = self._validate_and_correct_repository(repo_owner, repo_name)

        # コメントデータ
        comment_data = {"body": comment}

        # API呼び出し
        url = f"{self.api_base}/repos/{repo_info['owner']}/{repo_info['name']}/issues/{issue_number}/comments"

        try:
            response = requests.post(url, json=comment_data, headers=self.headers)

            if response.status_code == 201:
                comment_info = response.json()
                self.logger.info(f"コメント追加成功: Issue #{issue_number}")

                # アクセスログ
                self.validator.log_repository_access(
                    repo_info["owner"],
                    repo_info["name"],
                    "add_comment",
                    True,
                    f"Comment added to Issue #{issue_number}",
                )

                return comment_info
            else:
                error_msg = (
                    f"コメント追加失敗: {response.status_code} - {response.text}"
                )
                self.logger.error(error_msg)
                raise Exception(error_msg)

        except Exception as e:
            self.logger.error(f"コメント追加エラー: {e}")

            # エラーログ
            self.validator.log_repository_access(
                repo_info["owner"],
                repo_info["name"],
                "add_comment",
                False,
                f"Error: {str(e)}",
            )

            raise

    def list_issues(
        self,
        repo_owner: str,
        repo_name: str,
        state: str = "open",
        labels: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        セキュアなIssue一覧取得

        Args:
            repo_owner: リポジトリオーナー
            repo_name: リポジトリ名
            state: Issue状態（open/closed/all）
            labels: フィルタリング用ラベル

        Returns:
            Issue一覧
        """
        # リポジトリ検証・修正
        repo_info = self._validate_and_correct_repository(repo_owner, repo_name)

        # パラメータ設定
        params = {"state": state}
        if labels:
            params["labels"] = ",".join(labels)

        # API呼び出し
        url = f"{self.api_base}/repos/{repo_info['owner']}/{repo_info['name']}/issues"

        try:
            response = requests.get(url, params=params, headers=self.headers)

            if response.status_code == 200:
                issues = response.json()
                self.logger.info(f"Issue一覧取得成功: {len(issues)}件")

                # アクセスログ
                self.validator.log_repository_access(
                    repo_info["owner"],
                    repo_info["name"],
                    "list_issues",
                    True,
                    f"Retrieved {len(issues)} issues",
                )

                return issues
            else:
                error_msg = (
                    f"Issue一覧取得失敗: {response.status_code} - {response.text}"
                )
                self.logger.error(error_msg)
                raise Exception(error_msg)

        except Exception as e:
            self.logger.error(f"Issue一覧取得エラー: {e}")

            # エラーログ
            self.validator.log_repository_access(
                repo_info["owner"],
                repo_info["name"],
                "list_issues",
                False,
                f"Error: {str(e)}",
            )

            raise

    def get_repository_info(self, repo_owner: str, repo_name: str) -> Dict[str, Any]:
        """
        セキュアなリポジトリ情報取得

        Args:
            repo_owner: リポジトリオーナー
            repo_name: リポジトリ名

        Returns:
            リポジトリ情報
        """
        # リポジトリ検証・修正
        repo_info = self._validate_and_correct_repository(repo_owner, repo_name)

        # API呼び出し
        url = f"{self.api_base}/repos/{repo_info['owner']}/{repo_info['name']}"

        try:
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                repository = response.json()
                self.logger.info(f"リポジトリ情報取得成功: {repository['full_name']}")

                # アクセスログ
                self.validator.log_repository_access(
                    repo_info["owner"],
                    repo_info["name"],
                    "get_repository_info",
                    True,
                    "Repository info retrieved",
                )

                return repository
            else:
                error_msg = (
                    f"リポジトリ情報取得失敗: {response.status_code} - {response.text}"
                )
                self.logger.error(error_msg)
                raise Exception(error_msg)

        except Exception as e:
            self.logger.error(f"リポジトリ情報取得エラー: {e}")

            # エラーログ
            self.validator.log_repository_access(
                repo_info["owner"],
                repo_info["name"],
                "get_repository_info",
                False,
                f"Error: {str(e)}",
            )

            raise


# グローバルクライアントインスタンス
_secure_github_client = None


def get_secure_github_client() -> SecureGitHubClient:
    """グローバルセキュアクライアントインスタンスを取得"""
    global _secure_github_client
    if _secure_github_client is None:
        _secure_github_client = SecureGitHubClient()
    return _secure_github_client
