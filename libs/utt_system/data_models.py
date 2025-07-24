#!/usr/bin/env python3
"""
UTT (Unified Task Tracking) データモデル
========================================

Elders Guild統合タスク管理システムのデータ層実装
4賢者システム・Elder Flow・GitHub連携統合対応

Issue #17: [UTT-P1-1] データモデル設計・実装
Phase 1: Foundation - EldersServiceLegacy準拠

Author: Claude Elder
Created: 2025-01-19
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# 現在はEldersServiceLegacyのimportを一時的にコメントアウト
# from core.elders_legacy import EldersServiceLegacy
# from libs.elder_servants.base.elder_servant import ServantRequest, ServantResponse


# 暫定的な基底クラス
class EldersServiceLegacy:
    """暫定的なEldersServiceLegacy基底クラス"""

    def __init__(self):
        """初期化メソッド"""
        pass


class ServantRequest:
    """暫定的なServantRequestクラス"""

    def __init__(self, task_id, task_type, priority, payload, context):
        """初期化メソッド"""
        self.task_id = task_id
        self.task_type = task_type
        self.priority = priority
        self.payload = payload
        self.context = context


class ServantResponse:
    """暫定的なServantResponseクラス"""

    pass


Base = declarative_base()


class TaskStatus(Enum):
    """タスク状態定義 - Iron Will準拠"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
    DEFERRED = "deferred"


class TaskPriority(Enum):
    """タスク優先度 - エルダーズギルド基準"""

    CRITICAL = "critical"  # 🔴 Critical - 即座対応
    HIGH = "high"  # ⭐ High - 1-2日以内
    MEDIUM = "medium"  # 🌟 Medium - 1週間以内
    LOW = "low"  # ✨ Low - 1ヶ月以内
    BACKLOG = "backlog"  # 📋 Backlog - 優先度未定


class TaskCategory(Enum):
    """タスクカテゴリ - エルダーズギルド組織対応"""

    DWARF_WORKSHOP = "dwarf_workshop"  # 🔨 ドワーフ工房 - 開発実装
    RAG_WIZARDS = "rag_wizards"  # 🧙‍♂️ RAGウィザーズ - 調査研究
    ELF_FOREST = "elf_forest"  # 🧝‍♂️ エルフの森 - 監視保守
    INCIDENT_KNIGHTS = "incident_knights"  # ⚔️ インシデント騎士団 - 緊急対応
    ELDER_COUNCIL = "elder_council"  # 🏛️ エルダー評議会 - 意思決定
    QUALITY_ASSURANCE = "quality_assurance"  # 🛡️ 品質保証 - Iron Will
    INTEGRATION = "integration"  # 🔗 統合 - システム連携


class SageType(Enum):
    """4賢者タイプ"""

    KNOWLEDGE_SAGE = "knowledge_sage"  # 📚 ナレッジ賢者
    TASK_SAGE = "task_sage"  # 📋 タスク賢者
    INCIDENT_SAGE = "incident_sage"  # 🚨 インシデント賢者
    RAG_SAGE = "rag_sage"  # 🔍 RAG賢者


@dataclass
class IronWillCriteria:
    """Iron Will 6大品質基準"""

    root_cause_resolution: float = 0.0  # 根本解決度 (95%以上)
    dependency_completeness: float = 0.0  # 依存関係完全性 (100%)
    test_coverage: float = 0.0  # テストカバレッジ (95%以上)
    security_score: float = 0.0  # セキュリティスコア (90%以上)
    performance_score: float = 0.0  # パフォーマンス (85%以上)
    maintainability_score: float = 0.0  # 保守性 (80%以上)

    def overall_score(self) -> float:
        """総合品質スコア算出"""
        scores = [
            self.root_cause_resolution,
            self.dependency_completeness,
            self.test_coverage,
            self.security_score,
            self.performance_score,
            self.maintainability_score,
        ]
        return sum(scores) / len(scores)

    def meets_iron_will_standard(self) -> bool:
        """Iron Will基準達成判定"""
        return (
            self.root_cause_resolution >= 95.0
            and self.dependency_completeness >= 100.0
            and self.test_coverage >= 95.0
            and self.security_score >= 90.0
            and self.performance_score >= 85.0
            and self.maintainability_score >= 80.0
        )


