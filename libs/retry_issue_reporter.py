#!/usr/bin/env python3
"""
リトライ詳細記録 - Issue コメント機能
Auto Issue Processorのリトライプロセスを透明化し、Issueに詳細記録
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import traceback

from github import Github
from github.Issue import Issue

logger = logging.getLogger(__name__)


class RetryIssueReporter:
    """リトライ詳細をIssueに記録するレポーター"""
    
    def __init__(self, github_token: str = None, repo_owner: str = None, repo_name: str = None):
        """
        初期化
        
        Args:
            github_token: GitHubトークン
            repo_owner: リポジトリオーナー
            repo_name: リポジトリ名
        """
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.repo_owner = repo_owner or os.getenv("GITHUB_REPO_OWNER", "ext-maru")
        self.repo_name = repo_name or os.getenv("GITHUB_REPO_NAME", "ai-co")
        
        if not self.github_token:
            raise ValueError("GitHub token is required")
        
        self.github = Github(self.github_token)
        self.repo = self.github.get_repo(f"{self.repo_owner}/{self.repo_name}")
        
        # セッション管理
        self.session_id = f"retry-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.retry_sessions = {}
    
    def start_retry_session(self, issue_number: int, operation: str) -> str:
        """リトライセッション開始"""
        session_id = f"{self.session_id}-{issue_number}-{operation}"
        self.retry_sessions[session_id] = {
            "issue_number": issue_number,
            "operation": operation,
            "start_time": datetime.now(),
            "attempts": [],
            "final_status": None
        }
        return session_id
    
    async def record_retry_attempt(
        self,
        session_id: str,
        attempt_number: int,
        error: Exception,
        recovery_action: str,
        recovery_message: str,
        retry_delay: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """リトライ試行を記録"""
        if session_id not in self.retry_sessions:
            logger.warning(f"Unknown retry session: {session_id}")
            return
        
        session = self.retry_sessions[session_id]
        
        attempt_data = {
            "attempt": attempt_number,
            "timestamp": datetime.now(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "recovery_action": recovery_action,
            "recovery_message": recovery_message,
            "retry_delay": retry_delay,
            "context": context or {},
            "stack_trace": traceback.format_exc() if logger.isEnabledFor(logging.DEBUG) else None
        }
        
        session["attempts"].append(attempt_data)
        
        # 即座にIssueコメントを追加（リアルタイム更新）
        await self._post_retry_comment(session_id, attempt_data)
    
    async def record_retry_success(self, session_id: str, result: Dict[str, Any]) -> None:
        """リトライ成功を記録"""
        if session_id not in self.retry_sessions:
            logger.warning(f"Unknown retry session: {session_id}")
            return
        
        session = self.retry_sessions[session_id]
        session["final_status"] = "success"
        session["end_time"] = datetime.now()
        session["result"] = result
        
        await self._post_final_comment(session_id, success=True)
    
    async def record_retry_failure(self, session_id: str, final_error: Exception) -> None:
        """リトライ失敗を記録"""
        if session_id not in self.retry_sessions:
            logger.warning(f"Unknown retry session: {session_id}")
            return
        
        session = self.retry_sessions[session_id]
        session["final_status"] = "failure"
        session["end_time"] = datetime.now()
        session["final_error"] = {
            "type": type(final_error).__name__,
            "message": str(final_error)
        }
        
        await self._post_final_comment(session_id, success=False)
    
    async def _post_retry_comment(self, session_id: str, attempt_data: Dict[str, Any]) -> None:
        """リトライ試行のコメントを投稿"""
        session = self.retry_sessions[session_id]
        issue_number = session["issue_number"]
        
        try:
            issue = self.repo.get_issue(issue_number)
            
            # コメント内容生成
            comment = self._generate_retry_comment(session, attempt_data)
            
            # コメント投稿
            issue.create_comment(comment)
            logger.info(f"Posted retry attempt #{attempt_data['attempt']} comment to issue #{issue_number}")
            
        except Exception as e:
            logger.error(f"Failed to post retry comment to issue #{issue_number}: {e}")
    
    async def _post_final_comment(self, session_id: str, success: bool) -> None:
        """最終結果のコメントを投稿"""
        session = self.retry_sessions[session_id]
        issue_number = session["issue_number"]
        
        try:
            issue = self.repo.get_issue(issue_number)
            
            # 最終結果コメント生成
            comment = self._generate_final_comment(session, success)
            
            # コメント投稿
            issue.create_comment(comment)
            logger.info(f"Posted final retry result ({'success' if success else 'failure'}) to issue #{issue_number}")
            
        except Exception as e:
            logger.error(f"Failed to post final retry comment to issue #{issue_number}: {e}")
    
    def _generate_retry_comment(self, session: Dict[str, Any], attempt_data: Dict[str, Any]) -> str:
        """リトライ試行コメントを生成"""
        attempt = attempt_data["attempt"]
        timestamp = attempt_data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        error_type = attempt_data["error_type"]
        error_msg = attempt_data["error_message"][:200]  # メッセージを短縮
        recovery_action = attempt_data["recovery_action"]
        recovery_msg = attempt_data["recovery_message"]
        retry_delay = attempt_data.get("retry_delay")
        
        emoji_map = {
            "RETRY": "🔄",
            "ROLLBACK": "⏪",
            "SKIP": "⏭️",
            "ABORT": "❌",
            "CIRCUIT_BREAK": "🔌"
        }
        
        emoji = emoji_map.get(recovery_action, "🔄")
        
        comment = f"""## {emoji} Auto Issue Processor リトライ #{attempt}

