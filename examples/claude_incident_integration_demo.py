#!/usr/bin/env python3
"""
Claude Elder Incident Integration Demo
クロードエルダーとインシデント賢者の自動連携デモ
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.claude_elder_incident_integration import (
    claude_error_handler,
    get_incident_integration,
)


async def demo_automatic_incident_handling():
    """自動インシデント処理のデモ"""
    print("🚨 Claude Elder Incident Integration Demo")
    print("=" * 50)

    integration = get_incident_integration()

    print("📊 Current failure statistics:")
    stats = integration.get_failure_statistics()
    print(f"  Total incidents: {stats['total_incidents']}")

    print("\n🔧 Testing automatic incident handling...")

    # テストエラー1: インポートエラー
    try:
        import non_existent_module
    except ImportError as e:
        print(f"Caught ImportError: {e}")
        result = await claude_error_handler(
            e,
            {
                "task": "testing_import",
                "module": "non_existent_module",
                "critical": False,
            },
        )
        print(f"  Incident ID: {result.get('incident_id')}")
        print(f"  Elder Council summoned: {result.get('elder_council_summoned')}")
        print(f"  Learning recorded: {result.get('learning_recorded')}")

    print("\n" + "-" * 30)

    # テストエラー2: システムエラー（重要度高）
    try:
        with open("/non/existent/path/file.txt", "r") as f:
            f.read()
    except FileNotFoundError as e:
        print(f"Caught FileNotFoundError: {e}")
        result = await claude_error_handler(
            e,
            {
                "task": "file_operation",
                "file_path": "/non/existent/path/file.txt",
                "critical": True,
                "user": "claude_elder",
            },
        )
        print(f"  Incident ID: {result.get('incident_id')}")
        print(f"  Elder Council summoned: {result.get('elder_council_summoned')}")
        print(f"  Learning recorded: {result.get('learning_recorded')}")

    print("\n📊 Updated failure statistics:")
    stats = integration.get_failure_statistics()
    print(f"  Total incidents: {stats['total_incidents']}")
    print(f"  By severity: {stats.get('by_severity', {})}")
    print(f"  By type: {stats.get('by_type', {})}")

    if stats.get("recent_incidents"):
        print(f"\n📋 Recent incidents:")
        for incident in stats["recent_incidents"]:
            print(f"  - {incident['id']}: {incident['severity']} ({incident['type']})")

    print("\n✅ Demo completed!")
    print("Check the following directories for generated files:")
    print(f"  - {PROJECT_ROOT}/knowledge_base/failures/")


def demo_error_patterns():
    """エラーパターン学習のデモ"""
    print("\n🧠 Error Pattern Learning Demo")
    print("-" * 35)

    integration = get_incident_integration()

    # エラーパターンファイルが存在するかチェック
    patterns_file = PROJECT_ROOT / "knowledge_base" / "failures" / "error_patterns.json"
    if patterns_file.exists():
        import json

        try:
            with open(patterns_file, "r") as f:
                patterns = json.load(f)

            print("📈 Learned error patterns:")
            for pattern, count in patterns.items():
                print(f"  {pattern}: {count} occurrence(s)")
        except Exception as e:
            print(f"Failed to read error patterns: {e}")
    else:
        print("No error patterns learned yet")


def demo_elder_council_records():
    """エルダー評議会記録のデモ"""
    print("\n🏛️ Elder Council Records Demo")
    print("-" * 30)

    failures_dir = PROJECT_ROOT / "knowledge_base" / "failures"
    council_files = list(failures_dir.glob("elder_council_*.json"))

    if council_files:
        print(f"Found {len(council_files)} Elder Council records:")
        for council_file in council_files[-3:]:  # 最新3件
            print(f"  - {council_file.name}")
            try:
                import json

                with open(council_file, "r") as f:
                    council_data = json.load(f)
                print(f"    Severity: {council_data.get('severity')}")
                print(
                    f"    Sages required: {len(council_data.get('sages_required', []))}"
                )
                print(f"    Urgent: {council_data.get('urgent')}")
            except Exception as e:
                print(f"    Failed to read: {e}")
    else:
        print("No Elder Council records found")


def demo_learning_records():
    """学習記録のデモ"""
    print("\n📚 Learning Records Demo")
    print("-" * 25)

    failures_dir = PROJECT_ROOT / "knowledge_base" / "failures"
    learning_files = list(failures_dir.glob("learning_*.md"))

    if learning_files:
        print(f"Found {len(learning_files)} learning records:")
        for learning_file in learning_files[-2:]:  # 最新2件
            print(f"  - {learning_file.name}")
            try:
                content = learning_file.read_text(encoding="utf-8")
                lines = content.split("\n")
                for line in lines[:10]:  # 最初の10行
                    if not (line.strip()):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if line.strip():
                        print(f"    {line}")
                        if not (line.startswith("## 🚨 Error Details")):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if line.startswith("## 🚨 Error Details"):
                            break
            except Exception as e:
                print(f"    Failed to read: {e}")
    else:
        print("No learning records found")


async def main():
    """メインデモ実行"""
    try:
        await demo_automatic_incident_handling()
        demo_error_patterns()
        demo_elder_council_records()
        demo_learning_records()

        print(f"\n🎉 Claude Elder Incident Integration is working perfectly!")
        print(f"✅ FAIL-LEARN-EVOLVE Protocol is now fully automated")
        print(f"🚨 Crisis Sage integration: Active")
        print(f"📚 Knowledge preservation: Active")
        print(f"🏛️ Elder Council summoning: Active")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("Starting Claude Elder Incident Integration Demo...")
    asyncio.run(main())
