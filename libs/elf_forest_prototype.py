#!/usr/bin/env python3
"""
Elf Forest System Prototype
エルフの森システム プロトタイプ実装
"""

import asyncio
import logging
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# マナタイプ
class ManaType(Enum):
    FLOW = "flow"
    TIME = "time"
    BALANCE = "balance"
    HEAL = "heal"
    WISDOM = "wisdom"


# タスク状態
class TaskState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STUCK = "stuck"


@dataclass
class Task:
    """タスク表現"""

    id: str
    name: str
    state: TaskState = TaskState.PENDING
    priority: int = 5
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    assigned_worker: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ManaPool:
    """マナプール"""

    flow: float = 100.0
    time: float = 100.0
    balance: float = 100.0
    heal: float = 100.0
    wisdom: float = 100.0

    @property
    def total(self) -> float:
        return (self.flow + self.time + self.balance + self.heal + self.wisdom) / 5

    def consume(self, mana_type: ManaType, amount: float):
        """マナ消費"""
        current = getattr(self, mana_type.value)
        setattr(self, mana_type.value, max(0, current - amount))

    def regenerate(self, mana_type: ManaType, amount: float):
        """マナ回復"""
        current = getattr(self, mana_type.value)
        setattr(self, mana_type.value, min(100, current + amount))


class BaseElf(ABC):
    """エルフ基底クラス"""

    def __init__(self, name: str, forest: "ElfForest"):
        self.name = name
        self.forest = forest
        self.mana_consumption = 5.0
        self.active = True
        self.last_action = datetime.now()

    @abstractmethod
    async def perform_duty(self):
        """エルフの責務を実行"""
        pass

    def consume_mana(self, mana_type: ManaType, amount: Optional[float] = None):
        """マナを消費"""
        amount = amount or self.mana_consumption
        self.forest.mana_pool.consume(mana_type, amount)

    def log_action(self, action: str):
        """アクション記録"""
        logger.info(f"🧝 {self.name}: {action}")
        self.last_action = datetime.now()


class FlowElf(BaseElf):
    """フローエルフ - タスクの流れを監視"""

    def __init__(self, name: str, forest: "ElfForest", specialty: str = "queue"):
        super().__init__(name, forest)
        self.specialty = specialty

    async def perform_duty(self):
        """タスクフローの監視"""
        while self.active:
            try:
                # キューの状態チェック
                stuck_tasks = self._detect_stuck_tasks()
                if stuck_tasks:
                    self.log_action(f"⚠️ {len(stuck_tasks)}個の停滞タスクを検出")
                    self.consume_mana(ManaType.FLOW)
                    await self._handle_stuck_tasks(stuck_tasks)

                # ボトルネック検出
                bottlenecks = self._detect_bottlenecks()
                if bottlenecks:
                    self.log_action(f"🚧 ボトルネック検出: {bottlenecks}")
                    self.forest.mana_pool.regenerate(ManaType.WISDOM, 2.0)

                await asyncio.sleep(30)  # 30秒ごとにチェック

            except Exception as e:
                logger.error(f"FlowElf error: {e}")
                await asyncio.sleep(60)

    def _detect_stuck_tasks(self) -> List[Task]:
        """停滞タスクの検出"""
        stuck_tasks = []
        threshold = timedelta(minutes=30)

        for task in self.forest.task_queue:
            if task.state == TaskState.RUNNING:
                if datetime.now() - task.created_at > threshold:
                    task.state = TaskState.STUCK
                    stuck_tasks.append(task)

        return stuck_tasks

    def _detect_bottlenecks(self) -> Dict[str, Any]:
        """ボトルネック検出"""
        bottlenecks = {}

        # キュー長チェック
        if len(self.forest.task_queue) > 50:
            bottlenecks["queue_length"] = len(self.forest.task_queue)

        # 特定ワーカーへの偏り
        worker_loads = {}
        for task in self.forest.task_queue:
            if task.assigned_worker:
                worker_loads[task.assigned_worker] = (
                    worker_loads.get(task.assigned_worker, 0) + 1
                )

        if worker_loads:
            max_load = max(worker_loads.values())
            avg_load = sum(worker_loads.values()) / len(worker_loads)
            if max_load > avg_load * 2:
                bottlenecks["worker_imbalance"] = max_load / avg_load

        return bottlenecks

    async def _handle_stuck_tasks(self, tasks: List[Task]):
        """停滞タスクの処理"""
        for task in tasks:
            # ヒーリングエルフに通知
            await self.forest.notify_elves("heal", {"task": task, "issue": "stuck"})


