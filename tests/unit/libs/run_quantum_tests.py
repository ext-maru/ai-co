#!/usr/bin/env python3
"""
量子協調エンジンのテスト実行スクリプト
"""

import sys
import asyncio
import numpy as np
from pathlib import Path

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.quantum_collaboration_engine import (
    QuantumCollaborationEngine,
    QuantumAmplitude,
    SageResponse,
    QuantumSuperposition
)

def test_quantum_amplitude():
    """量子振幅テスト"""
    print("\n🧪 量子振幅テスト")
    
    amplitude = QuantumAmplitude(0.6, 0.8)
    
    tests_passed = 0
    tests_total = 3
    
    if abs(amplitude.magnitude - 1.0) < 0.001:
        print("  ✅ 振幅の大きさが正しい")
        tests_passed += 1
    else:
        print(f"  ❌ Expected magnitude ~1.0, got {amplitude.magnitude}")
    
    expected_phase = np.arctan2(0.8, 0.6)
    if abs(amplitude.phase - expected_phase) < 0.001:
        print("  ✅ 位相が正しい")
        tests_passed += 1
    else:
        print(f"  ❌ Expected phase {expected_phase}, got {amplitude.phase}")
    
    if isinstance(amplitude.magnitude, float) and isinstance(amplitude.phase, float):
        print("  ✅ 型が正しい")
        tests_passed += 1
    else:
        print("  ❌ Type error")
    
    return tests_passed, tests_total

def test_superposition_creation():
    """重ね合わせ状態作成テスト"""
    print("\n🧪 重ね合わせ状態作成テスト")
    engine = QuantumCollaborationEngine()
    
    potential_solutions = ["solution_a", "solution_b", "solution_c"]
    superposition = engine.create_superposition(potential_solutions)
    
    tests_passed = 0
    tests_total = 3
    
    if len(superposition.states) == 3:
        print("  ✅ 状態数が正しい")
        tests_passed += 1
    else:
        print(f"  ❌ Expected 3 states, got {len(superposition.states)}")
    
    if len(superposition.amplitudes) == 3:
        print("  ✅ 振幅数が正しい")
        tests_passed += 1
    else:
        print(f"  ❌ Expected 3 amplitudes, got {len(superposition.amplitudes)}")
    
    # 正規化チェック
    total_prob = sum(amp.magnitude**2 for amp in superposition.amplitudes)
    if abs(total_prob - 1.0) < 0.001:
        print("  ✅ 正規化されている")
        tests_passed += 1
    else:
        print(f"  ❌ Not normalized, total probability: {total_prob}")
    
    return tests_passed, tests_total

def test_amplitude_normalization():
    """振幅正規化テスト"""
    print("\n🧪 振幅正規化テスト")
    
    amplitudes = [
        QuantumAmplitude(0.6, 0.0),
        QuantumAmplitude(0.8, 0.0),
        QuantumAmplitude(0.1, 0.0)
    ]
    
    normalized = QuantumCollaborationEngine._normalize_amplitudes(amplitudes)
    
    tests_passed = 0
    tests_total = 2
    
    # 正規化チェック
    total_magnitude_squared = sum(amp.magnitude**2 for amp in normalized)
    if abs(total_magnitude_squared - 1.0) < 0.001:
        print("  ✅ 正規化が正しい")
        tests_passed += 1
    else:
        print(f"  ❌ Normalization failed: {total_magnitude_squared}")
    
    if len(normalized) == len(amplitudes):
        print("  ✅ 振幅数が保持されている")
        tests_passed += 1
    else:
        print("  ❌ Amplitude count changed")
    
    return tests_passed, tests_total

