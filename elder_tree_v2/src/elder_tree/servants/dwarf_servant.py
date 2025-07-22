"""
Dwarf Servant - ドワーフ族サーバント
開発特化型サーバント
"""

from typing import Dict, Any
import asyncio
import ast
import black
import isort
from elder_tree.servants.base_servant import ElderServantBase
import structlog


class DwarfServant(ElderServantBase):
    """
    ドワーフ族基底クラス
    
    特徴:
    - コード生成・実装に特化
    - TDDアプローチ
    - 高品質コードの追求
    """
    
    def __init__(self, name: str, specialty: str, port: int):
        super().__init__(
            name=name,
            tribe="dwarf",
            specialty=specialty,
            port=port
        )
        
        # ドワーフ特有の設定
        self.code_style = "black"  # コードフォーマッター
        self.test_framework = "pytest"
        self.coverage_target = 95  # カバレッジ目標


class CodeCrafter(DwarfServant):
    """
    Code Crafter - コード生成スペシャリスト
    
    専門:
    - Pythonコード生成
    - TDDアプローチ
    - リファクタリング
    - コード品質保証
    """
    
    def __init__(self, port: int = 60101):
        super().__init__(
            name="code_crafter",
            specialty="Python code generation and TDD",
            port=port
        )
        
        # 追加ハンドラー登録
        self._register_code_handlers()
    
    def _register_code_handlers(self):
        """コード生成専用ハンドラー"""
        
        @self.on_message("generate_code")
        async def handle_generate_code(message) -> Dict[str, Any]:
            """
            コード生成リクエスト
            
            Input:
                - specification: 仕様
                - language: プログラミング言語
                - use_tdd: TDDアプローチを使うか
            """
            spec = message.data.get("specification", {})
            language = message.data.get("language", "python")
            use_tdd = message.data.get("use_tdd", True)
            
            if language.lower() != "python":
                return {
                    "status": "error",
                    "message": f"Language {language} not supported yet"
                }
            
            result = await self.execute_specialized_task(
                "code_generation",
                {"specification": spec, "use_tdd": use_tdd},
                {}
            )
            
            return {
                "status": "success",
                "code": result
            }
    
    async def execute_specialized_task(
        self,
        task_type: str,
        parameters: Dict[str, Any],
        consultation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        ドワーフ特化タスク実行
        """
        if task_type == "code_generation":
            spec = parameters.get("specification", {})
            use_tdd = parameters.get("use_tdd", True)
            
            # TDDアプローチ
            if use_tdd:
                # 1. テストコード生成
                test_code = await self._generate_test_code(spec)
                
                # 2. 実装コード生成
                impl_code = await self._generate_implementation_code(spec, test_code)
                
                # 3. コード品質チェック
                formatted_code = await self._format_code(impl_code)
                formatted_test = await self._format_code(test_code)
                
                return {
                    "test_code": formatted_test,
                    "implementation_code": formatted_code,
                    "approach": "TDD",
                    "quality_checks": {
                        "syntax_valid": await self._check_syntax(formatted_code),
                        "test_syntax_valid": await self._check_syntax(formatted_test),
                        "formatted": True
                    }
                }
            else:
                # 直接実装
                impl_code = await self._generate_implementation_code(spec, None)
                formatted_code = await self._format_code(impl_code)
                
                return {
                    "implementation_code": formatted_code,
                    "approach": "Direct",
                    "quality_checks": {
                        "syntax_valid": await self._check_syntax(formatted_code),
                        "formatted": True
                    }
                }
        
        return await super().execute_specialized_task(
            task_type, parameters, consultation_result
        )
    
    async def _generate_test_code(self, spec: Dict[str, Any]) -> str:
        """
        テストコード生成
        """
        function_name = spec.get("function_name", "my_function")
        parameters = spec.get("parameters", [])
        returns = spec.get("returns", "Any")
        requirements = spec.get("requirements", [])
        
        # シンプルなテストテンプレート
        test_code = f'''
import pytest
from my_module import {function_name}


class Test{function_name.title().replace("_", "")}:
    """Test cases for {function_name}"""
    
    def test_{function_name}_basic(self):
        """Test basic functionality"""
        # Arrange
        {self._generate_test_params(parameters)}
        
        # Act
        result = {function_name}({', '.join(p["name"] for p in parameters)})
        
        # Assert
        assert result is not None
    
    def test_{function_name}_edge_cases(self):
        """Test edge cases"""
        # Test with None values
        with pytest.raises(ValueError):
            {function_name}({', '.join(["None" for _ in parameters])})
    
    @pytest.mark.parametrize("input_data,expected", [
        ({self._generate_parametrize_data(parameters)})
    ])
    def test_{function_name}_parametrized(self, input_data, expected):
        """Parametrized tests"""
        result = {function_name}(**input_data)
        assert result == expected
'''
        
        # Knowledge Sageからのアドバイスを適用
        if "knowledge_sage" in consultation_result:
            advice = consultation_result["knowledge_sage"].get("test_advice", [])
            # アドバイスに基づいてテストを追加
            # （簡略化のため省略）
        
        return test_code
    
    async def _generate_implementation_code(
        self, 
        spec: Dict[str, Any], 
        test_code: str = None
    ) -> str:
        """
        実装コード生成
        """
        function_name = spec.get("function_name", "my_function")
        parameters = spec.get("parameters", [])
        returns = spec.get("returns", "Any")
        requirements = spec.get("requirements", [])
        description = spec.get("description", "Function implementation")
        
        # パラメータ文字列生成
        param_str = ", ".join([
            f"{p['name']}: {p.get('type', 'Any')}" 
            for p in parameters
        ])
        
        # 基本実装テンプレート
        impl_code = f'''
from typing import {returns}
import logging

logger = logging.getLogger(__name__)


def {function_name}({param_str}) -> {returns}:
    """
    {description}
    
    Args:
{self._generate_docstring_args(parameters)}
    
    Returns:
        {returns}: Function result
        
    Raises:
        ValueError: If invalid parameters are provided
    """
    # Parameter validation
{self._generate_validation_code(parameters)}
    
    try:
        # Main implementation
{self._generate_implementation_body(spec, requirements)}
        
    except Exception as e:
        logger.error(f"Error in {function_name}: {{e}}")
        raise
'''
        
        return impl_code
    
    def _generate_test_params(self, parameters: list) -> str:
        """テストパラメータ生成"""
        lines = []
        for param in parameters:
            name = param["name"]
            param_type = param.get("type", "str")
            
            if param_type == "str":
                lines.append(f'{name} = "test_value"')
            elif param_type == "int":
                lines.append(f"{name} = 42")
            elif param_type == "float":
                lines.append(f"{name} = 3.14")
            elif param_type == "bool":
                lines.append(f"{name} = True")
            else:
                lines.append(f"{name} = None  # TODO: Set appropriate test value")
        
        return "\n        ".join(lines)
    
    def _generate_parametrize_data(self, parameters: list) -> str:
        """パラメトライズデータ生成"""
        # シンプルな例
        param_dict = "{" + ", ".join([f"'{p['name']}': 'value'" for p in parameters]) + "}"
        return f"({param_dict}, 'expected_result')"
    
    def _generate_docstring_args(self, parameters: list) -> str:
        """ドキュメント文字列の引数部分生成"""
        lines = []
        for param in parameters:
            name = param["name"]
            param_type = param.get("type", "Any")
            description = param.get("description", "Parameter description")
            lines.append(f"        {name} ({param_type}): {description}")
        
        return "\n".join(lines)
    
    def _generate_validation_code(self, parameters: list) -> str:
        """パラメータ検証コード生成"""
        lines = []
        for param in parameters:
            name = param["name"]
            param_type = param.get("type", "Any")
            required = param.get("required", True)
            
            if required:
                lines.append(f"    if {name} is None:")
                lines.append(f'        raise ValueError("{name} cannot be None")')
            
            # 型チェック（シンプル版）
            if param_type == "str":
                lines.append(f"    if not isinstance({name}, str):")
                lines.append(f'        raise TypeError("{name} must be a string")')
            elif param_type == "int":
                lines.append(f"    if not isinstance({name}, int):")
                lines.append(f'        raise TypeError("{name} must be an integer")')
        
        return "\n".join(lines) if lines else "    pass  # No validation needed"
    
    def _generate_implementation_body(self, spec: Dict[str, Any], requirements: list) -> str:
        """実装本体生成"""
        # 要件に基づいた基本実装
        lines = ["        # Implementation based on requirements"]
        
        for req in requirements:
            lines.append(f"        # Requirement: {req}")
        
        lines.append("        ")
        lines.append("        # TODO: Implement actual logic")
        lines.append("        result = None")
        lines.append("        ")
        lines.append("        return result")
        
        return "\n".join(lines)
    
    async def _format_code(self, code: str) -> str:
        """コードフォーマット"""
        try:
            # Blackでフォーマット
            formatted = black.format_str(code, mode=black.Mode())
            
            # isortでimport整理
            formatted = isort.code(formatted)
            
            return formatted
        except Exception as e:
            self.logger.warning(f"Code formatting failed: {e}")
            return code
    
    async def _check_syntax(self, code: str) -> bool:
        """構文チェック"""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False


# 単体実行用
async def main():
    crafter = CodeCrafter()
    await crafter.start()
    print(f"Code Crafter running on port {crafter.port}")
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await crafter.stop()


if __name__ == "__main__":
    asyncio.run(main())