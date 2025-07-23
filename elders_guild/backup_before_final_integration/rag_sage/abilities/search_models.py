#!/usr/bin/env python3
"""
RAG Sage Data Models
検索・インデックス関連のデータモデル定義
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from uuid import uuid4


class SearchType(Enum):
    """検索タイプ"""
    FULL_TEXT = "full_text"      # 全文検索
    SEMANTIC = "semantic"         # セマンティック検索
    HYBRID = "hybrid"            # ハイブリッド検索
    EXACT = "exact"              # 完全一致検索


class IndexStatus(Enum):
    """インデックスステータス"""
    INITIALIZING = "initializing"
    READY = "ready"
    OPTIMIZING = "optimizing"
    ERROR = "error"
    REBUILDING = "rebuilding"


@dataclass
class DocumentMetadata:
    """ドキュメントメタデータ"""
    title: str
    category: str
    tags: List[str] = field(default_factory=list)
    author: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    language: str = "ja"
    version: int = 1
    custom_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Document:
    """ドキュメントエンティティ"""
    id: str
    content: str
    source: str
    metadata: DocumentMetadata
    embedding: Optional[List[float]] = None  # ベクトル表現
    chunks: List["DocumentChunk"] = field(default_factory=list)
    indexed_at: Optional[datetime] = None
    access_count: int = 0
    relevance_boost: float = 1.0  # 関連性ブースト係数
    
    def __post_init__(self):
        """バリデーション"""
        if not self.content or not self.content.strip():
            raise ValueError("ドキュメントコンテンツは必須です")
        if not self.source:
            raise ValueError("ドキュメントソースは必須です")


@dataclass
class DocumentChunk:
    """ドキュメントチャンク（分割されたドキュメント片）"""
    document_id: str
    content: str
    position: int  # ドキュメント内の位置
    id: str = field(default_factory=lambda: str(uuid4()))
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchQuery:
    """検索クエリ"""
    query: str
    search_type: SearchType = SearchType.FULL_TEXT
    filters: Dict[str, Any] = field(default_factory=dict)
    limit: int = 10
    offset: int = 0
    include_metadata: bool = True
    boost_fields: Dict[str, float] = field(default_factory=dict)
    exclude_sources: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        """バリデーション"""
        if not self.query or not self.query.strip():
            raise ValueError("検索クエリは必須です")
        if self.limit < 1 or self.limit > 1000:
            raise ValueError("limitは1から1000の間である必要があります")
        if self.offset < 0:
            raise ValueError("offsetは0以上である必要があります")


@dataclass
class SearchResult:
    """検索結果アイテム"""
    document: Document
    score: float  # 関連性スコア (0.0-1.0)
    highlights: List[str] = field(default_factory=list)  # ハイライト部分
    explanation: Optional[str] = None  # スコアの説明
    matched_fields: List[str] = field(default_factory=list)


@dataclass
class SearchResults:
    """検索結果セット"""
    query: SearchQuery
    results: List[SearchResult]
    total_count: int
    search_time_ms: float
    facets: Dict[str, Dict[str, int]] = field(default_factory=dict)  # ファセット集計
    suggestions: List[str] = field(default_factory=list)  # クエリサジェスチョン
    
    @property
    def has_results(self) -> bool:
        """結果があるかどうか"""
        return len(self.results) > 0


@dataclass
class IndexResult:
    """インデックス結果"""
    success: bool
    document_id: str
    index_time_ms: float
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


@dataclass
class BatchIndexResult:
    """バッチインデックス結果"""
    total_documents: int
    successful_count: int
    failed_count: int
    total_time_ms: float
    failed_documents: List[Dict[str, str]] = field(default_factory=list)  # id: error_message
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_documents == 0:
            return 0.0
        return self.successful_count / self.total_documents


@dataclass
class Index:
    """インデックス情報"""
    name: str
    status: IndexStatus
    document_count: int
    size_bytes: int
    created_at: datetime
    last_updated: datetime
    last_optimized: Optional[datetime] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    statistics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationResult:
    """インデックス最適化結果"""
    success: bool
    optimization_time_ms: float
    before_size_bytes: int
    after_size_bytes: int
    documents_processed: int
    error_message: Optional[str] = None
    
    @property
    def size_reduction_percent(self) -> float:
        """サイズ削減率"""
        if self.before_size_bytes == 0:
            return 0.0
        return ((self.before_size_bytes - self.after_size_bytes) / self.before_size_bytes) * 100


@dataclass
class CacheEntry:
    """キャッシュエントリ"""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    
    @property
    def is_expired(self) -> bool:
        """有効期限切れかどうか"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


@dataclass
class SearchContext:
    """検索コンテキスト（賢者間連携用）"""
    domain: str
    urgency: str = "normal"  # low, normal, high, critical
    requester: str = ""  # リクエスト元の賢者
    purpose: str = ""  # 検索の目的
    related_task_id: Optional[str] = None
    history: List[SearchQuery] = field(default_factory=list)  # 検索履歴