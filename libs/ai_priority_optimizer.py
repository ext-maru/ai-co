#!/usr/bin/env python3
"""
AI駆動型タスク優先順位最適化システム
4賢者協調による自律的な優先度決定
"""

import asyncio
import json
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

# プロジェクトルート設定
PROJECT_ROOT = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(PROJECT_ROOT))

from libs.knowledge_base_manager import KnowledgeBaseManager
from features.database.task_history_db import TaskHistoryDB


class TaskType(Enum):
    """タスクタイプ定義"""
    PROJECT_INTERNAL = "project_internal"      # プロジェクト内タスク
    CROSS_PROJECT = "cross_project"           # プロジェクト横断タスク
    SYSTEM_WIDE = "system_wide"               # システム全体タスク
    INCIDENT = "incident"                     # インシデント対応
    TECHNICAL_DEBT = "technical_debt"         # 技術的負債


@dataclass
class Task:
    """タスク定義"""
    id: str
    name: str
    type: TaskType
    project: str
    dependencies: List[str] = field(default_factory=list)
    estimated_hours: float = 0
    business_value: float = 0
    technical_complexity: float = 0
    incident_risk: float = 0
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PriorityScore:
    """優先度スコア"""
    total_score: float
    business_impact: float
    technical_urgency: float
    risk_mitigation: float
    resource_efficiency: float
    reasoning: Dict[str, str]
    confidence: float


class SageEvaluator:
    """賢者評価基底クラス"""

    def __init__(self, name: str):
        self.name = name
        self.learning_data = []

    async def evaluate(self, task: Task, context: Dict[str, Any]) -> Dict[str, float]:
        """タスク評価（サブクラスで実装）"""
        raise NotImplementedError


class TaskSage(SageEvaluator):
    """タスク賢者 - ビジネス価値評価"""

    def __init__(self):
        super().__init__("📋 タスク賢者")

    async def evaluate(self, task: Task, context: Dict[str, Any]) -> Dict[str, float]:
        """ビジネスインパクト評価"""
        # ビジネス価値の評価
        business_score = task.business_value

        # プロジェクト重要度による調整
        project_importance = context.get("project_importance", {}).get(task.project, 1.0)
        business_score *= project_importance

        # タスクタイプによる調整
        if task.type == TaskType.INCIDENT:
            business_score *= 2.0  # インシデントは倍率
        elif task.type == TaskType.CROSS_PROJECT:
            business_score *= 1.5  # 横断タスクは1.5倍

        # 依存関係による加点
        dependency_bonus = len(task.dependencies) * 0.1
        business_score *= (1 + dependency_bonus)

        return {
            "business_impact": min(business_score, 10.0),
            "dependency_importance": dependency_bonus,
            "project_priority": project_importance
        }


class KnowledgeSage(SageEvaluator):
    """ナレッジ賢者 - 技術的負債評価"""

    def __init__(self):
        super().__init__("📚 ナレッジ賢者")

    async def evaluate(self, task: Task, context: Dict[str, Any]) -> Dict[str, float]:
        """技術的負債の評価"""
        debt_score = 0

        # 技術的負債タスクの評価
        if task.type == TaskType.TECHNICAL_DEBT:
            debt_score = 8.0  # ベース高スコア

            # 放置期間による加点
            age_days = (datetime.now() - task.created_at).days
            debt_score += min(age_days / 30, 2.0)  # 最大2点加点
        else:
            # 通常タスクでも複雑度を考慮
            debt_score = task.technical_complexity * 0.5

        # 過去の類似タスクから学習
        similar_tasks = context.get("similar_tasks", [])
        if similar_tasks:
            avg_impact = sum(t.get("impact", 0) for t in similar_tasks) / len(similar_tasks)
            debt_score *= (1 + avg_impact * 0.1)

        return {
            "technical_debt_score": min(debt_score, 10.0),
            "complexity_factor": task.technical_complexity,
            "age_factor": (datetime.now() - task.created_at).days / 30
        }


