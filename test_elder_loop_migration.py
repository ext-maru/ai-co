#!/usr/bin/env python3
"""
🧪 Elder Loop Migration Tests
Elder Loop移行システムのTDDテスト
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# テスト対象のインポート
sys.path.append(str(Path(__file__).parent))
from elder_loop_complete_migration import ElderLoopCompleteMigrator

class TestElderLoopMigration(unittest.TestCase):
    """Elder Loop Migration テストスイート"""
    
    def setUp(self):
        """テストセットアップ"""
        self.test_dir = Path(tempfile.mkdtemp(prefix="elder_loop_test_"))
        self.migrator = ElderLoopCompleteMigrator()
        # テスト用にベースパスを変更
        self.migrator.base_path = self.test_dir
        self.migrator.elder_tree_path = self.test_dir / "elders_guild" / "elder_tree"
        
        # テストディレクトリ構造作成
        self._create_test_structure()
    
    def tearDown(self):
        """テスト後処理"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def _create_test_structure(self):
        """テスト用ディレクトリ構造作成"""
        # libs/テストファイル作成
        libs_dir = self.test_dir / "libs"
        libs_dir.mkdir(parents=True)
        
        (libs_dir / "incident_sage.py").write_text("# Incident Sage")
        (libs_dir / "knowledge_sage.py").write_text("# Knowledge Sage")
        (libs_dir / "rag_sage.py").write_text("# RAG Sage")
        (libs_dir / "task_sage.py").write_text("# Task Sage")
        (libs_dir / "elder_flow_orchestrator.py").write_text("# Elder Flow")
        (libs_dir / "elder_servant.py").write_text("# Elder Servant")
        (libs_dir / "quality_engine.py").write_text("# Quality Engine")
        (libs_dir / "other_lib.py").write_text("# Other Library")
        
        # scripts/テストファイル作成
        scripts_dir = self.test_dir / "scripts"
        scripts_dir.mkdir(parents=True)
        
        (scripts_dir / "git-feature").write_text("#!/bin/bash\n# Git Feature")
        (scripts_dir / "elder-flow").write_text("#!/bin/bash\n# Elder Flow")
        (scripts_dir / "quality-check.py").write_text("# Quality Check")
        
        # Elder Tree基本構造作成
        self.migrator.elder_tree_path.mkdir(parents=True)
        for subdir in ["four_sages", "claude_elder", "elder_servants", "ancient_elder"]:
            (self.migrator.elder_tree_path / subdir).mkdir(parents=True)
    
    def test_analyze_unmigrated_files(self):
        """未移行ファイル分析テスト"""
        unmigrated = self.migrator.analyze_unmigrated_files()
        
        # libs Pythonファイル確認
        self.assertEqual(len(unmigrated["libs_python"]), 8)
        self.assertTrue(any("incident_sage.py" in str(f) for f in unmigrated["libs_python"]))
        
        # scripts確認
        self.assertEqual(len(unmigrated["scripts_shell"]), 2)  # git-feature, elder-flow
        self.assertEqual(len(unmigrated["scripts_python"]), 1)  # quality-check.py
    
    def test_elder_tree_mapping_creation(self):
        """Elder Tree マッピング作成テスト"""
        unmigrated = self.migrator.analyze_unmigrated_files()
        mapping = self.migrator.create_elder_tree_mapping(unmigrated)
        
        # 4賢者マッピング確認
        incident_files = [str(dest) for src, dest in mapping.items() if "incident_sage" in str(src)]
        self.assertTrue(any("four_sages/incident" in f for f in incident_files))
        
        # Elder Flow マッピング確認
        elder_flow_files = [str(dest) for src, dest in mapping.items() if "elder_flow" in str(src)]
        self.assertTrue(any("claude_elder/flow" in f for f in elder_flow_files))
        
        # scripts マッピング確認
        script_files = [str(dest) for src, dest in mapping.items() if "git-feature" in str(src)]
        self.assertTrue(any("dwarf_tribe/tools" in f for f in script_files))
    
    def test_migration_batch_execution(self):
        """バッチ移行実行テスト"""
        unmigrated = self.migrator.analyze_unmigrated_files()
        mapping = self.migrator.create_elder_tree_mapping(unmigrated)
        
        success_count, error_count, errors = self.migrator.execute_migration_batch(mapping)
        
        # 成功カウント確認
        self.assertGreater(success_count, 0)
        self.assertEqual(error_count, 0)
        
        # 実際のファイル移行確認
        four_sages_dir = self.migrator.elder_tree_path / "four_sages"
        incident_files = list(four_sages_dir.rglob("*incident_sage*"))
        self.assertGreater(len(incident_files), 0)
    
    def test_phase4_verification(self):
        """Phase 4厳密検証テスト"""
        # まず移行実行
        unmigrated = self.migrator.analyze_unmigrated_files()
        mapping = self.migrator.create_elder_tree_mapping(unmigrated)
        self.migrator.execute_migration_batch(mapping)
        
        # 検証実行
        expected_files = len(unmigrated["libs_python"]) + len(unmigrated["scripts_python"])
        is_passed, migration_rate, issues = self.migrator.phase4_strict_verification(expected_files)
        
        # 検証結果確認
        self.assertIsInstance(migration_rate, float)
        self.assertGreaterEqual(migration_rate, 0)
        self.assertIsInstance(issues, list)
    
    def test_naming_conventions(self):
        """命名規則テスト"""
        conventions = self.migrator.get_elder_naming_conventions()
        
        # 基本命名規則確認
        self.assertIn("libs", conventions)
        self.assertIn("scripts", conventions)
        self.assertEqual(conventions["libs"], "elder_servants")
        self.assertEqual(conventions["scripts"], "dwarf_tribe/tools")
    
    def test_quality_threshold(self):
        """品質基準テスト"""
        self.assertEqual(self.migrator.quality_threshold, 95)
        self.assertGreater(self.migrator.phase4_max_iterations, 0)

class TestElderLoopIntegration(unittest.TestCase):
    """Elder Loop統合テスト"""
    
    def test_elder_loop_quality_standards(self):
        """Elder Loop品質基準テスト"""
        # Elder Loop品質基準の確認
        migrator = ElderLoopCompleteMigrator()
        
        # Phase 1-7の完全実行フロー確認
        self.assertTrue(hasattr(migrator, 'analyze_unmigrated_files'))
        self.assertTrue(hasattr(migrator, 'create_elder_tree_mapping'))
        self.assertTrue(hasattr(migrator, 'execute_migration_batch'))
        self.assertTrue(hasattr(migrator, 'phase4_strict_verification'))
        self.assertTrue(hasattr(migrator, 'update_all_imports'))
        self.assertTrue(hasattr(migrator, 'execute_elder_loop'))
        
        # 品質基準確認
        self.assertGreaterEqual(migrator.quality_threshold, 95)

if __name__ == "__main__":
    # Elder Loop TDDテスト実行
    unittest.main(verbosity=2)