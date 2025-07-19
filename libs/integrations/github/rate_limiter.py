#!/usr/bin/env python3
"""
GitHub API レート制限管理システム
GitHub API Rate Limiting Manager

GitHub APIのレート制限を監視・管理し、適切な間隔でリクエストを実行する
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import requests


@dataclass
class RateLimitInfo:
    """レート制限情報"""

    limit: int  # 制限値
    remaining: int  # 残り回数
    reset_time: int  # リセット時刻（Unix timestamp）
    used: int  # 使用回数

    @property
    def reset_datetime(self) -> datetime:
        """リセット時刻をdatetimeで取得"""
        return datetime.fromtimestamp(self.reset_time)

    @property
    def seconds_until_reset(self) -> int:
        """リセットまでの秒数"""
        return max(0, self.reset_time - int(time.time()))


class GitHubRateLimiter:
    """GitHub APIレート制限管理"""

    def __init__(
        self, github_token: str, state_file: str = "logs/rate_limit_state.json"
    ):
        """
        Args:
            github_token: GitHub Personal Access Token
            state_file: レート制限状態保存ファイル
        """
        self.github_token = github_token
        self.state_file = Path(state_file)
        self.logger = logging.getLogger(self.__class__.__name__)

        # APIエンドポイント
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "EldersGuild-RateLimiter",
        }

        # レート制限情報
        self.rate_limit_info: Optional[RateLimitInfo] = None
        self.last_request_time: float = 0
        self.request_count: int = 0

        # 設定
        self.min_interval: float = 1.0  # 最小リクエスト間隔（秒）
        self.backoff_multiplier: float = 2.0  # バックオフ倍率
        self.max_backoff: float = 300.0  # 最大バックオフ時間（秒）

        # エラー連続回数
        self.consecutive_errors: int = 0
        self.max_consecutive_errors: int = 3

        # 状態を読み込み
        self._load_state()

    def _load_state(self):
        """状態を読み込み"""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)

                # レート制限情報を復元
                if "rate_limit" in state:
                    rl = state["rate_limit"]
                    self.rate_limit_info = RateLimitInfo(
                        limit=rl["limit"],
                        remaining=rl["remaining"],
                        reset_time=rl["reset_time"],
                        used=rl["used"],
                    )

                self.last_request_time = state.get("last_request_time", 0)
                self.request_count = state.get("request_count", 0)
                self.consecutive_errors = state.get("consecutive_errors", 0)

                self.logger.info(f"レート制限状態を読み込み: {self.request_count}回実行済み")

            except Exception as e:
                self.logger.error(f"状態読み込みエラー: {e}")
                self._reset_state()
        else:
            self._reset_state()

    def _save_state(self):
        """状態を保存"""
        try:
            # ディレクトリ作成
            self.state_file.parent.mkdir(exist_ok=True)

            state = {
                "last_request_time": self.last_request_time,
                "request_count": self.request_count,
                "consecutive_errors": self.consecutive_errors,
                "updated_at": datetime.now().isoformat(),
            }

            # レート制限情報を保存
            if self.rate_limit_info:
                state["rate_limit"] = {
                    "limit": self.rate_limit_info.limit,
                    "remaining": self.rate_limit_info.remaining,
                    "reset_time": self.rate_limit_info.reset_time,
                    "used": self.rate_limit_info.used,
                }

            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"状態保存エラー: {e}")

    def _reset_state(self):
        """状態をリセット"""
        self.rate_limit_info = None
        self.last_request_time = 0
        self.request_count = 0
        self.consecutive_errors = 0
        self.logger.info("レート制限状態をリセット")

    async def get_rate_limit_status(self) -> Optional[RateLimitInfo]:
        """現在のレート制限状況を取得"""
        try:
            response = requests.get(
                f"{self.api_base}/rate_limit", headers=self.headers, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                core = data["resources"]["core"]

                self.rate_limit_info = RateLimitInfo(
                    limit=core["limit"],
                    remaining=core["remaining"],
                    reset_time=core["reset"],
                    used=core["used"],
                )

                self.logger.info(
                    f"レート制限状況: {self.rate_limit_info.remaining}/{self.rate_limit_info.limit} (リセット: {self.rate_limit_info.reset_datetime})"
                )

                return self.rate_limit_info
            else:
                self.logger.error(f"レート制限取得エラー: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"レート制限取得エラー: {e}")
            return None

    def _update_rate_limit_from_response(self, response: requests.Response):
        """レスポンスヘッダからレート制限情報を更新"""
        try:
            if "X-RateLimit-Limit" in response.headers:
                self.rate_limit_info = RateLimitInfo(
                    limit=int(response.headers["X-RateLimit-Limit"]),
                    remaining=int(response.headers["X-RateLimit-Remaining"]),
                    reset_time=int(response.headers["X-RateLimit-Reset"]),
                    used=int(response.headers["X-RateLimit-Used"]),
                )

                self.logger.debug(
                    f"レート制限更新: {self.rate_limit_info.remaining}/{self.rate_limit_info.limit}"
                )

        except Exception as e:
            self.logger.error(f"レート制限更新エラー: {e}")

    async def wait_if_needed(self) -> bool:
        """必要に応じて待機"""
        current_time = time.time()

        # 最小間隔の確認
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            self.logger.debug(f"最小間隔待機: {wait_time:.2f}秒")
            await asyncio.sleep(wait_time)

        # レート制限確認
        if self.rate_limit_info:
            # 残り回数が少ない場合
            if self.rate_limit_info.remaining < 10:
                seconds_until_reset = self.rate_limit_info.seconds_until_reset
                if seconds_until_reset > 0:
                    self.logger.warning(f"レート制限近づいています。{seconds_until_reset}秒待機")
                    await asyncio.sleep(seconds_until_reset + 1)
                    return True

        # 連続エラー時のバックオフ
        if self.consecutive_errors > 0:
            backoff_time = min(
                self.min_interval
                * (self.backoff_multiplier**self.consecutive_errors),
                self.max_backoff,
            )
            self.logger.warning(
                f"連続エラー({self.consecutive_errors}回)によるバックオフ: {backoff_time:.2f}秒"
            )
            await asyncio.sleep(backoff_time)

        return False

    async def execute_request(
        self, method: str, url: str, **kwargs
    ) -> Optional[requests.Response]:
        """レート制限を考慮したリクエスト実行"""

        # 待機が必要かチェック
        await self.wait_if_needed()

        try:
            # リクエスト実行
            self.last_request_time = time.time()
            self.request_count += 1

            # ヘッダーを追加
            request_headers = kwargs.get("headers", {})
            request_headers.update(self.headers)
            kwargs["headers"] = request_headers

            # タイムアウト設定
            kwargs.setdefault("timeout", 30)

            response = requests.request(method, url, **kwargs)

            # レート制限情報を更新
            self._update_rate_limit_from_response(response)

            # エラー状況に応じた処理
            if response.status_code == 403:
                if "rate limit" in response.text.lower():
                    self.logger.error("レート制限に達しました")
                    self.consecutive_errors += 1
                    return None

            elif response.status_code == 429:
                self.logger.error("Abuse detection triggered")
                self.consecutive_errors += 1
                return None

            elif response.status_code >= 400:
                self.logger.error(f"HTTPエラー: {response.status_code} - {response.text}")
                self.consecutive_errors += 1
                return None

            # 成功時は連続エラーをリセット
            self.consecutive_errors = 0

            # 状態を保存
            self._save_state()

            return response

        except Exception as e:
            self.logger.error(f"リクエスト実行エラー: {e}")
            self.consecutive_errors += 1
            self._save_state()
            return None

    async def safe_request(
        self, method: str, url: str, max_retries: int = 3, **kwargs
    ) -> Optional[requests.Response]:
        """安全なリクエスト実行（リトライ付き）"""

        for attempt in range(max_retries):
            # 連続エラーが多い場合は停止
            if self.consecutive_errors >= self.max_consecutive_errors:
                self.logger.error(
                    f"連続エラーが{self.max_consecutive_errors}回に達しました。しばらく待機します。"
                )
                await asyncio.sleep(60)  # 1分間待機
                self.consecutive_errors = 0  # リセット

            response = await self.execute_request(method, url, **kwargs)

            if response is not None:
                return response

            # リトライ前の待機
            if attempt < max_retries - 1:
                wait_time = 2**attempt  # 指数バックオフ
                self.logger.info(
                    f"リトライ {attempt + 1}/{max_retries} - {wait_time}秒後に再試行"
                )
                await asyncio.sleep(wait_time)

        self.logger.error(f"最大リトライ回数({max_retries})に達しました")
        return None

    def get_status_summary(self) -> Dict[str, Any]:
        """現在の状況サマリーを取得"""
        return {
            "request_count": self.request_count,
            "consecutive_errors": self.consecutive_errors,
            "last_request_time": self.last_request_time,
            "rate_limit_info": {
                "limit": self.rate_limit_info.limit if self.rate_limit_info else None,
                "remaining": self.rate_limit_info.remaining
                if self.rate_limit_info
                else None,
                "reset_time": self.rate_limit_info.reset_datetime.isoformat()
                if self.rate_limit_info
                else None,
                "seconds_until_reset": self.rate_limit_info.seconds_until_reset
                if self.rate_limit_info
                else None,
            },
        }


# グローバルレート制限管理インスタンス
_rate_limiter = None


def get_rate_limiter(github_token: str = None) -> GitHubRateLimiter:
    """グローバルレート制限管理インスタンスを取得"""
    global _rate_limiter

    if _rate_limiter is None:
        import os

        token = github_token or os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GitHub tokenが設定されていません")
        _rate_limiter = GitHubRateLimiter(token)

    return _rate_limiter


# 便利関数
async def safe_github_request(
    method: str, url: str, **kwargs
) -> Optional[requests.Response]:
    """安全なGitHubリクエスト"""
    limiter = get_rate_limiter()
    return await limiter.safe_request(method, url, **kwargs)
