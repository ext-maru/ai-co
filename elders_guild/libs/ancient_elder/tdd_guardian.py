"""
🔴🟢🔵 TDD Guardian Magic - TDD守護監査魔法
Red→Green→Refactorサイクルの実践を監査し、TDD違反を検出する
"""

import ast
import asyncio
import json
import logging
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
import xml.etree.ElementTree as ET

# プロジェクトルートをパスに追加
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.ancient_elder.base import AncientElderBase, AuditResult, ViolationSeverity

class TDDCyclePhase:
    """TDD サイクルフェーズ"""
    RED = "red"        # 失敗するテストを書く
    GREEN = "green"    # 最小限の実装でテストを通す
    REFACTOR = "refactor"  # リファクタリング

class TDDViolationType:
    """TDD違反の種類"""
    MISSING_TEST_FIRST = "MISSING_TEST_FIRST"          # テストファーストなし
    IMPLEMENTATION_BEFORE_TEST = "IMPLEMENTATION_BEFORE_TEST"  # テスト前実装
    NO_RED_PHASE = "NO_RED_PHASE"                      # Red段階なし
    SKIPPED_GREEN_PHASE = "SKIPPED_GREEN_PHASE"        # Green段階スキップ
    INSUFFICIENT_REFACTOR = "INSUFFICIENT_REFACTOR"    # 不十分なリファクタリング
    POOR_TEST_QUALITY = "POOR_TEST_QUALITY"            # 低品質テスト
    COVERAGE_MANIPULATION = "COVERAGE_MANIPULATION"    # カバレッジ操作
    FAKE_TEST_IMPLEMENTATION = "FAKE_TEST_IMPLEMENTATION"  # 偽テスト実装

