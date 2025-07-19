"""
Notification Handler Component

復旧イベントの通知を管理するコンポーネント
"""

import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# Elders Guildのライブラリパスを追加
sys.path.append("/home/aicompany/ai_co")

logger = logging.getLogger(__name__)


class NotificationHandler:
    """通知処理を管理するクラス"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初期化

        Args:
            config: 通知設定
        """
        self.config = config or self._get_default_config()
        self.notification_history = []
        self.slack_notifier = None

        # Slack通知の初期化
        if self.config.get("slack_enabled", True):
            self._init_slack_notifier()

    def _get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定を取得"""
        return {
            "slack_enabled": True,
            "log_enabled": True,
            "elder_notification": True,
            "severity_levels": {
                "info": "📘",
                "warning": "⚠️",
                "error": "🚨",
                "critical": "🔴",
            },
        }

    def _init_slack_notifier(self):
        """Slack通知機能を初期化"""
        try:
            from libs.slack_notifier import SlackNotifier

            self.slack_notifier = SlackNotifier()
            logger.info("Slack notifier initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Slack notifier: {e}")
            self.slack_notifier = None

    def send_notification(
        self,
        title: str,
        message: str,
        severity: str = "info",
        worker_name: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None,
    ):
        """
        通知を送信

        Args:
            title: 通知タイトル
            message: 通知メッセージ
            severity: 重要度 (info, warning, error, critical)
            worker_name: ワーカー名
            additional_data: 追加データ
        """
        notification = {
            "timestamp": datetime.now().isoformat(),
            "title": title,
            "message": message,
            "severity": severity,
            "worker_name": worker_name,
            "additional_data": additional_data or {},
        }

        # 履歴に追加
        self.notification_history.append(notification)

        # ログ出力
        if self.config.get("log_enabled", True):
            self._log_notification(notification)

        # Slack通知
        if self.config.get("slack_enabled", True) and self.slack_notifier:
            self._send_slack_notification(notification)

        # 重大度が高い場合はElder Councilに通知
        if severity in ["error", "critical"] and self.config.get(
            "elder_notification", True
        ):
            self._notify_elder_council(notification)

    def _log_notification(self, notification: Dict[str, Any]):
        """ログに通知を記録"""
        severity = notification["severity"]
        emoji = self.config["severity_levels"].get(severity, "📝")

        log_message = f"{emoji} {notification['title']} - {notification['message']}"

        if severity == "error":
            logger.error(log_message)
        elif severity == "warning":
            logger.warning(log_message)
        elif severity == "critical":
            logger.critical(log_message)
        else:
            logger.info(log_message)

    def _send_slack_notification(self, notification: Dict[str, Any]):
        """Slackに通知を送信"""
        if not self.slack_notifier:
            return

        try:
            severity = notification["severity"]
            emoji = self.config["severity_levels"].get(severity, "📝")

            # メッセージをフォーマット
            slack_message = f"{emoji} *{notification['title']}*\n"
            slack_message += f"{notification['message']}\n"

            if notification.get("worker_name"):
                slack_message += f"ワーカー: `{notification['worker_name']}`\n"

            # 追加データがある場合
            additional_data = notification.get("additional_data", {})
            if additional_data:
                slack_message += "\n*詳細情報:*\n"
                for key, value in additional_data.items():
                    slack_message += f"• {key}: {value}\n"

            slack_message += f"\n_送信時刻: {notification['timestamp']}_"

            # 送信
            self.slack_notifier.send_message(slack_message)

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")

    def _notify_elder_council(self, notification: Dict[str, Any]):
        """Elder Councilに通知"""
        try:
            # Elder Council通知用のファイルを作成
            elder_dir = "/home/aicompany/ai_co/knowledge_base/elder_notifications"
            os.makedirs(elder_dir, exist_ok=True)

            filename = f"worker_recovery_{notification['severity']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            filepath = os.path.join(elder_dir, filename)

            content = f"""# 🚨 Worker Recovery System Notification

