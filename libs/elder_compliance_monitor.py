#!/usr/bin/env python3
"""
Elder Compliance Monitor - Automatic Claude Elder Protocol Enforcement
Monitors and enforces Universal Claude Elder Standards for Elder Servant coordination
"""

import asyncio
import json
import logging
import os
import re
import sqlite3
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ViolationType(Enum):
    """Types of compliance violations"""

    INDEPENDENT_WORK = "independent_work"
    MISSING_SERVANTS = "missing_servants"
    NO_REPORTING = "no_reporting"
    AUTHORITY_BYPASS = "authority_bypass"
    RESOURCE_CONFLICT = "resource_conflict"
    SILENT_OPERATION = "silent_operation"


class ComplianceLevel(Enum):
    """Compliance levels for violations"""

    COMPLIANT = "compliant"
    WARNING = "warning"
    VIOLATION = "violation"
    CRITICAL = "critical"


@dataclass
class ComplianceViolation:
    """Represents a compliance violation"""

    violation_type: ViolationType
    severity: ComplianceLevel
    description: str
    detected_at: datetime
    elder_instance: str
    evidence: Dict[str, Any]
    auto_corrected: bool = False
    escalated: bool = False


@dataclass
class ElderServantDeployment:
    """Represents an Elder Servant deployment"""

    servant_type: str
    deployment_id: str
    deployed_at: datetime
    status: str
    assigned_elder: str
    task_description: str
    progress_reports: List[Dict] = None

    def __post_init__(self):
        """__post_init__特殊メソッド"""
        if self.progress_reports is None:
            self.progress_reports = []


