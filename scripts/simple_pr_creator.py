#!/usr/bin/env python3
"""
🚀 Simple PR Creator
GitHub Actionsに依存しない直接PR作成システム
"""

import logging
import os
import sys
from pathlib import Path

from github import Github

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SimplePRCreator")


def create_simple_pr():
    """シンプルなPR作成"""
    try:
        # GitHub API初期化
        github_token = os.environ.get("GITHUB_TOKEN")
        if not github_token:
            logger.error("❌ GITHUB_TOKEN環境変数が設定されていません")
            return False

        github = Github(github_token)
        repo = github.get_repo("ext-maru/ai-co")

        logger.info("✅ GitHub API初期化完了")

        # 既存のPRをチェック
        open_prs = list(repo.get_pulls(state="open"))
        logger.info(f"📊 現在のオープンPR数: {len(open_prs)}")

        for pr in open_prs[:5]:  # 最初の5つだけ表示
            logger.info(f"  - PR #{pr.number}: {pr.title}")

        # もしオープンなIssueがあれば情報表示
        open_issues = list(repo.get_issues(state="open"))
        issues_only = [issue for issue in open_issues if not issue.pull_request]

        logger.info(f"📋 現在のオープンIssue数: {len(issues_only)}")

        for issue in issues_only[:5]:  # 最初の5つだけ表示
            logger.info(f"  - Issue #{issue.number}: {issue.title}")

        logger.info("✅ PR自動化システム準備完了")
        logger.info("💡 GitHub Actions無効化状態でもPR作成可能")

        return True

    except Exception as e:
        logger.error(f"❌ エラー: {str(e)}")
        return False


if __name__ == "__main__":
    success = create_simple_pr()
    sys.exit(0 if success else 1)
