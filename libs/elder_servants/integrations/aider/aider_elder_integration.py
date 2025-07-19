"""
Aider - Elder Servants Integration
Provides hooks and integration points for Aider to work with Elder Servants
"""

import os
import sys
import json
import subprocess
import asyncio
import uuid
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from libs.elder_servants.base.elder_servant import servant_registry
from libs.elder_flow_servant_executor_real import (
    QualityInspectorServantReal,
    GitKeeperServantReal
)
from libs.elder_flow_servant_executor import ServantTask, ServantType

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AiderElderIntegration:
    """Integration layer between Aider and Elder Servants"""
    
    def __init__(self):
        self.git_keeper = None
        self.quality_inspector = None
        self._initialize_servants()
        
    def _initialize_servants(self):
        """Initialize required Elder Servants"""
        # Initialize Git Keeper
        self.git_keeper = GitKeeperServantReal("GitKeeper")
        # Note: GitKeeperServantReal uses BaseServant, not ElderServant interface
        
        # Initialize Quality Inspector
        self.quality_inspector = QualityInspectorServantReal("QualityInspector")
        # Note: QualityInspectorServantReal uses BaseServant, not ElderServant interface
        
        logger.info("Initialized Elder Servants for Aider integration")
    
    async def pre_commit_hook(self, files_changed: List[str]) -> Tuple[bool, str]:
        """
        Pre-commit hook for Aider
        Runs Iron Will quality checks before allowing commit
        
        Args:
            files_changed: List of files to be committed
            
        Returns:
            Tuple[bool, str]: (should_commit, message)
        """
        logger.info(f"Running pre-commit hook for {len(files_changed)} files")
        
        # Skip non-code files
        code_files = [f for f in files_changed if self._is_code_file(f)]
        
        if not code_files:
            return True, "No code files to check"
        
        # Run quality checks
        total_score = 0
        failed_files = []
        
        for file_path in code_files:
            try:
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Create ServantTask for quality check
                
                task = ServantTask(
                    task_id=str(uuid.uuid4()),
                    servant_type=ServantType.QUALITY_INSPECTOR,
                    description=f"Quality check for {file_path}",
                    command="code_quality_check",
                    arguments={
                        "file_path": file_path
                    }
                )
                
                # Execute quality check
                result = await self.quality_inspector.execute_task(task)
                
                score = result.get("score", 0) * 10  # Convert to percentage
                total_score += score
                
                if score < 95:  # Iron Will threshold
                    failed_files.append((file_path, score))
                    
            except Exception as e:
                logger.error(f"Error checking {file_path}: {str(e)}")
                failed_files.append((file_path, 0))
        
        # Calculate average score
        avg_score = total_score / len(code_files) if code_files else 0
        
        # Determine if commit should proceed
        if failed_files:
            message = f"❌ Iron Will quality check failed (avg: {avg_score:.1f}%)\n"
            message += "Failed files:\n"
            for file_path, score in failed_files:
                message += f"  - {file_path}: {score:.1f}%\n"
            return False, message
        else:
            return True, f"✅ All files pass Iron Will quality check (avg: {avg_score:.1f}%)"
    
    async def enhance_commit_message(self, original_message: str, 
                                   files_changed: List[str],
                                   diff_content: str) -> str:
        """
        Enhance Aider's commit message with Elder context
        
        Args:
            original_message: Aider's generated message
            files_changed: List of changed files
            diff_content: Git diff content
            
        Returns:
            Enhanced commit message
        """
        # Add Elder signature
        enhanced = f"{original_message}\n\n"
        
        # Add quality metrics if available
        if hasattr(self, '_last_quality_scores'):
            avg_score = sum(self._last_quality_scores.values()) / len(self._last_quality_scores)
            enhanced += f"Quality Score: {avg_score:.1f}%\n"
        
        # Add Elder metadata
        enhanced += "\n🤖 Aider + Elder Servants Integration\n"
        enhanced += f"Timestamp: {datetime.now().isoformat()}\n"
        
        # Add Claude signature (consistent with Elder Flow)
        enhanced += "\nCo-Authored-By: Claude <noreply@anthropic.com>"
        
        return enhanced
    
    async def post_edit_analysis(self, file_path: str, 
                               original_content: str,
                               new_content: str) -> Dict[str, Any]:
        """
        Analyze changes after Aider makes edits
        
        Args:
            file_path: Path to edited file
            original_content: Content before edit
            new_content: Content after edit
            
        Returns:
            Analysis results
        """
        # Quality check on new content
        
        task = ServantTask(
            task_id=str(uuid.uuid4()),
            servant_type=ServantType.QUALITY_INSPECTOR,
            description=f"Post-edit analysis for {file_path}",
            command="code_quality_check",
            arguments={
                "file_path": file_path
            }
        )
        
        quality_result = await self.quality_inspector.execute_task(task)
        
        # Calculate diff stats
        original_lines = original_content.count('\n')
        new_lines = new_content.count('\n')
        
        quality_score = quality_result.get("score", 0) * 10  # Convert to percentage
        
        analysis = {
            "file_path": file_path,
            "quality_score": quality_score,
            "lines_added": max(0, new_lines - original_lines),
            "lines_removed": max(0, original_lines - new_lines),
            "passes_iron_will": quality_score >= 95,
            "quality_details": quality_result
        }
        
        return analysis
    
    async def suggest_improvements(self, file_path: str, content: str) -> List[str]:
        """
        Suggest improvements based on Elder analysis
        
        Args:
            file_path: Path to file
            content: File content
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        
        # Run quality check
        
        task = ServantTask(
            task_id=str(uuid.uuid4()),
            servant_type=ServantType.QUALITY_INSPECTOR,
            description=f"Suggest improvements for {file_path}",
            command="code_quality_check",
            arguments={
                "file_path": file_path
            }
        )
        
        quality_result = await self.quality_inspector.execute_task(task)
        quality_data = quality_result
        
        # Generate suggestions based on quality issues
        if quality_data.get("top_issues"):
            for issue in quality_data["top_issues"][:5]:  # Top 5 issues
                suggestions.append(f"Fix {issue.get('type', 'issue')}: {issue.get('message', 'Unknown issue')}")
        
        # Suggest based on score
        score = quality_data.get("score", 0) * 10
        if score < 95:
            grade = quality_data.get("grade", "F")
            suggestions.append(f"Improve code quality (current grade: {grade}, score: {score:.1f}%)")
        
        # Suggest based on issue counts
        issues = quality_data.get("issues", {})
        if issues.get("critical", 0) > 0:
            suggestions.append(f"Fix {issues['critical']} critical issues")
        if issues.get("warning", 0) > 0:
            suggestions.append(f"Address {issues['warning']} warnings")
        
        return suggestions
    
    async def create_elder_commit(self, message: str, files: List[str]) -> Dict[str, Any]:
        """
        Create a commit using Git Keeper Servant
        
        Args:
            message: Commit message
            files: Files to commit
            
        Returns:
            Commit result
        """
        # Stage files
        
        for file_path in files:
            task = ServantTask(
                task_id=str(uuid.uuid4()),
                servant_type=ServantType.GIT_KEEPER,
                description=f"Stage file {file_path}",
                command="git_add",
                arguments={"files": [file_path]}
            )
            await self.git_keeper.execute_task(task)
        
        # Create commit
        commit_task = ServantTask(
            task_id=str(uuid.uuid4()),
            servant_type=ServantType.GIT_KEEPER,
            description="Create commit with Elder integration",
            command="git_commit",
            arguments={"message": message}
        )
        
        result = await self.git_keeper.execute_task(commit_task)
        
        return result
    
    def _is_code_file(self, file_path: str) -> bool:
        """Check if file is a code file"""
        code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c',
            '.h', '.hpp', '.cs', '.rb', '.go', '.rs', '.swift', '.kt'
        }
        return Path(file_path).suffix in code_extensions
    
    # Aider command line integration
    def setup_aider_hooks(self):
        """Setup git hooks for Aider integration"""
        git_dir = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True
        ).stdout.strip()
        
        if not git_dir:
            logger.error("Not in a git repository")
            return False
        
        hooks_dir = Path(git_dir) / "hooks"
        hooks_dir.mkdir(exist_ok=True)
        
        # Create pre-commit hook
        pre_commit_hook = hooks_dir / "pre-commit"
        pre_commit_content = '''#!/bin/bash
# Elder Servants pre-commit hook for Aider

# Run Elder quality check
python -c "
import asyncio
import sys
sys.path.append('$(pwd)')
from libs.elder_servants.integrations.aider.aider_elder_integration import AiderElderIntegration

async def check():
    integration = AiderElderIntegration()
    files = sys.argv[1:] if len(sys.argv) > 1 else []
    should_commit, message = await integration.pre_commit_hook(files)
    print(message)
    return 0 if should_commit else 1

sys.exit(asyncio.run(check()))
" $(git diff --cached --name-only)

exit $?
'''
        
        with open(pre_commit_hook, 'w') as f:
            f.write(pre_commit_content)
        
        pre_commit_hook.chmod(0o755)
        logger.info(f"Created pre-commit hook at {pre_commit_hook}")
        
        return True


# CLI Integration wrapper
class AiderElderCLI:
    """CLI wrapper for using Aider with Elder Servants"""
    
    def __init__(self):
        self.integration = AiderElderIntegration()
    
    def run_aider_with_elder(self, *aider_args):
        """Run aider with Elder Servants integration"""
        # Set environment variables for integration
        env = os.environ.copy()
        env['AIDER_ELDER_INTEGRATION'] = '1'
        env['AIDER_COMMIT_PREFIX'] = '🤖 '
        
        # Add quality check as pre-commit
        if '--no-check' not in aider_args:
            self.integration.setup_aider_hooks()
        
        # Run aider
        cmd = ['aider'] + list(aider_args)
        logger.info(f"Running: {' '.join(cmd)}")
        
        try:
            subprocess.run(cmd, env=env)
        except KeyboardInterrupt:
            logger.info("Aider interrupted by user")
        except Exception as e:
            logger.error(f"Error running aider: {str(e)}")


# Example usage functions
async def example_quality_check():
    """Example of using quality check before commit"""
    integration = AiderElderIntegration()
    
    # Check files
    files = ["example.py", "test_example.py"]
    should_commit, message = await integration.pre_commit_hook(files)
    
    print(f"Should commit: {should_commit}")
    print(f"Message: {message}")


async def example_enhance_message():
    """Example of enhancing commit message"""
    integration = AiderElderIntegration()
    
    original = "feat: add user authentication"
    enhanced = await integration.enhance_commit_message(
        original,
        ["auth.py", "test_auth.py"],
        "diff content here..."
    )
    
    print("Original:", original)
    print("Enhanced:", enhanced)


if __name__ == "__main__":
    # Run examples
    asyncio.run(example_quality_check())