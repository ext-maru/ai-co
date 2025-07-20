#!/usr/bin/env python3
"""
🔍 RAG Manager - エルダーズギルド知識探索システム
RAG賢者 (Search Mystic) の完全実装

機能:
- 情報探索と理解
- 膨大な知識から最適解発見
- コンテキスト検索、知識統合、回答生成
- 4賢者連携による自律学習

作成者: クロードエルダー
作成日: 2025-07-19
"""

import hashlib
import json
import logging
import os
import re
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """検索結果データクラス"""

    content: str
    source: str
    relevance_score: float
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class KnowledgeItem:
    """知識アイテムデータクラス"""

    id: str
    content: str
    source: str
    category: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    access_count: int


class RagManager:
    """
    🔍 RAG賢者 (Search Mystic) - 完全実装

    エルダーズギルドの知識探索システム
    膨大な知識から最適解を発見する
    """

    def __init__(
        self, knowledge_base_path: str = "/home/aicompany/ai_co/knowledge_base"
    ):
        """RAG Managerを初期化"""
        self.knowledge_base_path = Path(knowledge_base_path)
        self.db_path = self.knowledge_base_path / "rag_knowledge.db"
        self.cache_path = self.knowledge_base_path / "search_cache.json"

        # ディレクトリ作成
        self.knowledge_base_path.mkdir(exist_ok=True)

        # データベース初期化
        self._init_database()

        # キャッシュ初期化
        self.search_cache = self._load_cache()

        logger.info("🔍 RAG Manager (Search Mystic) 初期化完了")

    def _init_database(self):
        """知識データベースを初期化"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 知識アイテムテーブル
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS knowledge_items (
                        id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        source TEXT NOT NULL,
                        category TEXT NOT NULL,
                        tags TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        access_count INTEGER DEFAULT 0
                    )
                """
                )

                # 検索履歴テーブル
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS search_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query TEXT NOT NULL,
                        results_count INTEGER DEFAULT 0,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        execution_time REAL DEFAULT 0.0
                    )
                """
                )

                # インデックス作成
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_content ON knowledge_items(content)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_category ON knowledge_items(category)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_source ON knowledge_items(source)"
                )

                conn.commit()
                logger.info("📊 RAG知識データベース初期化完了")

        except Exception as e:
            logger.error(f"❌ データベース初期化エラー: {e}")
            raise

    def _load_cache(self) -> Dict[str, Any]:
        """検索キャッシュをロード"""
        try:
            if self.cache_path.exists():
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                logger.info(f"💾 検索キャッシュロード完了 ({len(cache)} エントリ)")
                return cache
        except Exception as e:
            logger.warning(f"⚠️ キャッシュロードエラー: {e}")

        return {}

    def _save_cache(self):
        """検索キャッシュを保存"""
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(
                    self.search_cache, f, ensure_ascii=False, indent=2, default=str
                )
        except Exception as e:
            logger.warning(f"⚠️ キャッシュ保存エラー: {e}")

    def add_knowledge(
        self, content: str, source: str, category: str, tags: List[str] = None
    ) -> str:
        """知識アイテムを追加"""
        try:
            # IDを生成
            knowledge_id = hashlib.md5(f"{content}{source}".encode()).hexdigest()

            # タグをJSON形式で保存
            tags_json = json.dumps(tags or [])

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO knowledge_items
                    (id, content, source, category, tags, updated_at, access_count)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 0)
                """,
                    (knowledge_id, content, source, category, tags_json),
                )
                conn.commit()

            logger.info(f"📚 知識アイテム追加: {knowledge_id} ({category})")
            return knowledge_id

        except Exception as e:
            logger.error(f"❌ 知識追加エラー: {e}")
            raise

    def search_knowledge(
        self, query: str, category: str = None, limit: int = 10
    ) -> List[SearchResult]:
        """知識を検索"""
        start_time = time.time()

        try:
            # キャッシュ確認
            cache_key = f"{query}_{category}_{limit}"
            if cache_key in self.search_cache:
                cached_result = self.search_cache[cache_key]
                # キャッシュの有効期限チェック（1時間）
                cache_time = datetime.fromisoformat(cached_result["timestamp"])
                if datetime.now() - cache_time < timedelta(hours=1):
                    logger.info(f"💾 キャッシュから検索結果取得: {query}")
                    return [SearchResult(**item) for item in cached_result["results"]]

            # データベース検索
            results = self._search_database(query, category, limit)

            # 検索履歴を記録
            execution_time = time.time() - start_time
            self._record_search_history(query, len(results), execution_time)

            # キャッシュに保存
            self.search_cache[cache_key] = {
                "timestamp": datetime.now().isoformat(),
                "results": [
                    {
                        "content": r.content,
                        "source": r.source,
                        "relevance_score": r.relevance_score,
                        "timestamp": r.timestamp.isoformat(),
                        "metadata": r.metadata,
                    }
                    for r in results
                ],
            }
            self._save_cache()

            logger.info(f"🔍 検索完了: '{query}' -> {len(results)}件 ({execution_time:.3f}s)")
            return results

        except Exception as e:
            logger.error(f"❌ 検索エラー: {e}")
            return []

    def _search_database(
        self, query: str, category: str, limit: int
    ) -> List[SearchResult]:
        """データベースから検索"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 基本検索クエリ
                base_query = """
                    SELECT content, source, category, tags, created_at, updated_at, access_count
                    FROM knowledge_items
                    WHERE content LIKE ?
                """
                params = [f"%{query}%"]

                # カテゴリフィルタ
                if category:
                    base_query += " AND category = ?"
                    params.append(category)

                base_query += " ORDER BY access_count DESC, updated_at DESC LIMIT ?"
                params.append(limit)

                cursor.execute(base_query, params)
                rows = cursor.fetchall()

                # SearchResultオブジェクトに変換
                results = []
                for row in rows:
                    (
                        content,
                        source,
                        cat,
                        tags_json,
                        created_at,
                        updated_at,
                        access_count,
                    ) = row

                    # 関連性スコア計算（簡易版）
                    relevance_score = self._calculate_relevance(
                        query, content, access_count
                    )

                    # タグをパース
                    try:
                        tags = json.loads(tags_json)
                    except:
                        tags = []

                    result = SearchResult(
                        content=content,
                        source=source,
                        relevance_score=relevance_score,
                        timestamp=datetime.fromisoformat(updated_at),
                        metadata={
                            "category": cat,
                            "tags": tags,
                            "access_count": access_count,
                            "created_at": created_at,
                        },
                    )
                    results.append(result)

                    # アクセス回数を増加
                    cursor.execute(
                        "UPDATE knowledge_items SET access_count = access_count + 1 WHERE content = ? AND source = ?",
                        (content, source),
                    )

                conn.commit()
                return results

        except Exception as e:
            logger.error(f"❌ データベース検索エラー: {e}")
            return []

    def _calculate_relevance(
        self, query: str, content: str, access_count: int
    ) -> float:
        """関連性スコアを計算"""
        try:
            # 単語一致度
            query_words = set(query.lower().split())
            content_words = set(content.lower().split())
            word_match = len(query_words & content_words) / max(len(query_words), 1)

            # アクセス頻度ボーナス
            access_bonus = min(access_count / 100, 0.3)

            # 最終スコア
            score = word_match + access_bonus
            return min(score, 1.0)

        except Exception:
            return 0.1

    def _record_search_history(
        self, query: str, results_count: int, execution_time: float
    ):
        """検索履歴を記録"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO search_history (query, results_count, execution_time)
                    VALUES (?, ?, ?)
                """,
                    (query, results_count, execution_time),
                )
                conn.commit()
        except Exception as e:
            logger.warning(f"⚠️ 検索履歴記録エラー: {e}")

    def index_knowledge_base(self) -> int:
        """knowledge_baseディレクトリから知識をインデックス"""
        try:
            indexed_count = 0

            # Markdownファイルを検索
            for md_file in self.knowledge_base_path.glob("**/*.md"):
                try:
                    with open(md_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    # カテゴリを推定
                    category = self._infer_category(md_file.name, content)

                    # タグを抽出
                    tags = self._extract_tags(content)

                    # 知識を追加
                    self.add_knowledge(content, str(md_file), category, tags)
                    indexed_count += 1

                except Exception as e:
                    logger.warning(f"⚠️ ファイル処理エラー {md_file}: {e}")

            logger.info(f"📚 知識ベースインデックス完了: {indexed_count}ファイル")
            return indexed_count

        except Exception as e:
            logger.error(f"❌ インデックス処理エラー: {e}")
            return 0

    def _infer_category(self, filename: str, content: str) -> str:
        """ファイル名と内容からカテゴリを推定"""
        filename_lower = filename.lower()
        content_lower = content.lower()

        # カテゴリ推定ルール
        if "tdd" in filename_lower or "test" in filename_lower:
            return "testing"
        elif "elder" in filename_lower or "guild" in filename_lower:
            return "elders_guild"
        elif "guide" in filename_lower or "doc" in filename_lower:
            return "documentation"
        elif "api" in filename_lower or "service" in filename_lower:
            return "development"
        elif "protocol" in filename_lower or "process" in filename_lower:
            return "process"
        elif any(word in content_lower for word in ["error", "incident", "failure"]):
            return "incident_management"
        else:
            return "general"

    def _extract_tags(self, content: str) -> List[str]:
        """内容からタグを抽出"""
        tags = set()

        # 技術用語を検索
        tech_terms = [
            "python",
            "javascript",
            "docker",
            "git",
            "github",
            "tdd",
            "testing",
            "api",
            "database",
            "sql",
            "elder",
            "guild",
            "sage",
            "workflow",
        ]

        content_lower = content.lower()
        for term in tech_terms:
            if term in content_lower:
                tags.add(term)

        # マークダウンヘッダーからタグ抽出
        headers = re.findall(r"#+\s+(.+)", content)
        for header in headers[:3]:  # 最初の3個のヘッダー
            words = re.findall(r"\w+", header.lower())
            tags.update([w for w in words if len(w) > 3])

        return list(tags)[:10]  # 最大10個のタグ

    def get_knowledge_stats(self) -> Dict[str, Any]:
        """知識ベース統計を取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 総知識数
                cursor.execute("SELECT COUNT(*) FROM knowledge_items")
                total_items = cursor.fetchone()[0]

                # カテゴリ別統計
                cursor.execute(
                    """
                    SELECT category, COUNT(*)
                    FROM knowledge_items
                    GROUP BY category
                    ORDER BY COUNT(*) DESC
                """
                )
                category_stats = dict(cursor.fetchall())

                # 検索統計
                cursor.execute(
                    """
                    SELECT COUNT(*), AVG(execution_time), MAX(timestamp)
                    FROM search_history
                    WHERE timestamp > datetime('now', '-24 hours')
                """
                )
                search_stats = cursor.fetchone()

                return {
                    "total_knowledge_items": total_items,
                    "categories": category_stats,
                    "recent_searches": {
                        "count": search_stats[0] or 0,
                        "avg_time": search_stats[1] or 0,
                        "last_search": search_stats[2] or "N/A",
                    },
                    "cache_size": len(self.search_cache),
                }

        except Exception as e:
            logger.error(f"❌ 統計取得エラー: {e}")
            return {}

    def consult_on_issue(self, issue_title: str, issue_body: str) -> Dict[str, Any]:
        """
        イシューに対してRAG賢者として相談に応答
        4賢者連携で呼び出される主要メソッド
        """
        try:
            logger.info(f"🧙‍♂️ RAG賢者相談開始: {issue_title}")

            # 検索クエリを構築
            search_query = f"{issue_title} {issue_body}"

            # 関連知識を検索
            results = self.search_knowledge(search_query, limit=5)

            # 推奨アプローチを分析
            recommendations = self._analyze_recommendations(
                issue_title, issue_body, results
            )

            # 技術スタック分析
            tech_stack = self._analyze_tech_stack(issue_body)

            # 複雑度評価
            complexity = self._evaluate_complexity(issue_title, issue_body)

            consultation_result = {
                "status": "success",
                "issue_analysis": {
                    "title": issue_title,
                    "complexity": complexity,
                    "tech_stack": tech_stack,
                },
                "recommendations": recommendations,
                "related_knowledge": [
                    {
                        "content": r.content[:200] + "..."
                        if len(r.content) > 200
                        else r.content,
                        "source": r.source,
                        "relevance": r.relevance_score,
                    }
                    for r in results
                ],
                "consultation_metadata": {
                    "search_results_count": len(results),
                    "consultation_time": datetime.now().isoformat(),
                    "sage": "RAG賢者 (Search Mystic)",
                },
            }

            logger.info(f"✅ RAG賢者相談完了: {len(results)}件の関連知識")
            return consultation_result

        except Exception as e:
            logger.error(f"❌ RAG賢者相談エラー: {e}")
            return {"status": "error", "error": str(e), "sage": "RAG賢者 (Search Mystic)"}

    def _analyze_recommendations(
        self, title: str, body: str, search_results: List[SearchResult]
    ) -> List[str]:
        """推奨アプローチを分析"""
        recommendations = []

        # タイトル・本文分析
        text = f"{title} {body}".lower()

        # 技術別推奨
        if "test" in text or "tdd" in text:
            recommendations.append("TDD（テスト駆動開発）アプローチを推奨")

        if "api" in text or "endpoint" in text:
            recommendations.append("API設計とOpenAPI仕様書作成を推奨")

        if "database" in text or "sql" in text:
            recommendations.append("データベース設計とマイグレーション計画を推奨")

        if "ui" in text or "frontend" in text:
            recommendations.append("コンポーネント設計とスタイルガイド準拠を推奨")

        # 関連知識からの推奨
        for result in search_results:
            if result.relevance_score > 0.7:
                if "pattern" in result.content.lower():
                    recommendations.append("既存パターンの活用を推奨")
                if "error" in result.content.lower():
                    recommendations.append("エラーハンドリング強化を推奨")

        return recommendations[:5]  # 最大5個

    def _analyze_tech_stack(self, body: str) -> List[str]:
        """技術スタックを分析"""
        tech_stack = []
        body_lower = body.lower()

        # プログラミング言語
        languages = ["python", "javascript", "typescript", "java", "go", "rust"]
        for lang in languages:
            if lang in body_lower:
                tech_stack.append(lang.title())

        # フレームワーク
        frameworks = [
            "react",
            "vue",
            "angular",
            "django",
            "flask",
            "fastapi",
            "express",
        ]
        for fw in frameworks:
            if fw in body_lower:
                tech_stack.append(fw.title())

        # データベース
        databases = ["postgresql", "mysql", "mongodb", "redis", "sqlite"]
        for db in databases:
            if db in body_lower:
                tech_stack.append(db.upper())

        # インフラ
        infra = ["docker", "kubernetes", "aws", "gcp", "azure"]
        for inf in infra:
            if inf in body_lower:
                tech_stack.append(inf.upper())

        return tech_stack

    def _evaluate_complexity(self, title: str, body: str) -> str:
        """複雑度を評価"""
        text = f"{title} {body}".lower()
        complexity_score = 0

        # 複雑度指標
        complexity_indicators = [
            ("integration", 2),
            ("api", 1),
            ("database", 1),
            ("authentication", 2),
            ("security", 2),
            ("performance", 1),
            ("scalability", 2),
            ("migration", 2),
            ("refactor", 1),
            ("architecture", 3),
            ("system", 1),
            ("multi", 2),
        ]

        for indicator, score in complexity_indicators:
            if indicator in text:
                complexity_score += score

        # 長さによる調整
        if len(body) > 500:
            complexity_score += 1
        if len(body) > 1000:
            complexity_score += 1

        # 複雑度分類
        if complexity_score <= 2:
            return "low"
        elif complexity_score <= 5:
            return "medium"
        else:
            return "high"


# 互換性関数
def setup(*args, **kwargs):
    """RAG Manager セットアップ"""
    logger.info("🔍 RAG Manager setup実行")
    manager = RagManager()
    manager.index_knowledge_base()
    return manager


def main():
    """メイン実行関数"""
    logger.info("🔍 RAG Manager メイン実行開始")

    manager = RagManager()

    # 知識ベースインデックス
    indexed = manager.index_knowledge_base()

    # 統計表示
    stats = manager.get_knowledge_stats()
    logger.info(f"📊 RAG Manager統計: {stats}")

    logger.info("🏁 RAG Manager メイン実行完了")


# エクスポート
__all__ = ["RagManager", "SearchResult", "KnowledgeItem", "setup", "main"]


if __name__ == "__main__":
    main()
