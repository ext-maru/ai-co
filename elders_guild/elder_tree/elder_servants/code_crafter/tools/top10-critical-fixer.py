#!/usr/bin/env python3
"""
Top 10 Critical Fixer - 最も重要な10ファイルを集中修正
"""

import ast
import re
from pathlib import Path

def fix_critical_file(file_path):
    """重要ファイルの構文エラーを修正"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # elders_guild_integration_script.py
        if file_path.name == "elders_guild_integration_script.py":
            # Line 56 likely has invalid syntax
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if i == 55:  # Line 56 (0-indexed)
                    # Common patterns
                    if not line.strip().endswith(':') and ('def ' in line or 'class ' in line or 'if ' in line):
                        lines[i] = line.rstrip() + ':'
                    elif 'f"f"' in line:
                        lines[i] = line.replace('f"f"', 'f"')
            content = '\n'.join(lines)
        
        # commands/ai_shell.py 
        elif file_path.name == "ai_shell.py":
            # Fix Line 31: expected ':'
            content = re.sub(
                r'def __init__\(self\)super\(\).__init__\(',
                r'def __init__(self):\n        super().__init__(',
                content
            )
            # Fix other similar patterns
            content = re.sub(
                r'def (\w+)\(([^)]*)\)([^:\n]*?)\n(\s*)"""([^"]+)"""',
                r'def \1(\2)\3:\n\4"""\5"""',
                content
            )
        
        # commands/ai_dlq.py
        elif file_path.name == "ai_dlq.py":
            # Fix unterminated triple-quoted string literal
            content = re.sub(
                r'"""([^"]*?)$',
                r'"""\1"""',
                content,
                flags=re.MULTILINE
            )
            # Fix missing closing triple quotes
            if content.count('"""') % 2 != 0:
                content += '\n"""'
        
        # commands/ai_worker_comm.py
        elif file_path.name == "ai_worker_comm.py":
            # Similar fixes as ai_shell.py
            content = re.sub(
                r'def (\w+)\(([^)]*)\)([^:\n]*?)\n(\s*)"""([^"]+)"""',
                r'def \1(\2)\3:\n\4"""\5"""',
                content
            )
        
        # libs/auto_issue_processor_error_handling.py
        elif file_path.name == "auto_issue_processor_error_handling.py":
            # Complex file - focus on common patterns
            content = re.sub(
                r'def (\w+)\(([^)]*)\)(\s*->\s*[^:\n]+)?\s*\n(\s*)"""',
                r'def \1(\2)\3:\n\4"""',
                content
            )
        
        # libs/elder_scheduled_tasks.py
        elif file_path.name == "elder_scheduled_tasks.py":
            # Fix method definitions
            content = re.sub(
                r'def (\w+)\(([^)]*)\)(\s*->\s*[^:\n]+)?\s*\n(\s*)"""',
                r'def \1(\2)\3:\n\4"""',
                content
            )
        
        # libs/advanced_search_analytics_platform.py
        elif file_path.name == "advanced_search_analytics_platform.py":
            # Fix method definitions  
            content = re.sub(
                r'def (\w+)\(([^)]*)\)(\s*->\s*[^:\n]+)?\s*\n(\s*)"""',
                r'def \1(\2)\3:\n\4"""',
                content
            )
        
        # General fixes for all files
        
        # Fix function definitions without colons
        content = re.sub(
            r'^(\s*def\s+\w+\s*\([^)]*\)(?:\s*->\s*[^:\n]+)?)\s*$',
            r'\1:',
            content,
            flags=re.MULTILINE
        )
        
        # Fix class definitions without colons
        content = re.sub(
            r'^(\s*class\s+\w+(?:\([^)]*\))?)\s*$',
            r'\1:',
            content,
            flags=re.MULTILINE
        )
        
        # Fix malformed f-strings
        content = re.sub(r'f"f"', 'f"', content)
        
        if content != original_content:
            try:
                # Validate fix
                ast.parse(content)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            except SyntaxError:
                return False
        
        return False
        
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    """メイン処理"""
    project_root = Path(__file__).parent.parent.parent
    
    # Top 10 critical files
    critical_files = [
        "elders_guild_integration_script.py",
        "commands/ai_shell.py",
        "commands/ai_dlq.py", 
        "commands/ai_worker_comm.py",
        "libs/auto_issue_processor_error_handling.py",
        "libs/elder_scheduled_tasks.py",
        "libs/advanced_search_analytics_platform.py",
        "scripts/quality/fix-knowledge-consolidator-fstrings.py",
        "libs/knowledge_consolidator.py",
        "libs/celery_migration_poc.py"
    ]
    
    fixed_count = 0
    
    for file_name in critical_files:
        file_path = project_root / file_name
        if file_path.exists():
            if fix_critical_file(file_path):
                fixed_count += 1
                print(f"🔧 Fixed {file_name}")
            else:
                print(f"⚠️  Could not fix {file_name}")
        else:
            print(f"❌ File not found: {file_name}")
    
    print(f"\n✅ Top 10 Critical Fixer 完了!")
    print(f"   修正ファイル数: {fixed_count}")

if __name__ == "__main__":
    main()