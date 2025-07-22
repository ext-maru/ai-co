"""
Incident Knight Servant - インシデントナイト族サーバント
緊急対応・危機管理特化型サーバント
"""

from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta
from elder_tree.servants.base_servant import ElderServantBase
import structlog
from prometheus_client import Counter, Histogram
import json
import subprocess
import os


class IncidentKnightServant(ElderServantBase):
    """
    インシデントナイト族基底クラス
    
    特徴:
    - 緊急対応・危機管理に特化
    - 24/7即応体制
    - 根本原因分析
    """
    
    def __init__(self, name: str, specialty: str, port: int):
        super().__init__(
            name=name,
            tribe="incident_knight",
            specialty=specialty,
            port=port
        )
        
        # インシデントナイト特有の設定
        self.response_time_sla = 300  # 5分以内対応
        self.escalation_threshold = 900  # 15分でエスカレーション
        self.incident_history = []  # 直近のインシデント履歴


class CrisisResponder(IncidentKnightServant):
    """
    Crisis Responder - 危機対応スペシャリスト
    
    専門:
    - 緊急インシデント対応
    - 根本原因分析
    - 復旧作業実行
    - ポストモーテム作成
    """
    
    def __init__(self, port: int = 60104):
        super().__init__(
            name="crisis_responder",
            specialty="Emergency incident response and recovery",
            port=port
        )
        
        # 追加メトリクス
        self.incident_response_time = Histogram(
            'crisis_responder_response_seconds',
            'Time to respond to incidents',
            buckets=[30, 60, 120, 300, 600, 900, 1800]
        )
        
        self.recovery_success_rate = Counter(
            'crisis_responder_recovery_total',
            'Recovery attempts',
            ['status']
        )
        
        # 追加ハンドラー登録
        self._register_crisis_handlers()
    
    def _register_crisis_handlers(self):
        """危機対応専用ハンドラー"""
        
        @self.on_message("respond_to_incident")
        async def handle_respond_to_incident(message) -> Dict[str, Any]:
            """
            インシデント対応リクエスト
            
            Input:
                - incident: インシデント詳細
                - priority: 優先度
                - affected_systems: 影響を受けるシステム
            """
            incident = message.data.get("incident", {})
            priority = message.data.get("priority", "medium")
            affected_systems = message.data.get("affected_systems", [])
            
            # 対応時間の記録開始
            start_time = datetime.now()
            
            with self.incident_response_time.time():
                result = await self.execute_specialized_task(
                    "incident_response",
                    {
                        "incident": incident,
                        "priority": priority,
                        "affected_systems": affected_systems
                    },
                    {}
                )
            
            # インシデント履歴に追加
            self.incident_history.append({
                "timestamp": start_time.isoformat(),
                "incident_id": incident.get("id", "unknown"),
                "response_time": (datetime.now() - start_time).total_seconds(),
                "result": result.get("status", "unknown")
            })
            
            return {
                "status": "success",
                "response": result
            }
        
        @self.on_message("perform_recovery")
        async def handle_perform_recovery(message) -> Dict[str, Any]:
            """
            復旧作業実行リクエスト
            """
            recovery_plan = message.data.get("recovery_plan", {})
            target_systems = message.data.get("target_systems", [])
            
            result = await self.execute_specialized_task(
                "recovery",
                {
                    "recovery_plan": recovery_plan,
                    "target_systems": target_systems
                },
                {}
            )
            
            # 復旧成功率を記録
            self.recovery_success_rate.labels(
                status="success" if result.get("recovered", False) else "failed"
            ).inc()
            
            return {
                "status": "success",
                "recovery_result": result
            }
    
    async def execute_specialized_task(
        self,
        task_type: str,
        parameters: Dict[str, Any],
        consultation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        インシデントナイト特化タスク実行
        """
        if task_type == "incident_response":
            incident = parameters.get("incident", {})
            priority = parameters.get("priority", "medium")
            affected_systems = parameters.get("affected_systems", [])
            
            # インシデント分析
            analysis = await self._analyze_incident(incident, affected_systems)
            
            # 即時対応策の実行
            immediate_actions = await self._execute_immediate_actions(
                incident, analysis, priority
            )
            
            # 根本原因分析
            root_cause = await self._perform_root_cause_analysis(
                incident, analysis
            )
            
            # 復旧計画の策定
            recovery_plan = await self._create_recovery_plan(
                incident, root_cause, affected_systems
            )
            
            # Incident Sageへの報告
            await self._report_to_incident_sage(
                incident, analysis, root_cause, recovery_plan
            )
            
            return {
                "incident_id": incident.get("id", "unknown"),
                "status": "responded",
                "analysis": analysis,
                "immediate_actions": immediate_actions,
                "root_cause": root_cause,
                "recovery_plan": recovery_plan,
                "estimated_recovery_time": self._estimate_recovery_time(recovery_plan)
            }
        
        elif task_type == "recovery":
            recovery_plan = parameters.get("recovery_plan", {})
            target_systems = parameters.get("target_systems", [])
            
            # 復旧作業の実行
            recovery_results = await self._execute_recovery_plan(
                recovery_plan, target_systems
            )
            
            # 復旧確認
            verification = await self._verify_recovery(target_systems)
            
            # ポストモーテム準備
            postmortem_data = await self._prepare_postmortem_data(
                recovery_plan, recovery_results, verification
            )
            
            return {
                "recovered": verification.get("all_systems_healthy", False),
                "recovery_results": recovery_results,
                "verification": verification,
                "postmortem_data": postmortem_data
            }
        
        elif task_type == "emergency_fix":
            # 緊急修正タスク
            issue = parameters.get("issue", {})
            fix_strategy = parameters.get("fix_strategy", "hotfix")
            
            emergency_fix = await self._apply_emergency_fix(issue, fix_strategy)
            
            return {
                "fix_applied": emergency_fix.get("success", False),
                "fix_details": emergency_fix,
                "rollback_plan": self._create_rollback_plan(emergency_fix)
            }
        
        return await super().execute_specialized_task(
            task_type, parameters, consultation_result
        )
    
    async def _analyze_incident(
        self, 
        incident: Dict[str, Any], 
        affected_systems: List[str]
    ) -> Dict[str, Any]:
        """
        インシデント分析
        """
        analysis = {
            "severity": self._calculate_severity(incident, affected_systems),
            "impact_assessment": self._assess_impact(incident, affected_systems),
            "timeline": self._create_incident_timeline(incident),
            "patterns": self._identify_patterns(incident),
            "similar_incidents": await self._find_similar_incidents(incident)
        }
        
        # システムヘルスチェック
        health_status = await self._check_system_health(affected_systems)
        analysis["current_health"] = health_status
        
        # 影響範囲の特定
        analysis["blast_radius"] = self._determine_blast_radius(
            incident, affected_systems
        )
        
        return analysis
    
    async def _execute_immediate_actions(
        self,
        incident: Dict[str, Any],
        analysis: Dict[str, Any],
        priority: str
    ) -> List[Dict[str, Any]]:
        """
        即時対応策の実行
        """
        actions = []
        
        # 優先度に応じた即時対応
        if priority == "critical" or analysis["severity"] == "critical":
            # アラート送信
            alert_action = await self._send_critical_alerts(incident)
            actions.append({
                "type": "alert",
                "status": "sent",
                "recipients": alert_action.get("recipients", [])
            })
            
            # 自動スケーリング
            if "overload" in incident.get("type", "").lower():
                scale_action = await self._auto_scale_systems(
                    analysis["blast_radius"]
                )
                actions.append({
                    "type": "auto_scale",
                    "status": scale_action.get("status", "failed"),
                    "scaled_systems": scale_action.get("systems", [])
                })
        
        # ログ収集
        log_action = await self._collect_diagnostic_logs(
            analysis["blast_radius"]
        )
        actions.append({
            "type": "log_collection",
            "status": "completed",
            "log_locations": log_action.get("locations", [])
        })
        
        # 一時的な緩和策
        if "error_rate" in incident.get("metrics", {}):
            mitigation = await self._apply_temporary_mitigation(incident)
            actions.append({
                "type": "mitigation",
                "status": mitigation.get("status", "failed"),
                "details": mitigation.get("details", {})
            })
        
        return actions
    
    async def _perform_root_cause_analysis(
        self,
        incident: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        根本原因分析
        """
        # 5 Whys分析
        five_whys = await self._five_whys_analysis(incident, analysis)
        
        # タイムライン相関分析
        timeline_correlations = self._analyze_timeline_correlations(
            analysis["timeline"]
        )
        
        # システムメトリクス分析
        metrics_analysis = await self._analyze_system_metrics(
            incident.get("start_time", datetime.now() - timedelta(hours=1)),
            incident.get("end_time", datetime.now())
        )
        
        # 根本原因の特定
        root_causes = self._identify_root_causes(
            five_whys, timeline_correlations, metrics_analysis
        )
        
        return {
            "identified_causes": root_causes,
            "confidence_level": self._calculate_confidence(root_causes),
            "five_whys": five_whys,
            "correlations": timeline_correlations,
            "contributing_factors": self._identify_contributing_factors(
                incident, analysis
            )
        }
    
    async def _create_recovery_plan(
        self,
        incident: Dict[str, Any],
        root_cause: Dict[str, Any],
        affected_systems: List[str]
    ) -> Dict[str, Any]:
        """
        復旧計画の策定
        """
        # 復旧戦略の決定
        strategy = self._determine_recovery_strategy(incident, root_cause)
        
        # 復旧ステップの生成
        recovery_steps = []
        
        if strategy == "rollback":
            recovery_steps.extend(self._create_rollback_steps(affected_systems))
        elif strategy == "hotfix":
            recovery_steps.extend(await self._create_hotfix_steps(
                incident, root_cause
            ))
        elif strategy == "gradual":
            recovery_steps.extend(self._create_gradual_recovery_steps(
                affected_systems
            ))
        
        # 検証ステップの追加
        recovery_steps.extend(self._create_verification_steps(affected_systems))
        
        return {
            "strategy": strategy,
            "steps": recovery_steps,
            "estimated_duration": self._estimate_duration(recovery_steps),
            "risk_assessment": self._assess_recovery_risks(strategy, affected_systems),
            "rollback_points": self._identify_rollback_points(recovery_steps)
        }
    
    async def _report_to_incident_sage(
        self,
        incident: Dict[str, Any],
        analysis: Dict[str, Any],
        root_cause: Dict[str, Any],
        recovery_plan: Dict[str, Any]
    ):
        """
        Incident Sageへの詳細報告
        """
        report = {
            "incident_id": incident.get("id", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "responder": self.name,
            "incident_summary": {
                "type": incident.get("type", "unknown"),
                "severity": analysis["severity"],
                "impact": analysis["impact_assessment"]
            },
            "root_cause_analysis": root_cause,
            "recovery_plan": recovery_plan,
            "lessons_learned": self._extract_lessons_learned(
                incident, analysis, root_cause
            )
        }
        
        try:
            await self.send_message(
                target="incident_sage",
                message_type="incident_report",
                data=report
            )
        except Exception as e:
            self.logger.error("Failed to report to Incident Sage", error=str(e))
    
    def _calculate_severity(
        self, 
        incident: Dict[str, Any], 
        affected_systems: List[str]
    ) -> str:
        """
        インシデント重要度の計算
        """
        # 影響を受けるシステム数
        system_count = len(affected_systems)
        
        # エラー率やダウンタイムなどのメトリクス
        error_rate = incident.get("metrics", {}).get("error_rate", 0)
        downtime = incident.get("metrics", {}).get("downtime_minutes", 0)
        
        # 重要度判定
        if system_count > 5 or error_rate > 50 or downtime > 30:
            return "critical"
        elif system_count > 2 or error_rate > 20 or downtime > 10:
            return "high"
        elif system_count > 0 or error_rate > 5 or downtime > 5:
            return "medium"
        else:
            return "low"
    
    def _assess_impact(
        self, 
        incident: Dict[str, Any], 
        affected_systems: List[str]
    ) -> Dict[str, Any]:
        """
        影響評価
        """
        return {
            "user_impact": self._calculate_user_impact(incident),
            "business_impact": self._calculate_business_impact(incident),
            "technical_impact": {
                "affected_systems": affected_systems,
                "service_degradation": incident.get("metrics", {}).get("degradation", "unknown"),
                "data_loss_risk": self._assess_data_loss_risk(incident)
            }
        }
    
    def _create_incident_timeline(self, incident: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        インシデントタイムラインの作成
        """
        timeline = []
        
        # インシデント開始
        start_time = incident.get("start_time", datetime.now() - timedelta(hours=1))
        timeline.append({
            "timestamp": start_time.isoformat() if isinstance(start_time, datetime) else start_time,
            "event": "Incident started",
            "type": "start"
        })
        
        # 検出時刻
        detection_time = incident.get("detection_time", start_time + timedelta(minutes=5))
        timeline.append({
            "timestamp": detection_time.isoformat() if isinstance(detection_time, datetime) else detection_time,
            "event": "Incident detected",
            "type": "detection"
        })
        
        # 現在時刻（対応開始）
        timeline.append({
            "timestamp": datetime.now().isoformat(),
            "event": "Response initiated",
            "type": "response"
        })
        
        return sorted(timeline, key=lambda x: x["timestamp"])
    
    def _identify_patterns(self, incident: Dict[str, Any]) -> List[str]:
        """
        パターン識別
        """
        patterns = []
        
        # エラーパターン
        error_type = incident.get("error_type", "")
        if "timeout" in error_type.lower():
            patterns.append("timeout_pattern")
        if "memory" in error_type.lower():
            patterns.append("memory_leak_pattern")
        if "connection" in error_type.lower():
            patterns.append("connection_failure_pattern")
        
        # 時間パターン
        if incident.get("recurring", False):
            patterns.append("recurring_pattern")
        
        return patterns
    
    async def _find_similar_incidents(self, incident: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        類似インシデントの検索
        """
        # RAG Sageを使って類似インシデントを検索
        try:
            keywords = [
                incident.get("type", ""),
                incident.get("error_type", ""),
                *incident.get("affected_components", [])
            ]
            
            response = await self.send_message(
                target="rag_sage",
                message_type="search_similar_incidents",
                data={
                    "keywords": [k for k in keywords if k],
                    "limit": 5
                }
            )
            
            if response.data.get("status") == "success":
                return response.data.get("documents", [])
            else:
                return []
                
        except Exception as e:
            self.logger.error("Failed to search similar incidents", error=str(e))
            return []
    
    async def _check_system_health(self, systems: List[str]) -> Dict[str, Any]:
        """
        システムヘルスチェック
        """
        health_status = {}
        
        for system in systems:
            # 実際の実装ではシステムに応じた健全性チェックを行う
            health_status[system] = {
                "status": "degraded",  # healthy, degraded, down
                "response_time": 0.2,  # seconds
                "error_rate": 5.2,  # percentage
                "cpu_usage": 75.5,  # percentage
                "memory_usage": 82.3  # percentage
            }
        
        return health_status
    
    def _determine_blast_radius(
        self, 
        incident: Dict[str, Any], 
        affected_systems: List[str]
    ) -> List[str]:
        """
        影響範囲の特定
        """
        blast_radius = set(affected_systems)
        
        # 依存関係に基づいて影響範囲を拡大
        dependencies = incident.get("dependencies", {})
        for system in affected_systems:
            if system in dependencies:
                blast_radius.update(dependencies[system])
        
        return list(blast_radius)
    
    async def _send_critical_alerts(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """
        重要アラートの送信
        """
        # 実際の実装ではSlack、PagerDuty等に送信
        return {
            "status": "sent",
            "recipients": ["oncall-team", "engineering-leads"],
            "channels": ["slack", "pagerduty"],
            "message": f"Critical incident: {incident.get('type', 'Unknown')}"
        }
    
    async def _auto_scale_systems(self, systems: List[str]) -> Dict[str, Any]:
        """
        自動スケーリング
        """
        scaled_systems = []
        
        for system in systems:
            # 実際の実装ではクラウドAPIを使用してスケーリング
            scaled_systems.append(system)
        
        return {
            "status": "success",
            "systems": scaled_systems,
            "scale_factor": 2  # 2倍にスケール
        }
    
    async def _collect_diagnostic_logs(self, systems: List[str]) -> Dict[str, Any]:
        """
        診断ログの収集
        """
        log_locations = []
        
        for system in systems:
            # 実際の実装ではログ収集システムAPIを使用
            log_location = f"/tmp/incident_logs/{system}_{datetime.now().strftime('%Y%m%d%H%M%S')}.log"
            log_locations.append(log_location)
        
        return {
            "status": "completed",
            "locations": log_locations,
            "size_mb": 150  # 収集したログの合計サイズ
        }
    
    async def _apply_temporary_mitigation(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """
        一時的な緩和策の適用
        """
        mitigation_type = "rate_limiting"  # エラー率が高い場合はレート制限
        
        return {
            "status": "applied",
            "type": mitigation_type,
            "details": {
                "rate_limit": "100 req/min",
                "duration": "30 minutes",
                "affected_endpoints": incident.get("affected_endpoints", [])
            }
        }
    
    async def _five_whys_analysis(
        self, 
        incident: Dict[str, Any], 
        analysis: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        5 Whys分析
        """
        whys = []
        
        # 1st Why
        whys.append({
            "question": "Why did the incident occur?",
            "answer": f"{incident.get('type', 'System failure')} was detected"
        })
        
        # 2nd Why
        whys.append({
            "question": f"Why did {incident.get('type', 'the system')} fail?",
            "answer": "High resource utilization exceeded threshold"
        })
        
        # 3rd Why
        whys.append({
            "question": "Why was resource utilization high?",
            "answer": "Unexpected traffic spike from specific endpoints"
        })
        
        # 4th Why
        whys.append({
            "question": "Why was there an unexpected traffic spike?",
            "answer": "Bot traffic was not properly rate limited"
        })
        
        # 5th Why
        whys.append({
            "question": "Why was bot traffic not rate limited?",
            "answer": "Rate limiting rules were not updated after recent changes"
        })
        
        return whys
    
    def _analyze_timeline_correlations(
        self, 
        timeline: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        タイムライン相関分析
        """
        correlations = {
            "detection_delay": None,
            "escalation_time": None,
            "correlated_events": []
        }
        
        # 検出遅延の計算
        start_event = next((e for e in timeline if e["type"] == "start"), None)
        detection_event = next((e for e in timeline if e["type"] == "detection"), None)
        
        if start_event and detection_event:
            start_time = datetime.fromisoformat(start_event["timestamp"].replace('Z', '+00:00'))
            detection_time = datetime.fromisoformat(detection_event["timestamp"].replace('Z', '+00:00'))
            correlations["detection_delay"] = (detection_time - start_time).total_seconds()
        
        return correlations
    
    async def _analyze_system_metrics(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> Dict[str, Any]:
        """
        システムメトリクス分析
        """
        # 実際の実装ではPrometheusなどからメトリクスを取得
        return {
            "cpu_spike": {
                "detected": True,
                "max_value": 95.5,
                "timestamp": (start_time + timedelta(minutes=2)).isoformat()
            },
            "memory_leak": {
                "detected": False
            },
            "network_anomaly": {
                "detected": True,
                "type": "packet_loss",
                "rate": 2.5
            }
        }
    
    def _identify_root_causes(
        self,
        five_whys: List[Dict[str, str]],
        correlations: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        根本原因の特定
        """
        root_causes = []
        
        # 5 Whysから根本原因を抽出
        if five_whys:
            last_why = five_whys[-1]
            root_causes.append({
                "type": "process",
                "description": last_why["answer"],
                "confidence": 0.8
            })
        
        # メトリクスから根本原因を特定
        if metrics.get("cpu_spike", {}).get("detected"):
            root_causes.append({
                "type": "resource",
                "description": "CPU spike detected indicating resource exhaustion",
                "confidence": 0.9
            })
        
        return root_causes
    
    def _calculate_confidence(self, root_causes: List[Dict[str, Any]]) -> float:
        """
        根本原因分析の信頼度計算
        """
        if not root_causes:
            return 0.0
        
        # 各原因の信頼度の平均
        confidences = [cause.get("confidence", 0.5) for cause in root_causes]
        return sum(confidences) / len(confidences)
    
    def _identify_contributing_factors(
        self,
        incident: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> List[str]:
        """
        寄与要因の特定
        """
        factors = []
        
        # 時間帯要因
        if "peak_hours" in incident.get("tags", []):
            factors.append("Peak traffic hours")
        
        # システム要因
        health = analysis.get("current_health", {})
        for system, status in health.items():
            if status.get("cpu_usage", 0) > 80:
                factors.append(f"High CPU usage on {system}")
            if status.get("memory_usage", 0) > 80:
                factors.append(f"High memory usage on {system}")
        
        return factors
    
    def _determine_recovery_strategy(
        self,
        incident: Dict[str, Any],
        root_cause: Dict[str, Any]
    ) -> str:
        """
        復旧戦略の決定
        """
        # 根本原因に基づいて戦略を選択
        root_cause_types = [c.get("type") for c in root_cause.get("identified_causes", [])]
        
        if "configuration" in root_cause_types:
            return "rollback"
        elif "code" in root_cause_types:
            return "hotfix"
        elif "resource" in root_cause_types:
            return "gradual"
        else:
            return "standard"
    
    def _create_rollback_steps(self, affected_systems: List[str]) -> List[Dict[str, Any]]:
        """
        ロールバックステップの作成
        """
        steps = []
        
        for system in affected_systems:
            steps.append({
                "order": len(steps) + 1,
                "action": "rollback",
                "target": system,
                "description": f"Rollback {system} to previous stable version",
                "estimated_duration": 300,  # 5 minutes
                "risk_level": "low"
            })
        
        return steps
    
    async def _create_hotfix_steps(
        self,
        incident: Dict[str, Any],
        root_cause: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        ホットフィックスステップの作成
        """
        # Code Crafterと連携してホットフィックスを生成
        hotfix_request = await self.send_message(
            target="code_crafter",
            message_type="generate_hotfix",
            data={
                "issue": incident,
                "root_cause": root_cause,
                "urgency": "critical"
            }
        )
        
        steps = [
            {
                "order": 1,
                "action": "generate_fix",
                "description": "Generate hotfix code",
                "estimated_duration": 600,  # 10 minutes
                "risk_level": "medium"
            },
            {
                "order": 2,
                "action": "test_fix",
                "description": "Run automated tests on hotfix",
                "estimated_duration": 300,  # 5 minutes
                "risk_level": "low"
            },
            {
                "order": 3,
                "action": "deploy_fix",
                "description": "Deploy hotfix to production",
                "estimated_duration": 300,  # 5 minutes
                "risk_level": "medium"
            }
        ]
        
        return steps
    
    def _create_gradual_recovery_steps(
        self, 
        affected_systems: List[str]
    ) -> List[Dict[str, Any]]:
        """
        段階的復旧ステップの作成
        """
        steps = []
        
        # 10%ずつトラフィックを戻す
        for percentage in [10, 25, 50, 75, 100]:
            steps.append({
                "order": len(steps) + 1,
                "action": "restore_traffic",
                "percentage": percentage,
                "description": f"Restore {percentage}% traffic to affected systems",
                "estimated_duration": 300,  # 5 minutes each
                "risk_level": "low" if percentage < 50 else "medium"
            })
        
        return steps
    
    def _create_verification_steps(self, affected_systems: List[str]) -> List[Dict[str, Any]]:
        """
        検証ステップの作成
        """
        steps = []
        
        # ヘルスチェック
        steps.append({
            "order": 1000,  # 最後に実行
            "action": "health_check",
            "targets": affected_systems,
            "description": "Verify all systems are healthy",
            "estimated_duration": 180,  # 3 minutes
            "risk_level": "none"
        })
        
        # メトリクス確認
        steps.append({
            "order": 1001,
            "action": "verify_metrics",
            "description": "Confirm metrics are within normal range",
            "estimated_duration": 120,  # 2 minutes
            "risk_level": "none"
        })
        
        return steps
    
    def _estimate_duration(self, steps: List[Dict[str, Any]]) -> int:
        """
        復旧時間の見積もり（秒）
        """
        total_duration = sum(
            step.get("estimated_duration", 300) for step in steps
        )
        
        # バッファを追加（20%）
        return int(total_duration * 1.2)
    
    def _assess_recovery_risks(
        self, 
        strategy: str, 
        affected_systems: List[str]
    ) -> Dict[str, Any]:
        """
        復旧リスクの評価
        """
        risk_levels = {
            "rollback": "low",
            "hotfix": "medium",
            "gradual": "low",
            "standard": "medium"
        }
        
        return {
            "overall_risk": risk_levels.get(strategy, "medium"),
            "data_loss_risk": "none" if strategy == "rollback" else "low",
            "downtime_risk": "medium" if strategy == "hotfix" else "low",
            "cascade_failure_risk": "low" if len(affected_systems) < 3 else "medium"
        }
    
    def _identify_rollback_points(self, steps: List[Dict[str, Any]]) -> List[int]:
        """
        ロールバックポイントの特定
        """
        rollback_points = []
        
        for i, step in enumerate(steps):
            # 各主要ステップの後にロールバックポイントを設定
            if step.get("action") in ["deploy_fix", "restore_traffic"]:
                rollback_points.append(i)
        
        return rollback_points
    
    async def _execute_recovery_plan(
        self,
        recovery_plan: Dict[str, Any],
        target_systems: List[str]
    ) -> Dict[str, Any]:
        """
        復旧計画の実行
        """
        results = {
            "executed_steps": [],
            "failed_steps": [],
            "skipped_steps": []
        }
        
        for step in recovery_plan.get("steps", []):
            try:
                # ステップ実行（シミュレーション）
                step_result = await self._execute_recovery_step(step, target_systems)
                
                if step_result.get("success"):
                    results["executed_steps"].append({
                        "step": step["order"],
                        "action": step["action"],
                        "result": "success"
                    })
                else:
                    results["failed_steps"].append({
                        "step": step["order"],
                        "action": step["action"],
                        "error": step_result.get("error", "Unknown error")
                    })
                    
                    # 失敗した場合は後続ステップをスキップ
                    remaining_steps = [
                        s for s in recovery_plan["steps"] 
                        if s["order"] > step["order"]
                    ]
                    results["skipped_steps"].extend([
                        {"step": s["order"], "action": s["action"]} 
                        for s in remaining_steps
                    ])
                    break
                    
            except Exception as e:
                results["failed_steps"].append({
                    "step": step["order"],
                    "action": step["action"],
                    "error": str(e)
                })
                break
        
        return results
    
    async def _execute_recovery_step(
        self,
        step: Dict[str, Any],
        target_systems: List[str]
    ) -> Dict[str, Any]:
        """
        個別復旧ステップの実行
        """
        action = step.get("action")
        
        if action == "rollback":
            # ロールバック実行（シミュレーション）
            return {"success": True, "version": "previous-stable"}
        
        elif action == "deploy_fix":
            # ホットフィックスデプロイ（シミュレーション）
            return {"success": True, "deployed_version": "hotfix-001"}
        
        elif action == "restore_traffic":
            # トラフィック復旧（シミュレーション）
            percentage = step.get("percentage", 0)
            return {"success": True, "traffic_percentage": percentage}
        
        elif action == "health_check":
            # ヘルスチェック実行
            health_results = await self._check_system_health(target_systems)
            all_healthy = all(
                s.get("status") == "healthy" 
                for s in health_results.values()
            )
            return {"success": all_healthy, "health_status": health_results}
        
        else:
            return {"success": True, "message": f"Step {action} completed"}
    
    async def _verify_recovery(self, target_systems: List[str]) -> Dict[str, Any]:
        """
        復旧確認
        """
        verification_results = {
            "all_systems_healthy": True,
            "system_status": {},
            "metrics_normal": True,
            "user_impact_resolved": True
        }
        
        # 各システムの健全性確認
        health_status = await self._check_system_health(target_systems)
        for system, status in health_status.items():
            is_healthy = (
                status.get("status") == "healthy" and
                status.get("error_rate", 100) < 1 and
                status.get("response_time", 10) < 1
            )
            verification_results["system_status"][system] = is_healthy
            if not is_healthy:
                verification_results["all_systems_healthy"] = False
        
        # メトリクスの正常性確認
        metrics_check = await self._check_metrics_normalcy(target_systems)
        verification_results["metrics_normal"] = metrics_check.get("normal", False)
        
        return verification_results
    
    async def _prepare_postmortem_data(
        self,
        recovery_plan: Dict[str, Any],
        recovery_results: Dict[str, Any],
        verification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        ポストモーテムデータの準備
        """
        return {
            "incident_summary": {
                "recovery_strategy": recovery_plan.get("strategy"),
                "total_steps": len(recovery_plan.get("steps", [])),
                "executed_steps": len(recovery_results.get("executed_steps", [])),
                "failed_steps": len(recovery_results.get("failed_steps", [])),
                "recovery_duration": recovery_plan.get("estimated_duration", 0)
            },
            "verification_results": verification,
            "lessons_learned": self._generate_lessons_learned(
                recovery_plan, recovery_results, verification
            ),
            "action_items": self._generate_action_items(
                recovery_plan, recovery_results
            ),
            "timeline": self._create_recovery_timeline(recovery_results)
        }
    
    async def _apply_emergency_fix(
        self,
        issue: Dict[str, Any],
        fix_strategy: str
    ) -> Dict[str, Any]:
        """
        緊急修正の適用
        """
        if fix_strategy == "hotfix":
            # Code Crafterと連携
            fix_result = await self.send_message(
                target="code_crafter",
                message_type="generate_emergency_fix",
                data={"issue": issue}
            )
            
            return {
                "success": True,
                "fix_type": "hotfix",
                "code_changes": fix_result.data.get("changes", []),
                "deployment_status": "ready"
            }
        
        elif fix_strategy == "config_change":
            return {
                "success": True,
                "fix_type": "configuration",
                "changes": ["rate_limit: 100 -> 50", "timeout: 30s -> 60s"]
            }
        
        else:
            return {
                "success": False,
                "error": f"Unknown fix strategy: {fix_strategy}"
            }
    
    def _create_rollback_plan(self, emergency_fix: Dict[str, Any]) -> Dict[str, Any]:
        """
        ロールバック計画の作成
        """
        return {
            "trigger_conditions": [
                "Error rate increases by 20%",
                "Response time exceeds 5 seconds",
                "Health check failures"
            ],
            "rollback_steps": [
                {
                    "order": 1,
                    "action": "revert_code",
                    "description": "Revert to previous version"
                },
                {
                    "order": 2,
                    "action": "restart_services",
                    "description": "Restart affected services"
                },
                {
                    "order": 3,
                    "action": "verify_rollback",
                    "description": "Verify system is stable"
                }
            ],
            "estimated_time": 600  # 10 minutes
        }
    
    def _calculate_user_impact(self, incident: Dict[str, Any]) -> str:
        """
        ユーザー影響の計算
        """
        error_rate = incident.get("metrics", {}).get("error_rate", 0)
        affected_users = incident.get("metrics", {}).get("affected_users", 0)
        
        if error_rate > 50 or affected_users > 1000:
            return "severe"
        elif error_rate > 20 or affected_users > 100:
            return "moderate"
        elif error_rate > 5 or affected_users > 10:
            return "minor"
        else:
            return "minimal"
    
    def _calculate_business_impact(self, incident: Dict[str, Any]) -> str:
        """
        ビジネス影響の計算
        """
        downtime = incident.get("metrics", {}).get("downtime_minutes", 0)
        revenue_impact = incident.get("metrics", {}).get("revenue_impact", 0)
        
        if downtime > 60 or revenue_impact > 10000:
            return "critical"
        elif downtime > 30 or revenue_impact > 1000:
            return "high"
        elif downtime > 10 or revenue_impact > 100:
            return "medium"
        else:
            return "low"
    
    def _assess_data_loss_risk(self, incident: Dict[str, Any]) -> str:
        """
        データ損失リスクの評価
        """
        incident_type = incident.get("type", "").lower()
        
        if "database" in incident_type or "storage" in incident_type:
            return "high"
        elif "cache" in incident_type:
            return "medium"
        else:
            return "low"
    
    def _estimate_recovery_time(self, recovery_plan: Dict[str, Any]) -> str:
        """
        復旧時間の見積もり
        """
        duration_seconds = recovery_plan.get("estimated_duration", 0)
        
        if duration_seconds < 300:
            return "< 5 minutes"
        elif duration_seconds < 900:
            return "5-15 minutes"
        elif duration_seconds < 3600:
            return "15-60 minutes"
        else:
            hours = duration_seconds // 3600
            return f"{hours}+ hours"
    
    def _extract_lessons_learned(
        self,
        incident: Dict[str, Any],
        analysis: Dict[str, Any],
        root_cause: Dict[str, Any]
    ) -> List[str]:
        """
        教訓の抽出
        """
        lessons = []
        
        # 検出遅延から学ぶ
        detection_delay = analysis.get("correlations", {}).get("detection_delay")
        if detection_delay and detection_delay > 300:  # 5分以上
            lessons.append("Improve monitoring to reduce detection delay")
        
        # 根本原因から学ぶ
        for cause in root_cause.get("identified_causes", []):
            if cause["type"] == "configuration":
                lessons.append("Implement configuration validation before deployment")
            elif cause["type"] == "resource":
                lessons.append("Add predictive scaling based on traffic patterns")
        
        # パターンから学ぶ
        patterns = analysis.get("patterns", [])
        if "recurring_pattern" in patterns:
            lessons.append("Address recurring issues with permanent fixes")
        
        return lessons
    
    async def _check_metrics_normalcy(self, systems: List[str]) -> Dict[str, Any]:
        """
        メトリクスの正常性チェック
        """
        # 実際の実装ではPrometheusなどからメトリクスを確認
        return {
            "normal": True,
            "anomalies": [],
            "baseline_comparison": "within 5% of baseline"
        }
    
    def _generate_lessons_learned(
        self,
        recovery_plan: Dict[str, Any],
        recovery_results: Dict[str, Any],
        verification: Dict[str, Any]
    ) -> List[str]:
        """
        復旧プロセスからの教訓生成
        """
        lessons = []
        
        # 失敗したステップから学ぶ
        if recovery_results.get("failed_steps"):
            lessons.append("Improve error handling in recovery automation")
        
        # 復旧戦略から学ぶ
        if recovery_plan.get("strategy") == "hotfix":
            lessons.append("Maintain hotfix templates for common issues")
        
        # 検証結果から学ぶ
        if not verification.get("all_systems_healthy"):
            lessons.append("Enhance post-recovery verification procedures")
        
        return lessons
    
    def _generate_action_items(
        self,
        recovery_plan: Dict[str, Any],
        recovery_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        アクションアイテムの生成
        """
        action_items = []
        
        # 失敗したステップに対するアクション
        for failed_step in recovery_results.get("failed_steps", []):
            action_items.append({
                "priority": "high",
                "description": f"Investigate failure in {failed_step['action']} step",
                "assignee": "incident-team",
                "due_date": "within 48 hours"
            })
        
        # 予防的アクション
        action_items.append({
            "priority": "medium",
            "description": "Update runbooks based on this incident",
            "assignee": "documentation-team",
            "due_date": "within 1 week"
        })
        
        return action_items
    
    def _create_recovery_timeline(self, recovery_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        復旧タイムラインの作成
        """
        timeline = []
        current_time = datetime.now()
        
        for i, step in enumerate(recovery_results.get("executed_steps", [])):
            timeline.append({
                "timestamp": (current_time + timedelta(minutes=i*5)).isoformat(),
                "event": f"Executed {step['action']}",
                "result": step["result"]
            })
        
        return timeline


# 単体実行用
async def main():
    responder = CrisisResponder()
    await responder.start()
    print(f"Crisis Responder running on port {responder.port}")
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await responder.stop()


if __name__ == "__main__":
    asyncio.run(main())