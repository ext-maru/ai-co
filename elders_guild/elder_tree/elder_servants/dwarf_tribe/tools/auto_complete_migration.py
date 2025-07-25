#!/usr/bin/env python3
"""
🌳 Auto Complete Elder Tree Migration
自動で完全Elder Tree移行を実行
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def execute_complete_migration():
    """完全移行を実行"""
    base_path = Path("/home/aicompany/ai_co/elders_guild")
    
    # 移行マッピング
    mapping = {
        # エンシェントエルダー
        "ancient_elder": "elder_tree/ancient_elder/main",
        "ancient_elders": "elder_tree/ancient_elder/legacy", 
        
        # クロードエルダー
        "claude_elder": "elder_tree/claude_elder/main",
        "elder_flow": "elder_tree/claude_elder/flow",
        "elder_system": "elder_tree/claude_elder/core",
        
        # 4賢者
        "four_sages": "elder_tree/four_sages",
        
        # サーバント・インフラ
        "infrastructure": "elder_tree/elder_servants/coordination/infrastructure",
        "core": "elder_tree/elder_servants/coordination/shared_resources/core",
        "shared_libs": "elder_tree/elder_servants/coordination/shared_resources/shared_libs",
        
        # 品質・テスト
        "quality": "elder_tree/elder_servants/quality_tribe/engines",
        "testing": "elder_tree/elder_servants/quality_tribe/testing",
        "tests": "elder_tree/elder_servants/quality_tribe/tests",
        
        # 開発・デプロイ
        "deployment": "elder_tree/elder_servants/dwarf_tribe/deployment",
        "docker": "elder_tree/elder_servants/dwarf_tribe/containers",
        "scripts": "elder_tree/elder_servants/dwarf_tribe/tools",
        
        # 監視・データ
        "monitoring": "elder_tree/elder_servants/elf_tribe/monitoring",
        "data": "elder_tree/elder_servants/elf_tribe/data_management",
        
        # その他
        "orchestration": "elder_tree/elder_servants/coordination/orchestration",
        "mcp_tools": "elder_tree/elder_servants/wizard_tribe/mcp_tools",
        "documentation": "elder_tree/ancient_elder/documentation",
        "config": "elder_tree/elder_servants/coordination/shared_resources/config",
        "cli": "elder_tree/claude_elder/integration/cli",
    }
    
    logger.info("🌳 完全Elder Tree移行開始...")
    
    moved_count = 0
    for old_dir, new_path in mapping.items():
        old_path = base_path / old_dir
        new_full_path = base_path / new_path
        
        if old_path.exists() and old_path.is_dir():
            try:
                # 宛先ディレクトリを作成
                new_full_path.parent.mkdir(parents=True, exist_ok=True)
                
                # ディレクトリを移動
                shutil.move(str(old_path), str(new_full_path))
                logger.info(f"✅ {old_dir} → {new_path}")
                moved_count += 1
                
            except Exception as e:
                logger.error(f"❌ {old_dir}: {e}")
    
    logger.info(f"📊 {moved_count}個のディレクトリを移行完了")
    
    # 残ったディレクトリを確認
    remaining = []
    for item in base_path.iterdir():
        if item.is_dir() and item.name not in [
            'elder_tree', '.git', '.elder_guild', '.benchmarks', 
            'migration_backup', 'elders_guild'
        ]:
            remaining.append(item.name)
    
    if remaining:
        logger.warning(f"⚠️ 残っているディレクトリ: {remaining}")
        return False
    else:
        logger.info("✅ すべてのディレクトリがElder Treeに移行完了！")
        return True

if __name__ == "__main__":
    success = execute_complete_migration()
    if success:
        print("🎉 Elder Tree完全移行成功！")
    else:
        print("⚠️ 一部ディレクトリが残っています")