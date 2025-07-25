#!/usr/bin/env python3
"""
エラーパターン予測エンジン
過去のエラーパターンから将来のエラーを予測し、予防的対応を可能にする
"""

import hashlib
import json
import logging
import sqlite3

# プロジェクトルートをPythonパスに追加
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import BaseManager


class PredictionConfidence(Enum):
    """予測信頼度レベル"""

    VERY_HIGH = 0.9
    HIGH = 0.7
    MEDIUM = 0.5
    LOW = 0.3
    VERY_LOW = 0.1


@dataclass
class ErrorPattern:
    """エラーパターンデータクラス"""

    pattern_id: str
    error_type: str
    context_hash: str
    frequency: int
    last_occurrence: datetime
    avg_time_to_fix: float
    success_rate: float
    temporal_pattern: Optional[Dict] = None
    causal_factors: Optional[List] = None


@dataclass
class ErrorPrediction:
    """エラー予測データクラス"""

    error_type: str
    probability: float
    confidence: float
    time_window: str
    preventive_actions: List[Dict]
    risk_score: float
    rationale: str


class ErrorPatternPredictor(BaseManager):
    """エラーパターンを学習し予測するエンジン"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__()
        self.db_path = PROJECT_ROOT / "db" / "error_patterns_ml.db"
        self.logger = logging.getLogger(self.__class__.__name__)

        # 学習パラメータ
        self.min_occurrences_for_pattern = 3
        self.temporal_window_hours = 24
        self.context_similarity_threshold = 0.7
        self.prediction_horizon_hours = 6

        # パターンキャッシュ
        self.pattern_cache = {}
        self.temporal_patterns = defaultdict(list)
        self.causal_chains = defaultdict(list)

        # データベース初期化
        self._init_database()
        self._load_patterns()

    def _init_database(self):
        """機械学習用データベースの初期化"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3connect(self.db_path) as conn:
            # エラー発生履歴
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS error_occurrences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_hash TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    error_message TEXT,
                    context_json TEXT,
                    occurred_at TIMESTAMP,
                    day_of_week INTEGER,
                    hour_of_day INTEGER,
                    minute_of_hour INTEGER,
                    fixed BOOLEAN,
                    fix_duration REAL,
                    fix_strategy TEXT,
                    INDEX idx_error_hash (error_hash),
                    INDEX idx_occurred_at (occurred_at)
                )
            """
            )

            # 学習されたパターン
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS learned_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    error_type TEXT NOT NULL,
                    pattern_type TEXT,  -- temporal, sequential, environmental
                    pattern_data TEXT,  -- JSON
                    confidence REAL,
                    occurrences INTEGER,
                    last_updated TIMESTAMP,
                    success_rate REAL
                )
            """
            )

            # 予測履歴
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_id TEXT UNIQUE,
                    error_type TEXT,
                    predicted_at TIMESTAMP,
                    prediction_window TEXT,
                    probability REAL,
                    confidence REAL,
                    prevented BOOLEAN,
                    actual_occurred BOOLEAN,
                    feedback TEXT
                )
            """
            )

            # 因果関係
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS causal_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cause_event TEXT,
                    effect_error TEXT,
                    correlation_strength REAL,
                    avg_delay_minutes REAL,
                    occurrence_count INTEGER,
                    last_observed TIMESTAMP
                )
            """
            )

    def record_error_occurrence(self, error_info: Dict) -> str:
        """エラー発生を記録"""
        error_hash = self._compute_error_hash(error_info)
        occurred_at = datetime.now()

        context = {
            "worker_type": error_info.get("worker_type"),
            "task_type": error_info.get("task_type"),
            "system_state": self._get_system_state(),
            "recent_events": self._get_recent_events(),
        }

        with sqlite3connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO error_occurrences
                (error_hash, error_type, error_message, context_json,
                 occurred_at, day_of_week, hour_of_day, minute_of_hour,
                 fixed, fix_duration, fix_strategy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    error_hash,
                    error_info.get("error_type", "unknown"),
                    error_info.get("error_message", "")[:500],
                    json.dumps(context),
                    occurred_at,
                    occurred_at.weekday(),
                    occurred_at.hour,
                    occurred_at.minute,
                    False,
                    None,
                    None,
                ),
            )

        # パターン学習トリガー
        self._learn_from_occurrence(error_hash, error_info, context, occurred_at)

        return error_hash

    def predict_errors(self, context: Optional[Dict] = None) -> List[ErrorPrediction]:
        """次の時間枠で発生可能性のあるエラーを予測"""
        predictions = []
        current_time = datetime.now()

        # 1.0 時間的パターンに基づく予測
        temporal_predictions = self._predict_temporal_patterns(current_time)
        predictions.extend(temporal_predictions)

        # 2.0 因果関係に基づく予測
        causal_predictions = self._predict_causal_patterns(context)
        predictions.extend(causal_predictions)

        # 3.0 環境パターンに基づく予測
        environmental_predictions = self._predict_environmental_patterns(context)
        predictions.extend(environmental_predictions)

        # 4.0 予測の統合と優先順位付け
        merged_predictions = self._merge_predictions(predictions)

        # 予測を記録
        for pred in merged_predictions:
            self._record_prediction(pred)

        return sorted(merged_predictions, key=lambda p: p.risk_score, reverse=True)

    def _predict_temporal_patterns(
        self, current_time: datetime
    ) -> List[ErrorPrediction]:
        """時間的パターンに基づく予測"""
        predictions = []

        # 曜日と時間帯のパターンを分析
        with sqlite3connect(self.db_path) as conn:
            # 同じ曜日・時間帯のエラー頻度を取得
            cursor = conn.execute(
                """
                SELECT error_type, COUNT(*) as freq, AVG(fix_duration) as avg_fix
                FROM error_occurrences
                WHERE day_of_week = ?
                AND ABS(hour_of_day - ?) <= 1
                AND occurred_at > datetime('now', '-30 days')
                GROUP BY error_type
                HAVING freq >= ?
            """,
                (
                    current_time.weekday(),
                    current_time.hour,
                    self.min_occurrences_for_pattern,
                ),
            )

            for row in cursor:
                error_type, frequency, avg_fix_time = row

                # 発生確率を計算
                probability = min(frequency / 30.0, 0.9)  # 30日間での頻度

                # 予防アクションを生成
                preventive_actions = self._generate_preventive_actions(
                    error_type, "temporal"
                )

                prediction = ErrorPrediction(
                    error_type=error_type,
                    probability=probability,
                    confidence=self._calculate_confidence(frequency, "temporal"),
                    time_window=f"Next {self.prediction_horizon_hours} hours",
                    preventive_actions=preventive_actions,
                    risk_score=probability * (avg_fix_time or 60) / 60,  # リスクスコア
                    rationale=f"Historical pattern: {frequency} occurrences at this time",
                )

                predictions.append(prediction)

        return predictions

    def _predict_causal_patterns(
        self, context: Optional[Dict]
    ) -> List[ErrorPrediction]:
        """因果関係に基づく予測"""
        predictions = []

        if not context:
            return predictions

        # 最近のイベントから因果関係を確認
        recent_events = context.get("recent_events", [])

        with sqlite3connect(self.db_path) as conn:
            for event in recent_events:
            # 繰り返し処理
                cursor = conn.execute(
                    """
                    SELECT effect_error, correlation_strength, avg_delay_minutes
                    FROM causal_relationships
                    WHERE cause_event = ?
                    AND correlation_strength > 0.6
                """,
                    (event,),
                )

                for row in cursor:
                    effect_error, correlation, avg_delay = row

                    # 時間的に予測範囲内かチェック
                    if avg_delay <= self.prediction_horizon_hours * 60:
                        probability = correlation * 0.8  # 因果関係の強さを確率に変換

                        preventive_actions = self._generate_preventive_actions(
                            effect_error, "causal", {"trigger": event}
                        )

                        prediction = ErrorPrediction(
                            error_type=effect_error,
                            probability=probability,
                            confidence=self._calculate_confidence(
                                correlation, "causal"
                            ),
                            time_window=f"Within {int(avg_delay)} minutes",
                            preventive_actions=preventive_actions,
                            risk_score=probability * 1.5,  # 因果関係は高リスク
                            rationale=f"Causal relationship with {event}",
                        )

                        predictions.append(prediction)

        return predictions

    def _predict_environmental_patterns(
        self, context: Optional[Dict]
    ) -> List[ErrorPrediction]:
        """環境パターンに基づく予測"""
        predictions = []

        system_state = self._get_system_state()

        # メモリ使用率が高い場合
        if system_state.get("memory_usage", 0) > 80:
            predictions.append(
                ErrorPrediction(
                    error_type="MemoryError",
                    probability=0.7,
                    confidence=0.8,
                    time_window="Imminent",
                    preventive_actions=[
                        {
                            "action": "cleanup_memory",
                            "command": "python3 scripts/cleanup_memory.py",
                            "priority": "high",
                        }
                    ],
                    risk_score=0.9,
                    rationale=f"Memory usage at {system_state['memory_usage']}%",
                )
            )

        # ディスク使用率が高い場合
        if system_state.get("disk_usage", 0) > 90:
            predictions.append(
                ErrorPrediction(
                    error_type="IOError",
                    probability=0.8,
                    confidence=0.9,
                    time_window="Imminent",
                    preventive_actions=[
                        {
                            "action": "cleanup_disk",
                            "command": "bash scripts/cleanup_old_files.sh",
                            "priority": "critical",
                        }
                    ],
                    risk_score=0.95,
                    rationale=f"Disk usage at {system_state['disk_usage']}%",
                )
            )

        return predictions

    def _learn_from_occurrence(
        self, error_hash: str, error_info: Dict, context: Dict, occurred_at: datetime
    ):
        """エラー発生から学習"""
        # 時間的パターンの学習
        self._learn_temporal_pattern(error_info, occurred_at)

        # 因果関係の学習
        self._learn_causal_relationships(error_info, context)

        # 環境パターンの学習
        self._learn_environmental_patterns(error_info, context)

    def _learn_temporal_pattern(self, error_info: Dict, occurred_at: datetime):
        """時間的パターンを学習"""
        error_type = error_info.get("error_type", "unknown")

        # 時間帯別の発生頻度を更新
        pattern_key = (
            f"temporal_{error_type}_{occurred_at.weekday()}_{occurred_at.hour}"
        )

        with sqlite3connect(self.db_path) as conn:
            # 既存パターンを確認
            cursor = conn.execute(
                "SELECT pattern_data, occurrences FROM learned_patterns WHERE pattern_id = ?",
                (pattern_key,),
            )
            row = cursor.fetchone()

            if row:
                pattern_data = json.loads(row[0])
                occurrences = row[1] + 1
                pattern_data["times"].append(occurred_at.isoformat())
            else:
                pattern_data = {
                    "day_of_week": occurred_at.weekday(),
                    "hour": occurred_at.hour,
                    "times": [occurred_at.isoformat()],
                }
                occurrences = 1

            # パターンを更新
            confidence = min(occurrences / 10.0, 0.95)  # 10回で95%の信頼度

            conn.execute(
                """
                INSERT OR REPLACE INTO learned_patterns
                (pattern_id, error_type, pattern_type, pattern_data,
                 confidence, occurrences, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    pattern_key,
                    error_type,
                    "temporal",
                    json.dumps(pattern_data),
                    confidence,
                    occurrences,
                    datetime.now(),
                ),
            )

    def _learn_causal_relationships(self, error_info: Dict, context: Dict):
        """因果関係を学習"""
        recent_events = context.get("recent_events", [])
        error_type = error_info.get("error_type", "unknown")

        with sqlite3connect(self.db_path) as conn:
            for event in recent_events[-5:]:  # 直近5イベントを確認
                # 既存の関係を確認
                cursor = conn.execute(
                    """
                    SELECT id, correlation_strength, occurrence_count
                    FROM causal_relationships
                    WHERE cause_event = ? AND effect_error = ?
                """,
                    (event, error_type),
                )

                row = cursor.fetchone()

                if row:
                    # 相関を強化
                    rel_id, current_correlation, count = row
                    new_correlation = min(
                        current_correlation + (1 - current_correlation) * 0.1, 0.99
                    )

                    conn.execute(
                        """
                        UPDATE causal_relationships
                        SET correlation_strength = ?, occurrence_count = ?, last_observed = ?
                        WHERE id = ?
                    """,
                        (new_correlation, count + 1, datetime.now(), rel_id),
                    )
                else:
                    # 新しい関係を記録
                    conn.execute(
                        """
                        INSERT INTO causal_relationships
                        (cause_event, effect_error, correlation_strength,
                         avg_delay_minutes, occurrence_count, last_observed)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (event, error_type, 0.3, 30, 1, datetime.now()),
                    )

    def _generate_preventive_actions(
        self, error_type: str, pattern_type: str, context: Optional[Dict] = None
    ) -> List[Dict]:
        """予防アクションを生成"""
        actions = []

        # エラータイプ別の標準アクション
        standard_actions = {
            "ImportError": [
                {
                    "action": "verify_dependencies",
                    "command": "pip check",
                    "priority": "medium",
                },
                {
                    "action": "update_requirements",
                    "command": "pip freeze > requirements.txt",
                    "priority": "low",
                },
            ],
            "MemoryError": [
                {
                    "action": "free_memory",
                    "command": "python3 scripts/memory_cleanup.py",
                    "priority": "high",
                },
                {
                    "action": "restart_workers",
                    "command": "ai-restart --workers-only",
                    "priority": "medium",
                },
            ],
            "FileNotFoundError": [
                {
                    "action": "verify_paths",
                    "command": "python3 scripts/verify_file_paths.py",
                    "priority": "medium",
                }
            ],
            "ConnectionError": [
                {
                    "action": "check_services",
                    "command": "systemctl status rabbitmq-server",
                    "priority": "high",
                },
                {
                    "action": "restart_network",
                    "command": "sudo systemctl restart NetworkManager",
                    "priority": "medium",
                },
            ],
        }

        # 標準アクションを追加
        if error_type in standard_actions:
            actions.extend(standard_actions[error_type])

        # パターンタイプ別の追加アクション
        if pattern_type == "temporal":
            actions.append(
                {
                    "action": "schedule_preventive_maintenance",
                    "command": f"at now + 1 hour -f scripts/preventive_check.sh",
                    "priority": "low",
                }
            )
        elif pattern_type == "causal" and context:
            trigger = context.get("trigger")
            actions.append(
                {
                    "action": "monitor_trigger",
                    "command": f'python3 scripts/monitor_event.py --event "{trigger}"',
                    "priority": "medium",
                }
            )

        return actions

    def _calculate_confidence(self, value: float, pattern_type: str) -> float:
        """信頼度を計算"""
        if pattern_type == "temporal":
            # 発生回数に基づく
            return min(value / 10.0, 0.95)
        elif pattern_type == "causal":
            # 相関強度をそのまま使用
            return value
        elif pattern_type == "environmental":
            # 環境パターンは高信頼度
            return 0.9
        else:
            return 0.5

    def _compute_error_hash(self, error_info: Dict) -> str:
        """エラーのハッシュを計算"""
        key_parts = [
            error_info.get("error_type", "unknown"),
            error_info.get("error_pattern", ""),
            error_info.get("category", ""),
        ]
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_system_state(self) -> Dict:
        """システム状態を取得"""
        try:
            import psutil

            return {
                "memory_usage": psutil.virtual_memory().percent,
                "cpu_usage": psutil.cpu_percent(interval=1),
                "disk_usage": psutil.disk_usage("/").percent,
                "active_processes": len(psutil.pids()),
                "timestamp": datetime.now().isoformat(),
            }
        except:
            return {
                "memory_usage": 0,
                "cpu_usage": 0,
                "disk_usage": 0,
                "active_processes": 0,
                "timestamp": datetime.now().isoformat(),
            }

    def _get_recent_events(self, minutes: int = 30) -> List[str]:
        """最近のイベントを取得"""
        # TODO: 実際のイベントログから取得
        # 現在はモックデータ
        return ["git_push", "worker_restart", "config_update"]

    def _merge_predictions(
        self, predictions: List[ErrorPrediction]
    ) -> List[ErrorPrediction]:
        """重複する予測をマージ"""
        merged = {}

        for pred in predictions:
            key = pred.error_type
            if key in merged:
                # より高い確率を採用
                if pred.probability > merged[key].probability:
                    merged[key] = pred
                else:
                    # アクションをマージ
                    merged[key].preventive_actions.extend(pred.preventive_actions)
            else:
                merged[key] = pred

        return list(merged.values())

    def _record_prediction(self, prediction: ErrorPrediction):
        """予測を記録"""
        prediction_id = (
            f"pred_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{prediction.error_type}"
        )

        with sqlite3connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO predictions
                (prediction_id, error_type, predicted_at, prediction_window,
                 probability, confidence, prevented, actual_occurred)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    prediction_id,
                    prediction.error_type,
                    datetime.now(),
                    prediction.time_window,
                    prediction.probability,
                    prediction.confidence,
                    False,
                    False,
                ),
            )

    def _load_patterns(self):
        """既存のパターンをキャッシュに読み込む"""
        with sqlite3connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT pattern_id, pattern_data, confidence FROM learned_patterns"
            )
            for row in cursor:
                self.pattern_cache[row[0]] = {
                    "data": json.loads(row[1]),
                    "confidence": row[2],
                }

    def update_prediction_feedback(
        self, prediction_id: str, actual_occurred: bool, prevented: bool = False
    ):
        """予測の実際の結果をフィードバック"""
        with sqlite3connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE predictions
                SET actual_occurred = ?, prevented = ?, feedback = ?
                WHERE prediction_id = ?
            """,
                (actual_occurred, prevented, datetime.now().isoformat(), prediction_id),
            )

    def get_prediction_accuracy(self, days: int = 7) -> Dict:
        """予測精度を計算"""
        with sqlite3connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN actual_occurred = 1 AND probability > 0.5 THEN 1 ELSE 0 END) as true_positive,
                    SUM(CASE WHEN actual_occurred = 0 AND probability <= 0.5 THEN 1 ELSE 0 END) as true_negative,
                    SUM(CASE WHEN actual_occurred = 0 AND probability > 0.5 THEN 1 ELSE 0 END) as false_positive,
                    SUM(CASE WHEN actual_occurred = 1 AND probability <= 0.5 THEN 1 ELSE 0 END) as false_negative,
                    SUM(CASE WHEN prevented = 1 THEN 1 ELSE 0 END) as prevented_count
                FROM predictions
                WHERE predicted_at > datetime('now', '-{} days')
            """.format(
                    days
                )
            )

            row = cursor.fetchone()
            if row and row[0] > 0:
                total, tp, tn, fp, fn, prevented = row

                accuracy = (tp + tn) / total if total > 0 else 0
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0
                f1_score = (
                    2 * (precision * recall) / (precision + recall)
                    if (precision + recall) > 0
                    else 0
                )

                return {
                    "total_predictions": total,
                    "accuracy": accuracy,
                    "precision": precision,
                    "recall": recall,
                    "f1_score": f1_score,
                    "prevented_errors": prevented,
                    "prevention_rate": prevented / total if total > 0 else 0,
                }

        return {
            "total_predictions": 0,
            "accuracy": 0,
            "precision": 0,
            "recall": 0,
            "f1_score": 0,
            "prevented_errors": 0,
            "prevention_rate": 0,
        }


