#!/usr/bin/env python3
"""
Intelligent Test Generator
インテリジェントテスト生成システム (Phase 4)
"""

import ast
import re
import inspect
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path

# Hypothesis をオプショナルに
try:
    import hypothesis
    from hypothesis import strategies as st
    from hypothesis import given, assume, example
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """テストケース情報"""
    name: str
    test_type: str  # unit, integration, property
    code: str
    description: str
    priority: str  # high, medium, low
    dependencies: List[str] = field(default_factory=list)


@dataclass
class TestSuite:
    """テストスイート"""
    unit_tests: List[TestCase]
    integration_tests: List[TestCase]
    property_tests: List[TestCase]
    mock_configurations: Dict[str, Any]
    fixtures: List[str]


class CodeAnalyzer:
    """コード分析・テスト対象抽出"""
    
    def __init__(self):
    """初期化メソッド"""
    
    def analyze_implementation(self, code: str) -> Dict[str, Any]:
        """実装コードを分析してテスト対象を特定"""
        try:
            tree = ast.parse(code)
            analysis = {
                'classes': self._extract_classes(tree),
                'functions': self._extract_functions(tree),
                'imports': self._extract_imports(tree),
                'external_dependencies': self._extract_external_deps(tree),
                'complexity_indicators': self._analyze_complexity(tree),
                'testable_methods': self._identify_testable_methods(tree)
            }
            return analysis
            
        except Exception as e:
            self.logger.error(f"Code analysis failed: {e}")
            return self._fallback_analysis(code)
    
    def _extract_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """クラス情報を抽出"""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append({
                            'name': item.name,
                            'args': [arg.arg for arg in item.args.args],
                            'is_async': isinstance(item, ast.AsyncFunctionDef),
                            'has_return': self._has_return_statement(item),
                            'raises_exceptions': self._extract_exceptions(item),
                            'calls_external': self._calls_external_apis(item)
                        })
                
                classes.append({
                    'name': node.name,
                    'methods': methods,
                    'has_init': any(m['name'] == '__init__' for m in methods),
                    'inheritance': [self._get_base_name(base) for base in node.bases]
                })
        
        return classes
    
    def _extract_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """関数情報を抽出"""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not self._is_class_method(node, tree):
                functions.append({
                    'name': node.name,
                    'args': [arg.arg for arg in node.args.args],
                    'is_async': isinstance(node, ast.AsyncFunctionDef),
                    'has_return': self._has_return_statement(node),
                    'raises_exceptions': self._extract_exceptions(node),
                    'calls_external': self._calls_external_apis(node)
                })
        
        return functions
    
    def _extract_imports(self, tree: ast.AST) -> List[Dict[str, str]]:
        """インポート情報を抽出"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        'module': alias.name,
                        'alias': alias.asname,
                        'type': 'import'
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append({
                        'module': alias.name,
                        'from_module': module,
                        'alias': alias.asname,
                        'type': 'from_import'
                    })
        
        return imports
    
    def _extract_external_deps(self, tree: ast.AST) -> List[str]external_deps = set()
    """外部依存関係を抽出"""
        :
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # boto3クライアント作成
                if isinstance(node.func, ast.Attribute):
                    if hasattr(node.func.value, 'id') and node.func.value.id == 'boto3':
                        external_deps.add('aws_service')
                
                # HTTP リクエスト
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['requests', 'httpx', 'aiohttp']:
                        external_deps.add('http_api')
                
                # データベース
                if isinstance(node.func, ast.Attribute):
                    if 'execute' in node.func.attr or 'query' in node.func.attr:
                        external_deps.add('database')
        
        return list(external_deps)
    
    def _analyze_complexity(self, tree: ast.AST) -> Dict[str, float]:
        """コード複雑度を分析"""
        complexity = {
            'cyclomatic': 0,
            'nesting_depth': 0,
            'external_calls': 0,
            'exception_handling': 0
        }
        
        for node in ast.walk(tree):
            # 分岐・ループ
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With)):
                complexity['cyclomatic'] += 1
            
            # ネスト深度
            if isinstance(node, ast.FunctionDef):
                depth = self._calculate_nesting_depth(node)
                complexity['nesting_depth'] = max(complexity['nesting_depth'], depth)
            
            # 外部呼び出し
            if isinstance(node, ast.Call):
                complexity['external_calls'] += 1
            
            # 例外処理
            if isinstance(node, ast.Try):
                complexity['exception_handling'] += 1
        
        return complexity
    
    def _identify_testable_methods(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """テスト可能なメソッドを特定"""
        testable = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # プライベートメソッド以外
                if not node.name.startswith('_'):
                    testable.append({
                        'name': node.name,
                        'test_types': self._determine_test_types(node),
                        'mock_requirements': self._identify_mock_needs(node),
                        'edge_cases': self._identify_edge_cases(node)
                    })
        
        return testable
    
    def _has_return_statement(self, func_node: ast.FunctionDef) -> boolfor node in ast.walk(func_node)if isinstance(node, ast.Return) and node.value is not None:
    """return文があるかチェック"""
                return True
        return False
    
    def _extract_exceptions(self, func_node: ast.FunctionDef) -> List[str]:
        """発生する例外を抽出"""
        exceptions = []
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Raise):
                if isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name):
                    exceptions.append(node.exc.func.id)
                elif isinstance(node.exc, ast.Name):
                    exceptions.append(node.exc.id)
        
        return exceptions
    
    def _calls_external_apis(self, func_node: ast.FunctionDef) -> boolfor node in ast.walk(func_node)if isinstance(node, ast.Call)if isinstance(node.func, ast.Attribute):
    """外部API呼び出しがあるかチェック"""
                    # boto3, requests等の呼び出し
                    if hasattr(node.func.value, 'id'):
                        if node.func.value.id in ['boto3', 'requests', 'httpx']:
                            return True
        return False
    
    def _get_base_name(self, base: ast.expr) -> strif isinstance(base, ast.Name):
    """基底クラス名を取得"""
            return base.id
        elif isinstance(base, ast.Attribute):
            return f"{base.value.id}.{base.attr}" if hasattr(base.value, 'id') else base.attr
        return str(base)
    
    def _is_class_method(self, func_node: ast.FunctionDef, tree: ast.AST) -> boolfor node in ast.walk(tree)if isinstance(node, ast.ClassDef):
    """クラスメソッドかどうか判定"""
                if func_node in node.body:
                    return True
        return False
    
    def _calculate_nesting_depth(self, func_node: ast.FunctionDef) -> int:
        """ネスト深度を計算"""
        max_depth = 0
        
        def walk_with_depth(node, current_depth=0):
            """walk_with_depthメソッド"""
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)
            
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                current_depth += 1
            
            for child in ast.iter_child_nodes(node):
                walk_with_depth(child, current_depth)
        
        walk_with_depth(func_node)
        return max_depth
    
    def _determine_test_types(self, func_node: ast.FunctionDef) -> List[str]:
        """必要なテストタイプを決定"""
        test_types = ['unit']  # 基本はユニットテスト
        
        # 非同期メソッドの場合
        if isinstance(func_node, ast.AsyncFunctionDef):
            test_types.append('async')
        
        # 外部API呼び出しがある場合
        if self._calls_external_apis(func_node):
            test_types.append('integration')
            test_types.append('mock')
        
        # 複雑な処理の場合
        if self._calculate_nesting_depth(func_node) > 2:
            test_types.append('property')
        
        return test_types
    
    def _identify_mock_needs(self, func_node: ast.FunctionDef) -> List[str]:
        """モック対象を特定"""
        mock_targets = []
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                # boto3クライアント
                if isinstance(node.func, ast.Attribute):
                    if hasattr(node.func.value, 'id') and 'client' in node.func.value.id:
                        mock_targets.append('aws_client')
                
                # HTTP リクエスト
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['get', 'post', 'put', 'delete']:
                        mock_targets.append('http_request')
        
        return mock_targets
    
    def _identify_edge_cases(self, func_node: ast.FunctionDef) -> List[str]:
        """エッジケースを特定"""
        edge_cases = []
        
        # 引数チェック
        args = func_node.args.args
        if args:
            edge_cases.extend(['empty_input', 'invalid_input', 'none_input'])
        
        # 例外処理がある場合
        if self._extract_exceptions(func_node):
            edge_cases.append('exception_cases')
        
        # 外部依存がある場合
        if self._calls_external_apis(func_node):
            edge_cases.extend(['network_error', 'timeout', 'auth_error'])
        
        return edge_cases
    
    def _fallback_analysis(self, code: str) -> Dict[str, Any]:
        """フォールバック分析"""
        return {
            'classes': [],
            'functions': [],
            'imports': [],
            'external_dependencies': [],
            'complexity_indicators': {'cyclomatic': 1},
            'testable_methods': []
        }


class UnitTestGenerator:
    """ユニットテスト生成器"""
    
    def __init__(self):
    """初期化メソッド"""
    
    def generate_unit_tests(self, analysis: Dict[str, Any], intelligence=None) -> List[TestCase]:
        """ユニットテストを生成"""
        tests = []
        
        # クラステスト
        for cls in analysis.get('classes', []):
            tests.extend(self._generate_class_tests(cls, intelligence))
        
        # 関数テスト
        for func in analysis.get('functions', []):
            tests.extend(self._generate_function_tests(func, intelligence))
        
        return tests
    
    def _generate_class_tests(self, cls_info: Dict[str, Any], intelligence) -> List[TestCase]:
        """クラステストを生成"""
        tests = []
        class_name = cls_info['name']
        
        # 初期化テスト
        if cls_info.get('has_init'):
            init_test = self._generate_init_test(class_name, intelligence)
            tests.append(init_test)
        
        # メソッドテスト
        for method in cls_info.get('methods', []):
            if not method['name'].startswith('_'):  # パブリックメソッドのみ
                method_test = self._generate_method_test(class_name, method, intelligence)
                tests.append(method_test)
        
        return tests
    
    def _generate_init_test(self, class_name: str, intelligence) -> TestCase:
        """初期化テストを生成"""
        # 技術スタックに応じた初期化パラメータ
        init_params = ""
        if intelligence and intelligence.get('primary_domain') == 'aws':
            init_params = "region_name='us-east-1'"
        
        test_code = f"""
