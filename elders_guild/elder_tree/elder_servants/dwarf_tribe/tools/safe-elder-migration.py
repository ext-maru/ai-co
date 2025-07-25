#!/usr/bin/env python3
"""
🏛️ Safe Elder Tree Migration
安全で段階的なElder Tree移行（シンボリックリンク不使用）
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, List
import time

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SafeElderTreeMigrator:
    """安全なElder Tree移行"""
    
    def __init__(self):
        self.base_path = Path("/home/aicompany/ai_co")
        self.elder_tree_path = self.base_path / "elders_guild" / "elder_tree"
        
        # バックアップディレクトリ
        timestamp = int(time.time())
        self.backup_path = self.base_path / f"migration_backup_{timestamp}"
        
    def create_backup(self, paths: List[Path]):
        """重要ディレクトリのバックアップ作成"""
        logger.info(f"📦 バックアップ作成中: {self.backup_path}")
        
        self.backup_path.mkdir(exist_ok=True)
        
        for path in paths:
            if path.exists():
                backup_dest = self.backup_path / path.name
                logger.info(f"  {path.name} をバックアップ中...")
                shutil.copytree(path, backup_dest, dirs_exist_ok=True)
                
    def get_safe_migration_mapping(self) -> Dict[Path, Path]:
        """安全な移行マッピング"""
        base = self.base_path
        elder_tree = self.elder_tree_path
        
        return {
            # 4賢者関連ファイル（libs配下）
            base / "libs" / "incident_sage.py": elder_tree / "four_sages" / "incident" / "incident_sage.py",
            base / "libs" / "knowledge_sage.py": elder_tree / "four_sages" / "knowledge" / "knowledge_sage.py", 
            base / "libs" / "rag_sage.py": elder_tree / "four_sages" / "rag" / "rag_sage.py",
            base / "libs" / "task_sage.py": elder_tree / "four_sages" / "task" / "task_sage.py",
            
            # Elder Flow関連
            base / "libs" / "elder_flow_orchestrator.py": elder_tree / "claude_elder" / "flow" / "elder_flow" / "elder_flow_orchestrator.py",
            base / "libs" / "elder_flow_quality_gate.py": elder_tree / "claude_elder" / "flow" / "engine" / "elder_flow_quality_gate.py",
            
            # Elder Servant関連
            base / "libs" / "elder_servants_coordination_system.py": elder_tree / "elder_servants" / "coordination" / "elder_servants_coordination_system.py",
            
            # 品質関連
            base / "libs" / "elders_code_quality_engine.py": elder_tree / "elder_servants" / "quality_tribe" / "engines" / "elders_code_quality_engine.py",
            base / "libs" / "automated_code_review.py": elder_tree / "elder_servants" / "quality_tribe" / "engines" / "automated_code_review.py",
            
            # 重要ツール（scripts配下）
            base / "scripts" / "elder-flow": elder_tree / "elder_servants" / "dwarf_tribe" / "tools" / "elder-flow",
            base / "scripts" / "ai-elder-cast": elder_tree / "elder_servants" / "dwarf_tribe" / "tools" / "ai-elder-cast",
            base / "scripts" / "git-feature": elder_tree / "elder_servants" / "dwarf_tribe" / "tools" / "git-feature",
        }
    
    def migrate_single_file(self, source: Path, dest: Path) -> bool:
        """単一ファイルの安全な移行"""
        try:
            if not source.exists():
                logger.warning(f"⚠️ ソースファイルが存在しません: {source}")
                return False
                
            # 宛先ディレクトリ作成
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # ファイルコピー（移動ではなくコピーで安全性確保）
            shutil.copy2(source, dest)
            logger.info(f"✅ {source.name} -> {dest.relative_to(self.elder_tree_path)}")
            return True
            
        except Exception as e:
            logger.error(f"❌ {source.name}: {e}")
            return False
    
    def migrate_directory_structure(self):
        """重要ディレクトリ構造の移行"""
        logger.info("📁 ディレクトリ構造移行中...")
        
        # 重要ディレクトリの一括移行
        directory_mappings = {
            self.base_path / "libs" / "four_sages": self.elder_tree_path / "four_sages",
            self.base_path / "tests": self.elder_tree_path / "elder_servants" / "quality_tribe" / "tests",
            self.base_path / "docs": self.elder_tree_path / "ancient_elder" / "documentation",
        }
        
        for source_dir, dest_dir in directory_mappings.items():
            if source_dir.exists() and source_dir.is_dir():
                try:
                    dest_dir.parent.mkdir(parents=True, exist_ok=True)
                    
                    # ディレクトリ内容をコピー
                    if dest_dir.exists():
                        # 既存の場合はマージ
                        shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
                    else:
                        # 新規の場合はコピー
                        shutil.copytree(source_dir, dest_dir)
                        
                    logger.info(f"✅ {source_dir.name} -> {dest_dir.relative_to(self.elder_tree_path)}")
                    
                except Exception as e:
                    logger.error(f"❌ {source_dir.name}: {e}")
    
    def update_import_paths(self):
        """Elder Tree移行後のimport文更新"""
        logger.info("🔧 Import文更新中...")
        
        # Elder Tree内のPythonファイルを検索
        python_files = list(self.elder_tree_path.rglob("*.py"))
        
        # 基本的なimport文の更新
        old_to_new_imports = {
            "from elders_guild.elder_tree.": "from elders_guild.elder_tree.",
            "import elders_guild.elder_tree.": "import elders_guild.elder_tree.",
            "from elders_guild.elder_tree.elder_servants.dwarf_tribe.tools.": "from elders_guild.elder_tree.elder_servants.dwarf_tribe.tools.",
        }
        
        updated_count = 0
        for py_file in python_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                original_content = content
                
                for old_import, new_import in old_to_new_imports.items():
                    content = content.replace(old_import, new_import)
                
                if content != original_content:
                    py_file.write_text(content, encoding='utf-8')
                    updated_count += 1
                    logger.info(f"🔧 Updated imports in {py_file.name}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Import更新エラー {py_file.name}: {e}")
        
        logger.info(f"✅ {updated_count}個のファイルのimport文を更新完了")
    
    def execute_safe_migration(self):
        """安全な移行実行"""
        logger.info("🏛️ Safe Elder Tree Migration 開始...")
        
        # Step 1: バックアップ作成
        important_paths = [
            self.base_path / "libs",
            self.base_path / "scripts", 
            self.base_path / "tests",
            self.base_path / "docs"
        ]
        self.create_backup(important_paths)
        
        # Step 2: 重要ファイルの個別移行
        logger.info("📄 重要ファイル移行中...")
        migration_mapping = self.get_safe_migration_mapping()
        
        success_count = 0
        for source, dest in migration_mapping.items():
            if self.migrate_single_file(source, dest):
                success_count += 1
        
        logger.info(f"✅ {success_count}/{len(migration_mapping)} ファイル移行完了")
        
        # Step 3: ディレクトリ構造移行
        self.migrate_directory_structure()
        
        # Step 4: Import文更新
        self.update_import_paths()
        
        # Step 5: 環境設定作成
        self.create_elder_config()
        
        logger.info("✅ Safe Elder Tree Migration 完了！")
        logger.info(f"📦 バックアップ場所: {self.backup_path}")
    
    def create_elder_config(self):
        """Elder Tree設定ファイル作成"""
        config_path = self.elder_tree_path / "elder_servants" / "coordination" / "shared_resources" / "config" / "elder_tree.conf"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_content = f"""
