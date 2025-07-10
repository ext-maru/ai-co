#!/usr/bin/env python3
"""
Database Optimizer - データベース最適化ツール
エルダーズギルドのSQLiteデータベース最適化とメンテナンス

🗄️ 最適化項目:
- VACUUM実行（断片化解消）
- インデックス再構築
- 古いデータアーカイブ
- 統計情報更新
- データベースサイズ最適化
"""

import os
import sys
import sqlite3
import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

class DatabaseOptimizer:
    """データベース最適化クラス"""
    
    def __init__(self, project_dir: str = "/home/aicompany/ai_co"):
        self.project_dir = Path(project_dir)
        self.logs_dir = self.project_dir / "logs"
        
        # ログ設定
        self.setup_logging()
        
    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.logs_dir / 'database_optimizer.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def find_databases(self) -> List[Path]:
        """データベースファイルの検出"""
        self.logger.info("🔍 データベースファイル検出開始")
        
        db_patterns = ["*.db", "*.sqlite", "*.sqlite3"]
        databases = []
        
        for pattern in db_patterns:
            databases.extend(self.project_dir.rglob(pattern))
        
        # 重複除去とソート
        databases = sorted(list(set(databases)))
        
        self.logger.info(f"🔍 検出完了: {len(databases)}個のデータベース")
        for db in databases:
            size_kb = db.stat().st_size / 1024
            self.logger.debug(f"  {db.name}: {size_kb:.1f} KB")
        
        return databases
    
    def analyze_database(self, db_path: Path) -> Dict[str, Any]:
        """データベース分析"""
        self.logger.info(f"📊 データベース分析: {db_path.name}")
        
        analysis = {
            "path": str(db_path),
            "size_kb": db_path.stat().st_size / 1024,
            "tables": [],
            "indexes": [],
            "total_rows": 0,
            "page_count": 0,
            "page_size": 0,
            "fragmentation_percent": 0,
            "error": None
        }
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # テーブル情報取得
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            table_names = [row[0] for row in cursor.fetchall()]
            
            for table_name in table_names:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    analysis["tables"].append({
                        "name": table_name,
                        "rows": row_count
                    })
                    analysis["total_rows"] += row_count
                except Exception as e:
                    self.logger.warning(f"テーブル {table_name} 分析エラー: {e}")
            
            # インデックス情報取得
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            index_names = [row[0] for row in cursor.fetchall() if row[0]]
            analysis["indexes"] = index_names
            
            # ページ情報取得
            try:
                cursor.execute("PRAGMA page_count")
                analysis["page_count"] = cursor.fetchone()[0]
                
                cursor.execute("PRAGMA page_size")
                analysis["page_size"] = cursor.fetchone()[0]
                
                cursor.execute("PRAGMA freelist_count")
                free_pages = cursor.fetchone()[0]
                
                if analysis["page_count"] > 0:
                    analysis["fragmentation_percent"] = (free_pages / analysis["page_count"]) * 100
            except Exception as e:
                self.logger.debug(f"ページ情報取得エラー: {e}")
            
            conn.close()
            
        except Exception as e:
            analysis["error"] = str(e)
            self.logger.error(f"データベース分析エラー {db_path}: {e}")
        
        self.logger.info(f"📊 分析完了: {analysis['total_rows']}行, {len(analysis['tables'])}テーブル")
        return analysis
    
    def optimize_database(self, db_path: Path) -> Dict[str, Any]:
        """データベース最適化実行"""
        self.logger.info(f"⚡ データベース最適化: {db_path.name}")
        
        result = {
            "database": str(db_path),
            "size_before_kb": db_path.stat().st_size / 1024,
            "size_after_kb": 0,
            "space_saved_kb": 0,
            "vacuum_executed": False,
            "reindex_executed": False,
            "analyze_executed": False,
            "backup_created": False,
            "error": None
        }
        
        try:
            # バックアップ作成
            backup_path = db_path.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
            shutil.copy2(db_path, backup_path)
            result["backup_created"] = True
            self.logger.info(f"💾 バックアップ作成: {backup_path.name}")
            
            # データベース接続
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # VACUUM実行（断片化解消）
            self.logger.info("🧹 VACUUM実行中...")
            cursor.execute("VACUUM")
            result["vacuum_executed"] = True
            
            # インデックス再構築
            self.logger.info("📇 インデックス再構築中...")
            cursor.execute("REINDEX")
            result["reindex_executed"] = True
            
            # 統計情報更新
            self.logger.info("📈 統計情報更新中...")
            cursor.execute("ANALYZE")
            result["analyze_executed"] = True
            
            # コミットとクローズ
            conn.commit()
            conn.close()
            
            # 最適化後のサイズ
            result["size_after_kb"] = db_path.stat().st_size / 1024
            result["space_saved_kb"] = result["size_before_kb"] - result["size_after_kb"]
            
            self.logger.info(f"✅ 最適化完了: {result['space_saved_kb']:.1f}KB削減")
            
        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"最適化エラー {db_path}: {e}")
        
        return result
    
    def archive_old_data(self, db_path: Path, days_to_keep: int = 90) -> Dict[str, Any]:
        """古いデータのアーカイブ"""
        self.logger.info(f"📦 古いデータアーカイブ: {db_path.name} ({days_to_keep}日より古い)")
        
        result = {
            "database": str(db_path),
            "archived_tables": [],
            "total_archived_rows": 0,
            "error": None
        }
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # テーブル一覧取得
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cutoff_timestamp = cutoff_date.isoformat()
            
            for table in tables:
                # タイムスタンプカラムの検出
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                
                timestamp_columns = []
                for col in columns:
                    col_name = col[1].lower()
                    if any(keyword in col_name for keyword in ['timestamp', 'created', 'updated', 'date']):
                        timestamp_columns.append(col[1])
                
                if timestamp_columns:
                    timestamp_col = timestamp_columns[0]  # 最初のタイムスタンプカラムを使用
                    
                    try:
                        # 古いデータ数確認
                        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {timestamp_col} < ?", (cutoff_timestamp,))
                        old_count = cursor.fetchone()[0]
                        
                        if old_count > 0:
                            # アーカイブテーブル作成
                            archive_table = f"{table}_archive"
                            cursor.execute(f"CREATE TABLE IF NOT EXISTS {archive_table} AS SELECT * FROM {table} WHERE 1=0")
                            
                            # 古いデータ移動
                            cursor.execute(f"INSERT INTO {archive_table} SELECT * FROM {table} WHERE {timestamp_col} < ?", (cutoff_timestamp,))
                            cursor.execute(f"DELETE FROM {table} WHERE {timestamp_col} < ?", (cutoff_timestamp,))
                            
                            result["archived_tables"].append({
                                "table": table,
                                "archived_rows": old_count
                            })
                            result["total_archived_rows"] += old_count
                            
                            self.logger.info(f"📦 {table}: {old_count}行アーカイブ")
                    
                    except Exception as e:
                        self.logger.warning(f"テーブル {table} アーカイブエラー: {e}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"アーカイブエラー {db_path}: {e}")
        
        return result
    
    def check_database_integrity(self, db_path: Path) -> Dict[str, Any]:
        """データベース整合性チェック"""
        self.logger.info(f"🔍 整合性チェック: {db_path.name}")
        
        result = {
            "database": str(db_path),
            "integrity_ok": False,
            "quick_check_ok": False,
            "foreign_key_check_ok": False,
            "issues": [],
            "error": None
        }
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 整合性チェック
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchall()
            if len(integrity_result) == 1 and integrity_result[0][0] == "ok":
                result["integrity_ok"] = True
            else:
                result["issues"].extend([row[0] for row in integrity_result])
            
            # クイックチェック
            cursor.execute("PRAGMA quick_check")
            quick_result = cursor.fetchall()
            if len(quick_result) == 1 and quick_result[0][0] == "ok":
                result["quick_check_ok"] = True
            else:
                result["issues"].extend([row[0] for row in quick_result])
            
            # 外部キーチェック
            cursor.execute("PRAGMA foreign_key_check")
            fk_result = cursor.fetchall()
            if len(fk_result) == 0:
                result["foreign_key_check_ok"] = True
            else:
                result["issues"].extend([f"FK violation: {row}" for row in fk_result])
            
            conn.close()
            
            if result["integrity_ok"] and result["quick_check_ok"] and result["foreign_key_check_ok"]:
                self.logger.info("✅ 整合性チェック: 問題なし")
            else:
                self.logger.warning(f"⚠️ 整合性チェック: {len(result['issues'])}個の問題")
        
        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"整合性チェックエラー {db_path}: {e}")
        
        return result
    
    def optimize_all_databases(self, include_archive: bool = False, 
                             archive_days: int = 90) -> Dict[str, Any]:
        """全データベース最適化"""
        self.logger.info("🚀 全データベース最適化開始")
        
        results = {
            "start_time": datetime.now().isoformat(),
            "databases_found": 0,
            "databases_optimized": 0,
            "total_space_saved_kb": 0,
            "optimizations": [],
            "integrity_checks": [],
            "archives": [],
            "errors": [],
            "end_time": None
        }
        
        # データベースファイル検出
        databases = self.find_databases()
        results["databases_found"] = len(databases)
        
        for db_path in databases:
            try:
                # 分析
                analysis = self.analyze_database(db_path)
                
                # 整合性チェック
                integrity = self.check_database_integrity(db_path)
                results["integrity_checks"].append(integrity)
                
                if not integrity["integrity_ok"]:
                    self.logger.warning(f"⚠️ 整合性問題のため最適化スキップ: {db_path.name}")
                    continue
                
                # 古いデータアーカイブ（オプション）
                if include_archive and analysis["total_rows"] > 1000:
                    archive_result = self.archive_old_data(db_path, archive_days)
                    results["archives"].append(archive_result)
                
                # 最適化実行
                optimization = self.optimize_database(db_path)
                results["optimizations"].append(optimization)
                
                if optimization["error"]:
                    results["errors"].append(optimization["error"])
                else:
                    results["databases_optimized"] += 1
                    results["total_space_saved_kb"] += optimization["space_saved_kb"]
                
            except Exception as e:
                error_msg = f"データベース処理エラー {db_path}: {e}"
                results["errors"].append(error_msg)
                self.logger.error(error_msg)
        
        results["end_time"] = datetime.now().isoformat()
        self.logger.info(f"✅ 全データベース最適化完了: {results['total_space_saved_kb']:.1f}KB削減")
        
        return results
    
    def print_summary(self, results: Dict[str, Any]):
        """最適化結果サマリー表示"""
        print("\n" + "="*60)
        print("🗄️ Elders Guild Database Optimization Report")
        print("="*60)
        
        print(f"\n📊 Summary:")
        print(f"  Databases found: {results['databases_found']}")
        print(f"  Databases optimized: {results['databases_optimized']}")
        print(f"  Total space saved: {results['total_space_saved_kb']:.1f} KB")
        
        if results["optimizations"]:
            print(f"\n⚡ Optimizations:")
            for opt in results["optimizations"]:
                if not opt["error"]:
                    db_name = Path(opt["database"]).name
                    saved = opt["space_saved_kb"]
                    print(f"  {db_name}: {saved:.1f}KB saved")
        
        if results["integrity_checks"]:
            good_dbs = sum(1 for check in results["integrity_checks"] 
                          if check["integrity_ok"] and check["quick_check_ok"])
            print(f"\n🔍 Integrity Checks:")
            print(f"  Healthy databases: {good_dbs}/{len(results['integrity_checks'])}")
            
            for check in results["integrity_checks"]:
                if not (check["integrity_ok"] and check["quick_check_ok"]):
                    db_name = Path(check["database"]).name
                    print(f"  ⚠️ Issues in {db_name}: {len(check['issues'])} problems")
        
        if results["archives"]:
            total_archived = sum(archive["total_archived_rows"] for archive in results["archives"])
            print(f"\n📦 Data Archiving:")
            print(f"  Total rows archived: {total_archived}")
        
        if results["errors"]:
            print(f"\n❌ Errors ({len(results['errors'])}):")
            for error in results["errors"][:5]:  # 最初の5エラーのみ表示
                print(f"  {error}")
        
        print("\n" + "="*60)

