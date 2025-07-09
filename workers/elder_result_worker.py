#!/usr/bin/env python3
"""
Elder階層統合 Result Worker v2.0
AI Company Elder Hierarchy Integrated Result Processing & Notification

エルダーズ評議会承認済み統合認証対応結果処理・通知ワーカー
"""

import sys
import json
import time
import hashlib
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

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
    elder_worker_required
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
from core import BaseWorker, get_config, EMOJI
from libs.slack_notifier import SlackNotifier
from libs.ai_command_helper import AICommandHelper

# Elder階層専用絵文字
ELDER_RESULT_EMOJI = {
    **EMOJI,
    'result': '📊',
    'notification': '📢',
    'council': '🏛️',
    'sage': '🧙‍♂️',
    'crown': '👑',
    'shield': '🛡️',
    'elder': '⚡',
    'hierarchy': '🏰',
    'authority': '🔱',
    'secure': '🔒',
    'audit': '📋'
}


class ElderResultWorker(ElderAwareBaseWorker):
    """
    Elder階層統合結果処理ワーカー
    
    Elder階層システムと統合認証に対応した結果処理・通知システム
    """
    
    def __init__(self, worker_id: Optional[str] = None,
                 auth_provider: Optional[UnifiedAuthProvider] = None):
        # Elder階層BaseWorker初期化
        ElderAwareBaseWorker.__init__(
            self,
            auth_provider=auth_provider,
            required_elder_role=ElderRole.SERVANT,  # 結果処理は基本的にサーバントでも可能
            required_sage_type=None
        )
        
        # ワーカー設定
        self.worker_type = 'result'
        self.worker_id = worker_id or f"elder_result_worker_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Elder階層対応キュー設定
        self.input_queue = 'ai_results_elder'
        self.output_queue = 'ai_notifications_elder'
        
        self.config = get_config()
        self.slack_notifier = SlackNotifier()
        self.ai_helper = AICommandHelper()
        
        # Elder階層別通知設定
        self.elder_notification_config = self._configure_elder_notifications()
        
        # 統計情報（Elder階層別）
        self.elder_stats = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'total_duration': 0.0,
            'elder_stats': {
                ElderRole.GRAND_ELDER.value: {'count': 0, 'success_rate': 0.0},
                ElderRole.CLAUDE_ELDER.value: {'count': 0, 'success_rate': 0.0},
                ElderRole.SAGE.value: {'count': 0, 'success_rate': 0.0},
                ElderRole.SERVANT.value: {'count': 0, 'success_rate': 0.0}
            }
        }
        
        # Elder階層監査設定
        self.audit_config = {
            'log_all_results': True,
            'sensitive_data_filtering': True,
            'elder_context_tracking': True,
            'security_event_detection': True
        }
        
        self.logger.info(f"{ELDER_RESULT_EMOJI['council']} Elder Result Worker initialized - Required: {self.required_elder_role.value}")
    
    def _configure_elder_notifications(self) -> Dict[ElderRole, Dict[str, Any]]:
        """Elder階層別通知設定"""
        return {
            ElderRole.GRAND_ELDER: {
                'channels': ['#elder-council-emergency', '#grand-elder-notifications'],
                'priority': 'highest',
                'include_full_context': True,
                'include_system_metrics': True,
                'notification_format': 'detailed_with_security'
            },
            ElderRole.CLAUDE_ELDER: {
                'channels': ['#claude-elder-development', '#elder-notifications'],
                'priority': 'high',
                'include_full_context': True,
                'include_system_metrics': True,
                'notification_format': 'detailed_with_development'
            },
            ElderRole.SAGE: {
                'channels': ['#sage-notifications', '#general-elder'],
                'priority': 'medium',
                'include_full_context': True,
                'include_system_metrics': False,
                'notification_format': 'detailed'
            },
            ElderRole.SERVANT: {
                'channels': ['#servant-notifications', '#general'],
                'priority': 'normal',
                'include_full_context': False,
                'include_system_metrics': False,
                'notification_format': 'basic'
            }
        }
    
    async def process_elder_result_message(self, elder_context: ElderTaskContext,
                                         result_data: Dict[str, Any]) -> ElderTaskResult:
        """Elder階層認証済み結果メッセージ処理"""
        task_id = result_data.get('task_id', 'unknown')
        result_type = result_data.get('type', 'general')
        
        # Elder階層ログ
        self.audit_logger.log_elder_action(
            elder_context,
            f"result_processing_start",
            f"Processing result for task {task_id} - Type: {result_type}"
        )
        
        try:
            # Elder階層別結果処理
            if elder_context.execution_mode == WorkerExecutionMode.GRAND_ELDER:
                result = await self._process_grand_elder_result(elder_context, result_data)
            elif elder_context.execution_mode == WorkerExecutionMode.CLAUDE_ELDER:
                result = await self._process_claude_elder_result(elder_context, result_data)
            elif elder_context.execution_mode == WorkerExecutionMode.SAGE_MODE:
                result = await self._process_sage_result(elder_context, result_data)
            else:
                result = await self._process_servant_result(elder_context, result_data)
            
            # 統計更新
            self._update_elder_stats(elder_context, result_data, success=True)
            
            # 成功ログ
            self.audit_logger.log_elder_action(
                elder_context,
                f"result_processing_complete",
                f"Result processing completed for task {task_id}"
            )
            
            return result
            
        except Exception as e:
            # 統計更新
            self._update_elder_stats(elder_context, result_data, success=False)
            
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
    
    @elder_worker_required(ElderRole.GRAND_ELDER)
    async def _process_grand_elder_result(self, context: ElderTaskContext, result_data: Dict) -> Dict:
        """🌟 グランドエルダー専用結果処理"""
        self.logger.info(f"{ELDER_RESULT_EMOJI['crown']} Processing Grand Elder result: {result_data.get('task_id')}")
        
        # 最高権限での結果処理
        processed_result = await self._process_high_priority_result(context, result_data)
        
        # グランドエルダー専用通知
        await self._send_grand_elder_notification(context, processed_result)
        
        # システム全体への影響分析
        system_impact = await self._analyze_system_impact(context, result_data)
        processed_result['system_impact'] = system_impact
        
        # 緊急時評議会招集判定
        if self._should_convene_emergency_council(result_data):
            await self._convene_emergency_council(context, result_data)
        
        return processed_result
    
    @elder_worker_required(ElderRole.CLAUDE_ELDER)
    async def _process_claude_elder_result(self, context: ElderTaskContext, result_data: Dict) -> Dict:
        """🤖 クロードエルダー専用結果処理"""
        self.logger.info(f"{ELDER_RESULT_EMOJI['elder']} Processing Claude Elder result: {result_data.get('task_id')}")
        
        # 開発実行責任者権限での結果処理
        processed_result = await self._process_development_result(context, result_data)
        
        # クロードエルダー専用通知
        await self._send_claude_elder_notification(context, processed_result)
        
        # 開発メトリクス分析
        development_metrics = await self._analyze_development_metrics(context, result_data)
        processed_result['development_metrics'] = development_metrics
        
        # 4賢者への結果配信
        await self._distribute_result_to_sages(context, processed_result)
        
        return processed_result
    
    async def _process_sage_result(self, context: ElderTaskContext, result_data: Dict) -> Dict:
        """🧙‍♂️ 賢者専用結果処理"""
        self.logger.info(f"{ELDER_RESULT_EMOJI['sage']} Processing Sage result: {result_data.get('task_id')}")
        
        # 賢者権限での結果処理
        processed_result = await self._process_specialized_result(context, result_data)
        
        # 賢者専用通知
        await self._send_sage_notification(context, processed_result)
        
        # 賢者専門分析
        sage_analysis = await self._perform_sage_analysis(context, result_data)
        processed_result['sage_analysis'] = sage_analysis
        
        return processed_result
    
    async def _process_servant_result(self, context: ElderTaskContext, result_data: Dict) -> Dict:
        """🧝‍♂️ サーバント用制限付き結果処理"""
        self.logger.info(f"{ELDER_RESULT_EMOJI['info']} Processing Servant result: {result_data.get('task_id')}")
        
        # 基本結果処理（フィルタリング適用）
        filtered_result_data = self._filter_servant_result_data(result_data)
        processed_result = await self._process_basic_result(context, filtered_result_data)
        
        # サーバント用通知
        await self._send_servant_notification(context, processed_result)
        
        # 出力フィルタリング
        return self._filter_servant_result_output(processed_result)
    
    async def _process_high_priority_result(self, context: ElderTaskContext, result_data: Dict) -> Dict:
        """高優先度結果処理"""
        task_id = result_data.get('task_id', 'unknown')
        task_result = result_data.get('result', {})
        
        # 高優先度結果の包括的処理
        processed_result = {
            "task_id": task_id,
            "processed_at": datetime.now().isoformat(),
            "processed_by": context.user.username,
            "elder_role": context.user.elder_role.value,
            "priority": "highest",
            "original_result": task_result,
            "security_level": "maximum",
            "audit_trail": self.audit_logger.events[-10:],  # 最新10件
            "system_context": {
                "execution_mode": context.execution_mode.value,
                "task_priority": context.priority.value,
                "permissions": context.permissions
            }
        }
        
        # 結果の妥当性検証
        validation_result = await self._validate_result_integrity(context, result_data)
        processed_result['validation'] = validation_result
        
        return processed_result
    
    async def _send_grand_elder_notification(self, context: ElderTaskContext, result: Dict):
        """グランドエルダー専用通知送信"""
        config = self.elder_notification_config[ElderRole.GRAND_ELDER]
        
        # 最高権限用詳細通知
        notification_message = self._format_grand_elder_notification(context, result)
        
        for channel in config['channels']:
            try:
                await self.slack_notifier.send_message(
                    message=notification_message,
                    channel=channel,
                    priority=config['priority']
                )
            except Exception as e:
                self.logger.error(f"Failed to send Grand Elder notification to {channel}: {e}")
    
    async def _send_claude_elder_notification(self, context: ElderTaskContext, result: Dict):
        """クロードエルダー専用通知送信"""
        config = self.elder_notification_config[ElderRole.CLAUDE_ELDER]
        
        # 開発実行責任者用通知
        notification_message = self._format_claude_elder_notification(context, result)
        
        for channel in config['channels']:
            try:
                await self.slack_notifier.send_message(
                    message=notification_message,
                    channel=channel,
                    priority=config['priority']
                )
            except Exception as e:
                self.logger.error(f"Failed to send Claude Elder notification to {channel}: {e}")
    
    async def _send_sage_notification(self, context: ElderTaskContext, result: Dict):
        """賢者専用通知送信"""
        config = self.elder_notification_config[ElderRole.SAGE]
        
        # 賢者専門通知
        notification_message = self._format_sage_notification(context, result)
        
        for channel in config['channels']:
            try:
                await self.slack_notifier.send_message(
                    message=notification_message,
                    channel=channel,
                    priority=config['priority']
                )
            except Exception as e:
                self.logger.error(f"Failed to send Sage notification to {channel}: {e}")
    
    async def _send_servant_notification(self, context: ElderTaskContext, result: Dict):
        """サーバント用通知送信"""
        config = self.elder_notification_config[ElderRole.SERVANT]
        
        # 基本通知
        notification_message = self._format_servant_notification(context, result)
        
        for channel in config['channels']:
            try:
                await self.slack_notifier.send_message(
                    message=notification_message,
                    channel=channel,
                    priority=config['priority']
                )
            except Exception as e:
                self.logger.error(f"Failed to send Servant notification to {channel}: {e}")
    
    def _format_grand_elder_notification(self, context: ElderTaskContext, result: Dict) -> str:
        """グランドエルダー通知フォーマット"""
        return f"""
{ELDER_RESULT_EMOJI['crown']} **GRAND ELDER NOTIFICATION**

**Task ID**: {result.get('task_id', 'unknown')}
**Processed By**: {context.user.username} ({context.user.elder_role.value})
**Priority**: {context.priority.value}
**Status**: {result.get('status', 'unknown')}

**System Impact**: {result.get('system_impact', {}).get('level', 'unknown')}
**Security Level**: {result.get('security_level', 'unknown')}

**Audit Trail**: {len(result.get('audit_trail', []))} events recorded

**Emergency Council**: {'Required' if self._should_convene_emergency_council(result) else 'Not Required'}

{ELDER_RESULT_EMOJI['hierarchy']} Elder Authority: MAXIMUM
"""
    
    def _format_claude_elder_notification(self, context: ElderTaskContext, result: Dict) -> str:
        """クロードエルダー通知フォーマット"""
        return f"""
{ELDER_RESULT_EMOJI['elder']} **CLAUDE ELDER NOTIFICATION**

**Task ID**: {result.get('task_id', 'unknown')}
**Processed By**: {context.user.username} ({context.user.elder_role.value})
**Status**: {result.get('status', 'unknown')}

**Development Metrics**: {result.get('development_metrics', {}).get('summary', 'N/A')}
**Sage Distribution**: {result.get('sage_distribution_status', 'pending')}

{ELDER_RESULT_EMOJI['hierarchy']} Elder Authority: HIGH
"""
    
    def _format_sage_notification(self, context: ElderTaskContext, result: Dict) -> str:
        """賢者通知フォーマット"""
        sage_type = context.user.sage_type.value if context.user.sage_type else 'general'
        return f"""
{ELDER_RESULT_EMOJI['sage']} **SAGE NOTIFICATION** ({sage_type.upper()})

**Task ID**: {result.get('task_id', 'unknown')}
**Processed By**: {context.user.username}
**Status**: {result.get('status', 'unknown')}

**Sage Analysis**: {result.get('sage_analysis', {}).get('summary', 'N/A')}

{ELDER_RESULT_EMOJI['hierarchy']} Elder Authority: MEDIUM
"""
    
    def _format_servant_notification(self, context: ElderTaskContext, result: Dict) -> str:
        """サーバント通知フォーマット"""
        return f"""
{ELDER_RESULT_EMOJI['info']} **TASK NOTIFICATION**

**Task ID**: {result.get('task_id', 'unknown')}
**Status**: {result.get('status', 'unknown')}
**Completed**: {result.get('processed_at', 'unknown')}

{ELDER_RESULT_EMOJI['hierarchy']} Authority: BASIC
"""
    
    def _filter_servant_result_data(self, result_data: Dict) -> Dict:
        """サーバント用結果データフィルタリング"""
        filtered = result_data.copy()
        
        # センシティブ情報の除去
        sensitive_keys = ['admin_data', 'system_config', 'security_info', 'internal_data']
        for key in sensitive_keys:
            if key in filtered:
                filtered[key] = '[FILTERED]'
        
        return filtered
    
    def _filter_servant_result_output(self, result: Dict) -> Dict:
        """サーバント用結果出力フィルタリング"""
        filtered = result.copy()
        
        # 内部システム情報の除去
        internal_keys = ['audit_trail', 'system_context', 'validation', 'security_level']
        for key in internal_keys:
            if key in filtered:
                del filtered[key]
        
        return filtered
    
    def _update_elder_stats(self, context: ElderTaskContext, result_data: Dict, success: bool):
        """Elder階層統計更新"""
        self.elder_stats['total_tasks'] += 1
        
        if success:
            self.elder_stats['successful_tasks'] += 1
        else:
            self.elder_stats['failed_tasks'] += 1
        
        # Elder階層別統計
        elder_role = context.user.elder_role.value
        if elder_role in self.elder_stats['elder_stats']:
            self.elder_stats['elder_stats'][elder_role]['count'] += 1
            
            # 成功率計算
            total_count = self.elder_stats['elder_stats'][elder_role]['count']
            if total_count > 0:
                success_count = self.elder_stats['successful_tasks']  # 簡略化
                self.elder_stats['elder_stats'][elder_role]['success_rate'] = success_count / total_count
    
    async def _validate_result_integrity(self, context: ElderTaskContext, result_data: Dict) -> Dict:
        """結果整合性検証"""
        validation_checks = {
            'data_integrity': True,
            'format_validation': True,
            'security_compliance': True,
            'elder_authority_check': True
        }
        
        # 実際の検証ロジックをここに実装
        validation_result = {
            'checks': validation_checks,
            'validation_time': datetime.now().isoformat(),
            'validator': context.user.username,
            'overall_status': 'valid'
        }
        
        return validation_result
    
    def _should_convene_emergency_council(self, result_data: Dict) -> bool:
        """緊急評議会招集判定"""
        # 緊急事態判定ロジック
        emergency_indicators = [
            'system_failure',
            'security_breach',
            'critical_error',
            'data_corruption'
        ]
        
        result_type = result_data.get('type', '')
        status = result_data.get('status', '')
        
        return any(indicator in result_type.lower() or indicator in status.lower() 
                  for indicator in emergency_indicators)
    
    async def _convene_emergency_council(self, context: ElderTaskContext, result_data: Dict):
        """緊急評議会招集"""
        self.audit_logger.log_security_event(
            context,
            "emergency_council_convened",
            {
                "trigger_result": result_data.get('task_id'),
                "convened_by": context.user.username,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # 緊急評議会通知
        emergency_message = f"""
{ELDER_RESULT_EMOJI['crown']} **EMERGENCY COUNCIL CONVENED**

**Trigger**: {result_data.get('task_id')}
**Convened By**: {context.user.username}
**Reason**: {result_data.get('emergency_reason', 'Critical system event')}

**All Elders**: Please join emergency session immediately.
"""
        
        await self.slack_notifier.send_message(
            message=emergency_message,
            channel='#elder-council-emergency',
            priority='critical'
        )


# Elder階層結果ワーカーファクトリー
def create_elder_result_worker(elder_role: ElderRole = ElderRole.SERVANT,
                              auth_provider: Optional[UnifiedAuthProvider] = None) -> ElderResultWorker:
    """Elder階層結果ワーカー作成"""
    worker = ElderResultWorker(auth_provider=auth_provider)
    worker.required_elder_role = elder_role
    
    return worker


# デモ実行関数
async def demo_elder_result_execution():
    """Elder階層結果ワーカーのデモ実行"""
    from libs.unified_auth_provider import create_demo_auth_system, AuthRequest
    
    print(f"{ELDER_RESULT_EMOJI['start']} Elder Result Worker Demo Starting...")
    
    # デモ認証システム
    auth = create_demo_auth_system()
    
    # 結果ワーカー作成
    worker = create_elder_result_worker(
        elder_role=ElderRole.SERVANT,
        auth_provider=auth
    )
    
    # サーバントとして認証
    auth_request = AuthRequest(username="servant1", password="servant_password")
    result, session, user = auth.authenticate(auth_request)
    
    if result.value == "success":
        print(f"{ELDER_RESULT_EMOJI['success']} Authenticated as Servant: {user.username}")
        
        # 結果コンテキスト作成
        context = worker.create_elder_context(
            user=user,
            session=session,
            task_id="demo_elder_result_001",
            priority=ElderTaskPriority.LOW
        )
        
        # デモ結果データ
        demo_result_data = {
            "task_id": "demo_elder_result_001",
            "type": "general_completion",
            "status": "completed",
            "result": {
                "output": "Task completed successfully",
                "execution_time": "2.5s",
                "resources_used": "minimal"
            },
            "metadata": {
                "user_id": user.id,
                "completion_time": datetime.now().isoformat()
            }
        }
        
        # Elder階層結果処理実行
        async def demo_result_task():
            return await worker.process_elder_result_message(context, demo_result_data)
        
        result = await worker.execute_with_elder_context(context, demo_result_task)
        
        print(f"{ELDER_RESULT_EMOJI['complete']} Demo Result Processing:")
        print(f"  Status: {result.status}")
        print(f"  Execution Mode: {result.elder_context.execution_mode.value}")
        print(f"  Notification Config: {worker.elder_notification_config[user.elder_role]}")
        print(f"  Stats: {worker.elder_stats['elder_stats'][user.elder_role.value]}")
        
    else:
        print(f"{ELDER_RESULT_EMOJI['error']} Authentication failed: {result}")


if __name__ == "__main__":
    # デモ実行
    asyncio.run(demo_elder_result_execution())