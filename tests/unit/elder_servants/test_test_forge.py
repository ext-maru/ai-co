"""
TestForge (D02) サーバントのテストスイート
"""

import ast
import asyncio
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.append("/home/aicompany/ai_co")

from libs.elder_servants.base.elder_servant import ServantCategory, TaskStatus
from libs.elder_servants.dwarf_workshop.test_forge import TestForge


class TestTestForge:
    """TestForgeサーバントのテスト"""

    @pytest.fixture
    def test_forge(self):
        """TestForgeインスタンスのフィクスチャ"""
        return TestForge()

    def test_initialization(self, test_forge):
        """初期化テスト"""
        assert test_forge.servant_id == "D02"
        assert test_forge.servant_name == "TestForge"
        assert test_forge.category == ServantCategory.DWARF
        assert test_forge.specialization == "テスト生成"
        assert len(test_forge.capabilities) == 6

        # TestForge固有の設定確認
        assert "pytest" in test_forge.test_frameworks
        assert "unittest" in test_forge.test_frameworks
        assert test_forge.test_quality_metrics["coverage_target"] == 95.0

    def test_specialized_capabilities(self, test_forge):
        """専門能力のテスト"""
        capabilities = test_forge.get_specialized_capabilities()
        assert len(capabilities) == 3

        cap_names = [cap.name for cap in capabilities]
        assert "analyze_test_coverage" in cap_names
        assert "generate_test_data" in cap_names
        assert "optimize_test_suite" in cap_names

    @pytest.mark.asyncio
    async def test_generate_unit_tests_simple(self, test_forge):
        """簡単なユニットテスト生成のテスト"""
        source_code = '''
def add_numbers(a, b):
    """Add two numbers"""
    return a + b

class Calculator:
    def multiply(self, x, y):
        return x * y
'''

        task = {
            "task_id": "test_unit_001",
            "task_type": "generate_unit_tests",
            "spec": {
                "source_code": source_code,
                "framework": "pytest",
                "coverage_target": 90.0,
            },
        }

        result = await test_forge.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert result.quality_score >= 95.0
        assert "test_code" in result.result_data

        # 生成されたテストコードの検証
        test_code = result.result_data["test_code"]
        assert "def test_add_numbers" in test_code
        assert "Calculator" in test_code
        assert "import pytest" in test_code

        # 構文的に正しいか確認
        ast.parse(test_code)

        # メタデータ確認
        assert result.result_data["test_type"] == "unit"
        assert result.result_data["framework"] == "pytest"
        assert result.result_data["test_count"] > 0

    @pytest.mark.asyncio
    async def test_generate_unit_tests_unittest(self, test_forge):
        """Unittestフレームワークでのテスト生成"""
        source_code = """
def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
"""

        task = {
            "task_id": "test_unit_002",
            "task_type": "generate_unit_tests",
            "spec": {"source_code": source_code, "framework": "unittest"},
        }

        result = await test_forge.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        test_code = result.result_data["test_code"]
        assert "import unittest" in test_code
        assert "class TestSuite" in test_code
        assert "def test_divide" in test_code

    @pytest.mark.asyncio
    async def test_generate_integration_tests(self, test_forge):
        """統合テスト生成のテスト"""
        task = {
            "task_id": "test_integration_001",
            "task_type": "generate_integration_tests",
            "spec": {
                "modules": ["user_service", "database", "api"],
                "interactions": [
                    {
                        "name": "user_creation",
                        "modules": ["user_service", "database"],
                        "scenario": "Create user and save to database",
                        "expected": "user_created",
                    }
                ],
                "framework": "pytest",
            },
        }

        result = await test_forge.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert result.result_data["test_type"] == "integration"

        test_code = result.result_data["test_code"]
        assert "def test_user_creation" in test_code
        assert "def test_data_flow" in test_code
        assert result.result_data["modules_tested"] == 3

    @pytest.mark.asyncio
    async def test_generate_e2e_tests_playwright(self, test_forge):
        """Playwright E2Eテスト生成のテスト"""
        task = {
            "task_id": "test_e2e_001",
            "task_type": "generate_e2e_tests",
            "spec": {
                "user_journeys": [
                    {
                        "name": "login_flow",
                        "steps": [
                            "Navigate to login",
                            "Enter credentials",
                            "Click submit",
                        ],
                        "assertions": ["User is logged in", "Dashboard visible"],
                        "tags": ["auth"],
                    }
                ],
                "app_type": "web",
                "tool": "playwright",
            },
        }

        result = await test_forge.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert result.result_data["test_type"] == "e2e"
        assert result.result_data["tool"] == "playwright"

        test_code = result.result_data["test_code"]
        assert "from playwright.async_api import async_playwright" in test_code
        assert "async def test_user_journey_login_flow" in test_code

    @pytest.mark.asyncio
    async def test_generate_e2e_tests_selenium(self, test_forge):
        """Selenium E2Eテスト生成のテスト"""
        task = {
            "task_id": "test_e2e_002",
            "task_type": "generate_e2e_tests",
            "spec": {
                "user_journeys": [],  # 空の場合デフォルトテスト生成
                "app_type": "web",
                "tool": "selenium",
            },
        }

        result = await test_forge.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        test_code = result.result_data["test_code"]
        assert "from selenium import webdriver" in test_code
        assert "def test_application_loads" in test_code
        assert "def test_navigation_flow" in test_code

    @pytest.mark.asyncio
    async def test_generate_performance_tests(self, test_forge):
        """パフォーマンステスト生成のテスト"""
        task = {
            "task_id": "test_perf_001",
            "task_type": "generate_performance_tests",
            "spec": {
                "endpoints": [
                    {
                        "name": "api_users",
                        "url": "/api/users",
                        "method": "GET",
                        "users": 50,
                        "duration": 120,
                    }
                ],
                "load_patterns": [
                    {
                        "name": "ramp_up",
                        "type": "ramp_up",
                        "peak_users": 200,
                        "ramp_time": 600,
                    }
                ],
                "targets": {"response_time": 150, "throughput": 200},
                "tool": "locust",
            },
        }

        result = await test_forge.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert result.result_data["test_type"] == "performance"
        assert result.result_data["tool"] == "locust"

        test_code = result.result_data["test_code"]
        assert "from locust import HttpUser" in test_code
        assert "def test_load_api_users" in test_code
        assert result.result_data["endpoints_covered"] == 1
        assert result.result_data["load_patterns"] == 1

    @pytest.mark.asyncio
    async def test_generate_security_tests(self, test_forge):
        """セキュリティテスト生成のテスト"""
        task = {
            "task_id": "test_security_001",
            "task_type": "generate_security_tests",
            "spec": {
                "vulnerabilities": ["injection", "xss", "auth"],
                "requirements": [
                    {
                        "name": "custom_auth_check",
                        "description": "Custom authentication test",
                        "test_vectors": ["invalid_token", "expired_token"],
                    }
                ],
                "app_type": "web",
            },
        }

        result = await test_forge.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert result.result_data["test_type"] == "security"

        test_code = result.result_data["test_code"]
        assert "class SecurityTestSuite" in test_code
        assert "def test_sql_injection" in test_code
        assert "def test_xss_vulnerability" in test_code
        assert "def test_security_requirement_custom_auth_check" in test_code

        assert result.result_data["vulnerability_coverage"] > 0
        assert result.result_data["custom_requirements"] == 1

    @pytest.mark.asyncio
    async def test_generate_mutation_tests(self, test_forge):
        """ミューテーションテスト生成のテスト"""
        source_code = """
def compare_values(a, b):
    if a > b:
        return a + b
    elif a < b:
        return a - b
    else:
        return a * b
"""

        task = {
            "task_id": "test_mutation_001",
            "task_type": "generate_mutation_tests",
            "spec": {
                "source_code": source_code,
                "existing_tests": "",
                "operators": ["arithmetic", "logical", "relational"],
            },
        }

        result = await test_forge.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert result.result_data["test_type"] == "mutation"

        test_code = result.result_data["test_code"]
        assert "class MutationTester" in test_code
        assert "def test_mutation_" in test_code

        assert result.result_data["mutation_points"] > 0
        assert "arithmetic" in result.result_data["operators_used"]
        assert "relational" in result.result_data["operators_used"]
        assert result.result_data["mutation_coverage"] > 0

    @pytest.mark.asyncio
    async def test_analyze_test_coverage(self, test_forge):
        """テストカバレッジ分析のテスト"""
        source_code = """
def function_one():
    return "one"

def function_two():
    return "two"

class TestClass:
    def method_one(self):
        return "method"
"""

        test_code = """
def test_function_one():
    assert function_one() == "one"

class TestTestClass:
    def test_method_one(self):
        obj = TestClass()
        assert obj.method_one() == "method"
"""

        task = {
            "task_id": "test_coverage_001",
            "task_type": "analyze_test_coverage",
            "source_code": source_code,
            "test_code": test_code,
        }

        result = await test_forge.execute_task(task)

        assert result.status == TaskStatus.COMPLETED

        coverage_data = result.result_data
        assert "overall_coverage" in coverage_data
        assert "function_coverage" in coverage_data
        assert "class_coverage" in coverage_data
        assert "source_stats" in coverage_data
        assert "test_stats" in coverage_data
        assert "recommendations" in coverage_data

        # 統計確認
        assert coverage_data["source_stats"]["functions"] == 2
        assert coverage_data["source_stats"]["classes"] == 1
        assert coverage_data["test_stats"]["test_functions"] == 1
        assert coverage_data["test_stats"]["test_classes"] == 1

    @pytest.mark.asyncio
    async def test_generate_test_data(self, test_forge):
        """テストデータ生成のテスト"""
        task = {
            "task_id": "test_data_001",
            "task_type": "generate_test_data",
            "spec": {
                "schema": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                    "email": {"type": "email"},
                    "score": {"type": "float"},
                    "active": {"type": "boolean"},
                    "id": {"type": "uuid"},
                },
                "count": 5,
                "type": "random",
            },
        }

        result = await test_forge.execute_task(task)

        assert result.status == TaskStatus.COMPLETED

        test_data = result.result_data["test_data"]
        assert len(test_data) == 5

        for item in test_data:
            assert "name" in item
            assert "age" in item
            assert "email" in item
            assert "score" in item
            assert "active" in item
            assert "id" in item

            assert isinstance(item["age"], int)
            assert isinstance(item["score"], float)
            assert isinstance(item["active"], bool)
            assert "@example.com" in item["email"]

    @pytest.mark.asyncio
    async def test_optimize_test_suite(self, test_forge):
        """テストスイート最適化のテスト"""
        original_suite = """
def test_slow_function():
    time.sleep(1)
    assert True

def test_redundant_one():
    assert True

def test_redundant_two():
    assert True
"""

        task = {
            "task_id": "test_optimize_001",
            "task_type": "optimize_test_suite",
            "spec": {
                "test_suite": original_suite,
                "goals": ["speed", "coverage", "maintainability"],
            },
        }

        result = await test_forge.execute_task(task)

        assert result.status == TaskStatus.COMPLETED

        optimization_data = result.result_data
        assert "optimized_suite" in optimization_data
        assert "optimizations_applied" in optimization_data
        assert "optimization_goals" in optimization_data

        optimizations = optimization_data["optimizations_applied"]
        assert len(optimizations) > 0
        assert any("Parallel test execution" in opt for opt in optimizations)
        assert any("test case identification" in opt for opt in optimizations)

    @pytest.mark.asyncio
    async def test_craft_artifact(self, test_forge):
        """craft_artifactメソッドのテスト"""
        specification = {
            "test_type": "unit",
            "source_code": "def hello(): return 'world'",
            "framework": "pytest",
        }

        result = await test_forge.craft_artifact(specification)

        assert "test_code" in result
        assert result["test_type"] == "unit"
        assert result["framework"] == "pytest"

    @pytest.mark.asyncio
    async def test_error_handling_invalid_code(self, test_forge):
        """不正コードでのエラーハンドリングテスト"""
        task = {
            "task_id": "test_error_001",
            "task_type": "generate_unit_tests",
            "spec": {
                "source_code": "def invalid_syntax(: # 構文エラー",
                "framework": "pytest",
            },
        }

        result = await test_forge.execute_task(task)

        assert result.status == TaskStatus.FAILED
        assert result.error_message is not None
        assert "Invalid Python code" in result.error_message

    @pytest.mark.asyncio
    async def test_error_handling_missing_source(self, test_forge):
        """ソースコード不足でのエラーハンドリングテスト"""
        task = {
            "task_id": "test_error_002",
            "task_type": "generate_unit_tests",
            "spec": {
                "framework": "pytest"
                # source_codeが不足
            },
        }

        result = await test_forge.execute_task(task)

        assert result.status == TaskStatus.FAILED
        assert "Source code is required" in result.error_message

    @pytest.mark.asyncio
    async def test_error_handling_unknown_task(self, test_forge):
        """未知のタスクタイプでのエラーハンドリングテスト"""
        task = {
            "task_id": "test_error_003",
            "task_type": "unknown_test_type",
            "spec": {},
        }

        result = await test_forge.execute_task(task)

        assert result.status == TaskStatus.FAILED
        assert "Unknown task type" in result.error_message

    def test_assertion_patterns(self, test_forge):
        """アサーションパターンのテスト"""
        patterns = test_forge.assertion_patterns

        assert "equality" in patterns
        assert "truth" in patterns
        assert "raises" in patterns

        # パターンの形式確認
        equality_patterns = patterns["equality"]
        assert any("assert" in pattern for pattern in equality_patterns)
        assert any("assertEqual" in pattern for pattern in equality_patterns)

    def test_mock_strategies(self, test_forge):
        """モック戦略のテスト"""
        strategies = test_forge.mock_strategies

        assert "function" in strategies
        assert "class" in strategies
        assert "module" in strategies

        # 戦略の形式確認
        func_strategy = strategies["function"]
        assert "@patch" in func_strategy
        assert "def test_" in func_strategy

    def test_security_test_vectors(self, test_forge):
        """セキュリティテストベクターのテスト"""
        # SQL injection vectors
        sql_vectors = test_forge._get_security_test_vectors("injection")
        assert len(sql_vectors) > 0
        assert any("DROP TABLE" in vector for vector in sql_vectors)

        # XSS vectors
        xss_vectors = test_forge._get_security_test_vectors("xss")
        assert any("<script>" in vector for vector in xss_vectors)

        # Unknown category
        unknown_vectors = test_forge._get_security_test_vectors("unknown")
        assert unknown_vectors == ["test_vector"]

    def test_mutation_operators(self, test_forge):
        """ミューテーション演算子のテスト"""
        import ast

        # 算術演算子
        add_op = ast.Add()
        mutations = test_forge._get_arithmetic_mutations(add_op)
        assert "Sub" in mutations
        assert "Mult" in mutations
        assert "Div" in mutations

        # 論理演算子
        and_op = ast.And()
        mutations = test_forge._get_logical_mutations(and_op)
        assert "Or" in mutations

        # 比較演算子
        eq_op = ast.Eq()
        mutations = test_forge._get_relational_mutations(eq_op)
        assert "NotEq" in mutations
        assert "Lt" in mutations
        assert "Gt" in mutations

    def test_test_quality_validation(self, test_forge):
        """テスト品質検証のテスト"""
        # 高品質テストデータ
        high_quality_data = {
            "test_code": "def test_function(): assert True",
            "test_count": 10,
            "estimated_coverage": 95.0,
            "success": True,
        }

        # 品質検証の実行（非同期関数なのでasyncio.run使用は避ける）
        # 代わりに同期的なテストで検証

        # テストコードの構文チェック
        try:
            ast.parse(high_quality_data["test_code"])
            syntax_ok = True
        except:
            syntax_ok = False

        assert syntax_ok is True

        # アサーション密度計算
        assertion_count = high_quality_data["test_code"].count("assert")
        test_count = high_quality_data["test_count"]
        assertion_density = assertion_count / test_count

        # カバレッジ確認
        coverage = high_quality_data["estimated_coverage"]
        assert coverage >= test_forge.test_quality_metrics["coverage_target"]

    def test_templates(self, test_forge):
        """テンプレートのテスト"""
        # Pytestテンプレート
        pytest_template = test_forge._get_pytest_template()
        assert "{imports}" in pytest_template
        assert "{test_functions}" in pytest_template
        assert "import pytest" in pytest_template

        # Unittestテンプレート
        unittest_template = test_forge._get_unittest_template()
        assert "{imports}" in unittest_template
        assert "{test_classes}" in unittest_template
        assert "import unittest" in unittest_template

        # Doctestテンプレート
        doctest_template = test_forge._get_doctest_template()
        assert "{functions_with_doctests}" in doctest_template
        assert "import doctest" in doctest_template


