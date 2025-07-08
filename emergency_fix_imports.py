#!/usr/bin/env python3
"""
Emergency Import Fix Script
インポートエラーの緊急修正スクリプト
"""

import os
import re
from pathlib import Path

def fix_path_imports():
    """Pathインポートエラーの修正"""
    # テストファイルを検索
    test_files = []
    for root, dirs, files in os.walk("tests"):
        for file in files:
            if file.endswith(".py"):
                test_files.append(os.path.join(root, file))
    
    fixed_files = []
    
    for file_path in test_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # PROJECT_ROOT = Path の前にimportがない場合を検出
            if "PROJECT_ROOT = Path(__file__)" in content:
                lines = content.split('\n')
                needs_fix = False
                
                # Path import が存在するか確認
                has_path_import = any(
                    "from pathlib import Path" in line or 
                    "import pathlib" in line 
                    for line in lines
                )
                
                # sys import が存在するか確認
                has_sys_import = any(
                    "import sys" in line 
                    for line in lines
                )
                
                # PROJECT_ROOT行より前にimportがあるか確認
                project_root_line = -1
                for i, line in enumerate(lines):
                    if "PROJECT_ROOT = Path(__file__)" in line:
                        project_root_line = i
                        break
                
                if project_root_line > 0:
                    # PROJECT_ROOT より前にimportがあるか確認
                    path_import_before = any(
                        ("from pathlib import Path" in lines[i] or "import pathlib" in lines[i])
                        for i in range(project_root_line)
                    )
                    sys_import_before = any(
                        "import sys" in lines[i]
                        for i in range(project_root_line)
                    )
                    
                    if not path_import_before or not sys_import_before:
                        needs_fix = True
                
                if needs_fix:
                    # 修正を適用
                    new_lines = []
                    imports_added = False
                    
                    for i, line in enumerate(lines):
                        if "PROJECT_ROOT = Path(__file__)" in line and not imports_added:
                            # import文を追加
                            if not has_sys_import:
                                new_lines.append("import sys")
                            if not has_path_import:
                                new_lines.append("from pathlib import Path")
                            new_lines.append("")
                            imports_added = True
                        new_lines.append(line)
                    
                    # ファイルに書き戻し
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(new_lines))
                    
                    fixed_files.append(file_path)
                    print(f"Fixed: {file_path}")
        
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    return fixed_files

def fix_base_test_imports():
    """base_test.pyのManagerTestCase問題を修正"""
    base_test_file = "tests/base_test.py"
    
    if os.path.exists(base_test_file):
        try:
            with open(base_test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # ManagerTestCase クラスが存在するか確認
            if "class ManagerTestCase" not in content and "class WorkerTestCase" in content:
                # WorkerTestCase を基にManagerTestCase を作成
                manager_test_case = '''
class ManagerTestCase(unittest.TestCase):
    """マネージャークラスのテスト用基底クラス"""
    
    def setUp(self):
        """テストセットアップ"""
        self.mock_config = {
            "test_mode": True,
            "timeout": 30
        }
    
    def tearDown(self):
        """テストクリーンアップ"""
        pass
'''
                
                # WorkerTestCase の後に追加
                content = content.replace(
                    "class WorkerTestCase(unittest.TestCase):",
                    "class WorkerTestCase(unittest.TestCase):" + manager_test_case
                )
                
                with open(base_test_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"Fixed: {base_test_file} - Added ManagerTestCase")
        
        except Exception as e:
            print(f"Error fixing base_test.py: {e}")

def main():
    """メイン実行"""
    print("🚨 Emergency Import Fix Started...")
    
    # インポートエラーを修正
    fixed_files = fix_path_imports()
    
    # base_test.py を修正
    fix_base_test_imports()
    
    print(f"\n✅ Fixed {len(fixed_files)} files:")
    for file in fixed_files:
        print(f"  - {file}")
    
    print("\n🎯 Emergency fix complete!")

if __name__ == "__main__":
    main()