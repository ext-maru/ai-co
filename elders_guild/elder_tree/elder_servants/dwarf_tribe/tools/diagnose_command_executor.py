#!/usr/bin/env python3
"""
AI Command Executor 診断スクリプト
プロセス状態の確認と問題の診断・修正を行う
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import psutil

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.ai_command_helper import AICommandHelper
from libs.slack_notifier import SlackNotifier


class CommandExecutorDiagnostic:
    """CommandExecutorDiagnosticクラス"""
    def __init__(self):
        self.base_dir = PROJECT_ROOT / "ai_commands"
        self.log_file = PROJECT_ROOT / "logs" / "command_executor.log"
        self.issues = []
        self.slack = SlackNotifier()

    def run_full_diagnostic(self):
        """完全な診断を実行"""
        print("🔍 AI Command Executor 診断開始...\n")

        # 1.0 プロセス状態確認
        process_status = self.check_process_status()

        # 2.0 ディレクトリ状態確認
        dir_status = self.check_directories()

        # 3.0 ログ確認
        log_status = self.check_logs()

        # 4.0 tmuxセッション確認
        tmux_status = self.check_tmux_session()

        # 5.0 実行テスト
        test_status = self.test_execution()

        # 6.0 結果サマリー
        self.print_summary()

        # 7.0 自動修正
        if self.issues:
            self.auto_fix_issues()

    def check_process_status(self):
        """プロセス状態確認"""
        print("1️⃣ プロセス状態確認")

        # psutilでプロセスチェック
        executor_processes = []
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = proc.info.get("cmdline", [])
                if cmdline and "command_executor_worker.py" in " ".join(cmdline):
                    executor_processes.append(proc)
            except:
                pass

        if executor_processes:
            print(f"✅ Command Executor プロセスが動作中: {len(executor_processes)}個")
            for proc in executor_processes:
                print(f"   PID: {proc.pid}")
        else:
            print("❌ Command Executor プロセスが見つかりません")
            self.issues.append("NO_PROCESS")

        # psコマンドでも確認
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        if "command_executor_worker" in result.stdout:
            lines = [
                line
                for line in result.stdout.split("\n")
                if "command_executor_worker" in line
            ]
            print(f"   psコマンド確認: {len(lines)}個のプロセス")

        print()
        return len(executor_processes) > 0

    def check_directories(self):
        """ディレクトリ状態確認"""
        print("2️⃣ ディレクトリ状態確認")

        dirs = {
            "pending": self.base_dir / "pending",
            "running": self.base_dir / "running",
            "completed": self.base_dir / "completed",
            "logs": self.base_dir / "logs",
        }

        all_exist = True
        for name, path in dirs.items():
            if path.exists():
                # ファイル数も確認
                files = list(path.glob("*"))
                print(f"✅ {name}: 存在 ({len(files)}個のファイル)")
                if name == "pending" and files:
                    print(
                        f"   ⚠️ 実行待ちファイルがあります: {[f.name for f in files[:3]]}"
                    )
                    self.issues.append("PENDING_FILES")
            else:
                print(f"❌ {name}: 存在しない")
                all_exist = False
                self.issues.append(f"MISSING_DIR_{name}")

        print()
        return all_exist

    def check_logs(self):
        """ログファイル確認"""
        print("3️⃣ ログファイル確認")

        if self.log_file.exists():
            # 最終更新時刻確認
            mtime = datetime.fromtimestamp(self.log_file.stat().st_mtime)
            age = datetime.now() - mtime

            print(f"✅ ログファイル存在: {self.log_file}")
            print(
                f"   最終更新: {mtime.strftime('%Y-%m-%d %H:%M:%S')} ({age.total_seconds():0.0f}秒前)"
            )

            if age > timedelta(minutes=10):
                print("   ⚠️ ログが10分以上更新されていません")
                self.issues.append("STALE_LOG")

            # 最新のログ内容確認
            with open(self.log_file, "r") as f:
                lines = f.readlines()
                if lines:
                    print(f"   最新エントリ: {lines[-1].strip()[:80]}...")

                    # エラー確認
                    error_lines = [
                        l for l in lines[-20:] if "ERROR" in l or "error" in l
                    ]
                    if error_lines:
                        print(f"   ⚠️ 最近のエラー: {len(error_lines)}件")
                        # Deep nesting detected (depth: 5) - consider refactoring
                        for line in error_lines[-3:]:
                            print(f"      {line.strip()[:80]}...")
                        self.issues.append("RECENT_ERRORS")
        else:
            print("❌ ログファイルが存在しません")
            self.issues.append("NO_LOG_FILE")

        print()
        return self.log_file.exists()

    def check_tmux_session(self):
        """tmuxセッション確認"""
        print("4️⃣ tmuxセッション確認")

        result = subprocess.run(
            ["tmux", "list-sessions"], capture_output=True, text=True
        )

        if result.returncode == 0:
            sessions = result.stdout.strip().split("\n")
            executor_sessions = [s for s in sessions if "command_executor" in s]

            if executor_sessions:
                print(f"✅ Command Executor tmuxセッション: {len(executor_sessions)}個")
                for session in executor_sessions:
                    print(f"   {session}")
            else:
                print("❌ Command Executor tmuxセッションが見つかりません")
                self.issues.append("NO_TMUX_SESSION")
        else:
            print("⚠️ tmuxが実行されていません")

        print()
        return "command_executor" in result.stdout if result.returncode == 0 else False

    def test_execution(self):
        """実行テスト"""
        print("5️⃣ 実行テスト")

        try:
            # テストコマンド作成
            helper = AICommandHelper()
            test_id = f"diagnostic_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            bash_content = f"""#!/bin/bash
