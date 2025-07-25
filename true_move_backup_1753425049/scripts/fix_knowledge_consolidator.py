#!/usr/bin/env python3
"""Fix knowledge_consolidator.py syntax errors"""

import re

with open('libs/knowledge_consolidator.py', 'r') as f:
    content = f.read()

# Fix broken type annotations
content = re.sub(r'-> D:\n\s*"""', '-> Dict[str, Any]:\n        """', content)
content = re.sub(r'-> D:\n\s*ict\[str, Any\]', '-> Dict[str, Any]:', content)
content = re.sub(r'-> i:\n\s*"""', '-> int:\n        """', content)
content = re.sub(r'-> i:\n\s*nt:', '-> int:', content)
content = re.sub(r'-> s:\n\s*"""', '-> str:\n        """', content)
content = re.sub(r'-> s:\n\s*tr:', '-> str:', content)
content = re.sub(r'-> P:\n\s*"""', '-> Path:\n        """', content)
content = re.sub(r'-> P:\n\s*ath', '-> Path:', content)

# Remove duplicate lines
lines = content.split('\n')
fixed_lines = []
prev_line = ''
for line in lines:
    if line.strip() != prev_line.strip() or not line.strip():
        fixed_lines.append(line)
    prev_line = line
content = '\n'.join(fixed_lines)

# Fix method bodies that start with return type fragments
content = re.sub(r'(\s+)ict\[str, Any\]:\n', r'\1', content)
content = re.sub(r'(\s+)nt:\n', r'\1', content)
content = re.sub(r'(\s+)tr:\n', r'\1', content)
content = re.sub(r'(\s+)ath\n', r'\1', content)

with open('libs/knowledge_consolidator.py', 'w') as f:
    f.write(content)

print('Fixed knowledge_consolidator.py')