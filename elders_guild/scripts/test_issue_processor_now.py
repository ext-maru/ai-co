#!/usr/bin/env python3
"""
Auto Issue Processor実行テスト
即座に実行して動作確認
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.integrations.github.auto_issue_processor import AutoIssueProcessor


async def test_processor():
    """Auto Issue Processorのテスト実行"""
    print("\n🤖 Auto Issue Processor実行開始")
    
    try:
        processor = AutoIssueProcessor()
        
        # スキャンして処理可能なイシューを確認
        scan_result = await processor.process_request({"mode": "scan"})
        
        if scan_result.get("processable_issues", 0) > 0:
            print(f"📊 処理可能なイシュー数: {scan_result['processable_issues']}")
            
            # 実際の処理を実行
            process_result = await processor.process_request({"mode": "process"})
            
            if process_result.get("status") == "success":
                processed = process_result.get("processed_issue", {})
                print(f"✅ イシュー #{processed.get('number')} 処理完了: {processed.get('title', 'N/A')}")
            else:
                print(f"⚠️ イシュー処理結果: {process_result.get('status')}")
        else:
            print("📝 処理可能なイシューなし")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_processor())