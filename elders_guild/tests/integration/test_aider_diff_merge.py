"""
Specialized tests for Aider diff checking and merge functionality
Tests for Issue #81: Diff and merge capabilities
"""

import os
import subprocess
import sys

from pathlib import Path

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from libs.elder_flow_servant_executor_real import GitKeeperServantReal
from libs.elder_servants.integrations.aider.aider_elder_integration import (
    AiderElderIntegration,
)

class TestAiderDiffMergeCapabilities:
    """Test suite for diff checking and merge functionality"""

    @pytest.fixture
    async def git_keeper(self):
        """Create GitKeeperServant instance"""
        return GitKeeperServantReal()

    @pytest.fixture
    async def aider_integration(self):
        """Create AiderElderIntegration instance"""
        return AiderElderIntegration()

    @pytest.fixture

            original_cwd = os.getcwd()

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

            # Create initial files
            Path("main.py").write_text(
                """
def main():
    print("Hello World")

if __name__ == "__main__":
    main()
"""
            )
            Path("utils.py").write_text(
                """
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
"""
            )

            subprocess.run(["git", "add", "."], capture_output=True, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial commit"],
                capture_output=True,
                check=True,
            )

            # Create feature branch
            subprocess.run(
                ["git", "checkout", "-b", "feature/aider-changes"],
                capture_output=True,
                check=True,
            )

            # Reset working directory
            os.chdir(original_cwd)

    @pytest.mark.asyncio

        """Test basic diff checking"""
        # Modify a file
        Path("main.py").write_text(
            """
def main():
    \"\"\"Main entry point of the application.\"\"\"
    print("Hello World!")
    print("Welcome to Aider integration")

if __name__ == "__main__":
    main()
"""
        )

        # Get unstaged diff
        diff_result = await git_keeper.git_diff(staged=False)
        assert diff_result["success"] is True
        assert "main.py" in diff_result["diff"]
        assert "Hello World!" in diff_result["diff"]
        assert "Welcome to Aider integration" in diff_result["diff"]

        # Stage the file
        await git_keeper.git_add(["main.py"])

        # Get staged diff
        staged_diff_result = await git_keeper.git_diff(staged=True)
        assert staged_diff_result["success"] is True
        assert "main.py" in staged_diff_result["diff"]

    @pytest.mark.asyncio
    async def test_multi_file_diff_analysis(

    ):
        """Test diff analysis across multiple files"""
        # Modify multiple files
        Path("main.py").write_text(
            """
import utils

def main():
    \"\"\"Enhanced main function with utilities.\"\"\"
    result = utils.add(5, 3)
    print(f"Result: {result}")

def test_main():
    \"\"\"Test main function.\"\"\"
    # Simple test
    main()

if __name__ == "__main__":
    main()
"""
        )

        Path("utils.py").write_text(
            """
def add(a: int, b: int) -> int:
    \"\"\"Add two integers.

    Args:
        a: First integer
        b: Second integer

    Returns:
        Sum of a and b
    \"\"\"
    return a + b

def multiply(a: int, b: int) -> int:
    \"\"\"Multiply two integers.\"\"\"
    return a * b

def divide(a: int, b: int) -> float:
    \"\"\"Divide two numbers safely.\"\"\"
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def test_utils():
    \"\"\"Test utility functions.\"\"\"
    assert add(2, 3) == 5
    assert multiply(4, 5) == 20
    assert divide(10, 2) == 5.0
"""
        )

        # Get comprehensive diff
        diff_result = await git_keeper.git_diff(staged=False)
        assert diff_result["success"] is True

        # Analyze changes for each file
        files_to_analyze = ["main.py", "utils.py"]
        analysis_results = {}

        for file_path in files_to_analyze:
            # Read original content (from git)
            original_result = subprocess.run(
                ["git", "show", f"HEAD:{file_path}"], capture_output=True, text=True
            )
            original_content = (
                original_result.stdout if original_result.returncode == 0 else ""
            )

            # Read new content
            new_content = Path(file_path).read_text()

            # Analyze changes
            analysis = await aider_integration.post_edit_analysis(
                file_path, original_content, new_content
            )
            analysis_results[file_path] = analysis

        # Verify analysis
        assert all(analysis["has_tests"] for analysis in analysis_results.values())
        assert all(
            analysis["passes_iron_will"] for analysis in analysis_results.values()
        )
        assert (
            analysis_results["utils.py"]["lines_added"] > 10
        )  # Added divide function and tests

    @pytest.mark.asyncio

        """Test detection of potential merge conflicts"""
        # Create conflicting changes in main branch
        subprocess.run(["git", "checkout", "main"], capture_output=True, check=True)

        Path("utils.py").write_text(
            """
def add(a, b):
    # Main branch implementation
    result = a + b
    print(f"Adding {a} + {b} = {result}")
    return result

def multiply(a, b):
    return a * b
"""
        )

        subprocess.run(["git", "add", "utils.py"], capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Main branch changes"],
            capture_output=True,
            check=True,
        )

        # Go back to feature branch
        subprocess.run(
            ["git", "checkout", "feature/aider-changes"],
            capture_output=True,
            check=True,
        )

        Path("utils.py").write_text(
            """
def add(a: int, b: int) -> int:
    # Feature branch implementation
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("Both arguments must be integers")
    return a + b

def multiply(a, b):
    return a * b
"""
        )

        # Try to detect conflicts before merge
        diff_with_main = subprocess.run(
            ["git", "diff", "main...HEAD", "--", "utils.py"],
            capture_output=True,
            text=True,
        )

        assert diff_with_main.returncode == 0
        assert "add" in diff_with_main.stdout
        assert "Main branch implementation" not in diff_with_main.stdout  # Our version
        assert (
            "Feature branch implementation" not in diff_with_main.stdout
        )  # Diff format

    @pytest.mark.asyncio
    async def test_incremental_diff_tracking(

    ):
        """Test tracking incremental changes during Aider session"""
        file_path = "evolving_code.py"

        # Initial version
        version1 = """
def process_data(data):
    return data
"""
        Path(file_path).write_text(version1)
        await git_keeper.git_add([file_path])
        await git_keeper.git_commit("feat: initial implementation")

        # First Aider edit
        version2 = """
def process_data(data):
    \"\"\"Process input data.\"\"\"
    if not data:
        return []
    return data
"""
        Path(file_path).write_text(version2)

        # Analyze first change
        await git_keeper.git_diff(staged=False)  # diff1
        analysis1 = await aider_integration.post_edit_analysis(
            file_path, version1, version2
        )

        assert analysis1["quality_score"] > 50  # Improved with docstring
        assert not analysis1["has_tests"]  # Still no tests

        # Commit first change
        await git_keeper.git_add([file_path])
        await git_keeper.git_commit("docs: add docstring")

        # Second Aider edit - add tests
        version3 = """
def process_data(data):
    \"\"\"Process input data with validation.

    Args:
        data: Input data to process

    Returns:
        Processed data or empty list
    \"\"\"
    if not data:
        return []
    if not isinstance(data, (list, tuple)):
        raise TypeError("Data must be a list or tuple")
    return [item for item in data if item is not None]

def test_process_data():
    \"\"\"Test process_data function.\"\"\"
    assert process_data([1, 2, 3]) == [1, 2, 3]
    assert process_data([]) == []
    assert process_data([1, None, 3]) == [1, 3]

    try:
        process_data("string")
        assert False
    except TypeError:
        pass
"""
        Path(file_path).write_text(version3)

        # Analyze second change
        await git_keeper.git_diff(staged=False)  # diff2
        analysis2 = await aider_integration.post_edit_analysis(
            file_path, version2, version3
        )

        assert analysis2["quality_score"] > 85  # High quality with tests
        assert analysis2["has_tests"] is True
        assert analysis2["passes_iron_will"] is True

        # Verify cumulative changes
        cumulative_diff = subprocess.run(
            ["git", "diff", "HEAD~2", "--", file_path], capture_output=True, text=True
        )
        assert "process_data(data):" in cumulative_diff.stdout
        assert "test_process_data" in cumulative_diff.stdout

    @pytest.mark.asyncio
    async def test_diff_based_quality_suggestions(

    ):
        """Test quality suggestions based on diff analysis"""
        # Create a file with room for improvement
        file_path = "needs_improvement.py"
        original = """
def calc(x, y, op):
    if op == "+":
        return x + y
    elif op == "*":
        return x * y
    else:
        return 0
"""
        Path(file_path).write_text(original)
        subprocess.run(["git", "add", file_path], capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial calc function"],
            capture_output=True,
            check=True,
        )

        # Aider makes partial improvements
        improved = """
def calc(x: float, y: float, op: str) -> float:
    if op == "+":
        return x + y
    elif op == "*":
        return x * y
    elif op == "-":
        return x - y
    elif op == "/":
        if y == 0:
            raise ValueError("Division by zero")
        return x / y
    else:
        raise ValueError(f"Unknown operation: {op}")
"""
        Path(file_path).write_text(improved)

        # Get suggestions based on diff
        suggestions = await aider_integration.suggest_improvements(file_path, improved)

        # Should suggest docstring and tests
        suggestions_text = " ".join(suggestions).lower()
        assert "docstring" in suggestions_text or "documentation" in suggestions_text
        assert "test" in suggestions_text
        assert len(suggestions) >= 2

    @pytest.mark.asyncio

        """Test comparing diffs between branches"""
        # Make changes in feature branch
        Path("feature.py").write_text(
            """
def feature_function():
    \"\"\"New feature implementation.\"\"\"
    return "feature"

def test_feature():
    \"\"\"Test the feature.\"\"\"
    assert feature_function() == "feature"
"""
        )

        await git_keeper.git_add(["feature.py"])
        await git_keeper.git_commit("feat: add new feature")

        # Get diff against main branch
        branch_diff = subprocess.run(
            ["git", "diff", "main", "--name-only"], capture_output=True, text=True
        )

        assert "feature.py" in branch_diff.stdout

        # Get detailed diff
        detailed_diff = subprocess.run(
            ["git", "diff", "main", "--", "feature.py"], capture_output=True, text=True
        )

        assert "feature_function" in detailed_diff.stdout
        assert "test_feature" in detailed_diff.stdout

    @pytest.mark.asyncio

        """Test generating and applying patches from diffs"""
        # Create base state
        Path("patchable.py").write_text(
            """
def original():
    return "v1"
"""
        )
        await git_keeper.git_add(["patchable.py"])
        await git_keeper.git_commit("Initial patchable")

        # Make changes
        Path("patchable.py").write_text(
            """
def original():
    \"\"\"Original function with improvements.\"\"\"
    return "v2"

def enhanced():
    \"\"\"New enhanced function.\"\"\"
    return "enhanced"

def test_functions():
    \"\"\"Test all functions.\"\"\"
    assert original() == "v2"
    assert enhanced() == "enhanced"
"""
        )

        # Generate patch
        patch_result = subprocess.run(
            ["git", "diff", "HEAD", "--", "patchable.py"],
            capture_output=True,
            text=True,
        )

        patch_content = patch_result.stdout
        assert "@@" in patch_content  # Hunk header
        assert "+def enhanced():" in patch_content
        assert "+def test_functions():" in patch_content

        # Save patch for potential reuse
        Path("changes.patch").write_text(patch_content)

        # Verify patch can be applied (in theory)
        assert len(patch_content.splitlines()) > 10  # Substantial patch

