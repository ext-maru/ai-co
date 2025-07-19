#!/usr/bin/env python3
"""
Scaling Policy - スケーリング判断ロジック
"""
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger("ScalingPolicy")


class ScalingPolicy:
    def __init__(self, config_file=None):
        """スケーリングポリシーの初期化"""
        if config_file is None:
            config_file = Path(__file__).parent.parent / "config" / "scaling.conf"
        self.config = self._load_config(config_file)
        self.last_scaling_time = None
        self.scaling_history = []

    def _load_config(self, config_file):
        """設定ファイル読み込み"""
        config = {
            "MIN_WORKERS": 1,
            "MAX_WORKERS": 5,
            "SCALE_UP_QUEUE_LENGTH": 5,
            "SCALE_DOWN_QUEUE_LENGTH": 1,
            "COOLDOWN_SECONDS": 60,
            "MAX_CPU_PERCENT": 80,
            "MAX_MEMORY_PERCENT": 80,
        }

        try:
            with open(config_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        try:
                            config[key] = int(value)
                        except ValueError:
                            config[key] = value
        except Exception as e:
            logger.error(f"設定読み込みエラー: {e}")

        return config

    def should_scale(self, metrics):
        """スケーリングが必要か判断"""
        # クールダウン期間チェック
        if self.last_scaling_time:
            elapsed = (datetime.now() - self.last_scaling_time).seconds
            if elapsed < self.config["COOLDOWN_SECONDS"]:
                logger.info(
                    f"⏳ クールダウン中: あと{self.config['COOLDOWN_SECONDS'] - elapsed}秒"
                )
                return "none", None

        current_workers = metrics["active_workers"]
        queue_length = metrics["queue_length"]
        cpu_percent = metrics["system"]["cpu_percent"]
        memory_percent = metrics["system"]["memory_percent"]

        # スケールアップ判定
        if self._should_scale_up(
            current_workers, queue_length, cpu_percent, memory_percent
        ):
            target = min(current_workers + 1, self.config["MAX_WORKERS"])
            if target > current_workers:
                return "up", target

        # スケールダウン判定
        if self._should_scale_down(
            current_workers, queue_length, cpu_percent, memory_percent
        ):
            target = max(current_workers - 1, self.config["MIN_WORKERS"])
            if target < current_workers:
                return "down", target

        return "none", None

    def _should_scale_up(self, workers, queue_length, cpu, memory):
        """スケールアップ判定ロジック"""
        # 最大ワーカー数に達している場合
        if workers >= self.config["MAX_WORKERS"]:
            return False

        # キューが溜まっている場合
        if queue_length > self.config["SCALE_UP_QUEUE_LENGTH"]:
            logger.info(
                f"📈 スケールアップ条件: キュー長 {queue_length} > {self.config['SCALE_UP_QUEUE_LENGTH']}"
            )
            return True

        # ワーカー数に対してキューが多すぎる場合
        if workers > 0 and queue_length > workers * 3:
            logger.info(
                f"📈 スケールアップ条件: キュー/ワーカー比 {queue_length}/{workers} > 3"
            )
            return True

        # システムリソースに余裕がある場合でキューがある
        if queue_length > 0 and cpu < 50 and memory < 50:
            logger.info(
                f"📈 スケールアップ条件: リソース余裕あり (CPU:{cpu}%, Mem:{memory}%)"
            )
            return True

        return False

    def _should_scale_down(self, workers, queue_length, cpu, memory):
        """スケールダウン判定ロジック"""
        # 最小ワーカー数の場合
        if workers <= self.config["MIN_WORKERS"]:
            return False

        # キューが少ない場合
        if queue_length <= self.config["SCALE_DOWN_QUEUE_LENGTH"]:
            # 複数ワーカーでキューがほぼない場合
            if workers > 2 and queue_length == 0:
                logger.info(f"📉 スケールダウン条件: キューなし、ワーカー過剰")
                return True
            # 最小限を超えていてキューが閾値以下
            elif workers > self.config["MIN_WORKERS"]:
                logger.info(
                    f"📉 スケールダウン条件: キュー長 {queue_length} <= {self.config['SCALE_DOWN_QUEUE_LENGTH']}"
                )
                return True

        return False

    def record_scaling(self, action, from_workers, to_workers):
        """スケーリング実行を記録"""
        self.last_scaling_time = datetime.now()
        self.scaling_history.append(
            {
                "timestamp": self.last_scaling_time,
                "action": action,
                "from": from_workers,
                "to": to_workers,
            }
        )

        # 履歴は最新100件まで保持
        if len(self.scaling_history) > 100:
            self.scaling_history = self.scaling_history[-100:]

    def get_scaling_stats(self):
        """スケーリング統計を取得"""
        if not self.scaling_history:
            return {
                "total_scaling": 0,
                "scale_ups": 0,
                "scale_downs": 0,
                "last_scaling": None,
            }

        scale_ups = sum(1 for h in self.scaling_history if h["action"] == "up")
        scale_downs = sum(1 for h in self.scaling_history if h["action"] == "down")

        return {
            "total_scaling": len(self.scaling_history),
            "scale_ups": scale_ups,
            "scale_downs": scale_downs,
            "last_scaling": (
                self.scaling_history[-1]["timestamp"].isoformat()
                if self.scaling_history
                else None
            ),
        }


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    policy = ScalingPolicy()

    # テストメトリクス
    test_metrics = {
        "active_workers": 2,
        "queue_length": 10,
        "system": {"cpu_percent": 30, "memory_percent": 40},
    }

    action, target = policy.should_scale(test_metrics)
    print(f"スケーリング判定: {action}, 目標ワーカー数: {target}")
