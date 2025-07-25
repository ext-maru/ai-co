#!/usr/bin/env python3
"""
Fix method definition syntax errors
"""

import re
import sys

def fix_method_definitions(filepath):
    """メソッド定義の構文エラーを修正"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # パターン1: def method(self)code
            match = re.match(r'^(\s*)def\s+(\w+)\s*\(([^)]*)\)(.+)$', line)
            if match and not match.group(4).strip().startswith(':'):
                indent = match.group(1)
                method_name = match.group(2)
                params = match.group(3)
                rest = match.group(4).strip()
                
                # 次の行がdocstringの場合
                if i + 1 < len(lines) and '"""' in lines[i + 1]:
                    fixed_lines.append(f'{indent}def {method_name}({params}):\n')
                    fixed_lines.append(lines[i + 1])  # docstring
                    if rest:
                        # restの内容を適切なインデントで追加
                        fixed_lines.append(f'{indent}    {rest}\n')
                    i += 2
                else:
                    fixed_lines.append(f'{indent}def {method_name}({params}):\n')
                    if rest:
                        fixed_lines.append(f'{indent}    {rest}\n')
                    i += 1
            else:
                fixed_lines.append(line)
                i += 1
        
        # ファイルに書き戻す
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
            
        return True
        
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False

def main():
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        if fix_method_definitions(filepath):
            print(f"✅ Fixed: {filepath}")
        else:
            print(f"❌ Failed: {filepath}")
    else:
        # デフォルトで問題のあるファイルを修正
        files = [
            'libs/knowledge_consolidator.py',
            'libs/elder_scheduled_tasks.py',
            'libs/ai_test_generator.py',
            'libs/auto_adaptation_engine.py',
            'libs/intelligent_test_generator.py'
        ]
        
        for filepath in files:
            if fix_method_definitions(filepath):
                print(f"✅ Fixed: {filepath}")
            else:
                print(f"❌ Failed: {filepath}")

if __name__ == '__main__':
    main()