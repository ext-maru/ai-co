#!/usr/bin/env python3
"""
AutoIssueProcessor の完全テストスイート
"""

import asyncio
import json
import os
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from elders_guild.elder_tree.integrations.github.auto_issue_processor import (
    AutoIssueProcessor,
    ComplexityEvaluator,
    ComplexityScore,
    ProcessingLimiter,
)


class TestComplexityEvaluator(unittest.TestCase):
    """複雑度評価のテスト"""

    def setUp(self):
        self.evaluator = ComplexityEvaluator()

    def async_test(self, coro):
        """非同期テストヘルパー"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def test_simple_issue_evaluation(self):
        """単純なイシューの評価"""
        # モックイシュー作成
        issue = Mock()
        issue.title = "Fix typo in README"
        issue.body = "There's a typo in the documentation"
        issue.labels = []

        # 評価実行
        score = self.async_test(self.evaluator.evaluate(issue))

        self.assertIsInstance(score, ComplexityScore)
        self.assertLess(score.score, 0.7)
        self.assertTrue(score.is_processable)

    def test_complex_issue_evaluation(self):
        """複雑なイシューの評価"""
        issue = Mock()
        issue.title = "Implement OAuth2.0 authentication system"
        issue.body = "We need to add full OAuth2.0 support with multiple providers"
        issue.labels = []

        score = self.async_test(self.evaluator.evaluate(issue))

        self.assertGreaterEqual(score.score, 0.7)
        self.assertFalse(score.is_processable)

    def test_security_issue_evaluation(self):
        """セキュリティ関連イシューの評価"""
        issue = Mock()
        issue.title = "Security vulnerability in authentication"
        issue.body = "Found a security issue with token validation"
        issue.labels = []

        score = self.async_test(self.evaluator.evaluate(issue))

        # セキュリティ関連は高複雑度（0.7以上）
        self.assertGreaterEqual(score.score, 0.7)
        self.assertFalse(score.is_processable)

    def test_good_first_issue_label(self):
        """good first issueラベル付きイシュー"""
        issue = Mock()
        issue.title = "Add unit tests"
        issue.body = "Need more test coverage"

        label = Mock()
        label.name = "good first issue"
        issue.labels = [label]

        score = self.async_test(self.evaluator.evaluate(issue))

        self.assertLess(score.score, 0.5)
        self.assertTrue(score.is_processable)


class TestProcessingLimiter(unittest.TestCase):
    """処理制限機能のテスト"""

    def setUp(self):
        self.test_log_file = Path("logs/test_auto_issue_processing.json")
        self.limiter = ProcessingLimiter()
        """setUpの値を設定"""
        self.limiter.processing_log_file = self.test_log_file

        # テスト用ディレクトリ作成
        self.test_log_file.parent.mkdir(exist_ok=True)

    def tearDown(self):
        # テストファイルクリーンアップ
        if self.test_log_file.exists():
            self.test_log_file.unlink()

    def async_test(self, coro):
        loop = asyncio.new_event_loop()
        """async_testメソッド"""
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def test_can_process_empty_log(self):
        """ログが空の場合は処理可能"""
        result = self.async_test(self.limiter.can_process())
        self.assertTrue(result)

    def test_can_process_within_limit(self):
        """制限内の処理"""
        # 2つの処理記録を追加
        logs = [
            {"issue_id": 1, "timestamp": datetime.now().isoformat()},
            {"issue_id": 2, "timestamp": datetime.now().isoformat()},
        ]

        with open(self.test_log_file, "w") as f:
            json.dump(logs, f)

        result = self.async_test(self.limiter.can_process())
        self.assertTrue(result)  # 10個まで処理可能なので、2つなら余裕

    def test_cannot_process_at_limit(self):
        """制限に達した場合の処理"""
        # 10個の処理記録を追加（制限値）
        logs = [
            {"issue_id": i, "timestamp": datetime.now().isoformat()} for i in range(10)
        ]

        with open(self.test_log_file, "w") as f:
            json.dump(logs, f)

        result = self.async_test(self.limiter.can_process())
        self.assertFalse(result)  # 制限に達したので処理不可

    def test_old_logs_ignored(self):
        """古いログは無視される"""
        # 2時間前のログ
        old_time = datetime.now() - timedelta(hours=2)
        logs = [
            {"issue_id": 1, "timestamp": old_time.isoformat()},
            {"issue_id": 2, "timestamp": old_time.isoformat()},
            {"issue_id": 3, "timestamp": old_time.isoformat()},
            {"issue_id": 4, "timestamp": datetime.now().isoformat()},  # 最新1つ
        ]

        with open(self.test_log_file, "w") as f:
            json.dump(logs, f)

        result = self.async_test(self.limiter.can_process())
        self.assertTrue(result)  # 古いログは無視されるので処理可能


class TestAutoIssueProcessor(unittest.TestCase):
    """AutoIssueProcessor統合テスト"""

    @patch("libs.integrations.github.auto_issue_processor.Github")
    def setUp(self, mock_github):
        """テストセットアップ"""
        # GitHub APIモック
        self.mock_github = mock_github
        self.mock_repo = Mock()
        mock_github.return_value.get_repo.return_value = self.mock_repo

        # 環境変数設定
        os.environ["GITHUB_TOKEN"] = "test_token"

        # プロセッサー初期化
        self.processor = AutoIssueProcessor()

    def async_test(self, coro):
        """async_testメソッド"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def test_get_capabilities(self):
        """機能情報の取得"""
        capabilities = self.processor.get_capabilities()

        self.assertEqual(capabilities["service"], "AutoIssueProcessor")
        self.assertEqual(capabilities["version"], "1.0.0")
        self.assertIn("GitHub issue scanning", capabilities["capabilities"])
        self.assertEqual(capabilities["limits"]["max_issues_per_hour"], 10)

    def test_validate_request(self):
        """リクエスト検証"""
        # 有効なリクエスト
        valid_requests = [
            {"mode": "scan"},
            {"mode": "process"},
            {"mode": "dry_run", "issue_number": 123},
        ]

        for req in valid_requests:
            self.assertTrue(self.processor.validate_request(req))

        # 無効なリクエスト
        invalid_requests = [
            {"mode": "invalid_mode"},
            {"mode": "dry_run", "issue_number": "not_a_number"},
        ]

        for req in invalid_requests:
            self.assertFalse(self.processor.validate_request(req))

    def test_determine_priority(self):
        """優先度判定のテスト"""
        # ラベルベースの判定
        issue = Mock()
        issue.title = "Normal issue"

        # Criticalラベル
        label = Mock()
        label.name = "critical"
        issue.labels = [label]
        self.assertEqual(self.processor._determine_priority(issue), "critical")

        # Lowラベル
        label.name = "low"
        issue.labels = [label]
        self.assertEqual(self.processor._determine_priority(issue), "low")

        # タイトルベースの判定
        issue.labels = []
        issue.title = "URGENT: Fix production bug"
        self.assertEqual(self.processor._determine_priority(issue), "critical")

        issue.title = "Fix minor bug"
        self.assertEqual(self.processor._determine_priority(issue), "medium")

        issue.title = "Update documentation"
        self.assertEqual(self.processor._determine_priority(issue), "low")

    @patch("libs.integrations.github.auto_issue_processor.ComplexityEvaluator.evaluate")
    def test_scan_processable_issues(self, mock_evaluate):
        """処理可能イシューのスキャン"""
        # モックイシュー作成
        issues = []
        for i in range(5):
            issue = Mock()
            issue.number = i + 1
            issue.title = f"Issue {i + 1}"
            issue.pull_request = None

            # 優先度設定
            if i < 2:
                label = Mock()
                label.name = "high"
                issue.labels = [label]
            else:
                label = Mock()
                label.name = "medium"
                issue.labels = [label]

            issues.append(issue)

        self.mock_repo.get_issues.return_value = issues

        # 複雑度評価モック - 非同期関数として ComplexityScore を返す
        async def mock_eval(issue):
            return ComplexityScore(0.5, {"test": True})

        mock_evaluate.side_effect = mock_eval

        # スキャン実行
        result = self.async_test(self.processor.scan_processable_issues())

        # 優先度Low(0つ)のみ除外され、Critical/High/Medium(5つ)が処理対象
        self.assertEqual(len(result), 5)

    def test_process_request_scan_mode(self):
        """スキャンモードのテスト"""
        # モックイシュー
        issue = Mock()
        issue.number = 1
        issue.title = "Test issue"
        issue.body = "Test body"
        issue.pull_request = None
        label = Mock()
        label.name = "medium"
        issue.labels = [label]

        self.mock_repo.get_issues.return_value = [issue]

        # スキャン実行
        result = self.async_test(self.processor.process_request({"mode": "scan"}))

        self.assertEqual(result["status"], "success")
        self.assertGreater(result["processable_issues"], 0)
        self.assertIn("issues", result)


