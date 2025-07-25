#!/usr/bin/env python3
import asyncio
import os
from libs.integrations.github.enhanced_auto_issue_processor import EnhancedAutoIssueProcessor

async def test_integration():
    """統合テスト"""
    print("🧪 統合テスト開始...")
    
    # プロセッサ初期化
    processor = EnhancedAutoIssueProcessor()
    
    # スマートマージシステムが初期化可能か確認
    if processor.conflict_resolution_enabled:
        print("✅ コンフリクト解決機能: 有効")
    else:
        print("❌ コンフリクト解決機能: 無効")
    
    print("✅ 統合テスト完了")

if __name__ == "__main__":
    asyncio.run(test_integration())
