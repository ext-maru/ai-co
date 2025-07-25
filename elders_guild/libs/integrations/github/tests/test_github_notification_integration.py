#!/usr/bin/env python3
"""
GitHub統合システム総合テスト
Enhanced GitHub Manager統合テスト
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# プロジェクトルートを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.integrations.github.github_integration_enhanced import EnhancedGitHubManager, get_enhanced_github_manager
from libs.integrations.github.github_integration import GitHubIntegrationManager
from libs.notification.github_issue_notifier import EldersGuildGitHubNotifier

class TestEnhancedGitHubManager:
    """EnhancedGitHubManager統合テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.manager = EnhancedGitHubManager(
            repo_owner="test-owner",
            repo_name="test-repo",
            token="test-token"
        )
    
    def test_initialization(self):
        """初期化テスト"""
        assert self.manager is not None
        assert isinstance(self.manager.integration_manager, GitHubIntegrationManager)
        assert isinstance(self.manager.notifier, EldersGuildGitHubNotifier)
        assert self.manager.token == "test-token"
    
    def test_repository_operations(self):
        """リポジトリ操作テスト"""
        # get_repositories のテスト
        repos = self.manager.get_repositories()
        assert isinstance(repos, list)
        if len(repos) > 0:
            repo = repos[0]
            assert "name" in repo
            assert "full_name" in repo
            # リポジトリ名はGitHubIntegrationManagerの実装に依存
    
    @patch.object(GitHubIntegrationManager, 'get_repository_structure')
    def test_get_repository_structure(self, mock_get_structure):
        """リポジトリ構造取得テスト"""
        mock_get_structure.return_value = [
            {"name": "libs", "type": "dir"},
            {"name": "README.md", "type": "file"}
        ]
        
        structure = self.manager.get_repository_structure()
        assert len(structure) == 2
        assert structure[0]["name"] == "libs"
        mock_get_structure.assert_called_once_with("")
    
    @patch.object(GitHubIntegrationManager, 'get_file_content')
    def test_get_file_content(self, mock_get_content):
        """ファイル内容取得テスト"""
        mock_get_content.return_value = "# Test Content"
        
        content = self.manager.get_file_content("README.md")
        assert content == "# Test Content"
        mock_get_content.assert_called_once_with("README.md")
    
    @patch.object(GitHubIntegrationManager, 'create_issue')
    def test_create_issue(self, mock_create_issue):
        """Issue作成テスト"""
        mock_create_issue.return_value = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "state": "open"
            }
        }
        
        result = self.manager.create_issue(
            "Test Issue",
            "Test body",
            ["test", "automated"]
        )
        
        assert result["success"] is True
        assert result["issue"]["number"] == 123
        mock_create_issue.assert_called_once_with(
            "Test Issue",
            "Test body",
            ["test", "automated"]
        )
    
    @patch.object(GitHubIntegrationManager, 'send_task_notification')
    def test_send_task_notification(self, mock_send_notification):
        """タスク通知テスト"""
        mock_send_notification.return_value = True
        
        result = self.manager.send_task_notification(
            "task-123",
            "completed",
            "Task completed successfully",
            {"details": "test"}
        )
        
        assert result is True
        mock_send_notification.assert_called_once()
    
    @patch.object(GitHubIntegrationManager, 'send_error_notification')
    def test_send_error_notification(self, mock_send_error):
        """エラー通知テスト"""
        mock_send_error.return_value = True
        
        result = self.manager.send_error_notification(
            "task-123",
            "Test error",
            "Error details",
            "HIGH"
        )
        
        assert result is True
        mock_send_error.assert_called_once()
    
    @patch.object(EldersGuildGitHubNotifier, 'send_message')
    def test_send_message(self, mock_send_message):
        """一般メッセージ送信テスト"""
        mock_send_message.return_value = True
        
        result = self.manager.send_message("Test message")
        assert result is True
        mock_send_message.assert_called_once_with("Test message", "[エルダーズギルド]")
    
    def test_get_integration_status(self):
        """統合ステータステスト"""
        status = self.manager.get_integration_status()
        
        assert status["service"] == "github"
        assert status["connected"] is True
        assert "features" in status
        assert status["features"]["repository_operations"] is True
        assert status["features"]["issue_creation"] is True
        assert status["features"]["notifications"] is True
        
        assert "capabilities" in status
        assert status["capabilities"]["elder_flow_integration"] is True
        assert status["capabilities"]["iron_will_compliance"] is True
    
    def test_health_check(self):
        """ヘルスチェックテスト"""
        health = self.manager.health_check()
        
        assert "status" in health
        assert "timestamp" in health
        assert "components" in health
        assert "integration_manager" in health["components"]
        assert "notifier" in health["components"]
    
    def test_singleton_manager(self):
        """シングルトンマネージャーテスト"""
        manager1 = get_enhanced_github_manager()
        manager2 = get_enhanced_github_manager()
        
        assert manager1 is manager2  # 同じインスタンス

