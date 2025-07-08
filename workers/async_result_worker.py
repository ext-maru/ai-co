#!/usr/bin/env python3
"""
非同期対応Result Worker
レート制限、メッセージサイズ制限、統計情報永続化対応
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import aiofiles
import structlog

# プロジェクトルートをPythonパスに追加
import sys
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.async_base_worker import AsyncBaseWorker
from core.rate_limiter import RateLimiter, CacheManager
from libs.slack_notifier import SlackNotifier

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
            input_queues=['results', 'ai_results'],
            output_queues=[]  # 終端ワーカー
        )
        
        # Slack通知設定
        self.slack_notifier = SlackNotifier()
        
        # レート制限（Slack API用）
        self.slack_rate_limiter = RateLimiter(
            rate=config.get('slack_rate_limit', 1),  # 1msg/sec
            period=1,
            redis_client=self.redis_client
        )
        
        # キャッシュマネージャ
        self.cache_manager = CacheManager(
            redis_client=self.redis_client,
            default_ttl=config.get('cache_ttl', 86400)  # 24時間
        )
        
        # メッセージサイズ制限
        self.max_message_size = config.get('slack_max_message_size', 3000)
        
        # 統計情報
        self.stats = {
            'messages_processed': 0,
            'notifications_sent': 0,
            'notifications_failed': 0,
            'messages_split': 0,
            'last_reset': datetime.utcnow()
        }
        
        # 統計情報ファイル
        self.stats_file = Path(config.get('stats_file', 
            PROJECT_ROOT / "data" / "result_worker_stats.json"))
        self.stats_file.parent.mkdir(exist_ok=True)
        
        # 定期レポート設定
        self.report_interval = config.get('report_interval_hours', 1)
        
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        結果メッセージの処理
        """
        task_id = message.get('task_id', 'unknown')
        status = message.get('status', 'unknown')
        
        try:
            self.stats['messages_processed'] += 1
            
            # 処理タイプに応じて分岐
            if status == 'completed':
                await self._handle_success_notification(message)
            elif status == 'failed':
                await self._handle_error_notification(message)
            else:
                await self._handle_generic_notification(message)
            
            # 統計情報の更新
            await self._update_stats()
            
            return {
                'task_id': task_id,
                'processed': True,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.stats['notifications_failed'] += 1
            self.logger.error(
                "Failed to process result message",
                task_id=task_id,
                error=str(e)
            )
            raise
    
    async def _handle_success_notification(self, message: Dict[str, Any]):
        """成功通知の処理"""
        task_id = message.get('task_id')
        duration = message.get('duration', 0)
        result = message.get('result', '')
        files_created = message.get('files_created', [])
        
        # メイン通知メッセージ
        main_message = self._format_success_main_message(
            task_id, duration, len(files_created)
        )
        
        # 詳細情報（スレッド用）
        detail_message = self._format_success_detail_message(
            result, files_created
        )
        
        # Slack通知の送信
        await self._send_slack_notification(
            main_message,
            detail_message,
            color="good",
            task_id=task_id
        )
    
    async def _handle_error_notification(self, message: Dict[str, Any]):
        """エラー通知の処理"""
        task_id = message.get('task_id')
        error = message.get('error', 'Unknown error')
        error_type = message.get('error_type', 'Exception')
        duration = message.get('duration', 0)
        
        # メイン通知メッセージ
        main_message = self._format_error_main_message(
            task_id, error_type, duration
        )
        
        # 詳細情報（スレッド用）
        detail_message = self._format_error_detail_message(
            error, message.get('stack_trace', '')
        )
        
        # Slack通知の送信
        await self._send_slack_notification(
            main_message,
            detail_message,
            color="danger",
            task_id=task_id
        )
    
    async def _handle_generic_notification(self, message: Dict[str, Any]):
        """一般的な通知の処理"""
        task_id = message.get('task_id')
        status = message.get('status')
        
        main_message = f"📊 Task Update: {task_id}\nStatus: {status}"
        detail_message = json.dumps(message, indent=2, ensure_ascii=False)
        
        await self._send_slack_notification(
            main_message,
            detail_message,
            color="warning",
            task_id=task_id
        )
    
    def _format_success_main_message(
        self, 
        task_id: str, 
        duration: float, 
        file_count: int
    ) -> str:
        """成功メッセージのメイン部分フォーマット"""
        duration_str = f"{duration:.1f}s" if duration < 60 else f"{duration/60:.1f}m"
        
        return f"""✅ **Task Completed Successfully**

📋 Task ID: `{task_id}`
⏱️ Duration: {duration_str}
📁 Files Created: {file_count}
🕐 Completed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"""
    
    def _format_success_detail_message(
        self, 
        result: str, 
        files_created: List[str]
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
        self, 
        task_id: str, 
        error_type: str, 
        duration: float
    ) -> str:
        """エラーメッセージのメイン部分フォーマット"""
        duration_str = f"{duration:.1f}s" if duration < 60 else f"{duration/60:.1f}m"
        
        return f"""❌ **Task Failed**

📋 Task ID: `{task_id}`
🚨 Error Type: {error_type}
⏱️ Duration: {duration_str}
🕐 Failed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"""
    
    def _format_error_detail_message(
        self, 
        error: str, 
        stack_trace: str
    ) -> str:
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
        self,
        main_message: str,
        detail_message: str,
        color: str,
        task_id: str
    ):
        """Slack通知の送信（レート制限・サイズ制限対応）"""
        try:
            # レート制限チェック
            await self.slack_rate_limiter.wait_if_needed("slack_notifications")
            
            # メッセージサイズのチェックと分割
            messages = self._split_message_if_needed(main_message, detail_message)
            
            # メイン通知の送信
            main_response = await self.slack_notifier.send_enhanced_notification(
                message=messages[0],
                color=color,
                task_id=task_id
            )
            
            # 追加メッセージがある場合は スレッドで送信
            if len(messages) > 1 and main_response.get('ts'):
                for additional_message in messages[1:]:
                    await asyncio.sleep(0.5)  # 短い間隔
                    await self.slack_notifier.send_thread_reply(
                        thread_ts=main_response['ts'],
                        message=additional_message,
                        task_id=task_id
                    )
            
            self.stats['notifications_sent'] += 1
            
            if len(messages) > 1:
                self.stats['messages_split'] += 1
            
        except Exception as e:
            self.stats['notifications_failed'] += 1
            self.logger.error(
                "Slack notification failed",
                task_id=task_id,
                error=str(e)
            )
            # 失敗時はキャッシュに保存して後で再試行
            await self._cache_failed_notification(task_id, main_message, detail_message)
    
    def _split_message_if_needed(
        self, 
        main_message: str, 
        detail_message: str
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
            split_pos = remaining.rfind('\n', 0, chunk_size)
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
        
        return text[:max_length-3] + "..."
    
    async def _cache_failed_notification(
        self, 
        task_id: str, 
        main_message: str, 
        detail_message: str
    ):
        """失敗した通知をキャッシュに保存"""
        failed_notification = {
            'task_id': task_id,
            'main_message': main_message,
            'detail_message': detail_message,
            'timestamp': datetime.utcnow().isoformat(),
            'retry_count': 0
        }
        
        await self.cache_manager.set(
            f"failed_notification:{task_id}",
            failed_notification,
            ttl=86400  # 24時間保持
        )
    
    async def _update_stats(self):
        """統計情報の更新と永続化"""
        # 1時間ごとに統計をファイルに保存
        now = datetime.utcnow()
        if (now - self.stats['last_reset']).total_seconds() >= 3600:
            await self._save_stats()
            
            # Redisにも保存
            await self.cache_manager.set(
                "result_worker_stats",
                self.stats,
                ttl=86400
            )
    
    async def _save_stats(self):
        """統計情報をファイルに保存"""
        try:
            # 既存の統計を読み込み
            historical_stats = []
            if self.stats_file.exists():
                async with aiofiles.open(self.stats_file, 'r') as f:
                    content = await f.read()
                    if content.strip():
                        historical_stats = json.loads(content)
            
            # 現在の統計を追加
            current_stats = {
                **self.stats,
                'timestamp': datetime.utcnow().isoformat()
            }
            historical_stats.append(current_stats)
            
            # 古い統計を削除（最新100件のみ保持）
            if len(historical_stats) > 100:
                historical_stats = historical_stats[-100:]
            
            # ファイルに保存
            async with aiofiles.open(self.stats_file, 'w') as f:
                await f.write(json.dumps(historical_stats, indent=2))
            
            # 統計をリセット
            self.stats = {
                'messages_processed': 0,
                'notifications_sent': 0,
                'notifications_failed': 0,
                'messages_split': 0,
                'last_reset': datetime.utcnow()
            }
            
        except Exception as e:
            self.logger.error(
                "Failed to save statistics",
                error=str(e)
            )
    
    async def get_statistics(self) -> Dict[str, Any]:
        """統計情報の取得"""
        return {
            'current': self.stats,
            'file_path': str(self.stats_file)
        }


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
                self.logger.error(
                    "Periodic report error",
                    error=str(e)
                )
                await asyncio.sleep(300)  # エラー時は5分待機
    
    async def _generate_hourly_report(self):
        """時間ごとのレポート生成"""
        stats = await self.worker.get_statistics()
        current_stats = stats['current']
        
        # レート計算
        elapsed_time = (datetime.utcnow() - current_stats['last_reset']).total_seconds()
        if elapsed_time > 0:
            processing_rate = current_stats['messages_processed'] / elapsed_time * 3600
            success_rate = (
                current_stats['notifications_sent'] / 
                max(1, current_stats['messages_processed'])
            ) * 100
        else:
            processing_rate = 0
            success_rate = 0
        
        # レポートメッセージ
        report = f"""📊 **Result Worker Hourly Report**

⚡ **Performance Metrics:**
• Messages Processed: {current_stats['messages_processed']}
• Processing Rate: {processing_rate:.1f} msgs/hour
• Notifications Sent: {current_stats['notifications_sent']}
• Success Rate: {success_rate:.1f}%

🔧 **Quality Metrics:**
• Failed Notifications: {current_stats['notifications_failed']}
• Split Messages: {current_stats['messages_split']}

🕐 Report Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"""
        
        # レポートをSlackに送信
        if current_stats['messages_processed'] > 0:  # アクティビティがある場合のみ
            await self.worker.slack_notifier.send_message(report)


# 実行用のメイン関数
async def main():
    """ワーカーのエントリーポイント"""
    import yaml
    
    # 設定読み込み
    config_path = PROJECT_ROOT / "config" / "config.yaml"
    with open(config_path, 'r') as f:
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