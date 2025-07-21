#!/usr/bin/env python3
"""
Elder Flow機能強化のテスト
pre-commit自動修復、品質ゲート最適化のテスト
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import sys
import os

# テスト対象モジュールのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libs.elder_flow_pre_commit_handler import ElderFlowPreCommitHandler, PreCommitError
from libs.elder_flow_quality_gate_optimizer import ElderFlowQualityGateOptimizer, QualityMetrics


class TestElderFlowPreCommitHandler(unittest.TestCase):
    """Pre-commit自動修復ハンドラーのテスト"""

    def setUp(self):
        """テスト準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.handler = ElderFlowPreCommitHandler(self.temp_dir)

    def tearDown(self):
        """テスト後処理"""
        shutil.rmtree(self.temp_dir)

    def test_parse_pre_commit_output(self):
        """pre-commit出力解析のテスト"""
        stderr = """
trim trailing whitespace.................................................Failed
- hook id: trailing-whitespace
- exit code: 1
- files were modified by this hook

Fixing test1.py
Fixing test2.py

fix end of files.........................................................Failed
- hook id: end-of-file-fixer
- exit code: 1
- files were modified by this hook

Fixing test1.py
"""

        errors = self.handler._parse_pre_commit_output(stderr)

        self.assertEqual(len(errors), 2)
        self.assertEqual(errors[0].hook_id, "trailing-whitespace")
        self.assertEqual(errors[0].modified_files, ["test1.py", "test2.py"])
        self.assertEqual(errors[1].hook_id, "end-of-file-fixer")
        self.assertEqual(errors[1].modified_files, ["test1.py"])

    def test_fix_trailing_whitespace(self):
        """末尾空白修正のテスト"""
        # テストファイル作成
        test_file = Path(self.temp_dir) / "test.py"
        test_file.write_text("def test():  \n    pass   \n")

        # 修正実行
        result = self.handler._fix_trailing_whitespace(["test.py"])

        # 検証
        self.assertTrue(result)
        content = test_file.read_text()
        self.assertEqual(content, "def test():\n    pass\n")

    def test_fix_end_of_file(self):
        """ファイル末尾改行修正のテスト"""
        # テストファイル作成
        test_file = Path(self.temp_dir) / "test.py"
        test_file.write_text("def test():\n    pass")

        # 修正実行
        result = self.handler._fix_end_of_file(["test.py"])

        # 検証
        self.assertTrue(result)
        content = test_file.read_text()
        self.assertTrue(content.endswith("\n"))

    def test_fix_syntax_errors(self):
        """構文エラー修正のテスト"""
        # テストファイル作成
        test_file = Path(self.temp_dir) / "test.py"
        test_file.write_text("def test(\n    pass")

        # 修正実行
        result = self.handler._fix_syntax_errors(["test.py"])

        # 検証
        self.assertTrue(result)
        content = test_file.read_text()
        # 閉じ括弧が追加されているはず
        self.assertIn(")", content)

    @patch('subprocess.run')
    def test_run_with_auto_fix(self, mock_run):
        """自動修復付きコマンド実行のテスト"""
        # 初回失敗、2回目成功をシミュレート
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="Failed"),
            MagicMock(returncode=0, stdout="Success", stderr="")
        ]

        success, stdout, stderr = self.handler.run_with_auto_fix(["git", "commit", "-m", "test"])

        self.assertTrue(success)
        self.assertEqual(stdout, "Success")
        self.assertEqual(mock_run.call_count, 2)


