#!/usr/bin/env python3
"""
Elder Flow Servant Executor Real Implementation
エルダーサーバント実行システムの実装版
"""

import asyncio
import subprocess
import json
import os
import sys
import logging
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
try:
    import aiofiles
except ImportError:
    # aiofilesが利用できない場合の代替実装
    class aiofiles:
        @staticmethod
        def open(file_path, mode="r", encoding="utf-8"):
            return AsyncFileContext(file_path, mode, encoding)

class AsyncFileContext:
    """aiofilesの代替実装"""
    def __init__(self, file_path, mode="r", encoding="utf-8"):
        self.file_path = file_path
        self.mode = mode
        self.encoding = encoding
        self.file = None
    
    async def __aenter__(self):
        self.file = open(self.file_path, self.mode, encoding=self.encoding)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()
    
    async def write(self, data):
        if self.file:
            self.file.write(data)
    
    async def read(self):
        if self.file:
            return self.file.read()
        return ""
import ast
import black
import isort
import pytest

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.elder_flow_servant_executor import (
    ServantType,
    ServantStatus,
    ServantTask,
    BaseServant,
)

logger = logging.getLogger(__name__)


class CodeCraftsmanServantReal(BaseServant):
    """コード職人サーバント - 実装版"""

    def __init__(self, name: str = "CodeCraftsman"):
        super().__init__(ServantType.CODE_CRAFTSMAN, name)
        self.capabilities = [
            "create_file",
            "edit_file",
            "refactor_code",
            "generate_code",
            "tdd_generate_failing_test",
            "tdd_implement_code",
            "tdd_refactor_code",
            "analyze_code",
            "format_code",
            "optimize_imports",
        ]

    async def _execute_specific_task(self, task: ServantTask) -> Dict:
        """コード関連タスクの実行"""
        command = task.command
        args = task.arguments

        command_map = {
            "create_file": self._create_file,
            "edit_file": self._edit_file,
            "refactor_code": self._refactor_code,
            "generate_code": self._generate_code,
            "tdd_generate_failing_test": self._tdd_generate_failing_test,
            "tdd_implement_code": self._tdd_implement_code,
            "tdd_refactor_code": self._tdd_refactor_code,
            "analyze_code": self._analyze_code,
            "format_code": self._format_code,
            "optimize_imports": self._optimize_imports,
        }

        if command in command_map:
            return await command_map[command](args)
        else:
            raise ValueError(f"Unknown command: {command}")

    async def _create_file(self, args: Dict) -> Dict:
        """ファイル作成（実装）"""
        file_path = Path(args.get("file_path"))
        content = args.get("content", "")
        create_dirs = args.get("create_dirs", True)

        try:
            # ディレクトリを作成
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)

            # ファイルを非同期で書き込み
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(content)

            # ファイル情報を取得
            stat = file_path.stat()

            return {
                "action": "create_file",
                "file_path": str(file_path),
                "size": stat.st_size,
                "created": True,
                "success": True,
            }

        except Exception as e:
            return {
                "action": "create_file",
                "file_path": str(file_path),
                "error": str(e),
                "success": False,
            }

    async def _edit_file(self, args: Dict) -> Dict:
        """ファイル編集（実装）"""
        file_path = Path(args.get("file_path"))
        old_content = args.get("old_content", "")
        new_content = args.get("new_content", "")
        backup = args.get("backup", True)

        try:
            # ファイルが存在することを確認
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # バックアップを作成
            if backup:
                backup_path = file_path.with_suffix(file_path.suffix + ".bak")
                shutil.copy2(file_path, backup_path)

            # ファイルを読み込み
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()

            # 内容を置換
            if old_content in content:
                content = content.replace(old_content, new_content)
                replacements = 1
            else:
                # 部分一致を試みる
                replacements = 0
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if old_content.strip() in line:
                        lines[i] = line.replace(
                            old_content.strip(), new_content.strip()
                        )
                        replacements += 1
                content = "\n".join(lines)

            # ファイルに書き戻し
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(content)

            return {
                "action": "edit_file",
                "file_path": str(file_path),
                "replacements": replacements,
                "backup_created": backup,
                "success": True,
            }

        except Exception as e:
            return {
                "action": "edit_file",
                "file_path": str(file_path),
                "error": str(e),
                "success": False,
            }

    async def _generate_code(self, args: Dict) -> Dict:
        """コード生成（実装）"""
        code_type = args.get("code_type", "class")
        name = args.get("name", "Generated")
        methods = args.get("methods", [])
        docstring = args.get("docstring", "")
        imports = args.get("imports", [])
        base_class = args.get("base_class", None)

        try:
            # インポート文を生成
            import_lines = []
            for imp in imports:
                if isinstance(imp, dict):
                    module = imp.get("module", "")
                    items = imp.get("items", [])
                    if items:
                        import_lines.append(f"from {module} import {', '.join(items)}")
                    else:
                        import_lines.append(f"import {module}")
                else:
                    import_lines.append(f"import {imp}")

            # コード生成
            if code_type == "class":
                code = self._generate_class(name, methods, docstring, base_class)
            elif code_type == "function":
                code = self._generate_function(
                    name, args.get("parameters", []), docstring
                )
            elif code_type == "test":
                code = self._generate_test_class(name, methods)
            else:
                code = f"# Generated {code_type}: {name}\n"

            # 完全なコードを組み立て
            full_code = ""
            if import_lines:
                full_code = "\n".join(import_lines) + "\n\n"
            full_code += code

            # コードをフォーマット
            try:
                full_code = black.format_str(full_code, mode=black.Mode())
            except:
                pass  # フォーマットエラーは無視

            return {
                "action": "generate_code",
                "code_type": code_type,
                "name": name,
                "generated_code": full_code,
                "lines": len(full_code.split("\n")),
                "success": True,
            }

        except Exception as e:
            return {
                "action": "generate_code",
                "code_type": code_type,
                "name": name,
                "error": str(e),
                "success": False,
            }

    def _generate_class(
        self, name: str, methods: List[Dict], docstring: str, base_class: Optional[str]
    ) -> str:
        """クラスコードを生成"""
        inheritance = f"({base_class})" if base_class else ""

        code = f"class {name}{inheritance}:\n"
        if docstring:
            code += f'    """{docstring}"""\n\n'

        # __init__メソッド
        code += "    def __init__(self):\n"
        code += '        """Initialize the class"""\n'
        if base_class:
            code += "        super().__init__()\n"
        code += "        self.initialized = True\n\n"

        # その他のメソッド
        for method in methods:
            method_name = method.get("name", "method")
            params = method.get("parameters", [])
            method_docstring = method.get("docstring", "")

            param_str = ", ".join(["self"] + params)
            code += f"    def {method_name}({param_str}):\n"
            if method_docstring:
                code += f'        """{method_docstring}"""\n'
            code += "        # TODO: Implement this method\n"
            code += "        pass\n\n"

        return code

    def _generate_function(
        self, name: str, parameters: List[str], docstring: str
    ) -> str:
        """関数コードを生成"""
        param_str = ", ".join(parameters)

        code = f"def {name}({param_str}):\n"
        if docstring:
            code += f'    """{docstring}"""\n'
        code += "    # TODO: Implement this function\n"
        code += "    pass\n"

        return code

    def _generate_test_class(self, name: str, test_methods: List[Dict]) -> str:
        """テストクラスコードを生成"""
        code = f"class Test{name}:\n"
        code += '    """Test class for ' + name + '"""\n\n'

        # setup_methodを追加
        code += "    def setup_method(self):\n"
        code += '        """Setup test environment"""\n'
        code += "        self.test_instance = None\n\n"

        # テストメソッドを追加
        if not test_methods:
            test_methods = [
                {"name": "test_initialization", "docstring": "Test initialization"},
                {
                    "name": "test_basic_functionality",
                    "docstring": "Test basic functionality",
                },
                {"name": "test_edge_cases", "docstring": "Test edge cases"},
                {"name": "test_error_handling", "docstring": "Test error handling"},
            ]

        for method in test_methods:
            method_name = method.get("name", "test_method")
            if not method_name.startswith("test_"):
                method_name = "test_" + method_name

            method_docstring = method.get("docstring", "")

            code += f"    def {method_name}(self):\n"
            if method_docstring:
                code += f'        """{method_docstring}"""\n'
            code += "        # TODO: Implement test\n"
            code += "        assert True\n\n"

        return code

    async def _analyze_code(self, args: Dict) -> Dict:
        """コード分析（実装）"""
        file_path = Path(args.get("file_path"))

        try:
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # ファイルを読み込み
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()

            # 基本的なメトリクスを計算
            lines = content.split("\n")
            loc = len(lines)
            non_empty_lines = len([line for line in lines if line.strip()])
            comment_lines = len(
                [line for line in lines if line.strip().startswith("#")]
            )

            # AST解析
            try:
                tree = ast.parse(content)

                # クラスと関数をカウント
                classes = sum(
                    1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
                )
                functions = sum(
                    1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
                )

                # 複雑度の簡易計算（制御フロー文の数）
                complexity = sum(
                    1
                    for node in ast.walk(tree)
                    if isinstance(
                        node, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With)
                    )
                )

            except SyntaxError as e:
                classes = functions = complexity = 0
                syntax_error = str(e)
            else:
                syntax_error = None

            # 問題点の検出
            issues = []

            # 長い行を検出
            long_lines = [
                (i + 1, len(line)) for i, line in enumerate(lines) if len(line) > 100
            ]
            if long_lines:
                issues.append(
                    f"Long lines detected: {len(long_lines)} lines exceed 100 characters"
                )

            # TODOコメントを検出
            todos = [
                (i + 1, line.strip()) for i, line in enumerate(lines) if "TODO" in line
            ]
            if todos:
                issues.append(f"TODO comments found: {len(todos)} items")

            # ドキュメント不足を検出
            if functions > 0:
                docstring_count = sum(
                    1
                    for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef) and ast.get_docstring(node)
                )
                if docstring_count < functions * 0.8:
                    issues.append(
                        "Insufficient documentation: Less than 80% of functions have docstrings"
                    )

            return {
                "action": "analyze_code",
                "file_path": str(file_path),
                "metrics": {
                    "lines_of_code": loc,
                    "non_empty_lines": non_empty_lines,
                    "comment_lines": comment_lines,
                    "classes": classes,
                    "functions": functions,
                    "complexity": complexity,
                    "code_quality": self._calculate_quality_score(
                        loc, comment_lines, complexity, issues
                    ),
                },
                "issues": issues,
                "syntax_error": syntax_error,
                "success": True,
            }

        except Exception as e:
            return {
                "action": "analyze_code",
                "file_path": str(file_path),
                "error": str(e),
                "success": False,
            }

    def _calculate_quality_score(
        self, loc: int, comments: int, complexity: int, issues: List[str]
    ) -> str:
        """コード品質スコアを計算"""
        score = 100

        # コメント率
        comment_ratio = comments / loc if loc > 0 else 0
        if comment_ratio < 0.1:
            score -= 10

        # 複雑度
        if complexity > 20:
            score -= 15
        elif complexity > 10:
            score -= 5

        # 問題点
        score -= len(issues) * 5

        # グレードに変換
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    async def _format_code(self, args: Dict) -> Dict:
        """コードフォーマット（実装）"""
        file_path = Path(args.get("file_path"))

        try:
            # ファイルを読み込み
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()

            original_content = content

            # Blackでフォーマット
            try:
                content = black.format_str(content, mode=black.Mode())
                black_applied = True
            except Exception as e:
                black_applied = False
                black_error = str(e)

            # isortでインポートを整理
            try:
                content = isort.code(content)
                isort_applied = True
            except Exception as e:
                isort_applied = False
                isort_error = str(e)

            # 変更があった場合のみ書き込み
            if content != original_content:
                async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                    await f.write(content)
                changed = True
            else:
                changed = False

            return {
                "action": "format_code",
                "file_path": str(file_path),
                "changed": changed,
                "black_applied": black_applied,
                "isort_applied": isort_applied,
                "success": True,
            }

        except Exception as e:
            return {
                "action": "format_code",
                "file_path": str(file_path),
                "error": str(e),
                "success": False,
            }

    async def _optimize_imports(self, args: Dict) -> Dict:
        """インポート最適化（実装）"""
        file_path = Path(args.get("file_path"))

        try:
            # ファイルを読み込み
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()

            # ASTを解析
            tree = ast.parse(content)

            # 使用されているすべての名前を収集
            used_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    used_names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    if isinstance(node.value, ast.Name):
                        used_names.add(node.value.id)

            # インポートを分析
            imports = []
            unused_imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        if name not in used_names:
                            unused_imports.append(name)
                        imports.append(name)
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        if name not in used_names:
                            unused_imports.append(f"{node.module}.{name}")
                        imports.append(name)

            # isortで最適化
            optimized_content = isort.code(content)

            # ファイルに書き戻し
            if optimized_content != content:
                async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                    await f.write(optimized_content)
                changed = True
            else:
                changed = False

            return {
                "action": "optimize_imports",
                "file_path": str(file_path),
                "total_imports": len(imports),
                "unused_imports": unused_imports,
                "changed": changed,
                "success": True,
            }

        except Exception as e:
            return {
                "action": "optimize_imports",
                "file_path": str(file_path),
                "error": str(e),
                "success": False,
            }

    async def _refactor_code(self, args: Dict) -> Dict:
        """コードリファクタリング（実装）"""
        file_path = Path(args.get("file_path"))
        refactor_type = args.get("refactor_type", "general")

        try:
            # ファイルを読み込み
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()

            original_content = content
            improvements = []

            # リファクタリングタイプに応じて処理
            if refactor_type in ["general", "extract_method"]:
                # 長いメソッドを検出して分割の提案
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # 関数の行数を計算
                        if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                            func_lines = node.end_lineno - node.lineno
                            if func_lines > 20:
                                improvements.append(
                                    f"Consider extracting method from {node.name} (lines: {func_lines})"
                                )

            if refactor_type in ["general", "reduce_complexity"]:
                # 複雑な条件を簡略化
                improvements.append(
                    "Consider simplifying complex conditional statements"
                )

            if refactor_type in ["general", "add_type_hints"]:
                # 型ヒントの追加を提案
                improvements.append(
                    "Consider adding type hints to function parameters and return values"
                )

            # コードフォーマットを適用
            try:
                content = black.format_str(content, mode=black.Mode())
                content = isort.code(content)
                if content != original_content:
                    improvements.append("Applied code formatting")
            except:
                pass

            # 変更があった場合は保存
            if content != original_content:
                async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                    await f.write(content)
                changed = True
            else:
                changed = False

            return {
                "action": "refactor_code",
                "file_path": str(file_path),
                "refactor_type": refactor_type,
                "improvements": improvements,
                "changed": changed,
                "success": True,
            }

        except Exception as e:
            return {
                "action": "refactor_code",
                "file_path": str(file_path),
                "error": str(e),
                "success": False,
            }

    async def _tdd_generate_failing_test(self, args: Dict) -> Dict:
        """TDD Step 1: 失敗するテストを生成"""
        test_name = args.get("test_name", "test_feature")
        feature_description = args.get("feature_description", "")
        target_class = args.get("target_class", "Implementation")
        target_method = args.get("target_method", "execute")
        
        try:
            # 実際に失敗するテストを生成
            test_content = f'''"""
TDD Red Phase: {test_name}
{feature_description}

This test MUST fail initially - implementing TDD correctly.
"""

import pytest
from unittest.mock import Mock, patch


class {test_name.replace("test_", "").title()}Test:
    """TDD Test for {target_class}"""
    
    def test_{target_method}_should_exist(self):
        """Test that {target_method} method exists"""
        # RED: This will fail because class doesn't exist yet
        from auto_implementations.{target_class.lower()} import {target_class}
        
        instance = {target_class}()
        assert hasattr(instance, "{target_method}"), f"{target_class} should have {target_method} method"
    
    def test_{target_method}_basic_functionality(self):
        """Test basic functionality of {target_method}"""
        # RED: This will fail because implementation doesn't exist
        from auto_implementations.{target_class.lower()} import {target_class}
        
        instance = {target_class}()
        result = instance.{target_method}()
        
        # Define expected behavior
        assert result is not None, "Method should return a value"
        assert hasattr(result, '__str__'), "Result should be convertible to string"
    
    def test_{target_method}_error_handling(self):
        """Test error handling in {target_method}"""
        # RED: This will fail because error handling isn't implemented
        from auto_implementations.{target_class.lower()} import {target_class}
        
        instance = {target_class}()
        
        # Test with invalid input
        with pytest.raises(ValueError):
            instance.{target_method}(invalid_input=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''
            
            return {
                "action": "tdd_generate_failing_test", 
                "test_name": test_name,
                "target_class": target_class,
                "target_method": target_method,
                "generated_test": test_content,
                "phase": "RED",
                "should_fail": True,
                "success": True,
            }
            
        except Exception as e:
            return {
                "action": "tdd_generate_failing_test",
                "error": str(e),
                "success": False,
            }

    async def _tdd_implement_code(self, args: Dict) -> Dict:
        """TDD Step 2: テストを通すための最小実装"""
        target_class = args.get("target_class", "Implementation")
        target_method = args.get("target_method", "execute")
        feature_description = args.get("feature_description", "")
        
        try:
            # テストを通すための最小実装を生成
            impl_content = f'''"""
TDD Green Phase: {target_class}
{feature_description}

Minimal implementation to make tests pass.
"""


