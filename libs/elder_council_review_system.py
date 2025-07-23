#!/usr/bin/env python3
"""
Elder Council Review System - エルダー評議会報告審査システム
高品質な報告のみを4賢者へ反映するための品質管理システム
"""

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

# Import ReportEnhancer and SagePropagationEngine
try:
    from .report_enhancer import ReportEnhancer
    from .sage_propagation_engine import SagePropagationEngine
except ImportError:
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from report_enhancer import ReportEnhancer
    from sage_propagation_engine import SagePropagationEngine

logger = logging.getLogger(__name__)


class ReviewStatus(Enum):
    """審査ステータス"""

    PENDING = "pending"
    NEEDS_IMPROVEMENT = "needs_improvement"
    APPROVED = "approved"
    REJECTED = "rejected"


class PropagationTarget(Enum):
    """4賢者への反映対象"""

    KNOWLEDGE_SAGE = "knowledge_sage"
    INCIDENT_SAGE = "incident_sage"
    TASK_SAGE = "task_sage"
    RAG_SAGE = "rag_sage"


@dataclass
class QualityScore:
    """品質スコア"""

    clarity: float  # 明確性
    completeness: float  # 完全性
    actionability: float  # 実行可能性
    overall: float  # 総合スコア

    def meets_criteria(self, criteria: Dict) -> bool:
        """基準を満たしているか判定"""
        return (
            self.clarity >= criteria["clarity"]["min_score"]
            and self.completeness >= criteria["completeness"]["min_score"]
            and self.actionability >= criteria["actionability"]["min_score"]
        )


@dataclass
class ReviewResult:
    """審査結果"""

    status: ReviewStatus
    quality_score: QualityScore
    issues: List[str]
    suggestions: List[str]
    propagation_targets: List[PropagationTarget]
    enhanced_report: Optional[Dict] = None