**🕐 時刻**: {timestamp}  
**🔧 操作**: {session['operation']}  
**❌ エラー**: `{error_type}` - {error_msg}  
**🛠️ 回復アクション**: {recovery_action}  
**💬 詳細**: {recovery_msg}  
"""
        
        if retry_delay:
            comment += f"**⏰ 次回試行まで**: {retry_delay}秒  \n"
        
        if attempt_data.get("context"):
            context = attempt_data["context"]
            if context.get("branch_name"):
                comment += f"**🌿 ブランチ**: `{context['branch_name']}`  \n"
            if context.get("pr_number"):
                comment += f"**📋 関連PR**: #{context['pr_number']}  \n"
        
        comment += f"\n---\n*🤖 自動生成 - セッションID: `{session_id.split('-')[-3:]}`*"
        
        return comment
    
    def _generate_final_comment(self, session: Dict[str, Any], success: bool) -> str:
        """最終結果コメントを生成"""
        start_time = session["start_time"]
        end_time = session["end_time"]
        duration = (end_time - start_time).total_seconds()
        attempt_count = len(session["attempts"])
        
        if success:
            emoji = "✅"
            status = "成功"
            result = session.get("result", {})
        else:
            emoji = "❌"
            status = "失敗"
            final_error = session.get("final_error", {})
        
        comment = f"""## {emoji} Auto Issue Processor 処理{status}

**📊 処理サマリー**:
- **🔧 操作**: {session['operation']}
- **🔄 試行回数**: {attempt_count}回
- **⏰ 処理時間**: {duration:.1f}秒
- **📅 期間**: {start_time.strftime("%H:%M:%S")} → {end_time.strftime("%H:%M:%S")}

