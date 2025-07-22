# 🛡️ Ancient Elder Issue #6: サーバント査察魔法 (Servant Inspector Magic)

## 概要
エルダーサーバント（32体制）の実装品質、役割遵守、協調動作を監査し、手抜き実装やモック化を検出する古代魔法システムの実装

## 背景
エルダーサーバントは実装の実働部隊だが、実際にはスタブ実装、過度な抽象化、役割の形骸化が発生している可能性がある。サーバントの真の働きぶりを査察する魔法が必要。

## 実装要件

### 1. 基底クラス継承
```python
from souls.base_soul import BaseSoul, ElderType
from libs.elder_servants import ServantRole, ServantActivity

class AncientElderServantInspector(BaseSoul):
    """エルダーサーバントを査察するエンシェントエルダー"""
    
    def __init__(self):
        super().__init__(
            name="AncientElder_ServantInspector",
            elder_type=ElderType.ANCIENT_ELDER,
            specialty="servant_inspection"
        )
        self.servant_roles = {
            "code_architect": ["設計", "アーキテクチャ", "パターン適用"],
            "test_guardian": ["TDD実践", "テスト品質", "カバレッジ"],
            "quality_inspector": ["コード品質", "レビュー", "標準遵守"],
            "doc_scribe": ["ドキュメント", "コメント", "仕様記述"],
            "perf_optimizer": ["パフォーマンス", "最適化", "ボトルネック"],
            "security_sentinel": ["セキュリティ", "脆弱性", "認証認可"],
            "refactor_specialist": ["リファクタリング", "技術負債", "改善"],
            "integration_master": ["統合", "API", "連携"]
        }
```

### 2. サーバント実装品質検証

#### 2.1 実装実体性検証
```python
async def verify_servant_implementation_quality(self, servant_id: str, time_range: TimeRange) -> ServantQualityReport:
    """サーバントの実装品質を検証"""
    
    # サーバントの成果物取得
    artifacts = await self._get_servant_artifacts(servant_id, time_range)
    
    quality_issues = []
    
    for artifact in artifacts:
        if artifact.type == "code":
            # スタブ実装の検出
            stub_analysis = await self._detect_stub_implementation(artifact.content)
            if stub_analysis["stub_ratio"] > 0.2:
                quality_issues.append(ServantViolation(
                    type="EXCESSIVE_STUBS",
                    severity="HIGH",
                    servant_id=servant_id,
                    artifact_id=artifact.id,
                    evidence=f"Stub ratio: {stub_analysis['stub_ratio']:.2%}",
                    stub_locations=stub_analysis["locations"]
                ))
            
            # TODO/FIXME密度の確認
            todo_density = self._calculate_todo_density(artifact.content)
            if todo_density > 0.1:  # 10%以上
                quality_issues.append(ServantViolation(
                    type="HIGH_TODO_DENSITY",
                    severity="MEDIUM",
                    servant_id=servant_id,
                    artifact_id=artifact.id,
                    evidence=f"TODO density: {todo_density:.2%}"
                ))
            
            # 実装の深さ分析
            implementation_depth = await self._analyze_implementation_depth(artifact)
            if implementation_depth["average_complexity"] < 2:
                quality_issues.append(ServantViolation(
                    type="SHALLOW_IMPLEMENTATION",
                    severity="HIGH",
                    servant_id=servant_id,
                    artifact_id=artifact.id,
                    evidence="過度に単純な実装（実質的な処理なし）"
                ))
        
        elif artifact.type == "test":
            # テストの実質性確認
            test_quality = await self._analyze_test_quality(artifact.content)
            if test_quality["assertion_ratio"] < 0.5:
                quality_issues.append(ServantViolation(
                    type="WEAK_TEST_ASSERTIONS",
                    severity="HIGH",
                    servant_id=servant_id,
                    artifact_id=artifact.id,
                    evidence="アサーションが不十分"
                ))
            
            # モックの過剰使用
            if test_quality["mock_dependency_ratio"] > 0.6:
                quality_issues.append(ServantViolation(
                    type="OVER_MOCKING",
                    severity="MEDIUM",
                    servant_id=servant_id,
                    artifact_id=artifact.id,
                    evidence=f"Mock dependency: {test_quality['mock_dependency_ratio']:.2%}"
                ))
    
    # 成果物の量的評価
    expected_output = self._calculate_expected_output(servant_id, time_range)
    actual_output = len(artifacts)
    
    if actual_output < expected_output * 0.7:
        quality_issues.append(ServantViolation(
            type="LOW_PRODUCTIVITY",
            severity="MEDIUM",
            servant_id=servant_id,
            expected=expected_output,
            actual=actual_output
        ))
    
    return ServantQualityReport(
        servant_id=servant_id,
        period=time_range,
        artifacts_count=len(artifacts),
        quality_issues=quality_issues,
        quality_score=self._calculate_servant_quality_score(artifacts, quality_issues)
    )
```

