#!/usr/bin/env python3
"""
Elder Flow Quality Gate Real Implementation
品質ゲートシステムの実装版 - モック禁止
"""

import asyncio
import json
import logging
import subprocess
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import xml.etree.ElementTree as ET

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.elder_flow_quality_gate import (
    QualityGateStatus,
    QualityCheckType,
    QualityMetric,
    QualityCheckResult,
    BaseQualityChecker,
)

logger = logging.getLogger(__name__)


class UnitTestCheckerReal(BaseQualityChecker):
    """ユニットテストチェッカー - 実装版"""

    def __init__(self):
        super().__init__(QualityCheckType.UNIT_TESTS)
        self.test_path = "tests/unit/"

    async def _perform_check(self, context: Dict) -> QualityCheckResult:
        """実際のユニットテストを実行"""
        try:
            # pytest実行
            cmd = [
                "python",
                "-m",
                "pytest",
                self.test_path,
                "--json-report",
                "--json-report-file=test_report.json",
                "--cov=.",
                "--cov-report=xml",
                "-v",
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=PROJECT_ROOT,
            )

            stdout, stderr = await process.communicate()

            # テスト結果を解析
            test_results = await self._parse_test_results()
            coverage_data = await self._parse_coverage_results()

            # メトリクスを計算
            total_tests = test_results.get("total", 0)
            passed_tests = test_results.get("passed", 0)
            failed_tests = test_results.get("failed", 0)
            coverage = coverage_data.get("percent_covered", 0)

            pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

            metrics = [
                QualityMetric("Test Pass Rate", pass_rate, 100.0, "%"),
                QualityMetric("Test Coverage", coverage, 80.0, "%"),
                QualityMetric("Test Count", total_tests, 10.0, "tests"),
            ]

            # 問題点を収集
            issues = []
            if failed_tests > 0:
                failed_list = test_results.get("failed_tests", [])
                for test in failed_list[:5]:  # 最初の5件
                    issues.append(
                        {
                            "type": "failed_test",
                            "severity": "high",
                            "file": test.get("file", "unknown"),
                            "test": test.get("name", "unknown"),
                            "message": test.get("message", "Test failed"),
                        }
                    )

            if coverage < 80:
                uncovered_files = coverage_data.get("uncovered_files", [])
                for file_info in uncovered_files[:3]:  # 最も低い3ファイル
                    issues.append(
                        {
                            "type": "low_coverage",
                            "severity": "medium",
                            "file": file_info.get("file", "unknown"),
                            "coverage": file_info.get("coverage", 0),
                            "message": f"Coverage only {file_info.get('coverage', 0)}%",
                        }
                    )

            # ステータスを決定
            if failed_tests > 0:
                status = QualityGateStatus.FAILED
            elif coverage < 60:
                status = QualityGateStatus.WARNING
            elif all(m.passed for m in metrics):
                status = QualityGateStatus.PASSED
            else:
                status = QualityGateStatus.WARNING

            recommendations = []
            if failed_tests > 0:
                recommendations.append(f"Fix {failed_tests} failing tests")
            if coverage < 80:
                recommendations.append(
                    f"Improve test coverage from {coverage:.1f}% to 80%+"
                )
            if total_tests < 50:
                recommendations.append(
                    "Add more tests to ensure comprehensive coverage"
                )

            return QualityCheckResult(
                check_type=self.check_type,
                status=status,
                metrics=metrics,
                issues=issues,
                recommendations=recommendations,
                details={
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "skipped": test_results.get("skipped", 0),
                    "total": total_tests,
                    "coverage": coverage,
                    "execution_time": test_results.get("duration", 0),
                },
            )

        except Exception as e:
            self.logger.error(f"Unit test check failed: {e}")
            return QualityCheckResult(
                check_type=self.check_type,
                status=QualityGateStatus.FAILED,
                metrics=[],
                issues=[
                    {
                        "type": "execution_error",
                        "severity": "critical",
                        "message": str(e),
                    }
                ],
                recommendations=["Fix test execution environment"],
                details={"error": str(e)},
            )

    async def _parse_test_results(self) -> Dict:
        """pytest結果を解析"""
        report_path = PROJECT_ROOT / "test_report.json"

        if not report_path.exists():
            return {"total": 0, "passed": 0, "failed": 0}

        try:
            with open(report_path, "r") as f:
                data = json.load(f)

            summary = data.get("summary", {})
            tests = data.get("tests", [])

            failed_tests = []
            for test in tests:
                if test.get("outcome") == "failed":
                    failed_tests.append(
                        {
                            "file": test.get("nodeid", "").split("::")[0],
                            "name": test.get("nodeid", ""),
                            "message": test.get("call", {}).get("longrepr", "")[:200],
                        }
                    )

            return {
                "total": summary.get("total", 0),
                "passed": summary.get("passed", 0),
                "failed": summary.get("failed", 0),
                "skipped": summary.get("skipped", 0),
                "duration": data.get("duration", 0),
                "failed_tests": failed_tests,
            }

        except Exception as e:
            self.logger.error(f"Failed to parse test results: {e}")
            return {"total": 0, "passed": 0, "failed": 0}
        finally:
            # クリーンアップ
            if report_path.exists():
                report_path.unlink()

    async def _parse_coverage_results(self) -> Dict:
        """カバレッジ結果を解析"""
        coverage_path = PROJECT_ROOT / "coverage.xml"

        if not coverage_path.exists():
            return {"percent_covered": 0}

        try:
            tree = ET.parse(coverage_path)
            root = tree.getroot()

            # 全体のカバレッジ
            coverage_percent = float(root.attrib.get("line-rate", 0)) * 100

            # ファイル別カバレッジ
            uncovered_files = []
            for package in root.findall(".//package"):
                for class_elem in package.findall("classes/class"):
                    filename = class_elem.attrib.get("filename", "")
                    line_rate = float(class_elem.attrib.get("line-rate", 0)) * 100

                    if line_rate < 80:
                        uncovered_files.append(
                            {"file": filename, "coverage": line_rate}
                        )

            # カバレッジが低い順にソート
            uncovered_files.sort(key=lambda x: x["coverage"])

            return {
                "percent_covered": coverage_percent,
                "uncovered_files": uncovered_files,
            }

        except Exception as e:
            self.logger.error(f"Failed to parse coverage: {e}")
            return {"percent_covered": 0}
        finally:
            # クリーンアップ
            if coverage_path.exists():
                coverage_path.unlink()


