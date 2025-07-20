#!/usr/bin/env python3
"""
🌟 Soul Process Manager - 魂プロセス管理システム
================================================

複数の魂プロセスの生成、監視、管理を行う中央管理システム。
Elder Tree階層に基づく魂の起動・停止・健全性監視を提供。

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
import threading
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import psutil

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.lightweight_logger import get_logger
from souls.a2a_communication_protocol import (
    A2ACommunicationProtocol,
    A2AMessage,
    MessageType,
    create_a2a_protocol,
)
from souls.base_soul import (
    BaseSoul,
    ElderType,
    SoulCapability,
    SoulIdentity,
    SoulState,
    create_soul_identity,
)

logger = get_logger("soul_process_manager")


class SoulProcessState(Enum):
    """魂プロセス状態"""

    CREATED = "created"  # 作成済み
    STARTING = "starting"  # 起動中
    RUNNING = "running"  # 実行中
    STOPPING = "stopping"  # 停止中
    STOPPED = "stopped"  # 停止済み
    CRASHED = "crashed"  # クラッシュ
    UNRESPONSIVE = "unresponsive"  # 応答なし


class ManagementAction(Enum):
    """管理アクション"""

    START = "start"
    STOP = "stop"
    RESTART = "restart"
    HEALTH_CHECK = "health_check"
    KILL = "kill"
    PAUSE = "pause"
    RESUME = "resume"


@dataclass
class SoulProcessInfo:
    """魂プロセス情報"""

    soul_id: str
    soul_name: str
    elder_type: ElderType
    process_id: Optional[int] = None
    state: SoulProcessState = SoulProcessState.CREATED
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    restart_count: int = 0
    crash_count: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    error_message: Optional[str] = None
    auto_restart: bool = True
    max_restarts: int = 3
    health_check_interval: int = 30
    a2a_port: Optional[int] = None
    capabilities: List[str] = field(default_factory=list)
    configuration: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        data = asdict(self)
        data["elder_type"] = self.elder_type.value
        data["state"] = self.state.value
        data["created_at"] = self.created_at.isoformat() if self.created_at else None
        data["started_at"] = self.started_at.isoformat() if self.started_at else None
        data["stopped_at"] = self.stopped_at.isoformat() if self.stopped_at else None
        data["last_heartbeat"] = (
            self.last_heartbeat.isoformat() if self.last_heartbeat else None
        )
        return data

    def get_uptime(self) -> Optional[timedelta]:
        """稼働時間を取得"""
        if self.started_at and self.state == SoulProcessState.RUNNING:
            return datetime.now() - self.started_at
        return None

    def is_healthy(self) -> bool:
        """健全性チェック"""
        if self.state != SoulProcessState.RUNNING:
            return False

        if not self.last_heartbeat:
            return False

        # ハートビートが5分以内かチェック
        heartbeat_threshold = datetime.now() - timedelta(minutes=5)
        return self.last_heartbeat > heartbeat_threshold


class SoulProcessManager:
    """魂プロセス管理システム"""

    def __init__(self, max_processes: int = None):
        self.max_processes = max_processes or mp.cpu_count() * 2
        self.processes: Dict[str, SoulProcessInfo] = {}
        self.running_processes: Dict[str, mp.Process] = {}
        self.a2a_protocols: Dict[str, A2ACommunicationProtocol] = {}

        self.manager_lock = threading.RLock()
        self.is_running = mp.Value("b", False)

        # 管理用スレッドプール
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.process_executor = ProcessPoolExecutor(max_workers=self.max_processes)

        # 監視設定
        self.monitoring_interval = 10  # 10秒間隔
        self.health_check_timeout = 30  # 30秒タイムアウト

        # 統計情報
        self.stats = {
            "total_souls_created": 0,
            "total_souls_started": 0,
            "total_souls_stopped": 0,
            "total_crashes": 0,
            "total_restarts": 0,
            "start_time": datetime.now(),
        }

        self.logger = get_logger("soul_process_manager")

        # Elder Tree階層定義
        self.elder_hierarchy = {
            ElderType.GRAND_ELDER: {"level": 1, "max_instances": 1},
            ElderType.CLAUDE_ELDER: {"level": 2, "max_instances": 1},
            ElderType.ANCIENT_ELDER: {"level": 3, "max_instances": 1},
            ElderType.SAGE: {"level": 4, "max_instances": 4},  # 4賢者
            ElderType.KNIGHT: {"level": 5, "max_instances": 8},
            ElderType.SERVANT: {"level": 6, "max_instances": 32},  # 32エルダーサーバント
        }

    async def start_manager(self) -> bool:
        """プロセス管理システム開始"""
        try:
            self.is_running.value = True

            # 監視ループ開始
            asyncio.create_task(self._monitoring_loop())

            # ヘルスチェックループ開始
            asyncio.create_task(self._health_check_loop())

            # 統計収集ループ開始
            asyncio.create_task(self._statistics_loop())

            self.logger.info(
                f"🏛️ Soul Process Manager started (max_processes: {self.max_processes})"
            )
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to start Soul Process Manager: {e}")
            return False

    async def stop_manager(self):
        """プロセス管理システム停止"""
        self.is_running.value = False

        # 全魂プロセスを停止
        await self.stop_all_souls()

        # スレッドプール停止
        self.executor.shutdown(wait=True)
        self.process_executor.shutdown(wait=True)

        self.logger.info("🌅 Soul Process Manager stopped")

    def register_soul(
        self,
        soul_identity: SoulIdentity,
        auto_restart: bool = True,
        max_restarts: int = 3,
        configuration: Dict[str, Any] = None,
    ) -> str:
        """魂を登録"""
        with self.manager_lock:
            # 既に登録されているかチェック
            if soul_identity.soul_id in self.processes:
                raise ValueError(f"Soul {soul_identity.soul_id} is already registered")

            # Elder Tree階層制限チェック
            if not self._can_create_soul(soul_identity.elder_type):
                raise ValueError(
                    f"Cannot create more souls of type {soul_identity.elder_type.value}"
                )

            # A2Aポート割り当て
            a2a_port = self._allocate_a2a_port()

            # プロセス情報作成
            process_info = SoulProcessInfo(
                soul_id=soul_identity.soul_id,
                soul_name=soul_identity.soul_name,
                elder_type=soul_identity.elder_type,
                auto_restart=auto_restart,
                max_restarts=max_restarts,
                a2a_port=a2a_port,
                capabilities=[cap.value for cap in soul_identity.capabilities],
                configuration=configuration or {},
            )

            self.processes[soul_identity.soul_id] = process_info
            self.stats["total_souls_created"] += 1

            self.logger.info(
                f"🌟 Soul registered: {soul_identity.soul_name} ({soul_identity.soul_id})"
            )
            return soul_identity.soul_id

    def unregister_soul(self, soul_id: str) -> bool:
        """魂の登録解除"""
        with self.manager_lock:
            if soul_id not in self.processes:
                return False

            # 実行中の場合は停止
            if soul_id in self.running_processes:
                asyncio.create_task(self.stop_soul(soul_id))

            del self.processes[soul_id]

            self.logger.info(f"🗑️ Soul unregistered: {soul_id}")
            return True

    async def start_soul(self, soul_id: str) -> bool:
        """魂プロセス開始"""
        with self.manager_lock:
            if soul_id not in self.processes:
                self.logger.error(f"❌ Soul not registered: {soul_id}")
                return False

            process_info = self.processes[soul_id]

            if process_info.state == SoulProcessState.RUNNING:
                self.logger.warning(f"⚠️ Soul {soul_id} is already running")
                return True

            try:
                process_info.state = SoulProcessState.STARTING
                process_info.error_message = None

                # A2A通信プロトコル作成
                soul_identity = self._create_soul_identity_from_info(process_info)
                a2a_protocol = await create_a2a_protocol(
                    soul_identity, process_info.a2a_port
                )
                self.a2a_protocols[soul_id] = a2a_protocol

                # 魂プロセス起動
                process = mp.Process(
                    target=self._soul_process_wrapper,
                    args=(
                        soul_identity,
                        process_info.configuration,
                        process_info.a2a_port,
                    ),
                    name=f"Soul_{process_info.soul_name}",
                )

                process.start()

                self.running_processes[soul_id] = process
                process_info.process_id = process.pid
                process_info.state = SoulProcessState.RUNNING
                process_info.started_at = datetime.now()
                process_info.last_heartbeat = datetime.now()

                self.stats["total_souls_started"] += 1

                self.logger.info(
                    f"✨ Soul started: {process_info.soul_name} (PID: {process.pid})"
                )
                return True

            except Exception as e:
                process_info.state = SoulProcessState.CRASHED
                process_info.error_message = str(e)
                process_info.crash_count += 1
                self.stats["total_crashes"] += 1

                self.logger.error(f"❌ Failed to start soul {soul_id}: {e}")
                return False

    async def stop_soul(self, soul_id: str, force: bool = False) -> bool:
        """魂プロセス停止"""
        with self.manager_lock:
            if soul_id not in self.processes:
                return False

            process_info = self.processes[soul_id]

            if process_info.state != SoulProcessState.RUNNING:
                return True

            try:
                process_info.state = SoulProcessState.STOPPING

                # A2A通信プロトコル停止
                if soul_id in self.a2a_protocols:
                    await self.a2a_protocols[soul_id].stop_protocol()
                    del self.a2a_protocols[soul_id]

                # プロセス停止
                if soul_id in self.running_processes:
                    process = self.running_processes[soul_id]

                    if force:
                        # 強制終了
                        process.terminate()
                        process.join(timeout=5.0)

                        if process.is_alive():
                            process.kill()
                    else:
                        # 優雅な停止
                        process.terminate()
                        process.join(timeout=10.0)

                        if process.is_alive():
                            process.kill()

                    del self.running_processes[soul_id]

                process_info.state = SoulProcessState.STOPPED
                process_info.stopped_at = datetime.now()
                process_info.process_id = None

                self.stats["total_souls_stopped"] += 1

                self.logger.info(f"🌅 Soul stopped: {process_info.soul_name}")
                return True

            except Exception as e:
                self.logger.error(f"❌ Failed to stop soul {soul_id}: {e}")
                return False

    async def restart_soul(self, soul_id: str) -> bool:
        """魂プロセス再起動"""
        with self.manager_lock:
            if soul_id not in self.processes:
                return False

            process_info = self.processes[soul_id]

            # 再起動回数チェック
            if process_info.restart_count >= process_info.max_restarts:
                self.logger.error(f"❌ Max restart count reached for soul {soul_id}")
                return False

            # 停止→開始
            await self.stop_soul(soul_id)
            await asyncio.sleep(1.0)  # 少し待機

            success = await self.start_soul(soul_id)

            if success:
                process_info.restart_count += 1
                self.stats["total_restarts"] += 1
                self.logger.info(
                    f"🔄 Soul restarted: {process_info.soul_name} (restart #{process_info.restart_count})"
                )

            return success

    async def start_all_souls(self) -> Dict[str, bool]:
        """全魂プロセス開始"""
        results = {}

        # Elder Tree階層順で起動
        for elder_type in [
            ElderType.GRAND_ELDER,
            ElderType.CLAUDE_ELDER,
            ElderType.ANCIENT_ELDER,
            ElderType.SAGE,
            ElderType.KNIGHT,
            ElderType.SERVANT,
        ]:
            souls_to_start = [
                soul_id
                for soul_id, info in self.processes.items()
                if info.elder_type == elder_type
                and info.state != SoulProcessState.RUNNING
            ]

            for soul_id in souls_to_start:
                results[soul_id] = await self.start_soul(soul_id)
                await asyncio.sleep(0.5)  # 起動間隔

        successful = sum(1 for success in results.values() if success)
        self.logger.info(f"🚀 Started {successful}/{len(results)} souls")

        return results

    async def stop_all_souls(self) -> Dict[str, bool]:
        """全魂プロセス停止"""
        results = {}

        # 逆階層順で停止（下位から停止）
        for elder_type in [
            ElderType.SERVANT,
            ElderType.KNIGHT,
            ElderType.SAGE,
            ElderType.ANCIENT_ELDER,
            ElderType.CLAUDE_ELDER,
            ElderType.GRAND_ELDER,
        ]:
            souls_to_stop = [
                soul_id
                for soul_id, info in self.processes.items()
                if info.elder_type == elder_type
                and info.state == SoulProcessState.RUNNING
            ]

            for soul_id in souls_to_stop:
                results[soul_id] = await self.stop_soul(soul_id)
                await asyncio.sleep(0.2)  # 停止間隔

        successful = sum(1 for success in results.values() if success)
        self.logger.info(f"🌅 Stopped {successful}/{len(results)} souls")

        return results

    def get_soul_status(self, soul_id: str) -> Optional[Dict[str, Any]]:
        """魂ステータス取得"""
        with self.manager_lock:
            if soul_id not in self.processes:
                return None

            process_info = self.processes[soul_id]
            status = process_info.to_dict()

            # システムリソース情報追加
            if process_info.process_id:
                try:
                    psutil_process = psutil.Process(process_info.process_id)
                    status.update(
                        {
                            "cpu_percent": psutil_process.cpu_percent(),
                            "memory_info": psutil_process.memory_info()._asdict(),
                            "memory_percent": psutil_process.memory_percent(),
                            "num_threads": psutil_process.num_threads(),
                            "status": psutil_process.status(),
                        }
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    status["system_process_error"] = "Process not accessible"

            # 稼働時間
            uptime = process_info.get_uptime()
            if uptime:
                status["uptime_seconds"] = uptime.total_seconds()

            # 健全性
            status["is_healthy"] = process_info.is_healthy()

            return status

    def get_all_souls_status(self) -> Dict[str, Dict[str, Any]]:
        """全魂ステータス取得"""
        return {
            soul_id: self.get_soul_status(soul_id) for soul_id in self.processes.keys()
        }

    def get_manager_statistics(self) -> Dict[str, Any]:
        """管理システム統計取得"""
        with self.manager_lock:
            running_count = len(
                [
                    p
                    for p in self.processes.values()
                    if p.state == SoulProcessState.RUNNING
                ]
            )
            crashed_count = len(
                [
                    p
                    for p in self.processes.values()
                    if p.state == SoulProcessState.CRASHED
                ]
            )

            elder_type_counts = {}
            for elder_type in ElderType:
                count = len(
                    [p for p in self.processes.values() if p.elder_type == elder_type]
                )
                elder_type_counts[elder_type.value] = count

            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()

            return {
                "manager_uptime_seconds": uptime,
                "total_souls": len(self.processes),
                "running_souls": running_count,
                "crashed_souls": crashed_count,
                "elder_type_distribution": elder_type_counts,
                "max_processes": self.max_processes,
                "statistics": self.stats.copy(),
                "a2a_protocols_active": len(self.a2a_protocols),
            }

    async def _monitoring_loop(self):
        """監視ループ"""
        while self.is_running.value:
            try:
                with self.manager_lock:
                    for soul_id, process_info in self.processes.items():
                        if process_info.state == SoulProcessState.RUNNING:
                            # プロセス生存確認
                            if soul_id in self.running_processes:
                                process = self.running_processes[soul_id]

                                if not process.is_alive():
                                    # プロセス死亡検出
                                    self.logger.warning(
                                        f"💀 Process death detected: {soul_id}"
                                    )
                                    process_info.state = SoulProcessState.CRASHED
                                    process_info.crash_count += 1
                                    self.stats["total_crashes"] += 1

                                    del self.running_processes[soul_id]

                                    # 自動再起動
                                    if (
                                        process_info.auto_restart
                                        and process_info.restart_count
                                        < process_info.max_restarts
                                    ):
                                        asyncio.create_task(self.restart_soul(soul_id))

                await asyncio.sleep(self.monitoring_interval)

            except Exception as e:
                self.logger.error(f"❌ Monitoring loop error: {e}")
                await asyncio.sleep(self.monitoring_interval)

    async def _health_check_loop(self):
        """ヘルスチェックループ"""
        while self.is_running.value:
            try:
                for soul_id, protocol in self.a2a_protocols.items():
                    # A2Aプロトコル経由でヘルスチェック
                    try:
                        health_response = await protocol.send_request(
                            soul_id,
                            "health_check",
                            {"timestamp": datetime.now().isoformat()},
                            requires_response=True,
                        )

                        if health_response:
                            # ハートビート更新
                            if soul_id in self.processes:
                                self.processes[soul_id].last_heartbeat = datetime.now()
                        else:
                            # 応答なし
                            if soul_id in self.processes:
                                process_info = self.processes[soul_id]
                                if process_info.state == SoulProcessState.RUNNING:
                                    process_info.state = SoulProcessState.UNRESPONSIVE
                                    self.logger.warning(
                                        f"⚠️ Soul unresponsive: {soul_id}"
                                    )

                    except Exception as e:
                        self.logger.warning(
                            f"⚠️ Health check failed for {soul_id}: {e}"
                        )

                await asyncio.sleep(self.health_check_timeout)

            except Exception as e:
                self.logger.error(f"❌ Health check loop error: {e}")
                await asyncio.sleep(self.health_check_timeout)

    async def _statistics_loop(self):
        """統計収集ループ"""
        while self.is_running.value:
            try:
                # システムリソース統計更新
                for soul_id, process_info in self.processes.items():
                    if (
                        process_info.process_id
                        and process_info.state == SoulProcessState.RUNNING
                    ):
                        try:
                            psutil_process = psutil.Process(process_info.process_id)
                            process_info.cpu_usage = psutil_process.cpu_percent()
                            process_info.memory_usage = psutil_process.memory_percent()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                await asyncio.sleep(60)  # 1分間隔

            except Exception as e:
                self.logger.error(f"❌ Statistics loop error: {e}")
                await asyncio.sleep(60)

    def _can_create_soul(self, elder_type: ElderType) -> bool:
        """魂作成可能チェック"""
        hierarchy_info = self.elder_hierarchy.get(elder_type)
        if not hierarchy_info:
            return False

        current_count = len(
            [p for p in self.processes.values() if p.elder_type == elder_type]
        )
        return current_count < hierarchy_info["max_instances"]

    def _allocate_a2a_port(self) -> int:
        """A2Aポート割り当て"""
        # 簡単な実装：9000番台から順次割り当て
        used_ports = {
            info.a2a_port for info in self.processes.values() if info.a2a_port
        }

        for port in range(9000, 9100):
            if port not in used_ports:
                return port

        raise RuntimeError("No available A2A ports")

    def _create_soul_identity_from_info(
        self, process_info: SoulProcessInfo
    ) -> SoulIdentity:
        """プロセス情報から魂アイデンティティを作成"""
        capabilities = [
            SoulCapability(cap)
            for cap in process_info.capabilities
            if cap in [c.value for c in SoulCapability]
        ]

        return SoulIdentity(
            soul_id=process_info.soul_id,
            soul_name=process_info.soul_name,
            elder_type=process_info.elder_type,
            hierarchy_level=self.elder_hierarchy[process_info.elder_type]["level"],
            capabilities=capabilities,
        )

    @staticmethod
    def _soul_process_wrapper(
        soul_identity: SoulIdentity, configuration: Dict[str, Any], a2a_port: int
    ):
        """魂プロセスラッパー（プロセス内実行）"""
        try:
            # 新しいプロセスでのロガー設定
            process_logger = get_logger(f"soul_wrapper_{soul_identity.soul_id}")

            process_logger.info(
                f"👑 Soul process starting: {soul_identity.soul_name} (PID: {os.getpid()})"
            )

            # TODO: 実際の魂実装をここで実行
            # 現在は基本的なループのみ

            # A2A通信プロトコル（簡略版）
            async def run_soul():
                protocol = await create_a2a_protocol(soul_identity, a2a_port)

                # シンプルなメッセージループ
                while True:
                    await asyncio.sleep(1.0)

            asyncio.run(run_soul())

        except Exception as e:
            process_logger.error(f"💥 Soul process error: {e}")
            raise


# === 便利な関数 ===


async def create_soul_process_manager(max_processes: int = None) -> SoulProcessManager:
    """魂プロセス管理システムの作成"""
    manager = SoulProcessManager(max_processes)

    if await manager.start_manager():
        return manager
    else:
        raise RuntimeError("Failed to start Soul Process Manager")


def create_standard_elder_tree() -> List[SoulIdentity]:
    """標準Elder Tree構成の作成"""
    souls = []

    # Grand Elder Maru
    souls.append(
        create_soul_identity(
            "Grand Elder Maru",
            ElderType.GRAND_ELDER,
            [
                SoulCapability.LEADERSHIP,
                SoulCapability.WISDOM,
                SoulCapability.PROBLEM_SOLVING,
            ],
        )
    )

    # Claude Elder
    souls.append(
        create_soul_identity(
            "Claude Elder",
            ElderType.CLAUDE_ELDER,
            [
                SoulCapability.LEADERSHIP,
                SoulCapability.COMMUNICATION,
                SoulCapability.ANALYSIS,
            ],
        )
    )

    # Ancient Elder
    souls.append(
        create_soul_identity(
            "Ancient Elder",
            ElderType.ANCIENT_ELDER,
            [SoulCapability.QUALITY_ASSURANCE, SoulCapability.WISDOM],
        )
    )

    # 4賢者
    sage_configs = [
        ("Knowledge Sage", [SoulCapability.WISDOM, SoulCapability.LEARNING]),
        ("Task Sage", [SoulCapability.EXECUTION, SoulCapability.PROBLEM_SOLVING]),
        ("Incident Sage", [SoulCapability.QUALITY_ASSURANCE, SoulCapability.ANALYSIS]),
        ("RAG Sage", [SoulCapability.ANALYSIS, SoulCapability.SYNTHESIS]),
    ]

    for name, capabilities in sage_configs:
        souls.append(create_soul_identity(name, ElderType.SAGE, capabilities))

    # 騎士団（例：8名）
    knight_configs = [
        ("Security Knight", [SoulCapability.QUALITY_ASSURANCE]),
        ("Performance Knight", [SoulCapability.ANALYSIS]),
        ("Documentation Knight", [SoulCapability.COMMUNICATION]),
        ("Testing Knight", [SoulCapability.QUALITY_ASSURANCE]),
        ("DevOps Knight", [SoulCapability.EXECUTION]),
        ("Architecture Knight", [SoulCapability.SYNTHESIS]),
        ("Integration Knight", [SoulCapability.COMMUNICATION]),
        ("Monitoring Knight", [SoulCapability.ANALYSIS]),
    ]

    for name, capabilities in knight_configs:
        souls.append(create_soul_identity(name, ElderType.KNIGHT, capabilities))

    # エルダーサーバント（例：8名、実際は32名まで可能）
    servant_configs = [
        ("Code Servant", [SoulCapability.EXECUTION, SoulCapability.CREATIVITY]),
        ("Test Guardian", [SoulCapability.QUALITY_ASSURANCE]),
        (
            "Quality Inspector",
            [SoulCapability.QUALITY_ASSURANCE, SoulCapability.ANALYSIS],
        ),
        ("Security Auditor", [SoulCapability.QUALITY_ASSURANCE]),
        ("Performance Monitor", [SoulCapability.ANALYSIS]),
        ("Documentation Keeper", [SoulCapability.COMMUNICATION]),
        ("Git Master", [SoulCapability.EXECUTION]),
        ("Deploy Manager", [SoulCapability.EXECUTION]),
    ]

    for name, capabilities in servant_configs:
        souls.append(create_soul_identity(name, ElderType.SERVANT, capabilities))

    return souls


async def test_soul_process_manager():
    """魂プロセス管理システムのテスト"""
    print("🏛️ Testing Soul Process Manager...")

    # 管理システム作成
    manager = await create_soul_process_manager(max_processes=8)

    try:
        # 標準Elder Tree作成
        elder_tree = create_standard_elder_tree()

        # 魂を登録
        for soul_identity in elder_tree[:5]:  # 最初の5つのみテスト
            manager.register_soul(soul_identity)

        # 全魂起動
        print("🚀 Starting all souls...")
        start_results = await manager.start_all_souls()
        print(f"Started: {sum(start_results.values())}/{len(start_results)} souls")

        # 統計表示
        await asyncio.sleep(5)
        stats = manager.get_manager_statistics()
        print(f"📊 Manager statistics: {json.dumps(stats, indent=2, default=str)}")

        # 魂ステータス表示
        for soul_id in list(manager.processes.keys())[:3]:
            status = manager.get_soul_status(soul_id)
            print(f"👤 {soul_id}: {status['state']} (healthy: {status['is_healthy']})")

        # 一つの魂を再起動テスト
        if manager.processes:
            test_soul_id = list(manager.processes.keys())[0]
            print(f"🔄 Testing restart for {test_soul_id}...")
            restart_success = await manager.restart_soul(test_soul_id)
            print(f"Restart result: {restart_success}")

        # 全停止
        print("🌅 Stopping all souls...")
        stop_results = await manager.stop_all_souls()
        print(f"Stopped: {sum(stop_results.values())}/{len(stop_results)} souls")

    finally:
        await manager.stop_manager()

    print("✅ Soul Process Manager test completed!")


if __name__ == "__main__":
    print("🌟 Soul Process Manager - 魂プロセス管理システム")
    print("Test mode:")
    asyncio.run(test_soul_process_manager())