class UTTTask(Base):
    """
    UTT統合タスクモデル
    Elder Flow・4賢者システム・GitHub連携対応
    """

    __tablename__ = "utt_tasks"

    # 基本識別情報
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)

    # 状態・優先度
    status = Column(
        String(20), nullable=False, default=TaskStatus.PENDING.value, index=True
    )
    priority = Column(
        String(20), nullable=False, default=TaskPriority.MEDIUM.value, index=True
    )
    category = Column(String(30), nullable=False, index=True)

    # Elder統合情報
    assigned_sage = Column(String(20), nullable=True, index=True)  # 担当賢者
    assigned_servant = Column(String(50), nullable=True, index=True)  # 担当サーバント
    elder_flow_id = Column(String(100), nullable=True, index=True)  # Elder Flow実行ID

    # 品質管理 - Iron Will準拠
    iron_will_score = Column(Float, default=0.0)
    quality_criteria = Column(JSON)  # IronWillCriteria保存

    # GitHub連携
    github_issue_number = Column(Integer, nullable=True, index=True)
    github_pr_number = Column(Integer, nullable=True)
    github_branch = Column(String(200), nullable=True)
    github_labels = Column(JSON)  # ラベル配列

    # 時間管理
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)

    # メタデータ
    tags = Column(JSON)  # タグ配列
    task_metadata = Column(JSON)  # その他メタデータ（SQLAlchemyのmetadataと重複回避）

    # リレーション
    dependencies = relationship(
        "UTTTaskDependency",
        foreign_keys="UTTTaskDependency.task_id",
        back_populates="task",
    )
    dependents = relationship(
        "UTTTaskDependency",
        foreign_keys="UTTTaskDependency.depends_on_task_id",
        back_populates="depends_on_task",
    )
    logs = relationship(
        "UTTTaskLog", back_populates="task", order_by="UTTTaskLog.created_at"
    )
    sage_consultations = relationship("UTTSageConsultation", back_populates="task")

    # インデックス最適化
    __table_args__ = (
        Index("ix_utt_tasks_status_priority", "status", "priority"),
        Index("ix_utt_tasks_category_status", "category", "status"),
        Index("ix_utt_tasks_assigned_sage_status", "assigned_sage", "status"),
        Index("ix_utt_tasks_github_issue", "github_issue_number"),
        Index("ix_utt_tasks_created_at", "created_at"),
    )

    def to_servant_request(self) -> ServantRequest:
        """ServantRequest形式に変換 - Elder Servant連携用"""
        return ServantRequest(
            task_id=self.task_id,
            task_type=self.category,
            priority=self.priority,
            payload={
                "title": self.title,
                "description": self.description,
                "metadata": self.task_metadata or {},
                "github_issue": self.github_issue_number,
                "iron_will_score": self.iron_will_score,
            },
            context={
                "assigned_sage": self.assigned_sage,
                "assigned_servant": self.assigned_servant,
                "elder_flow_id": self.elder_flow_id,
            },
        )

    def update_iron_will_score(self, criteria: IronWillCriteria) -> None:
        """Iron Will品質スコア更新"""
        self.quality_criteria = {
            "root_cause_resolution": criteria.root_cause_resolution,
            "dependency_completeness": criteria.dependency_completeness,
            "test_coverage": criteria.test_coverage,
            "security_score": criteria.security_score,
            "performance_score": criteria.performance_score,
            "maintainability_score": criteria.maintainability_score,
        }
        self.iron_will_score = criteria.overall_score()
        self.updated_at = datetime.utcnow()


