#!/usr/bin/env python3
"""
⚡ GitHub Integration Parallel Processor
Iron Will Compliant - High Performance Parallel Execution
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class ParallelProcessor:
    """
    ⚡ 高性能並列処理システム
    
    Features:
    - Async/await native support
    - Thread pool execution
    - Process pool execution
    - Batch processing
    - Progress tracking
    - Error aggregation
    - Performance monitoring
    """
    
    def __init__(
        self,
        max_workers: int = 10,
        max_threads: int = 20,
        max_processes: int = 4,
        batch_size: int = 100
    ):
        """
        並列プロセッサー初期化
        
        Args:
            max_workers: 最大非同期ワーカー数
            max_threads: 最大スレッド数
            max_processes: 最大プロセス数
            batch_size: バッチサイズ
        """
        self.max_workers = max_workers
        self.max_threads = max_threads
        self.max_processes = max_processes
        self.batch_size = batch_size
        
        # エクゼキューター
        self.thread_pool = ThreadPoolExecutor(max_workers=max_threads)
        self.process_pool = ProcessPoolExecutor(max_workers=max_processes)
        
        # セマフォ
        self.async_semaphore = asyncio.Semaphore(max_workers)
        
        # パフォーマンス統計
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_time": 0,
            "average_time": 0,
            "peak_concurrency": 0,
            "current_concurrency": 0
        }
        
        logger.info(f"ParallelProcessor initialized: workers={max_workers}, threads={max_threads}, " \
            "processes={max_processes}")
    
    async def map_async(
        self,
        func: Callable,
        items: List[Any],
        progress_callback: Optional[Callable] = None
    ) -> List[Tuple[bool, Any]]:
        """
        非同期並列マッピング
        
        Args:
            func: 実行する非同期関数
            items: 処理対象アイテムリスト
            progress_callback: 進捗コールバック
            
        Returns:
            [(成功フラグ, 結果)] のリスト
        """
        start_time = time.time()
        self.stats["total_tasks"] += len(items)
        
        results = []
        tasks = []
        
        # バッチ処理
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_tasks = [
                self._execute_async_with_semaphore(func, item, i + j)
                for j, item in enumerate(batch)
            ]
            
            # バッチ実行
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # 結果処理
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    results.append((False, str(result)))
                    self.stats["failed_tasks"] += 1
                else:
                    results.append((True, result))
                    self.stats["completed_tasks"] += 1
                
                # 進捗通知
                if progress_callback:
                    progress = (i + j + 1) / len(items) * 100
                    await self._call_progress_callback(
                        progress_callback,
                        progress,
                        i + j + 1,
                        len(items)
                    )
        
        # 統計更新
        elapsed = time.time() - start_time
        self.stats["total_time"] += elapsed
        self._update_average_time()
        
        logger.info(f"Async map completed: {len(items)} items in {elapsed:.2f}s")
        return results
    
    async def _execute_async_with_semaphore(self, func: Callable, item: Any, index: int) -> Any:
        """セマフォ制御付き非同期実行"""
        async with self.async_semaphore:
            # 並行度統計
            self.stats["current_concurrency"] += 1
            if self.stats["current_concurrency"] > self.stats["peak_concurrency"]:
                self.stats["peak_concurrency"] = self.stats["current_concurrency"]
            
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(item)
                else:
                    # 同期関数を非同期で実行
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(self.thread_pool, func, item)
                return result
            finally:
                self.stats["current_concurrency"] -= 1
    
    async def _call_progress_callback(
        self,
        callback: Callable,
        progress: float,
        current: int,
        total: int
    ):
        """進捗コールバック呼び出し"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(progress, current, total)
            else:
                callback(progress, current, total)
        except Exception as e:
            logger.error(f"Progress callback error: {str(e)}")
    
    def map_threads(
        self,
        func: Callable,
        items: List[Any],
        progress_callback: Optional[Callable] = None
    ) -> List[Tuple[bool, Any]]:
        """
        スレッドプール並列マッピング
        
        Args:
            func: 実行する関数
            items: 処理対象アイテムリスト
            progress_callback: 進捗コールバック
            
        Returns:
            [(成功フラグ, 結果)] のリスト
        """
        start_time = time.time()
        self.stats["total_tasks"] += len(items)
        
        results = []
        futures = []
        
        # タスク投入
        for i, item in enumerate(items):
            future = self.thread_pool.submit(self._execute_with_error_handling, func, item)
            futures.append((i, future))
        
        # 結果収集
        for i, future in futures:
            try:
                result = future.result()
                results.append((True, result))
                self.stats["completed_tasks"] += 1
            except Exception as e:
                results.append((False, str(e)))
                self.stats["failed_tasks"] += 1
            
            # 進捗通知
            if progress_callback:
                progress = (i + 1) / len(items) * 100
                progress_callback(progress, i + 1, len(items))
        
        # 統計更新
        elapsed = time.time() - start_time
        self.stats["total_time"] += elapsed
        self._update_average_time()
        
        logger.info(f"Thread map completed: {len(items)} items in {elapsed:.2f}s")
        return results
    
    def map_processes(
        self,
        func: Callable,
        items: List[Any],
        progress_callback: Optional[Callable] = None
    ) -> List[Tuple[bool, Any]]:
        """
        プロセスプール並列マッピング
        
        Args:
            func: 実行する関数（pickle可能である必要がある）
            items: 処理対象アイテムリスト
            progress_callback: 進捗コールバック
            
        Returns:
            [(成功フラグ, 結果)] のリスト
        """
        start_time = time.time()
        self.stats["total_tasks"] += len(items)
        
        results = []
        futures = []
        
        # タスク投入
        for i, item in enumerate(items):
            future = self.process_pool.submit(self._execute_with_error_handling, func, item)
            futures.append((i, future))
        
        # 結果収集
        for i, future in futures:
            try:
                result = future.result()
                results.append((True, result))
                self.stats["completed_tasks"] += 1
            except Exception as e:
                results.append((False, str(e)))
                self.stats["failed_tasks"] += 1
            
            # 進捗通知
            if progress_callback:
                progress = (i + 1) / len(items) * 100
                progress_callback(progress, i + 1, len(items))
        
        # 統計更新
        elapsed = time.time() - start_time
        self.stats["total_time"] += elapsed
        self._update_average_time()
        
        logger.info(f"Process map completed: {len(items)} items in {elapsed:.2f}s")
        return results
    
    @staticmethod
    def _execute_with_error_handling(func: Callable, item: Any) -> Any:
        """エラーハンドリング付き実行"""
        try:
            return func(item)
        except Exception as e:
            logger.error(f"Task execution error: {str(e)}")
            raise
    
    async def execute_parallel_api_calls(
        self,
        api_calls: List[Dict[str, Any]],
        session_provider: Callable
    ) -> List[Dict[str, Any]]:
        """
        並列API呼び出し実行
        
        Args:
            api_calls: API呼び出し定義リスト
                [{
                    "method": "GET",
                    "endpoint": "/repos/owner/repo",
                    "params": {},
                    "data": {}
                }, ...]
            session_provider: HTTPセッション提供関数
            
        Returns:
            API応答リスト
        """
        async def execute_api_call(call_def: Dict[str, Any]) -> Dict[str, Any]:
            try:
                session = await session_provider()
                
                method = call_def.get("method", "GET")
                endpoint = call_def["endpoint"]
                params = call_def.get("params", {})
                data = call_def.get("data")
                
                async with session.request(
                    method=method,
                    url=endpoint,
                    params=params,
                    json=data
                ) as response:
                    return {
                        "success": response.status < 400,
                        "status": response.status,
                        "data": await response.json() if response.status < 400 else None,
                        "error": await response.text() if response.status >= 400 else None,
                        "endpoint": endpoint
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "endpoint": call_def.get("endpoint", "unknown")
                }
        
        # 並列実行
        results = await self.map_async(execute_api_call, api_calls)
        
        # 結果整形
        formatted_results = []
        for success, result in results:
            if success:
                formatted_results.append(result)
            else:
                formatted_results.append({
                    "success": False,
                    "error": result
                })
        
        return formatted_results
    
    def _update_average_time(self):
        """平均実行時間更新"""
        if self.stats["completed_tasks"] > 0:
            self.stats["average_time"] = self.stats["total_time"] / self.stats["completed_tasks"]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        パフォーマンス統計取得
        
        Returns:
            統計情報辞書
        """
        success_rate = 0
        if self.stats["total_tasks"] > 0:
            success_rate = (self.stats["completed_tasks"] / self.stats["total_tasks"]) * 100
        
        return {
            **self.stats,
            "success_rate": f"{success_rate:.2f}%",
            "throughput": f"{self.stats['completed_tasks'] / max(
                self.stats['total_time'],
                1
            ):.2f} tasks/sec"
        }
    
    def shutdown(self):
        """リソースクリーンアップ"""
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)
        logger.info("ParallelProcessor shutdown completed")


# 便利な関数
async def parallel_fetch(
    urls: List[str],
    session_provider: Callable,
    max_workers: int = 10
) -> List[Dict[str, Any]]:
    """
    並列URL取得
    
    Args:
        urls: URLリスト
        session_provider: HTTPセッション提供関数
        max_workers: 最大ワーカー数
        
    Returns:
        取得結果リスト
    """
    processor = ParallelProcessor(max_workers=max_workers)
    
    api_calls = [
        {"method": "GET", "endpoint": url}
        for url in urls
    ]
    
    try:
        results = await processor.execute_parallel_api_calls(api_calls, session_provider)
        return results
    finally:
        processor.shutdown()


# 使用例
async def example_usage():
    """使用例"""
    processor = ParallelProcessor(max_workers=5)
    
    # 非同期関数の並列実行
    async def fetch_data(item_id: int):
        await asyncio.sleep(0.1)  # API呼び出しシミュレート
        return {"id": item_id, "data": f"Data for {item_id}"}
    
    # 進捗表示コールバック
    def show_progress(progress: float, current: int, total: int):
        print(f"Progress: {progress:.1f}% ({current}/{total})")
    
    # 並列実行
    items = list(range(20))
    results = await processor.map_async(fetch_data, items, show_progress)
    
    # 結果表示
    successful = [r for s, r in results if s]
    failed = [r for s, r in results if not s]
    
    print(f"\nSuccessful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"\nStats: {processor.get_stats()}")
    
    processor.shutdown()


if __name__ == "__main__":
    asyncio.run(example_usage())