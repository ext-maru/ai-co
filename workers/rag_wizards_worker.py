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
    from libs.elder_tree_hierarchy import (
        get_elder_tree, ElderMessage, ElderRank, SageType,
        ElderTreeHierarchy, ElderNode, MessagePriority, ElderNodeType
    )
    from libs.elder_tree_soul_binding import (
        get_soul_binding_system, ElderSoulBindingSystem,
        SoulConnectionType, SoulBindingState
    )
    ELDER_TREE_AVAILABLE = True
    logging.info("🌳 Elder Tree integration fully available for RAG Wizards Worker")
except ImportError as e:
    # Handle specific exception case
    logging.warning(f"Elder Tree integration not available: {e}")
    FourSagesIntegration = None
    ElderCouncilSummoner = None
    get_elder_tree = None
    ElderMessage = None
    ElderRank = None
    SageType = None
    ElderTreeHierarchy = None
    ElderNode = None
    MessagePriority = None
    ElderNodeType = None
    get_soul_binding_system = None
    ElderSoulBindingSystem = None
    SoulConnectionType = None
    SoulBindingState = None
    ELDER_TREE_AVAILABLE = False


class RAGWizardsWorker(BaseWorker):
    """RAG Elder Wizards Worker"""

    def __init__(self, worker_id="rag_wizards")super().__init__(
    """初期化"""
            worker_type="rag_wizards",
            worker_id=worker_id
        )

        # RAGシステムの初期化
        self.rag_manager = RAGManager()
        try:
            self.enhanced_rag = EnhancedRAGManager()
        except Exception as e:
            # Handle specific exception case
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

        # Elder Tree統合
        self.elder_tree = None
        self.soul_binding_system = None
        self.wizard_node = None
        self.four_sages_integration = None

        if ELDER_TREE_AVAILABLE:
            self._initialize_elder_tree_integration()

    def _initialize_elder_tree_integration(self):
        """Elder Tree統合初期化"""
        try:
            self.elder_tree = get_elder_tree()
            self.soul_binding_system = get_soul_binding_system()

            # RAG Wizards WorkerをElder Treeに追加
            self._add_wizard_to_elder_tree()

            # Four Sages統合
            self.four_sages_integration = FourSagesIntegration()

            self.logger.info("🌳 RAG Wizards Worker Elder Tree integration complete")

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Elder Tree integration error: {e}")

    def _add_wizard_to_elder_tree(self):
        """ウィザードノードをElder Treeに追加"""
        try:
            if not self.elder_tree:
                return

            # RAG Wizards WorkerノードをElder Treeに追加
            wizard_node = ElderNode(
                id=f"rag_wizard_{self.worker_id}",
                name=f"RAG Wizard {self.worker_id}",
                rank=ElderRank.WIZARDS,
                node_type=ElderNodeType.PROCESS,
                parent_id="rag_sage",  # RAG賢者の下に配置
                capabilities=[
                    "knowledge_retrieval", "context_analysis", "wisdom_search",
                    "automated_learning", "gap_detection", "content_enrichment"
                ],
                metadata={
                    "worker_type": "rag_wizards",
                    "worker_id": self.worker_id,
                    "specialization": "elder_wizards_orchestration"
                }
            )

            # Elder Treeに追加
            success = self.elder_tree.add_elder_node(wizard_node)
            if success:
                self.wizard_node = wizard_node

                # 魂の紐づけ
                bound = self.elder_tree.bind_soul_to_elder(wizard_node.id)
                if bound:
                    self.logger.info(f"✨ RAG Wizard soul bound to Elder Tree: {wizard_node.id}")

                # RAG賢者との協調接続確立
                asyncio.create_task(self._establish_rag_sage_connection())
            else:
                self.logger.warning("Failed to add RAG Wizard to Elder Tree")

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Wizard node addition error: {e}")

    async def _establish_rag_sage_connection(self):
        """RAG賢者との協調接続確立"""
        if not self.soul_binding_system or not self.wizard_node:
            # Complex condition - consider breaking down
            return

        try:
            # RAG賢者との協調紐づけ
            binding = await self.soul_binding_system.create_soul_binding(
                self.wizard_node.id,
                "rag_sage",
                SoulConnectionType.HIERARCHICAL
            )

            if binding:
                self.logger.info("🔗 RAG Sage collaboration established")

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"RAG Sage connection error: {e}")

    async def send_message_to_rag_sage(self, message_content: Dict[str, Any]) -> bool:
        """RAG賢者にメッセージ送信"""
        if not self.elder_tree or not self.wizard_node:
            # Complex condition - consider breaking down
            return False

        try:
            elder_message = ElderMessage(
                sender_id=self.wizard_node.id,
                sender_rank=ElderRank.WIZARDS,
                receiver_id="rag_sage",
                receiver_rank=ElderRank.FOUR_SAGES,
                message_type="wizard_report",
                content=message_content,
                priority=MessagePriority.NORMAL
            )

            success = self.elder_tree.send_elder_message(elder_message)
            if success:
                processed = self.elder_tree.process_message_queue()
                self.logger.info(f"📨 Message sent to RAG Sage: {processed} processed")

            return success

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"RAG Sage message error: {e}")
            return False

    async def report_to_four_sages(self, report_data: Dict[str, Any]) -> Dict[str, bool]:
        """4賢者への報告"""
        if not self.four_sages_integration:
            return {}

        try:
            # レポート内容に追加情報を含める
            enhanced_report = {
                "wizard_worker_id": self.worker_id,
                "report_type": "rag_wizard_activity",
                "elder_tree_node_id": self.wizard_node.id if self.wizard_node else None,
                **report_data
            }

            # 全賢者にブロードキャスト
            results = await self.four_sages_integration.broadcast_to_all_sages(enhanced_report)

            self.logger.info(f"📡 Four Sages report completed: {sum(results.values())}/{len(results)} " \
                "📡 Four Sages report completed: {sum(results.values())}/{len(results)} " \
                "successful")
            return results

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Four Sages report error: {e}")
            return {}

    async def start(self)self.logger.info("🧙 RAG Elder Wizards Worker starting...")
    """ワーカー開始"""

        # Initialize RAG Grimoire Integration
        try:
            self.rag_integration = RagGrimoireIntegration(self.rag_config)
            await self.rag_integration.initialize()
            self.logger.info("🧙 RAG Grimoire Integration initialized for wizards")
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Failed to initialize RAG Grimoire Integration: {e}")
            self.rag_integration = None

        # ウィザードオーケストレータを初期化
        self.wizards_orchestrator = RAGElderWizardsOrchestrator()
        await self.wizards_orchestrator.start()

        # 通常のワーカー処理を開始
        await super().start()

    async def stop(self)self.logger.info("🛑 Stopping RAG Elder Wizards Worker...")
    """ワーカー停止"""

        # RAG Grimoire Integration cleanup
        if self.rag_integration:
            try:
                await self.rag_integration.cleanup()
                self.logger.info("🧙 RAG Grimoire Integration cleaned up")
            except Exception as e:
                # Handle specific exception case
                self.logger.error(f"Error cleaning up RAG integration: {e}")

        # ウィザードオーケストレータを停止
        if self.wizards_orchestrator:
            await self.wizards_orchestrator.stop()

        # バックグラウンドタスクをキャンセル
        for task in self.background_tasks:
            if not task.done():
                task.cancel()

        await super().stop()

    async def process_message(self, message: Dict) -> Dicttask_type = message.get('task_type', 'knowledge_gap'):
    """ッセージ処理"""

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

            # Elder Tree統合の場合、賢者への報告
            if ELDER_TREE_AVAILABLE and self.wizard_node:
                # Complex condition - consider breaking down
                await self._report_activity_to_elder_tree(message, result)

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Error processing message: {e}")
            await self.send_result({
                'task_id': message.get('task_id'),
                'error': str(e),
                'status': 'failed',
                'worker': self.worker_id
            })

        return result

    async def _report_activity_to_elder_tree(self, message: Dict, result: Dict):
        """Elder Treeへのアクティビティ報告"""
        try:
            report_data = {
                "activity_type": "message_processed",
                "task_type": message.get('task_type', 'unknown'),
                "result_status": result.get('status', 'unknown'),
                "timestamp": datetime.now().isoformat(),
                "wizard_health": "active"
            }

            # RAG賢者への直接報告
            await self.send_message_to_rag_sage(report_data)

            # 重要なアクティビティの場合は4賢者全体に報告
            if message.get('task_type') in ['manual_learning', 'status_report']:
                await self.report_to_four_sages(report_data)

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Elder Tree activity report error: {e}")

    async def _process_knowledge_gap(self, message: Dict) -> Dictgap_data = message.get('gap', {}):
    """識ギャップの処理"""

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

    async def _trigger_manual_learning(self, message: Dict) -> Dicttopic = message.get('topic'):
    """動学習のトリガー"""

        self.logger.info(f"🎯 Manual learning triggered for topic: {topic}")

        # ウィザードオーケストレータで学習を実行
        result = await self.wizards_orchestrator.manual_trigger_learning(topic)

        # Store the learning result in unified RAG system
        if result and self.rag_integration:
            # Complex condition - consider breaking down
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
                # Handle specific exception case
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

    async def _process_rag_query(self, message: Dict) -> Dictquery = message.get('query', ''):
    """常のRAGクエリ処理 with unified grimoire integration"""

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
                # Handle specific exception case
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
                    # Handle specific exception case
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
            # Handle specific exception case
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
                # Process each item in collection
                if query.lower() in gap.topic.lower() or query.lower() in gap.description.lower():
                    # Complex condition - consider breaking down
                    related_gaps.append({
                        'gap_id': gap.gap_id,
                        'topic': gap.topic,
                        'priority': gap.priority,
                        'type': gap.gap_type.value
                    })

            return {
                'related_gaps': related_gaps,
                'total_gaps': len(detector.detected_gaps),
                'recommendation': 'Consider triggering manual learning' \
                    if related_gaps \
                    else 'No immediate gaps detected'
            }

        except Exception as e:
            # Handle specific exception case
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
            # Handle specific exception case
            self.logger.error(f"Failed to store wizard knowledge: {e}")
            return None

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """設定検証"""
        try:
            # 必須フィールドチェック
            required_fields = getattr(self, 'REQUIRED_CONFIG_FIELDS', [])
            for field in required_fields:
                if field not in config:
                    self.logger.warning(f"必須フィールド不足: {field}")
                    return False
            return True
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"設定検証エラー: {e}")
            return False

    async def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str,
        Any]] = None
    ) -> None:
        """エラーハンドリング"""
        error_info = {
            "worker": self.__class__.__name__,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }

        self.logger.error(f"エラー発生: {error_info}")

        # エラー記録
        if hasattr(self, 'error_history'):
            self.error_history.append(error_info)

        # インシデント報告
        if hasattr(self, 'incident_reporter'):
            await self.incident_reporter.report(error_info)

    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """メッセージ処理"""
        try:
            message_type = message.get("type", "unknown")

            # メッセージタイプ別処理
            if hasattr(self, f"_handle_{message_type}"):
                handler = getattr(self, f"_handle_{message_type}")
                return await handler(message)

            # デフォルト処理
            return {
                "status": "processed",
                "worker": self.__class__.__name__,
                "message_id": message.get("id"),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            # Handle specific exception case
            await self.handle_error(e, {"message": message})
            return None

    def get_status(self) -> Dict[str, Any]:
        """ステータス取得"""
        return {
            "worker": self.__class__.__name__,
            "status": "running" if getattr(self, 'running', False) else "stopped",
            "uptime": self._calculate_uptime() if hasattr(self, '_calculate_uptime') else 0,
            "processed_count": getattr(self, 'processed_count', 0),
            "error_count": len(getattr(self, 'error_history', [])),
            "last_activity": getattr(self, 'last_activity', None),
            "health": self._check_health() if hasattr(self, '_check_health') else "unknown"
        }

    async def cleanup(self) -> Noneself.logger.info(f"{self.__class__.__name__} クリーンアップ開始"):
    """リーンアップ処理"""

        try:
            # 実行中タスクのキャンセル
            if hasattr(self, 'active_tasks'):
                for task in self.active_tasks:
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*self.active_tasks, return_exceptions=True)

            # リソース解放
            if hasattr(self, 'connection') and self.connection:
                # Complex condition - consider breaking down
                await self.connection.close()

            # 一時ファイル削除
            if hasattr(self, 'temp_dir') and self.temp_dir.exists():
                # Complex condition - consider breaking down
                import shutil
                shutil.rmtree(self.temp_dir)

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"クリーンアップエラー: {e}")

        self.logger.info(f"{self.__class__.__name__} クリーンアップ完了")

    async def initialize(self) -> Noneself.logger.info(f"{self.__class__.__name__} 初期化開始"):
    """期化処理"""

        try:
            # 基本属性初期化
            self.running = False
            self.processed_count = 0
            self.error_history = []
            self.start_time = datetime.now()
            self.last_activity = None
            self.active_tasks = set()

            # 設定検証
            if hasattr(self, 'config'):
                if not self.validate_config(self.config):
                    raise ValueError("設定検証失敗")

            # 必要なディレクトリ作成
            if hasattr(self, 'work_dir'):
                self.work_dir.mkdir(parents=True, exist_ok=True)

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"初期化エラー: {e}")
            raise

        self.logger.info(f"{self.__class__.__name__} 初期化完了")

    async def stop(self) -> Noneself.logger.info(f"{self.__class__.__name__} 停止処理開始"):
    """止処理"""

        self.running = False

        # クリーンアップ実行
        await self.cleanup()

        self.logger.info(f"{self.__class__.__name__} 停止完了")

    def get_elder_tree_status(self) -> Dict[str, Any]:
        """Elder Tree統合状態取得"""
        if not ELDER_TREE_AVAILABLE:
            return {"elder_tree_available": False}

        status = {
            "elder_tree_available": True,
            "wizard_node_id": self.wizard_node.id if self.wizard_node else None,
            "soul_bound": self.wizard_node.soul_bound if self.wizard_node else False,
            "rag_sage_connected": False,
            "four_sages_integration": self.four_sages_integration is not None
        }

        # RAG賢者との接続状況確認
        if self.soul_binding_system and self.wizard_node:
            # Complex condition - consider breaking down
            binding_status = self.soul_binding_system.get_soul_binding_status()
            status["active_bindings"] = binding_status.get("active_bindings", 0)

        # Four Sages統合状況
        if self.four_sages_integration:
            sage_status = self.four_sages_integration.get_sage_elder_tree_status()
            status["sage_tree_health"] = sage_status.get("tree_health", 0.0)

        return status


async def main()worker = RAGWizardsWorker()
"""テスト実行"""

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
        print(f"Result: {json.dumps(result, indent}")

        # ステータスレポートを生成
        status_message = {
            'task_id': 'test_002',
            'task_type': 'status_report'
        }

        status = await worker.process_message(status_message)
        print(f"Status: {json.dumps(status, indent}")

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
