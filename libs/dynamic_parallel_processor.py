#!/usr/bin/env python3
"""
Dynamic Parallel Processing System for Auto Issue Processor
Issue #192 Phase 2: 動的並列処理最適化

システムリソースに基づく動的な並列度調整とプロセス管理
"""

import asyncio
import logging
import os
import psutil
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """リソースタイプ"""
    CPU = "cpu"
    MEMORY = "memory"
    IO = "io"
    NETWORK = "network"


class ScalingDirection(Enum):
    """スケーリング方向"""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


@dataclass
class SystemResources:
    """システムリソース情報"""
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_io_percent: float
    load_average: float
    active_connections: int
    timestamp: float
    
    def is_under_pressure(self, thresholds: Dict[str, float]) -> bool:
        """リソースが圧迫状態かチェック"""
        return (
            self.cpu_percent > thresholds.get("cpu", 80.0) or
            self.memory_percent > thresholds.get("memory", 85.0) or
            self.load_average > thresholds.get("load", 2.0)
        )
    
    def has_capacity(self, thresholds: Dict[str, float]) -> bool:
        """リソースに余裕があるかチェック"""
        return (
            self.cpu_percent < thresholds.get("cpu_low", 50.0) and
            self.memory_percent < thresholds.get("memory_low", 60.0) and
            self.memory_available_gb > thresholds.get("memory_min_gb", 0.5)
        )


@dataclass
class ScalingDecision:
    """スケーリング決定"""
    direction: ScalingDirection
    target_concurrency: int
    reason: str
    confidence: float
    resource_utilization: Dict[str, float]


class ResourceMonitor:
    """システムリソースモニター"""
    
    def __init__(self, sampling_interval: float = 1.0):
        """初期化メソッド"""

        self.sampling_interval = sampling_interval
        self.history: List[SystemResources] = []
        self.max_history = 60  # 60秒間の履歴
        self.monitoring = False
        self._monitor_task = None
        
    async def start_monitoring(self):
        """監視開始"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Resource monitoring started")
    
    async def stop_monitoring(self):
        """監視停止"""
        if not self.monitoring:
            return
            
        self.monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Resource monitoring stopped")
    
    async def _monitor_loop(self):
        """監視ループ"""
        try:
            while self.monitoring:
                resources = self._collect_resources()
                self.history.append(resources)
                
                # 履歴サイズ制限
                if len(self.history) > self.max_history:
                    self.history.pop(0)
                
                await asyncio.sleep(self.sampling_interval)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in resource monitoring: {e}")
    
    def _collect_resources(self) -> SystemResources:
        """リソース情報収集"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=None)
        
        # メモリ情報
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_gb = memory.available / 1024 / 1024 / 1024
        
        # ディスクI/O (簡易的)
        disk_io_percent = 0.0
        try:
            disk_io = psutil.disk_io_counters()
            # 簡易的なI/O使用率計算（実装を簡略化）
            disk_io_percent = min(disk_io.read_count + disk_io.write_count, 100) / 100 * 100
        except:
            pass
        
        # ロードアベレージ
        load_average = 0.0
        try:
            load_average = os.getloadavg()[0]
        except:
            pass
        
        # アクティブ接続数
        active_connections = len(psutil.net_connections())
        
        return SystemResources(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_available_gb=memory_available_gb,
            disk_io_percent=disk_io_percent,
            load_average=load_average,
            active_connections=active_connections,
            timestamp=time.time()
        )
    
    def get_current_resources(self) -> Optional[SystemResources]:
        """現在のリソース情報取得"""
        if not self.history:
            return self._collect_resources()
        return self.history[-1]
    
    def get_average_resources(self, window_seconds: int = 30) -> Optional[SystemResources]:
        """指定期間の平均リソース使用率"""
        if not self.history:
            return None
        
        cutoff_time = time.time() - window_seconds
        recent_samples = [r for r in self.history if r.timestamp >= cutoff_time]
        
        if not recent_samples:
            return None
        
        # 平均値計算
        avg_cpu = sum(r.cpu_percent for r in recent_samples) / len(recent_samples)
        avg_memory = sum(r.memory_percent for r in recent_samples) / len(recent_samples)
        avg_memory_available = sum(r.memory_available_gb for r in recent_samples) / len(recent_samples)
        avg_disk_io = sum(r.disk_io_percent for r in recent_samples) / len(recent_samples)
        avg_load = sum(r.load_average for r in recent_samples) / len(recent_samples)
        avg_connections = sum(r.active_connections for r in recent_samples) / len(recent_samples)
        
        return SystemResources(
            cpu_percent=avg_cpu,
            memory_percent=avg_memory,
            memory_available_gb=avg_memory_available,
            disk_io_percent=avg_disk_io,
            load_average=avg_load,
            active_connections=int(avg_connections),
            timestamp=time.time()
        )