class IncidentSage(SageEvaluator):
    """インシデント賢者 - リスク評価"""

    def __init__(self):
        super().__init__("🚨 インシデント賢者")

    async def evaluate(self, task: Task, context: Dict[str, Any]) -> Dict[str, float]:
        """リスク評価"""
        risk_score = task.incident_risk

        # インシデントタスクは最高優先度
        if task.type == TaskType.INCIDENT:
            risk_score = 10.0
        else:
            # 予防的リスク評価
            if "security" in task.name.lower() or "critical" in task.name.lower():
                risk_score *= 2.0

            # システム全体への影響
            if task.type == TaskType.SYSTEM_WIDE:
                risk_score *= 1.5

        # 過去のインシデント履歴から学習
        incident_history = context.get("incident_history", [])
        if task.project in [inc.get("project") for inc in incident_history]:
            risk_score *= 1.3  # リスク履歴があるプロジェクトは加点

        return {
            "risk_score": min(risk_score, 10.0),
            "incident_probability": risk_score / 10.0,
            "impact_scope": "system" if task.type == TaskType.SYSTEM_WIDE else "project"
        }


class RAGSage(SageEvaluator):
    """RAG賢者 - リソース最適化評価"""

    def __init__(self):
        super().__init__("🔍 RAG賢者")

    async def evaluate(self, task: Task, context: Dict[str, Any]) -> Dict[str, float]:
        """リソース効率性評価"""
        # 利用可能リソースの確認
        available_resources = context.get("available_resources", 100)
        current_load = context.get("current_load", 0)

        # リソース効率スコア
        efficiency_score = 0

        # 小さなタスクで大きな価値
        if task.estimated_hours < 4 and task.business_value > 5:
            efficiency_score = 8.0
        # 適正規模のタスク
        elif 4 <= task.estimated_hours <= 16:
            efficiency_score = 6.0
        # 大規模タスク
        else:
            efficiency_score = 4.0

        # リソース余裕度による調整
        resource_availability = (available_resources - current_load) / available_resources
        efficiency_score *= (1 + resource_availability * 0.5)

        # 並列実行可能性
        if not task.dependencies:
            efficiency_score *= 1.2  # 依存なしは並列実行可能

        return {
            "resource_efficiency": min(efficiency_score, 10.0),
            "parallel_executable": len(task.dependencies) == 0,
            "resource_fit": resource_availability
        }


