#!/usr/bin/env python3
"""
品質ゲートシステム - テスト品質とデプロイメント制御
"""
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class QualityGateSystem:
    """品質ゲートシステムクラス"""

    def __init__(
        self,
        coverage_threshold: int = 80,
        test_success_threshold: int = 95,
        max_lint_errors: int = 10,
        security_threshold: int = 80,
        block_deployment_on_failure: bool = False,
        critical_gates: Optional[List[str]] = None,
    ):
        """
        品質ゲートシステムの初期化

        Args:
            coverage_threshold: カバレッジ閾値（%）
            test_success_threshold: テスト成功率閾値（%）
            max_lint_errors: 最大リントエラー数
            security_threshold: セキュリティスコア閾値
            block_deployment_on_failure: 失敗時のデプロイメント阻止
            critical_gates: 重要ゲートのリスト
        """
        self.coverage_threshold = coverage_threshold
        self.test_success_threshold = test_success_threshold
        self.max_lint_errors = max_lint_errors
        self.security_threshold = security_threshold
        self.block_deployment_on_failure = block_deployment_on_failure
        self.critical_gates = critical_gates or ["coverage", "security"]

    def check_coverage_gate(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        カバレッジゲートの検証

        Args:
            test_results: テスト結果データ

        Returns:
            ゲート検証結果
        """
        coverage_data = test_results.get("coverage", {})
        actual_coverage = coverage_data.get("coverage", 0)
        threshold = coverage_data.get("threshold", self.coverage_threshold)

        passed = actual_coverage >= threshold

        result = {
            "gate_type": "coverage",
            "passed": passed,
            "actual_value": actual_coverage,
            "threshold": threshold,
            "timestamp": datetime.now().isoformat(),
        }

        if not passed:
            result["reason"] = f"カバレッジが不足しています: {actual_coverage}% < {threshold}%"

        return result

    def check_test_gate(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        テスト成功率ゲートの検証

        Args:
            test_results: テスト結果データ

        Returns:
            ゲート検証結果
        """
        total_passed = 0
        total_failed = 0

        for test_type in ["unit_tests", "integration_tests"]:
            if test_type in test_results:
                output = test_results[test_type].get("output", "")
                passed, failed = self._extract_test_counts(output)
                total_passed += passed
                total_failed += failed

        total_tests = total_passed + total_failed
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        passed = success_rate >= self.test_success_threshold

        result = {
            "gate_type": "test_success_rate",
            "passed": passed,
            "actual_value": round(success_rate, 2),
            "threshold": self.test_success_threshold,
            "total_tests": total_tests,
            "passed_tests": total_passed,
            "failed_tests": total_failed,
            "timestamp": datetime.now().isoformat(),
        }

        if not passed:
            result[
                "reason"
            ] = f"テスト成功率が不足: {success_rate:.1f}% < {self.test_success_threshold}%"

        return result

    def check_security_gate(self, security_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        セキュリティゲートの検証

        Args:
            security_results: セキュリティ検査結果

        Returns:
            ゲート検証結果
        """
        vulnerabilities = security_results.get("vulnerabilities", [])
        security_score = security_results.get("security_score", 100)
        critical_issues = security_results.get("critical_issues", 0)
        high_issues = security_results.get("high_issues", 0)

        # クリティカル脆弱性は即座に失敗
        critical_vulns = [v for v in vulnerabilities if v.get("severity") == "CRITICAL"]
        has_critical = len(critical_vulns) > 0 or critical_issues > 0

        # セキュリティスコアもチェック
        score_passed = security_score >= self.security_threshold

        passed = not has_critical and score_passed

        result = {
            "gate_type": "security",
            "passed": passed,
            "security_score": security_score,
            "threshold": self.security_threshold,
            "critical_issues": critical_issues,
            "high_issues": high_issues,
            "total_vulnerabilities": len(vulnerabilities),
            "timestamp": datetime.now().isoformat(),
        }

        if not passed:
            reasons = []
            if has_critical:
                reasons.append(f"CRITICAL脆弱性が検出されました: {critical_issues}件")
            if not score_passed:
                reasons.append(
                    f"セキュリティスコアが不足: {security_score} < {self.security_threshold}"
                )
            result["reason"] = "; ".join(reasons)

        return result

    def check_lint_gate(self, lint_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        リント品質ゲートの検証

        Args:
            lint_results: リント検査結果

        Returns:
            ゲート検証結果
        """
        checks = lint_results.get("checks", {})
        total_errors = 0
        failed_tools = []

        for tool, result in checks.items():
            error_count = result.get("error_count", 0)
            total_errors += error_count

            if not result.get("success", True):
                failed_tools.append(tool)

        passed = total_errors <= self.max_lint_errors

        result = {
            "gate_type": "lint_quality",
            "passed": passed,
            "total_errors": total_errors,
            "max_allowed": self.max_lint_errors,
            "failed_tools": failed_tools,
            "timestamp": datetime.now().isoformat(),
        }

        if not passed:
            result["reason"] = f"リントエラーが多すぎます: {total_errors} > {self.max_lint_errors}"

        return result

    def evaluate_quality(
        self, test_results: Dict[str, Any], security_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        全体的な品質評価を実行

        Args:
            test_results: テスト結果データ
            security_results: セキュリティ検査結果

        Returns:
            総合品質評価結果
        """
        gate_results = []

        # 各ゲートを実行
        coverage_result = self.check_coverage_gate(test_results)
        gate_results.append(coverage_result)

        test_result = self.check_test_gate(test_results)
        gate_results.append(test_result)

        security_result = self.check_security_gate(security_results)
        gate_results.append(security_result)

        # リントゲート（存在する場合）
        if "lint" in test_results:
            lint_result = self.check_lint_gate(test_results["lint"])
            gate_results.append(lint_result)

        # 統計計算
        total_gates = len(gate_results)
        passed_gates = sum(1 for result in gate_results if result["passed"])
        failed_gates = total_gates - passed_gates

        overall_passed = failed_gates == 0

        # デプロイメント阻止の判定
        deployment_blocked = False
        blocking_reasons = []

        if self.block_deployment_on_failure and not overall_passed:
            # クリティカルゲートで失敗した場合のみブロック
            for result in gate_results:
                if not result["passed"] and result["gate_type"] in self.critical_gates:
                    deployment_blocked = True
                    blocking_reasons.append(result["gate_type"])

        return {
            "overall_passed": overall_passed,
            "total_gates": total_gates,
            "passed_gates": passed_gates,
            "failed_gates": failed_gates,
            "success_rate": round((passed_gates / total_gates * 100), 2),
            "gate_results": gate_results,
            "deployment_blocked": deployment_blocked,
            "blocking_reasons": blocking_reasons,
            "timestamp": datetime.now().isoformat(),
        }

    def generate_quality_report(
        self, evaluation_result: Dict[str, Any], output_path: Path
    ) -> None:
        """
        品質ゲートレポートを生成

        Args:
            evaluation_result: 品質評価結果
            output_path: 出力ファイルパス
        """
        recommendations = self._generate_recommendations(
            evaluation_result["gate_results"]
        )

        report_data = {
            "timestamp": evaluation_result["timestamp"],
            "summary": self._extract_summary(evaluation_result),
            "gate_details": evaluation_result["gate_results"],
            "deployment_status": self._extract_deployment_status(evaluation_result),
            "recommendations": recommendations,
        }

        with open(output_path, "w") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

    def _generate_recommendations(
        self, gate_results: List[Dict[str, Any]]
    ) -> List[str]:
        """失敗したゲートに対する推奨事項を生成"""
        recommendations = []

        for gate_result in gate_results:
            if not gate_result["passed"]:
                recommendation = self._get_gate_recommendation(gate_result)
                if recommendation:
                    recommendations.append(recommendation)

        return recommendations

    def _get_gate_recommendation(self, gate_result: Dict[str, Any]) -> Optional[str]:
        """特定のゲートに対する推奨事項を取得"""
        gate_type = gate_result["gate_type"]

        recommendations_map = {
            "coverage": lambda r: f"カバレッジを {r.get('threshold', 80)}% 以上に向上させてください",
            "test_success_rate": lambda r: f"テスト成功率を {r.get('threshold', 95)}% 以上に向上させてください",
            "security": lambda r: "セキュリティ脆弱性を修正してください",
            "lint_quality": lambda r: f"リントエラーを {r.get('max_allowed', 10)} 個以下に削減してください",
        }

        recommendation_func = recommendations_map.get(gate_type)
        return recommendation_func(gate_result) if recommendation_func else None

    def _extract_summary(self, evaluation_result: Dict[str, Any]) -> Dict[str, Any]:
        """評価結果からサマリーを抽出"""
        return {
            "overall_passed": evaluation_result["overall_passed"],
            "success_rate": evaluation_result["success_rate"],
            "total_gates": evaluation_result["total_gates"],
            "passed_gates": evaluation_result["passed_gates"],
            "failed_gates": evaluation_result["failed_gates"],
        }

    def _extract_deployment_status(
        self, evaluation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """デプロイメント状態を抽出"""
        return {
            "blocked": evaluation_result.get("deployment_blocked", False),
            "blocking_reasons": evaluation_result.get("blocking_reasons", []),
        }

    def analyze_quality_trends(
        self, historical_data: List[Dict[str, Any]], current_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        品質トレンドを分析

        Args:
            historical_data: 履歴データ
            current_metrics: 現在のメトリクス

        Returns:
            トレンド分析結果
        """

        def calculate_trend(values: List[float]) -> str:
            """calculate_trendメソッド"""
            if len(values) < 2:
                return "insufficient_data"

            # 簡単な線形トレンド
            recent_avg = sum(values[-2:]) / 2
            older_avg = (
                sum(values[:-2]) / len(values[:-2]) if len(values) > 2 else values[0]
            )

            if recent_avg > older_avg * 1.02:  # 2%以上の改善
                return "improving"
            elif recent_avg < older_avg * 0.98:  # 2%以上の悪化
                return "declining"
            else:
                return "stable"

        # カバレッジトレンド
        coverage_values = [item["coverage"] for item in historical_data] + [
            current_metrics["coverage"]
        ]
        coverage_trend = calculate_trend(coverage_values)

        # テスト成功率トレンド
        test_values = [item["test_success_rate"] for item in historical_data] + [
            current_metrics["test_success_rate"]
        ]
        test_trend = calculate_trend(test_values)

        # 全体健康度
        if coverage_trend == "improving" and test_trend == "improving":
            overall_health = "improving"
        elif coverage_trend == "declining" or test_trend == "declining":
            overall_health = "declining"
        else:
            overall_health = "stable"

        return {
            "coverage_trend": coverage_trend,
            "test_success_trend": test_trend,
            "overall_health": overall_health,
            "analysis_date": datetime.now().isoformat(),
        }

    def _extract_test_counts(self, output: str) -> tuple[int, int]:
        """テスト出力からテスト数を抽出"""
        passed = 0
        failed = 0

        passed_match = re.search(r"(\d+) passed", output)
        if passed_match:
            passed = int(passed_match.group(1))

        failed_match = re.search(r"(\d+) failed", output)
        if failed_match:
            failed = int(failed_match.group(1))

        return passed, failed
