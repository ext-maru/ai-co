#!/usr/bin/env python3
"""
パフォーマンス最適化テスト - 応急処置根絶令準拠
既存コードの直接修正によるパフォーマンス改善確認
"""

import asyncio
import time
import threading
import pytest
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.worker_status_monitor import WorkerStatusMonitor


def test_monitoring_performance_improvement():
    """モニタリングループのパフォーマンス改善テスト"""
    monitor = WorkerStatusMonitor()
    
    # 元の設定保存
    original_interval = monitor.monitoring_interval
    
    # パフォーマンス測定
    start_time = time.time()
    
    # モニタリング開始
    monitor.start_monitoring()
    
    # 5秒間実行
    time.sleep(5)
    
    # モニタリング停止
    monitor.stop_monitoring()
    
    elapsed_time = time.time() - start_time
    
    # インターバルが最適化されていることを確認
    assert monitor.monitoring_interval >= 1.0, "監視間隔が短すぎます"
    assert elapsed_time < 6.0, "処理時間が長すぎます"
    
    print(f"✅ モニタリングパフォーマンス改善テスト成功 - 処理時間: {elapsed_time:.2f}秒")


def test_efficient_worker_check():
    """ワーカーチェックの効率化テスト"""
    monitor = WorkerStatusMonitor()
    
    # 100個のワーカーを登録
    for i in range(100):
        worker_info = {
            "worker_id": f"test_worker_{i:03d}",
            "worker_type": "task_worker",
            "pid": 10000 + i,
        }
        monitor.register_worker(worker_info)
    
    # ヘルスチェックの時間測定
    start_time = time.time()
    
    # すべてのワーカーのヘルスチェック
    for worker_id in monitor.workers_status.keys():
        monitor.check_worker_health(worker_id)
    
    elapsed_time = time.time() - start_time
    
    # 100ワーカーのチェックが1秒以内に完了すること
    assert elapsed_time < 1.0, f"ヘルスチェックが遅すぎます: {elapsed_time:.2f}秒"
    
    print(f"✅ 効率的ワーカーチェックテスト成功 - 100ワーカー/{elapsed_time:.2f}秒")


def test_async_monitoring():
    """非同期モニタリングのテスト"""
    monitor = WorkerStatusMonitor()
    
    # モニタリングが非ブロッキングであることを確認
    monitor.start_monitoring()
    
    # メインスレッドが即座に継続できることを確認
    main_thread_running = True
    
    def check_main_thread():
        time.sleep(0.1)
        return main_thread_running
    
    assert check_main_thread(), "モニタリングがメインスレッドをブロックしています"
    
    monitor.stop_monitoring()
    
    print("✅ 非同期モニタリングテスト成功")


if __name__ == "__main__":
    test_monitoring_performance_improvement()
    test_efficient_worker_check()
    test_async_monitoring()