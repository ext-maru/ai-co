#!/usr/bin/env python3
"""
モニタリング機能ミックスイン
リアルタイムでワーカーのパフォーマンスを監視
"""

import json
import time
from collections import deque
from datetime import datetime
from typing import Any, Dict, Optional


class MonitoringMixin:
    """ワーカーにモニタリング機能を追加するミックスイン"""

    def __init__(self):
        """初期化メソッド"""
        self.metrics = {
            "processed_count": 0,
            "error_count": 0,
            "success_count": 0,
            "total_processing_time": 0,
            "last_error": None,
            "last_success_time": None,
            "start_time": datetime.now(),
        }

        # 最近の処理時間を記録（最大100件）
        self.recent_processing_times = deque(maxlen=100)

        # 分単位のスループット記録
        self.throughput_history = deque(maxlen=60)
        self.last_throughput_update = time.time()
        self.minute_processed_count = 0

    def record_task_start(self):
        """タスク開始時の記録"""
        return time.time()

    def record_task_complete(self, start_time: float, success: bool = True):
        """タスク完了時の記録"""
        processing_time = time.time() - start_time
        self.recent_processing_times.append(processing_time)
        self.metrics["total_processing_time"] += processing_time
        self.metrics["processed_count"] += 1
        self.minute_processed_count += 1

        if success:
            self.metrics["success_count"] += 1
            self.metrics["last_success_time"] = datetime.now()
        else:
            self.metrics["error_count"] += 1

        # 分単位のスループット更新
        self._update_throughput()

    def record_error(self, error: Exception):
        """エラーの記録"""
        self.metrics["error_count"] += 1
        self.metrics["last_error"] = {
            "type": type(error).__name__,
            "message": str(error),
            "timestamp": datetime.now().isoformat(),
        }

    def _update_throughput(self):
        """スループット履歴の更新"""
        current_time = time.time()
        if current_time - self.last_throughput_update >= 60:
            self.throughput_history.append(self.minute_processed_count)
            self.minute_processed_count = 0
            self.last_throughput_update = current_time

    @property
    def avg_processing_time(self) -> float:
        """平均処理時間"""
        if not self.recent_processing_times:
            return 0
        return sum(self.recent_processing_times) / len(self.recent_processing_times)

    @property
    def error_rate(self) -> float:
        """エラー率"""
        if self.metrics["processed_count"] == 0:
            return 0
        return self.metrics["error_count"] / self.metrics["processed_count"]

    @property
    def success_rate(self) -> float:
        """成功率"""
        return 1 - self.error_rate

    def get_throughput(self) -> float:
        """現在のスループット（タスク/分）"""
        if not self.throughput_history:
            return self.minute_processed_count

        # 直近5分間の平均
        recent = list(self.throughput_history)[-5:]
        return sum(recent) / len(recent) if recent else 0

    def calculate_health_score(self) -> float:
        """ヘルススコア計算（0-100）"""
        score = 100.0

        # エラー率による減点
        score -= self.error_rate * 50

        # 処理速度による評価
        if self.avg_processing_time > 10:  # 10秒以上は遅い
            score -= 20
        elif self.avg_processing_time > 5:  # 5秒以上はやや遅い
            score -= 10

        # 最近のエラー
        if self.metrics["last_error"]:
            last_error_time = datetime.fromisoformat(
                self.metrics["last_error"]["timestamp"]
            )
            if (datetime.now() - last_error_time).seconds < 300:  # 5分以内
                score -= 10

        return max(0, min(100, score))

    @property
    def performance_stats(self) -> Dict[str, Any]:
        """パフォーマンス統計"""
        uptime = (datetime.now() - self.metrics["start_time"]).total_seconds()

        return {
            "uptime_seconds": uptime,
            "processed_count": self.metrics["processed_count"],
            "success_count": self.metrics["success_count"],
            "error_count": self.metrics["error_count"],
            "error_rate": f"{self.error_rate:0.2%}",
            "success_rate": f"{self.success_rate:0.2%}",
            "avg_processing_time": f"{self.avg_processing_time:0.2f}s",
            "tasks_per_minute": f"{self.get_throughput():0.1f}",
            "health_score": f"{self.calculate_health_score():0.1f}",
            "last_error": self.metrics["last_error"],
            "last_success_time": self.metrics["last_success_time"].isoformat()
            if self.metrics["last_success_time"]
            else None,
        }

    def get_monitoring_data(self) -> Dict[str, Any]:
        """モニタリングデータ取得（ダッシュボード用）"""
        return {
            "worker_type": getattr(self, "worker_type", "unknown"),
            "worker_id": getattr(self, "worker_id", "unknown"),
            "status": "healthy" if self.calculate_health_score() > 70 else "unhealthy",
            "metrics": self.metrics,
            "performance": self.performance_stats,
            "recent_processing_times": list(self.recent_processing_times)[-20:],
            "throughput_history": list(self.throughput_history),
        }
