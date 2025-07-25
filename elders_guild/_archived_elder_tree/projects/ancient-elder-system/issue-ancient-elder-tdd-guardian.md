# 🔴🟢🔵 Ancient Elder Issue #3: TDD守護魔法 (TDD Guardian Magic)

## 概要
TDD（テスト駆動開発）のRed→Green→Refactorサイクルが正しく実践されているかを監査し、テスト後付けや形骸化したテストを検出する古代魔法システムの実装

## 背景
TDDはElders Guildの開発原則だが、実際にはテストが後付けされたり、意味のないテストでカバレッジを稼ぐケースが存在する。真のTDD実践を守護する魔法が必要。

## 実装要件

### 1. 基底クラス継承
```python
from souls.base_soul import BaseSoul, ElderType
from libs.git_analysis import GitHistoryAnalyzer

class AncientElderTDDGuardian(BaseSoul):
    """TDD実践を守護するエンシェントエルダー"""
    
    def __init__(self):
        super().__init__(
            name="AncientElder_TDDGuardian",
            elder_type=ElderType.ANCIENT_ELDER,
            specialty="tdd_guardian"
        )
        self.tdd_cycle = ["RED", "GREEN", "REFACTOR"]
        self.git_analyzer = GitHistoryAnalyzer()
```

### 2. TDD違反検出ロジック

#### 2.1 Red→Green→Refactorサイクル検証
```python
async def verify_tdd_cycle(self, feature_branch: str) -> TDDCycleReport:
    """TDDサイクルの適切な実行を検証"""
    
    # コミット履歴取得
    commits = await self.git_analyzer.get_branch_commits(feature_branch)
    
    # サイクル検出
    cycles = []
    current_cycle = {"red": None, "green": None, "refactor": []}
    
    for commit in commits:
        files_changed = await self.git_analyzer.get_commit_files(commit.sha)
        
        # RED: テストファイルの追加/変更（失敗するテスト）
        if self._is_test_commit(files_changed) and not self._has_implementation(files_changed):
            if current_cycle["red"] is None:
                current_cycle["red"] = commit
            else:
                # 新しいサイクル開始
                cycles.append(current_cycle)
                current_cycle = {"red": commit, "green": None, "refactor": []}
        
        # GREEN: 実装追加（テストを通す最小実装）
        elif self._has_implementation(files_changed) and current_cycle["red"]:
            current_cycle["green"] = commit
        
        # REFACTOR: リファクタリング
        elif current_cycle["green"] and self._is_refactoring(commit, files_changed):
            current_cycle["refactor"].append(commit)
    
    # サイクル分析
    violations = []
    for cycle in cycles:
        if not cycle["red"]:
            violations.append(TDDViolation(
                type="NO_TEST_FIRST",
                severity="CRITICAL",
                evidence="Implementation without prior failing test"
            ))
        
        if cycle["red"] and not cycle["green"]:
            violations.append(TDDViolation(
                type="INCOMPLETE_CYCLE",
                severity="HIGH",
                evidence="Test written but no implementation followed"
            ))
        
        # テストとコードのタイムスタンプ検証
        if cycle["red"] and cycle["green"]:
            time_diff = cycle["green"].timestamp - cycle["red"].timestamp
            if time_diff < 0:
                violations.append(TDDViolation(
                    type="RETROACTIVE_TEST",
                    severity="CRITICAL",
                    evidence="Test committed after implementation"
                ))
    
    return TDDCycleReport(
        cycles=cycles,
        violations=violations,
        compliance_score=self._calculate_tdd_score(cycles, violations)
    )
```

