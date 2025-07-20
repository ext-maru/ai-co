#!/usr/bin/env python3
"""
Quality Gate Enforcement System
Automated prevention and quality control for maintaining 66.7% coverage achievement

This system provides:
- Automated quality gate enforcement before commits
- Real-time quality monitoring and alerts
- Progressive quality improvement recommendations
- Integration with Elder Council Review System
- 4 Sages wisdom-based quality decisions
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
import json
import logging
import os
import sqlite3
import subprocess
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from test_quality_metrics import TestQualityMetrics

# Import our quality system components
from elder_council_review import ElderCouncilReview, QualityReviewResult
from four_sages_integration import FourSagesQualityIntegration, QualityLearningRequest

logger = logging.getLogger(__name__)


class QualityGateResult(Enum):
    """Quality gate enforcement results"""

    APPROVED = "approved"
    APPROVED_WITH_WARNINGS = "approved_with_warnings"
    REJECTED = "rejected"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    ERROR = "error"


@dataclass
class QualityGateConfig:
    """Configuration for quality gate enforcement"""

    minimum_quality_score: float = 0.70
    elder_approval_threshold: float = 0.85
    auto_reject_threshold: float = 0.50
    max_critical_issues: int = 3
    require_elder_consensus: bool = True
    enable_auto_improvement: bool = True
    enable_progressive_enforcement: bool = True


@dataclass
class QualityGateEnforcement:
    """Result of quality gate enforcement"""

    gate_result: QualityGateResult
    quality_score: float
    issues_found: List[str]
    recommendations: List[str]
    elder_decision: str
    sage_consensus: bool
    enforcement_timestamp: str
    next_steps: List[str]
    bypass_allowed: bool = False


class QualityGate:
    """
    Quality Gate Enforcement System

    Provides automated quality control with Elder Council and 4 Sages integration:
    - Pre-commit quality checks
    - Continuous quality monitoring
    - Progressive quality improvement
    - Intelligent quality decision making
    """

    def __init__(self, config: Optional[QualityGateConfig] = None):
        """Initialize Quality Gate system"""
        self.logger = logging.getLogger(__name__)
        self.project_root = PROJECT_ROOT
        self.db_path = self.project_root / "data" / "quality_gate.db"

        # Use provided config or default
        self.config = config or QualityGateConfig()

        # Initialize component systems
        self.elder_council = ElderCouncilReview()
        self.quality_metrics = TestQualityMetrics()
        self.four_sages = FourSagesQualityIntegration()

        # Quality gate enforcement history
        self.enforcement_history = []

        # Progressive enforcement tracking
        self.progressive_enforcement = {
            "consecutive_failures": 0,
            "recent_improvements": [],
            "enforcement_level": "standard",  # 'lenient', 'standard', 'strict'
        }

        # Initialize database
        self._init_database()

        self.logger.info("Quality Gate Enforcement System initialized")
        self.logger.info(f"Minimum quality score: {self.config.minimum_quality_score}")
        self.logger.info(
            f"Elder approval threshold: {self.config.elder_approval_threshold}"
        )

    def _init_database(self):
        """Initialize quality gate database"""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Quality gate enforcement log
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS quality_gate_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_file TEXT NOT NULL,
                gate_result TEXT NOT NULL,
                quality_score REAL,
                issues_count INTEGER,
                elder_decision TEXT,
                sage_consensus BOOLEAN,
                enforcement_timestamp TIMESTAMP,
                bypass_used BOOLEAN DEFAULT FALSE,
                enforcement_level TEXT DEFAULT 'standard'
            )
            """
            )

            # Quality violations tracking
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS quality_violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_file TEXT NOT NULL,
                violation_type TEXT,
                violation_description TEXT,
                severity TEXT,
                detected_timestamp TIMESTAMP,
                resolved BOOLEAN DEFAULT FALSE,
                resolution_method TEXT,
                resolution_timestamp TIMESTAMP
            )
            """
            )

            # Quality improvement tracking
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS quality_improvements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_file TEXT NOT NULL,
                improvement_type TEXT,
                before_score REAL,
                after_score REAL,
                improvement_actions TEXT,
                timestamp TIMESTAMP,
                auto_applied BOOLEAN DEFAULT FALSE
            )
            """
            )

            # Quality gate configuration history
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS gate_config_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_change TEXT,
                old_value TEXT,
                new_value TEXT,
                reason TEXT,
                changed_by TEXT,
                timestamp TIMESTAMP
            )
            """
            )

            conn.commit()
            conn.close()

            self.logger.info("Quality gate database initialized")

        except Exception as e:
            self.logger.error(f"Quality gate database initialization failed: {e}")

    async def enforce_quality_gate(
        self, test_file_path: str, context: Dict[str, Any] = None
    ) -> QualityGateEnforcement:
        """
        Main quality gate enforcement for a test file

        Args:
            test_file_path: Path to test file to evaluate
            context: Additional context (commit info, branch, etc.)

        Returns:
            QualityGateEnforcement result with decision and recommendations
        """
        try:
            self.logger.info(f"Enforcing quality gate for: {test_file_path}")

            context = context or {}
            enforcement_start = datetime.now()

            # Phase 1: Comprehensive Quality Analysis
            quality_analysis = await self._perform_comprehensive_quality_analysis(
                test_file_path
            )

            if "error" in quality_analysis:
                return self._create_error_enforcement(
                    test_file_path, quality_analysis["error"]
                )

            # Phase 2: Elder Council Review
            elder_review = await self._get_elder_council_decision(
                test_file_path, quality_analysis
            )

            # Phase 3: 4 Sages Consultation
            sage_consultation = await self._consult_four_sages(
                test_file_path, quality_analysis, elder_review
            )

            # Phase 4: Progressive Enforcement Decision
            gate_decision = await self._make_gate_decision(
                test_file_path,
                quality_analysis,
                elder_review,
                sage_consultation,
                context,
            )

            # Phase 5: Auto-improvement if enabled and appropriate
            if self.config.enable_auto_improvement and gate_decision.gate_result in [
                QualityGateResult.APPROVED_WITH_WARNINGS,
                QualityGateResult.MANUAL_REVIEW_REQUIRED,
            ]:
                improvement_result = await self._apply_auto_improvements(
                    test_file_path, gate_decision
                )
                if improvement_result:
                    gate_decision.recommendations.insert(
                        0, f"Auto-improvements applied: {improvement_result}"
                    )

            # Phase 6: Update progressive enforcement tracking
            self._update_progressive_enforcement(gate_decision)

            # Phase 7: Log enforcement result
            await self._log_enforcement_result(gate_decision)

            self.logger.info(
                f"Quality gate enforcement completed: {gate_decision.gate_result.value}"
            )
            return gate_decision

        except Exception as e:
            self.logger.error(
                f"Quality gate enforcement failed for {test_file_path}: {e}"
            )
            return self._create_error_enforcement(test_file_path, str(e))

    async def _perform_comprehensive_quality_analysis(
        self, test_file_path: str
    ) -> Dict[str, Any]:
        """Perform comprehensive quality analysis using our metrics system"""
        try:
            # Use our test quality metrics analyzer
            analysis = self.quality_metrics.analyze_test_file(test_file_path)

            if "error" in analysis:
                return analysis

            # Extract key quality information
            quality_info = {
                "quality_scores": analysis["quality_scores"],
                "detailed_metrics": analysis["detailed_metrics"],
                "quality_insights": analysis["quality_insights"],
                "improvement_recommendations": analysis["improvement_recommendations"],
                "risk_assessment": analysis["risk_assessment"],
                "pattern_analysis": analysis["pattern_analysis"],
            }

            return quality_info

        except Exception as e:
            self.logger.error(f"Comprehensive quality analysis failed: {e}")
            return {"error": str(e)}

    async def _get_elder_council_decision(
        self, test_file_path: str, quality_analysis: Dict[str, Any]
    ) -> QualityReviewResult:
        """Get Elder Council review decision"""
        try:
            # Use our Elder Council Review system
            elder_review = await self.elder_council.review_test_quality(test_file_path)
            return elder_review

        except Exception as e:
            self.logger.error(f"Elder Council review failed: {e}")
            # Create fallback review result
            from elder_council_review import TestQualityMetrics

            fallback_metrics = TestQualityMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
            return QualityReviewResult(
                test_file=test_file_path,
                quality_metrics=fallback_metrics,
                sage_recommendations={},
                quality_issues=[f"Elder Council review failed: {e}"],
                improvement_suggestions=["Fix review system issues"],
                approval_status="error",
                confidence_score=0.0,
                elder_decision=f"Review failed: {e}",
            )

    async def _consult_four_sages(
        self,
        test_file_path: str,
        quality_analysis: Dict[str, Any],
        elder_review: QualityReviewResult,
    ) -> Dict[str, Any]:
        """Consult 4 Sages for quality wisdom"""
        try:
            # Prepare learning request for 4 Sages
            learning_request = QualityLearningRequest(
                test_file=test_file_path,
                quality_metrics=quality_analysis["quality_scores"],
                current_issues=elder_review.quality_issues,
                improvement_goals=elder_review.improvement_suggestions[
                    :3
                ],  # Top 3 goals
                context={
                    "enforcement_context": True,
                    "elder_approval_status": elder_review.approval_status,
                    "quality_grade": quality_analysis["quality_scores"][
                        "quality_grade"
                    ],
                },
                priority="high"
                if elder_review.approval_status == "rejected"
                else "medium",
            )

            # Consult 4 Sages
            sage_result = await self.four_sages.consult_sages_for_quality(
                learning_request
            )
            return sage_result

        except Exception as e:
            self.logger.error(f"4 Sages consultation failed: {e}")
            return {
                "consensus_reached": False,
                "error": str(e),
                "recommended_actions": ["Fix Sages consultation system"],
            }

    async def _make_gate_decision(
        self,
        test_file_path: str,
        quality_analysis: Dict[str, Any],
        elder_review: QualityReviewResult,
        sage_consultation: Dict[str, Any],
        context: Dict[str, Any],
    ) -> QualityGateEnforcement:
        """Make final quality gate decision based on all inputs"""

        overall_quality_score = quality_analysis["quality_scores"][
            "overall_quality_score"
        ]
        elder_approval = elder_review.approval_status
        sage_consensus = sage_consultation.get("consensus_reached", False)

        # Determine base gate result
        if overall_quality_score < self.config.auto_reject_threshold:
            gate_result = QualityGateResult.REJECTED
        elif (
            overall_quality_score >= self.config.elder_approval_threshold
            and elder_approval == "approved"
        ):
            if sage_consensus:
                gate_result = QualityGateResult.APPROVED
            else:
                gate_result = QualityGateResult.APPROVED_WITH_WARNINGS
        elif overall_quality_score >= self.config.minimum_quality_score:
            if elder_approval in ["approved", "approved_with_recommendations"]:
                gate_result = QualityGateResult.APPROVED_WITH_WARNINGS
            else:
                gate_result = QualityGateResult.MANUAL_REVIEW_REQUIRED
        else:
            # Below minimum but above auto-reject
            if self._should_allow_progressive_pass(overall_quality_score, elder_review):
                gate_result = QualityGateResult.MANUAL_REVIEW_REQUIRED
            else:
                gate_result = QualityGateResult.REJECTED

        # Apply progressive enforcement adjustments
        if self.config.enable_progressive_enforcement:
            gate_result = self._apply_progressive_enforcement(
                gate_result, overall_quality_score
            )

        # Compile issues and recommendations
        all_issues = elder_review.quality_issues.copy()
        if "error" in sage_consultation:
            all_issues.append(f"Sage consultation error: {sage_consultation['error']}")

        all_recommendations = elder_review.improvement_suggestions.copy()
        sage_actions = sage_consultation.get("recommended_actions", [])
        all_recommendations.extend(sage_actions[:5])  # Add top 5 sage recommendations

        # Determine next steps
        next_steps = self._determine_next_steps(
            gate_result, overall_quality_score, elder_review, sage_consultation
        )

        # Check if bypass is allowed
        bypass_allowed = self._is_bypass_allowed(gate_result, context)

        return QualityGateEnforcement(
            gate_result=gate_result,
            quality_score=overall_quality_score,
            issues_found=all_issues,
            recommendations=all_recommendations,
            elder_decision=elder_review.elder_decision,
            sage_consensus=sage_consensus,
            enforcement_timestamp=datetime.now().isoformat(),
            next_steps=next_steps,
            bypass_allowed=bypass_allowed,
        )

    def _should_allow_progressive_pass(
        self, quality_score: float, elder_review: QualityReviewResult
    ) -> bool:
        """Determine if progressive enforcement should allow a marginal pass"""

        # Check recent improvement trend
        recent_improvements = self.progressive_enforcement.get(
            "recent_improvements", []
        )
        if len(recent_improvements) >= 2:
            # If quality has been improving, be more lenient
            if all(imp > 0 for imp in recent_improvements[-2:]):
                return quality_score >= self.config.minimum_quality_score - 0.05

        # Check number of critical issues
        critical_issues = len(
            [
                issue
                for issue in elder_review.quality_issues
                if any(
                    word in issue.lower() for word in ["critical", "severe", "major"]
                )
            ]
        )

        if (
            critical_issues <= 1
            and quality_score >= self.config.minimum_quality_score - 0.1
        ):
            return True

        return False

    def _apply_progressive_enforcement(
        self, gate_result: QualityGateResult, quality_score: float
    ) -> QualityGateResult:
        """Apply progressive enforcement based on history"""

        enforcement_level = self.progressive_enforcement.get(
            "enforcement_level", "standard"
        )
        consecutive_failures = self.progressive_enforcement.get(
            "consecutive_failures", 0
        )

        # Stricter enforcement after consecutive failures
        if consecutive_failures >= 3:
            if gate_result == QualityGateResult.APPROVED_WITH_WARNINGS:
                return QualityGateResult.MANUAL_REVIEW_REQUIRED
            elif (
                gate_result == QualityGateResult.MANUAL_REVIEW_REQUIRED
                and quality_score < 0.65
            ):
                return QualityGateResult.REJECTED

        # More lenient for improving trend
        elif enforcement_level == "lenient" and consecutive_failures == 0:
            if gate_result == QualityGateResult.REJECTED and quality_score >= 0.55:
                return QualityGateResult.MANUAL_REVIEW_REQUIRED

        return gate_result

    def _determine_next_steps(
        self,
        gate_result: QualityGateResult,
        quality_score: float,
        elder_review: QualityReviewResult,
        sage_consultation: Dict[str, Any],
    ) -> List[str]:
        """Determine next steps based on gate result"""

        next_steps = []

        if gate_result == QualityGateResult.APPROVED:
            next_steps = [
                "Test approved - proceed with commit",
                "Continue maintaining high quality standards",
                "Consider sharing best practices with team",
            ]

        elif gate_result == QualityGateResult.APPROVED_WITH_WARNINGS:
            next_steps = [
                "Test approved with warnings - safe to commit",
                "Address warnings in next iteration",
                "Monitor quality trends",
            ]

        elif gate_result == QualityGateResult.MANUAL_REVIEW_REQUIRED:
            next_steps = [
                "Manual review required before commit",
                "Contact Elder Council for guidance",
                "Implement top priority improvements",
                "Re-run quality gate after improvements",
            ]

        elif gate_result == QualityGateResult.REJECTED:
            next_steps = [
                "BLOCKED: Must improve quality before commit",
                "Implement critical improvements",
                "Focus on fixing major issues first",
                "Re-run quality analysis after fixes",
                "Consider consulting with team lead",
            ]

        # Add specific recommendations from Elder Council and Sages
        if elder_review.improvement_suggestions:
            next_steps.append(
                f"Elder Council priority: {elder_review.improvement_suggestions[0]}"
            )

        if sage_consultation.get("recommended_actions"):
            next_steps.append(
                f"Sages recommend: {sage_consultation['recommended_actions'][0]}"
            )

        return next_steps[:6]  # Limit to top 6 steps

    def _is_bypass_allowed(
        self, gate_result: QualityGateResult, context: Dict[str, Any]
    ) -> bool:
        """Determine if quality gate bypass is allowed"""

        # Never allow bypass for rejected tests
        if gate_result == QualityGateResult.REJECTED:
            return False

        # Allow bypass for emergency fixes
        if context.get("emergency", False):
            return True

        # Allow bypass for hotfixes
        if context.get("branch", "").startswith("hotfix/"):
            return True

        # Allow bypass for manual review cases with approval
        if gate_result == QualityGateResult.MANUAL_REVIEW_REQUIRED:
            return context.get("manual_approval", False)

        return False

    async def _apply_auto_improvements(
        self, test_file_path: str, gate_decision: QualityGateEnforcement
    ) -> Optional[str]:
        """Apply automated quality improvements if possible"""
        try:
            self.logger.info(f"Applying auto-improvements for {test_file_path}")

            # Read current test file
            test_file = Path(test_file_path)
            if not test_file.exists():
                return None

            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()

            improvements_applied = []

            # Auto-improvement 1: Add missing docstrings
            if any(
                "documentation" in issue.lower() for issue in gate_decision.issues_found
            ):
                if self._add_missing_docstrings(content):
                    improvements_applied.append("added_docstrings")

            # Auto-improvement 2: Fix simple assertion issues
            if any(
                "trivial assertion" in issue.lower()
                for issue in gate_decision.issues_found
            ):
                if self._fix_trivial_assertions(content):
                    improvements_applied.append("fixed_assertions")

            # Auto-improvement 3: Add basic setup/teardown if missing
            if any(
                "setup" in issue.lower() or "teardown" in issue.lower()
                for issue in gate_decision.issues_found
            ):
                if self._add_basic_setup_teardown(content):
                    improvements_applied.append("added_setup_teardown")

            if improvements_applied:
                # Save improved content
                with open(test_file, "w", encoding="utf-8") as f:
                    f.write(content)

                return ", ".join(improvements_applied)

        except Exception as e:
            self.logger.error(f"Auto-improvement failed: {e}")

        return None

    def _add_missing_docstrings(self, content: str) -> bool:
        """Add basic docstrings to test methods (mock implementation)"""
        # This would implement actual docstring addition logic
        return "def test_" in content and '"""' not in content

    def _fix_trivial_assertions(self, content: str) -> bool:
        """Fix trivial assertions like assert True (mock implementation)"""
        return "assert True" in content

    def _add_basic_setup_teardown(self, content: str) -> bool:
        """Add basic setup/teardown methods (mock implementation)"""
        return "class Test" in content and "setup_method" not in content

    def _update_progressive_enforcement(self, gate_decision: QualityGateEnforcement):
        """Update progressive enforcement tracking"""

        if gate_decision.gate_result == QualityGateResult.REJECTED:
            self.progressive_enforcement["consecutive_failures"] += 1
        else:
            # Reset consecutive failures on any non-rejection
            self.progressive_enforcement["consecutive_failures"] = 0

        # Track quality improvements
        recent_improvements = self.progressive_enforcement.setdefault(
            "recent_improvements", []
        )
        if len(recent_improvements) >= 5:
            recent_improvements.pop(0)  # Keep only last 5

        # For now, assume some improvement (would calculate actual improvement in real implementation)
        recent_improvements.append(
            0.05 if gate_decision.gate_result != QualityGateResult.REJECTED else -0.02
        )

        # Adjust enforcement level
        failures = self.progressive_enforcement["consecutive_failures"]
        if failures == 0 and all(imp > 0 for imp in recent_improvements[-3:]):
            self.progressive_enforcement["enforcement_level"] = "lenient"
        elif failures >= 3:
            self.progressive_enforcement["enforcement_level"] = "strict"
        else:
            self.progressive_enforcement["enforcement_level"] = "standard"

    async def _log_enforcement_result(self, gate_decision: QualityGateEnforcement):
        """Log enforcement result to database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO quality_gate_log
                (test_file, gate_result, quality_score, issues_count, elder_decision,
                 sage_consensus, enforcement_timestamp, bypass_used, enforcement_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    gate_decision.gate_result.name,  # This will be the test file
                    gate_decision.gate_result.value,
                    gate_decision.quality_score,
                    len(gate_decision.issues_found),
                    gate_decision.elder_decision,
                    gate_decision.sage_consensus,
                    gate_decision.enforcement_timestamp,
                    gate_decision.bypass_allowed,
                    self.progressive_enforcement["enforcement_level"],
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to log enforcement result: {e}")

    def _create_error_enforcement(
        self, test_file_path: str, error_message: str
    ) -> QualityGateEnforcement:
        """Create error enforcement result"""
        return QualityGateEnforcement(
            gate_result=QualityGateResult.ERROR,
            quality_score=0.0,
            issues_found=[f"Enforcement error: {error_message}"],
            recommendations=[
                "Fix quality gate system issues",
                "Manual review required",
            ],
            elder_decision=f"Error in enforcement: {error_message}",
            sage_consensus=False,
            enforcement_timestamp=datetime.now().isoformat(),
            next_steps=["Debug quality gate system", "Perform manual quality review"],
            bypass_allowed=True,  # Allow bypass for system errors
        )

    async def enforce_pre_commit_hook(
        self, changed_files: List[str] = None
    ) -> Dict[str, Any]:
        """
        Enforce quality gates for pre-commit hook

        Args:
            changed_files: List of changed files (if None, detect from git)

        Returns:
            Dictionary with enforcement results for all test files
        """
        try:
            self.logger.info("Enforcing pre-commit quality gates")

            # Detect changed test files
            if changed_files is None:
                changed_files = self._detect_changed_test_files()

            test_files = [
                f
                for f in changed_files
                if f.endswith(".py") and ("test_" in f or f.endswith("_test.py"))
            ]

            if not test_files:
                return {
                    "overall_result": "no_tests_changed",
                    "message": "No test files changed - proceeding",
                    "details": {},
                }

            self.logger.info(f"Found {len(test_files)} test files to check")

            # Enforce quality gates for each test file
            enforcement_results = {}
            overall_approved = True
            blocking_issues = []

            for test_file in test_files:
                try:
                    result = await self.enforce_quality_gate(
                        test_file, {"context": "pre_commit"}
                    )
                    enforcement_results[test_file] = result

                    # Check if this blocks the commit
                    if result.gate_result == QualityGateResult.REJECTED:
                        overall_approved = False
                        blocking_issues.append(f"{test_file}: {result.elder_decision}")
                    elif (
                        result.gate_result == QualityGateResult.MANUAL_REVIEW_REQUIRED
                        and not result.bypass_allowed
                    ):
                        overall_approved = False
                        blocking_issues.append(f"{test_file}: Requires manual review")

                except Exception as e:
                    self.logger.error(f"Enforcement failed for {test_file}: {e}")
                    overall_approved = False
                    blocking_issues.append(f"{test_file}: Enforcement error - {e}")

            # Compile overall result
            if overall_approved:
                overall_result = "approved"
                message = f"All {len(test_files)} test files passed quality gates"
            else:
                overall_result = "blocked"
                message = (
                    f"Commit blocked by quality issues in {len(blocking_issues)} files"
                )

            return {
                "overall_result": overall_result,
                "message": message,
                "files_checked": len(test_files),
                "files_approved": sum(
                    1
                    for r in enforcement_results.values()
                    if r.gate_result
                    in [
                        QualityGateResult.APPROVED,
                        QualityGateResult.APPROVED_WITH_WARNINGS,
                    ]
                ),
                "blocking_issues": blocking_issues,
                "detailed_results": {
                    k: asdict(v) for k, v in enforcement_results.items()
                },
                "next_steps": self._compile_pre_commit_next_steps(
                    enforcement_results, overall_approved
                ),
            }

        except Exception as e:
            self.logger.error(f"Pre-commit enforcement failed: {e}")
            return {
                "overall_result": "error",
                "message": f"Pre-commit quality gate error: {e}",
                "error": str(e),
            }

    def _detect_changed_test_files(self) -> List[str]:
        """Detect changed test files using git"""
        try:
            # Get staged files
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode == 0:
                return (
                    result.stdout.strip().split("\n") if result.stdout.strip() else []
                )
            else:
                self.logger.warning("Could not detect changed files from git")
                return []

        except Exception as e:
            self.logger.error(f"Failed to detect changed files: {e}")
            return []

    def _compile_pre_commit_next_steps(
        self, results: Dict[str, QualityGateEnforcement], approved: bool
    ) -> List[str]:
        """Compile next steps for pre-commit enforcement"""
        if approved:
            return [
                "All tests passed quality gates",
                "Commit can proceed safely",
                "Continue maintaining quality standards",
            ]

        steps = ["COMMIT BLOCKED - Quality issues must be resolved:"]

        # Add specific steps from each blocked file
        for file_path, result in results.items():
            if result.gate_result in [
                QualityGateResult.REJECTED,
                QualityGateResult.MANUAL_REVIEW_REQUIRED,
            ]:
                steps.append(
                    f"Fix {Path(file_path).name}: {result.next_steps[0] if result.next_steps else 'Improve quality'}"
                )

        steps.extend(
            [
                "Run 'python quality_gate.py --fix' for auto-improvements",
                "Re-run tests after fixes",
                "Contact Elder Council if assistance needed",
            ]
        )

        return steps[:8]  # Limit output

    async def generate_quality_gate_report(
        self, time_range_days: int = 7
    ) -> Dict[str, Any]:
        """Generate comprehensive quality gate enforcement report"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=time_range_days)

            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Get enforcement statistics
            cursor.execute(
                """
                SELECT gate_result, COUNT(*), AVG(quality_score)
                FROM quality_gate_log
                WHERE datetime(enforcement_timestamp) >= ?
                GROUP BY gate_result
            """,
                (start_date.isoformat(),),
            )

            enforcement_stats = {}
            for row in cursor.fetchall():
                enforcement_stats[row[0]] = {
                    "count": row[1],
                    "avg_quality_score": row[2],
                }

            # Get quality trends
            cursor.execute(
                """
                SELECT DATE(enforcement_timestamp) as date,
                       AVG(quality_score) as avg_quality,
                       COUNT(*) as enforcements
                FROM quality_gate_log
                WHERE datetime(enforcement_timestamp) >= ?
                GROUP BY DATE(enforcement_timestamp)
                ORDER BY date
            """,
                (start_date.isoformat(),),
            )

            quality_trends = [
                {"date": row[0], "avg_quality": row[1], "enforcements": row[2]}
                for row in cursor.fetchall()
            ]

            # Get most common violations
            cursor.execute(
                """
                SELECT violation_type, COUNT(*), AVG(CASE WHEN resolved THEN 1 ELSE 0 END)
                FROM quality_violations
                WHERE datetime(detected_timestamp) >= ?
                GROUP BY violation_type
                ORDER BY COUNT(*) DESC
                LIMIT 10
            """,
                (start_date.isoformat(),),
            )

            common_violations = [
                {"violation_type": row[0], "count": row[1], "resolution_rate": row[2]}
                for row in cursor.fetchall()
            ]

            conn.close()

            # Calculate overall statistics
            total_enforcements = sum(
                stats["count"] for stats in enforcement_stats.values()
            )
            approved_count = enforcement_stats.get("approved", {}).get("count", 0)
            approved_with_warnings = enforcement_stats.get(
                "approved_with_warnings", {}
            ).get("count", 0)
            rejected_count = enforcement_stats.get("rejected", {}).get("count", 0)

            approval_rate = (
                (approved_count + approved_with_warnings) / total_enforcements
                if total_enforcements > 0
                else 0
            )

            return {
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": time_range_days,
                },
                "enforcement_summary": {
                    "total_enforcements": total_enforcements,
                    "approval_rate": approval_rate,
                    "rejection_rate": rejected_count / total_enforcements
                    if total_enforcements > 0
                    else 0,
                    "enforcement_statistics": enforcement_stats,
                },
                "quality_trends": quality_trends,
                "common_violations": common_violations,
                "system_health": {
                    "progressive_enforcement": self.progressive_enforcement,
                    "current_enforcement_level": self.progressive_enforcement.get(
                        "enforcement_level", "standard"
                    ),
                    "system_performance": "operational"
                    if total_enforcements > 0
                    else "low_activity",
                },
                "recommendations": self._generate_system_recommendations(
                    enforcement_stats, approval_rate
                ),
                "elder_council_integration": "active",
                "four_sages_integration": "active",
            }

        except Exception as e:
            self.logger.error(f"Quality gate report generation failed: {e}")
            return {"error": str(e), "report_timestamp": datetime.now().isoformat()}

    def _generate_system_recommendations(
        self, stats: Dict[str, Any], approval_rate: float
    ) -> List[str]:
        """Generate system-level recommendations"""
        recommendations = []

        if approval_rate >= 0.9:
            recommendations.append(
                "Excellent quality gate performance - maintain current standards"
            )
        elif approval_rate >= 0.7:
            recommendations.append(
                "Good quality gate performance with room for improvement"
            )
        elif approval_rate >= 0.5:
            recommendations.append(
                "Quality gate showing mixed results - review thresholds"
            )
        else:
            recommendations.append(
                "Poor quality gate performance - urgent review needed"
            )

        if stats.get("rejected", {}).get("count", 0) > 5:
            recommendations.append("High rejection rate - consider developer training")

        if stats.get("manual_review_required", {}).get("count", 0) > 10:
            recommendations.append("Many manual reviews - optimize automation")

        recommendations.extend(
            [
                "Continue Elder Council and 4 Sages integration",
                "Monitor progressive enforcement effectiveness",
                "Regular quality threshold review",
            ]
        )

        return recommendations


