#!/usr/bin/env python3
"""
Elder階層統合 Enhanced PM Worker v2.0
AI Company Elder Hierarchy Integrated Project Management

エルダーズ評議会承認済み統合認証対応プロジェクトマネジメントワーカー
"""

import sys
from pathlib import Path
import json
import shutil
import asyncio
from datetime import datetime
import time
from typing import Dict, List, Optional, Any

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
from core import BaseWorker, get_config, EMOJI, ErrorSeverity, with_error_handling
from core.worker_communication import CommunicationMixin
from libs.self_evolution_manager import SelfEvolutionManager
from libs.github_flow_manager import GitHubFlowManager
from libs.project_design_manager import ProjectDesignManager
from libs.slack_notifier import SlackNotifier
from libs.ai_command_helper import AICommandHelper
from libs.knowledge_base_manager import KnowledgeAwareMixin
from libs.quality_checker import QualityChecker
from libs.pm_elder_integration import PMElderIntegration

# Elder階層専用絵文字
ELDER_EMOJI = {
    **EMOJI,
    'council': '🏛️',
    'sage': '🧙‍♂️',
    'crown': '👑',
    'shield': '🛡️',
    'elder': '⚡',
    'approval': '✅',
    'authority': '🔱',
    'hierarchy': '🏰'
}


