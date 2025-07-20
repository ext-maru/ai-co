#!/usr/bin/env python3
"""
pgvector ベクトル検索機能
384次元ベクトルを使用した類似性検索
"""

import subprocess
import logging
import json
from typing import List, Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class PgVectorSearch:
    """pgvector ベクトル検索クラス"""
    
    def __init__(self):
        self.config = {
            'postgres': {
                'host': 'localhost',
                'port': 8003,
                'database': 'elders_guild_pgvector',
                'user': 'admin'
            },
            'docker_command_prefix': ['sg', 'docker', '-c']
        }
    
    def generate_query_vector(self, query: str) -> List[float]:
        """クエリ文字列からベクトル生成"""
        if not query:
            return [0.0] * 384
        
        # 文字頻度ベースの簡易ベクトル
        vector = [0.0] * 384
        text_clean = query.lower()[:384]
        for i, char in enumerate(text_clean):
            vector[i] = ord(char) / 255.0
            
        # 正規化
        norm = sum(x*x for x in vector) ** 0.5
        if norm > 0:
            vector = [x/norm for x in vector]
            
        return vector
    
    def vector_to_pg_format(self, vector: List[float]) -> str:
        """ベクトルをPostgreSQL形式に変換"""
        return '[' + ','.join(f'{v:.6f}' for v in vector) + ']'
    
    def similarity_search(self, query: str, limit: int = 10, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """ベクトル類似性検索"""
        logger.info(f"🔍 ベクトル検索: '{query}' (limit: {limit}, threshold: {threshold})")
        
        try:
            # クエリベクトル生成
            query_vector = self.generate_query_vector(query)
            query_vector_str = self.vector_to_pg_format(query_vector)
            
            # 類似性検索SQL
            search_sql = f"""
            SELECT 
                title, content, source_file, category, priority,
                (embedding <=> '{query_vector_str}') as distance,
                (1 - (embedding <=> '{query_vector_str}')) as similarity
            FROM knowledge_documents 
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> '{query_vector_str}'
            LIMIT {limit};
            """
            
            cmd = self.config['docker_command_prefix'] + [
                f"docker exec elders-guild-postgres-new psql -U {self.config['postgres']['user']} "
                f"-d {self.config['postgres']['database']} -t -c \"{search_sql}\""
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                results = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip() and '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 7:
                            try:
                                distance = float(parts[5].strip())
                                similarity = float(parts[6].strip())
                                
                                # 閾値チェック
                                if similarity >= threshold:
                                    results.append({
                                        'title': parts[0].strip(),
                                        'content': parts[1].strip()[:500],
                                        'source_file': parts[2].strip(),
                                        'category': parts[3].strip(),
                                        'priority': int(parts[4].strip()) if parts[4].strip().isdigit() else 4,
                                        'distance': distance,
                                        'similarity': similarity,
                                        'search_type': 'vector_similarity',
                                        'source': 'postgresql'
                                    })
                            except (ValueError, IndexError) as e:
                                logger.warning(f"⚠️ ベクトル検索結果パースエラー: {e}")
                                continue
                
                logger.info(f"✅ ベクトル検索成功: {len(results)}件")
                return results
            else:
                logger.warning(f"⚠️ ベクトル検索SQL実行失敗: {result.stderr}")
                return []
                
        except Exception as e:
            logger.error(f"❌ ベクトル検索エラー: {e}")
            return []
    
    def hybrid_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """ハイブリッド検索（テキスト + ベクトル）"""
        logger.info(f"🔍 ハイブリッド検索: '{query}' (limit: {limit})")
        
        try:
            # テキスト検索
            text_results = self.text_search(query, limit // 2)
            
            # ベクトル検索
            vector_results = self.similarity_search(query, limit // 2, threshold=0.3)
            
            # 結果統合（重複除去）
            seen_files = set()
            combined_results = []
            
            # ベクトル検索結果を優先
            for result in vector_results:
                if result['source_file'] not in seen_files:
                    seen_files.add(result['source_file'])
                    result['search_method'] = 'vector_primary'
                    combined_results.append(result)
            
            # テキスト検索結果を追加
            for result in text_results:
                if result['source_file'] not in seen_files and len(combined_results) < limit:
                    seen_files.add(result['source_file'])
                    result['search_method'] = 'text_fallback'
                    combined_results.append(result)
            
            logger.info(f"✅ ハイブリッド検索完了: {len(combined_results)}件")
            return combined_results[:limit]
            
        except Exception as e:
            logger.error(f"❌ ハイブリッド検索エラー: {e}")
            return []
    
    def text_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """テキスト検索（フォールバック用）"""
        try:
            search_sql = f"""
            SELECT title, content, source_file, category, priority
            FROM knowledge_documents 
            WHERE content ILIKE '%{query}%' OR title ILIKE '%{query}%'
            ORDER BY priority ASC, created_at DESC
            LIMIT {limit};
            """
            
            cmd = self.config['docker_command_prefix'] + [
                f"docker exec elders-guild-postgres-new psql -U {self.config['postgres']['user']} "
                f"-d {self.config['postgres']['database']} -t -c \"{search_sql}\""
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
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
                                    'search_type': 'text_match',
                                    'source': 'postgresql'
                                })
                            except (ValueError, IndexError):
                                continue
                return results
            return []
            
        except Exception as e:
            logger.error(f"❌ テキスト検索エラー: {e}")
            return []
    
    def get_vector_stats(self) -> Dict[str, Any]:
        """ベクトルデータ統計情報取得"""
        try:
            stats_sql = """
            SELECT 
                COUNT(*) as total_documents,
                COUNT(embedding) as documents_with_vectors,
                AVG(CASE WHEN embedding IS NOT NULL THEN 1 ELSE 0 END) as vector_coverage
            FROM knowledge_documents;
            """
            
            cmd = self.config['docker_command_prefix'] + [
                f"docker exec elders-guild-postgres-new psql -U {self.config['postgres']['user']} "
                f"-d {self.config['postgres']['database']} -t -c \"{stats_sql}\""
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                line = result.stdout.strip()
                parts = line.split('|')
                if len(parts) >= 3:
                    return {
                        'total_documents': int(parts[0].strip()),
                        'documents_with_vectors': int(parts[1].strip()),
                        'vector_coverage': float(parts[2].strip()),
                        'timestamp': datetime.now().isoformat()
                    }
            
            return {
                'total_documents': 0,
                'documents_with_vectors': 0,
                'vector_coverage': 0.0,
                'error': 'データ取得失敗',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ ベクトル統計取得エラー: {e}")
            return {
                'total_documents': 0,
                'documents_with_vectors': 0,
                'vector_coverage': 0.0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

def main():
    """CLI テスト"""
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python3 pgvector_search.py search <query>")
        print("  python3 pgvector_search.py vector <query>")
        print("  python3 pgvector_search.py hybrid <query>")
        print("  python3 pgvector_search.py stats")
        return 1
    
    search = PgVectorSearch()
    command = sys.argv[1]
    
    if command == 'search' and len(sys.argv) > 2:
        query = ' '.join(sys.argv[2:])
        results = search.text_search(query)
        print(json.dumps(results, indent=2, ensure_ascii=False))
        
    elif command == 'vector' and len(sys.argv) > 2:
        query = ' '.join(sys.argv[2:])
        results = search.similarity_search(query)
        print(json.dumps(results, indent=2, ensure_ascii=False))
        
    elif command == 'hybrid' and len(sys.argv) > 2:
        query = ' '.join(sys.argv[2:])
        results = search.hybrid_search(query)
        print(json.dumps(results, indent=2, ensure_ascii=False))
        
    elif command == 'stats':
        stats = search.get_vector_stats()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        
    else:
        print("不明なコマンドまたは引数不足")
        return 1
    
    return 0

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    exit(main())