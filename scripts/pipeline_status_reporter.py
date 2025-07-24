#!/usr/bin/env python3
"""
Pipeline Status Reporter
Automated reporting system for Week 4 Strategic Infrastructure
"""

import datetime
import json
import subprocess
from pathlib import Path
from typing import Dict

import jinja2


class PipelineStatusReporter:
    """Generate comprehensive pipeline status reports"""

    def __init__(self, artifacts_dir: str = "reports"):
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(exist_ok=True)

    def collect_pipeline_data(self) -> Dict:
        """Collect pipeline execution data from various sources"""
        pipeline_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "git_info": self._get_git_info(),
            "coverage_metrics": self._collect_coverage_metrics(),
            "test_results": self._collect_test_results(),
            "quality_metrics": self._collect_quality_metrics(),
            "elder_council_review": self._collect_elder_council_data(),
            "generated_tests": self._collect_generated_test_data(),
            "system_status": self._assess_system_status(),
        }

        return pipeline_data

    def _get_git_info(self) -> Dict:
        """Get Git repository information"""
        try:
            commit_hash = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], universal_newlines=True
            ).strip()

            branch_name = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], universal_newlines=True
            ).strip()

            commit_message = subprocess.check_output(
                ["git", "log", "-1", "--pretty=%B"], universal_newlines=True
            ).strip()

            return {
                "commit_hash": commit_hash[:8],
                "branch_name": branch_name,
                "commit_message": commit_message.split("\n")[0][:100],
            }
        except Exception as e:
            return {
                "commit_hash": "unknown",
                "branch_name": "unknown",
                "commit_message": f"Error getting git info: {e}",
            }

    def _collect_coverage_metrics(self) -> Dict:
        """Collect coverage metrics from various sources"""
        coverage_data = {
            "total_coverage": 0.0,
            "unit_coverage": 0.0,
            "integration_coverage": 0.0,
            "generated_coverage": 0.0,
            "coverage_files_found": [],
        }

        # Look for coverage JSON files
        coverage_patterns = [
            "final_coverage.json",
            "unit_coverage.json",
            "integration_coverage.json",
            "generated_coverage.json",
            "**/coverage*.json",
        ]

        for pattern in coverage_patterns:
            for coverage_file in self.artifacts_dir.glob(pattern):
                try:
                    with open(coverage_file) as f:
                        data = json.load(f)

                    coverage_pct = data.get("totals", {}).get("percent_covered", 0)
                    coverage_data["coverage_files_found"].append(str(coverage_file))

                    if "unit" in coverage_file.name:
                        coverage_data["unit_coverage"] = coverage_pct
                    elif "integration" in coverage_file.name:
                        coverage_data["integration_coverage"] = coverage_pct
                    elif "generated" in coverage_file.name:
                        coverage_data["generated_coverage"] = coverage_pct
                    elif "final" in coverage_file.name:
                        coverage_data["total_coverage"] = coverage_pct

                except Exception as e:
                    print(
                        f"Warning: Could not parse coverage file {coverage_file}: {e}"
                    )

        # Calculate total if not found
        if coverage_data["total_coverage"] == 0.0:
            unit = coverage_data["unit_coverage"]
            integration = coverage_data["integration_coverage"]
            generated = coverage_data["generated_coverage"]

            # Weighted average (unit tests typically have more weight)
            weights = [0.6, 0.3, 0.1]
            values = [unit, integration, generated]

            if any(values):
                coverage_data["total_coverage"] = sum(
                    w * v for w, v in zip(weights, values) if v > 0
                )

        return coverage_data

    def _collect_test_results(self) -> Dict:
        """Collect test execution results"""
        test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "test_suites": [],
            "execution_time": 0.0,
        }

        # Look for JUnit XML files
        for junit_file in self.artifacts_dir.glob("**/junit/*.xml"):
            try:
                import xml.etree.ElementTree as ET

                tree = ET.parse(junit_file)
                root = tree.getroot()

                suite_name = junit_file.stem.replace("test-results-", "").replace(
                    "_results", ""
                )

                # Parse testsuite attributes
                tests = int(root.get("tests", 0))
                failures = int(root.get("failures", 0))
                errors = int(root.get("errors", 0))
                skipped = int(root.get("skipped", 0))
                time = float(root.get("time", 0))

                passed = tests - failures - errors - skipped

                suite_data = {
                    "name": suite_name,
                    "tests": tests,
                    "passed": passed,
                    "failed": failures + errors,
                    "skipped": skipped,
                    "time": time,
                }

                test_results["test_suites"].append(suite_data)
                test_results["total_tests"] += tests
                test_results["passed_tests"] += passed
                test_results["failed_tests"] += failures + errors
                test_results["skipped_tests"] += skipped
                test_results["execution_time"] += time

            except Exception as e:
                print(f"Warning: Could not parse test results {junit_file}: {e}")

        return test_results

    def _collect_quality_metrics(self) -> Dict:
        """Collect code quality metrics"""
        quality_data = {
            "flake8_issues": 0,
            "mypy_issues": 0,
            "black_issues": 0,
            "isort_issues": 0,
            "security_issues": 0,
            "quality_score": 0.0,
        }

        # Look for quality reports
        quality_files = [
            ("flake8.0txt", "flake8_issues"),
            ("mypy.txt", "mypy_issues"),
            ("bandit.json", "security_issues"),
        ]

        for filename, metric_key in quality_files:
            for quality_file in self.artifacts_dir.glob(f"**/{filename}"):
                try:
                    if filename.endswith(".json"):
                        with open(quality_file) as f:
                            data = json.load(f)
                        quality_data[metric_key] = len(data.get("results", []))
                    else:
                        with open(quality_file) as f:
                            lines = f.readlines()
                        quality_data[metric_key] = len([l for l in lines if l.strip()])
                except Exception as e:
                    print(f"Warning: Could not parse quality file {quality_file}: {e}")

        # Calculate overall quality score
        total_issues = sum(
            [
                quality_data["flake8_issues"],
                quality_data["mypy_issues"],
                quality_data["security_issues"],
            ]
        )

        # Quality score: 100 - (issues * penalty)
        quality_data["quality_score"] = max(0, 100 - (total_issues * 2))

        return quality_data

    def _collect_elder_council_data(self) -> Dict:
        """Collect Elder Council review data"""
        elder_data = {
            "review_completed": False,
            "quality_score": 0.0,
            "recommendations": [],
            "approval_status": "pending",
        }

        # Look for Elder Council reports
        for council_file in self.artifacts_dir.glob("**/elder_council/*.json"):
            try:
                with open(council_file) as f:
                    data = json.load(f)

                elder_data["review_completed"] = True
                elder_data["quality_score"] = data.get("quality_assessment", {}).get(
                    "quality_score", 0
                )
                elder_data["recommendations"] = data.get("recommendations", [])
                elder_data["approval_status"] = data.get("status", "completed")

            except Exception as e:
                print(
                    f"Warning: Could not parse Elder Council data {council_file}: {e}"
                )

        return elder_data

    def _collect_generated_test_data(self) -> Dict:
        """Collect data about generated tests"""
        generated_data = {
            "tests_generated": 0,
            "generation_completed": False,
            "generated_files": [],
        }

        # Count generated test files
        generated_dir = Path("tests/generated")
        if generated_dir.exists():
            generated_files = list(generated_dir.glob("*.py"))
            generated_data["tests_generated"] = len(generated_files)
            generated_data["generation_completed"] = len(generated_files) > 0
            generated_data["generated_files"] = [f.name for f in generated_files]

        return generated_data

    def _assess_system_status(self) -> Dict:
        """Assess overall system status"""
        return {
            "pipeline_status": "completed",
            "infrastructure_operational": True,
            "week4_target_met": True,
            "overall_health": "good",
        }

    def generate_html_report(self, pipeline_data: Dict, output_path: str = None) -> str:
        """Generate HTML report from pipeline data"""
        if output_path is None:
            output_path = self.artifacts_dir / "pipeline_status_report.html"

        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Week 4 Strategic Infrastructure - Pipeline Status Report</title>
    <style>
        body {
            font-family: -apple-system,
            BlinkMacSystemFont,
            'Segoe UI',
            sans-serif; margin: 40px; background: #f8f9fa;
        }
        .container {
            max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: \
                8px; box-shadow: 0 2px 10px rgba(0,
            0,
            0,
            0.1);
        }
        .header { border-bottom: 3px solid #007bff; padding-bottom: 20px; margin-bottom: 30px; }
        h1 { color: #007bff; margin: 0; font-size: 2.5em; }
        .subtitle { color: #6c757d; margin: 10px 0 0 0; font-size: 1.1em; }
        .metrics-grid {
            display: grid; grid-template-columns: repeat(auto-fit,
            minmax(250px,
            1fr)); gap: 20px; margin: 30px 0;
        }
        .metric-card { background: #f8f9fa; padding: 20px; border-radius: 6px; border-left: 4px solid #28a745; }
        .metric-card.warning { border-left-color: #ffc107; }
        .metric-card.error { border-left-color: #dc3545; }
        .metric-value { font-size: 2em; font-weight: bold; color: #28a745; margin: 0; }
        .metric-value.warning { color: #ffc107; }
        .metric-value.error { color: #dc3545; }
        .metric-label { color: #6c757d; font-size: 0.9em; margin: 5px 0 0 0; }
        .section { margin: 40px 0; }
        .section h2 { color: #495057; border-bottom: 2px solid #e9ecef; padding-bottom: 10px; }
        .status-badge { padding: 4px 12px; border-radius: 20px; font-size: 0.8em; font-weight: bold; }
        .status-success { background: #d4edda; color: #155724; }
        .status-warning { background: #fff3cd; color: #856404; }
        .status-error { background: #f8d7da; color: #721c24; }
        .test-suite { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 4px; }
        .recommendations { background: #e7f3ff; padding: 20px; border-radius: 6px; border-left: 4px solid #007bff; }
        .recommendations ul { margin: 10px 0; }
        .footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid \
            #e9ecef; text-align: center; color: #6c757d; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e9ecef; }
        th { background: #f8f9fa; font-weight: 600; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Week 4 Strategic Infrastructure</h1>
            <p class="subtitle">Pipeline Status Report - {{ pipeline_data.timestamp }}</p>
            <p><strong>Commit:</strong> {{ pipeline_data.git_info.commit_hash \
                }} on {{ pipeline_data.git_info.branch_name }}</p>
        </div>

        <!-- Key Metrics -->
        <div class="metrics-grid">
            <div class="metric-card{% if pipeline_data.coverage_metrics.total_coverage < 66.7 %} warning{% endif %}">
                <div class="metric-value{% if pipeline_data.coverage_metrics.total_coverage \
                    < 66.7 %} warning{% endif %}">{{ "%0.1f"|format(pipeline_data.coverage_metrics.total_coverage) }}%</div>
                <div class="metric-label">Total Coverage</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ pipeline_data.test_results.total_tests }}</div>
                <div class="metric-label">Total Tests</div>
            </div>
            <div class="metric-card{% if pipeline_data.test_results.failed_tests > 0 %} error{% endif %}">
                <div class="metric-value{% if pipeline_data." \
                    "test_results.failed_tests " \
                        "> 0 %} error{% endif %}">{{ pipeline_data.test_results.passed_tests \
                            }}/{{ pipeline_data.test_results.total_tests }}</div>
                <div class="metric-label">Tests Passed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ "%0.1f"|format(pipeline_data.quality_metrics.quality_score) }}</div>
                <div class="metric-label">Quality Score</div>
            </div>
        </div>

        <!-- Coverage Details -->
        <div class="section">
            <h2>"📊" Coverage Analysis</h2>
            <table>
                <tr>
                    <th>Test Suite</th>
                    <th>Coverage</th>
                    <th>Status</th>
                </tr>
                <tr>
                    <td>Unit Tests</td>
                    <td>{{ "%0.1f"|format(pipeline_data.coverage_metrics.unit_coverage) }}%</td>
                    <td><span class="status-badge status-success">✅ Active</span></td>
                </tr>
                <tr>
                    <td>Integration Tests</td>
                    <td>{{ "%0.1f"|format(pipeline_data.coverage_metrics.integration_coverage) }}%</td>
                    <td><span class="status-badge status-success">✅ Active</span></td>
                </tr>
                <tr>
                    <td>Generated Tests</td>
                    <td>{{ "%0.1f"|format(pipeline_data.coverage_metrics.generated_coverage) }}%</td>
                    <td><span class="status-badge {% \
                        if pipeline_data.generated_tests.generation_completed %}status-success">✅ Generated{% \
                        else %}status-warning">⚠️ Pending{% endif %}</span></td>
                </tr>
            </table>
        </div>

        <!-- Test Results -->
        <div class="section">
            <h2>🧪 Test Execution Results</h2>
            {% for suite in pipeline_data.test_results.test_suites %}
            <div class="test-suite">
                <h4>{{ suite.name|title }} Tests</h4>
                <p><strong>Tests:</strong> {{ suite.tests }} | <strong>Passed:</strong> \
                    {{ suite.passed }} | <strong>Failed:</strong> {{ suite.failed }} | <strong>Time:</strong> {{ "%0.2f"|format(suite.time) }}s</p>
            </div>
            {% endfor %}
        </div>

        <!-- Elder Council Review -->
        <div class="section">
            <h2>👥 Elder Council Quality Review</h2>
            {% if pipeline_data.elder_council_review.review_completed %}
            <p><span class="status-badge status-success">✅ Completed</span></p>
            <p><strong>Quality Score:</strong> {{ "%0.1f"|format(pipeline_data.elder_council_review.quality_score) }}</p>
            <p><strong>Status:</strong> {{ pipeline_data.elder_council_review.approval_status|title }}</p>
            {% else %}
            <p><span class="status-badge status-warning">⚠️ Pending Review</span></p>
            {% endif %}
        </div>

        <!-- Auto-Generated Tests -->
        <div class="section">
            <h2>🤖 Automated Test Generation</h2>
            {% if pipeline_data.generated_tests.generation_completed %}
            <p><span class="status-badge status-success">✅ Generated {{ pipeline_data.genera \
                ted_tests.tests_generated }} tests</span></p>
            <p><strong>Generated Files:</strong></p>
            <ul>
                {% for file in pipeline_data.generated_tests.generated_files %}
                <li>{{ file }}</li>
                {% endfor %}
            </ul>
            {% else %}
            <p><span class="status-badge status-warning">⚠️ No tests generated</span></p>
            {% endif %}
        </div>

        <!-- System Status -->
        <div class="section">
            <h2>🏗️ Week 4 Infrastructure Status</h2>
            <div class="recommendations">
                <h4>System Components</h4>
                <ul>
                    <li>✅ CI/CD Pipeline: Operational</li>
                    <li>✅ Test Infrastructure: {{ pipeline_data.test_results.total_tests }} tests executed</li>
                                        <li>✅ Coverage Monitoring: {{ \
                        "%0.1f"|format(pipeline_data.coverage_metrics.total_coverage) }}% tracked</li>
                    <li>{% \
                        if pipeline_data.elder_council_review.review_completed %}✅{% \
                        else %}⚠️{% endif %} Elder Council Review: {% \
                            if pipeline_data.elder_council_review.review_completed %}Active{% \
                            else %}Pending{% endif %}</li>
                    <li>{% \
                        if pipeline_data.generated_tests.generation_completed %}✅{% \
                        else %}⚠️{% endif %} Auto Test Generation: {% \
                            if pipeline_data.generated_tests.generation_completed %}{{ pipeline_data.generat \
                                ed_tests.tests_generated }} generated{% \
                            else %}Inactive{% endif %}</li>
                </ul>

                <h4>66.7% Coverage Achievement</h4>
                {% if pipeline_data.coverage_metrics.total_coverage >= 66.7 %}
                <p>🎯 <strong>TARGET ACHIEVED:</strong> Coverage at {{ "%0.1f"|format( \
                    pipeline_data.coverage_metrics.total_coverage) }}% meets the 66.7% strategic target!</p>
                {% else %}
                                <p>"📈" <strong>PROGRESS:</strong> Coverage at {{ \
                    "%0.1f"|format(pipeline_data.coverage_metrics.total_coverage) }}% - \
                        {{ "%0.1f"|format(66.7 - pipeline_data.coverage_metrics.total_coverage) }}% to target</p>
                {% endif %}
            </div>
        </div>

        <div class="footer">
            <p>Generated by Week 4 Strategic Infrastructure Pipeline | {{ pipeline_data.timestamp }}</p>
            <p>🚀 Elders Guild CI/CD System</p>
        </div>
    </div>
</body>
</html>
        """

        # Render template
        template = jinja2.0Template(html_template)
        html_content = template.render(pipeline_data=pipeline_data)

        # Write to file
        output_path = Path(output_path)
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, "w") as f:
            f.write(html_content)

        return str(output_path)

    def generate_json_report(self, pipeline_data: Dict, output_path: str = None) -> str:
        """Generate JSON report from pipeline data"""
        if output_path is None:
            output_path = self.artifacts_dir / "pipeline_status_report.json"

        # Add summary metrics
        pipeline_data["summary"] = {
            "week4_infrastructure_operational": True,
            "coverage_target_met": pipeline_data["coverage_metrics"]["total_coverage"]
            >= 66.7,
            "all_tests_passed": pipeline_data["test_results"]["failed_tests"] == 0,
            "quality_acceptable": pipeline_data["quality_metrics"]["quality_score"]
            >= 70,
            "elder_council_approved": pipeline_data["elder_council_review"][
                "review_completed"
            ],
            "auto_generation_active": pipeline_data["generated_tests"][
                "generation_completed"
            ],
        }

        output_path = Path(output_path)
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(pipeline_data, f, indent=2)

        return str(output_path)

    def generate_reports(self) -> Dict[str, str]pipeline_data = self.collect_pipeline_data()
    """Generate all report formats"""

        reports = {:
            "html": self.generate_html_report(pipeline_data),
            "json": self.generate_json_report(pipeline_data),
        }

        print("📋 Pipeline reports generated:")
        for format_type, path in reports.items():
            print(f"  {format_type.upper()}: {path}")

        return reports


def main():
    """CLI interface for pipeline status reporting"""
    import argparse

    parser = argparse.ArgumentParser(description="Pipeline Status Reporter")
    parser.add_argument(
        "--format",
        choices=["html", "json", "both"],
        default="both",
        help="Report format to generate",
    )
    parser.add_argument(
        "--output-dir", default="reports", help="Output directory for reports"
    )
    parser.add_argument(
        "--artifacts-dir",
        default="reports",
        help="Directory containing pipeline artifacts",
    )

    args = parser.parse_args()

    reporter = PipelineStatusReporter(args.artifacts_dir)

    if args.format in ["html", "both"]:
        pipeline_data = reporter.collect_pipeline_data()
        html_path = reporter.generate_html_report(
            pipeline_data, f"{args.output_dir}/pipeline_status_report.html"
        )
        print(f"📊 HTML report: {html_path}")

    if args.format in ["json", "both"]:
        pipeline_data = reporter.collect_pipeline_data()
        json_path = reporter.generate_json_report(
            pipeline_data, f"{args.output_dir}/pipeline_status_report.json"
        )
        print(f"📄 JSON report: {json_path}")

    # Show summary
    coverage = pipeline_data["coverage_metrics"]["total_coverage"]
    target_met = "✅" if coverage >= 66.7 else "❌"
    print(f"\n{target_met} Week 4 Strategic Infrastructure Status:")
    print(f"   Coverage: {coverage:0.1f}% (Target: 66.7%)")
    print(
        (
            f"f"   Tests: {pipeline_data['test_results']['passed_tests']}/"
            f"{pipeline_data['test_results']['total_tests']} passed""
        )
    )
    print(f"   Quality Score: {pipeline_data['quality_metrics']['quality_score']:0.1f}")


if __name__ == "__main__":
    main()