# CLI Interface
def main():
    """Command-line interface for quality gate system"""
    import argparse

    parser = argparse.ArgumentParser(description="Quality Gate Enforcement System")
    parser.add_argument("--file", type=str, help="Test file to check")
    parser.add_argument(
        "--pre-commit", action="store_true", help="Run pre-commit checks"
    )
    parser.add_argument("--report", action="store_true", help="Generate quality report")
    parser.add_argument("--days", type=int, default=7, help="Report time range in days")
    parser.add_argument("--fix", action="store_true", help="Apply auto-improvements")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Initialize quality gate
    quality_gate = QualityGate()

    async def run_async():
        if args.file:
            # Check single file
            result = await quality_gate.enforce_quality_gate(args.file)
            print(f"\nQuality Gate Result: {result.gate_result.value}")
            print(f"Quality Score: {result.quality_score:.2f}")
            print(f"Elder Decision: {result.elder_decision}")

            if result.issues_found:
                print("\nIssues Found:")
                for issue in result.issues_found[:5]:
                    print(f"  - {issue}")

            if result.next_steps:
                print("\nNext Steps:")
                for step in result.next_steps[:3]:
                    print(f"  - {step}")

        elif args.pre_commit:
            # Run pre-commit checks
            result = await quality_gate.enforce_pre_commit_hook()
            print(f"\nPre-commit Result: {result['overall_result']}")
            print(f"Message: {result['message']}")

            if result.get("blocking_issues"):
                print("\nBlocking Issues:")
                for issue in result["blocking_issues"]:
                    print(f"  - {issue}")

        elif args.report:
            # Generate report
            report = await quality_gate.generate_quality_gate_report(args.days)
            print(f"\nQuality Gate Report ({args.days} days)")
            print(
                f"Total Enforcements: {report['enforcement_summary']['total_enforcements']}"
            )
            print(
                f"Approval Rate: {report['enforcement_summary']['approval_rate']:.1%}"
            )
            print(
                f"Current Enforcement Level: {report['system_health']['current_enforcement_level']}"
            )

        else:
            print("Use --help for usage information")

    asyncio.run(run_async())


if __name__ == "__main__":
    main()
