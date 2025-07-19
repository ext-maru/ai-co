#!/usr/bin/env python3
"""
実行時間予測エンジン - Task Sage統合コンポーネント
Created: 2025-07-17
Author: Claude Elder
"""

import asyncio
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from collections import defaultdict
from dataclasses import dataclass
import logging

# プロジェクトルートインポート
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.four_sages.task.task_sage import TaskEntry, TaskType, TaskPriority
from libs.tracking.unified_tracking_db import UnifiedTrackingDB
from core.lightweight_logger import get_logger

logger = get_logger("execution_time_predictor")

@dataclass
class TimeFeatures:
    """時間予測のための特徴量"""
    task_type: str
    priority: str
    dependency_count: int
    resource_count: int
    has_due_date: bool
    description_length: int
    tag_count: int
    estimated_hours: float
    historical_avg_time: float
    similar_task_avg_time: float

class PredictionModel:
    """タスクタイプ別の予測モデル"""
    
    def __init__(self, task_type: TaskType):
        self.task_type = task_type
        self.coefficients = {
            'base_time': 300.0,  # 5分（秒）
            'dependency_factor': 60.0,  # 依存関係1つあたり1分追加
            'resource_factor': 30.0,  # リソース1つあたり30秒追加
            'priority_multiplier': {
                'critical': 0.8,  # 優先度が高いほど効率的に実行される傾向
                'high': 0.9,
                'medium': 1.0,
                'low': 1.1,
                'deferred': 1.2
            },
            'description_length_factor': 0.1,  # 説明文字数100文字あたり10秒
            'tag_factor': 20.0,  # タグ1つあたり20秒
            'historical_weight': 0.7,  # 履歴データの重み
            'estimation_weight': 0.3  # 見積もりの重み
        }
        self.prediction_history = []
        self.mape_history = []  # Mean Absolute Percentage Error
    
    def predict(self, features: TimeFeatures) -> float:
        """実行時間を予測（秒）"""
        # 基本時間
        predicted_time = self.coefficients['base_time']
        
        # 依存関係による調整
        predicted_time += features.dependency_count * self.coefficients['dependency_factor']
        
        # リソースによる調整
        predicted_time += features.resource_count * self.coefficients['resource_factor']
        
        # 優先度による調整
        priority_mult = self.coefficients['priority_multiplier'].get(features.priority, 1.0)
        predicted_time *= priority_mult
        
        # 説明文の長さによる調整
        predicted_time += (features.description_length / 100) * self.coefficients['description_length_factor']
        
        # タグによる調整
        predicted_time += features.tag_count * self.coefficients['tag_factor']
        
        # 履歴データとの統合
        if features.historical_avg_time > 0:
            historical_prediction = features.historical_avg_time
            predicted_time = (predicted_time * (1 - self.coefficients['historical_weight']) +
                            historical_prediction * self.coefficients['historical_weight'])
        
        # 見積もり時間との統合
        if features.estimated_hours > 0:
            estimated_seconds = features.estimated_hours * 3600
            predicted_time = (predicted_time * (1 - self.coefficients['estimation_weight']) +
                            estimated_seconds * self.coefficients['estimation_weight'])
        
        # 最小値・最大値の制限
        predicted_time = max(60.0, min(86400.0, predicted_time))  # 1分〜24時間
        
        return predicted_time
    
    def get_confidence_interval(self, predicted_time: float) -> Tuple[float, float]:
        """信頼区間を計算（95%）"""
        # 過去の予測誤差から標準偏差を計算
        if len(self.mape_history) >= 5:
            error_std = np.std(self.mape_history)
            margin = predicted_time * error_std * 1.96  # 95%信頼区間
        else:
            # データ不足時はデフォルトの30%マージン
            margin = predicted_time * 0.3
        
        lower_bound = max(60.0, predicted_time - margin)
        upper_bound = min(86400.0, predicted_time + margin)
        
        return lower_bound, upper_bound
    
    def update_model(self, features: TimeFeatures, actual_time: float, predicted_time: float):
        """実際の実行時間に基づいてモデルを更新"""
        # 予測誤差を記録
        if actual_time > 0:
            mape = abs(predicted_time - actual_time) / actual_time
            self.mape_history.append(mape)
            
            # 最新100件のみ保持
            if len(self.mape_history) > 100:
                self.mape_history.pop(0)
        
        # 予測履歴を記録
        self.prediction_history.append({
            'features': features,
            'predicted': predicted_time,
            'actual': actual_time,
            'timestamp': datetime.now()
        })
        
        # 係数の調整（簡易的な勾配降下法）
        learning_rate = 0.01
        error = actual_time - predicted_time
        
        # 各係数を誤差に基づいて調整
        if features.dependency_count > 0:
            self.coefficients['dependency_factor'] += (
                learning_rate * error * features.dependency_count / actual_time
            )
        
        if features.resource_count > 0:
            self.coefficients['resource_factor'] += (
                learning_rate * error * features.resource_count / actual_time
            )

