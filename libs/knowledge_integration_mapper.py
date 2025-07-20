#!/usr/bin/env python3
"""
Knowledge Base 統合マッピングシステム
pgvector + SQLite ハイブリッド構成
"""

import os
import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# 設定
KNOWLEDGE_BASE_PATH = "/home/aicompany/ai_co/knowledge_base"
SQLITE_DB_PATH = "/home/aicompany/ai_co/knowledge_base/integrated_knowledge.db"

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeIntegrationMapper:
    def __init__(self):
        self.db_conn = None
        
    def initialize_sqlite(self):
        """SQLite統合データベース初期化"""
        logger.info("SQLite統合データベース初期化")
        
        self.db_conn = sqlite3.connect(SQLITE_DB_PATH)
        self.db_conn.row_factory = sqlite3.Row
        
        # テーブル作成
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS knowledge_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            source_file TEXT NOT NULL,
            file_hash TEXT NOT NULL,
            chunk_index INTEGER DEFAULT 0,
            total_chunks INTEGER DEFAULT 1,
            category TEXT NOT NULL,
            priority INTEGER NOT NULL,
            file_size INTEGER NOT NULL,
            metadata TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        self.db_conn.execute(create_table_sql)
        
        # インデックス作成
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_source_file ON knowledge_documents(source_file)",
            "CREATE INDEX IF NOT EXISTS idx_category ON knowledge_documents(category)",
            "CREATE INDEX IF NOT EXISTS idx_priority ON knowledge_documents(priority)",
            "CREATE INDEX IF NOT EXISTS idx_file_hash ON knowledge_documents(file_hash)",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_uuid ON knowledge_documents(uuid)"
        ]
        
        for index_sql in indexes:
            self.db_conn.execute(index_sql)
            
        # FTS (Full Text Search) テーブル
        fts_sql = """
        CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
            title, content, source_file, category, content=knowledge_documents
        )
        """
        self.db_conn.execute(fts_sql)
        
        self.db_conn.commit()
        logger.info("SQLite初期化完了")
        
    def get_file_priority(self, filepath: str) -> int:
        """ファイル優先度判定"""
        path_str = str(filepath).lower()
        
        if any(x in path_str for x in ['master_kb', 'elder_identity', 'elder_knowledge_minimal']):
            return 1
        elif any(x in path_str for x in ['core/', 'four_sages/', 'protocols/']):
            return 2
        elif any(x in path_str for x in ['technical/', 'decisions/', 'guides/']):
            return 3
        else:
            return 4
            
    def categorize_file(self, filepath: str) -> str:
        """ファイルカテゴリ分類"""
        path_str = str(filepath)
        
        if 'core/' in path_str:
            if 'identity/' in path_str: return 'core_identity'
            elif 'protocols/' in path_str: return 'core_protocols'
            elif 'guides/' in path_str: return 'core_guides'
            return 'core_system'
        elif 'four_sages/' in path_str:
            return 'four_sages_system'
        elif 'technical/' in path_str:
            if 'architecture/' in path_str: return 'technical_architecture'
            elif 'implementations/' in path_str: return 'technical_implementations'
            return 'technical_general'
        elif 'elder_council/' in path_str:
            if 'decisions/' in path_str: return 'elder_council_decisions'
            elif 'reports/' in path_str: return 'elder_council_reports'
            return 'elder_council_general'
        elif 'projects/' in path_str:
            return 'project_management'
        else:
            return 'miscellaneous'
            
    def chunk_content(self, content: str, chunk_size: int = 2000) -> List[str]:
        """コンテンツチャンク化"""
        if len(content) <= chunk_size:
            return [content]
            
        chunks = []
        words = content.split()
        current_chunk = []
        current_size = 0
        
        for word in words:
            if current_size + len(word) + 1 <= chunk_size:
                current_chunk.append(word)
                current_size += len(word) + 1
            else:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
                
        if current_chunk:
            chunks.append(' '.join(current_chunk))
            
        return chunks
        
    def process_and_store_file(self, filepath: str) -> bool:
        """ファイル処理と保存"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if len(content.strip()) < 50:
                return False
                
            # メタデータ生成
            relative_path = os.path.relpath(filepath, KNOWLEDGE_BASE_PATH)
            title = Path(filepath).stem
            priority = self.get_file_priority(filepath)
            category = self.categorize_file(filepath)
            file_hash = str(hash(content))
            
            # チャンク化
            chunks = self.chunk_content(content)
            
            # データベース挿入
            for i, chunk in enumerate(chunks):
                import uuid
                doc_uuid = str(uuid.uuid4())
                
                metadata = {
                    'processed_at': datetime.now().isoformat(),
                    'chunk_size': len(chunk),
                    'directory': str(Path(relative_path).parent),
                    'integration_version': '2025.07.21',
                    'word_count': len(chunk.split())
                }
                
                insert_sql = """
                INSERT INTO knowledge_documents (
                    uuid, title, content, source_file, file_hash,
                    chunk_index, total_chunks, category, priority,
                    file_size, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                self.db_conn.execute(insert_sql, [
                    doc_uuid, title, chunk, relative_path, file_hash,
                    i, len(chunks), category, priority,
                    len(content), json.dumps(metadata)
                ])
                
                # FTS挿入
                fts_sql = """
                INSERT INTO knowledge_fts (title, content, source_file, category)
                VALUES (?, ?, ?, ?)
                """
                self.db_conn.execute(fts_sql, [title, chunk, relative_path, category])
                
            self.db_conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"ファイル処理エラー {filepath}: {e}")
            return False
            
    def process_all_files(self):
        """全ファイル処理"""
        logger.info("全ナレッジベースファイル処理開始")
        
        # 既存データクリア
        self.db_conn.execute("DELETE FROM knowledge_documents")
        self.db_conn.execute("DELETE FROM knowledge_fts")
        self.db_conn.commit()
        
        # マークダウンファイル取得
        markdown_files = []
        for root, dirs, files in os.walk(KNOWLEDGE_BASE_PATH):
            for file in files:
                if file.endswith('.md'):
                    filepath = os.path.join(root, file)
                    markdown_files.append(filepath)
                    
        # 優先度でソート
        markdown_files.sort(key=self.get_file_priority)
        
        logger.info(f"処理対象: {len(markdown_files)}ファイル")
        
        # 統計情報
        stats = {
            'total_files': len(markdown_files),
            'processed_files': 0,
            'skipped_files': 0,
            'total_chunks': 0,
            'categories': {},
            'priorities': {}
        }
        
        # ファイル処理
        for i, filepath in enumerate(markdown_files):
            if self.process_and_store_file(filepath):
                stats['processed_files'] += 1
                
                # 統計更新
                priority = self.get_file_priority(filepath)
                category = self.categorize_file(filepath)
                stats['categories'][category] = stats['categories'].get(category, 0) + 1
                stats['priorities'][priority] = stats['priorities'].get(priority, 0) + 1
            else:
                stats['skipped_files'] += 1
                
            # 進捗表示
            if (i + 1) % 20 == 0:
                logger.info(f"進捗: {i + 1}/{len(markdown_files)} ファイル処理")
                
        # 最終統計
        cursor = self.db_conn.execute("SELECT COUNT(*) FROM knowledge_documents")
        stats['total_chunks'] = cursor.fetchone()[0]
        
        return stats
        
    def create_search_functions(self):
        """検索機能作成"""
        logger.info("検索機能セットアップ")
        
        # ビュー作成
        view_sql = """
        CREATE VIEW IF NOT EXISTS knowledge_summary AS
        SELECT 
            category,
            priority,
            COUNT(*) as document_count,
            SUM(file_size) as total_size,
            AVG(file_size) as avg_size
        FROM knowledge_documents 
        GROUP BY category, priority
        ORDER BY priority, category
        """
        self.db_conn.execute(view_sql)
        
        # 統計関数
        self.db_conn.commit()
        logger.info("検索機能セットアップ完了")
        
    def generate_mapping_report(self) -> Dict[str, Any]:
        """マッピングレポート生成"""
        logger.info("統合マッピングレポート生成")
        
        # 基本統計
        cursor = self.db_conn.execute("SELECT COUNT(*) FROM knowledge_documents")
        total_docs = cursor.fetchone()[0]
        
        cursor = self.db_conn.execute("SELECT COUNT(DISTINCT source_file) FROM knowledge_documents")
        unique_files = cursor.fetchone()[0]
        
        # カテゴリ別統計
        cursor = self.db_conn.execute("""
        SELECT category, COUNT(*), AVG(file_size), MAX(priority)
        FROM knowledge_documents 
        GROUP BY category 
        ORDER BY COUNT(*) DESC
        """)
        category_stats = cursor.fetchall()
        
        # 優先度別統計
        cursor = self.db_conn.execute("""
        SELECT priority, COUNT(*), AVG(file_size)
        FROM knowledge_documents 
        GROUP BY priority 
        ORDER BY priority
        """)
        priority_stats = cursor.fetchall()
        
        # 最大ファイル
        cursor = self.db_conn.execute("""
        SELECT source_file, file_size, category, priority
        FROM knowledge_documents 
        ORDER BY file_size DESC 
        LIMIT 10
        """)
        largest_files = cursor.fetchall()
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_documents': total_docs,
            'unique_files': unique_files,
            'categories': [dict(row) for row in category_stats],
            'priorities': [dict(row) for row in priority_stats],
            'largest_files': [dict(row) for row in largest_files],
            'database_path': SQLITE_DB_PATH,
            'database_size': os.path.getsize(SQLITE_DB_PATH) if os.path.exists(SQLITE_DB_PATH) else 0
        }
        
        return report
        
    def run_integration(self):
        """統合処理実行"""
        logger.info("=== ナレッジベース統合マッピング開始 ===")
        
        try:
            # 初期化
            self.initialize_sqlite()
            
            # ファイル処理
            stats = self.process_all_files()
            
            # 検索機能作成
            self.create_search_functions()
            
            # レポート生成
            report = self.generate_mapping_report()
            
            # 結果出力
            logger.info("=== 統合完了統計 ===")
            logger.info(f"総ファイル数: {stats['total_files']}")
            logger.info(f"処理成功: {stats['processed_files']}")
            logger.info(f"スキップ: {stats['skipped_files']}")
            logger.info(f"総ドキュメント: {stats['total_chunks']}")
            logger.info(f"カテゴリ別: {stats['categories']}")
            logger.info(f"優先度別: {stats['priorities']}")
            
            # レポートファイル保存
            report_path = f"/home/aicompany/ai_co/knowledge_base/integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"レポート保存: {report_path}")
            
            logger.info("=== ナレッジベース統合マッピング完了 ===")
            
        except Exception as e:
            logger.error(f"統合エラー: {e}")
            raise
        finally:
            if self.db_conn:
                self.db_conn.close()

def main():
    """メイン実行"""
    mapper = KnowledgeIntegrationMapper()
    
    try:
        mapper.run_integration()
        return 0
    except Exception as e:
        logger.error(f"実行エラー: {e}")
        return 1

if __name__ == "__main__":
    exit(main())