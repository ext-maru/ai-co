#!/usr/bin/env python3
"""
AI Log Viewer - ログ参照ヘルパー
AIが実行ログを簡単に確認するためのツール
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from datetime import datetime


class AILogViewer:
    """AIのログ参照ヘルパー"""

    def __init__(self):
        self.base_dir = Path("/home/aicompany/ai_co")
        self.cmd_logs = self.base_dir / "ai_commands" / "logs"
        self.program_logs = self.base_dir / "ai_programs" / "ai_logs"

    def get_latest_command_logs(self, limit=5):
        """最新のCommand Executorログを取得"""
        logs = []
        if self.cmd_logs.exists():
            log_files = sorted(
                self.cmd_logs.glob("*.log"),
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )[:limit]

            for log_file in log_files:
                content = log_file.read_text(errors="ignore")
                # Exit Codeを抽出
                exit_code = "Unknown"
                if "Exit Code:" in content:
                    for line in content.split("\n"):
                        if line.strip().startswith("Exit Code:"):
                            exit_code = line.split(":")[-1].strip()
                            break

                logs.append(
                    {
                        "file": log_file.name,
                        "path": str(log_file),
                        "exit_code": exit_code,
                        "size": log_file.stat().st_size,
                        "modified": datetime.fromtimestamp(
                            log_file.stat().st_mtime
                        ).isoformat(),
                    }
                )
        return logs

    def get_latest_program_logs(self, limit=5):
        """最新のProgram Runnerログを取得"""
        logs = []
        if self.program_logs.exists():
            log_files = sorted(
                self.program_logs.glob("*.log"),
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )[:limit]

            for log_file in log_files:
                content = log_file.read_text(errors="ignore")
                # タスク名とExit Codeを抽出
                task_name = "Unknown"
                exit_code = "Unknown"

                for line in content.split("\n"):
                    if line.startswith("Task:"):
                        task_name = line.split(":")[-1].strip()
                    elif line.strip().startswith("Exit Code:"):
                        exit_code = line.split(":")[-1].strip()

                logs.append(
                    {
                        "file": log_file.name,
                        "path": str(log_file),
                        "task": task_name,
                        "exit_code": exit_code,
                        "size": log_file.stat().st_size,
                        "modified": datetime.fromtimestamp(
                            log_file.stat().st_mtime
                        ).isoformat(),
                    }
                )
        return logs

    def read_log(self, log_path):
        """指定されたログを読む"""
        log_file = Path(log_path)
        if log_file.exists():
            return log_file.read_text(errors="ignore")
        return f"ログファイルが見つかりません: {log_path}"

    def get_failed_programs(self):
        """失敗したプログラムのリストを取得"""
        failed_dir = self.base_dir / "ai_programs" / "failed"
        failed_programs = []

        if failed_dir.exists():
            for file in failed_dir.iterdir():
                if file.is_file():
                    failed_programs.append(
                        {
                            "name": file.name,
                            "path": str(file),
                            "size": file.stat().st_size,
                            "modified": datetime.fromtimestamp(
                                file.stat().st_mtime
                            ).isoformat(),
                        }
                    )

        return failed_programs

    def get_execution_summary(self):
        """実行サマリーを取得"""
        summary = {
            "command_logs": len(list(self.cmd_logs.glob("*.log")))
            if self.cmd_logs.exists()
            else 0,
            "program_logs": len(list(self.program_logs.glob("*.log")))
            if self.program_logs.exists()
            else 0,
            "failed_programs": len(self.get_failed_programs()),
            "latest_activity": None,
        }

        # 最新のアクティビティを特定
        all_logs = []
        if self.cmd_logs.exists():
            all_logs.extend(self.cmd_logs.glob("*.log"))
        if self.program_logs.exists():
            all_logs.extend(self.program_logs.glob("*.log"))

        if all_logs:
            latest = max(all_logs, key=lambda x: x.stat().st_mtime)
            summary["latest_activity"] = {
                "file": latest.name,
                "time": datetime.fromtimestamp(latest.stat().st_mtime).isoformat(),
            }

        return summary


# 使用例
if __name__ == "__main__":
    viewer = AILogViewer()

    print("📊 AI実行ログサマリー")
    print("=" * 50)

    summary = viewer.get_execution_summary()
    print(f"Command Executorログ: {summary['command_logs']}件")
    print(f"Program Runnerログ: {summary['program_logs']}件")
    print(f"失敗プログラム: {summary['failed_programs']}件")

    if summary["latest_activity"]:
        print(f"\n最新アクティビティ: {summary['latest_activity']['file']}")
        print(f"時刻: {summary['latest_activity']['time']}")

    print("\n📋 最新のCommand Executorログ:")
    for log in viewer.get_latest_command_logs(3):
        print(f"  - {log['file']} (Exit: {log['exit_code']})")

    print("\n📋 最新のProgram Runnerログ:")
    for log in viewer.get_latest_program_logs(3):
        print(f"  - {log['file']} ({log['task']}, Exit: {log['exit_code']})")

    print("\n❌ 失敗したプログラム:")
    for prog in viewer.get_failed_programs()[:3]:
        print(f"  - {prog['name']}")
