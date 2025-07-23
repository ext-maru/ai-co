#!/usr/bin/env python3
"""
🏛️ Elders Guild Integration Script
重複コード統合とimport修正を自動実行
"""

import os
import re
import shutil
from pathlib import Path
from typing import List, Tuple

def fix_imports_in_file(file_path: Path) -> Tuple[bool, List[str]]:
    """ファイル内のimport文を修正"""
    changes = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 修正パターン
        patterns = [
            # elders_guild_dev → elders_guild.src
            (r'from elders_guild_dev\.(\w+)', r'from elders_guild.src.\1'),
            (r'import elders_guild_dev\.(\w+)', r'import elders_guild.src.\1'),
            
            # 直下からsrc配下への修正
            (r'from elders_guild\.(incident_sage|knowledge_sage|rag_sage|task_sage)', 
             r'from elders_guild.src.\1'),
            (r'import elders_guild\.(incident_sage|knowledge_sage|rag_sage|task_sage)', 
             r'import elders_guild.src.\1'),
        ]
        
        for pattern, replacement in patterns:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                changes.append(f"修正: {pattern} → {replacement}")
                content = new_content
        
        # 変更があった場合のみファイルを更新
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes
        
        return False, []
        
    except Exception as e:
        print(f"エラー in {file_path}: {e}")
        return False, [f"エラー: {e}"]

def integrate_elders_guild():


"""Elders Guild統合処理""" テストファイルのimport修正
    test_files = list(base_path.rglob("test_*.py"))
    test_files.extend(list(base_path.rglob("**/test*.py")))
    
    print(f"\n📋 テストファイル修正 ({len(test_files)}ファイル)")
    modified_count = 0
    
    for test_file in test_files:
        changed, modifications = fix_imports_in_file(test_file)
        if changed:
            modified_count += 1
            print(f"  ✅ {test_file.relative_to(base_path)}")
            for mod in modifications:
                print(f"     {mod}")
    
    print(f"\n🎯 修正完了: {modified_count}/{len(test_files)} ファイル")
    
    # Phase 2: 実行スクリプトの修正
    run_scripts = list(base_path.glob("run_*_server.py"))
    run_scripts.extend(list(base_path.glob("test_*_client.py")))
    run_scripts.extend(list(base_path.glob("test_*_execution.py")))
    
    print(f"\n🚀 実行スクリプト修正 ({len(run_scripts)}ファイル)")
    script_modified = 0
    
    for script in run_scripts:
        changed, modifications = fix_imports_in_file(script)
        if changed:
            script_modified += 1
            print(f"  ✅ {script.name}")
    
    print(f"\n🎯 スクリプト修正完了: {script_modified}/{len(run_scripts)} ファイル")
    
    return modified_count + script_modified

if __name__ == "__main__":
    total_changes = integrate_elders_guild()
    print(f"\n🏆 統合完了! 総修正ファイル数: {total_changes}")