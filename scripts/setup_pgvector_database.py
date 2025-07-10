#!/usr/bin/env python3
"""
pgvectorデータベースセットアップスクリプト
PostgreSQLにpgvector拡張をインストールし、A2A通信データ用のスキーマを作成
"""

import os
import sys
import json
import psycopg2
from psycopg2 import sql
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PgVectorDatabaseSetup:
    """pgvectorデータベースセットアップクラス"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._load_default_config()
        self.connection = None
        self.cursor = None
        
    def _load_default_config(self) -> Dict[str, Any]:
        """デフォルト設定の読み込み"""
        return {
            "database": {
                "host": os.getenv("PGHOST", "localhost"),
                "port": int(os.getenv("PGPORT", 5432)),
                "database": os.getenv("PGDATABASE", "ai_company_db"),
                "user": os.getenv("PGUSER", "aicompany"),
                "password": os.getenv("PGPASSWORD", "")
            },
            "pgvector": {
                "vector_dimension": 1536,  # OpenAI text-embedding-3-small
                "index_method": "hnsw",
                "index_params": {
                    "m": 16,
                    "ef_construction": 64
                }
            },
            "tables": {
                "a2a_communications": {
                    "schema": "a2a",
                    "enable_partitioning": True,
                    "partition_by": "timestamp"
                },
                "anomaly_patterns": {
                    "schema": "a2a",
                    "enable_clustering": True
                }
            }
        }
    
    def connect(self):
        """データベース接続"""
        try:
            # まず postgres データベースに接続してデータベースを作成
            conn_params = self.config["database"].copy()
            target_db = conn_params.pop("database")
            conn_params["database"] = "postgres"
            
            self.connection = psycopg2.connect(**conn_params)
            self.connection.autocommit = True
            self.cursor = self.connection.cursor()
            
            # データベースの存在確認と作成
            self.cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (target_db,)
            )
            
            if not self.cursor.fetchone():
                logger.info(f"Creating database: {target_db}")
                self.cursor.execute(
                    sql.SQL("CREATE DATABASE {}").format(
                        sql.Identifier(target_db)
                    )
                )
            
            # 作成したデータベースに再接続
            self.connection.close()
            conn_params["database"] = target_db
            self.connection = psycopg2.connect(**conn_params)
            self.cursor = self.connection.cursor()
            
            logger.info("Database connection established")
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def setup_pgvector_extension(self):
        """pgvector拡張のセットアップ"""
        try:
            # pgvector拡張の作成
            self.cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            self.connection.commit()
            
            # バージョン確認
            self.cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
            version = self.cursor.fetchone()
            
            if version:
                logger.info(f"pgvector extension installed (version: {version[0]})")
            else:
                raise Exception("pgvector extension installation failed")
                
        except Exception as e:
            logger.error(f"Failed to setup pgvector extension: {e}")
            self.connection.rollback()
            raise
    
    def create_schemas(self):
        """スキーマの作成"""
        try:
            # a2aスキーマの作成
            self.cursor.execute("CREATE SCHEMA IF NOT EXISTS a2a;")
            
            # 統計用スキーマ
            self.cursor.execute("CREATE SCHEMA IF NOT EXISTS a2a_stats;")
            
            # インデックス用スキーマ
            self.cursor.execute("CREATE SCHEMA IF NOT EXISTS a2a_index;")
            
            self.connection.commit()
            logger.info("Schemas created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create schemas: {e}")
            self.connection.rollback()
            raise
    
    def create_tables(self):
        """テーブルの作成"""
        try:
            # A2A通信テーブル
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS a2a.communications (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL,
                    sender VARCHAR(255) NOT NULL,
                    receiver VARCHAR(255) NOT NULL,
                    message_type VARCHAR(100),
                    content TEXT,
                    metadata JSONB,
                    embedding vector(%s),
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );
            """, (self.config["pgvector"]["vector_dimension"],))
            
            # 異常パターンテーブル
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS a2a.anomaly_patterns (
                    id SERIAL PRIMARY KEY,
                    pattern_name VARCHAR(255) NOT NULL,
                    pattern_type VARCHAR(100),
                    severity VARCHAR(50),
                    description TEXT,
                    detection_rules JSONB,
                    embedding vector(%s),
                    occurrence_count INTEGER DEFAULT 0,
                    last_detected TIMESTAMPTZ,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );
            """, (self.config["pgvector"]["vector_dimension"],))
            
            # エージェント情報テーブル
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS a2a.agents (
                    id SERIAL PRIMARY KEY,
                    agent_name VARCHAR(255) UNIQUE NOT NULL,
                    agent_type VARCHAR(100),
                    status VARCHAR(50),
                    capabilities JSONB,
                    performance_metrics JSONB,
                    embedding vector(%s),
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );
            """, (self.config["pgvector"]["vector_dimension"],))
            
            # セマンティック分析結果テーブル
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS a2a.semantic_analysis (
                    id SERIAL PRIMARY KEY,
                    communication_id INTEGER REFERENCES a2a.communications(id),
                    analysis_type VARCHAR(100),
                    semantic_category VARCHAR(255),
                    confidence_score FLOAT,
                    insights JSONB,
                    embedding vector(%s),
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );
            """, (self.config["pgvector"]["vector_dimension"],))
            
            self.connection.commit()
            logger.info("Tables created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            self.connection.rollback()
            raise
    
    def create_indexes(self):
        """インデックスの作成"""
        try:
            # HNSWインデックスの作成
            index_method = self.config["pgvector"]["index_method"]
            index_params = self.config["pgvector"]["index_params"]
            
            # A2A通信のベクトルインデックス
            self.cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_communications_embedding 
                ON a2a.communications 
                USING {index_method} (embedding vector_cosine_ops)
                WITH (m = {index_params['m']}, ef_construction = {index_params['ef_construction']});
            """)
            
            # 異常パターンのベクトルインデックス
            self.cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_anomaly_patterns_embedding 
                ON a2a.anomaly_patterns 
                USING {index_method} (embedding vector_cosine_ops)
                WITH (m = {index_params['m']}, ef_construction = {index_params['ef_construction']});
            """)
            
            # タイムスタンプインデックス
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_communications_timestamp 
                ON a2a.communications(timestamp DESC);
            """)
            
            # エージェント名インデックス
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_communications_agents 
                ON a2a.communications(sender, receiver);
            """)
            
            # JSONB GINインデックス
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_communications_metadata 
                ON a2a.communications USING GIN (metadata);
            """)
            
            self.connection.commit()
            logger.info("Indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            self.connection.rollback()
            raise
    
    def create_functions(self):
        """便利な関数の作成"""
        try:
            # 類似検索関数
            self.cursor.execute("""
                CREATE OR REPLACE FUNCTION a2a.find_similar_communications(
                    query_embedding vector,
                    limit_count INTEGER DEFAULT 10
                )
                RETURNS TABLE(
                    id INTEGER,
                    sender VARCHAR,
                    receiver VARCHAR,
                    content TEXT,
                    similarity FLOAT
                )
                AS $$
                BEGIN
                    RETURN QUERY
                    SELECT 
                        c.id,
                        c.sender,
                        c.receiver,
                        c.content,
                        1 - (c.embedding <=> query_embedding) as similarity
                    FROM a2a.communications c
                    WHERE c.embedding IS NOT NULL
                    ORDER BY c.embedding <=> query_embedding
                    LIMIT limit_count;
                END;
                $$ LANGUAGE plpgsql;
            """)
            
            # 更新日時自動更新トリガー
            self.cursor.execute("""
                CREATE OR REPLACE FUNCTION a2a.update_updated_at()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """)
            
            # トリガーの作成
            for table in ['communications', 'anomaly_patterns', 'agents']:
                self.cursor.execute(f"""
                    CREATE TRIGGER update_{table}_updated_at
                    BEFORE UPDATE ON a2a.{table}
                    FOR EACH ROW
                    EXECUTE FUNCTION a2a.update_updated_at();
                """)
            
            self.connection.commit()
            logger.info("Functions and triggers created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create functions: {e}")
            self.connection.rollback()
            raise
    
    def setup_permissions(self):
        """権限設定"""
        try:
            user = self.config["database"]["user"]
            
            # スキーマへの権限
            self.cursor.execute(f"GRANT ALL ON SCHEMA a2a TO {user};")
            self.cursor.execute(f"GRANT ALL ON SCHEMA a2a_stats TO {user};")
            self.cursor.execute(f"GRANT ALL ON SCHEMA a2a_index TO {user};")
            
            # テーブルへの権限
            self.cursor.execute(f"GRANT ALL ON ALL TABLES IN SCHEMA a2a TO {user};")
            self.cursor.execute(f"GRANT ALL ON ALL SEQUENCES IN SCHEMA a2a TO {user};")
            self.cursor.execute(f"GRANT ALL ON ALL FUNCTIONS IN SCHEMA a2a TO {user};")
            
            self.connection.commit()
            logger.info("Permissions granted successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup permissions: {e}")
            self.connection.rollback()
            raise
    
    def verify_setup(self) -> Dict[str, Any]:
        """セットアップの検証"""
        verification = {
            "pgvector_installed": False,
            "schemas_created": [],
            "tables_created": [],
            "indexes_created": [],
            "setup_complete": False
        }
        
        try:
            # pgvector確認
            self.cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector';")
            verification["pgvector_installed"] = bool(self.cursor.fetchone())
            
            # スキーマ確認
            self.cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name LIKE 'a2a%';
            """)
            verification["schemas_created"] = [row[0] for row in self.cursor.fetchall()]
            
            # テーブル確認
            self.cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'a2a';
            """)
            verification["tables_created"] = [row[0] for row in self.cursor.fetchall()]
            
            # インデックス確認
            self.cursor.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE schemaname = 'a2a';
            """)
            verification["indexes_created"] = [row[0] for row in self.cursor.fetchall()]
            
            verification["setup_complete"] = (
                verification["pgvector_installed"] and
                len(verification["schemas_created"]) >= 3 and
                len(verification["tables_created"]) >= 4 and
                len(verification["indexes_created"]) >= 5
            )
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            
        return verification
    
    def close(self):
        """接続のクローズ"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            
    def execute_setup(self) -> Dict[str, Any]:
        """完全なセットアップの実行"""
        setup_result = {
            "timestamp": datetime.now().isoformat(),
            "status": "starting",
            "steps": {},
            "verification": {}
        }
        
        try:
            # 1. データベース接続
            logger.info("Step 1: Connecting to database...")
            self.connect()
            setup_result["steps"]["connection"] = "success"
            
            # 2. pgvector拡張のセットアップ
            logger.info("Step 2: Setting up pgvector extension...")
            self.setup_pgvector_extension()
            setup_result["steps"]["pgvector_extension"] = "success"
            
            # 3. スキーマ作成
            logger.info("Step 3: Creating schemas...")
            self.create_schemas()
            setup_result["steps"]["schemas"] = "success"
            
            # 4. テーブル作成
            logger.info("Step 4: Creating tables...")
            self.create_tables()
            setup_result["steps"]["tables"] = "success"
            
            # 5. インデックス作成
            logger.info("Step 5: Creating indexes...")
            self.create_indexes()
            setup_result["steps"]["indexes"] = "success"
            
            # 6. 関数作成
            logger.info("Step 6: Creating functions...")
            self.create_functions()
            setup_result["steps"]["functions"] = "success"
            
            # 7. 権限設定
            logger.info("Step 7: Setting up permissions...")
            self.setup_permissions()
            setup_result["steps"]["permissions"] = "success"
            
            # 8. 検証
            logger.info("Step 8: Verifying setup...")
            setup_result["verification"] = self.verify_setup()
            
            if setup_result["verification"]["setup_complete"]:
                setup_result["status"] = "completed"
                logger.info("✅ pgvector database setup completed successfully!")
            else:
                setup_result["status"] = "incomplete"
                logger.warning("⚠️ Setup completed with some issues")
                
        except Exception as e:
            setup_result["status"] = "failed"
            setup_result["error"] = str(e)
            logger.error(f"❌ Setup failed: {e}")
            raise
            
        finally:
            self.close()
            
        return setup_result

