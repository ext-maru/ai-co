#!/usr/bin/env python3
"""
Elder Reporting Rules Implementation
エルダー報告ルールv1.0 実装スクリプト
"""

import json
import logging
import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
KNOWLEDGE_BASE = PROJECT_ROOT / "knowledge_base"
DATA_DIR = PROJECT_ROOT / "data" / "metrics"
REPORTS_DIR = KNOWLEDGE_BASE / "reports"

# ディレクトリ作成
(DATA_DIR / "current").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "daily").mkdir(parents=True, exist_ok=True)
(REPORTS_DIR / "history").mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [ElderReporter] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


class UrgencyLevel(Enum):
    """UrgencyLevelクラス"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NORMAL = "NORMAL"


class ElderReportingSystem:
    """エルダー報告システム v1.0"""

    def __init__(self):
        """初期化メソッド"""
        # ルール読み込み
        self.rules = self._load_rules()
        self.last_report_time = {}
        self.alert_history = {}  # アラート疲れ対策用
        self.system_state = "NORMAL"  # NORMAL or WARNING

    def _load_rules(self):
        """決定されたルールを読み込み"""
        rules_file = KNOWLEDGE_BASE / "ELDER_REPORTING_RULES_DECISION.json"
        if rules_file.exists():
            with open(rules_file, "r", encoding="utf-8") as f:
                decision = json.load(f)
                return decision["reporting_rules"]
        else:
            logger.warning("ルールファイルが見つかりません。デフォルト設定を使用")
            return self._get_default_rules()

    def _get_default_rules(self):
        """デフォルトルール"""
        return {"定期報告": {"通常時": {"頻度": "1時間", "内容": ["基本メトリクス"], "形式": "Markdown"}}}

    def check_urgency_level(self, metrics):
        """緊急度を判定"""
        urgency_rules = self.rules.get("緊急度判定", {})

        # CRITICAL チェック
        if self._check_conditions(
            metrics, urgency_rules.get("CRITICAL", {}).get("条件", [])
        ):
            return UrgencyLevel.CRITICAL

        # HIGH チェック
        if self._check_conditions(metrics, urgency_rules.get("HIGH", {}).get("条件", [])):
            return UrgencyLevel.HIGH

        # MEDIUM チェック
        if self._check_conditions(
            metrics, urgency_rules.get("MEDIUM", {}).get("条件", [])
        ):
            return UrgencyLevel.MEDIUM

        # LOW チェック
        if self._check_conditions(metrics, urgency_rules.get("LOW", {}).get("条件", [])):
            return UrgencyLevel.LOW

        return UrgencyLevel.NORMAL

    def _check_conditions(self, metrics, conditions):
        """条件チェック"""
        for condition in conditions:
            if "ワーカー健全性" in condition and "<" in condition:
                threshold = float(condition.split("<")[1].replace("%", "")) / 100
                if metrics.get("worker_health", 1.0) < threshold:
                    return True

            elif "メモリ使用率" in condition and ">" in condition:
                threshold = float(condition.split(">")[1].replace("%", "")) / 100
                if metrics.get("memory_usage", 0.0) > threshold:
                    return True

            elif "エラー率" in condition and ">" in condition:
                threshold = float(condition.split(">")[1].replace("%", "")) / 100
                if not (metrics.get("error_rate", 0.0) > threshold):
                    continue  # Early return to reduce nesting
                # Reduced nesting - original condition satisfied
                if metrics.get("error_rate", 0.0) > threshold:
                    return True

            elif "キュー積滞" in condition and ">" in condition:
                threshold = int(condition.split(">")[1])
                if not (metrics.get("queue_backlog", 0) > threshold):
                    continue  # Early return to reduce nesting
                # Reduced nesting - original condition satisfied
                if metrics.get("queue_backlog", 0) > threshold:
                    return True

        return False

    def should_report(self, urgency_level, event_type="regular"):
        """報告すべきかチェック（アラート疲れ対策含む）"""
        current_time = datetime.now()

        # 同一事象のアラート疲れチェック
        if urgency_level in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
            alert_key = f"{urgency_level.value}_{event_type}"
            if alert_key in self.alert_history:
                last_alert = self.alert_history[alert_key]
                if (current_time - last_alert).total_seconds() < 3600:  # 1時間以内
                    return False
            self.alert_history[alert_key] = current_time

        # 定期報告の頻度チェック
        if event_type == "regular":
            report_type = "警戒時" if self.system_state == "WARNING" else "通常時"
            frequency = self.rules["定期報告"][report_type]["頻度"]

            if report_type in self.last_report_time:
                last_time = self.last_report_time[report_type]
                if (
                    frequency == "1時間"
                    and (current_time - last_time).total_seconds() < 3600
                ):
                    return False
                elif (
                    frequency == "15分"
                    and (current_time - last_time).total_seconds() < 900
                ):
                    return False

            self.last_report_time[report_type] = current_time

        return True

    def create_report(self, metrics, urgency_level, report_type="regular"):
        """レポート作成"""
        timestamp = datetime.now()

        if urgency_level == UrgencyLevel.CRITICAL:
            return self._create_critical_report(metrics, timestamp)
        elif urgency_level == UrgencyLevel.HIGH:
            return self._create_high_report(metrics, timestamp)
        elif report_type == "daily":
            return self._create_daily_summary(metrics, timestamp)
        elif report_type == "weekly":
            return self._create_weekly_review(metrics, timestamp)
        else:
            return self._create_regular_report(metrics, timestamp)

    def _create_critical_report(self, metrics, timestamp):
        """CRITICALレポート作成"""
        report = f"""# 🚨 CRITICAL アラート

