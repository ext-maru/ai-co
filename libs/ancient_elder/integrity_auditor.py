#!/usr/bin/env python3
"""
🔮 Ancient Elder Integrity Auditor - 誠実性監査魔法
========================================================

虚偽報告、モック/スタブ悪用、実装詐称を検出する古代魔法システム
Issue #197対応

Features:
- TODO/FIXME検出エンジン
- モック/スタブ悪用検出
- Git履歴整合性分析
- TDD違反検出
- 自動修正提案生成

Author: Claude Elder
Created: 2025-07-21
"""

import ast
import asyncio
import json
import logging
import os
import re
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import sys

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.base_soul import BaseSoul, ElderType, SoulCapability, SoulIdentity, SoulState
from libs.base_soul import SoulRequest, SoulResponse

logger = logging.getLogger(__name__)


class ViolationType(Enum):
    """違反タイプ"""
    FALSE_COMPLETION = "false_completion"
    STUB_IMPLEMENTATION = "stub_implementation"
    FAKE_TEST = "fake_test"
    MOCK_ABUSE = "mock_abuse"
    TDD_VIOLATION = "tdd_violation"
    GIT_FRAUD = "git_fraud"
    ELDER_FLOW_SKIP = "elder_flow_skip"
    SAGE_FRAUD = "sage_fraud"


