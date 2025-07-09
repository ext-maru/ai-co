#!/usr/bin/env python3
"""
タスクエルダー記憶魔法コマンド
セッションの保存と復元を簡単に実行
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.task_elder_memory_magic import TaskElderMemoryMagic, save_current_session, recall_session


def main():
    parser = argparse.ArgumentParser(description="タスクエルダー記憶魔法 - セッション管理")
    
    subparsers = parser.add_subparsers(dest='command', help='コマンド')
    
    # 保存コマンド
    save_parser = subparsers.add_parser('save', help='現在のセッションを保存')
    save_parser.add_argument('-p', '--project', required=True, help='プロジェクト名')
    save_parser.add_argument('-c', '--context', required=True, help='文脈の説明')
    save_parser.add_argument('-d', '--decisions', nargs='+', help='重要な決定事項')
    
    # 復元コマンド
    recall_parser = subparsers.add_parser('recall', help='セッションを復元')
    recall_parser.add_argument('-t', '--trigger', default='前回の続きから', help='復元トリガー')
    
    # リストコマンド
    list_parser = subparsers.add_parser('list', help='保存されたセッション一覧')
    
    # クリーンアップコマンド
    clean_parser = subparsers.add_parser('clean', help='期限切れセッションを削除')
    
    args = parser.parse_args()
    
    magic = TaskElderMemoryMagic()
    
    if args.command == 'save':
        # 簡易的なTodo取得（実際はtodo読み込みシステムと連携）
        todos = [
            {"id": "current-1", "content": "現在のタスク", "status": "in_progress"}
        ]
        
        decisions = args.decisions or ["コマンドラインから保存"]
        messages = ["記憶魔法で保存されました"]
        
        session_id = save_current_session(
            project_name=args.project,
            todos=todos,
            key_decisions=decisions,
            context=args.context,
            messages=messages
        )
        
        print(f"\n✅ セッション保存完了!")
        print(f"復元コマンド: ai-memory-magic recall -t '{args.project}の続き'")
        
    elif args.command == 'recall':
        memory = recall_session(args.trigger)
        if not memory:
            print("\n💡 ヒント: 以下のトリガーを試してください:")
            print("  - '前回の続きから'")
            print("  - 'プロジェクト[名前]の続き'")
            print("  - 'sess_[ID]を復元'")
            
    elif args.command == 'list':
        print("\n📚 保存されたセッション一覧:")
        print("="*60)
        
        memory_files = sorted(magic.memory_dir.glob("sess_*.json"), reverse=True)
        valid_count = 0
        
        for memory_file in memory_files[:10]:  # 最新10件
            memory = magic._load_memory_file(memory_file)
            if memory and magic._is_memory_valid(memory):
                valid_count += 1
                print(f"\nセッションID: {memory['session_id']}")
                print(f"  プロジェクト: {memory.get('project', {}).get('name', '不明')}")
                print(f"  保存日時: {memory['timestamp']}")
                print(f"  保持期限: {memory['retention_until']}")
                print(f"  文脈: {memory.get('context_summary', '')[:50]}...")
                
        if valid_count == 0:
            print("有効なセッションが見つかりません")
        else:
            print(f"\n合計 {valid_count} 件の有効なセッション")
            
    elif args.command == 'clean':
        magic._cleanup_expired_memories()
        print("✅ クリーンアップ完了")
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()