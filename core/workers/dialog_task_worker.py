#!/usr/bin/env python3
"""
Elders Guild Dialog Task Worker
対話型タスクワーカー - Elder Tree階層システム統合版
"""
import json
import logging
import os
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pika

sys.path.append("/root/ai_co")
from core.workers.task_worker import TaskWorker
from features.ai.rag_manager import RAGManager
from features.conversation.conversation_manager import ConversationManager
from libs.elder_council_summoner import (
    CouncilTrigger,
    ElderCouncilSummoner,
    TriggerCategory,
    UrgencyLevel,
)
from libs.elder_tree_hierarchy import (
    ElderDecision,
    ElderMessage,
    ElderRank,
    ElderTreeHierarchy,
    SageType,
    get_elder_tree,
)

# Elder Tree Integration imports
from libs.four_sages_integration import FourSagesIntegration

PROJECT_DIR = Path(__file__).parent.parent
LOG_DIR = PROJECT_DIR / "logs"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [DialogTaskWorker] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "dialog_task_worker.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("DialogTaskWorker")


@dataclass
class DialogContext:
    """対話コンテキスト情報"""

    conversation_id: str
    topic: str
    complexity: str  # 'simple', 'moderate', 'complex', 'critical'
    sentiment: str  # 'positive', 'neutral', 'negative', 'urgent'
    requires_elder_guidance: bool = False
    elder_recommendations: List[str] = None

    def __post_init__(self):
        if self.elder_recommendations is None:
            self.elder_recommendations = []


