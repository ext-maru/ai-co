#!/usr/bin/env python3
"""
🔴🟢🔵 TDD Guardian Magic テストスイート
TDD守護監査魔法の完全テスト
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

from libs.ancient_elder.tdd_guardian import (
    TDDGuardian,
    TDDCycleTracker,
    TestQualityAnalyzer,
    CoverageManipulationDetector,
    TDDCyclePhase,
    TDDViolationType
)
from libs.ancient_elder.base import ViolationSeverity


class TestTDDCycleTracker(unittest.TestCase):
    """TDDサイクル実行トラッカーテスト"""
    
    def setUp(self):
        """テスト環境セットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.tracker = TDDCycleTracker(self.project_root)
        
    def tearDown(self):
        """テスト環境クリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def test_tracker_initialization(self):
        """トラッカーの初期化テスト"""
        self.assertIsInstance(self.tracker, TDDCycleTracker)
        self.assertEqual(self.tracker.project_root, self.project_root)
        self.assertIsNotNone(self.tracker.git_patterns)
        
        # 各TDDフェーズのパターンが存在することを確認
        self.assertIn(TDDCyclePhase.RED, self.tracker.git_patterns)
        self.assertIn(TDDCyclePhase.GREEN, self.tracker.git_patterns)
        self.assertIn(TDDCyclePhase.REFACTOR, self.tracker.git_patterns)
        
    def test_tdd_phase_detection(self):
        """TDDフェーズ検出テスト"""
        test_cases = [
            ("🔴 Red: Add failing test for user authentication", TDDCyclePhase.RED),
            ("🟢 Green: Implement basic auth to pass tests", TDDCyclePhase.GREEN),
            ("🔵 Refactor: Clean up authentication code", TDDCyclePhase.REFACTOR),
            ("feat: Add new feature", None),  # TDDフェーズなし
        ]
        
        for commit_message, expected_phase in test_cases:
            detected_phase = self.tracker._detect_tdd_phase(commit_message)
            self.assertEqual(detected_phase, expected_phase, 
                           f"Failed for message: '{commit_message}'")
            
    def test_cycle_completion_detection(self):
        """サイクル完了検出テスト"""
        # 完了したサイクル
        complete_phases = {
            TDDCyclePhase.RED: [{"message": "red phase"}],
            TDDCyclePhase.GREEN: [{"message": "green phase"}],
            TDDCyclePhase.REFACTOR: [{"message": "refactor phase"}]
        }
        self.assertTrue(self.tracker._is_cycle_complete(complete_phases))
        
        # 不完全なサイクル（リファクタリングなし）
        incomplete_phases = {
            TDDCyclePhase.RED: [{"message": "red phase"}],
            TDDCyclePhase.GREEN: [{"message": "green phase"}]
        }
        self.assertTrue(self.tracker._is_cycle_complete(incomplete_phases))  # Red+Greenで最低限完了
        
        # 不完全なサイクル（Greenなし）
        very_incomplete_phases = {
            TDDCyclePhase.RED: [{"message": "red phase"}]
        }
        self.assertFalse(self.tracker._is_cycle_complete(very_incomplete_phases))
        
    def test_cycle_analysis(self):
        """TDDサイクル分析テスト"""
        mock_commits = [
            {"hash": "abc123", "message": "🔴 Red: Add failing test", "date": "2025-01-20", "author": "dev"},
            {"hash": "def456", "message": "🟢 Green: Implement feature", "date": "2025-01-20", "author": "dev"},
            {"hash": "ghi789", "message": "🔵 Refactor: Clean up code", "date": "2025-01-20", "author": "dev"},
            {"hash": "jkl012", "message": "🔴 Red: Add another test", "date": "2025-01-21", "author": "dev"},
            {"hash": "mno345", "message": "🟢 Green: Fix implementation", "date": "2025-01-21", "author": "dev"},
        ]
        
        cycles = self.tracker._analyze_tdd_cycles(mock_commits)
        
        # 2つのサイクルが検出されることを確認
        self.assertEqual(len(cycles), 2)
        
        # 最初のサイクル（時系列的に早い）- Red+Greenのみ
        first_cycle = cycles[0]
        self.assertTrue(first_cycle["complete"])
        self.assertIn(TDDCyclePhase.RED, first_cycle["phases"])
        self.assertIn(TDDCyclePhase.GREEN, first_cycle["phases"])
        # Refactorは含まれない（2番目のサイクルに属する）
        
        # 2番目のサイクル（時系列的に後）- Red+Green+Refactor
        second_cycle = cycles[1]
        self.assertTrue(second_cycle["complete"])
        self.assertIn(TDDCyclePhase.RED, second_cycle["phases"])
        self.assertIn(TDDCyclePhase.GREEN, second_cycle["phases"])
        self.assertIn(TDDCyclePhase.REFACTOR, second_cycle["phases"])
        
    def test_violation_detection(self):
        """TDD違反検出テスト"""
        # 不完全なサイクル（Redフェーズなし）
        incomplete_cycles = [
            {
                "phases": {TDDCyclePhase.GREEN: [{"message": "green"}]},
                "complete": False
            }
        ]
        
        violations = self.tracker._detect_cycle_violations(incomplete_cycles, "test_file.py")
        
        # Red段階なし違反が検出されることを確認
        red_violations = [v for v in violations if v["type"] == TDDViolationType.NO_RED_PHASE]
        self.assertGreater(len(red_violations), 0)
        
        # Green段階スキップ違反は検出されないことを確認（Greenは存在）
        green_violations = [v for v in violations if v["type"] == TDDViolationType.SKIPPED_GREEN_PHASE]
        self.assertEqual(len(green_violations), 0)
        
    def test_compliance_rate_calculation(self):
        """遵守率計算テスト"""
        cycles = [
            {"complete": True},
            {"complete": True},
            {"complete": False},
            {"complete": True}
        ]
        
        compliance_rate = self.tracker._calculate_compliance_rate(cycles)
        self.assertEqual(compliance_rate, 75.0)  # 4つ中3つ完了 = 75%
        
        # 空のサイクルリスト
        empty_compliance = self.tracker._calculate_compliance_rate([])
        self.assertEqual(empty_compliance, 0.0)


class TestTestQualityAnalyzer(unittest.TestCase):
    """テスト品質・実質性評価システムテスト"""
    
    def setUp(self):
        """テスト環境セットアップ"""
        self.analyzer = TestQualityAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """テスト環境クリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def test_analyzer_initialization(self):
        """解析器の初期化テスト"""
        self.assertIsInstance(self.analyzer, TestQualityAnalyzer)
        self.assertIsNotNone(self.analyzer.poor_quality_patterns)
        self.assertIsNotNone(self.analyzer.fake_implementation_patterns)
        
    def test_test_function_extraction(self):
        """テスト関数抽出テスト"""
        test_code = '''
import unittest

class TestExample(unittest.TestCase):
    def test_valid_function(self):
        """This is a proper test"""
        assert 1 == 1
        
    def test_empty_function(self):
        pass
        
    def helper_function(self):
        return True
        
    def test_no_assertion(self):
        x = 1 + 1
'''
        
        # 一時ファイルに書き込み
        test_file = Path(self.temp_dir) / "test_example.py"
        test_file.write_text(test_code)
        
        analysis = self.analyzer.analyze_test_quality(str(test_file))
        
        # 3つのテスト関数が検出されることを確認
        self.assertEqual(analysis["total_tests"], 3)
        
        # テスト関数名が正しく抽出されることを確認
        test_functions = analysis["test_functions"]
        self.assertIn("test_valid_function", test_functions)
        self.assertIn("test_empty_function", test_functions)
        self.assertIn("test_no_assertion", test_functions)
        
        # helper_functionは含まれないことを確認
        self.assertNotIn("helper_function", test_functions)
        
    def test_quality_score_calculation(self):
        """品質スコア計算テスト"""
        # 高品質なテスト
        good_test_code = '''
def test_user_authentication():
    """Test user authentication functionality"""
    user = User("test@example.com", "password")
    assert user.authenticate("password") == True
    assert user.authenticate("wrong") == False
'''
        
        good_test_file = Path(self.temp_dir) / "test_good.py"
        good_test_file.write_text(good_test_code)
        
        good_analysis = self.analyzer.analyze_test_quality(str(good_test_file))
        good_score = good_analysis["quality_score"]
        
        # 低品質なテスト
        poor_test_code = '''
def test_something():
    pass
    
def test_another():
    assert True
    
def test_fake():
    return True  # fake
'''
        
        poor_test_file = Path(self.temp_dir) / "test_poor.py"
        poor_test_file.write_text(poor_test_code)
        
        poor_analysis = self.analyzer.analyze_test_quality(str(poor_test_file))
        poor_score = poor_analysis["quality_score"]
        
        # 良いテストの方が高いスコアを持つことを確認
        self.assertGreater(good_score, poor_score)
        self.assertLess(poor_score, 50.0)  # 低品質テストは低スコア
        
    def test_violation_detection(self):
        """違反検出テスト"""
        violation_test_code = '''
def test_empty():
    pass
    
def test_no_assertion():
    x = 1 + 1
    print(x)
    
def test_fake_implementation():
    return True  # fake
    
def test_meaningless():
    assert True
'''
        
        violation_test_file = Path(self.temp_dir) / "test_violations.py"
        violation_test_file.write_text(violation_test_code)
        
        analysis = self.analyzer.analyze_test_quality(str(violation_test_file))
        violations = analysis["violations"]
        
        # 複数の違反が検出されることを確認
        self.assertGreater(len(violations), 0)
        
        # 空テスト違反
        empty_violations = [v for v in violations if "empty" in v["description"].lower()]
        self.assertGreater(len(empty_violations), 0)
        
        # アサーションなし違反
        no_assertion_violations = [v for v in violations if "assertion" in v["description"].lower()]
        self.assertGreater(len(no_assertion_violations), 0)
        
    def test_mock_usage_analysis(self):
        """モック使用状況分析テスト"""
        mock_test_code = '''
from unittest.mock import Mock, patch

@patch('requests.get')
def test_api_call(mock_get):
    mock_get.return_value.status_code = 200
    assert api_call() == 200
    
def test_with_mock():
    mock_obj = Mock()
    mock_obj.method.return_value = "test"
    assert mock_obj.method() == "test"
'''
        
        mock_usage = self.analyzer._analyze_mock_usage(mock_test_code)
        
        # モックが検出されることを確認
        self.assertGreater(mock_usage["total_mocks"], 0)
        self.assertGreater(mock_usage["mock_ratio"], 0)
        
    def test_coverage_indicators_analysis(self):
        """カバレッジ操作兆候分析テスト"""
        coverage_code = '''
def test_normal():
    assert True
    
def test_excluded():  # pragma: no cover
    pass
    
def test_ignored():  # coverage: ignore
    assert False
'''
        
        indicators = self.analyzer._analyze_coverage_indicators(coverage_code)
        
        # カバレッジ操作パターンが検出されることを確認
        self.assertGreater(indicators["suspicious_coverage_patterns"], 0)
        self.assertTrue(indicators["has_coverage_manipulation"])


