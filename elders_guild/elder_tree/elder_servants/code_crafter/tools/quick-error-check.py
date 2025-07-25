#!/usr/bin/env python3
"""
Quick Error Check - 構文エラー高速確認ツール
"""
import ast
import os

def quick_error_check():
    count = 0
    for root, dirs, files in os.walk('./libs'):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for file in files:
            if file.endswith('.py') and count < 15:  # 上位15件のみ
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        ast.parse(f.read())
                except SyntaxError as e:
                    count += 1
                    print(f'❌ {file}:{e.lineno} - {e.msg[:60]}')
                except Exception:
                    pass
            if count >= 15:
                break
        if count >= 15:
            break
    print(f'\n上位{count}件のエラーファイル表示完了')

if __name__ == "__main__":
    quick_error_check()