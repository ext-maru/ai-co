#!/usr/bin/env python3
"""
改善版Slack通知機能
客観的でプロフェッショナルな通知を実現
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

class ImprovedSlackNotifier:
    """改善されたSlack通知クラス"""

    def __init__(self, config_file=None):
        """初期化メソッド"""
        if config_file is None:
            config_file = Path(__file__).parent.parent / "config" / "slack.conf"

        self.config = self._load_config(config_file)
        self.enabled = self.config.get("ENABLE_SLACK", "false").lower() == "true"

    def _load_config(self, config_file):
        """設定ファイル読み込み"""
        config = {}
        try:
            with open(config_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        config[key.strip()] = value.strip().strip('"')
        except Exception as e:
            logger.error(f"Failed to load Slack config: {e}")

        return config

    def send_task_notification(
        self,
        task_id: str,
        status: str,
        duration: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """タスク通知（改善版）"""
        if not self.enabled:
            return False

        # ステータスに応じたシンプルなプレフィックス
        status_prefix = {
            "started": "Task started",
            "completed": "Task completed",
            "failed": "Task failed",
            "retrying": "Task retry",
        }.get(status, "Task update")

        # メインメッセージ（客観的）
        message = f"{status_prefix}: {task_id}"

        # 詳細情報を構造化
        if details or duration is not None:
            details_parts = []

            if duration is not None:
                details_parts.append(f"Duration: {duration:0.2f}s")

            if details:
                # 技術的に重要な情報のみ
                if "worker" in details:
                    details_parts.append(f"Worker: {details['worker']}")
                if "error" in details:
                    details_parts.append(f"Error: {details['error']}")
                if "files_created" in details:
                    details_parts.append(f"Files: {details['files_created']}")
                if "retry_count" in details:
                    details_parts.append(f"Retry: {details['retry_count']}")

            if details_parts:
                message += " | " + " | ".join(details_parts)

        # Slack送信
        slack_message = {
            "channel": self.config.get("SLACK_CHANNEL", "#general"),
            "username": self.config.get("SLACK_USERNAME", "AI-Company"),
            "text": message,
        }

        return self._send_message(slack_message)

    def send_metric_update(self, metrics: Dict[str, Any]):
        """メトリクス更新通知"""
        if not self.enabled:
            return False

        # メトリクスを簡潔にフォーマット
        metric_parts = []
        for key, value in metrics.items():
            if isinstance(value, float):
                metric_parts.append(f"{key}: {value:0.2f}")
            else:
                metric_parts.append(f"{key}: {value}")

        message = "System metrics: " + " | ".join(metric_parts)

        slack_message = {
            "channel": self.config.get("SLACK_CHANNEL", "#general"),
            "username": self.config.get("SLACK_USERNAME", "AI-Company"),
            "text": message,
        }

        return self._send_message(slack_message)

    def send_alert(self, alert_type: str, message: str, severity: str = "warning"):
        """アラート通知（技術的）"""
        if not self.enabled:
            return False

        # シンプルなプレフィックス
        prefix = {"error": "ERROR", "warning": "WARN", "critical": "CRITICAL"}.get(
            severity, "ALERT"
        )

        formatted_message = f"[{prefix}] {alert_type}: {message}"

        slack_message = {
            "channel": self.config.get("SLACK_ERROR_CHANNEL", "#ai-company-alerts"),
            "username": self.config.get("SLACK_USERNAME", "AI-Company"),
            "text": formatted_message,
        }

        return self._send_message(slack_message)

    def _send_message(self, message):
        """Slackメッセージ送信"""
        webhook_url = self.config.get("SLACK_WEBHOOK_URL")
        if not webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False

        try:
            response = requests.post(
                webhook_url,
                data=json.dumps(message),
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            if response.status_code == 200:

                return True
            else:
                logger.error(f"Slack notification failed: HTTP {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Slack notification error: {e}")
            return False

    def test_notification(self):
        """テスト通知（シンプル版）"""
        test_message = (
            f"Slack integration test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        slack_message = {
            "channel": self.config.get("SLACK_CHANNEL", "#general"),
            "username": self.config.get("SLACK_USERNAME", "AI-Company"),
            "text": test_message,
        }

        success = self._send_message(slack_message)
        return "Test notification sent" if success else "Test notification failed"

# 使用例とガイドライン
NOTIFICATION_EXAMPLES = """
# 改善されたSlack通知の例

## タスク完了通知
Before: "🚀 革新的なコード生成タスクが完璧に成功しました！✨"
After: "Task completed: code_20250702_123456 | Duration: 2.3s | Files: 3"

## エラー通知
Before: "😱 大変！エラーが発生してしまいました！💥"
After: "[ERROR] Task failed: code_20250702_123457 | Error: ConnectionTimeout | Retry: 1"

## メトリクス通知
Before: "📊 素晴らしいパフォーマンス！🌟"
After: "System metrics: queue_length: 5 | active_workers: 3 | memory_mb: 256.4"

## 原則
1.0 事実のみを報告
2.0 数値データを含める
3.0 技術者が必要とする情報を優先
4.0 モバイルでも読みやすい簡潔さ
"""
