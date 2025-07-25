#!/usr/bin/env python3
"""
Pattern Analyzer Type Annotation Fix Script
"""
import re

def fix_type_annotations():
    filepath = 'libs/pattern_analyzer.py'
    
    with open(filepath) as f:
        content = f.read()
    
    # パターン1: def method(param:\n    """docstring"""\n    type):
    fixes = [
        (r'def\s+(\w+)\s*\([^)]*?:\s*\n\s*"""([^"]*)"""\s*\n\s*([^)]+)\s*\):', 
         r'def \1(\3):\n        """\2"""'),
    ]
    
    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print('✅ Pattern Analyzer type annotations fixed')

if __name__ == '__main__':
    fix_type_annotations()