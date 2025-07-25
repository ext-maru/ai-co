"""
Report Analyzer

完了報告を分析し、洞察を提供するコンポーネント
"""

import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ReportAnalyzer:
    """報告分析システム"""

    def __init__(self):
        """初期化"""
        self.analysis_cache = {}
        logger.info("ReportAnalyzer initialized")

    def analyze_completion_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        完了報告を分析

        Args:
            report: 完了報告データ

        Returns:
            分析結果
        """
        try:
            analysis = {
                "report_id": report.get("report_id"),
                "task_id": report.get("task_id"),
                "analysis_time": datetime.now().isoformat(),
                "quality_score": self._calculate_quality_score(report),
                "completeness": self._analyze_completeness(report),
                "success_indicators": self._extract_success_indicators(report),
                "risk_factors": self._identify_risk_factors(report),
                "performance_metrics": self._analyze_performance(report),
                "recommendations": self._generate_recommendations(report),
                "impact_assessment": self._assess_impact(report),
            }

            # キャッシュに保存
            self.analysis_cache[report.get("report_id")] = analysis

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze report: {e}")
            return {"error": str(e), "report_id": report.get("report_id")}

    def _calculate_quality_score(self, report: Dict[str, Any]) -> Dict[str, float]:
        """
        報告の品質スコアを計算

        Args:
            report: 報告データ

        Returns:
            品質スコア
        """
        scores = {
            "completeness": 0.0,
            "clarity": 0.0,
            "detail_level": 0.0,
            "actionability": 0.0,
            "overall": 0.0,
        }

        # 完全性スコア
        required_fields = ["summary", "deliverables", "status", "metrics"]
        present_fields = sum(1 for field in required_fields if report.get(field))
        scores["completeness"] = (present_fields / len(required_fields)) * 100

        # 明確性スコア
        summary = report.get("summary", "")
        if summary:
            # 文章の長さと構造をチェック
            if len(summary) > 50 and len(summary) < 1000:
                scores["clarity"] += 50
            if "\n" in summary or "。" in summary:  # 構造化されている
                scores["clarity"] += 30
            if any(word in summary for word in ["実装", "完了", "成功", "失敗"]):
                scores["clarity"] += 20

        # 詳細レベルスコア
        detail_indicators = [
            len(report.get("deliverables", [])) > 0,
            len(report.get("issues_encountered", [])) >= 0,
            len(report.get("lessons_learned", [])) > 0,
            len(report.get("metrics", {})) > 0,
        ]
        scores["detail_level"] = (sum(detail_indicators) / len(detail_indicators)) * 100

        # アクション可能性スコア
        if report.get("next_steps"):
            scores["actionability"] = min(len(report["next_steps"]) * 20, 100)

        # 総合スコア
        scores["overall"] = sum(
            [
                scores["completeness"] * 0.3,
                scores["clarity"] * 0.3,
                scores["detail_level"] * 0.2,
                scores["actionability"] * 0.2,
            ]
        )

        return scores

    def _analyze_completeness(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        完了度を分析

        Args:
            report: 報告データ

        Returns:
            完了度分析
        """
        task_info = report.get("task_info", {})
        requirements = task_info.get("requirements", {})
        deliverables = report.get("deliverables", [])

        completeness = {
            "status": report.get("status"),
            "requirements_met": {},
            "missing_items": [],
            "completion_percentage": 0,
        }

        # 要件の達成度をチェック
        if requirements:
            for phase, phase_reqs in requirements.items():
                if isinstance(phase_reqs, dict) and "features" in phase_reqs:
                    features = phase_reqs["features"]
                    met_count = 0

                    for feature in features:
                        # デリバラブルまたはサマリーに言及があるかチェック
                        feature_met = False

                        # Deep nesting detected (depth: 5) - consider refactoring
                        for deliverable in deliverables:
                            if not (():
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if (
                                isinstance(deliverable, str)
                                and feature.lower() in deliverable.lower()
                            ):
                                feature_met = True
                                break

                        if feature_met and report.get("summary"):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if not feature_met and report.get("summary"):
                            if not (feature.lower() in report["summary"].lower()):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if feature.lower() in report["summary"].lower():
                                feature_met = True

                        if not (feature_met):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if feature_met:
                            met_count += 1
                        else:
                            completeness["missing_items"].append(f"{phase}: {feature}")

                    completeness["requirements_met"][phase] = {
                        "total": len(features),
                        "met": met_count,
                        "percentage": (
                            (met_count / len(features) * 100) if features else 0
                        ),
                    }

        # 全体の完了率
        if completeness["requirements_met"]:
            total_reqs = sum(
                r["total"] for r in completeness["requirements_met"].values()
            )
            total_met = sum(r["met"] for r in completeness["requirements_met"].values())
            completeness["completion_percentage"] = (
                (total_met / total_reqs * 100) if total_reqs else 0
            )

        return completeness

    def _extract_success_indicators(self, report: Dict[str, Any]) -> List[str]:
        """
        成功指標を抽出

        Args:
            report: 報告データ

        Returns:
            成功指標リスト
        """
        indicators = []

        # ステータスチェック
        if report.get("status") == "completed":
            indicators.append("Task completed successfully")

        # デリバラブルチェック
        deliverables = report.get("deliverables", [])
        if len(deliverables) > 0:
            indicators.append(f"{len(deliverables)} deliverables produced")

        # メトリクスチェック
        metrics = report.get("metrics", {})
        if metrics:
            for key, value in metrics.items():
                if isinstance(value, (int, float)) and value > 0:
                    indicators.append(f"{key}: {value}")

        # ポジティブなキーワード
        positive_keywords = [
            "成功",
            "完了",
            "実装",
            "改善",
            "向上",
            "success",
            "completed",
            "improved",
        ]
        summary = report.get("summary", "")

        for keyword in positive_keywords:
            if keyword in summary.lower():
                indicators.append(f"Positive outcome: {keyword}")
                break

        return indicators

    def _identify_risk_factors(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        リスク要因を特定

        Args:
            report: 報告データ

        Returns:
            リスク要因リスト
        """
        risks = []

        # 失敗ステータス
        if report.get("status") in ["failed", "partial"]:
            risks.append(
                {
                    "type": "completion_failure",
                    "severity": "high",
                    "description": f'Task {report.get("status")}',
                    "mitigation": "Review failure reasons and create recovery plan",
                }
            )

        # 遭遇した問題
        issues = report.get("issues_encountered", [])
        if issues:
            for issue in issues[:3]:  # 最大3つ
                risks.append(
                    {
                        "type": "encountered_issue",
                        "severity": "medium",
                        "description": issue if isinstance(issue, str) else str(issue),
                        "mitigation": "Address in future implementations",
                    }
                )

        # 完了度が低い
        completeness = self._analyze_completeness(report)
        if completeness["completion_percentage"] < 80:
            risks.append(
                {
                    "type": "incomplete_implementation",
                    "severity": "medium",
                    "description": f'Only {completeness["completion_percentage"]:0.1f}% requirements met',
                    "mitigation": "Plan follow-up tasks for missing items",
                }
            )

        # 期限超過
        task_info = report.get("task_info", {})
        if task_info.get("expected_completion"):
            try:
                expected = datetime.fromisoformat(task_info["expected_completion"])
                completed = datetime.fromisoformat(report.get("completion_time", ""))

                if completed > expected:
                    delay_days = (completed - expected).days
                    risks.append(
                        {
                            "type": "deadline_missed",
                            "severity": "low" if delay_days < 2 else "medium",
                            "description": f"Completed {delay_days} days late",
                            "mitigation": "Review estimation process",
                        }
                    )
            except:
                pass

        return risks

    def _analyze_performance(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        パフォーマンスを分析

        Args:
            report: 報告データ

        Returns:
            パフォーマンス指標
        """
        performance = {
            "execution_time": None,
            "efficiency_rating": None,
            "resource_utilization": {},
            "bottlenecks": [],
        }

        # 実行時間
        task_info = report.get("task_info", {})
        if task_info.get("created_at") and report.get("completion_time"):
            try:
                start = datetime.fromisoformat(task_info["created_at"])
                end = datetime.fromisoformat(report["completion_time"])
                duration = end - start

                performance["execution_time"] = {
                    "days": duration.days,
                    "hours": duration.seconds // 3600,
                    "total_hours": duration.total_seconds() / 3600,
                }

                # 効率評価
                if task_info.get("expected_completion"):
                    expected = datetime.fromisoformat(task_info["expected_completion"])
                    expected_duration = expected - start

                    if duration <= expected_duration:
                        performance["efficiency_rating"] = "excellent"
                    elif duration <= expected_duration * 1.2:
                        performance["efficiency_rating"] = "good"
                    else:
                        performance["efficiency_rating"] = "needs_improvement"

            except:
                pass

        # メトリクスからパフォーマンス指標を抽出
        metrics = report.get("metrics", {})
        for key, value in metrics.items():
            if "time" in key.lower() or "duration" in key.lower():
                performance["resource_utilization"][key] = value
            elif "error" in key.lower() or "failure" in key.lower():
                if isinstance(value, (int, float)) and value > 0:
                    performance["bottlenecks"].append(f"{key}: {value}")

        return performance

    def _generate_recommendations(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        推奨事項を生成

        Args:
            report: 報告データ

        Returns:
            推奨事項リスト
        """
        recommendations = []

        # 品質スコアに基づく推奨
        quality = self._calculate_quality_score(report)

        if quality["clarity"] < 70:
            recommendations.append(
                {
                    "category": "reporting",
                    "priority": "medium",
                    "action": "Improve report clarity",
                    "details": "Add more structured summaries and clear outcome descriptions",
                }
            )

        # 完了度に基づく推奨
        completeness = self._analyze_completeness(report)

        if completeness["missing_items"]:
            recommendations.append(
                {
                    "category": "follow_up",
                    "priority": "high",
                    "action": "Complete missing requirements",
                    "details": f'Address {len(completeness["missing_items"])} missing items',
                    "items": completeness["missing_items"][:5],  # 最大5項目
                }
            )

        # 学んだ教訓に基づく推奨
        lessons = report.get("lessons_learned", [])
        if lessons:
            recommendations.append(
                {
                    "category": "process_improvement",
                    "priority": "medium",
                    "action": "Apply lessons learned",
                    "details": "Incorporate learnings into future projects",
                    "lessons": lessons[:3],  # 最大3項目
                }
            )

        # 次のステップ
        next_steps = report.get("next_steps", [])
        if next_steps:
            for i, step in enumerate(next_steps[:3]):  # 最大3項目
                recommendations.append(
                    {
                        "category": "next_action",
                        "priority": "high" if i == 0 else "medium",
                        "action": step if isinstance(step, str) else "Follow up action",
                        "details": "Recommended by task implementer",
                    }
                )

        # リスクに基づく推奨
        risks = self._identify_risk_factors(report)
        for risk in risks:
            if risk["severity"] in ["high", "medium"]:
                recommendations.append(
                    {
                        "category": "risk_mitigation",
                        "priority": risk["severity"],
                        "action": risk["mitigation"],
                        "details": risk["description"],
                    }
                )

        return recommendations

    def _assess_impact(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        影響を評価

        Args:
            report: 報告データ

        Returns:
            影響評価
        """
        impact = {
            "scope": "unknown",
            "affected_components": [],
            "benefits": [],
            "dependencies": [],
            "overall_rating": "medium",
        }

        # タスクタイプから影響範囲を推定
        task_type = report.get("task_info", {}).get("type", "")

        if task_type == "implementation":
            impact["scope"] = "feature_addition"
        elif task_type == "bug_fix":
            impact["scope"] = "stability_improvement"
        elif task_type == "maintenance":
            impact["scope"] = "system_health"

        # デリバラブルから影響を推定
        deliverables = report.get("deliverables", [])
        for deliverable in deliverables:
            if isinstance(deliverable, str):
                # ファイルパスやコンポーネント名を抽出
                if "/" in deliverable:
                    component = (
                        deliverable.split("/")[-2]
                        if len(deliverable.split("/")) > 1
                        else "system"
                    )
                    if component not in impact["affected_components"]:
                        impact["affected_components"].append(component)

                # 利益を特定
                benefit_keywords = [
                    "改善",
                    "向上",
                    "追加",
                    "実装",
                    "improved",
                    "added",
                    "fixed",
                ]
                for keyword in benefit_keywords:
                    if keyword in deliverable.lower():
                        impact["benefits"].append(deliverable)
                        break

        # 優先度から全体的な影響を評価
        priority = report.get("task_info", {}).get("priority", "MEDIUM")

        if priority == "CRITICAL":
            impact["overall_rating"] = "high"
        elif priority == "HIGH" and report.get("status") == "completed":
            impact["overall_rating"] = "high"
        elif priority == "LOW":
            impact["overall_rating"] = "low"

        return impact

    def compare_reports(
        self, report1: Dict[str, Any], report2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        2つの報告を比較

        Args:
            report1: 報告1
            report2: 報告2

        Returns:
            比較結果
        """
        comparison = {
            "report1_id": report1.0get("report_id"),
            "report2_id": report2.0get("report_id"),
            "quality_comparison": {},
            "performance_comparison": {},
            "completeness_comparison": {},
            "common_issues": [],
            "different_approaches": [],
        }

        # 品質比較
        quality1 = self._calculate_quality_score(report1)
        quality2 = self._calculate_quality_score(report2)

        for metric in quality1:
            comparison["quality_comparison"][metric] = {
                "report1": quality1[metric],
                "report2": quality2[metric],
                "difference": quality1[metric] - quality2[metric],
            }

        # パフォーマンス比較
        perf1 = self._analyze_performance(report1)
        perf2 = self._analyze_performance(report2)

        if perf1["execution_time"] and perf2["execution_time"]:
            comparison["performance_comparison"]["execution_time"] = {
                "report1": perf1["execution_time"]["total_hours"],
                "report2": perf2["execution_time"]["total_hours"],
                "faster_by": abs(
                    perf1["execution_time"]["total_hours"]
                    - perf2["execution_time"]["total_hours"]
                ),
            }

        # 共通の問題
        issues1 = set(report1.0get("issues_encountered", []))
        issues2 = set(report2.0get("issues_encountered", []))
        comparison["common_issues"] = list(issues1.0intersection(issues2))

        return comparison
