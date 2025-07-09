#!/usr/bin/env python3
"""
強化インシデントマネージャーのテスト実行スクリプト
"""

import sys
import asyncio
from pathlib import Path

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.enhanced_incident_manager import (
    EnhancedIncidentManager, 
    IncidentCreature,
    KnightRank,
    IncidentLevel,
    FantasyIncident
)

def test_creature_classification():
    """クリーチャー分類テスト"""
    print("\n🧪 クリーチャー分類テスト")
    manager = EnhancedIncidentManager()
    
    # テストケース
    test_cases = [
        {
            "incident": {"type": "syntax_error", "severity": "low", "description": "Missing semicolon"},
            "expected": "妖精の悪戯"
        },
        {
            "incident": {"type": "performance", "severity": "medium", "description": "Memory usage increasing"},
            "expected": "スライムの増殖"
        },
        {
            "incident": {"type": "system_failure", "severity": "critical", "description": "Complete system failure"},
            "expected": "古龍の覚醒"
        }
    ]
    
    passed = 0
    for i, test in enumerate(test_cases):
        creature = manager.classify_creature(test["incident"])
        if creature.name == test["expected"]:
            print(f"  ✅ Test {i+1}: {test['expected']} - PASSED")
            passed += 1
        else:
            print(f"  ❌ Test {i+1}: Expected {test['expected']}, got {creature.name}")
    
    return passed, len(test_cases)

def test_knight_rank_assignment():
    """騎士ランク割り当てテスト"""
    print("\n🧪 騎士ランク割り当てテスト")
    manager = EnhancedIncidentManager()
    
    # 新人騎士のテスト
    knight = manager.assign_knight_rank(experience=0)
    
    tests_passed = 0
    tests_total = 3
    
    if knight.rank == KnightRank.SQUIRE:
        print("  ✅ 新人騎士のランクはSQUIRE")
        tests_passed += 1
    else:
        print(f"  ❌ Expected SQUIRE, got {knight.rank}")
    
    if knight.emoji == "🛡️":
        print("  ✅ 絵文字は🛡️")
        tests_passed += 1
    else:
        print(f"  ❌ Expected 🛡️, got {knight.emoji}")
    
    if "detect" in knight.abilities:
        print("  ✅ detect能力を持つ")
        tests_passed += 1
    else:
        print(f"  ❌ detect ability not found in {knight.abilities}")
    
    return tests_passed, tests_total

def test_fantasy_incident_creation():
    """ファンタジーインシデント作成テスト"""
    print("\n🧪 ファンタジーインシデント作成テスト")
    manager = EnhancedIncidentManager()
    
    incident = manager.create_fantasy_incident(
        title="Database connection timeout",
        description="Connection pool exhausted",
        affected_service="user-api"
    )
    
    tests_passed = 0
    tests_total = 4
    
    if isinstance(incident, FantasyIncident):
        print("  ✅ FantasyIncidentインスタンスが作成された")
        tests_passed += 1
    else:
        print("  ❌ Wrong instance type")
    
    if incident.creature is not None:
        print(f"  ✅ クリーチャーが割り当てられた: {incident.creature}")
        tests_passed += 1
    else:
        print("  ❌ No creature assigned")
    
    if incident.quest_title is not None:
        print(f"  ✅ クエストタイトル: {incident.quest_title}")
        tests_passed += 1
    else:
        print("  ❌ No quest title")
    
    if incident.reward_exp > 0:
        print(f"  ✅ 報酬EXP: {incident.reward_exp}")
        tests_passed += 1
    else:
        print("  ❌ No reward exp")
    
    return tests_passed, tests_total

def test_healing_spell():
    """治癒魔法テスト"""
    print("\n🧪 治癒魔法テスト")
    manager = EnhancedIncidentManager()
    
    # 単純エラーのテスト
    simple_incident = {
        "type": "syntax_error",
        "file": "test.py",
        "line": 42,
        "error": "missing colon"
    }
    
    result = manager.cast_healing_spell(simple_incident)
    
    tests_passed = 0
    tests_total = 2
    
    if result.success is True:
        print("  ✅ 単純エラーの治癒成功")
        tests_passed += 1
    else:
        print("  ❌ Simple error healing failed")
    
    if result.spell_type == "minor_healing":
        print("  ✅ minor_healing魔法を使用")
        tests_passed += 1
    else:
        print(f"  ❌ Expected minor_healing, got {result.spell_type}")
    
    return tests_passed, tests_total

