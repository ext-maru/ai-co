#!/usr/bin/env python3
"""
Auto Issue Processor 厳格監査テスト
生成品質、ロック機能、テンプレートシステムの包括的検証
"""

import unittest
import tempfile
import shutil
import os
import sys
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import asyncio

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 相対インポートに変更
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from libs.code_generation.template_manager import CodeGenerationTemplateManager
from libs.issue_processing_lock import IssueProcessingLockManager, get_global_lock_manager


class TestAutoIssueProcessorQualityAudit(unittest.TestCase):
    """Auto Issue Processor品質監査テスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.template_manager = CodeGenerationTemplateManager()
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """テストクリーンアップ"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_enhanced_template_disabled(self):
        """Enhanced版テンプレートが無効化されているか確認"""
        # generate_codeメソッドのデフォルト引数を確認
        import inspect
        sig = inspect.signature(self.template_manager.generate_code)
        use_enhanced_default = sig.parameters['use_enhanced'].default
        
        self.assertFalse(use_enhanced_default, 
                        "Enhanced版テンプレートはデフォルトで無効化されている必要があります")
    
    def test_template_variables_exist(self):
        """必須テンプレート変数が存在するか確認"""
        # Issue情報を作成
        issue_number = 999
        issue_title = "Test Issue"
        issue_body = "Test body"
        
        # コンテキストを生成（非同期関数のため同期実行）
        async def create_context():
            return await self.template_manager.create_context_from_issue(
                issue_number, issue_title, issue_body
            )
        
        context = asyncio.run(create_context())
        
        # 必須変数の確認
        required_vars = [
            'issue_number', 'issue_title', 'issue_body',
            'class_name', 'module_name', 'tech_stack',
            'enhanced_imports', 'naming_guide', 'error_handling_guide'
        ]
        
        for var in required_vars:
            self.assertIn(var, context, f"必須変数 '{var}' がコンテキストに存在しません")
        
        # enhanced_importsが配列であることを確認
        self.assertIsInstance(context['enhanced_imports'], list,
                            "enhanced_importsは配列である必要があります")
        
        # naming_guideとerror_handling_guideが辞書であることを確認
        self.assertIsInstance(context['naming_guide'], dict,
                            "naming_guideは辞書である必要があります")
        self.assertIsInstance(context['error_handling_guide'], dict,
                            "error_handling_guideは辞書である必要があります")
    
    def test_generated_code_quality(self):
        """生成されるコードの品質チェック"""
        # テスト用コンテキスト
        context = {
            "issue_number": 999,
            "issue_title": "Test Issue",
            "issue_body": "Test implementation",
            "class_name": "Issue999Implementation",
            "module_name": "issue_999_solution",
            "tech_stack": "web",
            "requirements": {"imports": [], "classes": [], "functions": []},
            "imports": ["from typing import Dict, Any", "import logging"],
            "timestamp": "2025-07-22",
            "enhanced_imports": [],
            "naming_guide": {
                "suggested_class_name": "Issue999Implementation",
                "suggested_function_names": ["execute", "process"]
            },
            "error_handling_guide": {
                "recommended_exceptions": ["ValueError", "RuntimeError"]
            }
        }
        
        # コード生成（Enhanced版無効）
        generated_code = self.template_manager.generate_code(
            "class", "web", context, use_enhanced=False
        )
        
        # 品質チェック
        self.assertIsNotNone(generated_code, "生成されたコードがNoneです")
        self.assertGreater(len(generated_code), 100, 
                          "生成されたコードが短すぎます（100文字未満）")
        
        # 必須要素の確認
        self.assertIn("class Issue999Implementation", generated_code,
                     "クラス定義が含まれていません")
        self.assertNotIn("from  import", generated_code,
                        "空のimport文が含まれています")
        
        # TODOコメントチェック（少ないほど良い）
        todo_count = generated_code.count("TODO")
        self.assertLess(todo_count, 5,
                       f"TODOコメントが多すぎます: {todo_count}個")


