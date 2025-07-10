#!/usr/bin/env python3
#\!/usr/bin/env python3
import os
import re
from pathlib import Path

# Create mock dependencies first
mock_libs = {
    'redis': 'class Redis:\n    def __init__(self, *args, **kwargs): pass\n    def get(self, key): return None\n    def set(self, key, value): return True\n    def pipeline(self): return self\n    def execute(self): return []\n',
    'aioredis': 'class Redis:\n    def __init__(self, *args, **kwargs): pass\n    async def get(self, key): return None\n    async def set(self, key, value): return True\nasync def create_redis(*args, **kwargs): return Redis()\nfrom_url = create_redis\n',
    'prometheus_client': 'class Counter:\n    def __init__(self, *args, **kwargs): pass\n    def inc(self, amount=1): pass\n    def labels(self, **kwargs): return self\nclass Histogram:\n    def __init__(self, *args, **kwargs): pass\n    def observe(self, value): pass\n    def labels(self, **kwargs): return self\nclass Gauge:\n    def __init__(self, *args, **kwargs): pass\n    def set(self, value): pass\n    def labels(self, **kwargs): return self\n'
}

# Create mocks
for name, content in mock_libs.items():
    Path(f'libs/{name}.py').write_text(content)
    print(f"Created mock for {name}")

# Fix syntax errors in all test files
test_files = list(Path('tests').rglob('*.py'))
fixed = 0

for filepath in test_files:
    try:
        content = filepath.read_text()
        original = content
        
        # Fix common syntax errors
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Add missing colons
            if re.match(r'^\s*(if < /dev/null | elif|else|for|while|def|class|try|except|finally|with)\s+.*[^:]$', line):
                line = line + ':'
            # Fix empty except
            elif re.match(r'^\s*except\s*:?\s*$', line):
                line = re.sub(r'except\s*:?\s*$', 'except Exception:', line)
            # Add pass to empty blocks
            elif line.strip().endswith(':') and i+1 < len(lines):
                next_line = lines[i+1] if i+1 < len(lines) else ''
                if not next_line.strip() or (next_line.strip() and not next_line[0].isspace()):
                    fixed_lines.append(line)
                    fixed_lines.append('    pass')
                    continue
            
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        if content != original:
            filepath.write_text(content)
            fixed += 1
            
    except Exception as e:
        print(f"Error in {filepath}: {e}")

print(f"Fixed {fixed} files")
