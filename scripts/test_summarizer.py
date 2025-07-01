#!/usr/bin/env python3
"""
要約機能テスト
"""
import sys
sys.path.append('/root/ai_co')
from libs.conversation_summarizer import ConversationSummarizer
from libs.conversation_manager import ConversationManager
import time

def test_summarizer():
    # テスト会話作成
    manager = ConversationManager()
    summarizer = ConversationSummarizer()
    
    # 長い会話を作成
    conv_id = manager.start_conversation(
        task_id=f"summary_test_{int(time.time())}",
        initial_prompt="要約テスト用の長い会話"
    )
    
    # 複数のメッセージ追加
    messages = [
        ("worker:worker-1", "要件を詳しく教えてください"),
        ("user", "ECサイトを作りたいです"),
        ("worker:worker-1", "どのような商品を扱いますか？"),
        ("user", "ハンドメイドのアクセサリーです"),
        ("worker:worker-1", "決済機能は必要ですか？"),
        ("user", "はい、クレジットカードと銀行振込に対応したいです"),
        ("worker:worker-1", "在庫管理機能も必要ですか？"),
        ("user", "はい、在庫数の自動管理が欲しいです"),
        ("worker:worker-1", "デザインの希望はありますか？"),
        ("user", "シンプルで女性向けのデザインでお願いします"),
        ("worker:worker-1", "了解しました。実装を開始します"),
    ]
    
    for sender, content in messages:
        if sender.startswith("worker"):
            manager.add_worker_message(conv_id, "worker-1", content)
        else:
            manager.db.add_message(conv_id, sender, content)
    
    print(f"テスト会話作成: {conv_id}")
    print(f"メッセージ数: {len(messages) + 1}")
    
    # 要約チェック
    need_summary = summarizer.check_conversations_for_summary()
    print(f"要約が必要な会話: {need_summary}")
    
    if conv_id in need_summary:
        # 要約生成
        print("\n要約生成中...")
        summary = summarizer.generate_summary(conv_id)
        print(f"生成された要約:\n{summary}")
        
        # 要約保存と圧縮
        if summary and "失敗" not in summary:
            summarizer.save_summary(conv_id, summary)
            summarizer.compress_old_messages(conv_id)
            print("\n✅ 要約保存・圧縮完了")

if __name__ == "__main__":
    test_summarizer()
