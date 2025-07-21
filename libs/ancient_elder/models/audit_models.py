"""
🏛️ Ancient Elder Audit Models
監査データベースモデルの定義
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, 
    DateTime, JSON, Text, ForeignKey, Index,
    UniqueConstraint, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

Base = declarative_base()


class AuditLog(Base):
    """監査ログ記録"""
    __tablename__ = 'ancient_elder_audit_logs'
    
    # Primary key
    audit_id = Column(String(64), primary_key=True)
    
    # 監査情報
    auditor_name = Column(String(100), nullable=False)
    audit_type = Column(String(50), nullable=False)  # integrity, flow_compliance, tdd, etc
    target_type = Column(String(50), nullable=False)  # file, function, commit, issue, etc
    target_id = Column(String(255), nullable=False)
    target_details = Column(JSON, default={})
    
    # タイムスタンプ
    audit_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    processing_time_ms = Column(Float, default=0.0)
    
    # 結果サマリー
    total_violations = Column(Integer, default=0)
    critical_violations = Column(Integer, default=0)
    high_violations = Column(Integer, default=0)
    medium_violations = Column(Integer, default=0)
    low_violations = Column(Integer, default=0)
    
    # メトリクス
    metrics = Column(JSON, default={})
    
    # インデックス
    __table_args__ = (
        Index('idx_audit_timestamp', 'audit_timestamp'),
        Index('idx_auditor_type', 'auditor_name', 'audit_type'),
        Index('idx_target', 'target_type', 'target_id'),
    )
    
    # リレーション
    violations = relationship("Violation", back_populates="audit_log", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "audit_id": self.audit_id,
            "auditor_name": self.auditor_name,
            "audit_type": self.audit_type,
            "target": {
                "type": self.target_type,
                "id": self.target_id,
                "details": self.target_details
            },
            "timestamp": self.audit_timestamp.isoformat(),
            "processing_time_ms": self.processing_time_ms,
            "violation_summary": {
                "total": self.total_violations,
                "critical": self.critical_violations,
                "high": self.high_violations,
                "medium": self.medium_violations,
                "low": self.low_violations
            },
            "metrics": self.metrics,
            "violations": [v.to_dict() for v in self.violations]
        }


class Violation(Base):
    """違反記録"""
    __tablename__ = 'ancient_elder_violations'
    
    # Primary key
    violation_id = Column(String(64), primary_key=True)
    
    # Foreign key
    audit_id = Column(String(64), ForeignKey('ancient_elder_audit_logs.audit_id'), nullable=False)
    
    # 違反情報
    severity = Column(String(20), nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    violation_type = Column(String(100), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    
    # 違反場所
    file_path = Column(String(500))
    line_number = Column(Integer)
    function_name = Column(String(255))
    class_name = Column(String(255))
    
    # 修正提案
    suggested_fix = Column(Text)
    auto_fixable = Column(Boolean, default=False)
    fix_complexity = Column(String(20))  # simple, moderate, complex
    
    # メタデータ
    metadata = Column(JSON, default={})
    tags = Column(JSON, default=[])
    
    # タイムスタンプ
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 制約
    __table_args__ = (
        CheckConstraint("severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')", name='check_severity'),
        Index('idx_violation_severity', 'severity'),
        Index('idx_violation_type', 'violation_type'),
        Index('idx_violation_location', 'file_path', 'line_number'),
    )
    
    # リレーション
    audit_log = relationship("AuditLog", back_populates="violations")
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "violation_id": self.violation_id,
            "severity": self.severity,
            "type": self.violation_type,
            "title": self.title,
            "description": self.description,
            "location": {
                "file_path": self.file_path,
                "line_number": self.line_number,
                "function_name": self.function_name,
                "class_name": self.class_name
            },
            "fix": {
                "suggested": self.suggested_fix,
                "auto_fixable": self.auto_fixable,
                "complexity": self.fix_complexity
            },
            "metadata": self.metadata,
            "tags": self.tags,
            "detected_at": self.detected_at.isoformat()
        }


class AuditThreshold(Base):
    """監査閾値設定"""
    __tablename__ = 'ancient_elder_thresholds'
    
    # Primary key
    threshold_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 設定情報
    auditor_name = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    max_violations = Column(Integer, nullable=False)
    action_type = Column(String(50), nullable=False)  # alert, block, auto_fix
    
    # 有効性
    is_active = Column(Boolean, default=True)
    
    # タイムスタンプ
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 制約
    __table_args__ = (
        UniqueConstraint('auditor_name', 'severity', name='uq_auditor_severity'),
        CheckConstraint("severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')", name='check_threshold_severity'),
    )


class AuditMetric(Base):
    """監査メトリクス時系列データ"""
    __tablename__ = 'ancient_elder_metrics'
    
    # Primary key
    metric_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # メトリクス情報
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50))
    
    # 関連情報
    auditor_name = Column(String(100), nullable=False)
    target_type = Column(String(50))
    target_id = Column(String(255))
    
    # タイムスタンプ
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # メタデータ
    tags = Column(JSON, default=[])
    context = Column(JSON, default={})
    
    # インデックス
    __table_args__ = (
        Index('idx_metric_name_time', 'metric_name', 'recorded_at'),
        Index('idx_metric_auditor', 'auditor_name', 'metric_name'),
    )


class ComplianceReport(Base):
    """コンプライアンスレポート"""
    __tablename__ = 'ancient_elder_compliance_reports'
    
    # Primary key
    report_id = Column(String(64), primary_key=True)
    
    # レポート情報
    report_type = Column(String(50), nullable=False)  # daily, weekly, monthly, on_demand
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # スコア情報
    guild_health_score = Column(Float, nullable=False)
    integrity_score = Column(Float, default=100.0)
    process_score = Column(Float, default=100.0)
    quality_score = Column(Float, default=100.0)
    collaboration_score = Column(Float, default=100.0)
    
    # 違反サマリー
    total_audits = Column(Integer, default=0)
    total_violations = Column(Integer, default=0)
    violations_by_severity = Column(JSON, default={})
    violations_by_type = Column(JSON, default={})
    
    # トレンド
    score_trend = Column(String(20))  # improving, stable, declining
    critical_issues = Column(JSON, default=[])
    recommendations = Column(JSON, default=[])
    
    # 生成情報
    generated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    generated_by = Column(String(100), default='AncientElderAuditEngine')
    
    # メタデータ
    metadata = Column(JSON, default={})
    
    # インデックス
    __table_args__ = (
        Index('idx_report_period', 'period_start', 'period_end'),
        Index('idx_report_type', 'report_type', 'generated_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "report_id": self.report_id,
            "report_type": self.report_type,
            "period": {
                "start": self.period_start.isoformat(),
                "end": self.period_end.isoformat()
            },
            "scores": {
                "guild_health": self.guild_health_score,
                "integrity": self.integrity_score,
                "process": self.process_score,
                "quality": self.quality_score,
                "collaboration": self.collaboration_score
            },
            "violations": {
                "total": self.total_violations,
                "by_severity": self.violations_by_severity,
                "by_type": self.violations_by_type
            },
            "analysis": {
                "trend": self.score_trend,
                "critical_issues": self.critical_issues,
                "recommendations": self.recommendations
            },
            "generated": {
                "at": self.generated_at.isoformat(),
                "by": self.generated_by
            },
            "metadata": self.metadata
        }


# ビューモデル（集計用）
class ViolationTrend(Base):
    """違反トレンドビュー"""
    __tablename__ = 'ancient_elder_violation_trends_view'
    __table_args__ = {'info': {'is_view': True}}
    
    date = Column(DateTime, primary_key=True)
    auditor_name = Column(String(100), primary_key=True)
    severity = Column(String(20), primary_key=True)
    violation_count = Column(Integer)
    
    @classmethod
    def create_view_sql(cls):
        """ビュー作成SQL"""
        return """
        CREATE OR REPLACE VIEW ancient_elder_violation_trends_view AS
        SELECT 
            DATE_TRUNC('day', v.detected_at) as date,
            al.auditor_name,
            v.severity,
            COUNT(*) as violation_count
        FROM ancient_elder_violations v
        JOIN ancient_elder_audit_logs al ON v.audit_id = al.audit_id
        GROUP BY DATE_TRUNC('day', v.detected_at), al.auditor_name, v.severity
        ORDER BY date DESC, auditor_name, severity;
        """