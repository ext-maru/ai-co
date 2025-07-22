"""
Incident Sage データモデル
========================

インシデント対応・品質監視に関するデータ構造定義

Author: Claude Elder
Created: 2025-07-22
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import uuid


class IncidentSeverity(Enum):
    """インシデント重要度"""
    CRITICAL = "critical"    # システム停止・重大問題
    HIGH = "high"           # 重要機能影響
    MEDIUM = "medium"       # 部分的影響
    LOW = "low"            # 軽微な問題
    INFO = "info"          # 情報レベル


class IncidentStatus(Enum):
    """インシデントステータス"""
    DETECTED = "detected"         # 検知済み
    INVESTIGATING = "investigating"  # 調査中
    RESOLVING = "resolving"       # 解決中
    RESOLVED = "resolved"         # 解決済み
    CLOSED = "closed"            # 完了
    ESCALATED = "escalated"      # エスカレーション


class IncidentCategory(Enum):
    """インシデントカテゴリ"""
    QUALITY = "quality"           # 品質問題
    SECURITY = "security"         # セキュリティ問題
    PERFORMANCE = "performance"   # パフォーマンス問題
    AVAILABILITY = "availability" # 可用性問題
    COMPLIANCE = "compliance"     # コンプライアンス違反
    INTEGRATION = "integration"   # 統合問題
    DATA = "data"                # データ問題


@dataclass
class Incident:
    """インシデント"""
    incident_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    status: IncidentStatus = IncidentStatus.DETECTED
    category: IncidentCategory = IncidentCategory.QUALITY
    
    # メタデータ
    source: str = "incident_sage"  # インシデント発生源
    affected_components: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    # 時系列
    detected_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    
    # 詳細情報
    root_cause: str = ""
    impact_assessment: str = ""
    resolution_steps: List[str] = field(default_factory=list)
    lessons_learned: str = ""
    
    # メトリクス
    detection_time_ms: Optional[int] = None
    resolution_time_ms: Optional[int] = None
    impact_score: float = 0.0
    confidence_score: float = 0.8


@dataclass
class QualityMetric:
    """品質メトリクス"""
    metric_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    value: float = 0.0
    target_value: float = 0.0
    threshold_min: float = 0.0
    threshold_max: float = 100.0
    
    # メタデータ
    category: str = "general"
    unit: str = ""
    description: str = ""
    
    # 評価
    is_within_threshold: bool = True
    deviation_score: float = 0.0
    trend_direction: str = "stable"  # improving, degrading, stable
    
    # 時系列
    measured_at: datetime = field(default_factory=datetime.now)
    source: str = "incident_sage"


@dataclass
class QualityStandard:
    """品質基準"""
    standard_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    category: str = "general"
    
    # 基準値
    metrics: Dict[str, QualityMetric] = field(default_factory=dict)
    compliance_threshold: float = 95.0  # コンプライアンス閾値(%)
    
    # メタデータ
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # 適用範囲
    applicable_components: List[str] = field(default_factory=list)
    mandatory: bool = True


@dataclass
class QualityAssessment:
    """品質評価結果"""
    assessment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target_component: str = ""
    standard_id: str = ""
    
    # 評価結果
    overall_score: float = 0.0
    compliance_score: float = 0.0
    is_compliant: bool = False
    
    # 詳細評価
    metric_scores: Dict[str, float] = field(default_factory=dict)
    violations: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # メタデータ
    assessed_at: datetime = field(default_factory=datetime.now)
    assessor: str = "incident_sage"
    confidence_score: float = 0.9


@dataclass
class IncidentResponse:
    """インシデント対応記録"""
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    incident_id: str = ""
    
    # 対応内容
    action_type: str = ""  # investigation, mitigation, resolution
    description: str = ""
    execution_steps: List[str] = field(default_factory=list)
    
    # 結果
    status: str = "pending"  # pending, in_progress, completed, failed
    effectiveness_score: float = 0.0
    side_effects: List[str] = field(default_factory=list)
    
    # 時系列
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # メタデータ
    responder: str = "incident_sage"
    priority: int = 1
    automated: bool = True


@dataclass 
class AlertRule:
    """アラートルール"""
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    
    # 条件
    condition_expression: str = ""  # メトリクス条件式
    threshold_value: float = 0.0
    comparison_operator: str = ">"  # >, <, >=, <=, ==, !=
    
    # アラート設定
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    cooldown_minutes: int = 5
    max_alerts_per_hour: int = 12
    
    # 対応
    auto_response_enabled: bool = False
    escalation_rules: List[str] = field(default_factory=list)
    notification_targets: List[str] = field(default_factory=list)
    
    # メタデータ
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_triggered_at: Optional[datetime] = None
    trigger_count: int = 0


@dataclass
class MonitoringTarget:
    """監視対象"""
    target_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: str = ""  # service, component, metric, endpoint
    
    # 設定
    endpoint_url: Optional[str] = None
    check_interval_seconds: int = 60
    timeout_seconds: int = 30
    
    # ヘルスチェック
    health_check_enabled: bool = True
    health_check_path: str = "/health"
    expected_response_codes: List[int] = field(default_factory=lambda: [200])
    
    # 品質監視
    quality_standards: List[str] = field(default_factory=list)
    alert_rules: List[str] = field(default_factory=list)
    
    # メタデータ
    created_at: datetime = field(default_factory=datetime.now)
    last_checked_at: Optional[datetime] = None
    status: str = "unknown"  # healthy, unhealthy, unknown
    uptime_percentage: float = 0.0