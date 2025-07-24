#!/usr/bin/env python3
"""
Claude Elder Integrated Incident Manager Demo
エルダーズ評議会承認の統合インシデント管理システムデモ
"""

import json
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def demo_integration_approach():
    """統合アプローチのデモ"""
    print("🏛️ Elder Council Approved Integration Approach")
    print("=" * 55)

    print("📊 Analysis Results:")
    print("  Option A: Extend existing system ⭐ RECOMMENDED")
    print("  Option B: Frontend integration")
    print("  Option C: Parallel operation")
    print()

    print("✅ Elder Council Decision: Option A - Extend existing system")
    print("📋 Reasons:")
    print("  - Existing 4 Sages system integration")
    print("  - Data compatibility")
    print("  - Minimal operational impact")
    print("  - System consistency")
    print()

    print("🔧 Integration Architecture:")
    print("  ┌─────────────────────────┐")
    print("  │  インシデント管理API    │")
    print("  ├─────────────────────────┤")
    print("  │  Claude Elder統合層     │ ← NEW")
    print("  ├─────────────────────────┤")
    print("  │  既存インシデント管理   │ ← EXTENDED")
    print("  ├─────────────────────────┤")
    print("  │  4賢者システム統合     │ ← EXISTING")
    print("  └─────────────────────────┘")


def demo_integration_features():
    """統合機能のデモ"""
    print("\n🚀 Integration Features Demo")
    print("-" * 30)

    # 統合データ構造のデモ
    integrated_incident_sample = {
        "incident_id": "INC-20250709-0001",
        "claude_incident_id": "CLAUDE_INCIDENT_20250709_132000_1234",
        "timestamp": "2025-07-09T13:20:00.000Z",
        "category": "error",
        "priority": "high",
        "title": "Claude Elder Error: ImportError",
        "description": "Module not found during execution",
        "affected_components": ["claude_elder", "import_system"],
        "impact": "medium - Feature functionality impacted",
        "status": "open",
        "assignee": "claude_elder",
        "claude_integration": {
            "integrated_at": "2025-07-09T13:20:00.000Z",
            "elder_council_summoned": True,
            "learning_recorded": True,
            "context": {"function": "test_integration", "critical": True},
        },
        "timeline": [
            {
                "timestamp": "2025-07-09T13:20:00.000Z",
                "action": "インシデント作成",
                "details": "カテゴリ: error, 優先度: high",
            },
            {
                "timestamp": "2025-07-09T13:20:01.000Z",
                "action": "Claude Elder統合",
                "details": {"integration_enabled": True},
            },
        ],
    }

    print("📊 Integrated Incident Data Structure:")
    print(json.dumps(integrated_incident_sample, indent=2, ensure_ascii=False))


def demo_workflow():
    """ワークフローのデモ"""
    print("\n🔄 Integrated Workflow Demo")
    print("-" * 28)

    workflow_steps = [
        "1.0 🚨 Claude Elder detects error",
        "2.0 🤖 Integrated Crisis Sage creates incident",
        "3.0 📋 Incident stored in existing system",
        "4.0 🏛️ Elder Council summoned (if high priority)",
        "5.0 📚 Learning record created",
        "6.0 🔍 4 Sages collaborate on resolution",
        "7.0 ✅ Incident resolved with learning",
    ]

    for step in workflow_steps:
        print(f"  {step}")

    print("\n🎯 Integration Benefits:")
    benefits = [
        "✅ Unified incident management",
        "✅ Automatic learning records",
        "✅ 4 Sages collaboration",
        "✅ Elder Council integration",
        "✅ FAIL-LEARN-EVOLVE Protocol",
        "✅ Backward compatibility",
    ]

    for benefit in benefits:
        print(f"  {benefit}")


def demo_usage_examples():
    """使用例のデモ"""
    print("\n💡 Usage Examples")
    print("-" * 18)

    print("🔧 Example 1: Basic Integration")
    print("```python")
    print(
        "from libs.claude_elder_integrated_incident_manager import get_integrated_incident_manager"
    )
    print()
    print("manager = get_integrated_incident_manager()")
    print()
    print("# Create incident from Claude error")
    print("try:")
    print("    risky_operation()")
    print("except Exception as e:")
    print("    incident_id = manager.create_incident_from_claude_error(e, {")
    print("        'function': 'risky_operation',")
    print("        'critical': True")
    print("    })")
    print("```")

    print("\n🔧 Example 2: Advanced Integration")
    print("```python")
    print("# Create incident with full integration")
    print("incident_id = manager.create_incident_with_claude_integration(")
    print("    category='error',")
    print("    priority='high',")
    print("    title='Claude Elder Integration Test',")
    print("    description='Testing integrated incident creation',")
    print("    affected_components=['claude_elder', 'integration_system'],")
    print("    impact='medium - Testing functionality',")
    print("    claude_context={'test': True},")
    print("    enable_elder_council=True,")
    print("    enable_learning_record=True")
    print(")")
    print("```")

    print("\n🔧 Example 3: Get Integrated Statistics")
    print("```python")
    print("stats = manager.get_integrated_incident_statistics()")
    print(
        'print(f\'Claude integrated: {stats["claude_integration"]["total_integrated"]}\')'
    )
    print(
        'print(f\'Elder council summoned: {stats["claude_integration"]["elder_council_summoned"]}\')'
    )
    print("```")


def demo_files_generated():
    """生成されるファイルのデモ"""
    print("\n📁 Generated Files Demo")
    print("-" * 23)

    print("🏛️ Elder Council Records:")
    print("  └── knowledge_base/")
    print("      └── elder_council_incident_INC-20250709-0001.0.json")
    print()

    print("📚 Learning Records:")
    print("  └── knowledge_base/failures/")
    print("      └── incident_learning_INC-20250709-0001.0.md")
    print()

    print("📊 Incident Database:")
    print("  └── knowledge_base/")
    print("      └── incident_history.json (extended with Claude integration)")
    print()

    print("🔍 File Contents Preview:")
    print("  - Elder Council: Summoning details, required sages, urgency")
    print("  - Learning Record: Incident analysis, context, improvements")
    print("  - Incident DB: Full incident data with Claude integration info")


def main():
    """メインデモ実行"""
    print("🤖🚨 Claude Elder Integrated Incident Manager Demo")
    print("🏛️ Elder Council Approved Integration System")
    print("=" * 60)

    demo_integration_approach()
    demo_integration_features()
    demo_workflow()
    demo_usage_examples()
    demo_files_generated()

    print("\n🎉 Integration Demo Completed!")
    print("✅ Elder Council approved approach ready for implementation")
    print("🚨 Crisis Sage integration: Active")
    print("📚 Learning system: Active")
    print("🏛️ Elder Council summoning: Active")
    print("🤖 Claude Elder integration: Active")

    print("\n📋 Next Steps:")
    print("1.0 🔧 Implement integrated incident manager")
    print("2.0 🧪 Test with real Claude errors")
    print("3.0 📊 Monitor integration statistics")
    print("4.0 🔄 Refine based on usage patterns")


if __name__ == "__main__":
    main()
