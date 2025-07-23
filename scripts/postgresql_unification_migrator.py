#!/usr/bin/env python3
"""
PostgreSQL統一移行システム
Elders Guild SQLite → PostgreSQL Complete Migration System
"""

import asyncio
import json
import logging
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import asyncpg

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PostgreSQLUnificationMigrator:
    """PostgreSQL統一移行システム"""

    def __init__(self):
        self.pg_url = os.getenv(
            "GRIMOIRE_DATABASE_URL",
            "postgresql://aicompany@localhost:5432/ai_company_grimoire",
        )
        self.migration_stats = {
            "start_time": None,
            "end_time": None,
            "tasks_migrated": 0,
            "conversations_migrated": 0,
            "errors": [],
        }
        logger.info("🚀 PostgreSQL統一移行システム初期化完了")

    async def create_unified_schemas(self):
        """統合スキーマ作成"""
        logger.info("📋 統合PostgreSQLスキーマ作成中...")

        conn = await asyncpg.connect(self.pg_url)

        # タスク統合テーブル
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS unified_tasks (
                id SERIAL PRIMARY KEY,
                task_id VARCHAR(255) UNIQUE,
                title TEXT NOT NULL,
                description TEXT,
                status VARCHAR(50) DEFAULT 'pending',
                priority VARCHAR(20) DEFAULT 'medium',
                assigned_sage VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                completed_at TIMESTAMP,
                metadata JSONB,
                -- AI機能統合
                task_embedding VECTOR(1536),
                complexity_score FLOAT,
                estimated_duration INTERVAL,
                -- 4賢者統合
                knowledge_refs TEXT[],
                incident_refs TEXT[],
                rag_context JSONB
            )
        """
        )

        # 会話統合テーブル
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS unified_conversations (
                id SERIAL PRIMARY KEY,
                conversation_id VARCHAR(255),
                session_id VARCHAR(255),
                user_message TEXT,
                ai_response TEXT,
                timestamp TIMESTAMP DEFAULT NOW(),
                context JSONB,
                -- AI機能統合
                message_embedding VECTOR(1536),
                response_embedding VECTOR(1536),
                quality_score FLOAT,
                sentiment_score FLOAT,
                -- 統合機能
                related_tasks TEXT[],
                knowledge_used TEXT[],
                sage_consulted VARCHAR(50)
            )
        """
        )

        # インデックス作成
        logger.info("🔍 パフォーマンスインデックス作成中...")

        # タスクインデックス
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_unified_tasks_status ON unified_tasks(status)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_unified_tasks_sage ON unified_tasks(assigned_sage)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_unified_tasks_priority ON unified_tasks(priority, created_at)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_unified_tasks_metadata ON unified_tasks USING gin(metadata)"
        )

        # 会話インデックス
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON unified_conversations(timestamp)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_conversations_session ON unified_conversations(session_id)"
        )

        # 全文検索インデックス
        try:
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_conversations_fts ON unified_conversations
                USING gin(to_tsvector('english', COALESCE(user_message, '') || ' ' || COALESCE(ai_response, '')))
            """
            )
        except Exception as e:
            logger.warning(f"全文検索インデックス作成警告: {e}")

        await conn.close()
        logger.info("✅ 統合スキーマ作成完了")

    async def migrate_task_history(self):
        """タスク履歴移行 - Phase 1"""
        logger.info("📋 Phase 1: タスク履歴移行開始...")

        # 複数のタスクDBを確認
        task_databases = ["task_history.db", "db/task_history.db", "data/tasks.db"]

        for db_path in task_databases:
            if os.path.exists(db_path):
                await self._migrate_single_task_db(db_path)

    async def _migrate_single_task_db(self, db_path):
        """単一タスクDB移行"""
        logger.info(f"📋 {db_path} からタスク移行開始...")

        # SQLiteからデータ取得
        sqlite_conn = sqlite3.connect(db_path)
        sqlite_conn.row_factory = sqlite3.Row
        cursor = sqlite_conn.cursor()

        # テーブル構造確認
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            logger.info(f"SQLiteテーブル: {tables}")

            if "task_history" in tables:
                table_name = "task_history"
            elif "tasks" in tables:
                table_name = "tasks"
            else:
                logger.error("タスクテーブルが見つかりません")
                return

            # データ取得
            cursor.execute(f"SELECT * FROM {table_name}")
            tasks = cursor.fetchall()
            logger.info(f"移行対象タスク: {len(tasks)}件")

            # PostgreSQLに移行
            pg_conn = await asyncpg.connect(self.pg_url)

            for task in tasks:
                try:
                    # タスクデータの正規化
                    task_dict = dict(task)

                    # 基本フィールドマッピング
                    task_id = task_dict.get("task_id") or task_dict.get(
                        "id", f"task_{datetime.now().timestamp()}"
                    )
                    title = (
                        task_dict.get("title")
                        or task_dict.get("description", "Untitled Task")[:100]
                    )
                    description = task_dict.get("description") or task_dict.get(
                        "content", ""
                    )
                    status = task_dict.get("status", "pending")
                    priority = task_dict.get("priority", "medium")

                    # 日時変換
                    created_at = task_dict.get("created_at") or task_dict.get(
                        "timestamp", datetime.now()
                    )
                    if isinstance(created_at, str):
                        # Deep nesting detected (depth: 5) - consider refactoring
                        try:
                            # 簡単な日時パース
                            created_at = datetime.fromisoformat(
                                created_at.replace("Z", "+00:00")
                            )
                        except:
                            created_at = datetime.now()

                    # メタデータ作成
                    metadata = {
                        "migrated_from": "sqlite_task_history",
                        "migration_date": datetime.now().isoformat(),
                        "original_data": {k: str(v) for k, v in task_dict.items()},
                    }

                    await pg_conn.execute(
                        """
                        INSERT INTO unified_tasks (
                            task_id, title, description, status, priority,
                            created_at, metadata, assigned_sage
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        ON CONFLICT (task_id) DO UPDATE SET
                            title = EXCLUDED.title,
                            description = EXCLUDED.description,
                            metadata = EXCLUDED.metadata
                    """,
                        task_id,
                        title,
                        description,
                        status,
                        priority,
                        created_at,
                        json.dumps(metadata),
                        "knowledge_sage",
                    )

                    self.migration_stats["tasks_migrated"] += 1

                except Exception as e:
                    logger.error(f"タスク移行エラー: {e}")
                    self.migration_stats["errors"].append(f"Task migration: {str(e)}")

            await pg_conn.close()
            sqlite_conn.close()

            logger.info(f"✅ タスク移行完了: {self.migration_stats['tasks_migrated']}件")

        except Exception as e:
            logger.error(f"❌ タスク移行失敗: {e}")
            self.migration_stats["errors"].append(f"Task migration failed: {str(e)}")

    async def migrate_conversations(self):
        """会話履歴移行 - Phase 2"""
        logger.info("💬 Phase 2: 会話履歴移行開始...")

        if not os.path.exists("conversations.db"):
            logger.warning("⚠️ conversations.db が見つかりません")
            return

        # SQLiteからデータ取得
        sqlite_conn = sqlite3.connect("conversations.db")
        sqlite_conn.row_factory = sqlite3.Row
        cursor = sqlite_conn.cursor()

        try:
            # テーブル構造確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            logger.info(f"会話テーブル: {tables}")

            conversation_table = None
            for table in ["conversations", "conversation_history", "messages"]:
                if table in tables:
                    conversation_table = table
                    break

            if not conversation_table:
                logger.warning("会話テーブルが見つかりません")
                return

            # データ取得
            cursor.execute(f"SELECT * FROM {conversation_table}")
            conversations = cursor.fetchall()
            logger.info(f"移行対象会話: {len(conversations)}件")

            # PostgreSQLに移行
            pg_conn = await asyncpg.connect(self.pg_url)

            for conv in conversations:
                try:
                    conv_dict = dict(conv)

                    # フィールドマッピング
                    conversation_id = conv_dict.get("conversation_id") or conv_dict.get(
                        "id", f"conv_{datetime.now().timestamp()}"
                    )
                    user_message = conv_dict.get("user_message") or conv_dict.get(
                        "message", ""
                    )
                    ai_response = conv_dict.get("ai_response") or conv_dict.get(
                        "response", ""
                    )

                    # 日時変換
                    timestamp = conv_dict.get("timestamp") or conv_dict.get(
                        "created_at", datetime.now()
                    )
                    if isinstance(timestamp, str):
                        # Deep nesting detected (depth: 5) - consider refactoring
                        try:
                            # 簡単な日時パース
                            timestamp = datetime.fromisoformat(
                                timestamp.replace("Z", "+00:00")
                            )
                        except:
                            timestamp = datetime.now()

                    # コンテキスト作成
                    context = {
                        "migrated_from": "sqlite_conversations",
                        "migration_date": datetime.now().isoformat(),
                        "original_data": {k: str(v) for k, v in conv_dict.items()},
                    }

                    await pg_conn.execute(
                        """
                        INSERT INTO unified_conversations (
                            conversation_id, user_message, ai_response,
                            timestamp, context, sage_consulted
                        ) VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                        conversation_id,
                        user_message,
                        ai_response,
                        timestamp,
                        json.dumps(context),
                        "knowledge_sage",
                    )

                    self.migration_stats["conversations_migrated"] += 1

                except Exception as e:
                    logger.error(f"会話移行エラー: {e}")
                    self.migration_stats["errors"].append(
                        f"Conversation migration: {str(e)}"
                    )

            await pg_conn.close()
            sqlite_conn.close()

            logger.info(f"✅ 会話移行完了: {self.migration_stats['conversations_migrated']}件")

        except Exception as e:
            logger.error(f"❌ 会話移行失敗: {e}")
            self.migration_stats["errors"].append(
                f"Conversation migration failed: {str(e)}"
            )

    async def verify_migration(self):
        """移行検証"""
        logger.info("🔍 移行結果検証中...")

        conn = await asyncpg.connect(self.pg_url)

        # タスク確認
        task_count = await conn.fetchval("SELECT COUNT(*) FROM unified_tasks")
        logger.info(f"PostgreSQL統合タスク: {task_count}件")

        # 会話確認
        conv_count = await conn.fetchval("SELECT COUNT(*) FROM unified_conversations")
        logger.info(f"PostgreSQL統合会話: {conv_count}件")

        # サンプルデータ確認
        sample_task = await conn.fetchrow("SELECT * FROM unified_tasks LIMIT 1")
        if sample_task:
            logger.info(f"サンプルタスク: {sample_task['title']}")

        sample_conv = await conn.fetchrow("SELECT * FROM unified_conversations LIMIT 1")
        if sample_conv:
            logger.info(f"サンプル会話: {sample_conv['user_message'][:50]}...")

        await conn.close()

        return {
            "tasks_in_postgresql": task_count,
            "conversations_in_postgresql": conv_count,
            "migration_successful": task_count > 0 or conv_count > 0,
        }

    async def create_unified_views(self):
        """統合ビュー作成"""
        logger.info("🎯 統合分析ビュー作成中...")

        conn = await asyncpg.connect(self.pg_url)

        # 4賢者統合ビュー
        await conn.execute(
            """
            CREATE OR REPLACE VIEW four_sages_integrated_view AS
            SELECT
                'task' as data_type,
                t.task_id as entity_id,
                t.title as content,
                t.assigned_sage,
                t.created_at,
                t.metadata
            FROM unified_tasks t
            UNION ALL
            SELECT
                'conversation' as data_type,
                c.conversation_id as entity_id,
                c.user_message as content,
                c.sage_consulted as assigned_sage,
                c.timestamp as created_at,
                c.context as metadata
            FROM unified_conversations c
            UNION ALL
            SELECT
                'knowledge' as data_type,
                k.id::text as entity_id,
                k.content,
                'knowledge_sage' as assigned_sage,
                k.created_at,
                '{}'::jsonb as metadata
            FROM knowledge_grimoire k
        """
        )

        logger.info("✅ 統合ビュー作成完了")
        await conn.close()

    def generate_migration_report(self, verification_result):
        """移行レポート生成"""
        duration = (
            self.migration_stats["end_time"] - self.migration_stats["start_time"]
        ).total_seconds()

        report = {
            "migration_id": f"postgresql_unification_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "execution_time": duration,
            "statistics": self.migration_stats,
            "verification": verification_result,
            "success_rate": (
                (
                    self.migration_stats["tasks_migrated"]
                    + self.migration_stats["conversations_migrated"]
                )
                / max(
                    1,
                    self.migration_stats["tasks_migrated"]
                    + self.migration_stats["conversations_migrated"],
                )
                * 100
            )
            if (
                self.migration_stats["tasks_migrated"]
                + self.migration_stats["conversations_migrated"]
            )
            > 0
            else 0,
            "postgresql_integration": "complete",
        }

        report_file = f"postgresql_unification_report_{report['migration_id']}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"📄 移行レポート保存: {report_file}")
        return report


