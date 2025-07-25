#!/usr/bin/env python3
"""
🌳 Simple Elder Tree Migration
実際に存在するファイルを移行する簡易スクリプト
"""

import os
import shutil
import logging
from pathlib import Path
import sys

# 環境変数設定のインポート
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared_libs.config import config

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate():
    base = Path(config.ELDERS_GUILD_HOME)
    tree = base / "elder_tree"
    
    # 移行マップ（実際に存在するファイルのみ）
    migrations = [
        # ドワーフ部族
        ("elder_servants/dwarf_workshop/code_crafter.py", "elder_servants/dwarf_tribe/code_crafter/code_crafter.py"),
        ("elder_servants/dwarf_workshop/api_forge.py", "elder_servants/dwarf_tribe/forge_master/api_forge.py"),
        ("elder_servants/dwarf_workshop/cicd_builder.py", "elder_servants/dwarf_tribe/tool_smith/cicd_builder.py"),
        ("elder_servants/dwarf_workshop/__init__.py", "elder_servants/dwarf_tribe/__init__.py"),
        
        # 品質部族
        ("quality_servants/quality_watcher_servant.py", "elder_servants/quality_tribe/quality_watcher/quality_watcher_servant.py"),
        ("quality_servants/test_forge_servant.py", "elder_servants/quality_tribe/test_forge/test_forge_servant.py"),
        ("quality_servants/comprehensive_guardian_servant.py", "elder_servants/quality_tribe/comprehensive_guardian/comprehensive_guardian_servant.py"),
        ("quality_servants/__init__.py", "elder_servants/quality_tribe/__init__.py"),
    ]
    
    # ファイルをコピー
    for src, dst in migrations:
        src_path = base / src
        dst_path = tree / dst
        
        if src_path.exists():
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
            logger.info(f"✅ {src} → elder_tree/{dst}")
            
            # __init__.pyを作成
            init = dst_path.parent / "__init__.py"
            if not init.exists():
                init.write_text("")

if __name__ == "__main__":
    migrate()