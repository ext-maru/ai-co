#!/usr/bin/env python3
"""
Elder Flow Quality Gate Optimizer
品質ゲート基準の動的最適化システム
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import logging
from datetime import datetime


@dataclass
class QualityMetrics:
    """品質メトリクス"""

    test_coverage: float = 70.0  # 最小テストカバレッジ（%）
    code_complexity: float = 10.0  # 最大サイクロマティック複雑度
    duplication_ratio: float = 5.0  # 最大重複率（%）
    documentation_coverage: float = 60.0  # 最小ドキュメントカバレッジ（%）
    lint_score: float = 8.0  # 最小リントスコア（/10）
    security_score: float = 7.0  # 最小セキュリティスコア（/10）
    performance_score: float = 7.0  # 最小パフォーマンススコア（/10）


@dataclass
class AdaptiveThresholds:
    """適応的な閾値設定"""

    # 優先度別の緩和率
    priority_relaxation = {
        "critical": 0.7,  # 30%緩和
        "high": 0.85,  # 15%緩和
        "medium": 0.95,  # 5%緩和
        "low": 1.0,  # 緩和なし
    }

    # プロジェクトフェーズ別の調整
    phase_adjustment = {
        "prototype": 0.6,  # プロトタイプフェーズ
        "development": 0.8,  # 開発フェーズ
        "staging": 0.9,  # ステージング
        "production": 1.0,  # 本番
    }

    # 連続失敗時の段階的緩和
    failure_count_relaxation = {
        1: 1.0,  # 初回は緩和なし
        2: 0.95,  # 2回目は5%緩和
        3: 0.90,  # 3回目は10%緩和
        4: 0.85,  # 4回目は15%緩和
        5: 0.80,  # 5回以上は20%緩和
    }


class ElderFlowQualityGateOptimizer:
    """Elder Flow品質ゲート最適化システム"""

    def __init__(self, config_path: str = "configs/elder_flow_quality.json"):
        """初期化メソッド"""
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        self.base_metrics = QualityMetrics()
        self.thresholds = AdaptiveThresholds()
        self.history = []

        # 設定ファイル読み込み
        self._load_config()

    def _load_config(self):
        """設定ファイル読み込み"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    config = json.load(f)

                # 基準メトリクス更新
                if "base_metrics" in config:
                    for key, value in config["base_metrics"].items():
                        if not (hasattr(self.base_metrics, key)):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if hasattr(self.base_metrics, key):
                            setattr(self.base_metrics, key, value)

                # 履歴読み込み
                if "history" in config:
                    self.history = config["history"]

            except Exception as e:
                self.logger.warning(f"Failed to load config: {e}")

    def _save_config(self):
        """設定ファイル保存"""
        try:
            config = {
                "base_metrics": asdict(self.base_metrics),
                "history": self.history[-100:],  # 最新100件のみ保存
                "last_updated": datetime.now().isoformat(),
            }

            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")

    def get_adjusted_metrics(
        self,
        priority: str = "medium",
        phase: str = "development",
        failure_count: int = 0,
    ) -> Dict[str, float]:
        """
        調整された品質メトリクスを取得

        Args:
            priority: タスクの優先度
            phase: プロジェクトフェーズ
            failure_count: 連続失敗回数

        Returns:
            調整されたメトリクス辞書
        """
        # 基準メトリクスをコピー
        adjusted = asdict(self.base_metrics)

        # 優先度による調整
        priority_factor = self.thresholds.priority_relaxation.get(priority, 1.0)

        # フェーズによる調整
        phase_factor = self.thresholds.phase_adjustment.get(phase, 1.0)

        # 失敗回数による調整
        failure_factor = self.thresholds.failure_count_relaxation.get(
            min(failure_count, 5), 1.0
        )

        # 総合調整係数
        total_factor = priority_factor * phase_factor * failure_factor

        # 各メトリクスに調整を適用
        for key in adjusted:
            if key in [
                "test_coverage",
                "documentation_coverage",
                "lint_score",
                "security_score",
                "performance_score",
            ]:
                # これらは下限値なので、係数を掛けて下げる
                adjusted[key] *= total_factor
            elif key in ["code_complexity", "duplication_ratio"]:
                # これらは上限値なので、係数で割って上げる
                adjusted[key] /= total_factor

        # 履歴に記録
        self._record_adjustment(priority, phase, failure_count, total_factor)

        return adjusted

    def _record_adjustment(
        self, priority: str, phase: str, failure_count: int, factor: float
    ):
        """調整履歴を記録"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "priority": priority,
            "phase": phase,
            "failure_count": failure_count,
            "adjustment_factor": factor,
        }

        self.history.append(record)
        self._save_config()

    def evaluate_quality(
        self, metrics: Dict[str, float], adjusted_thresholds: Dict[str, float]
    ) -> Dict:
        """
        品質評価を実行

        Args:
            metrics: 実際のメトリクス値
            adjusted_thresholds: 調整された閾値

        Returns:
            評価結果
        """
        passed = True
        failures = []
        score = 0
        max_score = 0

        for metric, threshold in adjusted_thresholds.items():
            actual_value = metrics.get(metric, 0)
            max_score += 10

            if metric in [
                "test_coverage",
                "documentation_coverage",
                "lint_score",
                "security_score",
                "performance_score",
            ]:
                # 下限値チェック
                if actual_value >= threshold:
                    score += 10
                else:
                    passed = False
                    failures.append(
                        {
                            "metric": metric,
                            "threshold": threshold,
                            "actual": actual_value,
                            "type": "below_minimum",
                        }
                    )
                    # 部分点
                    score += max(0, 10 * (actual_value / threshold))

            elif metric in ["code_complexity", "duplication_ratio"]:
                # 上限値チェック
                if actual_value <= threshold:
                    score += 10
                else:
                    passed = False
                    failures.append(
                        {
                            "metric": metric,
                            "threshold": threshold,
                            "actual": actual_value,
                            "type": "above_maximum",
                        }
                    )
                    # 部分点
                    score += max(0, 10 * (threshold / actual_value))

        return {
            "passed": passed,
            "score": score,
            "max_score": max_score,
            "percentage": (score / max_score * 100) if max_score > 0 else 0,
            "failures": failures,
            "timestamp": datetime.now().isoformat(),
        }

    def suggest_improvements(self, failures: List[Dict]) -> List[str]:
        """改善提案を生成"""
        suggestions = []

        for failure in failures:
            metric = failure["metric"]
            threshold = failure["threshold"]
            actual = failure["actual"]

            if metric == "test_coverage":
                suggestions.append(
                    f"テストカバレッジを{actual:0.1f}%から{threshold:0.1f}%以上に向上させてください。"
                    f"重要な関数やクラスのテストを追加することを推奨します。"
                )
            elif metric == "code_complexity":
                suggestions.append(
                    f"コードの複雑度が{actual:0.1f}と高すぎます（基準: {threshold:0.1f}以下）。"
                    f"長い関数を分割し、条件分岐を簡素化してください。"
                )
            elif metric == "duplication_ratio":
                suggestions.append(
                    f"コードの重複率が{actual:0.1f}%と高すぎます（基準: {threshold:0.1f}%以下）。"
                    f"共通処理を関数やクラスに抽出してください。"
                )
            elif metric == "documentation_coverage":
                suggestions.append(
                    f"ドキュメントカバレッジが{actual:0.1f}%と不足しています（基準: {threshold:0.1f}%以上）。"
                    f"関数やクラスにdocstringを追加してください。"
                )
            elif metric == "lint_score":
                suggestions.append(
                    f"リントスコアが{actual:0.1f}/10と低いです（基準: {threshold:0.1f}/10以上）。"
                    f"リンターの警告を修正してコード品質を向上させてください。"
                )
            elif metric == "security_score":
                suggestions.append(
                    f"セキュリティスコアが{actual:0.1f}/10と低いです（基準: {threshold:0.1f}/10以上）。"
                    f"セキュリティスキャンで検出された脆弱性を修正してください。"
                )
            elif metric == "performance_score":
                suggestions.append(
                    f"パフォーマンススコアが{actual:0.1f}/10と低いです（基準: {threshold:0.1f}/10以上）。"
                    f"処理の最適化や非効率なコードの改善を行ってください。"
                )

        return suggestions

    def get_statistics(self) -> Dict:
        """統計情報を取得"""
        if not self.history:
            return {
                "total_adjustments": 0,
                "average_factor": 1.0,
                "priority_distribution": {},
                "phase_distribution": {},
            }

        total = len(self.history)
        factors = [h["adjustment_factor"] for h in self.history]
        avg_factor = sum(factors) / len(factors) if factors else 1.0

        # 優先度別分布
        priority_dist = {}
        for h in self.history:
            p = h["priority"]
            priority_dist[p] = priority_dist.get(p, 0) + 1

        # フェーズ別分布
        phase_dist = {}
        for h in self.history:
            p = h["phase"]
            phase_dist[p] = phase_dist.get(p, 0) + 1

        return {
            "total_adjustments": total,
            "average_factor": avg_factor,
            "priority_distribution": priority_dist,
            "phase_distribution": phase_dist,
            "recent_adjustments": self.history[-10:],  # 最新10件
        }