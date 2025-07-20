#!/usr/bin/env python3
"""
GitHub Create Pull Request API実装

プルリクエスト作成に特化したAPIクライアント実装。
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import GitHubAPIBase

logger = logging.getLogger(__name__)


class GitHubCreatePullRequestImplementation(GitHubAPIBase):
    """GitHub Create Pull Request API実装クラス"""

    def __init__(self, token: str, repo_owner: str, repo_name: str):
        """
        初期化

        Args:
            token: GitHub APIトークン
            repo_owner: リポジトリオーナー
            repo_name: リポジトリ名
        """
        super().__init__(token, repo_owner, repo_name)

        # PR作成設定
        self.max_retries = 3
        self.retry_delay = 1.0
        self.backoff_factor = 2.0

        # コンフリクト検出設定
        self.check_conflicts = True
        self.auto_merge_enabled = False

        self._validate_configuration()

    def _validate_configuration(self) -> None:
        """設定の検証"""
        if not self.repo_owner:
            raise ValueError("Repository owner must be specified")

        if not self.repo_name:
            raise ValueError("Repository name must be specified")

        logger.info(
            f"CreatePullRequest client initialized for {self.repo_owner}/{self.repo_name}"
        )

    def create_pull_request(
        self,
        title: str,
        head: str,
        base: str,
        body: Optional[str] = None,
        draft: bool = False,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        reviewers: Optional[List[str]] = None,
        team_reviewers: Optional[List[str]] = None,
        milestone: Optional[int] = None,
        maintainer_can_modify: bool = True,
    ) -> Dict[str, Any]:
        """
        プルリクエストを作成

        Args:
            title: PRタイトル
            head: マージ元ブランチ
            base: マージ先ブランチ
            body: PR本文
            draft: ドラフトとして作成
            labels: ラベルリスト
            assignees: アサイン者リスト
            reviewers: レビュアーリスト
            team_reviewers: チームレビュアーリスト
            milestone: マイルストーンID
            maintainer_can_modify: メンテナーの編集許可

        Returns:
            Dict[str, Any]: PR作成結果
                - success: 成功フラグ
                - pull_request: PR情報（成功時）
                - error: エラーメッセージ（失敗時）
                - conflict_status: コンフリクト状態情報
        """
        try:
            # パラメータ検証
            validation = self._validate_pr_params(title, head, base)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": validation["error"],
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

            # 既存PRのチェック
            existing_pr = self._check_existing_pr(head, base)
            if existing_pr["exists"]:
                return {
                    "success": False,
                    "error": (
                        f"Pull request already exists: "
                        f"#{existing_pr['pr_number']} - {existing_pr['pr_title']}"
                    ),
                    "pull_request": existing_pr.get("pull_request"),
                }

            # PR作成前のブランチ比較
            comparison = self._compare_branches(base, head)
            if not comparison["success"]:
                return {
                    "success": False,
                    "error": comparison["error"],
                    "pull_request": None,
                }

            if comparison["commits"] == 0:
                return {
                    "success": False,
                    "error": "No commits between base and head branches",
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
                return {
                    "success": False,
                    "error": f"Base branch '{base}' not found",
                }

            # ヘッドブランチの確認
            head_response = self._make_api_request(
                endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/branches/{head}",
                method="GET",
            )

            if not head_response["success"]:
                return {
                    "success": False,
                    "error": f"Head branch '{head}' not found",
                }

            return {"success": True}

        except Exception as e:
            logger.error(f"Failed to check branches: {e}")
            return {"success": False, "error": str(e)}

    def _check_existing_pr(self, head: str, base: str) -> Dict[str, Any]:
        """既存PRのチェック"""
        try:
            # 同じブランチ間のオープンPRを検索
            response = self._make_api_request(
                endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/pulls",
                method="GET",
                params={"head": f"{self.repo_owner}:{head}", "base": base, "state": "open"},
            )

            if not response["success"]:
                return {"exists": False}

            prs = response["data"]
            if prs and len(prs) > 0:
                pr = prs[0]
                return {
                    "exists": True,
                    "pr_number": pr["number"],
                    "pr_title": pr["title"],
                    "pull_request": pr,
                }

            return {"exists": False}

        except Exception as e:
            logger.warning(f"Failed to check existing PR: {e}")
            return {"exists": False}

    def _compare_branches(self, base: str, head: str) -> Dict[str, Any]:
        """ブランチ間の差分を比較"""
        try:
            response = self._make_api_request(
                endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/compare/{base}...{head}",
                method="GET",
            )

            if not response["success"]:
                return {
                    "success": False,
                    "error": "Failed to compare branches",
                }

            data = response["data"]
            return {
                "success": True,
                "commits": data.get("total_commits", 0),
                "files_changed": len(data.get("files", [])),
                "additions": sum(f.get("additions", 0) for f in data.get("files", [])),
                "deletions": sum(f.get("deletions", 0) for f in data.get("files", [])),
            }

        except Exception as e:
            logger.error(f"Failed to compare branches: {e}")
            return {"success": False, "error": str(e)}

    def _configure_pull_request(
        self,
        pr_number: int,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        reviewers: Optional[List[str]] = None,
        team_reviewers: Optional[List[str]] = None,
        milestone: Optional[int] = None,
    ) -> None:
        """PR追加設定"""
        try:
            # ラベル設定
            if labels:
                self._make_api_request(
                    endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/issues/{pr_number}/labels",
                    method="POST",
                    json_data={"labels": labels},
                )

            # アサイン設定
            if assignees:
                self._make_api_request(
                    endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/issues/{pr_number}/assignees",
                    method="POST",
                    json_data={"assignees": assignees},
                )

            # レビュアー設定
            if reviewers or team_reviewers:
                review_data = {}
                if reviewers:
                    review_data["reviewers"] = reviewers
                if team_reviewers:
                    review_data["team_reviewers"] = team_reviewers

                self._make_api_request(
                    endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/pulls/{pr_number}/requested_reviewers",
                    method="POST",
                    json_data=review_data,
                )

            # マイルストーン設定
            if milestone:
                self._make_api_request(
                    endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/issues/{pr_number}",
                    method="PATCH",
                    json_data={"milestone": milestone},
                )

        except Exception as e:
            logger.warning(f"Failed to configure PR #{pr_number}: {e}")

    def _check_merge_conflicts(self, pr_number: int) -> Dict[str, Any]:
        """マージコンフリクトのチェック"""
        try:
            pr_data = self._get_pull_request(pr_number)
            if pr_data["success"]:
                pr = pr_data["pull_request"]
                return {
                    "has_conflicts": pr.get("mergeable_state") == "dirty",
                    "mergeable": pr.get("mergeable", None),
                    "mergeable_state": pr.get("mergeable_state", "unknown"),
                    "message": self._get_conflict_message(pr.get("mergeable_state")),
                }

            return {
                "has_conflicts": None,
                "mergeable": None,
                "mergeable_state": "unknown",
                "message": "Unable to check merge conflicts",
            }

        except Exception as e:
            logger.warning(f"Failed to check merge conflicts: {e}")
            return {
                "has_conflicts": None,
                "mergeable": None,
                "mergeable_state": "unknown",
                "message": str(e),
            }

    def _get_conflict_message(self, mergeable_state: Optional[str]) -> str:
        """マージ状態のメッセージを取得"""
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
            return {"success": False, "error": response.get("error")}