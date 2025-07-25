# 🌊 Ancient Elder Issue #2: Elder Flow遵守監査魔法 (Flow Compliance Audit Magic)

## 概要
Elder Flowの5段階フロー遵守状況を監査し、プロセススキップや不正な省略を検出する古代魔法システムの実装

## 背景
Elder Flowは品質保証の要だが、実際には部分的にスキップされたり、形骸化している可能性がある。全段階の確実な実行を監査する仕組みが必要。

## 実装要件

### 1. 基底クラス継承
```python
from souls.base_soul import BaseSoul, ElderType
from libs.elder_flow.flow_tracker import FlowExecutionLog

class AncientElderFlowComplianceAuditor(BaseSoul):
    """Elder Flow遵守を監査するエンシェントエルダー"""
    
    def __init__(self):
        super().__init__(
            name="AncientElder_FlowCompliance",
            elder_type=ElderType.ANCIENT_ELDER,
            specialty="flow_compliance_audit"
        )
        self.flow_stages = [
            "four_sages_council",
            "elder_servants_execution", 
            "quality_gate",
            "council_report",
            "git_automation"
        ]
```

### 2. Flow遵守検証ロジック

#### 2.1 Flow実行トレース検証
```python
async def verify_flow_execution(self, task_id: str) -> FlowComplianceReport:
    """Elder Flow実行の完全性を検証"""
    
    # Elder Flowログ取得
    flow_logs = await self._get_flow_execution_logs(task_id)
    
    # 各段階の実行確認
    stage_reports = {}
    for stage in self.flow_stages:
        stage_reports[stage] = await self._verify_stage_execution(
            task_id, stage, flow_logs
        )
    
    # 実行順序の検証
    sequence_valid = await self._verify_execution_sequence(flow_logs)
    
    # タイムスタンプ整合性
    timing_valid = await self._verify_stage_timing(flow_logs)
    
    return FlowComplianceReport(
        task_id=task_id,
        stages=stage_reports,
        sequence_valid=sequence_valid,
        timing_valid=timing_valid,
        overall_compliance=self._calculate_compliance_score(stage_reports)
    )
```

#### 2.2 4賢者会議検証
```python
async def verify_sages_council(self, task_id: str) -> SagesCouncilReport:
    """4賢者会議の実施を検証"""
    
    # 各賢者の参加ログ
    sage_logs = {
        "knowledge_sage": await self._get_sage_log("knowledge", task_id),
        "task_sage": await self._get_sage_log("task", task_id),
        "incident_sage": await self._get_sage_log("incident", task_id),
        "rag_sage": await self._get_sage_log("rag", task_id)
    }
    
    # 相談内容の実質性検証
    consultation_quality = {}
    for sage, log in sage_logs.items():
        if log:
            # 形式的な相談か実質的な相談かを判定
            consultation_quality[sage] = await self._assess_consultation_quality(log)
        else:
            consultation_quality[sage] = {"present": False, "quality": 0}
    
    # 会議の決定事項と実装の整合性
    council_decisions = await self._extract_council_decisions(sage_logs)
    implementation = await self._get_actual_implementation(task_id)
    
    decision_compliance = self._verify_decision_implementation(
        council_decisions, implementation
    )
    
    return SagesCouncilReport(
        participation=sage_logs,
        quality=consultation_quality,
        decisions=council_decisions,
        compliance=decision_compliance
    )
```

#### 2.3 品質ゲート検証
```python
async def verify_quality_gate(self, task_id: str) -> QualityGateReport:
    """品質ゲートの適切な実施を検証"""
    
    gate_log = await self._get_quality_gate_log(task_id)
    
    if not gate_log:
        return QualityGateReport(
            passed=False,
            skipped=True,
            reason="Quality gate was completely skipped"
        )
    
    # チェック項目の実施確認
    checks_performed = {
        "test_coverage": gate_log.get("coverage_check", False),
        "lint_check": gate_log.get("lint_check", False),
        "security_scan": gate_log.get("security_scan", False),
        "performance_test": gate_log.get("performance_test", False),
        "documentation": gate_log.get("doc_check", False)
    }
    
    # 強行突破の検出
    force_flags = await self._detect_force_flags(task_id)
    if force_flags:
        return QualityGateReport(
            passed=False,
            forced=True,
            violations=["Quality gate was forcefully bypassed"],
            evidence=force_flags
        )
    
    # 品質基準の適切性
    standards_met = all(checks_performed.values())
    
    return QualityGateReport(
        passed=standards_met,
        checks=checks_performed,
        score=self._calculate_quality_score(checks_performed)
    )
```

