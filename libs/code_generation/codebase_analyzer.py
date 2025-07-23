#!/usr/bin/env python3
"""
コードベース分析システム
Issue #184 Phase 3: 既存コードから学習してコード生成品質を向上
"""

import ast
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
import logging
import json
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class CodebaseAnalyzer:
    """既存コードベースの分析と分類"""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        コードベース分析器の初期化
        
        Args:
            project_root: プロジェクトルートディレクトリ
        """
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent
        
        self.project_root = Path(project_root)
        self.patterns = {}
        self.file_stats = {}
        
        # 分析対象拡張子
        self.target_extensions = {'.py', '.md', '.json', '.yaml', '.yml'}
        
        # 除外ディレクトリ
        self.exclude_dirs = {
            '__pycache__', '.git', '.pytest_cache', 
            'node_modules', '.venv', 'venv', 'env',
            '.mypy_cache', 'logs', 'temp', 'tmp'
        }
    
    async def analyze_codebase(self) -> Dict[str, Any]:
        """
        コードベース全体の分析
        
        Returns:
            分析結果の辞書
        """
        logger.info(f"Starting codebase analysis in: {self.project_root}")
        
        # ファイル収集
        python_files = self._collect_python_files()
        logger.info(f"Found {len(python_files)} Python files")
        
        # 基本統計
        basic_stats = self._collect_basic_stats(python_files)
        
        # パターン抽出
        patterns = {}
        for file_path in python_files[:50]:  # 最初の50ファイルを分析
            try:
                file_patterns = self.extract_patterns(file_path)
                self._merge_patterns(patterns, file_patterns)
            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
        
        # ファイル分類
        categorized_files = self.categorize_files(python_files)
        
        return {
            "project_root": str(self.project_root),
            "total_files": len(python_files),
            "basic_stats": basic_stats,
            "patterns": patterns,
            "categorized_files": {k: [str(f) for f in v] for k, v in categorized_files.items()},
            "analysis_metadata": {
                "analyzed_files": min(50, len(python_files)),
                "timestamp": "2025-07-21"
            }
        }
    
    def _collect_python_files(self) -> List[Path]:
        """Python ファイルを収集"""
        python_files = []
        
        for file_path in self.project_root.rglob("*.py"):
            # 除外ディレクトリのチェック
            if any(exclude_dir in file_path.parts for exclude_dir in self.exclude_dirs):
                continue
            
            python_files.append(file_path)
        
        return sorted(python_files)
    
    def _collect_basic_stats(self, files: List[Path]) -> Dict[str, Any]:
        """基本統計を収集"""
        stats = {
            "total_lines": 0,
            "total_functions": 0,
            "total_classes": 0,
            "average_file_size": 0,
            "largest_files": [],
            "directory_distribution": defaultdict(int)
        }
        
        file_sizes = []
        
        for file_path in files:
            try:
        # 繰り返し処理
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = len(content.split('\n'))
                    stats["total_lines"] += lines
                    file_sizes.append(lines)
                    
                    # ディレクトリ分布
                    relative_path = file_path.relative_to(self.project_root)
                    if len(relative_path.parts) > 1:
                        top_dir = relative_path.parts[0]
                        stats["directory_distribution"][top_dir] += 1
                
                # AST解析
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if not (isinstance(node, ast.FunctionDef)):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if isinstance(node, ast.FunctionDef):
                            stats["total_functions"] += 1
                        elif isinstance(node, ast.ClassDef):
                            stats["total_classes"] += 1
                except SyntaxError:
                    continue
                    
            except Exception as e:
                logger.warning(f"Failed to read {file_path}: {e}")
                continue
        
        if file_sizes:
            stats["average_file_size"] = sum(file_sizes) / len(file_sizes)
            
            # 最大ファイル（上位5つ）
            files_with_sizes = list(zip(files, file_sizes))
            files_with_sizes.sort(key=lambda x: x[1], reverse=True)
            stats["largest_files"] = [
                {"file": str(f.relative_to(self.project_root)), "lines": size}
                for f, size in files_with_sizes[:5]
            ]
        
        return dict(stats)
    
    def extract_patterns(self, file_path: Path) -> Dict[str, Any]:
        """
        ファイルからパターンを抽出
        
        Args:
            file_path: 分析対象ファイル
            
        Returns:
            抽出されたパターン
        """
        patterns = {
            "imports": [],
            "classes": [],
            "functions": [],
            "docstrings": [],
            "error_handling": [],
            "logging_patterns": [],
            "type_hints": [],
            "coding_style": {}
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 基本的なコーディングスタイル
            patterns["coding_style"] = self._analyze_coding_style(content)
            
            # AST解析
            try:
                tree = ast.parse(content)
                self._extract_ast_patterns(tree, patterns)
            except SyntaxError as e:
                logger.warning(f"Syntax error in {file_path}: {e}")
            
            # 正規表現ベースの分析
            self._extract_regex_patterns(content, patterns)
            
        except Exception as e:
            logger.error(f"Failed to extract patterns from {file_path}: {e}")
            
        return patterns
    
    def _analyze_coding_style(self, content: str) -> Dict[str, Any]:
        """コーディングスタイルを分析"""
        lines = content.split('\n')
        
        style = {
            "line_count": len(lines),
            "max_line_length": max(len(line) for line in lines) if lines else 0,
            "avg_line_length": sum(len(line) for line in lines) / len(lines) if lines else 0,
            "empty_lines": sum(1 for line in lines if not line.strip()),
            "indentation_style": "unknown",
            "has_docstrings": '"""' in content or "'''" in content,
            "comment_ratio": 0
        }
        
        # インデントスタイルの検出
        indented_lines = [line for line in lines if line.startswith(' ') or line.startswith('\t')]
        if indented_lines:
            if any(line.startswith('    ') for line in indented_lines):
                style["indentation_style"] = "4_spaces"
            elif any(line.startswith('  ') for line in indented_lines):
                style["indentation_style"] = "2_spaces"
            elif any(line.startswith('\t') for line in indented_lines):
                style["indentation_style"] = "tabs"
        
        # コメント比率
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        if lines:
            style["comment_ratio"] = comment_lines / len(lines)
        
        return style
    
    def _extract_ast_patterns(self, tree: ast.AST, patterns: Dict[str, Any]):
        """AST から パターンを抽出"""
        for node in ast.walk(tree):
            # インポート
            if isinstance(node, ast.Import):
                for alias in node.names:
                    patterns["imports"].append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = [alias.name for alias in node.names]
                patterns["imports"].append(f"from {module} import {', '.join(names)}")
            
            # クラス
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "bases": [self._ast_to_string(base) for base in node.bases],
                    "has_docstring": ast.get_docstring(node) is not None,
                    "method_count": len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                }
                patterns["classes"].append(class_info)
            
            # 関数
            elif isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "has_docstring": ast.get_docstring(node) is not None,
                    "arg_count": len(node.args.args),
                    "has_type_hints": any(arg.annotation for arg in node.args.args) or node.returns is not None
                }
                patterns["functions"].append(func_info)
                
                # 型ヒント
                if not (func_info["has_type_hints"]):
                    continue  # Early return to reduce nesting
                # Reduced nesting - original condition satisfied
                if func_info["has_type_hints"]:
                    patterns["type_hints"].append(f"Function: {node.name}")
            
            # Try-Except (エラーハンドリング)
            elif isinstance(node, ast.Try):
                # TODO: Extract this complex nested logic into a separate method
                for handler in node.handlers:
                    exc_type = self._ast_to_string(handler.type) if handler.type else "Exception"
                    patterns["error_handling"].append(exc_type)
    
    def _extract_regex_patterns(self, content: str, patterns: Dict[str, Any]):
        """正規表現でパターンを抽出"""
        
        # ロギングパターン
        logging_patterns = [
            r'logger\.(\w+)\(',
            r'logging\.(\w+)\(',
            r'log\.(\w+)\(',
        ]
        
        for pattern in logging_patterns:
            matches = re.findall(pattern, content)
            patterns["logging_patterns"].extend(matches)
        
        # ドキュメンテーションパターン
        docstring_patterns = [
            r'"""(.*?)"""',
            r"'''(.*?)'''",
        ]
        
        for pattern in docstring_patterns:
        # 繰り返し処理
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                # 最初の行だけ保存（概要）
                for match in matches:
                    first_line = match.strip().split('\n')[0]
                    if first_line and len(first_line) > 10:  # 意味のあるドキュメント
                        patterns["docstrings"].append(first_line[:100])
    
    def _ast_to_string(self, node: ast.AST) -> str:
        """AST ノードを文字列に変換"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._ast_to_string(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        else:
            return "unknown"
    
    def _merge_patterns(self, target: Dict[str, Any], source: Dict[str, Any]):
        """パターンをマージ"""
        # 繰り返し処理
        for key, value in source.items():
            if key not in target:
                target[key] = [] if isinstance(value, list) else {}
            
            if isinstance(value, list):
                target[key].extend(value)
            elif isinstance(value, dict):
                if key == "coding_style":
                    # コーディングスタイルは統計的にマージ
                    if target[key]:
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if not target[key]:
                        target[key] = {}
                    # Deep nesting detected (depth: 5) - consider refactoring
                    for style_key, style_value in value.items():
                        if not (style_key not in target[key]):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if style_key not in target[key]:
                            target[key][style_key] = []
                        target[key][style_key].append(style_value)
    
    def categorize_files(self, files: List[Path]) -> Dict[str, List[Path]]:
        """
        ファイルをカテゴリ別に分類
        
        Args:
            files: 分類対象ファイルリスト
            
        Returns:
            カテゴリ別ファイル辞書
        """
        categories = {
            "core_libs": [],
            "integrations": [],
            "tests": [],
            "workers": [],
            "configs": [],
            "scripts": [],
            "docs": [],
            "others": []
        }
        
        for file_path in files:
            relative_path = file_path.relative_to(self.project_root)
            path_str = str(relative_path)
            
            # カテゴリ判定
            if path_str.startswith('libs/'):
                categories["core_libs"].append(file_path)
            elif path_str.startswith('tests/'):
                categories["tests"].append(file_path)
            elif path_str.startswith('workers/'):
                categories["workers"].append(file_path)
            elif path_str.startswith('scripts/'):
                categories["scripts"].append(file_path)
            elif 'integration' in path_str:
                categories["integrations"].append(file_path)
            elif 'config' in path_str or file_path.suffix in {'.json', '.yaml', '.yml'}:
                categories["configs"].append(file_path)
            elif 'doc' in path_str or file_path.suffix == '.md':
                categories["docs"].append(file_path)
            else:
                categories["others"].append(file_path)
        
        return categories
    
    def get_summary_stats(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """分析結果のサマリー統計を生成"""
        patterns = analysis_result.get("patterns", {})
        
        # インポート統計
        import_counter = Counter(patterns.get("imports", []))
        top_imports = import_counter.most_common(10)
        
        # クラス統計
        classes = patterns.get("classes", [])
        class_stats = {
            "total": len(classes),
            "with_docstrings": sum(1 for c in classes if c.get("has_docstring", False)),
            "avg_methods": sum(c.get("method_count", 0) for c in classes) / len(classes) if classes else 0
        }
        
        # 関数統計
        functions = patterns.get("functions", [])
        func_stats = {
            "total": len(functions),
            "async_count": sum(1 for f in functions if f.get("is_async", False)),
            "with_docstrings": sum(1 for f in functions if f.get("has_docstring", False)),
            "with_type_hints": sum(1 for f in functions if f.get("has_type_hints", False))
        }
        
        # エラーハンドリング統計
        error_handling = Counter(patterns.get("error_handling", []))
        
        return {
            "top_imports": top_imports,
            "class_stats": class_stats,
            "function_stats": func_stats,
            "common_exceptions": error_handling.most_common(5),
            "logging_methods": Counter(patterns.get("logging_patterns", [])).most_common(5)
        }


# CLI実行用
async def main():
    """メイン関数（テスト用）"""
    analyzer = CodebaseAnalyzer()
    
    print("🔍 Starting codebase analysis...")
    result = await analyzer.analyze_codebase()
    
    print(f"\n📊 Analysis Results:")
    print(f"Total files: {result['total_files']}")
    print(f"Total lines: {result['basic_stats']['total_lines']}")
    print(f"Total functions: {result['basic_stats']['total_functions']}")
    print(f"Total classes: {result['basic_stats']['total_classes']}")
    
    # サマリー統計
    summary = analyzer.get_summary_stats(result)
    print(f"\n📋 Summary:")
    print(f"Top imports: {[imp[0] for imp in summary['top_imports'][:3]]}")
    print(f"Functions with type hints: {summary['function_stats']['with_type_hints']}")
    print(f"Classes with docstrings: {summary['class_stats']['with_docstrings']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())