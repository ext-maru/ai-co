#!/usr/bin/env python3
"""
PROJECT ELDERZAN - ナレッジ賢者統合
知識永続化・検索・進化システム統合
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import uuid

from ...enhanced_rag_manager import EnhancedRAGManager
from ...shared_enums import SageType

logger = logging.getLogger(__name__)


class KnowledgeSageIntegration:
    """
    ナレッジ賢者統合インターフェース
    
    知識永続化・検索・進化システムの統合管理
    - 知識ベース管理
    - セッション知識永続化
    - RAG検索統合
    - 知識進化追跡
    """
    
    def __init__(self, session_context, hybrid_storage, security_layer):
        """
        ナレッジ賢者統合初期化
        
        Args:
            session_context: セッションコンテキスト管理
            hybrid_storage: ハイブリッドストレージ
            security_layer: セキュリティレイヤー
        """
        self.session_context = session_context
        self.hybrid_storage = hybrid_storage
        self.security_layer = security_layer
        
        # 知識ベース管理
        self.knowledge_base = EnhancedRAGManager()
        
        # 知識メトリクス
        self.knowledge_metrics = {
            'total_knowledge_stored': 0,
            'total_searches': 0,
            'average_search_time': 0.0,
            'knowledge_retention_rate': 0.0
        }
        
        # ステータス
        self.status = {
            'initialized': True,
            'active': True,
            'last_activity': datetime.now().isoformat(),
            'health_status': 'healthy'
        }
        
        logger.info("ナレッジ賢者統合初期化完了")
    
    async def store_knowledge(self, knowledge_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        知識永続化
        
        Args:
            knowledge_data: 知識データ
            context: 実行コンテキスト
            
        Returns:
            str: 知識ID
            
        Raises:
            PermissionError: 権限不足
            Exception: 知識永続化エラー
        """
        try:
            # セキュリティチェック
            if not await self.security_layer.check_permission(context, 'knowledge_store'):
                raise PermissionError("Knowledge storage permission denied")
            
            # 知識処理
            processed_knowledge = await self._process_knowledge(knowledge_data, context)
            
            # RAGマネージャーで知識処理
            knowledge_id = await self.knowledge_base.store_knowledge(processed_knowledge)
            
            # HybridStorageに保存
            await self.hybrid_storage.store_knowledge(processed_knowledge, context)
            
            # セッションコンテキストに記録
            await self.session_context.add_sage_interaction(
                sage_type=SageType.KNOWLEDGE,
                operation='store_knowledge',
                input_data=knowledge_data,
                output_data={'knowledge_id': knowledge_id},
                success=True,
                processing_time=0.0,  # 実際の処理時間を記録
                confidence_score=0.95
            )
            
            # メトリクス更新
            self.knowledge_metrics['total_knowledge_stored'] += 1
            self.status['last_activity'] = datetime.now().isoformat()
            
            logger.info(f"知識永続化完了: {knowledge_id}")
            return knowledge_id
            
        except Exception as e:
            # エラー記録
            await self.session_context.add_sage_interaction(
                sage_type=SageType.KNOWLEDGE,
                operation='store_knowledge',
                input_data=knowledge_data,
                output_data={'error': str(e)},
                success=False,
                processing_time=0.0,
                confidence_score=0.0
            )
            logger.error(f"知識永続化エラー: {e}")
            raise
    
    async def retrieve_knowledge(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        知識検索
        
        Args:
            query: 検索クエリ
            context: 実行コンテキスト
            
        Returns:
            Dict[str, Any]: 検索結果
            
        Raises:
            PermissionError: 権限不足
            Exception: 知識検索エラー
        """
        start_time = datetime.now()
        
        try:
            # セキュリティチェック
            if not await self.security_layer.check_permission(context, 'knowledge_read'):
                raise PermissionError("Knowledge access permission denied")
            
            # 知識検索
            search_results = await self.knowledge_base.search_knowledge(query, context)
            
            # HybridStorageからキャッシュ取得
            cached_results = await self.hybrid_storage.get_cached_search_results(query, context)
            
            # 結果統合
            combined_results = await self._combine_search_results(search_results, cached_results)
            
            # 処理時間計算
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # セッションコンテキストに記録
            await self.session_context.add_sage_interaction(
                sage_type=SageType.KNOWLEDGE,
                operation='retrieve_knowledge',
                input_data={'query': query},
                output_data={'results_count': len(combined_results)},
                success=True,
                processing_time=processing_time,
                confidence_score=self._calculate_search_confidence(combined_results)
            )
            
            # メトリクス更新
            self.knowledge_metrics['total_searches'] += 1
            self.knowledge_metrics['average_search_time'] = (
                (self.knowledge_metrics['average_search_time'] * (self.knowledge_metrics['total_searches'] - 1) + 
                 processing_time) / self.knowledge_metrics['total_searches']
            )
            self.status['last_activity'] = datetime.now().isoformat()
            
            logger.info(f"知識検索完了: {query}, {len(combined_results)}件")
            return combined_results
            
        except Exception as e:
            # エラー記録
            processing_time = (datetime.now() - start_time).total_seconds()
            await self.session_context.add_sage_interaction(
                sage_type=SageType.KNOWLEDGE,
                operation='retrieve_knowledge',
                input_data={'query': query},
                output_data={'error': str(e)},
                success=False,
                processing_time=processing_time,
                confidence_score=0.0
            )
            logger.error(f"知識検索エラー: {e}")
            raise
    
    async def evolve_knowledge(self, knowledge_id: str, evolution_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        知識進化
        
        Args:
            knowledge_id: 知識ID
            evolution_data: 進化データ
            context: 実行コンテキスト
            
        Returns:
            Dict[str, Any]: 進化結果
            
        Raises:
            PermissionError: 権限不足
            Exception: 知識進化エラー
        """
        try:
            # セキュリティチェック
            if not await self.security_layer.check_permission(context, 'knowledge_evolve'):
                raise PermissionError("Knowledge evolution permission denied")
            
            # 知識進化処理
            evolution_result = await self.knowledge_base.evolve_knowledge(knowledge_id, evolution_data)
            
            # HybridStorageに進化履歴保存
            await self.hybrid_storage.store_knowledge_evolution(knowledge_id, evolution_data, context)
            
            # セッションコンテキストに記録
            await self.session_context.add_sage_interaction(
                sage_type=SageType.KNOWLEDGE,
                operation='evolve_knowledge',
                input_data={'knowledge_id': knowledge_id, 'evolution_data': evolution_data},
                output_data=evolution_result,
                success=True,
                processing_time=0.0,
                confidence_score=0.9
            )
            
            self.status['last_activity'] = datetime.now().isoformat()
            
            logger.info(f"知識進化完了: {knowledge_id}")
            return evolution_result
            
        except Exception as e:
            # エラー記録
            await self.session_context.add_sage_interaction(
                sage_type=SageType.KNOWLEDGE,
                operation='evolve_knowledge',
                input_data={'knowledge_id': knowledge_id, 'evolution_data': evolution_data},
                output_data={'error': str(e)},
                success=False,
                processing_time=0.0,
                confidence_score=0.0
            )
            logger.error(f"知識進化エラー: {e}")
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
        ナレッジ賢者状態取得
        
        Returns:
            Dict[str, Any]: 状態情報
        """
        return {
            'sage_type': 'knowledge',
            'status': self.status,
            'metrics': self.knowledge_metrics,
            'knowledge_base_status': await self.knowledge_base.get_status(),
            'timestamp': datetime.now().isoformat()
        }
    
    async def _process_knowledge(self, knowledge_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        知識処理
        
        Args:
            knowledge_data: 知識データ
            context: 実行コンテキスト
            
        Returns:
            Dict[str, Any]: 処理済み知識データ
        """
        processed_data = {
            'id': str(uuid.uuid4()),
            'content': knowledge_data.get('content', ''),
            'metadata': knowledge_data.get('metadata', {}),
            'context': context,
            'timestamp': datetime.now().isoformat(),
            'priority': knowledge_data.get('priority', 'medium'),
            'tags': knowledge_data.get('tags', []),
            'source': knowledge_data.get('source', 'unknown')
        }
        
        # 知識分類
        processed_data['category'] = await self._classify_knowledge(processed_data)
        
        # 知識重要度評価
        processed_data['importance_score'] = await self._calculate_importance_score(processed_data)
        
        return processed_data
    
    async def _classify_knowledge(self, knowledge_data: Dict[str, Any]) -> str:
        """
        知識分類
        
        Args:
            knowledge_data: 知識データ
            
        Returns:
            str: 分類結果
        """
        # 簡単な分類ロジック（実際の実装では機械学習モデルを使用）
        content = knowledge_data.get('content', '').lower()
        
        if 'error' in content or 'exception' in content:
            return 'error_knowledge'
        elif 'test' in content or 'テスト' in content:
            return 'test_knowledge'
        elif 'api' in content or 'API' in content:
            return 'api_knowledge'
        elif 'design' in content or '設計' in content:
            return 'design_knowledge'
        else:
            return 'general_knowledge'
    
    async def _calculate_importance_score(self, knowledge_data: Dict[str, Any]) -> float:
        """
        知識重要度評価
        
        Args:
            knowledge_data: 知識データ
            
        Returns:
            float: 重要度スコア (0.0-1.0)
        """
        # 簡単な重要度計算ロジック
        base_score = 0.5
        
        # 優先度による調整
        priority = knowledge_data.get('priority', 'medium')
        if priority == 'high':
            base_score += 0.3
        elif priority == 'low':
            base_score -= 0.2
        
        # カテゴリーによる調整
        category = knowledge_data.get('category', 'general_knowledge')
        if category == 'error_knowledge':
            base_score += 0.2
        elif category == 'design_knowledge':
            base_score += 0.1
        
        return max(0.0, min(1.0, base_score))
    
    async def _combine_search_results(self, search_results: List[Dict[str, Any]], 
                                    cached_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        検索結果統合
        
        Args:
            search_results: 新規検索結果
            cached_results: キャッシュ結果
            
        Returns:
            List[Dict[str, Any]]: 統合結果
        """
        # 重複排除と統合
        combined = {}
        
        # 検索結果処理
        for result in search_results:
            result_id = result.get('id')
            if result_id:
                combined[result_id] = result
        
        # キャッシュ結果処理
        for result in cached_results:
            result_id = result.get('id')
            if result_id and result_id not in combined:
                combined[result_id] = result
        
        # スコア順にソート
        return sorted(combined.values(), key=lambda x: x.get('score', 0.0), reverse=True)
    
    async def _calculate_search_confidence(self, search_results: List[Dict[str, Any]]) -> float:
        """
        検索信頼度計算
        
        Args:
            search_results: 検索結果
            
        Returns:
            float: 信頼度スコア (0.0-1.0)
        """
        if not search_results:
            return 0.0
        
        # 上位結果の平均スコア
        top_results = search_results[:5]  # 上位5件
        average_score = sum(result.get('score', 0.0) for result in top_results) / len(top_results)
        
        # 結果数による調整
        result_count_factor = min(1.0, len(search_results) / 10.0)
        
        return average_score * result_count_factor
    
    async def _handle_session_created(self, session_id: str, notification_data: Dict[str, Any]):
        """セッション作成通知処理"""
        # 新しいセッションのための知識準備
        await self.knowledge_base.prepare_session_knowledge(session_id)
        logger.info(f"ナレッジ賢者: セッション作成処理完了 {session_id}")
    
    async def _handle_session_updated(self, session_id: str, notification_data: Dict[str, Any]):
        """セッション更新通知処理"""
        # セッション知識の更新
        await self.knowledge_base.update_session_knowledge(session_id)
        logger.info(f"ナレッジ賢者: セッション更新処理完了 {session_id}")
    
    async def _handle_session_deleted(self, session_id: str, notification_data: Dict[str, Any]):
        """セッション削除通知処理"""
        # セッション知識のクリーンアップ
        await self.knowledge_base.cleanup_session_knowledge(session_id)
        logger.info(f"ナレッジ賢者: セッション削除処理完了 {session_id}")


# エクスポート
__all__ = ['KnowledgeSageIntegration']