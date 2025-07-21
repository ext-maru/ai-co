#!/usr/bin/env python3
"""
🔄 Smart Merge Retry Engine
マージ失敗時の高度なリトライ戦略を実装するシステム

機能:
- CI完了待ち（unstable → clean）
- 動的待機時間（指数バックオフ）
- 状況別リトライ戦略
- タイムアウト管理
- リアルタイム進捗報告
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# 定数定義
DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 30
DEFAULT_MAX_DELAY = 300
DEFAULT_BACKOFF_FACTOR = 2
LINEAR_DELAY_INCREMENT = 30  # ADAPTIVE戦略での線形増加量


class RetryStrategy(Enum):
    """リトライ戦略の種類"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_INTERVAL = "fixed_interval"
    ADAPTIVE = "adaptive"


class MergeableState(Enum):
    """GitHubのmergeable_state値"""
    CLEAN = "clean"          # マージ可能
    DIRTY = "dirty"          # コンフリクトあり
    UNSTABLE = "unstable"    # CI実行中・失敗
    BLOCKED = "blocked"      # ブランチプロテクション
    BEHIND = "behind"        # ベースブランチ遅れ
    UNKNOWN = "unknown"      # 状態不明


@dataclass
class RetryConfig:
    """リトライ設定"""
    max_retries: int = 10
    base_delay: int = 30  # 秒
    max_delay: int = 300  # 秒
    timeout: int = 1800   # 秒（30分）
    backoff_factor: float = 1.5
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF


@dataclass
class RetryAttempt:
    """リトライ試行の記録"""
    attempt_number: int
    timestamp: datetime
    mergeable_state: str
    mergeable: Optional[bool]
    delay_seconds: int
    success: bool
    error_message: Optional[str] = None