**Severity**: {notification['severity'].upper()}
**Time**: {notification['timestamp']}
**Title**: {notification['title']}

## Message
{notification['message']}

## Details
- Worker: {notification.get('worker_name', 'N/A')}
- System: Worker Auto-Recovery

## Additional Data
```json
{notification.get('additional_data', {})}
```

## Recommended Actions
1. Review the worker health status
2. Check recovery logs for details
3. Consider manual intervention if needed

---
*Generated by Worker Recovery System*
"""

            with open(filepath, "w") as f:
                f.write(content)

            logger.info(f"Elder Council notification created: {filename}")

        except Exception as e:
            logger.error(f"Failed to notify Elder Council: {e}")

    def send_recovery_report(self, worker_name: str, recovery_result: Dict[str, Any]):
        """
        復旧レポートを送信

        Args:
            worker_name: ワーカー名
            recovery_result: 復旧結果
        """
        if recovery_result.get("success"):
            title = f"Worker Recovery Successful: {worker_name}"
            severity = "info"
            message = f"復旧戦略 '{recovery_result.get('strategy')}' が成功しました。"
        else:
            title = f"Worker Recovery Failed: {worker_name}"
            severity = "error"
            message = f"復旧に失敗しました: {recovery_result.get('error', 'Unknown error')}"

        additional_data = {
            "strategy": recovery_result.get("strategy"),
            "duration": recovery_result.get("duration"),
            "details": recovery_result.get("details", {}),
        }

        self.send_notification(
            title=title,
            message=message,
            severity=severity,
            worker_name=worker_name,
            additional_data=additional_data,
        )

    def send_health_summary(self, health_data: Dict[str, Dict[str, Any]]):
        """
        健康状態サマリーを送信

        Args:
            health_data: 全ワーカーの健康状態
        """
        unhealthy_workers = [
            name for name, data in health_data.items() if not data.get("healthy", True)
        ]

        if unhealthy_workers:
            title = "Worker Health Alert"
            message = f"不健康なワーカー: {', '.join(unhealthy_workers)}"
            severity = "warning"

            # 詳細情報を追加
            details = {}
            for worker_name in unhealthy_workers:
                worker_data = health_data[worker_name]
                details[worker_name] = {
                    "health_score": worker_data.get("health_score", 0),
                    "status": worker_data.get("status", "unknown"),
                }

            self.send_notification(
                title=title,
                message=message,
                severity=severity,
                additional_data={"unhealthy_workers": details},
            )

    def get_notification_history(
        self,
        limit: int = 50,
        severity: Optional[str] = None,
        worker_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        通知履歴を取得

        Args:
            limit: 取得件数
            severity: フィルタする重要度
            worker_name: フィルタするワーカー名

        Returns:
            通知履歴リスト
        """
        history = self.notification_history

        # フィルタリング
        if severity:
            history = [n for n in history if n.get("severity") == severity]

        if worker_name:
            history = [n for n in history if n.get("worker_name") == worker_name]

        # 最新のものから返す
        return history[-limit:][::-1]

    def clear_notification_history(self, before_date: Optional[datetime] = None):
        """
        通知履歴をクリア

        Args:
            before_date: この日付より前の履歴をクリア
        """
        if before_date:
            self.notification_history = [
                n
                for n in self.notification_history
                if datetime.fromisoformat(n["timestamp"]) >= before_date
            ]
        else:
            self.notification_history = []

        logger.info(
            f"Notification history cleared. Remaining: {len(self.notification_history)}"
        )

    def test_notification(self):
        """通知機能のテスト"""
        self.send_notification(
            title="Worker Recovery System Test",
            message="これはテスト通知です。システムは正常に動作しています。",
            severity="info",
            additional_data={"test": True, "timestamp": datetime.now().isoformat()},
        )

        logger.info("Test notification sent")
