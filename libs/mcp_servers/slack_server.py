#!/usr/bin/env python3
"""
Slack Integration MCP Server
Slack連携機能を提供するMCPサーバー
"""

import asyncio
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.mcp_wrapper import MCPServer
from libs.slack_notifier import SlackNotifier


class SlackIntegrationMCPServer:
    """Slack連携MCPサーバー"""

    def __init__(self):
        self.server = MCPServer("slack")
        self.notifier = SlackNotifier()
        self.setup_tools()

    def setup_tools(self):
        @self.server.tool()
        async def send_message(message: str, channel: str = None):
            """Slackにメッセージを送信"""
            try:
                # チャンネル指定がある場合は設定
                if channel:
                    original_channel = self.notifier.channel
                    self.notifier.channel = channel

                # メッセージ送信
                result = self.notifier.send_message(message)

                # チャンネルを元に戻す
                if channel:
                    self.notifier.channel = original_channel

                return {
                    "status": "success",
                    "message": message,
                    "channel": channel or self.notifier.channel,
                }
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "message": "Failed to send message",
                }

        @self.server.tool()
        async def send_formatted_message(title: str, content: str, color: str = "good"):
            """フォーマット付きメッセージを送信"""
            try:
                # Slack用のアタッチメント形式
                attachments = [
                    {
                        "title": title,
                        "text": content,
                        "color": color,  # good, warning, danger, or hex color
                        "footer": "Elders Guild MCP",
                        "ts": int(asyncio.get_event_loop().time()),
                    }
                ]

                # 送信（実際のSlack APIでは attachments パラメータを使用）
                message = f"*{title}*\n{content}"
                result = self.notifier.send_message(message)

                return {
                    "status": "success",
                    "title": title,
                    "content": content,
                    "color": color,
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}

        @self.server.tool()
        async def send_worker_status(
            worker_name: str, status: str, details: str = None
        ):
            """ワーカーのステータスをSlackに通知"""
            # ステータスに応じた絵文字を選択
            emoji_map = {
                "started": "🟢",
                "stopped": "🔴",
                "restarted": "🔄",
                "error": "⚠️",
                "warning": "⚡",
                "info": "ℹ️",
            }

            emoji = emoji_map.get(status, "📌")

            # メッセージ作成
            message = f"{emoji} Worker Status: *{worker_name}*\n"
            message += f"Status: `{status}`"

            if details:
                message += f"\n{details}"

            try:
                result = self.notifier.send_message(message)

                return {
                    "status": "success",
                    "worker": worker_name,
                    "notification_status": status,
                    "message_sent": message,
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}

        @self.server.tool()
        async def send_error_alert(
            error_type: str, error_message: str, source: str = None
        ):
            """エラーアラートをSlackに送信"""
            # エラーメッセージの作成
            alert_message = "🚨 *Error Alert*\n"
            alert_message += f"Type: `{error_type}`\n"

            if source:
                alert_message += f"Source: `{source}`\n"

            alert_message += f"```\n{error_message}\n```"

            try:
                result = self.notifier.send_message(alert_message)

                # エラーログにも記録
                from datetime import datetime

                error_log = PROJECT_ROOT / "logs" / "mcp_errors.log"
                error_log.parent.mkdir(exist_ok=True)

                with open(error_log, "a") as f:
                    f.write(f"\n[{datetime.now()}] {error_type}: {error_message}\n")

                return {
                    "status": "success",
                    "alert_sent": True,
                    "logged": True,
                    "error_type": error_type,
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}

        @self.server.tool()
        async def send_daily_summary():
            """日次サマリーをSlackに送信"""
            try:
                from datetime import date, datetime

                # サマリー情報を収集（実際の実装では各種メトリクスを収集）
                summary = f"📊 *Daily Summary - {date.today()}*\n\n"

                # ワーカー情報（仮の実装）
                summary += "**Worker Status:**\n"
                summary += "• Running: 5/8\n"
                summary += "• CPU Usage: 45%\n"
                summary += "• Memory: 2.3GB\n\n"

                # タスク情報
                summary += "**Tasks Processed:**\n"
                summary += "• Completed: 156\n"
                summary += "• Failed: 3\n"
                summary += "• Pending: 12\n\n"

                summary += "_Generated by Elders Guild MCP_"

                result = self.notifier.send_message(summary)

                return {
                    "status": "success",
                    "summary_date": str(date.today()),
                    "sent": True,
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}

    async def process_request(self, request_json):
        request = json.loads(request_json)
        return await self.server.handle_request(request)


# CLI interface
if __name__ == "__main__":
    import asyncio

    server = SlackIntegrationMCPServer()

    # Read request from stdin
    request = input()

    # Process and return result
    result = asyncio.run(server.process_request(request))
    print(json.dumps(result))
