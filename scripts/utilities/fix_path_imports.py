#!/usr/bin/env python3
"""Fix Path import issues in test files"""

import os
import re
from pathlib import Path


def fix_path_imports(directory):
    """Fix Path import issues in all Python test files"""
    fixed_files = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)

                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Check if file uses Path without importing it first
                    if "PROJECT_ROOT = Path(" in content:
                        lines = content.split("\n")

                        # Find where Path is used
                        path_usage_line = None
                        path_import_line = None

                        for i, line in enumerate(lines):
                            if "PROJECT_ROOT = Path(" in line:
                                path_usage_line = i
                            if "from pathlib import Path" in line:
                                path_import_line = i

                        # If Path is used before import, fix it
                        if path_usage_line is not None and (
                            path_import_line is None
                            or path_import_line > path_usage_line
                        ):
                            # Add import after shebang and encoding
                            insert_pos = 0
                            if lines[0].startswith("#!"):
                                insert_pos = 1
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
                                if "import sys" in lines[i]:
                                    sys_import_pos = i
                                    break

                            # Insert Path import after sys import if present
                            if sys_import_pos is not None:
                                lines.insert(
                                    sys_import_pos + 1, "from pathlib import Path"
                                )
                            else:
                                lines.insert(insert_pos, "from pathlib import Path")

                            # Remove duplicate Path import if exists later
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
