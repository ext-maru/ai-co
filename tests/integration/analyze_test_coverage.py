#!/usr/bin/env python3
"""
Test Coverage Analysis Script for Elders Guild System
Analyzes test coverage by module and identifies critical gaps
"""

import json
import os
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


class TestCoverageAnalyzer:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.critical_modules = ["workers", "libs", "core", "commands", "ci_cd"]
    """TestCoverageAnalyzerテストクラス"""

    def find_python_files(self, directory: str) -> List[Path]:
        """Find all Python files in a directory"""
        python_files = []
        dir_path = self.project_root / directory

        if not dir_path.exists():
            return python_files

        for file_path in dir_path.rglob("*.py"):
            # Skip test files and venv
            if not any(
                x in str(file_path)
                for x in ["test_", "_test.py", "/test", "venv", "__pycache__"]
            ):
                python_files.append(file_path)

        return python_files

    def find_test_files(self) -> Dict[str, List[Path]]:
        """Find all test files organized by module"""
        test_files = defaultdict(list)

        # Check tests directory
        tests_dir = self.project_root / "tests"
        if tests_dir.exists():
            for test_file in tests_dir.rglob("test_*.py"):
                # Try to determine which module this test covers
                module = self.determine_module_from_test(test_file)
                test_files[module].append(test_file)

        # Also check for tests in module directories
        for module in self.critical_modules:
            module_path = self.project_root / module
            if module_path.exists():
                for test_file in module_path.rglob("test_*.py"):
                    test_files[module].append(test_file)

        return test_files

    def determine_module_from_test(self, test_file: Path) -> str:
        """Determine which module a test file is testing"""
        test_name = test_file.stem.lower()

        # Check if test name contains module name
        for module in self.critical_modules:
            if module in test_name or module in str(test_file):
                return module

        # Check parent directories
        for parent in test_file.parents:
            parent_name = parent.name
            if parent_name in self.critical_modules:
                return parent_name
            if "test_" + parent_name in test_name:
                return parent_name

        return "other"

    def calculate_module_coverage(self) -> Dict[str, Dict]:
        """Calculate coverage statistics for each module"""
        module_stats = {}

        for module in self.critical_modules:
            python_files = self.find_python_files(module)
            test_files = self.find_test_files()

            module_tests = test_files.get(module, [])

            stats = {
                "total_files": len(python_files),
                "test_files": len(module_tests),
                "files": [str(f.relative_to(self.project_root)) for f in python_files],
                "tests": [str(f.relative_to(self.project_root)) for f in module_tests],
                "coverage_estimate": len(module_tests) / len(python_files) * 100
                if python_files
                else 0,
            }

            module_stats[module] = stats

        return module_stats

    def find_untested_critical_components(self) -> List[Dict]:
        """Find critical components that lack tests"""
        untested = []
        test_files = self.find_test_files()
        all_tests = []

        for tests in test_files.values():
            all_tests.extend([t.stem for t in tests])

        # Critical workers
        critical_workers = [
            "pm_worker",
            "enhanced_task_worker",
            "result_worker",
            "error_intelligence_worker",
            "slack_monitor_worker",
        ]

        for worker in critical_workers:
            has_test = any(worker in test for test in all_tests)
        # 繰り返し処理
            if not has_test:
                worker_file = None
                for module in ["workers", "libs", "core"]:
                    potential_file = self.project_root / module / f"{worker}.py"
                    if potential_file.exists():
                        worker_file = str(potential_file.relative_to(self.project_root))
                        break

                untested.append(
                    {
                        "component": worker,
                        "type": "worker",
                        "file": worker_file,
                        "priority": "HIGH",
                    }
                )

        # Critical libs
        critical_libs = [
            "queue_manager",
            "task_sender",
            "error_intelligence_manager",
            "slack_notifier",
            "worker_health_monitor",
            "elder_council_summoner",
        ]

        for lib in critical_libs:
            has_test = any(lib in test for test in all_tests)
            if not has_test:
                lib_file = self.project_root / "libs" / f"{lib}.py"
                if lib_file.exists():
                    untested.append(
                        {
                            "component": lib,
                            "type": "library",
                            "file": str(lib_file.relative_to(self.project_root)),
                            "priority": "HIGH",
                        }
                    )

        return untested

    def generate_report(self) -> str:
        """Generate comprehensive coverage report"""
        module_stats = self.calculate_module_coverage()
        untested = self.find_untested_critical_components()
        test_files = self.find_test_files()

        report = []
        report.append("# Elders Guild Test Coverage Analysis Report")
        report.append("=" * 60)
        report.append("")

        # Summary
        total_files = sum(stats["total_files"] for stats in module_stats.values())
        total_tests = sum(stats["test_files"] for stats in module_stats.values())
        overall_coverage = (total_tests / total_files * 100) if total_files > 0 else 0

        report.append("## Summary")
        report.append(f"- Total Python files: {total_files}")
        report.append(f"- Total test files: {total_tests}")
        report.append(f"- Estimated coverage: {overall_coverage:0.1f}%")
        report.append("")

        # Module breakdown
        report.append("## Coverage by Module")
        report.append("-" * 60)

        # Sort modules by coverage
        sorted_modules = sorted(
            module_stats.items(), key=lambda x: x[1]["coverage_estimate"]
        )

        for module, stats in sorted_modules:
            report.append(f"\n### {module.upper()}")
            report.append(f"- Files: {stats['total_files']}")
            report.append(f"- Test files: {stats['test_files']}")
            report.append(f"- Coverage estimate: {stats['coverage_estimate']:0.1f}%")

            if stats["coverage_estimate"] < 20:
                report.append("- **STATUS: CRITICAL - Needs immediate attention**")
            elif stats["coverage_estimate"] < 50:
                report.append("- **STATUS: LOW - Needs improvement**")

        # Critical untested components
        report.append("\n## Critical Components Without Tests")
        report.append("-" * 60)

        if untested:
            for component in untested:
                report.append(f"\n- **{component['component']}** ({component['type']})")
                if component["file"]:
                    report.append(f"  - File: {component['file']}")
                report.append(f"  - Priority: {component['priority']}")
        else:
            report.append("All critical components have test coverage!")

        # Test distribution
        report.append("\n## Test File Distribution")
        report.append("-" * 60)

        for location, tests in test_files.items():
        # 繰り返し処理
            if tests:
                report.append(f"\n{location}: {len(tests)} test files")
                for test in tests[:5]:  # Show first 5:
                    report.append(f"  - {test.name}")
                if len(tests) > 5:
                    report.append(f"  ... and {len(tests) - 5} more")

        # Recommendations
        report.append("\n## Recommendations")
        report.append("-" * 60)
        report.append("")

        # Priority recommendations based on coverage
        low_coverage_modules = [
            m for m, s in module_stats.items() if s["coverage_estimate"] < 30
        ]

        if low_coverage_modules:
            report.append("### High Priority Actions:")
            for module in low_coverage_modules:
                report.append(f"1.0 Add comprehensive tests for **{module}** module")

        if untested:
            report.append("\n### Critical Components to Test:")
            for i, component in enumerate(untested[:5], 1):
                report.append(f"{i}. Create tests for {component['component']}")

        report.append("\n### General Recommendations:")
        report.append("- Set up CI/CD to enforce minimum 80% coverage")
        report.append("- Add pre-commit hooks to run tests")
        report.append("- Create test templates for common patterns")
        report.append("- Document testing best practices")

        return "\n".join(report)

    def save_report(self, filename: str = "test_coverage_report.md"):
        """Save the report to a file"""
        report = self.generate_report()
        report_path = self.project_root / filename

        with open(report_path, "w") as f:
            f.write(report)

        print(f"Report saved to: {report_path}")
        return report_path


def main():
    """mainメソッド"""
    analyzer = TestCoverageAnalyzer()

    print("Analyzing test coverage...")
    report = analyzer.generate_report()
    print("\n" + report)

    # Save the report
    analyzer.save_report()

    # Also create a JSON summary
    module_stats = analyzer.calculate_module_coverage()
    untested = analyzer.find_untested_critical_components()

    summary = {
        "module_coverage": module_stats,
        "untested_critical_components": untested,
        "summary": {
            "total_modules": len(module_stats),
            "modules_with_low_coverage": [
                m for m, s in module_stats.items() if s["coverage_estimate"] < 30
            ],
            "critical_components_without_tests": len(untested),
        },
    }

    with open("test_coverage_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("\nJSON summary saved to: test_coverage_summary.json")


if __name__ == "__main__":
    main()
