#!/usr/bin/env python3
"""
Automated Test Generator for AI Company
Generates high-quality tests based on AST parsing and proven patterns
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
import inspect
import importlib.util
import json
from collections import defaultdict

@dataclass
class FunctionInfo:
    """Information about a function extracted from AST"""
    name: str
    args: List[str]
    defaults: List[Any]
    return_annotation: Optional[str]
    decorators: List[str]
    docstring: Optional[str]
    is_async: bool
    is_method: bool
    class_name: Optional[str] = None
    complexity: int = 0
    calls_made: Set[str] = field(default_factory=set)
    raises: Set[str] = field(default_factory=set)
    line_number: int = 0

@dataclass
class ClassInfo:
    """Information about a class extracted from AST"""
    name: str
    bases: List[str]
    methods: List[FunctionInfo]
    docstring: Optional[str]
    decorators: List[str]
    is_abstract: bool
    line_number: int = 0
    init_method: Optional[FunctionInfo] = None

@dataclass
class ModuleInfo:
    """Information about a module"""
    path: Path
    classes: List[ClassInfo]
    functions: List[FunctionInfo]
    imports: List[str]
    docstring: Optional[str]
    coverage_percentage: float = 0.0


class ASTAnalyzer:
    """Analyzes Python modules using AST to extract testable components"""
    
    def __init__(self):
        self.current_class = None
        
    def analyze_module(self, file_path: Path) -> ModuleInfo:
        """Analyze a Python module and extract information"""
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
            
        tree = ast.parse(source)
        
        module_info = ModuleInfo(
            path=file_path,
            classes=[],
            functions=[],
            imports=[],
            docstring=ast.get_docstring(tree)
        )
        
        # Extract imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_info.imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_info.imports.append(node.module)
        
        # Extract classes and functions
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_info = self._analyze_class(node)
                module_info.classes.append(class_info)
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                func_info = self._analyze_function(node)
                module_info.functions.append(func_info)
                
        return module_info
        
    def _analyze_class(self, node: ast.ClassDef) -> ClassInfo:
        """Analyze a class definition"""
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{base.value.id}.{base.attr}" if isinstance(base.value, ast.Name) else base.attr)
                
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        is_abstract = 'ABC' in bases or 'abc.ABC' in bases or any('abstract' in d.lower() for d in decorators)
        
        class_info = ClassInfo(
            name=node.name,
            bases=bases,
            methods=[],
            docstring=ast.get_docstring(node),
            decorators=decorators,
            is_abstract=is_abstract,
            line_number=node.lineno
        )
        
        # Analyze methods
        self.current_class = node.name
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = self._analyze_function(item, is_method=True)
                class_info.methods.append(method_info)
                if method_info.name == '__init__':
                    class_info.init_method = method_info
        self.current_class = None
        
        return class_info
        
    def _analyze_function(self, node: ast.FunctionDef, is_method: bool = False) -> FunctionInfo:
        """Analyze a function/method definition"""
        args = []
        defaults = []
        
        # Extract arguments
        for arg in node.args.args:
            if not is_method or arg.arg != 'self':  # Skip 'self' for methods
                args.append(arg.arg)
                
        # Extract defaults
        if node.args.defaults:
            defaults = [self._get_default_value(d) for d in node.args.defaults]
            
        # Extract return annotation
        return_annotation = None
        if node.returns:
            return_annotation = self._get_annotation(node.returns)
            
        # Extract decorators
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        
        # Calculate complexity and extract calls/raises
        complexity = self._calculate_complexity(node)
        calls_made = self._extract_calls(node)
        raises = self._extract_raises(node)
        
        return FunctionInfo(
            name=node.name,
            args=args,
            defaults=defaults,
            return_annotation=return_annotation,
            decorators=decorators,
            docstring=ast.get_docstring(node),
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_method=is_method,
            class_name=self.current_class,
            complexity=complexity,
            calls_made=calls_made,
            raises=raises,
            line_number=node.lineno
        )
        
    def _get_decorator_name(self, decorator) -> str:
        """Extract decorator name from AST node"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr
        return "unknown"
        
    def _get_default_value(self, node) -> Any:
        """Extract default value from AST node"""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.List):
            return []
        elif isinstance(node, ast.Dict):
            return {}
        return None
        
    def _get_annotation(self, node) -> str:
        """Extract type annotation as string"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Subscript):
            return "Generic"  # Simplified for now
        return "Any"
        
    def _calculate_complexity(self, node) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
        return complexity
        
    def _extract_calls(self, node) -> Set[str]:
        """Extract function calls made within a function"""
        calls = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.add(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.add(child.func.attr)
        return calls
        
    def _extract_raises(self, node) -> Set[str]:
        """Extract exceptions that might be raised"""
        raises = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Raise):
                if child.exc:
                    if isinstance(child.exc, ast.Call) and isinstance(child.exc.func, ast.Name):
                        raises.add(child.exc.func.id)
                    elif isinstance(child.exc, ast.Name):
                        raises.add(child.exc.id)
        return raises


class PatternLibrary:
    """Library of successful test patterns extracted from high-coverage modules"""
    
    def __init__(self):
        self.patterns = {
            'initialization': self._load_initialization_patterns(),
            'method_test': self._load_method_test_patterns(),
            'error_handling': self._load_error_handling_patterns(),
            'mocking': self._load_mocking_patterns(),
            'async': self._load_async_patterns(),
            'integration': self._load_integration_patterns(),
            'parametrized': self._load_parametrized_patterns()
        }
        
    def _load_initialization_patterns(self) -> Dict[str, str]:
        """Load patterns for testing initialization"""
        return {
            'basic_init': '''def test_initialization(self):
        """Test {class_name} initialization"""
        instance = {class_name}({init_args})
        {assertions}''',
            
            'init_with_mocks': '''@patch('{mock_target}')
    def test_initialization(self, mock_{mock_name}):
        """Test {class_name} initialization with mocked dependencies"""
        instance = {class_name}({init_args})
        {assertions}
        mock_{mock_name}.assert_called_once()'''
        }
        
    def _load_method_test_patterns(self) -> Dict[str, str]:
        """Load patterns for testing methods"""
        return {
            'simple_method': '''def test_{method_name}(self):
        """Test {method_name} functionality"""
        instance = self._create_instance()
        result = instance.{method_name}({method_args})
        assert result == expected_value''',
        
            'method_with_side_effects': '''def test_{method_name}_side_effects(self):
        """Test {method_name} side effects"""
        instance = self._create_instance()
        initial_state = instance.get_state()
        
        instance.{method_name}({method_args})
        
        assert instance.get_state() != initial_state''',
        
            'async_method': '''@pytest.mark.asyncio
    async def test_{method_name}(self):
        """Test async {method_name}"""
        instance = self._create_instance()
        result = await instance.{method_name}({method_args})
        assert result is not None'''
        }
        
    def _load_error_handling_patterns(self) -> Dict[str, str]:
        """Load patterns for testing error handling"""
        return {
            'exception_raised': '''def test_{method_name}_raises_on_invalid_input(self):
        """Test {method_name} raises {exception} on invalid input"""
        instance = self._create_instance()
        with pytest.raises({exception}):
            instance.{method_name}({invalid_args})''',
            
            'error_recovery': '''def test_{method_name}_error_recovery(self):
        """Test {method_name} recovers from errors"""
        instance = self._create_instance()
        instance.{dependency} = Mock(side_effect=Exception("Test error"))
        
        result = instance.{method_name}({method_args})
        
        assert result is not None  # Should handle error gracefully'''
        }
        
    def _load_mocking_patterns(self) -> Dict[str, str]:
        """Load patterns for mocking"""
        return {
            'mock_external': '''@patch('{module}.{external_class}')
    def test_{method_name}_with_mock(self, mock_{external_class}):
        """Test {method_name} with mocked external dependency"""
        mock_instance = Mock()
        mock_{external_class}.return_value = mock_instance
        mock_instance.{external_method}.return_value = {return_value}
        
        instance = self._create_instance()
        result = instance.{method_name}({method_args})
        
        mock_instance.{external_method}.assert_called_once()
        assert result == expected_value''',
        
            'mock_rabbitmq': '''@patch('pika.BlockingConnection')
    def test_{method_name}_rabbitmq(self, mock_connection):
        """Test {method_name} with RabbitMQ mocking"""
        mock_channel = Mock()
        mock_connection.return_value.channel.return_value = mock_channel
        
        instance = self._create_instance()
        instance.{method_name}({method_args})
        
        mock_channel.basic_publish.assert_called()'''
        }
        
    def _load_async_patterns(self) -> Dict[str, str]:
        """Load patterns for async testing"""
        return {
            'async_concurrent': '''@pytest.mark.asyncio
    async def test_{method_name}_concurrent(self):
        """Test concurrent execution of {method_name}"""
        instance = self._create_instance()
        tasks = [
            instance.{method_name}(data) 
            for data in test_data_list
        ]
        results = await asyncio.gather(*tasks)
        assert all(r is not None for r in results)'''
        }
        
    def _load_integration_patterns(self) -> Dict[str, str]:
        """Load patterns for integration testing"""
        return {
            'worker_communication': '''def test_{class1}_{class2}_integration(self):
        """Test integration between {class1} and {class2}"""
        instance1 = {class1}()
        instance2 = {class2}()
        
        # Connect them
        instance1.output = instance2.input
        
        # Send test data
        test_data = self._create_test_data()
        result1 = instance1.process(test_data)
        result2 = instance2.process(result1)
        
        assert result2['status'] == 'completed' '''
        }
        
    def _load_parametrized_patterns(self) -> Dict[str, str]:
        """Load patterns for parametrized testing"""
        return {
            'parametrized_inputs': '''@pytest.mark.parametrize("input_value,expected", [
        {test_cases}
    ])
    def test_{method_name}_parametrized(self, input_value, expected):
        """Test {method_name} with various inputs"""
        instance = self._create_instance()
        result = instance.{method_name}(input_value)
        assert result == expected'''
        }
        
    def get_pattern(self, pattern_type: str, pattern_name: str) -> Optional[str]:
        """Get a specific pattern"""
        return self.patterns.get(pattern_type, {}).get(pattern_name)
        
    def suggest_patterns(self, function_info: FunctionInfo) -> List[Tuple[str, str]]:
        """Suggest appropriate patterns for a function"""
        suggestions = []
        
        # Basic test
        suggestions.append(('method_test', 'simple_method'))
        
        # Async test
        if function_info.is_async:
            suggestions.append(('async', 'async_method'))
            
        # Error handling
        if function_info.raises:
            suggestions.append(('error_handling', 'exception_raised'))
            
        # Mocking for external calls
        if function_info.calls_made:
            if 'publish' in function_info.calls_made or 'basic_publish' in function_info.calls_made:
                suggestions.append(('mocking', 'mock_rabbitmq'))
            else:
                suggestions.append(('mocking', 'mock_external'))
                
        # Parametrized for simple functions
        if function_info.complexity <= 3 and len(function_info.args) <= 2:
            suggestions.append(('parametrized', 'parametrized_inputs'))
            
        return suggestions


class TestTemplateEngine:
    """Engine for generating test code from templates"""
    
    def __init__(self, pattern_library: PatternLibrary):
        self.pattern_library = pattern_library
        
    def generate_test_class(self, class_info: ClassInfo, module_path: Path) -> str:
        """Generate a complete test class"""
        test_code = []
        
        # Imports
        test_code.append(self._generate_imports(class_info, module_path))
        test_code.append("")
        
        # Test class definition
        test_code.append(f"class Test{class_info.name}:")
        test_code.append(f'    """Test suite for {class_info.name}"""')
        test_code.append("")
        
        # Setup method
        test_code.append(self._generate_setup_method(class_info))
        test_code.append("")
        
        # Helper to create instance
        test_code.append(self._generate_create_instance_helper(class_info))
        test_code.append("")
        
        # Test initialization
        if class_info.init_method:
            test_code.append(self._generate_init_test(class_info))
            test_code.append("")
        
        # Test each method
        for method in class_info.methods:
            if method.name.startswith('_') and method.name != '__init__':
                continue  # Skip private methods
                
            method_tests = self._generate_method_tests(method, class_info)
            for test in method_tests:
                test_code.append(test)
                test_code.append("")
                
        return "\n".join(test_code)
        
    def generate_function_tests(self, function_info: FunctionInfo, module_path: Path) -> str:
        """Generate tests for standalone functions"""
        test_code = []
        
        # Generate tests based on suggested patterns
        suggestions = self.pattern_library.suggest_patterns(function_info)
        
        for pattern_type, pattern_name in suggestions:
            pattern = self.pattern_library.get_pattern(pattern_type, pattern_name)
            if pattern:
                test = self._apply_pattern(pattern, function_info)
                test_code.append(test)
                test_code.append("")
                
        return "\n".join(test_code)
        
    def _generate_imports(self, class_info: ClassInfo, module_path: Path) -> str:
        """Generate import statements"""
        imports = [
            "import pytest",
            "from unittest.mock import Mock, patch, MagicMock",
            "import sys",
            "from pathlib import Path",
            "",
            "# Add project root to path",
            "sys.path.insert(0, str(Path(__file__).parent.parent.parent))",
            "",
        ]
        
        # Import the module being tested
        module_import = str(module_path).replace('/', '.').replace('.py', '')
        if module_import.startswith('.'):
            module_import = module_import[1:]
            
        imports.append(f"from {module_import} import {class_info.name}")
        
        return "\n".join(imports)
        
    def _generate_setup_method(self, class_info: ClassInfo) -> str:
        """Generate setup method"""
        return '''    def setup_method(self):
        """Setup for each test method"""
        self.test_data = self._create_test_data()'''
        
    def _generate_create_instance_helper(self, class_info: ClassInfo) -> str:
        """Generate helper method to create instances"""
        if class_info.is_abstract:
            return f'''    def _create_instance(self):
        """Create a concrete instance for testing"""
        class Concrete{class_info.name}({class_info.name}):
            pass
            
        return Concrete{class_info.name}()'''
        else:
            # Generate default args based on init method
            if class_info.init_method:
                args = []
                for i, arg in enumerate(class_info.init_method.args):
                    if i < len(class_info.init_method.defaults):
                        continue  # Has default
                    args.append(f"{arg}=None")
                args_str = ", ".join(args)
            else:
                args_str = ""
                
            return f'''    def _create_instance(self):
        """Create instance for testing"""
        return {class_info.name}({args_str})'''
        
    def _generate_init_test(self, class_info: ClassInfo) -> str:
        """Generate initialization test"""
        pattern = self.pattern_library.get_pattern('initialization', 'basic_init')
        
        # Build assertions based on init parameters
        assertions = []
        if class_info.init_method:
            for arg in class_info.init_method.args:
                assertions.append(f"        assert hasattr(instance, '{arg}')")
                
        return pattern.format(
            class_name=class_info.name,
            init_args="",  # Will be filled based on actual requirements
            assertions="\n".join(assertions) if assertions else "        assert instance is not None"
        )
        
    def _generate_method_tests(self, method: FunctionInfo, class_info: ClassInfo) -> List[str]:
        """Generate tests for a method"""
        tests = []
        
        # Get suggested patterns
        suggestions = self.pattern_library.suggest_patterns(method)
        
        for pattern_type, pattern_name in suggestions[:3]:  # Limit to 3 tests per method
            pattern = self.pattern_library.get_pattern(pattern_type, pattern_name)
            if pattern:
                test = self._apply_pattern(pattern, method, class_info)
                tests.append(test)
                
        return tests
        
    def _apply_pattern(self, pattern: str, function_info: FunctionInfo, class_info: Optional[ClassInfo] = None) -> str:
        """Apply a pattern template with actual values"""
        # Build method args
        method_args = ", ".join([f"test_{arg}" for arg in function_info.args])
        
        # Handle exceptions
        exception = list(function_info.raises)[0] if function_info.raises else "Exception"
        
        # Handle external calls
        external_calls = list(function_info.calls_made)
        external_class = external_calls[0] if external_calls else "ExternalClass"
        
        replacements = {
            '{class_name}': class_info.name if class_info else "TestClass",
            '{method_name}': function_info.name,
            '{method_args}': method_args,
            '{init_args}': "",
            '{exception}': exception,
            '{invalid_args}': "None",  # Simplified
            '{mock_target}': "'external.module'",
            '{mock_name}': "dependency",
            '{dependency}': "connection",
            '{external_class}': external_class,
            '{external_method}': "execute",
            '{return_value}': "{'status': 'success'}",
            '{module}': "libs",
            '{test_cases}': self._generate_test_cases(function_info),
            '{class1}': "Worker1",
            '{class2}': "Worker2"
        }
        
        result = pattern
        for key, value in replacements.items():
            result = result.replace(key, value)
            
        return result
        
    def _generate_test_cases(self, function_info: FunctionInfo) -> str:
        """Generate test cases for parametrized testing"""
        # Simple example test cases
        cases = [
            '("input1", "expected1")',
            '("input2", "expected2")',
            '("", "")',
            '(None, None)'
        ]
        return ",\n        ".join(cases)
        
    def _create_test_data(self) -> str:
        """Generate test data creation"""
        return '''    def _create_test_data(self):
        """Create test data"""
        return {
            'task_id': 'test-123',
            'type': 'test',
            'data': {'test': True}
        }'''


class CoverageGapAnalyzer:
    """Analyzes coverage gaps and prioritizes modules for testing"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.coverage_data = self._load_coverage_data()
        
    def _load_coverage_data(self) -> Dict[str, float]:
        """Load existing coverage data"""
        coverage_file = self.project_root / "coverage.json"
        if coverage_file.exists():
            with open(coverage_file, 'r') as f:
                data = json.load(f)
                return data.get('files', {})
        return {}
        
    def identify_gaps(self, threshold: float = 70.0) -> List[Tuple[Path, float]]:
        """Identify modules with coverage below threshold"""
        gaps = []
        
        for module_path, coverage in self.coverage_data.items():
            if coverage < threshold:
                full_path = self.project_root / module_path
                if full_path.exists():
                    gaps.append((full_path, coverage))
                    
        # Sort by coverage (lowest first) and complexity
        gaps.sort(key=lambda x: x[1])
        return gaps
        
    def prioritize_modules(self, gaps: List[Tuple[Path, float]]) -> List[Tuple[Path, float, int]]:
        """Prioritize modules based on coverage and importance"""
        prioritized = []
        
        for path, coverage in gaps:
            # Calculate priority score
            priority = self._calculate_priority(path, coverage)
            prioritized.append((path, coverage, priority))
            
        # Sort by priority (highest first)
        prioritized.sort(key=lambda x: x[2], reverse=True)
        return prioritized
        
    def _calculate_priority(self, path: Path, coverage: float) -> int:
        """Calculate priority score for a module"""
        score = 100 - coverage  # Base score from lack of coverage
        
        # Boost score for core modules
        if 'core' in str(path):
            score += 50
        elif 'libs' in str(path):
            score += 30
        elif 'workers' in str(path):
            score += 40
            
        # Boost for commonly used modules
        module_name = path.stem
        if module_name in ['base_worker', 'base_manager', 'config', 'queue_manager']:
            score += 60
            
        return int(score)


