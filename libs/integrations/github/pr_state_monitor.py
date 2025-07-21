#!/usr/bin/env python3
"""
👀 PR State Monitor
PR状態の継続的監視とイベント発火システム

機能:
- 定期ポーリングによる状態監視
- 状態変化の自動検出
- イベントベースの通知システム
- バックグラウンド監視
- タイムアウト管理
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Set
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)


class StateChangeEvent(Enum):
    """状態変化イベントの種類"""
    CI_STARTED = "ci_started"
    CI_PASSED = "ci_passed"
    CI_FAILED = "ci_failed"
    REVIEW_REQUESTED = "review_requested"
    REVIEW_APPROVED = "review_approved"
    REVIEW_CHANGES_REQUESTED = "review_changes_requested"
    CONFLICTS_RESOLVED = "conflicts_resolved"
    CONFLICTS_DETECTED = "conflicts_detected"
    READY_TO_MERGE = "ready_to_merge"
    MERGE_BLOCKED = "merge_blocked"
    BRANCH_UPDATED = "branch_updated"
    DRAFT_CONVERTED = "draft_converted"


@dataclass
class PRState:
    """PR状態のスナップショット"""
    pr_number: int
    timestamp: datetime
    mergeable: Optional[bool]
    mergeable_state: str
    draft: bool
    state: str  # open, closed, merged
    ci_status: Optional[str]  # pending, success, failure, error
    review_state: Optional[str]  # pending, approved, changes_requested
    behind_by: int = 0
    ahead_by: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "pr_number": self.pr_number,
            "timestamp": self.timestamp.isoformat(),
            "mergeable": self.mergeable,
            "mergeable_state": self.mergeable_state,
            "draft": self.draft,
            "state": self.state,
            "ci_status": self.ci_status,
            "review_state": self.review_state,
            "behind_by": self.behind_by,
            "ahead_by": self.ahead_by
        }


@dataclass
class MonitoringConfig:
    """監視設定"""
    polling_interval: int = 30  # 秒
    max_monitoring_duration: int = 1800  # 30分
    event_callbacks: Dict[StateChangeEvent, List[Callable]] = None
    auto_stop_on_merge: bool = True
    auto_stop_on_close: bool = True
    
    def __post_init__(self):
        if self.event_callbacks is None:
            self.event_callbacks = {}


class PRStateMonitor:
    """PR状態監視システム"""
    
    def __init__(self, pr_api_client):
        """
        初期化
        
        Args:
            pr_api_client: PR操作用のAPIクライアント
        """
        self.pr_api_client = pr_api_client
        self.active_monitors: Dict[int, asyncio.Task] = {}
        self.state_history: Dict[int, List[PRState]] = {}
        self.monitoring_configs: Dict[int, MonitoringConfig] = {}
        
    async def start_monitoring(
        self, 
        pr_number: int, 
        config: Optional[MonitoringConfig] = None
    ) -> bool:
        """
        PR監視を開始
        
        Args:
            pr_number: 監視するPR番号
            config: 監視設定
            
        Returns:
            bool: 監視開始の成功/失敗
        """
        if pr_number in self.active_monitors:
            logger.warning(f"PR #{pr_number} is already being monitored")
            return False
        
        config = config or MonitoringConfig()
        self.monitoring_configs[pr_number] = config
        self.state_history[pr_number] = []
        
        # 初期状態を記録
        initial_state = await self._get_current_state(pr_number)
        if initial_state:
            self.state_history[pr_number].append(initial_state)
        
        # バックグラウンドタスクを開始
        task = asyncio.create_task(
            self._monitoring_loop(pr_number, config)
        )
        self.active_monitors[pr_number] = task
        
        logger.info(f"Started monitoring PR #{pr_number}")
        return True
    
    async def stop_monitoring(self, pr_number: int) -> bool:
        """
        PR監視を停止
        
        Args:
            pr_number: 停止するPR番号
            
        Returns:
            bool: 停止の成功/失敗
        """
        if pr_number not in self.active_monitors:
            logger.warning(f"PR #{pr_number} is not being monitored")
            return False
        
        task = self.active_monitors[pr_number]
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        if pr_number in self.active_monitors:
            del self.active_monitors[pr_number]
        logger.info(f"Stopped monitoring PR #{pr_number}")
        return True
    
    async def _monitoring_loop(self, pr_number: int, config: MonitoringConfig):
        """監視ループのメイン処理"""
        start_time = datetime.now()
        
        try:
            while True:
                # タイムアウトチェック
                if (datetime.now() - start_time).total_seconds() > config.max_monitoring_duration:
                    logger.info(f"Monitoring timeout for PR #{pr_number}")
                    await self._fire_event(pr_number, "monitoring_timeout", {
                        "duration": config.max_monitoring_duration,
                        "reason": "timeout"
                    })
                    break
                
                # 現在の状態を取得
                current_state = await self._get_current_state(pr_number)
                if not current_state:
                    logger.error(f"Failed to get state for PR #{pr_number}")
                    await asyncio.sleep(config.polling_interval)
                    continue
                
                # 状態変化を検出
                previous_state = self.state_history[pr_number][-1] if self.state_history[pr_number] else None
                
                if previous_state:
                    events = self._detect_state_changes(previous_state, current_state)
                    
                    # イベントを発火
                    for event_type, event_data in events:
                        await self._fire_event(pr_number, event_type.value, event_data)
                
                # 状態履歴に追加
                self.state_history[pr_number].append(current_state)
                
                # 自動停止条件をチェック
                if self._should_auto_stop(current_state, config):
                    logger.info(f"Auto-stopping monitoring for PR #{pr_number}")
                    break
                
                # 次のポーリングまで待機
                await asyncio.sleep(config.polling_interval)
                
        except asyncio.CancelledError:
            logger.info(f"Monitoring cancelled for PR #{pr_number}")
        except Exception as e:
            logger.error(f"Monitoring error for PR #{pr_number}: {e}")
        finally:
            # クリーンアップ
            if pr_number in self.active_monitors:
                del self.active_monitors[pr_number]
    
    async def _get_current_state(self, pr_number: int) -> Optional[PRState]:
        """現在のPR状態を取得"""
        try:
            pr_info = self.pr_api_client._get_pull_request(pr_number)
            if not pr_info["success"]:
                return None
            
            pr = pr_info["pull_request"]
            
            # CI状態を取得
            ci_status = await self._get_ci_status(pr_number)
            
            # レビュー状態を取得
            review_state = await self._get_review_state(pr_number)
            
            return PRState(
                pr_number=pr_number,
                timestamp=datetime.now(),
                mergeable=pr.get("mergeable"),
                mergeable_state=pr.get("mergeable_state", "unknown"),
                draft=pr.get("draft", False),
                state=pr.get("state", "unknown"),
                ci_status=ci_status,
                review_state=review_state,
                behind_by=pr.get("behind_by", 0),
                ahead_by=pr.get("ahead_by", 0)
            )
            
        except Exception as e:
            logger.error(f"Error getting PR #{pr_number} state: {e}")
            return None
    
    async def _get_ci_status(self, pr_number: int) -> Optional[str]:
        """CI状態の取得"""
        try:
            # GitHub Status API を使用してCI状態を取得
            # 実装は簡略化版
            return "unknown"
        except Exception as e:
            logger.warning(f"Failed to get CI status for PR #{pr_number}: {e}")
            return None
    
    async def _get_review_state(self, pr_number: int) -> Optional[str]:
        """レビュー状態の取得"""
        try:
            # GitHub Reviews API を使用してレビュー状態を取得
            # 実装は簡略化版
            return "unknown"
        except Exception as e:
            logger.warning(f"Failed to get review state for PR #{pr_number}: {e}")
            return None
    
    def _detect_state_changes(
        self, 
        previous: PRState, 
        current: PRState
    ) -> List[tuple[StateChangeEvent, Dict[str, Any]]]:
        """状態変化を検出してイベントを生成"""
        events = []
        
        # mergeable_state の変化
        if previous.mergeable_state != current.mergeable_state:
            if current.mergeable_state == "clean" and previous.mergeable_state in ["unstable", "dirty"]:
                if previous.mergeable_state == "unstable":
                    events.append((StateChangeEvent.CI_PASSED, {
                        "previous_state": previous.mergeable_state,
                        "current_state": current.mergeable_state
                    }))
                elif previous.mergeable_state == "dirty":
                    events.append((StateChangeEvent.CONFLICTS_RESOLVED, {
                        "previous_state": previous.mergeable_state,
                        "current_state": current.mergeable_state
                    }))
            elif current.mergeable_state == "dirty" and previous.mergeable_state != "dirty":
                events.append((StateChangeEvent.CONFLICTS_DETECTED, {
                    "previous_state": previous.mergeable_state,
                    "current_state": current.mergeable_state
                }))
            elif current.mergeable_state == "unstable" and previous.mergeable_state != "unstable":
                events.append((StateChangeEvent.CI_STARTED, {
                    "previous_state": previous.mergeable_state,
                    "current_state": current.mergeable_state
                }))
        
        # mergeable の変化
        if previous.mergeable != current.mergeable:
            if current.mergeable is True and current.mergeable_state == "clean":
                events.append((StateChangeEvent.READY_TO_MERGE, {
                    "mergeable_changed": True,
                    "mergeable_state": current.mergeable_state
                }))
            elif current.mergeable is False:
                events.append((StateChangeEvent.MERGE_BLOCKED, {
                    "mergeable_changed": True,
                    "mergeable_state": current.mergeable_state
                }))
        
        # draft状態の変化
        if previous.draft != current.draft:
            if not current.draft and previous.draft:
                events.append((StateChangeEvent.DRAFT_CONVERTED, {
                    "from_draft": previous.draft,
                    "to_draft": current.draft
                }))
        
        # ブランチの変化
        if previous.behind_by != current.behind_by or previous.ahead_by != current.ahead_by:
            events.append((StateChangeEvent.BRANCH_UPDATED, {
                "previous_behind": previous.behind_by,
                "current_behind": current.behind_by,
                "previous_ahead": previous.ahead_by,
                "current_ahead": current.ahead_by
            }))
        
        return events
    
    async def _fire_event(
        self, 
        pr_number: int, 
        event_type: str, 
        event_data: Dict[str, Any]
    ):
        """イベントを発火"""
        config = self.monitoring_configs.get(pr_number)
        if not config:
            return
        
        # イベントタイプに応じたコールバックを実行
        event_enum = None
        if isinstance(event_type, StateChangeEvent):
            event_enum = event_type
            event_type = event_type.value
        else:
            try:
                event_enum = StateChangeEvent(event_type)
            except ValueError:
                # カスタムイベントの場合はスキップ
                pass
        
        if event_enum and event_enum in config.event_callbacks:
            callbacks = config.event_callbacks[event_enum]
            for callback in callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(pr_number, event_enum, event_data)
                    else:
                        callback(pr_number, event_enum, event_data)
                except Exception as e:
                    logger.error(f"Event callback error: {e}")
        
        # ログ出力
        logger.info(f"Event fired for PR #{pr_number}: {event_type} - {event_data}")
    
    def _should_auto_stop(self, state: PRState, config: MonitoringConfig) -> bool:
        """自動停止条件をチェック"""
        if config.auto_stop_on_merge and state.state == "merged":
            return True
        
        if config.auto_stop_on_close and state.state == "closed":
            return True
        
        return False
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """監視状況の取得"""
        return {
            "active_monitors": list(self.active_monitors.keys()),
            "total_monitored": len(self.state_history),
            "monitoring_count": len(self.active_monitors)
        }
    
    def get_state_history(self, pr_number: int) -> List[Dict[str, Any]]:
        """状態履歴の取得"""
        history = self.state_history.get(pr_number, [])
        return [state.to_dict() for state in history]
    
    async def add_event_callback(
        self, 
        pr_number: int, 
        event_type: StateChangeEvent, 
        callback: Callable
    ):
        """イベントコールバックを追加"""
        if pr_number not in self.monitoring_configs:
            return False
        
        config = self.monitoring_configs[pr_number]
        if event_type not in config.event_callbacks:
            config.event_callbacks[event_type] = []
        
        config.event_callbacks[event_type].append(callback)
        return True


# 使用例とヘルパー関数
async def example_event_callback(pr_number: int, event_type: str, event_data: Dict[str, Any]):
    """イベントコールバックの例"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] PR #{pr_number} - Event: {event_type}")
    print(f"  Data: {json.dumps(event_data, indent=2)}")


def create_monitoring_config_for_merge() -> MonitoringConfig:
    """マージ用の監視設定を作成"""
    return MonitoringConfig(
        polling_interval=30,
        max_monitoring_duration=1800,  # 30分
        auto_stop_on_merge=True,
        auto_stop_on_close=True
    )