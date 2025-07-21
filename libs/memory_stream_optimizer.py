"""
Memory Stream Optimizer for Auto Issue Processor A2A
Phase 3 implementation - Memory efficiency through streaming
"""
import asyncio
import gc
import sys
import zlib
try:
    import lz4.frame
    HAS_LZ4 = True
except ImportError:
    HAS_LZ4 = False

try:
    import zstandard as zstd
    HAS_ZSTD = True
except ImportError:
    HAS_ZSTD = False
import mmap
import io
import psutil
from dataclasses import dataclass, field
from typing import AsyncIterator, List, Any, Optional, Dict, Union, Callable
from enum import Enum
import logging
from collections import deque

logger = logging.getLogger(__name__)


class CompressionType(Enum):
    """Supported compression types"""
    NONE = "none"
    GZIP = "gzip"
    LZ4 = "lz4"
    ZSTD = "zstd"


@dataclass
class StreamMetrics:
    """Metrics for stream processing"""
    total_processed: int = 0
    total_bytes: int = 0
    compression_ratio: float = 1.0
    zero_copy_transfers: int = 0
    gc_optimizations: int = 0
    memory_limit_hits: int = 0
    mmap_operations: int = 0


@dataclass
class CompressedData:
    """Compressed data container"""
    data: bytes
    original_size: int
    compressed_size: int
    compression_type: CompressionType


class ChunkBuffer:
    """Adaptive buffer for chunk management"""
    
    def __init__(self, initial_size: int = 4096):
        self._buffer = bytearray(initial_size)
        self._position = 0
        self._size = initial_size
    
    def write(self, data: bytes) -> None:
        """Write data to buffer"""
        required = self._position + len(data)
        if required > self._size:
            # Grow buffer
            new_size = max(required, self._size * 2)
            new_buffer = bytearray(new_size)
            new_buffer[:self._position] = self._buffer[:self._position]
            self._buffer = new_buffer
            self._size = new_size
        
        self._buffer[self._position:self._position + len(data)] = data
        self._position += len(data)
    
    def read(self, size: int) -> bytes:
        """Read data from buffer"""
        data = bytes(self._buffer[:min(size, self._position)])
        self._buffer[:self._position - len(data)] = self._buffer[len(data):self._position]
        self._position -= len(data)
        return data
    
    def reset(self) -> None:
        """Reset buffer"""
        self._position = 0
    
    @property
    def size(self) -> int:
        """Get current data size"""
        return self._position


class MemoryPool:
    """Memory pool for efficient allocation"""
    
    def __init__(self, block_size: int = 4096, max_blocks: int = 100):
        self.block_size = block_size
        self.max_blocks = max_blocks
        self._pool = deque()
        self._allocated = set()
        
        # Pre-allocate blocks
        for _ in range(max_blocks):
            self._pool.append(bytearray(block_size))
    
    def allocate(self) -> Optional[bytearray]:
        """Allocate a block from pool"""
        if self._pool:
            block = self._pool.popleft()
            self._allocated.add(id(block))
            return block
        return None
    
    def release(self, block: bytearray) -> None:
        """Release block back to pool"""
        if id(block) in self._allocated:
            self._allocated.remove(id(block))
            # Clear block before returning to pool
            block[:] = b'\x00' * len(block)
            self._pool.append(block)
    
    @property
    def available_blocks(self) -> int:
        """Get number of available blocks"""
        return len(self._pool)


class StreamProcessor:
    """Incremental stream processor"""
    
    def __init__(self):
        self._queue = deque()
        self._processed = 0
    
    def add_data(self, data: Any) -> None:
        """Add data to processing queue"""
        self._queue.append(data)
    
    def has_data(self) -> bool:
        """Check if has data to process"""
        return len(self._queue) > 0
    
    async def process_next(self) -> Optional[Any]:
        """Process next item"""
        if self._queue:
            item = self._queue.popleft()
            self._processed += 1
            # Simulate processing
            await asyncio.sleep(0)
            return item
        return None


