#!/usr/bin/env python3
"""
Script to consolidate duplicate Python files into libs/ directory
"""

import os
import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple

def get_file_hash(filepath: Path) -> str:
    """Calculate MD5 hash of a file"""
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def find_duplicates(directories: List[str]) -> Dict[str, List[Path]]:
    """Find duplicate Python files across directories"""
    file_map = {}
    
    for directory in directories:
        for py_file in Path(directory).rglob("*.py"):
            if py_file.is_file():
                filename = py_file.name
                if filename not in file_map:
                    file_map[filename] = []
                file_map[filename].append(py_file)
    
    # Filter to only show duplicates
    duplicates = {k: v for k, v in file_map.items() if len(v) > 1}
    return duplicates

def analyze_duplicates(duplicates: Dict[str, List[Path]]) -> List[Tuple[str, List[Path], Dict[str, int]]]:
    """Analyze duplicate files by content and size"""
    results = []
    
    for filename, paths in duplicates.items():
        size_info = {}
        hash_info = {}
        
        for path in paths:
            try:
                size = path.stat().st_size
                file_hash = get_file_hash(path)
                
                size_info[str(path)] = size
                if file_hash not in hash_info:
                    hash_info[file_hash] = []
                hash_info[file_hash].append(path)
            except Exception as e:
                print(f"Error processing {path}: {e}")
        
        results.append((filename, paths, size_info))
    
    return results

def main():
    """Main consolidation logic"""
    directories = ["libs", "shared_libs", "elder_tree"]
    
    print("Finding duplicate Python files...")
    duplicates = find_duplicates(directories)
    
    print(f"\nFound {len(duplicates)} files with duplicates")
    
    # Files to consolidate (based on analysis)
    consolidation_plan = {
        "base_worker.py": "libs/base_worker.py",
        "config_loader.py": "libs/config_loader.py",
        "env_config.py": "libs/env_config.py",
        "authentication.py": "libs/authentication.py",
        "grimoire_database.py": "libs/grimoire_database.py",
        "string_utils.py": "libs/string_utils.py",
        "unified_config_manager.py": "libs/unified_config_manager.py",
        "base_manager.py": "libs/base_manager.py",
        "common_fixes.py": "libs/auto_fix/common_fixes.py",
    }
    
    print("\nFiles to be consolidated:")
    for filename, target in consolidation_plan.items():
        if filename in duplicates:
            print(f"\n{filename}:")
            for path in duplicates[filename]:
                size = path.stat().st_size
                print(f"  - {path} ({size} bytes)")
            print(f"  → Keep: {target}")
    
    # Generate removal list
    print("\n\nFiles to be removed:")
    removal_count = 0
    for filename, target in consolidation_plan.items():
        if filename in duplicates:
            for path in duplicates[filename]:
                if str(path) != target and path.exists():
                    print(f"  rm {path}")
                    removal_count += 1
    
    print(f"\nTotal files to be removed: {removal_count}")
    
    # Check for files importing from core module
    print("\n\nFiles importing from 'core' module (need update):")
    for directory in directories:
        for py_file in Path(directory).rglob("*.py"):
            if py_file.is_file():
                try:
                    content = py_file.read_text()
                    if "from core." in content or "import core." in content:
                        print(f"  - {py_file}")
                except Exception:
                    pass

if __name__ == "__main__":
    main()