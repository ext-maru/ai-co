#!/usr/bin/env python3
"""
Codebase Analysis Engine
コードベース学習・パターン抽出システム (Phase 3)
"""

import ast
import os
import re
import json
import logging
from collections import defaultdict, Counter
from typing import Dict, Any, List, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ImportPattern:
    """インポートパターン"""
    module: str
    alias: Optional[str]
    from_items: List[str]
    frequency: int
    context: str  # 使用コンテキスト


@dataclass
class ClassPattern:
    """クラスパターン"""
    name: str
    base_classes: List[str]
    methods: List[str]
    attributes: List[str]
    docstring: Optional[str]
    file_path: str
    tech_domain: str


@dataclass
class MethodPattern:
    """メソッドパターン"""
    name: str
    args: List[str]
    return_annotation: Optional[str]
    decorators: List[str]
    is_async: bool
    error_handling: List[str]
    docstring: Optional[str]


@dataclass
class CodebaseIntelligence:
    """コードベース理解結果"""
    import_patterns: List[ImportPattern]
    class_patterns: List[ClassPattern]
    method_patterns: List[MethodPattern]
    tech_domains: Dict[str, float]
    common_error_handling: List[str]
    naming_conventions: Dict[str, str]
    file_structure: Dict[str, List[str]]


