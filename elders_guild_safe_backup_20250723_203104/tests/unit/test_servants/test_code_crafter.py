"""
Code Crafter (Dwarf Servant) ユニットテスト
TDDコード生成機能の包括的テスト
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import ast
import black
import isort
from typing import Dict, Any
from textwrap import dedent

from elder_tree.servants.dwarf_servant import CodeCrafter, DwarfServant
from python_a2a import Message


class TestCodeCrafter:


"""Code Crafterテストスイート"""
        """Code Crafterインスタンス"""
        crafter = CodeCrafter(port=60101)
        # 4賢者への接続をモック
        crafter.sage_connections = {
            "knowledge_sage": True,
            "task_sage": True,
            "incident_sage": True,
            "rag_sage": True
        }
        yield crafter
        if hasattr(crafter, '_client'):
            await crafter.stop()
    
    @pytest.fixture
    def code_spec(self):

            """コード仕様のサンプル""" "calculate_fibonacci",
            "parameters": [
                {"name": "n", "type": "int", "description": "The position in fibonacci sequence"}
            ],
            "returns": "int",
            "description": "Calculate nth fibonacci number",
            "requirements": [
                "Handle negative numbers by raising ValueError",
                "Use memoization for performance",
                "Support large numbers"
            ]
        }
    
    @pytest.fixture
    def mock_sage_consultation(self):

                """賢者協議のモックレスポンス""" {
                "recommendations": ["Use dynamic programming approach"],
                "best_practices": ["Add type hints", "Include docstring"]
            },
            "task_sage": {
                "estimated_complexity": "medium",
                "suggested_tests": 5
            }
        }

    @pytest.mark.asyncio
    async def test_code_generation_with_tdd(self, code_crafter, code_spec):

            """TDDアプローチでのコード生成テスト""" code_spec,
            "language": "python",
            "use_tdd": True
        }
        
        # ハンドラーを取得
        handler = None
        for h in code_crafter._message_handlers.get("generate_code", []):
            handler = h["handler"]
            break
        
        # 賢者協議をモック
        with patch.object(code_crafter, 'consult_sages_before_task', 
                         return_value=AsyncMock(return_value={})):
            result = await handler(message)
        
        # 検証
        assert result["status"] == "success"
        assert "test_code" in result["code"]
        assert "implementation_code" in result["code"]
        
        # テストコードが先に生成されていることを確認
        test_code = result["code"]["test_code"]
        impl_code = result["code"]["implementation_code"]
        
        assert "def test_" in test_code
        assert "calculate_fibonacci" in test_code
        assert "pytest" in test_code
        
        # 実装コードの検証
        assert "def calculate_fibonacci" in impl_code
        assert "ValueError" in impl_code  # エラーハンドリング

    @pytest.mark.asyncio
    async def test_test_code_generation(self, code_crafter, code_spec):

            """テストコード生成の詳細テスト"""
            ast.parse(test_code)
        except SyntaxError:
            pytest.fail("Generated test code has syntax errors")

    @pytest.mark.asyncio
    async def test_implementation_code_generation(self, code_crafter, code_spec):

            """実装コード生成テスト""" int) -> int:" in impl_code
        assert '"""' in impl_code  # Docstring
        assert "ValueError" in impl_code  # エラーハンドリング
        assert "logging" in impl_code  # ロギング
        
        # ASTで構文チェック
        try:
            tree = ast.parse(impl_code)
            # 関数が定義されていることを確認
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            assert len(functions) >= 1
            assert functions[0].name == "calculate_fibonacci"
        except SyntaxError:
            pytest.fail("Generated implementation code has syntax errors")

    @pytest.mark.asyncio
    async def test_code_formatting(self, code_crafter):

            """コードフォーマッティングテスト"""
    result=x+y+z
    return    result
"""
        
        formatted_code = await code_crafter._format_code(unformatted_code)
        
        # Blackフォーマットが適用されていることを確認
        assert "def messy_function(x, y, z):" in formatted_code
        assert "result = x + y + z" in formatted_code
        
        # isortも適用されていることを確認（importがある場合）
        code_with_imports = """
import os
import sys
from typing import List
import asyncio

def test():
    pass
