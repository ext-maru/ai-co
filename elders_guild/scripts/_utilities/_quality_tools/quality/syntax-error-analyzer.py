#!/usr/bin/env python3
"""
Syntax Error Analyzer - 構文エラー詳細分析ツール
"""
import ast
import os

def analyze_syntax_errors():
    error_types = {}
    error_files = []
    
    for root, dirs, files in os.walk('./libs'):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        ast.parse(f.read())
                except SyntaxError as e:
                    error_type = e.msg.split('(')[0].strip()
                    error_types[error_type] = error_types.get(error_type, 0) + 1
                    error_files.append({
                        'file': file_path,
                        'line': e.lineno,
                        'type': error_type,
                        'msg': e.msg
                    })
    
    print('🎯 残り33件の構文エラー内訳:')
    for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
        print(f'   {count:2d}件: {error_type}')
    
    print('\n📋 Top 10エラーファイル:')
    for i, error in enumerate(error_files[:10]):
        print(f"   {i+1:2d}. {os.path.basename(error['file'])}:{error['line']} - {error['type']}")

if __name__ == "__main__":
    analyze_syntax_errors()