class TestCoverageManipulationDetector(unittest.TestCase):
    """カバレッジ操作検出システムテスト"""
    
    def setUp(self):
        """テスト環境セットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.detector = CoverageManipulationDetector(self.project_root)
        
    def tearDown(self):
        """テスト環境クリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def test_detector_initialization(self):
        """検出器の初期化テスト"""
        self.assertIsInstance(self.detector, CoverageManipulationDetector)
        self.assertEqual(self.detector.project_root, self.project_root)
        
    def test_suspiciously_high_coverage_detection(self):
        """異常に高いカバレッジ検出テスト"""
        # 100%カバレッジのデータ（大規模プロジェクト）
        high_coverage_data = {
            "overall_coverage": 100.0,
            "files": {f"file_{i}.py": {"line_coverage": 100.0} for i in range(15)}
        }
        
        violations = self.detector._detect_suspiciously_high_coverage(high_coverage_data)
        
        # 疑わしい高カバレッジ違反が検出されることを確認
        high_coverage_violations = [v for v in violations 
                                  if v["type"] == TDDViolationType.COVERAGE_MANIPULATION]
        self.assertGreater(len(high_coverage_violations), 0)
        
        # 小規模プロジェクトの100%カバレッジは問題なし
        small_coverage_data = {
            "overall_coverage": 100.0,
            "files": {f"file_{i}.py": {"line_coverage": 100.0} for i in range(5)}
        }
        
        small_violations = self.detector._detect_suspiciously_high_coverage(small_coverage_data)
        self.assertEqual(len(small_violations), 0)
        
    def test_coverage_exclusion_abuse_detection(self):
        """カバレッジ除外乱用検出テスト"""
        # 大量の除外を含むファイルを作成
        excessive_exclusions_code = '''
def function1():  # pragma: no cover
    pass
    
def function2():  # pragma: no cover
    pass
    
def function3():  # coverage: ignore
    pass
    
def function4():  # pragma: no cover
    pass
    
def function5():  # nocov
    pass
'''
        
        test_file = self.project_root / "excessive_exclusions.py"
        test_file.write_text(excessive_exclusions_code)
        
        violations = self.detector._detect_coverage_exclusion_abuse()
        
        # 除外乱用違反が検出されることを確認
        exclusion_violations = [v for v in violations 
                              if "exclusion" in v["description"].lower()]
        self.assertGreater(len(exclusion_violations), 0)
        
    def test_fake_test_pattern_detection(self):
        """偽テストパターン検出テスト"""
        # 偽テストを含むファイルを作成
        fake_test_code = '''
def test_empty():
    pass
    
def test_fake_assertion():
    assert True  # fake
    
def test_meaningless():
    assert 1 == 1
'''
        
        test_file = self.project_root / "test_fake.py"
        test_file.write_text(fake_test_code)
        
        violations = self.detector._detect_fake_test_patterns()
        
        # 偽テスト違反が検出されることを確認
        fake_violations = [v for v in violations 
                         if v["type"] == TDDViolationType.FAKE_TEST_IMPLEMENTATION]
        self.assertGreater(len(fake_violations), 0)
        
    def test_manipulation_score_calculation(self):
        """操作スコア計算テスト"""
        violations = [
            {"severity": "CRITICAL"},
            {"severity": "HIGH"},
            {"severity": "MEDIUM"},
            {"severity": "LOW"}
        ]
        
        score = self.detector._calculate_manipulation_score(violations)
        
        # スコアが正しく計算されることを確認
        expected_score = 25 + 15 + 5 + 1  # 各重要度の重み
        self.assertEqual(score, expected_score)
        
        # 空の違反リスト
        empty_score = self.detector._calculate_manipulation_score([])
        self.assertEqual(empty_score, 0.0)


