#!/usr/bin/env python3
"""
🔍 RAG Manager Real
RAG (Retrieval-Augmented Generation) 管理システム

Created: 2025-07-17
Author: Claude Elder
Version: 2.0.0 - Elder Legacy準拠
Architecture: Elders Legacy AI層
"""

import asyncio
import json
import sqlite3
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import sys

# Elder Legacy統合
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.elders_legacy import EldersAILegacy, enforce_boundary, DomainBoundary


class DocumentType(Enum):
    """ドキュメントタイプ"""
    CODE = "code"
    DOCUMENTATION = "documentation"
    KNOWLEDGE_BASE = "knowledge_base"
    CONVERSATION = "conversation"
    TUTORIAL = "tutorial"
    SPECIFICATION = "specification"


class RetrievalStrategy(Enum):
    """検索戦略"""
    SIMILARITY = "similarity"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    SEMANTIC = "semantic"


@dataclass
class Document:
    """ドキュメント"""
    id: str
    content: str
    doc_type: DocumentType
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Query:
    """クエリ"""
    text: str
    strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    limit: int = 5
    filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalResult:
    """検索結果"""
    document: Document
    score: float
    relevance: str


@dataclass
class RAGResponse:
    """RAG応答"""
    query: str
    answer: str
    sources: List[RetrievalResult]
    confidence: float
    generated_at: datetime = field(default_factory=datetime.now)