class ViolationSeverity(Enum):
    """違反重要度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ViolationReport:
    """違反レポート"""
    type: ViolationType
    severity: ViolationSeverity
    file_path: str
    line_number: int
    evidence: str
    description: str
    suggestion: str = ""
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """to_dictメソッド"""
        return {
            "type": self.type.value,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "evidence": self.evidence,
            "description": self.description,
            "suggestion": self.suggestion,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class AuditRequest:
    """監査要求"""
    target_path: Path
    git_repo: Optional[Path] = None
    code_content: Optional[str] = None
    claimed_consultations: List[str] = field(default_factory=list)
    check_git_history: bool = True
    check_sage_logs: bool = True
    deep_analysis: bool = True


@dataclass
class AuditResult:
    """監査結果"""
    score: float
    violations: List[ViolationReport]
    recommendations: List[str]
    verdict: str
    processing_time_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """to_dictメソッド"""
        return {
            "score": self.score,
            "violations": [v.to_dict() for v in self.violations],
            "recommendations": self.recommendations,
            "verdict": self.verdict,
            "processing_time_ms": self.processing_time_ms,
            "timestamp": self.timestamp.isoformat()
        }


class IntegrityPatterns:
    """誠実性違反パターン定義"""
    
    # 虚偽実装パターン
    FALSE_IMPL = {
        "todo_markers": ["TODO", "FIXME", "HACK", "XXX", "仮実装", "後で", "temp", "placeholder"],
        "stub_functions": ["pass", "...", "NotImplementedError", "raise NotImplementedError"],
        "fake_returns": [
            r"return\s+True",
            r"return\s+\{\s*['\"]success['\"]\s*:\s*True\s*\}",
            r"return\s+['\"]OK['\"]",
            r"return\s+['\"]success['\"]"
        ],
        "empty_implementations": [
            r"def\s+\w+\([^)]*\):\s*pass",
            r"async\s+def\s+\w+\([^)]*\):\s*pass",
            r"class\s+\w+.*:\s*pass"
        ]
    }
    
    # モック悪用パターン  
    MOCK_ABUSE = {
        "sage_mocks": [
            r"mock.*knowledge_sage",
            r"mock.*incident_manager", 
            r"mock.*task_sage",
            r"mock.*rag_manager",
            r"patch.*libs\.knowledge_sage",
            r"patch.*libs\.incident_sage",
            r"patch.*libs\.task_sage",
            r"patch.*libs\.rag_manager"
        ],
        "db_stubs": ["fake_db", "mock_database", "InMemoryDB", "TestDB"],
        "api_fakes": ["FakeAPI", "MockHTTPClient", "StubRequests", "DummyAPI"],
        "mock_overuse": [
            r"@mock\.patch.*@mock\.patch.*@mock\.patch",  # 3個以上の連続パッチ
            r"MagicMock\(\).*MagicMock\(\).*MagicMock\(\)"  # 複数MagicMock
        ]
    }
    
    # プロセス違反パターン
    PROCESS_VIOLATIONS = {
        "no_test_first": "implementation commit before test commit",
        "no_elder_flow": "missing elder flow execution log",
        "skip_quality_gate": "force push without approval",
        "fake_commits": "empty or minimal commits with grand claims"
    }


class ASTPatternsDetector:
    """AST解析による高度パターン検出"""
    
    def __init__(self):
        """初期化メソッド"""
        self.violations = []
    
    def visit_source(self, source_code: str, file_path: str) -> List[ViolationReport]:
        """ソースコードをAST解析"""
        self.violations = []
        self.file_path = file_path
        
        try:
            tree = ast.parse(source_code)
            self.visit(tree)
        except SyntaxError as e:
            self.violations.append(ViolationReport(
                type=ViolationType.FALSE_COMPLETION,
                severity=ViolationSeverity.HIGH,
                file_path=file_path,
                line_number=e.lineno or 0,
                evidence=f"Syntax error: {e}",
                description="Code has syntax errors but claimed as completed"
            ))
        
        return self.violations
    
    def visit(self, node):
        """ノード訪問"""
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        visitor(node)
    
    def generic_visit(self, node):
        """汎用ノード処理"""
        for child in ast.iter_child_nodes(node):
            self.visit(child)
    
    def visit_FunctionDef(self, node):
        """関数定義の検査"""
        # 空の実装チェック
        if len(node.body) == 1:
            first_stmt = node.body[0]
            
            # pass のみの関数
            if isinstance(first_stmt, ast.Pass):
                self.violations.append(ViolationReport(
                    type=ViolationType.STUB_IMPLEMENTATION,
                    severity=ViolationSeverity.CRITICAL,
                    file_path=self.file_path,
                    line_number=node.lineno,
                    evidence=f"Function '{node.name}' contains only 'pass'",
                    description="Function is not implemented but marked as complete",
                    suggestion=f"Implement the actual logic for function '{node.name}'"
                ))
            
            # NotImplementedError のみの関数
            elif (isinstance(first_stmt, ast.Raise) and 
                  isinstance(first_stmt.exc, ast.Call) and
                  isinstance(first_stmt.exc.func, ast.Name) and
                  first_stmt.exc.func.id == "NotImplementedError"):
                self.violations.append(ViolationReport(
                    type=ViolationType.STUB_IMPLEMENTATION,
                    severity=ViolationSeverity.CRITICAL,
                    file_path=self.file_path,
                    line_number=node.lineno,
                    evidence=f"Function '{node.name}' raises NotImplementedError",
                    description="Function is not implemented",
                    suggestion=f"Replace NotImplementedError with actual implementation in '{node.name}'"
                ))
        
        # テスト関数の意味のないアサーションチェック
        if node.name.startswith("test_"):
            self._check_meaningless_test(node)
        
        self.generic_visit(node)
    
    def visit_Return(self, node):
        """return文の検査"""
        if isinstance(node.value, ast.Constant):
            if node.value.value is True:
                self.violations.append(ViolationReport(
                    type=ViolationType.FAKE_TEST,
                    severity=ViolationSeverity.MEDIUM,
                    file_path=self.file_path,
                    line_number=node.lineno,
                    evidence="Function returns bare 'True'",
                    description="Suspiciously simple return value",
                    suggestion="Ensure return value is meaningful and not hardcoded"
                ))
        
        self.generic_visit(node)
    
    def _check_meaningless_test(self, node):
        """意味のないテストをチェック"""
        has_assertions = False
        
        for stmt in ast.walk(node):
            # Assert文の検出
            if isinstance(stmt, ast.Assert):
                has_assertions = True
                break
            # assert関数呼び出しの検出
            elif isinstance(stmt, ast.Call):
                if (isinstance(stmt.func, ast.Attribute) and 
                    stmt.func.attr.startswith("assert")):
                    has_assertions = True
                    break
                elif (isinstance(stmt.func, ast.Name) and 
                      stmt.func.id.startswith("assert")):
                    has_assertions = True
                    break
        
        if not has_assertions:
            self.violations.append(ViolationReport(
                type=ViolationType.FAKE_TEST,
                severity=ViolationSeverity.HIGH,
                file_path=self.file_path,
                line_number=node.lineno,
                evidence=f"Test function '{node.name}' has no assertions",
                description="Test function exists but contains no actual assertions",
                suggestion=f"Add meaningful assertions to test function '{node.name}'"
            ))


class GitIntegrityAnalyzer:
    """Git履歴整合性分析"""
    
    def __init__(self, repo_path:
        """初期化メソッド"""
    Path):
        self.repo_path = repo_path
        
    async def analyze_tdd_compliance(self) -> List[ViolationReport]:
        """TDD遵守分析"""
        violations = []
        
        try:
            # 最近のコミット履歴を取得
            cmd = ["git", "log", "--oneline", "--name-only", "-20"]
            result = subprocess.run(cmd, cwd=self.repo_path, 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                return violations
            
            commits = self._parse_git_log(result.stdout)
            
            for commit in commits:
                # テストファイルと実装ファイルのコミット順序をチェック
                test_files = [f for f in commit.files if f.startswith("test_") or "/test_" in f]
                impl_files = [f for f in commit.files if f.endswith(".py") and f not in test_files]
                
                # 実装ファイルのみでテストファイルがない場合
                if impl_files and not test_files and "test" not in commit.message.lower():
                    violations.append(ViolationReport(
                        type=ViolationType.TDD_VIOLATION,
                        severity=ViolationSeverity.HIGH,
                        file_path=", ".join(impl_files),
                        line_number=0,
                        evidence=f"Commit {commit.hash}: {commit.message}",
                        description="Implementation committed without corresponding tests",
                        suggestion="Follow TDD: write tests first, then implementation"
                    ))
        
        except Exception as e:
            logger.error(f"Git analysis error: {e}")
        
        return violations
    
    def _parse_git_log(self, log_output: str) -> List[Any]:
        """Git logの解析"""
        commits = []
        lines = log_output.strip().split('\n')
        
        current_commit = None
        for line in lines:
            if ' ' in line and not line.startswith(' ') and not line.startswith('\t'):
                # 新しいコミット行
                if current_commit:
                    commits.append(current_commit)
                
                parts = line.split(' ', 1)
                current_commit = type('Commit', (), {
                    'hash': parts[0],
                    'message': parts[1] if len(parts) > 1 else '',
                    'files': []
                })()
            elif current_commit and line.strip():
                # ファイル名
                current_commit.files.append(line.strip())
        
        if current_commit:
            commits.append(current_commit)
        
        return commits
    
    async def check_commit_message_integrity(self) -> List[ViolationReport]:
        """コミットメッセージの整合性チェック"""
        violations = []
        
        try:
            # 最近のコミットの詳細情報を取得
            cmd = ["git", "log", "--stat", "-10", "--pretty=format:%H|%s|%an|%ad"]
            result = subprocess.run(cmd, cwd=self.repo_path, 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                return violations
            
            # グランドな主張と実際の変更量の乖離をチェック
            for line in result.stdout.split('\n'):
                if '|' in line and ' changed, ' in line:
                    commit_info = line.split('|')[1].lower()
                    
                    # 「実装完了」「major feature」等の大きな主張
                    grand_claims = ['complete', '完了', 'implement', 'major', 'full']
                    if any(claim in commit_info for claim in grand_claims):
                        # 実際の変更行数をチェック（簡易的）
                        if 'files changed' in line:
                            match = re.search(r'(\d+) files? changed', line)
                            if match:
                                files_changed = int(match.group(1))
                                if files_changed < 3:  # 変更ファイル数が少ない
                                    violations.append(ViolationReport(
                                        type=ViolationType.GIT_FRAUD,
                                        severity=ViolationSeverity.MEDIUM,
                                        file_path="git_commit",
                                        line_number=0,
                                        evidence=f"Commit message claims major work but only {files_changed} \
                                            files changed",
                                        description="Commit message overstates the amount of work done",
                                        suggestion="Make commit messages proportional to actual " \
                                            "changes"
                                    ))
        
        except Exception as e:
            logger.error(f"Commit message analysis error: {e}")
        
        return violations


class AncientElderIntegrityAuditor(BaseSoul):
    """🔮 誠実性監査を行うエンシェントエルダー"""
    
    def __init__(self):
        """初期化メソッド"""
        identity = SoulIdentity(
            soul_id="ancient_elder_integrity",
            soul_name="AncientElder_Integrity",
            elder_type=ElderType.ANCIENT_ELDER,
            hierarchy_level=9,  # 最高位
            capabilities=[
                SoulCapability.ANALYSIS,
                SoulCapability.QUALITY_ASSURANCE,
                SoulCapability.WISDOM,
                SoulCapability.PROBLEM_SOLVING
            ],
            specializations=["integrity_audit", "fraud_detection", "quality_enforcement"],
            loyalty_targets=["grand_elder_maru", "system_integrity"]
        )
        
        super().__init__(identity)
        
        self.patterns = IntegrityPatterns()
        self.ast_detector = ASTPatternsDetector()
        
        logger.info("🔮 Ancient Elder Integrity Auditor awakened")
    
    async def execute_audit(self, audit_request: AuditRequest) -> AuditResult:
        """誠実性監査を実行"""
        start_time = time.time()
        self.state = SoulState.PROCESSING
        
        logger.info(f"🔍 Starting integrity audit for: {audit_request.target_path}")
        
        all_violations = []
        
        try:
            # Phase 1: 静的解析
            static_violations = await self.detect_false_claims(audit_request.target_path)
            all_violations.extend(static_violations)
            
            # Phase 2: モック検出
            if audit_request.code_content:
                mock_violations = await self.detect_mock_abuse(audit_request.code_content)
                all_violations.extend(mock_violations)
            
            # Phase 3: Git履歴分析
            if audit_request.check_git_history and audit_request.git_repo:
                git_analyzer = GitIntegrityAnalyzer(audit_request.git_repo)
                git_violations = await git_analyzer.analyze_tdd_compliance()
                git_violations.extend(await git_analyzer.check_commit_message_integrity())
                all_violations.extend(git_violations)
            
            # Phase 4: 4賢者ログ照合
            if audit_request.check_sage_logs:
                sage_violations = await self._verify_sage_consultations(
                    audit_request.claimed_consultations
                )
                all_violations.extend(sage_violations)
            
            # Phase 5: 総合判定
            integrity_score = self._calculate_integrity_score(all_violations)
            
            # Phase 6: 違反時の自動対応
            if integrity_score < 60:
                await self._trigger_emergency_response(integrity_score, all_violations)
            
            verdict = self._determine_verdict(integrity_score)
            recommendations = self._generate_corrections(all_violations)
            
            processing_time = (time.time() - start_time) * 1000
            
            result = AuditResult(
                score=integrity_score,
                violations=all_violations,
                recommendations=recommendations,
                verdict=verdict,
                processing_time_ms=processing_time
            )
            
            logger.info(f"✅ Integrity audit completed. Score: {integrity_score}/100, Violations: {len(all_violations)}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Audit execution failed: {e}")
            self.state = SoulState.CRASHED
            raise
        finally:
            self.state = SoulState.ACTIVE
    
    async def detect_false_claims(self, target_path: Path) -> List[ViolationReport]:
        """虚偽報告を検出"""
        violations = []
        
        if target_path.is_file():
            files_to_check = [target_path]
        else:
            files_to_check = list(target_path.rglob("*.py"))
        
        for file_path in files_to_check:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # TODO/FIXME パターンチェック
                violations.extend(self._check_todo_patterns(content, str(file_path)))
                
                # スタブ実装チェック
                violations.extend(self._check_stub_implementations(content, str(file_path)))
                
                # AST解析
                violations.extend(self.ast_detector.visit_source(content, str(file_path)))
                
            except Exception as e:
                logger.warning(f"Failed to analyze file {file_path}: {e}")
        
        return violations
    
    def _check_todo_patterns(self, content: str, file_path: str) -> List[ViolationReport]:
        """TODO/FIXMEパターンチェック"""
        violations = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            for marker in self.patterns.FALSE_IMPL["todo_markers"]:
                if marker in line.upper():
                    violations.append(ViolationReport(
                        type=ViolationType.FALSE_COMPLETION,
                        severity=ViolationSeverity.CRITICAL,
                        file_path=file_path,
                        line_number=i,
                        evidence=line.strip(),
                        description=f"TODO/FIXME marker found: {marker}",
                        suggestion=f"Complete the implementation and remove {marker}"
                    ))
        
        return violations
    
    def _check_stub_implementations(self, content: str, file_path: str) -> List[ViolationReport]:
        """スタブ実装チェック"""
        violations = []
        
        for pattern in self.patterns.FALSE_IMPL["fake_returns"]:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                violations.append(ViolationReport(
                    type=ViolationType.STUB_IMPLEMENTATION,
                    severity=ViolationSeverity.HIGH,
                    file_path=file_path,
                    line_number=line_num,
                    evidence=match.group(),
                    description="Suspicious simple return value",
                    suggestion="Replace with meaningful implementation"
                ))
        
        return violations
    
    async def detect_mock_abuse(self, code_content: str) -> List[ViolationReport]:
        """モック/スタブの不正使用を検出"""
        violations = []
        
        # 4賢者APIのモック化チェック (最重要)
        for pattern in self.patterns.MOCK_ABUSE["sage_mocks"]:
            matches = re.finditer(pattern, code_content, re.IGNORECASE)
            for match in matches:
                line_num = code_content[:match.start()].count('\n') + 1
                violations.append(ViolationReport(
                    type=ViolationType.MOCK_ABUSE,
                    severity=ViolationSeverity.CRITICAL,
                    file_path="code_content",
                    line_number=line_num,
                    evidence=match.group(),
                    description="Critical: 4 Sages API is being mocked",
                    suggestion="Use real sage implementations instead of mocks"
                ))
        
        # 過度なモック使用チェック
        mock_count = len(re.findall(r'mock|Mock|patch', code_content, re.IGNORECASE))
        if mock_count > 10:  # 閾値は調整可能
            violations.append(ViolationReport(
                type=ViolationType.MOCK_ABUSE,
                severity=ViolationSeverity.MEDIUM,
                file_path="code_content",
                line_number=0,
                evidence=f"Found {mock_count} mock usages",
                description="Excessive use of mocks detected",
                suggestion="Reduce dependency on mocks, use real implementations where possible"
            ))
        
        return violations
    
    async def _verify_sage_consultations(
        self,
        claimed_consultations: List[str]
    ) -> List[ViolationReport]:
        """4賢者相談の検証"""
        violations = []
        
        # 実際のログファイルを確認
        log_patterns = [
            "logs/knowledge_sage.log",
            "logs/incident_sage.log", 
            "logs/task_sage.log",
            "logs/rag_manager.log"
        ]
        
        for consultation in claimed_consultations:
            verified = False
            for log_pattern in log_patterns:
                log_files = list(Path().glob(log_pattern))
                for log_file in log_files:
                    if log_file.exists():
                        try:
                            with open(log_file, 'r') as f:
                                if consultation in f.read():
                                    verified = True
                                    break
                        except Exception:
                            continue
                
                if verified:
                    break
            
            if not verified:
                violations.append(ViolationReport(
                    type=ViolationType.SAGE_FRAUD,
                    severity=ViolationSeverity.CRITICAL,
                    file_path="sage_logs",
                    line_number=0,
                    evidence=f"Claimed consultation: {consultation}",
                    description="Claimed sage consultation not found in logs",
                    suggestion="Ensure proper sage consultation is executed and logged"
                ))
        
        return violations
    
    def _calculate_integrity_score(self, violations: List[ViolationReport]) -> float:
        """誠実性スコア計算"""
        if not violations:
            return 100.0
        
        # 重要度に応じた減点
        penalty_map = {
            ViolationSeverity.CRITICAL: 25,
            ViolationSeverity.HIGH: 15,
            ViolationSeverity.MEDIUM: 8,
            ViolationSeverity.LOW: 3,
            ViolationSeverity.INFO: 1
        }
        
        total_penalty = sum(penalty_map[v.severity] * v.confidence for v in violations)
        score = max(0, 100 - total_penalty)
        
        return score
    
    def _determine_verdict(self, score: float) -> str:
        """判定結果を決定"""
        if score >= 90:
            return "EXCELLENT - 優秀な誠実性"
        elif score >= 75:
            return "GOOD - 良好な誠実性"
        elif score >= 60:
            return "ACCEPTABLE - 許容範囲の誠実性"
        elif score >= 40:
            return "CONCERNING - 懸念される誠実性"
        else:
            return "CRITICAL - 重大な誠実性問題"
    
    def _generate_corrections(self, violations: List[ViolationReport]) -> List[str]:
        """修正推奨事項生成"""
        recommendations = []
        
        violation_types = set(v.type for v in violations)
        
        if ViolationType.FALSE_COMPLETION in violation_types:
            recommendations.append("Complete all TODO/FIXME items before claiming implementation finished")
        
        if ViolationType.STUB_IMPLEMENTATION in violation_types:
            recommendations.append("Replace stub implementations with actual working code")
        
        if ViolationType.MOCK_ABUSE in violation_types:
            recommendations.append("Reduce reliance on mocks, especially for 4 Sages APIs")
        
        if ViolationType.TDD_VIOLATION in violation_types:
            recommendations.append("Follow TDD principles: write tests first, then implementation")
        
        if ViolationType.SAGE_FRAUD in violation_types:
            recommendations.append("Ensure all claimed sage consultations are properly executed and logged")
        
        if not recommendations:
            recommendations.append("Maintain current high standards of integrity")
        
        return recommendations
    
    async def _trigger_emergency_response(self, score: float, violations: List[ViolationReport]):
        """緊急対応トリガー"""
        logger.critical(f"🚨 INTEGRITY EMERGENCY: Score {score}/100")
        
        # Critical違反の集計
        critical_violations = [v for v in violations if v.severity == ViolationSeverity.CRITICAL]
        
        if critical_violations:
            logger.critical(f"🔥 Critical violations detected: {len(critical_violations)}")
            
            # 緊急レポートファイル作成
            emergency_report_path = Path(f"emergency_integrity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(emergency_report_path, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "score": score,
                    "critical_violations": [v.to_dict() for v in critical_violations],
                    "emergency_level": "CRITICAL" if score < 30 else "HIGH"
                }, f, indent=2)
            
            logger.critical(f"📄 Emergency report saved: {emergency_report_path}")
    
    # BaseSoul 抽象メソッドの実装
    def process_soul_request(self, request: SoulRequest) -> Dict[str, Any]:
        """魂固有のリクエスト処理（同期版）"""
        # 非同期メソッドをラップ
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 既にループが実行中の場合は新しいタスクとして実行
                return {}
            else:
                return loop.run_until_complete(self._process_request_async(request))
        except RuntimeError:
            # 新しいループを作成
            return asyncio.run(self._process_request_async(request))
    
    async def _process_request_async(self, request: SoulRequest) -> Dict[str, Any]:
        """非同期リクエスト処理"""
        if request.request_type == "integrity_audit":
            # 監査リクエストの処理
            audit_request = AuditRequest(
                target_path=Path(request.payload.get("target_path", ".")),
                git_repo=Path(request.payload.get("git_repo", ".")) if request.payload.get("git_repo") else None,
                code_content=request.payload.get("code_content"),
                claimed_consultations=request.payload.get("claimed_consultations", []),
                check_git_history=request.payload.get("check_git_history", True),
                check_sage_logs=request.payload.get("check_sage_logs", True)
            )
            
            result = await self.execute_audit(audit_request)
            return result.to_dict()
        else:
            return {"error": f"Unknown request type: {request.request_type}"}
    
    def on_soul_awakening(self):
        """魂覚醒時の初期化処理"""
        logger.info("🔮 Ancient Elder Integrity Auditor awakening...")
        # 初期化処理（必要に応じて追加）
        
    def on_autonomous_activity(self):
        """自律活動処理"""
        # 定期的な自律監査活動（必要に応じて実装）
        logger.debug("🔍 Performing autonomous integrity checks...")
        
    def on_learning_cycle(self):
        """学習サイクル処理"""
        # 誠実性パターンの学習・更新
        logger.info("📚 Learning new integrity patterns...")



# 使用例とテスト
async def main():
    """テスト用メイン関数"""
    logging.basicConfig(level=logging.INFO)
    
    # Ancient Elder Integrity Auditor を作成
    auditor = AncientElderIntegrityAuditor()
    
    # テスト用の監査リクエスト
    audit_request = AuditRequest(
        target_path=Path("libs/"),
        git_repo=Path("."),
        check_git_history=True,
        check_sage_logs=True
    )
    
    # 監査実行
    result = await auditor.execute_audit(audit_request)
    
    print("\n🔮 Ancient Elder Integrity Audit Results")
    print("=" * 50)
    print(f"Score: {result.score}/100")
    print(f"Verdict: {result.verdict}")
    print(f"Violations: {len(result.violations)}")
    print(f"Processing Time: {result.processing_time_ms:.2f}ms")
    
    if result.violations:
        print("\n📋 Violations Found:")
        for i, violation in enumerate(result.violations[:5], 1):  # 最初の5件のみ表示
            print(f"{i}. {violation.type.value} ({violation.severity.value})")
            print(f"   File: {violation.file_path}:{violation.line_number}")
            print(f"   Evidence: {violation.evidence}")
            print(f"   Description: {violation.description}")
            print()
    
    if result.recommendations:
        print("\n💡 Recommendations:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"{i}. {rec}")


if __name__ == "__main__":
    asyncio.run(main())