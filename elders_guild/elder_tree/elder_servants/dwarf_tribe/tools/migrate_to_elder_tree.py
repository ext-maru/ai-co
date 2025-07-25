#!/usr/bin/env python3
"""
🌳 Elder Tree Migration Script
エルダーズギルドの階層構造を新しいelder_tree構造に移行するスクリプト
"""

import os
import shutil
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import sys

# 環境変数設定のインポート
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared_libs.config import config

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('elder_tree_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ElderTreeMigrator:
    """Elder Tree構造への移行を管理するクラス"""
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            base_path = config.ELDERS_GUILD_HOME
        self.base_path = Path(base_path)
        self.elder_tree_path = self.base_path / "elder_tree"
        self.migration_map = self._create_migration_map()
        self.backup_path = self.base_path / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def _create_migration_map(self) -> Dict[str, str]:
        """移行マッピングを定義"""
        return {
            # Ancient Elder関連
            "ancient_elder": "elder_tree/ancient_elder",
            "ancient_elders": "elder_tree/ancient_elder",
            "tests/ancient_magic": "elder_tree/ancient_elder/ancient_magic",
            
            # Claude Elder関連
            "claude_elder": "elder_tree/claude_elder",
            "elder_flow": "elder_tree/claude_elder/flow",
            "cli": "elder_tree/claude_elder/integration/cli",
            "elder_system": "elder_tree/claude_elder/core",
            
            # 4賢者関連
            "four_sages": "elder_tree/four_sages",
            "four_sages/knowledge": "elder_tree/four_sages/knowledge_sage",
            "four_sages/task": "elder_tree/four_sages/task_sage",
            "four_sages/incident": "elder_tree/four_sages/incident_sage",
            "four_sages/rag": "elder_tree/four_sages/rag_sage",
            
            # サーバント関連
            "elder_servants": "elder_tree/elder_servants",
            "quality_servants": "elder_tree/elder_servants/quality_tribe",
            "elder_servants/dwarf_workshop": "elder_tree/elder_servants/dwarf_tribe",
            "elder_servants/elf_forest": "elder_tree/elder_servants/elf_tribe",
            "elder_servants/rag_wizards": "elder_tree/elder_servants/wizard_tribe",
            "elder_servants/integrations/production": "elder_tree/elder_servants/knight_tribe",
        }
    
    def create_elder_tree_structure(self):
        """Elder Tree構造を作成"""
        logger.info("🌳 Elder Tree構造を作成中...")
        
        # メイン構造
        structure = {
            "elder_tree": {
                "ancient_elder": {
                    "grand_elder": ["decrees", "visions", "wisdom"],
                    "ancient_magic": ["spells", "artifacts", "rituals", "grimoires"],
                    "council": ["meetings", "decisions", "protocols"]
                },
                "claude_elder": {
                    "core": ["identity", "authority", "execution"],
                    "flow": ["engine", "pipeline", "orchestration"],
                    "integration": ["a2a", "cli", "apis"]
                },
                "four_sages": {
                    "knowledge_sage": ["wisdom_base", "learning", "archives"],
                    "task_sage": ["tracking", "planning", "prioritization"],
                    "incident_sage": ["detection", "response", "prevention"],
                    "rag_sage": ["search", "analysis", "recommendations"]
                },
                "elder_servants": {
                    "quality_tribe": ["quality_watcher", "test_forge", "comprehensive_guardian", "iron_will_enforcer"],
                    "dwarf_tribe": ["code_crafter", "forge_master", "artifact_builder", "tool_smith"],
                    "elf_tribe": ["quality_guardian", "forest_keeper", "harmony_watcher", "ecosystem_healer"],
                    "wizard_tribe": ["research_wizard", "knowledge_seeker", "pattern_finder", "insight_oracle"],
                    "knight_tribe": ["crisis_responder", "bug_hunter", "shield_bearer", "rapid_striker"],
                    "coordination": ["tribal_council", "communication_hub", "shared_resources"]
                }
            }
        }
        
        self._create_directories(self.base_path, structure)
        logger.info("✅ Elder Tree構造作成完了")
    
    def _create_directories(self, base: Path, structure: Dict, level=0):
        """再帰的にディレクトリ構造を作成"""
        indent = "  " * level
        for name, content in structure.items():
            path = base / name
            path.mkdir(exist_ok=True)
            logger.info(f"{indent}📁 {path}")
            
            # README.mdを配置
            readme_path = path / "README.md"
            if not readme_path.exists():
                readme_content = f"# {name.replace('_', ' ').title()}\n\n"
                readme_content += f"このディレクトリは{name}に関連するファイルを格納します。\n"
                readme_path.write_text(readme_content)
            
            if isinstance(content, dict):
                self._create_directories(path, content, level + 1)
            elif isinstance(content, list):
                for subdir in content:
                    subpath = path / subdir
                    subpath.mkdir(exist_ok=True)
                    logger.info(f"{indent}  📁 {subpath}")
    
    def backup_current_structure(self):
        """現在の構造をバックアップ"""
        logger.info(f"📦 現在の構造をバックアップ中: {self.backup_path}")
        
        # バックアップ対象のディレクトリ
        backup_targets = [
            "ancient_elder", "ancient_elders", "claude_elder",
            "four_sages", "elder_servants", "quality_servants",
            "elder_flow", "cli", "elder_system"
        ]
        
        for target in backup_targets:
            source = self.base_path / target
            if source.exists():
                dest = self.backup_path / target
                shutil.copytree(source, dest, dirs_exist_ok=True)
                logger.info(f"  ✅ {target} をバックアップ")
    
    def migrate_files(self, dry_run: bool = True):
        """ファイルを新構造に移行"""
        mode = "（ドライラン）" if dry_run else ""
        logger.info(f"📋 ファイル移行を開始 {mode}")
        
        migration_log = []
        
        for old_path, new_path in self.migration_map.items():
            source = self.base_path / old_path
            dest = self.base_path / new_path
            
            if source.exists():
                if dry_run:
                    logger.info(f"  🔄 {old_path} → {new_path}")
                    migration_log.append({
                        "source": str(source),
                        "destination": str(dest),
                        "status": "planned"
                    })
                else:
                    try:
                        if source.is_dir():
                            shutil.copytree(source, dest, dirs_exist_ok=True)
                        else:
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(source, dest)
                        logger.info(f"  ✅ {old_path} → {new_path}")
                        migration_log.append({
                            "source": str(source),
                            "destination": str(dest),
                            "status": "success"
                        })
                    except Exception as e:
                        logger.error(f"  ❌ {old_path}: {e}")
                        migration_log.append({
                            "source": str(source),
                            "destination": str(dest),
                            "status": "failed",
                            "error": str(e)
                        })
        
        # 移行ログを保存
        log_file = self.base_path / "migration_log.json"
        with open(log_file, 'w') as f:
            json.dump(migration_log, f, indent=2)
        logger.info(f"📝 移行ログを保存: {log_file}")
        
        return migration_log
    
    def create_symlinks(self):
        """互換性のためのシンボリックリンクを作成"""
        logger.info("🔗 シンボリックリンクを作成中...")
        
        for old_path, new_path in self.migration_map.items():
            source = self.base_path / old_path
            target = self.base_path / new_path
            
            if not source.exists() and target.exists():
                try:
                    source.parent.mkdir(parents=True, exist_ok=True)
                    source.symlink_to(target)
                    logger.info(f"  ✅ {old_path} → {new_path}")
                except Exception as e:
                    logger.warning(f"  ⚠️ {old_path}: {e}")
    
    def update_imports(self):
        """Pythonファイルのimport文を更新"""
        logger.info("🔧 import文を更新中...")
        
        # import更新マップ
        import_updates = [
            ("from elder_servants", "from elder_tree.elder_servants"),
            ("from four_sages", "from elder_tree.four_sages"),
            ("from claude_elder", "from elder_tree.claude_elder"),
            ("from ancient_elder", "from elder_tree.ancient_elder"),
            ("import elder_servants", "import elder_tree.elder_servants"),
            ("import four_sages", "import elder_tree.four_sages"),
            ("import claude_elder", "import elder_tree.claude_elder"),
            ("import ancient_elder", "import elder_tree.ancient_elder"),
        ]
        
        # Pythonファイルを検索して更新
        python_files = list(self.elder_tree_path.rglob("*.py"))
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
        
        logger.info(f"📊 {updated_count}個のファイルを更新")
    
    def verify_migration(self) -> bool:
        """移行の検証"""
        logger.info("🔍 移行を検証中...")
        
        issues = []
        
        # 必須ディレクトリの存在確認
        required_dirs = [
            "elder_tree/ancient_elder",
            "elder_tree/claude_elder",
            "elder_tree/four_sages",
            "elder_tree/elder_servants"
        ]
        
        for dir_path in required_dirs:
            full_path = self.base_path / dir_path
            if not full_path.exists():
                issues.append(f"必須ディレクトリが存在しません: {dir_path}")
            else:
                logger.info(f"  ✅ {dir_path}")
        
        if issues:
            logger.error("❌ 検証エラー:")
            for issue in issues:
                logger.error(f"  - {issue}")
            return False
        
        logger.info("✅ 移行検証成功")
        return True

def main():
    """メイン実行関数"""
    migrator = ElderTreeMigrator()
    
    print("\n🌳 Elder Tree Migration Tool 🌳")
    print("================================")
    print("1. ドライラン（確認のみ）")
    print("2. 実際に移行を実行")
    print("3. 構造作成のみ")
    print("4. 検証のみ")
    print("0. 終了")
    
    choice = input("\n選択してください (0-4): ")
    
    if choice == "1":
        migrator.create_elder_tree_structure()
        migrator.migrate_files(dry_run=True)
    elif choice == "2":
        confirm = input("⚠️ 実際に移行を実行しますか？ (yes/no): ")
        if confirm.lower() == "yes":
            migrator.backup_current_structure()
            migrator.create_elder_tree_structure()
            migrator.migrate_files(dry_run=False)
            migrator.create_symlinks()
            migrator.update_imports()
            migrator.verify_migration()
        else:
            print("移行をキャンセルしました。")
    elif choice == "3":
        migrator.create_elder_tree_structure()
    elif choice == "4":
        migrator.verify_migration()
    elif choice == "0":
        print("終了します。")
    else:
        print("無効な選択です。")

if __name__ == "__main__":
    main()