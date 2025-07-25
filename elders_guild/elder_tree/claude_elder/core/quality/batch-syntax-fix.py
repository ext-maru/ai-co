#!/usr/bin/env python3
"""
Batch Syntax Fix - 一括構文修正ツール
🔧 型アノテーション位置エラーの一括修正
"""
import os
import re
import ast
from pathlib import Path

def fix_type_annotation_errors(file_path: str) -> bool:
    """型アノテーション位置エラーを修正"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # パターン1: def func(param:\n    """docstring"""\ntype):
        pattern1 = r'def\s+(\w+)\s*\(\s*([^:]*?):\s*\n\s*"""([^"]+)"""\s*\n\s*([^)]+)\):'
        def replace1(match):
            func_name, param, docstring, param_type = match.groups()
            return f'def {func_name}({param}: {param_type.strip()}):\n        """{docstring}"""'
        
        content = re.sub(pattern1, replace1, content, flags=re.MULTILINE | re.DOTALL)
        
        # パターン2: __init__(self, param:\n    """docstring"""\ntype):
        pattern2 = r'def\s+__init__\s*\(\s*self,\s*([^:]*?):\s*\n\s*"""([^"]+)"""\s*\n\s*([^)]+)\):'
        def replace2(match):
            param, docstring, param_type = match.groups()
            return f'def __init__(self, {param}: {param_type.strip()}):\n        """{docstring}"""'
        
        content = re.sub(pattern2, replace2, content, flags=re.MULTILINE | re.DOTALL)
        
        # 構文チェック
        if content != original_content:
            try:
                ast.parse(content)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            except SyntaxError:
                pass
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """メイン実行"""
    print("🔧 Batch Syntax Fix - Type Annotation Errors")
    print("=" * 50)
    
    # 対象ファイルリスト
    target_files = [
        "./libs/elder_flow_orchestrator.py",

        "./libs/prophecy_management_system.py",
        "./libs/syntax_repair_knight.py",
        "./libs/deployment_safeguard.py",
        "./libs/elders_guild_api_spec.py",
        "./libs/enhanced_quality_standards.py",
        "./libs/distributed_queue_manager.py",
        "./libs/simple_a2a_communication.py",
        "./libs/gui_test_framework.py",
        "./libs/priority_queue_manager.py",

        "./libs/elders_guild_fulltext_search.py",
        "./libs/mock_grimoire_database.py",
        "./libs/comprehensive_grimoire_migration.py",
        "./libs/knowledge_grimoire_adapter.py",
        "./libs/elder_flow_servant_executor_real.py",
        "./libs/elders_guild_claude_integration.py",
        "./libs/knowledge_index_optimizer.py",
        "./libs/apscheduler_integration.py"
    ]
    
    fixed_count = 0
    for file_path in target_files:
        if os.path.exists(file_path):
            if fix_type_annotation_errors(file_path):
                print(f"✅ Fixed: {file_path}")
                fixed_count += 1
            else:
                print(f"⏭️  Skipped: {file_path}")
        else:
            print(f"❌ Not found: {file_path}")
    
    print("=" * 50)
    print(f"📊 Result: {fixed_count}/{len(target_files)} files fixed")

if __name__ == "__main__":
    main()