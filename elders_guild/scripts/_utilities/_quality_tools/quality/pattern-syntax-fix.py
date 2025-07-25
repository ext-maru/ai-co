#!/usr/bin/env python3
"""
Pattern-Based Syntax Error Fix Tool - Issue #291 Continue
🎯 パターンベース構文エラー修正ツール
"""
import os
import re
import ast
from pathlib import Path

def fix_type_annotation_docstring_pattern(content: str) -> str:
    """型アノテーションとdocstringの順序問題を修正"""
    # パターン1: def func(param:\n    """docstring"""\ntype):
    pattern1 = r'def\s+(\w+)\s*\(\s*([^:]+):\s*\n\s*"""([^"]+)"""\s*\n\s*([^)]+)\):'
    def replace1(match):
        func_name, param, docstring, param_type = match.groups()
        return f'def {func_name}({param}: {param_type.strip()}):\n        """{docstring}"""'
    
    content = re.sub(pattern1, replace1, content, flags=re.MULTILINE)
    return content

    """壊れたf-stringを修正"""
    # パターン: f"f"text" -> f"text"
    content = re.sub(r'f"f"([^"]*)"', r'f"\1"', content)
    
    # パターン: f"text"other"text" -> f"textothertext"
    content = re.sub(r'f"([^"]*)"([^"]*)"([^"]*)"', r'f"\1\2\3"', content)
    
    return content

def fix_unterminated_string_pattern(content: str) -> str:
    """未終了文字列を修正"""
    lines = content.splitlines()
    for i, line in enumerate(lines):
        # 奇数個のクォートがある行をチェック
        if line.count('"') % 2 == 1 and not line.strip().endswith('\\'):
            lines[i] = line + '"'
        if line.count("'") % 2 == 1 and not line.strip().endswith('\\'):
            lines[i] = line + "'"
    
    return '\n'.join(lines)

def fix_invalid_character_pattern(content: str) -> str:
    """無効文字を修正"""
    # Unicode box-drawing characters
    content = re.sub(r'[│┌┐└┘├┤┬┴┼]', ' ', content)
    return content

def fix_comma_syntax_pattern(content: str) -> str:
    """カンマ忘れによる構文エラーを修正"""
    lines = content.splitlines()
    for i, line in enumerate(lines):
        # 引数リストでの改行時にカンマが必要なパターン
        if (i < len(lines) - 1 and 
            line.strip() and 
            not line.strip().endswith((',', ':', '(', '[', '{'))):
            next_line = lines[i + 1].strip()
            if (next_line and 
                not next_line.startswith((')', ']', '}', ':', 'def ', 'class ')) and
                '=' in line and '=' in next_line):
                lines[i] = line + ','
    
    return '\n'.join(lines)

def process_file(file_path: str) -> bool:
    """ファイルを処理"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        content = original_content
        
        # パターン別修正を適用
        content = fix_type_annotation_docstring_pattern(content)

        content = fix_unterminated_string_pattern(content)
        content = fix_invalid_character_pattern(content)
        content = fix_comma_syntax_pattern(content)
        
        # 構文チェック
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
    print("🎯 Pattern-Based Syntax Error Fix - Issue #291 Continue")
    print("=" * 60)
    
    # 構文エラーファイル一覧取得
    error_files = []
    for root, dirs, files in os.walk('.'):
        if any(skip in root for skip in ['.git', '__pycache__', '.venv', 'archives']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    ast.parse(content)
                except SyntaxError:
                    error_files.append(file_path)
                except Exception:
                    pass
    
    print(f"🔍 {len(error_files)}個の構文エラーファイルを検出")
    
    # パターンベース修正実行
    fixed_count = 0
    for file_path in error_files[:100]:  # 最初の100件を処理
        if process_file(file_path):
            fixed_count += 1
            print(f"✅ 修正: {file_path}")
        else:
            print(f"⏭️  スキップ: {file_path}")
    
    print("=" * 60)
    print(f"📊 修正結果: {fixed_count}/{min(len(error_files), 100)} ファイル修正")
    
    # 最終確認
    remaining = []
    for file_path in error_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
        except SyntaxError:
            remaining.append(file_path)
        except Exception:
            pass
    
    print(f"🔍 残存構文エラー: {len(remaining)}個")
    return len(remaining)

if __name__ == "__main__":
    main()