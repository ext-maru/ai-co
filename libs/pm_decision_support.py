#!/usr/bin/env python3
"""
PM意思決定支援システム - データ駆動型のプロジェクト管理意思決定

過去のプロジェクトデータ、実行結果、品質指標を分析し、
PMの意思決定をサポートするインテリジェントなシステム
"""

import json
import logging
import sqlite3
import statistics

# プロジェクトルートをPythonパスに追加
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import BaseManager

logger = logging.getLogger(__name__)


class DecisionType(Enum):
    """意思決定タイプ"""

    RESOURCE_ALLOCATION = "resource_allocation"  # リソース配分
    TASK_PRIORITIZATION = "task_prioritization"  # タスク優先度
    QUALITY_GATE = "quality_gate"  # 品質ゲート
    TIMELINE_ADJUSTMENT = "timeline_adjustment"  # スケジュール調整
    RISK_MITIGATION = "risk_mitigation"  # リスク軽減
    TEAM_ASSIGNMENT = "team_assignment"  # チーム配属
    TECHNOLOGY_CHOICE = "technology_choice"  # 技術選択
    SCOPE_CHANGE = "scope_change"  # スコープ変更


class DecisionUrgency(Enum):
    """意思決定の緊急度"""

    LOW = "low"  # 低: 1週間以内
    MEDIUM = "medium"  # 中: 1日以内
    HIGH = "high"  # 高: 数時間以内
    CRITICAL = "critical"  # 緊急: 即座に


class ConfidenceLevel(Enum):
    """信頼度レベル"""

    VERY_LOW = "very_low"  # 30%未満
    LOW = "low"  # 30-50%
    MEDIUM = "medium"  # 50-70%
    HIGH = "high"  # 70-90%
    VERY_HIGH = "very_high"  # 90%以上


@dataclass
class DecisionRecommendation:
    """意思決定推奨事項"""

    decision_id: str
    decision_type: DecisionType
    urgency: DecisionUrgency
    confidence: ConfidenceLevel
    recommendation: str
    reasoning: str
    supporting_data: Dict[str, Any]
    alternatives: List[str]
    risks: List[str]
    benefits: List[str]
    estimated_impact: float  # -1.0 to 1.0
    created_at: datetime


@dataclass
class ProjectMetrics:
    """プロジェクトメトリクス"""

    project_id: str
    completion_rate: float
    quality_score: float
    timeline_adherence: float
    resource_efficiency: float
    team_satisfaction: float
    defect_rate: float
    rework_rate: float
    cost_variance: float


