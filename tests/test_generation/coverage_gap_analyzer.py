#!/usr/bin/env python3
"""
Coverage Gap Analyzer
Analyzes test coverage and identifies gaps for targeted test generation
"""

import ast
import json
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class CoverageInfo:
    """Information about test coverage for a file"""

    file_path: Path
    total_lines: int
    covered_lines: int
    missing_lines: List[int]
    coverage_percentage: float
    functions_covered: int = 0
    functions_total: int = 0
    branches_covered: int = 0
    branches_total: int = 0

    @property
    def lines_missed(self) -> int:
        return self.total_lines - self.covered_lines

    @property
    def function_coverage(self) -> float:
        if self.functions_total == 0:
            return 100.0
        return (self.functions_covered / self.functions_total) * 100


@dataclass
class ModulePriority:
    """Priority ranking for a module"""

    file_path: Path
    coverage_info: CoverageInfo
    priority_score: int
    reasons: List[str] = field(default_factory=list)
    complexity_score: int = 0
    importance_level: str = "medium"  # low, medium, high, critical


class CoverageParser:
    """Parses coverage reports and extracts detailed information"""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def parse_coverage_json(
        self, coverage_file: Path = None
    ) -> Dict[str, CoverageInfo]:
        """Parse coverage.json file to extract detailed coverage info"""
        if coverage_file is None:
            coverage_file = self.project_root / "coverage.json"

        if not coverage_file.exists():
            print(f"Coverage file not found: {coverage_file}")
            return {}

        with open(coverage_file, "r") as f:
            data = json.load(f)

        coverage_info = {}
        files_data = data.get("files", {})

        for file_path, file_data in files_data.items():
            full_path = self.project_root / file_path

            # Extract coverage metrics
            summary = file_data.get("summary", {})
            total_lines = summary.get("num_statements", 0)
            covered_lines = summary.get("covered_lines", 0)
            missing_lines = summary.get("missing_lines", [])
            coverage_pct = summary.get("percent_covered", 0.0)

            coverage_info[file_path] = CoverageInfo(
                file_path=full_path,
                total_lines=total_lines,
                covered_lines=covered_lines,
                missing_lines=missing_lines,
                coverage_percentage=coverage_pct,
            )

        return coverage_info

    def run_coverage_analysis(self) -> Dict[str, CoverageInfo]:
        """Run coverage analysis and return results"""
        try:
            # Run pytest with coverage
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "pytest",
                    "--cov=.",
                    "--cov-report=json:coverage.json",
                    "--tb=no",
                    "-q",
                ],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            # Parse the generated coverage file
            return self.parse_coverage_json()

        except Exception as e:
            print(f"Error running coverage analysis: {e}")
            return {}

    def get_uncovered_functions(self, file_path: Path) -> List[Dict[str, any]]:
        """Identify uncovered functions in a file"""
        if not file_path.exists():
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)
            functions = []

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Skip private methods unless they're important
                    if node.name.startswith("_") and node.name != "__init__":
                        continue

                    functions.append(
                        {
                            "name": node.name,
                            "line_start": node.lineno,
                            "line_end": node.end_lineno or node.lineno,
                            "is_async": isinstance(node, ast.AsyncFunctionDef),
                            "args": [arg.arg for arg in node.args.args],
                            "complexity": self._calculate_complexity(node),
                        }
                    )

            return functions

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return []

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.With)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
        return complexity


