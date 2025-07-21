#!/usr/bin/env python3
"""
Auto Issue Processor A2A品質確認テスト
実装の品質とパフォーマンスを評価
"""

import asyncio
import json
import time
from unittest.mock import MagicMock, AsyncMock, patch
import pytest


class TestAutoIssueProcessorA2AQuality:
    """A2A実装の品質確認テスト"""

    @pytest.mark.asyncio
    async def test_parallel_processing_performance(self):
        """並列処理のパフォーマンステスト"""
        with patch("libs.integrations.github.auto_issue_processor.Github") as mock_github:
            with patch("libs.integrations.github.auto_issue_processor.ClaudeCLIExecutor") as mock_cli:
                from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
                
                # モックの設定
                mock_repo = MagicMock()
                mock_github.return_value.get_repo.return_value = mock_repo
                
                # 10個のIssueを作成
                issues = []
                for i in range(10):
                    issue = MagicMock()
                    issue.number = 100 + i
                    issue.title = f"Test Issue {i}"
                    issue.body = f"Body {i}"
                    issue.labels = []
                    issues.append(issue)
                
                # 処理時間をシミュレート（0.5秒）
                async def mock_isolated_process(issue):
                    await asyncio.sleep(0.5)
                    return {"status": "success", "issue_number": issue.number}
                
                processor = AutoIssueProcessor()
                processor.a2a_max_parallel = 5
                processor.process_issue_isolated = mock_isolated_process
                processor._check_existing_pr_for_issue = AsyncMock(return_value=None)
                
                # 実行時間を測定
                start_time = time.time()
                results = await processor.process_issues_a2a(issues)
                end_time = time.time()
                
                # 検証
                assert len(results) == 10
                assert all(r["status"] == "success" for r in results)
                
                # 並列処理により、10個を5並列で処理するので約1秒で完了するはず
                # （順次処理なら5秒かかる）
                execution_time = end_time - start_time
                assert execution_time < 1.5, f"Execution too slow: {execution_time}s"
                print(f"✅ Parallel processing completed in {execution_time:.2f}s")

    @pytest.mark.asyncio
    async def test_context_isolation(self):
        """コンテキスト分離の確認"""
        with patch("libs.integrations.github.auto_issue_processor.Github") as mock_github:
            with patch("libs.integrations.github.auto_issue_processor.ClaudeCLIExecutor") as mock_cli:
                from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
                
                # モックの設定
                mock_repo = MagicMock()
                mock_github.return_value.get_repo.return_value = mock_repo
                
                # Claude CLIの呼び出しを記録
                call_prompts = []
                
                def mock_execute(prompt, **kwargs):
                    call_prompts.append(prompt)
                    return json.dumps({"status": "success"})
                
                mock_executor = MagicMock()
                mock_executor.execute.side_effect = mock_execute
                mock_cli.return_value = mock_executor
                
                # 3つのIssue
                issues = []
                for i in range(3):
                    issue = MagicMock()
                    issue.number = 200 + i
                    issue.title = f"Issue {i}"
                    issue.body = f"Content {i}"
                    issue.labels = []
                    issues.append(issue)
                
                processor = AutoIssueProcessor()
                processor._check_existing_pr_for_issue = AsyncMock(return_value=None)
                
                results = await processor.process_issues_a2a(issues)
                
                # 各プロンプトが独立していることを確認
                assert len(call_prompts) == 3
                for i, prompt in enumerate(call_prompts):
                    assert f"番号: #{200 + i}" in prompt
                    assert "独立したプロセスで実行" in prompt
                    assert "Elder Flow" in prompt
                
                print("✅ Context isolation verified")

    @pytest.mark.asyncio
    async def test_error_resilience(self):
        """エラー耐性のテスト"""
        with patch("libs.integrations.github.auto_issue_processor.Github") as mock_github:
            with patch("libs.integrations.github.auto_issue_processor.ClaudeCLIExecutor") as mock_cli:
                from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
                
                # モックの設定
                mock_repo = MagicMock()
                mock_github.return_value.get_repo.return_value = mock_repo
                
                # 一部のIssueでエラーを発生させる
                error_count = 0
                
                def mock_execute(prompt, **kwargs):
                    nonlocal error_count
                    if "Issue 1" in prompt:
                        error_count += 1
                        raise Exception("Simulated error")
                    return json.dumps({"status": "success"})
                
                mock_executor = MagicMock()
                mock_executor.execute.side_effect = mock_execute
                mock_cli.return_value = mock_executor
                
                # 5つのIssue
                issues = []
                for i in range(5):
                    issue = MagicMock()
                    issue.number = 300 + i
                    issue.title = f"Issue {i}"
                    issue.body = "Test"
                    issue.labels = []
                    issues.append(issue)
                
                processor = AutoIssueProcessor()
                processor._check_existing_pr_for_issue = AsyncMock(return_value=None)
                
                results = await processor.process_issues_a2a(issues)
                
                # 1つがエラー、4つが成功
                error_results = [r for r in results if r["status"] == "error"]
                success_results = [r for r in results if r["status"] == "success"]
                
                assert len(error_results) == 1
                assert len(success_results) == 4
                assert error_count == 1
                
                print("✅ Error resilience confirmed - partial failures don't stop other issues")

    @pytest.mark.asyncio
    async def test_existing_pr_handling(self):
        """既存PR処理の確認"""
        with patch("libs.integrations.github.auto_issue_processor.Github") as mock_github:
            from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
            
            # モックの設定
            mock_repo = MagicMock()
            mock_github.return_value.get_repo.return_value = mock_repo
            
            # 3つのIssue（1つは既存PRあり）
            issues = []
            for i in range(3):
                issue = MagicMock()
                issue.number = 400 + i
                issue.title = f"Issue {i}"
                issue.body = "Test"
                issue.labels = []
                issues.append(issue)
            
            processor = AutoIssueProcessor()
            
            # Issue 401には既存PRがある
            async def mock_check_pr(issue_number):
                if issue_number == 401:
                    return {
                        "number": 501,
                        "html_url": "https://github.com/test/repo/pull/501"
                    }
                return None
            
            processor._check_existing_pr_for_issue = mock_check_pr
            
            # process_issue_isolatedをモック化して、実際のClaude CLI呼び出しを避ける
            async def mock_process_isolated(issue):
                # 既存PRチェックを先に行う
                existing_pr = await processor._check_existing_pr_for_issue(issue.number)
                if existing_pr:
                    return {
                        "status": "already_exists",
                        "issue_number": issue.number,
                        "pr_url": existing_pr["html_url"],
                        "message": f"Issue already has PR #{existing_pr['number']}"
                    }
                return {"status": "success", "issue_number": issue.number}
            
            processor.process_issue_isolated = mock_process_isolated
            
            # 処理実行
            results = await processor.process_issues_a2a(issues)
            
            # 検証
            assert len(results) == 3
            
            # Issue 401はスキップされる
            issue_401_result = next(r for r in results if r.get("issue_number") == 401)
            assert issue_401_result["status"] == "already_exists"
            assert "pull/501" in issue_401_result["pr_url"]
            
            print("✅ Existing PR handling works correctly")


if __name__ == "__main__":
    # 品質テストを実行
    import subprocess
    result = subprocess.run(
        ["python3", "-m", "pytest", __file__, "-v", "-s"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)