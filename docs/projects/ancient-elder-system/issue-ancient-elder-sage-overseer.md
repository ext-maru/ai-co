# 🧙‍♂️ Ancient Elder Issue #5: 4賢者監督魔法 (Four Sages Overseer Magic)

## 概要
4賢者（ナレッジ・タスク・インシデント・RAG）への相談義務履行、賢者活動の実質性、役割遵守を監査する古代魔法システムの実装

## 背景
4賢者システムは形式的には稼働しているが、実際には相談が形骸化したり、賢者の助言が無視されたり、役割を逸脱した活動が行われている可能性がある。賢者システムの真の稼働を監督する魔法が必要。

## 実装要件

### 1. 基底クラス継承
```python
from souls.base_soul import BaseSoul, ElderType
from libs.four_sages import SageType, SageActivity

class AncientElderSageOverseer(BaseSoul):
    """4賢者を監督するエンシェントエルダー"""
    
    def __init__(self):
        super().__init__(
            name="AncientElder_SageOverseer",
            elder_type=ElderType.ANCIENT_ELDER,
            specialty="sage_oversight"
        )
        self.sage_duties = {
            SageType.KNOWLEDGE: {
                "weekly_update": True,
                "best_practices_monitoring": True,
                "learning_evolution": True
            },
            SageType.TASK: {
                "priority_management": True,
                "daily_progress_report": True,
                "dependency_analysis": True
            },
            SageType.INCIDENT: {
                "5min_detection": True,
                "root_cause_analysis": True,
                "prevention_measures": True
            },
            SageType.RAG: {
                "monthly_research": True,
                "optimization_proposals": True,
                "tech_debt_detection": True
            }
        }
```

### 2. 賢者活動監査ロジック

#### 2.1 相談義務履行検証
```python
async def verify_sage_consultation_compliance(self, time_range: TimeRange) -> ConsultationComplianceReport:
    """賢者への相談義務履行を検証"""
    
    # クロードエルダーのタスク実行ログ取得
    task_logs = await self._get_task_execution_logs(time_range)
    
    violations = []
    consultation_stats = {sage: {"required": 0, "actual": 0} for sage in SageType}
    
    for task in task_logs:
        # タスクタイプから必要な相談を判定
        required_consultations = self._determine_required_consultations(task)
        
        # 実際の相談記録を取得
        actual_consultations = await self._get_sage_consultation_logs(task.id)
        
        # 相談義務違反の検出
        for sage_type in required_consultations:
            consultation_stats[sage_type]["required"] += 1
            
            sage_consultation = actual_consultations.get(sage_type)
            if not sage_consultation:
                violations.append(ConsultationViolation(
                    type="MISSING_CONSULTATION",
                    severity="CRITICAL",
                    task_id=task.id,
                    sage=sage_type,
                    reason="Required consultation not performed"
                ))
            else:
                consultation_stats[sage_type]["actual"] += 1
                
                # 相談の実質性検証
                quality = await self._assess_consultation_quality(sage_consultation)
                if quality["score"] < 50:
                    violations.append(ConsultationViolation(
                        type="LOW_QUALITY_CONSULTATION",
                        severity="HIGH",
                        task_id=task.id,
                        sage=sage_type,
                        evidence=quality["issues"]
                    ))
    
    # インシデント発生時の4賢者会議検証
    incidents = await self._get_incident_logs(time_range)
    for incident in incidents:
        council_log = await self._get_sage_council_log(incident.id)
        if not council_log:
            violations.append(ConsultationViolation(
                type="MISSING_COUNCIL",
                severity="CRITICAL",
                incident_id=incident.id,
                reason="4賢者会議が開催されていない"
            ))
        elif not all(sage in council_log.participants for sage in SageType):
            missing = [s for s in SageType if s not in council_log.participants]
            violations.append(ConsultationViolation(
                type="INCOMPLETE_COUNCIL",
                severity="HIGH",
                incident_id=incident.id,
                missing_sages=missing
            ))
    
    return ConsultationComplianceReport(
        period=time_range,
        consultation_stats=consultation_stats,
        violations=violations,
        compliance_rate=self._calculate_consultation_compliance(consultation_stats)
    )
```

