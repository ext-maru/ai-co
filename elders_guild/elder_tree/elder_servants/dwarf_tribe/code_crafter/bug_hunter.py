"""
BugHunter (D05) - バグ退治専門家サーバント
ドワーフ工房のデバッグ・品質保証スペシャリスト

EldersLegacy準拠実装 - Issue #70
"""

import ast
import asyncio
import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union

from elders_guild.elder_tree.elder_servants.base.elder_servant import (
    ServantCapability,
    TaskResult,
    TaskStatus,
)
from elders_guild.elder_tree.elder_servants.base.specialized_servants import DwarfServant


class BugHunter(DwarfServant[Dict[str, Any], Dict[str, Any]]):
    """
    D05: BugHunter - バグ退治専門家サーバント
    コードの問題検出・修正・品質向上のスペシャリスト

    EldersLegacy準拠: Iron Will品質基準に基づく
    徹底的なバグ検出と自動修正を提供
    """

    def __init__(self):
        """初期化メソッド"""
        capabilities = [
            ServantCapability(
                "static_analysis",
                "静的コード解析",
                ["source_code"],
                ["analysis_report"],
                complexity=6,
            ),
            ServantCapability(
                "bug_detection",
                "バグ検出・分類",
                ["source_code", "test_cases"],
                ["bug_report"],
                complexity=7,
            ),
            ServantCapability(
                "auto_fix_suggestion",
                "自動修正提案",
                ["source_code", "bug_report"],
                ["fix_suggestions"],
                complexity=8,
            ),
            ServantCapability(
                "code_smell_detection",
                "コードスメル検出",
                ["source_code"],
                ["smell_report"],
                complexity=5,
            ),
            ServantCapability(
                "vulnerability_scan",
                "脆弱性スキャン",
                ["source_code"],
                ["vulnerability_report"],
                complexity=9,
            ),
            ServantCapability(
                "quality_metrics",
                "品質メトリクス計算",
                ["source_code"],
                ["quality_metrics"],
                complexity=4,
            ),
        ]

        super().__init__(
            servant_id="D05",
            servant_name="BugHunter",
            specialization="バグ検出・修正",
            capabilities=capabilities,
        )

        # BugHunter固有の設定
        self.bug_patterns = self._initialize_bug_patterns()
        self.vulnerability_patterns = self._initialize_vulnerability_patterns()
        self.code_smell_patterns = self._initialize_code_smell_patterns()

        # 品質基準
        self.quality_thresholds = {
            "complexity_threshold": 15,
            "line_length_max": 100,
            "function_length_max": 50,
            "class_length_max": 500,
            "nesting_depth_max": 5,
        }

        # 検出エンジン
        self.syntax_analyzer = SyntaxAnalyzer()
        self.logic_analyzer = LogicAnalyzer()
        self.security_scanner = SecurityScanner()
        self.pattern_matcher = PatternMatcher()

        self.logger.info("BugHunter ready to hunt down bugs")

    def get_specialized_capabilities(self) -> List[ServantCapability]:
        """専門能力の取得"""
        return [
            ServantCapability(
                "regression_analysis",
                "回帰分析・テストケース生成",
                ["original_code", "modified_code"],
                ["regression_report"],
                complexity=7,
            ),
            ServantCapability(
                "performance_bug_detection",
                "パフォーマンスバグ検出",
                ["source_code", "profile_data"],
                ["performance_issues"],
                complexity=8,
            ),
            ServantCapability(
                "memory_leak_detection",
                "メモリリーク検出",
                ["source_code"],
                ["memory_issues"],
                complexity=8,
            ),
        ]

    async def execute_task(self, task: Dict[str, Any]) -> TaskResult:
        """タスク実行"""
        start_time = datetime.now()
        task_id = task.get("task_id", "unknown")
        task_type = task.get("task_type", "")

        try:
            self.logger.info(f"Hunting bugs for task {task_id}: {task_type}")

            result_data = {}
            payload = task.get("payload", {})

            if task_type == "static_analysis":
                result_data = await self._static_analysis(
                    payload.get("source_code", "")
                )
            elif task_type == "bug_detection":
                result_data = await self._bug_detection(
                    payload.get("source_code", ""), payload.get("test_cases", [])
                )
            elif task_type == "auto_fix_suggestion":
                result_data = await self._auto_fix_suggestion(
                    payload.get("source_code", ""), payload.get("bug_report", {})
                )
            elif task_type == "code_smell_detection":
                result_data = await self._code_smell_detection(
                    payload.get("source_code", "")
                )
            elif task_type == "vulnerability_scan":
                result_data = await self._vulnerability_scan(
                    payload.get("source_code", "")
                )
            elif task_type == "quality_metrics":
                result_data = await self._quality_metrics(
                    payload.get("source_code", "")
                )
            elif task_type == "regression_analysis":
                result_data = await self._regression_analysis(
                    payload.get("original_code", ""), payload.get("modified_code", "")
                )
            elif task_type == "performance_bug_detection":
                result_data = await self._performance_bug_detection(
                    payload.get("source_code", ""), payload.get("profile_data", {})
                )
            elif task_type == "memory_leak_detection":
                result_data = await self._memory_leak_detection(
                    payload.get("source_code", "")
                )
            else:
                raise ValueError(f"Unknown task type: {task_type}")

            # BugHunter品質検証
            quality_score = await self._validate_bug_hunting_quality(result_data)

            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            return TaskResult(
                task_id=task_id,
                servant_id=self.servant_id,
                status=TaskStatus.COMPLETED,
                result_data=result_data,
                execution_time_ms=execution_time,
                quality_score=quality_score,
            )

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Bug hunting failed for task {task_id}: {str(e)}")
            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            return TaskResult(
                task_id=task_id,
                servant_id=self.servant_id,
                status=TaskStatus.FAILED,
                error_message=str(e),
                execution_time_ms=execution_time,
                quality_score=0.0,
            )

    async def craft_artifact(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        """BugHunter専用の製作メソッド"""
        analysis_type = specification.get("type", "static_analysis")
        source_code = specification.get("source_code", "")

        if analysis_type == "comprehensive":
            # 包括的分析
            static_result = await self._static_analysis(source_code)
            bug_result = await self._bug_detection(source_code, [])
            smell_result = await self._code_smell_detection(source_code)

            return {
                "comprehensive_analysis": {
                    "static_analysis": static_result,
                    "bug_detection": bug_result,
                    "code_smells": smell_result,
                },
                "total_issues": (
                    len(static_result.get("issues", []))
                    + len(bug_result.get("bugs_found", []))
                    + len(smell_result.get("smells_detected", []))
                ),
            }
        elif analysis_type == "security":
            return await self._vulnerability_scan(source_code)
        else:
            return await self._static_analysis(source_code)

    async def _static_analysis(self, source_code: str) -> Dict[str, Any]:
        """静的コード解析"""
        if not source_code:
            raise ValueError("Source code is required for static analysis")

        try:
            # 構文解析
            tree = ast.parse(source_code)

            # 各種問題の検出
            issues = []

            # 構文エラー・問題の検出
            syntax_issues = self.syntax_analyzer.analyze(tree, source_code)
            issues.extend(syntax_issues)

            # ロジック問題の検出
            logic_issues = self.logic_analyzer.analyze(tree)
            issues.extend(logic_issues)

            # 品質問題の検出
            quality_issues = self._detect_quality_issues(tree, source_code)
            issues.extend(quality_issues)

            # 問題の重要度分類
            categorized_issues = self._categorize_issues(issues)

            return {
                "analysis_report": {
                    "total_issues": len(issues),
                    "critical_issues": len(categorized_issues["critical"]),
                    "major_issues": len(categorized_issues["major"]),
                    "minor_issues": len(categorized_issues["minor"]),
                    "issues_by_category": categorized_issues,
                },
                "issues": issues,
                "analysis_type": "static",
                "code_quality_score": self._calculate_quality_score(
                    issues, source_code
                ),
                "recommendations": self._generate_fix_recommendations(issues),
            }

        except SyntaxError as e:
            # Handle specific exception case
            return {
                "analysis_report": {"syntax_error": str(e)},
                "issues": [
                    {"type": "syntax_error", "message": str(e), "severity": "critical"}
                ],
                "analysis_type": "static",
                "code_quality_score": 0.0,
            }
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Static analysis failed: {e}")
            return {
                "analysis_report": {"error": str(e)},
                "issues": [],
                "analysis_type": "static",
                "code_quality_score": 0.0,
            }

    async def _bug_detection(
        self, source_code: str, test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """バグ検出・分類"""
        if not source_code:
            raise ValueError("Source code is required for bug detection")

        try:
            tree = ast.parse(source_code)

            bugs_found = []

            # 一般的なバグパターンの検出
            for pattern_name, pattern_info in self.bug_patterns.items():
                matches = self.pattern_matcher.find_pattern_matches(tree, pattern_info)
                for match in matches:
                    # Process each item in collection
                    bugs_found.append(
                        {
                            "bug_type": pattern_name,
                            "severity": pattern_info["severity"],
                            "line": match.get("line", 0),
                            "description": pattern_info["description"],
                            "fix_suggestion": pattern_info.get("fix_suggestion", ""),
                        }
                    )

            # ロジックエラーの検出
            logic_errors = self._detect_logic_errors(tree)
            bugs_found.extend(logic_errors)

            # テストケースベースの検証
            if test_cases:
                test_bugs = await self._validate_with_test_cases(
                    source_code, test_cases
                )
                bugs_found.extend(test_bugs)

            # バグの分類
            bug_categories = self._classify_bugs(bugs_found)

            return {
                "bug_report": {
                    "total_bugs": len(bugs_found),
                    "bug_categories": bug_categories,
                    "severity_distribution": self._get_severity_distribution(
                        bugs_found
                    ),
                },
                "bugs_found": bugs_found,
                "analysis_type": "bug_detection",
                "risk_level": self._calculate_risk_level(bugs_found),
                "fix_priority": self._prioritize_fixes(bugs_found),
            }

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Bug detection failed: {e}")
            return {
                "bug_report": {"error": str(e)},
                "bugs_found": [],
                "analysis_type": "bug_detection",
                "risk_level": "unknown",
            }

    async def _auto_fix_suggestion(
        self, source_code: str, bug_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """自動修正提案"""
        if not source_code or not bug_report:
            # Complex condition - consider breaking down
            return {
                "fix_suggestions": [],
                "analysis_type": "auto_fix",
                "fixes_available": 0,
            }

        try:
            bugs = bug_report.get("bugs_found", [])
            fix_suggestions = []

            for bug in bugs:
                # Process each item in collection
                bug_type = bug.get("bug_type", "")
                line = bug.get("line", 0)

                # 自動修正可能なバグの処理
                if bug_type in self._get_auto_fixable_bugs():
                    fix = self._generate_auto_fix(source_code, bug)
                    if fix:
                        fix_suggestions.append(fix)

            # 修正適用順序の最適化
            optimized_fixes = self._optimize_fix_order(fix_suggestions)

            return {
                "fix_suggestions": optimized_fixes,
                "analysis_type": "auto_fix",
                "fixes_available": len(optimized_fixes),
                "auto_fixable_count": len(
                    [f for f in optimized_fixes if f.get("auto_apply", False)]
                ),
                "manual_review_count": len(
                    [f for f in optimized_fixes if not f.get("auto_apply", False)]
                ),
            }

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Auto fix suggestion failed: {e}")
            return {
                "fix_suggestions": [],
                "error": str(e),
                "analysis_type": "auto_fix",
                "fixes_available": 0,
            }

    async def _code_smell_detection(self, source_code: str) -> Dict[str, Any]:
        """コードスメル検出"""
        if not source_code:
            raise ValueError("Source code is required for code smell detection")

        try:
            tree = ast.parse(source_code)

            smells_detected = []

            # 各種コードスメルの検出
            for smell_name, smell_pattern in self.code_smell_patterns.items():
                smell_instances = self._detect_code_smell(tree, smell_pattern)
                for instance in smell_instances:
                    # Process each item in collection
                    smells_detected.append(
                        {
                            "smell_type": smell_name,
                            "severity": smell_pattern["severity"],
                            "location": instance.get("location", ""),
                            "description": smell_pattern["description"],
                            "refactoring_suggestion": smell_pattern.get(
                                "refactoring", ""
                            ),
                        }
                    )

            # スメルの影響度計算
            impact_analysis = self._analyze_smell_impact(smells_detected)

            return {
                "smell_report": {
                    "total_smells": len(smells_detected),
                    "smell_types": list(set(s["smell_type"] for s in smells_detected)),
                    "impact_analysis": impact_analysis,
                },
                "smells_detected": smells_detected,
                "analysis_type": "code_smell",
                "maintainability_score": self._calculate_maintainability_score(
                    smells_detected
                ),
                "refactoring_priorities": self._prioritize_refactoring(smells_detected),
            }

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Code smell detection failed: {e}")
            return {
                "smell_report": {"error": str(e)},
                "smells_detected": [],
                "analysis_type": "code_smell",
                "maintainability_score": 0.0,
            }

    async def _vulnerability_scan(self, source_code: str) -> Dict[str, Any]:
        """脆弱性スキャン"""
        if not source_code:
            raise ValueError("Source code is required for vulnerability scan")

        try:
            tree = ast.parse(source_code)

            vulnerabilities = []

            # セキュリティパターンマッチング
            for vuln_name, vuln_pattern in self.vulnerability_patterns.items():
                matches = self.security_scanner.scan_for_vulnerability(
                    tree, vuln_pattern
                )
                for match in matches:
                    # Process each item in collection
                    vulnerabilities.append(
                        {
                            "vulnerability_type": vuln_name,
                            "severity": vuln_pattern["severity"],
                            "cwe_id": vuln_pattern.get("cwe_id", ""),
                            "location": match.get("location", ""),
                            "description": vuln_pattern["description"],
                            "mitigation": vuln_pattern.get("mitigation", ""),
                        }
                    )

            # リスク評価
            risk_assessment = self._assess_security_risk(vulnerabilities)

            return {
                "vulnerability_report": {
                    "total_vulnerabilities": len(vulnerabilities),
                    "critical_vulnerabilities": len(
                        [v for v in vulnerabilities if v["severity"] == "critical"]
                    ),
                    "high_vulnerabilities": len(
                        [v for v in vulnerabilities if v["severity"] == "high"]
                    ),
                    "risk_assessment": risk_assessment,
                },
                "vulnerabilities": vulnerabilities,
                "analysis_type": "vulnerability_scan",
                "security_score": self._calculate_security_score(vulnerabilities),
                "remediation_plan": self._create_remediation_plan(vulnerabilities),
            }

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Vulnerability scan failed: {e}")
            return {
                "vulnerability_report": {"error": str(e)},
                "vulnerabilities": [],
                "analysis_type": "vulnerability_scan",
                "security_score": 0.0,
            }

    async def _quality_metrics(self, source_code: str) -> Dict[str, Any]:
        """品質メトリクス計算"""
        if not source_code:
            raise ValueError("Source code is required for quality metrics")

        try:
            tree = ast.parse(source_code)
            lines = source_code.splitlines()

            # 基本メトリクス
            metrics = {
                "lines_of_code": len(lines),
                "logical_lines": len(
                    [
                        line
                        for line in lines
                        if line.strip() and not line.strip().startswith("#")
                    ]
                ),
                "comment_lines": len(
                    [line for line in lines if line.strip().startswith("#")]
                ),
                "blank_lines": len([line for line in lines if not line.strip()]),
                "functions": len(
                    [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                ),
                "classes": len(
                    [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
                ),
                "complexity": self._calculate_cyclomatic_complexity(tree),
                "maintainability_index": self._calculate_maintainability_index(
                    tree, source_code
                ),
            }

            # 品質指標
            quality_indicators = {
                "comment_ratio": metrics["comment_lines"]
                / max(metrics["lines_of_code"], 1),
                "function_complexity_avg": metrics["complexity"]
                / max(metrics["functions"], 1),
                "class_size_avg": (
                    metrics["logical_lines"] / max(metrics["classes"], 1)
                    if metrics["classes"] > 0
                    else 0
                ),
            }

            # 総合品質スコア
            overall_quality = self._calculate_overall_quality(
                metrics, quality_indicators
            )

            return {
                "quality_metrics": metrics,
                "quality_indicators": quality_indicators,
                "overall_quality_score": overall_quality,
                "analysis_type": "quality_metrics",
                "recommendations": self._generate_quality_recommendations(
                    metrics, quality_indicators
                ),
            }

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Quality metrics calculation failed: {e}")
            return {
                "quality_metrics": {},
                "error": str(e),
                "analysis_type": "quality_metrics",
                "overall_quality_score": 0.0,
            }

    async def _validate_bug_hunting_quality(self, result_data: Dict[str, Any]) -> float:
        """バグハンティング品質検証"""
        quality_score = await self.validate_crafting_quality(result_data)

        try:
            # 検出した問題数による加点
            issues_found = (
                len(result_data.get("issues", []))
                + len(result_data.get("bugs_found", []))
                + len(result_data.get("vulnerabilities", []))
            )
            quality_score += min(20.0, issues_found * 2.0)

            # 品質スコアによる加点
            code_quality = result_data.get("code_quality_score", 0)
            security_score = result_data.get("security_score", 0)
            overall_quality = result_data.get("overall_quality_score", 0)

            best_score = max(code_quality, security_score, overall_quality)
            quality_score += best_score * 0.2

            # 修正提案がある場合の加点
            if result_data.get("fix_suggestions") or result_data.get("recommendations"):
                # Complex condition - consider breaking down
                quality_score += 15.0

            # エラーなしボーナス
            if "error" not in result_data:
                quality_score += 10.0

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Bug hunting quality validation error: {e}")
            quality_score = max(quality_score - 10.0, 0.0)

        return min(quality_score, 100.0)

    # ヘルパーメソッドとクラス
    def _initialize_bug_patterns(self) -> Dict[str, Dict[str, Any]]:
        """バグパターン初期化"""
        return {
            "null_pointer": {
                "description": "Potential null pointer access",
                "severity": "high",
                "fix_suggestion": "Add null check before access",
            },
            "infinite_loop": {
                "description": "Potential infinite loop",
                "severity": "critical",
                "fix_suggestion": "Add proper loop termination condition",
            },
            "resource_leak": {
                "description": "Resource not properly closed",
                "severity": "medium",
                "fix_suggestion": "Use context manager or explicit close()",
            },
            "unused_variable": {
                "description": "Variable defined but not used",
                "severity": "low",
                "fix_suggestion": "Remove unused variable or add underscore prefix",
            },
        }

    def _initialize_vulnerability_patterns(self) -> Dict[str, Dict[str, Any]]:
        """脆弱性パターン初期化"""
        return {
            "sql_injection": {
                "description": "Potential SQL injection vulnerability",
                "severity": "critical",
                "cwe_id": "CWE-89",
                "mitigation": "Use parameterized queries",
            },
            "command_injection": {
                "description": "Potential command injection vulnerability",
                "severity": "critical",
                "cwe_id": "CWE-78",
                "mitigation": "Validate and sanitize input",
            },
            "path_traversal": {
                "description": "Potential path traversal vulnerability",
                "severity": "high",
                "cwe_id": "CWE-22",
                "mitigation": "Validate file paths and use safe path operations",
            },
        }

    def _initialize_code_smell_patterns(self) -> Dict[str, Dict[str, Any]]:
        """コードスメルパターン初期化"""
        return {
            "long_method": {
                "description": "Method is too long",
                "severity": "medium",
                "refactoring": "Extract smaller methods",
            },
            "large_class": {
                "description": "Class has too many responsibilities",
                "severity": "medium",
                "refactoring": "Split class into smaller classes",
            },
            "duplicate_code": {
                "description": "Duplicate code detected",
                "severity": "low",
                "refactoring": "Extract common functionality",
            },
        }


class SyntaxAnalyzer:
    """構文分析器"""

    def analyze(self, tree: ast.AST, source_code: str) -> List[Dict[str, Any]]:
        """構文分析実行"""
        issues = []

        # 長すぎる行の検出
        lines = source_code.splitlines()
        for i, line in enumerate(lines, 1):
            if len(line) > 100:
                issues.append(
                    {
                        "type": "line_too_long",
                        "line": i,
                        "severity": "low",
                        "message": f"Line {i} is too long ({len(line)} characters)",
                    }
                )

        return issues


class LogicAnalyzer:
    """ロジック分析器"""

    def analyze(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """ロジック分析実行"""
        issues = []

        # 到達不可能コードの検出
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if self._has_unreachable_code(node):
                    issues.append(
                        {
                            "type": "unreachable_code",
                            "line": getattr(node, "lineno", 0),
                            "severity": "medium",
                            "message": f"Function '{node.name}' contains unreachable code",
                        }
                    )

        return issues

    def _has_unreachable_code(self, func_node: ast.FunctionDef) -> bool:
        """到達不可能コード検出"""
        # 簡易実装: return文の後にコードがあるかチェック
        for i, stmt in enumerate(func_node.body[:-1]):
            if isinstance(stmt, ast.Return):
                return True
        return False


class SecurityScanner:
    """セキュリティスキャナー"""

    def scan_for_vulnerability(
        self, tree: ast.AST, pattern: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """脆弱性スキャン実行"""
        matches = []

        # 簡易実装: 危険な関数呼び出しの検出
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                # Complex condition - consider breaking down
                if node.func.id in ["eval", "exec", "compile"]:
                    matches.append(
                        {
                            "location": f"line {getattr(node, 'lineno', 0)}",
                            "function": node.func.id,
                        }
                    )

        return matches


class PatternMatcher:
    """パターンマッチャー"""

    def find_pattern_matches(
        self, tree: ast.AST, pattern: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """パターンマッチング実行"""
        matches = []

        # 簡易実装: 基本的なパターンマッチング
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and not hasattr(node.ctx, "__class__"):
                # Complex condition - consider breaking down
                matches.append({"line": getattr(node, "lineno", 0), "name": node.id})

        return matches
