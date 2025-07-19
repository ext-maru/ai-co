#!/usr/bin/env python3
"""
AI Program Runner - プログラム自動実行システム
AI Command Executorを拡張して、プログラムファイルの自動実行をサポート
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import datetime
import json
import shutil

from libs.ai_command_helper import AICommandHelper


class AIProgramRunner:
    """プログラムファイルの自動実行ヘルパー"""

    def __init__(self):
        self.helper = AICommandHelper()
        self.base_dir = Path("/home/aicompany/ai_co/ai_programs")
        self.inbox_dir = self.base_dir / "inbox"
        self.archive_dir = self.base_dir / "archive"
        self.ai_logs_dir = self.base_dir / "ai_logs"
        self.failed_dir = self.base_dir / "failed"

        # ディレクトリ作成
        for dir in [
            self.inbox_dir,
            self.archive_dir,
            self.ai_logs_dir,
            self.failed_dir,
        ]:
            dir.mkdir(parents=True, exist_ok=True)

    def run_python_program(
        self, code: str, task_name: str, description: str = ""
    ) -> dict:
        """Pythonプログラムを自動実行"""
        # プログラムファイルを作成
        program_file = self.inbox_dir / f"{task_name}.py"
        program_file.write_text(code)

        # 実行コマンドを作成
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.ai_logs_dir / f"exec_{timestamp}_{task_name}.log"

        bash_cmd = f"""#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "=== AI Program Execution ===" | tee {log_file}
echo "Task: {task_name}" | tee -a {log_file}
echo "Description: {description}" | tee -a {log_file}
echo "Started: $(date)" | tee -a {log_file}
echo "============================" | tee -a {log_file}

python3 {program_file} 2>&1 | tee -a {log_file}
EXIT_CODE=${{PIPESTATUS[0]}}

echo "============================" | tee -a {log_file}
echo "Completed: $(date)" | tee -a {log_file}
echo "Exit Code: $EXIT_CODE" | tee -a {log_file}

# アーカイブまたは失敗フォルダへ移動
if [ $EXIT_CODE -eq 0 ]; then
    ARCHIVE_DIR="{self.archive_dir}/$(date +%Y-%m-%d)"
    mkdir -p "$ARCHIVE_DIR"
    mv {program_file} "$ARCHIVE_DIR/{task_name}_{timestamp}.py"
    echo "Archived to: $ARCHIVE_DIR" | tee -a {log_file}
else
    mv {program_file} "{self.failed_dir}/{task_name}_{timestamp}.py"
    echo "Moved to failed directory" | tee -a {log_file}
fi

# Slack通知
if [ $EXIT_CODE -eq 0 ]; then
    EMOJI="✅"
    STATUS="成功"
else
    EMOJI="❌"
    STATUS="失敗"
fi

# Slack通知用のPythonスクリプト作成
cat > /tmp/notify_program_result.py << 'EOF'
import sys
sys.path.insert(0, "/home/aicompany/ai_co")
from libs.slack_notifier import SlackNotifier

task_name = "{task_name}"
exit_code = $EXIT_CODE
status = "$STATUS"
emoji = "$EMOJI"

try:
    notifier = SlackNotifier()
    message = f"{{emoji}} AIプログラム実行{{status}}: {{task_name}}\\nDescription: {description}\\nExit Code: {{exit_code}}"
    notifier.send_message(message)
except Exception as e:
    print(f"Slack notification failed: {{e}}")
EOF

python3 /tmp/notify_program_result.py
rm -f /tmp/notify_program_result.py

exit $EXIT_CODE
"""

        # AI Command Executorで実行
        cmd_id = f"program_{task_name}_{timestamp}"
        self.helper.create_bash_command(bash_cmd, cmd_id)

        return {
            "command_id": cmd_id,
            "log_file": str(log_file),
            "expected_archive": str(
                self.archive_dir
                / datetime.date.today().isoformat()
                / f"{task_name}_{timestamp}.py"
            ),
            "status": "scheduled",
            "execution_time": datetime.datetime.now().isoformat(),
        }

    def run_bash_script(
        self, script: str, task_name: str, description: str = ""
    ) -> dict:
        """Bashスクリプトを自動実行"""
        # スクリプトファイルを作成
        script_file = self.inbox_dir / f"{task_name}.sh"
        script_file.write_text(script)
        script_file.chmod(0o755)

        # 実行コマンドを作成
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.ai_logs_dir / f"exec_{timestamp}_{task_name}.log"

        bash_cmd = f"""#!/bin/bash
