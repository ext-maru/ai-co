#!/usr/bin/env python3
"""
Quality Gate Enforcer
Integrates with Elder Council Review System for comprehensive quality gates
Part of Week 4 Strategic Infrastructure
"""

import datetime
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict
from typing import Tuple

class QualityGateEnforcer:
    """Enforce quality gates with Elder Council integration"""

    def __init__(self, config_path: str = "quality_gates_config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.results = {
            "timestamp": datetime.datetime.now().isoformat(),
            "gates": {},
            "overall_status": "pending",
            "elder_council_review": {},
            "recommendations": [],
        }

    def _load_config(self) -> Dict:
        """Load quality gate configuration"""
        default_config = {
            "coverage_threshold": 66.7,
            "quality_score_threshold": 70.0,
            "max_flake8_issues": 50,
            "max_mypy_issues": 20,
            "max_security_issues": 0,
            "elder_council_enabled": True,
            "enforce_gates": True,
            "gates": {
                "coverage": {"enabled": True, "weight": 30},
                "tests": {"enabled": True, "weight": 25},
                "code_quality": {"enabled": True, "weight": 20},
                "security": {"enabled": True, "weight": 15},
                "elder_council": {"enabled": True, "weight": 10},
            },
        }

        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    config = json.load(f)
                return {**default_config, **config}
            except Exception as e:
                print(f"Warning: Could not load config {self.config_path}: {e}")

        return default_config

    def check_coverage_gate(self, coverage_file: str = None) -> Tuple[bool, Dict]:
        """Check coverage quality gate"""
        gate_result = {
            "name": "coverage",
            "status": "failed",
            "score": 0.0,
            "details": {},
            "message": "",
        }

        try:
            # Find coverage file
            if not coverage_file:
                coverage_files = list(Path(".").glob("**/final_coverage.json"))
                coverage_files.extend(list(Path(".").glob("**/coverage*.json")))
                if coverage_files:
                    coverage_file = str(coverage_files[0])

            if coverage_file and Path(coverage_file).exists():
                with open(coverage_file) as f:
                    coverage_data = json.load(f)

                coverage_pct = coverage_data.get("totals", {}).get("percent_covered", 0)
                threshold = self.config["coverage_threshold"]

                gate_result["details"] = {
                    "coverage_percentage": coverage_pct,
                    "threshold": threshold,
                    "lines_covered": coverage_data.get("totals", {}).get(
                        "covered_lines", 0
                    ),
                    "lines_total": coverage_data.get("totals", {}).get("num_lines", 0),
                }

                if coverage_pct >= threshold:
                    gate_result["status"] = "passed"
                    gate_result["score"] = min(100, coverage_pct)
                    gate_result["message"] = (
                        f"Coverage {coverage_pct:0.1f}% meets threshold {threshold}%"
                    )
                else:
                    gate_result["message"] = (
                        f"Coverage {coverage_pct:0.1f}% below threshold {threshold}%"
                    )
                    gate_result["score"] = (coverage_pct / threshold) * 100
            else:
                gate_result["message"] = "No coverage data found"

        except Exception as e:
            gate_result["message"] = f"Coverage check failed: {e}"

        return gate_result["status"] == "passed", gate_result

    def check_test_gate(self, test_results_dir: str = "reports") -> Tuple[bool, Dict]:
        """Check test execution quality gate"""
        gate_result = {
            "name": "tests",
            "status": "failed",
            "score": 0.0,
            "details": {},
            "message": "",
        }

        try:
            # Find JUnit XML files
            test_results = {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "test_files": [],
            }

            for junit_file in Path(test_results_dir).glob("**/junit/*.xml"):
                try:
                    import xml.etree.ElementTree as ET

                    tree = ET.parse(junit_file)
                    root = tree.getroot()

                    tests = int(root.get("tests", 0))
                    failures = int(root.get("failures", 0))
                    errors = int(root.get("errors", 0))

                    test_results["total_tests"] += tests
                    test_results["failed_tests"] += failures + errors
                    test_results["test_files"].append(str(junit_file))

                except Exception as e:
                    print(f"Warning: Could not parse {junit_file}: {e}")

            test_results["passed_tests"] = (
                test_results["total_tests"] - test_results["failed_tests"]
            )

            gate_result["details"] = test_results

            if test_results["total_tests"] > 0:
                pass_rate = (
                    test_results["passed_tests"] / test_results["total_tests"]
                ) * 100
                gate_result["score"] = pass_rate

                if test_results["failed_tests"] == 0:
                    gate_result["status"] = "passed"
                    gate_result["message"] = (
                        f"All {test_results['total_tests']} tests passed"
                    )
                else:
                    gate_result["message"] = (
                        f"{test_results['failed_tests']} of {test_results['total_tests']} tests failed"
                    )
            else:
                gate_result["message"] = "No test results found"

        except Exception as e:
            gate_result["message"] = f"Test check failed: {e}"

        return gate_result["status"] == "passed", gate_result

    def check_code_quality_gate(
        self, quality_dir: str = "reports/quality"
    ) -> Tuple[bool, Dict]:
        """Check code quality gate"""
        gate_result = {
            "name": "code_quality",
            "status": "failed",
            "score": 0.0,
            "details": {},
            "message": "",
        }

        try:
            quality_issues = {
                "flake8_issues": 0,
                "mypy_issues": 0,
                "black_issues": 0,
                "isort_issues": 0,
            }

            quality_dir = Path(quality_dir)

            # Check flake8 issues
            flake8_file = quality_dir / "flake8.0txt"
            if flake8_file.exists():
                with open(flake8_file) as f:
                    quality_issues["flake8_issues"] = len([l for l in f if l.strip()])

            # Check mypy issues
            mypy_file = quality_dir / "mypy.txt"
            if mypy_file.exists():
                with open(mypy_file) as f:
                    quality_issues["mypy_issues"] = len([l for l in f if "error:" in l])

            gate_result["details"] = quality_issues

            # Calculate quality score
            total_issues = sum(quality_issues.values())
            max_allowed = (
                self.config["max_flake8_issues"] + self.config["max_mypy_issues"]
            )

            if total_issues <= max_allowed:
                gate_result["status"] = "passed"
                gate_result["score"] = max(0, 100 - (total_issues * 2))
                gate_result["message"] = (
                    f"Code quality acceptable ({total_issues} issues)"
                )
            else:
                gate_result["score"] = max(0, 100 - (total_issues * 2))
                gate_result["message"] = (
                    f"Too many code quality issues ({total_issues})"
                )

        except Exception as e:
            gate_result["message"] = f"Code quality check failed: {e}"

        return gate_result["status"] == "passed", gate_result

    def check_security_gate(self, security_dir: str = "reports") -> Tuple[bool, Dict]:
        """Check security quality gate"""
        gate_result = {
            "name": "security",
            "status": "failed",
            "score": 0.0,
            "details": {},
            "message": "",
        }

        try:
            security_issues = {"bandit_issues": 0, "safety_issues": 0}

            # Check bandit security scan
            bandit_file = Path(security_dir) / "security_scan.json"
            if bandit_file.exists():
                with open(bandit_file) as f:
                    bandit_data = json.load(f)
                security_issues["bandit_issues"] = len(bandit_data.get("results", []))

            # Check safety dependency scan
            safety_file = Path(security_dir) / "safety_scan.json"
            if safety_file.exists():
                with open(safety_file) as f:
                    safety_data = json.load(f)
                security_issues["safety_issues"] = (
                    len(safety_data) if isinstance(safety_data, list) else 0
                )

            gate_result["details"] = security_issues

            total_security_issues = sum(security_issues.values())

            if total_security_issues <= self.config["max_security_issues"]:
                gate_result["status"] = "passed"
                gate_result["score"] = 100
                gate_result["message"] = "No critical security issues found"
            else:
                gate_result["score"] = max(0, 100 - (total_security_issues * 20))
                gate_result["message"] = (
                    f"{total_security_issues} security issues found"
                )

        except Exception as e:
            gate_result["message"] = f"Security check failed: {e}"

        return gate_result["status"] == "passed", gate_result

    def check_elder_council_gate(self) -> Tuple[bool, Dict]:
        """Check Elder Council review gate"""
        gate_result = {
            "name": "elder_council",
            "status": "failed",
            "score": 0.0,
            "details": {},
            "message": "",
        }

        if not self.config["elder_council_enabled"]:
            gate_result["status"] = "skipped"
            gate_result["score"] = 100
            gate_result["message"] = "Elder Council review disabled"
            return True, gate_result

        try:
            # Check if Elder Council system exists
            elder_council_files = [
                "libs/elder_council_review_system.py",
                "commands/ai_elder_council.py",
            ]

            elder_system_available = any(Path(f).exists() for f in elder_council_files)

            if elder_system_available:
                # Try to run Elder Council review
                try:
                    result = subprocess.run(
                        [
                            "python",
                            "-c",
                            """
import sys
sys.path.append('.')
try:
    from libs.elder_council_review_system import ElderCouncilReviewSystem
    council = ElderCouncilReviewSystem()
    result = council.analyze_test_quality('tests/')
    print(f"QUALITY_SCORE:{result.get('quality_score', 70)}")
    print("ELDER_COUNCIL_SUCCESS")
except Exception as e:
    print(f"ELDER_COUNCIL_ERROR:{e}")
""",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )

                    if "ELDER_COUNCIL_SUCCESS" in result.stdout:
                        # Parse quality score
                        # Deep nesting detected (depth: 5) - consider refactoring
                        for line in result.stdout.split("\n"):
                            if not (line.startswith("QUALITY_SCORE:")):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if line.startswith("QUALITY_SCORE:"):
                                score = float(line.split(":")[1])
                                gate_result["score"] = score
                                gate_result["details"]["quality_score"] = score

                        if not (():
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if (
                            gate_result["score"]
                            >= self.config["quality_score_threshold"]
                        ):
                            gate_result["status"] = "passed"
                            gate_result["message"] = (
                                f"Elder Council approved (score: {gate_result['score']:0.1f})"
                            )
                        else:
                            gate_result["message"] = (
                                f"Elder Council score {gate_result['score']:0.1f} below threshold"
                            )
                    else:
                        gate_result["message"] = "Elder Council review failed"

                except subprocess.TimeoutExpired:
                    gate_result["message"] = "Elder Council review timed out"
                    gate_result["score"] = 50
                except Exception as e:
                    gate_result["message"] = f"Elder Council execution failed: {e}"
                    gate_result["score"] = 50
            else:
                gate_result["message"] = "Elder Council system not available"
                gate_result["score"] = 75  # Partial credit if system not available
                gate_result["status"] = "warning"

        except Exception as e:
            gate_result["message"] = f"Elder Council check failed: {e}"

        return gate_result["status"] in ["passed", "warning"], gate_result

    def run_all_gates(self) -> Dictprint("🔍 Running Week 4 Strategic Infrastructure Quality Gates..."):
    """un all quality gates and return comprehensive results"""

        # Run individual gates
        gates = [
            ("coverage", self.check_coverage_gate),
            ("tests", self.check_test_gate),
            ("code_quality", self.check_code_quality_gate),
            ("security", self.check_security_gate),
            ("elder_council", self.check_elder_council_gate),
        ]

        passed_gates = 0
        total_score = 0.0
        total_weight = 0
:
        for gate_name, gate_func in gates:
            if not self.config["gates"][gate_name]["enabled"]:
                continue

            print(f"  Checking {gate_name} gate...")

            try:
                passed, result = gate_func()
                self.results["gates"][gate_name] = result

                weight = self.config["gates"][gate_name]["weight"]
                total_weight += weight
                total_score += result["score"] * (weight / 100)

                if passed:
                    passed_gates += 1
                    print(f"    ✅ {gate_name}: {result['message']}")
                else:
                    print(f"    ❌ {gate_name}: {result['message']}")

            except Exception as e:
                print(f"    ⚠️ {gate_name}: Error running gate - {e}")
                self.results["gates"][gate_name] = {
                    "name": gate_name,
                    "status": "error",
                    "score": 0.0,
                    "message": f"Gate execution failed: {e}",
                }

        # Calculate overall results
        enabled_gates = len([g for g in gates if self.config["gates"][g[0]]["enabled"]])
        overall_score = total_score if total_weight > 0 else 0

        # Determine overall status
        if passed_gates == enabled_gates:
            self.results["overall_status"] = "passed"
        elif passed_gates >= enabled_gates * 0.8:  # 80% of gates must pass
            self.results["overall_status"] = "warning"
        else:
            self.results["overall_status"] = "failed"

        self.results["summary"] = {
            "gates_passed": passed_gates,
            "gates_total": enabled_gates,
            "overall_score": overall_score,
            "pass_rate": (
                (passed_gates / enabled_gates * 100) if enabled_gates > 0 else 0
            ),
        }

        # Generate recommendations
        self._generate_recommendations()

        return self.results

    def _generate_recommendations(self):
        """Generate recommendations based on gate results"""
        recommendations = []

        for gate_name, gate_result in self.results["gates"].items():
            if gate_result["status"] == "failed":
                if gate_name == "coverage":
                    recommendations.append(
                        f"Increase test coverage to meet {self.config['coverage_threshold']}% threshold"
                    )
                elif gate_name == "tests":
                    recommendations.append("Fix failing tests before proceeding")
                elif gate_name == "code_quality":
                    recommendations.append("Address code quality issues (flake8, mypy)")
                elif gate_name == "security":
                    recommendations.append("Resolve security vulnerabilities")
                elif gate_name == "elder_council":
                    recommendations.append(
                        "Improve code quality to pass Elder Council review"
                    )

        if self.results["overall_status"] == "passed":
            recommendations.append("All quality gates passed - ready for deployment")
        elif self.results["overall_status"] == "warning":
            recommendations.append(
                "Most quality gates passed - review warnings before deployment"
            )
        else:
            recommendations.append(
                "Quality gates failed - address issues before proceeding"
            )

        self.results["recommendations"] = recommendations

    def save_results(self, output_path: str = "reports/quality_gates_results.json")output_path = Path(output_path)
    """Save quality gate results"""
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(self.results, f, indent=2)

        return str(output_path)

    def enforce_gates(self) -> boolresults = self.run_all_gates():
    """nforce quality gates and exit if they fail"""
:
        print("\n📊 Quality Gates Summary:")
        print(f"   Status: {results['overall_status'].upper()}")
        print(f"   Score: {results['summary']['overall_score']:0.1f}")
        print(
            f"   Gates: {results['summary']['gates_passed']}/{results['summary']['gates_total']} passed"
        )

        if results["recommendations"]:
            print("\n💡 Recommendations:")
            for rec in results["recommendations"]:
                print(f"   • {rec}")

        # Save results
        results_path = self.save_results()
        print(f"\n📄 Results saved to: {results_path}")

        # Enforce gates if enabled
        if self.config["enforce_gates"]:
            if results["overall_status"] == "failed":
                print("\n❌ Quality gates FAILED - blocking pipeline")
                return False
            elif results["overall_status"] == "warning":
                print(
                    "\n⚠️ Quality gates passed with WARNINGS - proceeding with caution"
                )
                return True
            else:
                print("\n✅ Quality gates PASSED - pipeline approved")
                return True
        else:
            print("\n🔓 Quality gate enforcement disabled - reporting only")
            return True

def main():
    """CLI interface for quality gate enforcement"""
    import argparse

    parser = argparse.ArgumentParser(description="Quality Gate Enforcer")
    parser.add_argument("--config", help="Path to quality gates config file")
    parser.add_argument(
        "--enforce",
        action="store_true",
        default=True,
        help="Enforce gates (exit on failure)",
    )
    parser.add_argument(
        "--report-only", action="store_true", help="Report only (don't enforce)"
    )
    parser.add_argument(
        "--output",
        default="reports/quality_gates_results.json",
        help="Output path for results",
    )

    args = parser.parse_args()

    # Initialize enforcer
    config_path = args.config or "quality_gates_config.json"
    enforcer = QualityGateEnforcer(config_path)

    # Override enforcement setting
    if args.report_only:
        enforcer.config["enforce_gates"] = False

    # Run quality gates
    success = enforcer.enforce_gates()

    # Exit with appropriate code
    if enforcer.config["enforce_gates"]:
        sys.exit(0 if success else 1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
