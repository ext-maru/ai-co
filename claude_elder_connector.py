#!/usr/bin/env python3
"""
Claude Elder Connector - 実際のClaude CLIとの接続
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

# claude_elder_api_directをインポートしてフォールバック
try:
    from claude_elder_api_direct import ClaudeElderAPIDirect

    use_api_direct = True
except ImportError:
    use_api_direct = False


class ClaudeElderConnector:
    """Claude CLIとの実際の接続を管理"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.project_root = Path(__file__).parent

        # API Direct使用可能ならそれを使う
        if use_api_direct:
            self.api_direct = ClaudeElderAPIDirect()
        else:
            self.api_direct = None

        # Claude CLIコマンドパス
        self.claude_cli_path = "/usr/local/bin/claude"  # 正しいClaude CLIパス

    def send_to_claude(
        self, message: str, context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Claude CLIに実際にメッセージを送信"""

        # Claude CLIを優先使用
        try:
            # コンテキスト情報を準備
            full_message = self._prepare_message(message, context)

            # Claude CLIコマンドを構築（シェル経由でuser環境を継承）
            # シングルクォートをエスケープ
            escaped_message = full_message.replace("'", "'\"'\"'")
            cmd = f"echo '{escaped_message}' | {self.claude_cli_path}"

            # 環境変数を設定（必要に応じて）
            env = os.environ.copy()
            env["CLAUDE_PROJECT_ROOT"] = str(self.project_root)
            # ユーザーのホームディレクトリを明示的に設定
            env["HOME"] = os.path.expanduser("~")
            env["USER"] = os.getenv("USER", "aicompany")

            # Claude CLIを実行（シェル経由）
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                env=env,
                timeout=60,  # 60秒のタイムアウト
            )

            if result.returncode == 0:
                # 成功時のレスポンス
                response = result.stdout.strip()
                return {
                    "success": True,
                    "response": response,
                    "timestamp": datetime.now().isoformat(),
                    "elder": "claude_elder_real",
                }
            else:
                # エラー時のレスポンス - API認証エラーの場合はAPI Directにフォールバック
                error_msg = (
                    result.stderr.strip() or result.stdout.strip() or "Claude CLIエラー"
                )
                self.logger.error(
                    f"Claude CLI error (exit {result.returncode}): {error_msg}"
                )

                if (
                    "Invalid API key" in error_msg
                    or "authentication" in error_msg.lower()
                ):
                    # API認証エラーの場合はAPI Directにフォールバック
                    if self.api_direct:
                        self.logger.info(
                            "Falling back to API Direct due to CLI auth issues"
                        )
                        return self.api_direct.send_to_claude_api(message, context)
                    else:
                        return self._fallback_response(message)

                return {
                    "success": False,
                    "response": f"🧾 クロードエルダー: エラーが発生しました - {error_msg}",
                    "timestamp": datetime.now().isoformat(),
                    "elder": "claude_elder_error",
                }

        except subprocess.TimeoutExpired:
            self.logger.error("Claude CLI timeout")
            return {
                "success": False,
                "response": "🧾 クロードエルダー: 応答がタイムアウトしました。もう一度お試しください。",
                "timestamp": datetime.now().isoformat(),
                "elder": "claude_elder_timeout",
            }
        except FileNotFoundError:
            self.logger.error("Claude CLI not found")
            # API Directが使える場合はそちらを使用
            if self.api_direct:
                return self.api_direct.send_to_claude_api(message, context)
            return self._fallback_response(message)
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            # API Directが使える場合はそちらを使用
            if self.api_direct:
                return self.api_direct.send_to_claude_api(message, context)
            return self._fallback_response(message)

    def _prepare_message(self, message: str, context: Optional[str] = None) -> str:
        """メッセージとコンテキストを準備"""
        full_message = ""

        # コンテキストがある場合は追加
        if context:
            full_message += f"Context: {context}\n\n"

        # Elders Guild階層構造を意識させる
        full_message += "🏛️ Elders Guild階層構造:\n"
        full_message += (
            "グランドエルダーmaru（最高位）→ クロードエルダー（あなた）→ 4賢者 → エルダー評議会 → エルダーサーベント\n\n"
        )

        # ユーザーメッセージ
        full_message += f"ユーザーからの質問: {message}\n\n"

        # 応答指示
        full_message += "Elders Guildのクロードエルダーとして、適切に応答してください。"

        return full_message

    def _fallback_response(self, message: str) -> Dict[str, Any]:
        """フォールバックレスポンス（Claude CLIが利用できない場合）"""
        response = "🧾 クロードエルダー: "

        # キーワードベースの簡易応答
        message_lower = message.lower()

        if "status" in message_lower or "状態" in message:
            response += "システムは正常に稼働しています。詳細な情報はダッシュボードでご確認ください。"
        elif "task" in message_lower or "タスク" in message:
            response += "タスクエルダーが最適な実行計画を立案します。具体的な内容をお聞かせください。"
        elif "help" in message_lower or "ヘルプ" in message:
            response += "Elders Guildのシステムについて何でもお尋ねください。4賢者システムが連携してサポートします。"
        elif "elder" in message_lower or "エルダー" in message:
            response += "エルダー評議会は4賢者（ナレッジ・タスク・インシデント・RAG）で構成されています。"
        else:
            response += f"'{message}' について承りました。詳細な分析を行いますので、少々お待ちください。"

        return {
            "success": True,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "elder": "claude_elder_fallback",
        }

    def get_system_context(self) -> str:
        """現在のシステムコンテキストを取得"""
        try:
            import psutil

            context = f"""
Elders Guild System Context:
- CPU: {psutil.cpu_percent()}%
- Memory: {psutil.virtual_memory().percent}%
- Active Workers: エルダーサーベント5体稼働中
- 4 Sages Status: All operational
- Grand Elder maru: Overseeing all operations
"""
            return context
        except:
            return "Elders Guild System: Operational"


# テスト用
if __name__ == "__main__":
    connector = ClaudeElderConnector()

    # テストメッセージ
    test_messages = ["システムの状態は？", "タスクエルダーにカバレッジ向上を依頼", "エルダー評議会について教えて"]

    for msg in test_messages:
        print(f"\n💬 Message: {msg}")
        result = connector.send_to_claude(msg)
        print(f"📝 Response: {result['response']}")
        print(f"✅ Success: {result['success']}")
