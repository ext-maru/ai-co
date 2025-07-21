#!/usr/bin/env python3
"""
🛡️ Servant Inspector Magic テストスイート
サーバント査察魔法の完全テスト
"""

import asyncio
import json
import logging
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock

import pytest

# プロジェクトルートをパスに追加
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.ancient_elder.servant_inspector import (
    ServantInspector,
    ServantImplementationAnalyzer,
    ServantCollaborationAnalyzer,
    ServantType,
    ServantViolationType
)
from libs.ancient_elder.base import ViolationSeverity


class TestServantImplementationAnalyzer(unittest.TestCase):
    """サーバント実装品質分析システムテスト"""
    
    def setUp(self):
        """テスト環境セットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.analyzer = ServantImplementationAnalyzer(self.project_root)
        
    def tearDown(self):
        """テスト環境クリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def test_analyzer_initialization(self):
        """アナライザーの初期化テスト"""
        self.assertIsInstance(self.analyzer, ServantImplementationAnalyzer)
        self.assertEqual(self.analyzer.project_root, self.project_root)
        
        # スタブパターンが設定されていることを確認
        self.assertIn("pass_only", self.analyzer.stub_patterns)
        self.assertIn("todo_comment", self.analyzer.stub_patterns)
        self.assertIn("not_implemented", self.analyzer.stub_patterns)
        
        # サーバント役割が設定されていることを確認
        self.assertIn(ServantType.CODE_CRAFTSMAN, self.analyzer.servant_roles)
        self.assertIn(ServantType.TEST_GUARDIAN, self.analyzer.servant_roles)
        
    def test_servant_type_detection(self):
        """サーバントタイプ検出テスト"""
        test_files = [
            ("code_craftsman.py", ServantType.CODE_CRAFTSMAN),
            ("test_guardian.py", ServantType.TEST_GUARDIAN),
            ("quality_inspector.py", ServantType.QUALITY_INSPECTOR),
            ("deployment_master.py", ServantType.DEPLOYMENT_MASTER),
            ("monitor_watcher.py", ServantType.MONITOR_WATCHER),
            ("doc_scribe.py", ServantType.DOC_SCRIBE),
            ("random_file.py", ServantType.CODE_CRAFTSMAN),  # デフォルト
        ]
        
        for file_name, expected_type in test_files:
            detected_type = self.analyzer._detect_servant_type(file_name)
            self.assertEqual(detected_type, expected_type, 
                           f"Failed to detect type for {file_name}")
                           
    def test_stub_implementation_detection(self):
        """スタブ実装検出テスト"""
        test_code = """
def function_with_pass():
    pass

def function_with_todo():
    # TODO: Implement this function
    return None

def function_with_not_implemented():
    raise NotImplementedError("This is not implemented yet")

def function_with_placeholder():
    return "placeholder result"

def proper_function():
    result = calculate_something()
    return result
"""
        
        violations = self.analyzer._detect_stub_implementations(test_code, "test.py")
        
        # 4つのスタブ実装が検出されることを確認
        self.assertGreaterEqual(len(violations), 3)
        
        # 各違反タイプを確認
        violation_types = [v["pattern"] for v in violations]
        self.assertIn("pass_only", violation_types)
        self.assertIn("todo_comment", violation_types)
        self.assertIn("not_implemented", violation_types)
        
    def test_lazy_implementation_detection(self):
        """手抜き実装検出テスト"""
        test_code = """
def hardcoded_function():
    return "hardcoded string"

def simple_return():
    return True

def minimal_function():
    return 42

def proper_function():
    try:
        result = complex_calculation()
        validate_result(result)
        return result
    except Exception as e:
        handle_error(e)
        return None
"""
        
        violations = self.analyzer._detect_lazy_implementations(test_code, "test.py")
        
        # 手抜き実装が検出されることを確認
        self.assertGreater(len(violations), 0)
        
        # 違反タイプを確認
        for violation in violations:
            self.assertEqual(violation["type"], ServantViolationType.LAZY_IMPLEMENTATION)
            self.assertIn(violation["severity"], ["LOW", "MEDIUM", "HIGH"])
            
    def test_role_compliance_check(self):
        """役割遵守チェックテスト"""
        # テスト用のソース解析結果
        source_analysis = {
            "content": """
def craft_code():
    \"\"\"Code crafting implementation\"\"\"
    return create_beautiful_code()

def implement_feature():
    \"\"\"Feature implementation\"\"\"
    return build_feature()

def some_other_function():
    pass
""",
            "ast_analysis": {
                "functions": [
                    {"name": "craft_code", "args_count": 0, "has_docstring": True},
                    {"name": "implement_feature", "args_count": 0, "has_docstring": True},
                    {"name": "some_other_function", "args_count": 0, "has_docstring": False}
                ]
            }
        }
        
        # CODE_CRAFTSMANの役割遵守チェック
        compliance = self.analyzer._check_role_compliance(
            source_analysis, ServantType.CODE_CRAFTSMAN, "craftsman.py"
        )
        
        self.assertIsInstance(compliance, dict)
        self.assertIn("compliant", compliance)
        self.assertIn("score", compliance)
        self.assertIn("violations", compliance)
        
        # 適切な実装の場合は高いスコアになることを確認
        if compliance["compliant"]:
            self.assertGreaterEqual(compliance["score"], 70.0)
            
    def test_expertise_evaluation(self):
        """専門性評価テスト"""
        # 高品質な実装例
        high_quality_analysis = {
            "has_docstrings": True,
            "has_type_hints": True,
            "lines_of_code": 150,
            "ast_analysis": {
                "functions": [
                    {"args_count": 3},
                    {"args_count": 2},
                    {"args_count": 4}
                ],
                "total_imports": 5
            }
        }
        
        expertise_score = self.analyzer._evaluate_expertise(high_quality_analysis, ServantType.CODE_CRAFTSMAN)
        self.assertGreaterEqual(expertise_score, 60.0)
        
        # 低品質な実装例
        low_quality_analysis = {
            "has_docstrings": False,
            "has_type_hints": False,
            "lines_of_code": 10,
            "ast_analysis": {
                "functions": [
                    {"args_count": 0}
                ],
                "total_imports": 0
            }
        }
        
        low_expertise_score = self.analyzer._evaluate_expertise(low_quality_analysis, ServantType.CODE_CRAFTSMAN)
        self.assertLess(low_expertise_score, expertise_score)
        
    def test_servant_quality_score_calculation(self):
        """サーバント品質スコア計算テスト"""
        # 高品質なサーバント
        high_quality_score = self.analyzer._calculate_servant_quality_score(
            stub_violations=[],  # スタブなし
            lazy_violations=[],  # 手抜きなし
            role_compliance={"score": 90.0},  # 高い役割遵守
            expertise_score=85.0  # 高い専門性
        )
        self.assertGreaterEqual(high_quality_score, 80.0)
        
        # 低品質なサーバント
        low_quality_score = self.analyzer._calculate_servant_quality_score(
            stub_violations=[{"type": "stub"}] * 3,  # 多数のスタブ
            lazy_violations=[{"type": "lazy"}] * 2,  # 手抜き実装
            role_compliance={"score": 30.0},  # 低い役割遵守
            expertise_score=20.0  # 低い専門性
        )
        self.assertLess(low_quality_score, high_quality_score)
        
    def test_source_code_analysis(self):
        """ソースコード解析テスト"""
        # テストファイル作成
        test_file = self.project_root / "test_servant.py"
        test_file.write_text("""
'''Test servant implementation'''

import os
from typing import Dict, Any

class TestServant:
    '''Test servant class'''
    
    def __init__(self):
        pass
        
    def process_data(self, data: Dict[str, Any]) -> str:
        '''Process data method'''
        return str(data)
        
async def async_function():
    '''Async function'''
    return "async result"
""")
        
        analysis = self.analyzer._analyze_source_code(str(test_file))
        
        self.assertIn("content", analysis)
        self.assertIn("lines_of_code", analysis)
        self.assertIn("ast_analysis", analysis)
        self.assertTrue(analysis["has_docstrings"])
        self.assertTrue(analysis["has_type_hints"])
        self.assertGreater(analysis["lines_of_code"], 10)
        
        # AST解析結果を確認
        ast_analysis = analysis["ast_analysis"]
        self.assertGreater(ast_analysis["total_functions"], 0)
        self.assertGreater(ast_analysis["total_classes"], 0)
        self.assertGreater(ast_analysis["total_imports"], 0)


