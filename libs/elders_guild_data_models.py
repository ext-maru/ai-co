"""
Elders Guild Unified Data Models - 統一データモデルシステム
Created: 2025-07-11
Author: Claude Elder
"""

from typing import Dict, List, Optional, Any, Union, Type, get_type_hints
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
from abc import ABC, abstractmethod
import asyncio
from contextlib import asynccontextmanager

from pydantic import BaseModel, Field, ConfigDict, validator, root_validator
from sqlalchemy import Column, String, DateTime, Integer, Float, Boolean, Text, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
import sqlalchemy as sa

# ============================================================================
# Base Types and Enums
# ============================================================================

class SageType(Enum):
    """4賢者タイプ"""
    KNOWLEDGE = "knowledge"
    TASK = "task"
    INCIDENT = "incident"
    RAG = "rag"

class DataStatus(Enum):
    """データ状態"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"
    DELETED = "deleted"

class DataPriority(Enum):
    """データ優先度"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class AccessLevel(Enum):
    """アクセスレベル"""
    PUBLIC = "public"
    PROTECTED = "protected"
    PRIVATE = "private"
    RESTRICTED = "restricted"

# ============================================================================
# Pydantic Base Models
# ============================================================================

class BaseDataModel(BaseModel):
    """基底データモデル"""
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        extra="forbid",
        use_enum_values=True
    )

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="ユニークID")
    created_at: Optional[datetime] = Field(default_factory=datetime.now, description="作成日時")
    updated_at: Optional[datetime] = Field(default_factory=datetime.now, description="更新日時")
    created_by: Optional[str] = Field(None, description="作成者")
    updated_by: Optional[str] = Field(None, description="更新者")
    version: int = Field(default=1, description="バージョン番号")

    # メタデータ
    metadata: Dict[str, Any] = Field(default_factory=dict, description="メタデータ")
    tags: List[str] = Field(default_factory=list, description="タグ")

    # ステータス
    status: DataStatus = Field(default=DataStatus.ACTIVE, description="データ状態")
    priority: DataPriority = Field(default=DataPriority.NORMAL, description="優先度")
    access_level: AccessLevel = Field(default=AccessLevel.PUBLIC, description="アクセスレベル")

    @validator('updated_at', pre=True, always=True)
    def set_updated_at(cls, v):
        """更新日時の自動設定"""
        return v or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return self.model_dump(mode='json')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseDataModel':
        """辞書から復元"""
        return cls(**data)