class ElderComplianceMonitor:
    """
    Monitors Claude Elder instances for protocol compliance
    Automatically enforces Universal Claude Elder Standards
    """

    def __init__(self, data_dir: str = "data/compliance"):
        """初期化メソッド"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self.db_path = self.data_dir / "compliance.db"
        self.init_database()

        # Compliance patterns
        self.non_compliant_patterns = {
            ViolationType.INDEPENDENT_WORK: [
                r"I'll implement this myself",
                r"Let me write the code directly",
                r"I'll handle this task personally",
                r"I'm going to create this file",
                r"I'll modify this directly",
                r"I will code this",
                r"I'll write this function",
                r"Let me implement",
                r"I'll directly modify",
            ],
            ViolationType.MISSING_SERVANTS: [
                r"I'll do this without help",
                r"No need for servants",
                r"I can handle this alone",
                r"Simple task, I'll do it myself",
            ],
            ViolationType.SILENT_OPERATION: [
                r"Working quietly",
                r"No need to report",
                r"I'll work in silence",
                r"No updates needed",
            ],
        }

        self.compliant_patterns = [
            r"I'll deploy the (.*) Knight",
            r"Let me coordinate multiple servants",
            r"I'll assign this to the appropriate servant",
            r"Deploying specialized knight for this task",
            r"Coordinating parallel servant deployment",
            r"I'll summon the (.*) to handle this",
            r"Delegating to Elder Servants",
            r"Orchestrating servant coordination",
            r"I'll deploy multiple servants",
            r"Coordinating with the Elder Council",
        ]

        # Active monitoring
        self.monitoring_active = False
        self.compliance_history = []
        self.active_deployments = {}

        # Performance metrics
        self.metrics = {
            "violations_detected": 0,
            "violations_corrected": 0,
            "servants_deployed": 0,
            "compliance_rate": 100.0,
            "last_violation": None,
            "monitoring_uptime": 0.0,
        }

        logger.info("Elder Compliance Monitor initialized")

    def init_database(self):
        """Initialize compliance tracking database"""
        with sqlite3connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    violation_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT NOT NULL,
                    detected_at TIMESTAMP NOT NULL,
                    elder_instance TEXT NOT NULL,
                    evidence TEXT NOT NULL,
                    auto_corrected BOOLEAN DEFAULT FALSE,
                    escalated BOOLEAN DEFAULT FALSE
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS deployments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    servant_type TEXT NOT NULL,
                    deployment_id TEXT NOT NULL,
                    deployed_at TIMESTAMP NOT NULL,
                    status TEXT NOT NULL,
                    assigned_elder TEXT NOT NULL,
                    task_description TEXT NOT NULL,
                    progress_reports TEXT DEFAULT '[]'
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS compliance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recorded_at TIMESTAMP NOT NULL,
                    compliance_rate REAL NOT NULL,
                    violations_count INTEGER NOT NULL,
                    servants_deployed INTEGER NOT NULL,
                    metrics_data TEXT NOT NULL
                )
            """
            )

    def check_compliance(
        self, elder_instance: str, activity_log: List[str], current_task: str = None
    ) -> List[ComplianceViolation]:
        """
        Check compliance of a Claude Elder instance

        Args:
            elder_instance: Identifier for the Elder instance
            activity_log: List of recent activities/messages
            current_task: Current task being performed

        Returns:
            List of compliance violations
        """
        violations = []

        # Check for independent work patterns
        violations.extend(self._check_independent_work(elder_instance, activity_log))

        # Check for missing servant delegation
        violations.extend(self._check_missing_servants(elder_instance, activity_log))

        # Check for progress reporting
        violations.extend(self._check_progress_reporting(elder_instance))

        # Check for authority bypass
        violations.extend(self._check_authority_bypass(elder_instance, activity_log))

        # Check for resource conflicts
        violations.extend(self._check_resource_conflicts(elder_instance))

        # Record violations
        for violation in violations:
            self._record_violation(violation)

        # Update metrics
        self.metrics["violations_detected"] += len(violations)
        if violations:
            self.metrics["last_violation"] = datetime.now()

        return violations

    def _check_independent_work(
        self, elder_instance: str, activity_log: List[str]
    ) -> List[ComplianceViolation]:
        """Check for independent work violations"""
        violations = []

        for activity in activity_log:
            for pattern in self.non_compliant_patterns[ViolationType.INDEPENDENT_WORK]:
                if re.search(pattern, activity, re.IGNORECASE):
                    violations.append(
                        ComplianceViolation(
                            violation_type=ViolationType.INDEPENDENT_WORK,
                            severity=ComplianceLevel.VIOLATION,
                            description=f"Independent work detected: {activity[:100]}...",
                            detected_at=datetime.now(),
                            elder_instance=elder_instance,
                            evidence={"activity": activity, "pattern": pattern},
                        )
                    )
                    break

        return violations

    def _check_missing_servants(
        self, elder_instance: str, activity_log: List[str]
    ) -> List[ComplianceViolation]:
        """Check for missing servant delegation"""
        violations = []

        # Check if there are any active servant deployments
        if not self._has_active_servants(elder_instance):
            # Check if there's ongoing work that should be delegated
            work_indicators = [
                "implementing",
                "creating",
                "writing",
                "modifying",
                "building",
                "developing",
                "coding",
                "fixing",
            ]

            for activity in activity_log:
                if any(indicator in activity.lower() for indicator in work_indicators):
                    # Check if this is being delegated to servants
                    if not any(
                        re.search(pattern, activity, re.IGNORECASE)
                        for pattern in self.compliant_patterns
                    ):
                        violations.append(
                            ComplianceViolation(
                                violation_type=ViolationType.MISSING_SERVANTS,
                                severity=ComplianceLevel.WARNING,
                                description="Work detected without servant delegation",
                                detected_at=datetime.now(),
                                elder_instance=elder_instance,
                                evidence={"activity": activity},
                            )
                        )
                        break

        return violations

    def _check_progress_reporting(
        self, elder_instance: str
    ) -> List[ComplianceViolation]:
        """Check for progress reporting violations"""
        violations = []

        # Check if there are active deployments without recent reports
        last_report = self._get_last_progress_report(elder_instance)
        if last_report:
            time_since_report = datetime.now() - last_report
            if time_since_report > timedelta(minutes=15):
                violations.append(
                    ComplianceViolation(
                        violation_type=ViolationType.NO_REPORTING,
                        severity=ComplianceLevel.WARNING,
                        description=f"No progress report in {time_since_report.total_seconds()//60} " \
                            "minutes",
                        detected_at=datetime.now(),
                        elder_instance=elder_instance,
                        evidence={"last_report": last_report.isoformat()},
                    )
                )

        return violations

    def _check_authority_bypass(
        self, elder_instance: str, activity_log: List[str]
    ) -> List[ComplianceViolation]:
        """Check for authority bypass violations"""
        violations = []

        bypass_patterns = [
            r"bypassing approval",
            r"skipping Elder Council",
            r"without permission",
            r"ignoring protocol",
        ]

        for activity in activity_log:
            for pattern in bypass_patterns:
                if re.search(pattern, activity, re.IGNORECASE):
                    violations.append(
                        ComplianceViolation(
                            violation_type=ViolationType.AUTHORITY_BYPASS,
                            severity=ComplianceLevel.CRITICAL,
                            description="Authority bypass detected",
                            detected_at=datetime.now(),
                            elder_instance=elder_instance,
                            evidence={"activity": activity, "pattern": pattern},
                        )
                    )
                    break

        return violations

    def _check_resource_conflicts(
        self, elder_instance: str
    ) -> List[ComplianceViolation]:
        """Check for resource conflicts between servants"""
        violations = []

        # Check for overlapping servant deployments
        active_servants = self._get_active_servants(elder_instance)

        # Look for potential conflicts
        conflict_pairs = [
            ("Coverage Enhancement Knight", "Test Runner"),
            ("Dwarf Workshop", "Performance Optimizer"),
            ("API Integration Knight", "Connection Manager"),
        ]

        deployed_types = [s["servant_type"] for s in active_servants]

        for type1, type2 in conflict_pairs:
            if type1 in deployed_types and type2 in deployed_types:
                violations.append(
                    ComplianceViolation(
                        violation_type=ViolationType.RESOURCE_CONFLICT,
                        severity=ComplianceLevel.WARNING,
                        description=f"Potential resource conflict: {type1} and {type2}",
                        detected_at=datetime.now(),
                        elder_instance=elder_instance,
                        evidence={"conflicting_servants": [type1, type2]},
                    )
                )

        return violations

    def enforce_compliance(self, violations: List[ComplianceViolation]) -> List[str]:
        """
        Automatically enforce compliance by correcting violations

        Args:
            violations: List of violations to correct

        Returns:
            List of correction actions taken
        """
        actions = []

        for violation in violations:
            try:
                if violation.violation_type == ViolationType.INDEPENDENT_WORK:
                    action = self._redirect_to_servant_deployment(violation)

                elif violation.violation_type == ViolationType.MISSING_SERVANTS:
                    action = self._auto_deploy_servants(violation)

                elif violation.violation_type == ViolationType.NO_REPORTING:
                    action = self._generate_progress_report(violation)

                elif violation.violation_type == ViolationType.AUTHORITY_BYPASS:
                    action = self._escalate_to_elder_council(violation)

                elif violation.violation_type == ViolationType.RESOURCE_CONFLICT:
                    action = self._resolve_resource_conflict(violation)

                else:
                    action = f"Unknown violation type: {violation.violation_type}"

                actions.append(action)

                # Mark as auto-corrected
                violation.auto_corrected = True
                self._update_violation_status(violation)

                self.metrics["violations_corrected"] += 1

            except Exception as e:
                logger.error(
                    f"Failed to enforce compliance for {violation.violation_type}: {e}"
                )
                actions.append(
                    f"Failed to correct {violation.violation_type}: {str(e)}"
                )

        return actions

    def _redirect_to_servant_deployment(self, violation: ComplianceViolation) -> str:
        """Redirect independent work to servant deployment"""
        # Determine appropriate servant type based on the work
        activity = violation.evidence.get("activity", "")

        if "test" in activity.lower():
            servant_type = "Coverage Enhancement Knight"
        elif "performance" in activity.lower():
            servant_type = "Dwarf Workshop"
        elif "api" in activity.lower():
            servant_type = "API Integration Knight"
        elif "error" in activity.lower() or "fix" in activity.lower():
            servant_type = "Incident Knights"
        else:
            servant_type = "General Purpose Knight"

        # Deploy the servant
        deployment_id = self._deploy_servant(
            servant_type=servant_type,
            elder_instance=violation.elder_instance,
            task_description=f"Redirected from independent work: {activity[:100]}",
        )

        return f"Redirected to {servant_type} deployment: {deployment_id}"

    def _auto_deploy_servants(self, violation: ComplianceViolation) -> str:
        """Automatically deploy appropriate servants"""
        activity = violation.evidence.get("activity", "")

        # Deploy multiple servants for complex tasks
        servants_to_deploy = []

        if "implement" in activity.lower():
            servants_to_deploy.extend(
                ["Coverage Enhancement Knight", "Syntax Repair Knight"]
            )
        elif "system" in activity.lower():
            servants_to_deploy.extend(["Dwarf Workshop", "Worker Stabilization Knight"])
        elif "fix" in activity.lower():
            servants_to_deploy.extend(["Incident Knights", "Auto Repair Knight"])
        else:
            servants_to_deploy.append("General Purpose Knight")

        deployments = []
        for servant_type in servants_to_deploy:
            deployment_id = self._deploy_servant(
                servant_type=servant_type,
                elder_instance=violation.elder_instance,
                task_description=f"Auto-deployed for: {activity[:100]}",
            )
            deployments.append(deployment_id)

        return f"Auto-deployed servants: {', '.join(deployments)}"

    def _generate_progress_report(self, violation: ComplianceViolation) -> str:
        """Generate and submit progress report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "elder_instance": violation.elder_instance,
            "status": "auto_generated",
            "active_servants": len(self._get_active_servants(violation.elder_instance)),
            "recent_activity": "Compliance monitoring detected missing reports",
            "next_checkpoint": (datetime.now() + timedelta(minutes=15)).isoformat(),
        }

        # Save progress report
        self._save_progress_report(violation.elder_instance, report)

        return f"Generated progress report for {violation.elder_instance}"

    def _escalate_to_elder_council(self, violation: ComplianceViolation) -> str:
        """Escalate critical violations to Elder Council"""
        escalation = {
            "timestamp": datetime.now().isoformat(),
            "violation_type": violation.violation_type.value,
            "severity": violation.severity.value,
            "elder_instance": violation.elder_instance,
            "description": violation.description,
            "evidence": violation.evidence,
            "urgency": "immediate",
        }

        # Save escalation
        escalation_file = self.data_dir / f"escalation_{int(time.time())}.json"
        with open(escalation_file, "w") as f:
            json.dump(escalation, f, indent=2)

        # Mark as escalated
        violation.escalated = True

        return f"Escalated to Elder Council: {escalation_file.name}"

    def _resolve_resource_conflict(self, violation: ComplianceViolation) -> str:
        """Resolve resource conflicts between servants"""
        conflicting_servants = violation.evidence.get("conflicting_servants", [])

        # Prioritize servants based on importance
        priority_order = [
            "Coverage Enhancement Knight",
            "Incident Knights",
            "Dwarf Workshop",
            "API Integration Knight",
        ]

        # Keep the higher priority servant, suspend the lower one
        for servant in priority_order:
            if servant in conflicting_servants:
                # Keep this one, suspend others
                for other_servant in conflicting_servants:
                    if other_servant != servant:
                        self._suspend_servant(other_servant, violation.elder_instance)
                        return f"Suspended {other_servant} to resolve conflict with {servant}"

        return "Resource conflict resolution completed"

    def _deploy_servant(
        self, servant_type: str, elder_instance: str, task_description: str
    ) -> str:
        """Deploy a specific servant type"""
        deployment_id = f"{servant_type.lower().replace(' ', '_')}_{int(time.time())}"

        deployment = ElderServantDeployment(
            servant_type=servant_type,
            deployment_id=deployment_id,
            deployed_at=datetime.now(),
            status="active",
            assigned_elder=elder_instance,
            task_description=task_description,
        )

        # Save deployment
        self._save_deployment(deployment)

        self.metrics["servants_deployed"] += 1

        logger.info(f"Deployed {servant_type} as {deployment_id}")

        return deployment_id

    def _suspend_servant(self, servant_type: str, elder_instance: str):
        """Suspend a servant to resolve conflicts"""
        with sqlite3connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE deployments
                SET status = 'suspended'
                WHERE servant_type = ? AND assigned_elder = ? AND status = 'active'
            """,
                (servant_type, elder_instance),
            )

    def _has_active_servants(self, elder_instance: str) -> bool:
        """Check if elder has active servants"""
        return len(self._get_active_servants(elder_instance)) > 0

    def _get_active_servants(self, elder_instance: str) -> List[Dict]:
        """Get active servants for an elder"""
        with sqlite3connect(self.db_path) as conn:
            conn.row_factory = sqlite3Row
            cursor = conn.execute(
                """
                SELECT * FROM deployments
                WHERE assigned_elder = ? AND status = 'active'
            """,
                (elder_instance,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def _get_last_progress_report(self, elder_instance: str) -> Optional[datetime]:
        """Get timestamp of last progress report"""
        # Check deployment progress reports
        with sqlite3connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT MAX(deployed_at) FROM deployments
                WHERE assigned_elder = ? AND progress_reports != '[]'
            """,
                (elder_instance,),
            )
            result = cursor.fetchone()

            if result[0]:
                return datetime.fromisoformat(result[0])

        return None

    def _save_progress_report(self, elder_instance: str, report: Dict):
        """Save progress report"""
        progress_file = (
            self.data_dir / f"progress_{elder_instance}_{int(time.time())}.json"
        )
        with open(progress_file, "w") as f:
            json.dump(report, f, indent=2)

    def _save_deployment(self, deployment: ElderServantDeployment):
        """Save deployment to database"""
        with sqlite3connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO deployments
                (servant_type, deployment_id, deployed_at, status, assigned_elder, task_description, progress_reports)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    deployment.servant_type,
                    deployment.deployment_id,
                    deployment.deployed_at.isoformat(),
                    deployment.status,
                    deployment.assigned_elder,
                    deployment.task_description,
                    json.dumps(deployment.progress_reports),
                ),
            )

    def _record_violation(self, violation: ComplianceViolation):
        """Record violation in database"""
        with sqlite3connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO violations
                 \
                    (
                        violation_type,
                        severity,
                        description,
                        detected_at,
                        elder_instance,
                        evidence,
                        auto_corrected,
                        escalated
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    violation.violation_type.value,
                    violation.severity.value,
                    violation.description,
                    violation.detected_at.isoformat(),
                    violation.elder_instance,
                    json.dumps(violation.evidence),
                    violation.auto_corrected,
                    violation.escalated,
                ),
            )

    def _update_violation_status(self, violation: ComplianceViolation):
        """Update violation status in database"""
        with sqlite3connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE violations
                SET auto_corrected = ?, escalated = ?
                WHERE violation_type = ? AND elder_instance = ? AND detected_at = ?
            """,
                (
                    violation.auto_corrected,
                    violation.escalated,
                    violation.violation_type.value,
                    violation.elder_instance,
                    violation.detected_at.isoformat(),
                ),
            )

    def get_compliance_report(self, elder_instance: str = None) -> Dict:
        """Generate compliance report"""
        with sqlite3connect(self.db_path) as conn:
            conn.row_factory = sqlite3Row

            # Get violations
            if elder_instance:
                violations_query = "SELECT * FROM violations WHERE elder_instance = ?"
                violations_params = (elder_instance,)
            else:
                violations_query = "SELECT * FROM violations"
                violations_params = ()

            violations = conn.execute(violations_query, violations_params).fetchall()

            # Get deployments
            if elder_instance:
                deployments_query = "SELECT * FROM deployments WHERE assigned_elder = ?"
                deployments_params = (elder_instance,)
            else:
                deployments_query = "SELECT * FROM deployments"
                deployments_params = ()

            deployments = conn.execute(deployments_query, deployments_params).fetchall()

        # Calculate compliance rate
        total_activities = len(violations) + len(deployments)
        if total_activities > 0:
            compliance_rate = (1 - len(violations) / total_activities) * 100
        else:
            compliance_rate = 100.0

        return {
            "compliance_rate": compliance_rate,
            "total_violations": len(violations),
            "total_deployments": len(deployments),
            "violations_by_type": self._group_violations_by_type(violations),
            "deployments_by_type": self._group_deployments_by_type(deployments),
            "recent_violations": [dict(v) for v in violations[-10:]],
            "active_deployments": [
                dict(d) for d in deployments if d["status"] == "active"
            ],
            "metrics": self.metrics,
        }

    def _group_violations_by_type(self, violations) -> Dict:
        """Group violations by type"""
        grouped = {}
        for violation in violations:
            vtype = violation["violation_type"]
            if vtype not in grouped:
                grouped[vtype] = 0
            grouped[vtype] += 1
        return grouped

    def _group_deployments_by_type(self, deployments) -> Dict:
        """Group deployments by type"""
        grouped = {}
        for deployment in deployments:
            dtype = deployment["servant_type"]
            if dtype not in grouped:
                grouped[dtype] = 0
            grouped[dtype] += 1
        return grouped

    async def start_continuous_monitoring(self, interval: int = 300):
        """Start continuous monitoring of compliance"""
        self.monitoring_active = True
        logger.info(
            f"Starting continuous compliance monitoring (interval: {interval}s)"
        )

        start_time = time.time()

        while self.monitoring_active:
            try:
                # This would typically integrate with the actual Claude instances
                # For now, it's a placeholder for the monitoring logic
                await asyncio.sleep(interval)

                # Update uptime
                self.metrics["monitoring_uptime"] = time.time() - start_time

                # Save metrics
                self._save_metrics()

            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                await asyncio.sleep(60)  # Brief pause before retrying

    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring_active = False
        logger.info("Stopped compliance monitoring")

    def _save_metrics(self):
        """Save current metrics to database"""
        with sqlite3connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO compliance_metrics
                (recorded_at, compliance_rate, violations_count, servants_deployed, metrics_data)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    datetime.now().isoformat(),
                    self.metrics["compliance_rate"],
                    self.metrics["violations_detected"],
                    self.metrics["servants_deployed"],
                    json.dumps(self.metrics),
                ),
            )