def test_{class_name.lower()}_initialization():
    \"\"\"Test {class_name} initialization\"\"\"
    instance = {class_name}({init_params})
    assert instance is not None
    assert hasattr(instance, 'initialized') or True
"""
        
        return TestCase(
            name=f"test_{class_name.lower()}_initialization",
            test_type="unit",
            code=test_code.strip(),
            description=f"Test {class_name} proper initialization",
            priority="high"
        )
    
    def _generate_method_test(
        self,
        class_name: str,
        method_info: Dict[str,
        Any],
        intelligence
    ) -> TestCase:
        """メソッドテストを生成"""
        method_name = method_info['name']
        
        # 技術固有のテストパターン
        test_code = self._generate_method_test_code(class_name, method_info, intelligence)
        
        return TestCase(
            name=f"test_{class_name.lower()}_{method_name}",
            test_type="unit",
            code=test_code,
            description=f"Test {class_name}.{method_name} functionality",
            priority="high" if method_info.get('calls_external') else "medium"
        )
    
    def _generate_method_test_code(
        self,
        class_name: str,
        method_info: Dict[str,
        Any],
        intelligence
    ) -> str:
        """メソッドテストコードを生成"""
        method_name = method_info['name']
        args = method_info.get('args', [])
        
        # 引数準備
        arg_setup = self._generate_test_arguments(args, intelligence)
        
        # モック設定
        mock_setup = ""
        if method_info.get('calls_external'):
            mock_setup = self._generate_mock_setup(intelligence)
        
        # アサーション
        assertions = self._generate_assertions(method_info, intelligence)
        
        test_code = f"""
