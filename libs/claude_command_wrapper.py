#!/usr/bin/env python3
"""
Claude Command Wrapper - Bashコマンドの自動保護ラッパー
全てのBashコマンドを環境ガーディアンでチェックしてから実行
"""

import os
import sys
import subprocess
from typing import List, Tuple, Optional
from libs.claude_environment_guardian import guardian


class ClaudeCommandWrapper:
    """Claudeのコマンド実行を安全化するラッパー"""

    def __init__(self):
        """初期化メソッド"""
        self.execution_log = []
        self.blocked_count = 0
        self.safe_count = 0

    def execute_command(
        self, command: str, timeout: Optional[int] = None
    ) -> Tuple[bool, str, str]:
        """
        コマンドを安全チェック後に実行

        Returns:
            (success, stdout, stderr)
        """
        # 環境ガーディアンでチェック
        is_safe, error_msg, alternative = guardian.check_command(command)

        if not is_safe:
            self.blocked_count += 1

            # エラーメッセージ構築
            error_output = f"{error_msg}\n"
            if alternative:
                error_output += f"代替案: {alternative}\n"

            # ブロックしたことを記録
            self.log_execution(command, "BLOCKED", error_msg)

            # 標準エラーとして返す
            return (False, "", error_output)

        # 安全なコマンドは実行
        try:
            self.safe_count += 1
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=timeout
            )

            self.log_execution(
                command, "EXECUTED", "Success" if result.returncode == 0 else "Failed"
            )

            return (result.returncode == 0, result.stdout, result.stderr)

        except subprocess.TimeoutExpired:
            self.log_execution(command, "TIMEOUT", f"Exceeded {timeout}s")
            return (False, "", f"Command timed out after {timeout}s")

        except Exception as e:
            self.log_execution(command, "ERROR", str(e))
            return (False, "", str(e))

    def log_execution(self, command: str, status: str, details: str):
        """実行ログを記録"""
        self.execution_log.append(
            {"command": command, "status": status, "details": details}
        )

    def get_statistics(self) -> dict:
        """実行統計を取得"""
        return {
            "total_commands": self.blocked_count + self.safe_count,
            "blocked_commands": self.blocked_count,
            "safe_commands": self.safe_count,
            "block_rate": f"{(self.blocked_count / max(
                1,
                self.blocked_count + self.safe_count) * 100
            ):0.1f}%",
        }


# グローバルラッパーインスタンス
command_wrapper = ClaudeCommandWrapper()


def safe_bash_execute(command: str, description: str = "", timeout: int = 120) -> dict:
    """
    Claudeが使用すべき安全なBash実行関数
    """
    print(f"🔍 コマンドチェック: {description}")

    success, stdout, stderr = command_wrapper.execute_command(command, timeout)

    if not success and stderr and "❌" in stderr:
        # 環境違反の場合
        print(f"\n🚨 環境保護システムが危険なコマンドをブロックしました")
        print(stderr)

        # 代替案があれば自動提案
        if "代替案:" in stderr:
            alternative = stderr.split("代替案:")[1].strip()
            print(f"\n💡 代わりにこのコマンドを使用してください:")
            print(f"   {alternative}")

        return {"success": False, "stdout": "", "stderr": stderr, "blocked": True}

    return {"success": success, "stdout": stdout, "stderr": stderr, "blocked": False}


# モンキーパッチ例（実際のClaude環境で適用）
def apply_claude_protection():
    """Claudeの実行環境に保護を適用"""

    # osモジュールの危険な関数を置き換え
    original_system = os.system

    def protected_system(command):
        """protected_systemメソッド"""
        result = safe_bash_execute(command, "os.system call")
        if result["blocked"]:
            raise EnvironmentError(f"危険なコマンドがブロックされました: {command}")
        return original_system(command) if result["success"] else 1

    os.system = protected_system

    # subprocessモジュールも保護
    import subprocess

    original_run = subprocess.run

    def protected_run(cmd, *args, **kwargs):
        """protected_runメソッド"""
        if isinstance(cmd, str) and kwargs.get("shell"):
            check_result = guardian.check_command(cmd)
            if not check_result[0]:  # 危険なコマンド
                raise EnvironmentError(f"危険なコマンド: {check_result[1]}")
        return original_run(cmd, *args, **kwargs)

    subprocess.run = protected_run


if __name__ == "__main__":
    # デモ実行
    print("🛡️ Claude Command Wrapper デモ")
    print("=" * 50)

    test_commands = [
        ("ls -la", "ファイル一覧"),
        ("docker ps", "Dockerプロセス確認"),
        ("pip install numpy", "パッケージインストール"),
        ("sg docker -c 'docker ps'", "正しいDocker実行"),
    ]

    for cmd, desc in test_commands:
        print(f"\n実行: {cmd}")
        result = safe_bash_execute(cmd, desc)

        if result["blocked"]:
            print("結果: ❌ ブロック")
        else:
            print(f"結果: ✅ 実行{'成功' if result['success'] else '失敗'}")
            if result["stdout"]:
                print(f"出力: {result['stdout'][:100]}...")

    print("\n" + "=" * 50)
    print("実行統計:", command_wrapper.get_statistics())