class RAGManager(EldersAILegacy):
    """
    🔍 RAG管理システム
    Elder Legacy AI層準拠のRAG統合管理システム
    """
    
    def __init__(self, db_path: str = "data/rag_knowledge.db", config: Optional[Dict[str, Any]] = None):
        """
        RAG管理システム初期化
        
        Args:
            db_path: データベースパス
            config: 設定辞書
        """
        super().__init__(name="RAGManager")
        self.db_path = Path(db_path)
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # データベースディレクトリ作成
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # データベース初期化
        self._initialize_database_sync()
        
        # インメモリインデックス
        self.document_index: Dict[str, Document] = {}
        self.keyword_index: Dict[str, Set[str]] = {}
    
    @enforce_boundary(DomainBoundary.WISDOM, "process_request")
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        RAGリクエスト処理
        
        Args:
            request: リクエストデータ
            
        Returns:
            処理結果
        """
        try:
            operation = request.get("operation", "unknown")
            
            if operation == "add_document":
                return await self._add_document(
                    request.get("content"),
                    request.get("doc_type", "knowledge_base"),
                    request.get("metadata", {})
                )
            elif operation == "search_documents":
                return await self._search_documents(
                    request.get("query"),
                    request.get("strategy", "hybrid"),
                    request.get("limit", 5)
                )
            elif operation == "generate_answer":
                return await self._generate_answer(
                    request.get("query"),
                    request.get("context", [])
                )
            elif operation == "get_document":
                return await self._get_document(request.get("doc_id"))
            elif operation == "delete_document":
                return await self._delete_document(request.get("doc_id"))
            elif operation == "get_stats":
                return await self._get_stats()
            elif operation == "health_check":
                return await self._health_check()
            else:
                return {
                    "status": "error",
                    "message": f"Unknown operation: {operation}",
                    "operation": operation
                }
                
        except Exception as e:
            self.logger.error(f"Error processing request: {e}")
            return {
                "status": "error",
                "message": str(e),
                "operation": request.get("operation", "unknown")
            }
    
    async def validate_request(self, request: Dict[str, Any]) -> bool:
        """
        リクエスト検証
        
        Args:
            request: 検証対象リクエスト
            
        Returns:
            検証結果
        """
        if not isinstance(request, dict):
            return False
            
        operation = request.get("operation")
        if not operation:
            return False
            
        # 操作別検証
        if operation == "add_document":
            return "content" in request
        elif operation == "search_documents":
            return "query" in request
        elif operation == "generate_answer":
            return "query" in request
        elif operation in ["get_document", "delete_document"]:
            return "doc_id" in request
        elif operation in ["get_stats", "health_check"]:
            return True
        else:
            return False
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        システム機能情報取得
        
        Returns:
            機能情報
        """
        return {
            "name": "RAGManager",
            "version": "2.0.0",
            "domain": "WISDOM",
            "operations": [
                "add_document",
                "search_documents",
                "generate_answer",
                "get_document",
                "delete_document",
                "get_stats",
                "health_check"
            ],
            "features": [
                "ドキュメント管理",
                "類似性検索",
                "キーワード検索",
                "ハイブリッド検索",
                "回答生成",
                "Elder Legacy準拠"
            ],
            "document_types": [dt.value for dt in DocumentType],
            "strategies": [rs.value for rs in RetrievalStrategy],
            "db_path": str(self.db_path),
            "config": self.config
        }
    
    def _initialize_database_sync(self) -> None:
        """データベース初期化（同期版）"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # ドキュメントテーブル作成
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    doc_type TEXT NOT NULL,
                    metadata TEXT,
                    content_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # キーワードインデックステーブル作成
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keyword_index (
                    keyword TEXT,
                    doc_id TEXT,
                    frequency INTEGER DEFAULT 1,
                    PRIMARY KEY (keyword, doc_id),
                    FOREIGN KEY (doc_id) REFERENCES documents (id)
                )
            """)
            
            # インデックス作成
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_type 
                ON documents(doc_type)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_hash 
                ON documents(content_hash)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_keyword_frequency 
                ON keyword_index(frequency DESC)
            """)
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"RAG database initialized: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        テキストからキーワード抽出
        
        Args:
            text: 対象テキスト
            
        Returns:
            キーワードリスト
        """
        # 簡易キーワード抽出（実際の実装では形態素解析等を使用）
        import re
        words = re.findall(r'\b\w+\b', text.lower())
        
        # ストップワード除去
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 
            'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'a', 'an', 'this', 'that', 'these', 'those', 'で', 'は', 'が', 
            'を', 'に', 'の', 'と', 'も', 'から', 'まで', 'です', 'である'
        }
        
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # 頻度計算
        from collections import Counter
        counter = Counter(keywords)
        
        # 頻度上位を返す
        return [word for word, freq in counter.most_common(20)]
    
    def _calculate_content_hash(self, content: str) -> str:
        """
        コンテンツハッシュ計算
        
        Args:
            content: コンテンツ
            
        Returns:
            ハッシュ値
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    async def _add_document(self, content: str, doc_type: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        ドキュメント追加
        
        Args:
            content: ドキュメント内容
            doc_type: ドキュメントタイプ
            metadata: メタデータ
            
        Returns:
            追加結果
        """
        try:
            # ドキュメントID生成
            doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(content.encode()).hexdigest()[:8]}"
            
            # コンテンツハッシュ計算
            content_hash = self._calculate_content_hash(content)
            
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 重複チェック
            cursor.execute("SELECT id FROM documents WHERE content_hash = ?", (content_hash,))
            existing = cursor.fetchone()
            
            if existing:
                conn.close()
                return {
                    "status": "warning",
                    "message": "Document with same content already exists",
                    "existing_id": existing[0],
                    "doc_id": doc_id
                }
            
            # ドキュメント保存
            cursor.execute("""
                INSERT INTO documents (id, content, doc_type, metadata, content_hash)
                VALUES (?, ?, ?, ?, ?)
            """, (doc_id, content, doc_type, json.dumps(metadata), content_hash))
            
            # キーワード抽出・保存
            keywords = self._extract_keywords(content)
            for keyword in keywords:
                cursor.execute("""
                    INSERT OR REPLACE INTO keyword_index (keyword, doc_id, frequency)
                    VALUES (?, ?, COALESCE((SELECT frequency FROM keyword_index WHERE keyword = ? AND doc_id = ?), 0) + 1)
                """, (keyword, doc_id, keyword, doc_id))
            
            conn.commit()
            conn.close()
            
            # インメモリインデックス更新
            doc = Document(
                id=doc_id,
                content=content,
                doc_type=DocumentType(doc_type),
                metadata=metadata
            )
            self.document_index[doc_id] = doc
            
            for keyword in keywords:
                if keyword not in self.keyword_index:
                    self.keyword_index[keyword] = set()
                self.keyword_index[keyword].add(doc_id)
            
            return {
                "status": "success",
                "message": "Document added successfully",
                "doc_id": doc_id,
                "keywords_count": len(keywords)
            }
            
        except Exception as e:
            self.logger.error(f"Error adding document: {e}")
            return {
                "status": "error",
                "message": str(e),
                "doc_id": None
            }
    
    async def _search_documents(self, query: str, strategy: str, limit: int) -> Dict[str, Any]:
        """
        ドキュメント検索
        
        Args:
            query: 検索クエリ
            strategy: 検索戦略
            limit: 結果数上限
            
        Returns:
            検索結果
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            results = []
            
            if strategy == "keyword":
                # キーワード検索
                query_keywords = self._extract_keywords(query)
                
                for keyword in query_keywords:
                    cursor.execute("""
                        SELECT d.id, d.content, d.doc_type, d.metadata, k.frequency
                        FROM documents d
                        JOIN keyword_index k ON d.id = k.doc_id
                        WHERE k.keyword LIKE ?
                        ORDER BY k.frequency DESC
                        LIMIT ?
                    """, (f"%{keyword}%", limit))
                    
                    for row in cursor.fetchall():
                        doc = Document(
                            id=row[0],
                            content=row[1],
                            doc_type=DocumentType(row[2]),
                            metadata=json.loads(row[3] or "{}")
                        )
                        score = row[4] / 10.0  # 正規化
                        results.append(RetrievalResult(doc, score, "keyword_match"))
            
            elif strategy == "similarity":
                # 類似性検索（簡易版 - 実際の実装ではベクトル類似度を使用）
                cursor.execute("""
                    SELECT id, content, doc_type, metadata
                    FROM documents
                    WHERE content LIKE ?
                    ORDER BY LENGTH(content) ASC
                    LIMIT ?
                """, (f"%{query}%", limit))
                
                for row in cursor.fetchall():
                    doc = Document(
                        id=row[0],
                        content=row[1],
                        doc_type=DocumentType(row[2]),
                        metadata=json.loads(row[3] or "{}")
                    )
                    # 簡易類似度計算
                    similarity = min(0.9, len(set(query.lower().split()) & set(doc.content.lower().split())) / len(query.split()))
                    results.append(RetrievalResult(doc, similarity, "content_similarity"))
            
            else:  # hybrid
                # ハイブリッド検索
                keyword_results = await self._search_documents(query, "keyword", limit // 2)
                similarity_results = await self._search_documents(query, "similarity", limit // 2)
                
                results = keyword_results["results"] + similarity_results["results"]
            
            conn.close()
            
            # 重複除去とスコア順ソート
            unique_results = {}
            for result in results:
                if isinstance(result, dict):
                    doc_id = result["document"]["id"]
                    if doc_id not in unique_results or result["score"] > unique_results[doc_id]["score"]:
                        unique_results[doc_id] = result
                else:
                    doc_id = result.document.id
                    if doc_id not in unique_results or result.score > unique_results[doc_id].score:
                        unique_results[doc_id] = result
            
            final_results = list(unique_results.values())
            final_results.sort(key=lambda x: x.score if hasattr(x, 'score') else x["score"], reverse=True)
            final_results = final_results[:limit]
            
            # 結果を辞書形式に変換
            formatted_results = []
            for result in final_results:
                if hasattr(result, 'document'):
                    formatted_results.append({
                        "document": {
                            "id": result.document.id,
                            "content": result.document.content[:500] + "..." if len(result.document.content) > 500 else result.document.content,
                            "doc_type": result.document.doc_type.value,
                            "metadata": result.document.metadata
                        },
                        "score": result.score,
                        "relevance": result.relevance
                    })
                else:
                    formatted_results.append(result)
            
            return {
                "status": "success",
                "query": query,
                "strategy": strategy,
                "results": formatted_results,
                "count": len(formatted_results)
            }
            
        except Exception as e:
            self.logger.error(f"Error searching documents: {e}")
            return {
                "status": "error",
                "message": str(e),
                "query": query,
                "results": []
            }
    
    async def _generate_answer(self, query: str, context: List[str]) -> Dict[str, Any]:
        """
        回答生成
        
        Args:
            query: 質問
            context: コンテキスト
            
        Returns:
            生成された回答
        """
        try:
            # コンテキストがない場合は検索
            if not context:
                search_result = await self._search_documents(query, "hybrid", 3)
                if search_result["status"] == "success":
                    context = [result["document"]["content"] for result in search_result["results"]]
            
            # 簡易回答生成（実際の実装ではLLMを使用）
            if context:
                answer = f"Based on the available information: {' '.join(context[:500])}"
                confidence = 0.8
            else:
                answer = "I don't have enough information to answer this question accurately."
                confidence = 0.2
            
            return {
                "status": "success",
                "query": query,
                "answer": answer,
                "confidence": confidence,
                "sources_count": len(context),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating answer: {e}")
            return {
                "status": "error",
                "message": str(e),
                "query": query
            }
    
    async def _get_document(self, doc_id: str) -> Dict[str, Any]:
        """
        ドキュメント取得
        
        Args:
            doc_id: ドキュメントID
            
        Returns:
            ドキュメント情報
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, content, doc_type, metadata, created_at, updated_at
                FROM documents WHERE id = ?
            """, (doc_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "status": "success",
                    "document": {
                        "id": row[0],
                        "content": row[1],
                        "doc_type": row[2],
                        "metadata": json.loads(row[3] or "{}"),
                        "created_at": row[4],
                        "updated_at": row[5]
                    }
                }
            else:
                return {
                    "status": "not_found",
                    "message": f"Document not found: {doc_id}",
                    "doc_id": doc_id
                }
                
        except Exception as e:
            self.logger.error(f"Error getting document: {e}")
            return {
                "status": "error",
                "message": str(e),
                "doc_id": doc_id
            }
    
    async def _delete_document(self, doc_id: str) -> Dict[str, Any]:
        """
        ドキュメント削除
        
        Args:
            doc_id: ドキュメントID
            
        Returns:
            削除結果
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 存在確認
            cursor.execute("SELECT id FROM documents WHERE id = ?", (doc_id,))
            if not cursor.fetchone():
                conn.close()
                return {
                    "status": "not_found",
                    "message": f"Document not found: {doc_id}",
                    "doc_id": doc_id
                }
            
            # キーワードインデックス削除
            cursor.execute("DELETE FROM keyword_index WHERE doc_id = ?", (doc_id,))
            
            # ドキュメント削除
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            
            conn.commit()
            conn.close()
            
            # インメモリインデックス更新
            if doc_id in self.document_index:
                del self.document_index[doc_id]
            
            for keyword_set in self.keyword_index.values():
                keyword_set.discard(doc_id)
            
            return {
                "status": "success",
                "message": f"Document deleted successfully",
                "doc_id": doc_id
            }
            
        except Exception as e:
            self.logger.error(f"Error deleting document: {e}")
            return {
                "status": "error",
                "message": str(e),
                "doc_id": doc_id
            }
    
    async def _get_stats(self) -> Dict[str, Any]:
        """
        統計情報取得
        
        Returns:
            統計情報
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 総ドキュメント数
            cursor.execute("SELECT COUNT(*) FROM documents")
            total_docs = cursor.fetchone()[0]
            
            # タイプ別ドキュメント数
            cursor.execute("SELECT doc_type, COUNT(*) FROM documents GROUP BY doc_type")
            type_counts = dict(cursor.fetchall())
            
            # 総キーワード数
            cursor.execute("SELECT COUNT(DISTINCT keyword) FROM keyword_index")
            total_keywords = cursor.fetchone()[0]
            
            # 最新のドキュメント
            cursor.execute("""
                SELECT id, doc_type, created_at FROM documents 
                ORDER BY created_at DESC LIMIT 5
            """)
            recent_docs = cursor.fetchall()
            
            conn.close()
            
            return {
                "status": "success",
                "stats": {
                    "total_documents": total_docs,
                    "total_keywords": total_keywords,
                    "type_distribution": type_counts,
                    "recent_documents": [
                        {"id": row[0], "type": row[1], "created_at": row[2]}
                        for row in recent_docs
                    ]
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _health_check(self) -> Dict[str, Any]:
        """
        ヘルスチェック
        
        Returns:
            ヘルス状態
        """
        try:
            # データベース接続テスト
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents")
            doc_count = cursor.fetchone()[0]
            conn.close()
            
            return {
                "status": "healthy",
                "database": "connected",
                "document_count": doc_count,
                "index_size": len(self.document_index),
                "keyword_index_size": len(self.keyword_index),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Convenience function for quick access
async def create_rag_manager(db_path: str = "data/rag_knowledge.db", config: Optional[Dict[str, Any]] = None) -> RAGManager:
    """
    RAG管理システム作成
    
    Args:
        db_path: データベースパス
        config: 設定辞書
        
    Returns:
        RAGManagerインスタンス
    """
    return RAGManager(db_path, config)


if __name__ == "__main__":
    async def test_rag_manager():
        """テスト実行"""
        rag = RAGManager("test_rag.db")
        
        # ドキュメント追加テスト
        result = await rag.process_request({
            "operation": "add_document",
            "content": "This is a test document about Python programming.",
            "doc_type": "documentation",
            "metadata": {"author": "test", "tags": ["python", "programming"]}
        })
        print("Add document:", result)
        
        # 検索テスト
        result = await rag.process_request({
            "operation": "search_documents",
            "query": "Python programming",
            "strategy": "hybrid",
            "limit": 3
        })
        print("Search results:", result)
        
        # 統計取得テスト
        result = await rag.process_request({
            "operation": "get_stats"
        })
        print("Stats:", result)
    
    asyncio.run(test_rag_manager())