class TestAiderMergeWorkflows:
    """Test complex merge workflows with Aider"""

    @pytest.mark.asyncio
    async def test_auto_merge_high_quality_changes(

    ):
        """Test automatic merging of high-quality Aider changes"""
        # Setup feature branch
        subprocess.run(
            ["git", "checkout", "-b", "aider-auto-merge"],
            capture_output=True,
            check=True,
        )

        # Aider creates high-quality changes
        Path("auto_merge.py").write_text(
            '''
"""
Module for demonstrating auto-merge capabilities.
"""

from typing import List, Optional

def process_items(items: List[str]) -> List[str]:
    """
    Process a list of items with validation.

    Args:
        items: List of string items to process

    Returns:
        Processed list with duplicates removed and sorted

    Raises:
        TypeError: If items is not a list
        ValueError: If any item is not a string
    """
    if not isinstance(items, list):
        raise TypeError("Items must be a list")

    processed = []
    for item in items:
        if not isinstance(item, str):
            raise ValueError(f"Item {item} is not a string")
        processed.append(item.strip().lower())

    return sorted(list(set(processed)))

def test_process_items():
    """Comprehensive tests for process_items."""
    # Test normal case
    assert process_items(["Apple", "banana", "Apple"]) == ["apple", "banana"]

    # Test empty list
    assert process_items([]) == []

    # Test with whitespace
    assert process_items([" test ", "TEST"]) == ["test"]

    # Test error cases
    try:
        process_items("not a list")
        assert False
    except TypeError:
        pass

    try:
        process_items(["valid", 123])
        assert False
    except ValueError:
        pass
'''
        )

        # Check quality before merge
        should_commit, message = await aider_integration.pre_commit_hook(
            ["auto_merge.py"]
        )
        assert should_commit is True

        # Commit and prepare for merge
        result = await aider_integration.create_elder_commit(
            ["auto_merge.py"], "feat: add process_items with comprehensive tests"
        )
        assert result["success"] is True

        # Simulate merge approval based on quality
        analysis = await aider_integration.post_edit_analysis(
            "auto_merge.py", "", Path("auto_merge.py").read_text()  # New file
        )

        # High quality should allow auto-merge
        assert analysis["quality_score"] > 90
        assert analysis["passes_iron_will"] is True
        assert analysis["has_tests"] is True

        # In real scenario, this would trigger auto-merge to main
        merge_ready = (
            analysis["quality_score"] > 85
            and analysis["passes_iron_will"]
            and analysis["has_tests"]
        )
        assert merge_ready is True
