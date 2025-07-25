"""
Test suite for Memory Stream Optimizer
Phase 3 implementation - Memory efficiency optimization
"""
import pytest
import asyncio
import io
import sys
from unittest.mock import Mock, patch, MagicMock
import psutil
import gc
from typing import List, AsyncIterator

from libs.memory_stream_optimizer import (
    MemoryStreamOptimizer,
    StreamProcessor,
    ChunkBuffer,
    MemoryPool,
    StreamMetrics,
    CompressionType
)

class TestMemoryStreamOptimizer:
    """Test suite for memory stream optimization"""
    
    @pytest.fixture
    def optimizer(self):
        """Create optimizer instance"""
        return MemoryStreamOptimizer(
            chunk_size=1024,
            buffer_size=4096,
            enable_compression=True,
            memory_limit_mb=100
        )
    
    def test_initialization(self, optimizer):
        """Test optimizer initialization"""
        assert optimizer.chunk_size == 1024
        assert optimizer.buffer_size == 4096
        assert optimizer.enable_compression is True
        assert optimizer.memory_limit_mb == 100
        assert optimizer.metrics.total_processed == 0
    
    @pytest.mark.asyncio
    async def test_stream_processing(self, optimizer):
        """Test basic stream processing"""
        # Create test data stream
        test_data = [f"issue-{i}" for i in range(100)]
        
        async def data_generator():
            for item in test_data:
                yield item
        
        # Process stream
        results = []
        async for processed in optimizer.process_stream(data_generator()):
            results.append(processed)
        
        assert len(results) == 100
        assert optimizer.metrics.total_processed == 100
    
    @pytest.mark.asyncio
    async def test_chunked_processing(self, optimizer):
        """Test chunked data processing"""
        # Large data that should be chunked
        large_data = "x" * 10000  # 10KB
        
        chunks = await optimizer.create_chunks(large_data)
        assert len(chunks) > 1  # Should be multiple chunks
        
        # Verify chunk sizes
        for chunk in chunks[:-1]:  # All but last
            assert len(chunk) == optimizer.chunk_size
        
        # Reconstruct and verify
        reconstructed = await optimizer.merge_chunks(chunks)
        assert reconstructed == large_data
    
    @pytest.mark.asyncio
    async def test_buffer_management(self, optimizer):
        """Test adaptive buffer management"""
        buffer = ChunkBuffer(initial_size=1024)
        
        # Test buffer growth
        data = b"x" * 2000
        buffer.write(data)
        assert buffer.size >= 2000
        
        # Test buffer read
        read_data = buffer.read(1000)
        assert len(read_data) == 1000
        
        # Test buffer reset
        buffer.reset()
        assert buffer.size == 0
    
    @pytest.mark.asyncio
    async def test_zero_copy_transfer(self, optimizer):
        """Test zero-copy data transfer"""
        # Create memory view
        original = bytearray(b"test data " * 100)
        view = memoryview(original)
        
        # Transfer without copy
        transferred = await optimizer.zero_copy_transfer(view)
        
        # Verify same memory location
        assert transferred.obj is original
        assert optimizer.metrics.zero_copy_transfers > 0
    
    @pytest.mark.asyncio
    async def test_compression(self, optimizer):
        """Test data compression"""
        # Repetitive data (compresses well)
        data = "repeat " * 1000
        
        compressed = await optimizer.compress_data(data, CompressionType.GZIP)
        assert len(compressed) < len(data)
        
        decompressed = await optimizer.decompress_data(compressed, CompressionType.GZIP)
        assert decompressed == data
        
        # Check compression ratio
        ratio = len(compressed) / len(data)
        assert ratio < 0.5  # Should compress to less than 50%
    
    @pytest.mark.asyncio
    async def test_memory_pool(self, optimizer):
        """Test memory pool management"""
        pool = MemoryPool(block_size=1024, max_blocks=10)
        
        # Allocate blocks
        blocks = []
        for i in range(5):
            block = pool.allocate()
            assert block is not None
            blocks.append(block)
        
        assert pool.available_blocks == 5
        
        # Release blocks
        for block in blocks:
            pool.release(block)
        
        assert pool.available_blocks == 10
    
    @pytest.mark.asyncio
    async def test_memory_pressure_handling(self, optimizer):
        """Test behavior under memory pressure"""
        # Simulate high memory usage
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value = Mock(percent=95.0)
            
            # Should trigger memory optimization
            await optimizer.check_memory_pressure()
            
            assert optimizer.is_under_pressure
            assert optimizer.chunk_size < 1024  # Should reduce chunk size
    
    @pytest.mark.asyncio
    async def test_incremental_processing(self, optimizer):
        """Test incremental data processing"""
        # Process data incrementally
        processor = StreamProcessor()
        
        # Add data in parts
        processor.add_data("part1")
        processor.add_data("part2")
        processor.add_data("part3")
        
        # Process incrementally
        results = []
        while processor.has_data():
            result = await processor.process_next()
            if result:
                results.append(result)
        
        assert len(results) == 3
        assert results == ["part1", "part2", "part3"]
    
    @pytest.mark.asyncio
    async def test_garbage_collection_optimization(self, optimizer):
        """Test GC optimization"""
        initial_gc_count = gc.get_count()
        
        # Process large amount of data
        for i in range(1000):
            data = f"data-{i}" * 100
            await optimizer.process_single(data)
        
        # Should have optimized GC
        assert optimizer.metrics.gc_optimizations > 0
        
        # Manual GC trigger
        await optimizer.optimize_gc()
        assert gc.get_count()[0] < initial_gc_count[0]
    
    @pytest.mark.asyncio
    async def test_streaming_pipeline(self, optimizer):
        """Test complete streaming pipeline"""
        # Create pipeline
        pipeline = await optimizer.create_pipeline(
            stages=["parse", "transform", "compress"]
        )
        
        # Process through pipeline
        input_data = {"issue": 123, "data": "x" * 1000}
        output = await pipeline.process(input_data)
        
        assert output is not None
        assert "compressed" in output
        assert len(output["compressed"]) < len(str(input_data))
    
    @pytest.mark.asyncio
    async def test_adaptive_chunk_sizing(self, optimizer):
        """Test adaptive chunk size adjustment"""
        # Start with default chunk size
        initial_size = optimizer.chunk_size
        
        # Process data with varying sizes
        small_items = ["x" * 10 for _ in range(100)]
        large_items = ["x" * 10000 for _ in range(10)]
        
        # Process small items
        async for _ in optimizer.process_stream(async_generator(small_items)):
            pass
        
        # Should adapt to smaller chunks
        assert optimizer.chunk_size < initial_size
        
        # Process large items
        async for _ in optimizer.process_stream(async_generator(large_items)):
            pass
        
        # Should adapt to larger chunks
        assert optimizer.chunk_size > initial_size
    
    @pytest.mark.asyncio
    async def test_memory_limit_enforcement(self, optimizer):
        """Test memory limit enforcement"""
        # Try to allocate beyond limit
        huge_data = "x" * (optimizer.memory_limit_mb * 1024 * 1024 * 2)
        
        with pytest.raises(MemoryError):
            await optimizer.process_single(huge_data)
        
        assert optimizer.metrics.memory_limit_hits > 0
    
    @pytest.mark.asyncio
    async def test_stream_batching(self, optimizer):
        """Test stream batching optimization"""
        # Create stream with many small items
        items = [f"item-{i}" for i in range(1000)]
        
        batches_processed = 0
        async for batch in optimizer.process_batched_stream(
            async_generator(items), 
            batch_size=50
        ):
            assert len(batch) <= 50
            batches_processed += 1
        
        assert batches_processed == 20  # 1000/50
    
    @pytest.mark.asyncio
    async def test_compression_selection(self, optimizer):
        """Test automatic compression type selection"""
        # Different data types
        json_data = '{"key": "value"}' * 100
        binary_data = bytes(range(256)) * 10
        text_data = "Hello World! " * 100
        
        # Should select appropriate compression
        json_compressed = await optimizer.auto_compress(json_data)
        assert json_compressed.compression_type == CompressionType.GZIP
        
        binary_compressed = await optimizer.auto_compress(binary_data)
        assert binary_compressed.compression_type == CompressionType.LZ4
        
        text_compressed = await optimizer.auto_compress(text_data)
        assert text_compressed.compression_type == CompressionType.ZSTD
    
    def test_metrics_export(self, optimizer):
        """Test metrics export"""
        metrics = optimizer.export_metrics()
        
        assert "total_processed" in metrics
        assert "memory_usage_mb" in metrics
        assert "compression_ratio" in metrics
        assert "zero_copy_transfers" in metrics
        assert "gc_optimizations" in metrics
        assert "average_chunk_size" in metrics
    
    @pytest.mark.asyncio
    async def test_concurrent_streams(self, optimizer):
        """Test concurrent stream processing"""
        # Create multiple streams
        streams = []
        for i in range(5):
            stream = async_generator([f"stream{i}-item{j}" for j in range(100)])
            streams.append(stream)
        
        # Process concurrently
        results = await asyncio.gather(*[
            optimizer.collect_stream(stream) for stream in streams
        ])
        
        assert len(results) == 5
        for i, result in enumerate(results):
            assert len(result) == 100
            assert all(f"stream{i}" in item for item in result)
    
    @pytest.mark.asyncio
    async def test_memory_mapped_processing(self, optimizer):
        """Test memory-mapped file processing"""

            tmp.write(b"x" * 1024 * 1024)  # 1MB
            tmp_path = tmp.name
        
        try:
            # Process using memory mapping
            result = await optimizer.process_mmap_file(tmp_path)
            assert result is not None
            assert optimizer.metrics.mmap_operations > 0
        finally:
            import os
            os.unlink(tmp_path)

async def async_generator(items: List):
    """Helper to create async generator"""
    for item in items:
        yield item