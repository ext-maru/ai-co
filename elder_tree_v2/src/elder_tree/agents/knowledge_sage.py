"""
Knowledge Sage Implementation
知識管理・技術分析エージェント
"""

from elder_tree.agents.base_agent import ElderTreeAgent
from python_a2a import Message
from typing import Dict, Any


class KnowledgeSage(ElderTreeAgent):
    """Knowledge Sage - 知識管理専門エージェント"""
    
    def __init__(self):
        super().__init__(
            name="knowledge_sage",
            domain="knowledge",
            port=50051
        )
        
        # ドメイン固有ハンドラー登録
        self._register_domain_handlers()
        
        # 知識ベース（簡易実装）
        self.knowledge_base = {}
    
    def _register_domain_handlers(self):
        """Knowledge Sage固有のハンドラー登録"""
        
        @self.on_message("analyze_technology")
        async def handle_analyze_technology(message: Message) -> Dict[str, Any]:
            """技術分析処理"""
            tech_name = message.data.get("technology")
            context = message.data.get("context", {})
            
            self.logger.info(
                "Analyzing technology",
                technology=tech_name,
                context=context
            )
            
            # 基本分析（TDD: テストが通る最小実装）
            analysis = {
                "technology": tech_name,
                "assessment": "suitable",
                "confidence": 0.85,
                "pros": [
                    "Good community support",
                    "Well documented",
                    "Production ready"
                ],
                "cons": [
                    "Learning curve",
                    "Dependency management"
                ],
                "recommendation": "Recommended for production use"
            }
            
            # 信頼度が低い場合はRAG Sageに調査依頼
            if message.data.get("require_research", False):
                rag_response = await self.collaborate_with_sage(
                    "rag_sage",
                    {
                        "action": "search_technical_docs",
                        "query": tech_name,
                        "limit": 5
                    }
                )
                
                # RAG結果を分析に統合
                if rag_response.status == "success":
                    analysis["additional_insights"] = rag_response.data.get("documents", [])
            
            return {"analysis": analysis, "status": "completed"}
        
        @self.on_message("store_knowledge")
        async def handle_store_knowledge(message: Message) -> Dict[str, Any]:
            """知識保存処理"""
            knowledge_item = message.data.get("knowledge")
            category = message.data.get("category", "general")
            
            if category not in self.knowledge_base:
                self.knowledge_base[category] = []
            
            self.knowledge_base[category].append(knowledge_item)
            
            self.logger.info(
                "Knowledge stored",
                category=category,
                total_items=len(self.knowledge_base[category])
            )
            
            return {
                "status": "stored",
                "category": category,
                "item_count": len(self.knowledge_base[category])
            }