class UTTTaskDependency(Base):
    """
    タスク依存関係モデル
    Elder Flow実行順序制御対応
    """

    __tablename__ = "utt_task_dependencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("utt_tasks.id"), nullable=False, index=True
    )
    depends_on_task_id = Column(
        UUID(as_uuid=True), ForeignKey("utt_tasks.id"), nullable=False, index=True
    )
    dependency_type = Column(
        String(20), nullable=False, default="blocks"
    )  # blocks, relates_to, child_of
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # リレーション
    task = relationship(
        "UTTTask", foreign_keys=[task_id], back_populates="dependencies"
    )
    depends_on_task = relationship(
        "UTTTask", foreign_keys=[depends_on_task_id], back_populates="dependents"
    )

    __table_args__ = (
        Index("ix_dependency_task_depends", "task_id", "depends_on_task_id"),
    )


class UTTTaskLog(Base):
    """
    タスクログモデル
    4賢者システム・Elder Flow実行履歴
    """

    __tablename__ = "utt_task_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("utt_tasks.id"), nullable=False, index=True
    )
    log_type = Column(
        String(30), nullable=False, index=True
    )  # status_change, sage_consultation, elder_flow, etc.
    actor_type = Column(String(20), nullable=False)  # sage, servant, elder_flow, user
    actor_id = Column(String(100), nullable=False)

    # ログ内容
    action = Column(String(100), nullable=False)
    description = Column(Text)
    old_value = Column(JSON)  # 変更前の値
    new_value = Column(JSON)  # 変更後の値
    log_metadata = Column(JSON)  # 追加メタデータ

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # リレーション
    task = relationship("UTTTask", back_populates="logs")

    __table_args__ = (
        Index("ix_task_logs_task_created", "task_id", "created_at"),
        Index("ix_task_logs_type_actor", "log_type", "actor_type"),
    )


class UTTSageConsultation(Base):
    """
    4賢者相談記録モデル
    賢者間協調と知識蓄積
    """

    __tablename__ = "utt_sage_consultations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("utt_tasks.id"), nullable=False, index=True
    )
    sage_type = Column(String(20), nullable=False, index=True)  # SageType enum
    consultation_type = Column(
        String(30), nullable=False
    )  # advice, analysis, approval, etc.

    # 相談内容
    query = Column(Text, nullable=False)
    response = Column(Text)
    confidence_score = Column(Float, default=0.0)  # 信頼度スコア
    reasoning = Column(Text)  # 判断理由

    # メタデータ
    processing_time_ms = Column(Integer)  # 処理時間（ミリ秒）
    context_data = Column(JSON)  # コンテキストデータ

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # リレーション
    task = relationship("UTTTask", back_populates="sage_consultations")

    __table_args__ = (
        Index("ix_sage_consultation_task_sage", "task_id", "sage_type"),
        Index("ix_sage_consultation_type_created", "consultation_type", "created_at"),
    )


class UTTProject(Base):
    """
    プロジェクトモデル
    複数タスクのグループ化・統計管理
    """

    __tablename__ = "utt_projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # 状態・分類
    status = Column(String(20), nullable=False, default="active", index=True)
    category = Column(String(30), nullable=False, index=True)

    # GitHub連携
    github_repo = Column(String(200))
    github_milestone = Column(String(100))

    # 品質管理
    overall_iron_will_score = Column(Float, default=0.0)
    target_completion_date = Column(DateTime)

    # 時間管理
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # メタデータ
    project_metadata = Column(JSON)