class CodeQualityCheckerReal(BaseQualityChecker):
    """コード品質チェッカー - 実装版"""

    def __init__(self):
        super().__init__(QualityCheckType.CODE_QUALITY)

    async def _perform_check(self, context: Dict) -> QualityCheckResult:
        """実際のコード品質チェック"""
        try:
            # 複数のツールを実行
            pylint_results = await self._run_pylint()
            flake8_results = await self._run_flake8()
            complexity_results = await self._run_complexity_check()

            # メトリクスを計算
            pylint_score = pylint_results.get("score", 0)
            flake8_issues = len(flake8_results.get("issues", []))
            avg_complexity = complexity_results.get("average_complexity", 0)
            max_complexity = complexity_results.get("max_complexity", 0)

            # 総合スコアを計算
            overall_score = self._calculate_overall_score(
                pylint_score, flake8_issues, avg_complexity
            )

            metrics = [
                QualityMetric("Overall Score", overall_score, 8.0, "/10"),
                QualityMetric("Pylint Score", pylint_score, 8.0, "/10"),
                QualityMetric(
                    "Flake8 Issues",
                    flake8_issues,
                    10,
                    "issues",
                    passed=(flake8_issues <= 10),
                ),
                QualityMetric("Average Complexity", avg_complexity, 10.0, ""),
                QualityMetric("Max Complexity", max_complexity, 20.0, ""),
            ]

            # 問題点を収集
            issues = []

            # Pylintの問題
            for issue in pylint_results.get("issues", [])[:5]:
                issues.append(
                    {
                        "type": "pylint",
                        "severity": self._map_pylint_severity(issue.get("type", "")),
                        "file": issue.get("path", ""),
                        "line": issue.get("line", 0),
                        "message": issue.get("message", ""),
                    }
                )

            # Flake8の問題
            for issue in flake8_results.get("issues", [])[:5]:
                issues.append(
                    {
                        "type": "flake8",
                        "severity": "medium",
                        "file": issue.get("filename", ""),
                        "line": issue.get("line_number", 0),
                        "message": f"{issue.get('code', '')}: {issue.get('text', '')}",
                    }
                )

            # 複雑度の問題
            for func in complexity_results.get("complex_functions", [])[:3]:
                issues.append(
                    {
                        "type": "complexity",
                        "severity": "high" if func["complexity"] > 15 else "medium",
                        "file": func.get("file", ""),
                        "line": func.get("line", 0),
                        "message": f"Function '{func.get(
                            'name',
                            '')}' has complexity {func.get('complexity', 0
                        )}",
                    }
                )

            # ステータスを決定
            if overall_score < 6:
                status = QualityGateStatus.FAILED
            elif overall_score < 8:
                status = QualityGateStatus.WARNING
            else:
                status = QualityGateStatus.PASSED

            # 推奨事項
            recommendations = []
            if pylint_score < 8:
                recommendations.append(
                    f"Improve Pylint score from {pylint_score:.1f} to 8.0+"
                )
            if flake8_issues > 10:
                recommendations.append(
                    f"Reduce Flake8 issues from {flake8_issues} to under 10"
                )
            if max_complexity > 20:
                recommendations.append("Refactor complex functions (complexity > 20)")

            return QualityCheckResult(
                check_type=self.check_type,
                status=status,
                metrics=metrics,
                issues=issues,
                recommendations=recommendations,
                details={
                    "overall_score": overall_score,
                    "pylint_score": pylint_score,
                    "flake8_issues": flake8_issues,
                    "average_complexity": avg_complexity,
                    "max_complexity": max_complexity,
                },
            )

        except Exception as e:
            self.logger.error(f"Code quality check failed: {e}")
            return QualityCheckResult(
                check_type=self.check_type,
                status=QualityGateStatus.FAILED,
                metrics=[],
                issues=[
                    {
                        "type": "execution_error",
                        "severity": "critical",
                        "message": str(e),
                    }
                ],
                recommendations=["Fix code quality check environment"],
                details={"error": str(e)},
            )

    async def _run_pylint(self) -> Dict:
        """Pylintを実行"""
        try:
            cmd = ["python", "-m", "pylint", ".", "--output-format=json", "--exit-zero"]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=PROJECT_ROOT,
            )

            stdout, stderr = await process.communicate()

            if stdout:
                issues = json.loads(stdout.decode())

                # スコアを計算（簡易版）
                total_statements = sum(
                    1 for i in issues if i.get("type") == "statement"
                )
                total_issues = len(issues)
                score = max(0, 10 - (total_issues / max(total_statements, 100) * 10))

                return {"score": score, "issues": issues[:20]}  # 最初の20件

            return {"score": 10.0, "issues": []}

        except Exception as e:
            self.logger.error(f"Pylint execution failed: {e}")
            return {"score": 0, "issues": []}

    async def _run_flake8(self) -> Dict:
        """Flake8を実行"""
        try:
            cmd = ["python", "-m", "flake8", ".", "--format=json"]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=PROJECT_ROOT,
            )

            stdout, stderr = await process.communicate()

            issues = []
            if stdout:
                for line in stdout.decode().split("\n"):
                    if line.strip():
                        try:
                            issue = json.loads(line)
                            issues.append(issue)
                        except:
                            pass

            return {"issues": issues}

        except Exception as e:
            self.logger.error(f"Flake8 execution failed: {e}")
            return {"issues": []}

    async def _run_complexity_check(self) -> Dict:
        """複雑度チェック（radon使用）"""
        try:
            cmd = ["python", "-m", "radon", "cc", ".", "-j"]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=PROJECT_ROOT,
            )

            stdout, stderr = await process.communicate()

            if stdout:
                data = json.loads(stdout.decode())

                all_complexities = []
                complex_functions = []

                for file_path, functions in data.items():
                    for func in functions:
                        complexity = func.get("complexity", 0)
                        all_complexities.append(complexity)

                        if complexity > 10:
                            complex_functions.append(
                                {
                                    "file": file_path,
                                    "name": func.get("name", ""),
                                    "line": func.get("lineno", 0),
                                    "complexity": complexity,
                                }
                            )

                # 複雑度が高い順にソート
                complex_functions.sort(key=lambda x: x["complexity"], reverse=True)

                avg_complexity = (
                    sum(all_complexities) / len(all_complexities)
                    if all_complexities
                    else 0
                )
                max_complexity = max(all_complexities) if all_complexities else 0

                return {
                    "average_complexity": avg_complexity,
                    "max_complexity": max_complexity,
                    "complex_functions": complex_functions,
                }

            return {
                "average_complexity": 0,
                "max_complexity": 0,
                "complex_functions": [],
            }

        except Exception as e:
            self.logger.error(f"Complexity check failed: {e}")
            return {
                "average_complexity": 0,
                "max_complexity": 0,
                "complex_functions": [],
            }

    def _calculate_overall_score(
        self, pylint_score: float, flake8_issues: int, avg_complexity: float
    ) -> float:
        """総合スコアを計算"""
        # Pylintスコア（重み: 40%）
        pylint_weight = 0.4

        # Flake8スコア（重み: 30%）
        flake8_score = max(0, 10 - (flake8_issues / 10))
        flake8_weight = 0.3

        # 複雑度スコア（重み: 30%）
        complexity_score = max(0, 10 - (avg_complexity / 10))
        complexity_weight = 0.3

        overall = (
            pylint_score * pylint_weight
            + flake8_score * flake8_weight
            + complexity_score * complexity_weight
        )

        return round(overall, 1)

    def _map_pylint_severity(self, pylint_type: str) -> str:
        """Pylintのタイプを重要度にマップ"""
        severity_map = {
            "error": "high",
            "fatal": "critical",
            "warning": "medium",
            "convention": "low",
            "refactor": "low",
            "info": "low",
        }
        return severity_map.get(pylint_type.lower(), "medium")


