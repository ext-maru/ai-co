#!/usr/bin/env python3
"""
Fix IndentationError issues in Python files
"""
import os
import re
from pathlib import Path

class IndentationFixer:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.fixed_count = 0
        self.error_patterns = [
            # Pattern for empty try blocks
            (r'(\s*)try:\s*\n(?=\s*except)', r'\1try:\n\1    pass\n'),
            # Pattern for empty with blocks
            (r'(\s*)with\s+[^:]+:\s*\n(?=\s*(?:except|finally|else|\S))', r'\g<0>\1    pass\n'),
            # Pattern for empty if blocks
            (r'(\s*)if\s+[^:]+:\s*\n(?=\s*(?:elif|else|\S))', r'\g<0>\1    pass\n'),
            # Pattern for empty for blocks
            (r'(\s*)for\s+[^:]+:\s*\n(?=\s*\S)', r'\g<0>\1    pass\n'),
            # Pattern for empty while blocks
            (r'(\s*)while\s+[^:]+:\s*\n(?=\s*\S)', r'\g<0>\1    pass\n'),
            # Pattern for empty except blocks
            (r'(\s*)except[^:]*:\s*\n(?=\s*(?:except|finally|else|\S))', r'\g<0>\1    pass\n'),
            # Pattern for empty finally blocks
            (r'(\s*)finally:\s*\n(?=\s*\S)', r'\g<0>\1    pass\n'),
            # Pattern for empty else blocks
            (r'(\s*)else:\s*\n(?=\s*\S)', r'\g<0>\1    pass\n'),
            # Pattern for empty class definitions
            (r'(\s*)class\s+[^:]+:\s*\n(?=\s*(?:class|def|\S))', r'\g<0>\1    pass\n'),
            # Pattern for empty function definitions
            (r'(\s*)def\s+[^:]+:\s*\n(?=\s*(?:def|class|\S))', r'\g<0>\1    """TODO: Implement"""\n\1    pass\n'),
        ]
    
    def fix_file(self, filepath):
        """Fix indentation errors in a single file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Apply each pattern
            for pattern, replacement in self.error_patterns:
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            
            # Fix specific indentation issues
            lines = content.split('\n')
            fixed_lines = []
            i = 0
            
            while i < len(lines):
                line = lines[i]
                stripped = line.strip()
                
                # Check for control structures that need bodies
                if any(stripped.startswith(kw + ' ') or stripped == kw + ':' 
                       for kw in ['try:', 'except', 'finally:', 'else:', 'elif']):
                    fixed_lines.append(line)
                    # Check if next line is properly indented
                    if i + 1 < len(lines):
                        next_line = lines[i + 1]
                        if next_line.strip() and not next_line.startswith(line[:len(line)-len(line.lstrip())] + '    '):
                            # Add pass statement
                            indent = line[:len(line)-len(line.lstrip())]
                            fixed_lines.append(indent + '    pass')
                    else:
                        # End of file, add pass
                        indent = line[:len(line)-len(line.lstrip())]
                        fixed_lines.append(indent + '    pass')
                else:
                    fixed_lines.append(line)
                i += 1
            
            content = '\n'.join(fixed_lines)
            
            # Write back if changed
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.fixed_count += 1
                return True
            return False
            
        except Exception as e:
            print(f"Error fixing {filepath}: {e}")
            return False
    
    def find_and_fix_errors(self):
        """Find and fix all indentation errors"""
        print("Searching for Python files with indentation errors...")
        
        # List of files known to have indentation errors from the test output
        problem_files = [
            "test_real_claude_chat.py",
            "scripts/rag_wizards.py",
            "tests/integration/test_rag_worker_integration.py",
            "tests/unit/test_async_worker_optimization_knights.py",
            "tests/unit/test_dlq_mixin_simple.py",
            "tests/unit/test_dlq_processor_simple.py",
            "tests/unit/test_dwarf_workshop.py",
            "tests/unit/test_base_worker_simple.py",
            "tests/unit/test_base_worker_dwarf.py",
            "tests/unit/test_task_worker_simple.py",
            "tests/unit/test_simple_task_worker_wizard.py",
            "tests/unit/test_pm_worker_wizard.py",
            "tests/unit/test_pm_worker_simple.py",
            "tests/unit/test_dialog_orchestrator_simple.py",
            "tests/unit/test_dialog_orchestrator_knights.py",
            "tests/unit/test_enhanced_pm_worker_simple.py",
            "tests/unit/test_rag_integrated_workers.py",
            "tests/unit/test_security_module_dwarf.py",
            "tests/unit/test_migration_engine.py",
            "tests/unit/test_rate_limiter_simple.py",
            "tests/unit/test_slack_monitor_worker_simple.py",
            "tests/unit/test_slack_monitor_worker_wizard.py",
            "tests/unit/test_rate_limiter_dwarf.py",
            "output/test_quick.py",
            "output/test_slack_notification_test.py",
        ]
        
        # Also scan for all Python files with potential issues
        for root, dirs, files in os.walk(self.project_root):
            # Skip venv and other non-project directories
            if any(skip in root for skip in ['venv', '__pycache__', '.git', 'node_modules']):
                continue
            
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, self.project_root)
                    
                    # Check if it's in our problem list or scan all
                    if any(prob in rel_path for prob in problem_files):
                        if self.fix_file(filepath):
                            print(f"Fixed: {rel_path}")
        
        print(f"\nFixed {self.fixed_count} files with indentation errors")

if __name__ == "__main__":
    fixer = IndentationFixer()
    fixer.find_and_fix_errors()