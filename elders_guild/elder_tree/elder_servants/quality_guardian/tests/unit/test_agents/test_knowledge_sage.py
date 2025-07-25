"""
Knowledge Sage Unit Tests (TDD)
"""

import pytest
from python_a2a import Message


class TestKnowledgeSage:
    """Knowledge Sage専用テスト"""
    
    @pytest.mark.asyncio
    async def test_analyze_technology_handler(self):
        """Test: 技術分析ハンドラーが正しく動作"""
        from elder_tree.agents.knowledge_sage import KnowledgeSage
        
        # Arrange
        sage = KnowledgeSage()
        
        # Act
        result = await sage.handle_analyze_technology(
            Message(data={
                "technology": "FastAPI",
                "context": {
                    "project_type": "web_api",
                    "team_size": 5
                }
            })
        )
        
        # Assert
        assert "analysis" in result
        assert result["analysis"]["technology"] == "FastAPI"
        assert "assessment" in result["analysis"]
        assert "confidence" in result["analysis"]
        assert 0 <= result["analysis"]["confidence"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_knowledge_sage_rag_integration(self):
        """Test: RAG Sageとの統合が動作"""
        from elder_tree.agents.knowledge_sage import KnowledgeSage
        from unittest.mock import AsyncMock
        
        # Arrange
        sage = KnowledgeSage()
        sage.send_message = AsyncMock(return_value=Message(
            status="success",
            data={"documents": ["doc1", "doc2"]}
        ))
        
        # Act
        result = await sage.handle_analyze_technology(
            Message(data={
                "technology": "UnknownTech",
                "require_research": True
            })
        )
        
        # Assert
        sage.send_message.assert_called_once()
        assert sage.send_message.call_args[1]["target"] == "rag_sage"
