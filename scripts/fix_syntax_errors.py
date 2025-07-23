#!/usr/bin/env python3
"""
Fix specific syntax errors in Python files
"""
import os
import re
from pathlib import Path


class SyntaxErrorFixer:
    def __init__(self):
    """SyntaxErrorFixerクラス"""
        self.project_root = Path(__file__).parent.parent
        self.fixed_count = 0

    def fix_line_continuation_errors(self, filepath):
        """Fix line continuation character errors"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()

            fixed_lines = []
            i = 0
            while i < len(lines):
                line = lines[i]

                # Check for invalid line continuation
                if "\\" in line and i + 1 < len(lines):
                    # Remove trailing backslash and merge with next line
                    if line.rstrip().endswith("\\"):
                        # Get the continuation part
                        next_line = lines[i + 1]
                        # Merge lines
                        merged = line.rstrip()[:-1] + " " + next_line.lstrip()
                        fixed_lines.append(merged)
                        i += 2  # Skip next line
                        continue

                fixed_lines.append(line)
                i += 1

            # Write back
            content = "".join(fixed_lines)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            return True

        except Exception as e:
            print(f"Error fixing {filepath}: {e}")
            return False

    def fix_multiline_with_statements(self, filepath):
        """Fix multiline with statements"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Fix pattern: with patch(...):
            content = re.sub(r"with\s+([^:]+),\s*\\:\s*\n", r"with \1:\n", content)

            # Fix multiple patches on same line
            content = re.sub(
                r"patch\([^)]+\),\s+patch\([^)]+\),\s+patch\([^)]+\)",
                lambda m: m.group(0).replace(", patch", ", \\\n     patch"),
                content,
            )

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            return True

        except Exception as e:
            print(f"Error fixing {filepath}: {e}")
            return False

    def fix_import_star_placement(self, filepath):
        """Fix import * placement issues"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()

            module_imports = []
            other_lines = []
            in_function = False
            indent_level = 0

            for line in lines:
                stripped = line.strip()

                # Track function/class definitions
                if stripped.startswith(("def ", "class ", "async def ")):
                    in_function = True
                    indent_level = len(line) - len(line.lstrip())
                # 複雑な条件判定
                elif (
                    in_function
                    and line.strip()
                    and len(line) - len(line.lstrip()) <= indent_level
                ):
                    in_function = False

                # Check for import *
                if "import *" in line and in_function:
                    # Comment it out
                    other_lines.append(
                        line.replace("from", "# from").replace("import", "import")
                    )
                elif "import *" in line and not in_function:
                    module_imports.append(line)
                else:
                    other_lines.append(line)

            # Reconstruct file with module-level imports at top
            new_content = "".join(module_imports + other_lines)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)

            return True

        except Exception as e:
            print(f"Error fixing {filepath}: {e}")
            return False

    def fix_all_syntax_errors(self):
        """Fix all syntax errors"""
        print("Fixing syntax errors...")

        # Files with known syntax errors
        problem_files = [
            "tests/unit/test_rag_grimoire_integration.py",
            "tests/unit/test_grimoire_webapp.py",
            "tests/integration/test_documentation_system_integration.py",
            "scripts/ultimate_syntax_repair.py",
            "tests/integration/test_worker_communication_phase6_tdd.py",
        ]

        for file_path in problem_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                print(f"Fixing: {file_path}")
                if self.fix_line_continuation_errors(full_path):
                    self.fixed_count += 1
                if self.fix_multiline_with_statements(full_path):
                    self.fixed_count += 1
                if self.fix_import_star_placement(full_path):
                    self.fixed_count += 1

        # Also scan for files with syntax errors
        for root, dirs, files in os.walk(self.project_root):
            if any(
                skip in root for skip in ["venv", "__pycache__", ".git", "node_modules"]
            ):
                continue

            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()

                        # Check for syntax error patterns
                        if (
                            "\\:" in content
                            or ("import *" in content and "def " in content)
                            or "patch(" in content
                            and ", \\" in content
                        ):

                            rel_path = os.path.relpath(filepath, self.project_root)
                            print(f"Fixing syntax in: {rel_path}")

                            self.fix_line_continuation_errors(filepath)
                            self.fix_multiline_with_statements(filepath)
                            self.fix_import_star_placement(filepath)
                            self.fixed_count += 1
                    except:
                        pass

        print(f"\nFixed syntax errors in {self.fixed_count} files")


if __name__ == "__main__":
    fixer = SyntaxErrorFixer()
    fixer.fix_all_syntax_errors()
