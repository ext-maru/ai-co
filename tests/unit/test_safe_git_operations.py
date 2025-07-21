#!/usr/bin/env python3
"""
Safe Git Operations のテスト

Created: 2025-07-20
Author: Claude Elder
"""

import unittest
import tempfile
import os
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from libs.integrations.github.safe_git_operations import SafeGitOperations


class TestSafeGitOperations(unittest.TestCase):
    """Safe Git Operations のテストケース"""

    def setUp(self):
        """テスト前の設定"""
        self.temp_dir = tempfile.mkdtemp()
        self.safe_git = SafeGitOperations(self.temp_dir)

    def tearDown(self):
        """テスト後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('subprocess.run')
    def test_run_git_command_success(self, mock_run):
        """Gitコマンド実行（成功）のテスト"""
        # Mock設定
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # テスト実行
        success, stdout, stderr = self.safe_git._run_git_command(["status"])

        # アサーション
        self.assertTrue(success)
        self.assertEqual(stdout, "test output")
        self.assertEqual(stderr, "")
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_run_git_command_failure(self, mock_run):
        """Gitコマンド実行（失敗）のテスト"""
        # Mock設定
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error message"
        mock_run.return_value = mock_result

        # テスト実行
        success, stdout, stderr = self.safe_git._run_git_command(["status"])

        # アサーション
        self.assertFalse(success)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "error message")

    @patch('subprocess.run')
    def test_ensure_git_state_is_clean_no_changes(self, mock_run):
        """Git状態確認（変更なし）のテスト"""
        # Mock設定（変更なし）
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""  # 変更なし
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # テスト実行
        result = self.safe_git.ensure_git_state_is_clean()

        # アサーション
        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "clean")

    @patch('subprocess.run')
    def test_ensure_git_state_is_clean_with_changes(self, mock_run):
        """Git状態確認（変更あり）のテスト"""
        # Mock設定
        def mock_run_side_effect(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            
            # git status --porcelain の場合
            if "status" in args[0] and "--porcelain" in args[0]:
                mock_result.stdout = " M test.py"  # 変更あり
            # git stash の場合
            elif "stash" in args[0]:
                mock_result.stdout = "Saved working directory"
            else:
                mock_result.stdout = ""
            
            return mock_result

        mock_run.side_effect = mock_run_side_effect

        # テスト実行
        result = self.safe_git.ensure_git_state_is_clean()

        # アサーション
        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "stashed")

    @patch('subprocess.run')
    def test_safe_git_pull_success(self, mock_run):
        """安全なGit pull（成功）のテスト"""
        # Mock設定
        def mock_run_side_effect(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            
            if "status" in args[0]:
                mock_result.stdout = ""  # clean状態
            elif "fetch" in args[0]:
                mock_result.stdout = "fetch success"
            elif "branch" in args[0] and "--show-current" in args[0]:
                mock_result.stdout = "main"
            elif "merge" in args[0]:
                mock_result.stdout = "merge success"
            else:
                mock_result.stdout = ""
            
            return mock_result

        mock_run.side_effect = mock_run_side_effect

        # テスト実行
        result = self.safe_git.safe_git_pull("origin", "main")

        # アサーション
        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "pulled")

    @patch('subprocess.run')
    def test_create_feature_branch_safely_success(self, mock_run):
        """安全なfeatureブランチ作成（成功）のテスト"""
        # Mock設定
        def mock_run_side_effect(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            
            if "branch" in args[0] and "-a" in args[0]:
                mock_result.stdout = "main"  # 既存ブランチなし
            elif "checkout" in args[0]:
                mock_result.stdout = "Switched to branch"
            elif "status" in args[0]:
                mock_result.stdout = ""  # clean状態
            elif "fetch" in args[0]:
                mock_result.stdout = "fetch success"
            elif "merge" in args[0]:
                mock_result.stdout = "merge success"
            else:
                mock_result.stdout = ""
            
            return mock_result

        mock_run.side_effect = mock_run_side_effect

        # テスト実行
        result = self.safe_git.create_feature_branch_safely("test-branch", "main")

        # アサーション
        self.assertTrue(result["success"])
        self.assertEqual(result["branch_name"], "test-branch")
        self.assertEqual(result["base_branch"], "main")

    @patch('subprocess.run')
    def test_auto_commit_if_changes_no_changes(self, mock_run):
        """自動コミット（変更なし）のテスト"""
        # Mock設定
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""  # 変更なし
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # テスト実行
        result = self.safe_git.auto_commit_if_changes("test message")

        # アサーション
        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "no_changes")

    @patch('subprocess.run')
    def test_auto_commit_if_changes_with_changes(self, mock_run):
        """自動コミット（変更あり）のテスト"""
        # Mock設定
        def mock_run_side_effect(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            
            if "status" in args[0]:
                mock_result.stdout = " M test.py"  # 変更あり
            elif "add" in args[0]:
                mock_result.stdout = "files added"
            elif "commit" in args[0]:
                mock_result.stdout = "commit success"
            else:
                mock_result.stdout = ""
            
            return mock_result

        mock_run.side_effect = mock_run_side_effect

        # テスト実行
        result = self.safe_git.auto_commit_if_changes("test message")

        # アサーション
        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "committed")

    @patch('subprocess.run')
    def test_create_pr_branch_workflow_success(self, mock_run):
        """PR用ブランチ作成ワークフロー（成功）のテスト"""
        # Mock設定
        def mock_run_side_effect(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            
            if "branch" in args[0] and "--show-current" in args[0]:
                mock_result.stdout = "main"
            elif "branch" in args[0] and "-a" in args[0]:
                mock_result.stdout = "main"
            elif "status" in args[0]:
                mock_result.stdout = ""  # clean状態
            elif "checkout" in args[0]:
                mock_result.stdout = "Switched to branch"
            elif "fetch" in args[0]:
                mock_result.stdout = "fetch success"
            elif "merge" in args[0]:
                mock_result.stdout = "merge success"
            elif "push" in args[0]:
                mock_result.stdout = "push success"
            else:
                mock_result.stdout = ""
            
            return mock_result

        mock_run.side_effect = mock_run_side_effect

        # テスト実行
        result = self.safe_git.create_pr_branch_workflow("Test PR Title", "main", "feature")

        # アサーション
        self.assertTrue(result["success"])
        self.assertIn("feature/test-pr-title", result["branch_name"])
        self.assertEqual(result["base_branch"], "main")

    def test_get_current_branch_success(self):
        """現在のブランチ取得（成功）のテスト"""
        with patch.object(self.safe_git, '_run_git_command') as mock_git:
            mock_git.return_value = (True, "main", "")
            
            result = self.safe_git.get_current_branch()
            
            self.assertTrue(result["success"])
            self.assertEqual(result["branch"], "main")

    def test_get_current_branch_failure(self):
        """現在のブランチ取得（失敗）のテスト"""
        with patch.object(self.safe_git, '_run_git_command') as mock_git:
            mock_git.return_value = (False, "", "error")
            
            result = self.safe_git.get_current_branch()
            
            self.assertFalse(result["success"])
            self.assertIn("error", result["error"])

    def test_restore_original_branch_success(self):
        """元のブランチ復元（成功）のテスト"""
        with patch.object(self.safe_git, '_run_git_command') as mock_git:
            mock_git.return_value = (True, "", "")
            
            result = self.safe_git.restore_original_branch("main")
            
            self.assertTrue(result["success"])
            self.assertIn("main", result["message"])

    def test_restore_original_branch_no_branch(self):
        """元のブランチ復元（ブランチなし）のテスト"""
        result = self.safe_git.restore_original_branch("")
        
        self.assertTrue(result["success"])
        self.assertIn("No original branch", result["message"])


class TestSafeGitOperationsIntegration(unittest.TestCase):
    """Safe Git Operations の統合テストケース"""

    def test_helper_functions_exist(self):
        """ヘルパー関数の存在確認"""
        from libs.integrations.github.safe_git_operations import (
            ensure_clean_git_state,
            safe_pull,
            create_pr_branch,
            restore_branch
        )
        
        # 関数が存在することを確認
        self.assertTrue(callable(ensure_clean_git_state))
        self.assertTrue(callable(safe_pull))
        self.assertTrue(callable(create_pr_branch))
        self.assertTrue(callable(restore_branch))

    def test_safe_git_global_instance(self):
        """グローバルインスタンスの存在確認"""
        from libs.integrations.github.safe_git_operations import safe_git
        
        self.assertIsInstance(safe_git, SafeGitOperations)


if __name__ == '__main__':
    unittest.main()