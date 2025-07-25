"""
Comprehensive integration tests for Aider + GitKeeperServant
Testing Issue #81: Continue.dev Integration Phase 2 - Aider Integration Tests
"""

import asyncio
import os
import subprocess
import sys

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from libs.elder_flow_servant_executor_real import GitKeeperServantReal
from libs.elder_servants.integrations.aider.aider_elder_integration import (
    AiderElderIntegration,
)

class TestAiderGitKeeperIntegration:
    """Test suite for Aider + GitKeeperServant integration"""

    @pytest.fixture
    async def git_keeper(self):
        """Create GitKeeperServant instance"""
        return GitKeeperServantReal()

    @pytest.fixture
    async def aider_integration(self):
        """Create AiderElderIntegration instance"""
        return AiderElderIntegration()

    @pytest.fixture

            # Initialize git repo
            subprocess.run(["git", "init"], capture_output=True, check=True)
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                capture_output=True,
                check=True,
            )

            # Create initial commit
            Path("README.md").write_text("# Test Project\n")
            subprocess.run(["git", "add", "README.md"], capture_output=True, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial commit"],
                capture_output=True,
                check=True,
            )

            # Reset working directory
            os.chdir("/")

    @pytest.mark.asyncio

        """Test basic GitKeeperServant operations"""
        # Test git status
        result = await git_keeper.git_status()
        assert result["success"] is True
        assert "status" in result

        # Create a new file
        test_file = Path("test.py")
        test_file.write_text("def hello():\n    return 'world'\n")

        # Test git add
        result = await git_keeper.git_add(["test.py"])
        assert result["success"] is True

        # Test git status after add
        result = await git_keeper.git_status()
        assert result["success"] is True
        assert "test.py" in result["status"]

        # Test git commit
        result = await git_keeper.git_commit("test: add test file")
        assert result["success"] is True
        assert "commit_hash" in result

        # Test git log
        result = await git_keeper.git_log(limit=5)
        assert result["success"] is True
        assert len(result["commits"]) >= 2  # Initial + new commit

    @pytest.mark.asyncio
    async def test_aider_integration_with_git_keeper(

    ):
        """Test Aider integration using GitKeeperServant"""
        # Create test file
        test_file = Path("calculator.py")
        test_file.write_text(
            """
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
"""
        )

        # Stage file
        await git_keeper.git_add(["calculator.py"])

        # Test pre-commit hook
        should_commit, message = await aider_integration.pre_commit_hook(
            ["calculator.py"]
        )
        assert should_commit is False  # No tests, should fail Iron Will
        assert "Iron Will" in message or "test" in message.lower()

        # Add tests to pass Iron Will
        test_file.write_text(
            """
def add(a, b):
    \"\"\"Add two numbers together.\"\"\"
    return a + b

def multiply(a, b):
    \"\"\"Multiply two numbers.\"\"\"
    return a * b

def test_add():
    \"\"\"Test addition function.\"\"\"
    assert add(2, 3) == 5
    assert add(-1, 1) == 0

def test_multiply():
    \"\"\"Test multiplication function.\"\"\"
    assert multiply(3, 4) == 12
    assert multiply(0, 5) == 0
"""
        )

        # Test again with tests
        should_commit, message = await aider_integration.pre_commit_hook(
            ["calculator.py"]
        )
        assert should_commit is True
        assert "quality" in message.lower() or "pass" in message.lower()

    @pytest.mark.asyncio
    async def test_auto_commit_workflow(

    ):
        """Test automatic commit workflow"""
        # Create high-quality file
        quality_file = Path("math_utils.py")
        quality_file.write_text(
            '''
"""
Mathematical utility functions with comprehensive testing.
"""

def factorial(n: int) -> int:
    """
    Calculate factorial of a non-negative integer.

    Args:
        n: Non-negative integer

    Returns:
        Factorial of n

    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)

def test_factorial():
    """Test factorial function."""
    assert factorial(0) == 1
    assert factorial(1) == 1
    assert factorial(5) == 120

    try:
        factorial(-1)
        assert False, "Should raise ValueError"
    except ValueError:
        pass
'''
        )

        # Run automatic commit workflow
        result = await aider_integration.create_elder_commit(
            ["math_utils.py"], "feat: add factorial function with tests"
        )

        assert result["success"] is True
        assert "commit_hash" in result

        # Verify commit was created
        log_result = await git_keeper.git_log(limit=1)
        assert log_result["success"] is True
        assert len(log_result["commits"]) == 1

        # Check commit message was enhanced
        latest_commit = log_result["commits"][0]
        assert "factorial" in latest_commit["message"].lower()
        assert (
            "🤖" in latest_commit["message"]
            or "Generated with Claude" in latest_commit["message"]
        )

    @pytest.mark.asyncio
    async def test_diff_and_merge_functionality(

    ):
        """Test diff checking and merge functionality"""
        # Create initial file
        file_path = Path("merge_test.py")
        original_content = """
def greet(name):
    return f"Hello, {name}!"
"""
        file_path.write_text(original_content)

        # Commit initial version
        await git_keeper.git_add(["merge_test.py"])
        await git_keeper.git_commit("feat: add greet function")

        # Modify file (simulate Aider edit)
        new_content = """
def greet(name: str) -> str:
    \"\"\"
    Generate greeting message.

    Args:
        name: Person's name

    Returns:
        Greeting message
    \"\"\"
    if not name:
        return "Hello, Anonymous!"
    return f"Hello, {name}!"

def test_greet():
    \"\"\"Test greeting function.\"\"\"
    assert greet("Alice") == "Hello, Alice!"
    assert greet("") == "Hello, Anonymous!"
"""
        file_path.write_text(new_content)

        # Get diff
        diff_result = await git_keeper.git_diff(staged=False)
        assert diff_result["success"] is True
        assert "merge_test.py" in diff_result["diff"]

        # Analyze changes
        analysis = await aider_integration.post_edit_analysis(
            "merge_test.py", original_content, new_content
        )

        assert analysis["quality_score"] > 80  # Should be high quality
        assert analysis["lines_added"] > 10
        assert analysis["has_tests"] is True
        assert analysis["passes_iron_will"] is True

    @pytest.mark.asyncio

        """Test Aider CLI wrapper integration"""
        wrapper_path = (
            Path(__file__).parent.parent.parent
            / "libs/elder_servants/integrations/aider/aider_elder_wrapper.sh"
        )

        if not wrapper_path.exists():
            pytest.skip("Aider wrapper script not found")

        # Test wrapper help
        result = subprocess.run(
            [str(wrapper_path), "--help"], capture_output=True, text=True
        )

        assert (
            result.returncode == 0
            or "Elder" in result.stdout
            or "Elder" in result.stderr
        )

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(

    ):
        """Test error handling and recovery mechanisms"""
        # Test with non-existent file
        should_commit, message = await aider_integration.pre_commit_hook(
            ["non_existent.py"]
        )
        assert should_commit is False
        assert "error" in message.lower() or "not found" in message.lower()

        # Test with invalid Python file
        bad_file = Path("syntax_error.py")

        should_commit, message = await aider_integration.pre_commit_hook(
            ["syntax_error.py"]
        )
        assert should_commit is False
        assert "syntax" in message.lower() or "error" in message.lower()

        # Test recovery - fix the file
        bad_file.write_text(
            """
def fixed():
    \"\"\"Fixed function.\"\"\"
    pass

def test_fixed():
    \"\"\"Test the fixed function.\"\"\"
    fixed()  # Should not raise
"""
        )

        should_commit, message = await aider_integration.pre_commit_hook(
            ["syntax_error.py"]
        )
        assert should_commit is True

    @pytest.mark.asyncio
    async def test_performance_with_multiple_files(

    ):
        """Test performance with multiple files"""
        # Create multiple files
        files = []
        for i in range(10):
            file_path = Path(f"module_{i}.py")
            file_path.write_text(
                f'''
"""Module {i} implementation."""

def function_{i}(x: int) -> int:
    """Process input."""
    return x * {i + 1}

def test_function_{i}():
    """Test function_{i}."""
    assert function_{i}(5) == {5 * (i + 1)}
'''
            )
            files.append(f"module_{i}.py")

        # Test batch pre-commit check
        import time

        start_time = time.time()

        should_commit, message = await aider_integration.pre_commit_hook(files)

        elapsed_time = time.time() - start_time

        assert should_commit is True
        assert elapsed_time < 5.0  # Should complete within 5 seconds

        # Test batch commit
        result = await aider_integration.create_elder_commit(
            files, "feat: add multiple modules"
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_integration_with_continue_dev_phase1(
        self, aider_integration, git_keeper
    ):
        """Test compatibility with Continue.dev Phase 1 integration"""
        # This test verifies that Aider integration doesn't conflict with Continue.dev

        # Mock Continue.dev adapter
        with patch(
            "libs.elder_servants.integrations.continue_dev.elder_servant_adapter.ElderServantAdapter"
        ) as MockAdapter:
            mock_adapter = MockAdapter.return_value
            mock_adapter.execute_command = AsyncMock(return_value={"status": "success"})

            # Test that both integrations can coexist
            # Create a file that both might process
            test_file = Path("shared_file.py")
            test_file.write_text(
                """
def shared_function():
    \"\"\"Function used by both integrations.\"\"\"
    return "success"

def test_shared_function():
    \"\"\"Test the shared function.\"\"\"
    assert shared_function() == "success"
"""
            )

            try:
                # Aider pre-commit check
                aider_result = await aider_integration.pre_commit_hook(
                    ["shared_file.py"]
                )
                assert aider_result[0] is True

                # Simulate Continue.dev command
                continue_result = await mock_adapter.execute_command(
                    {"command": "analyze", "files": ["shared_file.py"]}
                )
                assert continue_result["status"] == "success"

            finally:
                if test_file.exists():
                    test_file.unlink()

class TestAiderIntegrationEdgeCases:
    """Test edge cases and special scenarios"""

    @pytest.mark.asyncio
    async def test_concurrent_operations(

    ):
        """Test concurrent Aider operations"""
        # Create multiple files
        files = []
        for i in range(5):
            file_path = Path(f"concurrent_{i}.py")
            file_path.write_text(
                f"""
def func_{i}():
    \"\"\"Function {i}.\"\"\"
    return {i}

def test_func_{i}():
    \"\"\"Test function {i}.\"\"\"
    assert func_{i}() == {i}
"""
            )
            files.append(file_path.name)

        # Run concurrent pre-commit checks
        tasks = [aider_integration.pre_commit_hook([file]) for file in files]

        results = await asyncio.gather(*tasks)

        # All should pass
        for should_commit, message in results:
            assert should_commit is True

    @pytest.mark.asyncio
    async def test_large_diff_handling(

    ):
        """Test handling of large diffs"""
        # Create file with large content
        large_file = Path("large_module.py")

        # Generate large but valid Python content
        content_lines = ['"""Large module with many functions."""\n\n']

        for i in range(100):
            content_lines.append(
                f'''
def function_{i}(x: int) -> int:
    """Function {i} documentation."""
    return x + {i}

'''
            )

        # Add tests at the end
        content_lines.append("\n# Tests\n")
        for i in range(100):
            content_lines.append(
                f'''
def test_function_{i}():
    """Test function_{i}."""
    assert function_{i}(10) == {10 + i}

'''
            )

        large_file.write_text("".join(content_lines))

        # Test pre-commit with large file
        should_commit, message = await aider_integration.pre_commit_hook(
            ["large_module.py"]
        )
        assert should_commit is True

        # Test commit with large diff
        result = await aider_integration.create_elder_commit(
            ["large_module.py"], "feat: add large module with 100 functions"
        )

        assert result["success"] is True

# Performance benchmarks
@pytest.mark.benchmark
class TestAiderIntegrationPerformance:
    """Performance benchmarks for Aider integration"""

    @pytest.mark.asyncio
    async def test_pre_commit_performance(

    ):
        """Benchmark pre-commit hook performance"""
        # Create test file
        test_file = Path("perf_test.py")
        test_file.write_text(
            """
def calculate(x: int, y: int) -> int:
    \"\"\"Calculate sum.\"\"\"
    return x + y

def test_calculate():
    \"\"\"Test calculation.\"\"\"
    assert calculate(2, 3) == 5
"""
        )

        async def run_pre_commit():
            return await aider_integration.pre_commit_hook(["perf_test.py"])

        # Run benchmark
        result = benchmark(asyncio.run, run_pre_commit())
        assert result[0] is True
