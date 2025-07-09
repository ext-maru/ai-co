#!/usr/bin/env python3
"""
Elder階層統合 非同期Result Worker v2.0
AI Company Elder Hierarchy Integrated Asynchronous Result Processing

エルダーズ評議会承認済み統合認証対応非同期結果処理ワーカー
Elder階層別通知権限・チャンネル管理・セキュリティ監査対応
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import aiofiles
import structlog
import sys

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Elder階層システム統合
from core.elder_aware_base_worker import (
    ElderAwareBaseWorker,
    ElderTaskContext,
    ElderTaskResult,
    WorkerExecutionMode,
    ElderTaskPriority,
    elder_worker_required,
    SecurityError
)

# 統合認証システム
from libs.unified_auth_provider import (
    UnifiedAuthProvider,
    ElderRole,
    SageType,
    User,
    AuthSession
)

# 既存システム統合
from core.async_base_worker import AsyncBaseWorker
from core.rate_limiter import RateLimiter, CacheManager
from libs.slack_notifier import SlackNotifier
from core import get_config, EMOJI

# Elder階層専用絵文字
ELDER_RESULT_EMOJI = {
    **EMOJI,
    'result': '📊',
    'notify': '📢',
    'council': '🏛️',
    'sage': '🧙‍♂️',
    'crown': '👑',
    'shield': '🛡️',
    'elder': '⚡',
    'secure': '🔒',
    'stats': '📈',
    'authority': '🔱',
    'channel': '📺'
}


class ElderAsyncResultWorker(ElderAwareBaseWorker):
    """
    Elder階層統合非同期Result Worker
    
    Elder階層システムと統合認証に対応した非同期結果処理・通知システム
    階層別通知権限、チャンネル管理、セキュリティ監査対応
    """
    
    def __init__(self, worker_id: Optional[str] = None,
                 auth_provider: Optional[UnifiedAuthProvider] = None,
                 config: Optional[Dict[str, Any]] = None):
        # Elder階層BaseWorker初期化
        ElderAwareBaseWorker.__init__(
            self,
            auth_provider=auth_provider,
            required_elder_role=ElderRole.SERVANT,  # 基本的にサーバントでも利用可能
            required_sage_type=None
        )
        
        # ワーカー設定
        self.worker_type = 'async_result'
        self.worker_id = worker_id or f"elder_async_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Elder階層対応キュー設定
        self.input_queue = 'ai_results_elder'
        self.output_queue = None  # 終端ワーカー
        
        self.config = config or get_config()
        
        # Slack通知設定（Elder階層対応）
        self.slack_notifier = SlackNotifier()
        self.elder_channels = self._configure_elder_channels()
        
        # レート制限（Elder階層別）
        self.slack_rate_limiters = {
            ElderRole.GRAND_ELDER: RateLimiter(
                rate=self.config.get('grand_elder_rate_limit', 10),  # 10msg/sec
                period=1,
                redis_client=None
            ),
            ElderRole.CLAUDE_ELDER: RateLimiter(
                rate=self.config.get('claude_elder_rate_limit', 5),  # 5msg/sec
                period=1,
                redis_client=None
            ),
            ElderRole.SAGE: RateLimiter(
                rate=self.config.get('sage_rate_limit', 2),  # 2msg/sec
                period=1,
                redis_client=None
            ),
            ElderRole.SERVANT: RateLimiter(
                rate=self.config.get('servant_rate_limit', 1),  # 1msg/sec
                period=1,
                redis_client=None
            )
        }
        
        # キャッシュマネージャ
        self.cache_manager = CacheManager(
            redis_client=None,
            default_ttl=self.config.get('cache_ttl', 86400)
        )
        
        # メッセージサイズ制限（Elder階層別）
        self.max_message_sizes = {
            ElderRole.GRAND_ELDER: 10000,   # 最大サイズ
            ElderRole.CLAUDE_ELDER: 5000,
            ElderRole.SAGE: 3000,
            ElderRole.SERVANT: 2000         # 最小サイズ
        }
        
        # Elder階層統計情報
        self.elder_stats = {
            'by_role': {role.value: {
                'messages_processed': 0,
                'notifications_sent': 0,
                'notifications_failed': 0,
                'messages_split': 0
            } for role in ElderRole},
            'by_priority': {priority.value: 0 for priority in ElderTaskPriority},
            'security_events': 0,
            'last_reset': datetime.utcnow()
        }
        
        # 統計情報ファイル
        self.stats_file = Path(self.config.get('stats_file', 
            PROJECT_ROOT / "data" / "elder_result_worker_stats.json"))
        self.stats_file.parent.mkdir(exist_ok=True)
        
        # Elder階層権限設定
        self.elder_permissions = self._configure_elder_permissions()
        
        # 定期レポート設定
        self.report_interval = self.config.get('report_interval_hours', 1)
        
        self.logger.info(f"{ELDER_RESULT_EMOJI['council']} Elder Async Result Worker initialized - Required: {self.required_elder_role.value}")
    
    def _configure_elder_channels(self) -> Dict[ElderRole, Dict[str, str]]:
        """Elder階層別通知チャンネル設定"""
        return {
            ElderRole.GRAND_ELDER: {
                'default': self.config.get('SLACK_ELDER_COUNCIL_CHANNEL', '#elder-council'),
                'emergency': self.config.get('SLACK_EMERGENCY_CHANNEL', '#emergency'),
                'security': self.config.get('SLACK_SECURITY_CHANNEL', '#security-alerts')
            },
            ElderRole.CLAUDE_ELDER: {
                'default': self.config.get('SLACK_DEVELOPMENT_CHANNEL', '#development'),
                'sage': self.config.get('SLACK_SAGE_CHANNEL', '#sage-coordination'),
                'alerts': self.config.get('SLACK_ALERTS_CHANNEL', '#alerts')
            },
            ElderRole.SAGE: {
                'default': self.config.get('SLACK_SAGE_CHANNEL', '#sage-coordination'),
                'general': self.config.get('SLACK_GENERAL_CHANNEL', '#general')
            },
            ElderRole.SERVANT: {
                'default': self.config.get('SLACK_GENERAL_CHANNEL', '#general')
            }
        }
    
    def _configure_elder_permissions(self) -> Dict[ElderRole, Dict[str, Any]]:
        """Elder階層別権限設定"""
        return {
            ElderRole.SERVANT: {
                'can_notify_public': True,
                'can_notify_private': False,
                'can_notify_emergency': False,
                'can_access_full_details': False,
                'can_send_attachments': False,
                'max_notifications_per_hour': 10
            },
            ElderRole.SAGE: {
                'can_notify_public': True,
                'can_notify_private': True,
                'can_notify_emergency': False,
                'can_access_full_details': True,
                'can_send_attachments': True,
                'max_notifications_per_hour': 100
            },
            ElderRole.CLAUDE_ELDER: {
                'can_notify_public': True,
                'can_notify_private': True,
                'can_notify_emergency': True,
                'can_access_full_details': True,
                'can_send_attachments': True,
                'max_notifications_per_hour': 1000
            },
            ElderRole.GRAND_ELDER: {
                'can_notify_public': True,
                'can_notify_private': True,
                'can_notify_emergency': True,
                'can_access_full_details': True,
                'can_send_attachments': True,
                'max_notifications_per_hour': None  # 無制限
            }
        }
    
    async def process_elder_result_message(self, elder_context: ElderTaskContext,
                                         message: Dict[str, Any]) -> ElderTaskResult:
        """Elder階層認証済み結果メッセージ処理"""
        task_id = message.get('task_id', 'unknown')
        status = message.get('status', 'unknown')
        priority = ElderTaskPriority(message.get('elder_context', {}).get('priority', 'medium'))
        
        # Elder階層ログ
        self.audit_logger.log_elder_action(
            elder_context,
            f"result_processing_start",
            f"Processing result for task {task_id} - Status: {status}"
        )
        
        try:
            # Elder階層統計更新
            self.elder_stats['by_role'][elder_context.user.elder_role.value]['messages_processed'] += 1
            self.elder_stats['by_priority'][priority.value] += 1
            
            # 権限チェック
            permissions = self.elder_permissions[elder_context.user.elder_role]
            
            # セキュリティチェック
            security_check = await self._perform_security_check(message, elder_context)
            if not security_check['passed']:
                self.logger.warning(
                    f"{ELDER_RESULT_EMOJI['secure']} Security check failed: {security_check['reason']}"
                )
                
                self.audit_logger.log_security_event(
                    elder_context,
                    "result_notification_blocked",
                    security_check
                )
                
                self.elder_stats['security_events'] += 1
                return ElderTaskResult(
                    status='blocked',
                    result={'reason': security_check['reason']},
                    execution_time=0,
                    elder_context=elder_context
                )
            
            # 処理タイプに応じて分岐
            if status == 'completed':
                await self._handle_success_notification_with_elder(message, elder_context)
            elif status == 'failed':
                await self._handle_error_notification_with_elder(message, elder_context)
            else:
                await self._handle_generic_notification_with_elder(message, elder_context)
            
            # 統計情報の更新
            await self._update_elder_stats()
            
            # 成功ログ
            self.audit_logger.log_elder_action(
                elder_context,
                f"result_processing_complete",
                f"Result processing completed for task {task_id}"
            )
            
            return ElderTaskResult(
                status='completed',
                result={
                    'task_id': task_id,
                    'notification_sent': True,
                    'timestamp': datetime.utcnow().isoformat()
                },
                execution_time=0.1,
                elder_context=elder_context
            )
            
        except Exception as e:
            # エラー統計更新
            self.elder_stats['by_role'][elder_context.user.elder_role.value]['notifications_failed'] += 1
            
            # エラーログ
            self.audit_logger.log_elder_action(
                elder_context,
                f"result_processing_error",
                f"Result processing failed for task {task_id}: {str(e)}"
            )
            
            self.audit_logger.log_security_event(
                elder_context,
                "result_processing_error",
                {"task_id": task_id, "error": str(e)}
            )
            
            raise
    
    async def _perform_security_check(self, message: Dict[str, Any],
                                    elder_context: ElderTaskContext) -> Dict[str, Any]:
        """セキュリティチェック実行"""
        # センシティブ情報チェック
        sensitive_patterns = ['password', 'token', 'secret', 'key', 'credential']
        message_str = json.dumps(message).lower()
        
        for pattern in sensitive_patterns:
            if pattern in message_str:
                # Elder階層によって異なる対応
                if elder_context.user.elder_role in [ElderRole.GRAND_ELDER, ElderRole.CLAUDE_ELDER]:
                    # 高権限者は警告のみ
                    self.logger.warning(f"Sensitive pattern detected: {pattern}")
                else:
                    # 低権限者はブロック
                    return {
                        'passed': False,
                        'reason': f'Sensitive information detected: {pattern}',
                        'severity': 'high'
                    }
        
        # メッセージサイズチェック
        max_size = 1024 * 1024  # 1MB
        if len(message_str) > max_size:
            return {
                'passed': False,
                'reason': 'Message size exceeds limit',
                'severity': 'medium'
            }
        
        return {
            'passed': True,
            'reason': None,
            'severity': None
        }
    
    async def _handle_success_notification_with_elder(self, message: Dict[str, Any],
                                                    elder_context: ElderTaskContext):
        """Elder階層対応成功通知処理"""
        task_id = message.get('task_id')
        duration = message.get('duration', 0)
        result = message.get('result', '')
        files_created = message.get('files_created', [])
        elder_info = message.get('elder_context', {})
        
        # メイン通知メッセージ（Elder情報付き）
        main_message = self._format_success_main_message_elder(
            task_id, duration, len(files_created), elder_info
        )
        
        # 詳細情報（権限に応じてフィルタリング）
        permissions = self.elder_permissions[elder_context.user.elder_role]
        if permissions['can_access_full_details']:
            detail_message = self._format_success_detail_message(result, files_created)
        else:
            detail_message = self._format_limited_detail_message(result)
        
        # 通知チャンネル決定
        channel = self._determine_notification_channel(message, elder_context)
        
        # Elder階層別レート制限
        rate_limiter = self.slack_rate_limiters[elder_context.user.elder_role]
        
        # Slack通知の送信
        await self._send_elder_slack_notification(
            main_message,
            detail_message,
            color="good",
            task_id=task_id,
            channel=channel,
            elder_context=elder_context,
            rate_limiter=rate_limiter
        )
    
    async def _handle_error_notification_with_elder(self, message: Dict[str, Any],
                                                  elder_context: ElderTaskContext):
        """Elder階層対応エラー通知処理"""
        task_id = message.get('task_id')
        error = message.get('error', 'Unknown error')
        error_type = message.get('error_type', 'Exception')
        duration = message.get('duration', 0)
        elder_info = message.get('elder_context', {})
        
        # メイン通知メッセージ（Elder情報付き）
        main_message = self._format_error_main_message_elder(
            task_id, error_type, duration, elder_info
        )
        
        # 詳細情報（権限に応じてフィルタリング）
        permissions = self.elder_permissions[elder_context.user.elder_role]
        if permissions['can_access_full_details']:
            detail_message = self._format_error_detail_message(
                error, message.get('stack_trace', '')
            )
        else:
            detail_message = f"Error: {error[:100]}..."
        
        # エラーは高優先度チャンネルへ
        channel = self._determine_error_channel(message, elder_context)
        
        # Elder階層別レート制限
        rate_limiter = self.slack_rate_limiters[elder_context.user.elder_role]
        
        # Slack通知の送信
        await self._send_elder_slack_notification(
            main_message,
            detail_message,
            color="danger",
            task_id=task_id,
            channel=channel,
            elder_context=elder_context,
            rate_limiter=rate_limiter
        )
        
        # 重大エラーの場合、Elder Council に通知
        if error_type in ['SecurityError', 'CriticalError']:
            await self._notify_elder_council(message, elder_context)
    
    async def _handle_generic_notification_with_elder(self, message: Dict[str, Any],
                                                    elder_context: ElderTaskContext):
        """Elder階層対応一般通知処理"""
        task_id = message.get('task_id')
        status = message.get('status')
        
        main_message = f"{ELDER_RESULT_EMOJI['result']} Task Update: {task_id}\nStatus: {status}"
        
        # 権限に応じた詳細レベル
        permissions = self.elder_permissions[elder_context.user.elder_role]
        if permissions['can_access_full_details']:
            detail_message = json.dumps(message, indent=2, ensure_ascii=False)
        else:
            detail_message = f"Status: {status}\nProcessed by: {elder_context.user.username}"
        
        channel = self._determine_notification_channel(message, elder_context)
        rate_limiter = self.slack_rate_limiters[elder_context.user.elder_role]
        
        await self._send_elder_slack_notification(
            main_message,
            detail_message,
            color="warning",
            task_id=task_id,
            channel=channel,
            elder_context=elder_context,
            rate_limiter=rate_limiter
        )
    
    def _format_success_main_message_elder(self, task_id: str, duration: float,
                                         file_count: int, elder_info: Dict) -> str:
        """Elder情報付き成功メッセージフォーマット"""
        duration_str = f"{duration:.1f}s" if duration < 60 else f"{duration/60:.1f}m"
        
        elder_badge = self._get_elder_badge(elder_info.get('elder_role', 'unknown'))
        priority_icon = self._get_priority_icon(elder_info.get('priority', 'medium'))
        
        return f"""{ELDER_RESULT_EMOJI['success']} **Task Completed Successfully** {elder_badge}