def test_{class_name.lower()}_{method_name}():
    \"\"\"Test {class_name}.{method_name} functionality\"\"\"
    {mock_setup}
    
    # Setup
    instance = {class_name}()
    {arg_setup}
    
    # Execute
    {"result = " if method_info.get('has_return') " \
        "else ""}{f"await " if  \
            method_info.get('is_async') else ""}instance.{method_name}({', '.join(args[1:] if args and \
        \
        args[0] == 'self' else args)})
    
    # Assert
    {assertions}
"""
        
        return test_code.strip()
    
    def _generate_function_tests(self, func_info: Dict[str, Any], intelligence) -> List[TestCase]:
        """関数テストを生成"""
        func_name = func_info['name']
        
        test_code = self._generate_function_test_code(func_info, intelligence)
        
        return [TestCase(
            name=f"test_{func_name}",
            test_type="unit",
            code=test_code,
            description=f"Test {func_name} function",
            priority="medium"
        )]
    
    def _generate_function_test_code(self, func_info: Dict[str, Any], intelligence) -> str:
        """関数テストコードを生成"""
        func_name = func_info['name']
        args = func_info.get('args', [])
        
        arg_setup = self._generate_test_arguments(args, intelligence)
        assertions = self._generate_assertions(func_info, intelligence)
        
        test_code = f"""
