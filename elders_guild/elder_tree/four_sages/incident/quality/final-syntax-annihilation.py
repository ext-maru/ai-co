#!/usr/bin/env python3
"""
FINAL SYNTAX ANNIHILATION - 完全殲滅作戦
残存136体のシンタックスエラーを一掃する最終兵器
"""

import ast
import os
import re
from pathlib import Path
from collections import defaultdict

def fix_all_syntax_errors(content):
    """すべての既知のシンタックスエラーパターンを修正"""
    lines = content.split('\n')
    fixed_lines = []
    in_multiline_string = False
    multiline_quote_type = None
    
    for i, line in enumerate(lines):
        # マルチライン文字列の検出
        if '"""' in line or "'''" in line:
            triple_double = line.count('"""')
            triple_single = line.count("'''")
            
            if triple_double % 2 == 1:
                if not in_multiline_string:
                    in_multiline_string = True
                    multiline_quote_type = '"""'
                elif multiline_quote_type == '"""':
                    in_multiline_string = False
                    
            if triple_single % 2 == 1:
                if not in_multiline_string:
                    in_multiline_string = True
                    multiline_quote_type = "'''"
                elif multiline_quote_type == "'''":
                    in_multiline_string = False
        
        # マルチライン文字列内ではスキップ
        if in_multiline_string and not ('"""' in line or "'''" in line):
            fixed_lines.append(line)
            continue
            
        # パターン1: 型アノテーション位置エラー
        if i < len(lines) - 2:
            # def method(self, param:\n    """docstring"""\ntype) -> result:
            if (re.match(r'^(\s*)def\s+\w+\s*\([^)]*:\s*$', line) and 
                i + 1 < len(lines) and '"""' in lines[i + 1] and
                i + 2 < len(lines) and re.match(r'^[^)]*\)', lines[i + 2])):
                
                # 次の行のdocstringを取得
                docstring_line = lines[i + 1]
                param_end_line = lines[i + 2]
                
                # パラメータの型を抽出
                type_match = re.match(r'^([^)]*)\)', param_end_line)
                if type_match:
                    param_type = type_match.group(1).strip()
                    # 改行を削除して1行に
                    fixed_line = line.rstrip() + ' ' + param_type + '):'
                    fixed_lines.append(fixed_line)
                    fixed_lines.append(docstring_line)
                    # param_end_lineはスキップ
                    lines[i + 2] = ''  # 空行に置換
                    continue
        
        # パターン2: メソッド定義の改行エラー
        method_match = re.match(r'^(\s*)def\s+(\w+)\s*\(([^)]*?)(\s*)$', line)
        if method_match and not line.rstrip().endswith(':'):
            indent = method_match.group(1)
            method_name = method_match.group(2)
            params = method_match.group(3)
            
            # 次の行を確認
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # ドキュメント文字列の場合
                if '"""' in next_line:
                    # 型アノテーションを探す
                    if i + 2 < len(lines):
                        type_line = lines[i + 2]
                        type_match = re.match(r'^([^)]*)\)\s*(?:->.*)?:\s*$', type_line)
                        if type_match:
                            remaining_params = type_match.group(1).strip()
                            # パラメータを結合
                            if params:
                                params += ', ' + remaining_params
                            else:
                                params = remaining_params
                            # returnタイプを抽出
                            return_match = re.search(r'->\s*([^:]+):', type_line)
                            if return_match:
                                return_type = return_match.group(1).strip()
                                fixed_line = f"{indent}def {method_name}({params}) -> {return_type}:"
                            else:
                                fixed_line = f"{indent}def {method_name}({params}):"
                            fixed_lines.append(fixed_line)
                            fixed_lines.append(next_line)
                            lines[i + 2] = ''  # スキップ
                            continue
        
        # パターン3: sqlite3 -> sqlite3
        line = re.sub(r'\bsqlite3\.0\b', 'sqlite3', line)
        
        # パターン4: 不正な小数リテラル
        line = re.sub(r'(\w+)\.0(\w+)', r'\1.\2', line)
        line = re.sub(r'\.0lower\(\)', '.lower()', line)
        line = re.sub(r'\.0upper\(\)', '.upper()', line)
        line = re.sub(r'\.0get\(', '.get(', line)
        line = re.sub(r'\.0intersection\(', '.intersection(', line)
        line = re.sub(r'\.0union\(', '.union(', line)
        
        # パターン5: 改行位置の修正
        # def func(param) -> type"""docstring""":
        func_with_docstring = re.match(r'^(\s*)def\s+(\w+)\s*\(([^)]*)\)\s*(->\s*[^:]+)?"""([^"]+)""":\s*$', line)
        if func_with_docstring:
            indent = func_with_docstring.group(1)
            func_name = func_with_docstring.group(2)
            params = func_with_docstring.group(3)
            return_type = func_with_docstring.group(4) or ''
            docstring = func_with_docstring.group(5)
            
            fixed_lines.append(f"{indent}def {func_name}({params}){return_type}:")
            fixed_lines.append(f'{indent}    """{docstring}"""')
            continue
        
        # パターン6: 関数定義の継続行
        # def function(self)self.variable = value のパターン
        invalid_def = re.match(r'^(\s*)def\s+(\w+)\s*\(([^)]*)\)(.+)$', line)
        if invalid_def and not line.rstrip().endswith(':'):
            indent = invalid_def.group(1)
            func_name = invalid_def.group(2)
            params = invalid_def.group(3)
            remaining = invalid_def.group(4)
            
            # コロンを追加
            fixed_lines.append(f"{indent}def {func_name}({params}):")
            # 残りの部分を次の行に
            if remaining.strip():
                fixed_lines.append(f"{indent}    {remaining.strip()}")
            continue
        
        # パターン7: return文の修正
        # def func() -> typeif condition:
        return_if_pattern = re.match(r'^(\s*)def\s+(\w+)\s*\(([^)]*)\)\s*->\s*(\w+)if\s+(.+):\s*$', line)
        if return_if_pattern:
            indent = return_if_pattern.group(1)
            func_name = return_if_pattern.group(2)
            params = return_if_pattern.group(3)
            return_type = return_if_pattern.group(4)
            condition = return_if_pattern.group(5)
            
            fixed_lines.append(f"{indent}def {func_name}({params}) -> {return_type}:")
            fixed_lines.append(f"{indent}    if {condition}:")
            continue
        
        # パターン8: except節の修正
        # except Exceptionlogger.error()
        except_pattern = re.match(r'^(\s*)except\s+(\w+(?:\s+as\s+\w+)?)(.+)$', line)
        if except_pattern and not line.rstrip().endswith(':'):
            indent = except_pattern.group(1)
            exception = except_pattern.group(2)
            remaining = except_pattern.group(3)
            
            fixed_lines.append(f"{indent}except {exception}:")
            if remaining.strip():
                fixed_lines.append(f"{indent}    {remaining.strip()}")
            continue
        
        # パターン9: with文の修正
        # with sqlite3connect(...) as conn:
        with_pattern = re.match(r'^(\s*)with\s+sqlite3connect\(', line)
        if with_pattern and 'sqlite3connect' in line:
            line = line.replace('sqlite3connect', 'sqlite3.connect')
        
        # パターン10: f-stringの修正
        # f"string"続き" -> f"string続き"
        line = re.sub(r'"\s*"(?=[^"]*")', '', line)
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def check_and_fix_file(file_path):
    """ファイルのシンタックスエラーをチェックして修正"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # まず現在のコードをパース
        try:
            ast.parse(content)
            return True, None  # エラーなし
        except SyntaxError as e:
            # エラーがある場合は修正を試みる
            fixed_content = fix_all_syntax_errors(content)
            
            # 修正後のコードをパース
            try:
                ast.parse(fixed_content)
                # 修正成功
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                return True, f"Fixed: {e}"
            except SyntaxError as e2:
                return False, f"Still has error: {e2}"
                
    except Exception as e:
        return False, f"Error processing file: {e}"

def main():
    """メイン処理"""
    print("🔥 FINAL SYNTAX ANNIHILATION - 完全殲滅作戦開始！")
    
    # プロジェクトルート
    project_root = Path('/home/aicompany/ai_co')
    
    # エラーのあるファイルを特定
    error_files = []
    total_files = 0
    
    print("\n📡 スキャン開始...")
    for py_file in project_root.rglob('*.py'):
        if any(skip in str(py_file) for skip in ['.venv', '__pycache__', 'node_modules', '.git']):
            continue
            
        total_files += 1
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
        except SyntaxError as e:
            error_files.append((py_file, e))
        except Exception:
            pass
    
    print(f"\n🎯 検出されたエラーファイル: {len(error_files)}/{total_files}")
    
    # エラーを修正
    fixed_count = 0
    still_error_count = 0
    
    for file_path, original_error in error_files:
        print(f"\n🔧 修正中: {file_path}")
        print(f"   元のエラー: {original_error}")
        
        success, result = check_and_fix_file(file_path)
        
        if success and result:  # 修正された
            print(f"   ✅ 修正成功！")
            fixed_count += 1
        elif success and not result:  # 元々エラーなし
            print(f"   ⚠️  エラーなし（誤検出？）")
        else:  # まだエラーあり
            print(f"   ❌ {result}")
            still_error_count += 1
    
    # 最終チェック
    print("\n\n🔍 最終チェック実行中...")
    remaining_errors = []
    for py_file in project_root.rglob('*.py'):
        if any(skip in str(py_file) for skip in ['.venv', '__pycache__', 'node_modules', '.git']):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
        except SyntaxError as e:
            remaining_errors.append((py_file, e))
    
    print(f"\n\n🎯 作戦結果:")
    print(f"   修正成功: {fixed_count}")
    print(f"   修正失敗: {still_error_count}")
    print(f"   残存エラー: {len(remaining_errors)}")
    
    if remaining_errors:
        print(f"\n❌ まだ {len(remaining_errors)} 個のエラーが残っています:")
        for file_path, error in remaining_errors[:10]:
            print(f"   {file_path}: {error}")
    else:
        print("\n🎉 完全勝利！すべてのシンタックスエラーが撃破されました！")

if __name__ == "__main__":
    main()