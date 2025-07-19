#!/usr/bin/env python3
"""
Simple Aider Integration Test
Basic test to verify Aider can work with Elder Servants
"""

import os
import shutil
import subprocess
import tempfile


def test_aider_simple():
    """Simple Aider functionality test"""
    print("🚀 Testing Aider Integration with Elder System")

    # Get correct aider path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    aider_path = os.path.join(base_dir, "venv_continue_dev/bin/aider")

    print(f"📍 Aider path: {aider_path}")
    print(f"📁 Aider exists: {os.path.exists(aider_path)}")

    if not os.path.exists(aider_path):
        print("❌ Aider not found")
        return False

    # Test 1: Basic help
    try:
        result = subprocess.run(
            [aider_path, "--help"], capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print("✅ Test 1: Aider help works")
        else:
            print(f"❌ Test 1: Aider help failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Test 1: Error running aider help: {e}")
        return False

    # Test 2: Version check
    try:
        result = subprocess.run(
            [aider_path, "--version"], capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print(f"✅ Test 2: Aider version: {result.stdout.strip()}")
        else:
            print(f"❌ Test 2: Version check failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Test 2: Error checking version: {e}")
        return False

    # Test 3: Create test environment
    test_dir = tempfile.mkdtemp(prefix="aider_simple_test_")
    print(f"📁 Test directory: {test_dir}")

    try:
        # Create simple test file
        test_file = os.path.join(test_dir, "test.py")
        with open(test_file, "w") as f:
            f.write(
                """def hello():
    return "Hello World"
"""
            )

        # Initialize git
        subprocess.run(["git", "init"], cwd=test_dir, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=test_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"], cwd=test_dir, capture_output=True
        )

        # Test aider with simple request (non-interactive)
        env = os.environ.copy()
        env["AIDER_NO_AUTO_COMMITS"] = "1"

        result = subprocess.run(
            [
                aider_path,
                "--yes",
                "--message",
                "Add a docstring to the hello function",
                "test.py",
            ],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )

        if result.returncode == 0:
            # Check if file was modified
            with open(test_file, "r") as f:
                content = f.read()
            if '"""' in content or "'''" in content:
                print("✅ Test 3: Aider successfully modified code")
            else:
                print("❌ Test 3: Aider ran but didn't add docstring")
                return False
        else:
            print(f"❌ Test 3: Aider modification failed: {result.stderr}")
            print(f"stdout: {result.stdout}")
            return False

    except Exception as e:
        print(f"❌ Test 3: Error in modification test: {e}")
        return False
    finally:
        # Cleanup
        shutil.rmtree(test_dir)
        print(f"🧹 Cleaned up: {test_dir}")

    print("🎉 All Aider tests passed! Integration ready.")
    return True


if __name__ == "__main__":
    success = test_aider_simple()
    exit(0 if success else 1)