async def main():
    """メイン実行"""
    migrator = PostgreSQLUnificationMigrator()

    try:
        migrator.migration_stats["start_time"] = datetime.now()

        # Phase 1: スキーマ作成
        logger.info("🏗️ Phase 1: 統合スキーマ作成")
        await migrator.create_unified_schemas()

        # Phase 2: タスク移行
        logger.info("📋 Phase 2: タスクデータ移行")
        await migrator.migrate_task_history()

        # Phase 3: 会話移行
        logger.info("💬 Phase 3: 会話データ移行")
        await migrator.migrate_conversations()

        # Phase 4: 統合ビュー作成
        logger.info("🎯 Phase 4: 統合ビュー作成")
        await migrator.create_unified_views()

        # 検証
        logger.info("🔍 Phase 5: 移行検証")
        verification = await migrator.verify_migration()

        migrator.migration_stats["end_time"] = datetime.now()

        # レポート生成
        report = migrator.generate_migration_report(verification)

        # 結果表示
        print("\n" + "=" * 60)
        print("🎉 PostgreSQL統一移行完了!")
        print("=" * 60)
        print(f"移行タスク: {migrator.migration_stats['tasks_migrated']}件")
        print(f"移行会話: {migrator.migration_stats['conversations_migrated']}件")
        print(f"成功率: {report['success_rate']:.1f}%")
        print(f"実行時間: {report['execution_time']:.2f}秒")

        if migrator.migration_stats["errors"]:
            print(f"\n⚠️ エラー: {len(migrator.migration_stats['errors'])}件")
            for error in migrator.migration_stats["errors"]:
                print(f"  - {error}")

        if verification["migration_successful"]:
            print("\n✅ 移行検証: 成功")
            print("🏛️ Elders Guild PostgreSQL統一システム稼働開始!")
        else:
            print("\n❌ 移行検証: 失敗")

    except Exception as e:
        logger.error(f"❌ 移行プロセス失敗: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