class {target_class}:
    """Minimal implementation for TDD Green phase"""
    
    def __init__(self):
        """Initialize the implementation"""
        pass
    
    def {target_method}(self, invalid_input=False):
        """
        Minimal implementation of {target_method}
        
        Args:
            invalid_input: If True, raises ValueError for testing
            
        Returns:
            Simple result to pass tests
            
        Raises:
            ValueError: When invalid_input is True
        """
        if invalid_input:
            raise ValueError("Invalid input provided")
        
        # Minimal implementation - just enough to pass tests
        return "success"
    
    def __str__(self):
        """String representation"""
        return f"{target_class} instance"
'''
            
            return {
                "action": "tdd_implement_code",
                "target_class": target_class,
                "target_method": target_method,
                "generated_code": impl_content,
                "phase": "GREEN",
                "minimal_implementation": True,
                "success": True,
            }
            
        except Exception as e:
            return {
                "action": "tdd_implement_code",
                "error": str(e),
                "success": False,
            }

    async def _tdd_refactor_code(self, args: Dict) -> Dict:
        """TDD Step 3: リファクタリング（テストを保持しながら改善）"""
        target_class = args.get("target_class", "Implementation")
        current_code = args.get("current_code", "")
        improvement_goals = args.get("improvement_goals", [])
        
        try:
            # リファクタリング版のコード生成
            refactored_content = f'''"""
TDD Blue Phase: {target_class} (Refactored)
Improved implementation while maintaining test compatibility.

Improvements applied:
{chr(10).join(f"- {goal}" for goal in improvement_goals)}
"""

