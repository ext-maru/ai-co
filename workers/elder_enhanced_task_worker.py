#!/usr/bin/env python3
"""
Elder階層統合 Enhanced TaskWorker v2.0
AI Company Elder Hierarchy Integrated Task Processing

エルダーズ評議会承認済み統合認証対応タスクワーカー
"""

import json
import subprocess
import os
import asyncio
from datetime import datetime
from pathlib import Path
import sys
from typing import Dict, Any, Optional

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
from core.base_worker import BaseWorker
from libs.env_config import get_config
from core import ErrorSeverity, with_error_handling
from core import msg
from core.prompt_template_mixin import PromptTemplateMixin
from libs.rag_grimoire_integration import RagGrimoireIntegration, RagGrimoireConfig
from libs.slack_notifier import SlackNotifier
import logging

# 絵文字定義
EMOJI = {
    'start': '🚀',
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'info': 'ℹ️',
    'task': '📋',
    'thinking': '🤔',
    'complete': '🎉',
    'process': '⚙️',
    'robot': '🤖',
    'elder': '🏛️',
    'sage': '🧙‍♂️',
    'crown': '👑',
    'shield': '🛡️'
}


class ElderEnhancedTaskWorker(ElderAwareBaseWorker, PromptTemplateMixin):
    """
    Elder階層統合タスクワーカー
    
    Elder階層システムと統合認証に対応した高度なタスク処理システム
    """
    
    def __init__(self, worker_id: Optional[str] = None, 
                 auth_provider: Optional[UnifiedAuthProvider] = None):
        # Elder階層BaseWorker初期化
        ElderAwareBaseWorker.__init__(
            self,
            auth_provider=auth_provider,
            required_elder_role=ElderRole.SAGE,
            required_sage_type=SageType.TASK
        )
        
        # PromptTemplateMixin初期化
        PromptTemplateMixin.__init__(self)
        
        # BaseWorker設定継承
        self.worker_type = 'task'
        self.worker_id = worker_id or f"elder_task_worker_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # キュー設定
        self.input_queue = 'ai_tasks_elder'
        self.output_queue = 'ai_pm_elder'
        
        self.config = get_config()
        self.output_dir = PROJECT_ROOT / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        # Elder階層専用ツール設定
        self.elder_tools = self._configure_elder_tools()
        
        # 通知設定（Elder階層統合）
        self.slack_notifier = SlackNotifier()
        
        # タスク履歴DB（Elder監査対応）
        try:
            from libs.task_history_db import TaskHistoryDB
            self.task_history_db = TaskHistoryDB()
        except ImportError:
            self.task_history_db = None
        
        # RAG Grimoire Integration（Elder階層拡張）
        self.rag_integration = None
        self.rag_config = RagGrimoireConfig(
            database_url=getattr(self.config, 'GRIMOIRE_DATABASE_URL', 'postgresql://localhost/grimoire'),
            search_threshold=getattr(self.config, 'RAG_SEARCH_THRESHOLD', 0.7),
            max_search_results=getattr(self.config, 'RAG_MAX_RESULTS', 10)
        )
        
        self.logger.info(f"{EMOJI['elder']} Elder Enhanced TaskWorker initialized - Required: {self.required_elder_role.value}")
        
        # RAG統合の非同期初期化
        self._initialize_rag_integration()
    
    def _configure_elder_tools(self) -> Dict[ElderRole, list]:
        """Elder階層別ツール設定"""
        base_tools = [
            'Edit', 'Write', 'Read', 'MultiEdit', 'Glob', 'Grep', 'LS',
            'TodoRead', 'TodoWrite'
        ]
        
        elder_tools = {
            ElderRole.SERVANT: base_tools,
            ElderRole.SAGE: base_tools + [
                'Bash', 'Task', 'WebFetch', 'NotebookRead', 'NotebookEdit'
            ],
            ElderRole.CLAUDE_ELDER: base_tools + [
                'Bash', 'Task', 'WebFetch', 'WebSearch', 
                'NotebookRead', 'NotebookEdit', 'exit_plan_mode'
            ],
            ElderRole.GRAND_ELDER: base_tools + [
                'Bash', 'Task', 'WebFetch', 'WebSearch',
                'NotebookRead', 'NotebookEdit', 'exit_plan_mode',
                'SystemAdmin', 'EmergencyOverride'  # 特別権限
            ]
        }
        
        return elder_tools
    
    def get_allowed_tools_for_user(self, user: User) -> list:
        """ユーザーの Elder階層に基づく許可ツール取得"""
        return self.elder_tools.get(user.elder_role, self.elder_tools[ElderRole.SERVANT])
    
    async def process_elder_message(self, elder_context: ElderTaskContext, task_data: Dict[str, Any]) -> ElderTaskResult:
        """Elder階層認証済みメッセージ処理"""
        task_id = task_data.get('id', 'unknown')
        task_type = task_data.get('type', 'general')
        user_prompt = task_data.get('prompt', '')
        priority = task_data.get('priority', 'normal')
        
        # Elder階層ログ
        self.audit_logger.log_elder_action(
            elder_context, 
            f"task_processing_start",
            f"Task {task_id} - Type: {task_type}"
        )
        
        try:
            # Elder階層別タスク処理
            if elder_context.execution_mode == WorkerExecutionMode.GRAND_ELDER:
                result = await self._process_grand_elder_task(elder_context, task_data)
            elif elder_context.execution_mode == WorkerExecutionMode.CLAUDE_ELDER:
                result = await self._process_claude_elder_task(elder_context, task_data)
            elif elder_context.execution_mode == WorkerExecutionMode.SAGE_MODE:
                result = await self._process_sage_task(elder_context, task_data)
            else:
                result = await self._process_servant_task(elder_context, task_data)
            
            # 成功ログ
            self.audit_logger.log_elder_action(
                elder_context,
                f"task_processing_complete",
                f"Task {task_id} completed successfully"
            )
            
            return result
            
        except Exception as e:
            # エラーログ
            self.audit_logger.log_elder_action(
                elder_context,
                f"task_processing_error",
                f"Task {task_id} failed: {str(e)}"
            )
            
            self.audit_logger.log_security_event(
                elder_context,
                "task_execution_error",
                {"task_id": task_id, "error": str(e)}
            )
            
            raise
    
    @elder_worker_required(ElderRole.GRAND_ELDER)
    async def _process_grand_elder_task(self, context: ElderTaskContext, task_data: Dict) -> Dict:
        """🌟 グランドエルダー専用タスク処理"""
        self.logger.info(f"{EMOJI['crown']} Processing Grand Elder task: {task_data.get('id')}")
        
        # 最高権限でのタスク実行
        # 全システム制御、緊急時対応、システム管理
        task_type = task_data.get('type', 'general')
        
        if task_type == 'system_emergency':
            return await self._handle_system_emergency(context, task_data)
        elif task_type == 'elder_council_decision':
            return await self._execute_council_decision(context, task_data)
        elif task_type == 'global_system_control':
            return await self._execute_global_control(context, task_data)
        else:
            # 通常のタスクも最高権限で実行
            return await self._execute_enhanced_claude_task(context, task_data)
    
    @elder_worker_required(ElderRole.CLAUDE_ELDER)
    async def _process_claude_elder_task(self, context: ElderTaskContext, task_data: Dict) -> Dict:
        """🤖 クロードエルダー専用タスク処理"""
        self.logger.info(f"{EMOJI['robot']} Processing Claude Elder task: {task_data.get('id')}")
        
        # 開発実行責任者権限でのタスク実行
        task_type = task_data.get('type', 'general')
        
        if task_type == 'development_management':
            return await self._handle_development_task(context, task_data)
        elif task_type == 'sage_coordination':
            return await self._coordinate_sage_tasks(context, task_data)
        elif task_type == 'system_deployment':
            return await self._handle_deployment_task(context, task_data)
        else:
            return await self._execute_enhanced_claude_task(context, task_data)
    
    @elder_worker_required(ElderRole.SAGE, SageType.TASK)
    async def _process_sage_task(self, context: ElderTaskContext, task_data: Dict) -> Dict:
        """🧙‍♂️ 賢者専用タスク処理"""
        self.logger.info(f"{EMOJI['sage']} Processing Sage task: {task_data.get('id')}")
        
        # 賢者権限でのタスク実行
        sage_type = context.user.sage_type
        
        if sage_type == SageType.TASK:
            return await self._handle_task_sage_work(context, task_data)
        elif sage_type == SageType.KNOWLEDGE:
            return await self._handle_knowledge_sage_work(context, task_data)
        elif sage_type == SageType.INCIDENT:
            return await self._handle_incident_sage_work(context, task_data)
        elif sage_type == SageType.RAG:
            return await self._handle_rag_sage_work(context, task_data)
        else:
            return await self._execute_standard_claude_task(context, task_data)
    
    async def _process_servant_task(self, context: ElderTaskContext, task_data: Dict) -> Dict:
        """🧝‍♂️ サーバント用制限付きタスク処理"""
        self.logger.info(f"{EMOJI['info']} Processing Servant task: {task_data.get('id')}")
        
        # 基本権限のみでのタスク実行
        # セキュリティ制限、入力フィルタリング、出力制限
        filtered_task_data = self._filter_servant_task_data(task_data)
        result = await self._execute_limited_claude_task(context, filtered_task_data)
        
        # 出力フィルタリング
        return self._filter_servant_task_output(result)
    
    async def _handle_system_emergency(self, context: ElderTaskContext, task_data: Dict) -> Dict:
        """システム緊急事態対応"""
        emergency_type = task_data.get('emergency_type', 'unknown')
        
        self.audit_logger.log_security_event(
            context,
            "system_emergency_activated",
            {"emergency_type": emergency_type, "timestamp": datetime.now().isoformat()}
        )
        
        # 緊急時プロトコル実行
        if emergency_type == 'security_breach':
            return await self._handle_security_breach(context, task_data)
        elif emergency_type == 'system_failure':
            return await self._handle_system_failure(context, task_data)
        else:
            return await self._handle_general_emergency(context, task_data)
    
    async def _execute_council_decision(self, context: ElderTaskContext, task_data: Dict) -> Dict:
        """エルダーズ評議会決定事項実行"""
        decision_type = task_data.get('decision_type', 'general')
        decision_data = task_data.get('decision_data', {})
        
        self.audit_logger.log_elder_action(
            context,
            "council_decision_execution",
            f"Executing council decision: {decision_type}"
        )
        
        # 評議会決定事項の実行
        # 4賢者への指示配信、システム設定変更等
        return {
            "status": "council_decision_executed",
            "decision_type": decision_type,
            "execution_time": datetime.now().isoformat(),
            "executed_by": context.user.username
        }
    
    async def _handle_task_sage_work(self, context: ElderTaskContext, task_data: Dict) -> Dict:
        """📋 タスク賢者専用作業処理"""
        task_operation = task_data.get('task_operation', 'general')
        
        if task_operation == 'project_management':
            return await self._manage_project_tasks(context, task_data)
        elif task_operation == 'task_optimization':
            return await self._optimize_task_workflow(context, task_data)
        elif task_operation == 'resource_allocation':
            return await self._allocate_task_resources(context, task_data)
        else:
            return await self._execute_enhanced_claude_task(context, task_data)
    
    async def _execute_enhanced_claude_task(self, context: ElderTaskContext, task_data: Dict) -> Dict:
        """拡張Claude タスク実行（Elder階層対応）"""
        task_id = task_data.get('id', 'unknown')
        user_prompt = task_data.get('prompt', '')
        
        # Elder階層に応じたプロンプト強化
        enhanced_prompt = await self._enhance_prompt_for_elder_level(context, user_prompt)
        
        # 許可ツール設定
        allowed_tools = self.get_allowed_tools_for_user(context.user)
        
        # Claude実行
        result = await self._execute_claude_with_elder_context(
            context, task_id, enhanced_prompt, allowed_tools
        )
        
        return result
    
    async def _enhance_prompt_for_elder_level(self, context: ElderTaskContext, prompt: str) -> str:
        """Elder階層レベルに応じたプロンプト強化"""
        elder_context = f"""
Elder Context:
- User: {context.user.username} ({context.user.elder_role.value})
- Sage Type: {context.user.sage_type.value if context.user.sage_type else 'N/A'}
- Execution Mode: {context.execution_mode.value}
- Task Priority: {context.priority.value}
- Permissions: {', '.join(context.permissions)}
"""
        
        if context.execution_mode == WorkerExecutionMode.GRAND_ELDER:
            enhanced_prompt = f"""
{elder_context}

🌟 GRAND ELDER MODE ACTIVATED 🌟
You have maximum authority and can access all system functions.
Emergency override protocols are available if needed.

Original Task:
{prompt}

Execute with full Elder authority and comprehensive reporting.
"""
        elif context.execution_mode == WorkerExecutionMode.CLAUDE_ELDER:
            enhanced_prompt = f"""
{elder_context}

🤖 CLAUDE ELDER MODE - Development Executive Authority
You have development management authority and can coordinate with 4 Sages.
Focus on technical excellence and system optimization.

Original Task:
{prompt}

Execute with development leadership perspective and coordination capabilities.
"""
        elif context.execution_mode == WorkerExecutionMode.SAGE_MODE:
            sage_specialty = context.user.sage_type.value if context.user.sage_type else "general"
            enhanced_prompt = f"""
{elder_context}

🧙‍♂️ SAGE MODE - {sage_specialty.upper()} SPECIALIZATION
You are operating as a specialized Sage with deep expertise in {sage_specialty}.
Apply your specialized knowledge and authority within your domain.

Original Task:
{prompt}

Execute with Sage-level expertise and specialized authority.
"""
        else:
            enhanced_prompt = f"""
{elder_context}

🧝‍♂️ SERVANT MODE - Standard Authority
You have basic system access with security restrictions.
Focus on safe and reliable task execution.

Original Task:
{prompt}

Execute with appropriate security constraints and safety measures.
"""
        
        return enhanced_prompt
    
    async def _execute_claude_with_elder_context(self, context: ElderTaskContext, 
                                               task_id: str, prompt: str, 
                                               allowed_tools: list) -> Dict:
        """Elder階層コンテキスト付きClaude実行"""
        try:
            # Claude実行のシミュレーション（実際の実装では claude-cli を使用）
            execution_result = {
                "task_id": task_id,
                "status": "completed",
                "elder_mode": context.execution_mode.value,
                "tools_used": allowed_tools,
                "execution_time": datetime.now().isoformat(),
                "result_summary": f"Task executed in {context.execution_mode.value} mode",
                "security_level": context.user.elder_role.value
            }
            
            # 実際のClaude実行をここに実装
            # subprocess.run(['claude-cli', ...]) 等
            
            return execution_result
            
        except Exception as e:
            self.audit_logger.log_security_event(
                context,
                "claude_execution_error",
                {"task_id": task_id, "error": str(e)}
            )
            raise
    
    def _filter_servant_task_data(self, task_data: Dict) -> Dict:
        """サーバント用タスクデータフィルタリング"""
        filtered = task_data.copy()
        
        # 危険なタスクタイプを除外
        dangerous_types = ['system_admin', 'emergency', 'deployment', 'security']
        if filtered.get('type') in dangerous_types:
            filtered['type'] = 'general'
        
        # 危険なプロンプト要素を除去
        prompt = filtered.get('prompt', '')
        dangerous_keywords = ['sudo', 'rm -rf', 'delete', 'admin', 'root']
        for keyword in dangerous_keywords:
            if keyword in prompt.lower():
                self.logger.warning(f"Dangerous keyword filtered from servant task: {keyword}")
                prompt = prompt.replace(keyword, '[FILTERED]')
        
        filtered['prompt'] = prompt
        return filtered
    
    def _filter_servant_task_output(self, result: Dict) -> Dict:
        """サーバント用タスク出力フィルタリング"""
        filtered = result.copy()
        
        # センシティブ情報の除去
        sensitive_keys = ['password', 'secret', 'key', 'token', 'admin']
        for key in sensitive_keys:
            if key in filtered:
                filtered[key] = '***FILTERED***'
        
        return filtered
    
    def _initialize_rag_integration(self):
        """RAG統合初期化"""
        try:
            self.rag_integration = RagGrimoireIntegration(self.rag_config)
            self.logger.info(f"{EMOJI['success']} RAG Grimoire Integration initialized")
        except Exception as e:
            self.logger.error(f"{EMOJI['error']} Failed to initialize RAG: {e}")
            self.rag_integration = None


