#!/usr/bin/env python3
"""
Autonomous Learning System
エルダーズギルド 自律学習システム

Created by Claude Elder
Version: 1.0.0
"""

import asyncio
import logging
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import pickle
import os
from pathlib import Path
import hashlib
import copy

logger = logging.getLogger(__name__)

class LearningType(Enum):
    """学習タイプ"""
    SUPERVISED = "supervised"
    UNSUPERVISED = "unsupervised"
    REINFORCEMENT = "reinforcement"
    META_LEARNING = "meta_learning"
    TRANSFER = "transfer"
    SELF_SUPERVISED = "self_supervised"

class KnowledgeType(Enum):
    """知識タイプ"""
    PATTERN = "pattern"
    RULE = "rule"
    EXPERIENCE = "experience"
    STRATEGY = "strategy"
    MODEL = "model"
    HEURISTIC = "heuristic"

class PerformanceMetric(Enum):
    """パフォーマンス指標"""
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    EFFICIENCY = "efficiency"
    ADAPTABILITY = "adaptability"
    ROBUSTNESS = "robustness"

@dataclass
class LearningTask:
    """学習タスク"""
    task_id: str
    name: str
    learning_type: LearningType
    input_data: Any
    target_output: Optional[Any] = None
    context: Dict[str, Any] = field(default_factory=dict)
    priority: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    success: bool = False

@dataclass
class KnowledgeItem:
    """知識アイテム"""
    knowledge_id: str
    knowledge_type: KnowledgeType
    content: Any
    confidence: float
    source_task: str
    applicable_contexts: List[str]
    usage_count: int = 0
    success_rate: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "knowledge_id": self.knowledge_id,
            "knowledge_type": self.knowledge_type.value,
            "content": str(self.content),
            "confidence": self.confidence,
            "source_task": self.source_task,
            "applicable_contexts": self.applicable_contexts,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None
        }

@dataclass
class LearningExperience:
    """学習経験"""
    experience_id: str
    task_id: str
    approach_used: str
    input_features: Dict[str, Any]
    output_result: Any
    performance_score: float
    context: Dict[str, Any]
    lessons_learned: List[str]
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class AdaptationStrategy:
    """適応戦略"""
    strategy_id: str
    name: str
    trigger_conditions: Dict[str, Any]
    adaptation_actions: List[str]
    effectiveness_score: float = 0.5
    usage_count: int = 0

