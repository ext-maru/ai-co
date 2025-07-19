#!/usr/bin/env python3
"""
Knights Autonomous Guardian - 騎士団自律運用システム
完全自律的な監視・診断・修復システム

機能:
- 24/7自動監視
- 問題の自動検出・分析
- 自動修復実行
- エスカレーション管理
- セルフヒーリング
"""

import asyncio
import json
import logging
import time
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import schedule

# パス設定
sys.path.append(str(Path(__file__).parent.parent))

from scripts.knights_status_monitor import KnightsStatusMonitor

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/knights_autonomous.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("knights_autonomous_guardian")


class AutonomousAction:
    """自律アクション定義"""

    def __init__(
        self,
        name: str,
        command: List[str],
        timeout: int = 30,
        retry_count: int = 3,
        escalation_threshold: int = 5,
    ):
        self.name = name
        self.command = command
        self.timeout = timeout
        self.retry_count = retry_count
        self.escalation_threshold = escalation_threshold
        self.failure_count = 0
        self.last_execution = None
        self.last_success = None


class KnightsAutonomousGuardian:
    """騎士団自律守護システム"""

    def __init__(self):
        self.monitor = KnightsStatusMonitor()
        self.running = False
        self.check_interval = 60  # 1分ごとにチェック
        self.maintenance_mode = False

        # 自律アクション定義
        self.autonomous_actions = {
            "fix_workers": AutonomousAction(
                name="ワーカー修復",
                command=["python3", "check_and_fix_workers.py"],
                timeout=60,
                retry_count=3,
            ),
            "restart_rabbitmq": AutonomousAction(
                name="RabbitMQ再起動",
                command=["sudo", "systemctl", "restart", "rabbitmq-server"],
                timeout=30,
                retry_count=2,
            ),
            "clean_logs": AutonomousAction(
                name="ログクリーンアップ",
                command=["find", "logs/", "-name", "*.log", "-mtime", "+7", "-delete"],
                timeout=10,
                retry_count=1,
            ),
            "check_disk_space": AutonomousAction(
                name="ディスク容量チェック",
                command=["df", "-h"],
                timeout=5,
                retry_count=1,
            ),
            "update_dependencies": AutonomousAction(
                name="依存関係更新",
                command=[
                    "bash",
                    "-c",
                    "source venv/bin/activate && pip install -r requirements.txt",
                ],
                timeout=300,
                retry_count=1,
            ),
        }

        # 自動修復ルール
        self.auto_repair_rules = {
            "workers_down": {
                "condition": lambda status: status["workers"]["running_count"]
                < status["workers"]["total_expected"],
                "action": "fix_workers",
                "severity": "high",
                "auto_execute": True,
            },
            "rabbitmq_disconnected": {
                "condition": lambda status: status["rabbitmq"]["status"] != "connected",
                "action": "restart_rabbitmq",
                "severity": "critical",
                "auto_execute": True,
            },
            "knights_script_failed": {
                "condition": lambda status: status["local_knights"]["status"]
                != "operational",
                "action": "update_dependencies",
                "severity": "medium",
                "auto_execute": True,
            },
            "disk_space_low": {
                "condition": self._check_disk_space,
                "action": "clean_logs",
                "severity": "medium",
                "auto_execute": True,
            },
        }

        # 統計情報
        self.stats = {
            "start_time": datetime.now(),
            "total_checks": 0,
            "total_issues_detected": 0,
            "total_auto_repairs": 0,
            "successful_repairs": 0,
            "failed_repairs": 0,
            "escalations": 0,
        }

    def _check_disk_space(self, status: Dict) -> bool:
        """ディスク容量チェック"""
        try:
            result = subprocess.run(
                ["df", "/", "--output=pcent"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                usage = int(result.stdout.split("\n")[1].strip().replace("%", ""))
                return usage > 85  # 85%以上で警告
        except Exception:
            pass
        return False

    async def execute_action(self, action_name: str) -> Dict:
        """自律アクションを実行"""
        if action_name not in self.autonomous_actions:
            return {"success": False, "error": "Unknown action"}

        action = self.autonomous_actions[action_name]
        logger.info(f"🤖 Executing autonomous action: {action.name}")

        for attempt in range(action.retry_count):
            try:
                result = subprocess.run(
                    action.command,
                    capture_output=True,
                    text=True,
                    timeout=action.timeout,
                )

                action.last_execution = datetime.now()

                if result.returncode == 0:
                    action.last_success = datetime.now()
                    action.failure_count = 0
                    logger.info(f"✅ Action {action.name} succeeded")

                    return {
                        "success": True,
                        "action": action.name,
                        "attempt": attempt + 1,
                        "output": result.stdout,
                        "execution_time": action.last_execution.isoformat(),
                    }
                else:
                    logger.warning(
                        f"⚠️ Action {action.name} failed (attempt {attempt + 1}): {result.stderr}"
                    )

            except subprocess.TimeoutExpired:
                logger.error(
                    f"⏰ Action {action.name} timed out (attempt {attempt + 1})"
                )
            except Exception as e:
                logger.error(
                    f"❌ Action {action.name} error (attempt {attempt + 1}): {e}"
                )

        # 全試行失敗
        action.failure_count += 1
        logger.error(
            f"🚨 Action {action.name} failed after {action.retry_count} attempts"
        )

        return {
            "success": False,
            "action": action.name,
            "total_attempts": action.retry_count,
            "failure_count": action.failure_count,
            "error": "All retry attempts failed",
        }

    async def analyze_and_repair(self) -> Dict:
        """システム分析と自動修復"""
        logger.info("🔍 Starting autonomous system analysis...")

        # 現在の状況を取得
        current_status = self.monitor.generate_report("dict")
        self.stats["total_checks"] += 1

        analysis_result = {
            "timestamp": datetime.now().isoformat(),
            "overall_health": current_status["overall_health"],
            "issues_detected": [],
            "actions_taken": [],
            "recommendations": [],
        }

        # 各修復ルールをチェック
        for rule_name, rule in self.auto_repair_rules.items():
            try:
                if rule["condition"](current_status):
                    issue = {
                        "rule": rule_name,
                        "severity": rule["severity"],
                        "action_required": rule["action"],
                    }
                    analysis_result["issues_detected"].append(issue)
                    self.stats["total_issues_detected"] += 1

                    logger.warning(
                        f"🚨 Issue detected: {rule_name} (severity: {rule['severity']})"
                    )

                    # 自動修復実行判定
                    if rule["auto_execute"] and not self.maintenance_mode:
                        action_result = await self.execute_action(rule["action"])
                        analysis_result["actions_taken"].append(action_result)
                        self.stats["total_auto_repairs"] += 1

                        if action_result["success"]:
                            self.stats["successful_repairs"] += 1
                            logger.info(f"✅ Auto-repair successful for {rule_name}")
                        else:
                            self.stats["failed_repairs"] += 1
                            logger.error(f"❌ Auto-repair failed for {rule_name}")

                            # エスカレーション判定
                            action = self.autonomous_actions[rule["action"]]
                            if action.failure_count >= action.escalation_threshold:
                                self.stats["escalations"] += 1
                                analysis_result["recommendations"].append(
                                    f"ESCALATION REQUIRED: {rule_name} - manual intervention needed"
                                )
                                logger.critical(
                                    f"🚨 ESCALATION: {rule_name} requires manual intervention"
                                )
                    else:
                        analysis_result["recommendations"].append(
                            f"Manual action recommended: {rule['action']} for {rule_name}"
                        )

            except Exception as e:
                logger.error(f"❌ Error checking rule {rule_name}: {e}")

        # 予防保守の推奨
        if len(analysis_result["issues_detected"]) == 0:
            analysis_result["recommendations"].append(
                "System healthy - no immediate action required"
            )
            logger.info("✅ System health check passed - all systems operational")

        return analysis_result

    async def scheduled_maintenance(self):
        """定期メンテナンス実行"""
        logger.info("🔧 Starting scheduled maintenance...")

        maintenance_tasks = [
            ("clean_logs", "Log cleanup"),
            ("check_disk_space", "Disk space check"),
        ]

        for action_name, description in maintenance_tasks:
            logger.info(f"🔧 Maintenance: {description}")
            result = await self.execute_action(action_name)

            if result["success"]:
                logger.info(f"✅ Maintenance completed: {description}")
            else:
                logger.warning(f"⚠️ Maintenance issue: {description}")

    def generate_health_report(self) -> Dict:
        """健康状態レポート生成"""
        uptime = datetime.now() - self.stats["start_time"]

        return {
            "guardian_status": {
                "running": self.running,
                "uptime_seconds": int(uptime.total_seconds()),
                "uptime_human": str(uptime),
                "maintenance_mode": self.maintenance_mode,
            },
            "statistics": self.stats.copy(),
            "action_status": {
                name: {
                    "failure_count": action.failure_count,
                    "last_execution": (
                        action.last_execution.isoformat()
                        if action.last_execution
                        else None
                    ),
                    "last_success": (
                        action.last_success.isoformat() if action.last_success else None
                    ),
                }
                for name, action in self.autonomous_actions.items()
            },
            "efficiency_metrics": {
                "success_rate": (
                    self.stats["successful_repairs"]
                    / max(1, self.stats["total_auto_repairs"])
                )
                * 100,
                "average_checks_per_hour": self.stats["total_checks"]
                / max(1, uptime.total_seconds() / 3600),
                "escalation_rate": (
                    self.stats["escalations"]
                    / max(1, self.stats["total_issues_detected"])
                )
                * 100,
            },
        }

    async def autonomous_loop(self):
        """自律監視ループ"""
        logger.info("🚀 Knights Autonomous Guardian starting...")
        self.running = True

        # 定期メンテナンスのスケジュール
        schedule.every().day.at("02:00").do(
            lambda: asyncio.create_task(self.scheduled_maintenance())
        )
        schedule.every().sunday.at("03:00").do(
            lambda: asyncio.create_task(self.execute_action("update_dependencies"))
        )

        try:
            while self.running:
                start_time = time.time()

                # メインの分析・修復サイクル
                try:
                    analysis = await self.analyze_and_repair()

                    # 重要な問題がある場合はログに記録
                    if analysis["issues_detected"]:
                        report_file = Path(
                            f"logs/autonomous_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        )
                        with open(report_file, "w") as f:
                            json.dump(analysis, f, indent=2)
                        logger.info(f"📄 Analysis report saved: {report_file}")

                except Exception as e:
                    logger.error(f"❌ Error in analysis cycle: {e}")

                # スケジュールされたタスクを実行
                schedule.run_pending()

                # 次のチェックまで待機
                elapsed = time.time() - start_time
                sleep_time = max(0, self.check_interval - elapsed)

                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("🛑 Shutdown signal received")
        finally:
            self.running = False
            logger.info("🔌 Knights Autonomous Guardian stopped")

    def stop(self):
        """守護システム停止"""
        self.running = False


async def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(description="Knights Autonomous Guardian")
    parser.add_argument(
        "--maintenance",
        action="store_true",
        help="Enable maintenance mode (no auto-repairs)",
    )
    parser.add_argument(
        "--interval", type=int, default=60, help="Check interval in seconds"
    )
    parser.add_argument(
        "--report", action="store_true", help="Generate health report and exit"
    )

    args = parser.parse_args()

    # ログディレクトリ作成
    Path("logs").mkdir(exist_ok=True)

    guardian = KnightsAutonomousGuardian()
    guardian.check_interval = args.interval
    guardian.maintenance_mode = args.maintenance

    if args.report:
        # ヘルスレポートのみ生成
        report = guardian.generate_health_report()
        print("🛡️ Knights Autonomous Guardian Health Report")
        print("=" * 50)
        print(json.dumps(report, indent=2))
        return

    logger.info(
        f"""
🛡️ Knights Autonomous Guardian Configuration:
- Check interval: {args.interval} seconds
- Maintenance mode: {args.maintenance}
- Auto-repair: {'Disabled' if args.maintenance else 'Enabled'}
- Log file: logs/knights_autonomous.log

Starting autonomous operations...
"""
    )

    # 自律監視開始
    await guardian.autonomous_loop()


if __name__ == "__main__":
    asyncio.run(main())
