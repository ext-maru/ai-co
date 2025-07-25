#!/usr/bin/env python3
"""
pgvector簡易マイグレーター
文字エスケープ問題を回避した簡潔な実装
"""

import sqlite3
import json

import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class SimplePgVectorMigrator:
    """シンプルなpgvectorマイグレーター"""
    
    def __init__(self):
        """初期化メソッド"""
        self.sqlite_db = '/home/aicompany/ai_co/knowledge_base/integrated_knowledge.db'
        self.postgres_config = {
            'host': 'localhost',
            'port': 8003,
            'database': 'elders_guild_pgvector',
            'user': 'admin'
        }
        
    def migrate_data(self) -> Dict[str, Any]:
        """データマイグレーション実行"""
        logger.info("🔄 簡易マイグレーション開始")
        
        try:
            # SQLiteからデータ読み込み
            conn = sqlite3connect(self.sqlite_db)
            conn.row_factory = sqlite3Row
            cursor = conn.execute("SELECT COUNT(*) FROM knowledge_documents")
            total_count = cursor.fetchone()[0]
            
            logger.info(f"📊 ソースレコード数: {total_count}")
            
            # 小バッチで処理
            migrated_count = 0
            batch_size = 5
            
            for offset in range(0, total_count, batch_size):  # 全件処理
                batch = self._get_batch(conn, batch_size, offset)
                if not batch:
                    break
                    
                success = self._migrate_batch_simple(batch)
                if success:
                    migrated_count += len(batch)
                    logger.info(f"📈 マイグレーション進捗: {migrated_count}件")
                else:
                    logger.warning(f"⚠️ バッチ{offset}~{offset+batch_size}失敗")
                    
            conn.close()
            
            return {
                'status': 'success',
                'total_records': total_count,
                'migrated_records': migrated_count,
                'success_rate': migrated_count / total_count if total_count > 0 else 0,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ マイグレーションエラー: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_batch(self, conn, batch_size: int, offset: int) -> List[Dict]:
        """バッチデータ取得"""
        cursor = conn.execute(
            "SELECT title, content, source_file, category, priority "
            "FROM knowledge_documents ORDER BY priority LIMIT ? OFFSET ?",
            [batch_size, offset]
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def _migrate_batch_simple(self, batch: List[Dict]) -> bool:
        """簡潔なバッチマイグレーション"""
        try:
            # 一時ファイルでSQLスクリプト作成

                for row in batch:
                    # 安全な値の準備
                    title = self._safe_text(row['title'])[:100]
                    content = self._safe_text(row['content'])[:1000]
                    source_file = self._safe_text(row['source_file'])
                    category = self._safe_text(row['category'])
                    priority = int(row.get('priority', 5))
                    
                    # 簡易ベクトル（少数の次元）
                    vector = self._generate_simple_vector(content)
                    
                    # ハッシュとファイルサイズを計算
                    file_hash = f"hash_{hash(content) % 1000000}"
                    file_size = len(content)
                    
                    # 安全なSQL
                    sql = f"""
INSERT INTO knowledge_documents (
    title, content, source_file, file_hash, category, priority, 
    file_size, embedding, sage_type, created_at
) VALUES (
    '{title}', 
    '{content}', 
    '{source_file}', 
    '{file_hash}',
    '{category}', 
    {priority}, 
    {file_size},
    '{vector}', 
    'knowledge_sage', 
    NOW()
);
"""
                    f.write(sql)
                
                sql_file = f.name
            
            # PostgreSQLでSQL実行
            cmd = [
                'sg', 'docker', '-c',
                (
                    f"f'docker exec -i elders-guild-postgres-new psql -U admin -d "
                    f"{self.postgres_config["database"]} < {sql_file}'"
                )
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # 一時ファイル削除
            Path(sql_file).unlink()
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"❌ バッチ処理エラー: {e}")
            return False
    
    def _safe_text(self, text: str) -> str:
        """安全なテキスト変換"""
        if not text:
            return ''
        # SQLインジェクション対策
        return text.replace("'", "''").replace("\n", " ").replace("\r", "")[:500]
    
    def _generate_simple_vector(self, text: str) -> str:
        """簡易ベクトル生成（384次元）"""
        if not text:
            return '[' + ','.join(['0'] * 384) + ']'
        
        # 文字頻度ベースの簡易ベクトル
        vector = [0.0] * 384
        text_clean = text.lower()[:384]
        for i, char in enumerate(text_clean):
            vector[i] = ord(char) / 255.0
            
        # 正規化
        norm = sum(x*x for x in vector) ** 0.5
        if norm > 0:
            vector = [x/norm for x in vector]
            
        # JSON形式で返却
        return '[' + ','.join(f'{v:0.6f}' for v in vector) + ']'

def main():
    """メイン実行"""
    logging.basicConfig(level=logging.INFO)
    
    migrator = SimplePgVectorMigrator()
    result = migrator.migrate_data()
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result['status'] == 'success':
        print(f"\n✅ マイグレーション成功: {result['migrated_records']}件")
        return 0
    else:
        print(f"\n❌ マイグレーション失敗: {result.get('error', 'Unknown error')}")
        return 1

if __name__ == "__main__":
    exit(main())