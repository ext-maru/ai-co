#!/usr/bin/env python3
"""
Enhanced Knowledge Sage Test Suite
TDD implementation for Issue #56-1: 知識ベース管理システム強化

Features tested:
- Elders Legacy architecture compliance
- Vector search capabilities  
- PostgreSQL integration
- Advanced knowledge management
- Batch processing
- Performance optimization
"""

import pytest
import asyncio

import shutil
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Import the class we'll implement
try:
    from libs.four_sages.knowledge.enhanced_knowledge_sage import EnhancedKnowledgeSage
    from libs.four_sages.knowledge.vector_search_engine import VectorSearchEngine
    from libs.four_sages.knowledge.knowledge_schema import KnowledgeEntry, KnowledgeVector
except ImportError:
    # These will be implemented during TDD
    EnhancedKnowledgeSage = None
    VectorSearchEngine = None
    KnowledgeEntry = None
    KnowledgeVector = None

class TestEnhancedKnowledgeSage:
    """Enhanced Knowledge Sage comprehensive test suite"""
    
    @pytest.fixture

        if EnhancedKnowledgeSage is None:
            pytest.skip("EnhancedKnowledgeSage not implemented yet")

        sage = EnhancedKnowledgeSage(

            vector_dimensions=384,  # Sentence transformer default
            enable_postgresql=False  # Use SQLite for tests
        )
        
        yield sage
        
        # Cleanup
        await sage.cleanup()

    @pytest.fixture
    def sample_knowledge_entries(self) -> List[Dict[str, Any]]:
        """Sample knowledge entries for testing"""
        return [
            {
                "title": "TDD Best Practices",
                "content": "Test-Driven Development improves code quality and \

                "category": "development",
                "tags": ["tdd", "testing", "best_practices"],
                "source": "elders_guild_guide",
                "priority": "high"
            },
            {
                "title": "Elder Flow Architecture",
                "content": "Elder Flow provides automated development workflow with 4 Sages integration and \
                    quality gates.",
                "category": "architecture", 
                "tags": ["elder_flow", "architecture", "automation"],
                "source": "technical_documentation",
                "priority": "critical"
            },
            {
                "title": "Python Async Patterns",
                "content": "Asynchronous programming patterns in Python using asyncio for concurrent task execution.",
                "category": "development",
                "tags": ["python", "async", "concurrency"],
                "source": "technical_guide",
                "priority": "medium"
            }
        ]
    
    # Test 1: Elders Legacy Architecture Compliance
    @pytest.mark.asyncio

        """Test Elders Legacy architecture compliance"""

        # Should inherit from EldersLegacyBase
        assert hasattr(sage, 'process_request')
        assert hasattr(sage, 'validate_request')
        assert hasattr(sage, 'get_capabilities')
        assert hasattr(sage, 'execute_with_quality_gate')
        
        # Should have boundary enforcement
        assert hasattr(sage, 'boundary')
        assert sage.boundary == "WISDOM"  # Knowledge Sage domain
        
        # Should pass Iron Will quality standards
        quality_result = await sage.passes_iron_will()
        assert quality_result.get('passes') is True
        assert quality_result.get('score', 0) >= 95.0
    
    # Test 2: Vector Search Engine Integration
    @pytest.mark.asyncio 

        """Test vector search capabilities"""

        # Should have vector search engine
        assert hasattr(sage, 'vector_engine')
        assert sage.vector_engine is not None
        
        # Test vector embedding generation
        text = "This is a test knowledge entry"
        vector = await sage.vector_engine.encode_text(text)
        
        assert vector is not None
        assert isinstance(vector, np.ndarray)
        assert len(vector) == sage.vector_dimensions
        
        # Test vector similarity calculation
        text2 = "This is another test knowledge entry"
        vector2 = await sage.vector_engine.encode_text(text2)
        
        similarity = await sage.vector_engine.calculate_similarity(vector, vector2)
        assert 0.0 <= similarity <= 1.0
        assert similarity > 0.7  # Should be similar texts
    
    # Test 3: Enhanced Knowledge Storage
    @pytest.mark.asyncio

        """Test enhanced knowledge storage with vectors"""

        for entry_data in sample_knowledge_entries:
            result = await sage.process_request({
                "type": "store_enhanced_knowledge",
                **entry_data
            })
            
            assert result["success"] is True
            assert "knowledge_id" in result
            assert "vector_id" in result
            assert "embedding_quality" in result
            
            # Verify storage
            stored = await sage.process_request({
                "type": "get_knowledge",
                "knowledge_id": result["knowledge_id"]
            })
            
            assert stored["success"] is True
            assert stored["knowledge"]["title"] == entry_data["title"]
            assert stored["knowledge"]["vector_embedding"] is not None
    
    # Test 4: Semantic Vector Search
    @pytest.mark.asyncio

        """Test semantic search using vector embeddings"""

        # Store sample entries
        for entry_data in sample_knowledge_entries:
            await sage.process_request({
                "type": "store_enhanced_knowledge",
                **entry_data
            })
        
        # Test semantic search
        search_result = await sage.process_request({
            "type": "semantic_search",
            "query": "testing and development practices",
            "limit": 5,
            "similarity_threshold": 0.7
        })
        
        assert search_result["success"] is True
        assert len(search_result["results"]) > 0
        
        # Should find TDD best practices entry
        titles = [r["title"] for r in search_result["results"]]
        assert "TDD Best Practices" in titles
        
        # Results should be ordered by similarity
        similarities = [r["similarity_score"] for r in search_result["results"]]
        assert similarities == sorted(similarities, reverse=True)
    
    # Test 5: Batch Knowledge Processing
    @pytest.mark.asyncio

        """Test batch processing capabilities"""

        # Test batch storage
        batch_result = await sage.process_request({
            "type": "batch_store_knowledge",
            "entries": sample_knowledge_entries,
            "batch_size": 2
        })
        
        assert batch_result["success"] is True
        assert batch_result["processed_count"] == len(sample_knowledge_entries)
        assert batch_result["failed_count"] == 0
        assert "batch_id" in batch_result
        
        # Test batch status
        status_result = await sage.process_request({
            "type": "get_batch_status",
            "batch_id": batch_result["batch_id"]
        })
        
        assert status_result["success"] is True
        assert status_result["status"] == "completed"
    
    # Test 6: Advanced Knowledge Schema
    @pytest.mark.asyncio

        """Test enhanced knowledge schema with metadata"""

        advanced_entry = {
            "title": "Advanced Schema Test",
            "content": "Testing enhanced knowledge schema with metadata",
            "category": "testing",
            "tags": ["schema", "metadata", "testing"],
            "source": "test_suite",
            "priority": "high",
            "metadata": {
                "author": "Claude Elder",
                "version": "1.0",
                "dependencies": ["base_schema"],
                "complexity_score": 8.5,
                "last_updated": datetime.now().isoformat()
            },
            "relationships": [
                {"type": "depends_on", "target_id": "base_knowledge"},
                {"type": "related_to", "target_id": "schema_guide"}
            ]
        }
        
        result = await sage.process_request({
            "type": "store_enhanced_knowledge",
            **advanced_entry
        })
        
        assert result["success"] is True
        assert "schema_validation" in result
        assert result["schema_validation"]["valid"] is True
        
        # Verify advanced retrieval
        retrieved = await sage.process_request({
            "type": "get_knowledge_with_relationships",
            "knowledge_id": result["knowledge_id"]
        })
        
        assert retrieved["success"] is True
        assert "relationships" in retrieved["knowledge"]
        assert "metadata" in retrieved["knowledge"]
    
    # Test 7: Knowledge Indexing & Performance
    @pytest.mark.asyncio

        """Test knowledge indexing and search performance"""

        # Create larger dataset for performance testing
        large_dataset = []
        for i in range(100):
            large_dataset.append({
                "title": f"Performance Test Entry {i}",
                "content": f"This is performance test content {i} with unique data and information.",
                "category": "performance_test",
                "tags": ["performance", f"test_{i}", "benchmark"],
                "source": "performance_suite"
            })
        
        # Batch store for performance
        start_time = datetime.now()
        batch_result = await sage.process_request({
            "type": "batch_store_knowledge",
            "entries": large_dataset
        })
        storage_time = (datetime.now() - start_time).total_seconds()
        
        assert batch_result["success"] is True
        assert storage_time < 10.0  # Should complete within 10 seconds
        
        # Test search performance
        start_time = datetime.now()
        search_result = await sage.process_request({
            "type": "semantic_search",
            "query": "performance test information",
            "limit": 10
        })
        search_time = (datetime.now() - start_time).total_seconds()
        
        assert search_result["success"] is True
        assert search_time < 0.1  # Should complete within 100ms
        assert len(search_result["results"]) == 10
    
    # Test 8: PostgreSQL Integration (Conditional)
    @pytest.mark.asyncio
    async def test_postgresql_integration(self):
        """Test PostgreSQL integration when available"""
        if EnhancedKnowledgeSage is None:
            pytest.skip("EnhancedKnowledgeSage not implemented yet")
        
        try:
            # Try to create with PostgreSQL enabled
            sage = EnhancedKnowledgeSage(
                knowledge_base_path="test_postgres",
                enable_postgresql=True,
                postgres_config={
                    "host": "localhost",
                    "port": 5432,
                    "database": "test_knowledge",
                    "user": "test_user",
                    "password": "test_pass"
                }
            )
            
            # Test connection
            connection_result = await sage.test_postgresql_connection()
            assert connection_result["success"] is True
            
            await sage.cleanup()
            
        except Exception as e:
            pytest.skip(f"PostgreSQL not available: {e}")
    
    # Test 9: Quality Gates Integration
    @pytest.mark.asyncio

        """Test Iron Will quality gates integration"""

        # Test with quality gate enforcement
        result = await sage.execute_with_quality_gate(
            "store_enhanced_knowledge",
            {
                "title": "Quality Gate Test",
                "content": "Testing quality gate enforcement during knowledge storage",
                "category": "testing",
                "tags": ["quality", "testing"],
                "source": "quality_test"
            }
        )
        
        assert result["success"] is True
        assert "quality_metrics" in result
        assert result["quality_metrics"]["passes_iron_will"] is True
        assert result["quality_metrics"]["quality_score"] >= 95.0
    
    # Test 10: Capabilities and Health Check
    @pytest.mark.asyncio

        """Test sage capabilities and health check"""

        # Test capabilities
        capabilities = sage.get_capabilities()
        
        expected_capabilities = [
            "store_enhanced_knowledge",
            "semantic_search", 
            "batch_store_knowledge",
            "get_batch_status",
            "get_knowledge_with_relationships",
            "vector_search",
            "knowledge_analytics",
            "schema_validation"
        ]
        
        for capability in expected_capabilities:
            assert capability in capabilities
        
        # Test health check
        health_result = await sage.process_request({"type": "health_check"})
        
        assert health_result["success"] is True
        assert health_result["status"] == "healthy"
        assert "vector_engine_status" in health_result
        assert "database_status" in health_result

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])