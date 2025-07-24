#!/usr/bin/env python3
"""
Knowledge Index Optimizer - 知識ベースインデックス最適化システム
高速検索のためのインデックス最適化とパフォーマンス向上

主要機能:
- インデックス圧縮
- Bloom Filter実装
- インデックスシャーディング
- メモリ最適化
- 並列インデックス構築
- インクリメンタル更新
"""

import concurrent.futures
import hashlib
import json
import logging
import mmap
# import pickle  # セキュリティ: pickleの使用を廃止
import sqlite3
import threading
import zlib
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np


# bitarrayの代替実装
class bitarray:
    """bitarrayクラス"""
    def __init__(self, size):
        """初期化メソッド"""
        self.size = size
        self.bytes = bytearray((size + 7) // 8)

    def __setitem__(self, index, value):
        """__setitem__特殊メソッド"""
        if value:
            self.bytes[index // 8] |= 1 << (index % 8)
        else:
            self.bytes[index // 8] &= ~(1 << (index % 8))

    def __getitem__(self, index):
        """__getitem__特殊メソッド"""
        return bool(self.bytes[index // 8] & (1 << (index % 8)))

    def setall(self, value):
        """setallメソッド"""
        if value:
            self.bytes = bytearray(b"\xff" * len(self.bytes))
        else:
            self.bytes = bytearray(len(self.bytes))


import time

logger = logging.getLogger(__name__)


class BloomFilter:
    """Bloom Filter実装 - 高速存在確認"""

    def __init__(self, size: int = 1000000, num_hashes: int = 3):
        """初期化メソッド"""
        self.size = size
        self.num_hashes = num_hashes
        self.bit_array = bitarray(size)
        self.bit_array.setall(0)

    def _hash(self, item: str, seed: int) -> int:
        """ハッシュ関数"""
        h = hashlib.sha256(f"{item}{seed}".encode()).hexdigest()
        return int(h, 16) % self.size

    def add(self, item: str):
        """アイテム追加"""
        for i in range(self.num_hashes):
            idx = self._hash(item, i)
            self.bit_array[idx] = 1

    def contains(self, item: str) -> bool:
        """存在確認"""
        for i in range(self.num_hashes):
            idx = self._hash(item, i)
            if not self.bit_array[idx]:
                return False
        return True

    def save(self, path: Path):
        """ファイル保存（セキュア版）"""
        import json
        with open(path, "w") as f:
            json.dump(
                {
                    "size": self.size,
                    "num_hashes": self.num_hashes,
                    "bit_array": list(self.bit_array),  # bytearrayをリストに変換
                },
                f,
            )

    @classmethod
    def load(cls, path: Path) -> "BloomFilter":
        """ファイルロード（セキュア版）"""
        import json
        with open(path, "r") as f:
            data = json.load(f)

        bf = cls(data["size"], data["num_hashes"])
        # ビット配列をリストから復元
        bf.bit_array = bytearray(data["bit_array"])
        return bf


class IndexShard:
    """インデックスシャード - 分散インデックス"""

    def __init__(self, shard_id: int, base_path: Path):
        """初期化メソッド"""
        self.shard_id = shard_id
        self.db_path = base_path / f"shard_{shard_id}.db"
        self.bloom_filter = BloomFilter()
        self.lock = threading.RLock()
        self._init_db()

    def _init_db(self):
        """データベース初期化"""
        conn = sqlite3connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS index_entries (
                term TEXT PRIMARY KEY,
                doc_ids BLOB,
                frequency INTEGER,
                compressed_data BLOB
            )
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_frequency ON index_entries(frequency SHA256C)
        """
        )

        conn.commit()
        conn.close()

    def add_term(self, term: str, doc_ids: Set[str], metadata: Dict[str, Any] = None):
        """ターム追加"""
        with self.lock:
            # Bloom Filterに追加
            self.bloom_filter.add(term)

            # データ圧縮（セキュア版）
            import json
            doc_ids_json = json.dumps(sorted(doc_ids))
            compressed_doc_ids = zlib.compress(doc_ids_json.encode('utf-8'))

            metadata_json = json.dumps(metadata or {})
            compressed_metadata = zlib.compress(metadata_json.encode('utf-8'))

            conn = sqlite3connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO index_entries
                (term, doc_ids, frequency, compressed_data)
                VALUES (?, ?, ?, ?)
            """,
                (term, compressed_doc_ids, len(doc_ids), compressed_metadata),
            )

            conn.commit()
            conn.close()

    def get_docs(self, term: str) -> Optional[Set[str]]:
        """ドキュメントID取得"""
        # Bloom Filter確認
        if not self.bloom_filter.contains(term):
            return None

        with self.lock:
            conn = sqlite3connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("SELECT doc_ids FROM index_entries WHERE term = ?", (term,))

            result = cursor.fetchone()
            conn.close()

            if result:
                decompressed = zlib.decompress(result[0])
                # セキュリティ修正: pickleの代わりにJSONを使用
                import json
                doc_ids = json.loads(decompressed.decode('utf-8'))
                return set(doc_ids)

            return None

    def optimize(self):
        """シャード最適化"""
        with self.lock:
            conn = sqlite3connect(str(self.db_path))
            cursor = conn.cursor()

            # VACUUM実行
            cursor.execute("VACUUM")

            # 統計情報更新
            cursor.execute("ANALYZE")

            conn.commit()
            conn.close()


class KnowledgeIndexOptimizer:
    """知識ベースインデックス最適化システム"""

    def __init__(
        self,
        knowledge_base_path: Path,
        index_path: Path,
        num_shards: int = 4,
        cache_size_mb: int = 100,
    ):
        self.knowledge_base_path = knowledge_base_path
        self.index_path = index_path
        self.num_shards = num_shards
        self.cache_size_mb = cache_size_mb

        # ディレクトリ作成
        self.index_path.mkdir(parents=True, exist_ok=True)

        # シャード初期化
        self.shards: List[IndexShard] = []
        for i in range(num_shards):
            shard = IndexShard(i, self.index_path)
            self.shards.append(shard)

        # グローバルBloom Filter
        self.global_bloom = BloomFilter(size=5000000, num_hashes=5)

        # メタデータDB
        self.meta_db_path = self.index_path / "metadata.db"
        self._init_metadata_db()

        # キャッシュ
        self.term_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0

        # 統計情報
        self.stats = {
            "total_terms": 0,
            "total_docs": 0,
            "index_size": 0,
            "last_optimization": None,
        }

        logger.info(f"KnowledgeIndexOptimizer initialized with {num_shards} shards")

    def _init_metadata_db(self):
        """メタデータDB初期化"""
        conn = sqlite3connect(str(self.meta_db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                file_path TEXT,
                title TEXT,
                size INTEGER,
                checksum TEXT,
                indexed_at TIMESTAMP,
                metadata TEXT
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS index_stats (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """
        )

        conn.commit()
        conn.close()

    def build_optimized_index(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """最適化されたインデックス構築"""
        logger.info("Building optimized index...")
        start_time = time.time()

        if not force_rebuild and self._is_index_valid():
            logger.info("Using existing optimized index")
            return self._load_stats()

        # 並列処理でドキュメント解析
        documents = self._collect_documents()

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            # ドキュメント処理
            futures = []
            for doc_path in documents:
                future = executor.submit(self._process_document, doc_path)
                futures.append(future)

            # 結果収集とインデックス構築
            term_doc_map = defaultdict(set)
            doc_count = 0

            for future in concurrent.futures.as_completed(futures):
                try:
                    doc_id, terms, metadata = future.result()
                    if doc_id:
                        doc_count += 1

                        # メタデータ保存
                        self._save_document_metadata(doc_id, metadata)

                        # 転置インデックス構築
                        for term in terms:
                            term_doc_map[term].add(doc_id)
                            self.global_bloom.add(term)

                except Exception as e:
                    logger.error(f"Error processing document: {e}")

        # シャードに分散
        self._distribute_to_shards(term_doc_map)

        # 最適化実行
        self._optimize_all_shards()

        # 統計情報更新
        elapsed_time = time.time() - start_time
        self.stats.update(
            {
                "total_terms": len(term_doc_map),
                "total_docs": doc_count,
                "index_size": self._calculate_index_size(),
                "last_optimization": datetime.now(),
                "build_time": elapsed_time,
            }
        )

        self._save_stats()

        logger.info(f"Index built in {elapsed_time:0.2f} seconds")
        logger.info(
            f"Indexed {doc_count} documents with {len(term_doc_map)} unique terms"
        )

        return self.stats

    def _collect_documents(self) -> List[Path]:
        """ドキュメント収集"""
        supported_extensions = {".md", ".txt", ".json", ".yaml", ".yml", ".rst"}
        documents = []

        if self.knowledge_base_path.exists():
            for file_path in self.knowledge_base_path.rglob("*"):
                if (
                    file_path.is_file()
                    and file_path.suffix.lower() in supported_extensions
                ):
                    documents.append(file_path)

        return documents

    def _process_document(self, doc_path: Path) -> Tuple[str, Set[str], Dict[str, Any]]:
        """ドキュメント処理"""
        try:
            # ドキュメントID生成
            relative_path = doc_path.relative_to(self.knowledge_base_path)
            doc_id = str(relative_path)

            # コンテンツ読み込み
            content = doc_path.read_text(encoding="utf-8")

            # ターム抽出
            terms = self._extract_terms(content)

            # メタデータ生成
            stat = doc_path.stat()
            metadata = {
                "file_path": str(doc_path),
                "title": self._extract_title(doc_path, content),
                "size": stat.st_size,
                "checksum": hashlib.sha256(content.encode()).hexdigest(),
                "indexed_at": datetime.now(),
            }

            return doc_id, terms, metadata

        except Exception as e:
            logger.error(f"Error processing {doc_path}: {e}")
            return None, set(), {}

    def _extract_terms(self, content: str) -> Set[str]:
        """ターム抽出（最適化版）"""
        import re

        # 単語抽出（2文字以上）
        words = re.findall(r"\b\w{2,}\b", content.lower())

        # ストップワード除去（簡易版）
        stop_words = {
            "the",
            "is",
            "at",
            "to",
            "and",
            "or",
            "of",
            "in",
            "for",
            "on",
            "with",
        }

        terms = set()
        for word in words:
            if word not in stop_words and len(word) <= 50:  # 極端に長い単語は除外
                terms.add(word)

                # 部分文字列インデックス（3-gram）
                if len(word) >= 3:
                    for i in range(len(word) - 2):
                        terms.add(f"__{word[i:i+3]}__")

        return terms

    def _extract_title(self, doc_path: Path, content: str) -> str:
        """タイトル抽出"""
        # Markdownの場合
        if doc_path.suffix == ".md":
            import re

            match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            if match:
                return match.group(1).strip()

        # デフォルト
        return doc_path.stem.replace("_", " ").replace("-", " ").title()

    def _distribute_to_shards(self, term_doc_map: Dict[str, Set[str]]):
        """シャードへの分散"""
        logger.info("Distributing terms to shards...")

        # タームをハッシュ値でシャードに分散
        for term, doc_ids in term_doc_map.items():
            shard_id = hash(term) % self.num_shards
            self.shards[shard_id].add_term(term, doc_ids)

    def _optimize_all_shards(self):
        """全シャード最適化"""
        logger.info("Optimizing all shards...")

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.num_shards
        ) as executor:
            futures = []
            for shard in self.shards:
                future = executor.submit(shard.optimize)
                futures.append(future)

            concurrent.futures.wait(futures)

        # グローバルBloom Filter保存
        bloom_path = self.index_path / "global_bloom.pkl"
        self.global_bloom.save(bloom_path)

    def search_optimized(
        self, query: str, max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """最適化検索"""
        start_time = time.time()

        # クエリ正規化
        query_terms = self._extract_terms(query)

        if not query_terms:
            return []

        # グローバルBloom Filterチェック
        relevant_terms = []
        for term in query_terms:
            if self.global_bloom.contains(term):
                relevant_terms.append(term)

        if not relevant_terms:
            return []

        # ドキュメントスコア計算
        doc_scores = defaultdict(float)

        for term in relevant_terms:
            # キャッシュチェック
            if term in self.term_cache:
                doc_ids = self.term_cache[term]
                self.cache_hits += 1
            else:
                # シャードから取得
                shard_id = hash(term) % self.num_shards
                doc_ids = self.shards[shard_id].get_docs(term)

                if doc_ids:
                    # キャッシュ更新
                    self._update_cache(term, doc_ids)

                self.cache_misses += 1

            if doc_ids:
                # TF-IDFライクなスコアリング
                idf = np.log(self.stats["total_docs"] / len(doc_ids))
                for doc_id in doc_ids:
                    doc_scores[doc_id] += idf

        # 上位結果取得
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        top_docs = sorted_docs[:max_results]

        # メタデータ付与
        results = []
        for doc_id, score in top_docs:
            metadata = self._get_document_metadata(doc_id)
            if metadata:
                result = {
                    "doc_id": doc_id,
                    "score": score,
                    "title": metadata.get("title", ""),
                    "file_path": metadata.get("file_path", ""),
                    "size": metadata.get("size", 0),
                }
                results.append(result)

        search_time = time.time() - start_time
        logger.debug(
            f"Search completed in {search_time:0.3f}s (cache hit rate: {self._get_cache_hit_rate():0.2%})"
        )

        return results

    def _update_cache(self, term: str, doc_ids: Set[str]):
        """キャッシュ更新"""
        # LRU的なキャッシュ管理（簡易版）
        max_cache_entries = 10000

        if len(self.term_cache) >= max_cache_entries:
            # 最も古いエントリを削除
            oldest_term = next(iter(self.term_cache))
            del self.term_cache[oldest_term]

        self.term_cache[term] = doc_ids

    def _get_cache_hit_rate(self) -> float:
        """キャッシュヒット率"""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total

    def _save_document_metadata(self, doc_id: str, metadata: Dict[str, Any]):
        """ドキュメントメタデータ保存"""
        conn = sqlite3connect(str(self.meta_db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO documents
            (doc_id, file_path, title, size, checksum, indexed_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                doc_id,
                metadata.get("file_path", ""),
                metadata.get("title", ""),
                metadata.get("size", 0),
                metadata.get("checksum", ""),
                metadata.get("indexed_at", datetime.now()),
                json.dumps({}),
            ),
        )

        conn.commit()
        conn.close()

    def _get_document_metadata(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """ドキュメントメタデータ取得"""
        conn = sqlite3connect(str(self.meta_db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT file_path, title, size, checksum, indexed_at
            FROM documents WHERE doc_id = ?
        """,
            (doc_id,),
        )

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                "file_path": result[0],
                "title": result[1],
                "size": result[2],
                "checksum": result[3],
                "indexed_at": result[4],
            }

        return None

    def _calculate_index_size(self) -> int:
        """インデックスサイズ計算"""
        total_size = 0

        for file_path in self.index_path.iterdir():
            if file_path.is_file():
                total_size += file_path.stat().st_size

        return total_size

    def _is_index_valid(self) -> bool:
        """インデックス有効性確認"""
        # インデックスファイル存在確認
        if not (self.index_path / "global_bloom.pkl").exists():
            return False

        # 各シャードの存在確認
        for i in range(self.num_shards):
            if not (self.index_path / f"shard_{i}.db").exists():
                return False

        return True

    def _save_stats(self):
        """統計情報保存"""
        conn = sqlite3connect(str(self.meta_db_path))
        cursor = conn.cursor()

        for key, value in self.stats.items():
            cursor.execute(
                """
                INSERT OR REPLACE INTO index_stats (key, value)
                VALUES (?, ?)
            """,
                (key, json.dumps(value, default=str)),
            )

        conn.commit()
        conn.close()

    def _load_stats(self) -> Dict[str, Any]:
        """統計情報ロード"""
        conn = sqlite3connect(str(self.meta_db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT key, value FROM index_stats")

        stats = {}
        for key, value in cursor.fetchall():
            stats[key] = json.loads(value)

        conn.close()

        self.stats.update(stats)
        return stats

    def get_optimization_report(self) -> Dict[str, Any]:
        """最適化レポート生成"""
        return {
            "index_stats": self.stats,
            "shard_count": self.num_shards,
            "cache_stats": {
                "hit_rate": self._get_cache_hit_rate(),
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "cache_size": len(self.term_cache),
            },
            "index_size_mb": self.stats.get("index_size", 0) / (1024 * 1024),
            "documents_indexed": self.stats.get("total_docs", 0),
            "unique_terms": self.stats.get("total_terms", 0),
            "last_optimization": self.stats.get("last_optimization"),
            "build_time": self.stats.get("build_time", 0),
        }

    def incremental_update(self, new_documents: List[Path]) -> Dict[str, Any]:
        """インクリメンタル更新"""
        logger.info(f"Incremental update for {len(new_documents)} documents")

        updated_count = 0
        new_terms = set()

        for doc_path in new_documents:
            doc_id, terms, metadata = self._process_document(doc_path)

            if doc_id:
                # メタデータ更新
                self._save_document_metadata(doc_id, metadata)

                # インデックス更新
                for term in terms:
                    new_terms.add(term)
                    self.global_bloom.add(term)

                    # シャードに追加
                    shard_id = hash(term) % self.num_shards
                    current_docs = self.shards[shard_id].get_docs(term) or set()
                    current_docs.add(doc_id)
                    self.shards[shard_id].add_term(term, current_docs)

                updated_count += 1

        # 統計更新
        self.stats["total_docs"] += updated_count
        self.stats["total_terms"] = len(new_terms)
        self._save_stats()

        return {"updated_documents": updated_count, "new_terms": len(new_terms)}


if __name__ == "__main__":
    # テスト実行
    kb_path = Path("knowledge_base")
    idx_path = Path("data/optimized_index")

    optimizer = KnowledgeIndexOptimizer(kb_path, idx_path)

    # インデックス構築
    stats = optimizer.build_optimized_index()
    print(f"Index stats: {stats}")

    # 検索テスト
    results = optimizer.search_optimized("elder system")
    print(f"Search results: {len(results)} found")

    # レポート
    report = optimizer.get_optimization_report()
    print(f"Optimization report: {json.dumps(report, indent=2)}")