#!/usr/bin/env python3
"""
Auto Issue Processor A2A対応のテスト
独立プロセスでのIssue処理とPIDロック回避を検証
"""

import asyncio
import json
import os

import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

@pytest.mark.asyncio
class TestAutoIssueProcessorA2A(unittest.IsolatedAsyncioTestCase):
    """Auto Issue ProcessorのA2A機能テスト"""

    def setUp(self):
        """テスト環境のセットアップ"""
        # 環境変数の設定
        os.environ["GITHUB_TOKEN"] = "test_token"
        os.environ["GITHUB_REPO_OWNER"] = "test_owner"
        os.environ["GITHUB_REPO_NAME"] = "test_repo"
        
        # テスト用一時ディレクトリ

    @patch("libs.integrations.github.auto_issue_processor.Github")
    @patch("libs.integrations.github.auto_issue_processor.ClaudeCLIExecutor")
    async def test_process_issue_isolated(self, mock_claude_cli, mock_github):
        """独立プロセスでのIssue処理のテスト"""
        from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
        
        # モックの設定
        mock_repo = MagicMock()
        mock_github.return_value.get_repo.return_value = mock_repo
        
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "Test issue body"
        mock_issue.labels = []
        
        # Claude CLI実行結果のモック
        mock_executor = MagicMock()
        mock_executor.execute.return_value = json.dumps({
            "status": "success",
            "pr_number": 456,
            "pr_url": "https://github.com/test/repo/pull/456"
        })
        mock_claude_cli.return_value = mock_executor
        
        # テスト実行
        processor = AutoIssueProcessor()
        processor._check_existing_pr_for_issue = AsyncMock(return_value=None)
        result = await processor.process_issue_isolated(mock_issue)
        
        # 検証
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["pr_number"], 456)
        
        # Claude CLIが正しいプロンプトで呼ばれたか確認
        mock_executor.execute.assert_called_once()
        call_args = mock_executor.execute.call_args[1]
        self.assertIn("番号: #123", call_args["prompt"])
        self.assertIn("Test Issue", call_args["prompt"])

    @patch("libs.integrations.github.auto_issue_processor.Github")
    @patch("libs.integrations.github.auto_issue_processor.asyncio.create_task")
    async def test_process_issues_a2a_parallel(self, mock_create_task, mock_github):
        """複数Issueの並列処理テスト"""
        from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
        
        # モックの設定
        mock_repo = MagicMock()
        mock_github.return_value.get_repo.return_value = mock_repo
        
        # 5つのIssueを作成
        mock_issues = []
        for i in range(5):
            issue = MagicMock()
            issue.number = 100 + i
            issue.title = f"Issue {i}"
            issue.body = f"Body {i}"
            issue.labels = []
            mock_issues.append(issue)
        
        # タスク作成のモック
        mock_tasks = []
        for i in range(5):
            task = AsyncMock()
            task.return_value = {"status": "success", "issue_number": 100 + i}
            mock_tasks.append(task)
        
        mock_create_task.side_effect = mock_tasks
        
        # テスト実行
        processor = AutoIssueProcessor()
        processor.process_issue_isolated = AsyncMock(
            side_effect=[{"status": "success", "issue_number": 100 + i} for i in range(5)]
        )
        
        results = await processor.process_issues_a2a(mock_issues)
        
        # 検証：5つのタスクが作成された
        self.assertEqual(len(results), 5)
        self.assertEqual(processor.process_issue_isolated.call_count, 5)

    @patch("libs.integrations.github.auto_issue_processor.Github")
    async def test_a2a_default_enabled(self, mock_github):
        """A2Aがデフォルトで有効なことを確認"""
        from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
        
        # モックの設定
        mock_repo = MagicMock()
        mock_github.return_value.get_repo.return_value = mock_repo
        
        processor = AutoIssueProcessor()
        
        # A2Aは常に有効（a2a_enabledプロパティは削除済み）
        self.assertEqual(processor.a2a_max_parallel, 5)  # デフォルト並列度

    @patch("libs.integrations.github.auto_issue_processor.Github")
    @patch("libs.integrations.github.auto_issue_processor.ClaudeCLIExecutor")
    async def test_a2a_error_handling(self, mock_claude_cli, mock_github):
        """A2A処理のエラーハンドリングテスト"""
        from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
        
        # モックの設定
        mock_repo = MagicMock()
        mock_github.return_value.get_repo.return_value = mock_repo
        
        mock_issue = MagicMock()
        mock_issue.number = 999
        mock_issue.title = "Error Issue"
        mock_issue.body = "This will fail"
        
        # Claude CLIがエラーを返す
        mock_executor = MagicMock()
        mock_executor.execute.side_effect = Exception("Claude CLI error")
        mock_claude_cli.return_value = mock_executor
        
        # テスト実行
        processor = AutoIssueProcessor()
        processor._check_existing_pr_for_issue = AsyncMock(return_value=None)
        result = await processor.process_issue_isolated(mock_issue)
        
        # エラーが適切に処理されたか確認
        self.assertEqual(result["status"], "error")
        self.assertIn("Claude CLI error", result["message"])

    @patch("libs.integrations.github.auto_issue_processor.Github")
    async def test_a2a_concurrency_limit(self, mock_github):
        """A2A並列度制限のテスト"""
        from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
        
        # モックの設定
        mock_repo = MagicMock()
        mock_github.return_value.get_repo.return_value = mock_repo
        
        # 10個のIssueを作成
        mock_issues = []
        for i in range(10):
            issue = MagicMock()
            issue.number = 200 + i
            mock_issues.append(issue)
        
        processor = AutoIssueProcessor()
        processor.a2a_max_parallel = 5  # 最大5並列
        
        # 実行中のタスク数を記録
        running_count = {"current": 0, "max": 0}
        
        async def mock_process_isolated(issue):
            """mock_process_isolatedを処理"""
            running_count["current"] += 1
            running_count["max"] = max(running_count["max"], running_count["current"])
            await asyncio.sleep(0.01)  # 短い遅延
            running_count["current"] -= 1
            return {"status": "success"}
        
        processor.process_issue_isolated = mock_process_isolated
        
        # テスト実行
        await processor.process_issues_a2a(mock_issues)
        
        # 同時実行数が5を超えないことを確認
        self.assertLessEqual(running_count["max"], 5)

    @patch("libs.integrations.github.auto_issue_processor.Github")
    async def test_process_existing_pr_skip(self, mock_github):
        """既存PRがある場合のスキップ処理テスト"""
        from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
        
        # モックの設定
        mock_repo = MagicMock()
        mock_github.return_value.get_repo.return_value = mock_repo
        
        # 既存PRのモック
        mock_pr = MagicMock()
        mock_pr.number = 789
        mock_pr.html_url = "https://github.com/test/repo/pull/789"
        
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue with PR"
        
        processor = AutoIssueProcessor()
        processor._check_existing_pr_for_issue = AsyncMock(return_value={
            "number": mock_pr.number,
            "html_url": mock_pr.html_url
        })
        
        # テスト実行
        result = await processor.process_issue_isolated(mock_issue)
        
        # 検証
        self.assertEqual(result["status"], "already_exists")
        self.assertEqual(result["pr_url"], mock_pr.html_url)
        self.assertIn("already has PR", result["message"])

if __name__ == "__main__":
    pytest.main([__file__, "-v"])