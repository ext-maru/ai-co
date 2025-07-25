#!/usr/bin/env python3
"""
Auto Issue Processor重複PR防止機能テスト
Issue #25: 重複処理防止機能の動作確認
"""

import asyncio
import os
import sys
import unittest
from unittest.mock import Mock, patch, AsyncMock, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.integrations.github.auto_issue_processor import (
    AutoIssueProcessor,
    AutoIssueElderFlowEngine,
)


class TestAutoIssueProcessorDuplicatePrevention(unittest.TestCase):
    """重複PR防止機能のテスト"""
    
    @patch('libs.integrations.github.auto_issue_processor.Github')
    @patch('libs.integrations.github.auto_issue_processor.ActualElderFlowEngine')
    @patch('libs.integrations.github.auto_issue_processor.GitHubCreatePullRequestImplementation')
    def setUp(self, mock_pr_creator, mock_elder_flow, mock_github):
        """テストセットアップ"""
        # GitHub APIモック
        self.mock_github = mock_github
        self.mock_repo = Mock()
        mock_github.return_value.get_repo.return_value = self.mock_repo
        
        # Elder Flow Engineモック
        self.mock_elder_flow = mock_elder_flow
        self.mock_elder_flow_instance = Mock()
        mock_elder_flow.return_value = self.mock_elder_flow_instance
        
        # PR作成モック
        self.mock_pr_creator = mock_pr_creator
        self.mock_pr_creator_instance = Mock()
        mock_pr_creator.return_value = self.mock_pr_creator_instance
        
        # 環境変数設定
        os.environ['GITHUB_TOKEN'] = 'test_token'
        os.environ['GITHUB_REPO_OWNER'] = 'test_owner'
        os.environ['GITHUB_REPO_NAME'] = 'test_repo'
        
        # Auto Issue Processorインスタンス作成
        self.processor = AutoIssueProcessor()
    
    def test_check_existing_pr_for_issue_found(self):
        """既存のPRが見つかる場合のテスト"""
        # モックPR作成
        mock_pr = Mock()
        mock_pr.number = 107
        mock_pr.html_url = 'https://github.com/test/repo/pull/107'
        mock_pr.title = 'Auto-fix: Test Issue (#25)'
        mock_pr.body = 'Closes #25'
        mock_pr.state = 'open'
        
        # get_pullsが既存のPRを返すように設定
        self.mock_repo.get_pulls.return_value = [mock_pr]
        
        # テスト実行
        result = asyncio.run(self.processor._check_existing_pr_for_issue(25))
        
        # 検証
        self.assertIsNotNone(result)
        self.assertEqual(result['number'], 107)
        self.assertEqual(result['html_url'], 'https://github.com/test/repo/pull/107')
        self.assertEqual(result['state'], 'open')
    
    def test_check_existing_pr_for_issue_not_found(self):
        """既存のPRが見つからない場合のテスト"""
        # 空のPRリストを返すように設定
        self.mock_repo.get_pulls.return_value = []
        
        # テスト実行
        result = asyncio.run(self.processor._check_existing_pr_for_issue(999))
        
        # 検証
        self.assertIsNone(result)
    
    def test_check_existing_pr_with_title_reference(self):
        """タイトルにイシュー番号が含まれるPRのテスト"""
        # モックPR作成
        mock_pr = Mock()
        mock_pr.number = 108
        mock_pr.html_url = 'https://github.com/test/repo/pull/108'
        mock_pr.title = 'Fix for issue #25'
        mock_pr.body = 'Some fix description'
        mock_pr.state = 'open'
        
        # get_pullsがPRを返すように設定
        self.mock_repo.get_pulls.return_value = [mock_pr]
        
        # テスト実行
        result = asyncio.run(self.processor._check_existing_pr_for_issue(25))
        
        # 検証
        self.assertIsNotNone(result)
        self.assertEqual(result['number'], 108)
    
    def test_execute_auto_processing_with_existing_pr(self):
        """既存のPRがある場合の自動処理テスト"""
        # モックIssue作成
        mock_issue = Mock()
        mock_issue.number = 25
        mock_issue.title = 'Test Issue'
        mock_issue.body = 'Test body'
        mock_issue.labels = []
        mock_issue.create_comment = Mock()
        
        # 既存のPRをモック
        with patch.object(self.processor, '_check_existing_pr_for_issue', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = {
                'number': 107,
                'html_url': 'https://github.com/test/repo/pull/107',
                'title': 'Existing PR',
                'state': 'open'
            }
            
            # テスト実行
            result = asyncio.run(self.processor.execute_auto_processing(mock_issue))
            
            # 検証
            self.assertEqual(result['status'], 'already_exists')
            self.assertIn('PR #107 already exists', result['message'])
            self.assertEqual(result['pr_url'], 'https://github.com/test/repo/pull/107')
            
            # コメントが投稿されたことを確認
            mock_issue.create_comment.assert_called_once()
            comment_text = mock_issue.create_comment.call_args[0][0]
            self.assertIn('Auto Issue Processor Notice', comment_text)
            self.assertIn('already has an associated PR', comment_text)
    
    def test_execute_auto_processing_without_existing_pr(self):
        """既存のPRがない場合の自動処理テスト"""
        # モックIssue作成
        mock_issue = Mock()
        mock_issue.number = 26
        mock_issue.title = 'New Issue'
        mock_issue.body = 'New issue body'
        mock_issue.labels = []
        mock_issue.create_comment = Mock()
        
        # 既存のPRがないように設定
        self.processor._check_existing_pr_for_issue = AsyncMock(return_value=None)
        
        # Elder Flowが成功を返すように設定
        self.processor.elder_flow.execute_flow = AsyncMock(return_value={
            'status': 'success',
            'pr_url': 'https://github.com/test/repo/pull/109',
            'message': 'PR created successfully'
        })
        
        # 複雑度評価をモック
        self.processor.evaluator.evaluate = AsyncMock(return_value=Mock(score=0.5))
        
        # 4賢者相談をモック
        self.processor.consult_four_sages = AsyncMock(return_value={})
        
        # 処理記録をモック
        self.processor.limiter.record_processing = AsyncMock()
        
        # テスト実行
        result = asyncio.run(self.processor.execute_auto_processing(mock_issue))
        
        # 検証
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['pr_url'], 'https://github.com/test/repo/pull/109')
        
        # 既存PRチェックが呼ばれたことを確認
        self.processor._check_existing_pr_for_issue.assert_called_once_with(26)
    
    def test_branch_name_with_timestamp(self):
        """タイムスタンプ付きブランチ名のテスト"""
        # タイムスタンプオプションを有効化
        os.environ['AUTO_ISSUE_USE_TIMESTAMP'] = 'true'
        
        # Elder Flow Engineを再作成
        flow_engine = AutoIssueElderFlowEngine()
        
        # subprocessをモック
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(stdout='main\n', returncode=0)
            
            # PR作成を試行
            result = asyncio.run(flow_engine._create_pull_request(
                issue_number=25,
                issue_title='Test Issue',
                issue_body='Test body',
                task_name='Test task'
            ))
            
            # ブランチ作成コマンドを確認
            calls = mock_run.call_args_list
            checkout_call = None
            for call in calls:
                if call[0][0][:3] == ['git', 'checkout', '-b']:
                    checkout_call = call
                    break
            
            # ブランチ名がタイムスタンプを含むことを確認
            if checkout_call:
                branch_name = checkout_call[0][0][3]
                self.assertTrue(branch_name.startswith('auto-fix/issue-25-'))
                self.assertRegex(branch_name, r'auto-fix/issue-25-\d{6}$')
    
    def test_branch_name_without_timestamp(self):
        """タイムスタンプなしブランチ名のテスト"""
        # タイムスタンプオプションを無効化
        os.environ['AUTO_ISSUE_USE_TIMESTAMP'] = 'false'
        
        # Elder Flow Engineを再作成
        flow_engine = AutoIssueElderFlowEngine()
        
        # subprocessをモック
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(stdout='main\n', returncode=0)
            
            # PR作成を試行
            result = asyncio.run(flow_engine._create_pull_request(
                issue_number=25,
                issue_title='Test Issue',
                issue_body='Test body',
                task_name='Test task'
            ))
            
            # ブランチ作成コマンドを確認
            calls = mock_run.call_args_list
            checkout_call = None
            for call in calls:
                if call[0][0][:3] == ['git', 'checkout', '-b']:
                    checkout_call = call
                    break
            
            # ブランチ名がタイムスタンプを含まないことを確認
            if checkout_call:
                branch_name = checkout_call[0][0][3]
                self.assertEqual(branch_name, 'auto-fix-issue-25')


if __name__ == '__main__':
    unittest.main()