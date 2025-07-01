#!/usr/bin/env python3
"""
ワーカー管理システムのテスト
"""
import sys
sys.path.append('/root/ai_co')

from libs.worker_monitor import WorkerMonitor
from libs.worker_controller import WorkerController
import json
import time

def test_monitoring():
    """監視機能のテスト"""
    print("=== 📊 監視機能テスト ===")
    monitor = WorkerMonitor()
    
    # メトリクス取得
    metrics = monitor.get_all_metrics()
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    
    print(f"\n📈 サマリー:")
    print(f"  キュー長: {metrics['queue_length']}")
    print(f"  稼働ワーカー数: {metrics['active_workers']}")
    print(f"  CPU使用率: {metrics['system']['cpu_percent']}%")
    print(f"  メモリ使用率: {metrics['system']['memory_percent']}%")

def test_control():
    """制御機能のテスト"""
    print("\n=== 🎮 制御機能テスト ===")
    controller = WorkerController()
    monitor = WorkerMonitor()
    
    # 現在の状態
    initial_workers = monitor.get_active_workers()
    print(f"初期ワーカー数: {len(initial_workers)}")
    
    # テストワーカー起動
    print("\n📌 テストワーカー (worker-99) を起動...")
    controller.start_worker("worker-99")
    time.sleep(3)
    
    # 確認
    workers = monitor.get_active_workers()
    test_worker = None
    for w in workers:
        if w['worker_id'] == 'worker-99':
            test_worker = w
            break
    
    if test_worker:
        print(f"✅ テストワーカー起動成功: PID={test_worker['pid']}")
        
        # 停止テスト
        print("\n📌 テストワーカーを停止...")
        controller.stop_worker("worker-99")
        time.sleep(2)
        
        workers = monitor.get_active_workers()
        still_running = any(w['worker_id'] == 'worker-99' for w in workers)
        if not still_running:
            print("✅ テストワーカー停止成功")
    else:
        print("❌ テストワーカー起動失敗")

if __name__ == "__main__":
    test_monitoring()
    test_control()
