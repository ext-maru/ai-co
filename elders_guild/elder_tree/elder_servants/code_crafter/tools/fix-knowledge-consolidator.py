#!/usr/bin/env python3
"""Fix syntax errors in knowledge_consolidator.py"""

import re

file_path = "libs/knowledge_consolidator.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix pattern 1: Function definitions with return type on wrong line
# Pattern: def method_name(self):\n    """docstring"""\n        -> return_type...
pattern1 = re.compile(
    r'(def\s+\w+\([^)]*\)):\n(\s*"""[^"]*""")\n\s*->\s*([^:\n]+)',
    re.MULTILINE
)
content = pattern1.sub(r'\1 -> \3:\n\2', content)

# Fix pattern 2: Function definitions with code after return type
# Pattern: def method_name(self):\n    """docstring"""\n        -> return_typeself.logger...
pattern2 = re.compile(
    r'(def\s+\w+\([^)]*\)):\n(\s*"""[^"]*""")\n\s*->\s*([A-Za-z\[\], ]+)(.+)',
    re.MULTILINE
)
content = pattern2.sub(r'\1 -> \3:\n\2\n        \4', content)

# Fix pattern 3: structure = {: to structure = {
content = re.sub(r'structure = \{:', 'structure = {', content)
content = re.sub(r'system_map = \{:', 'system_map = {', content)
content = re.sub(r'data = \{:', 'data = {', content)

# Fix pattern 4: export_to_json definition
content = re.sub(
    r'def export_to_json\(self\):\n\s*"""JSON形式でのエクスポート"""\n\s*timestamp = datetime',
    'def export_to_json(self):\n        """JSON形式でのエクスポート"""\n        timestamp = datetime',
    content
)

# Write the fixed content
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed knowledge_consolidator.py")