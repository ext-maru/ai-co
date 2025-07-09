#!/usr/bin/env python3
"""
PROJECT ELDERZAN - Session Management Data Models
プロジェクトエルダーザン セッション管理データモデル

4賢者システム承認済み設計仕様に基づくデータモデル実装
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import hashlib

class SessionStatus(Enum):
    """セッション状態"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    ERROR = "error"

class SageType(Enum):
    """4賢者タイプ"""
    KNOWLEDGE = "knowledge"  # 📚 ナレッジ賢者
    TASK = "task"           # 📋 タスク賢者  
    INCIDENT = "incident"   # 🚨 インシデント賢者
    RAG = "rag"            # 🔍 RAG賢者

class Priority(Enum):
    """優先度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SageInteraction:
    """4賢者との相互作用記録"""
    sage_type: SageType
    interaction_type: str  # consultation, decision, analysis, etc.
    timestamp: datetime
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    confidence_score: float  # 0.0-1.0
    processing_time: float  # seconds
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        data = asdict(self)
        data['sage_type'] = self.sage_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SageInteraction':
        """辞書から復元"""
        data['sage_type'] = SageType(data['sage_type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

@dataclass
class SessionMetadata:
    """セッションメタデータ"""
    session_id: str
    user_id: str
    project_path: str
    created_at: datetime
    updated_at: datetime
    status: SessionStatus = SessionStatus.ACTIVE
    
    # パフォーマンス指標
    total_tokens_saved: int = 0
    compression_ratio: float = 0.0  # 0.0-1.0
    response_time_improvement: float = 0.0  # %
    
    # 4賢者利用統計
    sage_interactions_count: Dict[str, int] = field(default_factory=dict)
    last_sage_consultation: Optional[datetime] = None
    
    # 品質指標
    knowledge_retention_score: float = 0.0  # 0.0-1.0
    context_accuracy_score: float = 0.0  # 0.0-1.0
    user_satisfaction_score: float = 0.0  # 0.0-1.0
    
    def update_sage_interaction(self, sage_type: SageType):
        """4賢者相互作用カウンタ更新"""
        sage_key = sage_type.value
        self.sage_interactions_count[sage_key] = self.sage_interactions_count.get(sage_key, 0) + 1
        self.last_sage_consultation = datetime.now()
        self.updated_at = datetime.now()
    
    def calculate_efficiency_score(self) -> float:
        """効率性スコア計算"""
        scores = [
            self.compression_ratio,
            min(self.response_time_improvement / 100.0, 1.0),
            self.knowledge_retention_score,
            self.context_accuracy_score
        ]
        return sum(scores) / len(scores)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        data = asdict(self)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.last_sage_consultation:
            data['last_sage_consultation'] = self.last_sage_consultation.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionMetadata':
        """辞書から復元"""
        data['status'] = SessionStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if data.get('last_sage_consultation'):
            data['last_sage_consultation'] = datetime.fromisoformat(data['last_sage_consultation'])
        return cls(**data)

@dataclass
class ContextSnapshot:
    """コンテキストスナップショット"""
    snapshot_id: str
    timestamp: datetime
    conversation_summary: str
    key_decisions: List[Dict[str, Any]]
    active_tasks: List[Dict[str, Any]]
    error_patterns: List[Dict[str, Any]]
    success_patterns: List[Dict[str, Any]]
    
    # 圧縮・要約データ
    original_size: int  # bytes
    compressed_size: int  # bytes
    compression_method: str
    
    # ベクトル化データ
    vector_embeddings: Optional[List[float]] = None
    embedding_model: Optional[str] = None
    similarity_hash: Optional[str] = None
    
    def calculate_compression_ratio(self) -> float:
        """圧縮率計算"""
        if self.original_size == 0:
            return 0.0
        return 1.0 - (self.compressed_size / self.original_size)
    
    def generate_similarity_hash(self) -> str:
        """類似性ハッシュ生成"""
        content = f"{self.conversation_summary}{json.dumps(self.key_decisions, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextSnapshot':
        """辞書から復元"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

