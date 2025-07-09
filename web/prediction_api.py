#!/usr/bin/env python3
"""
予測分析 API
機械学習モデルを活用した予測・最適化
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import sys
import numpy as np
import pickle
import joblib
from collections import deque

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, Blueprint, jsonify, request
from libs.ml_models import ModelRegistry, TimeSeriesPredictor, AnomalyDetector, LoadPredictor
from libs.model_training import ModelTrainer, ModelEvaluator

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Blueprint作成
prediction_api = Blueprint('prediction_api', __name__, url_prefix='/api/predict')

class PredictionEngine:
    """予測エンジン"""
    
    def __init__(self):
        # モデルレジストリ
        self.model_registry = ModelRegistry()
        
        # モデルトレーナー
        self.model_trainer = ModelTrainer()
        
        # モデル評価器
        self.model_evaluator = ModelEvaluator()
        
        # 予測キャッシュ
        self.prediction_cache = {}
        self.cache_ttl = 300  # 5分
        
        # 予測履歴
        self.prediction_history = deque(maxlen=1000)
        
        # モデル初期化
        self._initialize_models()
    
    def predict_load(self, resource_type: str,
                    horizon_minutes: int = 60,
                    confidence_level: float = 0.95) -> Dict[str, Any]:
        """負荷予測"""
        try:
            # キャッシュチェック
            cache_key = f"load_{resource_type}_{horizon_minutes}"
            if cache_key in self.prediction_cache:
                cached, timestamp = self.prediction_cache[cache_key]
                if (datetime.now() - timestamp).seconds < self.cache_ttl:
                    return cached
            
            # モデル取得
            model = self.model_registry.get_model(f"load_predictor_{resource_type}")
            if not model:
                # モデルが存在しない場合は新規作成
                model = LoadPredictor(resource_type)
                self.model_registry.register_model(f"load_predictor_{resource_type}", model)
            
            # 予測実行
            predictions = model.predict(horizon_minutes)
            
            # 信頼区間計算
            confidence_intervals = model.get_confidence_intervals(
                predictions, confidence_level
            )
            
            # 最適化提案生成
            recommendations = self._generate_load_recommendations(
                resource_type, predictions
            )
            
            result = {
                "resource_type": resource_type,
                "horizon_minutes": horizon_minutes,
                "predictions": {
                    "timestamps": [
                        (datetime.now() + timedelta(minutes=i)).isoformat()
                        for i in range(0, horizon_minutes, 5)
                    ],
                    "values": predictions,
                    "confidence_intervals": confidence_intervals
                },
                "current_load": model.get_current_load(),
                "peak_prediction": {
                    "value": float(np.max(predictions)),
                    "time": (datetime.now() + timedelta(
                        minutes=int(np.argmax(predictions) * 5)
                    )).isoformat()
                },
                "recommendations": recommendations,
                "model_accuracy": model.get_accuracy_metrics()
            }
            
            # キャッシュ保存
            self.prediction_cache[cache_key] = (result, datetime.now())
            
            # 履歴記録
            self._record_prediction("load", result)
            
            return result
            
        except Exception as e:
            logger.error(f"負荷予測エラー: {e}")
            return {"error": str(e)}
    
    def predict_incidents(self, time_window_hours: int = 24,
                         severity_threshold: str = "all") -> Dict[str, Any]:
        """インシデント予測"""
        try:
            # インシデント予測モデル取得
            model = self.model_registry.get_model("incident_predictor")
            if not model:
                # デフォルトモデル作成
                model = self._create_incident_predictor()
                self.model_registry.register_model("incident_predictor", model)
            
            # 現在の状態分析
            current_state = self._analyze_current_state()
            
            # 予測実行
            incident_probabilities = model.predict_incidents(
                current_state, time_window_hours
            )
            
            # インシデントタイプ別予測
            predictions_by_type = {
                "system_failure": self._predict_system_failure_probability(current_state),
                "performance_degradation": self._predict_performance_degradation(current_state),
                "security_breach": self._predict_security_breach_probability(current_state),
                "data_corruption": self._predict_data_corruption_probability(current_state)
            }
            
            # リスクスコア計算
            risk_scores = self._calculate_risk_scores(
                incident_probabilities, predictions_by_type
            )
            
            # 予防措置提案
            preventive_actions = self._generate_preventive_actions(
                risk_scores, predictions_by_type
            )
            
            result = {
                "time_window_hours": time_window_hours,
                "overall_risk": self._calculate_overall_risk(risk_scores),
                "incident_probabilities": incident_probabilities,
                "predictions_by_type": predictions_by_type,
                "risk_scores": risk_scores,
                "preventive_actions": preventive_actions,
                "model_confidence": model.get_confidence_score(),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            # 履歴記録
            self._record_prediction("incident", result)
            
            return result
            
        except Exception as e:
            logger.error(f"インシデント予測エラー: {e}")
            return {"error": str(e)}
    
    def optimize_resources(self, optimization_goal: str = "cost",
                          constraints: Dict[str, Any] = None) -> Dict[str, Any]:
        """リソース最適化提案"""
        try:
            # 現在のリソース使用状況
            current_usage = self._get_current_resource_usage()
            
            # 予測データ取得
            load_predictions = {
                "cpu": self.predict_load("cpu", 1440)["predictions"]["values"],  # 24時間
                "memory": self.predict_load("memory", 1440)["predictions"]["values"],
                "disk": self.predict_load("disk", 1440)["predictions"]["values"],
                "network": self.predict_load("network", 1440)["predictions"]["values"]
            }
            
            # 最適化実行
            optimization_result = self._run_optimization(
                current_usage, load_predictions, optimization_goal, constraints
            )
            
            # コスト影響分析
            cost_analysis = self._analyze_cost_impact(
                current_usage, optimization_result["recommended_allocation"]
            )
            
            # 実装計画生成
            implementation_plan = self._generate_implementation_plan(
                optimization_result["recommended_allocation"]
            )
            
            result = {
                "optimization_goal": optimization_goal,
                "current_allocation": current_usage,
                "recommended_allocation": optimization_result["recommended_allocation"],
                "expected_improvements": {
                    "cost_reduction": f"{cost_analysis['savings_percentage']:.1f}%",
                    "performance_gain": f"{optimization_result['performance_improvement']:.1f}%",
                    "efficiency_increase": f"{optimization_result['efficiency_gain']:.1f}%"
                },
                "cost_analysis": cost_analysis,
                "implementation_plan": implementation_plan,
                "constraints_applied": constraints or {},
                "optimization_timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"リソース最適化エラー: {e}")
            return {"error": str(e)}
    
    def train_model(self, model_type: str,
                   training_data: Dict[str, Any],
                   hyperparameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """モデル学習"""
        try:
            # 学習データ準備
            X, y = self.model_trainer.prepare_training_data(training_data)
            
            # モデル作成・学習
            model = self.model_trainer.train_model(
                model_type, X, y, hyperparameters
            )
            
            # モデル評価
            evaluation_results = self.model_evaluator.evaluate_model(
                model, X, y
            )
            
            # モデル登録
            model_id = f"{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.model_registry.register_model(model_id, model)
            
            # A/Bテスト設定（必要に応じて）
            if evaluation_results["performance"]["accuracy"] > 0.8:
                self._setup_ab_test(model_id, model_type)
            
            return {
                "success": True,
                "model_id": model_id,
                "model_type": model_type,
                "evaluation_results": evaluation_results,
                "training_completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"モデル学習エラー: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_model_performance(self, model_id: str = None) -> Dict[str, Any]:
        """モデルパフォーマンス取得"""
        try:
            if model_id:
                # 特定モデルのパフォーマンス
                model = self.model_registry.get_model(model_id)
                if not model:
                    return {"error": f"Model {model_id} not found"}
                
                return {
                    "model_id": model_id,
                    "performance": model.get_performance_metrics(),
                    "last_updated": model.get_last_update_time()
                }
            else:
                # 全モデルのパフォーマンス
                all_models = self.model_registry.list_models()
                performances = {}
                
                for mid in all_models:
                    model = self.model_registry.get_model(mid)
                    performances[mid] = {
                        "accuracy": model.get_accuracy_metrics(),
                        "predictions_count": model.get_prediction_count(),
                        "last_used": model.get_last_used_time()
                    }
                
                return {
                    "models": performances,
                    "total_models": len(all_models),
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"モデルパフォーマンス取得エラー: {e}")
            return {"error": str(e)}
    
    # プライベートメソッド
    def _initialize_models(self):
        """初期モデル設定"""
        # 基本的な予測モデルを事前作成
        models = {
            "time_series_cpu": TimeSeriesPredictor("cpu"),
            "time_series_memory": TimeSeriesPredictor("memory"),
            "anomaly_detector": AnomalyDetector(),
            "load_predictor_cpu": LoadPredictor("cpu"),
            "load_predictor_memory": LoadPredictor("memory")
        }
        
        for model_id, model in models.items():
            self.model_registry.register_model(model_id, model)
        
        logger.info(f"初期モデル {len(models)} 個を登録しました")
    
    def _generate_load_recommendations(self, resource_type: str,
                                     predictions: List[float]) -> List[Dict[str, Any]]:
        """負荷予測に基づく推奨事項生成"""
        recommendations = []
        
        # ピーク検出
        peak_value = np.max(predictions)
        avg_value = np.mean(predictions)
        
        if peak_value > 80:
            recommendations.append({
                "priority": "high",
                "action": "scale_up",
                "reason": f"{resource_type}使用率がピーク時に{peak_value:.1f}%に達する見込み",
                "timing": "ピーク30分前",
                "expected_benefit": "サービス停止の回避"
            })
        
        if avg_value > 70:
            recommendations.append({
                "priority": "medium",
                "action": "optimize_queries",
                "reason": f"{resource_type}の平均使用率が高い（{avg_value:.1f}%）",
                "timing": "今すぐ",
                "expected_benefit": "15-25%の使用率削減"
            })
        
        # 変動が大きい場合
        std_value = np.std(predictions)
        if std_value > 20:
            recommendations.append({
                "priority": "medium",
                "action": "implement_caching",
                "reason": f"{resource_type}使用率の変動が大きい（標準偏差: {std_value:.1f}）",
                "timing": "今週中",
                "expected_benefit": "負荷の平準化"
            })
        
        return recommendations
    
    def _create_incident_predictor(self):
        """インシデント予測モデル作成"""
        # 簡易的なインシデント予測モデル
        class SimpleIncidentPredictor:
            def predict_incidents(self, state, hours):
                # モック実装
                base_prob = 0.05
                
                # 状態に基づく調整
                if state.get("cpu_usage", 0) > 80:
                    base_prob += 0.1
                if state.get("memory_usage", 0) > 85:
                    base_prob += 0.15
                if state.get("error_rate", 0) > 0.05:
                    base_prob += 0.2
                
                # 時間帯による調整
                probs = []
                for hour in range(hours):
                    hour_prob = base_prob * (1 + 0.1 * np.sin(2 * np.pi * hour / 24))
                    probs.append(min(hour_prob, 1.0))
                
                return probs
            
            def get_confidence_score(self):
                return 0.85
        
        return SimpleIncidentPredictor()
    
    def _analyze_current_state(self) -> Dict[str, Any]:
        """現在の状態分析"""
        # モック実装
        return {
            "cpu_usage": np.random.uniform(40, 80),
            "memory_usage": np.random.uniform(50, 85),
            "disk_usage": np.random.uniform(30, 70),
            "network_usage": np.random.uniform(20, 60),
            "error_rate": np.random.uniform(0, 0.05),
            "response_time": np.random.uniform(50, 200),
            "active_connections": np.random.randint(100, 500)
        }
    
    def _predict_system_failure_probability(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """システム障害確率予測"""
        # 簡易予測ロジック
        risk_factors = 0
        
        if state["cpu_usage"] > 90:
            risk_factors += 2
        elif state["cpu_usage"] > 80:
            risk_factors += 1
        
        if state["memory_usage"] > 90:
            risk_factors += 2
        elif state["memory_usage"] > 85:
            risk_factors += 1
        
        if state["error_rate"] > 0.1:
            risk_factors += 3
        elif state["error_rate"] > 0.05:
            risk_factors += 2
        
        probability = min(risk_factors * 0.1, 0.9)
        
        return {
            "probability": probability,
            "risk_level": "high" if probability > 0.5 else "medium" if probability > 0.2 else "low",
            "main_factors": self._identify_main_factors(state)
        }
    
    def _predict_performance_degradation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """パフォーマンス劣化予測"""
        degradation_score = 0
        
        # レスポンスタイムによる評価
        if state["response_time"] > 500:
            degradation_score += 3
        elif state["response_time"] > 200:
            degradation_score += 2
        elif state["response_time"] > 100:
            degradation_score += 1
        
        # リソース使用率による評価
        resource_pressure = (
            state["cpu_usage"] * 0.3 +
            state["memory_usage"] * 0.3 +
            state["network_usage"] * 0.4
        ) / 100
        
        degradation_score += resource_pressure * 5
        
        probability = min(degradation_score * 0.15, 0.95)
        
        return {
            "probability": probability,
            "expected_impact": f"{probability * 50:.1f}% レスポンスタイム増加",
            "affected_services": ["API", "Database", "Cache"]
        }
    
    def _predict_security_breach_probability(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """セキュリティ侵害確率予測"""
        # 簡易的なセキュリティリスク評価
        base_probability = 0.01
        
        # 異常な接続数
        if state["active_connections"] > 1000:
            base_probability += 0.05
        
        # エラー率が高い（攻撃の可能性）
        if state["error_rate"] > 0.1:
            base_probability += 0.03
        
        return {
            "probability": base_probability,
            "threat_types": ["DDoS", "Brute Force", "SQL Injection"],
            "recommended_actions": ["IP制限強化", "WAF設定見直し", "ログ監視強化"]
        }
    
    def _predict_data_corruption_probability(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """データ破損確率予測"""
        corruption_risk = 0.005  # ベースリスク
        
        # ディスク使用率が高い
        if state["disk_usage"] > 90:
            corruption_risk += 0.02
        
        # エラー率が高い
        if state["error_rate"] > 0.05:
            corruption_risk += 0.01
        
        return {
            "probability": corruption_risk,
            "high_risk_areas": ["Database", "File Storage", "Cache"],
            "backup_status": "最新バックアップ: 2時間前"
        }
    
    def _identify_main_factors(self, state: Dict[str, Any]) -> List[str]:
        """主要リスク要因特定"""
        factors = []
        
        if state["cpu_usage"] > 80:
            factors.append(f"高CPU使用率 ({state['cpu_usage']:.1f}%)")
        if state["memory_usage"] > 85:
            factors.append(f"高メモリ使用率 ({state['memory_usage']:.1f}%)")
        if state["error_rate"] > 0.05:
            factors.append(f"高エラー率 ({state['error_rate']:.3f})")
        if state["response_time"] > 200:
            factors.append(f"レスポンス遅延 ({state['response_time']:.0f}ms)")
        
        return factors
    
    def _calculate_risk_scores(self, probabilities: List[float],
                              predictions_by_type: Dict[str, Dict]) -> Dict[str, float]:
        """リスクスコア計算"""
        scores = {}
        
        # タイプ別重み付け
        weights = {
            "system_failure": 1.0,
            "performance_degradation": 0.7,
            "security_breach": 0.9,
            "data_corruption": 0.8
        }
        
        for incident_type, prediction in predictions_by_type.items():
            base_score = prediction["probability"] * 100
            weighted_score = base_score * weights.get(incident_type, 1.0)
            scores[incident_type] = min(weighted_score, 100)
        
        return scores
    
    def _calculate_overall_risk(self, risk_scores: Dict[str, float]) -> Dict[str, Any]:
        """総合リスク計算"""
        if not risk_scores:
            return {"level": "low", "score": 0}
        
        max_score = max(risk_scores.values())
        avg_score = sum(risk_scores.values()) / len(risk_scores)
        
        if max_score > 70 or avg_score > 50:
            level = "high"
        elif max_score > 40 or avg_score > 30:
            level = "medium"
        else:
            level = "low"
        
        return {
            "level": level,
            "score": avg_score,
            "max_risk": max(risk_scores.items(), key=lambda x: x[1])
        }
    
    def _generate_preventive_actions(self, risk_scores: Dict[str, float],
                                   predictions: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """予防措置生成"""
        actions = []
        
        for incident_type, score in risk_scores.items():
            if score > 50:
                if incident_type == "system_failure":
                    actions.append({
                        "type": "immediate",
                        "action": "リソーススケーリング",
                        "target": "計算リソース",
                        "urgency": "high",
                        "automated": True
                    })
                elif incident_type == "performance_degradation":
                    actions.append({
                        "type": "optimization",
                        "action": "クエリ最適化",
                        "target": "データベース",
                        "urgency": "medium",
                        "automated": False
                    })
                elif incident_type == "security_breach":
                    actions.append({
                        "type": "security",
                        "action": "セキュリティルール強化",
                        "target": "ファイアウォール",
                        "urgency": "high",
                        "automated": True
                    })
        
        return sorted(actions, key=lambda x: 
                     {"high": 0, "medium": 1, "low": 2}.get(x["urgency"], 3))
    
    def _get_current_resource_usage(self) -> Dict[str, float]:
        """現在のリソース使用状況取得"""
        return {
            "cpu": np.random.uniform(40, 70),
            "memory": np.random.uniform(50, 80),
            "disk": np.random.uniform(30, 60),
            "network": np.random.uniform(20, 50),
            "instances": 4
        }
    
    def _run_optimization(self, current: Dict[str, float],
                         predictions: Dict[str, List[float]],
                         goal: str,
                         constraints: Dict[str, Any]) -> Dict[str, Any]:
        """最適化実行"""
        # 簡易最適化ロジック
        recommended = current.copy()
        
        if goal == "cost":
            # コスト最適化: 予測ピークに合わせてリソース調整
            for resource, pred_values in predictions.items():
                peak = np.percentile(pred_values, 95)  # 95パーセンタイル
                recommended[resource] = min(peak * 1.1, 100)  # 10%マージン
        
        elif goal == "performance":
            # パフォーマンス最適化: 余裕を持たせる
            for resource, pred_values in predictions.items():
                peak = np.max(pred_values)
                recommended[resource] = min(peak * 1.3, 100)  # 30%マージン
        
        # 制約適用
        if constraints:
            if "max_cost" in constraints:
                # コスト上限制約
                total_cost = sum(recommended.values())
                if total_cost > constraints["max_cost"]:
                    scale = constraints["max_cost"] / total_cost
                    for k in recommended:
                        recommended[k] *= scale
        
        # 改善率計算
        performance_improvement = np.mean([
            (recommended[k] - current[k]) / current[k] * 100
            for k in current if k != "instances"
        ])
        
        efficiency_gain = (
            sum(current.values()) / sum(recommended.values()) - 1
        ) * 100
        
        return {
            "recommended_allocation": recommended,
            "performance_improvement": max(performance_improvement, 0),
            "efficiency_gain": max(efficiency_gain, 0)
        }
    
    def _analyze_cost_impact(self, current: Dict[str, float],
                           recommended: Dict[str, float]) -> Dict[str, Any]:
        """コスト影響分析"""
        # 仮想的なコスト計算
        cost_per_unit = {
            "cpu": 0.05,
            "memory": 0.02,
            "disk": 0.01,
            "network": 0.03,
            "instances": 10.0
        }
        
        current_cost = sum(
            current.get(k, 0) * v for k, v in cost_per_unit.items()
        )
        
        recommended_cost = sum(
            recommended.get(k, 0) * v for k, v in cost_per_unit.items()
        )
        
        savings = current_cost - recommended_cost
        savings_percentage = (savings / current_cost * 100) if current_cost > 0 else 0
        
        return {
            "current_monthly_cost": f"${current_cost * 720:.2f}",  # 月間コスト
            "projected_monthly_cost": f"${recommended_cost * 720:.2f}",
            "monthly_savings": f"${savings * 720:.2f}",
            "savings_percentage": savings_percentage,
            "roi_months": 3 if savings > 0 else None
        }
    
    def _generate_implementation_plan(self, recommended: Dict[str, float]) -> List[Dict[str, Any]]:
        """実装計画生成"""
        plan = []
        
        # フェーズ1: 即時対応
        plan.append({
            "phase": 1,
            "name": "即時最適化",
            "duration": "1-2時間",
            "actions": [
                "自動スケーリング設定の調整",
                "キャッシュ設定の最適化",
                "不要なプロセスの停止"
            ],
            "expected_impact": "10-15%改善"
        })
        
        # フェーズ2: 短期対応
        plan.append({
            "phase": 2,
            "name": "短期最適化",
            "duration": "1-2日",
            "actions": [
                "インスタンスタイプの変更",
                "ロードバランサー設定の調整",
                "データベースインデックスの最適化"
            ],
            "expected_impact": "20-30%改善"
        })
        
        # フェーズ3: 中期対応
        plan.append({
            "phase": 3,
            "name": "アーキテクチャ改善",
            "duration": "1-2週間",
            "actions": [
                "マイクロサービス化の推進",
                "コンテナ化とオーケストレーション",
                "サーバーレス化の検討"
            ],
            "expected_impact": "40-50%改善"
        })
        
        return plan
    
    def _setup_ab_test(self, model_id: str, model_type: str):
        """A/Bテスト設定"""
        logger.info(f"A/Bテスト設定: {model_id} (タイプ: {model_type})")
        # 実際の実装では A/B テストフレームワークと連携
    
    def _record_prediction(self, prediction_type: str, result: Dict[str, Any]):
        """予測履歴記録"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "type": prediction_type,
            "result_summary": {
                "success": "error" not in result,
                "key_metrics": self._extract_key_metrics(result)
            }
        }
        self.prediction_history.append(record)

    def _extract_key_metrics(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """主要メトリクス抽出"""
        metrics = {}
        
        if "predictions" in result:
            metrics["prediction_count"] = len(result["predictions"].get("values", []))
        if "overall_risk" in result:
            metrics["risk_level"] = result["overall_risk"].get("level")
        if "expected_improvements" in result:
            metrics["cost_reduction"] = result["expected_improvements"].get("cost_reduction")
        
        return metrics

# エンジンインスタンス
prediction_engine = PredictionEngine()

# API エンドポイント

@prediction_api.route('/load/<resource_type>')
def predict_load(resource_type):
    """負荷予測エンドポイント"""
    try:
        horizon = int(request.args.get('horizon_minutes', 60))
        confidence = float(request.args.get('confidence', 0.95))
        
        result = prediction_engine.predict_load(
            resource_type, horizon, confidence
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@prediction_api.route('/incidents')
def predict_incidents():
    """インシデント予測エンドポイント"""
    try:
        hours = int(request.args.get('hours', 24))
        severity = request.args.get('severity', 'all')
        
        result = prediction_engine.predict_incidents(hours, severity)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@prediction_api.route('/optimize')
def optimize_resources():
    """リソース最適化エンドポイント"""
    try:
        goal = request.args.get('goal', 'cost')
        
        # 制約条件
        constraints = {}
        if request.args.get('max_cost'):
            constraints['max_cost'] = float(request.args.get('max_cost'))
        if request.args.get('min_performance'):
            constraints['min_performance'] = float(request.args.get('min_performance'))
        
        result = prediction_engine.optimize_resources(goal, constraints)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@prediction_api.route('/train', methods=['POST'])
def train_model():
    """モデル学習エンドポイント"""
    try:
        data = request.json
        model_type = data.get('model_type')
        training_data = data.get('training_data')
        hyperparameters = data.get('hyperparameters', {})
        
        if not model_type or not training_data:
            return jsonify({"error": "model_type and training_data required"}), 400
        
        result = prediction_engine.train_model(
            model_type, training_data, hyperparameters
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@prediction_api.route('/models')
def get_models():
    """モデル一覧エンドポイント"""
    try:
        model_id = request.args.get('model_id')
        result = prediction_engine.get_model_performance(model_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@prediction_api.route('/history')
def get_prediction_history():
    """予測履歴エンドポイント"""
    try:
        # 最新の履歴を返す
        history = list(prediction_engine.prediction_history)
        history.reverse()  # 新しい順
        
        limit = int(request.args.get('limit', 100))
        
        return jsonify({
            "history": history[:limit],
            "total_predictions": len(history)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # テスト用実行
    app = Flask(__name__)
    app.register_blueprint(prediction_api)
    
    print("=== 予測分析 API ===")
    print("エンドポイント:")
    print("- GET  /api/predict/load/<resource_type>")
    print("- GET  /api/predict/incidents")
    print("- GET  /api/predict/optimize")
    print("- POST /api/predict/train")
    print("- GET  /api/predict/models")
    print("- GET  /api/predict/history")
    
    app.run(debug=True, port=5007)