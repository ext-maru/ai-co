"""
TestForge (D02) - テスト生成専門サーバントのテスト
ドワーフ工房所属 - ユニット・統合・E2Eテスト生成のエキスパート
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import ast
from libs.elder_servants.dwarf_workshop.test_forge import TestForge


class TestTestForgeBasics:
    """TestForgeの基本機能テスト"""
    
    @pytest.fixture
    def test_forge(self):
        """TestForgeインスタンスを生成"""
        return TestForge()
    
    def test_initialization(self, test_forge):
        """初期化テスト"""
        assert test_forge.servant_id == "D02"
        assert test_forge.name == "TestForge"
        assert test_forge.category == "dwarf_workshop"
        assert test_forge.specialization == "test_generation"
    
    def test_get_capabilities(self, test_forge):
        """能力リスト取得テスト"""
        capabilities = test_forge.get_capabilities()
        assert "generate_unit_tests" in capabilities
        assert "generate_integration_tests" in capabilities
        assert "generate_e2e_tests" in capabilities
        assert "analyze_test_coverage" in capabilities
        assert "generate_test_fixtures" in capabilities
        assert "create_mock_objects" in capabilities
        assert len(capabilities) >= 6


class TestTestGeneration:
    """テスト生成機能のテスト"""
    
    @pytest.fixture
    def test_forge(self):
        return TestForge()
    
    @pytest.mark.asyncio
    async def test_generate_unit_tests_for_function(self, test_forge):
        """関数のユニットテスト生成"""
        source_code = '''
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b
'''
        
        result = await test_forge.execute_task({
            "action": "generate_unit_tests",
            "source_code": source_code,
            "function_name": "add"
        })
        
        assert result["status"] == "success"
        assert "test_code" in result
        assert "def test_add" in result["test_code"]
        assert "assert add(2, 3) == 5" in result["test_code"]
        assert result["test_count"] >= 3  # 正常系、境界値、エラー系
    
    @pytest.mark.asyncio
    async def test_generate_unit_tests_for_class(self, test_forge):
        """クラスのユニットテスト生成"""
        source_code = '''
class Calculator:
    def __init__(self, precision: int = 2):
        self.precision = precision
    
    def divide(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Division by zero")
        return round(a / b, self.precision)
'''
        
        result = await test_forge.execute_task({
            "action": "generate_unit_tests",
            "source_code": source_code,
            "class_name": "Calculator"
        })
        
        assert result["status"] == "success"
        assert "test_code" in result
        assert "class TestCalculator" in result["test_code"]
        assert "test_divide_normal" in result["test_code"]
        assert "test_divide_by_zero" in result["test_code"]
        assert "pytest.raises(ValueError)" in result["test_code"]
    
    @pytest.mark.asyncio
    async def test_generate_integration_tests(self, test_forge):
        """統合テスト生成"""
        components = {
            "database": "PostgreSQL",
            "api": "FastAPI",
            "cache": "Redis"
        }
        
        result = await test_forge.execute_task({
            "action": "generate_integration_tests",
            "components": components,
            "test_scenario": "User registration flow"
        })
        
        assert result["status"] == "success"
        assert "test_code" in result
        assert "@pytest.fixture" in result["test_code"]
        assert "async def test_user_registration_flow" in result["test_code"]
        assert len(result["fixtures"]) >= 3
    
    @pytest.mark.asyncio
    async def test_generate_e2e_tests(self, test_forge):
        """E2Eテスト生成"""
        user_flow = {
            "flow_name": "Purchase flow",
            "steps": [
                "Visit homepage",
                "Search product",
                "Add to cart",
                "Checkout",
                "Payment confirmation"
            ]
        }
        
        result = await test_forge.execute_task({
            "action": "generate_e2e_tests",
            "user_flow": user_flow,
            "framework": "playwright"
        })
        
        assert result["status"] == "success"
        assert "test_code" in result
        assert "async def test_purchase_flow" in result["test_code"]
        assert "page.goto" in result["test_code"]
        assert len(result["test_steps"]) == 5


class TestTestAnalysis:
    """テスト分析機能のテスト"""
    
    @pytest.fixture
    def test_forge(self):
        return TestForge()
    
    @pytest.mark.asyncio
    async def test_analyze_test_coverage(self, test_forge):
        """テストカバレッジ分析"""
        with patch('libs.elder_servants.dwarf_workshop.test_forge.TestForge._run_coverage_analysis') as mock_coverage:
            mock_coverage.return_value = {
                "total_coverage": 85.5,
                "files": {
                    "module1.py": 90.0,
                    "module2.py": 80.0,
                    "module3.py": 86.5
                },
                "uncovered_lines": {
                    "module1.py": [45, 67, 89],
                    "module2.py": [12, 34, 56, 78]
                }
            }
            
            result = await test_forge.execute_task({
                "action": "analyze_test_coverage",
                "project_path": "/path/to/project"
            })
            
            assert result["status"] == "success"
            assert result["total_coverage"] == 85.5
            assert len(result["recommendations"]) > 0
            assert result["quality_score"] >= 80  # Iron Will基準
    
    @pytest.mark.asyncio
    async def test_generate_test_fixtures(self, test_forge):
        """テストフィクスチャ生成"""
        models = {
            "User": {
                "fields": ["id", "name", "email", "created_at"],
                "required": ["name", "email"]
            },
            "Product": {
                "fields": ["id", "name", "price", "stock"],
                "required": ["name", "price"]
            }
        }
        
        result = await test_forge.execute_task({
            "action": "generate_test_fixtures",
            "models": models,
            "factory_library": "factory_boy"
        })
        
        assert result["status"] == "success"
        assert "fixtures_code" in result
        assert "class UserFactory" in result["fixtures_code"]
        assert "class ProductFactory" in result["fixtures_code"]
        assert len(result["factories"]) == 2
    
    @pytest.mark.asyncio
    async def test_create_mock_objects(self, test_forge):
        """モックオブジェクト生成"""
        dependencies = {
            "EmailService": ["send_email", "verify_email"],
            "PaymentGateway": ["process_payment", "refund"],
            "DatabaseConnection": ["query", "execute", "commit"]
        }
        
        result = await test_forge.execute_task({
            "action": "create_mock_objects",
            "dependencies": dependencies
        })
        
        assert result["status"] == "success"
        assert "mock_code" in result
        assert "mock_email_service" in result["mock_code"]
        assert "mock_payment_gateway" in result["mock_code"]
        assert len(result["mocks"]) == 3


class TestQualityAndCompliance:
    """品質とコンプライアンステスト"""
    
    @pytest.fixture
    def test_forge(self):
        return TestForge()
    
    @pytest.mark.asyncio
    async def test_iron_will_compliance(self, test_forge):
        """Iron Will品質基準準拠テスト"""
        # 生成されたテストコードの品質チェック
        generated_test = '''
import pytest

def test_example():
    assert 1 + 1 == 2

def test_another():
    pass  # TODO: implement
'''
        
        quality_result = await test_forge._check_test_quality(generated_test)
        
        assert quality_result["has_assertions"] == True
        assert quality_result["has_empty_tests"] == True
        assert quality_result["quality_score"] < 95  # 空のテストがあるため
    
    @pytest.mark.asyncio
    async def test_error_handling(self, test_forge):
        """エラーハンドリングテスト"""
        # 無効なソースコード
        result = await test_forge.execute_task({
            "action": "generate_unit_tests",
            "source_code": "invalid python code {{"
        })
        
        assert result["status"] == "error"
        assert "error" in result
        assert "recovery_suggestion" in result
    
    @pytest.mark.asyncio
    async def test_sage_collaboration(self, test_forge):
        """4賢者との協調テスト"""
        with patch.object(test_forge, 'collaborate_with_sages') as mock_collab:
            mock_collab.return_value = {
                "knowledge_sage": {"test_patterns": ["AAA", "Given-When-Then"]},
                "task_sage": {"priority": "high", "dependencies": []},
                "incident_sage": {"risks": [], "warnings": []},
                "rag_sage": {"similar_tests": ["test_example.py"]}
            }
            
            result = await test_forge.execute_task({
                "action": "generate_unit_tests",
                "source_code": "def foo(): pass",
                "consult_sages": True
            })
            
            mock_collab.assert_called_once()
            assert result["status"] == "success"


class TestAdvancedFeatures:
    """高度な機能のテスト"""
    
    @pytest.fixture
    def test_forge(self):
        return TestForge()
    
    @pytest.mark.asyncio
    async def test_parametrized_test_generation(self, test_forge):
        """パラメータ化テスト生成"""
        result = await test_forge.execute_task({
            "action": "generate_parametrized_tests",
            "function_name": "validate_email",
            "test_cases": [
                {"input": "test@example.com", "expected": True},
                {"input": "invalid.email", "expected": False},
                {"input": "", "expected": False},
                {"input": "user@", "expected": False}
            ]
        })
        
        assert result["status"] == "success"
        assert "@pytest.mark.parametrize" in result["test_code"]
        assert len(result["test_cases"]) == 4
    
    @pytest.mark.asyncio
    async def test_performance_test_generation(self, test_forge):
        """パフォーマンステスト生成"""
        result = await test_forge.execute_task({
            "action": "generate_performance_tests",
            "target_function": "process_large_dataset",
            "performance_criteria": {
                "max_duration": 1.0,  # seconds
                "memory_limit": 100,  # MB
                "concurrent_users": 100
            }
        })
        
        assert result["status"] == "success"
        assert "measure_performance" in result["test_code"]
        assert "memory_profiler" in result["dependencies"]
    
    @pytest.mark.asyncio
    async def test_mutation_test_support(self, test_forge):
        """ミューテーションテストサポート"""
        result = await test_forge.execute_task({
            "action": "generate_mutation_tests",
            "source_file": "calculator.py",
            "mutation_operators": ["arithmetic", "comparison", "logical"]
        })
        
        assert result["status"] == "success"
        assert "mutation_config" in result
        assert len(result["mutation_operators"]) == 3


class TestHealthAndMetrics:
    """ヘルスチェックとメトリクステスト"""
    
    @pytest.fixture
    def test_forge(self):
        return TestForge()
    
    @pytest.mark.asyncio
    async def test_health_check(self, test_forge):
        """ヘルスチェック"""
        health = await test_forge.health_check()
        
        assert health["status"] == "healthy"
        assert health["servant_id"] == "D02"
        assert "capabilities" in health
        assert health["iron_will_compliance"] == True
        assert health["performance_metrics"]["avg_generation_time"] < 5.0
    
    def test_get_metrics(self, test_forge):
        """メトリクス取得"""
        metrics = test_forge.get_metrics()
        
        assert "total_tests_generated" in metrics
        assert "test_types_distribution" in metrics
        assert "average_quality_score" in metrics
        assert metrics["average_quality_score"] >= 95  # Iron Will基準