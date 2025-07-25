#!/usr/bin/env python3
"""
pgvector Knowledge Base 簡易再構築システム
既存ライブラリを使用した軽量版
"""

import os
import sys
import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import asyncio
import asyncpg

# 既存システムインポート
sys.path.append('/home/aicompany/ai_co')
from libs.enhanced_rag_manager import EnhancedRAGManager
from libs.four_sages_postgres_mcp_integration import PostgreSQLMCPIntegration

# 設定
DATABASE_URL = "postgresql://aicompany:secret123@localhost:5432/elders_guild_pgvector"
KNOWLEDGE_BASE_PATH = "/home/aicompany/ai_co/knowledge_base"

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleKnowledgeReconstructor:
    """SimpleKnowledgeReconstructorクラス"""
    def __init__(self):
        """初期化メソッド"""
        self.rag_manager = None
        self.db_integration = None
        
    async def initialize(self):
        """既存システム初期化"""
        logger.info("簡易再構築システム初期化")
        
        try:
            # RAGマネージャー初期化
            self.rag_manager = EnhancedRAGManager()
            await self.rag_manager.initialize()
            
            # PostgreSQL MCP統合初期化
            self.db_integration = PostgreSQLMCPIntegration()
            await self.db_integration.initialize()
            
            logger.info("既存システム初期化完了")
        except Exception as e:
            logger.error(f"初期化エラー: {e}")
            raise
            
    async def backup_and_clear(self):
        """データバックアップとクリア"""
        logger.info("データバックアップとクリア開始")
        
        try:
            # PostgreSQL接続
            conn = await asyncpg.connect(DATABASE_URL)
            
            # バックアップ作成
            backup_table = f"knowledge_documents_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            await conn.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM knowledge_documents")
            
            # 既存データ数確認
            count = await conn.fetchval("SELECT COUNT(*) FROM knowledge_documents")
            logger.info(f"バックアップ作成: {backup_table} ({count}件)")
            
            # データクリア
            await conn.execute("TRUNCATE TABLE knowledge_documents RESTART IDENTITY CASCADE")
            logger.info("既存データクリア完了")
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"バックアップ・クリアエラー: {e}")
            raise
            
    def get_file_priority(self, filepath: str) -> int:
        """ファイル優先度判定"""
        path_str = str(filepath).lower()
        
        # 超高優先度 - マスター文書
        if any(x in path_str for x in ['master_kb', 'elder_identity', 'elder_knowledge_minimal']):
            return 1
            
        # 高優先度 - コア知識
        if any(x in path_str for x in ['core/', 'four_sages/', 'protocols/']):
            return 2
            
        # 中優先度 - 技術・決定
        if any(x in path_str for x in ['technical/', 'decisions/', 'guides/']):
            return 3
            
        # 低優先度 - その他
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
            
    async def process_markdown_files(self) -> Dict[str, Any]:
        """マークダウンファイル処理"""
        logger.info("マークダウンファイル処理開始")
        
        # ファイル一覧取得
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
        
        # バッチ処理
        for i, filepath in enumerate(markdown_files):
            try:
                # ファイル読み込み
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if len(content.strip()) < 50:
                    stats['skipped_files'] += 1
                    continue
                    
                # メタデータ生成
                relative_path = os.path.relpath(filepath, KNOWLEDGE_BASE_PATH)
                priority = self.get_file_priority(filepath)
                category = self.categorize_file(filepath)
                
                # 統計更新
                stats['categories'][category] = stats['categories'].get(category, 0) + 1
                stats['priorities'][priority] = stats['priorities'].get(priority, 0) + 1
                
                # RAGマネージャーでドキュメント追加
                await self.rag_manager.add_document(
                    content=content,
                    title=Path(filepath).stem,
                    source=relative_path,
                    metadata={
                        'category': category,
                        'priority': priority,
                        'file_size': len(content),
                        'processed_at': datetime.now().isoformat(),
                        'directory': str(Path(relative_path).parent)
                    }
                )
                
                stats['processed_files'] += 1
                stats['total_chunks'] += 1  # RAGマネージャーが内部でチャンク処理
                
                # 進捗表示
                if (i + 1) % 20 == 0:
                    logger.info(f"進捗: {i + 1}/{len(markdown_files)} ファイル処理")
                    
            except Exception as e:
                logger.error(f"ファイル処理エラー {filepath}: {e}")
                stats['skipped_files'] += 1
                continue
                
        return stats
        
    async def optimize_database(self):
        """データベース最適化"""
        logger.info("データベース最適化開始")
        
        try:
            conn = await asyncpg.connect(DATABASE_URL)
            
            # 統計更新
            await conn.execute("ANALYZE knowledge_documents")
            
            # インデックス再構築
            await conn.execute("REINDEX TABLE knowledge_documents")
            
            # 最終統計
            total_docs = await conn.fetchval("SELECT COUNT(*) FROM knowledge_documents")
            unique_sources = await conn.fetchval("SELECT COUNT(DISTINCT source_file) FROM knowledge_documents" \
                "SELECT COUNT(DISTINCT source_file) FROM knowledge_documents")
            
            logger.info(f"最適化完了 - 総ドキュメント: {total_docs}, ユニークソース: {unique_sources}")
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"最適化エラー: {e}")
            
    async def reconstruct(self):
        """メイン再構築処理"""
        logger.info("=== pgvector知識ベース再構築開始 ===")
        
        try:
            # 初期化
            await self.initialize()
            
            # バックアップ・クリア
            await self.backup_and_clear()
            
            # ファイル処理
            stats = await self.process_markdown_files()
            
            # 最適化
            await self.optimize_database()
            
            # 結果出力
            logger.info("=== 再構築完了統計 ===")
            logger.info(f"総ファイル数: {stats['total_files']}")
            logger.info(f"処理成功: {stats['processed_files']}")
            logger.info(f"スキップ: {stats['skipped_files']}")
            logger.info(f"カテゴリ別: {stats['categories']}")
            logger.info(f"優先度別: {stats['priorities']}")
            
            logger.info("=== pgvector知識ベース再構築完了 ===")
            
        except Exception as e:
            logger.error(f"再構築失敗: {e}")
            raise
            
    async def close(self):
        """リソース解放"""
        if self.rag_manager:
            await self.rag_manager.close()
        if self.db_integration:
            await self.db_integration.close()

async def main():
    """メイン実行"""
    reconstructor = SimpleKnowledgeReconstructor()
    
    try:
        await reconstructor.reconstruct()
    except Exception as e:
        logger.error(f"実行エラー: {e}")
        sys.exit(1)
    finally:
        await reconstructor.close()

if __name__ == "__main__":
    asyncio.run(main())