class TestIntegrationScenarios:
    """統合シナリオテスト"""
    
    def test_create_issue_with_notification_not_implemented(self):
        """create_issue_with_notificationメソッドが未実装であることを確認"""
        manager = EnhancedGitHubManager()
        
        # メソッドが存在しないことを確認
        assert not hasattr(manager, 'create_issue_with_notification')
        
        # 計画書に記載されているメソッドが未実装

    @patch.object(GitHubIntegrationManager, 'create_issue')
    @patch.object(GitHubIntegrationManager, 'send_elder_council_report')
    def test_error_to_issue_flow(self, mock_report, mock_create_issue):
        """エラー発生からIssue作成までのフロー"""
        manager = EnhancedGitHubManager(
            repo_owner="test-owner",
            repo_name="test-repo",
            token="test-token"
        )
        
        # エラー通知が成功することを設定
        mock_create_issue.return_value = {
            "success": True,
            "issue": {"number": 456}
        }
        mock_report.return_value = True
        
        # エラー通知送信
        with patch.object(
            manager.integration_manager,
            'send_error_notification',
            return_value=True
        ):
            error_result = manager.send_error_notification(
                "task-789",
                "Critical error occurred",
                "Database connection failed",
                "CRITICAL"
            )
            assert error_result is True
        
        # エルダー評議会への報告
        report_result = manager.send_elder_council_report({
            "updates": ["Critical error handled"],
            "tasks_processed": 1,
            "errors": 1
        })
        assert report_result is True
    
    @patch.object(GitHubIntegrationManager, 'analyze_codebase')
    @patch.object(GitHubIntegrationManager, 'create_enhanced_commit')
    def test_code_analysis_commit_flow(self, mock_commit, mock_analyze):
        """コード分析からコミットまでのフロー"""
        manager = EnhancedGitHubManager(
            repo_owner="test-owner",
            repo_name="test-repo",
            token="test-token"
        )
        
        # コード分析
        mock_analyze.return_value = {
            "total_files": 100,
            "analyzed_files": 50,
            "issues_found": 3
        }
        
        analysis = manager.analyze_codebase(['libs', 'workers'])
        assert analysis["total_files"] == 100
        
        # 修正後のコミット
        mock_commit.return_value = True
        
        commit_result = manager.create_enhanced_commit(
            "fix-123",
            ["libs/fixed_file.py"],
            "Fixed code issues found in analysis"
        )
        assert commit_result is True

class TestMigrationCompatibility:
    """既存コードとの互換性テスト"""
    
    def test_external_services_api_compatibility(self):
        """external_services_api.pyとの互換性"""
        # creationsディレクトリのパスを追加
        creations_path = Path(__file__).parent.parent / "creations"
        if str(creations_path) not in sys.path:
            sys.path.insert(0, str(creations_path))
        
        # プロジェクトルートも追加
        project_root = Path(__file__).parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        try:
            # web-monitoring-dashboardディレクトリを直接追加
            dashboard_path = Path(__file__).parent.parent / "creations" / "web-monitoring-dashboard"
            if str(dashboard_path) not in sys.path:
                sys.path.insert(0, str(dashboard_path))
            
            # 必要なモジュールをインポート
            from libs.env_config import get_config
            import external_services_api as api
            
            # github_managerを取得
            github_manager = api.github_manager
            
            # github_managerがEnhancedGitHubManagerのインスタンスであることを確認
            assert isinstance(github_manager, EnhancedGitHubManager)
            
            # 必要なメソッドが存在することを確認
            assert hasattr(github_manager, 'get_repositories')
            assert hasattr(github_manager, 'create_issue')
            assert hasattr(github_manager, 'get_integration_status')
            assert hasattr(github_manager, 'health_check')
            
            # メソッドが呼び出し可能であることを確認
            assert callable(github_manager.get_repositories)
            assert callable(github_manager.create_issue)
            assert callable(github_manager.get_integration_status)
            assert callable(github_manager.health_check)
            
        except ImportError as e:
            # インポートエラーの詳細をデバッグ
            print(f"Import error details: {e}")
            print(f"sys.path: {sys.path}")
            pytest.skip(f"Cannot import external_services_api: {e}")
    
    def test_week2_test_compatibility(self):
        """test_week2_all_features.pyとの互換性"""
        # 必要なメソッドが実装されていることを確認
        manager = EnhancedGitHubManager()
        
        # Week2テストで使用されるメソッド
        assert callable(manager.get_repositories)
        assert callable(manager.create_issue)
        assert callable(manager.get_integration_status)
        assert callable(manager.health_check)
        
        # 戻り値の型チェック
        repos = manager.get_repositories()
        assert isinstance(repos, list)
        
        status = manager.get_integration_status()
        assert isinstance(status, dict)
        assert "service" in status
        assert "features" in status

if __name__ == "__main__":
    pytest.main([__file__, "-v"])