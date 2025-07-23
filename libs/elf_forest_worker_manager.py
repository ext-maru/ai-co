#!/usr/bin/env python3
"""
Elf Forest Worker Manager
エルフの森 - Elders Guildワーカー管理システム
"""

import asyncio
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ワーカー定義
WORKER_DEFINITIONS = {
    "enhanced_task_worker": {
        "path": "workers/enhanced_task_worker.py",
        "queue": "ai_tasks",
        "critical": True,
        "min_instances": 1,
        "max_instances": 5,
    },
    "intelligent_pm_worker": {
        "path": "workers/intelligent_pm_worker_simple.py",
        "queue": "ai_pm",
        "critical": True,
        "min_instances": 1,
        "max_instances": 3,
    },
    "async_result_worker": {
        "path": "workers/async_result_worker_simple.py",
        "queue": "ai_results",
        "critical": True,
        "min_instances": 1,
        "max_instances": 3,
    },
    "simple_task_worker": {
        "path": "workers/simple_task_worker.py",
        "queue": "ai_tasks",
        "critical": False,
        "min_instances": 0,
        "max_instances": 2,
    },
}


@dataclass
class WorkerStatus:
    """ワーカーステータス"""

    name: str
    pid: Optional[int] = None
    status: str = "stopped"
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    uptime: Optional[timedelta] = None
    tasks_processed: int = 0
    errors: int = 0
    last_heartbeat: Optional[datetime] = None
    queue_size: int = 0


class WorkerFlowElf:
    """ワーカーフロー監視エルフ"""

    def __init__(self, forest: "ElfForestWorkerManager"):
        """初期化メソッド"""
        self.forest = forest
        self.name = "Flowkeeper"
        self.check_interval = 30  # 30秒ごと

    async def monitor_worker_queues(self):
        """ワーカーキューを監視"""
        while True:
            try:
                for worker_name, worker_def in WORKER_DEFINITIONS.items():
                    queue_name = worker_def["queue"]
                    queue_size = await self._get_queue_size(queue_name)

                    # ワーカーステータス更新
                    if worker_name in self.forest.worker_statuses:
                        self.forest.worker_statuses[worker_name].queue_size = queue_size

                    # キュー積滞チェック
                    if queue_size > 100:
                        logger.warning(
                            f"🚨 {self.name}: {queue_name}キューが積滞 ({queue_size}件)"
                        )
                        await self.forest.notify_task_elder(
                            {
                                "alert": "queue_overflow",
                                "worker": worker_name,
                                "queue_size": queue_size,
                            }
                        )

                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"{self.name} エラー: {e}")
                await asyncio.sleep(60)

    async def _get_queue_size(self, queue_name: str) -> int:
        """キューサイズ取得"""
        try:
            import pika

            connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
            channel = connection.channel()

            method = channel.queue_declare(queue=queue_name, passive=True)
            size = method.method.message_count

            connection.close()
            return size

        except Exception:
            return 0

    def detect_worker_bottlenecks(self) -> Dict[str, Any]:
        """ワーカーボトルネック検出"""
        bottlenecks = {}

        for worker_name, status in self.forest.worker_statuses.items():
            # CPU使用率が高い
            if status.cpu_percent > 80:
                bottlenecks[worker_name] = {
                    "type": "high_cpu",
                    "value": status.cpu_percent,
                }

            # メモリ使用量が多い
            if status.memory_mb > 500:
                bottlenecks[worker_name] = {
                    "type": "high_memory",
                    "value": status.memory_mb,
                }

            # キューが詰まっている
            if status.queue_size > 100:
                bottlenecks[worker_name] = {
                    "type": "queue_backlog",
                    "value": status.queue_size,
                }

        return bottlenecks


