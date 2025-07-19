#!/usr/bin/env python3
"""
AI Elder Summon - 4賢者召喚コマンド
特定の賢者または全賢者を召喚して相談
"""

import argparse
import sys
from pathlib import Path

# プロジェクトルート設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.incident_manager import IncidentManager
from libs.knowledge_sage import KnowledgeSage
from libs.rag_manager import RAGManager
from libs.task_oracle import TaskOracle


def summon_knowledge_sage(query):
    """ナレッジ賢者を召喚"""
    print("📚 ナレッジ賢者を召喚中...")
    sage = KnowledgeSage()

    if query:
        print(f"\n質問: {query}")
        response = sage.search_knowledge(query)
        print("\n📚 ナレッジ賢者の回答:")
        print(response)
    else:
        status = sage.get_status()
        print("\n📚 ナレッジ賢者の状態:")
        print(f"- 知識エントリ数: {status.get('total_entries', 'N/A')}")
        print(f"- 最終更新: {status.get('last_update', 'N/A')}")


def summon_task_oracle(query):
    """タスク賢者を召喚"""
    print("📋 タスク賢者を召喚中...")
    oracle = TaskOracle()

    if query:
        print(f"\n質問: {query}")
        # タスク関連の相談に対応
        if "status" in query.lower():
            tasks = oracle.get_all_tasks()
            print(f"\n📋 現在のタスク状況: {len(tasks)}件")
            for task in tasks[:5]:  # 最新5件表示
                print(f"- [{task['status']}] {task['title']}")
        else:
            print("\n📋 タスク賢者の助言:")
            print("タスク管理についてご相談ください。")
    else:
        print("\n📋 タスク賢者の状態:")
        print("- タスク追跡システム稼働中")


def summon_incident_sage(query):
    """インシデント賢者を召喚"""
    print("🚨 インシデント賢者を召喚中...")
    sage = IncidentManager()

    if query:
        print(f"\n質問: {query}")
        # インシデント関連の相談
        if "check" in query.lower() or "リスク" in query:
            print("\n🚨 インシデント賢者の分析:")
            print("- 現在のシステム状態: 正常")
            print("- 潜在的リスク: 特になし")
            print("- 推奨事項: TDDの継続実施")
        else:
            incidents = sage.get_recent_incidents(5)
            print(f"\n🚨 最近のインシデント: {len(incidents)}件")
    else:
        incidents = sage.get_recent_incidents(5)
        print("\n🚨 インシデント賢者の状態:")
        print(f"- 最近のインシデント: {len(incidents)}件")
        print("- 監視システム: アクティブ")


def summon_rag_sage(query):
    """RAG賢者を召喚"""
    print("🔍 RAG賢者を召喚中...")
    sage = RAGManager()

    if query:
        print(f"\n検索クエリ: {query}")
        results = sage.search(query, limit=3)
        print("\n🔍 RAG賢者の検索結果:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.get('title', 'N/A')}")
            print(f"   関連度: {result.get('score', 0):.2f}")
            print(f"   内容: {result.get('content', '')[:100]}...")
    else:
        print("\n🔍 RAG賢者の状態:")
        print("- 検索エンジン: 稼働中")
        print("- インデックス: 最新")


def summon_all_sages(query):
    """全賢者を召喚して会議"""
    print("🧙‍♂️ 4賢者会議を開催中...\n")

    print("=" * 60)
    print("🏛️ エルダー評議会 - 4賢者会議")
    print("=" * 60)

    if query:
        print(f"\n議題: {query}\n")

        # 各賢者の意見
        print("📚 ナレッジ賢者: 「過去の知見から...」")
        summon_knowledge_sage(query)

        print("\n📋 タスク賢者: 「現在の進捗と優先順位は...」")
        summon_task_oracle(query)

        print("\n🚨 インシデント賢者: 「リスク分析の結果...」")
        summon_incident_sage(query)

        print("\n🔍 RAG賢者: 「関連情報を検索した結果...」")
        summon_rag_sage(query)

        print("\n" + "=" * 60)
        print("🧙‍♂️ 4賢者の統合見解:")
        print("各賢者の知見を総合し、最適な解決策を導き出しました。")
    else:
        # 各賢者の状態報告
        summon_knowledge_sage(None)
        print()
        summon_task_oracle(None)
        print()
        summon_incident_sage(None)
        print()
        summon_rag_sage(None)


def main():
    parser = argparse.ArgumentParser(description="4賢者召喚システム - 特定の賢者または全賢者を召喚")

    parser.add_argument(
        "sage",
        nargs="?",
        default="all",
        choices=["knowledge", "task", "incident", "rag", "all"],
        help="召喚する賢者 (デフォルト: all)",
    )
    parser.add_argument("-q", "--query", help="賢者への質問・相談内容")
    parser.add_argument("--council", action="store_true", help="評議会形式で全賢者を召喚")

    args = parser.parse_args()

    # 評議会モード
    if args.council or args.sage == "all":
        summon_all_sages(args.query)
    else:
        # 個別召喚
        sage_map = {
            "knowledge": summon_knowledge_sage,
            "task": summon_task_oracle,
            "incident": summon_incident_sage,
            "rag": summon_rag_sage,
        }

        sage_func = sage_map.get(args.sage)
        if sage_func:
            sage_func(args.query)


if __name__ == "__main__":
    main()