#### 2.2 役割遵守検証
```python
async def verify_servant_role_compliance(self, servant_id: str, expected_role: str) -> RoleComplianceReport:
    """サーバントが割り当てられた役割を遵守しているか検証"""
    
    # サーバントの活動ログ取得
    activities = await self._get_servant_activities(servant_id)
    
    role_violations = []
    role_adherence_stats = {
        "in_role": 0,
        "out_of_role": 0,
        "borderline": 0
    }
    
    expected_activities = self.servant_roles[expected_role]
    
    for activity in activities:
        # 活動が役割に適合しているか判定
        role_match = self._assess_role_match(activity, expected_activities)
        
        if role_match < 0.3:
            role_violations.append(RoleViolation(
                type="OUT_OF_ROLE_ACTIVITY",
                severity="HIGH",
                servant_id=servant_id,
                activity_id=activity.id,
                expected_role=expected_role,
                actual_activity=activity.description
            ))
            role_adherence_stats["out_of_role"] += 1
        elif role_match < 0.7:
            role_adherence_stats["borderline"] += 1
        else:
            role_adherence_stats["in_role"] += 1
        
        # 役割の重複検出
        overlapping_roles = self._detect_role_overlap(activity)
        if len(overlapping_roles) > 1:
            role_violations.append(RoleViolation(
                type="ROLE_CONFUSION",
                severity="MEDIUM",
                servant_id=servant_id,
                activity_id=activity.id,
                overlapping_roles=overlapping_roles
            ))
    
    # 専門性の深さ評価
    expertise_depth = await self._evaluate_expertise_depth(servant_id, expected_role)
    if expertise_depth["score"] < 60:
        role_violations.append(RoleViolation(
            type="SHALLOW_EXPERTISE",
            severity="HIGH",
            servant_id=servant_id,
            expected_role=expected_role,
            expertise_score=expertise_depth["score"],
            missing_skills=expertise_depth["gaps"]
        ))
    
    return RoleComplianceReport(
        servant_id=servant_id,
        expected_role=expected_role,
        role_adherence=role_adherence_stats,
        violations=role_violations,
        compliance_score=self._calculate_role_compliance_score(role_adherence_stats)
    )
```

#### 2.3 サーバント間協調検証
```python
async def verify_servant_coordination(self, task_id: str) -> ServantCoordinationReport:
    """サーバント間の協調動作を検証"""
    
    # タスクに関わったサーバント特定
    involved_servants = await self._get_task_servants(task_id)
    
    coordination_issues = []
    
    # 役割分担の適切性
    role_distribution = self._analyze_role_distribution(involved_servants)
    if self._has_missing_critical_roles(role_distribution):
        coordination_issues.append(CoordinationIssue(
            type="MISSING_CRITICAL_ROLES",
            severity="HIGH",
            task_id=task_id,
            missing_roles=self._get_missing_roles(role_distribution)
        ))
    
    # 作業順序の適切性
    work_sequence = await self._analyze_work_sequence(task_id)
    sequence_violations = self._detect_sequence_violations(work_sequence)
    
    for violation in sequence_violations:
        coordination_issues.append(CoordinationIssue(
            type="IMPROPER_SEQUENCE",
            severity="HIGH",
            task_id=task_id,
            violation=violation,
            suggestion=self._suggest_proper_sequence(violation)
        ))
    
    # 成果物の整合性
    artifacts = await self._get_task_artifacts(task_id)
    consistency_issues = self._check_artifact_consistency(artifacts)
    
    for issue in consistency_issues:
        coordination_issues.append(CoordinationIssue(
            type="ARTIFACT_INCONSISTENCY",
            severity="MEDIUM",
            task_id=task_id,
            issue=issue
        ))
    
    # コミュニケーション分析
    communications = await self._get_servant_communications(task_id)
    if len(communications) < len(involved_servants) * 2:
        coordination_issues.append(CoordinationIssue(
            type="INSUFFICIENT_COMMUNICATION",
            severity="MEDIUM",
            task_id=task_id,
            expected_min=len(involved_servants) * 2,
            actual=len(communications)
        ))
    
    return ServantCoordinationReport(
        task_id=task_id,
        involved_servants=involved_servants,
        coordination_issues=coordination_issues,
        coordination_score=self._calculate_coordination_score(coordination_issues)
    )
```

