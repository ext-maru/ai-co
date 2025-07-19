#!/usr/bin/env python3
"""
GitHub API update_issue 完全実装
Iron Will基準準拠・バリデーション・エラーハンドリング・監査ログ対応
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import requests

from libs.integrations.github.security import (
    SecurityViolationError,
    get_security_manager,
)

logger = logging.getLogger(__name__)


class GitHubUpdateIssueImplementation:
    """GitHub Issue更新の完全実装"""

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

        # 監査ログ設定
        self.enable_audit_log = True
        self.audit_log_file = "logs/github_issue_updates.log"

        self._validate_configuration()
        self._setup_audit_logger()

    def _validate_configuration(self) -> None:
        """設定の検証"""
        if not self.token:
            raise ValueError("GitHub token is required for issue updates")

        if not self.repo_owner or not self.repo_name:
            raise ValueError("Repository owner and name must be specified")

    def _setup_audit_logger(self) -> None:
        """監査ログの設定"""
        if self.enable_audit_log:
            os.makedirs(os.path.dirname(self.audit_log_file), exist_ok=True)

            self.audit_logger = logging.getLogger("github_issue_audit")
            handler = logging.FileHandler(self.audit_log_file)
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self.audit_logger.addHandler(handler)
            self.audit_logger.setLevel(logging.INFO)

    def update_issue(
        self,
        issue_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        milestone: Optional[int] = None,
        state_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        GitHub Issueを更新

        Args:
            issue_number: Issue番号
            title: 新しいタイトル
            body: 新しい本文
            state: 状態 ("open" or "closed")
            labels: ラベルリスト
            assignees: アサイン者リスト
            milestone: マイルストーン番号
            state_reason: クローズ理由 ("completed", "not_planned", "reopened")

        Returns:
            Dict containing:
                - success: 成功フラグ
                - issue: 更新後のIssue情報
                - changes: 変更内容
                - error: エラー情報（失敗時）
        """
        try:
            # 入力検証
            validation_result = self._validate_update_params(
                issue_number=issue_number, state=state, state_reason=state_reason
            )

            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": validation_result["error"],
                    "issue": None,
                }

            # 現在のIssue情報を取得（変更前の状態記録用）
            current_issue = self._get_current_issue(issue_number)
            if not current_issue["success"]:
                return current_issue

            # 更新データ構築
            update_data = self._build_update_data(
                title=title,
                body=body,
                state=state,
                labels=labels,
                assignees=assignees,
                milestone=milestone,
                state_reason=state_reason,
            )

            if not update_data:
                return {
                    "success": False,
                    "error": "No update parameters provided",
                    "issue": current_issue["issue"],
                }

            # APIコール実行
            response = self._make_api_request(
                endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}",
                method="PATCH",
                json_data=update_data,
            )

            if not response["success"]:
                return {"success": False, "error": response["error"], "issue": None}

            # 変更内容の記録
            changes = self._calculate_changes(
                before=current_issue["issue"], after=response["data"]
            )

            # 監査ログ記録
            self._log_audit_event(
                action="update_issue",
                issue_number=issue_number,
                changes=changes,
                user=self._get_current_user(),
            )

            return {"success": True, "issue": response["data"], "changes": changes}

        except Exception as e:
            logger.error(f"Failed to update issue #{issue_number}: {e}")
            return {"success": False, "error": str(e), "issue": None}

    def _validate_update_params(
        self, issue_number: int, state: Optional[str], state_reason: Optional[str]
    ) -> Dict[str, Any]:
        """更新パラメータの検証"""
        if not isinstance(issue_number, int) or issue_number <= 0:
            return {"valid": False, "error": "Invalid issue number"}

        if state and state not in ["open", "closed"]:
            return {
                "valid": False,
                "error": f"Invalid state: {state}. Must be 'open' or 'closed'",
            }

        if state_reason and state_reason not in [
            "completed",
            "not_planned",
            "reopened",
        ]:
            return {"valid": False, "error": f"Invalid state_reason: {state_reason}"}

        return {"valid": True}

    def _get_current_issue(self, issue_number: int) -> Dict[str, Any]:
        """現在のIssue情報を取得"""
        response = self._make_api_request(
            endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}",
            method="GET",
        )

        if response["success"]:
            return {"success": True, "issue": response["data"]}
        else:
            return {
                "success": False,
                "error": f"Failed to get current issue: {response['error']}",
                "issue": None,
            }

    def _build_update_data(
        self,
        title: Optional[str],
        body: Optional[str],
        state: Optional[str],
        labels: Optional[List[str]],
        assignees: Optional[List[str]],
        milestone: Optional[int],
        state_reason: Optional[str],
    ) -> Dict[str, Any]:
        """更新データを構築"""
        update_data = {}

        if title is not None:
            update_data["title"] = title

        if body is not None:
            update_data["body"] = body

        if state is not None:
            update_data["state"] = state

        if labels is not None:
            update_data["labels"] = labels

        if assignees is not None:
            update_data["assignees"] = assignees

        if milestone is not None:
            update_data["milestone"] = milestone

        if state_reason is not None:
            update_data["state_reason"] = state_reason

        return update_data

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

                # 権限エラー
                if response.status_code == 401:
                    return {
                        "success": False,
                        "error": "Authentication failed. Check your GitHub token.",
                        "status_code": response.status_code,
                    }

                # 権限不足
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
                        "error": f"Issue #{endpoint.split('/')[-1]} not found",
                        "status_code": response.status_code,
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

    def _calculate_changes(
        self, before: Dict[str, Any], after: Dict[str, Any]
    ) -> Dict[str, Any]:
        """変更内容を計算"""
        changes = {}

        # 比較対象フィールド
        fields = ["title", "body", "state", "labels", "assignees", "milestone"]

        for field in fields:
            before_value = before.get(field)
            after_value = after.get(field)

            # ラベルとアサイン者は配列なので特別処理
            if field in ["labels", "assignees"]:
                before_list = self._extract_list_field(before_value, field)
                after_list = self._extract_list_field(after_value, field)

                if before_list != after_list:
                    changes[field] = {"before": before_list, "after": after_list}

            # マイルストーンは番号で比較
            elif field == "milestone":
                before_milestone = before_value.get("number") if before_value else None
                after_milestone = after_value.get("number") if after_value else None

                if before_milestone != after_milestone:
                    changes[field] = {
                        "before": before_milestone,
                        "after": after_milestone,
                    }

            # その他のフィールド
            elif before_value != after_value:
                changes[field] = {"before": before_value, "after": after_value}

        return changes

    def _extract_list_field(self, value: Any, field: str) -> List[str]:
        """リストフィールドを抽出"""
        if not value:
            return []

        if field == "labels":
            return [label["name"] for label in value] if isinstance(value, list) else []
        elif field == "assignees":
            return [user["login"] for user in value] if isinstance(value, list) else []

        return []

    def _get_current_user(self) -> str:
        """現在のユーザーを取得"""
        try:
            response = self._make_api_request("/user", method="GET")
            if response["success"]:
                return response["data"].get("login", "unknown")
        except:
            pass

        return "unknown"

    def _log_audit_event(
        self, action: str, issue_number: int, changes: Dict[str, Any], user: str
    ) -> None:
        """監査イベントをログに記録"""
        if not self.enable_audit_log:
            return

        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "issue_number": issue_number,
            "repository": f"{self.repo_owner}/{self.repo_name}",
            "user": user,
            "changes": changes,
        }

        self.audit_logger.info(json.dumps(audit_entry, ensure_ascii=False))

    def add_comment(self, issue_number: int, body: str) -> Dict[str, Any]:
        """
        Issueにコメントを追加

        Args:
            issue_number: Issue番号
            body: コメント本文

        Returns:
            Dict containing:
                - success: 成功フラグ
                - comment: 作成されたコメント
                - error: エラー情報（失敗時）
        """
        try:
            if not body:
                return {
                    "success": False,
                    "error": "Comment body cannot be empty",
                    "comment": None,
                }

            response = self._make_api_request(
                endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}/comments",
                method="POST",
                json_data={"body": body},
            )

            if response["success"]:
                # 監査ログ
                self._log_audit_event(
                    action="add_comment",
                    issue_number=issue_number,
                    changes={"comment": body},
                    user=self._get_current_user(),
                )

                return {"success": True, "comment": response["data"]}
            else:
                return {"success": False, "error": response["error"], "comment": None}

        except Exception as e:
            logger.error(f"Failed to add comment to issue #{issue_number}: {e}")
            return {"success": False, "error": str(e), "comment": None}

    def add_labels(self, issue_number: int, labels: List[str]) -> Dict[str, Any]:
        """
        Issueにラベルを追加

        Args:
            issue_number: Issue番号
            labels: 追加するラベルリスト

        Returns:
            Dict containing:
                - success: 成功フラグ
                - labels: 更新後の全ラベル
                - error: エラー情報（失敗時）
        """
        try:
            if not labels:
                return {
                    "success": False,
                    "error": "Labels list cannot be empty",
                    "labels": [],
                }

            response = self._make_api_request(
                endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}/labels",
                method="POST",
                json_data={"labels": labels},
            )

            if response["success"]:
                return {"success": True, "labels": response["data"]}
            else:
                return {"success": False, "error": response["error"], "labels": []}

        except Exception as e:
            logger.error(f"Failed to add labels to issue #{issue_number}: {e}")
            return {"success": False, "error": str(e), "labels": []}

    def remove_label(self, issue_number: int, label_name: str) -> Dict[str, Any]:
        """
        Issueからラベルを削除

        Args:
            issue_number: Issue番号
            label_name: 削除するラベル名

        Returns:
            Dict containing:
                - success: 成功フラグ
                - labels: 更新後の全ラベル
                - error: エラー情報（失敗時）
        """
        try:
            response = self._make_api_request(
                endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}/labels/{label_name}",
                method="DELETE",
            )

            if response["success"]:
                # 削除後の全ラベルを取得
                labels_response = self._make_api_request(
                    endpoint=f"/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}/labels",
                    method="GET",
                )

                return {"success": True, "labels": labels_response.get("data", [])}
            else:
                return {"success": False, "error": response["error"], "labels": []}

        except Exception as e:
            logger.error(f"Failed to remove label from issue #{issue_number}: {e}")
            return {"success": False, "error": str(e), "labels": []}


# スタンドアロン関数（既存コードとの互換性）
def update_issue(
    issue_number: int,
    repo_owner: Optional[str] = None,
    repo_name: Optional[str] = None,
    token: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    GitHub Issue更新のスタンドアロン関数

    Args:
        issue_number: Issue番号
        repo_owner: リポジトリオーナー
        repo_name: リポジトリ名
        token: GitHub token
        **kwargs: その他の更新パラメータ

    Returns:
        Issue更新結果
    """
    implementation = GitHubUpdateIssueImplementation(
        token=token, repo_owner=repo_owner, repo_name=repo_name
    )

    return implementation.update_issue(issue_number, **kwargs)
