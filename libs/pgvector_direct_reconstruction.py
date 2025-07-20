#!/usr/bin/env python3
"""
pgvector Knowledge Base 直接再構築システム
最小限のライブラリを使用した確実版
"""

import os
import json
import logging
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np

# 設定
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'elders_guild_pgvector',
    'user': 'aicompany',
    'password': 'secret123'
}
KNOWLEDGE_BASE_PATH = "/home/aicompany/ai_co/knowledge_base"

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DirectPgVectorReconstructor:
    def __init__(self):
        self.conn = None
        
    def connect_db(self):
        """データベース接続"""
        try:
            self.conn = psycopg2.connect(**DATABASE_CONFIG)
            self.conn.autocommit = True
            logger.info("PostgreSQL接続成功")
        except Exception as e:
            logger.error(f"データベース接続エラー: {e}")
            raise
            
    def backup_and_clear(self):
        """バックアップとクリア"""
        logger.info("データベースバックアップとクリア開始")
        
        with self.conn.cursor() as cur:
            # バックアップテーブル作成
            backup_table = f"knowledge_documents_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            cur.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM knowledge_documents")
            
            # 既存データ数確認
            cur.execute("SELECT COUNT(*) FROM knowledge_documents")
            count = cur.fetchone()[0]
            logger.info(f"バックアップ作成: {backup_table} ({count}件)")
            
            # データクリア
            cur.execute("TRUNCATE TABLE knowledge_documents RESTART IDENTITY CASCADE")
            logger.info("既存データクリア完了")
            
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
            return 'core_knowledge'
        elif 'four_sages/' in path_str:
            return 'four_sages'
        elif 'technical/' in path_str:
            return 'technical'
        elif 'elder_council/' in path_str:
            return 'elder_council'
        elif 'projects/' in path_str:
            return 'projects'
        else:
            return 'general'
            
    def simple_chunk_content(self, content: str, chunk_size: int = 1000) -> list:
        """シンプルなコンテンツチャンク化"""
        words = content.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            if len(chunk.strip()) > 50:
                chunks.append(chunk)
                
        return chunks if chunks else [content]
        
    def generate_simple_embedding(self, text: str) -> list:
        """シンプルな埋め込み生成（文字頻度ベース）"""
        # 簡易的な特徴ベクトル生成（256次元）
        char_freq = {}
        for char in text.lower():
            if char.isalnum():
                char_freq[char] = char_freq.get(char, 0) + 1
                
        # 固定サイズベクトル化
        vector = [0.0] * 256
        for i, char in enumerate('abcdefghijklmnopqrstuvwxyz0123456789'):
            if i < 256:
                vector[i] = char_freq.get(char, 0) / max(len(text), 1)
                
        # 正規化
        norm = sum(x*x for x in vector) ** 0.5
        if norm > 0:
            vector = [x/norm for x in vector]
            
        return vector
        
    def process_file(self, filepath: str) -> dict:
        """ファイル処理"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if len(content.strip()) < 50:
                return None
                
            # メタデータ生成
            relative_path = os.path.relpath(filepath, KNOWLEDGE_BASE_PATH)
            file_hash = hashlib.md5(content.encode()).hexdigest()
            priority = self.get_file_priority(filepath)
            category = self.categorize_file(filepath)
            
            # チャンク分割
            chunks = self.simple_chunk_content(content)
            
            return {
                'filepath': relative_path,
                'title': Path(filepath).stem,
                'content': content,
                'chunks': chunks,
                'file_hash': file_hash,
                'priority': priority,
                'category': category,
                'file_size': len(content)
            }
            
        except Exception as e:
            logger.error(f"ファイル処理エラー {filepath}: {e}")
            return None
            
    def insert_document(self, doc_data: dict):
        """ドキュメント挿入"""
        with self.conn.cursor() as cur:
            for i, chunk in enumerate(doc_data['chunks']):
                # 埋め込みベクトル生成
                embedding = self.generate_simple_embedding(chunk)
                
                # メタデータ
                metadata = {
                    'processed_at': datetime.now().isoformat(),
                    'chunk_size': len(chunk),
                    'directory': str(Path(doc_data['filepath']).parent),
                    'reconstruction_version': '2025.07.21'
                }
                
                # データ挿入
                insert_query = """
                    INSERT INTO knowledge_documents (
                        uuid, title, content, source_file, file_hash, 
                        chunk_index, total_chunks, category, priority, 
                        file_size, embedding, metadata, sage_type, 
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """
                
                cur.execute(insert_query, [
                    str(uuid.uuid4()),
                    doc_data['title'],
                    chunk,
                    doc_data['filepath'],
                    doc_data['file_hash'],
                    i,
                    len(doc_data['chunks']),
                    doc_data['category'],
                    doc_data['priority'],
                    doc_data['file_size'],
                    embedding,
                    json.dumps(metadata),
                    'knowledge_sage',
                    datetime.now(),
                    datetime.now()
                ])
                
    def get_markdown_files(self) -> list:
        """マークダウンファイル一覧取得"""
        files = []
        for root, dirs, filenames in os.walk(KNOWLEDGE_BASE_PATH):
            for filename in filenames:
                if filename.endswith('.md'):
                    filepath = os.path.join(root, filename)
                    files.append(filepath)
                    
        # 優先度でソート
        files.sort(key=self.get_file_priority)
        return files
        
    def optimize_database(self):
        """データベース最適化"""
        logger.info("データベース最適化開始")
        
        with self.conn.cursor() as cur:
            # 統計更新
            cur.execute("ANALYZE knowledge_documents")
            
            # インデックス再構築
            cur.execute("REINDEX TABLE knowledge_documents")
            
            # 最終統計
            cur.execute("SELECT COUNT(*) FROM knowledge_documents")
            total_docs = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(DISTINCT source_file) FROM knowledge_documents")
            unique_sources = cur.fetchone()[0]
            
            logger.info(f"最適化完了 - 総ドキュメント: {total_docs}, ユニークソース: {unique_sources}")
            
    def reconstruct(self):
        """メイン再構築処理"""
        logger.info("=== pgvector直接再構築開始 ===")
        
        try:
            # データベース接続
            self.connect_db()
            
            # バックアップ・クリア
            self.backup_and_clear()
            
            # ファイル処理
            markdown_files = self.get_markdown_files()
            logger.info(f"処理対象: {len(markdown_files)}ファイル")
            
            stats = {
                'total_files': len(markdown_files),
                'processed_files': 0,
                'skipped_files': 0,
                'total_chunks': 0,
                'categories': {},
                'priorities': {}
            }
            
            for i, filepath in enumerate(markdown_files):
                doc_data = self.process_file(filepath)
                
                if doc_data:
                    self.insert_document(doc_data)
                    
                    stats['processed_files'] += 1
                    stats['total_chunks'] += len(doc_data['chunks'])
                    stats['categories'][doc_data['category']] = stats['categories'].get(doc_data['category'], 0) + 1
                    stats['priorities'][doc_data['priority']] = stats['priorities'].get(doc_data['priority'], 0) + 1
                else:
                    stats['skipped_files'] += 1
                    
                # 進捗表示
                if (i + 1) % 20 == 0:
                    logger.info(f"進捗: {i + 1}/{len(markdown_files)} ファイル処理")
                    
            # 最適化
            self.optimize_database()
            
            # 結果出力
            logger.info("=== 再構築完了統計 ===")
            logger.info(f"総ファイル数: {stats['total_files']}")
            logger.info(f"処理成功: {stats['processed_files']}")
            logger.info(f"スキップ: {stats['skipped_files']}")
            logger.info(f"総チャンク数: {stats['total_chunks']}")
            logger.info(f"カテゴリ別: {stats['categories']}")
            logger.info(f"優先度別: {stats['priorities']}")
            
            logger.info("=== pgvector直接再構築完了 ===")
            
        except Exception as e:
            logger.error(f"再構築エラー: {e}")
            raise
        finally:
            if self.conn:
                self.conn.close()

def main():
    """メイン実行"""
    reconstructor = DirectPgVectorReconstructor()
    
    try:
        reconstructor.reconstruct()
    except Exception as e:
        logger.error(f"実行エラー: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())