#### 2.2 テスト品質検証
```python
async def verify_test_quality(self, test_file: Path) -> TestQualityReport:
    """テストの実質性を検証"""
    
    content = await self._read_file(test_file)
    quality_issues = []
    
    # アサーションの実質性チェック
    assertions = self._extract_assertions(content)
    for assertion in assertions:
        # 意味のないアサーション検出
        if self._is_meaningless_assertion(assertion):
            quality_issues.append(QualityIssue(
                type="MEANINGLESS_ASSERTION",
                severity="HIGH",
                code=assertion,
                suggestion="Add meaningful assertions that verify behavior"
            ))
    
    # テストケースの網羅性
    test_cases = self._extract_test_cases(content)
    coverage_analysis = {
        "happy_path": self._has_happy_path_tests(test_cases),
        "edge_cases": self._has_edge_case_tests(test_cases),
        "error_cases": self._has_error_tests(test_cases),
        "boundary_cases": self._has_boundary_tests(test_cases)
    }
    
    # モックの過剰使用検出
    mock_usage = self._analyze_mock_usage(content)
    if mock_usage["mock_ratio"] > 0.7:
        quality_issues.append(QualityIssue(
            type="EXCESSIVE_MOCKING",
            severity="HIGH",
            evidence=f"Mock ratio: {mock_usage['mock_ratio']:.2%}",
            suggestion="Reduce mocks, use real implementations where possible"
        ))
    
    # テスト実行時間の異常検出
    execution_time = await self._get_test_execution_time(test_file)
    if execution_time and execution_time < 0.001:
        quality_issues.append(QualityIssue(
            type="SUSPICIOUSLY_FAST",
            severity="MEDIUM",
            evidence=f"Test completes in {execution_time}s",
            suggestion="Ensure test actually executes code paths"
        ))
    
    return TestQualityReport(
        file=test_file,
        assertions_count=len(assertions),
        meaningful_assertions=len([a for a in assertions if not self._is_meaningless_assertion(a)]),
        coverage=coverage_analysis,
        mock_usage=mock_usage,
        issues=quality_issues,
        quality_score=self._calculate_quality_score(quality_issues)
    )
```

#### 2.3 カバレッジ操作検出
```python
async def detect_coverage_manipulation(self, project_path: Path) -> CoverageManipulationReport:
    """カバレッジ不正操作を検出"""
    
    manipulations = []
    
    # カバレッジのみを目的とした無意味なテスト
    test_files = await self._find_test_files(project_path)
    for test_file in test_files:
        content = await self._read_file(test_file)
        
        # パターン1: 実行だけして検証しないテスト
        if self._has_execution_without_assertion(content):
            manipulations.append(CoverageManipulation(
                type="EXECUTION_ONLY_TEST",
                file=test_file,
                evidence="Test executes code but has no assertions"
            ))
        
        # パターン2: すべてのブランチを無理やり通すテスト
        if self._has_forced_branch_coverage(content):
            manipulations.append(CoverageManipulation(
                type="FORCED_BRANCH_COVERAGE",
                file=test_file,
                evidence="Artificial branch execution detected"
            ))
    
    # .coveragercの不正な除外設定
    coveragerc = project_path / ".coveragerc"
    if coveragerc.exists():
        exclusions = await self._parse_coverage_exclusions(coveragerc)
        if self._has_suspicious_exclusions(exclusions):
            manipulations.append(CoverageManipulation(
                type="SUSPICIOUS_EXCLUSIONS",
                file=coveragerc,
                evidence=f"Excluded: {exclusions}"
            ))
    
    return CoverageManipulationReport(
        manipulations=manipulations,
        genuine_coverage=await self._calculate_genuine_coverage(project_path),
        reported_coverage=await self._get_reported_coverage(project_path)
    )
```