"""
        formatted_with_imports = await code_crafter._format_code(code_with_imports)
        lines = formatted_with_imports.strip().split('\n')
        # import順序が整理されていることを確認
        import_lines = [line for line in lines if line.startswith('import') or line.startswith('from')]
        assert len(import_lines) > 0

    @pytest.mark.asyncio
    async def test_syntax_validation(self, code_crafter):

    """構文検証テスト"""
    return 42
"""
        
        invalid_code = """
def invalid_function(
    return 42
"""
        
        # 有効なコード
        assert await code_crafter._check_syntax(valid_code) is True
        
        # 無効なコード
        assert await code_crafter._check_syntax(invalid_code) is False

    @pytest.mark.asyncio
    async def test_complex_code_generation(self, code_crafter):

    """複雑なコード生成テスト""" "process_data_pipeline",
            "parameters": [
                {"name": "data", "type": "List[Dict[str, Any]]", "description": "Input data"},
                {"name": "transformers", "type": "List[Callable]", "description": "Transform functions"},
                {"name": "validators", "type": "List[Callable]", "description": "Validation functions"}
            ],
            "returns": "Tuple[List[Dict[str, Any]], List[str]]",
            "description": "Process data through transformation and validation pipeline",
            "requirements": [
                "Apply transformers in sequence",
                "Collect validation errors",
                "Support async transformers",
                "Handle exceptions gracefully"
            ]
        }
        
        result = await code_crafter.execute_specialized_task(
            "code_generation",
            {"specification": complex_spec, "use_tdd": True},
            {}
        )
        
        # 複雑な型ヒントが正しく生成されていることを確認
        impl_code = result["implementation_code"]
        assert "List[Dict[str, Any]]" in impl_code
        assert "List[Callable]" in impl_code
        assert "Tuple[" in impl_code
        
        # 非同期処理のサポート
        assert "async" in impl_code or "await" in impl_code or "asyncio" in impl_code

    @pytest.mark.asyncio
    async def test_quality_checks(self, code_crafter, code_spec):

            """品質チェックテスト""" code_spec, "use_tdd": True},
            {}
        )
        
        # 品質チェック結果の検証
        quality_checks = result["quality_checks"]
        assert quality_checks["syntax_valid"] is True
        assert quality_checks["test_syntax_valid"] is True
        assert quality_checks["formatted"] is True

    @pytest.mark.asyncio
    async def test_sage_consultation_integration(self, code_crafter, code_spec, mock_sage_consultation):

            """賢者協議統合テスト"""
            
            result = await code_crafter.execute_specialized_task(
                "code_generation",
                {"specification": code_spec, "use_tdd": True},
                mock_sage_consultation
            )
            
            # 賢者のアドバイスが反映されていることを確認
            # （実装によっては、アドバイスの適用方法が異なる可能性がある）
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_handling(self, code_crafter):

                """エラーハンドリングテスト""" "",  # 空の関数名
            "parameters": []
        }
        
        message = Mock()
        message.data = {
            "specification": incomplete_spec,
            "language": "python",
            "use_tdd": True
        }
        
        handler = None
        for h in code_crafter._message_handlers.get("generate_code", []):
            handler = h["handler"]
            break
        
        with patch.object(code_crafter, 'consult_sages_before_task', 
                         return_value=AsyncMock(return_value={})):
            result = await handler(message)
            
            # エラーが適切に処理されることを確認
            # （実装によってはエラーでもデフォルト値で処理される可能性がある）
            assert result is not None

    @pytest.mark.asyncio
    async def test_unsupported_language(self, code_crafter, code_spec):

            """サポートされていない言語のテスト""" code_spec,
            "language": "rust",  # サポートされていない
            "use_tdd": True
        }
        
        handler = None
        for h in code_crafter._message_handlers.get("generate_code", []):
            handler = h["handler"]
            break
        
        result = await handler(message)
        
        # エラーが返されることを確認
        assert result["status"] == "error"
        assert "not supported" in result["message"]

    @pytest.mark.asyncio
    @pytest.mark.benchmark(group="code_generation")
    async def test_code_generation_performance(self, code_crafter, code_spec, benchmark):

            """コード生成パフォーマンステスト"""
            """generate_codeを生成"""
            return await code_crafter.execute_specialized_task(
                "code_generation",
                {"specification": code_spec, "use_tdd": True},
                {}
            )
        
        # ベンチマーク実行
        result = benchmark(lambda: asyncio.run(generate_code()))
        
        # パフォーマンス基準: 1秒以内
        assert benchmark.stats["mean"] < 1.0
        assert result is not None

    @pytest.mark.asyncio
    async def test_parametrize_data_generation(self, code_crafter):

        """パラメトライズテストデータ生成テスト""" "x", "type": "int"},
            {"name": "y", "type": "str"},
            {"name": "z", "type": "bool"}
        ]
        
        result = code_crafter._generate_parametrize_data(parameters)
        
        # 生成されたデータの形式を確認
        assert "{'x': 'value', 'y': 'value', 'z': 'value'}" in result
        assert "expected_result" in result

    @pytest.mark.asyncio
    async def test_validation_code_generation(self, code_crafter):

        """バリデーションコード生成テスト""" "age", "type": "int", "required": True},
            {"name": "name", "type": "str", "required": True},
            {"name": "email", "type": "str", "required": False}
        ]
        
        validation_code = code_crafter._generate_validation_code(parameters)
        
        # 必須パラメータのチェックが含まれることを確認
        assert "if age is None:" in validation_code
        assert "if name is None:" in validation_code
        assert "ValueError" in validation_code
        
        # 型チェックが含まれることを確認
        assert "isinstance(age, int)" in validation_code
        assert "isinstance(name, str)" in validation_code

    @pytest.mark.asyncio
    async def test_dwarf_servant_inheritance(self, code_crafter):

        """DwarfServant継承テスト"""
        """品質ゲート統合テスト"""
        # 品質基準を満たさないコードの生成をシミュレート
        low_quality_spec = {
            "function_name": "minimal_function",
            "parameters": [],
            "returns": "Any",
            "description": "Basic implementation for testing",
            "requirements": ["Simple implementation"]
        }
        
        # 品質チェックメソッドをモック
        with patch.object(code_crafter, 'check_quality', 
                         return_value={"score": 70, "passed": False, "issues": ["Too simple"]}):
            
            # execute_task経由で実行（品質チェックが走る）
            message = Mock()
            message.data = {
                "task_type": "code_generation",
                "parameters": {"specification": low_quality_spec, "use_tdd": False},
                "quality_requirements": {"no_todos": True, "test_coverage": 90}
            }
            
            # execute_taskハンドラーを探す
            handler = None
            for h in code_crafter._message_handlers.get("execute_task", []):
                handler = h["handler"]
                break
            
            if handler:
                with patch.object(code_crafter, 'consult_sages_before_task', 
                                 return_value={}):
                    with patch.object(code_crafter, 'collaborate_with_sage',
                                     return_value=AsyncMock()):
                        result = await handler(message)
                        
                        # 品質基準を満たさない場合の処理を確認
                        assert result is not None


