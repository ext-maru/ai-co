#!/usr/bin/env python3
"""
Perfect Knowledge Injection 2.0 - 3段階知識注入システム実装 (Issue #115)

Advanced Knowledge Injection System with:
- 段階的知識注入: Basic → Contextual → Expert レベル
- 動的知識適応: リアルタイム知識更新・最適化
- 品質保証統合: 注入知識の検証・監査システム
- セマンティック検索: ベクトル化知識検索・関連性スコアリング

Author: クロードエルダー（Claude Elder）
Created: 2025/07/22 - Issue #115完全実装版
"""

import asyncio
import hashlib
import json
import logging
import pickle
import sqlite3
import time
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import threading
from collections import defaultdict, deque
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

logger = logging.getLogger(__name__)

class KnowledgeLevel(Enum):
    """知識レベル"""
    BASIC = "basic"
    CONTEXTUAL = "contextual" 
    EXPERT = "expert"

class InjectionStrategy(Enum):
    """注入戦略"""
    SEQUENTIAL = "sequential"      # 段階的注入
    PARALLEL = "parallel"         # 並列注入
    ADAPTIVE = "adaptive"         # 適応型注入
    SMART_MERGE = "smart_merge"   # スマートマージ

class KnowledgeQuality(Enum):
    """知識品質レベル"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    EXPERT = 4
    ELITE = 5

@dataclass
class KnowledgeChunk:
    """知識チャンク"""
    id: str
    content: str
    level: KnowledgeLevel
    quality: KnowledgeQuality
    tags: List[str]
    embeddings: Optional[np.ndarray]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    access_count: int = 0
    relevance_score: float = 0.0

@dataclass
class InjectionResult:
    """注入結果"""
    success: bool
    chunks_injected: int
    injection_time: float
    quality_score: float
    strategy_used: InjectionStrategy
    level_distribution: Dict[KnowledgeLevel, int]
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]

@dataclass
class KnowledgeContext:
    """知識コンテキスト"""
    task_type: str
    domain: str
    complexity_level: int  # 1-10
    required_expertise: List[str]
    user_preferences: Dict[str, Any]
    session_history: List[str]
    performance_constraints: Dict[str, Any]

class SemanticSearchEngine:
    """セマンティック検索エンジン"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.dimension = 384  # all-MiniLM-L6-v2の次元数
        self.chunk_map: Dict[int, str] = {}
        self._build_index()
    
    def _build_index(self):
        """FAISSインデックス構築"""
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner Product for cosine similarity
    
    def add_chunks(self, chunks: List[KnowledgeChunk]):
        """チャンクをインデックスに追加"""
        if not chunks:
            return
        
        embeddings = []
        for i, chunk in enumerate(chunks):
            if chunk.embeddings is None:
                # エンベディング生成
                chunk.embeddings = self.model.encode([chunk.content])[0]
                chunk.embeddings = chunk.embeddings / np.linalg.norm(chunk.embeddings)  # normalize
            
            embeddings.append(chunk.embeddings)
            self.chunk_map[self.index.ntotal + i] = chunk.id
        
        if embeddings:
            embeddings_array = np.array(embeddings).astype('float32')
            self.index.add(embeddings_array)
    
    def search(self, query: str, k: int = 10) -> List[Tuple[str, float]]:
        """セマンティック検索実行"""
        if self.index.ntotal == 0:
            return []
        
        query_embedding = self.model.encode([query])[0]
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        query_embedding = query_embedding.astype('float32').reshape(1, -1)
        
        scores, indices = self.index.search(query_embedding, min(k, self.index.ntotal))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1 and idx in self.chunk_map:
                results.append((self.chunk_map[idx], float(score)))
        
        return results

