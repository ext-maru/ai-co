#!/usr/bin/env python3
"""
Ancient Elder 5人順次監査システム
Iron Will基準による超厳格監査・テスト実行
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from governance.iron_will_execution_system import IronWillExecutionSystem

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/ancient_elder_sequential_audit.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class AncientElderAuditor:
    """Ancient Elder監査官クラス"""

    def __init__(self, elder_id: int, specialization: str):
        self.elder_id = elder_id
        self.specialization = specialization
        self.name = f"Ancient Elder #{elder_id} ({specialization})"
        self.iron_will = IronWillExecutionSystem()

        # 専門分野別の監査基準
        self.audit_criteria = self._get_specialized_criteria()

        logger.info(f"🏛️ {self.name} initialized")

    def _get_specialized_criteria(self) -> Dict[str, Any]:
        """専門分野別の監査基準を取得"""
        criteria_map = {
            "API_COMPLETENESS": {
                "focus": ["api_coverage", "implementation_quality", "documentation"],
                "threshold": 0.80,
                "weight": 1.2,
            },
            "ERROR_HANDLING": {
                "focus": ["error_coverage", "retry_mechanism", "recovery_actions"],
                "threshold": 0.90,
                "weight": 1.3,
            },
            "SECURITY": {
                "focus": ["authentication", "authorization", "data_protection"],
                "threshold": 0.95,
                "weight": 1.5,
            },
            "PERFORMANCE": {
                "focus": ["response_time", "throughput", "resource_usage"],
                "threshold": 0.85,
                "weight": 1.1,
            },
            "TEST_COVERAGE": {
                "focus": ["unit_tests", "integration_tests", "edge_cases"],
                "threshold": 0.95,
                "weight": 1.4,
            },
        }

        return criteria_map.get(
            self.specialization,
            {"focus": ["general"], "threshold": 0.90, "weight": 1.0},
        )

    def audit_implementation(self, target_path: str) -> Dict[str, Any]:
        """実装を監査"""
        start_time = time.time()

        audit_result = {
            "elder_id": self.elder_id,
            "elder_name": self.name,
            "specialization": self.specialization,
            "timestamp": datetime.now().isoformat(),
            "target": target_path,
            "findings": [],
            "metrics": {},
            "verdict": None,
            "recommendations": [],
        }

        try:
            logger.info(f"🔍 {self.name} beginning audit of {target_path}")

            # ファイル分析
            files_analyzed = self._analyze_files(target_path)
            audit_result["files_analyzed"] = len(files_analyzed)
            logger.info(f"📁 {self.name} analyzed {len(files_analyzed)} files")

            # 専門分野に応じた監査実施
            if self.specialization == "API_COMPLETENESS":
                findings = self._audit_api_completeness(files_analyzed)
            elif self.specialization == "ERROR_HANDLING":
                findings = self._audit_error_handling(files_analyzed)
            elif self.specialization == "SECURITY":
                findings = self._audit_security(files_analyzed)
            elif self.specialization == "PERFORMANCE":
                findings = self._audit_performance(files_analyzed)
            elif self.specialization == "TEST_COVERAGE":
                findings = self._audit_test_coverage(files_analyzed)
            else:
                findings = self._audit_general(files_analyzed)

            audit_result["findings"] = findings

            # メトリクス計算
            metrics = self._calculate_metrics(findings)
            audit_result["metrics"] = metrics

            # 判定
            verdict = self._make_verdict(metrics)
            audit_result["verdict"] = verdict

            # 推奨事項
            recommendations = self._generate_recommendations(findings, metrics)
            audit_result["recommendations"] = recommendations

            # Iron Will準拠チェック
            iron_will_compliance = self._check_iron_will_compliance(metrics)
            audit_result["iron_will_compliance"] = iron_will_compliance

            logger.info(
                f"✅ {self.name} completed audit - Verdict: {verdict}, Score: {metrics.get('weighted_score', 0):.2%}"
            )

        except Exception as e:
            logger.error(f"❌ {self.name} audit failed: {e}")
            audit_result["error"] = str(e)
            audit_result["verdict"] = "ERROR"

        finally:
            audit_result["execution_time"] = time.time() - start_time

        return audit_result

    def _analyze_files(self, target_path: str) -> List[Dict[str, Any]]:
        """ファイルを分析"""
        files = []
        path = Path(target_path)

        if path.is_file():
            files.append({"path": str(path), "size": path.stat().st_size})
        elif path.is_dir():
            for file_path in path.rglob("*.py"):
                if "__pycache__" not in str(file_path) and ".git" not in str(file_path):
                    try:
                        files.append(
                            {
                                "path": str(file_path),
                                "size": file_path.stat().st_size,
                                "lines": self._count_lines(file_path),
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Could not analyze {file_path}: {e}")

        return files

    def _count_lines(self, file_path: Path) -> int:
        """ファイルの行数をカウント"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return len(f.readlines())
        except:
            return 0

    def _audit_api_completeness(
        self, files: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """API完全性を監査"""
        findings = []

        # API実装ファイルを特定
        api_files = [f for f in files if "api_implementations" in f["path"]]

        logger.info(f"🔧 {self.name} auditing {len(api_files)} API implementation files")

        for file_info in api_files:
            file_path = file_info["path"]

            try:
                # 必須メソッドの存在確認
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # チェック項目
                checks = {
                    "error_handling": "try:" in content and "except" in content,
                    "logging": "logger" in content or "logging" in content,
                    "validation": "validate" in content or "_validate" in content,
                    "documentation": '"""' in content or "'''" in content,
                    "type_hints": "->" in content and ":" in content,
                    "retry_mechanism": "retry" in content or "backoff" in content,
                    "async_support": "async def" in content or "await" in content,
                    "comprehensive_params": content.count("def ") >= 3,
                }

                score = sum(checks.values()) / len(checks)

                findings.append(
                    {
                        "file": file_path,
                        "type": "api_completeness",
                        "score": score,
                        "details": checks,
                        "severity": "HIGH"
                        if score < 0.7
                        else "MEDIUM"
                        if score < 0.8
                        else "LOW",
                    }
                )

            except Exception as e:
                logger.warning(f"Could not audit {file_path}: {e}")

        # 統合システムファイルもチェック
        unified_files = [f for f in files if "unified_github_manager" in f["path"]]
        for file_info in unified_files:
            file_path = file_info["path"]

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # 統合機能のチェック
                integration_checks = {
                    "single_interface": "UnifiedGitHubManager" in content,
                    "backwards_compatibility": len(
                        [line for line in content.split("\n") if "def " in line]
                    )
                    >= 10,
                    "health_check": "health_check" in content,
                    "error_integration": "error_handler" in content,
                    "rate_limiting": "rate_limit" in content,
                }

                score = sum(integration_checks.values()) / len(integration_checks)

                findings.append(
                    {
                        "file": file_path,
                        "type": "integration_completeness",
                        "score": score,
                        "details": integration_checks,
                        "severity": "HIGH" if score < 0.8 else "LOW",
                    }
                )

            except Exception as e:
                logger.warning(f"Could not audit {file_path}: {e}")

        return findings

    def _audit_error_handling(
        self, files: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """エラーハンドリングを監査"""
        findings = []

        logger.info(f"⚠️ {self.name} auditing error handling across {len(files)} files")

        for file_info in files:
            file_path = file_info["path"]

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # エラーハンドリングパターンをチェック
                patterns = {
                    "try_except": content.count("try:"),
                    "specific_exceptions": content.count("except ")
                    - content.count("except:"),
                    "finally_blocks": content.count("finally:"),
                    "error_logging": content.count("logger.error")
                    + content.count("logger.exception"),
                    "raise_statements": content.count("raise "),
                    "circuit_breaker": "CircuitBreaker" in content
                    or "circuit_breaker" in content,
                    "retry_decorator": "@retry" in content
                    or "retry_with_backoff" in content,
                    "timeout_handling": "timeout" in content
                    or "TimeoutError" in content,
                }

                # スコア計算（重み付け）
                score = 0
                if patterns["try_except"] > 0:
                    score += 0.25
                if patterns["specific_exceptions"] > patterns["try_except"] * 0.5:
                    score += 0.20
                if patterns["error_logging"] > 0:
                    score += 0.20
                if patterns["circuit_breaker"] or patterns["retry_decorator"]:
                    score += 0.25
                if patterns["timeout_handling"]:
                    score += 0.10

                severity = (
                    "CRITICAL"
                    if score < 0.4
                    else "HIGH"
                    if score < 0.6
                    else "MEDIUM"
                    if score < 0.8
                    else "LOW"
                )

                findings.append(
                    {
                        "file": file_path,
                        "type": "error_handling",
                        "score": min(score, 1.0),
                        "patterns": patterns,
                        "severity": severity,
                    }
                )

            except Exception as e:
                logger.warning(f"Could not audit {file_path}: {e}")

        return findings

    def _audit_security(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """セキュリティを監査"""
        findings = []

        logger.info(f"🔒 {self.name} conducting security audit on {len(files)} files")

        security_patterns = {
            "hardcoded_secrets": [
                '"password"',
                '"token"',
                '"api_key"',
                '"secret"',
                "'password'",
                "'token'",
            ],
            "sql_injection": ['f"SELECT', "f'SELECT", "format(", "% ("],
            "insecure_random": ["random.random", "random.randint"],
            "eval_usage": ["eval(", "exec("],
            "pickle_usage": ["pickle.loads", "pickle.load"],
            "subprocess_shell": ["shell=True"],
            "weak_crypto": ["md5", "sha1"],
            "debug_info": ["print(", "pprint(", "debug=True"],
        }

        for file_info in files:
            file_path = file_info["path"]

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                issues = {}
                for category, patterns in security_patterns.items():
                    for pattern in patterns:
                        if pattern in content:
                            if category not in issues:
                                issues[category] = []
                            issues[category].append(pattern)

                # セキュリティ良好パターンもチェック
                good_patterns = {
                    "env_variables": "os.environ" in content or "getenv" in content,
                    "https_usage": "https://" in content,
                    "auth_headers": "Authorization" in content,
                    "input_validation": "validate" in content or "sanitize" in content,
                }

                # セキュリティスコア計算
                score = 1.0
                if issues:
                    score -= len(issues) * 0.15
                    score = max(0, score)

                # 良好パターンでボーナス
                good_count = sum(good_patterns.values())
                score = min(1.0, score + good_count * 0.05)

                severity = (
                    "CRITICAL"
                    if any("hardcoded_secrets" in i for i in issues)
                    else "HIGH"
                    if issues
                    else "LOW"
                )

                if issues or score < 1.0:
                    findings.append(
                        {
                            "file": file_path,
                            "type": "security",
                            "score": score,
                            "issues": issues,
                            "good_patterns": good_patterns,
                            "severity": severity,
                        }
                    )
                else:
                    findings.append(
                        {
                            "file": file_path,
                            "type": "security",
                            "score": score,
                            "issues": {},
                            "good_patterns": good_patterns,
                            "severity": "LOW",
                        }
                    )

            except Exception as e:
                logger.warning(f"Could not audit {file_path}: {e}")

        return findings

    def _audit_performance(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """パフォーマンスを監査"""
        findings = []

        logger.info(f"🚀 {self.name} conducting performance audit on {len(files)} files")

        performance_patterns = {
            "caching": ["cache", "lru_cache", "memoize", "@cached"],
            "async_usage": ["async def", "await ", "asyncio"],
            "batch_processing": ["batch", "bulk", "chunk"],
            "connection_pooling": ["pool", "ConnectionPool"],
            "lazy_loading": ["lazy", "defer", "yield"],
            "optimization": ["optimize", "performance"],
            "streaming": ["stream", "generator", "yield"],
            "rate_limiting": ["rate_limit", "throttle", "RateLimitManager"],
        }

        for file_info in files:
            file_path = file_info["path"]

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                optimizations = {}
                for category, patterns in performance_patterns.items():
                    for pattern in patterns:
                        if pattern in content:
                            optimizations[category] = True
                            break

                # パフォーマンス問題パターン
                anti_patterns = {
                    "blocking_io": "time.sleep" in content and "async" not in content,
                    "large_loops": content.count("for ") > 10,
                    "deep_recursion": content.count("def ") > 0
                    and content.count("return ") > content.count("def ") * 2,
                }

                # パフォーマンススコア計算
                base_score = len(optimizations) / len(performance_patterns)
                penalty = sum(anti_patterns.values()) * 0.1
                score = max(0, base_score - penalty)

                findings.append(
                    {
                        "file": file_path,
                        "type": "performance",
                        "score": score,
                        "optimizations": optimizations,
                        "anti_patterns": anti_patterns,
                        "severity": "HIGH"
                        if score < 0.4
                        else "MEDIUM"
                        if score < 0.6
                        else "LOW",
                    }
                )

            except Exception as e:
                logger.warning(f"Could not audit {file_path}: {e}")

        return findings

    def _audit_test_coverage(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """テストカバレッジを監査"""
        findings = []

        logger.info(f"🧪 {self.name} auditing test coverage")

        # テストファイルを特定
        test_files = [
            f for f in files if "test_" in f["path"] or "_test.py" in f["path"]
        ]
        implementation_files = [
            f
            for f in files
            if "test" not in f["path"] and "__pycache__" not in f["path"]
        ]

        logger.info(
            f"📊 Found {len(test_files)} test files and {len(implementation_files)} implementation files"
        )

        # テストカバレッジ推定
        test_coverage_score = (
            len(test_files) / max(len(implementation_files), 1)
            if implementation_files
            else 0
        )

        # 各テストファイルの品質をチェック
        total_test_quality = 0
        for file_info in test_files:
            file_path = file_info["path"]

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                quality_checks = {
                    "assertions": content.count("assert"),
                    "test_methods": content.count("def test_"),
                    "mocking": "mock" in content.lower() or "patch" in content,
                    "parametrized": "@pytest.mark.parametrize" in content,
                    "fixtures": "@pytest.fixture" in content or "self.setUp" in content,
                    "edge_cases": any(
                        word in content.lower()
                        for word in ["edge", "boundary", "corner", "error", "exception"]
                    ),
                    "integration_tests": "integration" in content.lower(),
                    "comprehensive": content.count("def test_") >= 5,
                }

                quality_score = (
                    min(quality_checks["assertions"] / 30, 1.0) * 0.2
                    + min(quality_checks["test_methods"] / 15, 1.0) * 0.3
                    + (0.15 if quality_checks["mocking"] else 0)
                    + (0.1 if quality_checks["parametrized"] else 0)
                    + (0.1 if quality_checks["fixtures"] else 0)
                    + (0.1 if quality_checks["edge_cases"] else 0)
                    + (0.05 if quality_checks["comprehensive"] else 0)
                )

                total_test_quality += quality_score

                findings.append(
                    {
                        "file": file_path,
                        "type": "test_quality",
                        "score": quality_score,
                        "quality_checks": quality_checks,
                        "severity": "HIGH"
                        if quality_score < 0.6
                        else "MEDIUM"
                        if quality_score < 0.8
                        else "LOW",
                    }
                )

            except Exception as e:
                logger.warning(f"Could not audit {file_path}: {e}")

        # 全体のテストカバレッジ
        average_test_quality = total_test_quality / len(test_files) if test_files else 0
        overall_score = (test_coverage_score * 0.6) + (average_test_quality * 0.4)

        findings.append(
            {
                "type": "overall_test_coverage",
                "score": overall_score,
                "test_files": len(test_files),
                "implementation_files": len(implementation_files),
                "coverage_ratio": test_coverage_score,
                "average_quality": average_test_quality,
                "severity": "CRITICAL"
                if overall_score < 0.7
                else "HIGH"
                if overall_score < 0.85
                else "LOW",
            }
        )

        return findings

    def _audit_general(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """一般的な監査"""
        findings = []

        logger.info(f"📋 {self.name} conducting general code quality audit")

        for file_info in files:
            file_path = file_info["path"]

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.splitlines()

                # コード品質チェック
                quality_metrics = {
                    "has_docstring": '"""' in content or "'''" in content,
                    "has_type_hints": "->" in content and ":" in content,
                    "max_line_length": max(len(line) for line in lines) if lines else 0,
                    "has_logging": "logger" in content or "logging" in content,
                    "follows_naming": not any(
                        line.strip().startswith("class ") and line[6].islower()
                        for line in lines
                    ),
                    "has_imports": "import " in content or "from " in content,
                    "proper_structure": content.count("class ") + content.count("def ")
                    >= 2,
                }

                score = (
                    (0.25 if quality_metrics["has_docstring"] else 0)
                    + (0.2 if quality_metrics["has_type_hints"] else 0)
                    + (0.15 if quality_metrics["max_line_length"] < 120 else 0)
                    + (0.15 if quality_metrics["has_logging"] else 0)
                    + (0.1 if quality_metrics["follows_naming"] else 0)
                    + (0.1 if quality_metrics["proper_structure"] else 0)
                    + (0.05 if quality_metrics["has_imports"] else 0)
                )

                findings.append(
                    {
                        "file": file_path,
                        "type": "code_quality",
                        "score": score,
                        "metrics": quality_metrics,
                        "severity": "HIGH"
                        if score < 0.5
                        else "MEDIUM"
                        if score < 0.7
                        else "LOW",
                    }
                )

            except Exception as e:
                logger.warning(f"Could not audit {file_path}: {e}")

        return findings

    def _calculate_metrics(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """メトリクスを計算"""
        if not findings:
            return {"average_score": 0, "critical_issues": 0, "weighted_score": 0}

        scores = [f["score"] for f in findings if "score" in f]
        critical_issues = sum(1 for f in findings if f.get("severity") == "CRITICAL")
        high_issues = sum(1 for f in findings if f.get("severity") == "HIGH")
        medium_issues = sum(1 for f in findings if f.get("severity") == "MEDIUM")

        metrics = {
            "average_score": sum(scores) / len(scores) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "critical_issues": critical_issues,
            "high_issues": high_issues,
            "medium_issues": medium_issues,
            "total_findings": len(findings),
            "weighted_score": self._calculate_weighted_score(findings),
        }

        return metrics

    def _calculate_weighted_score(self, findings: List[Dict[str, Any]]) -> float:
        """重み付きスコアを計算"""
        weighted_sum = 0
        total_weight = 0

        for finding in findings:
            if "score" in finding:
                base_weight = self.audit_criteria["weight"]

                # 重要度による重み調整
                if finding.get("severity") == "CRITICAL":
                    weight = base_weight * 0.3  # クリティカルは大幅減点
                elif finding.get("severity") == "HIGH":
                    weight = base_weight * 0.7
                elif finding.get("severity") == "MEDIUM":
                    weight = base_weight * 0.9
                else:
                    weight = base_weight

                weighted_sum += finding["score"] * weight
                total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0

    def _make_verdict(self, metrics: Dict[str, Any]) -> str:
        """判定を下す"""
        weighted_score = metrics.get("weighted_score", 0)
        critical_issues = metrics.get("critical_issues", 0)
        high_issues = metrics.get("high_issues", 0)

        if critical_issues > 0:
            return "REJECTED"
        elif high_issues > 5:
            return "REJECTED"
        elif weighted_score >= self.audit_criteria["threshold"]:
            return "APPROVED"
        elif weighted_score >= self.audit_criteria["threshold"] * 0.85:
            return "CONDITIONALLY_APPROVED"
        else:
            return "REJECTED"

    def _generate_recommendations(
        self, findings: List[Dict[str, Any]], metrics: Dict[str, Any]
    ) -> List[str]:
        """推奨事項を生成"""
        recommendations = []

        # 重大な問題に対する推奨事項
        for finding in findings:
            if finding.get("severity") == "CRITICAL":
                if finding["type"] == "security":
                    recommendations.append(
                        f"CRITICAL: Remove hardcoded secrets from {finding.get('file', 'unknown')}"
                    )
                elif finding["type"] == "error_handling":
                    recommendations.append(
                        f"CRITICAL: Implement comprehensive error handling in {finding.get('file', 'unknown')}"
                    )
                elif finding["type"] == "test_coverage":
                    recommendations.append(
                        "CRITICAL: Increase test coverage to meet 95% requirement"
                    )
            elif finding.get("severity") == "HIGH":
                if finding["type"] == "api_completeness":
                    recommendations.append(
                        f"HIGH: Complete API implementation in {finding.get('file', 'unknown')}"
                    )
                elif finding["type"] == "performance":
                    recommendations.append(
                        f"HIGH: Add performance optimizations to {finding.get('file', 'unknown')}"
                    )

        # 専門分野別の推奨事項
        if self.specialization == "API_COMPLETENESS" and metrics["average_score"] < 0.8:
            recommendations.append(
                "Improve API completeness with better documentation and validation"
            )
        elif self.specialization == "ERROR_HANDLING" and metrics["average_score"] < 0.9:
            recommendations.append(
                "Implement circuit breaker pattern and retry mechanisms"
            )
        elif self.specialization == "SECURITY" and metrics["average_score"] < 0.95:
            recommendations.append(
                "Enhance security measures and remove any hardcoded credentials"
            )
        elif self.specialization == "PERFORMANCE" and metrics["average_score"] < 0.85:
            recommendations.append("Add caching, async processing, and rate limiting")
        elif self.specialization == "TEST_COVERAGE" and metrics["average_score"] < 0.95:
            recommendations.append("Increase test coverage and add edge case testing")

        return recommendations[:5]  # 最大5個の推奨事項

    def _check_iron_will_compliance(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Iron Will準拠をチェック"""
        compliance = {
            "compliant": metrics.get("weighted_score", 0) >= 0.95,
            "score": metrics.get("weighted_score", 0),
            "threshold": 0.95,
            "gap": max(0, 0.95 - metrics.get("weighted_score", 0)),
            "specialization_threshold": self.audit_criteria["threshold"],
            "meets_specialization": metrics.get("weighted_score", 0)
            >= self.audit_criteria["threshold"],
        }

        return compliance


async def run_sequential_audit(target_path: str) -> Dict[str, Any]:
    """5人のAncient Elderによる順次監査を実行"""
    start_time = time.time()
    audit_id = str(uuid.uuid4())

    results = {
        "audit_id": audit_id,
        "start_time": datetime.now().isoformat(),
        "target": target_path,
        "elder_audits": [],
        "consensus": None,
        "final_verdict": None,
        "execution_time": 0,
    }

    # 5人のAncient Elder専門分野
    elder_specializations = [
        "API_COMPLETENESS",
        "ERROR_HANDLING",
        "SECURITY",
        "PERFORMANCE",
        "TEST_COVERAGE",
    ]

    try:
        logger.info("🏛️ Launching 5 Ancient Elders for sequential audit...")

        # 5人のAncient Elderを順次実行
        for i, specialization in enumerate(elder_specializations):
            logger.info(f"🏛️ Ancient Elder #{i+1} ({specialization}) starting audit...")

            auditor = AncientElderAuditor(i + 1, specialization)
            audit_result = auditor.audit_implementation(target_path)
            results["elder_audits"].append(audit_result)

            logger.info(
                f"✅ Ancient Elder #{i+1} completed - Verdict: {audit_result['verdict']}"
            )

        # コンセンサスを形成
        consensus = form_consensus(results["elder_audits"])
        results["consensus"] = consensus

        # 最終判定
        final_verdict = make_final_verdict(consensus)
        results["final_verdict"] = final_verdict

        # テスト実行
        logger.info("🧪 Running comprehensive tests...")
        test_results = await run_tests()
        results["test_results"] = test_results

    except Exception as e:
        logger.error(f"❌ Sequential audit failed: {e}")
        results["error"] = str(e)
        results["final_verdict"] = "ERROR"

    finally:
        results["end_time"] = datetime.now().isoformat()
        results["execution_time"] = time.time() - start_time

        # 結果を保存
        save_results(results)

    return results


def form_consensus(elder_audits: List[Dict[str, Any]]) -> Dict[str, Any]:
    """コンセンサスを形成"""
    verdicts = {}
    scores = []
    all_findings = []
    all_recommendations = []
    iron_will_scores = []

    for audit in elder_audits:
        if "verdict" in audit and audit["verdict"] != "ERROR":
            verdict = audit["verdict"]
            verdicts[verdict] = verdicts.get(verdict, 0) + 1

            if "metrics" in audit:
                scores.append(audit["metrics"].get("weighted_score", 0))

            if "findings" in audit:
                all_findings.extend(audit["findings"])

            if "recommendations" in audit:
                all_recommendations.extend(audit["recommendations"])

            if "iron_will_compliance" in audit:
                iron_will_scores.append(audit["iron_will_compliance"].get("score", 0))

    # 最も多い判定を採用
    if verdicts:
        majority_verdict = max(verdicts.items(), key=lambda x: x[1])[0]
    else:
        majority_verdict = "ERROR"

    consensus = {
        "majority_verdict": majority_verdict,
        "verdict_distribution": verdicts,
        "average_score": sum(scores) / len(scores) if scores else 0,
        "min_score": min(scores) if scores else 0,
        "max_score": max(scores) if scores else 0,
        "total_findings": len(all_findings),
        "unique_recommendations": list(set(all_recommendations)),
        "iron_will_average": sum(iron_will_scores) / len(iron_will_scores)
        if iron_will_scores
        else 0,
        "elder_count": len(elder_audits),
    }

    return consensus


def make_final_verdict(consensus: Dict[str, Any]) -> str:
    """最終判定を下す"""
    majority_verdict = consensus.get("majority_verdict", "ERROR")
    average_score = consensus.get("average_score", 0)
    verdict_distribution = consensus.get("verdict_distribution", {})

    # 判定ロジック
    approved_count = verdict_distribution.get("APPROVED", 0)
    conditional_count = verdict_distribution.get("CONDITIONALLY_APPROVED", 0)
    rejected_count = verdict_distribution.get("REJECTED", 0)

    if approved_count >= 4:  # 5人中4人以上が承認
        return "UNANIMOUSLY_APPROVED"
    elif approved_count >= 3:  # 5人中3人以上が承認
        return "APPROVED_BY_MAJORITY"
    elif approved_count + conditional_count >= 4:  # 承認+条件付き承認が4人以上
        return "CONDITIONALLY_APPROVED"
    elif rejected_count >= 3:  # 5人中3人以上が拒否
        return "REJECTED_BY_MAJORITY"
    elif average_score >= 0.8:
        return "CONDITIONALLY_APPROVED"
    else:
        return "REJECTED"


async def run_tests() -> Dict[str, Any]:
    """テストを実行"""
    test_results = {
        "tests_run": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "coverage": 0,
        "execution_time": 0,
    }

    start_time = time.time()

    try:
        # pytest実行
        result = subprocess.run(
            [
                "python3",
                "-m",
                "pytest",
                "-v",
                "--tb=short",
                "tests/test_unified_github_integration.py",
                "tests/test_github_notification_integration.py",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        output = result.stdout + result.stderr

        # 結果を解析
        import re

        # 合格数
        passed_match = re.search(r"(\d+) passed", output)
        if passed_match:
            test_results["tests_passed"] = int(passed_match.group(1))

        # 失敗数
        failed_match = re.search(r"(\d+) failed", output)
        if failed_match:
            test_results["tests_failed"] = int(failed_match.group(1))

        test_results["tests_run"] = (
            test_results["tests_passed"] + test_results["tests_failed"]
        )
        test_results["success"] = result.returncode == 0
        test_results["output_summary"] = output[-500:]  # 最後の500文字

        logger.info(
            f"🧪 Tests completed: {test_results['tests_passed']}/{test_results['tests_run']} passed"
        )

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        test_results["error"] = str(e)
        test_results["success"] = False

    finally:
        test_results["execution_time"] = time.time() - start_time

    return test_results


def save_results(results: Dict[str, Any]) -> None:
    """結果を保存"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ディレクトリ作成
    os.makedirs("audit_reports", exist_ok=True)

    # JSON形式で保存
    output_file = f"audit_reports/ancient_elder_sequential_{timestamp}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    logger.info(f"📊 Audit results saved to {output_file}")

    # Markdownレポートも生成
    generate_markdown_report(results, timestamp)


def generate_markdown_report(results: Dict[str, Any], timestamp: str) -> None:
    """Markdownレポートを生成"""
    report_file = f"audit_reports/ancient_elder_sequential_{timestamp}.md"

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# 🏛️ Ancient Elder Sequential Audit Report\n\n")
        f.write(f"**Audit ID**: {results['audit_id']}\n")
        f.write(f"**Date**: {results['start_time']}\n")
        f.write(f"**Target**: {results['target']}\n")
        f.write(f"**Execution Time**: {results['execution_time']:.2f} seconds\n\n")

        f.write(f"## 🎯 Final Verdict: **{results['final_verdict']}**\n\n")

        # コンセンサス
        consensus = results.get("consensus", {})
        f.write("## 📊 Consensus Results\n\n")
        f.write(f"- **Average Score**: {consensus.get('average_score', 0):.2%}\n")
        f.write(
            f"- **Score Range**: {consensus.get('min_score', 0):.2%} - {consensus.get('max_score', 0):.2%}\n"
        )
        f.write(
            f"- **Iron Will Average**: {consensus.get('iron_will_average', 0):.2%}\n"
        )
        f.write(f"- **Total Findings**: {consensus.get('total_findings', 0)}\n\n")

        # Elder投票詳細
        f.write("## 🗳️ Elder Votes\n\n")
        f.write("| Elder | Specialization | Verdict | Score |\n")
        f.write("|-------|---------------|---------|-------|\n")
        for audit in results.get("elder_audits", []):
            score = audit.get("metrics", {}).get("weighted_score", 0)
            f.write(
                f"| {audit.get('elder_name', 'Unknown')} | {audit.get('specialization', 'N/A')} | {audit.get('verdict', 'ERROR')} | {score:.2%} |\n"
            )
        f.write("\n")

        # 判定分布
        if consensus.get("verdict_distribution"):
            f.write("## 📈 Verdict Distribution\n\n")
            for verdict, count in consensus["verdict_distribution"].items():
                f.write(f"- **{verdict}**: {count} elders\n")
            f.write("\n")

        # テスト結果
        if "test_results" in results:
            test = results["test_results"]
            f.write("## 🧪 Test Results\n\n")
            f.write(f"- **Tests Run**: {test.get('tests_run', 0)}\n")
            f.write(f"- **Tests Passed**: {test.get('tests_passed', 0)}\n")
            f.write(f"- **Tests Failed**: {test.get('tests_failed', 0)}\n")
            f.write(
                f"- **Success Rate**: {(test.get('tests_passed', 0) / max(test.get('tests_run', 1), 1) * 100):.1f}%\n\n"
            )

        # 推奨事項
        if consensus.get("unique_recommendations"):
            f.write("## 💡 Recommendations\n\n")
            for i, rec in enumerate(consensus["unique_recommendations"][:10], 1):
                f.write(f"{i}. {rec}\n")
            f.write("\n")

        # 各Elderの詳細
        f.write("## 📋 Detailed Elder Reports\n\n")
        for audit in results.get("elder_audits", []):
            f.write(f"### {audit.get('elder_name', 'Unknown Elder')}\n\n")
            f.write(f"- **Verdict**: {audit.get('verdict', 'ERROR')}\n")
            if "metrics" in audit:
                metrics = audit["metrics"]
                f.write(f"- **Score**: {metrics.get('weighted_score', 0):.2%}\n")
                f.write(f"- **Critical Issues**: {metrics.get('critical_issues', 0)}\n")
                f.write(f"- **High Issues**: {metrics.get('high_issues', 0)}\n")
            f.write(f"- **Files Analyzed**: {audit.get('files_analyzed', 0)}\n")
            f.write(f"- **Execution Time**: {audit.get('execution_time', 0):.2f}s\n\n")

        # Iron Will準拠状況
        f.write("## 🗡️ Iron Will Compliance\n\n")
        f.write(
            f"- **Average Compliance Score**: {consensus.get('iron_will_average', 0):.2%}\n"
        )
        f.write(f"- **Iron Will Threshold**: 95%\n")
        f.write(
            f"- **Compliant**: {'✅' if consensus.get('iron_will_average', 0) >= 0.95 else '❌'}\n"
        )

    logger.info(f"📄 Markdown report saved to {report_file}")


async def main():
    """メイン実行関数"""
    logger.info("🏛️ Starting Ancient Elder Sequential Audit System")

    # 監査対象を指定
    target_path = "libs/integrations/github"

    # 監査実行
    results = await run_sequential_audit(target_path)

    # 結果サマリー
    logger.info("=" * 80)
    logger.info(f"🎯 FINAL VERDICT: {results['final_verdict']}")
    logger.info(f"📊 Consensus Score: {results['consensus']['average_score']:.2%}")
    logger.info(
        f"🗡️ Iron Will Average: {results['consensus']['iron_will_average']:.2%}"
    )
    logger.info(f"⏱️ Total Execution Time: {results['execution_time']:.2f} seconds")
    logger.info(
        f"🧪 Test Success: {results.get('test_results', {}).get('success', False)}"
    )
    logger.info("=" * 80)

    return results


if __name__ == "__main__":
    asyncio.run(main())
