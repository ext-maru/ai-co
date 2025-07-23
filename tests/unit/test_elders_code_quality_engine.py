#!/usr/bin/env python3
"""
🧪 Test Suite for Elders Guild Code Quality Engine
完全なTDDテスト - エルダーズギルド品質保証
"""

import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import Dict, List

# Import the system under test
import sys
sys.path.append('/home/aicompany/ai_co')
from libs.elders_code_quality_engine import (
    EldersCodeQualityEngine,
    CodeQualityAnalyzer,
    DatabaseManager,
    EmbeddingGenerator,
    SmartCodingAssistant,
    CodeAnalysisResult,
    QualityPattern,
    BugLearningCase,
    quick_analyze
)

class TestCodeQualityAnalyzer:
    """Test the core code quality analyzer"""
    
    @pytest.fixture
    def analyzer(self):
        return CodeQualityAnalyzer()
    
    @pytest.mark.asyncio
    async def test_analyze_simple_code(self, analyzer):
        """Test basic code analysis"""
        code = '''
def add_numbers(a, b):
    """Add two numbers together."""
    return a + b
'''
        result = await analyzer.analyze_code(code, "test.py")
        
        assert isinstance(result, CodeAnalysisResult)
        assert result.file_path == "test.py"
        assert result.quality_score > 0
        assert result.complexity_score >= 1
        assert isinstance(result.issues, list)
        assert isinstance(result.suggestions, list)
        assert isinstance(result.timestamp, datetime)
        
    @pytest.mark.asyncio
    async def test_analyze_complex_code(self, analyzer):
        """Test analysis of complex code"""
        code = '''
def complex_function(data):
    total = 0
    for i in range(len(data)):
        if data[i] > 0:
            for j in range(data[i]):
                if j % 2 == 0:
                    total += j
                else:
                    total -= j
        elif data[i] < 0:
            total *= 2
        else:
            total += 1
    return total
'''
        result = await analyzer.analyze_code(code, "complex.py")
        
        assert result.complexity_score > 5
        assert result.quality_score < 100  # Should have some issues
        
    @pytest.mark.asyncio
    async def test_analyze_code_with_anti_patterns(self, analyzer):
        """Test detection of anti-patterns"""
        code = '''
def bad_function():
    magic_number = 42  # Magic number
    # TODO: fix this later
    try:
        result = eval("1 + 1")  # Dangerous
    except:
        pass  # Silent exception
    return magic_number
'''
        result = await analyzer.analyze_code(code, "bad.py")
        
        assert len(result.issues) > 0
        assert len(result.bug_risks) > 0
        assert result.iron_will_compliance == False  # TODO comment
        
    @pytest.mark.asyncio
    async def test_analyze_good_code(self, analyzer):
        """Test analysis of high-quality code"""
        code = '''
def calculate_area(length: float, width: float) -> float:
    """
    Calculate the area of a rectangle.
    
    Args:
        length: The length of the rectangle
        width: The width of the rectangle
        
    Returns:
        The area of the rectangle
    """
    try:
        if length <= 0 or width <= 0:
            raise ValueError("Length and width must be positive")
        return length * width
    except TypeError as e:
        raise ValueError(f"Invalid input types: {e}")

def test_calculate_area():
    assert calculate_area(5.0, 3.0) == 15.0
'''
        result = await analyzer.analyze_code(code, "good.py")
        
        assert result.quality_score > 80
        assert result.iron_will_compliance == True
        assert result.tdd_compatibility == True
        
    @pytest.mark.asyncio
    async def test_analyze_syntax_error(self, analyzer):
        """Test handling of syntax errors"""
        code = '''
def broken_function(
    # Missing closing parenthesis
    return "broken"
'''
        result = await analyzer.analyze_code(code, "broken.py")
        
        assert result.quality_score == 0.0
        assert len(result.issues) > 0
        assert result.issues[0]['type'] == 'syntax_error'
        assert result.iron_will_compliance == False
        assert result.tdd_compatibility == False

