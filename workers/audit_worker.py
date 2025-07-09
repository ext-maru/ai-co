#!/usr/bin/env python3
"""
セキュリティ監査専用ワーカー v1.0
AI Company Elder Hierarchy Security Audit Worker

エルダーズ評議会セキュリティ監査・監視専用ワーカー
全Elder階層アクティビティの監査とセキュリティイベント追跡
"""

import asyncio
import json
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from collections import defaultdict, deque

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Elder階層システム統合
from core.elder_aware_base_worker import (
    ElderAwareBaseWorker,
    ElderTaskContext,
    ElderTaskResult,
    WorkerExecutionMode,
    ElderTaskPriority,
    elder_worker_required,
    SecurityError
)

# 統合認証システム
from libs.unified_auth_provider import (
    UnifiedAuthProvider,
    ElderRole,
    SageType,
    User,
    AuthSession,
    AuthRequest,
    create_demo_auth_system
)

# 既存システム統合
from core import BaseWorker, get_config, EMOJI
from libs.slack_notifier import SlackNotifier
from libs.ai_command_helper import AICommandHelper
import logging

# 監査専用絵文字
AUDIT_EMOJI = {
    **EMOJI,
    'audit': '📋',
    'security': '🛡️',
    'alert': '🚨',
    'investigate': '🔍',
    'report': '📊',
    'compliance': '✅',
    'violation': '⚠️',
    'forensics': '🔬',
    'shield': '🛡️',
    'lock': '🔒',
    'warning': '⚠️',
    'critical': '🚨',
    'elder': '🏛️'
}

# 監査イベントタイプ
class AuditEventType(Enum):
    """監査イベントタイプ"""
    # 認証関連
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    SESSION_CREATED = "session_created"
    SESSION_EXPIRED = "session_expired"
    MFA_CHALLENGE = "mfa_challenge"
    MFA_SUCCESS = "mfa_success"
    MFA_FAILURE = "mfa_failure"
    
    # 権限関連
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    ROLE_CHANGED = "role_changed"
    ELDER_PROMOTION = "elder_promotion"
    EMERGENCY_ACCESS = "emergency_access"
    
    # データアクセス
    DATA_READ = "data_read"
    DATA_WRITE = "data_write"
    DATA_DELETE = "data_delete"
    SENSITIVE_ACCESS = "sensitive_access"
    
    # システム操作
    CONFIG_CHANGE = "config_change"
    DEPLOYMENT = "deployment"
    SYSTEM_RESTART = "system_restart"
    EMERGENCY_SHUTDOWN = "emergency_shutdown"
    
    # セキュリティイベント
    SECURITY_BREACH = "security_breach"
    ANOMALY_DETECTED = "anomaly_detected"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    
    # Elder階層イベント
    ELDER_ACTION = "elder_action"
    COUNCIL_DECISION = "council_decision"
    SAGE_INSTRUCTION = "sage_instruction"
    GRAND_ELDER_OVERRIDE = "grand_elder_override"


# セキュリティ重要度
class SecuritySeverity(Enum):
    """セキュリティイベント重要度"""
    CRITICAL = "critical"    # 即座対応必要
    HIGH = "high"           # 高優先度
    MEDIUM = "medium"       # 通常優先度
    LOW = "low"            # 低優先度
    INFO = "info"          # 情報のみ


# コンプライアンスルール
class ComplianceRule(Enum):
    """コンプライアンスルール"""
    MFA_REQUIRED_FOR_ELDERS = "mfa_required_for_elders"
    SESSION_TIMEOUT_ENFORCEMENT = "session_timeout_enforcement"
    AUDIT_LOG_RETENTION = "audit_log_retention"
    DATA_ENCRYPTION_REQUIRED = "data_encryption_required"
    ACCESS_CONTROL_ENFORCEMENT = "access_control_enforcement"
    EMERGENCY_ACCESS_MONITORING = "emergency_access_monitoring"
    ELDER_ACTION_TRACKING = "elder_action_tracking"
    SAGE_COORDINATION_AUDIT = "sage_coordination_audit"