if __name__ == "__main__":
    # テスト実行
    predictor = ErrorPatternPredictor()

    print("=== Error Pattern Predictor Test ===")

    # テストエラーの記録
    test_errors = [
        {
            "error_type": "ImportError",
            "error_message": "No module named 'test_module'",
            "worker_type": "task",
        },
        {
            "error_type": "MemoryError",
            "error_message": "Unable to allocate memory",
            "worker_type": "task",
        },
    ]

    for error in test_errors:
        error_hash = predictor.record_error_occurrence(error)
        print(f"Recorded error: {error['error_type']} (hash: {error_hash})")

    # 予測実行
    print("\n=== Error Predictions ===")
    predictions = predictor.predict_errors()

    # 繰り返し処理
    for pred in predictions:
        print(f"\nError Type: {pred.error_type}")
        print(f"Probability: {pred.probability:0.2%}")
        print(f"Confidence: {pred.confidence:0.2%}")
        print(f"Time Window: {pred.time_window}")
        print(f"Risk Score: {pred.risk_score:0.2f}")
        print(f"Rationale: {pred.rationale}")

        if pred.preventive_actions:
            print("Preventive Actions:")
            for action in pred.preventive_actions:
                print(
                    f"  - {action['action']}: {action['command']} (Priority: {action['priority']})"
                )

    # 精度統計
    print("\n=== Prediction Accuracy ===")
    accuracy = predictor.get_prediction_accuracy()
    print(json.dumps(accuracy, indent=2))
