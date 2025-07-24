#!/usr/bin/env python3
"""
🌳 Elder Tree Integrated AsyncResultWorker
非同期対応Result Worker - Elders Guild統合版

Elders Guild Integration:
- 🌟 Grand Elder maru oversight
- 🤖 Claude Elder execution guidance
- 🧙‍♂️ Four Sages wisdom consultation
- 🏛️ Elder Council decision support
- ⚔️ Elder Servants coordination

Part of the Elder Tree Hierarchy for async result processing
"""

import asyncio
import json

# プロジェクトルートをPythonパスに追加
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
import structlog

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.async_base_worker import AsyncBaseWorker
from core.rate_limiter import CacheManager, RateLimiter
from libs.slack_notifier import SlackNotifier

# Elder Tree imports
try:
    from libs.elder_council_summoner import ElderCouncilSummoner
    from libs.elder_tree_hierarchy import (
        ElderMessage,
        ElderRank,
        SageType,
        get_elder_tree,
    )
    from libs.four_sages_integration import FourSagesIntegration

    ELDER_SYSTEM_AVAILABLE = True
except ImportError as e:
    # Handle specific exception case
    logger = structlog.get_logger(__name__)
    logger.warning(f"Elder system not available: {e}")
    ELDER_SYSTEM_AVAILABLE = False
    FourSagesIntegration = None
    ElderCouncilSummoner = None