class TestServantCollaborationAnalyzer(unittest.TestCase):
    """サーバント間協調分析システムテスト"""
    
    def setUp(self):
        """テスト環境セットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.analyzer = ServantCollaborationAnalyzer(self.project_root)
        
        # テスト用サーバントファイル作成
        self.servant_files = []
        self._create_test_servant_files()
        
    def tearDown(self):
        """テスト環境クリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def _create_test_servant_files(self):
        """テスト用サーバントファイルを作成"""
        # Code Craftsman (他のサーバントを使用)
        craftsman_file = self.project_root / "code_craftsman.py"
        craftsman_file.write_text("""
from test_guardian import TestGuardian
from quality_inspector import QualityInspector

class CodeCraftsman:
    def craft_code(self):
        guardian = TestGuardian()
        inspector = QualityInspector()
        return "crafted code"
""")
        self.servant_files.append(str(craftsman_file))
        
        # Test Guardian (孤立した実装)
        guardian_file = self.project_root / "test_guardian.py"
        guardian_file.write_text("""
class TestGuardian:
    def guard_tests(self):
        return "guarded tests"
""")
        self.servant_files.append(str(guardian_file))
        
        # Quality Inspector (一部協調)
        inspector_file = self.project_root / "quality_inspector.py"
        inspector_file.write_text("""
from test_guardian import TestGuardian

class QualityInspector:
    def inspect_quality(self):
        guardian = TestGuardian()
        return "quality report"
""")
        self.servant_files.append(str(inspector_file))
        
    def test_analyzer_initialization(self):
        """アナライザーの初期化テスト"""
        self.assertIsInstance(self.analyzer, ServantCollaborationAnalyzer)
        self.assertEqual(self.analyzer.project_root, self.project_root)
        
    def test_dependency_analysis(self):
        """依存関係分析テスト"""
        dependencies = self.analyzer._analyze_dependencies(self.servant_files)
        
        self.assertEqual(len(dependencies), len(self.servant_files))
        
        # 各ファイルの依存関係を確認
        for file_path in self.servant_files:
            self.assertIn(file_path, dependencies)
            dep_info = dependencies[file_path]
            self.assertIn("imports", dep_info)
            self.assertIn("import_count", dep_info)
            
        # 協調関係を確認
        craftsman_deps = dependencies[str(self.project_root / "code_craftsman.py")]
        self.assertGreater(craftsman_deps["import_count"], 0, "Code Craftsman should have dependencies")
        
    def test_collaboration_patterns_detection(self):
        """協調パターン検出テスト"""
        patterns = self.analyzer._detect_collaboration_patterns(self.servant_files)
        
        self.assertIsInstance(patterns, list)
        self.assertGreater(len(patterns), 0, "Should detect at least one collaboration pattern")
        
        # パターンの構造を確認
        for pattern in patterns:
            self.assertIn("pattern", pattern)
            self.assertIn("description", pattern)
            self.assertIn("quality", pattern)
            
    def test_collaboration_quality_evaluation(self):
        """協調品質評価テスト"""
        dependencies = self.analyzer._analyze_dependencies(self.servant_files)
        patterns = self.analyzer._detect_collaboration_patterns(self.servant_files)
        
        quality = self.analyzer._evaluate_collaboration_quality(dependencies, patterns)
        
        self.assertIn("quality_score", quality)
        self.assertIn("collaboration_ratio", quality)
        self.assertIn("total_dependencies", quality)
        
        self.assertGreaterEqual(quality["quality_score"], 0.0)
        self.assertLessEqual(quality["quality_score"], 100.0)
        
    def test_collaboration_violations_detection(self):
        """協調違反検出テスト"""
        dependencies = self.analyzer._analyze_dependencies(self.servant_files)
        patterns = self.analyzer._detect_collaboration_patterns(self.servant_files)
        
        violations = self.analyzer._detect_collaboration_violations(
            dependencies, patterns, self.servant_files
        )
        
        # 孤立したサーバント（test_guardian）が検出されることを確認
        isolated_violations = [
            v for v in violations 
            if v.get("type") == ServantViolationType.POOR_COLLABORATION
        ]
        self.assertGreater(len(isolated_violations), 0, "Should detect isolated servants")
        
    def test_collaboration_score_calculation(self):
        """協調スコア計算テスト"""
        # 高協調品質のケース
        high_quality = {"quality_score": 80.0}
        high_violations = []
        
        high_score = self.analyzer._calculate_collaboration_score(high_quality, high_violations)
        self.assertGreaterEqual(high_score, 70.0)
        
        # 低協調品質のケース
        low_quality = {"quality_score": 30.0}
        low_violations = [{"type": "violation"}] * 3
        
        low_score = self.analyzer._calculate_collaboration_score(low_quality, low_violations)
        self.assertLess(low_score, high_score)


