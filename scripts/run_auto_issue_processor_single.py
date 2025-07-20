#!/usr/bin/env python3
"""
Auto Issue Processor - 単一Issue処理スクリプト
特定のIssue番号を指定して処理を実行
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


async def process_single_issue(issue_number: int):
    """単一のIssueを処理"""
    print(f"\n🚀 Issue #{issue_number} の処理を開始します...\n")
    
    try:
        processor = AutoIssueProcessor()
        print("✅ AutoIssueProcessor初期化成功")
    except Exception as e:
        print(f"❌ 初期化エラー: {e}")
        return
    
    # 特定のIssueを処理
    print(f"\n📝 Issue #{issue_number} を処理します...")
    print("-" * 50)
    
    try:
        # 直接process_specific_issueを呼び出す
        result = await processor.process_request({
            'mode': 'process_specific',
            'issue_number': issue_number
        })
        
        if result['status'] == 'success':
            print(f"\n✅ 処理成功!")
            processed = result.get('processed_issue', {})
            print(f"  - Issue: #{processed.get('number')} {processed.get('title', '')}")
            
            pr_result = processed.get('result', {})
            if pr_result.get('pr_url'):
                print(f"  - PR作成: {pr_result['pr_url']}")
                print(f"  - PR番号: #{pr_result.get('pr_number')}")
            
            # A2A実行の詳細
            if 'flow_result' in pr_result:
                print(f"\n📊 Elder Flow実行結果:")
                flow_result = pr_result['flow_result']
                if 'results' in flow_result:
                    print(f"  - 品質スコア: {flow_result['results'].get('quality_gate', {}).get('score', 'N/A')}")
        elif result['status'] == 'skipped':
            print(f"⏭️ スキップ: {result.get('message', 'Unknown reason')}")
        else:
            print(f"❌ 処理エラー: {result.get('message', 'Unknown error')}")
            if 'error' in result:
                print(f"  詳細: {result['error']}")
    except Exception as e:
        print(f"❌ 実行エラー: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ 処理完了")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python run_auto_issue_processor_single.py <issue_number>")
        sys.exit(1)
    
    try:
        issue_number = int(sys.argv[1])
    except ValueError:
        print("❌ Issue番号は数値で指定してください")
        sys.exit(1)
    
    asyncio.run(process_single_issue(issue_number))