class AIPriorityOptimizer:
    """AI駆動型優先順位最適化システム"""

    def __init__(self):
        self.task_sage = TaskSage()
        self.knowledge_sage = KnowledgeSage()
        self.incident_sage = IncidentSage()
        self.rag_sage = RAGSage()

        # 学習データ保存
        self.learning_history_file = PROJECT_ROOT / "knowledge_base" / "ai_priority_learning.json"
        self.learning_history = self.load_learning_history()

        # ロガー設定
        self.logger = logging.getLogger("AIPriorityOptimizer")
        self.logger.setLevel(logging.INFO)

        # 人間のフィードバック履歴
        self.feedback_history = []

    def load_learning_history(self) -> List[Dict[str, Any]]:
        """学習履歴の読み込み"""
        if self.learning_history_file.exists():
            with open(self.learning_history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def save_learning_history(self):
        """学習履歴の保存"""
        self.learning_history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.learning_history_file, 'w', encoding='utf-8') as f:
            json.dump(self.learning_history, f, indent=2, ensure_ascii=False, default=str)

    async def calculate_priority(self, task: Task, context: Dict[str, Any]) -> PriorityScore:
        """AI駆動による優先度計算"""
        # 4賢者による評価を並列実行
        evaluations = await asyncio.gather(
            self.task_sage.evaluate(task, context),
            self.knowledge_sage.evaluate(task, context),
            self.incident_sage.evaluate(task, context),
            self.rag_sage.evaluate(task, context)
        )

        # 評価結果の統合
        task_eval = evaluations[0]
        knowledge_eval = evaluations[1]
        incident_eval = evaluations[2]
        rag_eval = evaluations[3]

        # AI最適化による重み付け（学習により調整）
        weights = self.get_dynamic_weights(task, context)

        # スコア計算
        business_impact = task_eval["business_impact"] * weights["business"]
        technical_urgency = knowledge_eval["technical_debt_score"] * weights["technical"]
        risk_mitigation = incident_eval["risk_score"] * weights["risk"]
        resource_efficiency = rag_eval["resource_efficiency"] * weights["resource"]

        # 総合スコア
        total_score = (
            business_impact +
            technical_urgency +
            risk_mitigation +
            resource_efficiency
        ) / 4.0

        # 信頼度計算
        confidence = self.calculate_confidence(task, context)

        # 推論理由の生成
        reasoning = {
            "business": f"ビジネス価値 {task.business_value:.1f} × プロジェクト重要度",
            "technical": f"技術的複雑度 {task.technical_complexity:.1f} + 負債スコア",
            "risk": f"リスクレベル {task.incident_risk:.1f} × インパクト範囲",
            "resource": f"推定時間 {task.estimated_hours:.1f}h での効率性"
        }

        # 学習データとして記録
        self.record_learning_data(task, total_score, weights, context)

        return PriorityScore(
            total_score=total_score,
            business_impact=business_impact,
            technical_urgency=technical_urgency,
            risk_mitigation=risk_mitigation,
            resource_efficiency=resource_efficiency,
            reasoning=reasoning,
            confidence=confidence
        )

    def get_dynamic_weights(self, task: Task, context: Dict[str, Any]) -> Dict[str, float]:
        """動的な重み付け取得（学習ベース）"""
        # デフォルトの重み
        weights = {
            "business": 0.25,
            "technical": 0.25,
            "risk": 0.25,
            "resource": 0.25
        }

        # タスクタイプによる調整
        if task.type == TaskType.INCIDENT:
            weights["risk"] = 0.5
            weights["business"] = 0.3
            weights["technical"] = 0.1
            weights["resource"] = 0.1
        elif task.type == TaskType.TECHNICAL_DEBT:
            weights["technical"] = 0.4
            weights["risk"] = 0.3
            weights["business"] = 0.2
            weights["resource"] = 0.1
        elif task.type == TaskType.CROSS_PROJECT:
            weights["business"] = 0.4
            weights["resource"] = 0.3
            weights["technical"] = 0.2
            weights["risk"] = 0.1

        # 学習による調整
        if self.learning_history:
            similar_tasks = self.find_similar_tasks(task)
            if similar_tasks:
                # 過去の成功パターンから学習
                avg_weights = self.calculate_average_weights(similar_tasks)
                # 徐々に学習結果を反映（急激な変化を避ける）
                for key in weights:
                    weights[key] = weights[key] * 0.7 + avg_weights.get(key, weights[key]) * 0.3

        return weights

    def calculate_confidence(self, task: Task, context: Dict[str, Any]) -> float:
        """優先度計算の信頼度"""
        confidence = 0.5  # ベース信頼度

        # 類似タスクの学習データがあるか
        similar_tasks = self.find_similar_tasks(task)
        if len(similar_tasks) > 10:
            confidence += 0.3
        elif len(similar_tasks) > 5:
            confidence += 0.2
        elif len(similar_tasks) > 0:
            confidence += 0.1

        # フィードバック履歴
        positive_feedback = sum(1 for f in self.feedback_history if f["positive"])
        if len(self.feedback_history) > 0:
            feedback_rate = positive_feedback / len(self.feedback_history)
            confidence += feedback_rate * 0.2

        return min(confidence, 1.0)

    def find_similar_tasks(self, task: Task) -> List[Dict[str, Any]]:
        """類似タスクの検索"""
        similar = []
        for record in self.learning_history:
            if (record["task_type"] == task.type.value and
                abs(record["business_value"] - task.business_value) < 2.0):
                similar.append(record)
        return similar

    def calculate_average_weights(self, tasks: List[Dict[str, Any]]) -> Dict[str, float]:
        """平均重み付けの計算"""
        if not tasks:
            return {}

        weights_sum = {"business": 0, "technical": 0, "risk": 0, "resource": 0}
        for task in tasks:
            for key in weights_sum:
                weights_sum[key] += task["weights"].get(key, 0)

        return {key: val / len(tasks) for key, val in weights_sum.items()}

    def record_learning_data(self, task: Task, score: float, weights: Dict[str, float], context: Dict[str, Any]):
        """学習データの記録"""
        learning_record = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task.id,
            "task_type": task.type.value,
            "business_value": task.business_value,
            "technical_complexity": task.technical_complexity,
            "incident_risk": task.incident_risk,
            "priority_score": score,
            "weights": weights,
            "context_summary": {
                "available_resources": context.get("available_resources", 0),
                "current_load": context.get("current_load", 0),
                "active_projects": len(context.get("project_importance", {}))
            }
        }

        self.learning_history.append(learning_record)

        # 定期的に保存（100件ごと）
        if len(self.learning_history) % 100 == 0:
            self.save_learning_history()

    async def batch_prioritize(self, tasks: List[Task], context: Dict[str, Any]) -> List[Tuple[Task, PriorityScore]]:
        """バッチでの優先順位付け"""
        # 並列で全タスクを評価
        priorities = await asyncio.gather(
            *[self.calculate_priority(task, context) for task in tasks]
        )

        # タスクと優先度のペアを作成
        task_priorities = list(zip(tasks, priorities))

        # 優先度でソート（降順）
        task_priorities.sort(key=lambda x: x[1].total_score, reverse=True)

        return task_priorities

    def receive_feedback(self, task_id: str, feedback: str, adjustment: Optional[float] = None):
        """人間からのフィードバック受信"""
        feedback_record = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "feedback": feedback,
            "positive": feedback.lower() in ["good", "correct", "ok", "良い", "正しい"],
            "adjustment": adjustment
        }

        self.feedback_history.append(feedback_record)

        # フィードバックに基づく学習
        if adjustment is not None:
            # 該当タスクの学習データを調整
            for record in self.learning_history:
                if record["task_id"] == task_id:
                    record["human_adjusted_score"] = adjustment
                    break

        # 即座に保存
        self.save_learning_history()

        self.logger.info(f"フィードバック受信: {task_id} - {feedback}")

    def generate_explanation(self, task: Task, score: PriorityScore) -> str:
        """優先度決定の説明生成"""
        explanation = f"""
🎯 タスク: {task.name}
📊 優先度スコア: {score.total_score:.2f} (信頼度: {score.confidence:.0%})

📋 評価内訳:
- ビジネスインパクト: {score.business_impact:.2f}
  {score.reasoning['business']}

- 技術的緊急度: {score.technical_urgency:.2f}
  {score.reasoning['technical']}

- リスク軽減: {score.risk_mitigation:.2f}
  {score.reasoning['risk']}

- リソース効率: {score.resource_efficiency:.2f}
  {score.reasoning['resource']}

💡 この優先度は{len(self.learning_history)}件の学習データに基づいています。
"""
        return explanation


