#!/usr/bin/env python3
"""
OPERATION DAWN BREAKER - 夜明けまでの完全殲滅スクリプト
朝までぶっ通しでtype annotation構文エラーを完全撲滅
"""
import os
import re
import ast
from pathlib import Path

def fix_type_annotation_errors(filepath):
    """Type annotation位置エラーを修正"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # パターン1: def method(param:\n    """docstring"""\ntype):
        pattern1 = r'def\s+(\w+)\s*\(([^:)]*?):\s*\n\s*"""([^"]*)"""\s*\n\s*([^)]+)\s*\):'
        
        def replacement1(match):
            method_name = match.group(1)
            params_before = match.group(2).strip()
            docstring = match.group(3)
            type_after = match.group(4).strip()
            
            # パラメータと型を結合
            if params_before:
                full_params = f'{params_before}: {type_after}'
            else:
                full_params = type_after
                
            return f'def {method_name}({full_params}):\n        """{docstring}"""'
        
        fixed_content = re.sub(pattern1, replacement1, content, flags=re.MULTILINE | re.DOTALL)
        
        # パターン2: async def method(param:\n    """docstring"""\ntype):
        pattern2 = r'async\s+def\s+(\w+)\s*\(([^:)]*?):\s*\n\s*"""([^"]*)"""\s*\n\s*([^)]+)\s*\):'
        
        def replacement2(match):
            method_name = match.group(1)
            params_before = match.group(2).strip()
            docstring = match.group(3)
            type_after = match.group(4).strip()
            
            if params_before:
                full_params = f'{params_before}: {type_after}'
            else:
                full_params = type_after
                
            return f'async def {method_name}({full_params}):\n        """{docstring}"""'
        
        fixed_content = re.sub(pattern2, replacement2, fixed_content, flags=re.MULTILINE | re.DOTALL)
        
        # 変更があった場合のみ書き込み
        if content != fixed_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            return True
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    return False

def main():
    """メイン処理"""
    print("⚔️ OPERATION DAWN BREAKER 開始！")
    
    fixed_count = 0
    error_count = 0
    
    # libsディレクトリ内のすべてのPythonファイルを処理
    for root, dirs, files in os.walk('libs'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                
                # まず構文エラーがあるか確認
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        ast.parse(f.read())
                except SyntaxError:
                    # エラーがある場合は修正を試みる
                    if fix_type_annotation_errors(filepath):
                        # 修正後に再検証
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                ast.parse(f.read())
                            print(f"✅ 修復成功: {filepath}")
                            fixed_count += 1
                        except SyntaxError as e:
                            print(f"⚠️ 部分修復: {filepath} - Line {e.lineno}")
                            error_count += 1
                    else:
                        error_count += 1
    
    print(f"\n🏆 戦果報告:")
    print(f"✅ 完全修復: {fixed_count}体")
    print(f"💥 要追加攻撃: {error_count}体")
    print(f"📊 勝利率: {(fixed_count/(fixed_count+error_count)*100):0.1f}%" if (fixed_count+error_count) > 0 else "N/A")

if __name__ == '__main__':
    main()