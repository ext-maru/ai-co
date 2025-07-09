#!/usr/bin/env python3
"""
高度データアナリティクスプラットフォーム
エルダーズギルドの全データを統合分析・予測する包括的システム

設計: RAGエルダー × クロードエルダー
承認: エルダーズ評議会（予定）
実装日: 2025年7月9日
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalyticsType(Enum):
    """分析タイプ"""
    COMMIT_PATTERN = "commit_pattern"      # コミットパターン分析
    SAGE_PERFORMANCE = "sage_performance"  # 4賢者パフォーマンス分析
    SYSTEM_HEALTH = "system_health"        # システムヘルス予測
    PROTOCOL_EFFICIENCY = "protocol_efficiency"  # プロトコル効率分析
    ERROR_PREDICTION = "error_prediction"  # エラー予測
    BOTTLENECK_DETECTION = "bottleneck_detection"  # ボトルネック検出

@dataclass
class AnalyticsResult:
    """分析結果"""
    type: AnalyticsType
    timestamp: datetime
    metrics: Dict[str, Any]
    insights: List[str]
    predictions: Dict[str, Any]
    recommendations: List[str]
    confidence: float

class DataCollector:
    """データ収集エンジン"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logs_dir = project_root / "logs"
        self.db_path = project_root / "elder_dashboard.db"
        
    async def collect_commit_data(self) -> pd.DataFrame:
        """コミットデータ収集"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            
            # プロトコル履歴を取得
            query = """
                SELECT 
                    timestamp,
                    protocol,
                    message,
                    approved,
                    execution_time,
                    sage_count,
                    risk_score,
                    files_changed,
                    complexity
                FROM protocol_history
                ORDER BY timestamp
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            # 日時型に変換
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            logger.info(f"📊 {len(df)}件のコミットデータを収集")
            return df
            
        except Exception as e:
            logger.error(f"❌ コミットデータ収集エラー: {e}")
            return pd.DataFrame()
    
    async def collect_sage_consultation_data(self) -> pd.DataFrame:
        """4賢者相談データ収集"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            
            query = """
                SELECT 
                    sc.sage_name,
                    sc.approval,
                    sc.risk_score,
                    sc.advice,
                    sc.timestamp,
                    ph.protocol,
                    ph.complexity
                FROM sage_consultations sc
                JOIN protocol_history ph ON sc.protocol_id = ph.id
                ORDER BY sc.timestamp
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            logger.info(f"🧙‍♂️ {len(df)}件の賢者相談データを収集")
            return df
            
        except Exception as e:
            logger.error(f"❌ 賢者相談データ収集エラー: {e}")
            return pd.DataFrame()
    
    async def collect_system_metrics(self) -> Dict[str, Any]:
        """システムメトリクス収集"""
        metrics = {
            "timestamp": datetime.now(),
            "active_workers": 0,
            "error_logs": 0,
            "warning_logs": 0,
            "total_log_files": 0,
            "disk_usage_mb": 0
        }
        
        try:
            # ログファイル統計
            log_files = list(self.logs_dir.glob("*.log"))
            metrics["total_log_files"] = len(log_files)
            
            # エラー・警告カウント（簡易版）
            for log_file in log_files[:10]:  # サンプリング
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        metrics["error_logs"] += content.count("ERROR")
                        metrics["warning_logs"] += content.count("WARNING")
                except:
                    pass
            
            # ディスク使用量
            total_size = sum(f.stat().st_size for f in log_files)
            metrics["disk_usage_mb"] = total_size / (1024 * 1024)
            
            logger.info(f"📈 システムメトリクス収集完了")
            return metrics
            
        except Exception as e:
            logger.error(f"❌ システムメトリクス収集エラー: {e}")
            return metrics