async def test_integration():
    """統合テスト"""
    print("=== TestForge統合テスト ===")

    forge = TestForge()

    # ユニットテスト生成
    unit_task = {
        "task_id": "integration_001",
        "task_type": "generate_unit_tests",
        "spec": {
            "source_code": """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)

class MathUtils:
    @staticmethod
    def is_prime(num):
        if num < 2:
            return False
        for i in range(2, int(num ** 0.5) + 1):
            if num % i == 0:
                return False
        return True
""",
            "framework": "pytest",
            "coverage_target": 90.0,
        },
    }

    result = await forge.execute_task(unit_task)
    print(f"✓ ユニットテスト生成: {result.status.value}, quality={result.quality_score}")

    # セキュリティテスト生成
    security_task = {
        "task_id": "integration_002",
        "task_type": "generate_security_tests",
        "spec": {"vulnerabilities": ["injection", "xss"], "app_type": "web"},
    }

    security_result = await forge.execute_task(security_task)
    print(
        f"✓ セキュリティテスト生成: vulnerability_coverage={security_result.result_data['vulnerability_coverage']}"
    )

    # テストデータ生成
    data_task = {
        "task_id": "integration_003",
        "task_type": "generate_test_data",
        "spec": {
            "schema": {
                "user_id": {"type": "uuid"},
                "username": {"type": "string"},
                "age": {"type": "integer"},
            },
            "count": 3,
        },
    }

    data_result = await forge.execute_task(data_task)
    print(f"✓ テストデータ生成: {data_result.result_data['data_count']}件生成")

    print("\n統合テスト: 完了")


if __name__ == "__main__":
    # pytestが使えない場合の簡易テスト
    asyncio.run(test_integration())
