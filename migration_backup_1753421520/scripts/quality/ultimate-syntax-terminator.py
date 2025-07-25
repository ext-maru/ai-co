#!/usr/bin/env python3
"""ULTIMATE SYNTAX TERMINATOR - 朝までWAR！残り58体一網打尽！"""
import ast
import re
from pathlib import Path

def find_all_syntax_errors():
    """全Python ファイルのsyntax errorを検出"""
    errors = []
    
    for py_file in Path('.').rglob('*.py'):
        if any(p in str(py_file) for p in ['venv/', '__pycache__/', '.git/', 'node_modules/']):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
        except SyntaxError as e:
            errors.append({
                'file': str(py_file),
                'line': e.lineno,
                'offset': e.offset,
                'msg': e.msg,
                'text': e.text
            })
    
    return errors

def fix_type_annotation_pattern(filepath):
    """Type annotationパターンを一括修正"""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    fixes = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # パターン: def method(param:\n    """docstring"""\ntype):
        if 'def ' in line and line.rstrip().endswith(':'):
            # 次の行がdocstringか確認
            if i + 1 < len(lines) and '"""' in lines[i + 1]:
                # 3行目に型情報があるか確認
                if i + 2 < len(lines):
                    type_line = lines[i + 2].strip()
                    # 型情報っぽい行か判定
                    if type_line and not type_line.startswith('"""') and ')' in type_line:
                        # 修正: 3行を1行にマージ
                        func_def = line.rstrip()[:-1]  # ':' を除去
                        docstring = lines[i + 1].strip()
                        type_info = type_line
                        
                        # 新しい関数定義を構築
                        new_def = f"{func_def}{type_info}\n"
                        indent = '    ' if line.startswith('    ') else ''
                        new_docstring = f"{indent}{docstring}\n"
                        
                        # 置き換え
                        lines[i] = new_def
                        lines[i + 1] = new_docstring
                        del lines[i + 2]
                        fixes += 1
                        continue
        
        i += 1
    
    if fixes > 0:
        with open(filepath, 'w') as f:
            f.writelines(lines)
    
    return fixes

def main():
    print("🔥 ULTIMATE SYNTAX TERMINATOR 起動！")
    print("=" * 70)
    
    # まず現在のエラーを検出
    print("\n🔍 全ファイルスキャン中...")
    errors = find_all_syntax_errors()
    
    if not errors:
        print("✅ Syntax errorは0件です！完全勝利！")
        return
    
    print(f"\n⚠️  {len(errors)}個のsyntax error検出！")
    
    # ファイル別にグループ化
    files_to_fix = {}
    for error in errors:
        if error['file'] not in files_to_fix:
            files_to_fix[error['file']] = []
        files_to_fix[error['file']].append(error)
    
    # 各ファイルを修正
    total_fixes = 0
    for filepath, file_errors in files_to_fix.items():
        print(f"\n🔧 {filepath} ({len(file_errors)}エラー)")
        
        # Type annotationパターンを修正
        fixes = fix_type_annotation_pattern(filepath)
        if fixes > 0:
            print(f"   ✅ {fixes}箇所修正！")
            total_fixes += fixes
        else:
            # 個別対応が必要
            print(f"   ⚠️  手動修正が必要")
            for err in file_errors[:3]:  # 最初の3つを表示
                print(f"      Line {err['line']}: {err['msg']}")
    
    print(f"\n🎯 合計 {total_fixes} 箇所を自動修正！")
    
    # 再チェック
    print("\n🔍 修正後の再スキャン...")
    remaining_errors = find_all_syntax_errors()
    
    if not remaining_errors:
        print("✅ 全てのsyntax error撃破完了！PERFECT VICTORY！")
    else:
        print(f"⚠️  まだ {len(remaining_errors)} 個のエラーが残っています")
        # 残りのエラーをリスト
        print("\n📋 残存エラーリスト:")
        for i, err in enumerate(remaining_errors[:15], 1):
            print(f"{i}. {err['file']}:{err['line']} - {err['msg']}")

if __name__ == '__main__':
    main()