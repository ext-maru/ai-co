#!/usr/bin/env python3
"""
Unified Tracking DB - 統合トラッキングデータベース（軽量版）
Created: 2025-01-20
Author: Claude Elder

Elder Flow実行記録を管理する軽量データベース
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class UnifiedTrackingDB:
    """統合トラッキングデータベース"""

    def __init__(self, db_path:
        """初期化メソッド"""
    Optional[str] = None):
        if db_path is None:
            # デフォルトパス
            self.db_path = Path.home() / ".elder_flow" / "tracking.db"
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            self.db_path = Path(db_path)

        self._init_db()

    def _init_db(self):
        """データベース初期化"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 実行記録テーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS execution_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flow_type TEXT NOT NULL,
                flow_id TEXT UNIQUE NOT NULL,
                task_name TEXT NOT NULL,
                priority TEXT,
                status TEXT NOT NULL,
                results TEXT,
                error TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # インデックス作成
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_flow_id ON execution_records(flow_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_status ON execution_records(status)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_created_at ON execution_records(created_at)"
        )

        conn.commit()
        conn.close()

    async def save_execution_record(self, record: Dict[str, Any]) -> bool:
        """実行記録を保存"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO execution_records
                (flow_type, flow_id, task_name, priority, status, results, error, start_time, end_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    record.get("flow_type", "elder_flow"),
                    record["flow_id"],
                    record["task_name"],
                    record.get("priority", "medium"),
                    record["status"],
                    json.dumps(record.get("results", {})),
                    record.get("error"),
                    record["start_time"],
                    record.get("end_time"),
                ),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error saving execution record: {e}")
            return False

    async def get_execution_record(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """実行記録を取得"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT flow_type, flow_id, task_name, priority, status, results, error,
                       start_time, end_time, created_at
                FROM execution_records
                WHERE flow_id = ?
            """,
                (flow_id,),
            )

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    "flow_type": row[0],
                    "flow_id": row[1],
                    "task_name": row[2],
                    "priority": row[3],
                    "status": row[4],
                    "results": json.loads(row[5]) if row[5] else {},
                    "error": row[6],
                    "start_time": row[7],
                    "end_time": row[8],
                    "created_at": row[9],
                }

            return None

        except Exception as e:
            print(f"Error getting execution record: {e}")
            return None

    async def get_recent_executions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """最近の実行記録を取得"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT flow_type, flow_id, task_name, priority, status, results, error,
                       start_time, end_time, created_at
                FROM execution_records
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (limit,),
            )

            rows = cursor.fetchall()
            conn.close()

            records = []
            for row in rows:
                records.append(
                    {
                        "flow_type": row[0],
                        "flow_id": row[1],
                        "task_name": row[2],
                        "priority": row[3],
                        "status": row[4],
                        "results": json.loads(row[5]) if row[5] else {},
                        "error": row[6],
                        "start_time": row[7],
                        "end_time": row[8],
                        "created_at": row[9],
                    }
                )

            return records

        except Exception as e:
            print(f"Error getting recent executions: {e}")
            return []

    async def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # 総実行数
            cursor.execute("SELECT COUNT(*) FROM execution_records")
            total_count = cursor.fetchone()[0]

            # ステータス別カウント
            cursor.execute(
                """
                SELECT status, COUNT(*)
                FROM execution_records
                GROUP BY status
            """
            )
            status_counts = dict(cursor.fetchall())

            # 優先度別カウント
            cursor.execute(
                """
                SELECT priority, COUNT(*)
                FROM execution_records
                GROUP BY priority
            """
            )
            priority_counts = dict(cursor.fetchall())

            conn.close()

            return {
                "total_executions": total_count,
                "status_counts": status_counts,
                "priority_counts": priority_counts,
                "success_rate": (status_counts.get("COMPLETED", 0) / total_count * 100)
                if total_count > 0
                else 0,
            }

        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {
                "total_executions": 0,
                "status_counts": {},
                "priority_counts": {},
                "success_rate": 0,
            }

    async def cleanup_old_records(self, days: int = 30) -> int:
        """古い記録をクリーンアップ"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM execution_records
                WHERE created_at < datetime('now', '-' || ? || ' days')
            """,
                (days,),
            )

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            return deleted_count

        except Exception as e:
            print(f"Error cleaning up old records: {e}")
            return 0


# 軽量版インスタンス
_tracking_db = None


def get_tracking_db() -> UnifiedTrackingDB:
    """トラッキングDBのシングルトンインスタンス取得"""
    global _tracking_db
    if _tracking_db is None:
        _tracking_db = UnifiedTrackingDB()
    return _tracking_db
