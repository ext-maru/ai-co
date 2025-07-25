#!/usr/bin/env python3
"""Database Manager専用修正スクリプト"""
import re

def fix_database_manager():
    filepath = 'libs/database_manager.py'
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # パターン: def method(param:\n    """docstring"""\ntype):
    pattern = r'def\s+(\w+)\s*\(([^:)]*?):\s*\n\s*"""([^"]*?)"""\s*\n\s*([^)]+)\s*\):'
    
    def replacement(match):
        method_name = match.group(1)
        params_before = match.group(2).strip()
        docstring = match.group(3)
        type_after = match.group(4).strip()
        
        if params_before:
            full_params = f'{params_before}: {type_after}'
        else:
            full_params = type_after
            
        return f'def {method_name}({full_params}):\n        """{docstring}"""'
    
    fixed_content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    
    with open(filepath, 'w') as f:
        f.write(fixed_content)
    
    print('✅ database_manager.py: 修正完了！')

if __name__ == '__main__':
    fix_database_manager()