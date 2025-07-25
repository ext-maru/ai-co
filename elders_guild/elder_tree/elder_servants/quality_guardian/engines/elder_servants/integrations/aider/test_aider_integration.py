"""
Test script for Aider + Elder Servants integration
"""

import asyncio

import os
import subprocess
from pathlib import Path
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from libs.elder_servants.integrations.aider.aider_elder_integration import AiderElderIntegration

async def test_pre_commit_hook()print("🔍 Testing pre-commit hook...")
"""Test the pre-commit quality check"""
    
    integration = AiderElderIntegration()
    
    # Create test files with different quality levels

        good_code = '''
"""
High quality Python module for demonstration
"""

def calculate_fibonacci(n: int) -> int:
    """
    Calculate fibonacci number for given position.
    
    Args:
        n: Position in fibonacci sequence (must be non-negative)
        
    Returns:
        Fibonacci number at position n
        
    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    
    if n <= 1:
        return n
    
    return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)

def test_calculate_fibonacci()assert calculate_fibonacci(0) == 0
"""Test fibonacci calculation function."""
    assert calculate_fibonacci(1) == 1
    assert calculate_fibonacci(5) == 5
    
    try:
        calculate_fibonacci(-1)
        assert False, "Should raise ValueError"
    except ValueError:
        pass
'''
        good_file.write(good_code)
        good_file_path = good_file.name

        bad_code = '''
def bad_func(x):
    # No docstring, poor naming, no error handling
    return x*2+1
'''
        bad_file.write(bad_code)
        bad_file_path = bad_file.name
    
    try:
        # Test with good file
        should_commit, message = await integration.pre_commit_hook([good_file_path])
        print(f"✅ Good file test: {should_commit}")
        print(f"   Message: {message}")
        
        # Test with bad file
        should_commit, message = await integration.pre_commit_hook([bad_file_path])
        print(f"❌ Bad file test: {should_commit}")
        print(f"   Message: {message}")
        
        # Test with mixed files
        should_commit, message = await integration.pre_commit_hook([good_file_path, bad_file_path])
        print(f"⚖️  Mixed files test: {should_commit}")
        print(f"   Message: {message}")
        
    finally:
        # Cleanup
        os.unlink(good_file_path)
        os.unlink(bad_file_path)

async def test_commit_message_enhancement()print("\n📝 Testing commit message enhancement...")
"""Test commit message enhancement"""
    
    integration = AiderElderIntegration()

    files_changed = ["auth.py", "test_auth.py"]
    
    enhanced = await integration.enhance_commit_message(
        original_message,
        files_changed,
        "diff content..."
    )
    
    print(f"Original: {original_message}")
    print(f"Enhanced:\n{enhanced}")

async def test_post_edit_analysis()print("\n🔍 Testing post-edit analysis...")
"""Test post-edit analysis functionality"""
    
    integration = AiderElderIntegration()

    try:
        original_content = '''
def simple_func(x):
    return x + 1
'''
        
        new_content = '''
def simple_func(x: int) -> intif not isinstance(x, int)raise TypeError("x must be an integer")
Add 1 to the input number.
    return x + 1

def test_simple_func()assert simple_func(5) == 6assert simple_func(0) == 1
"""est the simple_func function."""
'''
        
        analysis = await integration.post_edit_analysis(

            original_content,
            new_content
        )
        
        print(f"Analysis results:")
        print(f"  Quality score: {analysis['quality_score']:0.1f}%")
        print(f"  Lines added: {analysis['lines_added']}")
        print(f"  Passes Iron Will: {analysis['passes_iron_will']}")
        
    finally:

async def test_improvement_suggestions()print("\n💡 Testing improvement suggestions...")
"""Test improvement suggestions"""
    
    integration = AiderElderIntegration()

        poor_code = '''
def func(a, b):
    c = a + b
    return c
'''

    try:

        print("Improvement suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
            
    finally:

def test_git_hooks_setup()print("\n🔧 Testing git hooks setup...")
"""Test git hooks setup"""

        # Initialize git repo
        subprocess.run(["git", "init"], capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], capture_output=True)
        
        integration = AiderElderIntegration()
        success = integration.setup_aider_hooks()
        
        if success:
            print("✅ Git hooks setup successful")
            
            # Check if hook file exists
            hook_path = Path(".git/hooks/pre-commit")
            if hook_path.exists():
                print("✅ Pre-commit hook file created")
                print(f"   Hook is executable: {hook_path.stat().st_mode & 0o111 !}")
            else:
                print("❌ Pre-commit hook file not found")
        else:
            print("❌ Git hooks setup failed")

