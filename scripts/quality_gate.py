#!/usr/bin/env python3
import subprocess
import sys
import json


def run_quality_checks():
    results = {"passed": True, "checks": []}

    # テスト実行
    try:
        result = subprocess.run(
            ["pytest", "--tb=short"], capture_output=True, text=True
        )
        test_passed = result.returncode == 0
        results["checks"].append({"test": "pytest", "passed": test_passed})
    except:
        results["checks"].append({"test": "pytest", "passed": False})

    # カバレッジチェック
    try:
        result = subprocess.run(
            ["pytest", "--cov=.", "--cov-report=json"], capture_output=True, text=True
        )
        coverage_passed = result.returncode == 0
        results["checks"].append({"test": "coverage", "passed": coverage_passed})
    except:
        results["checks"].append({"test": "coverage", "passed": False})

    # Lintチェック
    try:
        result = subprocess.run(["flake8", "."], capture_output=True, text=True)
        lint_passed = result.returncode == 0
        results["checks"].append({"test": "lint", "passed": lint_passed})
    except:
        results["checks"].append({"test": "lint", "passed": False})

    results["passed"] = all(check["passed"] for check in results["checks"])
    return results


if __name__ == "__main__":
    results = run_quality_checks()
    if results["passed"]:
        print("✅ All quality gates passed!")
        sys.exit(0)
    else:
        print("❌ Quality gates failed!")
        print(json.dumps(results, indent=2))
        sys.exit(1)
