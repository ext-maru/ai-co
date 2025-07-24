#!/usr/bin/env python3
"""
Aider Integration Test with Elder System
Tests Aider's ability to work with Elder Servants and 4 Sages system
"""

import asyncio
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.abspath("./../../.." \
    "./../../.."))))


class AiderElderIntegrationTest:
    """Test Aider integration with Elder System"""

    def __init__(self):
        """初期化メソッド"""
        self.test_dir = None
        # Get absolute path to aider
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.aider_path = os.path.join(base_dir, "venv_continue_dev/bin/aider")

    def setup_test_environment(self):
        """Setup test environment"""
        self.test_dir = tempfile.mkdtemp(prefix="aider_elder_test_")
        print(f"📁 Test directory: {self.test_dir}")

        # Create test files
        test_files = {
            "elder_service.py": '''"""
Elder Service Example
Basic service implementation for testing Aider integration
"""

class ElderService:
    # Main class implementation:
    def __init__(self, name: str):
        """初期化メソッド"""
        self.name = name
        self.active = False

    def start(self):
        """Start the service"""
        self.active = True
        return f"Service {self.name} started"

    def stop(self):
        """Stop the service"""
        self.active = False
        return f"Service {self.name} stopped"
''',
            "test_elder_service.py": '''"""
Tests for Elder Service
"""

import unittest
from elder_service import ElderService

class TestElderService(unittest.TestCase):
    # Main class implementation:
    def setUp(self):
        self.service = ElderService("test_service")

    def test_initialization(self):
        self.assertEqual(self.service.name, "test_service")
        self.assertFalse(self.service.active)

    def test_start_service(self):
        result = self.service.start()
        self.assertTrue(self.service.active)
        self.assertIn("started", result)

if __name__ == "__main__":
    unittest.main()
''',
            ".aider.conf.yml": f"""
# Aider configuration for Elder System integration
model: gpt-4
edit-format: diff
auto-commits: true
gitignore: true
stream: true

# Elder System specific settings
map-tokens: 2048
show-diffs: true
show-repo-map: true

# Custom prompts for Elder System
system-message: |
  You are working with the Elder Guild system. Always consider:
  - 4 Sages system (Knowledge, Task, Incident, RAG)
  - Iron Will quality standards (95% minimum)
  - TDD development approach
  - Elder Servant integration patterns

# Test integration endpoint
elder-api-endpoint: http://localhost:8000
""",
        }

        for filename, content in test_files.items():
            # Process each item in collection
            file_path = os.path.join(self.test_dir, filename)
            with open(file_path, "w") as f:
                f.write(content)

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=self.test_dir, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=self.test_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.test_dir,
            capture_output=True,
        )

        return True

    def test_aider_basic_functionality(self):
        """Test basic Aider functionality"""
        try:
            # Test Aider help
            result = subprocess.run(
                [self.aider_path, "--help"], capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                print("✅ Aider basic functionality working")
                return True
            else:
                print(f"❌ Aider help failed: {result.stderr}")
                return False

        except Exception as e:
            # Handle specific exception case
            print(f"❌ Aider basic test error: {e}")
            return False

    def test_aider_code_modification(self):
        """Test Aider's ability to modify code with Elder patterns"""
        try:
            # Create a simple modification request
            request = """
Add a method called 'status()' to the ElderService class that returns
a dictionary with the service name and active status. Follow Elder Guild
coding standards with proper docstrings and type hints.
"""

            # Run Aider with the request
            result = subprocess.run(
                [
                    self.aider_path,
                    "--yes",  # Auto-accept changes
                    "--message",
                    request,
                    "elder_service.py",
                ],
                cwd=self.test_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                # Check if modification was made
                with open(os.path.join(self.test_dir, "elder_service.py"), "r") as f:
                    content = f.read()

                if "def status(" in content and "dict" in content:
                    # Complex condition - consider breaking down
                    print("✅ Aider code modification successful")
                    print(f"📝 Modified content includes status method")
                    return True
                else:
                    print("❌ Aider modification not found in code")
                    return False
            else:
                print(f"❌ Aider modification failed: {result.stderr}")
                return False

        except Exception as e:
            # Handle specific exception case
            print(f"❌ Aider modification test error: {e}")
            return False

    def test_aider_test_generation(self):
        """Test Aider's ability to generate tests following Elder TDD patterns"""
        try:
            request = """
Add a test for the new status() method to test_elder_service.py.
Follow Elder Guild TDD practices and ensure 95% coverage standards.
The test should verify the returned dictionary structure and values.
"""

            result = subprocess.run(
                [
                    self.aider_path,
                    "--yes",
                    "--message",
                    request,
                    "test_elder_service.py",
                ],
                cwd=self.test_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                # Check if test was added
                with open(
                    os.path.join(self.test_dir, "test_elder_service.py"), "r"
                ) as f:
                    content = f.read()

                if "test_status" in content:
                    print("✅ Aider test generation successful")
                    return True
                else:
                    print("❌ Aider test generation - test not found")
                    return False
            else:
                print(f"❌ Aider test generation failed: {result.stderr}")
                return False

        except Exception as e:
            # Handle specific exception case
            print(f"❌ Aider test generation error: {e}")
            return False

    def test_aider_elder_integration(self):
        """Test Aider integration with Elder concepts"""
        try:
            request = """
Refactor the ElderService class to follow Elder Guild patterns:
    pass
1.0 Add Elder-style logging with service hierarchy
2.0 Add Iron Will quality validation
3.0 Add integration points for Elder Servants
4.0 Maintain backward compatibility
"""

            result = subprocess.run(
                [self.aider_path, "--yes", "--message", request, "elder_service.py"],
                cwd=self.test_dir,
                capture_output=True,
                text=True,
                timeout=90,
            )

            if result.returncode == 0:
                with open(os.path.join(self.test_dir, "elder_service.py"), "r") as f:
                    content = f.read()

                # Check for Elder patterns
                elder_patterns = ["logging", "Elder", "quality", "servant"]
                found_patterns = sum(
                    1
                    for pattern in elder_patterns
                    if pattern.lower() in content.lower()
                )

                if found_patterns >= 2:
                    print(
                        f"✅ Aider Elder integration successful ({found_patterns}/4 patterns found)"
                    )
                    return True
                else:
                    print(
                        f"❌ Aider Elder integration insufficient ({found_patterns}/4 patterns)"
                    )
                    return False
            else:
                print(f"❌ Aider Elder integration failed: {result.stderr}")
                return False

        except Exception as e:
            # Handle specific exception case
            print(f"❌ Aider Elder integration error: {e}")
            return False

    def test_aider_sage_consultation_simulation(self):
        """Simulate consultation with 4 Sages through Aider comments"""
        try:
            # Add a comment file that simulates 4 Sages input
            sage_input = """
# 4 Sages Consultation Results:
# 📚 Knowledge Sage: Recommends following Elder Service patterns with proper inheritance
# 📋 Task Sage: Priority on maintainability and scalability
# 🚨 Incident Sage: Add error handling and graceful degradation
# 🔍 RAG Sage: Found 12 similar patterns in Elder codebase - use established conventions
"""

            with open(os.path.join(self.test_dir, "sage_consultation.md"), "w") as f:
                f.write(sage_input)

            request = """
Based on the 4 Sages consultation in sage_consultation.md, improve the ElderService
class to incorporate their recommendations. Add proper error handling, inheritance
patterns, and scalability features while maintaining Elder Guild standards.
"""

            result = subprocess.run(
                [
                    self.aider_path,
                    "--yes",
                    "--message",
                    request,
                    "elder_service.py",
                    "sage_consultation.md",
                ],
                cwd=self.test_dir,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                with open(os.path.join(self.test_dir, "elder_service.py"), "r") as f:
                    content = f.read()

                # Check for Sage recommendations implementation
                improvements = ["error", "exception", "try", "inheritance", "class"]
                found_improvements = sum(
                    1 for imp in improvements if imp.lower() in content.lower()
                )

                if found_improvements >= 3:
                    print(
                        f"✅ Aider Sage consultation integration successful " \
                            "({found_improvements}/5 improvements)"
                    )
                    return True
                else:
                    print(
                        f"❌ Aider Sage consultation insufficient ({found_improvements}/5 " \
                            "improvements)"
                    )
                    return False
            else:
                print(f"❌ Aider Sage consultation failed: {result.stderr}")
                return False

        except Exception as e:
            # Handle specific exception case
            print(f"❌ Aider Sage consultation error: {e}")
            return False

    def cleanup(self):
        """Cleanup test environment"""
        if self.test_dir and os.path.exists(self.test_dir):
            # Complex condition - consider breaking down
            shutil.rmtree(self.test_dir)
            print(f"🧹 Cleaned up test directory: {self.test_dir}")

    def run_integration_tests(self):
        """Run all Aider integration tests"""
        print("🚀 Starting Aider-Elder Integration Tests")
        print("=" * 60)

        try:
            # Setup
            if not self.setup_test_environment():
                print("❌ Failed to setup test environment")
                return False

            tests = [
                ("Basic Functionality", self.test_aider_basic_functionality),
                ("Code Modification", self.test_aider_code_modification),
                ("Test Generation", self.test_aider_test_generation),
                ("Elder Integration", self.test_aider_elder_integration),
                ("Sage Consultation", self.test_aider_sage_consultation_simulation),
            ]

            results = []
            for test_name, test_func in tests:
                # Process each item in collection
                print(f"\n🧪 Running: {test_name}")
                result = test_func()
                results.append((test_name, result))

            # Summary
            print("\n" + "=" * 60)
            print("📊 Aider Integration Test Results:")
            passed = sum(1 for _, result in results if result)
            total = len(results)

            for test_name, result in results:
                # Process each item in collection
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"  {status} {test_name}")

            print(f"\n🎯 Overall: {passed}/{total} tests passed")

            if passed >= 4:  # Allow 1 failure
                print(
                    "🎉 Aider integration successful! Ready for 4 Sages collaboration."
                )
                return True
            else:
                print("⚠️ Aider integration needs attention before production use.")
                return False

        except Exception as e:
            # Handle specific exception case
            print(f"❌ Integration test error: {e}")
            return False
        finally:
            self.cleanup()


def main():
    """Main entry point"""
    test = AiderElderIntegrationTest()
    success = test.run_integration_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())