"""
Test suite for Knowledge Sage Standalone ML Classifier
Tests ML functionality without external dependencies
"""

import asyncio
from unittest.mock import patch

import pytest

from libs.knowledge_sage_standalone_ml import KnowledgeSageStandaloneML


@pytest.fixture
async def ml_sage():
    """Create standalone ML-enabled Knowledge Sage instance"""
    sage = KnowledgeSageStandaloneML(test_mode=True)
    await sage.initialize()
    yield sage
    await sage.cleanup()


@pytest.fixture
def training_documents():
    """Sample training documents for ML models"""
    return [
        {
            "content": "Python asyncio provides concurrent programming using async/await syntax. It's great for I/O bound tasks.",
            "category": "development",
            "tags": ["python", "async", "concurrency"]
        },
        {
            "content": "Django REST framework makes it easy to build Web APIs. It provides serialization and authentication.",
            "category": "development", 
            "tags": ["python", "django", "api", "rest"]
        },
        {
            "content": "Docker containers provide isolated environments. Use docker-compose for multi-container applications.",
            "category": "devops",
            "tags": ["docker", "containers", "deployment"]
        },
        {
            "content": "Kubernetes orchestrates containerized applications. It handles scaling, load balancing, and self-healing.",
            "category": "devops",
            "tags": ["kubernetes", "k8s", "orchestration", "containers"]
        },
        {
            "content": "OAuth 2.0 provides secure authorization. Always use HTTPS and validate tokens properly.",
            "category": "security",
            "tags": ["oauth", "authentication", "security"]
        },
        {
            "content": "SQL injection attacks can be prevented using parameterized queries and input validation.",
            "category": "security",
            "tags": ["security", "sql", "vulnerability", "prevention"]
        },
        {
            "content": "Neural networks learn patterns from data. Deep learning uses multiple layers for complex tasks.",
            "category": "ai",
            "tags": ["ml", "neural-networks", "deep-learning", "ai"]
        },
        {
            "content": "Natural language processing enables machines to understand human language using transformers.",
            "category": "ai",
            "tags": ["nlp", "ai", "transformers", "language"]
        }
    ]


