#!/usr/bin/env python3
"""
GitHub API create_pull_request 完全実装
Iron Will基準準拠・ブランチ検証・コンフリクト検出・リトライ機構対応
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from libs.integrations.github.security import (
    SecurityViolationError,
    get_security_manager,
)

logger = logging.getLogger(__name__)


class GitHubCreatePullRequestImplementation:
    """GitHub Pull Request作成の完全実装"""

    def __init__(
        self,
        token: Optional[str] = None,
        repo_owner: Optional[str] = None,
        repo_name: Optional[str] = None,
    ):
        """
        初期化

        Args:
            token: GitHub Personal Access Token
            repo_owner: リポジトリオーナー
            repo_name: リポジトリ名
        """
        self.security_manager = get_security_manager()
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.repo_owner = repo_owner or os.environ.get("GITHUB_REPO_OWNER", "")
        self.repo_name = repo_name or os.environ.get("GITHUB_REPO_NAME", "")
        self.base_url = "https://api.github.com"

        # リトライ設定
        self.max_retries = 3
        self.retry_delay = 1.0
        self.backoff_factor = 2.0

        # コンフリクト検出設定
        self.check_conflicts = True
        self.auto_merge_enabled = False

        self._validate_configuration()

    def _validate_configuration(self) -> None:
        """設定の検証"""
        if not self.token:
            raise ValueError("GitHub token is required for creating pull requests")

        if not self.repo_owner or not self.repo_name:
            raise ValueError("Repository owner and name must be specified")

    def create_pull_request(
        self,
        title: str,
        head: str,
        base: str,
        body: Optional[str] = None,
        draft: bool = False,
        maintainer_can_modify: bool = True,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        reviewers: Optional[List[str]] = None,
        team_reviewers: Optional[List[str]] = None,
        milestone: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        GitHub Pull Requestを作成

        Args:
            title: PRタイトル
            head: マージ元ブランチ（feature branch）
            base: マージ先ブランチ（通常はmainまたはmaster）
            body: PR本文（説明）
            draft: ドラフトPRとして作成
            maintainer_can_modify: メンテナーによる編集を許可
            labels: ラベルリスト
            assignees: アサイン者リスト
            reviewers: レビュアーリスト
            team_reviewers: チームレビュアーリスト
            milestone: マイルストーン番号

        Returns:
            Dict containing:
                - success: 成功フラグ
                - pull_request: 作成されたPR情報
                - conflict_status: コンフリクト状態
                - error: エラー情報（失敗時）
        """
        try:
            # 入力検証
            validation_result = self._validate_pr_params(title, head, base)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": validation_result["error"],
                    "pull_request": None,
                }

            # ブランチの存在確認
            branch_check = self._check_branches_exist(head, base)
            if not branch_check["success"]:
                return {
                    "success": False,
                    "error": branch_check["error"],
                    "pull_request": None,
                }

            # 既存のPRチェック
            existing_pr = self._check_existing_pr(head, base)
            if existing_pr["exists"]:
                return {
                    "success": False,
                    "error": f"Pull request already exists: #{existing_pr['pr_number']}",
                    "pull_request": existing_pr["pull_request"],
                }

            # コミット差分の確認
            diff_check = self._check_commit_diff(head, base)
            if not diff_check["has_changes"]:
                return {
                    "success": False,
                    "error": "No changes between head and base branches",
                    "pull_request": None,
                }

            # PR作成データ構築
            pr_data = {
                "title": title,
                "head": head,
                "base": base,
                "body": body or "",
                "draft": draft,
                "maintainer_can_modify": maintainer_can_modify,
            }

            # PRを作成
            response = self._make_api_request(
                endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/pulls",
                method="POST",
                json_data=pr_data,
            )

            if not response["success"]:
                return {
                    "success": False,
                    "error": response["error"],
                    "pull_request": None,
                }

            pr = response["data"]
            pr_number = pr["number"]

            # 追加設定（ラベル、アサイン、レビュアー等）
            if labels or assignees or reviewers or team_reviewers or milestone:
                self._configure_pull_request(
                    pr_number=pr_number,
                    labels=labels,
                    assignees=assignees,
                    reviewers=reviewers,
                    team_reviewers=team_reviewers,
                    milestone=milestone,
                )

            # コンフリクトチェック
            conflict_status = self._check_merge_conflicts(pr_number)

            # 自動マージ設定（有効な場合）
            if self.auto_merge_enabled and not conflict_status["has_conflicts"]:
                self._enable_auto_merge(pr_number)

            # PRの最新情報を取得
            updated_pr = self._get_pull_request(pr_number)

            return {
                "success": True,
                "pull_request": (
                    updated_pr["pull_request"] if updated_pr["success"] else pr
                ),
                "conflict_status": conflict_status,
                "pr_url": pr["html_url"],
            }

        except Exception as e:
            logger.error(f"Failed to create pull request: {e}")
            return {"success": False, "error": str(e), "pull_request": None}

    def _validate_pr_params(self, title: str, head: str, base: str) -> Dict[str, Any]:
        """PRパラメータの検証"""
        if not title or not title.strip():
            return {"valid": False, "error": "Pull request title cannot be empty"}

        if not head or not head.strip():
            return {"valid": False, "error": "Head branch cannot be empty"}

        if not base or not base.strip():
            return {"valid": False, "error": "Base branch cannot be empty"}

        if head == base:
            return {
                "valid": False,
                "error": "Head and base branches cannot be the same",
            }

        return {"valid": True}

    def _check_branches_exist(self, head: str, base: str) -> Dict[str, Any]:
        """ブランチの存在確認"""
        try:
            # ベースブランチの確認
            base_response = self._make_api_request(
                endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/branches/{base}",
                method="GET",
            )

            if not base_response["success"]:
                return {"success": False, "error": f"Base branch '{base}' not found"}

            # ヘッドブランチの確認
            head_response = self._make_api_request(
                endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/branches/{head}",
                method="GET",
            )

            if not head_response["success"]:
                return {"success": False, "error": f"Head branch '{head}' not found"}

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": f"Failed to check branches: {e}"}

    def _check_existing_pr(self, head: str, base: str) -> Dict[str, Any]:
        """既存のPRをチェック"""
        try:
            # 既存のPRを検索
            response = self._make_api_request(
                endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/pulls",
                method="GET",
                params={
                    "head": f"{self.repo_owner}:{head}",
                    "base": base,
                    "state": "open",
                },
            )

            if response["success"] and response["data"]:
                pr = response["data"][0]
                return {"exists": True, "pr_number": pr["number"], "pull_request": pr}

            return {"exists": False}

        except Exception as e:
            logger.warning(f"Failed to check existing PR: {e}")
            return {"exists": False}

    def _check_commit_diff(self, head: str, base: str) -> Dict[str, Any]:
        """コミット差分の確認"""
        try:
            response = self._make_api_request(
                endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/compare/{base}...{head}",
                method="GET",
            )

            if response["success"]:
                data = response["data"]
                return {
                    "has_changes": data.get("ahead_by", 0) > 0,
                    "commits": data.get("commits", []),
                    "files_changed": data.get("files", []),
                }

            return {"has_changes": True}  # エラー時は作成を試みる

        except Exception as e:
            logger.warning(f"Failed to check commit diff: {e}")
            return {"has_changes": True}

    def _configure_pull_request(
        self,
        pr_number: int,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        reviewers: Optional[List[str]] = None,
        team_reviewers: Optional[List[str]] = None,
        milestone: Optional[int] = None,
    ) -> None:
        """PRの追加設定"""
        try:
            # Issue APIを使用してラベル、アサイン、マイルストーンを設定
            if labels or assignees or milestone:
                issue_update = {}

                if labels:
                    issue_update["labels"] = labels
                if assignees:
                    issue_update["assignees"] = assignees
                if milestone:
                    issue_update["milestone"] = milestone

                self._make_api_request(
                    endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/issues/{pr_number}",
                    method="PATCH",
                    json_data=issue_update,
                )

            # レビュアーの設定
            if reviewers or team_reviewers:
                review_request = {}

                if reviewers:
                    review_request["reviewers"] = reviewers
                if team_reviewers:
                    review_request["team_reviewers"] = team_reviewers

                self._make_api_request(
                    endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/pulls/{pr_number}/requested_reviewers",
                    method="POST",
                    json_data=review_request,
                )

        except Exception as e:
            logger.warning(f"Failed to configure PR #{pr_number}: {e}")

    def _check_merge_conflicts(self, pr_number: int) -> Dict[str, Any]:
        """マージコンフリクトのチェック"""
        try:
            response = self._make_api_request(
                endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/pulls/{pr_number}",
                method="GET",
            )

            if response["success"]:
                pr = response["data"]
                return {
                    "has_conflicts": pr.get("mergeable_state") == "dirty",
                    "mergeable": pr.get("mergeable", None),
                    "mergeable_state": pr.get("mergeable_state", "unknown"),
                    "message": self._get_conflict_message(pr.get("mergeable_state")),
                }

            return {
                "has_conflicts": False,
                "mergeable": None,
                "mergeable_state": "unknown",
                "message": "Unable to determine conflict status",
            }

        except Exception as e:
            logger.warning(f"Failed to check merge conflicts: {e}")
            return {
                "has_conflicts": False,
                "mergeable": None,
                "mergeable_state": "unknown",
                "message": str(e),
            }

    def _get_conflict_message(self, mergeable_state: str) -> str:
        """マージ状態に応じたメッセージを取得"""
        messages = {
            "clean": "No conflicts, ready to merge",
            "dirty": "Merge conflicts detected",
            "unstable": "Tests are failing",
            "blocked": "Merge is blocked",
            "behind": "Branch is behind base branch",
            "unknown": "Merge status unknown",
        }
        return messages.get(mergeable_state, "Unknown merge state")

    def _enable_auto_merge(self, pr_number: int) -> Dict[str, Any]:
        """自動マージを有効化（REST APIで即座にマージ）"""
        try:
            # PRの状態を確認
            pr_info = self._get_pull_request(pr_number)
            if not pr_info["success"]:
                return {"success": False, "error": "Failed to get PR info"}
            
            pr = pr_info["pull_request"]
            
            # マージ可能かチェック
            mergeable = pr.get("mergeable")
            if mergeable is None:
                # GitHubがまだ計算中の場合、少し待つ
                logger.info(f"PR #{pr_number} mergeable status is still being calculated, waiting...")
                import time
                time.sleep(2)
                # 再度取得
                pr_info = self._get_pull_request(pr_number)
                if pr_info["success"]:
                    pr = pr_info["pull_request"]
                    mergeable = pr.get("mergeable")
            
            if mergeable is False:
                return {"success": False, "error": "PR is not mergeable"}
            
            if pr.get("draft", False):
                return {"success": False, "error": "Cannot merge draft PR"}
            
            # マージ実行
            merge_response = self._make_api_request(
                endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/pulls/{pr_number}/merge",
                method="PUT",
                json_data={
                    "commit_title": f"Auto-merge PR #{pr_number}",
                    "commit_message": f"Automatically merged by Auto Issue Processor",
                    "merge_method": "merge"  # merge, squash, rebase から選択
                }
            )
            
            if merge_response["success"]:
                logger.info(f"Successfully auto-merged PR #{pr_number}")
                return {"success": True, "merged": True}
            else:
                logger.warning(f"Failed to auto-merge PR #{pr_number}: {merge_response.get('error')}")
                return {"success": False, "error": merge_response.get("error")}

        except Exception as e:
            logger.warning(f"Failed to enable auto-merge: {e}")
            return {"success": False, "error": str(e)}

    def _get_pull_request(self, pr_number: int) -> Dict[str, Any]:
        """PR情報を取得"""
        response = self._make_api_request(
            endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/pulls/{pr_number}",
            method="GET",
        )

        if response["success"]:
            return {"success": True, "pull_request": response["data"]}
        else:
            return {"success": False, "error": response["error"], "pull_request": None}

    def _make_api_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """APIリクエスト実行（リトライ機構付き）"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {self.token}",
            "User-Agent": "ElderGuild-GitHub-Integration",
        }

        last_error = None
        delay = self.retry_delay

        for attempt in range(self.max_retries):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                    timeout=30,
                )

                # レート制限チェック
                if (
                    response.status_code == 403
                    and "rate limit" in response.text.lower()
                ):
                    reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                    wait_time = max(0, reset_time - time.time())
                    logger.warning(f"Rate limit hit. Waiting {wait_time:.0f} seconds")
                    if wait_time > 0:
                        time.sleep(wait_time)
                    continue

                # 成功
                if response.status_code < 300:
                    return {
                        "success": True,
                        "data": response.json() if response.text else {},
                        "headers": dict(response.headers),
                    }

                # 認証エラー
                if response.status_code == 401:
                    return {
                        "success": False,
                        "error": "Authentication failed. Check your GitHub token.",
                        "status_code": response.status_code,
                    }

                # 権限エラー
                if (
                    response.status_code == 403
                    and "permission" in response.text.lower()
                ):
                    return {
                        "success": False,
                        "error": "Permission denied. Ensure your token has 'repo' scope.",
                        "status_code": response.status_code,
                    }

                # Not Found
                if response.status_code == 404:
                    return {
                        "success": False,
                        "error": f"Resource not found: {endpoint}",
                        "status_code": response.status_code,
                    }

                # Unprocessable Entity（バリデーションエラー）
                if response.status_code == 422:
                    error_data = response.json() if response.text else {}
                    errors = error_data.get("errors", [])
                    error_messages = [e.get("message", "") for e in errors]
                    return {
                        "success": False,
                        "error": f"Validation failed: {', '.join(error_messages)}",
                        "status_code": response.status_code,
                        "validation_errors": errors,
                    }

                # その他のクライアントエラー
                if 400 <= response.status_code < 500:
                    return {
                        "success": False,
                        "error": f"Client error: {response.status_code} - {response.text}",
                        "status_code": response.status_code,
                    }

                # サーバーエラー（リトライ）
                last_error = f"Server error: {response.status_code} - {response.text}"
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")

            except requests.exceptions.Timeout:
                last_error = "Request timeout"
                logger.warning(f"Attempt {attempt + 1} timed out")

            except requests.exceptions.ConnectionError:
                last_error = "Connection error"
                logger.warning(f"Attempt {attempt + 1} connection failed")

            except Exception as e:
                last_error = str(e)
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")

            # リトライ前の待機
            if attempt < self.max_retries - 1:
                logger.info(f"Retrying in {delay:.1f} seconds...")
                time.sleep(delay)
                delay *= self.backoff_factor

        return {
            "success": False,
            "error": f"All retries failed. Last error: {last_error}",
        }

    def create_pr_from_fork(
        self, title: str, head: str, base: str, head_repo: str, **kwargs
    ) -> Dict[str, Any]:
        """
        フォークからのPR作成

        Args:
            title: PRタイトル
            head: マージ元ブランチ
            base: マージ先ブランチ
            head_repo: フォーク元のリポジトリ（owner:branch形式）
            **kwargs: その他のPRパラメータ

        Returns:
            PR作成結果
        """
        # head を owner:branch 形式に変換
        full_head = f"{head_repo}:{head}" if ":" not in head else head_repo

        return self.create_pull_request(
            title=title, head=full_head, base=base, **kwargs
        )


# スタンドアロン関数（既存コードとの互換性）
def create_pull_request(
    title: str,
    head: str,
    base: str,
    repo_owner: Optional[str] = None,
    repo_name: Optional[str] = None,
    token: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    GitHub Pull Request作成のスタンドアロン関数

    Args:
        title: PRタイトル
        head: マージ元ブランチ
        base: マージ先ブランチ
        repo_owner: リポジトリオーナー
        repo_name: リポジトリ名
        token: GitHub token
        **kwargs: その他のPRパラメータ

    Returns:
        PR作成結果
    """
    implementation = GitHubCreatePullRequestImplementation(
        token=token, repo_owner=repo_owner, repo_name=repo_name
    )

    return implementation.create_pull_request(title, head, base, **kwargs)
