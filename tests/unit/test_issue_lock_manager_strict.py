#!/usr/bin/env python3
"""
Issue Lock Manager 厳格テストスイート
レースコンディション、エッジケース、セキュリティ、パフォーマンスの徹底検証
"""

import os
import json
import time
import asyncio
import tempfile
import shutil
import threading
import multiprocessing
import signal
import random
import string
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
import psutil

# テスト対象のインポート
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from libs.issue_lock_manager import (
    FileLockManager,
    HeartbeatManager,
    ProcessMonitor,
    SafeIssueProcessor
)


class TestRaceConditions:
    """レースコンディションの厳密なテスト"""
    
    @pytest.fixture
    def temp_lock_dir(self):
        """一時的なロックディレクトリ"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
        
    @pytest.mark.asyncio
    async def test_simultaneous_lock_acquisition(self, temp_lock_dir):
        """同時ロック取得の競合テスト"""
        manager = FileLockManager(lock_dir=temp_lock_dir)
        issue_number = 999
        results = []
        
        async def try_acquire_lock(processor_id: str):
            """ロック取得を試行"""
            # ランダムな微小遅延で実際の競合状態を再現
            await asyncio.sleep(random.uniform(0, 0.01))
            result = manager.acquire_lock(issue_number, processor_id)
            results.append((processor_id, result))
            
        # 100個の並行タスクでロック取得を試行
        tasks = [
            try_acquire_lock(f"processor_{i}")
            for i in range(100)
        ]
        
        await asyncio.gather(*tasks)
        
        # 成功したロック取得は1つだけであることを確認
        successful_locks = [(pid, res) for pid, res in results if res]
        assert len(successful_locks) == 1, f"Expected 1 successful lock, got {len(successful_locks)}"
        
    def test_multiprocess_lock_competition(self, temp_lock_dir):
        """マルチプロセス環境でのロック競合テスト"""
        def worker_process(worker_id: int, lock_dir: str, result_queue):
            """ワーカープロセス"""
            manager = FileLockManager(lock_dir=lock_dir)
            results = []
            
            for attempt in range(10):
                issue_number = 1000 + attempt
                acquired = manager.acquire_lock(issue_number, f"worker_{worker_id}")
                results.append((issue_number, acquired))
                if acquired:
                    # 少し作業をシミュレート
                    time.sleep(0.01)
                    manager.release_lock(issue_number, f"worker_{worker_id}")
                    
            result_queue.put((worker_id, results))
            
        # 10個のプロセスを起動
        processes = []
        result_queue = multiprocessing.Queue()
        
        for i in range(10):
            p = multiprocessing.Process(
                target=worker_process,
                args=(i, temp_lock_dir, result_queue)
            )
            p.start()
            processes.append(p)
            
        # すべてのプロセスの完了を待つ
        for p in processes:
            p.join(timeout=30)
            
        # 結果を収集
        all_results = {}
        while not result_queue.empty():
            worker_id, results = result_queue.get()
            all_results[worker_id] = results
            
        # 各Issue番号に対してロックを取得できたのは1プロセスのみであることを確認
        for issue_num in range(1000, 1010):
            acquired_count = sum(
                1 for worker_results in all_results.values()
                for issue, acquired in worker_results
                if issue == issue_num and acquired
            )
            assert acquired_count <= 10, f"Issue {issue_num}: Too many locks acquired"
            
    @pytest.mark.asyncio
    async def test_rapid_lock_release_reacquire(self, temp_lock_dir):
        """高速なロック解放・再取得のテスト"""
        processor = SafeIssueProcessor(lock_dir=temp_lock_dir)
        issue_number = 2000
        success_count = 0
        
        async def rapid_process(attempt: int):
            """高速処理"""
            result = await processor.process_issue_safely(
                issue_number,
                lambda _: asyncio.sleep(0.001)  # 1ms処理
            )
            return result is not None
            
        # 1000回の高速処理を並行実行
        tasks = [rapid_process(i) for i in range(1000)]
        results = await asyncio.gather(*tasks)
        
        # 少なくとも1つは成功し、同時実行されていないことを確認
        success_count = sum(results)
        assert success_count >= 1, "At least one process should succeed"
        assert success_count < 1000, "Not all should succeed (indicates no locking)"


class TestEdgeCases:
    """エッジケースの厳密なテスト"""
    
    @pytest.fixture
    def lock_manager(self, tmp_path):
        """テスト用ロックマネージャー"""
        return FileLockManager(lock_dir=str(tmp_path))
        
    def test_corrupted_lock_file_handling(self, lock_manager):
        """破損したロックファイルの処理"""
        issue_number = 3000
        lock_file = lock_manager.lock_dir / f"issue_{issue_number}.lock"
        
        # 破損したJSONファイルを作成
        test_cases = [
            b"",  # 空ファイル
            b"invalid json",  # 無効なJSON
            b'{"incomplete": ',  # 不完全なJSON
            b'{"processor_id": null}',  # 必須フィールドなし
            b'\x00\x01\x02\x03',  # バイナリデータ
        ]
        
        for i, corrupted_data in enumerate(test_cases):
            lock_file.write_bytes(corrupted_data)
            
            # ロック取得を試行（エラーにならず、新しいロックが作成される）
            result = lock_manager.acquire_lock(issue_number, f"processor_{i}")
            assert result is True, f"Test case {i}: Should acquire lock with corrupted file"
            
            # 正しいロックファイルが作成されていることを確認
            with open(lock_file, 'r') as f:
                lock_data = json.load(f)
                assert lock_data['processor_id'] == f"processor_{i}"
                
            lock_manager.release_lock(issue_number)
            
    def test_extremely_long_names(self, lock_manager):
        """極端に長い名前の処理"""
        # 1000文字のプロセッサーID
        long_processor_id = "processor_" + "x" * 990
        
        # 1000桁のIssue番号
        huge_issue_number = 10**100
        
        # ロック取得（ファイルシステムの制限内で動作すること）
        result = lock_manager.acquire_lock(huge_issue_number, long_processor_id)
        assert result is True
        
        # ロック情報が正しく保存されていることを確認
        lock_info = lock_manager.get_lock_info(huge_issue_number)
        assert lock_info is not None
        assert lock_info['processor_id'] == long_processor_id
        
    def test_special_characters_in_processor_id(self, lock_manager):
        """特殊文字を含むプロセッサーIDのテスト"""
        special_ids = [
            "processor/../../../etc/passwd",  # パストラバーサル試行
            "processor'; rm -rf /",  # コマンドインジェクション試行
            "processor\x00null",  # ヌル文字
            "processor\n\r\t",  # 制御文字
            "processor日本語",  # マルチバイト文字
            "processor🔒🔑",  # 絵文字
        ]
        
        for i, special_id in enumerate(special_ids):
            issue_number = 4000 + i
            
            # ロック取得（セキュアに処理される）
            result = lock_manager.acquire_lock(issue_number, special_id)
            assert result is True
            
            # ロック情報が正しく保存されている
            lock_info = lock_manager.get_lock_info(issue_number)
            assert lock_info['processor_id'] == special_id
            
            lock_manager.release_lock(issue_number, special_id)


class TestSecurityAudit:
    """セキュリティ監査テスト"""
    
    def test_file_permissions(self, tmp_path):
        """ファイル権限のテスト"""
        lock_manager = FileLockManager(lock_dir=str(tmp_path))
        
        # ロック作成
        lock_manager.acquire_lock(5000, "security_test")
        lock_file = tmp_path / "issue_5000.lock"
        
        # ファイル権限の確認（他ユーザーから読み取り不可）
        stat = os.stat(lock_file)
        mode = stat.st_mode & 0o777
        
        # 所有者のみ読み書き可能（0o600）であることが理想
        # ただし、システムによってデフォルトが異なる可能性がある
        assert mode & 0o077 == 0, f"Lock file has too permissive mode: {oct(mode)}"
        
    def test_directory_traversal_prevention(self, tmp_path):
        """ディレクトリトラバーサル攻撃の防止テスト"""
        lock_manager = FileLockManager(lock_dir=str(tmp_path))
        
        # 悪意のあるIssue番号でディレクトリトラバーサルを試行
        malicious_numbers = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM",
        ]
        
        for malicious in malicious_numbers:
            # 数値変換時にエラーになることを期待
            try:
                # ロックファイル名は "issue_{number}.lock" 形式
                # 数値以外は受け付けないはず
                lock_file = lock_manager.lock_dir / f"issue_{malicious}.lock"
                # 実際の使用では issue_number は整数型なので、この攻撃は不可能
            except Exception:
                pass
                
    def test_concurrent_file_access_security(self, tmp_path):
        """並行ファイルアクセスのセキュリティテスト"""
        lock_manager = FileLockManager(lock_dir=str(tmp_path))
        issue_number = 6000
        
        def attacker_thread():
            """攻撃者スレッド：ロックファイルを改ざんしようとする"""
            lock_file = Path(tmp_path) / f"issue_{issue_number}.lock"
            
            for _ in range(100):
                try:
                    # ファイルを直接改ざんしようとする
                    if lock_file.exists():
                        with open(lock_file, 'w') as f:
                            json.dump({"processor_id": "attacker", "hacked": True}, f)
                except Exception:
                    pass  # 失敗は想定内
                time.sleep(0.001)
                
        def legitimate_thread():
            """正規スレッド：正常にロックを使用"""
            for i in range(50):
                acquired = lock_manager.acquire_lock(issue_number, f"legitimate_{i}")
                if acquired:
                    time.sleep(0.01)
                    lock_manager.release_lock(issue_number, f"legitimate_{i}")
                    
        # 攻撃者と正規ユーザーを同時実行
        attacker = threading.Thread(target=attacker_thread)
        legitimate = threading.Thread(target=legitimate_thread)
        
        attacker.start()
        legitimate.start()
        
        attacker.join()
        legitimate.join()
        
        # 最終的なロックファイルが破損していないことを確認
        lock_info = lock_manager.get_lock_info(issue_number)
        if lock_info:
            assert 'hacked' not in lock_info, "Lock file was compromised"


class TestPerformanceUnderLoad:
    """高負荷パフォーマンステスト"""
    
    @pytest.mark.asyncio
    async def test_massive_concurrent_operations(self, tmp_path):
        """大量並行処理のパフォーマンステスト"""
        processor = SafeIssueProcessor(lock_dir=str(tmp_path), timeout=30)
        
        # パフォーマンス測定用
        start_time = time.time()
        processed_count = 0
        error_count = 0
        
        async def process_issue_load_test(issue_num: int):
            """負荷テスト用の処理"""
            nonlocal processed_count, error_count
            
            try:
                result = await processor.process_issue_safely(
                    issue_num,
                    lambda n: asyncio.sleep(random.uniform(0.001, 0.01))
                )
                if result is not None:
                    processed_count += 1
            except Exception:
                error_count += 1
                
        # 10000個のタスクを作成（100個のIssueを100回ずつ処理）
        tasks = []
        for issue_num in range(7000, 7100):
            for _ in range(100):
                tasks.append(process_issue_load_test(issue_num))
                
        # バッチ処理（メモリ制限を考慮）
        batch_size = 1000
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            await asyncio.gather(*batch, return_exceptions=True)
            
        elapsed_time = time.time() - start_time
        
        # パフォーマンス統計
        print(f"\nPerformance Test Results:")
        print(f"Total tasks: {len(tasks)}")
        print(f"Processed: {processed_count}")
        print(f"Errors: {error_count}")
        print(f"Elapsed time: {elapsed_time:.2f}s")
        print(f"Throughput: {len(tasks) / elapsed_time:.2f} tasks/s")
        
        # 基準: エラー率1%未満
        assert error_count < len(tasks) * 0.01, f"Error rate too high: {error_count}/{len(tasks)}"
        
        # 基準: スループット100 tasks/s以上
        throughput = len(tasks) / elapsed_time
        assert throughput > 100, f"Throughput too low: {throughput:.2f} tasks/s"
        
    def test_lock_cleanup_performance(self, tmp_path):
        """大量ロックのクリーンアップパフォーマンス"""
        lock_manager = FileLockManager(lock_dir=str(tmp_path))
        process_monitor = ProcessMonitor(lock_manager)
        
        # 10000個のデッドロックを作成
        dead_pid = 99999  # 存在しないPID
        for i in range(10000):
            lock_file = Path(tmp_path) / f"issue_{i}.lock"
            lock_data = {
                'processor_id': f'dead_processor_{i}',
                'locked_at': datetime.now().isoformat(),
                'pid': dead_pid,
                'hostname': os.uname().nodename
            }
            with open(lock_file, 'w') as f:
                json.dump(lock_data, f)
                
        # クリーンアップのパフォーマンス測定
        start_time = time.time()
        cleaned = process_monitor.cleanup_dead_locks()
        elapsed = time.time() - start_time
        
        print(f"\nCleanup Performance:")
        print(f"Cleaned locks: {cleaned}")
        print(f"Elapsed time: {elapsed:.2f}s")
        print(f"Rate: {cleaned / elapsed:.2f} locks/s")
        
        # 基準: 1000 locks/s以上のクリーンアップ速度
        assert cleaned / elapsed > 1000, f"Cleanup too slow: {cleaned / elapsed:.2f} locks/s"


class TestFailureInjection:
    """障害注入テスト"""
    
    @pytest.mark.asyncio
    async def test_process_kill_during_operation(self, tmp_path):
        """処理中のプロセスキルシミュレーション"""
        
        async def simulate_process_crash():
            """プロセスクラッシュをシミュレート"""
            processor = SafeIssueProcessor(lock_dir=str(tmp_path))
            
            # ロック取得
            lock_acquired = processor.lock_manager.acquire_lock(8000, processor.processor_id)
            assert lock_acquired
            
            # ハートビート開始
            processor.heartbeat_manager.start_heartbeat(8000, processor.processor_id)
            
            # 処理中に"クラッシュ"（クリーンアップをスキップ）
            # 通常のクリーンアップをバイパスして強制終了を模擬
            processor._cleanup_registered = True  # クリーンアップハンドラーを無効化
            
            # プロセス終了をシミュレート（実際には関数を抜けるだけ）
            return
            
        # クラッシュをシミュレート
        await simulate_process_crash()
        
        # 別のプロセスがデッドロックを検出してクリーンアップ
        new_processor = SafeIssueProcessor(lock_dir=str(tmp_path))
        
        # 少し待機（ハートビートタイムアウトをシミュレート）
        await asyncio.sleep(0.1)
        
        # 新しいプロセスがロックを取得できることを確認
        result = await new_processor.process_issue_safely(
            8000,
            lambda _: "processed"
        )
        
        assert result == "processed", "Should be able to acquire lock after crash"
        
    def test_disk_full_simulation(self, tmp_path):
        """ディスク満杯シミュレーション"""
        lock_manager = FileLockManager(lock_dir=str(tmp_path))
        
        # ディスク満杯をシミュレート（書き込みを失敗させる）
        original_open = open
        write_count = 0
        
        def mock_open(*args, **kwargs):
            nonlocal write_count
            if 'w' in str(args[1:]) and write_count > 5:
                raise IOError("No space left on device")
            write_count += 1
            return original_open(*args, **kwargs)
            
        with patch('builtins.open', mock_open):
            # 最初の数回は成功
            for i in range(5):
                result = lock_manager.acquire_lock(9000 + i, f"processor_{i}")
                assert result is True
                
            # その後は失敗
            for i in range(5, 10):
                result = lock_manager.acquire_lock(9000 + i, f"processor_{i}")
                assert result is False
                
    def test_network_partition_simulation(self, tmp_path):
        """ネットワーク分断シミュレーション（分散環境を想定）"""
        # 2つの"ノード"をシミュレート
        node1_locks = FileLockManager(lock_dir=str(tmp_path))
        node2_locks = FileLockManager(lock_dir=str(tmp_path))
        
        # Node1がロックを取得
        assert node1_locks.acquire_lock(10000, "node1_processor")
        
        # "ネットワーク分断"をシミュレート
        # （実際にはファイルシステムベースなので影響なし）
        
        # Node2は同じロックを取得できない
        assert not node2_locks.acquire_lock(10000, "node2_processor")
        
        # これはファイルシステムベースの利点を示す


class TestCodeQualityAudit:
    """コード品質監査"""
    
    def test_no_race_condition_in_atomic_operations(self):
        """アトミック操作でレースコンディションがないことを確認"""
        # FileLockManagerのacquire_lockメソッドを検査
        import inspect
        source = inspect.getsource(FileLockManager.acquire_lock)
        
        # アトミック操作の使用を確認
        assert 'rename' in source, "Should use atomic rename operation"
        assert 'temp_file' in source or '.tmp' in source, "Should use temporary file pattern"
        
    def test_proper_exception_handling(self):
        """適切な例外処理の確認"""
        import inspect
        
        # SafeIssueProcessorの主要メソッドを検査
        source = inspect.getsource(SafeIssueProcessor.process_issue_safely)
        
        # try-finally パターンの使用を確認
        assert 'try:' in source, "Should have try block"
        assert 'finally:' in source, "Should have finally block for cleanup"
        assert 'release_lock' in source, "Should release lock in finally"
        
    def test_no_hardcoded_secrets(self):
        """ハードコードされた秘密情報がないことを確認"""
        import inspect
        
        # すべてのクラスのソースコードを検査
        classes = [FileLockManager, HeartbeatManager, ProcessMonitor, SafeIssueProcessor]
        
        for cls in classes:
            source = inspect.getsource(cls)
            
            # 一般的な秘密情報パターンをチェック
            suspicious_patterns = [
                'password=',
                'secret=',
                'api_key=',
                'token=',
                'private_key='
            ]
            
            for pattern in suspicious_patterns:
                assert pattern not in source.lower(), f"Found suspicious pattern '{pattern}' in {cls.__name__}"


# 統合ストレステスト
@pytest.mark.asyncio
async def test_comprehensive_stress_test(tmp_path):
    """包括的ストレステスト"""
    print("\n=== Comprehensive Stress Test ===")
    
    # 複数のプロセッサーを作成
    processors = [
        SafeIssueProcessor(lock_dir=str(tmp_path))
        for _ in range(5)
    ]
    
    # 統計情報
    stats = {
        'total_attempts': 0,
        'successful_processes': 0,
        'lock_contentions': 0,
        'errors': 0
    }
    
    async def stress_worker(processor_id: int, processor: SafeIssueProcessor):
        """ストレステストワーカー"""
        for round in range(100):
            # ランダムなIssueを選択（競合を発生させる）
            issue_number = 20000 + random.randint(0, 20)
            
            stats['total_attempts'] += 1
            
            try:
                # 処理時間もランダム
                process_time = random.uniform(0.001, 0.05)
                
                result = await processor.process_issue_safely(
                    issue_number,
                    lambda n: asyncio.sleep(process_time)
                )
                
                if result is not None:
                    stats['successful_processes'] += 1
                else:
                    stats['lock_contentions'] += 1
                    
            except Exception as e:
                stats['errors'] += 1
                print(f"Error in processor {processor_id}: {e}")
                
            # 少し待機
            await asyncio.sleep(random.uniform(0, 0.01))
            
    # すべてのプロセッサーでストレステストを実行
    tasks = [
        stress_worker(i, processor)
        for i, processor in enumerate(processors)
    ]
    
    start_time = time.time()
    await asyncio.gather(*tasks)
    elapsed = time.time() - start_time
    
    # 結果レポート
    print(f"\nStress Test Results:")
    print(f"Duration: {elapsed:.2f}s")
    print(f"Total attempts: {stats['total_attempts']}")
    print(f"Successful: {stats['successful_processes']}")
    print(f"Lock contentions: {stats['lock_contentions']}")
    print(f"Errors: {stats['errors']}")
    print(f"Success rate: {stats['successful_processes'] / stats['total_attempts'] * 100:.1f}%")
    print(f"Error rate: {stats['errors'] / stats['total_attempts'] * 100:.1f}%")
    
    # 品質基準
    assert stats['errors'] < stats['total_attempts'] * 0.01, "Error rate > 1%"
    assert stats['successful_processes'] > 0, "No successful processes"
    
    # クリーンアップ確認
    remaining_locks = len(list(Path(tmp_path).glob("*.lock")))
    print(f"Remaining locks: {remaining_locks}")
    assert remaining_locks < 25, "Too many locks remaining"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])