class WorkerTimeElf:
    """ワーカー時間管理エルフ"""

    def __init__(self, forest: "ElfForestWorkerManager"):
        """初期化メソッド"""
        self.forest = forest
        self.name = "Timekeeper"
        self.reminders: Dict[str, List[Dict]] = {}

    def add_reminder(self, worker_name: str, when: datetime, message: str):
        """リマインダー追加"""
        if worker_name not in self.reminders:
            self.reminders[worker_name] = []

        self.reminders[worker_name].append(
            {"when": when, "message": message, "sent": False}
        )

        logger.info(f"📅 {self.name}: {worker_name}へのリマインダー設定 - {message}")

    async def process_reminders(self):
        """リマインダー処理"""
        while True:
            try:
                now = datetime.now()

                for worker_name, reminder_list in self.reminders.items():
                    for reminder in reminder_list:
                        if not reminder["sent"] and now >= reminder["when"]:
                            await self.remind_worker(worker_name, reminder["message"])
                            reminder["sent"] = True

                await asyncio.sleep(60)  # 1分ごとにチェック

            except Exception as e:
                logger.error(f"{self.name} エラー: {e}")
                await asyncio.sleep(60)

    async def remind_worker(self, worker_name: str, message: str):
        """ワーカーにリマインド"""
        logger.info(f"🔔 {self.name} → {worker_name}: {message}")

        # ログファイルに記録
        log_file = PROJECT_ROOT / "logs" / f"{worker_name}_reminders.log"
        with open(log_file, "a") as f:
            f.write(f"[{datetime.now()}] {message}\n")

        # 必要に応じてワーカー再起動を提案
        if "メンテナンス" in message or "再起動" in message:
            await self.forest.healing_elf.schedule_restart(worker_name)


class WorkerBalanceElf:
    """ワーカー負荷分散エルフ"""

    def __init__(self, forest: "ElfForestWorkerManager"):
        """初期化メソッド"""
        self.forest = forest
        self.name = "Balancer"

    async def balance_worker_loads(self):
        """ワーカー負荷バランス"""
        while True:
            try:
                # 負荷分析
                load_analysis = self._analyze_loads()

                if load_analysis["needs_rebalance"]:
                    logger.info(f"⚖️ {self.name}: 負荷再分散を実行")
                    await self._rebalance_workers(load_analysis)

                await asyncio.sleep(120)  # 2分ごと

            except Exception as e:
                logger.error(f"{self.name} エラー: {e}")
                await asyncio.sleep(120)

    def _analyze_loads(self) -> Dict[str, Any]:
        """負荷分析"""
        total_cpu = 0
        total_memory = 0
        worker_count = 0
        overloaded_workers = []

        for worker_name, status in self.forest.worker_statuses.items():
            if status.status == "running":
                total_cpu += status.cpu_percent
                total_memory += status.memory_mb
                worker_count += 1

                if status.cpu_percent > 70 or status.memory_mb > 400:
                    overloaded_workers.append(worker_name)

        avg_cpu = total_cpu / worker_count if worker_count > 0 else 0
        avg_memory = total_memory / worker_count if worker_count > 0 else 0

        return {
            "needs_rebalance": len(overloaded_workers) > 0,
            "overloaded": overloaded_workers,
            "avg_cpu": avg_cpu,
            "avg_memory": avg_memory,
        }

    async def _rebalance_workers(self, analysis: Dict[str, Any]):
        """ワーカー再分散"""
        for worker_name in analysis["overloaded"]:
            worker_def = WORKER_DEFINITIONS.get(worker_name, {})

            # 追加ワーカーが起動可能か確認
            current_count = self._count_worker_instances(worker_name)
            if current_count < worker_def.get("max_instances", 1):
                logger.info(f"🚀 {self.name}: {worker_name}の追加インスタンスを起動")
                await self.forest.start_worker(worker_name)

    def _count_worker_instances(self, worker_name: str) -> int:
        """ワーカーインスタンス数カウント"""
        count = 0
        for proc in psutil.process_iter(["cmdline"]):
            try:
                cmdline = " ".join(proc.info["cmdline"] or [])
                if worker_name in cmdline:
                    count += 1
            except:
                pass
        return count


