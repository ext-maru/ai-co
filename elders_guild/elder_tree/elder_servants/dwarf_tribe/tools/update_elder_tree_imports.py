#!/usr/bin/env python3
"""
🔧 Elder Tree Import Updater
Elder Tree移行後のimport文を一括更新するスクリプト
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import re
import sys

# 環境変数設定のインポート
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared_libs.config import config

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ElderTreeImportUpdater:
    """Elder Tree移行後のimport文更新"""
    
    def __init__(self):
        self.base_path = Path(config.ELDERS_GUILD_HOME)
        self.elder_tree_path = self.base_path / "elder_tree"
        
    def create_import_mapping(self) -> List[Tuple[str, str]]:
        """import文の更新マッピングを作成"""
        logger.info("📋 import更新マッピングを作成...")
        
        # 基本的なパス更新
        mappings = [
            # サーバント関連
            (r'from elder_servants\.', 'from elders_guild.elder_tree.elder_servants.'),
            (r'import elder_servants\.', 'import elders_guild.elder_tree.elder_servants.'),
            (r'from quality_servants\.', 'from elders_guild.elder_tree.elder_servants.quality_tribe.'),
            (r'import quality_servants\.', 'import elders_guild.elder_tree.elder_servants.quality_tribe.'),
            
            # 特定ディレクトリの詳細マッピング
            (r'from elder_servants\.dwarf_workshop', 'from elders_guild.elder_tree.elder_servants.dwarf_tribe'),
            (r'from elder_servants\.elf_forest', 'from elders_guild.elder_tree.elder_servants.elf_tribe'),
            (r'from elder_servants\.rag_wizards', 'from elders_guild.elder_tree.elder_servants.wizard_tribe'),
            (r'from elder_servants\.base', 'from elders_guild.elder_tree.elder_servants.coordination.shared_resources'),
            (r'from elder_servants\.registry', 'from elders_guild.elder_tree.elder_servants.coordination.shared_resources'),
            (r'from elder_servants\.coordination', 'from elders_guild.elder_tree.elder_servants.coordination.shared_resources'),
            
            # import文も同様に
            (r'import elder_servants\.dwarf_workshop', 'import elders_guild.elder_tree.elder_servants.dwarf_tribe'),
            (r'import elder_servants\.elf_forest', 'import elders_guild.elder_tree.elder_servants.elf_tribe'),
            (r'import elder_servants\.rag_wizards', 'import elders_guild.elder_tree.elder_servants.wizard_tribe'),
            (r'import elder_servants\.base', 'import elders_guild.elder_tree.elder_servants.coordination.shared_resources'),
            
            # 4賢者関連（将来の拡張用）
            (r'from four_sages\.', 'from elders_guild.elder_tree.four_sages.'),
            (r'import four_sages\.', 'import elders_guild.elder_tree.four_sages.'),
            
            # クロードエルダー関連（将来の拡張用）
            (r'from claude_elder\.', 'from elders_guild.elder_tree.claude_elder.'),
            (r'import claude_elder\.', 'import elders_guild.elder_tree.claude_elder.'),
            
            # エンシェントエルダー関連（将来の拡張用）
            (r'from ancient_elder\.', 'from elders_guild.elder_tree.ancient_elder.'),
            (r'import ancient_elder\.', 'import elders_guild.elder_tree.ancient_elder.'),
        ]
        
        logger.info(f"📊 {len(mappings)}個のimport更新パターンを作成")
        return mappings
    
    def update_file_imports(self, file_path: Path, mappings: List[Tuple[str, str]]) -> bool:
        """単一ファイルのimport文を更新"""
        try:
            content = file_path.read_text(encoding='utf-8')
            original_content = content
            
            # 各マッピングを適用
            for old_pattern, new_pattern in mappings:
                content = re.sub(old_pattern, new_pattern, content)
            
            # 変更がある場合のみファイルを更新
            if content != original_content:
                file_path.write_text(content, encoding='utf-8')
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"  ❌ {file_path}: {e}")
            return False
    
    def update_all_imports(self):
        """全ファイルのimport文を更新"""
        logger.info("🔧 import文の一括更新を開始...")
        
        mappings = self.create_import_mapping()
        
        # Elder Tree内のすべてのPythonファイルを取得
        python_files = list(self.elder_tree_path.rglob("*.py"))
        
        # プロジェクト全体のPythonファイルも対象にする
        project_python_files = list(self.base_path.rglob("*.py"))
        
        # Elder Tree以外のファイルもチェック
        all_files = set(python_files + project_python_files)
        
        updated_count = 0
        total_files = len(all_files)
        
        for py_file in all_files:
            # __pycache__や隠しファイルはスキップ
            if '__pycache__' in str(py_file) or py_file.name.startswith('.'):
                continue
                
            if self.update_file_imports(py_file, mappings):
                updated_count += 1
                logger.info(f"  ✅ {py_file.relative_to(self.base_path)}")
        
        logger.info(f"📊 {updated_count}/{total_files}個のファイルを更新")
    
    def verify_imports(self):
        """import文の妥当性を検証"""
        logger.info("🔍 import文の検証を実行...")
        
        python_files = list(self.elder_tree_path.rglob("*.py"))
        issue_count = 0
        
        for py_file in python_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # 古いパターンが残っていないかチェック
                old_patterns = [
                    r'from elder_servants\.',
                    r'from quality_servants\.',
                    r'import elder_servants\.',
                    r'import quality_servants\.',
                ]
                
                for pattern in old_patterns:
                    if re.search(pattern, content):
                        logger.warning(f"  ⚠️ 古いimportが残存: {py_file.relative_to(self.base_path)}")
                        issue_count += 1
                        break
                        
            except Exception as e:
                logger.error(f"  ❌ {py_file}: {e}")
        
        if issue_count == 0:
            logger.info("✅ import文の検証完了（問題なし）")
        else:
            logger.warning(f"⚠️ {issue_count}個のファイルに問題があります")

def main():
    """メイン実行関数"""
    updater = ElderTreeImportUpdater()
    
    print("🔧 Elder Tree Import更新を開始します...")
    print("======================================")
    
    # 1. import文を更新
    updater.update_all_imports()
    
    # 2. 検証
    updater.verify_imports()
    
    print("\n✅ Elder Tree Import更新が完了しました！")

if __name__ == "__main__":
    main()