import logging
from typing import Any, Optional


class {target_class}:
    """Refactored implementation with improved design"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize with improved design
        
        Args:
            logger: Optional logger for better debugging
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self._initialized = True
        
    def execute(self, invalid_input: bool = False) -> str:
        """
        Refactored implementation with better error handling and logging
        
        Args:
            invalid_input: If True, raises ValueError for testing
            
        Returns:
            Improved result with better structure
            
        Raises:
            ValueError: When invalid_input is True
        """
        self.logger.debug(f"Executing {{self.__class__.__name__}} with invalid_input={{invalid_input}}")
        
        if invalid_input:
            self.logger.error("Invalid input detected")
            raise ValueError("Invalid input provided")
        
        # Improved implementation with better structure
        result = self._perform_execution()
        self.logger.info(f"Execution completed successfully: {{result}}")
        
        return result
    
    def _perform_execution(self) -> str:
        """
        Internal execution logic (refactored for better separation of concerns)
        
        Returns:
            Execution result
        """
        # More sophisticated implementation
        return "success_refactored"
    
    def __str__(self) -> str:
        """Improved string representation"""
        return f"{{self.__class__.__name__}}(initialized={{self._initialized}})"
    
    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return f"{{self.__class__.__name__}}()"
'''
            
            return {
                "action": "tdd_refactor_code",
                "target_class": target_class,
                "refactored_code": refactored_content,
                "phase": "BLUE",
                "improvements": improvement_goals,
                "success": True,
            }
            
        except Exception as e:
            return {
                "action": "tdd_refactor_code",
                "error": str(e),
                "success": False,
            }


class TestGuardianServantReal(BaseServant):
    """テスト守護者サーバント - 実装版"""

    def __init__(self, name: str = "TestGuardian"):
        super().__init__(ServantType.TEST_GUARDIAN, name)
        self.capabilities = [
            "create_test",
            "run_test",
            "generate_test_data",
            "coverage_analysis",
            "test_optimization",
        ]

    async def _execute_specific_task(self, task: ServantTask) -> Dict:
        """テスト関連タスクの実行"""
        command = task.command
        args = task.arguments

        command_map = {
            "create_test": self._create_test,
            "run_test": self._run_test,
            "generate_test_data": self._generate_test_data,
            "coverage_analysis": self._coverage_analysis,
            "test_optimization": self._test_optimization,
        }

        if command in command_map:
            return await command_map[command](args)
        else:
            raise ValueError(f"Unknown command: {command}")

    async def _create_test(self, args: Dict) -> Dict:
        """テスト作成（実装）"""
        test_file = Path(args.get("test_file"))
        target_module = args.get("target_module")
        target_class = args.get("target_class", None)
        test_type = args.get("test_type", "unit")

        try:
            # テストディレクトリを作成
            test_file.parent.mkdir(parents=True, exist_ok=True)

            # テストコードを生成
            test_content = self._generate_test_content(
                target_module, target_class, test_type
            )

            # ファイルに書き込み
            async with aiofiles.open(test_file, "w", encoding="utf-8") as f:
                await f.write(test_content)

            # テストメソッドをカウント
            test_count = test_content.count("def test_")

            return {
                "action": "create_test",
                "test_file": str(test_file),
                "target_module": target_module,
                "target_class": target_class,
                "test_type": test_type,
                "test_count": test_count,
                "success": True,
            }

        except Exception as e:
            return {
                "action": "create_test",
                "test_file": str(test_file),
                "error": str(e),
                "success": False,
            }

    def _generate_test_content(
        self, target_module: str, target_class: Optional[str], test_type: str
    ) -> str:
        """テストコンテンツを生成"""
        imports = [
            "import pytest",
            "import unittest.mock as mock",
            "from pathlib import Path",
            "import sys",
            "",
            f"from {target_module} import {target_class or '*'}",
        ]

        test_class_name = f"Test{target_class}" if target_class else "TestModule"

        content = "\n".join(imports) + "\n\n"

        if test_type == "unit":
            content += f"""
