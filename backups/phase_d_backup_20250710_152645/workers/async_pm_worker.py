#!/usr/bin/env python3
"""
非同期対応PM Worker - Elders Guild Integration
メモリリーク対策、並列処理、ロールバック機構対応

エルダーツリー階層統合:
🌟 グランドエルダーmaru → 🤖 クロードエルダー → 🧙‍♂️ 4賢者 → 🏛️ 評議会 → ⚔️ PM Worker

PM Worker機能:
- 4賢者システム統合（Task Sage、Knowledge Sage、Incident Sage、RAG Sage）
- エルダー階層への報告・エスカレーション
- エルダー評議会との連携
- 自律的プロジェクト管理
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

# プロジェクトルートをPythonパスに追加
import sys
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.async_base_worker import AsyncBaseWorker
from core.rate_limiter import CacheManager
from libs.github_flow_manager import GitHubFlowManager
from libs.test_manager import TestManager
from libs.slack_notifier import SlackNotifier

# エルダーツリー階層統合
try:
    from libs.four_sages_integration import FourSagesIntegration
    from libs.elder_council_summoner import ElderCouncilSummoner
    from libs.elder_tree_hierarchy import get_elder_tree, ElderMessage, ElderRank
    ELDER_TREE_AVAILABLE = True
except ImportError as e:
    print(f"Elder Tree system not available: {e}")
    FourSagesIntegration = None
    ElderCouncilSummoner = None
    get_elder_tree = None
    ElderMessage = None
    ElderRank = None
    ELDER_TREE_AVAILABLE = False

@dataclass
class TaskContext:
    """タスクコンテキスト（メモリ効率重視）"""
    task_id: str
    created_at: datetime
    status: str
    phase: str = "pending"
    iteration: int = 0
    temp_files: Set[str] = None
    error_count: int = 0
    
    def __post_init__(self):
        if self.temp_files is None:
            self.temp_files = set()

class MemoryManager:
    """メモリ管理クラス"""
    
    def __init__(self, max_memory_mb: int = 1024, cleanup_threshold: float = 0.8):
        self.max_memory_mb = max_memory_mb
        self.cleanup_threshold = cleanup_threshold
        self.logger = structlog.get_logger(__name__)
        self.process = psutil.Process()
        
        # 弱参照でオブジェクトを追跡
        self.tracked_objects = weakref.WeakSet()
    
    def track_object(self, obj):
        """オブジェクトの追跡開始"""
        self.tracked_objects.add(obj)
    
    def get_memory_usage(self) -> float:
        """現在のメモリ使用量（MB）"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def get_memory_percent(self) -> float:
        """メモリ使用率（%）"""
        return self.get_memory_usage() / self.max_memory_mb
    
    async def check_and_cleanup(self, force: bool = False) -> bool:
        """メモリチェックとクリーンアップ"""
        current_usage = self.get_memory_usage()
        usage_percent = self.get_memory_percent()
        
        if force or usage_percent > self.cleanup_threshold:
            self.logger.info(
                "Starting memory cleanup",
                current_mb=current_usage,
                usage_percent=f"{usage_percent:.1f}%",
                tracked_objects=len(self.tracked_objects)
            )
            
            # ガベージコレクション実行
            collected = gc.collect()
            
            # メモリ使用量の再計算
            new_usage = self.get_memory_usage()
            freed_mb = current_usage - new_usage
            
            self.logger.info(
                "Memory cleanup completed",
                freed_mb=f"{freed_mb:.1f}MB",
                collected_objects=collected,
                new_usage_mb=new_usage
            )
            
            return freed_mb > 0
        
        return False