class TDDCycleTracker:
    """TDDサイクル実行トラッカー"""
    
    def __init__(self, project_root: Optional[Path] = None)self.project_root = project_root or Path.cwd()
    """初期化メソッド"""
        self.logger = logging.getLogger("TDDCycleTracker")
        
        # Gitコミット履歴からTDDサイクルを追跡
        self.git_patterns = {
            TDDCyclePhase.RED: [
                re.compile(r'red[:\s]|failing.*test|test.*fail', re.IGNORECASE),
                re.compile(r'tdd.*red|add.*failing.*test', re.IGNORECASE),
                re.compile(r'🔴|red.*phase', re.IGNORECASE),
            ],
            TDDCyclePhase.GREEN: [
                re.compile(r'green[:\s]|test.*pass|make.*test.*pass', re.IGNORECASE),
                re.compile(r'tdd.*green|implement.*to.*pass', re.IGNORECASE),
                re.compile(r'🟢|green.*phase', re.IGNORECASE),
            ],
            TDDCyclePhase.REFACTOR: [
                re.compile(r'refactor|cleanup|improve', re.IGNORECASE),
                re.compile(r'tdd.*refactor|code.*improvement', re.IGNORECASE),
                re.compile(r'🔵|refactor.*phase', re.IGNORECASE),
            ]
        }
        
    def analyze_tdd_cycle_compliance(self, 
                                   file_path: str,
                                   time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """TDDサイクル遵守状況を分析"""
        if time_window is None:
            time_window = timedelta(days=30)  # デフォルト30日
            
        try:
            # Gitコミット履歴を取得
            commits = self._get_git_commits(file_path, time_window)
            
            # TDDサイクルを分析
            cycles = self._analyze_tdd_cycles(commits)
            
            # 違反を検出
            violations = self._detect_cycle_violations(cycles, file_path)
            
            return {
                "file_path": file_path,
                "time_window": str(time_window),
                "total_commits": len(commits),
                "detected_cycles": len(cycles),
                "violations": violations,
                "cycle_compliance_rate": self._calculate_compliance_rate(cycles),
                "cycles": cycles
            }
            
        except Exception as e:
            self.logger.error(f"TDD cycle analysis failed for {file_path}: {e}")
            return {
                "file_path": file_path,
                "error": str(e),
                "violations": [],
                "cycle_compliance_rate": 0.0
            }
            
    def _get_git_commits(self, file_path: str, time_window: timedelta) -> List[Dict[str, Any]]since_date = (datetime.now() - time_window).strftime('%Y-%m-%d'):
    """定ファイルのGitコミット履歴を取得"""
        :
        try:
            cmd = [
                'git', 'log', '--oneline', '--follow', 
                f'--since={since_date}', '--format=%H|%s|%ai|%an', 
                file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                self.logger.warning(f"Git log failed for {file_path}: {result.stderr}")
                return []
                
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        commits.append({
                            "hash": parts[0],
                            "message": parts[1],
                            "date": parts[2],
                            "author": parts[3]
                        })
                        
            return commits
            
        except Exception as e:
            self.logger.error(f"Git commits retrieval failed: {e}")
            return []
            
    def _analyze_tdd_cycles(self, commits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """コミット履歴からTDDサイクルを分析"""
        cycles = []
        current_cycle = None
        
        # 新しい順（最新→最古）で処理し、Redで逆向きサイクル開始を検出
        for commit in commits:  # 新しい順に処理
            message = commit["message"]
            detected_phase = self._detect_tdd_phase(message)
            
            if detected_phase == TDDCyclePhase.RED:
                # 前のサイクルを完了してから新しいサイクル開始
                if current_cycle:
                    # 前のサイクルの完了判定
                    if self._is_cycle_complete(current_cycle["phases"]):
                        current_cycle["complete"] = True
                    cycles.insert(0, current_cycle)  # 時系列順に保つため先頭に挿入
                    
                current_cycle = {
                    "start_commit": commit,
                    "phases": {TDDCyclePhase.RED: [commit]},
                    "complete": False
                }
                
            elif current_cycle and detected_phase:
                # 既存サイクルにフェーズ追加
                if detected_phase not in current_cycle["phases"]:
                    current_cycle["phases"][detected_phase] = []
                current_cycle["phases"][detected_phase].append(commit)
                
                # サイクル完了判定
                if self._is_cycle_complete(current_cycle["phases"]):
                    current_cycle["complete"] = True
                    
        # 最後のサイクルを追加（完了判定も実行）
        if current_cycle:
            if self._is_cycle_complete(current_cycle["phases"]):
                current_cycle["complete"] = True
            cycles.insert(0, current_cycle)  # 時系列順に保つため先頭に挿入
            
        return cycles
        
    def _detect_tdd_phase(self, commit_message: str) -> Optional[str]for phase, patterns in self.git_patterns.items():
    """コミットメッセージからTDDフェーズを検出"""
            for pattern in patterns:
                if pattern.search(commit_message):
                    return phase
        return None
        
    def _is_cycle_complete(self, phases: Dict[str, List]) -> bool:
        """TDDサイクルが完了しているかチェック"""
        required_phases = [TDDCyclePhase.RED, TDDCyclePhase.GREEN]
        return all(phase in phases for phase in required_phases)
        
    def _detect_cycle_violations(
        self,
        cycles: List[Dict[str, Any]],
        file_path: str
    ) -> List[Dict[str, Any]]:
        """TDDサイクル違反を検出"""
        violations = []
        
        for i, cycle in enumerate(cycles):
            cycle_violations = []
            
            # Red段階なしの違反
            if TDDCyclePhase.RED not in cycle["phases"]:
                cycle_violations.append({
                    "type": TDDViolationType.NO_RED_PHASE,
                    "severity": "CRITICAL",
                    "description": "TDD cycle missing Red phase (failing test first)",
                    "cycle_index": i
                })
                
            # Green段階スキップの違反
            if TDDCyclePhase.GREEN not in cycle["phases"]:
                cycle_violations.append({
                    "type": TDDViolationType.SKIPPED_GREEN_PHASE,
                    "severity": "HIGH",
                    "description": "TDD cycle missing Green phase (minimal implementation)",
                    "cycle_index": i
                })
                
            # リファクタリング不足の違反
            if (cycle["complete"] and 
                TDDCyclePhase.REFACTOR not in cycle["phases"]):
                cycle_violations.append({
                    "type": TDDViolationType.INSUFFICIENT_REFACTOR,
                    "severity": "MEDIUM",
                    "description": "TDD cycle missing Refactor phase",
                    "cycle_index": i
                })
                
            violations.extend(cycle_violations)
            
        return violations
        
    def _calculate_compliance_rate(self, cycles: List[Dict[str, Any]]) -> float:
        """TDDサイクル遵守率を計算"""
        if not cycles:
            return 0.0
            
        complete_cycles = sum(1 for cycle in cycles if cycle["complete"])
        return (complete_cycles / len(cycles)) * 100.0

class TestQualityAnalyzer:
    """テスト品質・実質性評価システム"""
    
    def __init__(self):
    """初期化メソッド"""
        
        # 低品質テストのパターン
        self.poor_quality_patterns = [
            # 空のテスト
            re.compile(r'def\s+test_\w+\([^)]*\):\s*pass', re.MULTILINE),
            re.compile(r'def\s+test_\w+\([^)]*\):\s*\.\.\.$', re.MULTILINE),

            re.compile(r'@pytest\.mark\.skip|@unittest\.skip', re.IGNORECASE),
            re.compile(r'@pytest\.mark\.xfail', re.IGNORECASE),
            # 常にTrueアサーション
            re.compile(r'assert\s+True', re.IGNORECASE),
            re.compile(r'assertEqual\(True,\s*True\)', re.IGNORECASE),
        ]
        
        # 偽実装パターン
        self.fake_implementation_patterns = [
            re.compile(r'return\s+True\s*#.*fake', re.IGNORECASE),
            re.compile(r'return\s+False\s*#.*fake', re.IGNORECASE),
            re.compile(r'return\s+".*"\s*#.*fake', re.IGNORECASE),
            re.compile(r'pass\s*#.*fake', re.IGNORECASE),
        ]
        
    def analyze_test_quality(self, test_file_path: str) -> Dict[str, Any]:
        """テストファイルの品質を分析"""
        try:
            with open(test_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # AST解析
            tree = ast.parse(content)
            
            # テスト関数を抽出
            test_functions = self._extract_test_functions(tree)
            
            # 品質評価
            quality_score = self._calculate_quality_score(content, test_functions)
            
            # 違反検出
            violations = self._detect_test_violations(content, test_functions)
            
            return {
                "file_path": test_file_path,
                "total_tests": len(test_functions),
                "quality_score": quality_score,
                "violations": violations,
                "test_functions": [func["name"] for func in test_functions],
                "analysis_details": {
                    "empty_tests": self._count_empty_tests(test_functions),
                    "assertion_count": self._count_assertions(content),
                    "mock_usage": self._analyze_mock_usage(content),
                    "coverage_indicators": self._analyze_coverage_indicators(content)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Test quality analysis failed for {test_file_path}: {e}")
            return {
                "file_path": test_file_path,
                "error": str(e),
                "quality_score": 0.0,
                "violations": []
            }
            
    def _extract_test_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """ASTからテスト関数を抽出"""
        test_functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                test_functions.append({
                    "name": node.name,
                    "lineno": node.lineno,
                    "body_length": len(node.body),
                    "docstring": ast.get_docstring(node),
                    "decorators": [d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list],
                    "has_assertions": self._has_assertions(node)
                })
                
        return test_functions
        
    def _has_assertions(self, func_node: ast.FunctionDef) -> boolfor node in ast.walk(func_node)if isinstance(node, ast.Assert):
    """関数内にアサーションがあるかチェック"""
                return True
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr.startswith('assert'):
                        return True
        return False
        
    def _calculate_quality_score(self, content: str, test_functions: List[Dict[str, Any]]) -> float:
        """テスト品質スコアを計算（0-100）"""
        if not test_functions:
            return 0.0
            
        score = 100.0
        
        # 空のテストペナルティ
        empty_tests = sum(1 for func in test_functions if func["body_length"] <= 1)
        if empty_tests > 0:
            score -= (empty_tests / len(test_functions)) * 50
            
        # アサーションなしペナルティ
        no_assertion_tests = sum(1 for func in test_functions if not func["has_assertions"])
        if no_assertion_tests > 0:
            score -= (no_assertion_tests / len(test_functions)) * 30
            
        # 低品質パターンペナルティ
        for pattern in self.poor_quality_patterns:
            matches = len(pattern.findall(content))
            if matches > 0:
                score -= matches * 10
                
        # ドキュメント不足ペナルティ
        undocumented_tests = sum(1 for func in test_functions if not func["docstring"])
        if undocumented_tests > 0:
            score -= (undocumented_tests / len(test_functions)) * 5
            
        return max(0.0, score)
        
    def _detect_test_violations(
        self,
        content: str,
        test_functions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """テスト品質違反を検出"""
        violations = []
        
        # 空のテスト検出
        for func in test_functions:
            if func["body_length"] <= 1:
                violations.append({
                    "type": TDDViolationType.POOR_TEST_QUALITY,
                    "severity": "HIGH",
                    "description": f"Empty or minimal test: {func['name']}",
                    "location": f"line {func['lineno']}",
                    "function_name": func["name"]
                })
                
        # アサーションなしテスト検出
        for func in test_functions:
            if not func["has_assertions"]:
                violations.append({
                    "type": TDDViolationType.POOR_TEST_QUALITY,
                    "severity": "CRITICAL",
                    "description": f"Test without assertions: {func['name']}",
                    "location": f"line {func['lineno']}",
                    "function_name": func["name"]
                })
                
        # 偽実装検出
        for pattern in self.fake_implementation_patterns:
            for match in pattern.finditer(content):
                violations.append({
                    "type": TDDViolationType.FAKE_TEST_IMPLEMENTATION,
                    "severity": "CRITICAL",
                    "description": f"Fake test implementation detected",
                    "location": f"line {content[:match.start()].count(chr(10)) + 1}",
                    "code_snippet": match.group()
                })
                
        return violations
        
    def _count_empty_tests(self, test_functions: List[Dict[str, Any]]) -> intreturn sum(1 for func in test_functions if func["body_length"] <= 1):
    """のテスト数をカウント"""
        :
    def _count_assertions(self, content: str) -> int:
        """アサーションの数をカウント"""
        assertion_patterns = [
            re.compile(r'\bassert\s+', re.IGNORECASE),
            re.compile(r'\.assert\w+\(', re.IGNORECASE),
            re.compile(r'pytest\.raises', re.IGNORECASE),
        ]
        
        total_assertions = 0
        for pattern in assertion_patterns:
            total_assertions += len(pattern.findall(content))
            
        return total_assertions
        
    def _analyze_mock_usage(self, content: str) -> Dict[str, Any]:
        """モック使用状況を分析"""
        mock_patterns = [
            re.compile(r'@patch|@mock', re.IGNORECASE),
            re.compile(r'Mock\(|MagicMock\(', re.IGNORECASE),
            re.compile(r'unittest\.mock', re.IGNORECASE),
        ]
        
        mock_count = 0
        for pattern in mock_patterns:
            mock_count += len(pattern.findall(content))
            
        return {
            "total_mocks": mock_count,
            "mock_ratio": mock_count / max(1, content.count('def test_'))
        }
        
    def _analyze_coverage_indicators(self, content: str) -> Dict[str, Any]:
        """カバレッジ操作の兆候を分析"""
        coverage_manipulation_patterns = [
            re.compile(r'pragma:\s*no\s*cover', re.IGNORECASE),
            re.compile(r'coverage:\s*ignore', re.IGNORECASE),
            re.compile(r'#.*coverage.*skip', re.IGNORECASE),
        ]
        
        suspicious_patterns = 0
        for pattern in coverage_manipulation_patterns:
            suspicious_patterns += len(pattern.findall(content))
            
        return {
            "suspicious_coverage_patterns": suspicious_patterns,
            "has_coverage_manipulation": suspicious_patterns > 0
        }

class CoverageManipulationDetector:
    """カバレッジ操作検出システム"""
    
    def __init__(self, project_root: Optional[Path] = None)self.project_root = project_root or Path.cwd()
    """初期化メソッド"""
        self.logger = logging.getLogger("CoverageManipulationDetector")
        
    def detect_coverage_manipulation(self, coverage_file: Optional[str] = None) -> Dict[str, Any]:
        """カバレッジ操作を検出"""
        try:
            # カバレッジレポートを分析
            coverage_data = self._load_coverage_data(coverage_file)
            
            # 疑わしいパターンを検出
            violations = []
            
            # 異常に高いカバレッジ率
            high_coverage_violations = self._detect_suspiciously_high_coverage(coverage_data)
            violations.extend(high_coverage_violations)
            
            # カバレッジ除外の乱用
            exclusion_violations = self._detect_coverage_exclusion_abuse()
            violations.extend(exclusion_violations)
            
            # 偽のテストパターン
            fake_test_violations = self._detect_fake_test_patterns()
            violations.extend(fake_test_violations)
            
            return {
                "coverage_data": coverage_data,
                "violations": violations,
                "manipulation_score": self._calculate_manipulation_score(violations),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Coverage manipulation detection failed: {e}")
            return {
                "error": str(e),
                "violations": [],
                "manipulation_score": 0.0
            }
            
    def _load_coverage_data(self, coverage_file: Optional[str]) -> Dict[str, Any]if coverage_file and Path(coverage_file).exists():
    """カバレッジデータを読み込み"""
            try:
                if coverage_file.endswith('.xml'):
                    return self._parse_coverage_xml(coverage_file)
                elif coverage_file.endswith('.json'):
                    with open(coverage_file, 'r') as f:
                        return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load coverage file {coverage_file}: {e}")
                
        # カバレッジファイルが見つからない場合はpytestで生成を試行
        return self._generate_coverage_report()
        
    def _parse_coverage_xml(self, xml_file: str) -> Dict[str, Any]tree = ET.parse(xml_file)root = tree.getroot()
    """ML形式のカバレッジレポートを解析"""
        
        coverage_data = {:
            "overall_coverage": 0.0,
            "files": {},
            "summary": {}
        }
        
        # 全体カバレッジ取得
        if root.attrib.get('line-rate'):
            coverage_data["overall_coverage"] = float(root.attrib['line-rate']) * 100
            
        # ファイル別カバレッジ取得
        for package in root.findall('.//package'):
            for class_elem in package.findall('classes/class'):
                filename = class_elem.get('filename', '')
                line_rate = float(class_elem.get('line-rate', 0))
                
                coverage_data["files"][filename] = {
                    "line_coverage": line_rate * 100,
                    "lines": {}
                }
                
        return coverage_data
        
    def _generate_coverage_report(self) -> Dict[str, Any]:
        """pytestでカバレッジレポートを生成"""
        try:
            cmd = ['python', '-m', 'pytest', '--cov=.', '--cov-report=json', '--cov-report=term-missing']
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            # JSONレポートを読み込み
            coverage_json = self.project_root / 'coverage.json'
            if coverage_json.exists():
                with open(coverage_json, 'r') as f:
                    return json.load(f)
                    
        except Exception as e:
            self.logger.warning(f"Failed to generate coverage report: {e}")
            
        return {"overall_coverage": 0.0, "files": {}}
        
    def _detect_suspiciously_high_coverage(
        self,
        coverage_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """異常に高いカバレッジ率を検出"""
        violations = []
        
        overall_coverage = coverage_data.get("overall_coverage", 0.0)
        
        # 100%カバレッジは疑わしい（小さなプロジェクトを除く）
        if overall_coverage >= 100.0:
            file_count = len(coverage_data.get("files", {}))
            if file_count > 10:  # 10ファイル以上で100%は疑わしい
                violations.append({
                    "type": TDDViolationType.COVERAGE_MANIPULATION,
                    "severity": "HIGH",
                    "description": f"Suspiciously high coverage: {overall_coverage}% for {file_count} files",
                    "details": {
                        "coverage_percentage": overall_coverage,
                        "file_count": file_count
                    }
                })
                
        return violations
        
    def _detect_coverage_exclusion_abuse(self) -> List[Dict[str, Any]]:
        """カバレッジ除外の乱用を検出"""
        violations = []
        
        # プロジェクト内のPythonファイルでカバレッジ除外パターンを検索
        exclusion_patterns = [
            re.compile(r'#\s*pragma:\s*no\s*cover', re.IGNORECASE),
            re.compile(r'#\s*coverage:\s*ignore', re.IGNORECASE),
            re.compile(r'#\s*nocov', re.IGNORECASE),
        ]
        
        total_exclusions = 0
        files_with_exclusions = 0
        
        for py_file in self.project_root.rglob('*.py'):
            if 'test' in str(py_file) or 'venv' in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                file_exclusions = 0
                for pattern in exclusion_patterns:
                    matches = pattern.findall(content)
                    file_exclusions += len(matches)
                    
                if file_exclusions > 0:
                    files_with_exclusions += 1
                    total_exclusions += file_exclusions
                    
                    # 1ファイルで5個以上の除外は疑わしい
                    if file_exclusions >= 5:
                        violations.append({
                            "type": TDDViolationType.COVERAGE_MANIPULATION,
                            "severity": "MEDIUM",
                            "description": f"Excessive coverage exclusions in 
                                f"{py_file.name}: {file_exclusions} exclusions",
                            "location": str(py_file),
                            "exclusion_count": file_exclusions
                        })
                        
            except Exception as e:
                self.logger.warning(f"Failed to analyze {py_file}: {e}")
                
        # 全体的な除外乱用チェック
        if total_exclusions > 50:  # プロジェクト全体で50個以上は疑わしい
            violations.append({
                "type": TDDViolationType.COVERAGE_MANIPULATION,
                "severity": "HIGH",
                "description": f"Excessive project-wide coverage exclusions: {total_exclusions} total",
                "details": {
                    "total_exclusions": total_exclusions,
                    "files_with_exclusions": files_with_exclusions
                }
            })
            
        return violations
        
    def _detect_fake_test_patterns(self) -> List[Dict[str, Any]]:
        """偽のテストパターンを検出"""
        violations = []
        
        # テストファイルを検索
        for test_file in self.project_root.rglob('test_*.py'):
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 偽テストパターンを検出
                fake_patterns = [
                    (re.compile(
                        r'def\s+test_\w+\([^)]*\):\s*pass',
                        re.MULTILINE), "Empty test function"
                    ),
                    (re.compile(r'assert\s+True\s*#.*fake', re.IGNORECASE), "Fake assertion"),
                    (re.compile(r'assert\s+1\s*==\s*1', re.IGNORECASE), "Meaningless assertion"),
                ]
                
                for pattern, description in fake_patterns:
                    matches = pattern.findall(content)
                    if matches:
                        violations.append({
                            "type": TDDViolationType.FAKE_TEST_IMPLEMENTATION,
                            "severity": "CRITICAL",
                            "description": f"{description} in {test_file.name}",
                            "location": str(test_file),
                            "pattern_matches": len(matches)
                        })
                        
            except Exception as e:
                self.logger.warning(f"Failed to analyze test file {test_file}: {e}")
                
        return violations
        
    def _calculate_manipulation_score(self, violations: List[Dict[str, Any]]) -> float:
        """カバレッジ操作スコアを計算（0-100、高いほど疑わしい）"""
        if not violations:
            return 0.0
            
        score = 0.0
        
        severity_weights = {
            "CRITICAL": 25,
            "HIGH": 15,
            "MEDIUM": 5,
            "LOW": 1
        }
        
        for violation in violations:
            severity = violation.get("severity", "LOW")
            score += severity_weights.get(severity, 1)
            
        return min(100.0, score)

class TDDGuardian(AncientElderBase):
    """
    🔴🟢🔵 TDD守護監査魔法
    
    Red→Green→Refactorサイクルの実践を監査し、
    TDD違反を検出する
    """
    
    def __init__(self, project_root: Optional[Path] = None)super().__init__(specialty="tdd_guardian")
    """初期化メソッド"""
        
        # コンポーネント初期化
        self.cycle_tracker = TDDCycleTracker(project_root)
        self.quality_analyzer = TestQualityAnalyzer()
        self.coverage_detector = CoverageManipulationDetector(project_root)
        
        # 設定
        self.project_root = project_root or Path.cwd()
        
        # TDD品質基準
        self.quality_thresholds = {
            "minimum_test_quality_score": 70.0,
            "maximum_coverage_manipulation_score": 20.0,
            "minimum_cycle_compliance_rate": 80.0,
            "maximum_empty_test_ratio": 0.1,  # 10%
            "minimum_assertion_per_test": 1.0
        }
        
    async def execute_audit(self, target_path: str, **kwargs) -> AuditResultstart_time = datetime.now():
    """DD守護監査を実行"""
        violations = []
        metrics = {}
        :
        try:
            self.logger.info(f"🧪 Starting TDD Guardian audit for: {target_path}")
            
            # テストファイルを発見
            test_files = self._discover_test_files(target_path)
            
            if not test_files:
                self.logger.warning(f"No test files found in {target_path}")
                # 空の場合のAuditResultを正しく作成
                empty_result = AuditResult()
                empty_result.auditor_name = "TDDGuardian"
                empty_result.violations = []
                empty_result.metrics = {
                    "test_files_found": 0,
                    "target_path": target_path,
                    "recommendations": ["Implement TDD with test files"],
                    "execution_time": (datetime.now() - start_time).total_seconds()
                }
                return empty_result
                
            # 1.0 TDDサイクル分析
            time_window = timedelta(days=30)
            cycle_violations = 0
            
            for test_file in test_files:
                cycle_analysis = self.cycle_tracker.analyze_tdd_cycle_compliance(
                    str(test_file), time_window
                )
                violations.extend(cycle_analysis.get("violations", []))
                cycle_violations += len(cycle_analysis.get("violations", []))
                
            # 2.0 テスト品質分析
            quality_violations = 0
            total_quality_score = 0.0
            
            for test_file in test_files:
                quality_analysis = self.quality_analyzer.analyze_test_quality(str(test_file))
                violations.extend(quality_analysis.get("violations", []))
                quality_violations += len(quality_analysis.get("violations", []))
                total_quality_score += quality_analysis.get("quality_score", 0.0)
                
            # 3.0 カバレッジ操作検出
            coverage_analysis = self.coverage_detector.detect_coverage_manipulation()
            violations.extend(coverage_analysis.get("violations", []))
            coverage_violations = len(coverage_analysis.get("violations", []))
            
            # 4.0 総合TDDスコア計算
            avg_quality_score = total_quality_score / max(len(test_files), 1)
            overall_score = self._calculate_overall_tdd_score(
                avg_quality_score, cycle_violations, quality_violations, coverage_violations
            )
            
            metrics["overall_tdd_score"] = overall_score
            metrics["test_files_analyzed"] = len(test_files)
            metrics["cycle_violations"] = cycle_violations
            metrics["quality_violations"] = quality_violations
            metrics["coverage_violations"] = coverage_violations
            metrics["average_test_quality"] = avg_quality_score
            
            # 5.0 改善提案生成
            recommendations = self._generate_tdd_improvement_recommendations(
                cycle_violations, quality_violations, coverage_violations, violations
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            metrics["execution_time"] = execution_time
            
            self.logger.info(f"✅ TDD Guardian audit completed in {execution_time:0.2f}s")
            
            # AuditResultを正しく作成
            result = AuditResult()
            result.auditor_name = "TDDGuardian"
            result.violations = violations
            result.metrics = metrics
            result.metrics["target_path"] = target_path
            result.metrics["recommendations"] = recommendations
            result.metrics["execution_time"] = execution_time
            return result
            
        except Exception as e:
            self.logger.error(f"❌ TDD Guardian audit failed: {e}")
            # エラー時のAuditResultを正しく作成
            error_result = AuditResult()
            error_result.auditor_name = "TDDGuardian"
            error_result.violations = [{
                "type": "AUDIT_EXECUTION_FAILURE",
                "severity": ViolationSeverity.HIGH.value,
                "description": f"TDD Guardian audit execution failed: {str(e)}",
                "location": target_path
            }]
            error_result.metrics = {
                "error": str(e),
                "target_path": target_path,
                "recommendations": [],
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
            return error_result
            
    def _discover_test_files(self, target_path: str) -> List[str]:
        """テストファイルを発見"""
        test_files = []
        
        # テストファイルパターン
        test_patterns = [
            "**/test_*.py",
            "**/*_test.py", 
            "**/tests/**/*.py",
            "**/*Test.py"
        ]
        
        target_dir = Path(target_path)
        if target_dir.is_file():
            target_dir = target_dir.parent
            
        for pattern in test_patterns:
            test_files.extend([str(f) for f in target_dir.rglob(pattern)])
            
        # 重複除去
        return list(set(test_files))
        
    def _calculate_overall_tdd_score(self, 
                                   avg_quality: float,
                                   cycle_violations: int,
                                   quality_violations: int,
                                   coverage_violations: int) -> float:
        """総合TDDスコアを計算"""
        base_score = avg_quality
        
        # 違反による減点
        violation_penalty = (cycle_violations * 15 + 
                           quality_violations * 10 + 
                           coverage_violations * 20)
        
        final_score = base_score - violation_penalty
        return max(min(final_score, 100.0), 0.0)
        
    def _generate_tdd_improvement_recommendations(self,
                                                cycle_violations: int,
                                                quality_violations: int,
                                                coverage_violations: int,
                                                violations: List[Dict[str, Any]]) -> List[str]:
        """TDD改善提案を生成"""
        recommendations = []
        
        if cycle_violations > 0:
            recommendations.append("Follow proper TDD Red-Green-Refactor cycle")
            
        if quality_violations > 0:
            recommendations.append("Improve test quality by adding meaningful assertions")
            
        if coverage_violations > 0:
            recommendations.append("Remove coverage manipulation and write genuine tests")
            
        # 違反固有の提案
        violation_types = set(v.get("type") for v in violations)
        
        if "NO_RED_PHASE" in violation_types:
            recommendations.append("Always start with a failing test (Red phase)")
            
        if "POOR_TEST_QUALITY" in violation_types:
            recommendations.append("Remove empty tests and add proper test logic")
            
        if "FAKE_TEST_IMPLEMENTATION" in violation_types:
            recommendations.append("Replace fake test implementations with real tests")
            
        return recommendations
        
    def get_audit_scope(self) -> List[str]:
        """監査対象スコープを返す"""
        return [
            "tdd_cycle_compliance",
            "test_quality_assessment", 
            "coverage_manipulation_detection",
            "test_first_principle_validation"
        ]
        
    async def audit(self, target: Dict[str, Any]) -> AuditResult:
        """
        TDD守護監査を実行
        
        Args:
            target: 監査対象
                - type: "project", "file", "test_file"
                - path: ファイルパス（省略可）
                - time_window_days: 監査期間（日数、デフォルト30）
                - include_coverage: カバレッジ分析を含むか（デフォルトTrue）
                
        Returns:
            AuditResult: 監査結果
        """
        result = AuditResult()
        result.auditor_name = self.name
        
        target_type = target.get("type", "project")
        target_path = target.get("path", str(self.project_root))
        time_window = timedelta(days=target.get("time_window_days", 30))
        include_coverage = target.get("include_coverage", True)
        
        try:
            if target_type == "project":
                await self._audit_project(result, target_path, time_window, include_coverage)
            elif target_type == "file":
                await self._audit_single_file(result, target_path, time_window)
            elif target_type == "test_file":
                await self._audit_test_file(result, target_path)
            else:
                result.add_violation(
                    severity=ViolationSeverity.HIGH,
                    title="Invalid audit target type",
                    description=f"Unsupported target type: {target_type}",
                    metadata={"category": "configuration"}
                )
                
            # メトリクスを計算
            self._calculate_tdd_metrics(result, target)
            
        except Exception as e:
            result.add_violation(
                severity=ViolationSeverity.HIGH,
                title="TDD Guardian audit failed",
                description=f"Audit execution failed: {str(e)}",
                metadata={"category": "system", "error": str(e)}
            )
            
        return result
        
    async def _audit_project(self, 
                           result: AuditResult, 
                           project_path: str, 
                           time_window: timedelta,
                           include_coverage: bool):
        """プロジェクト全体のTDD監査"""
        project_root = Path(project_path)
        
        # Python実装ファイルを検索
        python_files = list(project_root.rglob('*.py'))
        implementation_files = [f for f in python_files if not f.name.startswith('test_')]
        test_files = [f for f in python_files if f.name.startswith('test_')]
        
        # TDDサイクル遵守監査
        cycle_violations = 0
        total_files_analyzed = 0
        
        for impl_file in implementation_files:
            if self._should_skip_file(impl_file):
                continue
                
            total_files_analyzed += 1
            cycle_analysis = self.cycle_tracker.analyze_tdd_cycle_compliance(
                str(impl_file), time_window
            )
            
            for violation in cycle_analysis.get("violations", []):
                result.add_violation(
                    severity=ViolationSeverity[violation["severity"]],
                    title="TDD cycle violation",
                    description=violation["description"],
                    location=str(impl_file),
                    metadata={
                        "category": "tdd_cycle",
                        "violation_type": violation["type"],
                        "cycle_index": violation.get("cycle_index"),
                        "file_path": str(impl_file)
                    }
                )
                cycle_violations += 1
                
        # テスト品質監査
        test_violations = 0
        total_test_quality_score = 0.0
        
        for test_file in test_files:
            if self._should_skip_file(test_file):
                continue
                
            quality_analysis = self.quality_analyzer.analyze_test_quality(str(test_file))
            
            total_test_quality_score += quality_analysis.get("quality_score", 0.0)
            
            for violation in quality_analysis.get("violations", []):
                result.add_violation(
                    severity=ViolationSeverity[violation["severity"]],
                    title="Test quality violation",
                    description=violation["description"],
                    location=f"{test_file}:{violation.get('location', '')}",
                    suggested_fix=self._suggest_test_quality_fix(violation),
                    metadata={
                        "category": "test_quality",
                        "violation_type": violation["type"],
                        "function_name": violation.get("function_name"),
                        "file_path": str(test_file)
                    }
                )
                test_violations += 1
                
        # カバレッジ操作検出
        coverage_violations = 0
        if include_coverage:
            coverage_analysis = self.coverage_detector.detect_coverage_manipulation()
            
            for violation in coverage_analysis.get("violations", []):
                result.add_violation(
                    severity=ViolationSeverity[violation["severity"]],
                    title="Coverage manipulation detected",
                    description=violation["description"],
                    location=violation.get("location", ""),
                    suggested_fix="Remove unnecessary coverage exclusions and write genuine tests",
                    metadata={
                        "category": "coverage",
                        "violation_type": violation["type"],
                        "manipulation_details": violation.get("details", {})
                    }
                )
                coverage_violations += 1
                
        # プロジェクトレベルの品質評価
        avg_test_quality = total_test_quality_score / max(1, len(test_files))
        
        if avg_test_quality < self.quality_thresholds["minimum_test_quality_score"]:
            result.add_violation(
                severity=ViolationSeverity.HIGH,
                title="Low overall test quality",
                description=f"Average test quality score: {avg_test_quality:." \
                    "1f} < {self.quality_thresholds['minimum_test_quality_score']}",
                suggested_fix="Improve test assertions, documentation, and remove empty tests",
                metadata={
                    "category": "project_quality",
                    "average_score": avg_test_quality,
                    "threshold": self.quality_thresholds["minimum_test_quality_score"]
                }
            )
            
    async def _audit_single_file(self, result: AuditResult, file_path: str, time_window: timedelta)cycle_analysis = self.cycle_tracker.analyze_tdd_cycle_compliance(file_path, time_window)
    """単一ファイルのTDD監査"""
        
        for violation in cycle_analysis.get("violations", []):
            result.add_violation(
                severity=ViolationSeverity[violation["severity"]],
                title="TDD cycle violation",
                description=violation["description"],
                location=file_path,
                suggested_fix=self._suggest_cycle_fix(violation),
                metadata={
                    "category": "tdd_cycle",
                    "violation_type": violation["type"],
                    "file_path": file_path
                }
            )
            
    async def _audit_test_file(self, result: AuditResult, test_file_path: str)quality_analysis = self.quality_analyzer.analyze_test_quality(test_file_path)
    """テストファイルの品質監査"""
        
        for violation in quality_analysis.get("violations", []):
            result.add_violation(
                severity=ViolationSeverity[violation["severity"]],
                title="Test quality violation",
                description=violation["description"],
                location=f"{test_file_path}:{violation.get('location', '')}",
                suggested_fix=self._suggest_test_quality_fix(violation),
                metadata={
                    "category": "test_quality",
                    "violation_type": violation["type"],
                    "function_name": violation.get("function_name"),
                    "file_path": test_file_path
                }
            )
            
    def _should_skip_file(self, file_path: Path) -> bool:
        """ファイルをスキップすべきかチェック"""
        skip_patterns = [
            'venv', 'node_modules', '.git', '__pycache__',

        ]
        
        path_str = str(file_path)
        return any(pattern in path_str for pattern in skip_patterns)
        
    def _suggest_cycle_fix(self, violation: Dict[str, Any]) -> strviolation_type = violation.get("type", ""):
    """DDサイクル違反の修正提案"""
        
        fixes = {:
            TDDViolationType.NO_RED_PHASE: "Write a failing test first before implementing functionality",
            TDDViolationType.SKIPPED_GREEN_PHASE: "Implement minimal code to make the test pass",
            TDDViolationType.INSUFFICIENT_REFACTOR: "Refactor code after making tests pass",
            TDDViolationType.IMPLEMENTATION_BEFORE_TEST: "Always write tests before implementation"
        }
        
        return fixes.get(violation_type, "Follow proper TDD Red→Green→Refactor cycle")
        
    def _suggest_test_quality_fix(self, violation: Dict[str, Any]) -> strviolation_type = violation.get("type", ""):
    """スト品質違反の修正提案"""
        
        fixes = {:
            TDDViolationType.POOR_TEST_QUALITY: "Add meaningful assertions and test logic",
            TDDViolationType.FAKE_TEST_IMPLEMENTATION: "Remove fake implementations and write real tests"
        }
        
        return fixes.get(violation_type, "Improve test quality and add proper assertions")
        
    def _calculate_tdd_metrics(self, result: AuditResult, target: Dict[str, Any]):
        """TDDメトリクスを計算"""
        violations = result.violations
        
        # 違反カテゴリ別カウント
        cycle_violations = len([v for v in violations if v.get("metadata", {}).get("category") == "tdd_cycle"])
        quality_violations = len([v for v in violations if v.get("metadata", {}).get("category") == "test_quality"])
        coverage_violations = len([v for v in violations if v.get("metadata", {}).get("category") == "coverage"])
        
        # TDD遵守スコア計算
        total_violations = len(violations)
        tdd_compliance_score = max(0, 100 - (total_violations * 5))  # 違反1件につき5点減点
        
        result.add_metric("tdd_compliance_score", tdd_compliance_score)
        result.add_metric("cycle_violations", cycle_violations)
        result.add_metric("test_quality_violations", quality_violations)
        result.add_metric("coverage_violations", coverage_violations)
        result.add_metric("total_violations", total_violations)
        
        # 追加メトリクス
        result.add_metric("audit_target_type", target.get("type", "unknown"))
        result.add_metric("audit_timestamp", datetime.now().isoformat())
        
    def get_audit_scope(self) -> Dict[str, Any]:
        """監査範囲を返す"""
        return {
            "scope": "tdd_guardian_magic",
            "targets": [
                "TDD Red→Green→Refactor cycle compliance",
                "Test quality and substantiality",
                "Coverage manipulation detection",
                "Fake test implementation detection",
                "Test-first development verification"
            ],
            "violation_types": [
                TDDViolationType.MISSING_TEST_FIRST,
                TDDViolationType.IMPLEMENTATION_BEFORE_TEST,
                TDDViolationType.NO_RED_PHASE,
                TDDViolationType.SKIPPED_GREEN_PHASE,
                TDDViolationType.INSUFFICIENT_REFACTOR,
                TDDViolationType.POOR_TEST_QUALITY,
                TDDViolationType.COVERAGE_MANIPULATION,
                TDDViolationType.FAKE_TEST_IMPLEMENTATION
            ],
            "quality_thresholds": self.quality_thresholds,
            "description": "TDD守護監査魔法 - Red→Green→Refactorサイクル実践監査とテスト品質評価"
        }