def test_insight_correlation():
    """洞察相関計算テスト"""
    print("\n🧪 洞察相関計算テスト")
    engine = QuantumCollaborationEngine()
    
    insight1 = "Database optimization needed for better performance"
    insight2 = "Database performance improvement required"
    insight3 = "User interface enhancement suggestion"
    
    correlation_high = engine._calculate_insight_correlation(insight1, insight2)
    correlation_low = engine._calculate_insight_correlation(insight1, insight3)
    
    tests_passed = 0
    tests_total = 3
    
    if correlation_high > correlation_low:
        print(f"  ✅ 高相関 ({correlation_high:.3f}) > 低相関 ({correlation_low:.3f})")
        tests_passed += 1
    else:
        print(f"  ❌ Correlation logic failed: {correlation_high} <= {correlation_low}")
    
    if 0 <= correlation_high <= 1:
        print("  ✅ 高相関値が範囲内")
        tests_passed += 1
    else:
        print(f"  ❌ High correlation out of range: {correlation_high}")
    
    if 0 <= correlation_low <= 1:
        print("  ✅ 低相関値が範囲内")
        tests_passed += 1
    else:
        print(f"  ❌ Low correlation out of range: {correlation_low}")
    
    return tests_passed, tests_total

async def test_parallel_exploration():
    """並列探索テスト"""
    print("\n🧪 並列探索テスト")
    engine = QuantumCollaborationEngine()
    
    learning_request = {
        "problem": "optimize system performance",
        "context": "production environment",
        "constraints": ["memory", "time"]
    }
    
    responses = await engine._parallel_exploration(learning_request)
    
    tests_passed = 0
    tests_total = 3
    
    if len(responses) == 4:
        print("  ✅ 4賢者からの応答を取得")
        tests_passed += 1
    else:
        print(f"  ❌ Expected 4 responses, got {len(responses)}")
    
    all_sage_response = all(isinstance(r, SageResponse) for r in responses)
    if all_sage_response:
        print("  ✅ すべてSageResponseインスタンス")
        tests_passed += 1
    else:
        print("  ❌ Wrong response types")
    
    all_have_confidence = all(hasattr(r, 'confidence') and r.confidence >= 0 for r in responses)
    if all_have_confidence:
        print("  ✅ すべての応答に信頼度あり")
        tests_passed += 1
    else:
        print("  ❌ Missing confidence values")
    
    return tests_passed, tests_total

async def test_quantum_consensus():
    """量子コンセンサステスト"""
    print("\n🧪 量子コンセンサステスト")
    engine = QuantumCollaborationEngine()
    
    learning_request = {
        "problem": "improve application performance",
        "context": "web application with high load",
        "urgency": "medium"
    }
    
    consensus = await engine.quantum_consensus(learning_request)
    
    tests_passed = 0
    tests_total = 5
    
    if consensus.solution is not None:
        print(f"  ✅ ソリューション生成: {consensus.solution[:30]}...")
        tests_passed += 1
    else:
        print("  ❌ No solution generated")
    
    if 0 <= consensus.confidence <= 1:
        print(f"  ✅ 信頼度範囲OK: {consensus.confidence:.3f}")
        tests_passed += 1
    else:
        print(f"  ❌ Confidence out of range: {consensus.confidence}")
    
    if 0 <= consensus.coherence <= 1:
        print(f"  ✅ コヒーレンス範囲OK: {consensus.coherence:.3f}")
        tests_passed += 1
    else:
        print(f"  ❌ Coherence out of range: {consensus.coherence}")
    
    if len(consensus.contributing_sages) > 0:
        print(f"  ✅ 貢献賢者: {len(consensus.contributing_sages)}名")
        tests_passed += 1
    else:
        print("  ❌ No contributing sages")
    
    if len(consensus.entanglement_map) > 0:
        print(f"  ✅ もつれマップ: {len(consensus.entanglement_map)}項目")
        tests_passed += 1
    else:
        print("  ❌ No entanglement map")
    
    return tests_passed, tests_total