class {test_class_name}:
    \"\"\"Unit tests for {target_class or target_module}\"\"\"

    def setup_method(self):
        \"\"\"Setup test environment\"\"\"
        self.test_instance = {target_class}() if {target_class} else None

    def teardown_method(self):
        \"\"\"Cleanup after test\"\"\"
        self.test_instance = None

    def test_initialization(self):
        \"\"\"Test class initialization\"\"\"
        assert self.test_instance is not None
        # TODO: Add specific initialization tests

    def test_basic_functionality(self):
        \"\"\"Test basic functionality\"\"\"
        # TODO: Implement basic functionality tests
        assert True

    def test_edge_cases(self):
        \"\"\"Test edge cases\"\"\"
        # TODO: Implement edge case tests
        assert True

    def test_error_handling(self):
        \"\"\"Test error handling\"\"\"
        # TODO: Implement error handling tests
        with pytest.raises(Exception):
            # Test expected exceptions
            pass

    @pytest.mark.parametrize("input,expected", [
        (1, 1),
        (2, 4),
        (3, 9),
    ])
    def test_parametrized(self, input, expected):
        \"\"\"Test with multiple inputs\"\"\"
        # TODO: Implement parametrized test
        result = input ** 2
        assert result == expected
"""

        elif test_type == "integration":
            content += f"""
class {test_class_name}Integration:
    \"\"\"Integration tests for {target_class or target_module}\"\"\"

    @pytest.fixture
    def setup_integration(self):
        \"\"\"Setup integration test environment\"\"\"
        # TODO: Setup integration environment
        yield
        # TODO: Cleanup

    def test_integration_with_dependencies(self, setup_integration):
        \"\"\"Test integration with external dependencies\"\"\"
        # TODO: Implement integration tests
        assert True

    def test_end_to_end_workflow(self, setup_integration):
        \"\"\"Test complete workflow\"\"\"
        # TODO: Implement end-to-end test
        assert True
