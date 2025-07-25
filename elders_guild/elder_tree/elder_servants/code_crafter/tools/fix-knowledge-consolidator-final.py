#!/usr/bin/env python3
"""Final fix for knowledge_consolidator.py syntax errors"""

import re

file_path = "libs/knowledge_consolidator.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the indentation issues in function definitions
# Pattern: def method():\n    """docstring"""\n        code
# Should be: def method():\n        """docstring"""\n        code

fixes = [
    # consolidate_knowledge_base
    ('def consolidate_knowledge_base(self) -> Dict[str, Any]:\n    """ナレッジベースの統合"""',
     'def consolidate_knowledge_base(self) -> Dict[str, Any]:\n        """ナレッジベースの統合"""'),
    
    # analyze_implementations with extra colon
    ('def analyze_implementations(self) -> Dict[str, Any]:\n    """実装の分析"""\n        self.logger.info(f"{EMOJI[\'gear\']} Analyzing implementations...")\n:',
     'def analyze_implementations(self) -> Dict[str, Any]:\n        """実装の分析"""\n        self.logger.info(f"{EMOJI[\'gear\']} Analyzing implementations...")'),
    
    # generate_system_map
    ('def generate_system_map(self) -> Dict[str, Any]:\n    """システム全体のマップ生成"""',
     'def generate_system_map(self) -> Dict[str, Any]:\n        """システム全体のマップ生成"""'),
    
    # generate_documentation
    ('def generate_documentation(self) -> Path:\n    """統合ドキュメントの生成"""',
     'def generate_documentation(self) -> Path:\n        """統合ドキュメントの生成"""'),
    
    # create_interactive_report
    ('def create_interactive_report(self) -> Path:\n    """インタラクティブなHTMLレポート生成"""',
     'def create_interactive_report(self) -> Path:\n        """インタラクティブなHTMLレポート生成"""'),
]

for old, new in fixes:
    content = content.replace(old, new)

# Remove duplicate logger.info calls
content = content.replace(
    'self.logger.info(f"{EMOJI[\'info\']} Scanning project structure...")\n        self.logger.info(f"{EMOJI[\'info\']} Scanning project structure...")',
    'self.logger.info(f"{EMOJI[\'info\']} Scanning project structure...")'
)

# Remove extra colons after docstrings for simple return methods
content = re.sub(r'("""[^"]*"""):\n(\s+return)', r'\1\n\2', content)

# Write the fixed content
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed knowledge_consolidator.py (final)")