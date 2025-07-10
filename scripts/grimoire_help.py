#!/usr/bin/env python3
"""
4賢者グリモア クイックヘルプ
"""

import sys
from pathlib import Path

def show_help(topic=None):
    """ヘルプ表示"""
    if topic is None:
        print("🏛️ 4賢者グリモア - クイックヘルプ")
        print("=" * 50)
        print("使用法: python grimoire_help.py [トピック]")
        print("")
        print("📚 利用可能なトピック:")
        print("- sages: 4賢者の概要")
        print("- files: グリモアファイル一覧")
        print("- search: 検索方法")
        print("- index: 索引ファイルの使い方")
        print("- navigation: ナビゲーション方法")
        print("")
        print("例: python grimoire_help.py sages")
    
    elif topic == "sages":
        print("🧙‍♂️ 4賢者の概要")
        print("=" * 30)
        print("📚 ナレッジ賢者: 知識の蓄積と継承")
        print("📋 タスク賢者: 進捗管理と実行順序")
        print("🚨 インシデント賢者: 問題対応と復旧")
        print("🔍 RAG賢者: 情報検索と統合")
    
    elif topic == "files":
        print("📁 グリモアファイル一覧")
        print("=" * 30)
        print("00_common_knowledge.md - 共通知識")
        print("01_knowledge_sage_grimoire.md - ナレッジ賢者")
        print("02_task_oracle_grimoire.md - タスク賢者")
        print("03_incident_sage_grimoire.md - インシデント賢者")
        print("04_rag_mystic_grimoire.md - RAG賢者")
        print("")
        print("📖 索引ファイル:")
        print("MASTER_INDEX.md - 統合索引")
        print("TOPIC_INDEX.md - トピック別索引")
        print("QUICK_REFERENCE.md - クイックリファレンス")
        print("README.md - ナビゲーションガイド")
    
    else:
        print(f"❌ 不明なトピック: {topic}")
        print("利用可能なトピック: sages, files, search, index, navigation")

if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else None
    show_help(topic)