class TimestampedModel(BaseDataModel):
    """タイムスタンプ付きモデル"""
    started_at: Optional[datetime] = Field(None, description="開始日時")
    completed_at: Optional[datetime] = Field(None, description="完了日時")
    deadline: Optional[datetime] = Field(None, description="締切日時")

    @property
    def duration(self) -> Optional[timedelta]:
        """実行時間の計算"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    @property
    def is_overdue(self) -> bool:
        """期限切れかどうか"""
        if self.deadline:
            return datetime.now() > self.deadline
        return False

# ============================================================================
# Knowledge Sage Models
# ============================================================================

class KnowledgeCategory(BaseDataModel):
    """知識カテゴリ"""
    name: str = Field(..., description="カテゴリ名")
    description: Optional[str] = Field(None, description="説明")
    parent_id: Optional[str] = Field(None, description="親カテゴリID")
    display_order: int = Field(default=0, description="表示順序")

    # 統計情報
    knowledge_count: int = Field(default=0, description="知識数")
    total_access_count: int = Field(default=0, description="総アクセス数")

class KnowledgeEntity(BaseDataModel):
    """知識エンティティ"""
    title: str = Field(..., max_length=500, description="タイトル")
    content: str = Field(..., description="内容")
    content_type: str = Field(default="text", description="コンテンツタイプ")
    summary: Optional[str] = Field(None, max_length=1000, description="要約")

    # 分類
    category_id: Optional[str] = Field(None, description="カテゴリID")

    # 品質・評価
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0, description="品質スコア")
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="関連性スコア")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="信頼度スコア")

    # 階層構造
    parent_id: Optional[str] = Field(None, description="親知識ID")
    children_ids: List[str] = Field(default_factory=list, description="子知識IDリスト")

    # 統計情報
    access_count: int = Field(default=0, description="アクセス数")
    last_accessed: Optional[datetime] = Field(None, description="最終アクセス日時")
    usage_count: int = Field(default=0, description="使用回数")

    # 検索・AI関連
    embedding_vector: Optional[List[float]] = Field(None, description="埋め込みベクトル")
    keywords: List[str] = Field(default_factory=list, description="キーワード")
    search_terms: List[str] = Field(default_factory=list, description="検索語句")

    # 関係性
    related_knowledge_ids: List[str] = Field(default_factory=list, description="関連知識IDリスト")
    source_references: List[str] = Field(default_factory=list, description="参照元")

    @validator('quality_score', 'relevance_score', 'confidence_score')
    def validate_score_range(cls, v):
        """スコアの範囲検証"""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Score must be between 0.0 and 1.0')
        return v

class KnowledgeRelationship(BaseDataModel):
    """知識関係"""
    source_id: str = Field(..., description="元知識ID")
    target_id: str = Field(..., description="対象知識ID")
    relationship_type: str = Field(..., description="関係タイプ")
    strength: float = Field(default=1.0, ge=0.0, le=1.0, description="関係の強さ")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="信頼度")

    # 関係の詳細
    description: Optional[str] = Field(None, description="関係の説明")
    evidence: Optional[str] = Field(None, description="根拠")

    # 双方向関係
    is_bidirectional: bool = Field(default=False, description="双方向関係かどうか")

    class Config:
        # 一意制約のためのインデックス
        unique_together = ['source_id', 'target_id', 'relationship_type']

# ============================================================================
# Task Sage Models
# ============================================================================

class TaskCategory(BaseDataModel):
    """タスクカテゴリ"""
    name: str = Field(..., description="カテゴリ名")
    description: Optional[str] = Field(None, description="説明")
    color: Optional[str] = Field(None, description="表示色")
    icon: Optional[str] = Field(None, description="アイコン")

    # 設定
    default_priority: DataPriority = Field(default=DataPriority.NORMAL, description="デフォルト優先度")
    estimated_duration: Optional[int] = Field(None, description="推定所要時間（分）")

    # 統計情報
    task_count: int = Field(default=0, description="タスク数")
    completed_count: int = Field(default=0, description="完了数")

    @property
    def completion_rate(self) -> float:
        """完了率"""
        if self.task_count == 0:
            return 0.0
        return self.completed_count / self.task_count

class TaskEntity(TimestampedModel):
    """タスクエンティティ"""
    name: str = Field(..., max_length=200, description="タスク名")
    description: Optional[str] = Field(None, description="説明")

    # 分類
    category_id: Optional[str] = Field(None, description="カテゴリID")

    # 実行情報
    assigned_to: Optional[str] = Field(None, description="担当者")
    assigned_sage: Optional[SageType] = Field(None, description="担当賢者")

    # 依存関係
    dependencies: List[str] = Field(default_factory=list, description="依存タスクIDリスト")
    dependents: List[str] = Field(default_factory=list, description="依存されるタスクIDリスト")

    # リソース
    resource_requirements: Dict[str, Any] = Field(default_factory=dict, description="リソース要件")
    allocated_resources: Dict[str, Any] = Field(default_factory=dict, description="割り当てリソース")

    # 実行結果
    result: Optional[Dict[str, Any]] = Field(None, description="実行結果")
    output: Optional[str] = Field(None, description="出力")
    error_message: Optional[str] = Field(None, description="エラーメッセージ")

    # 統計情報
    execution_time: Optional[float] = Field(None, description="実行時間（秒）")
    retry_count: int = Field(default=0, description="リトライ回数")
    max_retries: int = Field(default=3, description="最大リトライ回数")

    # 進捗
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="進捗率")

    @property
    def can_start(self) -> bool:
        """実行可能かどうか"""
        # 依存関係がすべて完了している場合のみ実行可能
        # 実際の実装では依存タスクの状態をチェック
        return len(self.dependencies) == 0 or self.status == DataStatus.ACTIVE

class TaskWorkflow(BaseDataModel):
    """タスクワークフロー"""
    name: str = Field(..., description="ワークフロー名")
    description: Optional[str] = Field(None, description="説明")

    # ワークフロー定義
    definition: Dict[str, Any] = Field(..., description="ワークフロー定義（DAG）")

    # 実行情報
    is_active: bool = Field(default=True, description="アクティブかどうか")
    execution_count: int = Field(default=0, description="実行回数")
    success_count: int = Field(default=0, description="成功回数")

    # スケジュール
    schedule: Optional[str] = Field(None, description="スケジュール（cron形式）")
    next_run: Optional[datetime] = Field(None, description="次回実行日時")

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.execution_count == 0:
            return 0.0
        return self.success_count / self.execution_count

# ============================================================================
# Incident Sage Models
# ============================================================================

class IncidentCategory(BaseDataModel):
    """インシデントカテゴリ"""
    name: str = Field(..., description="カテゴリ名")
    description: Optional[str] = Field(None, description="説明")

    # 設定
    default_severity: str = Field(default="medium", description="デフォルト重要度")
    auto_escalation_time: Optional[int] = Field(None, description="自動エスカレーション時間（分）")

    # 統計情報
    incident_count: int = Field(default=0, description="インシデント数")
    resolved_count: int = Field(default=0, description="解決済み数")
    avg_resolution_time: Optional[float] = Field(None, description="平均解決時間（分）")

class IncidentEntity(TimestampedModel):
    """インシデントエンティティ"""
    title: str = Field(..., max_length=200, description="タイトル")
    description: str = Field(..., description="説明")

    # 分類
    category_id: Optional[str] = Field(None, description="カテゴリID")

    # 重要度・影響度
    severity: str = Field(..., description="重要度")
    impact_level: str = Field(..., description="影響レベル")
    urgency: str = Field(..., description="緊急度")

    # 影響範囲
    affected_systems: List[str] = Field(default_factory=list, description="影響システム")
    affected_users: List[str] = Field(default_factory=list, description="影響ユーザー")

    # 担当者
    assignee: Optional[str] = Field(None, description="担当者")
    resolver: Optional[str] = Field(None, description="解決者")

    # 対応状況
    acknowledged_at: Optional[datetime] = Field(None, description="認知日時")
    resolved_at: Optional[datetime] = Field(None, description="解決日時")

    # 解決情報
    root_cause: Optional[str] = Field(None, description="根本原因")
    resolution: Optional[str] = Field(None, description="解決策")
    prevention_measures: Optional[str] = Field(None, description="予防策")

    # 統計情報
    escalation_count: int = Field(default=0, description="エスカレーション回数")
    reopen_count: int = Field(default=0, description="再発回数")

    @property
    def resolution_time(self) -> Optional[timedelta]:
        """解決時間"""
        if self.started_at and self.resolved_at:
            return self.resolved_at - self.started_at
        return None

    @property
    def is_critical(self) -> bool:
        """クリティカルかどうか"""
        return self.severity in ["critical", "high"]

class IncidentMetric(BaseDataModel):
    """インシデントメトリクス"""
    metric_name: str = Field(..., description="メトリクス名")
    value: float = Field(..., description="値")
    unit: Optional[str] = Field(None, description="単位")

    # 時系列情報
    timestamp: datetime = Field(..., description="タイムスタンプ")

    # 関連情報
    incident_id: Optional[str] = Field(None, description="関連インシデントID")
    source: Optional[str] = Field(None, description="データソース")

    # 閾値
    threshold: Optional[float] = Field(None, description="閾値")
    warning_threshold: Optional[float] = Field(None, description="警告閾値")

    @property
    def is_over_threshold(self) -> bool:
        """閾値超過かどうか"""
        if self.threshold is not None:
            return self.value > self.threshold
        return False

# ============================================================================
# RAG Sage Models
# ============================================================================

class DocumentEntity(BaseDataModel):
    """文書エンティティ"""
    title: Optional[str] = Field(None, max_length=500, description="タイトル")
    content: str = Field(..., description="内容")
    content_type: str = Field(default="text", description="コンテンツタイプ")

    # ソース情報
    source: Optional[str] = Field(None, description="ソース")
    source_url: Optional[str] = Field(None, description="ソースURL")
    language: str = Field(default="ja", description="言語")

    # ハッシュ
    content_hash: str = Field(..., description="コンテンツハッシュ")

    # 検索・AI関連
    embedding_vector: Optional[List[float]] = Field(None, description="埋め込みベクトル")

    # 品質情報
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0, description="品質スコア")
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="関連性スコア")

    # 統計情報
    access_count: int = Field(default=0, description="アクセス数")
    last_accessed: Optional[datetime] = Field(None, description="最終アクセス日時")

    # インデックス情報
    indexed_at: Optional[datetime] = Field(None, description="インデックス日時")

    @validator('content_hash')
    def validate_content_hash(cls, v):
        """コンテンツハッシュの検証"""
        if len(v) != 64:  # SHA256想定
            raise ValueError('Content hash must be 64 characters')
        return v

class RAGContext(BaseDataModel):
    """RAGコンテキスト"""
    session_id: str = Field(..., description="セッションID")
    user_id: Optional[str] = Field(None, description="ユーザーID")

    # クエリ情報
    query: str = Field(..., description="クエリ")
    query_type: str = Field(default="general", description="クエリタイプ")
    query_embedding: Optional[List[float]] = Field(None, description="クエリ埋め込み")

    # 検索結果
    retrieved_documents: List[str] = Field(default_factory=list, description="検索文書IDリスト")
    search_results: Optional[Dict[str, Any]] = Field(None, description="検索結果")

    # 回答情報
    response: Optional[str] = Field(None, description="回答")
    response_quality: Optional[float] = Field(None, ge=0.0, le=1.0, description="回答品質")

    # フィードバック
    user_feedback: Optional[int] = Field(None, ge=1, le=5, description="ユーザーフィードバック")
    feedback_text: Optional[str] = Field(None, description="フィードバックテキスト")

    # 統計情報
    response_time: Optional[float] = Field(None, description="応答時間（秒）")
    token_count: Optional[int] = Field(None, description="トークン数")

    @property
    def is_satisfied(self) -> bool:
        """満足度が高いかどうか"""
        if self.user_feedback is not None:
            return self.user_feedback >= 4
        return False

class RAGSession(BaseDataModel):
    """RAGセッション"""
    user_id: Optional[str] = Field(None, description="ユーザーID")

    # セッション情報
    session_type: str = Field(default="chat", description="セッションタイプ")
    context_ids: List[str] = Field(default_factory=list, description="コンテキストIDリスト")

    # 統計情報
    query_count: int = Field(default=0, description="クエリ数")
    avg_response_time: Optional[float] = Field(None, description="平均応答時間")
    satisfaction_score: Optional[float] = Field(None, description="満足度スコア")

    # セッション制御
    is_active: bool = Field(default=True, description="アクティブかどうか")
    ended_at: Optional[datetime] = Field(None, description="終了日時")

    @property
    def duration(self) -> Optional[timedelta]:
        """セッション継続時間"""
        end_time = self.ended_at or datetime.now()
        return end_time - self.created_at

# ============================================================================
# Unified Data Manager
# ============================================================================

class UnifiedDataManager:
    """統一データマネージャー"""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.model_registry = {
            # Knowledge Sage
            'knowledge_category': KnowledgeCategory,
            'knowledge_entity': KnowledgeEntity,
            'knowledge_relationship': KnowledgeRelationship,

            # Task Sage
            'task_category': TaskCategory,
            'task_entity': TaskEntity,
            'task_workflow': TaskWorkflow,

            # Incident Sage
            'incident_category': IncidentCategory,
            'incident_entity': IncidentEntity,
            'incident_metric': IncidentMetric,

            # RAG Sage
            'document_entity': DocumentEntity,
            'rag_context': RAGContext,
            'rag_session': RAGSession,
        }

    def get_model_class(self, model_name: str) -> Type[BaseDataModel]:
        """モデルクラスの取得"""
        if model_name not in self.model_registry:
            raise ValueError(f"Unknown model: {model_name}")
        return self.model_registry[model_name]

    async def create_entity(self, model_name: str, data: Dict[str, Any]) -> BaseDataModel:
        """エンティティの作成"""
        model_class = self.get_model_class(model_name)
        entity = model_class(**data)

        # データベースに保存
        await self._save_entity(entity)

        return entity

    async def get_entity(self, model_name: str, entity_id: str) -> Optional[BaseDataModel]:
        """エンティティの取得"""
        model_class = self.get_model_class(model_name)

        # データベースから取得
        data = await self._load_entity(model_name, entity_id)
        if data:
            return model_class.from_dict(data)

        return None

    async def update_entity(self, model_name: str, entity_id: str, updates: Dict[str, Any]) -> bool:
        """エンティティの更新"""
        entity = await self.get_entity(model_name, entity_id)
        if not entity:
            return False

        # 更新データの適用
        for key, value in updates.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

        # バージョン更新
        entity.version += 1
        entity.updated_at = datetime.now()

        # データベースに保存
        await self._save_entity(entity)

        return True

    async def delete_entity(self, model_name: str, entity_id: str) -> bool:
        """エンティティの削除"""
        entity = await self.get_entity(model_name, entity_id)
        if not entity:
            return False

        # 論理削除
        entity.status = DataStatus.DELETED
        entity.updated_at = datetime.now()

        # データベースに保存
        await self._save_entity(entity)

        return True

    async def list_entities(self, model_name: str,
                          filters: Optional[Dict[str, Any]] = None,
                          limit: int = 100,
                          offset: int = 0) -> List[BaseDataModel]:
        """エンティティの一覧取得"""
        model_class = self.get_model_class(model_name)

        # データベースから取得
        data_list = await self._load_entities(model_name, filters, limit, offset)

        entities = []
        for data in data_list:
            entities.append(model_class.from_dict(data))

        return entities

    async def _save_entity(self, entity: BaseDataModel):
        """エンティティの保存"""
        # 実際のデータベース保存処理
        # 現在は簡易実装
        pass

    async def _load_entity(self, model_name: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """エンティティの読み込み"""
        # 実際のデータベース読み込み処理
        # 現在は簡易実装
        return None

    async def _load_entities(self, model_name: str,
                           filters: Optional[Dict[str, Any]] = None,
                           limit: int = 100,
                           offset: int = 0) -> List[Dict[str, Any]]:
        """エンティティの一覧読み込み"""
        # 実際のデータベース読み込み処理
        # 現在は簡易実装
        return []

    async def validate_entity(self, model_name: str, data: Dict[str, Any]) -> bool:
        """エンティティの検証"""
        try:
            model_class = self.get_model_class(model_name)
            entity = model_class(**data)
            return True
        except Exception:
            return False

    def get_model_schema(self, model_name: str) -> Dict[str, Any]:
        """モデルスキーマの取得"""
        model_class = self.get_model_class(model_name)
        return model_class.model_json_schema()

    def get_all_models(self) -> Dict[str, Type[BaseDataModel]]:
        """全モデルの取得"""
        return self.model_registry.copy()

# ============================================================================
# Usage Example
# ============================================================================

async def main():
    """使用例"""
    from .elders_guild_db_manager import EldersGuildDatabaseManager, DatabaseConfig

    # データベース設定
    db_config = DatabaseConfig()
    db_manager = EldersGuildDatabaseManager(db_config)

    # 統一データマネージャー
    data_manager = UnifiedDataManager(db_manager)

    # 知識エンティティの作成
    knowledge_data = {
        "title": "エルダーズギルド アーキテクチャ",
        "content": "4つの賢者が連携するAI統合プラットフォームの設計について...",
        "category_id": "architecture",
        "quality_score": 0.95,
        "keywords": ["architecture", "AI", "platform", "elders"],
        "tags": ["system", "design", "elders-guild"]
    }

    knowledge = await data_manager.create_entity("knowledge_entity", knowledge_data)
    print(f"Created knowledge: {knowledge.title}")

    # タスクエンティティの作成
    task_data = {
        "name": "データベース最適化",
        "description": "PostgreSQLのパフォーマンスチューニングを実施",
        "priority": DataPriority.HIGH,
        "assigned_to": "Claude Elder",
        "deadline": datetime.now() + timedelta(days=7)
    }

    task = await data_manager.create_entity("task_entity", task_data)
    print(f"Created task: {task.name}")

    # モデルスキーマの取得
    schema = data_manager.get_model_schema("knowledge_entity")
    print(f"Knowledge entity schema: {schema}")

if __name__ == "__main__":
    asyncio.run(main())