**発生時刻**: {timestamp.strftime('%Y年%m月%d日 %H:%M:%S')}
**緊急度**: CRITICAL

## 検出された問題

"""

        if metrics.get("worker_health", 1.0) < 0.5:
            report += f"- **ワーカー健全性**: {metrics['worker_health']:0.1%} (閾値: 50%)\n"
        if metrics.get("memory_usage", 0.0) > 0.95:
            report += f"- **メモリ使用率**: {metrics['memory_usage']:0.1%} (閾値: 95%)\n"
        if metrics.get("error_rate", 0.0) > 0.2:
            report += f"- **エラー率**: {metrics['error_rate']:0.1%} (閾値: 20%)\n"

        report += """
## 自動対応

エルダー報告ルールv1.0に基づき、以下の自動対応を実行します：
1.0 影響を受けたワーカーの再起動
2.0 リソースの最適化
3.0 エラーログの詳細分析

## 詳細メトリクス
"""

        # JSON形式で詳細データも添付
        report += f"\n```json\n{json.dumps(metrics, indent=2)}\n```\n"

        return report, "markdown+json"

    def _create_regular_report(self, metrics, timestamp):
        """定期レポート作成"""
        report = f"""# 📊 定期システムレポート

**報告時刻**: {timestamp.strftime('%Y年%m月%d日 %H:%M')}
**システム状態**: {self.system_state}

## サマリー
- システムヘルススコア: {self._calculate_health_score(metrics):0.1%}
- ワーカー稼働率: {metrics.get('worker_health', 0):0.1%}
- エラー率: {metrics.get('error_rate', 0):0.1%}

"""

        if self.system_state == "WARNING":
            report += "## ⚠️ 警戒モード\n詳細な監視を継続中\n"

        return report, "markdown"

    def _create_daily_summary(self, metrics, timestamp):
        """日次サマリー作成"""
        report = f"""# 📅 日次サマリーレポート

**日付**: {timestamp.strftime('%Y年%m月%d日')}

## 24時間統計
- 平均稼働率: {metrics.get('avg_health', 0):0.1%}
- 総エラー数: {metrics.get('total_errors', 0)}
- インシデント数: {metrics.get('incident_count', 0)}

## 自動対応実績
- ワーカー再起動: {metrics.get('worker_restarts', 0)}回
- リソース調整: {metrics.get('resource_adjustments', 0)}回

## 明日への提言
{self._generate_recommendations(metrics)}
"""
        return report, "markdown"

    def _create_weekly_review(self, metrics, timestamp):
        """週次レビュー作成"""
        report = f"""# 📈 週次レビューレポート

**週**: {timestamp.strftime('%Y年 第%W週')}