class ExecutionTimePredictor:
    """実行時間予測エンジン"""
    
    def __init__(self, tracking_db: UnifiedTrackingDB):
        self.tracking_db = tracking_db
        self.prediction_models = {}
        self.feature_cache = {}
        self.cache_ttl = 600  # 10分
        
        logger.info("⏱️ ExecutionTimePredictor initialized")
    
    async def predict_execution_time(self, task: TaskEntry) -> Tuple[float, Tuple[float, float]]:
        """タスクの実行時間を予測
        
        Returns:
            (predicted_time, (lower_bound, upper_bound))
        """
        try:
            # キャッシュチェック
            cache_key = f"{task.id}_{task.updated_at.isoformat()}"
            if cache_key in self.feature_cache:
                cached_data = self.feature_cache[cache_key]
                if datetime.now() - cached_data['timestamp'] < timedelta(seconds=self.cache_ttl):
                    return cached_data['prediction'], cached_data['confidence_interval']
            
            # タスクタイプ別のモデル取得
            model = await self._get_or_create_model(task.task_type)
            
            # 特徴量抽出
            features = await self._extract_features(task)
            
            # 予測実行
            predicted_time = model.predict(features)
            confidence_interval = model.get_confidence_interval(predicted_time)
            
            # キャッシュに保存
            self.feature_cache[cache_key] = {
                'prediction': predicted_time,
                'confidence_interval': confidence_interval,
                'timestamp': datetime.now()
            }
            
            logger.info(f"Predicted execution time for task {task.id}: "
                       f"{predicted_time:.0f}s ({confidence_interval[0]:.0f}s - {confidence_interval[1]:.0f}s)")
            
            return predicted_time, confidence_interval
            
        except Exception as e:
            logger.error(f"Failed to predict execution time: {e}")
            # エラー時はデフォルト値を返す
            default_time = 600.0  # 10分
            return default_time, (300.0, 1800.0)  # 5分〜30分
    
    async def _get_or_create_model(self, task_type: TaskType) -> PredictionModel:
        """タスクタイプ別のモデルを取得または作成"""
        if task_type not in self.prediction_models:
            self.prediction_models[task_type] = PredictionModel(task_type)
            
            # 履歴データからモデルを初期化
            await self._initialize_model_from_history(task_type)
        
        return self.prediction_models[task_type]
    
    async def _initialize_model_from_history(self, task_type: TaskType):
        """履歴データからモデルを初期化"""
        try:
            # 過去30日のタスクデータを取得
            tasks = self.tracking_db.search_tasks(limit=1000)
            
            # タスクタイプ別の実行時間を集計
            execution_times = []
            for task_data in tasks:
                if task_data.get('status') == 'completed' and task_data.get('execution_time_seconds'):
                    # メタデータからタスクタイプを取得
                    metadata = json.loads(task_data.get('metadata', '{}'))
                    if metadata.get('task_type') == task_type.value:
                        execution_times.append(task_data['execution_time_seconds'])
            
            # 統計情報を計算
            if execution_times:
                model = self.prediction_models[task_type]
                avg_time = np.mean(execution_times)
                std_time = np.std(execution_times)
                
                # モデルの基本時間を調整
                model.coefficients['base_time'] = avg_time
                
                logger.info(f"Initialized model for {task_type.value} with "
                           f"avg_time={avg_time:.0f}s, std={std_time:.0f}s")
                
        except Exception as e:
            logger.error(f"Failed to initialize model from history: {e}")
    
    async def _extract_features(self, task: TaskEntry) -> TimeFeatures:
        """タスクから特徴量を抽出"""
        # 履歴データから類似タスクの平均時間を取得
        historical_avg_time = await self._get_historical_avg_time(task.task_type)
        similar_task_avg_time = await self._get_similar_task_avg_time(task)
        
        # 見積もり時間（時間）
        estimated_hours = 0.0
        if task.estimated_duration:
            estimated_hours = task.estimated_duration.total_seconds() / 3600
        
        return TimeFeatures(
            task_type=task.task_type.value,
            priority=task.priority.value,
            dependency_count=len(task.dependencies),
            resource_count=len(task.resources),
            has_due_date=task.due_date is not None,
            description_length=len(task.description),
            tag_count=len(task.tags),
            estimated_hours=estimated_hours,
            historical_avg_time=historical_avg_time,
            similar_task_avg_time=similar_task_avg_time
        )
    
    async def _get_historical_avg_time(self, task_type: TaskType) -> float:
        """タスクタイプの過去の平均実行時間を取得"""
        try:
            metrics_summary = self.tracking_db.get_metrics_summary(days=30)
            avg_execution_time = metrics_summary.get('stats', {}).get('avg_execution_time', 0)
            return avg_execution_time if avg_execution_time > 0 else 0.0
        except Exception as e:
            logger.error(f"Failed to get historical avg time: {e}")
            return 0.0
    
    async def _get_similar_task_avg_time(self, task: TaskEntry) -> float:
        """類似タスクの平均実行時間を取得"""
        try:
            # タグベースの類似性で検索
            similar_times = []
            
            tasks = self.tracking_db.search_tasks(limit=100)
            for task_data in tasks:
                if task_data.get('status') == 'completed' and task_data.get('execution_time_seconds'):
                    metadata = json.loads(task_data.get('metadata', '{}'))
                    task_tags = set(metadata.get('tags', []))
                    
                    # タグの重複をチェック
                    if task_tags.intersection(task.tags):
                        similar_times.append(task_data['execution_time_seconds'])
            
            return np.mean(similar_times) if similar_times else 0.0
            
        except Exception as e:
            logger.error(f"Failed to get similar task avg time: {e}")
            return 0.0
    
    async def update_prediction(self, task_id: str, actual_execution_time: float):
        """実際の実行時間でモデルを更新"""
        try:
            # タスクデータを取得
            task_data = self.tracking_db.get_task(task_id)
            if not task_data:
                return
            
            metadata = json.loads(task_data.get('metadata', '{}'))
            task_type_str = metadata.get('task_type')
            if not task_type_str:
                return
            
            task_type = TaskType(task_type_str)
            model = self.prediction_models.get(task_type)
            if not model:
                return
            
            # 特徴量を再構築（簡易版）
            features = TimeFeatures(
                task_type=task_type_str,
                priority=metadata.get('priority', 'medium'),
                dependency_count=metadata.get('dependency_count', 0),
                resource_count=metadata.get('resource_count', 0),
                has_due_date=metadata.get('has_due_date', False),
                description_length=metadata.get('description_length', 0),
                tag_count=len(metadata.get('tags', [])),
                estimated_hours=metadata.get('estimated_hours', 0),
                historical_avg_time=0,  # 更新時は使用しない
                similar_task_avg_time=0
            )
            
            # 予測値を取得（キャッシュから）
            cache_key = f"{task_id}_"
            predicted_time = 600.0  # デフォルト
            for key in self.feature_cache:
                if key.startswith(cache_key):
                    predicted_time = self.feature_cache[key]['prediction']
                    break
            
            # モデルを更新
            model.update_model(features, actual_execution_time, predicted_time)
            
            logger.info(f"Updated prediction model for task {task_id}, "
                       f"actual: {actual_execution_time:.0f}s, predicted: {predicted_time:.0f}s")
            
        except Exception as e:
            logger.error(f"Failed to update prediction: {e}")
    
    def get_model_accuracy(self, task_type: Optional[TaskType] = None) -> Dict[str, Any]:
        """モデルの精度メトリクスを取得"""
        try:
            if task_type and task_type in self.prediction_models:
                model = self.prediction_models[task_type]
                if model.mape_history:
                    return {
                        'task_type': task_type.value,
                        'mape': np.mean(model.mape_history),
                        'mape_std': np.std(model.mape_history),
                        'sample_size': len(model.mape_history)
                    }
            
            # 全モデルの精度を集計
            all_accuracy = {}
            for t_type, model in self.prediction_models.items():
                if model.mape_history:
                    all_accuracy[t_type.value] = {
                        'mape': np.mean(model.mape_history),
                        'mape_std': np.std(model.mape_history),
                        'sample_size': len(model.mape_history)
                    }
            
            return all_accuracy
            
        except Exception as e:
            logger.error(f"Failed to get model accuracy: {e}")
            return {}