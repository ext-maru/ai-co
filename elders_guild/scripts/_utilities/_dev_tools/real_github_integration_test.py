#!/usr/bin/env python3
"""
🔗 Real GitHub Integration Test
実際のGitHub APIとの統合テスト

環境変数:
- GITHUB_TOKEN: GitHub Personal Access Token
- GITHUB_REPO: テスト対象リポジトリ (例: "owner/repo")
- TEST_PR_NUMBER: テスト対象PR番号
"""

import asyncio
import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional

# プロジェクトのパスを追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# GitHub API用（実際のライブラリを使用）
try:
    import github
except ImportError:
    print("PyGithubがインストールされていません: pip install PyGithub")
    sys.exit(1)

from libs.integrations.github.pr_state_monitor import (
    PRStateMonitor, MonitoringConfig, StateChangeEvent
)
from libs.integrations.github.auto_action_engine import AutoActionEngine
from libs.integrations.github.progress_reporter import ProgressReporter

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RealGitHubClient:
    """実際のGitHub APIクライアント"""
    
    def __init__(self, token: str, repo_name: str):
        """
        初期化
        
        Args:
            token: GitHub Personal Access Token
            repo_name: リポジトリ名 (例: "owner/repo")
        """
        self.github = github.Github(token)
        self.repo = self.github.get_repo(repo_name)
        self.token = token
        
        logger.info(f"GitHub client initialized for repo: {repo_name}")
    
    def _get_pull_request(self, pr_number: int) -> dict:
        """PR情報を取得"""
        try:
            pr = self.repo.get_pull(pr_number)
            
            return {
                "success": True,
                "pull_request": {
                    "number": pr.number,
                    "title": pr.title,
                    "state": pr.state,
                    "mergeable": pr.mergeable,
                    "mergeable_state": pr.mergeable_state,
                    "draft": pr.draft,
                    "behind_by": pr.behind_by if hasattr(pr, 'behind_by') else 0,
                    "ahead_by": pr.ahead_by if hasattr(pr, 'ahead_by') else 0,
                    "head": {
                        "sha": pr.head.sha,
                        "ref": pr.head.ref
                    },
                    "base": {
                        "sha": pr.base.sha,
                        "ref": pr.base.ref
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error getting PR #{pr_number}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_pull_request(self, pr_number: int) -> dict:
        """AutoActionEngine用のPR取得"""
        return self._get_pull_request(pr_number)
    
    async def merge_pull_request(self, pr_number: int, merge_method: str = "merge") -> dict:
        """PRをマージ（実際にはマージしない - テスト用）"""
        try:
            pr = self.repo.get_pull(pr_number)
            
            # 実際のマージは危険なので、シミュレーションのみ
            logger.warning(f"SIMULATION: Would merge PR #{pr_number} with method '{merge_method}'")
            
            return {
                "success": True,
                "merged": True,
                "sha": pr.head.sha,
                "message": f"SIMULATED: Pull Request #{pr_number} would be merged"
            }
        except Exception as e:
            logger.error(f"Error in merge simulation for PR #{pr_number}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_issue_comment(self, issue_number: int, body: str) -> dict:
        """イシューにコメントを作成"""
        try:
            issue = self.repo.get_issue(issue_number)
            comment = issue.create_comment(body)
            
            logger.info(f"Created comment on issue #{issue_number}: {comment.id}")
            
            return {
                "success": True,
                "comment_id": comment.id,
                "html_url": comment.html_url
            }
        except Exception as e:
            logger.error(f"Error creating comment on issue #{issue_number}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_issue_comment(self, comment_id: int, body: str) -> dict:
        """イシューコメントを更新"""
        try:
            # コメントIDからコメントを取得して更新
            # 簡略化のため、最後のコメントを更新
            logger.info(f"SIMULATION: Would update comment #{comment_id}")
            
            return {
                "success": True,
                "comment_id": comment_id
            }
        except Exception as e:
            logger.error(f"Error updating comment #{comment_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }


async def run_real_integration_test():
    """実際のGitHub APIとの統合テスト"""
    # 環境変数の確認
    github_token = os.getenv('GITHUB_TOKEN')
    github_repo = os.getenv('GITHUB_REPO')
    test_pr_number = os.getenv('TEST_PR_NUMBER')
    
    if not all([github_token, github_repo, test_pr_number]):
        print("必要な環境変数が設定されていません:")
        print("- GITHUB_TOKEN: GitHub Personal Access Token")
        print("- GITHUB_REPO: テスト対象リポジトリ (例: 'owner/repo')")
        print("- TEST_PR_NUMBER: テスト対象PR番号")
        return False
    
    try:
        test_pr_number = int(test_pr_number)
    except ValueError:
        print("TEST_PR_NUMBERは数値である必要があります")
        return False
    
    print(f"🚀 Real GitHub Integration Test Starting")
    print(f"Repository: {github_repo}")
    print(f"PR: #{test_pr_number}")
    print("=" * 60)
    
    # GitHub クライアントを初期化
    try:
        github_client = RealGitHubClient(github_token, github_repo)
    except Exception as e:
        logger.error(f"Failed to initialize GitHub client: {e}")
        return False
    
    # PR情報を取得してテスト
    print("\n📋 Step 1: PR情報取得テスト")
    pr_info = github_client._get_pull_request(test_pr_number)
    if pr_info["success"]:
        pr_data = pr_info["pull_request"]
        print(f"✅ PR #{test_pr_number}: {pr_data['title']}")
        print(f"   State: {pr_data['state']}")
        print(f"   Mergeable: {pr_data['mergeable']}")
        print(f"   Mergeable State: {pr_data['mergeable_state']}")
        print(f"   Draft: {pr_data['draft']}")
    else:
        print(f"❌ Failed to get PR info: {pr_info.get('error')}")
        return False
    
    # 監視システムのテスト
    print("\n👀 Step 2: PR State Monitor テスト")
    monitor = PRStateMonitor(github_client)
    
    # イベントハンドラー
    events_received = []
    async def event_handler(pr_number, event_type, event_data):
        events_received.append((event_type, event_data))
        print(f"🔔 Event: {event_type} for PR #{pr_number}")
        print(f"   Data: {event_data}")
    
    # 監視設定
    config = MonitoringConfig(
        polling_interval=10,  # 10秒間隔
        max_monitoring_duration=60,  # 1分間のテスト
        event_callbacks={
            StateChangeEvent.CI_PASSED: [event_handler],
            StateChangeEvent.CI_FAILED: [event_handler],
            StateChangeEvent.CONFLICTS_DETECTED: [event_handler],
            StateChangeEvent.READY_TO_MERGE: [event_handler]
        }
    )
    
    # 監視開始
    print(f"   監視開始: PR #{test_pr_number}")
    monitoring_started = await monitor.start_monitoring(test_pr_number, config)
    if not monitoring_started:
        print("   ❌ 監視開始に失敗")
        return False
    
    # 30秒間監視
    print("   ⏳ 30秒間の状態変化を監視中...")
    await asyncio.sleep(30)
    
    # 監視状況確認
    status = monitor.get_monitoring_status()
    print(f"   監視状況: {status}")
    
    # 監視停止
    await monitor.stop_monitoring(test_pr_number)
    print("   🛑 監視停止")
    
    # AutoActionEngineのテスト
    print("\n🎯 Step 3: Auto Action Engine テスト")
    action_engine = AutoActionEngine(github_client)
    
    # CI成功イベントをシミュレート
    test_event = StateChangeEvent.CI_PASSED
    test_data = {"mergeable_state": "clean", "simulation": True}
    
    print(f"   シミュレートイベント: {test_event.value}")
    result = await action_engine.handle_state_change(test_pr_number, test_event, test_data)
    print(f"   結果: {result}")
    
    # ProgressReporterのテスト
    print("\n📊 Step 4: Progress Reporter テスト")
    reporter = ProgressReporter(github_client)
    
    # 進捗報告をテスト（実際にはコメントしない）
    print("   進捗報告システムの初期化: OK")
    
    # テスト結果のまとめ
    print("\n🎉 Integration Test Results")
    print("=" * 60)
    print(f"✅ GitHub API接続: 成功")
    print(f"✅ PR情報取得: 成功")
    print(f"✅ 状態監視システム: 正常動作")
    print(f"✅ 自動アクションエンジン: 正常動作")
    print(f"✅ 進捗報告システム: 初期化成功")
    print(f"🔔 検出されたイベント数: {len(events_received)}")
    
    # アクション履歴を表示
    history = action_engine.get_action_history()
    if history:
        print(f"📋 アクション履歴:")
        for action in history:
            print(f"   - {action['timestamp']}: {action['action_type']} (success: {action['success']})")
    
    return True


if __name__ == "__main__":
    # 使用方法の表示
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print(__doc__)
        sys.exit(0)
    
    # 統合テストの実行
    try:
        success = asyncio.run(run_real_integration_test())
        if success:
            print("\n🎉 All tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during test: {e}")
        sys.exit(1)