#!/usr/bin/env python3
"""
pgvector Knowledge Base 完全再構築システム
2025年7月21日 - knowledge_baseクリーンアップ後の再構築
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio
import asyncpg
import hashlib
import tiktoken
from sentence_transformers import SentenceTransformer

# 設定
DATABASE_URL = "postgresql://aicompany:secret123@localhost:5432/elders_guild_pgvector"
KNOWLEDGE_BASE_PATH = "/home/aicompany/ai_co/knowledge_base"
CHUNK_SIZE = 1000  # トークン数
OVERLAP_SIZE = 100  # オーバーラップ
BATCH_SIZE = 10   # バッチ処理サイズ

# 埋め込みモデル
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/aicompany/ai_co/logs/pgvector_reconstruction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PgVectorKnowledgeReconstructor:
    """PgVectorKnowledgeReconstructorクラス"""
    def __init__(self):
        """初期化メソッド"""
        self.model = None
        self.tokenizer = None
        self.db_pool = None
        
    async def initialize(self):
        """初期化処理"""
        logger.info("pgvector再構築システム初期化開始")
        
        # 埋め込みモデル初期化
        logger.info(f"埋め込みモデル読み込み: {MODEL_NAME}")
        self.model = SentenceTransformer(MODEL_NAME)
        
        # トークナイザー初期化
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # データベース接続プール作成
        try:
            self.db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=5)
            logger.info("データベース接続プール作成成功")
        except Exception as e:
            logger.error(f"データベース接続エラー: {e}")
            raise
            
    async def cleanup_existing_data(self):
        """既存データのクリーンアップ"""
        logger.info("既存データクリーンアップ開始")
        
        async with self.db_pool.acquire() as conn:
            # バックアップテーブル作成
            backup_table = f"knowledge_documents_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            await conn.execute(f"""
                CREATE TABLE {backup_table} AS 
                SELECT * FROM knowledge_documents;
            """)
            logger.info(f"バックアップテーブル作成: {backup_table}")
            
            # 既存データ削除
            count = await conn.fetchval("SELECT COUNT(*) FROM knowledge_documents")
            await conn.execute("TRUNCATE TABLE knowledge_documents RESTART IDENTITY CASCADE")
            logger.info(f"既存データ削除完了: {count}件")
            
    def get_file_priority(self, filepath: str) -> int:
        """ファイルの優先度を決定"""
        path = Path(filepath)
        
        # 超高優先度 (1)
        if any(
            x in str(path) for x in ['MASTER_KB',
            'CLAUDE_ELDER_IDENTITY',
            'ELDER_KNOWLEDGE_MINIMAL']
        ):
            return 1
            
        # 高優先度 (2) - コア知識
        if any(x in str(path) for x in ['core/', 'four_sages/', 'technical/architecture']):
            return 2
            
        # 中優先度 (3) - 技術・プロジェクト
        if any(x in str(path) for x in ['technical/', 'projects/', 'elder_council/decisions']):
            return 3
            
        # 低優先度 (4) - その他
        return 4
        
    def categorize_file(self, filepath: str) -> str:
        """ファイルのカテゴリ分類"""
        path = Path(filepath)
        
        if 'core/' in str(path):
            if 'identity/' in str(path):
                return 'core_identity'
            elif 'protocols/' in str(path):
                return 'core_protocols'
            elif 'guides/' in str(path):
                return 'core_guides'
            return 'core_system'
            
        elif 'four_sages/' in str(path):
            return 'four_sages_system'
            
        elif 'technical/' in str(path):
            if 'architecture/' in str(path):
                return 'technical_architecture'
            elif 'implementations/' in str(path):
                return 'technical_implementations'
            return 'technical_general'
            
        elif 'elder_council/' in str(path):
            if not ('decisions/' in str(path)):
                continue  # Early return to reduce nesting
            # Reduced nesting - original condition satisfied
            if 'decisions/' in str(path):
                return 'elder_council_decisions'
            elif 'reports/' in str(path):
                return 'elder_council_reports'
            return 'elder_council_general'
            
        elif 'projects/' in str(path):
            return 'project_management'
            
        else:
            return 'miscellaneous'
            
    def chunk_content(self, content: str, max_tokens: int = CHUNK_SIZE) -> List[str]:
        """コンテンツをチャンクに分割"""
        tokens = self.tokenizer.encode(content)
        chunks = []
        
        for i in range(0, len(tokens), max_tokens - OVERLAP_SIZE):
            chunk_tokens = tokens[i:i + max_tokens]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)
            
        return chunks
        
    async def process_file(self, filepath: str) -> List[Dict[str, Any]]:
        """単一ファイルの処理"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if len(content.strip()) < 50:  # 最小長チェック
                logger.warning(f"ファイルが短すぎます: {filepath}")
                return []
                
            # メタデータ生成
            relative_path = os.path.relpath(filepath, KNOWLEDGE_BASE_PATH)
            file_hash = hashlib.sha256(content.encode()).hexdigest()
            priority = self.get_file_priority(filepath)
            category = self.categorize_file(filepath)
            
            # チャンク分割
            chunks = self.chunk_content(content)
            
            processed_chunks = []
            for i, chunk in enumerate(chunks):
                # 埋め込みベクトル生成
                embedding = self.model.encode(chunk)
                
                chunk_data = {
                    'title': Path(filepath).stem,
                    'content': chunk,
                    'source_file': relative_path,
                    'file_hash': file_hash,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'category': category,
                    'priority': priority,
                    'file_size': len(content),
                    'embedding': embedding.tolist(),
                    'metadata': {
                        'processed_at': datetime.now().isoformat(),
                        'model_version': MODEL_NAME,
                        'chunk_size': len(chunk),
                        'directory': str(Path(relative_path).parent)
                    }
                }
                processed_chunks.append(chunk_data)
                
            logger.info(f"ファイル処理完了: {relative_path} ({len(chunks)}チャンク)")
            return processed_chunks
            
        except Exception as e:
            logger.error(f"ファイル処理エラー {filepath}: {e}")
            return []
            
    async def insert_chunks_batch(self, chunks: List[Dict[str, Any]]):
        """チャンクのバッチ挿入"""
        if not chunks:
            return
            
        async with self.db_pool.acquire() as conn:
            insert_query = """
                INSERT INTO knowledge_documents (
                    title, content, source_file, file_hash, chunk_index, total_chunks,
                    category, priority, file_size, embedding, metadata, sage_type
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """
            
            batch_data = []
            for chunk in chunks:
                batch_data.append([
                    chunk['title'],
                    chunk['content'],
                    chunk['source_file'],
                    chunk['file_hash'],
                    chunk['chunk_index'],
                    chunk['total_chunks'],
                    chunk['category'],
                    chunk['priority'],
                    chunk['file_size'],
                    chunk['embedding'],
                    json.dumps(chunk['metadata']),
                    'knowledge_sage'  # デフォルト賢者
                ])
                
            await conn.executemany(insert_query, batch_data)
            logger.info(f"バッチ挿入完了: {len(chunks)}チャンク")
            
    async def get_markdown_files(self) -> List[str]:
        """全markdownファイルの取得（優先順位順）"""
        files = []
        # 繰り返し処理
        for root, dirs, filenames in os.walk(KNOWLEDGE_BASE_PATH):
            for filename in filenames:
                if filename.endswith('.md'):
                    filepath = os.path.join(root, filename)
                    files.append(filepath)
                    
        # 優先順位でソート
        files.sort(key=self.get_file_priority)
        return files
        
    async def reconstruct_knowledge_base(self):
        """ナレッジベース完全再構築"""
        logger.info("pgvectorナレッジベース完全再構築開始")
        
        # 初期化
        await self.initialize()
        
        # 既存データクリーンアップ
        await self.cleanup_existing_data()
        
        # ファイル一覧取得
        markdown_files = await self.get_markdown_files()
        logger.info(f"処理対象ファイル数: {len(markdown_files)}")
        
        # カテゴリ別統計
        category_stats = {}
        priority_stats = {}
        
        # バッチ処理
        batch_chunks = []
        processed_files = 0
        
        for filepath in markdown_files:
            try:
                chunks = await self.process_file(filepath)
                batch_chunks.extend(chunks)
                processed_files += 1
                
                # 統計更新
                if chunks:
                    category = chunks[0]['category']
                    priority = chunks[0]['priority']
                    category_stats[category] = category_stats.get(category, 0) + 1
                    priority_stats[priority] = priority_stats.get(priority, 0) + 1
                
                # バッチサイズに達したら挿入
                if len(batch_chunks) >= BATCH_SIZE * 10:  # チャンク単位でのバッチ
                    await self.insert_chunks_batch(batch_chunks)
                    batch_chunks = []
                    
                # 進捗表示
                if processed_files % 20 == 0:
                    logger.info(f"進捗: {processed_files}/{len(markdown_files)} ファイル処理完了")
                    
            except Exception as e:
                logger.error(f"ファイル処理スキップ {filepath}: {e}")
                continue
                
        # 残りのチャンクを挿入
        if batch_chunks:
            await self.insert_chunks_batch(batch_chunks)
            
        # 統計情報出力
        logger.info("=== 再構築完了統計 ===")
        logger.info(f"処理ファイル数: {processed_files}")
        logger.info(f"カテゴリ別: {category_stats}")
        logger.info(f"優先度別: {priority_stats}")
        
        # 最終データベース統計
        async with self.db_pool.acquire() as conn:
            total_chunks = await conn.fetchval("SELECT COUNT(*) FROM knowledge_documents")
            logger.info(f"総チャンク数: {total_chunks}")
            
            # インデックス最適化
            await conn.execute("REINDEX TABLE knowledge_documents")
            await conn.execute("ANALYZE knowledge_documents")
            logger.info("インデックス最適化完了")
            
        logger.info("pgvectorナレッジベース完全再構築完了!")
        
    async def close(self):
        """リソースクリーンアップ"""
        if self.db_pool:
            await self.db_pool.close()

async def main():
    """メイン実行関数"""
    reconstructor = PgVectorKnowledgeReconstructor()
    
    try:
        await reconstructor.reconstruct_knowledge_base()
    except Exception as e:
        logger.error(f"再構築エラー: {e}")
        sys.exit(1)
    finally:
        await reconstructor.close()

if __name__ == "__main__":
    asyncio.run(main())