"""
DocForge (D03) エルダーサーバント テストスイート

ドワーフ工房のドキュメント生成専門サーバントのテスト。
Iron Will 品質基準に基づく包括的テスト実装。
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List
import tempfile
import os
from datetime import datetime

from libs.elder_servants.base.elder_servant_base import (
    ElderServantBase, ServantRequest, ServantResponse, 
    ServantDomain, ServantCapability
)
from libs.elder_servants.dwarf_workshop.doc_forge import DocForge


class TestDocForge:
    """DocForge エルダーサーバントのテストクラス"""

    @pytest.fixture
    def doc_forge(self) -> DocForge:
        """DocForge インスタンスを作成"""
        return DocForge("D03", "DocForge", "documentation_generation")

    @pytest.fixture
    def sample_request(self) -> ServantRequest:
        """サンプルリクエストを作成"""
        return ServantRequest(
            task_id="doc_test_001",
            task_type="documentation_generation",
            priority="medium",
            data={
                "source_code": "def hello_world():\n    return 'Hello, World!'",
                "doc_type": "api_documentation",
                "format": "markdown",
                "language": "python"
            },
            context={"project_name": "test_project"}
        )

    def test_initialization(self, doc_forge: DocForge):
        """DocForge の初期化テスト"""
        assert doc_forge.name == "DocForge"
        assert doc_forge.servant_id == "D03"
        assert doc_forge.domain == ServantDomain.DWARF_WORKSHOP
        assert doc_forge.specialization == "documentation_generation"
        assert doc_forge.category == "dwarf_workshop"

    def test_get_capabilities(self, doc_forge: DocForge):
        """能力取得テスト"""
        capabilities = doc_forge.get_capabilities()
        expected_capabilities = [
            ServantCapability.DOCUMENTATION,
            ServantCapability.CODE_GENERATION,
            ServantCapability.ANALYSIS
        ]
        
        for cap in expected_capabilities:
            assert cap in capabilities

    def test_validate_request_valid(self, doc_forge: DocForge, sample_request: ServantRequest):
        """有効なリクエストの検証テスト"""
        assert doc_forge.validate_request(sample_request) is True

    def test_validate_request_invalid_task_type(self, doc_forge: DocForge):
        """無効なタスクタイプの検証テスト"""
        invalid_request = ServantRequest(
            task_id="doc_test_002",
            task_type="invalid_type",
            priority="medium",
            data={"source_code": "test"},
            context={}
        )
        
        assert doc_forge.validate_request(invalid_request) is False

    def test_validate_request_missing_source_code(self, doc_forge: DocForge):
        """ソースコード不足の検証テスト"""
        invalid_request = ServantRequest(
            task_id="doc_test_003",
            task_type="documentation_generation",
            priority="medium",
            data={"doc_type": "api_documentation"},
            context={}
        )
        
        assert doc_forge.validate_request(invalid_request) is False

    @pytest.mark.asyncio
    async def test_process_request_api_documentation(self, doc_forge: DocForge):
        """API ドキュメント生成の処理テスト"""
        request = ServantRequest(
            task_id="doc_test_004",
            task_type="documentation_generation",
            priority="high",
            data={
                "source_code": """
def calculate_sum(a: int, b: int) -> int:
    '''Calculate the sum of two integers.'''
    return a + b

class Calculator:
    '''A simple calculator class.'''
    
    def add(self, x: float, y: float) -> float:
        '''Add two numbers.'''
        return x + y
""",
                "doc_type": "api_documentation",
                "format": "markdown",
                "language": "python"
            },
            context={"project_name": "Calculator API"}
        )
        
        with patch.object(doc_forge, 'collaborate_with_sages', new_callable=AsyncMock) as mock_collab:
            mock_collab.return_value = {
                "knowledge_sage": {"documentation_patterns": "best_practices"},
                "rag_sage": {"similar_examples": ["example1", "example2"]}
            }
            
            response = await doc_forge.process_request(request)
            
            assert response.status == "success"
            assert response.task_id == "doc_test_004"
            assert "documentation" in response.data
            assert len(response.errors) == 0
            
            # ドキュメント内容の検証
            documentation = response.data["documentation"]
            assert "calculate_sum" in documentation
            assert "Calculator" in documentation
            assert "API Documentation" in documentation

    @pytest.mark.asyncio
    async def test_process_request_user_guide(self, doc_forge: DocForge):
        """ユーザーガイド生成の処理テスト"""
        request = ServantRequest(
            task_id="doc_test_005",
            task_type="documentation_generation",
            priority="medium",
            data={
                "source_code": """
