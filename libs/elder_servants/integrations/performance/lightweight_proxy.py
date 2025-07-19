"""
🪶 Elder Servants軽量プロキシレイヤー
Phase 3 パフォーマンス最適化：最小オーバーヘッドアクセス層

EldersServiceLegacy統合: Iron Will品質基準とエルダー評議会令第27号完全準拠
目標: Elder機能への高速アクセスを低オーバーヘッドで提供
"""

import asyncio
import logging
import time
import weakref
from typing import Dict, Any, List, Optional, Union, Callable, TypeVar, Generic
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import json
import gzip
import pickle
from functools import lru_cache, wraps
import threading
from concurrent.futures import Future

# EldersLegacy統合インポート
from libs.core.elders_legacy import (
    EldersServiceLegacy,
    enforce_boundary,
    EldersLegacyDomain,
    IronWillCriteria
)

# パフォーマンス最適化インポート
from libs.elder_servants.integrations.performance.cache_manager import (
    ElderCacheManager, CacheKeyType, get_cache_manager
)
from libs.elder_servants.integrations.performance.async_optimizer import (
    AsyncWorkerOptimizer, ResourceType, get_global_optimizer
)


class ProxyMode(Enum):
    """プロキシモード"""
    DIRECT = "direct"                   # 直接アクセス（最高速）
    CACHED = "cached"                   # キャッシュ使用（高速）
    OPTIMIZED = "optimized"             # 最適化使用（バランス）
    STREAMING = "streaming"             # ストリーミング（大容量）
    LAZY = "lazy"                       # 遅延ロード（メモリ効率）


class CompressionLevel(Enum):
    """圧縮レベル"""
    NONE = 0                           # 圧縮なし
    FAST = 1                           # 高速圧縮
    BALANCED = 6                       # バランス圧縮
    MAXIMUM = 9                        # 最大圧縮


@dataclass
class ProxyConfig:
    """プロキシ設定"""
    mode: ProxyMode = ProxyMode.OPTIMIZED
    enable_compression: bool = True
    compression_level: CompressionLevel = CompressionLevel.BALANCED
    compression_threshold_bytes: int = 1024  # 1KB以上で圧縮
    enable_streaming: bool = True
    streaming_chunk_size: int = 8192  # 8KB chunks
    enable_lazy_loading: bool = True
    cache_small_responses: bool = True
    small_response_threshold: int = 10240  # 10KB以下をキャッシュ
    max_response_size_mb: int = 50  # 50MB制限
    timeout_seconds: int = 30


