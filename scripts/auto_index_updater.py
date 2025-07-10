#!/usr/bin/env python3
"""
自動索引更新スクリプト
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def update_indices():
    """索引を更新"""
    try:
        from scripts.grimoire_accessibility_enhancer_fixed import GrimoireAccessibilityEnhancer

        enhancer = GrimoireAccessibilityEnhancer()

        # 索引ファイルのみ更新
        index_files = enhancer._create_index_files()

        print(f"索引更新完了: {len(index_files)}ファイル")
        return True

    except Exception as e:
        print(f"索引更新エラー: {e}")
        return False


if __name__ == "__main__":
    success = update_indices()
    sys.exit(0 if success else 1)