class AnalyticsEngine:
    """分析エンジン"""
    
    def __init__(self):
        self.ml_models = {}  # 機械学習モデル格納用
        
    async def analyze_commit_patterns(self, df: pd.DataFrame) -> AnalyticsResult:
        """コミットパターン分析"""
        insights = []
        predictions = {}
        metrics = {}
        
        if df.empty:
            return self._empty_result(AnalyticsType.COMMIT_PATTERN)
        
        # 基本統計
        metrics["total_commits"] = len(df)
        metrics["approval_rate"] = df['approved'].mean() * 100
        metrics["avg_execution_time"] = df['execution_time'].mean()
        metrics["avg_complexity"] = df['complexity'].mean()
        
        # プロトコル別分析
        protocol_stats = df.groupby('protocol').agg({
            'approved': ['count', 'mean'],
            'execution_time': 'mean',
            'complexity': 'mean'
        }).round(2)
        
        # MultiIndexを処理しやすい形に変換
        protocol_distribution = {}
        for protocol in protocol_stats.index:
            protocol_distribution[protocol] = {
                'count': int(protocol_stats.loc[protocol, ('approved', 'count')]),
                'approval_rate': float(protocol_stats.loc[protocol, ('approved', 'mean')]),
                'avg_execution_time': float(protocol_stats.loc[protocol, ('execution_time', 'mean')]),
                'avg_complexity': float(protocol_stats.loc[protocol, ('complexity', 'mean')])
            }
        
        metrics["protocol_distribution"] = protocol_distribution
        
        # 時系列分析
        df['hour'] = df['timestamp'].dt.hour
        hourly_commits = df.groupby('hour').size()
        peak_hour = hourly_commits.idxmax()
        
        insights.append(f"📊 ピークコミット時間: {peak_hour}時台")
        insights.append(f"⚡ 平均実行時間: {metrics['avg_execution_time']:.1f}秒")
        
        # 予測
        if len(df) > 10:
            # 簡易的な次回コミット時間予測
            commit_intervals = df['timestamp'].diff().dropna()
            avg_interval = commit_intervals.mean()
            next_commit = df['timestamp'].iloc[-1] + avg_interval
            predictions["next_commit_time"] = next_commit.isoformat()
            predictions["expected_protocol"] = df['protocol'].mode()[0]
        
        # 推奨事項
        recommendations = []
        if metrics["avg_execution_time"] > 10:
            recommendations.append("🚀 実行時間が長いため、Lightning Protocol の活用を推奨")
        if metrics["approval_rate"] < 90:
            recommendations.append("⚠️ 承認率が低下傾向。品質チェックの強化を推奨")
        
        return AnalyticsResult(
            type=AnalyticsType.COMMIT_PATTERN,
            timestamp=datetime.now(),
            metrics=metrics,
            insights=insights,
            predictions=predictions,
            recommendations=recommendations,
            confidence=0.85
        )
    
    async def analyze_sage_performance(self, df: pd.DataFrame) -> AnalyticsResult:
        """4賢者パフォーマンス分析"""
        insights = []
        predictions = {}
        metrics = {}
        
        if df.empty:
            return self._empty_result(AnalyticsType.SAGE_PERFORMANCE)
        
        # 賢者別パフォーマンス
        sage_stats = df.groupby('sage_name').agg({
            'approval': ['count', 'mean'],
            'risk_score': 'mean'
        }).round(3)
        
        # MultiIndexを処理しやすい形に変換
        sage_performance = {}
        for sage in sage_stats.index:
            sage_performance[sage] = {
                'consultation_count': int(sage_stats.loc[sage, ('approval', 'count')]),
                'approval_rate': float(sage_stats.loc[sage, ('approval', 'mean')]),
                'avg_risk_score': float(sage_stats.loc[sage, ('risk_score', 'mean')])
            }
        
        metrics["sage_performance"] = sage_performance
        
        # 賢者間の相関分析
        sage_approvals = df.pivot_table(
            index='timestamp', 
            columns='sage_name', 
            values='approval',
            aggfunc='mean'
        )
        
        if len(sage_approvals.columns) > 1:
            correlation = sage_approvals.corr()
            metrics["sage_correlation"] = correlation.to_dict()
            
            # 高相関ペアの検出
            high_corr_pairs = []
            for i in range(len(correlation.columns)):
                for j in range(i+1, len(correlation.columns)):
                    corr_value = correlation.iloc[i, j]
                    if corr_value > 0.7:
                        high_corr_pairs.append({
                            "pair": f"{correlation.columns[i]} - {correlation.columns[j]}",
                            "correlation": corr_value
                        })
            
            if high_corr_pairs:
                insights.append(f"🤝 高相関賢者ペア検出: {len(high_corr_pairs)}組")
        
        # プロトコル別の賢者承認率
        protocol_sage_approval = df.groupby(['protocol', 'sage_name'])['approval'].mean()
        
        # MultiIndexを処理しやすい形に変換
        approval_dict = {}
        for (protocol, sage_name), approval_rate in protocol_sage_approval.items():
            if protocol not in approval_dict:
                approval_dict[protocol] = {}
            approval_dict[protocol][sage_name] = float(approval_rate)
        
        metrics["protocol_sage_approval"] = approval_dict
        
        # 推奨事項
        recommendations = []
        for sage, stats in sage_stats.iterrows():
            approval_rate = stats[('approval', 'mean')] * 100
            if approval_rate < 80:
                recommendations.append(f"⚠️ {sage}の承認率が{approval_rate:.1f}%と低い")
        
        return AnalyticsResult(
            type=AnalyticsType.SAGE_PERFORMANCE,
            timestamp=datetime.now(),
            metrics=metrics,
            insights=insights,
            predictions=predictions,
            recommendations=recommendations,
            confidence=0.90
        )
    
    async def predict_system_health(self, 
                                  commit_df: pd.DataFrame, 
                                  system_metrics: Dict) -> AnalyticsResult:
        """システムヘルス予測"""
        insights = []
        predictions = {}
        metrics = {}
        
        # 現在のヘルススコア計算
        health_score = 100.0
        
        # エラー率による減点
        if system_metrics["error_logs"] > 100:
            health_score -= 20
            insights.append("⚠️ エラーログが多数検出")
        
        # 警告率による減点
        if system_metrics["warning_logs"] > 500:
            health_score -= 10
            insights.append("⚠️ 警告ログが増加傾向")
        
        # コミット承認率による評価
        if not commit_df.empty:
            approval_rate = commit_df['approved'].mean() * 100
            if approval_rate < 80:
                health_score -= 15
                insights.append(f"📉 コミット承認率が{approval_rate:.1f}%と低下")
        
        metrics["current_health_score"] = health_score
        metrics["error_rate"] = system_metrics["error_logs"] / max(system_metrics["total_log_files"], 1)
        metrics["warning_rate"] = system_metrics["warning_logs"] / max(system_metrics["total_log_files"], 1)
        
        # ヘルス予測（簡易版）
        if health_score >= 80:
            predictions["next_24h_health"] = "良好"
            predictions["maintenance_required"] = False
        elif health_score >= 60:
            predictions["next_24h_health"] = "注意"
            predictions["maintenance_required"] = True
            predictions["maintenance_type"] = "予防的メンテナンス"
        else:
            predictions["next_24h_health"] = "要対応"
            predictions["maintenance_required"] = True
            predictions["maintenance_type"] = "緊急メンテナンス"
        
        # 推奨事項
        recommendations = []
        if health_score < 80:
            recommendations.append("🔧 システムヘルスチェックの実行を推奨")
        if metrics["error_rate"] > 0.1:
            recommendations.append("🚨 エラーログの詳細分析が必要")
        
        return AnalyticsResult(
            type=AnalyticsType.SYSTEM_HEALTH,
            timestamp=datetime.now(),
            metrics=metrics,
            insights=insights,
            predictions=predictions,
            recommendations=recommendations,
            confidence=0.75
        )
    
    def _empty_result(self, analytics_type: AnalyticsType) -> AnalyticsResult:
        """空の結果を返す"""
        return AnalyticsResult(
            type=analytics_type,
            timestamp=datetime.now(),
            metrics={},
            insights=["データが不足しています"],
            predictions={},
            recommendations=["より多くのデータ収集が必要です"],
            confidence=0.0
        )

