#!/usr/bin/env python3
"""
Elder Dashboard Evolution 起動スクリプト
"""

import os
import sys
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 仮想環境からの実行
if __name__ == "__main__":
    from web.elder_dashboard_evolution import main

    main()
