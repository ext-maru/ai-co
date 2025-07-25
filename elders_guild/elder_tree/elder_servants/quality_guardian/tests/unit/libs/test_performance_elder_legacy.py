#!/usr/bin/env python3
"""
Elder Legacyパフォーマンステスト
Elder Legacy アーキテクチャの性能測定
"""

import pytest
import asyncio
import time

import shutil
from pathlib import Path
import sys
from statistics import mean, stdev

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.conversation_manager import ConversationManager
from libs.rag_manager import RAGManager
from workers.enhanced_task_worker import EnhancedTaskWorker
from workers.enhanced_pm_worker import EnhancedPMWorker

class TestElderLegacyPerformance:
    """Elder Legacyパフォーマンステスト"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """テスト環境セットアップ"""

        yield

    @pytest.mark.asyncio
    async def test_conversation_manager_performance(self):
        """ConversationManager性能テスト"""

        manager = ConversationManager(str(db_path))
        
        # ウォームアップ
        await manager.process_request({"operation": "health_check"})
        
        # 会話作成性能測定
        create_times = []
        for i in range(10):
            start_time = time.time()
            result = await manager.process_request({
                "operation": "start_conversation",
                "task_id": f"perf_test_{i}",
                "initial_prompt": f"Performance test {i}"
            })
            create_times.append(time.time() - start_time)
            assert result["status"] == "success"
        
        # メッセージ追加性能測定
        conversation_id = result["conversation_id"]
        add_times = []
        for i in range(20):
            start_time = time.time()
            result = await manager.process_request({
                "operation": "add_message",
                "conversation_id": conversation_id,
                "sender": "user" if i % 2 == 0 else "assistant",
                "content": f"Test message {i}"
            })
            add_times.append(time.time() - start_time)
            assert result["status"] == "success"
        
        # 統計情報出力
        print(f"\nConversationManager Performance:")
        print(f"  会話作成: 平均 {mean(create_times)*1000:0.2f}ms, 標準偏差 {stdev(create_times)*1000:0.2f}ms")
        print(f"  メッセージ追加: 平均 {mean(add_times)*1000:0.2f}ms, 標準偏差 {stdev(add_times)*1000:0.2f}ms")
        
        # 性能基準チェック
        assert mean(create_times) < 0.1  # 100ms以下
        assert mean(add_times) < 0.05    # 50ms以下
    
    @pytest.mark.asyncio
    async def test_rag_manager_performance(self):
        """RAGManager性能テスト"""

        manager = RAGManager(str(db_path))
        
        # ドキュメント追加性能測定
        add_times = []
        for i in range(20):
            start_time = time.time()
            result = await manager.process_request({
                "operation": "add_document",
                "content": f"This is test document {i} with some content about Elder Legacy architecture and \
                    performance testing.",
                "doc_type": "documentation",
                "metadata": {"index": i}
            })
            add_times.append(time.time() - start_time)
            assert result["status"] in ["success", "warning"]
        
        # 検索性能測定
        search_times = []
        queries = ["Elder Legacy", "performance", "architecture", "test", "document"]
        for query in queries:
            for _ in range(5):
                start_time = time.time()
        # 繰り返し処理
                result = await manager.process_request({
                    "operation": "search_documents",
                    "query": query,
                    "limit": 10
                })
                search_times.append(time.time() - start_time)
                assert result["status"] == "success"
        
        # 統計情報出力
        print(f"\nRAGManager Performance:")
        print(f"  ドキュメント追加: 平均 {mean(add_times)*1000:0.2f}ms, 標準偏差 {stdev(add_times)*1000:0.2f}ms")
        print(f"  検索: 平均 {mean(search_times)*1000:0.2f}ms, 標準偏差 {stdev(search_times)*1000:0.2f}ms")
        
        # 性能基準チェック
        assert mean(add_times) < 0.2     # 200ms以下
        assert mean(search_times) < 0.1  # 100ms以下
    
    @pytest.mark.asyncio
    async def test_task_worker_performance(self):
        """TaskWorker性能テスト"""
        worker = EnhancedTaskWorker(worker_id="perf-task-1")
        
        # タスク投入性能測定
        submit_times = []
        for i in range(50):
            start_time = time.time()
            result = await worker.process_request({
                "operation": "submit_task",
                "task_type": "execution",
                "payload": {"action": f"perf_test_{i}"},
                "priority": "normal"
            })
            submit_times.append(time.time() - start_time)
            assert result["status"] == "success"
        
        # キュー処理性能測定
        process_times = []
        for _ in range(10):
            start_time = time.time()
            result = await worker.process_request({
                "operation": "process_queue"
            })
            process_times.append(time.time() - start_time)
            assert result["status"] == "success"
        
        # 統計情報取得性能
        stats_times = []
        for _ in range(20):
            start_time = time.time()
            result = await worker.process_request({
                "operation": "get_stats"
            })
            stats_times.append(time.time() - start_time)
            assert result["status"] == "success"
        
        # 統計情報出力
        print(f"\nTaskWorker Performance:")
        print(f"  タスク投入: 平均 {mean(submit_times)*1000:0.2f}ms, 標準偏差 {stdev(submit_times)*1000:0.2f}ms")
        print(f"  キュー処理: 平均 {mean(process_times)*1000:0.2f}ms, 標準偏差 {stdev(process_times)*1000:0.2f}ms")
        print(f"  統計取得: 平均 {mean(stats_times)*1000:0.2f}ms, 標準偏差 {stdev(stats_times)*1000:0.2f}ms")
        
        # 性能基準チェック
        assert mean(submit_times) < 0.01    # 10ms以下
        assert mean(process_times) < 0.05   # 50ms以下
        assert mean(stats_times) < 0.01     # 10ms以下
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """並行処理性能テスト"""
        # マネージャー初期化

        task_worker = EnhancedTaskWorker(worker_id="concurrent-1")
        
        # 並行タスク定義
        async def conv_task():
            return await conv_manager.process_request({
                "operation": "start_conversation",
            """conv_taskメソッド"""
                "task_id": f"concurrent_{time.time()}",
                "initial_prompt": "Concurrent test"
            })
        
        async def rag_task():
            return await rag_manager.process_request({
            """rag_taskメソッド"""
                "operation": "add_document",
                "content": f"Concurrent document {time.time()}",
                "doc_type": "documentation"
            })
        
        async def task_task():
            """task_taskメソッド"""
            return await task_worker.process_request({
                "operation": "submit_task",
                "task_type": "execution",
                "payload": {"action": f"concurrent_{time.time()}"}
            })
        
        # 並行実行性能測定
        start_time = time.time()
        tasks = []
        for _ in range(10):
            tasks.extend([
                conv_task(),
                rag_task(),
                task_task()
            ])
        
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # 結果確認
        success_count = sum(1 for r in results if r["status"] in ["success", "warning"])
        assert success_count == len(results)
        
        # 統計情報出力
        print(f"\nConcurrent Operations Performance:")
        print(f"  30タスク並行実行: {total_time:0.2f}秒")
        print(f"  平均タスク時間: {total_time/30*1000:0.2f}ms")
        
        # 性能基準チェック
        assert total_time < 3.0  # 3秒以内に完了
    
    @pytest.mark.asyncio
    async def test_memory_efficiency(self):
        """メモリ効率性テスト"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 大量のタスク実行
        worker = EnhancedTaskWorker(worker_id="memory-test")
        for i in range(100):
            await worker.process_request({
                "operation": "submit_task",
                "task_type": "execution",
                "payload": {"data": "x" * 1000}  # 1KBのデータ
            })
        
        # メモリ使用量確認
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"\nMemory Efficiency:")
        print(f"  初期メモリ: {initial_memory:0.2f}MB")
        print(f"  最終メモリ: {final_memory:0.2f}MB")
        print(f"  増加量: {memory_increase:0.2f}MB")
        
        # メモリ効率基準チェック
        assert memory_increase < 50  # 50MB以下の増加

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])