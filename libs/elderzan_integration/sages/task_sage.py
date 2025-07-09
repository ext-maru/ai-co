#!/usr/bin/env python3
"""
PROJECT ELDERZAN - タスク賢者統合
タスク管理・計画・実行システム統合
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import uuid

from ...claude_task_tracker import ClaudeTaskTracker
from ...shared_enums import SageType, Priority

logger = logging.getLogger(__name__)


class TaskSageIntegration:
    """
    タスク賢者統合インターフェース
    
    タスク管理・計画・実行システムの統合管理
    - タスクライフサイクル管理
    - 優先順位決定
    - 進捗追跡
    - 計画最適化
    """
    
    def __init__(self, session_context, hybrid_storage, security_layer):
        """
        タスク賢者統合初期化
        
        Args:
            session_context: セッションコンテキスト管理
            hybrid_storage: ハイブリッドストレージ
            security_layer: セキュリティレイヤー
        """
        self.session_context = session_context
        self.hybrid_storage = hybrid_storage
        self.security_layer = security_layer
        
        # タスク管理システム
        self.task_tracker = ClaudeTaskTracker()
        
        # タスクメトリクス
        self.task_metrics = {
            'total_tasks_created': 0,
            'total_tasks_completed': 0,
            'average_completion_time': 0.0,
            'task_success_rate': 0.0,
            'priority_distribution': {
                'high': 0,
                'medium': 0,
                'low': 0
            }
        }
        
        # アクティブタスク
        self.active_tasks = {}
        
        # ステータス
        self.status = {
            'initialized': True,
            'active': True,
            'last_activity': datetime.now().isoformat(),
            'health_status': 'healthy'
        }
        
        logger.info("タスク賢者統合初期化完了")
    
    async def create_task(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        タスク作成
        
        Args:
            task_data: タスクデータ
            context: 実行コンテキスト
            
        Returns:
            str: タスクID
            
        Raises:
            PermissionError: 権限不足
            Exception: タスク作成エラー
        """
        try:
            # セキュリティチェック
            if not await self.security_layer.check_permission(context, 'task_create'):
                raise PermissionError("Task creation permission denied")
            
            # タスク処理
            processed_task = await self._process_task_data(task_data, context)
            
            # タスクトラッカーでタスク作成
            task_id = await self.task_tracker.create_task(processed_task)
            
            # HybridStorageに保存
            await self.hybrid_storage.store_task_data(processed_task, context)
            
            # アクティブタスク追加
            self.active_tasks[task_id] = {
                'task_data': processed_task,
                'created_at': datetime.now().isoformat(),
                'status': 'pending'
            }
            
            # セッションコンテキストに記録
            await self.session_context.add_sage_interaction(
                sage_type=SageType.TASK,
                operation='create_task',
                input_data=task_data,
                output_data={'task_id': task_id},
                success=True,
                processing_time=0.0,
                confidence_score=0.95
            )
            
            # メトリクス更新
            self.task_metrics['total_tasks_created'] += 1
            priority = processed_task.get('priority', 'medium')
            self.task_metrics['priority_distribution'][priority] += 1
            self.status['last_activity'] = datetime.now().isoformat()
            
            logger.info(f"タスク作成完了: {task_id}")
            return task_id
            
        except Exception as e:
            # エラー記録
            await self.session_context.add_sage_interaction(
                sage_type=SageType.TASK,
                operation='create_task',
                input_data=task_data,
                output_data={'error': str(e)},
                success=False,
                processing_time=0.0,
                confidence_score=0.0
            )
            logger.error(f"タスク作成エラー: {e}")
            raise
    
    async def update_task_status(self, task_id: str, status: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        タスク状態更新
        
        Args:
            task_id: タスクID
            status: 新しい状態
            context: 実行コンテキスト
            
        Returns:
            Dict[str, Any]: 更新後タスク情報
            
        Raises:
            PermissionError: 権限不足
            Exception: タスク更新エラー
        """
        try:
            # セキュリティチェック
            if not await self.security_layer.check_permission(context, 'task_update'):
                raise PermissionError("Task update permission denied")
            
            # タスク状態更新
            task_info = await self.task_tracker.update_task_status(task_id, status)
            
            # HybridStorageに更新保存
            await self.hybrid_storage.update_task_status(task_id, status, context)
            
            # アクティブタスク更新
            if task_id in self.active_tasks:
                self.active_tasks[task_id]['status'] = status
                self.active_tasks[task_id]['updated_at'] = datetime.now().isoformat()
                
                # 完了時の処理
                if status == 'completed':
                    await self._handle_task_completion(task_id, context)
            
            # セッションコンテキストに記録
            await self.session_context.add_sage_interaction(
                sage_type=SageType.TASK,
                operation='update_task_status',
                input_data={'task_id': task_id, 'status': status},
                output_data=task_info,
                success=True,
                processing_time=0.0,
                confidence_score=0.9
            )
            
            self.status['last_activity'] = datetime.now().isoformat()
            
            logger.info(f"タスク状態更新完了: {task_id} -> {status}")
            return task_info
            
        except Exception as e:
            # エラー記録
            await self.session_context.add_sage_interaction(
                sage_type=SageType.TASK,
                operation='update_task_status',
                input_data={'task_id': task_id, 'status': status},
                output_data={'error': str(e)},
                success=False,
                processing_time=0.0,
                confidence_score=0.0
            )
            logger.error(f"タスク状態更新エラー: {e}")
            raise
    
    async def get_task_status(self, task_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        タスク状態取得
        
        Args:
            task_id: タスクID
            context: 実行コンテキスト
            
        Returns:
            Dict[str, Any]: タスク状態
            
        Raises:
            PermissionError: 権限不足
            Exception: タスク取得エラー
        """
        try:
            # セキュリティチェック
            if not await self.security_layer.check_permission(context, 'task_read'):
                raise PermissionError("Task access permission denied")
            
            # タスク状態取得
            task_status = await self.task_tracker.get_task_status(task_id)
            
            # アクティブタスク情報統合
            if task_id in self.active_tasks:
                task_status.update(self.active_tasks[task_id])
            
            # セッションコンテキストに記録
            await self.session_context.add_sage_interaction(
                sage_type=SageType.TASK,
                operation='get_task_status',
                input_data={'task_id': task_id},
                output_data={'status': task_status.get('status', 'unknown')},
                success=True,
                processing_time=0.0,
                confidence_score=0.9
            )
            
            self.status['last_activity'] = datetime.now().isoformat()
            
            logger.info(f"タスク状態取得完了: {task_id}")
            return task_status
            
        except Exception as e:
            # エラー記録
            await self.session_context.add_sage_interaction(
                sage_type=SageType.TASK,
                operation='get_task_status',
                input_data={'task_id': task_id},
                output_data={'error': str(e)},
                success=False,
                processing_time=0.0,
                confidence_score=0.0
            )
            logger.error(f"タスク状態取得エラー: {e}")
            raise
    
    async def prioritize_tasks(self, task_list: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        タスク優先順位決定
        
        Args:
            task_list: タスクIDリスト
            context: 実行コンテキスト
            
        Returns:
            List[Dict[str, Any]]: 優先順位付きタスクリスト
            
        Raises:
            PermissionError: 権限不足
            Exception: 優先順位決定エラー
        """
        try:
            # セキュリティチェック
            if not await self.security_layer.check_permission(context, 'task_prioritize'):
                raise PermissionError("Task prioritization permission denied")
            
            # 各タスクの詳細情報取得
            task_details = []
            for task_id in task_list:
                task_info = await self.task_tracker.get_task_status(task_id)
                task_details.append(task_info)
            
            # 優先順位計算
            prioritized_tasks = await self._calculate_task_priorities(task_details, context)
            
            # HybridStorageに優先順位保存
            await self.hybrid_storage.store_task_priorities(prioritized_tasks, context)
            
            # セッションコンテキストに記録
            await self.session_context.add_sage_interaction(
                sage_type=SageType.TASK,
                operation='prioritize_tasks',
                input_data={'task_count': len(task_list)},
                output_data={'prioritized_count': len(prioritized_tasks)},
                success=True,
                processing_time=0.0,
                confidence_score=0.85
            )
            
            self.status['last_activity'] = datetime.now().isoformat()
            
            logger.info(f"タスク優先順位決定完了: {len(prioritized_tasks)}件")
            return prioritized_tasks
            
        except Exception as e:
            # エラー記録
            await self.session_context.add_sage_interaction(
                sage_type=SageType.TASK,
                operation='prioritize_tasks',
                input_data={'task_count': len(task_list)},
                output_data={'error': str(e)},
                success=False,
                processing_time=0.0,
                confidence_score=0.0
            )
            logger.error(f"タスク優先順位決定エラー: {e}")
            raise
    
    async def handle_notification(self, notification_data: Dict[str, Any]):
        """
        通知ハンドリング
        
        Args:
            notification_data: 通知データ
        """
        try:
            event_type = notification_data.get('event_type')
            session_id = notification_data.get('session_id')
            
            # イベントタイプに応じた処理
            if event_type == 'session_created':
                await self._handle_session_created(session_id, notification_data)
            elif event_type == 'session_updated':
                await self._handle_session_updated(session_id, notification_data)
            elif event_type == 'session_deleted':
                await self._handle_session_deleted(session_id, notification_data)
            
            self.status['last_activity'] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"通知ハンドリングエラー: {e}")
            self.status['health_status'] = 'warning'
    
    async def get_status(self) -> Dict[str, Any]:
        """
        タスク賢者状態取得
        
        Returns:
            Dict[str, Any]: 状態情報
        """
        return {
            'sage_type': 'task',
            'status': self.status,
            'metrics': self.task_metrics,
            'active_tasks_count': len(self.active_tasks),
            'task_tracker_status': await self.task_tracker.get_status(),
            'timestamp': datetime.now().isoformat()
        }
    
    async def _process_task_data(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        タスクデータ処理
        
        Args:
            task_data: タスクデータ
            context: 実行コンテキスト
            
        Returns:
            Dict[str, Any]: 処理済みタスクデータ
        """
        processed_data = {
            'id': str(uuid.uuid4()),
            'title': task_data.get('title', ''),
            'description': task_data.get('description', ''),
            'priority': task_data.get('priority', 'medium'),
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'context': context,
            'metadata': task_data.get('metadata', {}),
            'dependencies': task_data.get('dependencies', []),
            'estimated_duration': task_data.get('estimated_duration', 0),
            'tags': task_data.get('tags', [])
        }
        
        # タスク分類
        processed_data['category'] = await self._classify_task(processed_data)
        
        # 緊急度評価
        processed_data['urgency_score'] = await self._calculate_urgency_score(processed_data)
        
        # 複雑度評価
        processed_data['complexity_score'] = await self._calculate_complexity_score(processed_data)
        
        return processed_data
    
    async def _classify_task(self, task_data: Dict[str, Any]) -> str:
        """
        タスク分類
        
        Args:
            task_data: タスクデータ
            
        Returns:
            str: 分類結果
        """
        title = task_data.get('title', '').lower()
        description = task_data.get('description', '').lower()
        
        # 簡単な分類ロジック
        if 'bug' in title or 'error' in title or 'fix' in title:
            return 'bug_fix'
        elif 'feature' in title or 'implement' in title:
            return 'feature_development'
        elif 'test' in title or 'テスト' in title:
            return 'testing'
        elif 'design' in title or '設計' in title:
            return 'design'
        elif 'document' in title or 'doc' in title:
            return 'documentation'
        else:
            return 'general'
    
    async def _calculate_urgency_score(self, task_data: Dict[str, Any]) -> float:
        """
        緊急度評価
        
        Args:
            task_data: タスクデータ
            
        Returns:
            float: 緊急度スコア (0.0-1.0)
        """
        base_score = 0.5
        
        # 優先度による調整
        priority = task_data.get('priority', 'medium')
        if priority == 'high':
            base_score += 0.3
        elif priority == 'low':
            base_score -= 0.2
        
        # カテゴリーによる調整
        category = task_data.get('category', 'general')
        if category == 'bug_fix':
            base_score += 0.2
        elif category == 'feature_development':
            base_score += 0.1
        
        # 依存関係による調整
        dependencies = task_data.get('dependencies', [])
        if len(dependencies) > 0:
            base_score += 0.1
        
        return max(0.0, min(1.0, base_score))
    
    async def _calculate_complexity_score(self, task_data: Dict[str, Any]) -> float:
        """
        複雑度評価
        
        Args:
            task_data: タスクデータ
            
        Returns:
            float: 複雑度スコア (0.0-1.0)
        """
        base_score = 0.3
        
        # 推定時間による調整
        estimated_duration = task_data.get('estimated_duration', 0)
        if estimated_duration > 0:
            base_score += min(0.4, estimated_duration / 10.0)
        
        # 依存関係による調整
        dependencies = task_data.get('dependencies', [])
        base_score += min(0.3, len(dependencies) * 0.1)
        
        return max(0.0, min(1.0, base_score))
    
    async def _calculate_task_priorities(self, task_details: List[Dict[str, Any]], 
                                       context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        タスク優先順位計算
        
        Args:
            task_details: タスク詳細リスト
            context: 実行コンテキスト
            
        Returns:
            List[Dict[str, Any]]: 優先順位付きタスクリスト
        """
        prioritized_tasks = []
        
        for task in task_details:
            # 優先度スコア計算
            urgency_score = task.get('urgency_score', 0.5)
            complexity_score = task.get('complexity_score', 0.3)
            
            # 総合優先度計算
            priority_score = (urgency_score * 0.7) + (complexity_score * 0.3)
            
            prioritized_task = {
                'task_id': task.get('id'),
                'title': task.get('title'),
                'priority_score': priority_score,
                'urgency_score': urgency_score,
                'complexity_score': complexity_score,
                'recommended_order': 0  # 後で設定
            }
            
            prioritized_tasks.append(prioritized_task)
        
        # 優先度スコア順にソート
        prioritized_tasks.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # 推奨順序設定
        for i, task in enumerate(prioritized_tasks):
            task['recommended_order'] = i + 1
        
        return prioritized_tasks
    
    async def _handle_task_completion(self, task_id: str, context: Dict[str, Any]):
        """
        タスク完了処理
        
        Args:
            task_id: タスクID
            context: 実行コンテキスト
        """
        task_info = self.active_tasks.get(task_id)
        if task_info:
            # 完了時間計算
            created_at = datetime.fromisoformat(task_info['created_at'])
            completion_time = (datetime.now() - created_at).total_seconds()
            
            # メトリクス更新
            self.task_metrics['total_tasks_completed'] += 1
            self.task_metrics['average_completion_time'] = (
                (self.task_metrics['average_completion_time'] * (self.task_metrics['total_tasks_completed'] - 1) + 
                 completion_time) / self.task_metrics['total_tasks_completed']
            )
            
            # 成功率計算
            if self.task_metrics['total_tasks_created'] > 0:
                self.task_metrics['task_success_rate'] = (
                    self.task_metrics['total_tasks_completed'] / self.task_metrics['total_tasks_created']
                )
            
            # アクティブタスクから削除
            del self.active_tasks[task_id]
            
            logger.info(f"タスク完了処理: {task_id}, 完了時間: {completion_time:.2f}秒")
    
    async def _handle_session_created(self, session_id: str, notification_data: Dict[str, Any]):
        """セッション作成通知処理"""
        # 新しいセッションのためのタスク準備
        await self.task_tracker.prepare_session_tasks(session_id)
        logger.info(f"タスク賢者: セッション作成処理完了 {session_id}")
    
    async def _handle_session_updated(self, session_id: str, notification_data: Dict[str, Any]):
        """セッション更新通知処理"""
        # セッションタスクの更新
        await self.task_tracker.update_session_tasks(session_id)
        logger.info(f"タスク賢者: セッション更新処理完了 {session_id}")
    
    async def _handle_session_deleted(self, session_id: str, notification_data: Dict[str, Any]):
        """セッション削除通知処理"""
        # セッションタスクのクリーンアップ
        await self.task_tracker.cleanup_session_tasks(session_id)
        logger.info(f"タスク賢者: セッション削除処理完了 {session_id}")


# エクスポート
__all__ = ['TaskSageIntegration']