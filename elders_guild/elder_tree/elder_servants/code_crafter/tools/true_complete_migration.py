#!/usr/bin/env python3
"""
🌳 True Complete Elder Tree Migration
本当にすべてを Elder Tree に移行する真の完全移行スクリプト
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, List

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TrueCompleteElderTreeMigrator:
    """本当の完全Elder Tree移行"""
    
    def __init__(self):
        # 環境変数から設定を取得
        try:
            from shared_libs.config import config  
            self.base_path = Path(config.ELDERS_GUILD_HOME)
        except ImportError:
            # fallback to default
            self.base_path = Path("/home/aicompany/ai_co/elders_guild")
        self.elder_tree_path = self.base_path / "elder_tree"
        
    def get_migration_mapping(self) -> Dict[str, str]:
        """真の完全移行マッピング"""
        return {
            # エンシェントエルダー
            "ancient_elder": "elder_tree/ancient_elder/main",
            "ancient_elders": "elder_tree/ancient_elder/legacy",
            
            # クロードエルダー  
            "claude_elder": "elder_tree/claude_elder/main",
            "elder_flow": "elder_tree/claude_elder/flow",
            "cli": "elder_tree/claude_elder/integration/cli",
            "elder_system": "elder_tree/claude_elder/core",
            
            # 4賢者
            "four_sages": "elder_tree/four_sages",
            
            # インフラ・コア
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
        }
    
    def execute_true_migration(self):
        """真の完全移行を実行"""
        logger.info("🌳 TRUE COMPLETE Elder Tree Migration 開始...")
        
        mapping = self.get_migration_mapping()
        
        for old_dir, new_path in mapping.items():
            old_path = self.base_path / old_dir
            new_full_path = self.base_path / new_path
            
            if old_path.exists() and old_path.is_dir():
                try:
                    # 宛先ディレクトリを作成
                    new_full_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # ディレクトリを移動
                    shutil.move(str(old_path), str(new_full_path))
                    logger.info(f"✅ {old_dir} → {new_path}")
                    
                except Exception as e:
                    logger.error(f"❌ {old_dir}: {e}")
        
        # 残ったディレクトリを確認
        remaining = []
        for item in self.base_path.iterdir():
            if item.is_dir() and item.name not in [
                'elder_tree', '.git', '.elder_guild', '.benchmarks', 
                'migration_backup', 'elders_guild'
            ]:
                remaining.append(item.name)
        
        if remaining:
            logger.warning(f"⚠️ 残っているディレクトリ: {remaining}")
        else:
            logger.info("✅ すべてのディレクトリがElder Treeに移行完了！")
    
    def create_root_symlinks(self):
        """ルートレベルのシンボリックリンクを作成"""
        logger.info("🔗 ルートシンボリックリンクを作成中...")
        
        # 重要なディレクトリのシンボリックリンク
        symlinks = {
            "claude_elder": "elder_tree/claude_elder",
            "four_sages": "elder_tree/four_sages", 
            "ancient_elder": "elder_tree/ancient_elder",
            "quality": "elder_tree/elder_servants/quality_tribe",
            "scripts": "elder_tree/elder_servants/dwarf_tribe/tools",
            "tests": "elder_tree/elder_servants/quality_tribe/tests",
            "docs": "elder_tree/ancient_elder/documentation",
        }
        
        for link_name, target_path in symlinks.items():
            link_path = self.base_path / link_name
            target_full = self.base_path / target_path
            
            if not link_path.exists() and target_full.exists():
                try:
                    link_path.symlink_to(target_full)
                    logger.info(f"✅ {link_name} → {target_path}")
                except Exception as e:
                    logger.warning(f"⚠️ {link_name}: {e}")

def main():
    """メイン実行"""
    migrator = TrueCompleteElderTreeMigrator()
    
    print("🌳 TRUE COMPLETE Elder Tree Migration")
    print("=====================================")
    
    # 実行確認
    response = input("本当にすべてをElder Treeに移行しますか？ (yes/no): ")
    if response.lower() != "yes":
        print("移行をキャンセルしました。")
        return
    
    # 真の完全移行実行
    migrator.execute_true_migration()
    
    # シンボリックリンク作成
    migrator.create_root_symlinks()
    
    print("\n✅ TRUE COMPLETE Elder Tree Migration 完了！")

if __name__ == "__main__":
    main()