"""
Decision Support System

完了報告を基に次のアクションを提案するシステム
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """アクションタイプ"""

    DEPLOY = "deploy"
    TEST = "test"
    REVIEW = "review"
    FOLLOWUP = "followup"
    ROLLBACK = "rollback"
    ESCALATE = "escalate"
    DOCUMENT = "document"
    CELEBRATE = "celebrate"
    MONITOR = "monitor"
    IMPROVE = "improve"


class DecisionSupportSystem:
    """意思決定支援システム"""

    def __init__(self):
        """初期化"""
        self.decision_history = []
        self.decision_rules = self._initialize_rules()
        logger.info("DecisionSupportSystem initialized")

    def _initialize_rules(self) -> Dict[str, Any]:
        """決定ルールを初期化"""
        return {
            "success_actions": {
                "high_quality_complete": [
                    ActionType.DEPLOY,
                    ActionType.DOCUMENT,
                    ActionType.CELEBRATE,
                ],
                "complete_with_issues": [
                    ActionType.TEST,
                    ActionType.REVIEW,
                    ActionType.FOLLOWUP,
                ],
                "partial_complete": [ActionType.FOLLOWUP, ActionType.REVIEW],
            },
            "failure_actions": {
                "critical_failure": [ActionType.ROLLBACK, ActionType.ESCALATE],
                "recoverable_failure": [ActionType.FOLLOWUP, ActionType.IMPROVE],
                "minor_failure": [ActionType.IMPROVE, ActionType.DOCUMENT],
            },
            "risk_thresholds": {"high": 0.7, "medium": 0.4, "low": 0.2},
        }

    def generate_decision(
        self,
        report: Dict[str, Any],
        analysis: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        完了報告と分析に基づいて決定を生成

        Args:
            report: 完了報告
            analysis: 分析結果
            context: 追加コンテキスト

        Returns:
            決定内容
        """
        try:
            decision = {
                "decision_id": f"decision_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "report_id": report.get("report_id"),
                "timestamp": datetime.now().isoformat(),
                "recommended_actions": [],
                "priority_order": [],
                "risk_assessment": {},
                "confidence_level": 0.0,
                "rationale": [],
                "prerequisites": [],
                "timeline": {},
            }

            # 状況を評価
            situation = self._assess_situation(report, analysis)
            decision["situation_assessment"] = situation

            # リスクを評価
            risk_assessment = self._assess_risks(report, analysis, situation)
            decision["risk_assessment"] = risk_assessment

            # 推奨アクションを決定
            actions = self._determine_actions(situation, risk_assessment, context)
            decision["recommended_actions"] = actions

            # 優先順位を決定
            priority_order = self._prioritize_actions(
                actions, situation, risk_assessment
            )
            decision["priority_order"] = priority_order

            # 信頼度を計算
            confidence = self._calculate_confidence(
                analysis, situation, risk_assessment
            )
            decision["confidence_level"] = confidence

            # 根拠を生成
            rationale = self._generate_rationale(situation, risk_assessment, actions)
            decision["rationale"] = rationale

            # 前提条件を特定
            prerequisites = self._identify_prerequisites(actions, report, context)
            decision["prerequisites"] = prerequisites

            # タイムラインを生成
            timeline = self._generate_timeline(actions, situation)
            decision["timeline"] = timeline

            # 履歴に追加
            self.decision_history.append(decision)

            return decision

        except Exception as e:
            logger.error(f"Failed to generate decision: {e}")
            return {"error": str(e), "report_id": report.get("report_id")}

    def _assess_situation(
        self, report: Dict[str, Any], analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        状況を評価

        Args:
            report: 完了報告
            analysis: 分析結果

        Returns:
            状況評価
        """
        situation = {
            "overall_status": "unknown",
            "success_level": "none",
            "completion_level": 0,
            "quality_level": "unknown",
            "urgency": "medium",
            "complexity": "medium",
        }

        # ステータスから全体状況を判断
        status = report.get("status", "")
        if status == "completed":
            situation["overall_status"] = "success"
            situation["success_level"] = "full"
        elif status == "partial":
            situation["overall_status"] = "partial_success"
            situation["success_level"] = "partial"
        elif status == "failed":
            situation["overall_status"] = "failure"
            situation["success_level"] = "none"

        # 完了度
        completeness = analysis.get("completeness", {})
        situation["completion_level"] = completeness.get("completion_percentage", 0)

        # 品質レベル
        quality = analysis.get("quality_score", {})
        overall_quality = quality.get("overall", 0)

        if overall_quality >= 80:
            situation["quality_level"] = "high"
        elif overall_quality >= 60:
            situation["quality_level"] = "medium"
        else:
            situation["quality_level"] = "low"

        # 緊急度
        priority = report.get("task_info", {}).get("priority", "MEDIUM")
        if priority == "CRITICAL":
            situation["urgency"] = "critical"
        elif priority == "HIGH":
            situation["urgency"] = "high"
        elif priority == "LOW":
            situation["urgency"] = "low"

        # 複雑度（デリバラブル数やメトリクス数から推定）
        deliverables = len(report.get("deliverables", []))
        metrics = len(report.get("metrics", {}))

        if deliverables > 10 or metrics > 10:
            situation["complexity"] = "high"
        elif deliverables < 3 and metrics < 3:
            situation["complexity"] = "low"

        return situation

    def _assess_risks(
        self,
        report: Dict[str, Any],
        analysis: Dict[str, Any],
        situation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        リスクを評価

        Args:
            report: 完了報告
            analysis: 分析結果
            situation: 状況評価

        Returns:
            リスク評価
        """
        risk_assessment = {
            "overall_risk_level": "medium",
            "risk_score": 0.5,
            "risk_factors": [],
            "mitigation_needed": False,
        }

        risk_score = 0.0
        risk_factors = []

        # 分析から特定されたリスク
        identified_risks = analysis.get("risk_factors", [])
        for risk in identified_risks:
            severity = risk.get("severity", "medium")

            if severity == "high":
                risk_score += 0.3
                risk_factors.append(risk)
            elif severity == "medium":
                risk_score += 0.2
                risk_factors.append(risk)
            elif severity == "low":
                risk_score += 0.1

        # 状況に基づくリスク
        if situation["overall_status"] == "failure":
            risk_score += 0.4
            risk_factors.append(
                {
                    "type": "task_failure",
                    "severity": "high",
                    "description": "Task failed to complete",
                }
            )

        if situation["quality_level"] == "low":
            risk_score += 0.2
            risk_factors.append(
                {
                    "type": "quality_issue",
                    "severity": "medium",
                    "description": "Low quality implementation",
                }
            )

        if situation["completion_level"] < 70:
            risk_score += 0.3
            risk_factors.append(
                {
                    "type": "incomplete_implementation",
                    "severity": "high",
                    "description": f'Only {situation["completion_level"]:.0f}% complete',
                }
            )

        # リスクレベルを決定
        risk_score = min(risk_score, 1.0)  # 最大1.0

        if risk_score >= self.decision_rules["risk_thresholds"]["high"]:
            risk_assessment["overall_risk_level"] = "high"
            risk_assessment["mitigation_needed"] = True
        elif risk_score >= self.decision_rules["risk_thresholds"]["medium"]:
            risk_assessment["overall_risk_level"] = "medium"
            risk_assessment["mitigation_needed"] = True
        else:
            risk_assessment["overall_risk_level"] = "low"

        risk_assessment["risk_score"] = risk_score
        risk_assessment["risk_factors"] = risk_factors

        return risk_assessment

    def _determine_actions(
        self,
        situation: Dict[str, Any],
        risk_assessment: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        推奨アクションを決定

        Args:
            situation: 状況評価
            risk_assessment: リスク評価
            context: 追加コンテキスト

        Returns:
            アクションリスト
        """
        actions = []

        # 成功/失敗に基づくアクション
        if situation["overall_status"] == "success":
            if (
                situation["quality_level"] == "high"
                and situation["completion_level"] >= 90
            ):
                # 高品質な完了
                action_types = self.decision_rules["success_actions"][
                    "high_quality_complete"
                ]
            elif risk_assessment["risk_factors"]:
                # 問題ありの完了
                action_types = self.decision_rules["success_actions"][
                    "complete_with_issues"
                ]
            else:
                # 通常の完了
                action_types = [ActionType.DEPLOY, ActionType.DOCUMENT]

        elif situation["overall_status"] == "partial_success":
            action_types = self.decision_rules["success_actions"]["partial_complete"]

        else:  # failure
            if risk_assessment["overall_risk_level"] == "high":
                action_types = self.decision_rules["failure_actions"][
                    "critical_failure"
                ]
            elif situation["urgency"] in ["critical", "high"]:
                action_types = self.decision_rules["failure_actions"][
                    "recoverable_failure"
                ]
            else:
                action_types = self.decision_rules["failure_actions"]["minor_failure"]

        # アクションを構築
        for action_type in action_types:
            action = self._build_action(
                action_type, situation, risk_assessment, context
            )
            if action:
                actions.append(action)

        # リスク軽減アクションを追加
        if risk_assessment["mitigation_needed"]:
            for risk in risk_assessment["risk_factors"][:3]:  # 最大3つ
                if risk.get("severity") in ["high", "medium"]:
                    mitigation_action = {
                        "type": ActionType.IMPROVE.value,
                        "title": f"Mitigate: {risk['type']}",
                        "description": risk.get(
                            "mitigation", "Address identified risk"
                        ),
                        "priority": "high" if risk["severity"] == "high" else "medium",
                        "estimated_effort": "medium",
                    }
                    actions.append(mitigation_action)

        return actions

    def _build_action(
        self,
        action_type: ActionType,
        situation: Dict[str, Any],
        risk_assessment: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        アクションを構築

        Args:
            action_type: アクションタイプ
            situation: 状況評価
            risk_assessment: リスク評価
            context: 追加コンテキスト

        Returns:
            アクション詳細
        """
        action_templates = {
            ActionType.DEPLOY: {
                "title": "Deploy to production",
                "description": "Deploy the completed implementation to production environment",
                "prerequisites": ["All tests passing", "Documentation complete"],
                "estimated_effort": "low",
            },
            ActionType.TEST: {
                "title": "Conduct thorough testing",
                "description": "Perform comprehensive testing to ensure quality",
                "prerequisites": ["Test environment ready"],
                "estimated_effort": "medium",
            },
            ActionType.REVIEW: {
                "title": "Conduct code review",
                "description": "Review implementation for quality and standards compliance",
                "prerequisites": ["Code complete"],
                "estimated_effort": "medium",
            },
            ActionType.FOLLOWUP: {
                "title": "Create follow-up tasks",
                "description": "Address incomplete items and improvements",
                "prerequisites": [],
                "estimated_effort": "low",
            },
            ActionType.ROLLBACK: {
                "title": "Rollback changes",
                "description": "Revert to previous stable state",
                "prerequisites": ["Backup available"],
                "estimated_effort": "high",
            },
            ActionType.ESCALATE: {
                "title": "Escalate to Elder Council",
                "description": "Escalate critical issues for senior decision",
                "prerequisites": [],
                "estimated_effort": "low",
            },
            ActionType.DOCUMENT: {
                "title": "Update documentation",
                "description": "Document implementation details and learnings",
                "prerequisites": [],
                "estimated_effort": "low",
            },
            ActionType.CELEBRATE: {
                "title": "Celebrate success",
                "description": "Recognize team achievement",
                "prerequisites": [],
                "estimated_effort": "low",
            },
            ActionType.MONITOR: {
                "title": "Monitor system",
                "description": "Set up monitoring for deployed changes",
                "prerequisites": ["Deployment complete"],
                "estimated_effort": "medium",
            },
            ActionType.IMPROVE: {
                "title": "Implement improvements",
                "description": "Apply lessons learned and fix identified issues",
                "prerequisites": [],
                "estimated_effort": "high",
            },
        }

        template = action_templates.get(action_type)
        if not template:
            return None

        action = {
            "type": action_type.value,
            "title": template["title"],
            "description": template["description"],
            "priority": "high"
            if situation["urgency"] in ["critical", "high"]
            else "medium",
            "prerequisites": template["prerequisites"],
            "estimated_effort": template["estimated_effort"],
            "rationale": self._generate_action_rationale(
                action_type, situation, risk_assessment
            ),
        }

        return action

    def _generate_action_rationale(
        self,
        action_type: ActionType,
        situation: Dict[str, Any],
        risk_assessment: Dict[str, Any],
    ) -> str:
        """
        アクションの根拠を生成

        Args:
            action_type: アクションタイプ
            situation: 状況評価
            risk_assessment: リスク評価

        Returns:
            根拠文字列
        """
        if action_type == ActionType.DEPLOY:
            return f"Task completed with {situation['completion_level']:.0f}% completion and {situation['quality_level']} quality"

        elif action_type == ActionType.TEST:
            return f"Additional testing needed due to {len(risk_assessment['risk_factors'])} identified risks"

        elif action_type == ActionType.ROLLBACK:
            return f"Critical failure with {risk_assessment['overall_risk_level']} risk level requires immediate rollback"

        elif action_type == ActionType.ESCALATE:
            return f"High risk situation ({risk_assessment['risk_score']:.2f}) requires senior decision"

        else:
            return f"Recommended based on {situation['overall_status']} status and {risk_assessment['overall_risk_level']} risk"

    def _prioritize_actions(
        self,
        actions: List[Dict[str, Any]],
        situation: Dict[str, Any],
        risk_assessment: Dict[str, Any],
    ) -> List[str]:
        """
        アクションの優先順位を決定

        Args:
            actions: アクションリスト
            situation: 状況評価
            risk_assessment: リスク評価

        Returns:
            優先順位付けされたアクションIDリスト
        """
        # 優先度スコアを計算
        scored_actions = []

        for i, action in enumerate(actions):
            score = 0.0

            # 基本優先度
            if action["priority"] == "high":
                score += 1.0
            elif action["priority"] == "medium":
                score += 0.5

            # 緊急度による調整
            if situation["urgency"] == "critical":
                if action["type"] in ["rollback", "escalate"]:
                    score += 2.0

            # リスクによる調整
            if risk_assessment["overall_risk_level"] == "high":
                if action["type"] in ["test", "review", "rollback"]:
                    score += 1.0

            # 努力量による調整（低い方が優先）
            if action["estimated_effort"] == "low":
                score += 0.3
            elif action["estimated_effort"] == "high":
                score -= 0.3

            scored_actions.append((i, score, action["title"]))

        # スコアでソート
        scored_actions.sort(key=lambda x: x[1], reverse=True)

        return [action[2] for action in scored_actions]

    def _calculate_confidence(
        self,
        analysis: Dict[str, Any],
        situation: Dict[str, Any],
        risk_assessment: Dict[str, Any],
    ) -> float:
        """
        決定の信頼度を計算

        Args:
            analysis: 分析結果
            situation: 状況評価
            risk_assessment: リスク評価

        Returns:
            信頼度（0-1）
        """
        confidence = 0.5  # 基本信頼度

        # 品質スコアによる調整
        quality = analysis.get("quality_score", {})
        overall_quality = quality.get("overall", 50) / 100
        confidence += overall_quality * 0.2

        # 完了度による調整
        completion = situation["completion_level"] / 100
        confidence += completion * 0.2

        # リスクによる調整
        risk_score = risk_assessment["risk_score"]
        confidence -= risk_score * 0.3

        # 成功/失敗による調整
        if situation["overall_status"] == "success":
            confidence += 0.1
        elif situation["overall_status"] == "failure":
            confidence -= 0.1

        # 0-1の範囲に制限
        confidence = max(0.0, min(1.0, confidence))

        return confidence

    def _generate_rationale(
        self,
        situation: Dict[str, Any],
        risk_assessment: Dict[str, Any],
        actions: List[Dict[str, Any]],
    ) -> List[str]:
        """
        決定の根拠を生成

        Args:
            situation: 状況評価
            risk_assessment: リスク評価
            actions: アクションリスト

        Returns:
            根拠リスト
        """
        rationale = []

        # 状況に基づく根拠
        rationale.append(
            f"Task {situation['overall_status']} with {situation['completion_level']:.0f}% completion"
        )

        # 品質に基づく根拠
        rationale.append(
            f"Quality level is {situation['quality_level']}, which impacts deployment readiness"
        )

        # リスクに基づく根拠
        if risk_assessment["risk_factors"]:
            rationale.append(
                f"Identified {len(risk_assessment['risk_factors'])} risk factors requiring attention"
            )

        # アクションに基づく根拠
        if actions:
            primary_actions = [a["type"] for a in actions[:2]]
            rationale.append(
                f"Recommended actions ({', '.join(primary_actions)}) address current priorities"
            )

        return rationale

    def _identify_prerequisites(
        self,
        actions: List[Dict[str, Any]],
        report: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        前提条件を特定

        Args:
            actions: アクションリスト
            report: 完了報告
            context: 追加コンテキスト

        Returns:
            前提条件リスト
        """
        prerequisites = set()

        # アクションの前提条件を収集
        for action in actions:
            for prereq in action.get("prerequisites", []):
                prerequisites.add(prereq)

        # 状況に基づく追加の前提条件
        if report.get("status") == "partial":
            prerequisites.add("Complete missing requirements")

        if report.get("issues_encountered"):
            prerequisites.add("Resolve identified issues")

        # コンテキストからの前提条件
        if context:
            if context.get("requires_approval"):
                prerequisites.add("Obtain necessary approvals")

            if context.get("dependencies"):
                prerequisites.add("Ensure dependencies are met")

        return list(prerequisites)

    def _generate_timeline(
        self, actions: List[Dict[str, Any]], situation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        タイムラインを生成

        Args:
            actions: アクションリスト
            situation: 状況評価

        Returns:
            タイムライン
        """
        timeline = {
            "immediate": [],  # 24時間以内
            "short_term": [],  # 1週間以内
            "medium_term": [],  # 1ヶ月以内
            "long_term": [],  # それ以降
        }

        # 緊急度による調整
        urgency_factor = 1.0
        if situation["urgency"] == "critical":
            urgency_factor = 0.5
        elif situation["urgency"] == "high":
            urgency_factor = 0.7
        elif situation["urgency"] == "low":
            urgency_factor = 1.5

        # アクションを時間枠に割り当て
        for action in actions:
            effort = action.get("estimated_effort", "medium")

            # 努力量と緊急度から時間枠を決定
            if action["type"] in ["rollback", "escalate"]:
                timeline["immediate"].append(action["title"])

            elif effort == "low":
                if urgency_factor <= 0.7:
                    timeline["immediate"].append(action["title"])
                else:
                    timeline["short_term"].append(action["title"])

            elif effort == "medium":
                if urgency_factor <= 0.7:
                    timeline["short_term"].append(action["title"])
                else:
                    timeline["medium_term"].append(action["title"])

            else:  # high effort
                if urgency_factor <= 0.7:
                    timeline["medium_term"].append(action["title"])
                else:
                    timeline["long_term"].append(action["title"])

        return timeline

    def get_decision_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        決定履歴を取得

        Args:
            limit: 取得件数

        Returns:
            決定履歴リスト
        """
        return self.decision_history[-limit:][::-1]
