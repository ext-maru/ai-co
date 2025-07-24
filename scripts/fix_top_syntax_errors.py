#!/usr/bin/env python3
"""Fix top syntax errors in the project"""

import os
import re
import sys

def fix_file(filepath):
    """Fix common syntax errors in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original = content
        
        # Fix 1: continue outside loop
        content = re.sub(
            r'(\s+)if\s+not\s*\([^)]+\):\s*\n\s+continue\s*#.*\n',
            r'\1# Removed invalid continue statement\n',
            content
        )
        
        # Fix 2: Malformed method definitions
        content = re.sub(
            r'def\s+(\w+)\s*\(self\)def\s+',
            r'def \1(self):\n        """Method"""\n        pass\n\n    def ',
            content
        )
        
        # Fix 3: Unterminated f-strings
        content = re.sub(
            r'print\(f"([^"]+)}\)"?\s*\)',
            r'print(f"\1}")',
            content
        )
        
        # Fix 4: Invalid decimal literals (like error1.0lower())
        content = re.sub(
            r'(\w+)\.0(\w+)',
            r'\1.\2',
            content
        )
        
        # Fix 5: JSON dumps with missing argument
        content = re.sub(
            r'json\.dumps\(([^,]+),\s*indent\s*}\)"',
            r'json.dumps(\1, indent=2)"',
            content
        )
        
        # Fix 6: Indentation after if statement
        lines = content.split('\n')
        fixed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check for if statement without proper indentation on next line
            if re.match(r'^(\s*)if\s+[^:]+:\s*$', line) and i + 1 < len(lines):
                next_line = lines[i + 1]
                if next_line.strip() and not re.match(r'^\s+', next_line):
                    # Add proper indentation
                    indent = re.match(r'^(\s*)', line).group(1)
                    lines[i + 1] = indent + '    ' + next_line.lstrip()
                    
            fixed_lines.append(line)
            i += 1
            
        content = '\n'.join(fixed_lines)
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
            
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        
    return False

def main():
    # Priority files to fix
    files_to_fix = [
        'libs/system_health_dashboard.py',
        'libs/task_validation_engine.py',
        'libs/auto_issue_processor_error_handling.py',
        'libs/celery_migration_poc.py',
        'libs/elder_flow_ultimate_evolution.py',
        'libs/slack_api_integration.py',
        'libs/elder_scheduled_tasks.py',
        'libs/auto_fix_executor.py',
        'libs/error_classification_system.py',
        'libs/elders_guild_data_mapper.py'
    ]
    
    fixed = 0
    for filepath in files_to_fix:
        if os.path.exists(filepath):
            print(f"Processing: {filepath}")
            if fix_file(filepath):
                print(f"  ✅ Fixed")
                fixed += 1
            else:
                print(f"  ❌ No changes")
                
    print(f"\n📊 Fixed {fixed} files")

if __name__ == '__main__':
    main()