#!/usr/bin/env python3
"""
GitHub Issue 自動監視システム
Automated GitHub Issue Monitoring System

GitHubのIssueを定期的に監視し、新しいコメントを検出・処理する
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .secure_github_client import SecureGitHubClient, get_secure_github_client
from libs.env_manager import EnvManager


class GitHubIssueMonitor:
    """GitHub Issue監視システム"""

    def __init__(
        self,
        repo_owner: str = None,
        repo_name: str = None,
        check_interval: int = 30,
        state_file: str = "logs/issue_monitor_state.json",
    ):
        """
        Args:
            repo_owner: リポジトリオーナー
            repo_name: リポジトリ名
            check_interval: チェック間隔（秒）
            state_file: 状態保存ファイル
        """
        self.repo_owner = repo_owner or EnvManager.get_github_repo_owner()
        self.repo_name = repo_name or EnvManager.get_github_repo_name()
        self.check_interval = check_interval
        self.state_file = Path(state_file)

        # セキュアクライアント
        self.client = get_secure_github_client()

        # ログ設定
        self.logger = logging.getLogger(self.__class__.__name__)

        # 監視状態
        self.last_check_time = None
        self.processed_comments = set()
        self.running = False

        # 状態を読み込み
        self._load_state()

    def _load_state(self)if self.state_file.exists():
    """監視状態を読み込み"""
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)

                self.last_check_time = state.get("last_check_time")
                if self.last_check_time:
                    self.last_check_time = datetime.fromisoformat(self.last_check_time)

                self.processed_comments = set(state.get("processed_comments", []))
                self.logger.info(
                    f"監視状態を読み込み: {len(self.processed_comments)}件のコメント処理済み"
                )

            except Exception as e:
                self.logger.error(f"状態読み込みエラー: {e}")
                self._reset_state()
        else:
            self._reset_state()

    def _save_state(self):
        """監視状態を保存"""
        try:
            # ディレクトリ作成
            self.state_file.parent.mkdir(exist_ok=True)

            state = {
                "last_check_time": (
                    self.last_check_time.isoformat() if self.last_check_time else None
                ),
                "processed_comments": list(self.processed_comments),
                "repo_owner": self.repo_owner,
                "repo_name": self.repo_name,
                "updated_at": datetime.now().isoformat(),
            }

            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"状態保存エラー: {e}")

    def _reset_state(self)self.last_check_time = datetime.now() - timedelta(hours=1)  # 1時間前から開始
    """監視状態をリセット"""
        self.processed_comments = set()
        self.logger.info("監視状態をリセット")

    async def start_monitoring(self):
        """監視を開始"""
        self.running = True
        self.logger.info(f"Issue監視を開始: {self.repo_owner}/{self.repo_name}")

        while self.running:
            try:
                await self._check_issues()
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                self.logger.error(f"監視エラー: {e}")
                await asyncio.sleep(60)  # エラー時は1分待機

    def stop_monitoring(self):
        """監視を停止"""
        self.running = False
        self.logger.info("Issue監視を停止")

    async def _check_issues(self):
        """Issueをチェック"""
        try:
            # 開いているIssueを取得
            issues = self.client.list_issues(
                repo_owner=self.repo_owner, repo_name=self.repo_name, state="open"
            )

            new_comments_count = 0

            for issue in issues:
                issue_number = issue["number"]

                # コメントを取得
                comments = await self._get_issue_comments(issue_number)

                # 新しいコメントをチェック
                for comment in comments:
                    if await self._is_new_comment(comment):
                        await self._process_comment(issue, comment)
                        new_comments_count += 1

            # 最終チェック時刻を更新
            self.last_check_time = datetime.now()
            self._save_state()

            if new_comments_count > 0:
                self.logger.info(f"新しいコメントを{new_comments_count}件処理しました")

        except Exception as e:
            self.logger.error(f"Issueチェックエラー: {e}")

    async def _get_issue_comments(self, issue_number: int) -> List[Dict[str, Any]]:
        """Issue のコメントを取得"""
        try:
            import os

            import requests

            # GitHub API直接呼び出し（secure_clientに無いメソッド）
            url = f"{EnvManager.get_github_api_base_url()}/repos/{self." \
                "repo_owner}/{self.repo_name}/issues/{issue_number}/comments"
            headers = {
                "Authorization": f"token {EnvManager.get_github_token()}",
                "Accept": "application/vnd.github.v3+json",
            }

            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"コメント取得エラー: {response.status_code}")
                return []

        except Exception as e:
            self.logger.error(f"コメント取得エラー: {e}")
            return []

    async def _is_new_comment(self, comment: Dict[str, Any]) -> bool:
        """新しいコメントかどうかチェック"""
        comment_id = comment["id"]
        comment_created = datetime.fromisoformat(
            comment["created_at"].replace("Z", "+00:00")
        )

        # 既に処理済みかチェック
        if comment_id in self.processed_comments:
            return False

        # 最終チェック時刻以降かチェック
        if self.last_check_time and comment_created <= self.last_check_time:
            return False

        # Claude Elderのコメントは除外
        if (
            comment["user"]["login"] == "claude-elder"
            or "claude-elder" in comment["body"].lower()
        ):
            return False

        return True

    async def _process_comment(self, issue: Dict[str, Any], comment: Dict[str, Any]):
        """コメントを処理"""
        comment_id = comment["id"]
        comment_body = comment["body"]
        comment_author = comment["user"]["login"]
        issue_number = issue["number"]

        self.logger.info(
            f"新しいコメントを処理: Issue #{issue_number}, コメント#{comment_id}"
        )

        # コメントを解析
        command = self._parse_comment(comment_body)

        if command:
            # コマンドを実行
            await self._execute_command(issue, comment, command)
        else:
            # 通常のコメント（acknowledgment）
            await self._acknowledge_comment(issue, comment)

        # 処理済みマーク
        self.processed_comments.add(comment_id)

        # 状態保存
        self._save_state()

    def _parse_comment(self, comment_body: str) -> Optional[Dict[str, Any]]:
        """コメントを解析してコマンドを抽出"""
        # コマンドパターン
        patterns = {
            "implement": r"(?:implement|実装|作成|create)\s+(.+)",
            "fix": r"(?:fix|修正|直す|repair)\s+(.+)",
            "test": r"(?:test|テスト|検証|verify)\s+(.+)",
            "document": r"(?:document|ドキュメント|説明|document)\s+(.+)",
            "deploy": r"(?:deploy|デプロイ|リリース|release)\s+(.+)",
            "question": r"(?:\?|？|question|質問|疑問)",
            "approval": r"(?:ok|OK|approve|承認|良い|いいね)",
            "rejection": r"(?:no|NO|reject|拒否|だめ|NG)",
        }

        comment_lower = comment_body.lower()

        for command_type, pattern in patterns.items():
            match = re.search(pattern, comment_lower)
            if match:
                return {
                    "type": command_type,
                    "text": match.group(1) if match.groups() else comment_body,
                    "original": comment_body,
                }

        return None

    async def _execute_command(
        self, issue: Dict[str, Any], comment: Dict[str, Any], command: Dict[str, Any]
    ):
        """コマンドを実行"""
        command_type = command["type"]
        command_text = command["text"]
        issue_number = issue["number"]

        self.logger.info(f"コマンド実行: {command_type} - {command_text}")

        # 実行中であることを報告
        await self._post_comment(
            issue_number,
            f"🤖 **Claude Elder**: コマンドを実行中...\n\n**コマンド**: {command_type}\n**内容**: {command_text}",
        )

        try:
            if command_type == "implement":
                result = await self._handle_implement(command_text)
            elif command_type == "fix":
                result = await self._handle_fix(command_text)
            elif command_type == "test":
                result = await self._handle_test(command_text)
            elif command_type == "document":
                result = await self._handle_document(command_text)
            elif command_type == "question":
                result = await self._handle_question(command["original"])
            elif command_type == "approval":
                result = await self._handle_approval(issue, command["original"])
            elif command_type == "rejection":
                result = await self._handle_rejection(issue, command["original"])
            else:
                result = f"未対応のコマンドタイプ: {command_type}"

            # 結果を報告
            await self._post_comment(
                issue_number, f"✅ **Claude Elder**: コマンド実行完了\n\n{result}"
            )

        except Exception as e:
            error_msg = f"❌ **Claude Elder**: コマンド実行エラー\n\n```\n{str(e)}\n```"
            await self._post_comment(issue_number, error_msg)
            self.logger.error(f"コマンド実行エラー: {e}")

    async def _acknowledge_comment(
        self, issue: Dict[str, Any], comment: Dict[str, Any]
    ):
        """通常のコメントに返信"""
        issue_number = issue["number"]
        comment_author = comment["user"]["login"]

        # 簡単な返信
        response = f"🤖 **Claude Elder**: @{comment_author} " \
            "さん、コメントを確認しました。\n\n何か実行すべきタスクがあれば、具体的な指示をお願いします。"

        await self._post_comment(issue_number, response)

    async def _handle_implement(self, text: str) -> str:
        """実装コマンドを処理"""
        # 実際の実装処理をここに書く
        return f"実装タスクを開始します: {text}\n\n（実装処理をここに追加予定）"

    async def _handle_fix(self, text: str) -> str:
        """修正コマンドを処理"""
        return f"修正タスクを開始します: {text}\n\n（修正処理をここに追加予定）"

    async def _handle_test(self, text: str) -> str:
        """テストコマンドを処理"""
        return f"テストを実行します: {text}\n\n（テスト実行をここに追加予定）"

    async def _handle_document(self, text: str) -> str:
        """ドキュメント作成コマンドを処理"""
        return (
            f"ドキュメントを作成します: {text}\n\n（ドキュメント作成をここに追加予定）"
        )

    async def _handle_question(self, text: str) -> str:
        """質問コマンドを処理"""
        return f"質問を確認しました: {text}\n\n（質問への回答をここに追加予定）"

    async def _handle_approval(self, issue: Dict[str, Any], text: str) -> str:
        """承認コマンドを処理"""
        return f"承認を確認しました。タスクを完了としてマークします。\n\n（承認処理をここに追加予定）"

    async def _handle_rejection(self, issue: Dict[str, Any], text: str) -> str:
        """拒否コマンドを処理"""
        return (
            f"拒否を確認しました。タスクを見直します。\n\n（拒否処理をここに追加予定）"
        )

    async def _post_comment(self, issue_number: int, comment_body: str):
        """Issueにコメントを投稿"""
        try:
            result = self.client.add_comment(
                repo_owner=self.repo_owner,
                repo_name=self.repo_name,
                issue_number=issue_number,
                comment=comment_body,
            )
            self.logger.info(f"コメント投稿成功: Issue #{issue_number}")

        except Exception as e:
            self.logger.error(f"コメント投稿エラー: {e}")


# グローバルモニターインスタンス
_issue_monitor = None


def get_issue_monitor() -> GitHubIssueMonitor:
    """グローバルモニターインスタンスを取得"""
    global _issue_monitor
    if _issue_monitor is None:
        _issue_monitor = GitHubIssueMonitor()
    return _issue_monitor


async def start_monitoring()monitor = get_issue_monitor()
"""監視を開始"""
    await monitor.start_monitoring()


def stop_monitoring()monitor = get_issue_monitor()
"""監視を停止"""
    monitor.stop_monitoring()


# スタンドアロン実行
if __name__ == "__main__":
    import os
    import sys

    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # .envファイルを読み込み
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value

    # 監視開始
    try:
        asyncio.run(start_monitoring())
    except KeyboardInterrupt:
        print("\n監視を停止しました")
