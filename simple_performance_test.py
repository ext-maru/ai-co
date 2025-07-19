#!/usr/bin/env python3
"""
Simplified Performance Test for Enhanced Knowledge Sage
"""

import asyncio
import time
import psutil
import sys
import tempfile
import os
import shutil

sys.path.insert(0, '/home/aicompany/ai_co')
from libs.four_sages.knowledge.enhanced_knowledge_sage import EnhancedKnowledgeSage


async def run_performance_test():
    print("🚀 Enhanced Knowledge Sage - Quick Performance Test")
    print("=" * 55)
    
    # Setup isolated test environment
    test_db_dir = tempfile.mkdtemp(prefix="simple_perf_test_")
    sage = EnhancedKnowledgeSage()
    sage.knowledge_base_path = test_db_dir
    sage.db_path = os.path.join(test_db_dir, "test_knowledge.db")
    sage._init_database()
    
    try:
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Test 1: Basic operations
        print("\n📝 Test 1: Basic Storage & Retrieval")
        start_time = time.perf_counter()
        
        knowledge_id = await sage.store_knowledge(
            title="Test Performance Entry",
            content="This is a test entry for performance measurement.",
            category="development",
            tags=["test", "performance"]
        )
        
        store_time = (time.perf_counter() - start_time) * 1000
        print(f"   ✅ Store time: {store_time:.2f}ms")
        
        # Test 2: Search performance
        print("\n🔍 Test 2: Search Performance")
        start_time = time.perf_counter()
        
        results = await sage.semantic_search("test performance", top_k=5)
        
        search_time = (time.perf_counter() - start_time) * 1000
        print(f"   ✅ Search time: {search_time:.2f}ms ({len(results)} results)")
        
        # Test 3: Batch operations
        print("\n📦 Test 3: Batch Operations")
        start_time = time.perf_counter()
        
        for i in range(10):
            await sage.store_knowledge(
                title=f"Batch Entry {i}",
                content=f"This is batch entry number {i} with unique content.",
                category="development",
                tags=[f"batch-{i}", "test"]
            )
        
        batch_time = (time.perf_counter() - start_time) * 1000
        print(f"   ✅ Batch store (10 entries): {batch_time:.2f}ms ({batch_time/10:.2f}ms avg)")
        
        # Test 4: Quality assessment
        print("\n⭐ Test 4: Quality Assessment")
        start_time = time.perf_counter()
        
        quality_score = await sage.assess_knowledge_quality({
            "title": "Comprehensive Guide",
            "content": "This is a detailed guide with multiple sections and examples.",
            "category": "documentation",
            "tags": ["guide", "comprehensive", "examples"]
        })
        
        quality_time = (time.perf_counter() - start_time) * 1000
        print(f"   ✅ Quality assessment: {quality_time:.2f}ms (score: {quality_score:.2f})")
        
        # Test 5: Memory usage
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory
        print(f"\n💾 Memory Usage:")
        print(f"   Initial: {initial_memory:.1f} MB")
        print(f"   Final: {final_memory:.1f} MB")
        print(f"   Growth: {memory_growth:.1f} MB")
        
        # Test 6: Analytics
        print("\n📊 Test 6: Analytics")
        start_time = time.perf_counter()
        
        analytics = await sage.get_knowledge_analytics()
        
        analytics_time = (time.perf_counter() - start_time) * 1000
        print(f"   ✅ Analytics generation: {analytics_time:.2f}ms")
        print(f"   Total entries: {analytics['total_entries']}")
        print(f"   Categories: {len(analytics['categories_distribution'])}")
        
        # Overall performance rating
        print("\n🏆 Performance Summary:")
        
        if store_time < 10 and search_time < 5 and memory_growth < 20:
            rating = "🟢 EXCELLENT"
        elif store_time < 50 and search_time < 20 and memory_growth < 50:
            rating = "🟡 GOOD"
        elif store_time < 100 and search_time < 50 and memory_growth < 100:
            rating = "🟠 ACCEPTABLE"
        else:
            rating = "🔴 NEEDS IMPROVEMENT"
        
        print(f"   Overall Rating: {rating}")
        print(f"   Store Performance: {store_time:.2f}ms")
        print(f"   Search Performance: {search_time:.2f}ms")
        print(f"   Memory Efficiency: {memory_growth:.1f}MB growth")
        
        # Recommendations
        print("\n💡 Recommendations:")
        if store_time > 50:
            print("   - Consider database optimizations for storage")
        if search_time > 20:
            print("   - Implement vector indexing for faster search")
        if memory_growth > 50:
            print("   - Add memory management and cache limits")
        if store_time < 10 and search_time < 5 and memory_growth < 20:
            print("   ✅ Performance is excellent for current implementation")
        
    finally:
        # Cleanup
        try:
            shutil.rmtree(test_db_dir)
            print(f"\n🧹 Cleaned up test database")
        except Exception as e:
            print(f"\n⚠️ Cleanup warning: {e}")


if __name__ == "__main__":
    asyncio.run(run_performance_test())