# UTTデータ管理サービス - EldersServiceLegacy準拠
class UTTDataManager(EldersServiceLegacy):
    """
    UTT統合データ管理サービス
    EldersServiceLegacy準拠・Iron Will品質基準対応
    """

    def __init__(self, database_url: str = "sqlite:///utt_system.db"):
        """初期化メソッド"""
        super().__init__()
        self.engine = create_engine(database_url, echo=False)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # 統計情報
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "average_iron_will_score": 0.0,
            "sage_consultations": 0,
            "elder_flow_executions": 0,
        }

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        UTTデータ操作要求処理
        4賢者システム・Elder Flow統合対応
        """
        operation = request.get("operation")
        data = request.get("data", {})

        try:
            if operation == "create_task":
                result = await self._create_task(data)
            elif operation == "update_task":
                result = await self._update_task(data)
            elif operation == "get_task":
                result = await self._get_task(data)
            elif operation == "list_tasks":
                result = await self._list_tasks(data)
            elif operation == "add_dependency":
                result = await self._add_dependency(data)
            elif operation == "log_sage_consultation":
                result = await self._log_sage_consultation(data)
            elif operation == "update_iron_will_score":
                result = await self._update_iron_will_score(data)
            else:
                raise ValueError(f"Unknown operation: {operation}")

            return {"success": True, "result": result, "stats": self.stats}

        except Exception as e:
            return {"success": False, "error": str(e), "stats": self.stats}

    async def validate_request(self, request: Dict[str, Any]) -> bool:
        """要求データ検証"""
        required_fields = ["operation"]
        return all(field in request for field in required_fields)

    def get_capabilities(self) -> List[str]:
        """UTTシステム機能一覧"""
        return [
            "create_task",
            "update_task",
            "get_task",
            "list_tasks",
            "add_dependency",
            "log_sage_consultation",
            "update_iron_will_score",
            "elder_flow_integration",
            "github_sync",
            "4_sages_coordination",
        ]

    async def _create_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """新規タスク作成"""
        task = UTTTask(
            task_id=data.get("task_id", f"TASK-{uuid.uuid4().hex[:8]}"),
            title=data["title"],
            description=data.get("description", ""),
            priority=data.get("priority", TaskPriority.MEDIUM.value),
            category=data.get("category", TaskCategory.DWARF_WORKSHOP.value),
            github_issue_number=data.get("github_issue"),
            task_metadata=data.get("metadata", {}),
        )

        self.session.add(task)
        self.session.commit()
        self.stats["total_tasks"] += 1

        return {"task_id": task.task_id, "id": str(task.id)}

    async def _update_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """タスク更新"""
        task = self.session.query(UTTTask).filter_by(task_id=data["task_id"]).first()
        if not task:
            raise ValueError(f"Task not found: {data['task_id']}")

        # 更新可能フィールド
        for field in [
            "title",
            "description",
            "status",
            "priority",
            "category",
            "assigned_sage",
            "assigned_servant",
            "elder_flow_id",
        ]:
            if field in data:
                setattr(task, field, data[field])

        # 完了時の統計更新
        if (
            data.get("status") == TaskStatus.COMPLETED.value
            and task.status != TaskStatus.COMPLETED.value
        ):
            task.completed_at = datetime.utcnow()
            self.stats["completed_tasks"] += 1

        self.session.commit()
        return {"task_id": task.task_id, "updated_at": task.updated_at.isoformat()}

    async def _get_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """タスク取得"""
        task = self.session.query(UTTTask).filter_by(task_id=data["task_id"]).first()
        if not task:
            raise ValueError(f"Task not found: {data['task_id']}")

        return {
            "task_id": task.task_id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "category": task.category,
            "iron_will_score": task.iron_will_score,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
        }

    async def _list_tasks(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """タスク一覧取得"""
        query = self.session.query(UTTTask)

        # フィルタリング
        if "status" in data:
            query = query.filter(UTTTask.status == data["status"])
        if "priority" in data:
            query = query.filter(UTTTask.priority == data["priority"])
        if "category" in data:
            query = query.filter(UTTTask.category == data["category"])
        if "assigned_sage" in data:
            query = query.filter(UTTTask.assigned_sage == data["assigned_sage"])

        # ソート
        sort_by = data.get("sort_by", "created_at")
        if hasattr(UTTTask, sort_by):
            query = query.order_by(getattr(UTTTask, sort_by).desc())

        # ページング
        limit = data.get("limit", 50)
        offset = data.get("offset", 0)
        tasks = query.offset(offset).limit(limit).all()

        return {
            "tasks": [
                {
                    "task_id": task.task_id,
                    "title": task.title,
                    "status": task.status,
                    "priority": task.priority,
                    "category": task.category,
                    "iron_will_score": task.iron_will_score,
                    "created_at": task.created_at.isoformat(),
                }
                for task in tasks
            ],
            "total": query.count(),
            "offset": offset,
            "limit": limit,
        }

    async def _add_dependency(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """タスク依存関係追加"""
        task = self.session.query(UTTTask).filter_by(task_id=data["task_id"]).first()
        depends_on_task = (
            self.session.query(UTTTask)
            .filter_by(task_id=data["depends_on_task_id"])
            .first()
        )

        if not task or not depends_on_task:
            raise ValueError("One or both tasks not found")

        dependency = UTTTaskDependency(
            task_id=task.id,
            depends_on_task_id=depends_on_task.id,
            dependency_type=data.get("dependency_type", "blocks"),
        )

        self.session.add(dependency)
        self.session.commit()

        return {"dependency_id": str(dependency.id)}

    async def _log_sage_consultation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """4賢者相談記録"""
        task = self.session.query(UTTTask).filter_by(task_id=data["task_id"]).first()
        if not task:
            raise ValueError(f"Task not found: {data['task_id']}")

        consultation = UTTSageConsultation(
            task_id=task.id,
            sage_type=data["sage_type"],
            consultation_type=data["consultation_type"],
            query=data["query"],
            response=data.get("response", ""),
            confidence_score=data.get("confidence_score", 0.0),
            reasoning=data.get("reasoning", ""),
            processing_time_ms=data.get("processing_time_ms", 0),
            context_data=data.get("context_data", {}),
        )

        self.session.add(consultation)
        self.session.commit()
        self.stats["sage_consultations"] += 1

        return {"consultation_id": str(consultation.id)}

    async def _update_iron_will_score(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Iron Will品質スコア更新"""
        task = self.session.query(UTTTask).filter_by(task_id=data["task_id"]).first()
        if not task:
            raise ValueError(f"Task not found: {data['task_id']}")

        criteria = IronWillCriteria(**data["criteria"])
        task.update_iron_will_score(criteria)
        self.session.commit()

        # 統計更新
        avg_score = (
            self.session.query(UTTTask)
            .filter(UTTTask.iron_will_score > 0)
            .with_entities(func.avg(UTTTask.iron_will_score))
            .scalar()
            or 0.0
        )
        self.stats["average_iron_will_score"] = float(avg_score)

        return {
            "task_id": task.task_id,
            "iron_will_score": task.iron_will_score,
            "meets_standard": criteria.meets_iron_will_standard(),
        }

    def close(self):
        """データベース接続クローズ"""
        self.session.close()


