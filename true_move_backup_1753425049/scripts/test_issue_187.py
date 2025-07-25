#!/usr/bin/env python3
"""
Issue #187 の直接A2A処理テスト
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
from github import Github


async def test_issue_187():
    """Issue #187を直接処理"""
    print("\n🚀 Issue #187 の直接A2A処理テスト開始...\n")
    
    # GitHub APIクライアント
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("❌ GITHUB_TOKEN環境変数が設定されていません")
        return
    
    try:
        g = Github(github_token)
        repo = g.get_repo("ext-maru/ai-co")
        issue = repo.get_issue(187)
        
        print(f"✅ Issue #{issue.number}を取得: {issue.title}")
        print(f"   状態: {issue.state}")
        print(f"   ラベル: {[label.name for label in issue.labels]}")
        
    except Exception as e:
        print(f"❌ Issue取得エラー: {e}")
        return
    
    # AutoIssueProcessor初期化
    try:
        processor = AutoIssueProcessor()
        print("✅ AutoIssueProcessor初期化成功")
    except Exception as e:
        print(f"❌ AutoIssueProcessor初期化エラー: {e}")
        return
    
    # Issue #187の直接処理
    print(f"\n📝 Issue #{issue.number}をA2A処理で実行...")
    print("-" * 60)
    
    try:
        # A2A処理を単一Issueで実行
        results = await processor.process_issues_a2a([issue])
        
        if results:
            result = results[0]
            print(f"\n✅ A2A処理完了:")
            print(f"  - ステータス: {result.get('status')}")
            print(f"  - Issue番号: {result.get('issue_number')}")
            
            if result.get('status') == 'success':
                print(f"  - PR番号: {result.get('pr_number')}")
                print(f"  - PR URL: {result.get('pr_url')}")
                
                # 生成されたプログラムの詳細を確認
                if 'claude_result' in result:
                    claude_result = json.loads(result['claude_result'])
                    print(f"\n📊 Claude生成プログラムの詳細:")
                    print(f"  - 実行ステータス: {claude_result.get('status')}")
                    
            elif result.get('status') == 'error':
                print(f"  - エラー: {result.get('message')}")
                print(f"  - 詳細: {result.get('error')}")
                
            elif result.get('status') == 'already_exists':
                print(f"  - 既存PR: {result.get('pr_url')}")
                print(f"  - メッセージ: {result.get('message')}")
                
        else:
            print("❌ 結果が返されませんでした")
            
    except Exception as e:
        print(f"❌ A2A処理エラー: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ テスト完了")


if __name__ == "__main__":
    asyncio.run(test_issue_187())