class DialogTaskWorker(TaskWorker):
    def __init__(self, worker_id="dialog-worker-1"):
        """初期化メソッド"""
        super().__init__(worker_id)
        self.conversation_manager = ConversationManager()

        # Elder Tree Integration
        try:
            self.elder_tree = get_elder_tree()
            self.four_sages = FourSagesIntegration()
            self.elder_council_summoner = ElderCouncilSummoner()

            # Register this worker as a servant in the Elder Tree
            self.elder_rank = ElderRank.SERVANT
            self.elder_id = f"dialog_servant_{worker_id}"

            logger.info(f"🌳 Elder Tree Integration initialized for {self.elder_id}")
            logger.info("📜 Connected to Four Sages and Elder Council systems")

        except Exception as e:
            logger.error(f"❌ Elder Tree Integration failed: {e}")
            logger.warning("⚠️ Dialog Worker operating without Elder guidance")
            self.elder_tree = None
            self.four_sages = None
            self.elder_council_summoner = None

    def connect(self):
        """拡張接続（対話キューも含む）"""
        super().connect()
        self.channel.queue_declare(queue="dialog_task_queue", durable=True)
        self.channel.queue_declare(queue="dialog_response_queue", durable=True)
        logger.info(f"{self.worker_id} - 対話キュー接続成功")
        return True

    def process_dialog_task(self, ch, method, properties, body):
        """対話型タスク処理 - Elder Tree統合版"""
        try:
            task_data = json.loads(body)
            conversation_id = task_data.get("conversation_id")
            instruction = task_data.get("instruction")
            context = task_data.get("context", {})

            logger.info(f"📨 対話タスク受信: {conversation_id}")
            logger.info(f"指示: {instruction[:100]}")

            # 会話履歴取得
            messages = self.conversation_manager.db.get_messages(conversation_id)
            conversation_context = self._build_conversation_context(messages)

            # 対話の複雑さを分析
            dialog_context = self.analyze_dialog_complexity(
                instruction,
                {"conversation_id": conversation_id, "message_count": len(messages)},
            )

            logger.info(
                f"📊 Dialog Analysis - Complexity: {dialog_context.complexity}, Sentiment: " \
                    "{dialog_context.sentiment}"
            )

            # Elder Tree統合処理
            elder_guidance = None
            rag_insights = None

            if self.elder_tree and dialog_context.requires_elder_guidance:
                # RAG Sageに相談（非同期処理をシミュレート）
                import asyncio

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    rag_insights = loop.run_until_complete(
                        self.consult_rag_sage_for_context(
                            conversation_id, instruction, messages
                        )
                    )

                    # 複雑な対話の場合はClaude Elderにエスカレート
                    if (
                        dialog_context.complexity == "complex"
                        or dialog_context.sentiment == "urgent"
                    ):
                        elder_guidance = loop.run_until_complete(
                            self.escalate_to_claude_elder(
                                conversation_id,
                                f"Complex dialog: {dialog_context.complexity}/{dialog_context.sentiment}",
                                {
                                    "instruction": instruction,
                                    "context": conversation_context,
                                },
                            )
                        )

                    # ポリシー決定が必要な場合
                    if "policy" in instruction.lower() or "ポリシー" in instruction:
                        council_decision = loop.run_until_complete(
                            self.request_elder_council_for_policy(
                                conversation_id,
                                f"Policy question from dialog: {instruction[:100]}",
                            )
                        )
                        if council_decision:
                            dialog_context.elder_recommendations.extend(
                                council_decision.get("guidelines", [])
                            )

                finally:
                    loop.close()

            # RAG適用（会話履歴 + Elder知見を含む）
            enhanced_prompt = f"{conversation_context}\n\n新しい指示: {instruction}"

            # RAG Sageからの知見を追加
            if rag_insights:
                enhanced_prompt += (
                    f"\n\n関連知識: {rag_insights.get('context_enhancement', '')}"
                )

            # Elder guidanceを適用
            if elder_guidance:
                enhanced_prompt += f"\n\nElder指導: {elder_guidance.get('guidance', '')}"

            enhanced_prompt = self.rag.build_context_prompt(enhanced_prompt)

            # 処理実行（Elder Tree統合版）
            if "詳細" in instruction or "？" in instruction:
                # 追加情報が必要
                question = self._generate_clarification_question(instruction)

                # Elder recommendationsがある場合は質問を調整
                if dialog_context.elder_recommendations:
                    question += "\n\n参考情報: " + ", ".join(
                        dialog_context.elder_recommendations[:2]
                    )

                response = {
                    "conversation_id": conversation_id,
                    "worker_id": self.worker_id,
                    "status": "need_info",
                    "content": "追加情報が必要です",
                    "question": question,
                    "elder_tree_engaged": bool(elder_guidance or rag_insights),
                }
            else:
                # 処理実行
                content = f"{instruction}を処理中です"

                # Elder guidanceに基づいてレスポンスを調整
                if (
                    elder_guidance
                    and elder_guidance.get("suggested_approach")
                    == "empathetic_technical"
                ):
                    content = f"承知いたしました。{instruction}について丁寧に対応させていただきます"

                response = {
                    "conversation_id": conversation_id,
                    "worker_id": self.worker_id,
                    "status": "progress",
                    "content": content,
                    "progress": 50,
                    "elder_tree_engaged": bool(elder_guidance or rag_insights),
                }

            # 対話インサイトをKnowledge Sageに報告（非同期）
            if self.elder_tree and (
                dialog_context.complexity != "simple" or len(messages) > 10
            ):
                insights = {
                    "dialog_complexity": dialog_context.complexity,
                    "sentiment": dialog_context.sentiment,
                    "topic": dialog_context.topic,
                    "message_count": len(messages),
                    "elder_guidance_used": bool(elder_guidance),
                    "rag_insights_used": bool(rag_insights),
                }

                # 非同期で報告（メインフローをブロックしない）
                import threading

                def report_async():
                    """report_asyncメソッド"""
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(
                        self.report_dialog_insights_to_knowledge_sage(
                            conversation_id, insights
                        )
                    )
                    loop.close()

                threading.Thread(target=report_async, daemon=True).start()

            # PMに応答送信
            self.channel.basic_publish(
                exchange="",
                routing_key="dialog_response_queue",
                body=json.dumps(response),
                properties=pika.BasicProperties(delivery_mode=2),
            )

            # 会話記録（Elder Tree統合情報を含む）
            metadata = {
                "status": response["status"],
                "dialog_complexity": dialog_context.complexity,
                "elder_tree_engaged": response.get("elder_tree_engaged", False),
            }

            self.conversation_manager.add_worker_message(
                conversation_id, self.worker_id, response["content"], metadata=metadata
            )

            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(
                f"✅ 対話応答送信: {conversation_id} (Elder Tree: {response.get('elder_tree_engaged', False)})"
            )

        except Exception as e:
            logger.error(f"❌ 対話タスク処理エラー: {e}")
            traceback.print_exc()
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def _build_conversation_context(self, messages):
        """会話コンテキスト構築"""
        context = "【会話履歴】\n"
        for msg in messages[-10:]:  # 最新10件
            sender = msg["sender"]
            content = msg["content"][:100]  # 要約
            context += f"{sender}: {content}\n"
        return context

    def _generate_clarification_question(self, instruction):
        """明確化質問生成"""
        if "Webアプリ" in instruction:
            return "どのような機能が必要ですか？（ユーザー認証、データベース、API等）"
        elif "データ" in instruction:
            return "どのような形式のデータですか？（CSV、JSON、データベース等）"
        else:
            return "もう少し詳しく要件を教えてください"

    async def consult_rag_sage_for_context(
        self, conversation_id: str, instruction: str, messages: List[Dict]
    ) -> Optional[Dict[str, Any]]:
        """RAG賢者に対話コンテキストを相談"""
        if not self.elder_tree:
            return None

        try:
            logger.info(
                f"🧙‍♂️ Consulting RAG Sage for dialog context: {conversation_id}"
            )

            # Prepare message for RAG Sage
            sage_message = ElderMessage(
                sender_rank=self.elder_rank,
                sender_id=self.elder_id,
                recipient_rank=ElderRank.SAGE,
                recipient_id="rag_sage",
                message_type="context_request",
                content={
                    "conversation_id": conversation_id,
                    "instruction": instruction,
                    "recent_messages": messages[-5:] if messages else [],
                    "request_type": "dialog_context_enhancement",
                },
                requires_response=True,
                priority="normal",
            )

            # Send message through Elder Tree
            await self.elder_tree.send_message(sage_message)

            # Simulate RAG Sage response (in real system, would wait for actual response)
            # Note: search_similar_conversations would be implemented in real RAG system
            similar_contexts = []
            if hasattr(self.rag, "search_similar_conversations"):
                similar_contexts = self.rag.search_similar_conversations(instruction)

            context_insights = {
                "relevant_knowledge": similar_contexts,
                "suggested_responses": [],
                "context_enhancement": "Based on similar conversations, this topic relates to...",
                "confidence": 0.85,
            }

            logger.info(
                f"✅ RAG Sage provided context insights with confidence: {context_insights['confidence']}"
            )
            return context_insights

        except Exception as e:
            logger.error(f"❌ RAG Sage consultation failed: {e}")
            return None

    async def report_dialog_insights_to_knowledge_sage(
        self, conversation_id: str, insights: Dict[str, Any]
    ):
        """Knowledge賢者に対話インサイトを報告"""
        if not self.elder_tree:
            return

        try:
            logger.info(
                f"📚 Reporting dialog insights to Knowledge Sage: {conversation_id}"
            )

            sage_message = ElderMessage(
                sender_rank=self.elder_rank,
                sender_id=self.elder_id,
                recipient_rank=ElderRank.SAGE,
                recipient_id="knowledge_sage",
                message_type="knowledge_update",
                content={
                    "conversation_id": conversation_id,
                    "insights": insights,
                    "timestamp": datetime.now().isoformat(),
                    "source": "dialog_worker",
                },
                requires_response=False,
                priority="low",
            )

            await self.elder_tree.send_message(sage_message)
            logger.info("✅ Dialog insights reported to Knowledge Sage")

        except Exception as e:
            logger.error(f"❌ Knowledge Sage reporting failed: {e}")

    async def escalate_to_claude_elder(
        self, conversation_id: str, reason: str, context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Claude Elderに複雑な対話をエスカレート"""
        if not self.elder_tree:
            return None

        try:
            logger.info(
                f"🤖 Escalating complex dialog to Claude Elder: {conversation_id}"
            )

            escalation_message = ElderMessage(
                sender_rank=self.elder_rank,
                sender_id=self.elder_id,
                recipient_rank=ElderRank.CLAUDE_ELDER,
                recipient_id="claude",
                message_type="dialog_escalation",
                content={
                    "conversation_id": conversation_id,
                    "escalation_reason": reason,
                    "dialog_context": context,
                    "urgency": "high" if "critical" in reason.lower() else "normal",
                    "requested_action": "provide_guidance",
                },
                requires_response=True,
                priority="high",
            )

            await self.elder_tree.send_message(escalation_message)

            # Simulate Claude Elder response
            elder_guidance = {
                "guidance": "Handle this conversation with care. Consider these points...",
                "suggested_approach": "empathetic_technical",
                "key_points": [
                    "Acknowledge user concerns",
                    "Provide clear technical explanation",
                    "Offer multiple solution paths",
                ],
                "escalate_to_human": False,
            }

            logger.info("✅ Claude Elder provided guidance for complex dialog")
            return elder_guidance

        except Exception as e:
            logger.error(f"❌ Claude Elder escalation failed: {e}")
            return None

    async def request_elder_council_for_policy(
        self, conversation_id: str, policy_question: str
    ) -> Optional[Dict[str, Any]]:
        """Elder評議会に対話ポリシー決定を要請"""
        if not self.elder_council_summoner:
            return None

        try:
            logger.info(
                f"🏛️ Requesting Elder Council for policy decision: {conversation_id}"
            )

            # Create council trigger for policy decision
            trigger = CouncilTrigger(
                trigger_id=f"dialog_policy_{conversation_id}",
                category=TriggerCategory.STRATEGIC_DECISION,
                urgency=UrgencyLevel.MEDIUM,
                title=f"Dialog Policy Decision Required: {policy_question[:50]}",
                description=f"Dialog worker requires policy guidance for conversation {conversation_id}" \
                    "Dialog worker requires policy guidance for conversation {conversation_id}" \
                    "Dialog worker requires policy guidance for conversation {conversation_id}",
                triggered_at=datetime.now(),
                metrics={
                    "conversation_length": len(
                        self.conversation_manager.db.get_messages(conversation_id)
                    )
                },
                affected_systems=["dialog_system", "conversation_manager"],
                suggested_agenda=[
                    "Review conversation context",
                    "Determine appropriate policy",
                    "Set guidelines for similar future cases",
                ],
                auto_analysis={
                    "policy_question": policy_question,
                    "conversation_id": conversation_id,
                },
            )

            # Submit to council (in real system, would await council decision)
            logger.info(f"📋 Council trigger created: {trigger.trigger_id}")

            # Simulate council decision
            council_decision = {
                "decision_id": f"council_decision_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "policy": "Approved with conditions",
                "guidelines": [
                    "Maintain professional tone",
                    "Prioritize user privacy",
                    "Escalate if technical complexity exceeds threshold",
                ],
                "applicable_to_similar_cases": True,
            }

            logger.info("✅ Elder Council provided policy decision")
            return council_decision

        except Exception as e:
            logger.error(f"❌ Elder Council request failed: {e}")
            return None

    def analyze_dialog_complexity(
        self, instruction: str, context: Dict[str, Any]
    ) -> DialogContext:
        """対話の複雑さを分析"""
        # Analyze instruction complexity
        complexity = "simple"
        sentiment = "neutral"
        requires_elder = False

        # Complexity indicators
        if any(
            word in instruction.lower()
            for word in ["複雑", "difficult", "urgent", "critical"]
        ):
            complexity = "complex"
            requires_elder = True
        elif any(
            word in instruction.lower() for word in ["詳細", "specific", "technical"]
        ):
            complexity = "moderate"

        # Sentiment analysis
        if any(word in instruction.lower() for word in ["urgent", "急", "immediately"]):
            sentiment = "urgent"
            requires_elder = True
        elif any(
            word in instruction.lower() for word in ["problem", "issue", "error", "失敗"]
        ):
            sentiment = "negative"
        elif any(
            word in instruction.lower()
            for word in ["thank", "great", "excellent", "素晴らしい"]
        ):
            sentiment = "positive"

        # Topic extraction
        topic = "general"
        if "Webアプリ" in instruction or "web" in instruction.lower():
            topic = "web_development"
        elif "データ" in instruction or "data" in instruction.lower():
            topic = "data_processing"
        elif "API" in instruction:
            topic = "api_integration"

        return DialogContext(
            conversation_id=context.get("conversation_id", "unknown"),
            topic=topic,
            complexity=complexity,
            sentiment=sentiment,
            requires_elder_guidance=requires_elder,
            elder_recommendations=[],
        )

    def get_elder_tree_status(self) -> Dict[str, Any]:
        """Elder Tree統合ステータスを取得"""
        status = {
            "elder_tree_connected": self.elder_tree is not None,
            "four_sages_connected": self.four_sages is not None,
            "elder_council_available": self.elder_council_summoner is not None,
            "worker_elder_id": self.elder_id if hasattr(self, "elder_id") else None,
            "worker_elder_rank": self.elder_rank.value
            if hasattr(self, "elder_rank")
            else None,
        }

        if self.elder_tree:
            # Get position in hierarchy
            try:
                worker_node = self.elder_tree.nodes.get(self.elder_id)
                if worker_node:
                    path = worker_node.get_path_to_root()
                    status["hierarchy_path"] = [node.name for node in path]
                    status["wisdom_level"] = worker_node.wisdom_level
            except:
                pass

        return status

    def start(self):
        """対話型ワーカー起動"""
        if not self.connect():
            return

        self.channel.basic_qos(prefetch_count=1)

        # 通常タスクと対話タスクの両方を処理
        self.channel.basic_consume(
            queue="task_queue", on_message_callback=self.process_task
        )
        self.channel.basic_consume(
            queue="dialog_task_queue", on_message_callback=self.process_dialog_task
        )

        # Elder Tree統合ステータスを表示
        elder_status = self.get_elder_tree_status()
        logger.info(f"🌳 Elder Tree Status: {elder_status}")

        logger.info(f"🚀 {self.worker_id} 対話型モード起動 (Elders Guild Dialog Task Worker)")

        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("停止中...")
            self.channel.stop_consuming()
            self.connection.close()


if __name__ == "__main__":
    worker_id = sys.argv[1] if len(sys.argv) > 1 else "dialog-worker-1"
    worker = DialogTaskWorker(worker_id)
    worker.start()
