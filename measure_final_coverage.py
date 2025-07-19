#!/usr/bin/env python3
"""
Measure final coverage after Week 3 Phase 2 implementation
"""

import json
import subprocess
import sys
from pathlib import Path


def run_coverage_test():
    """Run pytest with coverage and parse results"""

    print("🚀 Running Week 3 Phase 2 Final Coverage Measurement...")
    print("=" * 60)

    # Find all test files
    test_files = [
        "tests/unit/test_monitoring_mixin.py",
        "tests/unit/test_queue_manager.py",
        "tests/unit/test_workers/test_enhanced_pm_worker_simple.py",
        "tests/unit/test_enhanced_task_worker_comprehensive.py",
        "tests/unit/test_rag_manager.py",
        "tests/unit/libs/test_claude_task_tracker.py",
    ]

    # Filter to existing files
    existing_tests = [f for f in test_files if Path(f).exists()]

    if not existing_tests:
        print("❌ No test files found!")
        return

    print(f"Found {len(existing_tests)} test files")

    # Run pytest with coverage
    cmd = [
        "python3",
        "-m",
        "pytest",
        *existing_tests,
        "--cov=.",
        "--cov-report=term",
        "--cov-report=json",
        "-q",
        "--tb=short",
    ]

    print("\nRunning tests...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Parse coverage.json if it exists
    coverage_file = Path("coverage.json")
    if coverage_file.exists():
        with open(coverage_file) as f:
            coverage_data = json.load(f)

        total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)

        print("\n📊 Coverage Results:")
        print("=" * 60)
        print(f"Overall Coverage: {total_coverage:.1f}%")

        # Show key module coverage
        files = coverage_data.get("files", {})
        key_modules = [
            "libs/monitoring_mixin.py",
            "libs/queue_manager.py",
            "workers/enhanced_pm_worker.py",
            "workers/enhanced_task_worker.py",
            "libs/enhanced_rag_manager.py",
            "libs/claude_task_tracker.py",
        ]

        print("\n🎯 Key Module Coverage:")
        for module in key_modules:
            if module in files:
                module_cov = files[module]["summary"]["percent_covered"]
                print(f"  {module}: {module_cov:.1f}%")

        print("\n📈 Coverage Analysis:")
        if total_coverage >= 30:
            print(f"✅ SUCCESS! Target of 30% achieved: {total_coverage:.1f}%")
        else:
            print(f"⚠️  Current: {total_coverage:.1f}% (Target: 30%)")
            print(f"   Need {30 - total_coverage:.1f}% more coverage")

    else:
        # Fallback to parsing terminal output
        print("\nParsing terminal output...")
        output_lines = result.stdout.split("\n")

        for line in output_lines:
            if "TOTAL" in line and "%" in line:
                print(f"\n{line}")

    # Show test results summary
    if "passed" in result.stdout:
        passed_count = result.stdout.count("passed")
        print(f"\n✅ {passed_count} tests passed")

    if "failed" in result.stdout:
        failed_count = result.stdout.count("FAILED")
        print(f"❌ {failed_count} tests failed")

    print("\n" + "=" * 60)
    print("Week 3 Phase 2 Coverage Measurement Complete!")


if __name__ == "__main__":
    run_coverage_test()