class TimeElf(BaseElf):
    """タイムエルフ - 時間管理とリマインダー"""

    def __init__(self, name: str, forest: "ElfForest", precision: str = "minute"):
        super().__init__(name, forest)
        self.precision = precision
        self.reminders: List[Dict[str, Any]] = []

    async def perform_duty(self):
        """時間管理の実行"""
        while self.active:
            try:
                # デッドラインチェック
                await self._check_deadlines()

                # リマインダー処理
                await self._process_reminders()

                # 時間効率の分析
                efficiency = self._analyze_time_efficiency()
                if efficiency < 0.7:
                    self.log_action(f"⏰ 時間効率低下: {efficiency:.1%}")
                    self.consume_mana(ManaType.TIME, 10.0)

                await asyncio.sleep(60)  # 1分ごとにチェック

            except Exception as e:
                logger.error(f"TimeElf error: {e}")
                await asyncio.sleep(60)

    def set_reminder(self, task_id: str, when: datetime, message: str):
        """リマインダー設定"""
        self.reminders.append(
            {"task_id": task_id, "when": when, "message": message, "fired": False}
        )
        self.log_action(f"📅 リマインダー設定: {message} @ {when}")

    async def _check_deadlines(self):
        """デッドラインチェック"""
        now = datetime.now()
        warning_threshold = timedelta(hours=1)

        for task in self.forest.task_queue:
            if task.deadline and task.state in [TaskState.PENDING, TaskState.RUNNING]:
                time_left = task.deadline - now

                if time_left < timedelta(0):
                    self.log_action(f"🚨 デッドライン超過: {task.name}")
                    await self.forest.notify_elves(
                        "all", {"alert": "deadline_exceeded", "task": task}
                    )
                elif time_left < warning_threshold:
                    self.log_action(
                        f"⚠️ デッドライン接近: {task.name} (残り{time_left})"
                    )

    async def _process_reminders(self):
        """リマインダー処理"""
        now = datetime.now()

        for reminder in self.reminders:
            if not reminder["fired"] and now >= reminder["when"]:
                self.log_action(f"🔔 リマインダー: {reminder['message']}")
                reminder["fired"] = True

                # 該当タスクに通知
                task = self._find_task(reminder["task_id"])
                if task and task.assigned_worker:
                    await self.forest.notify_worker(
                        task.assigned_worker, reminder["message"]
                    )

    def _analyze_time_efficiency(self) -> float:
        """時間効率の分析"""
        completed_tasks = [
            t
            for t in self.forest.completed_tasks
            if t.deadline and t.state == TaskState.COMPLETED
        ]

        if not completed_tasks:
            return 1.0

        on_time = sum(
            1
            for t in completed_tasks
            if t.metadata.get("completed_at", datetime.now()) <= t.deadline
        )

        return on_time / len(completed_tasks) if completed_tasks else 1.0

    def _find_task(self, task_id: str) -> Optional[Task]:
        """タスク検索"""
        for task in self.forest.task_queue + self.forest.completed_tasks:
            if task.id == task_id:
                return task
        return None


class BalanceElf(BaseElf):
    """バランスエルフ - 負荷分散"""

    async def perform_duty(self):
        """負荷分散の実行"""
        while self.active:
            try:
                # ワーカー負荷の分析
                imbalance = self._analyze_load_balance()

                if imbalance > 0.3:  # 30%以上の不均衡
                    self.log_action(f"⚖️ 負荷不均衡検出: {imbalance:.1%}")
                    self.consume_mana(ManaType.BALANCE)
                    await self._rebalance_tasks()

                await asyncio.sleep(120)  # 2分ごとにチェック

            except Exception as e:
                logger.error(f"BalanceElf error: {e}")
                await asyncio.sleep(120)

    def _analyze_load_balance(self) -> float:
        """負荷バランスの分析"""
        worker_loads = {}

        for task in self.forest.task_queue:
            if task.assigned_worker:
                worker_loads[task.assigned_worker] = (
                    worker_loads.get(task.assigned_worker, 0) + 1
                )

        if len(worker_loads) < 2:
            return 0.0

        loads = list(worker_loads.values())
        avg_load = sum(loads) / len(loads)
        variance = sum((x - avg_load) ** 2 for x in loads) / len(loads)

        return (variance**0.5) / avg_load if avg_load > 0 else 0.0

    async def _rebalance_tasks(self):
        """タスクの再配分"""
        self.log_action("♻️ タスク再配分を開始")
        # 実際の再配分ロジックはここに実装
        self.forest.mana_pool.regenerate(ManaType.BALANCE, 5.0)


