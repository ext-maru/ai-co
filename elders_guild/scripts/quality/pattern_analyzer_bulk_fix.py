#!/usr/bin/env python3
"""Pattern Analyzer一括修正スクリプト - 朝まで戦闘用"""
import re

def bulk_fix_pattern_analyzer():
    filepath = 'libs/pattern_analyzer.py'
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    fixes = 0
    
    # すべてのパターンを一括修正
    patterns = [
        # パターン1: def method(self, data:\n    """docstring"""\nList[Dict]) -> type:
        (r'def\s+(\w+)\s*\(self,\s*data:\s*\n\s*"""([^"]*?)"""\s*\n\s*List\[Dict\]\)\s*->\s*([^:]+):', 
         r'def \1(self, data: List[Dict]) -> \3:\n        """\2"""'),
        
        # パターン2: def method(self, patterns:\n    """docstring"""\nDict) -> type:
        (r'def\s+(\w+)\s*\(self,\s*patterns:\s*\n\s*"""([^"]*?)"""\s*\n\s*Dict\)\s*->\s*([^:]+):', 
         r'def \1(self, patterns: Dict) -> \3:\n        """\2"""'),
         
        # パターン3: def method(self, optimizations:\n    """docstring"""\nList[Dict]) -> type:
        (r'def\s+(\w+)\s*\(self,\s*optimizations:\s*\n\s*"""([^"]*?)"""\s*\n\s*List\[Dict\]\)\s*->\s*([^:]+):', 
         r'def \1(self, optimizations: List[Dict]) -> \3:\n        """\2"""'),
         
        # パターン4: def method(self, results:\n    """docstring"""\nDict) -> type:
        (r'def\s+(\w+)\s*\(self,\s*results:\s*\n\s*"""([^"]*?)"""\s*\n\s*Dict\)\s*->\s*([^:]+):', 
         r'def \1(self, results: Dict) -> \3:\n        """\2"""'),
    ]
    
    for pattern, replacement in patterns:
        new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
        if count > 0:
            content = new_content
            fixes += count
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f'✅ pattern_analyzer.py: {fixes}箇所一括修正完了！')
    return fixes

if __name__ == '__main__':
    bulk_fix_pattern_analyzer()