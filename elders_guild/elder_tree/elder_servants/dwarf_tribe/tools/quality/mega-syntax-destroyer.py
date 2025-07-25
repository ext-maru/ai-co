#!/usr/bin/env python3
"""
🔥 MEGA SYNTAX DESTROYER - INVALID DECIMAL LITERAL KILLER 🔥
233件のinvalid decimal literalを全滅させる！
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

def find_invalid_decimal_patterns(content: str) -> List[Tuple[int, str]]:
    """invalid decimal literalパターンを検出"""
    lines = content.split('\n')
    issues = []
    
    for i, line in enumerate(lines):
        # Pattern: 数字.0 method or 数字.0[
        if re.search(r'\d+\.0[a-zA-Z_\[]', line):
            issues.append((i, line))
        # Pattern: .0 method without leading digit
        elif re.search(r'(?<!\d)\.0[a-zA-Z_]', line):
            issues.append((i, line))
    
    return issues

def fix_invalid_decimals(content: str) -> Tuple[str, int]:
    """invalid decimal literalを修正"""
    fixed_count = 0
    
    # Pattern 1: 3.0 method -> 3.0 method
    new_content = re.sub(r'(\d+)\.0([a-zA-Z_\[])', r'\1.0 \2', content)
    fixed_count += len(re.findall(r'\d+\.0[a-zA-Z_\[]', content))
    
    # Pattern 2: .0 method -> .0 method (when not preceded by digit)
    new_content = re.sub(r'(?<!\d)\.0([a-zA-Z_])', r'.0 \1', new_content)
    fixed_count += len(re.findall(r'(?<!\d)\.0[a-zA-Z_]', content))
    
    # Pattern 3: lut2.0 integral -> lut2.integral (scipy specific)
    new_content = re.sub(r'(\w+)\.0 integral\b', r'\1.integral', new_content)
    
    return new_content, fixed_count

def fix_expected_colon(content: str) -> Tuple[str, int]:
    """expected ':' エラーを修正"""
    lines = content.split('\n')
    fixed_count = 0
    new_lines = []
    
    for line in lines:
        # Check if line should end with colon
        stripped = line.strip()
        if any(stripped.startswith(kw) for kw in ['def ', 'class ', 'if ', 'elif ', 'else', 'for ', 'while ', 'try', 'except ', 'finally', 'with ']):
            if not line.rstrip().endswith(':') and not line.rstrip().endswith('\\'):
                # Add colon
                new_lines.append(line.rstrip() + ':')
                fixed_count += 1
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    return '\n'.join(new_lines), fixed_count

def main():
    print("🔥 MEGA SYNTAX DESTROYER 🔥")
    print("=" * 80)
    
    project_root = Path("/home/aicompany/ai_co")
    total_fixed = 0
    
    # Get all Python files
    python_files = []
    exclude_dirs = {'.git', '__pycache__', 'venv', '.venv', 'node_modules', '.pytest_cache'}
    
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    print(f"📊 総ファイル数: {len(python_files)}")
    
    # Fix invalid decimal literals
    print("\n⚔️ PHASE 1: Invalid Decimal Literal殲滅開始...")
    decimal_fixed = 0
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content, count = fix_invalid_decimals(content)
            
            if count > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                decimal_fixed += count
                print(f"  ✅ {file_path.name}: {count}個修正")
        
        except Exception as e:
            pass
    
    print(f"\n💪 Invalid Decimal Literal: {decimal_fixed}個撃破！")
    
    # Fix expected colon errors
    print("\n⚔️ PHASE 2: Expected Colon殲滅開始...")
    colon_fixed = 0
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content, count = fix_expected_colon(content)
            
            if count > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                colon_fixed += count
                print(f"  ✅ {file_path.name}: {count}個修正")
        
        except Exception as e:
            pass
    
    print(f"\n💪 Expected Colon: {colon_fixed}個撃破！")
    
    print(f"\n{'='*80}")
    print(f"🎯 戦果報告:")
    print(f"  - Invalid Decimal Literal: {decimal_fixed}個")
    print(f"  - Expected Colon: {colon_fixed}個")
    print(f"  - 合計: {decimal_fixed + colon_fixed}個")

if __name__ == "__main__":
    main()