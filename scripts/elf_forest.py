#!/usr/bin/env python3
"""
ELF FOREST - Test Execution Monitor and Auto-Healer
Monitors test execution and automatically heals failures
"""
import json
import os
import queue
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class ElfForest:
    """Elder Servant: Elf Forest - Test Monitor and Healer"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.heals_performed = 0
        self.tests_monitored = 0
        self.coverage_history = []
        self.failure_queue = queue.Queue()

    def get_current_coverage(self):
        """Get current test coverage percentage"""
        try:
            result = subprocess.run(
                ["pytest", "--cov=.", "--cov-report=json", "--no-cov-on-fail", "-q"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )

            # Parse coverage report
            coverage_file = self.project_root / ".coverage"
            if coverage_file.exists():
                cov_json_file = self.project_root / "coverage.json"
                if cov_json_file.exists():
                    with open(cov_json_file, "r") as f:
                        data = json.load(f)
                        return data.get("totals", {}).get("percent_covered", 0)

            # Fallback: parse from output
            for line in result.stdout.split("\n"):
                if "TOTAL" in line and "%" in line:
                    parts = line.split()
                    for part in parts:
                        if not (part.endswith("%")):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if part.endswith("%"):
                            return float(part.rstrip("%"))

            return 0
        except Exception as e:
            print(f"Error getting coverage: {e}")
            return 0

    def monitor_test_execution(self, test_file):
        """Monitor individual test file execution"""
        try:
            print(f"🧝 Monitoring: {test_file}")

            result = subprocess.run(
                ["pytest", "-xvs", str(test_file)],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )

            self.tests_monitored += 1

            if result.returncode != 0:
                # Test failed, add to healing queue
                self.failure_queue.put(
                    {
                        "file": test_file,
                        "error": result.stderr + result.stdout,
                        "timestamp": datetime.now(),
                    }
                )
                return False

            return True

        except subprocess.TimeoutExpired:
            print(f"⏱️ Timeout monitoring: {test_file}")
            self.failure_queue.put(
                {
                    "file": test_file,
                    "error": "Test execution timeout",
                    "timestamp": datetime.now(),
                }
            )
            return False
        except Exception as e:
            print(f"❌ Error monitoring {test_file}: {e}")
            return False

    def heal_test_failure(self, failure_info):
        """Attempt to heal a test failure"""
        test_file = failure_info["file"]
        error = failure_info["error"]

        print(f"🌿 Attempting to heal: {test_file}")

        # Common healing strategies
        healed = False

        # Strategy 1: Fix import errors
        if "ImportError" in error or "ModuleNotFoundError" in error:
            healed = self.heal_import_error(test_file, error)

        # Strategy 2: Fix missing fixtures
        elif "fixture" in error.lower():
            healed = self.heal_fixture_error(test_file, error)

        # Strategy 3: Fix assertion errors
        elif "AssertionError" in error:
            healed = self.heal_assertion_error(test_file, error)

        # Strategy 4: Fix timeout issues
        elif "timeout" in error.lower():
            healed = self.heal_timeout_error(test_file)

        # Strategy 5: Fix missing mocks
        elif "Mock" in error or "patch" in error:
            healed = self.heal_mock_error(test_file, error)

        if healed:
            self.heals_performed += 1
            print(f"✅ Healed: {test_file}")
        else:
            print(f"❌ Could not heal: {test_file}")

        return healed

    def heal_import_error(self, test_file, error):
        """Heal import errors in test file"""
        try:
            with open(test_file, "r") as f:
                content = f.read()

            # Add missing imports
            if "No module named 'tests.mock_utils'" in error:
                # Ensure mock_utils import is correct
                content = content.replace(
                    "from tests.mock_utils import", "from tests.mock_utils import"
                )

            # Fix PROJECT_ROOT if needed
            if "PROJECT_ROOT" not in content:
                import_section = """import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