# 使用例
async def demo():
    """デモ実行"""
    optimizer = AIPriorityOptimizer()

    # サンプルタスク
    tasks = [
        Task(
            id="task-001",
            name="緊急セキュリティパッチ適用",
            type=TaskType.INCIDENT,
            project="api",
            business_value=8.0,
            technical_complexity=3.0,
            incident_risk=9.0,
            estimated_hours=2.0
        ),
        Task(
            id="task-002",
            name="新機能：ユーザーダッシュボード",
            type=TaskType.PROJECT_INTERNAL,
            project="frontend",
            business_value=7.0,
            technical_complexity=6.0,
            incident_risk=2.0,
            estimated_hours=40.0
        ),
        Task(
            id="task-003",
            name="技術的負債：データベース最適化",
            type=TaskType.TECHNICAL_DEBT,
            project="api",
            business_value=4.0,
            technical_complexity=8.0,
            incident_risk=3.0,
            estimated_hours=16.0
        )
    ]

    # コンテキスト情報
    context = {
        "available_resources": 100,
        "current_load": 30,
        "project_importance": {
            "api": 1.2,
            "frontend": 1.0
        },
        "incident_history": [
            {"project": "api", "severity": "high"}
        ]
    }

    # 優先順位付け実行
    prioritized = await optimizer.batch_prioritize(tasks, context)

    print("🏛️ AI駆動型優先順位付け結果")
    print("=" * 60)

    for i, (task, score) in enumerate(prioritized, 1):
        print(f"\n{i}位: {task.name}")
        print(f"   スコア: {score.total_score:.2f}")
        print(f"   信頼度: {score.confidence:.0%}")

    # 説明生成
    top_task, top_score = prioritized[0]
    explanation = optimizer.generate_explanation(top_task, top_score)
    print("\n" + explanation)


if __name__ == "__main__":
    asyncio.run(demo())
