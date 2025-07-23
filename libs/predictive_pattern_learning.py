#!/usr/bin/env python3
"""
🔮 Predictive Pattern Learning System
予測的パターン学習システム

Task Sageの戦略に基づく予測的タスク実行最適化システム
過去の成功パターンを学習し、将来の実行を予測・最適化

Author: Claude Elder
Date: 2025-07-10
Phase: 1 (予測的パターン学習システム導入)
"""

import asyncio
import hashlib
import json
import logging
import pickle
import sqlite3
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent


class ExecutionPattern(Enum):
    """実行パターン種別"""

    SEQUENTIAL = "sequential"  # 順次実行
    PARALLEL = "parallel"  # 並列実行
    CONDITIONAL = "conditional"  # 条件分岐
    LOOP = "loop"  # ループ処理
    RECURSIVE = "recursive"  # 再帰処理
    BATCH = "batch"  # バッチ処理


class TaskComplexity(Enum):
    """タスク複雑度"""

    SIMPLE = "simple"  # 単純（1-10分）
    MEDIUM = "medium"  # 中程度（10-60分）
    COMPLEX = "complex"  # 複雑（1-8時間）
    EPIC = "epic"  # 史詩級（1日以上）


class SuccessMetrics(Enum):
    """成功指標"""

    COMPLETION_TIME = "completion_time"
    RESOURCE_USAGE = "resource_usage"
    ERROR_RATE = "error_rate"
    QUALITY_SCORE = "quality_score"
    USER_SATISFACTION = "user_satisfaction"


@dataclass
class TaskExecutionRecord:
    """タスク実行記録"""

    task_id: str
    task_type: str
    complexity: TaskComplexity
    pattern: ExecutionPattern
    start_time: datetime
    end_time: Optional[datetime]
    success: bool
    completion_time: float
    resource_usage: Dict[str, float]
    error_count: int
    quality_score: float
    context: Dict[str, Any]
    dependencies: List[str]

    def __post_init__(self):
        if self.end_time is None:
            self.end_time = datetime.now()
        if self.completion_time == 0:
            self.completion_time = (self.end_time - self.start_time).total_seconds()


@dataclass
class PredictionResult:
    """予測結果"""

    task_id: str
    predicted_pattern: ExecutionPattern
    predicted_completion_time: float
    predicted_resource_usage: Dict[str, float]
    predicted_success_rate: float
    confidence: float
    reasoning: str
    recommended_optimizations: List[str]


@dataclass
class PatternLearningModel:
    """パターン学習モデル"""

    model_id: str
    model_type: str
    trained_at: datetime
    accuracy: float
    feature_importance: Dict[str, float]
    model_data: bytes
    training_samples: int


