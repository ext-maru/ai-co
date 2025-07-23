"""
Incident Sage - インシデント対応・品質監視賢者
============================================

Elder Tree分散AIアーキテクチャの4賢者システム
インシデント検知・対応・品質保証専門AI

Author: Claude Elder
Created: 2025-07-22
"""

import asyncio
import sqlite3
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from statistics import mean, stdev
from dataclasses import asdict

from ..shared_libs.soul_base import BaseSoul
from .abilities.incident_models import (
    Incident, IncidentSeverity, IncidentStatus, IncidentCategory,
    QualityMetric, QualityStandard, QualityAssessment,
    IncidentResponse, AlertRule, MonitoringTarget
)



class IncidentSageSoul(BaseSoul):


"""
    インシデント対応・品質監視賢者
    
    責務:
    - インシデント検知・分析・対応
    - 品質基準管理・評価
    - アラートルール管理
    - 監視対象ヘルスチェック
    - 自動修復・エスカレーション
    - パターン学習・予測的防止
    """ Optional[Path] = None):
        """Incident Sage初期化"""
        super().__init__(
            soul_type="incident_sage",
            domain="incident_management", 
            soul_name="Incident Sage"
        )
        
        # データディレクトリ設定
        self.data_dir = data_dir or Path("data/incident_sage")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # データベース初期化
        self.db_path = self.data_dir / "incident_sage.db"
        self.logger = logging.getLogger(f"incident_sage_{self.soul_id}")
        
        # メモリストレージ
        self.incidents: Dict[str, Incident] = {}
        self.quality_standards: Dict[str, QualityStandard] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.monitoring_targets: Dict[str, MonitoringTarget] = {}
        
        # 運用メトリクス
        self.operational_metrics = {
            "incidents_detected": 0,
            "incidents_resolved": 0,
            "average_resolution_time": 0.0,
            "quality_assessments_performed": 0,
            "alert_rules_active": 0,
            "monitoring_targets_healthy": 0,
            "pattern_learning_count": 0,
            "automated_remediations": 0
        }
        
        # パターン学習
        self.incident_patterns: Dict[str, Any] = {}
        self.correlation_cache: Dict[str, List[str]] = {}
        
        # 初期化実行
        self._initialize_database()
        self._load_default_quality_standards()
        self._load_all_data()
        
        self.logger.info(f"Incident Sage initialized: {self.soul_id}")
    
    async def initialize(self) -> bool:

    
    """魂の初期化処理"""
            self.logger.info(f"Initializing Incident Sage: {self.soul_name}")
            
            # 能力登録
            abilities = [
                "incident_detection", "quality_assessment", "automated_response",
                "alert_management", "pattern_learning", "correlation_analysis",
                "preventive_monitoring", "automated_remediation"
            ]
            
            for ability in abilities:
                self.register_ability(ability)
            
            # 初期データロード確認
            self._update_operational_metrics()
            
            self.logger.info(f"Incident Sage initialized successfully with {len(abilities)} abilities" \
                "Incident Sage initialized successfully with {len(abilities)} abilities" \
                "Incident Sage initialized successfully with {len(abilities)} abilities")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Incident Sage: {e}")
            return False
    
    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """メッセージ処理"""
        try:
            message_type = message.get("type", "unknown")
            self.logger.info(f"Processing message: {message_type}")
            
            if message_type == "incident_alert":
                return await self._handle_incident_alert(message)
            elif message_type == "quality_check_request":
                return await self._handle_quality_check(message)
            elif message_type == "health_check":
                return await self._handle_health_check(message)
            elif message_type == "metrics_request":
                return await self._handle_metrics_request(message)
            elif message_type == "sage_consultation":
                return await self._handle_sage_consultation(message)
            else:
                return self._create_error_response(message, f"Unknown message type: {message_type}")
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return self._create_error_response(message, str(e))
    
    async def shutdown(self):

            """シャットダウン処理"""
            self.logger.info(f"Shutting down Incident Sage: {self.soul_name}")
            
            # アクティブタスクの停止
            for task_id in list(self.context.active_tasks):
                self.context.complete_task(task_id)
            
            # データベース接続クローズ
            # SQLiteは自動でクローズされるが、必要に応じて明示的処理
            
            self.logger.info("Incident Sage shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
    
    def _initialize_database(self):

    
    """データベース初期化"""
            # インシデントテーブル
            conn.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    category TEXT NOT NULL,
                    source TEXT,
                    affected_components TEXT,
                    tags TEXT,
                    detected_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    resolved_at TIMESTAMP,
                    root_cause TEXT,
                    impact_assessment TEXT,
                    resolution_steps TEXT,
                    lessons_learned TEXT,
                    detection_time_ms INTEGER,
                    resolution_time_ms INTEGER,
                    impact_score REAL,
                    confidence_score REAL
                )
            """)
            
            # 品質基準テーブル
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quality_standards (
                    standard_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    metrics_json TEXT,
                    compliance_threshold REAL,
                    version TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    applicable_components TEXT,
                    mandatory BOOLEAN
                )
            """)
            
            # 品質評価テーブル  
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quality_assessments (
                    assessment_id TEXT PRIMARY KEY,
                    target_component TEXT NOT NULL,
                    standard_id TEXT NOT NULL,
                    overall_score REAL,
                    compliance_score REAL,
                    is_compliant BOOLEAN,
                    metric_scores TEXT,
                    violations TEXT,
                    recommendations TEXT,
                    assessed_at TIMESTAMP,
                    assessor TEXT,
                    confidence_score REAL
                )
            """)
            
            # アラートルールテーブル
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alert_rules (
                    rule_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    condition_expression TEXT NOT NULL,
                    threshold_value REAL,
                    comparison_operator TEXT,
                    severity TEXT,
                    cooldown_minutes INTEGER,
                    max_alerts_per_hour INTEGER,
                    auto_response_enabled BOOLEAN,
                    escalation_rules TEXT,
                    notification_targets TEXT,
                    enabled BOOLEAN,
                    created_at TIMESTAMP,
                    last_triggered_at TIMESTAMP,
                    trigger_count INTEGER
                )
            """)
            
            # 監視対象テーブル
            conn.execute("""
                CREATE TABLE IF NOT EXISTS monitoring_targets (
                    target_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    endpoint_url TEXT,
                    check_interval_seconds INTEGER,
                    timeout_seconds INTEGER,
                    health_check_enabled BOOLEAN,
                    health_check_path TEXT,
                    expected_response_codes TEXT,
                    quality_standards TEXT,
                    alert_rules TEXT,
                    created_at TIMESTAMP,
                    last_checked_at TIMESTAMP,
                    status TEXT,
                    uptime_percentage REAL
                )
            """)
            
            conn.commit()
    
    def _load_default_quality_standards(self):

            """デフォルト品質基準ロード""" QualityMetric(
                    name="Test Coverage",
                    target_value=95.0,
                    threshold_min=90.0,
                    unit="%",
                    description="コードテストカバレッジ"
                ),
                "iron_will_compliance": QualityMetric(
                    name="Iron Will Compliance", 
                    target_value=100.0,
                    threshold_min=100.0,
                    unit="%",
                    description="Iron Will原則遵守率"
                ),
                "code_quality_score": QualityMetric(
                    name="Code Quality Score",
                    target_value=90.0,
                    threshold_min=80.0,
                    unit="points",
                    description="コード品質スコア"
                )
            },
            compliance_threshold=95.0,
            applicable_components=["all"]
        )
        
        self.quality_standards[elder_guild_standard.standard_id] = elder_guild_standard
    
    def _load_all_data(self):

                    """全データロード"""
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # インシデントロード
                for row in conn.execute("SELECT * FROM incidents"):
                    incident = self._row_to_incident(row)
                    self.incidents[incident.incident_id] = incident
                
                # 品質基準ロード
                for row in conn.execute("SELECT * FROM quality_standards"):
                    standard = self._row_to_quality_standard(row)
                    self.quality_standards[standard.standard_id] = standard
                
                # アラートルールロード
                for row in conn.execute("SELECT * FROM alert_rules"):
                    rule = self._row_to_alert_rule(row)
                    self.alert_rules[rule.rule_id] = rule
                
                # 監視対象ロード
                for row in conn.execute("SELECT * FROM monitoring_targets"):
                    target = self._row_to_monitoring_target(row)
                    self.monitoring_targets[target.target_id] = target
                
            # 運用メトリクス更新
            self._update_operational_metrics()
            
            self.logger.info(f"Loaded: {len(self.incidents)} incidents, "
                           f"{len(self.quality_standards)} standards, "
                           f"{len(self.alert_rules)} alert rules, "
                           f"{len(self.monitoring_targets)} monitoring targets")
                           
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            raise
    
    async def detect_incident(self, anomaly_data: Dict[str, Any]) -> Incident:
        """インシデント検知"""
        start_time = time.time()
        
        # 異常データから重要度判定
        severity = self._determine_severity(anomaly_data)
        category = self._determine_category(anomaly_data)
        
        # インシデント作成
        incident = Incident(
            title=f"Anomaly detected in {anomaly_data.get('component', 'unknown')}",
            description=self._generate_incident_description(anomaly_data),
            severity=severity,
            category=category,
            affected_components=[anomaly_data.get('component', 'unknown')],
            tags=self._extract_tags(anomaly_data),
            detection_time_ms=int((time.time() - start_time) * 1000),
            confidence_score=anomaly_data.get('confidence', 0.8)
        )
        
        # インシデント登録
        await self.register_incident(incident)
        
        # 自動対応判定
        if severity in [IncidentSeverity.CRITICAL, IncidentSeverity.HIGH]:
            await self._trigger_automatic_response(incident)
        
        self.operational_metrics["incidents_detected"] += 1
        
        self.logger.info(f"Incident detected: {incident.incident_id} ({severity.value})")
        return incident
    
    async def register_incident(self, incident: Incident):
        """インシデント登録"""
        self.incidents[incident.incident_id] = incident
        
        # データベース保存
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO incidents VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                incident.incident_id, incident.title, incident.description,
                incident.severity.value, incident.status.value, incident.category.value,
                incident.source, json.dumps(incident.affected_components),
                json.dumps(incident.tags), incident.detected_at.isoformat(),
                incident.updated_at.isoformat(),
                incident.resolved_at.isoformat() if incident.resolved_at else None,
                incident.root_cause, incident.impact_assessment,
                json.dumps(incident.resolution_steps), incident.lessons_learned,
                incident.detection_time_ms, incident.resolution_time_ms,
                incident.impact_score, incident.confidence_score
            ))
            conn.commit()
    
    async def assess_quality(
        self,
        standard_id: str,
        assessment_data: Dict[str,
        Any]
    ) -> QualityAssessment:

        """品質評価実行"""
            raise ValueError(f"Quality standard not found: {standard_id}")
        
        standard = self.quality_standards[standard_id]
        component = assessment_data["component"]
        metrics = assessment_data["metrics"]
        
        # メトリクススコア計算
        metric_scores = {}
        violations = []
        recommendations = []
        
        for metric_name, metric_def in standard.metrics.items():
            if metric_name in metrics:
                actual_value = metrics[metric_name]
                metric_scores[metric_name] = actual_value
                
                # 閾値チェック
                if actual_value < metric_def.threshold_min:
                    violations.append(f"{metric_name}: {actual_value} < {metric_def.threshold_min}")
                    recommendations.append(f"Improve {metric_name} to meet minimum threshold")
        
        # 総合スコア計算
        overall_score = self._calculate_overall_score(metric_scores, standard)
        compliance_score = (overall_score / 100) * 100
        is_compliant = compliance_score >= standard.compliance_threshold
        
        # 評価結果作成
        assessment = QualityAssessment(
            target_component=component,
            standard_id=standard_id,
            overall_score=overall_score,
            compliance_score=compliance_score,
            is_compliant=is_compliant,
            metric_scores=metric_scores,
            violations=violations,
            recommendations=recommendations
        )
        
        # データベース保存
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO quality_assessments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                assessment.assessment_id, assessment.target_component, assessment.standard_id,
                assessment.overall_score, assessment.compliance_score, assessment.is_compliant,
                json.dumps(assessment.metric_scores), json.dumps(assessment.violations),
                json.dumps(assessment.recommendations), assessment.assessed_at.isoformat(),
                assessment.assessor, assessment.confidence_score
            ))
            conn.commit()
        
        self.operational_metrics["quality_assessments_performed"] += 1
        
        # 品質問題の場合はインシデント生成
        if not is_compliant:
            await self._create_quality_incident(assessment)
        
        self.logger.info(f"Quality assessment completed: {component} -> {overall_score:.1f}%")
        return assessment
    
    async def respond_to_incident(self, incident_id: str) -> IncidentResponse:
        """インシデント対応実行"""
        if incident_id not in self.incidents:
            raise ValueError(f"Incident not found: {incident_id}")
        
        incident = self.incidents[incident_id]
        
        # 対応戦略決定
        response_actions = self._determine_response_actions(incident)
        
        # 対応実行
        response = IncidentResponse(
            incident_id=incident_id,
            action_type="automated_response",
            description=f"Automated response to {incident.severity.value} incident",
            execution_steps=response_actions,
            responder="incident_sage",
            automated=True
        )
        
        # 実際の対応実行
        success = await self._execute_response_actions(response_actions, incident)
        
        if success:
            response.status = "completed"
            response.effectiveness_score = 0.8
            incident.status = IncidentStatus.RESOLVED
            incident.resolved_at = datetime.now()
            self.operational_metrics["incidents_resolved"] += 1
        else:
            response.status = "failed"
            response.effectiveness_score = 0.2
            incident.status = IncidentStatus.ESCALATED
        
        response.completed_at = datetime.now()
        
        # 更新保存
        await self.register_incident(incident)
        
        self.logger.info(f"Incident response: {incident_id} -> {response.status}")
        return response
    
    async def create_alert_rule(self, alert_rule: AlertRule):
        """アラートルール作成"""
        self.alert_rules[alert_rule.rule_id] = alert_rule
        
        # データベース保存
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO alert_rules VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                alert_rule.rule_id, alert_rule.name, alert_rule.description,
                alert_rule.condition_expression, alert_rule.threshold_value,
                alert_rule.comparison_operator, alert_rule.severity.value,
                alert_rule.cooldown_minutes, alert_rule.max_alerts_per_hour,
                alert_rule.auto_response_enabled, json.dumps(alert_rule.escalation_rules),
                json.dumps(alert_rule.notification_targets), alert_rule.enabled,
                alert_rule.created_at.isoformat(),
                alert_rule.last_triggered_at.isoformat() if alert_rule.last_triggered_at else None,
                alert_rule.trigger_count
            ))
            conn.commit()
        
        if alert_rule.enabled:
            self.operational_metrics["alert_rules_active"] += 1
        
        self.logger.info(f"Alert rule created: {alert_rule.name}")
    
    async def evaluate_alert_rules(self, metric_data: Dict[str, Any]) -> List[Incident]:
        """アラートルール評価"""
        triggered_alerts = []
        
        for rule in self.alert_rules.values():
            if not rule.enabled:
                continue
            
            # クールダウン期間チェック
            if rule.last_triggered_at:
                cooldown_delta = datetime.now() - rule.last_triggered_at
                if cooldown_delta.total_seconds() < (rule.cooldown_minutes * 60):
                    continue
            
            # 条件評価
            if self._evaluate_alert_condition(rule, metric_data):
                # アラート生成
                alert_incident = await self._create_alert_incident(rule, metric_data)
                triggered_alerts.append(alert_incident)
                
                # ルール更新
                rule.last_triggered_at = datetime.now()
                rule.trigger_count += 1
                await self.create_alert_rule(rule)  # 更新保存
        
        return triggered_alerts
    
    async def register_monitoring_target(self, target: MonitoringTarget):
        """監視対象登録"""
        self.monitoring_targets[target.target_id] = target
        
        # データベース保存
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO monitoring_targets VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                target.target_id, target.name, target.type, target.endpoint_url,
                target.check_interval_seconds, target.timeout_seconds,
                target.health_check_enabled, target.health_check_path,
                json.dumps(target.expected_response_codes),
                json.dumps(target.quality_standards), json.dumps(target.alert_rules),
                target.created_at.isoformat(),
                target.last_checked_at.isoformat() if target.last_checked_at else None,
                target.status, target.uptime_percentage
            ))
            conn.commit()
        
        self.logger.info(f"Monitoring target registered: {target.name}")
    
    async def check_target_health(self, target_id: str) -> Dict[str, Any]:
        """監視対象ヘルスチェック"""
        if target_id not in self.monitoring_targets:
            raise ValueError(f"Monitoring target not found: {target_id}")
        
        target = self.monitoring_targets[target_id]
        
        # ヘルスチェック実行
        health_result = await self._perform_health_check(target)
        
        # ステータス更新
        target.last_checked_at = datetime.now()
        target.status = health_result["status"]
        
        if health_result["status"] == "healthy":
            self.operational_metrics["monitoring_targets_healthy"] += 1
        
        # データベース更新
        await self.register_monitoring_target(target)
        
        return health_result
    
    def should_escalate_incident(self, incident: Incident) -> bool:
        """インシデントエスカレーション判定"""
        # 重要度による即座エスカレーション
        if incident.severity == IncidentSeverity.CRITICAL:
            time_threshold = 10  # 10分
        elif incident.severity == IncidentSeverity.HIGH:
            time_threshold = 30  # 30分
        else:
            return False  # 低重要度はエスカレーション不要
        
        # 時間経過チェック
        elapsed_minutes = (datetime.now() - incident.detected_at).total_seconds() / 60
        
        return elapsed_minutes >= time_threshold
    
    async def learn_incident_patterns(self) -> List[Dict[str, Any]]:

            """インシデントパターン学習"""
            category = incident.category.value
            if category not in category_incidents:
                category_incidents[category] = []
            category_incidents[category].append(incident)
        
        for category, incidents in category_incidents.items():
            if len(incidents) >= 2:  # 最低2つのインシデントで学習
                pattern = {
                    "category": category,
                    "incident_count": len(incidents),
                    "common_components": self._find_common_components(incidents),
                    "common_tags": self._find_common_tags(incidents),
                    "average_severity": self._calculate_average_severity(incidents),
                    "typical_causes": self._extract_typical_causes(incidents)
                }
                patterns.append(pattern)
                self.incident_patterns[category] = pattern
        
        self.operational_metrics["pattern_learning_count"] += len(patterns)
        
        self.logger.info(f"Learned {len(patterns)} incident patterns")
        return patterns
    
    def analyze_metric_trend(self, metrics: List[QualityMetric]) -> Dict[str, Any]:
        """品質メトリクストレンド分析"""
        if len(metrics) < 2:
            return {"direction": "unknown", "rate": 0.0}
        
        # 時系列ソート
        sorted_metrics = sorted(metrics, key=lambda m: m.measured_at)
        values = [m.value for m in sorted_metrics]
        
        # トレンド計算
        first_value = values[0]
        last_value = values[-1]
        
        if last_value > first_value:
            direction = "improving"
            rate = (last_value - first_value) / len(values)
        elif last_value < first_value:
            direction = "degrading"
            rate = (first_value - last_value) / len(values)
        else:
            direction = "stable"
            rate = 0.0
        
        return {
            "direction": direction,
            "rate": abs(rate),
            "first_value": first_value,
            "last_value": last_value,
            "trend_strength": abs(rate) / max(first_value, 1.0)
        }
    
    async def attempt_automated_remediation(self, incident_id: str) -> Dict[str, Any]:
        """自動修復試行"""
        if incident_id not in self.incidents:
            raise ValueError(f"Incident not found: {incident_id}")
        
        incident = self.incidents[incident_id]
        
        # パターンベース修復
        remediation_actions = self._determine_remediation_actions(incident)
        
        if remediation_actions:
            # 修復実行
            success = await self._execute_remediation_actions(remediation_actions, incident)
            
            result = {
                "status": "success" if success else "failed",
                "actions_taken": remediation_actions,
                "incident_id": incident_id,
                "timestamp": datetime.now().isoformat()
            }
            
            if success:
                self.operational_metrics["automated_remediations"] += 1
                incident.status = IncidentStatus.RESOLVED
                incident.resolved_at = datetime.now()
                await self.register_incident(incident)
        else:
            result = {
                "status": "no_action",
                "reason": "No automated remediation available",
                "incident_id": incident_id
            }
        
        return result
    
    async def analyze_incident_correlations(self) -> List[Dict[str, Any]]:

            """インシデント相関分析"""
            related_incidents = []
            
            for j, other_incident in enumerate(recent_incidents):
                if i != j:
                    # 時間的近接性
                    time_diff = abs((incident.detected_at - other_incident.detected_at).total_seconds())
                    
                    # コンポーネント重複
                    component_overlap = set(incident.affected_components) & set(other_incident.affected_components)
                    
                    # 相関判定
                    if time_diff < 300 or component_overlap:  # 5分以内または共通コンポーネント
                        related_incidents.append(other_incident.incident_id)
            
            if related_incidents:
                correlations.append({
                    "primary_incident": incident.incident_id,
                    "related_incidents": related_incidents,
                    "correlation_type": "temporal_spatial",
                    "confidence": 0.7
                })
        
        return correlations
    
    async def send_message_to_sage(self, sage_type: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """他賢者へのメッセージ送信"""
        try:
            # 簡易メッセージ送信実装
            response = await self.send_a2a_message(sage_type, message)
            return {"status": "success", "response": response}
        except Exception as e:
            self.logger.error(f"Failed to send message to {sage_type}: {e}")
            return {"status": "error", "error": str(e)}
    
    async def request_task_creation(self, incident_id: str) -> Dict[str, Any]:
        """タスク作成要求（Task Sageとの連携）"""
        if incident_id not in self.incidents:
            raise ValueError(f"Incident not found: {incident_id}")
        
        incident = self.incidents[incident_id]
        
        return {
            "task_type": "incident_resolution",
            "title": f"Resolve Incident: {incident.title}",
            "description": incident.description,
            "priority": incident.severity.value,
            "affected_components": incident.affected_components,
            "incident_id": incident_id,
            "created_by": "incident_sage"
        }
    
    async def search_similar_incidents(self, query: str) -> List[Dict[str, Any]]:
        """類似インシデント検索（RAG Sageとの連携）"""
        # 簡単な類似検索実装
        similar = []
        query_words = set(query.lower().split())
        
        for incident in self.incidents.values():
            title_words = set(incident.title.lower().split())
            desc_words = set(incident.description.lower().split())
            all_words = title_words | desc_words
            
            similarity = len(query_words & all_words) / len(query_words | all_words) if query_words | all_words else 0
            
            if similarity > 0.3:  # 30%以上の類似度
                similar.append({
                    "incident_id": incident.incident_id,
                    "title": incident.title,
                    "similarity": similarity,
                    "resolution_time": incident.resolution_time_ms,
                    "resolution_steps": incident.resolution_steps
                })
        
        return sorted(similar, key=lambda x: x["similarity"], reverse=True)[:10]
    
    def get_operational_metrics(self) -> Dict[str, Union[int, float]]:

    
    """運用メトリクス取得""" Dict[str, Any]) -> IncidentSeverity:
        """重要度判定"""
        severity_str = anomaly_data.get('severity', 'medium').lower()
        severity_map = {
            'critical': IncidentSeverity.CRITICAL,
            'high': IncidentSeverity.HIGH,
            'medium': IncidentSeverity.MEDIUM,
            'low': IncidentSeverity.LOW,
            'info': IncidentSeverity.INFO
        }
        return severity_map.get(severity_str, IncidentSeverity.MEDIUM)
    
    def _determine_category(self, anomaly_data: Dict[str, Any]) -> IncidentCategory:
        """カテゴリ判定"""
        metric = anomaly_data.get('metric', '').lower()
        
        if 'error' in metric or 'exception' in metric:
            return IncidentCategory.QUALITY
        elif 'response_time' in metric or 'latency' in metric:
            return IncidentCategory.PERFORMANCE
        elif 'availability' in metric or 'uptime' in metric:
            return IncidentCategory.AVAILABILITY
        elif 'security' in metric or 'auth' in metric:
            return IncidentCategory.SECURITY
        else:
            return IncidentCategory.QUALITY
    
    def _generate_incident_description(self, anomaly_data: Dict[str, Any]) -> str:
        """インシデント説明生成"""
        component = anomaly_data.get('component', 'unknown')
        metric = anomaly_data.get('metric', 'unknown')
        value = anomaly_data.get('value', 'N/A')
        threshold = anomaly_data.get('threshold', 'N/A')
        
        return f"Anomalous {metric} detected in {component}. Current value: {value}, Threshold: " \
            "{threshold}"
    
    def _extract_tags(self, anomaly_data: Dict[str, Any]) -> List[str]:
        """タグ抽出"""
        tags = ['anomaly_detected']
        
        if 'component' in anomaly_data:
            tags.append(f"component:{anomaly_data['component']}")
        if 'metric' in anomaly_data:
            tags.append(f"metric:{anomaly_data['metric']}")
        
        return tags
    
    async def _trigger_automatic_response(self, incident: Incident):
        """自動対応トリガー"""
        # 重要インシデントの場合は即座に対応開始
        self.logger.info(f"Triggering automatic response for critical incident: {incident.incident_id}" \
            "Triggering automatic response for critical incident: {incident.incident_id}" \
            "Triggering automatic response for critical incident: {incident.incident_id}")
        
        # バックグラウンドで対応実行
        asyncio.create_task(self.respond_to_incident(incident.incident_id))
    
    def _calculate_overall_score(
        self,
        metric_scores: Dict[str,
        float],
        standard: QualityStandard
    ) -> float:

    """総合スコア計算"""
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for metric_name, score in metric_scores.items():
            if metric_name in standard.metrics:
                metric_def = standard.metrics[metric_name]
                target = metric_def.target_value
                threshold_min = metric_def.threshold_min
                weight = 1.0  # 均等重み付け
                
                # 閾値ベースの評価（target値ではなく最小閾値ベース）
                if score >= threshold_min:
                    normalized_score = min(100.0, (score / target) * 100.0) if target > 0 else 100.0
                else:
                    # 最小閾値未満は大幅減点
                    normalized_score = (score / threshold_min) * 50.0 if threshold_min > 0 else 0.0
                
                total_score += normalized_score * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    async def _create_quality_incident(self, assessment: QualityAssessment):
        """品質問題インシデント生成"""
        incident = Incident(
            title=f"Quality Standard Violation: {assessment.target_component}",
            description=f"Component {assessment.target_component} failed quality assessment with score " \
                "Component {assessment.target_component} failed quality assessment with score " \
                "{assessment.overall_score:.1f}%",
            severity=IncidentSeverity.MEDIUM,
            category=IncidentCategory.QUALITY,
            affected_components=[assessment.target_component],
            tags=['quality_violation', f'score:{assessment.overall_score:.1f}']
        )
        
        await self.register_incident(incident)
    
    def _determine_response_actions(self, incident: Incident) -> List[str]:
        """対応アクション決定"""
        actions = []
        
        if incident.category == IncidentCategory.PERFORMANCE:
            actions.extend([
                "Check system resource usage",
                "Analyze recent performance metrics",
                "Review recent deployments",
                "Scale resources if necessary"
            ])
        elif incident.category == IncidentCategory.QUALITY:
            actions.extend([
                "Run automated tests",
                "Check code quality metrics",
                "Review recent commits",
                "Notify development team"
            ])
        elif incident.category == IncidentCategory.AVAILABILITY:
            actions.extend([
                "Restart affected services",
                "Check network connectivity",
                "Verify load balancer status",
                "Escalate to operations team"
            ])
        else:
            actions.extend([
                "Gather additional diagnostics",
                "Check system logs",
                "Notify relevant team"
            ])
        
        return actions
    
    async def _execute_response_actions(self, actions: List[str], incident: Incident) -> bool:
        """対応アクション実行"""
        # シミュレーション実装
        self.logger.info(f"Executing response actions for {incident.incident_id}: {actions}")
        
        # 実際の実装では具体的な対応を実行
        await asyncio.sleep(0.1)  # シミュレーション遅延
        
        # 60%の確率で成功とする（テスト用）
        import random
        return random.random() > 0.4
    
    def _evaluate_alert_condition(self, rule: AlertRule, metric_data: Dict[str, Any]) -> bool:
        """アラート条件評価"""
        # 簡単な条件評価実装
        try:
            # conditionから対象メトリクス名を抽出
            parts = rule.condition_expression.split()
            if len(parts) >= 3:
                metric_name = parts[0]
                operator = parts[1]
                threshold = float(parts[2])
                
                if metric_name in metric_data:
                    value = float(metric_data[metric_name])
                    
                    if operator == '>':
                        return value > threshold
                    elif operator == '<':
                        return value < threshold
                    elif operator == '>=':
                        return value >= threshold
                    elif operator == '<=':
                        return value <= threshold
                    elif operator == '==':
                        return value == threshold
                    elif operator == '!=':
                        return value != threshold
        
        except (ValueError, KeyError, IndexError):
            pass
        
        return False
    
    async def _create_alert_incident(
        self,
        rule: AlertRule,
        metric_data: Dict[str,
        Any]
    ) -> Incident:

        """アラートインシデント生成""" {rule.name}",
            description=f"Alert rule '{rule.name}' triggered by condition: {rule.condition_expression}",
            severity=rule.severity,
            category=IncidentCategory.QUALITY,  # デフォルト
            affected_components=[metric_data.get('component', 'unknown')],
            tags=['alert', f'rule:{rule.name}']
        )
        
        await self.register_incident(incident)
        return incident
    
    async def _perform_health_check(self, target: MonitoringTarget) -> Dict[str, Any]:
        """ヘルスチェック実行"""
        # シミュレーション実装
        import random
        
        # 90%の確率でヘルシー
        is_healthy = random.random() > 0.1
        response_time = random.randint(50, 300)
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "response_time_ms": response_time,
            "uptime": 99.5 if is_healthy else 85.2,
            "last_check": datetime.now().isoformat()
        }
    
    def _find_common_components(self, incidents: List[Incident]) -> List[str]:
        """共通影響コンポーネント抽出"""
        component_counts = {}
        for incident in incidents:
        # 繰り返し処理
            for component in incident.affected_components:
                component_counts[component] = component_counts.get(component, 0) + 1
        
        # 50%以上のインシデントに共通するコンポーネント
        threshold = len(incidents) * 0.5
        return [comp for comp, count in component_counts.items() if count >= threshold]
    
    def _find_common_tags(self, incidents: List[Incident]) -> List[str]:
        """共通タグ抽出"""
        tag_counts = {}
        # 繰り返し処理
        for incident in incidents:
            for tag in incident.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        threshold = len(incidents) * 0.3
        return [tag for tag, count in tag_counts.items() if count >= threshold]
    
    def _calculate_average_severity(self, incidents: List[Incident]) -> float:
        """平均重要度計算"""
        severity_values = {
            IncidentSeverity.INFO: 1,
            IncidentSeverity.LOW: 2,
            IncidentSeverity.MEDIUM: 3,
            IncidentSeverity.HIGH: 4,
            IncidentSeverity.CRITICAL: 5
        }
        
        total = sum(severity_values[incident.severity] for incident in incidents)
        return total / len(incidents) if incidents else 0
    
    def _extract_typical_causes(self, incidents: List[Incident]) -> List[str]:
        """典型的原因抽出"""
        causes = [incident.root_cause for incident in incidents if incident.root_cause]
        
        # 共通原因パターンを抽出（簡易実装）
        cause_words = {}
        for cause in causes:
            for word in cause.lower().split():
                if len(word) > 3:  # 短い語は除外
                    cause_words[word] = cause_words.get(word, 0) + 1
        
        # 頻出語をベースに典型原因を構築
        return [word for word, count in cause_words.items() if count >= 2]
    
    def _determine_remediation_actions(self, incident: Incident) -> List[str]:
        """修復アクション決定"""
        # パターンベース修復
        if incident.category == IncidentCategory.PERFORMANCE:
            return ["restart_service", "clear_cache", "scale_up"]
        elif incident.category == IncidentCategory.AVAILABILITY:
            return ["health_check", "restart_service", "failover"]
        elif incident.category == IncidentCategory.QUALITY:
            return ["run_tests", "rollback_deployment", "notify_team"]
        else:
            return ["gather_logs", "notify_team"]
    
    async def _execute_remediation_actions(self, actions: List[str], incident: Incident) -> bool:
        """修復アクション実行"""
        self.logger.info(f"Executing remediation actions: {actions}")
        
        # シミュレーション実装
        await asyncio.sleep(0.1)
        
        # 70%の成功率
        import random
        return random.random() > 0.3
    
    def _update_operational_metrics(self):

        
        """運用メトリクス更新"""
            self.operational_metrics["average_resolution_time"] = mean([
                i.resolution_time_ms for i in resolved_incidents
            ])
    
    # データベース行変換メソッド群
    def _row_to_incident(self, row) -> Incident:

            """データベース行からIncidentオブジェクト変換"""
        """データベース行からQualityStandardオブジェクト変換"""
        metrics_data = json.loads(row['metrics_json'] or '{}')
        metrics = {}
        
        for name, metric_dict in metrics_data.items():
            metrics[name] = QualityMetric(**metric_dict)
        
        return QualityStandard(
            standard_id=row['standard_id'],
            name=row['name'],
            description=row['description'] or "",
            category=row['category'] or "general",
            metrics=metrics,
            compliance_threshold=row['compliance_threshold'] or 95.0,
            version=row['version'] or "1.0.0",
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            applicable_components=json.loads(row['applicable_components'] or '[]'),
            mandatory=bool(row['mandatory'])
        )
    
    def _row_to_alert_rule(self, row) -> AlertRule:

            """データベース行からAlertRuleオブジェクト変換"""
        """データベース行からMonitoringTargetオブジェクト変換"""
        return MonitoringTarget(
            target_id=row['target_id'],
            name=row['name'],
            type=row['type'],
            endpoint_url=row['endpoint_url'],
            check_interval_seconds=row['check_interval_seconds'] or 60,
            timeout_seconds=row['timeout_seconds'] or 30,
            health_check_enabled=bool(row['health_check_enabled']),
            health_check_path=row['health_check_path'] or "/health",
            expected_response_codes=json.loads(row['expected_response_codes'] or '[200]'),
            quality_standards=json.loads(row['quality_standards'] or '[]'),
            alert_rules=json.loads(row['alert_rules'] or '[]'),
            created_at=datetime.fromisoformat(row['created_at']),
            last_checked_at=datetime.fromisoformat(row['last_checked_at']) if row['last_checked_at'] else None,
            status=row['status'] or "unknown",
            uptime_percentage=row['uptime_percentage'] or 0.0
        )
    
    async def register_quality_standard(self, standard: QualityStandard):
        """品質基準登録"""
        self.quality_standards[standard.standard_id] = standard
        
        # メトリクスをJSONに変換（datetimeは文字列に変換）
        metrics_json = {}
        for name, metric in standard.metrics.items():
            metric_dict = asdict(metric)
            # datetimeオブジェクトを文字列に変換
            if 'measured_at' in metric_dict and metric_dict['measured_at']:
                metric_dict['measured_at'] = metric_dict['measured_at'].isoformat()
            metrics_json[name] = metric_dict
        
        # データベース保存
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO quality_standards VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                standard.standard_id, standard.name, standard.description,
                standard.category, json.dumps(metrics_json),
                standard.compliance_threshold, standard.version,
                standard.created_at.isoformat(), standard.updated_at.isoformat(),
                json.dumps(standard.applicable_components), standard.mandatory
            ))
            conn.commit()
        
        self.logger.info(f"Quality standard registered: {standard.name}")
    
    # === メッセージハンドラー ===
    
    async def _handle_incident_alert(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """インシデントアラート処理"""
        try:
            incident_data = message.get("incident_data", {})
            incident = await self.detect_incident(incident_data)
            
            return self._create_success_response(message, {
                "incident_id": incident.incident_id,
                "status": "detected",
                "severity": incident.severity.value
            })
            
        except Exception as e:
            return self._create_error_response(message, str(e))
    
    async def _handle_quality_check(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """品質チェック処理"""
        try:
            standard_id = message.get("standard_id")
            assessment_data = message.get("assessment_data", {})
            
            assessment = await self.assess_quality(standard_id, assessment_data)
            
            return self._create_success_response(message, {
                "assessment_id": assessment.assessment_id,
                "is_compliant": assessment.is_compliant,
                "overall_score": assessment.overall_score,
                "violations": assessment.violations
            })
            
        except Exception as e:
            return self._create_error_response(message, str(e))
    
    async def _handle_health_check(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """ヘルスチェック処理"""
        try:
            soul_info = self.get_soul_info()
            operational_metrics = self.get_operational_metrics()
            
            health_status = {
                "status": "healthy" if self._running else "unhealthy",
                "soul_info": soul_info,
                "operational_metrics": operational_metrics,
                "incidents_count": len(self.incidents),
                "quality_standards_count": len(self.quality_standards)
            }
            
            return self._create_success_response(message, health_status)
            
        except Exception as e:
            return self._create_error_response(message, str(e))
    
    async def _handle_metrics_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """メトリクス要求処理"""
        try:
            metrics = self.get_operational_metrics()
            
            return self._create_success_response(message, {
                "metrics": metrics,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return self._create_error_response(message, str(e))
    
    async def _handle_sage_consultation(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """賢者間相談処理"""
        try:
            consultation_type = message.get("consultation_type")
            consultation_data = message.get("data", {})
            
            if consultation_type == "incident_collaboration":
                # インシデント協調対応
                incident_id = consultation_data.get("incident_id")
                recommendations = await self._provide_incident_recommendations(incident_id)
                
                return self._create_success_response(message, {
                    "consultation_type": consultation_type,
                    "recommendations": recommendations
                })
                
            elif consultation_type == "quality_expertise":
                # 品質専門知識提供
                domain = consultation_data.get("domain")
                quality_guidelines = await self._provide_quality_guidelines(domain)
                
                return self._create_success_response(message, {
                    "consultation_type": consultation_type,
                    "guidelines": quality_guidelines
                })
            
            else:
                return self._create_error_response(message, f"Unknown consultation type: {consultation_type}" \
                    "Unknown consultation type: {consultation_type}" \
                    "Unknown consultation type: {consultation_type}")
                
        except Exception as e:
            return self._create_error_response(message, str(e))
    
    async def _provide_incident_recommendations(self, incident_id: str) -> List[str]:
        """インシデント対応推奨事項提供"""
        if incident_id not in self.incidents:
            return ["Incident not found in system"]
        
        incident = self.incidents[incident_id]
        recommendations = []
        
        # 重要度別推奨事項
        if incident.severity == IncidentSeverity.CRITICAL:
            recommendations.extend([
                "Immediate escalation to on-call team",
                "Activate incident response protocol",
                "Consider emergency rollback if deployment related"
            ])
        elif incident.severity == IncidentSeverity.HIGH:
            recommendations.extend([
                "Notify relevant team leads",
                "Prioritize resolution over new features",
                "Document all troubleshooting steps"
            ])
        
        # カテゴリ別推奨事項
        if incident.category == IncidentCategory.PERFORMANCE:
            recommendations.extend([
                "Check system resource utilization",
                "Review recent performance metrics",
                "Consider scaling resources"
            ])
        elif incident.category == IncidentCategory.SECURITY:
            recommendations.extend([
                "Immediate security assessment",
                "Check for potential data exposure",
                "Review access logs"
            ])
        
        return recommendations
    
    async def _provide_quality_guidelines(self, domain: str) -> List[str]:
        """品質ガイドライン提供"""
        guidelines = {
            "code_quality": [
                "Maintain minimum 90% test coverage",
                "Follow established coding standards",
                "Perform thorough code reviews",
                "Use static analysis tools"
            ],
            "security": [
                "Implement security-by-design principles",
                "Regular security audits and penetration testing",
                "Keep dependencies up to date",
                "Follow OWASP guidelines"
            ],
            "performance": [
                "Set performance budgets and monitor",
                "Optimize critical user journeys",
                "Regular load testing",
                "Monitor key performance indicators"
            ],
            "general": [
                "Follow Iron Will principles",
                "Implement comprehensive monitoring",
                "Maintain detailed documentation",
                "Regular quality assessments"
            ]
        }
        
        return guidelines.get(domain, guidelines["general"])
    
    # === 通信用ユーティリティ ===
    
    async def send_a2a_message(self, target_sage: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """メッセージ送信（基本実装）"""
        # 基本的なモック実装
        return {
            "status": "success",
            "message": f"Message sent to {target_sage}",
            "response": {"acknowledged": True}
        }
    
    @property 
    def soul_id(self) -> str:
        """Soul ID取得（互換性のため）"""
        return self.context.session_id


# 後方互換性のためのエイリアス
IncidentSage = IncidentSageSoul