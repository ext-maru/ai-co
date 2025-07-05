#!/usr/bin/env python3
"""
会話システムヘルスチェック
"""
import sys
sys.path.append('/root/ai_co')
from features.conversation.conversation_recovery import ConversationRecoveryManager
from features.conversation.conversation_manager import ConversationManager
import json

def health_check():
    recovery = ConversationRecoveryManager()
    manager = ConversationManager()
    
    print("=== 🏥 会話システムヘルスチェック ===")
    
    # アクティブ会話
    active = manager.db.get_active_conversations()
    print(f"\n📊 アクティブ会話: {len(active)}件")
    
    for conv in active[:5]:  # 最初の5件
        print(f"  - {conv['conversation_id']}: {conv['state']} ({conv['message_count']}メッセージ)")
    
    # 停止会話チェック
    stalled = recovery.check_stalled_conversations()
    print(f"\n⚠️ 停止会話: {len(stalled)}件")
    
    for conv in stalled:
        print(f"  - {conv['conversation_id']}: 最終更新 {conv['last_update']}")
    
    # ワーカー状態
    print("\n🤖 ワーカー状態:")
    workers = ['dialog-worker-1', 'dialog-worker-2']
    for worker in workers:
        alive = recovery.check_worker_heartbeat(worker)
        status = "✅ 稼働中" if alive else "❌ 停止"
        print(f"  - {worker}: {status}")
    
    # 統計
    import sqlite3
    conn = sqlite3.connect(recovery.db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT state, COUNT(*) FROM conversations GROUP BY state")
    stats = cursor.fetchall()
    
    print("\n📈 会話統計:")
    for state, count in stats:
        print(f"  - {state}: {count}件")
    
    conn.close()

if __name__ == "__main__":
    health_check()
