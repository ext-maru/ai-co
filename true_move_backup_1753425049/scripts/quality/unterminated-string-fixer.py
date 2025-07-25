#!/usr/bin/env python3
"""
UNTERMINATED STRING LITERAL FIXER
文字列リテラルエラーを専門に修正
"""

import ast
import re
from pathlib import Path

def fix_unterminated_strings(content):
    """文字列リテラルの終了エラーを修正"""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # パターン1: 単独の"""を閉じる
        if line.strip() == '"""' and i > 0:
            # 前の行を確認
            prev_line = lines[i-1].strip()
            if prev_line.endswith('"""'):
                # すでに閉じられている
                fixed_lines.append(line)
                continue
            elif '"""' in prev_line and not prev_line.count('"""') % 2 == 0:
                # 奇数個の"""がある場合は追加しない
                continue
        
        # パターン2: 行末に開いた"""を閉じる
        if line.count('"""') % 2 == 1 and not line.strip().endswith('"""'):
            line = line.rstrip() + '"""'
        
        # パターン3: f-stringの修正
        # f"text" "more" -> f"text more"
        line = re.sub(r'(f"[^"]*")\s*"([^"]*")', r'\1\2', line)
        
        # パターン4: 継続されたdocstring
        if i > 0 and '"""' in lines[i-1] and lines[i-1].count('"""') == 1:
            # 前の行で開始されたdocstring
            if '"""' not in line:
                # この行にも"""を追加
                if i + 1 < len(lines) and lines[i+1].strip():
                    line = line + '"""'
        
        fixed_lines.append(line)
    
    # 全体をチェックして未完の文字列を修正
    content = '\n'.join(fixed_lines)
    
    # マルチラインdocstringの修正
    content = re.sub(r'"""([^"]+)(?!""")', r'"""\1"""', content, flags=re.DOTALL)
    
    return content

def main():
    """メイン処理"""
    print("🔧 UNTERMINATED STRING LITERAL FIXER")
    
    project_root = Path('/home/aicompany/ai_co')
    error_files = []
    
    # エラーファイルを収集
    for py_file in project_root.rglob('*.py'):
        if any(skip in str(py_file) for skip in ['.venv', '__pycache__', 'node_modules', '.git']):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
        except SyntaxError as e:
            if 'unterminated string literal' in str(e):
                error_files.append((py_file, e))
    
    print(f"\n🎯 見つかったunterminated string literal: {len(error_files)}")
    
    fixed_count = 0
    for file_path, error in error_files:
        print(f"\n修正中: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            fixed_content = fix_unterminated_strings(content)
            
            # テスト
            try:
                ast.parse(fixed_content)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                print("  ✅ 修正成功")
                fixed_count += 1
            except SyntaxError as e:
                print(f"  ❌ まだエラー: {e}")
                
        except Exception as e:
            print(f"  ❌ 処理エラー: {e}")
    
    print(f"\n📊 結果: {fixed_count}/{len(error_files)} 修正")

if __name__ == "__main__":
    main()