📋 Task ID: `{task_id}`
⏱️ Duration: {duration_str}
📁 Files Created: {file_count}
{priority_icon} Priority: {elder_info.get('priority', 'medium').upper()}
👤 Processed by: {elder_info.get('processed_by', 'system')}
🕐 Completed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"""
    
    def _format_error_main_message_elder(self, task_id: str, error_type: str,
                                       duration: float, elder_info: Dict) -> str:
        """Elder情報付きエラーメッセージフォーマット"""
        duration_str = f"{duration:.1f}s" if duration < 60 else f"{duration/60:.1f}m"
        
        elder_badge = self._get_elder_badge(elder_info.get('elder_role', 'unknown'))
        priority_icon = self._get_priority_icon(elder_info.get('priority', 'medium'))
        
        return f"""{ELDER_RESULT_EMOJI['error']} **Task Failed** {elder_badge}

📋 Task ID: `{task_id}`
🚨 Error Type: {error_type}
⏱️ Duration: {duration_str}
{priority_icon} Priority: {elder_info.get('priority', 'medium').upper()}
👤 Processed by: {elder_info.get('processed_by', 'system')}
🕐 Failed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"""
    
    def _format_limited_detail_message(self, result: str) -> str:
        """制限付き詳細メッセージフォーマット"""
        return f"Result summary: {result[:200]}..." if result else "No details available."
    
    def _get_elder_badge(self, elder_role: str) -> str:
        """Elder階層バッジ取得"""
        badges = {
            'grand_elder': '👑',
            'claude_elder': '🤖',
            'sage': '🧙',
            'servant': '🧝'
        }
        return badges.get(elder_role, '❓')
    
    def _get_priority_icon(self, priority: str) -> str:
        """優先度アイコン取得"""
        icons = {
            'critical': '🚨',
            'high': '⚡',
            'medium': '📌',
            'low': '📎'
        }
        return icons.get(priority, '📌')
    
    def _determine_notification_channel(self, message: Dict[str, Any],
                                      elder_context: ElderTaskContext) -> str:
        """通知チャンネル決定"""
        elder_channels = self.elder_channels[elder_context.user.elder_role]
        priority = message.get('elder_context', {}).get('priority', 'medium')
        
        # 優先度に応じたチャンネル選択
        if priority == 'critical' and 'emergency' in elder_channels:
            return elder_channels['emergency']
        elif priority == 'high' and 'alerts' in elder_channels:
            return elder_channels['alerts']
        else:
            return elder_channels.get('default', '#general')
    
    def _determine_error_channel(self, message: Dict[str, Any],
                               elder_context: ElderTaskContext) -> str:
        """エラー通知チャンネル決定"""
        elder_channels = self.elder_channels[elder_context.user.elder_role]
        error_type = message.get('error_type', 'Exception')
        
        # セキュリティエラーは専用チャンネルへ
        if error_type in ['SecurityError', 'AuthenticationError']:
            return elder_channels.get('security', elder_channels.get('default', '#general'))
        else:
            return elder_channels.get('alerts', elder_channels.get('default', '#general'))
    
    async def _send_elder_slack_notification(self, main_message: str, detail_message: str,
                                           color: str, task_id: str, channel: str,
                                           elder_context: ElderTaskContext,
                                           rate_limiter: RateLimiter):
        """Elder階層対応Slack通知送信"""
        try:
            # レート制限チェック
            await rate_limiter.wait_if_needed(f"slack_{elder_context.user.elder_role.value}")
            
            # メッセージサイズ制限
            max_size = self.max_message_sizes[elder_context.user.elder_role]
            messages = self._split_message_if_needed_elder(
                main_message, detail_message, max_size
            )
            
            # メイン通知の送信
            main_response = await self.slack_notifier.send_enhanced_notification(
                message=messages[0],
                color=color,
                task_id=task_id,
                channel=channel
            )
            
            # 追加メッセージがある場合はスレッドで送信
            if len(messages) > 1 and main_response.get('ts'):
                for additional_message in messages[1:]:
                    await asyncio.sleep(0.5)
                    await self.slack_notifier.send_thread_reply(
                        thread_ts=main_response['ts'],
                        message=additional_message,
                        task_id=task_id,
                        channel=channel
                    )
            
            # 統計更新
            self.elder_stats['by_role'][elder_context.user.elder_role.value]['notifications_sent'] += 1
            if len(messages) > 1:
                self.elder_stats['by_role'][elder_context.user.elder_role.value]['messages_split'] += 1
            
            # 監査ログ
            self.audit_logger.log_elder_action(
                elder_context,
                "notification_sent",
                f"Notification sent to {channel} for task {task_id}"
            )
            
        except Exception as e:
            self.elder_stats['by_role'][elder_context.user.elder_role.value]['notifications_failed'] += 1
            
            self.logger.error(
                "Elder Slack notification failed",
                task_id=task_id,
                channel=channel,
                error=str(e)
            )
            
            # 失敗時はキャッシュに保存
            await self._cache_failed_notification_elder(
                task_id, main_message, detail_message, channel, elder_context
            )
    
    def _split_message_if_needed_elder(self, main_message: str, detail_message: str,
                                     max_size: int) -> List[str]:
        """Elder階層別メッセージ分割"""
        combined = f"{main_message}\n\n{detail_message}"
        
        if len(combined) <= max_size:
            return [combined]
        
        # 分割が必要な場合
        messages = [main_message]
        
        # 詳細メッセージを分割
        remaining = detail_message
        while remaining:
            chunk_size = max_size - 100  # マージン
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
    
    async def _notify_elder_council(self, message: Dict[str, Any],
                                  elder_context: ElderTaskContext):
        """Elder評議会への通知"""
        council_message = f"""
{ELDER_RESULT_EMOJI['council']} **ELDER COUNCIL NOTIFICATION**

