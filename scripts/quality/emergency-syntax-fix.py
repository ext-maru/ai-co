#!/usr/bin/env python3
"""
Emergency Syntax Error Batch Fix Tool - Issue #291 Continue
🚨 緊急構文エラー一括修正ツール
"""
import os
import ast
import sys
import re
from pathlib import Path
from typing import List

def find_syntax_errors():
    """構文エラーのあるファイルを検出"""
    error_files = []
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip in root for skip in ['.git', '__pycache__', '.venv']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    ast.parse(content)
                except SyntaxError as e:
                    error_files.append((file_path, str(e)))
                except Exception:
                    pass
    return error_files

def fix_common_syntax_errors(file_path: str) -> bool:
    """一般的な構文エラーを修正"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        lines = content.splitlines()
        
        # 1.0 壊れたf-stringを修正
        content = re.sub(r'f"([^"]*)"([^"]*)"', r'f"\1\2"', content)
        content = re.sub(r"f'([^']*)'([^']*)'", r"f'\1\2'", content)
        
        # 2.0 continue文の不正使用を修正（ループ外）
        content = re.sub(r'\s+continue\s*#\s*Early return.*\n', '\n', content)
        
        # 3.0 壊れた引用符を修正
        content = re.sub(r'f"f"([^"]*)"', r'f"\1"', content)
        content = re.sub(r'"([^"]*)"([^"]*)"([^"]*)"', r'"\1\2\3"', content)
        
        # 4.0 インデントエラー（docstringの位置）
        lines = content.splitlines()
        for i, line in enumerate(lines):
            # docstringが間違った位置にある場合
            if i > 0 and '"""' in line and not line.strip().startswith('"""'):
                # 前の行が関数定義かチェック
                prev_line = lines[i-1].strip()
                if prev_line.endswith(':'):
                    # docstringを正しい位置に移動
                    indent = len(lines[i-1]) - len(lines[i-1].lstrip()) + 4
                    lines[i] = ' ' * indent + line.strip()
        
        content = '\n'.join(lines)
        
        # 5.0 未閉じの括弧を検出・修正
        open_parens = content.count('(') - content.count(')')
        open_brackets = content.count('[') - content.count(']')
        open_braces = content.count('{') - content.count('}')
        
        if open_parens > 0:
            content += ')' * open_parens
        if open_brackets > 0:
            content += ']' * open_brackets
        if open_braces > 0:
            content += '}' * open_braces
            
        # 修正後の構文チェック
        try:
            ast.parse(content)
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
        except SyntaxError:
            pass
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    
    return False

def main():
    """メイン実行"""
    print("🚨 Emergency Syntax Error Fix - Issue #291 Continue")
    print("=" * 60)
    
    # 構文エラーファイルを検出
    print("📍 構文エラーファイル検出中...")
    error_files = find_syntax_errors()
    
    if not error_files:
        print("✅ 構文エラーなし！")
        return
        
    print(f"🔍 {len(error_files)}個の構文エラーファイルを検出")
    
    # 修正実行
    fixed_count = 0
    for file_path, error_msg in error_files[:50]:  # 最初の50件を処理
        print(f"🔧 修正中: {file_path}")
        if fix_common_syntax_errors(file_path):
            fixed_count += 1
            print(f"✅ 修正完了: {file_path}")
        else:
            print(f"❌ 修正失敗: {file_path} - {error_msg}")
    
    print("=" * 60)
    print(f"📊 修正結果: {fixed_count}/{len(error_files[:50])} ファイル修正")
    
    # 残りのエラー確認
    remaining_errors = find_syntax_errors()
    print(f"🔍 残存構文エラー: {len(remaining_errors)}個")

if __name__ == "__main__":
    main()