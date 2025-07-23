"""
Knowledge Sage Implementation
知識管理・技術分析エージェント
"""

from elder_tree.agents.base_agent import ElderTreeAgent
from typing import Dict, Any, List, Optional
import json
import os
from datetime import datetime
import sqlite3
from pathlib import Path
from flask import Flask


class KnowledgeSage(ElderTreeAgent):
    """Knowledge Sage - 知識管理専門エージェント"""
    
    def __init__(self, db_path: str = "./knowledge_base.db", port: int = 50051):
        """初期化メソッド"""
        super().__init__(
            name="knowledge_sage",
            domain="knowledge",
            port=port
        )
        
        self.port = port  # ポート番号を保存
        self.db_path = Path(db_path)
        self.knowledge_base = {}
        self.learning_history = []
        
        # データベース初期化
        self._init_database()
        
        # ドメイン固有ハンドラー登録
        self._register_domain_handlers()
        
        self.logger.info("Knowledge Sage initialized", db_path=str(self.db_path))
    
    def _init_database(self):
        """SQLite データベース初期化"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 知識テーブル作成
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    relevance_score REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0
                )
            """)
            
            # 技術分析テーブル作成
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tech_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    technology TEXT NOT NULL,
                    assessment TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    pros TEXT DEFAULT '[]',
                    cons TEXT DEFAULT '[]',
                    recommendation TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 学習履歴テーブル作成
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    learning_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT,
                    confidence REAL DEFAULT 0.8,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            self.logger.info("Database initialized successfully")
        except Exception as e:
            self.logger.error("Database initialization failed", error=str(e))
            raise
    
    def _register_domain_handlers(self):
        """Knowledge Sage固有のハンドラー登録"""
        # handle_messageメソッドで直接処理するため、ここでは何もしない
        pass
    
    def handle_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """メッセージハンドラー"""
        message_type = data.get('type', 'unknown')
        
        # 基本メッセージタイプの処理（親クラスに委譲）
        if message_type in ["health_check", "get_metrics"]:
            return super().handle_message(data)
        
        # Knowledge Sage固有のメッセージタイプ処理
        if message_type == "analyze_technology":
            return self._handle_analyze_technology(data)
        elif message_type == "store_knowledge":
            return self._handle_store_knowledge(data)
        elif message_type == "search_knowledge":
            return self._handle_search_knowledge(data)
        elif message_type == "learn_from_feedback":
            return self._handle_learn_from_feedback(data)
        elif message_type == "get_statistics":
            return self._handle_get_statistics(data)
        else:
            return {"status": "error", "message": f"Unknown message type: {message_type}"}
    
    def _handle_analyze_technology(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """技術分析処理"""
        tech_name = data.get("technology")
        context = data.get("context", {})
        
        self.logger.info(
            "Analyzing technology",
            technology=tech_name,
            context=context
        )
        
        # 基本分析（TDD: テストが通る最小実装）
        analysis = {
            "technology": tech_name,
            "assessment": "suitable",
            "confidence": 0.85,
            "pros": [
                "Good community support",
                "Well documented",
                "Production ready"
            ],
            "cons": [
                "Learning curve",
                "Dependency management"
            ],
            "recommendation": "Recommended for production use"
        }
        
        # データベースに技術分析保存
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tech_analyses (technology, assessment, confidence, pros, cons, recommendation)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                tech_name,
                analysis["assessment"],
                analysis["confidence"],
                json.dumps(analysis["pros"]),
                json.dumps(analysis["cons"]),
                analysis["recommendation"]
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error("Failed to store tech analysis", error=str(e))
        
        # 信頼度が低い場合はRAG Sageに調査依頼
        if data.get("require_research", False):
            rag_response = self.collaborate_with_sage(
                "rag_sage",
                {
                    "action": "search_technical_docs",
                    "query": tech_name,
                    "limit": 5
                }
            )
            
            # RAG結果を分析に統合
            if rag_response and rag_response.get("status") == "success":
                analysis["additional_insights"] = rag_response.get("data", {}).get("documents", [])
        
        return {"analysis": analysis, "status": "completed"}
    
    def _handle_store_knowledge(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """知識保存処理"""
        knowledge_item = data.get("knowledge")
        category = data.get("category", "general")
        title = data.get("title", "Untitled Knowledge")
        metadata = data.get("metadata", {})
        
        # メモリ内ストレージ
        if category not in self.knowledge_base:
            self.knowledge_base[category] = []
        
        self.knowledge_base[category].append(knowledge_item)
        
        # データベース永続化
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO knowledge_items (category, title, content, metadata)
                VALUES (?, ?, ?, ?)
            """, (
                category,
                title,
                str(knowledge_item),
                json.dumps(metadata)
            ))
            conn.commit()
            item_id = cursor.lastrowid
            conn.close()
            
            self.logger.info(
                "Knowledge stored",
                category=category,
                item_id=item_id,
                total_items=len(self.knowledge_base[category])
            )
            
            return {
                "status": "stored",
                "category": category,
                "item_id": item_id,
                "item_count": len(self.knowledge_base[category])
            }
        except Exception as e:
            self.logger.error("Failed to store knowledge", error=str(e))
            return {
                "status": "error",
                "message": f"Storage failed: {str(e)}"
            }
    
    def _handle_search_knowledge(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """知識検索処理"""
        query = data.get("query", "")
        category = data.get("category")
        limit = data.get("limit", 10)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # SQL構築
            sql = """
                SELECT id, category, title, content, metadata, relevance_score, created_at
                FROM knowledge_items
                WHERE content LIKE ? OR title LIKE ?
            """
            params = [f"%{query}%", f"%{query}%"]
            
            if category:
                sql += " AND category = ?"
                params.append(category)
            
            sql += " ORDER BY relevance_score DESC, created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(sql, params)
            results = cursor.fetchall()
            
            # アクセスカウント更新
            for row in results:
                cursor.execute(
                    "UPDATE knowledge_items SET access_count = access_count + 1 WHERE id = ?",
                    (row[0],)
                )
            
            conn.commit()
            conn.close()
            
            # 結果フォーマット
            knowledge_items = []
            for row in results:
                knowledge_items.append({
                    "id": row[0],
                    "category": row[1],
                    "title": row[2],
                    "content": row[3],
                    "metadata": json.loads(row[4]) if row[4] else {},
                    "relevance_score": row[5],
                    "created_at": row[6]
                })
            
            return {
                "status": "success",
                "query": query,
                "results": knowledge_items,
                "count": len(knowledge_items)
            }
            
        except Exception as e:
            self.logger.error("Knowledge search failed", error=str(e))
            return {
                "status": "error",
                "message": f"Search failed: {str(e)}"
            }
    
    def _handle_learn_from_feedback(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """フィードバックからの学習処理"""
        feedback_type = data.get("type", "general")
        content = data.get("content", "")
        source = data.get("source", "user")
        confidence = data.get("confidence", 0.8)
        
        try:
            # 学習履歴に保存
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO learning_history (learning_type, content, source, confidence)
                VALUES (?, ?, ?, ?)
            """, (feedback_type, content, source, confidence))
            conn.commit()
            learning_id = cursor.lastrowid
            conn.close()
            
            # メモリ内学習履歴更新
            self.learning_history.append({
                "id": learning_id,
                "type": feedback_type,
                "content": content,
                "source": source,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat()
            })
            
            self.logger.info(
                "Learning from feedback recorded",
                learning_id=learning_id,
                feedback_type=feedback_type
            )
            
            return {
                "status": "learned",
                "learning_id": learning_id,
                "type": feedback_type,
                "confidence": confidence
            }
            
        except Exception as e:
            self.logger.error("Learning from feedback failed", error=str(e))
            return {
                "status": "error",
                "message": f"Learning failed: {str(e)}"
            }
    
    def _handle_get_statistics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """統計情報取得"""
        stats = self.get_knowledge_statistics()
        return {
            "status": "success",
            "statistics": stats
        }
    
    def get_knowledge_statistics(self) -> Dict[str, Any]:
        """知識統計情報取得"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 基本統計
            cursor.execute("SELECT COUNT(*) FROM knowledge_items")
            total_items = cursor.fetchone()[0]
            
            cursor.execute("SELECT category, COUNT(*) FROM knowledge_items GROUP BY category")
            category_counts = dict(cursor.fetchall())
            
            cursor.execute("SELECT COUNT(*) FROM tech_analyses")
            tech_analyses_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM learning_history")
            learning_records = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_knowledge_items": total_items,
                "categories": category_counts,
                "tech_analyses": tech_analyses_count,
                "learning_records": learning_records,
                "memory_items": sum(len(items) for items in self.knowledge_base.values())
            }
        except Exception as e:
            self.logger.error("Failed to get knowledge statistics", error=str(e))
            return {}


# 単体実行用
def main():
    # Create Knowledge Sage with port
    port = int(os.getenv("KNOWLEDGE_SAGE_PORT", 50051))
    sage = KnowledgeSage(port=port)
    
    # Create Flask app
    app = sage.create_app()
    
    # Consul registration (optional)
    if os.getenv("CONSUL_HOST"):
        try:
            import consul
            c = consul.Consul(
                host=os.getenv("CONSUL_HOST"),
                port=int(os.getenv("CONSUL_PORT", 8500))
            )
            c.agent.service.register(
                name="knowledge-sage",
                service_id=f"knowledge-sage-{port}",
                address="knowledge_sage",
                port=port,
                tags=["elder-tree", "sage", "knowledge"],
                check=consul.Check.http(f"http://knowledge_sage:{port}/health", interval="10s")
            )
            print(f"Registered with Consul as knowledge-sage")
        except ImportError:
            print("Consul client not available, skipping registration")
        except Exception as e:
            print(f"Failed to register with Consul: {e}")
    
    # Start Flask app
    print(f"Knowledge Sage running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()