class PredictivePatternLearningSystem:
    """予測的パターン学習システム"""

    def __init__(self, db_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path or str(PROJECT_ROOT / "data" / "predictive_patterns.db")

        # 学習モデル
        self.completion_time_model = RandomForestRegressor(
            n_estimators=100, random_state=42
        )
        self.success_prediction_model = GradientBoostingClassifier(
            n_estimators=100, random_state=42
        )
        self.pattern_classifier = GradientBoostingClassifier(
            n_estimators=100, random_state=42
        )

        # 前処理器
        self.scaler = StandardScaler()

        # キャッシュ
        self.execution_cache = {}
        self.pattern_cache = {}
        self.model_cache = {}

        # 学習データ
        self.training_data = []
        self.is_trained = False

        # 並列処理用ロック
        self.lock = threading.Lock()

        # データベース初期化
        self._init_database()

        # 既存データ読み込み
        self._load_existing_data()

        self.logger.info("🔮 Predictive Pattern Learning System initialized")

    def _init_database(self):
        """データベース初期化"""
        try:
            # データディレクトリ作成
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # タスク実行記録テーブル
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS task_execution_records (
                    task_id TEXT PRIMARY KEY,
                    task_type TEXT,
                    complexity TEXT,
                    execution_pattern TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    success BOOLEAN,
                    completion_time REAL,
                    resource_usage TEXT,
                    error_count INTEGER,
                    quality_score REAL,
                    context TEXT,
                    dependencies TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """
            )

            # パターン学習モデルテーブル
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS pattern_models (
                    model_id TEXT PRIMARY KEY,
                    model_type TEXT,
                    trained_at TEXT,
                    accuracy REAL,
                    feature_importance TEXT,
                    model_data BLOB,
                    training_samples INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """
            )

            # 予測結果テーブル
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS prediction_results (
                    prediction_id TEXT PRIMARY KEY,
                    task_id TEXT,
                    predicted_pattern TEXT,
                    predicted_completion_time REAL,
                    predicted_resource_usage TEXT,
                    predicted_success_rate REAL,
                    confidence REAL,
                    reasoning TEXT,
                    recommended_optimizations TEXT,
                    actual_completion_time REAL,
                    actual_success BOOLEAN,
                    prediction_accuracy REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """
            )

            # インデックス作成
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_type ON task_execution_records(task_type);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_complexity ON task_execution_records(complexity);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_execution_pattern ON " \
                    "task_execution_records(execution_pattern);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_success ON task_execution_records(success);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_start_time ON task_execution_records(start_time);"
            )

            conn.commit()
            conn.close()

            self.logger.info("🗄️ Pattern learning database initialized")

        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise

    def _load_existing_data(self):
        """既存データ読み込み"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 実行記録読み込み
            cursor.execute(
                "SELECT * FROM task_execution_records ORDER BY start_time DESC LIMIT 1000"
            )
            records = cursor.fetchall()

            for record in records:
                execution_record = TaskExecutionRecord(
                    task_id=record[0],
                    task_type=record[1],
                    complexity=TaskComplexity(record[2]),
                    pattern=ExecutionPattern(record[3]),
                    start_time=datetime.fromisoformat(record[4]),
                    end_time=datetime.fromisoformat(record[5]) if record[5] else None,
                    success=bool(record[6]),
                    completion_time=record[7],
                    resource_usage=json.loads(record[8]),
                    error_count=record[9],
                    quality_score=record[10],
                    context=json.loads(record[11]),
                    dependencies=json.loads(record[12]),
                )
                self.training_data.append(execution_record)

            conn.close()

            self.logger.info(f"📊 Loaded {len(self.training_data)} execution records")

            # 十分なデータがあれば学習実行
            if len(self.training_data) >= 10:
                asyncio.create_task(self._train_models())

        except Exception as e:
            self.logger.error(f"Data loading failed: {e}")

    async def record_execution(self, execution_record: TaskExecutionRecord):
        """実行記録保存"""
        try:
            with self.lock:
                # メモリに追加
                self.training_data.append(execution_record)

                # キャッシュ更新
                self.execution_cache[execution_record.task_id] = execution_record

                # データベース保存
                await self._store_execution_record(execution_record)

                self.logger.info(f"📝 Execution recorded: {execution_record.task_id}")

                # 一定数蓄積したら再学習
                if len(self.training_data) % 50 == 0:
                    asyncio.create_task(self._train_models())

        except Exception as e:
            self.logger.error(f"Execution recording failed: {e}")

    async def predict_execution_pattern(
        self,
        task_type: str,
        complexity: TaskComplexity,
        context: Dict[str, Any] = None,
        dependencies: List[str] = None,
    ) -> PredictionResult:
        """実行パターン予測"""
        try:
            # 特徴量準備
            features = self._prepare_features(
                task_type, complexity, context, dependencies
            )

            if not self.is_trained:
                # 学習データが不足している場合は基本予測
                return await self._basic_prediction(
                    task_type, complexity, context, dependencies
                )

            # パターン予測
            predicted_pattern = await self._predict_pattern(features)

            # 完了時間予測
            predicted_completion_time = await self._predict_completion_time(features)

            # リソース使用量予測
            predicted_resource_usage = await self._predict_resource_usage(features)

            # 成功率予測
            predicted_success_rate = await self._predict_success_rate(features)

            # 信頼度計算
            confidence = await self._calculate_confidence(features)

            # 推論理由生成
            reasoning = await self._generate_reasoning(
                features, predicted_pattern, predicted_completion_time
            )

            # 最適化推奨
            recommended_optimizations = await self._generate_optimizations(
                predicted_pattern, predicted_completion_time, predicted_success_rate
            )

            task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(task_type.encode()).hexdigest()[:8]}"

            prediction_result = PredictionResult(
                task_id=task_id,
                predicted_pattern=predicted_pattern,
                predicted_completion_time=predicted_completion_time,
                predicted_resource_usage=predicted_resource_usage,
                predicted_success_rate=predicted_success_rate,
                confidence=confidence,
                reasoning=reasoning,
                recommended_optimizations=recommended_optimizations,
            )

            # 予測結果保存
            await self._store_prediction_result(prediction_result)

            self.logger.info(f"🔮 Prediction completed: {task_id}")
            return prediction_result

        except Exception as e:
            self.logger.error(f"Pattern prediction failed: {e}")
            return await self._basic_prediction(
                task_type, complexity, context, dependencies
            )

    async def learn_from_failure(self, task_id: str, failure_details: Dict[str, Any]):
        """失敗からの学習"""
        try:
            if task_id in self.execution_cache:
                execution_record = self.execution_cache[task_id]

                # 失敗情報を追加
                execution_record.success = False
                execution_record.context.update(failure_details)

                # 失敗パターン分析
                failure_pattern = await self._analyze_failure_pattern(
                    execution_record, failure_details
                )

                # 学習データ更新
                await self.record_execution(execution_record)

                # 失敗パターンをキャッシュに保存
                failure_key = (
                    f"{execution_record.task_type}_{execution_record.complexity.value}"
                )
                if failure_key not in self.pattern_cache:
                    self.pattern_cache[failure_key] = []
                self.pattern_cache[failure_key].append(failure_pattern)

                self.logger.info(f"📚 Learned from failure: {task_id}")

                # 即座に再学習
                await self._train_models()

        except Exception as e:
            self.logger.error(f"Failure learning failed: {e}")

    async def optimize_execution_strategy(
        self, prediction: PredictionResult, constraints: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """実行戦略最適化"""
        try:
            optimization_strategy = {
                "original_prediction": prediction,
                "optimizations": [],
                "expected_improvement": {},
                "implementation_steps": [],
            }

            # 時間最適化
            if prediction.predicted_completion_time > 3600:  # 1時間以上
                time_optimization = await self._optimize_completion_time(prediction)
                optimization_strategy["optimizations"].append(time_optimization)

            # リソース最適化
            if any(
                usage > 0.8 for usage in prediction.predicted_resource_usage.values()
            ):
                resource_optimization = await self._optimize_resource_usage(prediction)
                optimization_strategy["optimizations"].append(resource_optimization)

            # 成功率最適化
            if prediction.predicted_success_rate < 0.9:
                success_optimization = await self._optimize_success_rate(prediction)
                optimization_strategy["optimizations"].append(success_optimization)

            # 制約条件適用
            if constraints:
                optimization_strategy = await self._apply_constraints(
                    optimization_strategy, constraints
                )

            # 期待改善効果計算
            optimization_strategy["expected_improvement"] = (
                await self._calculate_expected_improvement(
                    prediction, optimization_strategy["optimizations"]
                )
            )

            # 実装手順生成
            optimization_strategy["implementation_steps"] = (
                await self._generate_implementation_steps(
                    optimization_strategy["optimizations"]
                )
            )

            return optimization_strategy

        except Exception as e:
            self.logger.error(f"Execution strategy optimization failed: {e}")
            return {"error": str(e)}

    async def continuous_learning(self):
        """継続学習"""
        try:
            while True:
                # 1時間毎に実行
                await asyncio.sleep(3600)

                # 新しいデータがあれば学習
                if len(self.training_data) > 0:
                    await self._train_models()

                    # パフォーマンス評価
                    performance_metrics = await self._evaluate_performance()

                    # モデル品質チェック
                    if performance_metrics.get("accuracy", 0) < 0.7:
                        await self._retrain_with_enhanced_features()

                    self.logger.info(f"🔄 Continuous learning cycle completed")

        except Exception as e:
            self.logger.error(f"Continuous learning failed: {e}")

    async def _train_models(self):
        """モデル学習"""
        try:
            if len(self.training_data) < 10:
                self.logger.warning("Insufficient training data")
                return

            # 特徴量準備
            X, y_completion_time, y_success, y_pattern = self._prepare_training_data()

            if len(X) == 0:
                self.logger.warning("No valid training data")
                return

            # データ分割
            X_train, X_test, y_completion_train, y_completion_test = train_test_split(
                X, y_completion_time, test_size=0.2, random_state=42
            )

            # 正規化
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # 完了時間予測モデル学習
            self.completion_time_model.fit(X_train_scaled, y_completion_train)
            completion_time_accuracy = self.completion_time_model.score(
                X_test_scaled, y_completion_test
            )

            # 成功率予測モデル学習
            if len(set(y_success)) > 1:  # 成功・失敗両方のデータがある場合
                self.success_prediction_model.fit(
                    X_train_scaled, y_success[: len(X_train_scaled)]
                )
                success_accuracy = self.success_prediction_model.score(
                    X_test_scaled, y_success[: len(X_test_scaled)]
                )
            else:
                success_accuracy = 0.0

            # パターン分類モデル学習
            if len(set(y_pattern)) > 1:  # 複数パターンがある場合
                self.pattern_classifier.fit(
                    X_train_scaled, y_pattern[: len(X_train_scaled)]
                )
                pattern_accuracy = self.pattern_classifier.score(
                    X_test_scaled, y_pattern[: len(X_test_scaled)]
                )
            else:
                pattern_accuracy = 0.0

            self.is_trained = True

            # モデル保存
            await self._save_models(
                {
                    "completion_time_accuracy": completion_time_accuracy,
                    "success_accuracy": success_accuracy,
                    "pattern_accuracy": pattern_accuracy,
                }
            )

            self.logger.info(
                f"🎯 Models trained: CT={completion_time_accuracy:.3f}, S={success_accuracy:.3f}, P={pattern_accuracy:.3f}"
            )

        except Exception as e:
            self.logger.error(f"Model training failed: {e}")

    def _prepare_features(
        self,
        task_type: str,
        complexity: TaskComplexity,
        context: Dict[str, Any] = None,
        dependencies: List[str] = None,
    ) -> np.ndarray:
        """特徴量準備"""
        features = []

        # タスクタイプ特徴 (ワンホットエンコーディング)
        task_types = [
            "development",
            "testing",
            "deployment",
            "analysis",
            "optimization",
            "maintenance",
        ]
        for task_type_option in task_types:
            features.append(1 if task_type == task_type_option else 0)

        # 複雑度特徴
        complexity_encoding = {
            TaskComplexity.SIMPLE: [1, 0, 0, 0],
            TaskComplexity.MEDIUM: [0, 1, 0, 0],
            TaskComplexity.COMPLEX: [0, 0, 1, 0],
            TaskComplexity.EPIC: [0, 0, 0, 1],
        }
        features.extend(complexity_encoding[complexity])

        # コンテキスト特徴
        if context:
            features.extend(
                [
                    context.get("priority", 0.5),
                    context.get("resource_limit", 1.0),
                    context.get("deadline_pressure", 0.5),
                    len(context.get("requirements", [])),
                    len(context.get("stakeholders", [])),
                    context.get("risk_level", 0.5),
                ]
            )
        else:
            features.extend([0.5, 1.0, 0.5, 0, 0, 0.5])

        # 依存関係特徴
        if dependencies:
            features.extend(
                [
                    len(dependencies),
                    len([d for d in dependencies if "critical" in d.lower()]),
                    len([d for d in dependencies if "optional" in d.lower()]),
                ]
            )
        else:
            features.extend([0, 0, 0])

        # 時間特徴
        now = datetime.now()
        features.extend([now.hour / 24.0, now.weekday() / 7.0, now.month / 12.0])

        return np.array(features)

    def _prepare_training_data(
        self,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """学習データ準備"""
        X = []
        y_completion_time = []
        y_success = []
        y_pattern = []

        for record in self.training_data:
            try:
                features = self._prepare_features(
                    record.task_type,
                    record.complexity,
                    record.context,
                    record.dependencies,
                )

                X.append(features)
                y_completion_time.append(record.completion_time)
                y_success.append(1 if record.success else 0)

                # パターンを数値エンコーディング
                pattern_encoding = {
                    ExecutionPattern.SEQUENTIAL: 0,
                    ExecutionPattern.PARALLEL: 1,
                    ExecutionPattern.CONDITIONAL: 2,
                    ExecutionPattern.LOOP: 3,
                    ExecutionPattern.RECURSIVE: 4,
                    ExecutionPattern.BATCH: 5,
                }
                y_pattern.append(pattern_encoding[record.pattern])

            except Exception as e:
                self.logger.warning(f"Skipping invalid training record: {e}")
                continue

        return (
            np.array(X),
            np.array(y_completion_time),
            np.array(y_success),
            np.array(y_pattern),
        )

    async def _predict_pattern(self, features: np.ndarray) -> ExecutionPattern:
        """パターン予測"""
        if not self.is_trained:
            return ExecutionPattern.SEQUENTIAL

        try:
            features_scaled = self.scaler.transform([features])
            prediction = self.pattern_classifier.predict(features_scaled)[0]

            pattern_decoding = {
                0: ExecutionPattern.SEQUENTIAL,
                1: ExecutionPattern.PARALLEL,
                2: ExecutionPattern.CONDITIONAL,
                3: ExecutionPattern.LOOP,
                4: ExecutionPattern.RECURSIVE,
                5: ExecutionPattern.BATCH,
            }

            return pattern_decoding.get(prediction, ExecutionPattern.SEQUENTIAL)

        except Exception as e:
            self.logger.warning(f"Pattern prediction failed: {e}")
            return ExecutionPattern.SEQUENTIAL

    async def _predict_completion_time(self, features: np.ndarray) -> float:
        """完了時間予測"""
        if not self.is_trained:
            return 3600.0  # デフォルト1時間

        try:
            features_scaled = self.scaler.transform([features])
            prediction = self.completion_time_model.predict(features_scaled)[0]
            return max(60.0, prediction)  # 最低1分

        except Exception as e:
            self.logger.warning(f"Completion time prediction failed: {e}")
            return 3600.0

    async def _predict_resource_usage(self, features: np.ndarray) -> Dict[str, float]:
        """リソース使用量予測"""
        # 簡略化実装
        return {"cpu": 0.5, "memory": 0.3, "disk": 0.2, "network": 0.1}

    async def _predict_success_rate(self, features: np.ndarray) -> float:
        """成功率予測"""
        if not self.is_trained:
            return 0.8  # デフォルト80%

        try:
            features_scaled = self.scaler.transform([features])
            prediction = self.success_prediction_model.predict_proba(features_scaled)[0]
            return prediction[1] if len(prediction) > 1 else 0.8

        except Exception as e:
            self.logger.warning(f"Success rate prediction failed: {e}")
            return 0.8

    async def _calculate_confidence(self, features: np.ndarray) -> float:
        """信頼度計算"""
        if not self.is_trained:
            return 0.3

        # 学習データとの類似度に基づく信頼度
        try:
            training_features, _, _, _ = self._prepare_training_data()
            if len(training_features) == 0:
                return 0.3

            # 最近傍との距離計算
            distances = []
            for train_feature in training_features:
                if len(train_feature) == len(features):
                    distance = np.linalg.norm(features - train_feature)
                    distances.append(distance)

            if not distances:
                return 0.3

            # 最小距離に基づく信頼度
            min_distance = min(distances)
            confidence = max(0.1, 1.0 - min_distance / 10.0)

            return min(1.0, confidence)

        except Exception as e:
            self.logger.warning(f"Confidence calculation failed: {e}")
            return 0.3

    async def _generate_reasoning(
        self,
        features: np.ndarray,
        predicted_pattern: ExecutionPattern,
        predicted_completion_time: float,
    ) -> str:
        """推論理由生成"""
        reasoning_parts = []

        # パターン推論
        reasoning_parts.append(f"推奨実行パターン: {predicted_pattern.value}")

        # 時間推論
        if predicted_completion_time < 600:  # 10分未満
            reasoning_parts.append("短時間での完了が期待されます")
        elif predicted_completion_time < 3600:  # 1時間未満
            reasoning_parts.append("中程度の時間での完了が期待されます")
        else:
            reasoning_parts.append("長時間の実行が予想されます")

        # 過去の類似タスクからの学習
        if len(self.training_data) > 0:
            similar_tasks = len(
                [r for r in self.training_data if r.pattern == predicted_pattern]
            )
            reasoning_parts.append(
                f"過去の類似タスク {similar_tasks} 件のデータに基づく予測"
            )

        return "。".join(reasoning_parts)

    async def _generate_optimizations(
        self,
        predicted_pattern: ExecutionPattern,
        predicted_completion_time: float,
        predicted_success_rate: float,
    ) -> List[str]:
        """最適化推奨生成"""
        optimizations = []

        # 時間最適化
        if predicted_completion_time > 3600:
            optimizations.append("並列処理による時間短縮")
            optimizations.append("タスク分割による効率化")

        # 成功率最適化
        if predicted_success_rate < 0.9:
            optimizations.append("エラー処理の強化")
            optimizations.append("依存関係の事前チェック")

        # パターン別最適化
        if predicted_pattern == ExecutionPattern.SEQUENTIAL:
            optimizations.append("並列実行可能な部分の特定")
        elif predicted_pattern == ExecutionPattern.PARALLEL:
            optimizations.append("リソース競合の回避")
        elif predicted_pattern == ExecutionPattern.LOOP:
            optimizations.append("ループ最適化とバッチ処理")

        return optimizations

    async def _basic_prediction(
        self,
        task_type: str,
        complexity: TaskComplexity,
        context: Dict[str, Any] = None,
        dependencies: List[str] = None,
    ) -> PredictionResult:
        """基本予測（学習データ不足時）"""

        # 複雑度に基づく基本予測
        complexity_predictions = {
            TaskComplexity.SIMPLE: {
                "time": 600,  # 10分
                "pattern": ExecutionPattern.SEQUENTIAL,
                "success_rate": 0.95,
            },
            TaskComplexity.MEDIUM: {
                "time": 3600,  # 1時間
                "pattern": ExecutionPattern.PARALLEL,
                "success_rate": 0.85,
            },
            TaskComplexity.COMPLEX: {
                "time": 14400,  # 4時間
                "pattern": ExecutionPattern.CONDITIONAL,
                "success_rate": 0.75,
            },
            TaskComplexity.EPIC: {
                "time": 86400,  # 24時間
                "pattern": ExecutionPattern.BATCH,
                "success_rate": 0.65,
            },
        }

        base_prediction = complexity_predictions[complexity]

        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(task_type.encode()).hexdigest()[:8]}"

        return PredictionResult(
            task_id=task_id,
            predicted_pattern=base_prediction["pattern"],
            predicted_completion_time=base_prediction["time"],
            predicted_resource_usage={
                "cpu": 0.5,
                "memory": 0.3,
                "disk": 0.2,
                "network": 0.1,
            },
            predicted_success_rate=base_prediction["success_rate"],
            confidence=0.3,
            reasoning=f"基本予測: {complexity.value}レベルのタスクに基づく推定",
            recommended_optimizations=["十分な学習データを蓄積してください"],
        )

    async def _store_execution_record(self, record: TaskExecutionRecord):
        """実行記録保存"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO task_execution_records
                (task_id, task_type, complexity, execution_pattern, start_time, end_time,
                 success, completion_time, resource_usage, error_count, quality_score,
                 context, dependencies)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    record.task_id,
                    record.task_type,
                    record.complexity.value,
                    record.pattern.value,
                    record.start_time.isoformat(),
                    record.end_time.isoformat() if record.end_time else None,
                    record.success,
                    record.completion_time,
                    json.dumps(record.resource_usage),
                    record.error_count,
                    record.quality_score,
                    json.dumps(record.context),
                    json.dumps(record.dependencies),
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Execution record storage failed: {e}")

    async def _store_prediction_result(self, result: PredictionResult):
        """予測結果保存"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            prediction_id = (
                f"pred_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{result.task_id}"
            )

            cursor.execute(
                """
                INSERT INTO prediction_results
                (prediction_id, task_id, predicted_pattern, predicted_completion_time,
                 predicted_resource_usage, predicted_success_rate, confidence, reasoning,
                 recommended_optimizations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    prediction_id,
                    result.task_id,
                    result.predicted_pattern.value,
                    result.predicted_completion_time,
                    json.dumps(result.predicted_resource_usage),
                    result.predicted_success_rate,
                    result.confidence,
                    result.reasoning,
                    json.dumps(result.recommended_optimizations),
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Prediction result storage failed: {e}")

    async def _save_models(self, accuracy_metrics: Dict[str, float]):
        """モデル保存"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # モデルデータをシリアライズ
            model_data = {
                "completion_time_model": self.completion_time_model,
                "success_prediction_model": self.success_prediction_model,
                "pattern_classifier": self.pattern_classifier,
                "scaler": self.scaler,
            }

            serialized_model = pickle.dumps(model_data)

            model_id = f"model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            cursor.execute(
                """
                INSERT INTO pattern_models
                (model_id, model_type, trained_at, accuracy, feature_importance,
                 model_data, training_samples)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    model_id,
                    "ensemble",
                    datetime.now().isoformat(),
                    accuracy_metrics.get("completion_time_accuracy", 0.0),
                    json.dumps(accuracy_metrics),
                    serialized_model,
                    len(self.training_data),
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Model saving failed: {e}")

    async def _analyze_failure_pattern(
        self, record: TaskExecutionRecord, failure_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """失敗パターン分析"""
        return {
            "failure_type": failure_details.get("error_type", "unknown"),
            "context": record.context,
            "complexity": record.complexity.value,
            "pattern": record.pattern.value,
            "lessons": failure_details.get("lessons", []),
        }

    async def _optimize_completion_time(
        self, prediction: PredictionResult
    ) -> Dict[str, Any]:
        """完了時間最適化"""
        return {
            "type": "completion_time_optimization",
            "current_time": prediction.predicted_completion_time,
            "target_reduction": 0.3,
            "strategies": ["parallel_processing", "task_splitting", "resource_scaling"],
        }

    async def _optimize_resource_usage(
        self, prediction: PredictionResult
    ) -> Dict[str, Any]:
        """リソース使用量最適化"""
        return {
            "type": "resource_optimization",
            "current_usage": prediction.predicted_resource_usage,
            "target_reduction": 0.2,
            "strategies": ["memory_optimization", "cpu_scheduling", "io_optimization"],
        }

    async def _optimize_success_rate(
        self, prediction: PredictionResult
    ) -> Dict[str, Any]:
        """成功率最適化"""
        return {
            "type": "success_rate_optimization",
            "current_rate": prediction.predicted_success_rate,
            "target_rate": 0.95,
            "strategies": [
                "error_handling",
                "dependency_validation",
                "testing_enhancement",
            ],
        }

    async def _apply_constraints(
        self, strategy: Dict[str, Any], constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """制約条件適用"""
        # 制約条件に基づいて最適化戦略を調整
        if "time_limit" in constraints:
            strategy["time_constraint"] = constraints["time_limit"]

        if "resource_limit" in constraints:
            strategy["resource_constraint"] = constraints["resource_limit"]

        return strategy

    async def _calculate_expected_improvement(
        self, prediction: PredictionResult, optimizations: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """期待改善効果計算"""
        improvements = {
            "time_reduction": 0.0,
            "resource_reduction": 0.0,
            "success_rate_improvement": 0.0,
        }

        for optimization in optimizations:
            if optimization["type"] == "completion_time_optimization":
                improvements["time_reduction"] += optimization.get(
                    "target_reduction", 0
                )
            elif optimization["type"] == "resource_optimization":
                improvements["resource_reduction"] += optimization.get(
                    "target_reduction", 0
                )
            elif optimization["type"] == "success_rate_optimization":
                improvements["success_rate_improvement"] += (
                    optimization.get("target_rate", 0)
                    - prediction.predicted_success_rate
                )

        return improvements

    async def _generate_implementation_steps(
        self, optimizations: List[Dict[str, Any]]
    ) -> List[str]:
        """実装手順生成"""
        steps = []

        for optimization in optimizations:
            if optimization["type"] == "completion_time_optimization":
                steps.extend(
                    [
                        "1. 並列処理可能な部分を特定",
                        "2. タスク分割を実行",
                        "3. リソーススケーリングを適用",
                    ]
                )
            elif optimization["type"] == "resource_optimization":
                steps.extend(
                    [
                        "1. メモリ使用量を最適化",
                        "2. CPU スケジューリングを調整",
                        "3. I/O 処理を最適化",
                    ]
                )
            elif optimization["type"] == "success_rate_optimization":
                steps.extend(
                    [
                        "1. エラーハンドリングを強化",
                        "2. 依存関係の事前検証",
                        "3. テストカバレッジを向上",
                    ]
                )

        return list(set(steps))  # 重複除去

    async def _evaluate_performance(self) -> Dict[str, float]:
        """パフォーマンス評価"""
        # 簡略化実装
        return {"accuracy": 0.8, "precision": 0.75, "recall": 0.85, "f1_score": 0.8}

    async def _retrain_with_enhanced_features(self):
        """強化特徴量での再学習"""
        # 特徴量エンジニアリング強化
        self.logger.info("🔄 Retraining with enhanced features")
        await self._train_models()


# 使用例
async def main():
    """メイン実行関数"""
    try:
        # システム初期化
        pattern_learning = PredictivePatternLearningSystem()

        # サンプル実行記録作成
        print("📝 Creating sample execution records...")

        sample_records = [
            TaskExecutionRecord(
                task_id="task_001",
                task_type="development",
                complexity=TaskComplexity.MEDIUM,
                pattern=ExecutionPattern.SEQUENTIAL,
                start_time=datetime.now() - timedelta(hours=2),
                end_time=datetime.now() - timedelta(hours=1),
                success=True,
                completion_time=3600,
                resource_usage={"cpu": 0.5, "memory": 0.3, "disk": 0.2, "network": 0.1},
                error_count=0,
                quality_score=0.9,
                context={"priority": 0.8, "deadline_pressure": 0.6},
                dependencies=["db_connection", "api_service"],
            ),
            TaskExecutionRecord(
                task_id="task_002",
                task_type="testing",
                complexity=TaskComplexity.SIMPLE,
                pattern=ExecutionPattern.PARALLEL,
                start_time=datetime.now() - timedelta(hours=1),
                end_time=datetime.now() - timedelta(minutes=30),
                success=True,
                completion_time=1800,
                resource_usage={
                    "cpu": 0.3,
                    "memory": 0.2,
                    "disk": 0.1,
                    "network": 0.05,
                },
                error_count=0,
                quality_score=0.95,
                context={"priority": 0.6, "deadline_pressure": 0.3},
                dependencies=["test_framework"],
            ),
            TaskExecutionRecord(
                task_id="task_003",
                task_type="deployment",
                complexity=TaskComplexity.COMPLEX,
                pattern=ExecutionPattern.CONDITIONAL,
                start_time=datetime.now() - timedelta(hours=4),
                end_time=datetime.now() - timedelta(hours=1),
                success=False,
                completion_time=10800,
                resource_usage={"cpu": 0.8, "memory": 0.7, "disk": 0.5, "network": 0.3},
                error_count=3,
                quality_score=0.6,
                context={"priority": 0.9, "deadline_pressure": 0.8},
                dependencies=["production_server", "database", "load_balancer"],
            ),
        ]

        # 実行記録保存
        for record in sample_records:
            await pattern_learning.record_execution(record)
            print(f"✅ Record saved: {record.task_id}")

        # 学習実行
        print("\n🧠 Training models...")
        await pattern_learning._train_models()

        # 予測実行
        print("\n🔮 Testing predictions...")

        prediction = await pattern_learning.predict_execution_pattern(
            task_type="optimization",
            complexity=TaskComplexity.MEDIUM,
            context={"priority": 0.7, "deadline_pressure": 0.5},
            dependencies=["performance_tools", "monitoring_system"],
        )

        print(f"📊 Prediction Result:")
        print(f"  Task ID: {prediction.task_id}")
        print(f"  Predicted Pattern: {prediction.predicted_pattern.value}")
        print(f"  Predicted Time: {prediction.predicted_completion_time:.1f}s")
        print(f"  Success Rate: {prediction.predicted_success_rate:.2f}")
        print(f"  Confidence: {prediction.confidence:.2f}")
        print(f"  Reasoning: {prediction.reasoning}")
        print(f"  Optimizations: {prediction.recommended_optimizations}")

        # 実行戦略最適化
        print("\n⚡ Testing execution strategy optimization...")

        optimization_strategy = await pattern_learning.optimize_execution_strategy(
            prediction
        )
        print(f"🎯 Optimization Strategy:")
        print(f"  Optimizations: {len(optimization_strategy['optimizations'])}")
        print(
            f"  Expected Improvement: {optimization_strategy['expected_improvement']}"
        )
        print(
            f"  Implementation Steps: {len(optimization_strategy['implementation_steps'])}"
        )

        # 失敗学習テスト
        print("\n📚 Testing failure learning...")

        failure_details = {
            "error_type": "dependency_failure",
            "error_message": "Database connection timeout",
            "lessons": ["Add connection retry logic", "Implement health checks"],
        }

        await pattern_learning.learn_from_failure("task_003", failure_details)
        print("✅ Failure learning completed")

        print("\n🎉 Predictive Pattern Learning System Phase 1 testing completed!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
