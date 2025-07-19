#!/usr/bin/env python3
"""
AI Elder Compliance Management Command
Manages Elder Servant coordination protocol compliance
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from libs.elder_compliance_monitor import (
    ComplianceLevel,
    ElderComplianceMonitor,
    ViolationType,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ElderComplianceManager:
    """
    Command-line interface for Elder Compliance Management
    Enforces Universal Claude Elder Standards
    """

    def __init__(self):
        self.monitor = ElderComplianceMonitor()
        self.commands = {
            "check": self.check_compliance,
            "enforce": self.enforce_compliance,
            "report": self.generate_report,
            "monitor": self.start_monitoring,
            "stop": self.stop_monitoring,
            "status": self.show_status,
            "deploy": self.deploy_servant,
            "simulate": self.simulate_violation,
            "help": self.show_help,
        }

    def run(self, args):
        """Main entry point for CLI"""
        if not args.command:
            self.show_help()
            return

        if args.command in self.commands:
            try:
                self.commands[args.command](args)
            except Exception as e:
                logger.error(f"Error executing {args.command}: {e}")
                sys.exit(1)
        else:
            print(f"Unknown command: {args.command}")
            self.show_help()
            sys.exit(1)

    def check_compliance(self, args):
        """Check compliance for a specific elder instance"""
        elder_instance = args.elder or "default_elder"

        # Sample activity log (in real implementation, this would come from actual monitoring)
        sample_activities = [
            "I'll implement this feature myself",
            "Let me write the code directly",
            "Deploying Coverage Enhancement Knight for testing",
            "Coordinating with multiple servants",
            "I'll handle this task personally",
        ]

        if args.activity_log:
            # Load activities from file
            with open(args.activity_log, "r") as f:
                sample_activities = json.load(f)

        print(f"🔍 Checking compliance for Elder: {elder_instance}")
        print(f"📋 Analyzing {len(sample_activities)} activities...")

        violations = self.monitor.check_compliance(elder_instance, sample_activities)

        if violations:
            print(f"\n⚠️  Found {len(violations)} compliance violations:")
            for i, violation in enumerate(violations, 1):
                print(f"  {i}. {violation.violation_type.value.upper()}")
                print(f"     Severity: {violation.severity.value}")
                print(f"     Description: {violation.description}")
                print(f"     Evidence: {violation.evidence}")
                print()

            if args.auto_correct:
                print("🔧 Auto-correcting violations...")
                actions = self.monitor.enforce_compliance(violations)
                print("✅ Correction actions taken:")
                for action in actions:
                    print(f"  - {action}")
        else:
            print("✅ No compliance violations found. Elder is operating correctly.")

        # Show compliance score
        report = self.monitor.get_compliance_report(elder_instance)
        print(f"\n📊 Compliance Score: {report['compliance_rate']:.1f}%")

    def enforce_compliance(self, args):
        """Enforce compliance by correcting violations"""
        elder_instance = args.elder or "default_elder"

        print(f"🛡️ Enforcing compliance for Elder: {elder_instance}")

        # Get recent violations
        report = self.monitor.get_compliance_report(elder_instance)
        recent_violations = report.get("recent_violations", [])

        if not recent_violations:
            print("✅ No recent violations to correct.")
            return

        print(f"🔧 Correcting {len(recent_violations)} violations...")

        # Convert to violation objects for enforcement
        violations = []
        for v_data in recent_violations:
            if not v_data.get("auto_corrected", False):
                violations.append(self._create_violation_from_data(v_data))

        if violations:
            actions = self.monitor.enforce_compliance(violations)
            print("✅ Enforcement actions completed:")
            for action in actions:
                print(f"  - {action}")
        else:
            print("✅ All violations have already been corrected.")

    def generate_report(self, args):
        """Generate compliance report"""
        elder_instance = args.elder if args.elder else None

        print("📊 Generating Elder Compliance Report...")
        print("=" * 60)

        report = self.monitor.get_compliance_report(elder_instance)

        # Overall compliance
        print(f"🎯 Overall Compliance Rate: {report['compliance_rate']:.1f}%")
        print(f"📈 Total Violations: {report['total_violations']}")
        print(f"🚀 Total Servant Deployments: {report['total_deployments']}")
        print()

        # Violations by type
        if report["violations_by_type"]:
            print("⚠️  Violations by Type:")
            for vtype, count in report["violations_by_type"].items():
                print(f"  - {vtype}: {count}")
            print()

        # Deployments by type
        if report["deployments_by_type"]:
            print("🛡️ Servant Deployments by Type:")
            for dtype, count in report["deployments_by_type"].items():
                print(f"  - {dtype}: {count}")
            print()

        # Active deployments
        if report["active_deployments"]:
            print(f"🔄 Active Deployments ({len(report['active_deployments'])}):")
            for deployment in report["active_deployments"]:
                print(
                    f"  - {deployment['servant_type']}: {deployment['deployment_id']}"
                )
                print(f"    Status: {deployment['status']}")
                print(f"    Task: {deployment['task_description'][:50]}...")
                print()

        # Metrics
        metrics = report["metrics"]
        print("📊 Performance Metrics:")
        print(f"  - Violations Detected: {metrics['violations_detected']}")
        print(f"  - Violations Corrected: {metrics['violations_corrected']}")
        print(f"  - Servants Deployed: {metrics['servants_deployed']}")
        print(f"  - Monitoring Uptime: {metrics['monitoring_uptime']:.1f}s")

        if metrics["last_violation"]:
            print(f"  - Last Violation: {metrics['last_violation']}")

        # Save report if requested
        if args.output:
            with open(args.output, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\n💾 Report saved to: {args.output}")

    def start_monitoring(self, args):
        """Start continuous compliance monitoring"""
        interval = args.interval or 300

        print(f"🚀 Starting Elder Compliance Monitoring")
        print(f"⏱️  Monitoring interval: {interval} seconds")
        print("🛡️ Enforcing Universal Claude Elder Standards")
        print("Press Ctrl+C to stop monitoring")
        print()

        try:
            asyncio.run(self.monitor.start_continuous_monitoring(interval))
        except KeyboardInterrupt:
            print("\n🛑 Stopping compliance monitoring...")
            self.monitor.stop_monitoring()
            print("✅ Monitoring stopped.")

    def stop_monitoring(self, args):
        """Stop compliance monitoring"""
        self.monitor.stop_monitoring()
        print("✅ Compliance monitoring stopped.")

    def show_status(self, args):
        """Show current compliance status"""
        print("🏛️ Elder Compliance System Status")
        print("=" * 40)

        # System status
        print(f"📡 Monitoring Active: {self.monitor.monitoring_active}")
        print(f"📊 Database: {self.monitor.db_path}")
        print(f"💾 Data Directory: {self.monitor.data_dir}")
        print()

        # Recent activity
        report = self.monitor.get_compliance_report()
        print("📈 Recent Activity:")
        print(f"  - Total Violations: {report['total_violations']}")
        print(f"  - Total Deployments: {report['total_deployments']}")
        print(f"  - Compliance Rate: {report['compliance_rate']:.1f}%")
        print()

        # Active deployments
        active_deployments = report["active_deployments"]
        print(f"🔄 Active Deployments: {len(active_deployments)}")
        for deployment in active_deployments[:5]:  # Show first 5
            print(f"  - {deployment['servant_type']}: {deployment['deployment_id']}")

        if len(active_deployments) > 5:
            print(f"  ... and {len(active_deployments) - 5} more")

    def deploy_servant(self, args):
        """Manually deploy a servant"""
        servant_type = args.servant_type
        elder_instance = args.elder or "manual_elder"
        task_description = args.task or "Manually deployed servant"

        print(f"🚀 Deploying {servant_type} for Elder: {elder_instance}")

        deployment_id = self.monitor._deploy_servant(
            servant_type=servant_type,
            elder_instance=elder_instance,
            task_description=task_description,
        )

        print(f"✅ Deployed successfully: {deployment_id}")

    def simulate_violation(self, args):
        """Simulate a compliance violation for testing"""
        elder_instance = args.elder or "test_elder"
        violation_type = args.violation_type or "independent_work"

        print(f"🧪 Simulating {violation_type} violation for Elder: {elder_instance}")

        # Create test activity log with violations
        test_activities = {
            "independent_work": [
                "I'll implement this feature myself",
                "Let me write the code directly",
                "I'll handle this task personally",
            ],
            "missing_servants": [
                "I'll do this complex task alone",
                "No need for servants on this one",
                "I can handle this without help",
            ],
            "silent_operation": [
                "Working quietly on this",
                "No need to report progress",
                "I'll work in silence",
            ],
        }

        activities = test_activities.get(
            violation_type, test_activities["independent_work"]
        )

        # Check compliance
        violations = self.monitor.check_compliance(elder_instance, activities)

        print(f"✅ Simulated {len(violations)} violations")
        for violation in violations:
            print(f"  - {violation.violation_type.value}: {violation.description}")

        # Auto-correct if requested
        if args.auto_correct and violations:
            print("🔧 Auto-correcting violations...")
            actions = self.monitor.enforce_compliance(violations)
            print("✅ Correction actions:")
            for action in actions:
                print(f"  - {action}")

    def show_help(self, args=None):
        """Show help information"""
        print(
            """
