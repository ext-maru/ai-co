#!/usr/bin/env python3
"""
🌳 Elder Tree Migration Executor
実際のファイル移行を実行するスクリプト
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Tuple

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ElderTreeMigrationExecutor:
    """Elder Tree構造への実際の移行を実行"""
    
    def __init__(self):
        self.base_path = Path("/home/aicompany/ai_co/elders_guild")
        self.elder_tree_path = self.base_path / "elder_tree"
        
    def migrate_servants(self):
        """サーバントファイルを部族別に移行"""
        logger.info("🛡️ サーバントファイルの移行を開始...")
        
        # ドワーフ部族への移行
        dwarf_files = [
            ("elder_servants/dwarf_workshop/code_crafter.py", "elder_servants/dwarf_tribe/code_crafter/code_crafter.py"),
            ("elder_servants/dwarf_workshop/api_forge.py", "elder_servants/dwarf_tribe/forge_master/api_forge.py"),
            ("elder_servants/dwarf_workshop/deployment_forge.py", "elder_servants/dwarf_tribe/artifact_builder/deployment_forge.py"),
            ("elder_servants/dwarf_workshop/cicd_builder.py", "elder_servants/dwarf_tribe/tool_smith/cicd_builder.py"),
        ]
        
        # エルフ部族への移行
        elf_files = [
            ("elder_servants/elf_forest/quality_guardian.py", "elder_servants/elf_tribe/quality_guardian/quality_guardian.py"),
            ("elder_servants/elf_forest/forest_keeper.py", "elder_servants/elf_tribe/forest_keeper/forest_keeper.py"),
            ("elder_servants/elf_forest/harmony_watcher.py", "elder_servants/elf_tribe/harmony_watcher/harmony_watcher.py"),
        ]
        
        # ウィザード部族への移行
        wizard_files = [
            ("elder_servants/rag_wizards/research_wizard.py", "elder_servants/wizard_tribe/research_wizard/research_wizard.py"),
            ("elder_servants/rag_wizards/knowledge_seeker.py", "elder_servants/wizard_tribe/knowledge_seeker/knowledge_seeker.py"),
            ("elder_servants/rag_wizards/pattern_finder.py", "elder_servants/wizard_tribe/pattern_finder/pattern_finder.py"),
        ]
        
        # 品質部族への移行
        quality_files = [
            ("quality_servants/quality_watcher_servant.py", "elder_servants/quality_tribe/quality_watcher/quality_watcher_servant.py"),
            ("quality_servants/test_forge_servant.py", "elder_servants/quality_tribe/test_forge/test_forge_servant.py"),
            ("quality_servants/comprehensive_guardian_servant.py", "elder_servants/quality_tribe/comprehensive_guardian/comprehensive_guardian_servant.py"),
        ]
        
        # すべてのファイルを移行
        all_migrations = dwarf_files + elf_files + wizard_files + quality_files
        
        for src, dst in all_migrations:
            self._migrate_file(src, dst)
    
    def migrate_four_sages(self):
        """4賢者ファイルを移行"""
        logger.info("🧙‍♂️ 4賢者ファイルの移行を開始...")
        
        sage_files = [
            ("four_sages/knowledge/knowledge_sage.py", "four_sages/knowledge_sage/wisdom_base/knowledge_sage.py"),
            ("four_sages/task/task_sage.py", "four_sages/task_sage/tracking/task_sage.py"),
            ("four_sages/incident/incident_sage.py", "four_sages/incident_sage/detection/incident_sage.py"),
            ("four_sages/rag/rag_sage.py", "four_sages/rag_sage/search/rag_sage.py"),
        ]
        
        for src, dst in sage_files:
            self._migrate_file(src, dst)
    
    def migrate_claude_elder(self):
        """クロードエルダー関連ファイルを移行"""
        logger.info("🤖 クロードエルダーファイルの移行を開始...")
        
        claude_files = [
            ("elder_flow/elder_flow_engine.py", "claude_elder/flow/engine/elder_flow_engine.py"),
            ("elder_flow/elder_flow_orchestrator.py", "claude_elder/flow/orchestration/elder_flow_orchestrator.py"),
            ("cli/elder_cli.py", "claude_elder/integration/cli/elder_cli.py"),
            ("elder_system/core/elder_identity.py", "claude_elder/core/identity/elder_identity.py"),
        ]
        
        for src, dst in claude_files:
            self._migrate_file(src, dst)
    
    def migrate_ancient_elder(self):
        """エンシェントエルダー関連ファイルを移行"""
        logger.info("🏛️ エンシェントエルダーファイルの移行を開始...")
        
        ancient_files = [
            ("tests/ancient_magic/test_ancient_spells.py", "ancient_elder/ancient_magic/spells/test_ancient_spells.py"),
            ("ancient_elder/grand_vision.py", "ancient_elder/grand_elder/visions/grand_vision.py"),
        ]
        
        for src, dst in ancient_files:
            self._migrate_file(src, dst)
    
    def _migrate_file(self, src_path: str, dst_path: str):
        """個別ファイルの移行"""
        src_full = self.base_path / src_path
        dst_full = self.elder_tree_path / dst_path
        
        if src_full.exists():
            # 宛先ディレクトリを作成
            dst_full.parent.mkdir(parents=True, exist_ok=True)
            
            # __init__.pyを作成
            init_file = dst_full.parent / "__init__.py"
            if not init_file.exists():
                init_file.write_text('"""エルダーツリー モジュール"""\\n')
            
            # ファイルをコピー
            shutil.copy2(src_full, dst_full)
            logger.info(f"  ✅ {src_path} → elder_tree/{dst_path}")
        else:
            logger.warning(f"  ⚠️ ソースファイルが見つかりません: {src_path}")
    
    def update_imports(self):
        """import文を更新"""
        logger.info("🔧 import文を更新中...")
        
        # Elder Tree内のすべてのPythonファイルを取得
        python_files = list(self.elder_tree_path.rglob("*.py"))
        
        # import更新マップ
        import_updates = [
            # サーバント関連
            ("from elders_guild.elder_tree.elder_servants.dwarf_workshop", "from elders_guild.elder_tree.elder_servants.dwarf_tribe"),
            ("from elders_guild.elder_tree.elder_servants.elf_forest", "from elders_guild.elder_tree.elder_servants.elf_tribe"),
            ("from elders_guild.elder_tree.elder_servants.rag_wizards", "from elders_guild.elder_tree.elder_servants.wizard_tribe"),
            ("from quality_servants", "from elders_guild.elder_tree.elder_servants.quality_tribe"),
            
            # 4賢者関連
            ("from elders_guild.elder_tree.four_sages.knowledge", "from elders_guild.elder_tree.four_sages.knowledge_sage"),
            ("from elders_guild.elder_tree.four_sages.task", "from elders_guild.elder_tree.four_sages.task_sage"),
            ("from elders_guild.elder_tree.four_sages.incident", "from elders_guild.elder_tree.four_sages.incident_sage"),
            ("from elders_guild.elder_tree.four_sages.rag", "from elders_guild.elder_tree.four_sages.rag_sage"),
            
            # クロードエルダー関連
            ("from elder_flow", "from elders_guild.elder_tree.claude_elder.flow"),
            ("from cli", "from elders_guild.elder_tree.claude_elder.integration.cli"),
            
            # import文も同様に
            ("import elders_guild.elder_tree.elder_servants.dwarf_workshop", "import elders_guild.elder_tree.elder_servants.dwarf_tribe"),
            ("import four_sages", "import elders_guild.elder_tree.four_sages"),
        ]
        
        updated_count = 0
        for py_file in python_files:
            try:
                content = py_file.read_text()
                original_content = content
                
                for old_import, new_import in import_updates:
                    content = content.replace(old_import, new_import)
                
                if content != original_content:
                    py_file.write_text(content)
                    updated_count += 1
                    logger.info(f"  ✅ {py_file.relative_to(self.base_path)}")
            except Exception as e:
                logger.error(f"  ❌ {py_file}: {e}")
        
        logger.info(f"📊 {updated_count}個のファイルのimportを更新")
    
    def create_symlinks(self):
        """互換性のためのシンボリックリンクを作成"""
        logger.info("🔗 シンボリックリンクを作成中...")
        
        # 主要なシンボリックリンク
        links = [
            ("elder_servants", "elder_tree/elder_servants"),
            ("four_sages", "elder_tree/four_sages"),
            ("claude_elder", "elder_tree/claude_elder"),
            ("ancient_elder", "elder_tree/ancient_elder"),
        ]
        
        for link_name, target in links:
            link_path = self.base_path / link_name
            target_path = self.base_path / target
            
            if not link_path.exists() and target_path.exists():
                try:
                    link_path.symlink_to(target_path)
                    logger.info(f"  ✅ {link_name} → {target}")
                except Exception as e:
                    logger.warning(f"  ⚠️ {link_name}: {e}")

def main():
    """メイン実行関数"""
    executor = ElderTreeMigrationExecutor()
    
    logger.info("🌳 Elder Tree移行を開始します...")
    
    # 段階的に移行
    executor.migrate_servants()
    executor.migrate_four_sages()
    executor.migrate_claude_elder()
    executor.migrate_ancient_elder()
    
    # import文を更新
    executor.update_imports()
    
    # シンボリックリンクを作成
    executor.create_symlinks()
    
    logger.info("✅ Elder Tree移行が完了しました！")

if __name__ == "__main__":
    main()