@dataclass
class SessionContext:
    """
    PROJECT ELDERZAN メインセッションコンテキスト
    4賢者システム承認済み設計仕様
    """
    
    # 基本情報
    metadata: SessionMetadata
    
    # 構造化データ
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    knowledge_graph: Dict[str, Any] = field(default_factory=dict)
    error_patterns: List[Dict[str, Any]] = field(default_factory=list)
    success_patterns: List[Dict[str, Any]] = field(default_factory=list)
    
    # 4賢者相互作用記録
    sage_interactions: List[SageInteraction] = field(default_factory=list)
    
    # スナップショット履歴
    snapshots: List[ContextSnapshot] = field(default_factory=list)
    
    # キャッシュ・一時データ
    cache_data: Dict[str, Any] = field(default_factory=dict)
    temp_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初期化後処理"""
        if not self.metadata.session_id:
            self.metadata.session_id = self.generate_session_id()
    
    @classmethod
    def create_new(
        cls, 
        user_id: str, 
        project_path: str, 
        session_id: Optional[str] = None
    ) -> 'SessionContext':
        """新規セッションコンテキスト作成"""
        now = datetime.now()
        
        if not session_id:
            session_id = cls.generate_session_id()
        
        metadata = SessionMetadata(
            session_id=session_id,
            user_id=user_id,
            project_path=project_path,
            created_at=now,
            updated_at=now
        )
        
        context = cls(metadata=metadata)
        
        # 初期スナップショット作成
        context.create_snapshot("initial")
        
        return context
    
    @staticmethod
    def generate_session_id() -> str:
        """セッションID生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"elderzan_{timestamp}_{unique_id}"
    
    def add_sage_interaction(self, interaction: SageInteraction):
        """4賢者相互作用記録追加"""
        self.sage_interactions.append(interaction)
        self.metadata.update_sage_interaction(interaction.sage_type)
    
    def create_snapshot(self, description: str = "") -> ContextSnapshot:
        """コンテキストスナップショット作成"""
        snapshot = ContextSnapshot(
            snapshot_id=f"{self.metadata.session_id}_{len(self.snapshots):04d}",
            timestamp=datetime.now(),
            conversation_summary=f"Snapshot {len(self.snapshots) + 1}: {description}",
            key_decisions=[],  # TODO: 実装
            active_tasks=self.tasks.copy(),
            error_patterns=self.error_patterns.copy(),
            success_patterns=self.success_patterns.copy(),
            original_size=0,  # TODO: 実際のサイズ計算
            compressed_size=0,  # TODO: 圧縮サイズ計算
            compression_method="none"
        )
        
        snapshot.similarity_hash = snapshot.generate_similarity_hash()
        self.snapshots.append(snapshot)
        return snapshot
    
    def get_latest_snapshot(self) -> Optional[ContextSnapshot]:
        """最新スナップショット取得"""
        return self.snapshots[-1] if self.snapshots else None
    
    def calculate_total_compression_ratio(self) -> float:
        """総合圧縮率計算"""
        if not self.snapshots:
            return 0.0
        
        total_original = sum(s.original_size for s in self.snapshots)
        total_compressed = sum(s.compressed_size for s in self.snapshots)
        
        if total_original == 0:
            return 0.0
        
        return 1.0 - (total_compressed / total_original)
    
    def get_sage_interaction_summary(self) -> Dict[str, Any]:
        """4賢者相互作用サマリー"""
        summary = {
            "total_interactions": len(self.sage_interactions),
            "by_sage": {},
            "by_type": {},
            "success_rate": 0.0,
            "average_confidence": 0.0,
            "average_processing_time": 0.0
        }
        
        if not self.sage_interactions:
            return summary
        
        # 賢者別集計
        for interaction in self.sage_interactions:
            sage_key = interaction.sage_type.value
            summary["by_sage"][sage_key] = summary["by_sage"].get(sage_key, 0) + 1
            
            type_key = interaction.interaction_type
            summary["by_type"][type_key] = summary["by_type"].get(type_key, 0) + 1
        
        # 品質指標計算
        successful = [i for i in self.sage_interactions if i.success]
        summary["success_rate"] = len(successful) / len(self.sage_interactions)
        summary["average_confidence"] = sum(i.confidence_score for i in self.sage_interactions) / len(self.sage_interactions)
        summary["average_processing_time"] = sum(i.processing_time for i in self.sage_interactions) / len(self.sage_interactions)
        
        return summary
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "metadata": self.metadata.to_dict(),
            "tasks": self.tasks,
            "knowledge_graph": self.knowledge_graph,
            "error_patterns": self.error_patterns,
            "success_patterns": self.success_patterns,
            "sage_interactions": [i.to_dict() for i in self.sage_interactions],
            "snapshots": [s.to_dict() for s in self.snapshots],
            "cache_data": self.cache_data,
            "temp_data": self.temp_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionContext':
        """辞書から復元"""
        metadata = SessionMetadata.from_dict(data["metadata"])
        
        context = cls(
            metadata=metadata,
            tasks=data.get("tasks", []),
            knowledge_graph=data.get("knowledge_graph", {}),
            error_patterns=data.get("error_patterns", []),
            success_patterns=data.get("success_patterns", []),
            cache_data=data.get("cache_data", {}),
            temp_data=data.get("temp_data", {})
        )
        
        # 4賢者相互作用復元
        for interaction_data in data.get("sage_interactions", []):
            interaction = SageInteraction.from_dict(interaction_data)
            context.sage_interactions.append(interaction)
        
        # スナップショット復元
        for snapshot_data in data.get("snapshots", []):
            snapshot = ContextSnapshot.from_dict(snapshot_data)
            context.snapshots.append(snapshot)
        
        return context