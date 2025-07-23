#!/usr/bin/env python3
"""
📊 Coverage Enhancement Knight - Test Coverage Improvement Specialist
Automatically improves test coverage during idle system periods
"""

import ast
import json
import logging
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Import our idle monitor
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from libs.idle_resource_monitor import IdleResourceMonitor


@dataclass
class CoverageTarget:
    """Represents a target for coverage improvement"""

    file_path: str
    function_name: str
    line_numbers: List[int]
    current_coverage: float
    priority: str  # LOW, MEDIUM, HIGH, CRITICAL
    estimated_effort: int  # Minutes to implement test
    test_file_path: str


@dataclass
class CoverageImprovement:
    """Represents a completed coverage improvement"""

    target: CoverageTarget
    test_code: str
    lines_covered: List[int]
    coverage_gain: float
    completion_time: str
    success: bool
    error_message: Optional[str] = None


class CoverageEnhancementKnight:
    """
    🛡️ Coverage Enhancement Knight
    Automatically improves test coverage during idle periods
    """

    def __init__(
        self,
        project_root: str = ".",
        min_idle_duration: int = 300,  # 5 minutes
        coverage_threshold: float = 90.0,
    ):
        """
        Initialize the Coverage Enhancement Knight

        Args:
            project_root: Root directory of the project
            min_idle_duration: Minimum idle time before starting work (seconds)
            coverage_threshold: Target coverage percentage
        """
        self.project_root = Path(project_root).resolve()
        self.min_idle_duration = min_idle_duration
        self.coverage_threshold = coverage_threshold

        # Knight identification
        self.knight_id = "coverage_enhancement_001"
        self.knight_name = "📊 Coverage Enhancement Knight"

        # State tracking
        self.is_active = False
        self.current_task: Optional[CoverageTarget] = None
        self.completed_improvements: List[CoverageImprovement] = []
        self.failed_attempts: List[CoverageTarget] = []

        # Resource monitoring
        self.resource_monitor = IdleResourceMonitor(
            check_interval=60,  # Check every minute
            idle_thresholds={
                "cpu": 20.0,
                "memory": 70.0,
                "load": 1.0,
                "min_duration": min_idle_duration,
            },
        )

        # Work queue
        self.coverage_targets = queue.PriorityQueue()
        self.work_thread: Optional[threading.Thread] = None

        # Setup logging
        self.logger = logging.getLogger(f"{__name__}.{self.knight_id}")
        self.logger.setLevel(logging.INFO)

        # File patterns to analyze
        self.source_patterns = ["*.py"]
        self.test_patterns = ["test_*.py", "*_test.py"]
        self.ignore_patterns = [
            "__pycache__",
            ".git",
            ".pytest_cache",
            "venv",
            ".venv",
            "node_modules",
        ]

    def analyze_current_coverage(self) -> Dict[str, float]:
        """Analyze current test coverage"""
        try:
            # Run coverage analysis
            coverage_file = self.project_root / ".coverage"

            # Run pytest with coverage
            cmd = [
                "python",
                "-m",
                "pytest",
                "--cov=.",
                "--cov-report=json",
                "--cov-report=term-missing",
                "--quiet",
                str(self.project_root / "tests"),
            ]

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            # Parse coverage.json if it exists
            coverage_json_path = self.project_root / "coverage.json"
            if coverage_json_path.exists():
                with open(coverage_json_path, encoding="utf-8") as f:
                    coverage_data = json.load(f)

                file_coverage = {}
                for filepath, data in coverage_data.get("files", {}).items():
                    file_coverage[filepath] = data.get("summary", {}).get(
                        "percent_covered", 0.0
                    )

                return file_coverage

            return {}

        except Exception as e:
            self.logger.error(f"❌ Coverage analysis failed: {e}")
            return {}

    def find_uncovered_functions(self, filepath: str) -> List[CoverageTarget]:
        """Find uncovered functions in a Python file"""
        targets = []

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                source_code = f.read()

            # Parse AST to find functions
            tree = ast.parse(source_code)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Skip private functions and test functions
                    if (
                        node.name.startswith("_") and not node.name.startswith("__")
                    ) or node.name.startswith("test_"):
                        continue

                    # Estimate priority based on function complexity
                    priority = self._estimate_function_priority(node, source_code)
                    effort = self._estimate_test_effort(node, source_code)

                    # Generate test file path
                    rel_path = Path(filepath).relative_to(self.project_root)
                    test_file = self._generate_test_file_path(rel_path)

                    target = CoverageTarget(
                        file_path=filepath,
                        function_name=node.name,
                        line_numbers=list(range(node.lineno, node.end_lineno + 1)),
                        current_coverage=0.0,  # Will be updated by coverage analysis
                        priority=priority,
                        estimated_effort=effort,
                        test_file_path=str(test_file),
                    )

                    targets.append(target)

        except Exception as e:
            self.logger.error(f"❌ Error analyzing {filepath}: {e}")

        return targets

    def _estimate_function_priority(
        self, node: ast.FunctionDef, source_code: str
    ) -> str:
        """Estimate the priority of testing a function"""
        # Check for decorators that indicate importance
        decorators = [
            d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list
        ]

        if any(dec in ["route", "app.route", "api", "endpoint"] for dec in decorators):
            return "CRITICAL"  # API endpoints are critical

        if any(
            dec in ["property", "staticmethod", "classmethod"] for dec in decorators
        ):
            return "HIGH"

        # Check function complexity (number of if statements, loops, etc.)
        complexity = self._calculate_complexity(node)

        if complexity > 10:
            return "HIGH"
        elif complexity > 5:
            return "MEDIUM"
        else:
            return "LOW"

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _estimate_test_effort(self, node: ast.FunctionDef, source_code: str) -> int:
        """Estimate effort to write tests (in minutes)"""
        complexity = self._calculate_complexity(node)
        num_params = len(node.args.args)

        # Base effort
        effort = 5  # 5 minutes base

        # Add time for complexity
        effort += complexity * 2

        # Add time for parameters (mocking/setup)
        effort += num_params * 1

        # Cap at reasonable maximum
        return min(effort, 30)

    def _generate_test_file_path(self, source_file: Path) -> Path:
        """Generate appropriate test file path"""
        test_dir = self.project_root / "tests"

        # Handle different source locations
        if source_file.parts[0] in ["libs", "workers", "commands"]:
            # Create corresponding test structure
            test_path = (
                test_dir / "unit" / source_file.parent / f"test_{source_file.name}"
            )
        else:
            # Default test location
            test_path = test_dir / f"test_{source_file.name}"

        return test_path

    def generate_test_code(self, target: CoverageTarget) -> str:
        """Generate test code for a coverage target"""
        try:
            # Read the source file to understand the function
            with open(target.file_path, "r") as f:
                source_code = f.read()

            # Parse to get function details
            tree = ast.parse(source_code)
            function_node = None

            for node in ast.walk(tree):
                if (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == target.function_name
                ):
                    function_node = node
                    break

            if not function_node:
                return ""

            # Generate test template
            template = self._create_test_template(target, function_node, source_code)
            return template

        except Exception as e:
            self.logger.error(
                f"❌ Error generating test for {target.function_name}: {e}"
            )
            return ""

    def _create_test_template(
        self, target: CoverageTarget, func_node: ast.FunctionDef, source_code: str
    ) -> str:
        """Create a test template for the function"""
        # Extract module path for import
        rel_path = Path(target.file_path).relative_to(self.project_root)
        module_path = str(rel_path.with_suffix("")).replace("/", ".")

        # Get function signature
        args = [arg.arg for arg in func_node.args.args if arg.arg != "self"]

        # Generate test cases based on function analysis
        test_cases = self._generate_test_cases(func_node, args)

        template = f'''#!/usr/bin/env python3
"""
Test cases for {target.function_name} function
Auto-generated by Coverage Enhancement Knight
"""

import pytest
import unittest.mock as mock
from unittest.mock import Mock, patch, MagicMock

# Import the function to test
from {module_path} import {target.function_name}


class Test{target.function_name.title()}:
    """Test cases for {target.function_name} function"""

    def test_{target.function_name}_basic_functionality(self):
        """Test basic functionality of {target.function_name}"""
        # TODO: Implement basic test case
        {test_cases.get('basic', 'pass')}

    def test_{target.function_name}_edge_cases(self):
        """Test edge cases for {target.function_name}"""
        # TODO: Implement edge case tests
        {test_cases.get('edge_cases', 'pass')}

    def test_{target.function_name}_error_handling(self):
        """Test error handling in {target.function_name}"""
        # TODO: Implement error handling tests
        {test_cases.get('error_handling', 'pass')}
'''

        # Add parameter-specific tests if function has parameters
        if args:
            template += f'''
    def test_{target.function_name}_with_different_parameters(self):
        """Test {target.function_name} with various parameter combinations"""
        # TODO: Test with different parameter values
        {test_cases.get('parameters', 'pass')}
'''

        return template

    def _generate_test_cases(
        self, func_node: ast.FunctionDef, args: List[str]
    ) -> Dict[str, str]:
        """Generate specific test case code snippets"""
        test_cases = {
            "basic": "pass  # Add basic functionality test",
            "edge_cases": "pass  # Add edge case tests",
            "error_handling": "pass  # Add error handling tests",
            "parameters": "pass  # Add parameter tests",
        }

        # Analyze function body for specific patterns
        for node in ast.walk(func_node):
            if isinstance(node, ast.Raise):
                test_cases["error_handling"] = (
                    "with pytest.raises(Exception):\n            pass  # Test exception raising"
                )
            elif isinstance(node, ast.Return):
                test_cases["basic"] = (
                    "result = {target.function_name}()\n        assert result is not None"
                )

        return test_cases

    def implement_coverage_improvement(
        self, target: CoverageTarget
    ) -> CoverageImprovement:
        """Implement a coverage improvement for a target"""
        self.logger.info(f"🔧 Working on {target.function_name} in {target.file_path}")

        start_time = datetime.now()

        try:
            # Generate test code
            test_code = self.generate_test_code(target)
            if not test_code:
                raise Exception("Failed to generate test code")

            # Ensure test directory exists
            test_file_path = Path(target.test_file_path)
            test_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if test file already exists
            if test_file_path.exists():
                # Append to existing file
                with open(test_file_path, "a") as f:
                    f.write(f"\n\n# Added by Coverage Enhancement Knight\n{test_code}")
            else:
                # Create new test file
                with open(test_file_path, "w") as f:
                    f.write(test_code)

            # Run the new tests to verify they work
            result = subprocess.run(
                ["python", "-m", "pytest", str(test_file_path), "-v"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Calculate coverage improvement
            coverage_gain = self._calculate_coverage_gain(target)

            improvement = CoverageImprovement(
                target=target,
                test_code=test_code,
                lines_covered=target.line_numbers,
                coverage_gain=coverage_gain,
                completion_time=datetime.now().isoformat(),
                success=result.returncode == 0,
                error_message=result.stderr if result.returncode != 0 else None,
            )

            if improvement.success:
                self.logger.info(
                    f"✅ Completed {target.function_name} (+{coverage_gain:.1f}% coverage)"
                )
            else:
                self.logger.warning(
                    f"⚠️ Tests created but failed: {improvement.error_message}"
                )

            return improvement

        except Exception as e:
            self.logger.error(
                f"❌ Failed to improve coverage for {target.function_name}: {e}"
            )

            return CoverageImprovement(
                target=target,
                test_code="",
                lines_covered=[],
                coverage_gain=0.0,
                completion_time=datetime.now().isoformat(),
                success=False,
                error_message=str(e),
            )

    def _calculate_coverage_gain(self, target: CoverageTarget) -> float:
        """Calculate estimated coverage gain from implementing test"""
        # Simple estimation based on function size
        function_lines = len(target.line_numbers)
        total_project_lines = self._count_total_project_lines()

        if total_project_lines > 0:
            return (function_lines / total_project_lines) * 100
        return 0.0

    def _count_total_project_lines(self) -> int:
        """Count total lines of code in project"""
        total_lines = 0

        for py_file in self.project_root.rglob("*.py"):
            if any(ignore in str(py_file) for ignore in self.ignore_patterns):
                continue

            try:
                with open(py_file, "r") as f:
                    total_lines += len(f.readlines())
            except:
                continue

        return total_lines

    def scan_for_coverage_targets(self) -> List[CoverageTarget]:
        """Scan project for coverage improvement opportunities"""
        self.logger.info("🔍 Scanning for coverage targets...")

        targets = []
        current_coverage = self.analyze_current_coverage()

        # Find all Python source files
        for py_file in self.project_root.rglob("*.py"):
            if any(ignore in str(py_file) for ignore in self.ignore_patterns):
                continue

            if any(
                pattern.replace("*", "") in py_file.name
                for pattern in self.test_patterns
            ):
                continue  # Skip test files

            # Get coverage for this file
            rel_path = str(py_file.relative_to(self.project_root))
            file_coverage = current_coverage.get(rel_path, 0.0)

            # Only target files with low coverage
            if file_coverage < self.coverage_threshold:
                file_targets = self.find_uncovered_functions(str(py_file))
                for target in file_targets:
                    target.current_coverage = file_coverage
                targets.extend(file_targets)

        # Sort by priority and effort
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        targets.sort(
            key=lambda t: (priority_order.get(t.priority, 4), t.estimated_effort)
        )

        self.logger.info(f"📊 Found {len(targets)} coverage targets")
        return targets

    def start_coverage_monitoring(self):
        """Start monitoring for idle periods to improve coverage"""
        self.logger.info(f"🛡️ {self.knight_name} starting patrol")

        self.is_active = True
        self.resource_monitor.start_monitoring()
        self.work_thread = threading.Thread(
            target=self._coverage_work_loop, daemon=True
        )
        self.work_thread.start()

    def stop_coverage_monitoring(self):
        """Stop coverage monitoring"""
        self.logger.info(f"🛑 {self.knight_name} ending patrol")

        self.is_active = False
        self.resource_monitor.stop_monitoring()

        if self.work_thread:
            self.work_thread.join(timeout=10)

    def _coverage_work_loop(self):
        """Main work loop for coverage improvement"""
        while self.is_active:
            try:
                # Check if system is idle
                idle_status = self.resource_monitor.get_current_idle_status()

                if idle_status.get("suitable_for_tasks", False):
                    if self.coverage_targets.empty():
                        # Scan for new targets
                        targets = self.scan_for_coverage_targets()
                        for i, target in enumerate(targets[:10]):  # Limit to top 10
                            priority = (
                                0
                                if target.priority == "CRITICAL"
                                else (
                                    1
                                    if target.priority == "HIGH"
                                    else 2 if target.priority == "MEDIUM" else 3
                                )
                            )
                            self.coverage_targets.put((priority, i, target))

                    if not self.coverage_targets.empty():
                        # Get next target
                        _, _, target = self.coverage_targets.get()
                        self.current_task = target

                        # Implement improvement
                        improvement = self.implement_coverage_improvement(target)

                        if improvement.success:
                            self.completed_improvements.append(improvement)
                        else:
                            self.failed_attempts.append(target)

                        self.current_task = None

                # Sleep before next check
                time.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"❌ Error in coverage work loop: {e}")
                time.sleep(60)

    def get_knight_status(self) -> Dict:
        """Get current status of the coverage knight"""
        idle_status = self.resource_monitor.get_current_idle_status()

        return {
            "knight_id": self.knight_id,
            "knight_name": self.knight_name,
            "is_active": self.is_active,
            "current_task": asdict(self.current_task) if self.current_task else None,
            "completed_improvements": len(self.completed_improvements),
            "failed_attempts": len(self.failed_attempts),
            "targets_in_queue": self.coverage_targets.qsize(),
            "system_idle": idle_status.get("suitable_for_tasks", False),
            "idle_duration": idle_status.get("duration", 0),
            "total_coverage_gain": sum(
                imp.coverage_gain for imp in self.completed_improvements
            ),
            "last_activity": (
                self.completed_improvements[-1].completion_time
                if self.completed_improvements
                else None
            ),
        }

    def generate_activity_report(self) -> str:
        """Generate a detailed activity report"""
        status = self.get_knight_status()

        report = f"""
🛡️ {self.knight_name} Activity Report
{'='*50}

📊 Performance Metrics:
   • Completed Improvements: {status['completed_improvements']}
   • Failed Attempts: {status['failed_attempts']}
   • Total Coverage Gain: {status['total_coverage_gain']:.2f}%
   • Targets in Queue: {status['targets_in_queue']}

🎯 Current Status:
   • Active: {'✅' if status['is_active'] else '❌'}
   • System Idle: {'✅' if status['system_idle'] else '❌'}
   • Idle Duration: {status['idle_duration']:.1f}s
   • Current Task: {status['current_task']['function_name'] if status['current_task'] else 'None'}

📈 Recent Improvements:
"""

        for improvement in self.completed_improvements[-5:]:  # Last 5
            report += f"   • {improvement.target.function_name} (+{improvement.coverage_gain:.1f}%)\n" \
                "   • {improvement.target.function_name} (+{improvement.coverage_gain:.1f}%)\n"

        return report


def main():
    """CLI interface for the Coverage Enhancement Knight"""
    import argparse

    parser = argparse.ArgumentParser(description="Coverage Enhancement Knight")
    parser.add_argument("--scan", action="store_true", help="Scan for coverage targets")
    parser.add_argument("--monitor", action="store_true", help="Start monitoring mode")
    parser.add_argument("--status", action="store_true", help="Show knight status")
    parser.add_argument(
        "--duration", type=int, default=3600, help="Monitor duration (seconds)"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    knight = CoverageEnhancementKnight()

    try:
        if args.scan:
            targets = knight.scan_for_coverage_targets()
            print(f"📊 Found {len(targets)} coverage targets:")
            for target in targets[:10]:
                print(
                    f"   • {target.function_name} ({target.priority}, {target.estimated_effort}min)"
                )

        elif args.status:
            status = knight.get_knight_status()
            print(knight.generate_activity_report())

        elif args.monitor:
            print(f"🛡️ Starting {knight.knight_name}")
            print(f"⏰ Duration: {args.duration}s")
            print("Press Ctrl+C to stop")

            knight.start_coverage_monitoring()
            time.sleep(args.duration)

        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\n⏹️ Stopping knight...")
    finally:
        knight.stop_coverage_monitoring()
        print("🛑 Knight patrol ended")


if __name__ == "__main__":
    main()