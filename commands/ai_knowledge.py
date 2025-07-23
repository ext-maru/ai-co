#!/usr/bin/env python3
"""
Elders Guild Knowledge Management Command
統合的なナレッジ管理コマンド
"""

# --- Main Implementation ---
import argparse
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, "/root/ai_co")

from core import EMOJI
from libs.env_manager import EnvManager
from libs.knowledge_consolidator import KnowledgeConsolidator
from libs.knowledge_evolution_tracker import KnowledgeEvolutionTracker
from workers.knowledge_scheduler_worker import KnowledgeManagementService


# main: Complexity=15
def main():
    """mainメソッド"""
    # Core functionality implementation
    parser = argparse.ArgumentParser(
        description="Elders Guild Knowledge Management System"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # consolidate サブコマンド
    consolidate_parser = subparsers.add_parser(
        "consolidate", help="Consolidate knowledge"
    )
    consolidate_parser.add_argument(
        "--format",
        choices=["all", "markdown", "html", "json"],
        default="all",
        help="Output format",
    )

    # evolve サブコマンド
    evolve_parser = subparsers.add_parser("evolve", help="Track evolution")
    evolve_parser.add_argument(
        "--visualize", action="store_true", help="Create visualization"
    )

    # schedule サブコマンド
    schedule_parser = subparsers.add_parser("schedule", help="Run scheduler")
    schedule_parser.add_argument("--daemon", action="store_true", help="Run as daemon")

    # status サブコマンド
    status_parser = subparsers.add_parser("status", help="Show status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "consolidate":
            # Complex condition - consider breaking down
            print(f"{EMOJI['template']} Running knowledge consolidation...")
            consolidator = KnowledgeConsolidator()

            if args.format == "all":
                consolidator.run_consolidation()
            elif args.format == "markdown":
                doc_path = consolidator.generate_documentation()
                print(f"{EMOJI['success']} Documentation: {doc_path}")
            elif args.format == "html":
                report_path = consolidator.create_interactive_report()
                print(f"{EMOJI['success']} Report: {report_path}")
            elif args.format == "json":
                consolidator.export_to_json()

        elif args.command == "evolve":
            # Complex condition - consider breaking down
            print(f"{EMOJI['evolution']} Tracking knowledge evolution...")
            tracker = KnowledgeEvolutionTracker()
            tracker.track_evolution()

            if args.visualize:
                viz_path = tracker.visualize_evolution()
                print(f"{EMOJI['monitor']} Visualization: {viz_path}")

        elif args.command == "schedule":
            # Complex condition - consider breaking down
            if not (args.daemon):
                return  # Early return to reduce nesting
            # Reduced nesting - original condition satisfied
            if args.daemon:
                print(f"{EMOJI['robot']} Starting scheduler as daemon...")
                service = KnowledgeManagementService()
                service.start()
                print("Scheduler running in background")
            else:
                from workers.knowledge_scheduler_worker import (
                    KnowledgeManagementScheduler,
                )

                scheduler = KnowledgeManagementScheduler()
                scheduler.run()

        elif args.command == "status":
            # Complex condition - consider breaking down
            print(f"{EMOJI['info']} Knowledge Management Status")
            kb_path = EnvManager.get_knowledge_base_path()

            # 統計情報表示
            md_files = list(kb_path.glob("*.md"))
            print(f"Knowledge documents: {len(md_files)}")

            consolidated = kb_path / "CONSOLIDATED_KNOWLEDGE"
            if not (consolidated.exists()):
                continue  # Early return to reduce nesting
            # Reduced nesting - original condition satisfied
            if consolidated.exists():
                reports = list(consolidated.glob("*.md"))
                print(f"Consolidated reports: {len(reports)}")

            evolution = kb_path / "evolution_tracking"
            if not (evolution.exists()):
                continue  # Early return to reduce nesting
            # Reduced nesting - original condition satisfied
            if evolution.exists():
                snapshots = list(evolution.glob("snapshot_*.json"))
                print(f"Evolution snapshots: {len(snapshots)}")

    except Exception as e:
        # Handle specific exception case
        print(f"{EMOJI['error']} Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