class TestServantInspector(unittest.TestCase):
    """サーバント査察魔法総合テスト"""
    
    def setUp(self):
        """テスト環境セットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.inspector = ServantInspector(self.project_root)
        
        # テスト用サーバントファイル作成
        self._create_test_servants()
        
    def tearDown(self):
        """テスト環境クリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def _create_test_servants(self):
        """テスト用サーバント作成"""
        # 高品質サーバント
        good_servant = self.project_root / "good_craftsman.py"
        good_servant.write_text("""
'''High quality code craftsman servant'''

from typing import Dict, Any
import logging

class GoodCraftsman:
    '''Professional code craftsman'''
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def craft_code(self, requirements: Dict[str, Any]) -> str:
        '''Craft high quality code based on requirements'''
        try:
            self.logger.info("Starting code crafting")
            code = self._generate_code(requirements)
            self._validate_code(code)
            return code
        except Exception as e:
            self.logger.error(f"Code crafting failed: {e}")
            raise
            
    def implement_feature(self, feature_spec: str) -> bool:
        '''Implement feature according to specification'''
        if not feature_spec:
            raise ValueError("Feature specification is required")
        # Implementation logic here
        return True
        
    def _generate_code(self, requirements: Dict[str, Any]) -> str:
        '''Generate code implementation'''
        return "generated_code"
        
    def _validate_code(self, code: str) -> None:
        '''Validate generated code'''
        if not code:
            raise ValueError("Code cannot be empty")
""")
        
        # 低品質サーバント（スタブ多数）
        bad_servant = self.project_root / "bad_craftsman.py"
        bad_servant.write_text("""
class BadCraftsman:
    def craft_code(self):
        # TODO: Implement this
        pass
        
    def implement_feature(self):
        raise NotImplementedError("Not implemented yet")
        
    def build_component(self):
        return "placeholder"
""")
        
    def test_inspector_initialization(self):
        """インスペクターの初期化テスト"""
        self.assertIsInstance(self.inspector, ServantInspector)
        self.assertEqual(self.inspector.project_root, self.project_root)
        self.assertIsInstance(self.inspector.implementation_analyzer, ServantImplementationAnalyzer)
        self.assertIsInstance(self.inspector.collaboration_analyzer, ServantCollaborationAnalyzer)
        
    def test_get_audit_scope(self):
        """監査スコープ取得テスト"""
        scope = self.inspector.get_audit_scope()
        
        self.assertIsInstance(scope, list)
        self.assertIn("servant_implementation_quality", scope)
        self.assertIn("servant_role_compliance", scope)
        self.assertIn("servant_collaboration", scope)
        self.assertIn("servant_expertise_evaluation", scope)
        
    def test_discover_servant_files(self):
        """サーバントファイル発見テスト"""
        servant_files = self.inspector._discover_servant_files(str(self.project_root))
        
        self.assertGreater(len(servant_files), 0, "Should discover servant files")
        
        # 作成したファイルが発見されることを確認
        file_names = [Path(f).name for f in servant_files]
        self.assertIn("good_craftsman.py", file_names)
        self.assertIn("bad_craftsman.py", file_names)
        
    @patch.object(ServantImplementationAnalyzer, 'analyze_servant_implementation')
    @patch.object(ServantCollaborationAnalyzer, 'analyze_servant_collaboration')
    async def test_execute_audit_success(self, mock_collaboration, mock_implementation):
        """監査実行成功テスト"""
        # モックレスポンス設定
        mock_implementation.return_value = {
            "stub_violations": [],
            "lazy_violations": [],
            "role_compliance": {"violations": []},
            "overall_quality_score": 85.0
        }
        
        mock_collaboration.return_value = {
            "collaboration_violations": [],
            "overall_collaboration_score": 80.0
        }
        
        result = await self.inspector.execute_audit(str(self.project_root))
        
        self.assertEqual(result.auditor_name, "ServantInspector")
        self.assertIsInstance(result.violations, list)
        self.assertIsInstance(result.metrics, dict)
        self.assertIn("overall_servant_score", result.metrics)
        self.assertGreater(result.metrics["overall_servant_score"], 70.0)
        
    async def test_execute_audit_no_servants(self):
        """サーバントなしの場合の監査テスト"""
        # 空のディレクトリで監査実行
        empty_dir = self.temp_dir / "empty"
        empty_dir.mkdir()
        
        result = await self.inspector.execute_audit(str(empty_dir))
        
        self.assertEqual(result.auditor_name, "ServantInspector")
        self.assertEqual(result.metrics["servant_files_found"], 0)
        self.assertIn("Create elder servant implementations", result.recommendations)
        
    @patch.object(ServantImplementationAnalyzer, 'analyze_servant_implementation')
    @patch.object(ServantCollaborationAnalyzer, 'analyze_servant_collaboration')
    async def test_execute_audit_with_violations(self, mock_collaboration, mock_implementation):
        """違反検出時の監査実行テスト"""
        # 違反を含むモックレスポンス設定
        mock_implementation.return_value = {
            "stub_violations": [
                {
                    "type": ServantViolationType.STUB_IMPLEMENTATION,
                    "severity": "HIGH",
                    "description": "Stub implementation detected"
                }
            ],
            "lazy_violations": [
                {
                    "type": ServantViolationType.LAZY_IMPLEMENTATION,
                    "severity": "MEDIUM",
                    "description": "Lazy implementation detected"
                }
            ],
            "role_compliance": {
                "violations": [
                    {
                        "type": ServantViolationType.ROLE_VIOLATION,
                        "severity": "HIGH",
                        "description": "Role violation detected"
                    }
                ]
            },
            "overall_quality_score": 30.0
        }
        
        mock_collaboration.return_value = {
            "collaboration_violations": [
                {
                    "type": ServantViolationType.POOR_COLLABORATION,
                    "severity": "MEDIUM",
                    "description": "Poor collaboration detected"
                }
            ],
            "overall_collaboration_score": 25.0
        }
        
        result = await self.inspector.execute_audit(str(self.project_root))
        
        # 違反が適切に統合されることを確認
        self.assertEqual(len(result.violations), 4)
        self.assertLessEqual(result.metrics["overall_servant_score"], 40.0)
        
    def test_overall_servant_score_calculation(self):
        """総合サーバントスコア計算テスト"""
        # 高品質実装結果
        high_implementation_results = [
            {"overall_quality_score": 90.0},
            {"overall_quality_score": 85.0}
        ]
        high_collaboration_result = {"overall_collaboration_score": 80.0}
        
        high_score = self.inspector._calculate_overall_servant_score(
            high_implementation_results, high_collaboration_result
        )
        self.assertGreaterEqual(high_score, 80.0)
        
        # 低品質実装結果
        low_implementation_results = [
            {"overall_quality_score": 30.0},
            {"overall_quality_score": 25.0}
        ]
        low_collaboration_result = {"overall_collaboration_score": 20.0}
        
        low_score = self.inspector._calculate_overall_servant_score(
            low_implementation_results, low_collaboration_result
        )
        self.assertLess(low_score, high_score)
        
    def test_servant_improvement_recommendations(self):
        """サーバント改善提案生成テスト"""
        implementation_results = [{"overall_quality_score": 60.0}]
        collaboration_result = {"overall_collaboration_score": 50.0}
        violations = [
            {"type": ServantViolationType.STUB_IMPLEMENTATION},
            {"type": ServantViolationType.ROLE_VIOLATION}
        ]
        
        recommendations = self.inspector._generate_servant_improvement_recommendations(
            implementation_results, collaboration_result, violations
        )
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0, "Should generate improvement recommendations")
        
        # 実装品質改善の提案が含まれることを確認
        quality_recommendations = [r for r in recommendations if "implementation quality" in r.lower()]
        self.assertGreater(len(quality_recommendations), 0)


