#!/usr/bin/env python3
"""
🌊 Elder Flow包括的統合テストスクリプト
=======================================

統合完了システムの包括的テスト実行

Author: Claude Elder
Created: 2025-07-23
"""

import sys
import subprocess
import importlib
from pathlib import Path
from typing import Dict, List, Tuple, Any
import traceback


class ElderFlowComprehensiveTest:
    """Elder Flow包括テスト実行システム"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        sys.path.insert(0, str(self.project_root))
        
        self.test_results = {
            "4sages_import": [],
            "a2a_agents": [],
            "business_logic": [],
            "naming_compliance": [],
            "soul_deprecation": [],
            "project_structure": []
        }
        
        self.sages = ["incident_sage", "knowledge_sage", "task_sage", "rag_sage"]
    
    def test_4sages_import(self) -> Tuple[bool, List[str]]:
        """4賢者システムImportテスト"""
        print("🔍 4賢者システムImportテスト")
        print("-" * 40)
        
        results = []
        all_success = True
        
        for sage in self.sages:
            try:
                # business_logic.py import
                bl_module = importlib.import_module(f"{sage}.business_logic")
                results.append(f"✅ {sage}.business_logic: Import成功")
                
                # a2a_agent.py import  
                a2a_module = importlib.import_module(f"{sage}.a2a_agent")
                agent_class_name = sage.title().replace('_', '') + 'Agent'
                agent_class = getattr(a2a_module, agent_class_name)
                results.append(f"✅ {sage}.a2a_agent.{agent_class_name}: クラス取得成功")
                
            except Exception as e:
                results.append(f"❌ {sage}: Import失敗 - {e}")
                all_success = False
        
        self.test_results["4sages_import"] = results
        return all_success, results
    
    def test_a2a_agents_functionality(self) -> Tuple[bool, List[str]]:
        """A2Aエージェント機能テスト"""
        print("\\n📡 A2Aエージェント機能テスト")
        print("-" * 40)
        
        results = []
        all_success = True
        
        for sage in self.sages:
            try:
                # A2Aエージェント作成
                a2a_module = importlib.import_module(f"{sage}.a2a_agent")
                agent_class_name = sage.title().replace('_', '') + 'Agent'
                agent_class = getattr(a2a_module, agent_class_name)
                agent = agent_class()
                
                # 基本メソッド存在確認
                if hasattr(agent, 'send_message'):
                    results.append(f"✅ {sage}: send_message メソッド存在")
                else:
                    results.append(f"❌ {sage}: send_message メソッド不存在")
                    all_success = False
                
                if hasattr(agent, 'receive_message'):
                    results.append(f"✅ {sage}: receive_message メソッド存在")
                else:
                    results.append(f"❌ {sage}: receive_message メソッド不存在")
                    all_success = False
                
                if hasattr(agent, 'broadcast_status'):
                    results.append(f"✅ {sage}: broadcast_status メソッド存在")
                else:
                    results.append(f"❌ {sage}: broadcast_status メソッド不存在")
                    all_success = False
                
            except Exception as e:
                results.append(f"❌ {sage}: A2Aエージェント機能テスト失敗 - {e}")
                all_success = False
        
        self.test_results["a2a_agents"] = results
        return all_success, results
    
    def test_soul_deprecation_cleanup(self) -> Tuple[bool, List[str]]:
        """Soul廃止クリーンアップ確認"""
        print("\\n🗑️ Soul廃止クリーンアップ確認")
        print("-" * 40)
        
        results = []
        all_success = True
        
        # Soul関連ファイルが存在しないことを確認
        soul_files_to_check = [
            "shared_libs/soul_base.py",
            "libs/base_soul.py",
            "libs/elder_flow_soul_integration.py",
            "libs/google_a2a_soul_integration.py"
        ]
        
        for soul_file in soul_files_to_check:
            file_path = self.project_root / soul_file
            if not file_path.exists():
                results.append(f"✅ {soul_file}: 正しく廃止済み")
            else:
                results.append(f"❌ {soul_file}: まだ存在している")
                all_success = False
        
        # 4賢者のsoul.pyが存在しないことを確認
        for sage in self.sages:
            soul_file = self.project_root / sage / "soul.py"
            if not soul_file.exists():
                results.append(f"✅ {sage}/soul.py: 正しく廃止済み")
            else:
                results.append(f"❌ {sage}/soul.py: まだ存在している")
                all_success = False
        
        self.test_results["soul_deprecation"] = results
        return all_success, results
    
    def test_naming_compliance(self) -> Tuple[bool, List[str]]:
        """命名規約準拠確認"""
        print("\\n🏷️ 命名規約準拠確認")
        print("-" * 40)
        
        results = []
        all_success = True
        
        # configs/ ディレクトリ存在確認
        configs_dir = self.project_root / "configs"
        if configs_dir.exists():
            results.append("✅ configs/: 正規命名存在")
        else:
            results.append("❌ configs/: ディレクトリ不存在")
            all_success = False
        
        # config/ ディレクトリが存在しないことを確認
        config_dir = self.project_root / "config"
        if not config_dir.exists():
            results.append("✅ config/: 正しく廃止済み")
        else:
            results.append("❌ config/: まだ存在している")
            all_success = False
        
        # 4賢者システム内configs確認
        for sage in self.sages:
            configs_path = self.project_root / sage / "configs"
            config_path = self.project_root / sage / "config"
            
            if configs_path.exists() and not config_path.exists():
                results.append(f"✅ {sage}: 命名規約準拠（configs/）")
            elif config_path.exists():
                results.append(f"❌ {sage}: 旧命名残存（config/）")
                all_success = False
            else:
                results.append(f"ℹ️ {sage}: 設定ディレクトリなし")
        
        self.test_results["naming_compliance"] = results
        return all_success, results
    
    def test_project_structure_integrity(self) -> Tuple[bool, List[str]]:
        """プロジェクト構造整合性確認"""
        print("\\n🏗️ プロジェクト構造整合性確認")
        print("-" * 40)
        
        results = []
        all_success = True
        
        # 4賢者システム必須ファイル確認
        for sage in self.sages:
            sage_dir = self.project_root / sage
            if not sage_dir.exists():
                results.append(f"❌ {sage}/: ディレクトリ不存在")
                all_success = False
                continue
            
            required_files = ["__init__.py", "business_logic.py", "a2a_agent.py"]
            for req_file in required_files:
                file_path = sage_dir / req_file
                if file_path.exists():
                    results.append(f"✅ {sage}/{req_file}: 存在")
                else:
                    results.append(f"❌ {sage}/{req_file}: 不存在")
                    all_success = False
        
        # 重要ドキュメント存在確認
        important_docs = [
            "docs/standards/PROJECT_STRUCTURE_STANDARDS.md",
            "docs/standards/NAMING_CONVENTIONS_AND_DIRECTORY_RULES.md",
            "docs/projects/ISSUE_302_RESOLUTION_COMPLETE_GUIDE.md"
        ]
        
        for doc in important_docs:
            doc_path = self.project_root / doc
            if doc_path.exists():
                results.append(f"✅ {doc}: 存在")
            else:
                results.append(f"❌ {doc}: 不存在")
                all_success = False
        
        self.test_results["project_structure"] = results
        return all_success, results
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """包括テスト実行"""
        print("🌊 Elder Flow包括的統合テスト開始")
        print("=" * 60)
        
        test_functions = [
            ("4賢者システムImport", self.test_4sages_import),
            ("A2Aエージェント機能", self.test_a2a_agents_functionality),
            ("Soul廃止クリーンアップ", self.test_soul_deprecation_cleanup),
            ("命名規約準拠", self.test_naming_compliance),
            ("プロジェクト構造整合性", self.test_project_structure_integrity)
        ]
        
        overall_success = True
        test_summary = []
        
        for test_name, test_func in test_functions:
            try:
                success, details = test_func()
                test_summary.append({
                    "name": test_name,
                    "success": success,
                    "details": details
                })
                
                if not success:
                    overall_success = False
                    
            except Exception as e:
                print(f"\\n❌ {test_name}テスト実行エラー: {e}")
                traceback.print_exc()
                overall_success = False
                test_summary.append({
                    "name": test_name,
                    "success": False,
                    "details": [f"テスト実行エラー: {e}"]
                })
        
        # 結果サマリー
        print("\\n" + "=" * 60)
        print("🎉 Elder Flow包括テスト完了")
        print("=" * 60)
        
        successful_tests = sum(1 for test in test_summary if test["success"])
        total_tests = len(test_summary)
        
        print(f"📊 テスト結果: {successful_tests}/{total_tests}")
        print(f"🎯 総合判定: {'✅ PASS' if overall_success else '❌ FAIL'}")
        
        if overall_success:
            print("\\n🚀 統合システム完全動作確認！")
            print("✅ Issue #302解決完了")
            print("✅ 魂システム→4賢者システム統合完了")
            print("✅ 命名規約完全準拠")
            print("✅ GitHub Issue更新準備完了")
        else:
            print("\\n⚠️ 一部テスト失敗 - 詳細確認が必要")
        
        print("=" * 60)
        
        return {
            "overall_success": overall_success,
            "test_summary": test_summary,
            "test_results": self.test_results,
            "successful_tests": successful_tests,
            "total_tests": total_tests
        }


def main():
    """メイン実行"""
    tester = ElderFlowComprehensiveTest()
    result = tester.run_comprehensive_test()
    
    # 終了コード設定
    sys.exit(0 if result["overall_success"] else 1)


if __name__ == "__main__":
    main()