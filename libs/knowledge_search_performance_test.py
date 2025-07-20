#!/usr/bin/env python3
"""
Knowledge Base 検索性能テストシステム
"""

import os
import time
import sqlite3
import logging
from typing import List, Dict, Any

# 設定
SQLITE_DB_PATH = "/home/aicompany/ai_co/knowledge_base/integrated_knowledge.db"

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SearchPerformanceTester:
    def __init__(self):
        self.db_conn = None
        
    def connect_db(self):
        """データベース接続"""
        self.db_conn = sqlite3.connect(SQLITE_DB_PATH)
        self.db_conn.row_factory = sqlite3.Row
        
    def test_basic_queries(self) -> Dict[str, float]:
        """基本クエリ性能テスト"""
        logger.info("基本クエリ性能テスト開始")
        
        test_queries = {
            'count_all': "SELECT COUNT(*) FROM knowledge_documents",
            'count_by_category': "SELECT category, COUNT(*) FROM knowledge_documents GROUP BY category",
            'count_by_priority': "SELECT priority, COUNT(*) FROM knowledge_documents GROUP BY priority",
            'high_priority': "SELECT * FROM knowledge_documents WHERE priority <= 2 LIMIT 10",
            'large_files': "SELECT source_file, file_size FROM knowledge_documents WHERE file_size > 10000 LIMIT 10"
        }
        
        results = {}
        
        for test_name, query in test_queries.items():
            start_time = time.time()
            cursor = self.db_conn.execute(query)
            rows = cursor.fetchall()
            end_time = time.time()
            
            execution_time = end_time - start_time
            results[test_name] = execution_time
            
            logger.info(f"{test_name}: {execution_time:.4f}秒 ({len(rows)}件)")
            
        return results
        
    def test_full_text_search(self) -> Dict[str, float]:
        """全文検索性能テスト"""
        logger.info("全文検索性能テスト開始")
        
        search_terms = [
            'elder',
            'claude',
            'pgvector',
            'four sages',
            'technical',
            'protocol',
            'implementation',
            'system',
            'knowledge',
            'database'
        ]
        
        results = {}
        
        for term in search_terms:
            # FTS検索
            start_time = time.time()
            cursor = self.db_conn.execute(
                "SELECT * FROM knowledge_fts WHERE knowledge_fts MATCH ? LIMIT 10",
                [term]
            )
            fts_rows = cursor.fetchall()
            fts_time = time.time() - start_time
            
            # LIKE検索（比較用）
            start_time = time.time()
            cursor = self.db_conn.execute(
                "SELECT * FROM knowledge_documents WHERE content LIKE ? LIMIT 10",
                [f'%{term}%']
            )
            like_rows = cursor.fetchall()
            like_time = time.time() - start_time
            
            results[f'fts_{term}'] = fts_time
            results[f'like_{term}'] = like_time
            
            logger.info(f"'{term}' - FTS: {fts_time:.4f}秒 ({len(fts_rows)}件), LIKE: {like_time:.4f}秒 ({len(like_rows)}件)")
            
        return results
        
    def test_complex_queries(self) -> Dict[str, float]:
        """複合クエリ性能テスト"""
        logger.info("複合クエリ性能テスト開始")
        
        complex_queries = {
            'category_priority': """
                SELECT category, priority, COUNT(*), AVG(file_size)
                FROM knowledge_documents 
                GROUP BY category, priority 
                ORDER BY category, priority
            """,
            'large_core_files': """
                SELECT source_file, file_size, category
                FROM knowledge_documents 
                WHERE category LIKE 'core_%' AND file_size > 5000
                ORDER BY file_size DESC
            """,
            'four_sages_content': """
                SELECT title, source_file, LENGTH(content) as content_length
                FROM knowledge_documents 
                WHERE category = 'four_sages_system'
                ORDER BY content_length DESC
                LIMIT 10
            """,
            'technical_summary': """
                SELECT 
                    category,
                    COUNT(*) as doc_count,
                    AVG(file_size) as avg_size,
                    MAX(file_size) as max_size,
                    MIN(file_size) as min_size
                FROM knowledge_documents 
                WHERE category LIKE 'technical_%'
                GROUP BY category
            """
        }
        
        results = {}
        
        for test_name, query in complex_queries.items():
            start_time = time.time()
            cursor = self.db_conn.execute(query)
            rows = cursor.fetchall()
            end_time = time.time()
            
            execution_time = end_time - start_time
            results[test_name] = execution_time
            
            logger.info(f"{test_name}: {execution_time:.4f}秒 ({len(rows)}件)")
            
        return results
        
    def analyze_database_structure(self) -> Dict[str, Any]:
        """データベース構造分析"""
        logger.info("データベース構造分析開始")
        
        # テーブル情報
        cursor = self.db_conn.execute("PRAGMA table_info(knowledge_documents)")
        table_info = cursor.fetchall()
        
        # インデックス情報
        cursor = self.db_conn.execute("PRAGMA index_list(knowledge_documents)")
        index_list = cursor.fetchall()
        
        # データベースサイズ
        db_size = os.path.getsize(SQLITE_DB_PATH)
        
        # 統計情報
        cursor = self.db_conn.execute("SELECT COUNT(*) FROM knowledge_documents")
        total_docs = cursor.fetchone()[0]
        
        cursor = self.db_conn.execute("SELECT COUNT(DISTINCT source_file) FROM knowledge_documents")
        unique_files = cursor.fetchone()[0]
        
        cursor = self.db_conn.execute("SELECT AVG(LENGTH(content)) FROM knowledge_documents")
        avg_content_length = cursor.fetchone()[0]
        
        return {
            'table_columns': len(table_info),
            'indexes': len(index_list),
            'database_size_mb': db_size / (1024 * 1024),
            'total_documents': total_docs,
            'unique_files': unique_files,
            'avg_content_length': avg_content_length,
            'docs_per_file': total_docs / unique_files if unique_files > 0 else 0
        }
        
    def generate_performance_report(self) -> Dict[str, Any]:
        """性能レポート生成"""
        logger.info("=== 検索性能総合テスト開始 ===")
        
        try:
            self.connect_db()
            
            # 各テスト実行
            basic_results = self.test_basic_queries()
            fts_results = self.test_full_text_search()
            complex_results = self.test_complex_queries()
            structure_info = self.analyze_database_structure()
            
            # 性能分析
            fts_avg = sum(v for k, v in fts_results.items() if k.startswith('fts_')) / len([k for k in fts_results.keys() if k.startswith('fts_')])
            like_avg = sum(v for k, v in fts_results.items() if k.startswith('like_')) / len([k for k in fts_results.keys() if k.startswith('like_')])
            
            report = {
                'test_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'database_structure': structure_info,
                'basic_query_performance': basic_results,
                'full_text_search_performance': fts_results,
                'complex_query_performance': complex_results,
                'performance_summary': {
                    'fts_avg_time': fts_avg,
                    'like_avg_time': like_avg,
                    'fts_speedup': like_avg / fts_avg if fts_avg > 0 else 0,
                    'basic_avg_time': sum(basic_results.values()) / len(basic_results),
                    'complex_avg_time': sum(complex_results.values()) / len(complex_results)
                },
                'recommendations': self.generate_recommendations(basic_results, fts_results, complex_results, structure_info)
            }
            
            logger.info("=== 検索性能総合テスト完了 ===")
            return report
            
        except Exception as e:
            logger.error(f"性能テストエラー: {e}")
            raise
        finally:
            if self.db_conn:
                self.db_conn.close()
                
    def generate_recommendations(self, basic: Dict, fts: Dict, complex: Dict, structure: Dict) -> List[str]:
        """最適化推奨事項生成"""
        recommendations = []
        
        # FTS性能チェック
        fts_avg = sum(v for k, v in fts.items() if k.startswith('fts_')) / len([k for k in fts.keys() if k.startswith('fts_')])
        if fts_avg > 0.1:
            recommendations.append("FTS検索が遅い可能性があります。インデックス再構築を検討してください。")
            
        # 複合クエリ性能チェック
        complex_avg = sum(complex.values()) / len(complex)
        if complex_avg > 0.5:
            recommendations.append("複合クエリが遅い可能性があります。追加インデックスを検討してください。")
            
        # データベースサイズチェック
        if structure['database_size_mb'] > 100:
            recommendations.append("データベースサイズが大きいです。定期的なVACUUMを検討してください。")
            
        # ドキュメント密度チェック
        if structure['docs_per_file'] > 5:
            recommendations.append("ファイルあたりのチャンク数が多いです。チャンクサイズ調整を検討してください。")
            
        if not recommendations:
            recommendations.append("現在の性能は良好です。")
            
        return recommendations