class TestTDDGuardian(unittest.TestCase):
    """TDD Guardian メインクラステスト"""
    
    def setUp(self):
        """テスト環境セットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.guardian = TDDGuardian(self.project_root)
        
        # テスト用のPythonファイルを作成
        self._create_test_files()
        
    def tearDown(self):
        """テスト環境クリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def _create_test_files(self):
        """テスト用ファイルを作成"""
        # 実装ファイル
        impl_file = self.project_root / "example.py"
        impl_file.write_text('''
def add(a, b):
    """Add two numbers"""
    return a + b

def multiply(a, b):
    """Multiply two numbers"""
    return a * b
''')
        
        # 良いテストファイル
        good_test_file = self.project_root / "test_good.py"
        good_test_file.write_text('''
import unittest
from example import add, multiply

class TestMath(unittest.TestCase):
    def test_add_positive_numbers(self):
        """Test addition of positive numbers"""
        self.assertEqual(add(2, 3), 5)
        self.assertEqual(add(0, 0), 0)
        
    def test_multiply_numbers(self):
        """Test multiplication"""
        self.assertEqual(multiply(3, 4), 12)
        self.assertEqual(multiply(0, 5), 0)
''')
        
        # 悪いテストファイル
        poor_test_file = self.project_root / "test_poor.py"
        poor_test_file.write_text('''
def test_empty():
    pass
    
def test_no_assertion():
    x = 1 + 1
    
def test_fake():
    assert True  # fake implementation
''')
        
    def test_guardian_initialization(self):
        """ガーディアンの初期化テスト"""
        self.assertIsInstance(self.guardian, TDDGuardian)
        self.assertEqual(self.guardian.name, "AncientElder_TDDGuardian")
        self.assertIsInstance(self.guardian.cycle_tracker, TDDCycleTracker)
        self.assertIsInstance(self.guardian.quality_analyzer, TestQualityAnalyzer)
        self.assertIsInstance(self.guardian.coverage_detector, CoverageManipulationDetector)
        
    def test_quality_thresholds_configuration(self):
        """品質閾値設定テスト"""
        thresholds = self.guardian.quality_thresholds
        
        self.assertIn("minimum_test_quality_score", thresholds)
        self.assertIn("maximum_coverage_manipulation_score", thresholds)
        self.assertIn("minimum_cycle_compliance_rate", thresholds)
        
        # 閾値が妥当な範囲にあることを確認
        self.assertGreater(thresholds["minimum_test_quality_score"], 0)
        self.assertLess(thresholds["minimum_test_quality_score"], 100)
        
    @pytest.mark.asyncio
    async def test_audit_project(self):
        """プロジェクト監査テスト"""
        target = {
            "type": "project",
            "path": str(self.project_root),
            "time_window_days": 30,
            "include_coverage": False  # 簡単のためカバレッジ分析は無効
        }
        
        result = await self.guardian.audit(target)
        
        # 監査結果の基本検証
        self.assertEqual(result.auditor_name, self.guardian.name)
        self.assertIsNotNone(result.violations)
        self.assertIsNotNone(result.metrics)
        
        # テスト品質違反が検出されることを確認（poor test fileがあるため）
        quality_violations = [v for v in result.violations 
                            if v.get("metadata", {}).get("category") == "test_quality"]
        self.assertGreater(len(quality_violations), 0)
        
    @pytest.mark.asyncio
    async def test_audit_single_file(self):
        """単一ファイル監査テスト"""
        impl_file = self.project_root / "example.py"
        
        target = {
            "type": "file",
            "path": str(impl_file),
            "time_window_days": 30
        }
        
        result = await self.guardian.audit(target)
        
        # 監査結果の基本検証
        self.assertEqual(result.auditor_name, self.guardian.name)
        # Gitコミット履歴がないため、エラーまたは違反なしの可能性
        
    @pytest.mark.asyncio
    async def test_audit_test_file(self):
        """テストファイル監査テスト"""
        poor_test_file = self.project_root / "test_poor.py"
        
        target = {
            "type": "test_file",
            "path": str(poor_test_file)
        }
        
        result = await self.guardian.audit(target)
        
        # 監査結果の基本検証
        self.assertEqual(result.auditor_name, self.guardian.name)
        
        # 品質違反が検出されることを確認
        self.assertGreater(len(result.violations), 0)
        
        # 違反タイプの確認
        violation_types = [v.get("metadata", {}).get("violation_type") for v in result.violations]
        self.assertIn(TDDViolationType.POOR_TEST_QUALITY, violation_types)
        
    @pytest.mark.asyncio
    async def test_audit_invalid_target(self):
        """無効なターゲット監査テスト"""
        target = {
            "type": "invalid_type",
            "path": str(self.project_root)
        }
        
        result = await self.guardian.audit(target)
        
        # エラー違反が追加されることを確認
        self.assertGreater(len(result.violations), 0)
        
        # 設定エラーが検出されることを確認
        config_violations = [v for v in result.violations 
                           if v.get("metadata", {}).get("category") == "configuration"]
        self.assertGreater(len(config_violations), 0)
        
    def test_file_skip_logic(self):
        """ファイルスキップロジックテスト"""
        skip_cases = [
            Path("/project/venv/lib/python3.9/site-packages/module.py"),
            Path("/project/node_modules/package/index.js"),
            Path("/project/.git/config"),
            Path("/project/__pycache__/module.pyc"),
            Path("/project/migrations/0001_initial.py")
        ]
        
        for file_path in skip_cases:
            should_skip = self.guardian._should_skip_file(file_path)
            self.assertTrue(should_skip, f"Should skip {file_path}")
            
        # スキップしないファイル
        normal_files = [
            Path("/project/src/main.py"),
            Path("/project/tests/test_main.py"),
            Path("/project/lib/utils.py")
        ]
        
        for file_path in normal_files:
            should_skip = self.guardian._should_skip_file(file_path)
            self.assertFalse(should_skip, f"Should not skip {file_path}")
            
    def test_cycle_fix_suggestions(self):
        """TDDサイクル修正提案テスト"""
        violations = [
            {"type": TDDViolationType.NO_RED_PHASE},
            {"type": TDDViolationType.SKIPPED_GREEN_PHASE},
            {"type": TDDViolationType.INSUFFICIENT_REFACTOR},
            {"type": "UNKNOWN_TYPE"}
        ]
        
        for violation in violations:
            suggestion = self.guardian._suggest_cycle_fix(violation)
            self.assertIsInstance(suggestion, str)
            self.assertGreater(len(suggestion), 0)
            
    def test_test_quality_fix_suggestions(self):
        """テスト品質修正提案テスト"""
        violations = [
            {"type": TDDViolationType.POOR_TEST_QUALITY},
            {"type": TDDViolationType.FAKE_TEST_IMPLEMENTATION},
            {"type": "UNKNOWN_TYPE"}
        ]
        
        for violation in violations:
            suggestion = self.guardian._suggest_test_quality_fix(violation)
            self.assertIsInstance(suggestion, str)
            self.assertGreater(len(suggestion), 0)
            
    def test_tdd_metrics_calculation(self):
        """TDDメトリクス計算テスト"""
        # モック違反データでテスト
        from libs.ancient_elder.base import AuditResult
        
        result = AuditResult()
        result.add_violation(
            severity=ViolationSeverity.HIGH,
            title="TDD cycle violation",
            description="Test description",
            metadata={"category": "tdd_cycle", "violation_type": TDDViolationType.NO_RED_PHASE}
        )
        result.add_violation(
            severity=ViolationSeverity.MEDIUM,
            title="Test quality violation", 
            description="Test description",
            metadata={"category": "test_quality", "violation_type": TDDViolationType.POOR_TEST_QUALITY}
        )
        
        target = {"type": "project"}
        
        self.guardian._calculate_tdd_metrics(result, target)
        
        # メトリクスが正しく計算されることを確認
        self.assertIsNotNone(result.metrics.get("tdd_compliance_score"))
        self.assertEqual(result.metrics.get("cycle_violations"), 1)
        self.assertEqual(result.metrics.get("test_quality_violations"), 1)
        self.assertEqual(result.metrics.get("total_violations"), 2)
        
        # コンプライアンススコアが妥当な範囲にあることを確認
        compliance_score = result.metrics.get("tdd_compliance_score")
        self.assertGreaterEqual(compliance_score, 0)
        self.assertLessEqual(compliance_score, 100)
        
    def test_audit_scope_definition(self):
        """監査範囲定義テスト"""
        scope = self.guardian.get_audit_scope()
        
        # 範囲定義の確認
        self.assertEqual(scope["scope"], "tdd_guardian_magic")
        self.assertIn("targets", scope)
        self.assertIn("violation_types", scope)
        self.assertIn("quality_thresholds", scope)
        self.assertIn("description", scope)
        
        # 対象項目の確認
        targets = scope["targets"]
        self.assertIn("TDD Red→Green→Refactor cycle compliance", targets)
        self.assertIn("Test quality and substantiality", targets)
        self.assertIn("Coverage manipulation detection", targets)
        
        # 違反タイプの確認
        violation_types = scope["violation_types"]
        expected_types = [
            TDDViolationType.MISSING_TEST_FIRST,
            TDDViolationType.NO_RED_PHASE,
            TDDViolationType.POOR_TEST_QUALITY,
            TDDViolationType.COVERAGE_MANIPULATION
        ]
        
        for expected_type in expected_types:
            self.assertIn(expected_type, violation_types)
            
        # 品質閾値の確認
        self.assertEqual(scope["quality_thresholds"], self.guardian.quality_thresholds)


