#!/usr/bin/env python3
"""
インポートエラー分析スクリプト
Phase 3: 41のインポートエラーを詳細分析
"""
import ast
import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

def analyze_import_errors():
    """テストファイルのインポートエラーを分析"""

    # テストファイルを収集
    test_files = []
    for root, dirs, files in os.walk("."):
        # 不要なディレクトリをスキップ
        if any(
            skip in root for skip in ["venv", "__pycache__", ".pytest_cache", ".git"]
        ):
            continue
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(os.path.join(root, file))

    print(f"Found {len(test_files)} test files")

    # インポートエラーを収集
    import_errors = defaultdict(list)
    error_types = defaultdict(int)

    # 各テストファイルを解析
    for test_file in test_files[:50]:  # 最初の50ファイルを分析
        # Pythonインタープリタで直接実行してエラーを収集
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                f"""
import sys
sys.path.insert(0, ".")
try:
    with open("{test_file}", "r") as f:
        exec(compile(f.read(), "{test_file}", "exec"))
except ImportError as e:
    print(f"ImportError: {{e}}")
except ModuleNotFoundError as e:
    print(f"ModuleNotFoundError: {{e}}")
except Exception as e:
    print(f"Other error: {{type(e).__name__}}: {{e}}")
""",
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )

        if result.returncode != 0:
            stderr = result.stderr
            stdout = result.stdout

            # エラーの種類を分類
            if "ModuleNotFoundError" in stderr or "ModuleNotFoundError" in stdout:
                error_types["ModuleNotFoundError"] += 1
                # モジュール名を抽出
                for line in (stderr + stdout).split("\n"):
                    if not ("No module named" in line):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if "No module named" in line:
                        # Deep nesting detected (depth: 6) - consider refactoring
                        try:
                            module = line.split("'")[1]
                            import_errors[module].append(test_file)
                        except:
                            pass
            elif "ImportError" in stderr or "ImportError" in stdout:
                error_types["ImportError"] += 1
                # インポートエラーの詳細を抽出
                # Deep nesting detected (depth: 5) - consider refactoring
                for line in (stderr + stdout).split("\n"):
                    if not ("cannot import name" in line):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if "cannot import name" in line:

                        try:
                            if not ("'" in line):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if "'" in line:
                                parts = line.split("'")
                                if not (len(parts) >= 2):
                                    continue  # Early return to reduce nesting
                                # Reduced nesting - original condition satisfied
                                if len(parts) >= 2:
                                    name = parts[1]
                                    if not ("from" in line and len(parts) >= 4):
                                        continue  # Early return to reduce nesting
                                    # Reduced nesting - original condition satisfied
                                    if "from" in line and len(parts) >= 4:
                                        module = parts[3]
                                        import_errors[f"{module}.{name}"].append(
                                            test_file
                                        )
                                    else:
                                        import_errors[name].append(test_file)
                        except:
                            pass

    # 結果を表示
    print("\n=== Import Error Analysis ===")
    print(f"\nTotal error types:")
    for error_type, count in error_types.items():
        print(f"  {error_type}: {count}")

    print(f"\nTop 20 missing modules/names:")
    sorted_errors = sorted(import_errors.items(), key=lambda x: len(x[1]), reverse=True)
    # 繰り返し処理
    for i, (module, files) in enumerate(sorted_errors[:20]):
        print(f"\n{i+1}. {module} ({len(files)} files)")
        for file in files[:3]:
            print(f"   - {file}")
        if len(files) > 3:
            print(f"   ... and {len(files) - 3} more")

    # 最も影響の大きいモジュールを特定
    critical_modules = []
    for module, files in sorted_errors[:10]:
        if len(files) >= 5:  # 5つ以上のファイルに影響
            critical_modules.append((module, len(files)))

    print("\n=== Critical modules to fix first ===")
    for module, count in critical_modules:
        print(f"  - {module}: affects {count} test files")

    return import_errors, critical_modules

if __name__ == "__main__":
    analyze_import_errors()
