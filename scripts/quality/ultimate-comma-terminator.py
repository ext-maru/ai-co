#!/usr/bin/env python3
"""
Ultimate Comma Terminator - 最終カンマエラー完全撲滅システム
残り21件を0件にする最終兵器
"""
import ast
import os
import re
from typing import List, Tuple

def ultimate_comma_terminator():


"""21件のカンマエラーを完全撲滅""" {len(comma_files)}件")
    
    for i, file_info in enumerate(comma_files):
        print(f"   {i+1:2d}. {file_info['file']}:{file_info['line']}")
    
    # 超精密修正実行
    fixed_count = 0
    for file_info in comma_files:
        if fix_comma_error_ultra_precise(file_info):
            print(f"✅ Fixed: {file_info['file']}")
            fixed_count += 1
        else:
            print(f"❌ Failed: {file_info['file']}")
    
    print(f"\n📊 ULTIMATE修正結果:")
    print(f"   修正成功: {fixed_count}件")
    print(f"   成功率: {fixed_count/len(comma_files)*100:.1f}%")
    
    return fixed_count

def get_comma_error_files():

    
    """カンマエラーファイルを取得"""
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        ast.parse(f.read())
                except SyntaxError as e:
                    if 'comma' in e.msg.lower():
                        comma_files.append({
                            'path': file_path,
                            'file': os.path.basename(file_path),
                            'line': e.lineno
                        })
    return comma_files

def fix_comma_error_ultra_precise(file_info: dict) -> bool:
    """超精密カンマエラー修正"""
    try:
        with open(file_info['path'], 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        original_lines = lines.copy()
        error_line_idx = file_info['line'] - 1
        
        # エラー行周辺の修正（±3行範囲）
        start_idx = max(0, error_line_idx - 3)
        end_idx = min(len(lines), error_line_idx + 4)
        
        # パターン1: def func_name(param:\n    \"\"\"docstring\"\"\"\ntype):
        for i in range(start_idx, end_idx - 2):
            if i < len(lines) - 2:
                line1 = lines[i].strip()
                line2 = lines[i + 1].strip()
                line3 = lines[i + 2].strip()
                
                # メソッド定義 + docstring + 型の分離パターン
                if (('def ' in line1 or 'async def' in line1) and 
                    line1.endswith(':') and
                    line2.startswith('\"\"\"') and line2.endswith('\"\"\"') and
                    line3.endswith('):')):
                    
                    # 修正: 型をメソッド定義行に統合
                    method_part = line1[:-1]  # ':' を除去
                    type_part = line3[:-2]    # '):' を除去
                    
                    lines[i] = method_part + ': ' + type_part + '):\n'
                    lines[i + 1] = '        ' + line2 + '\n'  # docstringをインデント
                    lines[i + 2] = '\n'  # 空行化
                    
                    # 構文チェック
                    try:
                        ast.parse(''.join(lines))
                        with open(file_info['path'], 'w', encoding='utf-8') as f:
                            f.writelines(lines)
                        return True
                    except SyntaxError:
                        lines = original_lines.copy()  # 復元
        
        # パターン2: 単純な型分離パターン
        for i in range(start_idx, end_idx - 1):
            if i < len(lines) - 1:
                current_line = lines[i]
                next_line = lines[i + 1]
                
                # def func(param: の後に改行があり、次行が型の場合
                if ('def ' in current_line and ':' in current_line and
                    current_line.rstrip().endswith(':') and
                    next_line.strip().endswith('):')):
                    
                    method_part = current_line.rstrip()[:-1]  # ':' 除去
                    type_part = next_line.strip()[:-2]        # '):' 除去
                    
                    lines[i] = method_part + ': ' + type_part + '):\n'
                    lines[i + 1] = '\n'  # 空行化
                    
                    try:
                        ast.parse(''.join(lines))
                        with open(file_info['path'], 'w', encoding='utf-8') as f:
                            f.writelines(lines)
                        return True
                    except SyntaxError:
                        lines = original_lines.copy()
        
        return False
        
    except Exception as e:
        print(f"   Error fixing {file_info['file']}: {e}")
        return False

if __name__ == "__main__":
    ultimate_comma_terminator()