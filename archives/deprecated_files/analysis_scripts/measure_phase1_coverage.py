#!/usr/bin/env python3
"""
Week 3 Phase 1 Coverage Measurement Report
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_coverage_test(test_path, module_name):
    """Run coverage test for a specific module"""
    cmd = [
        "python3",
        "-m",
        "pytest",
        test_path,
        f"--cov={module_name}",
        "--cov-report=json",
        "--cov-report=term",
        "-q",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Parse coverage JSON if exists
        coverage_file = Path("coverage.json")
        if coverage_file.exists():
            with open(coverage_file) as f:
                coverage_data = json.load(f)

            # Extract coverage percentage
            if "totals" in coverage_data:
                percent_covered = coverage_data["totals"]["percent_covered"]
                return {
                    "module": module_name,
                    "test_path": test_path,
                    "coverage_percent": percent_covered,
                    "lines_total": coverage_data["totals"]["num_statements"],
                    "lines_covered": coverage_data["totals"]["covered_lines"],
                    "lines_missing": coverage_data["totals"]["missing_lines"],
                    "status": "success",
                }

        # Fallback: parse from terminal output
        for line in result.stdout.split("\n"):
            if module_name in line and "%" in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if not ("%" in part):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if "%" in part:
                        percent = float(part.rstrip("%"))
                        return {
                            "module": module_name,
                            "test_path": test_path,
                            "coverage_percent": percent,
                            "status": "success",
                        }

    except Exception as e:
        return {
            "module": module_name,
            "test_path": test_path,
            "error": str(e),
            "status": "error",
        }

    return {"module": module_name, "test_path": test_path, "status": "no_coverage_data"}


def main():
    """Main coverage measurement"""
    print("=" * 80)
    print("Elders Guild - Week 3 Phase 1 Coverage Report")
    print("=" * 80)
    print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Define modules tested in Phase 1
    modules_tested = [
        {
            "name": "core.monitoring_mixin",
            "test": "tests/unit/core/test_monitoring_mixin.py",
            "description": "Monitoring functionality mixin",
        },
        {
            "name": "libs.queue_manager",
            "test": "tests/unit/libs/test_queue_manager.py",
            "description": "RabbitMQ queue management",
        },
        {
            "name": "workers.result_worker",
            "test": "tests/unit/test_workers/test_result_worker.py",
            "description": "Result processing worker",
        },
        {
            "name": "libs.database_manager",
            "test": "tests/unit/libs/test_database_manager.py",
            "description": "Database connection management",
        },
    ]

    # Run coverage for each module
    results = []
    total_lines = 0
    covered_lines = 0

    for module in modules_tested:
        print(f"Testing {module['name']}...")
        result = run_coverage_test(module["test"], module["name"])
        result["description"] = module["description"]
        results.append(result)

        if result.get("lines_total"):
            total_lines += result["lines_total"]
            covered_lines += result["lines_covered"]

    # Run overall coverage test
    print("\nRunning overall coverage test...")
    overall_cmd = [
        "python3",
        "-m",
        "pytest",
        "tests/",
        "--cov=.",
        "--cov-report=json",
        "--cov-report=term",
        "-q",
        "--tb=no",
        "-x",  # Stop on first failure to get quick results
    ]

    try:
        subprocess.run(overall_cmd, capture_output=True, text=True, timeout=60)

        # Read overall coverage
        coverage_file = Path("coverage.json")
        if coverage_file.exists():
            with open(coverage_file) as f:
                overall_data = json.load(f)
                overall_percent = overall_data["totals"]["percent_covered"]
        else:
            overall_percent = None
    except:
        overall_percent = None

    # Generate report
    print("\n" + "=" * 80)
    print("PHASE 1 COVERAGE RESULTS")
    print("=" * 80)

    print("\nModule-by-Module Results:")
    print("-" * 80)
    print(f"{'Module':<30} {'Description':<30} {'Coverage':>10} {'Status':>10}")
    print("-" * 80)

    for result in results:
        module = result["module"]
        desc = result["description"][:30]
        if result["status"] == "success":
            coverage = f"{result['coverage_percent']:.1f}%"
        else:
            coverage = "N/A"
        status = result["status"]

        print(f"{module:<30} {desc:<30} {coverage:>10} {status:>10}")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    # Calculate achieved coverage
    successful_tests = [r for r in results if r["status"] == "success"]
    if successful_tests:
        avg_module_coverage = sum(
            r["coverage_percent"] for r in successful_tests
        ) / len(successful_tests)
        print(f"Average Module Coverage: {avg_module_coverage:.1f}%")

    if overall_percent:
        print(f"Overall Project Coverage: {overall_percent:.1f}%")
        print(
            f"Coverage Improvement: {overall_percent - 2.21:.1f}% (from baseline 2.21%)"
        )

    print(f"\nModules Activated: {len(modules_tested)}")
    print(f"Successful Tests: {len(successful_tests)}")

    if total_lines > 0:
        actual_coverage = (covered_lines / total_lines) * 100
        print(f"\nLines Coverage for Tested Modules:")
        print(f"  Total Lines: {total_lines}")
        print(f"  Covered Lines: {covered_lines}")
        print(f"  Coverage: {actual_coverage:.1f}%")

    # Save detailed report
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "phase": "Week 3 Phase 1",
        "modules_tested": results,
        "overall_coverage": overall_percent,
        "baseline_coverage": 2.21,
        "summary": {
            "modules_activated": len(modules_tested),
            "successful_tests": len(successful_tests),
            "average_module_coverage": avg_module_coverage if successful_tests else 0,
            "total_lines_tested": total_lines,
            "covered_lines": covered_lines,
        },
    }

    with open("phase1_coverage_report.json", "w") as f:
        json.dump(report_data, f, indent=2)

    print(f"\nDetailed report saved to: phase1_coverage_report.json")

    # Recommendations for Phase 2
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS FOR PHASE 2")
    print("=" * 80)
    print("1. Fix failing tests in database_manager and result_worker")
    print("2. Target high-line-count modules:")
    print("   - workers/enhanced_pm_worker.py (748 lines)")
    print("   - workers/task_worker.py")
    print("   - core/base_worker.py")
    print("3. Implement batch test generation for similar modules")
    print("4. Use proven patterns from monitoring_mixin (99% coverage)")
    print("5. Focus on import verification and basic functionality tests")

    return overall_percent


if __name__ == "__main__":
    coverage = main()
    sys.exit(0 if coverage and coverage > 10 else 1)
