# 🏛️ Ancient Elder Issue #1: 誠実性監査魔法 (Integrity Audit Magic)

## 概要
エルダーやサーバントの虚偽報告、モック/スタブ悪用、実装詐称を検出する古代魔法システムの実装

## 背景
現在のシステムでは、エルダーたちが「実装完了」「テスト成功」と報告しても、実際にはモックやスタブで偽装されている可能性がある。真の品質保証のため、誠実性を監査する古代魔法が必要。

## 実装要件

### 1. 基底クラス継承
```python
from souls.base_soul import BaseSoul, ElderType

class AncientElderIntegrityAuditor(BaseSoul):
    """誠実性監査を行うエンシェントエルダー"""
    
    def __init__(self):
        super().__init__(
            name="AncientElder_Integrity",
            elder_type=ElderType.ANCIENT_ELDER,
            specialty="integrity_audit"
        )
```

### 2. 監査対象と検出ロジック

#### 2.1 虚偽報告検出
```python
async def detect_false_claims(self, target_path: Path) -> List[ViolationReport]:
    """虚偽報告を検出"""
    violations = []
    
    # パターン1: TODOやFIXMEが残っているのに「完了」
    if await self._check_todo_patterns(target_path):
        violations.append(ViolationReport(
            type="FALSE_COMPLETION",
            severity="CRITICAL",
            evidence="TODO/FIXME found in 'completed' code"
        ))
    
    # パターン2: NotImplementedErrorやpassが残存
    if await self._check_stub_implementations(target_path):
        violations.append(ViolationReport(
            type="STUB_IMPLEMENTATION",
            severity="CRITICAL",
            evidence="Stub/Mock implementation detected"
        ))
    
    # パターン3: テストが意味のないアサーション
    if await self._check_meaningless_tests(target_path):
        violations.append(ViolationReport(
            type="FAKE_TEST",
            severity="HIGH",
            evidence="Test with no real assertions"
        ))
```

#### 2.2 モック/スタブ検出
```python
async def detect_mock_abuse(self, code_content: str) -> bool:
    """モック/スタブの不正使用を検出"""
    
    # 検出パターン
    mock_patterns = [
        r'@mock\.patch\([\'"]libs\.(knowledge_sage|incident_manager|task_sage|rag_manager)',
        r'MagicMock\(\)',
        r'return\s+\{\s*[\'"]success[\'"]\s*:\s*True\s*\}',  # 安易な成功返却
        r'except.*:\s*pass',  # エラー握りつぶし
    ]
    
    # 4賢者APIのモック化は特に重大
    sage_mock_patterns = [
        r'mock.*knowledge_sage',
        r'mock.*incident_manager',
        r'stub.*task_sage',
        r'fake.*rag_manager'
    ]
```

#### 2.3 実装整合性検証
```python
async def verify_implementation_consistency(self, git_repo: Path) -> Dict[str, Any]:
    """Git履歴とコードの整合性を検証"""
    
    # TDD違反検出: テストファイルが後から作成
    test_timing = await self._analyze_test_creation_timing(git_repo)
    
    # コミットメッセージと実装の乖離
    commit_claims = await self._extract_commit_claims(git_repo)
    actual_impl = await self._analyze_actual_implementation(git_repo)
    
    # Elder Flow実行ログとの照合
    flow_logs = await self._get_elder_flow_logs()
    
    return {
        "tdd_violations": test_timing.violations,
        "false_claims": self._compare_claims_vs_reality(commit_claims, actual_impl),
        "elder_flow_skips": flow_logs.skipped_flows
    }
```

### 3. 監査実行フロー
```python
async def execute_audit(self, audit_request: AuditRequest) -> AuditResult:
    """誠実性監査を実行"""
    
    # Phase 1: 静的解析
    static_violations = await self.detect_false_claims(audit_request.target_path)
    
    # Phase 2: モック検出
    mock_violations = await self.detect_mock_abuse(audit_request.code_content)
    
    # Phase 3: Git履歴分析
    consistency_report = await self.verify_implementation_consistency(
        audit_request.git_repo
    )
    
    # Phase 4: 4賢者ログ照合
    sage_logs = await self._verify_sage_consultations(audit_request.claimed_consultations)
    
    # Phase 5: 総合判定
    integrity_score = self._calculate_integrity_score(
        static_violations,
        mock_violations,
        consistency_report,
        sage_logs
    )
    
    # Phase 6: 違反時の自動対応
    if integrity_score < 60:
        await self._trigger_emergency_council()
        await self._block_deployment()
        await self._notify_grand_elder()
    
    return AuditResult(
        score=integrity_score,
        violations=all_violations,
        recommendations=self._generate_corrections(),
        verdict=self._determine_verdict(integrity_score)
    )
```

### 4. 検出パターン定義
```python
class IntegrityPatterns:
    """誠実性違反パターン定義"""
    
    # 虚偽実装パターン
    FALSE_IMPL = {
        "todo_markers": ["TODO", "FIXME", "HACK", "XXX", "仮実装", "後で"],
        "stub_functions": ["pass", "...", "NotImplementedError", "raise NotImplementedError"],
        "fake_returns": ["return True", "return {'success': True}", "return 'OK'"],
    }
    
    # モック悪用パターン  
    MOCK_ABUSE = {
        "sage_mocks": ["mock_knowledge_sage", "mock_incident_manager"],
        "db_stubs": ["fake_db", "mock_database", "InMemoryDB"],
        "api_fakes": ["FakeAPI", "MockHTTPClient", "StubRequests"],
    }
    
    # プロセス違反パターン
    PROCESS_VIOLATIONS = {
        "no_test_first": "implementation commit before test commit",
        "no_elder_flow": "missing elder flow execution log",
        "skip_quality_gate": "force push without approval",
    }
```

### 5. 自動修正アクション
```python
async def auto_correct_violations(self, violations: List[Violation]) -> None:
    """違反の自動修正"""
    
    for violation in violations:
        if violation.type == "STUB_IMPLEMENTATION":
            # スタブを実装に置き換えるPR作成
            await self._create_implementation_pr(violation)
            
        elif violation.type == "MISSING_TESTS":
            # テスト作成タスクを自動生成
            await self._create_test_task(violation)
            
        elif violation.type == "MOCK_ABUSE":
            # モックを実際のAPIコールに修正
            await self._replace_mock_with_real(violation)
```

## 実装優先度: CRITICAL

## 関連ファイル
- `souls/base_soul.py` - 基底クラス
- `libs/elder_flow/` - Elder Flow統合
- `libs/integrations/github/` - Git履歴分析

## テスト要件
- 各検出パターンの単体テスト
- 誤検出防止のための境界値テスト
- 実際の違反コードでの統合テスト

## 成功基準
- 虚偽報告の95%以上を検出
- モック/スタブ悪用の100%検出
- 誤検出率5%以下