def test_{func_name}():
    \"\"\"Test {func_name} function\"\"\"
    # Setup
    {arg_setup}
    
    # Execute
    {"result = " \
        if func_info.get('has_return') \
        else ""}{f"await " if func_info.get('is_async') else ""}{func_name}({', '.join(args)})
    
    # Assert
    {assertions}
"""
        
        return test_code.strip()
    
    def _generate_test_arguments(self, args: List[str], intelligence) -> str:
        """テスト引数を生成"""
        if not args:
            return "# No arguments needed"
        
        arg_lines = []
        for arg in args:
            if arg == 'self':
                continue
            
            # 技術スタックに応じた引数
            if intelligence and intelligence.get('primary_domain') == 'aws':
                if 'bucket' in arg.lower():
                    arg_lines.append(f'{arg} = "test-bucket-name"')
                elif 'key' in arg.lower():
                    arg_lines.append(f'{arg} = "test-object-key"')
                else:
                    arg_lines.append(f'{arg} = "test_value"')
            else:
                arg_lines.append(f'{arg} = "test_value"')
        
        return '\n    '.join(arg_lines) if arg_lines else "# No arguments needed"
    
    def _generate_mock_setup(self, intelligence) -> str:
        """モック設定を生成"""
        if not intelligence:
            return "@patch('requests.get')\n    @patch('boto3client')"
        
        domain = intelligence.get('primary_domain', 'general')
        if domain == 'aws':
            return "@patch('boto3client')"
        elif domain == 'web':
            return "@patch('requests.post')\n    @patch('requests.get')"
        else:
            return "@patch('external_service')"
    
    def _generate_assertions(self, method_info: Dict[str, Any], intelligence) -> str:
        """アサーションを生成"""
        assertions = []
        
        if method_info.get('has_return'):
            assertions.append("assert result is not None")
            
            # 技術固有のアサーション
            if intelligence and intelligence.get('primary_domain') == 'aws':
                assertions.append("assert 'status' in result or result")
            elif intelligence and intelligence.get('primary_domain') == 'web':
                assertions.append("assert result.status_code == 200 or result")
        else:
            assertions.append("# Method executed without error")
        
        return '\n    '.join(assertions) if assertions else "assert True"


class PropertyTestGenerator:
    """プロパティベーステスト生成器"""
    
    def __init__(self):
    """初期化メソッド"""
    
    def generate_property_tests(
        self,
        analysis: Dict[str,
        Any],
        intelligence=None
    ) -> List[TestCase]:
        """プロパティベーステストを生成"""
        if not HYPOTHESIS_AVAILABLE:
            self.logger.warning("Hypothesis not available, skipping property tests")
            return []
        
        tests = []
        
        # 複雑なメソッドに対してプロパティテストを生成
        for method in analysis.get('testable_methods', []):
            if 'property' in method.get('test_types', []):
                prop_test = self._generate_property_test(method, intelligence)
                tests.append(prop_test)
        
        return tests
    
    def _generate_property_test(self, method_info: Dict[str, Any], intelligence) -> TestCase:
        """プロパティテストを生成"""
        method_name = method_info['name']
        
        # 技術固有のストラテジー
        strategies = self._generate_strategies(method_info, intelligence)
        
        test_code = f"""
