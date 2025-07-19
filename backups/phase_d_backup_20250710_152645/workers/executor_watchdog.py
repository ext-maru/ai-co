#!/usr/bin/env python3
"""
Executor Watchdog - Elders Guild System Guardian
コマンドエグゼキュータ監視員 - エルダー評議会のシステム守護者

This worker serves as the system guardian within the Elder Tree hierarchy,
reporting to the Incident Sage and ensuring service reliability.
"""

import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import EMOJI, setup_logging
from libs.slack_notifier import SlackNotifier

# Elder Tree imports
try:
    from libs.elder_council_summoner import ElderCouncilSummoner
    from libs.elder_tree_hierarchy import (
        ElderMessage,
        ElderRank,
        SageType,
        get_elder_tree,
    )
    from libs.four_sages_integration import FourSagesIntegration

    ELDER_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"Elder system not available: {e}")
    ELDER_SYSTEM_AVAILABLE = False
    FourSagesIntegration = None
    ElderCouncilSummoner = None


class CommandExecutorWatchdog:
    """Executor Watchdog - System guardian of the Elder Tree hierarchy"""

    def __init__(self):
        self.logger = setup_logging(
            name="CommandExecutorWatchdog",
            log_file=PROJECT_ROOT / "logs" / "executor_watchdog.log",
        )
        self.slack = SlackNotifier()
        self.running = True
        self.check_interval = 30  # 30秒ごとにチェック
        self.restart_count = 0
        self.max_restarts = 10  # 最大再起動回数
        self.created_at = datetime.now()

        # Initialize Elder systems
        self.elder_systems_initialized = False
        self._initialize_elder_systems()

        self.logger.info(f"ExecutorWatchdog initialized as Elder Tree system guardian")

    def _initialize_elder_systems(self):
        """Initialize Elder Tree hierarchy systems with error handling"""
        if not ELDER_SYSTEM_AVAILABLE:
            self.logger.warning(
                "Elder systems not available, running in standalone mode"
            )
            self.four_sages = None
            self.council_summoner = None
            self.elder_tree = None
            return

        try:
            # Initialize Four Sages Integration
            self.four_sages = FourSagesIntegration()
            self.logger.info("Four Sages Integration initialized successfully")

            # Initialize Elder Council Summoner
            self.council_summoner = ElderCouncilSummoner()
            self.logger.info("Elder Council Summoner initialized successfully")

            # Get Elder Tree reference
            self.elder_tree = get_elder_tree()
            self.logger.info("Elder Tree hierarchy connected")

            self.elder_systems_initialized = True

        except Exception as e:
            self.logger.error(f"Failed to initialize Elder systems: {e}")
            self.four_sages = None
            self.council_summoner = None
            self.elder_tree = None
            self.elder_systems_initialized = False

    def run(self):
        """メインループ with Elder Tree integration"""
        self.logger.info(
            f"{EMOJI['start']} Command Executor Watchdog started as Elder Tree guardian"
        )

        # Report startup to Task Sage
        if self.elder_systems_initialized:
            self._report_startup_to_task_sage()

        # シグナルハンドラ設定
        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGINT, self.handle_signal)

        try:
            while self.running:
                if not self.check_executor_running():
                    self._handle_executor_failure_with_elders()
                    self.restart_executor()

                time.sleep(self.check_interval)

        except Exception as e:
            self._report_watchdog_error_to_incident_sage(e)
            self.logger.error(f"Watchdog error: {e}")

    def _handle_executor_failure_with_elders(self):
        """Handle executor failure with Elder Tree integration"""
        if self.elder_systems_initialized:
            try:
                failure_data = {
                    "type": "executor_failure",
                    "restart_count": self.restart_count,
                    "max_restarts": self.max_restarts,
                    "timestamp": datetime.now().isoformat(),
                    "critical": self.restart_count >= self.max_restarts - 2,
                }

                # Report to Incident Sage
                self.four_sages.consult_incident_sage(failure_data)

                # Escalate if approaching max restarts
                if self.restart_count >= self.max_restarts - 2:
                    self._escalate_to_claude_elder(failure_data)

            except Exception as e:
                self.logger.error(f"Failed to report executor failure to Elders: {e}")

    def handle_signal(self, signum, frame):
        """シグナルハンドラ"""
        self.logger.info(f"{EMOJI['stop']} Received signal {signum}, shutting down...")

        # Report shutdown to Task Sage
        if self.elder_systems_initialized:
            self._report_shutdown_to_task_sage(signum)

        self.running = False

    def check_executor_running(self):
        """Command Executorが動作しているか確認"""
        for proc in psutil.process_iter(["pid", "cmdline"]):
            try:
                cmdline = proc.info.get("cmdline", [])
                if cmdline and "command_executor_worker.py" in " ".join(cmdline):
                    return True
            except:
                pass
        return False

    def restart_executor(self):
        """Command Executorを再起動 with Elder reporting"""
        if self.restart_count >= self.max_restarts:
            error_msg = (
                f"Maximum restart attempts ({self.max_restarts}) reached. Giving up."
            )
            self.logger.error(error_msg)

            # Report critical failure to Elder Tree
            if self.elder_systems_initialized:
                self._escalate_critical_failure_to_claude_elder()

            self.slack.send_message(message=f"🚨 {error_msg}", channel="#alerts")
            self.running = False
            return False

        self.restart_count += 1
        self.logger.info(
            f"Attempting to restart Command Executor (attempt {self.restart_count})"
        )

        # Report restart attempt to Task Sage
        if self.elder_systems_initialized:
            self._report_restart_attempt_to_task_sage()

        try:
            # tmuxで起動
            cmd = f"""
cd {PROJECT_ROOT}
source venv/bin/activate
tmux new-session -d -s command_executor_{self.restart_count} 'python3 workers/command_executor_worker.py'
"""
            subprocess.run(["bash", "-c", cmd], check=True)

            # 起動確認
            time.sleep(3)
            if self.check_executor_running():
                self.logger.info("Command Executor restarted successfully")

                # Report successful restart to Task Sage
                if self.elder_systems_initialized:
                    self._report_successful_restart_to_task_sage()

                self.slack.send_message(
                    message=f"✅ Command Executor restarted (attempt {self.restart_count})",
                    channel="#alerts",
                )
                return True
            else:
                self.logger.error(
                    "Command Executor failed to start after restart attempt"
                )
                return False

        except subprocess.SubprocessError as e:
            self.logger.error(f"Failed to restart Command Executor: {e}")

            # Report restart failure to Incident Sage
            if self.elder_systems_initialized:
                self._report_restart_failure_to_incident_sage(e)

            self.slack.send_message(
                message=f"❌ Failed to restart Command Executor: {str(e)}",
                channel="#alerts",
            )
            return False

    def _report_startup_to_task_sage(self):
        """Report watchdog startup to Task Sage"""
        if not self.four_sages:
            return

        try:
            report = {
                "type": "watchdog_startup",
                "service": "executor_watchdog",
                "check_interval": self.check_interval,
                "max_restarts": self.max_restarts,
                "timestamp": datetime.now().isoformat(),
            }

            self.four_sages.report_to_task_sage(report)

        except Exception as e:
            self.logger.error(f"Failed to report startup to Task Sage: {e}")

    def _report_shutdown_to_task_sage(self, signal_num):
        """Report watchdog shutdown to Task Sage"""
        if not self.four_sages:
            return

        try:
            report = {
                "type": "watchdog_shutdown",
                "service": "executor_watchdog",
                "signal": signal_num,
                "uptime": (datetime.now() - self.created_at).total_seconds(),
                "restart_count": self.restart_count,
                "timestamp": datetime.now().isoformat(),
            }

            self.four_sages.report_to_task_sage(report)

        except Exception as e:
            self.logger.error(f"Failed to report shutdown to Task Sage: {e}")

    def _report_restart_attempt_to_task_sage(self):
        """Report restart attempt to Task Sage"""
        if not self.four_sages:
            return

        try:
            report = {
                "type": "executor_restart_attempt",
                "attempt_number": self.restart_count,
                "max_restarts": self.max_restarts,
                "timestamp": datetime.now().isoformat(),
            }

            self.four_sages.report_to_task_sage(report)

        except Exception as e:
            self.logger.error(f"Failed to report restart attempt to Task Sage: {e}")

    def _report_successful_restart_to_task_sage(self):
        """Report successful restart to Task Sage"""
        if not self.four_sages:
            return

        try:
            report = {
                "type": "executor_restart_success",
                "attempt_number": self.restart_count,
                "timestamp": datetime.now().isoformat(),
            }

            self.four_sages.report_to_task_sage(report)

        except Exception as e:
            self.logger.error(f"Failed to report successful restart to Task Sage: {e}")

    def _report_restart_failure_to_incident_sage(self, error):
        """Report restart failure to Incident Sage"""
        if not self.four_sages:
            return

        try:
            incident_data = {
                "type": "executor_restart_failure",
                "attempt_number": self.restart_count,
                "error": str(error),
                "timestamp": datetime.now().isoformat(),
            }

            self.four_sages.consult_incident_sage(incident_data)

        except Exception as e:
            self.logger.error(f"Failed to report restart failure to Incident Sage: {e}")

    def _report_watchdog_error_to_incident_sage(self, error):
        """Report watchdog error to Incident Sage"""
        if not self.four_sages:
            return

        try:
            incident_data = {
                "type": "watchdog_error",
                "error": str(error),
                "uptime": (datetime.now() - self.created_at).total_seconds(),
                "timestamp": datetime.now().isoformat(),
            }

            self.four_sages.consult_incident_sage(incident_data)

        except Exception as e:
            self.logger.error(f"Failed to report watchdog error to Incident Sage: {e}")

    def _escalate_to_claude_elder(self, failure_data):
        """Escalate approaching max restarts to Claude Elder"""
        if not self.elder_tree:
            self.logger.warning("Cannot escalate - Elder Tree not available")
            return

        try:
            message = ElderMessage(
                sender_rank=ElderRank.SAGE,
                sender_type=SageType.INCIDENT,
                content={
                    "type": "executor_failure_escalation",
                    "failure_data": failure_data,
                    "recommendation": "Executor service requires immediate attention",
                    "timestamp": datetime.now().isoformat(),
                },
                urgency="high",
            )

            self.elder_tree.send_to_claude_elder(message)
            self.logger.info("Executor failure escalated to Claude Elder")

        except Exception as e:
            self.logger.error(f"Failed to escalate to Claude Elder: {e}")

    def _escalate_critical_failure_to_claude_elder(self):
        """Escalate critical failure (max restarts reached) to Claude Elder"""
        if not self.elder_tree:
            self.logger.warning("Cannot escalate - Elder Tree not available")
            return

        try:
            message = ElderMessage(
                sender_rank=ElderRank.SAGE,
                sender_type=SageType.INCIDENT,
                content={
                    "type": "critical_executor_failure",
                    "restart_count": self.restart_count,
                    "max_restarts": self.max_restarts,
                    "status": "watchdog_giving_up",
                    "recommendation": "Manual intervention required immediately",
                    "timestamp": datetime.now().isoformat(),
                },
                urgency="critical",
            )

            self.elder_tree.send_to_claude_elder(message)
            self.logger.info("Critical executor failure escalated to Claude Elder")

        except Exception as e:
            self.logger.error(
                f"Failed to escalate critical failure to Claude Elder: {e}"
            )

    def get_elder_watchdog_status(self):
        """Get comprehensive Elder watchdog status"""
        status = {
            "service": "executor_watchdog",
            "elder_role": "System Guardian",
            "reporting_to": "Incident Sage",
            "elder_systems": {
                "initialized": self.elder_systems_initialized,
                "four_sages_active": self.four_sages is not None,
                "council_summoner_active": self.council_summoner is not None,
                "elder_tree_connected": self.elder_tree is not None,
            },
            "watchdog_stats": {
                "restart_count": self.restart_count,
                "max_restarts": self.max_restarts,
                "check_interval": self.check_interval,
                "executor_running": self.check_executor_running(),
            },
            "uptime": (datetime.now() - self.created_at).total_seconds(),
            "status": "healthy"
            if self.running and self.elder_systems_initialized
            else "degraded",
        }

        # Add Four Sages status if available
        if self.four_sages:
            try:
                status["four_sages_status"] = self.four_sages.get_sages_status()
            except Exception as e:
                status["four_sages_status"] = f"Error retrieving status: {e}"

        return status


if __name__ == "__main__":
    watchdog = CommandExecutorWatchdog()
    try:
        watchdog.run()
    except KeyboardInterrupt:
        watchdog.logger.info("Watchdog stopped by user")
    except Exception as e:
        watchdog.logger.error(f"Watchdog failed: {e}")
