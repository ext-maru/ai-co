#!/usr/bin/env python3
"""
🛡️ エルダーズギルド 重複防止チェックスクリプト
=======================================

Issue #302 教訓に基づく重複ディレクトリ・ファイル検知システム
「想定しない名前で作り始めない」を技術的に支援

Author: Claude Elder
Created: 2025-07-23
Based on: Issue #302 resolution lessons
"""

import os
import sys
import argparse
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import fnmatch


class DuplicateChecker:
    """重複検知エンジン"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.ignore_patterns = [
            "__pycache__",
            ".git",
            ".pytest_cache", 
            "venv",
            "node_modules",
            "*.pyc",
            "*.pyo",
            ".DS_Store",
            "Thumbs.db"
        ]
        
        # Issue #302 で発見された危険パターン
        self.dangerous_patterns = [
            "src/",           # 重複の温床
            "source/",        # srcと同義
            "*/src/*/",       # ネストしたsrc
            "lib/",           # libsと混同
            "script/",        # scriptsと混同
            "test/",          # testsと混同
            "config/"         # configsと混同
        ]
        
        # 4賢者システム固定名
        self.sage_names = {
            "incident_sage",
            "knowledge_sage", 
            "task_sage",
            "rag_sage"
        }
    
    def should_ignore(self, path: Path) -> bool:
        """無視すべきパスかチェック"""
        path_str = str(path)
        
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(path.name, pattern):
                return True
        
        return False
    
    def find_duplicate_directories(self) -> Dict[str, List[str]]:
        """重複ディレクトリ検知"""
        directory_names = defaultdict(list)
        
        for root, dirs, files in os.walk(self.project_root):
            # 無視パターン適用
            dirs[:] = [d for d in dirs if not self.should_ignore(Path(root) / d)]
            
            root_path = Path(root)
            
            for dir_name in dirs:
                full_path = root_path / dir_name
                relative_path = full_path.relative_to(self.project_root)
                directory_names[dir_name].append(str(relative_path))
        
        # 重複のみ抽出
        duplicates = {name: paths for name, paths in directory_names.items() 
                     if len(paths) > 1}
        
        return duplicates
    
    def find_duplicate_files(self) -> Dict[str, List[str]]:
        """重複ファイル検知"""
        file_names = defaultdict(list)
        
        for root, dirs, files in os.walk(self.project_root):
            # 無視ディレクトリをスキップ
            dirs[:] = [d for d in dirs if not self.should_ignore(Path(root) / d)]
            
            root_path = Path(root)
            
            for file_name in files:
                full_path = root_path / file_name
                
                if self.should_ignore(full_path):
                    continue
                
                relative_path = full_path.relative_to(self.project_root)
                file_names[file_name].append(str(relative_path))
        
        # 重複のみ抽出
        duplicates = {name: paths for name, paths in file_names.items() 
                     if len(paths) > 1}
        
        return duplicates
    
    def check_dangerous_patterns(self) -> List[str]:
        """危険パターン検知"""
        dangerous_found = []
        
        for root, dirs, files in os.walk(self.project_root):
            root_path = Path(root)
            relative_path = root_path.relative_to(self.project_root)
            
            for pattern in self.dangerous_patterns:
                if fnmatch.fnmatch(str(relative_path), pattern):
                    dangerous_found.append(f"危険パターン '{pattern}': {relative_path}")
                
                # ディレクトリ名チェック
                for dir_name in dirs:
                    if fnmatch.fnmatch(dir_name, pattern.rstrip("/")):
                        full_dir_path = relative_path / dir_name
                        dangerous_found.append(f"危険ディレクトリ '{pattern}': {full_dir_path}")
        
        return dangerous_found
    
    def check_sage_conflicts(self) -> List[str]:
        """4賢者システム競合チェック"""
        conflicts = []
        
        for sage_name in self.sage_names:
            sage_paths = []
            
            for root, dirs, files in os.walk(self.project_root):
                if sage_name in dirs:
                    root_path = Path(root)
                    sage_path = root_path / sage_name
                    relative_path = sage_path.relative_to(self.project_root)
                    sage_paths.append(str(relative_path))
            
            if len(sage_paths) > 1:
                conflicts.append(f"4賢者重複: {sage_name} -> {sage_paths}")
        
        return conflicts
    
    def check_import_consistency(self) -> List[str]:
        """Import path一貫性チェック"""
        issues = []
        
        for root, dirs, files in os.walk(self.project_root):
            # 無視ディレクトリをスキップ
            dirs[:] = [d for d in dirs if not self.should_ignore(Path(root) / d)]
            
            for file in files:
                if not file.endswith('.py'):
                    continue
                
                file_path = Path(root) / file
                
                if self.should_ignore(file_path):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 相対import検知
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        line = line.strip()
                        if line.startswith('from ..') or line.startswith('from .'):
                            relative_path = file_path.relative_to(self.project_root)
                            issues.append(f"相対import検出: {relative_path}:{i} -> {line}")
                
                except (UnicodeDecodeError, PermissionError):
                    continue
        
        return issues
    
    def generate_report(self) -> Dict:
        """包括的レポート生成"""
        print("🔍 エルダーズギルド重複チェック実行中...")
        
        report = {
            "timestamp": "2025-07-23T20:xx:xx",
            "project_root": str(self.project_root),
            "checks": {
                "duplicate_directories": self.find_duplicate_directories(),
                "duplicate_files": self.find_duplicate_files(), 
                "dangerous_patterns": self.check_dangerous_patterns(),
                "sage_conflicts": self.check_sage_conflicts(),
                "import_issues": self.check_import_consistency()
            },
            "summary": {}
        }
        
        # サマリー生成
        total_issues = 0
        for check_name, results in report["checks"].items():
            if isinstance(results, dict):
                count = len(results)
            else:
                count = len(results)
            
            report["summary"][check_name] = count
            total_issues += count
        
        report["summary"]["total_issues"] = total_issues
        report["summary"]["status"] = "PASS" if total_issues == 0 else "FAIL"
        
        return report


def print_colored_report(report: Dict):
    """カラフルなレポート出力"""
    print("\n" + "="*70)
    print("🏛️ エルダーズギルド重複チェックレポート")
    print("="*70)
    
    summary = report["summary"]
    status = summary["status"]
    total_issues = summary["total_issues"]
    
    if status == "PASS":
        print(f"✅ ステータス: {status} - 重複問題なし")
    else:
        print(f"❌ ステータス: {status} - {total_issues}個の問題を検出")
    
    print(f"📁 プロジェクトルート: {report['project_root']}")
    print()
    
    # 詳細結果表示
    checks = report["checks"]
    
    # 重複ディレクトリ
    duplicate_dirs = checks["duplicate_directories"]
    if duplicate_dirs:
        print("🚨 重複ディレクトリ検出:")
        for name, paths in duplicate_dirs.items():
            print(f"  📁 {name}:")
            for path in paths:
                print(f"    - {path}")
        print()
    
    # 重複ファイル（重要なもののみ）
    duplicate_files = checks["duplicate_files"]
    important_files = {}
    for name, paths in duplicate_files.items():
        if name.endswith(('.py', '.md', '.yml', '.yaml', '.json')):
            important_files[name] = paths
    
    if important_files:
        print("🚨 重複ファイル検出:")
        for name, paths in important_files.items():
            print(f"  📄 {name}:")
            for path in paths[:5]:  # 最大5個まで表示
                print(f"    - {path}")
            if len(paths) > 5:
                print(f"    ... (+{len(paths)-5} more)")
        print()
    
    # 危険パターン
    dangerous_patterns = checks["dangerous_patterns"]
    if dangerous_patterns:
        print("⚠️ 危険パターン検出:")
        for pattern in dangerous_patterns:
            print(f"  🚨 {pattern}")
        print()
    
    # 4賢者競合
    sage_conflicts = checks["sage_conflicts"]
    if sage_conflicts:
        print("🏛️ 4賢者システム競合:")
        for conflict in sage_conflicts:
            print(f"  ⚔️ {conflict}")
        print()
    
    # Import問題
    import_issues = checks["import_issues"]
    if import_issues:
        print("📦 Import問題検出:")
        for issue in import_issues[:10]:  # 最大10個まで表示
            print(f"  📝 {issue}")
        if len(import_issues) > 10:
            print(f"  ... (+{len(import_issues)-10} more issues)")
        print()
    
    # 推奨対応
    if total_issues > 0:
        print("🛠️ 推奨対応:")
        if duplicate_dirs:
            print("  1.0 重複ディレクトリの統合・削除")
        if dangerous_patterns:
            print("  2.0 危険パターンディレクトリの改名・削除")
        if sage_conflicts:
            print("  3.0 4賢者システムの重複解決（Issue #302パターン）")
        if import_issues:
            print("  4.0 相対importの絶対import化")
        print("\n📚 詳細: docs/standards/PROJECT_STRUCTURE_STANDARDS.md")
    else:
        print("🎉 素晴らしい！プロジェクト構造は完璧です")
    
    print("\n" + "="*70)


def main():
    parser = argparse.ArgumentParser(
        description="エルダーズギルド重複防止チェックスクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python3 scripts/check_duplicates.py                    # 基本チェック
  python3 scripts/check_duplicates.py --json             # JSON出力
  python3 scripts/check_duplicates.py --target incident  # 特定名前チェック
  python3 scripts/check_duplicates.py --report report.json # レポート保存

Issue #302の教訓:
  このスクリプトは「incident_sage」と「src/incident_sage」のような
  重複ディレクトリ問題を未然に防ぐために作成されました。
        """
    )
    
    parser.add_argument(
        "--project-root", 
        default=".",
        help="プロジェクトルートディレクトリ（デフォルト: .）"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON形式で結果出力"
    )
    
    parser.add_argument(
        "--report",
        help="レポートをファイルに保存"
    )
    
    parser.add_argument(
        "--target",
        help="特定の名前パターンのみチェック"
    )
    
    parser.add_argument(
        "--exit-code",
        action="store_true", 
        help="問題がある場合は終了コード1で終了"
    )
    
    args = parser.parse_args()
    
    try:
        checker = DuplicateChecker(args.project_root)
        report = checker.generate_report()
        
        # 特定ターゲットフィルタリング
        if args.target:
            filtered_report = {"checks": {}, "summary": {"total_issues": 0}}
            
            for check_name, results in report["checks"].items():
                if isinstance(results, dict):
                    filtered_results = {k: v for k, v in results.items() 
                                      if args.target.lower() in k.lower()}
                else:
                    filtered_results = [r for r in results 
                                      if args.target.lower() in r.lower()]
                
                if filtered_results:
                    filtered_report["checks"][check_name] = filtered_results
            
            # サマリー再計算
            total = sum(len(v) if isinstance(v, (list, dict)) else 0 
                       for v in filtered_report["checks"].values())
            filtered_report["summary"]["total_issues"] = total
            filtered_report["summary"]["status"] = "PASS" if total == 0 else "FAIL"
            
            report = filtered_report
        
        # 出力処理
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print_colored_report(report)
        
        # レポート保存
        if args.report:
            with open(args.report, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n📊 レポート保存: {args.report}")
        
        # 終了コード設定
        if args.exit_code and report["summary"]["total_issues"] > 0:
            sys.exit(1)
        
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ エラー: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()