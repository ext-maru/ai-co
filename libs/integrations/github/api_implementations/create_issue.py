"""
GitHub Issue作成API実装
完全なエラーハンドリングと検証機能を含む
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from github import Github, GithubException
from github.Issue import Issue

# セキュリティモジュールのインポート
try:
    from ..security.input_validator import InputValidator
    from ..security.audit_logger import AuditLogger
    from ..security.rate_limiter import RateLimiter
except ImportError:
    # セキュリティモジュールが利用できない場合の簡易実装
    class InputValidator:
        @staticmethod
        def validate_text(text, field_name, max_length=None):
            if not text:
                raise ValueError(f"{field_name} cannot be empty")
            if max_length and len(text) > max_length:
                raise ValueError(f"{field_name} exceeds maximum length of {max_length}")
            return text
        
        @staticmethod
        def validate_labels(labels):
            if not isinstance(labels, list):
                raise ValueError("Labels must be a list")
            return [str(label) for label in labels]
    
    class AuditLogger:
        @staticmethod
        def log_operation(operation, details):
            logging.info(f"Audit: {operation} - {details}")
    
    class RateLimiter:
        def check_rate_limit(self):
            return True

logger = logging.getLogger(__name__)


class GitHubIssueCreator:
    """GitHub Issue作成クラス"""
    
    def __init__(self, token: Optional[str] = None):
        """初期化
        
        Args:
            token: GitHubアクセストークン（省略時は環境変数から取得）
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable.")
        
        self.github = Github(self.token)
        self.validator = InputValidator()
        self.audit_logger = AuditLogger()
        self.rate_limiter = RateLimiter()
        
    def create_issue(
        self,
        repo_name: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        milestone: Optional[int] = None
    ) -> Issue:
        """Issueを作成
        
        Args:
            repo_name: リポジトリ名（owner/repo形式）
            title: Issueタイトル
            body: Issue本文
            labels: ラベルリスト（オプション）
            assignees: アサイニーリスト（オプション）
            milestone: マイルストーン番号（オプション）
            
        Returns:
            作成されたIssue
            
        Raises:
            ValueError: 入力検証エラー
            GithubException: GitHub APIエラー
        """
        # 入力検証
        title = self.validator.validate_text(title, "Title", max_length=255)
        body = self.validator.validate_text(body, "Body", max_length=65536)
        
        if labels:
            labels = self.validator.validate_labels(labels)
        
        # レート制限チェック
        self.rate_limiter.check_rate_limit()
        
        try:
            # リポジトリを取得
            repo = self.github.get_repo(repo_name)
            
            # Issueを作成
            create_params = {
                "title": title,
                "body": body
            }
            
            if labels:
                create_params["labels"] = labels
            
            if assignees:
                create_params["assignees"] = assignees
                
            if milestone:
                create_params["milestone"] = repo.get_milestone(milestone)
            
            issue = repo.create_issue(**create_params)
            
            # 監査ログ
            self.audit_logger.log_operation(
                "issue_created",
                {
                    "repo": repo_name,
                    "issue_number": issue.number,
                    "title": title,
                    "labels": labels,
                    "assignees": assignees
                }
            )
            
            logger.info(f"Created issue #{issue.number} in {repo_name}")
            return issue
            
        except GithubException as e:
            logger.error(f"GitHub API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating issue: {e}")
            raise
    
    def create_issue_from_template(
        self,
        repo_name: str,
        template_name: str,
        variables: Dict[str, Any]
    ) -> Issue:
        """テンプレートからIssueを作成
        
        Args:
            repo_name: リポジトリ名
            template_name: テンプレート名
            variables: テンプレート変数
            
        Returns:
            作成されたIssue
        """
        # テンプレート定義
        templates = {
            "bug": {
                "title": "🐛 Bug: {title}",
                "body": """## 🐛 Bug Report

**Description**: {description}

**Steps to Reproduce**:
{steps}

**Expected Behavior**: {expected}

**Actual Behavior**: {actual}

**Environment**:
- OS: {os}
- Version: {version}
""",
                "labels": ["bug", "needs-triage"]
            },
            "feature": {
                "title": "✨ Feature: {title}",
                "body": """## ✨ Feature Request

**Description**: {description}

**Use Case**: {use_case}

**Proposed Solution**: {solution}

**Alternatives**: {alternatives}
""",
                "labels": ["enhancement", "needs-discussion"]
            },
            "task": {
                "title": "📋 Task: {title}",
                "body": """## 📋 Task

**Objective**: {objective}

**Tasks**:
{tasks}

**Acceptance Criteria**:
{criteria}

**Due Date**: {due_date}
""",
                "labels": ["task"]
            }
        }
        
        if template_name not in templates:
            raise ValueError(f"Unknown template: {template_name}")
        
        template = templates[template_name]
        
        # テンプレート変数を適用
        title = template["title"].format(**variables)
        body = template["body"].format(**variables)
        labels = template["labels"]
        
        return self.create_issue(repo_name, title, body, labels)
    
    def create_sub_issues(
        self,
        repo_name: str,
        parent_issue_number: int,
        sub_tasks: List[Dict[str, str]]
    ) -> List[Issue]:
        """親IssueからSub Issueを作成
        
        Args:
            repo_name: リポジトリ名
            parent_issue_number: 親Issue番号
            sub_tasks: サブタスクリスト
            
        Returns:
            作成されたSub Issueのリスト
        """
        created_issues = []
        
        try:
            repo = self.github.get_repo(repo_name)
            parent_issue = repo.get_issue(parent_issue_number)
            
            for task in sub_tasks:
                title = f"[Sub] {task['title']}"
                body = f"""This is a sub-issue of #{parent_issue_number}

**Task**: {task['description']}

**Parent Issue**: #{parent_issue_number} - {parent_issue.title}
"""
                
                # 親Issueのラベルを継承
                labels = [label.name for label in parent_issue.labels]
                if "sub-issue" not in labels:
                    labels.append("sub-issue")
                
                sub_issue = self.create_issue(repo_name, title, body, labels)
                created_issues.append(sub_issue)
                
                # 親Issueにコメントを追加
                parent_issue.create_comment(
                    f"📋 Created sub-issue: #{sub_issue.number} - {task['title']}"
                )
            
            return created_issues
            
        except Exception as e:
            logger.error(f"Error creating sub-issues: {e}")
            raise


