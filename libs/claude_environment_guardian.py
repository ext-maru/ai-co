#!/usr/bin/env python3
"""
Claude Environment Guardian - 環境破壊防止システム
Claude Elderの全コマンドを監視し、危険な操作を自動ブロック
"""

import re
import sys
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

class EnvironmentGuardian:
    """Claudeの環境破壊を防ぐ守護者"""

    def __init__(self):
        self.violation_log = []
        self.safe_commands_cache = set()

        # 危険なコマンドパターン
        self.DANGEROUS_PATTERNS = [
            # Python環境汚染
            (r"python.*-m\s+venv", "❌ venv作成は環境汚染！Dockerを使用してください"),
            (r"pip\s+install(?!.*requirements\.txt)", "❌ pip installは禁止！Dockerコンテナ内で実行"),
            (r"pip3\s+install", "❌ pip3 installは禁止！既存環境を破壊します"),
            (r"python.*setup\.py", "❌ setup.py実行は環境変更！禁止"),

            # Docker違反
            (r"^docker\s+(?!.*sg\s+docker\s+-c)", "❌ docker直接実行は禁止！sg docker -c を使用"),
            (r"^docker-compose", "❌ docker-compose直接実行は禁止！sg docker -c を使用"),
            (r"sudo\s+docker", "❌ sudo dockerは絶対禁止！環境破壊の危険"),

            # プロセス汚染
            (r"nohup.*python", "⚠️ nohupでのPython実行は管理外プロセス！禁止"),
            (r".*&\s*$", "⚠️ バックグラウンド実行は要確認"),
            (r"systemctl|service", "❌ サービス操作は禁止！"),

            # 権限昇格
            (r"^sudo\s+", "❌ sudo使用は禁止！権限昇格は危険"),
            (r"chmod\s+777", "❌ chmod 777は超危険！絶対禁止"),

            # ファイルシステム破壊
            (r"rm\s+-rf\s+/", "💀 システム全体削除！！絶対禁止"),
            (r"rm\s+-rf\s+~", "💀 ホームディレクトリ削除！禁止"),
            (r">\s*/dev/.*", "❌ デバイスファイルへの書き込み禁止"),
        ]

        # 安全な代替コマンド
        self.SAFE_ALTERNATIVES = {
            "docker": "sg docker -c \"docker {args}\"",
            "docker-compose": "sg docker -c \"docker compose {args}\"",
            "pip install": "sg docker -c \"docker run -v $(pwd):/app python:3.12 pip install {args}\"",
            "python -m venv": "# Dockerコンテナを使用してください",
            "nohup": "# systemdサービスまたはDockerで実行",
        }

        # ログ設定
        self.logger = logging.getLogger("EnvironmentGuardian")
        handler = logging.FileHandler("/home/aicompany/ai_co/logs/environment_guardian.log")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.WARNING)

    def check_command(self, command: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        コマンドの安全性をチェック

        Returns:
            (is_safe, error_message, alternative_command)
        """
        # キャッシュチェック
        if command in self.safe_commands_cache:
            return (True, None, None)

        # 危険パターンチェック
        for pattern, message in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                # 違反を記録
                self.record_violation(command, pattern, message)

                # 代替案を提案
                alternative = self.suggest_alternative(command)

                return (False, message, alternative)

        # 安全なコマンドをキャッシュ
        self.safe_commands_cache.add(command)
        return (True, None, None)

    def suggest_alternative(self, dangerous_command: str) -> Optional[str]:
        """危険なコマンドに対する安全な代替案を提案"""
        for key, alternative in self.SAFE_ALTERNATIVES.items():
            if key in dangerous_command:
                # コマンドの引数を抽出して代替案に適用
                args = dangerous_command.replace(key, "").strip()
                return alternative.format(args=args)

        return "# このコマンドは実行できません。別の方法を検討してください"

    def record_violation(self, command: str, pattern: str, message: str):
        """違反を記録"""
        violation = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "pattern": pattern,
            "message": message,
            "severity": self.assess_severity(pattern)
        }

        self.violation_log.append(violation)
        self.logger.warning(f"環境違反検出: {command} - {message}")

        # 重大な違反は即座にアラート
        if violation["severity"] == "CRITICAL":
            self.raise_critical_alert(violation)

    def assess_severity(self, pattern: str) -> str:
        """違反の重大度を評価"""
        if "rm -rf /" in pattern or "sudo" in pattern:
            return "CRITICAL"
        elif "pip install" in pattern or "venv" in pattern:
            return "HIGH"
        elif "&" in pattern:
            return "MEDIUM"
        return "LOW"

    def raise_critical_alert(self, violation: Dict):
        """重大な違反に対するアラート"""
        alert_file = Path("/home/aicompany/ai_co/CRITICAL_ENVIRONMENT_ALERT.txt")
        with open(alert_file, "w") as f:
            f.write(f"""
🚨🚨🚨 重大な環境違反検出 🚨🚨🚨

時刻: {violation['timestamp']}
コマンド: {violation['command']}
メッセージ: {violation['message']}

このコマンドは環境を破壊する可能性があります！
実行は自動的にブロックされました。

対応:
1. このアラートをグランドエルダーmaruに報告
2. インシデント賢者による原因分析
3. 再発防止策の実装
""")

    def get_violation_report(self) -> str:
        """違反レポートを生成"""
        if not self.violation_log:
            return "✅ 環境違反なし"

        report = "🚨 環境違反レポート\n"
        report += f"違反件数: {len(self.violation_log)}\n\n"

        for v in self.violation_log:
            report += f"[{v['timestamp']}] {v['severity']}\n"
            report += f"コマンド: {v['command']}\n"
            report += f"理由: {v['message']}\n\n"

        return report

    def enforce_command(self, command: str) -> str:
        """コマンドを強制的に安全化"""
        is_safe, error_msg, alternative = self.check_command(command)

        if not is_safe:
            print(f"\n{error_msg}")
            if alternative:
                print(f"代替案: {alternative}\n")

            # 危険なコマンドは実行させない
            return "echo '❌ 危険なコマンドはブロックされました'"

        return command

# グローバルガーディアンインスタンス
guardian = EnvironmentGuardian()

def safe_execute(command: str) -> str:
    """安全なコマンド実行ラッパー"""
    return guardian.enforce_command(command)

# Claudeのコマンド実行をフック
def hook_claude_commands():
    """Claudeの全コマンドをフック（実装例）"""
    import subprocess
    original_run = subprocess.run

    def safe_run(cmd, *args, **kwargs):
        if isinstance(cmd, str):
            cmd = safe_execute(cmd)
        elif isinstance(cmd, list):
            cmd[0] = safe_execute(' '.join(cmd)).split()[0]

        return original_run(cmd, *args, **kwargs)

    subprocess.run = safe_run

if __name__ == "__main__":
    # テスト実行
    test_commands = [
        "docker ps",  # 危険
        "sg docker -c 'docker ps'",  # 安全
        "pip install requests",  # 危険
        "python -m venv myenv",  # 危険
        "rm -rf /",  # 超危険
        "ls -la",  # 安全
    ]

    print("🛡️ Environment Guardian テスト")
    print("=" * 50)

    for cmd in test_commands:
        is_safe, error, alt = guardian.check_command(cmd)
        print(f"\nコマンド: {cmd}")
        print(f"安全性: {'✅ 安全' if is_safe else '❌ 危険'}")
        if error:
            print(f"理由: {error}")
        if alt:
            print(f"代替案: {alt}")

    print("\n" + "=" * 50)
    print(guardian.get_violation_report())