#### 2.2 賢者活動実質性検証
```python
async def verify_sage_activity_quality(self, sage_type: SageType, time_range: TimeRange) -> SageActivityReport:
    """賢者活動の実質性を検証"""
    
    activities = await self._get_sage_activities(sage_type, time_range)
    quality_issues = []
    
    if sage_type == SageType.KNOWLEDGE:
        # ナレッジ賢者の検証
        updates = [a for a in activities if a.type == "knowledge_update"]
        
        # 週次更新の確認
        weeks_in_range = (time_range.end - time_range.start).days // 7
        if len(updates) < weeks_in_range:
            quality_issues.append(QualityIssue(
                type="MISSING_WEEKLY_UPDATE",
                severity="HIGH",
                expected=weeks_in_range,
                actual=len(updates)
            ))
        
        # 更新内容の実質性
        for update in updates:
            content_analysis = await self._analyze_knowledge_content(update)
            if content_analysis["new_information_ratio"] < 0.2:
                quality_issues.append(QualityIssue(
                    type="LOW_VALUE_UPDATE",
                    severity="MEDIUM",
                    activity_id=update.id,
                    evidence="80%以上が既存情報の繰り返し"
                ))
    
    elif sage_type == SageType.TASK:
        # タスク賢者の検証
        daily_reports = [a for a in activities if a.type == "daily_progress"]
        
        # 日次報告の確認
        days_in_range = (time_range.end - time_range.start).days
        if len(daily_reports) < days_in_range * 0.8:  # 80%以上の日で報告
            quality_issues.append(QualityIssue(
                type="MISSING_DAILY_REPORTS",
                severity="HIGH",
                expected=days_in_range,
                actual=len(daily_reports)
            ))
        
        # Docker権限問題の優先度確認
        docker_issues = await self._get_docker_related_tasks(time_range)
        for issue in docker_issues:
            if issue.priority < 1:  # 最優先でない
                quality_issues.append(QualityIssue(
                    type="DOCKER_PRIORITY_VIOLATION",
                    severity="CRITICAL",
                    task_id=issue.id,
                    current_priority=issue.priority
                ))
    
    elif sage_type == SageType.INCIDENT:
        # インシデント賢者の検証
        incidents = await self._get_incidents(time_range)
        
        for incident in incidents:
            # 5分以内検知の確認
            detection_time = incident.detected_at - incident.occurred_at
            if detection_time.total_seconds() > 300:
                quality_issues.append(QualityIssue(
                    type="LATE_DETECTION",
                    severity="CRITICAL",
                    incident_id=incident.id,
                    detection_minutes=detection_time.total_seconds() / 60
                ))
            
            # 根本原因分析の確認
            rca = await self._get_root_cause_analysis(incident.id)
            if not rca:
                quality_issues.append(QualityIssue(
                    type="MISSING_RCA",
                    severity="HIGH",
                    incident_id=incident.id
                ))
            elif rca.depth < 3:  # 表面的な分析
                quality_issues.append(QualityIssue(
                    type="SHALLOW_RCA",
                    severity="MEDIUM",
                    incident_id=incident.id,
                    analysis_depth=rca.depth
                ))
    
    elif sage_type == SageType.RAG:
        # RAG賢者の検証
        researches = [a for a in activities if a.type == "technology_research"]
        
        # 月次調査の確認
        months_in_range = (time_range.end.month - time_range.start.month) + 1
        if len(researches) < months_in_range:
            quality_issues.append(QualityIssue(
                type="MISSING_MONTHLY_RESEARCH",
                severity="HIGH",
                expected=months_in_range,
                actual=len(researches)
            ))
        
        # 技術負債検出の確認
        tech_debt_reports = [a for a in activities if a.type == "tech_debt_detection"]
        if not tech_debt_reports:
            quality_issues.append(QualityIssue(
                type="NO_TECH_DEBT_DETECTION",
                severity="MEDIUM"
            ))
    
    return SageActivityReport(
        sage_type=sage_type,
        period=time_range,
        total_activities=len(activities),
        quality_issues=quality_issues,
        activity_score=self._calculate_activity_score(activities, quality_issues)
    )
```