class WorkerHealingElf:
    """ワーカー回復エルフ"""

    def __init__(self, forest: "ElfForestWorkerManager"):
        """初期化メソッド"""
        self.forest = forest
        self.name = "Healer"
        self.restart_schedule: Dict[str, datetime] = {}

    async def heal_sick_workers(self):
        """不調ワーカーの回復"""
        while True:
            try:
                for worker_name, status in self.forest.worker_statuses.items():
                    # メモリリークチェック
                    if status.memory_mb > 500:
                        logger.warning(
                            f"💊 {self.name}: {worker_name}のメモリ使用量が高い ({status.memory_mb}MB)"
                        )
                        await self.schedule_restart(worker_name)

                    # 応答なしチェック
                    if status.last_heartbeat:
                        silence_time = datetime.now() - status.last_heartbeat
                        if silence_time > timedelta(minutes=5):
                            logger.error(f"💀 {self.name}: {worker_name}が応答なし")
                            await self.force_restart_worker(worker_name)

                # スケジュールされた再起動の実行
                await self._process_restart_schedule()

                await asyncio.sleep(60)  # 1分ごと

            except Exception as e:
                logger.error(f"{self.name} エラー: {e}")
                await asyncio.sleep(60)

    async def schedule_restart(self, worker_name: str, delay_minutes: int = 5):
        """再起動スケジュール"""
        restart_time = datetime.now() + timedelta(minutes=delay_minutes)
        self.restart_schedule[worker_name] = restart_time
        logger.info(f"🔄 {self.name}: {worker_name}を{delay_minutes}分後に再起動予定")

    async def _process_restart_schedule(self):
        """スケジュールされた再起動を処理"""
        now = datetime.now()

        for worker_name, restart_time in list(self.restart_schedule.items()):
            if now >= restart_time:
                logger.info(f"🔄 {self.name}: {worker_name}の予定再起動を実行")
                await self.forest.restart_worker(worker_name)
                del self.restart_schedule[worker_name]

    async def force_restart_worker(self, worker_name: str):
        """ワーカー強制再起動"""
        logger.warning(f"⚡ {self.name}: {worker_name}を強制再起動")
        await self.forest.stop_worker(worker_name, force=True)
        await asyncio.sleep(2)
        await self.forest.start_worker(worker_name)