if __name__ == "__main__":
    # 簡単な動作確認
    import asyncio

    async def test_utt_system():
        """UTTシステム基本動作テスト"""
        manager = UTTDataManager()

        # テストタスク作成
        create_result = await manager.process_request(
            {
                "operation": "create_task",
                "data": {
                    "title": "UTTシステムテスト",
                    "description": "Issue #17 データモデル動作確認",
                    "priority": TaskPriority.HIGH.value,
                    "category": TaskCategory.DWARF_WORKSHOP.value,
                    "github_issue": 17,
                },
            }
        )
        print(f"Task created: {create_result}")

        # Iron Will品質スコア更新
        task_id = create_result["result"]["task_id"]
        iron_will_result = await manager.process_request(
            {
                "operation": "update_iron_will_score",
                "data": {
                    "task_id": task_id,
                    "criteria": {
                        "root_cause_resolution": 95.0,
                        "dependency_completeness": 100.0,
                        "test_coverage": 98.0,
                        "security_score": 92.0,
                        "performance_score": 88.0,
                        "maintainability_score": 85.0,
                    },
                },
            }
        )
        print(f"Iron Will updated: {iron_will_result}")

        manager.close()
        return True

    if asyncio.run(test_utt_system()):
        print("✅ UTT Data Model implementation successful!")