class SmartMergeRetryEngine:
    """スマートマージリトライエンジン"""

    # 状況別のデフォルト設定
    DEFAULT_CONFIGS = {
        MergeableState.UNSTABLE: RetryConfig(
            max_retries=10, base_delay=30, max_delay=300, timeout=1800
        ),
        MergeableState.BEHIND: RetryConfig(
            max_retries=3, base_delay=60, max_delay=180, timeout=600
        ),
        MergeableState.BLOCKED: RetryConfig(
            max_retries=5, base_delay=120, max_delay=600, timeout=1200
        ),
        MergeableState.DIRTY: RetryConfig(
            max_retries=0, base_delay=0, max_delay=0, timeout=0  # 手動対応必要
        ),
        MergeableState.UNKNOWN: RetryConfig(
            max_retries=3, base_delay=60, max_delay=120, timeout=300
        ),
    }

    def __init__(self, pr_api_client, progress_callback: Optional[Callable] = None):
        """
        初期化
        
        Args:
            pr_api_client: PR操作用のAPIクライアント
            progress_callback: 進捗報告用のコールバック関数
        """
        self.pr_api_client = pr_api_client
        self.progress_callback = progress_callback
        self.retry_history: Dict[int, List[RetryAttempt]] = {}

    async def attempt_smart_merge(
        self, 
        pr_number: int, 
        custom_config: Optional[Dict[MergeableState, RetryConfig]] = None
    ) -> Dict[str, Any]:
        """
        スマートマージの実行
        
        Args:
            pr_number: PR番号
            custom_config: カスタムリトライ設定
            
        Returns:
            Dict[str, Any]: マージ結果
        """
        start_time = datetime.now()
        self.retry_history[pr_number] = []
        
        # 設定の準備
        configs = custom_config or self.DEFAULT_CONFIGS
        
        try:
            # 初回状態チェック
            pr_state = await self._get_pr_state(pr_number)
            
            if pr_state["mergeable"] is True and pr_state["mergeable_state"] == "clean":
                # 即座にマージ可能
                return await self._execute_merge(pr_number)
            
            # 状況に応じたリトライ戦略を選択
            mergeable_state = MergeableState(pr_state.get("mergeable_state", "unknown"))
            config = configs.get(mergeable_state, self.DEFAULT_CONFIGS[MergeableState.UNKNOWN])
            
            # マージ不可能な状況の事前チェック
            if config.max_retries == 0:
                return {
                    "success": False,
                    "reason": "manual_intervention_required",
                    "mergeable_state": mergeable_state.value,
                    "message": f"状況 '{mergeable_state.value}' は手動対応が必要です"
                }
            
            # 進捗報告
            await self._report_progress(
                pr_number, "started", 
                f"スマートリトライ開始 - 状況: {mergeable_state.value}"
            )
            
            # リトライループ実行
            return await self._execute_retry_loop(pr_number, config, start_time)
            
        except Exception as e:
            logger.error(f"Smart merge error for PR #{pr_number}: {e}")
            return {
                "success": False,
                "reason": "unexpected_error",
                "error": str(e)
            }

    async def _execute_retry_loop(
        self, 
        pr_number: int, 
        config: RetryConfig, 
        start_time: datetime
    ) -> Dict[str, Any]:
        """リトライループの実行"""
        
        for attempt in range(config.max_retries + 1):
            # タイムアウトチェック
            if (datetime.now() - start_time).total_seconds() > config.timeout:
                await self._report_progress(
                    pr_number, "timeout", 
                    f"タイムアウト ({config.timeout}秒) に達しました"
                )
                return {
                    "success": False,
                    "reason": "timeout",
                    "attempts": attempt,
                    "duration": (datetime.now() - start_time).total_seconds()
                }
            
            # PR状態を取得
            pr_state = await self._get_pr_state(pr_number)
            mergeable_state = pr_state.get("mergeable_state", "unknown")
            
            # リトライ記録
            retry_attempt = RetryAttempt(
                attempt_number=attempt,
                timestamp=datetime.now(),
                mergeable_state=mergeable_state,
                mergeable=pr_state.get("mergeable"),
                delay_seconds=0,
                success=False
            )
            
            # マージ可能性チェック
            if pr_state.get("mergeable") is True and mergeable_state == "clean":
                # マージ実行
                merge_result = await self._execute_merge(pr_number)
                retry_attempt.success = merge_result["success"]
                retry_attempt.error_message = merge_result.get("error")
                
                self.retry_history[pr_number].append(retry_attempt)
                
                if merge_result["success"]:
                    await self._report_progress(
                        pr_number, "completed", 
                        f"マージ成功 - 試行回数: {attempt + 1}"
                    )
                    return {
                        "success": True,
                        "attempts": attempt + 1,
                        "duration": (datetime.now() - start_time).total_seconds(),
                        "merge_result": merge_result
                    }
                else:
                    # マージ失敗（履歴は既に記録済み）
                    pass
            else:
                # マージ不可能な状態の場合も履歴に記録
                retry_attempt.state_after_attempt = mergeable_state
                retry_attempt.error_message = f"Not mergeable: {mergeable_state}"
                self.retry_history[pr_number].append(retry_attempt)
            
            # 最後の試行で失敗した場合
            if attempt >= config.max_retries:
                await self._report_progress(
                    pr_number, "failed", 
                    f"最大試行回数 ({config.max_retries}) に達しました"
                )
                break
            
            # 次の試行までの待機時間計算
            delay = self._calculate_delay(attempt, config)
            retry_attempt.delay_seconds = delay
            
            self.retry_history[pr_number].append(retry_attempt)
            
            # 進捗報告
            await self._report_progress(
                pr_number, "retrying", 
                f"試行 {attempt + 1}/{config.max_retries + 1} - "
                f"状況: {mergeable_state} - {delay}秒後に再試行"
            )
            
            # 待機
            await asyncio.sleep(delay)
        
        return {
            "success": False,
            "reason": "max_retries_exceeded",
            "attempts": config.max_retries + 1,
            "duration": (datetime.now() - start_time).total_seconds(),
            "final_state": mergeable_state
        }

    async def _get_pr_state(self, pr_number: int) -> Dict[str, Any]:
        """PR状態の取得"""
        try:
            pr_info = self.pr_api_client._get_pull_request(pr_number)
            if pr_info["success"]:
                pr = pr_info["pull_request"]
                return {
                    "mergeable": pr.get("mergeable"),
                    "mergeable_state": pr.get("mergeable_state", "unknown"),
                    "draft": pr.get("draft", False),
                    "state": pr.get("state", "unknown")
                }
            else:
                logger.error(f"Failed to get PR #{pr_number} state: {pr_info.get('error')}")
                return {"mergeable": None, "mergeable_state": "unknown"}
                
        except Exception as e:
            logger.error(f"Error getting PR #{pr_number} state: {e}")
            return {"mergeable": None, "mergeable_state": "unknown"}

    async def _execute_merge(self, pr_number: int) -> Dict[str, Any]:
        """マージの実行"""
        try:
            return self.pr_api_client._enable_auto_merge(pr_number)
        except Exception as e:
            logger.error(f"Merge execution error for PR #{pr_number}: {e}")
            return {"success": False, "error": str(e)}

    def _calculate_delay(self, attempt: int, config: RetryConfig) -> int:
        """待機時間の計算"""
        if config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = min(
                config.base_delay * (config.backoff_factor ** attempt),
                config.max_delay
            )
        elif config.strategy == RetryStrategy.FIXED_INTERVAL:
            delay = config.base_delay
        else:  # ADAPTIVE
            # 簡単な適応型：試行回数に応じて線形増加
            delay = min(
                config.base_delay + (attempt * LINEAR_DELAY_INCREMENT),
                config.max_delay
            )
        
        return int(delay)

    async def _report_progress(
        self, 
        pr_number: int, 
        status: str, 
        message: str
    ) -> None:
        """進捗報告"""
        if self.progress_callback:
            try:
                await self.progress_callback(pr_number, status, message)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")
        
        # ログ出力
        logger.info(f"PR #{pr_number} - {status}: {message}")

    def get_retry_history(self, pr_number: int) -> List[RetryAttempt]:
        """リトライ履歴の取得"""
        return self.retry_history.get(pr_number, [])

    def get_statistics(self) -> Dict[str, Any]:
        """統計情報の取得"""
        total_prs = len(self.retry_history)
        if total_prs == 0:
            return {"total_prs": 0}
        
        total_attempts = sum(len(attempts) for attempts in self.retry_history.values())
        successful_prs = sum(
            1 for attempts in self.retry_history.values() 
            if attempts and attempts[-1].success
        )
        
        return {
            "total_prs": total_prs,
            "successful_prs": successful_prs,
            "success_rate": successful_prs / total_prs * 100,
            "average_attempts": total_attempts / total_prs,
            "total_attempts": total_attempts
        }


# 使用例とテスト用のヘルパー関数
async def example_progress_callback(pr_number: int, status: str, message: str):
    """進捗報告の例"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] PR #{pr_number} - {status}: {message}")


# カスタム設定の例
AGGRESSIVE_RETRY_CONFIG = {
    MergeableState.UNSTABLE: RetryConfig(
        max_retries=15, base_delay=20, max_delay=180, timeout=2400
    ),
    MergeableState.BEHIND: RetryConfig(
        max_retries=5, base_delay=30, max_delay=120, timeout=900
    ),
}

CONSERVATIVE_RETRY_CONFIG = {
    MergeableState.UNSTABLE: RetryConfig(
        max_retries=5, base_delay=60, max_delay=300, timeout=1200
    ),
    MergeableState.BEHIND: RetryConfig(
        max_retries=2, base_delay=120, max_delay=240, timeout=480
    ),
}