class WorkerWisdomElf:
    """ワーカー学習エルフ"""

    def __init__(self, forest: "ElfForestWorkerManager"):
        """初期化メソッド"""
        self.forest = forest
        self.name = "Sage"
        self.patterns: List[Dict[str, Any]] = []

    async def learn_worker_patterns(self):
        """ワーカーパターン学習"""
        while True:
            try:
                # パフォーマンスデータ収集
                performance_data = self._collect_performance_data()

                # パターン分析
                new_patterns = self._analyze_patterns(performance_data)
                if new_patterns:
                    self.patterns.extend(new_patterns)
                    logger.info(
                        f"🎓 {self.name}: {len(new_patterns)}個の新パターン発見"
                    )

                # 最適化提案
                suggestions = self._generate_suggestions()
                if suggestions:
                    await self.forest.notify_task_elder(
                        {"type": "optimization_suggestions", "suggestions": suggestions}
                    )

                await asyncio.sleep(300)  # 5分ごと

            except Exception as e:
                logger.error(f"{self.name} エラー: {e}")
                await asyncio.sleep(300)

    def _collect_performance_data(self) -> Dict[str, Any]:
        """パフォーマンスデータ収集"""
        data = {}

        for worker_name, status in self.forest.worker_statuses.items():
            data[worker_name] = {
                "cpu_avg": status.cpu_percent,
                "memory_avg": status.memory_mb,
                "tasks_per_hour": status.tasks_processed,
                "error_rate": status.errors / max(status.tasks_processed, 1),
                "queue_size": status.queue_size,
            }

        return data

    def _analyze_patterns(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """パターン分析"""
        patterns = []

        # 高負荷時間帯の検出
        current_hour = datetime.now().hour
        for worker_name, metrics in data.items():
            if metrics["cpu_avg"] > 60:
                patterns.append(
                    {
                        "type": "high_load_time",
                        "worker": worker_name,
                        "hour": current_hour,
                        "cpu": metrics["cpu_avg"],
                    }
                )

        return patterns

    def _generate_suggestions(self) -> List[Dict[str, Any]]:
        """最適化提案生成"""
        suggestions = []

        # 頻繁に高負荷になるワーカーの検出
        high_load_workers = {}
        for pattern in self.patterns:
            if pattern["type"] == "high_load_time":
                worker = pattern["worker"]
                high_load_workers[worker] = high_load_workers.get(worker, 0) + 1

        for worker, count in high_load_workers.items():
            if count > 5:
                suggestions.append(
                    {
                        "worker": worker,
                        "suggestion": "インスタンス数を増やすことを推奨",
                        "reason": f"{count}回の高負荷を検出",
                    }
                )

        return suggestions


class ElfForestWorkerManager:
    """エルフの森ワーカー管理システム"""

    def __init__(self):
        """初期化メソッド"""
        self.worker_statuses: Dict[str, WorkerStatus] = {}
        self.flow_elf = WorkerFlowElf(self)
        self.time_elf = WorkerTimeElf(self)
        self.balance_elf = WorkerBalanceElf(self)
        self.healing_elf = WorkerHealingElf(self)
        self.wisdom_elf = WorkerWisdomElf(self)

        # 各ワーカーの初期ステータス作成
        for worker_name in WORKER_DEFINITIONS:
            self.worker_statuses[worker_name] = WorkerStatus(name=worker_name)

        logger.info("🌲 エルフの森ワーカー管理システムが起動しました")

    async def start(self):
        """システム起動"""
        # 既存ワーカーの状態取得
        await self.update_worker_statuses()

        # エルフたちの活動開始
        tasks = [
            self.flow_elf.monitor_worker_queues(),
            self.time_elf.process_reminders(),
            self.balance_elf.balance_worker_loads(),
            self.healing_elf.heal_sick_workers(),
            self.wisdom_elf.learn_worker_patterns(),
            self._status_update_loop(),
            self._dashboard_loop(),
        ]

        await asyncio.gather(*tasks)

    async def update_worker_statuses(self):
        """ワーカーステータス更新"""
        for worker_name in WORKER_DEFINITIONS:
            status = await self._get_worker_status(worker_name)
            self.worker_statuses[worker_name] = status

    async def _get_worker_status(self, worker_name: str) -> WorkerStatus:
        """ワーカーステータス取得"""
        status = WorkerStatus(name=worker_name)

        # プロセス検索
        for proc in psutil.process_iter(["pid", "cmdline", "create_time"]):
            try:
                cmdline = " ".join(proc.info["cmdline"] or [])
                if worker_name in cmdline:
                    status.pid = proc.info["pid"]
                    status.status = "running"

                    # リソース情報
                    process = psutil.Process(status.pid)
                    status.cpu_percent = process.cpu_percent(interval=0.1)
                    status.memory_mb = process.memory_info().rss / 1024 / 1024

                    # 稼働時間
                    create_time = datetime.fromtimestamp(proc.info["create_time"])
                    status.uptime = datetime.now() - create_time

                    break

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return status

    async def start_worker(self, worker_name: str):
        """ワーカー起動"""
        worker_def = WORKER_DEFINITIONS.get(worker_name)
        if not worker_def:
            logger.error(f"Unknown worker: {worker_name}")
            return

        worker_path = PROJECT_ROOT / worker_def["path"]
        log_path = (
            PROJECT_ROOT
            / "logs"
            / f'{worker_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        )

        # セキュリティ修正: shell=Trueを使わない安全な実装
        with open(log_path, 'w') as log_file:
            subprocess.Popen(
                ['python3', str(worker_path)],
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True  # nohupの代わり
            )

        logger.info(f"✅ {worker_name}を起動しました")
        await asyncio.sleep(2)
        await self.update_worker_statuses()

    async def stop_worker(self, worker_name: str, force: bool = False):
        """ワーカー停止"""
        status = self.worker_statuses.get(worker_name)
        if not status or status.pid is None:
            return

        try:
            process = psutil.Process(status.pid)
            if force:
                process.kill()
            else:
                process.terminate()

            logger.info(f"🛑 {worker_name}を停止しました")

        except psutil.NoSuchProcess:
            pass

        await self.update_worker_statuses()

    async def restart_worker(self, worker_name: str):
        """ワーカー再起動"""
        await self.stop_worker(worker_name)
        await asyncio.sleep(2)
        await self.start_worker(worker_name)

    async def _status_update_loop(self):
        """定期的なステータス更新"""
        while True:
            await self.update_worker_statuses()
            await asyncio.sleep(30)

    async def _dashboard_loop(self):
        """ダッシュボード表示"""
        while True:
            self.display_dashboard()
            await asyncio.sleep(300)  # 5分ごと

    def display_dashboard(self):
        """ダッシュボード表示"""
        print("\n" + "=" * 60)
        print("🌲 エルフの森 - ワーカー管理ダッシュボード 🌲")
        print("=" * 60)
        print(f"時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n📊 ワーカー状態:")
        print("┌─────────────────────┬────────┬─────┬────────┬──────────┐")
        print("│ ワーカー名          │ 状態   │ CPU │ メモリ │ キュー   │")
        print("├─────────────────────┼────────┼─────┼────────┼──────────┤")

        for worker_name, status in self.worker_statuses.items():
            state_icon = "✅" if status.status == "running" else "❌"
            print(
                f"│ {worker_name:<18} │ {state_icon}{status.status:<6} │{status.cpu_percent:4.0f}%│{status.memory_mb:6.0f}MB│{status.queue_size:9}│"
            )

        print("└─────────────────────┴────────┴─────┴────────┴──────────┘")

        # エルフ活動状況
        print("\n🧝 エルフ活動:")
        print(f"- {self.flow_elf.name}: キュー監視中")
        print(f"- {self.time_elf.name}: リマインダー管理中")
        print(f"- {self.balance_elf.name}: 負荷分散実行中")
        print(f"- {self.healing_elf.name}: ワーカー健康管理中")
        print(f"- {self.wisdom_elf.name}: パターン学習中")

        # ボトルネック情報
        bottlenecks = self.flow_elf.detect_worker_bottlenecks()
        if bottlenecks:
            print("\n⚠️ 検出されたボトルネック:")
            for worker, issue in bottlenecks.items():
                print(f"  - {worker}: {issue['type']} ({issue['value']})")

    async def notify_task_elder(self, message: Dict[str, Any]):
        """タスクエルダーへの通知"""
        logger.info(f"📜 タスクエルダーへ: {message}")


# デモ実行
async def demo():
    """デモンストレーション"""
    manager = ElfForestWorkerManager()

    # テスト用リマインダー設定
    manager.time_elf.add_reminder(
        "enhanced_task_worker",
        datetime.now() + timedelta(seconds=10),
        "デモ: 10秒後のリマインダー",
    )

    # 30秒間実行
    try:
        await asyncio.wait_for(manager.start(), timeout=30)
    except asyncio.TimeoutError:
        logger.info("🌙 デモ終了")


if __name__ == "__main__":
    print("🧝‍♂️ エルフの森ワーカー管理システム - デモ実行")
    asyncio.run(demo())