**Critical Error Detected**
Task ID: {message.get('task_id')}
Error Type: {message.get('error_type')}
Reported by: {elder_context.user.username} ({elder_context.user.elder_role.value})

Immediate attention required.
"""
        
        # Grand Elder以上のチャンネルに通知
        if ElderRole.GRAND_ELDER in self.elder_channels:
            council_channel = self.elder_channels[ElderRole.GRAND_ELDER].get(
                'emergency', '#elder-council'
            )
            
            await self.slack_notifier.send_message(
                council_message,
                channel=council_channel
            )
    
    async def _cache_failed_notification_elder(self, task_id: str, main_message: str,
                                             detail_message: str, channel: str,
                                             elder_context: ElderTaskContext):
        """Elder情報付き失敗通知キャッシュ"""
        failed_notification = {
            'task_id': task_id,
            'main_message': main_message,
            'detail_message': detail_message,
            'channel': channel,
            'elder_role': elder_context.user.elder_role.value,
            'timestamp': datetime.utcnow().isoformat(),
            'retry_count': 0
        }
        
        await self.cache_manager.set(
            f"failed_notification:{task_id}",
            failed_notification,
            ttl=86400
        )
    
    async def _update_elder_stats(self):
        """Elder階層統計情報の更新と永続化"""
        now = datetime.utcnow()
        if (now - self.elder_stats['last_reset']).total_seconds() >= 3600:
            await self._save_elder_stats()
            
            # Redisにも保存（実装がある場合）
            try:
                await self.cache_manager.set(
                    "elder_result_worker_stats",
                    self.elder_stats,
                    ttl=86400
                )
            except:
                pass  # Redis未実装の場合はスキップ
    
    async def _save_elder_stats(self):
        """Elder階層統計情報をファイルに保存"""
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
                **self.elder_stats,
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
            for role in self.elder_stats['by_role']:
                self.elder_stats['by_role'][role] = {
                    'messages_processed': 0,
                    'notifications_sent': 0,
                    'notifications_failed': 0,
                    'messages_split': 0
                }
            for priority in self.elder_stats['by_priority']:
                self.elder_stats['by_priority'][priority] = 0
            self.elder_stats['security_events'] = 0
            self.elder_stats['last_reset'] = datetime.utcnow()
            
        except Exception as e:
            self.logger.error("Failed to save Elder statistics", error=str(e))
    
    async def get_elder_statistics(self) -> Dict[str, Any]:
        """Elder階層統計情報の取得"""
        return {
            'current': self.elder_stats,
            'file_path': str(self.stats_file),
            'elder_distribution': {
                role: stats['messages_processed']
                for role, stats in self.elder_stats['by_role'].items()
            },
            'priority_distribution': self.elder_stats['by_priority'],
            'security_events': self.elder_stats['security_events']
        }
    
    @elder_worker_required(ElderRole.CLAUDE_ELDER)
    async def generate_elder_report(self, elder_context: ElderTaskContext) -> Dict[str, Any]:
        """Elder階層レポート生成（Claude Elder以上）"""
        stats = await self.get_elder_statistics()
        
        # レポート生成
        report = f"""
{ELDER_RESULT_EMOJI['stats']} **Elder Result Worker Report**

