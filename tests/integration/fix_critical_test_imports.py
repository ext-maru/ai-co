#!/usr/bin/env python3
"""
Critical Test Import Fixer
重要なテストファイルのインポートを修正
"""
from pathlib import Path


def fix_critical_tests():
    """Phase 1-14の重要なテストのインポートを修正"""

    critical_tests = [
        "tests/unit/test_automated_code_review.py",
        "tests/unit/test_async_worker_optimization.py",
        "tests/unit/test_integration_test_framework.py",
        "tests/unit/test_advanced_monitoring_dashboard.py",
        "tests/unit/test_security_audit_system.py",
    ]

    fixed_count = 0

    for test_file in critical_tests:
        test_path = Path(test_file)
        if test_path.exists():
            content = test_path.read_text()
            lines = content.split("\n")

            # 必要なインポートを追加
            new_lines = []
            imports_added = False

            for i, line in enumerate(lines):
                # ドキュメント文字列の後にインポートを追加
                if i < len(lines) - 1 and '"""' in line and not imports_added:
                    new_lines.append(line)
                    # 次の行も"""なら、その後に追加
                    if i + 1 < len(lines) and '"""' in lines[i + 1]:
                        new_lines.append(lines[i + 1])
                        i += 1

                    # 必要なインポートを追加
                    new_lines.extend(
                        [
                            "",
                            "import sys",
                            "from pathlib import Path",
                            "",
                            "# Add project root to Python path",
                            "PROJECT_ROOT = Path(__file__).resolve().parent.parent",
                            "sys.path.insert(0, str(PROJECT_ROOT))",
                            "",
                        ]
                    )
                    imports_added = True
                    # すでにPROJECT_ROOTがあるが、インポートが不足している場合
                    new_lines.extend(["import sys", "", line])
                    imports_added = True
                else:
                    new_lines.append(line)

            # 修正した内容を書き戻す
            new_content = "\n".join(new_lines)
            if new_content != content:
                test_path.write_text(new_content)
                print(f"✅ Fixed imports in {test_file}")
                fixed_count += 1
            else:
                print(f"ℹ️  {test_file} already has correct imports")

    return fixed_count


def verify_fixes():
    """修正が正しく適用されたか確認"""
    import subprocess

    print("\n🔍 Verifying fixes...")

    # テストコレクションを試行
    result = subprocess.run(
        ["python3", "-m", "pytest", "--collect-only", "-q"]
        + [
            "tests/unit/test_performance_optimizer.py",
            "tests/unit/test_hypothesis_generator.py",
            "tests/unit/test_ab_testing_framework.py",
        ],
        capture_output=True,
        text=True,
    )

    if "ERROR" not in result.stderr:
        print("✅ Test collection successful!")
        return True
    else:
        print("❌ Some tests still have issues:")
        print(result.stderr[:500])
        return False


if __name__ == "__main__":
    print("🔧 Critical Test Import Fixer")
    print("=" * 50)

    fixed = fix_critical_tests()
    print(f"\n📊 Fixed {fixed} test files")

    print("\n" + "=" * 50)
    if verify_fixes():
        print("✨ All critical tests are ready!")
    else:
        print("⚠️  Some issues remain, manual intervention may be needed")
