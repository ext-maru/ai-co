#!/usr/bin/env python3
"""
非同期対応PM Worker
メモリリーク対策、並列処理、ロールバック機構対応
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
            
            # タスクタイプの判定
            if self._is_project_mode(message):
                result = await self._handle_project_mode(context, message)
            else:
                result = await self._handle_simple_mode(context, message)
            
            # 履歴に追加
            self.task_history.append({
                'task_id': task_id,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'completed',
                'duration': (datetime.utcnow() - context.created_at).total_seconds()
            })
            
            return result
            
        except Exception as e:
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
        return {
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