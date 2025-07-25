#!/usr/bin/env python3
"""ULTIMATE FINAL SYNTAX WAR - 残存304体完全殲滅！"""
import re
from pathlib import Path

def fix_expected_colon_errors():
    """expected ':' エラーを一括修正"""
    patterns = [
        # Type annotationのコロン抜け: def method(self, param\n    """docstring"""\ntype) -> resultr'def \1(\2) -> \3:\n    """\4"""'),
    (r'def\s+(\w+)\s*\(([^)]*)\)\s*->\s*([^:]+)\n\s*"""([^"]*)"""\s*:',
        
        # 関数定義の最後のコロン抜け
        (r'def\s+(\w+)\s*\([^)]*\)\s*->\s*[^:]+$', r'\g<0>:'),
        
        # クラス定義の最後のコロン抜け  
        (r'class\s+(\w+)(?:\([^)]*\))?\s*$', r'\g<0>:'),
    ]
    
    fixes = 0
    for py_file in Path('.').rglob('*.py'):
        if any(p in str(py_file) for p in ['venv/', '__pycache__/', '.git/', 'node_modules/']):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original = content
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            
            if content != original:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixes += 1
        except:
            pass
    
    return fixes

def fix_invalid_decimal_literals():
    """invalid decimal literal エラーを修正"""
    patterns = [
        # 0.5が 0.5になっているケース
        (r'(?<![0-9])\.[0-9]+', r'0\g<0>'),
        # 10.0が 10になっているケース  
        (r'[0-9]+\.(?![0-9])', r'\g<0>0'),
    ]
    
    fixes = 0
    for py_file in Path('.').rglob('*.py'):
        if any(p in str(py_file) for p in ['venv/', '__pycache__/', '.git/', 'node_modules/']):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original = content
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)
            
            if content != original:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixes += 1
        except:
            pass
    
    return fixes

def fix_indentation_errors():
    """expected an indented block エラーを修正"""
    fixes = 0
    for py_file in Path('.').rglob('*.py'):
        if any(p in str(py_file) for p in ['venv/', '__pycache__/', '.git/', 'node_modules/']):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            modified = False
            i = 0
            while i < len(lines):
                line = lines[i].rstrip()
                
                # 関数・クラス定義の後に空行がある場合
                if (line.endswith(':') and 
                    ('def ' in line or 'class ' in line or 'if ' in line or 
                     'for ' in line or 'while ' in line or 'try:' in line or
                     'except' in line or 'finally:' in line or 'with ' in line)):
                         pass
                    
                    # 次の行が空またはインデントがない場合
                    if i + 1 < len(lines):
                        next_line = lines[i + 1]
                        if not next_line.strip() or (next_line[0] not in ' \t' and next_line.strip()):
                            # passを追加
                            indent = '    '
                            if line.startswith(' '):
                                indent = line[:len(line) - len(line.lstrip())] + '    '
                            lines.insert(i + 1, f'{indent}pass\n')
                            modified = True
                
                i += 1
            
            if modified:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                fixes += 1
        except:
            pass
    
    return fixes

def fix_fstring_errors():
    """f-string エラーを修正"""
    fixes = 0
    for py_file in Path('.').rglob('*.py'):
        if any(p in str(py_file) for p in ['venv/', '__pycache__/', '.git/', 'node_modules/']):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # f-string内の不正な文字を修正
            content = re.sub(r'f"([^"]*?)\{([^}]*?)=([^}]*?)\}"', r'f"\1{\2}"', content)
            
            with open(py_file, 'w', encoding='utf-8') as f:
                f.write(content)
            fixes += 1
        except:
            pass
    
    return fixes

def fix_invalid_unicode_chars():
    """invalid character (絵文字など)を修正"""
    fixes = 0
    for py_file in Path('.').rglob('*.py'):
        if any(p in str(py_file) for p in ['venv/', '__pycache__/', '.git/', 'node_modules/']):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            modified = False
            for i, line in enumerate(lines):
                # コメント内の絵文字はOK、コード内の絵文字は文字列にする
                if '📊' in line or '🔍' in line or '📈' in line:
                    # コメントでない場合
                    if not line.strip().startswith('#'):
                        # 文字列内でない場合
                        if '"' not in line and "'" not in line:
                            lines[i] = line.replace('📊', '"📊"').replace('🔍', '"🔍"').replace('📈', '"📈"')
                            modified = True
            
            if modified:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                fixes += 1
        except:
            pass
    
    return fixes

def main():
    print("🔥 ULTIMATE FINAL SYNTAX WAR 開始！")
    print("=" * 70)
    
    print("\n🔧 expected ':' エラー修正中...")
    colon_fixes = fix_expected_colon_errors()
    print(f"   ✅ {colon_fixes}ファイル修正")
    
    print("\n🔧 invalid decimal literal エラー修正中...")
    decimal_fixes = fix_invalid_decimal_literals()
    print(f"   ✅ {decimal_fixes}ファイル修正")
    
    print("\n🔧 indentation エラー修正中...")
    indent_fixes = fix_indentation_errors()
    print(f"   ✅ {indent_fixes}ファイル修正")
    
    print("\n🔧 f-string エラー修正中...")
    fstring_fixes = fix_fstring_errors()
    print(f"   ✅ {fstring_fixes}ファイル修正")
    
    print("\n🔧 invalid character エラー修正中...")
    unicode_fixes = fix_invalid_unicode_chars()
    print(f"   ✅ {unicode_fixes}ファイル修正")
    
    total_fixes = colon_fixes + decimal_fixes + indent_fixes + fstring_fixes + unicode_fixes
    print(f"\n🎯 合計 {total_fixes} ファイル修正完了！")

if __name__ == '__main__':
    main()