class ScalingStrategy(ABC):
    """スケーリング戦略の抽象基底クラス"""
    
    @abstractmethod
    async def decide_scaling(
        self,
        current_concurrency: int,
        resources: SystemResources,
        performance_metrics: Dict[str, float]
    ) -> ScalingDecision:
        """スケーリング決定"""
        pass


class AdaptiveScalingStrategy(ScalingStrategy):
    """適応的スケーリング戦略"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初期化メソッド"""
        self.config = config or self._default_config()
        
    def _default_config(self) -> Dict[str, Any]:
        """デフォルト設定"""
        return {
            "min_concurrency": 1,
            "max_concurrency": psutil.cpu_count() * 2,
            "scale_up_threshold": {
                "cpu_low": 40.0,
                "memory_low": 50.0,
                "memory_min_gb": 1.0
            },
            "scale_down_threshold": {
                "cpu": 85.0,
                "memory": 90.0,
                "load": 3.0
            },
            "scale_factor": 1.5,  # スケールアップ時の倍率
            "scale_down_factor": 0.7,  # スケールダウン時の倍率
            "cooldown_seconds": 30,  # スケーリング後のクールダウン時間
            "confidence_threshold": 0.7  # 決定の信頼度閾値
        }
    
    async def decide_scaling(
        self,
        current_concurrency: int,
        resources: SystemResources,
        performance_metrics: Dict[str, float]
    ) -> ScalingDecision:
        """適応的スケーリング決定"""
        
        # リソース使用状況の分析
        resource_pressure = self._analyze_resource_pressure(resources)
        performance_score = self._calculate_performance_score(performance_metrics)
        
        # スケーリング方向の決定
        if resource_pressure > 0.8:
            # リソース不足 - スケールダウン
            target = max(
                self.config["min_concurrency"],
                int(current_concurrency * self.config["scale_down_factor"])
            )
            direction = ScalingDirection.DOWN
            reason = f"High resource pressure ({resource_pressure:0.2f})"
            confidence = resource_pressure
            
        elif resource_pressure < 0.4 and performance_score > 0.7:
            # リソース余裕あり・性能良好 - スケールアップ
            target = min(
                self.config["max_concurrency"],
                int(current_concurrency * self.config["scale_factor"])
            )
            direction = ScalingDirection.UP
            reason = f"Low resource pressure ({resource_pressure:0.2f}) and good performance " \
                "({performance_score:0.2f})"
            confidence = (1.0 - resource_pressure) * performance_score
            
        else:
            # 現状維持
            target = current_concurrency
            direction = ScalingDirection.STABLE
            reason = f"Balanced state (pressure: {resource_pressure:0.2f}, performance: " \
                "{performance_score:0.2f})"
            confidence = 0.5
        
        return ScalingDecision(
            direction=direction,
            target_concurrency=target,
            reason=reason,
            confidence=confidence,
            resource_utilization={
                "cpu": resources.cpu_percent,
                "memory": resources.memory_percent,
                "pressure_score": resource_pressure,
                "performance_score": performance_score
            }
        )
    
    def _analyze_resource_pressure(self, resources: SystemResources) -> float:
        """リソース圧迫度を0-1のスコアで計算"""
        weights = {
            "cpu": 0.4,
            "memory": 0.4,
            "load": 0.2
        }
        
        # 各リソースの圧迫度（0-1）
        cpu_pressure = min(resources.cpu_percent / 100.0, 1.0)
        memory_pressure = min(resources.memory_percent / 100.0, 1.0)
        load_pressure = min(resources.load_average / psutil.cpu_count(), 1.0)
        
        # 重み付き平均
        total_pressure = (
            cpu_pressure * weights["cpu"] +
            memory_pressure * weights["memory"] +
            load_pressure * weights["load"]
        )
        
        return total_pressure
    
    def _calculate_performance_score(self, metrics: Dict[str, float]) -> float:
        """性能スコアを0-1で計算"""
        throughput = metrics.get("throughput", 0)
        error_rate = metrics.get("error_rate", 0)
        avg_response_time = metrics.get("avg_response_time", 1.0)
        
        # スループットスコア（基準値との比較）
        baseline_throughput = 10.0  # issues/second
        throughput_score = min(throughput / baseline_throughput, 1.0)
        
        # エラー率スコア（低いほど良い）
        error_score = max(1.0 - error_rate, 0.0)
        
        # レスポンス時間スコア（速いほど良い）
        baseline_response = 0.1  # seconds
        response_score = max(1.0 - (avg_response_time / baseline_response), 0.0)
        
        # 総合スコア
        overall_score = (throughput_score * 0.5 + error_score * 0.3 + response_score * 0.2)
        
        return overall_score


