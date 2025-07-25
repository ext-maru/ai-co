#!/usr/bin/env python3
"""
EITMS AI最適化・学習エンジン

AI駆動によるタスク管理最適化システム
- 優先度自動調整
- 工数見積もり学習
- パフォーマンス予測
- 4賢者連携AI最適化

Author: クロードエルダー（Claude Elder）  
Created: 2025/07/21
Version: 1.0.0
"""

import asyncio
import json
import logging
import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import pickle
import numpy as np
from collections import defaultdict, deque
import uuid

# 内部インポート処理
import sys
import os
sys.path.append(os.path.dirname(__file__))

# 統一データモデルからインポート
if os.path.exists(os.path.join(os.path.dirname(__file__), 'eitms_unified_data_model.py')):
    from eitms_unified_data_model import (
        UnifiedTask, TaskType, TaskStatus, Priority,
        EitmsUnifiedManager
    )
else:
    # モック定義
    from enum import Enum
    from dataclasses import dataclass
    
    class TaskType(Enum):
        """TaskTypeクラス"""

        PROJECT_TASK = "project_task" 
        ISSUE = "issue"
        PLANNING = "planning"
    
    class TaskStatus(Enum):
        """TaskStatusクラス"""
        CREATED = "created"
        IN_PROGRESS = "in_progress"
        COMPLETED = "completed"
        BLOCKED = "blocked"
    
    class Priority(Enum):
        """Priorityクラス"""
        HIGH = "high"
        MEDIUM = "medium"
        LOW = "low"
        CRITICAL = "critical"
    
    @dataclass
    class UnifiedTask:
        """UnifiedTaskクラス"""
        id: str = "mock-id"
        title: str = ""

        status: TaskStatus = TaskStatus.CREATED
        priority: Priority = Priority.MEDIUM
        context: Dict = field(default_factory=dict)
        time_estimated: Optional[int] = None
        time_spent: Optional[int] = None

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizationStrategy(Enum):
    """最適化戦略"""
    PRIORITY_BOOST = "priority_boost"
    EFFORT_BALANCE = "effort_balance"
    DEADLINE_DRIVEN = "deadline_driven"
    SKILL_MATCHING = "skill_matching"
    DEPENDENCY_AWARE = "dependency_aware"

@dataclass
class TaskMetrics:
    """タスクメトリクス"""
    
    task_id: str = ""
    complexity_score: float = 0.0
    estimated_hours: float = 0.0
    actual_hours: Optional[float] = None
    completion_probability: float = 0.5
    priority_score: float = 0.0
    dependency_impact: float = 0.0
    skills_required: List[str] = field(default_factory=list)
    historical_accuracy: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """to_dictメソッド"""
        return {
            'task_id': self.task_id,
            'complexity_score': self.complexity_score,
            'estimated_hours': self.estimated_hours,
            'actual_hours': self.actual_hours,
            'completion_probability': self.completion_probability,
            'priority_score': self.priority_score,
            'dependency_impact': self.dependency_impact,
            'skills_required': self.skills_required,
            'historical_accuracy': self.historical_accuracy
        }

@dataclass
class AIRecommendation:
    """AI推奨事項"""
    
    task_id: str = ""
    recommendation_type: str = ""
    current_value: Any = None
    recommended_value: Any = None
    confidence: float = 0.0
    reasoning: str = ""
    impact_score: float = 0.0
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """to_dictメソッド"""
        return {
            'task_id': self.task_id,
            'recommendation_type': self.recommendation_type,
            'current_value': self.current_value,
            'recommended_value': self.recommended_value,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'impact_score': self.impact_score,
            'generated_at': self.generated_at.isoformat()
        }