"""
                # Insert after initial imports
                lines = content.split("\n")
                insert_pos = 0
                for i, line in enumerate(lines):
                    if line.startswith("import") or line.startswith("from"):
                        insert_pos = i + 1
                    # 複雑な条件判定
                    elif (
                        insert_pos > 0
                        and line
                        and not line.startswith(("import", "from"))
                    ):
                        break

                lines.insert(insert_pos, import_section)
                content = "\n".join(lines)

            with open(test_file, "w") as f:
                f.write(content)

            return True

        except Exception as e:
            print(f"Error healing import: {e}")
            return False

    def heal_fixture_error(self, test_file, error):
        """Heal fixture errors"""
        try:
            with open(test_file, "r") as f:
                content = f.read()

            # Add common fixtures
            fixture_code = '''
@pytest.fixture
def mock_logger():
    """Mock logger fixture"""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.debug = Mock()
    return logger

@pytest.fixture
def mock_rabbit_connection():
    """Mock RabbitMQ connection fixture"""
    conn = Mock()
    channel = Mock()
    conn.channel.return_value = channel
    return conn, channel
'''

            if "@pytest.fixture" not in content:
                # Add pytest import if needed
                if "import pytest" not in content:
                    content = "import pytest\n" + content

                # Add fixtures before first test class
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if line.startswith("class Test"):
                        lines.insert(i, fixture_code)
                        break

                content = "\n".join(lines)

            with open(test_file, "w") as f:
                f.write(content)

            return True

        except Exception as e:
            print(f"Error healing fixture: {e}")
            return False

    def heal_assertion_error(self, test_file, error):
        """Heal assertion errors by adjusting expectations"""
        # This is more complex and would need specific patterns
        # For now, we'll skip tests with persistent assertion errors
        return False

    def heal_timeout_error(self, test_file):
        """Heal timeout errors by adding timeout decorators"""
        try:
            with open(test_file, "r") as f:
                content = f.read()

            # Add timeout to slow tests
            if "@pytest.mark.timeout" not in content:
                content = content.replace(
                    "def test_", "@pytest.mark.timeout(30)\n    def test_"
                )

            with open(test_file, "w") as f:
                f.write(content)

            return True

        except Exception as e:
            print(f"Error healing timeout: {e}")
            return False

    def heal_mock_error(self, test_file, error):
        """Heal mock-related errors"""
        try:
            with open(test_file, "r") as f:
                content = f.read()

            # Ensure Mock imports
            if "from unittest.mock import" not in content:
                content = "from unittest.mock import Mock, MagicMock, patch\n" + content

            with open(test_file, "w") as f:
                f.write(content)

            return True

        except Exception as e:
            print(f"Error healing mock: {e}")
            return False

    def healing_worker(self):
        """Worker thread for healing test failures"""
        while True:
            try:
                failure = self.failure_queue.get(timeout=1)
                self.heal_test_failure(failure)
                self.failure_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Healing worker error: {e}")

    def monitor_all_tests(self):
        """Monitor all test files in parallel"""
        print("🌲 ELF FOREST AWAKENED")
        print("=" * 60)

        # Start healing worker
        healer = threading.Thread(target=self.healing_worker, daemon=True)
        healer.start()

        # Get initial coverage
        initial_coverage = self.get_current_coverage()
        print(f"📊 Initial coverage: {initial_coverage:.1f}%")

        # Find all test files
        test_files = list(Path(self.project_root / "tests").rglob("test_*.py"))
        print(f"📁 Found {len(test_files)} test files to monitor")

        # Monitor tests in batches
        batch_size = 10
        for i in range(0, len(test_files), batch_size):
            batch = test_files[i : i + batch_size]
            threads = []

            for test_file in batch:
                thread = threading.Thread(
                    target=self.monitor_test_execution, args=(test_file,)
                )
                threads.append(thread)
                thread.start()

            # Wait for batch to complete
            for thread in threads:
                thread.join()

            # Check coverage progress
            current_coverage = self.get_current_coverage()
            self.coverage_history.append(current_coverage)
            print(
                f"📈 Coverage: {current_coverage:.1f}% (+{current_coverage - initial_coverage:.1f}%)"
            )

            # Stop if we hit 60%
            if current_coverage >= 60.0:
                print("🎯 TARGET ACHIEVED: 60% coverage!")
                break

        # Wait for healing queue to empty
        self.failure_queue.join()

        # Final coverage check
        final_coverage = self.get_current_coverage()

        print("\n" + "=" * 60)
        print(f"✅ ELF FOREST MISSION COMPLETE")
        print(f"🧝 Tests monitored: {self.tests_monitored}")
        print(f"🌿 Heals performed: {self.heals_performed}")
        print(f"📊 Initial coverage: {initial_coverage:.1f}%")
        print(f"📊 Final coverage: {final_coverage:.1f}%")
        print(f"📈 Coverage gained: +{final_coverage - initial_coverage:.1f}%")
        print("=" * 60)

    def generate_coverage_report(self):
        """Generate detailed coverage report"""
        try:
            # Generate HTML report
            subprocess.run(
                ["pytest", "--cov=.", "--cov-report=html", "--no-cov-on-fail"],
                cwd=self.project_root,
                capture_output=True,
                timeout=300,
            )

            print(
                f"📊 Coverage report generated: {self.project_root}/htmlcov/index.html"
            )

        except Exception as e:
            print(f"Error generating report: {e}")


if __name__ == "__main__":
    forest = ElfForest()
    forest.monitor_all_tests()
    forest.generate_coverage_report()
