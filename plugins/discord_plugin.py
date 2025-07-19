#!/usr/bin/env python3
"""
Discord通知プラグイン
タスクイベントをDiscordに通知
"""

import json
from datetime import datetime
from typing import Any, Dict

import requests

from core.plugin_system import WorkerPlugin


class DiscordNotificationPlugin(WorkerPlugin):
    """Discord通知プラグイン"""

    @property
    def name(self) -> str:
        return "discord_notification"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Send task notifications to Discord channel"

    def initialize(self, config: Dict[str, Any]) -> bool:
        """プラグイン初期化"""
        self.webhook_url = config.get("webhook_url")
        self.channel_name = config.get("channel_name", "ai-company")
        self.notify_on_success = config.get("notify_on_success", True)
        self.notify_on_error = config.get("notify_on_error", True)
        self.notify_on_start = config.get("notify_on_start", False)

        return bool(self.webhook_url)

    def on_task_start(self, task: Dict[str, Any]):
        """タスク開始時の通知"""
        if not self.notify_on_start:
            return

        embed = {
            "title": "🚀 Task Started",
            "description": f"Task ID: {task.get('task_id', 'Unknown')}",
            "color": 3447003,  # Blue
            "fields": [
                {
                    "name": "Type",
                    "value": task.get("task_type", "general"),
                    "inline": True,
                },
                {
                    "name": "Priority",
                    "value": task.get("priority", "NORMAL"),
                    "inline": True,
                },
            ],
            "timestamp": datetime.now().isoformat(),
        }

        self._send_notification(embed)

    def on_task_complete(self, task: Dict[str, Any], result: Any):
        """タスク完了時の通知"""
        if not self.notify_on_success:
            return

        files_created = (
            result.get("files_created", []) if isinstance(result, dict) else []
        )

        embed = {
            "title": "✅ Task Completed",
            "description": f"Task ID: {task.get('task_id', 'Unknown')}",
            "color": 65280,  # Green
            "fields": [
                {
                    "name": "Type",
                    "value": task.get("task_type", "general"),
                    "inline": True,
                },
                {
                    "name": "Files Created",
                    "value": str(len(files_created)),
                    "inline": True,
                },
                {
                    "name": "Prompt",
                    "value": task.get("prompt", "")[:100] + "..."
                    if len(task.get("prompt", "")) > 100
                    else task.get("prompt", ""),
                    "inline": False,
                },
            ],
            "timestamp": datetime.now().isoformat(),
        }

        self._send_notification(embed)

    def on_task_error(self, task: Dict[str, Any], error: Exception):
        """タスクエラー時の通知"""
        if not self.notify_on_error:
            return

        embed = {
            "title": "❌ Task Failed",
            "description": f"Task ID: {task.get('task_id', 'Unknown')}",
            "color": 16711680,  # Red
            "fields": [
                {"name": "Error", "value": str(error)[:200], "inline": False},
                {
                    "name": "Type",
                    "value": task.get("task_type", "general"),
                    "inline": True,
                },
                {"name": "Error Type", "value": type(error).__name__, "inline": True},
            ],
            "timestamp": datetime.now().isoformat(),
        }

        self._send_notification(embed)

    def on_worker_start(self, worker_info: Dict[str, Any]):
        """ワーカー起動時の通知"""
        embed = {
            "title": "🟢 Worker Started",
            "description": f"Worker Type: {worker_info.get('worker_type', 'Unknown')}",
            "color": 3066993,  # Green
            "fields": [
                {
                    "name": "Worker ID",
                    "value": worker_info.get("worker_id", "Unknown"),
                    "inline": True,
                }
            ],
            "timestamp": datetime.now().isoformat(),
        }

        self._send_notification(embed)

    def _send_notification(self, embed: Dict[str, Any]):
        """Discord Webhookに通知を送信"""
        try:
            payload = {
                "username": "Elders Guild Bot",
                "avatar_url": "https://example.com/ai-company-avatar.png",
                "embeds": [embed],
            }

            response = requests.post(self.webhook_url, json=payload, timeout=5)

            response.raise_for_status()

        except Exception as e:
            # 通知エラーは無視（メイン処理に影響させない）
            print(f"Discord notification error: {str(e)}")

    def cleanup(self):
        """クリーンアップ処理"""
        pass
