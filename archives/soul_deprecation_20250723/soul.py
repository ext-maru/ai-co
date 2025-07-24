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
    
    def __init__(self):
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
        """魂固有の能力を初期化"""
        # 検索アルゴリズム設定
        self.scoring_weights = {
            "content_match": 0.4,      # コンテンツマッチ
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
        logger.info("RAG Sage initializing...")
        
        # データベース初期化
        await self._init_database()
        
        # インデックス初期化
        await self._init_search_index()
        
        logger.info("RAG Sage initialized successfully")
    
    async def shutdown(self) -> None:
        """魂のシャットダウン処理"""
        logger.info("RAG Sage shutting down...")
        
        # キャッシュクリア
        self.cache.clear()
        
        logger.info("RAG Sage shutdown complete")
    
    async def _init_database(self) -> None:
        """データベースの初期化"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3connect(str(self.db_path))
        try:
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
            conn.execute('CREATE INDEX IF NOT EXISTS idx_documents_indexed_at ON documents(indexed_at)')
            
            conn.commit()
        finally:
            conn.close()
    
    async def _init_search_index(self) -> None:
        """検索インデックスの初期化"""
        # 将来的にはElasticsearchやSolrなどの外部検索エンジンとの統合
        pass
    
    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
        """リクエスト処理"""
        # 実装予定
        pass
        
    async def _handle_command(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """コマンド処理"""
        # 実装予定
        pass
    
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
        conn = sqlite3connect(str(self.db_path))
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
        conn = sqlite3connect(str(self.db_path))
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
            conn = sqlite3connect(str(self.db_path))
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
        conn = sqlite3connect(str(self.db_path))
        try:
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
        start_time = time.time()
        before_size = self.db_path.stat().st_size if self.db_path.exists() else 0
        
        try:
            conn = sqlite3connect(str(self.db_path))
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
        conn = sqlite3connect(str(self.db_path))
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
        conn = sqlite3connect(str(self.db_path))
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


async def main():
    """魂のメインループ"""
    soul = RAGSageSoul()
    await soul.start()


if __name__ == "__main__":
    asyncio.run(main())