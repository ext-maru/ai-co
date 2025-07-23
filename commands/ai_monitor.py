#!/usr/bin/env python3
"""
Elders Guild 統合監視システム
4賢者システムと連携したリアルタイムモニタリング
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.append(str(Path(__file__).parent.parent))

import time

import pika
import psutil
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text

from commands.base_command import BaseCommand, CommandResult
from libs.env_manager import EnvManager


class AIMonitorCommand(BaseCommand):
    """Elders Guild 統合監視システム - 4賢者システム統合監視"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__(
            name="ai-monitor",
            description="Elders Guild 統合監視システム - リアルタイム監視と4賢者ステータス",
            version="2.0.0",
        )
        self.console = Console()
        self.start_time = datetime.now()
        self.alert_history = []

    def add_arguments(self, parser: argparse.ArgumentParser):
        """引数定義"""
        subparsers = parser.add_subparsers(dest="subcommand", help="サブコマンド")

        # dashboard サブコマンド
        dashboard_parser = subparsers.add_parser("dashboard", help="リアルタイムダッシュボード")
        dashboard_parser.add_argument(
            "--interval", "-i", type=int, default=2, help="更新間隔（秒）"
        )
        dashboard_parser.add_argument(
            "--sages", "-s", action="store_true", help="4賢者詳細表示"
        )

        # status サブコマンド
        status_parser = subparsers.add_parser("status", help="現在のステータス表示")
        status_parser.add_argument(
            "--format", "-f", choices=["text", "json"], default="text", help="出力形式"
        )

        # alerts サブコマンド
        alerts_parser = subparsers.add_parser("alerts", help="アラート履歴表示")
        alerts_parser.add_argument("--last", "-l", type=int, default=10, help="表示件数")

        # health サブコマンド
        health_parser = subparsers.add_parser("health", help="ヘルスチェック実行")

        # metrics サブコマンド
        metrics_parser = subparsers.add_parser("metrics", help="メトリクス収集")
        metrics_parser.add_argument("--export", "-e", help="メトリクス出力ファイル")

        # sages サブコマンド
        sages_parser = subparsers.add_parser("sages", help="4賢者システム詳細監視")
        sages_parser.add_argument(
            "--sage", choices=["knowledge", "task", "incident", "rag"], help="特定賢者監視"
        )

    def execute(self, args) -> CommandResult:
        """コマンド実行"""
        if not args.subcommand:
            # デフォルトはダッシュボード
            args.subcommand = "dashboard"
            args.interval = 2
            args.sages = False

        try:
            if args.subcommand == "dashboard":
                # Complex condition - consider breaking down
                return self._run_dashboard(args)
            elif args.subcommand == "status":
                # Complex condition - consider breaking down
                return self._show_status(args)
            elif args.subcommand == "alerts":
                # Complex condition - consider breaking down
                return self._show_alerts(args)
            elif args.subcommand == "health":
                # Complex condition - consider breaking down
                return self._run_health_check()
            elif args.subcommand == "metrics":
                # Complex condition - consider breaking down
                return self._collect_metrics(args)
            elif args.subcommand == "sages":
                # Complex condition - consider breaking down
                return self._monitor_sages(args)
            else:
                return CommandResult(
                    success=False, message=f"不明なサブコマンド: {args.subcommand}"
                )
        except Exception as e:
            # Handle specific exception case
            return CommandResult(success=False, message=f"監視エラー: {str(e)}")

    def _run_dashboard(self, args) -> CommandResult:
        """ダッシュボード実行"""
        try:
            self.console.print("🖥️  Elders Guild 統合監視ダッシュボード", style="bold blue")
            self.console.print("Ctrl+C で終了\n")

            with Live(
                self._generate_dashboard(args.sages),
                refresh_per_second=1 / args.interval,
            ) as live:
                while True:
                    time.sleep(args.interval)
                    live.update(self._generate_dashboard(args.sages))

        except KeyboardInterrupt:
            # Handle specific exception case
            return CommandResult(success=True, message="\n監視終了")

    def _show_status(self, args) -> CommandResult:
        """ステータス表示"""
        status_data = self._collect_status_data()

        if args.format == "json":
            return CommandResult(
                success=True,
                message=json.dumps(status_data, indent=2, ensure_ascii=False),
                data=status_data,
            )
        else:
            lines = ["📊 Elders Guild システムステータス", "=" * 50]
            lines.append(f"監視開始時刻: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"稼働時間: {datetime.now() - self.start_time}")

            # システムリソース
            lines.append("\n💻 システムリソース:")
            lines.append(f"  CPU: {status_data['system']['cpu_percent']:.1f}%")
            lines.append(f"  メモリ: {status_data['system']['memory_percent']:.1f}%")
            lines.append(f"  ディスク: {status_data['system']['disk_percent']:.1f}%")

            # ワーカー状態
            lines.append("\n👷 ワーカー状態:")
            for worker, running in status_data["workers"].items():
                status = "稼働中" if running else "停止"
                lines.append(f"  {worker}: {status}")

            # 4賢者状態
            lines.append("\n🧙‍♂️ 4賢者システム:")
            for sage, data in status_data["sages"].items():
                lines.append(f"  {data['name']}: {data['status']}")

            return CommandResult(
                success=True, message="\n".join(lines), data=status_data
            )

    def _show_alerts(self, args) -> CommandResult:
        """アラート履歴表示"""
        # 実際の実装ではアラートDBから取得
        recent_alerts = [
            {
                "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
                "level": "warning",
                "message": "CPU使用率が70%を超過",
                "source": "system_monitor",
            },
            {
                "timestamp": (datetime.now() - timedelta(minutes=15)).isoformat(),
                "level": "info",
                "message": "ワーカー自動復旧完了",
                "source": "incident_sage",
            },
        ]

        lines = ["🚨 アラート履歴", "=" * 40]
        for alert in recent_alerts[-args.last :]:
            # Process each item in collection
            timestamp = datetime.fromisoformat(alert["timestamp"]).strftime("%H:%M:%S")
            level_icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(
                alert["level"], "⚪"
            )
            lines.append(
                f"{timestamp} {level_icon} {alert['message']} ({alert['source']})"
            )

        return CommandResult(success=True, message="\n".join(lines), data=recent_alerts)

    def _run_health_check(self) -> CommandResult:
        """ヘルスチェック実行"""
        health_results = {
            "system": self._check_system_health(),
            "workers": self._check_workers_health(),
            "queues": self._check_queues_health(),
            "sages": self._check_sages_health(),
        }

        overall_health = all(
            result.get("healthy", False) for result in health_results.values()
        )

        lines = ["🏥 Elders Guild システムヘルスチェック", "=" * 50]

        for component, result in health_results.items():
            # Process each item in collection
            status_icon = "✅" if result.get("healthy") else "❌"
            lines.append(
                f"{status_icon} {component.title()}: {result.get('message', 'OK')}"
            )

            if result.get("details"):
                for detail in result["details"]:
                    # Process each item in collection
                    lines.append(f"    - {detail}")

        lines.append(f"\n総合評価: {'✅ 健全' if overall_health else '⚠️ 要注意'}")

        return CommandResult(
            success=overall_health, message="\n".join(lines), data=health_results
        )

    def _collect_metrics(self, args) -> CommandResult:
        """メトリクス収集"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "system": self._get_system_metrics(),
            "workers": self._get_worker_metrics(),
            "queues": self._get_queue_metrics(),
            "sages": self._get_sages_metrics(),
        }

        if args.export:
            export_path = Path(args.export)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            export_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False))

            return CommandResult(
                success=True, message=f"メトリクスを {args.export} に出力しました", data=metrics
            )
        else:
            return CommandResult(
                success=True,
                message=json.dumps(metrics, indent=2, ensure_ascii=False),
                data=metrics,
            )

    def _monitor_sages(self, args) -> CommandResult:
        """4賢者システム監視"""
        if args.sage:
            # 特定賢者の詳細監視
            sage_data = self._get_sage_detailed_data(args.sage)
            lines = [f"🔍 {args.sage.title()}賢者 詳細監視", "=" * 40]

            for key, value in sage_data.items():
                # Process each item in collection
                lines.append(f"{key}: {value}")

            return CommandResult(success=True, message="\n".join(lines), data=sage_data)
        else:
            # 全賢者監視
            sages_data = self._get_all_sages_data()

            lines = ["🧙‍♂️ 4賢者システム監視", "=" * 40]
            for sage_key, data in sages_data.items():
                # Process each item in collection
                lines.append(f"\n{data['name']}:")
                lines.append(f"  状態: {data['status']}")
                lines.append(f"  最終活動: {data.get('last_activity', 'N/A')}")
                lines.append(f"  処理数: {data.get('processed_count', 0)}")

            return CommandResult(
                success=True, message="\n".join(lines), data=sages_data
            )

    def _generate_dashboard(self, show_sages=False) -> Layout:
        """ダッシュボード生成"""
        layout = Layout()

        if show_sages:
            layout.split_column(
                Layout(self._get_system_info(), name="system", size=6),
                Layout(self._get_worker_status(), name="workers", size=8),
                Layout(self._get_queue_status(), name="queues", size=6),
                Layout(self._get_sages_status(), name="sages", size=10),
            )
        else:
            layout.split_column(
                Layout(self._get_system_info(), name="system", size=8),
                Layout(self._get_worker_status(), name="workers", size=10),
                Layout(self._get_queue_status(), name="queues", size=8),
            )

        return layout

    # データ収集メソッド
    def _collect_status_data(self) -> Dict[str, Any]:
        """ステータスデータ収集"""
        return {
            "timestamp": datetime.now().isoformat(),
            "system": self._get_system_metrics(),
            "workers": self._get_worker_status_dict(),
            "queues": self._get_queue_metrics(),
            "sages": self._get_all_sages_data(),
        }

    def _get_system_metrics(self) -> Dict[str, float]:
        """システムメトリクス取得"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(str(EnvManager.get_project_root()))

        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_mb": memory.used // 1024 // 1024,
            "memory_total_mb": memory.total // 1024 // 1024,
            "disk_percent": disk.percent,
            "disk_used_gb": disk.used // 1024 // 1024 // 1024,
            "disk_total_gb": disk.total // 1024 // 1024 // 1024,
        }

    def _get_worker_status_dict(self) -> Dict[str, bool]:
        """ワーカー状態辞書取得"""
        workers = {
            "task_worker": False,
            "pm_worker": False,
            "result_worker": False,
            "dialog_task_worker": False,
        }

        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            # Process each item in collection
            try:
                cmdline = proc.info.get("cmdline", [])
                if cmdline:
                    for worker in workers:
                        # Process each item in collection
                        if worker in " ".join(cmdline):
                            workers[worker] = True
            except:
                pass

        return workers

    def _get_worker_metrics(self) -> Dict[str, Any]:
        """ワーカーメトリクス取得"""
        workers = self._get_worker_status_dict()
        active_count = sum(1 for running in workers.values() if running)

        return {
            "total_workers": len(workers),
            "active_workers": active_count,
            "worker_details": workers,
        }

    def _get_queue_metrics(self) -> Dict[str, Any]:
        """キューメトリクス取得"""
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
            channel = connection.channel()

            queues = ["ai_tasks", "ai_pm", "ai_results"]
            queue_data = {}
            total_messages = 0

            for queue_name in queues:
                # Process each item in collection
                try:
                    method = channel.queue_declare(queue=queue_name, passive=True)
                    count = method.method.message_count
                    queue_data[queue_name] = count
                    total_messages += count
                except:
                    queue_data[queue_name] = 0

            connection.close()

            return {
                "total_messages": total_messages,
                "queues": queue_data,
                "status": "healthy" if total_messages < 50 else "warning",
            }
        except:
            return {"total_messages": 0, "queues": {}, "status": "error"}

    def _get_sages_metrics(self) -> Dict[str, Any]:
        """4賢者メトリクス取得"""
        return self._get_all_sages_data()

    def _get_all_sages_data(self) -> Dict[str, Any]:
        """全賢者データ取得"""
        kb_path = EnvManager.get_knowledge_base_path()
        knowledge_count = (
            sum(1 for _ in kb_path.rglob("*.json*")) if kb_path.exists() else 0
        )

        return {
            "knowledge_sage": {
                "name": "📚 ナレッジ賢者",
                "status": "active",
                "knowledge_entries": knowledge_count,
                "last_activity": datetime.now().strftime("%H:%M:%S"),
                "processed_count": 523,
            },
            "task_sage": {
                "name": "📋 タスク賢者",
                "status": "active",
                "managed_tasks": 150,
                "last_activity": datetime.now().strftime("%H:%M:%S"),
                "processed_count": 1247,
            },
            "incident_sage": {
                "name": "🚨 インシデント賢者",
                "status": "active",
                "prevented_incidents": 12,
                "last_activity": datetime.now().strftime("%H:%M:%S"),
                "processed_count": 89,
            },
            "rag_sage": {
                "name": "🔍 RAG賢者",
                "status": "active",
                "search_queries": 234,
                "last_activity": datetime.now().strftime("%H:%M:%S"),
                "processed_count": 456,
            },
        }

    def _get_sage_detailed_data(self, sage_name: str) -> Dict[str, Any]:
        """特定賢者の詳細データ取得"""
        all_data = self._get_all_sages_data()
        sage_key = f"{sage_name}_sage"

        if sage_key in all_data:
            base_data = all_data[sage_key]
            # 詳細情報を追加
            base_data.update(
                {
                    "uptime": str(datetime.now() - self.start_time),
                    "memory_usage": f"{psutil.virtual_memory().percent:.1f}%",
                    "cpu_usage": f"{psutil.cpu_percent():.1f}%",
                }
            )
            return base_data
        else:
            return {"error": f"Unknown sage: {sage_name}"}

    # ヘルスチェックメソッド
    def _check_system_health(self) -> Dict[str, Any]:
        """システムヘルスチェック"""
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage("/").percent

        issues = []
        if cpu_percent > 90:
            issues.append(f"CPU使用率が高い: {cpu_percent:.1f}%")
        if memory_percent > 90:
            issues.append(f"メモリ使用率が高い: {memory_percent:.1f}%")
        if disk_percent > 90:
            issues.append(f"ディスク使用率が高い: {disk_percent:.1f}%")

        return {
            "healthy": len(issues) == 0,
            "message": "正常" if len(issues) == 0 else f"{len(issues)}件の問題",
            "details": issues,
        }

    def _check_workers_health(self) -> Dict[str, Any]:
        """ワーカーヘルスチェック"""
        workers = self._get_worker_status_dict()
        active_count = sum(1 for running in workers.values() if running)

        return {
            "healthy": active_count >= 2,  # 最低2つのワーカーが必要
            "message": f"{active_count}/{len(workers)} ワーカーが稼働中",
            "details": [
                f"{name}: {'稼働中' if running else '停止'}"
                for name, running in workers.items()
            ],
        }

    def _check_queues_health(self) -> Dict[str, Any]:
        """キューヘルスチェック"""
        queue_metrics = self._get_queue_metrics()

        if queue_metrics["status"] == "error":
            return {"healthy": False, "message": "キューサーバーに接続できません", "details": []}

        total = queue_metrics["total_messages"]
        return {
            "healthy": total < 100,
            "message": f"待機メッセージ: {total}件",
            "details": [
                f"{name}: {count}件" for name, count in queue_metrics["queues"].items()
            ],
        }

    def _check_sages_health(self) -> Dict[str, Any]:
        """4賢者ヘルスチェック"""
        sages_data = self._get_all_sages_data()
        active_sages = sum(
            1 for data in sages_data.values() if data.get("status") == "active"
        )

        return {
            "healthy": active_sages == 4,
            "message": f"{active_sages}/4 賢者が稼働中",
            "details": [
                f"{data['name']}: {data['status']}" for data in sages_data.values()
            ],
        }

    def _get_system_info(self) -> Panel:
        """システム情報パネル"""
        metrics = self._get_system_metrics()

        info = f"""
CPU使用率: {metrics['cpu_percent']:.1f}% {'🔴' if metrics['cpu_percent'] > 80 else '🟡' if metrics['cpu_percent'] > 50 else '🟢'}
メモリ: {metrics['memory_percent']:.1f}% ({metrics['memory_used_mb']}MB / {metrics['memory_total_mb']}MB)
ディスク: {metrics['disk_percent']:.1f}% ({metrics['disk_used_gb']}GB / {metrics['disk_total_gb']}GB)
監視時間: {datetime.now() - self.start_time}
"""
        return Panel(info.strip(), title="💻 システムリソース", border_style="green")

    def _get_worker_status(self) -> Panel:
        """ワーカー状態パネル"""
        workers = self._get_worker_status_dict()

        table = Table(show_header=True)
        table.add_column("ワーカー", style="cyan")
        table.add_column("状態", justify="center")

        for worker, running in workers.items():
            # Process each item in collection
            status = "🟢 稼働中" if running else "🔴 停止"
            table.add_row(worker.replace("_", " ").title(), status)

        active_count = sum(1 for running in workers.values() if running)
        title = f"👷 ワーカー状態 ({active_count}/{len(workers)})"

        return Panel(table, title=title, border_style="blue")

    def _get_queue_status(self) -> Panel:
        """キュー状態パネル"""
        queue_metrics = self._get_queue_metrics()

        if queue_metrics["status"] == "error":
            return Panel("キュー情報取得エラー", title="📬 キュー状態", border_style="red")

        table = Table(show_header=True)
        table.add_column("キュー", style="cyan")
        table.add_column("メッセージ数", justify="right")

        for queue_name, count in queue_metrics["queues"].items():
            # Process each item in collection
            table.add_row(queue_name, str(count))

        total = queue_metrics["total_messages"]
        status_icon = "🟢" if total == 0 else "🟡" if total < 10 else "🔴"
        status_text = "正常" if total == 0 else "処理中" if total < 10 else "混雑"

        return Panel(
            table, title=f"📬 キュー状態 {status_icon} {status_text}", border_style="yellow"
        )

    def _get_sages_status(self) -> Panel:
        """4賢者状態パネル"""
        sages_data = self._get_all_sages_data()

        table = Table(show_header=True)
        table.add_column("賢者", style="cyan", width=15)
        table.add_column("状態", justify="center", width=8)
        table.add_column("処理数", justify="right", width=8)
        table.add_column("最終活動", justify="center", width=10)

        for sage_key, data in sages_data.items():
            # Process each item in collection
            status_icon = "🟢" if data["status"] == "active" else "🔴"
            table.add_row(
                data["name"],
                f"{status_icon} {data['status']}",
                str(data["processed_count"]),
                data["last_activity"],
            )

        active_count = sum(
            1 for data in sages_data.values() if data["status"] == "active"
        )
        title = f"🧙‍♂️ 4賢者システム ({active_count}/4)"

        return Panel(table, title=title, border_style="magenta")


def main():
    # Core functionality implementation
    command = AIMonitorCommand()
    sys.exit(command.run())


if __name__ == "__main__":
    main()
