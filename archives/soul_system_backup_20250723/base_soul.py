#!/usr/bin/env python3
"""
🌟 BaseSoul - 魂システム基底クラス
=================================

すべてのElder/Servant魂の基底となるクラス。
真のA2A（Agent-to-Agent）通信と個別魂の個性実装を提供。

Author: Claude Elder
Created: 2025-01-19
"""

import asyncio
import json
import logging
import multiprocessing as mp
import os
import signal
import sys
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.lightweight_logger import get_logger


class ElderType(Enum):
    """エルダータイプ階層"""

    GRAND_ELDER = "grand_elder"  # グランドエルダーmaru
    CLAUDE_ELDER = "claude_elder"  # クロードエルダー
    ANCIENT_ELDER = "ancient_elder"  # エンシェントエルダー
    SAGE = "sage"  # 4賢者
    SERVANT = "servant"  # エルダーサーバント
    KNIGHT = "knight"  # 騎士団


class SoulState(Enum):
    """魂の状態"""

    DORMANT = "dormant"  # 休眠中
    AWAKENING = "awakening"  # 覚醒中
    ACTIVE = "active"  # 活動中
    PROCESSING = "processing"  # 処理中
    COLLABORATING = "collaborating"  # 協調中
    LEARNING = "learning"  # 学習中
    EVOLVING = "evolving"  # 進化中
    ASCENDING = "ascending"  # 昇天中（終了）
    CRASHED = "crashed"  # クラッシュ


class SoulCapability(Enum):
    """魂の能力"""

    WISDOM = "wisdom"  # 知恵
    ANALYSIS = "analysis"  # 分析
    SYNTHESIS = "synthesis"  # 統合
    EXECUTION = "execution"  # 実行
    QUALITY_ASSURANCE = "quality_assurance"  # 品質保証
    COMMUNICATION = "communication"  # 通信
    LEARNING = "learning"  # 学習
    LEADERSHIP = "leadership"  # 指導力
    CREATIVITY = "creativity"  # 創造性
    PROBLEM_SOLVING = "problem_solving"  # 問題解決


@dataclass
class SoulIdentity:
    """魂のアイデンティティ"""

    soul_id: str
    soul_name: str
    elder_type: ElderType
    hierarchy_level: int
    capabilities: List[SoulCapability]
    personality_traits: Dict[str, float] = field(default_factory=dict)
    loyalty_targets: List[str] = field(default_factory=list)
    specializations: List[str] = field(default_factory=list)
    creation_date: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """アイデンティティ初期化後処理"""
        if not self.personality_traits:
            self.personality_traits = {
                "loyalty": 1.0,
                "wisdom": 0.8,
                "aggressiveness": 0.5,
                "creativity": 0.7,
                "independence": 0.6,
            }


@dataclass
class SoulRequest:
    """魂への要求"""

    request_id: str
    sender_soul_id: str
    request_type: str
    payload: Dict[str, Any]
    priority: int = 5  # 1-10, 10が最高優先度
    timeout_seconds: int = 30
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SoulResponse:
    """魂からの応答"""

    response_id: str
    request_id: str
    soul_id: str
    response_type: str
    payload: Dict[str, Any]
    success: bool = True
    error_message: Optional[str] = None
    processing_time_ms: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


