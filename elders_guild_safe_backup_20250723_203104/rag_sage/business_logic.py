#!/usr/bin/env python3
"""
"🔍" RAG Sage Business Logic - 検索・分析・洞察生成
================================================

Elder Loop Phase 1: ビジネスロジック分離
フレームワーク依存なしの純粋なビジネスロジック実装

Author: Claude Elder
Created: 2025-07-23
"""

import asyncio
import logging
import sqlite3
import json
import hashlib
import time
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SearchType(Enum):
    pass


"""検索タイプ"""
    """ドキュメント"""
    id: str
    content: str
    source: str
    title: str = ""
    category: str = ""
    tags: List[str] = field(default_factory=list)
    author: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    indexed_at: Optional[datetime] = None
    access_count: int = 0
    relevance_boost: float = 1.0
    embedding: Optional[List[float]] = None


@dataclass
class SearchResult:
    pass



"""検索結果""" Document
    score: float
    highlights: List[str] = field(default_factory=list)
    matched_fields: List[str] = field(default_factory=list)


@dataclass
class SearchQuery:
    pass



"""検索クエリ""" str
    search_type: SearchType = SearchType.FULL_TEXT
    filters: Dict[str, Any] = field(default_factory=dict)
    limit: int = 10
    offset: int = 0
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IndexResult:
    pass



"""インデックス結果""" bool
    document_id: str
    index_time_ms: float
    error_message: Optional[str] = None


@dataclass
class CacheEntry:
    pass



"""キャッシュエントリ""" str
    value: Any
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 1
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at