def test_prevention_shield():
    """予防シールドテスト"""
    print("\n🧪 予防シールドテスト")
    manager = EnhancedIncidentManager()
    
    shield = manager.activate_prevention_shield(
        service="payment-api",
        threat_level="medium"
    )
    
    tests_passed = 0
    tests_total = 3
    
    if shield.is_active is True:
        print("  ✅ シールドがアクティブ")
        tests_passed += 1
    else:
        print("  ❌ Shield not active")
    
    if shield.protection_level >= 0.7:
        print(f"  ✅ 防御力: {shield.protection_level * 100}%")
        tests_passed += 1
    else:
        print(f"  ❌ Protection level too low: {shield.protection_level}")
    
    if shield.service == "payment-api":
        print("  ✅ 正しいサービスを保護")
        tests_passed += 1
    else:
        print(f"  ❌ Wrong service: {shield.service}")
    
    return tests_passed, tests_total

def test_commit_risk_assessment():
    """コミットリスク評価テスト"""
    print("\n🧪 コミットリスク評価テスト")
    manager = EnhancedIncidentManager()
    
    changes = [
        {"file": "payment.py", "lines_changed": 150},
        {"file": "database.py", "lines_changed": 200}
    ]
    
    risk = manager.assess_commit_risk(changes)
    
    tests_passed = 0
    tests_total = 3
    
    if risk["level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        print(f"  ✅ リスクレベル: {risk['level']}")
        tests_passed += 1
    else:
        print(f"  ❌ Invalid risk level: {risk['level']}")
    
    if risk["creature"] is not None:
        print(f"  ✅ クリーチャー割り当て: {risk['creature']}")
        tests_passed += 1
    else:
        print("  ❌ No creature assigned")
    
    if risk["recommendation"] is not None:
        print(f"  ✅ 推奨事項: {risk['recommendation']}")
        tests_passed += 1
    else:
        print("  ❌ No recommendation")
    
    return tests_passed, tests_total

async def test_async_incident_quest():
    """非同期インシデントクエストテスト"""
    print("\n🧪 非同期インシデントクエストテスト")
    manager = EnhancedIncidentManager()
    
    # インシデント発生
    incident = await manager.start_incident_quest(
        title="API Response Timeout",
        description="Users experiencing slow responses",
        reporter="monitoring-system"
    )
    
    tests_passed = 0
    tests_total = 3
    
    if incident.quest_id is not None:
        print(f"  ✅ クエストID: {incident.quest_id}")
        tests_passed += 1
    else:
        print("  ❌ No quest ID")
    
    if len(incident.assigned_knights) > 0:
        print(f"  ✅ 騎士が割り当てられた: {len(incident.assigned_knights)}名")
        tests_passed += 1
    else:
        print("  ❌ No knights assigned")
    
    # クエスト完了
    completion = await manager.complete_quest(
        quest_id=incident.quest_id,
        resolution="Applied performance optimization"
    )
    
    if completion["success"] is True:
        print(f"  ✅ クエスト完了! 獲得EXP: {completion['exp_awarded']}")
        tests_passed += 1
    else:
        print("  ❌ Quest completion failed")
    
    return tests_passed, tests_total

def main():
    """メインテスト実行"""
    print("🏰 強化インシデントマネージャーテスト開始")
    print("=" * 50)
    
    total_passed = 0
    total_tests = 0
    
    # 同期テスト実行
    tests = [
        test_creature_classification,
        test_knight_rank_assignment,
        test_fantasy_incident_creation,
        test_healing_spell,
        test_prevention_shield,
        test_commit_risk_assessment
    ]
    
    for test_func in tests:
        passed, total = test_func()
        total_passed += passed
        total_tests += total
    
    # 非同期テスト実行
    passed, total = asyncio.run(test_async_incident_quest())
    total_passed += passed
    total_tests += total
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print(f"📊 テスト結果: {total_passed}/{total_tests} 成功")
    
    if total_passed == total_tests:
        print("🎉 すべてのテストが成功しました！")
        return 0
    else:
        print(f"❌ {total_tests - total_passed}個のテストが失敗しました")
        return 1

if __name__ == "__main__":
    sys.exit(main())