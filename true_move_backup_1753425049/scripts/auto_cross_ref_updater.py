#!/usr/bin/env python3
"""
自動相互参照更新スクリプト
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def update_cross_references():
    """相互参照を更新"""
    try:
        from scripts.grimoire_accessibility_enhancer_fixed import (
            GrimoireAccessibilityEnhancer,
        )

        enhancer = GrimoireAccessibilityEnhancer()

        # 相互参照システムのみ更新
        cross_ref_result = enhancer._create_cross_reference_system()

        print(f"相互参照更新完了: {cross_ref_result['status']}")
        return cross_ref_result["status"] == "completed"

    except Exception as e:
        print(f"相互参照更新エラー: {e}")
        return False


if __name__ == "__main__":
    success = update_cross_references()
    sys.exit(0 if success else 1)