@dataclass
class ProxyMetrics:
    """プロキシメトリクス"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    compression_saves_bytes: int = 0
    streaming_requests: int = 0
    lazy_loads: int = 0
    total_response_time_ms: float = 0.0
    total_bytes_transferred: int = 0


T = TypeVar('T')


class ProxyRequest(Generic[T]):
    """プロキシリクエスト"""

    def __init__(self, request_id: str, target_service: str,
                 method: str, payload: T, config: ProxyConfig = None):
        self.request_id = request_id
        self.target_service = target_service
        self.method = method
        self.payload = payload
        self.config = config or ProxyConfig()
        self.created_at = datetime.now()
        self.metadata: Dict[str, Any] = {}


class ProxyResponse(Generic[T]):
    """プロキシレスポンス"""

    def __init__(self, request_id: str, success: bool,
                 data: T = None, error_message: Optional[str] = None,
                 was_cached: bool = False, was_compressed: bool = False,
                 was_streamed: bool = False, response_size_bytes: int = 0,
                 processing_time_ms: float = 0.0):
        self.request_id = request_id
        self.success = success
        self.data = data
        self.error_message = error_message
        self.was_cached = was_cached
        self.was_compressed = was_compressed
        self.was_streamed = was_streamed
        self.response_size_bytes = response_size_bytes
        self.processing_time_ms = processing_time_ms
        self.completed_at = datetime.now()


class LightweightElderProxy(EldersServiceLegacy[ProxyRequest, ProxyResponse]):
    """
    🪶 Elder Servants軽量プロキシレイヤー

    EldersServiceLegacyから継承し、Iron Will品質基準に完全準拠。
    最小オーバーヘッドでElder機能への高速アクセスを提供。
    """

    def __init__(self, config: ProxyConfig = None):
        # EldersServiceLegacy初期化 (EXECUTION域)
        super().__init__("lightweight_elder_proxy")

        self.config = config or ProxyConfig()
        self.logger = logging.getLogger("elder_servants.lightweight_proxy")

        # メトリクス
        self.metrics = ProxyMetrics()
        self.response_cache: Dict[str, Any] = {}

        # 軽量サービス参照（弱参照使用）
        self._service_refs: Dict[str, weakref.ReferenceType] = {}
        self._cache_manager: Optional[ElderCacheManager] = None
        self._async_optimizer: Optional[AsyncWorkerOptimizer] = None

        # 遅延ロードキュー
        self._lazy_queue: asyncio.Queue = asyncio.Queue()
        self._lazy_worker_task: Optional[asyncio.Task] = None

        # ストリーミングハンドラー
        self._streaming_handlers: Dict[str, Callable] = {}

        # パフォーマンス最適化
        self._hot_cache: Dict[str, Any] = {}  # インメモリホットキャッシュ
        self._compression_cache: Dict[str, bytes] = {}  # 圧縮キャッシュ

        # Iron Will品質基準
        self.quality_threshold = 95.0

        self.logger.info(f"Lightweight Elder Proxy initialized: {self.config.mode.value}")

    @enforce_boundary("proxy")
    async def process_request(self, request: ProxyRequest) -> ProxyResponse:
        """
        EldersServiceLegacy統一リクエスト処理

        Args:
            request: ProxyRequest形式のリクエスト

        Returns:
            ProxyResponse: プロキシ処理結果
        """
        start_time = time.time()

        try:
            self.metrics.total_requests += 1

            # 処理モード決定
            if request.config.mode == ProxyMode.DIRECT:
                response = await self._process_direct(request)
            elif request.config.mode == ProxyMode.CACHED:
                response = await self._process_cached(request)
            elif request.config.mode == ProxyMode.OPTIMIZED:
                response = await self._process_optimized(request)
            elif request.config.mode == ProxyMode.STREAMING:
                response = await self._process_streaming(request)
            elif request.config.mode == ProxyMode.LAZY:
                response = await self._process_lazy(request)
            else:
                response = await self._process_optimized(request)  # デフォルト

            # メトリクス更新
            processing_time = (time.time() - start_time) * 1000
            response.processing_time_ms = processing_time
            self.metrics.total_response_time_ms += processing_time

            if response.was_cached:
                self.metrics.cache_hits += 1
            else:
                self.metrics.cache_misses += 1

            if response.was_compressed:
                # 圧縮節約バイト数を推定
                estimated_original = response.response_size_bytes * 2  # 50%圧縮率と仮定
                self.metrics.compression_saves_bytes += max(0, estimated_original - response.response_size_bytes)

            if response.was_streamed:
                self.metrics.streaming_requests += 1

            self.metrics.total_bytes_transferred += response.response_size_bytes

            return response

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self.logger.error(f"Proxy processing failed for {request.request_id}: {str(e)}")

            return ProxyResponse(
                request_id=request.request_id,
                success=False,
                error_message=str(e),
                processing_time_ms=processing_time
            )

    async def _process_direct(self, request: ProxyRequest) -> ProxyResponse:
        """直接処理（最高速モード）"""
        # サービス直接呼び出し
        service = await self._get_service(request.target_service)
        if not service:
            raise Exception(f"Service not found: {request.target_service}")

        # メソッド実行
        if hasattr(service, request.method):
            method = getattr(service, request.method)
            if asyncio.iscoroutinefunction(method):
                result = await method(request.payload)
            else:
                result = method(request.payload)
        else:
            raise Exception(f"Method not found: {request.method}")

        # レスポンス作成
        response_data = result
        response_size = len(str(response_data).encode())

        return ProxyResponse(
            request_id=request.request_id,
            success=True,
            data=response_data,
            response_size_bytes=response_size
        )

    async def _process_cached(self, request: ProxyRequest) -> ProxyResponse:
        """キャッシュ処理"""
        # キャッシュキー生成
        cache_key = self._generate_cache_key(request)

        # ホットキャッシュ確認
        if cache_key in self._hot_cache:
            cached_data = self._hot_cache[cache_key]
            return ProxyResponse(
                request_id=request.request_id,
                success=True,
                data=cached_data,
                was_cached=True,
                response_size_bytes=len(str(cached_data).encode())
            )

        # 外部キャッシュ確認
        cache_manager = await self._get_cache_manager()
        cached_result = await cache_manager.get_quality_check_cache(
            request.request_id,
            f"{request.target_service}_{request.method}"
        )

        if cached_result:
            # ホットキャッシュに保存
            if request.config.cache_small_responses:
                data_size = len(str(cached_result).encode())
                if data_size <= request.config.small_response_threshold:
                    self._hot_cache[cache_key] = cached_result

            return ProxyResponse(
                request_id=request.request_id,
                success=True,
                data=cached_result,
                was_cached=True,
                response_size_bytes=len(str(cached_result).encode())
            )

        # キャッシュミス - 直接処理して結果をキャッシュ
        response = await self._process_direct(request)

        if response.success:
            # キャッシュ保存
            await cache_manager.set_quality_check_cache(
                request.request_id,
                f"{request.target_service}_{request.method}",
                response.data
            )

            # ホットキャッシュ保存
            if (request.config.cache_small_responses and
                response.response_size_bytes <= request.config.small_response_threshold):
                self._hot_cache[cache_key] = response.data

        return response

    async def _process_optimized(self, request: ProxyRequest) -> ProxyResponse:
        """最適化処理（非同期最適化使用）"""
        async_optimizer = await self._get_async_optimizer()

        # 最適化実行リクエスト作成
        async def optimized_execution():
            return await self._process_direct(request)

        # リソースタイプ決定
        resource_type = self._determine_resource_type(request)

        # 最適化実行
        from libs.elder_servants.integrations.performance.async_optimizer import AsyncOptimizationRequest

        opt_request = AsyncOptimizationRequest(
            task_id=request.request_id,
            coroutine_func=optimized_execution,
            resource_type=resource_type,
            timeout_s=request.config.timeout_seconds
        )

        opt_response = await async_optimizer.process_request(opt_request)

        if opt_response.success:
            result = opt_response.result
            response_size = len(str(result.data).encode()) if result else 0

            return ProxyResponse(
                request_id=request.request_id,
                success=True,
                data=result.data if result else None,
                response_size_bytes=response_size
            )
        else:
            return ProxyResponse(
                request_id=request.request_id,
                success=False,
                error_message=opt_response.error_message
            )

    async def _process_streaming(self, request: ProxyRequest) -> ProxyResponse:
        """ストリーミング処理"""
        # 大容量レスポンス用のストリーミング処理
        response_data = await self._process_direct(request)

        if not response_data.success:
            return response_data

        # データサイズ確認
        data_size = response_data.response_size_bytes

        if data_size > request.config.streaming_chunk_size:
            # ストリーミング実行
            compressed_data = await self._compress_data(
                response_data.data,
                request.config.compression_level
            )

            return ProxyResponse(
                request_id=request.request_id,
                success=True,
                data=compressed_data,
                was_streamed=True,
                was_compressed=True,
                response_size_bytes=len(compressed_data)
            )
        else:
            # 小さなデータは直接返す
            return response_data

    async def _process_lazy(self, request: ProxyRequest) -> ProxyResponse:
        """遅延処理"""
        # 遅延ロードキューに追加
        future = Future()
        await self._lazy_queue.put((request, future))

        # 遅延ワーカーが未起動の場合は起動
        if self._lazy_worker_task is None or self._lazy_worker_task.done():
            self._lazy_worker_task = asyncio.create_task(self._lazy_worker())

        # 遅延実行指示レスポンス
        self.metrics.lazy_loads += 1

        return ProxyResponse(
            request_id=request.request_id,
            success=True,
            data={"status": "lazy_loading", "future_id": id(future)},
            response_size_bytes=50  # 小さな応答サイズ
        )

    async def _lazy_worker(self):
        """遅延ワーカー"""
        while True:
            try:
                # タイムアウト付きで次のタスクを取得
                request, future = await asyncio.wait_for(
                    self._lazy_queue.get(),
                    timeout=5.0
                )

                # 実際の処理実行
                try:
                    response = await self._process_direct(request)
                    future.set_result(response)
                except Exception as e:
                    future.set_exception(e)

            except asyncio.TimeoutError:
                # タイムアウト - ワーカー終了
                break
            except Exception as e:
                self.logger.error(f"Lazy worker error: {str(e)}")

    def _generate_cache_key(self, request: ProxyRequest) -> str:
        """キャッシュキー生成"""
        key_data = {
            "service": request.target_service,
            "method": request.method,
            "payload_hash": hash(str(request.payload))
        }
        return f"proxy_{hash(str(key_data))}"

    def _determine_resource_type(self, request: ProxyRequest) -> ResourceType:
        """リソースタイプ決定"""
        # サービス・メソッド名からリソースタイプを推定
        if "cpu" in request.method.lower() or "compute" in request.method.lower():
            return ResourceType.CPU_BOUND
        elif "io" in request.method.lower() or "file" in request.method.lower():
            return ResourceType.IO_BOUND
        elif "network" in request.method.lower() or "api" in request.method.lower():
            return ResourceType.NETWORK_BOUND
        else:
            return ResourceType.IO_BOUND  # デフォルト

    async def _compress_data(self, data: Any, level: CompressionLevel) -> bytes:
        """データ圧縮"""
        try:
            # データをJSONシリアライズ
            json_data = json.dumps(data, ensure_ascii=False)
            json_bytes = json_data.encode('utf-8')

            # 圧縮レベルに応じて圧縮
            if level == CompressionLevel.NONE:
                return json_bytes

            compressed = gzip.compress(json_bytes, compresslevel=level.value)

            # 圧縮効果確認
            if len(compressed) >= len(json_bytes):
                # 圧縮効果がない場合は元データを返す
                return json_bytes

            return compressed

        except Exception as e:
            self.logger.warning(f"Compression failed: {str(e)}")
            # 圧縮失敗時は元データをJSON化して返す
            return json.dumps(data, ensure_ascii=False).encode('utf-8')

    async def _get_service(self, service_name: str) -> Optional[Any]:
        """サービス取得（弱参照管理）"""
        if service_name in self._service_refs:
            service_ref = self._service_refs[service_name]
            service = service_ref()
            if service is not None:
                return service
            else:
                # 弱参照が無効になった場合は削除
                del self._service_refs[service_name]

        # サービス動的ロード（プレースホルダー実装）
        # 実際の実装では適切なサービスロケーターを使用
        return None

    async def _get_cache_manager(self) -> ElderCacheManager:
        """キャッシュマネージャー取得"""
        if self._cache_manager is None:
            self._cache_manager = await get_cache_manager()
        return self._cache_manager

    async def _get_async_optimizer(self) -> AsyncWorkerOptimizer:
        """非同期最適化取得"""
        if self._async_optimizer is None:
            self._async_optimizer = await get_global_optimizer()
        return self._async_optimizer

    def register_service(self, name: str, service: Any):
        """サービス登録（弱参照）"""
        self._service_refs[name] = weakref.ref(service)
        self.logger.info(f"Registered service: {name}")

    def register_streaming_handler(self, handler_name: str, handler: Callable):
        """ストリーミングハンドラー登録"""
        self._streaming_handlers[handler_name] = handler
        self.logger.info(f"Registered streaming handler: {handler_name}")

    def validate_request(self, request: ProxyRequest) -> bool:
        """EldersServiceLegacyリクエスト検証"""
        if not request.request_id:
            return False
        if not request.target_service:
            return False
        if not request.method:
            return False
        return True

    def get_capabilities(self) -> List[str]:
        """EldersServiceLegacy能力取得"""
        return [
            "lightweight_proxying",
            "intelligent_caching",
            "data_compression",
            "streaming_support",
            "lazy_loading",
            "performance_optimization",
            "resource_management"
        ]

    @lru_cache(maxsize=1000)
    def _cached_method_lookup(self, service_name: str, method_name: str) -> Optional[str]:
        """メソッド検索キャッシュ"""
        # メソッド存在確認のキャッシュ
        return f"{service_name}.{method_name}"

    async def get_proxy_metrics(self) -> Dict[str, Any]:
        """プロキシメトリクス取得"""
        hit_rate = (self.metrics.cache_hits / max(self.metrics.total_requests, 1)) * 100
        avg_response_time = (self.metrics.total_response_time_ms /
                           max(self.metrics.total_requests, 1))

        compression_efficiency = 0.0
        if self.metrics.total_bytes_transferred > 0:
            compression_efficiency = (self.metrics.compression_saves_bytes /
                                    self.metrics.total_bytes_transferred) * 100

        return {
            "total_requests": self.metrics.total_requests,
            "cache_hit_rate": round(hit_rate, 2),
            "average_response_time_ms": round(avg_response_time, 2),
            "total_bytes_transferred": self.metrics.total_bytes_transferred,
            "compression_saves_bytes": self.metrics.compression_saves_bytes,
            "compression_efficiency_percent": round(compression_efficiency, 2),
            "streaming_requests": self.metrics.streaming_requests,
            "lazy_loads": self.metrics.lazy_loads,
            "hot_cache_size": len(self._hot_cache),
            "registered_services": len(self._service_refs),
            "proxy_mode": self.config.mode.value,
            "iron_will_compliance": hit_rate >= 70.0 and avg_response_time <= 100.0
        }

    async def clear_caches(self):
        """キャッシュクリア"""
        self._hot_cache.clear()
        self._compression_cache.clear()
        self._cached_method_lookup.cache_clear()
        self.logger.info("All caches cleared")

    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        try:
            # 基本ヘルスチェック
            base_health = await super().health_check()

            # プロキシ固有メトリクス
            metrics = await self.get_proxy_metrics()

            # パフォーマンス評価
            performance_healthy = (
                metrics["cache_hit_rate"] >= 70.0 and
                metrics["average_response_time_ms"] <= 100.0
            )

            # リソース健全性
            resource_healthy = (
                len(self._hot_cache) < 10000 and  # ホットキャッシュサイズ制限
                self.metrics.total_bytes_transferred < 1024*1024*1024  # 1GB制限
            )

            overall_healthy = performance_healthy and resource_healthy

            return {
                **base_health,
                "proxy_status": "healthy" if overall_healthy else "degraded",
                "metrics": metrics,
                "performance_healthy": performance_healthy,
                "resource_healthy": resource_healthy,
                "iron_will_compliance": overall_healthy
            }

        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                "success": False,
                "status": "error",
                "error": str(e)
            }

    async def cleanup_resources(self):
        """リソースクリーンアップ"""
        # 遅延ワーカー停止
        if self._lazy_worker_task and not self._lazy_worker_task.done():
            self._lazy_worker_task.cancel()
            try:
                await self._lazy_worker_task
            except asyncio.CancelledError:
                pass

        # キャッシュクリア
        await self.clear_caches()

        # 弱参照クリア
        self._service_refs.clear()

        self.logger.info("Lightweight proxy resources cleaned up")


# デコレータ関数群
def lightweight_proxy(mode: ProxyMode = ProxyMode.OPTIMIZED,
                     cache_response: bool = True,
                     compress_response: bool = True):
    """軽量プロキシデコレータ"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # プロキシ経由で実行
            proxy = LightweightElderProxy(ProxyConfig(
                mode=mode,
                cache_small_responses=cache_response,
                enable_compression=compress_response
            ))

            try:
                # 関数をプロキシ経由で実行
                request = ProxyRequest(
                    request_id=f"decorated_{int(time.time())}",
                    target_service="decorator_service",
                    method=func.__name__,
                    payload={"args": args, "kwargs": kwargs}
                )

                # 直接実行をシミュレート
                result = await func(*args, **kwargs)

                return ProxyResponse(
                    request_id=request.request_id,
                    success=True,
                    data=result
                )

            finally:
                await proxy.cleanup_resources()

        return wrapper
    return decorator