class PredictiveAnalytics:
    """予測分析エンジン"""
    
    def __init__(self):
        self.models = {}
        
    async def train_models(self, commit_df: pd.DataFrame, sage_df: pd.DataFrame):
        """予測モデルの訓練"""
        logger.info("🤖 予測モデルの訓練開始")
        
        # ここでは簡易的な統計モデルを使用
        # 実際のプロジェクトではscikit-learn等を使用
        
        if not commit_df.empty:
            # コミット間隔予測モデル
            commit_intervals = commit_df['timestamp'].diff().dropna()
            self.models['commit_interval'] = {
                'mean': commit_intervals.mean(),
                'std': commit_intervals.std()
            }
            
            # プロトコル選択予測モデル
            protocol_dist = commit_df['protocol'].value_counts(normalize=True)
            self.models['protocol_selection'] = protocol_dist.to_dict()
        
        logger.info("✅ 予測モデルの訓練完了")
    
    async def predict_next_commit(self) -> Dict[str, Any]:
        """次回コミット予測"""
        predictions = {}
        
        if 'commit_interval' in self.models:
            model = self.models['commit_interval']
            # 正規分布を仮定した予測
            next_interval = np.random.normal(
                model['mean'].total_seconds(),
                model['std'].total_seconds()
            )
            predictions['next_commit_in_seconds'] = max(0, next_interval)
            predictions['confidence'] = 0.7
        
        if 'protocol_selection' in self.models:
            # 確率に基づくプロトコル予測
            protocols = list(self.models['protocol_selection'].keys())
            probabilities = list(self.models['protocol_selection'].values())
            predictions['likely_protocol'] = np.random.choice(protocols, p=probabilities)
        
        return predictions

