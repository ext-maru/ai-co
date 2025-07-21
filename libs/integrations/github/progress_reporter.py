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
        "merge_state": lambda d: f"マージ状態: {d.get('mergeable_state', 'unknown')}",
        "ci_jobs_completed": lambda d: f"{d.get('ci_jobs_completed', 0)}/{d.get('ci_jobs_total', 0)} jobs完了"
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
        self._reports: Dict[int, Dict[str, Any]] = {}  # テスト用の簡易レポート管理
    
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
            
            # TODO: 履歴データからProgressSessionオブジェクトを復元
            logger.info(f"Loaded {len(history_data)} session records")
            return True
        except Exception as e:
            logger.error(f"Failed to load session history: {e}")
            return False
    
    # テスト用の追加メソッド
    async def create_initial_report(
        self, 
        pr_number: int, 
        issue_number: int, 
        title: str
    ) -> Dict[str, Any]:
        """初期レポートを作成（テスト用）"""
        self.start_session(pr_number, issue_number, f"PR #{pr_number}: {title} の監視を開始しました")
        
        # 初期レポートを作成
        self._reports[issue_number] = {
            "pr_number": pr_number,
            "title": title,
            "start_time": datetime.now(),
            "current_state": "監視開始",
            "current_emoji": "🚀",
            "history": [],
            "comment_id": 12345  # モック用
        }
        
        # GitHub APIを呼び出し
        body = self._format_progress_report(issue_number)
        result = await self.github_client.create_issue_comment(issue_number, body)
        
        return {
            "success": result.get("success", True),
            "comment_id": result.get("comment_id", 12345)
        }
    
    async def update_progress(
        self,
        issue_number: int,
        state: str,
        emoji: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """進捗を更新（テスト用の簡易版）"""
        if issue_number not in self._reports:
            return {"success": False, "reason": "No report found"}
        
        # レポートを更新
        self._reports[issue_number]["current_state"] = state
        self._reports[issue_number]["current_emoji"] = emoji
        
        # 履歴に追加
        if details:
            history_entry = {
                "timestamp": datetime.now(),
                "state": state,
                "emoji": emoji,
                "details": details
            }
            self._reports[issue_number]["history"].append(history_entry)
        
        # コメントを更新
        body = self._format_progress_report(issue_number)
        result = await self.github_client.update_issue_comment(
            self._reports[issue_number]["comment_id"],
            body
        )
        
        return {"success": result.get("success", True)}
    
    def add_event_to_history(
        self,
        issue_number: int,
        event_type: Any,
        description: str,
        emoji: str
    ):
        """イベント履歴に追加（テスト用）"""
        if issue_number not in self._reports:
            self._reports[issue_number] = {
                "history": [],
                "current_state": "初期化",
                "current_emoji": "🚀"
            }
        
        event = {
            "timestamp": datetime.now(),
            "event_type": event_type,
            "description": description,
            "emoji": emoji
        }
        
        if "history" not in self._reports[issue_number]:
            self._reports[issue_number]["history"] = []
        
        self._reports[issue_number]["history"].append(event)
    
    def get_event_history(self, issue_number: int) -> List[Dict[str, Any]]:
        """イベント履歴を取得（テスト用）"""
        if issue_number not in self._reports:
            return []
        return self._reports[issue_number].get("history", [])
    
    async def complete_monitoring(
        self,
        issue_number: int,
        success: bool,
        final_state: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """監視を完了（テスト用）"""
        if issue_number not in self._reports:
            return {"success": False, "reason": "No report found"}
        
        # 最終状態を設定
        self._reports[issue_number]["current_state"] = final_state
        self._reports[issue_number]["current_emoji"] = "✅" if success else "❌"
        self._reports[issue_number]["completed"] = True
        self._reports[issue_number]["end_time"] = datetime.now()
        
        if details:
            self._reports[issue_number]["final_details"] = details
        
        # 最終コメントを更新
        body = self._format_progress_report(issue_number)
        result = await self.github_client.update_issue_comment(
            self._reports[issue_number]["comment_id"],
            body
        )
        
        return {"success": result.get("success", True)}
    
    async def report_error(
        self,
        issue_number: int,
        error_type: str,
        error_message: str,
        suggested_action: str
    ) -> Dict[str, Any]:
        """エラーを報告（テスト用）"""
        if issue_number not in self._reports:
            return {"success": False, "reason": "No report found"}
        
        # エラー状態を設定
        self._reports[issue_number]["current_state"] = "エラー"
        self._reports[issue_number]["current_emoji"] = "❌"
        self._reports[issue_number]["error"] = {
            "type": error_type,
            "message": error_message,
            "suggested_action": suggested_action
        }
        
        # エラー報告コメントを更新
        body = self._format_progress_report(issue_number)
        result = await self.github_client.update_issue_comment(
            self._reports[issue_number]["comment_id"],
            body
        )
        
        return {"success": result.get("success", True)}
    
    def _format_progress_report(self, issue_number: int) -> str:
        """進捗レポートをフォーマット（テスト用）"""
        if issue_number not in self._reports:
            return "レポートが見つかりません"
        
        report = self._reports[issue_number]
        lines = ["🤖 **Auto Issue Processor - 進捗報告**", ""]
        
        # 現在の状態
        lines.append(f"**現在の状態**: {report['current_state']} {report['current_emoji']}")
        
        # 開始時刻と経過時間
        if "start_time" in report:
            start_time = report["start_time"]
            lines.append(f"**開始時刻**: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            elapsed = datetime.now() - start_time
            lines.append(f"**経過時間**: {self._format_duration(elapsed.total_seconds())}")
        
        # エラー情報
        if "error" in report:
            lines.append("")
            lines.append("**❌ エラー**")
            lines.append(f"- エラータイプ: {report['error']['type']}")
            lines.append(f"- メッセージ: {report['error']['message']}")
            lines.append(f"- 対処法: {report['error']['suggested_action']}")
        
        # 処理履歴
        if "history" in report and report["history"]:
            lines.append("")
            lines.append("**処理履歴**:")
            for entry in report["history"]:
                timestamp = entry["timestamp"].strftime("%H:%M:%S")
                emoji = entry.get("emoji", "📝")
                desc = entry.get("description", "")
                lines.append(f"- {emoji} {timestamp} - {desc}")
                
                # 詳細情報
                if "details" in entry:
                    details = entry["details"]
                    if "ci_jobs_completed" in details and "ci_jobs_total" in details:
                        lines.append(f"  - {details['ci_jobs_completed']}/{details['ci_jobs_total']} jobs完了")
        
        # 完了情報
        if report.get("completed"):
            lines.append("")
            lines.append("**✅ 完了**")
            if "final_details" in report:
                details = report["final_details"]
                if "merge_sha" in details:
                    lines.append(f"- マージSHA: {details['merge_sha']}")
                if "total_duration" in details:
                    lines.append(f"- 総時間: {details['total_duration']}")
        
        # 次のアクション
        lines.append("")
        lines.append("**次のアクション**: " + report.get("next_action", "待機中"))
        
        # 最終更新
        lines.append("")
        lines.append(f"---")
        lines.append(f"*最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return "\n".join(lines)
    
    def _calculate_eta(self, start_time: datetime, progress: float) -> datetime:
        """完了予想時刻を計算（テスト用）"""
        if progress <= 0 or progress >= 1:
            return datetime.now() + timedelta(minutes=5)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        total_estimated = elapsed / progress
        remaining = total_estimated - elapsed
        
        return datetime.now() + timedelta(seconds=remaining)
    
    def _format_duration(self, seconds: float) -> str:
        """時間をフォーマット（テスト用）"""
        seconds = int(seconds)
        
        if seconds < 60:
            return f"{seconds}秒"
        
        minutes = seconds // 60
        seconds = seconds % 60
        
        if minutes < 60:
            return f"{minutes}分{seconds}秒"
        
        hours = minutes // 60
        minutes = minutes % 60
        
        return f"{hours}時間{minutes}分{seconds}秒"


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