# グローバルプロキシインスタンス
_global_proxy: Optional[LightweightElderProxy] = None


async def get_global_proxy() -> LightweightElderProxy:
    """グローバルプロキシ取得"""
    global _global_proxy

    if _global_proxy is None:
        _global_proxy = LightweightElderProxy()

    return _global_proxy


# 便利関数群
async def quick_proxy_call(service_name: str, method_name: str,
                          payload: Any, mode: ProxyMode = ProxyMode.OPTIMIZED) -> Any:
    """クイックプロキシ呼び出し"""
    proxy = await get_global_proxy()

    request = ProxyRequest(
        request_id=f"quick_{int(time.time())}",
        target_service=service_name,
        method=method_name,
        payload=payload,
        config=ProxyConfig(mode=mode)
    )

    response = await proxy.process_request(request)

    if response.success:
        return response.data
    else:
        raise Exception(response.error_message)


async def cached_proxy_call(service_name: str, method_name: str, payload: Any) -> Any:
    """キャッシュ付きプロキシ呼び出し"""
    return await quick_proxy_call(service_name, method_name, payload, ProxyMode.CACHED)


async def streaming_proxy_call(service_name: str, method_name: str, payload: Any) -> Any:
    """ストリーミングプロキシ呼び出し"""
    return await quick_proxy_call(service_name, method_name, payload, ProxyMode.STREAMING)