#### 2.4 自動化スキップ検出
```python
async def detect_automation_bypass(self, task_id: str) -> List[BypassViolation]:
    """Elder Flow自動化のバイパスを検出"""
    
    violations = []
    
    # バイパスキーワードの悪用
    task_description = await self._get_task_description(task_id)
    if self._contains_bypass_keywords(task_description):
        # バイパスキーワードが含まれているのにElder Flowが必要なタスク
        if self._requires_elder_flow(task_description):
            violations.append(BypassViolation(
                type="BYPASS_KEYWORD_ABUSE",
                severity="HIGH",
                evidence=f"Bypass keyword used for flow-required task: {task_description}"
            ))
    
    # 手動実行の痕跡
    manual_markers = await self._detect_manual_execution(task_id)
    if manual_markers:
        violations.append(BypassViolation(
            type="MANUAL_OVERRIDE",
            severity="MEDIUM",
            evidence=manual_markers
        ))
    
    # 部分的実行
    partial_execution = await self._detect_partial_execution(task_id)
    if partial_execution:
        violations.append(BypassViolation(
            type="INCOMPLETE_FLOW",
            severity="HIGH",
            evidence=f"Only {partial_execution['completed_stages']}/{len(self.flow_stages)} stages completed"
        ))
    
    return violations
```

### 3. 監査実行フロー
```python
async def execute_audit(self, audit_request: FlowAuditRequest) -> FlowAuditResult:
    """Elder Flow遵守監査を実行"""
    
    # Phase 1: Flow実行ログ収集
    flow_logs = await self._collect_all_flow_logs(audit_request.time_range)
    
    # Phase 2: 各タスクの遵守状況確認
    task_reports = {}
    for task_id in audit_request.task_ids:
        # Flow全体の検証
        flow_report = await self.verify_flow_execution(task_id)
        
        # 4賢者会議の検証
        sages_report = await self.verify_sages_council(task_id)
        
        # 品質ゲートの検証
        gate_report = await self.verify_quality_gate(task_id)
        
        # バイパス検出
        bypass_violations = await self.detect_automation_bypass(task_id)
        
        task_reports[task_id] = {
            "flow": flow_report,
            "sages": sages_report,
            "quality": gate_report,
            "violations": bypass_violations
        }
    
    # Phase 3: 統計分析
    statistics = self._analyze_compliance_statistics(task_reports)
    
    # Phase 4: 違反パターン分析
    violation_patterns = self._identify_violation_patterns(task_reports)
    
    # Phase 5: 改善提案生成
    recommendations = self._generate_process_improvements(violation_patterns)
    
    # Phase 6: 重大違反への対応
    critical_violations = self._filter_critical_violations(task_reports)
    if critical_violations:
        await self._escalate_to_grand_elder(critical_violations)
        await self._block_future_bypasses(critical_violations)
    
    return FlowAuditResult(
        period=audit_request.time_range,
        total_tasks=len(task_reports),
        compliance_rate=statistics["overall_compliance"],
        stage_compliance=statistics["by_stage"],
        violations=violation_patterns,
        recommendations=recommendations,
        actions_taken=self._get_enforcement_actions()
    )
```

### 4. 違反検出パターン
```python
class FlowCompliancePatterns:
    """Flow遵守違反パターン"""
    
    # スキップパターン
    SKIP_PATTERNS = {
        "forced_push": ["--force", "-f", "force push"],
        "skip_tests": ["--no-verify", "skip-checks", "SKIP_TESTS=true"],
        "bypass_quality": ["--bypass-quality", "FORCE_DEPLOY=true"],
        "mock_sages": ["MOCK_SAGES=true", "mock_council=True"],
    }
    
    # 形骸化パターン
    HOLLOW_PATTERNS = {
        "instant_approval": "council duration < 1 second",
        "empty_consultation": "sage response is empty or template",
        "fake_tests": "all tests pass in < 0.1 seconds",
        "no_real_changes": "quality gate with 0 files checked",
    }
    
    # タイミング異常
    TIMING_ANOMALIES = {
        "retroactive_test": "test created after implementation",
        "future_timestamp": "log timestamp > current time",
        "impossible_sequence": "stage B completed before stage A started",
        "weekend_automation": "automated flow on non-working hours",
    }
```

### 5. 自動是正アクション
```python
async def enforce_compliance(self, violations: List[FlowViolation]) -> None:
    """Flow違反への自動是正"""
    
    for violation in violations:
        if violation.severity == "CRITICAL":
            # 即座にデプロイメントをブロック
            await self._block_deployment(violation.task_id)
            
            # Elder Flowの再実行を強制
            await self._force_rerun_elder_flow(violation.task_id)
            
            # 違反者への教育タスク生成
            await self._create_education_task(violation.violator)
            
        elif violation.severity == "HIGH":
            # 警告とログ記録
            await self._issue_warning(violation)
            
            # 次回から自動でより厳格なチェック
            await self._tighten_future_checks(violation.violator)
```

## 実装優先度: CRITICAL

## 関連ファイル
- `libs/elder_flow/flow_tracker.py` - Flow実行ログ
- `libs/elder_flow/orchestrator.py` - Flow制御
- `data/elder_flow_logs.db` - 実行履歴DB

## テスト要件
- 全5段階の個別検証テスト
- スキップ・バイパス検出テスト
- タイミング異常検出テスト
- 統計分析の正確性テスト

## 成功基準
- Flow違反の99%以上を検出
- 全段階の実行証跡を確実に記録
- 違反の自動是正成功率90%以上