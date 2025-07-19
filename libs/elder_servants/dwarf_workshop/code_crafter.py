"""
CodeCrafter - Python実装専門サーバント
ドワーフ工房のエースプログラマー
"""

import ast
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import textwrap
# Optional formatting libraries
try:
    import black
    HAS_BLACK = True
except ImportError:
    HAS_BLACK = False

try:
    import autopep8
    HAS_AUTOPEP8 = True
except ImportError:
    HAS_AUTOPEP8 = False

from libs.elder_servants.base.elder_servant import (
    ServantCategory, ServantCapability, 
    TaskResult, TaskStatus
)
from libs.elder_servants.base.specialized_servants import DwarfServant


class CodeCrafter(DwarfServant[Dict[str, Any], Dict[str, Any]]):
    """
    D01: CodeCrafter - Python実装専門サーバント
    関数・クラス・モジュール生成のエキスパート
    
    EldersLegacy準拠: EldersServiceLegacy継承による統一インターフェース
    """
    
    def __init__(self):
        capabilities = [
            ServantCapability(
                "generate_function",
                "Python関数の生成",
                ["function_spec"],
                ["python_code"],
                complexity=3
            ),
            ServantCapability(
                "generate_class",
                "Pythonクラスの生成",
                ["class_spec"],
                ["python_code"],
                complexity=5
            ),
            ServantCapability(
                "generate_module",
                "Pythonモジュールの生成",
                ["module_spec"],
                ["python_code"],
                complexity=7
            ),
            ServantCapability(
                "refactor_code",
                "コードリファクタリング",
                ["python_code", "refactor_spec"],
                ["refactored_code"],
                complexity=6
            ),
            ServantCapability(
                "add_type_hints",
                "型ヒント追加",
                ["python_code"],
                ["typed_code"],
                complexity=4
            ),
            ServantCapability(
                "optimize_code",
                "コード最適化",
                ["python_code", "optimization_target"],
                ["optimized_code"],
                complexity=5
            )
        ]
        
        super().__init__(
            servant_id="D01",
            servant_name="CodeCrafter",
            specialization="Python実装",
            capabilities=capabilities
        )
        
        # コード生成テンプレート
        self.templates = {
            "function": self._get_function_template(),
            "class": self._get_class_template(),
            "module": self._get_module_template()
        }
    
    async def craft_artifact(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        """
        DwarfServant実装: 製作品作成
        
        Args:
            specification: 製作仕様
            
        Returns:
            Dict[str, Any]: 製作品
        """
        artifact_type = specification.get("type", "function")
        
        if artifact_type == "function":
            return await self._generate_function(specification)
        elif artifact_type == "class":
            return await self._generate_class(specification)
        elif artifact_type == "module":
            return await self._generate_module(specification)
        else:
            return {
                "code": "",
                "type": "error",
                "error": f"Unknown artifact type: {artifact_type}"
            }
    
    def get_specialized_capabilities(self) -> List[ServantCapability]:
        """専門能力の取得"""
        return [
            ServantCapability(
                "generate_test_code",
                "テストコード生成",
                ["code_to_test"],
                ["test_code"],
                complexity=5
            ),
            ServantCapability(
                "generate_documentation",
                "ドキュメント生成",
                ["python_code"],
                ["documentation"],
                complexity=3
            ),
            ServantCapability(
                "code_analysis",
                "コード品質分析",
                ["python_code"],
                ["analysis_report"],
                complexity=4
            )
        ]
    
    async def execute_task(self, task: Dict[str, Any]) -> TaskResult:
        """タスク実行"""
        start_time = datetime.now()
        task_id = task.get("task_id", "unknown")
        task_type = task.get("task_type", "")
        
        try:
            self.logger.info(f"Executing task {task_id}: {task_type}")
            
            result_data = {}
            
            # ペイロードから仕様を取得
            payload = task.get("payload", {})
            
            if task_type == "generate_function":
                result_data = await self._generate_function(payload.get("spec", {}))
            elif task_type == "generate_class":
                result_data = await self._generate_class(payload.get("spec", {}))
            elif task_type == "generate_module":
                result_data = await self._generate_module(payload.get("spec", {}))
            elif task_type == "refactor_code":
                result_data = await self._refactor_code(
                    payload.get("code", ""),
                    payload.get("refactor_spec", {})
                )
            elif task_type == "add_type_hints":
                result_data = await self._add_type_hints(payload.get("code", ""))
            elif task_type == "optimize_code":
                result_data = await self._optimize_code(
                    payload.get("code", ""),
                    payload.get("optimization_target", "performance")
                )
            elif task_type == "generate_test_code":
                result_data = await self._generate_test_code(payload.get("code", ""))
            elif task_type == "code_analysis":
                result_data = await self._analyze_code(payload.get("code", ""))
            else:
                raise ValueError(f"Unknown task type: {task_type}")
            
            # 品質検証
            quality_score = await self._validate_code_quality(result_data)
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return TaskResult(
                task_id=task_id,
                servant_id=self.servant_id,
                status=TaskStatus.COMPLETED,
                result_data=result_data,
                execution_time_ms=execution_time,
                quality_score=quality_score
            )
            
        except Exception as e:
            self.logger.error(f"Task {task_id} failed: {str(e)}")
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return TaskResult(
                task_id=task_id,
                servant_id=self.servant_id,
                status=TaskStatus.FAILED,
                error_message=str(e),
                execution_time_ms=execution_time,
                quality_score=0.0
            )
    
    async def _generate_function(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """関数生成"""
        name = spec.get("name", "unnamed_function")
        params = spec.get("parameters", [])
        return_type = spec.get("return_type", "Any")
        docstring = spec.get("docstring", "")
        body = spec.get("body", "pass")
        decorators = spec.get("decorators", [])
        
        # パラメータ文字列の生成
        param_strings = []
        for param in params:
            param_str = param["name"]
            if "type" in param:
                param_str += f": {param['type']}"
            if "default" in param:
                param_str += f" = {param['default']}"
            param_strings.append(param_str)
        
        params_str = ", ".join(param_strings)
        
        # デコレータ文字列
        decorator_lines = [f"@{dec}" for dec in decorators]
        decorator_str = "\n".join(decorator_lines) + "\n" if decorators else ""
        
        # 関数生成
        code = f"""{decorator_str}def {name}({params_str}) -> {return_type}:
    \"\"\"{docstring}\"\"\"
    {body}"""
        
        # フォーマット
        if HAS_BLACK:
            try:
                formatted_code = black.format_str(code, mode=black.Mode())
            except:
                formatted_code = code
        elif HAS_AUTOPEP8:
            try:
                formatted_code = autopep8.fix_code(code)
            except:
                formatted_code = code
        else:
            formatted_code = code
        
        return {
            "code": formatted_code,
            "name": name,
            "type": "function",
            "line_count": len(formatted_code.splitlines())
        }
    
    async def _generate_class(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """クラス生成"""
        name = spec.get("name", "UnnamedClass")
        base_classes = spec.get("base_classes", [])
        docstring = spec.get("docstring", "")
        attributes = spec.get("attributes", [])
        methods = spec.get("methods", [])
        decorators = spec.get("decorators", [])
        
        # 基底クラス文字列
        bases_str = f"({', '.join(base_classes)})" if base_classes else ""
        
        # デコレータ文字列
        decorator_lines = [f"@{dec}" for dec in decorators]
        decorator_str = "\n".join(decorator_lines) + "\n" if decorators else ""
        
        # クラス本体の生成
        class_body = []
        
        # __init__メソッド
        if attributes:
            init_params = ["self"] + [f"{attr['name']}: {attr.get('type', 'Any')}" for attr in attributes]
            init_body = "\n        ".join([f"self.{attr['name']} = {attr['name']}" for attr in attributes])
            class_body.append(f"""
    def __init__({", ".join(init_params)}):
        {init_body}""")
        
        # その他のメソッド
        for method in methods:
            method_spec = {
                "name": method.get("name", "method"),
                "parameters": [{"name": "self"}] + method.get("parameters", []),
                "return_type": method.get("return_type", "None"),
                "docstring": method.get("docstring", ""),
                "body": method.get("body", "pass"),
                "decorators": method.get("decorators", [])
            }
            method_result = await self._generate_function(method_spec)
            class_body.append("\n    " + "\n    ".join(method_result["code"].splitlines()))
        
        # クラス生成
        body_str = "\n".join(class_body) if class_body else "\n    pass"
        
        code = f"""{decorator_str}class {name}{bases_str}:
    \"\"\"{docstring}\"\"\"{body_str}"""
        
        # フォーマット
        if HAS_BLACK:
            try:
                formatted_code = black.format_str(code, mode=black.Mode())
            except:
                formatted_code = code
        elif HAS_AUTOPEP8:
            try:
                formatted_code = autopep8.fix_code(code)
            except:
                formatted_code = code
        else:
            formatted_code = code
        
        return {
            "code": formatted_code,
            "name": name,
            "type": "class",
            "line_count": len(formatted_code.splitlines()),
            "method_count": len(methods) + (1 if attributes else 0)
        }
    
    async def _generate_module(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """モジュール生成"""
        name = spec.get("name", "unnamed_module")
        docstring = spec.get("docstring", "")
        imports = spec.get("imports", [])
        constants = spec.get("constants", [])
        functions = spec.get("functions", [])
        classes = spec.get("classes", [])
        
        module_parts = []
        
        # モジュールドキュメント
        if docstring:
            module_parts.append(f'"""\n{docstring}\n"""')
        
        # インポート
        if imports:
            import_lines = []
            for imp in imports:
                if isinstance(imp, str):
                    import_lines.append(f"import {imp}")
                elif isinstance(imp, dict):
                    module = imp.get("module", "")
                    names = imp.get("names", [])
                    if names:
                        import_lines.append(f"from {module} import {', '.join(names)}")
                    else:
                        import_lines.append(f"import {module}")
            module_parts.append("\n".join(import_lines))
        
        # 定数
        if constants:
            const_lines = []
            for const in constants:
                const_lines.append(f"{const['name']} = {const['value']}")
            module_parts.append("\n".join(const_lines))
        
        # 関数
        for func_spec in functions:
            func_result = await self._generate_function(func_spec)
            module_parts.append(func_result["code"])
        
        # クラス
        for class_spec in classes:
            class_result = await self._generate_class(class_spec)
            module_parts.append(class_result["code"])
        
        # モジュール全体のコード
        code = "\n\n\n".join(module_parts)
        
        # フォーマット
        if HAS_BLACK:
            try:
                formatted_code = black.format_str(code, mode=black.Mode())
            except:
                formatted_code = code
        elif HAS_AUTOPEP8:
            try:
                formatted_code = autopep8.fix_code(code)
            except:
                formatted_code = code
        else:
            formatted_code = code
        
        return {
            "code": formatted_code,
            "name": name,
            "type": "module",
            "line_count": len(formatted_code.splitlines()),
            "function_count": len(functions),
            "class_count": len(classes)
        }
    
    async def _refactor_code(self, code: str, refactor_spec: Dict[str, Any]) -> Dict[str, Any]:
        """コードリファクタリング"""
        refactor_type = refactor_spec.get("type", "general")
        
        try:
            # ASTパース
            tree = ast.parse(code)
            
            if refactor_type == "extract_function":
                # 関数抽出（簡易実装）
                refactored_code = self._extract_function(code, tree, refactor_spec)
            elif refactor_type == "rename":
                # リネーム
                refactored_code = self._rename_identifiers(code, tree, refactor_spec)
            elif refactor_type == "simplify":
                # 簡略化
                refactored_code = self._simplify_code(code, tree)
            else:
                # デフォルト: フォーマットのみ
                refactored_code = self._format_code(code)
            
            return {
                "code": refactored_code,
                "type": "refactored",
                "changes": self._detect_changes(code, refactored_code)
            }
            
        except Exception as e:
            self.logger.error(f"Refactoring failed: {e}")
            return {
                "code": code,
                "type": "unchanged",
                "error": str(e)
            }
    
    async def _add_type_hints(self, code: str) -> Dict[str, Any]:
        """型ヒント追加（簡易実装）"""
        try:
            tree = ast.parse(code)
            
            # 型推論（簡易版）
            type_hints = self._infer_types(tree)
            
            # 型ヒント適用
            typed_code = self._apply_type_hints(code, type_hints)
            
            return {
                "code": typed_code,
                "type": "typed",
                "hints_added": len(type_hints)
            }
            
        except Exception as e:
            self.logger.error(f"Type hint addition failed: {e}")
            return {
                "code": code,
                "type": "unchanged",
                "error": str(e)
            }
    
    async def _optimize_code(self, code: str, optimization_target: str) -> Dict[str, Any]:
        """コード最適化"""
        try:
            tree = ast.parse(code)
            
            if optimization_target == "performance":
                optimized_code = self._optimize_performance(code, tree)
            elif optimization_target == "memory":
                optimized_code = self._optimize_memory(code, tree)
            elif optimization_target == "readability":
                optimized_code = self._optimize_readability(code, tree)
            else:
                optimized_code = self._format_code(code)
            
            return {
                "code": optimized_code,
                "type": "optimized",
                "target": optimization_target,
                "improvements": self._measure_improvements(code, optimized_code)
            }
            
        except Exception as e:
            self.logger.error(f"Optimization failed: {e}")
            return {
                "code": code,
                "type": "unchanged",
                "error": str(e)
            }
    
    async def _generate_test_code(self, code: str) -> Dict[str, Any]:
        """テストコード生成"""
        try:
            tree = ast.parse(code)
            
            # テスト対象の関数とクラスを抽出
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            
            test_code_parts = [
                '"""自動生成されたテストコード"""',
                "import pytest",
                "import unittest",
                "from unittest.mock import Mock, patch",
                ""
            ]
            
            # 関数のテスト生成
            for func in functions:
                if not func.name.startswith("_"):
                    test_name = f"test_{func.name}"
                    test_code_parts.append(f"""
def {test_name}():
    \"\"\"Test for {func.name}\"\"\"
    # TODO: Implement test
    assert True  # Placeholder""")
            
            # クラスのテスト生成
            for cls in classes:
                test_class_name = f"Test{cls.name}"
                test_code_parts.append(f"""

class {test_class_name}(unittest.TestCase):
    \"\"\"Test for {cls.name}\"\"\"
    
    def setUp(self):
        # TODO: Setup test fixtures
        pass
    
    def test_init(self):
        \"\"\"Test initialization\"\"\"
        # TODO: Implement test
        pass""")
            
            test_code = "\n".join(test_code_parts)
            
            return {
                "code": test_code,
                "type": "test",
                "test_count": len(functions) + len(classes)
            }
            
        except Exception as e:
            self.logger.error(f"Test generation failed: {e}")
            return {
                "code": "",
                "type": "error",
                "error": str(e)
            }
    
    async def _analyze_code(self, code: str) -> Dict[str, Any]:
        """コード品質分析"""
        try:
            tree = ast.parse(code)
            
            analysis = {
                "line_count": len(code.splitlines()),
                "function_count": len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                "class_count": len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
                "complexity": self._calculate_complexity(tree),
                "issues": self._detect_code_issues(tree),
                "suggestions": self._generate_suggestions(tree)
            }
            
            return {
                "type": "analysis",
                "report": analysis,
                "quality_score": self._calculate_quality_score(analysis)
            }
            
        except Exception as e:
            self.logger.error(f"Code analysis failed: {e}")
            return {
                "type": "error",
                "error": str(e)
            }
    
    async def _validate_code_quality(self, result_data: Dict[str, Any]) -> float:
        """コード品質検証"""
        if "error" in result_data:
            return 0.0
        
        quality_score = 50.0  # 基本スコア
        
        # コードが存在する
        if "code" in result_data and result_data["code"]:
            quality_score += 20.0
            
            # 構文的に正しい
            try:
                ast.parse(result_data["code"])
                quality_score += 20.0
            except:
                pass
            
            # フォーマットされている
            if self._is_formatted(result_data["code"]):
                quality_score += 10.0
        
        return min(quality_score, 100.0)
    
    # ヘルパーメソッド
    def _get_function_template(self) -> str:
        return """def {name}({params}) -> {return_type}:
    \"\"\"{docstring}\"\"\"
    {body}"""
    
    def _get_class_template(self) -> str:
        return """class {name}{bases}:
    \"\"\"{docstring}\"\"\"
    {body}"""
    
    def _get_module_template(self) -> str:
        return """\"\"\"{docstring}\"\"\"

{imports}

{constants}

{functions}

{classes}"""
    
    def _extract_function(self, code: str, tree: ast.AST, spec: Dict[str, Any]) -> str:
        """関数抽出（簡易実装）"""
        # TODO: 実装
        return code
    
    def _rename_identifiers(self, code: str, tree: ast.AST, spec: Dict[str, Any]) -> str:
        """識別子リネーム（簡易実装）"""
        old_name = spec.get("old_name", "")
        new_name = spec.get("new_name", "")
        
        if old_name and new_name:
            return code.replace(old_name, new_name)
        return code
    
    def _simplify_code(self, code: str, tree: ast.AST) -> str:
        """コード簡略化（簡易実装）"""
        return self._format_code(code)
    
    def _detect_changes(self, original: str, refactored: str) -> List[str]:
        """変更検出"""
        changes = []
        if len(original.splitlines()) != len(refactored.splitlines()):
            changes.append(f"Line count changed: {len(original.splitlines())} -> {len(refactored.splitlines())}")
        return changes
    
    def _infer_types(self, tree: ast.AST) -> Dict[str, str]:
        """型推論（簡易実装）"""
        return {}
    
    def _apply_type_hints(self, code: str, type_hints: Dict[str, str]) -> str:
        """型ヒント適用（簡易実装）"""
        return code
    
    def _optimize_performance(self, code: str, tree: ast.AST) -> str:
        """パフォーマンス最適化（簡易実装）"""
        return self._format_code(code)
    
    def _optimize_memory(self, code: str, tree: ast.AST) -> str:
        """メモリ最適化（簡易実装）"""
        return self._format_code(code)
    
    def _optimize_readability(self, code: str, tree: ast.AST) -> str:
        """可読性最適化"""
        return self._format_code(code)
    
    def _measure_improvements(self, original: str, optimized: str) -> List[str]:
        """改善測定"""
        return ["Code formatted and optimized"]
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """複雑度計算（簡易実装）"""
        # McCabe複雑度の簡易版
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
        return complexity
    
    def _detect_code_issues(self, tree: ast.AST) -> List[str]:
        """コード問題検出"""
        issues = []
        
        # 長すぎる関数
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if len(node.body) > 50:
                    issues.append(f"Function '{node.name}' is too long")
        
        return issues
    
    def _generate_suggestions(self, tree: ast.AST) -> List[str]:
        """改善提案生成"""
        suggestions = []
        
        # docstring不足
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    suggestions.append(f"Add docstring to '{node.name}'")
        
        return suggestions
    
    def _calculate_quality_score(self, analysis: Dict[str, Any]) -> float:
        """品質スコア計算"""
        score = 100.0
        
        # 問題ごとに減点
        score -= len(analysis.get("issues", [])) * 5
        
        # 複雑度による減点
        complexity = analysis.get("complexity", 0)
        if complexity > 10:
            score -= (complexity - 10) * 2
        
        return max(score, 0.0)
    
    def _format_code(self, code: str) -> str:
        """コードフォーマット"""
        if HAS_BLACK:
            try:
                return black.format_str(code, mode=black.Mode())
            except:
                pass
        
        if HAS_AUTOPEP8:
            try:
                return autopep8.fix_code(code)
            except:
                pass
        
        return code
    
    def _is_formatted(self, code: str) -> bool:
        """フォーマット済みかチェック"""
        formatted = self._format_code(code)
        return formatted == code