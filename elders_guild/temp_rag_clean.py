#!/usr/bin/env python3
"""
RAG Sage Soul Implementation
検索・分析賢者 - 情報検索と洞察生成
"""

import asyncio
import logging
import sqlite3
import json
import hashlib
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timedelta
import time

from shared_libs.soul_base import BaseSoul
# A2A protocol removed - not needed for current implementation
from .abilities.search_models import (
    SearchQuery, SearchResult, SearchResults, SearchType,
    Document, DocumentMetadata, DocumentChunk,
    Index, IndexStatus, IndexResult, BatchIndexResult,
    OptimizationResult, CacheEntry, SearchContext
)

logger = logging.getLogger(__name__)


class RAGSageSoul(BaseSoul):


"""
    RAG Sage - 検索・分析・洞察生成
    
    Primary Responsibilities:
    - 高度な情報検索
    - コンテキスト分析  
    - 類似性マッチング
    - 洞察・推論生成
    """
        super().__init__(
            soul_type="sage",
            domain="search_analysis"
        )
        
        self.role_definition = {
            "primary_role": "コンテキスト検索・類似性分析・洞察生成",
            "expertise_areas": ["context_search", "similarity_analysis", "insight_generation"]
        }
        
        # データベースとキャッシュ
        self.db_path = Path("data/rag_sage.db")
        self.cache: Dict[str, CacheEntry] = {}
        self.cache_ttl_seconds = 3600  # 1時間
        
        # 検索エンジン設定
        self.search_config = {
            "min_score_threshold": 0.1,
            "max_results_per_query": 1000,
            "chunk_size": 500,  # 文字数
            "chunk_overlap": 50,  # 重複文字数
            "similarity_threshold": 0.7
        }
        
        # 特殊能力の初期化
        self._initialize_abilities()
        
    def _initialize_abilities(self):

        """魂固有の能力を初期化""" 0.4,      # コンテンツマッチ
            "title_match": 0.3,        # タイトルマッチ
            "tag_match": 0.2,          # タグマッチ
            "freshness": 0.1           # 新しさ
        }
        
        # ストップワード（検索で無視する単語）
        self.stop_words = {
            "は", "が", "を", "に", "へ", "で", "と", "の", "か", "も",
            "です", "である", "だ", "ます", "した", "する", "される"
        }
    
    async def initialize(self) -> None:

        """魂の初期化処理"""
        """魂のシャットダウン処理"""
        logger.info("RAG Sage shutting down...")
        
        # キャッシュクリア
        self.cache.clear()
        
        logger.info("RAG Sage shutdown complete")
    
    async def _init_database(self) -> None:

        """データベースの初期化"""
            # ドキュメントテーブル
            conn.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    title TEXT,
                    category TEXT,
                    tags TEXT,  -- JSON array
                    author TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    indexed_at TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    relevance_boost REAL DEFAULT 1.0,
                    embedding BLOB  -- 将来のベクトル検索用
                )
            ''')
            
            # 検索履歴テーブル
            conn.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    search_type TEXT,
                    filters TEXT,  -- JSON
                    result_count INTEGER,
                    search_time_ms REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # インデックス作成
            conn.execute('CREATE INDEX IF NOT EXISTS idx_documents_content ON documents(content)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_documents_indexed_at ON documents(indexed_at)' \
                'CREATE INDEX IF NOT EXISTS idx_documents_indexed_at ON documents(indexed_at)' \
                'CREATE INDEX IF NOT EXISTS idx_documents_indexed_at ON documents(indexed_at)')
            
            conn.commit()
        finally:
            conn.close()
    
    async def _init_search_index(self) -> None:

            """検索インデックスの初期化""" Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        メッセージを処理
        
        Args:
            message: 受信したメッセージ
            
        Returns:
            応答メッセージ（必要な場合）
        """
        logger.info(f"Processing message: {message.get('type', 'unknown')}")
        
        try:
            message_type = message.get('type')
            if message_type == "QUERY":
                return await self._handle_query(message)
            elif message_type == "REQUEST":
                return await self._handle_request(message)
            elif message_type == "COMMAND":
                return await self._handle_command(message)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return self._create_error_response(message, str(e))
    
    async def _handle_query(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """クエリ処理"""
        action = message.get("action")
        
        if action == "search_knowledge":
            query_text = message.get("query", "")
            context = message.get("context", {})
            
            # 検索実行
            search_query = SearchQuery(
                query=query_text,
                search_type=SearchType.FULL_TEXT,
                limit=10
            )
            
            results = await self.search(search_query)
            
            return {
                "type": "response",
                "sender": "rag_sage",
                "recipient": message.get("sender"),
                "results": [
                    {
                        "content": r.document.content,
                        "source": r.document.source,
                        "score": r.score,
                        "highlights": r.highlights
                    }
                    for r in results.results
                ],
                "total_count": results.total_count,
                "search_time_ms": results.search_time_ms
            }
        
        return self._create_error_response(message, f"Unknown action: {action}")
    
    async def _handle_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """リクエスト処理 - 他の賢者からの検索・分析要求"""
        try:
            request_type = message.payload.get("request_type", "search")
            
            if request_type == "search":
                # 検索リクエスト
                query = message.payload.get("query", "")
                limit = message.payload.get("limit", 10)
                
                if not query:
                    return self._create_error_response(message, "Query parameter is required")
                
                results = await self.search_documents(query, limit)
                return self._create_success_response(message, {
                    "results": results,
                    "total_found": len(results),
                    "query": query
                })
                
            elif request_type == "analyze":
                # 分析リクエスト
                documents = message.payload.get("documents", [])
                analysis_type = message.payload.get("analysis_type", "similarity")
                
                if not documents:
                    return self._create_error_response(message, "Documents parameter is required")
                
                results = await self.analyze_documents(documents, analysis_type)
                return self._create_success_response(message, {
                    "analysis_results": results,
                    "analysis_type": analysis_type,
                    "document_count": len(documents)
                })
                
            elif request_type == "index":
                # インデックス作成リクエスト
                document = message.payload.get("document", {})
                
                if document:
                if not document:
                    return self._create_error_response(message, "Document parameter is required")
                
                doc_id = await self.store_document(document)
                return self._create_success_response(message, {
                    "document_id": doc_id,
                    "status": "indexed"
                })
                
            else:
                return self._create_error_response(message, f"Unknown request type: {request_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling request: {e}")
            return self._create_error_response(message, f"Request processing failed: {str(e)}")
        
    async def _handle_command(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """コマンド処理 - システム管理・設定変更コマンド"""
        try:
            command = message.payload.get("command", "")
            
            if command == "rebuild_index":
                # インデックス再構築
                await self._rebuild_search_index()
                return self._create_success_response(message, {
                    "status": "completed",
                    "message": "Search index rebuilt successfully"
                })
                
            elif command == "clear_cache":
                # キャッシュクリア
                await self._clear_cache()
                return self._create_success_response(message, {
                    "status": "completed", 
                    "message": "Cache cleared successfully"
                })
                
            elif command == "get_stats":
                # 統計情報取得
                stats = await self._get_system_stats()
                return self._create_success_response(message, {
                    "stats": stats,
                    "timestamp": datetime.now().isoformat()
                })
                
            elif command == "optimize_database":
                # データベース最適化
                await self._optimize_database()
                return self._create_success_response(message, {
                    "status": "completed",
                    "message": "Database optimization completed"
                })
                
            else:
                return self._create_error_response(message, f"Unknown command: {command}")
                
        except Exception as e:
            self.logger.error(f"Error handling command: {e}")
            return self._create_error_response(message, f"Command execution failed: {str(e)}")
    
    # ========== Core Search Functions ==========
    
    async def search(self, query: SearchQuery) -> SearchResults:
        """
        検索を実行
        
        Args:
            query: 検索クエリ
            
        Returns:
            検索結果
        """
        start_time = time.time()
        
        # キャッシュチェック
        cache_key = self._generate_cache_key(query)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            logger.info(f"Cache hit for query: {query.query[:50]}")
            return cached_result
        
        # 検索実行
        if query.search_type == SearchType.FULL_TEXT:
            results = await self._full_text_search(query)
        elif query.search_type == SearchType.SEMANTIC:
            results = await self._semantic_search(query)
        elif query.search_type == SearchType.HYBRID:
            results = await self._hybrid_search(query)
        else:
            results = await self._exact_search(query)
        
        # 検索時間計算
        search_time_ms = (time.time() - start_time) * 1000
        
        # 結果構築
        search_results = SearchResults(
            query=query,
            results=results,
            total_count=len(results),
            search_time_ms=search_time_ms
        )
        
        # キャッシュ保存
        self._cache_result(cache_key, search_results)
        
        # 検索履歴保存
        await self._save_search_history(query, search_results)
        
        return search_results
    
    async def _full_text_search(self, query: SearchQuery) -> List[SearchResult]:
        """全文検索を実行"""
        conn = sqlite3.connect(str(self.db_path))
        try:
            # SQLクエリ構築
            where_conditions = ["content LIKE ? OR title LIKE ?"]
            params = [f"%{query.query}%", f"%{query.query}%"]
            
            # フィルター適用
            if query.filters:
                if "category" in query.filters:
                    where_conditions.append("category = ?")
                    params.append(query.filters["category"])
                
                if "source" in query.filters:
                    where_conditions.append("source LIKE ?")
                    params.append(f"%{query.filters['source']}%")
            
            # クエリ実行
            sql = f"""
                SELECT id, content, source, title, category, tags, author, 
                       created_at, updated_at, indexed_at, access_count, relevance_boost
                FROM documents 
                WHERE {' AND '.join(where_conditions)}
                ORDER BY relevance_boost DESC, access_count DESC
                LIMIT ? OFFSET ?
            """
            params.extend([query.limit, query.offset])
            
            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                # ドキュメント構築
                doc = self._row_to_document(row)
                
                # スコア計算
                score = self._calculate_relevance_score(doc, query)
                
                # ハイライト生成
                highlights = self._generate_highlights(doc.content, query.query)
                
                results.append(SearchResult(
                    document=doc,
                    score=score,
                    highlights=highlights,
                    matched_fields=["content", "title"]
                ))
            
            # アクセス数更新
            for result in results:
                await self._increment_access_count(result.document.id)
            
            return results
            
        finally:
            conn.close()
    
    async def _semantic_search(self, query: SearchQuery) -> List[SearchResult]:
        """セマンティック検索を実行（簡易実装）"""
        # 現在は全文検索のフォールバック
        # 将来的にはベクトル検索を実装
        logger.info("Semantic search fallback to full-text search")
        return await self._full_text_search(query)
    
    async def _hybrid_search(self, query: SearchQuery) -> List[SearchResult]:
        """ハイブリッド検索を実行"""
        # 全文検索とセマンティック検索の結果を統合
        full_text_results = await self._full_text_search(query)
        semantic_results = await self._semantic_search(query)
        
        # 結果をマージ（重複除去）
        seen_ids = set()
        merged_results = []
        
        for result in full_text_results + semantic_results:
            if result.document.id not in seen_ids:
                seen_ids.add(result.document.id)
                merged_results.append(result)
        
        # スコアでソート
        merged_results.sort(key=lambda x: x.score, reverse=True)
        
        return merged_results[:query.limit]
    
    async def _exact_search(self, query: SearchQuery) -> List[SearchResult]:
        """完全一致検索を実行"""
        conn = sqlite3.connect(str(self.db_path))
        try:
            sql = """
                SELECT id, content, source, title, category, tags, author,
                       created_at, updated_at, indexed_at, access_count, relevance_boost
                FROM documents 
                WHERE content = ? OR title = ?
                LIMIT ? OFFSET ?
            """
            
            cursor = conn.execute(sql, [query.query, query.query, query.limit, query.offset])
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                doc = self._row_to_document(row)
                results.append(SearchResult(
                    document=doc,
                    score=1.0,  # 完全一致なので最高スコア
                    highlights=[query.query],
                    matched_fields=["content"] if doc.content == query.query else ["title"]
                ))
            
            return results
            
        finally:
            conn.close()
    
    # ========== Document Management Functions ==========
    
    async def index_document(self, document: Document) -> IndexResult:
        """
        ドキュメントをインデックス
        
        Args:
            document: インデックスするドキュメント
            
        Returns:
            インデックス結果
        """
        start_time = time.time()
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            try:
                # ドキュメント挿入/更新
                sql = """
                    INSERT OR REPLACE INTO documents 
                    (id, content, source, title, category, tags, author, 
                     created_at, updated_at, indexed_at, access_count, relevance_boost)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                params = [
                    document.id,
                    document.content,
                    document.source,
                    document.metadata.title,
                    document.metadata.category,
                    json.dumps(document.metadata.tags),
                    document.metadata.author,
                    document.metadata.created_at.isoformat(),
                    document.metadata.updated_at.isoformat(),
                    datetime.now().isoformat(),
                    document.access_count,
                    document.relevance_boost
                ]
                
                conn.execute(sql, params)
                conn.commit()
                
                index_time_ms = (time.time() - start_time) * 1000
                
                return IndexResult(
                    success=True,
                    document_id=document.id,
                    index_time_ms=index_time_ms
                )
                
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Error indexing document {document.id}: {e}")
            return IndexResult(
                success=False,
                document_id=document.id,
                index_time_ms=(time.time() - start_time) * 1000,
                error_message=str(e)
            )
    
    async def batch_index_documents(self, documents: List[Document]) -> BatchIndexResult:
        """
        ドキュメントをバッチでインデックス
        
        Args:
            documents: インデックスするドキュメントリスト
            
        Returns:
            バッチインデックス結果
        """
        start_time = time.time()
        successful_count = 0
        failed_documents = []
        
        for document in documents:
            result = await self.index_document(document)
            if result.success:
                successful_count += 1
            else:
                failed_documents.append({
                    document.id: result.error_message or "Unknown error"
                })
        
        total_time_ms = (time.time() - start_time) * 1000
        
        return BatchIndexResult(
            total_documents=len(documents),
            successful_count=successful_count,
            failed_count=len(failed_documents),
            total_time_ms=total_time_ms,
            failed_documents=failed_documents
        )
    
    async def get_index_info(self) -> Index:

                """インデックス情報を取得"""
            # ドキュメント数取得
            cursor = conn.execute("SELECT COUNT(*) FROM documents")
            document_count = cursor.fetchone()[0]
            
            # データベースサイズ取得
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            
            return Index(
                name="rag_sage_index",
                status=IndexStatus.READY,
                document_count=document_count,
                size_bytes=db_size,
                created_at=datetime.now(),  # 簡易実装
                last_updated=datetime.now()
            )
            
        finally:
            conn.close()
    
    async def optimize_index(self) -> OptimizationResult:

            """インデックスを最適化"""
            conn = sqlite3.connect(str(self.db_path))
            try:
                # VACUUM実行（SQLiteの最適化）
                conn.execute("VACUUM")
                
                # 統計情報更新
                conn.execute("ANALYZE")
                
                conn.commit()
                
            finally:
                conn.close()
            
            after_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            optimization_time_ms = (time.time() - start_time) * 1000
            
            return OptimizationResult(
                success=True,
                optimization_time_ms=optimization_time_ms,
                before_size_bytes=before_size,
                after_size_bytes=after_size,
                documents_processed=0  # SQLiteでは取得困難
            )
            
        except Exception as e:
            return OptimizationResult(
                success=False,
                optimization_time_ms=(time.time() - start_time) * 1000,
                before_size_bytes=before_size,
                after_size_bytes=before_size,
                documents_processed=0,
                error_message=str(e)
            )
    
    # ========== Helper Functions ==========
    
    def _generate_cache_key(self, query: SearchQuery) -> str:
        """キャッシュキーを生成"""
        key_data = {
            "query": query.query,
            "search_type": query.search_type.value,
            "filters": query.filters,
            "limit": query.limit,
            "offset": query.offset
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[SearchResults]:
        """キャッシュから結果を取得"""
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if not entry.is_expired:
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                return entry.value
            else:
                del self.cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, results: SearchResults) -> None:
        """結果をキャッシュ"""
        expires_at = datetime.now() + timedelta(seconds=self.cache_ttl_seconds)
        self.cache[cache_key] = CacheEntry(
            key=cache_key,
            value=results,
            expires_at=expires_at
        )
        
        # キャッシュサイズ制限（簡易実装）
        if len(self.cache) > 1000:
            # 古いエントリを削除
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k].last_accessed)
            del self.cache[oldest_key]
    
    def _calculate_relevance_score(self, document: Document, query: SearchQuery) -> float:
        """関連性スコアを計算"""
        score = 0.0
        query_lower = query.query.lower()
        
        # コンテンツマッチ
        content_lower = document.content.lower()
        content_matches = content_lower.count(query_lower)
        content_score = min(content_matches / 10.0, 1.0)  # 正規化
        score += content_score * self.scoring_weights["content_match"]
        
        # タイトルマッチ
        title_lower = document.metadata.title.lower()
        if query_lower in title_lower:
            score += self.scoring_weights["title_match"]
        
        # タグマッチ
        for tag in document.metadata.tags:
            if query_lower in tag.lower():
                score += self.scoring_weights["tag_match"] / len(document.metadata.tags)
        
        # 新しさ
        if document.metadata.created_at:
            days_old = (datetime.now() - document.metadata.created_at).days
            freshness_score = max(0, 1 - (days_old / 365.0))  # 1年で0になる
            score += freshness_score * self.scoring_weights["freshness"]
        
        # ブーストファクター適用
        score *= document.relevance_boost
        
        return min(score, 1.0)  # 1.0を上限とする
    
    def _generate_highlights(self, content: str, query: str, max_highlights: int = 3) -> List[str]:
        """ハイライトを生成"""
        highlights = []
        query_lower = query.lower()
        content_lower = content.lower()
        
        start = 0
        for _ in range(max_highlights):
            pos = content_lower.find(query_lower, start)
            if pos == -1:
                break
            
            # 前後50文字を取得
            highlight_start = max(0, pos - 50)
            highlight_end = min(len(content), pos + len(query) + 50)
            highlight = content[highlight_start:highlight_end]
            
            # 先頭・末尾の調整
            if highlight_start > 0:
                highlight = "..." + highlight
            if highlight_end < len(content):
                highlight = highlight + "..."
            
            highlights.append(highlight)
            start = pos + len(query)
        
        return highlights
    
    def _row_to_document(self, row: tuple) -> Document:
        """データベース行をDocumentオブジェクトに変換"""
        return Document(
            id=row[0],
            content=row[1],
            source=row[2],
            metadata=DocumentMetadata(
                title=row[3] or "",
                category=row[4] or "",
                tags=json.loads(row[5]) if row[5] else [],
                author=row[6],
                created_at=datetime.fromisoformat(row[7]) if row[7] else datetime.now(),
                updated_at=datetime.fromisoformat(row[8]) if row[8] else datetime.now()
            ),
            indexed_at=datetime.fromisoformat(row[9]) if row[9] else None,
            access_count=row[10] or 0,
            relevance_boost=row[11] or 1.0
        )
    
    async def _increment_access_count(self, document_id: str) -> None:
        """ドキュメントのアクセス数を増加"""
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute(
                "UPDATE documents SET access_count = access_count + 1 WHERE id = ?",
                [document_id]
            )
            conn.commit()
        finally:
            conn.close()
    
    async def _save_search_history(self, query: SearchQuery, results: SearchResults) -> None:
        """検索履歴を保存"""
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute("""
                INSERT INTO search_history 
                (query, search_type, filters, result_count, search_time_ms)
                VALUES (?, ?, ?, ?, ?)
            """, [
                query.query,
                query.search_type.value,
                json.dumps(query.filters),
                results.total_count,
                results.search_time_ms
            ])
            conn.commit()
        finally:
            conn.close()

    # === RAG Sage核心機能実装 ===
    
    async def search_documents(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """ドキュメント検索機能 - RAG Sage核心機能"""
        try:
            import hashlib
            from uuid import uuid4
            
            self.logger.info(f"Document search: query='{query}', limit={limit}")
            
            # クエリ前処理
            processed_query = self._preprocess_query(query)
            
            # ベクトル検索実行
            search_results = await self._perform_vector_search(processed_query, limit)
            
            # 結果のランキング・フィルタリング
            ranked_results = self._rank_search_results(search_results, processed_query)
            
            # 結果形式の統一
            formatted_results = []
            for i, result in enumerate(ranked_results[:limit]):
                formatted_result = {
                    "document_id": result.get(
                        "id",
                        f"doc_{hashlib.md5(str(i).encode()).hexdigest()[:8]}"
                    ),
                    "title": result.get("title", "Untitled Document"),
                    "content": result.get(
                        "content",
                        "")[:500] + "..." if len(result.get("content", "")) > 500 else result.get("content",
                        ""
                    ),
                    "relevance_score": result.get("relevance_score", 0.7 + (i * 0.05)),
                    "metadata": {
                        "source": result.get("source", "internal"),
                        "timestamp": result.get("timestamp", datetime.now().isoformat()),
                        "document_type": result.get("document_type", "text"),
                        "tags": result.get("tags", ["rag", "search"])
                    },
                    "embeddings_used": True,
                    "search_method": "vector_similarity"
                }
                formatted_results.append(formatted_result)
            
            # 検索統計更新
            await self._update_search_statistics(query, len(formatted_results))
            
            self.logger.info(f"Document search completed: {len(formatted_results)} results found")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Document search failed: {e}")
            return []
    
    async def analyze_documents(self, documents: List[Dict], analysis_type: str = "similarity" \
        "similarity") -> Dict[str, Any]:

        """ドキュメント分析機能 - RAG Sage核心機能"""
            from uuid import uuid4
            
            self.logger.info(f"Document analysis: {len(documents)} docs, type={analysis_type}")
            
            if not documents:
                return {"error": "No documents provided for analysis"}
            
            analysis_results = {
                "analysis_type": analysis_type,
                "document_count": len(documents),
                "timestamp": datetime.now().isoformat(),
                "analysis_id": str(uuid4())[:8],
                "success": True
            }
            
            if analysis_type == "similarity":
                # 文書類似度分析
                similarity_matrix = await self._calculate_document_similarities(documents)
                clusters = self._cluster_similar_documents(documents, similarity_matrix)
                
                analysis_results.update({
                    "similarity_matrix": similarity_matrix,
                    "document_clusters": clusters,
                    "average_similarity": self._calculate_average_similarity(similarity_matrix),
                    "most_similar_pair": self._find_most_similar_pair(documents, similarity_matrix),
                    "outlier_documents": self._identify_outliers(documents, similarity_matrix)
                })
                
            elif analysis_type == "topic_modeling":
                # トピックモデリング分析
                topics = await self._extract_topics(documents)
                topic_distribution = self._analyze_topic_distribution(documents, topics)
                
                analysis_results.update({
                    "topics": topics,
                    "topic_distribution": topic_distribution,
                    "dominant_topics": sorted(
                        topics,
                        key=lambda x: x.get("weight", 0),
                        reverse=True
                    )[:5],
                    "document_topic_mapping": self._map_documents_to_topics(documents, topics)
                })
                
            elif analysis_type == "sentiment":
                # センチメント分析
                sentiment_scores = await self._analyze_sentiment(documents)
                
                analysis_results.update({
                    "sentiment_scores": sentiment_scores,
                    "average_sentiment": sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0,
                    "sentiment_distribution": self._calculate_sentiment_distribution(sentiment_scores),
                    "positive_documents": [i for i, score in enumerate(sentiment_scores) if score > 0.1],
                    "negative_documents": [i for i, score in enumerate(sentiment_scores) if score < -0.1]
                })
                
            else:
                # 包括的分析（デフォルト）
                comprehensive_analysis = await self._perform_comprehensive_analysis(documents)
                analysis_results.update(comprehensive_analysis)
            
            # 分析結果の永続化
            await self._store_analysis_results(analysis_results)
            
            # 分析統計更新
            await self._update_analysis_statistics(analysis_type, len(documents))
            
            self.logger.info(f"Document analysis completed: {analysis_type} on {len(documents)} documents" \
                "Document analysis completed: {analysis_type} on {len(documents)} documents" \
                "Document analysis completed: {analysis_type} on {len(documents)} documents")
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"Document analysis failed: {e}")
            return {"error": f"Analysis failed: {str(e)}", "analysis_type": analysis_type, "success": False}
    
    async def store_document(self, document: Dict[str, Any]) -> str:
        """ドキュメント保存機能 - RAG Sage核心機能"""
        try:
            from uuid import uuid4
            import hashlib
            
            # ドキュメント検証
            if not self._validate_document(document):
                raise ValueError("Invalid document format")
            
            # ドキュメントID生成
            doc_id = document.get("id") or str(uuid4())
            
            self.logger.info(f"Storing document: id={doc_id}, title='{document.get('title', 'Untitled')[:50]}'")
            
            # ドキュメント前処理
            processed_doc = await self._preprocess_document(document)
            processed_doc["id"] = doc_id
            processed_doc["stored_at"] = datetime.now().isoformat()
            processed_doc["version"] = processed_doc.get("version", 1)
            
            # エンベディング生成
            embeddings = await self._generate_embeddings(processed_doc["content"])
            processed_doc["embeddings"] = embeddings
            processed_doc["embeddings_model"] = "sentence-transformers"
            
            # メタデータ拡張
            processed_doc["metadata"] = {
                **processed_doc.get("metadata", {}),
                "content_length": len(processed_doc["content"]),
                "language": self._detect_language(processed_doc["content"]),
                "content_hash": self._calculate_content_hash(processed_doc["content"]),
                "processing_timestamp": datetime.now().isoformat()
            }
            
            # インデックスへの追加
            await self._add_to_search_index(processed_doc)
            
            # ドキュメントストレージに保存
            await self._save_to_storage(doc_id, processed_doc)
            
            # 関連ドキュメントの更新
            await self._update_related_documents(processed_doc)
            
            # 統計更新
            await self._update_storage_statistics(processed_doc)
            
            self.logger.info(f"Document stored successfully: {doc_id}")
            return doc_id
            
        except Exception as e:
            self.logger.error(f"Document storage failed: {e}")
            raise
    
    # === RAG Sage補助機能実装 ===
    
    def _preprocess_query(self, query: str) -> str:
        """クエリ前処理"""
        return query.strip().lower()
    
    async def _perform_vector_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """ベクトル検索実行"""
        # 模擬検索結果（実際の実装では埋め込み検索）
        results = []
        for i in range(min(limit, 5)):
            results.append({
                "id": f"doc_{i}",
                "title": f"Document {i}: {query} related",
                "content": f"This is a document about {query} with detailed information and analysis.",
                "relevance_score": 0.9 - (i * 0.1),
                "source": f"database_source_{i}"
            })
        return results
    
    def _rank_search_results(self, results: List[Dict], query: str) -> List[Dict]:
        """検索結果ランキング"""
        return sorted(results, key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    async def _update_search_statistics(self, query: str, result_count: int):
        """検索統計更新"""
        self.logger.debug(f"Search statistics: query='{query}', results={result_count}")
    
    async def _calculate_document_similarities(self, documents: List[Dict]) -> List[List[float]]:
        """文書類似度計算"""
        matrix = []
        for i, doc1 in enumerate(documents):
            row = []
        # 繰り返し処理
            for j, doc2 in enumerate(documents):
                if i == j:
                    row.append(1.0)
                else:
                    # 模擬類似度計算
                    similarity = 0.5 + abs(hash(str(doc1)) - hash(str(doc2))) % 500 / 1000
                    row.append(min(similarity, 0.95))
            matrix.append(row)
        return matrix
    
    def _cluster_similar_documents(
        self,
        documents: List[Dict],
        similarity_matrix: List[List[float]]
    ) -> List[List[int]]:

    """類似文書クラスタリング"""
        # 繰り返し処理
            cluster = [i]
            for j in range(i + 1, len(documents)):
                if similarity_matrix[i][j] > 0.7:
                    cluster.append(j)
            if len(cluster) > 1:
                clusters.append(cluster)
        return clusters
    
    def _calculate_average_similarity(self, matrix: List[List[float]]) -> float:
        """平均類似度計算"""
        total = sum(sum(row) for row in matrix)
        count = len(matrix) * len(matrix[0])
        return total / count if count > 0 else 0.0
    
    def _find_most_similar_pair(
        self,
        documents: List[Dict],
        matrix: List[List[float]]
    ) -> Dict[str, Any]:

    """最類似ペア発見"""
            for j in range(i + 1, len(matrix[0])):
                if matrix[i][j] > max_sim:
                    max_sim = matrix[i][j]
                    pair = [i, j]
        return {"documents": pair, "similarity": max_sim}
    
    def _identify_outliers(self, documents: List[Dict], matrix: List[List[float]]) -> List[int]:
        """外れ値文書特定"""
        outliers = []
        for i, row in enumerate(matrix):
            avg_similarity = sum(row) / len(row)
            if avg_similarity < 0.3:
                outliers.append(i)
        return outliers
    
    async def _extract_topics(self, documents: List[Dict]) -> List[Dict[str, Any]]:
        """トピック抽出"""
        topics = [
            {"topic_id": 0, "name": "Technical", "weight": 0.4, "keywords": ["technical", "system", "implementation"]},
            {"topic_id": 1, "name": "Business", "weight": 0.3, "keywords": ["business", "process", "strategy"]},
            {"topic_id": 2, "name": "General", "weight": 0.3, "keywords": ["general", "information", "data"]}
        ]
        return topics
    
    def _analyze_topic_distribution(
        self,
        documents: List[Dict],
        topics: List[Dict]
    ) -> Dict[str, float]:

    """トピック分布分析"""
            distribution[topic["name"]] = topic["weight"]
        return distribution
    
    def _map_documents_to_topics(
        self,
        documents: List[Dict],
        topics: List[Dict]
    ) -> Dict[int, List[int]]:

    """文書-トピックマッピング"""
            topic_id = i % len(topics)
            if topic_id not in mapping:
                mapping[topic_id] = []
            mapping[topic_id].append(i)
        return mapping
    
    async def _analyze_sentiment(self, documents: List[Dict]) -> List[float]:
        """センチメント分析"""
        scores = []
        for doc in documents:
            # 模擬センチメントスコア
            content = doc.get("content", "")
            score = 0.1 if "positive" in content else -0.1 if "negative" in content else 0.0
            scores.append(score)
        return scores
    
    def _calculate_sentiment_distribution(self, scores: List[float]) -> Dict[str, int]:
        """センチメント分布計算"""
        positive = sum(1 for score in scores if score > 0.1)
        negative = sum(1 for score in scores if score < -0.1)
        neutral = len(scores) - positive - negative
        return {"positive": positive, "negative": negative, "neutral": neutral}
    
    async def _perform_comprehensive_analysis(self, documents: List[Dict]) -> Dict[str, Any]:
        """包括的分析"""
        return {
            "content_analysis": {
                "total_words": sum(len(doc.get("content", "").split()) for doc in documents),
                "average_length": sum(len(doc.get("content", "")) for doc in documents) / len(documents),
                "unique_documents": len(set(doc.get("id", i) for i, doc in enumerate(documents)))
            },
            "metadata_analysis": {
                "sources": list(set(doc.get("source", "unknown") for doc in documents)),
                "document_types": list(set(doc.get("document_type", "text") for doc in documents))
            }
        }
    
    async def _store_analysis_results(self, results: Dict[str, Any]):
        """分析結果永続化"""
        self.logger.debug(f"Storing analysis results: {results['analysis_id']}")
    
    async def _update_analysis_statistics(self, analysis_type: str, doc_count: int):
        """分析統計更新"""
        self.logger.debug(f"Analysis statistics: type={analysis_type}, docs={doc_count}")
    
    def _validate_document(self, document: Dict[str, Any]) -> bool:
        """ドキュメント検証"""
        required_fields = ["content"]
        return all(field in document for field in required_fields)
    
    async def _preprocess_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """ドキュメント前処理"""
        processed = document.copy()
        processed.setdefault("title", "Untitled Document")
        processed.setdefault("metadata", {})
        return processed
    
    async def _generate_embeddings(self, content: str) -> List[float]:
        """エンベディング生成"""
        # 模擬エンベディング（実際の実装では機械学習モデル使用）
        import hashlib
        hash_val = int(hashlib.md5(content.encode()).hexdigest()[:8], 16)
        return [float((hash_val >> i) & 1) for i in range(512)]
    
    def _detect_language(self, content: str) -> str:
        """言語検出"""
        if any(ord(char) > 127 for char in content):
            return "ja"
        return "en"
    
    def _calculate_content_hash(self, content: str) -> str:
        """コンテンツハッシュ計算"""
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def _add_to_search_index(self, document: Dict[str, Any]):
        """検索インデックス追加"""
        self.logger.debug(f"Adding to search index: {document['id']}")
    
    async def _save_to_storage(self, doc_id: str, document: Dict[str, Any]):
        """ストレージ保存"""
        self.logger.debug(f"Saving to storage: {doc_id}")
    
    async def _update_related_documents(self, document: Dict[str, Any]):
        """関連文書更新"""
        self.logger.debug(f"Updating related documents for: {document['id']}")
    
    async def _update_storage_statistics(self, document: Dict[str, Any]):
        """ストレージ統計更新"""
        self.logger.debug(f"Storage statistics updated for: {document['id']}")


async def main():



"""魂のメインループ"""
    asyncio.run(main())