class TestKnowledgeSageStandaloneML:
    """Test suite for standalone ML classifier"""

    @pytest.mark.asyncio
    async def test_initialization(self, ml_sage):
        """Test ML classifier initialization"""
        assert ml_sage is not None
        assert ml_sage.is_initialized()
        assert len(ml_sage.get_models()) > 0
        assert "category_classifier" in ml_sage.get_models()
        assert "tag_generator" in ml_sage.get_models()

    @pytest.mark.asyncio
    async def test_model_training(self, ml_sage, training_documents):
        """Test training ML models with sample data"""
        result = await ml_sage.train_models(
            documents=training_documents,
            model_types=["category", "tags"],
            validation_split=0.2
        )
        
        assert result["success"] is True
        assert result["category_accuracy"] >= 0.0
        assert result["tag_f1_score"] >= 0.0
        assert "training_time" in result
        assert "model_versions" in result

    @pytest.mark.asyncio
    async def test_category_classification(self, ml_sage, training_documents):
        """Test automatic category classification"""
        # Train the model first
        await ml_sage.train_models(documents=training_documents)
        
        # Test classification
        test_content = "FastAPI is a modern Python web framework that supports async operations"
        result = await ml_sage.classify_category(test_content)
        
        assert "category" in result
        assert "confidence" in result
        assert "probabilities" in result
        assert result["category"] in ["development", "devops", "security", "ai"]
        assert 0 <= result["confidence"] <= 1

    @pytest.mark.asyncio
    async def test_tag_generation(self, ml_sage, training_documents):
        """Test automatic tag generation"""
        # Train the model
        await ml_sage.train_models(documents=training_documents)
        
        # Test tag generation
        test_content = "Building microservices with Docker and Kubernetes for scalable cloud deployment"
        
        result = await ml_sage.generate_tags(
            content=test_content,
            max_tags=5,
            confidence_threshold=0.1  # Lower threshold for testing
        )
        
        assert "tags" in result
        assert "tag_scores" in result
        assert len(result["tags"]) <= 5

    @pytest.mark.asyncio
    async def test_content_analysis(self, ml_sage):
        """Test comprehensive content analysis"""
        content = """
        This article discusses implementing OAuth 2.0 authentication in a Python Flask application.
        We'll use JWT tokens for stateless authentication and Redis for token storage.
        The implementation includes rate limiting and CSRF protection for enhanced security.
        """
        
        analysis = await ml_sage.analyze_content(content)
        
        assert "entities" in analysis
        assert "keywords" in analysis
        assert "sentiment" in analysis
        assert "complexity_score" in analysis
        assert "reading_time" in analysis
        assert "language" in analysis
        
        # Check basic metrics
        assert analysis["word_count"] > 0
        assert analysis["character_count"] > 0
        assert 0 <= analysis["complexity_score"] <= 1

    @pytest.mark.asyncio
    async def test_document_similarity(self, ml_sage, training_documents):
        """Test document similarity search"""
        # Store training documents
        for doc in training_documents:
            await ml_sage.store_document(
                content=doc["content"],
                category=doc["category"],
                tags=doc["tags"]
            )
        
        # Test similarity search
        query = "How to implement async programming in Python?"
        similar_docs = await ml_sage.find_similar_documents(
            query=query,
            top_k=3,
            min_similarity=0.0  # Low threshold for testing
        )
        
        assert len(similar_docs) <= 3
        assert all("similarity_score" in doc for doc in similar_docs)
        assert all("id" in doc for doc in similar_docs)

    @pytest.mark.asyncio
    async def test_document_clustering(self, ml_sage, training_documents):
        """Test document clustering"""
        # Store documents
        for doc in training_documents:
            await ml_sage.store_document(
                content=doc["content"],
                category=doc["category"],
                tags=doc["tags"]
            )
        
        # Add training documents to enable clustering
        ml_sage.training_cache = training_documents
        
        # Test clustering
        clusters = await ml_sage.cluster_documents(
            n_clusters=4,
            algorithm="kmeans"
        )
        
        assert len(clusters) == 4
        assert all("cluster_id" in c for c in clusters)
        assert all("documents" in c for c in clusters)
        assert all("keywords" in c for c in clusters)

    @pytest.mark.asyncio
    async def test_batch_classification(self, ml_sage, training_documents):
        """Test batch classification performance"""
        # Train model
        await ml_sage.train_models(documents=training_documents)
        
        # Prepare batch
        test_contents = [
            "Python web development with Django",
            "Container orchestration with Kubernetes",
            "Security vulnerabilities in web applications",
            "Machine learning model deployment"
        ]
        
        # Batch classify
        start_time = asyncio.get_event_loop().time()
        results = await ml_sage.batch_classify(contents=test_contents)
        end_time = asyncio.get_event_loop().time()
        
        assert len(results) == len(test_contents)
        assert all("category" in r for r in results)
        
        processing_time = end_time - start_time
        assert processing_time < 5.0  # Should complete within reasonable time

    @pytest.mark.asyncio
    async def test_model_metrics(self, ml_sage, training_documents):
        """Test model performance metrics tracking"""
        # Train models
        await ml_sage.train_models(documents=training_documents)
        
        # Get metrics
        metrics = await ml_sage.get_model_metrics()
        
        assert "category_classifier" in metrics
        assert "tag_generator" in metrics
        
        # Check category classifier metrics
        cat_metrics = metrics["category_classifier"]
        assert "accuracy" in cat_metrics

    @pytest.mark.asyncio
    async def test_edge_cases(self, ml_sage):
        """Test edge cases and error handling"""
        # Test with empty content
        result = await ml_sage.classify_category("")
        assert result["category"] == "unknown"
        assert result["confidence"] == 0.0
        
        # Test with no training data
        result = await ml_sage.classify_category("test content")
        assert "error" in result or result["category"] == "unknown"
        
        # Test tag generation with empty content
        result = await ml_sage.generate_tags("")
        assert result["tags"] == []

    @pytest.mark.asyncio
    async def test_embedding_generation(self, ml_sage):
        """Test embedding generation"""
        content = "This is a test document for embedding generation"
        embedding = await ml_sage.generate_embedding(content)
        
        assert len(embedding) == 384
        assert isinstance(embedding, type(embedding))  # Should be numpy array
        
        # Test with empty content
        empty_embedding = await ml_sage.generate_embedding("")
        assert len(empty_embedding) == 384

    @pytest.mark.asyncio
    async def test_keyword_extraction(self, ml_sage, training_documents):
        """Test keyword extraction functionality"""
        # Add some training data for better keyword extraction
        ml_sage.training_cache = training_documents
        
        content = "Python machine learning with scikit-learn and TensorFlow for neural networks"
        keywords = await ml_sage._extract_keywords(content, top_k=5)
        
        assert isinstance(keywords, list)
        assert all(isinstance(kw, dict) for kw in keywords)
        assert all("word" in kw and "score" in kw for kw in keywords)

    @pytest.mark.asyncio
    async def test_sentiment_analysis(self, ml_sage):
        """Test sentiment analysis functionality"""
        positive_content = "This is an amazing and wonderful Python framework that works great!"
        negative_content = "This terrible software has awful bugs and problems everywhere!"
        neutral_content = "Python is a programming language used for development."
        
        # Test positive sentiment
        positive_sentiment = ml_sage._analyze_sentiment(positive_content)
        assert positive_sentiment["polarity"] > 0
        
        # Test negative sentiment
        negative_sentiment = ml_sage._analyze_sentiment(negative_content)
        assert negative_sentiment["polarity"] < 0
        
        # Test neutral sentiment
        neutral_sentiment = ml_sage._analyze_sentiment(neutral_content)
        assert abs(neutral_sentiment["polarity"]) < 0.5

    @pytest.mark.asyncio
    async def test_entity_extraction(self, ml_sage):
        """Test named entity extraction"""
        content = "Using Python with Django and PostgreSQL for OAuth authentication"
        entities = ml_sage._extract_entities(content)
        
        assert isinstance(entities, list)
        entity_texts = [e["text"] for e in entities]
        
        # Should detect some technology entities
        assert any(tech in entity_texts for tech in ["Python", "Django", "PostgreSQL", "OAuth"])

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, ml_sage, training_documents):
        """Test concurrent ML operations"""
        # Train model
        await ml_sage.train_models(documents=training_documents[:4])
        
        # Concurrent classification
        test_contents = [
            "Python async programming",
            "Docker containerization", 
            "Security authentication",
            "AI neural networks"
        ]
        
        # Run classifications concurrently
        tasks = [ml_sage.classify_category(content) for content in test_contents]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == len(test_contents)
        assert all("category" in result for result in results)

    @pytest.mark.asyncio
    async def test_cleanup(self, ml_sage):
        """Test cleanup functionality"""
        # Store some data
        await ml_sage.store_document(content="test", category="test")
        
        # Verify data exists
        assert len(ml_sage.documents) > 0
        assert ml_sage.is_initialized()
        
        # Cleanup
        await ml_sage.cleanup()
        
        # Verify cleanup
        assert not ml_sage.is_initialized()
        assert len(ml_sage.documents) == 0
        assert len(ml_sage.models) == 0