def main():
    """メイン実行"""
    tester = SearchPerformanceTester()
    
    try:
        report = tester.generate_performance_report()
        
        # レポート出力
        print("\n=== 検索性能テスト結果 ===")
        print(f"テスト日時: {report['test_timestamp']}")
        print(f"データベースサイズ: {report['database_structure']['database_size_mb']:.2f}MB")
        print(f"総ドキュメント数: {report['database_structure']['total_documents']}")
        print(f"ユニークファイル数: {report['database_structure']['unique_files']}")
        
        print("\n--- 性能サマリー ---")
        summary = report['performance_summary']
        print(f"FTS平均時間: {summary['fts_avg_time']:.4f}秒")
        print(f"LIKE平均時間: {summary['like_avg_time']:.4f}秒")
        print(f"FTS高速化倍率: {summary['fts_speedup']:.2f}倍")
        print(f"基本クエリ平均: {summary['basic_avg_time']:.4f}秒")
        print(f"複合クエリ平均: {summary['complex_avg_time']:.4f}秒")
        
        print("\n--- 推奨事項 ---")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. {rec}")
            
        # JSONレポート保存
        import json
        report_path = f"/home/aicompany/ai_co/knowledge_base/performance_test_report_{int(time.time())}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n詳細レポート保存: {report_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"テスト実行エラー: {e}")
        return 1

if __name__ == "__main__":
    exit(main())