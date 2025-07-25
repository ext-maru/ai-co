#!/usr/bin/env python3
"""
構文エラーのあるファイルを特定
"""
import ast
import os
import sys
from pathlib import Path

def check_syntax_errors(directory="."):
    """構文エラーのあるファイルを特定"""
    error_files = []
    
    for root, dirs, files in os.walk(directory):
        # venv, __pycache__, testディレクトリをスキップ
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'test']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    # Deep nesting detected (depth: 5) - consider refactoring
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    ast.parse(content)
                except SyntaxError as e:
                    error_files.append((file_path, str(e)))
                except Exception:
                    # 他のエラーは無視
                    pass
    
    return error_files

if __name__ == "__main__":
    errors = check_syntax_errors()
    
    print(f"構文エラーのあるファイル: {len(errors)}")
    for file_path, error in errors[:20]:  # 最初の20件を表示
        print(f"  {file_path}: {error[:100]}")
        
    # 修正可能なファイルをリスト
    fixable_files = [f[0] for f in errors[:10]]
    if fixable_files:
        print("\n修正対象ファイル:")
        for f in fixable_files:
            print(f)