#!/usr/bin/env python3
"""
Elders Guild ローカルIssue監視スクリプト
ローカルIssueファイルの存在を検知し、GitHub移行を促す
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 監視対象パターン
ISSUE_PATTERNS = [
    "**/docs/issues/*.md",

    "**/TASKS.md", 

    "**/tasks.json",
    "**/*issue*.md"
]

# 除外パス
EXCLUDE_PATHS = [
    "archives/",
    ".git/",
    "node_modules/",
    "__pycache__/",
    "docs/policies/NO_LOCAL_ISSUES_POLICY.md"
]

def find_local_issues(base_path: Path):
    """ローカルIssueファイルを検索"""
    violations = []
    
    for pattern in ISSUE_PATTERNS:
        for file_path in base_path.glob(pattern):
            # 除外パスチェック
            if any(exclude in str(file_path) for exclude in EXCLUDE_PATHS):
                continue
                
            violations.append(file_path)
    
    return violations

def report_violations(violations):
    pass

                """違反を報告"""
        print("✅ ローカルIssueファイルは見つかりませんでした。")
        return 0
    
    print("🚨 ローカルIssue廃止ポリシー違反が検出されました！")
    print(f"\n検出されたファイル数: {len(violations)}")
    print("\n違反ファイル一覧:")
    
    for file_path in violations:
        print(f"  ❌ {file_path}")
    
    print("\n📋 対応方法:")
    print("1.0 各ファイルの内容をGitHub Issueとして作成")
    print("2.0 gh issue create --title 'タイトル' --body-file ファイルパス")
    print("3.0 ローカルファイルを削除またはアーカイブへ移動")
    print("\n詳細: elders_guild/docs/policies/NO_LOCAL_ISSUES_POLICY.md")
    
    return 1

def main():
    pass

    """メイン処理""" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"対象ディレクトリ: {base_path}\n")
    
    violations = find_local_issues(base_path)
    return report_violations(violations)

if __name__ == "__main__":
    sys.exit(main())