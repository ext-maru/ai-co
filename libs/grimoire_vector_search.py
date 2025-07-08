#!/usr/bin/env python3
"""
Magic Grimoire Vector Search Engine
魔法書ベクトル検索エンジン - OpenAI embeddings + pgvector
"""

import os
import sys
import json
import asyncio
import logging
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
from enum import Enum

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.grimoire_database import GrimoireDatabase, SpellType, MagicSchool

logger = logging.getLogger(__name__)

# OpenAI API用インポート（実際の実装では必要）
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available - using mock embeddings")

@dataclass
class SearchQuery:
    """検索クエリ"""
    query_text: str
    filters: Optional[Dict[str, Any]] = None
    limit: int = 10
    similarity_threshold: float = 0.8
    include_eternal_only: bool = False
    magic_schools: Optional[List[MagicSchool]] = None
    spell_types: Optional[List[SpellType]] = None
    min_power_level: Optional[int] = None

@dataclass
class SearchResult:
    """検索結果"""
    spell_id: str
    spell_name: str
    content: str
    similarity_score: float
    spell_type: str
    magic_school: str
    tags: List[str]
    power_level: int
    is_eternal: bool
    casting_frequency: int
    created_at: datetime
    snippet: str  # 検索結果のハイライト部分

class EmbeddingGenerator:
    """埋め込みベクトル生成器"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初期化"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model_name = "text-embedding-3-small"  # 1536次元
        self.cache = {}  # 単純なインメモリキャッシュ
        
        if OPENAI_AVAILABLE and self.api_key:
            openai.api_key = self.api_key
            self.use_real_embeddings = True
        else:
            self.use_real_embeddings = False
            logger.warning("Using mock embeddings - set OPENAI_API_KEY for real embeddings")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """テキストの埋め込みベクトル生成"""
        # キャッシュチェック
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self.cache:
            return self.cache[text_hash]
        
        if self.use_real_embeddings:
            try:
                response = await openai.Embedding.acreate(
                    model=self.model_name,
                    input=text
                )
                embedding = response['data'][0]['embedding']
            except Exception as e:
                logger.error(f"OpenAI embedding failed: {e}")
                embedding = self._generate_mock_embedding(text)
        else:
            embedding = self._generate_mock_embedding(text)
        
        # キャッシュに保存
        self.cache[text_hash] = embedding
        return embedding
    
    def _generate_mock_embedding(self, text: str) -> List[float]:
        """モック埋め込み生成（テスト・開発用）"""
        # テキストのハッシュベースで一貫性のある埋め込みを生成
        text_hash = hashlib.md5(text.encode()).digest()
        np.random.seed(int.from_bytes(text_hash[:4], 'big'))
        
        # 正規化された1536次元ベクトル
        embedding = np.random.normal(0, 1, 1536)
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding.tolist()
    
    async def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """バッチ埋め込み生成"""
        if self.use_real_embeddings and len(texts) > 1:
            try:
                response = await openai.Embedding.acreate(
                    model=self.model_name,
                    input=texts
                )
                return [item['embedding'] for item in response['data']]
            except Exception as e:
                logger.error(f"Batch embedding failed: {e}")
        
        # フォールバック：個別生成
        embeddings = []
        for text in texts:
            embedding = await self.generate_embedding(text)
            embeddings.append(embedding)
        
        return embeddings

class SemanticProcessor:
    """意味処理器"""
    
    def __init__(self):
        """初期化"""
        self.magic_keywords = {
            MagicSchool.KNOWLEDGE_SAGE: [
                'knowledge', 'learn', 'document', 'guide', 'tutorial', 
                'explanation', 'concept', 'theory', 'understand'
            ],
            MagicSchool.TASK_ORACLE: [
                'task', 'project', 'workflow', 'process', 'step', 
                'procedure', 'plan', 'execute', 'manage'
            ],
            MagicSchool.CRISIS_SAGE: [
                'error', 'bug', 'fix', 'debug', 'incident', 'crisis', 
                'emergency', 'troubleshoot', 'resolve'
            ],
            MagicSchool.SEARCH_MYSTIC: [
                'search', 'find', 'query', 'analyze', 'discover', 
                'explore', 'investigate', 'research'
            ]
        }
    
    def preprocess_query(self, query: str) -> str:
        """クエリ前処理"""
        # 小文字化
        processed = query.lower().strip()
        
        # 日本語・英語の正規化（簡単な実装）
        replacements = {
            'エラー': 'error',
            'バグ': 'bug',
            'タスク': 'task',
            'プロジェクト': 'project',
            'ナレッジ': 'knowledge',
            '検索': 'search',
            'claude': 'claude cli development'
        }
        
        for jp, en in replacements.items():
            processed = processed.replace(jp, en)
        
        return processed
    
    def infer_magic_school(self, text: str) -> Optional[MagicSchool]:
        """テキストから魔法学派を推定"""
        text_lower = text.lower()
        school_scores = {}
        
        for school, keywords in self.magic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                school_scores[school] = score
        
        if school_scores:
            return max(school_scores, key=school_scores.get)
        
        return None
    
    def extract_keywords(self, text: str) -> List[str]:
        """キーワード抽出"""
        # 簡単な実装：よく使われる技術用語
        keywords = [
            'claude', 'tdd', 'test', 'database', 'api', 'web', 'ui',
            'postgresql', 'vector', 'search', 'embedding', 'ai',
            'worker', 'task', 'project', 'system', 'error', 'bug'
        ]
        
        found_keywords = []
        text_lower = text.lower()
        
        for keyword in keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def generate_snippet(self, content: str, query: str, max_length: int = 200) -> str:
        """検索結果スニペット生成"""
        query_words = query.lower().split()
        content_lower = content.lower()
        
        # クエリワードが含まれる位置を特定
        best_pos = 0
        best_score = 0
        
        for i in range(0, len(content_lower) - max_length + 1, 50):
            section = content_lower[i:i + max_length]
            score = sum(1 for word in query_words if word in section)
            if score > best_score:
                best_score = score
                best_pos = i
        
        # スニペット抽出
        snippet = content[best_pos:best_pos + max_length]
        
        # 文の境界で切る
        if best_pos > 0:
            # 最初の文の境界を探す
            first_period = snippet.find('.')
            if first_period > 50:
                snippet = '...' + snippet[first_period + 1:]
        
        if len(snippet) == max_length:
            # 最後の文の境界を探す
            last_period = snippet.rfind('.')
            if last_period > max_length - 50:
                snippet = snippet[:last_period + 1] + '...'
            else:
                snippet += '...'
        
        return snippet.strip()

class GrimoireVectorSearch:
    """魔法書ベクトル検索エンジン"""
    
    def __init__(self, database: Optional[GrimoireDatabase] = None):
        """初期化"""
        self.database = database or GrimoireDatabase()
        self.embedding_generator = EmbeddingGenerator()
        self.semantic_processor = SemanticProcessor()
        
        logger.info("🔍 Grimoire Vector Search Engine initialized")
    
    async def initialize(self) -> bool:
        """初期化"""
        if not await self.database.initialize():
            return False
        
        logger.info("✅ Vector Search Engine ready")
        return True
    
    async def index_spell(self, spell_id: str, spell_data: Dict[str, Any]) -> bool:
        """呪文のインデックス化"""
        try:
            # 検索用テキストを準備
            searchable_text = self._prepare_searchable_text(spell_data)
            
            # 埋め込みベクトル生成
            embedding = await self.embedding_generator.generate_embedding(searchable_text)
            
            # データベースに保存
            await self.database.create_spell(spell_data, embedding)
            
            logger.info(f"🔮 Spell indexed: {spell_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to index spell {spell_id}: {e}")
            return False
    
    def _prepare_searchable_text(self, spell_data: Dict[str, Any]) -> str:
        """検索可能テキストの準備"""
        components = [
            spell_data.get('spell_name', ''),
            spell_data.get('content', ''),
            ' '.join(spell_data.get('tags', [])),
            spell_data.get('spell_type', ''),
            spell_data.get('magic_school', '')
        ]
        
        return ' '.join(filter(None, components))
    
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """セマンティック検索"""
        try:
            # クエリ前処理
            processed_query = self.semantic_processor.preprocess_query(query.query_text)
            
            # クエリの埋め込みベクトル生成
            query_embedding = await self.embedding_generator.generate_embedding(processed_query)
            
            # フィルター準備
            filters = self._prepare_filters(query)
            
            # データベース検索
            raw_results = await self.database.search_spells_by_vector(
                query_embedding,
                limit=query.limit * 2,  # 後処理のため多めに取得
                filters=filters
            )
            
            # 結果処理
            search_results = []
            for raw_result in raw_results:
                # 類似度スコア計算（距離を類似度に変換）
                similarity_score = 1.0 - raw_result['similarity_distance']
                
                if similarity_score >= query.similarity_threshold:
                    # スニペット生成
                    snippet = self.semantic_processor.generate_snippet(
                        raw_result['content'], 
                        query.query_text
                    )
                    
                    result = SearchResult(
                        spell_id=raw_result['id'],
                        spell_name=raw_result['spell_name'],
                        content=raw_result['content'],
                        similarity_score=similarity_score,
                        spell_type=raw_result['spell_type'],
                        magic_school=raw_result['magic_school'],
                        tags=raw_result['tags'],
                        power_level=raw_result['power_level'],
                        is_eternal=raw_result['is_eternal'],
                        casting_frequency=raw_result['casting_frequency'],
                        created_at=raw_result['created_at'],
                        snippet=snippet
                    )
                    
                    search_results.append(result)
                    
                    # 詠唱回数更新
                    await self.database.update_casting_frequency(raw_result['id'])
            
            # 類似度とパワーレベルでソート
            search_results.sort(
                key=lambda x: (x.similarity_score, x.power_level), 
                reverse=True
            )
            
            return search_results[:query.limit]
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    def _prepare_filters(self, query: SearchQuery) -> Dict[str, Any]:
        """検索フィルター準備"""
        filters = query.filters or {}
        
        if query.include_eternal_only:
            filters['is_eternal'] = True
        
        if query.magic_schools:
            filters['magic_school'] = [school.value for school in query.magic_schools]
        
        if query.spell_types:
            filters['spell_type'] = [spell_type.value for spell_type in query.spell_types]
        
        if query.min_power_level:
            filters['min_power_level'] = query.min_power_level
        
        return filters
    
    async def find_related_spells(self, spell_id: str, limit: int = 5) -> List[SearchResult]:
        """関連呪文検索"""
        try:
            # 元呪文取得
            spell_data = await self.database.get_spell_by_id(spell_id)
            if not spell_data:
                return []
            
            # 元呪文のテキストで検索
            searchable_text = self._prepare_searchable_text(spell_data)
            
            query = SearchQuery(
                query_text=searchable_text,
                limit=limit + 1,  # 自分自身を除外するため+1
                similarity_threshold=0.3
            )
            
            results = await self.search(query)
            
            # 自分自身を除外
            related_results = [r for r in results if r.spell_id != spell_id]
            
            return related_results[:limit]
            
        except Exception as e:
            logger.error(f"❌ Related search failed: {e}")
            return []
    
    async def suggest_tags(self, content: str) -> List[str]:
        """自動タグ提案"""
        try:
            # キーワード抽出
            keywords = self.semantic_processor.extract_keywords(content)
            
            # 魔法学派推定
            inferred_school = self.semantic_processor.infer_magic_school(content)
            if inferred_school:
                keywords.append(inferred_school.value)
            
            # 重複除去
            return list(set(keywords))
            
        except Exception as e:
            logger.error(f"❌ Tag suggestion failed: {e}")
            return []
    
    async def search_by_similarity(self, reference_text: str, limit: int = 10) -> List[SearchResult]:
        """類似度による検索"""
        query = SearchQuery(
            query_text=reference_text,
            limit=limit,
            similarity_threshold=0.5
        )
        
        return await self.search(query)
    
    async def get_search_statistics(self) -> Dict[str, Any]:
        """検索統計取得"""
        # 簡単な統計実装
        return {
            'total_indexed_spells': 0,  # 実装時に実際の数を取得
            'cache_size': len(self.embedding_generator.cache),
            'search_engine_status': 'active'
        }
    
    async def close(self):
        """リソースクローズ"""
        await self.database.close()
        logger.info("🔍 Vector Search Engine closed")

# 使用例とテスト用関数
async def test_vector_search():
    """テスト実行"""
    search_engine = GrimoireVectorSearch()
    
    try:
        await search_engine.initialize()
        
        # サンプル呪文作成・インデックス化
        sample_spell = {
            'spell_name': 'Claude CLI Vector Search Guide',
            'content': 'Claudeでベクトル検索を実装するための完全ガイド。PostgreSQLのpgvectorを使用してセマンティック検索を構築します。',
            'spell_type': SpellType.KNOWLEDGE.value,
            'magic_school': MagicSchool.SEARCH_MYSTIC.value,
            'tags': ['claude', 'vector', 'search', 'postgresql'],
            'power_level': 8
        }
        
        await search_engine.index_spell("test-vector-spell", sample_spell)
        print("✅ Test spell indexed")
        
        # 検索テスト
        query = SearchQuery(
            query_text="ベクトル検索の実装方法",
            limit=5,
            similarity_threshold=0.7
        )
        
        results = await search_engine.search(query)
        print(f"✅ Search completed: {len(results)} results")
        
        for result in results:
            print(f"- {result.spell_name} (similarity: {result.similarity_score:.3f})")
        
        # タグ提案テスト
        suggested_tags = await search_engine.suggest_tags(sample_spell['content'])
        print(f"✅ Suggested tags: {suggested_tags}")
        
    finally:
        await search_engine.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_vector_search())