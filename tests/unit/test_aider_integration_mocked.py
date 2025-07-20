"""
Unit tests for Aider integration with mocked dependencies
Focus on isolated testing of integration logic
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from libs.elder_servants.integrations.aider.aider_elder_integration import (
    AiderElderIntegration,
)


class TestAiderIntegrationUnit:
    """Unit tests for AiderElderIntegration with mocked dependencies"""

    @pytest.fixture
    def mock_quality_analyzer(self):
        """Mock QualityAnalyzerReal"""
        with patch(
            "libs.elder_servants.integrations.aider.aider_elder_integration.QualityAnalyzerReal"
        ) as mock:
            analyzer = mock.return_value
            analyzer.analyze_file = AsyncMock(
                return_value={
                    "quality_score": 85.0,
                    "passes_iron_will": True,
                    "has_tests": True,
                    "has_docstrings": True,
                    "issues": [],
                }
            )
            yield analyzer

    @pytest.fixture
    def mock_git_keeper(self):
        """Mock GitKeeperServantReal"""
        with patch(
            "libs.elder_servants.integrations.aider.aider_elder_integration.GitKeeperServantReal"
        ) as mock:
            keeper = mock.return_value
            keeper.git_add = AsyncMock(return_value={"success": True})
            keeper.git_commit = AsyncMock(
                return_value={"success": True, "commit_hash": "abc123"}
            )
            keeper.git_status = AsyncMock(
                return_value={"success": True, "status": "clean"}
            )
            keeper.git_diff = AsyncMock(
                return_value={"success": True, "diff": "diff content"}
            )
            yield keeper

    @pytest.fixture
    def aider_integration(self, mock_quality_analyzer, mock_git_keeper):
        """Create AiderElderIntegration with mocked dependencies"""
        return AiderElderIntegration()

    @pytest.mark.asyncio
    async def test_pre_commit_hook_with_high_quality_code(
        self, aider_integration, mock_quality_analyzer
    ):
        """Test pre-commit hook with high quality code"""
        # Setup
        test_file = "test_file.py"
        mock_quality_analyzer.analyze_file.return_value = {
            "quality_score": 95.0,
            "passes_iron_will": True,
            "has_tests": True,
            "has_docstrings": True,
            "issues": [],
        }

        # Execute
        should_commit, message = await aider_integration.pre_commit_hook([test_file])

        # Assert
        assert should_commit is True
        assert "high quality" in message.lower() or "pass" in message.lower()
        mock_quality_analyzer.analyze_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_pre_commit_hook_with_low_quality_code(
        self, aider_integration, mock_quality_analyzer
    ):
        """Test pre-commit hook with low quality code"""
        # Setup
        test_file = "bad_file.py"
        mock_quality_analyzer.analyze_file.return_value = {
            "quality_score": 45.0,
            "passes_iron_will": False,
            "has_tests": False,
            "has_docstrings": False,
            "issues": [
                {"type": "missing_tests", "message": "No tests found"},
                {"type": "missing_docstrings", "message": "Functions lack docstrings"},
            ],
        }

        # Execute
        should_commit, message = await aider_integration.pre_commit_hook([test_file])

        # Assert
        assert should_commit is False
        assert "iron will" in message.lower() or "quality" in message.lower()
        assert "tests" in message.lower()

    @pytest.mark.asyncio
    async def test_enhance_commit_message(self, aider_integration):
        """Test commit message enhancement"""
        # Setup
        original_message = "fix: bug in auth"
        files_changed = ["auth.py", "test_auth.py"]
        diff_content = """
diff --git a/auth.py b/auth.py
@@ -1,5 +1,10 @@
 def authenticate(user, password):
-    return True
+    if not user or not password:
+        raise ValueError("User and password required")
+    return validate_credentials(user, password)
+
+def validate_credentials(user, password):
+    # Actual validation logic
+    return True
"""

        # Execute
        enhanced = await aider_integration.enhance_commit_message(
            original_message, files_changed, diff_content
        )

        # Assert
        assert len(enhanced) > len(original_message)
        assert "auth" in enhanced.lower()
        assert "🤖" in enhanced or "Generated with Claude" in enhanced
        assert "fix:" in enhanced  # Should preserve conventional commit format

    @pytest.mark.asyncio
    async def test_post_edit_analysis(self, aider_integration):
        """Test post-edit analysis functionality"""
        # Setup
        file_path = "test.py"
        original_content = "def func():\n    pass"
        new_content = """def func():
    \"\"\"Function with documentation.\"\"\"
    return "improved"

def test_func():
    \"\"\"Test the function.\"\"\"
    assert func() == "improved"
"""

        # Execute
        with patch("builtins.open", mock_open(read_data=new_content)):
            analysis = await aider_integration.post_edit_analysis(
                file_path, original_content, new_content
            )

        # Assert
        assert "quality_score" in analysis
        assert "lines_added" in analysis
        assert "lines_removed" in analysis
        assert "has_tests" in analysis
        assert "passes_iron_will" in analysis
        assert analysis["lines_added"] > 0

    @pytest.mark.asyncio
    async def test_suggest_improvements(self, aider_integration):
        """Test improvement suggestions generation"""
        # Setup
        file_path = "improve_me.py"
        content = """
def calculate(x, y):
    result = x + y
    return result