def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Optimizer")
    parser.add_argument("--optimize-all", action="store_true", help="全データベース最適化")
    parser.add_argument("--analyze-only", action="store_true", help="分析のみ実行")
    parser.add_argument("--integrity-check", action="store_true", help="整合性チェックのみ")
    parser.add_argument("--include-archive", action="store_true", help="古いデータアーカイブを含む")
    parser.add_argument("--archive-days", type=int, default=90, help="アーカイブ対象日数")
    parser.add_argument("--save", action="store_true", help="結果をファイルに保存")
    
    args = parser.parse_args()
    
    optimizer = DatabaseOptimizer()
    
    if args.analyze_only:
        databases = optimizer.find_databases()
        for db_path in databases[:5]:  # 最初の5個のみ
            analysis = optimizer.analyze_database(db_path)
            print(f"\n📊 {db_path.name}:")
            print(f"  Size: {analysis['size_kb']:.1f} KB")
            print(f"  Tables: {len(analysis['tables'])}")
            print(f"  Total rows: {analysis['total_rows']}")
            print(f"  Fragmentation: {analysis['fragmentation_percent']:.1f}%")
    elif args.integrity_check:
        databases = optimizer.find_databases()
        for db_path in databases[:5]:  # 最初の5個のみ
            integrity = optimizer.check_database_integrity(db_path)
            status = "✅ OK" if integrity["integrity_ok"] and integrity["quick_check_ok"] else "⚠️ Issues"
            print(f"{db_path.name}: {status}")
    elif args.optimize_all:
        results = optimizer.optimize_all_databases(
            include_archive=args.include_archive,
            archive_days=args.archive_days
        )
        optimizer.print_summary(results)
        
        if args.save:
            import json
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = optimizer.logs_dir / f"database_optimization_{timestamp}.json"
            with open(report_file, 'w') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n📄 Report saved: {report_file}")
    else:
        print("🗄️ Elders Guild Database Optimizer")
        print("使用方法:")
        print("  --optimize-all    : 全データベース最適化")
        print("  --analyze-only    : 分析のみ実行")
        print("  --integrity-check : 整合性チェックのみ")
        print("  --include-archive : 古いデータアーカイブ")
        print("  --save            : 結果保存")

if __name__ == "__main__":
    main()