# CLI interface for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Elder Compliance Monitor")
    parser.add_argument("--check", help="Check compliance for elder instance")
    parser.add_argument("--report", help="Generate compliance report")
    parser.add_argument(
        "--monitor", action="store_true", help="Start continuous monitoring"
    )
    parser.add_argument(
        "--interval", type=int, default=300, help="Monitoring interval (seconds)"
    )

    args = parser.parse_args()

    monitor = ElderComplianceMonitor()

    if args.check:
        # Example compliance check
        sample_log = [
            "I'll implement this feature myself",
            "Let me write the code directly",
            "Deploying Coverage Enhancement Knight for testing",
        ]

        violations = monitor.check_compliance(args.check, sample_log)
        print(f"Found {len(violations)} violations:")
        for v in violations:
            print(f"  - {v.violation_type.value}: {v.description}")

        if violations:
            actions = monitor.enforce_compliance(violations)
            print(f"Correction actions: {actions}")

    elif args.report:
        report = monitor.get_compliance_report(args.report)
        print(json.dumps(report, indent=2))

    elif args.monitor:
        print(f"Starting continuous monitoring (interval: {args.interval}s)")
        print("Press Ctrl+C to stop")
        try:
            asyncio.run(monitor.start_continuous_monitoring(args.interval))
        except KeyboardInterrupt:
            print("\nStopping monitoring...")
            monitor.stop_monitoring()