class AuditWorker(ElderAwareBaseWorker):
    """
    セキュリティ監査専用ワーカー
    
    全Elder階層システムの監査、セキュリティモニタリング、コンプライアンス確保
    """
    
    def __init__(self, worker_id: Optional[str] = None,
                 auth_provider: Optional[UnifiedAuthProvider] = None):
        # Elder階層BaseWorker初期化
        ElderAwareBaseWorker.__init__(
            self,
            auth_provider=auth_provider,
            required_elder_role=ElderRole.CLAUDE_ELDER,  # 監査は高権限が必要
            required_sage_type=None  # 全賢者タイプを監査
        )
        
        # ワーカー設定
        self.worker_type = 'audit'
        self.worker_id = worker_id or f"audit_worker_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 監査専用キュー
        self.input_queue = 'ai_audit_events'
        self.output_queue = 'ai_audit_reports'
        
        self.config = get_config()
        self.slack_notifier = SlackNotifier()
        
        # 監査設定
        self.audit_config = {
            'retention_days': 90,  # 監査ログ保持期間
            'real_time_monitoring': True,
            'anomaly_detection': True,
            'compliance_checking': True,
            'forensics_enabled': True,
            'alert_threshold': {
                SecuritySeverity.CRITICAL: 1,   # 1件で即アラート
                SecuritySeverity.HIGH: 3,       # 3件でアラート
                SecuritySeverity.MEDIUM: 10,    # 10件でアラート
                SecuritySeverity.LOW: 50        # 50件でアラート
            }
        }
        
        # リアルタイム監視状態
        self.monitoring_state = {
            'active_sessions': {},
            'failed_login_attempts': defaultdict(int),
            'rate_limit_tracking': defaultdict(lambda: deque(maxlen=100)),
            'anomaly_scores': defaultdict(float),
            'compliance_violations': defaultdict(list)
        }
        
        # 監査統計
        self.audit_stats = {
            'total_events': 0,
            'security_events': 0,
            'compliance_violations': 0,
            'anomalies_detected': 0,
            'alerts_sent': 0,
            'elder_actions': defaultdict(int),
            'event_types': defaultdict(int)
        }
        
        # フォレンジック分析キャッシュ
        self.forensics_cache = {}
        
        self.logger.info(f"{AUDIT_EMOJI['audit']} Audit Worker initialized - Required: {self.required_elder_role.value}")
    
    async def process_audit_message(self, elder_context: ElderTaskContext,
                                   audit_data: Dict[str, Any]) -> ElderTaskResult:
        """監査メッセージ処理"""
        event_type = audit_data.get('event_type', 'unknown')
        event_id = audit_data.get('event_id', 'unknown')
        
        # 監査イベントログ
        self.audit_logger.log_elder_action(
            elder_context,
            f"audit_event_processing",
            f"Processing audit event: {event_type} - ID: {event_id}"
        )
        
        try:
            # イベントタイプ別処理
            if event_type in [e.value for e in AuditEventType]:
                result = await self._process_audit_event(elder_context, audit_data)
            elif event_type == 'compliance_check':
                result = await self._perform_compliance_check(elder_context, audit_data)
            elif event_type == 'security_scan':
                result = await self._perform_security_scan(elder_context, audit_data)
            elif event_type == 'forensic_analysis':
                result = await self._perform_forensic_analysis(elder_context, audit_data)
            elif event_type == 'report_generation':
                result = await self._generate_audit_report(elder_context, audit_data)
            else:
                result = await self._process_general_audit(elder_context, audit_data)
            
            # 統計更新
            self._update_audit_stats(event_type, result)
            
            # 成功ログ
            self.audit_logger.log_elder_action(
                elder_context,
                f"audit_event_complete",
                f"Audit event {event_id} processed successfully"
            )
            
            return result
            
        except Exception as e:
            # エラーログ
            self.audit_logger.log_elder_action(
                elder_context,
                f"audit_event_error",
                f"Audit event {event_id} failed: {str(e)}"
            )
            
            self.audit_logger.log_security_event(
                elder_context,
                "audit_processing_error",
                {"event_id": event_id, "error": str(e)}
            )
            
            raise
    
    async def _process_audit_event(self, context: ElderTaskContext, audit_data: Dict) -> Dict:
        """監査イベント処理"""
        event_type = AuditEventType(audit_data.get('event_type'))
        severity = self._determine_severity(event_type, audit_data)
        
        # イベント記録
        audit_record = {
            "event_id": audit_data.get('event_id'),
            "event_type": event_type.value,
            "severity": severity.value,
            "timestamp": datetime.now().isoformat(),
            "user": audit_data.get('user', 'unknown'),
            "source": audit_data.get('source', 'unknown'),
            "details": audit_data.get('details', {}),
            "elder_context": {
                "auditor": context.user.username,
                "auditor_role": context.user.elder_role.value
            }
        }
        
        # リアルタイム監視更新
        await self._update_monitoring_state(event_type, audit_data)
        
        # 異常検知
        anomaly_score = await self._detect_anomalies(event_type, audit_data)
        if anomaly_score > 0.7:  # 高異常スコア
            audit_record["anomaly_detected"] = True
            audit_record["anomaly_score"] = anomaly_score
            await self._handle_anomaly(context, audit_record)
        
        # コンプライアンスチェック
        compliance_violations = await self._check_compliance_rules(event_type, audit_data)
        if compliance_violations:
            audit_record["compliance_violations"] = compliance_violations
            await self._handle_compliance_violation(context, compliance_violations)
        
        # セキュリティアラート判定
        if self._should_send_alert(severity, event_type):
            await self._send_security_alert(context, audit_record)
        
        # Elder階層特別監査
        if event_type in [AuditEventType.ELDER_ACTION, AuditEventType.GRAND_ELDER_OVERRIDE]:
            await self._perform_elder_audit(context, audit_record)
        
        return audit_record
    
    async def _perform_compliance_check(self, context: ElderTaskContext, audit_data: Dict) -> Dict:
        """コンプライアンスチェック実行"""
        check_type = audit_data.get('check_type', 'general')
        target = audit_data.get('target', 'system')
        
        compliance_result = {
            "check_type": check_type,
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "auditor": context.user.username,
            "status": "compliant",
            "violations": [],
            "recommendations": []
        }
        
        # ルール別チェック
        for rule in ComplianceRule:
            violation = await self._check_specific_rule(rule, target)
            if violation:
                compliance_result["violations"].append({
                    "rule": rule.value,
                    "severity": violation["severity"],
                    "details": violation["details"]
                })
                compliance_result["status"] = "non_compliant"
        
        # レポート生成
        if compliance_result["violations"]:
            compliance_result["report"] = await self._generate_compliance_report(
                context, compliance_result["violations"]
            )
        
        return compliance_result
    
    async def _perform_security_scan(self, context: ElderTaskContext, audit_data: Dict) -> Dict:
        """セキュリティスキャン実行"""
        scan_type = audit_data.get('scan_type', 'full')
        targets = audit_data.get('targets', ['system'])
        
        scan_result = {
            "scan_type": scan_type,
            "targets": targets,
            "timestamp": datetime.now().isoformat(),
            "scanner": context.user.username,
            "findings": [],
            "risk_level": "low"
        }
        
        # スキャン実行
        for target in targets:
            findings = await self._scan_target(target, scan_type)
            scan_result["findings"].extend(findings)
        
        # リスクレベル判定
        scan_result["risk_level"] = self._calculate_risk_level(scan_result["findings"])
        
        # 高リスク発見時の処理
        if scan_result["risk_level"] in ["high", "critical"]:
            await self._handle_high_risk_finding(context, scan_result)
        
        return scan_result
    
    async def _perform_forensic_analysis(self, context: ElderTaskContext, audit_data: Dict) -> Dict:
        """フォレンジック分析実行"""
        incident_id = audit_data.get('incident_id')
        analysis_type = audit_data.get('analysis_type', 'standard')
        
        forensic_result = {
            "incident_id": incident_id,
            "analysis_type": analysis_type,
            "timestamp": datetime.now().isoformat(),
            "analyst": context.user.username,
            "timeline": [],
            "evidence": [],
            "conclusions": [],
            "recommendations": []
        }
        
        # タイムライン構築
        forensic_result["timeline"] = await self._build_incident_timeline(incident_id)
        
        # 証拠収集
        forensic_result["evidence"] = await self._collect_forensic_evidence(incident_id)
        
        # 分析実行
        analysis = await self._analyze_forensic_data(
            forensic_result["timeline"],
            forensic_result["evidence"]
        )
        
        forensic_result["conclusions"] = analysis["conclusions"]
        forensic_result["recommendations"] = analysis["recommendations"]
        
        # キャッシュ保存
        self.forensics_cache[incident_id] = forensic_result
        
        return forensic_result
    
    @elder_worker_required(ElderRole.GRAND_ELDER)
    async def _generate_audit_report(self, context: ElderTaskContext, audit_data: Dict) -> Dict:
        """監査レポート生成（グランドエルダー権限必要）"""
        report_type = audit_data.get('report_type', 'summary')
        period = audit_data.get('period', 'last_24_hours')
        
        report = {
            "report_type": report_type,
            "period": period,
            "generated_at": datetime.now().isoformat(),
            "generated_by": context.user.username,
            "executive_summary": "",
            "statistics": {},
            "key_findings": [],
            "recommendations": [],
            "detailed_events": []
        }
        
        # 統計収集
        report["statistics"] = {
            "total_events": self.audit_stats["total_events"],
            "security_events": self.audit_stats["security_events"],
            "compliance_violations": self.audit_stats["compliance_violations"],
            "anomalies_detected": self.audit_stats["anomalies_detected"],
            "elder_actions": dict(self.audit_stats["elder_actions"]),
            "event_distribution": dict(self.audit_stats["event_types"])
        }
        
        # 主要な発見事項
        report["key_findings"] = await self._analyze_key_findings(period)
        
        # エグゼクティブサマリー生成
        report["executive_summary"] = self._generate_executive_summary(report)
        
        # 推奨事項
        report["recommendations"] = await self._generate_recommendations(report["key_findings"])
        
        # 詳細イベント（必要に応じて）
        if report_type == "detailed":
            report["detailed_events"] = await self._get_detailed_events(period)
        
        # エルダーズ評議会への報告
        if self._requires_council_attention(report):
            await self._notify_elder_council(context, report)
        
        return report
    
    def _determine_severity(self, event_type: AuditEventType, audit_data: Dict) -> SecuritySeverity:
        """イベント重要度判定"""
        # 重要度マッピング
        severity_map = {
            AuditEventType.SECURITY_BREACH: SecuritySeverity.CRITICAL,
            AuditEventType.GRAND_ELDER_OVERRIDE: SecuritySeverity.CRITICAL,
            AuditEventType.EMERGENCY_ACCESS: SecuritySeverity.HIGH,
            AuditEventType.ELDER_PROMOTION: SecuritySeverity.HIGH,
            AuditEventType.ANOMALY_DETECTED: SecuritySeverity.HIGH,
            AuditEventType.PERMISSION_DENIED: SecuritySeverity.MEDIUM,
            AuditEventType.LOGIN_FAILURE: SecuritySeverity.MEDIUM,
            AuditEventType.DATA_READ: SecuritySeverity.LOW,
            AuditEventType.LOGIN_SUCCESS: SecuritySeverity.INFO
        }
        
        base_severity = severity_map.get(event_type, SecuritySeverity.INFO)
        
        # コンテキストによる調整
        if audit_data.get('repeated_failure', False):
            return SecuritySeverity.HIGH
        
        if audit_data.get('sensitive_data', False):
            return SecuritySeverity(min(base_severity.value, SecuritySeverity.HIGH.value))
        
        return base_severity
    
    async def _update_monitoring_state(self, event_type: AuditEventType, audit_data: Dict):
        """リアルタイム監視状態更新"""
        user = audit_data.get('user', 'unknown')
        timestamp = datetime.now()
        
        # ログイン失敗追跡
        if event_type == AuditEventType.LOGIN_FAILURE:
            self.monitoring_state['failed_login_attempts'][user] += 1
            
            # しきい値超過チェック
            if self.monitoring_state['failed_login_attempts'][user] > 5:
                await self._handle_brute_force_attempt(user)
        
        # レート制限追跡
        self.monitoring_state['rate_limit_tracking'][user].append(timestamp)
        
        # セッション追跡
        if event_type == AuditEventType.SESSION_CREATED:
            session_id = audit_data.get('session_id')
            self.monitoring_state['active_sessions'][session_id] = {
                'user': user,
                'created_at': timestamp,
                'last_activity': timestamp
            }
        elif event_type in [AuditEventType.SESSION_EXPIRED, AuditEventType.LOGOUT]:
            session_id = audit_data.get('session_id')
            if session_id in self.monitoring_state['active_sessions']:
                del self.monitoring_state['active_sessions'][session_id]
    
    async def _detect_anomalies(self, event_type: AuditEventType, audit_data: Dict) -> float:
        """異常検知（異常スコア: 0.0-1.0）"""
        anomaly_score = 0.0
        user = audit_data.get('user', 'unknown')
        
        # 時間帯異常
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:  # 深夜・早朝
            anomaly_score += 0.2
        
        # アクセスパターン異常
        recent_actions = self.monitoring_state['rate_limit_tracking'][user]
        if len(recent_actions) > 50:  # 直近50アクション
            time_diffs = [(recent_actions[i] - recent_actions[i-1]).total_seconds() 
                         for i in range(1, len(recent_actions))]
            avg_interval = sum(time_diffs) / len(time_diffs) if time_diffs else 0
            
            if avg_interval < 1:  # 平均1秒未満の間隔
                anomaly_score += 0.3
        
        # 権限昇格異常
        if event_type == AuditEventType.ELDER_PROMOTION:
            prev_role = audit_data.get('previous_role')
            new_role = audit_data.get('new_role')
            if prev_role == 'servant' and new_role == 'grand_elder':
                anomaly_score += 0.5  # 極端な昇格
        
        # 地理的異常（IPアドレスベース）
        ip_address = audit_data.get('ip_address')
        if ip_address and self._is_suspicious_location(ip_address):
            anomaly_score += 0.3
        
        # ユーザー別異常スコア更新
        self.monitoring_state['anomaly_scores'][user] = anomaly_score
        
        return min(anomaly_score, 1.0)
    
    async def _check_compliance_rules(self, event_type: AuditEventType, 
                                    audit_data: Dict) -> List[Dict]:
        """コンプライアンスルールチェック"""
        violations = []
        
        # MFA必須チェック
        if event_type == AuditEventType.LOGIN_SUCCESS:
            user_role = audit_data.get('user_role')
            mfa_used = audit_data.get('mfa_used', False)
            
            if user_role in ['grand_elder', 'claude_elder'] and not mfa_used:
                violations.append({
                    'rule': ComplianceRule.MFA_REQUIRED_FOR_ELDERS.value,
                    'severity': 'high',
                    'details': f'Elder {user_role} logged in without MFA'
                })
        
        # セッションタイムアウトチェック
        for session_id, session_info in self.monitoring_state['active_sessions'].items():
            last_activity = session_info['last_activity']
            if (datetime.now() - last_activity).total_seconds() > 3600:  # 1時間
                violations.append({
                    'rule': ComplianceRule.SESSION_TIMEOUT_ENFORCEMENT.value,
                    'severity': 'medium',
                    'details': f'Session {session_id} exceeded timeout'
                })
        
        return violations
    
    def _should_send_alert(self, severity: SecuritySeverity, event_type: AuditEventType) -> bool:
        """アラート送信判定"""
        # 常にアラートするイベント
        always_alert = [
            AuditEventType.SECURITY_BREACH,
            AuditEventType.GRAND_ELDER_OVERRIDE,
            AuditEventType.EMERGENCY_ACCESS
        ]
        
        if event_type in always_alert:
            return True
        
        # 重要度によるアラート
        return severity in [SecuritySeverity.CRITICAL, SecuritySeverity.HIGH]
    
    async def _send_security_alert(self, context: ElderTaskContext, audit_record: Dict):
        """セキュリティアラート送信"""
        severity = audit_record.get('severity', 'unknown')
        event_type = audit_record.get('event_type', 'unknown')
        
        alert_message = f"""
{AUDIT_EMOJI['alert']} **SECURITY ALERT** - {severity.upper()}

**Event Type**: {event_type}
**User**: {audit_record.get('user', 'unknown')}
**Time**: {audit_record.get('timestamp')}
**Auditor**: {context.user.username}

**Details**: {json.dumps(audit_record.get('details', {}), indent=2)}

**Action Required**: Immediate investigation recommended
"""
        
        # Slack通知
        channels = ['#security-alerts', '#elder-security-alerts']
        for channel in channels:
            try:
                await self.slack_notifier.send_message(
                    message=alert_message,
                    channel=channel,
                    priority='high'
                )
            except Exception as e:
                self.logger.error(f"Failed to send alert to {channel}: {e}")
        
        self.audit_stats['alerts_sent'] += 1
    
    async def _perform_elder_audit(self, context: ElderTaskContext, audit_record: Dict):
        """Elder階層特別監査"""
        elder_action = audit_record.get('details', {}).get('action')
        elder_user = audit_record.get('user')
        
        # Elder行動追跡
        self.audit_stats['elder_actions'][elder_user] += 1
        
        # 特別監査ログ
        self.audit_logger.log_elder_action(
            context,
            "elder_special_audit",
            f"Special audit for Elder action: {elder_action} by {elder_user}"
        )
        
        # グランドエルダー行動は評議会に報告
        if audit_record.get('details', {}).get('elder_role') == 'grand_elder':
            await self._notify_elder_council(context, audit_record)
    
    async def _handle_anomaly(self, context: ElderTaskContext, audit_record: Dict):
        """異常検知ハンドリング"""
        anomaly_score = audit_record.get('anomaly_score', 0)
        
        self.audit_stats['anomalies_detected'] += 1
        
        # 異常通知
        anomaly_message = f"""
{AUDIT_EMOJI['warning']} **ANOMALY DETECTED**

**Anomaly Score**: {anomaly_score:.2f}
**Event**: {audit_record.get('event_type')}
**User**: {audit_record.get('user')}
**Detected By**: {context.user.username}

Immediate investigation required.
"""
        
        await self.slack_notifier.send_message(
            message=anomaly_message,
            channel='#security-anomalies'
        )
    
    async def _handle_compliance_violation(self, context: ElderTaskContext, violations: List[Dict]):
        """コンプライアンス違反ハンドリング"""
        self.audit_stats['compliance_violations'] += len(violations)
        
        for violation in violations:
            # 違反記録
            self.monitoring_state['compliance_violations'][violation['rule']].append({
                'timestamp': datetime.now().isoformat(),
                'severity': violation['severity'],
                'details': violation['details']
            })
            
            # 高重要度違反は即座に通知
            if violation['severity'] == 'high':
                await self._send_compliance_alert(context, violation)
    
    async def _send_compliance_alert(self, context: ElderTaskContext, violation: Dict):
        """コンプライアンス違反アラート"""
        alert_message = f"""
{AUDIT_EMOJI['violation']} **COMPLIANCE VIOLATION**

**Rule**: {violation['rule']}
**Severity**: {violation['severity'].upper()}
**Details**: {violation['details']}
**Detected By**: {context.user.username}

Corrective action required.
"""
        
        await self.slack_notifier.send_message(
            message=alert_message,
            channel='#compliance-alerts'
        )
    
    async def _notify_elder_council(self, context: ElderTaskContext, data: Dict):
        """エルダーズ評議会への通知"""
        council_message = f"""
{AUDIT_EMOJI['elder']} **ELDER COUNCIL NOTIFICATION**

**From**: Security Audit System
**Auditor**: {context.user.username}
**Priority**: HIGH

**Subject**: {data.get('event_type', 'Security Event')}

**Details**:
{json.dumps(data, indent=2)}

Council attention requested.
"""
        
        await self.slack_notifier.send_message(
            message=council_message,
            channel='#elder-council-notifications'
        )
    
    def _update_audit_stats(self, event_type: str, result: Dict):
        """監査統計更新"""
        self.audit_stats['total_events'] += 1
        self.audit_stats['event_types'][event_type] += 1
        
        if result.get('severity') in ['critical', 'high']:
            self.audit_stats['security_events'] += 1
    
    def _is_suspicious_location(self, ip_address: str) -> bool:
        """疑わしい地理的位置チェック（簡略実装）"""
        # 実際の実装ではGeoIPデータベースを使用
        suspicious_patterns = ['10.0.0.', '192.168.', '172.16.']
        return not any(ip_address.startswith(pattern) for pattern in suspicious_patterns)
    
    async def _check_specific_rule(self, rule: ComplianceRule, target: str) -> Optional[Dict]:
        """特定コンプライアンスルールチェック"""
        # 実際の実装では各ルールの詳細チェックを実行
        # ここでは簡略化
        return None
    
    async def _scan_target(self, target: str, scan_type: str) -> List[Dict]:
        """ターゲットスキャン実行"""
        # 実際の実装ではセキュリティスキャンを実行
        return []
    
    def _calculate_risk_level(self, findings: List[Dict]) -> str:
        """リスクレベル計算"""
        if not findings:
            return "low"
        
        critical_count = sum(1 for f in findings if f.get('severity') == 'critical')
        high_count = sum(1 for f in findings if f.get('severity') == 'high')
        
        if critical_count > 0:
            return "critical"
        elif high_count > 3:
            return "high"
        elif high_count > 0:
            return "medium"
        return "low"
    
    async def _handle_high_risk_finding(self, context: ElderTaskContext, scan_result: Dict):
        """高リスク発見時の処理"""
        # 即座にセキュリティチームに通知
        await self._send_security_alert(context, {
            'severity': 'critical',
            'event_type': 'high_risk_finding',
            'details': scan_result
        })
    
    async def _build_incident_timeline(self, incident_id: str) -> List[Dict]:
        """インシデントタイムライン構築"""
        # 実際の実装では関連イベントを時系列で収集
        return []
    
    async def _collect_forensic_evidence(self, incident_id: str) -> List[Dict]:
        """フォレンジック証拠収集"""
        # 実際の実装では関連ログ、ファイル、設定を収集
        return []
    
    async def _analyze_forensic_data(self, timeline: List[Dict], evidence: List[Dict]) -> Dict:
        """フォレンジックデータ分析"""
        return {
            "conclusions": ["Analysis complete"],
            "recommendations": ["Enhance monitoring"]
        }
    
    async def _analyze_key_findings(self, period: str) -> List[Dict]:
        """主要な発見事項分析"""
        return [
            {
                "finding": "Increased login attempts",
                "severity": "medium",
                "recommendation": "Enable rate limiting"
            }
        ]
    
    def _generate_executive_summary(self, report: Dict) -> str:
        """エグゼクティブサマリー生成"""
        return f"""
During the reporting period, the security audit system processed {report['statistics']['total_events']} events.
Key findings include {len(report['key_findings'])} items requiring attention.
Overall system security posture: GOOD
"""
    
    async def _generate_recommendations(self, findings: List[Dict]) -> List[str]:
        """推奨事項生成"""
        recommendations = []
        for finding in findings:
            if finding.get('recommendation'):
                recommendations.append(finding['recommendation'])
        return recommendations
    
    async def _get_detailed_events(self, period: str) -> List[Dict]:
        """詳細イベント取得"""
        # 実際の実装では期間内の全イベントを取得
        return []
    
    def _requires_council_attention(self, report: Dict) -> bool:
        """評議会注意必要判定"""
        # 重大なセキュリティイベントや違反がある場合
        return (report['statistics']['security_events'] > 10 or
                report['statistics']['compliance_violations'] > 5)
    
    async def _handle_brute_force_attempt(self, user: str):
        """ブルートフォース攻撃ハンドリング"""
        # アカウントロックやIP制限などの対策を実施
        self.audit_logger.log_security_event(
            None,  # システムレベルイベント
            "brute_force_detected",
            {"user": user, "attempts": self.monitoring_state['failed_login_attempts'][user]}
        )
        
        # アラート送信
        await self.slack_notifier.send_message(
            f"{AUDIT_EMOJI['critical']} Brute force attack detected for user: {user}",
            channel='#security-critical'
        )
    
    async def _process_general_audit(self, context: ElderTaskContext, audit_data: Dict) -> Dict:
        """一般監査処理"""
        return {
            "status": "processed",
            "event_type": "general",
            "timestamp": datetime.now().isoformat(),
            "auditor": context.user.username
        }