class TestTDDGuardianIntegration(unittest.TestCase):
    """TDD Guardian 統合テスト"""
    
    def setUp(self):
        """統合テスト環境セットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.guardian = TDDGuardian(self.project_root)
        
        # 複雑なテストプロジェクトを作成
        self._create_complex_test_project()
        
    def tearDown(self):
        """統合テスト環境クリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def _create_complex_test_project(self):
        """複雑なテストプロジェクトを作成"""
        # ソースコード
        (self.project_root / "src").mkdir()
        
        # ユーザー管理モジュール
        user_module = self.project_root / "src" / "user.py"
        user_module.write_text('''
class User:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.is_active = True
        
    def authenticate(self, password):
        return self.password == password
        
    def deactivate(self):
        self.is_active = False
''')
        
        # 高品質テスト
        good_test = self.project_root / "test_user_good.py"
        good_test.write_text('''
import unittest
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "src"))

from user import User

class TestUserAuthentication(unittest.TestCase):
    """Test user authentication functionality"""
    
    def test_user_creation(self):
        """Test user object creation"""
        user = User("test@example.com", "secret123")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.is_active)
        
    def test_authentication_success(self):
        """Test successful authentication"""
        user = User("test@example.com", "secret123")
        self.assertTrue(user.authenticate("secret123"))
        
    def test_authentication_failure(self):
        """Test failed authentication"""
        user = User("test@example.com", "secret123")
        self.assertFalse(user.authenticate("wrong_password"))
        
    def test_user_deactivation(self):
        """Test user deactivation"""
        user = User("test@example.com", "secret123")
        user.deactivate()
        self.assertFalse(user.is_active)
''')
        
        # 低品質テスト（多くの違反を含む）
        poor_test = self.project_root / "test_user_poor.py"
        poor_test.write_text('''
# Poor quality test file with multiple violations

def test_empty_test():
    """Empty test that does nothing"""
    pass

def test_no_assertions():
    """Test without any assertions"""
    user = User("test@test.com", "pass")
    # No assertions - this is bad!
    
def test_fake_implementation():
    """Fake test implementation"""
    assert True  # fake - this always passes
    
def test_meaningless_assertion():
    """Test with meaningless assertion"""
    assert 1 == 1  # This tells us nothing
    
def test_coverage_exclusion():  # pragma: no cover
    """Test with suspicious coverage exclusion"""
    assert False  # This should fail but is excluded
    
@unittest.skip("Skipping because reasons")  # coverage: ignore
def test_skipped():
    """Skipped test that should be fixed"""
    assert user_function_exists()
''')
        
        # カバレッジ除外の乱用を含むソースファイル
        problematic_source = self.project_root / "src" / "problematic.py"
        problematic_source.write_text('''
def function1():  # pragma: no cover
    """Function with unnecessary coverage exclusion"""
    return "hello"
    
def function2():  # coverage: ignore  
    """Another function with coverage exclusion"""
    return "world"
    
def function3():  # nocov
    """Third function with exclusion"""
    return "test"
    
def function4():  # pragma: no cover
    """Fourth function excluded"""
    return "excluded"
    
def function5():  # pragma: no cover
    """Fifth function excluded"""
    return "also excluded"
    
def function6():  # coverage: ignore
    """Sixth function excluded"""
    return "ignore me"
''')
        
    @pytest.mark.asyncio
    async def test_comprehensive_project_audit(self):
        """包括的プロジェクト監査テスト"""
        target = {
            "type": "project",
            "path": str(self.project_root),
            "time_window_days": 30,
            "include_coverage": True
        }
        
        result = await self.guardian.audit(target)
        
        # 基本監査結果の検証
        self.assertIsNotNone(result)
        self.assertEqual(result.auditor_name, self.guardian.name)
        
        # 多数の違反が検出されることを確認（低品質テストファイルがあるため）
        self.assertGreater(len(result.violations), 0)
        
        # 各カテゴリの違反が検出されることを確認
        violation_categories = [v.get("metadata", {}).get("category") for v in result.violations]
        
        # テスト品質違反
        self.assertIn("test_quality", violation_categories)
        
        # カバレッジ操作違反（カバレッジ除外の乱用により）
        self.assertIn("coverage", violation_categories)
        
        # メトリクスの確認
        self.assertIsNotNone(result.metrics.get("tdd_compliance_score"))
        self.assertIsNotNone(result.metrics.get("total_violations"))
        
        # 低いコンプライアンススコア（多数の違反があるため）
        compliance_score = result.metrics.get("tdd_compliance_score")
        self.assertLess(compliance_score, 80.0)  # 多くの違反があるため低スコア
        
    @pytest.mark.asyncio
    async def test_test_quality_comparison(self):
        """テスト品質比較テスト"""
        # 良いテストファイルの監査
        good_target = {
            "type": "test_file",
            "path": str(self.project_root / "test_user_good.py")
        }
        
        good_result = await self.guardian.audit(good_target)
        
        # 悪いテストファイルの監査
        poor_target = {
            "type": "test_file", 
            "path": str(self.project_root / "test_user_poor.py")
        }
        
        poor_result = await self.guardian.audit(poor_target)
        
        # 悪いテストファイルの方が多くの違反を持つことを確認
        self.assertGreater(len(poor_result.violations), len(good_result.violations))
        
        # 良いテストファイルは違反が少ない（またはゼロ）
        self.assertLessEqual(len(good_result.violations), 2)  # 最大2つまで許容
        
        # 悪いテストファイルは多数の違反
        self.assertGreater(len(poor_result.violations), 3)
        
    def test_violation_severity_distribution(self):
        """違反重要度分布テスト"""
        # TDD Guardianは適切な重要度を割り当てるかテスト
        
        # 偽テスト実装は CRITICAL
        fake_violation = {"type": TDDViolationType.FAKE_TEST_IMPLEMENTATION}
        fake_fix = self.guardian._suggest_test_quality_fix(fake_violation)
        self.assertIn("fake", fake_fix.lower())
        
        # 品質不足は HIGH/MEDIUM
        quality_violation = {"type": TDDViolationType.POOR_TEST_QUALITY}
        quality_fix = self.guardian._suggest_test_quality_fix(quality_violation)
        self.assertIn("assertion", quality_fix.lower())
        
        # TDDサイクル違反の修正提案
        cycle_violation = {"type": TDDViolationType.NO_RED_PHASE}
        cycle_fix = self.guardian._suggest_cycle_fix(cycle_violation)
        self.assertIn("test", cycle_fix.lower())
        self.assertIn("first", cycle_fix.lower())


if __name__ == "__main__":
    # ログレベルを設定
    logging.basicConfig(level=logging.INFO)
    
    # テストスイートを実行
    unittest.main(verbosity=2)