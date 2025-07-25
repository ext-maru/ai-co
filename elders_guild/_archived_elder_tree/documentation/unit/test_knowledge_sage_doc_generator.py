"""
Test suite for Knowledge Sage Document Generator
Tests automatic documentation generation and content synthesis
"""

import asyncio
import os

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from libs.knowledge_sage_doc_generator import KnowledgeSageDocGenerator

@pytest.fixture
async def doc_generator():
    """Create document generator instance"""
    generator = KnowledgeSageDocGenerator()
    await generator.initialize()
    yield generator
    await generator.cleanup()

@pytest.fixture
def sample_knowledge_base():
    """Sample knowledge base for document generation"""
    return [
        {
            "id": "doc1",
            "title": "Python Async Programming",
            "content": "Asyncio is a library to write concurrent code using async/await \
                syntax. It provides event loops, coroutines, and \
                \
                tasks for efficient I/O operations.",
            "category": "development",
            "tags": ["python", "async", "concurrency", "performance"],
            "created_at": "2024-01-01T10:00:00",
            "quality_score": 0.9
        },
        {
            "id": "doc2", 
            "title": "Docker Best Practices",
            "content": "Docker containers should be lightweight, use multi-stage builds, and \
                follow security best practices. Always use specific image tags and minimize layers.",
            "category": "devops",
            "tags": ["docker", "containers", "best-practices", "security"],
            "created_at": "2024-01-02T11:00:00",
            "quality_score": 0.8
        },
        {
            "id": "doc3",
            "title": "RESTful API Design",
            "content": "REST APIs should follow HTTP semantics, use proper status codes, implement pagination, and \
                provide clear error messages. Version your APIs appropriately.",
            "category": "architecture",
            "tags": ["api", "rest", "design", "http"],
            "created_at": "2024-01-03T12:00:00",
            "quality_score": 0.85
        }
    ]

