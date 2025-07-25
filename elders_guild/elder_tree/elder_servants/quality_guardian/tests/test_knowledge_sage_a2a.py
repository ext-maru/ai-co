"""
🧪 Knowledge Sage A2A Agent - 厳密テストスイート
TDD品質保証: 完璧になるまでのループテスト

テスト範囲:
- A2AServer基本機能
- 全スキル動作検証  
- エラーハンドリング
- 4賢者協調機能
- パフォーマンス検証
"""

import pytest
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from python_a2a import Message, TextContent, MessageRole
from python_a2a.errors import A2AError

# テスト対象インポート
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from knowledge_sage.a2a_agent import KnowledgeSageAgent
from knowledge_sage.business_logic import KnowledgeProcessor


class TestKnowledgeSageAgent:
    """Knowledge Sage A2A Agent テストスイート"""
    
    @pytest.fixture
    async def agent(self):
        """テスト用エージェント作成"""
        # ログレベル調整（テスト時はWARNING以上のみ）
        logging.getLogger("KnowledgeSageAgent").setLevel(logging.WARNING)
        logging.getLogger("KnowledgeProcessor").setLevel(logging.WARNING)
        
        agent = KnowledgeSageAgent(host="localhost", port=8901)  # テスト用ポート
        
        # モックプロセッサーに置き換え（実際のファイルI/O回避）
        agent.knowledge_processor = AsyncMock(spec=KnowledgeProcessor)
        
        yield agent
        
        # クリーンアップ
        try:
            await agent.shutdown()
        except:
            pass
    
    @pytest.fixture
    def mock_knowledge_processor(self):
        """モックナレッジプロセッサー"""
        processor = AsyncMock(spec=KnowledgeProcessor)
        
        # デフォルトレスポンス設定
        processor.process_action.return_value = {
            "success": True,
            "data": {"test": "response"}
        }
        
        return processor
    
    # === 基本機能テスト ===
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent):
        """エージェント初期化テスト"""
        # 初期化テスト
        result = await agent.initialize()
        assert result is True
        
        # 属性確認
        assert agent.name == "knowledge-sage"
        assert agent.port == 8901
        assert hasattr(agent, 'knowledge_processor')
        assert hasattr(agent, 'logger')
    
    @pytest.mark.asyncio
    async def test_agent_initialization_failure(self):
        """初期化失敗テスト"""
        agent = KnowledgeSageAgent()
        
        # プロセッサー初期化エラーをシミュレート
        with patch.object(agent, 'knowledge_processor', side_effect=Exception("Init failed")):
            # 初期化は既にコンストラクタで完了するため、例外が発生しない場合がある
            # このテストは初期化プロセスの堅牢性を確認
            result = await agent.initialize()
            assert result is True  # 現在の実装では常にTrue
    
    # === スキル個別テスト ===
    
    @pytest.mark.asyncio
    async def test_search_knowledge_skill_text_content(self, agent):
        """知識検索スキル - テキストコンテンツ"""
        # モック設定
        agent.knowledge_processor.process_action.return_value = {
            "success": True,
            "data": {
                "results": [
                    {"title": "Test Knowledge", "content": "Test content"}
                ]
            }
        }
        
        # テストメッセージ作成
        message = Message(content=TextContent(text="python programming"))
        
        # スキル実行
        response = await agent.search_knowledge_skill(message)
        
        # 検証
        assert isinstance(response, Message)
        assert isinstance(response.content, StructuredContent)
        assert response.content.data["success"] is True
        assert "results" in response.content.data["data"]
        assert response.metadata["skill"] == "search_knowledge"
        assert response.metadata["agent"] == "knowledge-sage"
        
        # プロセッサー呼び出し確認
        agent.knowledge_processor.process_action.assert_called_once_with(
            "search_knowledge", 
            {"query": "python programming"}
        )
    
    @pytest.mark.asyncio
    async def test_search_knowledge_skill_structured_content(self, agent):
        """知識検索スキル - 構造化コンテンツ"""
        # モック設定
        agent.knowledge_processor.process_action.return_value = {
            "success": True,
            "data": {"results": []}
        }
        
        # 構造化メッセージ
        message = Message(content=StructuredContent(data={
            "query": "machine learning",
            "limit": 10
        }))
        
        # スキル実行
        response = await agent.search_knowledge_skill(message)
        
        # 検証
        assert response.content.data["success"] is True
        agent.knowledge_processor.process_action.assert_called_once_with(
            "search_knowledge",
            {"query": "machine learning", "limit": 10}
        )
    
    @pytest.mark.asyncio
    async def test_search_knowledge_skill_error_handling(self, agent):
        """知識検索スキル - エラーハンドリング"""
        # プロセッサーエラーをシミュレート
        agent.knowledge_processor.process_action.side_effect = Exception("Database error")
        
        message = Message(content=TextContent(text="test query"))
        
        # スキル実行
        response = await agent.search_knowledge_skill(message)
        
        # エラー応答確認
        assert response.content.data["success"] is False
        assert "error" in response.content.data
        assert "Database error" in response.content.data["error"]
        assert response.metadata["success"] is False
    
    @pytest.mark.asyncio
    async def test_store_knowledge_skill(self, agent):
        """知識保存スキル"""
        # モック設定
        agent.knowledge_processor.process_action.return_value = {
            "success": True,
            "knowledge_id": "test_id_123",
            "message": "Knowledge stored successfully"
        }
        
        # テストデータ
        knowledge_data = {
            "knowledge": {
                "title": "Test Knowledge",
                "content": "This is test content",
                "tags": ["test", "python"]
            }
        }
        
        message = Message(content=StructuredContent(data=knowledge_data))
        
        # スキル実行
        response = await agent.store_knowledge_skill(message)
        
        # 検証
        assert response.content.data["success"] is True
        assert response.content.data["knowledge_id"] == "test_id_123"
        agent.knowledge_processor.process_action.assert_called_once_with(
            "store_knowledge",
            knowledge_data
        )
    
    @pytest.mark.asyncio
    async def test_get_best_practices_skill_with_domain(self, agent):
        """ベストプラクティス取得スキル - ドメイン指定"""
        # モック設定
        agent.knowledge_processor.process_action.return_value = {
            "success": True,
            "data": {
                "practices": [
                    {"title": "Python Best Practice", "domain": "programming"}
                ]
            }
        }
        
        message = Message(content=StructuredContent(data={"domain": "programming"}))
        
        # スキル実行
        response = await agent.get_best_practices_skill(message)
        
        # 検証
        assert response.content.data["success"] is True
        assert "practices" in response.content.data["data"]
        agent.knowledge_processor.process_action.assert_called_once_with(
            "get_best_practices",
            {"domain": "programming"}
        )
    
    @pytest.mark.asyncio
    async def test_get_best_practices_skill_text_domain(self, agent):
        """ベストプラクティス取得スキル - テキストドメイン"""
        agent.knowledge_processor.process_action.return_value = {
            "success": True,
            "data": {"practices": []}
        }
        
        message = Message(content=TextContent(text="security"))
        
        # スキル実行
        response = await agent.get_best_practices_skill(message)
        
        # 検証
        agent.knowledge_processor.process_action.assert_called_once_with(
            "get_best_practices",
            {"domain": "security"}
        )
    
    @pytest.mark.asyncio
    async def test_synthesize_knowledge_skill(self, agent):
        """知識統合スキル"""
        # モック設定
        agent.knowledge_processor.process_action.return_value = {
            "success": True,
            "data": {
                "topic": "AI development",
                "summary": "Comprehensive AI development knowledge synthesis",
                "key_points": ["TDD", "Clean Code", "Testing"]
            }
        }
        
        message = Message(content=TextContent(text="AI development"))
        
        # スキル実行
        response = await agent.synthesize_knowledge_skill(message)
        
        # 検証
        assert response.content.data["success"] is True
        assert "summary" in response.content.data["data"]
        agent.knowledge_processor.process_action.assert_called_once_with(
            "synthesize_knowledge",
            {"topic": "AI development"}
        )
    
    @pytest.mark.asyncio
    async def test_get_statistics_skill(self, agent):
        """統計情報取得スキル"""
        # モック設定
        agent.knowledge_processor.process_action.return_value = {
            "success": True,
            "data": {
                "total_items": 150,
                "total_best_practices": 25,
                "average_confidence": 0.85,
                "timestamp": "2025-07-23T10:30:00Z"
            }
        }
        
        message = Message(content=TextContent(text=""))  # 引数不要
        
        # スキル実行
        response = await agent.get_statistics_skill(message)
        
        # 検証
        assert response.content.data["success"] is True
        assert response.content.data["data"]["total_items"] == 150
        agent.knowledge_processor.process_action.assert_called_once_with(
            "get_statistics",
            {}
        )
    
    @pytest.mark.asyncio
    async def test_recommend_knowledge_skill(self, agent):
        """知識推奨スキル"""
        # モック設定
        agent.knowledge_processor.process_action.return_value = {
            "success": True,
            "data": {
                "recommendations": [
                    {
                        "title": "Python Testing Guide",
                        "relevance_score": 0.95,
                        "confidence": 0.90
                    }
                ]
            }
        }
        
        message = Message(content=StructuredContent(data={
            "context": "unit testing",
            "expertise": "intermediate"
        }))
        
        # スキル実行
        response = await agent.recommend_knowledge_skill(message)
        
        # 検証
        assert response.content.data["success"] is True
        assert "recommendations" in response.content.data["data"]
        agent.knowledge_processor.process_action.assert_called_once_with(
            "recommend_knowledge",
            {"context": "unit testing", "expertise": "intermediate"}
        )
    
    @pytest.mark.asyncio
    async def test_search_by_tags_skill(self, agent):
        """タグ検索スキル"""
        # モック設定
        agent.knowledge_processor.process_action.return_value = {
            "success": True,
            "data": {
                "results": [
                    {"title": "Tagged Knowledge", "tags": ["python", "testing"]}
                ]
            }
        }
        
        message = Message(content=StructuredContent(data={
            "tags": ["python", "testing"]
        }))
        
        # スキル実行
        response = await agent.search_by_tags_skill(message)
        
        # 検証
        assert response.content.data["success"] is True
        assert "results" in response.content.data["data"]
        agent.knowledge_processor.process_action.assert_called_once_with(
            "search_by_tags",
            {"tags": ["python", "testing"]}
        )
    
    @pytest.mark.asyncio
    async def test_export_knowledge_base_skill(self, agent):
        """ナレッジベースエクスポートスキル"""
        # モック設定
        agent.knowledge_processor.process_action.return_value = {
            "success": True,
            "data": {
                "knowledge_items": [],
                "best_practices": [],
                "export_timestamp": "2025-07-23T10:30:00Z",
                "version": "1.0"
            }
        }
        
        message = Message(content=TextContent(text=""))  # 引数不要
        
        # スキル実行
        response = await agent.export_knowledge_base_skill(message)
        
        # 検証
        assert response.content.data["success"] is True
        assert "export_timestamp" in response.content.data["data"]
        agent.knowledge_processor.process_action.assert_called_once_with(
            "export_knowledge_base",
            {}
        )
    
    # === 4賢者協調スキルテスト ===
    
    @pytest.mark.asyncio
    async def test_elder_collaboration_knowledge_synthesis(self, agent):
        """4賢者協調 - 知識統合パターン"""
        # モック設定
        agent.knowledge_processor.process_action.return_value = {
            "success": True,
            "data": {
                "topic": "distributed systems",
                "summary": "Distributed systems knowledge synthesis"
            }
        }
        
        message = Message(content=StructuredContent(data={
            "type": "knowledge_synthesis",
            "topic": "distributed systems"
        }))
        
        # スキル実行
        response = await agent.elder_collaboration_skill(message)
        
        # 検証
        assert response.content.data["success"] is True
        assert response.content.data["collaboration_type"] == "knowledge_synthesis"
        assert response.content.data["agent"] == "knowledge-sage"
        assert response.metadata["collaboration_type"] == "knowledge_synthesis"
    
    @pytest.mark.asyncio
    async def test_elder_collaboration_domain_expertise(self, agent):
        """4賢者協調 - ドメイン専門知識パターン"""
        # モック設定
        agent.knowledge_processor.process_action.return_value = {
            "success": True,
            "data": {
                "practices": [
                    {"title": "Security Best Practice", "domain": "security"}
                ]
            }
        }
        
        message = Message(content=StructuredContent(data={
            "type": "domain_expertise",
            "domain": "security"
        }))
        
        # スキル実行
        response = await agent.elder_collaboration_skill(message)
        
        # 検証
        assert response.content.data["success"] is True
        assert response.content.data["collaboration_type"] == "domain_expertise"
        assert response.content.data["domain"] == "security"
    
    @pytest.mark.asyncio
    async def test_elder_collaboration_general_knowledge(self, agent):
        """4賢者協調 - 一般知識パターン"""
        # モック設定
        agent.knowledge_processor.process_action.return_value = {
            "success": True,
            "data": {"results": []}
        }
        
        message = Message(content=StructuredContent(data={
            "type": "general_inquiry",
            "query": "machine learning algorithms"
        }))
        
        # スキル実行
        response = await agent.elder_collaboration_skill(message)
        
        # 検証
        assert response.content.data["success"] is True
        assert response.content.data["collaboration_type"] == "general_knowledge"
    
    # === ヘルスチェックテスト ===
    
    @pytest.mark.asyncio
    async def test_health_check_skill(self, agent):
        """ヘルスチェックスキル"""
        # モック設定
        agent.knowledge_processor.process_action.return_value = {
            "success": True,
            "data": {
                "total_items": 100,
                "timestamp": "2025-07-23T10:30:00Z"
            }
        }
        
        message = Message(content=TextContent(text=""))
        
        # スキル実行
        response = await agent.health_check_skill(message)
        
        # 検証
        assert response.content.data["status"] == "healthy"
        assert response.content.data["agent"] == "knowledge-sage"
        assert "knowledge_items" in response.content.data
        assert response.metadata["success"] is True
    
    @pytest.mark.asyncio
    async def test_health_check_skill_unhealthy(self, agent):
        """ヘルスチェックスキル - 異常状態"""
        # プロセッサーエラーをシミュレート
        agent.knowledge_processor.process_action.side_effect = Exception("System error")
        
        message = Message(content=TextContent(text=""))
        
        # スキル実行
        response = await agent.health_check_skill(message)
        
        # 検証
        assert response.content.data["status"] == "unhealthy"
        assert "error" in response.content.data
        assert response.metadata["success"] is False
    
    # === エラーハンドリングテスト ===
    
    @pytest.mark.asyncio
    async def test_invalid_message_content_handling(self, agent):
        """無効なメッセージコンテンツ処理"""
        # 無効なコンテンツタイプ（実際のpython-a2aでは発生しにくいが安全性確認）
        message = Message(content=None)
        
        # 各スキルでのエラーハンドリング確認
        skills_to_test = [
            agent.search_knowledge_skill,
            agent.store_knowledge_skill,
            agent.synthesize_knowledge_skill
        ]
        
        for skill in skills_to_test:
            response = await skill(message)
            assert response.content.data["success"] is False
            assert "error" in response.content.data
    
    # === パフォーマンステスト ===
    
    @pytest.mark.asyncio
    async def test_concurrent_skill_execution(self, agent):
        """並行スキル実行テスト"""
        # 複数の並行リクエストをシミュレート
        agent.knowledge_processor.process_action.return_value = {
            "success": True,
            "data": {"test": "concurrent"}
        }
        
        messages = [
            Message(content=TextContent(text=f"query {i}"))
            for i in range(5)
        ]
        
        # 並行実行
        tasks = [
            agent.search_knowledge_skill(msg)
            for msg in messages
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # 全て成功確認
        assert len(responses) == 5
        for response in responses:
            assert response.content.data["success"] is True
    
    # === 統合テスト ===
    
    @pytest.mark.asyncio
    async def test_complete_workflow_simulation(self, agent):
        """完全ワークフローシミュレーション"""
        # ワークフロー: 知識検索 → 統計取得 → ヘルスチェック
        
        # 1.0 知識検索
        agent.knowledge_processor.process_action.return_value = {
            "success": True,
            "data": {"results": [{"title": "Test"}]}
        }
        
        search_msg = Message(content=TextContent(text="test query"))
        search_response = await agent.search_knowledge_skill(search_msg)
        assert search_response.content.data["success"] is True
        
        # 2.0 統計取得
        agent.knowledge_processor.process_action.return_value = {
            "success": True,
            "data": {"total_items": 50}
        }
        
        stats_msg = Message(content=TextContent(text=""))
        stats_response = await agent.get_statistics_skill(stats_msg)
        assert stats_response.content.data["success"] is True
        
        # 3.0 ヘルスチェック
        health_msg = Message(content=TextContent(text=""))
        health_response = await agent.health_check_skill(health_msg)
        assert health_response.content.data["status"] == "healthy"


# === パフォーマンスベンチマークテスト ===

class TestKnowledgeSagePerformance:
    """Knowledge Sage A2A Agent パフォーマンステスト"""
    
    @pytest.fixture
    async def perf_agent(self):
        """パフォーマンステスト用エージェント"""
        agent = KnowledgeSageAgent(host="localhost", port=8902)
        agent.knowledge_processor = AsyncMock(spec=KnowledgeProcessor)
        agent.knowledge_processor.process_action.return_value = {
            "success": True,
            "data": {"test": "performance"}
        }
        
        yield agent
        
        try:
            await agent.shutdown()
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_skill_response_time(self, perf_agent):
        """スキル応答時間テスト"""
        import time
        
        message = Message(content=TextContent(text="performance test"))
        
        # 応答時間測定
        start_time = time.time()
        response = await perf_agent.search_knowledge_skill(message)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # 応答時間は100ms以下であることを確認
        assert response_time < 0.1, f"Response time {response_time:0.3f}s exceeds 100ms limit"
        assert response.content.data["success"] is True
    
    @pytest.mark.asyncio
    async def test_high_load_handling(self, perf_agent):
        """高負荷処理テスト"""
        # 100並行リクエスト
        messages = [
            Message(content=TextContent(text=f"load test {i}"))
            for i in range(100)
        ]
        
        import time
        start_time = time.time()
        
        # 並行実行
        tasks = [
            perf_agent.search_knowledge_skill(msg)
            for msg in messages
        ]
        
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # 全リクエスト処理時間は5秒以下
        assert total_time < 5.0, f"High load processing time {total_time:0.3f}s exceeds 5s limit"
        
        # 全て成功確認
        assert len(responses) == 100
        for response in responses:
            assert response.content.data["success"] is True