class MetaLearner:
    """メタ学習エンジン"""

    def __init__(self):
        self.learning_history: List[LearningExperience] = []
        self.adaptation_strategies: Dict[str, AdaptationStrategy] = {}
        self.performance_trends: Dict[str, List[float]] = {}

    def analyze_learning_patterns(self) -> Dict[str, Any]:
        """学習パターン分析"""
        if not self.learning_history:
            return {"status": "no_data"}

        # 成功率分析
        success_rates = {}
        approach_counts = {}

        for exp in self.learning_history:
            approach = exp.approach_used
            if approach not in success_rates:
                success_rates[approach] = []
                approach_counts[approach] = 0

            success_rates[approach].append(exp.performance_score)
            approach_counts[approach] += 1

        # 平均成功率計算
        avg_success_rates = {
            approach: np.mean(scores)
            for approach, scores in success_rates.items()
        }

        # 最適アプローチ決定
        best_approach = max(avg_success_rates, key=avg_success_rates.get)

        # 学習改善提案
        improvements = self._generate_learning_improvements(success_rates)

        return {
            "status": "analyzed",
            "total_experiences": len(self.learning_history),
            "approaches_used": len(success_rates),
            "success_rates": avg_success_rates,
            "approach_counts": approach_counts,
            "best_approach": best_approach,
            "best_score": avg_success_rates[best_approach],
            "improvements": improvements,
            "analysis_time": datetime.now().isoformat()
        }

    def _generate_learning_improvements(self, success_rates: Dict[str, List[float]]) -> List[str]:
        """学習改善提案生成"""
        improvements = []

        for approach, scores in success_rates.items():
            if len(scores) > 1:
                trend = np.polyfit(range(len(scores)), scores, 1)[0]

                if trend < -0.1:
                    improvements.append(f"Approach '{approach}' showing declining performance - consider alternative")
                elif trend > 0.1:
                    improvements.append(f"Approach '{approach}' improving - increase usage")

                volatility = np.std(scores)
                if volatility > 0.3:
                    improvements.append(f"Approach '{approach}' has high volatility - investigate causes")

        return improvements

    def recommend_approach(self, task_context: Dict[str, Any]) -> Tuple[str, float]:
        """アプローチ推奨"""
        if not self.learning_history:
            return "default", 0.5

        # コンテキスト類似度に基づく推奨
        context_similarities = []

        for exp in self.learning_history:
            similarity = self._calculate_context_similarity(task_context, exp.context)
            context_similarities.append((exp.approach_used, exp.performance_score, similarity))

        # 類似度と性能スコアで重み付け
        weighted_scores = {}
        for approach, score, similarity in context_similarities:
            if approach not in weighted_scores:
                weighted_scores[approach] = []
            weighted_scores[approach].append(score * (0.7 + 0.3 * similarity))

        # 最高スコアアプローチを推奨
        best_approach = max(weighted_scores, key=lambda k: np.mean(weighted_scores[k]))
        confidence = np.mean(weighted_scores[best_approach])

        return best_approach, confidence

    def _calculate_context_similarity(self, context1: Dict[str, Any],
                                    context2: Dict[str, Any]) -> float:
        """コンテキスト類似度計算"""
        common_keys = set(context1.keys()) & set(context2.keys())
        if not common_keys:
            return 0.0

        similarities = []
        for key in common_keys:
            val1, val2 = context1[key], context2[key]

            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                # 数値の場合
                max_val = max(abs(val1), abs(val2), 1e-10)
                similarity = 1.0 - abs(val1 - val2) / max_val
            elif val1 == val2:
                similarity = 1.0
            else:
                similarity = 0.0

            similarities.append(similarity)

        return np.mean(similarities)

class KnowledgeBase:
    """知識ベース"""

    def __init__(self, max_size: int = 10000):
        self.knowledge_items: Dict[str, KnowledgeItem] = {}
        self.max_size = max_size
        self.access_log: List[Tuple[str, datetime]] = []

    def add_knowledge(self, item: KnowledgeItem):
        """知識追加"""
        # 容量制限チェック
        if len(self.knowledge_items) >= self.max_size:
            self._evict_old_knowledge()

        self.knowledge_items[item.knowledge_id] = item
        logger.info(f"Added knowledge: {item.knowledge_id} ({item.knowledge_type.value})")

    def retrieve_knowledge(self, context: Dict[str, Any],
                         knowledge_type: Optional[KnowledgeType] = None) -> List[KnowledgeItem]:
        """知識検索"""
        relevant_items = []

        for item in self.knowledge_items.values():
            # タイプフィルタ
            if knowledge_type and item.knowledge_type != knowledge_type:
                continue

            # コンテキスト適用性チェック
            if self._is_applicable_context(item, context):
                relevant_items.append(item)
                # 使用統計更新
                item.usage_count += 1
                item.last_used = datetime.now()

        # 信頼度と適用性でソート
        relevant_items.sort(key=lambda x: (x.confidence, x.success_rate), reverse=True)

        return relevant_items

    def _is_applicable_context(self, item: KnowledgeItem, context: Dict[str, Any]) -> bool:
        """コンテキスト適用性判定"""
        if not item.applicable_contexts:
            return True  # 汎用知識

        # コンテキストキーワードマッチング
        context_str = json.dumps(context, default=str).lower()

        for applicable_context in item.applicable_contexts:
            if applicable_context.lower() in context_str:
                return True

        return False

    def update_knowledge_performance(self, knowledge_id: str, success: bool):
        """知識性能更新"""
        if knowledge_id in self.knowledge_items:
            item = self.knowledge_items[knowledge_id]

            # 成功率更新（指数移動平均）
            alpha = 0.1
            if success:
                item.success_rate = item.success_rate * (1 - alpha) + alpha
            else:
                item.success_rate = item.success_rate * (1 - alpha)

    def _evict_old_knowledge(self):
        """古い知識の削除"""
        # 使用頻度と成功率の低い知識を削除
        items_by_score = sorted(
            self.knowledge_items.values(),
            key=lambda x: x.usage_count * x.success_rate
        )

        # 下位10%を削除
        to_remove = int(len(items_by_score) * 0.1)
        for item in items_by_score[:to_remove]:
            del self.knowledge_items[item.knowledge_id]
            logger.info(f"Evicted knowledge: {item.knowledge_id}")

    def get_knowledge_statistics(self) -> Dict[str, Any]:
        """知識統計取得"""
        if not self.knowledge_items:
            return {"total_items": 0}

        by_type = {}
        confidences = []
        success_rates = []
        usage_counts = []

        for item in self.knowledge_items.values():
            # タイプ別統計
            type_name = item.knowledge_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

            # 性能統計
            confidences.append(item.confidence)
            success_rates.append(item.success_rate)
            usage_counts.append(item.usage_count)

        return {
            "total_items": len(self.knowledge_items),
            "by_type": by_type,
            "avg_confidence": np.mean(confidences),
            "avg_success_rate": np.mean(success_rates),
            "avg_usage": np.mean(usage_counts),
            "max_usage": max(usage_counts),
            "capacity_used": f"{len(self.knowledge_items)}/{self.max_size}"
        }

