#!/usr/bin/env python3
"""
エルダーズ知識管理システム
ベクトルデータベースを使用した意味検索可能な知識管理
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import psycopg2
from openai import OpenAI
from psycopg2.extras import RealDictCursor

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EldersKnowledgeManager:
    """エルダーズ知識管理システムのメインクラス"""

    def __init__(self, db_config: Dict[str, str] = None, openai_api_key: str = None):
        """
        初期化

        Args:
            db_config: PostgreSQL接続設定
            openai_api_key: OpenAI APIキー
        """
        self.db_config = db_config or {
            "host": "localhost",
            "port": 5432,
            "database": "elders_knowledge",
            "user": os.getenv("USER", "postgres"),
        }

        # OpenAI APIキーの設定
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        else:
            logger.warning("OpenAI APIキーが設定されていません。埋め込み機能は使用できません。")
            self.openai_client = None

    def _get_connection(self):
        """データベース接続を取得"""
        return psycopg2.connect(**self.db_config)

    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """テキストから埋め込みベクトルを生成"""
        if not self.openai_client:
            logger.warning("OpenAI APIキーが設定されていないため、埋め込みを生成できません")
            return None

        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002", input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"埋め込み生成エラー: {e}")
            return None

    def add_elder(
        self,
        name: str,
        expertise: List[str],
        description: str = "",
        reliability_score: float = 1.0,
    ) -> int:
        """新しいエルダーを追加"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO elders (name, expertise, description, reliability_score)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """,
                    (name, expertise, description, reliability_score),
                )
                elder_id = cur.fetchone()[0]
                conn.commit()
                logger.info(f"エルダー追加完了: {name} (ID: {elder_id})")
                return elder_id

    def add_knowledge(
        self,
        title: str,
        content: str,
        category_id: int,
        elder_id: int,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
        importance_score: float = 0.5,
    ) -> int:
        """新しい知識エントリを追加"""
        # 埋め込みベクトルの生成
        embedding = self._generate_embedding(f"{title}\n{content}")

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO knowledge_entries
                    (title, content, category_id, elder_id, embedding, tags, metadata, importance_score)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """,
                    (
                        title,
                        content,
                        category_id,
                        elder_id,
                        embedding,
                        tags or [],
                        json.dumps(metadata or {}),
                        importance_score,
                    ),
                )
                knowledge_id = cur.fetchone()[0]
                conn.commit()
                logger.info(f"知識追加完了: {title} (ID: {knowledge_id})")
                return knowledge_id

    def search_knowledge(
        self,
        query: str,
        limit: int = 10,
        category_id: Optional[int] = None,
        elder_id: Optional[int] = None,
        min_score: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """意味検索で知識を検索"""
        # クエリの埋め込みベクトルを生成
        query_embedding = self._generate_embedding(query)

        if not query_embedding:
            logger.warning("埋め込みが生成できないため、フォールバック検索を実行")
            return self._search_knowledge_fallback(query, limit, category_id, elder_id)

        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # ベース SQLクエリ
                sql = """
                    SELECT
                        k.id,
                        k.title,
                        k.content,
                        k.tags,
                        k.metadata,
                        k.importance_score,
                        k.created_at,
                        k.updated_at,
                        e.name as elder_name,
                        c.name as category_name,
                        1 - (k.embedding <=> %s::vector) as similarity_score
                    FROM knowledge_entries k
                    JOIN elders e ON k.elder_id = e.id
                    JOIN knowledge_categories c ON k.category_id = c.id
                    WHERE 1=1
                """
                params = [query_embedding]

                # フィルタ条件を追加
                if category_id:
                    sql += " AND k.category_id = %s"
                    params.append(category_id)

                if elder_id:
                    sql += " AND k.elder_id = %s"
                    params.append(elder_id)

                # 類似度でフィルタし、ソート
                sql += f"""
                    AND 1 - (k.embedding <=> %s::vector) >= %s
                    ORDER BY similarity_score DESC, k.importance_score DESC
                    LIMIT %s
                """
                params.extend([query_embedding, min_score, limit])

                cur.execute(sql, params)
                results = cur.fetchall()

                # 検索履歴を保存
                cur.execute(
                    """
                    INSERT INTO search_history (query, query_embedding, results)
                    VALUES (%s, %s, %s)
                """,
                    (query, query_embedding, json.dumps([r["id"] for r in results])),
                )
                conn.commit()

                return results

    def _search_knowledge_fallback(
        self,
        query: str,
        limit: int = 10,
        category_id: Optional[int] = None,
        elder_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """フォールバック: テキスト検索で知識を検索"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                sql = """
                    SELECT
                        k.id,
                        k.title,
                        k.content,
                        k.tags,
                        k.metadata,
                        k.importance_score,
                        k.created_at,
                        k.updated_at,
                        e.name as elder_name,
                        c.name as category_name
                    FROM knowledge_entries k
                    JOIN elders e ON k.elder_id = e.id
                    JOIN knowledge_categories c ON k.category_id = c.id
                    WHERE (
                        k.title ILIKE %s OR
                        k.content ILIKE %s OR
                        %s = ANY(k.tags)
                    )
                """
                params = [f"%{query}%", f"%{query}%", query]

                if category_id:
                    sql += " AND k.category_id = %s"
                    params.append(category_id)

                if elder_id:
                    sql += " AND k.elder_id = %s"
                    params.append(elder_id)

                sql += " ORDER BY k.importance_score DESC LIMIT %s"
                params.append(limit)

                cur.execute(sql, params)
                return cur.fetchall()

    def add_knowledge_relation(
        self, source_id: int, target_id: int, relation_type: str, strength: float = 0.5
    ) -> int:
        """知識間の関連を追加"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO knowledge_relations
                    (source_id, target_id, relation_type, strength)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (source_id, target_id, relation_type)
                    DO UPDATE SET strength = EXCLUDED.strength
                    RETURNING id
                """,
                    (source_id, target_id, relation_type, strength),
                )
                relation_id = cur.fetchone()[0]
                conn.commit()
                return relation_id

    def get_related_knowledge(
        self, knowledge_id: int, relation_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """関連する知識を取得"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                sql = """
                    SELECT
                        k.*,
                        kr.relation_type,
                        kr.strength,
                        e.name as elder_name,
                        c.name as category_name
                    FROM knowledge_relations kr
                    JOIN knowledge_entries k ON kr.target_id = k.id
                    JOIN elders e ON k.elder_id = e.id
                    JOIN knowledge_categories c ON k.category_id = c.id
                    WHERE kr.source_id = %s
                """
                params = [knowledge_id]

                if relation_types:
                    sql += " AND kr.relation_type = ANY(%s)"
                    params.append(relation_types)

                sql += " ORDER BY kr.strength DESC"

                cur.execute(sql, params)
                return cur.fetchall()

    def update_search_feedback(self, search_id: int, feedback: int):
        """検索結果へのフィードバックを更新"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE search_history
                    SET user_feedback = %s
                    WHERE id = %s
                """,
                    (feedback, search_id),
                )
                conn.commit()

    def get_categories(self) -> List[Dict[str, Any]]:
        """全カテゴリを取得"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT * FROM knowledge_categories
                    ORDER BY name
                """
                )
                return cur.fetchall()

    def get_elders(self) -> List[Dict[str, Any]]:
        """全エルダーを取得"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT * FROM elders
                    ORDER BY reliability_score DESC, name
                """
                )
                return cur.fetchall()

    def bulk_import_knowledge(self, knowledge_data: List[Dict[str, Any]]):
        """知識を一括インポート"""
        success_count = 0
        error_count = 0

        for item in knowledge_data:
            try:
                self.add_knowledge(
                    title=item["title"],
                    content=item["content"],
                    category_id=item.get("category_id", 1),
                    elder_id=item.get("elder_id", 1),
                    tags=item.get("tags", []),
                    metadata=item.get("metadata", {}),
                    importance_score=item.get("importance_score", 0.5),
                )
                success_count += 1
            except Exception as e:
                logger.error(f"インポートエラー: {item.get('title', 'Unknown')}: {e}")
                error_count += 1

        logger.info(f"一括インポート完了: 成功 {success_count}件, エラー {error_count}件")
        return success_count, error_count


# テスト用サンプルデータ生成関数
def create_sample_data(manager: EldersKnowledgeManager):
    """サンプルデータを作成"""
    sample_knowledge = [
        {
            "title": "Pythonでのベクトルデータベース活用",
            "content": "pgvectorを使用してPostgreSQLでベクトル検索を実装する方法。埋め込みベクトルを使った意味検索により、キーワード検索では見つからない関連情報も発見できます。",
            "category_id": 1,
            "elder_id": 1,
            "tags": ["Python", "PostgreSQL", "pgvector", "ベクトル検索"],
            "importance_score": 0.9,
        },
        {
            "title": "効果的なチームマネジメント",
            "content": "チームメンバーの強みを理解し、適切な役割分担を行うことが重要です。定期的な1on1ミーティングと透明性の高いコミュニケーションが信頼関係を築きます。",
            "category_id": 2,
            "elder_id": 2,
            "tags": ["マネジメント", "リーダーシップ", "チームビルディング"],
            "importance_score": 0.8,
        },
        {
            "title": "健康的な睡眠習慣",
            "content": "毎日同じ時間に就寝・起床することで体内時計が整います。寝る前のスマートフォン使用を避け、適度な運動を心がけることで睡眠の質が向上します。",
            "category_id": 3,
            "elder_id": 3,
            "tags": ["健康", "睡眠", "生活習慣"],
            "importance_score": 0.7,
        },
    ]

    return manager.bulk_import_knowledge(sample_knowledge)


if __name__ == "__main__":
    # テスト実行
    manager = EldersKnowledgeManager()

    # サンプルデータの作成
    print("サンプルデータを作成中...")
    success, errors = create_sample_data(manager)
    print(f"作成完了: 成功 {success}件")

    # 検索テスト
    print("\n検索テスト: 'ベクトル'")
    results = manager.search_knowledge("ベクトル", limit=5)
    for result in results:
        print(f"- {result['title']} (類似度: {result.get('similarity_score', 'N/A')})")
