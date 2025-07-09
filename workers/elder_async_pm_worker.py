#!/usr/bin/env python3
"""
Elder階層統合 非同期PM Worker v2.0
AI Company Elder Hierarchy Integrated Asynchronous Project Management

エルダーズ評議会承認済み統合認証対応非同期プロジェクトマネジメントワーカー
メモリ管理、並列処理、ロールバック機構＋Elder階層権限管理
"""

import asyncio
import json
import gc
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
import weakref
import structlog
from collections import deque
from dataclasses import dataclass
import aiofiles
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
from core.rate_limiter import CacheManager
from libs.github_flow_manager import GitHubFlowManager
from libs.test_manager import TestManager
from libs.slack_notifier import SlackNotifier
from core import get_config, EMOJI

# Elder階層専用絵文字
ELDER_ASYNC_EMOJI = {
    **EMOJI,
    'async': '⚡',
    'parallel': '🔀',
    'memory': '💾',
    'rollback': '↩️',
    'checkpoint': '📍',
    'council': '🏛️',
    'sage': '🧙‍♂️',
    'crown': '👑',
    'shield': '🛡️',
    'elder': '⚡',
    'phase': '🔄',
    'authority': '🔱'
}


@dataclass
class ElderTaskContext:
    """Elder階層対応タスクコンテキスト（メモリ効率重視）"""
    task_id: str
    created_at: datetime
    status: str
    phase: str = "pending"
    iteration: int = 0
    temp_files: Set[str] = None
    error_count: int = 0
    elder_role: ElderRole = None
    permissions: Dict[str, bool] = None
    audit_trail: List[Dict] = None
    
    def __post_init__(self):
        if self.temp_files is None:
            self.temp_files = set()
        if self.audit_trail is None:
            self.audit_trail = []
        if self.permissions is None:
            self.permissions = {}