class DynamicParallelProcessor:
    """動的並列プロセッサー"""
    
    def __init__(
        self,
        initial_concurrency: int = 5,
        strategy: ScalingStrategy = None,
        monitor_interval: float = 5.0
    ):
        self.current_concurrency = initial_concurrency
        self.strategy = strategy or AdaptiveScalingStrategy()
        self.monitor_interval = monitor_interval
        
        self.resource_monitor = ResourceMonitor()
        self.scaling_history: List[Dict[str, Any]] = []
        self.last_scaling_time = 0
        self.performance_metrics = {}
        
        # 処理統計
        self.processed_count = 0
        self.error_count = 0
        self.total_processing_time = 0.0
        self.processing_times = []
        
        # セマフォ（並列度制御）
        self._semaphore = asyncio.Semaphore(initial_concurrency)
        self._semaphore_lock = asyncio.Lock()
        
        logger.info(f"Dynamic Parallel Processor initialized with concurrency: {initial_concurrency}" \
            "Dynamic Parallel Processor initialized with concurrency: {initial_concurrency}")
    
    async def start(self):
        """プロセッサー開始"""
        await self.resource_monitor.start_monitoring()
        asyncio.create_task(self._auto_scaling_loop())
        logger.info("Dynamic Parallel Processor started")
    
    async def stop(self):
        """プロセッサー停止"""
        await self.resource_monitor.stop_monitoring()
        logger.info("Dynamic Parallel Processor stopped")
    
    async def process_items(
        self,
        items: List[Any],
        processor_func: Callable[[Any], Any],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Any]:
        """アイテムリストを動的並列処理"""
        results = []
        completed = 0
        
        async def process_single_item(item):
            """process_single_item処理メソッド"""
            nonlocal completed
            async with self._semaphore:
                start_time = time.time()
                try:
                    result = await processor_func(item)
                    processing_time = time.time() - start_time
                    
                    # 統計更新
                    self.processed_count += 1
                    self.total_processing_time += processing_time
                    self.processing_times.append(processing_time)
                    
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, len(items))
                    
                    return result
                    
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing item: {e}")
                    raise
        
        # 全アイテムを並列処理
        tasks = [process_single_item(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return results
    
    async def _auto_scaling_loop(self):
        """自動スケーリングループ"""
        try:
            while True:
                await asyncio.sleep(self.monitor_interval)
                await self._check_and_scale()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in auto-scaling loop: {e}")
    
    async def _check_and_scale(self):
        """スケーリングチェックと実行"""
        # 現在のリソース状況を取得
        current_resources = self.resource_monitor.get_current_resources()
        if not current_resources:
            return
        
        # 性能メトリクスを更新
        self._update_performance_metrics()
        
        # スケーリング決定
        decision = await self.strategy.decide_scaling(
            self.current_concurrency,
            current_resources,
            self.performance_metrics
        )
        
        # クールダウン期間チェック
        cooldown_period = self.strategy.config.get("cooldown_seconds", 30)
        if time.time() - self.last_scaling_time < cooldown_period:
            return
        
        # 信頼度チェック
        confidence_threshold = self.strategy.config.get("confidence_threshold", 0.7)
        if decision.confidence < confidence_threshold:
            return
        
        # スケーリング実行
        if decision.direction != ScalingDirection.STABLE:
            await self._execute_scaling(decision)
    
    def _update_performance_metrics(self):
        """性能メトリクス更新"""
        if self.processed_count == 0:
            self.performance_metrics = {
                "throughput": 0.0,
                "error_rate": 0.0,
                "avg_response_time": 0.0
            }
            return
        
        # スループット計算（最近の処理から推定）
        recent_window = 60  # seconds
        recent_times = [t for t in self.processing_times if time.time() - t < recent_window]
        throughput = len(recent_times) / recent_window if recent_times else 0.0
        
        # エラー率
        error_rate = self.error_count / max(self.processed_count, 1)
        
        # 平均レスポンス時間
        avg_response_time = self.total_processing_time / max(self.processed_count, 1)
        
        self.performance_metrics = {
            "throughput": throughput,
            "error_rate": error_rate,
            "avg_response_time": avg_response_time,
            "processed_count": self.processed_count,
            "total_errors": self.error_count
        }
    
    async def _execute_scaling(self, decision: ScalingDecision):
        """スケーリング実行"""
        old_concurrency = self.current_concurrency
        new_concurrency = decision.target_concurrency
        
        if old_concurrency == new_concurrency:
            return
        
        logger.info(
            f"Scaling {decision.direction.value}: {old_concurrency} -> {new_concurrency} "
            f"(reason: {decision.reason}, confidence: {decision.confidence:0.2f})"
        )
        
        # セマフォを更新
        async with self._semaphore_lock:
            # 新しいセマフォを作成
            self._semaphore = asyncio.Semaphore(new_concurrency)
            self.current_concurrency = new_concurrency
        
        # スケーリング履歴を記録
        self.scaling_history.append({
            "timestamp": time.time(),
            "old_concurrency": old_concurrency,
            "new_concurrency": new_concurrency,
            "direction": decision.direction.value,
            "reason": decision.reason,
            "confidence": decision.confidence,
            "resource_utilization": decision.resource_utilization
        })
        
        self.last_scaling_time = time.time()
    
    def get_status(self) -> Dict[str, Any]:
        """現在のステータス取得"""
        current_resources = self.resource_monitor.get_current_resources()
        
        return {
            "current_concurrency": self.current_concurrency,
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "performance_metrics": self.performance_metrics,
            "current_resources": current_resources.__dict__ if current_resources else None,
            "scaling_history_count": len(self.scaling_history),
            "last_scaling": self.scaling_history[-1] if self.scaling_history else None
        }
    
    def save_scaling_history(self, filepath: str):
        """スケーリング履歴保存"""
        history_data = {
            "processor_config": {
                "initial_concurrency": self.current_concurrency,
                "strategy": self.strategy.__class__.__name__
            },
            "performance_summary": self.performance_metrics,
            "scaling_events": self.scaling_history,
            "resource_history": [r.__dict__ for r in self.resource_monitor.history],
            "timestamp": datetime.now().isoformat()
        }
        
        with open(filepath, "w") as f:
            json.dump(history_data, f, indent=2)
        
        logger.info(f"Scaling history saved to: {filepath}")


# 使用例とテスト
async def example_processor_function(item: Any) -> Any:
    """処理関数の例"""
    # 実際の処理をシミュレート
    processing_time = 0.1  # 100ms
    await asyncio.sleep(processing_time)
    return f"processed_{item}"


async def main():
    """メイン関数（テスト用）"""
    logging.basicConfig(level=logging.INFO)
    
    # 動的並列プロセッサーを作成
    processor = DynamicParallelProcessor(initial_concurrency=3)
    
    try:
        await processor.start()
        
        # テストデータ
        test_items = list(range(50))
        
        def progress_callback(completed, total):
            """progress_callbackメソッド"""
            print(f"Progress: {completed}/{total} ({completed/total*100:0.1f}%)")
        
        print("Starting parallel processing with dynamic scaling...")
        start_time = time.time()
        
        results = await processor.process_items(
            test_items,
            example_processor_function,
            progress_callback
        )
        
        end_time = time.time()
        
        print(f"\nProcessing completed in {end_time - start_time:0.2f} seconds")
        print(f"Results: {len([r for r in results if not isinstance(r, Exception)])} successful, "
              f"{len([r for r in results if isinstance(r, Exception)])} errors")
        
        # ステータス表示
        status = processor.get_status()
        print(f"\nFinal Status:")
        print(f"- Concurrency: {status['current_concurrency']}")
        print(f"- Processed: {status['processed_count']}")
        print(f"- Errors: {status['error_count']}")
        print(f"- Throughput: {status['performance_metrics'].get('throughput', 0):0.2f} items/sec")
        
        # 履歴保存
        processor.save_scaling_history("performance_results/scaling_history_test.json")
        
    finally:
        await processor.stop()


if __name__ == "__main__":
    asyncio.run(main())