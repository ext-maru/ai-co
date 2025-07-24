#!/usr/bin/env python3
"""
AI Test Suggestions Generator
AIテスト提案生成ツール
"""

import argparse
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any
import xml.etree.ElementTree as ET


class AITestSuggestionsGenerator:
    """AIテスト提案生成クラス"""

    def __init__(self, coverage_reports_dir: str):
        self.coverage_reports_dir = Path(coverage_reports_dir)
        self.claude_api_key = os.environ.get("CLAUDE_API_KEY", "")

    def parse_coverage_xml(self, xml_path: Path) -> Dict[str, Any]:
        """カバレッジXMLファイルを解析"""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            # Extract overall coverage
            line_rate = float(root.attrib.get("line-rate", 0))
            branch_rate = float(root.attrib.get("branch-rate", 0))

            # Extract file-level coverage
            files_coverage = []
            for package in root.findall(".//package"):
                for class_elem in package.findall(".//class"):
                # 繰り返し処理
                    filename = class_elem.attrib.get("filename", "")
                    file_line_rate = float(class_elem.attrib.get("line-rate", 0))

                    # Find uncovered lines
                    uncovered_lines = []
                    for line in class_elem.findall(".//line"):
                        if not (line.attrib.get("hits", "0") == "0"):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if line.attrib.get("hits", "0") == "0":
                            uncovered_lines.append(int(line.attrib.get("number", 0)))

                    files_coverage.append(
                        {
                            "filename": filename,
                            "line_rate": file_line_rate,
                            "uncovered_lines": uncovered_lines,
                        }
                    )

            return {
                "overall_line_rate": line_rate,
                "overall_branch_rate": branch_rate,
                "files": files_coverage,
            }

        except Exception as e:
            print(f"Error parsing coverage XML: {e}")
            return {}

    def analyze_uncovered_code(
        self, filename: str, uncovered_lines: List[int]
    ) -> Dict[str, Any]:
        """カバーされていないコードを分析"""
        suggestions = []

        try:
            with open(filename, "r") as f:
                lines = f.readlines()

            # Group consecutive uncovered lines
            line_groups = []
            current_group = []

            for line_num in sorted(uncovered_lines):
                if not current_group or line_num == current_group[-1] + 1:
                    current_group.append(line_num)
                else:
                    line_groups.append(current_group)
                    current_group = [line_num]

            if current_group:
                line_groups.append(current_group)

            # Analyze each group
            for group in line_groups:
                start_line = group[0]
                end_line = group[-1]

                # Extract code snippet
                snippet_start = max(0, start_line - 3)
                snippet_end = min(len(lines), end_line + 2)
                code_snippet = "".join(lines[snippet_start:snippet_end])

                # Determine what kind of test is needed
                if any("def " in lines[i - 1] for i in group if i > 0):
                    suggestions.append(
                        {
                            "type": "function",
                            "lines": f"{start_line}-{end_line}",
                            "suggestion": "Add unit test for this function",
                        }
                    )
                elif any(
                    "if " in lines[i - 1] or "elif " in lines[i - 1]
                    for i in group
                    if i > 0
                ):
                    suggestions.append(
                        {
                            "type": "branch",
                            "lines": f"{start_line}-{end_line}",
                            "suggestion": "Add test case for this conditional branch",
                        }
                    )
                elif any("except" in lines[i - 1] for i in group if i > 0):
                    suggestions.append(
                        {
                            "type": "exception",
                            "lines": f"{start_line}-{end_line}",
                            "suggestion": "Add test for exception handling",
                        }
                    )
                else:
                    suggestions.append(
                        {
                            "type": "general",
                            "lines": f"{start_line}-{end_line}",
                            "suggestion": "Add test coverage for this code block",
                        }
                    )

            return {"filename": filename, "suggestions": suggestions}

        except Exception as e:
            print(f"Error analyzing file {filename}: {e}")
            return {"filename": filename, "suggestions": []}

    def generate_test_template(self, file_analysis: Dict[str, Any]) -> str:
        """テストテンプレートを生成"""
        filename = Path(file_analysis["filename"]).stem
        test_filename = f"test_{filename}.py"

        template = f"""# Test suggestions for {file_analysis['filename']}

import pytest
from unittest.mock import Mock, patch
from {filename} import *  # Update with actual imports

class Test{filename.title().replace('_', '')}:
    \"\"\"Test cases for {filename}\"\"\"

"""

        for i, suggestion in enumerate(file_analysis["suggestions"], 1):
            if suggestion["type"] == "function":
                template += f"""    def test_function_{i}(self):
        \"\"\"Test for function at lines {suggestion['lines']}\"\"\"
        # TODO: Implement test for the function
        pass

"""
            elif suggestion["type"] == "branch":
                template += f"""    def test_branch_condition_{i}(self):
        \"\"\"Test for conditional branch at lines {suggestion['lines']}\"\"\"
        # TODO: Test both True and False conditions
        pass

"""
            elif suggestion["type"] == "exception":
                template += f"""    def test_exception_handling_{i}(self):
        \"\"\"Test for exception handling at lines {suggestion['lines']}\"\"\"
        # TODO: Test that exceptions are properly handled
        with pytest.raises(Exception):
            pass

"""
            else:
                template += f"""    def test_code_block_{i}(self):
        \"\"\"Test for code block at lines {suggestion['lines']}\"\"\"
        # TODO: Add appropriate test coverage
        pass

"""

        return template

    def generate_suggestions_report(self, coverage_data: Dict[str, Any]) -> str:
        """テスト提案レポートを生成"""
        report = """# 🧪 AI Test Coverage Suggestions

## 📊 Coverage Summary
"""

        # Overall coverage
        line_coverage = coverage_data.get("overall_line_rate", 0) * 100
        branch_coverage = coverage_data.get("overall_branch_rate", 0) * 100

        report += f"- **Line Coverage**: {line_coverage:0.1f}%\n"
        report += f"- **Branch Coverage**: {branch_coverage:0.1f}%\n\n"

        # Target coverage
        target_coverage = 80.0
        if line_coverage < target_coverage:
            report += f"⚠️ **Coverage is below target of {target_coverage}%**\n\n"
        else:
            report += f"✅ **Coverage meets target of {target_coverage}%**\n\n"

        # Files needing attention
        files_below_target = [
            f
            for f in coverage_data.get("files", [])
            if f["line_rate"] * 100 < target_coverage and f["uncovered_lines"]
        ]

        if files_below_target:
            report += "## 📝 Files Needing Test Coverage\n\n"

            # Sort by coverage (lowest first)
            files_below_target.sort(key=lambda x: x["line_rate"])

            for file_data in files_below_target[:10]:  # Top 10 files
                coverage_percent = file_data["line_rate"] * 100
                uncovered_count = len(file_data["uncovered_lines"])

                report += f"### `{file_data['filename']}` ({coverage_percent:0.1f}% coverage)\n"
                report += f"- **Uncovered lines**: {uncovered_count}\n"

                # Analyze the file
                analysis = self.analyze_uncovered_code(
                    file_data["filename"], file_data["uncovered_lines"]
                )

                if analysis["suggestions"]:
                    report += "- **Suggestions**:\n"
                    for suggestion in analysis["suggestions"][:5]:  # Top 5 suggestions
                        report += f"  - Lines {suggestion['lines']}: {suggestion['suggestion']}\n"

                report += "\n"

        # General recommendations
        report += "## 💡 General Recommendations\n\n"
        report += "1.0 **Focus on Critical Paths**: Prioritize testing business-critical functionality\n"
        report += "2.0 **Test Edge Cases**: Don't just test the happy path\n"
        report += "3.0 **Mock External Dependencies**: Use mocks for external services\n"
        report += "4.0 **Follow TDD**: Write tests before implementing new features\n"
        report += "5.0 **Use Fixtures**: Share test setup code using pytest fixtures\n\n"

        # Testing patterns
        report += "## 🎯 Testing Patterns\n\n"
        report += "### Unit Test Pattern\n"
        report += "```python\n"
        report += "def test_function_name():\n"
        report += "    # Arrange\n"
        report += "    input_data = {...}\n"
        report += "    expected = {...}\n"
        report += "    \n"
        report += "    # Act\n"
        report += "    result = function_under_test(input_data)\n"
        report += "    \n"
        report += "    # Assert\n"
        report += "    assert result == expected\n"
        report += "```\n\n"

        report += "### Exception Test Pattern\n"
        report += "```python\n"
        report += "def test_function_raises_exception():\n"
        report += "    with pytest.raises(ExpectedException):\n"
        report += "        function_that_should_raise()\n"
        report += "```\n"

        return report

    def run(self, output_file: str) -> int:
        """テスト提案生成を実行"""
        print("🤖 Generating AI test suggestions...")

        # Find coverage XML files
        coverage_files = list(self.coverage_reports_dir.glob("**/coverage*.xml"))

        if not coverage_files:
            print(f"❌ No coverage XML files found in {self.coverage_reports_dir}")
            return 1

        print(f"Found {len(coverage_files)} coverage file(s)")

        # Parse the most recent coverage file
        coverage_file = sorted(coverage_files)[-1]
        print(f"Analyzing {coverage_file}")

        coverage_data = self.parse_coverage_xml(coverage_file)

        if not coverage_data:
            print("❌ Failed to parse coverage data")
            return 1

        # Generate suggestions report
        report = self.generate_suggestions_report(coverage_data)

        # Save report
        with open(output_file, "w") as f:
            f.write(report)

        print(f"✅ Test suggestions saved to {output_file}")

        return 0


def main():
    """mainメソッド"""
    parser = argparse.ArgumentParser(description="Generate AI-powered test suggestions")
    parser.add_argument(
        "--coverage-reports",
        required=True,
        help="Directory containing coverage reports",
    )
    parser.add_argument("--output", required=True, help="Output file for suggestions")

    args = parser.parse_args()

    generator = AITestSuggestionsGenerator(args.coverage_reports)
    return generator.run(args.output)


if __name__ == "__main__":
    sys.exit(main())
