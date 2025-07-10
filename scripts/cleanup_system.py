#!/usr/bin/env python3
"""
System Cleanup Tool - システムクリーンアップツール
エルダーズギルドの不要ファイル削除とシステム最適化

🧹 クリーンアップ対象:
- Python キャッシュファイル (.pyc, __pycache__)
- 一時ファイル (.tmp, .bak, *~)
- 空ディレクトリ
- 重複ファイル
- 古いログファイル
"""

import os
import sys
import shutil
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Set
from collections import defaultdict

class SystemCleanup:
    """システムクリーンアップクラス"""
    
    def __init__(self, project_dir: str = "/home/aicompany/ai_co"):
        self.project_dir = Path(project_dir)
        self.logs_dir = self.project_dir / "logs"
        
        # 除外ディレクトリ
        self.exclude_dirs = {
            '.git', 'node_modules', '.venv', 'venv', '__pycache__',
            '.pytest_cache', '.mypy_cache', 'dist', 'build'
        }
        
        # 削除対象拡張子
        self.cleanup_extensions = {
            '.pyc', '.pyo', '.tmp', '.bak', '.swp', '.swo', 
            '.orig', '.rej', '.patch', '.DS_Store'
        }
        
        # ログ設定
        self.setup_logging()
        
    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.logs_dir / 'system_cleanup.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def clean_python_cache(self) -> Dict[str, int]:
        """Python キャッシュファイルのクリーンアップ"""
        self.logger.info("🐍 Python キャッシュクリーンアップ開始")
        
        stats = {
            "pycache_dirs": 0,
            "pyc_files": 0,
            "size_freed_mb": 0
        }
        
        total_size = 0
        
        # __pycache__ ディレクトリの削除
        for pycache_dir in self.project_dir.rglob("__pycache__"):
            if pycache_dir.is_dir():
                try:
                    # サイズ計算
                    dir_size = sum(f.stat().st_size for f in pycache_dir.rglob('*') if f.is_file())
                    total_size += dir_size
                    
                    # ディレクトリ削除
                    shutil.rmtree(pycache_dir)
                    stats["pycache_dirs"] += 1
                    self.logger.debug(f"削除: {pycache_dir}")
                except Exception as e:
                    self.logger.warning(f"削除失敗 {pycache_dir}: {e}")
        
        # 個別 .pyc ファイルの削除
        for pyc_file in self.project_dir.rglob("*.pyc"):
            try:
                file_size = pyc_file.stat().st_size
                total_size += file_size
                pyc_file.unlink()
                stats["pyc_files"] += 1
            except Exception as e:
                self.logger.warning(f"削除失敗 {pyc_file}: {e}")
        
        stats["size_freed_mb"] = total_size / (1024 * 1024)
        
        self.logger.info(f"🐍 Python キャッシュクリーンアップ完了: "
                        f"{stats['pycache_dirs']}ディレクトリ, "
                        f"{stats['pyc_files']}ファイル, "
                        f"{stats['size_freed_mb']:.1f}MB解放")
        
        return stats
    
    def clean_temp_files(self) -> Dict[str, int]:
        """一時ファイルのクリーンアップ"""
        self.logger.info("🗑️ 一時ファイルクリーンアップ開始")
        
        stats = {
            "temp_files": 0,
            "size_freed_mb": 0
        }
        
        total_size = 0
        
        for file_path in self.project_dir.rglob("*"):
            if not file_path.is_file():
                continue
                
            # 拡張子チェック
            if file_path.suffix in self.cleanup_extensions:
                try:
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    file_path.unlink()
                    stats["temp_files"] += 1
                    self.logger.debug(f"削除: {file_path}")
                except Exception as e:
                    self.logger.warning(f"削除失敗 {file_path}: {e}")
            
            # バックアップファイル（末尾~）
            elif file_path.name.endswith('~'):
                try:
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    file_path.unlink()
                    stats["temp_files"] += 1
                    self.logger.debug(f"削除: {file_path}")
                except Exception as e:
                    self.logger.warning(f"削除失敗 {file_path}: {e}")
        
        stats["size_freed_mb"] = total_size / (1024 * 1024)
        
        self.logger.info(f"🗑️ 一時ファイルクリーンアップ完了: "
                        f"{stats['temp_files']}ファイル, "
                        f"{stats['size_freed_mb']:.1f}MB解放")
        
        return stats
    
    def clean_empty_directories(self) -> int:
        """空ディレクトリの削除"""
        self.logger.info("📁 空ディレクトリクリーンアップ開始")
        
        removed_dirs = 0
        
        # 下位ディレクトリから上位に向かって処理
        all_dirs = sorted([d for d in self.project_dir.rglob("*") if d.is_dir()], 
                         key=lambda x: len(x.parts), reverse=True)
        
        for dir_path in all_dirs:
            # 除外ディレクトリをスキップ
            if dir_path.name in self.exclude_dirs:
                continue
            
            # 重要ディレクトリをスキップ
            if any(important in str(dir_path) for important in ['.git', 'node_modules']):
                continue
            
            try:
                # ディレクトリが空かチェック
                if dir_path.is_dir() and not any(dir_path.iterdir()):
                    dir_path.rmdir()
                    removed_dirs += 1
                    self.logger.debug(f"空ディレクトリ削除: {dir_path}")
            except Exception as e:
                self.logger.debug(f"ディレクトリ削除失敗 {dir_path}: {e}")
        
        self.logger.info(f"📁 空ディレクトリクリーンアップ完了: {removed_dirs}ディレクトリ削除")
        return removed_dirs
    
    def find_duplicate_files(self) -> Dict[str, List[Path]]:
        """重複ファイルの検出"""
        self.logger.info("🔍 重複ファイル検出開始")
        
        file_hashes = defaultdict(list)
        
        for file_path in self.project_dir.rglob("*"):
            if not file_path.is_file():
                continue
            
            # 大きなファイルのみチェック (1KB以上)
            if file_path.stat().st_size < 1024:
                continue
            
            # バイナリファイルや特定ファイルをスキップ
            if file_path.suffix in {'.pyc', '.pyo', '.so', '.dll', '.exe'}:
                continue
            
            try:
                # ファイルハッシュ計算
                hasher = hashlib.md5()
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)
                file_hash = hasher.hexdigest()
                file_hashes[file_hash].append(file_path)
            except Exception as e:
                self.logger.debug(f"ハッシュ計算失敗 {file_path}: {e}")
        
        # 重複ファイルのみ抽出
        duplicates = {hash_val: paths for hash_val, paths in file_hashes.items() if len(paths) > 1}
        
        total_duplicates = sum(len(paths) - 1 for paths in duplicates.values())
        self.logger.info(f"🔍 重複ファイル検出完了: {len(duplicates)}グループ, {total_duplicates}個の重複")
        
        return duplicates
    
    def clean_old_logs(self, days_to_keep: int = 30) -> Dict[str, int]:
        """古いログファイルのクリーンアップ"""
        self.logger.info(f"📋 古いログファイルクリーンアップ開始 ({days_to_keep}日より古い)")
        
        stats = {
            "old_logs": 0,
            "size_freed_mb": 0
        }
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        total_size = 0
        
        for log_file in self.logs_dir.rglob("*.log"):
            if not log_file.is_file():
                continue
            
            try:
                modified_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if modified_time < cutoff_date:
                    file_size = log_file.stat().st_size
                    total_size += file_size
                    log_file.unlink()
                    stats["old_logs"] += 1
                    self.logger.debug(f"古いログ削除: {log_file}")
            except Exception as e:
                self.logger.warning(f"ログ削除失敗 {log_file}: {e}")
        
        stats["size_freed_mb"] = total_size / (1024 * 1024)
        
        self.logger.info(f"📋 古いログファイルクリーンアップ完了: "
                        f"{stats['old_logs']}ファイル, "
                        f"{stats['size_freed_mb']:.1f}MB解放")
        
        return stats
    
    def optimize_git_repository(self) -> Dict[str, any]:
        """Git リポジトリの最適化"""
        self.logger.info("📦 Git リポジトリ最適化開始")
        
        stats = {
            "git_gc_run": False,
            "size_before_mb": 0,
            "size_after_mb": 0,
            "error": None
        }
        
        git_dir = self.project_dir / ".git"
        if not git_dir.exists():
            self.logger.info("Git リポジトリが見つかりません")
            return stats
        
        try:
            # .git ディレクトリサイズ（前）
            size_before = sum(f.stat().st_size for f in git_dir.rglob('*') if f.is_file())
            stats["size_before_mb"] = size_before / (1024 * 1024)
            
            # Git ガベージコレクション実行
            import subprocess
            result = subprocess.run(
                ["git", "gc", "--aggressive", "--prune=now"],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                stats["git_gc_run"] = True
                
                # .git ディレクトリサイズ（後）
                size_after = sum(f.stat().st_size for f in git_dir.rglob('*') if f.is_file())
                stats["size_after_mb"] = size_after / (1024 * 1024)
                
                self.logger.info(f"📦 Git リポジトリ最適化完了: "
                               f"{stats['size_before_mb']:.1f}MB → {stats['size_after_mb']:.1f}MB")
            else:
                stats["error"] = result.stderr
                self.logger.warning(f"Git 最適化失敗: {result.stderr}")
                
        except Exception as e:
            stats["error"] = str(e)
            self.logger.error(f"Git 最適化エラー: {e}")
        
        return stats
    
    def run_full_cleanup(self, include_duplicates: bool = False, 
                        include_old_logs: bool = True) -> Dict[str, any]:
        """フルクリーンアップ実行"""
        self.logger.info("🚀 フルシステムクリーンアップ開始")
        
        results = {
            "start_time": datetime.now().isoformat(),
            "python_cache": None,
            "temp_files": None,
            "empty_dirs": 0,
            "duplicates": None,
            "old_logs": None,
            "git_optimization": None,
            "total_size_freed_mb": 0
        }
        
        # Python キャッシュクリーンアップ
        results["python_cache"] = self.clean_python_cache()
        
        # 一時ファイルクリーンアップ
        results["temp_files"] = self.clean_temp_files()
        
        # 空ディレクトリクリーンアップ
        results["empty_dirs"] = self.clean_empty_directories()
        
        # 重複ファイル検出（削除は手動）
        if include_duplicates:
            results["duplicates"] = self.find_duplicate_files()
        
        # 古いログファイルクリーンアップ
        if include_old_logs:
            results["old_logs"] = self.clean_old_logs()
        
        # Git リポジトリ最適化
        results["git_optimization"] = self.optimize_git_repository()
        
        # 合計解放容量計算
        total_freed = 0
        if results["python_cache"]:
            total_freed += results["python_cache"]["size_freed_mb"]
        if results["temp_files"]:
            total_freed += results["temp_files"]["size_freed_mb"]
        if results["old_logs"]:
            total_freed += results["old_logs"]["size_freed_mb"]
        
        results["total_size_freed_mb"] = total_freed
        results["end_time"] = datetime.now().isoformat()
        
        self.logger.info(f"✅ フルシステムクリーンアップ完了: {total_freed:.1f}MB解放")
        
        return results
    
    def print_summary(self, results: Dict[str, any]):
        """クリーンアップ結果サマリー表示"""
        print("\n" + "="*60)
        print("🧹 Elders Guild System Cleanup Report")
        print("="*60)
        
        print(f"\n📊 Summary:")
        print(f"  Total Space Freed: {results['total_size_freed_mb']:.1f} MB")
        
        if results["python_cache"]:
            pc = results["python_cache"]
            print(f"\n🐍 Python Cache Cleanup:")
            print(f"  __pycache__ dirs removed: {pc['pycache_dirs']}")
            print(f"  .pyc files removed: {pc['pyc_files']}")
            print(f"  Space freed: {pc['size_freed_mb']:.1f} MB")
        
        if results["temp_files"]:
            tf = results["temp_files"]
            print(f"\n🗑️ Temporary Files Cleanup:")
            print(f"  Files removed: {tf['temp_files']}")
            print(f"  Space freed: {tf['size_freed_mb']:.1f} MB")
        
        print(f"\n📁 Empty Directories:")
        print(f"  Directories removed: {results['empty_dirs']}")
        
        if results["duplicates"]:
            dup = results["duplicates"]
            total_dups = sum(len(paths) - 1 for paths in dup.values())
            print(f"\n🔍 Duplicate Files (not removed):")
            print(f"  Duplicate groups: {len(dup)}")
            print(f"  Total duplicates: {total_dups}")
        
        if results["old_logs"]:
            ol = results["old_logs"]
            print(f"\n📋 Old Logs Cleanup:")
            print(f"  Files removed: {ol['old_logs']}")
            print(f"  Space freed: {ol['size_freed_mb']:.1f} MB")
        
        if results["git_optimization"]:
            git = results["git_optimization"]
            if git["git_gc_run"]:
                print(f"\n📦 Git Repository Optimization:")
                print(f"  Size before: {git['size_before_mb']:.1f} MB")
                print(f"  Size after: {git['size_after_mb']:.1f} MB")
                saved = git['size_before_mb'] - git['size_after_mb']
                print(f"  Space saved: {saved:.1f} MB")
        
        print("\n" + "="*60)

def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="System Cleanup Tool")
    parser.add_argument("--full", action="store_true", help="フルクリーンアップ実行")
    parser.add_argument("--python-cache", action="store_true", help="Python キャッシュのみクリーンアップ")
    parser.add_argument("--temp-files", action="store_true", help="一時ファイルのみクリーンアップ")
    parser.add_argument("--empty-dirs", action="store_true", help="空ディレクトリのみクリーンアップ")
    parser.add_argument("--find-duplicates", action="store_true", help="重複ファイル検出のみ")
    parser.add_argument("--git-optimize", action="store_true", help="Git リポジトリ最適化のみ")
    parser.add_argument("--include-duplicates", action="store_true", help="重複ファイル検出を含める")
    parser.add_argument("--skip-old-logs", action="store_true", help="古いログ削除をスキップ")
    parser.add_argument("--save", action="store_true", help="結果をファイルに保存")
    
    args = parser.parse_args()
    
    cleanup = SystemCleanup()
    
    if args.python_cache:
        results = cleanup.clean_python_cache()
        print(f"Python キャッシュクリーンアップ完了: {results}")
    elif args.temp_files:
        results = cleanup.clean_temp_files()
        print(f"一時ファイルクリーンアップ完了: {results}")
    elif args.empty_dirs:
        count = cleanup.clean_empty_directories()
        print(f"空ディレクトリクリーンアップ完了: {count}個削除")
    elif args.find_duplicates:
        duplicates = cleanup.find_duplicate_files()
        print(f"重複ファイル検出完了: {len(duplicates)}グループ")
        for hash_val, paths in list(duplicates.items())[:5]:  # 最初の5グループ表示
            print(f"  重複グループ {hash_val[:8]}:")
            for path in paths:
                print(f"    {path}")
    elif args.git_optimize:
        results = cleanup.optimize_git_repository()
        print(f"Git リポジトリ最適化完了: {results}")
    elif args.full:
        results = cleanup.run_full_cleanup(
            include_duplicates=args.include_duplicates,
            include_old_logs=not args.skip_old_logs
        )
        cleanup.print_summary(results)
        
        if args.save:
            import json
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = cleanup.logs_dir / f"cleanup_report_{timestamp}.json"
            with open(report_file, 'w') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n📄 Report saved: {report_file}")
    else:
        print("🧹 Elders Guild System Cleanup Tool")
        print("使用方法:")
        print("  --full            : フルクリーンアップ")
        print("  --python-cache    : Python キャッシュクリーンアップ")
        print("  --temp-files      : 一時ファイルクリーンアップ")
        print("  --empty-dirs      : 空ディレクトリクリーンアップ")
        print("  --find-duplicates : 重複ファイル検出")
        print("  --git-optimize    : Git リポジトリ最適化")
        print("  --save            : 結果保存 (--fullと併用)")

if __name__ == "__main__":
    main()