#!/usr/bin/env python3
"""
A2A通信データのpgvectorへの移行スクリプト
既存のJSONデータをPostgreSQLに移行し、OpenAI APIでベクトル化
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import psycopg2
from psycopg2.extras import execute_batch

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# OpenAI import
try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI library not available. Install with: pip install openai")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class A2APgVectorMigration:
    """A2Aデータのpgvector移行クラス"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._load_default_config()
        self.connection = None
        self.cursor = None
        self.openai_client = None

        # 統計情報
        self.stats = {
            "total_communications": 0,
            "migrated_communications": 0,
            "total_anomalies": 0,
            "migrated_anomalies": 0,
            "embeddings_generated": 0,
            "errors": [],
        }

        # バッチサイズ
        self.batch_size = 100
        self.embedding_batch_size = 20

    def _load_default_config(self) -> Dict[str, Any]:
        """デフォルト設定の読み込み"""
        return {
            "database": {
                "host": os.getenv("PGHOST", "localhost"),
                "port": int(os.getenv("PGPORT", 5432)),
                "database": os.getenv("PGDATABASE", "ai_company_db"),
                "user": os.getenv("PGUSER", "aicompany"),
                "password": os.getenv("PGPASSWORD", ""),
            },
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "model": "text-embedding-3-small",
                "dimension": 1536,
            },
            "data_sources": {
                "communications": str(
                    PROJECT_ROOT / "analysis_results" / "a2a_communications_*.json"
                ),
                "anomalies": str(
                    PROJECT_ROOT / "analysis_results" / "anomaly_patterns_*.json"
                ),
                "semantic_analysis": str(
                    PROJECT_ROOT / "analysis_results" / "semantic_analysis_*.json"
                ),
            },
        }

    def connect_database(self):
        """データベース接続"""
        try:
            self.connection = psycopg2.connect(**self.config["database"])
            self.cursor = self.connection.cursor()
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def setup_openai(self):
        """OpenAI APIのセットアップ"""
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI library not available")
            return False

        api_key = self.config["openai"]["api_key"]
        if not api_key:
            logger.warning("OpenAI API key not configured")
            return False

        try:
            self.openai_client = openai.OpenAI(api_key=api_key)
            # テスト埋め込み生成
            test_response = self.openai_client.embeddings.create(
                model=self.config["openai"]["model"],
                input="test",
                dimensions=self.config["openai"]["dimension"],
            )
            logger.info("OpenAI API configured successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to setup OpenAI API: {e}")
            return False

    def load_json_data(self, pattern: str) -> List[Dict[str, Any]]:
        """JSONファイルからデータを読み込み"""
        data = []
        files = list(Path(pattern).parent.glob(Path(pattern).name))

        for file_path in files:
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        file_data = json.load(f)
                        if isinstance(file_data, list):
                            data.extend(file_data)
                        elif isinstance(file_data, dict):
                            # 辞書の場合は値を抽出
                            for key, value in file_data.items():
                                if isinstance(value, dict):
                                    value["_key"] = key
                                    data.append(value)
                                elif isinstance(value, list):
                                    data.extend(value)
                except Exception as e:
                    logger.error(f"Failed to load {file_path}: {e}")
                    self.stats["errors"].append(f"Load error: {file_path}")

        logger.info(f"Loaded {len(data)} records from {len(files)} files")
        return data

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """テキストからベクトル埋め込みを生成"""
        if not self.openai_client:
            return None

        try:
            response = self.openai_client.embeddings.create(
                model=self.config["openai"]["model"],
                input=text,
                dimensions=self.config["openai"]["dimension"],
            )
            embedding = response.data[0].embedding
            self.stats["embeddings_generated"] += 1
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            self.stats["errors"].append(f"Embedding error: {str(e)[:100]}")
            return None

    def generate_embeddings_batch(
        self, texts: List[str]
    ) -> List[Optional[List[float]]]:
        """バッチでベクトル埋め込みを生成"""
        if not self.openai_client:
            return [None] * len(texts)

        embeddings = []

        # バッチ処理
        for i in range(0, len(texts), self.embedding_batch_size):
            batch = texts[i : i + self.embedding_batch_size]

            try:
                response = self.openai_client.embeddings.create(
                    model=self.config["openai"]["model"],
                    input=batch,
                    dimensions=self.config["openai"]["dimension"],
                )

                batch_embeddings = [data.embedding for data in response.data]
                embeddings.extend(batch_embeddings)
                self.stats["embeddings_generated"] += len(batch_embeddings)

                # レート制限対策
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Failed to generate batch embeddings: {e}")
                self.stats["errors"].append(f"Batch embedding error: {str(e)[:100]}")
                embeddings.extend([None] * len(batch))

        return embeddings

    def migrate_communications(self):
        """A2A通信データの移行"""
        logger.info("Migrating A2A communications...")

        # データ読み込み
        pattern = self.config["data_sources"]["communications"]
        communications = self.load_json_data(pattern)
        self.stats["total_communications"] = len(communications)

        if not communications:
            logger.warning("No communications data found")
            return

        # エージェント情報の抽出と登録
        agents = set()
        for comm in communications:
            if "sender" in comm:
                agents.add(comm["sender"])
            if "receiver" in comm:
                agents.add(comm["receiver"])

        self._migrate_agents(list(agents))

        # バッチ処理で通信データを移行
        for i in range(0, len(communications), self.batch_size):
            batch = communications[i : i + self.batch_size]

            # テキスト準備（埋め込み用）
            texts = []
            for comm in batch:
                text_parts = []
                if "sender" in comm:
                    text_parts.append(f"Sender: {comm['sender']}")
                if "receiver" in comm:
                    text_parts.append(f"Receiver: {comm['receiver']}")
                if "type" in comm:
                    text_parts.append(f"Type: {comm['type']}")
                if "content" in comm:
                    content = comm["content"]
                    if isinstance(content, dict):
                        content = json.dumps(content)
                    text_parts.append(f"Content: {content}")

                texts.append(" | ".join(text_parts))

            # 埋め込み生成
            embeddings = self.generate_embeddings_batch(texts)

            # データベースへの挿入
            insert_data = []
            for j, comm in enumerate(batch):
                try:
                    # タイムスタンプ処理
                    timestamp = comm.get("timestamp", datetime.now())
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(
                            timestamp.replace("Z", "+00:00")
                        )

                    # メタデータ準備
                    metadata = {}
                    for key in ["priority", "status", "error", "retry_count"]:
                        if key in comm:
                            metadata[key] = comm[key]

                    # コンテンツ処理
                    content = comm.get("content", "")
                    if isinstance(content, dict):
                        content = json.dumps(content)

                    insert_data.append(
                        (
                            timestamp,
                            comm.get("sender", "unknown"),
                            comm.get("receiver", "unknown"),
                            comm.get("type", "unknown"),
                            str(content),
                            json.dumps(metadata) if metadata else None,
                            embeddings[j] if embeddings[j] else None,
                        )
                    )

                except Exception as e:
                    logger.error(f"Failed to process communication: {e}")
                    self.stats["errors"].append(
                        f"Communication processing error: {str(e)[:100]}"
                    )

            # バッチ挿入
            if insert_data:
                try:
                    execute_batch(
                        self.cursor,
                        """
                        INSERT INTO a2a.communications
                        (timestamp, sender, receiver, message_type, content, metadata, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        insert_data,
                        page_size=100,
                    )
                    self.connection.commit()
                    self.stats["migrated_communications"] += len(insert_data)
                    logger.info(
                        f"Migrated {len(insert_data)} communications (total: {self.stats['migrated_communications']})"
                    )

                except Exception as e:
                    logger.error(f"Failed to insert communications batch: {e}")
                    self.connection.rollback()
                    self.stats["errors"].append(f"Insert error: {str(e)[:100]}")

    def _migrate_agents(self, agents: List[str]):
        """エージェント情報の移行"""
        logger.info(f"Migrating {len(agents)} agents...")

        insert_data = []
        for agent in agents:
            # エージェントタイプの推定
            agent_type = "worker"
            if "system" in agent.lower():
                agent_type = "system"
            elif "elder" in agent.lower():
                agent_type = "elder"
            elif "sage" in agent.lower():
                agent_type = "sage"

            insert_data.append(
                (
                    agent,
                    agent_type,
                    "active",
                    json.dumps({"auto_detected": True}),
                    json.dumps({"message_count": 0}),
                )
            )

        try:
            execute_batch(
                self.cursor,
                """
                INSERT INTO a2a.agents (agent_name, agent_type, status, capabilities, performance_metrics)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (agent_name) DO NOTHING
                """,
                insert_data,
                page_size=100,
            )
            self.connection.commit()
            logger.info(f"Migrated {len(insert_data)} agents")

        except Exception as e:
            logger.error(f"Failed to migrate agents: {e}")
            self.connection.rollback()

    def migrate_anomaly_patterns(self):
        """異常パターンデータの移行"""
        logger.info("Migrating anomaly patterns...")

        # データ読み込み
        pattern = self.config["data_sources"]["anomalies"]
        anomalies = self.load_json_data(pattern)
        self.stats["total_anomalies"] = len(anomalies)

        if not anomalies:
            logger.warning("No anomaly patterns found")
            return

        # 重複排除（パターン名でグループ化）
        unique_patterns = {}
        for anomaly in anomalies:
            pattern_name = anomaly.get("pattern", anomaly.get("type", "unknown"))
            if pattern_name not in unique_patterns:
                unique_patterns[pattern_name] = anomaly
            else:
                # 既存のパターンの発生回数を更新
                if "count" in anomaly:
                    unique_patterns[pattern_name]["count"] = (
                        unique_patterns[pattern_name].get("count", 0) + anomaly["count"]
                    )

        # バッチ処理で移行
        patterns_list = list(unique_patterns.values())

        # テキスト準備（埋め込み用）
        texts = []
        for pattern in patterns_list:
            text_parts = []
            text_parts.append(
                f"Pattern: {pattern.get('pattern', pattern.get('type', 'unknown'))}"
            )
            if "description" in pattern:
                text_parts.append(f"Description: {pattern['description']}")
            if "severity" in pattern:
                text_parts.append(f"Severity: {pattern['severity']}")

            texts.append(" | ".join(text_parts))

        # 埋め込み生成
        embeddings = self.generate_embeddings_batch(texts)

        # データベースへの挿入
        insert_data = []
        for i, pattern in enumerate(patterns_list):
            try:
                pattern_name = pattern.get("pattern", pattern.get("type", "unknown"))

                # 検出ルールの構築
                detection_rules = {}
                for key in ["agents", "keywords", "threshold", "time_window"]:
                    if key in pattern:
                        detection_rules[key] = pattern[key]

                # 最終検出時刻
                last_detected = pattern.get("last_detected", pattern.get("timestamp"))
                if isinstance(last_detected, str):
                    last_detected = datetime.fromisoformat(
                        last_detected.replace("Z", "+00:00")
                    )
                elif not isinstance(last_detected, datetime):
                    last_detected = None

                insert_data.append(
                    (
                        pattern_name,
                        pattern.get("category", "general"),
                        pattern.get("severity", "medium"),
                        pattern.get("description", ""),
                        json.dumps(detection_rules) if detection_rules else None,
                        embeddings[i] if embeddings[i] else None,
                        pattern.get("count", 1),
                        last_detected,
                    )
                )

            except Exception as e:
                logger.error(f"Failed to process anomaly pattern: {e}")
                self.stats["errors"].append(f"Anomaly processing error: {str(e)[:100]}")

        # バッチ挿入
        if insert_data:
            try:
                execute_batch(
                    self.cursor,
                    """
                    INSERT INTO a2a.anomaly_patterns
                    (pattern_name, pattern_type, severity, description, detection_rules,
                     embedding, occurrence_count, last_detected)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    insert_data,
                    page_size=100,
                )
                self.connection.commit()
                self.stats["migrated_anomalies"] = len(insert_data)
                logger.info(f"Migrated {len(insert_data)} anomaly patterns")

            except Exception as e:
                logger.error(f"Failed to insert anomaly patterns: {e}")
                self.connection.rollback()
                self.stats["errors"].append(f"Anomaly insert error: {str(e)[:100]}")

    def create_sample_queries(self):
        """サンプルクエリの作成"""
        sample_queries = [
            {
                "name": "Find similar communications",
                "description": "特定の通信に類似した通信を検索",
                "query": """
                    -- 最新の通信から類似検索
                    WITH latest_comm AS (
                        SELECT embedding
                        FROM a2a.communications
                        WHERE embedding IS NOT NULL
                        ORDER BY timestamp DESC
                        LIMIT 1
                    )
                    SELECT * FROM a2a.find_similar_communications(
                        (SELECT embedding FROM latest_comm),
                        10
                    );
                """,
            },
            {
                "name": "Anomaly pattern search",
                "description": "特定の異常パターンに類似したパターンを検索",
                "query": """
                    -- 重要度の高い異常パターンの類似検索
                    SELECT
                        a1.pattern_name,
                        a1.severity,
                        a1.occurrence_count,
                        1 - (a1.embedding <=> a2.embedding) as similarity
                    FROM a2a.anomaly_patterns a1
                    CROSS JOIN a2a.anomaly_patterns a2
                    WHERE a2.pattern_name = 'system-overload'
                      AND a1.pattern_name != a2.pattern_name
                      AND a1.embedding IS NOT NULL
                      AND a2.embedding IS NOT NULL
                    ORDER BY similarity DESC
                    LIMIT 5;
                """,
            },
            {
                "name": "Agent communication patterns",
                "description": "エージェント間の通信パターン分析",
                "query": """
                    -- エージェント別通信統計
                    SELECT
                        sender,
                        receiver,
                        message_type,
                        COUNT(*) as message_count,
                        MAX(timestamp) as last_communication
                    FROM a2a.communications
                    GROUP BY sender, receiver, message_type
                    ORDER BY message_count DESC
                    LIMIT 20;
                """,
            },
        ]

        # クエリをファイルに保存
        query_file = PROJECT_ROOT / "scripts" / "pgvector_sample_queries.sql"
        with open(query_file, "w", encoding="utf-8") as f:
            f.write("-- pgvector Sample Queries for A2A Communication Analysis\n")
            f.write(f"-- Generated: {datetime.now().isoformat()}\n\n")

            for query in sample_queries:
                f.write(f"-- {query['name']}\n")
                f.write(f"-- {query['description']}\n")
                f.write(query["query"])
                f.write("\n\n")

        logger.info(f"Sample queries saved to: {query_file}")

    def generate_migration_report(self) -> Dict[str, Any]:
        """移行レポートの生成"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "statistics": self.stats,
            "database_status": {},
            "recommendations": [],
        }

        # データベース統計
        try:
            # 通信数
            self.cursor.execute("SELECT COUNT(*) FROM a2a.communications;")
            report["database_status"]["total_communications"] = self.cursor.fetchone()[
                0
            ]

            # 埋め込みありの通信数
            self.cursor.execute(
                "SELECT COUNT(*) FROM a2a.communications WHERE embedding IS NOT NULL;"
            )
            report["database_status"][
                "communications_with_embeddings"
            ] = self.cursor.fetchone()[0]

            # 異常パターン数
            self.cursor.execute("SELECT COUNT(*) FROM a2a.anomaly_patterns;")
            report["database_status"][
                "total_anomaly_patterns"
            ] = self.cursor.fetchone()[0]

            # エージェント数
            self.cursor.execute("SELECT COUNT(*) FROM a2a.agents;")
            report["database_status"]["total_agents"] = self.cursor.fetchone()[0]

        except Exception as e:
            logger.error(f"Failed to get database statistics: {e}")

        # 推奨事項
        if report["database_status"].get("communications_with_embeddings", 0) == 0:
            report["recommendations"].append(
                "OpenAI API設定を確認してベクトル埋め込みを生成してください"
            )

        if self.stats["errors"]:
            report["recommendations"].append(
                f"{len(self.stats['errors'])}個のエラーが発生しました。ログを確認してください"
            )

        if self.stats["migrated_communications"] < self.stats["total_communications"]:
            report["recommendations"].append(
                "一部の通信データが移行されていません。データ形式を確認してください"
            )

        return report

    def close(self):
        """接続のクローズ"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def execute_migration(self) -> Dict[str, Any]:
        """完全な移行の実行"""
        logger.info("Starting A2A to pgvector migration...")

        try:
            # 1. データベース接続
            self.connect_database()

            # 2. OpenAI設定
            openai_ready = self.setup_openai()
            if not openai_ready:
                logger.warning("Proceeding without OpenAI embeddings")

            # 3. 通信データの移行
            self.migrate_communications()

            # 4. 異常パターンの移行
            self.migrate_anomaly_patterns()

            # 5. サンプルクエリの作成
            self.create_sample_queries()

            # 6. レポート生成
            report = self.generate_migration_report()

            logger.info("Migration completed successfully!")

            return report

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise

        finally:
            self.close()


def main():
    """メイン処理"""
    print("🚀 A2A to pgvector Migration")
    print("=" * 60)

    # OpenAI API キーの確認
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set")
        print("   Embeddings will not be generated")
        response = input("   Continue without embeddings? (y/N): ")
        if response.lower() != "y":
            print("Migration cancelled")
            return

    try:
        migration = A2APgVectorMigration()
        report = migration.execute_migration()

        # レポート保存
        report_file = (
            PROJECT_ROOT
            / "logs"
            / f"pgvector_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n💾 Migration report saved to: {report_file}")

        # 結果表示
        print("\n📊 Migration Summary")
        print("-" * 40)
        print(
            f"Communications migrated: {report['statistics']['migrated_communications']}/{report['statistics']['total_communications']}"
        )
        print(
            f"Anomaly patterns migrated: {report['statistics']['migrated_anomalies']}/{report['statistics']['total_anomalies']}"
        )
        print(f"Embeddings generated: {report['statistics']['embeddings_generated']}")
        print(f"Errors: {len(report['statistics']['errors'])}")

        if report.get("recommendations"):
            print("\n💡 Recommendations")
            print("-" * 40)
            for rec in report["recommendations"]:
                print(f"- {rec}")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
