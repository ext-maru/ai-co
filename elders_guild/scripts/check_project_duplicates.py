#!/usr/bin/env python3
"""
🛡️ エルダーズギルド プロジェクト重複チェッカー（簡潔版）
============================================

Issue #302 教訓に基づく実用的な重複検知
プロジェクト固有の重複のみを検出

Author: Claude Elder  
Created: 2025-07-23
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

class ProjectDuplicateChecker:
    """プロジェクト重複検知（実用版）"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        
        # 除外ディレクトリ（外部ライブラリ等）
        self.exclude_dirs = {
            "venv", ".venv", "node_modules", "__pycache__", 
            ".git", ".mypy_cache", ".pytest_cache",
            "libs/elder_servants/integrations/continue_dev/venv_continue_dev",

        }
        
        # 4賢者システム
        self.sage_names = {
            "incident_sage", "knowledge_sage", "task_sage", "rag_sage"
        }
        
        # 危険パターン（Issue #302教訓）
        self.dangerous_patterns = ["src", "source", "lib", "script", "test", "config"]
    
    def should_exclude(self, path: Path) -> bool:
        """除外すべきパスかチェック"""
        path_str = str(path.relative_to(self.project_root))
        
        for exclude in self.exclude_dirs:
            if exclude in path_str or path.name in self.exclude_dirs:
                return True
        return False
    
    def find_project_duplicates(self) -> Dict[str, List[str]]:
        """プロジェクト内重複検知"""
        directory_map = defaultdict(list)
        
        for root, dirs, files in os.walk(self.project_root):
            # 除外ディレクトリをスキップ
            dirs[:] = [d for d in dirs if not self.should_exclude(Path(root) / d)]
            
            root_path = Path(root)
            if self.should_exclude(root_path):
                continue
            
            for dir_name in dirs:
                full_path = root_path / dir_name
                rel_path = full_path.relative_to(self.project_root)
                directory_map[dir_name].append(str(rel_path))
        
        # 重複のみ抽出（2個以上）
        duplicates = {name: paths for name, paths in directory_map.items() 
                     if len(paths) > 1}
        
        return duplicates
    
    def check_sage_conflicts(self) -> List[str]:
        """4賢者重複チェック"""
        conflicts = []
        
        for sage_name in self.sage_names:
            locations = []
            
            for root, dirs, files in os.walk(self.project_root):
                if self.should_exclude(Path(root)):
                    continue
                
                if sage_name in dirs:
                    sage_path = Path(root) / sage_name
                    rel_path = sage_path.relative_to(self.project_root)
                    locations.append(str(rel_path))
            
            if len(locations) > 1:
                conflicts.append(f"{sage_name}: {locations}")
        
        return conflicts
    
    def check_dangerous_patterns(self) -> List[str]:
        """危険パターンチェック"""
        dangerous_found = []
        
        for root, dirs, files in os.walk(self.project_root):
            if self.should_exclude(Path(root)):
                continue
            
            root_path = Path(root)
            
            for dir_name in dirs:
                if dir_name in self.dangerous_patterns:
                    full_path = root_path / dir_name
                    rel_path = full_path.relative_to(self.project_root)
                    dangerous_found.append(str(rel_path))
        
        return dangerous_found
    
    def generate_report(self) -> Dict:
        """簡潔レポート生成"""
        print("🔍 プロジェクト重複チェック実行中...")
        
        duplicates = self.find_project_duplicates()
        sage_conflicts = self.check_sage_conflicts()
        dangerous = self.check_dangerous_patterns()
        
        # 重要な重複のみフィルタリング
        important_duplicates = {}
        for name, paths in duplicates.items():
            # 重要なディレクトリのみ
            if (name in self.sage_names or 
                name in ["data", "tests", "scripts", "docs", "configs", "libs"] or
                any(sage in name for sage in self.sage_names)):
                important_duplicates[name] = paths
        
        total_issues = len(important_duplicates) + len(sage_conflicts) + len(dangerous)
        
        return {
            "status": "PASS" if total_issues == 0 else "FAIL",
            "total_issues": total_issues,
            "important_duplicates": important_duplicates,
            "sage_conflicts": sage_conflicts,
            "dangerous_patterns": dangerous
        }

def print_simple_report(report: Dict):
    """簡潔なレポート出力"""
    print("\n" + "="*60)
    print("🏛️ エルダーズギルド プロジェクト重複チェック")
    print("="*60)
    
    status = report["status"]
    total = report["total_issues"]
    
    if status == "PASS":
        print("✅ ステータス: PASS - 重複問題なし")
        print("🎉 プロジェクト構造は完璧です！")
    else:
        print(f"❌ ステータス: FAIL - {total}個の問題検出")
    
    print()
    
    # 重要な重複
    important = report["important_duplicates"]
    if important:
        print("🚨 重要な重複ディレクトリ:")
        for name, paths in important.items():
            print(f"  📁 {name}:")
            for path in paths:
                print(f"    - {path}")
        print()
    
    # 4賢者競合
    sage_conflicts = report["sage_conflicts"]
    if sage_conflicts:
        print("🏛️ 4賢者システム競合（Issue #302パターン）:")
        for conflict in sage_conflicts:
            print(f"  ⚔️ {conflict}")
        print()
    
    # 危険パターン
    dangerous = report["dangerous_patterns"]
    if dangerous:
        print("⚠️ 危険パターンディレクトリ:")
        for pattern in dangerous:
            print(f"  🚨 {pattern}")
        print()
    
    # 対応推奨
    if total > 0:
        print("🛠️ 推奨対応:")
        if important:
            print("  1.0 重複ディレクトリの統合・削除")
        if sage_conflicts:
            print("  2.0 4賢者システム重複解決（最安全策適用）")
        if dangerous:
            print("  3.0 危険パターンディレクトリの改名")
        print("\n📚 詳細: docs/standards/PROJECT_STRUCTURE_STANDARDS.md")
    
    print("="*60)

def main():
    """メイン実行"""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = "."
    
    try:
        checker = ProjectDuplicateChecker(project_root)
        report = checker.generate_report()
        print_simple_report(report)
        
        # 問題がある場合は終了コード1
        if report["total_issues"] > 0:
            sys.exit(1)
        
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ エラー: {e}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()