class ComplexityAnalyzer:
    """複雑度分析エンジン"""
    
    def __init__(self):
        """初期化メソッド"""
        self.keywords_weights = {
            # 高複雑度キーワード
            'system': 1.5, 'architecture': 2.0, 'integration': 1.8, 'optimization': 1.6,
            'algorithm': 1.7, 'performance': 1.4, 'security': 1.9, 'migration': 2.1,
            'refactor': 1.3, 'database': 1.5, 'api': 1.2, 'framework': 1.4,
            
            # 中複雑度キーワード  
            'feature': 1.0, 'function': 0.9, 'component': 1.1, 'module': 1.0,
            'test': 0.8, 'documentation': 0.6, 'ui': 0.9, 'frontend': 1.0,
            
            # 低複雑度キーワード
            'fix': 0.7, 'update': 0.5, 'config': 0.6, 'style': 0.4,
            'typo': 0.2, 'text': 0.3, 'comment': 0.3
        }
        
        self.type_multipliers = {
            TaskType.PLANNING: 1.8,
            TaskType.ISSUE: 1.4,
            TaskType.PROJECT_TASK: 1.2,

        }
    
    def analyze_complexity(self, task: UnifiedTask) -> float:
        """タスク複雑度分析"""
        text = f"{task.title} {task.description}".lower()
        
        # キーワードベース複雑度
        keyword_score = 1.0
        for keyword, weight in self.keywords_weights.items():
            if keyword in text:
                keyword_score *= weight
        
        # テキスト長による調整
        length_factor = min(len(text) / 200, 2.0)  # 最大2倍まで
        
        # タスク種別による調整
        type_multiplier = self.type_multipliers.get(task.task_type, 1.0)
        
        # 依存関係による調整
        dependency_factor = 1.0
        if hasattr(task, 'dependencies') and task.dependencies:
            dependency_factor = 1 + (len(task.dependencies) * 0.1)
        
        complexity = keyword_score * length_factor * type_multiplier * dependency_factor
        
        # 0.1〜5.0の範囲に正規化
        return max(0.1, min(5.0, complexity))

class EffortEstimator:
    """工数見積もりエンジン"""
    
    def __init__(self):
        """初期化メソッド"""
        self.historical_data = defaultdict(list)
        self.base_estimates = {

            TaskType.PROJECT_TASK: 4.0,  # 4時間
            TaskType.ISSUE: 8.0,     # 8時間
            TaskType.PLANNING: 2.0   # 2時間
        }
        
        self.complexity_multipliers = {
            'very_low': 0.5,
            'low': 0.8,
            'medium': 1.0,
            'high': 1.5,
            'very_high': 2.5
        }
    
    def estimate_effort(self, task: UnifiedTask, complexity_score: float) -> float:
        """工数見積もり"""
        # ベース見積もり
        base_hours = self.base_estimates.get(task.task_type, 2.0)
        
        # 複雑度による調整
        complexity_category = self._categorize_complexity(complexity_score)
        complexity_multiplier = self.complexity_multipliers[complexity_category]
        
        # 過去データによる調整
        historical_adjustment = self._get_historical_adjustment(task)
        
        # 優先度による調整（高優先度はより慎重に見積もり）
        priority_adjustment = {
            Priority.CRITICAL: 1.3,
            Priority.HIGH: 1.2,
            Priority.MEDIUM: 1.0,
            Priority.LOW: 0.9
        }.get(task.priority, 1.0)
        
        estimated_hours = (base_hours * complexity_multiplier * 
                         historical_adjustment * priority_adjustment)
        
        return round(max(0.25, estimated_hours), 2)  # 最低15分
    
    def _categorize_complexity(self, score: float) -> str:
        """複雑度カテゴリ化"""
        if score <= 0.5:
            return 'very_low'
        elif score <= 1.0:
            return 'low'
        elif score <= 2.0:
            return 'medium'
        elif score <= 3.5:
            return 'high'
        else:
            return 'very_high'
    
    def _get_historical_adjustment(self, task: UnifiedTask) -> float:
        """過去データによる調整係数"""
        task_type_data = self.historical_data.get(task.task_type.value, [])
        
        if len(task_type_data) < 3:
            return 1.0  # データ不足の場合はデフォルト
        
        # 過去の見積もり精度から調整
        accuracies = [data['accuracy'] for data in task_type_data[-10:]]  # 最新10件
        avg_accuracy = statistics.mean(accuracies)
        
        # 精度が低い場合は見積もりを上げる
        if avg_accuracy < 0.8:
            return 1.2
        elif avg_accuracy > 1.2:
            return 0.9
        else:
            return 1.0
    
    def learn_from_completion(self, task: UnifiedTask, actual_hours: float, estimated_hours: float):
        """完了データからの学習"""
        accuracy = actual_hours / max(estimated_hours, 0.1)
        
        self.historical_data[task.task_type.value].append({
            'task_id': task.id,
            'estimated': estimated_hours,
            'actual': actual_hours,
            'accuracy': accuracy,
            'complexity_indicators': self._extract_complexity_indicators(task),
            'timestamp': datetime.now(timezone.utc)
        })
        
        # 古いデータの削除（最大100件保持）
        if len(self.historical_data[task.task_type.value]) > 100:
            self.historical_data[task.task_type.value] = \
                self.historical_data[task.task_type.value][-100:]
    
    def _extract_complexity_indicators(self, task: UnifiedTask) -> Dict[str, Any]:
        """複雑度指標抽出"""
        return {
            'title_length': len(task.title),
            'description_length': len(task.description or ''),
            'has_dependencies': bool(getattr(task, 'dependencies', [])),
            'priority': task.priority.value
        }