**Performance by Elder Role:**
"""
        for role, role_stats in stats['current']['by_role'].items():
            if role_stats['messages_processed'] > 0:
                success_rate = (role_stats['notifications_sent'] / 
                              role_stats['messages_processed']) * 100
                report += f"\n{self._get_elder_badge(role)} **{role.upper()}**"
                report += f"\n  • Processed: {role_stats['messages_processed']}"
                report += f"\n  • Success Rate: {success_rate:.1f}%"
                report += f"\n  • Failed: {role_stats['notifications_failed']}"
        
        report += f"\n\n**Priority Distribution:**"
        for priority, count in stats['priority_distribution'].items():
            if count > 0:
                report += f"\n  • {self._get_priority_icon(priority)} {priority.upper()}: {count}"
        
        report += f"\n\n**Security Events:** {stats['security_events']}"
        report += f"\n\n*Report generated by {elder_context.user.username}*"
        
        # レポート送信
        channel = self.elder_channels[elder_context.user.elder_role].get(
            'default', '#reports'
        )
        
        await self.slack_notifier.send_message(report, channel=channel)
        
        return {
            'report_generated': True,
            'timestamp': datetime.now().isoformat(),
            'generated_by': elder_context.user.username
        }


# Elder階層ファクトリー関数
def create_elder_async_result_worker(auth_provider: Optional[UnifiedAuthProvider] = None,
                                   config: Optional[Dict[str, Any]] = None) -> ElderAsyncResultWorker:
    """Elder階層非同期結果ワーカー作成"""
    return ElderAsyncResultWorker(auth_provider=auth_provider, config=config)


# デモ実行関数
async def demo_elder_async_result():
    """Elder階層非同期結果ワーカーのデモ実行"""
    from libs.unified_auth_provider import create_demo_auth_system, AuthRequest
    
    print(f"{ELDER_RESULT_EMOJI['start']} Elder Async Result Worker Demo Starting...")
    
    # デモ認証システム
    auth = create_demo_auth_system()
    
    # 結果ワーカー作成
    worker = create_elder_async_result_worker(auth_provider=auth)
    
    # Claude Elderとして認証
    auth_request = AuthRequest(username="claude_elder", password="claude_password")
    result, session, user = auth.authenticate(auth_request)
    
    if result.value == "success":
        print(f"{ELDER_RESULT_EMOJI['success']} Authenticated as Claude Elder: {user.username}")
        
        # 結果処理コンテキスト作成
        context = worker.create_elder_context(
            user=user,
            session=session,
            task_id="demo_result_001",
            priority=ElderTaskPriority.HIGH
        )
        
        # デモ結果メッセージ（成功）
        demo_success_message = {
            "task_id": "elder_task_001",
            "status": "completed",
            "duration": 45.2,
            "result": "Successfully created Elder-integrated worker system",
            "files_created": [
                "/workers/elder_task_worker.py",
                "/workers/elder_pm_worker.py",
                "/tests/test_elder_integration.py"
            ],
            "elder_context": {
                "processed_by": "task_sage",
                "elder_role": "sage",
                "priority": "high"
            }
        }
        
        print(f"\n{ELDER_RESULT_EMOJI['notify']} Processing success notification...")
        async def demo_success_task():
            return await worker.process_elder_result_message(context, demo_success_message)
        
        success_result = await worker.execute_with_elder_context(context, demo_success_task)
        print(f"  Status: {success_result.status}")
        
        # デモ結果メッセージ（エラー）
        demo_error_message = {
            "task_id": "elder_task_002",
            "status": "failed",
            "duration": 12.5,
            "error": "SecurityError: Unauthorized access attempt",
            "error_type": "SecurityError",
            "stack_trace": "Traceback...",
            "elder_context": {
                "processed_by": "servant1",
                "elder_role": "servant",
                "priority": "critical"
            }
        }
        
        print(f"\n{ELDER_RESULT_EMOJI['notify']} Processing error notification...")
        async def demo_error_task():
            return await worker.process_elder_result_message(context, demo_error_message)
        
        error_result = await worker.execute_with_elder_context(context, demo_error_task)
        print(f"  Status: {error_result.status}")
        
        # 統計情報表示
        stats = await worker.get_elder_statistics()
        print(f"\n{ELDER_RESULT_EMOJI['stats']} Elder Statistics:")
        print(f"  By Role: {stats['elder_distribution']}")
        print(f"  By Priority: {stats['priority_distribution']}")
        print(f"  Security Events: {stats['security_events']}")
        
        # レポート生成
        print(f"\n{ELDER_RESULT_EMOJI['report']} Generating Elder report...")
        report_result = await worker.generate_elder_report(context)
        print(f"  Report generated: {report_result['report_generated']}")
        
    else:
        print(f"{ELDER_RESULT_EMOJI['error']} Authentication failed: {result}")


if __name__ == "__main__":
    # デモ実行
    import asyncio
    asyncio.run(demo_elder_async_result())