class AnalyticsReporter:
    """分析レポート生成器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.reports_dir = project_root / "analytics_reports"
        self.reports_dir.mkdir(exist_ok=True)
        
    async def generate_comprehensive_report(self, results: List[AnalyticsResult]) -> Path:
        """包括的レポート生成"""
        timestamp = datetime.now()
        report = {
            "title": "エルダーズギルド データアナリティクスレポート",
            "generated_at": timestamp.isoformat(),
            "summary": self._generate_summary(results),
            "detailed_results": [self._result_to_dict(r) for r in results],
            "executive_insights": self._generate_executive_insights(results),
            "action_items": self._generate_action_items(results)
        }
        
        # レポートファイル保存
        report_file = self.reports_dir / f"analytics_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 包括的レポート生成: {report_file}")
        return report_file
    
    def _generate_summary(self, results: List[AnalyticsResult]) -> Dict[str, Any]:
        """サマリー生成"""
        return {
            "total_analyses": len(results),
            "average_confidence": np.mean([r.confidence for r in results]),
            "key_findings": sum(len(r.insights) for r in results),
            "recommendations": sum(len(r.recommendations) for r in results)
        }
    
    def _result_to_dict(self, result: AnalyticsResult) -> Dict[str, Any]:
        """結果を辞書に変換"""
        return {
            "type": result.type.value,
            "timestamp": result.timestamp.isoformat(),
            "metrics": result.metrics,
            "insights": result.insights,
            "predictions": result.predictions,
            "recommendations": result.recommendations,
            "confidence": result.confidence
        }
    
    def _generate_executive_insights(self, results: List[AnalyticsResult]) -> List[str]:
        """エグゼクティブ向け洞察"""
        insights = []
        
        # 各分析結果から重要な洞察を抽出
        for result in results:
            if result.confidence > 0.8 and result.insights:
                insights.extend(result.insights[:2])  # 上位2つの洞察
        
        return insights[:5]  # 最大5つ
    
    def _generate_action_items(self, results: List[AnalyticsResult]) -> List[str]:
        """アクションアイテム生成"""
        action_items = []
        
        # 推奨事項を優先度付けして集約
        all_recommendations = []
        for result in results:
            for rec in result.recommendations:
                all_recommendations.append({
                    'recommendation': rec,
                    'confidence': result.confidence,
                    'type': result.type.value
                })
        
        # 信頼度でソート
        all_recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        
        # 上位のアクションアイテムを選択
        for item in all_recommendations[:5]:
            action_items.append(f"[{item['type']}] {item['recommendation']}")
        
        return action_items

class DataAnalyticsPlatform:
    """高度データアナリティクスプラットフォーム メインクラス"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.collector = DataCollector(project_root)
        self.analytics = AnalyticsEngine()
        self.predictive = PredictiveAnalytics()
        self.reporter = AnalyticsReporter(project_root)
        
        logger.info("📊 データアナリティクスプラットフォーム初期化完了")
    
    async def run_full_analysis(self) -> Path:
        """完全分析実行"""
        logger.info("🚀 完全分析開始")
        
        try:
            # データ収集フェーズ
            logger.info("📥 データ収集フェーズ")
            commit_df = await self.collector.collect_commit_data()
            sage_df = await self.collector.collect_sage_consultation_data()
            system_metrics = await self.collector.collect_system_metrics()
            
            # 予測モデル訓練
            await self.predictive.train_models(commit_df, sage_df)
            
            # 分析実行フェーズ
            logger.info("🔍 分析実行フェーズ")
            results = []
            
            # コミットパターン分析
            commit_analysis = await self.analytics.analyze_commit_patterns(commit_df)
            results.append(commit_analysis)
            
            # 4賢者パフォーマンス分析
            sage_analysis = await self.analytics.analyze_sage_performance(sage_df)
            results.append(sage_analysis)
            
            # システムヘルス予測
            health_prediction = await self.analytics.predict_system_health(commit_df, system_metrics)
            results.append(health_prediction)
            
            # レポート生成フェーズ
            logger.info("📋 レポート生成フェーズ")
            report_path = await self.reporter.generate_comprehensive_report(results)
            
            logger.info("✅ 完全分析完了")
            return report_path
            
        except Exception as e:
            logger.error(f"❌ 分析中にエラー発生: {e}")
            raise

# テスト実行
async def main():
    """テスト実行"""
    platform = DataAnalyticsPlatform(Path("/home/aicompany/ai_co"))
    report_path = await platform.run_full_analysis()
    print(f"📊 分析レポート生成完了: {report_path}")

if __name__ == "__main__":
    asyncio.run(main())