class PriorityOptimizer:
    """優先度最適化エンジン"""
    
    def __init__(self):
        """初期化メソッド"""
        self.urgency_factors = {
            'deadline': 2.0,
            'blocking': 1.8,
            'critical_path': 1.6,
            'stakeholder_priority': 1.4,
            'business_value': 1.3
        }
        
        self.priority_scores = {
            Priority.CRITICAL: 100,
            Priority.HIGH: 75,
            Priority.MEDIUM: 50,
            Priority.LOW: 25
        }
    
    def optimize_priority(
        self,
        task: UnifiedTask,
        context: Dict[str,
        Any]
    ) -> Tuple[Priority, float]:
        """優先度最適化"""
        current_score = self.priority_scores[task.priority]
        
        # コンテキスト要因による調整
        urgency_boost = self._calculate_urgency_boost(context)
        impact_multiplier = self._calculate_impact_multiplier(task, context)
        effort_factor = self._calculate_effort_factor(context.get('estimated_hours', 2.0))
        
        # 最適化スコア計算
        optimized_score = current_score * urgency_boost * impact_multiplier * effort_factor
        
        # 新しい優先度決定
        new_priority = self._score_to_priority(optimized_score)
        confidence = self._calculate_confidence(current_score, optimized_score)
        
        return new_priority, confidence
    
    def _calculate_urgency_boost(self, context: Dict[str, Any]) -> float:
        """緊急度ブースト計算"""
        boost = 1.0
        
        # 期限による緊急度
        if 'due_date' in context and context['due_date']:
            try:
                due_date = datetime.fromisoformat(context['due_date'])
                days_until_due = (due_date - datetime.now(timezone.utc)).days
                
                if days_until_due <= 1:
                    boost *= 2.0
                elif days_until_due <= 3:
                    boost *= 1.5
                elif days_until_due <= 7:
                    boost *= 1.2
            except:
                pass
        
        # ブロッキング要因
        if context.get('blocking_tasks', 0) > 0:
            boost *= (1 + context['blocking_tasks'] * 0.2)
        
        # ステークホルダー要求
        if context.get('stakeholder_urgency', 'normal') == 'high':
            boost *= 1.3
        
        return min(boost, 3.0)  # 最大3倍まで
    
    def _calculate_impact_multiplier(self, task: UnifiedTask, context: Dict[str, Any]) -> float:
        """影響度乗数計算"""
        multiplier = 1.0
        
        # ビジネス価値
        business_value = context.get('business_value', 'medium')
        value_multipliers = {'critical': 1.5, 'high': 1.3, 'medium': 1.0, 'low': 0.8}
        multiplier *= value_multipliers.get(business_value, 1.0)
        
        # 依存関係影響
        dependent_tasks = context.get('dependent_tasks', 0)
        if dependent_tasks > 0:
            multiplier *= (1 + dependent_tasks * 0.1)
        
        # システム影響度
        system_impact = context.get('system_impact', 'low')
        impact_multipliers = {'high': 1.4, 'medium': 1.1, 'low': 1.0}
        multiplier *= impact_multipliers.get(system_impact, 1.0)
        
        return multiplier
    
    def _calculate_effort_factor(self, estimated_hours: float) -> float:
        """工数要因計算"""
        # 短時間で高価値なタスクを優先
        if estimated_hours <= 0.5:
            return 1.2  # クイックウィン
        elif estimated_hours <= 2.0:
            return 1.1
        elif estimated_hours >= 8.0:
            return 0.9  # 大規模タスクは若干優先度下げ
        else:
            return 1.0
    
    def _score_to_priority(self, score: float) -> Priority:
        """スコアから優先度変換"""
        if score >= 120:
            return Priority.CRITICAL
        elif score >= 85:
            return Priority.HIGH
        elif score >= 40:
            return Priority.MEDIUM
        else:
            return Priority.LOW
    
    def _calculate_confidence(self, original_score: float, optimized_score: float) -> float:
        """信頼度計算"""
        difference = abs(optimized_score - original_score)
        max_difference = max(original_score, optimized_score)
        
        if max_difference == 0:
            return 1.0
        
        # 変更幅が大きいほど信頼度は下がる
        confidence = 1.0 - (difference / max_difference * 0.5)
        return max(0.1, min(1.0, confidence))