class AsyncResultWorker(AsyncBaseWorker):
    """
    非同期対応のResult Worker

    Features:
    - Slack API レート制限対応
    - メッセージサイズ制限対応（分割送信）
    - 統計情報の永続化
    - 非同期通知処理
    - エラー時の再試行機構
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(
            worker_name="async_result_worker",
            config=config,
            input_queues=["results", "ai_results"],
            output_queues=[],  # 終端ワーカー
        )

        # Slack通知設定
        self.slack_notifier = SlackNotifier()

        # レート制限（Slack API用）
        self.slack_rate_limiter = RateLimiter(
            rate=config.get("slack_rate_limit", 1),  # 1msg/sec
            period=1,
            redis_client=self.redis_client,
        )

        # キャッシュマネージャ
        self.cache_manager = CacheManager(
            redis_client=self.redis_client,
            default_ttl=config.get("cache_ttl", 86400),  # 24時間
        )

        # メッセージサイズ制限
        self.max_message_size = config.get("slack_max_message_size", 3000)

        # 統計情報
        self.stats = {
            "messages_processed": 0,
            "notifications_sent": 0,
            "notifications_failed": 0,
            "messages_split": 0,
            "last_reset": datetime.utcnow(),
        }

        # 統計情報ファイル
        self.stats_file = Path(
            config.get("stats_file", PROJECT_ROOT / "data" / "result_worker_stats.json")
        )
        self.stats_file.parent.mkdir(exist_ok=True)

        # 定期レポート設定
        self.report_interval = config.get("report_interval_hours", 1)

        # Elder systems
        self.elder_systems_initialized = False
        self.four_sages = None
        self.elder_council = None
        self.elder_role = ElderRank.SERVANT if ELDER_SYSTEM_AVAILABLE else None
        self.reporting_sage = SageType.RESULT if ELDER_SYSTEM_AVAILABLE else None

    async def _initialize_elder_systems(self):
        """Initialize Elder Tree hierarchy systems"""
        if not ELDER_SYSTEM_AVAILABLE:
            self.logger.warning(
                "Elder system not available - running in standalone mode"
            )
            return

        try:
            # Initialize Four Sages Integration
            self.four_sages = FourSagesIntegration()
            await self.four_sages.initialize()

            # Initialize Elder Council Summoner
            self.elder_council = ElderCouncilSummoner(
                worker_type="async_result_worker", elder_rank=self.elder_role
            )
            await self.elder_council.initialize()

            # Report to Result/Incident Sage
            await self._report_to_result_sage("Result Worker initialized", "startup")

            self.elder_systems_initialized = True
            self.logger.info("Elder systems initialized successfully")

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Failed to initialize Elder systems: {e}")
            self.elder_systems_initialized = False

    async def start(self):
        """Start the worker with Elder systems"""
        # Initialize Elder systems
        await self._initialize_elder_systems()

        # Start the base worker
        await super().start()

    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        結果メッセージの処理
        """
        task_id = message.get("task_id", "unknown")
        status = message.get("status", "unknown")

        try:
            self.stats["messages_processed"] += 1

            # 処理タイプに応じて分岐
            if status == "completed":
                await self._handle_success_notification(message)
            elif status == "failed":
                await self._handle_error_notification(message)
            else:
                await self._handle_generic_notification(message)

            # 統計情報の更新
            await self._update_stats()

            # Report to Elder Tree
            if self.elder_systems_initialized:
                await self._report_result_processed(task_id, status)

            return {
                "task_id": task_id,
                "processed": True,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            # Handle specific exception case
            self.stats["notifications_failed"] += 1
            self.logger.error(
                "Failed to process result message", task_id=task_id, error=str(e)
            )

            # Report error to Elder Tree
            if self.elder_systems_initialized:
                await self._report_processing_error(task_id, str(e))

            raise

    async def _handle_success_notification(self, message: Dict[str, Any]):
        """成功通知の処理"""
        task_id = message.get("task_id")
        duration = message.get("duration", 0)
        result = message.get("result", "")
        files_created = message.get("files_created", [])

        # メイン通知メッセージ
        main_message = self._format_success_main_message(
            task_id, duration, len(files_created)
        )

        # 詳細情報（スレッド用）
        detail_message = self._format_success_detail_message(result, files_created)

        # Slack通知の送信
        await self._send_slack_notification(
            main_message, detail_message, color="good", task_id=task_id
        )

    async def _handle_error_notification(self, message: Dict[str, Any]):
        """エラー通知の処理"""
        task_id = message.get("task_id")
        error = message.get("error", "Unknown error")
        error_type = message.get("error_type", "Exception")
        duration = message.get("duration", 0)

        # メイン通知メッセージ
        main_message = self._format_error_main_message(task_id, error_type, duration)

        # 詳細情報（スレッド用）
        detail_message = self._format_error_detail_message(
            error, message.get("stack_trace", "")
        )

        # Slack通知の送信
        await self._send_slack_notification(
            main_message, detail_message, color="danger", task_id=task_id
        )

    async def _handle_generic_notification(self, message: Dict[str, Any]):
        """一般的な通知の処理"""
        task_id = message.get("task_id")
        status = message.get("status")

        main_message = f"📊 Task Update: {task_id}\nStatus: {status}"
        detail_message = json.dumps(message, indent=2, ensure_ascii=False)

        await self._send_slack_notification(
            main_message, detail_message, color="warning", task_id=task_id
        )

    def _format_success_main_message(
        self, task_id: str, duration: float, file_count: int
    ) -> str:
        """成功メッセージのメイン部分フォーマット"""
        duration_str = f"{duration:0.1f}s" if duration < 60 else f"{duration/60:0.1f}m"

        return f"""✅ **Task Completed Successfully**

📋 Task ID: `{task_id}`
⏱️ Duration: {duration_str}
📁 Files Created: {file_count}
🕐 Completed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"""

    def _format_success_detail_message(
        self, result: str, files_created: List[str]
    ) -> str:
        """成功メッセージの詳細部分フォーマット"""
        detail = "## 📊 Task Details\n\n"

        # 結果の要約
        if result:
            truncated_result = self._truncate_text(result, 500)
            detail += f"**Result:**\n```\n{truncated_result}\n```\n\n"

        # 作成されたファイル
        if files_created:
            detail += "**Created Files:**\n"
            for file_path in files_created[:10]:  # 最大10個
                detail += f"• `{file_path}`\n"

            if len(files_created) > 10:
                detail += f"• ... and {len(files_created) - 10} more files\n"

        return detail

    def _format_error_main_message(
        self, task_id: str, error_type: str, duration: float
    ) -> str:
        """エラーメッセージのメイン部分フォーマット"""
        duration_str = f"{duration:0.1f}s" if duration < 60 else f"{duration/60:0.1f}m"

        return f"""❌ **Task Failed**

📋 Task ID: `{task_id}`
🚨 Error Type: {error_type}
⏱️ Duration: {duration_str}
🕐 Failed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"""

    def _format_error_detail_message(self, error: str, stack_trace: str) -> str:
        """エラーメッセージの詳細部分フォーマット"""
        detail = "## 🚨 Error Details\n\n"

        # エラーメッセージ
        truncated_error = self._truncate_text(error, 300)
        detail += f"**Error Message:**\n```\n{truncated_error}\n```\n\n"

        # スタックトレース（ある場合）
        if stack_trace:
            truncated_trace = self._truncate_text(stack_trace, 1000)
            detail += f"**Stack Trace:**\n```\n{truncated_trace}\n```\n"

        return detail

    async def _send_slack_notification(
        self, main_message: str, detail_message: str, color: str, task_id: str
    ):
        """Slack通知の送信（レート制限・サイズ制限対応）"""
        try:
            # レート制限チェック
            await self.slack_rate_limiter.wait_if_needed("slack_notifications")

            # メッセージサイズのチェックと分割
            messages = self._split_message_if_needed(main_message, detail_message)

            # メイン通知の送信
            main_response = await self.slack_notifier.send_enhanced_notification(
                message=messages[0], color=color, task_id=task_id
            )

            # 追加メッセージがある場合は スレッドで送信
            if len(messages) > 1 and main_response.get("ts"):
                # Complex condition - consider breaking down
                for additional_message in messages[1:]:
                    await asyncio.sleep(0.5)  # 短い間隔
                    await self.slack_notifier.send_thread_reply(
                        thread_ts=main_response["ts"],
                        message=additional_message,
                        task_id=task_id,
                    )

            self.stats["notifications_sent"] += 1

            if len(messages) > 1:
                self.stats["messages_split"] += 1

        except Exception as e:
            # Handle specific exception case
            self.stats["notifications_failed"] += 1
            self.logger.error(
                "Slack notification failed", task_id=task_id, error=str(e)
            )
            # 失敗時はキャッシュに保存して後で再試行
            await self._cache_failed_notification(task_id, main_message, detail_message)

    def _split_message_if_needed(
        self, main_message: str, detail_message: str
    ) -> List[str]:
        """メッセージサイズ制限に応じてメッセージを分割"""
        combined = f"{main_message}\n\n{detail_message}"

        if len(combined) <= self.max_message_size:
            return [combined]

        # 分割が必要な場合
        messages = [main_message]

        # 詳細メッセージを分割
        remaining = detail_message
        while remaining:
            chunk_size = self.max_message_size - 100  # マージン
            if len(remaining) <= chunk_size:
                messages.append(remaining)
                break

            # 改行で分割を試行
            split_pos = remaining.rfind("\n", 0, chunk_size)
            if split_pos == -1:
                split_pos = chunk_size

            chunk = remaining[:split_pos]
            messages.append(chunk)
            remaining = remaining[split_pos:].lstrip()

        return messages

    def _truncate_text(self, text: str, max_length: int) -> str:
        """テキストの切り詰め"""
        if len(text) <= max_length:
            return text

        return text[: max_length - 3] + "..."

    async def _cache_failed_notification(
        self, task_id: str, main_message: str, detail_message: str
    ):
        """失敗した通知をキャッシュに保存"""
        failed_notification = {
            "task_id": task_id,
            "main_message": main_message,
            "detail_message": detail_message,
            "timestamp": datetime.utcnow().isoformat(),
            "retry_count": 0,
        }

        await self.cache_manager.set(
            f"failed_notification:{task_id}", failed_notification, ttl=86400  # 24時間保持
        )

    async def _update_stats(self):
        """統計情報の更新と永続化"""
        # 1時間ごとに統計をファイルに保存
        now = datetime.utcnow()
        if (now - self.stats["last_reset"]).total_seconds() >= 3600:
            await self._save_stats()

            # Redisにも保存
            await self.cache_manager.set("result_worker_stats", self.stats, ttl=86400)

    async def _save_stats(self):
        """統計情報をファイルに保存"""
        try:
            # 既存の統計を読み込み
            historical_stats = []
            if self.stats_file.exists():
                async with aiofiles.open(self.stats_file, "r") as f:
                    content = await f.read()
                    if content.strip():
                        historical_stats = json.loads(content)

            # 現在の統計を追加
            current_stats = {**self.stats, "timestamp": datetime.utcnow().isoformat()}
            historical_stats.append(current_stats)

            # 古い統計を削除（最新100件のみ保持）
            if len(historical_stats) > 100:
                historical_stats = historical_stats[-100:]

            # ファイルに保存
            async with aiofiles.open(self.stats_file, "w") as f:
                await f.write(json.dumps(historical_stats, indent=2))

            # 統計をリセット
            self.stats = {
                "messages_processed": 0,
                "notifications_sent": 0,
                "notifications_failed": 0,
                "messages_split": 0,
                "last_reset": datetime.utcnow(),
            }

        except Exception as e:
            # Handle specific exception case
            self.logger.error("Failed to save statistics", error=str(e))

    async def get_statistics(self) -> Dict[str, Any]:
        """統計情報の取得"""
        return {"current": self.stats, "file_path": str(self.stats_file)}

    async def _report_to_result_sage(self, message: str, event_type: str):
        """Report to Result/Incident Sage in Elder Tree hierarchy"""
        if not self.elder_systems_initialized or not self.four_sages:
            # Complex condition - consider breaking down
            return

        try:
            elder_message = ElderMessage(
                sender="async_result_worker",
                recipient="incident_sage",  # Results often relate to incidents
                content=message,
                event_type=event_type,
                timestamp=datetime.utcnow().isoformat(),
            )

            await self.four_sages.send_to_sage(
                sage_type=SageType.INCIDENT, message=elder_message
            )
        except Exception as e:
            # Handle specific exception case
            self.logger.warning(f"Failed to report to Result Sage: {e}")

    async def _report_result_processed(self, task_id: str, status: str):
        """Report result processing to Elder Tree"""
        message = f"Result for task {task_id} processed with status: {status}"
        await self._report_to_result_sage(message, "result_processed")

    async def _report_processing_error(self, task_id: str, error: str):
        """Report processing error to Elder Tree"""
        message = f"Error processing result for task {task_id}: {error}"
        await self._report_to_result_sage(message, "processing_error")

        # Critical errors may need Elder Council attention
        if self.elder_council:
            await self.elder_council.summon_for_critical_error(
                error_type="ResultProcessingError",
                error_details={"task_id": task_id, "error": error},
            )

    async def get_elder_result_status(self) -> Dict[str, Any]:
        """Get Elder-aware result worker status"""
        status = {
            "worker_type": "async_result_worker",
            "elder_systems_initialized": self.elder_systems_initialized,
            "elder_role": self.elder_role.value if self.elder_role else None,
            "reporting_sage": "incident_sage",  # Results report to Incident Sage
            "messages_processed": self.stats["messages_processed"],
            "notifications_sent": self.stats["notifications_sent"],
            "current_status": "active"
            if self.elder_systems_initialized
            else "standalone",
        }

        if self.elder_systems_initialized and self.four_sages:
            # Complex condition - consider breaking down
            try:
                sage_status = await self.four_sages.get_sage_status(SageType.INCIDENT)
                status["sage_connection"] = sage_status
            except:
                status["sage_connection"] = "unavailable"

        return status

    async def cleanup(self):
        """Cleanup resources including Elder systems"""
        if self.elder_systems_initialized:
            try:
                await self._report_to_result_sage(
                    "Result Worker shutting down", "shutdown"
                )
                if self.four_sages:
                    await self.four_sages.cleanup()
                if self.elder_council:
                    await self.elder_council.cleanup()
                self.logger.info("Elder systems cleaned up")
            except Exception as e:
                # Handle specific exception case
                self.logger.error(f"Error during Elder cleanup: {e}")

        # Call parent cleanup if available
        if hasattr(super(), "cleanup"):
            await super().cleanup()


# 定期レポート機能
class PeriodicReporter:
    """定期的な統計レポート生成"""

    def __init__(self, result_worker: AsyncResultWorker):
        self.worker = result_worker
        self.logger = structlog.get_logger(__name__)

    async def start_reporting(self):
        """定期レポートの開始"""
        while self.worker.running:
            try:
                await self._generate_hourly_report()
                await asyncio.sleep(3600)  # 1時間待機

            except Exception as e:
                # Handle specific exception case
                self.logger.error("Periodic report error", error=str(e))
                await asyncio.sleep(300)  # エラー時は5分待機

    async def _generate_hourly_report(self):
        """時間ごとのレポート生成"""
        stats = await self.worker.get_statistics()
        current_stats = stats["current"]

        # レート計算
        elapsed_time = (datetime.utcnow() - current_stats["last_reset"]).total_seconds()
        if elapsed_time > 0:
            processing_rate = current_stats["messages_processed"] / elapsed_time * 3600
            success_rate = (
                current_stats["notifications_sent"]
                / max(1, current_stats["messages_processed"])
            ) * 100
        else:
            processing_rate = 0
            success_rate = 0

        # レポートメッセージ
        report = f"""📊 **Result Worker Hourly Report**

⚡ **Performance Metrics:**
• Messages Processed: {current_stats['messages_processed']}
• Processing Rate: {processing_rate:0.1f} msgs/hour
• Notifications Sent: {current_stats['notifications_sent']}
• Success Rate: {success_rate:0.1f}%

🔧 **Quality Metrics:**
• Failed Notifications: {current_stats['notifications_failed']}
• Split Messages: {current_stats['messages_split']}

🕐 Report Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"""

        # レポートをSlackに送信
        if current_stats["messages_processed"] > 0:  # アクティビティがある場合のみ
            await self.worker.slack_notifier.send_message(report)


# 実行用のメイン関数
async def main():
    """ワーカーのエントリーポイント"""
    import yaml

    # 設定読み込み
    config_path = PROJECT_ROOT / "config" / "config.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # ワーカー起動
    worker = AsyncResultWorker(config)

    # 定期レポート機能の開始
    reporter = PeriodicReporter(worker)
    report_task = asyncio.create_task(reporter.start_reporting())

    # ワーカー実行
    try:
        await worker.start()
    finally:
        report_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
