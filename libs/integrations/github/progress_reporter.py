#!/usr/bin/env python3
"""
📊 Progress Reporter
リアルタイム進捗報告システム

機能:
- イシューコメントでの進捗更新
- リアルタイム状況報告
- 詳細ログ記録
- 履歴管理
- フォーマット済み報告書生成
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
import json
import os

logger = logging.getLogger(__name__)


@dataclass
class ProgressEntry:
    """進捗エントリ"""
    timestamp: datetime
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "message": self.message,
            "details": self.details or {}
        }


@dataclass
class ProgressSession:
    """進捗セッション"""
    pr_number: int
    issue_number: Optional[int]
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    entries: List[ProgressEntry] = field(default_factory=list)
    current_status: str = "started"
    last_comment_id: Optional[int] = None
    
    def add_entry(self, status: str, message: str, details: Optional[Dict[str, Any]] = None):
        """進捗エントリを追加"""
        entry = ProgressEntry(
            timestamp=datetime.now(),
            status=status,
            message=message,
            details=details
        )
        self.entries.append(entry)
        self.current_status = status
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "pr_number": self.pr_number,
            "issue_number": self.issue_number,
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "current_status": self.current_status,
            "entries": [entry.to_dict() for entry in self.entries],
            "last_comment_id": self.last_comment_id
        }


class ProgressReporter:
    """進捗報告システム"""
    
    # ステータス絵文字マッピング
    STATUS_EMOJIS = {
        "started": "🚀",
        "in_progress": "⏳", 
        "waiting": "⏰",
        "retrying": "🔄",
        "success": "✅",
        "completed": "🎉",
        "failed": "❌",
        "error": "💥",
        "warning": "⚠️",
        "manual_required": "👋",
        "timeout": "⏱️",
        "cancelled": "🛑"
    }
    
    # 詳細情報の表示フォーマット
    DETAIL_FORMATTERS = {
        "retry_info": lambda d: f"試行 {d.get('attempt', 0)}/{d.get('max_attempts', 0)}",
        "duration": lambda d: f"経過時間: {d.get('duration', 0):.1f}秒",
        "next_retry": lambda d: f"次回試行: {d.get('next_retry', 0)}秒後",
        "ci_status": lambda d: f"CI状況: {d.get('ci_status', 'unknown')}",
        "merge_state": lambda d: f"マージ状態: {d.get('mergeable_state', 'unknown')}"
    }
    
    def __init__(self, github_client):
        """
        初期化
        
        Args:
            github_client: GitHub APIクライアント
        """
        self.github_client = github_client
        self.active_sessions: Dict[int, ProgressSession] = {}
        self.session_history: List[ProgressSession] = []
        self.comment_update_interval = 30  # 秒
        self.last_comment_updates: Dict[int, datetime] = {}
    
    def start_session(
        self, 
        pr_number: int, 
        issue_number: Optional[int] = None,
        initial_message: str = "自動処理を開始しています..."
    ) -> str:
        """
        進捗セッションを開始
        
        Args:
            pr_number: PR番号
            issue_number: 関連イシュー番号
            initial_message: 初期メッセージ
            
        Returns:
            str: セッションID
        """
        session_id = f"pr_{pr_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session = ProgressSession(
            pr_number=pr_number,
            issue_number=issue_number,
            session_id=session_id,
            start_time=datetime.now()
        )
        
        session.add_entry("started", initial_message)
        self.active_sessions[pr_number] = session
        
        logger.info(f"Started progress session {session_id} for PR #{pr_number}")
        return session_id
    
    async def update_progress(
        self,
        pr_number: int,
        status: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        force_comment_update: bool = False
    ) -> bool:
        """
        進捗を更新
        
        Args:
            pr_number: PR番号
            status: ステータス
            message: メッセージ
            details: 詳細情報
            force_comment_update: 強制コメント更新
            
        Returns:
            bool: 更新成功/失敗
        """
        if pr_number not in self.active_sessions:
            logger.warning(f"No active session for PR #{pr_number}")
            return False
        
        session = self.active_sessions[pr_number]
        session.add_entry(status, message, details)
        
        # コメント更新の判定
        should_update_comment = (
            force_comment_update or
            self._should_update_comment(pr_number, status) or
            status in ["completed", "failed", "error", "manual_required"]
        )
        
        if should_update_comment:
            success = await self._update_issue_comment(session)
            if success:
                self.last_comment_updates[pr_number] = datetime.now()
            return success
        
        return True
    
    def _should_update_comment(self, pr_number: int, status: str) -> bool:
        """コメント更新が必要かどうか判定"""
        if pr_number not in self.last_comment_updates:
            return True
        
        last_update = self.last_comment_updates[pr_number]
        time_since_update = (datetime.now() - last_update).total_seconds()
        
        # 重要なステータス変化は即座に更新
        critical_statuses = ["error", "failed", "completed", "manual_required"]
        if status in critical_statuses:
            return True
        
        # 一定時間経過後に更新
        return time_since_update >= self.comment_update_interval
    
    async def _update_issue_comment(self, session: ProgressSession) -> bool:
        """イシューコメントを更新"""
        try:
            # コメント本文を生成
            comment_body = self._generate_comment_body(session)
            
            if session.issue_number:
                # イシューにコメント
                if session.last_comment_id:
                    # 既存コメントを更新
                    success = await self._update_existing_comment(
                        session.issue_number, session.last_comment_id, comment_body
                    )
                else:
                    # 新規コメント作成
                    comment_id = await self._create_new_comment(
                        session.issue_number, comment_body
                    )
                    if comment_id:
                        session.last_comment_id = comment_id
                        success = True
                    else:
                        success = False
            else:
                # PRにコメント（フォールバック）
                success = await self._comment_on_pr(session.pr_number, comment_body)
            
            if success:
                logger.info(f"Updated progress comment for PR #{session.pr_number}")
            else:
                logger.error(f"Failed to update progress comment for PR #{session.pr_number}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating comment for PR #{session.pr_number}: {e}")
            return False
    
    def _generate_comment_body(self, session: ProgressSession) -> str:
        """コメント本文を生成"""
        current_entry = session.entries[-1] if session.entries else None
        if not current_entry:
            return "🤖 Auto Issue Processor - 状況不明"
        
        emoji = self.STATUS_EMOJIS.get(current_entry.status, "🤖")
        
        # ヘッダー
        header = f"🤖 **Auto Issue Processor - 進捗報告**\n\n"
        
        # 現在の状況
        current_status = f"**現在の状況**: {emoji} {current_entry.message}\n"
        current_status += f"**最終更新**: {current_entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        # 詳細情報
        details_text = ""
        if current_entry.details:
            details_text = "\n**詳細情報**:\n"
            for key, value in current_entry.details.items():
                if key in self.DETAIL_FORMATTERS:
                    formatted = self.DETAIL_FORMATTERS[key](current_entry.details)
                    details_text += f"- {formatted}\n"
                else:
                    details_text += f"- {key}: {value}\n"
        
        # 処理履歴（最新5件）
        history_text = "\n**処理履歴**:\n"
        recent_entries = session.entries[-5:] if len(session.entries) > 1 else session.entries[:-1]
        
        for entry in reversed(recent_entries):
            entry_emoji = self.STATUS_EMOJIS.get(entry.status, "📝")
            time_str = entry.timestamp.strftime("%H:%M:%S")
            history_text += f"- {entry_emoji} `{time_str}` - {entry.message}\n"
        
        if not recent_entries:
            history_text += "- (履歴なし)\n"
        
        # セッション情報
        duration = (datetime.now() - session.start_time).total_seconds()
        session_info = f"\n**セッション情報**:\n"
        session_info += f"- セッションID: `{session.session_id}`\n"
        session_info += f"- 開始時刻: {session.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        session_info += f"- 経過時間: {duration:.0f}秒\n"
        session_info += f"- PR: #{session.pr_number}\n"
        
        # フッター
        footer = f"\n---\n*この進捗は自動的に更新されます*"
        
        return header + current_status + details_text + history_text + session_info + footer
    
    async def _create_new_comment(self, issue_number: int, body: str) -> Optional[int]:
        """新規コメントを作成"""
        try:
            issue = self.github_client.repo.get_issue(issue_number)
            comment = issue.create_comment(body)
            return comment.id
        except Exception as e:
            logger.error(f"Failed to create comment on issue #{issue_number}: {e}")
            return None
    
    async def _update_existing_comment(
        self, 
        issue_number: int, 
        comment_id: int, 
        body: str
    ) -> bool:
        """既存コメントを更新"""
        try:
            issue = self.github_client.repo.get_issue(issue_number)
            comment = issue.get_comment(comment_id)
            comment.edit(body)
            return True
        except Exception as e:
            logger.error(f"Failed to update comment #{comment_id} on issue #{issue_number}: {e}")
            return False
    
    async def _comment_on_pr(self, pr_number: int, body: str) -> bool:
        """PRにコメント"""
        try:
            pr = self.github_client.repo.get_pull(pr_number)
            pr.create_issue_comment(body)
            return True
        except Exception as e:
            logger.error(f"Failed to comment on PR #{pr_number}: {e}")
            return False
    
    async def complete_session(
        self, 
        pr_number: int, 
        final_status: str = "completed",
        final_message: str = "処理が完了しました",
        final_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        セッションを完了
        
        Args:
            pr_number: PR番号
            final_status: 最終ステータス
            final_message: 最終メッセージ
            final_details: 最終詳細情報
            
        Returns:
            bool: 完了成功/失敗
        """
        if pr_number not in self.active_sessions:
            return False
        
        session = self.active_sessions[pr_number]
        session.end_time = datetime.now()
        session.add_entry(final_status, final_message, final_details)
        
        # 最終コメント更新
        success = await self._update_issue_comment(session)
        
        # セッションを履歴に移動
        self.session_history.append(session)
        del self.active_sessions[pr_number]
        
        if pr_number in self.last_comment_updates:
            del self.last_comment_updates[pr_number]
        
        logger.info(f"Completed progress session for PR #{pr_number}")
        return success
    
    def get_session_status(self, pr_number: int) -> Optional[Dict[str, Any]]:
        """セッション状況を取得"""
        if pr_number in self.active_sessions:
            return self.active_sessions[pr_number].to_dict()
        return None
    
    def get_all_active_sessions(self) -> Dict[int, Dict[str, Any]]:
        """全アクティブセッションを取得"""
        return {
            pr_num: session.to_dict() 
            for pr_num, session in self.active_sessions.items()
        }
    
    def save_session_history(self, file_path: str) -> bool:
        """セッション履歴をファイルに保存"""
        try:
            history_data = [session.to_dict() for session in self.session_history]
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save session history: {e}")
            return False
    
    def load_session_history(self, file_path: str) -> bool:
        """セッション履歴をファイルから読み込み"""
        try:
            if not os.path.exists(file_path):
                return True
            
            with open(file_path, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
            
            # 履歴データからProgressSessionオブジェクトを復元（実装予定）
            logger.info(f"Loaded {len(history_data)} session records")
            return True
        except Exception as e:
            logger.error(f"Failed to load session history: {e}")
            return False


# 使用例
async def example_usage():
    """使用例"""
    # reporter = ProgressReporter(github_client)
    
    # # セッション開始
    # session_id = reporter.start_session(123, 456, "新機能の実装を開始します")
    
    # # 進捗更新
    # await reporter.update_progress(123, "in_progress", "コード分析中...", {
    #     "step": "analysis",
    #     "progress": 25
    # })
    
    # await reporter.update_progress(123, "retrying", "CI実行中...", {
    #     "attempt": 2,
    #     "max_attempts": 5,
    #     "ci_status": "pending"
    # })
    
    # # セッション完了
    # await reporter.complete_session(123, "completed", "実装が正常に完了しました", {
    #     "pr_url": "https://github.com/repo/pull/123",
    #     "merge_status": "success"
    # })
    pass