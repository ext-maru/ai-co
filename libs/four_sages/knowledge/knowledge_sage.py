"""
ナレッジ賢者 (Knowledge Sage)
知識の蓄積、検索、学習機能を提供
"""

import os
import json
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib

from ..base_sage import BaseSage

class KnowledgeSage(BaseSage):
    """ナレッジ賢者 - 知識管理と学習"""
    
    def __init__(self, knowledge_base_path: str = "knowledge_base"):
        super().__init__("Knowledge")
        
        self.knowledge_base_path = knowledge_base_path
        self.db_path = os.path.join(knowledge_base_path, "knowledge.db")
        
        # データベース初期化
        self._init_database()
        
        # 知識カテゴリ
        self.categories = [
            "development",
            "architecture", 
            "best_practices",
            "troubleshooting",
            "documentation",
            "tools",
            "processes"
        ]
        
        self.logger.info("Knowledge Sage ready for learning")
    
    def _init_database(self):
        """知識ベースデータベースの初期化"""
        os.makedirs(self.knowledge_base_path, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    tags TEXT,
                    source TEXT,
                    hash TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS learning_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    outcome TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_category ON knowledge_entries(category);
                CREATE INDEX IF NOT EXISTS idx_tags ON knowledge_entries(tags);
                CREATE INDEX IF NOT EXISTS idx_hash ON knowledge_entries(hash);
            """)
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """ナレッジ賢者のリクエスト処理"""
        start_time = datetime.now()
        
        try:
            request_type = request.get("type", "unknown")
            
            if request_type == "store_knowledge":
                result = await self._store_knowledge(request)
            elif request_type == "search_knowledge":
                result = await self._search_knowledge(request)
            elif request_type == "learn_from_experience":
                result = await self._learn_from_experience(request)
            elif request_type == "get_recommendations":
                result = await self._get_recommendations(request)
            elif request_type == "update_knowledge":
                result = await self._update_knowledge(request)
            elif request_type == "get_categories":
                result = await self._get_categories()
            elif request_type == "get_insights":
                result = await self._get_insights(request)
            else:
                result = {
                    "success": False,
                    "error": f"Unknown request type: {request_type}",
                    "supported_types": [
                        "store_knowledge", "search_knowledge", "learn_from_experience",
                        "get_recommendations", "update_knowledge", "get_categories", "get_insights"
                    ]
                }
            
            # 処理時間を計算
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            result["processing_time_ms"] = processing_time
            
            await self.log_request(request, result)
            return result
            
        except Exception as e:
            await self.log_error(e, {"request": request})
            return {
                "success": False,
                "error": str(e),
                "sage": self.sage_name
            }
    
    async def _store_knowledge(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """知識の保存"""
        title = request.get("title", "")
        content = request.get("content", "")
        category = request.get("category", "general")
        tags = request.get("tags", [])
        source = request.get("source", "unknown")
        
        if not title or not content:
            return {
                "success": False,
                "error": "Title and content are required"
            }
        
        # 重複チェック用のハッシュ
        content_hash = hashlib.md5(f"{title}{content}".encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 重複チェック
            cursor.execute("SELECT id FROM knowledge_entries WHERE hash = ?", (content_hash,))
            if cursor.fetchone():
                return {
                    "success": False,
                    "error": "Knowledge already exists",
                    "hash": content_hash
                }
            
            # 新規保存
            cursor.execute("""
                INSERT INTO knowledge_entries 
                (title, content, category, tags, source, hash)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, content, category, json.dumps(tags), source, content_hash))
            
            knowledge_id = cursor.lastrowid
        
        return {
            "success": True,
            "knowledge_id": knowledge_id,
            "hash": content_hash,
            "message": "Knowledge stored successfully"
        }
    
    async def _search_knowledge(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """知識の検索"""
        query = request.get("query", "")
        category = request.get("category")
        tags = request.get("tags", [])
        limit = request.get("limit", 10)
        
        if not query:
            return {
                "success": False,
                "error": "Search query is required"
            }
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 基本検索クエリ
            sql = """
                SELECT id, title, content, category, tags, source, created_at, access_count
                FROM knowledge_entries 
                WHERE (title LIKE ? OR content LIKE ?)
            """
            params = [f"%{query}%", f"%{query}%"]
            
            # カテゴリフィルタ
            if category:
                sql += " AND category = ?"
                params.append(category)
            
            # タグフィルタ
            if tags:
                for tag in tags:
                    sql += " AND tags LIKE ?"
                    params.append(f"%{tag}%")
            
            sql += " ORDER BY access_count DESC, created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(sql, params)
            results = cursor.fetchall()
            
            # アクセス回数を更新
            if results:
                ids = [str(row[0]) for row in results]
                cursor.execute(f"""
                    UPDATE knowledge_entries 
                    SET access_count = access_count + 1 
                    WHERE id IN ({','.join(['?'] * len(ids))})
                """, ids)
        
        # 結果をフォーマット
        knowledge_entries = []
        for row in results:
            knowledge_entries.append({
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "category": row[3],
                "tags": json.loads(row[4]) if row[4] else [],
                "source": row[5],
                "created_at": row[6],
                "access_count": row[7]
            })
        
        return {
            "success": True,
            "query": query,
            "results": knowledge_entries,
            "count": len(knowledge_entries)
        }
    
    async def _learn_from_experience(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """経験からの学習"""
        session_type = request.get("session_type", "general")
        content = request.get("content", "")
        outcome = request.get("outcome", "")
        
        if not content:
            return {
                "success": False,
                "error": "Learning content is required"
            }
        
        # 学習セッションを記録
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO learning_sessions (session_type, content, outcome)
                VALUES (?, ?, ?)
            """, (session_type, content, outcome))
            
            session_id = cursor.lastrowid
        
        # 学習内容から知識を抽出して保存
        if outcome and "success" in outcome.lower():
            await self._store_knowledge({
                "title": f"Learning: {session_type}",
                "content": f"Experience: {content}\nOutcome: {outcome}",
                "category": "learning",
                "tags": ["experience", session_type],
                "source": "learning_session"
            })
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Learning session recorded"
        }
    
    async def _get_recommendations(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """知識に基づく推奨事項を提供"""
        context = request.get("context", "")
        category = request.get("category", "best_practices")
        
        # カテゴリに基づく推奨知識を検索
        search_result = await self._search_knowledge({
            "query": context,
            "category": category,
            "limit": 5
        })
        
        recommendations = []
        if search_result.get("success"):
            for entry in search_result["results"]:
                recommendations.append({
                    "title": entry["title"],
                    "summary": entry["content"][:200] + "...",
                    "confidence": min(entry["access_count"] * 10, 100),
                    "category": entry["category"]
                })
        
        return {
            "success": True,
            "context": context,
            "recommendations": recommendations,
            "count": len(recommendations)
        }
    
    async def _update_knowledge(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """既存知識の更新"""
        knowledge_id = request.get("id")
        updates = request.get("updates", {})
        
        if not knowledge_id:
            return {
                "success": False,
                "error": "Knowledge ID is required"
            }
        
        # 更新可能フィールド
        allowed_fields = ["title", "content", "category", "tags"]
        update_fields = []
        params = []
        
        for field, value in updates.items():
            if field in allowed_fields:
                update_fields.append(f"{field} = ?")
                if field == "tags":
                    params.append(json.dumps(value))
                else:
                    params.append(value)
        
        if not update_fields:
            return {
                "success": False,
                "error": "No valid fields to update"
            }
        
        params.append(knowledge_id)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE knowledge_entries 
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, params)
            
            if cursor.rowcount == 0:
                return {
                    "success": False,
                    "error": "Knowledge entry not found"
                }
        
        return {
            "success": True,
            "message": "Knowledge updated successfully",
            "updated_fields": list(updates.keys())
        }
    
    async def _get_categories(self) -> Dict[str, Any]:
        """利用可能な知識カテゴリを取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM knowledge_entries 
                GROUP BY category 
                ORDER BY count DESC
            """)
            results = cursor.fetchall()
        
        categories = [{"name": row[0], "count": row[1]} for row in results]
        
        return {
            "success": True,
            "categories": categories,
            "available_categories": self.categories
        }
    
    async def _get_insights(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """知識ベースからの洞察を提供"""
        topic = request.get("topic", "general")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 統計情報を取得
            cursor.execute("SELECT COUNT(*) FROM knowledge_entries")
            total_knowledge = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT category, COUNT(*) 
                FROM knowledge_entries 
                GROUP BY category 
                ORDER BY COUNT(*) DESC 
                LIMIT 5
            """)
            top_categories = cursor.fetchall()
            
            cursor.execute("""
                SELECT title, access_count 
                FROM knowledge_entries 
                ORDER BY access_count DESC 
                LIMIT 3
            """)
            popular_knowledge = cursor.fetchall()
        
        insights = {
            "knowledge_base_stats": {
                "total_entries": total_knowledge,
                "top_categories": [{"category": cat, "count": count} for cat, count in top_categories],
                "most_accessed": [{"title": title, "access_count": count} for title, count in popular_knowledge]
            },
            "recommendations": [
                "Consider creating more documentation in less populated categories",
                "Popular knowledge indicates team interests and needs",
                "Regular knowledge updates improve relevance"
            ]
        }
        
        return {
            "success": True,
            "topic": topic,
            "insights": insights
        }
    
    def get_capabilities(self) -> List[str]:
        """ナレッジ賢者の能力一覧"""
        return [
            "store_knowledge",
            "search_knowledge", 
            "learn_from_experience",
            "get_recommendations",
            "update_knowledge",
            "get_categories",
            "get_insights",
            "knowledge_analytics"
        ]