class TestIssueProcessingLock(unittest.TestCase):
    """Issue処理ロック機能の監査テスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.lock_manager = IssueProcessingLockManager(
            lock_dir=os.path.join(self.temp_dir, "locks")
        )
        
    def tearDown(self):
        """テストクリーンアップ"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_lock_acquisition_and_release(self):
        """ロックの取得と解放が正常に動作するか"""
        issue_number = 123
        
        # ロック取得
        success = self.lock_manager.acquire_lock(issue_number, "test_operation", 60)
        self.assertTrue(success, "ロック取得に失敗しました")
        
        # ロック状態確認
        self.assertTrue(self.lock_manager.is_locked(issue_number),
                       "ロックが取得されていません")
        
        # 同じIssueの再ロック試行（失敗すべき）
        success2 = self.lock_manager.acquire_lock(issue_number, "test_operation2", 60)
        self.assertFalse(success2, "同じIssueの重複ロックが許可されました")
        
        # ロック解放
        released = self.lock_manager.release_lock(issue_number)
        self.assertTrue(released, "ロック解放に失敗しました")
        
        # ロック解放確認
        self.assertFalse(self.lock_manager.is_locked(issue_number),
                        "ロックが解放されていません")
    
    def test_processing_interval_enforcement(self):
        """処理間隔制限が機能するか"""
        issue_number = 456
        
        # 初回ロック取得
        success1 = self.lock_manager.acquire_lock(issue_number, "test", 10)
        self.assertTrue(success1, "初回ロック取得に失敗")
        
        # ロック解放
        self.lock_manager.release_lock(issue_number)
        
        # 即座に再ロック試行（5分間隔制限により失敗すべき）
        success2 = self.lock_manager.acquire_lock(issue_number, "test2", 10)
        self.assertFalse(success2, 
                        "処理間隔制限が機能していません（即座の再処理が許可されました）")
        
        # 処理履歴を確認
        self.assertIn(issue_number, self.lock_manager.processing_history,
                     "処理履歴が記録されていません")
    
    def test_lock_persistence(self):
        """ロック情報がファイルに永続化されるか"""
        issue_number = 789
        
        # ロック取得
        self.lock_manager.acquire_lock(issue_number, "persistent_test", 300)
        
        # ロックファイルの存在確認
        lock_file = self.lock_manager.lock_dir / f"issue_{issue_number}.lock"
        self.assertTrue(lock_file.exists(), "ロックファイルが作成されていません")
        
        # ロックファイルの内容確認
        with open(lock_file, 'r') as f:
            lock_data = json.load(f)
        
        self.assertEqual(lock_data['issue_number'], issue_number,
                        "ロックファイルのIssue番号が不正です")
        self.assertEqual(lock_data['operation'], "persistent_test",
                        "ロックファイルの操作名が不正です")
        self.assertIn('process_id', lock_data,
                     "ロックファイルにプロセスIDが含まれていません")
    
    def test_expired_lock_cleanup(self):
        """期限切れロックの自動クリーンアップ"""
        issue_number = 321
        
        # 短い期限でロック取得
        self.lock_manager.acquire_lock(issue_number, "expire_test", 1)
        
        # ロック情報を直接操作して期限切れにする
        if issue_number in self.lock_manager.active_locks:
            self.lock_manager.active_locks[issue_number].locked_at = time.time() - 3600
        
        # 期限切れチェック
        is_locked = self.lock_manager.is_locked(issue_number)
        self.assertFalse(is_locked, "期限切れロックが有効と判定されました")
        
        # クリーンアップ後の確認
        self.assertNotIn(issue_number, self.lock_manager.active_locks,
                        "期限切れロックがクリーンアップされていません")
    
    def test_concurrent_lock_attempts(self):
        """並行ロック試行のテスト"""
        issue_number = 654
        results = []
        
        def try_lock(operation_name):
            success = self.lock_manager.acquire_lock(issue_number, operation_name, 60)
            results.append((operation_name, success))
            if success:
                time.sleep(0.1)  # 少し待機
                self.lock_manager.release_lock(issue_number)
        
        # 複数のロック試行を順次実行（本来は並行だが、テストでは順次）
        operations = ["op1", "op2", "op3"]
        for op in operations:
            try_lock(op)
        
        # 最初の操作のみ成功すべき
        successful_ops = [op for op, success in results if success]
        self.assertEqual(len(successful_ops), 1,
                        f"複数の操作が成功しました: {successful_ops}")


class TestFileOverwritePrevention(unittest.TestCase):
    """ファイル上書き防止機能の監査テスト"""
    
    def test_issue_189_files_integrity(self):
        """Issue #189のファイルが正しい状態を保っているか"""
        # 実装ファイルのチェック
        impl_file = PROJECT_ROOT / "libs/web/issue_189_implementation.py"
        if impl_file.exists():
            with open(impl_file, 'r') as f:
                content = f.read()
            
            # 最小限の実装ではないことを確認
            self.assertGreater(len(content), 200,
                             "実装ファイルが最小スタブに戻っています")
            self.assertNotIn("TODO: Implement functionality", content,
                            "実装ファイルにTODOスタブが含まれています")
            
            # 適切なクラスが定義されているか
            self.assertIn("class Issue189Implementation", content,
                         "Issue189Implementationクラスが定義されていません")
        
        # テストファイルのチェック
        test_file = PROJECT_ROOT / "tests/test_issue_189.py"
        if test_file.exists():
            with open(test_file, 'r') as f:
                content = f.read()
            
            # 壊れたimport文がないことを確認
            self.assertNotIn("from  import", content,
                            "テストファイルに空のimport文が含まれています")
            
            # Web APIテストではなくアーキテクチャテストであることを確認
            if "TestTest189" in content and "Web API" in content:
                self.fail("テストファイルが不適切なWeb APIテンプレートを使用しています")


class TestTemplateSystemIntegrity(unittest.TestCase):
    """テンプレートシステムの整合性監査"""
    
    def test_base_template_availability(self):
        """Base版テンプレートが利用可能か"""
        template_manager = CodeGenerationTemplateManager()
        
        # Base版テンプレートの存在確認
        template_types = ["class", "test"]
        for template_type in template_types:
            try:
                template = template_manager.get_template(template_type, "base", use_enhanced=False)
                self.assertIsNotNone(template,
                                   f"Base版{template_type}テンプレートが取得できません")
            except Exception as e:
                self.fail(f"Base版{template_type}テンプレート取得でエラー: {e}")
    
    def test_module_name_generation(self):
        """モジュール名が正しく生成されるか"""
        template_manager = CodeGenerationTemplateManager()
        
        # 複数のIssue番号でテスト
        test_cases = [
            (123, "issue_123_solution"),
            (999, "issue_999_solution"),
            (1, "issue_1_solution")
        ]
        
        for issue_number, expected_module in test_cases:
            async def create_context():
                return await template_manager.create_context_from_issue(
                    issue_number, "Test", "Body"
                )
            
            context = asyncio.run(create_context())
            self.assertEqual(context['module_name'], expected_module,
                           f"Issue #{issue_number} のモジュール名が不正です")


# テスト実行
if __name__ == "__main__":
    # 詳細な出力を有効化
    unittest.main(verbosity=2)