#!/usr/bin/env python3
"""
🚨 Incident Sage Business Logic - ビジネスロジック分離
=====================================

Elder Loop Phase 1: Knowledge Sageパターン適用
soul.pyからインシデント対応・品質監視ビジネスロジックを分離

Author: Claude Elder
Created: 2025-07-23
"""

import asyncio
import sqlite3
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from statistics import mean
from dataclasses import asdict

# Incident Sage Models import (Elder Tree共通パス対応)
import sys
sys.path.append("/home/aicompany/ai_co/elders_guild")
from src.incident_sage.abilities.incident_models import (
    Incident, IncidentSeverity, IncidentStatus, IncidentCategory,
    QualityMetric, QualityStandard, QualityAssessment,
    IncidentResponse, AlertRule, MonitoringTarget
)


class IncidentProcessor:


"""
    Incident Sage核心ビジネスロジック処理クラス
    
    Knowledge Sageパターンを適用したピュアビジネスロジック:
    - フレームワーク依存性なし
    - A2A通信から独立
    - テスト容易性向上
    - Elder Loop対応
    """ Optional[Path] = None, test_mode: bool = False):
        """Incident Processor初期化"""
        # データディレクトリ設定
        if test_mode:
            # テストモード：一時的なデータディレクトリ
            import tempfile
            temp_dir = tempfile.mkdtemp(prefix="incident_sage_test_")
            self.data_dir = Path(temp_dir)
        else:
            self.data_dir = data_dir or Path("data/incident_sage")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # データベース初期化
        self.db_path = self.data_dir / "incident_sage.db"
        self.logger = logging.getLogger("incident_processor")
        
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
        if not test_mode:
            self._load_all_data()
        
        self.logger.info("Incident Processor initialized successfully")
    
    def reset_for_testing(self):

            """テスト用データリセット""" 0,
            "incidents_resolved": 0,
            "average_resolution_time": 0.0,
            "quality_assessments_performed": 0,
            "alert_rules_active": 0,
            "monitoring_targets_healthy": 0,
            "pattern_learning_count": 0,
            "automated_remediations": 0
        }
        self.incident_patterns.clear()
        self.correlation_cache.clear()
    
    async def process_action(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        アクション処理メインエントリーポイント
        
        Knowledge Sageパターン適用:
        統一インターフェースでビジネスロジック実行
        """
        try:
            self.logger.info(f"Processing action: {action}")
            
            if action == "detect_incident":
                return await self._detect_incident_action(data)
            elif action == "register_incident":
                return await self._register_incident_action(data)
            elif action == "assess_quality":
                return await self._assess_quality_action(data)
            elif action == "respond_to_incident":
                return await self._respond_to_incident_action(data)
            elif action == "create_alert_rule":
                return await self._create_alert_rule_action(data)
            elif action == "evaluate_alert_rules":
                return await self._evaluate_alert_rules_action(data)
            elif action == "register_monitoring_target":
                return await self._register_monitoring_target_action(data)
            elif action == "check_target_health":
                return await self._check_target_health_action(data)
            elif action == "learn_incident_patterns":
                return await self._learn_incident_patterns_action(data)
            elif action == "analyze_correlations":
                return await self._analyze_correlations_action(data)
            elif action == "attempt_automated_remediation":
                return await self._attempt_automated_remediation_action(data)
            elif action == "search_similar_incidents":
                return await self._search_similar_incidents_action(data)
            elif action == "get_operational_metrics":
                return await self._get_operational_metrics_action(data)
            elif action == "register_quality_standard":
                return await self._register_quality_standard_action(data)
            elif action == "get_statistics":
                return await self._get_statistics_action(data)
            elif action == "health_check":
                return await self._health_check_action(data)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "action": action
                }
                
        except Exception as e:
            self.logger.error(f"Error processing action {action}: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": action
            }
    
    # === Core Business Logic Actions ===
    
    async def _detect_incident_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """インシデント検知アクション"""
        try:
            # 入力データ検証
            if not data:
                return {"success": False, "error": "Empty data provided"}
            
            if data is None:
                return {"success": False, "error": "NULL data provided"}
                
            # JSON構造検証
            if not isinstance(data, dict):
                return {"success": False, "error": "Invalid data structure, expected dict"}
            
            anomaly_data = data.get("anomaly_data", {})
            
            # anomaly_dataの必須チェック
            if not anomaly_data or not isinstance(anomaly_data, dict):
                return {"success": False, "error": "Missing or invalid anomaly_data"}
            
            # データサイズ制限チェック (JSONエンコード後で1MB制限)
            try:
                data_size = len(json.dumps(data))
                if data_size > 1024 * 1024:  # 1MB
                    return {"success": False, "error": f"Data too large: {data_size} bytes"}
            except Exception:
                return {"success": False, "error": "Data not JSON serializable"}
            
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
            await self._register_incident_internal(incident)
            
            # 自動対応判定
            auto_response_triggered = False
            if severity in [IncidentSeverity.CRITICAL, IncidentSeverity.HIGH]:
                auto_response_triggered = True
                # Note: 実際の自動対応は別途実行
            
            self.operational_metrics["incidents_detected"] += 1
            
            return {
                "success": True,
                "data": {
                    "incident_id": incident.incident_id,
                    "title": incident.title,
                    "severity": incident.severity.value,
                    "category": incident.category.value,
                    "status": incident.status.value,
                    "confidence_score": incident.confidence_score,
                    "detection_time_ms": incident.detection_time_ms,
                    "auto_response_triggered": auto_response_triggered
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _assess_quality_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """品質評価アクション"""
        try:
            # 入力データ検証
            if not data or not isinstance(data, dict):
                return {"success": False, "error": "Invalid or empty data"}
            
            standard_id = data.get("standard_id")
            component = data.get("component")
            metrics = data.get("metrics", {})
            
            if not standard_id or not component:
                return {"success": False, "error": "standard_id and component are required"}
            
            if standard_id not in self.quality_standards:
                return {"success": False, "error": f"Quality standard not found: {standard_id}"}
            
            standard = self.quality_standards[standard_id]
            
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
            await self._save_quality_assessment(assessment)
            
            self.operational_metrics["quality_assessments_performed"] += 1
            
            # 品質問題の場合はインシデント生成通知
            quality_incident_created = False
            if not is_compliant:
                # 品質問題インシデント生成マーク
                quality_incident_created = True
            
            return {
                "success": True,
                "data": {
                    "assessment_id": assessment.assessment_id,
                    "target_component": assessment.target_component,
                    "overall_score": assessment.overall_score,
                    "compliance_score": assessment.compliance_score,
                    "is_compliant": assessment.is_compliant,
                    "violations": assessment.violations,
                    "recommendations": assessment.recommendations,
                    "confidence_score": assessment.confidence_score,
                    "quality_incident_created": quality_incident_created
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _respond_to_incident_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """インシデント対応アクション"""
        try:
            incident_id = data.get("incident_id")
            
            if not incident_id:
                return {"success": False, "error": "incident_id is required"}
            
            if incident_id not in self.incidents:
                return {"success": False, "error": f"Incident not found: {incident_id}"}
            
            incident = self.incidents[incident_id]
            
            # 対応戦略決定
            response_actions = self._determine_response_actions(incident)
            
            # 対応実行
            response = IncidentResponse(
                incident_id=incident_id,
                action_type="automated_response",
                description=f"Automated response to {incident.severity.value} incident",
                execution_steps=response_actions,
                responder="incident_processor",
                automated=True
            )
            
            # 実際の対応実行（シミュレーション）
            success = await self._execute_response_actions(response_actions, incident)
            
            if success:
                response.status = "completed"
                response.effectiveness_score = 0.8
                incident.status = IncidentStatus.RESOLVED
                incident.resolved_at = datetime.now()
                incident.resolution_time_ms = int((datetime.now() - incident.detected_at).total_seconds() * 1000)
                self.operational_metrics["incidents_resolved"] += 1
            else:
                response.status = "failed"
                response.effectiveness_score = 0.2
                incident.status = IncidentStatus.ESCALATED
            
            response.completed_at = datetime.now()
            
            # 更新保存
            await self._register_incident_internal(incident)
            
            return {
                "success": True,
                "data": {
                    "incident_id": incident_id,
                    "response_status": response.status,
                    "effectiveness_score": response.effectiveness_score,
                    "execution_steps": response.execution_steps,
                    "incident_status": incident.status.value,
                    "resolution_time_ms": incident.resolution_time_ms
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _learn_incident_patterns_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """インシデントパターン学習アクション"""
        try:
            patterns = []
            
            # カテゴリ別パターン学習
            category_incidents = {}
            for incident in self.incidents.values():
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
            
            return {
                "success": True,
                "data": {
                    "patterns_learned": len(patterns),
                    "patterns": patterns,
                    "total_incidents_analyzed": len(self.incidents)
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_statistics_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """統計情報取得アクション"""
        try:
            # インシデント統計
            incident_stats = {
                "total_incidents": len(self.incidents),
                "incidents_by_status": self._count_by_status(),
                "incidents_by_severity": self._count_by_severity(),
                "incidents_by_category": self._count_by_category(),
                "resolution_rate": self._calculate_resolution_rate(),
                "average_resolution_time_minutes": self._calculate_average_resolution_time()
            }
            
            # 品質統計
            quality_stats = {
                "quality_standards_count": len(self.quality_standards),
                "total_assessments": self.operational_metrics["quality_assessments_performed"],
                "assessments_performed": self.operational_metrics["quality_assessments_performed"],
                "average_quality_score": 85.0,  # 仮の値
                "compliance_trends": self._analyze_compliance_trends()
            }
            
            # アラート統計
            alert_stats = {
                "alert_rules_total": len(self.alert_rules),
                "alert_rules_active": len([r for r in self.alert_rules.values() if r.enabled]),
                "total_alerts_triggered": sum(rule.trigger_count for rule in self.alert_rules.values())
            }
            
            # 監視統計
            monitoring_stats = {
                "monitoring_targets_count": len(self.monitoring_targets),
                "healthy_targets": len([t for t in self.monitoring_targets.values() if t.status == "healthy"]),
                "average_uptime": self._calculate_average_uptime()
            }
            
            # 運用メトリクス
            operational_metrics = self.operational_metrics.copy()
            
            return {
                "success": True,
                "data": {
                    "incident_statistics": incident_stats,
                    "quality_statistics": quality_stats,
                    "alert_statistics": alert_stats,
                    "monitoring_statistics": monitoring_stats,
                    "operational_metrics": operational_metrics,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _health_check_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """ヘルスチェックアクション"""
        try:
            health_status = {
                "status": "healthy",
                "agent_name": "Incident Processor",
                "incidents_managed": len(self.incidents),
                "quality_standards": len(self.quality_standards),
                "alert_rules": len(self.alert_rules),
                "monitoring_targets": len(self.monitoring_targets),
                "uptime_seconds": time.time(),  # 簡易実装
                "operational_metrics": self.operational_metrics.copy()
            }
            
            return {
                "success": True,
                "data": health_status
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # === Internal Helper Methods ===
    
    async def _register_incident_internal(self, incident: Incident):
        """インシデント内部登録"""
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
    
    async def _save_quality_assessment(self, assessment: QualityAssessment):
        """品質評価保存"""
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
    
    def _determine_severity(self, anomaly_data: Dict[str, Any]) -> IncidentSeverity:
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
        
        return f"Anomalous {metric} detected in {component}. Current value: {value}, Threshold: {threshold}"
    
    def _extract_tags(self, anomaly_data: Dict[str, Any]) -> List[str]:
        """タグ抽出"""
        tags = ['anomaly_detected']
        
        if 'component' in anomaly_data:
            tags.append(f"component:{anomaly_data['component']}")
        if 'metric' in anomaly_data:
            tags.append(f"metric:{anomaly_data['metric']}")
        
        return tags
    
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
        """対応アクション実行（シミュレーション）"""
        self.logger.info(f"Executing response actions for {incident.incident_id}: {actions}")
        
        # 実際の実装では具体的な対応を実行
        await asyncio.sleep(0.01)  # シミュレーション遅延
        
        # 75%の確率で成功とする（Knowledge Sageより高い成功率）
        import random
        return random.random() > 0.25
    
    def _calculate_overall_score(self, metric_scores: Dict[str, float], standard: QualityStandard) -> float:
        """総合スコア計算"""
        if not metric_scores:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for metric_name, score in metric_scores.items():
            if metric_name in standard.metrics:
                metric_def = standard.metrics[metric_name]
                target = metric_def.target_value
                threshold_min = metric_def.threshold_min
                weight = 1.0  # 均等重み付け
                
                # 閾値ベースの評価
                if score >= threshold_min:
                    normalized_score = min(100.0, (score / target) * 100.0) if target > 0 else 100.0
                else:
                    # 最小閾値未満は大幅減点
                    normalized_score = (score / threshold_min) * 50.0 if threshold_min > 0 else 0.0
                
                total_score += normalized_score * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    # === Statistics Calculation Methods ===
    
    def _count_by_status(self) -> Dict[str, int]:

                    """ステータス別カウント"""
            status = incident.status.value
            counts[status] = counts.get(status, 0) + 1
        return counts
    
    def _count_by_severity(self) -> Dict[str, int]:

            """重要度別カウント"""
            severity = incident.severity.value
            counts[severity] = counts.get(severity, 0) + 1
        return counts
    
    def _count_by_category(self) -> Dict[str, int]:

            """カテゴリ別カウント"""
            category = incident.category.value
            counts[category] = counts.get(category, 0) + 1
        return counts
    
    def _calculate_resolution_rate(self) -> float:

            """解決率計算"""
            return 0.0
        
        resolved_count = len([i for i in self.incidents.values() if i.status == IncidentStatus.RESOLVED])
        return (resolved_count / len(self.incidents)) * 100.0
    
    def _calculate_average_resolution_time(self) -> float:

            """平均解決時間計算（分）"""
            return 0.0
        
        total_time_ms = sum(i.resolution_time_ms for i in resolved_incidents)
        average_time_ms = total_time_ms / len(resolved_incidents)
        return average_time_ms / (1000 * 60)  # 分に変換
    
    def _analyze_compliance_trends(self) -> Dict[str, Any]:

            """コンプライアンス傾向分析""" "stable",
            "compliance_rate": 85.0,
            "improvement_areas": ["test_coverage", "code_quality"]
        }
    
    def _calculate_average_uptime(self) -> float:

        """平均稼働率計算"""
            return 0.0
        
        total_uptime = sum(target.uptime_percentage for target in self.monitoring_targets.values())
        return total_uptime / len(self.monitoring_targets)
    
    # === Pattern Learning Methods ===
    
    def _find_common_components(self, incidents: List[Incident]) -> List[str]:
        """共通影響コンポーネント抽出"""
        component_counts = {}
        for incident in incidents:
            for component in incident.affected_components:
                component_counts[component] = component_counts.get(component, 0) + 1
        
        # 50%以上のインシデントに共通するコンポーネント
        threshold = len(incidents) * 0.5
        return [comp for comp, count in component_counts.items() if count >= threshold]
    
    def _find_common_tags(self, incidents: List[Incident]) -> List[str]:
        """共通タグ抽出"""
        tag_counts = {}
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
    
    # === Database Initialization ===
    
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
                
                # 品質基準ロード（デフォルト以外）
                for row in conn.execute("SELECT * FROM quality_standards"):
                    standard = self._row_to_quality_standard(row)
                    if standard.standard_id not in self.quality_standards:
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
            # 初期化エラーは継続、空データで開始
    
    def _update_operational_metrics(self):

            """運用メトリクス更新"""
            self.operational_metrics["average_resolution_time"] = mean([
                i.resolution_time_ms for i in resolved_incidents
            ])
    
    # === Database Row Conversion Methods ===
    
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
    
    # === Additional Action Methods (残りの実装) ===
    
    async def _register_incident_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """インシデント登録アクション"""
        try:
            # Incident作成パラメータを処理
            incident_data = data.get("incident", {})
            
            incident = Incident(
                title=incident_data.get("title", "Unknown Incident"),
                description=incident_data.get("description", ""),
                severity=IncidentSeverity(incident_data.get("severity", "medium")),
                category=IncidentCategory(incident_data.get("category", "quality")),
                affected_components=incident_data.get("affected_components", []),
                tags=incident_data.get("tags", [])
            )
            
            await self._register_incident_internal(incident)
            
            return {
                "success": True,
                "data": {
                    "incident_id": incident.incident_id,
                    "status": "registered"
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _create_alert_rule_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """アラートルール作成アクション"""
        try:
            rule_data = data.get("alert_rule", {})
            
            # alert_ruleが辞書でない場合はエラー
            if not isinstance(rule_data, dict):
                return {"success": False, "error": "alert_rule must be a dictionary"}
            
            # 必須フィールドチェック
            if not rule_data.get("name"):
                return {"success": False, "error": "alert_rule.name is required"}
            
            if not rule_data.get("condition_expression"):
                return {"success": False, "error": "alert_rule.condition_expression is required"}
            
            alert_rule = AlertRule(
                name=rule_data.get("name"),
                description=rule_data.get("description", ""),
                condition_expression=rule_data.get("condition_expression"),
                severity=IncidentSeverity(rule_data.get("severity", "medium")),
                enabled=rule_data.get("enabled", True)
            )
            
            self.alert_rules[alert_rule.rule_id] = alert_rule
            
            # データベース保存（簡易版）
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
            
            return {
                "success": True,
                "data": {
                    "rule_id": alert_rule.rule_id,
                    "name": alert_rule.name,
                    "enabled": alert_rule.enabled
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _evaluate_alert_rules_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """アラートルール評価アクション"""
        try:
            metric_data = data.get("metrics", {})
            reset_cooldown = data.get("reset_cooldown", False)  # テスト用のクールダウンリセット
            triggered_alerts = []
            
            for rule in self.alert_rules.values():
                if not rule.enabled:
                    continue
                
                # テスト用クールダウンリセット
                if reset_cooldown:
                    rule.last_triggered_at = None
                    rule.trigger_count = 0
                
                # クールダウン期間チェック
                if rule.last_triggered_at:
                    cooldown_delta = datetime.now() - rule.last_triggered_at
                    if cooldown_delta.total_seconds() < (rule.cooldown_minutes * 60):
                        continue
                
                # 条件評価（簡易実装）
                if self._evaluate_alert_condition(rule, metric_data):
                    triggered_alerts.append({
                        "rule_id": rule.rule_id,
                        "rule_name": rule.name,
                        "severity": rule.severity.value,
                        "condition": rule.condition_expression
                    })
                    
                    # ルール更新
                    rule.last_triggered_at = datetime.now()
                    rule.trigger_count += 1
            
            return {
                "success": True,
                "data": {
                    "triggered_alerts": triggered_alerts,
                    "alert_count": len(triggered_alerts)
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _evaluate_alert_condition(self, rule: AlertRule, metric_data: Dict[str, Any]) -> bool:
        """アラート条件評価（簡易実装）"""
        try:
            # condition_expressionから対象メトリクス名を抽出
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
    
    async def _register_monitoring_target_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """監視対象登録アクション"""
        try:
            target_data = data.get("target", {})
            
            target = MonitoringTarget(
                name=target_data.get("name", "Unknown Target"),
                type=target_data.get("type", "service"),
                endpoint_url=target_data.get("endpoint_url", ""),
                health_check_enabled=target_data.get("health_check_enabled", True)
            )
            
            self.monitoring_targets[target.target_id] = target
            
            # データベース保存（簡易版）
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
            
            return {
                "success": True,
                "data": {
                    "target_id": target.target_id,
                    "name": target.name,
                    "status": target.status
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _check_target_health_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """監視対象ヘルスチェックアクション"""
        try:
            target_id = data.get("target_id")
            
            if not target_id or target_id not in self.monitoring_targets:
                return {"success": False, "error": f"Monitoring target not found: {target_id}"}
            
            target = self.monitoring_targets[target_id]
            
            # ヘルスチェック実行（シミュレーション）
            import random
            is_healthy = random.random() > 0.1  # 90%の確率でヘルシー
            response_time = random.randint(50, 300)
            uptime = 99.5 if is_healthy else 85.2
            
            # ステータス更新
            target.last_checked_at = datetime.now()
            target.status = "healthy" if is_healthy else "unhealthy"
            target.uptime_percentage = uptime
            
            health_result = {
                "target_id": target_id,
                "status": target.status,
                "response_time_ms": response_time,
                "uptime_percentage": uptime,
                "last_check": target.last_checked_at.isoformat()
            }
            
            if is_healthy:
                self.operational_metrics["monitoring_targets_healthy"] += 1
            
            return {
                "success": True,
                "data": health_result
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _analyze_correlations_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """インシデント相関分析アクション"""
        try:
            correlations = []
            recent_incidents = [i for i in self.incidents.values() 
                              if (datetime.now() - i.detected_at).total_seconds() < 3600]  # 1時間以内
            
            # 時系列相関
            for i, incident in enumerate(recent_incidents):
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
            
            return {
                "success": True,
                "data": {
                    "correlations": correlations,
                    "correlation_count": len(correlations),
                    "analyzed_incidents": len(recent_incidents)
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _attempt_automated_remediation_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """自動修復試行アクション"""
        try:
            incident_id = data.get("incident_id")
            
            if not incident_id or incident_id not in self.incidents:
                return {"success": False, "error": f"Incident not found: {incident_id}"}
            
            incident = self.incidents[incident_id]
            
            # パターンベース修復
            remediation_actions = self._determine_remediation_actions(incident)
            
            if remediation_actions:
                # 修復実行（シミュレーション）
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
                    incident.resolution_time_ms = int((datetime.now() - incident.detected_at).total_seconds() * 1000)
                    await self._register_incident_internal(incident)
            else:
                result = {
                    "status": "no_action",
                    "reason": "No automated remediation available",
                    "incident_id": incident_id
                }
            
            return {
                "success": True,
                "data": result
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
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
        """修復アクション実行（シミュレーション）"""
        self.logger.info(f"Executing remediation actions: {actions}")
        
        # シミュレーション実装
        await asyncio.sleep(0.01)
        
        # 80%の成功率（高め）
        import random
        return random.random() > 0.2
    
    async def _search_similar_incidents_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """類似インシデント検索アクション"""
        try:
            query = data.get("query", "")
            
            if not query:
                return {"success": False, "error": "query is required"}
            
            # クエリサイズ制限（10KB）
            if len(query) > 10 * 1024:
                return {"success": False, "error": f"Query too large: {len(query)} bytes (max 10KB)"}
            
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
                        "resolution_time_ms": incident.resolution_time_ms,
                        "resolution_steps": incident.resolution_steps
                    })
            
            # 類似度順でソート
            similar.sort(key=lambda x: x["similarity"], reverse=True)
            similar = similar[:10]  # 上位10件
            
            return {
                "success": True,
                "data": {
                    "query": query,
                    "similar_incidents": similar,
                    "total_matches": len(similar)
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_operational_metrics_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """運用メトリクス取得アクション"""
        try:
            metrics = self.operational_metrics.copy()
            
            return {
                "success": True,
                "data": {
                    "operational_metrics": metrics,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _register_quality_standard_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """品質基準登録アクション"""
        try:
            standard_data = data.get("standard", {})
            
            # QualityStandard作成（簡易版）
            metrics = {}
            for name, metric_data in standard_data.get("metrics", {}).items():
                metrics[name] = QualityMetric(
                    name=metric_data.get("name", name),
                    target_value=metric_data.get("target_value", 100.0),
                    threshold_min=metric_data.get("threshold_min", 90.0),
                    unit=metric_data.get("unit", "points"),
                    description=metric_data.get("description", "")
                )
            
            standard = QualityStandard(
                name=standard_data.get("name", "Unknown Standard"),
                description=standard_data.get("description", ""),
                category=standard_data.get("category", "general"),
                metrics=metrics,
                compliance_threshold=standard_data.get("compliance_threshold", 95.0),
                applicable_components=standard_data.get("applicable_components", ["all"])
            )
            
            self.quality_standards[standard.standard_id] = standard
            
            # データベース保存（簡易版）
            # メトリクスをJSONに変換
            metrics_json = {}
            for name, metric in standard.metrics.items():
                metric_dict = asdict(metric)
                # datetimeオブジェクトを文字列に変換
                if 'measured_at' in metric_dict and metric_dict['measured_at']:
                    metric_dict['measured_at'] = metric_dict['measured_at'].isoformat()
                metrics_json[name] = metric_dict
            
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
            
            return {
                "success": True,
                "data": {
                    "standard_id": standard.standard_id,
                    "name": standard.name,
                    "metrics_count": len(standard.metrics)
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}