#!/usr/bin/env python3
"""
pgvector統合管理システム
全機能を統一インターフェースで提供
"""

import os
import json
import asyncio
import logging
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import sqlite3
import subprocess

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PgVectorUnifiedManager:
    """pgvector統合管理システム"""
    
    def __init__(self):
        """初期化メソッド"""
        self.config = {
            'postgres': {
                'host': 'localhost',
                'port': 8003,
                'database': 'elders_guild_pgvector',
                'user': 'aicompany',
                'password': 'secret123'
            },
            'sqlite_backup': '/home/aicompany/ai_co/knowledge_base/integrated_knowledge.db',
            'knowledge_base_path': '/home/aicompany/ai_co/knowledge_base',
            'docker_command_prefix': ['sg', 'docker', '-c']
        }
        
    async def health_check(self) -> Dict[str, Any]:
        """システムヘルスチェック"""
        logger.info("🔍 pgvectorシステムヘルスチェック開始")
        
        health = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'unknown',
            'components': {}
        }
        
        # 1. Dockerコンテナ状況
        try:
            result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
            postgres_running = 'elders-guild-postgres-new' in result.stdout
            health['components']['docker_container'] = {
                'status': 'healthy' if postgres_running else 'unhealthy',
                'details': 'PostgreSQL container running' if postgres_running else 'PostgreSQL container not found'
            }
        except Exception as e:
            health['components']['docker_container'] = {
                'status': 'error',
                'details': f'Docker check failed: {e}'
            }
            
        # 2. PostgreSQL接続
        try:
            cmd = self.config['docker_command_prefix'] + [
                f"docker exec elders-guild-postgres-new psql -U {self.config['postgres']['user']} "
                f"-d {self.config['postgres']['database']} -c 'SELECT version();'"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                health['components']['postgresql'] = {
                    'status': 'healthy',
                    'details': 'PostgreSQL connection successful',
                    'version': result.stdout.strip()
                }
            else:
                health['components']['postgresql'] = {
                    'status': 'unhealthy',
                    'details': f'Connection failed: {result.stderr}'
                }
        except Exception as e:
            health['components']['postgresql'] = {
                'status': 'error',
                'details': f'PostgreSQL check failed: {e}'
            }
            
        # 3. pgvector拡張
        try:
            cmd = self.config['docker_command_prefix'] + [
                f"docker exec elders-guild-postgres-new psql -U admin "
                f"-d {self.config['postgres']['database']} -c \"SELECT extname FROM pg_extension WHERE extname =  \
                    'vector';\""
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and 'vector' in result.stdout:
                health['components']['pgvector'] = {
                    'status': 'healthy',
                    'details': 'pgvector extension active',
                    'version_check': result.stdout.strip()
                }
            else:
                health['components']['pgvector'] = {
                    'status': 'unhealthy',
                    'details': f'pgvector extension not found. Output: {result.stdout}, Error: {result.stderr}'
                }
        except Exception as e:
            health['components']['pgvector'] = {
                'status': 'error',
                'details': f'pgvector check failed: {e}'
            }
            
        # 4. SQLiteバックアップ
        try:
            if os.path.exists(self.config['sqlite_backup']):
                size = os.path.getsize(self.config['sqlite_backup'])
                health['components']['sqlite_backup'] = {
                    'status': 'healthy',
                    'details': f'SQLite backup available ({size/1024/1024:.2f}MB)'
                }
            else:
                health['components']['sqlite_backup'] = {
                    'status': 'missing',
                    'details': 'SQLite backup file not found'
                }
        except Exception as e:
            health['components']['sqlite_backup'] = {
                'status': 'error',
                'details': f'SQLite check failed: {e}'
            }
            
        # 5. ナレッジベースファイル
        try:
            md_files = list(Path(self.config['knowledge_base_path']).rglob('*.md'))
            health['components']['knowledge_base'] = {
                'status': 'healthy',
                'details': f'{len(md_files)} markdown files found'
            }
        except Exception as e:
            health['components']['knowledge_base'] = {
                'status': 'error',
                'details': f'Knowledge base check failed: {e}'
            }
            
        # 総合ステータス判定
        statuses = [comp['status'] for comp in health['components'].values()]
        if all(s == 'healthy' for s in statuses):
            health['overall_status'] = 'healthy'
        elif any(s == 'error' for s in statuses):
            health['overall_status'] = 'error'
        else:
            health['overall_status'] = 'degraded'
            
        logger.info(f"✅ ヘルスチェック完了: {health['overall_status']}")
        return health
        
    async def setup_tables(self) -> bool:
        """PostgreSQLテーブル初期化"""
        logger.info("🔧 PostgreSQLテーブル初期化開始")
        
        try:
            # テーブル作成SQL
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS knowledge_documents (
                id SERIAL PRIMARY KEY,
                uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source_file TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                chunk_index INTEGER DEFAULT 0,
                total_chunks INTEGER DEFAULT 1,
                category TEXT NOT NULL,
                priority INTEGER NOT NULL,
                file_size INTEGER NOT NULL,
                embedding vector(384),
                metadata JSONB,
                sage_type TEXT DEFAULT 'knowledge_sage',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_knowledge_source_file ON knowledge_documents(source_file);
            CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_documents(category);
            CREATE INDEX IF NOT EXISTS idx_knowledge_priority ON knowledge_documents(priority);
            CREATE INDEX IF NOT EXISTS idx_knowledge_file_hash ON knowledge_documents(file_hash);
            CREATE INDEX IF NOT EXISTS idx_knowledge_embedding ON knowledge_documents 
                USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
            """
            
            cmd = self.config['docker_command_prefix'] + [
                f"docker exec elders-guild-postgres-new psql -U {self.config['postgres']['user']} "
                f"-d {self.config['postgres']['database']} -c \"{create_table_sql}\""
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ テーブル初期化成功")
                return True
            else:
                logger.error(f"❌ テーブル初期化失敗: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ テーブル初期化エラー: {e}")
            return False
            
    async def migrate_from_sqlite(self) -> Dict[str, Any]:
        """SQLiteからPostgreSQLへのデータマイグレーション"""
        logger.info("🔄 SQLite→PostgreSQLデータマイグレーション開始")
        
        migration_stats = {
            'start_time': datetime.now().isoformat(),
            'source_records': 0,
            'migrated_records': 0,
            'failed_records': 0,
            'status': 'unknown'
        }
        
        try:
            # SQLiteデータ読み込み
            sqlite_conn = sqlite3.connect(self.config['sqlite_backup'])
            sqlite_conn.row_factory = sqlite3.Row
            
            cursor = sqlite_conn.execute("SELECT COUNT(*) FROM knowledge_documents")
            migration_stats['source_records'] = cursor.fetchone()[0]
            logger.info(f"📊 SQLiteソースレコード数: {migration_stats['source_records']}")
            
            # PostgreSQL準備
            await self.setup_tables()
            
            # バッチマイグレーション
            cursor = sqlite_conn.execute("SELECT * FROM knowledge_documents ORDER BY priority, category" \
                "SELECT * FROM knowledge_documents ORDER BY priority, category")
            batch_size = 10  # より小さなバッチサイズ
            batch = []
            
            for row in cursor:
                batch.append(dict(row))
                
                if len(batch) >= batch_size:
                    success_count = await self._migrate_batch(batch)
                    migration_stats['migrated_records'] += success_count
                    migration_stats['failed_records'] += len(batch) - success_count
                    batch = []
                    
                    # 進捗表示
                    if migration_stats['migrated_records'] % 100 == 0:
                        logger.info(f"📈 マイグレーション進捗: {migration_stats['migrated_records']}件")
                        
            # 残りのバッチ処理
            if batch:
                success_count = await self._migrate_batch(batch)
                migration_stats['migrated_records'] += success_count
                migration_stats['failed_records'] += len(batch) - success_count
                
            sqlite_conn.close()
            
            # ステータス判定
            success_rate = migration_stats['migrated_records'] / migration_stats['source_records']
            if success_rate >= 0.95:
                migration_stats['status'] = 'success'
            elif success_rate >= 0.8:
                migration_stats['status'] = 'partial_success'
            else:
                migration_stats['status'] = 'failed'
                
            migration_stats['end_time'] = datetime.now().isoformat()
            migration_stats['success_rate'] = success_rate
            
            logger.info(f"✅ マイグレーション完了: {migration_stats['status']} "
                       f"({migration_stats['migrated_records']}/{migration_stats['source_records']})")
            
            return migration_stats
            
        except Exception as e:
            logger.error(f"❌ マイグレーションエラー: {e}")
            migration_stats['status'] = 'error'
            migration_stats['error'] = str(e)
            return migration_stats
            
    async def _migrate_batch(self, batch: List[Dict]) -> int:
        """バッチデータのマイグレーション"""
        try:
            # 簡易埋め込みベクトル生成（384次元）
            def generate_simple_embedding(text:
                """generate_simple_embedding生成メソッド"""
            str) -> str:
                # 文字頻度ベースの簡易ベクトル
                vector = [0.0] * 384
                for i, char in enumerate(text.lower()[:384]):
                    vector[i] = ord(char) / 255.0
                # 正規化
                norm = sum(x*x for x in vector) ** 0.5
                if norm > 0:
                    vector = [x/norm for x in vector]
                return '[' + ','.join(map(str, vector)) + ']'
            
            # 一件ずつ処理（コマンドライン長制限回避）
            success_count = 0
            for row in batch:
                try:
                    embedding = generate_simple_embedding(row['content'])
                    metadata = row.get('metadata', '{}')
                    
                    # 安全な文字列エスケープ
                    title = row['title'].replace("'", "''")[:100]
                    content = row['content'].replace("'", "''")[:5000]  # 短縮
                    source_file = row['source_file'].replace("'", "''")
                    category = row['category'].replace("'", "''")
                    
                    insert_sql = f"""
                    INSERT INTO knowledge_documents (
                        title, content, source_file, file_hash, chunk_index, total_chunks,
                        category, priority, file_size, embedding, metadata, sage_type
                    ) VALUES (
                        '{title}', '{content}', '{source_file}', 
                        '{row['file_hash']}', {row['chunk_index']}, {row['total_chunks']}, 
                        '{category}', {row['priority']}, {row['file_size']}, 
                        '{embedding}', '{metadata}', 'knowledge_sage'
                    );
                    """
                    
                    # PostgreSQL実行
                    cmd = self.config['docker_command_prefix'] + [
                        f"docker exec elders-guild-postgres-new psql -U admin "
                        f"-d {self.config['postgres']['database']} -c \"{insert_sql}\""
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        success_count += 1
                    else:
                        logger.warning(f"❌ 個別挿入失敗: {result.stderr[:200]}")
                        
                except Exception as e:
                    logger.warning(f"❌ 個別レコード処理失敗: {e}")
                    continue
                    
            return success_count
                
        except Exception as e:
            logger.error(f"❌ バッチマイグレーションエラー: {e}")
            return 0
            
    async def search_knowledge(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """統合知識検索"""
        logger.info(f"🔍 知識検索: '{query}' (limit: {limit})")
        
        try:
            # PostgreSQL検索を試行（similarity関数なしの簡易版）
            search_sql = f"""
            SELECT title, content, source_file, category, priority
            FROM knowledge_documents 
            WHERE content ILIKE '%{query}%' OR title ILIKE '%{query}%'
            ORDER BY priority ASC, created_at DESC
            LIMIT {limit};
            """
            
            cmd = self.config['docker_command_prefix'] + [
                f"docker exec elders-guild-postgres-new psql -U admin "
                f"-d {self.config['postgres']['database']} -t -c \"{search_sql}\""
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                # PostgreSQL結果をパース
                results = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip() and '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 5:
                            try:
                                results.append({
                                    'title': parts[0].strip(),
                                    'content': parts[1].strip()[:500],
                                    'source_file': parts[2].strip(),
                                    'category': parts[3].strip(),
                                    'priority': int(parts[4].strip()) if parts[4].strip().isdigit() else 4,
                                    'source': 'postgresql'
                                })
                            except (ValueError, IndexError) as e:
                                logger.warning(f"⚠️ PostgreSQL結果パースエラー: {e}")
                                continue
                
                if results:
                    logger.info(f"✅ PostgreSQL検索成功: {len(results)}件")
                    return results
                else:
                    logger.info("📝 PostgreSQL検索結果が空、SQLiteにフォールバック")
            
        except Exception as e:
            logger.warning(f"⚠️ PostgreSQL検索失敗: {e}")
            
        # フォールバック: SQLite検索
        try:
            sqlite_conn = sqlite3.connect(self.config['sqlite_backup'])
            sqlite_conn.row_factory = sqlite3.Row
            
            cursor = sqlite_conn.execute(
                "SELECT title, content, source_file, category, priority "
                "FROM knowledge_documents WHERE content LIKE ? "
                "ORDER BY priority ASC LIMIT ?",
                [f'%{query}%', limit]
            )
            
            results = []
            for row in cursor:
                results.append({
                    'title': row['title'],
                    'content': row['content'][:500],
                    'source_file': row['source_file'],
                    'category': row['category'],
                    'priority': row['priority'],
                    'source': 'sqlite'
                })
                
            sqlite_conn.close()
            logger.info(f"✅ SQLiteフォールバック検索成功: {len(results)}件")
            return results
            
        except Exception as e:
            logger.error(f"❌ SQLite検索も失敗: {e}")
            return []
            
    async def get_status(self) -> Dict[str, Any]:
        """システム状況取得"""
        logger.info("📊 システム状況取得")
        
        health = await self.health_check()
        
        # 追加統計情報
        try:
            # PostgreSQL統計
            cmd = self.config['docker_command_prefix'] + [
                f"docker exec elders-guild-postgres-new psql -U {self.config['postgres']['user']} "
                f"-d {self.config['postgres']['database']} -t -c "
                f"'SELECT COUNT(*) FROM knowledge_documents;'"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            pg_count = 0
            if result.returncode == 0 and result.stdout.strip():
                pg_count = int(result.stdout.strip())
                
            # SQLite統計
            sqlite_count = 0
            if os.path.exists(self.config['sqlite_backup']):
                sqlite_conn = sqlite3.connect(self.config['sqlite_backup'])
                cursor = sqlite_conn.execute("SELECT COUNT(*) FROM knowledge_documents")
                sqlite_count = cursor.fetchone()[0]
                sqlite_conn.close()
                
            health['statistics'] = {
                'postgresql_documents': pg_count,
                'sqlite_documents': sqlite_count,
                'knowledge_base_files': len(list(Path(self.config['knowledge_base_path']).rglob('*.md')))
            }
            
        except Exception as e:
            logger.warning(f"⚠️ 統計情報取得部分失敗: {e}")
            
        return health

# CLI インターフェース
async def main():
    """メインCLI"""
    import sys
    
    manager = PgVectorUnifiedManager()
    
    if len(sys.argv) < 2:
        print("使用方法: python3 pgvector_unified_manager.py <command>")
        print("コマンド: health, setup, migrate, search <query>, status")
        return 1
        
    command = sys.argv[1]
    
    try:
        if command == 'health':
            health = await manager.health_check()
            print(json.dumps(health, indent=2, ensure_ascii=False))
            
        elif command == 'setup':
            success = await manager.setup_tables()
            print("✅ セットアップ成功" if success else "❌ セットアップ失敗")
            
        elif command == 'migrate':
            stats = await manager.migrate_from_sqlite()
            print(json.dumps(stats, indent=2, ensure_ascii=False))
            
        elif command == 'search':
            if len(sys.argv) < 3:
                print("使用方法: search <query>")
                return 1
            query = ' '.join(sys.argv[2:])
            results = await manager.search_knowledge(query)
            print(json.dumps(results, indent=2, ensure_ascii=False))
            
        elif command == 'status':
            status = await manager.get_status()
            print(json.dumps(status, indent=2, ensure_ascii=False))
            
        else:
            print(f"未知のコマンド: {command}")
            return 1
            
        return 0
        
    except Exception as e:
        logger.error(f"❌ コマンド実行エラー: {e}")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))