class TestEndToEnd(unittest.TestCase):
    """エンドツーエンドテスト"""

    def test_full_workflow(self):
        """完全なワークフローテスト"""
        print("\n🔍 === エンドツーエンドテスト開始 ===")

        # 1.0 複雑度評価
        print("1️⃣ 複雑度評価テスト...")
        evaluator = ComplexityEvaluator()

        # テスト用イシュー
        test_cases = [
            ("Fix typo", "Simple typo fix", True),
            ("Add OAuth2.0", "Complex auth system", False),
            ("Security fix", "Security vulnerability", False),
        ]

        loop = asyncio.new_event_loop()
        for title, body, should_process in test_cases:
            issue = Mock()
            issue.title = title
            issue.body = body
            issue.labels = []

            score = loop.run_until_complete(evaluator.evaluate(issue))
            print(f"   - '{title}': スコア={score.score:0.2f}, 処理可能={score.is_processable}")
            self.assertEqual(score.is_processable, should_process)

        # 2.0 処理制限
        print("\n2️⃣ 処理制限テスト...")
        limiter = ProcessingLimiter()
        limiter.processing_log_file = Path("logs/test_e2e_processing.json")
        limiter.processing_log_file.parent.mkdir(exist_ok=True)

        # クリーンスタート
        if limiter.processing_log_file.exists():
            limiter.processing_log_file.unlink()

        # 10回まで処理可能、11回目で制限
        for i in range(11):
            can_process = loop.run_until_complete(limiter.can_process())
            print(f"   - 処理 {i+1}: {'可能' if can_process else '制限到達'}")

            if can_process:
                loop.run_until_complete(limiter.record_processing(i + 1))

        # クリーンアップ
        if limiter.processing_log_file.exists():
            limiter.processing_log_file.unlink()

        loop.close()

        print("\n✅ === エンドツーエンドテスト完了 ===")


if __name__ == "__main__":
    # 単体テスト実行
    print("🧪 AutoIssueProcessor テストスイート実行中...\n")

    # テストローダー
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 各テストクラスを追加
    suite.addTests(loader.loadTestsFromTestCase(TestComplexityEvaluator))
    suite.addTests(loader.loadTestsFromTestCase(TestProcessingLimiter))
    suite.addTests(loader.loadTestsFromTestCase(TestAutoIssueProcessor))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEnd))

    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 結果サマリー
    print(f"\n📊 テスト結果サマリー:")
    print(f"   実行: {result.testsRun}件")
    print(f"   成功: {result.testsRun - len(result.failures) - len(result.errors)}件")
    print(f"   失敗: {len(result.failures)}件")
    print(f"   エラー: {len(result.errors)}件")

    # 終了コード
    sys.exit(0 if result.wasSuccessful() else 1)
