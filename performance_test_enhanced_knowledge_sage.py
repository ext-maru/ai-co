#!/usr/bin/env python3
"""
Performance Test Suite for Enhanced Knowledge Sage
Tests load handling, memory usage, and response times
"""

import asyncio
import time
import psutil
import sys
import gc
from typing import Dict, List, Any
import numpy as np
from pathlib import Path

sys.path.insert(0, '/home/aicompany/ai_co')
from libs.four_sages.knowledge.enhanced_knowledge_sage import EnhancedKnowledgeSage


class PerformanceTester:
    """Performance testing suite for Enhanced Knowledge Sage"""
    
    def __init__(self):
        self.sage = None
        self.results = {}
        self.test_data = []
        
    def setup(self):
        """Set up test environment"""
        print("🔧 Setting up performance test environment...")
        
        # Create sage with unique test database
        import tempfile
        import os
        test_db_dir = tempfile.mkdtemp(prefix="perf_test_")
        self.test_db_path = test_db_dir
        
        # Initialize sage with test database
        self.sage = EnhancedKnowledgeSage()
        self.sage.knowledge_base_path = test_db_dir
        self.sage.db_path = os.path.join(test_db_dir, "test_knowledge.db")
        self.sage._init_database()  # Initialize test database
        
        # Generate test data
        self.test_data = self._generate_test_data(100)
        print(f"✅ Generated {len(self.test_data)} test knowledge entries")
        print(f"🗄️ Using test database: {self.sage.db_path}")
    
    def _generate_test_data(self, count: int) -> List[Dict[str, Any]]:
        """Generate test knowledge data"""
        test_data = []
        
        topics = ["Python", "JavaScript", "Docker", "Kubernetes", "React", "Vue", "Angular", 
                 "Machine Learning", "Deep Learning", "Data Science", "DevOps", "Security"]
        
        for i in range(count):
            topic = topics[i % len(topics)]
            test_data.append({
                "title": f"{topic} Guide {i:03d} - Performance Test",
                "content": f"""
                This is a comprehensive guide about {topic} (entry {i}).
                
                {topic} is an important technology in modern software development.
                This entry covers various aspects including:
                
                - Basic concepts and principles of {topic}
                - Best practices for {topic} implementation
                - Common patterns and anti-patterns
                - Performance optimization techniques
                - Integration with other technologies
                
                Advanced topics include:
                - Scaling {topic} applications
                - Monitoring and debugging
                - Security considerations
                - Future trends and developments
                
                This content is unique for entry {i} and covers {topic} specifically
                to ensure no duplicates are created during performance testing.
                """,
                "category": ["development", "architecture", "best_practices"][i % 3],
                "tags": [f"tag-{i}", topic.lower().replace(" ", "-"), "performance", "test"]
            })
        
        return test_data
    
    async def test_memory_usage(self) -> Dict[str, Any]:
        """Test memory usage patterns"""
        print("\n💾 Testing memory usage...")
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        results = {
            "initial_memory_mb": initial_memory,
            "peak_memory_mb": initial_memory,
            "memory_growth_mb": 0,
            "memory_efficiency": "UNKNOWN"
        }
        
        # Store test data and monitor memory
        for i, data in enumerate(self.test_data):
            await self.sage.store_knowledge(**data)
            
            if i % 10 == 0:  # Check every 10 entries
                current_memory = process.memory_info().rss / 1024 / 1024
                results["peak_memory_mb"] = max(results["peak_memory_mb"], current_memory)
                
                if i > 0:
                    print(f"   Entry {i:3d}: {current_memory:.1f} MB (+{current_memory - initial_memory:.1f} MB)")
        
        final_memory = process.memory_info().rss / 1024 / 1024
        results["final_memory_mb"] = final_memory
        results["memory_growth_mb"] = final_memory - initial_memory
        
        # Calculate efficiency
        if results["memory_growth_mb"] < 50:
            results["memory_efficiency"] = "EXCELLENT"
        elif results["memory_growth_mb"] < 100:
            results["memory_efficiency"] = "GOOD"
        elif results["memory_growth_mb"] < 200:
            results["memory_efficiency"] = "ACCEPTABLE"
        else:
            results["memory_efficiency"] = "POOR"
        
        print(f"   📊 Memory growth: {results['memory_growth_mb']:.1f} MB ({results['memory_efficiency']})")
        
        return results
    
    async def test_search_performance(self) -> Dict[str, Any]:
        """Test search performance with various loads"""
        print("\n🔍 Testing search performance...")
        
        search_queries = [
            "Python async programming",
            "machine learning algorithms",
            "database optimization",
            "performance testing",
            "vector embeddings"
        ]
        
        results = {
            "queries_tested": len(search_queries),
            "total_time_ms": 0,
            "average_time_ms": 0,
            "fastest_ms": float('inf'),
            "slowest_ms": 0,
            "performance_rating": "UNKNOWN"
        }
        
        times = []
        
        for query in search_queries:
            start_time = time.perf_counter()
            
            # Test semantic search
            search_results = await self.sage.semantic_search(query, top_k=10)
            
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            times.append(duration_ms)
            
            results["fastest_ms"] = min(results["fastest_ms"], duration_ms)
            results["slowest_ms"] = max(results["slowest_ms"], duration_ms)
            
            print(f"   Query '{query[:30]}...': {duration_ms:.2f}ms ({len(search_results)} results)")
        
        results["total_time_ms"] = sum(times)
        results["average_time_ms"] = sum(times) / len(times)
        
        # Rate performance
        if results["average_time_ms"] < 10:
            results["performance_rating"] = "EXCELLENT"
        elif results["average_time_ms"] < 50:
            results["performance_rating"] = "GOOD"
        elif results["average_time_ms"] < 100:
            results["performance_rating"] = "ACCEPTABLE"
        else:
            results["performance_rating"] = "POOR"
        
        print(f"   📊 Average search time: {results['average_time_ms']:.2f}ms ({results['performance_rating']})")
        
        return results
    
    async def test_concurrent_operations(self) -> Dict[str, Any]:
        """Test concurrent operation handling"""
        print("\n⚡ Testing concurrent operations...")
        
        async def concurrent_store(data, task_id):
            """Store knowledge concurrently"""
            start_time = time.perf_counter()
            try:
                knowledge_id = await self.sage.store_knowledge(
                    title=f"Concurrent Test {task_id} - {int(time.time() * 1000000)}",  # Add timestamp for uniqueness
                    content=f"{data['content']} - Unique content for task {task_id}",
                    category=data["category"],
                    tags=data["tags"] + [f"concurrent-{task_id}", f"timestamp-{int(time.time())}"]
                )
                success = True
            except Exception as e:
                knowledge_id = None
                success = False
                print(f"     Task {task_id} failed: {str(e)[:50]}...")
            
            end_time = time.perf_counter()
            return {
                "task_id": task_id,
                "knowledge_id": knowledge_id,
                "success": success,
                "duration_ms": (end_time - start_time) * 1000
            }
        
        # Test with different concurrency levels
        concurrency_levels = [1, 5, 10]
        results = {}
        
        for level in concurrency_levels:
            print(f"   Testing with {level} concurrent operations...")
            
            start_time = time.perf_counter()
            
            # Create concurrent tasks
            tasks = []
            for i in range(level):
                task = concurrent_store(self.test_data[i % len(self.test_data)], i)
                tasks.append(task)
            
            # Execute concurrently
            task_results = await asyncio.gather(*tasks)
            
            end_time = time.perf_counter()
            total_duration = (end_time - start_time) * 1000
            
            # Calculate metrics
            individual_times = [r["duration_ms"] for r in task_results]
            
            successful_tasks = [r for r in task_results if r.get("success", False)]
            
            results[f"concurrent_{level}"] = {
                "total_time_ms": total_duration,
                "average_individual_ms": sum(individual_times) / len(individual_times),
                "throughput_ops_per_sec": level / (total_duration / 1000),
                "successful_operations": len(successful_tasks),
                "success_rate": len(successful_tasks) / len(task_results) * 100
            }
            
            print(f"     Total time: {total_duration:.2f}ms")
            print(f"     Throughput: {results[f'concurrent_{level}']['throughput_ops_per_sec']:.2f} ops/sec")
        
        return results
    
    async def test_scalability(self) -> Dict[str, Any]:
        """Test system scalability with increasing load"""
        print("\n📈 Testing scalability...")
        
        dataset_sizes = [10, 50, 100]
        results = {}
        
        for size in dataset_sizes:
            print(f"   Testing with {size} knowledge entries...")
            
            # Reset sage for clean test
            test_sage = EnhancedKnowledgeSage()
            
            # Store data
            store_times = []
            for i in range(size):
                start_time = time.perf_counter()
                await test_sage.store_knowledge(**self.test_data[i % len(self.test_data)])
                end_time = time.perf_counter()
                store_times.append((end_time - start_time) * 1000)
            
            # Test search performance
            search_times = []
            for i in range(5):  # 5 search operations
                start_time = time.perf_counter()
                await test_sage.semantic_search("test query", top_k=5)
                end_time = time.perf_counter()
                search_times.append((end_time - start_time) * 1000)
            
            results[f"size_{size}"] = {
                "dataset_size": size,
                "average_store_ms": sum(store_times) / len(store_times),
                "average_search_ms": sum(search_times) / len(search_times),
                "total_store_time_ms": sum(store_times),
                "cache_size": len(test_sage.embeddings_cache)
            }
            
            print(f"     Avg store time: {results[f'size_{size}']['average_store_ms']:.2f}ms")
            print(f"     Avg search time: {results[f'size_{size}']['average_search_ms']:.2f}ms")
        
        # Calculate scalability trend
        search_times = [results[f"size_{size}"]["average_search_ms"] for size in dataset_sizes]
        if len(search_times) >= 2:
            growth_rate = (search_times[-1] - search_times[0]) / search_times[0]
            if growth_rate < 0.5:  # Less than 50% increase
                scalability_rating = "EXCELLENT"
            elif growth_rate < 1.0:  # Less than 100% increase
                scalability_rating = "GOOD"
            elif growth_rate < 2.0:  # Less than 200% increase
                scalability_rating = "ACCEPTABLE"
            else:
                scalability_rating = "POOR"
        else:
            scalability_rating = "UNKNOWN"
        
        results["scalability_rating"] = scalability_rating
        print(f"   📊 Scalability rating: {scalability_rating}")
        
        return results
    
    async def test_cache_efficiency(self) -> Dict[str, Any]:
        """Test caching system efficiency"""
        print("\n🗄️ Testing cache efficiency...")
        
        # Enable caching
        self.sage.enable_caching(ttl_seconds=300)
        
        results = {
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_efficiency_percent": 0
        }
        
        # Perform repeated searches to test cache
        repeated_queries = ["Python programming", "async functions", "database design"]
        
        for query in repeated_queries:
            # First search (cache miss)
            start_time = time.perf_counter()
            await self.sage.semantic_search(query, top_k=5)
            first_time = time.perf_counter() - start_time
            
            # Second search (should be cache hit)
            start_time = time.perf_counter()
            await self.sage.semantic_search(query, top_k=5)
            second_time = time.perf_counter() - start_time
            
            # Check if second search was significantly faster
            if second_time < first_time * 0.5:  # At least 50% faster
                results["cache_hits"] += 1
                print(f"   Cache HIT for '{query}': {first_time*1000:.2f}ms -> {second_time*1000:.2f}ms")
            else:
                results["cache_misses"] += 1
                print(f"   Cache MISS for '{query}': {first_time*1000:.2f}ms -> {second_time*1000:.2f}ms")
        
        total_tests = results["cache_hits"] + results["cache_misses"]
        results["cache_efficiency_percent"] = (results["cache_hits"] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"   📊 Cache efficiency: {results['cache_efficiency_percent']:.1f}%")
        
        return results
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run complete performance test suite"""
        print("🚀 Starting Enhanced Knowledge Sage Performance Tests")
        print("=" * 60)
        
        self.setup()
        
        # Run all performance tests
        memory_results = await self.test_memory_usage()
        search_results = await self.test_search_performance()
        concurrent_results = await self.test_concurrent_operations()
        scalability_results = await self.test_scalability()
        cache_results = await self.test_cache_efficiency()
        
        # Compile overall results
        overall_results = {
            "test_timestamp": time.time(),
            "test_data_size": len(self.test_data),
            "memory_performance": memory_results,
            "search_performance": search_results,
            "concurrent_performance": concurrent_results,
            "scalability_performance": scalability_results,
            "cache_performance": cache_results
        }
        
        # Calculate overall performance score
        score_components = {
            "memory": self._rate_performance(memory_results["memory_efficiency"]),
            "search": self._rate_performance(search_results["performance_rating"]),
            "scalability": self._rate_performance(scalability_results["scalability_rating"]),
            "cache": cache_results["cache_efficiency_percent"]
        }
        
        overall_score = sum(score_components.values()) / len(score_components)
        overall_results["overall_performance_score"] = overall_score
        overall_results["performance_grade"] = self._get_performance_grade(overall_score)
        
        return overall_results
    
    def _rate_performance(self, rating: str) -> float:
        """Convert rating to numeric score"""
        ratings = {
            "EXCELLENT": 95,
            "GOOD": 80,
            "ACCEPTABLE": 65,
            "POOR": 40,
            "UNKNOWN": 50
        }
        return ratings.get(rating, 50)
    
    def _get_performance_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 90:
            return "A+ (Excellent)"
        elif score >= 80:
            return "A (Good)"
        elif score >= 70:
            return "B (Acceptable)"
        elif score >= 60:
            return "C (Needs Improvement)"
        else:
            return "F (Poor)"
    
    def cleanup(self):
        """Clean up test environment"""
        print("\n🧹 Cleaning up test environment...")
        
        # Clean up test database
        if hasattr(self, 'test_db_path'):
            import shutil
            try:
                shutil.rmtree(self.test_db_path)
                print(f"   🗑️ Removed test database: {self.test_db_path}")
            except Exception as e:
                print(f"   ⚠️ Failed to remove test database: {e}")
        
        # Force garbage collection
        gc.collect()


async def main():
    """Run performance tests"""
    tester = PerformanceTester()
    
    try:
        results = await tester.run_all_tests()
        
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE TEST SUMMARY")
        print("=" * 60)
        
        print(f"🏆 Overall Performance Grade: {results['performance_grade']}")
        print(f"📈 Overall Score: {results['overall_performance_score']:.1f}/100")
        
        print(f"\n📋 Component Scores:")
        print(f"   💾 Memory: {results['memory_performance']['memory_efficiency']}")
        print(f"   🔍 Search: {results['search_performance']['performance_rating']}")
        print(f"   📈 Scalability: {results['scalability_performance']['scalability_rating']}")
        print(f"   🗄️ Cache: {results['cache_performance']['cache_efficiency_percent']:.1f}%")
        
        print(f"\n🔢 Key Metrics:")
        print(f"   Memory Growth: {results['memory_performance']['memory_growth_mb']:.1f} MB")
        print(f"   Avg Search Time: {results['search_performance']['average_time_ms']:.2f} ms")
        print(f"   Max Throughput: {max([r['throughput_ops_per_sec'] for r in results['concurrent_performance'].values()]):.1f} ops/sec")
        
        print(f"\n💡 Recommendations:")
        if results['memory_performance']['memory_efficiency'] in ['POOR', 'ACCEPTABLE']:
            print("   - Implement memory management and cache limits")
        if results['search_performance']['performance_rating'] in ['POOR', 'ACCEPTABLE']:
            print("   - Consider vector indexing (FAISS) for faster search")
        if results['scalability_performance']['scalability_rating'] in ['POOR', 'ACCEPTABLE']:
            print("   - Optimize database operations and add connection pooling")
        if results['cache_performance']['cache_efficiency_percent'] < 80:
            print("   - Review caching strategy and implementation")
        
        if results['overall_performance_score'] >= 80:
            print("   ✅ Performance is acceptable for production use")
        else:
            print("   ⚠️ Performance improvements needed before production")
        
    finally:
        tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())