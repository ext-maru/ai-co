#!/usr/bin/env python3
"""
🔥 SYNTAX WAR - 639 ERRORS DESTROYER 🔥
朝までぶっ通し！完全殲滅作戦！
"""

import ast
import os
import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import List, Tuple, Dict

def get_all_python_files(root_dir: Path) -> List[Path]:
    """全Pythonファイル取得"""
    python_files = []
    exclude_dirs = {'.git', '__pycache__', 'venv', '.venv', 'node_modules', '.pytest_cache'}
    
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    return python_files

def check_syntax_error(file_path: Path) -> Tuple[bool, str, int]:
    """構文エラーチェック"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        compile(content, str(file_path), 'exec')
        return False, "", 0
    except SyntaxError as e:
        return True, str(e.msg), e.lineno or 0
    except Exception as e:
        return True, str(e), 0

def fix_common_patterns(content: str, error_msg: str, line_no: int) -> str:
    """共通パターン修正"""
    lines = content.split('\n')
    
    if line_no > 0 and line_no <= len(lines):
        problem_line = lines[line_no - 1]
        
        # Pattern 1: def method()code: -> def method():\n    code
        if 'expected ":"' in error_msg and 'def ' in problem_line:
            match = re.match(r'^(\s*)def\s+(\w+)\s*\([^)]*\)(.+)$', problem_line)
            if match and not problem_line.rstrip().endswith(':'):
                indent = match.group(1)
                method_name = match.group(2)
                rest = match.group(3)
                # Check if there's code after the parenthesis
                if rest and not rest.strip().startswith(':'):
                    lines[line_no - 1] = f'{indent}def {method_name}():'
                    if rest.strip():
                        lines.insert(line_no, f'{indent}    {rest.strip()}')
        
        # Pattern 2: Missing colons in class/def/if/for/while/try/except
        if 'expected ":"' in error_msg:
            # Add missing colon at end of line
            if not problem_line.rstrip().endswith(':'):
                for keyword in ['class ', 'def ', 'if ', 'elif ', 'else', 'for ', 'while ', 'try', 'except', 'finally', 'with ']:
                    if problem_line.strip().startswith(keyword):
                        lines[line_no - 1] = problem_line.rstrip() + ':'
                        break
        
        # Pattern 3: invalid decimal literal (e.g., 3.0 method)
        if 'invalid decimal literal' in error_msg:
            lines[line_no - 1] = re.sub(r'(\d+)\.0([a-zA-Z_])', r'\1.0 \2', problem_line)
        
        # Pattern 4: Malformed function with type annotations
        if '-> ' in problem_line and 'def ' in problem_line:
            # Fix: def method() -> Typecode: to def method() -> Type:\n    code
            match = re.match(r'^(\s*)def\s+(\w+)\s*\([^)]*\)\s*->\s*([A-Za-z\[\], ]+)(.+)$', problem_line)
            if match:
                indent = match.group(1)
                method_name = match.group(2) 
                return_type = match.group(3)
                rest = match.group(4)
                if rest and not rest.strip().startswith(':'):
                    lines[line_no - 1] = f'{indent}def {method_name}() -> {return_type}:'
                    if rest.strip() and rest.strip() != ':':
                        lines.insert(line_no, f'{indent}    {rest.strip()}')
    
    return '\n'.join(lines)

def aggressive_fix(file_path: Path) -> bool:
    """アグレッシブ修正"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Multiple rounds of fixes
        for _ in range(3):
            has_error, error_msg, line_no = check_syntax_error(file_path)
            if not has_error:
                break
                
            content = fix_common_patterns(content, error_msg, line_no)
            
            # Write and check again
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Final check
        has_error, _, _ = check_syntax_error(file_path)
        if has_error:
            # Restore original if we couldn't fix it
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            return False
        
        return content != original_content
    
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    print("🔥 SYNTAX WAR - 639 ERRORS DESTROYER 🔥")
    print("=" * 80)
    
    project_root = Path("/home/aicompany/ai_co")
    
    # Get all Python files
    python_files = get_all_python_files(project_root)
    print(f"📊 総ファイル数: {len(python_files)}")
    
    # Find files with syntax errors
    error_files = []
    error_types = defaultdict(int)
    
    print("\n🔍 エラーファイル検出中...")
    for file_path in python_files:
        has_error, error_msg, line_no = check_syntax_error(file_path)
        if has_error:
            error_files.append((file_path, error_msg, line_no))
            error_types[error_msg] += 1
    
    print(f"\n💀 発見されたエラー: {len(error_files)}個")
    
    # Show error distribution
    print("\n📊 エラータイプ分布:")
    for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  - {error_type}: {count}件")
    
    # Fix errors
    print("\n⚔️ 修正開始...")
    fixed_count = 0
    
    for i, (file_path, error_msg, line_no) in enumerate(error_files):
        print(f"\r💪 修正中: {i+1}/{len(error_files)} ({fixed_count}個修正済み)", end='', flush=True)
        
        if aggressive_fix(file_path):
            fixed_count += 1
    
    print(f"\n\n✅ 修正完了: {fixed_count}個のファイル")
    
    # Re-scan for remaining errors
    print("\n🔍 残存エラー確認中...")
    remaining_errors = 0
    for file_path in python_files:
        has_error, _, _ = check_syntax_error(file_path)
        if has_error:
            remaining_errors += 1
    
    print(f"\n{'='*80}")
    print(f"📊 最終結果:")
    print(f"  - 初期エラー: {len(error_files)}個")
    print(f"  - 修正成功: {fixed_count}個")
    print(f"  - 残存エラー: {remaining_errors}個")
    print(f"  - 削減率: {((len(error_files) - remaining_errors) / len(error_files) * 100):.1f}%")
    
    if remaining_errors == 0:
        print("\n🎉 完全勝利！全エラー殲滅完了！")
    else:
        print(f"\n⚔️ まだ {remaining_errors}個のエラーが残っています。戦いは続く...")

if __name__ == "__main__":
    main()