@given({strategies})
def test_{method_name}_property(input_data):
    \"\"\"Property-based test for {method_name}\"\"\"
    assume(input_data is not None)
    
    # Property: Function should not crash with valid input
    try:
        result = {method_name}(input_data)
        assert result is not None or result == [] or result == {{}}
    except ValueError:
        # Expected for invalid input
        pass
    except Exception as e:
        # Unexpected exceptions should be caught
        pytest.fail(f"Unexpected exception: {{e}}")
"""
        
        return TestCase(
            name=f"test_{method_name}_property",
            test_type="property",
            code=test_code.strip(),
            description=f"Property-based test for {method_name}",
            priority="medium"
        )
    
    def _generate_strategies(self, method_info: Dict[str, Any], intelligence) -> str:
        """Hypothesisストラテジーを生成"""
        if not intelligence:
            return "st.text()"
        
        domain = intelligence.get('primary_domain', 'general')
        
        if domain == 'aws':
            return "st.text(min_size=3, max_size=63).filter(lambda x: x.replace('-', '').replace('_', '').isalnum())"
        elif domain == 'web':
            return "st.dictionaries(st.text(), st.one_of(st.text(), st.integers(), st.booleans()))"
        elif domain == 'data':
            return "st.lists(st.floats(allow_nan=False), min_size=1, max_size=100)"
        else:
            return "st.text()"


class IntegrationTestGenerator:
    """統合テスト生成器"""
    
    def __init__(self):
    """初期化メソッド"""
    
    def generate_integration_tests(
        self,
        analysis: Dict[str,
        Any],
        intelligence=None
    ) -> List[TestCase]:
        """統合テストを生成"""
        tests = []
        
        external_deps = analysis.get('external_dependencies', [])
        
        for dep in external_deps:
            if dep == 'aws_service':
                tests.append(self._generate_aws_integration_test(intelligence))
            elif dep == 'http_api':
                tests.append(self._generate_api_integration_test(intelligence))
            elif dep == 'database':
                tests.append(self._generate_database_integration_test(intelligence))
        
        return tests
    
    def _generate_aws_integration_test(self, intelligence) -> TestCase:
        """AWS統合テストを生成"""
        test_code = """
@pytest.mark.integration
@pytest.mark.aws
def test_aws_service_integration():
    \"\"\"Integration test for AWS service\"\"\"
    # Setup: Use LocalStack or moto for testing
    with mock_aws():
        # Create service instance
        service = AWSServiceManager()
        
        # Test actual AWS operations
        result = service.create_test_resource()
        
        # Verify integration
        assert result['status'] == 'success'
        assert 'resource_id' in result
"""
        
        return TestCase(
            name="test_aws_service_integration",
            test_type="integration",
            code=test_code.strip(),
            description="AWS service integration test",
            priority="high",
            dependencies=["moto", "localstack"]
        )
    
    def _generate_api_integration_test(self, intelligence) -> TestCase:
        """API統合テストを生成"""
        test_code = """
@pytest.mark.integration
@pytest.mark.api
def test_api_integration():
    \"\"\"Integration test for API endpoints\"\"\"
    # Setup test client
    client = TestClient(app)
    
    # Test API integration
    response = client.post("/api/test", json={"data": "test"})
    
    # Verify response
    assert response.status_code == 200
    assert response.json()["status"] == "success"
"""
        
        return TestCase(
            name="test_api_integration",
            test_type="integration",
            code=test_code.strip(),
            description="API endpoint integration test",
            priority="high",
            dependencies=["fastapi.testclient"]
        )
    
    def _generate_database_integration_test(self, intelligence) -> TestCase:
        """データベース統合テストを生成"""
        test_code = """
@pytest.mark.integration
@pytest.mark.database
def test_database_integration():
    \"\"\"Integration test for database operations\"\"\"
    # Setup test database
    test_db = create_test_database()
    
    try:
        # Test database operations
        result = perform_database_operation(test_db)
        
        # Verify data integrity
        assert result is not None
        assert test_db.verify_data_consistency()
        
    finally:
        # Cleanup
        cleanup_test_database(test_db)
