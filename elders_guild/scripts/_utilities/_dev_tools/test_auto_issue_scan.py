#!/usr/bin/env python3
"""
Auto Issue Processor - スキャンテスト
処理可能なIssueをスキャンして表示
"""

import asyncio
import json
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.integrations.github.auto_issue_processor import AutoIssueProcessor


async def scan_issues():
    """処理可能なIssueをスキャン"""
    print("\n🔍 処理可能なIssueをスキャンしています...\n")
    
    try:
        processor = AutoIssueProcessor()
        print("✅ AutoIssueProcessor初期化成功")
    except Exception as e:
        print(f"❌ 初期化エラー: {e}")
        return
    
    # スキャンモードで実行
    try:
        result = await processor.process_request({'mode': 'scan'})
        
        print(f"\n📊 スキャン結果:")
        print(f"  - ステータス: {result.get('status')}")
        print(f"  - 処理可能なIssue数: {result.get('processable_issues', 0)}")
        
        if result.get('issues'):
            print("\n📋 処理可能なIssue一覧:")
            for issue in result['issues']:
                print(f"  - #{issue['number']}: {issue['title']}")
                if 'labels' in issue:
                    print(f"    ラベル: {', '.join(issue['labels'])}")
        else:
            print("\n📝 現在処理可能なIssueはありません")
            
    except Exception as e:
        print(f"\n❌ スキャンエラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(scan_issues())