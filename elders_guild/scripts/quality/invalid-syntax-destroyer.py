#!/usr/bin/env python3
"""
Invalid Syntax Destroyer - invalid syntax専門殲滅スクリプト
"""

import re
import ast
from pathlib import Path

def fix_invalid_syntax_errors():
    """invalid syntaxエラーを修正"""
    project_root = Path(__file__).parent.parent.parent
    py_files = list(project_root.rglob('*.py'))
    
    fixes_applied = 0
    files_modified = 0
    
    for file_path in py_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Common invalid syntax patterns
            
            # Pattern 1: Missing colon in function definitions
            content = re.sub(
                r'(\n\s*def\s+\w+\s*\([^)]*\))(\s*(?:->\s*[^:\n]+)?)\s*\n(\s*""")',
                r'\1\2:\n\3',
                content
            )
            
            # Pattern 2: Missing colon in class definitions
            content = re.sub(
                r'(\n\s*class\s+\w+(?:\([^)]*\))?)\s*\n(\s*""")',
                r'\1:\n\2',
                content
            )
            
            # Pattern 3: Malformed f-strings - extra 'f' prefix
            content = re.sub(
                r'f"([^"]*)"',
                r'f"\1"',
                content
            )
            
            # Pattern 4: Function definitions without proper colons
            content = re.sub(
                r'(\n\s*def\s+\w+\s*\([^)]*\))\s*([^:\n]*)\n(\s*[^"])',
                lambda m: f"{m.group(1)}:\n{m.group(3)}" if not m.group(2).strip().endswith(':') else m.group(0),
                content
            )
            
            # Pattern 5: Missing colon after control structures
            content = re.sub(
                r'(\n\s*(?:if|elif|else|while|for|with|try|except|finally)\s+[^:\n]*)\n(\s*[^"])',
                lambda m: f"{m.group(1)}:\n{m.group(2)}" if not m.group(1).strip().endswith(':') else m.group(0),
                content
            )
            
            # Pattern 6: Fix malformed method signatures
            content = re.sub(
                r'def (\w+)\(([^)]*)\)([^:\n]*)\n\s*"""([^"]+)"""\n\s*([^:\n]+):',
                r'def \1(\2)\3:\n        """\4"""\n        \5',
                content
            )
            
            # Pattern 7: Fix decimal literals like '3.0.method'
            content = re.sub(
                r'(\d+)\.0([a-zA-Z_]\w*)',
                r'\1.0.\2',
                content
            )
            
            # Pattern 8: Fix malformed sqlite references
            content = re.sub(
                r'sqlite3\.0',
                r'sqlite3',
                content
            )
            
            if content != original_content:
                try:
                    # Validate the fix
                    ast.parse(content)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    files_modified += 1
                    fixes_applied += len(re.findall(r'\n', original_content)) - len(re.findall(r'\n', content)) + 1
                    print(f"🔧 Fixed {file_path.relative_to(project_root)}")
                except SyntaxError:
                    # Fix didn't work, don't apply it
                    pass
                    
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            continue
    
    print(f"\n✅ Invalid Syntax Destroyer 完了!")
    print(f"   修正ファイル数: {files_modified}")
    print(f"   適用修正数: {fixes_applied}")

if __name__ == "__main__":
    fix_invalid_syntax_errors()