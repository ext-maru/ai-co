#!/usr/bin/env python3
"""
🎯 Issue Completion Manager - イシュー完了管理システム
エルダーズギルド自動化システムでのイシュー完了追跡と管理

機能:
- PR作成後のイシュー完了追跡
- 自動クローズ管理
- 完了率統計とレポート
- 失敗イシューの再処理キュー

作成者: クロードエルダー
作成日: 2025-07-19
"""

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IssueStatus(Enum):
    """イシューステータス列挙型"""

    PENDING = "pending"
    PROCESSING = "processing"
    PR_CREATED = "pr_created"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class CompletionResult(Enum):
    """完了結果列挙型"""

    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class IssueRecord:
    """イシュー記録データクラス"""

    issue_number: int
    title: str
    status: IssueStatus
    pr_number: Optional[int]
    pr_url: Optional[str]
    completion_result: Optional[CompletionResult]
    started_at: datetime
    completed_at: Optional[datetime]
    processing_time: Optional[float]
    error_message: Optional[str]
    retry_count: int
    metadata: Dict[str, Any]


class IssueCompletionManager:
    """
    🎯 イシュー完了管理システム

    自動化システムでのイシュー処理完了を追跡し、
    統計情報と再処理管理を提供
    """

    def __init__(self, db_path: str = "/home/aicompany/ai_co/data/issue_completion.db"):
        """イシュー完了管理システムを初期化"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # データベース初期化
        self._init_database()

        # 統計キャッシュ
        self._stats_cache = {}
        self._cache_timestamp = None

        logger.info("🎯 Issue Completion Manager 初期化完了")

    def _init_database(self):
        """データベースを初期化"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # イシュー記録テーブル
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS issue_records (
                        issue_number INTEGER PRIMARY KEY,
                        title TEXT NOT NULL,
                        status TEXT NOT NULL,
                        pr_number INTEGER,
                        pr_url TEXT,
                        completion_result TEXT,
                        started_at TIMESTAMP NOT NULL,
                        completed_at TIMESTAMP,
                        processing_time REAL,
                        error_message TEXT,
                        retry_count INTEGER DEFAULT 0,
                        metadata TEXT DEFAULT '{}'
                    )
                """
                )

                # 処理履歴テーブル
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS processing_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        issue_number INTEGER NOT NULL,
                        action TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        details TEXT,
                        success BOOLEAN DEFAULT TRUE
                    )
                """
                )

                # 統計サマリーテーブル
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS daily_statistics (
                        date TEXT PRIMARY KEY,
                        total_issues INTEGER DEFAULT 0,
                        completed_issues INTEGER DEFAULT 0,
                        failed_issues INTEGER DEFAULT 0,
                        avg_processing_time REAL DEFAULT 0.0,
                        success_rate REAL DEFAULT 0.0,
                        metadata TEXT DEFAULT '{}'
                    )
                """
                )

                # インデックス作成
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_status ON issue_records(status)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_started_at ON issue_records(started_at)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_completion_result ON " \
                        "issue_records(completion_result)"
                )

                conn.commit()
                logger.info("📊 Issue Completion データベース初期化完了")

        except Exception as e:
            logger.error(f"❌ データベース初期化エラー: {e}")
            raise

    def start_issue_processing(
        self, issue_number: int, title: str, metadata: Dict[str, Any] = None
    ) -> bool:
        """イシュー処理開始を記録"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 既存記録確認
                cursor.execute(
                    "SELECT issue_number FROM issue_records WHERE issue_number = ?",
                    (issue_number,),
                )
                existing = cursor.fetchone()

                if existing:
                    # 既存記録を更新（再処理の場合）
                    cursor.execute(
                        """
                        UPDATE issue_records
                        SET status = ?, started_at = CURRENT_TIMESTAMP, retry_count = retry_count + 1,
                            error_message = NULL, metadata = ?
                        WHERE issue_number = ?
                    """,
                        (
                            IssueStatus.PROCESSING.value,
                            json.dumps(metadata or {}),
                            issue_number,
                        ),
                    )

                    # 履歴記録
                    self._record_action(
                        cursor,
                        issue_number,
                        "restart_processing",
                        f"Re-processing issue #{issue_number}",
                    )
                else:
                    # 新規記録作成
                    cursor.execute(
                        """
                        INSERT INTO issue_records
                        (issue_number, title, status, started_at, metadata)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
                    """,
                        (
                            issue_number,
                            title,
                            IssueStatus.PROCESSING.value,
                            json.dumps(metadata or {}),
                        ),
                    )

                    # 履歴記録
                    self._record_action(
                        cursor,
                        issue_number,
                        "start_processing",
                        f"Started processing issue #{issue_number}: {title}",
                    )

                conn.commit()
                logger.info(f"📋 イシュー処理開始記録: #{issue_number}")
                return True

        except Exception as e:
            logger.error(f"❌ イシュー処理開始記録エラー: {e}")
            return False

    def record_pr_creation(
        self, issue_number: int, pr_number: int, pr_url: str
    ) -> bool:
        """PR作成を記録"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE issue_records
                    SET status = ?, pr_number = ?, pr_url = ?
                    WHERE issue_number = ?
                """,
                    (IssueStatus.PR_CREATED.value, pr_number, pr_url, issue_number),
                )

                # 履歴記録
                self._record_action(
                    cursor,
                    issue_number,
                    "pr_created",
                    f"PR #{pr_number} created for issue #{issue_number}",
                )

                conn.commit()
                logger.info(f"🚀 PR作成記録: Issue #{issue_number} -> PR #{pr_number}")
                return True

        except Exception as e:
            logger.error(f"❌ PR作成記録エラー: {e}")
            return False

    def complete_issue(
        self,
        issue_number: int,
        completion_result: CompletionResult,
        error_message: str = None,
    ) -> bool:
        """イシュー完了を記録"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 開始時刻を取得して処理時間を計算
                cursor.execute(
                    "SELECT started_at FROM issue_records WHERE issue_number = ?",
                    (issue_number,),
                )
                result = cursor.fetchone()

                if result:
                    started_at = datetime.fromisoformat(result[0])
                    processing_time = (datetime.now() - started_at).total_seconds()
                else:
                    processing_time = None

                # ステータスを決定
                if completion_result == CompletionResult.SUCCESS:
                    status = IssueStatus.COMPLETED
                elif completion_result in [
                    CompletionResult.FAILED,
                    CompletionResult.TIMEOUT,
                ]:
                    status = IssueStatus.FAILED
                else:
                    status = IssueStatus.COMPLETED  # partial_success, cancelled

                cursor.execute(
                    """
                    UPDATE issue_records
                    SET status = ?, completion_result = ?, completed_at = CURRENT_TIMESTAMP,
                        processing_time = ?, error_message = ?
                    WHERE issue_number = ?
                """,
                    (
                        status.value,
                        completion_result.value,
                        processing_time,
                        error_message,
                        issue_number,
                    ),
                )

                # 履歴記録
                action_detail = f"Completed with result: {completion_result.value}"
                if error_message:
                    action_detail += f" (Error: {error_message})"

                self._record_action(
                    cursor,
                    issue_number,
                    "complete",
                    action_detail,
                    success=(completion_result == CompletionResult.SUCCESS),
                )

                conn.commit()
                logger.info(f"✅ イシュー完了記録: #{issue_number} ({completion_result.value})")

                # 統計キャッシュを無効化
                self._invalidate_stats_cache()

                return True

        except Exception as e:
            logger.error(f"❌ イシュー完了記録エラー: {e}")
            return False

    def get_issue_record(self, issue_number: int) -> Optional[IssueRecord]:
        """イシュー記録を取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT issue_number, title, status, pr_number, pr_url, completion_result,
                           started_at, completed_at, processing_time, error_message, retry_count, metadata
                    FROM issue_records WHERE issue_number = ?
                """,
                    (issue_number,),
                )

                row = cursor.fetchone()
                if not row:
                    return None

                return IssueRecord(
                    issue_number=row[0],
                    title=row[1],
                    status=IssueStatus(row[2]),
                    pr_number=row[3],
                    pr_url=row[4],
                    completion_result=CompletionResult(row[5]) if row[5] else None,
                    started_at=datetime.fromisoformat(row[6]),
                    completed_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    processing_time=row[8],
                    error_message=row[9],
                    retry_count=row[10],
                    metadata=json.loads(row[11] or "{}"),
                )

        except Exception as e:
            logger.error(f"❌ イシュー記録取得エラー: {e}")
            return None

    def get_pending_issues(self) -> List[IssueRecord]:
        """処理待ちイシューを取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT issue_number, title, status, pr_number, pr_url, completion_result,
                           started_at, completed_at, processing_time, error_message, retry_count, metadata
                    FROM issue_records
                    WHERE status IN (?, ?)
                    ORDER BY started_at DESC
                """,
                    (IssueStatus.PENDING.value, IssueStatus.PROCESSING.value),
                )

                return [
                    IssueRecord(
                        issue_number=row[0],
                        title=row[1],
                        status=IssueStatus(row[2]),
                        pr_number=row[3],
                        pr_url=row[4],
                        completion_result=CompletionResult(row[5]) if row[5] else None,
                        started_at=datetime.fromisoformat(row[6]),
                        completed_at=datetime.fromisoformat(row[7]) if row[7] else None,
                        processing_time=row[8],
                        error_message=row[9],
                        retry_count=row[10],
                        metadata=json.loads(row[11] or "{}"),
                    )
                    for row in cursor.fetchall()
                ]

        except Exception as e:
            logger.error(f"❌ 処理待ちイシュー取得エラー: {e}")
            return []

    def get_failed_issues(self, max_retries: int = 3) -> List[IssueRecord]:
        """失敗イシューを取得（再処理対象）"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT issue_number, title, status, pr_number, pr_url, completion_result,
                           started_at, completed_at, processing_time, error_message, retry_count, metadata
                    FROM issue_records
                    WHERE status = ? AND retry_count < ?
                    ORDER BY started_at DESC
                """,
                    (IssueStatus.FAILED.value, max_retries),
                )

                return [
                    IssueRecord(
                        issue_number=row[0],
                        title=row[1],
                        status=IssueStatus(row[2]),
                        pr_number=row[3],
                        pr_url=row[4],
                        completion_result=CompletionResult(row[5]) if row[5] else None,
                        started_at=datetime.fromisoformat(row[6]),
                        completed_at=datetime.fromisoformat(row[7]) if row[7] else None,
                        processing_time=row[8],
                        error_message=row[9],
                        retry_count=row[10],
                        metadata=json.loads(row[11] or "{}"),
                    )
                    for row in cursor.fetchall()
                ]

        except Exception as e:
            logger.error(f"❌ 失敗イシュー取得エラー: {e}")
            return []

    def get_completion_statistics(self, days: int = 7) -> Dict[str, Any]:
        """完了統計を取得"""
        # キャッシュ確認
        if self._cache_timestamp and datetime.now() - self._cache_timestamp < timedelta(
            minutes=10
        ):
            cached_stats = self._stats_cache.get(f"stats_{days}")
            if cached_stats:
                return cached_stats

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 期間指定
                since_date = datetime.now() - timedelta(days=days)

                # 総合統計
                cursor.execute(
                    """
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                        SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) as processing,
                        AVG(processing_time) as avg_time,
                        MAX(processing_time) as max_time,
                        MIN(processing_time) as min_time
                    FROM issue_records
                    WHERE started_at >= ?
                """,
                    (since_date.isoformat(),),
                )

                stats = cursor.fetchone()

                # PR統計
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM issue_records
                    WHERE pr_number IS NOT NULL AND started_at >= ?
                """,
                    (since_date.isoformat(),),
                )

                pr_count = cursor.fetchone()[0]

                # エラー統計
                cursor.execute(
                    """
                    SELECT error_message, COUNT(*) as count
                    FROM issue_records
                    WHERE error_message IS NOT NULL AND started_at >= ?
                    GROUP BY error_message
                    ORDER BY count DESC
                    LIMIT 10
                """,
                    (since_date.isoformat(),),
                )

                error_stats = dict(cursor.fetchall())

                # 日別統計
                cursor.execute(
                    """
                    SELECT
                        DATE(started_at) as date,
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
                    FROM issue_records
                    WHERE started_at >= ?
                    GROUP BY DATE(started_at)
                    ORDER BY date DESC
                """,
                    (since_date.isoformat(),),
                )

                daily_stats = [
                    {"date": row[0], "total": row[1], "completed": row[2]}
                    for row in cursor.fetchall()
                ]

                # 統計をまとめ
                total = stats[0] or 0
                completed = stats[1] or 0
                failed = stats[2] or 0
                processing = stats[3] or 0

                result = {
                    "period_days": days,
                    "total_issues": total,
                    "completed_issues": completed,
                    "failed_issues": failed,
                    "processing_issues": processing,
                    "pr_created_count": pr_count,
                    "success_rate": (completed / total * 100) if total > 0 else 0,
                    "completion_rate": ((completed + failed) / total * 100)
                    if total > 0
                    else 0,
                    "avg_processing_time": stats[4] or 0,
                    "max_processing_time": stats[5] or 0,
                    "min_processing_time": stats[6] or 0,
                    "error_summary": error_stats,
                    "daily_statistics": daily_stats,
                    "generated_at": datetime.now().isoformat(),
                }

                # キャッシュに保存
                self._stats_cache[f"stats_{days}"] = result
                self._cache_timestamp = datetime.now()

                return result

        except Exception as e:
            logger.error(f"❌ 完了統計取得エラー: {e}")
            return {}

    def generate_completion_report(self, days: int = 7) -> str:
        """完了レポートを生成"""
        try:
            stats = self.get_completion_statistics(days)

            if not stats:
                return "統計データの取得に失敗しました。"

            report = f"""
# 🎯 イシュー完了レポート（過去{days}日間）

## 📊 総合統計
- **総イシュー数**: {stats['total_issues']}件
- **完了イシュー数**: {stats['completed_issues']}件
- **失敗イシュー数**: {stats['failed_issues']}件
- **処理中イシュー数**: {stats['processing_issues']}件
- **PR作成数**: {stats['pr_created_count']}件

## 📈 成功率
- **成功率**: {stats['success_rate']:.1f}%
- **完了率**: {stats['completion_rate']:.1f}%

## ⏱️ 処理時間
- **平均処理時間**: {stats['avg_processing_time']:.2f}秒
- **最大処理時間**: {stats['max_processing_time']:.2f}秒
- **最小処理時間**: {stats['min_processing_time']:.2f}秒

## 🚨 エラー分析
"""

            if stats["error_summary"]:
                for error, count in list(stats["error_summary"].items())[:5]:
                    report += f"- **{error}**: {count}件\n"
            else:
                report += "- エラーなし\n"

            report += f"""
## 📅 日別統計
"""

            for day_stat in stats["daily_statistics"][:7]:
                success_rate = (
                    (day_stat["completed"] / day_stat["total"] * 100)
                    if day_stat["total"] > 0
                    else 0
                )
                report += f"- **{day_stat['date']}**: {day_stat['total']}件処理, " \
                    "{day_stat['completed']}件完了 ({success_rate:.1f}%)\n"

            report += f"""
---
📅 生成日時: {stats['generated_at']}
🤖 Generated by Claude Elder Issue Completion Manager
"""

            return report

        except Exception as e:
            logger.error(f"❌ 完了レポート生成エラー: {e}")
            return f"レポート生成エラー: {e}"

    def _record_action(
        self, cursor, issue_number: int, action: str, details: str, success: bool = True
    ):
        """アクション履歴を記録"""
        try:
            cursor.execute(
                """
                INSERT INTO processing_history (issue_number, action, details, success)
                VALUES (?, ?, ?, ?)
            """,
                (issue_number, action, details, success),
            )
        except Exception as e:
            logger.warning(f"履歴記録エラー: {e}")

    def _invalidate_stats_cache(self):
        """統計キャッシュを無効化"""
        self._stats_cache.clear()
        self._cache_timestamp = None

    def cleanup_old_records(self, days: int = 30) -> int:
        """古い記録をクリーンアップ"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 完了した古い記録を削除
                cursor.execute(
                    """
                    DELETE FROM issue_records
                    WHERE status = 'completed' AND completed_at < ?
                """,
                    (cutoff_date.isoformat(),),
                )

                deleted_issues = cursor.rowcount

                # 古い履歴を削除
                cursor.execute(
                    """
                    DELETE FROM processing_history
                    WHERE timestamp < ?
                """,
                    (cutoff_date.isoformat(),),
                )

                deleted_history = cursor.rowcount

                conn.commit()

                logger.info(
                    f"🧹 古い記録クリーンアップ完了: {deleted_issues}イシュー, {deleted_history}履歴"
                )
                return deleted_issues

        except Exception as e:
            logger.error(f"❌ クリーンアップエラー: {e}")
            return 0


# 使用例とテスト関数
def main():
    """メイン実行関数"""
    logger.info("🎯 Issue Completion Manager テスト開始")

    manager = IssueCompletionManager()

    # テストデータ作成
    test_issues = [
        {"number": 100, "title": "Test Issue 1"},
        {"number": 101, "title": "Test Issue 2"},
        {"number": 102, "title": "Test Issue 3"},
    ]

    for issue in test_issues:
        # 処理開始
        manager.start_issue_processing(issue["number"], issue["title"])

        # PR作成記録
        manager.record_pr_creation(
            issue["number"],
            issue["number"] + 1000,
            f"https://github.com/test/repo/pull/{issue['number'] + 1000}",
        )

        # 完了記録
        result = (
            CompletionResult.SUCCESS
            if issue["number"] % 2 == 0
            else CompletionResult.FAILED
        )
        error_msg = "Test error" if result == CompletionResult.FAILED else None
        manager.complete_issue(issue["number"], result, error_msg)

    # 統計表示
    stats = manager.get_completion_statistics(7)
    logger.info(f"📊 統計: {stats}")

    # レポート生成
    report = manager.generate_completion_report(7)
    logger.info(f"📋 レポート:\n{report}")

    logger.info("🏁 Issue Completion Manager テスト完了")


if __name__ == "__main__":
    main()
