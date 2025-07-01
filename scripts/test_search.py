#!/usr/bin/env python3
"""
検索・分析機能テスト
"""
import sys
sys.path.append('/root/ai_co')
from libs.conversation_search import ConversationSearchEngine
from libs.ai_learning_interface import AILearningInterface

def test_search():
    search = ConversationSearchEngine()
    ai_interface = AILearningInterface()
    
    print("=== 🔍 検索・分析テスト ===\n")
    
    # 1. キーワード検索
    print("【1】キーワード検索テスト")
    keywords = ["ECサイト", "Webアプリ", "作成"]
    results = search.search_by_keywords(keywords, limit=5)
    print(f"検索結果: {len(results)}件")
    for r in results:
        print(f"  - {r['task_id']}: スコア{r['relevance_score']}")
    
    # 2. 類似タスク検索
    print("\n【2】類似タスク検索")
    new_task = "オンラインショップを作りたい"
    similar = search.find_similar_tasks(new_task)
    print(f"類似タスク: {len(similar)}件")
    for s in similar:
        print(f"  - {s['task_id']}: 類似度{s['similarity_score']:.1%}")
    
    # 3. AI学習
    print("\n【3】AI学習データ")
    learning = ai_interface.learn_from_similar_tasks(new_task)
    if learning['suggested_approach']:
        print(f"推奨アプローチ: {learning['suggested_approach']}")
    
    # 4. 自己改善レポート
    print("\n【4】自己改善レポート")
    print(ai_interface.generate_self_improvement_report())

if __name__ == "__main__":
    test_search()
