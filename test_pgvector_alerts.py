#!/usr/bin/env python3
"""
pgvectorアラート機能テスト
"""

import asyncio
import sys
import os
sys.path.append('/home/aicompany/ai_co')

from libs.pgvector_auto_system import PgVectorAutoSystem

async def test_alerts():
    """アラート機能テスト"""
    print("🧪 pgvectorアラート機能テスト開始")
    
    auto_system = PgVectorAutoSystem()
    
    # 1. アラート送信テスト
    print("\n1. アラート送信テスト...")
    await auto_system._send_alert("テストアラート: システム正常動作確認")
    
    # 2. 擬似エラーアラート
    print("\n2. エラーアラートテスト...")
    await auto_system._send_alert("エラーテスト: 模擬的なシステム異常を検出")
    
    # 3. 統計情報付きアラート
    print("\n3. 統計情報付きアラートテスト...")
    auto_system.stats.update({
        'files_processed': 123,
        'errors_count': 1,
        'last_update': '2025-07-21T02:58:00'
    })
    await auto_system._send_alert("統計アラート: 処理統計情報を含むアラート")
    
    # 4. ログファイル確認
    print("\n4. ログファイル確認...")
    log_path = auto_system.config['alert_log']
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"✅ アラートログファイル作成済み: {log_path}")
        print(f"📝 ログエントリ数: {len(lines)}")
        
        if lines:
            print("\n📋 最新のアラートログ:")
            import json
            try:
                latest = json.loads(lines[-1])
                print(f"  時刻: {latest['timestamp']}")
                print(f"  メッセージ: {latest['message']}")
                print(f"  システム: {latest['system']}")
            except json.JSONDecodeError:
                print("  ⚠️ JSON解析エラー")
    else:
        print(f"❌ アラートログファイルが作成されていません: {log_path}")
    
    print("\n✅ アラート機能テスト完了")

if __name__ == "__main__":
    asyncio.run(test_alerts())