def main():
    """メイン処理"""
    # 設定ファイルの確認
    config_path = PROJECT_ROOT / "config" / "pgvector_config.json"
    
    config = None
    if config_path.exists():
        with open(config_path, 'r') as f:
            config_data = json.load(f)
            # database設定を追加
            if "database" not in config_data:
                config = {
                    "database": {
                        "host": "localhost",
                        "port": 5432,
                        "database": "ai_company_db",
                        "user": "aicompany",
                        "password": ""
                    },
                    "pgvector": config_data.get("pgvector", {
                        "vector_dimension": 1536,
                        "index_method": "hnsw",
                        "index_params": {"m": 16, "ef_construction": 64}
                    })
                }
    
    print("🚀 pgvector Database Setup")
    print("=" * 60)
    
    # 環境変数の確認
    if not os.getenv("PGPASSWORD"):
        print("⚠️  Warning: PGPASSWORD environment variable not set")
        print("   You may need to set it for database connection")
        print("   Example: export PGPASSWORD='your_password'")
        print()
    
    try:
        setup = PgVectorDatabaseSetup(config)
        result = setup.execute_setup()
        
        # 結果の保存
        result_file = PROJECT_ROOT / "logs" / f"pgvector_setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"\n💾 Setup report saved to: {result_file}")
        
        # 結果表示
        if result["status"] == "completed":
            print("\n✅ Setup completed successfully!")
            print(f"\n📊 Verification Summary:")
            print(f"   - pgvector installed: {result['verification']['pgvector_installed']}")
            print(f"   - Schemas created: {len(result['verification']['schemas_created'])}")
            print(f"   - Tables created: {len(result['verification']['tables_created'])}")
            print(f"   - Indexes created: {len(result['verification']['indexes_created'])}")
        else:
            print("\n❌ Setup failed or incomplete")
            if "error" in result:
                print(f"   Error: {result['error']}")
                
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()