class KnowledgeQualityAssurance:
    """知識品質保証システム"""
    
    def __init__(self):
        self.quality_rules = self._load_quality_rules()
        self.validation_history = []
    
    def validate_chunk(self, chunk: KnowledgeChunk) -> Dict[str, Any]:
        """チャンク品質検証"""
        issues = []
        warnings = []
        score = 100.0
        
        # 内容品質チェック
        if len(chunk.content) < 50:
            issues.append("Content too short")
            score -= 20
        
        if not chunk.content.strip():
            issues.append("Empty content")
            score = 0
        
        # メタデータ品質チェック
        if not chunk.tags:
            warnings.append("No tags specified")
            score -= 5
        
        if not chunk.metadata:
            warnings.append("No metadata provided")
            score -= 5
        
        # セマンティック品質チェック（簡易版）
        word_count = len(chunk.content.split())
        if word_count < 10:
            issues.append("Content lacks semantic richness")
            score -= 15
        elif word_count > 1000:
            warnings.append("Content might be too verbose")
            score -= 5
        
        # 品質スコアに基づく品質レベル決定
        if score >= 90:
            suggested_quality = KnowledgeQuality.ELITE
        elif score >= 80:
            suggested_quality = KnowledgeQuality.EXPERT
        elif score >= 70:
            suggested_quality = KnowledgeQuality.HIGH
        elif score >= 60:
            suggested_quality = KnowledgeQuality.MEDIUM
        else:
            suggested_quality = KnowledgeQuality.LOW
        
        return {
            "quality_score": score,
            "suggested_quality": suggested_quality,
            "issues": issues,
            "warnings": warnings,
            "is_valid": len(issues) == 0
        }
    
    def _load_quality_rules(self) -> Dict[str, Any]:
        """品質ルール読み込み"""
        return {
            "min_content_length": 50,
            "max_content_length": 10000,
            "required_tags": ["domain", "difficulty"],
            "semantic_coherence_threshold": 0.7
        }