class ASTAnalyzer:
    """AST解析エンジン"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _is_external_library_file(self, file_path: str) -> bool:
        """外部ライブラリファイルかどうかを判定"""
        path_str = str(file_path).lower()
        external_indicators = [
            'site-packages', 'dist-packages', 'lib/python',
            'miniconda', 'anaconda', 'virtualenv', 'venv',
            '.tox', '.conda', '__pycache__', '.git'
        ]
        return any(indicator in path_str for indicator in external_indicators)
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Pythonファイルを解析"""
        try:
            # 外部ライブラリファイルの早期除外
            if self._is_external_library_file(file_path):
                self.logger.debug(f"Skipping external library file: {file_path}")
                return self._create_fallback_analysis(file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 大きなファイルのスキップ (>50KB)
            if len(content) > 50000:
                self.logger.debug(f"Skipping large file: {file_path}")
                return self._create_fallback_analysis(file_path)
            
            tree = ast.parse(content)
            analysis = {
                'imports': self._extract_imports(tree),
                'classes': self._extract_classes(tree),
                'functions': self._extract_functions(tree),
                'constants': self._extract_constants(tree),
                'docstring': ast.get_docstring(tree),
                'tech_indicators': self._detect_tech_indicators(content),
                'error_patterns': self._extract_error_patterns(tree)
            }
            
            return analysis
            
        except (SyntaxError, UnicodeDecodeError) as e:
            self.logger.debug(f"Parse error in {file_path}: {e}")
            return self._create_fallback_analysis(file_path)
        except Exception as e:
            self.logger.warning(f"Failed to analyze {file_path}: {e}")
            return self._create_fallback_analysis(file_path)
    
    def _extract_imports(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """インポート文を抽出"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        'type': 'import',
                        'module': alias.name,
                        'alias': alias.asname,
                        'from_module': None
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append({
                        'type': 'from_import',
                        'module': alias.name,
                        'alias': alias.asname,
                        'from_module': module
                    })
        
        return imports
    
    def _extract_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """クラス定義を抽出"""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                attributes = []
                
                # メソッドと属性を抽出
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append({
                            'name': item.name,
                            'is_async': isinstance(item, ast.AsyncFunctionDef),
                            'args': [arg.arg for arg in item.args.args],
                            'decorators': [self._get_decorator_name(dec) for dec in item.decorator_list],
                            'docstring': ast.get_docstring(item),
                            'returns': getattr(item.returns, 'id', None) if item.returns else None
                        })
                    elif isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                attributes.append(target.id)
                
                classes.append({
                    'name': node.name,
                    'base_classes': [self._get_base_name(base) for base in node.bases],
                    'methods': methods,
                    'attributes': attributes,
                    'docstring': ast.get_docstring(node),
                    'decorators': [self._get_decorator_name(dec) for dec in node.decorator_list]
                })
        
        return classes
    
    def _extract_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """関数定義を抽出"""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # クラスメソッドは除外（クラス解析で処理済み）
                if any(isinstance(parent, ast.ClassDef) for parent in ast.walk(tree) 
                       if hasattr(parent, 'body') and node in getattr(parent, 'body', [])):
                    continue
                
                functions.append({
                    'name': node.name,
                    'is_async': isinstance(node, ast.AsyncFunctionDef),
                    'args': [arg.arg for arg in node.args.args],
                    'decorators': [self._get_decorator_name(dec) for dec in node.decorator_list],
                    'docstring': ast.get_docstring(node),
                    'returns': getattr(node.returns, 'id', None) if node.returns else None,
                    'error_handling': self._extract_function_error_handling(node)
                })
        
        return functions
    
    def _extract_constants(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """定数を抽出"""
        constants = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        constants.append({
                            'name': target.id,
                            'value': self._get_constant_value(node.value)
                        })
        
        return constants
    
    def _detect_tech_indicators(self, content: str) -> Dict[str, float]:
        """技術指標を検出"""
        indicators = {
            'aws': 0.0,
            'web': 0.0,
            'data': 0.0,
            'database': 0.0,
            'testing': 0.0,
            'async': 0.0,
            'security': 0.0
        }
        
        content_lower = content.lower()
        
        # AWS関連
        aws_keywords = ['boto3', 'aws', 's3', 'dynamodb', 'lambda', 'cloudwatch']
        indicators['aws'] = sum(1 for kw in aws_keywords if kw in content_lower) / len(aws_keywords)
        
        # Web関連
        web_keywords = ['flask', 'django', 'fastapi', 'request', 'response', 'api']
        indicators['web'] = sum(1 for kw in web_keywords if kw in content_lower) / len(web_keywords)
        
        # データ処理関連
        data_keywords = ['pandas', 'numpy', 'dataframe', 'csv', 'json', 'data']
        indicators['data'] = sum(1 for kw in data_keywords if kw in content_lower) / len(data_keywords)
        
        # データベース関連
        db_keywords = ['sql', 'database', 'postgresql', 'mysql', 'sqlite', 'query']
        indicators['database'] = sum(1 for kw in db_keywords if kw in content_lower) / len(db_keywords)
        
        # テスト関連
        test_keywords = ['test', 'pytest', 'mock', 'assert', 'fixture']
        indicators['testing'] = sum(1 for kw in test_keywords if kw in content_lower) / len(test_keywords)
        
        # 非同期関連
        async_keywords = ['async', 'await', 'asyncio', 'coroutine']
        indicators['async'] = sum(1 for kw in async_keywords if kw in content_lower) / len(async_keywords)
        
        # セキュリティ関連
        security_keywords = ['auth', 'token', 'password', 'encrypt', 'hash', 'security']
        indicators['security'] = sum(1 for kw in security_keywords if kw in content_lower) / len(security_keywords)
        
        return indicators
    
    def _extract_error_patterns(self, tree: ast.AST) -> List[str]:
        """エラーハンドリングパターンを抽出"""
        patterns = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                # except節の例外タイプを収集
                for handler in node.handlers:
                    if handler.type:
                        exception_name = self._get_exception_name(handler.type)
                        if exception_name:
                            patterns.append(exception_name)
        
        return patterns
    
    def _extract_function_error_handling(self, func_node: ast.FunctionDef) -> List[str]:
        """関数内のエラーハンドリングを抽出"""
        patterns = []
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Try):
                for handler in node.handlers:
                    if handler.type:
                        exception_name = self._get_exception_name(handler.type)
                        if exception_name:
                            patterns.append(exception_name)
        
        return patterns
    
    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """デコレータ名を取得"""
        try:
            if isinstance(decorator, ast.Name):
                return decorator.id
            elif isinstance(decorator, ast.Attribute):
                return f"{decorator.value.id}.{decorator.attr}" if hasattr(
                    decorator.value,
                    'id'
                ) else decorator.attr
            elif isinstance(decorator, ast.Call):
                func_name = self._get_decorator_name(decorator.func)
                return f"{func_name}(...)"
            return f"<{type(decorator).__name__}>"
        except Exception:
            return "<decorator_error>"
    
    def _get_base_name(self, base: ast.expr) -> str:
        """基底クラス名を取得"""
        try:
            if isinstance(base, ast.Name):
                return base.id
            elif isinstance(base, ast.Attribute):
                return f"{base.value.id}.{base.attr}" if hasattr(base.value, 'id') else base.attr
            return f"<{type(base).__name__}>"
        except Exception:
            return "<base_error>"
    
    def _get_exception_name(self, exc_type: ast.expr) -> Optional[str]:
        """例外タイプ名を取得"""
        try:
            if isinstance(exc_type, ast.Name):
                return exc_type.id
            elif isinstance(exc_type, ast.Attribute):
                return f"{exc_type.value.id}.{exc_type.attr}" if hasattr(
                    exc_type.value,
                    'id'
                ) else exc_type.attr
            return f"<{type(exc_type).__name__}>"
        except Exception:
            return "<exception_error>"
    
    def _get_constant_value(self, value_node: ast.expr) -> Any:
        """定数値を取得"""
        try:
            if isinstance(value_node, ast.Constant):
                return value_node.value
            elif isinstance(value_node, ast.Str):
                return value_node.s
            elif isinstance(value_node, ast.Num):
                return value_node.n
            elif isinstance(value_node, (ast.List, ast.Tuple)):
                return "[collection]"
            elif isinstance(value_node, ast.Dict):
                return "{dict}"
            elif isinstance(value_node, ast.Call):
                return f"call({getattr(value_node.func, 'id', 'function')})"
            elif isinstance(value_node, ast.Name):
                return f"ref({value_node.id})"
        except Exception as e:
            # より詳細なエラーログ
            return f"<parse_error: {type(value_node).__name__}>"
        return "<unknown>"
    
    def _create_fallback_analysis(self, file_path: str) -> Dict[str, Any]:
        """フォールバック解析結果"""
        return {
            'imports': [],
            'classes': [],
            'functions': [],
            'constants': [],
            'docstring': None,
            'tech_indicators': {},
            'error_patterns': [],
            'analysis_failed': True,
            'file_path': file_path
        }


class PatternExtractor:
    """パターン抽出エンジン"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def extract_import_patterns(self, analyses: List[Dict[str, Any]]) -> List[ImportPattern]:
        """インポートパターンを抽出"""
        import_counts = defaultdict(int)
        import_contexts = defaultdict(set)
        
        for analysis in analyses:
            for imp in analysis.get('imports', []):
                module = imp['module']
                from_module = imp.get('from_module', '')
                
                # キーの生成
                if from_module:
                    key = f"from {from_module} import {module}"
                else:
                    key = f"import {module}"
                
                import_counts[key] += 1
                
                # コンテキスト情報を追加
                tech_indicators = analysis.get('tech_indicators', {})
                if tech_indicators:
                    primary_tech = max(tech_indicators.items(), key=lambda x: x[1])[0]
                    import_contexts[key].add(primary_tech)
        
        patterns = []
        for import_str, frequency in import_counts.items():
            if frequency >= 2:  # 2回以上使用されているパターンのみ
                # パース
                if import_str.startswith('from'):
                    match = re.match(r'from (\S+) import (\S+)', import_str)
                    if match:
                        from_module, module = match.groups()
                        patterns.append(ImportPattern(
                            module=module,
                            alias=None,
                            from_items=[module],
                            frequency=frequency,
                            context=', '.join(import_contexts[import_str])
                        ))
                else:
                    module = import_str.replace('import ', '')
                    patterns.append(ImportPattern(
                        module=module,
                        alias=None,
                        from_items=[],
                        frequency=frequency,
                        context=', '.join(import_contexts[import_str])
                    ))
        
        return sorted(patterns, key=lambda x: x.frequency, reverse=True)
    
    def extract_class_patterns(self, analyses: List[Dict[str, Any]]) -> List[ClassPattern]:
        """クラスパターンを抽出"""
        patterns = []
        
        for analysis in analyses:
            file_path = analysis.get('file_path', 'unknown')
            tech_indicators = analysis.get('tech_indicators', {})
            primary_tech = max(tech_indicators.items(), key=lambda x: x[1])[0] if tech_indicators else 'general' \
                'general'
            
            for cls in analysis.get('classes', []):
                patterns.append(ClassPattern(
                    name=cls['name'],
                    base_classes=cls['base_classes'],
                    methods=[m['name'] for m in cls['methods']],
                    attributes=cls['attributes'],
                    docstring=cls['docstring'],
                    file_path=file_path,
                    tech_domain=primary_tech
                ))
        
        return patterns
    
    def extract_method_patterns(self, analyses: List[Dict[str, Any]]) -> List[MethodPattern]:
        """メソッドパターンを抽出"""
        patterns = []
        
        for analysis in analyses:
            # クラスメソッド
            for cls in analysis.get('classes', []):
                for method in cls['methods']:
                    patterns.append(MethodPattern(
                        name=method['name'],
                        args=method['args'],
                        return_annotation=method.get('returns'),
                        decorators=method['decorators'],
                        is_async=method['is_async'],
                        error_handling=[],
                        docstring=method['docstring']
                    ))
            
            # 関数
            for func in analysis.get('functions', []):
                patterns.append(MethodPattern(
                    name=func['name'],
                    args=func['args'],
                    return_annotation=func.get('returns'),
                    decorators=func['decorators'],
                    is_async=func['is_async'],
                    error_handling=func.get('error_handling', []),
                    docstring=func['docstring']
                ))
        
        return patterns
    
    def extract_error_handling_patterns(self, analyses: List[Dict[str, Any]]) -> List[str]:
        """エラーハンドリングパターンを抽出"""
        error_counts = Counter()
        
        for analysis in analyses:
            for pattern in analysis.get('error_patterns', []):
                error_counts[pattern] += 1
        
        # 2回以上使用されているパターンを返す
        return [pattern for pattern, count in error_counts.items() if count >= 2]
    
    def analyze_naming_conventions(self, analyses: List[Dict[str, Any]]) -> Dict[str, str]:
        """命名規則を分析"""
        conventions = {
            'class_naming': 'PascalCase',
            'function_naming': 'snake_case',
            'constant_naming': 'UPPER_CASE',
            'variable_naming': 'snake_case'
        }
        
        # 簡単な分析（実際の命名パターンをチェック）
        class_names = []
        function_names = []
        
        for analysis in analyses:
            class_names.extend([cls['name'] for cls in analysis.get('classes', [])])
            function_names.extend([func['name'] for func in analysis.get('functions', [])])
        
        # クラス名の分析
        if class_names:
            pascal_case_count = sum(1 for name in class_names if name[0].isupper() and '_' not in name)
            if pascal_case_count / len(class_names) > 0.8:
                conventions['class_naming'] = 'PascalCase'
        
        # 関数名の分析
        if function_names:
            snake_case_count = sum(1 for name in function_names if '_' in name and name.islower())
            if snake_case_count / len(function_names) > 0.8:
                conventions['function_naming'] = 'snake_case'
        
        return conventions


class CodebaseAnalysisEngine:
    """コードベース分析エンジン (Phase 3)"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.ast_analyzer = ASTAnalyzer()
        self.pattern_extractor = PatternExtractor()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 除外するディレクトリ (外部ライブラリ強化)
        self.exclude_dirs = {
            '__pycache__', '.git', '.pytest_cache', 'node_modules',
            '.venv', 'venv', 'env', '.env', 'build', 'dist',
            'site-packages', 'lib', 'dist-packages', 'Lib',
            '.tox', '.conda', 'miniconda3', 'anaconda3'
        }
    
    def analyze_codebase(self, tech_stack: Dict[str, Any]) -> CodebaseIntelligence:
        """コードベース全体を分析"""
        self.logger.info("Starting codebase analysis...")
        
        # Python ファイルを収集
        python_files = self._collect_python_files()
        self.logger.info(f"Found {len(python_files)} Python files")
        
        # 技術スタックに基づいて関連ファイルをフィルタリング
        relevant_files = self._filter_relevant_files(python_files, tech_stack)
        self.logger.info(f"Filtered to {len(relevant_files)} relevant files")
        
        # ファイルを解析
        analyses = []
        for file_path in relevant_files:
            analysis = self.ast_analyzer.analyze_file(str(file_path))
            analysis['file_path'] = str(file_path)
            analyses.append(analysis)
        
        # パターン抽出
        import_patterns = self.pattern_extractor.extract_import_patterns(analyses)
        class_patterns = self.pattern_extractor.extract_class_patterns(analyses)
        method_patterns = self.pattern_extractor.extract_method_patterns(analyses)
        error_handling = self.pattern_extractor.extract_error_handling_patterns(analyses)
        naming_conventions = self.pattern_extractor.analyze_naming_conventions(analyses)
        
        # 技術ドメイン分析
        tech_domains = self._analyze_tech_domains(analyses)
        
        # ファイル構造分析
        file_structure = self._analyze_file_structure(python_files)
        
        self.logger.info(f"Analysis complete: {len(import_patterns)} import patterns, "
                        f"{len(class_patterns)} class patterns, {len(method_patterns)} " \
                            "method patterns")
        
        return CodebaseIntelligence(
            import_patterns=import_patterns,
            class_patterns=class_patterns,
            method_patterns=method_patterns,
            tech_domains=tech_domains,
            common_error_handling=error_handling,
            naming_conventions=naming_conventions,
            file_structure=file_structure
        )
    
    def find_similar_implementations(self, tech_stack: Dict[str, Any]) -> List[str]:
        """類似実装を検索"""
        primary_stack = tech_stack.get('primary_stack', 'general')
        services = tech_stack.get('services', [])
        
        similar_files = []
        python_files = self._collect_python_files()
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                
                # 技術スタックキーワードでマッチング
                if primary_stack == 'aws':
                    aws_keywords = ['boto3', 'aws'] + services
                    if any(keyword in content for keyword in aws_keywords):
                        similar_files.append(str(file_path))
                elif primary_stack == 'web':
                    web_keywords = ['flask', 'django', 'fastapi', 'api']
                    if any(keyword in content for keyword in web_keywords):
                        similar_files.append(str(file_path))
                elif primary_stack == 'data':
                    data_keywords = ['pandas', 'numpy', 'dataframe']
                    if any(keyword in content for keyword in data_keywords):
                        similar_files.append(str(file_path))
                        
            except Exception as e:
                self.logger.warning(f"Failed to read {file_path}: {e}")
        
        return similar_files[:10]  # 最大10ファイル
    
    def _collect_python_files(self) -> List[Path]:
        """Python ファイルを収集"""
        python_files = []
        
        for file_path in self.project_root.rglob("*.py"):
            # 除外ディレクトリをチェック
            if any(exclude_dir in file_path.parts for exclude_dir in self.exclude_dirs):
                continue
            
            python_files.append(file_path)
        
        return python_files
    
    def _filter_relevant_files(self, files: List[Path], tech_stack: Dict[str, Any]) -> List[Path]:
        """技術スタックに関連するファイルをフィルタリング"""
        if not tech_stack or tech_stack.get('primary_stack') == 'general':
            return files[:10]  # 一般的な場合は最大10ファイル (最適化)
        
        primary_stack = tech_stack.get('primary_stack', '')
        relevant_files = []
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                
                # 関連性スコア計算
                relevance_score = 0
                
                if primary_stack == 'aws':
                    aws_keywords = ['boto3', 'aws', 's3', 'dynamodb', 'cloudwatch', 'lambda']
                    relevance_score = sum(1 for kw in aws_keywords if kw in content)
                elif primary_stack == 'web':
                    web_keywords = ['flask', 'django', 'fastapi', 'request', 'response']
                    relevance_score = sum(1 for kw in web_keywords if kw in content)
                elif primary_stack == 'data':
                    data_keywords = ['pandas', 'numpy', 'dataframe', 'csv']
                    relevance_score = sum(1 for kw in data_keywords if kw in content)
                
                if relevance_score > 0:
                    relevant_files.append((file_path, relevance_score))
                    
            except Exception as e:
                self.logger.warning(f"Failed to read {file_path}: {e}")
        
        # スコア順にソートして上位を返す
        relevant_files.sort(key=lambda x: x[1], reverse=True)
        return [file_path for file_path, _ in relevant_files[:10]]  # 最大10ファイル (最適化)
    
    def _analyze_tech_domains(self, analyses: List[Dict[str, Any]]) -> Dict[str, float]:
        """技術ドメインを分析"""
        domain_scores = defaultdict(float)
        
        for analysis in analyses:
            tech_indicators = analysis.get('tech_indicators', {})
            for domain, score in tech_indicators.items():
                domain_scores[domain] += score
        
        # 正規化
        total_files = len(analyses)
        if total_files > 0:
            for domain in domain_scores:
                domain_scores[domain] /= total_files
        
        return dict(domain_scores)
    
    def _analyze_file_structure(self, files: List[Path]) -> Dict[str, List[str]]:
        """ファイル構造を分析"""
        structure = defaultdict(list)
        
        for file_path in files:
            parts = file_path.parts
            if len(parts) > 1:
                directory = parts[-2]  # 親ディレクトリ
                filename = parts[-1]
                structure[directory].append(filename)
        
        return dict(structure)
    
    def _is_external_library_file(self, file_path: str) -> bool:
        """外部ライブラリファイルかどうかを判定"""
        path_str = str(file_path).lower()
        external_indicators = [
            'site-packages', 'dist-packages', 'lib/python',
            'miniconda', 'anaconda', 'virtualenv', 'venv',
            '.tox', '.conda', '__pycache__', '.git'
        ]
        return any(indicator in path_str for indicator in external_indicators)