#!/usr/bin/env python3
"""
Measure Test Infrastructure Stability
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class TestStabilityMeasurer:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
    """TestStabilityMeasurerテストクラス"""
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "collection_errors": 0,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "error_tests": 0,
            "skipped_tests": 0,
            "stability_rate": 0.0,
            "execution_time": 0,
            "error_types": {},
        }

    def run_pytest_collection(self)print("🔍 Running pytest collection...")
    """Run pytest collection and count tests"""

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "--quiet",
            "--no-header",
            "--tb=no",
        ]

        env = os.environ.copy()
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                env=env if "env" in locals() else None,
            )

            # Parse output
            output = result.stdout + result.stderr

            # Count collection errors
            if "error" in output.lower():
                error_lines = [line for line in output.split("\n") if "ERROR" in line]
                self.results["collection_errors"] = len(error_lines)

            # Count collected tests
            for line in output.split("\n"):
                if "tests collected" in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "tests":
                            try:
                                self.results["total_tests"] = int(parts[i - 1])
                            except:
                                pass

            print(f"  ✓ Found {self.results['total_tests']} tests")
            print(f"  ✗ Collection errors: {self.results['collection_errors']}")

        except Exception as e:
            print(f"  ❌ Collection failed: {e}")
            self.results["collection_errors"] = -1

    def run_sample_tests(self)print("\n🧪 Running sample tests...")
    """Run a sample of tests to measure stability"""

        test_samples = [
            "tests/unit/test_basic_utilities.py",
            "tests/unit/test_base_worker_simple.py",
            "tests/unit/test_config_module.py",
            "tests/unit/test_conversation_manager.py",
            "tests/unit/test_log_manager.py",
        ]

        env = os.environ.copy()
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"

        start_time = datetime.now()
        total_run = 0
        total_passed = 0

        for test_file in test_samples:
        # 繰り返し処理
            test_path = self.project_root / test_file
            if not test_path.exists():
                continue

            cmd = [
                sys.executable,
                "-m",
                "pytest",
                str(test_file),
                "--quiet",
                "--no-header",
                "--tb=short",
                "-v",
            ]

            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, cwd=self.project_root
                )

                output = result.stdout + result.stderr

                # Count results
                for line in output.split("\n"):
                    if " PASSED" in line:
                        total_passed += 1
                        total_run += 1
                    elif " FAILED" in line:
                        self.results["failed_tests"] += 1
                        total_run += 1
                    elif " ERROR" in line:
                        self.results["error_tests"] += 1
                        total_run += 1
                    elif " SKIPPED" in line:
                        self.results["skipped_tests"] += 1

            except Exception as e:
                print(f"  ❌ Failed to run {test_file}: {e}")

        self.results["passed_tests"] = total_passed
        self.results["execution_time"] = (datetime.now() - start_time).total_seconds()

        if total_run > 0:
            self.results["stability_rate"] = (total_passed / total_run) * 100

        print(f"  ✓ Ran {total_run} tests")
        print(f"  ✓ Passed: {total_passed}")
        print(f"  ✗ Failed: {self.results['failed_tests']}")
        print(f"  ✗ Errors: {self.results['error_tests']}")

    def analyze_error_patterns(self)print("\n🔬 Analyzing error patterns...")
    """Analyze common error patterns"""

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "--quiet",
            "--tb=short",
        ]

        env = os.environ.copy()
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                env=env if "env" in locals() else None,
            )

            output = result.stderr

            # Count error types
            error_patterns = {
                "ImportError": 0,
                "ModuleNotFoundError": 0,
                "AttributeError": 0,
                "SyntaxError": 0,
                "IndentationError": 0,
                "NameError": 0,
                "Other": 0,
            }

            # 繰り返し処理
            for line in output.split("\n"):
                for error_type in error_patterns:
                    if error_type in line:
                        error_patterns[error_type] += 1
                        break
                else:
                    if "Error" in line:
                        error_patterns["Other"] += 1

            self.results["error_types"] = {
                k: v for k, v in error_patterns.items() if v > 0
            }

            for error_type, count in self.results["error_types"].items():
                print(f"  • {error_type}: {count}")

        except Exception as e:
            print(f"  ❌ Analysis failed: {e}")

    def generate_report(self)print("\n📊 TEST INFRASTRUCTURE STABILITY REPORT")
    """Generate stability report"""
        print("=" * 50)

        # Calculate overall stability
        if self.results["collection_errors"] == 0:
            collection_stability = 100.0
        elif self.results["collection_errors"] == -1:
            collection_stability = 0.0
        else:
            collection_stability = max(0, 100 - (self.results["collection_errors"] * 2))

        overall_stability = (collection_stability + self.results["stability_rate"]) / 2

        print(f"\n🎯 Overall Stability: {overall_stability:0.1f}%")
        print(f"  • Collection Stability: {collection_stability:0.1f}%")
        print(f"  • Execution Stability: {self.results['stability_rate']:0.1f}%")

        print("\n📈 Metrics:")
        print(f"  • Total Tests Collected: {self.results['total_tests']}")
        print(f"  • Collection Errors: {self.results['collection_errors']}")
        print(
            f"  • Tests Run: {self.results['passed_tests'] + self.results['failed_tests'] +  \
                self.results['error_tests']}"
        )
        print(f"  • Tests Passed: {self.results['passed_tests']}")
        print(f"  • Tests Failed: {self.results['failed_tests']}")
        print(f"  • Tests with Errors: {self.results['error_tests']}")
        print(f"  • Execution Time: {self.results['execution_time']:0.2f}s")

        if self.results["error_types"]:
            print("\n🐛 Error Distribution:")
            for error_type, count in sorted(
                self.results["error_types"].items(), key=lambda x: x[1], reverse=True
            ):
                print(f"  • {error_type}: {count}")

        # Success criteria
        print("\n✅ Success Criteria:")
        print(
            f"  • Collection errors: {'✓ PASS' if self.results['collection_errors'] == 0 else '✗ FAIL'} (target: 0)"
        )
        print(
            f"  • Test stability: {'✓ PASS' if self.results['stability_rate'] >= 95 else '✗ FAIL'} (target: 95%+)"
        )

        # Save report
        report_path = self.project_root / "test_stability_report.json"
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Report saved to: {report_path}")

        return overall_stability >= 95


if __name__ == "__main__":
    measurer = TestStabilityMeasurer()

    measurer.run_pytest_collection()
    measurer.run_sample_tests()
    measurer.analyze_error_patterns()

    success = measurer.generate_report()

    if success:
        print("\n🎉 Test infrastructure is stable!")
    else:
        print("\n⚠️ Test infrastructure needs improvement.")

    sys.exit(0 if success else 1)
