#!/usr/bin/env python3
"""
🔄 Execute Elder Loop True Move - Direct
非対話式で真の移行を直接実行
"""

import sys
import os
sys.path.append('/home/aicompany/ai_co')

from elder_loop_true_move_strict import ElderLoopTrueMoveStrict

def main():
    """直接実行"""
    print("🔄 Elder Loop True MOVE - Direct Execution")
    print("==========================================")
    
    migrator = ElderLoopTrueMoveStrict()
    
    # 削除対象確認
    print("削除対象ディレクトリ:")
    for dir_name in migrator.move_targets:
        dir_path = migrator.base_path / dir_name
        if dir_path.exists():
            file_count = len(list(dir_path.rglob("*.py")))
            print(f"  - {dir_name}: {file_count}ファイル")
    
    print("\n🔄 真の移動を直接実行...")
    
    # 真の移動実行
    success = migrator.execute_true_move()
    
    # レポート作成
    migrator.create_final_report()
    
    if success:
        print("\n🎉 Elder Loop True Move 成功！")
        print("✅ 元ディレクトリ完全削除完了")
        print("✅ elders_guild のみが残存")
        print("✅ 真の移行達成")
        
        # 最終検証
        print("\n🔍 最終検証実行...")
        os.system("find /home/aicompany/ai_co -name '*.py' | grep -E '(libs|scripts)' | wc -l")
        
    else:
        print("\n🚨 Elder Loop True Move 失敗")
        print("❌ 一部ディレクトリが残存")

if __name__ == "__main__":
    main()