# Elder Tree Configuration
ELDER_HOME={self.elder_tree_path}
ELDER_TOOLS={self.elder_tree_path}/elder_servants/dwarf_tribe/tools
ELDER_SAGES={self.elder_tree_path}/four_sages
ELDER_SERVANTS={self.elder_tree_path}/elder_servants
ELDER_BACKUP={self.backup_path}

# Migration Info
MIGRATION_DATE={time.strftime('%Y-%m-%d %H:%M:%S')}
MIGRATION_TYPE=Safe Migration
"""
        
        config_path.write_text(config_content.strip())
        logger.info(f"✅ 設定ファイル作成: {config_path}")

def main():
    """メイン実行"""
    migrator = SafeElderTreeMigrator()
    
    print("🏛️ Safe Elder Tree Migration")
    print("============================")
    print("⚠️ この操作は重要ファイルをElder Tree構造に移行します")
    print("💾 自動的にバックアップが作成されます")
    print("")
    
    # 実行確認
    response = input("安全な移行を実行しますか？ (yes/no): ")
    if response.lower() != "yes":
        print("移行をキャンセルしました。")
        return
    
    # 安全な移行実行
    migrator.execute_safe_migration()
    
    print("\n🎉 Safe Elder Tree Migration 完了！")
    print("💡 次に環境設定を実行してください:")
    print("   ./elders_guild/elder_tree/elder_servants/dwarf_tribe/tools/elder-env-setup.sh")

if __name__ == "__main__":
    main()