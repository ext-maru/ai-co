#!/usr/bin/env python3
"""Fix all syntax errors in knowledge_consolidator.py"""

import re

file_path = "libs/knowledge_consolidator.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix malformed function definitions with return type and code on wrong line
# Pattern: def method(self) -> Type...code:
# Should be: def method(self) -> Type:
#               """docstring"""
#               code
fixes = [
    # scan_project_structure
    (r'def scan_project_structure\(self\) -> Dict\[str, Any\]self\.logger\.info\(f"{EMOJI\[\'info\'\]} Scanning project structure..."\):',
     'def scan_project_structure(self) -> Dict[str, Any]:'),
    
    # consolidate_knowledge_base

     'def consolidate_knowledge_base(self) -> Dict[str, Any]:'),
    
    # analyze_implementations
    (r'def analyze_implementations\(self\) -> Dict\[str, Any\]self\.logger\.info\(f"{EMOJI\[\'gear\'\]} Analyzing implementations..."\):',
     'def analyze_implementations(self) -> Dict[str, Any]:'),
    
    # generate_system_map
    (r'def generate_system_map\(self\) -> Dict\[str, Any\]self\.logger\.info\(f"{EMOJI\[\'network\'\]} Generating system map..."\):',
     'def generate_system_map(self) -> Dict[str, Any]:'),
    
    # generate_documentation
    (r'def generate_documentation\(self\) -> Pathself\.logger\.info\(f"{EMOJI\[\'file\'\]} Generating consolidated documentation..."\):',
     'def generate_documentation(self) -> Path:'),
    
    # create_interactive_report
    (r'def create_interactive_report\(self\) -> Pathself\.logger\.info\(f"{EMOJI\[\'monitor\'\]} Creating interactive report..."\):',
     'def create_interactive_report(self) -> Path:'),
]

for old, new in fixes:
    content = re.sub(old, new, content)

# Fix docstrings placed after return type
# Pattern: -> Type:\n    """docstring"""
# Should be: -> Type:\n        """docstring"""
content = re.sub(r'(-> [^:]+):\n(\s*"""[^"]*""""):', r'\1:\n\2', content)

# Add proper indentation after docstrings for the logger.info calls
missing_logger_calls = [
    ('"""プロジェクト構造のスキャン"""', '        self.logger.info(f"{EMOJI[\'info\']} Scanning project structure...")'),

    ('"""実装の分析"""', '        self.logger.info(f"{EMOJI[\'gear\']} Analyzing implementations...")'),
    ('"""システム全体のマップ生成"""', '        self.logger.info(f"{EMOJI[\'network\']} Generating system map...")'),
    ('"""統合ドキュメントの生成"""', '        self.logger.info(f"{EMOJI[\'file\']} Generating consolidated documentation...")'),
    ('"""インタラクティブなHTMLレポート生成"""', '        self.logger.info(f"{EMOJI[\'monitor\']} Creating interactive report...")'),
]

for docstring, logger_call in missing_logger_calls:
    # Find the docstring and add logger call after it
    pattern = f'({docstring})\n'
    replacement = f'\\1\n{logger_call}\n'
    content = re.sub(pattern, replacement, content)

# Remove the extra colons after docstrings in simple methods
content = re.sub(r'("""[^"]*""""):(\n\s+(?:return|if|try|for|with))', r'\1\2', content)

# Fix the analyze_implementations extra colon
content = re.sub(r'("""実装の分析""")\n:', r'\1', content)

# Write the fixed content
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed knowledge_consolidator.py (v2)")