#### 2.4 サーバント生産性分析
```python
async def analyze_servant_productivity(self, servant_id: str, time_range: TimeRange) -> ProductivityReport:
    """サーバントの生産性と効率を分析"""
    
    # 成果物の量的分析
    artifacts = await self._get_servant_artifacts(servant_id, time_range)
    
    productivity_metrics = {
        "lines_of_code": 0,
        "test_coverage": 0,
        "documentation_pages": 0,
        "refactoring_impact": 0,
        "bug_fixes": 0,
        "feature_implementations": 0
    }
    
    quality_adjusted_metrics = {}
    
    for artifact in artifacts:
        # 量的指標の集計
        if artifact.type == "code":
            loc = self._count_lines_of_code(artifact.content)
            productivity_metrics["lines_of_code"] += loc
            
            # 品質調整（低品質なコードは割り引く）
            quality_factor = await self._assess_code_quality(artifact.content)
            quality_adjusted_metrics["effective_loc"] = loc * quality_factor
        
        elif artifact.type == "test":
            coverage = await self._calculate_test_coverage(artifact)
            productivity_metrics["test_coverage"] += coverage
        
        elif artifact.type == "documentation":
            pages = self._count_documentation_pages(artifact.content)
            productivity_metrics["documentation_pages"] += pages
    
    # 時間効率の分析
    time_efficiency = await self._analyze_time_efficiency(servant_id, time_range)
    
    # 他のサーバントとの比較
    peer_comparison = await self._compare_with_peers(servant_id, productivity_metrics)
    
    # 改善トレンドの分析
    historical_data = await self._get_historical_productivity(servant_id)
    improvement_trend = self._calculate_improvement_trend(historical_data)
    
    violations = []
    
    # 生産性が著しく低い場合
    if peer_comparison["percentile"] < 20:
        violations.append(ProductivityViolation(
            type="LOW_PRODUCTIVITY",
            severity="HIGH",
            servant_id=servant_id,
            percentile=peer_comparison["percentile"],
            suggestion="生産性向上のためのトレーニングが必要"
        ))
    
    # 品質を犠牲にした量産
    if quality_adjusted_metrics.get("effective_loc", 0) < productivity_metrics["lines_of_code"] * 0.5:
        violations.append(ProductivityViolation(
            type="QUALITY_SACRIFICE",
            severity="HIGH",
            servant_id=servant_id,
            raw_output=productivity_metrics["lines_of_code"],
            quality_adjusted=quality_adjusted_metrics.get("effective_loc", 0)
        ))
    
    return ProductivityReport(
        servant_id=servant_id,
        period=time_range,
        metrics=productivity_metrics,
        quality_adjusted_metrics=quality_adjusted_metrics,
        time_efficiency=time_efficiency,
        peer_comparison=peer_comparison,
        improvement_trend=improvement_trend,
        violations=violations
    )
```

