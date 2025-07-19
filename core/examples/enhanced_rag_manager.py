#!/usr/bin/env python3
"""
Enhanced RAG Manager - 基底クラスを使用した改良版

BaseManagerを継承したRAGManagerの実装例。
"""

import sqlite3

# core基盤の使用
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.append(str(Path(__file__).parent.parent.parent))
from core import EMOJI, BaseManager, get_config


class EnhancedRAGManager(BaseManager):
    """改良版RAGManager - 基底クラスを活用"""

    def __init__(self):
        # 基底クラスの初期化
        super().__init__("EnhancedRAGManager")

        # 設定の読み込み
        self.config = get_config()

        # DB設定
        self.db_path = self.paths["db"] / "task_history.db"
        self.connection: Optional[sqlite3.Connection] = None

        # 統計情報
        self.cache_hits = 0
        self.cache_misses = 0

    def initialize(self) -> bool:
        """
        初期化処理（BaseManagerの抽象メソッド）
        """
        try:
            # DBディレクトリ確保
            if not self.ensure_directory(self.db_path.parent):
                return False

            # DB接続
            self.connection = sqlite3.connect(
                str(self.db_path), check_same_thread=False
            )
            self.connection.row_factory = sqlite3.Row

            # テーブル作成
            self._create_tables()

            self.logger.info(
                f"{EMOJI['database']} Database initialized: {self.db_path}"
            )

            return True

        except Exception as e:
            self.handle_error(e, "initialize", critical=True)
            return False

    def _create_tables(self):
        """テーブル作成"""
        cursor = self.connection.cursor()

        # タスク履歴テーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS task_history (
                task_id TEXT PRIMARY KEY,
                worker TEXT NOT NULL,
                model TEXT,
                prompt TEXT NOT NULL,
                response TEXT,
                summary TEXT,
                status TEXT DEFAULT 'pending',
                task_type TEXT DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # インデックス作成
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_task_type
            ON task_history(task_type)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_created_at
            ON task_history(created_at)
        """
        )

        self.connection.commit()

    def save_task(self, task_data: Dict[str, Any]) -> bool:
        """
        タスク保存

        Args:
            task_data: タスクデータ

        Returns:
            成功かどうか
        """
        required_fields = ["task_id", "worker", "prompt"]

        if not self.validate_config(task_data, required_fields):
            return False

        try:
            cursor = self.connection.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO task_history
                (task_id, worker, model, prompt, response,
                 summary, status, task_type, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    task_data["task_id"],
                    task_data["worker"],
                    task_data.get("model", self.config.worker.default_model),
                    task_data["prompt"],
                    task_data.get("response", ""),
                    task_data.get("summary", ""),
                    task_data.get("status", "completed"),
                    task_data.get("task_type", "general"),
                    datetime.now().isoformat(),
                ),
            )

            self.connection.commit()
            self._increment_stats("save_task")

            self.logger.debug(f"{EMOJI['success']} Task saved: {task_data['task_id']}")

            return True

        except Exception as e:
            self.handle_error(e, "save_task")
            return False

    def search_similar_tasks(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        類似タスク検索

        Args:
            query: 検索クエリ
            limit: 最大件数

        Returns:
            類似タスクのリスト
        """
        try:
            cursor = self.connection.cursor()

            # 単純なキーワード検索（実際はベクトル検索等が望ましい）
            cursor.execute(
                """
                SELECT task_id, prompt, response, summary,
                       created_at, task_type
                FROM task_history
                WHERE prompt LIKE ? OR summary LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (f"%{query}%", f"%{query}%", limit),
            )

            results = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "task_id": row["task_id"],
                        "prompt": row["prompt"],
                        "response": row["response"],
                        "summary": row["summary"],
                        "created_at": row["created_at"],
                        "task_type": row["task_type"],
                    }
                )

            if results:
                self.cache_hits += 1
                self.logger.info(
                    f"{EMOJI['success']} Found {len(results)} similar tasks"
                )
            else:
                self.cache_misses += 1
                self.logger.debug("No similar tasks found")

            self._increment_stats("search_similar_tasks")

            return results

        except Exception as e:
            self.handle_error(e, "search_similar_tasks")
            return []

    def get_recent_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        最近のタスク取得

        Args:
            limit: 最大件数

        Returns:
            タスクリスト
        """
        try:
            cursor = self.connection.cursor()

            cursor.execute(
                """
                SELECT task_id, worker, prompt, status,
                       task_type, created_at
                FROM task_history
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (limit,),
            )

            results = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "task_id": row["task_id"],
                        "worker": row["worker"],
                        "prompt": row["prompt"][:100] + "..."
                        if len(row["prompt"]) > 100
                        else row["prompt"],
                        "status": row["status"],
                        "task_type": row["task_type"],
                        "created_at": row["created_at"],
                    }
                )

            self._increment_stats("get_recent_tasks")

            return results

        except Exception as e:
            self.handle_error(e, "get_recent_tasks")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """
        統計情報取得

        Returns:
            統計情報
        """
        try:
            cursor = self.connection.cursor()

            # 総タスク数
            cursor.execute("SELECT COUNT(*) as count FROM task_history")
            total_tasks = cursor.fetchone()["count"]

            # タイプ別タスク数
            cursor.execute(
                """
                SELECT task_type, COUNT(*) as count
                FROM task_history
                GROUP BY task_type
            """
            )

            type_counts = {}
            for row in cursor.fetchall():
                type_counts[row["task_type"]] = row["count"]

            # ステータス別タスク数
            cursor.execute(
                """
                SELECT status, COUNT(*) as count
                FROM task_history
                GROUP BY status
            """
            )

            status_counts = {}
            for row in cursor.fetchall():
                status_counts[row["status"]] = row["count"]

            # キャッシュヒット率
            total_searches = self.cache_hits + self.cache_misses
            hit_rate = self.cache_hits / total_searches if total_searches > 0 else 0

            stats = {
                "total_tasks": total_tasks,
                "type_counts": type_counts,
                "status_counts": status_counts,
                "cache_hit_rate": hit_rate,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                **self.get_stats(),  # 基底クラスの統計も含める
            }

            self._increment_stats("get_statistics")

            return stats

        except Exception as e:
            self.handle_error(e, "get_statistics")
            return {}

    def cleanup(self) -> None:
        """
        クリーンアップ処理
        """
        if self.connection:
            self.connection.close()
            self.logger.info(f"{EMOJI['success']} Database connection closed")

        super().cleanup()  # 基底クラスのクリーンアップも実行

    def health_check(self) -> Dict[str, Any]:
        """
        ヘルスチェック（拡張版）
        """
        base_health = super().health_check()

        # DB接続チェック
        db_healthy = False
        try:
            if self.connection:
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
                db_healthy = True
        except:
            pass

        # 統計情報追加
        stats = self.get_statistics()

        return {
            **base_health,
            "database_healthy": db_healthy,
            "total_tasks": stats.get("total_tasks", 0),
            "cache_hit_rate": stats.get("cache_hit_rate", 0),
        }


def main():
    """使用例"""
    # コンテキストマネージャーとして使用
    with EnhancedRAGManager() as rag:
        # タスク保存
        rag.save_task(
            {
                "task_id": "test_001",
                "worker": "test_worker",
                "prompt": "Create a Python hello world program",
                "response": 'print("Hello, World!")',
                "status": "completed",
            }
        )

        # 類似タスク検索
        similar = rag.search_similar_tasks("Python hello")
        print(f"Similar tasks: {len(similar)}")

        # 統計情報
        stats = rag.get_statistics()
        print(f"Statistics: {stats}")

        # ヘルスチェック
        health = rag.health_check()
        print(f"Health: {health}")


if __name__ == "__main__":
    main()
