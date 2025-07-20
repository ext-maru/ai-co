#!/usr/bin/env python3
"""
Elder Council Quality Review System
4 Sages Integration for Test Quality Management and Enforcement

Mission: Ensure and maintain 66.7% test coverage quality through intelligent
analysis, comprehensive review, and automated quality gates.

Architecture:
- Elder Council Review Engine: Central quality assessment
- 4 Sages Integration: Knowledge, Task, Incident, RAG wisdom
- Quality Metrics Analyzer: Multi-dimensional quality evaluation
- Quality Gate Enforcement: Automated prevention and improvement
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import ast
import asyncio
import json
import logging
import re
import sqlite3
import subprocess
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

# Import existing 4 Sages system
from libs.four_sages_integration import FourSagesIntegration

logger = logging.getLogger(__name__)


@dataclass
class TestQualityMetrics:
    """Test quality assessment metrics"""

    coverage_effectiveness: float  # How well tests cover critical paths
    test_complexity_score: float  # Maintainability and readability
    pattern_compliance: float  # Follows proven successful patterns
    documentation_quality: float  # Clear naming and documentation
    edge_case_coverage: float  # Handles edge cases and errors
    overall_quality_score: float  # Composite quality score

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class QualityReviewResult:
    """Results from Elder Council quality review"""

    test_file: str
    quality_metrics: TestQualityMetrics
    sage_recommendations: Dict[str, Any]
    quality_issues: List[str]
    improvement_suggestions: List[str]
    approval_status: str  # 'approved', 'needs_improvement', 'rejected'
    confidence_score: float
    elder_decision: str


class ElderCouncilReview:
    """
    Elder Council Quality Review System

    Integrates 4 Sages wisdom for comprehensive test quality assessment:
    - Knowledge Sage: Learn from test patterns and maintain quality database
    - Task Sage: Track test quality objectives and progress
    - Incident Sage: Detect test quality issues and failures
    - RAG Sage: Search for similar test patterns and best practices
    """

    def __init__(self):
        """Initialize Elder Council Review System"""
        self.logger = logging.getLogger(__name__)
        self.project_root = PROJECT_ROOT
        self.db_path = self.project_root / "data" / "elder_council_quality.db"

        # Initialize 4 Sages Integration
        self.four_sages = FourSagesIntegration()

        # Quality thresholds (based on proven 98.6%, 100% coverage modules)
        self.quality_thresholds = {
            "minimum_acceptable": 0.7,  # 70% minimum quality
            "good_quality": 0.8,  # 80% good quality
            "excellent_quality": 0.9,  # 90% excellent quality
            "elder_approval": 0.85,  # 85% required for Elder approval
        }

        # Known high-quality test patterns (from successful modules)
        self.proven_patterns = {
            "setup_teardown": "Proper test setup and cleanup",
            "mocking_patterns": "Effective mocking and isolation",
            "edge_case_testing": "Comprehensive edge case coverage",
            "error_handling": "Robust error condition testing",
            "parameterized_tests": "Data-driven test approaches",
            "integration_patterns": "System integration testing",
        }

        # Quality assessment weights
        self.quality_weights = {
            "coverage_effectiveness": 0.25,
            "test_complexity_score": 0.20,
            "pattern_compliance": 0.20,
            "documentation_quality": 0.15,
            "edge_case_coverage": 0.20,
        }

        # Initialize database
        self._init_database()

        self.logger.info("Elder Council Quality Review System initialized")
        self.logger.info("4 Sages Integration active for test quality management")

    def _init_database(self):
        """Initialize Elder Council quality database"""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Quality review history
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS quality_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_file TEXT NOT NULL,
                review_timestamp TIMESTAMP,
                quality_score REAL,
                approval_status TEXT,
                sage_recommendations TEXT,
                quality_issues TEXT,
                improvement_suggestions TEXT,
                elder_decision TEXT,
                confidence_score REAL
            )
            """
            )

            # Quality metrics tracking
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS quality_metrics_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_file TEXT NOT NULL,
                timestamp TIMESTAMP,
                coverage_effectiveness REAL,
                test_complexity_score REAL,
                pattern_compliance REAL,
                documentation_quality REAL,
                edge_case_coverage REAL,
                overall_quality_score REAL
            )
            """
            )

            # Quality patterns database
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS quality_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_name TEXT NOT NULL,
                pattern_description TEXT,
                example_code TEXT,
                quality_impact REAL,
                usage_frequency INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 1.0
            )
            """
            )

            # Quality gate violations
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS quality_gate_violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_file TEXT NOT NULL,
                violation_type TEXT,
                violation_description TEXT,
                severity TEXT,
                timestamp TIMESTAMP,
                resolved BOOLEAN DEFAULT FALSE
            )
            """
            )

            conn.commit()
            conn.close()

            self.logger.info("Elder Council quality database initialized")

        except Exception as e:
            self.logger.error(f"Quality database initialization failed: {e}")

    async def review_test_quality(self, test_file_path: str) -> QualityReviewResult:
        """
        Comprehensive test quality review using 4 Sages wisdom

        Args:
            test_file_path: Path to test file for review

        Returns:
            QualityReviewResult with comprehensive assessment
        """
        try:
            self.logger.info(f"Starting Elder Council review for: {test_file_path}")

            # Phase 1: Read and analyze test file
            test_content = self._read_test_file(test_file_path)
            if not test_content:
                return self._create_error_result(
                    test_file_path, "Unable to read test file"
                )

            # Phase 2: Calculate quality metrics
            quality_metrics = await self._calculate_quality_metrics(
                test_file_path, test_content
            )

            # Phase 3: Consult all 4 Sages for comprehensive analysis
            sage_recommendations = await self._consult_four_sages(
                test_file_path, test_content, quality_metrics
            )

            # Phase 4: Identify quality issues
            quality_issues = self._identify_quality_issues(
                test_content, quality_metrics
            )

            # Phase 5: Generate improvement suggestions
            improvement_suggestions = await self._generate_improvement_suggestions(
                test_file_path, test_content, quality_metrics, sage_recommendations
            )

            # Phase 6: Elder Council decision
            elder_decision_result = await self._make_elder_decision(
                quality_metrics, sage_recommendations, quality_issues
            )

            # Create comprehensive review result
            review_result = QualityReviewResult(
                test_file=test_file_path,
                quality_metrics=quality_metrics,
                sage_recommendations=sage_recommendations,
                quality_issues=quality_issues,
                improvement_suggestions=improvement_suggestions,
                approval_status=elder_decision_result["approval_status"],
                confidence_score=elder_decision_result["confidence_score"],
                elder_decision=elder_decision_result["decision_explanation"],
            )

            # Phase 7: Save review to database
            await self._save_quality_review(review_result)

            self.logger.info(
                f"Elder Council review completed: {review_result.approval_status}"
            )
            return review_result

        except Exception as e:
            self.logger.error(f"Elder Council review failed for {test_file_path}: {e}")
            return self._create_error_result(test_file_path, str(e))

    async def _calculate_quality_metrics(
        self, test_file_path: str, test_content: str
    ) -> TestQualityMetrics:
        """Calculate comprehensive test quality metrics"""
        try:
            # Parse test file for analysis
            test_ast = ast.parse(test_content)

            # 1. Coverage Effectiveness Analysis
            coverage_effectiveness = self._analyze_coverage_effectiveness(
                test_ast, test_content
            )

            # 2. Test Complexity Score
            test_complexity_score = self._analyze_test_complexity(
                test_ast, test_content
            )

            # 3. Pattern Compliance
            pattern_compliance = self._analyze_pattern_compliance(
                test_ast, test_content
            )

            # 4. Documentation Quality
            documentation_quality = self._analyze_documentation_quality(
                test_ast, test_content
            )

            # 5. Edge Case Coverage
            edge_case_coverage = self._analyze_edge_case_coverage(
                test_ast, test_content
            )

            # 6. Calculate overall quality score (weighted average)
            overall_quality_score = (
                coverage_effectiveness * self.quality_weights["coverage_effectiveness"]
                + test_complexity_score * self.quality_weights["test_complexity_score"]
                + pattern_compliance * self.quality_weights["pattern_compliance"]
                + documentation_quality * self.quality_weights["documentation_quality"]
                + edge_case_coverage * self.quality_weights["edge_case_coverage"]
            )

            return TestQualityMetrics(
                coverage_effectiveness=coverage_effectiveness,
                test_complexity_score=test_complexity_score,
                pattern_compliance=pattern_compliance,
                documentation_quality=documentation_quality,
                edge_case_coverage=edge_case_coverage,
                overall_quality_score=overall_quality_score,
            )

        except Exception as e:
            self.logger.error(f"Quality metrics calculation failed: {e}")
            # Return default metrics with error indication
            return TestQualityMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    def _analyze_coverage_effectiveness(
        self, test_ast: ast.AST, test_content: str
    ) -> float:
        """Analyze how effectively tests cover critical code paths"""
        score = 0.0

        # Check for test method count
        test_methods = [
            node
            for node in ast.walk(test_ast)
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        ]

        if len(test_methods) >= 5:
            score += 0.3  # Good number of test methods
        elif len(test_methods) >= 3:
            score += 0.2
        elif len(test_methods) >= 1:
            score += 0.1

        # Check for different test types
        if "test_initialization" in test_content or "test_init" in test_content:
            score += 0.2  # Tests initialization

        if "test_error" in test_content or "test_exception" in test_content:
            score += 0.2  # Tests error handling

        if "mock" in test_content.lower() or "patch" in test_content:
            score += 0.2  # Uses mocking for isolation

        if "pytest.raises" in test_content or "assertRaises" in test_content:
            score += 0.1  # Tests exception cases

        return min(score, 1.0)

    def _analyze_test_complexity(self, test_ast: ast.AST, test_content: str) -> float:
        """Analyze test complexity and maintainability"""
        score = 1.0  # Start with perfect score, deduct for complexity issues

        # Check for overly complex test methods
        for node in ast.walk(test_ast):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                # Count nested statements (complexity indicator)
                nested_depth = self._calculate_nesting_depth(node)
                if nested_depth > 3:
                    score -= 0.1  # Deduct for high complexity

                # Count lines in test method
                if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                    lines = node.end_lineno - node.lineno
                    if lines > 50:
                        score -= 0.2  # Very long test method
                    elif lines > 20:
                        score -= 0.1  # Long test method

        # Check for good patterns
        if "setup_method" in test_content and "teardown_method" in test_content:
            score += 0.1  # Good setup/teardown

        if len(re.findall(r"assert\s+\w+", test_content)) >= 3:
            score += 0.1  # Good assertion coverage

        return max(score, 0.0)

    def _analyze_pattern_compliance(
        self, test_ast: ast.AST, test_content: str
    ) -> float:
        """Analyze compliance with proven test patterns"""
        score = 0.0

        # Check for proven patterns
        pattern_checks = {
            "setup_teardown": (
                "setup_method" in test_content and "teardown_method" in test_content
            ),
            "mocking_patterns": (
                "mock" in test_content.lower() or "patch" in test_content
            ),
            "edge_case_testing": (
                "edge" in test_content.lower() or "boundary" in test_content.lower()
            ),
            "error_handling": (
                "pytest.raises" in test_content or "exception" in test_content.lower()
            ),
            "parameterized_tests": (
                "parametrize" in test_content or "@pytest.mark" in test_content
            ),
            "integration_patterns": (
                "integration" in test_content.lower()
                or "end_to_end" in test_content.lower()
            ),
        }

        patterns_found = sum(1 for pattern, found in pattern_checks.items() if found)
        score = patterns_found / len(pattern_checks)

        return score

    def _analyze_documentation_quality(
        self, test_ast: ast.AST, test_content: str
    ) -> float:
        """Analyze test documentation and clarity"""
        score = 0.0

        # Check for docstrings
        test_methods = [
            node
            for node in ast.walk(test_ast)
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        ]

        documented_methods = 0
        for method in test_methods:
            if ast.get_docstring(method):
                documented_methods += 1

        if test_methods:
            score += (documented_methods / len(test_methods)) * 0.4

        # Check for clear test names
        clear_names = sum(
            1 for method in test_methods if len(method.name) > 10 and "_" in method.name
        )
        if test_methods:
            score += (clear_names / len(test_methods)) * 0.3

        # Check for class docstring
        for node in ast.walk(test_ast):
            if isinstance(node, ast.ClassDef) and ast.get_docstring(node):
                score += 0.3
                break

        return min(score, 1.0)

    def _analyze_edge_case_coverage(
        self, test_ast: ast.AST, test_content: str
    ) -> float:
        """Analyze coverage of edge cases and error conditions"""
        score = 0.0

        # Check for edge case indicators
        edge_case_indicators = [
            "none",
            "null",
            "empty",
            "zero",
            "negative",
            "boundary",
            "limit",
            "max",
            "min",
            "overflow",
            "underflow",
            "invalid",
            "error",
            "exception",
            "fail",
            "edge",
        ]

        content_lower = test_content.lower()
        found_indicators = sum(
            1 for indicator in edge_case_indicators if indicator in content_lower
        )

        # Score based on edge case coverage
        if found_indicators >= 5:
            score += 0.4
        elif found_indicators >= 3:
            score += 0.3
        elif found_indicators >= 1:
            score += 0.2

        # Check for exception testing
        if "pytest.raises" in test_content or "assertRaises" in test_content:
            score += 0.3

        # Check for parametrized tests (good for edge cases)
        if "parametrize" in test_content:
            score += 0.3

        return min(score, 1.0)

    def _calculate_nesting_depth(self, node: ast.AST) -> int:
        """Calculate maximum nesting depth in AST node"""
        max_depth = 0

        def visit_node(current_node, depth=0):
            nonlocal max_depth
            max_depth = max(max_depth, depth)

            for child in ast.iter_child_nodes(current_node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                    visit_node(child, depth + 1)
                else:
                    visit_node(child, depth)

        visit_node(node)
        return max_depth

    async def _consult_four_sages(
        self,
        test_file_path: str,
        test_content: str,
        quality_metrics: TestQualityMetrics,
    ) -> Dict[str, Any]:
        """Consult all 4 Sages for comprehensive test quality analysis"""
        try:
            # Prepare learning request for 4 Sages
            learning_request = {
                "type": "test_quality_analysis",
                "data": {
                    "test_file": test_file_path,
                    "quality_metrics": quality_metrics.to_dict(),
                    "test_content_summary": self._summarize_test_content(test_content),
                    "analysis_focus": "quality_improvement",
                },
            }

            # Coordinate learning session with all 4 Sages
            coordination_result = self.four_sages.coordinate_learning_session(
                learning_request
            )

            # Extract individual sage recommendations
            sage_responses = coordination_result.get("individual_responses", {})

            # Compile comprehensive recommendations
            recommendations = {
                "knowledge_sage": self._extract_knowledge_sage_insights(
                    sage_responses.get("knowledge_sage", {})
                ),
                "task_sage": self._extract_task_sage_insights(
                    sage_responses.get("task_sage", {})
                ),
                "incident_sage": self._extract_incident_sage_insights(
                    sage_responses.get("incident_sage", {})
                ),
                "rag_sage": self._extract_rag_sage_insights(
                    sage_responses.get("rag_sage", {})
                ),
                "consensus_reached": coordination_result.get(
                    "consensus_reached", False
                ),
                "learning_outcome": coordination_result.get(
                    "learning_outcome", "No consensus"
                ),
                "session_id": coordination_result.get("session_id", "unknown"),
            }

            return recommendations

        except Exception as e:
            self.logger.error(f"4 Sages consultation failed: {e}")
            return self._get_fallback_sage_recommendations()

    def _summarize_test_content(self, test_content: str) -> Dict[str, Any]:
        """Create summary of test content for Sages analysis"""
        lines = test_content.split("\n")

        return {
            "total_lines": len(lines),
            "test_methods_count": len(re.findall(r"def test_\w+", test_content)),
            "has_setup_teardown": "setup_method" in test_content
            and "teardown_method" in test_content,
            "has_mocking": "mock" in test_content.lower() or "patch" in test_content,
            "has_exception_testing": "pytest.raises" in test_content
            or "assertRaises" in test_content,
            "has_parametrization": "parametrize" in test_content,
            "assertion_count": len(re.findall(r"assert\s+\w+", test_content)),
            "import_statements": len(
                re.findall(r"^import\s+|^from\s+", test_content, re.MULTILINE)
            ),
        }

    def _extract_knowledge_sage_insights(
        self, response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract Knowledge Sage specific insights for test quality"""
        base_recommendation = response.get(
            "recommendation", "Store test patterns in knowledge base"
        )
        confidence = response.get("confidence_score", 0.9)

        return {
            "pattern_storage_advice": base_recommendation,
            "historical_patterns": ["setup_teardown_pattern", "mocking_best_practices"],
            "knowledge_base_integration": "Store successful test patterns for reuse",
            "learning_opportunities": [
                "Edge case patterns",
                "Error handling approaches",
            ],
            "confidence": confidence,
            "sage_priority": "knowledge_preservation",
        }

    def _extract_task_sage_insights(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract Task Sage specific insights for test quality"""
        base_recommendation = response.get(
            "recommendation", "Optimize test execution workflow"
        )
        confidence = response.get("confidence_score", 0.85)

        return {
            "workflow_optimization": base_recommendation,
            "priority_suggestions": [
                "Focus on critical path testing",
                "Improve test organization",
            ],
            "scheduling_advice": "Run quality checks before commit",
            "task_dependencies": [
                "Code review integration",
                "CI/CD pipeline inclusion",
            ],
            "confidence": confidence,
            "sage_priority": "workflow_optimization",
        }

    def _extract_incident_sage_insights(
        self, response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract Incident Sage specific insights for test quality"""
        base_recommendation = response.get(
            "recommendation", "Monitor for test quality degradation"
        )
        confidence = response.get("confidence_score", 0.8)

        return {
            "quality_monitoring": base_recommendation,
            "risk_assessment": ["Low test coverage risk", "Poor assertion quality"],
            "prevention_strategies": ["Automated quality gates", "Pre-commit hooks"],
            "incident_patterns": ["Test flakiness", "Incomplete error handling"],
            "confidence": confidence,
            "sage_priority": "risk_prevention",
        }

    def _extract_rag_sage_insights(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract RAG Sage specific insights for test quality"""
        base_recommendation = response.get(
            "recommendation", "Enhance test pattern search and reuse"
        )
        confidence = response.get("confidence_score", 0.88)

        return {
            "pattern_search": base_recommendation,
            "similar_tests": ["test_manager_patterns", "test_worker_patterns"],
            "context_enhancement": "Link related test patterns",
            "search_suggestions": [
                "Find similar test structures",
                "Locate best practices",
            ],
            "confidence": confidence,
            "sage_priority": "pattern_discovery",
        }

    def _get_fallback_sage_recommendations(self) -> Dict[str, Any]:
        """Fallback recommendations when Sages consultation fails"""
        return {
            "knowledge_sage": {
                "pattern_storage_advice": "Store test patterns for future reference",
                "confidence": 0.7,
                "sage_priority": "knowledge_preservation",
            },
            "task_sage": {
                "workflow_optimization": "Optimize test execution pipeline",
                "confidence": 0.7,
                "sage_priority": "workflow_optimization",
            },
            "incident_sage": {
                "quality_monitoring": "Monitor for quality degradation",
                "confidence": 0.7,
                "sage_priority": "risk_prevention",
            },
            "rag_sage": {
                "pattern_search": "Search for similar test patterns",
                "confidence": 0.7,
                "sage_priority": "pattern_discovery",
            },
            "consensus_reached": False,
            "learning_outcome": "Fallback recommendations applied",
            "session_id": "fallback_session",
        }

    def _identify_quality_issues(
        self, test_content: str, quality_metrics: TestQualityMetrics
    ) -> List[str]:
        """Identify specific quality issues in test"""
        issues = []

        # Check each quality dimension
        if quality_metrics.coverage_effectiveness < 0.7:
            issues.append(
                "Insufficient test coverage effectiveness - consider testing more code paths"
            )

        if quality_metrics.test_complexity_score < 0.7:
            issues.append("High test complexity - consider simplifying test structure")

        if quality_metrics.pattern_compliance < 0.7:
            issues.append("Poor pattern compliance - review proven test patterns")

        if quality_metrics.documentation_quality < 0.7:
            issues.append(
                "Inadequate documentation - add test docstrings and clear naming"
            )

        if quality_metrics.edge_case_coverage < 0.7:
            issues.append(
                "Limited edge case coverage - add boundary and error condition tests"
            )

        # Specific content-based issues
        if "assert True" in test_content:
            issues.append(
                "Trivial assertions found - replace with meaningful assertions"
            )

        if test_content.count("def test_") < 3:
            issues.append(
                "Too few test methods - consider adding more comprehensive tests"
            )

        if "mock" not in test_content.lower() and "patch" not in test_content:
            issues.append("No mocking detected - consider isolating dependencies")

        return issues

    async def _generate_improvement_suggestions(
        self,
        test_file_path: str,
        test_content: str,
        quality_metrics: TestQualityMetrics,
        sage_recommendations: Dict[str, Any],
    ) -> List[str]:
        """Generate specific improvement suggestions based on analysis"""
        suggestions = []

        # Based on quality metrics
        if quality_metrics.coverage_effectiveness < 0.8:
            suggestions.append(
                "Add tests for initialization, error handling, and edge cases"
            )

        if quality_metrics.test_complexity_score < 0.8:
            suggestions.append(
                "Refactor complex test methods into smaller, focused tests"
            )

        if quality_metrics.pattern_compliance < 0.8:
            suggestions.append(
                "Implement setup_method/teardown_method for better test isolation"
            )
            suggestions.append("Use pytest.parametrize for data-driven tests")

        if quality_metrics.documentation_quality < 0.8:
            suggestions.append(
                "Add docstrings to test methods explaining what they verify"
            )
            suggestions.append("Use more descriptive test method names")

        if quality_metrics.edge_case_coverage < 0.8:
            suggestions.append(
                "Add tests for None values, empty inputs, and boundary conditions"
            )
            suggestions.append("Use pytest.raises for exception testing")

        # Based on Sage recommendations
        for sage_name, recommendations in sage_recommendations.items():
            if sage_name == "knowledge_sage" and isinstance(recommendations, dict):
                suggestions.append(
                    f"Knowledge Sage: {recommendations.get('pattern_storage_advice', '')}"
                )
            elif sage_name == "task_sage" and isinstance(recommendations, dict):
                suggestions.append(
                    f"Task Sage: {recommendations.get('workflow_optimization', '')}"
                )
            elif sage_name == "incident_sage" and isinstance(recommendations, dict):
                suggestions.append(
                    f"Incident Sage: {recommendations.get('quality_monitoring', '')}"
                )
            elif sage_name == "rag_sage" and isinstance(recommendations, dict):
                suggestions.append(
                    f"RAG Sage: {recommendations.get('pattern_search', '')}"
                )

        # General best practices
        suggestions.extend(
            [
                "Consider using fixtures for common test data setup",
                "Ensure each test method focuses on a single concern",
                "Add integration tests alongside unit tests",
                "Use meaningful assertion messages for better debugging",
            ]
        )

        return suggestions[:10]  # Limit to top 10 suggestions

    async def _make_elder_decision(
        self,
        quality_metrics: TestQualityMetrics,
        sage_recommendations: Dict[str, Any],
        quality_issues: List[str],
    ) -> Dict[str, Any]:
        """Make final Elder Council decision on test quality"""
        overall_score = quality_metrics.overall_quality_score

        # Determine approval status based on thresholds
        if overall_score >= self.quality_thresholds["elder_approval"]:
            if len(quality_issues) == 0:
                approval_status = "approved"
                decision_explanation = (
                    "Elder Council approves: Excellent test quality meets all standards"
                )
                confidence = 0.95
            else:
                approval_status = "approved_with_recommendations"
                decision_explanation = (
                    "Elder Council approves with minor recommendations for improvement"
                )
                confidence = 0.85
        elif overall_score >= self.quality_thresholds["good_quality"]:
            approval_status = "needs_improvement"
            decision_explanation = "Elder Council requires improvements before approval"
            confidence = 0.75
        else:
            approval_status = "rejected"
            decision_explanation = (
                "Elder Council rejects: Quality below acceptable standards"
            )
            confidence = 0.90

        # Consider Sage consensus
        consensus_reached = sage_recommendations.get("consensus_reached", False)
        if consensus_reached:
            confidence += 0.05  # Boost confidence with Sage consensus

        # Factor in critical issues
        critical_issues = [
            issue
            for issue in quality_issues
            if "trivial assertions" in issue or "too few test" in issue
        ]
        if critical_issues and approval_status == "approved":
            approval_status = "needs_improvement"
            decision_explanation += " - Critical issues detected"
            confidence -= 0.1

        return {
            "approval_status": approval_status,
            "decision_explanation": decision_explanation,
            "confidence_score": min(confidence, 1.0),
            "elder_consensus": consensus_reached,
            "quality_threshold_met": overall_score
            >= self.quality_thresholds["elder_approval"],
        }

    def _read_test_file(self, test_file_path: str) -> Optional[str]:
        """Read test file content"""
        try:
            file_path = Path(test_file_path)
            if not file_path.exists():
                self.logger.error(f"Test file not found: {test_file_path}")
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        except Exception as e:
            self.logger.error(f"Failed to read test file {test_file_path}: {e}")
            return None

    def _create_error_result(
        self, test_file: str, error_message: str
    ) -> QualityReviewResult:
        """Create error result for failed reviews"""
        return QualityReviewResult(
            test_file=test_file,
            quality_metrics=TestQualityMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            sage_recommendations={},
            quality_issues=[f"Review failed: {error_message}"],
            improvement_suggestions=["Fix review errors before proceeding"],
            approval_status="error",
            confidence_score=0.0,
            elder_decision=f"Elder Council review failed: {error_message}",
        )

    async def _save_quality_review(self, review_result: QualityReviewResult):
        """Save quality review results to database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Save main review record
            cursor.execute(
                """
                INSERT INTO quality_reviews
                (test_file, review_timestamp, quality_score, approval_status,
                 sage_recommendations, quality_issues, improvement_suggestions,
                 elder_decision, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    review_result.test_file,
                    datetime.now(),
                    review_result.quality_metrics.overall_quality_score,
                    review_result.approval_status,
                    json.dumps(review_result.sage_recommendations, default=str),
                    json.dumps(review_result.quality_issues),
                    json.dumps(review_result.improvement_suggestions),
                    review_result.elder_decision,
                    review_result.confidence_score,
                ),
            )

            # Save detailed quality metrics
            cursor.execute(
                """
                INSERT INTO quality_metrics_history
                (test_file, timestamp, coverage_effectiveness, test_complexity_score,
                 pattern_compliance, documentation_quality, edge_case_coverage,
                 overall_quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    review_result.test_file,
                    datetime.now(),
                    review_result.quality_metrics.coverage_effectiveness,
                    review_result.quality_metrics.test_complexity_score,
                    review_result.quality_metrics.pattern_compliance,
                    review_result.quality_metrics.documentation_quality,
                    review_result.quality_metrics.edge_case_coverage,
                    review_result.quality_metrics.overall_quality_score,
                ),
            )

            conn.commit()
            conn.close()

            self.logger.info(f"Quality review saved for {review_result.test_file}")

        except Exception as e:
            self.logger.error(f"Failed to save quality review: {e}")

    async def analyze_test_batch(self, test_files: List[str]) -> Dict[str, Any]:
        """Analyze a batch of test files for quality assessment"""
        try:
            self.logger.info(f"Starting batch analysis of {len(test_files)} test files")

            batch_results = []
            quality_distribution = defaultdict(int)
            total_quality_score = 0.0

            for test_file in test_files:
                try:
                    review_result = await self.review_test_quality(test_file)
                    batch_results.append(review_result)

                    # Track quality distribution
                    quality_distribution[review_result.approval_status] += 1
                    total_quality_score += (
                        review_result.quality_metrics.overall_quality_score
                    )

                except Exception as e:
                    self.logger.error(f"Failed to analyze {test_file}: {e}")
                    continue

            # Calculate batch statistics
            avg_quality_score = (
                total_quality_score / len(batch_results) if batch_results else 0.0
            )

            # Generate batch report
            batch_report = {
                "batch_summary": {
                    "total_files_analyzed": len(batch_results),
                    "average_quality_score": avg_quality_score,
                    "quality_distribution": dict(quality_distribution),
                    "analysis_timestamp": datetime.now().isoformat(),
                },
                "quality_breakdown": {
                    "excellent_quality": len(
                        [
                            r
                            for r in batch_results
                            if r.quality_metrics.overall_quality_score >= 0.9
                        ]
                    ),
                    "good_quality": len(
                        [
                            r
                            for r in batch_results
                            if 0.8 <= r.quality_metrics.overall_quality_score < 0.9
                        ]
                    ),
                    "needs_improvement": len(
                        [
                            r
                            for r in batch_results
                            if 0.7 <= r.quality_metrics.overall_quality_score < 0.8
                        ]
                    ),
                    "poor_quality": len(
                        [
                            r
                            for r in batch_results
                            if r.quality_metrics.overall_quality_score < 0.7
                        ]
                    ),
                },
                "detailed_results": [
                    {
                        "test_file": result.test_file,
                        "quality_score": result.quality_metrics.overall_quality_score,
                        "approval_status": result.approval_status,
                        "major_issues": len(result.quality_issues),
                        "confidence": result.confidence_score,
                    }
                    for result in batch_results
                ],
                "elder_council_summary": {
                    "total_approved": quality_distribution.get("approved", 0),
                    "needs_improvement": quality_distribution.get(
                        "needs_improvement", 0
                    ),
                    "rejected": quality_distribution.get("rejected", 0),
                    "overall_batch_quality": self._assess_batch_quality(
                        avg_quality_score, quality_distribution
                    ),
                },
            }

            self.logger.info(
                f"Batch analysis completed: {avg_quality_score:.2f} average quality score"
            )
            return batch_report

        except Exception as e:
            self.logger.error(f"Batch analysis failed: {e}")
            return {
                "batch_summary": {"error": str(e)},
                "analysis_timestamp": datetime.now().isoformat(),
            }

    def _assess_batch_quality(
        self, avg_score: float, distribution: Dict[str, int]
    ) -> str:
        """Assess overall batch quality"""
        approved = distribution.get("approved", 0)
        total = sum(distribution.values())

        if total == 0:
            return "no_data"

        approval_rate = approved / total

        if avg_score >= 0.9 and approval_rate >= 0.8:
            return "excellent"
        elif avg_score >= 0.8 and approval_rate >= 0.6:
            return "good"
        elif avg_score >= 0.7 and approval_rate >= 0.4:
            return "acceptable"
        else:
            return "needs_significant_improvement"

    async def generate_quality_report(self, time_range_days: int = 7) -> Dict[str, Any]:
        """Generate comprehensive quality report for Elder Council review"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=time_range_days)

            # Query database for recent reviews
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Get review statistics
            cursor.execute(
                """
                SELECT approval_status, COUNT(*), AVG(quality_score), AVG(confidence_score)
                FROM quality_reviews
                WHERE review_timestamp >= ?
                GROUP BY approval_status
            """,
                (start_date,),
            )

            status_stats = {}
            for row in cursor.fetchall():
                status_stats[row[0]] = {
                    "count": row[1],
                    "avg_quality": row[2],
                    "avg_confidence": row[3],
                }

            # Get quality trends
            cursor.execute(
                """
                SELECT DATE(review_timestamp) as review_date,
                       AVG(quality_score) as avg_quality,
                       COUNT(*) as reviews_count
                FROM quality_reviews
                WHERE review_timestamp >= ?
                GROUP BY DATE(review_timestamp)
                ORDER BY review_date
            """,
                (start_date,),
            )

            quality_trends = [
                {"date": row[0], "avg_quality": row[1], "reviews_count": row[2]}
                for row in cursor.fetchall()
            ]

            # Get most common issues
            cursor.execute(
                """
                SELECT quality_issues
                FROM quality_reviews
                WHERE review_timestamp >= ? AND quality_issues != '[]'
            """,
                (start_date,),
            )

            all_issues = []
            for row in cursor.fetchall():
                try:
                    issues = json.loads(row[0])
                    all_issues.extend(issues)
                except:
                    continue

            issue_frequency = Counter(all_issues)

            conn.close()

            # Generate 4 Sages analytics
            sages_analytics = self.four_sages.get_integration_analytics(time_range_days)

            # Compile comprehensive report
            quality_report = {
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": time_range_days,
                },
                "quality_overview": {
                    "total_reviews": sum(
                        stats["count"] for stats in status_stats.values()
                    ),
                    "approval_status_distribution": status_stats,
                    "overall_quality_trend": self._analyze_quality_trend(
                        quality_trends
                    ),
                },
                "quality_metrics_analysis": {
                    "quality_trends": quality_trends,
                    "most_common_issues": dict(issue_frequency.most_common(10)),
                    "quality_improvement_areas": self._identify_improvement_areas(
                        issue_frequency
                    ),
                },
                "four_sages_insights": {
                    "sages_analytics": sages_analytics,
                    "consensus_rate": sages_analytics.get(
                        "learning_session_analytics", {}
                    ).get("consensus_rate", 0),
                    "sage_effectiveness": sages_analytics.get("sage_effectiveness", {}),
                    "improvement_opportunities": sages_analytics.get(
                        "improvement_opportunities", []
                    ),
                },
                "elder_council_recommendations": {
                    "strategic_focus": self._generate_strategic_recommendations(
                        status_stats, quality_trends
                    ),
                    "immediate_actions": self._generate_immediate_actions(
                        issue_frequency
                    ),
                    "long_term_initiatives": self._generate_long_term_initiatives(
                        sages_analytics
                    ),
                },
                "coverage_achievement_status": {
                    "current_coverage_quality": self._assess_coverage_quality(
                        status_stats
                    ),
                    "maintenance_recommendations": self._generate_maintenance_recommendations(),
                    "elder_council_confidence": self._calculate_elder_confidence(
                        status_stats, quality_trends
                    ),
                },
            }

            self.logger.info("Comprehensive quality report generated for Elder Council")
            return quality_report

        except Exception as e:
            self.logger.error(f"Quality report generation failed: {e}")
            return {"error": str(e), "report_timestamp": datetime.now().isoformat()}

    def _analyze_quality_trend(self, quality_trends: List[Dict]) -> str:
        """Analyze overall quality trend"""
        if len(quality_trends) < 2:
            return "insufficient_data"

        recent_avg = sum(trend["avg_quality"] for trend in quality_trends[-3:]) / min(
            3, len(quality_trends)
        )
        earlier_avg = sum(trend["avg_quality"] for trend in quality_trends[:3]) / min(
            3, len(quality_trends)
        )

        if recent_avg > earlier_avg + 0.05:
            return "improving"
        elif recent_avg < earlier_avg - 0.05:
            return "declining"
        else:
            return "stable"

    def _identify_improvement_areas(self, issue_frequency: Counter) -> List[str]:
        """Identify key areas for quality improvement"""
        top_issues = issue_frequency.most_common(5)
        areas = []

        for issue, count in top_issues:
            if "coverage" in issue.lower():
                areas.append("Test Coverage Enhancement")
            elif "documentation" in issue.lower():
                areas.append("Documentation Quality")
            elif "complexity" in issue.lower():
                areas.append("Test Simplification")
            elif "edge case" in issue.lower():
                areas.append("Edge Case Testing")
            elif "pattern" in issue.lower():
                areas.append("Pattern Compliance")

        return list(set(areas))  # Remove duplicates

    def _generate_strategic_recommendations(
        self, status_stats: Dict, quality_trends: List
    ) -> List[str]:
        """Generate strategic recommendations for Elder Council"""
        recommendations = []

        total_reviews = sum(stats["count"] for stats in status_stats.values())
        approved = status_stats.get("approved", {}).get("count", 0)

        if total_reviews > 0:
            approval_rate = approved / total_reviews

            if approval_rate < 0.6:
                recommendations.append(
                    "Urgent: Implement quality training and review processes"
                )
                recommendations.append("Focus on improving test pattern compliance")
            elif approval_rate < 0.8:
                recommendations.append("Enhance quality guidelines and best practices")
                recommendations.append(
                    "Increase 4 Sages integration for better quality insights"
                )
            else:
                recommendations.append("Maintain current quality standards")
                recommendations.append(
                    "Explore advanced quality optimization opportunities"
                )

        recommendations.extend(
            [
                "Continue 4 Sages collaborative quality reviews",
                "Implement proactive quality monitoring",
                "Establish quality mentorship programs",
            ]
        )

        return recommendations

    def _generate_immediate_actions(self, issue_frequency: Counter) -> List[str]:
        """Generate immediate action items"""
        actions = []
        top_issues = issue_frequency.most_common(3)

        for issue, count in top_issues:
            if count > 5:  # Frequent issue
                actions.append(f"Address frequent issue: {issue}")

        actions.extend(
            [
                "Review and update quality thresholds",
                "Enhance automated quality gate enforcement",
                "Schedule Elder Council quality review session",
            ]
        )

        return actions

    def _generate_long_term_initiatives(self, sages_analytics: Dict) -> List[str]:
        """Generate long-term quality initiatives"""
        return [
            "Develop AI-powered quality prediction system",
            "Expand 4 Sages integration for proactive quality management",
            "Create quality excellence certification program",
            "Implement cross-project quality knowledge sharing",
            "Establish quality metrics evolution framework",
        ]

    def _assess_coverage_quality(self, status_stats: Dict) -> str:
        """Assess current coverage quality status"""
        total = sum(stats["count"] for stats in status_stats.values())
        approved = status_stats.get("approved", {}).get("count", 0)

        if total == 0:
            return "no_data"

        approval_rate = approved / total

        if approval_rate >= 0.9:
            return "excellent"
        elif approval_rate >= 0.8:
            return "good"
        elif approval_rate >= 0.7:
            return "acceptable"
        else:
            return "needs_improvement"

    def _generate_maintenance_recommendations(self) -> List[str]:
        """Generate maintenance recommendations for coverage quality"""
        return [
            "Continue regular Elder Council quality reviews",
            "Maintain 4 Sages integration for ongoing quality insights",
            "Monitor quality trends and proactively address degradation",
            "Ensure quality gates remain effective and up-to-date",
            "Regular training on quality best practices",
        ]

    def _calculate_elder_confidence(
        self, status_stats: Dict, quality_trends: List
    ) -> float:
        """Calculate Elder Council confidence in quality system"""
        # Base confidence from approval rates
        total = sum(stats["count"] for stats in status_stats.values())
        approved = status_stats.get("approved", {}).get("count", 0)

        if total == 0:
            return 0.5

        approval_rate = approved / total
        base_confidence = approval_rate

        # Adjust for quality trends
        if quality_trends:
            recent_quality = sum(
                trend["avg_quality"] for trend in quality_trends[-3:]
            ) / min(3, len(quality_trends))
            base_confidence = (base_confidence + recent_quality) / 2

        # Boost confidence with 4 Sages integration
        base_confidence += 0.1  # Boost for Sages integration

        return min(base_confidence, 1.0)


# Utility functions for external use
async def review_single_test(test_file_path: str) -> QualityReviewResult:
    """Utility function to review a single test file"""
    elder_council = ElderCouncilReview()
    return await elder_council.review_test_quality(test_file_path)


async def analyze_project_tests(
    test_directory: str = "/home/aicompany/ai_co/tests",
) -> Dict[str, Any]:
    """Utility function to analyze all tests in project"""
    elder_council = ElderCouncilReview()

    # Find all test files
    test_files = []
    test_dir = Path(test_directory)

    if test_dir.exists():
        for test_file in test_dir.rglob("test_*.py"):
            test_files.append(str(test_file))

    return await elder_council.analyze_test_batch(test_files)


if __name__ == "__main__":
    # Example usage
    import asyncio

    async def main():
        elder_council = ElderCouncilReview()

        # Example: Review a single test file
        test_file = "/home/aicompany/ai_co/workers/test_generator_worker.py"
        result = await elder_council.review_test_quality(test_file)

        print(f"Quality Review Results for {test_file}:")
        print(
            f"Overall Quality Score: {result.quality_metrics.overall_quality_score:.2f}"
        )
        print(f"Approval Status: {result.approval_status}")
        print(f"Elder Decision: {result.elder_decision}")

        if result.quality_issues:
            print("\nQuality Issues:")
            for issue in result.quality_issues:
                print(f"  - {issue}")

        if result.improvement_suggestions:
            print("\nImprovement Suggestions:")
            for suggestion in result.improvement_suggestions[:5]:
                print(f"  - {suggestion}")

    asyncio.run(main())