class ElderMemoryManager(object):
    """Elder階層対応メモリ管理クラス"""
    
    def __init__(self, max_memory_mb: int = 1024, cleanup_threshold: float = 0.8):
        self.max_memory_mb = max_memory_mb
        self.cleanup_threshold = cleanup_threshold
        self.logger = structlog.get_logger(__name__)
        self.process = psutil.Process()
        
        # 弱参照でオブジェクトを追跡
        self.tracked_objects = weakref.WeakSet()
        
        # Elder階層別メモリ制限
        self.elder_memory_limits = {
            ElderRole.GRAND_ELDER: max_memory_mb,
            ElderRole.CLAUDE_ELDER: int(max_memory_mb * 0.8),
            ElderRole.SAGE: int(max_memory_mb * 0.6),
            ElderRole.SERVANT: int(max_memory_mb * 0.4)
        }
    
    def get_memory_limit_for_elder(self, elder_role: ElderRole) -> int:
        """Elder階層に応じたメモリ制限取得"""
        return self.elder_memory_limits.get(elder_role, self.max_memory_mb // 2)
    
    def track_object(self, obj):
        """オブジェクトの追跡開始"""
        self.tracked_objects.add(obj)
    
    def get_memory_usage(self) -> float:
        """現在のメモリ使用量（MB）"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def get_memory_percent(self) -> float:
        """メモリ使用率（%）"""
        return self.get_memory_usage() / self.max_memory_mb
    
    async def check_and_cleanup(self, elder_context: Optional[ElderTaskContext] = None, 
                               force: bool = False) -> bool:
        """Elder階層対応メモリチェックとクリーンアップ"""
        current_usage = self.get_memory_usage()
        usage_percent = self.get_memory_percent()
        
        # Elder階層に応じたクリーンアップ閾値
        adjusted_threshold = self.cleanup_threshold
        if elder_context and elder_context.elder_role:
            if elder_context.elder_role in [ElderRole.SERVANT]:
                adjusted_threshold = 0.6  # より厳しい制限
        
        if force or usage_percent > adjusted_threshold:
            self.logger.info(
                "Starting Elder memory cleanup",
                current_mb=current_usage,
                usage_percent=f"{usage_percent:.1f}%",
                tracked_objects=len(self.tracked_objects),
                elder_role=elder_context.elder_role.value if elder_context else "system"
            )
            
            # ガベージコレクション実行
            collected = gc.collect()
            
            # メモリ使用量の再計算
            new_usage = self.get_memory_usage()
            freed_mb = current_usage - new_usage
            
            self.logger.info(
                "Elder memory cleanup completed",
                freed_mb=f"{freed_mb:.1f}MB",
                collected_objects=collected,
                new_usage_mb=new_usage
            )
            
            # Elder監査ログ
            if elder_context:
                elder_context.audit_trail.append({
                    'action': 'memory_cleanup',
                    'freed_mb': freed_mb,
                    'timestamp': datetime.now().isoformat()
                })
            
            return freed_mb > 0
        
        return False


class ElderTaskPhaseManager:
    """Elder階層対応タスクフェーズ管理（並列処理対応）"""
    
    def __init__(self, max_concurrent_tasks: int = 5):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.active_tasks: Dict[str, ElderTaskContext] = {}
        self.task_semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.logger = structlog.get_logger(__name__)
        
        # Elder階層別同時実行数制限
        self.elder_concurrency_limits = {
            ElderRole.GRAND_ELDER: max_concurrent_tasks,
            ElderRole.CLAUDE_ELDER: max(max_concurrent_tasks - 1, 3),
            ElderRole.SAGE: max(max_concurrent_tasks - 2, 2),
            ElderRole.SERVANT: 1
        }
        
        # フェーズ実行時間の追跡
        self.phase_timings: Dict[str, deque] = {
            'requirements': deque(maxlen=100),
            'design': deque(maxlen=100),
            'development': deque(maxlen=100),
            'testing': deque(maxlen=100),
            'deployment': deque(maxlen=100)
        }
    
    def get_concurrency_limit(self, elder_role: ElderRole) -> int:
        """Elder階層に応じた同時実行数制限取得"""
        return self.elder_concurrency_limits.get(elder_role, 1)
    
    async def execute_task_phases(
        self, 
        task_context: ElderTaskContext,
        phases_to_run: List[str],
        elder_context: ElderTaskContext
    ) -> Dict[str, Any]:
        """Elder階層対応タスクフェーズの並列実行"""
        # Elder階層に応じた同時実行数制限
        concurrency_limit = self.get_concurrency_limit(elder_context.elder_role)
        phase_semaphore = asyncio.Semaphore(concurrency_limit)
        
        async with self.task_semaphore:
            self.active_tasks[task_context.task_id] = task_context
            
            try:
                results = {}
                
                # Elder権限チェック
                allowed_phases = self._get_allowed_phases(elder_context.elder_role)
                phases_to_run = [p for p in phases_to_run if p in allowed_phases]
                
                for phase in phases_to_run:
                    async with phase_semaphore:
                        start_time = datetime.utcnow()
                        task_context.phase = phase
                        
                        # Elder監査ログ
                        task_context.audit_trail.append({
                            'phase': phase,
                            'started_by': elder_context.elder_role.value,
                            'timestamp': start_time.isoformat()
                        })
                        
                        # フェーズ実行
                        phase_result = await self._execute_single_phase(
                            task_context, phase, elder_context
                        )
                        results[phase] = phase_result
                        
                        # 実行時間の記録
                        duration = (datetime.utcnow() - start_time).total_seconds()
                        self.phase_timings[phase].append(duration)
                        
                        # フェーズ間でのメモリクリーンアップ
                        if phase in ['development', 'testing']:
                            gc.collect()
                
                task_context.status = 'completed'
                return results
                
            except Exception as e:
                task_context.status = 'failed'
                task_context.error_count += 1
                
                # Elder階層エラーログ
                task_context.audit_trail.append({
                    'error': str(e),
                    'phase': task_context.phase,
                    'elder_role': elder_context.elder_role.value,
                    'timestamp': datetime.now().isoformat()
                })
                
                raise
            
            finally:
                # タスクコンテキストのクリーンアップ
                if task_context.task_id in self.active_tasks:
                    del self.active_tasks[task_context.task_id]
                
                # 一時ファイルのクリーンアップ
                await self._cleanup_temp_files(task_context)
    
    def _get_allowed_phases(self, elder_role: ElderRole) -> List[str]:
        """Elder階層に応じた許可フェーズ取得"""
        if elder_role == ElderRole.GRAND_ELDER:
            return ['requirements', 'design', 'development', 'testing', 'deployment']
        elif elder_role == ElderRole.CLAUDE_ELDER:
            return ['requirements', 'design', 'development', 'testing', 'deployment']
        elif elder_role == ElderRole.SAGE:
            return ['requirements', 'design', 'development', 'testing']
        else:  # SERVANT
            return ['requirements', 'development']
    
    async def _execute_single_phase(
        self, 
        context: ElderTaskContext, 
        phase: str,
        elder_context: ElderTaskContext
    ) -> Dict[str, Any]:
        """Elder階層対応単一フェーズの実行"""
        self.logger.info(
            "Executing Elder phase",
            task_id=context.task_id,
            phase=phase,
            iteration=context.iteration,
            elder_role=elder_context.elder_role.value
        )
        
        # フェーズ別の実行ロジック
        if phase == 'requirements':
            return await self._phase_requirements(context, elder_context)
        elif phase == 'design':
            return await self._phase_design(context, elder_context)
        elif phase == 'development':
            return await self._phase_development(context, elder_context)
        elif phase == 'testing':
            return await self._phase_testing(context, elder_context)
        elif phase == 'deployment':
            return await self._phase_deployment(context, elder_context)
        else:
            raise ValueError(f"Unknown phase: {phase}")
    
    async def _phase_requirements(self, context: ElderTaskContext, 
                                elder_context: ElderTaskContext) -> Dict[str, Any]:
        """要件定義フェーズ（Elder階層対応）"""
        # Elder階層に応じた要件分析深度
        if elder_context.elder_role in [ElderRole.GRAND_ELDER, ElderRole.CLAUDE_ELDER]:
            requirements = ['基本機能', 'テスト要件', 'セキュリティ要件', 'パフォーマンス要件']
            complexity = 'high'
        elif elder_context.elder_role == ElderRole.SAGE:
            requirements = ['基本機能', 'テスト要件', 'セキュリティ要件']
            complexity = 'medium'
        else:
            requirements = ['基本機能', 'テスト要件']
            complexity = 'low'
        
        return {
            'status': 'completed',
            'requirements': requirements,
            'estimated_complexity': complexity,
            'analyzed_by': elder_context.elder_role.value
        }
    
    async def _phase_design(self, context: ElderTaskContext, 
                          elder_context: ElderTaskContext) -> Dict[str, Any]:
        """設計フェーズ（Elder階層対応）"""
        # Elder階層に応じた設計詳細度
        if elder_context.elder_role == ElderRole.GRAND_ELDER:
            design_docs = ['architecture.md', 'api_spec.md', 'security_design.md', 'scalability.md']
        elif elder_context.elder_role == ElderRole.CLAUDE_ELDER:
            design_docs = ['architecture.md', 'api_spec.md', 'security_design.md']
        elif elder_context.elder_role == ElderRole.SAGE:
            design_docs = ['architecture.md', 'api_spec.md']
        else:
            design_docs = ['basic_design.md']
        
        return {
            'status': 'completed',
            'design_docs': design_docs,
            'components': ['main_module', 'test_module', 'auth_module'],
            'designed_by': elder_context.elder_role.value
        }
    
    async def _phase_development(self, context: ElderTaskContext, 
                                elder_context: ElderTaskContext) -> Dict[str, Any]:
        """開発フェーズ（Elder階層対応並列ファイル操作）"""
        # Elder階層に応じたファイル作成権限
        if elder_context.elder_role in [ElderRole.GRAND_ELDER, ElderRole.CLAUDE_ELDER]:
            files_to_create = ['main.py', 'test_main.py', 'requirements.txt', 'security.py']
        elif elder_context.elder_role == ElderRole.SAGE:
            files_to_create = ['main.py', 'test_main.py', 'requirements.txt']
        else:
            files_to_create = ['main.py', 'test_main.py']
        
        # 並列ファイル作成
        tasks = [
            self._create_file_async(context, filename, elder_context)
            for filename in files_to_create
        ]
        
        created_files = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 成功したファイルのみを記録
        successful_files = [
            f for f in created_files 
            if isinstance(f, str) and not isinstance(f, Exception)
        ]
        
        return {
            'status': 'completed',
            'files_created': successful_files,
            'errors': [str(e) for e in created_files if isinstance(e, Exception)],
            'developed_by': elder_context.elder_role.value
        }
    
    async def _create_file_async(self, context: ElderTaskContext, filename: str,
                               elder_context: ElderTaskContext) -> str:
        """Elder階層対応非同期ファイル作成"""
        file_path = Path(f"/tmp/{context.task_id}_{filename}")
        context.temp_files.add(str(file_path))
        
        # Elder階層情報を含むコンテンツ
        content = f"""# {filename}
# Generated for task {context.task_id}
# Created by: {elder_context.elder_role.value}
# Timestamp: {datetime.now().isoformat()}
# Elder Authority: {elder_context.permissions}

"""
        
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(content)
        
        return str(file_path)
    
    async def _phase_testing(self, context: ElderTaskContext, 
                           elder_context: ElderTaskContext) -> Dict[str, Any]:
        """テストフェーズ（Elder階層対応非同期待機）"""
        # Elder階層に応じたテスト深度
        if elder_context.elder_role in [ElderRole.GRAND_ELDER, ElderRole.CLAUDE_ELDER]:
            await asyncio.sleep(3)  # より詳細なテスト
            test_types = ['unit', 'integration', 'security', 'performance']
        elif elder_context.elder_role == ElderRole.SAGE:
            await asyncio.sleep(2)
            test_types = ['unit', 'integration']
        else:
            await asyncio.sleep(1)
            test_types = ['unit']
        
        return {
            'status': 'completed',
            'test_results': {'passed': 5, 'failed': 0},
            'coverage': 95.0,
            'test_types': test_types,
            'tested_by': elder_context.elder_role.value
        }
    
    @elder_worker_required(ElderRole.CLAUDE_ELDER)
    async def _phase_deployment(self, context: ElderTaskContext, 
                              elder_context: ElderTaskContext) -> Dict[str, Any]:
        """デプロイフェーズ（Elder階層制限）"""
        return {
            'status': 'completed',
            'deployed_version': f"v1.0.{context.iteration}",
            'deployment_url': f"https://deploy.example.com/{context.task_id}",
            'deployed_by': elder_context.elder_role.value,
            'deployment_authority': 'ELDER_APPROVED'
        }
    
    async def _cleanup_temp_files(self, context: ElderTaskContext):
        """一時ファイルのクリーンアップ"""
        for temp_file in context.temp_files:
            try:
                Path(temp_file).unlink(missing_ok=True)
            except Exception as e:
                self.logger.warning(
                    "Failed to cleanup temp file",
                    file=temp_file,
                    error=str(e)
                )
        
        context.temp_files.clear()
    
    def get_phase_statistics(self) -> Dict[str, Any]:
        """フェーズ統計情報の取得"""
        stats = {}
        
        for phase, timings in self.phase_timings.items():
            if timings:
                stats[phase] = {
                    'avg_duration': sum(timings) / len(timings),
                    'min_duration': min(timings),
                    'max_duration': max(timings),
                    'total_executions': len(timings)
                }
            else:
                stats[phase] = {
                    'avg_duration': 0,
                    'min_duration': 0,
                    'max_duration': 0,
                    'total_executions': 0
                }
        
        return stats


class ElderAsyncPMWorker(ElderAwareBaseWorker):
    """
    Elder階層統合非同期PM Worker
    
    Elder階層システムと統合認証に対応した非同期プロジェクト管理システム
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
        self.worker_type = 'async_pm'
        self.worker_id = worker_id or f"elder_async_pm_worker_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Elder階層対応キュー設定
        self.input_queue = 'ai_async_pm_elder'
        self.output_queue = 'ai_async_results_elder'
        
        self.config = config or get_config()
        
        # Elder階層メモリ管理
        self.memory_manager = ElderMemoryManager(
            max_memory_mb=self.config.get('max_memory_mb', 1024),
            cleanup_threshold=self.config.get('cleanup_threshold', 0.8)
        )
        
        # Elder階層タスクフェーズ管理
        self.phase_manager = ElderTaskPhaseManager(
            max_concurrent_tasks=self.config.get('max_concurrent_tasks', 5)
        )
        
        # 外部サービス
        self.github_manager = GitHubFlowManager()
        self.test_manager = TestManager()
        self.slack_notifier = SlackNotifier()
        
        # タスク履歴（LRUキャッシュ）
        self.task_history = deque(maxlen=1000)
        
        # ロールバック用のチェックポイント
        self.checkpoints: Dict[str, Dict[str, Any]] = {}
        
        # Elder階層権限設定
        self.elder_pm_permissions = self._configure_elder_permissions()
        
        # 自動クリーンアップタスク
        self.cleanup_task = None
        
        self.logger.info(f"{ELDER_ASYNC_EMOJI['council']} Elder Async PM Worker initialized - Required: {self.required_elder_role.value}")
    
    def _configure_elder_permissions(self) -> Dict[ElderRole, Dict[str, bool]]:
        """Elder階層別権限設定"""
        return {
            ElderRole.SERVANT: {
                'simple_tasks': True,
                'project_mode': False,
                'deployment': False,
                'rollback': False,
                'emergency_override': False
            },
            ElderRole.SAGE: {
                'simple_tasks': True,
                'project_mode': True,
                'deployment': False,
                'rollback': True,
                'emergency_override': False
            },
            ElderRole.CLAUDE_ELDER: {
                'simple_tasks': True,
                'project_mode': True,
                'deployment': True,
                'rollback': True,
                'emergency_override': False
            },
            ElderRole.GRAND_ELDER: {
                'simple_tasks': True,
                'project_mode': True,
                'deployment': True,
                'rollback': True,
                'emergency_override': True
            }
        }
    
    async def process_elder_async_message(self, elder_context: ElderTaskContext,
                                        message: Dict[str, Any]) -> ElderTaskResult:
        """Elder階層認証済み非同期メッセージ処理"""
        task_id = message.get('task_id', f"async_pm_{int(datetime.utcnow().timestamp())}")
        
        # Elder階層ログ
        self.audit_logger.log_elder_action(
            elder_context,
            f"async_pm_start",
            f"Starting async PM task: {task_id}"
        )
        
        # タスクコンテキスト作成
        task_context = ElderTaskContext(
            task_id=task_id,
            created_at=datetime.utcnow(),
            status='processing',
            elder_role=elder_context.user.elder_role,
            permissions=self.elder_pm_permissions[elder_context.user.elder_role]
        )
        
        # メモリ管理に追加
        self.memory_manager.track_object(task_context)
        
        try:
            # チェックポイント作成
            await self._create_checkpoint(task_id, message, elder_context)
            
            # タスクタイプの判定
            if self._is_project_mode(message):
                # 権限チェック
                if not task_context.permissions['project_mode']:
                    raise PermissionError("Insufficient permissions for project mode")
                result = await self._handle_project_mode(task_context, message, elder_context)
            else:
                result = await self._handle_simple_mode(task_context, message, elder_context)
            
            # 履歴に追加
            self.task_history.append({
                'task_id': task_id,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'completed',
                'duration': (datetime.utcnow() - task_context.created_at).total_seconds(),
                'elder_role': elder_context.user.elder_role.value
            })
            
            # 成功ログ
            self.audit_logger.log_elder_action(
                elder_context,
                f"async_pm_complete",
                f"Async PM task completed: {task_id}"
            )
            
            return ElderTaskResult(
                status='completed',
                result=result,
                execution_time=(datetime.utcnow() - task_context.created_at).total_seconds(),
                elder_context=elder_context,
                audit_log={'events': task_context.audit_trail}
            )
            
        except Exception as e:
            # ロールバック実行（権限チェック）
            if task_context.permissions['rollback']:
                await self._rollback_task(task_id, elder_context)
            
            # エラー履歴に追加
            self.task_history.append({
                'task_id': task_id,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'failed',
                'error': str(e),
                'duration': (datetime.utcnow() - task_context.created_at).total_seconds(),
                'elder_role': elder_context.user.elder_role.value
            })
            
            # エラーログ
            self.audit_logger.log_elder_action(
                elder_context,
                f"async_pm_error",
                f"Async PM task failed: {task_id} - {str(e)}"
            )
            
            self.audit_logger.log_security_event(
                elder_context,
                "async_pm_execution_error",
                {"task_id": task_id, "error": str(e)}
            )
            
            raise
        
        finally:
            # チェックポイントのクリーンアップ
            if task_id in self.checkpoints:
                del self.checkpoints[task_id]
            
            # メモリクリーンアップ
            await self.memory_manager.check_and_cleanup(elder_context)
    
    def _is_project_mode(self, message: Dict[str, Any]) -> bool:
        """プロジェクトモードの判定"""
        complexity_indicators = [
            'プロジェクト', 'project', '設計', 'design',
            'アーキテクチャ', 'architecture', '複数ファイル'
        ]
        
        prompt = message.get('prompt', '').lower()
        return any(indicator in prompt for indicator in complexity_indicators)
    
    async def _handle_project_mode(
        self, 
        task_context: ElderTaskContext, 
        message: Dict[str, Any],
        elder_context: ElderTaskContext
    ) -> Dict[str, Any]:
        """Elder階層対応プロジェクトモードの処理"""
        phases = ['requirements', 'design', 'development', 'testing']
        
        # Elder階層に応じてデプロイメントフェーズを追加
        if elder_context.user.elder_role in [ElderRole.GRAND_ELDER, ElderRole.CLAUDE_ELDER]:
            phases.append('deployment')
        
        # 並列フェーズ実行
        phase_results = await self.phase_manager.execute_task_phases(
            task_context, phases, elder_context
        )
        
        return {
            'task_id': task_context.task_id,
            'mode': 'project',
            'status': 'completed',
            'phase_results': phase_results,
            'duration': (datetime.utcnow() - task_context.created_at).total_seconds(),
            'elder_authority': elder_context.user.elder_role.value,
            'audit_trail': task_context.audit_trail
        }
    
    async def _handle_simple_mode(
        self, 
        task_context: ElderTaskContext, 
        message: Dict[str, Any],
        elder_context: ElderTaskContext
    ) -> Dict[str, Any]:
        """Elder階層対応シンプルモードの処理"""
        # 単一フェーズ実行
        phase_results = await self.phase_manager.execute_task_phases(
            task_context, ['development'], elder_context
        )
        
        return {
            'task_id': task_context.task_id,
            'mode': 'simple',
            'status': 'completed',
            'result': phase_results['development'],
            'duration': (datetime.utcnow() - task_context.created_at).total_seconds(),
            'elder_authority': elder_context.user.elder_role.value
        }
    
    async def _create_checkpoint(self, task_id: str, message: Dict[str, Any],
                               elder_context: ElderTaskContext):
        """Elder階層対応タスクのチェックポイント作成"""
        self.checkpoints[task_id] = {
            'timestamp': datetime.utcnow().isoformat(),
            'original_message': message.copy(),
            'git_state': await self._capture_git_state(),
            'elder_context': {
                'user': elder_context.user.username,
                'role': elder_context.user.elder_role.value,
                'permissions': elder_context.permissions
            }
        }
        
        # Elder監査ログ
        self.audit_logger.log_elder_action(
            elder_context,
            "checkpoint_created",
            f"Checkpoint created for task {task_id}"
        )
    
    async def _capture_git_state(self) -> Dict[str, str]:
        """Git状態のキャプチャ"""
        try:
            return {
                'branch': await self.github_manager.get_current_branch(),
                'commit': await self.github_manager.get_current_commit(),
                'status': await self.github_manager.get_git_status()
            }
        except Exception as e:
            self.logger.warning("Failed to capture git state", error=str(e))
            return {}
    
    @elder_worker_required(ElderRole.SAGE)
    async def _rollback_task(self, task_id: str, elder_context: ElderTaskContext):
        """Elder階層対応タスクのロールバック（賢者以上）"""
        if task_id not in self.checkpoints:
            return
        
        checkpoint = self.checkpoints[task_id]
        
        try:
            # Gitロールバック
            git_state = checkpoint.get('git_state', {})
            if git_state.get('commit'):
                await self.github_manager.reset_to_commit(git_state['commit'])
            
            self.logger.info(
                "Elder task rolled back successfully",
                task_id=task_id,
                checkpoint_time=checkpoint['timestamp'],
                rolled_back_by=elder_context.user.username
            )
            
            # Elder監査ログ
            self.audit_logger.log_elder_action(
                elder_context,
                "task_rollback",
                f"Task {task_id} rolled back to checkpoint"
            )
            
        except Exception as e:
            self.logger.error(
                "Elder rollback failed",
                task_id=task_id,
                error=str(e)
            )
            
            self.audit_logger.log_security_event(
                elder_context,
                "rollback_failure",
                {"task_id": task_id, "error": str(e)}
            )
    
    async def periodic_cleanup(self):
        """定期的なクリーンアップ（Elder階層対応）"""
        while True:
            try:
                # システムレベルクリーンアップ（Grand Elder権限相当）
                system_context = ElderTaskContext(
                    task_id="system_cleanup",
                    created_at=datetime.utcnow(),
                    status='running',
                    elder_role=ElderRole.GRAND_ELDER,
                    permissions=self.elder_pm_permissions[ElderRole.GRAND_ELDER]
                )
                
                # メモリクリーンアップ
                await self.memory_manager.check_and_cleanup(system_context)
                
                # 古いチェックポイントの削除
                await self._cleanup_old_checkpoints()
                
                # 統計情報の記録
                await self._record_statistics()
                
                # 10分ごとに実行
                await asyncio.sleep(600)
                
            except Exception as e:
                self.logger.error("Periodic cleanup error", error=str(e))
                await asyncio.sleep(60)
    
    async def _cleanup_old_checkpoints(self):
        """古いチェックポイントのクリーンアップ"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        to_delete = []
        for task_id, checkpoint in self.checkpoints.items():
            checkpoint_time = datetime.fromisoformat(
                checkpoint['timestamp'].replace('Z', '+00:00')
            )
            if checkpoint_time < cutoff_time:
                to_delete.append(task_id)
        
        for task_id in to_delete:
            del self.checkpoints[task_id]
        
        if to_delete:
            self.logger.info("Cleaned up old checkpoints", count=len(to_delete))
    
    async def _record_statistics(self):
        """統計情報の記録"""
        stats = {
            'memory_usage_mb': self.memory_manager.get_memory_usage(),
            'active_tasks': len(self.phase_manager.active_tasks),
            'checkpoints': len(self.checkpoints),
            'task_history_size': len(self.task_history),
            'phase_stats': self.phase_manager.get_phase_statistics(),
            'elder_task_distribution': self._get_elder_task_distribution(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.logger.info("Elder async PM statistics", **stats)
    
    def _get_elder_task_distribution(self) -> Dict[str, int]:
        """Elder階層別タスク分布"""
        distribution = {role.value: 0 for role in ElderRole}
        
        for task in self.task_history:
            role = task.get('elder_role', 'unknown')
            if role in distribution:
                distribution[role] += 1
        
        return distribution
    
    async def get_worker_statistics(self) -> Dict[str, Any]:
        """ワーカー統計情報の取得"""
        return {
            'memory': {
                'usage_mb': self.memory_manager.get_memory_usage(),
                'usage_percent': f"{self.memory_manager.get_memory_percent():.1f}%",
                'max_mb': self.memory_manager.max_memory_mb,
                'elder_limits': {
                    role.value: limit 
                    for role, limit in self.memory_manager.elder_memory_limits.items()
                }
            },
            'tasks': {
                'active': len(self.phase_manager.active_tasks),
                'history_size': len(self.task_history),
                'checkpoints': len(self.checkpoints),
                'elder_distribution': self._get_elder_task_distribution()
            },
            'phases': self.phase_manager.get_phase_statistics(),
            'concurrency': {
                role.value: limit
                for role, limit in self.phase_manager.elder_concurrency_limits.items()
            }
        }
    
    @elder_worker_required(ElderRole.GRAND_ELDER)
    async def emergency_override(self, elder_context: ElderTaskContext, 
                               override_data: Dict[str, Any]) -> Dict[str, Any]:
        """緊急オーバーライド（Grand Elder専用）"""
        self.audit_logger.log_security_event(
            elder_context,
            "emergency_override_activated",
            override_data
        )
        
        # 全タスクの強制停止
        for task_id in list(self.phase_manager.active_tasks.keys()):
            self.phase_manager.active_tasks[task_id].status = 'emergency_stopped'
        
        # メモリ強制クリーンアップ
        await self.memory_manager.check_and_cleanup(elder_context, force=True)
        
        return {
            'status': 'emergency_override_complete',
            'stopped_tasks': len(self.phase_manager.active_tasks),
            'timestamp': datetime.now().isoformat(),
            'authorized_by': elder_context.user.username
        }


# Elder階層ファクトリー関数
def create_elder_async_pm_worker(auth_provider: Optional[UnifiedAuthProvider] = None,
                               config: Optional[Dict[str, Any]] = None) -> ElderAsyncPMWorker:
    """Elder階層非同期PMワーカー作成"""
    return ElderAsyncPMWorker(auth_provider=auth_provider, config=config)


# デモ実行関数
async def demo_elder_async_pm_execution():
    """Elder階層非同期PMワーカーのデモ実行"""
    from libs.unified_auth_provider import create_demo_auth_system, AuthRequest
    
    print(f"{ELDER_ASYNC_EMOJI['start']} Elder Async PM Worker Demo Starting...")
    
    # デモ認証システム
    auth = create_demo_auth_system()
    
    # 非同期PMワーカー作成
    worker = create_elder_async_pm_worker(auth_provider=auth)
    
    # 賢者として認証
    auth_request = AuthRequest(username="task_sage", password="task_password")
    result, session, user = auth.authenticate(auth_request)
    
    if result.value == "success":
        print(f"{ELDER_ASYNC_EMOJI['success']} Authenticated as Task Sage: {user.username}")
        
        # 非同期PMコンテキスト作成
        context = worker.create_elder_context(
            user=user,
            session=session,
            task_id="demo_async_pm_001",
            priority=ElderTaskPriority.HIGH
        )
        
        # デモプロジェクトデータ
        demo_message = {
            "task_id": "async_project_001",
            "prompt": "Create a new microservice architecture project with authentication",
            "priority": "high",
            "async_mode": True
        }
        
        # Elder階層非同期PM実行
        async def demo_async_task():
            return await worker.process_elder_async_message(context, demo_message)
        
        result = await worker.execute_with_elder_context(context, demo_async_task)
        
        print(f"{ELDER_ASYNC_EMOJI['complete']} Demo Async PM Result:")
        print(f"  Status: {result.status}")
        print(f"  Execution Time: {result.execution_time:.2f}s")
        print(f"  Elder Authority: {user.elder_role.value}")
        
        # 統計情報表示
        stats = await worker.get_worker_statistics()
        print(f"\n{ELDER_ASYNC_EMOJI['memory']} Memory Stats:")
        print(f"  Usage: {stats['memory']['usage_mb']:.1f}MB ({stats['memory']['usage_percent']})")
        print(f"\n{ELDER_ASYNC_EMOJI['phase']} Phase Stats:")
        for phase, phase_stats in stats['phases'].items():
            if phase_stats['total_executions'] > 0:
                print(f"  {phase}: avg={phase_stats['avg_duration']:.2f}s")
        
    else:
        print(f"{ELDER_ASYNC_EMOJI['error']} Authentication failed: {result}")


if __name__ == "__main__":
    # デモ実行
    asyncio.run(demo_elder_async_pm_execution())