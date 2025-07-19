"""
Enhanced Knowledge Sage Tests - TDD Implementation
Tests for vector search, auto-tagging, and quality assurance features
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pytest

from libs.four_sages.knowledge.enhanced_knowledge_sage import EnhancedKnowledgeSage


class TestEnhancedKnowledgeSage:
    """Test suite for Enhanced Knowledge Sage with vector search and auto-tagging"""

    @pytest.fixture
    def sage(self):
        """Create Enhanced Knowledge Sage instance"""
        return EnhancedKnowledgeSage()

    @pytest.fixture
    def sample_knowledge(self):
        """Sample knowledge entries for testing"""
        return [
            {
                "title": "Python Async Programming",
                "content": "Asyncio is a library to write concurrent code using async/await syntax.",
                "category": "development",
                "tags": ["python", "async", "concurrency"],
            },
            {
                "title": "Docker Best Practices",
                "content": "Always use multi-stage builds to reduce image size and improve security.",
                "category": "best_practices",
                "tags": ["docker", "devops", "containers"],
            },
            {
                "title": "TDD Methodology",
                "content": "Test-Driven Development involves writing tests before implementation code.",
                "category": "processes",
                "tags": ["testing", "tdd", "methodology"],
            },
        ]

    @pytest.mark.asyncio
    async def test_vector_embedding_generation(self, sage):
        """Test that knowledge entries generate proper vector embeddings"""
        text = "This is a test document about Python programming"
        embedding = await sage.generate_embedding(text)

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)  # Using sentence-transformers dimension
        assert -1 <= embedding.min() <= embedding.max() <= 1

    @pytest.mark.asyncio
    async def test_semantic_search(self, sage, sample_knowledge):
        """Test semantic/vector search functionality"""
        # Store sample knowledge
        for knowledge in sample_knowledge:
            await sage.store_knowledge(
                title=knowledge["title"],
                content=knowledge["content"],
                category=knowledge["category"],
                tags=knowledge["tags"],
            )

        # Perform semantic search
        query = "How to write asynchronous Python code?"
        results = await sage.semantic_search(query, top_k=2)

        assert len(results) <= 2
        assert results[0]["title"] == "Python Async Programming"
        assert results[0]["similarity_score"] > 0.7
        assert "similarity_score" in results[0]

    @pytest.mark.asyncio
    async def test_auto_tagging(self, sage):
        """Test automatic tag generation from content"""
        content = """
        This article discusses machine learning algorithms, particularly
        neural networks and deep learning. We'll explore TensorFlow and PyTorch
        for implementing convolutional neural networks (CNN) and transformers.
        """

        tags = await sage.auto_generate_tags(content)

        assert isinstance(tags, list)
        assert len(tags) > 0
        assert len(tags) <= 10  # Limit number of tags
        expected_tags = ["machine-learning", "neural-networks", "deep-learning"]
        assert any(tag in tags for tag in expected_tags)

    @pytest.mark.asyncio
    async def test_knowledge_categorization(self, sage):
        """Test automatic category classification"""
        content = "Fix critical security vulnerability in authentication system"

        category = await sage.auto_categorize(content)

        assert category in sage.categories
        assert category == "troubleshooting"

    @pytest.mark.asyncio
    async def test_knowledge_quality_scoring(self, sage):
        """Test knowledge quality assessment"""
        # High quality knowledge
        high_quality = {
            "title": "Comprehensive Guide to Microservices Architecture",
            "content": """
            Microservices architecture is a design pattern where applications are built
            as a collection of small, autonomous services. Each service is self-contained
            and implements a single business capability. Key benefits include:
            1. Scalability - Services can be scaled independently
            2. Flexibility - Different technologies can be used for different services
            3. Resilience - Failure of one service doesn't bring down the entire system

            Implementation considerations:
            - Service discovery and registration
            - Inter-service communication (REST, gRPC, message queues)
            - Data consistency and distributed transactions
            - Monitoring and observability
            """,
            "category": "architecture",
            "tags": ["microservices", "architecture", "design-patterns"],
        }

        # Low quality knowledge
        low_quality = {
            "title": "Bug fix",
            "content": "Fixed the thing",
            "category": "troubleshooting",
            "tags": [],
        }

        high_score = await sage.assess_knowledge_quality(high_quality)
        low_score = await sage.assess_knowledge_quality(low_quality)

        assert 0 <= high_score <= 1
        assert 0 <= low_score <= 1
        assert high_score > low_score
        assert high_score > 0.7  # High quality threshold
        assert low_score < 0.3  # Low quality threshold

    @pytest.mark.asyncio
    async def test_knowledge_deduplication(self, sage):
        """Test duplicate knowledge detection"""
        original = {
            "title": "Docker Compose Guide",
            "content": "Docker Compose is a tool for defining multi-container applications",
            "category": "tools",
            "tags": ["docker", "containers"],
        }

        # Store original
        await sage.store_knowledge(**original)

        # Try to store near-duplicate
        duplicate = {
            "title": "Guide to Docker Compose",
            "content": "Docker Compose is a utility for defining applications with multiple containers",
            "category": "tools",
            "tags": ["docker", "compose"],
        }

        is_duplicate, similarity = await sage.check_duplicate(duplicate)

        assert is_duplicate is True
        assert similarity > 0.8

    @pytest.mark.asyncio
    async def test_knowledge_versioning(self, sage):
        """Test knowledge version control"""
        # Create initial version
        knowledge_id = await sage.store_knowledge(
            title="API Design Guide",
            content="RESTful API design principles",
            category="architecture",
            tags=["api", "rest"],
        )

        # Update knowledge
        await sage.update_knowledge(
            knowledge_id,
            content="RESTful API design principles with GraphQL comparison",
        )

        # Get version history
        history = await sage.get_knowledge_history(knowledge_id)

        assert len(history) == 2
        assert history[0]["version"] == 1
        assert history[1]["version"] == 2
        assert "RESTful API design principles" in history[0]["content"]
        assert "GraphQL" in history[1]["content"]

    @pytest.mark.asyncio
    async def test_knowledge_relationships(self, sage):
        """Test knowledge graph relationships"""
        # Create related knowledge entries
        python_id = await sage.store_knowledge(
            title="Python Basics",
            content="Introduction to Python programming",
            category="development",
            tags=["python", "programming"],
        )

        django_id = await sage.store_knowledge(
            title="Django Framework",
            content="Web development with Django",
            category="development",
            tags=["python", "django", "web"],
        )

        # Create relationship
        await sage.create_relationship(
            source_id=python_id, target_id=django_id, relationship_type="prerequisite"
        )

        # Get related knowledge
        related = await sage.get_related_knowledge(django_id)

        assert len(related) > 0
        assert any(r["id"] == python_id for r in related)
        assert any(r["relationship_type"] == "prerequisite" for r in related)

    @pytest.mark.asyncio
    async def test_batch_knowledge_import(self, sage):
        """Test bulk knowledge import with progress tracking"""
        knowledge_batch = [
            {
                "title": f"Knowledge Entry {i}",
                "content": f"Content for entry {i}",
                "category": "development",
                "tags": ["batch", "import"],
            }
            for i in range(100)
        ]

        progress_updates = []

        async def progress_callback(current, total):
            progress_updates.append((current, total))

        results = await sage.batch_import_knowledge(
            knowledge_batch, progress_callback=progress_callback
        )

        assert results["total"] == 100
        assert results["successful"] == 100
        assert results["failed"] == 0
        assert len(progress_updates) > 0
        assert progress_updates[-1] == (100, 100)

    @pytest.mark.asyncio
    async def test_knowledge_expiration(self, sage):
        """Test knowledge expiration and archival"""
        # Create knowledge with expiration
        knowledge_id = await sage.store_knowledge(
            title="Temporary Fix",
            content="Workaround for issue #123",
            category="troubleshooting",
            tags=["temporary", "workaround"],
            expires_in_days=1,
        )

        # Check if knowledge is expired
        is_expired = await sage.is_knowledge_expired(knowledge_id)
        assert is_expired is False

        # Simulate time passage
        with patch("datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime.now().replace(
                day=datetime.now().day + 2
            )
            is_expired = await sage.is_knowledge_expired(knowledge_id)
            assert is_expired is True

    @pytest.mark.asyncio
    async def test_sage_collaboration(self, sage):
        """Test integration with other sages"""
        # Mock other sages
        mock_task_sage = Mock()
        mock_incident_sage = Mock()
        mock_rag_sage = Mock()

        sage.set_collaborators(
            task_sage=mock_task_sage,
            incident_sage=mock_incident_sage,
            rag_sage=mock_rag_sage,
        )

        # Test knowledge sharing with Task Sage
        task_context = {"current_task": "implement_feature"}
        relevant_knowledge = await sage.get_knowledge_for_task(task_context)

        assert isinstance(relevant_knowledge, list)

        # Test incident knowledge lookup
        incident_context = {"error_type": "database_connection"}
        incident_knowledge = await sage.get_incident_solutions(incident_context)

        assert isinstance(incident_knowledge, list)

    @pytest.mark.asyncio
    async def test_knowledge_analytics(self, sage, sample_knowledge):
        """Test knowledge usage analytics"""
        # Store and access knowledge
        for knowledge in sample_knowledge:
            knowledge_id = await sage.store_knowledge(**knowledge)
            # Simulate access
            await sage.get_knowledge(knowledge_id)
            await sage.get_knowledge(knowledge_id)

        # Get analytics
        analytics = await sage.get_knowledge_analytics()

        assert "total_entries" in analytics
        assert "categories_distribution" in analytics
        assert "popular_tags" in analytics
        assert "access_patterns" in analytics
        assert analytics["total_entries"] == len(sample_knowledge)

    @pytest.mark.asyncio
    async def test_knowledge_export(self, sage, sample_knowledge):
        """Test knowledge export functionality"""
        # Store sample knowledge
        for knowledge in sample_knowledge:
            await sage.store_knowledge(**knowledge)

        # Export to different formats
        json_export = await sage.export_knowledge(format="json")
        markdown_export = await sage.export_knowledge(format="markdown")

        assert isinstance(json_export, str)
        assert isinstance(markdown_export, str)
        assert "Python Async Programming" in json_export
        assert "# Python Async Programming" in markdown_export

    @pytest.mark.asyncio
    async def test_performance_optimization(self, sage):
        """Test caching and performance features"""
        # Enable caching
        sage.enable_caching(ttl_seconds=300)

        # First search (cache miss)
        start_time = asyncio.get_event_loop().time()
        results1 = await sage.semantic_search("Python programming", top_k=5)
        first_duration = asyncio.get_event_loop().time() - start_time

        # Second search (cache hit)
        start_time = asyncio.get_event_loop().time()
        results2 = await sage.semantic_search("Python programming", top_k=5)
        second_duration = asyncio.get_event_loop().time() - start_time

        assert results1 == results2
        assert second_duration < first_duration * 0.1  # Cache should be much faster

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, sage):
        """Test thread-safe concurrent operations"""

        async def store_knowledge_task(i):
            return await sage.store_knowledge(
                title=f"Concurrent Entry {i}",
                content=f"Content {i}",
                category="development",
                tags=["concurrent"],
            )

        # Run concurrent stores
        tasks = [store_knowledge_task(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(isinstance(r, str) for r in results)  # All should return IDs
        assert len(set(results)) == 10  # All IDs should be unique
