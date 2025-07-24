"""
📚 Knowledge Sage A2A Agent - 修正版
既存のビジネスロジックを活用したA2AServer実装

完全にpython-a2a APIに準拠した実装
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from python_a2a import A2AServer, skill, Message, TextContent, MessageRole, A2AError

# ビジネスロジック（既存実装を活用）
from .business_logic import KnowledgeProcessor


class KnowledgeSageAgent(A2AServer):
    """
    📚 Knowledge Sage A2A Agent
    
    python-a2aを使用した標準的なA2Aエージェント実装
    既存のKnowledgeProcessorビジネスロジックを活用
    """
    
    def __init__(self, host: str = "localhost", port: int = 8001):
        """A2AServer初期化"""
        super().__init__()
        
        # エージェント情報設定
        self.agent_name = "knowledge-sage"
        self.description = "Elders Guild Knowledge Management Sage - A2A Standard Implementation"
        self.host = host
        self.port = port
        
        # Logger設定
        self.logger = logging.getLogger(f"KnowledgeSageAgent")
        
        # ビジネスロジックプロセッサ（既存実装活用）
        self.knowledge_processor = KnowledgeProcessor()
        
        self.logger.info(f"Knowledge Sage A2A Agent initialized on {host}:{port}")
    
    async def initialize(self) -> bool:
        """A2Aエージェント初期化"""
        try:
            # ビジネスロジック初期化は既にコンストラクタで完了
            self.logger.info("Knowledge Sage A2A Agent fully initialized")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Knowledge Sage A2A Agent: {e}")
            return False
    
    def _extract_data_from_message(self, message: Message) -> Dict[str, Any]:
        """メッセージからデータを抽出"""
        if isinstance(message.content, TextContent):
            text_content = message.content.text
            try:
                # JSON形式の場合はパース
                return json.loads(text_content)
            except json.JSONDecodeError:
                # プレーンテキストの場合
                return {"query": text_content}
        else:
            raise A2AError("TextContent required")
    
    def _create_response_message(self, result: Dict[str, Any]) -> Message:
        """結果からレスポンスメッセージを作成"""
        return Message(
            content=TextContent(text=json.dumps(result)),
            role=MessageRole.AGENT
        )
    
    def _create_error_message(self, error: Exception) -> Message:
        """エラーからエラーメッセージを作成"""
        return Message(
            content=TextContent(text=json.dumps({
                "success": False,
                "error": str(error)
            })),
            role=MessageRole.AGENT
        )
    
    # === コア知識管理スキル ===
    
    @skill(name="search_knowledge")
    async def search_knowledge_skill(self, message: Message) -> Message:
        """知識検索スキル"""
        try:
            # メッセージからデータ抽出
            data = self._extract_data_from_message(message)
            
            # ビジネスロジック実行
            result = await self.knowledge_processor.process_action("search_knowledge", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in search_knowledge skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="store_knowledge")
    async def store_knowledge_skill(self, message: Message) -> Message:
        """知識保存スキル"""
        try:
            # データ抽出
            data = self._extract_data_from_message(message)
            
            # ビジネスロジック実行
            result = await self.knowledge_processor.process_action("store_knowledge", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in store_knowledge skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="get_best_practices")
    async def get_best_practices_skill(self, message: Message) -> Message:
        """ベストプラクティス取得スキル"""
        try:
            # データ抽出
            data = self._extract_data_from_message(message)
            
            # ビジネスロジック実行
            result = await self.knowledge_processor.process_action("get_best_practices", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in get_best_practices skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="synthesize_knowledge")
    async def synthesize_knowledge_skill(self, message: Message) -> Message:
        """知識統合スキル"""
        try:
            # データ抽出
            data = self._extract_data_from_message(message)
            
            # ビジネスロジック実行
            result = await self.knowledge_processor.process_action("synthesize_knowledge", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in synthesize_knowledge skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="get_statistics")
    async def get_statistics_skill(self, message: Message) -> Message:
        """統計情報取得スキル"""
        try:
            # ビジネスロジック実行（引数不要）
            result = await self.knowledge_processor.process_action("get_statistics", {})
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in get_statistics skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="recommend_knowledge")
    async def recommend_knowledge_skill(self, message: Message) -> Message:
        """知識推奨スキル"""
        try:
            # データ抽出
            data = self._extract_data_from_message(message)
            
            # ビジネスロジック実行
            result = await self.knowledge_processor.process_action("recommend_knowledge", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in recommend_knowledge skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="search_by_tags")
    async def search_by_tags_skill(self, message: Message) -> Message:
        """タグ検索スキル"""
        try:
            # データ抽出
            data = self._extract_data_from_message(message)
            
            # ビジネスロジック実行
            result = await self.knowledge_processor.process_action("search_by_tags", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in search_by_tags skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="export_knowledge_base")
    async def export_knowledge_base_skill(self, message: Message) -> Message:
        """ナレッジベースエクスポートスキル"""
        try:
            # ビジネスロジック実行（引数不要）
            result = await self.knowledge_processor.process_action("export_knowledge_base", {})
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in export_knowledge_base skill: {e}")
            return self._create_error_message(e)
    
    # === 4賢者協調スキル ===
    
    @skill(name="elder_collaboration")
    async def elder_collaboration_skill(self, message: Message) -> Message:
        """4賢者協調スキル"""
        try:
            # A2A協調処理（他の賢者との連携）
            collaboration_request = self._extract_data_from_message(message)
            
            # 協調パターン識別
            collaboration_type = collaboration_request.get("type", "knowledge_synthesis")
            
            if collaboration_type == "knowledge_synthesis":
                # 知識統合協調
                topic = collaboration_request.get("topic", "")
                synthesis_result = await self.knowledge_processor.process_action(
                    "synthesize_knowledge", 
                    {"topic": topic}
                )
                
                result = {
                    "success": True,
                    "collaboration_type": "knowledge_synthesis",
                    "result": synthesis_result,
                    "agent": "knowledge-sage"
                }
                
            elif collaboration_type == "domain_expertise":
                # ドメイン専門知識提供
                domain = collaboration_request.get("domain", "general")
                best_practices_result = await self.knowledge_processor.process_action(
                    "get_best_practices",
                    {"domain": domain}
                )
                
                result = {
                    "success": True,
                    "collaboration_type": "domain_expertise",
                    "result": best_practices_result,
                    "agent": "knowledge-sage",
                    "domain": domain
                }
                
            else:
                # 一般的な協調処理
                search_result = await self.knowledge_processor.process_action(
                    "search_knowledge",
                    {"query": collaboration_request.get("query", "")}
                )
                
                result = {
                    "success": True,
                    "collaboration_type": "general_knowledge",
                    "result": search_result,
                    "agent": "knowledge-sage"
                }
            
            return self._create_response_message(result)
                
        except Exception as e:
            self.logger.error(f"Error in elder_collaboration skill: {e}")
            return self._create_error_message(e)
    
    # === ヘルスチェック・管理 ===
    
    @skill(name="health_check")
    async def health_check_skill(self, message: Message) -> Message:
        """ヘルスチェックスキル"""
        try:
            # 統計情報取得でシステム状態確認
            stats_result = await self.knowledge_processor.process_action("get_statistics", {})
            
            health_status = {
                "status": "healthy",
                "agent": "knowledge-sage",
                "timestamp": stats_result.get("data", {}).get("timestamp", "unknown"),
                "knowledge_items": stats_result.get("data", {}).get("total_items", 0),
                "uptime": "operational"
            }
            
            return self._create_response_message(health_status)
            
        except Exception as e:
            self.logger.error(f"Error in health_check skill: {e}")
            error_status = {
                "status": "unhealthy",
                "agent": "knowledge-sage",
                "error": str(e)
            }
            return self._create_response_message(error_status)
    
    async def shutdown(self):
        """A2Aエージェント終了処理"""
        try:
            self.logger.info("Knowledge Sage A2A Agent shutdown initiated")
            # シンプルな終了処理
            self.logger.info("Knowledge Sage A2A Agent shutdown completed")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


# === エージェント実行スクリプト ===

async def main():
    """Knowledge Sage A2Aエージェント実行"""
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # エージェント作成・起動
    agent = KnowledgeSageAgent()
    
    try:
        if await agent.initialize():
            print(f"🚀 Starting Knowledge Sage A2A Agent on port 8001.0..")
            await agent.run()  # A2AServerの標準実行メソッド
        else:
            print("❌ Failed to initialize Knowledge Sage A2A Agent")
            
    except KeyboardInterrupt:
        print("\n🛑 Received shutdown signal")
    except Exception as e:
        print(f"❌ Error running Knowledge Sage A2A Agent: {e}")
    finally:
        await agent.shutdown()
        print("✅ Knowledge Sage A2A Agent stopped")


if __name__ == "__main__":
    asyncio.run(main())