#!/usr/bin/env python3
"""
🔄 PR監視システム統合テスト
PR状態の継続的監視システムの動作確認
"""

import asyncio
import sys
import os
from datetime import datetime

# プロジェクトのパスを追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from libs.integrations.github.pr_state_monitor import (
    PRStateMonitor, MonitoringConfig, StateChangeEvent
)
from libs.integrations.github.auto_action_engine import AutoActionEngine
from libs.integrations.github.progress_reporter import ProgressReporter


class MockGitHubClient:
    """モックGitHubクライアント"""
    def __init__(self):
        self.pr_state = "open"
        self.mergeable_state = "unstable"
        self.mergeable = None
        self.call_count = 0
    
    def _get_pull_request(self, pr_number):
        """PRの状態を返す（時間経過で変化をシミュレート）"""
        self.call_count += 1
        
        # 3回目の呼び出しでCI成功
        if self.call_count >= 3:
            self.mergeable = True
            self.mergeable_state = "clean"
        
        return {
            "success": True,
            "pull_request": {
                "number": pr_number,
                "title": "テストPR",
                "state": self.pr_state,
                "mergeable": self.mergeable,
                "mergeable_state": self.mergeable_state,
                "draft": False,
                "behind_by": 0,
                "ahead_by": 3
            }
        }
    
    def get_pull_request(self, pr_number):
        """PRの状態を返す（AutoActionEngine用）"""
        return self._get_pull_request(pr_number)
    
    async def merge_pull_request(self, pr_number):
        """PRをマージ（モック）"""
        self.pr_state = "merged"
        return {
            "success": True,
            "sha": "abc123def456",
            "merged": True,
            "message": "Pull Request successfully merged"
        }
    
    async def create_issue_comment(self, issue_number, body):
        """イシューコメント作成（モック）"""
        print(f"\n=== Issue #{issue_number} に新規コメント ===")
        print(body)
        print("=" * 50)
        return {"success": True, "comment_id": 12345}
    
    async def update_issue_comment(self, comment_id, body):
        """イシューコメント更新（モック）"""
        print(f"\n=== コメント #{comment_id} を更新 ===")
        print(body)
        print("=" * 50)
        return {"success": True}


async def test_pr_monitoring():
    """PR監視システムのテスト"""
    print("🚀 PR監視システムの統合テストを開始します\n")
    
    # モッククライアントを作成
    github_client = MockGitHubClient()
    
    # 各コンポーネントを初期化
    monitor = PRStateMonitor(github_client)
    action_engine = AutoActionEngine(github_client)
    reporter = ProgressReporter(github_client)
    
    # テスト用のPR番号とIssue番号
    pr_number = 123
    issue_number = 147
    
    # 進捗報告を初期化
    print("📊 進捗報告を初期化...")
    await reporter.create_initial_report(
        pr_number=pr_number,
        issue_number=issue_number,
        title="マージ状態の継続的監視システム構築"
    )
    
    # イベントハンドラーを定義
    async def handle_state_change(pr_num, event_type, event_data):
        """状態変化時のハンドラー"""
        print(f"\n🔔 イベント検出: {event_type.value}")
        print(f"   データ: {event_data}")
        
        # 進捗を更新
        if event_type == StateChangeEvent.CI_STARTED:
            await reporter.update_progress(
                issue_number=issue_number,
                state="CI実行中",
                emoji="⏳",
                details={"ci_jobs_completed": 0, "ci_jobs_total": 8}
            )
        elif event_type == StateChangeEvent.CI_PASSED:
            await reporter.update_progress(
                issue_number=issue_number,
                state="CI成功",
                emoji="✅",
                details={"ci_jobs_completed": 8, "ci_jobs_total": 8}
            )
            # 自動マージを試行
            print("\n🎯 自動マージを試行...")
            result = await action_engine.handle_state_change(pr_num, event_type, event_data)
            print(f"   結果: {result}")
            
            if result.get("success"):
                await reporter.complete_monitoring(
                    issue_number=issue_number,
                    success=True,
                    final_state="マージ完了",
                    details={
                        "merge_sha": result.get("merge_sha", "unknown"),
                        "total_duration": "2分30秒"
                    }
                )
    
    # 監視設定
    config = MonitoringConfig(
        polling_interval=2,  # 2秒間隔でポーリング
        max_monitoring_duration=30,  # 最大30秒
        event_callbacks={
            StateChangeEvent.CI_STARTED: [handle_state_change],
            StateChangeEvent.CI_PASSED: [handle_state_change],
            StateChangeEvent.READY_TO_MERGE: [handle_state_change]
        }
    )
    
    # 監視を開始
    print(f"\n👀 PR #{pr_number} の監視を開始...")
    await monitor.start_monitoring(pr_number, config)
    
    # 10秒待機（その間に状態変化を検出）
    print("\n⏳ 状態変化を待機中（10秒間）...")
    await asyncio.sleep(10)
    
    # 監視状況を確認
    status = monitor.get_monitoring_status()
    print(f"\n📈 監視状況: {status}")
    
    # 監視を停止
    print(f"\n🛑 PR #{pr_number} の監視を停止...")
    await monitor.stop_monitoring(pr_number)
    
    # 最終レポート
    print("\n✅ テスト完了!")
    print(f"   アクション履歴: {action_engine.get_action_history(pr_number)}")


if __name__ == "__main__":
    # イベントループを実行
    asyncio.run(test_pr_monitoring())