### 3. 監査実行フロー
```python
async def execute_audit(self, audit_request: TDDAuditRequest) -> TDDAuditResult:
    """TDD実践監査を実行"""
    
    # Phase 1: Git履歴からTDDサイクル検証
    cycle_report = await self.verify_tdd_cycle(audit_request.branch)
    
    # Phase 2: テストファイルの品質検証
    test_quality_reports = []
    for test_file in audit_request.test_files:
        quality_report = await self.verify_test_quality(test_file)
        test_quality_reports.append(quality_report)
    
    # Phase 3: カバレッジ操作検出
    coverage_report = await self.detect_coverage_manipulation(audit_request.project_path)
    
    # Phase 4: TDD実践度スコア計算
    tdd_score = self._calculate_overall_tdd_score(
        cycle_report,
        test_quality_reports,
        coverage_report
    )
    
    # Phase 5: 違反への対応
    if tdd_score < 70:
        violations = self._collect_all_violations(
            cycle_report, test_quality_reports, coverage_report
        )
        
        # 自動修正可能な違反は修正
        for violation in violations:
            if violation.auto_fixable:
                await self._auto_fix_violation(violation)
        
        # 重大違反は開発をブロック
        critical_violations = [v for v in violations if v.severity == "CRITICAL"]
        if critical_violations:
            await self._block_merge(audit_request.branch, critical_violations)
            await self._require_tdd_training(audit_request.developer)
    
    # Phase 6: レポート生成と通知
    report = TDDAuditResult(
        branch=audit_request.branch,
        tdd_score=tdd_score,
        cycle_compliance=cycle_report,
        test_quality=test_quality_reports,
        coverage_integrity=coverage_report,
        recommendations=self._generate_tdd_improvements(tdd_score),
        actions_taken=self._get_enforcement_actions()
    )
    
    await self._notify_stakeholders(report)
    
    return report
```

### 4. TDD違反パターン定義
```python
class TDDViolationPatterns:
    """TDD違反パターン定義"""
    
    # テスト後付けパターン
    RETROACTIVE_PATTERNS = {
        "test_after_impl": "test file created after implementation",
        "bulk_test_commit": "multiple test files in single commit",
        "coverage_sprint": "sudden test additions near deadline",
    }
    
    # 形骸化テストパターン
    HOLLOW_TEST_PATTERNS = {
        "assert_true": "assert True",
        "assert_none": "assert foo is not None",
        "no_assertion": "test method with no assert statements",
        "print_only": "test that only prints",
    }
    
    # カバレッジ操作パターン
    COVERAGE_GAMING = {
        "import_only": "importing module just for coverage",
        "unreachable_exclusion": "# pragma: no cover on reachable code",
        "dummy_execution": "executing code without verification",
    }
    
    # 意味のないアサーション
    MEANINGLESS_ASSERTIONS = [
        r"assert\s+True",
        r"assert\s+.*\s+is\s+not\s+None",
        r"assert\s+.*\s*==\s*.*\s*#\s*同じ値",
        r"assert\s+1\s*==\s*1",
    ]
```

### 5. TDD実践支援アクション
```python
async def support_tdd_practice(self, developer: str, violations: List[TDDViolation]) -> None:
    """TDD実践を支援する自動アクション"""
    
    # 違反タイプ別の対応
    for violation in violations:
        if violation.type == "NO_TEST_FIRST":
            # テストスケルトンの自動生成
            await self._generate_test_skeleton(violation.context)
            
            # TDDリマインダーの設定
            await self._set_tdd_reminder(developer)
            
        elif violation.type == "MEANINGLESS_ASSERTION":
            # 意味のあるアサーションの提案
            suggestions = await self._suggest_meaningful_assertions(violation.context)
            await self._create_improvement_pr(violation.file, suggestions)
            
        elif violation.type == "INCOMPLETE_CYCLE":
            # 次のステップのガイダンス提供
            await self._provide_next_step_guidance(developer, violation.context)
    
    # TDDメトリクスダッシュボード更新
    await self._update_tdd_metrics(developer, violations)
    
    # 継続的な改善のためのフィードバック
    await self._schedule_tdd_review(developer)
```

## 実装優先度: CRITICAL

## 関連ファイル
- `libs/git_analysis.py` - Git履歴解析
- `tests/` - テストファイル群
- `.coveragerc` - カバレッジ設定

## テスト要件
- TDDサイクル検出の正確性テスト
- テスト品質評価の妥当性テスト
- カバレッジ操作検出の網羅性テスト
- 誤検出防止テスト

## 成功基準
- TDD違反の95%以上を検出
- テスト後付けの100%検出
- カバレッジ操作の90%以上検出
- 開発者のTDD実践率20%向上