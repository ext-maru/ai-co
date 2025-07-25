"""
Elders Guild Vector Search Engine - pgvector統合セマンティック検索
Created: 2025-07-11
Author: Claude Elder
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import json
import numpy as np
from enum import Enum
import hashlib

import openai
from sentence_transformers import SentenceTransformer
import asyncpg
from pgvector.asyncpg import register_vector

from .elders_guild_db_manager import (
    EldersGuildDatabaseManager,
    KnowledgeEntity,
    DatabaseConfig,
)

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================


class EmbeddingProvider(Enum):
    """埋め込みプロバイダー"""

    OPENAI = "openai"
    SENTENCE_TRANSFORMERS = "sentence_transformers"
    HUGGING_FACE = "hugging_face"


@dataclass
class VectorSearchConfig:
    """ベクター検索設定"""

    embedding_provider: EmbeddingProvider = EmbeddingProvider.OPENAI
    embedding_model: str = "text-embedding-ada-002"
    embedding_dimension: int = 1536

    # Search parameters
    similarity_threshold: float = 0.8
    max_results: int = 10

    # Index parameters
    ivfflat_lists: int = 1000
    hnsw_m: int = 16
    hnsw_ef_construction: int = 64

    # Performance parameters
    batch_size: int = 100
    cache_embeddings: bool = True

    # OpenAI settings
    openai_api_key: Optional[str] = None
    openai_organization: Optional[str] = None

    # Sentence Transformers settings
    sentence_transformer_model: str = "all-MiniLM-L6-v2"
    sentence_transformer_device: str = "cpu"


# ============================================================================
# Embedding Generators
# ============================================================================


class EmbeddingGenerator:
    """埋め込みベクター生成基底クラス"""

    def __init__(self, config: VectorSearchConfig):
        """初期化メソッド"""
        self.config = config

    async def generate_embedding(self, text: str) -> np.ndarray:
        """テキストから埋め込みベクターを生成"""
        raise NotImplementedError

    async def generate_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """バッチでの埋め込みベクター生成"""
        embeddings = []
        for text in texts:
            embedding = await self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings


class OpenAIEmbeddingGenerator(EmbeddingGenerator):
    """OpenAI埋め込み生成器"""

    def __init__(self, config: VectorSearchConfig):
        """初期化メソッド"""
        super().__init__(config)
        if config.openai_api_key:
            openai.api_key = config.openai_api_key
        if config.openai_organization:
            openai.organization = config.openai_organization

    async def generate_embedding(self, text: str) -> np.ndarray:
        """OpenAI APIを使用した埋め込み生成"""
        try:
            response = await openai.Embedding.acreate(
                model=self.config.embedding_model, input=text
            )
            embedding = np.array(response["data"][0]["embedding"])
            return embedding
        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {e}")
            raise

    async def generate_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """OpenAI APIを使用したバッチ埋め込み生成"""
        try:
            response = await openai.Embedding.acreate(
                model=self.config.embedding_model, input=texts
            )
            embeddings = []
            for item in response["data"]:
                embedding = np.array(item["embedding"])
                embeddings.append(embedding)
            return embeddings
        except Exception as e:
            logger.error(f"OpenAI batch embedding generation failed: {e}")
            raise


class SentenceTransformerEmbeddingGenerator(EmbeddingGenerator):
    """Sentence Transformers埋め込み生成器"""

    def __init__(self, config: VectorSearchConfig):
        """初期化メソッド"""
        super().__init__(config)
        self.model = SentenceTransformer(
            config.sentence_transformer_model, device=config.sentence_transformer_device
        )

    async def generate_embedding(self, text: str) -> np.ndarray:
        """Sentence Transformersを使用した埋め込み生成"""
        try:
            embedding = self.model.encode(text)
            return np.array(embedding)
        except Exception as e:
            logger.error(f"Sentence Transformer embedding generation failed: {e}")
            raise

    async def generate_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Sentence Transformersを使用したバッチ埋め込み生成"""
        try:
            embeddings = self.model.encode(texts)
            return [np.array(embedding) for embedding in embeddings]
        except Exception as e:
            logger.error(f"Sentence Transformer batch embedding generation failed: {e}")
            raise


