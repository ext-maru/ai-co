"""
📚 Knowledge Sage データモデル

知識管理システムのデータモデル定義
ナレッジベース、ベストプラクティス、学習パターンを管理
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional, Union
from uuid import uuid4


class KnowledgeCategory(Enum):
    pass


"""知識カテゴリ"""
    """知識アイテム"""
    title: str
    content: str
    category: KnowledgeCategory
    tags: List[str]
    source: str
    confidence_score: float = 0.8
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    id: str = field(default_factory=lambda: str(uuid4()))
    version: int = 1
    references: List[str] = field(default_factory=list)
    related_items: List[str] = field(default_factory=list)
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def __post_init__(self):
        pass

    
    """バリデーション"""
            raise ValueError("Title cannot be empty")
        if not self.content.strip():
            raise ValueError("Content cannot be empty")
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        
        # タグの正規化（小文字、重複除去）
        self.tags = list(set(tag.lower().strip() for tag in self.tags if tag.strip()))
    
    def update_content(self, new_content: str, source: str = None):
        """コンテンツ更新"""
        self.content = new_content
        self.updated_at = datetime.now(timezone.utc)
        self.version += 1
        if source:
            self.source = source
    
    def access(self):
        pass

            """アクセス記録"""
        """辞書変換"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": self.category.value,
            "tags": self.tags,
            "source": self.source,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "version": self.version,
            "references": self.references,
            "related_items": self.related_items,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None
        }


