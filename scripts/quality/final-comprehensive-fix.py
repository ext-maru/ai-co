#!/usr/bin/env python3
"""
FINAL COMPREHENSIVE FIX - 最終包括修正
残存エラーを一掃する最終手段
"""

import ast
import re
from pathlib import Path

def apply_all_fixes(content):
    """すべての修正パターンを適用"""
    
    # 1. .0attribute -> .attribute
    content = re.sub(r'\.0(\w+)', r'.\1', content)
    
    # 2. sqlite3 -> sqlite3
    content = re.sub(r'\bsqlite3\.0\b', 'sqlite3', content)
    
    # 3. メソッド定義の修正
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # def method()docstring -> def method():\n    """docstring"""
        method_match = re.match(r'^(\s*)def\s+(\w+)\s*\(([^)]*)\)(.*)$', line)
        if method_match and not line.rstrip().endswith(':'):
            indent = method_match.group(1)
            method_name = method_match.group(2)
            params = method_match.group(3)
            remaining = method_match.group(4)
            
            # 次の行がdocstringかチェック
            if i + 1 < len(lines) and '"""' in lines[i + 1]:
                fixed_lines.append(f"{indent}def {method_name}({params}):")
                i += 1
                continue
            # 残りに何か含まれている場合
            elif remaining.strip():
                fixed_lines.append(f"{indent}def {method_name}({params}):")
                # 残りの部分を次の行に
                fixed_lines.append(f"{indent}    {remaining.strip()}")
                i += 1
                continue
        
        fixed_lines.append(line)
        i += 1
    
    content = '\n'.join(fixed_lines)
    
    # 4. 特殊なパターンの修正
    # def func() -> typelogger = ... -> def func() -> type:\n    logger = ...
    content = re.sub(
        r'def\s+(\w+)\s*\(([^)]*)\)\s*->\s*([^:\n]+)([^:\n]+)$',
        r'def \1(\2) -> \3:\n    \4',
        content,
        flags=re.MULTILINE
    )
    
    return content

def main():
    """メイン処理"""
    print("🔥 FINAL COMPREHENSIVE FIX - 最終包括修正")
    
    project_root = Path('/home/aicompany/ai_co')
    
    # すべてのPythonファイルをチェック
    error_count = 0
    fixed_count = 0
    
    for py_file in project_root.rglob('*.py'):
        if any(skip in str(py_file) for skip in ['.venv', '__pycache__', 'node_modules', '.git']):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 現在の状態を確認
            try:
                ast.parse(content)
                continue  # エラーなし
            except SyntaxError:
                error_count += 1
            
            # 修正適用
            fixed_content = apply_all_fixes(content)
            
            # テスト
            try:
                ast.parse(fixed_content)
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                fixed_count += 1
                print(f"✅ 修正: {py_file}")
            except SyntaxError:
                pass  # まだエラーあり
                
        except Exception:
            pass
    
    print(f"\n📊 結果: {fixed_count}/{error_count} 修正")
    
    # 最終チェック
    print("\n🔍 最終チェック...")
    remaining = 0
    for py_file in project_root.rglob('*.py'):
        if any(skip in str(py_file) for skip in ['.venv', '__pycache__', 'node_modules', '.git']):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
        except SyntaxError:
            remaining += 1
    
    print(f"\n🎯 残存エラー: {remaining}")

if __name__ == "__main__":
    main()