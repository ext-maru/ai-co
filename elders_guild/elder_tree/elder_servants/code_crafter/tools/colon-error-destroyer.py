#!/usr/bin/env python3
"""
Colon Error Destroyer - コロンエラー専門殲滅スクリプト
"""

import re
import os
from pathlib import Path

def fix_colon_errors():
    """コロンエラーを修正"""
    project_root = Path(__file__).parent.parent.parent
    py_files = list(project_root.rglob('*.py'))
    
    fixes_applied = 0
    files_modified = 0
    
    for file_path in py_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Pattern 1: def method(self) -> Type:
            # Missing colon after function definition
            pattern1 = re.compile(r'def\s+(\w+)\s*\([^)]*\)\s*(?:->\s*[^:]+)?\s*\n\s*"""')
            for match in pattern1.finditer(content):
                before = content[:match.start()]
                after = content[match.end()-3:]  # Keep the """
                
                # Extract the function signature
                func_sig = match.group(0).replace('"""', '')
                if not func_sig.rstrip().endswith(':'):
                    func_sig = func_sig.rstrip() + ':'
                
                content = before + func_sig + '\n    """' + after[4:]  # Skip original """
                fixes_applied += 1
            
            # Pattern 2: Missing colon after class definition
            pattern2 = re.compile(r'class\s+(\w+)(?:\([^)]*\))?\s*\n\s*"""')
            for match in pattern2.finditer(content):
                before = content[:match.start()]
                after = content[match.end()-3:]
                
                class_sig = match.group(0).replace('"""', '')
                if not class_sig.rstrip().endswith(':'):
                    class_sig = class_sig.rstrip() + ':'
                
                content = before + class_sig + '\n    """' + after[4:]
                fixes_applied += 1
                
            # Pattern 3: __init__ method without colon
            pattern3 = re.compile(r'def\s+__init__\s*\([^)]*\)\s*\n\s*"""')
            for match in pattern3.finditer(content):
                before = content[:match.start()]
                after = content[match.end()-3:]
                
                init_sig = match.group(0).replace('"""', '')
                if not init_sig.rstrip().endswith(':'):
                    init_sig = init_sig.rstrip() + ':'
                
                content = before + init_sig + '\n        """' + after[4:]
                fixes_applied += 1
            
            # Pattern 4: Method calls like super().__init__(...)
            content = re.sub(
                r'def __init__\(self\)(super\(\).__init__\()',
                r'def __init__(self):\n        """\1',
                content
            )
            
            # Pattern 5: Lines ending with function definitions without colons
            lines = content.split('\n')
            modified_lines = []
            for i, line in enumerate(lines):
                # Check if it's a function definition without colon
                if (re.match(r'^\s*def\s+\w+\s*\([^)]*\)\s*(?:->\s*\w+)?\s*$', line) and 
                    not line.strip().endswith(':')):
                    line = line.rstrip() + ':'
                    fixes_applied += 1
                
                # Check if it's a class definition without colon
                elif (re.match(r'^\s*class\s+\w+(?:\([^)]*\))?\s*$', line) and 
                      not line.strip().endswith(':')):
                    line = line.rstrip() + ':'
                    fixes_applied += 1
                
                modified_lines.append(line)
            
            content = '\n'.join(modified_lines)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                files_modified += 1
                print(f"🔧 Fixed {file_path.relative_to(project_root)}")
                
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            continue
    
    print(f"\n✅ Colon Error Destroyer 完了!")
    print(f"   修正ファイル数: {files_modified}")
    print(f"   適用修正数: {fixes_applied}")

if __name__ == "__main__":
    fix_colon_errors()