#!/usr/bin/env python3
"""
A2Aマルチプロセス Ancient Elder 5人監査システム
Iron Will基準による超厳格並列監査・テスト実行
"""

import asyncio
import json
import logging
import multiprocessing as mp
import os
import subprocess
import sys
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
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
        logging.FileHandler("logs/multiprocess_ancient_elder_audit.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class AncientElderAuditor:
    """Ancient Elder監査官クラス"""

    def __init__(self, elder_id: int, specialization: str):
        """
        初期化

        Args:
            elder_id: Elder識別番号
            specialization: 専門分野
        """
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
            # ファイル分析
            files_analyzed = self._analyze_files(target_path)
            audit_result["files_analyzed"] = len(files_analyzed)

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

        except Exception as e:
            logger.error(f"{self.name} audit failed: {e}")
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
                if "__pycache__" not in str(file_path):
                    files.append(
                        {
                            "path": str(file_path),
                            "size": file_path.stat().st_size,
                            "lines": self._count_lines(file_path),
                        }
                    )

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

        for file_info in api_files:
            file_path = file_info["path"]

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
            }

            score = sum(checks.values()) / len(checks)

            findings.append(
                {
                    "file": file_path,
                    "type": "api_completeness",
                    "score": score,
                    "details": checks,
                    "severity": "HIGH" if score < 0.8 else "LOW",
                }
            )

        return findings

    def _audit_error_handling(
        self, files: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """エラーハンドリングを監査"""
        findings = []

        for file_info in files:
            file_path = file_info["path"]

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
                "circuit_breaker": "CircuitBreaker" in content,
                "retry_decorator": "@retry" in content
                or "retry_with_backoff" in content,
            }

            # スコア計算
            score = 0
            if patterns["try_except"] > 0:
                score += 0.3
            if patterns["specific_exceptions"] > patterns["try_except"] * 0.7:
                score += 0.2
            if patterns["error_logging"] > 0:
                score += 0.2
            if patterns["circuit_breaker"] or patterns["retry_decorator"]:
                score += 0.3

            findings.append(
                {
                    "file": file_path,
                    "type": "error_handling",
                    "score": min(score, 1.0),
                    "patterns": patterns,
                    "severity": (
                        "CRITICAL"
                        if score < 0.5
                        else "MEDIUM" if score < 0.8 else "LOW"
                    ),
                }
            )

        return findings

    def _audit_security(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """セキュリティを監査"""
        findings = []

        security_patterns = {
            "hardcoded_secrets": ["password=", "token=", "api_key=", "secret="],
            "sql_injection": ['f"SELECT', "f'SELECT", "format(", "% ("],
            "insecure_random": ["random.random", "random.randint"],
            "eval_usage": ["eval(", "exec("],
            "pickle_usage": ["pickle.loads", "pickle.load"],
            "subprocess_shell": ["shell=True"],
        }

        for file_info in files:
            file_path = file_info["path"]

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            issues = {}
            for category, patterns in security_patterns.items():
                for pattern in patterns:
                    if pattern in content:
                        if category not in issues:
                            issues[category] = []
                        issues[category].append(pattern)

            # セキュリティスコア計算
            score = 1.0
            if issues:
                score -= len(issues) * 0.2
                score = max(0, score)

            if issues or score < 1.0:
                findings.append(
                    {
                        "file": file_path,
                        "type": "security",
                        "score": score,
                        "issues": issues,
                        "severity": "CRITICAL" if issues else "LOW",
                    }
                )

        return findings

    def _audit_performance(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """パフォーマンスを監査"""
        findings = []

        performance_patterns = {
            "caching": ["cache", "lru_cache", "memoize"],
            "async_usage": ["async def", "await ", "asyncio"],
            "batch_processing": ["batch", "bulk", "chunk"],
            "connection_pooling": ["pool", "ConnectionPool"],
            "lazy_loading": ["lazy", "defer", "yield"],
            "optimization": ["optimize", "performance"],
        }

        for file_info in files:
            file_path = file_info["path"]

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            optimizations = {}
            for category, patterns in performance_patterns.items():
                for pattern in patterns:
                    if pattern in content:
                        optimizations[category] = True
                        break

            # パフォーマンススコア計算
            score = len(optimizations) / len(performance_patterns)

            findings.append(
                {
                    "file": file_path,
                    "type": "performance",
                    "score": score,
                    "optimizations": optimizations,
                    "severity": (
                        "HIGH" if score < 0.5 else "MEDIUM" if score < 0.7 else "LOW"
                    ),
                }
            )

        return findings

    def _audit_test_coverage(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """テストカバレッジを監査"""
        findings = []

        # テストファイルを特定
        test_files = [
            f for f in files if "test_" in f["path"] or "_test.py" in f["path"]
        ]
        implementation_files = [
            f
            for f in files
            if "test" not in f["path"] and "__pycache__" not in f["path"]
        ]

        # テストカバレッジ推定
        test_coverage_score = len(test_files) / max(len(implementation_files), 1)

        # テスト品質チェック
        for file_info in test_files:
            file_path = file_info["path"]

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            quality_checks = {
                "assertions": content.count("assert"),
                "test_methods": content.count("def test_"),
                "mocking": "mock" in content.lower() or "patch" in content,
                "parametrized": "@pytest.mark.parametrize" in content,
                "fixtures": "@pytest.fixture" in content or "self.setUp" in content,
                "edge_cases": any(
                    word in content.lower() for word in ["edge", "boundary", "corner"]
                ),
            }

            quality_score = (
                min(quality_checks["assertions"] / 20, 1.0) * 0.3
                + min(quality_checks["test_methods"] / 10, 1.0) * 0.3
                + (0.4 if quality_checks["mocking"] else 0)
                + (0.2 if quality_checks["parametrized"] else 0)
                + (0.2 if quality_checks["edge_cases"] else 0)
            ) / 1.4

            findings.append(
                {
                    "file": file_path,
                    "type": "test_quality",
                    "score": quality_score,
                    "quality_checks": quality_checks,
                    "severity": "HIGH" if quality_score < 0.7 else "LOW",
                }
            )

        # 全体のテストカバレッジ
        findings.append(
            {
                "type": "test_coverage",
                "score": test_coverage_score,
                "test_files": len(test_files),
                "implementation_files": len(implementation_files),
                "severity": "CRITICAL" if test_coverage_score < 0.8 else "LOW",
            }
        )

        return findings

    def _audit_general(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """一般的な監査"""
        findings = []

        for file_info in files:
            file_path = file_info["path"]

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.splitlines()

            # コード品質チェック
            quality_metrics = {
                "has_docstring": '"""' in content or "'''" in content,
                "has_type_hints": "->" in content,
                "max_line_length": max(len(line) for line in lines) if lines else 0,
                "has_logging": "logger" in content or "logging" in content,
                "follows_naming": not any(
                    line.strip().startswith("class ") and line[6].islower()
                    for line in lines
                ),
            }

            score = (
                (0.3 if quality_metrics["has_docstring"] else 0)
                + (0.2 if quality_metrics["has_type_hints"] else 0)
                + (0.2 if quality_metrics["max_line_length"] < 120 else 0)
                + (0.2 if quality_metrics["has_logging"] else 0)
                + (0.1 if quality_metrics["follows_naming"] else 0)
            )

            findings.append(
                {
                    "file": file_path,
                    "type": "code_quality",
                    "score": score,
                    "metrics": quality_metrics,
                    "severity": "MEDIUM" if score < 0.7 else "LOW",
                }
            )

        return findings

    def _calculate_metrics(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """メトリクスを計算"""
        if not findings:
            return {"average_score": 0, "critical_issues": 0}

        scores = [f["score"] for f in findings if "score" in f]
        critical_issues = sum(1 for f in findings if f.get("severity") == "CRITICAL")
        high_issues = sum(1 for f in findings if f.get("severity") == "HIGH")

        metrics = {
            "average_score": sum(scores) / len(scores) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "critical_issues": critical_issues,
            "high_issues": high_issues,
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
                weight = self.audit_criteria["weight"]
                if finding.get("severity") == "CRITICAL":
                    weight *= 2.0
                elif finding.get("severity") == "HIGH":
                    weight *= 1.5

                weighted_sum += finding["score"] * weight
                total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0

    def _make_verdict(self, metrics: Dict[str, Any]) -> str:
        """判定を下す"""
        weighted_score = metrics.get("weighted_score", 0)
        critical_issues = metrics.get("critical_issues", 0)

        if critical_issues > 0:
            return "REJECTED"
        elif weighted_score >= self.audit_criteria["threshold"]:
            return "APPROVED"
        elif weighted_score >= self.audit_criteria["threshold"] * 0.9:
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
            if finding.get("severity") in ["CRITICAL", "HIGH"]:
                if finding["type"] == "security":
                    recommendations.append(
                        f"CRITICAL: Security issues found in {finding['file']}"
                    )
                elif finding["type"] == "error_handling":
                    recommendations.append(
                        f"Improve error handling in {finding['file']}"
                    )
                elif finding["type"] == "test_coverage":
                    recommendations.append(
                        "Increase test coverage to meet 95% requirement"
                    )

        # 全体的な推奨事項
        if metrics["average_score"] < 0.8:
            recommendations.append("Overall quality needs improvement across all files")

        return recommendations[:10]  # 最大10個の推奨事項

    def _check_iron_will_compliance(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Iron Will準拠をチェック"""
        compliance = {
            "compliant": metrics.get("weighted_score", 0) >= 0.95,
            "score": metrics.get("weighted_score", 0),
            "threshold": 0.95,
            "gap": max(0, 0.95 - metrics.get("weighted_score", 0)),
        }

        return compliance


class MultiProcessAncientElderAudit:
    """マルチプロセスAncient Elder監査システム"""

    def __init__(self):
        """初期化"""
        self.process_count = min(mp.cpu_count(), 5)  # 最大5プロセス
        self.executor = ProcessPoolExecutor(max_workers=self.process_count)

        # 5人のAncient Elder専門分野
        self.elder_specializations = [
            "API_COMPLETENESS",
            "ERROR_HANDLING",
            "SECURITY",
            "PERFORMANCE",
            "TEST_COVERAGE",
        ]

        logger.info(
            f"🏛️ Multi-Process Ancient Elder Audit System initialized with {self." \
                "process_count} elders"
        )

    async def execute_parallel_audit(self, target_path: str) -> Dict[str, Any]:
        """並列監査を実行"""
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

        try:
            # 5人のAncient Elderを並列で起動
            logger.info("🏛️ Launching 5 Ancient Elders for parallel audit...")

            loop = asyncio.get_event_loop()
            audit_futures = []

            for i, specialization in enumerate(self.elder_specializations):
                future = loop.run_in_executor(
                    self.executor,
                    self._run_elder_audit,
                    i + 1,
                    specialization,
                    target_path,
                )
                audit_futures.append((i + 1, specialization, future))

            # 結果を収集
            for elder_id, specialization, future in audit_futures:
                try:
                    audit_result = await future
                    results["elder_audits"].append(audit_result)
                    logger.info(
                        f"✅ Ancient Elder #{elder_id} ({specialization}) completed audit"
                    )
                except Exception as e:
                    logger.error(
                        f"❌ Ancient Elder #{elder_id} ({specialization}) failed: {e}"
                    )
                    results["elder_audits"].append(
                        {
                            "elder_id": elder_id,
                            "specialization": specialization,
                            "error": str(e),
                            "verdict": "ERROR",
                        }
                    )

            # コンセンサスを形成
            consensus = self._form_consensus(results["elder_audits"])
            results["consensus"] = consensus

            # 最終判定
            final_verdict = self._make_final_verdict(consensus)
            results["final_verdict"] = final_verdict

            # テスト実行
            logger.info("🧪 Running comprehensive tests...")
            test_results = await self._run_tests(target_path)
            results["test_results"] = test_results

            # 総合レポート生成
            report = self._generate_comprehensive_report(results)
            results["comprehensive_report"] = report

        except Exception as e:
            logger.error(f"❌ Multi-process audit failed: {e}")
            results["error"] = str(e)
            results["final_verdict"] = "ERROR"

        finally:
            results["end_time"] = datetime.now().isoformat()
            results["execution_time"] = time.time() - start_time

            # 結果を保存
            self._save_results(results)

        return results

    def _run_elder_audit(
        self, elder_id: int, specialization: str, target_path: str
    ) -> Dict[str, Any]:
        """Elder監査を実行（プロセス内）"""
        auditor = AncientElderAuditor(elder_id, specialization)
        return auditor.audit_implementation(target_path)

    def _form_consensus(self, elder_audits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """コンセンサスを形成"""
        verdicts = {}
        scores = []
        all_findings = []
        all_recommendations = []

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
        }

        return consensus

    def _make_final_verdict(self, consensus: Dict[str, Any]) -> str:
        """最終判定を下す"""
        majority_verdict = consensus.get("majority_verdict", "ERROR")
        average_score = consensus.get("average_score", 0)

        # 全員一致でAPPROVEDの場合のみ承認
        verdict_distribution = consensus.get("verdict_distribution", {})
        if verdict_distribution.get("APPROVED", 0) == 5:
            return "UNANIMOUSLY_APPROVED"
        elif verdict_distribution.get("APPROVED", 0) >= 3:
            return "APPROVED_BY_MAJORITY"
        elif verdict_distribution.get("CONDITIONALLY_APPROVED", 0) >= 3:
            return "CONDITIONALLY_APPROVED"
        elif average_score >= 0.8:
            return "CONDITIONALLY_APPROVED"
        else:
            return "REJECTED"

    async def _run_tests(self, target_path: str) -> Dict[str, Any]:
        """テストを実行"""
        test_results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "coverage": 0,
            "details": [],
        }

        try:
            # pytest実行
            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "pytest",
                    "-v",
                    "--tb=short",
                    "--cov=libs/integrations/github",
                    "tests/test_unified_github_integration.py",
                    "tests/test_github_notification_integration.py",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            output = result.stdout + result.stderr

            # 結果を解析
            if "passed" in output:
                import re

                match = re.search(r"(\d+) passed", output)
                if match:
                    test_results["tests_passed"] = int(match.group(1))
                    test_results["tests_run"] = test_results["tests_passed"]

            if "failed" in output:
                import re

                match = re.search(r"(\d+) failed", output)
                if match:
                    test_results["tests_failed"] = int(match.group(1))
                    test_results["tests_run"] += test_results["tests_failed"]

            # カバレッジ情報
            if "TOTAL" in output:
                import re

                match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
                if match:
                    test_results["coverage"] = int(match.group(1))

            test_results["success"] = result.returncode == 0
            test_results["output_summary"] = output[-1000:]  # 最後の1000文字

        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            test_results["error"] = str(e)
            test_results["success"] = False

        return test_results

    def _generate_comprehensive_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """総合レポートを生成"""
        report = {
            "title": "Ancient Elder Parallel Audit Report",
            "audit_id": results["audit_id"],
            "timestamp": datetime.now().isoformat(),
            "executive_summary": {
                "final_verdict": results["final_verdict"],
                "consensus_score": results["consensus"]["average_score"],
                "test_success_rate": 0,
                "iron_will_compliance": False,
            },
            "elder_votes": {},
            "critical_findings": [],
            "action_items": [],
        }

        # Elder投票集計
        for audit in results["elder_audits"]:
            if "verdict" in audit:
                report["elder_votes"][audit["elder_name"]] = audit["verdict"]

        # クリティカルな発見事項
        for audit in results["elder_audits"]:
            if "findings" in audit:
                for finding in audit["findings"]:
                    if finding.get("severity") == "CRITICAL":
                        report["critical_findings"].append(
                            {"elder": audit["elder_name"], "finding": finding}
                        )

        # テスト成功率
        if "test_results" in results and results["test_results"]["tests_run"] > 0:
            report["executive_summary"]["test_success_rate"] = (
                results["test_results"]["tests_passed"]
                / results["test_results"]["tests_run"]
                * 100
            )

        # Iron Will準拠
        report["executive_summary"]["iron_will_compliance"] = (
            results["consensus"]["average_score"] >= 0.95
        )

        # アクション項目
        report["action_items"] = results["consensus"].get("unique_recommendations", [])

        return report

    def _save_results(self, results: Dict[str, Any]) -> None:
        """結果を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON形式で保存
        output_file = f"audit_reports/ancient_elder_audit_{timestamp}.json"
        os.makedirs("audit_reports", exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"📊 Audit results saved to {output_file}")

        # Markdownレポートも生成
        self._generate_markdown_report(results, timestamp)

    def _generate_markdown_report(
        self, results: Dict[str, Any], timestamp: str
    ) -> None:
        """Markdownレポートを生成"""
        report_file = f"audit_reports/ancient_elder_audit_{timestamp}.md"

        with open(report_file, "w", encoding="utf-8") as f:
            f.write("# 🏛️ Ancient Elder Parallel Audit Report\n\n")
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
                f"- **Score Range**: {consensus.get(
                    'min_score',
                    0):.2%} - {consensus.get('max_score',
                    0
                ):.2%}\n"
            )
            f.write(f"- **Total Findings**: {consensus.get('total_findings', 0)}\n\n")

            # Elder投票
            f.write("## 🗳️ Elder Votes\n\n")
            f.write("| Elder | Specialization | Verdict |\n")
            f.write("|-------|---------------|----------|\n")
            for audit in results.get("elder_audits", []):
                f.write(
                    f"| {audit.get(
                        'elder_name',
                        'Unknown')} | {audit.get('specialization',
                        'N/A')} | {audit.get('verdict',
                        'ERROR'
                    )} |\n"
                )
            f.write("\n")

            # テスト結果
            if "test_results" in results:
                test = results["test_results"]
                f.write("## 🧪 Test Results\n\n")
                f.write(f"- **Tests Run**: {test.get('tests_run', 0)}\n")
                f.write(f"- **Tests Passed**: {test.get('tests_passed', 0)}\n")
                f.write(f"- **Tests Failed**: {test.get('tests_failed', 0)}\n")
                f.write(f"- **Coverage**: {test.get('coverage', 0)}%\n\n")

            # 推奨事項
            if consensus.get("unique_recommendations"):
                f.write("## 💡 Recommendations\n\n")
                for rec in consensus["unique_recommendations"]:
                    f.write(f"- {rec}\n")
                f.write("\n")

            # 総合レポート
            if "comprehensive_report" in results:
                report = results["comprehensive_report"]
                f.write("## 📋 Executive Summary\n\n")
                summary = report.get("executive_summary", {})
                f.write(
                    f"- **Iron Will Compliance**: {'✅' if summary.get('iron_will_compliance') else '❌'}\n"
                )
                f.write(
                    f"- **Test Success Rate**: {summary.get('test_success_rate', 0):.1f}%\n"
                )
                f.write(
                    f"- **Consensus Score**: {summary.get('consensus_score', 0):.2%}\n"
                )

        logger.info(f"📄 Markdown report saved to {report_file}")

    def __del__(self):
        """クリーンアップ"""
        if hasattr(self, "executor"):
            self.executor.shutdown(wait=True)


async def main():
    """メイン実行関数"""
    logger.info("🏛️ Starting Multi-Process Ancient Elder Audit System")

    # 監査対象を指定
    target_path = "libs/integrations/github"

    # 監査システムを起動
    audit_system = MultiProcessAncientElderAudit()
    results = await audit_system.execute_parallel_audit(target_path)

    # 結果サマリー
    logger.info("=" * 60)
    logger.info(f"🎯 FINAL VERDICT: {results['final_verdict']}")
    logger.info(f"📊 Consensus Score: {results['consensus']['average_score']:.2%}")
    logger.info(f"⏱️ Total Execution Time: {results['execution_time']:.2f} seconds")
    logger.info("=" * 60)

    return results


if __name__ == "__main__":
    asyncio.run(main())