class SelfImprovementEngine:
    """自己改善エンジン"""

    def __init__(self):
        self.improvement_history: List[Dict[str, Any]] = []
        self.current_performance: Dict[str, float] = {}
        self.baseline_performance: Dict[str, float] = {}

    def evaluate_current_performance(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """現在の性能評価"""
        self.current_performance = metrics.copy()

        if not self.baseline_performance:
            self.baseline_performance = metrics.copy()
            return {"status": "baseline_set", "metrics": metrics}

        # 改善度計算
        improvements = {}
        degradations = {}

        for metric, current_value in metrics.items():
            if metric in self.baseline_performance:
                baseline_value = self.baseline_performance[metric]
                change = current_value - baseline_value
                change_percent = (change / baseline_value * 100) if baseline_value != 0 else 0

                if change > 0:
                    improvements[metric] = change_percent
                elif change < 0:
                    degradations[metric] = abs(change_percent)

        # 総合評価
        overall_improvement = self._calculate_overall_improvement(improvements, degradations)

        evaluation = {
            "status": "evaluated",
            "current_metrics": metrics,
            "baseline_metrics": self.baseline_performance,
            "improvements": improvements,
            "degradations": degradations,
            "overall_improvement": overall_improvement,
            "evaluation_time": datetime.now().isoformat()
        }

        return evaluation

    def _calculate_overall_improvement(self, improvements: Dict[str, float],
                                     degradations: Dict[str, float]) -> float:
        """総合改善度計算"""
        total_improvement = sum(improvements.values())
        total_degradation = sum(degradations.values())

        # 重み付け（劣化にペナルティ）
        net_improvement = total_improvement - (total_degradation * 1.5)

        return net_improvement

    def generate_improvement_plan(self, performance_evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """改善計画生成"""
        plan = {
            "plan_id": f"improvement_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "created_at": datetime.now().isoformat(),
            "actions": [],
            "expected_impact": 0.0
        }

        # 劣化メトリクスへの対応
        degradations = performance_evaluation.get("degradations", {})
        for metric, degradation in degradations.items():
            if degradation > 5:  # 5%以上の劣化
                plan["actions"].append({
                    "action_type": "fix_degradation",
                    "target_metric": metric,
                    "degradation_percent": degradation,
                    "priority": "high" if degradation > 20 else "medium",
                    "suggested_approach": self._suggest_fix_approach(metric)
                })

        # 改善機会の特定
        improvements = performance_evaluation.get("improvements", {})
        for metric, improvement in improvements.items():
            if improvement < 10:  # 改善余地あり
                plan["actions"].append({
                    "action_type": "enhance_performance",
                    "target_metric": metric,
                    "current_improvement": improvement,
                    "priority": "medium",
                    "suggested_approach": self._suggest_enhancement_approach(metric)
                })

        # 期待効果計算
        plan["expected_impact"] = len(plan["actions"]) * 2.5

        return plan

    def _suggest_fix_approach(self, metric: str) -> str:
        """修正アプローチ提案"""
        approaches = {
            "accuracy": "Review training data quality and model architecture",
            "efficiency": "Optimize algorithms and reduce computational complexity",
            "response_time": "Implement caching and parallel processing",
            "memory_usage": "Optimize data structures and implement garbage collection",
            "throughput": "Scale resources and optimize bottlenecks"
        }

        return approaches.get(metric, "Analyze root cause and implement targeted optimizations")

    def _suggest_enhancement_approach(self, metric: str) -> str:
        """強化アプローチ提案"""
        approaches = {
            "accuracy": "Implement ensemble methods and feature engineering",
            "efficiency": "Apply advanced optimization techniques",
            "adaptability": "Implement meta-learning and transfer learning",
            "robustness": "Add error handling and fallback mechanisms"
        }

        return approaches.get(metric, "Implement advanced techniques and continuous optimization")

class AutonomousLearningSystem:
    """自律学習システム"""

    def __init__(self, knowledge_base_size: int = 10000):
        self.knowledge_base = KnowledgeBase(knowledge_base_size)
        self.meta_learner = MetaLearner()
        self.improvement_engine = SelfImprovementEngine()
        self.learning_queue: List[LearningTask] = []
        self.active_learning = False
        self.performance_history: List[Dict[str, Any]] = []

    async def learn_from_experience(self, task: LearningTask) -> Dict[str, Any]:
        """経験から学習"""
        start_time = datetime.now()

        try:
            # 既存知識の検索
            relevant_knowledge = self.knowledge_base.retrieve_knowledge(
                task.context,
                self._infer_knowledge_type(task.learning_type)
            )

            # メタ学習によるアプローチ推奨
            recommended_approach, confidence = self.meta_learner.recommend_approach(task.context)

            # 学習実行
            learning_result = await self._execute_learning(task, relevant_knowledge, recommended_approach)

            # 経験記録
            experience = LearningExperience(
                experience_id=f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{task.task_id}",
                task_id=task.task_id,
                approach_used=recommended_approach,
                input_features=self._extract_features(task.input_data),
                output_result=learning_result.get("output"),
                performance_score=learning_result.get("performance", 0.0),
                context=task.context,
                lessons_learned=learning_result.get("lessons", [])
            )

            self.meta_learner.learning_history.append(experience)

            # 新しい知識の抽出と保存
            if learning_result.get("success", False):
                new_knowledge = self._extract_knowledge(task, learning_result, experience)
                if new_knowledge:
                    self.knowledge_base.add_knowledge(new_knowledge)

            # タスク完了マーク
            task.completed_at = datetime.now()
            task.success = learning_result.get("success", False)

            duration = (datetime.now() - start_time).total_seconds()

            return {
                "success": True,
                "task_id": task.task_id,
                "approach_used": recommended_approach,
                "confidence": confidence,
                "performance": learning_result.get("performance", 0.0),
                "knowledge_created": new_knowledge.knowledge_id if new_knowledge else None,
                "duration_seconds": duration,
                "experience_id": experience.experience_id
            }

        except Exception as e:
            logger.error(f"Learning failed for task {task.task_id}: {e}")
            task.completed_at = datetime.now()
            task.success = False

            return {
                "success": False,
                "task_id": task.task_id,
                "error": str(e),
                "duration_seconds": (datetime.now() - start_time).total_seconds()
            }

    async def _execute_learning(self, task: LearningTask, relevant_knowledge: List[KnowledgeItem],
                               approach: str) -> Dict[str, Any]:
        """学習実行"""
        # 学習タイプ別の実行
        if task.learning_type == LearningType.SUPERVISED:
            return await self._execute_supervised_learning(task, relevant_knowledge, approach)
        elif task.learning_type == LearningType.REINFORCEMENT:
            return await self._execute_reinforcement_learning(task, relevant_knowledge, approach)
        elif task.learning_type == LearningType.META_LEARNING:
            return await self._execute_meta_learning(task, relevant_knowledge, approach)
        else:
            return await self._execute_default_learning(task, relevant_knowledge, approach)

    async def _execute_supervised_learning(self, task: LearningTask,
                                         knowledge: List[KnowledgeItem], approach: str) -> Dict[str, Any]:
        """教師あり学習実行"""
        # シミュレーション実装
        await asyncio.sleep(0.1)  # 学習時間のシミュレート

        # 既存知識の活用
        base_performance = 0.5
        if knowledge:
            # 関連知識があれば性能向上
            avg_confidence = np.mean([k.confidence for k in knowledge])
            base_performance += avg_confidence * 0.3

        # アプローチ別の性能調整
        approach_multipliers = {
            "neural_network": 1.2,
            "ensemble": 1.1,
            "default": 1.0
        }

        multiplier = approach_multipliers.get(approach, 1.0)
        final_performance = min(0.95, base_performance * multiplier + np.random.uniform(-0.1, 0.1))

        return {
            "success": final_performance > 0.6,
            "performance": final_performance,
            "output": f"trained_model_{task.task_id}",
            "lessons": [
                f"Approach '{approach}' achieved {final_performance:.1%} performance",
                f"Used {len(knowledge)} relevant knowledge items"
            ]
        }

    async def _execute_reinforcement_learning(self, task: LearningTask,
                                            knowledge: List[KnowledgeItem], approach: str) -> Dict[str, Any]:
        """強化学習実行"""
        await asyncio.sleep(0.2)  # より長い学習時間

        # エピソード数シミュレーション
        episodes = task.context.get("episodes", 100)
        base_performance = min(0.9, 0.3 + (episodes / 1000))

        # 既存戦略の活用
        if knowledge:
            strategy_knowledge = [k for k in knowledge if k.knowledge_type == KnowledgeType.STRATEGY]
            if strategy_knowledge:
                base_performance += len(strategy_knowledge) * 0.05

        final_performance = min(0.95, base_performance + np.random.uniform(-0.05, 0.1))

        return {
            "success": final_performance > 0.5,
            "performance": final_performance,
            "output": f"policy_{task.task_id}",
            "lessons": [
                f"Completed {episodes} episodes",
                f"Final performance: {final_performance:.1%}",
                "Exploration vs exploitation balance achieved"
            ]
        }

    async def _execute_meta_learning(self, task: LearningTask,
                                   knowledge: List[KnowledgeItem], approach: str) -> Dict[str, Any]:
        """メタ学習実行"""
        await asyncio.sleep(0.15)

        # メタ学習パターン分析
        patterns = self.meta_learner.analyze_learning_patterns()
        base_performance = 0.6

        if patterns.get("status") == "analyzed":
            # 過去の学習パターンを活用
            if patterns.get("best_score", 0) > 0.7:
                base_performance = 0.75

        final_performance = min(0.95, base_performance + np.random.uniform(-0.05, 0.15))

        return {
            "success": final_performance > 0.65,
            "performance": final_performance,
            "output": f"meta_strategy_{task.task_id}",
            "lessons": [
                "Analyzed learning patterns across tasks",
                f"Meta-performance: {final_performance:.1%}",
                "Developed adaptive learning strategy"
            ]
        }

    async def _execute_default_learning(self, task: LearningTask,
                                      knowledge: List[KnowledgeItem], approach: str) -> Dict[str, Any]:
        """デフォルト学習実行"""
        await asyncio.sleep(0.05)

        base_performance = 0.6 + np.random.uniform(-0.2, 0.2)

        return {
            "success": base_performance > 0.5,
            "performance": base_performance,
            "output": f"result_{task.task_id}",
            "lessons": [f"Completed {task.learning_type.value} learning"]
        }

    def _extract_knowledge(self, task: LearningTask, result: Dict[str, Any],
                          experience: LearningExperience) -> Optional[KnowledgeItem]:
        """知識抽出"""
        if not result.get("success", False):
            return None

        # 知識タイプ決定
        knowledge_type = self._infer_knowledge_type(task.learning_type)

        # 知識内容作成
        content = {
            "approach": experience.approach_used,
            "performance": result.get("performance", 0.0),
            "context_features": self._extract_features(task.input_data),
            "lessons": result.get("lessons", [])
        }

        # 適用可能コンテキスト推定
        contexts = self._infer_applicable_contexts(task.context)

        knowledge_id = f"knowledge_{hashlib.md5(str(content).encode()).hexdigest()[:8]}"

        return KnowledgeItem(
            knowledge_id=knowledge_id,
            knowledge_type=knowledge_type,
            content=content,
            confidence=result.get("performance", 0.0),
            source_task=task.task_id,
            applicable_contexts=contexts
        )

    def _infer_knowledge_type(self, learning_type: LearningType) -> KnowledgeType:
        """学習タイプから知識タイプを推定"""
        mapping = {
            LearningType.SUPERVISED: KnowledgeType.MODEL,
            LearningType.REINFORCEMENT: KnowledgeType.STRATEGY,
            LearningType.META_LEARNING: KnowledgeType.HEURISTIC,
            LearningType.UNSUPERVISED: KnowledgeType.PATTERN
        }
        return mapping.get(learning_type, KnowledgeType.EXPERIENCE)

    def _extract_features(self, input_data: Any) -> Dict[str, Any]:
        """特徴量抽出"""
        if isinstance(input_data, dict):
            return {k: str(v) for k, v in input_data.items()}
        elif isinstance(input_data, (list, tuple)):
            return {"length": len(input_data), "type": "sequence"}
        elif isinstance(input_data, str):
            return {"length": len(input_data), "type": "text"}
        else:
            return {"type": type(input_data).__name__}

    def _infer_applicable_contexts(self, context: Dict[str, Any]) -> List[str]:
        """適用可能コンテキスト推定"""
        contexts = []

        # ドメイン
        if "domain" in context:
            contexts.append(context["domain"])

        # タスクタイプ
        if "task_type" in context:
            contexts.append(context["task_type"])

        # データタイプ
        if "data_type" in context:
            contexts.append(context["data_type"])

        return contexts

    async def continuous_learning_loop(self, interval_minutes: int = 30):
        """継続学習ループ"""
        self.active_learning = True
        logger.info("Autonomous learning started")

        while self.active_learning:
            try:
                # キューからタスクを取得
                if self.learning_queue:
                    task = self.learning_queue.pop(0)
                    result = await self.learn_from_experience(task)
                    logger.info(f"Completed learning task: {task.task_id}")

                # 自己評価と改善
                await self._perform_self_evaluation()

                # 待機
                await asyncio.sleep(interval_minutes * 60)

            except Exception as e:
                logger.error(f"Error in learning loop: {e}")
                await asyncio.sleep(60)

    def stop_learning(self):
        """学習停止"""
        self.active_learning = False
        logger.info("Autonomous learning stopped")

    async def _perform_self_evaluation(self):
        """自己評価実行"""
        # 現在の性能メトリクス収集
        current_metrics = {
            "knowledge_items": len(self.knowledge_base.knowledge_items),
            "learning_experiences": len(self.meta_learner.learning_history),
            "avg_knowledge_confidence": 0.0,
            "recent_success_rate": 0.0
        }

        # 知識ベース統計
        kb_stats = self.knowledge_base.get_knowledge_statistics()
        if kb_stats.get("total_items", 0) > 0:
            current_metrics["avg_knowledge_confidence"] = kb_stats.get("avg_confidence", 0.0)

        # 最近の成功率
        recent_experiences = self.meta_learner.learning_history[-10:]
        if recent_experiences:
            current_metrics["recent_success_rate"] = np.mean([
                exp.performance_score for exp in recent_experiences
            ])

        # 性能評価
        evaluation = self.improvement_engine.evaluate_current_performance(current_metrics)

        # 改善計画生成
        if evaluation.get("overall_improvement", 0) < 0:
            improvement_plan = self.improvement_engine.generate_improvement_plan(evaluation)
            logger.info(f"Generated improvement plan: {improvement_plan['plan_id']}")

        # 履歴記録
        self.performance_history.append({
            "timestamp": datetime.now().isoformat(),
            "metrics": current_metrics,
            "evaluation": evaluation
        })

    def get_system_status(self) -> Dict[str, Any]:
        """システム状態取得"""
        kb_stats = self.knowledge_base.get_knowledge_statistics()
        meta_analysis = self.meta_learner.analyze_learning_patterns()

        return {
            "active_learning": self.active_learning,
            "queued_tasks": len(self.learning_queue),
            "knowledge_base": kb_stats,
            "learning_analysis": meta_analysis,
            "performance_evaluations": len(self.performance_history),
            "last_evaluation": self.performance_history[-1]["timestamp"] if self.performance_history else None
        }

# グローバルインスタンス
autonomous_learner = AutonomousLearningSystem()

# 便利な関数
def add_learning_task(task_id: str, name: str, learning_type: LearningType,
                     input_data: Any, target_output: Any = None,
                     context: Dict[str, Any] = None) -> LearningTask:
    """学習タスク追加"""
    task = LearningTask(
        task_id=task_id,
        name=name,
        learning_type=learning_type,
        input_data=input_data,
        target_output=target_output,
        context=context or {}
    )
    autonomous_learner.learning_queue.append(task)
    return task

def start_autonomous_learning(interval_minutes: int = 30):
    """自律学習開始"""
    return asyncio.create_task(autonomous_learner.continuous_learning_loop(interval_minutes))

def stop_autonomous_learning():
    """自律学習停止"""
    autonomous_learner.stop_learning()

def get_learning_status() -> Dict[str, Any]:
    """学習状態取得"""
    return autonomous_learner.get_system_status()

if __name__ == "__main__":
    async def main():
        print("🧠 Autonomous Learning System")
        print("=" * 50)

        # テスト学習タスク追加
        task1 = add_learning_task(
            "test_supervised",
            "Test Supervised Learning",
            LearningType.SUPERVISED,
            {"features": [1, 2, 3, 4], "labels": [0, 1, 0, 1]},
            context={"domain": "classification", "data_type": "tabular"}
        )

        task2 = add_learning_task(
            "test_reinforcement",
            "Test Reinforcement Learning",
            LearningType.REINFORCEMENT,
            {"environment": "test_env", "actions": 4},
            context={"domain": "control", "episodes": 500}
        )

        print(f"Added {len(autonomous_learner.learning_queue)} learning tasks")

        # 学習実行
        print("\n🔄 Executing learning tasks...")
        for task in autonomous_learner.learning_queue.copy():
            result = await autonomous_learner.learn_from_experience(task)
            print(f"  {task.name}: {'✅' if result['success'] else '❌'} "
                  f"({result.get('performance', 0):.1%})")

        # システム状態確認
        status = get_learning_status()
        print(f"\n📊 System Status:")
        print(f"  Knowledge Items: {status['knowledge_base']['total_items']}")
        print(f"  Learning Experiences: {status['learning_analysis'].get('total_experiences', 0)}")
        print(f"  Active Learning: {status['active_learning']}")

        if status['knowledge_base']['total_items'] > 0:
            print(f"  Avg Confidence: {status['knowledge_base']['avg_confidence']:.1%}")

        if status['learning_analysis'].get('best_approach'):
            print(f"  Best Approach: {status['learning_analysis']['best_approach']}")

    asyncio.run(main())
