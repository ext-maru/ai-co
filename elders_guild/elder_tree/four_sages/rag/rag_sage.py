"""
RAG賢者 (RAG Sage)
情報検索、コンテキスト理解、知識統合機能を提供
"""

import hashlib
import json
import math
import os
import re
import sqlite3
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..base_sage import BaseSage


class RAGSage(BaseSage):
    """RAG賢者 - 情報検索と知識統合"""

    def __init__(self, data_path: str = "data/rag"):
        """初期化メソッド"""
        super().__init__("RAG")

        self.data_path = data_path
        self.db_path = os.path.join(data_path, "rag.db")

        # データベース初期化
        self._init_database()

        # ストップワード（簡易版）
        self.stop_words = {
            "の",
            "で",
            "に",
            "を",
            "は",
            "が",
            "と",
            "し",
            "て",
            "です",
            "である",
            "a",
            "an",
            "and",
            "are",
            "as",
            "at",
            "be",
            "by",
            "for",
            "from",
            "has",
            "he",
            "in",
            "is",
            "it",
            "its",
            "of",
            "on",
            "that",
            "the",
            "to",
            "was",
            "will",
            "with",
            "the",
            "this",
            "but",
            "they",
            "have",
            "had",
            "what",
            "said",
            "each",
            "which",
            "their",
            "time",
            "if",
            "up",
            "out",
            "many",
        }

        # 文書タイプ
        self.document_types = [
            "documentation",
            "code",
            "configuration",
            "log",
            "specification",
            "tutorial",
            "faq",
            "troubleshooting",
        ]

        self.logger.info("RAG Sage ready for information retrieval")

    def _init_database(self):
        """RAGデータベースの初期化"""
        os.makedirs(self.data_path, exist_ok=True)

        with sqlite3connect(self.db_path) as conn:
            # 文書テーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    document_type TEXT NOT NULL DEFAULT 'documentation',
                    source TEXT,
                    language TEXT DEFAULT 'ja',
                    content_hash TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    relevance_score REAL DEFAULT 0.0,
                    tags TEXT,
                    metadata TEXT
                )
            """
            )

            # チャンクテーブル（文書を小さなセクションに分割）
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    content_length INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(id)
                )
            """
            )

            # キーワードテーブル（TF-IDF用）
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    chunk_id TEXT,
                    tf_score REAL NOT NULL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(id),
                    FOREIGN KEY (chunk_id) REFERENCES chunks(id)
                )
            """
            )

            # 検索クエリテーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS search_queries (
                    id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    query_hash TEXT NOT NULL,
                    results_count INTEGER DEFAULT 0,
                    execution_time_ms REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """
            )

            # 検索結果テーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS search_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    chunk_id TEXT,
                    relevance_score REAL NOT NULL,
                    rank_position INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (query_id) REFERENCES search_queries(id),
                    FOREIGN KEY (document_id) REFERENCES documents(id),
                    FOREIGN KEY (chunk_id) REFERENCES chunks(id)
                )
            """
            )

            # コンテキストテーブル（関連文書の管理）
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS contexts (
                    id TEXT PRIMARY KEY,
                    context_name TEXT NOT NULL,
                    description TEXT,
                    document_ids TEXT NOT NULL,
                    context_type TEXT DEFAULT 'general',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """
            )

            # インデックス作成
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(content_hash)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_keywords_document ON keywords(document_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_search_hash ON search_queries(query_hash)"
            )
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_keyword_document_unique ON " \
                    "keywords(keyword, document_id, chunk_id)"
            )

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """RAG賢者のリクエスト処理"""
        start_time = datetime.now()

        try:
            request_type = request.get("type", "unknown")

            if request_type == "add_document":
                result = await self._add_document(request)
            elif request_type == "search":
                result = await self._search(request)
            elif request_type == "get_document":
                result = await self._get_document(request)
            elif request_type == "list_documents":
                result = await self._list_documents(request)
            elif request_type == "update_document":
                result = await self._update_document(request)
            elif request_type == "delete_document":
                result = await self._delete_document(request)
            elif request_type == "create_context":
                result = await self._create_context(request)
            elif request_type == "search_in_context":
                result = await self._search_in_context(request)
            elif request_type == "get_recommendations":
                result = await self._get_recommendations(request)
            elif request_type == "get_analytics":
                result = await self._get_analytics(request)
            elif request_type == "reindex_documents":
                result = await self._reindex_documents(request)
            else:
                result = {
                    "success": False,
                    "error": f"Unknown request type: {request_type}",
                    "supported_types": [
                        "add_document",
                        "search",
                        "get_document",
                        "list_documents",
                        "update_document",
                        "delete_document",
                        "create_context",
                        "search_in_context",
                        "get_recommendations",
                        "get_analytics",
                        "reindex_documents",
                    ],
                }

            # 処理時間を計算
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            result["processing_time_ms"] = processing_time

            await self.log_request(request, result)
            return result

        except Exception as e:
            await self.log_error(e, {"request": request})
            return {"success": False, "error": str(e), "sage": self.sage_name}

    async def _add_document(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """文書追加"""
        title = request.get("title", "")
        content = request.get("content", "")
        document_type = request.get("document_type", "documentation")
        source = request.get("source", "")
        language = request.get("language", "ja")
        tags = request.get("tags", [])
        metadata = request.get("metadata", {})

        if not title or not content:
            return {"success": False, "error": "Title and content are required"}

        # コンテンツハッシュで重複チェック
        content_hash = hashlib.md5(f"{title}{content}".encode()).hexdigest()
        document_id = str(uuid.uuid4())

        with sqlite3connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 重複チェック
            cursor.execute(
                "SELECT id FROM documents WHERE content_hash = ?", (content_hash,)
            )
            if cursor.fetchone():
                return {
                    "success": False,
                    "error": "Document with identical content already exists",
                    "content_hash": content_hash,
                }

            # 文書追加
            cursor.execute(
                """
                INSERT INTO documents
                (id, title, content, document_type, source, language, content_hash, tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    document_id,
                    title,
                    content,
                    document_type,
                    source,
                    language,
                    content_hash,
                    json.dumps(tags),
                    json.dumps(metadata),
                ),
            )

        # チャンキングとインデックシング
        await self._chunk_and_index_document(document_id, title, content)

        return {
            "success": True,
            "document_id": document_id,
            "content_hash": content_hash,
            "message": "Document added and indexed successfully",
        }

    async def _chunk_and_index_document(
        self, document_id: str, title: str, content: str
    ):
        """文書のチャンキングとインデックシング"""
        # コンテンツをチャンクに分割（簡易実装）
        chunk_size = 500  # 文字数
        chunks = []

        # タイトルもコンテンツに含める
        full_content = f"{title}\n\n{content}"

        for i in range(0, len(full_content), chunk_size):
            chunk_content = full_content[i : i + chunk_size]
            chunk_id = str(uuid.uuid4())
            chunks.append(
                {
                    "id": chunk_id,
                    "index": len(chunks),
                    "content": chunk_content,
                    "length": len(chunk_content),
                }
            )

        with sqlite3connect(self.db_path) as conn:
            cursor = conn.cursor()

            # チャンク保存
            for chunk in chunks:
                cursor.execute(
                    """
                    INSERT INTO chunks (id, document_id, chunk_index, content, content_length)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        chunk["id"],
                        document_id,
                        chunk["index"],
                        chunk["content"],
                        chunk["length"],
                    ),
                )

            # キーワードインデックシング
            all_keywords = self._extract_keywords(full_content)
            document_keyword_count = defaultdict(int)

            # 文書全体のキーワード频度計算
            for keyword in all_keywords:
                document_keyword_count[keyword] += 1

            # キーワード保存（文書レベル）
            for keyword, count in document_keyword_count.items():
                tf_score = count / len(all_keywords) if all_keywords else 0

                cursor.execute(
                    """
                    INSERT OR IGNORE INTO keywords (keyword, document_id, tf_score)
                    VALUES (?, ?, ?)
                """,
                    (keyword, document_id, tf_score),
                )

            # チャンクレベルのキーワード保存
            for chunk in chunks:
                chunk_keywords = self._extract_keywords(chunk["content"])
                chunk_keyword_count = defaultdict(int)

                for keyword in chunk_keywords:
                    chunk_keyword_count[keyword] += 1

                for keyword, count in chunk_keyword_count.items():
                    tf_score = count / len(chunk_keywords) if chunk_keywords else 0

                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO keywords (keyword, document_id, chunk_id, tf_score)
                        VALUES (?, ?, ?, ?)
                    """,
                        (keyword, document_id, chunk["id"], tf_score),
                    )

    def _extract_keywords(self, text: str) -> List[str]:
        """テキストからキーワードを抜き出し"""
        # 簡易トークナイザー
        # 英数字、ひらがな、カタカナ、漢字を分割
        tokens = re.findall(r"[\w぀-ゟ゠-ヿ一-龯]+", text.lower())

        # ストップワード除去と長さフィルタリング
        keywords = []
        for token in tokens:
            if token not in self.stop_words and len(token) >= 2 and not token.isdigit():
                keywords.append(token)

        return keywords

    async def _search(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """文書検索"""
        query = request.get("query", "")
        document_type = request.get("document_type")
        language = request.get("language")
        limit = request.get("limit", 10)
        min_score = request.get("min_score", 0.1)

        if not query:
            return {"success": False, "error": "Search query is required"}

        start_time = datetime.now()
        query_id = str(uuid.uuid4())
        query_hash = hashlib.md5(query.encode()).hexdigest()

        # クエリキーワード抽出
        query_keywords = self._extract_keywords(query)

        if not query_keywords:
            return {"success": False, "error": "No valid keywords found in query"}

        with sqlite3connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 基本検索クエリ構築
            where_conditions = []
            params = []

            if document_type:
                where_conditions.append("d.document_type = ?")
                params.append(document_type)

            if language:
                where_conditions.append("d.language = ?")
                params.append(language)

            where_clause = (
                " AND " + " AND ".join(where_conditions) if where_conditions else ""
            )

            # TF-IDFベースの検索
            relevance_scores = await self._calculate_relevance_scores(
                query_keywords, document_type, language
            )

            # 結果をスコア順でソート
            sorted_results = sorted(
                relevance_scores.items(), key=lambda x: x[1], reverse=True
            )[:limit]

            # 最小スコアフィルタリング
            filtered_results = [
                (doc_id, score)
                for doc_id, score in sorted_results
                if score >= min_score
            ]

            # 文書詳細取得
            results = []
            for rank, (document_id, score) in enumerate(filtered_results):
                cursor.execute(
                    """
                    SELECT id, title, content, document_type, source, created_at, tags
                    FROM documents WHERE id = ?
                """,
                    (document_id,),
                )

                doc_row = cursor.fetchone()
                if doc_row:
                    # アクセス回数更新
                    cursor.execute(
                        "UPDATE documents SET access_count = access_count + 1 WHERE id = ?",
                        (document_id,),
                    )

                    # 関連チャンク取得
                    cursor.execute(
                        """
                        SELECT c.id, c.content FROM chunks c
                        JOIN keywords k ON c.id = k.chunk_id
                        WHERE c.document_id = ? AND k.keyword IN ({})
                        GROUP BY c.id
                        ORDER BY SUM(k.tf_score) DESC
                        LIMIT 3
                    """.format(
                            ",".join(["?"] * len(query_keywords))
                        ),
                        [document_id] + query_keywords,
                    )

                    relevant_chunks = [
                        {
                            "id": row[0],
                            "content": (
                                row[1][:200] + "..." if len(row[1]) > 200 else row[1]
                            ),
                        }
                        for row in cursor.fetchall()
                    ]

                    results.append(
                        {
                            "document_id": doc_row[0],
                            "title": doc_row[1],
                            "content_preview": (
                                doc_row[2][:300] + "..."
                                if len(doc_row[2]) > 300
                                else doc_row[2]
                            ),
                            "document_type": doc_row[3],
                            "source": doc_row[4],
                            "created_at": doc_row[5],
                            "tags": json.loads(doc_row[6]) if doc_row[6] else [],
                            "relevance_score": round(score, 4),
                            "rank": rank + 1,
                            "relevant_chunks": relevant_chunks,
                        }
                    )

            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            # 検索クエリ記録
            cursor.execute(
                """
                INSERT INTO search_queries (id, query, query_hash, results_count, execution_time_ms, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    query_id,
                    query,
                    query_hash,
                    len(results),
                    execution_time,
                    json.dumps(
                        {
                            "keywords": query_keywords,
                            "filters": {
                                "document_type": document_type,
                                "language": language,
                            },
                        }
                    ),
                ),
            )

            # 検索結果記録
            for result in results:
                cursor.execute(
                    """
                    INSERT INTO search_results (query_id, document_id, relevance_score, rank_position)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        query_id,
                        result["document_id"],
                        result["relevance_score"],
                        result["rank"],
                    ),
                )

        return {
            "success": True,
            "query": query,
            "query_id": query_id,
            "results": results,
            "total_results": len(results),
            "execution_time_ms": execution_time,
            "keywords_used": query_keywords,
        }

    async def _calculate_relevance_scores(
        self,
        query_keywords: List[str],
        document_type: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Dict[str, float]:
        """TF-IDFベースの関連度スコア計算"""
        with sqlite3connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 総文書数取得
            where_conditions = []
            params = []

            if document_type:
                where_conditions.append("document_type = ?")
                params.append(document_type)

            if language:
                where_conditions.append("language = ?")
                params.append(language)

            where_clause = (
                " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            )

            cursor.execute(f"SELECT COUNT(*) FROM documents{where_clause}", params)
            total_documents = cursor.fetchone()[0]

            if total_documents == 0:
                return {}

            document_scores = defaultdict(float)

            # 各キーワードにTF-IDF計算
            for keyword in query_keywords:
                # キーワードを含む文書数を取得（DF）
                keyword_params = [keyword] + params
                cursor.execute(
                    f"""
                    SELECT COUNT(DISTINCT k.document_id)
                    FROM keywords k
                    JOIN documents d ON k.document_id = d.id
                    WHERE k.keyword = ?{where_clause.replace(
                        'WHERE',
                        ' AND'
                    ) if where_clause else ''}
                """,
                    keyword_params,
                )

                document_frequency = cursor.fetchone()[0]

                if document_frequency == 0:
                    continue

                # IDF計算
                idf = math.log(total_documents / document_frequency)

                # 各文書のTFスコア取得
                cursor.execute(
                    f"""
                    SELECT k.document_id, k.tf_score
                    FROM keywords k
                    JOIN documents d ON k.document_id = d.id
                    WHERE k.keyword = ? AND k.chunk_id IS NULL{where_clause.replace(
                        'WHERE',
                        ' AND'
                    ) if where_clause else ''}
                """,
                    keyword_params,
                )

                for document_id, tf_score in cursor.fetchall():
                    # TF-IDFスコア計算
                    tfidf_score = tf_score * idf
                    document_scores[document_id] += tfidf_score

            return dict(document_scores)

    async def _get_document(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """文書詳細取得"""
        document_id = request.get("document_id")

        if not document_id:
            return {"success": False, "error": "Document ID is required"}

        with sqlite3connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 文書詳細取得
            cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
            doc_row = cursor.fetchone()

            if not doc_row:
                return {"success": False, "error": "Document not found"}

            # カラム名取得
            columns = [description[0] for description in cursor.description]
            document = dict(zip(columns, doc_row))

            # JSONフィールドをパース
            if document.get("tags"):
                document["tags"] = json.loads(document["tags"])
            if document.get("metadata"):
                document["metadata"] = json.loads(document["metadata"])

            # チャンク取得
            cursor.execute(
                """
                SELECT id, chunk_index, content, content_length
                FROM chunks
                WHERE document_id = ?
                ORDER BY chunk_index
            """,
                (document_id,),
            )

            chunks = [
                {"id": row[0], "index": row[1], "content": row[2], "length": row[3]}
                for row in cursor.fetchall()
            ]

            # キーワード取得
            cursor.execute(
                """
                SELECT keyword, tf_score
                FROM keywords
                WHERE document_id = ? AND chunk_id IS NULL
                ORDER BY tf_score DESC
                LIMIT 20
            """,
                (document_id,),
            )

            keywords = [
                {"keyword": row[0], "tf_score": round(row[1], 4)}
                for row in cursor.fetchall()
            ]

            document["chunks"] = chunks
            document["keywords"] = keywords

        return {"success": True, "document": document}

    async def _list_documents(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """文書一覧取得"""
        filters = request.get("filters", {})
        sort_by = request.get("sort_by", "created_at")
        sort_order = request.get("sort_order", "DESC")
        limit = request.get("limit", 50)
        offset = request.get("offset", 0)

        with sqlite3connect(self.db_path) as conn:
            cursor = conn.cursor()

            # WHERE句構築
            where_conditions = []
            params = []

            for field, value in filters.items():
                if field in ["document_type", "language", "source"]:
                    where_conditions.append(f"{field} = ?")
                    params.append(value)
                elif field == "date_range":
                    if "start" in value:
                        where_conditions.append("created_at >= ?")
                        params.append(value["start"])
                    if "end" in value:
                        where_conditions.append("created_at <= ?")
                        params.append(value["end"])

            where_clause = (
                " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            )

            # クエリ実行
            query = f"""
                SELECT id, title, document_type, source, language, created_at, access_count, tags
                FROM documents
                {where_clause}
                ORDER BY {sort_by} {sort_order}
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])

            cursor.execute(query, params)
            doc_rows = cursor.fetchall()

            documents = []
            for row in doc_rows:
                doc = {
                    "id": row[0],
                    "title": row[1],
                    "document_type": row[2],
                    "source": row[3],
                    "language": row[4],
                    "created_at": row[5],
                    "access_count": row[6],
                    "tags": json.loads(row[7]) if row[7] else [],
                }
                documents.append(doc)

            # 総数取得
            count_query = f"SELECT COUNT(*) FROM documents{where_clause}"
            cursor.execute(count_query, params[:-2])  # limit, offsetを除く
            total_count = cursor.fetchone()[0]

        return {
            "success": True,
            "documents": documents,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
        }

    async def _update_document(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """文書更新"""
        document_id = request.get("document_id")
        updates = request.get("updates", {})

        if not document_id:
            return {"success": False, "error": "Document ID is required"}

        allowed_fields = [
            "title",
            "content",
            "document_type",
            "source",
            "language",
            "tags",
            "metadata",
        ]
        update_fields = []
        params = []
        reindex_needed = False

        for field, value in updates.items():
            if field in allowed_fields:
                update_fields.append(f"{field} = ?")

                if field in ["tags", "metadata"] and isinstance(value, (list, dict)):
                    params.append(json.dumps(value))
                else:
                    params.append(value)

                # コンテンツやタイトルが変更された場合は再インデックシングが必要
                if field in ["title", "content"]:
                    reindex_needed = True

        if not update_fields:
            return {"success": False, "error": "No valid fields to update"}

        params.append(datetime.now().isoformat())  # updated_at
        params.append(document_id)

        with sqlite3connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 文書存在確認
            cursor.execute(
                "SELECT title, content FROM documents WHERE id = ?", (document_id,)
            )
            existing_doc = cursor.fetchone()

            if not existing_doc:
                return {"success": False, "error": "Document not found"}

            # 文書更新
            cursor.execute(
                f"""
                UPDATE documents
                SET {', '.join(update_fields)}, updated_at = ?
                WHERE id = ?
            """,
                params,
            )

            # 再インデックシングが必要な場合
            if reindex_needed:
                # 既存のチャンクとキーワードを削除
                cursor.execute(
                    "DELETE FROM chunks WHERE document_id = ?", (document_id,)
                )
                cursor.execute(
                    "DELETE FROM keywords WHERE document_id = ?", (document_id,)
                )

                # 新しいコンテンツ取得
                cursor.execute(
                    "SELECT title, content FROM documents WHERE id = ?", (document_id,)
                )
                updated_doc = cursor.fetchone()

                if updated_doc:
                    # 再インデックシング実行
                    await self._chunk_and_index_document(
                        document_id, updated_doc[0], updated_doc[1]
                    )

        return {
            "success": True,
            "message": "Document updated successfully",
            "updated_fields": list(updates.keys()),
            "reindexed": reindex_needed,
        }

    async def _delete_document(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """文書削除"""
        document_id = request.get("document_id")

        if not document_id:
            return {"success": False, "error": "Document ID is required"}

        with sqlite3connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 文書存在確認
            cursor.execute("SELECT title FROM documents WHERE id = ?", (document_id,))
            document = cursor.fetchone()

            if not document:
                return {"success": False, "error": "Document not found"}

            # 関連データ削除
            cursor.execute("DELETE FROM keywords WHERE document_id = ?", (document_id,))
            cursor.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            cursor.execute(
                "DELETE FROM search_results WHERE document_id = ?", (document_id,)
            )
            cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))

        return {
            "success": True,
            "message": "Document deleted successfully",
            "deleted_document": document[0],
        }

    async def _create_context(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """コンテキスト作成"""
        context_name = request.get("context_name", "")
        description = request.get("description", "")
        document_ids = request.get("document_ids", [])
        context_type = request.get("context_type", "general")
        metadata = request.get("metadata", {})

        if not context_name or not document_ids:
            return {
                "success": False,
                "error": "Context name and document IDs are required",
            }

        context_id = str(uuid.uuid4())

        with sqlite3connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 指定された文書が存在するかチェック
            placeholders = ",".join(["?"] * len(document_ids))
            cursor.execute(
                f"""
                SELECT COUNT(*) FROM documents WHERE id IN ({placeholders})
            """,
                document_ids,
            )

            existing_count = cursor.fetchone()[0]
            if existing_count != len(document_ids):
                return {
                    "success": False,
                    "error": f"Some documents not found. Expected {len(document_ids)}, found {existing_count}",
                }

            # コンテキスト作成
            cursor.execute(
                """
                INSERT INTO contexts
                (id, context_name, description, document_ids, context_type, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    context_id,
                    context_name,
                    description,
                    json.dumps(document_ids),
                    context_type,
                    json.dumps(metadata),
                ),
            )

        return {
            "success": True,
            "context_id": context_id,
            "message": "Context created successfully",
            "document_count": len(document_ids),
        }

    async def _search_in_context(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """コンテキスト内検索"""
        context_id = request.get("context_id")
        query = request.get("query", "")
        limit = request.get("limit", 10)

        if not context_id or not query:
            return {"success": False, "error": "Context ID and query are required"}

        with sqlite3connect(self.db_path) as conn:
            cursor = conn.cursor()

            # コンテキスト取得
            cursor.execute(
                "SELECT document_ids FROM contexts WHERE id = ?", (context_id,)
            )
            context_row = cursor.fetchone()

            if not context_row:
                return {"success": False, "error": "Context not found"}

            document_ids = json.loads(context_row[0])

        # 通常の検索を実行し、結果をコンテキストでフィルタリング
        search_result = await self._search(
            {
                "query": query,
                "limit": limit * 2,
            }  # コンテキストフィルタリングを考慮して多めに取得
        )

        if not search_result.get("success"):
            return search_result

        # コンテキスト内の文書のみをフィルタリング
        context_results = []
        for result in search_result["results"]:
            if result["document_id"] in document_ids:
                context_results.append(result)
                if len(context_results) >= limit:
                    break

        return {
            "success": True,
            "context_id": context_id,
            "query": query,
            "results": context_results,
            "total_results": len(context_results),
            "context_document_count": len(document_ids),
        }

    async def _get_recommendations(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """関連文書推薦"""
        document_id = request.get("document_id")
        limit = request.get("limit", 5)

        if not document_id:
            return {"success": False, "error": "Document ID is required"}

        with sqlite3connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 対象文書のキーワード取得
            cursor.execute(
                """
                SELECT keyword, tf_score
                FROM keywords
                WHERE document_id = ? AND chunk_id IS NULL
                ORDER BY tf_score DESC
                LIMIT 10
            """,
                (document_id,),
            )

            keywords = cursor.fetchall()

            if not keywords:
                return {"success": False, "error": "No keywords found for document"}

            # 簡易推薦アルゴリズム：共通キーワードベース
            keyword_list = [k[0] for k in keywords[:5]]  # 上位5キーワードを使用

            placeholders = ",".join(["?"] * len(keyword_list))
            cursor.execute(
                f"""
                SELECT
                    k.document_id,
                    d.title,
                    d.document_type,
                    COUNT(*) as common_keywords,
                    AVG(k.tf_score) as avg_score
                FROM keywords k
                JOIN documents d ON k.document_id = d.id
                WHERE k.keyword IN ({placeholders})
                  AND k.document_id != ?
                  AND k.chunk_id IS NULL
                GROUP BY k.document_id, d.title, d.document_type
                HAVING common_keywords >= 2
                ORDER BY common_keywords DESC, avg_score DESC
                LIMIT ?
            """,
                keyword_list + [document_id, limit],
            )

            recommendations = []
            for row in cursor.fetchall():
                recommendations.append(
                    {
                        "document_id": row[0],
                        "title": row[1],
                        "document_type": row[2],
                        "common_keywords": row[3],
                        "average_score": round(row[4], 4),
                        "similarity_score": round(row[3] / len(keyword_list), 4),
                    }
                )

        return {
            "success": True,
            "source_document_id": document_id,
            "recommendations": recommendations,
            "total_recommendations": len(recommendations),
            "based_on_keywords": keyword_list,
        }

    async def _get_analytics(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """RAGシステム分析データ"""
        period_days = request.get("period_days", 30)

        start_date = (datetime.now() - timedelta(days=period_days)).isoformat()

        with sqlite3connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 文書統計
            cursor.execute(
                """
                SELECT
                    document_type,
                    COUNT(*) as count,
                    AVG(access_count) as avg_access
                FROM documents
                WHERE created_at >= ?
                GROUP BY document_type
                ORDER BY count DESC
            """,
                (start_date,),
            )

            document_stats = [
                {
                    "document_type": row[0],
                    "count": row[1],
                    "average_access": round(row[2], 2),
                }
                for row in cursor.fetchall()
            ]

            # 検索統計
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_searches,
                    AVG(results_count) as avg_results,
                    AVG(execution_time_ms) as avg_execution_time
                FROM search_queries
                WHERE created_at >= ?
            """,
                (start_date,),
            )

            search_stats = cursor.fetchone()

            # 人気文書
            cursor.execute(
                """
                SELECT title, access_count
                FROM documents
                WHERE created_at >= ?
                ORDER BY access_count DESC
                LIMIT 10
            """,
                (start_date,),
            )

            popular_documents = [
                {"title": row[0], "access_count": row[1]} for row in cursor.fetchall()
            ]

            # 人気キーワード
            cursor.execute(
                """
                SELECT
                    k.keyword,
                    COUNT(DISTINCT k.document_id) as document_count,
                    AVG(k.tf_score) as avg_score
                FROM keywords k
                JOIN documents d ON k.document_id = d.id
                WHERE d.created_at >= ? AND k.chunk_id IS NULL
                GROUP BY k.keyword
                HAVING document_count >= 2
                ORDER BY document_count DESC, avg_score DESC
                LIMIT 20
            """,
                (start_date,),
            )

            popular_keywords = [
                {
                    "keyword": row[0],
                    "document_count": row[1],
                    "average_score": round(row[2], 4),
                }
                for row in cursor.fetchall()
            ]

        analytics = {
            "period_days": period_days,
            "document_statistics": document_stats,
            "search_statistics": {
                "total_searches": search_stats[0] or 0,
                "average_results": round(search_stats[1] or 0, 2),
                "average_execution_time_ms": round(search_stats[2] or 0, 2),
            },
            "popular_documents": popular_documents,
            "popular_keywords": popular_keywords,
        }

        return {"success": True, "analytics": analytics}

    async def _reindex_documents(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """文書の再インデックシング"""
        document_ids = request.get("document_ids", [])

        with sqlite3connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 全文書または指定文書の再インデックシング
            if document_ids:
                placeholders = ",".join(["?"] * len(document_ids))
                cursor.execute(
                    f"""
                    SELECT id, title, content FROM documents WHERE id IN ({placeholders})
                """,
                    document_ids,
                )
            else:
                cursor.execute("SELECT id, title, content FROM documents")

            documents = cursor.fetchall()

            reindexed_count = 0

            for doc_id, title, content in documents:
                try:
                    # 既存インデックス削除
                    cursor.execute(
                        "DELETE FROM chunks WHERE document_id = ?", (doc_id,)
                    )
                    cursor.execute(
                        "DELETE FROM keywords WHERE document_id = ?", (doc_id,)
                    )

                    # 再インデックシング
                    await self._chunk_and_index_document(doc_id, title, content)
                    reindexed_count += 1

                except Exception as e:
                    self.logger.error(f"Failed to reindex document {doc_id}: {str(e)}")

        return {
            "success": True,
            "message": "Documents reindexed successfully",
            "reindexed_count": reindexed_count,
            "total_documents": len(documents),
        }

    def get_capabilities(self) -> List[str]:
        """RAG賢者の能力一覧"""
        return [
            "add_document",
            "search",
            "get_document",
            "list_documents",
            "update_document",
            "delete_document",
            "create_context",
            "search_in_context",
            "get_recommendations",
            "get_analytics",
            "reindex_documents",
            "information_retrieval",
            "document_management",
            "semantic_search",
            "context_management",
        ]
