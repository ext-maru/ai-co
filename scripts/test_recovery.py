#!/usr/bin/env python3
"""
リカバリ機能テスト
"""
import sys
import time
from datetime import datetime, timedelta
sys.path.append('/root/ai_co')
from libs.conversation_recovery import ConversationRecoveryManager
from libs.conversation_manager import ConversationManager

def test_recovery():
    manager = ConversationManager()
    recovery = ConversationRecoveryManager()
    
    print("=== リカバリ機能テスト ===")
    
    # 1. 古い会話を作成（タイムアウトテスト用）
    old_task_id = f"timeout_test_{int(time.time())}"
    conv_id = manager.start_conversation(old_task_id, "タイムアウトテスト")
    
    # 手動で古い時刻に更新
    import sqlite3
    conn = sqlite3.connect(recovery.db_path)
    old_time = (datetime.now() - timedelta(hours=1)).isoformat()
    conn.execute(
        "UPDATE conversations SET updated_at = ? WHERE conversation_id = ?",
        (old_time, conv_id)
    )
    conn.commit()
    conn.close()
    
    print(f"古い会話作成: {conv_id}")
    
    # 2. 停止会話チェック
    stalled = recovery.check_stalled_conversations()
    print(f"停止会話検出: {len(stalled)}件")
    
    if stalled:
        print(f"リカバリ対象: {stalled[0]['conversation_id']}")
        
        # 3. リカバリ実行
        success = recovery.recover_conversation(stalled[0]['conversation_id'])
        print(f"リカバリ結果: {'成功' if success else '失敗'}")
    
    # 4. ヘルスチェック
    print("\n現在の状態:")
    import subprocess
    subprocess.run([sys.executable, "scripts/conversation_health_check.py"])

if __name__ == "__main__":
    test_recovery()
