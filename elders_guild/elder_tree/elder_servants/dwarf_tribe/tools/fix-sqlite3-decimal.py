#!/usr/bin/env python3
"""sqlite3connect問題修正 - 誤って追加された小数点を除去"""
import re
from pathlib import Path

def fix_sqlite3_decimal():
    """sqlite3のような誤った小数点を修正"""
    errors_fixed = 0
    
    for py_file in Path('.').rglob('*.py'):
        if any(p in str(py_file) for p in ['venv/', '__pycache__/', '.git/', 'node_modules/']):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original = content
            
            # sqlite3 -> sqlite3
            content = re.sub(r'sqlite3\.0', 'sqlite3', content)
            
            # boto3 -> boto3
            content = re.sub(r'boto3\.0', 'boto3', content)
            
            # その他の一般的なモジュール名の修正
            modules = ['requests', 'numpy', 'pandas', 'torch', 'tensorflow', 'sklearn']
            for module in modules:
                content = re.sub(f'{module}\\.0', module, content)
            
            if content != original:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                errors_fixed += 1
                print(f"✅ Fixed: {py_file}")
        except:
            pass
    
    return errors_fixed

def main():
    print("🔧 sqlite3問題修正開始...")
    print("=" * 50)
    
    fixes = fix_sqlite3_decimal()
    
    print(f"\n✅ {fixes}ファイル修正完了！")

if __name__ == '__main__':
    main()