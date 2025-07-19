#!/bin/bash
#!/bin/bash
# Knowledge Management System Startup Script

cd /home/aicompany/ai_co
source venv/bin/activate

echo "🚀 Setting up Knowledge Management System..."

# ai-knowledge コマンドの作成
cat > commands/ai_knowledge.py << 'EOF'
#!/usr/bin/env python3
"""
AI Company Knowledge Management Command
統合的なナレッジ管理コマンド
"""

import sys
from pathlib import Path
import argparse

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.knowledge_consolidator import KnowledgeConsolidator
from libs.knowledge_evolution_tracker import KnowledgeEvolutionTracker
from workers.knowledge_scheduler_worker import KnowledgeManagementService
from core import EMOJI

def main():
    parser = argparse.ArgumentParser(
        description='AI Company Knowledge Management System'
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # consolidate サブコマンド
    consolidate_parser = subparsers.add_parser('consolidate', help='Consolidate knowledge')
    consolidate_parser.add_argument('--format', choices=['all', 'markdown', 'html', 'json'],
                                   default='all', help='Output format')

    # evolve サブコマンド
    evolve_parser = subparsers.add_parser('evolve', help='Track evolution')
    evolve_parser.add_argument('--visualize', action='store_true', help='Create visualization')

    # schedule サブコマンド
    schedule_parser = subparsers.add_parser('schedule', help='Run scheduler')
    schedule_parser.add_argument('--daemon', action='store_true', help='Run as daemon')

    # status サブコマンド
    status_parser = subparsers.add_parser('status', help='Show status')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == 'consolidate':
            print(f"{EMOJI['book']} Running knowledge consolidation...")
            consolidator = KnowledgeConsolidator()

            if args.format == 'all':
                consolidator.run_consolidation()
            elif args.format == 'markdown':
                doc_path = consolidator.generate_documentation()
                print(f"{EMOJI['check']} Documentation: {doc_path}")
            elif args.format == 'html':
                report_path = consolidator.create_interactive_report()
                print(f"{EMOJI['check']} Report: {report_path}")
            elif args.format == 'json':
                consolidator.export_to_json()

        elif args.command == 'evolve':
            print(f"{EMOJI['seedling']} Tracking knowledge evolution...")
            tracker = KnowledgeEvolutionTracker()
            tracker.track_evolution()

            if args.visualize:
                viz_path = tracker.visualize_evolution()
                print(f"{EMOJI['chart']} Visualization: {viz_path}")

        elif args.command == 'schedule':
            if args.daemon:
                print(f"{EMOJI['robot']} Starting scheduler as daemon...")
                service = KnowledgeManagementService()
                service.start()
                print("Scheduler running in background")
            else:
                from workers.knowledge_scheduler_worker import KnowledgeManagementScheduler
                scheduler = KnowledgeManagementScheduler()
                scheduler.run()

        elif args.command == 'status':
            print(f"{EMOJI['info']} Knowledge Management Status")
            kb_path = Path("/home/aicompany/ai_co/knowledge_base")

            # 統計情報表示
            md_files = list(kb_path.glob("*.md"))
            print(f"Knowledge documents: {len(md_files)}")

            consolidated = kb_path / "CONSOLIDATED_KNOWLEDGE"
            if consolidated.exists():
                reports = list(consolidated.glob("*.md"))
                print(f"Consolidated reports: {len(reports)}")

            evolution = kb_path / "evolution_tracking"
            if evolution.exists():
                snapshots = list(evolution.glob("snapshot_*.json"))
                print(f"Evolution snapshots: {len(snapshots)}")

    except Exception as e:
        print(f"{EMOJI['x']} Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

EOF

chmod +x commands/ai_knowledge.py
ln -sf ../commands/ai_knowledge.py bin/ai-knowledge

echo "✅ ai-knowledge command created"

# 初回の統合実行
echo "📚 Running initial knowledge consolidation..."
python3 commands/ai_knowledge.py consolidate

echo "🌱 Running initial evolution tracking..."
python3 commands/ai_knowledge.py evolve --visualize

echo "✅ Knowledge Management System setup complete!"
echo ""
echo "Available commands:"
echo "  ai-knowledge consolidate    - Consolidate all knowledge"
echo "  ai-knowledge evolve         - Track evolution"
echo "  ai-knowledge schedule       - Run scheduler"
echo "  ai-knowledge status         - Show status"