class PMDecisionSupport(BaseManager):
    """PM意思決定支援システム"""

    def __init__(self):
        super().__init__("PMDecisionSupport")
        self.db_path = PROJECT_ROOT / "db" / "pm_decisions.db"

        # 分析のための重み設定
        self.metric_weights = {
            "completion_rate": 0.25,
            "quality_score": 0.20,
            "timeline_adherence": 0.15,
            "resource_efficiency": 0.15,
            "team_satisfaction": 0.10,
            "defect_rate": 0.10,
            "rework_rate": 0.05,
        }

        # 意思決定しきい値
        self.decision_thresholds = {
            DecisionType.RESOURCE_ALLOCATION: {
                "resource_efficiency": 0.6,  # 60%未満で警告
                "timeline_adherence": 0.7,
            },
            DecisionType.TASK_PRIORITIZATION: {
                "completion_rate": 0.8,
                "quality_score": 0.7,
            },
            DecisionType.QUALITY_GATE: {
                "defect_rate": 0.05,  # 5%以上で警告
                "quality_score": 0.8,
            },
            DecisionType.TIMELINE_ADJUSTMENT: {
                "timeline_adherence": 0.7,
                "completion_rate": 0.6,
            },
        }

        # 履歴データストレージ
        self.decision_history: List[DecisionRecommendation] = []
        self.project_metrics_cache: Dict[str, ProjectMetrics] = {}

        self.initialize()

    def initialize(self) -> bool:
        """初期化処理"""
        try:
            self._init_database()
            self._load_historical_data()
            return True
        except Exception as e:
            self.handle_error(e, "初期化")
            return False

    def _init_database(self):
        """データベース初期化"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            # 意思決定推奨テーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS decision_recommendations (
                    decision_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    decision_type TEXT NOT NULL,
                    urgency TEXT NOT NULL,
                    confidence TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    reasoning TEXT NOT NULL,
                    supporting_data TEXT,
                    alternatives TEXT,
                    risks TEXT,
                    benefits TEXT,
                    estimated_impact REAL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    decided_at TIMESTAMP,
                    outcome TEXT
                )
            """
            )

            # プロジェクトメトリクステーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS project_metrics (
                    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    completion_rate REAL DEFAULT 0.0,
                    quality_score REAL DEFAULT 0.0,
                    timeline_adherence REAL DEFAULT 0.0,
                    resource_efficiency REAL DEFAULT 0.0,
                    team_satisfaction REAL DEFAULT 0.0,
                    defect_rate REAL DEFAULT 0.0,
                    rework_rate REAL DEFAULT 0.0,
                    cost_variance REAL DEFAULT 0.0,
                    measurement_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 意思決定パターンテーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS decision_patterns (
                    pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_name TEXT NOT NULL,
                    conditions TEXT NOT NULL,
                    recommended_action TEXT NOT NULL,
                    success_rate REAL DEFAULT 0.0,
                    confidence_score REAL DEFAULT 0.0,
                    usage_count INTEGER DEFAULT 0,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 意思決定成果テーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS decision_outcomes (
                    outcome_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    actual_impact REAL,
                    success_rating INTEGER,
                    lessons_learned TEXT,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (decision_id) REFERENCES decision_recommendations(decision_id)
                )
            """
            )

            # 予測精度テーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS prediction_accuracy (
                    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_type TEXT NOT NULL,
                    predicted_value REAL,
                    actual_value REAL,
                    accuracy_score REAL,
                    model_version TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # インデックス作成
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_decisions_project ON " \
                    "decision_recommendations(project_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_metrics_project ON project_metrics(project_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_patterns_type ON decision_patterns(pattern_name)"
            )

    def _load_historical_data(self):
        """過去データの読み込み"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 意思決定履歴を読み込み
                cursor = conn.execute(
                    """
                    SELECT decision_id, decision_type, urgency, confidence,
                           recommendation, reasoning, supporting_data,
                           alternatives, risks, benefits, estimated_impact, created_at
                    FROM decision_recommendations
                    WHERE created_at >= datetime('now', '-30 days')
                    ORDER BY created_at DESC
                """
                )

                for row in cursor:
                    decision = DecisionRecommendation(
                        decision_id=row[0],
                        decision_type=DecisionType(row[1]),
                        urgency=DecisionUrgency(row[2]),
                        confidence=ConfidenceLevel(row[3]),
                        recommendation=row[4],
                        reasoning=row[5],
                        supporting_data=json.loads(row[6]) if row[6] else {},
                        alternatives=json.loads(row[7]) if row[7] else [],
                        risks=json.loads(row[8]) if row[8] else [],
                        benefits=json.loads(row[9]) if row[9] else [],
                        estimated_impact=row[10],
                        created_at=datetime.fromisoformat(row[11]),
                    )
                    self.decision_history.append(decision)

                logger.info(
                    f"📊 過去データ読み込み完了: {len(self.decision_history)}件の意思決定"
                )

        except Exception as e:
            logger.error(f"過去データ読み込みエラー: {e}")

    def analyze_project_status(self, project_id: str) -> Dict[str, Any]:
        """プロジェクト状況の総合分析"""
        try:
            logger.info(f"📊 プロジェクト状況分析開始: {project_id}")

            # 現在のメトリクスを取得
            metrics = self._get_project_metrics(project_id)

            # 過去データとの比較
            historical_metrics = self._get_historical_metrics(project_id)

            # トレンド分析
            trends = self._analyze_trends(project_id, historical_metrics)

            # リスク分析
            risks = self._identify_risks(metrics, trends)

            # 機会の特定
            opportunities = self._identify_opportunities(metrics, trends)

            # 総合スコア計算
            overall_score = self._calculate_overall_score(metrics)

            analysis = {
                "project_id": project_id,
                "current_metrics": metrics.__dict__ if metrics else {},
                "trends": trends,
                "risks": risks,
                "opportunities": opportunities,
                "overall_score": overall_score,
                "health_status": self._determine_health_status(overall_score),
                "analysis_timestamp": datetime.now().isoformat(),
            }

            logger.info(f"✅ プロジェクト状況分析完了: スコア{overall_score:.2f}")
            return analysis

        except Exception as e:
            logger.error(f"プロジェクト状況分析エラー: {e}")
            return {}

    def generate_decision_recommendations(
        self, project_id: str
    ) -> List[DecisionRecommendation]:
        """意思決定推奨事項の生成"""
        try:
            logger.info(f"🤖 意思決定推奨生成開始: {project_id}")

            # プロジェクト分析
            analysis = self.analyze_project_status(project_id)

            recommendations = []

            # 各意思決定タイプについて分析
            for decision_type in DecisionType:
                recommendation = self._generate_recommendation_for_type(
                    project_id, decision_type, analysis
                )
                if recommendation:
                    recommendations.append(recommendation)

            # 緊急度でソート
            recommendations.sort(
                key=lambda x: self._get_urgency_priority(x.urgency), reverse=True
            )

            # データベースに保存
            for rec in recommendations:
                self._save_recommendation(rec)

            logger.info(f"📋 意思決定推奨生成完了: {len(recommendations)}件")
            return recommendations

        except Exception as e:
            logger.error(f"意思決定推奨生成エラー: {e}")
            return []

    def _generate_recommendation_for_type(
        self, project_id: str, decision_type: DecisionType, analysis: Dict[str, Any]
    ) -> Optional[DecisionRecommendation]:
        """特定タイプの意思決定推奨生成"""
        try:
            metrics = analysis.get("current_metrics", {})
            trends = analysis.get("trends", {})
            risks = analysis.get("risks", [])

            # 意思決定が必要かチェック
            if not self._needs_decision(decision_type, metrics, trends):
                return None

            # 推奨事項の生成
            recommendation_text = self._generate_recommendation_text(
                decision_type, metrics, trends
            )
            reasoning = self._generate_reasoning(decision_type, metrics, trends, risks)

            # 代替案の生成
            alternatives = self._generate_alternatives(decision_type, metrics)

            # リスクと利益の分析
            decision_risks = self._analyze_decision_risks(decision_type, metrics)
            benefits = self._analyze_decision_benefits(decision_type, metrics)

            # 影響度の推定
            estimated_impact = self._estimate_decision_impact(
                decision_type, metrics, trends
            )

            # 緊急度の判定
            urgency = self._determine_urgency(decision_type, metrics, trends)

            # 信頼度の計算
            confidence = self._calculate_confidence(decision_type, metrics, trends)

            decision_id = f"{project_id}_{decision_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            recommendation = DecisionRecommendation(
                decision_id=decision_id,
                decision_type=decision_type,
                urgency=urgency,
                confidence=confidence,
                recommendation=recommendation_text,
                reasoning=reasoning,
                supporting_data={"metrics": metrics, "trends": trends},
                alternatives=alternatives,
                risks=decision_risks,
                benefits=benefits,
                estimated_impact=estimated_impact,
                created_at=datetime.now(),
            )

            return recommendation

        except Exception as e:
            logger.error(f"意思決定推奨生成エラー ({decision_type.value}): {e}")
            return None

    def _needs_decision(
        self,
        decision_type: DecisionType,
        metrics: Dict[str, Any],
        trends: Dict[str, Any],
    ) -> bool:
        """意思決定が必要かの判定"""
        thresholds = self.decision_thresholds.get(decision_type, {})

        for metric_name, threshold in thresholds.items():
            current_value = metrics.get(metric_name, 0.0)

            # しきい値を下回る場合は意思決定が必要
            if metric_name in ["defect_rate", "rework_rate"]:
                # 低いほど良い指標
                if current_value > threshold:
                    return True
            else:
                # 高いほど良い指標
                if current_value < threshold:
                    return True

        # トレンドが悪化している場合
        for metric_name in thresholds.keys():
            trend = trends.get(metric_name, {})
            if (
                trend.get("direction") == "decreasing"
                and trend.get("significance", 0) > 0.5
            ):
                return True

        return False

    def _generate_recommendation_text(
        self,
        decision_type: DecisionType,
        metrics: Dict[str, Any],
        trends: Dict[str, Any],
    ) -> str:
        """推奨事項テキストの生成"""
        templates = {
            DecisionType.RESOURCE_ALLOCATION: [
                "リソース配分の最適化を行い、効率性を{efficiency_improvement:.1f}%向上させることを推奨します。",
                "チーム間のリソース再配分により、タイムライン遵守率を{timeline_improvement:.1f}%改善できます。",
                "外部リソースの活用により、プロジェクト完了率を{completion_improvement:.1f}%向上させることが可能です。",
            ],
            DecisionType.TASK_PRIORITIZATION: [
                "高優先度タスクの見直しにより、品質スコアを{quality_improvement:.1f}%向上させることを推奨します。",
                "クリティカルパスの最適化により、完了率を{completion_improvement:.1f}%改善できます。",
                "依存関係の解析に基づくタスク優先度の調整が必要です。",
            ],
            DecisionType.QUALITY_GATE: [
                "品質ゲートの強化により、欠陥率を{defect_reduction:.1f}%削減することを推奨します。",
                "レビュープロセスの改善により、手戻り率を{rework_reduction:.1f}%削減できます。",
                "自動化テストの導入により、品質スコアを{quality_improvement:.1f}%向上させることが可能です。",
            ],
            DecisionType.TIMELINE_ADJUSTMENT: [
                "スケジュール調整により、タイムライン遵守率を{timeline_improvement:.1f}%改善することを推奨します。",
                "マイルストーンの見直しにより、プロジェクト完了の確実性を向上させることができます。",
                "バッファ時間の追加により、リスクを{risk_reduction:.1f}%削減できます。",
            ],
        }

        # メトリクスベースの改善予測値を計算
        improvements = self._calculate_improvements(decision_type, metrics, trends)

        # テンプレートをランダム選択
        template_list = templates.get(decision_type, ["一般的な改善施策を推奨します。"])
        template = template_list[0]  # 最初のテンプレートを使用

        try:
            return template.format(**improvements)
        except KeyError:
            return template

    def _generate_reasoning(
        self,
        decision_type: DecisionType,
        metrics: Dict[str, Any],
        trends: Dict[str, Any],
        risks: List[str],
    ) -> str:
        """推論理由の生成"""
        reasoning_parts = []

        # メトリクスベースの理由
        for metric_name, value in metrics.items():
            if metric_name in self.decision_thresholds.get(decision_type, {}):
                threshold = self.decision_thresholds[decision_type][metric_name]

                if metric_name in ["defect_rate", "rework_rate"]:
                    if value > threshold:
                        reasoning_parts.append(
                            f"{metric_name}が{value:.1f}%でしきい値{threshold:.1f}%を超過"
                        )
                else:
                    if value < threshold:
                        reasoning_parts.append(
                            f"{metric_name}が{value:.1f}%でしきい値{threshold:.1f}%を下回る"
                        )

        # トレンドベースの理由
        for metric_name, trend in trends.items():
            if (
                trend.get("direction") == "decreasing"
                and trend.get("significance", 0) > 0.5
            ):
                reasoning_parts.append(f"{metric_name}に悪化傾向が見られる")

        # リスクベースの理由
        relevant_risks = [risk for risk in risks if decision_type.value in risk.lower()]
        if relevant_risks:
            reasoning_parts.append(f"関連リスク: {', '.join(relevant_risks[:2])}")

        return (
            "; ".join(reasoning_parts)
            if reasoning_parts
            else "定期的な評価に基づく推奨"
        )

    def _generate_alternatives(
        self, decision_type: DecisionType, metrics: Dict[str, Any]
    ) -> List[str]:
        """代替案の生成"""
        alternatives_map = {
            DecisionType.RESOURCE_ALLOCATION: [
                "外部リソースの活用",
                "チーム間のスキル共有",
                "作業の自動化推進",
                "優先度の再評価",
            ],
            DecisionType.TASK_PRIORITIZATION: [
                "MoSCoW分析の実施",
                "ビジネス価値ベースの優先度設定",
                "リスクベースの優先度調整",
                "ステークホルダーとの優先度再確認",
            ],
            DecisionType.QUALITY_GATE: [
                "段階的品質チェックの導入",
                "自動化テストの拡充",
                "ピアレビューの強化",
                "品質メトリクスの見直し",
            ],
            DecisionType.TIMELINE_ADJUSTMENT: [
                "スコープの調整",
                "並列作業の増加",
                "外部支援の活用",
                "マイルストーンの見直し",
            ],
        }

        return alternatives_map.get(decision_type, ["代替案を検討してください"])

    def _analyze_decision_risks(
        self, decision_type: DecisionType, metrics: Dict[str, Any]
    ) -> List[str]:
        """意思決定のリスク分析"""
        risks_map = {
            DecisionType.RESOURCE_ALLOCATION: [
                "リソース変更による一時的な生産性低下",
                "チーム内のスキル不足",
                "コスト増加のリスク",
            ],
            DecisionType.TASK_PRIORITIZATION: [
                "優先度変更による混乱",
                "ステークホルダーの不満",
                "既存作業の停滞",
            ],
            DecisionType.QUALITY_GATE: [
                "品質チェック強化による開発遅延",
                "プロセス変更への抵抗",
                "初期コストの増加",
            ],
            DecisionType.TIMELINE_ADJUSTMENT: [
                "スケジュール変更による影響範囲拡大",
                "ステークホルダーの期待値調整",
                "コスト増加の可能性",
            ],
        }

        return risks_map.get(decision_type, ["一般的なプロジェクトリスク"])

    def _analyze_decision_benefits(
        self, decision_type: DecisionType, metrics: Dict[str, Any]
    ) -> List[str]:
        """意思決定の利益分析"""
        benefits_map = {
            DecisionType.RESOURCE_ALLOCATION: [
                "リソース効率性の向上",
                "チームの生産性向上",
                "コスト最適化",
            ],
            DecisionType.TASK_PRIORITIZATION: [
                "重要な機能の早期提供",
                "顧客満足度の向上",
                "リスクの早期発見",
            ],
            DecisionType.QUALITY_GATE: [
                "製品品質の向上",
                "長期的な保守コスト削減",
                "顧客信頼の向上",
            ],
            DecisionType.TIMELINE_ADJUSTMENT: [
                "現実的なスケジュール設定",
                "チームのモチベーション向上",
                "品質の確保",
            ],
        }

        return benefits_map.get(decision_type, ["プロジェクト成功率の向上"])

    def _estimate_decision_impact(
        self,
        decision_type: DecisionType,
        metrics: Dict[str, Any],
        trends: Dict[str, Any],
    ) -> float:
        """意思決定の影響度推定"""
        # 基本影響度
        base_impact = {
            DecisionType.RESOURCE_ALLOCATION: 0.6,
            DecisionType.TASK_PRIORITIZATION: 0.4,
            DecisionType.QUALITY_GATE: 0.5,
            DecisionType.TIMELINE_ADJUSTMENT: 0.7,
        }.get(decision_type, 0.5)

        # メトリクスベースの調整
        overall_score = self._calculate_overall_score_from_dict(metrics)

        # スコアが低いほど影響が大きい
        impact_multiplier = 1.5 - overall_score

        # トレンドベースの調整
        trend_multiplier = 1.0
        for trend in trends.values():
            if isinstance(trend, dict) and trend.get("direction") == "decreasing":
                trend_multiplier += 0.1

        final_impact = base_impact * impact_multiplier * trend_multiplier

        # -1.0 to 1.0 の範囲に正規化
        return max(-1.0, min(1.0, final_impact))

    def _determine_urgency(
        self,
        decision_type: DecisionType,
        metrics: Dict[str, Any],
        trends: Dict[str, Any],
    ) -> DecisionUrgency:
        """緊急度の判定"""
        overall_score = self._calculate_overall_score_from_dict(metrics)

        # 非常に低いスコアは緊急
        if overall_score < 0.3:
            return DecisionUrgency.CRITICAL

        # 悪化傾向が見られる場合
        negative_trends = sum(
            1
            for trend in trends.values()
            if isinstance(trend, dict) and trend.get("direction") == "decreasing"
        )

        if negative_trends >= 3:
            return DecisionUrgency.HIGH
        elif negative_trends >= 1:
            return DecisionUrgency.MEDIUM
        else:
            return DecisionUrgency.LOW

    def _calculate_confidence(
        self,
        decision_type: DecisionType,
        metrics: Dict[str, Any],
        trends: Dict[str, Any],
    ) -> ConfidenceLevel:
        """信頼度の計算"""
        # データの完全性チェック
        required_metrics = list(self.decision_thresholds.get(decision_type, {}).keys())
        available_metrics = [m for m in required_metrics if m in metrics]

        data_completeness = (
            len(available_metrics) / len(required_metrics) if required_metrics else 1.0
        )

        # 過去の類似意思決定の成功率
        historical_success = self._get_historical_success_rate(decision_type)

        # 総合信頼度
        confidence_score = (data_completeness * 0.6) + (historical_success * 0.4)

        if confidence_score >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif confidence_score >= 0.7:
            return ConfidenceLevel.HIGH
        elif confidence_score >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif confidence_score >= 0.3:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def _get_historical_success_rate(self, decision_type: DecisionType) -> float:
        """過去の意思決定成功率を取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT AVG(success_rating)
                    FROM decision_outcomes do
                    JOIN decision_recommendations dr ON do.decision_id = dr.decision_id
                    WHERE dr.decision_type = ?
                """,
                    (decision_type.value,),
                )

                result = cursor.fetchone()
                return (
                    (result[0] / 5.0) if result and result[0] else 0.7
                )  # デフォルト70%

        except Exception as e:
            logger.error(f"過去成功率取得エラー: {e}")
            return 0.7

    def _calculate_improvements(
        self,
        decision_type: DecisionType,
        metrics: Dict[str, Any],
        trends: Dict[str, Any],
    ) -> Dict[str, float]:
        """改善予測値の計算"""
        improvements = {}

        # 決定タイプ別の改善予測ロジック
        if decision_type == DecisionType.RESOURCE_ALLOCATION:
            current_efficiency = metrics.get("resource_efficiency", 0.5)
            improvements["efficiency_improvement"] = (0.8 - current_efficiency) * 100
            improvements["timeline_improvement"] = max(
                10, 30 - (current_efficiency * 50)
            )
            improvements["completion_improvement"] = max(
                5, 20 - (current_efficiency * 40)
            )

        elif decision_type == DecisionType.QUALITY_GATE:
            current_quality = metrics.get("quality_score", 0.7)
            current_defect_rate = metrics.get("defect_rate", 0.05)
            improvements["quality_improvement"] = (0.9 - current_quality) * 100
            improvements["defect_reduction"] = current_defect_rate * 50
            improvements["rework_reduction"] = metrics.get("rework_rate", 0.1) * 60

        # デフォルト値を設定
        for key in [
            "efficiency_improvement",
            "timeline_improvement",
            "completion_improvement",
            "quality_improvement",
            "defect_reduction",
            "rework_reduction",
            "risk_reduction",
        ]:
            if key not in improvements:
                improvements[key] = 15.0  # デフォルト15%改善

        return improvements

    def _get_urgency_priority(self, urgency: DecisionUrgency) -> int:
        """緊急度の優先度を数値で返す"""
        return {
            DecisionUrgency.CRITICAL: 4,
            DecisionUrgency.HIGH: 3,
            DecisionUrgency.MEDIUM: 2,
            DecisionUrgency.LOW: 1,
        }.get(urgency, 1)

    def _save_recommendation(self, recommendation: DecisionRecommendation):
        """推奨事項をデータベースに保存"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO decision_recommendations
                    (decision_id, project_id, decision_type, urgency, confidence,
                     recommendation, reasoning, supporting_data, alternatives,
                     risks, benefits, estimated_impact, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        recommendation.decision_id,
                        recommendation.decision_id.split("_")[0],  # project_id
                        recommendation.decision_type.value,
                        recommendation.urgency.value,
                        recommendation.confidence.value,
                        recommendation.recommendation,
                        recommendation.reasoning,
                        json.dumps(recommendation.supporting_data),
                        json.dumps(recommendation.alternatives),
                        json.dumps(recommendation.risks),
                        json.dumps(recommendation.benefits),
                        recommendation.estimated_impact,
                        recommendation.created_at,
                    ),
                )

        except Exception as e:
            logger.error(f"推奨事項保存エラー: {e}")

    def _get_project_metrics(self, project_id: str) -> Optional[ProjectMetrics]:
        """プロジェクトメトリクスを取得"""
        # 実際の実装では、WorkflowController、ParallelExecutionManager、
        # PMQualityEvaluatorなどから実際のメトリクスを取得

        # シミュレーション用のダミーデータ
        import random

        return ProjectMetrics(
            project_id=project_id,
            completion_rate=random.uniform(0.4, 0.9),
            quality_score=random.uniform(0.6, 0.95),
            timeline_adherence=random.uniform(0.5, 0.9),
            resource_efficiency=random.uniform(0.4, 0.8),
            team_satisfaction=random.uniform(0.6, 0.9),
            defect_rate=random.uniform(0.01, 0.08),
            rework_rate=random.uniform(0.02, 0.12),
            cost_variance=random.uniform(-0.2, 0.3),
        )

    def _get_historical_metrics(self, project_id: str) -> List[ProjectMetrics]:
        """過去のメトリクスデータを取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT project_id, completion_rate, quality_score, timeline_adherence,
                           resource_efficiency, team_satisfaction, defect_rate, rework_rate,
                           cost_variance, measurement_date
                    FROM project_metrics
                    WHERE project_id = ?
                    ORDER BY measurement_date DESC
                    LIMIT 10
                """,
                    (project_id,),
                )

                metrics_list = []
                for row in cursor:
                    metrics = ProjectMetrics(*row[:-1])  # 最後のtimestampを除く
                    metrics_list.append(metrics)

                return metrics_list

        except Exception as e:
            logger.error(f"過去メトリクス取得エラー: {e}")
            return []

    def _analyze_trends(
        self, project_id: str, historical_metrics: List[ProjectMetrics]
    ) -> Dict[str, Any]:
        """トレンド分析"""
        trends = {}

        if len(historical_metrics) < 2:
            return trends

        # 各メトリクスのトレンドを計算
        metrics_names = [
            "completion_rate",
            "quality_score",
            "timeline_adherence",
            "resource_efficiency",
            "team_satisfaction",
            "defect_rate",
            "rework_rate",
        ]

        for metric_name in metrics_names:
            values = [getattr(m, metric_name) for m in historical_metrics]

            if len(values) >= 2:
                # 簡単な線形トレンド
                if values[0] > values[-1]:
                    direction = "decreasing"
                elif values[0] < values[-1]:
                    direction = "increasing"
                else:
                    direction = "stable"

                # 変化の大きさ
                change_magnitude = abs(values[0] - values[-1])
                significance = min(
                    1.0, change_magnitude / values[0] if values[0] != 0 else 0
                )

                trends[metric_name] = {
                    "direction": direction,
                    "significance": significance,
                    "current_value": values[0],
                    "previous_value": values[-1],
                    "change_rate": (
                        (values[0] - values[-1]) / values[-1] if values[-1] != 0 else 0
                    ),
                }

        return trends

    def _identify_risks(
        self, metrics: Optional[ProjectMetrics], trends: Dict[str, Any]
    ) -> List[str]:
        """リスクの特定"""
        risks = []

        if not metrics:
            return risks

        # メトリクスベースのリスク
        if metrics.completion_rate < 0.6:
            risks.append("プロジェクト完了率が低い")

        if metrics.quality_score < 0.7:
            risks.append("品質スコアが基準を下回る")

        if metrics.defect_rate > 0.05:
            risks.append("欠陥率が高い")

        if metrics.timeline_adherence < 0.7:
            risks.append("スケジュール遵守率が低い")

        # トレンドベースのリスク
        for metric_name, trend in trends.items():
            if isinstance(trend, dict) and trend.get("direction") == "decreasing":
                if trend.get("significance", 0) > 0.3:
                    risks.append(f"{metric_name}の悪化傾向")

        return risks

    def _identify_opportunities(
        self, metrics: Optional[ProjectMetrics], trends: Dict[str, Any]
    ) -> List[str]:
        """機会の特定"""
        opportunities = []

        if not metrics:
            return opportunities

        # 改善可能な領域
        if metrics.resource_efficiency < 0.8:
            opportunities.append("リソース効率の改善余地")

        if metrics.team_satisfaction < 0.8:
            opportunities.append("チーム満足度の向上機会")

        # 好調な指標の活用
        if metrics.quality_score > 0.8:
            opportunities.append("高品質プロセスの他領域への展開")

        if metrics.completion_rate > 0.8:
            opportunities.append("成功パターンの標準化")

        return opportunities

    def _calculate_overall_score(self, metrics: Optional[ProjectMetrics]) -> float:
        """総合スコア計算"""
        if not metrics:
            return 0.5

        return self._calculate_overall_score_from_dict(metrics.__dict__)

    def _calculate_overall_score_from_dict(self, metrics: Dict[str, Any]) -> float:
        """辞書からの総合スコア計算"""
        weighted_score = 0.0
        total_weight = 0.0

        for metric_name, weight in self.metric_weights.items():
            if metric_name in metrics:
                value = metrics[metric_name]

                # 負の指標は反転
                if metric_name in ["defect_rate", "rework_rate"]:
                    value = 1.0 - min(1.0, value * 10)  # 10%を上限として正規化

                weighted_score += value * weight
                total_weight += weight

        return weighted_score / total_weight if total_weight > 0 else 0.5

    def _determine_health_status(self, overall_score: float) -> str:
        """健康状態の判定"""
        if overall_score >= 0.8:
            return "excellent"
        elif overall_score >= 0.6:
            return "good"
        elif overall_score >= 0.4:
            return "fair"
        elif overall_score >= 0.2:
            return "poor"
        else:
            return "critical"

    def record_decision_outcome(
        self,
        decision_id: str,
        actual_impact: float,
        success_rating: int,
        lessons_learned: str = "",
    ):
        """意思決定の結果を記録"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # project_idを取得
                cursor = conn.execute(
                    """
                    SELECT project_id FROM decision_recommendations
                    WHERE decision_id = ?
                """,
                    (decision_id,),
                )

                row = cursor.fetchone()
                if not row:
                    logger.error(f"意思決定が見つかりません: {decision_id}")
                    return

                project_id = row[0]

                # 結果を記録
                conn.execute(
                    """
                    INSERT INTO decision_outcomes
                    (decision_id, project_id, actual_impact, success_rating, lessons_learned)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        decision_id,
                        project_id,
                        actual_impact,
                        success_rating,
                        lessons_learned,
                    ),
                )

                # 推奨事項のステータスを更新
                conn.execute(
                    """
                    UPDATE decision_recommendations
                    SET status = 'completed', decided_at = ?, outcome = ?
                    WHERE decision_id = ?
                """,
                    (datetime.now(), f"Rating: {success_rating}/5", decision_id),
                )

            logger.info(
                f"✅ 意思決定結果記録: {decision_id} (評価: {success_rating}/5)"
            )

        except Exception as e:
            logger.error(f"意思決定結果記録エラー: {e}")

    def get_decision_dashboard(self, project_id: str) -> Dict[str, Any]:
        """意思決定ダッシュボード情報を取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 現在の推奨事項
                cursor = conn.execute(
                    """
                    SELECT decision_id, decision_type, urgency, confidence,
                           recommendation, created_at, status
                    FROM decision_recommendations
                    WHERE project_id = ? AND status = 'pending'
                    ORDER BY
                        CASE urgency
                            WHEN 'critical' THEN 4
                            WHEN 'high' THEN 3
                            WHEN 'medium' THEN 2
                            WHEN 'low' THEN 1
                        END DESC,
                        created_at DESC
                """,
                    (project_id,),
                )

                pending_decisions = []
                for row in cursor:
                    pending_decisions.append(
                        {
                            "decision_id": row[0],
                            "decision_type": row[1],
                            "urgency": row[2],
                            "confidence": row[3],
                            "recommendation": row[4],
                            "created_at": row[5],
                            "status": row[6],
                        }
                    )

                # 過去の意思決定の統計
                cursor = conn.execute(
                    """
                    SELECT decision_type, COUNT(*) as count, AVG(success_rating) as avg_rating
                    FROM decision_outcomes do
                    JOIN decision_recommendations dr ON do.decision_id = dr.decision_id
                    WHERE dr.project_id = ?
                    GROUP BY decision_type
                """,
                    (project_id,),
                )

                decision_stats = {}
                for row in cursor:
                    decision_stats[row[0]] = {
                        "count": row[1],
                        "avg_rating": row[2] or 0,
                    }

                # プロジェクト分析
                analysis = self.analyze_project_status(project_id)

                return {
                    "project_id": project_id,
                    "pending_decisions": pending_decisions,
                    "decision_statistics": decision_stats,
                    "project_analysis": analysis,
                    "dashboard_updated": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"ダッシュボード取得エラー: {e}")
            return {}


if __name__ == "__main__":
    # テスト実行
    pm_support = PMDecisionSupport()

    print("=" * 80)
    print("🤖 PM Decision Support System Test")
    print("=" * 80)

    # テストプロジェクト
    test_project_id = "test_project_003"

    # プロジェクト状況分析
    print(f"\n📊 プロジェクト状況分析: {test_project_id}")
    analysis = pm_support.analyze_project_status(test_project_id)
    print(f"総合スコア: {analysis.get('overall_score', 0):.2f}")
    print(f"健康状態: {analysis.get('health_status', 'unknown')}")
    print(f"リスク数: {len(analysis.get('risks', []))}")
    print(f"機会数: {len(analysis.get('opportunities', []))}")

    # 意思決定推奨生成
    print(f"\n🤖 意思決定推奨生成")
    recommendations = pm_support.generate_decision_recommendations(test_project_id)

    for i, rec in enumerate(recommendations[:3]):  # 上位3件を表示
        print(f"\n📋 推奨事項 {i+1}:")
        print(f"  タイプ: {rec.decision_type.value}")
        print(f"  緊急度: {rec.urgency.value}")
        print(f"  信頼度: {rec.confidence.value}")
        print(f"  推奨: {rec.recommendation}")
        print(f"  影響度: {rec.estimated_impact:+.2f}")

        if rec.risks:
            print(f"  リスク: {rec.risks[0]}")
        if rec.benefits:
            print(f"  利益: {rec.benefits[0]}")

    # ダッシュボード表示
    print(f"\n📊 意思決定ダッシュボード")
    dashboard = pm_support.get_decision_dashboard(test_project_id)

    pending_count = len(dashboard.get("pending_decisions", []))
    print(f"  未決定事項: {pending_count}件")

    stats = dashboard.get("decision_statistics", {})
    print(f"  過去の意思決定統計: {len(stats)}タイプ")
    for decision_type, stat in stats.items():
        print(
            f"    {decision_type}: {stat['count']}件 (平均評価: {stat['avg_rating']:.1f}/5)"
        )

    # 意思決定結果記録のテスト
    if recommendations:
        test_decision_id = recommendations[0].decision_id
        print(f"\n✅ 意思決定結果記録テスト: {test_decision_id}")
        pm_support.record_decision_outcome(
            test_decision_id,
            actual_impact=0.8,
            success_rating=4,
            lessons_learned="リソース配分の最適化により期待以上の効果",
        )
        print("結果記録完了")

    print(f"\n🎯 PM Decision Support System テスト完了")
