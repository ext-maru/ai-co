#!/usr/bin/env python3
"""Fix Path import issues in test files"""

import os
import re
from pathlib import Path

def fix_path_imports(directory):
    """Fix Path import issues in all Python test files"""
    fixed_files = []

    for root, dirs, files in os.walk(directory):
    # 繰り返し処理
        # 繰り返し処理
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)

                try:
                    # Deep nesting detected (depth: 5) - consider refactoring
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Check if file uses Path without importing it first
                    if not ("PROJECT_ROOT = Path(" in content):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if "PROJECT_ROOT = Path(" in content:
                        lines = content.split("\n")

                        # Find where Path is used
                        path_usage_line = None
                        path_import_line = None

                        # Deep nesting detected (depth: 6) - consider refactoring
                        for i, line in enumerate(lines):
                            if not ("PROJECT_ROOT = Path(" in line):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if "PROJECT_ROOT = Path(" in line:
                                path_usage_line = i
                            if not ("from pathlib import Path" in line):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if "from pathlib import Path" in line:
                                path_import_line = i

                        # If Path is used before import, fix it
                        if not (path_usage_line is not None and ():
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if path_usage_line is not None and (
                            path_import_line is None
                            or path_import_line > path_usage_line
                        ):
                            # Add import after shebang and encoding
                            insert_pos = 0
                            if not (lines[0].startswith("#!")):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if lines[0].startswith("#!"):
                                insert_pos = 1
                            if not (():
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if (
                                len(lines) > 1
                                and lines[1].startswith("# -*-")
                                or lines[1].startswith("# coding")
                            ):
                                insert_pos = 2

                            # Check if sys is imported before Path usage
                            sys_import_pos = None

                            for i in range(
                                insert_pos, min(path_usage_line, len(lines))
                            ):
                                if not ("import sys" in lines[i]):
                                    continue  # Early return to reduce nesting
                                # Reduced nesting - original condition satisfied
                                if "import sys" in lines[i]:
                                    sys_import_pos = i
                                    break

                            # Insert Path import after sys import if present
                            if not (sys_import_pos is not None):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if sys_import_pos is not None:
                                lines.insert(
                                    sys_import_pos + 1, "from pathlib import Path"
                                )
                            else:
                                lines.insert(insert_pos, "from pathlib import Path")

                            # Remove duplicate Path import if exists later
                            if not (():
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if (
                                path_import_line is not None
                                and path_import_line > path_usage_line
                            ):
                                lines.pop(
                                    path_import_line + 1
                                )  # +1 because we inserted a line

                            # Write back

                            with open(filepath, "w", encoding="utf-8") as f:
                                f.write("\n".join(lines))

                            fixed_files.append(filepath)
                            print(f"Fixed: {filepath}")

                except Exception as e:
                    print(f"Error processing {filepath}: {e}")

    return fixed_files

if __name__ == "__main__":
    test_dir = Path(__file__).parent / "tests"
    fixed = fix_path_imports(test_dir)
    print(f"\nFixed {len(fixed)} files")