class MemoryStreamOptimizer:
    """Memory-efficient stream processing optimizer"""
    
    def __init__(self, chunk_size: int = 4096, buffer_size: int = 16384,
                 enable_compression: bool = True, memory_limit_mb: int = 500):
        self.chunk_size = chunk_size
        self.buffer_size = buffer_size
        self.enable_compression = enable_compression
        self.memory_limit_mb = memory_limit_mb
        
        self.metrics = StreamMetrics()
        self._memory_pool = MemoryPool()
        self._chunk_buffer = ChunkBuffer(buffer_size)
        
        self.is_under_pressure = False
        self._original_chunk_size = chunk_size
        
        # Compression engines
        if HAS_ZSTD:
            self._zstd_compressor = zstd.ZstdCompressor(level=3)
            self._zstd_decompressor = zstd.ZstdDecompressor()
        else:
            self._zstd_compressor = None
            self._zstd_decompressor = None
    
    async def process_stream(self, stream: AsyncIterator[Any]) -> AsyncIterator[Any]:
        """Process data stream efficiently"""
        buffer = []
        buffer_size = 0
        
        async for item in stream:
            buffer.append(item)
            buffer_size += sys.getsizeof(item)
            
            # Process when buffer is full or under memory pressure
            if buffer_size >= self.buffer_size or self.is_under_pressure:
                for processed in buffer:
                    self.metrics.total_processed += 1
                    yield processed
                
                buffer = []
                buffer_size = 0
                
                # Check memory pressure
                await self.check_memory_pressure()
        
        # Process remaining items
        for processed in buffer:
            self.metrics.total_processed += 1
            yield processed
    
    async def create_chunks(self, data: Union[str, bytes]) -> List[bytes]:
        """Create chunks from data"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        chunks = []
        for i in range(0, len(data), self.chunk_size):
            chunk = data[i:i + self.chunk_size]
            chunks.append(chunk)
            self.metrics.total_bytes += len(chunk)
        
        return chunks
    
    async def merge_chunks(self, chunks: List[bytes]) -> str:
        """Merge chunks back to data"""
        merged = b''.join(chunks)
        return merged.decode('utf-8')
    
    async def zero_copy_transfer(self, data: memoryview) -> memoryview:
        """Transfer data without copying"""
        self.metrics.zero_copy_transfers += 1
        # Return same memoryview - no copy
        return data
    
    async def compress_data(self, data: Union[str, bytes], 
                          compression_type: CompressionType) -> bytes:
        """Compress data using specified method"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        if compression_type == CompressionType.GZIP:
            compressed = zlib.compress(data, level=6)
        elif compression_type == CompressionType.LZ4 and HAS_LZ4:
            compressed = lz4.frame.compress(data)
        elif compression_type == CompressionType.ZSTD and HAS_ZSTD:
            compressed = self._zstd_compressor.compress(data)
        else:
            compressed = data
        
        self.metrics.compression_ratio = len(compressed) / len(data)
        return compressed
    
    async def decompress_data(self, data: bytes, 
                            compression_type: CompressionType) -> str:
        """Decompress data"""
        if compression_type == CompressionType.GZIP:
            decompressed = zlib.decompress(data)
        elif compression_type == CompressionType.LZ4 and HAS_LZ4:
            decompressed = lz4.frame.decompress(data)
        elif compression_type == CompressionType.ZSTD and HAS_ZSTD:
            decompressed = self._zstd_decompressor.decompress(data)
        else:
            decompressed = data
        
        return decompressed.decode('utf-8')
    
    async def check_memory_pressure(self) -> None:
        """Check and handle memory pressure"""
        memory = psutil.virtual_memory()
        
        if memory.percent > 90:
            self.is_under_pressure = True
            # Reduce chunk size under pressure
            self.chunk_size = max(512, self.chunk_size // 2)
            # Trigger GC
            await self.optimize_gc()
        elif memory.percent < 70 and self.is_under_pressure:
            self.is_under_pressure = False
            # Restore chunk size
            self.chunk_size = min(self._original_chunk_size, self.chunk_size * 2)
    
    async def process_single(self, data: Any) -> Any:
        """Process single data item"""
        # Check memory limit
        data_size = sys.getsizeof(data)
        if data_size > self.memory_limit_mb * 1024 * 1024:
            self.metrics.memory_limit_hits += 1
            raise MemoryError(f"Data size {data_size} exceeds memory limit")
        
        self.metrics.total_processed += 1
        self.metrics.total_bytes += data_size
        
        # Simulate processing
        await asyncio.sleep(0)
        return data
    
    async def optimize_gc(self) -> None:
        """Optimize garbage collection"""
        # Disable GC temporarily
        gc_was_enabled = gc.isenabled()
        gc.disable()
        
        try:
            # Collect garbage
            gc.collect(2)  # Full collection
            self.metrics.gc_optimizations += 1
        finally:
            if gc_was_enabled:
                gc.enable()
    
    async def create_pipeline(self, stages: List[str]) -> 'StreamPipeline':
        """Create processing pipeline"""
        return StreamPipeline(self, stages)
    
    async def process_stream(self, stream: AsyncIterator[Any]) -> AsyncIterator[Any]:
        """Process stream with adaptive chunking"""
        async for item in stream:
            # Adapt chunk size based on item size
            item_size = sys.getsizeof(item)
            if item_size < 100:
                # Small items - increase chunk size
                self.chunk_size = min(self._original_chunk_size * 2, self.chunk_size + 512)
            elif item_size > 10000:
                # Large items - decrease chunk size
                self.chunk_size = max(512, self.chunk_size - 512)
            
            yield item
    
    async def process_batched_stream(self, stream: AsyncIterator[Any], 
                                   batch_size: int) -> AsyncIterator[List[Any]]:
        """Process stream in batches"""
        batch = []
        
        async for item in stream:
            batch.append(item)
            
            if len(batch) >= batch_size:
                yield batch
                batch = []
        
        # Yield remaining items
        if batch:
            yield batch
    
    async def auto_compress(self, data: Union[str, bytes]) -> CompressedData:
        """Automatically select best compression"""
        if isinstance(data, str):
            original_bytes = data.encode('utf-8')
        else:
            original_bytes = data
        
        original_size = len(original_bytes)
        
        # Try different compression methods
        compressions = {
            CompressionType.GZIP: await self.compress_data(data, CompressionType.GZIP),
        }
        
        if HAS_LZ4:
            compressions[CompressionType.LZ4] = await self.compress_data(data, CompressionType.LZ4)
        if HAS_ZSTD:
            compressions[CompressionType.ZSTD] = await self.compress_data(data, CompressionType.ZSTD)
        
        # Select best compression
        best_type = CompressionType.GZIP  # Default
        best_size = len(compressions[CompressionType.GZIP])
        
        for comp_type, compressed in compressions.items():
            if len(compressed) < best_size:
                best_type = comp_type
                best_size = len(compressed)
        
        return CompressedData(
            data=compressions[best_type],
            original_size=original_size,
            compressed_size=best_size,
            compression_type=best_type
        )
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export optimizer metrics"""
        memory = psutil.virtual_memory()
        
        return {
            'total_processed': self.metrics.total_processed,
            'total_bytes': self.metrics.total_bytes,
            'memory_usage_mb': memory.used / 1024 / 1024,
            'compression_ratio': self.metrics.compression_ratio,
            'zero_copy_transfers': self.metrics.zero_copy_transfers,
            'gc_optimizations': self.metrics.gc_optimizations,
            'average_chunk_size': self.chunk_size,
            'is_under_pressure': self.is_under_pressure,
            'memory_limit_hits': self.metrics.memory_limit_hits
        }
    
    async def collect_stream(self, stream: AsyncIterator[Any]) -> List[Any]:
        """Collect all items from stream"""
        items = []
        async for item in stream:
            items.append(item)
        return items
    
    async def process_mmap_file(self, file_path: str) -> Optional[bytes]:
        """Process file using memory mapping"""
        try:
            with open(file_path, 'r+b') as f:
                with mmap.mmap(f.fileno(), 0) as mmapped:
                    self.metrics.mmap_operations += 1
                    # Process mmapped data
                    data = mmapped[:]
                    return data
        except Exception as e:
            logger.error(f"Memory mapping failed: {e}")
            return None


class StreamPipeline:
    """Stream processing pipeline"""
    
    def __init__(self, optimizer: MemoryStreamOptimizer, stages: List[str]):
        self.optimizer = optimizer
        self.stages = stages
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data through pipeline stages"""
        result = data.copy()
        
        for stage in self.stages:
            if stage == "parse":
                # Parsing stage
                pass
            elif stage == "transform":
                # Transformation stage
                pass
            elif stage == "compress":
                # Compression stage
                if "data" in result:
                    compressed = await self.optimizer.auto_compress(str(result))
                    result["compressed"] = compressed.data
        
        return result