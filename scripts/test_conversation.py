#!/usr/bin/env python3
"""
会話管理テスト
"""
import sys
sys.path.append('/root/ai_co')
from libs.conversation_manager import ConversationManager

def test_conversation():
    manager = ConversationManager()
    
    # 会話開始
    conv_id = manager.start_conversation(
        task_id="test_001",
        initial_prompt="複雑なWebアプリを作成してください",
        context={"project": "test"}
    )
    
    print(f"会話ID: {conv_id}")
    
    # ワーカー応答
    manager.add_worker_message(
        conv_id,
        worker_id="worker-1",
        content="Webアプリの要件を詳しく教えてください"
    )
    
    # PM判断要求
    manager.request_user_input(
        conv_id,
        question="どのようなWebアプリを作成しますか？",
        options=["ECサイト", "ブログ", "管理画面", "その他"]
    )
    
    # サマリー取得
    summary = manager.get_conversation_summary(conv_id)
    print(f"サマリー: {summary}")
    
    # アクティブ会話一覧
    active = manager.db.get_active_conversations()
    print(f"アクティブ会話数: {len(active)}")

if __name__ == "__main__":
    test_conversation()