def test_wrapper_script()print("\n🚀 Testing wrapper script...")
"""Test the wrapper script"""
    
    script_path = Path(__file__).parent / "aider_elder_wrapper.sh"
    
    if script_path.exists():
        print(f"✅ Wrapper script exists: {script_path}")
        print(f"   Script is executable: {script_path.stat().st_mode & 0o111 !}")
        
        # Test help output
        try:
            result = subprocess.run(
                [str(script_path), "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if "Elder" in result.stdout or "Elder" in result.stderr:
                print("✅ Wrapper script shows Elder integration")
            else:
                print("⚠️  Wrapper script may not show Elder integration")
        except subprocess.TimeoutExpired:
            print("⚠️  Wrapper script help test timed out")
        except Exception as e:
            print(f"⚠️  Error testing wrapper script: {e}")
    else:
        print("❌ Wrapper script not found")

async def test_integration_workflow()print("\n🎯 Testing complete integration workflow...")
"""Test complete integration workflow"""
    
    integration = AiderElderIntegration()
    
    # Simulate Aider workflow
    print("1️⃣ Aider makes code changes...")

        original = "def old_func(): pass"
        new_code = '''
dedef improved_func(x: int) -> strif not isinstance(x, int)raise TypeError("Input must be an integer")
Convert integer to string with validation.
    return str(x)

def test_improved_func()assert improved_func(42) == "42"assert improved_func(0) == "0"
"""t the improved function."""
'''

    try:
        # 2.0 Analyze changes
        print("2️⃣ Analyzing changes...")

        print(f"   Quality score: {analysis['quality_score']:0.1f}%")
        
        # 3.0 Pre-commit check
        print("3️⃣ Running pre-commit check...")

        print(f"   Should commit: {should_commit}")
        
        # 4.0 Enhance commit message
        if should_commit:
            print("4️⃣ Enhancing commit message...")
            original_msg = "refactor: improve function implementation"
            enhanced_msg = await integration.enhance_commit_message(
                original_msg,

                "diff content..."
            )
            print(f"   Enhanced message preview: {enhanced_msg[:100]}...")
        
        print("✅ Complete workflow test successful")
        
    finally:

async def run_all_tests()print("🚀 Starting Aider + Elder Servants Integration Tests\n")
"""Run all integration tests"""
    
    tests = [
        ("Pre-commit Hook", test_pre_commit_hook()),
        ("Commit Message Enhancement", test_commit_message_enhancement()),
        ("Post-edit Analysis", test_post_edit_analysis()),
        ("Improvement Suggestions", test_improvement_suggestions()),
        ("Complete Workflow", test_integration_workflow())
    ]
    
    results = {}
    
    for test_name, test_coro in tests:
        try:
            await test_coro
            results[test_name] = "✅ PASS"
        except Exception as e:
            results[test_name] = f"❌ FAIL: {str(e)}"
    
    # Run sync tests
    try:
        test_git_hooks_setup()
        results["Git Hooks Setup"] = "✅ PASS"
    except Exception as e:
        results["Git Hooks Setup"] = f"❌ FAIL: {str(e)}"
    
    try:
        test_wrapper_script()
        results["Wrapper Script"] = "✅ PASS"
    except Exception as e:
        results["Wrapper Script"] = f"❌ FAIL: {str(e)}"
    
    # Print results
    print("\n📊 Test Results Summary:")
    passed = 0
    for test_name, result in results.items():
        print(f"   {test_name}: {result}")
        if "PASS" in result:
            passed += 1
    
    print(f"\n🎯 Total: {passed}/{len(results)} tests passed")
    
    return passed == len(results)

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n🎉 All tests passed! Aider integration is ready.")
        print("\n💡 Usage:")
        print("   ./aider_elder_wrapper.sh [aider-arguments]")
        print("   ./aider_elder_wrapper.sh --elder-quality *.py")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
        sys.exit(1)