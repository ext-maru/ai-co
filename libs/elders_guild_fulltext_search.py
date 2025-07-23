"""
Elders Guild Full-Text Search Engine - 日本語/英語対応高度全文検索
Created: 2025-07-11
Author: Claude Elder
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import json
import re
from enum import Enum
import unicodedata

import asyncpg
import MeCab
import sudachipy
from sudachipy import Dictionary, SplitMode

from .elders_guild_db_manager import (
    EldersGuildDatabaseManager,
    KnowledgeEntity,
    DatabaseConfig,
)

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================


class TextLanguage(Enum):
    """テキスト言語"""

    JAPANESE = "ja"
    ENGLISH = "en"
    AUTO = "auto"


class TokenizerType(Enum):
    """トークナイザータイプ"""

    MECAB = "mecab"
    SUDACHI = "sudachi"
    POSTGRESQL = "postgresql"


@dataclass
class FullTextSearchConfig:
    """全文検索設定"""

    # 基本設定
    default_language: TextLanguage = TextLanguage.AUTO
    japanese_tokenizer: TokenizerType = TokenizerType.SUDACHI

    # 検索パラメータ
    max_results: int = 20
    min_score: float = 0.1

    # 言語検出パラメータ
    japanese_char_threshold: float = 0.3
    hiragana_katakana_threshold: float = 0.1

    # トークナイザー設定
    mecab_dict_path: Optional[str] = None
    sudachi_mode: SplitMode = SplitMode.C

    # PostgreSQL全文検索設定
    japanese_config: str = "japanese"
    english_config: str = "english"

    # 検索重み付け
    title_weight: str = "A"
    content_weight: str = "B"

    # 高度な検索設定
    enable_fuzzy_search: bool = True
    fuzzy_threshold: float = 0.6
    enable_synonym_search: bool = False
    synonym_dict: Dict[str, List[str]] = field(default_factory=dict)

    # パフォーマンス設定
    cache_search_results: bool = True
    cache_ttl: int = 300  # 5分


# ============================================================================
# Language Detection
# ============================================================================


class LanguageDetector:
    """言語検出器"""

    def __init__(self, config: FullTextSearchConfig):
        """初期化メソッド"""
        self.config = config

    def detect_language(self, text: str) -> TextLanguage:
        """テキストの言語を検出"""
        if not text:
            return TextLanguage.ENGLISH

        # 日本語文字の検出
        japanese_chars = 0
        hiragana_katakana_chars = 0
        total_chars = 0

        for char in text:
            if unicodedata.category(char) in ["Lo", "Hiragana", "Katakana"]:
                total_chars += 1
                if unicodedata.name(char, "").startswith(("HIRAGANA", "KATAKANA")):
                    hiragana_katakana_chars += 1
                    japanese_chars += 1
                elif unicodedata.name(char, "").startswith("CJK"):
                    japanese_chars += 1
            elif unicodedata.category(char) in ["Lu", "Ll", "Nd"]:
                total_chars += 1

        if total_chars == 0:
            return TextLanguage.ENGLISH

        japanese_ratio = japanese_chars / total_chars
        hiragana_katakana_ratio = hiragana_katakana_chars / total_chars

        # 日本語判定
        if (
            japanese_ratio >= self.config.japanese_char_threshold
            or hiragana_katakana_ratio >= self.config.hiragana_katakana_threshold
        ):
            return TextLanguage.JAPANESE

        return TextLanguage.ENGLISH

    def is_mixed_language(self, text: str) -> bool:
        """混合言語テキストの判定"""
        if not text:
            return False

        has_japanese = False
        has_english = False

        for char in text:
            if unicodedata.name(char, "").startswith(("HIRAGANA", "KATAKANA", "CJK")):
                has_japanese = True
            elif unicodedata.category(char) in ["Lu", "Ll"]:
                has_english = True

            if has_japanese and has_english:
                return True

        return False


# ============================================================================
# Text Tokenizers
# ============================================================================


class JapaneseTokenizer:
    """日本語トークナイザー"""

    def __init__(self, config: FullTextSearchConfig):
        """初期化メソッド"""
        self.config = config
        self.mecab_tagger = None
        self.sudachi_tokenizer = None

        if config.japanese_tokenizer == TokenizerType.MECAB:
            self._init_mecab()
        elif config.japanese_tokenizer == TokenizerType.SUDACHI:
            self._init_sudachi()

    def _init_mecab(self):
        """MeCabの初期化"""
        try:
            if self.config.mecab_dict_path:
                self.mecab_tagger = MeCab.Tagger(f"-d {self.config.mecab_dict_path}")
            else:
                self.mecab_tagger = MeCab.Tagger()
        except Exception as e:
            logger.warning(f"MeCab initialization failed: {e}")

    def _init_sudachi(self):
        """SudachiPyの初期化"""
        try:
            dictionary = Dictionary()
            self.sudachi_tokenizer = dictionary.create()
        except Exception as e:
            logger.warning(f"SudachiPy initialization failed: {e}")

    def tokenize(self, text: str) -> List[str]:
        """日本語テキストのトークン化"""
        if not text:
            return []

        if self.config.japanese_tokenizer == TokenizerType.MECAB and self.mecab_tagger:
            return self._tokenize_with_mecab(text)
        elif (
            self.config.japanese_tokenizer == TokenizerType.SUDACHI
            and self.sudachi_tokenizer
        ):
            return self._tokenize_with_sudachi(text)
        else:
            # フォールバック: 簡単な分割
            return self._simple_tokenize(text)

    def _tokenize_with_mecab(self, text: str) -> List[str]:
        """MeCabでのトークン化"""
        try:
            parsed = self.mecab_tagger.parse(text)
            tokens = []

            for line in parsed.split("\n"):
                if line == "EOS" or line == "":
                    continue

                parts = line.split("\t")
                if len(parts) >= 2:
                    word = parts[0]
                    features = parts[1].split(",")

                    # 品詞フィルタリング
                    pos = features[0] if features else ""
                    if pos in ["名詞", "動詞", "形容詞", "副詞"]:
                        tokens.append(word)

            return tokens
        except Exception as e:
            logger.error(f"MeCab tokenization failed: {e}")
            return self._simple_tokenize(text)

    def _tokenize_with_sudachi(self, text: str) -> List[str]:
        """SudachiPyでのトークン化"""
        try:
            morphemes = self.sudachi_tokenizer.tokenize(text, self.config.sudachi_mode)
            tokens = []

            for morpheme in morphemes:
                # 品詞フィルタリング
                pos = morpheme.part_of_speech()[0]
                if pos in ["名詞", "動詞", "形容詞", "副詞"]:
                    # 正規化形を使用
                    normalized = morpheme.normalized_form()
                    if normalized and len(normalized) > 1:  # 1文字以上
                        tokens.append(normalized)

            return tokens
        except Exception as e:
            logger.error(f"SudachiPy tokenization failed: {e}")
            return self._simple_tokenize(text)

    def _simple_tokenize(self, text: str) -> List[str]:
        """簡単なトークン化（フォールバック）"""
        # 基本的な分割
        tokens = []

        # 英数字の分割
        words = re.findall(r"[a-zA-Z0-9]+", text)
        tokens.extend(words)

        # 日本語の文字単位分割（改良の余地あり）
        japanese_chars = re.findall(r"[ぁ-ん]+|[ァ-ヶ]+|[一-龯]+", text)
        tokens.extend(japanese_chars)

        return [token for token in tokens if len(token) > 1]


# ============================================================================
# Full-Text Search Engine
# ============================================================================


@dataclass
class FullTextSearchResult:
    """全文検索結果"""

    knowledge: KnowledgeEntity
    relevance_score: float
    matched_tokens: List[str]
    search_method: str
    language: TextLanguage
    metadata: Dict[str, Any] = field(default_factory=dict)


class FullTextSearchEngine:
    """全文検索エンジン"""

    def __init__(
        self, config: FullTextSearchConfig, db_manager: EldersGuildDatabaseManager
    ):
        self.config = config
        self.db_manager = db_manager
        self.language_detector = LanguageDetector(config)
        self.japanese_tokenizer = JapaneseTokenizer(config)
        self.search_cache = {}

    async def initialize(self):
        """検索エンジンの初期化"""
        await self.db_manager.initialize()
        await self._setup_fulltext_indexes()
        logger.info("Full-text search engine initialized")

    async def _setup_fulltext_indexes(self):
        """全文検索インデックスの設定"""
        async with self.db_manager.db_manager.get_connection() as conn:
            # 全文検索用の関数が存在することを確認
            await conn.execute(
                """
                CREATE OR REPLACE FUNCTION knowledge_sage.update_search_vector()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.search_vector :=
                        setweight(to_tsvector('japanese', COALESCE(NEW.title, '')), 'A') ||
                        setweight(to_tsvector('japanese', COALESCE(NEW.content, '')), 'B') ||
                        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
                        setweight(to_tsvector('english', COALESCE(NEW.content, '')), 'B');
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """
            )

            # トリガーの作成
            await conn.execute(
                """
                DROP TRIGGER IF EXISTS trigger_knowledge_search_vector ON knowledge_sage.knowledge_entities;
                CREATE TRIGGER trigger_knowledge_search_vector
                    BEFORE INSERT OR UPDATE ON knowledge_sage.knowledge_entities
                    FOR EACH ROW EXECUTE FUNCTION knowledge_sage.update_search_vector();
            """
            )

            # 既存データの検索ベクター更新
            await conn.execute(
                """
                UPDATE knowledge_sage.knowledge_entities
                SET search_vector =
                    setweight(to_tsvector('japanese', COALESCE(title, '')), 'A') ||
                    setweight(to_tsvector('japanese', COALESCE(content, '')), 'B') ||
                    setweight(to_tsvector('english', COALESCE(title, '')), 'A') ||
                    setweight(to_tsvector('english', COALESCE(content, '')), 'B')
                WHERE search_vector IS NULL;
            """
            )

            logger.info("Full-text search indexes updated")

    async def search(
        self,
        query: str,
        language: Optional[TextLanguage] = None,
        max_results: Optional[int] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[FullTextSearchResult]:
        """全文検索"""
        max_results = max_results or self.config.max_results
        language = language or self.config.default_language

        # 言語自動検出
        if language == TextLanguage.AUTO:
            language = self.language_detector.detect_language(query)

        # キャッシュチェック
        cache_key = self._generate_cache_key(
            query, language, max_results, category, tags, metadata_filter
        )
        if self.config.cache_search_results and cache_key in self.search_cache:
            cached_result = self.search_cache[cache_key]
            if (
                datetime.now() - cached_result["timestamp"]
            ).seconds < self.config.cache_ttl:
                return cached_result["results"]

        # 検索実行
        results = await self._execute_search(
            query, language, max_results, category, tags, metadata_filter
        )

        # キャッシュに保存
        if self.config.cache_search_results:
            self.search_cache[cache_key] = {
                "results": results,
                "timestamp": datetime.now(),
            }

        return results

    async def _execute_search(
        self,
        query: str,
        language: TextLanguage,
        max_results: int,
        category: Optional[str],
        tags: Optional[List[str]],
        metadata_filter: Optional[Dict[str, Any]],
    ) -> List[FullTextSearchResult]:
        """検索実行"""
        # 混合言語の場合は両方の言語で検索
        if self.language_detector.is_mixed_language(query):
            japanese_results = await self._search_by_language(
                query,
                TextLanguage.JAPANESE,
                max_results,
                category,
                tags,
                metadata_filter,
            )
            english_results = await self._search_by_language(
                query,
                TextLanguage.ENGLISH,
                max_results,
                category,
                tags,
                metadata_filter,
            )

            # 結果をマージ
            results = self._merge_results(japanese_results, english_results)
            return results[:max_results]
        else:
            return await self._search_by_language(
                query, language, max_results, category, tags, metadata_filter
            )

    async def _search_by_language(
        self,
        query: str,
        language: TextLanguage,
        max_results: int,
        category: Optional[str],
        tags: Optional[List[str]],
        metadata_filter: Optional[Dict[str, Any]],
    ) -> List[FullTextSearchResult]:
        """言語別検索"""
        async with self.db_manager.db_manager.get_connection() as conn:
            # 基本クエリ
            if language == TextLanguage.JAPANESE:
                search_config = self.config.japanese_config
            else:
                search_config = self.config.english_config

            base_query = f"""
                SELECT id, title, content, content_type, embedding, metadata, category, tags,
                       quality_score, parent_id, created_at, updated_at, created_by, updated_by,
                       version, access_count, last_accessed,
                       ts_rank(
                           search_vector,
                           plainto_tsquery('{search_config}', $1)
                       ) as relevance_score
                FROM knowledge_sage.knowledge_entities
                WHERE search_vector @@ plainto_tsquery('{search_config}', $1)
                AND ts_rank(search_vector, plainto_tsquery('{search_config}', $1)) > $2
            """

            params = [query, self.config.min_score]
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
            base_query += f" ORDER BY relevance_score DESC LIMIT ${param_count}"
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
                    embedding=result["embedding"],
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

                # マッチしたトークンの抽出
                matched_tokens = self._extract_matched_tokens(
                    query, knowledge, language
                )

                search_result = FullTextSearchResult(
                    knowledge=knowledge,
                    relevance_score=float(result["relevance_score"]),
                    matched_tokens=matched_tokens,
                    search_method=f"fulltext_{language.value}",
                    language=language,
                    metadata={
                        "query": query,
                        "search_config": search_config,
                        "min_score": self.config.min_score,
                        "category_filter": category,
                        "tags_filter": tags,
                        "metadata_filter": metadata_filter,
                    },
                )
                search_results.append(search_result)

            return search_results

    def _extract_matched_tokens(
        self, query: str, knowledge: KnowledgeEntity, language: TextLanguage
    ) -> List[str]:
        """マッチしたトークンの抽出"""
        if language == TextLanguage.JAPANESE:
            query_tokens = self.japanese_tokenizer.tokenize(query)
            title_tokens = self.japanese_tokenizer.tokenize(knowledge.title)
            content_tokens = self.japanese_tokenizer.tokenize(knowledge.content)
        else:
            # 英語の場合は単語分割
            query_tokens = query.lower().split()
            title_tokens = knowledge.title.lower().split()
            content_tokens = knowledge.content.lower().split()

        # マッチしたトークンを収集
        matched_tokens = []
        all_tokens = set(title_tokens + content_tokens)

        for query_token in query_tokens:
            for token in all_tokens:
                if query_token in token or token in query_token:
                    matched_tokens.append(token)

        return list(set(matched_tokens))

    def _merge_results(
        self,
        japanese_results: List[FullTextSearchResult],
        english_results: List[FullTextSearchResult],
    ) -> List[FullTextSearchResult]:
        """検索結果のマージ"""
        # IDでグループ化
        result_map = {}

        for result in japanese_results + english_results:
            knowledge_id = result.knowledge.id
            if knowledge_id not in result_map:
                result_map[knowledge_id] = result
            else:
                # より高いスコアを採用
                if result.relevance_score > result_map[knowledge_id].relevance_score:
                    result_map[knowledge_id] = result

        # スコアでソート
        merged_results = list(result_map.values())
        merged_results.sort(key=lambda x: x.relevance_score, reverse=True)

        return merged_results

    def _generate_cache_key(
        self,
        query: str,
        language: TextLanguage,
        max_results: int,
        category: Optional[str],
        tags: Optional[List[str]],
        metadata_filter: Optional[Dict[str, Any]],
    ) -> str:
        """キャッシュキーの生成"""
        import hashlib

        key_data = {
            "query": query,
            "language": language.value,
            "max_results": max_results,
            "category": category,
            "tags": sorted(tags) if tags else None,
            "metadata_filter": metadata_filter,
        }

        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    async def fuzzy_search(
        self, query: str, max_results: Optional[int] = None
    ) -> List[FullTextSearchResult]:
        """ファジー検索"""
        if not self.config.enable_fuzzy_search:
            return await self.search(query, max_results=max_results)

        max_results = max_results or self.config.max_results

        async with self.db_manager.db_manager.get_connection() as conn:
            # PostgreSQLの類似検索機能を使用
            fuzzy_query = f"""
                SELECT id, title, content, content_type, embedding, metadata, category, tags,
                       quality_score, parent_id, created_at, updated_at, created_by, updated_by,
                       version, access_count, last_accessed,
                       similarity(title, $1) as title_similarity,
                       similarity(content, $1) as content_similarity,
                       GREATEST(similarity(title, $1), similarity(content, $1)) as max_similarity
                FROM knowledge_sage.knowledge_entities
                WHERE similarity(title, $1) > $2 OR similarity(content, $1) > $2
                ORDER BY max_similarity DESC
                LIMIT $3
            """

            results = await conn.fetch(
                fuzzy_query, query, self.config.fuzzy_threshold, max_results
            )

            # 結果の変換
            search_results = []
            for result in results:
                knowledge = KnowledgeEntity(
                    id=str(result["id"]),
                    title=result["title"],
                    content=result["content"],
                    content_type=result["content_type"],
                    embedding=result["embedding"],
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

                search_result = FullTextSearchResult(
                    knowledge=knowledge,
                    relevance_score=float(result["max_similarity"]),
                    matched_tokens=[],
                    search_method="fuzzy_search",
                    language=self.language_detector.detect_language(query),
                    metadata={
                        "query": query,
                        "title_similarity": float(result["title_similarity"]),
                        "content_similarity": float(result["content_similarity"]),
                        "fuzzy_threshold": self.config.fuzzy_threshold,
                    },
                )
                search_results.append(search_result)

            return search_results

    async def advanced_search(
        self,
        query: str,
        search_fields: List[str] = None,
        boost_factors: Dict[str, float] = None,
        max_results: Optional[int] = None,
    ) -> List[FullTextSearchResult]:
        """高度な検索"""
        search_fields = search_fields or ["title", "content"]
        boost_factors = boost_factors or {"title": 2.0, "content": 1.0}
        max_results = max_results or self.config.max_results

        async with self.db_manager.db_manager.get_connection() as conn:
            # 動的にクエリを構築
            search_expressions = []

            for field in search_fields:
                if field in boost_factors:
                    boost = boost_factors[field]
                    if field == "title":
                        search_expressions.append(
                            f"ts_rank(search_vector, plainto_tsquery('japanese', $1)) * {boost}"
                        )
                        search_expressions.append(
                            f"ts_rank(search_vector, plainto_tsquery('english', $1)) * {boost}"
                        )
                    elif field == "content":
                        search_expressions.append(
                            f"ts_rank(search_vector, plainto_tsquery('japanese', $1)) * {boost}"
                        )
                        search_expressions.append(
                            f"ts_rank(search_vector, plainto_tsquery('english', $1)) * {boost}"
                        )

            if not search_expressions:
                return []

            combined_score = " + ".join(search_expressions)

            advanced_query = f"""
                SELECT id, title, content, content_type, embedding, metadata, category, tags,
                       quality_score, parent_id, created_at, updated_at, created_by, updated_by,
                       version, access_count, last_accessed,
                       ({combined_score}) as advanced_score
                FROM knowledge_sage.knowledge_entities
                WHERE search_vector @@ (plainto_tsquery(
                    'japanese',
                    $1) || plainto_tsquery('english',
                    $1)
                )
                AND ({combined_score}) > $2
                ORDER BY advanced_score DESC
                LIMIT $3
            """

            results = await conn.fetch(
                advanced_query, query, self.config.min_score, max_results
            )

            # 結果の変換
            search_results = []
            for result in results:
                knowledge = KnowledgeEntity(
                    id=str(result["id"]),
                    title=result["title"],
                    content=result["content"],
                    content_type=result["content_type"],
                    embedding=result["embedding"],
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

                search_result = FullTextSearchResult(
                    knowledge=knowledge,
                    relevance_score=float(result["advanced_score"]),
                    matched_tokens=[],
                    search_method="advanced_search",
                    language=self.language_detector.detect_language(query),
                    metadata={
                        "query": query,
                        "search_fields": search_fields,
                        "boost_factors": boost_factors,
                    },
                )
                search_results.append(search_result)

            return search_results

    async def reindex_all(self):
        """全インデックスの再構築"""
        async with self.db_manager.db_manager.get_connection() as conn:
            # 全レコードの検索ベクターを再構築
            await conn.execute(
                """
                UPDATE knowledge_sage.knowledge_entities
                SET search_vector =
                    setweight(to_tsvector('japanese', COALESCE(title, '')), 'A') ||
                    setweight(to_tsvector('japanese', COALESCE(content, '')), 'B') ||
                    setweight(to_tsvector('english', COALESCE(title, '')), 'A') ||
                    setweight(to_tsvector('english', COALESCE(content, '')), 'B')
            """
            )

            # キャッシュのクリア
            self.search_cache.clear()

            logger.info("Full-text search reindexing completed")

    async def get_search_statistics(self) -> Dict[str, Any]:
        """検索統計の取得"""
        async with self.db_manager.db_manager.get_connection() as conn:
            stats = {}

            # 総文書数
            total_docs = await conn.fetchval(
                "SELECT COUNT(*) FROM knowledge_sage.knowledge_entities"
            )
            stats["total_documents"] = total_docs

            # 検索ベクターが設定されている文書数
            indexed_docs = await conn.fetchval(
                "SELECT COUNT(*) FROM knowledge_sage.knowledge_entities WHERE search_vector " \
                    "IS NOT NULL"
            )
            stats["indexed_documents"] = indexed_docs

            # 言語別文書数（推定）
            japanese_docs = await conn.fetchval(
                """
                SELECT COUNT(*) FROM knowledge_sage.knowledge_entities
                WHERE search_vector @@ plainto_tsquery('japanese', 'の')
            """
            )
            stats["estimated_japanese_documents"] = japanese_docs

            # カテゴリ別文書数
            category_stats = await conn.fetch(
                """
                SELECT category, COUNT(*) as count
                FROM knowledge_sage.knowledge_entities
                GROUP BY category
                ORDER BY count DESC
            """
            )
            stats["category_distribution"] = {
                row["category"]: row["count"] for row in category_stats
            }

            # キャッシュ統計
            stats["cache_size"] = len(self.search_cache)

            return stats

    async def close(self):
        """リソースのクリーンアップ"""
        self.search_cache.clear()
        await self.db_manager.close()
        logger.info("Full-text search engine closed")


# ============================================================================
# Usage Example
# ============================================================================


async def main():
    """使用例"""
    # 設定
    config = FullTextSearchConfig(
        default_language=TextLanguage.AUTO,
        japanese_tokenizer=TokenizerType.SUDACHI,
        max_results=10,
        enable_fuzzy_search=True,
    )

    db_config = DatabaseConfig()
    db_manager = EldersGuildDatabaseManager(db_config)

    # 検索エンジンの初期化
    search_engine = FullTextSearchEngine(config, db_manager)

    try:
        await search_engine.initialize()

        # 通常の検索
        results = await search_engine.search("PostgreSQL最適化")
        print(f"Found {len(results)} results for 'PostgreSQL最適化'")

        for result in results:
            print(
                f"- {result.knowledge.title} (score: {result.relevance_score:.3f}, lang: " \
                    "{result.language.value})"
            )

        # 英語検索
        english_results = await search_engine.search(
            "database optimization", language=TextLanguage.ENGLISH
        )
        print(f"Found {len(english_results)} results for 'database optimization'")

        # ファジー検索
        fuzzy_results = await search_engine.fuzzy_search("PostgreSQl")  # 意図的な誤字
        print(f"Found {len(fuzzy_results)} fuzzy results")

        # 統計情報
        stats = await search_engine.get_search_statistics()
        print(f"Search statistics: {stats}")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await search_engine.close()


if __name__ == "__main__":
    asyncio.run(main())
