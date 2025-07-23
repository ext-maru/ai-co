#!/usr/bin/env python3
"""
構文エラー自動修正ツール
"""
import ast
import os
import sys
from pathlib import Path
from typing import List, Tuple

def fix_syntax_errors(file_path: str) -> Tuple[bool, str]:
    """構文エラーを修正"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # まず現在のコードを解析してエラーを確認
        try:
            ast.parse(content)
            return False, "No syntax errors found"
        except SyntaxError as e:
            # 一般的な構文エラーを修正
            lines = content.splitlines()
            
            # 行番号が有効な場合
            if e.lineno and 0 < e.lineno <= len(lines):
                error_line = lines[e.lineno - 1]
                
                # 未閉じの括弧
                if "unexpected EOF" in str(e) or "unmatched" in str(e):
                    # 括弧の数を数える
                    open_parens = error_line.count('(') - error_line.count(')')
                    open_brackets = error_line.count('[') - error_line.count(']')
                    open_braces = error_line.count('{') - error_line.count('}')
                    
                    # 閉じ括弧を追加
                    if open_parens > 0:
                        lines[e.lineno - 1] = error_line + ')' * open_parens
                    if open_brackets > 0:
                        lines[e.lineno - 1] = error_line + ']' * open_brackets
                    if open_braces > 0:
                        lines[e.lineno - 1] = error_line + '}' * open_braces
                
                # 未閉じのクォート
                elif "unterminated string" in str(e) or "EOL while scanning" in str(e):
                    # クォートの数を数える
                    single_quotes = error_line.count("'") % 2
                    double_quotes = error_line.count('"') % 2
                    
                    if single_quotes == 1:
                        lines[e.lineno - 1] = error_line + "'"
                    elif double_quotes == 1:
                        lines[e.lineno - 1] = error_line + '"'
                
                # インデントエラー
                elif isinstance(e, IndentationError):
                    # 前の行のインデントレベルに合わせる
                    if e.lineno > 1:
                        prev_line = lines[e.lineno - 2]
                        indent = len(prev_line) - len(prev_line.lstrip())
                        
                        # 前の行が : で終わっている場合は4スペース追加
                        if prev_line.rstrip().endswith(':'):
                            indent += 4
                        
                        # 正しいインデントで行を再構築
                        lines[e.lineno - 1] = ' ' * indent + error_line.lstrip()
                
                # 修正したコンテンツを作成
                fixed_content = '\n'.join(lines)
                
                # 修正後の構文チェック
                try:
                    ast.parse(fixed_content)
                    # 修正成功
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                    return True, f"Fixed syntax error on line {e.lineno}"
                except:
                    # 修正失敗
                    return False, f"Could not fix syntax error: {str(e)}"
            
            return False, f"Syntax error but could not determine location: {str(e)}"
            
    except Exception as e:
        return False, f"Error processing file: {str(e)}"

def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        print("Usage: fix-syntax-errors.py <file1> [file2] ...")
        sys.exit(1)
    
    total_fixed = 0
    
    for file_path in sys.argv[1:]:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue
        
        print(f"Checking {file_path}...")
        fixed, message = fix_syntax_errors(file_path)
        
        if fixed:
            total_fixed += 1
            print(f"  ✅ {message}")
        else:
            print(f"  ℹ️  {message}")
    
    print(f"\n✅ Summary: Fixed syntax errors in {total_fixed} files")

if __name__ == "__main__":
    main()