### 3. 監査実行フロー
```python
async def execute_audit(self, audit_request: ServantAuditRequest) -> ServantAuditResult:
    """エルダーサーバント査察を実行"""
    
    # Phase 1: 個別サーバントの品質検証
    quality_reports = {}
    for servant_id in audit_request.servant_ids:
        quality_reports[servant_id] = await self.verify_servant_implementation_quality(
            servant_id, audit_request.time_range
        )
    
    # Phase 2: 役割遵守の検証
    role_reports = {}
    for servant_id, expected_role in audit_request.servant_roles.items():
        role_reports[servant_id] = await self.verify_servant_role_compliance(
            servant_id, expected_role
        )
    
    # Phase 3: タスクごとの協調検証
    coordination_reports = {}
    for task_id in audit_request.task_ids:
        coordination_reports[task_id] = await self.verify_servant_coordination(task_id)
    
    # Phase 4: 生産性分析
    productivity_reports = {}
    for servant_id in audit_request.servant_ids:
        productivity_reports[servant_id] = await self.analyze_servant_productivity(
            servant_id, audit_request.time_range
        )
    
    # Phase 5: 総合評価
    servant_system_health = self._calculate_servant_system_health(
        quality_reports,
        role_reports,
        coordination_reports,
        productivity_reports
    )
    
    # Phase 6: 違反への対応
    all_violations = self._collect_all_violations(
        quality_reports,
        role_reports,
        coordination_reports,
        productivity_reports
    )
    
    critical_violations = [v for v in all_violations if v.severity == "CRITICAL"]
    if critical_violations:
        # 即座の是正措置
        await self._halt_servant_operations(critical_violations)
        await self._initiate_servant_retraining(critical_violations)
        
        # 自動修正
        for violation in critical_violations:
            if violation.type == "EXCESSIVE_STUBS":
                await self._replace_stubs_with_implementation(violation)
            elif violation.type == "ROLE_CONFUSION":
                await self._reassign_servant_roles(violation)
    
    # Phase 7: 改善計画
    improvement_plan = self._generate_servant_improvement_plan(
        all_violations,
        servant_system_health
    )
    
    return ServantAuditResult(
        audit_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        servant_system_health=servant_system_health,
        quality_reports=quality_reports,
        role_compliance=role_reports,
        coordination=coordination_reports,
        productivity=productivity_reports,
        critical_violations=critical_violations,
        improvement_plan=improvement_plan,
        enforcement_actions=self._get_enforcement_actions()
    )
```

### 4. サーバント違反パターン定義
```python
class ServantViolationPatterns:
    """サーバント違反パターン"""
    
    # 実装品質違反
    QUALITY_VIOLATIONS = {
        "stub_overuse": "過度なスタブ・モック使用",
        "shallow_impl": "表面的な実装（実質なし）",
        "todo_accumulation": "TODO/FIXMEの蓄積",
        "copy_paste": "コピペコードの多用",
    }
    
    # 役割違反
    ROLE_VIOLATIONS = {
        "role_drift": "割り当て役割からの逸脱",
        "role_overlap": "他サーバントの領域侵犯",
        "shallow_expertise": "専門性の欠如",
        "generalist_tendency": "何でも屋化",
    }
    
    # 協調違反
    COORDINATION_VIOLATIONS = {
        "silo_work": "孤立した作業",
        "sequence_violation": "作業順序の無視",
        "inconsistent_output": "成果物の不整合",
        "communication_failure": "連携不足",
    }
    
    # 生産性違反
    PRODUCTIVITY_VIOLATIONS = {
        "low_output": "著しく低い生産性",
        "quality_sacrifice": "品質を犠牲にした量産",
        "time_waste": "非効率な時間使用",
        "no_improvement": "改善の停滞",
    }
```

### 5. サーバント強化アクション
```python
async def strengthen_servant_system(self, violations: List[ServantViolation]) -> None:
    """サーバントシステムを強化する自動アクション"""
    
    # 品質基準の自動適用
    await self._enforce_quality_standards(
        min_test_coverage=80,
        max_todo_ratio=0.05,
        min_assertion_ratio=0.7
    )
    
    # 役割定義の明確化と強制
    await self._clarify_servant_roles(
        role_descriptions=self.servant_roles,
        overlap_prevention=True,
        expertise_requirements=True
    )
    
    # 協調プロトコルの実装
    await self._implement_coordination_protocol(
        mandatory_sync_points=True,
        artifact_validation=True,
        communication_templates=True
    )
    
    # 生産性モニタリング
    await self._setup_productivity_monitoring(
        real_time_tracking=True,
        peer_comparison=True,
        improvement_targets=True
    )
    
    # 継続的改善プログラム
    await self._initiate_improvement_program(
        weekly_reviews=True,
        skill_development=True,
        best_practice_sharing=True
    )
```

## 実装優先度: HIGH

## 関連ファイル
- `libs/elder_servants/` - サーバント実装
- `souls/servant_souls/` - サーバント魂定義
- `data/servant_activities.db` - 活動記録

## テスト要件
- 各種違反パターンの検出テスト
- 役割判定の正確性テスト
- 協調動作の評価テスト
- 生産性メトリクスの妥当性テスト

## 成功基準
- スタブ実装の95%以上検出
- 役割逸脱の90%以上検出
- 協調問題の85%以上検出
- サーバント生産性20%向上