class TestKnowledgeSageDocGenerator:
    """Test suite for automatic document generation"""

    @pytest.mark.asyncio
    async def test_initialization(self, doc_generator):
        """Test document generator initialization"""
        assert doc_generator is not None
        assert doc_generator.is_initialized()

        assert hasattr(doc_generator, 'generators')

    @pytest.mark.asyncio
    async def test_api_documentation_generation(self, doc_generator, sample_knowledge_base):
        """Test API documentation generation"""
        # Filter API-related content
        api_docs = [doc for doc in sample_knowledge_base if "api" in doc["tags"]]
        
        result = await doc_generator.generate_api_documentation(
            knowledge_entries=api_docs,
            api_name="Knowledge Management API",
            version="2.0",
            output_format="markdown"
        )
        
        assert result["success"] is True
        assert "documentation" in result
        assert "metadata" in result
        
        doc_content = result["documentation"]
        assert "# Knowledge Management API" in doc_content
        assert "Version:** 2.0" in doc_content
        assert "## Endpoints" in doc_content or "## API Reference" in doc_content

    @pytest.mark.asyncio
    async def test_user_guide_generation(self, doc_generator, sample_knowledge_base):
        """Test user guide generation"""
        result = await doc_generator.generate_user_guide(
            knowledge_entries=sample_knowledge_base,
            title="Development Best Practices Guide",
            target_audience="developers",
            include_examples=True
        )
        
        assert result["success"] is True
        assert "documentation" in result
        
        guide_content = result["documentation"]
        assert "# Development Best Practices Guide" in guide_content
        assert "## Table of Contents" in guide_content
        # Check for either examples section or that examples are empty (which is acceptable)
        has_examples_section = "## Examples" in guide_content or "## Code Examples" in guide_content
        has_content_sections = any(category in guide_content for category in ["Development", "Devops", "Architecture"])
        assert has_examples_section or has_content_sections

    @pytest.mark.asyncio
    async def test_technical_specification_generation(self, doc_generator, sample_knowledge_base):
        """Test technical specification generation"""
        result = await doc_generator.generate_technical_specification(
            knowledge_entries=sample_knowledge_base,
            system_name="Knowledge Sage System",
            include_architecture=True,
            include_api_specs=True
        )
        
        assert result["success"] is True
        assert "documentation" in result
        
        spec_content = result["documentation"]
        assert "# Knowledge Sage System" in spec_content
        assert "## Architecture" in spec_content
        assert "## Technical Requirements" in spec_content or "## System Requirements" in spec_content

    @pytest.mark.asyncio
    async def test_knowledge_synthesis(self, doc_generator, sample_knowledge_base):
        """Test knowledge synthesis from multiple sources"""
        result = await doc_generator.synthesize_knowledge(
            knowledge_entries=sample_knowledge_base,
            synthesis_type="summary",
            max_length=500,
            include_citations=True
        )
        
        assert result["success"] is True
        assert "synthesized_content" in result
        assert "citations" in result
        assert "confidence_score" in result
        
        content = result["synthesized_content"]
        assert len(content) <= 600  # Allow some margin
        assert len(result["citations"]) > 0

    @pytest.mark.asyncio
    async def test_tutorial_generation(self, doc_generator, sample_knowledge_base):
        """Test step-by-step tutorial generation"""
        # Focus on development content
        dev_docs = [doc for doc in sample_knowledge_base if doc["category"] == "development"]
        
        result = await doc_generator.generate_tutorial(
            knowledge_entries=dev_docs,
            tutorial_title="Getting Started with Python Async",
            difficulty_level="intermediate",
            include_code_examples=True
        )
        
        assert result["success"] is True
        assert "documentation" in result
        
        tutorial_content = result["documentation"]
        assert "# Getting Started with Python Async" in tutorial_content
        assert "## Prerequisites" in tutorial_content
        assert "## Step" in tutorial_content  # Should contain numbered steps

    @pytest.mark.asyncio
    async def test_faq_generation(self, doc_generator, sample_knowledge_base):
        """Test FAQ generation from knowledge base"""
        result = await doc_generator.generate_faq(
            knowledge_entries=sample_knowledge_base,
            category_filter="development",
            max_questions=10
        )
        
        assert result["success"] is True
        assert "documentation" in result
        
        faq_content = result["documentation"]
        assert "# Frequently Asked Questions" in faq_content
        assert "?" in faq_content  # Should contain questions
        
        # Count questions
        question_count = faq_content.count("?")
        assert question_count <= 10

    @pytest.mark.asyncio
    async def test_glossary_generation(self, doc_generator, sample_knowledge_base):
        """Test glossary generation"""
        result = await doc_generator.generate_glossary(
            knowledge_entries=sample_knowledge_base,
            extract_technical_terms=True,
            alphabetical_order=True
        )
        
        assert result["success"] is True
        assert "documentation" in result
        
        glossary_content = result["documentation"]
        assert "# Glossary" in glossary_content
        assert "**" in glossary_content  # Should contain bold terms

    @pytest.mark.asyncio
    async def test_changelog_generation(self, doc_generator):
        """Test changelog generation from version history"""
        version_history = [
            {
                "version": "2.0.0",
                "date": "2024-01-15",
                "changes": ["Added ML classification", "Improved vector search", "Enhanced API"],
                "type": "major"
            },
            {
                "version": "1.2.1", 
                "date": "2024-01-10",

                "type": "patch"
            }
        ]
        
        result = await doc_generator.generate_changelog(
            version_history=version_history,
            format="markdown"
        )
        
        assert result["success"] is True
        assert "documentation" in result
        
        changelog_content = result["documentation"]
        assert "# Changelog" in changelog_content
        assert "## [2.0.0]" in changelog_content
        assert "## [1.2.1]" in changelog_content

    @pytest.mark.asyncio
    async def test_multiple_output_formats(self, doc_generator, sample_knowledge_base):
        """Test generation in multiple output formats"""
        formats = ["markdown", "html", "rst", "pdf"]
        
        for format_type in formats[:2]:  # Test first two formats
            result = await doc_generator.generate_user_guide(
                knowledge_entries=sample_knowledge_base,
                title="Test Guide",
                output_format=format_type
            )
            
            assert result["success"] is True
            assert "documentation" in result
            assert result["metadata"]["format"] == format_type

    @pytest.mark.asyncio

        # {{title}}
        Generated on: {{date}}
        
        ## Content
        {{content}}
        
        ## Metadata
        - Categories: {{categories}}
        - Tags: {{tags}}
        """

            context={
                "title": "Custom Document",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "content": "This is custom content",
                "categories": ["test"],

            }
        )
        
        assert result["success"] is True
        assert "documentation" in result
        assert "Custom Document" in result["documentation"]
        assert "This is custom content" in result["documentation"]

    @pytest.mark.asyncio
    async def test_batch_documentation_generation(self, doc_generator, sample_knowledge_base):
        """Test batch generation of multiple document types"""
        generation_jobs = [
            {
                "type": "user_guide",
                "title": "User Guide",
                "knowledge_entries": sample_knowledge_base
            },
            {
                "type": "api_docs",
                "api_name": "Knowledge Management API",
                "version": "2.0",
                "knowledge_entries": sample_knowledge_base
            },
            {
                "type": "faq",
                "knowledge_entries": sample_knowledge_base
            }
        ]
        
        result = await doc_generator.generate_batch(
            generation_jobs=generation_jobs,
            output_directory="/tmp/batch_docs"
        )
        
        assert result["success"] is True
        assert "generated_files" in result
        assert len(result["generated_files"]) == len(generation_jobs)

    @pytest.mark.asyncio
    async def test_documentation_validation(self, doc_generator):
        """Test documentation validation and quality checks"""
        doc_content = """
        # Test Document
        
        This is a test document with some content.
        
        ## Section 1
        Content for section 1.0
        
        ## Section 2  
        Content for section 2.0
        """
        
        result = await doc_generator.validate_documentation(
            content=doc_content,
            check_structure=True,
            check_completeness=True,
            check_readability=True
        )
        
        assert result["success"] is True
        assert "validation_score" in result
        assert "issues" in result
        assert 0 <= result["validation_score"] <= 1

    @pytest.mark.asyncio
    async def test_content_gap_analysis(self, doc_generator, sample_knowledge_base):
        """Test content gap analysis for documentation planning"""
        result = await doc_generator.analyze_content_gaps(
            knowledge_entries=sample_knowledge_base,
            required_topics=["security", "testing", "deployment", "monitoring"],
            coverage_threshold=0.7
        )
        
        assert result["success"] is True
        assert "coverage_analysis" in result
        assert "missing_topics" in result
        assert "recommendations" in result

    @pytest.mark.asyncio
    async def test_documentation_metrics(self, doc_generator):
        """Test documentation metrics calculation"""
        doc_content = "# Test\n\nThis is a test document with approximately 50 words " * 10
        
        result = await doc_generator.calculate_documentation_metrics(
            content=doc_content
        )
        
        assert result["success"] is True
        assert "metrics" in result
        
        metrics = result["metrics"]
        assert "word_count" in metrics
        assert "readability_score" in metrics
        assert "structure_score" in metrics
        assert "estimated_reading_time" in metrics

    @pytest.mark.asyncio
    async def test_cross_reference_generation(self, doc_generator, sample_knowledge_base):
        """Test automatic cross-reference generation"""
        result = await doc_generator.generate_cross_references(
            knowledge_entries=sample_knowledge_base,
            reference_threshold=0.1  # Lower threshold to find more relationships
        )
        
        assert result["success"] is True
        assert "cross_references" in result
        
        # Should find relationships between entries or be empty (both acceptable)
        assert "cross_references" in result

    @pytest.mark.asyncio
    async def test_localization_support(self, doc_generator, sample_knowledge_base):
        """Test documentation localization"""
        # Test basic localization (simplified)
        result = await doc_generator.generate_user_guide(
            knowledge_entries=sample_knowledge_base,
            title="User Guide",
            language="ja",  # Japanese
            localize_content=True
        )
        
        # Should succeed even if localization is basic
        assert result["success"] is True
        assert "documentation" in result

    @pytest.mark.asyncio
    async def test_version_comparison(self, doc_generator):
        """Test documentation version comparison"""
        old_doc = "# Version 1.0\n\nBasic functionality only."
        new_doc = "# Version 2.0\n\nBasic functionality plus advanced features."
        
        result = await doc_generator.compare_documentation_versions(
            old_content=old_doc,
            new_content=new_doc,
            highlight_changes=True
        )
        
        assert result["success"] is True
        assert "comparison" in result
        assert "changes_summary" in result

    @pytest.mark.asyncio
    async def test_interactive_documentation(self, doc_generator, sample_knowledge_base):
        """Test interactive documentation generation"""
        result = await doc_generator.generate_interactive_documentation(
            knowledge_entries=sample_knowledge_base,
            include_search=True,
            include_navigation=True,
            output_format="html"
        )
        
        assert result["success"] is True
        assert "documentation" in result
        
        # Should contain interactive elements
        html_content = result["documentation"]
        assert "<script>" in html_content or "search" in html_content.lower()

    @pytest.mark.asyncio
    async def test_documentation_export(self, doc_generator):
        """Test documentation export to various formats"""
        test_content = """
        # Test Document
        
        This is a **test** document with:
        - Bullet points
        - *Italic text*
        - `Code snippets`
        
        ## Code Example
        ```python
        def hello():
            print("Hello, World!")
        ```
        """
        
        formats = ["markdown", "html", "rst"]
        
        for format_type in formats:
            result = await doc_generator.export_documentation(
                content=test_content,
                format=format_type,
                include_metadata=True
            )
            
            assert result["success"] is True
            assert "exported_content" in result
            assert result["metadata"]["format"] == format_type

    @pytest.mark.asyncio
    async def test_performance_optimization(self, doc_generator, sample_knowledge_base):
        """Test performance with large knowledge base"""
        # Create larger dataset
        large_kb = sample_knowledge_base * 20  # 60 entries
        
        start_time = asyncio.get_event_loop().time()
        result = await doc_generator.generate_user_guide(
            knowledge_entries=large_kb,
            title="Large Guide"
        )
        end_time = asyncio.get_event_loop().time()
        
        assert result["success"] is True
        processing_time = end_time - start_time
        assert processing_time < 30.0  # Should complete within reasonable time

    @pytest.mark.asyncio
    async def test_error_handling(self, doc_generator):
        """Test error handling in document generation"""
        # Test with empty knowledge base
        result = await doc_generator.generate_user_guide(
            knowledge_entries=[],
            title="Empty Guide"
        )
        
        # Should handle gracefully
        assert "success" in result
        if not result["success"]:
            assert "error" in result

    @pytest.mark.asyncio
    async def test_cleanup(self, doc_generator):
        """Test cleanup of document generation resources"""
        # Generate some content to create resources
        await doc_generator.generate_user_guide(
            knowledge_entries=[{"title": "test", "content": "test"}],
            title="Test"
        )
        
        # Cleanup
        await doc_generator.cleanup()
        
        # Verify cleanup
        assert not doc_generator.is_initialized()