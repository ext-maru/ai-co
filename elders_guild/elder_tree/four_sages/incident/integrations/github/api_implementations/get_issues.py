#!/usr/bin/env python3
"""
GitHub API get_issues 完全実装
Iron Will基準準拠・エラーハンドリング・リトライ機構・ページネーション対応
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests

from libs.integrations.github.security import (
    SecurityViolationError,
    get_security_manager,
)

logger = logging.getLogger(__name__)

class GitHubGetIssuesImplementation:
    """GitHub Issues取得の完全実装"""

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
        self.retry_delay = 1.0  # 初期遅延（秒）
        self.backoff_factor = 2.0  # 指数バックオフ係数

        # レート制限管理
        self.rate_limit_remaining = None
        self.rate_limit_reset = None

        self._validate_configuration()

    def _validate_configuration(self) -> None:
        """設定の検証"""
        if not self.token:
            logger.warning("GitHub token not set. API rate limits will be restrictive.")

        if not self.repo_owner or not self.repo_name:
            raise ValueError("Repository owner and name must be specified")

    def get_issues(
        self,
        state: str = "open",
        labels: Optional[List[str]] = None,
        assignee: Optional[str] = None,
        creator: Optional[str] = None,
        milestone: Optional[str] = None,
        since: Optional[str] = None,
        sort: str = "created",
        direction: str = "desc",
        per_page: int = 30,
        max_results: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        GitHub Issuesを取得

        Args:
            state: Issue状態 ("open", "closed", "all")
            labels: ラベルフィルタ（カンマ区切り）
            assignee: アサイン者フィルタ
            creator: 作成者フィルタ
            milestone: マイルストーンフィルタ
            since: この日時以降のIssueのみ (ISO 8601形式)
            sort: ソート基準 ("created", "updated", "comments")
            direction: ソート順 ("asc", "desc")
            per_page: 1ページあたりの結果数 (最大100)
            max_results: 取得する最大結果数

        Returns:
            Dict containing:
                - success: 成功フラグ
                - issues: Issue配列
                - total_count: 総Issue数
                - metadata: メタデータ（ページネーション情報等）
                - error: エラー情報（失敗時）
        """
        try:
            # パラメータ構築
            params = {
                "state": state,
                "sort": sort,
                "direction": direction,
                "per_page": min(per_page, 100),  # GitHubの最大値は100
            }

            # オプションパラメータ追加
            if labels:
                params["labels"] = (
                    ",".join(labels) if isinstance(labels, list) else labels
                )
            if assignee:
                params["assignee"] = assignee
            if creator:
                params["creator"] = creator
            if milestone:
                params["milestone"] = milestone
            if since:
                params["since"] = since

            # ページネーション対応で全Issue取得
            all_issues = []
            page = 1
            total_pages = None

            while True:
                params["page"] = page

                # APIコール（リトライ付き）
                response = self._make_api_request(
                    endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/issues",
                    params=params,
                )

                if not response["success"]:
                    return response

                issues = response["data"]
                all_issues.extend(issues)

                # レート制限情報更新
                self._update_rate_limit_info(response.get("headers", {}))

                # ページネーション情報取得
                if "Link" in response.get("headers", {}):
                    links = self._parse_link_header(response["headers"]["Link"])
                    if "last" in links and total_pages is None:
                        # 最終ページ番号を取得
                        last_url = links["last"]
                        total_pages = int(last_url.split("page=")[-1].split("&")[0])

                # 終了条件チェック
                if not issues:  # 結果が空
                    break

                if max_results and len(all_issues) >= max_results:
                    all_issues = all_issues[:max_results]
                    break

                if "next" not in response.get("headers", {}).get("Link", ""):
                    break  # 次ページなし

                page += 1

                # レート制限チェック
                if self.rate_limit_remaining and self.rate_limit_remaining < 10:
                    logger.warning(
                        f"Rate limit low: {self.rate_limit_remaining} remaining"
                    )
                    if self.rate_limit_reset:
                        wait_time = max(0, self.rate_limit_reset - time.time())
                        if not (wait_time > 0):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if wait_time > 0:
                            logger.info(
                                f"Waiting {wait_time:0.0f} seconds for rate limit reset"
                            )
                            time.sleep(wait_time)

            # Pull RequestをIssueから除外（GitHubはPRもIssueとして返す）
            filtered_issues = [
                issue for issue in all_issues if "pull_request" not in issue
            ]

            return {
                "success": True,
                "issues": filtered_issues,
                "total_count": len(filtered_issues),
                "metadata": {
                    "parameters": params,
                    "total_pages": total_pages or page,
                    "rate_limit_remaining": self.rate_limit_remaining,
                    "rate_limit_reset": (
                        datetime.fromtimestamp(self.rate_limit_reset).isoformat()
                        if self.rate_limit_reset
                        else None
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Failed to get issues: {e}")
            return {"success": False, "error": str(e), "issues": [], "total_count": 0}

    def _make_api_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        APIリクエスト実行（リトライ機構付き）

        Args:
            endpoint: APIエンドポイント
            method: HTTPメソッド
            params: クエリパラメータ
            json_data: JSONボディデータ

        Returns:
            Dict containing:
                - success: 成功フラグ
                - data: レスポンスデータ
                - headers: レスポンスヘッダー
                - error: エラー情報（失敗時）
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ElderGuild-GitHub-Integration",
        }

        if self.token:
            headers["Authorization"] = f"token {self.token}"

        # リトライループ
        last_error = None
        delay = self.retry_delay

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
                    logger.warning(f"Rate limit hit. Waiting {wait_time:0.0f} seconds")
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

                # クライアントエラー（4xx）はリトライしない
                if 400 <= response.status_code < 500:
                    return {
                        "success": False,
                        "error": f"Client error: {response.status_code} - {response.text}",
                        "status_code": response.status_code,
                    }

                # サーバーエラー（5xx）はリトライ
                last_error = f"Server error: {response.status_code} - {response.text}"

            except requests.exceptions.Timeout:
                last_error = "Request timeout"

            except requests.exceptions.ConnectionError:
                last_error = "Connection error"

            except Exception as e:
                last_error = str(e)

            # 最後の試行でなければ待機

                logger.info(f"Retrying in {delay:0.1f} seconds...")
                time.sleep(delay)
                delay *= self.backoff_factor  # 指数バックオフ

        # すべてのリトライが失敗
        return {
            "success": False,
            "error": f"All retries failed. Last error: {last_error}",
        }

    def _update_rate_limit_info(self, headers: Dict[str, str]) -> None:
        """レート制限情報を更新"""
        if "X-RateLimit-Remaining" in headers:
            self.rate_limit_remaining = int(headers["X-RateLimit-Remaining"])

        if "X-RateLimit-Reset" in headers:
            self.rate_limit_reset = int(headers["X-RateLimit-Reset"])

    def _parse_link_header(self, link_header: str) -> Dict[str, str]:
        """Linkヘッダーをパース"""
        links = {}

        for link in link_header.split(","):
            parts = link.strip().split(";")
            if len(parts) == 2:
                url = parts[0].strip("<>")
                rel = parts[1].split("=")[1].strip('"')
                links[rel] = url

        return links

    def get_issue_by_number(self, issue_number: int) -> Dict[str, Any]:
        """
        特定のIssueを番号で取得

        Args:
            issue_number: Issue番号

        Returns:
            Dict containing:
                - success: 成功フラグ
                - issue: Issue情報
                - error: エラー情報（失敗時）
        """
        try:
            response = self._make_api_request(
                endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}"
            )

            if response["success"]:
                return {"success": True, "issue": response["data"]}
            else:
                return {"success": False, "error": response["error"], "issue": None}

        except Exception as e:
            logger.error(f"Failed to get issue #{issue_number}: {e}")
            return {"success": False, "error": str(e), "issue": None}

    def search_issues(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Issue検索（GitHub Search API使用）

        Args:
            query: 検索クエリ
            **kwargs: 追加の検索パラメータ

        Returns:
            Dict containing:
                - success: 成功フラグ
                - issues: 検索結果
                - total_count: 総件数
                - error: エラー情報（失敗時）
        """
        try:
            # リポジトリスコープを追加
            full_query = f"{query} repo:{self.repo_owner}/{self.repo_name}"

            params = {
                "q": full_query,
                "per_page": kwargs.get("per_page", 30),
                "sort": kwargs.get("sort", "created"),
                "order": kwargs.get("order", "desc"),
            }

            response = self._make_api_request(endpoint="/search/issues", params=params)

            if response["success"]:
                return {
                    "success": True,
                    "issues": response["data"].get("items", []),
                    "total_count": response["data"].get("total_count", 0),
                }
            else:
                return {
                    "success": False,
                    "error": response["error"],
                    "issues": [],
                    "total_count": 0,
                }

        except Exception as e:
            logger.error(f"Failed to search issues: {e}")
            return {"success": False, "error": str(e), "issues": [], "total_count": 0}

# スタンドアロン関数（既存コードとの互換性）
def get_issues(
    repo_owner: Optional[str] = None,
    repo_name: Optional[str] = None,
    token: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    GitHub Issues取得のスタンドアロン関数

    Args:
        repo_owner: リポジトリオーナー
        repo_name: リポジトリ名
        token: GitHub token
        **kwargs: その他のパラメータ

    Returns:
        Issues取得結果
    """
    implementation = GitHubGetIssuesImplementation(
        token=token, repo_owner=repo_owner, repo_name=repo_name
    )

    return implementation.get_issues(**kwargs)