"""

        # Execute
        with patch("builtins.open", mock_open(read_data=content)):
            suggestions = await aider_integration.suggest_improvements(
                file_path, content
            )

        # Assert
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        # Should suggest type hints, docstrings, tests
        suggestions_text = " ".join(suggestions).lower()
        assert any(
            keyword in suggestions_text
            for keyword in ["type", "docstring", "test", "document"]
        )

    @pytest.mark.asyncio
    async def test_create_elder_commit(self, aider_integration, mock_git_keeper):
        """Test Elder commit creation"""
        # Setup
        files = ["file1.py", "file2.py"]
        message = "feat: add new feature"

        # Execute
        result = await aider_integration.create_elder_commit(files, message)

        # Assert
        assert result["success"] is True
        assert "commit_hash" in result
        mock_git_keeper.git_add.assert_called_once_with(files)
        mock_git_keeper.git_commit.assert_called_once()

        # Check commit message was enhanced
        commit_call_args = mock_git_keeper.git_commit.call_args[0][0]
        assert len(commit_call_args) > len(message)
        assert "feat:" in commit_call_args

    @pytest.mark.asyncio
    async def test_create_elder_commit_with_failure(
        self, aider_integration, mock_git_keeper
    ):
        """Test Elder commit creation with git failure"""
        # Setup
        files = ["file1.py"]
        message = "feat: add feature"
        mock_git_keeper.git_add.return_value = {
            "success": False,
            "error": "Failed to add files",
        }

        # Execute
        result = await aider_integration.create_elder_commit(files, message)

        # Assert
        assert result["success"] is False
        assert "error" in result
        mock_git_keeper.git_commit.assert_not_called()

    def test_setup_aider_hooks(self, aider_integration):
        """Test git hooks setup"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock git directory
            git_dir = Path(temp_dir) / ".git" / "hooks"
            git_dir.mkdir(parents=True)

            # Mock subprocess to avoid actual git commands
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0)

                # Change to temp directory
                original_cwd = os.getcwd()
                os.chdir(temp_dir)

                try:
                    # Execute
                    success = aider_integration.setup_aider_hooks()

                    # Assert
                    assert success is True

                    # Check pre-commit hook was created
                    pre_commit_hook = git_dir / "pre-commit"
                    assert pre_commit_hook.exists()
                    assert pre_commit_hook.stat().st_mode & 0o111  # Check executable

                    # Check hook content
                    hook_content = pre_commit_hook.read_text()
                    assert "python" in hook_content
                    assert "aider_pre_commit" in hook_content

                finally:
                    os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_multiple_file_analysis(
        self, aider_integration, mock_quality_analyzer
    ):
        """Test handling multiple files with mixed quality"""
        # Setup
        files = ["good.py", "bad.py", "medium.py"]

        # Configure different quality scores for each file
        mock_quality_analyzer.analyze_file.side_effect = [
            {
                "quality_score": 95.0,
                "passes_iron_will": True,
                "has_tests": True,
                "has_docstrings": True,
                "issues": [],
            },
            {
                "quality_score": 40.0,
                "passes_iron_will": False,
                "has_tests": False,
                "has_docstrings": False,
                "issues": [{"type": "missing_tests", "message": "No tests"}],
            },
            {
                "quality_score": 75.0,
                "passes_iron_will": True,
                "has_tests": True,
                "has_docstrings": False,
                "issues": [{"type": "missing_docstrings", "message": "No docs"}],
            },
        ]

        # Execute
        should_commit, message = await aider_integration.pre_commit_hook(files)

        # Assert
        assert should_commit is False  # One file fails Iron Will
        assert "2/3 files pass" in message or "bad.py" in message
        assert mock_quality_analyzer.analyze_file.call_count == 3

    @pytest.mark.asyncio
    async def test_concurrent_file_processing(
        self, aider_integration, mock_quality_analyzer
    ):
        """Test concurrent processing of multiple files"""
        # Setup
        files = [f"file_{i}.py" for i in range(10)]

        # All files pass
        mock_quality_analyzer.analyze_file.return_value = {
            "quality_score": 85.0,
            "passes_iron_will": True,
            "has_tests": True,
            "has_docstrings": True,
            "issues": [],
        }

        # Execute
        import time

        start_time = time.time()
        should_commit, message = await aider_integration.pre_commit_hook(files)
        elapsed = time.time() - start_time

        # Assert
        assert should_commit is True
        assert elapsed < 2.0  # Should process concurrently, not take 10x time
        assert mock_quality_analyzer.analyze_file.call_count == 10


def mock_open(read_data=""):
    """Helper to create mock file open"""
    m = MagicMock()
    m.__enter__.return_value.read.return_value = read_data
    m.__enter__.return_value.__iter__.return_value = read_data.splitlines()
    return m


class TestAiderIntegrationErrorHandling:
    """Test error handling scenarios"""

    @pytest.mark.asyncio
    async def test_handle_file_not_found(self, aider_integration):
        """Test handling of non-existent files"""
        # Execute
        should_commit, message = await aider_integration.pre_commit_hook(
            ["non_existent.py"]
        )

        # Assert
        assert should_commit is False
        assert "error" in message.lower() or "not found" in message.lower()

    @pytest.mark.asyncio
    async def test_handle_syntax_errors(self, aider_integration, mock_quality_analyzer):
        """Test handling of files with syntax errors"""
        # Setup
        mock_quality_analyzer.analyze_file.side_effect = SyntaxError("Invalid syntax")

        # Execute
        should_commit, message = await aider_integration.pre_commit_hook(
            ["syntax_error.py"]
        )

        # Assert
        assert should_commit is False
        assert "syntax" in message.lower()

    @pytest.mark.asyncio
    async def test_handle_analysis_timeout(
        self, aider_integration, mock_quality_analyzer
    ):
        """Test handling of analysis timeout"""

        # Setup
        async def slow_analysis(*args, **kwargs):
            await asyncio.sleep(10)  # Simulate slow analysis
            return {"quality_score": 100}

        mock_quality_analyzer.analyze_file = slow_analysis

        # Execute with timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                aider_integration.pre_commit_hook(["slow_file.py"]), timeout=0.1
            )
