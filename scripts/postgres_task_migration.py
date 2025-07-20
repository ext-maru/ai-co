#!/usr/bin/env python3
"""
PostgreSQL タスク移行スクリプト
SQLiteからPostgreSQLへタスクデータを移行
"""

import asyncio
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import asyncpg

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 環境変数を直接読み込み


class PostgreSQLTaskMigration:
    """PostgreSQL タスク移行クラス"""

    def __init__(self):
        # SQLiteデータベースパス
        self.sqlite_db_paths = [
            PROJECT_ROOT / "libs/elder_system/flow/data/task_sage.db",
            PROJECT_ROOT / "db/task_history.db",
        ]

        # PostgreSQL接続情報（環境変数から取得）
        self.pg_config = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", 5432)),
            "database": os.getenv("POSTGRES_DATABASE", "elders_knowledge"),
            "user": os.getenv("POSTGRES_USER", "elders_guild"),
            "password": os.getenv("POSTGRES_PASSWORD", "elders_2025"),
        }

    async def create_task_sage_table(self, conn):
        """PostgreSQLにtask_sageテーブルを作成"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS task_sage (
            id SERIAL PRIMARY KEY,
            task_id VARCHAR(255) UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            status VARCHAR(50) NOT NULL,
            priority VARCHAR(50),
            task_type VARCHAR(50),
            assignee VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            metadata JSONB,
            dependencies JSONB,
            results JSONB,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            tags TEXT[],
            estimated_duration INTEGER,
            actual_duration INTEGER,
            parent_task_id VARCHAR(255),
            is_archived BOOLEAN DEFAULT FALSE
        );

        -- インデックス作成
        CREATE INDEX IF NOT EXISTS idx_task_sage_status ON task_sage(status);
        CREATE INDEX IF NOT EXISTS idx_task_sage_priority ON task_sage(priority);
        CREATE INDEX IF NOT EXISTS idx_task_sage_created_at ON task_sage(created_at);
        CREATE INDEX IF NOT EXISTS idx_task_sage_assignee ON task_sage(assignee);
        CREATE INDEX IF NOT EXISTS idx_task_sage_tags ON task_sage USING GIN(tags);
        CREATE INDEX IF NOT EXISTS idx_task_sage_metadata ON task_sage USING GIN(metadata);
        """

        await conn.execute(create_table_sql)
        print("✅ PostgreSQL task_sageテーブル作成完了")

    def read_sqlite_tasks(self, db_path: Path) -> List[Dict[str, Any]]:
        """SQLiteからタスクデータを読み込み"""
        if not db_path.exists():
            print(f"⚠️ SQLiteデータベースが存在しません: {db_path}")
            return []

        tasks = []
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # テーブル構造を確認
            cursor.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='tasks'"
            )
            table_info = cursor.fetchone()

            if not table_info:
                print(f"⚠️ tasksテーブルが存在しません: {db_path}")
                return []

            print(f"📋 SQLiteテーブル構造: {table_info['sql']}")

            # タスクデータを取得
            cursor.execute("SELECT * FROM tasks")
            rows = cursor.fetchall()

            for row in rows:
                task = dict(row)
                # JSONフィールドをパース
                for field in ["metadata", "dependencies", "results"]:
                    if field in task and task[field]:
                        try:
                            task[field] = json.loads(task[field])
                        except:
                            task[field] = {}

                # tagsフィールドを配列に変換
                if "tags" in task and task["tags"]:
                    if isinstance(task["tags"], str):
                        task["tags"] = (
                            json.loads(task["tags"])
                            if task["tags"].startswith("[")
                            else [task["tags"]]
                        )
                else:
                    task["tags"] = []

                tasks.append(task)

            print(f"✅ {len(tasks)}件のタスクを読み込みました: {db_path}")

        except Exception as e:
            print(f"❌ SQLite読み込みエラー: {e}")
        finally:
            conn.close()

        return tasks

    async def insert_tasks_to_postgres(self, conn, tasks: List[Dict[str, Any]]):
        """PostgreSQLにタスクデータを挿入"""
        if not tasks:
            print("⚠️ 挿入するタスクがありません")
            return

        insert_sql = """
        INSERT INTO task_sage (
            task_id, name, description, status, priority, task_type,
            assignee, created_at, updated_at, completed_at,
            metadata, dependencies, results, error_message,
            retry_count, tags, estimated_duration, actual_duration,
            parent_task_id, is_archived
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
            $11, $12, $13, $14, $15, $16, $17, $18, $19, $20
        )
        ON CONFLICT (task_id) DO UPDATE SET
            name = EXCLUDED.name,
            description = EXCLUDED.description,
            status = EXCLUDED.status,
            priority = EXCLUDED.priority,
            task_type = EXCLUDED.task_type,
            assignee = EXCLUDED.assignee,
            updated_at = EXCLUDED.updated_at,
            completed_at = EXCLUDED.completed_at,
            metadata = EXCLUDED.metadata,
            dependencies = EXCLUDED.dependencies,
            results = EXCLUDED.results,
            error_message = EXCLUDED.error_message,
            retry_count = EXCLUDED.retry_count,
            tags = EXCLUDED.tags,
            estimated_duration = EXCLUDED.estimated_duration,
            actual_duration = EXCLUDED.actual_duration,
            parent_task_id = EXCLUDED.parent_task_id,
            is_archived = EXCLUDED.is_archived
        """

        inserted_count = 0
        for task in tasks:
            try:
                # データ準備
                values = (
                    task.get(
                        "task_id", task.get("id", f"task_{datetime.now().timestamp()}")
                    ),
                    task.get("name", "Unnamed Task"),
                    task.get("description"),
                    task.get("status", "pending"),
                    task.get("priority", "medium"),
                    task.get("task_type", "feature"),
                    task.get("assignee"),
                    task.get("created_at", datetime.now()),
                    task.get("updated_at", datetime.now()),
                    task.get("completed_at"),
                    json.dumps(task.get("metadata", {})),
                    json.dumps(task.get("dependencies", {})),
                    json.dumps(task.get("results", {})),
                    task.get("error_message"),
                    task.get("retry_count", 0),
                    task.get("tags", []),
                    task.get("estimated_duration"),
                    task.get("actual_duration"),
                    task.get("parent_task_id"),
                    task.get("is_archived", False),
                )

                await conn.execute(insert_sql, *values)
                inserted_count += 1

            except Exception as e:
                print(f"❌ タスク挿入エラー: {e}")
                print(f"   タスクID: {task.get('task_id', 'unknown')}")

        print(f"✅ {inserted_count}/{len(tasks)}件のタスクをPostgreSQLに挿入しました")

    async def migrate(self):
        """移行処理のメイン関数"""
        print("🚀 PostgreSQLタスク移行を開始します...")
        print(
            f"📊 PostgreSQL接続情報: {self.pg_config['host']}:{self.pg_config['port']}/{self.pg_config['database']}"
        )

        # PostgreSQL接続
        conn = None
        try:
            conn = await asyncpg.connect(**self.pg_config)
            print("✅ PostgreSQL接続成功")

            # テーブル作成
            await self.create_task_sage_table(conn)

            # 各SQLiteデータベースから移行
            all_tasks = []
            for db_path in self.sqlite_db_paths:
                tasks = self.read_sqlite_tasks(db_path)
                all_tasks.extend(tasks)

            # PostgreSQLに挿入
            await self.insert_tasks_to_postgres(conn, all_tasks)

            # 統計情報表示
            count = await conn.fetchval("SELECT COUNT(*) FROM task_sage")
            print(f"\n📊 移行完了統計:")
            print(f"   総タスク数: {count}")

            # ステータス別統計
            status_stats = await conn.fetch(
                """
                SELECT status, COUNT(*) as count
                FROM task_sage
                GROUP BY status
                ORDER BY count DESC
            """
            )
            print("   ステータス別:")
            for row in status_stats:
                print(f"     - {row['status']}: {row['count']}件")

        except Exception as e:
            print(f"❌ 移行エラー: {e}")
            raise
        finally:
            if conn:
                await conn.close()
                print("✅ PostgreSQL接続を閉じました")


async def main():
    """メイン関数"""
    migration = PostgreSQLTaskMigration()
    await migration.migrate()


if __name__ == "__main__":
    asyncio.run(main())