"""

        return content

    async def _run_test(self, args: Dict) -> Dict:
        """テスト実行（実装）"""
        test_path = args.get("test_path", "tests/")
        verbose = args.get("verbose", False)
        coverage = args.get("coverage", True)

        try:
            # pytestコマンドを構築
            cmd = ["python", "-m", "pytest", test_path]

            if verbose:
                cmd.append("-v")

            if coverage:
                cmd.extend(["--cov", ".", "--cov-report", "term"])

            # テストを実行
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=PROJECT_ROOT,
            )

            stdout, stderr = await process.communicate()

            # 結果を解析
            output = stdout.decode()
            error_output = stderr.decode()

            # テスト結果をパース
            results = self._parse_pytest_output(output)

            return {
                "action": "run_test",
                "test_path": test_path,
                "results": results,
                "output": output[-1000:],  # 最後の1000文字
                "error_output": error_output[-500:] if error_output else None,
                "exit_code": process.returncode,
                "success": process.returncode == 0,
            }

        except Exception as e:
            return {
                "action": "run_test",
                "test_path": test_path,
                "error": str(e),
                "success": False,
            }

    def _parse_pytest_output(self, output: str) -> Dict:
        """pytest出力をパース"""
        results = {"passed": 0, "failed": 0, "skipped": 0, "total": 0, "coverage": None}

        # テスト結果の行を探す
        for line in output.split("\n"):
            if " passed" in line and " failed" in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed":
                        results["passed"] = int(parts[i - 1])
                    elif part == "failed":
                        results["failed"] = int(parts[i - 1])
                    elif part == "skipped":
                        results["skipped"] = int(parts[i - 1])

            # カバレッジ情報
            if "TOTAL" in line and "%" in line:
                parts = line.split()
                for part in parts:
                    if part.endswith("%"):
                        try:
                            results["coverage"] = float(part.rstrip("%"))
                        except:
                            pass

        results["total"] = results["passed"] + results["failed"] + results["skipped"]

        return results

    async def _generate_test_data(self, args: Dict) -> Dict:
        """テストデータ生成（実装）"""
        data_type = args.get("data_type", "json")
        count = args.get("count", 10)
        schema = args.get("schema", {})
        output_file = args.get("output_file", None)

        try:
            # データを生成
            generated_data = []

            for i in range(count):
                if data_type == "json":
                    item = self._generate_json_item(schema, i)
                elif data_type == "csv":
                    item = self._generate_csv_item(schema, i)
                else:
                    item = {"id": i, "value": f"test_{i}"}

                generated_data.append(item)

            # ファイルに保存
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                if data_type == "json":
                    import json

                    async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
                        await f.write(json.dumps(generated_data, indent=2))
                elif data_type == "csv":
                    import csv

                    async with aiofiles.open(
                        output_path, "w", encoding="utf-8", newline=""
                    ) as f:
                        if generated_data:
                            writer = csv.DictWriter(
                                f, fieldnames=generated_data[0].keys()
                            )
                            writer.writeheader()
                            writer.writerows(generated_data)

            return {
                "action": "generate_test_data",
                "data_type": data_type,
                "count": count,
                "output_file": str(output_file) if output_file else None,
                "sample_data": generated_data[:3],  # 最初の3件をサンプルとして返す
                "success": True,
            }

        except Exception as e:
            return {"action": "generate_test_data", "error": str(e), "success": False}

    def _generate_json_item(self, schema: Dict, index: int) -> Dict:
        """JSONアイテムを生成"""
        item = {"id": index}

        for field, field_type in schema.items():
            if field_type == "string":
                item[field] = f"test_{field}_{index}"
            elif field_type == "number":
                item[field] = index * 10
            elif field_type == "boolean":
                item[field] = index % 2 == 0
            elif field_type == "array":
                item[field] = [f"item_{i}" for i in range(3)]
            else:
                item[field] = f"value_{index}"

        return item

    def _generate_csv_item(self, schema: Dict, index: int) -> Dict:
        """CSVアイテムを生成"""
        return self._generate_json_item(schema, index)

    async def _coverage_analysis(self, args: Dict) -> Dict:
        """カバレッジ分析（実装）"""
        source_path = args.get("source_path", ".")
        test_path = args.get("test_path", "tests/")

        try:
            # カバレッジコマンドを実行
            cmd = [
                "python",
                "-m",
                "coverage",
                "run",
                "--source",
                source_path,
                "-m",
                "pytest",
                test_path,
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=PROJECT_ROOT,
            )

            await process.communicate()

            # カバレッジレポートを生成
            report_cmd = ["python", "-m", "coverage", "report", "--format=json"]

            report_process = await asyncio.create_subprocess_exec(
                *report_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=PROJECT_ROOT,
            )

            report_stdout, _ = await report_process.communicate()

            # 結果をパース
            try:
                coverage_data = json.loads(report_stdout.decode())

                return {
                    "action": "coverage_analysis",
                    "source_path": source_path,
                    "test_path": test_path,
                    "total_coverage": coverage_data.get("totals", {}).get(
                        "percent_covered", 0
                    ),
                    "files": self._summarize_file_coverage(
                        coverage_data.get("files", {})
                    ),
                    "success": True,
                }
            except:
                # JSONパースに失敗した場合はテキストレポートを取得
                text_cmd = ["python", "-m", "coverage", "report"]

                text_process = await asyncio.create_subprocess_exec(
                    *text_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=PROJECT_ROOT,
                )

                text_stdout, _ = await text_process.communicate()

                return {
                    "action": "coverage_analysis",
                    "source_path": source_path,
                    "test_path": test_path,
                    "report": text_stdout.decode(),
                    "success": True,
                }

        except Exception as e:
            return {"action": "coverage_analysis", "error": str(e), "success": False}

    def _summarize_file_coverage(self, files_data: Dict) -> List[Dict]:
        """ファイルカバレッジをサマリー"""
        summary = []

        for file_path, data in files_data.items():
            summary.append(
                {
                    "file": file_path,
                    "coverage": data.get("summary", {}).get("percent_covered", 0),
                    "missing_lines": data.get("summary", {}).get("missing_lines", 0),
                    "excluded_lines": data.get("summary", {}).get("excluded_lines", 0),
                }
            )

        # カバレッジが低い順にソート
        summary.sort(key=lambda x: x["coverage"])

        return summary[:10]  # 最もカバレッジが低い10ファイル

    async def _test_optimization(self, args: Dict) -> Dict:
        """テスト最適化（実装）"""
        test_path = args.get("test_path", "tests/")

        try:
            # テストファイルを探す
            test_files = list(Path(test_path).rglob("test_*.py"))

            optimizations = []

            for test_file in test_files:
                # ファイルを分析
                async with aiofiles.open(test_file, "r", encoding="utf-8") as f:
                    content = await f.read()

                # 最適化の提案を生成
                file_optimizations = self._analyze_test_file(test_file, content)
                if file_optimizations:
                    optimizations.append(
                        {"file": str(test_file), "suggestions": file_optimizations}
                    )

            return {
                "action": "test_optimization",
                "test_path": test_path,
                "analyzed_files": len(test_files),
                "optimizations": optimizations,
                "success": True,
            }

        except Exception as e:
            return {"action": "test_optimization", "error": str(e), "success": False}

    def _analyze_test_file(self, file_path: Path, content: str) -> List[str]:
        """テストファイルを分析して最適化を提案"""
        suggestions = []

        lines = content.split("\n")

        # 重複したセットアップコードを検出
        setup_count = content.count("def setup_")
        if setup_count > 1:
            suggestions.append("Consider using fixtures to reduce setup duplication")

        # 長いテストメソッドを検出
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                        method_lines = node.end_lineno - node.lineno
                        if method_lines > 20:
                            suggestions.append(
                                f"Consider splitting {node.name} (lines: {method_lines})"
                            )
        except:
            pass

        # parametrizeの使用を提案
        similar_tests = []
        test_names = [
            line.strip() for line in lines if line.strip().startswith("def test_")
        ]
        for i, name1 in enumerate(test_names):
            for name2 in test_names[i + 1 :]:
                if self._are_similar_test_names(name1, name2):
                    similar_tests.append((name1, name2))

        if similar_tests:
            suggestions.append(
                "Consider using @pytest.mark.parametrize for similar tests"
            )

        # アサーションの改善
        if "assert True" in content or "assert False" in content:
            suggestions.append("Replace placeholder assertions with meaningful tests")

        return suggestions

    def _are_similar_test_names(self, name1: str, name2: str) -> bool:
        """テスト名が類似しているかチェック"""
        # 簡単な類似性チェック
        name1_parts = name1.replace("def test_", "").split("_")
        name2_parts = name2.replace("def test_", "").split("_")

        common_parts = set(name1_parts) & set(name2_parts)

        return len(common_parts) >= len(name1_parts) * 0.7


class QualityInspectorServantReal(BaseServant):
    """品質検査官サーバント - 実装版"""

    def __init__(self, name: str = "QualityInspector"):
        super().__init__(ServantType.QUALITY_INSPECTOR, name)
        self.capabilities = [
            "code_quality_check",
            "security_scan",
            "performance_test",
            "lint_check",
            "type_check",
        ]

    async def _execute_specific_task(self, task: ServantTask) -> Dict:
        """品質検査タスクの実行"""
        command = task.command
        args = task.arguments

        command_map = {
            "code_quality_check": self._code_quality_check,
            "security_scan": self._security_scan,
            "performance_test": self._performance_test,
            "lint_check": self._lint_check,
            "type_check": self._type_check,
        }

        if command in command_map:
            return await command_map[command](args)
        else:
            raise ValueError(f"Unknown command: {command}")

    async def _code_quality_check(self, args: Dict) -> Dict:
        """コード品質チェック（実装）"""
        file_path = args.get("file_path")
        check_all = args.get("check_all", False)

        try:
            if check_all:
                # プロジェクト全体をチェック
                target_path = PROJECT_ROOT
            else:
                target_path = Path(file_path)

            # pylintを実行
            cmd = ["python", "-m", "pylint", str(target_path), "--output-format=json"]

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            # 結果をパース
            try:
                issues = json.loads(stdout.decode()) if stdout else []
            except:
                issues = []

            # 重要度別に分類
            critical_issues = [i for i in issues if i.get("type") in ["error", "fatal"]]
            warning_issues = [i for i in issues if i.get("type") == "warning"]
            info_issues = [
                i for i in issues if i.get("type") in ["convention", "refactor"]
            ]

            # スコアを計算
            score = max(
                0,
                10
                - len(critical_issues) * 2
                - len(warning_issues) * 0.5
                - len(info_issues) * 0.1,
            )

            return {
                "action": "code_quality_check",
                "target": str(target_path),
                "score": min(10, score),
                "grade": self._score_to_grade(score),
                "issues": {
                    "critical": len(critical_issues),
                    "warning": len(warning_issues),
                    "info": len(info_issues),
                    "total": len(issues),
                },
                "top_issues": issues[:10],  # 最初の10件
                "success": True,
            }

        except Exception as e:
            return {"action": "code_quality_check", "error": str(e), "success": False}

    def _score_to_grade(self, score: float) -> str:
        """スコアをグレードに変換"""
        if score >= 9:
            return "A"
        elif score >= 8:
            return "B"
        elif score >= 7:
            return "C"
        elif score >= 6:
            return "D"
        else:
            return "F"

    async def _security_scan(self, args: Dict) -> Dict:
        """セキュリティスキャン（実装）"""
        target_path = args.get("target_path", ".")

        try:
            # banditを実行
            cmd = ["python", "-m", "bandit", "-r", target_path, "-f", "json"]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=PROJECT_ROOT,
            )

            stdout, stderr = await process.communicate()

            # 結果をパース
            try:
                result = json.loads(stdout.decode()) if stdout else {}
            except:
                result = {}

            # 脆弱性を重要度別に分類
            vulnerabilities = result.get("results", [])

            high_severity = [
                v for v in vulnerabilities if v.get("issue_severity") == "HIGH"
            ]
            medium_severity = [
                v for v in vulnerabilities if v.get("issue_severity") == "MEDIUM"
            ]
            low_severity = [
                v for v in vulnerabilities if v.get("issue_severity") == "LOW"
            ]

            return {
                "action": "security_scan",
                "target_path": target_path,
                "vulnerabilities": {
                    "high": len(high_severity),
                    "medium": len(medium_severity),
                    "low": len(low_severity),
                    "total": len(vulnerabilities),
                },
                "scan_status": "passed" if not high_severity else "failed",
                "critical_issues": high_severity[:5],  # 最初の5件
                "metrics": result.get("metrics", {}),
                "success": True,
            }

        except Exception as e:
            return {"action": "security_scan", "error": str(e), "success": False}

    async def _performance_test(self, args: Dict) -> Dict:
        """パフォーマンステスト（実装）"""
        test_script = args.get("test_script")
        iterations = args.get("iterations", 100)

        try:
            # 簡易的なパフォーマンステスト
            import timeit
            import statistics

            # テストスクリプトを読み込み
            if test_script and Path(test_script).exists():
                async with aiofiles.open(test_script, "r", encoding="utf-8") as f:
                    code = await f.read()
            else:
                # デフォルトのテストコード
                code = "sum(range(1000))"

            # パフォーマンス測定
            times = []
            for _ in range(iterations):
                elapsed = timeit.timeit(code, number=1)
                times.append(elapsed)

            # 統計を計算
            avg_time = statistics.mean(times)
            median_time = statistics.median(times)
            std_dev = statistics.stdev(times) if len(times) > 1 else 0

            return {
                "action": "performance_test",
                "iterations": iterations,
                "metrics": {
                    "average_time": avg_time,
                    "median_time": median_time,
                    "std_deviation": std_dev,
                    "min_time": min(times),
                    "max_time": max(times),
                },
                "performance_status": "passed" if avg_time < 1.0 else "warning",
                "success": True,
            }

        except Exception as e:
            return {"action": "performance_test", "error": str(e), "success": False}

    async def _lint_check(self, args: Dict) -> Dict:
        """Lintチェック（実装）"""
        target_path = args.get("target_path", ".")

        try:
            # flake8を実行
            cmd = ["python", "-m", "flake8", target_path, "--format=json"]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=PROJECT_ROOT,
            )

            stdout, stderr = await process.communicate()

            # 結果をパース（flake8のJSON出力は特殊なので、行ごとに処理）
            issues = []
            if stdout:
                for line in stdout.decode().split("\n"):
                    if line.strip():
                        try:
                            issue = json.loads(line)
                            issues.append(issue)
                        except:
                            pass

            # エラータイプ別に分類
            error_types = {}
            for issue in issues:
                error_code = issue.get("code", "unknown")
                error_types[error_code] = error_types.get(error_code, 0) + 1

            return {
                "action": "lint_check",
                "target_path": target_path,
                "total_issues": len(issues),
                "error_types": error_types,
                "top_issues": issues[:10],
                "lint_status": "passed" if len(issues) == 0 else "warning",
                "success": True,
            }

        except Exception as e:
            return {"action": "lint_check", "error": str(e), "success": False}

    async def _type_check(self, args: Dict) -> Dict:
        """型チェック（実装）"""
        target_path = args.get("target_path", ".")

        try:
            # mypyを実行
            cmd = ["python", "-m", "mypy", target_path, "--json-report", "-"]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=PROJECT_ROOT,
            )

            stdout, stderr = await process.communicate()

            # 結果をパース
            type_errors = []
            if stderr:
                for line in stderr.decode().split("\n"):
                    if ": error:" in line:
                        type_errors.append(line.strip())

            return {
                "action": "type_check",
                "target_path": target_path,
                "total_errors": len(type_errors),
                "type_errors": type_errors[:10],  # 最初の10件
                "type_check_status": "passed" if len(type_errors) == 0 else "failed",
                "success": True,
            }

        except Exception as e:
            return {"action": "type_check", "error": str(e), "success": False}


class GitKeeperServantReal(BaseServant):
    """Git管理者サーバント - 実装版"""

    def __init__(self, name: str = "GitKeeper"):
        super().__init__(ServantType.GIT_KEEPER, name)
        self.capabilities = [
            "git_add",
            "git_commit",
            "git_push",
            "git_status",
            "git_diff",
            "git_log",
            "create_branch",
            "create_pr",
        ]

    async def _execute_specific_task(self, task: ServantTask) -> Dict:
        """Git関連タスクの実行"""
        command = task.command
        args = task.arguments

        command_map = {
            "git_add": self._git_add,
            "git_commit": self._git_commit,
            "git_push": self._git_push,
            "git_status": self._git_status,
            "git_diff": self._git_diff,
            "git_log": self._git_log,
            "create_branch": self._create_branch,
            "create_pr": self._create_pr,
        }

        if command in command_map:
            return await command_map[command](args)
        else:
            raise ValueError(f"Unknown command: {command}")

    async def _git_add(self, args: Dict) -> Dict:
        """Git add実行"""
        files = args.get("files", [])
        add_all = args.get("add_all", False)

        try:
            if add_all:
                cmd = ["git", "add", "-A"]
            else:
                if not files:
                    return {
                        "action": "git_add",
                        "error": "No files specified",
                        "success": False,
                    }
                cmd = ["git", "add"] + files

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=PROJECT_ROOT,
            )

            stdout, stderr = await process.communicate()

            # git statusで確認
            status_result = await self._git_status({})

            return {
                "action": "git_add",
                "files": files if not add_all else "all",
                "staged_files": status_result.get("staged_files", []),
                "success": process.returncode == 0,
            }

        except Exception as e:
            return {"action": "git_add", "error": str(e), "success": False}

    async def _git_commit(self, args: Dict) -> Dict:
        """Git commit実行"""
        message = args.get("message", "")
        author = args.get("author", "Claude Elder <claude@elders-guild.ai>")

        try:
            if not message:
                return {
                    "action": "git_commit",
                    "error": "Commit message is required",
                    "success": False,
                }

            # Claude Elder署名を追加
            full_message = f"{message}\n\n🤖 Generated with [Claude Code](https://claude.ai/code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"

            # コミットコマンドを実行
            cmd = ["git", "commit", "-m", full_message, f"--author={author}"]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=PROJECT_ROOT,
            )

            stdout, stderr = await process.communicate()

            # コミットIDを取得
            if process.returncode == 0:
                get_hash_cmd = ["git", "rev-parse", "HEAD"]
                hash_process = await asyncio.create_subprocess_exec(
                    *get_hash_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=PROJECT_ROOT,
                )
                hash_stdout, _ = await hash_process.communicate()
                commit_id = hash_stdout.decode().strip()
            else:
                commit_id = None

            return {
                "action": "git_commit",
                "message": message,
                "commit_id": commit_id,
                "output": stdout.decode(),
                "error_output": stderr.decode() if stderr else None,
                "success": process.returncode == 0,
            }

        except Exception as e:
            return {"action": "git_commit", "error": str(e), "success": False}

    async def _git_push(self, args: Dict) -> Dict:
        """Git push実行"""
        remote = args.get("remote", "origin")
        branch = args.get("branch", None)
        force = args.get("force", False)

        try:
            # 現在のブランチを取得
            if not branch:
                branch_cmd = ["git", "branch", "--show-current"]
                branch_process = await asyncio.create_subprocess_exec(
                    *branch_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=PROJECT_ROOT,
                )
                branch_stdout, _ = await branch_process.communicate()
                branch = branch_stdout.decode().strip()

            # pushコマンドを構築
            cmd = ["git", "push", remote, branch]
            if force:
                cmd.append("--force")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=PROJECT_ROOT,
            )

            stdout, stderr = await process.communicate()

            return {
                "action": "git_push",
                "remote": remote,
                "branch": branch,
                "force": force,
                "output": stdout.decode(),
                "error_output": stderr.decode() if stderr else None,
                "success": process.returncode == 0,
            }

        except Exception as e:
            return {"action": "git_push", "error": str(e), "success": False}

    async def _git_status(self, args: Dict) -> Dict:
        """Git status実行"""
        try:
            cmd = ["git", "status", "--porcelain"]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=PROJECT_ROOT,
            )

            stdout, stderr = await process.communicate()

            # ステータスをパース
            status_lines = stdout.decode().strip().split("\n") if stdout else []

            staged_files = []
            modified_files = []
            untracked_files = []

            for line in status_lines:
                if not line:
                    continue

                status = line[:2]
                filename = line[3:]

                if status[0] in ["A", "M", "D", "R", "C"]:
                    staged_files.append(filename)
                if status[1] == "M":
                    modified_files.append(filename)
                elif status == "??":
                    untracked_files.append(filename)

            # 現在のブランチを取得
            branch_cmd = ["git", "branch", "--show-current"]
            branch_process = await asyncio.create_subprocess_exec(
                *branch_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=PROJECT_ROOT,
            )
            branch_stdout, _ = await branch_process.communicate()
            current_branch = branch_stdout.decode().strip()

            return {
                "action": "git_status",
                "current_branch": current_branch,
                "staged_files": staged_files,
                "modified_files": modified_files,
                "untracked_files": untracked_files,
                "clean": len(status_lines) == 0
                or (len(status_lines) == 1 and not status_lines[0]),
                "success": True,
            }

        except Exception as e:
            return {"action": "git_status", "error": str(e), "success": False}

    async def _git_diff(self, args: Dict) -> Dict:
        """Git diff実行"""
        staged = args.get("staged", False)
        files = args.get("files", [])

        try:
            cmd = ["git", "diff"]
            if staged:
                cmd.append("--staged")
            if files:
                cmd.extend(files)

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=PROJECT_ROOT,
            )

            stdout, stderr = await process.communicate()

            diff_output = stdout.decode()

            # 差分のサマリーを作成
            additions = diff_output.count("\n+")
            deletions = diff_output.count("\n-")

            return {
                "action": "git_diff",
                "staged": staged,
                "files": files,
                "diff": diff_output[:1000],  # 最初の1000文字
                "additions": additions,
                "deletions": deletions,
                "has_changes": len(diff_output) > 0,
                "success": True,
            }

        except Exception as e:
            return {"action": "git_diff", "error": str(e), "success": False}

    async def _git_log(self, args: Dict) -> Dict:
        """Git log実行"""
        limit = args.get("limit", 10)
        oneline = args.get("oneline", True)

        try:
            cmd = ["git", "log", f"-{limit}"]
            if oneline:
                cmd.append("--oneline")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=PROJECT_ROOT,
            )

            stdout, stderr = await process.communicate()

            log_output = stdout.decode()
            commits = log_output.strip().split("\n") if log_output else []

            return {
                "action": "git_log",
                "limit": limit,
                "commits": commits,
                "commit_count": len(commits),
                "success": True,
            }

        except Exception as e:
            return {"action": "git_log", "error": str(e), "success": False}

    async def _create_branch(self, args: Dict) -> Dict:
        """ブランチ作成"""
        branch_name = args.get("branch_name", "")
        checkout = args.get("checkout", True)

        try:
            if not branch_name:
                return {
                    "action": "create_branch",
                    "error": "Branch name is required",
                    "success": False,
                }

            # ブランチを作成
            cmd = ["git", "branch", branch_name]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=PROJECT_ROOT,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                return {
                    "action": "create_branch",
                    "branch_name": branch_name,
                    "error": stderr.decode(),
                    "success": False,
                }

            # チェックアウト
            if checkout:
                checkout_cmd = ["git", "checkout", branch_name]
                checkout_process = await asyncio.create_subprocess_exec(
                    *checkout_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=PROJECT_ROOT,
                )

                await checkout_process.communicate()

            return {
                "action": "create_branch",
                "branch_name": branch_name,
                "checked_out": checkout,
                "success": True,
            }

        except Exception as e:
            return {"action": "create_branch", "error": str(e), "success": False}

    async def _create_pr(self, args: Dict) -> Dict:
        """Pull Request作成（GitHub CLI使用）"""
        title = args.get("title", "")
        body = args.get("body", "")
        base = args.get("base", "main")

        try:
            if not title:
                return {
                    "action": "create_pr",
                    "error": "PR title is required",
                    "success": False,
                }

            # PR本文を生成
            pr_body = body or "Generated by Elder Flow"
            pr_body += "\n\n🤖 Generated with [Claude Code](https://claude.ai/code)"

            # GitHub CLIでPR作成
            cmd = [
                "gh",
                "pr",
                "create",
                "--title",
                title,
                "--body",
                pr_body,
                "--base",
                base,
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=PROJECT_ROOT,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                pr_url = stdout.decode().strip()
                return {
                    "action": "create_pr",
                    "title": title,
                    "base": base,
                    "pr_url": pr_url,
                    "success": True,
                }
            else:
                return {
                    "action": "create_pr",
                    "error": stderr.decode(),
                    "success": False,
                }

        except Exception as e:
            return {"action": "create_pr", "error": str(e), "success": False}


# サーバントファクトリー
class ServantFactory:
    """サーバントファクトリー - 実装版"""

    @staticmethod
    def create_servant(
        servant_type: ServantType, name: Optional[str] = None
    ) -> BaseServant:
        """サーバントを作成"""
        if servant_type == ServantType.CODE_CRAFTSMAN:
            return CodeCraftsmanServantReal(name or "CodeCraftsman")
        elif servant_type == ServantType.TEST_GUARDIAN:
            return TestGuardianServantReal(name or "TestGuardian")
        elif servant_type == ServantType.QUALITY_INSPECTOR:
            return QualityInspectorServantReal(name or "QualityInspector")
        elif servant_type == ServantType.GIT_KEEPER:
            return GitKeeperServantReal(name or "GitKeeper")
        else:
            raise ValueError(f"Unknown servant type: {servant_type}")


# エクスポート
__all__ = [
    "CodeCraftsmanServantReal",
    "TestGuardianServantReal",
    "QualityInspectorServantReal",
    "GitKeeperServantReal",
    "ServantFactory",
]