class HealingElf(BaseElf):
    """ヒーリングエルフ - エラー回復"""

    async def perform_duty(self):
        """回復処理の実行"""
        while self.active:
            try:
                # 失敗タスクの検出
                failed_tasks = [
                    t for t in self.forest.task_queue if t.state == TaskState.FAILED
                ]

                for task in failed_tasks:
                    if task.retry_count < 3:
                        self.log_action(f"💚 タスク回復試行: {task.name}")
                        self.consume_mana(ManaType.HEAL, 15.0)
                        await self._heal_task(task)

                await asyncio.sleep(60)  # 1分ごとにチェック

            except Exception as e:
                logger.error(f"HealingElf error: {e}")
                await asyncio.sleep(60)

    async def _heal_task(self, task: Task):
        """タスクの回復"""
        task.retry_count += 1
        task.state = TaskState.PENDING

        # エラー原因の分析
        error_pattern = task.metadata.get("error_pattern", "unknown")

        if error_pattern == "timeout":
            task.metadata["timeout"] = task.metadata.get("timeout", 60) * 2
            self.log_action(f"⏱️ タイムアウト延長: {task.name}")
        elif error_pattern == "resource":
            # リソース不足の場合は優先度を上げる
            task.priority = min(10, task.priority + 2)
            self.log_action(f"📈 優先度上昇: {task.name}")

        self.forest.mana_pool.regenerate(ManaType.HEAL, 3.0)


class WisdomElf(BaseElf):
    """ウィズダムエルフ - 学習と知識蓄積"""

    def __init__(self, name: str, forest: "ElfForest", domain: str = "general"):
        super().__init__(name, forest)
        self.domain = domain
        self.learned_patterns: List[Dict[str, Any]] = []

    async def perform_duty(self):
        """学習処理の実行"""
        while self.active:
            try:
                # パターン学習
                new_patterns = self._analyze_patterns()
                if new_patterns:
                    self.learned_patterns.extend(new_patterns)
                    self.log_action(f"🎓 新パターン学習: {len(new_patterns)}個")
                    self.consume_mana(ManaType.WISDOM)
                    self.forest.mana_pool.regenerate(ManaType.WISDOM, 10.0)

                # 最適化提案
                suggestions = self._generate_suggestions()
                if suggestions:
                    self.log_action(f"💡 最適化提案: {len(suggestions)}個")
                    await self.forest.notify_task_elder(suggestions)

                await asyncio.sleep(300)  # 5分ごとに分析

            except Exception as e:
                logger.error(f"WisdomElf error: {e}")
                await asyncio.sleep(300)

    def _analyze_patterns(self) -> List[Dict[str, Any]]:
        """パターン分析"""
        patterns = []

        # 成功パターンの抽出
        successful_tasks = [
            t for t in self.forest.completed_tasks if t.state == TaskState.COMPLETED
        ]

        if len(successful_tasks) > 10:
            # タスクタイプ別の平均実行時間
            type_times = {}
            for task in successful_tasks:
                task_type = task.metadata.get("type", "default")
                exec_time = task.metadata.get("execution_time", 0)

                if task_type not in type_times:
                    type_times[task_type] = []
                type_times[task_type].append(exec_time)

            for task_type, times in type_times.items():
                if len(times) > 5:
                    avg_time = sum(times) / len(times)
                    patterns.append(
                        {
                            "type": "execution_time",
                            "task_type": task_type,
                            "average": avg_time,
                            "samples": len(times),
                        }
                    )

        return patterns

    def _generate_suggestions(self) -> List[Dict[str, Any]]:
        """最適化提案の生成"""
        suggestions = []

        # 学習したパターンに基づく提案
        for pattern in self.learned_patterns[-10:]:  # 最新10個
            if pattern["type"] == "execution_time":
                suggestions.append(
                    {
                        "type": "optimization",
                        "target": pattern["task_type"],
                        "suggestion": f"平均実行時間: {pattern['average']:.1f}秒",
                        "confidence": min(0.9, pattern["samples"] / 20),
                    }
                )

        return suggestions