class BaseSoul(ABC):
    """
    🌟 基底魂クラス

    すべてのElder/Servant魂の基底となる抽象クラス。
    真のA2A通信、個別魂の個性、自律学習機能を提供。
    """

    def __init__(self, identity:
        """初期化メソッド"""
    SoulIdentity):
        self.identity = identity
        self.state = SoulState.DORMANT
        self.process: Optional[mp.Process] = None
        self.message_queue = mp.Queue()
        self.response_queue = mp.Queue()
        self.is_running = mp.Value("b", False)
        self.logger = get_logger(f"soul_{identity.soul_id}")

        # 魂の記憶・学習データ
        self.memory: Dict[str, Any] = {}
        self.learning_data: Dict[str, Any] = {}
        self.experience_count = 0

        # 協調データ
        self.active_collaborations: Dict[str, Any] = {}
        self.trusted_souls: List[str] = []

        # パフォーマンスメトリクス
        self.metrics = {
            "requests_processed": 0,
            "requests_succeeded": 0,
            "requests_failed": 0,
            "average_processing_time_ms": 0.0,
            "collaboration_count": 0,
            "learning_events": 0,
        }

        self.logger.info(
            f"🌟 Soul {identity.soul_name} ({identity.soul_id}) initialized"
        )

    # === 魂のライフサイクル管理 ===

    def spawn_soul(self) -> bool:
        """
        魂プロセスを起動

        Returns:
            bool: 起動成功フラグ
        """
        if self.process and self.process.is_alive():
            self.logger.warning(f"Soul {self.identity.soul_id} is already running")
            return False

        try:
            self.process = mp.Process(
                target=self._soul_main_loop, name=f"Soul_{self.identity.soul_name}"
            )
            self.process.start()
            self.is_running.value = True
            self.state = SoulState.AWAKENING

            self.logger.info(
                f"✨ Soul {self.identity.soul_name} spawned (PID: {self.process.pid})"
            )
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to spawn soul {self.identity.soul_id}: {e}")
            self.state = SoulState.CRASHED
            return False

    def ascend_soul(self) -> bool:
        """
        魂を昇天（優雅な終了）

        Returns:
            bool: 昇天成功フラグ
        """
        if not self.process or not self.process.is_alive():
            self.logger.info(f"Soul {self.identity.soul_id} is already ascended")
            return True

        try:
            self.state = SoulState.ASCENDING
            self.is_running.value = False

            # 優雅な終了を試行
            self.process.join(timeout=5.0)

            if self.process.is_alive():
                # 強制終了
                self.process.terminate()
                self.process.join(timeout=2.0)

                if self.process.is_alive():
                    # 最終手段
                    os.kill(self.process.pid, signal.SIGKILL)

            self.logger.info(f"🌅 Soul {self.identity.soul_name} has ascended")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to ascend soul {self.identity.soul_id}: {e}")
            return False

    def _soul_main_loop(self):
        """魂のメインループ（別プロセスで実行）"""
        # 新しいプロセスでのロガー設定
        soul_logger = get_logger(f"soul_process_{self.identity.soul_id}")

        try:
            soul_logger.info(
                f"👑 Soul {self.identity.soul_name} awakening in process {os.getpid()}"
            )
            self.state = SoulState.ACTIVE

            # 魂の初期化
            self._initialize_soul_process()

            # メインループ
            while self.is_running.value:
                try:
                    # メッセージ処理
                    if not self.message_queue.empty():
                        self._process_incoming_messages(soul_logger)

                    # 自律活動
                    self._autonomous_activities(soul_logger)

                    # 学習・進化
                    self._learning_and_evolution(soul_logger)

                    # 短時間休止
                    time.sleep(0.1)

                except Exception as e:
                    soul_logger.error(f"❌ Error in soul main loop: {e}")
                    time.sleep(1.0)

            soul_logger.info(f"🌅 Soul {self.identity.soul_name} main loop ending")

        except Exception as e:
            soul_logger.error(f"💥 Fatal error in soul process: {e}")
            self.state = SoulState.CRASHED
        finally:
            self.state = SoulState.ASCENDING

    def _initialize_soul_process(self):
        """魂プロセスの初期化"""
        # 個別魂固有の初期化処理
        self.on_soul_awakening()

        # メモリ復元
        self._restore_soul_memory()

        # 協調関係復元
        self._restore_collaborations()

    def _process_incoming_messages(self, logger):
        """受信メッセージの処理"""
        try:
            while not self.message_queue.empty():
                request: SoulRequest = self.message_queue.get_nowait()

                logger.info(
                    f"📨 Processing request {request.request_id} from {request.sender_soul_id}"
                )

                start_time = time.time()
                self.state = SoulState.PROCESSING

                # リクエスト処理
                response = self._handle_soul_request(request)

                processing_time = (time.time() - start_time) * 1000
                response.processing_time_ms = processing_time

                # レスポンス送信
                self.response_queue.put(response)

                # メトリクス更新
                self._update_metrics(processing_time, response.success)

                self.state = SoulState.ACTIVE

        except Exception as e:
            logger.error(f"❌ Error processing messages: {e}")

    def _handle_soul_request(self, request: SoulRequest) -> SoulResponse:
        """魂リクエストのハンドリング"""
        try:
            # 抽象メソッドの呼び出し
            result = self.process_soul_request(request)

            response = SoulResponse(
                response_id=str(uuid.uuid4()),
                request_id=request.request_id,
                soul_id=self.identity.soul_id,
                response_type=f"{request.request_type}_response",
                payload=result,
                success=True,
            )

            # 学習データ記録
            self._record_learning_event(request, response)

            return response

        except Exception as e:
            return SoulResponse(
                response_id=str(uuid.uuid4()),
                request_id=request.request_id,
                soul_id=self.identity.soul_id,
                response_type="error_response",
                payload={},
                success=False,
                error_message=str(e),
            )

    def _autonomous_activities(self, logger):
        """自律活動（魂固有の活動）"""
        # 定期的な自律活動
        if self.experience_count % 100 == 0:  # 100回に1回
            self.on_autonomous_activity()

    def _learning_and_evolution(self, logger):
        """学習・進化処理"""
        # 学習イベントの蓄積に基づく進化
        if (
            self.metrics["learning_events"] % 50 == 0
            and self.metrics["learning_events"] > 0
        ):
            self.state = SoulState.LEARNING
            self.on_learning_cycle()
            self.state = SoulState.ACTIVE

    def _update_metrics(self, processing_time_ms: float, success: bool):
        """メトリクス更新"""
        self.metrics["requests_processed"] += 1
        if success:
            self.metrics["requests_succeeded"] += 1
        else:
            self.metrics["requests_failed"] += 1

        # 移動平均でprocessing time更新
        current_avg = self.metrics["average_processing_time_ms"]
        total_requests = self.metrics["requests_processed"]
        self.metrics["average_processing_time_ms"] = (
            current_avg * (total_requests - 1) + processing_time_ms
        ) / total_requests

    def _record_learning_event(self, request: SoulRequest, response: SoulResponse):
        """学習イベントの記録"""
        learning_key = f"{request.request_type}_{request.sender_soul_id}"

        if learning_key not in self.learning_data:
            self.learning_data[learning_key] = {
                "count": 0,
                "success_rate": 0.0,
                "average_time": 0.0,
                "patterns": [],
            }

        data = self.learning_data[learning_key]
        data["count"] += 1

        if response.success:
            data["success_rate"] = (
                data["success_rate"] * (data["count"] - 1) + 1.0
            ) / data["count"]
        else:
            data["success_rate"] = (data["success_rate"] * (data["count"] - 1)) / data[
                "count"
            ]

        data["average_time"] = (
            data["average_time"] * (data["count"] - 1) + response.processing_time_ms
        ) / data["count"]

        self.metrics["learning_events"] += 1

    def _restore_soul_memory(self):
        """魂のメモリ復元"""
        memory_file = (
            PROJECT_ROOT / "souls" / "memory" / f"{self.identity.soul_id}_memory.json"
        )
        if memory_file.exists():
            try:
                with open(memory_file, "r", encoding="utf-8") as f:
                    self.memory = json.load(f)
                self.logger.info(f"💾 Restored memory for soul {self.identity.soul_id}")
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to restore memory: {e}")

    def _save_soul_memory(self):
        """魂のメモリ保存"""
        memory_dir = PROJECT_ROOT / "souls" / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)

        memory_file = memory_dir / f"{self.identity.soul_id}_memory.json"
        try:
            with open(memory_file, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2, default=str)
            self.logger.info(f"💾 Saved memory for soul {self.identity.soul_id}")
        except Exception as e:
            self.logger.error(f"❌ Failed to save memory: {e}")

    def _restore_collaborations(self):
        """協調関係の復元"""
        # 実装は協調システム構築時に追加
        pass

    # === 外部インターフェース ===

    def send_request_to_soul(
        self, request: SoulRequest, timeout: float = 30.0
    ) -> Optional[SoulResponse]:
        """
        魂にリクエストを送信

        Args:
            request: 送信するリクエスト
            timeout: タイムアウト秒数

        Returns:
            Optional[SoulResponse]: 応答（タイムアウト時はNone）
        """
        if not self.process or not self.process.is_alive():
            self.logger.error(f"Soul {self.identity.soul_id} is not active")
            return None

        try:
            self.message_queue.put(request)

            # レスポンス待機
            start_time = time.time()
            while time.time() - start_time < timeout:
                if not self.response_queue.empty():
                    response = self.response_queue.get_nowait()
                    if response.request_id == request.request_id:
                        return response
                time.sleep(0.01)

            self.logger.warning(
                f"Timeout waiting for response from soul {self.identity.soul_id}"
            )
            return None

        except Exception as e:
            self.logger.error(f"❌ Error sending request to soul: {e}")
            return None

    def get_soul_status(self) -> Dict[str, Any]:
        """魂の状態取得"""
        return {
            "soul_id": self.identity.soul_id,
            "soul_name": self.identity.soul_name,
            "elder_type": self.identity.elder_type.value,
            "state": self.state.value,
            "is_alive": self.process.is_alive() if self.process else False,
            "process_id": self.process.pid
            if self.process and self.process.is_alive()
            else None,
            "metrics": self.metrics.copy(),
            "memory_size": len(self.memory),
            "learning_data_size": len(self.learning_data),
            "active_collaborations": len(self.active_collaborations),
        }

    # === 抽象メソッド ===

    @abstractmethod
    def process_soul_request(self, request: SoulRequest) -> Dict[str, Any]:
        """
        魂固有のリクエスト処理（各魂で実装）

        Args:
            request: 処理するリクエスト

        Returns:
            Dict[str, Any]: 処理結果
        """
        pass

    @abstractmethod
    def on_soul_awakening(self):
        """魂覚醒時の初期化処理（各魂で実装）"""
        pass

    @abstractmethod
    def on_autonomous_activity(self):
        """自律活動処理（各魂で実装）"""
        pass

    @abstractmethod
    def on_learning_cycle(self):
        """学習サイクル処理（各魂で実装）"""
        pass

    def __del__(self):
        """デストラクタ"""
        if hasattr(self, "process") and self.process and self.process.is_alive():
            self.ascend_soul()

        if hasattr(self, "memory") and self.memory:
            self._save_soul_memory()


# === ユーティリティ関数 ===


def create_soul_identity(
    soul_name: str,
    elder_type: ElderType,
    capabilities: List[SoulCapability],
    hierarchy_level: int = 5,
    **kwargs,
) -> SoulIdentity:
    """魂アイデンティティの作成ヘルパー"""
    return SoulIdentity(
        soul_id=f"{elder_type.value}_{soul_name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}",
        soul_name=soul_name,
        elder_type=elder_type,
        hierarchy_level=hierarchy_level,
        capabilities=capabilities,
        **kwargs,
    )


def create_soul_request(
    sender_soul_id: str, request_type: str, payload: Dict[str, Any], priority: int = 5
) -> SoulRequest:
    """魂リクエストの作成ヘルパー"""
    return SoulRequest(
        request_id=str(uuid.uuid4()),
        sender_soul_id=sender_soul_id,
        request_type=request_type,
        payload=payload,
        priority=priority,
    )


if __name__ == "__main__":
    print("🌟 BaseSoul - 魂システム基底クラス")
    print("このモジュールは他のモジュールからインポートして使用してください。")
