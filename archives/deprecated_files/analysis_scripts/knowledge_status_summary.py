#!/usr/bin/env python3
"""
Knowledge Management Status Summary
ナレッジ管理システムのステータスサマリー
"""

import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path("/home/aicompany/ai_co")
sys.path.insert(0, str(PROJECT_ROOT))

print("🎯 Elders Guild Knowledge Management System v5.3")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"Status Check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 1.0 統合ドキュメントの確認
print("📚 Consolidated Knowledge:")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
consolidated_path = PROJECT_ROOT / "knowledge_base" / "CONSOLIDATED_KNOWLEDGE"
if consolidated_path.exists():
    docs = sorted(consolidated_path.glob("*.md"))
    json_files = sorted(consolidated_path.glob("*.json"))

    print(f"📄 Markdown Documents: {len(docs)}")
    for doc in docs[-3:]:
        size = doc.stat().st_size / 1024
        print(f"   - {doc.name} ({size:0.1f} KB)")

    print(f"\n📊 JSON Exports: {len(json_files)}")
    for jf in json_files[-3:]:
        size = jf.stat().st_size / 1024
        print(f"   - {jf.name} ({size:0.1f} KB)")
else:
    print("❌ Consolidated knowledge directory not found")

# 2.0 進化トラッキング
print("\n\n🌱 Evolution Tracking:")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
evolution_path = PROJECT_ROOT / "knowledge_base" / "evolution_tracking"
if evolution_path.exists():
    snapshots = sorted(evolution_path.glob("snapshot_*.json"))
    reports = sorted(evolution_path.glob("evolution_report_*.md"))
    comparisons = sorted(evolution_path.glob("comparison_*.json"))

    print(f"📸 Snapshots: {len(snapshots)}")
    print(f"📈 Evolution Reports: {len(reports)}")
    print(f"🔍 Comparisons: {len(comparisons)}")

    if snapshots:
        latest = snapshots[-1]
        print(f"\n⏰ Latest Snapshot: {latest.name}")
else:
    print("❌ Evolution tracking directory not found")

# 3.0 Webレポート
print("\n\n🌐 Interactive Reports:")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
web_path = PROJECT_ROOT / "web"
if web_path.exists():
    knowledge_reports = sorted(web_path.glob("*knowledge*.html"))
    evolution_viz = sorted(web_path.glob("*evolution*.html"))

    print(f"📊 Knowledge Reports: {len(knowledge_reports)}")
    for report in knowledge_reports[-3:]:
        size = report.stat().st_size / 1024
        print(f"   - {report.name} ({size:0.1f} KB)")

    print(f"\n📈 Evolution Visualizations: {len(evolution_viz)}")
    for viz in evolution_viz[-3:]:
        size = viz.stat().st_size / 1024
        print(f"   - {viz.name} ({size:0.1f} KB)")

    if knowledge_reports or evolution_viz:
        print(f"\n🌐 Access at: http://localhost:8080/")
else:
    print("❌ Web directory not found")

# 4.0 システム統計
print("\n\n📊 System Statistics:")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

# 最新の統合ドキュメントから統計を読み取る
if consolidated_path.exists() and docs:
    latest_doc = docs[-1]
    content = latest_doc.read_text(encoding="utf-8")

    # エグゼクティブサマリーから統計を抽出
    import re

    stats = {}
    patterns = {
        "version": r"\*\*プロジェクトバージョン\*\*: (.+)",
        "files": r"\*\*総ファイル数\*\*: (\d+)",
        "lines": r"\*\*総行数\*\*: (\d+)",
        "workers": r"\*\*ワーカー数\*\*: (\d+)",
        "managers": r"\*\*マネージャー数\*\*: (\d+)",
        "commands": r"\*\*コマンド数\*\*: (\d+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        if match:
            stats[key] = match.group(1)

    print(f"📌 Project Version: {stats.get('version', 'Unknown')}")
    print(f"📁 Total Files: {stats.get('files', 'Unknown')}")
    print(f"📝 Total Lines: {stats.get('lines', 'Unknown')}")
    print(f"🤖 Workers: {stats.get('workers', 'Unknown')}")
    print(f"📊 Managers: {stats.get('managers', 'Unknown')}")
    print(f"⚡ Commands: {stats.get('commands', 'Unknown')}")

# 5.0 使用可能なコマンド
print("\n\n⚡ Available Commands:")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("ai-knowledge consolidate    # Run full consolidation")
print("ai-knowledge evolve         # Track evolution")
print("ai-knowledge evolve --visualize  # With visualization")
print("ai-knowledge status         # Show this status")
print("ai-knowledge schedule       # Run scheduler")

print("\n✅ Knowledge Management System is operational!")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