class TaskPhaseManager:
    """タスクフェーズ管理（並列処理対応）"""
    
    def __init__(self, max_concurrent_tasks: int = 5):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.active_tasks: Dict[str, TaskContext] = {}
        self.task_semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.logger = structlog.get_logger(__name__)
        
        # フェーズ実行時間の追跡
        self.phase_timings: Dict[str, deque] = {
            'requirements': deque(maxlen=100),
            'design': deque(maxlen=100),
            'development': deque(maxlen=100),
            'testing': deque(maxlen=100),
            'deployment': deque(maxlen=100)
        }
    
    async def execute_task_phases(
        self, 
        task_context: TaskContext,
        phases_to_run: List[str]
    ) -> Dict[str, Any]:
        """タスクフェーズの並列実行"""
        async with self.task_semaphore:
            self.active_tasks[task_context.task_id] = task_context
            
            try:
                results = {}
                
                for phase in phases_to_run:
                    start_time = datetime.utcnow()
                    task_context.phase = phase
                    
                    # フェーズ実行
                    phase_result = await self._execute_single_phase(
                        task_context, phase
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
                raise
            
            finally:
                # タスクコンテキストのクリーンアップ
                if task_context.task_id in self.active_tasks:
                    del self.active_tasks[task_context.task_id]
                
                # 一時ファイルのクリーンアップ
                await self._cleanup_temp_files(task_context)
    
    async def _execute_single_phase(
        self, 
        context: TaskContext, 
        phase: str
    ) -> Dict[str, Any]:
        """単一フェーズの実行"""
        self.logger.info(
            "Executing phase",
            task_id=context.task_id,
            phase=phase,
            iteration=context.iteration
        )
        
        # フェーズ別の実行ロジック
        if phase == 'requirements':
            return await self._phase_requirements(context)
        elif phase == 'design':
            return await self._phase_design(context)
        elif phase == 'development':
            return await self._phase_development(context)
        elif phase == 'testing':
            return await self._phase_testing(context)
        elif phase == 'deployment':
            return await self._phase_deployment(context)
        else:
            raise ValueError(f"Unknown phase: {phase}")
    
    async def _phase_requirements(self, context: TaskContext) -> Dict[str, Any]:
        """要件定義フェーズ"""
        # 軽量な要件分析
        return {
            'status': 'completed',
            'requirements': ['基本機能', 'テスト要件'],
            'estimated_complexity': 'medium'
        }
    
    async def _phase_design(self, context: TaskContext) -> Dict[str, Any]:
        """設計フェーズ"""
        # 設計ドキュメント生成
        return {
            'status': 'completed',
            'design_docs': ['architecture.md', 'api_spec.md'],
            'components': ['main_module', 'test_module']
        }
    
    async def _phase_development(self, context: TaskContext) -> Dict[str, Any]:
        """開発フェーズ（並列ファイル操作）"""
        files_to_create = ['main.py', 'test_main.py', 'requirements.txt']
        
        # 並列ファイル作成
        tasks = [
            self._create_file_async(context, filename)
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
            'errors': [str(e) for e in created_files if isinstance(e, Exception)]
        }
    
    async def _create_file_async(self, context: TaskContext, filename: str) -> str:
        """非同期ファイル作成"""
        file_path = Path(f"/tmp/{context.task_id}_{filename}")
        context.temp_files.add(str(file_path))
        
        # サンプルコンテンツ
        content = f"# {filename}\n# Generated for task {context.task_id}\n"
        
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(content)
        
        return str(file_path)
    
    async def _phase_testing(self, context: TaskContext) -> Dict[str, Any]:
        """テストフェーズ（非同期待機）"""
        # 非同期でテスト実行をシミュレート
        await asyncio.sleep(2)  # time.sleep(5)の代替
        
        return {
            'status': 'completed',
            'test_results': {'passed': 5, 'failed': 0},
            'coverage': 95.0
        }
    
    async def _phase_deployment(self, context: TaskContext) -> Dict[str, Any]:
        """デプロイフェーズ"""
        return {
            'status': 'completed',
            'deployed_version': f"v1.0.{context.iteration}",
            'deployment_url': f"https://deploy.example.com/{context.task_id}"
        }
    
    async def _cleanup_temp_files(self, context: TaskContext):
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

class AsyncPMWorker(AsyncBaseWorker):
    """
    非同期対応のPM Worker
    
    Features:
    - メモリリーク対策
    - 並列フェーズ処理
    - ロールバック機構
    - リソース管理
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(
            worker_name="async_pm_worker",
            config=config,
            input_queues=['ai_tasks', 'pm_task_queue'],
            output_queues=['worker_tasks', 'result_queue']
        )
        
        # メモリ管理
        self.memory_manager = MemoryManager(
            max_memory_mb=config.get('max_memory_mb', 1024),
            cleanup_threshold=config.get('cleanup_threshold', 0.8)
        )
        
        # タスクフェーズ管理
        self.phase_manager = TaskPhaseManager(
            max_concurrent_tasks=config.get('max_concurrent_tasks', 5)
        )
        
        # キャッシュマネージャ
        self.cache_manager = CacheManager(
            redis_client=self.redis_client,
            default_ttl=config.get('cache_ttl', 3600)
        )
        
        # 外部サービス
        self.github_manager = GitHubFlowManager()
        self.test_manager = TestManager()
        self.slack_notifier = SlackNotifier()
        
        # タスク履歴（LRUキャッシュ）
        self.task_history = deque(maxlen=1000)
        
        # ロールバック用のチェックポイント
        self.checkpoints: Dict[str, Dict[str, Any]] = {}
        
        # 自動クリーンアップタスク
        self.cleanup_task = None
        
        # エルダーツリー階層統合
        self.elder_tree_enabled = ELDER_TREE_AVAILABLE
        self.elder_tree = None
        self.four_sages_integration = None
        self.elder_council_summoner = None
        
        # エルダーシステム初期化
        if self.elder_tree_enabled:
            self._initialize_elder_systems()
        
        # PM最適化状態
        self.pm_optimization_state = {
            'task_sage_guidance': None,
            'knowledge_sage_patterns': None,
            'incident_sage_monitoring': None,
            'rag_sage_analysis': None,
            'last_elder_consultation': None,
            'elder_recommendations': []
        }
    
    def _initialize_elder_systems(self):
        """エルダーシステムの初期化"""
        try:
            self.logger.info("🌳 エルダーツリー階層システム初期化開始")
            
            # エルダーツリーインスタンス取得
            self.elder_tree = get_elder_tree()
            
            # 4賢者統合システム初期化
            self.four_sages_integration = FourSagesIntegration()
            
            # エルダー評議会召喚システム初期化
            self.elder_council_summoner = ElderCouncilSummoner()
            
            self.logger.info("✅ エルダーシステム初期化完了")
            self.logger.info("🏛️ PM Worker は エルダーツリー階層に統合されました")
            
        except Exception as e:
            self.logger.error(f"❌ エルダーシステム初期化失敗: {e}")
            self.elder_tree_enabled = False
            self.elder_tree = None
            self.four_sages_integration = None
            self.elder_council_summoner = None
    
    async def run(self):
        """ワーカーのメインループ（拡張）"""
        # 定期クリーンアップタスクの開始
        self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        try:
            await super().run()
        finally:
            if self.cleanup_task:
                self.cleanup_task.cancel()
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        メッセージ処理のメイン実装
        """
        task_id = message.get('task_id', f"pm_{int(datetime.utcnow().timestamp())}")
        
        # タスクコンテキスト作成
        context = TaskContext(
            task_id=task_id,
            created_at=datetime.utcnow(),
            status='processing'
        )
        
        # メモリ管理に追加
        self.memory_manager.track_object(context)
        
        try:
            # チェックポイント作成
            await self._create_checkpoint(task_id, message)
            
            # エルダーガイダンス取得
            if self.elder_tree_enabled:
                await self._consult_elder_guidance(context, message)
            
            # タスクタイプの判定
            if self._is_project_mode(message):
                result = await self._handle_project_mode(context, message)
            else:
                result = await self._handle_simple_mode(context, message)
            
            # エルダーへの結果報告
            if self.elder_tree_enabled:
                await self._report_to_elders(context, result)
            
            # 履歴に追加
            self.task_history.append({
                'task_id': task_id,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'completed',
                'duration': (datetime.utcnow() - context.created_at).total_seconds()
            })
            
            return result
            
        except Exception as e:
            # エルダーへの緊急報告
            if self.elder_tree_enabled:
                await self._escalate_critical_issue(task_id, str(e), context)
            
            # ロールバック実行
            await self._rollback_task(task_id)
            
            # エラー履歴に追加
            self.task_history.append({
                'task_id': task_id,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'failed',
                'error': str(e),
                'duration': (datetime.utcnow() - context.created_at).total_seconds()
            })
            
            raise
        
        finally:
            # チェックポイントのクリーンアップ
            if task_id in self.checkpoints:
                del self.checkpoints[task_id]
    
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
        context: TaskContext, 
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """プロジェクトモードの処理"""
        phases = ['requirements', 'design', 'development', 'testing', 'deployment']
        
        # 並列フェーズ実行
        phase_results = await self.phase_manager.execute_task_phases(
            context, phases
        )
        
        return {
            'task_id': context.task_id,
            'mode': 'project',
            'status': 'completed',
            'phase_results': phase_results,
            'duration': (datetime.utcnow() - context.created_at).total_seconds()
        }
    
    async def _handle_simple_mode(
        self, 
        context: TaskContext, 
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """シンプルモードの処理"""
        # 単一フェーズ実行
        phase_results = await self.phase_manager.execute_task_phases(
            context, ['development']
        )
        
        return {
            'task_id': context.task_id,
            'mode': 'simple',
            'status': 'completed',
            'result': phase_results['development'],
            'duration': (datetime.utcnow() - context.created_at).total_seconds()
        }
    
    async def _create_checkpoint(self, task_id: str, message: Dict[str, Any]):
        """タスクのチェックポイント作成"""
        self.checkpoints[task_id] = {
            'timestamp': datetime.utcnow().isoformat(),
            'original_message': message.copy(),
            'git_state': await self._capture_git_state()
        }
    
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
    
    async def _rollback_task(self, task_id: str):
        """タスクのロールバック"""
        if task_id not in self.checkpoints:
            return
        
        checkpoint = self.checkpoints[task_id]
        
        try:
            # Gitロールバック
            git_state = checkpoint.get('git_state', {})
            if git_state.get('commit'):
                await self.github_manager.reset_to_commit(git_state['commit'])
            
            self.logger.info(
                "Task rolled back successfully",
                task_id=task_id,
                checkpoint_time=checkpoint['timestamp']
            )
            
        except Exception as e:
            self.logger.error(
                "Rollback failed",
                task_id=task_id,
                error=str(e)
            )
    
    async def _periodic_cleanup(self):
        """定期的なクリーンアップ"""
        while self.running:
            try:
                # メモリクリーンアップ
                await self.memory_manager.check_and_cleanup()
                
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
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Redisに保存
        await self.cache_manager.set(
            "pm_worker_stats",
            stats,
            ttl=86400
        )
    
    async def get_worker_statistics(self) -> Dict[str, Any]:
        """ワーカー統計情報の取得"""
        base_stats = {
            'memory': {
                'usage_mb': self.memory_manager.get_memory_usage(),
                'usage_percent': f"{self.memory_manager.get_memory_percent():.1f}%",
                'max_mb': self.memory_manager.max_memory_mb
            },
            'tasks': {
                'active': len(self.phase_manager.active_tasks),
                'history_size': len(self.task_history),
                'checkpoints': len(self.checkpoints)
            },
            'phases': self.phase_manager.get_phase_statistics()
        }
        
        # エルダーシステム統計追加
        if self.elder_tree_enabled:
            elder_stats = await self._get_elder_system_statistics()
            base_stats['elder_integration'] = elder_stats
        
        return base_stats


# 実行用のメイン関数
async def main():
    """ワーカーのエントリーポイント"""
    import yaml
    
    # 設定読み込み
    config_path = PROJECT_ROOT / "config" / "config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # ワーカー起動
    worker = AsyncPMWorker(config)
    await worker.start()

    # ========== エルダーツリー統合メソッド ==========
    
    async def _consult_elder_guidance(self, context: TaskContext, message: Dict[str, Any]):
        """エルダーガイダンスの取得"""
        try:
            self.logger.info("🧙‍♂️ 4賢者システムにPM最適化指導を要請")
            
            # Task Sageに最適化相談
            task_guidance = await self._consult_task_sage_for_optimization(context, message)
            self.pm_optimization_state['task_sage_guidance'] = task_guidance
            
            # Knowledge Sageにパターン分析依頼
            knowledge_patterns = await self._get_knowledge_sage_patterns(context, message)
            self.pm_optimization_state['knowledge_sage_patterns'] = knowledge_patterns
            
            # Incident Sageに監視設定
            incident_monitoring = await self._setup_incident_sage_monitoring(context, message)
            self.pm_optimization_state['incident_sage_monitoring'] = incident_monitoring
            
            # RAG Sageにプロジェクトパターン分析
            rag_analysis = await self._get_rag_sage_project_analysis(context, message)
            self.pm_optimization_state['rag_sage_analysis'] = rag_analysis
            
            self.pm_optimization_state['last_elder_consultation'] = datetime.utcnow()
            
            self.logger.info("✅ エルダーガイダンス取得完了")
            
        except Exception as e:
            self.logger.error(f"❌ エルダーガイダンス取得失敗: {e}")
    
    async def _consult_task_sage_for_optimization(self, context: TaskContext, message: Dict[str, Any]) -> Dict[str, Any]:
        """Task SageにPM最適化を相談"""
        try:
            learning_request = {
                'type': 'pm_optimization',
                'data': {
                    'task_id': context.task_id,
                    'prompt': message.get('prompt', ''),
                    'current_phase': context.phase,
                    'iteration': context.iteration,
                    'complexity': self._assess_task_complexity(message)
                }
            }
            
            # 4賢者システムに学習セッション要求
            session_result = self.four_sages_integration.coordinate_learning_session(learning_request)
            
            # Task Sageの具体的な推奨事項を抽出
            task_recommendations = self._extract_task_sage_recommendations(session_result)
            
            return {
                'session_id': session_result.get('session_id'),
                'recommendations': task_recommendations,
                'optimization_suggestions': [
                    'フェーズ並列化の可能性',
                    'リソース配分の最適化',
                    'タスクの優先順位再評価',
                    'ボトルネック解消戦略'
                ],
                'confidence': session_result.get('consensus_reached', False)
            }
            
        except Exception as e:
            self.logger.error(f"Task Sage相談失敗: {e}")
            return {'error': str(e), 'recommendations': []}
    
    async def _get_knowledge_sage_patterns(self, context: TaskContext, message: Dict[str, Any]) -> Dict[str, Any]:
        """Knowledge Sageからプロジェクトパターンを取得"""
        try:
            # 類似プロジェクトパターンの検索
            pattern_request = {
                'type': 'pattern_analysis',
                'data': {
                    'task_type': message.get('task_type', 'pm_task'),
                    'domain': message.get('domain', 'software_development'),
                    'complexity': self._assess_task_complexity(message),
                    'requirements': self._extract_requirements(message)
                }
            }
            
            # Knowledge Sageに分析依頼
            pattern_result = self.four_sages_integration.facilitate_cross_sage_learning(pattern_request)
            
            return {
                'historical_patterns': [
                    'プロジェクト成功パターン',
                    'よくある失敗パターン',
                    'リスク軽減策',
                    '品質向上手法'
                ],
                'similar_projects': pattern_result.get('knowledge_transfers', {}),
                'best_practices': [
                    'イテレーション管理',
                    'ステークホルダー管理',
                    'リスク管理',
                    '品質保証'
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Knowledge Sage pattern取得失敗: {e}")
            return {'error': str(e), 'patterns': []}
    
    async def _setup_incident_sage_monitoring(self, context: TaskContext, message: Dict[str, Any]) -> Dict[str, Any]:
        """Incident Sageによる監視設定"""
        try:
            # PM プロセスの監視項目設定
            monitoring_config = {
                'task_id': context.task_id,
                'monitoring_points': [
                    'フェーズ実行時間',
                    'エラー発生率',
                    'リソース使用状況',
                    'タスク完了率'
                ],
                'alert_thresholds': {
                    'phase_duration_max': 3600,  # 1時間
                    'error_rate_max': 0.1,       # 10%
                    'memory_usage_max': 0.8,     # 80%
                    'task_failure_rate_max': 0.2 # 20%
                }
            }
            
            # Incident Sageに監視設定
            monitoring_result = await self._request_incident_sage_monitoring(monitoring_config)
            
            return {
                'monitoring_active': True,
                'monitoring_id': f"pm_monitor_{context.task_id}",
                'alert_endpoints': ['pm_worker', 'elder_council'],
                'escalation_rules': {
                    'critical': 'immediate_elder_notification',
                    'high': 'elder_council_review',
                    'medium': 'sage_consultation',
                    'low': 'standard_logging'
                }
            }
            
        except Exception as e:
            self.logger.error(f"Incident Sage監視設定失敗: {e}")
            return {'error': str(e), 'monitoring_active': False}
    
    async def _get_rag_sage_project_analysis(self, context: TaskContext, message: Dict[str, Any]) -> Dict[str, Any]:
        """RAG Sageによるプロジェクトパターン分析"""
        try:
            # プロジェクトコンテキストの分析
            analysis_request = {
                'type': 'project_context_analysis',
                'data': {
                    'prompt': message.get('prompt', ''),
                    'project_type': self._classify_project_type(message),
                    'requirements': self._extract_requirements(message),
                    'constraints': self._extract_constraints(message)
                }
            }
            
            # RAG Sageに分析依頼
            analysis_result = await self._request_rag_sage_analysis(analysis_request)
            
            return {
                'semantic_analysis': {
                    'project_category': analysis_result.get('category', 'unknown'),
                    'complexity_score': analysis_result.get('complexity', 0.5),
                    'risk_factors': analysis_result.get('risks', []),
                    'success_factors': analysis_result.get('success_factors', [])
                },
                'similar_contexts': analysis_result.get('similar_projects', []),
                'optimization_opportunities': [
                    'プロセス自動化',
                    'テンプレート活用',
                    'ベストプラクティス適用',
                    'リスク予防策'
                ]
            }
            
        except Exception as e:
            self.logger.error(f"RAG Sage分析失敗: {e}")
            return {'error': str(e), 'analysis': {}}
    
    async def _report_to_elders(self, context: TaskContext, result: Dict[str, Any]):
        """エルダーへの結果報告"""
        try:
            # Knowledge Sageへの結果報告
            await self._report_to_knowledge_sage(context, result)
            
            # プロジェクト成功度に基づいて追加報告
            success_rate = self._calculate_project_success_rate(result)
            
            if success_rate >= 0.9:
                # 高い成功率の場合、ベストプラクティスとして記録
                await self._record_best_practice(context, result)
            elif success_rate < 0.5:
                # 低い成功率の場合、改善提案を要求
                await self._request_improvement_suggestions(context, result)
            
            # エルダー評議会への定期報告
            await self._send_elder_council_report(context, result)
            
        except Exception as e:
            self.logger.error(f"エルダー報告失敗: {e}")
    
    async def _report_to_knowledge_sage(self, context: TaskContext, result: Dict[str, Any]):
        """Knowledge Sageへの結果報告"""
        try:
            report_data = {
                'task_id': context.task_id,
                'project_type': result.get('mode', 'unknown'),
                'outcome': result.get('status', 'unknown'),
                'duration': result.get('duration', 0),
                'phase_results': result.get('phase_results', {}),
                'lessons_learned': self._extract_lessons_learned(context, result),
                'performance_metrics': self._calculate_performance_metrics(result)
            }
            
            # 4賢者システムへの報告
            await self.four_sages_integration.report_to_claude_elder(
                'knowledge_sage',
                'project_completion_report',
                report_data
            )
            
            self.logger.info(f"📚 Knowledge Sage へのプロジェクト結果報告完了: {context.task_id}")
            
        except Exception as e:
            self.logger.error(f"Knowledge Sage報告失敗: {e}")
    
    async def _escalate_critical_issue(self, task_id: str, error: str, context: TaskContext):
        """重大な問題のIncident Sageへのエスカレーション"""
        try:
            escalation_data = {
                'task_id': task_id,
                'error_type': 'pm_critical_failure',
                'error_message': error,
                'context': {
                    'phase': context.phase,
                    'iteration': context.iteration,
                    'duration': (datetime.utcnow() - context.created_at).total_seconds()
                },
                'impact_assessment': {
                    'severity': 'high',
                    'affected_systems': ['pm_worker', 'task_processing'],
                    'user_impact': 'project_delivery_delay',
                    'business_impact': 'productivity_loss'
                },
                'suggested_actions': [
                    'Immediate task recovery',
                    'Root cause analysis',
                    'Process improvement',
                    'Prevention measures'
                ]
            }
            
            # Incident Sageへの緊急報告
            await self.four_sages_integration.escalate_to_grand_elder(
                'pm_critical_failure',
                'high',
                escalation_data
            )
            
            self.logger.critical(f"🚨 Incident Sage へ重大問題エスカレーション: {task_id}")
            
        except Exception as e:
            self.logger.error(f"重大問題エスカレーション失敗: {e}")
    
    async def _get_elder_system_statistics(self) -> Dict[str, Any]:
        """エルダーシステム統計取得"""
        try:
            stats = {
                'elder_tree_active': self.elder_tree_enabled,
                'pm_optimization_state': self.pm_optimization_state.copy(),
                'elder_consultations': {
                    'total_consultations': len(self.pm_optimization_state.get('elder_recommendations', [])),
                    'last_consultation': self.pm_optimization_state.get('last_elder_consultation'),
                    'success_rate': self._calculate_elder_guidance_success_rate()
                }
            }
            
            # 4賢者システムからの統計
            if self.four_sages_integration:
                four_sages_stats = await self.four_sages_integration.get_system_status()
                stats['four_sages_system'] = four_sages_stats
            
            # エルダー評議会システムからの統計
            if self.elder_council_summoner:
                council_stats = self.elder_council_summoner.get_system_status()
                stats['elder_council_system'] = council_stats
            
            return stats
            
        except Exception as e:
            self.logger.error(f"エルダー統計取得失敗: {e}")
            return {'error': str(e), 'elder_tree_active': False}
    
    # ========== ヘルパーメソッド ==========
    
    def _assess_task_complexity(self, message: Dict[str, Any]) -> float:
        """タスク複雑度評価"""
        complexity_indicators = {
            'multiple_files': 0.3,
            'database_operations': 0.2,
            'api_integrations': 0.2,
            'complex_logic': 0.3,
            'testing_required': 0.1
        }
        
        prompt = message.get('prompt', '').lower()
        complexity = 0.0
        
        for indicator, weight in complexity_indicators.items():
            if indicator.replace('_', ' ') in prompt:
                complexity += weight
        
        return min(complexity, 1.0)
    
    def _extract_requirements(self, message: Dict[str, Any]) -> List[str]:
        """要件抽出"""
        # 簡略化実装
        return ['基本機能実装', 'テスト作成', 'ドキュメント作成']
    
    def _extract_constraints(self, message: Dict[str, Any]) -> List[str]:
        """制約抽出"""
        # 簡略化実装
        return ['時間制約', 'リソース制約', '品質制約']
    
    def _classify_project_type(self, message: Dict[str, Any]) -> str:
        """プロジェクトタイプ分類"""
        prompt = message.get('prompt', '').lower()
        
        if 'web' in prompt or 'api' in prompt:
            return 'web_development'
        elif 'data' in prompt or 'analysis' in prompt:
            return 'data_analysis'
        elif 'test' in prompt:
            return 'testing'
        else:
            return 'general_development'
    
    def _calculate_project_success_rate(self, result: Dict[str, Any]) -> float:
        """プロジェクト成功率計算"""
        if result.get('status') == 'completed':
            return 0.9
        elif result.get('status') == 'failed':
            return 0.1
        else:
            return 0.5
    
    def _extract_lessons_learned(self, context: TaskContext, result: Dict[str, Any]) -> List[str]:
        """教訓抽出"""
        return [
            f"Phase {context.phase} completed successfully",
            f"Task duration: {result.get('duration', 0)} seconds",
            "Error handling worked properly"
        ]
    
    def _calculate_performance_metrics(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """パフォーマンスメトリクス計算"""
        return {
            'completion_time': result.get('duration', 0),
            'success_rate': 1.0 if result.get('status') == 'completed' else 0.0,
            'efficiency_score': 0.8
        }
    
    def _calculate_elder_guidance_success_rate(self) -> float:
        """エルダーガイダンス成功率計算"""
        recommendations = self.pm_optimization_state.get('elder_recommendations', [])
        if not recommendations:
            return 0.0
        
        successful = sum(1 for r in recommendations if r.get('applied', False))
        return successful / len(recommendations)
    
    def _extract_task_sage_recommendations(self, session_result: Dict[str, Any]) -> List[str]:
        """Task Sage推奨事項抽出"""
        # 簡略化実装
        return [
            'タスクの並列化を検討',
            'リソース使用量を最適化',
            'エラーハンドリングを強化',
            'フェーズ間のデータ共有を改善'
        ]
    
    async def _request_incident_sage_monitoring(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Incident Sage監視要求"""
        # 簡略化実装
        return {
            'monitoring_started': True,
            'monitoring_id': config.get('task_id'),
            'status': 'active'
        }
    
    async def _request_rag_sage_analysis(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """RAG Sage分析要求"""
        # 簡略化実装
        return {
            'category': 'software_development',
            'complexity': 0.6,
            'risks': ['技術的複雑さ', '時間制約'],
            'success_factors': ['明確な要件', '適切なテスト'],
            'similar_projects': ['project_a', 'project_b']
        }
    
    async def _record_best_practice(self, context: TaskContext, result: Dict[str, Any]):
        """ベストプラクティス記録"""
        best_practice = {
            'task_id': context.task_id,
            'success_factors': self._extract_success_factors(result),
            'recorded_at': datetime.utcnow().isoformat()
        }
        
        # Knowledge Sageに記録
        await self.four_sages_integration.report_to_claude_elder(
            'knowledge_sage',
            'best_practice_record',
            best_practice
        )
    
    async def _request_improvement_suggestions(self, context: TaskContext, result: Dict[str, Any]):
        """改善提案要求"""
        improvement_request = {
            'task_id': context.task_id,
            'issues': self._extract_issues(result),
            'requested_at': datetime.utcnow().isoformat()
        }
        
        # Task Sageに改善提案要求
        await self.four_sages_integration.report_to_claude_elder(
            'task_sage',
            'improvement_request',
            improvement_request
        )
    
    async def _send_elder_council_report(self, context: TaskContext, result: Dict[str, Any]):
        """エルダー評議会への報告"""
        council_report = {
            'task_id': context.task_id,
            'pm_worker_status': 'operational',
            'project_completion': result.get('status'),
            'elder_integration_status': 'active',
            'reported_at': datetime.utcnow().isoformat()
        }
        
        # エルダー評議会へ報告
        if self.elder_council_summoner:
            # 必要に応じて会議召集トリガーの評価
            await self._evaluate_council_trigger(council_report)
    
    async def _evaluate_council_trigger(self, report: Dict[str, Any]):
        """評議会トリガー評価"""
        # 重要な決定が必要な場合のみ評議会召集を検討
        if report.get('project_completion') == 'failed':
            self.elder_council_summoner.force_trigger_evaluation()
    
    def _extract_success_factors(self, result: Dict[str, Any]) -> List[str]:
        """成功要因抽出"""
        return [
            '適切なフェーズ管理',
            '効率的なリソース使用',
            '適切なエラーハンドリング'
        ]
    
    def _extract_issues(self, result: Dict[str, Any]) -> List[str]:
        """問題抽出"""
        return [
            '実行時間が長い',
            'エラー発生率が高い',
            'リソース使用量が多い'
        ]


# 実行用のメイン関数
async def main():
    """ワーカーのエントリーポイント"""
    import yaml
    
    # 設定読み込み
    config_path = PROJECT_ROOT / "config" / "config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # ワーカー起動
    worker = AsyncPMWorker(config)
    await worker.start()

if __name__ == "__main__":
    asyncio.run(main())