class RAGProcessor:
    pass

        """
    RAG処理エンジン
    検索・分析・洞察生成のビジネスロジック
    """ str = "data/rag_sage.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # キャッシュ
        self.cache: Dict[str, CacheEntry] = {}
        self.cache_ttl_seconds = 3600  # 1時間
        
        # 検索設定
        self.search_config = {
            "min_score_threshold": 0.1,
            "max_results_per_query": 1000,
            "chunk_size": 500,
            "chunk_overlap": 50,
            "similarity_threshold": 0.7
        }
        
        # スコアリング重み
        self.scoring_weights = {
            "content_match": 0.4,
            "title_match": 0.3,
            "tag_match": 0.2,
            "freshness": 0.1
        }
        
        # ストップワード
        self.stop_words = {
            "は", "が", "を", "に", "へ", "で", "と", "の", "か", "も",
            "です", "である", "だ", "ます", "した", "する", "される"
        }
        
        # データベース初期化
        self._init_database()
        
        logger.info("RAG Processor initialized successfully")
    
    def _init_database(self):
        pass

        """データベース初期化"""
            # ドキュメントテーブル
            conn.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    title TEXT,
                    category TEXT,
                    tags TEXT,
                    author TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    indexed_at TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    relevance_boost REAL DEFAULT 1.0,
                    embedding BLOB
                )
            ''')
            
            # 検索履歴テーブル
            conn.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    search_type TEXT,
                    filters TEXT,
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
    
    async def process_action(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        アクション処理
        
        Args:
            action: アクション名
            data: アクションデータ
            
        Returns:
            処理結果
        """
        logger.info(f"Processing action: {action}")
        
        try:
            if action == "search_knowledge":
                return await self._search_knowledge_action(data)
            elif action == "index_document":
                return await self._index_document_action(data)
            elif action == "batch_index_documents":
                return await self._batch_index_documents_action(data)
            elif action == "get_similar_documents":
                return await self._get_similar_documents_action(data)
            elif action == "analyze_query_intent":
                return await self._analyze_query_intent_action(data)
            elif action == "generate_insights":
                return await self._generate_insights_action(data)
            elif action == "optimize_index":
                return await self._optimize_index_action(data)
            elif action == "get_search_statistics":
                return await self._get_search_statistics_action(data)
            elif action == "get_index_info":
                return await self._get_index_info_action(data)
            elif action == "delete_document":
                return await self._delete_document_action(data)
            elif action == "update_document_boost":
                return await self._update_document_boost_action(data)
            elif action == "health_check":
                return await self._health_check_action(data)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Error processing action {action}: {e}")
            return {"success": False, "error": str(e)}
    
    # === Action Handlers ===
    
    async def _search_knowledge_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """知識検索アクション"""
        try:
            # SearchQuery構築
            try:
                search_type = SearchType(data.get("search_type", "full_text"))
            except ValueError:
                return {"success": False, "error": f"Invalid search_type: {data.get('search_type')}"}
            
            query = SearchQuery(
                query=data.get("query", ""),
                search_type=search_type,
                filters=data.get("filters", {}),
                limit=data.get("limit", 10),
                offset=data.get("offset", 0),
                context=data.get("context", {})
            )
            
            # 検索実行
            results = await self._search(query)
            
            return {
                "success": True,
                "data": {
                    "results": [
                        {
                            "document_id": r.document.id,
                            "content": r.document.content,
                            "source": r.document.source,
                            "title": r.document.title,
                            "category": r.document.category,
                            "tags": r.document.tags,
                            "score": r.score,
                            "highlights": r.highlights,
                            "matched_fields": r.matched_fields
                        }
                        for r in results
                    ],
                    "total_count": len(results),
                    "query": query.query,
                    "search_type": query.search_type.value
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _index_document_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """ドキュメントインデックスアクション"""
        try:
            # Document構築
            doc_data = data.get("document", {})
            
            # 必須フィールドチェック
            if not doc_data.get("content"):
                return {"success": False, "error": "content is required"}
            
            document = Document(
                id=doc_data.get("id", str(int(time.time() * 1000))),
                content=doc_data.get("content", ""),
                source=doc_data.get("source", ""),
                title=doc_data.get("title", ""),
                category=doc_data.get("category", ""),
                tags=doc_data.get("tags", []),
                author=doc_data.get("author", ""),
                relevance_boost=doc_data.get("relevance_boost", 1.0)
            )
            
            # インデックス実行
            result = await self._index_document(document)
            
            return {
                "success": result.success,
                "data": {
                    "document_id": result.document_id,
                    "index_time_ms": result.index_time_ms
                },
                "error": result.error_message
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _batch_index_documents_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """バッチドキュメントインデックスアクション"""
        try:
            documents = []
            for doc_data in data.get("documents", []):
                documents.append(Document(
                    id=doc_data.get("id", str(int(time.time() * 1000))),
                    content=doc_data.get("content", ""),
                    source=doc_data.get("source", ""),
                    title=doc_data.get("title", ""),
                    category=doc_data.get("category", ""),
                    tags=doc_data.get("tags", []),
                    author=doc_data.get("author", ""),
                    relevance_boost=doc_data.get("relevance_boost", 1.0)
                ))
            
            # バッチインデックス実行
            successful_count = 0
            failed_documents = []
            
            for document in documents:
                result = await self._index_document(document)
                if result.success:
                    successful_count += 1
                else:
                    failed_documents.append({
                        "document_id": document.id,
                        "error": result.error_message
                    })
            
            return {
                "success": True,
                "data": {
                    "total_documents": len(documents),
                    "successful_count": successful_count,
                    "failed_count": len(failed_documents),
                    "failed_documents": failed_documents
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_similar_documents_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """類似ドキュメント取得アクション"""
        try:
            document_id = data.get("document_id", "")
            limit = data.get("limit", 5)
            
            # 元ドキュメント取得
            conn = sqlite3connect(str(self.db_path))
            try:
                cursor = conn.execute(
                    "SELECT content, category, tags FROM documents WHERE id = ?",
                    [document_id]
                )
                row = cursor.fetchone()
                
                if not row:
                    return {"success": False, "error": "Document not found"}
                
                content, category, tags = row
                
                # 類似検索（簡易実装）
                query = SearchQuery(
                    query=content[:100],  # 最初の100文字で検索
                    search_type=SearchType.FULL_TEXT,
                    filters={"category": category} if category else {},
                    limit=limit + 1  # 自分自身を除外するため+1
                )
                
                results = await self._search(query)
                
                # 自分自身を除外
                similar_results = [r for r in results if r.document.id != document_id][:limit]
                
                return {
                    "success": True,
                    "data": {
                        "similar_documents": [
                            {
                                "document_id": r.document.id,
                                "title": r.document.title,
                                "source": r.document.source,
                                "similarity_score": r.score
                            }
                            for r in similar_results
                        ]
                    }
                }
                
            finally:
                conn.close()
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _analyze_query_intent_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """クエリ意図分析アクション"""
        try:
            query = data.get("query", "")
            
            # 簡易的な意図分析
            intent = {
                "query": query,
                "intent_type": "unknown",
                "entities": [],
                "keywords": [],
                "suggested_filters": {}
            }
            
            # 意図タイプ判定
            query_lower = query.lower()
            if any(word in query_lower for word in ["how to", "どうやって", "方法", "手順"]):
                intent["intent_type"] = "how_to"
            elif any(word in query_lower for word in ["what is", "とは", "定義", "意味"]):
                intent["intent_type"] = "definition"
            elif any(word in query_lower for word in ["why", "なぜ", "理由", "原因"]):
                intent["intent_type"] = "explanation"
            elif any(word in query_lower for word in ["list", "一覧", "すべて", "全部"]):
                intent["intent_type"] = "enumeration"
            else:
                intent["intent_type"] = "general"
            
            # キーワード抽出（簡易実装）
            words = query.split()
            keywords = [w for w in words if len(w) > 2 and w not in self.stop_words]
            intent["keywords"] = keywords[:5]  # 上位5キーワード
            
            # フィルター提案
            if "エラー" in query_lower or "error" in query_lower:
                intent["suggested_filters"]["category"] = "error"
            elif "設定" in query_lower or "config" in query_lower:
                intent["suggested_filters"]["category"] = "configuration"
            
            return {
                "success": True,
                "data": intent
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _generate_insights_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """洞察生成アクション"""
        try:
            search_results = data.get("search_results", [])
            query = data.get("query", "")
            
            # 簡易的な洞察生成
            insights = {
                "query": query,
                "total_results": len(search_results),
                "key_themes": [],
                "summary": "",
                "recommendations": []
            }
            
            if not search_results:
                insights["summary"] = "検索結果が見つかりませんでした。"
                insights["recommendations"] = ["検索クエリを変更してみてください"]
            else:
                # カテゴリ分析
                categories = {}
                for result in search_results:
                    category = result.get("category", "unknown")
                    categories[category] = categories.get(category, 0) + 1
                
                # 主要テーマ
                insights["key_themes"] = [
                    {"theme": cat, "count": count}
                    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
                ]
                
                # サマリー生成
                insights["summary"] = f"{len(search_results)}件の結果が見つかりました。"
                if insights["key_themes"]:
                    main_theme = insights["key_themes"][0]["theme"]
                    insights["summary"] += f" 主なカテゴリは「{main_theme}」です。"
                
                # 推奨事項
                if len(search_results) > 10:
                    insights["recommendations"].append("結果が多いため、フィルターで絞り込むことをお勧めします")
                if len(set(r.get("source", "") for r in search_results)) > 5:
                    insights["recommendations"].append("複数のソースから情報が見つかりました")
            
            return {
                "success": True,
                "data": insights
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _optimize_index_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """インデックス最適化アクション"""
        try:
            start_time = time.time()
            
            conn = sqlite3connect(str(self.db_path))
            try:
                # VACUUM実行
                conn.execute("VACUUM")
                
                # 統計情報更新
                conn.execute("ANALYZE")
                
                # 古い検索履歴削除（30日以上）
                thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
                conn.execute(
                    "DELETE FROM search_history WHERE created_at < ?",
                    [thirty_days_ago]
                )
                
                conn.commit()
                
                optimization_time_ms = (time.time() - start_time) * 1000
                
                return {
                    "success": True,
                    "data": {
                        "optimization_time_ms": optimization_time_ms,
                        "message": "インデックスの最適化が完了しました"
                    }
                }
                
            finally:
                conn.close()
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_search_statistics_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """検索統計取得アクション"""
        try:
            conn = sqlite3connect(str(self.db_path))
            try:
                # 総検索数
                cursor = conn.execute("SELECT COUNT(*) FROM search_history")
                total_searches = cursor.fetchone()[0]
                
                # 人気検索クエリ（上位10件）
                cursor = conn.execute("""
                    SELECT query, COUNT(*) as count 
                    FROM search_history 
                    GROUP BY query 
                    ORDER BY count DESC 
                    LIMIT 10
                """)
                popular_queries = [
                    {"query": row[0], "count": row[1]}
                    for row in cursor.fetchall()
                ]
                
                # 平均検索時間
                cursor = conn.execute("SELECT AVG(search_time_ms) FROM search_history")
                avg_search_time = cursor.fetchone()[0] or 0
                
                # 検索タイプ分布
                cursor = conn.execute("""
                    SELECT search_type, COUNT(*) as count 
                    FROM search_history 
                    WHERE search_type IS NOT NULL
                    GROUP BY search_type
                """)
                search_type_distribution = {
                    row[0]: row[1] for row in cursor.fetchall()
                }
                
                return {
                    "success": True,
                    "data": {
                        "total_searches": total_searches,
                        "popular_queries": popular_queries,
                        "average_search_time_ms": avg_search_time,
                        "search_type_distribution": search_type_distribution
                    }
                }
                
            finally:
                conn.close()
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_index_info_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """インデックス情報取得アクション"""
        try:
            conn = sqlite3connect(str(self.db_path))
            try:
                # ドキュメント数
                cursor = conn.execute("SELECT COUNT(*) FROM documents")
                document_count = cursor.fetchone()[0]
                
                # カテゴリ分布
                cursor = conn.execute("""
                    SELECT category, COUNT(*) as count 
                    FROM documents 
                    WHERE category IS NOT NULL
                    GROUP BY category
                """)
                category_distribution = {
                    row[0]: row[1] for row in cursor.fetchall()
                }
                
                # ソース分布
                cursor = conn.execute("""
                    SELECT source, COUNT(*) as count 
                    FROM documents 
                    GROUP BY source
                    ORDER BY count DESC
                    LIMIT 10
                """)
                source_distribution = [
                    {"source": row[0], "count": row[1]}
                    for row in cursor.fetchall()
                ]
                
                # データベースサイズ
                db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
                
                return {
                    "success": True,
                    "data": {
                        "index_name": "rag_sage_index",
                        "document_count": document_count,
                        "size_bytes": db_size,
                        "category_distribution": category_distribution,
                        "source_distribution": source_distribution
                    }
                }
                
            finally:
                conn.close()
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _delete_document_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """ドキュメント削除アクション"""
        try:
            document_id = data.get("document_id", "")
            
            conn = sqlite3connect(str(self.db_path))
            try:
                # 削除実行
                cursor = conn.execute(
                    "DELETE FROM documents WHERE id = ?",
                    [document_id]
                )
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    # キャッシュクリア
                    self.cache.clear()
                    
                    return {
                        "success": True,
                        "data": {
                            "document_id": document_id,
                            "deleted": True
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": "Document not found"
                    }
                    
            finally:
                conn.close()
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _update_document_boost_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """ドキュメントブースト更新アクション"""
        try:
            document_id = data.get("document_id", "")
            boost_value = data.get("boost_value", 1.0)
            
            # ブースト値の範囲チェック
            boost_value = max(0.1, min(10.0, boost_value))
            
            conn = sqlite3connect(str(self.db_path))
            try:
                cursor = conn.execute(
                    "UPDATE documents SET relevance_boost = ? WHERE id = ?",
                    [boost_value, document_id]
                )
                
                updated_count = cursor.rowcount
                conn.commit()
                
                if updated_count > 0:
                    # キャッシュクリア
                    self.cache.clear()
                    
                    return {
                        "success": True,
                        "data": {
                            "document_id": document_id,
                            "boost_value": boost_value,
                            "updated": True
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": "Document not found"
                    }
                    
            finally:
                conn.close()
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _health_check_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """ヘルスチェックアクション"""
        try:
            health_status = {
                "status": "healthy",
                "agent_name": "RAG Processor",
                "cache_size": len(self.cache),
                "db_accessible": False,
                "search_functional": False
            }
            
            # データベース接続チェック
            try:
                conn = sqlite3connect(str(self.db_path))
                cursor = conn.execute("SELECT COUNT(*) FROM documents")
                document_count = cursor.fetchone()[0]
                conn.close()
                health_status["db_accessible"] = True
                health_status["document_count"] = document_count
            except:
                health_status["status"] = "unhealthy"
            
            # 検索機能チェック
            try:
                test_query = SearchQuery(query="test", limit=1)
                results = await self._search(test_query)
                health_status["search_functional"] = True
            except:
                health_status["status"] = "unhealthy"
            
            return {
                "success": True,
                "data": health_status
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # === Core Search Functions ===
    
    async def _search(self, query: SearchQuery) -> List[SearchResult]start_time = time.time()
    """検索実行"""
        
        # キャッシュチェック
        cache_key = self._generate_cache_key(query)
        cached_result = self._get_cached_result(cache_key):
        if cached_result:
            logger.info(f"Cache hit for query: {query.query[:50]}")
            return cached_result
        
        # 検索タイプに応じた検索実行
        if query.search_type == SearchType.FULL_TEXT:
            results = await self._full_text_search(query)
        elif query.search_type == SearchType.SEMANTIC:
            results = await self._semantic_search(query)
        elif query.search_type == SearchType.HYBRID:
            results = await self._hybrid_search(query)
        else:
            results = await self._exact_search(query)
        
        # キャッシュ保存
        self._cache_result(cache_key, results)
        
        # 検索履歴保存
        search_time_ms = (time.time() - start_time) * 1000
        await self._save_search_history(query, len(results), search_time_ms)
        
        return results
    
    async def _full_text_search(self, query: SearchQuery) -> List[SearchResult]conn = sqlite3connect(str(self.db_path))
    """全文検索""":
        try:
            # SQLクエリ構築
            where_conditions = ["(content LIKE ? OR title LIKE ?)"]
            params = [f"%{query.query}%", f"%{query.query}%"]
            
            # フィルター適用
            if query.filters:
                if "category" in query.filters:
                    where_conditions.append("category = ?")
                    params.append(query.filters["category"])
                
                if "source" in query.filters:
                    where_conditions.append("source LIKE ?")
                    params.append(f"%{query.filters['source']}%")
                
                if "tags" in query.filters:
                    # タグのいずれかを含む
                    tag_conditions = []
                    for tag in query.filters["tags"]:
                        tag_conditions.append("tags LIKE ?")
                        params.append(f"%{tag}%")
                    if tag_conditions:
                        where_conditions.append(f"({' OR '.join(tag_conditions)})")
            
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
                document = self._row_to_document(row)
                score = self._calculate_relevance_score(document, query)
                highlights = self._generate_highlights(document.content, query.query)
                
                results.append(SearchResult(
                    document=document,
                    score=score,
                    highlights=highlights,
                    matched_fields=["content", "title"]
                ))
            
            # スコアでソート
            results.sort(key=lambda x: x.score, reverse=True)
            
            # アクセス数更新
            for result in results:
                await self._increment_access_count(result.document.id)
            
            return results
            
        finally:
            conn.close()
    
    async def _semantic_search(self, query: SearchQuery) -> List[SearchResult]:
        """セマンティック検索（簡易実装）"""
        # 現時点では全文検索にフォールバック
        logger.info("Semantic search fallback to full-text search")
        return await self._full_text_search(query)
    
    async def _hybrid_search(self, query: SearchQuery) -> List[SearchResult]:
        """ハイブリッド検索"""
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
    
    async def _exact_search(self, query: SearchQuery) -> List[SearchResult]conn = sqlite3connect(str(self.db_path))
    """完全一致検索""":
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
                document = self._row_to_document(row)
                results.append(SearchResult(
                    document=document,
                    score=1.0,  # 完全一致
                    highlights=[query.query],
                    matched_fields=["content"] if document.content == query.query else ["title"]
                ))
            
            return results
            
        finally:
            conn.close()
    
    # === Document Management ===
    
    async def _index_document(self, document: Document) -> IndexResultstart_time = time.time()
    """ドキュメントインデックス"""
        :
        try:
            conn = sqlite3connect(str(self.db_path))
            try:
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
                    document.title,
                    document.category,
                    json.dumps(document.tags),
                    document.author,
                    document.created_at.isoformat(),
                    document.updated_at.isoformat(),
                    datetime.now().isoformat(),
                    document.access_count,
                    document.relevance_boost
                ]
                
                conn.execute(sql, params)
                conn.commit()
                
                # キャッシュクリア
                self.cache.clear()
                
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
    
    # === Helper Functions ===
    
    def _generate_cache_key(self, query: SearchQuery) -> str:
        """キャッシュキー生成"""
        key_data = {
            "query": query.query,
            "search_type": query.search_type.value,
            "filters": query.filters,
            "limit": query.limit,
            "offset": query.offset
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[List[SearchResult]]:
        """キャッシュから結果取得"""
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if not entry.is_expired:
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                return entry.value
            else:
                del self.cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, results: List[SearchResult]) -> Noneexpires_at = datetime.now() + timedelta(seconds=self.cache_ttl_seconds)
    """結果をキャッシュ"""
        self.cache[cache_key] = CacheEntry(
            key=cache_key,
            value=results,
            expires_at=expires_at
        )
        
        # キャッシュサイズ制限:
        if len(self.cache) > 1000:
            # 最も古いエントリを削除
            oldest_key = min(self.cache.keys(),
                           key=lambda k: self.cache[k].last_accessed)
            del self.cache[oldest_key]
    
    def _calculate_relevance_score(self, document: Document, query: SearchQuery) -> float:
        """関連性スコア計算"""
        score = 0.0
        query_lower = query.query.lower()
        
        # コンテンツマッチ
        content_lower = document.content.lower()
        content_matches = content_lower.count(query_lower)
        content_score = min(content_matches / 10.0, 1.0)
        score += content_score * self.scoring_weights["content_match"]
        
        # タイトルマッチ
        title_lower = document.title.lower()
        if query_lower in title_lower:
            score += self.scoring_weights["title_match"]
        
        # タグマッチ
        for tag in document.tags:
            if query_lower in tag.lower():
                score += self.scoring_weights["tag_match"] / len(document.tags)
        
        # 新しさ
        days_old = (datetime.now() - document.created_at).days
        freshness_score = max(0, 1 - (days_old / 365.0))
        score += freshness_score * self.scoring_weights["freshness"]
        
        # ブーストファクター適用
        score *= document.relevance_boost
        
        return min(score, 1.0)
    
    def _generate_highlights(self, content: str, query: str, max_highlights: int = 3) -> List[str]:
        """ハイライト生成"""
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
    
    def _row_to_document(self, row: Tuple) -> Document:
        """データベース行をDocumentに変換"""
        return Document(
            id=row[0],
            content=row[1],
            source=row[2],
            title=row[3] or "",
            category=row[4] or "",
            tags=json.loads(row[5]) if row[5] else [],
            author=row[6] or "",
            created_at=datetime.fromisoformat(row[7]) if row[7] else datetime.now(),
            updated_at=datetime.fromisoformat(row[8]) if row[8] else datetime.now(),
            indexed_at=datetime.fromisoformat(row[9]) if row[9] else None,
            access_count=row[10] or 0,
            relevance_boost=row[11] or 1.0
        )
    
    async def _increment_access_count(self, document_id: str) -> Noneconn = sqlite3connect(str(self.db_path))
    """アクセス数増加""":
        try:
            conn.execute(
                "UPDATE documents SET access_count = access_count + 1 WHERE id = ?",
                [document_id]
            )
            conn.commit()
        finally:
            conn.close()
    
    async def _save_search_history(self, query: SearchQuery, result_count: int, search_time_ms: float) -> Noneconn = sqlite3connect(str(self.db_path))
    """検索履歴保存""":
        try:
            conn.execute("""
                INSERT INTO search_history
                (query, search_type, filters, result_count, search_time_ms)
                VALUES (?, ?, ?, ?, ?)
            """, [
                query.query,
                query.search_type.value,
                json.dumps(query.filters),
                result_count,
                search_time_ms
            ])
            conn.commit()
        finally:
            conn.close()