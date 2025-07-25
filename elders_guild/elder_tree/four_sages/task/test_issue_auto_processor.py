#!/usr/bin/env python3
"""
イシュー自動処理システムのシンプルなテスト
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
import json

async def test_scan_issues()print("🔍 イシュー自動処理システムのテスト開始...")
"""イシューのスキャンをテスト"""
    
    try:
        # プロセッサーの初期化
        processor = AutoIssueProcessor()
        print("✅ AutoIssueProcessor 初期化成功")
        
        # 機能確認
        capabilities = processor.get_capabilities()
        print(f"📋 機能一覧: {json.dumps(capabilities, indent}")
        
        # スキャンモードでテスト
        print("\n📊 処理可能なイシューをスキャン中...")
        result = await processor.process_request({'mode': 'scan'})
        
        if result['status'] == 'success':
            print(f"✅ スキャン成功！")
            print(f"📌 処理可能なイシュー数: {result['processable_issues']}")
            
            if result['issues']:
                print("\n📝 処理可能なイシュー:")
                for issue in result['issues']:
                    print(f"  - #{issue['number']}: {issue['title']}")
                    print(f"    優先度: {issue['priority']}, 複雑度: {issue['complexity']:0.2f}")
        else:
            print(f"❌ スキャン失敗: {result}")
            
    except Exception as e:
        print(f"❌ エラー発生: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_dry_run(issue_number: int)print(f"\n🧪 Issue #{issue_number} のドライランテスト...")
"""特定のイシューでドライランテスト"""
    
    try:
        processor = AutoIssueProcessor()
        result = await processor.process_request({
            'mode': 'dry_run',
            'issue_number': issue_number
        })
        
        print(f"結果: {json.dumps(result, indent}")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

async def main():
    """メイン処理"""
    # 1.0 スキャンテスト
    await test_scan_issues()
    
    # 2.0 特定のイシューでドライラン（例: Issue #92）
    # await test_dry_run(92)

if __name__ == "__main__":
    asyncio.run(main())