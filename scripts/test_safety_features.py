#!/usr/bin/env python3
"""
安全機能の統合テスト
"""
import sys
import os
import signal
import time
sys.path.append('/root/ai_co')

from libs.worker_controller import WorkerController
from libs.health_checker import HealthChecker
from libs.worker_monitor import WorkerMonitor

def test_graceful_shutdown():
    """Graceful Shutdownのテスト"""
    print("=== 🛑 Graceful Shutdown テスト ===")
    controller = WorkerController()
    monitor = WorkerMonitor()
    
    # テストワーカー起動
    print("📌 テストワーカー (worker-test) 起動...")
    controller.start_worker("worker-test")
    time.sleep(3)
    
    # ワーカーを探す
    workers = monitor.get_active_workers()
    test_worker = None
    for w in workers:
        if w['worker_id'] == 'worker-test':
            test_worker = w
            break
    
    if test_worker:
        print(f"✅ テストワーカー起動確認: PID={test_worker['pid']}")
        
        # SIGTERM送信
        print("📤 SIGTERM送信...")
        os.kill(test_worker['pid'], signal.SIGTERM)
        
        # 終了待機
        for i in range(10):
            time.sleep(1)
            try:
                os.kill(test_worker['pid'], 0)
                print(f"⏳ 終了待機中... {i+1}秒")
            except ProcessLookupError:
                print("✅ Graceful Shutdown成功")
                break
    else:
        print("❌ テストワーカーが見つかりません")

def test_health_check():
    """ヘルスチェックのテスト"""
    print("\n=== 🏥 ヘルスチェック テスト ===")
    checker = HealthChecker()
    monitor = WorkerMonitor()
    
    workers = monitor.get_active_workers()
    print(f"📊 アクティブワーカー数: {len(workers)}")
    
    for worker in workers[:2]:  # 最初の2つをテスト
        health = checker.check_worker_health(worker)
        print(f"\n{worker['worker_id']} ヘルスチェック:")
        print(f"  健康状態: {'✅ 健康' if health['healthy'] else '❌ 不健康'}")
        print(f"  CPU: {health.get('cpu_percent', 'N/A')}%")
        print(f"  メモリ: {health.get('memory_percent', 'N/A')}%")
        if not health['healthy']:
            print(f"  問題: {', '.join(health.get('issues', []))}")

def test_auto_recovery():
    """自動復旧のテスト"""
    print("\n=== 🔄 自動復旧テスト ===")
    checker = HealthChecker()
    
    # 擬似的に不健康状態を作成
    test_worker_id = "worker-test-unhealthy"
    
    # 連続して不健康と判定
    for i in range(4):
        checker._record_unhealthy(test_worker_id, {
            'issues': ['テスト用の不健康状態']
        })
        print(f"📌 不健康記録 {i+1}回目")
        
        should_restart = checker.should_restart_worker(test_worker_id)
        print(f"  再起動判定: {should_restart}")
        
        if should_restart:
            print("✅ 再起動閾値に到達")
            checker.record_restart(test_worker_id)
            break

if __name__ == "__main__":
    # 各テストを実行
    test_graceful_shutdown()
    test_health_check()
    test_auto_recovery()
    
    print("\n=== ✅ 安全機能テスト完了 ===")
