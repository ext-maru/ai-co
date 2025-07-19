#!/usr/bin/env python3
"""
Analyze test errors from test report
"""

import json
import re
from collections import defaultdict
from pathlib import Path


def analyze_test_report():
    """Analyze test report for common error patterns"""
    report_file = Path(__file__).parent / "test_report.json"

    with open(report_file, "r") as f:
        report = json.load(f)

    error_patterns = defaultdict(list)
    error_counts = defaultdict(int)

    for result in report["results"]:
        if result["status"] != "passed":
            # Extract error messages from stderr and stdout
            error_text = result.get("stderr", "") + result.get("stdout", "")

            # Common patterns
            if "AMQPConnectionError" in error_text:
                error_patterns["AMQPConnectionError"].append(result["file"])
                error_counts["AMQPConnectionError"] += 1

            if "AttributeError" in error_text:
                error_patterns["AttributeError"].append(result["file"])
                error_counts["AttributeError"] += 1

            if "ImportError" in error_text or "ModuleNotFoundError" in error_text:
                error_patterns["ImportError"].append(result["file"])
                error_counts["ImportError"] += 1

            if "Mock" in error_text and "assert" in error_text:
                error_patterns["Mock/Assert"].append(result["file"])
                error_counts["Mock/Assert"] += 1

            if "connect" in error_text.lower():
                error_patterns["Connection"].append(result["file"])
                error_counts["Connection"] += 1

    print("Error Pattern Analysis")
    print("=" * 50)

    for pattern, files in sorted(
        error_patterns.items(), key=lambda x: len(x[1]), reverse=True
    ):
        print(f"\n{pattern} ({len(files)} files):")
        for file in sorted(set(files)):
            print(f"  - {file}")

    print("\n\nRecommendations:")
    print("=" * 50)

    if "AMQPConnectionError" in error_patterns:
        print("1. AMQPConnectionError issues:")
        print("   - Need to properly mock pika.exceptions")
        print("   - Ensure pika_exceptions is defined in test files")

    if "Connection" in error_patterns:
        print("2. Connection-related issues:")
        print("   - Mock pika.BlockingConnection properly")
        print("   - Handle retry logic in tests")

    if "Mock/Assert" in error_patterns:
        print("3. Mock/Assertion issues:")
        print("   - Review mock setup and expectations")
        print("   - Check call counts and arguments")


if __name__ == "__main__":
    analyze_test_report()