@dataclass
class BestPractice:
    pass

        """ベストプラクティス""" str
    description: str
    domain: str  # 適用領域
    impact_level: str  # critical, high, medium, low
    implementation_steps: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    id: str = field(default_factory=lambda: str(uuid4()))
    success_rate: float = 0.0
    adoption_count: int = 0
    
    def __post_init__(self):
        pass

    
    """バリデーション"""
            raise ValueError("Title cannot be empty")
        if self.impact_level not in ["critical", "high", "medium", "low"]:
            raise ValueError("Invalid impact level")
        if not (0.0 <= self.success_rate <= 1.0):
            raise ValueError("Success rate must be between 0.0 and 1.0")
    
    def add_example(self, title: str, description: str, code_snippet: str = None):
        """実例追加"""
        example = {
            "title": title,
            "description": description,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        if code_snippet:
            example["code_snippet"] = code_snippet
        self.examples.append(example)
    
    def record_adoption(self):
        pass

            """採用記録"""
        """辞書変換"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "domain": self.domain,
            "impact_level": self.impact_level,
            "implementation_steps": self.implementation_steps,
            "prerequisites": self.prerequisites,
            "benefits": self.benefits,
            "risks": self.risks,
            "examples": self.examples,
            "metrics": self.metrics,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "success_rate": self.success_rate,
            "adoption_count": self.adoption_count
        }


@dataclass
class LearningPattern:
    pass

        """学習パターン""" str
    trigger: str  # 発動条件
    approach: str  # アプローチ・手法
    success_rate: float = 0.0
    usage_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    id: str = field(default_factory=lambda: str(uuid4()))
    context_conditions: List[str] = field(default_factory=list)
    expected_outcomes: List[str] = field(default_factory=list)
    failure_modes: List[Dict[str, str]] = field(default_factory=list)
    adaptations: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        pass

    
    """バリデーション"""
            raise ValueError("Pattern name cannot be empty")
        if not (0.0 <= self.success_rate <= 1.0):
            raise ValueError("Success rate must be between 0.0 and 1.0")
    
    def record_usage(self, success: bool):
        """使用記録"""
        self.usage_count += 1
        # 成功率の更新（移動平均）
        if self.usage_count == 1:
            self.success_rate = 1.0 if success else 0.0
        else:
            # 指数移動平均で更新
            alpha = 0.1
            new_value = 1.0 if success else 0.0
            self.success_rate = alpha * new_value + (1 - alpha) * self.success_rate
        
        self.updated_at = datetime.now(timezone.utc)
    
    def add_failure_mode(self, condition: str, reason: str, recovery: str):
        """失敗モード追加"""
        failure_mode = {
            "condition": condition,
            "reason": reason,
            "recovery": recovery,
            "recorded_at": datetime.now(timezone.utc).isoformat()
        }
        self.failure_modes.append(failure_mode)
    
    def to_dict(self) -> Dict[str, Any]:
        pass

        """辞書変換""" self.id,
            "pattern_name": self.pattern_name,
            "trigger": self.trigger,
            "approach": self.approach,
            "success_rate": self.success_rate,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "context_conditions": self.context_conditions,
            "expected_outcomes": self.expected_outcomes,
            "failure_modes": self.failure_modes,
            "adaptations": self.adaptations
        }


@dataclass
class SearchQuery:
    pass

        """検索クエリ""" List[str] = field(default_factory=list)
    category: Optional[KnowledgeCategory] = None
    tags: List[str] = field(default_factory=list)
    min_confidence: float = 0.0
    max_results: int = 50
    sort_by: str = "relevance"  # relevance, date, confidence, access_count
    sort_order: str = "desc"  # desc, asc
    date_range: Optional[Dict[str, datetime]] = None
    include_related: bool = True
    
    def __post_init__(self):
        pass

    
    """バリデーション"""
            raise ValueError("Min confidence must be between 0.0 and 1.0")
        if self.sort_by not in ["relevance", "date", "confidence", "access_count"]:
            raise ValueError("Invalid sort_by value")
        if self.sort_order not in ["desc", "asc"]:
            raise ValueError("Invalid sort_order value")
        
        # キーワードとタグの正規化
        self.keywords = [kw.lower().strip() for kw in self.keywords if kw.strip()]
        self.tags = [tag.lower().strip() for tag in self.tags if tag.strip()]


@dataclass
class SearchResult:
    pass

            """検索結果""" KnowledgeItem
    relevance_score: float
    match_reasons: List[str] = field(default_factory=list)
    related_items: List['SearchResult'] = field(default_factory=list)
    
    def __post_init__(self):
        pass

    
    """バリデーション"""
            raise ValueError("Relevance score must be between 0.0 and 1.0")


@dataclass
class KnowledgeStatistics:
    pass

            """知識統計情報""" int = 0
    categories: Dict[KnowledgeCategory, int] = field(default_factory=dict)
    total_best_practices: int = 0
    total_learning_patterns: int = 0
    average_confidence: float = 0.0
    most_accessed_items: List[Dict[str, Any]] = field(default_factory=list)
    popular_tags: List[Dict[str, Any]] = field(default_factory=list)
    growth_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        pass

    
    """辞書変換""" self.total_items,
            "categories": {cat.value: count for cat, count in self.categories.items()},
            "total_best_practices": self.total_best_practices,
            "total_learning_patterns": self.total_learning_patterns,
            "average_confidence": self.average_confidence,
            "most_accessed_items": self.most_accessed_items,
            "popular_tags": self.popular_tags,
            "growth_metrics": self.growth_metrics
        }


@dataclass 
class KnowledgeSynthesis:
    pass

        """知識統合結果""" str
    summary: str
    key_points: List[str]
    related_items: List[str]  # Knowledge item IDs
    confidence: float
    sources: List[str]
    synthesis_method: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        pass

    
    """辞書変換""" self.topic,
            "summary": self.summary,
            "key_points": self.key_points,
            "related_items": self.related_items,
            "confidence": self.confidence,
            "sources": self.sources,
            "synthesis_method": self.synthesis_method,
            "created_at": self.created_at.isoformat()
        }


# ユーティリティ関数
def create_knowledge_item_from_dict(data: Dict[str, Any]) -> KnowledgeItem:
    """辞書からKnowledgeItemを作成"""
    # 日時文字列をdatetimeオブジェクトに変換
    created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data else None
    updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
    last_accessed = datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else None
    
    return KnowledgeItem(
        id=data.get("id", str(uuid4())),
        title=data["title"],
        content=data["content"],
        category=KnowledgeCategory(data["category"]),
        tags=data.get("tags", []),
        source=data["source"],
        confidence_score=data.get("confidence_score", 0.8),
        created_at=created_at or datetime.now(timezone.utc),
        updated_at=updated_at,
        version=data.get("version", 1),
        references=data.get("references", []),
        related_items=data.get("related_items", []),
        access_count=data.get("access_count", 0),
        last_accessed=last_accessed
    )