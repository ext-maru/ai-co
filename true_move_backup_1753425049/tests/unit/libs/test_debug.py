#!/usr/bin/env python3
"""デバッグ用スクリプト"""

content = '''
def create_template()def test_{test_name}():
test_template = f"""
    pass
"""
    return test_template
'''

lines = content.split("\n")
for i, line in enumerate(lines):
    stripped = line.strip()
    print(f"Line {i}: '{line}' -> stripped: '{stripped}'")
    print(f"  endswith('\"\"\"'): {stripped.endswith('"""')}")
    print(f"  count('\"\"\"'): {line.count('"""')}")
    print(f"  '=' in line: {'}")
    print(f"  starts with f/r/b: {any(stripped.startswith(prefix + \
        '"""') for prefix in ['f', 'r', 'b', 'fr', 'rf', 'br', 'rb'])}")
    print()