#!/usr/bin/env python3
"""
インポートエラー自動修復スクリプト
エルダー評議会緊急対策
"""
import ast
import re
import sys
from pathlib import Path


def fix_import_errors():
    """テストファイルのインポートエラーを自動修復"""
    test_files = list(Path("tests").glob("**/*.py"))
    fixed_count = 0
    error_files = []

    print(f"🔍 Found {len(test_files)} test files to check...")

    for test_file in test_files:
        if test_file.name == "__init__.py":
            continue

        try:
            content = test_file.read_text()
            original_content = content
            modified = False

            # Fix 1: Add sys.path manipulation if missing
            if "sys.path" not in content and "import" in content:
                lines = content.split("\n")

                # Find where to insert sys.path manipulation
                import_line = -1
                for i, line in enumerate(lines):
                    if line.strip().startswith("import ") or line.strip().startswith(
                        "from "
                    ):
                        import_line = i
                        break

                if import_line > 0:
                    # Check if we already have Path import
                    if "from pathlib import Path" not in content:
                        lines.insert(import_line, "from pathlib import Path")
                        import_line += 1

                    # Add sys.path manipulation
                    path_insert = [
                        "",
                        "# Add project root to Python path",
                        "PROJECT_ROOT = Path(__file__).parent.parent.parent",
                        "sys.path.insert(0, str(PROJECT_ROOT))",
                        "",
                    ]

                    for i, line in enumerate(path_insert):
                        lines.insert(import_line + i, line)

                    content = "\n".join(lines)
                    modified = True

            # Fix 2: Replace relative imports with absolute imports
            if "from .." in content or "from ." in content:
                # Convert relative imports to absolute
                content = re.sub(r"from \.\. import", "from ai_co import", content)
                content = re.sub(r"from \. import", "from ai_co import", content)
                modified = True

            # Fix 3: Fix common import errors
            replacements = [
                ("from tests.base_test import", "from base_test import"),
                ("from workers.", "from workers."),
                ("from libs.", "from libs."),
                ("from core.", "from core."),
            ]

            for old, new in replacements:
                if old in content and old != new:
                    content = content.replace(old, new)
                    modified = True

            # Write back if modified
            if modified and content != original_content:
                test_file.write_text(content)
                fixed_count += 1
                print(f"✅ Fixed imports in: {test_file}")

        except Exception as e:
            error_files.append((test_file, str(e)))
            print(f"❌ Error processing {test_file}: {e}")

    print(f"\n📊 Summary:")
    print(f"✅ Fixed {fixed_count} files")
    print(f"❌ {len(error_files)} files had errors")

    if error_files:
        print("\n⚠️ Files with errors:")
        for file, error in error_files[:5]:  # Show first 5 errors
            print(f"  - {file}: {error}")


def check_and_fix_specific_errors():
    """特定の既知のエラーを修正"""

    # Fix error_intelligence_worker test
    error_intel_test = Path("tests/unit/test_error_intelligence_worker_incident.py")
    if error_intel_test.exists():
        content = error_intel_test.read_text()

        # Fix the class name typo
        content = content.replace(
            "class Testerror_intelligence_workerWithIncident",
            "class TestErrorIntelligenceWorkerWithIncident",
        )

        error_intel_test.write_text(content)
        print(f"✅ Fixed class name in {error_intel_test}")

    # Create missing test base imports
    test_dirs = ["tests/unit/test_workers", "tests/unit/web", "tests/integration"]
    for test_dir in test_dirs:
        dir_path = Path(test_dir)
        if dir_path.exists():
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                init_file.write_text("# Test package\n")
                print(f"✅ Created {init_file}")


if __name__ == "__main__":
    print("🔧 Elder Council Import Error Fix Script")
    print("=" * 50)

    fix_import_errors()
    print("\n" + "=" * 50)

    check_and_fix_specific_errors()
    print("=" * 50)
    print("✨ Import error fixes completed!")