class CouncilReviewCriteria:
    """エルダー評議会審査基準"""

    # 報告品質基準
    QUALITY_CRITERIA = {
        "clarity": {
            "min_score": 0.8,
            "checks": ["具体性", "明確性", "構造化"],
            "weight": 0.3,
        },
        "completeness": {
            "min_score": 0.9,
            "checks": ["5W1H", "根拠", "影響範囲"],
            "weight": 0.4,
        },
        "actionability": {
            "min_score": 0.7,
            "checks": ["実行可能性", "期限", "担当者"],
            "weight": 0.3,
        },
    }

    # 4賢者反映基準
    PROPAGATION_CRITERIA = {
        PropagationTarget.INCIDENT_SAGE: {
            "required_conditions": [
                "エラー・障害の明確な記載",
                "影響範囲の特定",
                "緊急度の判定",
            ],
            "keywords": ["error", "エラー", "障害", "failure", "exception", "incident"],
        },
        PropagationTarget.TASK_SAGE: {
            "required_conditions": [
                "具体的なアクション",
                "実行可能な粒度",
                "優先順位の明確化",
            ],
            "keywords": ["task", "タスク", "TODO", "実装", "修正", "改善", "必要"],
        },
        PropagationTarget.KNOWLEDGE_SAGE: {
            "required_conditions": [
                "再利用可能な知見",
                "一般化された学習",
                "将来への適用可能性",
            ],
            "keywords": ["学習", "知見", "ナレッジ", "ノウハウ", "解決策", "方法"],
        },
        PropagationTarget.RAG_SAGE: {
            "required_conditions": [
                "検索可能なキーワード",
                "関連文書との紐付け",
                "コンテキスト情報",
            ],
            "keywords": [],  # RAGは全ての承認済み報告を対象
        },
    }

    def __init__(self):
        """初期化メソッド"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def evaluate_report(self, report: Dict) -> ReviewResult:
        """報告書を評価"""
        self.logger.info(f"Evaluating report: {report.get('title', 'Untitled')}")

        # 品質スコアの算出
        quality_score = self._calculate_quality_score(report)

        # 問題点の抽出
        issues = self._identify_issues(report, quality_score)

        # 改善提案の生成
        suggestions = self._generate_suggestions(report, issues)

        # ステータスの判定
        status = self._determine_status(quality_score, issues)

        # 反映対象の判定
        propagation_targets = []
        if status == ReviewStatus.APPROVED:
            propagation_targets = self._determine_propagation_targets(report)

        return ReviewResult(
            status=status,
            quality_score=quality_score,
            issues=issues,
            suggestions=suggestions,
            propagation_targets=propagation_targets,
        )

    def _calculate_quality_score(self, report: Dict) -> QualityScore:
        """品質スコアを計算"""
        content = report.get("content", "")

        # 明確性スコア
        clarity_score = self._evaluate_clarity(content)

        # 完全性スコア
        completeness_score = self._evaluate_completeness(report)

        # 実行可能性スコア
        actionability_score = self._evaluate_actionability(report)

        # 総合スコア（重み付き平均）
        overall_score = (
            clarity_score * self.QUALITY_CRITERIA["clarity"]["weight"]
            + completeness_score * self.QUALITY_CRITERIA["completeness"]["weight"]
            + actionability_score * self.QUALITY_CRITERIA["actionability"]["weight"]
        )

        return QualityScore(
            clarity=clarity_score,
            completeness=completeness_score,
            actionability=actionability_score,
            overall=overall_score,
        )

    def _evaluate_clarity(self, content: str) -> float:
        """明確性を評価"""
        score = 1.0

        # 曖昧な表現のチェック
        ambiguous_patterns = [
            r"多分|おそらく|かもしれない|思われる",
            r"など|等|その他",
            r"いくつか|複数|様々な",
        ]

        for pattern in ambiguous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                score -= 0.1

        # 具体的な数値や固有名詞の存在チェック
        if re.search(r"\d+", content):
            score += 0.1

        # 構造化されているか（箇条書き、見出しなど）
        if re.search(r"^[#\-\*\d]+\s", content, re.MULTILINE):
            score += 0.1

        return max(0.0, min(1.0, score))

    def _evaluate_completeness(self, report: Dict) -> float:
        """完全性を評価"""
        score = 0.0
        required_fields = ["title", "content", "category", "priority"]

        # 必須フィールドの存在チェック
        for field in required_fields:
            if field in report and report[field]:
                score += 0.2

        content = report.get("content", "")

        # 5W1Hのチェック
        w_patterns = {
            "what": r"何|what|エラー|問題|issue",
            "when": r"いつ|when|時間|日時|\d{4}[-/]\d{2}[-/]\d{2}",
            "where": r"どこ|where|場所|ファイル|システム|コンポーネント",
            "why": r"なぜ|why|原因|理由|because",
            "how": r"どのように|how|方法|手順|ステップ",
        }

        for w_type, pattern in w_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                score += 0.1

        return max(0.0, min(1.0, score))

    def _evaluate_actionability(self, report: Dict) -> float:
        """実行可能性を評価"""
        score = 0.5
        content = report.get("content", "")

        # アクション関連キーワードの存在
        action_keywords = [
            r"実装|implement",
            r"修正|fix",
            r"調査|investigate",
            r"確認|check|verify",
            r"作成|create",
            r"更新|update",
        ]

        for keyword in action_keywords:
            if re.search(keyword, content, re.IGNORECASE):
                score += 0.1

        # 期限の明記
        if re.search(r"期限|deadline|まで|by", content):
            score += 0.2

        # 担当者の明記
        if re.search(r"担当|assign|責任者|owner", content):
            score += 0.2

        return max(0.0, min(1.0, score))

    def _identify_issues(self, report: Dict, quality_score: QualityScore) -> List[str]:
        """問題点を特定"""
        issues = []

        if quality_score.clarity < self.QUALITY_CRITERIA["clarity"]["min_score"]:
            issues.append("報告内容が曖昧で具体性に欠ける")

        if (
            quality_score.completeness
            < self.QUALITY_CRITERIA["completeness"]["min_score"]
        ):
            issues.append("必要な情報（5W1H）が不足している")

        if (
            quality_score.actionability
            < self.QUALITY_CRITERIA["actionability"]["min_score"]
        ):
            issues.append("実行可能なアクションが不明確")

        # 必須フィールドチェック
        required_fields = ["title", "content", "category", "priority"]
        for field in required_fields:
            if field not in report or not report[field]:
                issues.append(f"必須フィールド '{field}' が未設定")

        return issues

    def _generate_suggestions(self, report: Dict, issues: List[str]) -> List[str]:
        """改善提案を生成"""
        suggestions = []

        for issue in issues:
            if "曖昧" in issue:
                suggestions.append(
                    "具体的な数値、日時、エラーメッセージを記載してください"
                )
            elif "5W1H" in issue:
                suggestions.append(
                    "いつ・どこで・何が・なぜ・どのように発生したかを明記してください"
                )
            elif "アクション" in issue:
                suggestions.append("具体的な対応策と実行者、期限を設定してください")
            elif "必須フィールド" in issue:
                field = issue.split("'")[1]
                suggestions.append(f"{field}フィールドを設定してください")

        return suggestions

    def _determine_status(
        self, quality_score: QualityScore, issues: List[str]
    ) -> ReviewStatus:
        """審査ステータスを決定"""
        if not issues and quality_score.meets_criteria(self.QUALITY_CRITERIA):
            return ReviewStatus.APPROVED
        elif quality_score.overall < 0.5:
            return ReviewStatus.REJECTED
        else:
            return ReviewStatus.NEEDS_IMPROVEMENT

    def _determine_propagation_targets(self, report: Dict) -> List[PropagationTarget]:
        """4賢者への反映対象を決定"""
        targets = []
        content = report.get("content", "").lower()
        category = report.get("category", "").lower()

        # 各賢者への反映判定
        for target, criteria in self.PROPAGATION_CRITERIA.items():
            # カテゴリマッチング
            if category in target.value:
                targets.append(target)
                continue

            # キーワードマッチング
            for keyword in criteria["keywords"]:
                if keyword.lower() in content:
                    targets.append(target)
                    break

        # ナレッジ賢者は常に対象（アーカイブ目的）
        if PropagationTarget.KNOWLEDGE_SAGE not in targets:
            targets.append(PropagationTarget.KNOWLEDGE_SAGE)

        # RAG賢者も承認済みは常に対象
        if PropagationTarget.RAG_SAGE not in targets:
            targets.append(PropagationTarget.RAG_SAGE)

        return targets


class ElderCouncilReviewSystem:
    """エルダー評議会報告審査システム"""

    def __init__(self):
        """初期化メソッド"""
        self.criteria = CouncilReviewCriteria()
        self.enhancer = ReportEnhancer()
        self.propagation_engine = SagePropagationEngine()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.report_storage_path = (
            "/home/aicompany/ai_co/knowledge_base/council_reports"
        )

    def submit_report(self, report: Dict) -> Tuple[str, ReviewResult]:
        """評議会への報告提出"""
        report_id = self._generate_report_id()
        self.logger.info(f"Report submitted: {report_id}")

        # 基本検証
        if not self._validate_basic_structure(report):
            return report_id, ReviewResult(
                status=ReviewStatus.REJECTED,
                quality_score=QualityScore(0, 0, 0, 0),
                issues=["報告書の基本構造が不正です"],
                suggestions=["正しいフォーマットで再提出してください"],
                propagation_targets=[],
            )

        # 評議会での審査
        review_result = self.criteria.evaluate_report(report)

        # ステータスに応じた処理
        if review_result.status == ReviewStatus.NEEDS_IMPROVEMENT:
            self.logger.info(
                f"Report {report_id} needs improvement, attempting enhancement"
            )

            # ReportEnhancerによる自動改善
            enhanced_report = self.enhancer.enhance_report(report)
            review_result.enhanced_report = enhanced_report

            # 改善後の再評価
            re_review_result = self.criteria.evaluate_report(enhanced_report)

            if re_review_result.status == ReviewStatus.APPROVED:
                self.logger.info(
                    f"Report {report_id} improved and approved after enhancement"
                )
                review_result = re_review_result
                review_result.enhanced_report = enhanced_report
            else:
                self.logger.info(
                    f"Report {report_id} still needs manual improvement after enhancement"
                )
                # 元の結果に改善版を付加
                review_result.enhanced_report = enhanced_report

        elif review_result.status == ReviewStatus.APPROVED:
            self.logger.info(f"Report {report_id} approved for propagation")

            # 4賢者への反映実行
            final_report = (
                review_result.enhanced_report
                if review_result.enhanced_report
                else report
            )
            propagation_result = self.propagation_engine.propagate_to_sages(
                final_report,
                [target.value for target in review_result.propagation_targets],
                report_id,
            )

            if propagation_result.success:
                self.logger.info(
                    f"Successfully propagated {report_id} to {len(propagation_result.actions_executed)} sages"
                )
            else:
                self.logger.warning(
                    f"Propagation partially failed for {report_id}: {propagation_result.errors}"
                )
        else:
            self.logger.warning(f"Report {report_id} rejected")

        # 審査結果の記録
        self._record_review_result(report_id, report, review_result)

        return report_id, review_result

    def _generate_report_id(self) -> str:
        """報告IDを生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"council_{timestamp}"

    def _validate_basic_structure(self, report: Dict) -> bool:
        """基本構造を検証"""
        required_keys = ["title", "content"]
        return all(key in report for key in required_keys)

    def _record_review_result(self, report_id: str, report: Dict, result: ReviewResult):
        """審査結果を記録"""
        record = {
            "report_id": report_id,
            "timestamp": datetime.now().isoformat(),
            "original_report": report,
            "review_result": {
                "status": result.status.value,
                "quality_score": {
                    "clarity": result.quality_score.clarity,
                    "completeness": result.quality_score.completeness,
                    "actionability": result.quality_score.actionability,
                    "overall": result.quality_score.overall,
                },
                "issues": result.issues,
                "suggestions": result.suggestions,
                "propagation_targets": [t.value for t in result.propagation_targets],
            },
        }

        # TODO: 実際のストレージ実装
        self.logger.info(
            f"Review result recorded: {json.dumps(record, ensure_ascii=False, indent=2)}"
        )
