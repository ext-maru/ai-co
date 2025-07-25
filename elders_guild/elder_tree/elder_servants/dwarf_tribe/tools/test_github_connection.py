#!/usr/bin/env python3
"""GitHub接続テスト"""

import os
import sys
sys.path.insert(0, '/home/aicompany/ai_co')

from github import Github
import requests
from libs.env_manager import EnvManager

async def test_github_connection():
    """GitHub接続をテスト"""
    print("🔧 GitHub接続テスト開始")
    
    # 環境変数からトークンを取得
    github_token = os.environ.get('GITHUB_TOKEN')
    if github_token:
        print(f"✅ GITHUB_TOKEN検出: {github_token[:10]}...{github_token[-4:]}")
    else:
        print("❌ GITHUB_TOKENが設定されていません")
        return
    
    try:
        # PyGithubを使用した接続テスト
        print("\n📊 PyGithub接続テスト中...")
        g = Github(github_token)
        
        # ユーザー情報を取得（実際のAPI呼び出し）
        user = g.get_user()
        print(f"✅ 認証済みユーザー: {user.login}")
        print(f"✅ レート制限: {g.rate_limiting[0]}/{g.rate_limiting[1]}")
        
        # リポジトリ情報を取得
        repo_owner = EnvManager.get_github_repo_owner()
        repo_name = EnvManager.get_github_repo_name()
        if repo_owner and repo_name:
            try:
                repo = g.get_repo(f"{repo_owner}/{repo_name}")
                print(f"✅ リポジトリアクセス可能: {repo.full_name}")
                print(f"   - Issues: {repo.open_issues_count}")
                print(f"   - Stars: {repo.stargazers_count}")
            except Exception as repo_error:
                print(f"⚠️  リポジトリアクセスエラー: {repo_error}")
        
        # REST API直接テスト
        print("\n📊 REST API直接テスト中...")
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        response = requests.get(f'{EnvManager.get_github_api_base_url()}/user', headers=headers)
        if response.status_code == 200:
            print("✅ REST API接続成功")
        else:
            print(f"❌ REST API接続失敗: {response.status_code}")
        
        print("\n✅ GitHub API接続テスト完了")
        
    except Exception as e:
        print(f"❌ 接続エラー: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_github_connection())