#!/usr/bin/env python3
"""
学習最適化エンジン
修復戦略の継続的な学習と最適化を行う
"""

import json
import logging
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available, machine learning features disabled")
import hashlib
import pickle

# プロジェクトルートをPythonパスに追加
import sys

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import BaseManager


@dataclass
class StrategyPerformance:
    """戦略パフォーマンスデータ"""

    strategy_id: str
    error_type: str
    success_count: int
    failure_count: int
    avg_execution_time: float
    avg_resource_usage: float
    context_features: Dict
    effectiveness_score: float
    last_updated: datetime


@dataclass
class OptimizationResult:
    """最適化結果"""

    original_strategy: Dict
    optimized_strategy: Dict
    improvement_score: float
    confidence: float
    rationale: str


class LearningOptimizer(BaseManager):
    """修復戦略を学習し最適化するエンジン"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)

        # データベース
        self.db_path = PROJECT_ROOT / "db" / "learning_optimizer.db"
        self.model_path = PROJECT_ROOT / "models"
        self.model_path.mkdir(parents=True, exist_ok=True)

        # 学習パラメータ
        self.min_samples_for_learning = 10
        self.learning_rate = 0.1
        self.exploration_rate = 0.2  # 探索と活用のバランス

        # モデル
        self.strategy_models = {}  # エラータイプ別の予測モデル
        self.feature_extractors = {}
        self.performance_cache = {}

        # 初期化
        self._init_database()
        self._load_models()

        # 統計
        self.optimization_stats = {
            "total_optimizations": 0,
            "successful_improvements": 0,
            "failed_attempts": 0,
            "avg_improvement": 0,
        }

    def _init_database(self):
        """学習データベースの初期化"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            # 戦略実行履歴
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS strategy_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT UNIQUE,
                    error_type TEXT,
                    error_context TEXT,  -- JSON
                    strategy_used TEXT,  -- JSON
                    execution_time REAL,
                    resource_usage REAL,
                    success BOOLEAN,
                    side_effects TEXT,
                    feedback_score REAL,
                    executed_at TIMESTAMP
                )
            """
            )

            # 学習済み戦略
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS learned_strategies (
                    strategy_id TEXT PRIMARY KEY,
                    error_type TEXT,
                    strategy_definition TEXT,  -- JSON
                    performance_metrics TEXT,  -- JSON
                    context_patterns TEXT,     -- JSON
                    effectiveness_score REAL,
                    sample_count INTEGER,
                    created_at TIMESTAMP,
                    last_updated TIMESTAMP
                )
            """
            )

            # A/Bテスト結果
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ab_test_results (
                    test_id TEXT PRIMARY KEY,
                    error_type TEXT,
                    strategy_a TEXT,  -- JSON
                    strategy_b TEXT,  -- JSON
                    executions_a INTEGER,
                    executions_b INTEGER,
                    success_rate_a REAL,
                    success_rate_b REAL,
                    avg_time_a REAL,
                    avg_time_b REAL,
                    winner TEXT,
                    confidence REAL,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """
            )

            # 最適化履歴
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS optimization_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    optimization_id TEXT,
                    error_type TEXT,
                    original_effectiveness REAL,
                    optimized_effectiveness REAL,
                    improvement REAL,
                    optimization_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

    def start_optimization(self):
        """最適化プロセスを開始"""
        self.logger.info("Starting learning optimization engine...")
        # 定期的な最適化は上位のオーケストレーターが管理
        pass

    def record_execution(
        self, error_type: str, strategy: Dict, execution_result: Dict, context: Dict
    ):
        """戦略実行を記録"""
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{error_type}"

        # 特徴量を抽出
        features = self._extract_context_features(context)

        # リソース使用量を推定
        resource_usage = self._estimate_resource_usage(execution_result)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO strategy_executions
                (execution_id, error_type, error_context, strategy_used,
                 execution_time, resource_usage, success, side_effects,
                 feedback_score, executed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    execution_id,
                    error_type,
                    json.dumps(features),
                    json.dumps(strategy),
                    execution_result.get("execution_time", 0),
                    resource_usage,
                    execution_result.get("success", False),
                    json.dumps(execution_result.get("side_effects", [])),
                    self._calculate_feedback_score(execution_result),
                    datetime.now(),
                ),
            )

        # 学習トリガー
        if self._should_trigger_learning(error_type):
            self._learn_from_executions(error_type)

    def get_optimized_strategy(
        self, error_type: str, context: Optional[Dict] = None
    ) -> Optional[Dict]:
        """最適化された戦略を取得"""
        # キャッシュチェック
        cache_key = f"{error_type}_{self._hash_context(context)}"
        if cache_key in self.performance_cache:
            return self.performance_cache[cache_key]

        # 学習済み戦略を取得
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT strategy_definition, context_patterns, effectiveness_score
                FROM learned_strategies
                WHERE error_type = ?
                ORDER BY effectiveness_score DESC
                LIMIT 5
            """,
                (error_type,),
            )

            candidates = []
            for row in cursor:
                strategy = json.loads(row[0])
                patterns = json.loads(row[1])
                score = row[2]

                # コンテキストマッチング
                if context:
                    match_score = self._calculate_context_match(context, patterns)
                    adjusted_score = score * match_score
                else:
                    adjusted_score = score

                candidates.append((strategy, adjusted_score))

            if candidates:
                # 最高スコアの戦略を選択（探索も考慮）
                if np.random.random() < self.exploration_rate:
                    # 探索: ランダムに選択
                    strategy, _ = candidates[np.random.randint(len(candidates))]
                else:
                    # 活用: 最高スコアを選択
                    strategy, _ = max(candidates, key=lambda x: x[1])

                # キャッシュに保存
                self.performance_cache[cache_key] = strategy
                return strategy

        return None

    def optimize_all_strategies(self) -> Dict:
        """全ての戦略を最適化"""
        self.optimization_stats["total_optimizations"] += 1

        optimization_results = {
            "optimized_strategies": [],
            "improvements": 0,
            "failures": 0,
        }

        # エラータイプ別に最適化
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT DISTINCT error_type FROM strategy_executions")
            error_types = [row[0] for row in cursor]

        for error_type in error_types:
            try:
                result = self._optimize_strategy_for_error_type(error_type)
                if result and result.improvement_score > 0:
                    optimization_results["optimized_strategies"].append(result)
                    optimization_results["improvements"] += 1
                    self.optimization_stats["successful_improvements"] += 1
                else:
                    optimization_results["failures"] += 1
                    self.optimization_stats["failed_attempts"] += 1
            except Exception as e:
                self.logger.error(f"Failed to optimize {error_type}: {e}")
                optimization_results["failures"] += 1

        # 統計更新
        if optimization_results["improvements"] > 0:
            self._update_optimization_stats(optimization_results)

        return optimization_results

    def _optimize_strategy_for_error_type(
        self, error_type: str
    ) -> Optional[OptimizationResult]:
        """特定エラータイプの戦略を最適化"""
        # 実行履歴を取得
        executions = self._get_recent_executions(error_type, limit=100)

        if len(executions) < self.min_samples_for_learning:
            return None

        # 現在の最良戦略を取得
        current_best = self._get_current_best_strategy(error_type)
        if not current_best:
            return None

        # 最適化手法を選択
        optimization_method = self._select_optimization_method(executions)

        # 最適化実行
        if optimization_method == "parameter_tuning":
            optimized = self._optimize_parameters(current_best, executions)
        elif optimization_method == "strategy_combination":
            optimized = self._combine_strategies(error_type, executions)
        elif optimization_method == "context_adaptation":
            optimized = self._adapt_to_context(current_best, executions)
        else:
            optimized = self._evolutionary_optimization(current_best, executions)

        if optimized:
            # 改善度を計算
            improvement = self._calculate_improvement(
                current_best, optimized, executions
            )

            if improvement > 0.05:  # 5%以上の改善
                # 最適化結果を保存
                self._save_optimized_strategy(error_type, optimized, improvement)

                return OptimizationResult(
                    original_strategy=current_best,
                    optimized_strategy=optimized,
                    improvement_score=improvement,
                    confidence=0.8,  # 仮の値
                    rationale=f"Optimized using {optimization_method}",
                )

        return None

    def _learn_from_executions(self, error_type: str):
        """実行履歴から学習"""
        if not SKLEARN_AVAILABLE:
            self.logger.warning("scikit-learn not available, skipping machine learning")
            return

        executions = self._get_recent_executions(error_type, limit=200)

        if len(executions) < self.min_samples_for_learning:
            return

        # 特徴量とラベルを準備
        X, y = self._prepare_training_data(executions)

        if len(X) < 10:
            return

        # モデル学習
        model = RandomForestClassifier(n_estimators=50, random_state=42)
        scaler = StandardScaler()

        X_scaled = scaler.fit_transform(X)
        model.fit(X_scaled, y)

        # モデルを保存
        model_key = f"strategy_model_{error_type}"
        self.strategy_models[model_key] = model
        self.feature_extractors[model_key] = scaler

        # モデルをディスクに保存
        model_file = self.model_path / f"{model_key}.pkl"
        with open(model_file, "wb") as f:
            pickle.dump(
                {
                    "model": model,
                    "scaler": scaler,
                    "feature_names": self._get_feature_names(),
                },
                f,
            )

        self.logger.info(
            f"Learned model for {error_type} from {len(executions)} executions"
        )

    def _prepare_training_data(
        self, executions: List[Dict]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """学習データを準備"""
        X = []
        y = []

        for exec_data in executions:
            # 特徴量
            features = []
            context = json.loads(exec_data["error_context"])

            # 数値特徴
            features.extend(
                [
                    context.get("hour_of_day", 12),
                    context.get("day_of_week", 3),
                    context.get("system_load", 0.5),
                    context.get("memory_usage", 50),
                    context.get("error_frequency", 1),
                    exec_data["execution_time"],
                    exec_data["resource_usage"],
                ]
            )

            # カテゴリカル特徴（ワンホットエンコーディング）
            strategy = json.loads(exec_data["strategy_used"])
            strategy_type = strategy.get("type", "unknown")
            features.extend(
                [
                    1 if strategy_type == "reactive" else 0,
                    1 if strategy_type == "preventive" else 0,
                    1 if strategy_type == "adaptive" else 0,
                ]
            )

            X.append(features)
            y.append(1 if exec_data["success"] else 0)

        return np.array(X), np.array(y)

    def _get_feature_names(self) -> List[str]:
        """特徴量名を取得"""
        return [
            "hour_of_day",
            "day_of_week",
            "system_load",
            "memory_usage",
            "error_frequency",
            "execution_time",
            "resource_usage",
            "is_reactive",
            "is_preventive",
            "is_adaptive",
        ]

    def _optimize_parameters(self, strategy: Dict, executions: List[Dict]) -> Dict:
        """パラメータチューニング"""
        optimized = strategy.copy()

        # パラメータ範囲を定義
        param_ranges = {
            "timeout": (5, 60),
            "retry_count": (1, 5),
            "backoff_factor": (1.0, 3.0),
        }

        # グリッドサーチ的な最適化
        best_score = self._evaluate_strategy(strategy, executions)

        for param, (min_val, max_val) in param_ranges.items():
            if param in strategy:
                # 複数の値を試す
                for value in np.linspace(min_val, max_val, 5):
                    test_strategy = optimized.copy()
                    test_strategy[param] = value

                    score = self._evaluate_strategy(test_strategy, executions)
                    if score > best_score:
                        best_score = score
                        optimized[param] = value

        return optimized

    def _combine_strategies(self, error_type: str, executions: List[Dict]) -> Dict:
        """複数戦略の組み合わせ"""
        # 上位戦略を取得
        top_strategies = self._get_top_strategies(error_type, limit=3)

        if len(top_strategies) < 2:
            return None

        # 戦略を組み合わせ
        combined = {"type": "combined", "strategies": []}

        for strategy in top_strategies:
            # 各戦略の良い部分を抽出
            if self._evaluate_strategy(strategy, executions) > 0.7:
                combined["strategies"].append(
                    {
                        "condition": self._extract_success_condition(
                            strategy, executions
                        ),
                        "action": strategy,
                    }
                )

        return combined if combined["strategies"] else None

    def _adapt_to_context(self, strategy: Dict, executions: List[Dict]) -> Dict:
        """コンテキストに適応"""
        # コンテキストパターンを分析
        context_patterns = self._analyze_context_patterns(executions)

        # 適応的戦略を作成
        adaptive_strategy = {
            "type": "context_adaptive",
            "base_strategy": strategy,
            "adaptations": [],
        }

        for pattern in context_patterns:
            if pattern["success_rate"] > 0.8:
                adaptive_strategy["adaptations"].append(
                    {
                        "context_condition": pattern["condition"],
                        "modification": pattern["optimal_modification"],
                    }
                )

        return adaptive_strategy if adaptive_strategy["adaptations"] else strategy

    def _evolutionary_optimization(
        self, strategy: Dict, executions: List[Dict]
    ) -> Dict:
        """進化的最適化"""
        population_size = 20
        generations = 10
        mutation_rate = 0.1

        # 初期集団を生成
        population = [self._mutate_strategy(strategy) for _ in range(population_size)]

        for generation in range(generations):
            # 適応度を評価
            fitness_scores = [
                (s, self._evaluate_strategy(s, executions)) for s in population
            ]

            # 上位を選択
            fitness_scores.sort(key=lambda x: x[1], reverse=True)
            survivors = [s for s, _ in fitness_scores[: population_size // 2]]

            # 新世代を生成
            new_population = survivors.copy()

            while len(new_population) < population_size:
                # 交叉
                if len(survivors) >= 2:
                    parent1, parent2 = np.random.choice(survivors, 2, replace=False)
                    child = self._crossover_strategies(parent1, parent2)
                else:
                    child = survivors[0].copy()

                # 突然変異
                if np.random.random() < mutation_rate:
                    child = self._mutate_strategy(child)

                new_population.append(child)

            population = new_population

        # 最良個体を返す
        best_strategy = max(
            population, key=lambda s: self._evaluate_strategy(s, executions)
        )
        return best_strategy

    def _mutate_strategy(self, strategy: Dict) -> Dict:
        """戦略を変異させる"""
        mutated = strategy.copy()

        # ランダムにパラメータを変更
        if "timeout" in mutated and np.random.random() < 0.3:
            mutated["timeout"] = max(5, mutated["timeout"] + np.random.randint(-10, 11))

        if "retry_count" in mutated and np.random.random() < 0.3:
            mutated["retry_count"] = max(
                1, mutated["retry_count"] + np.random.randint(-1, 2)
            )

        return mutated

    def _crossover_strategies(self, strategy1: Dict, strategy2: Dict) -> Dict:
        """戦略を交叉"""
        child = {}

        # 各パラメータをランダムに選択
        all_keys = set(strategy1.keys()) | set(strategy2.keys())

        for key in all_keys:
            if key in strategy1 and key in strategy2:
                # 両方にある場合はランダムに選択
                child[key] = (
                    strategy1[key] if np.random.random() < 0.5 else strategy2[key]
                )
            elif key in strategy1:
                child[key] = strategy1[key]
            else:
                child[key] = strategy2[key]

        return child

    def _evaluate_strategy(self, strategy: Dict, executions: List[Dict]) -> float:
        """戦略を評価"""
        # シミュレーション的な評価
        success_count = 0
        total_time = 0

        for exec_data in executions[-50:]:  # 直近50件で評価
            # 戦略が成功したかを推定
            if self._would_strategy_succeed(strategy, exec_data):
                success_count += 1
                total_time += exec_data["execution_time"] * 0.9  # 改善を仮定
            else:
                total_time += exec_data["execution_time"] * 1.1

        if len(executions) > 0:
            success_rate = success_count / min(50, len(executions))
            avg_time = total_time / min(50, len(executions))

            # スコア計算（成功率重視）
            score = success_rate * 0.7 + (1 - min(avg_time / 60, 1)) * 0.3
            return score

        return 0.5

    def _would_strategy_succeed(self, strategy: Dict, execution: Dict) -> bool:
        """戦略が成功するか推定"""
        # 簡易的な推定ロジック
        base_success = execution["success"]

        # タイムアウトが十分か
        if strategy.get("timeout", 30) < execution["execution_time"]:
            return False

        # リトライが有効か
        if not base_success and strategy.get("retry_count", 1) > 1:
            # リトライで成功する可能性を考慮
            return np.random.random() < 0.6

        return base_success

    def _extract_context_features(self, context: Dict) -> Dict:
        """コンテキストから特徴量を抽出"""
        now = datetime.now()

        features = {
            "hour_of_day": now.hour,
            "day_of_week": now.weekday(),
            "system_load": context.get("cpu_usage", 50) / 100,
            "memory_usage": context.get("memory_usage", 50),
            "error_frequency": context.get("error_count", 1),
            "worker_type": context.get("worker_type", "unknown"),
        }

        return features

    def _estimate_resource_usage(self, execution_result: Dict) -> float:
        """リソース使用量を推定"""
        # 簡易的な推定
        base_usage = 0.1  # 基本使用量

        # 実行時間に基づく
        time_factor = min(execution_result.get("execution_time", 0) / 60, 1)

        # メモリ使用量（仮定）
        memory_factor = 0.5

        return base_usage + time_factor * 0.5 + memory_factor * 0.3

    def _calculate_feedback_score(self, execution_result: Dict) -> float:
        """フィードバックスコアを計算"""
        score = 0.0

        # 成功/失敗
        if execution_result.get("success"):
            score += 1.0

        # 実行時間
        exec_time = execution_result.get("execution_time", 60)
        if exec_time < 10:
            score += 0.5
        elif exec_time < 30:
            score += 0.3

        # 副作用
        if not execution_result.get("side_effects"):
            score += 0.2

        return min(score, 1.0)

    def _should_trigger_learning(self, error_type: str) -> bool:
        """学習をトリガーすべきか判断"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM strategy_executions
                WHERE error_type = ?
                AND executed_at > datetime('now', '-1 hour')
            """,
                (error_type,),
            )

            recent_count = cursor.fetchone()[0]

            # 1時間で10件以上なら学習
            return recent_count >= 10

    def _hash_context(self, context: Optional[Dict]) -> str:
        """コンテキストのハッシュを計算"""
        if not context:
            return "default"

        # 重要な特徴のみを使用
        key_features = {
            "worker_type": context.get("worker_type", "unknown"),
            "error_frequency": context.get("error_count", 0) // 10,  # 10単位で丸める
        }

        return hashlib.md5(
            json.dumps(key_features, sort_keys=True).encode()
        ).hexdigest()[:8]

    def _calculate_context_match(self, context: Dict, patterns: Dict) -> float:
        """コンテキストマッチ度を計算"""
        if not patterns:
            return 1.0

        match_score = 0.0
        weights = 0.0

        # 各パターンとの類似度を計算
        for key, pattern_value in patterns.items():
            if key in context:
                weight = pattern_value.get("importance", 1.0)
                weights += weight

                # 値の類似度
                if isinstance(context[key], (int, float)) and isinstance(
                    pattern_value.get("value"), (int, float)
                ):
                    diff = abs(context[key] - pattern_value["value"])
                    similarity = 1.0 / (1.0 + diff)
                else:
                    similarity = (
                        1.0 if context[key] == pattern_value.get("value") else 0.0
                    )

                match_score += similarity * weight

        return match_score / weights if weights > 0 else 0.5

    def _get_recent_executions(self, error_type: str, limit: int = 100) -> List[Dict]:
        """最近の実行履歴を取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM strategy_executions
                WHERE error_type = ?
                ORDER BY executed_at DESC
                LIMIT ?
            """,
                (error_type, limit),
            )

            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor]

    def _get_current_best_strategy(self, error_type: str) -> Optional[Dict]:
        """現在の最良戦略を取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT strategy_definition FROM learned_strategies
                WHERE error_type = ?
                ORDER BY effectiveness_score DESC
                LIMIT 1
            """,
                (error_type,),
            )

            row = cursor.fetchone()
            if row:
                return json.loads(row[0])

        return None

    def _select_optimization_method(self, executions: List[Dict]) -> str:
        """最適化手法を選択"""
        # 実行数に基づいて選択
        if len(executions) < 50:
            return "parameter_tuning"
        elif len(executions) < 100:
            return "strategy_combination"
        elif len(executions) < 200:
            return "context_adaptation"
        else:
            return "evolutionary"

    def _calculate_improvement(
        self, original: Dict, optimized: Dict, executions: List[Dict]
    ) -> float:
        """改善度を計算"""
        original_score = self._evaluate_strategy(original, executions)
        optimized_score = self._evaluate_strategy(optimized, executions)

        if original_score > 0:
            return (optimized_score - original_score) / original_score
        else:
            return optimized_score

    def _save_optimized_strategy(
        self, error_type: str, strategy: Dict, improvement: float
    ):
        """最適化された戦略を保存"""
        strategy_id = f"opt_{error_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        with sqlite3.connect(self.db_path) as conn:
            # 既存の戦略を更新または新規作成
            conn.execute(
                """
                INSERT OR REPLACE INTO learned_strategies
                (strategy_id, error_type, strategy_definition, effectiveness_score,
                 sample_count, created_at, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    strategy_id,
                    error_type,
                    json.dumps(strategy),
                    0.7 + improvement,  # ベーススコア + 改善度
                    100,  # 仮の値
                    datetime.now(),
                    datetime.now(),
                ),
            )

            # 最適化履歴を記録
            conn.execute(
                """
                INSERT INTO optimization_history
                (optimization_id, error_type, original_effectiveness,
                 optimized_effectiveness, improvement, optimization_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    strategy_id,
                    error_type,
                    0.7,
                    0.7 + improvement,
                    improvement,
                    "auto_optimization",
                ),
            )

    def _load_models(self):
        """保存されたモデルを読み込む"""
        for model_file in self.model_path.glob("strategy_model_*.pkl"):
            try:
                with open(model_file, "rb") as f:
                    model_data = pickle.load(f)
                    model_key = model_file.stem
                    self.strategy_models[model_key] = model_data["model"]
                    self.feature_extractors[model_key] = model_data["scaler"]
                    self.logger.info(f"Loaded model: {model_key}")
            except Exception as e:
                self.logger.error(f"Failed to load model {model_file}: {e}")

    def provide_feedback(self, incident_id: str, result: Dict):
        """修復結果のフィードバックを提供"""
        # フィードバックを記録
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO healing_feedback
                (incident_id, feedback_type, feedback_data, impact_score)
                VALUES (?, ?, ?, ?)
            """,
                (
                    incident_id,
                    "success" if result.get("success") else "failure",
                    json.dumps(result),
                    self._calculate_impact_score(result),
                ),
            )

    def _calculate_impact_score(self, result: Dict) -> float:
        """影響スコアを計算"""
        base_score = 1.0 if result.get("success") else -0.5

        # 実行時間による調整
        time_factor = min(result.get("duration", 60) / 60, 1)

        # 手動介入が必要だった場合はペナルティ
        if result.get("manual_required"):
            base_score -= 0.3

        return base_score * (1 - time_factor * 0.3)

    def record_success(self, error_type: str, strategy: Dict):
        """成功を記録"""
        # 簡易的な成功記録
        self.logger.info(f"Strategy success recorded for {error_type}")

    def get_statistics(self) -> Dict:
        """統計情報を取得"""
        with sqlite3.connect(self.db_path) as conn:
            # 基本統計
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total_executions,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
                    AVG(execution_time) as avg_time,
                    COUNT(DISTINCT error_type) as error_types
                FROM strategy_executions
                WHERE executed_at > datetime('now', '-7 days')
            """
            )

            row = cursor.fetchone()
            basic_stats = {
                "total_executions": row[0] or 0,
                "successful_executions": row[1] or 0,
                "avg_execution_time": row[2] or 0,
                "distinct_error_types": row[3] or 0,
            }

            # 最適化統計
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total_optimizations,
                    AVG(improvement) as avg_improvement
                FROM optimization_history
                WHERE created_at > datetime('now', '-7 days')
            """
            )

            row = cursor.fetchone()
            optimization_stats = {
                "recent_optimizations": row[0] or 0,
                "avg_improvement": row[1] or 0,
            }

        return {
            "execution_stats": basic_stats,
            "optimization_stats": dict(self.optimization_stats, **optimization_stats),
            "loaded_models": len(self.strategy_models),
            "cached_strategies": len(self.performance_cache),
        }

    def _get_top_strategies(self, error_type: str, limit: int = 5) -> List[Dict]:
        """上位戦略を取得"""
        strategies = []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT strategy_definition FROM learned_strategies
                WHERE error_type = ?
                ORDER BY effectiveness_score DESC
                LIMIT ?
            """,
                (error_type, limit),
            )

            for row in cursor:
                strategies.append(json.loads(row[0]))

        return strategies

    def _extract_success_condition(
        self, strategy: Dict, executions: List[Dict]
    ) -> Dict:
        """成功条件を抽出"""
        # 成功した実行のコンテキストを分析
        successful_contexts = []

        for exec_data in executions:
            if exec_data["success"]:
                context = json.loads(exec_data["error_context"])
                successful_contexts.append(context)

        if not successful_contexts:
            return {}

        # 共通パターンを見つける
        common_conditions = {}

        # 時間帯
        hours = [c.get("hour_of_day", 12) for c in successful_contexts]
        if hours:
            avg_hour = np.mean(hours)
            common_conditions["hour_range"] = (int(avg_hour - 2), int(avg_hour + 2))

        # システム負荷
        loads = [c.get("system_load", 0.5) for c in successful_contexts]
        if loads:
            common_conditions["max_load"] = np.percentile(loads, 80)

        return common_conditions

    def _analyze_context_patterns(self, executions: List[Dict]) -> List[Dict]:
        """コンテキストパターンを分析"""
        patterns = []

        # コンテキストをグループ化
        context_groups = defaultdict(list)

        for exec_data in executions:
            context = json.loads(exec_data["error_context"])
            # 簡易的なグループ化キー
            group_key = f"{context.get(
                'worker_type',
                'unknown')}_{context.get('hour_of_day',
                0
            ) // 6}"
            context_groups[group_key].append(
                {
                    "context": context,
                    "success": exec_data["success"],
                    "execution_time": exec_data["execution_time"],
                }
            )

        # 各グループのパターンを分析
        for group_key, group_data in context_groups.items():
            if len(group_data) >= 5:
                success_rate = sum(d["success"] for d in group_data) / len(group_data)
                avg_time = np.mean([d["execution_time"] for d in group_data])

                if success_rate > 0.7:
                    patterns.append(
                        {
                            "condition": group_key,
                            "success_rate": success_rate,
                            "avg_execution_time": avg_time,
                            "optimal_modification": {
                                "timeout": int(avg_time * 1.5),
                                "retry_count": 2 if success_rate < 0.9 else 1,
                            },
                        }
                    )

        return patterns

    def _update_optimization_stats(self, results: Dict):
        """最適化統計を更新"""
        if results["improvements"] > 0:
            total_optimizations = self.optimization_stats["total_optimizations"]
            current_avg = self.optimization_stats["avg_improvement"]

            # 新しい平均を計算
            new_improvements = results["improvements"]
            new_avg_improvement = (
                sum(r.improvement_score for r in results["optimized_strategies"])
                / new_improvements
                if new_improvements > 0
                else 0
            )

            # 全体平均を更新
            self.optimization_stats["avg_improvement"] = (
                (
                    (current_avg * (total_optimizations - 1) + new_avg_improvement)
                    / total_optimizations
                )
                if total_optimizations > 0
                else new_avg_improvement
            )


if __name__ == "__main__":
    # テスト実行
    optimizer = LearningOptimizer()

    print("=== Learning Optimizer Test ===")

    # テスト実行を記録
    test_executions = [
        {
            "error_type": "ImportError",
            "strategy": {"type": "reactive", "timeout": 30, "retry_count": 2},
            "execution_result": {
                "success": True,
                "execution_time": 15.5,
                "side_effects": [],
            },
            "context": {"worker_type": "task", "memory_usage": 45},
        },
        {
            "error_type": "ImportError",
            "strategy": {"type": "reactive", "timeout": 20, "retry_count": 1},
            "execution_result": {
                "success": False,
                "execution_time": 20.1,
                "side_effects": ["timeout"],
            },
            "context": {"worker_type": "task", "memory_usage": 80},
        },
    ]

    for exec_data in test_executions:
        optimizer.record_execution(
            exec_data["error_type"],
            exec_data["strategy"],
            exec_data["execution_result"],
            exec_data["context"],
        )

    # 最適化実行
    print("\nOptimizing strategies...")
    results = optimizer.optimize_all_strategies()
    print(f"Optimization results: {json.dumps(results, indent=2)}")

    # 統計表示
    stats = optimizer.get_statistics()
    print(f"\nStatistics: {json.dumps(stats, indent=2)}")
