#!/usr/bin/env python3
"""
🔍 Lightweight RAG Sage - メモリ効率的な実装
Elder Flow用の軽量版RAG賢者実装

主な最適化:
- 遅延初期化
- ストリーミング処理
- キャッシュサイズ制限
- バッチ処理
- リソース管理

作成者: クロードエルダー
作成日: 2025-07-20
"""

import gc
import hashlib
import json
import logging
import os
import sqlite3
import time
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """検索結果データクラス（軽量版）"""

    content: str
    source: str
    relevance_score: float
    timestamp: datetime
    metadata: Dict[str, Any]


class LightweightRAGSage:
    """
    🔍 軽量版RAG賢者 - メモリ効率的な実装

    Elder Flow用に最適化されたRAG Manager
    """

    def __init__(
        self,
        knowledge_base_path: str = "/home/aicompany/ai_co/knowledge_base",
        max_cache_size: int = 100,
        enable_connection_pool: bool = False,
    ):
        """軽量版RAG Sageを初期化（遅延初期化）"""
        self.knowledge_base_path = Path(knowledge_base_path)
        self.db_path = self.knowledge_base_path / "rag_knowledge_light.db"
        self.max_cache_size = max_cache_size
        self.enable_connection_pool = enable_connection_pool

        # 遅延初期化のためのフラグ
        self.is_initialized = False
        self._db_connection = None
        self._connection_count = 0

        # LRUキャッシュ（OrderedDictで実装）
        self.search_cache = OrderedDict()

        # ディレクトリ作成
        self.knowledge_base_path.mkdir(exist_ok=True)

        # 最小限の初期化のみ実行
        self.is_initialized = True
        logger.info("🔍 Lightweight RAG Sage 初期化完了（遅延初期化モード）")

    def _get_connection(self) -> sqlite3.Connection:
        """データベース接続を取得（遅延初期化）"""
        if self._db_connection is None:
            self._init_database()
        return self._db_connection

    def _init_database(self):
        """データベースを遅延初期化"""
        try:
            # メモリ効率的な設定でデータベース接続
            self._db_connection = sqlite3.connect(
                self.db_path, check_same_thread=False, isolation_level=None  # 自動コミット
            )
            self._connection_count = 1

            # WALモードで並行性を向上
            self._db_connection.execute("PRAGMA journal_mode=WAL")
            # キャッシュサイズを制限
            self._db_connection.execute("PRAGMA cache_size=1000")

            cursor = self._db_connection.cursor()

            # 最小限のテーブル作成
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_items (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    category TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 最小限のインデックス
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_category ON knowledge_items(category)"
            )

            logger.info("📊 軽量版データベース初期化完了")

        except Exception as e:
            logger.error(f"❌ データベース初期化エラー: {e}")
            raise

    def add_knowledge(self, content: str, source: str, category: str) -> str:
        """知識を追加（簡易版）"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # IDを生成
            knowledge_id = hashlib.md5(f"{content[:100]}{source}".encode()).hexdigest()[
                :16
            ]

            cursor.execute(
                """
                INSERT OR REPLACE INTO knowledge_items
                (id, content, source, category)
                VALUES (?, ?, ?, ?)
            """,
                (knowledge_id, content, source, category),
            )

            return knowledge_id

        except Exception as e:
            logger.error(f"❌ 知識追加エラー: {e}")
            raise

    def add_knowledge_batch(self, batch_data: List[Tuple[str, str, str]]):
        """バッチで知識を追加"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            prepared_data = []
            for content, source, category in batch_data:
                knowledge_id = hashlib.md5(
                    f"{content[:100]}{source}".encode()
                ).hexdigest()[:16]
                prepared_data.append((knowledge_id, content, source, category))

            cursor.executemany(
                """
                INSERT OR REPLACE INTO knowledge_items
                (id, content, source, category)
                VALUES (?, ?, ?, ?)
            """,
                prepared_data,
            )

            logger.info(f"📚 バッチ追加完了: {len(batch_data)}件")

        except Exception as e:
            logger.error(f"❌ バッチ追加エラー: {e}")
            raise

    def search_knowledge(
        self, query: str, category: str = None, limit: int = 10
    ) -> List[SearchResult]:
        """知識を検索（キャッシュ付き）"""
        try:
            # キャッシュ確認
            cache_key = f"{query}_{category}_{limit}"
            if cache_key in self.search_cache:
                # LRU: 最近使用したものを末尾に移動
                self.search_cache.move_to_end(cache_key)
                return self.search_cache[cache_key]

            # データベース検索
            conn = self._get_connection()
            cursor = conn.cursor()

            # シンプルなLIKE検索
            if category:
                cursor.execute(
                    """
                    SELECT content, source, category, created_at
                    FROM knowledge_items
                    WHERE content LIKE ? AND category = ?
                    LIMIT ?
                """,
                    (f"%{query}%", category, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT content, source, category, created_at
                    FROM knowledge_items
                    WHERE content LIKE ?
                    LIMIT ?
                """,
                    (f"%{query}%", limit),
                )

            results = []
            for row in cursor.fetchall():
                content, source, cat, created_at = row

                # 簡易関連性スコア
                score = self._calculate_simple_relevance(query, content)

                result = SearchResult(
                    content=content,
                    source=source,
                    relevance_score=score,
                    timestamp=datetime.fromisoformat(created_at),
                    metadata={"category": cat},
                )
                results.append(result)

            # キャッシュに保存（サイズ制限付き）
            self._add_to_cache(cache_key, results)

            return results

        except Exception as e:
            logger.error(f"❌ 検索エラー: {e}")
            return []

    def _calculate_simple_relevance(self, query: str, content: str) -> float:
        """簡易関連性スコア計算"""
        query_lower = query.lower()
        content_lower = content.lower()

        # 単純な出現回数ベース
        count = content_lower.count(query_lower)
        score = min(count / 10.0, 1.0)

        return score

    def _add_to_cache(self, key: str, value: Any):
        """LRUキャッシュに追加"""
        # キャッシュサイズ制限
        if len(self.search_cache) >= self.max_cache_size:
            # 最も古いものを削除
            self.search_cache.popitem(last=False)

        self.search_cache[key] = value

    def index_knowledge_base(self, max_files: int = 100) -> int:
        """知識ベースをインデックス（ファイル数制限付き）"""
        try:
            indexed_count = 0

            # Markdownファイルを検索（制限付き）
            md_files = list(self.knowledge_base_path.glob("**/*.md"))[:max_files]

            # バッチ処理用リスト
            batch_data = []

            for md_file in md_files:
                try:
                    # ストリーミング読み込み
                    content = self._read_file_streaming(md_file)
                    category = self._infer_simple_category(md_file.name)

                    batch_data.append((content, str(md_file), category))

                    # バッチサイズに達したら処理
                    if len(batch_data) >= 10:
                        self.add_knowledge_batch(batch_data)
                        batch_data = []
                        indexed_count += 10

                        # メモリ解放
                        gc.collect()

                except Exception as e:
                    logger.warning(f"⚠️ ファイル処理エラー {md_file}: {e}")

            # 残りのバッチを処理
            if batch_data:
                self.add_knowledge_batch(batch_data)
                indexed_count += len(batch_data)

            logger.info(f"📚 インデックス完了: {indexed_count}ファイル")
            return indexed_count

        except Exception as e:
            logger.error(f"❌ インデックス処理エラー: {e}")
            return 0

    def _read_file_streaming(self, file_path: Path, max_size: int = 10000) -> str:
        """ファイルをストリーミングで読み込み（サイズ制限付き）"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read(max_size)
                if len(content) == max_size:
                    content += "\n... (truncated)"
                return content
        except Exception as e:
            logger.warning(f"ファイル読み込みエラー: {e}")
            return ""

    def process_file_streaming(self, file_path: Path):
        """大きなファイルをストリーミング処理"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                chunk_size = 1000  # 1000文字ずつ処理
                buffer = ""

                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break

                    buffer += chunk
                    # 段落ごとに処理
                    paragraphs = buffer.split("\n\n")

                    # 最後の段落以外を処理
                    for para in paragraphs[:-1]:
                        if para.strip():
                            self.add_knowledge(
                                para,
                                str(file_path),
                                self._infer_simple_category(file_path.name),
                            )

                    # 最後の段落をバッファに保持
                    buffer = paragraphs[-1]

                # 残りを処理
                if buffer.strip():
                    self.add_knowledge(
                        buffer,
                        str(file_path),
                        self._infer_simple_category(file_path.name),
                    )

        except Exception as e:
            logger.error(f"ストリーミング処理エラー: {e}")

    def _infer_simple_category(self, filename: str) -> str:
        """シンプルなカテゴリ推定"""
        filename_lower = filename.lower()

        if "test" in filename_lower:
            return "testing"
        elif "elder" in filename_lower:
            return "elders_guild"
        elif "guide" in filename_lower or "doc" in filename_lower:
            return "documentation"
        else:
            return "general"

    def consult_on_issue(self, issue_title: str, issue_body: str) -> Dict[str, Any]:
        """イシューに対する相談（軽量版）"""
        try:
            logger.info(f"🧙‍♂️ 軽量版RAG賢者相談: {issue_title}")

            # シンプルな検索
            results = self.search_knowledge(
                f"{issue_title} {issue_body[:100]}", limit=3
            )

            # 基本的な分析
            recommendations = []
            if "memory" in issue_body.lower() or "メモリ" in issue_body:
                recommendations.append("メモリ効率的な実装パターンの使用を推奨")
                recommendations.append("遅延初期化とストリーミング処理を検討")

            if "error" in issue_body.lower():
                recommendations.append("エラーハンドリングの強化を推奨")

            return {
                "status": "success",
                "issue_analysis": {"title": issue_title, "complexity": "medium"},
                "recommendations": recommendations,
                "related_knowledge": [
                    {
                        "content": r.content[:100] + "...",
                        "source": r.source,
                        "relevance": r.relevance_score,
                    }
                    for r in results
                ],
                "consultation_metadata": {"sage": "軽量版RAG賢者", "mode": "lightweight"},
            }

        except Exception as e:
            logger.error(f"❌ 相談エラー: {e}")
            return {"status": "error", "error": str(e), "sage": "軽量版RAG賢者"}

    def cleanup(self):
        """リソースをクリーンアップ"""
        try:
            if self._db_connection:
                self._db_connection.close()
                self._db_connection = None

            self.search_cache.clear()
            gc.collect()

            logger.info("🧹 リソースクリーンアップ完了")

        except Exception as e:
            logger.warning(f"クリーンアップエラー: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得（軽量版）"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM knowledge_items")
            total = cursor.fetchone()[0]

            return {
                "total_items": total,
                "cache_size": len(self.search_cache),
                "max_cache_size": self.max_cache_size,
                "mode": "lightweight",
            }

        except Exception as e:
            logger.error(f"統計取得エラー: {e}")
            return {}


# 互換性関数
def setup(*args, **kwargs):
    """軽量版RAG Sage セットアップ"""
    logger.info("🔍 Lightweight RAG Sage setup実行")
    sage = LightweightRAGSage()
    sage.index_knowledge_base(max_files=50)  # 制限付きインデックス
    return sage


def main():
    """メイン実行関数"""
    logger.info("🔍 Lightweight RAG Sage 起動")

    sage = LightweightRAGSage()
    stats = sage.get_stats()
    logger.info(f"📊 統計: {stats}")

    # クリーンアップ
    sage.cleanup()
    logger.info("🏁 完了")


if __name__ == "__main__":
    main()