def test_quantum_metrics():
    """量子メトリクステスト"""
    print("\n🧪 量子メトリクステスト")
    engine = QuantumCollaborationEngine()
    
    metrics = engine.get_quantum_metrics()
    
    tests_passed = 0
    tests_total = 5
    
    expected_keys = [
        "total_consensus_requests",
        "average_coherence", 
        "entanglement_strength",
        "quantum_efficiency",
        "sage_participation_rate"
    ]
    
    for key in expected_keys:
        if key in metrics:
            print(f"  ✅ {key}: {metrics[key]}")
            tests_passed += 1
        else:
            print(f"  ❌ Missing metric: {key}")
    
    return tests_passed, tests_total

def test_quantum_health():
    """量子健全性テスト"""
    print("\n🧪 量子健全性テスト")
    engine = QuantumCollaborationEngine()
    
    health = engine.check_quantum_health()
    
    tests_passed = 0
    tests_total = 3
    
    valid_statuses = ["healthy", "degraded", "critical"]
    if health["overall_status"] in valid_statuses:
        print(f"  ✅ 総合状態: {health['overall_status']}")
        tests_passed += 1
    else:
        print(f"  ❌ Invalid status: {health['overall_status']}")
    
    if "quantum_coherence_level" in health:
        print(f"  ✅ コヒーレンスレベル: {health['quantum_coherence_level']:.3f}")
        tests_passed += 1
    else:
        print("  ❌ Missing coherence level")
    
    if "entanglement_stability" in health:
        print(f"  ✅ もつれ安定性: {health['entanglement_stability']:.3f}")
        tests_passed += 1
    else:
        print("  ❌ Missing entanglement stability")
    
    return tests_passed, tests_total

async def test_quantum_learning():
    """量子学習テスト"""
    print("\n🧪 量子学習テスト")
    engine = QuantumCollaborationEngine()
    
    learning_examples = [
        {"input": "problem A", "output": "solution A", "success": True, "confidence": 0.9},
        {"input": "problem B", "output": "solution B", "success": False, "confidence": 0.3},
        {"input": "problem C", "output": "solution C", "success": True, "confidence": 0.8}
    ]
    
    result = await engine.quantum_learn(learning_examples)
    
    tests_passed = 0
    tests_total = 3
    
    if result["patterns_learned"] == 2:  # 2つの成功例
        print(f"  ✅ 学習パターン数: {result['patterns_learned']}")
        tests_passed += 1
    else:
        print(f"  ❌ Expected 2 patterns, got {result['patterns_learned']}")
    
    if "quantum_weights" in result and len(result["quantum_weights"]) == 4:
        print("  ✅ 量子重み更新")
        tests_passed += 1
    else:
        print("  ❌ Quantum weights error")
    
    if result["coherence_improvement"] >= 0:
        print(f"  ✅ コヒーレンス改善: {result['coherence_improvement']:.3f}")
        tests_passed += 1
    else:
        print("  ❌ Coherence improvement negative")
    
    return tests_passed, tests_total

async def main():
    """メインテスト実行"""
    print("🌌 量子協調エンジンテスト開始")
    print("=" * 50)
    
    total_passed = 0
    total_tests = 0
    
    # 同期テスト実行
    sync_tests = [
        test_quantum_amplitude,
        test_superposition_creation,
        test_amplitude_normalization,
        test_insight_correlation,
        test_quantum_metrics,
        test_quantum_health
    ]
    
    for test_func in sync_tests:
        passed, total = test_func()
        total_passed += passed
        total_tests += total
    
    # 非同期テスト実行
    async_tests = [
        test_parallel_exploration,
        test_quantum_consensus,
        test_quantum_learning
    ]
    
    for test_func in async_tests:
        passed, total = await test_func()
        total_passed += passed
        total_tests += total
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print(f"📊 テスト結果: {total_passed}/{total_tests} 成功")
    
    if total_passed == total_tests:
        print("🎉 すべてのテストが成功しました！")
        print("🌌 量子協調エンジンが正常に動作しています")
        return 0
    else:
        print(f"❌ {total_tests - total_passed}個のテストが失敗しました")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))