# Elder階層ファクトリー関数
def create_elder_task_worker(elder_role: ElderRole = ElderRole.SAGE,
                           sage_type: Optional[SageType] = SageType.TASK,
                           auth_provider: Optional[UnifiedAuthProvider] = None) -> ElderEnhancedTaskWorker:
    """Elder階層タスクワーカー作成"""
    worker = ElderEnhancedTaskWorker(auth_provider=auth_provider)
    worker.required_elder_role = elder_role
    worker.required_sage_type = sage_type
    
    return worker


# デモ実行関数
async def demo_elder_task_execution():
    """Elder階層タスクワーカーのデモ実行"""
    from libs.unified_auth_provider import create_demo_auth_system, AuthRequest
    
    print(f"{EMOJI['start']} Elder Task Worker Demo Starting...")
    
    # デモ認証システム
    auth = create_demo_auth_system()
    
    # タスクワーカー作成
    worker = create_elder_task_worker(
        elder_role=ElderRole.SAGE,
        sage_type=SageType.TASK,
        auth_provider=auth
    )
    
    # タスク賢者として認証
    auth_request = AuthRequest(username="task_sage", password="task_password")
    result, session, user = auth.authenticate(auth_request)
    
    if result.value == "success":
        print(f"{EMOJI['success']} Authenticated as Task Sage: {user.username}")
        
        # タスクコンテキスト作成
        context = worker.create_elder_context(
            user=user,
            session=session,
            task_id="demo_elder_task_001",
            priority=ElderTaskPriority.HIGH
        )
        
        # デモタスクデータ
        demo_task_data = {
            "id": "demo_elder_task_001",
            "type": "project_management",
            "prompt": "AI Companyの新機能開発プロジェクトの進捗管理を実行してください",
            "priority": "high",
            "task_operation": "project_management"
        }
        
        # Elder階層タスク実行
        async def demo_task():
            return await worker.process_elder_message(context, demo_task_data)
        
        result = await worker.execute_with_elder_context(context, demo_task)
        
        print(f"{EMOJI['complete']} Demo Task Result:")
        print(f"  Status: {result.status}")
        print(f"  Execution Mode: {result.elder_context.execution_mode.value}")
        print(f"  Task Priority: {result.elder_context.priority.value}")
        print(f"  Execution Time: {result.execution_time:.2f}s")
        print(f"  Audit Events: {len(result.audit_log['events'])}")
        
    else:
        print(f"{EMOJI['error']} Authentication failed: {result}")


if __name__ == "__main__":
    # デモ実行
    asyncio.run(demo_elder_task_execution())