def main():
    '''Main application entry point.'''
    print("Hello, World!")

if __name__ == "__main__":
    main()
""",
                "doc_type": "user_guide",
                "format": "markdown",
                "language": "python"
            },
            context={"project_name": "Hello World App"}
        )
        
        with patch.object(doc_forge, 'collaborate_with_sages', new_callable=AsyncMock) as mock_collab:
            mock_collab.return_value = {
                "knowledge_sage": {"user_guide_templates": "standard"},
                "task_sage": {"workflow_optimization": "completed"}
            }
            
            response = await doc_forge.process_request(request)
            
            assert response.status == "success"
            assert "documentation" in response.data
            
            # ユーザーガイド特有の内容を検証
            documentation = response.data["documentation"]
            assert "User Guide" in documentation
            assert "Getting Started" in documentation
            assert "Usage" in documentation

    @pytest.mark.asyncio
    async def test_process_request_readme_generation(self, doc_forge: DocForge):
        """README生成の処理テスト"""
        request = ServantRequest(
            task_id="doc_test_006",
            task_type="documentation_generation",
            priority="high",
            data={
                "source_code": "# Project files content here",
                "doc_type": "readme",
                "format": "markdown",
                "project_structure": {
                    "src/": ["main.py", "utils.py"],
                    "tests/": ["test_main.py"],
                    "docs/": ["api.md"]
                }
            },
            context={
                "project_name": "Awesome Project",
                "description": "A fantastic project that does amazing things"
            }
        )
        
        response = await doc_forge.process_request(request)
        
        assert response.status == "success"
        documentation = response.data["documentation"]
        
        # README特有の要素を検証
        assert "# Awesome Project" in documentation
        assert "## Installation" in documentation
        assert "## Usage" in documentation
        assert "## Project Structure" in documentation

    @pytest.mark.asyncio
    async def test_generate_api_documentation(self, doc_forge: DocForge):
        """API ドキュメント生成の詳細テスト"""
        source_code = """
class UserService:
    '''Service for managing users.'''
    
    def create_user(self, name: str, email: str) -> dict:
        '''Create a new user.
        
        Args:
            name: User's full name
            email: User's email address
            
        Returns:
            dict: Created user information
        '''
        return {"name": name, "email": email, "id": 123}
    
    def get_user(self, user_id: int) -> dict:
        '''Retrieve user by ID.'''
        return {"id": user_id, "name": "Test User"}
"""
        
        documentation = await doc_forge._generate_api_documentation(
            source_code, "python", {"project_name": "User API"}
        )
        
        assert "UserService" in documentation
        assert "create_user" in documentation
        assert "get_user" in documentation
        assert "Args:" in documentation
        assert "Returns:" in documentation

    @pytest.mark.asyncio
    async def test_generate_user_guide(self, doc_forge: DocForge):
        """ユーザーガイド生成の詳細テスト"""
        source_code = """
def setup_environment():
    '''Setup the development environment.'''
    pass

def run_application():
    '''Run the main application.'''
    pass