class GapAnalyzer:
    """Analyzes coverage gaps and prioritizes modules for testing"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.coverage_parser = CoverageParser(project_root)
        self.module_importance = self._define_module_importance()

    def _define_module_importance(self) -> Dict[str, str]:
        """Define importance levels for different modules"""
        return {
            # Critical - core system components
            "core/base_worker.py": "critical",
            "core/base_manager.py": "critical",
            "core/config.py": "critical",
            "core/common_utils.py": "critical",
            # High - key functionality
            "libs/queue_manager.py": "high",
            "libs/slack_notifier.py": "high",
            "libs/rag_manager.py": "high",
            "workers/task_worker.py": "high",
            "workers/pm_worker.py": "high",
            "workers/result_worker.py": "high",
            # Medium - supporting components
            "commands/": "medium",
            "ci_cd/": "medium",
            "libs/": "medium",
            # Low - utilities and less critical
            "examples/": "low",
            "utils/": "low",
        }

    def analyze_gaps(self, min_coverage: float = 70.0) -> List[ModulePriority]:
        """Analyze coverage gaps and return prioritized list"""
        print("Analyzing coverage gaps...")

        # Get current coverage data
        coverage_data = self.coverage_parser.run_coverage_analysis()

        gaps = []

        for file_path, coverage_info in coverage_data.items():
            if coverage_info.coverage_percentage < min_coverage:
                priority = self._calculate_priority(file_path, coverage_info)
                gaps.append(priority)

        # Sort by priority score (highest first)
        gaps.sort(key=lambda x: x.priority_score, reverse=True)

        return gaps

    def _calculate_priority(
        self, file_path: str, coverage_info: CoverageInfo
    ) -> ModulePriority:
        """Calculate priority score for a module"""
        score = 0
        reasons = []

        # Base score from coverage gap
        coverage_gap = 100 - coverage_info.coverage_percentage
        score += coverage_gap

        # Importance multiplier
        importance = self._get_module_importance(file_path)
        importance_multipliers = {
            "critical": 3.0,
            "high": 2.0,
            "medium": 1.5,
            "low": 1.0,
        }
        score *= importance_multipliers.get(importance, 1.0)

        if importance in ["critical", "high"]:
            reasons.append(f"Module importance: {importance}")

        # Lines missed factor
        if coverage_info.lines_missed > 50:
            score += 30
            reasons.append(f"Many lines missed: {coverage_info.lines_missed}")
        elif coverage_info.lines_missed > 20:
            score += 15
            reasons.append(f"Moderate lines missed: {coverage_info.lines_missed}")

        # Core module bonus
        if "core/" in file_path:
            score += 40
            reasons.append("Core module")

        # Worker module bonus
        if "workers/" in file_path:
            score += 30
            reasons.append("Worker module")

        # Library module bonus
        if "libs/" in file_path:
            score += 20
            reasons.append("Library module")

        # Penalty for very low coverage (might be hard to test)
        if coverage_info.coverage_percentage < 10:
            score -= 20
            reasons.append("Very low coverage - may need investigation")

        # Get complexity score
        complexity_score = self._analyze_complexity(coverage_info.file_path)

        return ModulePriority(
            file_path=coverage_info.file_path,
            coverage_info=coverage_info,
            priority_score=int(score),
            reasons=reasons,
            complexity_score=complexity_score,
            importance_level=importance,
        )

    def _get_module_importance(self, file_path: str) -> str:
        """Get importance level for a module"""
        # Check exact matches first
        if file_path in self.module_importance:
            return self.module_importance[file_path]

        # Check directory matches
        for pattern, importance in self.module_importance.items():
            if pattern.endswith("/") and file_path.startswith(pattern):
                return importance

        return "medium"  # Default

    def _analyze_complexity(self, file_path: Path) -> int:
        """Analyze file complexity"""
        if not file_path.exists():
            return 0

        functions = self.coverage_parser.get_uncovered_functions(file_path)
        return sum(func.get("complexity", 1) for func in functions)

    def get_top_priority_modules(
        self, gaps: List[ModulePriority], count: int = 5
    ) -> List[ModulePriority]:
        """Get top priority modules for test generation"""
        return gaps[:count]

    def get_modules_by_importance(
        self, gaps: List[ModulePriority], importance: str
    ) -> List[ModulePriority]:
        """Get modules filtered by importance level"""
        return [gap for gap in gaps if gap.importance_level == importance]

    def analyze_missing_coverage_areas(
        self, module_priority: ModulePriority
    ) -> Dict[str, List[str]]:
        """Analyze what specific areas are missing coverage"""
        file_path = module_priority.file_path
        coverage_info = module_priority.coverage_info

        missing_areas = {
            "functions": [],
            "error_handling": [],
            "edge_cases": [],
            "integration_points": [],
        }

        # Get uncovered functions
        functions = self.coverage_parser.get_uncovered_functions(file_path)

        for func in functions:
            start_line = func["line_start"]
            end_line = func["line_end"]

            # Check if function lines are in missing coverage
            missing_lines_set = set(coverage_info.missing_lines)
            func_lines = set(range(start_line, end_line + 1))

            if func_lines.intersection(missing_lines_set):
                missing_areas["functions"].append(func["name"])

                # Analyze function characteristics
                if (
                    func["name"].startswith("handle_")
                    or "error" in func["name"].lower()
                ):
                    missing_areas["error_handling"].append(func["name"])

                if func["complexity"] > 5:
                    missing_areas["edge_cases"].append(f"{func['name']} (complex)")

        return missing_areas

    def generate_gap_report(self, gaps: List[ModulePriority]) -> str:
        """Generate a comprehensive gap analysis report"""
        report = [
            "# Coverage Gap Analysis Report",
            f"\nTotal modules analyzed: {len(gaps)}",
            f"Analysis performed at: {self.project_root}",
            "\n## High Priority Modules (Score > 100):",
        ]

        high_priority = [g for g in gaps if g.priority_score > 100]
        for i, gap in enumerate(high_priority[:10], 1):
            coverage_pct = gap.coverage_info.coverage_percentage
            lines_missed = gap.coverage_info.lines_missed

            report.extend(
                [
                    f"\n### {i}. {gap.file_path.name}",
                    f"- **Priority Score**: {gap.priority_score}",
                    f"- **Current Coverage**: {coverage_pct:.1f}%",
                    f"- **Lines Missed**: {lines_missed}",
                    f"- **Importance**: {gap.importance_level}",
                    f"- **Complexity Score**: {gap.complexity_score}",
                    f"- **Reasons**: {', '.join(gap.reasons)}",
                ]
            )

            # Add missing areas analysis
            missing_areas = self.analyze_missing_coverage_areas(gap)
            if missing_areas["functions"]:
                report.append(
                    f"- **Missing Functions**: {', '.join(missing_areas['functions'][:5])}"
                )

        report.extend(
            [
                "\n## Coverage by Module Type:",
                self._generate_module_type_summary(gaps),
                "\n## Recommendations:",
                "1. Focus on critical and high importance modules first",
                "2. Prioritize modules with high complexity scores",
                "3. Target specific missing functions identified above",
                "4. Implement error handling and edge case tests",
                "5. Add integration tests for worker modules",
            ]
        )

        return "\n".join(report)

    def _generate_module_type_summary(self, gaps: List[ModulePriority]) -> str:
        """Generate summary by module type"""
        by_type = defaultdict(list)

        for gap in gaps:
            path_str = str(gap.file_path)
            if "/core/" in path_str:
                by_type["Core"].append(gap)
            elif "/workers/" in path_str:
                by_type["Workers"].append(gap)
            elif "/libs/" in path_str:
                by_type["Libraries"].append(gap)
            elif "/commands/" in path_str:
                by_type["Commands"].append(gap)
            else:
                by_type["Other"].append(gap)

        summary = []
        for module_type, type_gaps in by_type.items():
            avg_coverage = sum(
                g.coverage_info.coverage_percentage for g in type_gaps
            ) / len(type_gaps)
            summary.append(
                f"- **{module_type}**: {len(type_gaps)} modules, avg coverage: {avg_coverage:.1f}%"
            )

        return "\n".join(summary)


def main():
    """Main function for coverage gap analysis"""
    print("=== Coverage Gap Analyzer ===\n")

    project_root = Path.cwd()
    analyzer = GapAnalyzer(project_root)

    # Analyze gaps
    gaps = analyzer.analyze_gaps(min_coverage=70.0)

    print(f"Found {len(gaps)} modules with coverage below 70%")

    # Get top priority modules
    top_modules = analyzer.get_top_priority_modules(gaps, count=10)

    print("\nTop Priority Modules:")
    for i, module in enumerate(top_modules, 1):
        print(
            f"{i}. {module.file_path.name} - Score: {module.priority_score}, Coverage: {module.coverage_info.coverage_percentage:.1f}%"
        )

    # Generate report
    report = analyzer.generate_gap_report(gaps)

    report_path = project_root / "coverage_gap_analysis.md"
    with open(report_path, "w") as f:
        f.write(report)

    print(f"\nDetailed report saved to: {report_path}")

    return gaps


if __name__ == "__main__":
    main()
