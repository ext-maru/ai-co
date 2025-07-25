#!/usr/bin/env python3
"""
GitHub API実装の包括的テストスイート
Iron Will基準準拠・95%カバレッジ達成・古代エルダー#5監査対応
"""

import pytest
import os
import sys
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta
import requests
from typing import Dict, Any, List, Optional

# プロジェクトルートを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.integrations.github.api_implementations.get_issues import GitHubGetIssuesImplementation
from libs.integrations.github.api_implementations.update_issue import GitHubUpdateIssueImplementation
from libs.integrations.github.api_implementations.create_pull_request import GitHubCreatePullRequestImplementation
from libs.integrations.github.api_implementations.get_pull_requests import GitHubGetPullRequestsImplementation


class TestGitHubGetIssuesImplementation:
    """GitHub Issue取得の包括的テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.implementation = GitHubGetIssuesImplementation(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo"
        )
    
    def test_initialization_success(self):
        """正常な初期化テスト"""
        assert self.implementation.token == "test-token"
        assert self.implementation.repo_owner == "test-owner"
        assert self.implementation.repo_name == "test-repo"
        assert self.implementation.base_url == "https://api.github.com"
        assert self.implementation.max_retries == 3
        assert self.implementation.retry_delay == 1.0
        assert self.implementation.backoff_factor == 2.0
    
    def test_initialization_from_env(self):
        """環境変数からの初期化テスト"""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'env-token',
            'GITHUB_REPO_OWNER': 'env-owner',
            'GITHUB_REPO_NAME': 'env-repo'
        }):
            impl = GitHubGetIssuesImplementation()
            assert impl.token == "env-token"
            assert impl.repo_owner == "env-owner"
            assert impl.repo_name == "env-repo"
    
    def test_initialization_validation_failure(self):
        """初期化バリデーション失敗テスト"""
        with pytest.raises(ValueError, match="Repository owner and name must be specified"):
            GitHubGetIssuesImplementation(
                token="test-token",
                repo_owner="",
                repo_name=""
            )
    
    def test_get_issues_basic(self):
        """基本的なIssue取得テスト"""
        mock_response = {
            "success": True,
            "data": [
                {"number": 1, "title": "Test Issue 1", "state": "open"},
                {"number": 2, "title": "Test Issue 2", "state": "closed"}
            ],
            "headers": {"X-RateLimit-Remaining": "4999", "X-RateLimit-Reset": "1234567890"}
        }
        
        with patch.object(self.implementation, '_make_api_request', return_value=mock_response):
            result = self.implementation.get_issues()
            
            assert result["success"] is True
            assert len(result["issues"]) == 2
            assert result["total_count"] == 2
            assert "metadata" in result
            assert result["metadata"]["rate_limit_remaining"] == 4999
    
    def test_get_issues_with_all_parameters(self):
        """全パラメータ付きIssue取得テスト"""
        mock_response = {
            "success": True,
            "data": [{"number": 1, "title": "Test Issue"}],
            "headers": {}
        }
        
        with patch.object(
            self.implementation,
            '_make_api_request',
            return_value=mock_response
        ) as mock_request:
            result = self.implementation.get_issues(
                state="closed",
                labels=["bug", "enhancement"],
                assignee="testuser",
                creator="creator",
                milestone="v1.0",
                since="2024-01-01T00:00:00Z",
                sort="updated",
                direction="asc",
                per_page=50,
                max_results=100
            )
            
            assert result["success"] is True
            
            # パラメータが正しく渡されているか確認
            call_args = mock_request.call_args
            assert call_args[1]["params"]["state"] == "closed"
            assert call_args[1]["params"]["labels"] == "bug,enhancement"
            assert call_args[1]["params"]["assignee"] == "testuser"
            assert call_args[1]["params"]["creator"] == "creator"
            assert call_args[1]["params"]["milestone"] == "v1.0"
            assert call_args[1]["params"]["since"] == "2024-01-01T00:00:00Z"
            assert call_args[1]["params"]["sort"] == "updated"
            assert call_args[1]["params"]["direction"] == "asc"
            assert call_args[1]["params"]["per_page"] == 50
    
    def test_get_issues_pagination(self):
        """ページネーションテスト"""
        # 最初のページ
        first_page = {
            "success": True,
            "data": [{"number": 1, "title": "Issue 1"}],
            "headers": {
                "Link": '<https://api.github.com/repos/test/test/issues?page=2>; rel="next",  \
                    <https://api.github.com/repos/test/test/issues?page=3>; rel="last"'
            }
        }
        
        # 2ページ目
        second_page = {
            "success": True,
            "data": [{"number": 2, "title": "Issue 2"}],
            "headers": {
                "Link": '<https://api.github.com/repos/test/test/issues?page=3>; rel="next",  \
                    <https://api.github.com/repos/test/test/issues?page=3>; rel="last"'
            }
        }
        
        # 最終ページ
        last_page = {
            "success": True,
            "data": [{"number": 3, "title": "Issue 3"}],
            "headers": {}
        }
        
        with patch.object(
            self.implementation,
            '_make_api_request',
            side_effect=[first_page,
            second_page,
            last_page]
        ):
            result = self.implementation.get_issues()
            
            assert result["success"] is True
            assert len(result["issues"]) == 3
            assert result["metadata"]["total_pages"] == 3
    
    def test_get_issues_pull_request_filtering(self):
        """Pull Request除外テスト"""
        mock_response = {
            "success": True,
            "data": [
                {"number": 1, "title": "Issue 1"},
                {"number": 2, "title": "PR 1", "pull_request": {"url": "https://..."}},
                {"number": 3, "title": "Issue 2"}
            ],
            "headers": {}
        }
        
        with patch.object(self.implementation, '_make_api_request', return_value=mock_response):
            result = self.implementation.get_issues()
            
            assert result["success"] is True
            assert len(result["issues"]) == 2  # PRが除外されている
            assert result["issues"][0]["number"] == 1
            assert result["issues"][1]["number"] == 3
    
    def test_get_issues_max_results_limit(self):
        """最大結果数制限テスト"""
        mock_response = {
            "success": True,
            "data": [{"number": i, "title": f"Issue {i}"} for i in range(1, 6)],
            "headers": {}
        }
        
        with patch.object(self.implementation, '_make_api_request', return_value=mock_response):
            result = self.implementation.get_issues(max_results=3)
            
            assert result["success"] is True
            assert len(result["issues"]) == 3
            assert result["total_count"] == 3
    
    def test_get_issues_rate_limit_handling(self):
        """レート制限処理テスト"""
        # レート制限の状態を設定
        self.implementation.rate_limit_remaining = 5
        self.implementation.rate_limit_reset = int(time.time()) + 3600
        
        mock_response = {
            "success": True,
            "data": [{"number": 1, "title": "Issue 1"}],
            "headers": {"X-RateLimit-Remaining": "1", "X-RateLimit-Reset": str(int(time.time()) + 10)}
        }
        
        with patch.object(self.implementation, '_make_api_request', return_value=mock_response):
            with patch('time.sleep') as mock_sleep:
                result = self.implementation.get_issues()
                
                assert result["success"] is True
                # レート制限が更新されている
                assert self.implementation.rate_limit_remaining == 1
    
    def test_get_issues_api_error(self):
        """APIエラーテスト"""
        mock_response = {
            "success": False,
            "error": "API Error"
        }
        
        with patch.object(self.implementation, '_make_api_request', return_value=mock_response):
            result = self.implementation.get_issues()
            
            assert result["success"] is False
            assert result["error"] == "API Error"
            assert result["issues"] == []
            assert result["total_count"] == 0
    
    def test_get_issues_exception_handling(self):
        """例外処理テスト"""
        with patch.object(
            self.implementation,
            '_make_api_request',
            side_effect=Exception("Network error")
        ):
            result = self.implementation.get_issues()
            
            assert result["success"] is False
            assert "Network error" in result["error"]
            assert result["issues"] == []
            assert result["total_count"] == 0
    
    def test_get_issue_by_number_success(self):
        """特定Issue取得成功テスト"""
        mock_response = {
            "success": True,
            "data": {"number": 123, "title": "Test Issue", "state": "open"}
        }
        
        with patch.object(self.implementation, '_make_api_request', return_value=mock_response):
            result = self.implementation.get_issue_by_number(123)
            
            assert result["success"] is True
            assert result["issue"]["number"] == 123
            assert result["issue"]["title"] == "Test Issue"
    
    def test_get_issue_by_number_not_found(self):
        """特定Issue取得失敗テスト"""
        mock_response = {
            "success": False,
            "error": "Issue not found"
        }
        
        with patch.object(self.implementation, '_make_api_request', return_value=mock_response):
            result = self.implementation.get_issue_by_number(999)
            
            assert result["success"] is False
            assert result["error"] == "Issue not found"
            assert result["issue"] is None
    
    def test_search_issues_success(self):
        """Issue検索成功テスト"""
        mock_response = {
            "success": True,
            "data": {
                "items": [
                    {"number": 1, "title": "Bug report"},
                    {"number": 2, "title": "Feature request"}
                ],
                "total_count": 2
            }
        }
        
        with patch.object(self.implementation, '_make_api_request', return_value=mock_response):
            result = self.implementation.search_issues("bug")
            
            assert result["success"] is True
            assert len(result["issues"]) == 2
            assert result["total_count"] == 2
    
    def test_search_issues_with_parameters(self):
        """パラメータ付きIssue検索テスト"""
        mock_response = {
            "success": True,
            "data": {"items": [], "total_count": 0}
        }
        
        with patch.object(
            self.implementation,
            '_make_api_request',
            return_value=mock_response
        ) as mock_request:
            result = self.implementation.search_issues(
                "bug",
                per_page=50,
                sort="updated",
                order="asc"
            )
            
            assert result["success"] is True
            
            # パラメータが正しく渡されているか確認
            call_args = mock_request.call_args
            assert "bug repo:test-owner/test-repo" in call_args[1]["params"]["q"]
            assert call_args[1]["params"]["per_page"] == 50
            assert call_args[1]["params"]["sort"] == "updated"
            assert call_args[1]["params"]["order"] == "asc"
    
    def test_make_api_request_success(self):
        """APIリクエスト成功テスト"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"test": "data"}'
        mock_response.json.return_value = {"test": "data"}
        mock_response.headers = {"X-RateLimit-Remaining": "4999"}
        
        with patch('requests.request', return_value=mock_response):
            result = self.implementation._make_api_request("/test")
            
            assert result["success"] is True
            assert result["data"] == {"test": "data"}
            assert result["headers"]["X-RateLimit-Remaining"] == "4999"
    
    def test_make_api_request_rate_limit_retry(self):
        """レート制限時のリトライテスト"""
        rate_limit_response = Mock()
        rate_limit_response.status_code = 403
        rate_limit_response.text = "rate limit exceeded"
        rate_limit_response.headers = {"X-RateLimit-Reset": str(int(time.time()) + 1)}
        
        success_response = Mock()
        success_response.status_code = 200
        success_response.text = '{"success": true}'
        success_response.json.return_value = {"success": True}
        success_response.headers = {}
        
        with patch('requests.request', side_effect=[rate_limit_response, success_response]):
            with patch('time.sleep') as mock_sleep:
                result = self.implementation._make_api_request("/test")
                
                assert result["success"] is True
                mock_sleep.assert_called_once()
    
    def test_make_api_request_client_error(self):
        """クライアントエラーテスト"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        
        with patch('requests.request', return_value=mock_response):
            result = self.implementation._make_api_request("/test")
            
            assert result["success"] is False
            assert "Client error: 404" in result["error"]
            assert result["status_code"] == 404
    
    def test_make_api_request_server_error_retry(self):
        """サーバーエラーリトライテスト"""
        error_response = Mock()
        error_response.status_code = 500
        error_response.text = "Internal Server Error"
        
        success_response = Mock()
        success_response.status_code = 200
        success_response.text = '{"success": true}'
        success_response.json.return_value = {"success": True}
        success_response.headers = {}
        
        with patch('requests.request', side_effect=[error_response, success_response]):
            with patch('time.sleep') as mock_sleep:
                result = self.implementation._make_api_request("/test")
                
                assert result["success"] is True
                mock_sleep.assert_called_once()
    
    def test_make_api_request_timeout_retry(self):
        """タイムアウトリトライテスト"""
        timeout_error = requests.exceptions.Timeout("Request timeout")
        
        success_response = Mock()
        success_response.status_code = 200
        success_response.text = '{"success": true}'
        success_response.json.return_value = {"success": True}
        success_response.headers = {}
        
        with patch('requests.request', side_effect=[timeout_error, success_response]):
            with patch('time.sleep') as mock_sleep:
                result = self.implementation._make_api_request("/test")
                
                assert result["success"] is True
                mock_sleep.assert_called_once()
    
    def test_make_api_request_connection_error_retry(self):
        """接続エラーリトライテスト"""
        connection_error = requests.exceptions.ConnectionError("Connection failed")
        
        success_response = Mock()
        success_response.status_code = 200
        success_response.text = '{"success": true}'
        success_response.json.return_value = {"success": True}
        success_response.headers = {}
        
        with patch('requests.request', side_effect=[connection_error, success_response]):
            with patch('time.sleep') as mock_sleep:
                result = self.implementation._make_api_request("/test")
                
                assert result["success"] is True
                mock_sleep.assert_called_once()
    
    def test_make_api_request_max_retries_exceeded(self):
        """最大リトライ回数超過テスト"""
        error_response = Mock()
        error_response.status_code = 500
        error_response.text = "Internal Server Error"
        
        with patch('requests.request', return_value=error_response):
            with patch('time.sleep') as mock_sleep:
                result = self.implementation._make_api_request("/test")
                
                assert result["success"] is False
                assert "All retries failed" in result["error"]
                assert mock_sleep.call_count == 2  # max_retries - 1
    
    def test_update_rate_limit_info(self):
        """レート制限情報更新テスト"""
        headers = {
            "X-RateLimit-Remaining": "4999",
            "X-RateLimit-Reset": "1234567890"
        }
        
        self.implementation._update_rate_limit_info(headers)
        
        assert self.implementation.rate_limit_remaining == 4999
        assert self.implementation.rate_limit_reset == 1234567890
    
    def test_parse_link_header(self):
        """Linkヘッダーパーステスト"""
        link_header = '<https://api.github.com/repos/test/test/issues?page=2>; rel="next",  \
            <https://api.github.com/repos/test/test/issues?page=5>; rel="last"'
        
        result = self.implementation._parse_link_header(link_header)
        
        assert "next" in result
        assert "last" in result
        assert "page=2" in result["next"]
        assert "page=5" in result["last"]


class TestGitHubUpdateIssueImplementation:
    """GitHub Issue更新の包括的テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        with patch('os.makedirs'):
            with patch('logging.FileHandler'):
                self.implementation = GitHubUpdateIssueImplementation(
                    token="test-token",
                    repo_owner="test-owner",
                    repo_name="test-repo"
                )
    
    def test_initialization_success(self):
        """正常な初期化テスト"""
        assert self.implementation.token == "test-token"
        assert self.implementation.repo_owner == "test-owner"
        assert self.implementation.repo_name == "test-repo"
        assert self.implementation.enable_audit_log is True
        assert self.implementation.audit_log_file == "logs/github_issue_updates.log"
    
    def test_initialization_no_token(self):
        """トークンなし初期化失敗テスト"""
        with pytest.raises(ValueError, match="GitHub token is required"):
            GitHubUpdateIssueImplementation(
                token="",
                repo_owner="test-owner",
                repo_name="test-repo"
            )
    
    def test_update_issue_success(self):
        """Issue更新成功テスト"""
        # 現在のIssue情報
        current_issue_response = {
            "success": True,
            "data": {
                "number": 123,
                "title": "Old Title",
                "state": "open",
                "labels": [{"name": "bug"}],
                "assignees": [],
                "milestone": None
            }
        }
        
        # 更新後のIssue情報
        updated_issue_response = {
            "success": True,
            "data": {
                "number": 123,
                "title": "New Title",
                "state": "closed",
                "labels": [{"name": "bug"}, {"name": "fixed"}],
                "assignees": [{"login": "assignee1"}],
                "milestone": {"number": 1}
            }
        }
        
        with patch.object(
            self.implementation,
            '_make_api_request',
            side_effect=[current_issue_response,
            updated_issue_response]
        ):
            with patch.object(self.implementation, '_log_audit_event'):
                result = self.implementation.update_issue(
                    issue_number=123,
                    title="New Title",
                    state="closed",
                    labels=["bug", "fixed"],
                    assignees=["assignee1"],
                    milestone=1
                )
                
                assert result["success"] is True
                assert result["issue"]["title"] == "New Title"
                assert result["issue"]["state"] == "closed"
                assert "changes" in result
                assert "title" in result["changes"]
                assert result["changes"]["title"]["before"] == "Old Title"
                assert result["changes"]["title"]["after"] == "New Title"
    
    def test_update_issue_validation_failure(self):
        """Issue更新バリデーション失敗テスト"""
        result = self.implementation.update_issue(
            issue_number=0,  # 無効なIssue番号
            title="Test"
        )
        
        assert result["success"] is False
        assert "Invalid issue number" in result["error"]
    
    def test_update_issue_invalid_state(self):
        """無効な状態での更新テスト"""
        result = self.implementation.update_issue(
            issue_number=123,
            state="invalid"
        )
        
        assert result["success"] is False
        assert "Invalid state: invalid" in result["error"]
    
    def test_update_issue_no_params(self):
        """パラメータなしでの更新テスト"""
        current_issue_response = {
            "success": True,
            "data": {"number": 123, "title": "Test"}
        }
        
        with patch.object(
            self.implementation,
            '_make_api_request',
            return_value=current_issue_response
        ):
            result = self.implementation.update_issue(issue_number=123)
            
            assert result["success"] is False
            assert "No update parameters provided" in result["error"]
    
    def test_update_issue_get_current_failure(self):
        """現在のIssue取得失敗テスト"""
        current_issue_response = {
            "success": False,
            "error": "Issue not found"
        }
        
        with patch.object(
            self.implementation,
            '_make_api_request',
            return_value=current_issue_response
        ):
            result = self.implementation.update_issue(
                issue_number=123,
                title="New Title"
            )
            
            assert result["success"] is False
            assert "Issue not found" in result["error"]
    
    def test_update_issue_api_failure(self):
        """API呼び出し失敗テスト"""
        current_issue_response = {
            "success": True,
            "data": {"number": 123, "title": "Test"}
        }
        
        update_response = {
            "success": False,
            "error": "API Error"
        }
        
        with patch.object(
            self.implementation,
            '_make_api_request',
            side_effect=[current_issue_response,
            update_response]
        ):
            result = self.implementation.update_issue(
                issue_number=123,
                title="New Title"
            )
            
            assert result["success"] is False
            assert result["error"] == "API Error"
    
    def test_validate_update_params(self):
        """更新パラメータバリデーションテスト"""
        # 有効なパラメータ
        result = self.implementation._validate_update_params(
            issue_number=123,
            state="open",
            state_reason="reopened"
        )
        assert result["valid"] is True
        
        # 無効なIssue番号
        result = self.implementation._validate_update_params(
            issue_number=-1,
            state="open",
            state_reason=None
        )
        assert result["valid"] is False
        assert "Invalid issue number" in result["error"]
        
        # 無効な状態
        result = self.implementation._validate_update_params(
            issue_number=123,
            state="invalid",
            state_reason=None
        )
        assert result["valid"] is False
        assert "Invalid state: invalid" in result["error"]
        
        # 無効な状態理由
        result = self.implementation._validate_update_params(
            issue_number=123,
            state="closed",
            state_reason="invalid"
        )
        assert result["valid"] is False
        assert "Invalid state_reason: invalid" in result["error"]
    
    def test_build_update_data(self):
        """更新データ構築テスト"""
        result = self.implementation._build_update_data(
            title="New Title",
            body="New Body",
            state="closed",
            labels=["bug", "fixed"],
            assignees=["user1", "user2"],
            milestone=1,
            state_reason="completed"
        )
        
        assert result["title"] == "New Title"
        assert result["body"] == "New Body"
        assert result["state"] == "closed"
        assert result["labels"] == ["bug", "fixed"]
        assert result["assignees"] == ["user1", "user2"]
        assert result["milestone"] == 1
        assert result["state_reason"] == "completed"
    
    def test_build_update_data_none_values(self):
        """None値での更新データ構築テスト"""
        result = self.implementation._build_update_data(
            title=None,
            body=None,
            state=None,
            labels=None,
            assignees=None,
            milestone=None,
            state_reason=None
        )
        
        assert result == {}
    
    def test_calculate_changes(self):
        """変更内容計算テスト"""
        before = {
            "title": "Old Title",
            "body": "Old Body",
            "state": "open",
            "labels": [{"name": "bug"}],
            "assignees": [{"login": "user1"}],
            "milestone": {"number": 1}
        }
        
        after = {
            "title": "New Title",
            "body": "Old Body",  # 変更なし
            "state": "closed",
            "labels": [{"name": "bug"}, {"name": "fixed"}],
            "assignees": [{"login": "user2"}],
            "milestone": {"number": 2}
        }
        
        result = self.implementation._calculate_changes(before, after)
        
        assert "title" in result
        assert result["title"]["before"] == "Old Title"
        assert result["title"]["after"] == "New Title"
        
        assert "body" not in result  # 変更なし
        
        assert "state" in result
        assert result["state"]["before"] == "open"
        assert result["state"]["after"] == "closed"
        
        assert "labels" in result
        assert result["labels"]["before"] == ["bug"]
        assert result["labels"]["after"] == ["bug", "fixed"]
        
        assert "assignees" in result
        assert result["assignees"]["before"] == ["user1"]
        assert result["assignees"]["after"] == ["user2"]
        
        assert "milestone" in result
        assert result["milestone"]["before"] == 1
        assert result["milestone"]["after"] == 2
    
    def test_extract_list_field(self):
        """リストフィールド抽出テスト"""
        # ラベル
        labels = [{"name": "bug"}, {"name": "enhancement"}]
        result = self.implementation._extract_list_field(labels, "labels")
        assert result == ["bug", "enhancement"]
        
        # アサイン者
        assignees = [{"login": "user1"}, {"login": "user2"}]
        result = self.implementation._extract_list_field(assignees, "assignees")
        assert result == ["user1", "user2"]
        
        # 空の場合
        result = self.implementation._extract_list_field(None, "labels")
        assert result == []
        
        result = self.implementation._extract_list_field([], "labels")
        assert result == []
    
    def test_get_current_user_success(self):
        """現在のユーザー取得成功テスト"""
        mock_response = {
            "success": True,
            "data": {"login": "testuser"}
        }
        
        with patch.object(self.implementation, '_make_api_request', return_value=mock_response):
            result = self.implementation._get_current_user()
            assert result == "testuser"
    
    def test_get_current_user_failure(self):
        """現在のユーザー取得失敗テスト"""
        mock_response = {
            "success": False,
            "error": "API Error"
        }
        
        with patch.object(self.implementation, '_make_api_request', return_value=mock_response):
            result = self.implementation._get_current_user()
            assert result == "unknown"
    
    def test_log_audit_event(self):
        """監査ログ記録テスト"""
        changes = {"title": {"before": "Old", "after": "New"}}
        
        with patch.object(self.implementation, 'audit_logger') as mock_logger:
            self.implementation._log_audit_event(
                action="update_issue",
                issue_number=123,
                changes=changes,
                user="testuser"
            )
            
            mock_logger.info.assert_called_once()
            
            # ログ内容を確認
            call_args = mock_logger.info.call_args[0][0]
            log_data = json.loads(call_args)
            
            assert log_data["action"] == "update_issue"
            assert log_data["issue_number"] == 123
            assert log_data["user"] == "testuser"
            assert log_data["changes"] == changes
            assert log_data["repository"] == "test-owner/test-repo"
    
    def test_add_comment_success(self):
        """コメント追加成功テスト"""
        mock_response = {
            "success": True,
            "data": {"id": 123, "body": "Test comment"}
        }
        
        with patch.object(self.implementation, '_make_api_request', return_value=mock_response):
            with patch.object(self.implementation, '_log_audit_event'):
                result = self.implementation.add_comment(123, "Test comment")
                
                assert result["success"] is True
                assert result["comment"]["body"] == "Test comment"
    
    def test_add_comment_empty_body(self):
        """空のコメント追加テスト"""
        result = self.implementation.add_comment(123, "")
        
        assert result["success"] is False
        assert "Comment body cannot be empty" in result["error"]
    
    def test_add_labels_success(self):
        """ラベル追加成功テスト"""
        mock_response = {
            "success": True,
            "data": [{"name": "bug"}, {"name": "enhancement"}]
        }
        
        with patch.object(self.implementation, '_make_api_request', return_value=mock_response):
            result = self.implementation.add_labels(123, ["bug", "enhancement"])
            
            assert result["success"] is True
            assert len(result["labels"]) == 2
    
    def test_add_labels_empty_list(self):
        """空のラベルリスト追加テスト"""
        result = self.implementation.add_labels(123, [])
        
        assert result["success"] is False
        assert "Labels list cannot be empty" in result["error"]
    
    def test_remove_label_success(self):
        """ラベル削除成功テスト"""
        delete_response = {"success": True}
        labels_response = {
            "success": True,
            "data": [{"name": "bug"}]
        }
        
        with patch.object(
            self.implementation,
            '_make_api_request',
            side_effect=[delete_response,
            labels_response]
        ):
            result = self.implementation.remove_label(123, "enhancement")
            
            assert result["success"] is True
            assert len(result["labels"]) == 1
            assert result["labels"][0]["name"] == "bug"


