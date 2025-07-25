#!/usr/bin/env python3
"""
🎯 Simple Docstring Pattern Fixer
最も一般的な不正配置docstringパターンを修正
"""

import ast
import os
import re


def fix_docstring_pattern_in_file(file_path: str) -> bool:
    """特定パターンのdocstring配置エラーを修正"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # パターン1: 関数定義直後の不正配置docstring + 正しいdocstring
        # def function():
        # """不正配置docstring"""  
        #     """正しい位置のdocstring"""
        pattern1 = re.compile(
            r'(^\s*def\s+\w+\([^)]*\):\s*\n)'
            r'(\s*)"""[^"]*"""\s*\n'
            r'(\s+)"""([^"]*)"""',
            re.MULTILINE
        )
        
        def replace_pattern1(match):
            func_def = match.group(1)
            correct_indent = match.group(3)
            docstring_content = match.group(4)
            return f'{func_def}{correct_indent}"""{docstring_content}"""'
        
        content = pattern1.sub(replace_pattern1, content)
        
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
    print("🎯 Simple Docstring Pattern Fixing - Starting...")
    
    skip_patterns = [
        '__pycache__', '.git', 'venv', '.venv', 'node_modules', 'backups'
    ]
    
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
                except SyntaxError:
                    syntax_error_files.append(file_path)
                except Exception:
                    pass
    
    print(f"Found {len(syntax_error_files)} files with syntax errors")
    
    # 修正実行
    for file_path in syntax_error_files:
        if fix_docstring_pattern_in_file(file_path):
            fixed_files.append(file_path)
            print(f"🔧 Fixed: {file_path}")
    
    print(f"\n📊 Results:")
    print(f"Files processed: {len(syntax_error_files)}")
    print(f"Files fixed: {len(fixed_files)}")
    
    if fixed_files:
        print(f"\n✅ Fixed files (first 20):")
        for i, file_path in enumerate(fixed_files[:20]):
            print(f"{i+1:2d}. {file_path}")
        
        if len(fixed_files) > 20:
            print(f"... and {len(fixed_files) - 20} more files")


if __name__ == "__main__":
    main()