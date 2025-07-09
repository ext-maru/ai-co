#!/usr/bin/env python3
"""
Analyze Test Coverage Gaps
===========================

Phase 4 Test Coverage Improvement - Coverage Gap Analysis
"""

import os
from pathlib import Path


def get_libs_modules():
    """Get all libs modules"""
    libs_modules = []
    for root, dirs, files in os.walk('libs'):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                module_name = file[:-3]  # Remove .py extension
                libs_modules.append(module_name)
    return set(libs_modules)


def get_existing_libs_tests():
    """Get existing test files for libs"""
    test_files = []
    for root, dirs, files in os.walk('tests'):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                if 'libs' in root or 'libs' in file:
                    test_name = file[5:-3] if file.startswith('test_') else file[:-3]  # Remove test_ prefix and .py
                    test_files.append(test_name)
    return set(test_files)


def analyze_coverage():
    """Analyze test coverage gaps"""
    
    libs_modules = get_libs_modules()
    test_files = get_existing_libs_tests()
    
    missing_tests = libs_modules - test_files
    
    print("📊 Test Coverage Analysis")
    print("=" * 50)
    print(f"Total libs modules: {len(libs_modules)}")
    print(f"Existing libs tests: {len(test_files)}")
    print(f"Missing tests for: {len(missing_tests)} modules")
    print(f"Coverage: {((len(libs_modules) - len(missing_tests)) / len(libs_modules) * 100):.1f}%")
    print()
    
    print("📁 Sample libs modules:")
    for module in sorted(libs_modules)[:10]:
        print(f"  {module}")
    print()
    
    print("🧪 Sample existing tests:")
    for test in sorted(test_files)[:10]:
        print(f"  test_{test}")
    print()
    
    print("❌ Modules without tests:")
    for module in sorted(missing_tests)[:20]:
        print(f"  {module}")
    
    return missing_tests


def main():
    """Main analysis function"""
    missing_tests = analyze_coverage()
    
    # Identify high-priority modules for test creation
    priority_modules = []
    
    for module in missing_tests:
        module_path = f"libs/{module}.py"
        if os.path.exists(module_path):
            try:
                with open(module_path, 'r') as f:
                    content = f.read()
                
                # Check if module has substantial code
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                code_lines = [line for line in lines if not line.startswith('#') and not line.startswith('"""')]
                
                if len(code_lines) > 10:  # Substantial module
                    priority_modules.append((module, len(code_lines)))
            except:
                continue
    
    # Sort by code size
    priority_modules.sort(key=lambda x: x[1], reverse=True)
    
    print("\n🎯 High-priority modules for test creation:")
    for module, lines in priority_modules[:10]:
        print(f"  {module} ({lines} lines of code)")
    
    return priority_modules


if __name__ == "__main__":
    main()