def create_issue(
    repo: str,
    title: str,
    body: str,
    labels: Optional[List[str]] = None,
    token: Optional[str] = None
) -> Dict[str, Any]:
    """シンプルなIssue作成関数
    
    Args:
        repo: リポジトリ名（owner/repo）
        title: Issueタイトル
        body: Issue本文
        labels: ラベルリスト
        token: GitHubトークン
        
    Returns:
        作成されたIssueの情報
    """
    try:
        creator = GitHubIssueCreator(token)
        issue = creator.create_issue(repo, title, body, labels)
        
        return {
            "success": True,
            "issue_number": issue.number,
            "issue_url": issue.html_url,
            "title": issue.title
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# CLI実行用
if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Create GitHub Issue")
    parser.add_argument("repo", help="Repository (owner/repo)")
    parser.add_argument("title", help="Issue title")
    parser.add_argument("body", help="Issue body")
    parser.add_argument("--labels", nargs="+", help="Labels")
    parser.add_argument("--assignees", nargs="+", help="Assignees")
    parser.add_argument("--template", help="Use template (bug/feature/task)")
    parser.add_argument("--template-vars", help="Template variables (JSON)")
    
    args = parser.parse_args()
    
    try:
        if args.template:
            # テンプレート使用
            variables = json.loads(args.template_vars) if args.template_vars else {}
            creator = GitHubIssueCreator()
            issue = creator.create_issue_from_template(args.repo, args.template, variables)
        else:
            # 通常のIssue作成
            creator = GitHubIssueCreator()
            issue = creator.create_issue(
                args.repo,
                args.title,
                args.body,
                args.labels,
                args.assignees
            )
        
        print(f"✅ Issue created successfully!")
        print(f"Issue Number: #{issue.number}")
        print(f"Issue URL: {issue.html_url}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)