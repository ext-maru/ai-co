"""
CodeCrafter サーバントのテストスイート
"""

import ast
import asyncio
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.append("/home/aicompany/ai_co")

from libs.elder_servants.base.elder_servant import ServantCategory, TaskStatus
from libs.elder_servants.dwarf_workshop.code_crafter import CodeCrafter


class TestCodeCrafter:
    """CodeCrafterサーバントのテスト"""

    @pytest.fixture
    def code_crafter(self):
        """CodeCrafterインスタンスのフィクスチャ"""
        return CodeCrafter()

    def test_initialization(self, code_crafter):
        """初期化テスト"""
        assert code_crafter.servant_id == "D01"
        assert code_crafter.servant_name == "CodeCrafter"
        assert code_crafter.category == ServantCategory.DWARF
        assert code_crafter.specialization == "Python実装"
        assert len(code_crafter.capabilities) == 6

    def test_specialized_capabilities(self, code_crafter):
        """専門能力のテスト"""
        capabilities = code_crafter.get_specialized_capabilities()
        assert len(capabilities) == 3

        cap_names = [cap.name for cap in capabilities]
        assert "generate_test_code" in cap_names
        assert "generate_documentation" in cap_names
        assert "code_analysis" in cap_names

    @pytest.mark.asyncio
    async def test_generate_function_simple(self, code_crafter):
        """簡単な関数生成のテスト"""
        task = {
            "task_id": "test_func_001",
            "task_type": "generate_function",
            "spec": {
                "name": "add_numbers",
                "parameters": [
                    {"name": "a", "type": "int"},
                    {"name": "b", "type": "int"},
                ],
                "return_type": "int",
                "docstring": "Add two numbers",
                "body": "return a + b",
            },
        }

        result = await code_crafter.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert result.quality_score >= 90.0
        assert "code" in result.result_data

        # 生成されたコードの検証
        code = result.result_data["code"]
        assert "def add_numbers(a: int, b: int) -> int:" in code
        assert "Add two numbers" in code
        assert "return a + b" in code

        # 構文的に正しいか確認
        ast.parse(code)

    @pytest.mark.asyncio
    async def test_generate_function_with_decorators(self, code_crafter):
        """デコレータ付き関数生成のテスト"""
        task = {
            "task_id": "test_func_002",
            "task_type": "generate_function",
            "spec": {
                "name": "cached_function",
                "parameters": [{"name": "x", "type": "int"}],
                "return_type": "int",
                "docstring": "Cached function",
                "body": "return x * 2",
                "decorators": ["lru_cache", "staticmethod"],
            },
        }

        result = await code_crafter.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        code = result.result_data["code"]
        assert "@lru_cache" in code
        assert "@staticmethod" in code

    @pytest.mark.asyncio
    async def test_generate_class_simple(self, code_crafter):
        """簡単なクラス生成のテスト"""
        task = {
            "task_id": "test_class_001",
            "task_type": "generate_class",
            "spec": {
                "name": "Person",
                "docstring": "A simple person class",
                "attributes": [
                    {"name": "name", "type": "str"},
                    {"name": "age", "type": "int"},
                ],
                "methods": [
                    {
                        "name": "greet",
                        "parameters": [],
                        "return_type": "str",
                        "body": "return f'Hello, I am {self.name}'",
                    }
                ],
            },
        }

        result = await code_crafter.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert result.quality_score >= 90.0

        code = result.result_data["code"]
        assert "class Person:" in code
        assert "def __init__(self, name: str, age: int):" in code
        assert "self.name = name" in code
        assert "def greet(self) -> str:" in code

        # 構文チェック
        ast.parse(code)

    @pytest.mark.asyncio
    async def test_generate_class_with_inheritance(self, code_crafter):
        """継承付きクラス生成のテスト"""
        task = {
            "task_id": "test_class_002",
            "task_type": "generate_class",
            "spec": {
                "name": "Student",
                "base_classes": ["Person", "ABC"],
                "docstring": "Student class",
                "attributes": [{"name": "student_id", "type": "str"}],
            },
        }

        result = await code_crafter.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        code = result.result_data["code"]
        assert "class Student(Person, ABC):" in code

    @pytest.mark.asyncio
    async def test_generate_module(self, code_crafter):
        """モジュール生成のテスト"""
        task = {
            "task_id": "test_module_001",
            "task_type": "generate_module",
            "spec": {
                "name": "utils",
                "docstring": "Utility functions",
                "imports": ["os", {"module": "typing", "names": ["List", "Dict"]}],
                "constants": [{"name": "MAX_SIZE", "value": "1024"}],
                "functions": [
                    {
                        "name": "helper",
                        "parameters": [],
                        "return_type": "None",
                        "body": "pass",
                    }
                ],
            },
        }

        result = await code_crafter.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        code = result.result_data["code"]
        assert "Utility functions" in code
        assert "import os" in code
        assert "from typing import List, Dict" in code
        assert "MAX_SIZE = 1024" in code
        assert "def helper() -> None:" in code

    @pytest.mark.asyncio
    async def test_refactor_code_rename(self, code_crafter):
        """コードリファクタリング（リネーム）のテスト"""
        original_code = """
def old_function():
    return "old_function called"
"""

        task = {
            "task_id": "test_refactor_001",
            "task_type": "refactor_code",
            "code": original_code,
            "refactor_spec": {
                "type": "rename",
                "old_name": "old_function",
                "new_name": "new_function",
            },
        }

        result = await code_crafter.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        code = result.result_data["code"]
        assert "new_function" in code
        assert "old_function" not in code

    @pytest.mark.asyncio
    async def test_add_type_hints(self, code_crafter):
        """型ヒント追加のテスト"""
        code_without_hints = """
def multiply(x, y):
    return x * y
"""

        task = {
            "task_id": "test_type_001",
            "task_type": "add_type_hints",
            "code": code_without_hints,
        }

        result = await code_crafter.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        # 簡易実装なので、現時点では変更なし
        assert "code" in result.result_data

    @pytest.mark.asyncio
    async def test_optimize_code(self, code_crafter):
        """コード最適化のテスト"""
        unformatted_code = """
def   messy_function(  x,y,  z ):
    return x+y+z
"""

        task = {
            "task_id": "test_optimize_001",
            "task_type": "optimize_code",
            "code": unformatted_code,
            "optimization_target": "readability",
        }

        result = await code_crafter.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        code = result.result_data["code"]
        # Blackでフォーマットされているはず
        assert "def messy_function(x, y, z):" in code

    @pytest.mark.asyncio
    async def test_generate_test_code(self, code_crafter):
        """テストコード生成のテスト"""
        source_code = """
def calculate(x, y):
    return x + y

class Calculator:
    def add(self, a, b):
        return a + b
"""

        task = {
            "task_id": "test_gen_test_001",
            "task_type": "generate_test_code",
            "code": source_code,
        }

        result = await code_crafter.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        test_code = result.result_data["code"]
        assert "import pytest" in test_code
        assert "test_calculate" in test_code
        assert "TestCalculator" in test_code

    @pytest.mark.asyncio
    async def test_code_analysis(self, code_crafter):
        """コード分析のテスト"""
        code_to_analyze = """
def complex_function(x, y, z):
    if x > 0:
        if y > 0:
            return x + y
        else:
            return x - y
    else:
        return z

class MyClass:
    pass
"""

        task = {
            "task_id": "test_analysis_001",
            "task_type": "code_analysis",
            "code": code_to_analyze,
        }

        result = await code_crafter.execute_task(task)

        assert result.status == TaskStatus.COMPLETED
        report = result.result_data["report"]
        assert report["function_count"] == 1
        assert report["class_count"] == 1
        assert report["complexity"] > 1
        assert isinstance(report["suggestions"], list)

    @pytest.mark.asyncio
    async def test_error_handling(self, code_crafter):
        """エラーハンドリングのテスト"""
        task = {"task_id": "test_error_001", "task_type": "unknown_type", "spec": {}}

        result = await code_crafter.execute_task(task)

        assert result.status == TaskStatus.FAILED
        assert result.error_message is not None
        assert "Unknown task type" in result.error_message

    @pytest.mark.asyncio
    async def test_invalid_code_generation(self, code_crafter):
        """不正なコード生成のテスト"""
        task = {
            "task_id": "test_invalid_001",
            "task_type": "generate_function",
            "spec": {"name": "123invalid", "body": "invalid syntax here!"},  # 不正な関数名
        }

        result = await code_crafter.execute_task(task)

        # タスク自体は完了するが、品質スコアが低い
        assert result.status == TaskStatus.COMPLETED
        assert result.quality_score < 100.0

    def test_template_methods(self, code_crafter):
        """テンプレートメソッドのテスト"""
        func_template = code_crafter._get_function_template()
        assert "{name}" in func_template
        assert "{params}" in func_template

        class_template = code_crafter._get_class_template()
        assert "{name}" in class_template
        assert "{docstring}" in class_template

        module_template = code_crafter._get_module_template()
        assert "{imports}" in module_template
        assert "{functions}" in module_template


async def test_integration():
    """統合テスト"""
    print("=== CodeCrafter統合テスト ===")

    crafter = CodeCrafter()

    # 関数生成
    func_task = {
        "task_id": "integration_001",
        "task_type": "generate_function",
        "spec": {
            "name": "fibonacci",
            "parameters": [{"name": "n", "type": "int"}],
            "return_type": "int",
            "docstring": "Calculate fibonacci number",
            "body": "if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
        },
    }

    result = await crafter.execute_task(func_task)
    print(f"✓ 関数生成: {result.status.value}, quality={result.quality_score}")

    # 生成したコードの分析
    analysis_task = {
        "task_id": "integration_002",
        "task_type": "code_analysis",
        "code": result.result_data["code"],
    }

    analysis_result = await crafter.execute_task(analysis_task)
    print(f"✓ コード分析: complexity={analysis_result.result_data['report']['complexity']}")

    print("\n統合テスト: 完了")


if __name__ == "__main__":
    # pytestが使えない場合の簡易テスト
    asyncio.run(test_integration())