echo "Diagnostic test at $(date)"
echo "Python version: $(python3 --version)"
echo "Working directory: $(pwd)"
echo "Test ID: {test_id}"
"""

            result = helper.create_bash_command(bash_content, test_id)
            print(f"✅ テストコマンド作成: {test_id}")

            # 実行を待つ
            print("   実行を待機中（最大15秒）...")
            for i in range(15):
                time.sleep(1)
                check_result = helper.check_results(test_id)
                if check_result.get("status") != "pending":
                    print(
                        f"✅ テスト実行完了！ Exit Code: {check_result.get('exit_code', 'N/A')}"
                    )

                    # ログ確認
                    log_content = helper.get_latest_log(test_id)
                    if log_content and "Test ID:" in log_content:
                        print("✅ ログ出力確認済み")
                    return True

                if i == 5:
                    print("   ⚠️ 5秒経過... まだ実行されていません")

            print("❌ テストコマンドが実行されませんでした")
            self.issues.append("EXECUTION_FAILED")
            return False

        except Exception as e:
            print(f"❌ テスト実行エラー: {str(e)}")
            self.issues.append("TEST_ERROR")
            return False

        finally:
            print()

    def print_summary(self):
        """診断結果サマリー"""
        print("📊 診断結果サマリー")
        print("=" * 50)

        if not self.issues:
            print("✅ 全て正常です！")
        else:
            print(f"⚠️ {len(self.issues)}個の問題が見つかりました:")
            for issue in self.issues:
                print(f"   - {issue}")

        print()

    def auto_fix_issues(self):
        """問題の自動修正"""
        print("🔧 自動修正開始...")

        fixed = []

        # プロセスが存在しない場合
        if "NO_PROCESS" in self.issues:
            print("   Command Executorを起動します...")

            # tmuxで起動
            cmd = f"""
cd {PROJECT_ROOT}
source venv/bin/activate
tmux new-session -d -s command_executor 'python3 workers/command_executor_worker.py'
"""
            subprocess.run(["bash", "-c", cmd])
            time.sleep(2)

            # 確認
            if self.verify_process_running():
                print("   ✅ Command Executor起動成功")
                fixed.append("NO_PROCESS")
            else:
                print("   ❌ 起動に失敗しました")

        # ディレクトリが存在しない場合
        for issue in self.issues:
            if issue.startswith("MISSING_DIR_"):
                dir_name = issue.replace("MISSING_DIR_", "")
                dir_path = self.base_dir / dir_name
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"   ✅ ディレクトリ作成: {dir_name}")
                fixed.append(issue)

        # 実行待ちファイルがある場合
        if "PENDING_FILES" in self.issues:
            print(
                "   ⚠️ 実行待ちファイルがあります。プロセスが正常に動作しているか確認してください。"
            )

        # Slack通知
        if fixed:
            self.slack.send_message(
                f"🔧 AI Command Executor自動修正完了\n"
                f"修正項目: {', '.join(fixed)}\n"
                f"残りの問題: {len(self.issues) - len(fixed)}個"
            )

        print(f"\n✅ {len(fixed)}個の問題を修正しました")

    def verify_process_running(self):
        """プロセスが動作しているか確認"""
        for proc in psutil.process_iter(["cmdline"]):
            try:
                cmdline = proc.info.get("cmdline", [])
                if cmdline and "command_executor_worker.py" in " ".join(cmdline):
                    return True
            except:
                pass
        return False


if __name__ == "__main__":
    diagnostic = CommandExecutorDiagnostic()
    diagnostic.run_full_diagnostic()