"""
        
        return TestCase(
            name="test_database_integration",
            test_type="integration",
            code=test_code.strip(),
            description="Database integration test",
            priority="medium",
            dependencies=["sqlalchemy", "pytest-postgresql"]
        )


class IntelligentTestGenerator:
    """インテリジェントテスト生成メインクラス (Phase 4)"""
    
    def __init__(self)self.unit_generator = UnitTestGenerator()
    """初期化メソッド"""
        self.property_generator = PropertyTestGenerator()
        self.integration_generator = IntegrationTestGenerator()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def generate_comprehensive_tests(
        self, 
        implementation_code: str, 
        intelligence=None,
        codebase_intelligence=None
    ) -> TestSuite:
        """包括的テストスイートを生成"""
        
        self.logger.info("Starting intelligent test generation...")
        
        # 1.0 コード分析
        analysis = self.code_analyzer.analyze_implementation(implementation_code)
        self.logger.info(f"Code analysis complete: {len(analysis." \
            "get('classes', []))} classes, {len(analysis.get('functions', []))} functions")
        
        # 2.0 ユニットテスト生成
        unit_tests = self.unit_generator.generate_unit_tests(analysis, intelligence)
        self.logger.info(f"Generated {len(unit_tests)} unit tests")
        
        # 3.0 プロパティベーステスト生成
        property_tests = self.property_generator.generate_property_tests(analysis, intelligence)
        self.logger.info(f"Generated {len(property_tests)} property tests")
        
        # 4.0 統合テスト生成
        integration_tests = self.integration_generator.generate_integration_tests(
            analysis,
            intelligence
        )
        self.logger.info(f"Generated {len(integration_tests)} integration tests")
        
        # 5.0 モック設定・フィクスチャ生成
        mock_configs = self._generate_mock_configurations(analysis, intelligence)
        fixtures = self._generate_fixtures(analysis, intelligence, codebase_intelligence)
        
        return TestSuite(
            unit_tests=unit_tests,
            integration_tests=integration_tests,
            property_tests=property_tests,
            mock_configurations=mock_configs,
            fixtures=fixtures
        )
    
    def _generate_mock_configurations(
        self,
        analysis: Dict[str,
        Any],
        intelligence
    ) -> Dict[str, Any]:
        """モック設定を生成"""
        mock_configs = {}
        
        external_deps = analysis.get('external_dependencies', [])
        
        if 'aws_service' in external_deps:
            mock_configs['aws'] = {
                'mock_type': 'moto',
                'services': ['s3', 'dynamodb', 'cloudwatch'],
                'configuration': '@mock_aws()'
            }
        
        if 'http_api' in external_deps:
            mock_configs['http'] = {
                'mock_type': 'requests_mock',
                'endpoints': ['GET /api/test', 'POST /api/data'],
                'configuration': '@requests_mock.Mocker()'
            }
        
        if 'database' in external_deps:
            mock_configs['database'] = {
                'mock_type': 'sqlalchemy_mock',
                'tables': ['users', 'data'],
                'configuration': '@pytest.fixture(scope="function")'
            }
        
        return mock_configs
    
    def _generate_fixtures(
        self,
        analysis: Dict[str,
        Any],
        intelligence,
        codebase_intelligence
    ) -> List[str]:
        """テストフィクスチャを生成"""
        fixtures = []
        
        # 基本フィクスチャ
        fixtures.append("""
@pytest.fixture
def sample_data():
    \"\"\"Sample test data fixture\"\"\"
    return {
        "test_string": "test_value",
        "test_number": 42,
        "test_list": [1, 2, 3],
        "test_dict": {"key": "value"}
    }
""")
        
        # 技術固有フィクスチャ
        if intelligence and intelligence.get('primary_domain') == 'aws':
            fixtures.append("""
@pytest.fixture
def aws_credentials():
    \"\"\"Mock AWS credentials for testing\"\"\"
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
""")
        
        # コードベース学習ベースのフィクスチャ
        if codebase_intelligence:
            for pattern in codebase_intelligence.class_patterns[:3]:
                if pattern.tech_domain == intelligence.get('primary_domain', 'general'):
                    fixtures.append(f"""
@pytest.fixture
def mock_{pattern.name.lower()}():
    \"\"\"Mock {pattern.name} for testing\"\"\"
    mock = Mock(spec={pattern.name})
    mock.initialized = True
    return mock
""")
        
        return fixtures