# ============================================================================
# Vector Search Engine
# ============================================================================


@dataclass
class SearchResult:
    """検索結果データクラス"""

    knowledge: KnowledgeEntity
    similarity_score: float
    search_method: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class VectorSearchEngine:
    """ベクター検索エンジン"""

    def __init__(
        self, config: VectorSearchConfig, db_manager: EldersGuildDatabaseManager
    ):
        self.config = config
        self.db_manager = db_manager
        self.embedding_generator = self._create_embedding_generator()
        self.embedding_cache = {}

    def _create_embedding_generator(self) -> EmbeddingGenerator:
        """埋め込み生成器の作成"""
        if self.config.embedding_provider == EmbeddingProvider.OPENAI:
            return OpenAIEmbeddingGenerator(self.config)
        elif self.config.embedding_provider == EmbeddingProvider.SENTENCE_TRANSFORMERS:
            return SentenceTransformerEmbeddingGenerator(self.config)
        else:
            raise ValueError(
                f"Unsupported embedding provider: {self.config.embedding_provider}"
            )

    async def initialize(self):
        """検索エンジンの初期化"""
        await self.db_manager.initialize()
        await self._create_vector_indexes()
        logger.info("Vector search engine initialized")

    async def _create_vector_indexes(self):
        """ベクターインデックスの作成・最適化"""
        async with self.db_manager.db_manager.get_connection() as conn:
            # HNSW インデックスの作成（より高速）
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_knowledge_embedding_hnsw
                ON knowledge_sage.knowledge_entities
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = $1, ef_construction = $2)
            """,
                self.config.hnsw_m,
                self.config.hnsw_ef_construction,
            )

            # IVFFlat インデックスの作成（メモリ効率）
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_knowledge_embedding_ivfflat
                ON knowledge_sage.knowledge_entities
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = $1)
            """,
                self.config.ivfflat_lists,
            )

            # RAG文書用インデックス
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_documents_embedding_hnsw
                ON rag_sage.documents
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = $1, ef_construction = $2)
            """,
                self.config.hnsw_m,
                self.config.hnsw_ef_construction,
            )

            logger.info("Vector indexes created/updated")

    async def semantic_search(
        self,
        query: str,
        similarity_threshold: Optional[float] = None,
        max_results: Optional[int] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """セマンティック検索"""
        similarity_threshold = similarity_threshold or self.config.similarity_threshold
        max_results = max_results or self.config.max_results

        # クエリ埋め込み生成
        query_embedding = await self._get_or_generate_embedding(query)

        # データベース検索
        results = await self._search_database(
            query_embedding,
            similarity_threshold,
            max_results,
            category,
            tags,
            metadata_filter,
        )

        return results

    async def _get_or_generate_embedding(self, text: str) -> np.ndarray:
        """埋め込みの取得または生成（キャッシュ付き）"""
        if not self.config.cache_embeddings:
            return await self.embedding_generator.generate_embedding(text)

        # キャッシュキー生成
        cache_key = hashlib.md5(text.encode()).hexdigest()

        # キャッシュから取得
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]

        # Redisキャッシュから取得
        if self.db_manager.db_manager.redis_client:
            cached_embedding = await self.db_manager.db_manager.redis_client.get(
                f"embedding:{cache_key}"
            )
            if cached_embedding:
                embedding = np.frombuffer(
                    bytes.fromhex(cached_embedding), dtype=np.float32
                )
                self.embedding_cache[cache_key] = embedding
                return embedding

        # 埋め込み生成
        embedding = await self.embedding_generator.generate_embedding(text)

        # キャッシュに保存
        self.embedding_cache[cache_key] = embedding

        if self.db_manager.db_manager.redis_client:
            embedding_hex = embedding.astype(np.float32).tobytes().hex()
            await self.db_manager.db_manager.redis_client.setex(
                f"embedding:{cache_key}", 3600, embedding_hex  # 1 hour TTL
            )

        return embedding

    async def _search_database(
        self,
        query_embedding: np.ndarray,
        similarity_threshold: float,
        max_results: int,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """データベースでのベクター検索"""
        async with self.db_manager.db_manager.get_connection() as conn:
            # 基本クエリ
            base_query = """
                SELECT id, title, content, content_type, embedding, metadata, category, tags,
                       quality_score, parent_id, created_at, updated_at, created_by, updated_by,
                       version, access_count, last_accessed,
                       1 - (embedding <=> $1) as similarity_score
                FROM knowledge_sage.knowledge_entities
                WHERE embedding IS NOT NULL
                AND 1 - (embedding <=> $1) > $2
            """

            params = [query_embedding.tolist(), similarity_threshold]
            param_count = 3

            # フィルター条件の追加
            conditions = []

            if category:
                conditions.append(f"category = ${param_count}")
                params.append(category)
                param_count += 1

            if tags:
                conditions.append(f"tags && ${param_count}")
                params.append(tags)
                param_count += 1

            if metadata_filter:
                conditions.append(f"metadata @> ${param_count}")
                params.append(json.dumps(metadata_filter))
                param_count += 1

            # 条件の結合
            if conditions:
                base_query += " AND " + " AND ".join(conditions)

            # 順序とリミット
            base_query += f" ORDER BY embedding <=> $1 LIMIT ${param_count}"
            params.append(max_results)

            # クエリ実行
            results = await conn.fetch(base_query, *params)

            # 結果の変換
            search_results = []
            for result in results:
                knowledge = KnowledgeEntity(
                    id=str(result["id"]),
                    title=result["title"],
                    content=result["content"],
                    content_type=result["content_type"],
                    embedding=(
                        np.array(result["embedding"]) if result["embedding"] else None
                    ),
                    metadata=(
                        json.loads(result["metadata"]) if result["metadata"] else {}
                    ),
                    category=result["category"],
                    tags=result["tags"] or [],
                    quality_score=result["quality_score"],
                    parent_id=str(result["parent_id"]) if result["parent_id"] else None,
                    created_at=result["created_at"],
                    updated_at=result["updated_at"],
                    created_by=result["created_by"],
                    updated_by=result["updated_by"],
                    version=result["version"],
                    access_count=result["access_count"],
                    last_accessed=result["last_accessed"],
                )

                search_result = SearchResult(
                    knowledge=knowledge,
                    similarity_score=float(result["similarity_score"]),
                    search_method="vector_cosine",
                    metadata={
                        "query_embedding_size": len(query_embedding),
                        "similarity_threshold": similarity_threshold,
                        "category_filter": category,
                        "tags_filter": tags,
                        "metadata_filter": metadata_filter,
                    },
                )
                search_results.append(search_result)

            return search_results

    async def hybrid_search(
        self,
        query: str,
        semantic_weight: float = 0.7,
        fulltext_weight: float = 0.3,
        max_results: Optional[int] = None,
    ) -> List[SearchResult]:
        """ハイブリッド検索（セマンティック + 全文検索）"""
        max_results = max_results or self.config.max_results

        # セマンティック検索
        semantic_results = await self.semantic_search(
            query, max_results=max_results * 2  # より多くの結果を取得
        )

        # 全文検索
        fulltext_results = await self.db_manager.knowledge_sage.fulltext_search(
            query, max_results=max_results * 2
        )

        # 結果の統合とスコア計算
        combined_results = await self._combine_search_results(
            semantic_results, fulltext_results, semantic_weight, fulltext_weight
        )

        # 結果を制限
        return combined_results[:max_results]

    async def _combine_search_results(
        self,
        semantic_results: List[SearchResult],
        fulltext_results: List[KnowledgeEntity],
        semantic_weight: float,
        fulltext_weight: float,
    ) -> List[SearchResult]:
        """検索結果の統合"""
        # セマンティック検索結果をIDでマップ
        semantic_map = {result.knowledge.id: result for result in semantic_results}

        # 全文検索結果をIDでマップ
        fulltext_map = {entity.id: entity for entity in fulltext_results}

        # 統合結果
        combined_results = []
        processed_ids = set()

        # セマンティック検索結果の処理
        for result in semantic_results:
            if result.knowledge.id in processed_ids:
                continue

            semantic_score = result.similarity_score
            fulltext_score = 0.5  # デフォルトスコア

            # 全文検索結果に含まれている場合、スコアを上げる
            if result.knowledge.id in fulltext_map:
                fulltext_score = 1.0

            # 統合スコア計算
            combined_score = (
                semantic_score * semantic_weight + fulltext_score * fulltext_weight
            )

            combined_result = SearchResult(
                knowledge=result.knowledge,
                similarity_score=combined_score,
                search_method="hybrid",
                metadata={
                    "semantic_score": semantic_score,
                    "fulltext_score": fulltext_score,
                    "semantic_weight": semantic_weight,
                    "fulltext_weight": fulltext_weight,
                },
            )
            combined_results.append(combined_result)
            processed_ids.add(result.knowledge.id)

        # 全文検索のみの結果を追加
        for entity in fulltext_results:
            if entity.id in processed_ids:
                continue

            semantic_score = 0.0  # セマンティックスコアなし
            fulltext_score = 1.0

            combined_score = (
                semantic_score * semantic_weight + fulltext_score * fulltext_weight
            )

            combined_result = SearchResult(
                knowledge=entity,
                similarity_score=combined_score,
                search_method="hybrid",
                metadata={
                    "semantic_score": semantic_score,
                    "fulltext_score": fulltext_score,
                    "semantic_weight": semantic_weight,
                    "fulltext_weight": fulltext_weight,
                },
            )
            combined_results.append(combined_result)
            processed_ids.add(entity.id)

        # スコアでソート
        combined_results.sort(key=lambda x: x.similarity_score, reverse=True)

        return combined_results

    async def add_knowledge_with_embedding(self, knowledge: KnowledgeEntity) -> str:
        """埋め込み付きで知識を追加"""
        if knowledge.embedding is None:
            # 埋め込み生成
            text_to_embed = f"{knowledge.title}\n{knowledge.content}"
            knowledge.embedding = await self._get_or_generate_embedding(text_to_embed)

        # 知識の追加
        knowledge_id = await self.db_manager.knowledge_sage.create_knowledge(knowledge)

        logger.info(f"Added knowledge with embedding: {knowledge_id}")
        return knowledge_id

    async def batch_add_knowledge(
        self, knowledge_list: List[KnowledgeEntity]
    ) -> List[str]:
        """バッチで知識を追加"""
        # 埋め込み生成するテキストを収集
        texts_to_embed = []
        for knowledge in knowledge_list:
            if knowledge.embedding is None:
                text_to_embed = f"{knowledge.title}\n{knowledge.content}"
                texts_to_embed.append(text_to_embed)
            else:
                texts_to_embed.append(None)

        # バッチで埋め込み生成
        embeddings = await self.embedding_generator.generate_embeddings_batch(
            [text for text in texts_to_embed if text is not None]
        )

        # 埋め込みを知識に設定
        embedding_idx = 0
        for i, knowledge in enumerate(knowledge_list):
            if texts_to_embed[i] is not None:
                knowledge.embedding = embeddings[embedding_idx]
                embedding_idx += 1

        # バッチで知識を追加
        knowledge_ids = []
        for knowledge in knowledge_list:
            knowledge_id = await self.db_manager.knowledge_sage.create_knowledge(
                knowledge
            )
            knowledge_ids.append(knowledge_id)

        logger.info(f"Added {len(knowledge_ids)} knowledge items with embeddings")
        return knowledge_ids

    async def reindex_embeddings(self):
        """全埋め込みの再インデックス"""
        async with self.db_manager.db_manager.get_connection() as conn:
            # 埋め込みがない知識を取得
            query = """
                SELECT id, title, content
                FROM knowledge_sage.knowledge_entities
                WHERE embedding IS NULL
                ORDER BY created_at DESC
            """

            results = await conn.fetch(query)

            logger.info(f"Found {len(results)} knowledge items without embeddings")

            # バッチで埋め込み生成
            batch_size = self.config.batch_size
            for i in range(0, len(results), batch_size):
                batch = results[i : i + batch_size]

                # テキストの準備
                texts = [f"{row['title']}\n{row['content']}" for row in batch]

                # 埋め込み生成
                embeddings = await self.embedding_generator.generate_embeddings_batch(
                    texts
                )

                # データベース更新
                for j, row in enumerate(batch):
                    update_query = """
                        UPDATE knowledge_sage.knowledge_entities
                        SET embedding = $1
                        WHERE id = $2
                    """
                    await conn.execute(update_query, embeddings[j].tolist(), row["id"])

                logger.info(
                    f"Updated embeddings for batch {i//batch_size + 1}/{(len(results) + batch_size - 1)//batch_size}"
                )

        logger.info("Embedding reindexing completed")

    async def get_similar_knowledge(
        self, knowledge_id: str, max_results: int = 5
    ) -> List[SearchResult]:
        """類似知識の取得"""
        # 対象知識の取得
        knowledge = await self.db_manager.knowledge_sage.get_knowledge(knowledge_id)
        if not knowledge or knowledge.embedding is None:
            return []

        # 類似検索
        results = await self._search_database(
            knowledge.embedding,
            self.config.similarity_threshold,
            max_results + 1,  # 自分自身を除外するため+1
            knowledge.category,
        )

        # 自分自身を除外
        filtered_results = [
            result for result in results if result.knowledge.id != knowledge_id
        ]

        return filtered_results[:max_results]

    async def close(self):
        """リソースのクリーンアップ"""
        await self.db_manager.close()
        logger.info("Vector search engine closed")


# ============================================================================
# Usage Example
# ============================================================================


async def main():
    """使用例"""
    # 設定
    vector_config = VectorSearchConfig(
        embedding_provider=EmbeddingProvider.SENTENCE_TRANSFORMERS,
        sentence_transformer_model="all-MiniLM-L6-v2",
        similarity_threshold=0.7,
        max_results=10,
    )

    db_config = DatabaseConfig()
    db_manager = EldersGuildDatabaseManager(db_config)

    # 検索エンジンの初期化
    search_engine = VectorSearchEngine(vector_config, db_manager)

    try:
        await search_engine.initialize()

        # サンプル知識の追加
        knowledge = KnowledgeEntity(
            title="PostgreSQL最適化",
            content="PostgreSQLのパフォーマンス最適化には、適切なインデックスの設計が重要です。",
            category="database",
            tags=["postgresql", "optimization", "performance"],
            quality_score=0.9,
            created_by="Claude Elder",
        )

        knowledge_id = await search_engine.add_knowledge_with_embedding(knowledge)
        print(f"Added knowledge: {knowledge_id}")

        # セマンティック検索
        results = await search_engine.semantic_search("データベース最適化")
        print(f"Semantic search found {len(results)} results")

        for result in results:
            print(
                f"- {result.knowledge.title} (similarity: {result.similarity_score:0.3f})"
            )

        # ハイブリッド検索
        hybrid_results = await search_engine.hybrid_search("PostgreSQL パフォーマンス")
        print(f"Hybrid search found {len(hybrid_results)} results")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await search_engine.close()


if __name__ == "__main__":
    asyncio.run(main())
