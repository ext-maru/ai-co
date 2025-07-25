#!/usr/bin/env python3
"""
Tests for PID Lock Manager
==========================

PIDロック管理システムのテストスイート。
マルチプロセス環境での正しい動作を保証します。

Author: Claude Elder
Created: 2025-01-19
"""

import os
import sys
import json
import time

import multiprocessing
from pathlib import Path
import pytest
import psutil

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.elder_system.flow.pid_lock_manager import PIDLockManager, PIDLockContext

class TestPIDLockManager:
    """PIDロック管理システムのテストケース"""
    
    @pytest.fixture
    def lock_manager(self):
        """テスト用の一時ディレクトリを使用するロックマネージャー"""

            yield PIDLockManager(lock_dir=tmpdir)
            
    def test_acquire_and_release_lock(self, lock_manager):
        """ロックの取得と解放の基本動作をテスト"""
        task_id = "test_task_1"
        
        # ロックを取得
        assert lock_manager.acquire_lock(task_id) is True
        
        # 同じタスクのロックを再度取得しようとすると失敗
        assert lock_manager.acquire_lock(task_id) is False
        
        # ロックを解放
        assert lock_manager.release_lock(task_id) is True
        
        # 解放後は再度取得可能
        assert lock_manager.acquire_lock(task_id) is True
        
    def test_lock_with_task_info(self, lock_manager):
        """タスク情報付きロックのテスト"""
        task_id = "test_task_with_info"
        task_info = {
            "description": "Test task",
            "priority": "high",
            "user": "test_user"
        }
        
        # タスク情報付きでロック取得
        assert lock_manager.acquire_lock(task_id, task_info) is True
        
        # ロック情報を確認
        lock_info = lock_manager.is_task_locked(task_id)
        assert lock_info is not None
        assert lock_info['task_info'] == task_info
        
    def test_stale_lock_cleanup(self, lock_manager):
        """古いロックのクリーンアップテスト"""
        task_id = "stale_task"
        
        # 偽のロックファイルを作成（存在しないPID）
        lock_file = lock_manager._get_lock_file_path(task_id)
        fake_lock_data = {
            'pid': 99999999,  # 存在しないPID
            'task_id': task_id,
            'started_at': '2025-01-01T00:00:00'
        }
        
        with open(lock_file, 'w') as f:
            json.dump(fake_lock_data, f)
            
        # 古いロックがあっても新しいロックを取得できることを確認
        assert lock_manager.acquire_lock(task_id) is True
        
    def test_cleanup_stale_locks(self, lock_manager):
        """複数の古いロックのクリーンアップテスト"""
        # 複数の偽ロックを作成
        for i in range(5):
            task_id = f"stale_task_{i}"
            lock_file = lock_manager._get_lock_file_path(task_id)
            fake_lock_data = {
                'pid': 99999990 + i,  # 存在しないPID
                'task_id': task_id,
                'started_at': '2025-01-01T00:00:00'
            }
            with open(lock_file, 'w') as f:
                json.dump(fake_lock_data, f)
                
        # クリーンアップ実行
        cleaned = lock_manager.cleanup_stale_locks()
        assert cleaned == 5
        
    def test_context_manager(self, lock_manager):
        """コンテキストマネージャーとしての使用テスト"""
        task_id = "context_test"
        
        # コンテキストマネージャーでロック取得
        with PIDLockContext(lock_manager, task_id):
            # ロックが取得されていることを確認
            assert lock_manager.is_task_locked(task_id) is not None
            
        # コンテキストを抜けたらロックが解放されていることを確認
        assert lock_manager.is_task_locked(task_id) is None
        
    def test_context_manager_exception(self, lock_manager):
        """例外発生時のコンテキストマネージャーの動作テスト"""
        task_id = "context_exception_test"
        
        try:
            with PIDLockContext(lock_manager, task_id):
                # ロックが取得されていることを確認
                assert lock_manager.is_task_locked(task_id) is not None
                # 意図的に例外を発生
                raise ValueError("Test exception")
        except ValueError:
            pass
            
        # 例外が発生してもロックが解放されていることを確認
        assert lock_manager.is_task_locked(task_id) is None
        
    def test_active_tasks_listing(self, lock_manager):
        """アクティブタスクのリスト取得テスト"""
        # 複数のタスクのロックを取得
        task_ids = ["task_1", "task_2", "task_3"]
        for task_id in task_ids:
            assert lock_manager.acquire_lock(task_id) is True
            
        # アクティブタスクのリストを取得
        active_tasks = lock_manager.get_active_tasks()
        assert len(active_tasks) == 3
        assert all(task_id in active_tasks for task_id in task_ids)
        
    def test_different_process_cannot_release(self, lock_manager):
        """異なるプロセスからのロック解放を防ぐテスト"""
        task_id = "cross_process_test"
        
        # ロックを取得
        assert lock_manager.acquire_lock(task_id) is True
        
        # PIDを一時的に変更（異なるプロセスをシミュレート）
        original_pid = lock_manager.current_pid
        lock_manager.current_pid = 99999
        
        # 異なるPIDからは解放できない
        assert lock_manager.release_lock(task_id) is False
        
        # 元のPIDに戻す
        lock_manager.current_pid = original_pid
        
        # 元のPIDからは解放できる
        assert lock_manager.release_lock(task_id) is True
        
    def test_special_characters_in_task_id(self, lock_manager):
        """タスクIDに特殊文字が含まれる場合のテスト"""
        special_task_ids = [
            "task/with/slashes",
            "task with spaces",
            "task-with-dashes",
            "task_with_underscores",
            "task.with.dots"
        ]
        
        for task_id in special_task_ids:
            assert lock_manager.acquire_lock(task_id) is True
            assert lock_manager.release_lock(task_id) is True

def test_multiprocess_lock_behavior():
    """マルチプロセス環境でのロック動作をテスト"""
    
    def worker_process(lock_dir, task_id, result_queue):
        """ワーカープロセスがロック取得を試みる"""
        lock_manager = PIDLockManager(lock_dir=lock_dir)
        acquired = lock_manager.acquire_lock(task_id)
        result_queue.put(acquired)
        
        if acquired:
            # ロックを取得できた場合は少し待ってから解放
            time.sleep(0.5)
            lock_manager.release_lock(task_id)

        task_id = "multiprocess_test"
        result_queue = multiprocessing.Queue()
        
        # 5つのプロセスを同時に起動
        processes = []
        for i in range(5):
            p = multiprocessing.Process(
                target=worker_process,
                args=(tmpdir, task_id, result_queue)
            )
            p.start()
            processes.append(p)
            
        # すべてのプロセスの終了を待つ
        for p in processes:
            p.join()
            
        # 結果を集計
        results = []
        while not result_queue.empty():
            results.append(result_queue.get())
            
        # 1つのプロセスのみがロックを取得できたことを確認
        assert sum(results) == 1
        assert results.count(True) == 1
        assert results.count(False) == 4

if __name__ == "__main__":
    pytest.main([__file__, "-v"])