🏛️ AI Elder Compliance Management

Universal Claude Elder Standards Enforcement System
Ensures all Claude Elders follow Elder Servant coordination protocols.

Commands:
  check      Check compliance for an elder instance
  enforce    Enforce compliance by correcting violations
  report     Generate compliance report
  monitor    Start continuous compliance monitoring
  stop       Stop compliance monitoring
  status     Show current system status
  deploy     Manually deploy a servant
  simulate   Simulate violations for testing
  help       Show this help message

Examples:
  ai-elder-compliance check --elder claude_001
  ai-elder-compliance report --output report.json
  ai-elder-compliance monitor --interval 300
  ai-elder-compliance deploy --servant-type "Coverage Enhancement Knight"
  ai-elder-compliance simulate --violation-type independent_work --auto-correct

Options:
  --elder INSTANCE        Target elder instance
  --activity-log FILE     Load activities from JSON file
  --auto-correct         Automatically correct violations
  --output FILE          Save report to file
  --interval SECONDS     Monitoring interval
  --servant-type TYPE    Type of servant to deploy
  --task DESCRIPTION     Task description for deployment
  --violation-type TYPE  Type of violation to simulate

For more information, see: knowledge_base/UNIVERSAL_CLAUDE_ELDER_STANDARDS.md
"""
        )

    def _create_violation_from_data(self, v_data):
        """Create violation object from stored data"""
        from libs.elder_compliance_monitor import ComplianceViolation

        return ComplianceViolation(
            violation_type=ViolationType(v_data["violation_type"]),
            severity=ComplianceLevel(v_data["severity"]),
            description=v_data["description"],
            detected_at=datetime.fromisoformat(v_data["detected_at"]),
            elder_instance=v_data["elder_instance"],
            evidence=json.loads(v_data["evidence"])
            if isinstance(v_data["evidence"], str)
            else v_data["evidence"],
        )


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="AI Elder Compliance Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("command", nargs="?", help="Command to execute")
    parser.add_argument("--elder", help="Target elder instance")
    parser.add_argument("--activity-log", help="Load activities from JSON file")
    parser.add_argument(
        "--auto-correct", action="store_true", help="Automatically correct violations"
    )
    parser.add_argument("--output", help="Save report to file")
    parser.add_argument(
        "--interval", type=int, default=300, help="Monitoring interval (seconds)"
    )
    parser.add_argument("--servant-type", help="Type of servant to deploy")
    parser.add_argument("--task", help="Task description for deployment")
    parser.add_argument("--violation-type", help="Type of violation to simulate")

    args = parser.parse_args()

    manager = ElderComplianceManager()
    manager.run(args)


if __name__ == "__main__":
    main()
