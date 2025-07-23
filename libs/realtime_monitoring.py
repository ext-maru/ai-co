#!/usr/bin/env python3
"""
Real-time Monitoring System
"""
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path


class RealTimeMonitor:
    """RealTimeMonitor - 監視クラス"""
    def __init__(self):
        """初期化メソッド"""
        self.metrics = {}
        self.alerts = []
        self.running = False

    async def collect_metrics(self):
        """メトリクス収集"""
        while self.running:
            try:
                import psutil

                metrics = {
                    "timestamp": datetime.now().isoformat(),
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage("/").percent,
                    "active_processes": len(psutil.pids()),
                }

                # 異常検知
                if metrics["cpu_percent"] > 90:
                    self.alerts.append(f"HIGH CPU: {metrics['cpu_percent']:.1f}%")

                if metrics["memory_percent"] > 95:
                    self.alerts.append(f"HIGH MEMORY: {metrics['memory_percent']:.1f}%")

                self.metrics = metrics

            except ImportError:
                self.metrics = {"status": "monitoring unavailable"}

            await asyncio.sleep(5)  # 5秒間隔

    def start_monitoring(self):
        """監視開始"""
        self.running = True
        print("📊 リアルタイム監視開始")

    def stop_monitoring(self):
        """監視停止"""
        self.running = False
        print("📊 リアルタイム監視停止")

    def get_status_report(self):
        """ステータスレポート取得"""
        return {
            "current_metrics": self.metrics,
            "recent_alerts": self.alerts[-10:],  # 最新10件
            "monitoring_active": self.running,
        }


# 予測分析システム
class PredictiveAnalyzer:
    """PredictiveAnalyzer - 分析クラス"""
    def __init__(self):
        """初期化メソッド"""
        self.history = []

    def add_datapoint(self, metrics):
        """データポイント追加"""
        self.history.append(metrics)
        if len(self.history) > 100:  # 最新100件のみ保持
            self.history.pop(0)

    def predict_trend(self, metric_name):
        """トレンド予測"""
        if len(self.history) < 5:
            return "insufficient data"

        recent_values = [h.get(metric_name, 0) for h in self.history[-5:]]
        avg_change = sum(
            recent_values[i] - recent_values[i - 1]
            for i in range(1, len(recent_values))
        ) / (len(recent_values) - 1)

        if avg_change > 5:
            return "increasing"
        elif avg_change < -5:
            return "decreasing"
        else:
            return "stable"


if __name__ == "__main__":
    monitor = RealTimeMonitor()
    analyzer = PredictiveAnalyzer()

    # デモ実行
    monitor.start_monitoring()
    print("監視システム稼働中...")
    print(json.dumps(monitor.get_status_report(), indent=2))