"""
        
        if success:
            comment += "**🎉 成功詳細**:\n"
            if result.get("pr_url"):
                comment += f"- **📋 作成PR**: {result['pr_url']}\n"
            if result.get("message"):
                comment += f"- **💬 メッセージ**: {result['message']}\n"
        else:
            comment += "**🚨 失敗詳細**:\n"
            comment += f"- **❌ 最終エラー**: `{final_error.get(
                'type',
                'Unknown')}` - {final_error.get('message',
                'No details'
            )}\n"
            comment += f"- **📋 推奨アクション**: 手動レビューが必要です\n"
        
        # 試行履歴の要約
        if attempt_count > 0:
            comment += f"\n**📈 試行履歴**:\n"
            for i, attempt in enumerate(session["attempts"], 1):
                comment += f"{i}. `{attempt['error_type']}` → {attempt['recovery_action']}\n"
        
        comment += f"\n---\n*🤖 自動生成 - 詳細ログは各リトライコメントを参照*"
        
        return comment
    
    async def generate_retry_analytics(self, issue_number: int, days: int = 7) -> Dict[str, Any]:
        """指定Issueのリトライ分析を生成"""
        try:
            issue = self.repo.get_issue(issue_number)
            comments = issue.get_comments()
            
            retry_comments = []
            for comment in comments:
                if "Auto Issue Processor リトライ" in comment.body:
                    retry_comments.append(comment)
            
            if not retry_comments:
                return {"message": "リトライ記録なし"}
            
            # 分析データ生成
            error_types = {}
            recovery_actions = {}
            
            for comment in retry_comments:
                # 簡単なパターンマッチングで分析
                body = comment.body
                if "エラー**: `" in body:
                    error_type = body.split("エラー**: `")[1].split("`")[0]
                    error_types[error_type] = error_types.get(error_type, 0) + 1
                
                if "回復アクション**: " in body:
                    action = body.split("回復アクション**: ")[1].split("\n")[0]
                    recovery_actions[action] = recovery_actions.get(action, 0) + 1
            
            return {
                "total_retries": len(retry_comments),
                "error_types": error_types,
                "recovery_actions": recovery_actions,
                "analysis_period": f"{days}日間",
                "last_retry": retry_comments[-1].created_at.isoformat() if retry_comments else None
            }
            
        except Exception as e:
            logger.error(f"Failed to generate retry analytics for issue #{issue_number}: {e}")
            return {"error": str(e)}
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """セッションサマリーを取得"""
        if session_id not in self.retry_sessions:
            return {"error": "Session not found"}
        
        session = self.retry_sessions[session_id]
        
        return {
            "session_id": session_id,
            "issue_number": session["issue_number"],
            "operation": session["operation"],
            "start_time": session["start_time"].isoformat(),
            "end_time": session.get(
                "end_time",
                {}).isoformat() if session.get("end_time"
            ) else None,
            "attempt_count": len(session["attempts"]),
            "final_status": session.get("final_status"),
            "duration_seconds": (session["end_time"] - session["start_time"]).total_seconds() \
                if session.get("end_time") \
                else None
        }


# 使いやすいヘルパー関数
async def with_retry_reporting(
    func,
    issue_number: int,
    operation: str,
    max_retries: int = 3,
    github_token: str = None,
    **kwargs
):
    """リトライレポート付きで関数を実行"""
    reporter = RetryIssueReporter(github_token=github_token)
    session_id = reporter.start_retry_session(issue_number, operation)
    
    for attempt in range(1, max_retries + 1):
        try:
            result = await func(**kwargs)
            await reporter.record_retry_success(session_id, {"result": result})
            return result
            
        except Exception as e:
            if attempt < max_retries:
                # リトライ試行記録
                await reporter.record_retry_attempt(
                    session_id=session_id,
                    attempt_number=attempt,
                    error=e,
                    recovery_action="RETRY",
                    recovery_message=f"試行 {attempt} 失敗、{max_retries - attempt} 回再試行します",
                    retry_delay=2 ** attempt,  # 指数バックオフ
                    context=kwargs
                )
                
                # 遅延
                await asyncio.sleep(2 ** attempt)
            else:
                # 最終失敗記録
                await reporter.record_retry_failure(session_id, e)
                raise e


# 統合例
if __name__ == "__main__":
    async def test_integration():
        """統合テスト例"""
        
        # テスト用の失敗する関数
        async def failing_function(fail_count=2):
            """failing_functionメソッド"""
            if hasattr(failing_function, 'call_count'):
                failing_function.call_count += 1
            else:
                failing_function.call_count = 1
            
            if failing_function.call_count <= fail_count:
                raise ConnectionError(f"Simulated failure #{failing_function.call_count}")
            
            return {"success": True, "message": f"Success on attempt {failing_function.call_count}"}
        
        # リトライレポート付きで実行
        try:
            result = await with_retry_reporting(
                failing_function,
                issue_number=999,  # テスト用Issue番号
                operation="test_operation",
                max_retries=4,
                fail_count=2
            )
            print(f"Success: {result}")
        except Exception as e:
            print(f"Final failure: {e}")
    
    # テスト実行（実際のGitHubトークンが必要）
    # asyncio.run(test_integration())
    print("Retry Issue Reporter implementation complete!")