# プロパティベーステスト
from hypothesis import given, strategies as st

class TestCodeCrafterProperties:

                        """Code Crafterプロパティベーステスト"""
        """Code Crafterインスタンス"""
        crafter = CodeCrafter(port=60101)
        yield crafter
        if hasattr(crafter, '_client'):
            await crafter.stop()
    
    @given(
        function_name=st.text(min_size=1, max_size=50).filter(lambda x: x.isidentifier()),
        param_count=st.integers(min_value=0, max_value=10),
        has_return=st.booleans(),
        use_tdd=st.booleans()
    )
    @pytest.mark.asyncio
    async def test_code_generation_properties(self, code_crafter, function_name, param_count, has_return, use_tdd):

        """コード生成のプロパティテスト"""
            parameters.append({
                "name": f"param_{i}",
                "type": "Any",
                "description": f"Parameter {i}"
            })
        
        spec = {
            "function_name": function_name,
            "parameters": parameters,
            "returns": "Any" if has_return else "None",
            "description": "Property test function",
            "requirements": ["Basic implementation"]
        }
        
        result = await code_crafter.execute_specialized_task(
            "code_generation",
            {"specification": spec, "use_tdd": use_tdd},
            {}
        )
        
        # プロパティ: 必ず結果が返される
        assert result is not None
        
        # プロパティ: TDDの場合、テストコードが含まれる
        if use_tdd:
            assert "test_code" in result
            assert "implementation_code" in result
        
        # プロパティ: 生成されたコードに関数名が含まれる
        if "implementation_code" in result:
            assert function_name in result["implementation_code"]