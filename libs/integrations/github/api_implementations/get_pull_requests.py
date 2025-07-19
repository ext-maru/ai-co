#!/usr/bin/env python3
"""
GitHub API get_pull_requests 完全実装
Iron Will基準準拠・ページネーション・フィルタリング・ステータス追跡対応
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

import requests

from libs.integrations.github.security import (
    SecurityViolationError,
    get_security_manager,
)

logger = logging.getLogger(__name__)


class GitHubGetPullRequestsImplementation:
    """GitHub Pull Requests取得の完全実装"""

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

        # レート制限管理
        self.rate_limit_remaining = None
        self.rate_limit_reset = None

        # キャッシュ設定
        self.enable_cache = True
        self.cache_ttl = 300  # 5分
        self._cache = {}

        self._validate_configuration()

    def _validate_configuration(self) -> None:
        """設定の検証"""
        if not self.token:
            logger.warning("GitHub token not set. API rate limits will be restrictive.")

        if not self.repo_owner or not self.repo_name:
            raise ValueError("Repository owner and name must be specified")

    def get_pull_requests(
        self,
        state: str = "open",
        head: Optional[str] = None,
        base: Optional[str] = None,
        sort: str = "created",
        direction: str = "desc",
        per_page: int = 30,
        max_results: Optional[int] = None,
        labels: Optional[List[str]] = None,
        milestone: Optional[Union[str, int]] = None,
        assignee: Optional[str] = None,
        creator: Optional[str] = None,
        mentioned: Optional[str] = None,
        reviews_requested: bool = False,
        include_draft: bool = True,
    ) -> Dict[str, Any]:
        """
        GitHub Pull Requestsを取得

        Args:
            state: PR状態 ("open", "closed", "all")
            head: フィルタ用のheadブランチ (user:branch形式も可)
            base: フィルタ用のbaseブランチ
            sort: ソート基準 ("created", "updated", "popularity", "long-running")
            direction: ソート順 ("asc", "desc")
            per_page: 1ページあたりの結果数 (最大100)
            max_results: 取得する最大結果数
            labels: ラベルフィルタ
            milestone: マイルストーンフィルタ (番号またはタイトル)
            assignee: アサイン者フィルタ
            creator: 作成者フィルタ
            mentioned: メンション者フィルタ
            reviews_requested: レビュー待ちのPRのみ
            include_draft: ドラフトPRを含むか

        Returns:
            Dict containing:
                - success: 成功フラグ
                - pull_requests: PR配列
                - total_count: 総PR数
                - statistics: 統計情報
                - metadata: メタデータ
                - error: エラー情報（失敗時）
        """
        try:
            # キャッシュチェック
            cache_key = self._generate_cache_key(locals())
            if self.enable_cache and cache_key in self._cache:
                cached_result = self._cache[cache_key]
                if time.time() - cached_result["timestamp"] < self.cache_ttl:
                    logger.info("Returning cached pull requests")
                    return cached_result["data"]

            # パラメータ構築
            params = {
                "state": state,
                "sort": sort,
                "direction": direction,
                "per_page": min(per_page, 100),
            }

            # オプションパラメータ追加
            if head:
                params["head"] = head if ":" in head else f"{self.repo_owner}:{head}"
            if base:
                params["base"] = base

            # ページネーション対応で全PR取得
            all_prs = []
            page = 1
            total_pages = None

            while True:
                params["page"] = page

                # APIコール（リトライ付き）
                response = self._make_api_request(
                    endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/pulls",
                    params=params,
                )

                if not response["success"]:
                    return response

                prs = response["data"]

                # 追加フィルタリング（APIでサポートされていないフィルタ）
                filtered_prs = self._apply_additional_filters(
                    prs,
                    labels=labels,
                    milestone=milestone,
                    assignee=assignee,
                    creator=creator,
                    mentioned=mentioned,
                    reviews_requested=reviews_requested,
                    include_draft=include_draft,
                )

                all_prs.extend(filtered_prs)

                # レート制限情報更新
                self._update_rate_limit_info(response.get("headers", {}))

                # ページネーション情報取得
                if "Link" in response.get("headers", {}):
                    links = self._parse_link_header(response["headers"]["Link"])
                    if "last" in links and total_pages is None:
                        last_url = links["last"]
                        total_pages = int(last_url.split("page=")[-1].split("&")[0])

                # 終了条件チェック
                if not prs:  # 結果が空
                    break

                if max_results and len(all_prs) >= max_results:
                    all_prs = all_prs[:max_results]
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
                        if wait_time > 0:
                            logger.info(
                                f"Waiting {wait_time:.0f} seconds for rate limit reset"
                            )
                            time.sleep(wait_time)

            # 詳細情報の取得（必要に応じて）
            enriched_prs = self._enrich_pull_requests(all_prs)

            # 統計情報の計算
            statistics = self._calculate_statistics(enriched_prs)

            result = {
                "success": True,
                "pull_requests": enriched_prs,
                "total_count": len(enriched_prs),
                "statistics": statistics,
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

            # キャッシュに保存
            if self.enable_cache:
                self._cache[cache_key] = {"timestamp": time.time(), "data": result}

            return result

        except Exception as e:
            logger.error(f"Failed to get pull requests: {e}")
            return {
                "success": False,
                "error": str(e),
                "pull_requests": [],
                "total_count": 0,
            }

    def _apply_additional_filters(
        self,
        prs: List[Dict[str, Any]],
        labels: Optional[List[str]] = None,
        milestone: Optional[Union[str, int]] = None,
        assignee: Optional[str] = None,
        creator: Optional[str] = None,
        mentioned: Optional[str] = None,
        reviews_requested: bool = False,
        include_draft: bool = True,
    ) -> List[Dict[str, Any]]:
        """追加フィルタリングを適用"""
        filtered = prs

        # ドラフトフィルタ
        if not include_draft:
            filtered = [pr for pr in filtered if not pr.get("draft", False)]

        # ラベルフィルタ
        if labels:
            filtered = [
                pr
                for pr in filtered
                if any(label["name"] in labels for label in pr.get("labels", []))
            ]

        # マイルストーンフィルタ
        if milestone is not None:
            if isinstance(milestone, int):
                filtered = [
                    pr
                    for pr in filtered
                    if pr.get("milestone", {}).get("number") == milestone
                ]
            else:
                filtered = [
                    pr
                    for pr in filtered
                    if pr.get("milestone", {}).get("title") == milestone
                ]

        # アサイン者フィルタ
        if assignee:
            filtered = [
                pr
                for pr in filtered
                if any(user["login"] == assignee for user in pr.get("assignees", []))
            ]

        # 作成者フィルタ
        if creator:
            filtered = [
                pr for pr in filtered if pr.get("user", {}).get("login") == creator
            ]

        # メンションフィルタ（本文内でのメンションをチェック）
        if mentioned:
            mention_pattern = f"@{mentioned}"
            filtered = [pr for pr in filtered if mention_pattern in pr.get("body", "")]

        # レビュー待ちフィルタ
        if reviews_requested:
            filtered = [
                pr
                for pr in filtered
                if pr.get("requested_reviewers", []) or pr.get("requested_teams", [])
            ]

        return filtered

    def _enrich_pull_requests(self, prs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """PR情報を充実させる"""
        enriched = []

        for pr in prs:
            # 基本情報はそのまま保持
            enriched_pr = pr.copy()

            # 追加情報を計算
            enriched_pr["age_days"] = self._calculate_age_days(pr["created_at"])
            enriched_pr["last_updated_days"] = self._calculate_age_days(
                pr["updated_at"]
            )

            # ステータス情報
            enriched_pr["status"] = {
                "is_draft": pr.get("draft", False),
                "is_merged": pr.get("merged", False),
                "is_closed": pr["state"] == "closed",
                "has_conflicts": (
                    pr.get("mergeable_state") == "dirty"
                    if "mergeable_state" in pr
                    else None
                ),
                "review_status": self._get_review_status(pr),
            }

            # サイズ情報
            enriched_pr["size_info"] = {
                "additions": pr.get("additions", 0),
                "deletions": pr.get("deletions", 0),
                "changed_files": pr.get("changed_files", 0),
                "total_changes": pr.get("additions", 0) + pr.get("deletions", 0),
            }

            enriched.append(enriched_pr)

        return enriched

    def _calculate_age_days(self, date_str: str) -> float:
        """作成からの経過日数を計算"""
        try:
            created_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            age = datetime.now(created_date.tzinfo) - created_date
            return age.total_seconds() / 86400  # 日数に変換
        except Exception:
            return 0

    def _get_review_status(self, pr: Dict[str, Any]) -> str:
        """レビューステータスを取得"""
        if pr.get("draft"):
            return "draft"
        elif pr.get("requested_reviewers") or pr.get("requested_teams"):
            return "review_requested"
        elif pr.get("review_comments", 0) > 0:
            return "changes_requested"  # 簡易判定
        else:
            return "ready"

    def _calculate_statistics(self, prs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """統計情報を計算"""
        if not prs:
            return {
                "total": 0,
                "by_state": {},
                "by_author": {},
                "average_age_days": 0,
                "average_size": 0,
            }

        # 状態別カウント
        by_state = {
            "open": sum(
                1 for pr in prs if pr["state"] == "open" and not pr.get("draft")
            ),
            "draft": sum(1 for pr in prs if pr.get("draft")),
            "closed": sum(
                1 for pr in prs if pr["state"] == "closed" and not pr.get("merged")
            ),
            "merged": sum(1 for pr in prs if pr.get("merged")),
        }

        # 作者別カウント
        by_author = {}
        for pr in prs:
            author = pr.get("user", {}).get("login", "unknown")
            by_author[author] = by_author.get(author, 0) + 1

        # 平均経過日数
        ages = [pr.get("age_days", 0) for pr in prs if pr["state"] == "open"]
        average_age = sum(ages) / len(ages) if ages else 0

        # 平均サイズ
        sizes = [pr.get("size_info", {}).get("total_changes", 0) for pr in prs]
        average_size = sum(sizes) / len(sizes) if sizes else 0

        return {
            "total": len(prs),
            "by_state": by_state,
            "by_author": by_author,
            "average_age_days": round(average_age, 2),
            "average_size": round(average_size, 2),
            "oldest_pr": max(prs, key=lambda x: x.get("age_days", 0)) if prs else None,
            "largest_pr": (
                max(prs, key=lambda x: x.get("size_info", {}).get("total_changes", 0))
                if prs
                else None
            ),
        }

    def get_pull_request_by_number(self, pr_number: int) -> Dict[str, Any]:
        """
        特定のPRを番号で取得

        Args:
            pr_number: PR番号

        Returns:
            Dict containing:
                - success: 成功フラグ
                - pull_request: PR情報
                - reviews: レビュー情報
                - comments: コメント情報
                - error: エラー情報（失敗時）
        """
        try:
            # PR基本情報取得
            pr_response = self._make_api_request(
                endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/pulls/{pr_number}"
            )

            if not pr_response["success"]:
                return {
                    "success": False,
                    "error": pr_response["error"],
                    "pull_request": None,
                }

            pr = pr_response["data"]

            # レビュー情報取得
            reviews_response = self._make_api_request(
                endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/pulls/{pr_number}/reviews"
            )

            reviews = reviews_response["data"] if reviews_response["success"] else []

            # コメント情報取得
            comments_response = self._make_api_request(
                endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/pulls/{pr_number}/comments"
            )

            comments = comments_response["data"] if comments_response["success"] else []

            # 充実した情報を含めて返す
            enriched_pr = self._enrich_pull_requests([pr])[0]

            return {
                "success": True,
                "pull_request": enriched_pr,
                "reviews": reviews,
                "comments": comments,
                "review_summary": self._summarize_reviews(reviews),
            }

        except Exception as e:
            logger.error(f"Failed to get PR #{pr_number}: {e}")
            return {"success": False, "error": str(e), "pull_request": None}

    def _summarize_reviews(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """レビューサマリーを作成"""
        if not reviews:
            return {
                "total_reviews": 0,
                "approved": 0,
                "changes_requested": 0,
                "commented": 0,
                "dismissed": 0,
                "latest_review": None,
            }

        summary = {
            "total_reviews": len(reviews),
            "approved": sum(1 for r in reviews if r.get("state") == "APPROVED"),
            "changes_requested": sum(
                1 for r in reviews if r.get("state") == "CHANGES_REQUESTED"
            ),
            "commented": sum(1 for r in reviews if r.get("state") == "COMMENTED"),
            "dismissed": sum(1 for r in reviews if r.get("state") == "DISMISSED"),
            "latest_review": (
                max(reviews, key=lambda x: x.get("submitted_at", ""))
                if reviews
                else None
            ),
        }

        return summary

    def search_pull_requests(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        PR検索（GitHub Search API使用）

        Args:
            query: 検索クエリ
            **kwargs: 追加の検索パラメータ

        Returns:
            Dict containing:
                - success: 成功フラグ
                - pull_requests: 検索結果
                - total_count: 総件数
                - error: エラー情報（失敗時）
        """
        try:
            # リポジトリスコープとPRタイプを追加
            full_query = f"{query} repo:{self.repo_owner}/{self.repo_name} type:pr"

            params = {
                "q": full_query,
                "per_page": kwargs.get("per_page", 30),
                "sort": kwargs.get("sort", "created"),
                "order": kwargs.get("order", "desc"),
            }

            response = self._make_api_request(endpoint="/search/issues", params=params)

            if response["success"]:
                prs = response["data"].get("items", [])
                enriched_prs = self._enrich_pull_requests(prs)

                return {
                    "success": True,
                    "pull_requests": enriched_prs,
                    "total_count": response["data"].get("total_count", 0),
                }
            else:
                return {
                    "success": False,
                    "error": response["error"],
                    "pull_requests": [],
                    "total_count": 0,
                }

        except Exception as e:
            logger.error(f"Failed to search pull requests: {e}")
            return {
                "success": False,
                "error": str(e),
                "pull_requests": [],
                "total_count": 0,
            }

    def _generate_cache_key(self, params: Dict[str, Any]) -> str:
        """キャッシュキーを生成"""
        # 関数ローカル変数を除外
        filtered_params = {
            k: v
            for k, v in params.items()
            if k not in ["self", "cache_key"] and v is not None
        }
        return f"get_prs_{json.dumps(filtered_params, sort_keys=True)}"

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
            "User-Agent": "ElderGuild-GitHub-Integration",
        }

        if self.token:
            headers["Authorization"] = f"token {self.token}"

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

                # クライアントエラー（4xx）はリトライしない
                if 400 <= response.status_code < 500:
                    return {
                        "success": False,
                        "error": f"Client error: {response.status_code} - {response.text}",
                        "status_code": response.status_code,
                    }

                # サーバーエラー（5xx）はリトライ
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


# スタンドアロン関数（既存コードとの互換性）
def get_pull_requests(
    repo_owner: Optional[str] = None,
    repo_name: Optional[str] = None,
    token: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    GitHub Pull Requests取得のスタンドアロン関数

    Args:
        repo_owner: リポジトリオーナー
        repo_name: リポジトリ名
        token: GitHub token
        **kwargs: その他のパラメータ

    Returns:
        Pull Requests取得結果
    """
    implementation = GitHubGetPullRequestsImplementation(
        token=token, repo_owner=repo_owner, repo_name=repo_name
    )

    return implementation.get_pull_requests(**kwargs)
