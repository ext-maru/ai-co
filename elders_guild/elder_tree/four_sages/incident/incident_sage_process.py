#!/usr/bin/env python3
"""
インシデント賢者プロセス - 危機対応専門家
Elder Soul - A2A Architecture
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

import sys
sys.path.append(str(Path(__file__).parent.parent))

from libs.elder_process_base import (
    ElderProcessBase,
    ElderRole,
    SageType,
    ElderMessage,
    MessageType
)

class IncidentSeverity(Enum):
    """インシデント重要度"""
    CRITICAL = 1  # システム停止レベル
    HIGH = 2      # 重大な機能障害
    MEDIUM = 3    # 部分的な機能障害
    LOW = 4       # 軽微な問題
    INFO = 5      # 情報レベル

class IncidentStatus(Enum):
    """インシデントステータス"""
    DETECTED = "detected"      # 検出
    ANALYZING = "analyzing"    # 分析中
    RESPONDING = "responding"  # 対応中
    RESOLVED = "resolved"      # 解決済み
    MONITORING = "monitoring"  # 監視中

@dataclass
class Incident:
    """インシデント情報"""
    incident_id: str
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus
    detected_at: datetime
    source: str
    affected_systems: List[str]
    root_cause: Optional[str] = None
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None
    response_time: Optional[float] = None
    recovery_time: Optional[float] = None

@dataclass
class ResponsePlan:
    """対応計画"""
    plan_id: str
    incident_id: str
    steps: List[Dict[str, Any]]
    estimated_time: float
    required_resources: List[str]
    priority: int

class IncidentSageProcess(ElderProcessBase):
    """
    インシデント賢者 - 危機対応専門プロセス

    責務:
    - インシデントの検出と分析
    - 緊急対応の指揮
    - 根本原因の特定
    - 再発防止策の立案
    """

    def __init__(self):
        """初期化メソッド"""
        super().__init__(
            elder_name="incident_sage",
            elder_role=ElderRole.SAGE,
            sage_type=SageType.INCIDENT,
            port=5005
        )

        # インシデント管理
        self.active_incidents: Dict[str, Incident] = {}
        self.resolved_incidents: List[Incident] = []
        self.response_plans: Dict[str, ResponsePlan] = {}

        # 監視設定
        self.monitoring_config = {
            "check_interval": 30,  # 秒
            "alert_threshold": 3,  # 連続エラー回数
            "escalation_time": 300  # 5分でエスカレーション
        }

        # パターン認識
        self.incident_patterns: List[Dict[str, Any]] = []
        self.resolution_database: Dict[str, List[Dict[str, Any]]] = {}

        # パス設定
        self.data_dir = Path("data/incident_sage")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """初期化処理"""
        self.logger.info("🚨 Initializing Incident Sage...")

        # インシデント履歴の読み込み
        await self._load_incident_history()

        # 対応パターンの読み込み
        await self._load_response_patterns()

        # アラート設定の初期化
        await self._initialize_alert_system()

        self.logger.info(f"✅ Incident Sage initialized with {len(self.incident_patterns)} patterns")

    async def process(self):
        """メイン処理"""
        # アクティブインシデントの監視
        await self._monitor_active_incidents()

        # エスカレーション確認
        await self._check_escalations()

        # パターン分析（10分ごと）
        if not hasattr(self, '_last_analysis') or \
           (datetime.now() - self._last_analysis).total_seconds() > 600:
            await self._analyze_incident_patterns()
            self._last_analysis = datetime.now()

    async def handle_message(self, message: ElderMessage):
        """メッセージ処理"""
        self.logger.info(f"Received {message.message_type.value} from {message.source_elder}")

        if message.message_type == MessageType.EMERGENCY:
            # 緊急メッセージは最優先で処理
            await self._handle_emergency(message)
        elif message.message_type == MessageType.COMMAND:
            await self._handle_command(message)
        elif message.message_type == MessageType.QUERY:
            await self._handle_query(message)
        elif message.message_type == MessageType.REPORT:
            await self._handle_report(message)

    def register_handlers(self):
        """追加のメッセージハンドラー登録"""
        # 緊急メッセージハンドラーは基底クラスで登録済み
        pass

    async def on_cleanup(self):
        """クリーンアップ処理"""
        # インシデント履歴の保存
        await self._save_incident_history()

        # 対応パターンの保存
        await self._save_response_patterns()

    # プライベートメソッド

    async def _load_incident_history(self):
        """インシデント履歴の読み込み"""
        history_file = self.data_dir / "incident_history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # 解決済みインシデントの復元
                    for inc_data in data.get('resolved_incidents', []):
                        incident = Incident(
                            incident_id=inc_data['id'],
                            title=inc_data['title'],
                            description=inc_data['description'],
                            severity=IncidentSeverity(inc_data['severity']),
                            status=IncidentStatus(inc_data['status']),
                            detected_at=datetime.fromisoformat(inc_data['detected_at']),
                            source=inc_data['source'],
                            affected_systems=inc_data['affected_systems']
                        )

                        if not (inc_data.get('resolved_at')):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if inc_data.get('resolved_at'):
                            incident.resolved_at = datetime.fromisoformat(inc_data['resolved_at'])

                        incident.root_cause = inc_data.get('root_cause')
                        incident.resolution = inc_data.get('resolution')
                        incident.response_time = inc_data.get('response_time')
                        incident.recovery_time = inc_data.get('recovery_time')

                        self.resolved_incidents.append(incident)

                self.logger.info(f"Loaded {len(self.resolved_incidents)} historical incidents")

            except Exception as e:
                self.logger.error(f"Failed to load incident history: {e}")

    async def _load_response_patterns(self):
        """対応パターンの読み込み"""
        patterns_file = self.data_dir / "response_patterns.json"
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.incident_patterns = data.get('patterns', [])
                    self.resolution_database = data.get('resolutions', {})

                self.logger.info(f"Loaded {len(self.incident_patterns)} response patterns")

            except Exception as e:
                self.logger.error(f"Failed to load response patterns: {e}")

    async def _initialize_alert_system(self):
        """アラートシステムの初期化"""
        self.alert_counters = {}
        self.last_alerts = {}
        self.logger.info("Alert system initialized")

    async def _save_incident_history(self):
        """インシデント履歴の保存"""
        try:
            # インシデントデータの準備
            resolved_data = []
            for incident in self.resolved_incidents[-1000:]:  # 最新1000件のみ保存
                inc_data = {
                    'id': incident.incident_id,
                    'title': incident.title,
                    'description': incident.description,
                    'severity': incident.severity.value,
                    'status': incident.status.value,
                    'detected_at': incident.detected_at.isoformat(),
                    'source': incident.source,
                    'affected_systems': incident.affected_systems,
                    'root_cause': incident.root_cause,
                    'resolution': incident.resolution,
                    'response_time': incident.response_time,
                    'recovery_time': incident.recovery_time
                }

                if incident.resolved_at:
                    inc_data['resolved_at'] = incident.resolved_at.isoformat()

                resolved_data.append(inc_data)

            # 保存
            history_file = self.data_dir / "incident_history.json"
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'resolved_incidents': resolved_data,
                    'total_incidents': len(self.resolved_incidents),
                    'last_updated': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)

            self.logger.info("Incident history saved successfully")

        except Exception as e:
            self.logger.error(f"Failed to save incident history: {e}")

    async def _save_response_patterns(self):
        """対応パターンの保存"""
        try:
            patterns_file = self.data_dir / "response_patterns.json"
            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'patterns': self.incident_patterns,
                    'resolutions': self.resolution_database,
                    'last_updated': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)

            self.logger.info("Response patterns saved successfully")

        except Exception as e:
            self.logger.error(f"Failed to save response patterns: {e}")

    async def _handle_emergency(self, message: ElderMessage):
        """緊急メッセージ処理"""
        self.logger.warning(f"🚨 EMERGENCY from {message.source_elder}")

        # インシデント作成
        incident = await self._create_incident(
            title=message.payload.get('title', 'Emergency Incident'),
            description=message.payload.get('description', ''),
            severity=IncidentSeverity.CRITICAL,
            source=message.source_elder,
            affected_systems=message.payload.get('affected_systems', [])
        )

        # 即座に対応開始
        await self._initiate_emergency_response(incident)

        # グランドエルダーへエスカレーション
        escalation_msg = ElderMessage(
            message_id=f"emergency_escalation_{incident.incident_id}",
            source_elder=self.elder_name,
            target_elder="grand_elder",
            message_type=MessageType.EMERGENCY,
            payload={
                'incident_id': incident.incident_id,
                'title': incident.title,
                'severity': incident.severity.value,
                'source': incident.source,
                'immediate_action': 'Emergency response initiated'
            },
            priority=10
        )

        await self.send_message(escalation_msg)

    async def _handle_command(self, message: ElderMessage):
        """コマンド処理"""
        command = message.payload.get('command')

        if command == 'report_incident':
            # インシデント報告
            await self._handle_incident_report(message.payload)

        elif command == 'resolve_incident':
            # インシデント解決
            await self._resolve_incident(message.payload)

        elif command == 'execute_task':
            # タスク実行（クロードエルダーから）
            await self._execute_incident_task(message.payload)

    async def _handle_query(self, message: ElderMessage):
        """クエリ処理"""
        query_type = message.payload.get('query_type')

        if query_type == 'incident_status':
            # インシデントステータス照会
            incident_id = message.payload.get('incident_id')
            status = await self._get_incident_status(incident_id)

            response_msg = ElderMessage(
                message_id=f"status_response_{message.message_id}",
                source_elder=self.elder_name,
                target_elder=message.source_elder,
                message_type=MessageType.REPORT,
                payload={'incident_status': status},
                priority=message.priority
            )

            await self.send_message(response_msg)

        elif query_type == 'active_incidents':
            # アクティブインシデント一覧
            incidents = await self._get_active_incidents()

            response_msg = ElderMessage(
                message_id=f"incidents_response_{message.message_id}",
                source_elder=self.elder_name,
                target_elder=message.source_elder,
                message_type=MessageType.REPORT,
                payload={'active_incidents': incidents},
                priority=message.priority
            )

            await self.send_message(response_msg)

        elif query_type == 'availability':
            # 利用可能性確認
            response_msg = ElderMessage(
                message_id=f"availability_response_{message.message_id}",
                source_elder=self.elder_name,
                target_elder=message.source_elder,
                message_type=MessageType.REPORT,
                payload={
                    'available': True,
                    'capacity': 0.9,
                    'active_incidents': len(self.active_incidents),
                    'response_readiness': 'high'
                },
                priority=message.priority
            )

            await self.send_message(response_msg)

    async def _handle_report(self, message: ElderMessage):
        """レポート処理"""
        report_type = message.payload.get('type')

        if report_type == 'error':
            # エラー報告
            await self._process_error_report(message.payload)

        elif report_type == 'anomaly':
            # 異常検知報告
            await self._process_anomaly_report(message.payload)

        elif report_type == 'resolution':
            # 解決報告
            await self._process_resolution_report(message.payload)

    async def _create_incident(self, title: str, description: str,
                             severity: IncidentSeverity, source: str,
                             affected_systems: List[str]) -> Incident:
        """インシデント作成"""
        incident_id = f"INC_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        incident = Incident(
            incident_id=incident_id,
            title=title,
            description=description,
            severity=severity,
            status=IncidentStatus.DETECTED,
            detected_at=datetime.now(),
            source=source,
            affected_systems=affected_systems
        )

        self.active_incidents[incident_id] = incident

        self.logger.info(f"Created incident: {incident_id} - {title}")

        # 対応計画の作成
        response_plan = await self._create_response_plan(incident)
        self.response_plans[incident_id] = response_plan

        return incident

    async def _create_response_plan(self, incident: Incident) -> ResponsePlan:
        """対応計画作成"""
        # 類似インシデントから対応策を検索
        similar_resolutions = await self._find_similar_resolutions(incident)

        # 基本的な対応ステップ
        steps = [
            {"step": 1, "action": "Initial assessment", "duration": 5},
            {"step": 2, "action": "Impact analysis", "duration": 10},
            {"step": 3, "action": "Root cause investigation", "duration": 20}
        ]

        # 重要度に応じた追加ステップ
        if incident.severity == IncidentSeverity.CRITICAL:
            steps.extend([
                {"step": 4, "action": "Emergency mitigation", "duration": 15},
                {"step": 5, "action": "Stakeholder notification", "duration": 5}
            ])

        # 類似事例からの対応策追加
        if similar_resolutions:
            steps.append({
                "step": len(steps) + 1,
                "action": f"Apply known resolution: {similar_resolutions[0]['resolution']}",
                "duration": 30
            })

        plan = ResponsePlan(
            plan_id=f"PLAN_{incident.incident_id}",
            incident_id=incident.incident_id,
            steps=steps,
            estimated_time=sum(s['duration'] for s in steps),
            required_resources=self._determine_required_resources(incident),
            priority=incident.severity.value
        )

        return plan

    def _determine_required_resources(self, incident: Incident) -> List[str]:
        """必要リソースの決定"""
        resources = []

        # 影響システムに基づくリソース
        for system in incident.affected_systems:
            if "database" in system.lower():
                resources.append("database_expert")
            elif "api" in system.lower():
                resources.append("api_specialist")
            elif "security" in system.lower():
                resources.append("security_analyst")

        # 重要度に基づくリソース
        if incident.severity in [IncidentSeverity.CRITICAL, IncidentSeverity.HIGH]:
            resources.extend(["senior_engineer", "incident_commander"])

        return list(set(resources))  # 重複除去

    async def _initiate_emergency_response(self, incident: Incident):
        """緊急対応開始"""
        self.logger.warning(f"🚨 Initiating emergency response for {incident.incident_id}")

        incident.status = IncidentStatus.RESPONDING

        # 全エルダーに通知
        alert_msg = ElderMessage(
            message_id=f"emergency_alert_{incident.incident_id}",
            source_elder=self.elder_name,
            target_elder="all",  # ブロードキャスト
            message_type=MessageType.REPORT,
            payload={
                'type': 'emergency_alert',
                'incident_id': incident.incident_id,
                'title': incident.title,
                'severity': incident.severity.value,
                'action_required': 'Standby for instructions'
            },
            priority=9
        )

        await self.send_message(alert_msg)

        # 自動対応アクション実行
        await self._execute_automatic_responses(incident)

    async def _execute_automatic_responses(self, incident: Incident):
        """自動対応アクション実行"""
        # シミュレーション: 基本的な自動対応
        await asyncio.sleep(2)

        actions_taken = []

        # ログ収集
        actions_taken.append("Collected relevant logs")

        # 影響範囲の隔離
        if incident.severity == IncidentSeverity.CRITICAL:
            actions_taken.append("Isolated affected systems")

        # バックアップ確認
        actions_taken.append("Verified backup availability")

        self.logger.info(f"Automatic responses executed: {', '.join(actions_taken)}")

    async def _monitor_active_incidents(self):
        """アクティブインシデントの監視"""
        for incident_id, incident in self.active_incidents.items():
            if incident.status == IncidentStatus.RESPONDING:
                # 対応時間の更新
                elapsed = (datetime.now() - incident.detected_at).total_seconds()

                # 長時間化の警告
                if elapsed > 1800 and not hasattr(incident, '_long_duration_alerted'):
                    self.logger.warning(f"Incident {incident_id} running for {elapsed/60:0.1f} minutes" \
                        "Incident {incident_id} running for {elapsed/60:0.1f} minutes" \
                        "Incident {incident_id} running for {elapsed/60:0.1f} minutes")
                    incident._long_duration_alerted = True

    async def _check_escalations(self):
        """エスカレーション確認"""
        for incident_id, incident in self.active_incidents.items():
            elapsed = (datetime.now() - incident.detected_at).total_seconds()

            # エスカレーション条件
            should_escalate = False

            if incident.severity == IncidentSeverity.CRITICAL and elapsed > 300:
                should_escalate = True
            elif incident.severity == IncidentSeverity.HIGH and elapsed > 600:
                should_escalate = True

            if should_escalate and not hasattr(incident, '_escalated'):
                await self._escalate_incident(incident)
                incident._escalated = True

    async def _escalate_incident(self, incident: Incident):
        """インシデントエスカレーション"""
        self.logger.warning(f"Escalating incident {incident.incident_id}")

        escalation_msg = ElderMessage(
            message_id=f"escalation_{incident.incident_id}",
            source_elder=self.elder_name,
            target_elder="claude_elder",
            message_type=MessageType.REPORT,
            payload={
                'type': 'incident_escalation',
                'incident_id': incident.incident_id,
                'title': incident.title,
                'elapsed_time': (datetime.now() - incident.detected_at).total_seconds(),
                'reason': 'Extended resolution time',
                'action_needed': 'Additional resources required'
            },
            priority=8
        )

        await self.send_message(escalation_msg)

    async def _find_similar_resolutions(self, incident: Incident) -> List[Dict[str, Any]]:
        """類似解決策の検索"""
        similar = []

        # キーワードベースの簡易検索
        keywords = incident.title.lower().split() + incident.description.lower().split()

        for resolved in self.resolved_incidents[-100:]:  # 最新100件から検索
            if resolved.resolution:
                score = 0
                for keyword in keywords:
                    if keyword in resolved.title.lower() or keyword in resolved.description.lower():
                        score += 1

                if score > 2:  # 閾値
                    similar.append({
                        'incident_id': resolved.incident_id,
                        'title': resolved.title,
                        'resolution': resolved.resolution,
                        'score': score
                    })

        # スコア順にソート
        similar.sort(key=lambda x: x['score'], reverse=True)

        return similar[:5]  # 上位5件

    async def _analyze_incident_patterns(self):
        """インシデントパターン分析"""
        self.logger.info("Analyzing incident patterns...")

        # 最近のインシデントから傾向分析
        recent_incidents = self.resolved_incidents[-50:]

        if recent_incidents:
            # 原因別分類
            root_causes = {}
            for incident in recent_incidents:
                if incident.root_cause:
                    cause = incident.root_cause
                    root_causes[cause] = root_causes.get(cause, 0) + 1

            # 頻出パターンの特定
            frequent_causes = sorted(root_causes.items(), key=lambda x: x[1], reverse=True)[:5]

            if frequent_causes:
                # 分析結果をクロードエルダーに報告
                analysis_report = ElderMessage(
                    message_id=f"pattern_analysis_{datetime.now().timestamp()}",
                    source_elder=self.elder_name,
                    target_elder="claude_elder",
                    message_type=MessageType.REPORT,
                    payload={
                        'type': 'incident_pattern_analysis',
                        'frequent_causes': frequent_causes,
                        'total_incidents': len(recent_incidents),
                        'avg_resolution_time': self._calculate_avg_resolution_time(recent_incidents),
                        'recommendations': self._generate_prevention_recommendations(frequent_causes)
                    },
                    priority=5
                )

                await self.send_message(analysis_report)

    def _calculate_avg_resolution_time(self, incidents: List[Incident]) -> float:
        """平均解決時間の計算"""
        resolution_times = [
            inc.recovery_time for inc in incidents
            if inc.recovery_time is not None
        ]

        if resolution_times:
            return sum(resolution_times) / len(resolution_times)
        return 0.0

    def _generate_prevention_recommendations(self, frequent_causes: List[tuple]) -> List[str]:
        """予防策の生成"""
        recommendations = []

        for cause, count in frequent_causes[:3]:
            if "configuration" in cause.lower():
                recommendations.append("Implement configuration validation checks")
            elif "memory" in cause.lower():
                recommendations.append("Add memory monitoring and alerts")
            elif "timeout" in cause.lower():
                recommendations.append("Review and adjust timeout settings")
            else:
                recommendations.append(f"Investigate and address: {cause}")

        return recommendations

    async def _handle_incident_report(self, payload: Dict[str, Any]):
        """インシデント報告処理"""
        incident = await self._create_incident(
            title=payload.get('title', 'Reported Incident'),
            description=payload.get('description', ''),
            severity=IncidentSeverity(payload.get('severity', IncidentSeverity.MEDIUM.value)),
            source=payload.get('source', 'unknown'),
            affected_systems=payload.get('affected_systems', [])
        )

        # 自動分析開始
        incident.status = IncidentStatus.ANALYZING
        await self._analyze_incident(incident)

    async def _analyze_incident(self, incident: Incident):
        """インシデント分析"""
        # シミュレーション: 分析処理
        await asyncio.sleep(3)

        # 類似事例の検索
        similar = await self._find_similar_resolutions(incident)

        if similar:
            # 推定原因の設定
            incident.root_cause = f"Likely related to: {similar[0]['title']}"

        incident.status = IncidentStatus.RESPONDING

    async def _resolve_incident(self, payload: Dict[str, Any]):
        """インシデント解決"""
        incident_id = payload.get('incident_id')

        if incident_id not in self.active_incidents:
            self.logger.warning(f"Incident {incident_id} not found")
            return

        incident = self.active_incidents[incident_id]

        # 解決情報の記録
        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = datetime.now()
        incident.resolution = payload.get('resolution', 'Resolved')
        incident.root_cause = payload.get('root_cause', incident.root_cause)

        # 応答時間と回復時間の計算
        incident.response_time = (incident.resolved_at - incident.detected_at).total_seconds()
        incident.recovery_time = incident.response_time

        # 解決済みリストに移動
        self.resolved_incidents.append(incident)
        del self.active_incidents[incident_id]

        self.logger.info(f"Incident {incident_id} resolved in {incident.response_time/60:0.1f} minutes" \
            "Incident {incident_id} resolved in {incident.response_time/60:0.1f} minutes" \
            "Incident {incident_id} resolved in {incident.response_time/60:0.1f} minutes")

        # 解決通知
        await self._notify_incident_resolution(incident)

    async def _notify_incident_resolution(self, incident: Incident):
        """インシデント解決通知"""
        resolution_msg = ElderMessage(
            message_id=f"resolution_{incident.incident_id}",
            source_elder=self.elder_name,
            target_elder="claude_elder",
            message_type=MessageType.REPORT,
            payload={
                'type': 'incident_resolved',
                'incident_id': incident.incident_id,
                'title': incident.title,
                'resolution': incident.resolution,
                'response_time': incident.response_time,
                'lessons_learned': await self._extract_lessons_learned(incident)
            },
            priority=6
        )

        await self.send_message(resolution_msg)

    async def _extract_lessons_learned(self, incident: Incident) -> List[str]:
        """教訓の抽出"""
        lessons = []

        # 応答時間に基づく教訓
        if incident.response_time > 1800:  # 30分以上
            lessons.append("Response time exceeded 30 minutes - review escalation procedures")

        # 重要度に基づく教訓
        if incident.severity == IncidentSeverity.CRITICAL:
            lessons.append("Critical incident - ensure emergency response plan is updated")

        # 根本原因に基づく教訓
        if incident.root_cause and "configuration" in incident.root_cause.lower():
            lessons.append("Configuration-related issue - implement validation checks")

        return lessons

    async def _get_incident_status(self, incident_id: str) -> Dict[str, Any]:
        """インシデントステータス取得"""
        if incident_id in self.active_incidents:
            incident = self.active_incidents[incident_id]

            return {
                'incident_id': incident_id,
                'status': incident.status.value,
                'title': incident.title,
                'severity': incident.severity.value,
                'elapsed_time': (datetime.now() - incident.detected_at).total_seconds(),
                'response_plan': self._get_response_plan_summary(incident_id)
            }

        # 解決済みインシデントから検索
        for incident in self.resolved_incidents:
            if incident.incident_id == incident_id:
                return {
                    'incident_id': incident_id,
                    'status': incident.status.value,
                    'title': incident.title,
                    'resolution': incident.resolution,
                    'response_time': incident.response_time
                }

        return {'error': 'Incident not found'}

    def _get_response_plan_summary(self, incident_id: str) -> Dict[str, Any]:
        """対応計画サマリー取得"""
        if incident_id in self.response_plans:
            plan = self.response_plans[incident_id]

            return {
                'total_steps': len(plan.steps),
                'estimated_time': plan.estimated_time,
                'required_resources': plan.required_resources
            }

        return {}

    async def _get_active_incidents(self) -> List[Dict[str, Any]]:
        """アクティブインシデント一覧取得"""
        incidents = []

        for incident in self.active_incidents.values():
            incidents.append({
                'incident_id': incident.incident_id,
                'title': incident.title,
                'severity': incident.severity.value,
                'status': incident.status.value,
                'elapsed_time': (datetime.now() - incident.detected_at).total_seconds(),
                'affected_systems': incident.affected_systems
            })

        # 重要度順にソート
        incidents.sort(key=lambda x: x['severity'])

        return incidents

    async def _process_error_report(self, error_data: Dict[str, Any]):
        """エラー報告処理"""
        error_type = error_data.get('error_type', 'unknown')
        source = error_data.get('source', 'unknown')

        # エラーカウンターの更新
        counter_key = f"{source}:{error_type}"
        self.alert_counters[counter_key] = self.alert_counters.get(counter_key, 0) + 1

        # 閾値チェック
        if self.alert_counters[counter_key] >= self.monitoring_config['alert_threshold']:
            # インシデント作成
            await self._create_incident(
                title=f"Repeated errors: {error_type}",
                description=f"Multiple {error_type} errors from {source}",
                severity=IncidentSeverity.MEDIUM,
                source=source,
                affected_systems=[source]
            )

            # カウンターリセット
            self.alert_counters[counter_key] = 0

    async def _process_anomaly_report(self, anomaly_data: Dict[str, Any]):
        """異常検知報告処理"""
        anomaly_type = anomaly_data.get('type', 'unknown')
        confidence = anomaly_data.get('confidence', 0.5)

        # 高信頼度の異常のみ処理
        if confidence > 0.7:
            await self._create_incident(
                title=f"Anomaly detected: {anomaly_type}",
                description=anomaly_data.get('description', ''),
                severity=IncidentSeverity.HIGH if confidence > 0.9 else IncidentSeverity.MEDIUM,
                source='anomaly_detection',
                affected_systems=anomaly_data.get('affected_systems', [])
            )

    async def _process_resolution_report(self, resolution_data: Dict[str, Any]):
        """解決報告処理"""
        incident_id = resolution_data.get('incident_id')

        if incident_id in self.active_incidents:
            # 外部からの解決報告
            await self._resolve_incident(resolution_data)

            # パターン学習
            self._learn_from_resolution(resolution_data)

    def _learn_from_resolution(self, resolution_data: Dict[str, Any]):
        """解決策から学習"""
        pattern = {
            'symptoms': resolution_data.get('symptoms', []),
            'root_cause': resolution_data.get('root_cause'),
            'resolution': resolution_data.get('resolution'),
            'effectiveness': resolution_data.get('effectiveness', 1.0)
        }

        self.incident_patterns.append(pattern)

        # パターンデータベースの更新
        root_cause = resolution_data.get('root_cause', 'unknown')
        if root_cause not in self.resolution_database:
            self.resolution_database[root_cause] = []

        self.resolution_database[root_cause].append({
            'resolution': resolution_data.get('resolution'),
            'success_rate': resolution_data.get('effectiveness', 1.0)
        })

    async def _execute_incident_task(self, task_data: Dict[str, Any]):
        """インシデントタスクの実行"""
        task_id = task_data.get('task_id')
        description = task_data.get('description', '')

        self.logger.info(f"Executing incident task {task_id}: {description}")

        # インシデント関連タスクの実行
        if "investigate" in description.lower():
            result = await self._execute_investigation_task(task_data)
        elif "mitigate" in description.lower():
            result = await self._execute_mitigation_task(task_data)
        else:
            # 一般的なインシデントタスク
            result = await self._execute_general_incident_task(task_data)

        # 完了報告
        completion_msg = ElderMessage(
            message_id=f"task_complete_{task_id}",
            source_elder=self.elder_name,
            target_elder="claude_elder",
            message_type=MessageType.REPORT,
            payload={
                'type': 'task_complete',
                'task_id': task_id,
                'result': result
            },
            priority=6
        )

        await self.send_message(completion_msg)

    async def _execute_investigation_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """調査タスクの実行"""
        # シミュレーション
        await asyncio.sleep(3)

        return {
            'status': 'completed',
            'investigation': {
                'findings': ['Memory leak detected', 'Configuration mismatch'],
                'root_cause': 'Improper resource management',
                'evidence': 5
            }
        }

    async def _execute_mitigation_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """緩和タスクの実行"""
        # シミュレーション
        await asyncio.sleep(2)

        return {
            'status': 'completed',
            'mitigation': {

                'effectiveness': 0.8,
                'permanent_fix_needed': True
            }
        }

    async def _execute_general_incident_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """一般的なインシデントタスクの実行"""
        # シミュレーション
        await asyncio.sleep(1)

        return {
            'status': 'completed',
            'message': 'Incident task completed successfully'
        }

# プロセス起動
if __name__ == "__main__":
    from libs.elder_process_base import run_elder_process
    run_elder_process(IncidentSageProcess)