#### 2.3 賢者間連携検証
```python
async def verify_sage_coordination(self, time_range: TimeRange) -> SageCoordinationReport:
    """賢者間の連携と情報共有を検証"""
    
    coordination_issues = []
    
    # 賢者間メッセージの分析
    sage_messages = await self._get_inter_sage_messages(time_range)
    
    # 情報サイロ化の検出
    message_matrix = self._build_communication_matrix(sage_messages)
    isolated_sages = self._detect_isolated_sages(message_matrix)
    
    if isolated_sages:
        coordination_issues.append(CoordinationIssue(
            type="SAGE_ISOLATION",
            severity="HIGH",
            isolated_sages=isolated_sages,
            evidence="他の賢者との通信が極端に少ない"
        ))
    
    # 重要情報の共有確認
    critical_info = await self._identify_critical_information(time_range)
    for info in critical_info:
        shared_with = await self._get_information_recipients(info.id)
        required_sages = self._determine_required_recipients(info)
        
        missing_recipients = set(required_sages) - set(shared_with)
        if missing_recipients:
            coordination_issues.append(CoordinationIssue(
                type="INFORMATION_NOT_SHARED",
                severity="CRITICAL",
                info_id=info.id,
                missing_recipients=list(missing_recipients)
            ))
    
    # 相互学習の確認
    learning_events = await self._get_sage_learning_events(time_range)
    if len(learning_events) < time_range.days / 7:  # 週1回以上の相互学習
        coordination_issues.append(CoordinationIssue(
            type="INSUFFICIENT_MUTUAL_LEARNING",
            severity="MEDIUM",
            expected_frequency="weekly",
            actual_events=len(learning_events)
        ))
    
    return SageCoordinationReport(
        communication_matrix=message_matrix,
        coordination_issues=coordination_issues,
        collaboration_score=self._calculate_collaboration_score(sage_messages)
    )
```

#### 2.4 賢者助言の実施状況検証
```python
async def verify_sage_advice_implementation(self, time_range: TimeRange) -> AdviceImplementationReport:
    """賢者の助言が実際に実施されているかを検証"""
    
    # すべての賢者助言を取得
    all_advice = await self._get_sage_advice(time_range)
    
    implementation_stats = []
    ignored_advice = []
    
    for advice in all_advice:
        # 助言に対する実装を追跡
        implementation = await self._track_advice_implementation(advice)
        
        if implementation.status == "IGNORED":
            ignored_advice.append(IgnoredAdvice(
                advice_id=advice.id,
                sage=advice.sage_type,
                severity=advice.severity,
                given_at=advice.timestamp,
                reason=implementation.ignore_reason
            ))
        
        elif implementation.status == "PARTIAL":
            implementation_stats.append({
                "advice_id": advice.id,
                "implementation_rate": implementation.completion_rate,
                "missing_parts": implementation.missing_parts
            })
        
        elif implementation.status == "MODIFIED":
            # 助言が勝手に変更されている
            if not implementation.modification_approved:
                ignored_advice.append(IgnoredAdvice(
                    advice_id=advice.id,
                    sage=advice.sage_type,
                    severity="HIGH",
                    reason="Unauthorized modification of sage advice"
                ))
    
    # 実装率の計算
    implementation_rate = len([a for a in all_advice if a.implemented]) / len(all_advice)
    
    return AdviceImplementationReport(
        total_advice=len(all_advice),
        implemented=len([a for a in all_advice if a.implemented]),
        ignored=ignored_advice,
        implementation_rate=implementation_rate,
        by_sage=self._group_by_sage(implementation_stats)
    )
```

