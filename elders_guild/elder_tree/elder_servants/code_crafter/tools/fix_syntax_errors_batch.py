#!/usr/bin/env python3
"""
Batch syntax error fixer for the AI Company project
Systematically finds and fixes common syntax error patterns
"""

import os
import re
import sys
import py_compile
import traceback
from pathlib import Path
from typing import List, Tuple, Dict, Set

class SyntaxErrorFixer:
    def __init__(self):
        self.fixed_count = 0
        self.error_patterns = {
            'continue_outside_loop': (
                r'(\s*)if\s+not\s*\([^)]+\):\s*\n\s*continue\s*#.*Early return.*\n\s*#.*\n\s*if\s+[^:]+:',
                lambda m: f"{m.group(1)}if {m.group(0).split('not (')[1].split(')')[0]}:"
            ),
            'malformed_init': (
                r'def __init__\(self\)([^:]+)\n\s*"""',
                r'def __init__(self):\n    """'
            ),
            'unterminated_fstring': (
                r'f"([^"]*)\n\s*f"([^"]*)"',
                r'f"\1\2"'
            ),
            'invalid_decimal': (
                r'(\d+)0(\d+)',
                r'\1\2'
            ),
            'expected_colon': (
                r'def\s+(\w+)\s*\([^)]*\)\s*->\s*(\w+)([^:]+)\n\s*"""',
                r'def \1(self) -> \2:\n    """'
            )
        }
        
    def find_syntax_errors(self, directory: str = '.') -> List[Tuple[str, str]]:
        """Find all Python files with syntax errors"""
        errors = []
        
        for root, dirs, files in os.walk(directory):
            # Skip certain directories
            if any(skip in root for skip in ['venv', 'site-packages', '.git', '__pycache__', 'node_modules']):
                continue
                
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        py_compile.compile(filepath, doraise=True)
                    except py_compile.PyCompileError as e:
                        error_msg = str(e)
                        errors.append((filepath, error_msg))
                    except Exception as e:
                        errors.append((filepath, str(e)))
                        
        return errors
    
    def analyze_error(self, filepath: str, error_msg: str) -> Dict[str, any]:
        """Analyze the error and determine the fix"""
        analysis = {
            'file': filepath,
            'error': error_msg,
            'line': None,
            'type': None,
            'fix': None
        }
        
        # Extract line number
        line_match = re.search(r'line (\d+)', error_msg)
        if line_match:
            analysis['line'] = int(line_match.group(1))
            
        # Determine error type
        if "'continue' not properly in loop" in error_msg:
            analysis['type'] = 'continue_outside_loop'
        elif "expected ':'" in error_msg:
            analysis['type'] = 'expected_colon'
        elif "unterminated" in error_msg and "string" in error_msg:
            analysis['type'] = 'unterminated_fstring'
        elif "invalid decimal literal" in error_msg:
            analysis['type'] = 'invalid_decimal'
            
        return analysis
    
    def fix_file(self, filepath: str, error_type: str, line_num: int = None) -> bool:
        """Fix a specific syntax error in a file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            original_content = content
            
            if error_type == 'continue_outside_loop':
                # Fix continue outside loop
                pattern = r'(\s*)if\s+not\s*\(([^)]+)\):\s*\n\s*continue\s*(?:#.*)?(?:\n\s*#.*)?\n\s*(?:if\s+[^:]+:)?'
                
                def replace_continue(match):
                    indent = match.group(1)
                    condition = match.group(2)
                    # Simply remove the problematic lines
                    remaining = match.group(0).split('\n')[-1] if 'if' in match.group(0).split('\n')[-1] else ''
                    if remaining and not remaining.strip().startswith('if'):
                        remaining = ''
                    return f"{indent}if {condition}:\n{remaining}" if remaining else f"{indent}if {condition}:"
                
                content = re.sub(pattern, replace_continue, content)
                
            elif error_type == 'expected_colon':
                # Fix missing colon in method definitions
                pattern = r'def\s+__init__\s*\(self\)([^:\n]+)\n(\s*)"""'
                content = re.sub(pattern, r'def __init__(self):\n\2"""', content)
                
            elif error_type == 'unterminated_fstring':
                # Fix unterminated f-strings
                pattern = r'f"([^"]*?)\n\s*f"([^"]*?)"'
                content = re.sub(pattern, r'f"\1 \2"', content)
                
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.fixed_count += 1
                return True
                
        except Exception as e:
            print(f"Error fixing {filepath}: {e}")
            
        return False
    
    def run(self, target_dir: str = '.', max_fixes: int = None):
        """Run the syntax error fixer"""
        print("🔍 Finding syntax errors...")
        errors = self.find_syntax_errors(target_dir)
        
        print(f"\n📊 Found {len(errors)} files with syntax errors")
        
        if not errors:
            print("✅ No syntax errors found!")
            return
            
        # Group errors by type
        error_types = {}
        for filepath, error_msg in errors:
            analysis = self.analyze_error(filepath, error_msg)
            error_type = analysis['type'] or 'unknown'
            
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append((filepath, error_msg, analysis))
            
        # Display error summary
        print("\n📋 Error types found:")
        for error_type, files in error_types.items():
            print(f"  - {error_type}: {len(files)} files")
            
        # Fix errors

        fixed_files = []
        
        for error_type, files in error_types.items():
            if error_type == 'unknown':
                continue
                
            for filepath, error_msg, analysis in files:
                if max_fixes and len(fixed_files) >= max_fixes:
                    break
                    
                if self.fix_file(filepath, error_type, analysis.get('line')):
                    fixed_files.append(filepath)
                    print(f"  ✅ Fixed {error_type} in {filepath}")
                    
        print(f"\n✨ Fixed {len(fixed_files)} files")
        
        # Verify fixes
        print("\n🔍 Verifying fixes...")
        remaining_errors = self.find_syntax_errors(target_dir)
        
        print(f"\n📊 Results:")
        print(f"  - Initial errors: {len(errors)}")
        print(f"  - Files fixed: {len(fixed_files)}")
        print(f"  - Remaining errors: {len(remaining_errors)}")
        print(f"  - Success rate: {(len(fixed_files)/len(errors)*100):.1f}%")

def main():
    fixer = SyntaxErrorFixer()
    
    # Run with limited fixes first
    fixer.run(target_dir='./libs', max_fixes=50)
    
if __name__ == '__main__':
    main()