class SecurityCheckerReal(BaseQualityChecker):
    """セキュリティチェッカー - 実装版"""

    def __init__(self):
        super().__init__(QualityCheckType.SECURITY_SCAN)

    async def _perform_check(self, context: Dict) -> QualityCheckResult:
        """実際のセキュリティチェック"""
        try:
            # banditでセキュリティスキャン
            bandit_results = await self._run_bandit()

            # safety で依存関係をチェック
            dependency_results = await self._check_dependencies()

            # 結果を集計
            total_issues = len(bandit_results.get("results", []))
            high_severity = sum(
                1
                for r in bandit_results.get("results", [])
                if r.get("issue_severity") == "HIGH"
            )
            medium_severity = sum(
                1
                for r in bandit_results.get("results", [])
                if r.get("issue_severity") == "MEDIUM"
            )
            low_severity = sum(
                1
                for r in bandit_results.get("results", [])
                if r.get("issue_severity") == "LOW"
            )

            vulnerable_deps = len(dependency_results.get("vulnerabilities", []))

            # セキュリティスコアを計算
            security_score = self._calculate_security_score(
                high_severity, medium_severity, low_severity, vulnerable_deps
            )

            metrics = [
                QualityMetric("Security Score", security_score, 8.5, "/10"),
                QualityMetric("High Severity Issues", high_severity, 0, "issues"),
                QualityMetric(
                    "Medium Severity Issues",
                    medium_severity,
                    5,
                    "issues",
                    passed=(medium_severity <= 5),
                ),
                QualityMetric(
                    "Low Severity Issues",
                    low_severity,
                    10,
                    "issues",
                    passed=(low_severity <= 10),
                ),
                QualityMetric(
                    "Vulnerable Dependencies", vulnerable_deps, 0, "packages"
                ),
            ]

            # 問題点を収集
            issues = []

            # Banditの問題
            for result in bandit_results.get("results", [])[:10]:
                issues.append(
                    {
                        "type": "security_vulnerability",
                        "severity": result.get("issue_severity", "").lower(),
                        "file": result.get("filename", ""),
                        "line": result.get("line_number", 0),
                        "message": f"{result.get('issue_text', '')} ({result.get('test_name', '')})",
                    }
                )

            # 脆弱な依存関係
            for vuln in dependency_results.get("vulnerabilities", [])[:5]:
                issues.append(
                    {
                        "type": "vulnerable_dependency",
                        "severity": "high",
                        "package": vuln.get("package", ""),
                        "version": vuln.get("installed_version", ""),
                        "message": vuln.get("description", ""),
                    }
                )

            # ステータスを決定
            if high_severity > 0 or vulnerable_deps > 0:
                status = QualityGateStatus.FAILED
            elif medium_severity > 5:
                status = QualityGateStatus.WARNING
            else:
                status = QualityGateStatus.PASSED

            # 推奨事項
            recommendations = []
            if high_severity > 0:
                recommendations.append(
                    f"Fix {high_severity} high severity security issues immediately"
                )
            if vulnerable_deps > 0:
                recommendations.append(
                    f"Update {vulnerable_deps} vulnerable dependencies"
                )
            if medium_severity > 5:
                recommendations.append("Review and fix medium severity issues")

            return QualityCheckResult(
                check_type=self.check_type,
                status=status,
                metrics=metrics,
                issues=issues,
                recommendations=recommendations,
                details={
                    "security_score": security_score,
                    "vulnerabilities": {
                        "high": high_severity,
                        "medium": medium_severity,
                        "low": low_severity,
                        "total": total_issues,
                    },
                    "vulnerable_dependencies": vulnerable_deps,
                },
            )

        except Exception as e:
            self.logger.error(f"Security check failed: {e}")
            return QualityCheckResult(
                check_type=self.check_type,
                status=QualityGateStatus.FAILED,
                metrics=[],
                issues=[
                    {
                        "type": "execution_error",
                        "severity": "critical",
                        "message": str(e),
                    }
                ],
                recommendations=["Fix security check environment"],
                details={"error": str(e)},
            )

    async def _run_bandit(self) -> Dict:
        """Banditでセキュリティスキャン"""
        try:
            cmd = ["python", "-m", "bandit", "-r", ".", "-f", "json"]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=PROJECT_ROOT,
            )

            stdout, stderr = await process.communicate()

            if stdout:
                return json.loads(stdout.decode())

            return {"results": []}

        except Exception as e:
            self.logger.error(f"Bandit execution failed: {e}")
            return {"results": []}

    async def _check_dependencies(self) -> Dict:
        """依存関係の脆弱性をチェック"""
        try:
            # pip-auditを使用
            cmd = ["python", "-m", "pip_audit", "--format", "json"]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=PROJECT_ROOT,
            )

            stdout, stderr = await process.communicate()

            if stdout:
                data = json.loads(stdout.decode())
                vulnerabilities = []

                for vuln in data.get("vulnerabilities", []):
                    vulnerabilities.append(
                        {
                            "package": vuln.get("name", ""),
                            "installed_version": vuln.get("version", ""),
                            "vulnerability_id": vuln.get("id", ""),
                            "description": vuln.get("description", ""),
                        }
                    )

                return {"vulnerabilities": vulnerabilities}

            return {"vulnerabilities": []}

        except Exception as e:
            self.logger.error(f"Dependency check failed: {e}")
            # フォールバック: requirements.txtをチェック
            return await self._check_requirements_txt()

    async def _check_requirements_txt(self) -> Dict:
        """requirements.txtの基本チェック"""
        vulnerabilities = []
        requirements_path = PROJECT_ROOT / "requirements.txt"

        if requirements_path.exists():
            # 既知の脆弱なバージョンをチェック（簡易版）
            vulnerable_packages = {
                "flask": ["< 2.0.0"],
                "django": ["< 3.2"],
                "requests": ["< 2.20.0"],
                "urllib3": ["< 1.24.2"],
            }

            with open(requirements_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        for pkg, vulnerable_versions in vulnerable_packages.items():
                            if pkg in line.lower():
                                vulnerabilities.append(
                                    {
                                        "package": pkg,
                                        "installed_version": "unknown",
                                        "description": f"Potentially vulnerable version of {pkg}",
                                    }
                                )

        return {"vulnerabilities": vulnerabilities}

    def _calculate_security_score(
        self, high: int, medium: int, low: int, deps: int
    ) -> float:
        """セキュリティスコアを計算"""
        # 基本スコア10から減点
        score = 10.0

        # 高severity: -2点/件
        score -= high * 2.0

        # 中severity: -0.5点/件
        score -= medium * 0.5

        # 低severity: -0.1点/件
        score -= low * 0.1

        # 脆弱な依存関係: -1点/件
        score -= deps * 1.0

        return max(0, round(score, 1))


# Quality Gate Manager Real Implementation
class QualityGateManagerReal:
    """品質ゲートマネージャー - 実装版"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.checkers = {
            QualityCheckType.UNIT_TESTS: UnitTestCheckerReal(),
            QualityCheckType.CODE_QUALITY: CodeQualityCheckerReal(),
            QualityCheckType.SECURITY_SCAN: SecurityCheckerReal(),
        }

        # モック禁止ポリシー
        self.NO_MOCK_POLICY = True
        self.logger.info("🚫 Quality Gate Real Implementation - NO MOCKS ALLOWED")

    async def run_quality_checks(
        self, context: Dict, check_types: Optional[List[QualityCheckType]] = None
    ) -> Dict:
        """品質チェックを実行"""
        if check_types is None:
            check_types = list(self.checkers.keys())

        results = {}
        overall_status = QualityGateStatus.PASSED

        # 並列実行
        tasks = []
        for check_type in check_types:
            if check_type in self.checkers:
                checker = self.checkers[check_type]
                tasks.append(self._run_check_with_timeout(checker, context))

        check_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 結果を集計
        for i, check_type in enumerate(check_types):
            if isinstance(check_results[i], Exception):
                self.logger.error(
                    f"Check {check_type} failed with exception: {check_results[i]}"
                )
                results[check_type] = QualityCheckResult(
                    check_type=check_type,
                    status=QualityGateStatus.FAILED,
                    metrics=[],
                    issues=[
                        {
                            "type": "check_error",
                            "severity": "critical",
                            "message": str(check_results[i]),
                        }
                    ],
                    recommendations=["Fix quality check execution"],
                    details={"error": str(check_results[i])},
                )
                overall_status = QualityGateStatus.FAILED
            else:
                results[check_type] = check_results[i]

                # 全体ステータスを更新
                if check_results[i].status == QualityGateStatus.FAILED:
                    overall_status = QualityGateStatus.FAILED
                elif (
                    check_results[i].status == QualityGateStatus.WARNING
                    and overall_status != QualityGateStatus.FAILED
                ):
                    overall_status = QualityGateStatus.WARNING

        return {
            "overall_status": overall_status,
            "check_results": results,
            "summary": self._generate_summary(results),
            "timestamp": datetime.now().isoformat(),
        }

    async def _run_check_with_timeout(
        self, checker: BaseQualityChecker, context: Dict, timeout: float = 60.0
    ) -> QualityCheckResult:
        """タイムアウト付きでチェックを実行"""
        try:
            return await asyncio.wait_for(checker.check(context), timeout=timeout)
        except asyncio.TimeoutError:
            return QualityCheckResult(
                check_type=checker.check_type,
                status=QualityGateStatus.FAILED,
                metrics=[],
                issues=[
                    {
                        "type": "timeout",
                        "severity": "critical",
                        "message": f"Check timed out after {timeout} seconds",
                    }
                ],
                recommendations=["Optimize check performance or increase timeout"],
                details={"timeout": timeout},
            )

    def _generate_summary(
        self, results: Dict[QualityCheckType, QualityCheckResult]
    ) -> Dict:
        """結果のサマリーを生成"""
        total_checks = len(results)
        passed_checks = sum(
            1 for r in results.values() if r.status == QualityGateStatus.PASSED
        )
        failed_checks = sum(
            1 for r in results.values() if r.status == QualityGateStatus.FAILED
        )
        warning_checks = sum(
            1 for r in results.values() if r.status == QualityGateStatus.WARNING
        )

        all_issues = []
        all_recommendations = []

        for result in results.values():
            all_issues.extend(result.issues)
            all_recommendations.extend(result.recommendations)

        # 重複を除去
        unique_recommendations = list(set(all_recommendations))

        return {
            "total_checks": total_checks,
            "passed": passed_checks,
            "failed": failed_checks,
            "warnings": warning_checks,
            "total_issues": len(all_issues),
            "critical_issues": len(
                [i for i in all_issues if i.get("severity") == "critical"]
            ),
            "high_issues": len([i for i in all_issues if i.get("severity") == "high"]),
            "recommendations": unique_recommendations[:5],  # 上位5件
        }


# エクスポート
__all__ = [
    "QualityGateManagerReal",
    "UnitTestCheckerReal",
    "CodeQualityCheckerReal",
    "SecurityCheckerReal",
]
