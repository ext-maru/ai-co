#!/usr/bin/env python3
"""
🌳 Complete Elder Tree Migration
全サーバントファイルをElder Tree構造に完全移行するスクリプト
"""

import os
import shutil
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CompleteElderTreeMigrator:
    """Elder Tree構造への完全移行を実行"""
    
    def __init__(self):
        self.base_path = Path("/home/aicompany/ai_co/elders_guild")
        self.elder_tree_path = self.base_path / "elder_tree"
        self.backup_path = self.base_path / "migration_backup"
        
    def create_complete_migration_map(self) -> Dict[str, str]:
        """完全な移行マッピングを作成"""
        logger.info("📋 完全移行マッピングを作成中...")
        
        migration_map = {}
        
        # === 品質部族 (Quality Tribe) ===
        quality_files = [
            "quality_servants/quality_watcher_servant.py",
            "quality_servants/quality_watcher_judgment.py", 
            "quality_servants/test_forge_servant.py",
            "quality_servants/test_forge_judgment.py",
            "quality_servants/comprehensive_guardian_servant.py",
            "quality_servants/__init__.py",
            # elder_servants内の品質関連
            "elder_servants/quality_watcher_judgment.py",
            "elder_servants/test_forge_judgment.py",
        ]
        
        for file_path in quality_files:
            if "quality_watcher" in file_path:
                dest = f"elder_servants/quality_tribe/quality_watcher/{Path(file_path).name}"
            elif "test_forge" in file_path:
                dest = f"elder_servants/quality_tribe/test_forge/{Path(file_path).name}"
            elif "comprehensive" in file_path:
                dest = f"elder_servants/quality_tribe/comprehensive_guardian/{Path(file_path).name}"
            elif "__init__.py" in file_path:
                dest = f"elder_servants/quality_tribe/{Path(file_path).name}"
            migration_map[file_path] = dest
        
        # === ドワーフ部族 (Dwarf Tribe) ===
        dwarf_workshop_files = self._get_all_files("elder_servants/dwarf_workshop")
        for file_path in dwarf_workshop_files:
            filename = Path(file_path).name
            if "code_crafter" in filename.lower() or "crafter" in filename.lower():
                dest = f"elder_servants/dwarf_tribe/code_crafter/{filename}"
            elif "forge" in filename.lower() or "api" in filename.lower():
                dest = f"elder_servants/dwarf_tribe/forge_master/{filename}"
            elif "build" in filename.lower() or "deploy" in filename.lower() or "artifact" in filename.lower():
                dest = f"elder_servants/dwarf_tribe/artifact_builder/{filename}"
            elif "tool" in filename.lower() or "cicd" in filename.lower():
                dest = f"elder_servants/dwarf_tribe/tool_smith/{filename}"
            else:
                dest = f"elder_servants/dwarf_tribe/code_crafter/{filename}"  # デフォルト
            migration_map[file_path] = dest
        
        # === エルフ部族 (Elf Tribe) ===
        elf_forest_files = self._get_all_files("elder_servants/elf_forest")
        for file_path in elf_forest_files:
            filename = Path(file_path).name
            if "quality_guardian" in filename.lower() or "guardian" in filename.lower():
                dest = f"elder_servants/elf_tribe/quality_guardian/{filename}"
            elif "forest_keeper" in filename.lower() or "keeper" in filename.lower():
                dest = f"elder_servants/elf_tribe/forest_keeper/{filename}"
            elif "harmony" in filename.lower() or "watcher" in filename.lower():
                dest = f"elder_servants/elf_tribe/harmony_watcher/{filename}"
            elif "healer" in filename.lower() or "ecosystem" in filename.lower():
                dest = f"elder_servants/elf_tribe/ecosystem_healer/{filename}"
            else:
                dest = f"elder_servants/elf_tribe/quality_guardian/{filename}"  # デフォルト
            migration_map[file_path] = dest
        
        # === ウィザード部族 (Wizard Tribe) ===
        rag_wizards_files = self._get_all_files("elder_servants/rag_wizards")
        for file_path in rag_wizards_files:
            filename = Path(file_path).name
            if "research" in filename.lower() or "wizard" in filename.lower():
                dest = f"elder_servants/wizard_tribe/research_wizard/{filename}"
            elif "knowledge" in filename.lower() or "seeker" in filename.lower():
                dest = f"elder_servants/wizard_tribe/knowledge_seeker/{filename}"
            elif "pattern" in filename.lower() or "finder" in filename.lower():
                dest = f"elder_servants/wizard_tribe/pattern_finder/{filename}"
            elif "insight" in filename.lower() or "oracle" in filename.lower():
                dest = f"elder_servants/wizard_tribe/insight_oracle/{filename}"
            else:
                dest = f"elder_servants/wizard_tribe/research_wizard/{filename}"  # デフォルト
            migration_map[file_path] = dest
        
        # === ナイト部族 (Knight Tribe) ===
        # インシデント対応関連
        incident_files = [
            "elder_servants/integrations/production",
            "elder_servants/fallback",
        ]
        
        for dir_path in incident_files:
            if self.base_path.joinpath(dir_path).is_dir():
                files = self._get_all_files(dir_path)
                for file_path in files:
                    filename = Path(file_path).name
                    if "crisis" in filename.lower() or "emergency" in filename.lower():
                        dest = f"elder_servants/knight_tribe/crisis_responder/{filename}"
                    elif "bug" in filename.lower() or "hunter" in filename.lower():
                        dest = f"elder_servants/knight_tribe/bug_hunter/{filename}"
                    elif "shield" in filename.lower() or "guard" in filename.lower():
                        dest = f"elder_servants/knight_tribe/shield_bearer/{filename}"
                    elif "rapid" in filename.lower() or "quick" in filename.lower():
                        dest = f"elder_servants/knight_tribe/rapid_striker/{filename}"
                    else:
                        dest = f"elder_servants/knight_tribe/crisis_responder/{filename}"  # デフォルト
                    migration_map[file_path] = dest
        
        # === 調整部族 (Coordination) ===
        coordination_files = self._get_all_files("elder_servants/coordination")
        coordination_files.extend(self._get_all_files("elder_servants/registry"))
        coordination_files.extend(self._get_all_files("elder_servants/selection"))
        coordination_files.extend(self._get_all_files("elder_servants/load_balancing"))
        
        for file_path in coordination_files:
            filename = Path(file_path).name
            if "council" in filename.lower() or "meeting" in filename.lower():
                dest = f"elder_servants/coordination/tribal_council/{filename}"
            elif "communication" in filename.lower() or "hub" in filename.lower():
                dest = f"elder_servants/coordination/communication_hub/{filename}"
            else:
                dest = f"elder_servants/coordination/shared_resources/{filename}"
            migration_map[file_path] = dest
        
        # === ベースファイル ===
        base_files = self._get_all_files("elder_servants/base")
        for file_path in base_files:
            filename = Path(file_path).name
            dest = f"elder_servants/coordination/shared_resources/{filename}"
            migration_map[file_path] = dest
        
        logger.info(f"📊 {len(migration_map)}個のファイル移行を計画")
        return migration_map
    
    def _get_all_files(self, dir_path: str) -> List[str]:
        """指定ディレクトリ内のすべてのファイルを取得"""
        full_path = self.base_path / dir_path
        if not full_path.exists():
            return []
        
        files = []
        for item in full_path.rglob("*"):
            if item.is_file() and not item.name.startswith('.') and '__pycache__' not in str(item):
                relative_path = item.relative_to(self.base_path)
                files.append(str(relative_path))
        return files
    
    def create_backup(self):
        """移行前にバックアップを作成"""
        logger.info("📦 移行前バックアップを作成中...")
        
        if self.backup_path.exists():
            shutil.rmtree(self.backup_path)
        
        backup_dirs = ["elder_servants", "quality_servants", "elder_tree"]
        
        for dir_name in backup_dirs:
            source = self.base_path / dir_name
            if source.exists():
                dest = self.backup_path / dir_name
                shutil.copytree(source, dest)
                logger.info(f"  ✅ {dir_name} をバックアップ")
    
    def execute_migration(self, migration_map: Dict[str, str]):
        """移行を実行"""
        logger.info("🚀 ファイル移行を実行中...")
        
        success_count = 0
        error_count = 0
        
        for src_path, dst_path in migration_map.items():
            try:
                src_full = self.base_path / src_path
                dst_full = self.elder_tree_path / dst_path
                
                if src_full.exists():
                    # 宛先ディレクトリを作成
                    dst_full.parent.mkdir(parents=True, exist_ok=True)
                    
                    # __init__.pyを作成
                    init_file = dst_full.parent / "__init__.py"
                    if not init_file.exists():
                        init_file.write_text('"""Elder Tree サーバント モジュール"""\\n')
                    
                    # ファイルをコピー
                    shutil.copy2(src_full, dst_full)
                    logger.info(f"  ✅ {src_path} → elder_tree/{dst_path}")
                    success_count += 1
                else:
                    logger.warning(f"  ⚠️ ソースファイルが見つかりません: {src_path}")
            except Exception as e:
                logger.error(f"  ❌ {src_path}: {e}")
                error_count += 1
        
        logger.info(f"📊 移行結果: 成功={success_count}, エラー={error_count}")
    
    def cleanup_old_directories(self):
        """旧ディレクトリをクリーンアップ"""
        logger.info("🧹 旧ディレクトリをクリーンアップ中...")
        
        # 移行元ディレクトリを削除
        old_dirs = ["elder_servants", "quality_servants"]
        
        for dir_name in old_dirs:
            old_path = self.base_path / dir_name
            if old_path.exists():
                shutil.rmtree(old_path)
                logger.info(f"  ✅ {dir_name} を削除")
        
        # new_systemも不要なら削除
        new_system_path = self.base_path / "new_system"
        if new_system_path.exists():
            config_only = len(list(new_system_path.rglob("*"))) <= 3  # config以外にファイルがない
            if config_only:
                shutil.rmtree(new_system_path)
                logger.info("  ✅ new_system を削除")
        
        # シンボリックリンクを削除
        quality_tribe_link = self.base_path / "quality_tribe"
        if quality_tribe_link.is_symlink():
            quality_tribe_link.unlink()
            logger.info("  ✅ quality_tribe シンボリックリンクを削除")
    
    def create_new_symlinks(self):
        """新しいシンボリックリンクを作成"""
        logger.info("🔗 新しいシンボリックリンクを作成中...")
        
        links = [
            ("elder_servants", "elder_tree/elder_servants"),
            ("quality_servants", "elder_tree/elder_servants/quality_tribe"),
        ]
        
        for link_name, target in links:
            link_path = self.base_path / link_name
            target_path = self.elder_tree_path / target.replace("elder_tree/", "")
            
            if not link_path.exists() and target_path.exists():
                try:
                    link_path.symlink_to(target_path)
                    logger.info(f"  ✅ {link_name} → {target}")
                except Exception as e:
                    logger.warning(f"  ⚠️ {link_name}: {e}")

def main():
    """メイン実行関数"""
    migrator = CompleteElderTreeMigrator()
    
    print("🌳 Elder Tree完全移行を開始します...")
    print("================================")
    
    # 1. バックアップ作成
    migrator.create_backup()
    
    # 2. 移行マップ作成
    migration_map = migrator.create_complete_migration_map()
    
    # 3. 移行実行
    migrator.execute_migration(migration_map)
    
    # 4. 旧ディレクトリクリーンアップ
    migrator.cleanup_old_directories()
    
    # 5. 新しいシンボリックリンク作成
    migrator.create_new_symlinks()
    
    print("\n✅ Elder Tree完全移行が完了しました！")
    print(f"📁 Elder Tree場所: {migrator.elder_tree_path}")
    print(f"📦 バックアップ場所: {migrator.backup_path}")

if __name__ == "__main__":
    main()