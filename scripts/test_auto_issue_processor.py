#!/usr/bin/env python3
"""
自動イシュー処理システムの総合テスト
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 環境変数確認
print("🔍 環境変数チェック...")
print(f"GITHUB_TOKEN: {'✅ 設定済み' if os.getenv('GITHUB_TOKEN') else '❌ 未設定'}")
print(f"GITHUB_REPOSITORY: {os.getenv('GITHUB_REPOSITORY', 'ext-maru/ai-co')}")

from libs.integrations.github.auto_issue_processor import AutoIssueProcessor


async def test_auto_issue_processor()print("\n🚀 自動イシュー処理テスト開始...\n")
"""自動イシュー処理の総合テスト"""
    
    try:
        processor = AutoIssueProcessor()
        print("✅ AutoIssueProcessor初期化成功")
    except Exception as e:
        print(f"❌ 初期化エラー: {e}")
        return
    
    # 1.0 スキャンモードテスト
    print("\n📊 Step 1: スキャンモードテスト")
    print("-" * 50)
    
    scan_result = await processor.process_request({'mode': 'scan'})
    
    if scan_result['status'] == 'success':
        print(f"✅ スキャン成功: {scan_result['processable_issues']}件の処理可能なイシューを発見")
        
        if scan_result['processable_issues'] > 0:
            print("\n処理可能なイシュー:")
            for issue in scan_result.get('issues', []):
                print(f"  - #{issue['number']}: {issue['title']}")
                print(f"    優先度: {issue['priority']}, 複雑度: {issue['complexity']:0.2f}")
        else:
            print("ℹ️ 処理可能なイシューがありません")
            return
    else:
        print(f"❌ スキャンエラー: {scan_result.get('message', 'Unknown error')}")
        return
    
    # 2.0 ドライランテスト（最初のイシュー）
    if scan_result.get('issues'):
        first_issue = scan_result['issues'][0]
        
        print(f"\n📝 Step 2: Issue #{first_issue['number']}のドライランテスト")
        print("-" * 50)
        
        dry_run_result = await processor.process_request({
            'mode': 'dry_run',
            'issue_number': first_issue['number']
        })
        
        if dry_run_result['status'] == 'dry_run':
            issue_info = dry_run_result['issue']
            print(f"✅ ドライラン成功:")
            print(f"  - タイトル: {issue_info['title']}")
            print(f"  - 優先度: {issue_info['priority']}")
            print(f"  - 複雑度: {issue_info['complexity']:0.2f}")
            print(f"  - 処理可能: {'✅' if issue_info['processable'] else '❌'}")
            print(f"  - 評価要因: {json.dumps(issue_info['factors'], indent}")
        else:
            print(f"❌ ドライランエラー: {dry_run_result}")
    
    # 3.0 実際の処理テスト（実行するかユーザーに確認）
    print("\n⚠️ Step 3: 実際の処理（PR作成）")
    print("-" * 50)
    print("実際にPRを作成しますか？")
    print("※ 実際のGitHub上でPRが作成されます")
    
    user_input = input("実行する場合は 'yes' と入力してください: ")
    
    if user_input.lower() == 'yes':
        print("\n🔄 実際の処理を開始します...")
        
        process_result = await processor.process_request({'mode': 'process'})
        
        if process_result['status'] == 'success':
            processed = process_result.get('processed_issue', {})
            print(f"\n✅ 処理成功!")
            print(f"  - Issue: #{processed.get('number')} {processed.get('title', '')}")
            
            result = processed.get('result', {})
            if result.get('pr_url'):
                print(f"  - PR作成: {result['pr_url']}")
            else:
                print(f"  - 結果: {result.get('message', 'Unknown result')}")
        else:
            print(f"❌ 処理エラー: {process_result}")
    else:
        print("ℹ️ 実際の処理はスキップされました")
    
    print("\n✅ テスト完了")


if __name__ == "__main__":
    asyncio.run(test_auto_issue_processor())