class ElderEnhancedPMWorker(ElderAwareBaseWorker, CommunicationMixin, KnowledgeAwareMixin):
    """
    Elder階層統合プロジェクトマネジメントワーカー
    
    Elder階層システムと統合認証に対応したプロジェクト管理システム
    """
    
    def __init__(self, worker_id: Optional[str] = None,
                 auth_provider: Optional[UnifiedAuthProvider] = None):
        # Elder階層BaseWorker初期化
        ElderAwareBaseWorker.__init__(
            self,
            auth_provider=auth_provider,
            required_elder_role=ElderRole.SAGE,
            required_sage_type=SageType.TASK  # プロジェクト管理はタスク賢者の専門領域
        )
        
        # 従来のミックスイン初期化
        CommunicationMixin.__init__(self)
        KnowledgeAwareMixin.__init__(self)
        
        # ワーカー設定
        self.worker_type = 'pm'
        self.worker_id = worker_id or f"elder_pm_worker_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Elder階層対応キュー設定
        self.input_queue = 'ai_pm_elder'
        self.output_queue = 'ai_results_elder'
        
        self.setup_communication()
        self.output_dir = PROJECT_ROOT / "output"
        
        # Elder階層統合管理システム
        self.elder_pm_integration = PMElderIntegration()
        
        # プロジェクト管理システム
        self.evolution_manager = SelfEvolutionManager()
        self.git_manager = GitHubFlowManager()
        self.project_manager = ProjectDesignManager()
        self.slack = SlackNotifier()
        self.ai_helper = AICommandHelper()
        self.config = get_config()
        
        # Elder階層権限別機能設定
        self.elder_pm_features = self._configure_elder_pm_features()
        
        # 品質管理機能統合
        try:
            self.quality_checker = QualityChecker()
        except Exception as e:
            self.logger.warning(f"QualityChecker initialization failed: {e}")
            self.quality_checker = None
        
        # SE-Tester連携設定
        self.se_testing_enabled = self.config.get('pm.se_testing_enabled', True)
        
        self.logger.info(f"{ELDER_EMOJI['council']} Elder Enhanced PM Worker initialized - Required: {self.required_elder_role.value}")
    
    def _configure_elder_pm_features(self) -> Dict[ElderRole, Dict[str, bool]]:
        """Elder階層別PM機能設定"""
        return {
            ElderRole.SERVANT: {
                'view_projects': True,
                'create_tasks': True,
                'update_status': True,
                'delete_projects': False,
                'deploy_production': False,
                'emergency_override': False,
                'council_integration': False
            },
            ElderRole.SAGE: {
                'view_projects': True,
                'create_tasks': True,
                'update_status': True,
                'delete_projects': True,
                'deploy_production': False,
                'emergency_override': False,
                'council_integration': True,
                'sage_coordination': True
            },
            ElderRole.CLAUDE_ELDER: {
                'view_projects': True,
                'create_tasks': True,
                'update_status': True,
                'delete_projects': True,
                'deploy_production': True,
                'emergency_override': False,
                'council_integration': True,
                'sage_coordination': True,
                'development_control': True
            },
            ElderRole.GRAND_ELDER: {
                'view_projects': True,
                'create_tasks': True,
                'update_status': True,
                'delete_projects': True,
                'deploy_production': True,
                'emergency_override': True,
                'council_integration': True,
                'sage_coordination': True,
                'development_control': True,
                'system_override': True
            }
        }
    
    def get_elder_pm_permissions(self, user: User) -> Dict[str, bool]:
        """ユーザーのElder階層PM権限取得"""
        return self.elder_pm_features.get(user.elder_role, self.elder_pm_features[ElderRole.SERVANT])
    
    async def process_elder_pm_message(self, elder_context: ElderTaskContext, 
                                     pm_data: Dict[str, Any]) -> ElderTaskResult:
        """Elder階層認証済みPMメッセージ処理"""
        project_id = pm_data.get('project_id', 'unknown')
        pm_action = pm_data.get('action', 'general')
        
        # Elder階層ログ
        self.audit_logger.log_elder_action(
            elder_context,
            f"pm_action_start",
            f"PM Action: {pm_action} on Project: {project_id}"
        )
        
        try:
            # Elder階層別PM処理
            if elder_context.execution_mode == WorkerExecutionMode.GRAND_ELDER:
                result = await self._process_grand_elder_pm(elder_context, pm_data)
            elif elder_context.execution_mode == WorkerExecutionMode.CLAUDE_ELDER:
                result = await self._process_claude_elder_pm(elder_context, pm_data)
            elif elder_context.execution_mode == WorkerExecutionMode.SAGE_MODE:
                result = await self._process_sage_pm(elder_context, pm_data)
            else:
                result = await self._process_servant_pm(elder_context, pm_data)
            
            # 成功ログ
            self.audit_logger.log_elder_action(
                elder_context,
                f"pm_action_complete",
                f"PM Action {pm_action} completed successfully"
            )
            
            return result
            
        except Exception as e:
            # エラーログ
            self.audit_logger.log_elder_action(
                elder_context,
                f"pm_action_error",
                f"PM Action {pm_action} failed: {str(e)}"
            )
            
            self.audit_logger.log_security_event(
                elder_context,
                "pm_execution_error",
                {"project_id": project_id, "action": pm_action, "error": str(e)}
            )
            
            raise
    
    @elder_worker_required(ElderRole.GRAND_ELDER)
    async def _process_grand_elder_pm(self, context: ElderTaskContext, pm_data: Dict) -> Dict:
        """🌟 グランドエルダー専用PM処理"""
        self.logger.info(f"{ELDER_EMOJI['crown']} Processing Grand Elder PM: {pm_data.get('action')}")
        
        action = pm_data.get('action', 'general')
        
        if action == 'emergency_project_override':
            return await self._handle_emergency_project_override(context, pm_data)
        elif action == 'council_decision_implementation':
            return await self._implement_council_decision(context, pm_data)
        elif action == 'system_wide_deployment':
            return await self._execute_system_wide_deployment(context, pm_data)
        elif action == 'crisis_management':
            return await self._handle_project_crisis(context, pm_data)
        else:
            # 通常のPMタスクも最高権限で実行
            return await self._execute_enhanced_pm_task(context, pm_data)
    
    @elder_worker_required(ElderRole.CLAUDE_ELDER)
    async def _process_claude_elder_pm(self, context: ElderTaskContext, pm_data: Dict) -> Dict:
        """🤖 クロードエルダー専用PM処理"""
        self.logger.info(f"{ELDER_EMOJI['elder']} Processing Claude Elder PM: {pm_data.get('action')}")
        
        action = pm_data.get('action', 'general')
        
        if action == 'development_coordination':
            return await self._coordinate_development_teams(context, pm_data)
        elif action == 'sage_task_delegation':
            return await self._delegate_to_sages(context, pm_data)
        elif action == 'production_deployment':
            return await self._handle_production_deployment(context, pm_data)
        elif action == 'quality_assurance':
            return await self._execute_quality_assurance(context, pm_data)
        else:
            return await self._execute_enhanced_pm_task(context, pm_data)
    
    @elder_worker_required(ElderRole.SAGE, SageType.TASK)
    async def _process_sage_pm(self, context: ElderTaskContext, pm_data: Dict) -> Dict:
        """🧙‍♂️ タスク賢者専用PM処理"""
        self.logger.info(f"{ELDER_EMOJI['sage']} Processing Sage PM: {pm_data.get('action')}")
        
        action = pm_data.get('action', 'general')
        
        if action == 'project_lifecycle_management':
            return await self._manage_project_lifecycle(context, pm_data)
        elif action == 'resource_optimization':
            return await self._optimize_project_resources(context, pm_data)
        elif action == 'stakeholder_coordination':
            return await self._coordinate_stakeholders(context, pm_data)
        elif action == 'quality_monitoring':
            return await self._monitor_project_quality(context, pm_data)
        else:
            return await self._execute_standard_pm_task(context, pm_data)
    
    async def _process_servant_pm(self, context: ElderTaskContext, pm_data: Dict) -> Dict:
        """🧝‍♂️ サーバント用制限付きPM処理"""
        self.logger.info(f"{ELDER_EMOJI['info']} Processing Servant PM: {pm_data.get('action')}")
        
        # 権限チェック
        permissions = self.get_elder_pm_permissions(context.user)
        action = pm_data.get('action', 'general')
        
        # 制限された操作のチェック
        if action == 'delete_project' and not permissions['delete_projects']:
            raise PermissionError("Insufficient permissions to delete projects")
        
        if action == 'deploy_production' and not permissions['deploy_production']:
            raise PermissionError("Insufficient permissions for production deployment")
        
        # 基本PM操作のみ許可
        if action in ['view_projects', 'create_tasks', 'update_status']:
            return await self._execute_basic_pm_task(context, pm_data)
        else:
            raise PermissionError(f"Action '{action}' not permitted for Servant role")
    
    async def _handle_emergency_project_override(self, context: ElderTaskContext, pm_data: Dict) -> Dict:
        """緊急プロジェクトオーバーライド処理"""
        emergency_type = pm_data.get('emergency_type', 'general')
        project_id = pm_data.get('project_id', 'unknown')
        
        self.audit_logger.log_security_event(
            context,
            "emergency_project_override",
            {
                "emergency_type": emergency_type,
                "project_id": project_id,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # 緊急時プロジェクト制御
        if emergency_type == 'security_incident':
            return await self._handle_security_incident_project(context, pm_data)
        elif emergency_type == 'critical_bug':
            return await self._handle_critical_bug_project(context, pm_data)
        elif emergency_type == 'system_failure':
            return await self._handle_system_failure_project(context, pm_data)
        else:
            return await self._handle_general_emergency_project(context, pm_data)
    
    async def _implement_council_decision(self, context: ElderTaskContext, pm_data: Dict) -> Dict:
        """エルダーズ評議会決定事項実装"""
        decision_data = pm_data.get('council_decision', {})
        decision_type = decision_data.get('type', 'general')
        
        self.audit_logger.log_elder_action(
            context,
            "council_decision_implementation",
            f"Implementing council decision: {decision_type}"
        )
        
        # 評議会決定の実装
        if decision_type == 'architecture_change':
            return await self._implement_architecture_change(context, decision_data)
        elif decision_type == 'process_improvement':
            return await self._implement_process_improvement(context, decision_data)
        elif decision_type == 'resource_reallocation':
            return await self._implement_resource_reallocation(context, decision_data)
        else:
            return await self._implement_general_decision(context, decision_data)
    
    async def _coordinate_development_teams(self, context: ElderTaskContext, pm_data: Dict) -> Dict:
        """開発チーム調整"""
        coordination_type = pm_data.get('coordination_type', 'general')
        teams = pm_data.get('teams', [])
        
        coordination_result = {
            "coordination_type": coordination_type,
            "teams_involved": teams,
            "coordinator": context.user.username,
            "timestamp": datetime.now().isoformat(),
            "status": "coordinated"
        }
        
        # 4賢者への指示配信
        if coordination_type == 'sage_coordination':
            await self._distribute_sage_instructions(context, pm_data)
        
        return coordination_result
    
    async def _delegate_to_sages(self, context: ElderTaskContext, pm_data: Dict) -> Dict:
        """賢者への委任"""
        delegation_data = pm_data.get('delegation', {})
        target_sages = delegation_data.get('target_sages', [])
        
        self.audit_logger.log_elder_action(
            context,
            "sage_delegation",
            f"Delegating to sages: {', '.join(target_sages)}"
        )
        
        delegation_results = []
        for sage_type in target_sages:
            sage_result = await self._delegate_to_specific_sage(context, sage_type, delegation_data)
            delegation_results.append(sage_result)
        
        return {
            "delegation_status": "completed",
            "target_sages": target_sages,
            "results": delegation_results,
            "delegated_by": context.user.username,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _manage_project_lifecycle(self, context: ElderTaskContext, pm_data: Dict) -> Dict:
        """プロジェクトライフサイクル管理"""
        project_id = pm_data.get('project_id', 'unknown')
        lifecycle_phase = pm_data.get('phase', 'planning')
        
        lifecycle_actions = {
            'planning': self._execute_planning_phase,
            'design': self._execute_design_phase,
            'development': self._execute_development_phase,
            'testing': self._execute_testing_phase,
            'deployment': self._execute_deployment_phase,
            'maintenance': self._execute_maintenance_phase
        }
        
        if lifecycle_phase in lifecycle_actions:
            return await lifecycle_actions[lifecycle_phase](context, pm_data)
        else:
            raise ValueError(f"Unknown lifecycle phase: {lifecycle_phase}")
    
    async def _execute_enhanced_pm_task(self, context: ElderTaskContext, pm_data: Dict) -> Dict:
        """拡張PM タスク実行（Elder階層対応）"""
        action = pm_data.get('action', 'general')
        project_id = pm_data.get('project_id', 'unknown')
        
        # Elder階層に応じた処理強化
        enhanced_result = {
            "action": action,
            "project_id": project_id,
            "elder_mode": context.execution_mode.value,
            "permissions": context.permissions,
            "execution_time": datetime.now().isoformat(),
            "executed_by": context.user.username,
            "elder_role": context.user.elder_role.value
        }
        
        # 実際のPM処理をここに実装
        if action == 'project_status_update':
            enhanced_result["status_update"] = await self._update_project_status(context, pm_data)
        elif action == 'resource_allocation':
            enhanced_result["resource_allocation"] = await self._allocate_resources(context, pm_data)
        elif action == 'quality_check':
            enhanced_result["quality_check"] = await self._perform_quality_check(context, pm_data)
        
        return enhanced_result
    
    async def _update_project_status(self, context: ElderTaskContext, pm_data: Dict) -> Dict:
        """プロジェクトステータス更新"""
        project_id = pm_data.get('project_id', 'unknown')
        new_status = pm_data.get('status', 'unknown')
        
        # Elder階層に応じた更新権限チェック
        permissions = self.get_elder_pm_permissions(context.user)
        
        if not permissions['update_status']:
            raise PermissionError("Insufficient permissions to update project status")
        
        status_update = {
            "project_id": project_id,
            "previous_status": "in_progress",  # 実際の実装では DB から取得
            "new_status": new_status,
            "updated_by": context.user.username,
            "update_time": datetime.now().isoformat(),
            "elder_authority": context.user.elder_role.value
        }
        
        # Slack通知（Elder階層情報付き）
        await self._send_elder_slack_notification(context, f"Project {project_id} status updated to {new_status}")
        
        return status_update
    
    async def _send_elder_slack_notification(self, context: ElderTaskContext, message: str):
        """Elder階層情報付きSlack通知"""
        elder_info = f"[{context.user.elder_role.value.upper()}] {context.user.username}"
        enhanced_message = f"{ELDER_EMOJI['hierarchy']} {elder_info}: {message}"
        
        # Slack通知の実装
        try:
            await self.slack.send_message(enhanced_message)
        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {e}")
    
    async def _distribute_sage_instructions(self, context: ElderTaskContext, pm_data: Dict):
        """賢者への指示配信"""
        instructions = pm_data.get('sage_instructions', {})
        
        for sage_type, instruction in instructions.items():
            self.audit_logger.log_elder_action(
                context,
                f"sage_instruction_sent",
                f"Instruction sent to {sage_type}: {instruction[:100]}..."
            )
            
            # 実際の賢者への指示配信をここに実装
            # RabbitMQ メッセージングやAPI呼び出し等


# Elder階層PMワーカーファクトリー
def create_elder_pm_worker(elder_role: ElderRole = ElderRole.SAGE,
                          sage_type: Optional[SageType] = SageType.TASK,
                          auth_provider: Optional[UnifiedAuthProvider] = None) -> ElderEnhancedPMWorker:
    """Elder階層PMワーカー作成"""
    worker = ElderEnhancedPMWorker(auth_provider=auth_provider)
    worker.required_elder_role = elder_role
    worker.required_sage_type = sage_type
    
    return worker


# デモ実行関数
async def demo_elder_pm_execution():
    """Elder階層PMワーカーのデモ実行"""
    from libs.unified_auth_provider import create_demo_auth_system, AuthRequest
    
    print(f"{ELDER_EMOJI['start']} Elder PM Worker Demo Starting...")
    
    # デモ認証システム
    auth = create_demo_auth_system()
    
    # PMワーカー作成
    worker = create_elder_pm_worker(
        elder_role=ElderRole.SAGE,
        sage_type=SageType.TASK,
        auth_provider=auth
    )
    
    # タスク賢者として認証
    auth_request = AuthRequest(username="task_sage", password="task_password")
    result, session, user = auth.authenticate(auth_request)
    
    if result.value == "success":
        print(f"{ELDER_EMOJI['success']} Authenticated as Task Sage: {user.username}")
        
        # PMコンテキスト作成
        context = worker.create_elder_context(
            user=user,
            session=session,
            task_id="demo_elder_pm_001",
            priority=ElderTaskPriority.HIGH
        )
        
        # デモPMデータ
        demo_pm_data = {
            "project_id": "ai_company_v2",
            "action": "project_lifecycle_management",
            "phase": "development",
            "stakeholders": ["development_team", "qa_team", "design_team"],
            "priority": "high"
        }
        
        # Elder階層PM実行
        async def demo_pm_task():
            return await worker.process_elder_pm_message(context, demo_pm_data)
        
        result = await worker.execute_with_elder_context(context, demo_pm_task)
        
        print(f"{ELDER_EMOJI['complete']} Demo PM Result:")
        print(f"  Status: {result.status}")
        print(f"  Execution Mode: {result.elder_context.execution_mode.value}")
        print(f"  PM Permissions: {worker.get_elder_pm_permissions(user)}")
        print(f"  Execution Time: {result.execution_time:.2f}s")
        print(f"  Audit Events: {len(result.audit_log['events'])}")
        
    else:
        print(f"{ELDER_EMOJI['error']} Authentication failed: {result}")


if __name__ == "__main__":
    # デモ実行
    asyncio.run(demo_elder_pm_execution())