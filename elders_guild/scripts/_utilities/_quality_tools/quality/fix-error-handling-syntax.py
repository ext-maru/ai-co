#!/usr/bin/env python3
"""Fix all syntax errors in auto_issue_processor_error_handling.py"""

import re

file_path = "libs/auto_issue_processor_error_handling.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Fix pattern: async def can_handle(self, contextErrorContext) -> bool:
    if 'async def can_handle(self, contextErrorContext) -> bool:' in line:
        fixed_lines.append(line.replace('contextErrorContext', 'context: ErrorContext'))
        i += 1
        continue
    
    # Fix pattern: async def recover(self, contextErrorContext) -> RecoveryResult...
    if 'async def recover(self, contextErrorContext) -> RecoveryResult' in line:
        # Extract any code that follows on the same line
        match = re.match(r'(\s*)async def recover\(self, contextErrorContext\) -> RecoveryResult(.+)', line)
        if match:
            indent = match.group(1)
            extra_code = match.group(2).strip()
            fixed_lines.append(f'{indent}async def recover(self, context: ErrorContext) -> RecoveryResult:\n')
            # Check if next line is a misplaced docstring
            if i + 1 < len(lines) and '"""' in lines[i + 1] and lines[i + 1].strip().startswith('"""'):
                i += 1
                fixed_lines.append(f'{indent}    {lines[i].strip()}\n')
            # Add the extra code as a new line
            if extra_code:
                fixed_lines.append(f'{indent}    {extra_code}\n')
        else:
            fixed_lines.append(line.replace('contextErrorContext', 'context: ErrorContext'))
        i += 1
        continue
    
    # Fix pattern: def method(args) -> Typecode_on_same_line
    match = re.match(r'(\s*)(async\s+)?def\s+(\w+)\(([^)]*)\)\s*->\s*([A-Za-z\[\], ]+)(.+)', line)
    if match and not line.strip().endswith(':'):
        indent = match.group(1)
        async_kw = match.group(2) or ''
        method_name = match.group(3)
        args = match.group(4)
        return_type = match.group(5)
        extra_code = match.group(6).strip()
        
        # Reconstruct the method definition
        fixed_lines.append(f'{indent}{async_kw}def {method_name}({args}) -> {return_type}:\n')
        
        # Check if next line is a misplaced docstring
        if i + 1 < len(lines) and '"""' in lines[i + 1] and lines[i + 1].strip().startswith('"""'):
            i += 1
            fixed_lines.append(f'{indent}    {lines[i].strip()}\n')
        
        # Add the extra code as a new line
        if extra_code and extra_code != ':':
            fixed_lines.append(f'{indent}    {extra_code}\n')
        
        i += 1
        continue
    
    # Default: keep the line as is
    fixed_lines.append(line)
    i += 1

# Write the fixed content
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print("Fixed auto_issue_processor_error_handling.py")