echo "=== AI Script Execution ===" | tee {log_file}
echo "Task: {task_name}" | tee -a {log_file}
echo "Description: {description}" | tee -a {log_file}
echo "Started: $(date)" | tee -a {log_file}
echo "============================" | tee -a {log_file}

{script_file} 2>&1 | tee -a {log_file}
EXIT_CODE=${{PIPESTATUS[0]}}

echo "============================" | tee -a {log_file}
echo "Completed: $(date)" | tee -a {log_file}
echo "Exit Code: $EXIT_CODE" | tee -a {log_file}

# アーカイブまたは失敗フォルダへ移動
if [ $EXIT_CODE -eq 0 ]; then
    ARCHIVE_DIR="{self.archive_dir}/$(date +%Y-%m-%d)"
    mkdir -p "$ARCHIVE_DIR"
    mv {script_file} "$ARCHIVE_DIR/{task_name}_{timestamp}.sh"
    echo "Archived to: $ARCHIVE_DIR" | tee -a {log_file}
else
    mv {script_file} "{self.failed_dir}/{task_name}_{timestamp}.sh"
    echo "Moved to failed directory" | tee -a {log_file}
fi

exit $EXIT_CODE
"""

        # AI Command Executorで実行
        cmd_id = f"script_{task_name}_{timestamp}"
        self.helper.create_bash_command(bash_cmd, cmd_id)

        return {
            "command_id": cmd_id,
            "log_file": str(log_file),
            "expected_archive": str(
                self.archive_dir
                / datetime.date.today().isoformat()
                / f"{task_name}_{timestamp}.sh"
            ),
            "status": "scheduled",
            "execution_time": datetime.datetime.now().isoformat(),
        }

    def get_latest_logs(self, task_name: str = None, limit: int = 10) -> list:
        """最新のログを取得"""
        logs = []
        log_files = sorted(self.ai_logs_dir.glob("*.log"), reverse=True)

        if task_name:
            log_files = [f for f in log_files if task_name in f.name]

        for log_file in log_files[:limit]:
            logs.append(
                {
                    "file": log_file.name,
                    "path": str(log_file),
                    "size": log_file.stat().st_size,
                    "modified": datetime.datetime.fromtimestamp(
                        log_file.stat().st_mtime
                    ).isoformat(),
                }
            )

        return logs

    def get_execution_summary(self) -> dict:
        """実行サマリーを取得"""
        today = datetime.date.today().isoformat()

        # 今日のアーカイブ数
        today_archive = self.archive_dir / today
        archived_count = (
            len(list(today_archive.glob("*"))) if today_archive.exists() else 0
        )

        # 失敗数
        failed_count = len(list(self.failed_dir.glob("*")))

        # 待機中
        inbox_count = len(list(self.inbox_dir.glob("*")))

        return {
            "today_executed": archived_count,
            "total_failed": failed_count,
            "pending": inbox_count,
            "archive_dirs": sorted(
                [d.name for d in self.archive_dir.iterdir() if d.is_dir()]
            ),
            "summary_time": datetime.datetime.now().isoformat(),
        }

    def cleanup_old_archives(self, days_to_keep: int = 7):
        """古いアーカイブを削除"""
        cutoff_date = datetime.date.today() - datetime.timedelta(days=days_to_keep)

        cleaned = []
        for archive_dir in self.archive_dir.iterdir():
            if archive_dir.is_dir():
                try:
                    dir_date = datetime.date.fromisoformat(archive_dir.name)
                    if dir_date < cutoff_date:
                        shutil.rmtree(archive_dir)
                        cleaned.append(archive_dir.name)
                except ValueError:
                    # 日付形式でないディレクトリはスキップ
                    pass

        return cleaned


# 使用例とテスト
if __name__ == "__main__":
    print("AI Program Runner - Test")
    runner = AIProgramRunner()

    # サマリー表示
    summary = runner.get_execution_summary()
    print(f"\n実行サマリー:")
    print(f"  今日の実行: {summary['today_executed']}")
    print(f"  失敗総数: {summary['total_failed']}")
    print(f"  待機中: {summary['pending']}")

    # テストプログラムの実行
    test_code = """
import json
import datetime

result = {
    "test": "AI Program Runner Test",
    "timestamp": datetime.datetime.now().isoformat(),
    "status": "success"
}

print(json.dumps(result, indent=2))
print("Test completed successfully!")
"""

    result = runner.run_python_program(
        code=test_code, task_name="test_runner", description="AI Program Runnerの動作テスト"
    )

    print(f"\nテスト実行:")
    print(f"  Command ID: {result['command_id']}")
    print(f"  Log File: {result['log_file']}")
    print(f"  Status: {result['status']}")
    print("\n6秒後に実行されます...")
