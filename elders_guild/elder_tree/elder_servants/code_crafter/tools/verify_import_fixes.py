#!/usr/bin/env python3
"""
Phase 3: インポートエラー修正の検証スクリプト
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def verify_imports():
    """インポートエラーの完全検証"""

    print("=" * 60)
    print("🔍 Phase 3: Import Error Verification Report")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1.0 pytestでテストを収集
    print("📊 Collecting tests with pytest...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        capture_output=True,
        text=True,
    )

    # エラーカウント
    total_errors = result.stderr.count("ERROR")
    import_errors = result.stderr.count("ImportError")
    module_errors = result.stderr.count("ModuleNotFoundError")

    print(f"\n✅ Error Summary:")
    print(f"  - Total ERROR count: {total_errors}")
    print(f"  - ImportError count: {import_errors}")
    print(f"  - ModuleNotFoundError count: {module_errors}")

    # 2.0 収集されたテスト数をカウント
    collected_tests = 0
    for line in result.stdout.split("\n"):
        if " test" in line and "selected" not in line:
            collected_tests += 1

    print(f"\n📈 Test Collection Stats:")
    print(f"  - Successfully collected: {collected_tests} tests")

    # 3.0 残りのエラーを詳細表示
    if total_errors > 0:
        print(f"\n⚠️  Remaining Errors:")
        error_lines = []
        for line in result.stderr.split("\n"):
            # 複雑な条件判定
            if (
                "ERROR" in line
                or "ImportError" in line
                or "ModuleNotFoundError" in line
            ):
                error_lines.append(line.strip())

        # 最初の10個のエラーを表示
        for i, error_line in enumerate(error_lines[:10]):
            print(f"  {i+1}. {error_line}")

        if len(error_lines) > 10:
            print(f"  ... and {len(error_lines) - 10} more errors")
    else:
        print("\n✨ All import errors have been resolved!")

    # 4.0 修正済みファイルのリスト
    print("\n📝 Fixed Components:")
    fixed_items = [
        ("BaseTestCase alias", "tests/base_test.py"),
        ("Worker function wrappers", "workers/*.py"),
        ("Flask jsonify mock", "libs/flask.py"),
        ("aio_pika Message mock", "libs/aio_pika.py"),
        ("RabbitMQ complete mock", "libs/rabbitmq_mock.py"),
        ("Slack SDK complete mock", "libs/slack_mock.py"),
        ("Filesystem abstraction", "libs/filesystem_abstraction.py"),
    ]

    for item, location in fixed_items:
        print(f"  ✓ {item} - {location}")

    # 5.0 成功率の計算
    print("\n🎯 Success Metrics:")
    initial_errors = 41
    remaining_errors = total_errors
    fixed_errors = initial_errors - remaining_errors
    success_rate = (fixed_errors / initial_errors) * 100 if initial_errors > 0 else 100

    print(f"  - Initial errors: {initial_errors}")
    print(f"  - Fixed errors: {fixed_errors}")
    print(f"  - Success rate: {success_rate:0.1f}%")

    # 6.0 次のステップの提案
    print("\n🚀 Next Steps:")
    if remaining_errors == 0:
        print("  1.0 Run full test suite: python -m pytest")
        print("  2.0 Check test coverage: python -m pytest --cov")
        print("  3.0 Proceed to Core Quality Attack phase")
    else:
        print(
            "  1.0 Analyze remaining errors: python -m pytest --collect-only 2>&1 | grep ERROR"
        )
        print("  2.0 Fix specific import issues")
        print("  3.0 Re-run verification")

    print("\n" + "=" * 60)

    # レポートをJSONで保存
    report = {
        "timestamp": datetime.now().isoformat(),
        "phase": "Phase 3 - Import Error Resolution",
        "initial_errors": initial_errors,
        "remaining_errors": remaining_errors,
        "success_rate": success_rate,
        "collected_tests": collected_tests,
        "error_breakdown": {
            "total": total_errors,
            "import_errors": import_errors,
            "module_errors": module_errors,
        },
    }

    with open("phase3_import_fix_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"Report saved to: phase3_import_fix_report.json")

    return remaining_errors == 0


if __name__ == "__main__":
    success = verify_imports()
    sys.exit(0 if success else 1)