class TestDatabaseManager:
    """Test database operations"""
    
    @pytest.fixture
    def mock_connection(self):
        """Mock database connection"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        return mock_conn, mock_cursor
    
    @pytest.fixture
    def db_manager(self):
        return DatabaseManager({
            'host': 'localhost',
        """db_managerメソッド"""
            'database': 'test_db',
            'user': 'test_user',
            'password': 'test_pass'
        })
    
    @pytest.mark.asyncio
    async def test_store_quality_pattern(self, db_manager, mock_connection):
        """Test storing quality pattern"""
        mock_conn, mock_cursor = mock_connection
        db_manager.connection = mock_conn
        mock_cursor.fetchone.return_value = ('test-uuid-123',)
        
        pattern = QualityPattern(
            pattern_type='best_practice',
            pattern_name='Type Hints',
            problematic_code='def func(x):',
            improved_code='def func(x: int) -> int:',
            description='Add type hints',
            improvement_score=85.0,
            language='python',
            tags=['typing', 'clarity']
        )
        
        embedding = [0.1] * 1536
        uuid = await db_manager.store_quality_pattern(pattern, embedding)
        
        assert uuid == 'test-uuid-123'
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_store_bug_case(self, db_manager, mock_connection):
        """Test storing bug learning case"""
        mock_conn, mock_cursor = mock_connection
        db_manager.connection = mock_conn
        mock_cursor.fetchone.return_value = ('bug-uuid-456',)
        
        bug_case = BugLearningCase(
            bug_category='logic_error',
            bug_title='Off by one error',
            original_code='for i in range(len(items) + 1):',
            bug_description='Loop iterates one time too many',
            error_message='IndexError: list index out of range',
            fix_solution='Remove +1 from range',
            fix_code='for i in range(len(items)):',
            severity_level=6,
            language='python',
            prevention_tips=['Use enumerate', 'Check array bounds']
        )
        
        embedding = [0.2] * 1536
        uuid = await db_manager.store_bug_case(bug_case, embedding)
        
        assert uuid == 'bug-uuid-456'
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_search_similar_patterns(self, db_manager, mock_connection):
        """Test searching similar patterns"""
        mock_conn, mock_cursor = mock_connection
        db_manager.connection = mock_conn
        mock_cursor.fetchall.return_value = [
            ('uuid1', 'Pattern 1', 'best_practice', 'improved_code', 'desc', 90.0, 0.95),
            ('uuid2', 'Pattern 2', 'optimization', 'better_code', 'desc2', 85.0, 0.88)
        ]
        
        embedding = [0.3] * 1536
        results = await db_manager.search_similar_patterns(embedding, 0.8, 5)
        
        assert len(results) == 2
        assert results[0]['uuid'] == 'uuid1'
        assert results[0]['similarity'] == 0.95
        assert results[1]['pattern_type'] == 'optimization'
        mock_cursor.execute.assert_called_once()

class TestEmbeddingGenerator:
    """Test embedding generation"""
    
    @pytest.fixture
    def mock_openai_client(self):
        mock_client = Mock()
        """mock_openai_clientメソッド"""
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1] * 1536
        mock_client.embeddings.create.return_value = mock_response
        return mock_client
    
    @pytest.mark.asyncio
    async def test_generate_embedding(self, mock_openai_client):
        """Test embedding generation"""
        with patch('libs.elders_code_quality_engine.OpenAI') as mock_openai:
            mock_openai.return_value = mock_openai_client
            
            generator = EmbeddingGenerator("test-api-key")
            embedding = await generator.generate_embedding("test code")
            
            assert len(embedding) == 1536
            assert embedding[0] == 0.1
            mock_openai_client.embeddings.create.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_generate_embedding_error_handling(self):
        """Test embedding generation error handling"""
        with patch('libs.elders_code_quality_engine.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create.side_effect = Exception("API Error")
            mock_openai.return_value = mock_client
            
            generator = EmbeddingGenerator("test-api-key")
            embedding = await generator.generate_embedding("test code")
            
            # Should return zero vector on error
            assert len(embedding) == 1536
            assert all(x == 0.0 for x in embedding)

class TestSmartCodingAssistant:
    """Test the smart coding assistant"""
    
    @pytest.fixture
    def mock_components(self):
        mock_db = Mock(spec=DatabaseManager)
        mock_embedder = Mock(spec=EmbeddingGenerator)
        return mock_db, mock_embedder
    
    @pytest.fixture
    def assistant(self, mock_components):
        mock_db, mock_embedder = mock_components
        return SmartCodingAssistant(mock_db, mock_embedder)
    
    @pytest.mark.asyncio
    async def test_analyze_and_suggest(self, assistant, mock_components):
        """Test comprehensive analysis and suggestions"""
        mock_db, mock_embedder = mock_components
        
        # Mock embedding generation
        mock_embedder.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
        
        # Mock database searches
        mock_db.search_similar_patterns = AsyncMock(return_value=[
            {
                'uuid': 'pattern1',
                'pattern_name': 'Type Hints',
                'pattern_type': 'best_practice',
                'improved_code': 'def func(x: int) -> int:',
                'description': 'Add type hints',
                'improvement_score': 85.0,
                'similarity': 0.92
            }
        ])
        
        mock_db.search_similar_bugs = AsyncMock(return_value=[
            {
                'uuid': 'bug1',
                'bug_title': 'Null pointer',
                'bug_category': 'runtime_error',
                'fix_solution': 'Add null checks',
                'prevention_tips': ['Validate inputs'],
                'severity_level': 8,
                'similarity': 0.87
            }
        ])
        
        code = '''
def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result
'''
        
        result = await assistant.analyze_and_suggest(code, "test.py")
        
        assert 'analysis' in result
        assert 'similar_patterns' in result
        assert 'similar_bugs' in result
        assert 'ai_suggestions' in result
        assert 'overall_recommendation' in result
        
        # Verify the analysis structure
        analysis = result['analysis']
        assert 'quality_score' in analysis
        assert 'complexity_score' in analysis
        assert 'iron_will_compliance' in analysis
        assert 'tdd_compatibility' in analysis
        
    @pytest.mark.asyncio
    async def test_learn_from_bug(self, assistant, mock_components):
        """Test learning from bug cases"""
        mock_db, mock_embedder = mock_components
        
        mock_embedder.generate_embedding = AsyncMock(return_value=[0.2] * 1536)
        mock_db.store_bug_case = AsyncMock(return_value='learned-bug-uuid')
        
        bug_case = BugLearningCase(
            bug_category='logic_error',
            bug_title='Test bug',
            original_code='buggy code',
            bug_description='description',
            error_message='error',
            fix_solution='fix',
            fix_code='fixed code',
            severity_level=5,
            language='python',
            prevention_tips=['tip1', 'tip2']
        )
        
        uuid = await assistant.learn_from_bug(bug_case)
        
        assert uuid == 'learned-bug-uuid'
        mock_embedder.generate_embedding.assert_called_once()
        mock_db.store_bug_case.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_learn_from_pattern(self, assistant, mock_components):
        """Test learning from quality patterns"""
        mock_db, mock_embedder = mock_components
        
        mock_embedder.generate_embedding = AsyncMock(return_value=[0.3] * 1536)
        mock_db.store_quality_pattern = AsyncMock(return_value='learned-pattern-uuid')
        
        pattern = QualityPattern(
            pattern_type='best_practice',
            pattern_name='Test pattern',
            problematic_code='bad code',
            improved_code='good code',
            description='improvement',
            improvement_score=90.0,
            language='python',
            tags=['test']
        )
        
        uuid = await assistant.learn_from_pattern(pattern)
        
        assert uuid == 'learned-pattern-uuid'
        mock_embedder.generate_embedding.assert_called_once()
        mock_db.store_quality_pattern.assert_called_once()

class TestEldersCodeQualityEngine:
    """Test the main engine class"""
    
    @pytest.fixture
    def engine_config(self):
        """engine_configメソッド"""
        return {
            'host': 'localhost',
            'database': 'test_db',
            'user': 'test_user',
            'password': 'test_pass'
        }
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, engine_config):
        """Test engine initialization"""
        with patch('libs.elders_code_quality_engine.DatabaseManager') as mock_db_class:
            mock_db = Mock()
            mock_db.connect = AsyncMock()
            mock_db_class.return_value = mock_db
            
            engine = EldersCodeQualityEngine(engine_config, "test-api-key")
            await engine.initialize()
            
            assert engine.assistant is not None
            mock_db.connect.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_analyze_file(self, engine_config):
        """Test file analysis"""
        with patch('libs.elders_code_quality_engine.DatabaseManager'), \
             patch('libs.elders_code_quality_engine.SmartCodingAssistant') as mock_assistant_class:
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write('def hello(): return "world"')
                temp_file = f.name
            
            try:
                mock_assistant = Mock()
                mock_assistant.analyze_and_suggest = AsyncMock(return_value={
                    'analysis': {'quality_score': 85.0},
                    'suggestions': []
                })
                mock_assistant_class.return_value = mock_assistant
                
                engine = EldersCodeQualityEngine(engine_config)
                engine.assistant = mock_assistant
                
                result = await engine.analyze_file(temp_file)
                
                assert 'analysis' in result
                assert result['analysis']['quality_score'] == 85.0
                mock_assistant.analyze_and_suggest.assert_called_once()
                
            finally:
                os.unlink(temp_file)
                
    @pytest.mark.asyncio
    async def test_analyze_code_snippet(self, engine_config):
        """Test code snippet analysis"""
        with patch('libs.elders_code_quality_engine.DatabaseManager'), \
             patch('libs.elders_code_quality_engine.SmartCodingAssistant') as mock_assistant_class:
            
            mock_assistant = Mock()
            mock_assistant.analyze_and_suggest = AsyncMock(return_value={
                'analysis': {'quality_score': 75.0},
                'suggestions': ['Add type hints']
            })
            mock_assistant_class.return_value = mock_assistant
            
            engine = EldersCodeQualityEngine(engine_config)
            engine.assistant = mock_assistant
            
            code = "def test(): pass"
            result = await engine.analyze_code_snippet(code)
            
            assert 'analysis' in result
            assert result['analysis']['quality_score'] == 75.0
            mock_assistant.analyze_and_suggest.assert_called_once_with(code)

class TestQuickAnalyze:
    """Test the convenience quick analyze function"""
    
    @pytest.mark.asyncio
    async def test_quick_analyze(self):
        """Test quick analysis function"""
        with patch('libs.elders_code_quality_engine.EldersCodeQualityEngine') as mock_engine_class:
            mock_engine = Mock()
            mock_engine.initialize = AsyncMock()
            mock_engine.shutdown = AsyncMock()
            mock_engine.analyze_code_snippet = AsyncMock(return_value={
                'analysis': {'quality_score': 90.0},
                'suggestions': []
            })
            mock_engine_class.return_value = mock_engine
            
            db_params = {'host': 'localhost', 'database': 'test'}
            code = "def perfect_function(): return 'perfect'"
            
            result = await quick_analyze(code, db_params, "test-key")
            
            assert 'analysis' in result
            assert result['analysis']['quality_score'] == 90.0
            mock_engine.initialize.assert_called_once()
            mock_engine.shutdown.assert_called_once()

class TestIntegration:
    """Integration tests for the complete system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_analysis(self):
        """Test complete end-to-end analysis workflow"""
        # This would be a full integration test with real database
        # For now, we'll mock the components but test the full flow
        
        with patch('libs.elders_code_quality_engine.psycopg2.connect') as mock_connect, \
             patch('libs.elders_code_quality_engine.OpenAI') as mock_openai:
            
            # Mock database
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = ('test-uuid',)
            mock_cursor.fetchall.return_value = []
            mock_connect.return_value = mock_conn
            
            # Mock OpenAI
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = [Mock()]
            mock_response.data[0].embedding = [0.1] * 1536
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            # Test the full workflow
            db_params = {
                'host': 'localhost',
                'database': 'elders_guild_pgvector',
                'user': 'postgres',
                'password': ''
            }
            
            sample_code = '''
def calculate_discount(price, discount_percent):
    """Calculate discounted price."""
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount must be between 0 and 100")
    return price * (1 - discount_percent / 100)

def test_calculate_discount():
    assert calculate_discount(100, 20) == 80
'''
            
            result = await quick_analyze(sample_code, db_params, "test-key")
            
            # Verify we got a complete analysis
            assert 'analysis' in result
            assert 'similar_patterns' in result
            assert 'similar_bugs' in result
            assert 'ai_suggestions' in result
            assert 'overall_recommendation' in result

# Test runner
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])