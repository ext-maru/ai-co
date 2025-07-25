#!/usr/bin/env python3
"""Fix all syntax errors in elder_scheduled_tasks.py"""

import re

file_path = "libs/elder_scheduled_tasks.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix pattern: def func()code: -> def func():\n    code
content = re.sub(
    r'def (\w+)\(\)([^:\n]+):',
    r'def \1():\n            \2',
    content
)

# Fix pattern: def func()code (no colon) -> def func():\n    code
content = re.sub(
    r'def (\w+)\(\)([a-z][^:\n]+)$',
    r'def \1():\n            \2',
    content,
    flags=re.MULTILINE
)

# Fix misplaced docstrings after function name without colon
# Pattern: def func()\n    """docstring""" -> def func():\n        """docstring"""
content = re.sub(
    r'def (\w+)\(\)\n(\s*"""[^"]*""")',
    r'def \1():\n\2',
    content
)

# Write the fixed content
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed elder_scheduled_tasks.py")