class ElfForest:
    """エルフの森 - 中央管理システム"""

    def __init__(self):
        self.mana_pool = ManaPool()
        self.elves: List[BaseElf] = []
        self.task_queue: List[Task] = []
        self.completed_tasks: List[Task] = []
        self.active = False
        self.start_time = datetime.now()

        logger.info("🌲 エルフの森が目覚めました...")

    def summon_elves(self):
        """エルフたちを召喚"""
        # フローエルフ
        self.elves.append(FlowElf("Flowinda", self, "queue"))
        self.elves.append(FlowElf("Streamar", self, "pipeline"))

        # タイムエルフ
        self.elves.append(TimeElf("Chronos", self, "minute"))
        self.elves.append(TimeElf("Tempora", self, "hour"))

        # バランスエルフ
        self.elves.append(BalanceElf("Equilibria", self))

        # ヒーリングエルフ
        self.elves.append(HealingElf("Healara", self))

        # ウィズダムエルフ
        self.elves.append(WisdomElf("Sophias", self, "patterns"))

        logger.info(f"🧝 {len(self.elves)}体のエルフが集まりました")

    async def awaken(self):
        """森を起動"""
        self.active = True
        self.summon_elves()

        # 各エルフの活動開始
        tasks = [elf.perform_duty() for elf in self.elves]

        # マナ回復タスク
        tasks.append(self._mana_regeneration())

        # ステータス表示タスク
        tasks.append(self._status_reporter())

        await asyncio.gather(*tasks)

    async def _mana_regeneration(self):
        """マナの自然回復"""
        while self.active:
            # 各マナタイプを少しずつ回復
            for mana_type in ManaType:
                self.mana_pool.regenerate(mana_type, 2.0)

            await asyncio.sleep(60)  # 1分ごとに回復

    async def _status_reporter(self):
        """定期的な状態レポート"""
        while self.active:
            await asyncio.sleep(300)  # 5分ごと
            self.display_status()

    def display_status(self):
        """森の状態表示"""
        runtime = datetime.now() - self.start_time

        status = f"""
🌲 エルフの森ステータス 🌲
========================

稼働時間: {runtime}
総マナレベル: {'█' * int(self.mana_pool.total / 10)}{'░' * (10 - int(self.mana_pool.total / 10))} {self.mana_pool.total:.1f}%

マナ詳細:
- フロー: {self.mana_pool.flow:.1f}%
- タイム: {self.mana_pool.time:.1f}%
- バランス: {self.mana_pool.balance:.1f}%
- ヒール: {self.mana_pool.heal:.1f}%
- ウィズダム: {self.mana_pool.wisdom:.1f}%

エルフ活動状況:
"""

        for elf in self.elves:
            idle_time = (datetime.now() - elf.last_action).seconds
            status += f"- {elf.name}: {'稼働中' if idle_time < 300 else '待機中'}\n"

        status += f"""
タスク状況:
- キュー内: {len(self.task_queue)}
- 完了済み: {len(self.completed_tasks)}
- 停滞中: {sum(1 for t in self.task_queue if t.state == TaskState.STUCK)}
"""

        logger.info(status)

    async def notify_elves(self, target: str, message: Dict[str, Any]):
        """エルフへの通知"""
        # 実装は簡略化
        logger.debug(f"通知 -> {target}: {message}")

    async def notify_worker(self, worker: str, message: str):
        """ワーカーへの通知"""
        logger.info(f"📨 ワーカー通知 -> {worker}: {message}")

    async def notify_task_elder(self, suggestions: List[Dict[str, Any]]):
        """タスクエルダーへの提案"""
        logger.info(f"📜 タスクエルダーへ: {len(suggestions)}個の提案")

    def add_task(self, task: Task):
        """タスク追加"""
        self.task_queue.append(task)
        logger.info(f"📥 新規タスク: {task.name}")


# デモ実行
async def demo():
    """デモンストレーション"""
    forest = ElfForest()

    # サンプルタスク追加
    for i in range(10):
        task = Task(
            id=f"task_{i}",
            name=f"サンプルタスク{i}",
            priority=random.randint(1, 10),
            deadline=datetime.now() + timedelta(hours=random.randint(1, 24)),
        )
        if i % 3 == 0:
            task.assigned_worker = f"worker_{random.randint(1, 3)}"
            task.state = TaskState.RUNNING

        forest.add_task(task)

    # 森を30秒間起動
    try:
        await asyncio.wait_for(forest.awaken(), timeout=30)
    except asyncio.TimeoutError:
        forest.display_status()
        logger.info("🌙 エルフの森が眠りにつきました...")


if __name__ == "__main__":
    print("🧝‍♂️ エルフの森プロトタイプ - デモ実行")
    asyncio.run(demo())