class TestServantInspectorIntegration(unittest.TestCase):
    """サーバント査察魔法統合テスト"""
    
    def setUp(self):
        """テスト環境セットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.inspector = ServantInspector(self.project_root)
        
    def tearDown(self):
        """テスト環境クリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    async def test_comprehensive_servant_audit(self):
        """包括的サーバント監査テスト"""
        # 複数のサーバントファイルを作成
        servants_dir = self.project_root / "servants"
        servants_dir.mkdir()
        
        # Code Craftsman
        (servants_dir / "code_craftsman.py").write_text("""
class CodeCraftsman:
    def craft_code(self):
        return "crafted code"
    
    def implement_feature(self):
        return True
""")
        
        # Test Guardian (スタブ実装)
        (servants_dir / "test_guardian.py").write_text("""
class TestGuardian:
    def guard_tests(self):
        # TODO: Implement test guarding
        pass
        
    def verify_quality(self):
        raise NotImplementedError("Not implemented")
""")
        
        result = await self.inspector.execute_audit(str(servants_dir))
        
        # 結果検証
        self.assertEqual(result.auditor_name, "ServantInspector")
        self.assertIsInstance(result.violations, list)
        self.assertIsInstance(result.metrics, dict)
        self.assertIn("overall_servant_score", result.metrics)
        self.assertGreater(result.metrics["servant_files_analyzed"], 0)
        
        # スタブ実装違反が検出されることを確認
        stub_violations = [
            v for v in result.violations 
            if v.get("type") == ServantViolationType.STUB_IMPLEMENTATION
        ]
        self.assertGreater(len(stub_violations), 0, "Should detect stub implementations")
        
    async def test_servant_quality_comparison(self):
        """サーバント品質比較テスト"""
        # 高品質ディレクトリ
        high_quality_dir = self.project_root / "high_quality"
        high_quality_dir.mkdir()
        
        (high_quality_dir / "excellent_craftsman.py").write_text("""
'''Excellent code craftsman implementation'''

from typing import Dict, Any, Optional
import logging

class ExcellentCraftsman:
    '''Professional code craftsman with high expertise'''
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def craft_code(self, requirements: Dict[str, Any]) -> str:
        '''Craft high quality code based on requirements'''
        self.logger.info("Crafting code with requirements")
        return self._generate_professional_code(requirements)
        
    def implement_feature(self, feature: str) -> bool:
        '''Implement feature with proper validation'''
        if not feature:
            raise ValueError("Feature specification required")
        return True
        
    def _generate_professional_code(self, requirements: Dict[str, Any]) -> str:
        '''Generate professional code implementation'''
        return "professional_code"
""")
        
        # 低品質ディレクトリ
        low_quality_dir = self.project_root / "low_quality"
        low_quality_dir.mkdir()
        
        (low_quality_dir / "poor_craftsman.py").write_text("""
class PoorCraftsman:
    def craft_code(self):
        pass
        
    def implement_feature(self):
        return "hardcoded"
""")
        
        # 両方を監査
        high_result = await self.inspector.execute_audit(str(high_quality_dir))
        low_result = await self.inspector.execute_audit(str(low_quality_dir))
        
        # 高品質サーバントの方が高いスコアであることを確認
        high_score = high_result.metrics["overall_servant_score"]
        low_score = low_result.metrics["overall_servant_score"]
        
        self.assertGreater(high_score, low_score, "High quality servant should have higher score")
        self.assertGreater(len(low_result.violations), len(high_result.violations), 
                          "Low quality servant should have more violations")


if __name__ == "__main__":
    # 基本テスト実行
    unittest.main(verbosity=2)