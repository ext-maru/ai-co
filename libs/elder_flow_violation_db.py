"""
Elder Flow違反データベース接続ユーティリティ
"""
import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
import logging

from libs.elder_flow_violation_detector import ViolationRecord
from libs.elder_flow_violation_types import (
    ViolationType, ViolationSeverity, ViolationCategory
)


logger = logging.getLogger(__name__)


class ElderFlowViolationDB:
    """Elder Flow違反データベース管理クラス"""

    def __init__(self, db_path: Optional[Path] = None):
        """初期化"""
        self.db_path = db_path or Path("data/elder_flow_violations.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    @contextmanager
    def get_connection(self):
        """データベース接続のコンテキストマネージャ"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_database(self):
        """データベースを初期化"""
        schema_path = Path(__file__).parent.parent / "database/schema/elder_flow_violations_sqlite.sql"

        with self.get_connection() as conn:
            if schema_path.exists():
                with open(schema_path, 'r') as f:
                    conn.executescript(f.read())
            else:
                # スキーマファイルがない場合は最小限のテーブルを作成
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS elder_flow_violations (
                        id TEXT PRIMARY KEY,
                        violation_type TEXT NOT NULL,
                        category TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        description TEXT NOT NULL,
                        context_command TEXT,
                        context_file_path TEXT,
                        context_timestamp DATETIME NOT NULL,
                        context_additional_info TEXT DEFAULT '{}',
                        detected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        resolved_at DATETIME,
                        resolution_notes TEXT,
                        auto_fixed INTEGER DEFAULT 0,
                        auto_fixable INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            conn.commit()

    def save_violation(self, violation: ViolationRecord) -> str:
        """違反を保存"""
        violation_id = str(uuid.uuid4())

        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO elder_flow_violations (
                    id, violation_type, category, severity, description,
                    context_command, context_file_path, context_timestamp,
                    context_additional_info, detected_at, resolved_at,
                    resolution_notes, auto_fixed, auto_fixable
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                violation_id,
                violation.violation_type.value,
                violation.category.value,
                violation.severity.value,
                violation.description,
                violation.context.command,
                violation.context.file_path,
                violation.context.timestamp,
                json.dumps(violation.context.additional_info),
                violation.detected_at,
                violation.resolved_at,
                violation.resolution_notes,
                1 if violation.auto_fixed else 0,
                1 if violation.auto_fixable else 0
            ))
            conn.commit()

        logger.info(f"違反を保存しました: {violation_id}")
        return violation_id

    def get_violation(self, violation_id: str) -> Optional[Dict[str, Any]]:
        """IDで違反を取得"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM elder_flow_violations WHERE id = ?",
                (violation_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_active_violations(self) -> List[Dict[str, Any]]:
        """アクティブな違反を取得"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM elder_flow_violations
                WHERE resolved_at IS NULL
                ORDER BY detected_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def resolve_violation(self, violation_id: str, resolution_notes: str) -> bool:
        """違反を解決済みにする"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE elder_flow_violations
                SET resolved_at = ?, resolution_notes = ?, updated_at = ?
                WHERE id = ?
            """, (datetime.now(), resolution_notes, datetime.now(), violation_id))
            conn.commit()
            return conn.total_changes > 0

    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        with self.get_connection() as conn:
            # 基本統計
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total_violations,
                    COUNT(CASE WHEN resolved_at IS NULL THEN 1 END) as active_violations,
                    COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_violations,
                    COUNT(CASE WHEN severity = 'high' THEN 1 END) as high_violations,
                    COUNT(CASE WHEN severity = 'medium' THEN 1 END) as medium_violations,
                    COUNT(CASE WHEN severity = 'low' THEN 1 END) as low_violations,
                    COUNT(CASE WHEN auto_fixed = 1 THEN 1 END) as auto_fixed_violations
                FROM elder_flow_violations
            """)
            row = cursor.fetchone()
            stats = dict(row) if row else {}

            # カテゴリ別統計
            cursor = conn.execute("""
                SELECT
                    category,
                    COUNT(*) as violation_count,
                    COUNT(CASE WHEN resolved_at IS NULL THEN 1 END) as active_count
                FROM elder_flow_violations
                GROUP BY category
                ORDER BY violation_count DESC
            """)
            stats['by_category'] = [dict(row) for row in cursor.fetchall()]

            # 違反タイプ別統計
            cursor = conn.execute("""
                SELECT violation_type, COUNT(*) as count
                FROM elder_flow_violations
                GROUP BY violation_type
                ORDER BY count DESC
            """)
            stats['by_type'] = [dict(row) for row in cursor.fetchall()]

            return stats

    def search_violations(
        self,
        violation_type: Optional[str] = None,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        resolved: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """条件に基づいて違反を検索"""
        query = "SELECT * FROM elder_flow_violations WHERE 1=1"
        params = []

        if violation_type:
            query += " AND violation_type = ?"
            params.append(violation_type)

        if category:
            query += " AND category = ?"
            params.append(category)

        if severity:
            query += " AND severity = ?"
            params.append(severity)

        if start_date:
            query += " AND detected_at >= ?"
            params.append(start_date)

        if end_date:
            query += " AND detected_at <= ?"
            params.append(end_date)

        if resolved is not None:
            if resolved:
                query += " AND resolved_at IS NOT NULL"
            else:
                query += " AND resolved_at IS NULL"

        query += " ORDER BY detected_at DESC"

        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def add_fix_suggestion(self, violation_id: str, suggestion: str) -> str:
        """修正提案を追加"""
        suggestion_id = str(uuid.uuid4())

        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO violation_fix_suggestions
                (id, violation_id, suggestion_text)
                VALUES (?, ?, ?)
            """, (suggestion_id, violation_id, suggestion))
            conn.commit()

        return suggestion_id

    def get_recent_violations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """最近の違反を取得"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT
                    id,
                    violation_type,
                    category,
                    severity,
                    description,
                    context_command,
                    detected_at,
                    resolved_at,
                    auto_fixable
                FROM elder_flow_violations
                ORDER BY detected_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