class TestElderFlowQualityGateOptimizer(unittest.TestCase):
    """品質ゲート最適化システムのテスト"""

    def setUp(self):
        """テスト準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "quality_config.json"
        self.optimizer = ElderFlowQualityGateOptimizer(str(self.config_path))

    def tearDown(self):
        """テスト後処理"""
        shutil.rmtree(self.temp_dir)

    def test_default_metrics(self):
        """デフォルトメトリクスのテスト"""
        metrics = self.optimizer.base_metrics

        self.assertEqual(metrics.test_coverage, 70.0)
        self.assertEqual(metrics.code_complexity, 10.0)
        self.assertEqual(metrics.duplication_ratio, 5.0)
        self.assertEqual(metrics.documentation_coverage, 60.0)

    def test_get_adjusted_metrics_priority(self):
        """優先度による調整のテスト"""
        # Critical優先度（30%緩和）
        critical = self.optimizer.get_adjusted_metrics(priority="critical")
        self.assertAlmostEqual(critical["test_coverage"], 49.0)  # 70 * 0.7

        # High優先度（15%緩和）
        high = self.optimizer.get_adjusted_metrics(priority="high")
        self.assertAlmostEqual(high["test_coverage"], 59.5)  # 70 * 0.85

        # Medium優先度（5%緩和）
        medium = self.optimizer.get_adjusted_metrics(priority="medium")
        self.assertAlmostEqual(medium["test_coverage"], 66.5)  # 70 * 0.95

    def test_get_adjusted_metrics_phase(self):
        """フェーズによる調整のテスト"""
        # プロトタイプフェーズ（40%緩和）
        prototype = self.optimizer.get_adjusted_metrics(phase="prototype")
        self.assertAlmostEqual(prototype["test_coverage"], 42.0)  # 70 * 0.6

        # 開発フェーズ（20%緩和）
        development = self.optimizer.get_adjusted_metrics(phase="development")
        self.assertAlmostEqual(development["test_coverage"], 56.0)  # 70 * 0.8

    def test_get_adjusted_metrics_failure_count(self):
        """失敗回数による調整のテスト"""
        # 3回失敗（10%緩和）
        failed_3 = self.optimizer.get_adjusted_metrics(failure_count=3)
        self.assertAlmostEqual(failed_3["test_coverage"], 63.0)  # 70 * 0.9

        # 5回以上失敗（20%緩和）
        failed_5 = self.optimizer.get_adjusted_metrics(failure_count=5)
        self.assertAlmostEqual(failed_5["test_coverage"], 56.0)  # 70 * 0.8

    def test_evaluate_quality(self):
        """品質評価のテスト"""
        metrics = {
            "test_coverage": 75.0,
            "code_complexity": 8.0,
            "lint_score": 9.0
        }

        thresholds = {
            "test_coverage": 70.0,
            "code_complexity": 10.0,
            "lint_score": 8.0
        }

        result = self.optimizer.evaluate_quality(metrics, thresholds)

        self.assertTrue(result["passed"])
        self.assertEqual(result["score"], 30)  # 全てパス
        self.assertEqual(len(result["failures"]), 0)

    def test_evaluate_quality_with_failures(self):
        """品質評価（失敗あり）のテスト"""
        metrics = {
            "test_coverage": 50.0,  # 閾値以下
            "code_complexity": 15.0,  # 閾値以上
            "lint_score": 9.0
        }

        thresholds = {
            "test_coverage": 70.0,
            "code_complexity": 10.0,
            "lint_score": 8.0
        }

        result = self.optimizer.evaluate_quality(metrics, thresholds)

        self.assertFalse(result["passed"])
        self.assertEqual(len(result["failures"]), 2)
        self.assertTrue(result["score"] < 30)

    def test_suggest_improvements(self):
        """改善提案生成のテスト"""
        failures = [
            {
                "metric": "test_coverage",
                "threshold": 70.0,
                "actual": 50.0,
                "type": "below_minimum"
            },
            {
                "metric": "code_complexity",
                "threshold": 10.0,
                "actual": 15.0,
                "type": "above_maximum"
            }
        ]

        suggestions = self.optimizer.suggest_improvements(failures)

        self.assertEqual(len(suggestions), 2)
        self.assertIn("テストカバレッジ", suggestions[0])
        self.assertIn("複雑度", suggestions[1])

    def test_config_persistence(self):
        """設定の永続化テスト"""
        # 履歴を追加
        self.optimizer._record_adjustment("high", "development", 2, 0.85)

        # 新しいインスタンスで読み込み
        new_optimizer = ElderFlowQualityGateOptimizer(str(self.config_path))

        # 履歴が保存されているか確認
        self.assertEqual(len(new_optimizer.history), 1)
        self.assertEqual(new_optimizer.history[0]["priority"], "high")

    def test_statistics(self):
        """統計情報のテスト"""
        # 複数の調整を記録
        self.optimizer._record_adjustment("high", "development", 1, 0.85)
        self.optimizer._record_adjustment("critical", "prototype", 3, 0.5)
        self.optimizer._record_adjustment("medium", "production", 0, 0.95)

        stats = self.optimizer.get_statistics()

        self.assertEqual(stats["total_adjustments"], 3)
        self.assertAlmostEqual(stats["average_factor"], 0.77, places=2)
        self.assertEqual(stats["priority_distribution"]["high"], 1)
        self.assertEqual(stats["priority_distribution"]["critical"], 1)


if __name__ == "__main__":
    unittest.main()
