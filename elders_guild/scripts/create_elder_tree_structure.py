#!/usr/bin/env python3
"""
🌳 Elder Tree Structure Creator
Elder Tree構造を作成する専用スクリプト
"""

import os
import sys
from pathlib import Path

# migrate_to_elder_tree.pyから必要な部分をインポート
sys.path.append(str(Path(__file__).parent))
from migrate_to_elder_tree import ElderTreeMigrator

def main():
    """Elder Tree構造を作成"""
    print("🌳 Elder Tree構造を作成します...")
    
    migrator = ElderTreeMigrator()
    
    # 構造作成
    migrator.create_elder_tree_structure()
    
    # 検証
    if migrator.verify_migration():
        print("\n✅ Elder Tree構造の作成が完了しました！")
        print(f"📁 場所: {migrator.elder_tree_path}")
    else:
        print("\n❌ 構造作成中にエラーが発生しました。")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())