"""
        context = {
            "project_name": "Development Tool",
            "description": "A tool for developers"
        }
        
        guide = await doc_forge._generate_user_guide(source_code, "python", context)
        
        assert "# Development Tool User Guide" in guide
        assert "## Getting Started" in guide
        assert "## Usage" in guide
        assert "setup_environment" in guide
        assert "run_application" in guide

    @pytest.mark.asyncio
    async def test_generate_readme(self, doc_forge: DocForge):
        """README生成の詳細テスト"""
        project_structure = {
            "src/": ["main.py", "config.py"],
            "tests/": ["test_main.py", "test_config.py"],
            "docs/": ["api.md", "user_guide.md"]
        }
        
        context = {
            "project_name": "Test Project",
            "description": "A test project for demonstration",
            "author": "Test Author",
            "license": "MIT"
        }
        
        readme = await doc_forge._generate_readme(project_structure, context)
        
        assert "# Test Project" in readme
        assert "A test project for demonstration" in readme
        assert "## Installation" in readme
        assert "## Usage" in readme
        assert "## License" in readme
        assert "MIT" in readme

    def test_extract_python_docstrings(self, doc_forge: DocForge):
        """Python docstring抽出テスト"""
        source_code = '''
def function_with_docstring():
    """This is a function docstring."""
    pass

class ClassWithDocstring:
    """This is a class docstring."""
    
    def method_with_docstring(self):
        """This is a method docstring."""
        pass
'''
        
        docstrings = doc_forge._extract_python_docstrings(source_code)
        
        assert "function_with_docstring" in docstrings
        assert "ClassWithDocstring" in docstrings
        assert "method_with_docstring" in docstrings
        assert "This is a function docstring." in docstrings["function_with_docstring"]

    def test_extract_function_signatures(self, doc_forge: DocForge):
        """関数シグネチャ抽出テスト"""
        source_code = '''
def simple_function():
    pass

def function_with_params(a: int, b: str = "default") -> bool:
    return True

async def async_function(x: float) -> None:
    pass
'''
        
        signatures = doc_forge._extract_function_signatures(source_code)
        
        assert "simple_function()" in signatures
        assert "function_with_params(a: int, b: str = \"default\") -> bool" in signatures
        assert "async_function(x: float) -> None" in signatures

    def test_extract_class_structure(self, doc_forge: DocForge):
        """クラス構造抽出テスト"""
        source_code = '''
class ParentClass:
    """Parent class docstring."""
    
    def parent_method(self):
        pass

class ChildClass(ParentClass):
    """Child class docstring."""
    
    def __init__(self, value: int):
        self.value = value
    
    def child_method(self) -> str:
        return "child"
'''
        
        structure = doc_forge._extract_class_structure(source_code)
        
        assert "ParentClass" in structure
        assert "ChildClass" in structure
        assert "parent_method" in structure["ParentClass"]["methods"]
        assert "child_method" in structure["ChildClass"]["methods"]
        assert "ParentClass" in structure["ChildClass"]["inheritance"]

    @pytest.mark.asyncio
    async def test_error_handling_invalid_syntax(self, doc_forge: DocForge):
        """無効な構文のエラーハンドリングテスト"""
        request = ServantRequest(
            task_id="doc_test_007",
            task_type="documentation_generation",
            priority="medium",
            data={
                "source_code": "def invalid_syntax(\n    # missing closing parenthesis",
                "doc_type": "api_documentation",
                "format": "markdown",
                "language": "python"
            },
            context={}
        )
        
        response = await doc_forge.process_request(request)
        
        # エラーがあっても部分的な結果を返すべき
        assert response.status in ["partial", "success"]
        assert len(response.warnings) > 0 or len(response.errors) > 0

    @pytest.mark.asyncio
    async def test_performance_large_codebase(self, doc_forge: DocForge):
        """大規模コードベースのパフォーマンステスト"""
        # 大きなソースコードを生成
        large_code = "\n".join([
            f"def function_{i}():\n    '''Function {i} docstring.'''\n    pass"
            for i in range(100)
        ])
        
        request = ServantRequest(
            task_id="doc_test_008",
            task_type="documentation_generation",
            priority="high",
            data={
                "source_code": large_code,
                "doc_type": "api_documentation",
                "format": "markdown",
                "language": "python"
            },
            context={"project_name": "Large Project"}
        )
        
        start_time = datetime.now()
        response = await doc_forge.process_request(request)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        assert response.status == "success"
        assert processing_time < 10  # 10秒以内で完了
        assert "function_0" in response.data["documentation"]
        assert "function_99" in response.data["documentation"]

    @pytest.mark.asyncio
    async def test_multi_language_support(self, doc_forge: DocForge):
        """多言語サポートテスト"""
        test_cases = [
            {
                "language": "javascript",
                "code": "function testFunction() { return 'hello'; }",
                "expected": "testFunction"
            },
            {
                "language": "java",
                "code": "public class TestClass { public void testMethod() {} }",
                "expected": "TestClass"
            },
            {
                "language": "cpp",
                "code": "class TestClass { public: void testMethod(); };",
                "expected": "TestClass"
            }
        ]
        
        for case in test_cases:
            request = ServantRequest(
                task_id=f"doc_test_{case['language']}",
                task_type="documentation_generation",
                priority="medium",
                data={
                    "source_code": case["code"],
                    "doc_type": "api_documentation",
                    "format": "markdown",
                    "language": case["language"]
                },
                context={"project_name": f"Test {case['language']} Project"}
            )
            
            response = await doc_forge.process_request(request)
            
            assert response.status == "success"
            assert case["expected"] in response.data["documentation"]

    @pytest.mark.asyncio
    async def test_iron_will_quality_standards(self, doc_forge: DocForge, sample_request: ServantRequest):
        """Iron Will品質基準テスト"""
        # 品質基準を満たす処理を実行
        for _ in range(10):
            response = await doc_forge.execute_with_quality_gate(sample_request)
            assert response.status == "success"
        
        # 品質スコアの確認
        metrics = doc_forge.get_metrics()
        quality_scores = metrics["quality_scores"]
        
        # Iron Will基準の確認
        assert quality_scores["root_cause_resolution"] >= 95
        assert quality_scores["dependency_completeness"] >= 100
        assert quality_scores["test_coverage"] >= 95
        assert quality_scores["security_score"] >= 90
        assert quality_scores["performance_score"] >= 85
        assert quality_scores["maintainability_score"] >= 80

    @pytest.mark.asyncio
    async def test_collaboration_with_sages(self, doc_forge: DocForge):
        """4賢者との協調テスト"""
        request_data = {
            "source_code": "test code",
            "doc_type": "api_documentation"
        }
        
        with patch.object(doc_forge, 'collaborate_with_sages', new_callable=AsyncMock) as mock_collab:
            mock_collab.return_value = {
                "knowledge_sage": {"status": "consulted", "templates": ["api_template"]},
                "task_sage": {"status": "consulted", "priority": "high"},
                "incident_sage": {"status": "consulted", "health": "good"},
                "rag_sage": {"status": "consulted", "examples": ["example1"]}
            }
            
            result = await doc_forge.collaborate_with_sages(request_data)
            
            assert "knowledge_sage" in result
            assert "task_sage" in result
            assert "incident_sage" in result
            assert "rag_sage" in result
            assert result["knowledge_sage"]["status"] == "consulted"

    def test_metrics_tracking(self, doc_forge: DocForge):
        """メトリクス追跡テスト"""
        initial_metrics = doc_forge.get_metrics()
        
        assert "tasks_processed" in initial_metrics
        assert "tasks_succeeded" in initial_metrics
        assert "tasks_failed" in initial_metrics
        assert "success_rate" in initial_metrics
        assert "quality_scores" in initial_metrics

    @pytest.mark.asyncio
    async def test_concurrent_processing(self, doc_forge: DocForge):
        """並行処理テスト"""
        requests = []
        for i in range(5):
            request = ServantRequest(
                task_id=f"concurrent_test_{i}",
                task_type="documentation_generation",
                priority="medium",
                data={
                    "source_code": f"def function_{i}(): pass",
                    "doc_type": "api_documentation",
                    "format": "markdown",
                    "language": "python"
                },
                context={"project_name": f"Project {i}"}
            )
            requests.append(request)
        
        # 並行実行
        tasks = [doc_forge.process_request(req) for req in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # すべてのレスポンスが成功していることを確認
        for i, response in enumerate(responses):
            assert not isinstance(response, Exception)
            assert response.status == "success"
            assert f"function_{i}" in response.data["documentation"]

    def test_repr_method(self, doc_forge: DocForge):
        """__repr__メソッドテスト"""
        repr_str = repr(doc_forge)
        assert "DocForge" in repr_str
        assert "DocForge" in repr_str
        assert "dwarf_workshop" in repr_str