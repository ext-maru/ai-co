#!/usr/bin/env python3
"""
自動イシュー処理の修正テスト
"""

import asyncio
import json
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.integrations.github.auto_issue_processor import AutoIssueProcessor


async def test_auto_issue_processor():
    """修正されたAutoIssueProcessorをテスト"""
    processor = AutoIssueProcessor()
    
    print("🔍 自動イシュー処理テスト開始...")
    
    # スキャンモード
    print("\n📊 スキャンモードでテスト...")
    scan_result = await processor.process_request({'mode': 'scan'})
    print(json.dumps(scan_result, indent=2, ensure_ascii=False))
    
    if scan_result['status'] == 'success' and scan_result['processable_issues'] > 0:
        print(f"\n✅ {scan_result['processable_issues']}件の処理可能なイシューが見つかりました")
        print("処理可能なイシュー:")
        for issue in scan_result.get('issues', []):
            print(f"  - #{issue['number']}: {issue['title']}")
        
        # 最初のイシューだけテスト処理
        if scan_result.get('issues'):
            first_issue = scan_result['issues'][0]
            print(f"\n🚀 Issue #{first_issue['number']}の処理をテスト...")
            
            # 処理実行（ドライランモード）
            process_result = await processor.process_request({
                'mode': 'process',
                'dry_run': True,  # 実際には処理しない
                'issue_numbers': [first_issue['number']]
            })
            
            print("\n📝 処理結果:")
            print(json.dumps(process_result, indent=2, ensure_ascii=False))
    else:
        print("\n ℹ️ 処理可能なイシューがありません")
    
    print("\n✅ テスト完了")


if __name__ == "__main__":
    asyncio.run(test_auto_issue_processor())