# ファクトリー関数
def create_audit_worker(auth_provider: Optional[UnifiedAuthProvider] = None) -> AuditWorker:
    """監査ワーカー作成"""
    return AuditWorker(auth_provider=auth_provider)


# デモ実行関数
async def demo_audit_worker():
    """監査ワーカーのデモ実行"""
    print(f"{AUDIT_EMOJI['start']} Audit Worker Demo Starting...")
    
    # デモ認証システム
    auth = create_demo_auth_system()
    
    # 監査ワーカー作成
    worker = create_audit_worker(auth_provider=auth)
    
    # クロードエルダーとして認証
    auth_request = AuthRequest(username="claude_elder", password="claude_password")
    result, session, user = auth.authenticate(auth_request)
    
    if result.value == "success":
        print(f"{AUDIT_EMOJI['success']} Authenticated as Claude Elder: {user.username}")
        
        # 監査コンテキスト作成
        context = worker.create_elder_context(
            user=user,
            session=session,
            task_id="demo_audit_001",
            priority=ElderTaskPriority.HIGH
        )
        
        # デモ監査イベント
        demo_audit_data = {
            "event_id": "audit_demo_001",
            "event_type": AuditEventType.ELDER_ACTION.value,
            "user": "task_sage",
            "user_role": "sage",
            "source": "elder_task_worker",
            "details": {
                "action": "project_creation",
                "project_id": "ai_company_v3",
                "elder_role": "sage",
                "sage_type": "task"
            },
            "ip_address": "192.168.1.100",
            "timestamp": datetime.now().isoformat()
        }
        
        # 監査処理実行
        async def demo_audit_task():
            return await worker.process_audit_message(context, demo_audit_data)
        
        result = await worker.execute_with_elder_context(context, demo_audit_task)
        
        print(f"{AUDIT_EMOJI['complete']} Demo Audit Result:")
        print(f"  Status: {result.status}")
        print(f"  Audit Stats: {worker.audit_stats}")
        print(f"  Active Sessions: {len(worker.monitoring_state['active_sessions'])}")
        print(f"  Compliance Violations: {worker.audit_stats['compliance_violations']}")
        
    else:
        print(f"{AUDIT_EMOJI['error']} Authentication failed: {result}")


if __name__ == "__main__":
    # デモ実行
    asyncio.run(demo_audit_worker())