class AutoTestGenerator:
    """Main class for automated test generation"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.ast_analyzer = ASTAnalyzer()
        self.pattern_library = PatternLibrary()
        self.template_engine = TestTemplateEngine(self.pattern_library)
        self.coverage_analyzer = CoverageGapAnalyzer(self.project_root)
        
    def generate_tests_for_module(self, module_path: Path) -> Dict[str, str]:
        """Generate tests for a specific module"""
        print(f"Analyzing module: {module_path}")
        
        # Analyze module
        module_info = self.ast_analyzer.analyze_module(module_path)
        
        tests = {}
        
        # Generate tests for classes
        for class_info in module_info.classes:
            print(f"  Generating tests for class: {class_info.name}")
            test_code = self.template_engine.generate_test_class(class_info, module_path)
            test_name = f"test_{class_info.name.lower()}_generated.py"
            tests[test_name] = test_code
            
        # Generate tests for standalone functions
        if module_info.functions:
            print(f"  Generating tests for {len(module_info.functions)} functions")
            function_tests = []
            for func in module_info.functions:
                func_tests = self.template_engine.generate_function_tests(func, module_path)
                if func_tests:
                    function_tests.append(func_tests)
                    
            if function_tests:
                test_name = f"test_{module_path.stem}_functions_generated.py"
                tests[test_name] = "\n\n".join(function_tests)
                
        return tests
        
    def learn_from_existing_tests(self) -> Dict[str, Any]:
        """Analyze existing high-coverage tests to extract patterns"""
        print("Learning from existing successful tests...")
        
        # Find test files with high coverage
        high_coverage_tests = [
            self.project_root / "tests/unit/core/test_monitoring_mixin.py",
            self.project_root / "tests/unit/libs/test_queue_manager.py",
            self.project_root / "tests/unit/core/test_base_worker_phase6_tdd.py"
        ]
        
        patterns_found = defaultdict(list)
        
        for test_file in high_coverage_tests:
            if test_file.exists():
                print(f"  Analyzing: {test_file.name}")
                
                # Analyze test structure
                with open(test_file, 'r') as f:
                    content = f.read()
                    
                # Extract patterns (simplified for demonstration)
                if "@patch" in content:
                    patterns_found['mocking'].append("Uses @patch decorator extensively")
                if "pytest.raises" in content:
                    patterns_found['error_handling'].append("Tests exception cases")
                if "@pytest.mark.parametrize" in content:
                    patterns_found['parametrized'].append("Uses parametrized tests")
                if "assert_called" in content:
                    patterns_found['verification'].append("Verifies mock calls")
                    
        return dict(patterns_found)
        
    def generate_for_coverage_gaps(self, max_modules: int = 3) -> Dict[str, Dict[str, str]]:
        """Generate tests for modules with lowest coverage"""
        print("Identifying coverage gaps...")
        
        # Get modules with low coverage
        gaps = self.coverage_analyzer.identify_gaps(threshold=70.0)
        prioritized = self.coverage_analyzer.prioritize_modules(gaps)
        
        all_tests = {}
        
        for i, (module_path, coverage, priority) in enumerate(prioritized[:max_modules]):
            print(f"\nModule {i+1}: {module_path.name}")
            print(f"  Current coverage: {coverage:.1f}%")
            print(f"  Priority score: {priority}")
            
            try:
                tests = self.generate_tests_for_module(module_path)
                if tests:
                    all_tests[str(module_path)] = tests
            except Exception as e:
                print(f"  Error generating tests: {e}")
                
        return all_tests
        
    def save_generated_tests(self, tests: Dict[str, Dict[str, str]], output_dir: Path) -> List[Path]:
        """Save generated tests to files"""
        saved_files = []
        
        for module_path, test_files in tests.items():
            # Create directory structure
            module_parts = Path(module_path).parts
            if 'ai_co' in module_parts:
                idx = module_parts.index('ai_co')
                relative_parts = module_parts[idx+1:-1]  # Exclude filename
            else:
                relative_parts = module_parts[:-1]
                
            test_dir = output_dir / "tests" / "generated" / Path(*relative_parts)
            test_dir.mkdir(parents=True, exist_ok=True)
            
            # Save each test file
            for test_name, test_content in test_files.items():
                test_path = test_dir / test_name
                with open(test_path, 'w') as f:
                    f.write(test_content)
                saved_files.append(test_path)
                print(f"  Saved: {test_path}")
                
        return saved_files
        
    def generate_coverage_report(self, generated_files: List[Path]) -> str:
        """Generate a report on the test generation results"""
        report = [
            "# Automated Test Generation Report",
            f"\nGenerated at: {Path.cwd()}",
            f"\nTotal test files generated: {len(generated_files)}",
            "\n## Generated Test Files:",
        ]
        
        for file_path in generated_files:
            report.append(f"- {file_path}")
            
        report.extend([
            "\n## Pattern Library Used:",
            "- Initialization patterns",
            "- Method testing patterns", 
            "- Error handling patterns",
            "- Mocking patterns",
            "- Async testing patterns",
            "- Integration patterns",
            "- Parametrized testing patterns",
            "\n## Next Steps:",
            "1. Review generated tests",
            "2. Run tests to verify they work",
            "3. Adjust test data and assertions as needed",
            "4. Measure coverage improvement"
        ])
        
        return "\n".join(report)


def main():
    """Main entry point for test generation"""
    print("=== AI Company Automated Test Generator ===\n")
    
    # Initialize generator
    generator = AutoTestGenerator()
    
    # Learn from existing tests
    print("Phase 1: Learning from existing successful tests")
    patterns = generator.learn_from_existing_tests()
    print(f"Learned patterns: {list(patterns.keys())}")
    
    # Generate tests for coverage gaps
    print("\nPhase 2: Generating tests for low-coverage modules")
    all_tests = generator.generate_for_coverage_gaps(max_modules=3)
    
    # Save generated tests
    print("\nPhase 3: Saving generated tests")
    output_dir = Path.cwd()
    saved_files = generator.save_generated_tests(all_tests, output_dir)
    
    # Generate report
    print("\nPhase 4: Generating report")
    report = generator.generate_coverage_report(saved_files)
    
    report_path = output_dir / "test_generation_report.md"
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"Report saved to: {report_path}")
    
    print("\n=== Test Generation Complete ===")
    print(f"Generated {len(saved_files)} test files")
    print("Run pytest on generated tests to verify and measure coverage improvement")


if __name__ == "__main__":
    main()