#!/usr/bin/env python3
"""
Elders Guild コマンドランチャー（シンプル版）
全てのai-xxxコマンドはこのスクリプトを経由して実行される
"""
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def main():
    """メインエントリーポイント"""
    # コマンド名は第一引数として渡される
    if len(sys.argv) < 2:
        print("エラー: コマンド名が指定されていません")
        sys.exit(1)
    
    command_name = sys.argv[1]
    
    # 引数リストを調整（コマンド名を除去）
    original_argv = sys.argv[:]
    sys.argv = [command_name] + sys.argv[2:]
    
    # コマンド名からモジュール名を決定
    if command_name == 'ai':
        # 'ai' コマンドは特別扱い
        module_name = 'ai'
    elif command_name.startswith('ai-'):
        # 'ai-xxx' 形式の場合、ハイフンをアンダースコアに変換
        module_name = command_name.replace('-', '_')
    else:
        # その他の場合は'ai'コマンドのサブコマンドとして扱う
        # 例: 'ai status' -> 'ai' + ['status']
        sys.argv = ['ai', command_name] + sys.argv[2:]
        module_name = 'ai'
    
    try:
        # 対応するモジュールをインポート
        module = __import__(f'commands.{module_name}', fromlist=['main'])
        
        # main関数を実行
        if hasattr(module, 'main'):
            sys.exit(module.main())
        else:
            print(f"エラー: {module_name}モジュールにmain関数がありません")
            sys.exit(1)
            
    except ImportError as e:
        print(f"エラー: コマンド '{command_name}' が見つかりません")
        print(f"詳細: {e}")
        print(f"モジュール名: commands.{module_name}")
        sys.exit(1)
        
    except Exception as e:
        print(f"エラー: コマンド実行中に問題が発生しました")
        print(f"詳細: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
