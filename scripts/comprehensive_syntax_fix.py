#!/usr/bin/env python3
"""
Comprehensive syntax error fixer using multiple approaches
"""

import os
import re
import ast
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional

class ComprehensiveSyntaxFixer:
    def __init__(self):
        self.fixed_count = 0
        self.patterns = [
            # Pattern 1: def method()code on same line
            (r'^(\s*)def\s+(\w+)\s*\(([^)]*)\)(.+)$', self.fix_method_definition),
            
            # Pattern 2: return type on wrong line
            (r'^(\s*)->?\s*(\w+[\[\]]*):?\s*$', self.fix_return_type),
            
            # Pattern 3: continue outside loop
            (r'^(\s*)continue\s*(?:#.*)?$', self.fix_continue_statement),
            
            # Pattern 4: duplicate colons
            (r':\s*:', self.fix_duplicate_colons),
            
            # Pattern 5: missing colons after def
            (r'^(\s*)def\s+(\w+)\s*\(([^)]*)\)\s*$', self.fix_missing_colon),
        ]
        
    def fix_method_definition(self, match, lines, i):
        """Fix method definition with code on same line"""
        indent = match.group(1)
        method_name = match.group(2)
        params = match.group(3)
        rest = match.group(4).strip()
        
        if rest and not rest.startswith(':'):
            # Check if next line is docstring
            if i + 1 < len(lines) and '"""' in lines[i + 1]:
                return [f'{indent}def {method_name}({params}):\n'], 1
            else:
                return [f'{indent}def {method_name}({params}):\n', f'{indent}    {rest}\n'], 1
        return None, 0
        
    def fix_return_type(self, match, lines, i):
        """Fix return type on wrong line"""
        # Look at previous line
        if i > 0:
            prev_line = lines[i - 1].rstrip()
            if re.match(r'^(\s*)def\s+\w+\s*\([^)]*\)\s*$', prev_line):
                # Merge with previous line
                lines[i - 1] = prev_line + ' ' + lines[i].strip() + '\n'
                return [], 1  # Remove current line
        return None, 0
        
    def fix_continue_statement(self, match, lines, i):
        """Fix continue outside loop"""
        # Simply comment it out
        indent = match.group(1)
        return [f'{indent}# Removed invalid continue statement\n'], 1
        
    def fix_duplicate_colons(self, match, lines, i):
        """Fix duplicate colons"""
        return [lines[i].replace('::', ':')], 1
        
    def fix_missing_colon(self, match, lines, i):
        """Add missing colon after method definition"""
        line = lines[i].rstrip()
        if not line.endswith(':'):
            return [line + ':\n'], 1
        return None, 0
        
    def fix_file(self, filepath):
        """Fix syntax errors in a file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # First pass: try to compile and identify syntax errors
            try:
                compile(content, filepath, 'exec')
                return True  # No syntax errors
            except SyntaxError as e:
                print(f"  Syntax error in {filepath} at line {e.lineno}: {e.msg}")
                
            # Second pass: apply fixes
            lines = content.splitlines(True)
            fixed_lines = []
            i = 0
            
            while i < len(lines):
                line = lines[i]
                fixed = False
                
                for pattern, fixer in self.patterns:
                    match = re.match(pattern, line)
                    if match:
                        replacement, skip = fixer(match, lines, i)
                        if replacement is not None:
                            fixed_lines.extend(replacement)
                            i += skip
                            fixed = True
                            break
                            
                if not fixed:
                    fixed_lines.append(line)
                    i += 1
                    
            # Third pass: specific fixes for knowledge_consolidator.py patterns
            content = ''.join(fixed_lines)
            
            # Fix "def method() -> Type:" pattern
            content = re.sub(
                r'def\s+(\w+)\s*\(([^)]*)\):\s*\n\s*"""([^"]+)"""\s*\n\s*->\s*(\w+[\[\]]*):',
                r'def \1(\2) -> \4:\n    """\3"""',
                content
            )
            
            # Fix standalone colons
            content = re.sub(r'\n(\s*):(\s*\n)', r'\n', content)
            
            # Fix method with immediate dictionary
            content = re.sub(
                r'def\s+(\w+)\s*\(([^)]*)\):\s*\n(\s*)\{\s*:',
                r'def \1(\2):\n\3return {',
                content
            )
            
            # Write back
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
            # Verify fix
            try:
                compile(content, filepath, 'exec')
                self.fixed_count += 1
                return True
            except SyntaxError as e:
                print(f"  Still has error at line {e.lineno}: {e.msg}")
                return False
                
        except Exception as e:
            print(f"  Error processing {filepath}: {e}")
            return False
            
    def run(self, directory='libs', max_files=None):
        """Run the fixer on a directory"""
        print(f"🔍 Scanning {directory} for syntax errors...")
        
        error_files = []
        checked = 0
        
        # First, find all files with syntax errors
        for root, dirs, files in os.walk(directory):
            if any(skip in root for skip in ['venv', 'site-packages', '.git', '__pycache__']):
                continue
                
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    checked += 1
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            compile(f.read(), filepath, 'exec')
                    except SyntaxError:
                        error_files.append(filepath)
                        
                    if max_files and checked >= max_files:
                        break
                        
        print(f"\n📊 Found {len(error_files)} files with syntax errors out of {checked} checked")
        
        if not error_files:
            print("✅ No syntax errors found!")
            return
            
        # Fix errors
        print(f"\n🔧 Attempting to fix {len(error_files)} files...")
        
        fixed = 0
        for filepath in error_files:
            print(f"\nProcessing: {filepath}")
            if self.fix_file(filepath):
                print(f"  ✅ Fixed!")
                fixed += 1
            else:
                print(f"  ❌ Failed to fix completely")
                
        print(f"\n📊 Summary:")
        print(f"  - Files with errors: {len(error_files)}")
        print(f"  - Successfully fixed: {fixed}")
        print(f"  - Still have errors: {len(error_files) - fixed}")

def main():
    fixer = ComprehensiveSyntaxFixer()
    
    # Priority directories
    directories = [
        ('libs/elder_servants', 100),
        ('libs/integrations', 100),
        ('libs', 200),
    ]
    
    for directory, max_files in directories:
        if os.path.exists(directory):
            print(f"\n{'='*60}")
            print(f"Processing: {directory}")
            print(f"{'='*60}")
            fixer.run(directory, max_files)

if __name__ == '__main__':
    main()