class PerfectKnowledgeInjector:
    """Perfect Knowledge Injection 2.0 メインクラス"""
    
    def __init__(self, 
                 db_path: str = "/home/aicompany/ai_co/data/knowledge_injection_v2.db",
                 enable_semantic_search: bool = True):
        self.db_path = db_path
        self.enable_semantic_search = enable_semantic_search
        
        # コンポーネント初期化
        self.search_engine = SemanticSearchEngine() if enable_semantic_search else None
        self.quality_assurance = KnowledgeQualityAssurance()
        
        # 知識ストレージ
        self.knowledge_store: Dict[str, KnowledgeChunk] = {}
        self.injection_history: List[InjectionResult] = []
        
        # 統計・キャッシュ
        self.access_stats = defaultdict(int)
        self.performance_cache = {}
        self.cache_ttl = 3600  # 1時間
        
        # データベース初期化
        self._init_database()
        self._load_knowledge_base()
    
    def _init_database(self):
        """データベース初期化"""
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS knowledge_chunks (
                        id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        level TEXT NOT NULL,
                        quality INTEGER NOT NULL,
                        tags TEXT NOT NULL,
                        embeddings BLOB,
                        metadata TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        access_count INTEGER DEFAULT 0,
                        relevance_score REAL DEFAULT 0.0
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS injection_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        success BOOLEAN NOT NULL,
                        chunks_injected INTEGER NOT NULL,
                        injection_time REAL NOT NULL,
                        quality_score REAL NOT NULL,
                        strategy_used TEXT NOT NULL,
                        level_distribution TEXT NOT NULL,
                        errors TEXT NOT NULL,
                        warnings TEXT NOT NULL,
                        metadata TEXT NOT NULL
                    )
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_level ON knowledge_chunks(level)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_quality ON knowledge_chunks(quality)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_results_timestamp ON injection_results(timestamp)
                """)
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    def _load_knowledge_base(self):
        """知識ベース読み込み"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM knowledge_chunks")
                rows = cursor.fetchall()
                
                chunks = []
                for row in rows:
                    chunk = KnowledgeChunk(
                        id=row[0],
                        content=row[1],
                        level=KnowledgeLevel(row[2]),
                        quality=KnowledgeQuality(row[3]),
                        tags=json.loads(row[4]),
                        embeddings=pickle.loads(row[5]) if row[5] else None,
                        metadata=json.loads(row[6]),
                        created_at=datetime.fromisoformat(row[7]),
                        updated_at=datetime.fromisoformat(row[8]),
                        access_count=row[9],
                        relevance_score=row[10]
                    )
                    self.knowledge_store[chunk.id] = chunk
                    chunks.append(chunk)
                
                # セマンティック検索インデックス構築
                if self.search_engine and chunks:
                    self.search_engine.add_chunks(chunks)
                
                logger.info(f"Loaded {len(chunks)} knowledge chunks")
                
        except Exception as e:
            logger.error(f"Knowledge base loading error: {e}")
    
    def add_knowledge(self, 
                     content: str, 
                     level: KnowledgeLevel, 
                     tags: List[str], 
                     metadata: Optional[Dict[str, Any]] = None) -> str:
        """知識追加"""
        
        # 知識チャンク作成
        chunk_id = hashlib.md5(content.encode()).hexdigest()
        chunk = KnowledgeChunk(
            id=chunk_id,
            content=content,
            level=level,
            quality=KnowledgeQuality.MEDIUM,  # デフォルト
            tags=tags,
            embeddings=None,  # 後で生成
            metadata=metadata or {},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # 品質検証
        validation_result = self.quality_assurance.validate_chunk(chunk)
        if not validation_result["is_valid"]:
            raise ValueError(f"Knowledge quality validation failed: {validation_result['issues']}")
        
        chunk.quality = validation_result["suggested_quality"]
        
        # セマンティック検索用エンベディング生成
        if self.search_engine:
            self.search_engine.add_chunks([chunk])
        
        # ストレージに追加
        self.knowledge_store[chunk_id] = chunk
        
        # データベース保存
        self._save_chunk_to_db(chunk)
        
        logger.info(f"Added knowledge chunk {chunk_id} with quality {chunk.quality.name}")
        return chunk_id
    
    def _save_chunk_to_db(self, chunk: KnowledgeChunk):
        """チャンクをデータベースに保存"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO knowledge_chunks
                    (id, content, level, quality, tags, embeddings, metadata, 
                     created_at, updated_at, access_count, relevance_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    chunk.id,
                    chunk.content,
                    chunk.level.value,
                    chunk.quality.value,
                    json.dumps(chunk.tags),
                    pickle.dumps(chunk.embeddings) if chunk.embeddings is not None else None,
                    json.dumps(chunk.metadata),
                    chunk.created_at.isoformat(),
                    chunk.updated_at.isoformat(),
                    chunk.access_count,
                    chunk.relevance_score
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Database save error: {e}")
    
    async def inject_knowledge(self, 
                              context: KnowledgeContext, 
                              strategy: InjectionStrategy = InjectionStrategy.ADAPTIVE) -> InjectionResult:
        """知識注入実行"""
        
        start_time = time.time()
        errors = []
        warnings = []
        injected_chunks = []
        
        try:
            # 1. コンテキスト分析による知識選択
            relevant_chunks = await self._select_relevant_knowledge(context)
            if not relevant_chunks:
                warnings.append("No relevant knowledge found for context")
                return self._create_injection_result(
                    success=False, chunks_injected=0, 
                    injection_time=time.time() - start_time,
                    errors=["No relevant knowledge available"],
                    warnings=warnings, strategy_used=strategy
                )
            
            # 2. 注入戦略に基づく処理
            if strategy == InjectionStrategy.SEQUENTIAL:
                injected_chunks = await self._sequential_injection(relevant_chunks, context)
            elif strategy == InjectionStrategy.PARALLEL:
                injected_chunks = await self._parallel_injection(relevant_chunks, context)
            elif strategy == InjectionStrategy.ADAPTIVE:
                injected_chunks = await self._adaptive_injection(relevant_chunks, context)
            elif strategy == InjectionStrategy.SMART_MERGE:
                injected_chunks = await self._smart_merge_injection(relevant_chunks, context)
            
            # 3. 品質検証
            quality_score = await self._calculate_injection_quality(injected_chunks, context)
            
            # 4. 統計更新
            for chunk in injected_chunks:
                chunk.access_count += 1
                self.access_stats[chunk.id] += 1
                self._save_chunk_to_db(chunk)
            
            # 5. 結果作成
            injection_time = time.time() - start_time
            result = self._create_injection_result(
                success=True,
                chunks_injected=len(injected_chunks),
                injection_time=injection_time,
                quality_score=quality_score,
                strategy_used=strategy,
                level_distribution=self._calculate_level_distribution(injected_chunks),
                errors=errors,
                warnings=warnings
            )
            
            # 6. 結果保存
            self._save_injection_result(result)
            self.injection_history.append(result)
            
            logger.info(f"Knowledge injection completed: {len(injected_chunks)} chunks, quality={quality_score:.2f}")
            return result
            
        except Exception as e:
            errors.append(str(e))
            logger.error(f"Knowledge injection failed: {e}")
            return self._create_injection_result(
                success=False, chunks_injected=0,
                injection_time=time.time() - start_time,
                errors=errors, warnings=warnings,
                strategy_used=strategy
            )
    
    async def _select_relevant_knowledge(self, context: KnowledgeContext) -> List[KnowledgeChunk]:
        """関連知識選択"""
        relevant_chunks = []
        
        # セマンティック検索による関連性スコアリング
        if self.search_engine:
            query = f"{context.task_type} {context.domain} {' '.join(context.required_expertise)}"
            search_results = self.search_engine.search(query, k=50)
            
            for chunk_id, relevance_score in search_results:
                if chunk_id in self.knowledge_store:
                    chunk = self.knowledge_store[chunk_id]
                    chunk.relevance_score = relevance_score
                    
                    # コンテキスト適合性フィルタリング
                    if self._is_context_compatible(chunk, context):
                        relevant_chunks.append(chunk)
        
        # 品質・レベル別ソート
        relevant_chunks.sort(key=lambda c: (c.relevance_score, c.quality.value), reverse=True)
        
        # 複雑度に応じた選択数調整
        max_chunks = min(20, max(5, context.complexity_level * 2))
        return relevant_chunks[:max_chunks]
    
    def _is_context_compatible(self, chunk: KnowledgeChunk, context: KnowledgeContext) -> bool:
        """コンテキスト適合性チェック"""
        # ドメイン一致チェック
        if context.domain and context.domain not in chunk.tags:
            return False
        
        # 複雑度レベル適合チェック
        level_complexity = {
            KnowledgeLevel.BASIC: 3,
            KnowledgeLevel.CONTEXTUAL: 6,
            KnowledgeLevel.EXPERT: 10
        }
        
        if level_complexity[chunk.level] > context.complexity_level + 2:
            return False
        
        return True
    
    async def _sequential_injection(self, chunks: List[KnowledgeChunk], context: KnowledgeContext) -> List[KnowledgeChunk]:
        """段階的注入"""
        injected = []
        
        # レベル順で段階的注入
        for level in [KnowledgeLevel.BASIC, KnowledgeLevel.CONTEXTUAL, KnowledgeLevel.EXPERT]:
            level_chunks = [c for c in chunks if c.level == level]
            for chunk in level_chunks[:5]:  # 各レベル最大5チャンク
                injected.append(chunk)
                await asyncio.sleep(0.001)  # 非同期処理のため
        
        return injected
    
    async def _parallel_injection(self, chunks: List[KnowledgeChunk], context: KnowledgeContext) -> List[KnowledgeChunk]:
        """並列注入"""
        # 並列処理のシミュレーション
        tasks = []
        for chunk in chunks[:15]:  # 最大15チャンク
            tasks.append(self._process_chunk_async(chunk, context))
        
        results = await asyncio.gather(*tasks)
        return [chunk for chunk, success in results if success]
    
    async def _adaptive_injection(self, chunks: List[KnowledgeChunk], context: KnowledgeContext) -> List[KnowledgeChunk]:
        """適応型注入"""
        injected = []
        
        # 動的品質閾値調整
        quality_threshold = max(1, context.complexity_level // 2)
        
        for chunk in chunks:
            if chunk.quality.value >= quality_threshold:
                injected.append(chunk)
                
                # 動的閾値調整
                if len(injected) > 10:
                    quality_threshold += 1
                    
            if len(injected) >= 20:
                break
        
        return injected
    
    async def _smart_merge_injection(self, chunks: List[KnowledgeChunk], context: KnowledgeContext) -> List[KnowledgeChunk]:
        """スマートマージ注入"""
        # 重複内容のマージとクラスタリング
        merged_chunks = []
        processed_content = set()
        
        for chunk in chunks:
            content_hash = hashlib.md5(chunk.content[:100].encode()).hexdigest()
            
            if content_hash not in processed_content:
                processed_content.add(content_hash)
                merged_chunks.append(chunk)
                
            if len(merged_chunks) >= 15:
                break
        
        return merged_chunks
    
    async def _process_chunk_async(self, chunk: KnowledgeChunk, context: KnowledgeContext) -> Tuple[KnowledgeChunk, bool]:
        """チャンク非同期処理"""
        await asyncio.sleep(0.001)  # 非同期処理シミュレーション
        return chunk, True
    
    async def _calculate_injection_quality(self, chunks: List[KnowledgeChunk], context: KnowledgeContext) -> float:
        """注入品質計算"""
        if not chunks:
            return 0.0
        
        # 基本品質スコア
        quality_scores = [chunk.quality.value for chunk in chunks]
        base_score = sum(quality_scores) / len(quality_scores) * 20  # 0-100スケール
        
        # 関連性スコア
        relevance_scores = [chunk.relevance_score for chunk in chunks]
        relevance_score = sum(relevance_scores) / len(relevance_scores) * 100
        
        # 多様性スコア
        level_diversity = len(set(chunk.level for chunk in chunks)) / 3 * 100
        
        # 総合スコア計算
        overall_score = (base_score * 0.4 + relevance_score * 0.4 + level_diversity * 0.2)
        return min(100.0, overall_score)
    
    def _calculate_level_distribution(self, chunks: List[KnowledgeChunk]) -> Dict[KnowledgeLevel, int]:
        """レベル分布計算"""
        distribution = {level: 0 for level in KnowledgeLevel}
        for chunk in chunks:
            distribution[chunk.level] += 1
        return distribution
    
    def _create_injection_result(self, **kwargs) -> InjectionResult:
        """注入結果作成"""
        return InjectionResult(
            success=kwargs.get('success', False),
            chunks_injected=kwargs.get('chunks_injected', 0),
            injection_time=kwargs.get('injection_time', 0.0),
            quality_score=kwargs.get('quality_score', 0.0),
            strategy_used=kwargs.get('strategy_used', InjectionStrategy.ADAPTIVE),
            level_distribution=kwargs.get('level_distribution', {}),
            errors=kwargs.get('errors', []),
            warnings=kwargs.get('warnings', []),
            metadata=kwargs.get('metadata', {})
        )
    
    def _save_injection_result(self, result: InjectionResult):
        """注入結果保存"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO injection_results
                    (timestamp, success, chunks_injected, injection_time, quality_score,
                     strategy_used, level_distribution, errors, warnings, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now(timezone.utc).isoformat(),
                    result.success,
                    result.chunks_injected,
                    result.injection_time,
                    result.quality_score,
                    result.strategy_used.value,
                    json.dumps({k.value: v for k, v in result.level_distribution.items()}),
                    json.dumps(result.errors),
                    json.dumps(result.warnings),
                    json.dumps(result.metadata)
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Result save error: {e}")
    
    def get_injection_statistics(self) -> Dict[str, Any]:
        """注入統計取得"""
        if not self.injection_history:
            return {"message": "No injection history available"}
        
        successful_injections = [r for r in self.injection_history if r.success]
        
        return {
            "total_injections": len(self.injection_history),
            "successful_injections": len(successful_injections),
            "success_rate": len(successful_injections) / len(self.injection_history) * 100,
            "average_quality_score": sum(r.quality_score for r in successful_injections) / len(successful_injections) if successful_injections else 0,
            "average_injection_time": sum(r.injection_time for r in successful_injections) / len(successful_injections) if successful_injections else 0,
            "total_chunks_in_store": len(self.knowledge_store),
            "most_accessed_chunks": sorted(self.access_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        }
    
    def export_knowledge_base(self, format: str = "json") -> str:
        """知識ベースエクスポート"""
        if format == "json":
            export_data = {}
            for chunk_id, chunk in self.knowledge_store.items():
                export_data[chunk_id] = {
                    "content": chunk.content,
                    "level": chunk.level.value,
                    "quality": chunk.quality.value,
                    "tags": chunk.tags,
                    "metadata": chunk.metadata,
                    "access_count": chunk.access_count,
                    "relevance_score": chunk.relevance_score
                }
            return json.dumps(export_data, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Unsupported export format: {format}")


# 使用例とユーティリティ関数
async def initialize_sample_knowledge_base(injector: PerfectKnowledgeInjector):
    """サンプル知識ベース初期化"""
    
    sample_knowledge = [
        {
            "content": "Pythonの基本的なデータ型には、int, float, str, bool, list, dict, tupleがあります。これらは最も頻繁に使用される型です。",
            "level": KnowledgeLevel.BASIC,
            "tags": ["python", "basics", "data-types"],
            "metadata": {"domain": "programming", "difficulty": 1}
        },
        {
            "content": "非同期プログラミングでは、async/awaitキーワードを使用してコルーチンを定義し、I/O待機時間を効率的に活用できます。asyncio.gather()を使用して複数のタスクを並列実行できます。",
            "level": KnowledgeLevel.CONTEXTUAL,
            "tags": ["python", "async", "concurrency"],
            "metadata": {"domain": "programming", "difficulty": 5}
        },
        {
            "content": "高性能なシステム設計では、CAP定理（Consistency, Availability, Partition tolerance）を理解し、システム要件に応じて適切なトレードオフを選択する必要があります。分散システムではPartition toleranceは必須であり、ConsistencyとAvailabilityのバランスを取る必要があります。",
            "level": KnowledgeLevel.EXPERT,
            "tags": ["system-design", "distributed-systems", "cap-theorem"],
            "metadata": {"domain": "architecture", "difficulty": 9}
        }
    ]
    
    for knowledge in sample_knowledge:
        try:
            chunk_id = injector.add_knowledge(
                content=knowledge["content"],
                level=knowledge["level"],
                tags=knowledge["tags"],
                metadata=knowledge["metadata"]
            )
            print(f"Added knowledge chunk: {chunk_id}")
        except Exception as e:
            print(f"Failed to add knowledge: {e}")

async def demonstrate_perfect_knowledge_injection():
    """Perfect Knowledge Injection 2.0 デモ"""
    
    # システム初期化
    injector = PerfectKnowledgeInjector(
        db_path="/tmp/demo_knowledge.db",
        enable_semantic_search=True
    )
    
    print("🚀 Perfect Knowledge Injection 2.0 Demo")
    print("=" * 50)
    
    # サンプル知識ベース初期化
    await initialize_sample_knowledge_base(injector)
    
    # コンテキスト作成
    context = KnowledgeContext(
        task_type="code_development",
        domain="python",
        complexity_level=6,
        required_expertise=["async_programming", "performance"],
        user_preferences={"detail_level": "high"},
        session_history=["async", "performance"],
        performance_constraints={"max_injection_time": 2.0}
    )
    
    print(f"\n📋 Context: {context.task_type} in {context.domain} domain")
    print(f"    Complexity: {context.complexity_level}/10")
    print(f"    Required expertise: {context.required_expertise}")
    
    # 各戦略での知識注入テスト
    strategies = [
        InjectionStrategy.SEQUENTIAL,
        InjectionStrategy.PARALLEL,
        InjectionStrategy.ADAPTIVE,
        InjectionStrategy.SMART_MERGE
    ]
    
    for strategy in strategies:
        print(f"\n🔄 Testing {strategy.value} injection strategy...")
        
        result = await injector.inject_knowledge(context, strategy)
        
        print(f"    Success: {result.success}")
        print(f"    Chunks injected: {result.chunks_injected}")
        print(f"    Quality score: {result.quality_score:.2f}")
        print(f"    Injection time: {result.injection_time:.3f}s")
        
        if result.errors:
            print(f"    Errors: {result.errors}")
        if result.warnings:
            print(f"    Warnings: {result.warnings}")
    
    # 統計表示
    print(f"\n📊 Knowledge Injection Statistics:")
    stats = injector.get_injection_statistics()
    for key, value in stats.items():
        if key != "most_accessed_chunks":
            print(f"    {key}: {value}")
    
    print("\n✅ Perfect Knowledge Injection 2.0 Demo completed!")


if __name__ == "__main__":
    # デモ実行
    asyncio.run(demonstrate_perfect_knowledge_injection())