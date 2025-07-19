#!/usr/bin/env python3
"""
Elders Guild Command Executor MCP Server
コマンド実行を管理し、結果を追跡するMCPサーバー
"""

import asyncio
import json
import logging
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Elders Guildプロジェクトルート
PROJECT_ROOT = Path("/home/aicompany/ai_co")
AI_COMMANDS_DIR = PROJECT_ROOT / "ai_commands"
AI_PROGRAMS_DIR = PROJECT_ROOT / "ai_programs"


class AICompanyExecutorServer:
    """Elders Guild Command Executor MCPサーバー"""

    def __init__(self):
        self.server = Server("ai-company-executor")
        self.setup_tools()

    def setup_tools(self):
        """ツールの定義"""

        @self.server.tool()
        async def execute_command(
            command: str,
            command_type: str = "bash",
            task_name: Optional[str] = None,
            async_exec: bool = True,
            notify_slack: bool = True,
        ) -> Dict[str, Any]:
            """コマンドを実行（同期または非同期）"""

            # タスク名の生成
            if not task_name:
                task_name = f"cmd_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # 非同期実行の場合はAI Command Executorを使用
            if async_exec:
                from libs.ai_command_helper import AICommandHelper

                helper = AICommandHelper()

                if command_type == "bash":
                    helper.create_bash_command(command, task_name)
                elif command_type == "python":
                    helper.create_python_command(command, task_name)
                else:
                    return {"error": f"Unknown command type: {command_type}"}

                return {
                    "status": "scheduled",
                    "task_name": task_name,
                    "message": "Command scheduled for execution (6 seconds)",
                    "check_result_command": f"helper.check_results('{task_name}')",
                }

            # 同期実行の場合
            else:
                try:
                    if command_type == "bash":
                        result = subprocess.run(
                            command,
                            shell=True,
                            capture_output=True,
                            text=True,
                            cwd=PROJECT_ROOT,
                        )
                    elif command_type == "python":
                        result = subprocess.run(
                            ["python3", "-c", command],
                            capture_output=True,
                            text=True,
                            cwd=PROJECT_ROOT,
                        )
                    else:
                        return {"error": f"Unknown command type: {command_type}"}

                    # 結果を保存
                    log_content = f"""
=== Command Execution Log ===
Task: {task_name}
Type: {command_type}
Started: {datetime.now().isoformat()}
Exit Code: {result.returncode}

=== STDOUT ===
{result.stdout}

=== STDERR ===
{result.stderr}
====================
"""

                    log_file = AI_COMMANDS_DIR / "logs" / f"{task_name}.log"
                    log_file.parent.mkdir(exist_ok=True)
                    log_file.write_text(log_content)

                    # Slack通知
                    if notify_slack and result.returncode == 0:
                        await self._notify_slack(
                            f"✅ Command {task_name} completed successfully"
                        )
                    elif notify_slack:
                        await self._notify_slack(
                            f"❌ Command {task_name} failed with code {result.returncode}"
                        )

                    return {
                        "status": "completed",
                        "exit_code": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "log_file": str(log_file),
                    }

                except Exception as e:
                    return {"status": "error", "error": str(e)}

        @self.server.tool()
        async def check_result(task_name: str) -> Dict[str, Any]:
            """コマンド実行結果を確認"""
            from libs.ai_command_helper import AICommandHelper

            helper = AICommandHelper()

            result = helper.check_results(task_name)
            if result:
                # ログファイルの内容も取得
                log_file = (
                    AI_COMMANDS_DIR
                    / "logs"
                    / f"{task_name}_{result.get('timestamp', '')}.log"
                )
                if log_file.exists():
                    result["log_content"] = log_file.read_text()

                return result
            else:
                return {
                    "status": "not_found",
                    "message": f"No results found for task: {task_name}",
                }

        @self.server.tool()
        async def get_logs(
            limit: int = 10, log_type: str = "command"
        ) -> List[Dict[str, Any]]:
            """最新のログを取得"""
            from libs.ai_log_viewer import AILogViewer

            viewer = AILogViewer()

            if log_type == "command":
                logs = viewer.get_latest_command_logs(limit)
            elif log_type == "program":
                logs = viewer.get_latest_program_logs(limit)
            else:
                logs = []

            return logs

        @self.server.tool()
        async def run_program(
            code: str,
            language: str = "python",
            task_name: Optional[str] = None,
            description: str = "",
        ) -> Dict[str, Any]:
            """プログラムを実行（AI Program Runner使用）"""
            from libs.ai_program_runner import AIProgramRunner

            runner = AIProgramRunner()

            if language == "python":
                result = runner.run_python_program(
                    code=code,
                    task_name=task_name or f"prog_{uuid.uuid4().hex[:8]}",
                    description=description,
                )
            elif language == "bash":
                result = runner.run_bash_script(
                    script=code,
                    task_name=task_name or f"script_{uuid.uuid4().hex[:8]}",
                    description=description,
                )
            else:
                return {"error": f"Unsupported language: {language}"}

            return result

        @self.server.tool()
        async def get_execution_summary() -> Dict[str, Any]:
            """実行統計を取得"""
            from libs.ai_log_viewer import AILogViewer

            viewer = AILogViewer()

            summary = viewer.get_execution_summary()

            # 直近の成功率を計算
            recent_logs = viewer.get_latest_command_logs(20)
            if recent_logs:
                success_count = sum(
                    1 for log in recent_logs if log.get("exit_code") == 0
                )
                summary["recent_success_rate"] = (
                    f"{(success_count / len(recent_logs)) * 100:.1f}%"
                )

            return summary

    async def _notify_slack(self, message: str):
        """Slack通知（非同期）"""
        try:
            from libs.slack_notifier import SlackNotifier

            notifier = SlackNotifier()
            notifier.send_message(message)
        except Exception as e:
            logging.warning(f"Slack notification failed: {e}")

    async def run(self):
        """サーバーを起動"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream)


if __name__ == "__main__":
    server = AICompanyExecutorServer()
    asyncio.run(server.run())
