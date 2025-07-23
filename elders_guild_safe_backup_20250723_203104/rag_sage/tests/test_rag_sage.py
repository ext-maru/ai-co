#!/usr/bin/env python3
"""
RAG Sage Unit Tests
TDD: テストファースト開発
"""

import asyncio
import pytest
from datetime import datetime
from uuid import uuid4
from pathlib import Path

# Elder Tree imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from shared_libs import MessageType, MessagePriority
from rag_sage.soul import RAGSageSoul
from rag_sage.abilities.search_models import (
    SearchQuery, SearchResult, SearchType,
    Document, DocumentMetadata,
    Index, IndexStatus
)


class TestRAGSageCore:


"""RAG Sageのコア機能テスト"""
        """RAG Sageインスタンスの作成"""
        import tempfile
        import shutil
        
        # テスト用の一時データベースを使用
        test_db_path = Path("data/test_rag_sage.db")
        
        sage = RAGSageSoul()
        # テスト用データベースパスを設定
        sage.db_path = test_db_path
        
        await sage.initialize()
        yield sage
        await sage.shutdown()
        
        # テスト後にクリーンアップ
        if test_db_path.exists():
            test_db_path.unlink()
    
    @pytest.mark.asyncio
    async def test_document_indexing(self, rag_sage):

            """ドキュメントインデックス機能のテスト"""
        """検索機能のテスト"""
        # Arrange - ドキュメントを事前にインデックス
        test_docs = [
            Document(
                id=str(uuid4()),
                content="Task Sageはタスク管理を担当する賢者です。",
                source="docs/task_sage.md",
                metadata=DocumentMetadata(
                    title="Task Sage Documentation",
                    category="sage",
                    tags=["task", "sage", "management"]
                )
            ),
            Document(
                id=str(uuid4()),
                content="RAG Sageは情報検索と分析を担当する賢者です。",
                source="docs/rag_sage.md",
                metadata=DocumentMetadata(
                    title="RAG Sage Documentation",
                    category="sage",
                    tags=["rag", "sage", "search"]
                )
            )
        ]
        
        for doc in test_docs:
            await rag_sage.index_document(doc)
        
        # Act
        query = SearchQuery(
            query="賢者",
            search_type=SearchType.FULL_TEXT,
            filters={"category": "sage"},
            limit=10
        )
        results = await rag_sage.search(query)
        
        # Assert
        assert len(results.results) == 2
        assert all(isinstance(r, SearchResult) for r in results.results)
        assert all("賢者" in r.document.content for r in results.results)
        assert results.total_count == 2
        assert results.search_time_ms < 500  # 500ms以内
    
    @pytest.mark.asyncio
    async def test_semantic_search(self, rag_sage):

            """セマンティック検索のテスト（現在は全文検索フォールバック）"""
        """インデックス管理機能のテスト"""
        # Act
        index_info = await rag_sage.get_index_info()
        
        # Assert
        assert isinstance(index_info, Index)
        assert index_info.status == IndexStatus.READY
        assert index_info.document_count >= 0
        assert index_info.size_bytes >= 0
        
        # インデックス最適化
        optimization_result = await rag_sage.optimize_index()
        assert optimization_result.success is True


class TestRAGSageIntegration:

        """RAG Sageの統合テスト"""
        """RAG Sageインスタンスの作成"""
        # テスト用の一時データベースを使用
        test_db_path = Path("data/test_rag_sage_integration.db")
        
        sage = RAGSageSoul()
        # テスト用データベースパスを設定
        sage.db_path = test_db_path
        
        await sage.initialize()
        yield sage
        await sage.shutdown()
        
        # テスト後にクリーンアップ
        if test_db_path.exists():
            test_db_path.unlink()
    
    # A2A通信テストは削除（A2A依存除去）
    # @pytest.mark.asyncio
    # async def test_sage_communication(self, rag_sage):
    #     """他の賢者との通信テスト"""
    #     pass
    
    @pytest.mark.asyncio
    async def test_batch_indexing(self, rag_sage):

    """バッチインデックスのテスト""" テストコンテンツ",
                source=f"test/doc_{i}.md",
                metadata=DocumentMetadata(
                    title=f"Test Document {i}",
                    category="test"
                )
            )
            for i in range(50)
        ]
        
        # Act
        results = await rag_sage.batch_index_documents(documents)
        
        # Assert
        assert results.total_documents == 50
        assert results.successful_count == 50
        assert results.failed_count == 0
        assert results.total_time_ms < 5000  # 5秒以内
    
    @pytest.mark.asyncio
    async def test_search_caching(self, rag_sage):

                """検索キャッシュのテスト"""
    """品質保証テスト（Elder Guild品質基準）"""
    
    @pytest.fixture
    async def rag_sage(self):

    """RAG Sageインスタンスの作成"""
            test_db_path.unlink()
    
    @pytest.mark.asyncio
    async def test_iron_will_compliance(self, rag_sage):

            """Iron Will遵守テスト - TODO/FIXME禁止"""
        """検索パフォーマンステスト"""
        # 1000ドキュメントをインデックス
        large_docs = [
            Document(
                id=str(uuid4()),
                content=f"Performance test document {i} with some content " * 10,
                source=f"perf/doc_{i}.md",
                metadata=DocumentMetadata(
                    title=f"Perf Doc {i}",
                    category="performance"
                )
            )
            for i in range(1000)
        ]
        
        await rag_sage.batch_index_documents(large_docs)
        
        # 検索パフォーマンステスト
        query = SearchQuery(
            query="performance test",
            search_type=SearchType.FULL_TEXT,
            limit=100
        )
        
        import time
        start_time = time.time()
        results = await rag_sage.search(query)
        search_time = (time.time() - start_time) * 1000
        
        # Assert: 1000ドキュメントから100件を1秒以内に検索
        assert search_time < 1000
        assert len(results.results) <= 100
        assert results.total_count > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, rag_sage):

        """並行操作のテスト""" エラーなく完了
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])