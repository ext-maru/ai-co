#!/usr/bin/env python3
"""
Final Syntax Assault - 最終構文攻略戦
🏆 残存構文エラーへの総攻撃
"""
import os
import re
import ast
from pathlib import Path

def get_all_syntax_errors():
    pass


"""全構文エラーを取得""" [],
        'f_string': [],
        'indent': [],
        'other': []
    }
    
    for root, dirs, files in os.walk('./libs'):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        ast.parse(f.read())
                except SyntaxError as e:
                    error_info = {
                        'file': file_path,
                        'line': e.lineno,
                        'msg': e.msg,
                        'text': e.text.strip() if e.text else ''
                    }
                    
                    msg_lower = e.msg.lower()
                    if 'comma' in msg_lower:
                        error_categories['comma'].append(error_info)
                    elif 'f-string' in msg_lower or 'unterminated' in msg_lower:
                        error_categories['f_string'].append(error_info)
                    elif 'indent' in msg_lower:
                        error_categories['indent'].append(error_info)
                    else:
                        error_categories['other'].append(error_info)
                except Exception:
                    pass
    
    return error_categories

def smart_fix_file(file_path: str, error_type: str) -> bool:
    """スマート修正"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        if error_type == 'comma':
            # Comma fixes - 最も強力なパターン
            patterns = [
                # Pattern 1: Basic def with docstring break
                (r'(\s*)(def|async def)\s+([a-zA-Z_]\w*)\s*\(\s*([^)]*?):\s*\n(\s*)"""([^"]*?)"""\s*\n\s*([^)]+?)\):', 
                 r'\1\2 \3(\4: \7):\n\5"""\6"""'),
                
                # Pattern 2: __init__ specific
                (r'(\s*)def\s+__init__\s*\(\s*(self[^)]*?):\s*\n(\s*)"""([^"]*?)"""\s*\n\s*([^)]+?)\):',
                 r'\1def __init__(\2: \5):\n\3"""\4"""'),
                
                # Pattern 3: Multiple parameters
                (r'(\s*)(def|async def)\s+([a-zA-Z_]\w*)\s*\(\s*([^:,]*?),\s*([^)]*?):\s*\n(\s*)"""([^"]*?)"""\s*\n\s*([^)]+?)\):',
                 r'\1\2 \3(\4, \5: \8):\n\6"""\7"""'),
            ]
            
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
        
        elif error_type == 'f_string':
            # F-string fixes
            patterns = [
                # Double f prefix
                (r'f"([^"]+)"', r'f"\1"'),
                # Unterminated f-strings
                (r'f"([^"]*?)([^"]*?)$', r'f"\1\2"'),
            ]
            
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        if content != original:
            try:
                ast.parse(content)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            except SyntaxError:
                return False
        
        return False
        
    except Exception:
        return False

def main():
    pass

        """メイン実行"""")
    print(f"   Total errors: {total_errors}")
    for category, errors in error_categories.items():
        print(f"   {category}: {len(errors)} files")
    
    # カテゴリ別修正実行
    total_fixed = 0
    
    for category, errors in error_categories.items():
        if not errors:
            continue
            
        print(f"\n🔧 Attacking {category} errors ({len(errors)} files)...")
        fixed_count = 0
        
        for error in errors[:20]:  # 各カテゴリ最大20件
            filename = os.path.basename(error['file'])
            if smart_fix_file(error['file'], category):
                print(f"✅ {filename}")
                fixed_count += 1
            else:
                print(f"❌ {filename}")
        
        print(f"   {category} result: {fixed_count}/{min(len(errors), 20)} fixed")
        total_fixed += fixed_count
    
    # 最終結果
    final_errors = get_all_syntax_errors()
    final_total = sum(len(errors) for errors in final_errors.values())
    
    print("=" * 70)
    print(f"🎯 Final Assault Results:")
    print(f"   Before: {total_errors} errors")
    print(f"   Fixed: {total_fixed} files")
    print(f"   After: {final_total} errors")
    print(f"   Reduction: {((total_errors-final_total)/max(1,total_errors)*100):0.1f}%")
    
    if final_total < 50:
        print("\n🎉 Major progress! Under 50 errors remaining!")
    elif final_total < 100:
        print("\n🚀 Good progress! Under 100 errors remaining!")
    else:
        print(f"\n🎯 {final_total} errors still need attention")

if __name__ == "__main__":
    main()