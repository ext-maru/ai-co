#!/usr/bin/env python3
"""
GitHub連携テスト
"""
import sys
import os
sys.path.append('/root/ai_co')
from libs.github_integration import GitHubIntegrationManager
from libs.github_aware_rag import GitHubAwareRAGManager

def test_github():
    print("=== 🐙 GitHub連携テスト ===\n")
    
    # トークンチェック
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("⚠️ GITHUB_TOKEN未設定")
        print("実行: source scripts/setup_github.sh")
        return
    
    github = GitHubIntegrationManager()
    
    # 基本情報
    print("【リポジトリ情報】")
    print(f"URL: {github.repo_url}")
    if github.owner and github.repo:
        print(f"Owner/Repo: {github.owner}/{github.repo}")
    else:
        print("⚠️ GitHubリポジトリが検出されませんでした")
        print("ローカルでの使用は可能です")
        return
    
    # コードベース分析
    print("\n【コードベース分析】")
    analysis = github.analyze_codebase(['libs', 'workers'])
    print(f"総ファイル数: {analysis['total_files']}")
    print(f"ファイルタイプ: {analysis['file_types']}")
    
    # GitHub RAGテスト
    print("\n【GitHub対応RAGテスト】")
    rag = GitHubAwareRAGManager()
    test_prompt = "TaskWorkerの改善方法を教えて"
    context = rag.build_context_with_github(test_prompt)
    print(f"コンテキストサイズ: {len(context)}文字")
    print(f"GitHub情報含む: {'関連コード情報' in context}")

if __name__ == "__main__":
    test_github()