class EitmsAiEngine:
    """EITMS AI最適化エンジン - メインオーケストレーター"""
    
    def __init__(self, unified_manager):
        """初期化メソッド"""
        self.unified_manager = unified_manager
        self.complexity_analyzer = ComplexityAnalyzer()
        self.effort_estimator = EffortEstimator()
        self.priority_optimizer = PriorityOptimizer()
        
        self.learning_enabled = True
        self.auto_optimization = True
        self.optimization_history = deque(maxlen=1000)
        
        self.ai_stats = {
            'recommendations_generated': 0,
            'recommendations_applied': 0,
            'learning_sessions': 0,
            'optimization_accuracy': 0.0
        }
    
    async def analyze_task(self, task_id: str) -> TaskMetrics:
        """タスク総合分析"""
        task = await self.unified_manager.db.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        # 複雑度分析
        complexity_score = self.complexity_analyzer.analyze_complexity(task)
        
        # 工数見積もり
        estimated_hours = self.effort_estimator.estimate_effort(task, complexity_score)
        
        # 優先度スコア計算
        priority_scores = {
            Priority.CRITICAL: 100,
            Priority.HIGH: 75, 
            Priority.MEDIUM: 50,
            Priority.LOW: 25
        }
        priority_score = priority_scores[task.priority]
        
        # 依存関係影響度
        dependency_impact = self._calculate_dependency_impact(task)
        
        # 完了確率予測
        completion_probability = self._predict_completion_probability(
            task, complexity_score, estimated_hours
        )
        
        metrics = TaskMetrics(
            task_id=task_id,
            complexity_score=complexity_score,
            estimated_hours=estimated_hours,
            completion_probability=completion_probability,
            priority_score=priority_score,
            dependency_impact=dependency_impact,
            skills_required=self._extract_required_skills(task)
        )
        
        logger.info(f"🧠 AI分析完了: {task.title} (複雑度: {complexity_score:0.2f}, 工数: {estimated_hours:0.1f}h)" \
            "🧠 AI分析完了: {task.title} (複雑度: {complexity_score:0.2f}, 工数: {estimated_hours:0.1f}h)")
        return metrics
    
    async def generate_recommendations(self, task_id: str) -> List[AIRecommendation]:
        """AI推奨事項生成"""
        task = await self.unified_manager.db.get_task(task_id)
        if not task:
            return []
        
        recommendations = []
        
        # 複雑度分析
        complexity_score = self.complexity_analyzer.analyze_complexity(task)
        
        # 1.0 優先度最適化推奨
        context = self._build_task_context(task)
        new_priority, confidence = self.priority_optimizer.optimize_priority(task, context)
        
        if new_priority != task.priority and confidence > 0.7:
            recommendations.append(AIRecommendation(
                task_id=task_id,
                recommendation_type='priority_adjustment',
                current_value=task.priority.value,
                recommended_value=new_priority.value,
                confidence=confidence,
                reasoning=f"コンテキスト分析により優先度調整を推奨 (信頼度: {confidence:0.2f})",
                impact_score=self._calculate_priority_impact(task.priority, new_priority)
            ))
        
        # 2.0 工数見積もり推奨
        estimated_hours = self.effort_estimator.estimate_effort(task, complexity_score)
        current_estimate = task.time_estimated or 0
        
        if abs(estimated_hours - current_estimate) > 0.5:  # 30分以上の差
            recommendations.append(AIRecommendation(
                task_id=task_id,
                recommendation_type='effort_estimation',
                current_value=current_estimate,
                recommended_value=estimated_hours,
                confidence=0.8,
                reasoning=f"複雑度分析に基づく工数見積もり調整 (複雑度: {complexity_score:0.2f})",
                impact_score=abs(estimated_hours - current_estimate) / max(estimated_hours, 1)
            ))
        
        # 3.0 分解推奨 (大規模タスク用)
        if complexity_score > 3.0 and estimated_hours > 6.0:
            recommendations.append(AIRecommendation(
                task_id=task_id,
                recommendation_type='task_breakdown',
                current_value='single_task',
                recommended_value='multiple_subtasks',
                confidence=0.85,
                reasoning=f"高複雑度・大工数タスクの分解を推奨 (複雑度: {complexity_score:0.2f}, 工数: {estimated_hours:0.1f}h)",
                impact_score=complexity_score / 5.0
            ))
        
        # 4.0 スキルマッチング推奨
        required_skills = self._extract_required_skills(task)
        if required_skills:
            recommendations.append(AIRecommendation(
                task_id=task_id,
                recommendation_type='skill_matching',
                current_value=[],
                recommended_value=required_skills,
                confidence=0.75,
                reasoning=f"必要スキル: {', '.join(required_skills)}",
                impact_score=len(required_skills) / 10.0
            ))
        
        self.ai_stats['recommendations_generated'] += len(recommendations)
        logger.info(f"🤖 AI推奨生成: {task.title} → {len(recommendations)}件")
        
        return recommendations
    
    async def apply_recommendation(self, recommendation: AIRecommendation) -> bool:
        """AI推奨事項適用"""
        try:
            task = await self.unified_manager.db.get_task(recommendation.task_id)
            if not task:
                return False
            
            if recommendation.recommendation_type == 'priority_adjustment':
                new_priority = Priority(recommendation.recommended_value)
                await self.unified_manager.update_task_status(task.id, task.status)
                # 実際の優先度更新は unified_manager の機能拡張が必要
                
            elif recommendation.recommendation_type == 'effort_estimation':
                # 工数見積もり更新（実装は unified_manager 拡張が必要）
                pass
            
            self.ai_stats['recommendations_applied'] += 1
            self.optimization_history.append({
                'task_id': recommendation.task_id,
                'type': recommendation.recommendation_type,
                'applied_at': datetime.now(timezone.utc),
                'confidence': recommendation.confidence
            })
            
            logger.info(f"✅ AI推奨適用: {recommendation.recommendation_type} → {task.title}")
            return True
            
        except Exception as e:
            logger.error(f"❌ AI推奨適用失敗: {e}")
            return False
    
    async def learn_from_completion(self, task_id: str, actual_hours: float):
        """完了データからの学習"""
        if not self.learning_enabled:
            return
        
        try:
            task = await self.unified_manager.db.get_task(task_id)
            if not task:
                return
            
            # 工数見積もり学習
            estimated_hours = task.time_estimated or 0
            self.effort_estimator.learn_from_completion(task, actual_hours, estimated_hours)
            
            # 学習統計更新
            self.ai_stats['learning_sessions'] += 1
            
            # 精度計算
            if estimated_hours > 0:
                accuracy = min(actual_hours, estimated_hours) / max(actual_hours, estimated_hours)
                current_accuracy = self.ai_stats['optimization_accuracy']
                sessions = self.ai_stats['learning_sessions']
                
                # 移動平均で精度更新
                self.ai_stats['optimization_accuracy'] = (
                    (current_accuracy * (sessions - 1) + accuracy) / sessions
                )
            
            logger.info(f"🧠 AI学習完了: {task.title} (実績: {actual_hours}h, 見積: {estimated_hours}h)")
            
        except Exception as e:
            logger.error(f"❌ AI学習失敗: {e}")
    
    async def optimize_task_batch(self, task_ids: List[str]) -> Dict[str, List[AIRecommendation]]:
        """タスク一括最適化"""
        results = {}
        
        for task_id in task_ids:
            try:
                recommendations = await self.generate_recommendations(task_id)
                results[task_id] = recommendations
            except Exception as e:
                logger.error(f"❌ バッチ最適化失敗 {task_id}: {e}")
                results[task_id] = []
        
        return results
    
    def _calculate_dependency_impact(self, task: UnifiedTask) -> float:
        """依存関係影響度計算"""
        # 実装時は依存関係グラフ分析
        dependencies = getattr(task, 'dependencies', [])
        sub_tasks = getattr(task, 'sub_tasks', [])
        
        impact = len(dependencies) * 0.1 + len(sub_tasks) * 0.2
        return min(impact, 1.0)
    
    def _predict_completion_probability(
        self,
        task: UnifiedTask,
        complexity: float,
        effort: float
    ) -> float:
        """完了確率予測"""
        base_probability = 0.8
        
        # 複雑度による調整
        complexity_factor = max(0.3, 1.0 - (complexity - 1.0) * 0.15)
        
        # 工数による調整
        if effort > 8.0:
            effort_factor = 0.8
        elif effort < 1.0:
            effort_factor = 0.95
        else:
            effort_factor = 0.9
        
        # 優先度による調整
        priority_factor = {
            Priority.CRITICAL: 0.95,
            Priority.HIGH: 0.9,
            Priority.MEDIUM: 0.85,
            Priority.LOW: 0.7
        }[task.priority]
        
        probability = base_probability * complexity_factor * effort_factor * priority_factor
        return max(0.1, min(0.99, probability))
    
    def _extract_required_skills(self, task: UnifiedTask) -> List[str]:
        """必要スキル抽出"""
        text = f"{task.title} {task.description}".lower()
        
        skill_keywords = {
            'python': ['python', 'django', 'flask', 'fastapi'],
            'javascript': ['javascript', 'js', 'node', 'react', 'vue'],
            'database': ['database', 'sql', 'mysql', 'postgresql', 'mongodb'],
            'devops': ['docker', 'kubernetes', 'aws', 'ci/cd', 'deployment'],
            'frontend': ['frontend', 'ui', 'css', 'html', 'design'],
            'backend': ['backend', 'api', 'server', 'microservice'],
            'testing': ['test', 'testing', 'pytest', 'unittest'],
            'security': ['security', 'auth', 'encryption', 'vulnerability']
        }
        
        skills = [skill for skill, keywords in skill_keywords.items() 
                 if any(keyword in text for keyword in keywords)]
        
        return skills[:5]  # 最大5つまで
    
    def _build_task_context(self, task: UnifiedTask) -> Dict[str, Any]:
        """タスクコンテキスト構築"""
        return {
            'due_date': task.context.get('due_date'),
            'blocking_tasks': len(getattr(task, 'sub_tasks', [])),
            'dependent_tasks': len(getattr(task, 'dependencies', [])),
            'business_value': task.context.get('business_value', 'medium'),
            'system_impact': task.context.get('system_impact', 'low'),
            'stakeholder_urgency': task.context.get('stakeholder_urgency', 'normal'),
            'estimated_hours': task.time_estimated
        }
    
    def _calculate_priority_impact(self, current: Priority, new: Priority) -> float:
        """優先度変更影響度計算"""
        priority_values = {Priority.LOW: 1, Priority.MEDIUM: 2, Priority.HIGH: 3, Priority.CRITICAL: 4}
        current_val = priority_values[current]
        new_val = priority_values[new]
        
        return abs(new_val - current_val) / 4.0
    
    def get_ai_statistics(self) -> Dict[str, Any]:
        """AI統計取得"""
        recent_optimizations = list(self.optimization_history)[-10:]
        
        return {
            **self.ai_stats,
            'learning_enabled': self.learning_enabled,
            'auto_optimization': self.auto_optimization,
            'recent_optimizations': len(recent_optimizations),
            'average_confidence': statistics.mean([opt['confidence'] for opt in recent_optimizations]) \
                if recent_optimizations \
                else 0.0,
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
    
    def enable_learning(self):
        """学習機能有効化"""
        self.learning_enabled = True
        logger.info("🧠 AI学習機能有効化")
    
    def disable_learning(self):
        """学習機能無効化"""
        self.learning_enabled = False
        logger.info("⏸️ AI学習機能無効化")

# テスト実行用
async def main():
    """テスト実行"""
    # モック統一管理システム
    class MockUnifiedManager:
        """MockUnifiedManager - 管理システムクラス"""
        def __init__(self):
            """初期化メソッド"""
            self.tasks = {}
        
        async def create_task(self, **kwargs):
            """task作成メソッド"""
            return "ai-test-task"
        
        @property
        def db(self):
            """dbメソッド"""
            return type('MockDB', (), {
                'get_task': lambda self, task_id: UnifiedTask(
                    id=task_id,
                    title="AI最適化テストタスク",
                    description="複雑なシステム統合とアーキテクチャ設計が必要な大規模プロジェクト",
                    task_type=TaskType.PROJECT_TASK,
                    priority=Priority.MEDIUM,
                    time_estimated=4.0,
                    context={'business_value': 'high', 'system_impact': 'medium'}
                )
            })()
    
    # テスト実行
    manager = MockUnifiedManager()
    ai_engine = EitmsAiEngine(manager)
    
    # タスク分析
    task_id = "ai-test-task"
    metrics = await ai_engine.analyze_task(task_id)
    logger.info(f"🎯 分析結果: 複雑度={metrics.complexity_score:0.2f}, 工数={metrics.estimated_hours:0.1f}h")
    
    # AI推奨生成
    recommendations = await ai_engine.generate_recommendations(task_id)
    logger.info(f"🤖 AI推奨: {len(recommendations)}件生成")
    
    for rec in recommendations:
        logger.info(f"  - {rec.recommendation_type}: {rec.reasoning}")
    
    # 統計確認
    stats = ai_engine.get_ai_statistics()
    logger.info(f"📊 AI統計: {stats['recommendations_generated']}件推奨生成")

if __name__ == "__main__":
    asyncio.run(main())