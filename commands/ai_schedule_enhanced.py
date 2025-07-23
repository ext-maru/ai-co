#!/usr/bin/env python3
"""
Elders Guild - APScheduler統合スケジュール管理コマンド
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, "/root/ai_co")

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from commands.base_command import BaseCommand, CommandResult
from libs.apscheduler_integration import get_elder_scheduler, get_scheduler_stats


class AIScheduleEnhancedCommand(BaseCommand):
    """APScheduler統合スケジュール管理コマンド"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__(
            name="schedule-enhanced", description="Elders Guild APScheduler統合スケジュール管理", version="2.0.0"
        )
        self.console = Console()
        self.scheduler = get_elder_scheduler()

    def setup_arguments(self):
        """引数設定"""
        self.parser.add_argument(
            "action", 
            choices=["list", "add", "remove", "status", "start", "stop", "pause", "resume", "stats"], 
            help="実行するアクション"
        )
        self.parser.add_argument("--job-id", help="ジョブID")
        self.parser.add_argument("--name", help="ジョブ名")
        self.parser.add_argument("--trigger", choices=["interval", "cron", "date"], help="トリガータイプ")
        self.parser.add_argument("--seconds", type=int, help="秒間隔")
        self.parser.add_argument("--minutes", type=int, help="分間隔")
        self.parser.add_argument("--hours", type=int, help="時間間隔")
        self.parser.add_argument("--cron", help="Cron式")
        self.parser.add_argument("--function", help="実行する関数名")

    def execute(self, args) -> CommandResult:
        """実行"""
        try:
            if args.action == "list":
                return self._handle_list()
            elif args.action == "status":
                return self._handle_status()
            elif args.action == "start":
                return self._handle_start()
            elif args.action == "stop":
                return self._handle_stop()
            elif args.action == "add":
                return self._handle_add(args)
            elif args.action == "remove":
                return self._handle_remove(args)
            elif args.action == "pause":
                return self._handle_pause(args)
            elif args.action == "resume":
                return self._handle_resume(args)
            elif args.action == "stats":
                return self._handle_stats()
            else:
                return CommandResult(success=False, message=f"Unknown action: {args.action}")
        except Exception as e:
            # Handle specific exception case
            return CommandResult(success=False, message=f"Error: {str(e)}")
            
    def _handle_list(self) -> CommandResult:
        """ジョブ一覧表示"""
        jobs = self.scheduler.get_jobs()
        
        if not jobs:
            self.console.print("📅 登録済みジョブはありません")
            return CommandResult(success=True)
            
        table = Table(title="📅 登録済みスケジュールジョブ")
        table.add_column("ID", style="cyan")
        table.add_column("名前", style="magenta")
        table.add_column("次回実行", style="green")
        table.add_column("トリガー", style="yellow")
        table.add_column("状態", style="blue")
        
        for job in jobs:
            # Process each item in collection
            next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else "N/A"
            table.add_row(
                job.id,
                job.name or "Unnamed",
                next_run,
                str(job.trigger),
                "⏸️ 停止中" if job.next_run_time is None else "▶️ 実行中"
            )
            
        self.console.print(table)
        return CommandResult(success=True)
        
    def _handle_status(self) -> CommandResult:
        """スケジューラー状態表示"""
        running = self.scheduler.scheduler.running
        job_count = len(self.scheduler.get_jobs())
        
        status_text = "✅ 動作中" if running else "🛑 停止中"
        
        panel = Panel(
            f"[bold]スケジューラー状態:[/bold] {status_text}\n"
            f"[bold]登録ジョブ数:[/bold] {job_count}\n"
            f"[bold]最大ワーカー数:[/bold] {self.scheduler.config.max_workers}",
            title="⏰ Elder Scheduler Status",
            border_style="green" if running else "red"
        )
        
        self.console.print(panel)
        return CommandResult(success=True)
        
    def _handle_start(self) -> CommandResult:
        """スケジューラー開始"""
        if self.scheduler.scheduler.running:
            self.console.print("⚠️ スケジューラーは既に動作中です")
            return CommandResult(success=True)
            
        self.scheduler.start()
        self.console.print("🚀 スケジューラーを開始しました")
        return CommandResult(success=True)
        
    def _handle_stop(self) -> CommandResult:
        """スケジューラー停止"""
        if not self.scheduler.scheduler.running:
            self.console.print("⚠️ スケジューラーは既に停止中です")
            return CommandResult(success=True)
            
        self.scheduler.shutdown()
        self.console.print("🛑 スケジューラーを停止しました")
        return CommandResult(success=True)
        
    def _handle_add(self, args) -> CommandResult:
        """ジョブ追加"""
        if not args.trigger:
            return CommandResult(success=False, message="--trigger は必須です")
            
        if not args.function:
            return CommandResult(success=False, message="--function は必須です")
            
        # 簡単なテスト関数を定義
        def test_function():
            print(f"🎯 Test job executed at {datetime.now()}")
            
        trigger_args = {}
        
        if args.trigger == "interval":
            if args.seconds:
                trigger_args['seconds'] = args.seconds
            elif args.minutes:
                trigger_args['minutes'] = args.minutes
            elif args.hours:
                trigger_args['hours'] = args.hours
            else:
                return CommandResult(success=False, message="interval trigger requires --seconds, --minutes, or \
                    --hours" \
                    "interval trigger requires --seconds, --minutes, or --hours" \
                    "interval trigger requires --seconds, --minutes, or --hours")
                
        elif args.trigger == "cron":
            if not args.cron:
                return CommandResult(success=False, message="cron trigger requires --cron expression" \
                    "cron trigger requires --cron expression" \
                    "cron trigger requires --cron expression")
            # Cron式を解析（簡単な例）
            parts = args.cron.split()
            if len(parts) == 5:
                trigger_args.update({
                    'minute': parts[0],
                    'hour': parts[1],
                    'day': parts[2],
                    'month': parts[3],
                    'day_of_week': parts[4]
                })
            else:
                return CommandResult(success=False, message="Invalid cron expression")
                
        job = self.scheduler.add_job(
            func=test_function,
            trigger=args.trigger,
            id=args.job_id,
            name=args.name,
            **trigger_args
        )
        
        self.console.print(f"✅ ジョブを追加しました: {job.id}")
        return CommandResult(success=True)
        
    def _handle_remove(self, args) -> CommandResult:
        """ジョブ削除"""
        if not args.job_id:
            return CommandResult(success=False, message="--job-id は必須です")
            
        try:
            self.scheduler.remove_job(args.job_id)
            self.console.print(f"🗑️ ジョブを削除しました: {args.job_id}")
            return CommandResult(success=True)
        except Exception as e:
            # Handle specific exception case
            return CommandResult(success=False, message=f"ジョブ削除失敗: {str(e)}")
            
    def _handle_pause(self, args) -> CommandResult:
        """ジョブ一時停止"""
        if not args.job_id:
            return CommandResult(success=False, message="--job-id は必須です")
            
        try:
            self.scheduler.pause_job(args.job_id)
            self.console.print(f"⏸️ ジョブを一時停止しました: {args.job_id}")
            return CommandResult(success=True)
        except Exception as e:
            # Handle specific exception case
            return CommandResult(success=False, message=f"ジョブ一時停止失敗: {str(e)}")
            
    def _handle_resume(self, args) -> CommandResult:
        """ジョブ再開"""
        if not args.job_id:
            return CommandResult(success=False, message="--job-id は必須です")
            
        try:
            self.scheduler.resume_job(args.job_id)
            self.console.print(f"▶️ ジョブを再開しました: {args.job_id}")
            return CommandResult(success=True)
        except Exception as e:
            # Handle specific exception case
            return CommandResult(success=False, message=f"ジョブ再開失敗: {str(e)}")
            
    def _handle_stats(self) -> CommandResult:
        """統計情報表示"""
        stats = get_scheduler_stats()
        
        panel = Panel(
            f"[bold]総実行回数:[/bold] {stats['total_executed']}\n"
            f"[bold]エラー回数:[/bold] {stats['total_errors']}\n"
            f"[bold]最終実行:[/bold] {stats['last_execution'] or 'なし'}\n"
            f"[bold]アクティブジョブ:[/bold] {stats['active_jobs']}",
            title="📊 Scheduler Statistics",
            border_style="blue"
        )
        
        self.console.print(panel)
        return CommandResult(success=True)


def main():
    # Core functionality implementation
    command = AIScheduleEnhancedCommand()
    return command.run()


if __name__ == "__main__":
    sys.exit(main())