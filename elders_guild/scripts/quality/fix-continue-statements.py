#!/usr/bin/env python3
"""
🔧 Fix Invalid Continue Statements
ループ外のcontinue文を修正
"""

import ast
import os
import re


def fix_invalid_continue_statements(file_path: str) -> bool:
    """ループ外のcontinue文を修正"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # パターン1: ループ外のcontinue文をreturnに変更
        # "continue  # Early return to reduce nesting" -> "return  # Early return to reduce nesting"
        content = re.sub(
            r'continue(\s*#\s*Early return to reduce nesting)',
            r'return\1',
            content
        )
        
        # パターン2: 一般的なループ外continue文
        lines = content.split('\n')
        fixed_lines = []
        in_loop = False
        loop_depth = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # ループの開始を検出
            if re.match(r'^\s*(for|while)\s+', line):
                in_loop = True
                loop_depth += 1
            
            # ブロックの終了を検出（インデントレベルで判断）
            if in_loop and line and not line.startswith(' ') and not line.startswith('\t'):
                in_loop = False
                loop_depth = 0
            
            # continue文の処理
            if stripped.startswith('continue'):
                if not in_loop:
                    # ループ外のcontinue文はreturnに変更
                    line = line.replace('continue', 'return')
            
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        if content != original_content:
            # 修正後の構文をチェック
            try:
                ast.parse(content)
                # 構文が正しければファイルを更新
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            except SyntaxError:
                return False
        
        return False
        
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def main():
    """メインエントリーポイント"""
    print("🔧 Fixing Invalid Continue Statements...")
    
    skip_patterns = ['__pycache__', '.git', 'venv', '.venv', 'node_modules', 'backups']
    
    syntax_error_files = []
    fixed_files = []
    
    # 構文エラーファイルを特定
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if not any(skip in os.path.join(root, d) for skip in skip_patterns)]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                if any(skip in file_path for skip in skip_patterns):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    ast.parse(content)
                except SyntaxError as e:
                    if "'continue' not properly in loop" in str(e):
                        syntax_error_files.append(file_path)
                except Exception:
                    pass
    
    print(f"Found {len(syntax_error_files)} files with invalid continue statements")
    
    # 修正実行
    for file_path in syntax_error_files:
        if fix_invalid_continue_statements(file_path):
            fixed_files.append(file_path)
            print(f"🔧 Fixed: {file_path}")
    
    print(f"\n📊 Results:")
    print(f"Files processed: {len(syntax_error_files)}")
    print(f"Files fixed: {len(fixed_files)}")
    
    if fixed_files:
        print(f"\n✅ Fixed files:")
        for i, file_path in enumerate(fixed_files):
            print(f"{i+1:2d}. {file_path}")


if __name__ == "__main__":
    main()