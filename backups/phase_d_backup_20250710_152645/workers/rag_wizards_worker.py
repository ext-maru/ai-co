#!/usr/bin/env python3
"""
🌳 Elder Tree Integrated RAGWizardsWorker
RAGエルダーウィザードシステムのワーカー - Elders Guild統合版

Elders Guild Integration:
- 🌟 Grand Elder maru oversight
- 🤖 Claude Elder execution guidance
- 🧙‍♂️ Four Sages wisdom consultation
- 🏛️ Elder Council decision support
- ⚔️ Elder Servants coordination

Part of the Elder Tree Hierarchy for RAG wizards processing
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.base_worker import BaseWorker
from libs.rag_elder_wizards import (
    RAGElderWizardsOrchestrator,
    KnowledgeGap,
    KnowledgeGapType
)
from libs.rag_grimoire_integration import RagGrimoireIntegration, RagGrimoireConfig
from libs.rag_manager import RAGManager
from libs.enhanced_rag_manager import EnhancedRAGManager

# Elder Tree Integration imports
try:
    from libs.four_sages_integration import FourSagesIntegration
    from libs.elder_council_summoner import ElderCouncilSummoner
    from libs.elder_tree_hierarchy import get_elder_tree, ElderMessage, ElderRank
    ELDER_TREE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Elder Tree integration not available: {e}")
    FourSagesIntegration = None
    ElderCouncilSummoner = None
    get_elder_tree = None
    ElderMessage = None
    ElderRank = None
    ELDER_TREE_AVAILABLE = False


class RAGWizardsWorker(BaseWorker):
    """RAG Elder Wizards Worker"""
    
    def __init__(self, worker_id="rag_wizards"):
        """初期化"""
        super().__init__(
            worker_type="rag_wizards",
            worker_id=worker_id
        )
        
        # RAGシステムの初期化
        self.rag_manager = RAGManager()
        try:
            self.enhanced_rag = EnhancedRAGManager()
        except Exception as e:
            self.logger.warning(f"Enhanced RAG initialization failed: {e}")
            self.enhanced_rag = None
        
        # RAG Grimoire Integration setup
        self.rag_config = RagGrimoireConfig(
            database_url="postgresql://localhost/grimoire",
            search_threshold=0.7,
            max_search_results=10
        )
        self.rag_integration = None
            
        # ウィザードオーケストレータの初期化
        self.wizards_orchestrator = None
        self.background_tasks = []
        
    async def start(self):
        """ワーカー開始"""
        self.logger.info("🧙 RAG Elder Wizards Worker starting...")
        
        # Initialize RAG Grimoire Integration
        try:
            self.rag_integration = RagGrimoireIntegration(self.rag_config)
            await self.rag_integration.initialize()
            self.logger.info("🧙 RAG Grimoire Integration initialized for wizards")
        except Exception as e:
            self.logger.error(f"Failed to initialize RAG Grimoire Integration: {e}")
            self.rag_integration = None
        
        # ウィザードオーケストレータを初期化
        self.wizards_orchestrator = RAGElderWizardsOrchestrator()
        await self.wizards_orchestrator.start()
        
        # 通常のワーカー処理を開始
        await super().start()
        
    async def stop(self):
        """ワーカー停止"""
        self.logger.info("🛑 Stopping RAG Elder Wizards Worker...")
        
        # RAG Grimoire Integration cleanup
        if self.rag_integration:
            try:
                await self.rag_integration.cleanup()
                self.logger.info("🧙 RAG Grimoire Integration cleaned up")
            except Exception as e:
                self.logger.error(f"Error cleaning up RAG integration: {e}")
        
        # ウィザードオーケストレータを停止
        if self.wizards_orchestrator:
            await self.wizards_orchestrator.stop()
            
        # バックグラウンドタスクをキャンセル
        for task in self.background_tasks:
            if not task.done():
                task.cancel()
                
        await super().stop()
        
    async def process_message(self, message: Dict) -> Dict:
        """メッセージ処理"""
        task_type = message.get('task_type', 'knowledge_gap')
        
        try:
            if task_type == 'knowledge_gap':
                # 特定の知識ギャップの処理
                result = await self._process_knowledge_gap(message)
                
            elif task_type == 'manual_learning':
                # 手動学習トリガー
                result = await self._trigger_manual_learning(message)
                
            elif task_type == 'status_report':
                # ステータスレポート生成
                result = await self._generate_status_report()
                
            else:
                # 通常のRAGクエリ処理
                result = await self._process_rag_query(message)
                
            # 結果を送信
            await self.send_result({
                'task_id': message.get('task_id'),
                'result': result,
                'status': 'completed',
                'worker': self.worker_id
            })
            
            # アクティビティを報告（アイドルタイマーリセット）
            if self.wizards_orchestrator:
                self.wizards_orchestrator.learning_engine.report_activity()
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            await self.send_result({
                'task_id': message.get('task_id'),
                'error': str(e),
                'status': 'failed',
                'worker': self.worker_id
            })
            
        return result
        
    async def _process_knowledge_gap(self, message: Dict) -> Dict:
        """知識ギャップの処理"""
        gap_data = message.get('gap', {})
        
        # KnowledgeGapオブジェクトを作成
        gap = KnowledgeGap(
            gap_id=gap_data.get('gap_id', f"manual_{datetime.now().timestamp()}"),
            gap_type=KnowledgeGapType(gap_data.get('gap_type', 'missing_context')),
            topic=gap_data.get('topic', 'unknown'),
            description=gap_data.get('description', 'Manual gap processing'),
            priority=gap_data.get('priority', 0.5),
            detected_at=datetime.now(),
            context=gap_data.get('context', {})
        )
        
        # ウィザードで処理
        enrichment_result = await self.wizards_orchestrator.manual_trigger_learning(gap.topic)
        
        return {
            'gap_id': gap.gap_id,
            'enrichment_result': enrichment_result.__dict__ if enrichment_result else None,
            'status': 'processed'
        }
        
    async def _trigger_manual_learning(self, message: Dict) -> Dict:
        """手動学習のトリガー"""
        topic = message.get('topic')
        
        self.logger.info(f"🎯 Manual learning triggered for topic: {topic}")
        
        # ウィザードオーケストレータで学習を実行
        result = await self.wizards_orchestrator.manual_trigger_learning(topic)
        
        # Store the learning result in unified RAG system
        if result and self.rag_integration:
            try:
                knowledge_content = f"Manual learning completed for topic: {topic}\n"
                knowledge_content += f"Result: {str(result)}\n"
                knowledge_content += f"Timestamp: {datetime.now().isoformat()}"
                
                await self._store_wizard_knowledge(
                    topic=topic,
                    content=knowledge_content,
                    metadata={
                        'learning_type': 'manual_trigger',
                        'result_available': True,
                        'wizard_id': self.worker_id
                    }
                )
            except Exception as e:
                self.logger.warning(f"Failed to store learning result: {e}")
        
        return {
            'topic': topic,
            'learning_result': result.__dict__ if result else None,
            'timestamp': datetime.now().isoformat()
        }
        
    async def _generate_status_report(self) -> Dict:
        """ステータスレポート生成"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'wizards_status': 'active' if self.wizards_orchestrator else 'inactive',
            'statistics': {}
        }
        
        if self.wizards_orchestrator:
            # 検出されたギャップの統計
            detector = self.wizards_orchestrator.gap_detector
            report['statistics']['detected_gaps'] = len(detector.detected_gaps)
            
            # ウィザードの状態
            wizard_states = []
            for wizard in self.wizards_orchestrator.hunter_wizards:
                wizard_states.append({
                    'id': wizard.wizard_id,
                    'state': wizard.state.value
                })
            report['wizard_states'] = wizard_states
            
            # 学習エンジンの状態
            learning_engine = self.wizards_orchestrator.learning_engine
            report['learning_engine'] = {
                'is_learning': learning_engine.is_learning,
                'last_activity': learning_engine.last_activity.isoformat(),
                'queue_size': len(learning_engine.learning_queue)
            }
            
        return report
        
    async def _process_rag_query(self, message: Dict) -> Dict:
        """通常のRAGクエリ処理 with unified grimoire integration"""
        query = message.get('query', '')
        
        # Unified RAG search using grimoire integration
        unified_results = None
        if self.rag_integration:
            try:
                unified_results = await self.rag_integration.search_unified(
                    query=query,
                    limit=10,
                    threshold=self.rag_config.search_threshold
                )
            except Exception as e:
                self.logger.warning(f"Unified RAG search failed: {e}")
        
        # Fallback to legacy systems if unified search fails
        basic_rag_results = None
        enhanced_results = None
        
        if not unified_results:
            # 基本RAGで検索
            basic_rag_results = self.rag_manager.get_related_history(query)
            
            # Enhanced RAGが利用可能な場合は追加検索
            if self.enhanced_rag:
                try:
                    enhanced_results = await self._search_with_enhanced_rag(query)
                except Exception as e:
                    self.logger.warning(f"Enhanced RAG search failed: {e}")
                
        # ウィザードシステムにも問い合わせ
        wizard_insights = await self._get_wizard_insights(query)
        
        return {
            'query': query,
            'unified_rag_results': unified_results,
            'basic_rag_results': basic_rag_results,
            'enhanced_rag_results': enhanced_results,
            'wizard_insights': wizard_insights,
            'timestamp': datetime.now().isoformat()
        }
        
    async def _search_with_enhanced_rag(self, query: str) -> List[Dict]:
        """Enhanced RAGでの検索"""
        if not self.enhanced_rag:
            return []
            
        try:
            # ベクトル検索
            vector_results = self.enhanced_rag.vector_search(query, k=5)
            
            # 意味的検索
            semantic_results = self.enhanced_rag.semantic_search(query, k=5)
            
            # 結果を統合
            combined_results = []
            for result in vector_results + semantic_results:
                combined_results.append({
                    'content': result.content,
                    'score': result.similarity_score,
                    'source': result.source,
                    'metadata': result.metadata
                })
                
            return combined_results
            
        except Exception as e:
            self.logger.error(f"Enhanced RAG search error: {e}")
            return []
            
    async def _get_wizard_insights(self, query: str) -> Dict:
        """ウィザードシステムから洞察を取得"""
        if not self.wizards_orchestrator:
            return {}
            
        try:
            # クエリに関連する知識ギャップがあるかチェック
            detector = self.wizards_orchestrator.gap_detector
            related_gaps = []
            
            for gap_id, gap in detector.detected_gaps.items():
                if query.lower() in gap.topic.lower() or query.lower() in gap.description.lower():
                    related_gaps.append({
                        'gap_id': gap.gap_id,
                        'topic': gap.topic,
                        'priority': gap.priority,
                        'type': gap.gap_type.value
                    })
                    
            return {
                'related_gaps': related_gaps,
                'total_gaps': len(detector.detected_gaps),
                'recommendation': 'Consider triggering manual learning' if related_gaps else 'No immediate gaps detected'
            }
            
        except Exception as e:
            self.logger.error(f"Wizard insights error: {e}")
            return {}
    
    async def _store_wizard_knowledge(self, topic: str, content: str, metadata: Dict = None):
        """Store wizard-generated knowledge in the unified RAG system"""
        if not self.rag_integration:
            return
        
        try:
            spell_id = await self.rag_integration.add_knowledge_unified(
                spell_name=f"wizard_knowledge_{topic}",
                content=content,
                metadata=metadata or {},
                category='wizard_learning',
                tags=['wizard', 'automated_learning', topic]
            )
            
            self.logger.info(f"🧙 Wizard knowledge stored: {spell_id}")
            return spell_id
            
        except Exception as e:
            self.logger.error(f"Failed to store wizard knowledge: {e}")
            return None


async def main():
    """テスト実行"""
    worker = RAGWizardsWorker()
    
    try:
        # ワーカーを開始
        await worker.start()
        
        # テストメッセージを処理
        test_message = {
            'task_id': 'test_001',
            'task_type': 'manual_learning',
            'topic': 'worker_health_monitoring'
        }
        
        result = await worker.process_message(test_message)
        print(f"Result: {json.dumps(result, indent=2, default=str)}")
        
        # ステータスレポートを生成
        status_message = {
            'task_id': 'test_002',
            'task_type': 'status_report'
        }
        
        status = await worker.process_message(status_message)
        print(f"Status: {json.dumps(status, indent=2, default=str)}")
        
        # 少し待機
        await asyncio.sleep(5)
        
    finally:
        await worker.stop()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
    )
    asyncio.run(main())