## 週間トレンド
- 稼働率推移: {"↑" if metrics.get('health_trend', 0) > 0 else "↓"}
- パフォーマンス: {"改善" if metrics.get('perf_trend', 0) > 0 else "低下"}

## 改善提案
{self._generate_improvement_suggestions(metrics)}

## 学習成果
- 新規パターン検出: {metrics.get('new_patterns', 0)}
- 自動対応成功率: {metrics.get('auto_fix_rate', 0):0.1%}
"""
        return report, "markdown+graph"

    def _calculate_health_score(self, metrics):
        """ヘルススコア計算"""
        worker_health = metrics.get("worker_health", 0)
        error_rate = 1 - metrics.get("error_rate", 0)
        memory_ok = 1 if metrics.get("memory_usage", 0) < 0.8 else 0.5

        return worker_health * 0.5 + error_rate * 0.3 + memory_ok * 0.2

    def _generate_recommendations(self, metrics):
        """推奨事項生成"""
        recommendations = []

        if metrics.get("error_rate", 0) > 0.05:
            recommendations.append("- エラー率が高いため、根本原因分析を推奨")
        if metrics.get("memory_usage", 0) > 0.7:
            recommendations.append("- メモリ使用率が高いため、リソース最適化を検討")

        return "\n".join(recommendations) if recommendations else "- 特に推奨事項はありません"

    def _generate_improvement_suggestions(self, metrics):
        """改善提案生成"""
        suggestions = []

        if metrics.get("test_coverage", 0) < 0.8:
            suggestions.append("- テストカバレッジ向上プロジェクトの開始")
        if metrics.get("avg_response_time", 0) > 1.0:
            suggestions.append("- パフォーマンス最適化の実施")

        return "\n".join(suggestions) if suggestions else "- 現状維持で問題ありません"

    def save_report(self, report_content, report_format, urgency_level):
        """レポート保存"""
        timestamp = datetime.now()

        # ファイル名決定
        if urgency_level in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
            filename = (
                f"alert_{urgency_level.value}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            )
        else:
            filename = f"report_{timestamp.strftime('%Y%m%d_%H%M%S')}"

        # 保存先決定
        if urgency_level == UrgencyLevel.CRITICAL:
            save_dir = REPORTS_DIR
        else:
            save_dir = REPORTS_DIR / "history"

        # Markdown保存
        md_file = save_dir / f"{filename}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(report_content)

        logger.info(f"レポート保存: {md_file}")

        return str(md_file)

    def execute_auto_response(self, urgency_level, metrics):
        """自動対応実行"""
        if urgency_level != UrgencyLevel.CRITICAL:
            return None

        logger.info("🤖 自動対応を開始します...")

        responses = []

        # ワーカー健全性が低い場合
        if metrics.get("worker_health", 1.0) < 0.5:
            logger.info("  - ワーカー再起動を実行")
            # 実際の再起動コマンドはここに実装
            responses.append("ワーカー再起動を実行")

        # メモリ使用率が高い場合
        if metrics.get("memory_usage", 0.0) > 0.95:
            logger.info("  - メモリ最適化を実行")
            # 実際の最適化コマンドはここに実装
            responses.append("メモリ最適化を実行")

        return responses


def demo_reporting_system():
    """デモ実行"""
    system = ElderReportingSystem()

    # テストメトリクス
    test_metrics = {
        "worker_health": 0.85,
        "memory_usage": 0.65,
        "error_rate": 0.02,
        "queue_backlog": 100,
        "test_coverage": 0.018,
        "cpu_usage": 0.45,
    }

    # 緊急度チェック
    urgency = system.check_urgency_level(test_metrics)
    logger.info(f"緊急度: {urgency.value}")

    # レポート作成
    if system.should_report(urgency):
        report, format_type = system.create_report(test_metrics, urgency)
        saved_path = system.save_report(report, format_type, urgency)
        logger.info(f"レポート作成完了: {saved_path}")

        # 自動対応
        if urgency == UrgencyLevel.CRITICAL:
            responses = system.execute_auto_response(urgency, test_metrics)
            logger.info(f"自動対応完了: {responses}")


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("エルダー報告ルール v1.0 実装デモ")
    logger.info("=" * 60)
    demo_reporting_system()