### 3. 監査実行フロー
```python
async def execute_audit(self, audit_request: SageAuditRequest) -> SageAuditResult:
    """4賢者システム監査を実行"""
    
    # Phase 1: 相談義務履行の検証
    consultation_report = await self.verify_sage_consultation_compliance(
        audit_request.time_range
    )
    
    # Phase 2: 各賢者の活動品質検証
    activity_reports = {}
    for sage_type in SageType:
        activity_reports[sage_type] = await self.verify_sage_activity_quality(
            sage_type, audit_request.time_range
        )
    
    # Phase 3: 賢者間連携の検証
    coordination_report = await self.verify_sage_coordination(
        audit_request.time_range
    )
    
    # Phase 4: 助言実施状況の検証
    implementation_report = await self.verify_sage_advice_implementation(
        audit_request.time_range
    )
    
    # Phase 5: 総合評価
    sage_health_score = self._calculate_sage_system_health(
        consultation_report,
        activity_reports,
        coordination_report,
        implementation_report
    )
    
    # Phase 6: 違反への対応
    all_violations = self._collect_all_violations(
        consultation_report,
        activity_reports,
        coordination_report,
        implementation_report
    )
    
    critical_violations = [v for v in all_violations if v.severity == "CRITICAL"]
    if critical_violations:
        # 緊急対応
        await self._summon_emergency_sage_council(critical_violations)
        await self._enforce_sage_discipline(critical_violations)
        
        # 自動修正
        for violation in critical_violations:
            if violation.type == "MISSING_CONSULTATION":
                await self._force_sage_consultation(violation)
            elif violation.type == "IGNORED_ADVICE":
                await self._escalate_to_grand_elder(violation)
    
    # Phase 7: 改善提案
    improvements = self._generate_sage_improvements(all_violations)
    
    return SageAuditResult(
        audit_id=str(uuid.uuid4()),
        period=audit_request.time_range,
        sage_health_score=sage_health_score,
        consultation_compliance=consultation_report,
        activity_quality=activity_reports,
        coordination=coordination_report,
        advice_implementation=implementation_report,
        critical_issues=critical_violations,
        improvements=improvements,
        actions_taken=self._get_enforcement_actions()
    )
```

### 4. 賢者違反パターン定義
```python
class SageViolationPatterns:
    """賢者システム違反パターン"""
    
    # 相談違反
    CONSULTATION_VIOLATIONS = {
        "skip_incident_sage": "コード作成前のインシデント賢者相談なし",
        "ignore_sage_advice": "賢者の助言を無視して実装",
        "fake_consultation": "形式的な相談（内容なし）",
        "missing_4sage_council": "失敗時の4賢者会議未開催",
    }
    
    # 活動違反
    ACTIVITY_VIOLATIONS = {
        "knowledge_stale": "ナレッジ賢者の週次更新なし",
        "task_priority_wrong": "タスク賢者のDocker最優先違反",
        "incident_slow": "インシデント賢者の5分検知失敗",
        "rag_no_research": "RAG賢者の月次調査なし",
    }
    
    # 連携違反
    COORDINATION_VIOLATIONS = {
        "sage_silo": "賢者間の情報共有不足",
        "no_mutual_learning": "相互学習の欠如",
        "conflicting_advice": "矛盾する助言の未調整",
        "emergency_no_summon": "緊急時の評議会未召集",
    }
```

### 5. 賢者システム強化アクション
```python
async def strengthen_sage_system(self, violations: List[SageViolation]) -> None:
    """賢者システムを強化する自動アクション"""
    
    # 相談プロセスの自動化強化
    await self._enhance_consultation_automation(
        pre_code_check=True,
        failure_detection=True,
        auto_summon_council=True
    )
    
    # 賢者活動の自動リマインダー
    await self._setup_sage_reminders({
        SageType.KNOWLEDGE: "weekly",
        SageType.TASK: "daily",
        SageType.INCIDENT: "realtime",
        SageType.RAG: "monthly"
    })
    
    # 賢者間通信チャネルの強化
    await self._create_sage_communication_channel(
        auto_share_critical_info=True,
        weekly_sync_meeting=True
    )
    
    # 助言追跡システムの実装
    await self._implement_advice_tracking(
        auto_follow_up=True,
        escalation_threshold=48  # 48時間未実施で上申
    )
```

## 実装優先度: CRITICAL

## 関連ファイル
- `libs/knowledge_sage.py` - ナレッジ賢者
- `libs/task_sage.py` - タスク賢者
- `libs/incident_manager.py` - インシデント賢者
- `libs/rag_manager.py` - RAG賢者
- `data/sages_integration.db` - 賢者活動DB

## テスト要件
- 各賢者の義務履行検証テスト
- 賢者間連携の検出テスト
- 助言実施追跡テスト
- 誤検出防止テスト

## 成功基準
- 相談義務違反の100%検出
- 賢者活動品質の定量評価
- 助言無視の95%以上検出
- 賢者システム稼働率30%向上