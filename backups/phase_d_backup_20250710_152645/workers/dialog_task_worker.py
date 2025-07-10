#!/usr/bin/env python3
"""
🌳 Elder Tree Integrated DialogTaskWorker
対話型タスクワーカー - Elders Guild統合版

Elders Guild Integration:
- 🌟 Grand Elder maru oversight
- 🤖 Claude Elder execution guidance
- 🧙‍♂️ Four Sages wisdom consultation
- 🏛️ Elder Council decision support
- ⚔️ Elder Servants coordination

Part of the Elder Tree Hierarchy for dialog-based task processing
"""
import os
import sys
import json
import pika
import logging
import traceback
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from core.base_worker import BaseWorker
from core import ErrorSeverity
from libs.conversation_manager import ConversationManager
from libs.rag_grimoire_integration import RagGrimoireIntegration, RagGrimoireConfig
from libs.rag_manager import RAGManager

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

class DialogTaskWorker(BaseWorker):
    """🌳 Elder Tree統合対話型タスクワーカー"""
    
    def __init__(self, worker_id="dialog-worker-1"):
        super().__init__(worker_type='dialog', worker_id=worker_id)
        self.conversation_manager = ConversationManager()
        self.rag_manager = RAGManager()
        
        # RAG Grimoire Integration setup
        self.rag_config = RagGrimoireConfig(
            database_url="postgresql://localhost/grimoire",
            search_threshold=0.7,
            max_search_results=5
        )
        self.rag_integration = None
        self._initialize_rag_integration()
        
        # Elder Tree Integration
        self.elder_tree = None
        self.four_sages = None
        self.elder_council_summoner = None
        self.elder_integration_enabled = False
        self._initialize_elder_systems()
    
    def _initialize_elder_systems(self):
        """Elder Tree システムの初期化（エラー処理付き）"""
        try:
            if get_elder_tree:
                self.elder_tree = get_elder_tree()
                self.logger.info("🌳 Elder Tree Hierarchy connected")
            
            if FourSagesIntegration:
                self.four_sages = FourSagesIntegration()
                self.logger.info("🧙‍♂️ Four Sages Integration activated")
            
            if ElderCouncilSummoner:
                self.elder_council_summoner = ElderCouncilSummoner()
                self.logger.info("🏛️ Elder Council Summoner initialized")
            
            if all([self.elder_tree, self.four_sages, self.elder_council_summoner]):
                self.elder_integration_enabled = True
                self.logger.info("✅ Full Elder Tree Integration enabled")
            else:
                self.logger.warning("⚠️ Partial Elder Tree Integration - some systems unavailable")
                
        except Exception as e:
            self.logger.error(f"Elder Tree initialization failed: {e}")
            self.elder_integration_enabled = False
        
    def setup_queues(self):
        """対話用キューの設定"""
        self.input_queue = 'ai_dialog'
        self.output_queue = 'ai_results'
        
        # 追加の対話用キュー
        self.channel.queue_declare(queue='ai_dialog_response', durable=True)
        self.logger.info(f"{self.worker_id} - 対話キュー設定完了")
        
    def process_message(self, ch, method, properties, body):
        """対話型タスク処理"""
        try:
            task_data = json.loads(body)
            conversation_id = task_data.get('conversation_id')
            instruction = task_data.get('instruction')
            context = task_data.get('context', {})
            
            self.logger.info(f"📨 対話タスク受信: {conversation_id}")
            self.logger.info(f"指示: {instruction[:100]}")
            
            # 会話履歴取得
            messages = self.conversation_manager.get_conversation(conversation_id)
            conversation_context = self._build_conversation_context(messages)
            
            # RAG適用（会話履歴も含む） with unified grimoire integration
            enhanced_prompt = f"{conversation_context}\n\n新しい指示: {instruction}"
            try:
                # Try unified RAG search first
                if self.rag_integration:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    rag_results = loop.run_until_complete(
                        self.rag_integration.search_unified(
                            query=instruction,
                            limit=3,
                            threshold=self.rag_config.search_threshold
                        )
                    )
                    loop.close()
                    
                    if rag_results:
                        rag_context = "\n\n## Related Knowledge:\n"
                        for result in rag_results:
                            rag_context += f"- {result['content'][:150]}...\n"
                        enhanced_prompt += rag_context
                else:
                    # Fallback to legacy RAG
                    enhanced_prompt = self.rag_manager.build_context_prompt(enhanced_prompt)
            except Exception as e:
                self.logger.warning(f"RAG適用失敗: {e}")
            
            # 処理実行
            if "詳細" in instruction or "？" in instruction:
                # 追加情報が必要
                response = {
                    'conversation_id': conversation_id,
                    'worker_id': self.worker_id,
                    'status': 'need_info',
                    'content': '追加情報が必要です',
                    'question': self._generate_clarification_question(instruction)
                }
            else:
                # 処理実行
                response = {
                    'conversation_id': conversation_id,
                    'worker_id': self.worker_id,
                    'status': 'progress',
                    'content': f'{instruction}を処理中です',
                    'progress': 50
                }
            
            # PMに応答送信
            self.channel.basic_publish(
                exchange='',
                routing_key='ai_dialog_response',
                body=json.dumps(response, ensure_ascii=False),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            
            # 会話記録
            self.conversation_manager.add_message(
                conversation_id,
                'assistant',
                response['content']
            )
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            self.logger.info(f"✅ 対話応答送信: {conversation_id}")
            
            # Store successful interactions in RAG system
            self._store_conversation_knowledge(conversation_id, instruction, response)
            
        except Exception as e:
            # 対話タスク処理エラー
            context = {
                'operation': 'dialog_process_message',
                'conversation_id': task_data.get('conversation_id') if 'task_data' in locals() else 'unknown',
                'instruction': task_data.get('instruction', '')[:100] if 'task_data' in locals() else 'unknown'
            }
            self.handle_error(e, context, severity=ErrorSeverity.MEDIUM)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def _build_conversation_context(self, messages):
        """会話コンテキスト構築"""
        if not messages:
            return "【新しい会話】"
            
        context = "【会話履歴】\n"
        for msg in messages[-10:]:  # 最新10件
            role = msg.get('role', 'user')
            content = msg.get('content', '')[:100]  # 要約
            context += f"{role}: {content}\n"
        return context
    
    def _generate_clarification_question(self, instruction):
        """明確化質問生成"""
        if "Webアプリ" in instruction:
            return "どのような機能が必要ですか？（ユーザー認証、データベース、API等）"
        elif "データ" in instruction:
            return "どのような形式のデータですか？（CSV、JSON、データベース等）"
        else:
            return "もう少し詳しく要件を教えてください"
    
    def _initialize_rag_integration(self):
        """Initialize RAG Grimoire Integration"""
        try:
            import asyncio
            self.rag_integration = RagGrimoireIntegration(self.rag_config)
            # Initialize in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.rag_integration.initialize())
            loop.close()
            self.logger.info("💬 RAG Grimoire Integration initialized for dialog worker")
        except Exception as e:
            self.logger.error(f"Failed to initialize RAG Grimoire Integration: {e}")
            self.rag_integration = None
    
    def _store_conversation_knowledge(self, conversation_id: str, instruction: str, response: Dict):
        """Store conversation knowledge in unified RAG system"""
        if not self.rag_integration or response.get('status') != 'progress':
            return
        
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            knowledge_content = f"Dialog interaction in conversation {conversation_id}\n"
            knowledge_content += f"User instruction: {instruction}\n"
            knowledge_content += f"Assistant response: {response.get('content', '')}\n"
            knowledge_content += f"Status: {response.get('status', 'unknown')}"
            
            loop.run_until_complete(
                self.rag_integration.add_knowledge_unified(
                    spell_name=f"dialog_{conversation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    content=knowledge_content,
                    metadata={
                        'conversation_id': conversation_id,
                        'worker_id': self.worker_id,
                        'interaction_type': 'dialog',
                        'status': response.get('status')
                    },
                    category='dialog_interaction',
                    tags=['dialog', 'conversation', 'interaction']
                )
            )
            loop.close()
            
            self.logger.info(f"💬 Dialog knowledge stored for conversation {conversation_id}")
            
        except Exception as e:
            self.logger.warning(f"Failed to store dialog knowledge: {e}")

    def cleanup(self):
        """Cleanup resources including RAG integration"""
        if self.rag_integration:
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.rag_integration.cleanup())
                loop.close()
                self.logger.info("💬 RAG Grimoire Integration cleaned up")
            except Exception as e:
                self.logger.error(f"Error during RAG cleanup: {e}")
        pass

    def stop(self):
        """TODO: stopメソッドを実装してください"""
        pass

    def initialize(self) -> None:
        """ワーカーの初期化処理"""
        # TODO: 初期化ロジックを実装してください
        logger.info(f"{self.__class__.__name__} initialized")
        pass

    def handle_error(self):
        """TODO: handle_errorメソッドを実装してください"""
        pass

    def get_status(self):
        """TODO: get_statusメソッドを実装してください"""
        pass

    def validate_config(self):
        """TODO: validate_configメソッドを実装してください"""
        pass

if __name__ == "__main__":
    worker_id = sys.argv[1] if len(sys.argv) > 1 else "dialog-worker-1"
    worker = DialogTaskWorker(worker_id)
    worker.start()