class TestGitHubCreatePullRequestImplementation:
    """GitHub Pull Request作成の包括的テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.implementation = GitHubCreatePullRequestImplementation(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo"
        )
    
    def test_initialization_success(self):
        """正常な初期化テスト"""
        assert self.implementation.token == "test-token"
        assert self.implementation.repo_owner == "test-owner"
        assert self.implementation.repo_name == "test-repo"
        assert self.implementation.check_conflicts is True
        assert self.implementation.auto_merge_enabled is False
    
    def test_initialization_no_token(self):
        """トークンなし初期化失敗テスト"""
        with pytest.raises(ValueError, match="GitHub token is required"):
            GitHubCreatePullRequestImplementation(
                token="",
                repo_owner="test-owner",
                repo_name="test-repo"
            )
    
    def test_create_pull_request_success(self):
        """PR作成成功テスト"""
        # ブランチ存在確認
        base_branch_response = {"success": True, "data": {"name": "main"}}
        head_branch_response = {"success": True, "data": {"name": "feature"}}
        
        # 既存PRチェック
        existing_pr_response = {"success": True, "data": []}
        
        # コミット差分チェック
        diff_response = {"success": True, "data": {"ahead_by": 5, "commits": []}}
        
        # PR作成
        pr_response = {
            "success": True,
            "data": {
                "number": 123,
                "title": "Test PR",
                "html_url": "https://github.com/test/repo/pull/123",
                "mergeable_state": "clean"
            }
        }
        
        # PRの最新情報
        updated_pr_response = {
            "success": True,
            "data": {
                "number": 123,
                "title": "Test PR",
                "html_url": "https://github.com/test/repo/pull/123",
                "mergeable_state": "clean"
            }
        }
        
        with patch.object(self.implementation, '_make_api_request', side_effect=[
            base_branch_response, head_branch_response, existing_pr_response,
            diff_response, pr_response, updated_pr_response
        ]):
            result = self.implementation.create_pull_request(
                title="Test PR",
                head="feature",
                base="main",
                body="Test PR body"
            )
            
            assert result["success"] is True
            assert result["pull_request"]["number"] == 123
            assert result["pull_request"]["title"] == "Test PR"
            assert "conflict_status" in result
            assert result["conflict_status"]["has_conflicts"] is False
    
    def test_create_pull_request_with_all_options(self):
        """全オプション付きPR作成テスト"""
        # 必要なレスポンスをモック
        responses = [
            {"success": True, "data": {"name": "main"}},  # base branch
            {"success": True, "data": {"name": "feature"}},  # head branch
            {"success": True, "data": []},  # existing PR check
            {"success": True, "data": {"ahead_by": 5}},  # diff check
            {
                "success": True,
                "data": {"number": 123,
                "title": "Test PR",
                "html_url": "https://github.com/test/repo/pull/123"}
            },  # create PR
            {"success": True},  # configure PR (labels/assignees)
            {"success": True},  # configure PR (reviewers)
            {"success": True, "data": {"number": 123, "mergeable_state": "clean"}},  # conflict check
            {"success": True, "data": {"number": 123, "title": "Test PR"}}  # final PR info
        ]
        
        with patch.object(self.implementation, '_make_api_request', side_effect=responses):
            result = self.implementation.create_pull_request(
                title="Test PR",
                head="feature",
                base="main",
                body="Test PR body",
                draft=True,
                labels=["feature"],
                assignees=["user1"],
                reviewers=["reviewer1"],
                team_reviewers=["team1"],
                milestone=1
            )
            
            assert result["success"] is True
            assert result["pull_request"]["number"] == 123
    
    def test_create_pull_request_validation_failure(self):
        """PR作成バリデーション失敗テスト"""
        # 空のタイトル
        result = self.implementation.create_pull_request(
            title="",
            head="feature",
            base="main"
        )
        
        assert result["success"] is False
        assert "Pull request title cannot be empty" in result["error"]
        
        # 同じブランチ
        result = self.implementation.create_pull_request(
            title="Test PR",
            head="main",
            base="main"
        )
        
        assert result["success"] is False
        assert "Head and base branches cannot be the same" in result["error"]
    
    def test_create_pull_request_branch_not_found(self):
        """ブランチ未発見テスト"""
        base_branch_response = {"success": False, "error": "Branch not found"}
        
        with patch.object(
            self.implementation,
            '_make_api_request',
            return_value=base_branch_response
        ):
            result = self.implementation.create_pull_request(
                title="Test PR",
                head="feature",
                base="nonexistent"
            )
            
            assert result["success"] is False
            assert "Base branch 'nonexistent' not found" in result["error"]
    
    def test_create_pull_request_existing_pr(self):
        """既存PR存在テスト"""
        responses = [
            {"success": True, "data": {"name": "main"}},  # base branch
            {"success": True, "data": {"name": "feature"}},  # head branch
            {"success": True, "data": [{"number": 456, "title": "Existing PR"}]}  # existing PR
        ]
        
        with patch.object(self.implementation, '_make_api_request', side_effect=responses):
            result = self.implementation.create_pull_request(
                title="Test PR",
                head="feature",
                base="main"
            )
            
            assert result["success"] is False
            assert "Pull request already exists: #456" in result["error"]
    
    def test_create_pull_request_no_changes(self):
        """変更なしでのPR作成テスト"""
        responses = [
            {"success": True, "data": {"name": "main"}},  # base branch
            {"success": True, "data": {"name": "feature"}},  # head branch
            {"success": True, "data": []},  # existing PR check
            {"success": True, "data": {"ahead_by": 0}}  # no changes
        ]
        
        with patch.object(self.implementation, '_make_api_request', side_effect=responses):
            result = self.implementation.create_pull_request(
                title="Test PR",
                head="feature",
                base="main"
            )
            
            assert result["success"] is False
            assert "No changes between head and base branches" in result["error"]
    
    def test_validate_pr_params(self):
        """PRパラメータバリデーションテスト"""
        # 有効なパラメータ
        result = self.implementation._validate_pr_params("Test PR", "feature", "main")
        assert result["valid"] is True
        
        # 無効なパラメータ
        result = self.implementation._validate_pr_params("", "feature", "main")
        assert result["valid"] is False
        assert "title cannot be empty" in result["error"]
        
        result = self.implementation._validate_pr_params("Test PR", "", "main")
        assert result["valid"] is False
        assert "Head branch cannot be empty" in result["error"]
        
        result = self.implementation._validate_pr_params("Test PR", "feature", "")
        assert result["valid"] is False
        assert "Base branch cannot be empty" in result["error"]
        
        result = self.implementation._validate_pr_params("Test PR", "main", "main")
        assert result["valid"] is False
        assert "Head and base branches cannot be the same" in result["error"]
    
    def test_check_branches_exist(self):
        """ブランチ存在確認テスト"""
        responses = [
            {"success": True, "data": {"name": "main"}},  # base branch
            {"success": True, "data": {"name": "feature"}}  # head branch
        ]
        
        with patch.object(self.implementation, '_make_api_request', side_effect=responses):
            result = self.implementation._check_branches_exist("feature", "main")
            assert result["success"] is True
        
        # ベースブランチが存在しない場合
        responses = [
            {"success": False, "error": "Branch not found"},  # base branch
        ]
        
        with patch.object(self.implementation, '_make_api_request', side_effect=responses):
            result = self.implementation._check_branches_exist("feature", "nonexistent")
            assert result["success"] is False
            assert "Base branch 'nonexistent' not found" in result["error"]
    
    def test_check_existing_pr(self):
        """既存PRチェックテスト"""
        # 既存PRなし
        response = {"success": True, "data": []}
        
        with patch.object(self.implementation, '_make_api_request', return_value=response):
            result = self.implementation._check_existing_pr("feature", "main")
            assert result["exists"] is False
        
        # 既存PRあり
        response = {"success": True, "data": [{"number": 123, "title": "Existing PR"}]}
        
        with patch.object(self.implementation, '_make_api_request', return_value=response):
            result = self.implementation._check_existing_pr("feature", "main")
            assert result["exists"] is True
            assert result["pr_number"] == 123
    
    def test_check_commit_diff(self):
        """コミット差分チェックテスト"""
        # 変更あり
        response = {"success": True, "data": {"ahead_by": 5, "commits": [], "files": []}}
        
        with patch.object(self.implementation, '_make_api_request', return_value=response):
            result = self.implementation._check_commit_diff("feature", "main")
            assert result["has_changes"] is True
            assert result["commits"] == []
            assert result["files_changed"] == []
        
        # 変更なし
        response = {"success": True, "data": {"ahead_by": 0}}
        
        with patch.object(self.implementation, '_make_api_request', return_value=response):
            result = self.implementation._check_commit_diff("feature", "main")
            assert result["has_changes"] is False
    
    def test_check_merge_conflicts(self):
        """マージコンフリクトチェックテスト"""
        # コンフリクトなし
        response = {"success": True, "data": {"mergeable_state": "clean", "mergeable": True}}
        
        with patch.object(self.implementation, '_make_api_request', return_value=response):
            result = self.implementation._check_merge_conflicts(123)
            assert result["has_conflicts"] is False
            assert result["mergeable"] is True
            assert result["mergeable_state"] == "clean"
        
        # コンフリクトあり
        response = {"success": True, "data": {"mergeable_state": "dirty", "mergeable": False}}
        
        with patch.object(self.implementation, '_make_api_request', return_value=response):
            result = self.implementation._check_merge_conflicts(123)
            assert result["has_conflicts"] is True
            assert result["mergeable"] is False
            assert result["mergeable_state"] == "dirty"
    
    def test_get_conflict_message(self):
        """コンフリクトメッセージ取得テスト"""
        assert self.implementation._get_conflict_message("clean") == "No conflicts, ready to merge"
        assert self.implementation._get_conflict_message("dirty") == "Merge conflicts detected"
        assert self.implementation._get_conflict_message("unstable") == "Tests are failing"
        assert self.implementation._get_conflict_message("blocked") == "Merge is blocked"
        assert self.implementation._get_conflict_message("behind") == "Branch is behind base branch"
        assert self.implementation._get_conflict_message("unknown") == "Merge status unknown"
        assert self.implementation._get_conflict_message("invalid") == "Unknown merge state"
    
    def test_create_pr_from_fork(self):
        """フォークからのPR作成テスト"""
        with patch.object(self.implementation, 'create_pull_request') as mock_create:
            mock_create.return_value = {"success": True, "pull_request": {"number": 123}}
            
            result = self.implementation.create_pr_from_fork(
                title="Test PR",
                head="feature",
                base="main",
                head_repo="fork-owner",
                body="Test body"
            )
            
            assert result["success"] is True
            mock_create.assert_called_once_with(
                title="Test PR",
                head="fork-owner:feature",
                base="main",
                body="Test body"
            )


class TestGitHubGetPullRequestsImplementation:
    """GitHub Pull Requests取得の包括的テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.implementation = GitHubGetPullRequestsImplementation(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo"
        )
    
    def test_initialization_success(self):
        """正常な初期化テスト"""
        assert self.implementation.token == "test-token"
        assert self.implementation.repo_owner == "test-owner"
        assert self.implementation.repo_name == "test-repo"
        assert self.implementation.enable_cache is True
        assert self.implementation.cache_ttl == 300
    
    def test_get_pull_requests_basic(self):
        """基本的なPR取得テスト"""
        mock_response = {
            "success": True,
            "data": [
                {
                    "number": 1,
                    "title": "Test PR 1",
                    "state": "open",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "draft": False,
                    "merged": False,
                    "additions": 10,
                    "deletions": 5,
                    "changed_files": 2,
                    "user": {"login": "user1"},
                    "labels": [],
                    "assignees": []
                }
            ],
            "headers": {}
        }
        
        with patch.object(self.implementation, '_make_api_request', return_value=mock_response):
            result = self.implementation.get_pull_requests()
            
            assert result["success"] is True
            assert len(result["pull_requests"]) == 1
            assert result["total_count"] == 1
            assert "statistics" in result
            assert "metadata" in result
    
    def test_get_pull_requests_with_filters(self):
        """フィルタ付きPR取得テスト"""
        mock_response = {
            "success": True,
            "data": [
                {
                    "number": 1,
                    "title": "Test PR",
                    "state": "closed",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "draft": False,
                    "merged": False,
                    "user": {"login": "user1"},
                    "labels": [{"name": "bug"}],
                    "assignees": [{"login": "assignee1"}],
                    "milestone": {"number": 1, "title": "v1.0"}
                }
            ],
            "headers": {}
        }
        
        with patch.object(
            self.implementation,
            '_make_api_request',
            return_value=mock_response
        ) as mock_request:
            result = self.implementation.get_pull_requests(
                state="closed",
                labels=["bug"],
                assignee="assignee1",
                creator="user1",
                milestone=1
            )
            
            assert result["success"] is True
            assert len(result["pull_requests"]) == 1
            
            # パラメータが正しく渡されているか確認
            call_args = mock_request.call_args
            assert call_args[1]["params"]["state"] == "closed"
    
    def test_get_pull_requests_cache_hit(self):
        """キャッシュヒットテスト"""
        # キャッシュにデータを設定
        cache_data = {
            "success": True,
            "pull_requests": [{"number": 1, "title": "Cached PR"}],
            "total_count": 1,
            "statistics": {},
            "metadata": {}
        }
        
        cache_key = self.implementation._generate_cache_key({"state": "open"})
        self.implementation._cache[cache_key] = {
            "timestamp": time.time(),
            "data": cache_data
        }
        
        # APIを呼び出さずにキャッシュから返されることを確認
        with patch.object(self.implementation, '_make_api_request') as mock_request:
            result = self.implementation.get_pull_requests(state="open")
            
            assert result["success"] is True
            assert result["pull_requests"][0]["title"] == "Cached PR"
            mock_request.assert_not_called()
    
    def test_get_pull_requests_cache_expired(self):
        """キャッシュ期限切れテスト"""
        # 期限切れのキャッシュデータを設定
        cache_data = {
            "success": True,
            "pull_requests": [{"number": 1, "title": "Expired PR"}],
            "total_count": 1,
            "statistics": {},
            "metadata": {}
        }
        
        cache_key = self.implementation._generate_cache_key({"state": "open"})
        self.implementation._cache[cache_key] = {
            "timestamp": time.time() - 400,  # 期限切れ
            "data": cache_data
        }
        
        # 新しいデータを返すモックレスポンス
        mock_response = {
            "success": True,
            "data": [
                {
                    "number": 2,
                    "title": "Fresh PR",
                    "state": "open",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "draft": False,
                    "merged": False,
                    "user": {"login": "user1"},
                    "labels": [],
                    "assignees": []
                }
            ],
            "headers": {}
        }
        
        with patch.object(self.implementation, '_make_api_request', return_value=mock_response):
            result = self.implementation.get_pull_requests(state="open")
            
            assert result["success"] is True
            assert result["pull_requests"][0]["title"] == "Fresh PR"
    
    def test_apply_additional_filters(self):
        """追加フィルタ適用テスト"""
        prs = [
            {
                "number": 1,
                "draft": False,
                "labels": [{"name": "bug"}],
                "milestone": {"number": 1, "title": "v1.0"},
                "assignees": [{"login": "user1"}],
                "user": {"login": "creator1"},
                "body": "Fixes issue mentioned by @user2",
                "requested_reviewers": [{"login": "reviewer1"}]
            },
            {
                "number": 2,
                "draft": True,
                "labels": [{"name": "feature"}],
                "milestone": {"number": 2, "title": "v2.0"},
                "assignees": [],
                "user": {"login": "creator2"},
                "body": "New feature implementation",
                "requested_reviewers": []
            }
        ]
        
        # ドラフト除外
        result = self.implementation._apply_additional_filters(prs, include_draft=False)
        assert len(result) == 1
        assert result[0]["number"] == 1
        
        # ラベルフィルタ
        result = self.implementation._apply_additional_filters(prs, labels=["bug"])
        assert len(result) == 1
        assert result[0]["number"] == 1
        
        # マイルストーンフィルタ（番号）
        result = self.implementation._apply_additional_filters(prs, milestone=1)
        assert len(result) == 1
        assert result[0]["number"] == 1
        
        # マイルストーンフィルタ（タイトル）
        result = self.implementation._apply_additional_filters(prs, milestone="v2.0")
        assert len(result) == 1
        assert result[0]["number"] == 2
        
        # アサイン者フィルタ
        result = self.implementation._apply_additional_filters(prs, assignee="user1")
        assert len(result) == 1
        assert result[0]["number"] == 1
        
        # 作成者フィルタ
        result = self.implementation._apply_additional_filters(prs, creator="creator2")
        assert len(result) == 1
        assert result[0]["number"] == 2
        
        # メンションフィルタ
        result = self.implementation._apply_additional_filters(prs, mentioned="user2")
        assert len(result) == 1
        assert result[0]["number"] == 1
        
        # レビュー待ちフィルタ
        result = self.implementation._apply_additional_filters(prs, reviews_requested=True)
        assert len(result) == 1
        assert result[0]["number"] == 1
    
    def test_enrich_pull_requests(self):
        """PR情報充実化テスト"""
        prs = [
            {
                "number": 1,
                "title": "Test PR",
                "state": "open",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-02T00:00:00Z",
                "draft": False,
                "merged": False,
                "mergeable_state": "clean",
                "additions": 10,
                "deletions": 5,
                "changed_files": 2,
                "requested_reviewers": [{"login": "reviewer1"}]
            }
        ]
        
        result = self.implementation._enrich_pull_requests(prs)
        
        assert len(result) == 1
        enriched_pr = result[0]
        
        assert "age_days" in enriched_pr
        assert "last_updated_days" in enriched_pr
        assert "status" in enriched_pr
        assert "size_info" in enriched_pr
        
        # ステータス情報
        status = enriched_pr["status"]
        assert status["is_draft"] is False
        assert status["is_merged"] is False
        assert status["is_closed"] is False
        assert status["has_conflicts"] is False
        assert status["review_status"] == "review_requested"
        
        # サイズ情報
        size_info = enriched_pr["size_info"]
        assert size_info["additions"] == 10
        assert size_info["deletions"] == 5
        assert size_info["changed_files"] == 2
        assert size_info["total_changes"] == 15
    
    def test_calculate_age_days(self):
        """経過日数計算テスト"""
        # 現在時刻の1日前
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.isoformat() + "Z"
        
        result = self.implementation._calculate_age_days(date_str)
        assert 0.9 < result < 1.1  # 約1日
        
        # 無効な日付
        result = self.implementation._calculate_age_days("invalid-date")
        assert result == 0
    
    def test_get_review_status(self):
        """レビューステータス取得テスト"""
        # ドラフト
        pr = {"draft": True}
        assert self.implementation._get_review_status(pr) == "draft"
        
        # レビュー待ち
        pr = {"draft": False, "requested_reviewers": [{"login": "reviewer1"}]}
        assert self.implementation._get_review_status(pr) == "review_requested"
        
        # 変更要求
        pr = {"draft": False, "requested_reviewers": [], "review_comments": 5}
        assert self.implementation._get_review_status(pr) == "changes_requested"
        
        # 準備完了
        pr = {"draft": False, "requested_reviewers": [], "review_comments": 0}
        assert self.implementation._get_review_status(pr) == "ready"
    
    def test_calculate_statistics(self):
        """統計情報計算テスト"""
        prs = [
            {
                "state": "open",
                "draft": False,
                "merged": False,
                "user": {"login": "user1"},
                "age_days": 5,
                "size_info": {"total_changes": 100}
            },
            {
                "state": "open",
                "draft": True,
                "merged": False,
                "user": {"login": "user2"},
                "age_days": 3,
                "size_info": {"total_changes": 50}
            },
            {
                "state": "closed",
                "draft": False,
                "merged": True,
                "user": {"login": "user1"},
                "age_days": 10,
                "size_info": {"total_changes": 200}
            }
        ]
        
        result = self.implementation._calculate_statistics(prs)
        
        assert result["total"] == 3
        assert result["by_state"]["open"] == 1
        assert result["by_state"]["draft"] == 1
        assert result["by_state"]["merged"] == 1
        assert result["by_author"]["user1"] == 2
        assert result["by_author"]["user2"] == 1
        assert result["average_age_days"] == 4.0  # (5 + 3) / 2 (openのみ)
        assert result["average_size"] == 116.67  # (100 + 50 + 200) / 3
    
    def test_get_pull_request_by_number_success(self):
        """特定PR取得成功テスト"""
        pr_response = {
            "success": True,
            "data": {
                "number": 123,
                "title": "Test PR",
                "state": "open",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "draft": False,
                "merged": False,
                "user": {"login": "user1"},
                "labels": [],
                "assignees": []
            }
        }
        
        reviews_response = {
            "success": True,
            "data": [
                {"id": 1, "state": "APPROVED", "user": {"login": "reviewer1"}},
                {"id": 2, "state": "CHANGES_REQUESTED", "user": {"login": "reviewer2"}}
            ]
        }
        
        comments_response = {
            "success": True,
            "data": [
                {"id": 1, "body": "Good work!", "user": {"login": "user1"}}
            ]
        }
        
        with patch.object(
            self.implementation,
            '_make_api_request',
            side_effect=[pr_response,
            reviews_response,
            comments_response]
        ):
            result = self.implementation.get_pull_request_by_number(123)
            
            assert result["success"] is True
            assert result["pull_request"]["number"] == 123
            assert len(result["reviews"]) == 2
            assert len(result["comments"]) == 1
            assert "review_summary" in result
    
    def test_summarize_reviews(self):
        """レビューサマリー作成テスト"""
        reviews = [
            {"id": 1, "state": "APPROVED", "submitted_at": "2024-01-01T00:00:00Z"},
            {"id": 2, "state": "CHANGES_REQUESTED", "submitted_at": "2024-01-02T00:00:00Z"},
            {"id": 3, "state": "COMMENTED", "submitted_at": "2024-01-03T00:00:00Z"},
            {"id": 4, "state": "DISMISSED", "submitted_at": "2024-01-04T00:00:00Z"}
        ]
        
        result = self.implementation._summarize_reviews(reviews)
        
        assert result["total_reviews"] == 4
        assert result["approved"] == 1
        assert result["changes_requested"] == 1
        assert result["commented"] == 1
        assert result["dismissed"] == 1
        assert result["latest_review"]["id"] == 4
        
        # 空のレビュー
        result = self.implementation._summarize_reviews([])
        assert result["total_reviews"] == 0
        assert result["approved"] == 0
        assert result["latest_review"] is None
    
    def test_search_pull_requests_success(self):
        """PR検索成功テスト"""
        mock_response = {
            "success": True,
            "data": {
                "items": [
                    {
                        "number": 1,
                        "title": "Bug fix PR",
                        "state": "open",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z",
                        "draft": False,
                        "merged": False,
                        "user": {"login": "user1"},
                        "labels": [],
                        "assignees": []
                    }
                ],
                "total_count": 1
            }
        }
        
        with patch.object(self.implementation, '_make_api_request', return_value=mock_response):
            result = self.implementation.search_pull_requests("bug")
            
            assert result["success"] is True
            assert len(result["pull_requests"]) == 1
            assert result["total_count"] == 1
    
    def test_generate_cache_key(self):
        """キャッシュキー生成テスト"""
        params = {
            "self": self.implementation,
            "state": "open",
            "labels": ["bug"],
            "cache_key": "should_be_excluded",
            "none_value": None
        }
        
        result = self.implementation._generate_cache_key(params)
        
        assert "self" not in result
        assert "cache_key" not in result
        assert "none_value" not in result
        assert "state" in result
        assert "labels" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])