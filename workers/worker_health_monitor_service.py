#!/usr/bin/env python3
"""
ワーカーヘルス監視サービス
統合的なワーカー監視・管理を提供するサービス
"""
import sys
import time
import signal
import threading
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timedelta

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import setup_logging, EMOJI
from libs.worker_health_monitor import WorkerHealthMonitor, WorkerPerformanceAnalyzer, WorkerAutoScaler
from libs.slack_notifier import SlackNotifier


class WorkerHealthMonitorService:
    """ワーカーヘルス監視サービス"""
    
    def __init__(self):
        """サービスの初期化"""
        self.logger = setup_logging(
            name="WorkerHealthMonitorService",
            log_file=PROJECT_ROOT / "logs" / "worker_health_monitor.log"
        )
        
        # コンポーネント初期化
        self.health_monitor = WorkerHealthMonitor()
        self.performance_analyzer = WorkerPerformanceAnalyzer()
        self.auto_scaler = WorkerAutoScaler()
        self.slack = SlackNotifier()
        
        # 設定
        self.running = True
        self.check_interval = 30  # 30秒間隔
        self.performance_check_interval = 300  # 5分間隔
        self.scaling_check_interval = 600  # 10分間隔
        
        # 最後のチェック時刻
        self.last_performance_check = datetime.now()
        self.last_scaling_check = datetime.now()
        
        # メトリクス履歴
        self.metrics_history = []
        self.max_history_length = 1000
    
    def run(self):
        """メインサービスループ"""
        self.logger.info(f"{EMOJI['start']} Worker Health Monitor Service started")
        
        # シグナルハンドラ設定
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
        
        try:
            while self.running:
                self._perform_health_checks()
                
                # パフォーマンスチェック
                if self._should_perform_performance_check():
                    self._perform_performance_analysis()
                    self.last_performance_check = datetime.now()
                
                # スケーリングチェック
                if self._should_perform_scaling_check():
                    self._perform_scaling_analysis()
                    self.last_scaling_check = datetime.now()
                
                time.sleep(self.check_interval)
                
        except Exception as e:
            self.logger.error(f"{EMOJI['error']} Service error: {str(e)}")
            self._send_critical_alert("Service error", str(e))
        finally:
            self.logger.info(f"{EMOJI['stop']} Worker Health Monitor Service stopped")
    
    def _handle_signal(self, signum, frame):
        """シグナルハンドラ"""
        self.logger.info(f"{EMOJI['stop']} Received signal {signum}, shutting down...")
        self.running = False
    
    def _perform_health_checks(self):
        """ヘルスチェック実行"""
        try:
            # 包括的メトリクス収集
            metrics = self.health_monitor.collect_comprehensive_metrics()
            
            # メトリクス履歴に追加
            self._add_to_history(metrics)
            
            # 健全性評価
            overall_healthy = metrics['system_health']['overall_healthy']
            
            if not overall_healthy:
                self.logger.warning(f"{EMOJI['warning']} System health degraded")
                self._handle_unhealthy_system(metrics)
            else:
                self.logger.debug(f"{EMOJI['success']} System health OK")
            
        except Exception as e:
            self.logger.error(f"{EMOJI['error']} Health check failed: {str(e)}")
    
    def _perform_performance_analysis(self):
        """パフォーマンス分析実行"""
        try:
            self.logger.info(f"{EMOJI['monitor']} Performing performance analysis")
            
            # 最近のメトリクスを取得
            recent_metrics = self._get_recent_metrics(minutes=30)
            
            if not recent_metrics:
                return
            
            # ボトルネック検出
            worker_metrics = self._extract_worker_metrics(recent_metrics)
            bottlenecks = self.performance_analyzer.detect_bottlenecks(worker_metrics)
            
            if bottlenecks:
                self.logger.warning(f"{EMOJI['warning']} Performance bottlenecks detected: {list(bottlenecks.keys())}")
                self._handle_performance_issues(bottlenecks)
            
        except Exception as e:
            self.logger.error(f"{EMOJI['error']} Performance analysis failed: {str(e)}")
    
    def _perform_scaling_analysis(self):
        """スケーリング分析実行（エラー耐性強化）"""
        try:
            self.logger.info(f"{EMOJI['scaling']} Performing scaling analysis")
            
            # WorkerHealthMonitor が不完全な場合の対策
            if not hasattr(self.health_monitor, 'collect_comprehensive_metrics'):
                self.logger.warning("Scaling analysis skipped - collect_comprehensive_metrics not implemented")
                return
                
            if not hasattr(self.health_monitor, 'get_scaling_recommendations'):
                self.logger.warning("Scaling analysis skipped - get_scaling_recommendations not implemented")
                return
            
            # 現在のシステムメトリクス
            current_metrics = self.health_monitor.collect_comprehensive_metrics()
            
            # スケーリング推奨取得
            system_metrics = {
                'queue_lengths': {'task_queue': 50, 'pm_queue': 10},  # 実際にはキューから取得
                'worker_counts': {'task_worker': 2, 'pm_worker': 1},
                'avg_processing_times': {'task_worker': 2000, 'pm_worker': 1500},
                'system_load': 0.6
            }
            
            recommendations = self.health_monitor.get_scaling_recommendations(system_metrics)
            
            if recommendations:
                self.logger.info(f"{EMOJI['scaling']} Scaling recommendations: {recommendations}")
                self._handle_scaling_recommendations(recommendations)
                
        except AttributeError as e:
            self.logger.warning(f"{EMOJI['warning']} Scaling feature not available: {e}")
        except Exception as e:
            self.logger.error(f"{EMOJI['error']} Scaling analysis failed: {str(e)}")
    
    def _handle_unhealthy_system(self, metrics: Dict[str, Any]):
        """不健全システムの対処"""
        unhealthy_workers = []
        
        for worker_name, worker_metrics in metrics.get('workers', {}).items():
            if worker_metrics.get('status') != 'running':
                unhealthy_workers.append(worker_name)
        
        if unhealthy_workers:
            self.logger.warning(f"{EMOJI['warning']} Unhealthy workers: {unhealthy_workers}")
            
            # 自動再起動試行
            restart_results = self.health_monitor.restart_unhealthy_workers()
            
            # 結果をログ出力
            for result in restart_results:
                if result.get('success'):
                    self.logger.info(f"{EMOJI['success']} Worker restarted successfully")
                else:
                    self.logger.error(f"{EMOJI['error']} Worker restart failed: {result.get('error')}")
                    
                    # クリティカルアラート送信
                    self._send_critical_alert(
                        f"Worker restart failed",
                        f"Failed to restart worker: {result}"
                    )
    
    def _handle_performance_issues(self, bottlenecks: Dict[str, Any]):
        """パフォーマンス問題の対処"""
        for worker_name, issue in bottlenecks.items():
            issue_type = issue.get('type')
            
            if issue_type == 'queue_overload':
                self._send_performance_alert(worker_name, "Queue overload detected")
            elif issue_type == 'slow_processing':
                self._send_performance_alert(worker_name, "Slow processing detected")
            elif issue_type == 'high_error_rate':
                self._send_critical_alert(worker_name, "High error rate detected")
    
    def _handle_scaling_recommendations(self, recommendations: Dict[str, Any]):
        """スケーリング推奨の対処"""
        for worker_name, rec in recommendations.items():
            action = rec.get('action')
            current_count = rec.get('current_count', 1)
            recommended_count = rec.get('recommended_count', 1)
            
            if action == 'scale_up':
                self.logger.info(f"{EMOJI['scaling']} Recommending scale up for {worker_name}: {current_count} → {recommended_count}")
                self._send_scaling_alert(worker_name, f"Scale up recommended: {current_count} → {recommended_count}")
            elif action == 'scale_down':
                self.logger.info(f"{EMOJI['scaling']} Recommending scale down for {worker_name}: {current_count} → {recommended_count}")
    
    def _should_perform_performance_check(self) -> bool:
        """パフォーマンスチェック実行タイミング判定"""
        return (datetime.now() - self.last_performance_check).total_seconds() >= self.performance_check_interval
    
    def _should_perform_scaling_check(self) -> bool:
        """スケーリングチェック実行タイミング判定"""
        return (datetime.now() - self.last_scaling_check).total_seconds() >= self.scaling_check_interval
    
    def _add_to_history(self, metrics: Dict[str, Any]):
        """メトリクス履歴に追加"""
        self.metrics_history.append(metrics)
        
        # 履歴サイズ制限
        if len(self.metrics_history) > self.max_history_length:
            self.metrics_history = self.metrics_history[-self.max_history_length:]
    
    def _get_recent_metrics(self, minutes: int = 30) -> list:
        """最近のメトリクス取得"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        recent_metrics = []
        for metric in reversed(self.metrics_history):
            timestamp_str = metric.get('timestamp')
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    if timestamp >= cutoff_time:
                        recent_metrics.append(metric)
                except ValueError:
                    continue
        
        return recent_metrics
    
    def _extract_worker_metrics(self, metrics_list: list) -> Dict[str, Any]:
        """ワーカーメトリクス抽出"""
        worker_metrics = {}
        
        for metrics in metrics_list:
            workers = metrics.get('workers', {})
            for worker_name, worker_data in workers.items():
                if worker_name not in worker_metrics:
                    worker_metrics[worker_name] = {
                        'queue_length': 50,  # 実際にはキューから取得
                        'processing_time': 2000,  # 実際には計測
                        'error_rate': 0.05  # 実際にはログから計算
                    }
        
        return worker_metrics
    
    def _send_critical_alert(self, title: str, message: str):
        """クリティカルアラート送信"""
        try:
            alert_message = f"🚨 CRITICAL: {title}\n{message}\nTimestamp: {datetime.now().isoformat()}"
            self.slack.send_message(alert_message)
        except Exception as e:
            self.logger.error(f"Failed to send critical alert: {e}")
    
    def _send_performance_alert(self, worker_name: str, message: str):
        """パフォーマンスアラート送信"""
        try:
            alert_message = f"⚠️ PERFORMANCE: {worker_name}\n{message}\nTimestamp: {datetime.now().isoformat()}"
            self.slack.send_message(alert_message)
        except Exception as e:
            self.logger.error(f"Failed to send performance alert: {e}")
    
    def _send_scaling_alert(self, worker_name: str, message: str):
        """スケーリングアラート送信"""
        try:
            alert_message = f"📈 SCALING: {worker_name}\n{message}\nTimestamp: {datetime.now().isoformat()}"
            self.slack.send_message(alert_message)
        except Exception as e:
            self.logger.error(f"Failed to send scaling alert: {e}")


if __name__ == "__main__":
    service = WorkerHealthMonitorService()
    service.run()